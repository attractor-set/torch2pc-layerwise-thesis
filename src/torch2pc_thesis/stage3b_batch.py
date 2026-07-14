"""Batch-readiness primitives for bounded Stage 3B B0 smoke execution."""

from __future__ import annotations

import json
import os
import socket
import uuid
from collections import Counter
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final, Literal, Protocol, cast

from torch2pc_thesis.stage3b_execution import (
    STAGE3B_CAMPAIGN_ID,
    STAGE3B_EXECUTION_SCHEMA_VERSION,
    Stage3BExecutionError,
    atomic_write_json,
    execute_single_cell_smoke,
    validate_manifest,
    validated_temporary_output_root,
)

B0_CANDIDATE_ID: Final[str] = "stage2_baseline"
B0_EXPECTED_CELL_COUNT: Final[int] = 96
B0_BATCH_MAX_CELLS: Final[int] = 4
B0_BATCH_DEFAULT_MAX_ATTEMPTS: Final[int] = 2

BatchCellState = Literal[
    "pending",
    "running",
    "smoke_passed",
    "failed",
    "retryable",
    "exhausted",
    "blocked",
]


class SingleCellSmokeRunner(Protocol):
    """Callable contract used by the bounded batch orchestrator."""

    def __call__(
        self,
        manifest: Mapping[str, object],
        *,
        output_root: Path,
        cell_id: str,
        device: str,
        dtype: str,
        torch2pc_dir: Path,
        source_commit: str,
        image_id: str | None = None,
    ) -> dict[str, object]: ...


@dataclass(frozen=True)
class B0BatchPlannedCell:
    """Resume-aware state for one B0 smoke cell in one device lane."""

    cell_id: str
    block_id: str
    block_order: int
    method: str
    depth: int
    width: int
    batch_size: int
    model_seed: int
    state: BatchCellState
    attempt_count: int
    failed_attempt_count: int
    running_attempt_count: int
    selected_for_execution: bool

    def to_record(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class B0BatchPlan:
    """Deterministic bounded plan over all 96 B0 cells."""

    manifest_digest: str
    output_root: str
    source_commit: str
    device: str
    dtype: str
    max_cells: int
    max_attempts: int
    resume: bool
    retry_failed: bool
    summary: dict[str, int]
    selected_cell_ids: tuple[str, ...]
    cells: tuple[B0BatchPlannedCell, ...]

    def to_record(self) -> dict[str, object]:
        return {
            "schema_version": STAGE3B_EXECUTION_SCHEMA_VERSION,
            "campaign_id": STAGE3B_CAMPAIGN_ID,
            "execution_scope": "b0_batch_smoke_readiness",
            "evidence": False,
            "full_campaign_complete": False,
            "full_campaign_execution_enabled": False,
            "manifest_digest": self.manifest_digest,
            "output_root": self.output_root,
            "source_commit": self.source_commit,
            "device": self.device,
            "dtype": self.dtype,
            "b0_cell_count": len(self.cells),
            "max_cells": self.max_cells,
            "hard_max_cells": B0_BATCH_MAX_CELLS,
            "max_attempts": self.max_attempts,
            "resume": self.resume,
            "retry_failed": self.retry_failed,
            "summary": dict(sorted(self.summary.items())),
            "selected_cell_ids": list(self.selected_cell_ids),
            "cells": [cell.to_record() for cell in self.cells],
        }


@dataclass(frozen=True)
class _AttemptSummary:
    attempt_count: int = 0
    failed_count: int = 0
    running_count: int = 0
    matching_success: bool = False


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _utc_now() -> str:
    return datetime.now(tz=UTC).isoformat().replace("+00:00", "Z")


def _batch_id() -> str:
    timestamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%S%fZ")
    return f"{timestamp}-{uuid.uuid4().hex[:12]}"


def _append_jsonl(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = (_canonical_json(payload) + "\n").encode("utf-8")
    descriptor = os.open(path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
    try:
        os.write(descriptor, line)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _validated_source_commit(source_commit: str) -> str:
    normalized = source_commit.strip().lower()
    if len(normalized) != 40 or any(character not in "0123456789abcdef" for character in normalized):
        raise Stage3BExecutionError(
            "B0 batch readiness requires an exact clean 40-character source commit"
        )
    return normalized


def _validated_lane(*, device: str, dtype: str) -> tuple[str, str]:
    normalized_device = device.lower()
    normalized_dtype = dtype.lower()
    if normalized_device == "cpu" and normalized_dtype == "float64":
        return normalized_device, normalized_dtype
    if normalized_device == "rocm" and normalized_dtype == "float32":
        return normalized_device, normalized_dtype
    raise Stage3BExecutionError(
        "B0 batch smoke lanes are limited to cpu/float64 and rocm/float32"
    )


def _validated_limits(*, max_cells: int, max_attempts: int) -> tuple[int, int]:
    if max_cells < 0 or max_cells > B0_BATCH_MAX_CELLS:
        raise Stage3BExecutionError(
            f"B0 batch smoke max_cells must be between 0 and {B0_BATCH_MAX_CELLS}"
        )
    if max_attempts < 1 or max_attempts > 3:
        raise Stage3BExecutionError("B0 batch smoke max_attempts must be between 1 and 3")
    return max_cells, max_attempts


def _load_json_object(path: Path) -> dict[str, object] | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(raw, dict):
        return None
    return cast(dict[str, object], raw)


def _request_matches_lane(
    request: Mapping[str, object],
    *,
    cell_id: str,
    manifest_digest: str,
    device: str,
    dtype: str,
) -> bool:
    return (
        request.get("cell_id") == cell_id
        and request.get("manifest_digest") == manifest_digest
        and request.get("candidate_id") == B0_CANDIDATE_ID
        and request.get("device") == device
        and request.get("dtype") == dtype
        and request.get("execution_scope") == "single_cell_smoke"
    )


def _inspect_attempts(
    *,
    output_root: Path,
    cell_id: str,
    manifest_digest: str,
    source_commit: str,
    device: str,
    dtype: str,
) -> _AttemptSummary:
    attempts_root = output_root / "smoke" / "cells" / cell_id / "attempts"
    if not attempts_root.is_dir():
        return _AttemptSummary()

    attempt_count = 0
    failed_count = 0
    running_count = 0
    matching_success = False

    for attempt_dir in sorted(path for path in attempts_root.iterdir() if path.is_dir()):
        request = _load_json_object(attempt_dir / "request.json")
        if request is None or not _request_matches_lane(
            request,
            cell_id=cell_id,
            manifest_digest=manifest_digest,
            device=device,
            dtype=dtype,
        ):
            continue

        attempt_count += 1
        completed = _load_json_object(attempt_dir / "completed.json")
        failed = _load_json_object(attempt_dir / "failed.json")
        started = _load_json_object(attempt_dir / "started.json")

        if completed is not None and completed.get("status") == "smoke_passed":
            environment = _load_json_object(attempt_dir / "environment.json")
            if environment is not None and environment.get("project_source_commit") == source_commit:
                matching_success = True
            continue
        if failed is not None and failed.get("status") == "smoke_failed":
            failed_count += 1
            continue
        if started is not None and started.get("status") == "smoke_running":
            running_count += 1

    return _AttemptSummary(
        attempt_count=attempt_count,
        failed_count=failed_count,
        running_count=running_count,
        matching_success=matching_success,
    )


def _state_from_attempts(
    summary: _AttemptSummary,
    *,
    resume: bool,
    retry_failed: bool,
    max_attempts: int,
) -> BatchCellState:
    if summary.matching_success:
        return "smoke_passed"
    if summary.attempt_count >= max_attempts and (summary.failed_count or summary.running_count):
        return "exhausted"
    if summary.running_count:
        return "retryable" if resume else "running"
    if summary.failed_count:
        return "retryable" if retry_failed else "failed"
    return "pending"


def _b0_cells(manifest: Mapping[str, object]) -> list[dict[str, object]]:
    raw_cells = cast(list[dict[str, object]], manifest["cells"])
    cells = [dict(cell) for cell in raw_cells if cell.get("candidate_id") == B0_CANDIDATE_ID]
    cells.sort(
        key=lambda cell: (
            int(cast(int, cell["depth"])),
            int(cast(int, cell["width"])),
            int(cast(int, cell["batch_size"])),
            int(cast(int, cell["model_seed"])),
            str(cell["method"]),
            str(cell["cell_id"]),
        )
    )
    if len(cells) != B0_EXPECTED_CELL_COUNT:
        raise Stage3BExecutionError(
            f"B0 batch plan requires {B0_EXPECTED_CELL_COUNT} cells, got {len(cells)}"
        )
    return cells


def plan_b0_batch_smoke(
    manifest: Mapping[str, object],
    *,
    output_root: Path,
    device: str,
    dtype: str,
    source_commit: str,
    max_cells: int = B0_BATCH_MAX_CELLS,
    max_attempts: int = B0_BATCH_DEFAULT_MAX_ATTEMPTS,
    resume: bool = False,
    retry_failed: bool = False,
) -> B0BatchPlan:
    """Build a deterministic resume-aware plan over all 96 B0 cells."""

    validate_manifest(manifest)
    resolved_root = validated_temporary_output_root(output_root)
    normalized_device, normalized_dtype = _validated_lane(device=device, dtype=dtype)
    clean_commit = _validated_source_commit(source_commit)
    bounded_cells, bounded_attempts = _validated_limits(
        max_cells=max_cells,
        max_attempts=max_attempts,
    )
    manifest_digest = str(manifest["manifest_digest"])

    staged: list[tuple[dict[str, object], BatchCellState, _AttemptSummary]] = []
    for cell in _b0_cells(manifest):
        cell_id = str(cell["cell_id"])
        summary = _inspect_attempts(
            output_root=resolved_root,
            cell_id=cell_id,
            manifest_digest=manifest_digest,
            source_commit=clean_commit,
            device=normalized_device,
            dtype=normalized_dtype,
        )
        state = _state_from_attempts(
            summary,
            resume=resume,
            retry_failed=retry_failed,
            max_attempts=bounded_attempts,
        )
        staged.append((cell, state, summary))

    eligible_states: set[BatchCellState] = {"pending", "retryable"}
    selected_ids: list[str] = []
    if bounded_cells:
        selected_ids = [
            str(cell["cell_id"])
            for cell, state, _summary in staged
            if state in eligible_states
        ][:bounded_cells]
    selected_set = set(selected_ids)

    planned: list[B0BatchPlannedCell] = []
    for cell, state, summary in staged:
        cell_id = str(cell["cell_id"])
        planned.append(
            B0BatchPlannedCell(
                cell_id=cell_id,
                block_id=str(cell["block_id"]),
                block_order=int(cast(int, cell["block_order"])),
                method=str(cell["method"]),
                depth=int(cast(int, cell["depth"])),
                width=int(cast(int, cell["width"])),
                batch_size=int(cast(int, cell["batch_size"])),
                model_seed=int(cast(int, cell["model_seed"])),
                state=state,
                attempt_count=summary.attempt_count,
                failed_attempt_count=summary.failed_count,
                running_attempt_count=summary.running_count,
                selected_for_execution=cell_id in selected_set,
            )
        )

    summary_counts = Counter(cell.state for cell in planned)
    return B0BatchPlan(
        manifest_digest=manifest_digest,
        output_root=str(resolved_root),
        source_commit=clean_commit,
        device=normalized_device,
        dtype=normalized_dtype,
        max_cells=bounded_cells,
        max_attempts=bounded_attempts,
        resume=resume,
        retry_failed=retry_failed,
        summary={str(key): value for key, value in summary_counts.items()},
        selected_cell_ids=tuple(selected_ids),
        cells=tuple(planned),
    )


def _process_is_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _acquire_lane_lock(path: Path, *, resume: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "pid": os.getpid(),
        "hostname": socket.gethostname(),
        "created_at": _utc_now(),
    }
    while True:
        try:
            descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            existing = _load_json_object(path)
            same_host = existing is not None and existing.get("hostname") == socket.gethostname()
            raw_pid = existing.get("pid") if existing is not None else None
            pid = raw_pid if isinstance(raw_pid, int) else -1
            if not resume or (same_host and _process_is_alive(pid)):
                raise Stage3BExecutionError(
                    f"B0 batch lane is already locked: {path}"
                ) from None
            path.unlink(missing_ok=True)
            continue
        try:
            os.write(descriptor, (_canonical_json(payload) + "\n").encode("utf-8"))
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        return


def execute_b0_batch_smoke(
    manifest: Mapping[str, object],
    *,
    output_root: Path,
    device: str,
    dtype: str,
    source_commit: str,
    max_cells: int,
    torch2pc_dir: Path,
    image_id: str | None = None,
    max_attempts: int = B0_BATCH_DEFAULT_MAX_ATTEMPTS,
    resume: bool = False,
    retry_failed: bool = False,
    runner: SingleCellSmokeRunner = execute_single_cell_smoke,
) -> dict[str, object]:
    """Execute at most four B0 smoke cells with failure isolation and journaling."""

    if max_cells < 1:
        raise Stage3BExecutionError("B0 batch smoke execution requires max_cells >= 1")

    plan = plan_b0_batch_smoke(
        manifest,
        output_root=output_root,
        device=device,
        dtype=dtype,
        source_commit=source_commit,
        max_cells=max_cells,
        max_attempts=max_attempts,
        resume=resume,
        retry_failed=retry_failed,
    )
    if not plan.selected_cell_ids:
        raise Stage3BExecutionError("B0 batch smoke plan has no eligible cells")

    resolved_root = Path(plan.output_root)
    lane_name = f"{plan.device}-{plan.dtype}"
    lock_path = resolved_root / "batch" / "locks" / f"{lane_name}.lock"
    _acquire_lane_lock(lock_path, resume=resume)

    batch_id = _batch_id()
    batch_dir = resolved_root / "batch" / "runs" / batch_id
    batch_dir.mkdir(parents=True, exist_ok=False)
    journal_path = resolved_root / "batch" / "campaign-journal.jsonl"

    request = {
        "schema_version": STAGE3B_EXECUTION_SCHEMA_VERSION,
        "campaign_id": STAGE3B_CAMPAIGN_ID,
        "batch_id": batch_id,
        "execution_scope": "bounded_b0_batch_smoke",
        "evidence": False,
        "full_campaign_complete": False,
        "manifest_digest": plan.manifest_digest,
        "source_commit": plan.source_commit,
        "device": plan.device,
        "dtype": plan.dtype,
        "max_cells": plan.max_cells,
        "hard_max_cells": B0_BATCH_MAX_CELLS,
        "max_attempts": plan.max_attempts,
        "resume": plan.resume,
        "retry_failed": plan.retry_failed,
        "selected_cell_ids": list(plan.selected_cell_ids),
    }
    atomic_write_json(batch_dir / "request.json", request)
    atomic_write_json(batch_dir / "plan.json", plan.to_record())
    started = {**request, "status": "batch_smoke_running", "started_at": _utc_now()}
    atomic_write_json(batch_dir / "started.json", started)
    _append_jsonl(journal_path, started)

    results: list[dict[str, object]] = []
    try:
        for cell_id in plan.selected_cell_ids:
            try:
                result = runner(
                    manifest,
                    output_root=resolved_root,
                    cell_id=cell_id,
                    device=plan.device,
                    dtype=plan.dtype,
                    torch2pc_dir=torch2pc_dir,
                    source_commit=plan.source_commit,
                    image_id=image_id,
                )
                results.append(
                    {
                        "cell_id": cell_id,
                        "status": "smoke_passed",
                        "attempt_id": result.get("attempt_id"),
                        "attempt_directory": result.get("attempt_directory"),
                    }
                )
            except Exception as exc:
                results.append(
                    {
                        "cell_id": cell_id,
                        "status": "failed",
                        "exception_type": type(exc).__name__,
                        "exception_message": str(exc),
                    }
                )

        failed_count = sum(result["status"] == "failed" for result in results)
        final_status = "batch_smoke_passed" if failed_count == 0 else "batch_smoke_partial_failure"
        results_payload = {
            **request,
            "status": final_status,
            "executed_cell_count": len(results),
            "passed_cell_count": len(results) - failed_count,
            "failed_cell_count": failed_count,
            "results": results,
        }
        atomic_write_json(batch_dir / "results.json", results_payload)
        completed = {
            **results_payload,
            "completed_at": _utc_now(),
            "batch_directory": str(batch_dir),
        }
        atomic_write_json(batch_dir / "completed.json", completed)
        _append_jsonl(journal_path, completed)
        return completed
    finally:
        lock_path.unlink(missing_ok=True)
