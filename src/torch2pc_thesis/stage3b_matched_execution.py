"""Authorized matched Stage 3B B0/B1/B2 lane execution primitives."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import socket
import subprocess
import sys
import uuid
from collections import Counter, defaultdict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final, Literal, Protocol, cast

import torch
from torch import Tensor, nn

from torch2pc_thesis.models import build_model
from torch2pc_thesis.profiling import STAGE3_PROFILE_REGIONS, ProfilingProtocol
from torch2pc_thesis.reproducibility import set_global_seed, stable_int_seed
from torch2pc_thesis.stage3b_b0_integration import (
    B0GateConfig,
    MethodName,
    run_b0_non_perturbation_gate,
    torch2pc_method_label,
)
from torch2pc_thesis.stage3b_execution import (
    STAGE3B_CAMPAIGN_ID,
    Stage3BExecutionError,
    atomic_write_json,
    validate_manifest,
    validated_temporary_output_root,
)
from torch2pc_thesis.stage3b_matched_authorization import (
    MATCHED_AUTHORIZATION_SCOPE,
    MATCHED_CANONICAL_LANES,
    MatchedRuntimeProbe,
    validate_matched_campaign_authorization,
    verify_matched_authorization_for_lane,
)
from torch2pc_thesis.stage3b_matched_profiling import (
    MATCHED_PROFILING_CANDIDATES,
    MATCHED_PROFILING_EXPECTED_CELL_COUNT,
    validate_matched_manifest,
    validate_matched_request,
)
from torch2pc_thesis.stage3b_matched_runner import (
    MATCHED_RUNNER_STATE_RESET_POLICY,
    adapter_for_candidate,
    load_candidate_pc_infer,
    validate_runner_inputs,
)
from torch2pc_thesis.stage3b_profiling import (
    RegionMeasurement,
    iter_protocol_steps,
    validate_profile_completeness,
)

MATCHED_EXECUTION_SCHEMA_VERSION: Final[int] = 1
MATCHED_EXECUTION_SCOPE: Final[str] = "authorized_b1_b2_matched_lane"
MATCHED_EXECUTION_CELL_SCOPE: Final[str] = "authorized_b1_b2_matched_cell"
MATCHED_EXECUTION_PROCESS_SCOPE: Final[str] = "authorized_b1_b2_matched_cell_process"
MATCHED_EXECUTION_PROCESS_MODE: Final[str] = "fresh_python_child_per_cell"
MATCHED_EXECUTION_STATE_RECONSTRUCTION: Final[str] = (
    "deterministic_fresh_process_reconstruction_per_candidate"
)
MATCHED_EXECUTION_DEFAULT_MAX_ATTEMPTS: Final[int] = 2
MATCHED_EXECUTION_MAX_ATTEMPTS: Final[int] = 3
MATCHED_EXECUTION_ETA: Final[float] = 0.1
MATCHED_EXECUTION_LEARNING_RATE: Final[float] = 0.01
MATCHED_EXECUTION_INFERENCE_STEPS: Final[dict[str, int]] = {
    "fixedpred": 10,
    "strict": 20,
}
MATCHED_EXECUTION_PROTOCOL: Final[dict[str, int]] = {
    "warmup_steps": 20,
    "measured_steps": 50,
    "repetitions": 5,
}
MATCHED_EXECUTION_FULL_PROTOCOL: Final[dict[str, object]] = {
    **MATCHED_EXECUTION_PROTOCOL,
    "independent_unit": "model_seed",
    "candidate_order": ("exactly_counterbalanced_hash_ranked_rotation_within_method"),
}
MATCHED_EXECUTION_REQUIRED_REGIONS: Final[tuple[str, ...]] = tuple(sorted(STAGE3_PROFILE_REGIONS))
MATCHED_ENGINEERING_CONTROL_LANES: Final[frozenset[tuple[str, str]]] = frozenset(
    {("cpu", "float64")}
)

MatchedCellState = Literal[
    "pending",
    "running",
    "completed",
    "failed",
    "retryable",
    "exhausted",
    "blocked",
]

AuthorizationVerifier = Callable[..., dict[str, object]]


@dataclass(frozen=True)
class MatchedCellContext:
    """Frozen inputs passed to one matched cell measurement executor."""

    cell: Mapping[str, object]
    authorization_token: str
    matched_manifest_digest: str
    opening_request_digest: str
    source_manifest_digest: str
    output_root: Path
    attempt_directory: Path
    device: torch.device
    requested_device: str
    dtype: torch.dtype
    dtype_name: str
    torch2pc_dir: Path
    source_commit: str
    image_digest: str
    emergency_stop_path: Path
    protocol: ProfilingProtocol


@dataclass(frozen=True)
class MatchedCellResult:
    """Serializable payload returned by a matched cell executor."""

    resolved_config: Mapping[str, object]
    environment: Mapping[str, object]
    measurements: Mapping[str, object]


MatchedCellExecutor = Callable[[MatchedCellContext], MatchedCellResult]


class MatchedCellRunner(Protocol):
    """Callable contract used by the matched lane orchestrator."""

    def __call__(
        self,
        matched_manifest: Mapping[str, object],
        request: Mapping[str, object],
        base_manifest: Mapping[str, object],
        authorization: Mapping[str, object],
        *,
        output_root: Path,
        cell_id: str,
        device: str,
        dtype: str,
        project_root: Path,
        base_manifest_path: Path,
        torch2pc_dir: Path,
        source_commit: str,
        image_digest: str,
        executor: MatchedCellExecutor | None = None,
    ) -> dict[str, object]: ...


class MatchedCellProcessError(Stage3BExecutionError):
    """Raised when a per-cell child process violates the lifecycle contract."""


@dataclass(frozen=True)
class MatchedPlannedCell:
    """Resume-aware state for one authorized matched cell in one lane."""

    cell_id: str
    block_id: str
    block_order: int
    candidate_order: int
    candidate_id: str
    method: str
    depth: int
    width: int
    batch_size: int
    model_seed: int
    state: MatchedCellState
    attempt_count: int
    failed_attempt_count: int
    running_attempt_count: int
    selected_for_execution: bool

    def to_record(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class MatchedLanePlan:
    """Deterministic authorization-verified plan over 288 matched cells."""

    authorization_token: str
    matched_manifest_digest: str
    opening_request_digest: str
    source_manifest_digest: str
    output_root: str
    source_commit: str
    device: str
    dtype: str
    image_digest: str
    max_attempts: int
    resume: bool
    retry_failed: bool
    summary: dict[str, int]
    selected_cell_ids: tuple[str, ...]
    cells: tuple[MatchedPlannedCell, ...]

    def to_record(self) -> dict[str, object]:
        return {
            "schema_version": MATCHED_EXECUTION_SCHEMA_VERSION,
            "campaign_id": STAGE3B_CAMPAIGN_ID,
            "authorization_scope": MATCHED_AUTHORIZATION_SCOPE,
            "execution_scope": MATCHED_EXECUTION_SCOPE,
            "authorization_verified": True,
            "authorization_token": self.authorization_token,
            "execution_permitted": True,
            "execution_performed": False,
            "evidence": False,
            "full_lane_complete": False,
            "full_stage3b_campaign_complete": False,
            "results_publication_permitted": False,
            "test_dataset_access": False,
            "admitted_candidates": list(MATCHED_PROFILING_CANDIDATES),
            "matched_manifest_digest": self.matched_manifest_digest,
            "opening_request_digest": self.opening_request_digest,
            "source_manifest_digest": self.source_manifest_digest,
            "output_root": self.output_root,
            "source_commit": self.source_commit,
            "device": self.device,
            "dtype": self.dtype,
            "image_digest": self.image_digest,
            "matched_protocol": dict(MATCHED_EXECUTION_FULL_PROTOCOL),
            "state_reset_policy": MATCHED_RUNNER_STATE_RESET_POLICY,
            "state_reconstruction": MATCHED_EXECUTION_STATE_RECONSTRUCTION,
            "matched_cell_count": len(self.cells),
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


def _identifier() -> str:
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


def _load_json_object(path: Path) -> dict[str, object] | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(raw, dict):
        return None
    return cast(dict[str, object], raw)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _text_tail(value: str, *, limit: int = 4096) -> str:
    return value[-limit:]


def _validated_source_commit(source_commit: str) -> str:
    normalized = source_commit.strip().lower()
    if len(normalized) != 40 or any(
        character not in "0123456789abcdef" for character in normalized
    ):
        raise Stage3BExecutionError(
            "matched execution requires an exact 40-character source commit"
        )
    return normalized


def _validated_lane(
    *,
    device: str,
    dtype: str,
    allow_engineering_control: bool = False,
) -> tuple[str, str]:
    lane = (device.strip().lower(), dtype.strip().lower())
    if lane in MATCHED_CANONICAL_LANES:
        return lane
    if allow_engineering_control and lane in MATCHED_ENGINEERING_CONTROL_LANES:
        return lane
    raise Stage3BExecutionError(
        "matched execution is limited to rocm/float32; cpu/float64 is available "
        "only through injected engineering-control tests"
    )


def _validated_max_attempts(max_attempts: int) -> int:
    if not 1 <= max_attempts <= MATCHED_EXECUTION_MAX_ATTEMPTS:
        raise Stage3BExecutionError(
            f"matched max_attempts must be between 1 and {MATCHED_EXECUTION_MAX_ATTEMPTS}"
        )
    return max_attempts


def _matched_protocol(authorization: Mapping[str, object]) -> ProfilingProtocol:
    raw = authorization.get("canonical_protocol")
    if not isinstance(raw, Mapping):
        raise Stage3BExecutionError("matched protocol is missing from authorization")
    observed = {
        "warmup_steps": int(cast(int, raw.get("warmup_steps"))),
        "measured_steps": int(cast(int, raw.get("measured_steps"))),
        "repetitions": int(cast(int, raw.get("repetitions"))),
        "independent_unit": str(raw.get("independent_unit")),
        "candidate_order": str(raw.get("candidate_order")),
    }
    if observed != MATCHED_EXECUTION_FULL_PROTOCOL:
        raise Stage3BExecutionError(
            f"authorization protocol differs from matched contract: {observed}"
        )
    return ProfilingProtocol(**MATCHED_EXECUTION_PROTOCOL)


def _matched_cells(
    matched_manifest: Mapping[str, object],
    request: Mapping[str, object],
) -> list[dict[str, object]]:
    cells = validate_runner_inputs(matched_manifest, request)
    records = [dict(cell) for cell in cells]
    if len(records) != MATCHED_PROFILING_EXPECTED_CELL_COUNT:
        raise Stage3BExecutionError("matched plan requires exactly 288 cells")
    return records


def _select_matched_cell(
    matched_manifest: Mapping[str, object],
    request: Mapping[str, object],
    *,
    cell_id: str,
) -> dict[str, object]:
    matches = [
        cell for cell in _matched_cells(matched_manifest, request) if cell.get("cell_id") == cell_id
    ]
    if len(matches) != 1:
        raise Stage3BExecutionError(f"expected one matched cell, got {len(matches)}")
    return matches[0]


def _lane_name(*, device: str, dtype: str) -> str:
    return f"{device}-{dtype}"


def _lane_root(output_root: Path, *, device: str, dtype: str) -> Path:
    return output_root / "matched" / "lanes" / _lane_name(device=device, dtype=dtype)


def _request_matches(
    request: Mapping[str, object],
    *,
    cell: Mapping[str, object],
    authorization_token: str,
    matched_manifest_digest: str,
    opening_request_digest: str,
    source_manifest_digest: str,
    source_commit: str,
    device: str,
    dtype: str,
    image_digest: str,
) -> bool:
    return bool(
        request.get("execution_scope") == MATCHED_EXECUTION_CELL_SCOPE
        and request.get("cell_id") == cell.get("cell_id")
        and request.get("block_id") == cell.get("block_id")
        and request.get("candidate_id") == cell.get("candidate_id")
        and request.get("candidate_order") == cell.get("candidate_order")
        and request.get("authorization_token") == authorization_token
        and request.get("matched_manifest_digest") == matched_manifest_digest
        and request.get("opening_request_digest") == opening_request_digest
        and request.get("source_manifest_digest") == source_manifest_digest
        and request.get("source_commit") == source_commit
        and request.get("device") == device
        and request.get("dtype") == dtype
        and request.get("image_digest") == image_digest
        and request.get("matched_protocol") == MATCHED_EXECUTION_FULL_PROTOCOL
        and request.get("state_reset_policy") == MATCHED_RUNNER_STATE_RESET_POLICY
        and request.get("state_reconstruction") == MATCHED_EXECUTION_STATE_RECONSTRUCTION
    )


def _attempt_directories(
    *,
    output_root: Path,
    cell_id: str,
    device: str,
    dtype: str,
) -> set[Path]:
    attempts_root = (
        _lane_root(output_root, device=device, dtype=dtype) / "cells" / cell_id / "attempts"
    )
    if not attempts_root.is_dir():
        return set()
    return {path.resolve() for path in attempts_root.iterdir() if path.is_dir()}


def _validated_child_terminal(
    *,
    attempt_dir: Path,
    cell: Mapping[str, object],
    authorization_token: str,
    matched_manifest_digest: str,
    opening_request_digest: str,
    source_manifest_digest: str,
    source_commit: str,
    device: str,
    dtype: str,
    image_digest: str,
) -> tuple[dict[str, object], Path]:
    request = _load_json_object(attempt_dir / "request.json")
    if request is None or not _request_matches(
        request,
        cell=cell,
        authorization_token=authorization_token,
        matched_manifest_digest=matched_manifest_digest,
        opening_request_digest=opening_request_digest,
        source_manifest_digest=source_manifest_digest,
        source_commit=source_commit,
        device=device,
        dtype=dtype,
        image_digest=image_digest,
    ):
        raise MatchedCellProcessError(
            f"child attempt request does not match the authorized matched cell: {attempt_dir}"
        )

    completed_path = attempt_dir / "completed.json"
    failed_path = attempt_dir / "failed.json"
    existing_terminals = [path for path in (completed_path, failed_path) if path.exists()]
    if len(existing_terminals) != 1:
        raise MatchedCellProcessError(
            "child process must leave exactly one terminal record for "
            f"{cell['cell_id']}; found {len(existing_terminals)}"
        )

    terminal_path = existing_terminals[0]
    terminal = _load_json_object(terminal_path)
    if terminal is None:
        raise MatchedCellProcessError(
            f"child terminal record is not a JSON object: {terminal_path}"
        )
    expected_status = (
        "matched_cell_complete" if terminal_path == completed_path else "matched_cell_failed"
    )
    if not _request_matches(
        terminal,
        cell=cell,
        authorization_token=authorization_token,
        matched_manifest_digest=matched_manifest_digest,
        opening_request_digest=opening_request_digest,
        source_manifest_digest=source_manifest_digest,
        source_commit=source_commit,
        device=device,
        dtype=dtype,
        image_digest=image_digest,
    ):
        raise MatchedCellProcessError(
            f"child terminal record does not match the authorized matched cell: {terminal_path}"
        )
    immutable_fields = (
        "schema_version",
        "campaign_id",
        "authorization_scope",
        "execution_scope",
        "attempt_id",
        "cell_id",
        "block_id",
        "block_order",
        "candidate_id",
        "candidate_order",
        "method",
        "authorization_token",
        "matched_manifest_digest",
        "opening_request_digest",
        "source_manifest_digest",
        "source_commit",
        "device",
        "dtype",
        "image_digest",
        "matched_protocol",
        "state_reset_policy",
        "state_reconstruction",
        "evidence",
        "full_lane_complete",
        "full_stage3b_campaign_complete",
        "results_publication_permitted",
        "test_dataset_access",
    )
    mismatched = [field for field in immutable_fields if terminal.get(field) != request.get(field)]
    if mismatched:
        raise MatchedCellProcessError(
            f"child terminal differs from immutable request fields {mismatched}: {terminal_path}"
        )
    if terminal.get("attempt_directory") != str(attempt_dir):
        raise MatchedCellProcessError(
            f"child terminal attempt_directory differs from parent observation: {terminal_path}"
        )
    if terminal.get("status") != expected_status:
        raise MatchedCellProcessError(f"child terminal status is invalid: {terminal_path}")
    if expected_status == "matched_cell_complete":
        if terminal.get("full_cell_complete") is not True:
            raise MatchedCellProcessError(
                f"completed child did not mark the cell complete: {terminal_path}"
            )
    elif terminal.get("full_cell_complete") is not False:
        raise MatchedCellProcessError(f"failed child changed full_cell_complete: {terminal_path}")
    return terminal, terminal_path


def _systemic_gpu_oom(
    *,
    terminal: Mapping[str, object] | None,
    stderr: str,
) -> bool:
    exception_type = ""
    exception_message = ""
    if terminal is not None:
        exception_type = str(terminal.get("exception_type", "")).lower()
        exception_message = str(terminal.get("exception_message", "")).lower()
    combined = f"{exception_type}\n{exception_message}\n{stderr.lower()}"
    return (
        "outofmemoryerror" in combined
        or "hip out of memory" in combined
        or "cuda out of memory" in combined
        or "hiperroroutofmemory" in combined
        or "cudaerror_memoryallocation" in combined
    )


@dataclass(frozen=True)
class MatchedSubprocessCellRunner:
    """Run each matched cell in a fresh Python interpreter."""

    run_directory: Path
    authorization_snapshot: Path
    matched_manifest_snapshot: Path
    opening_request_snapshot: Path
    base_manifest_snapshot: Path
    base_manifest_path: Path
    project_root: Path
    python_executable: str = sys.executable
    child_module: str = "torch2pc_thesis.stage3b_matched_child"

    def __call__(
        self,
        matched_manifest: Mapping[str, object],
        request: Mapping[str, object],
        base_manifest: Mapping[str, object],
        authorization: Mapping[str, object],
        *,
        output_root: Path,
        cell_id: str,
        device: str,
        dtype: str,
        project_root: Path,
        base_manifest_path: Path,
        torch2pc_dir: Path,
        source_commit: str,
        image_digest: str,
        executor: MatchedCellExecutor | None = None,
    ) -> dict[str, object]:
        if executor is not None:
            raise MatchedCellProcessError(
                "production subprocess cells do not accept an injected executor"
            )
        if project_root.resolve() != self.project_root.resolve():
            raise MatchedCellProcessError("project root differs from frozen child input")
        if base_manifest_path.resolve() != self.base_manifest_path.resolve():
            raise MatchedCellProcessError("base manifest path differs from frozen child input")
        normalized_device, normalized_dtype = _validated_lane(
            device=device,
            dtype=dtype,
        )
        cell = _select_matched_cell(
            matched_manifest,
            request,
            cell_id=cell_id,
        )
        before = _attempt_directories(
            output_root=output_root,
            cell_id=cell_id,
            device=normalized_device,
            dtype=normalized_dtype,
        )
        command = [
            self.python_executable,
            "-m",
            self.child_module,
            "--authorization",
            str(self.authorization_snapshot),
            "--matched-manifest",
            str(self.matched_manifest_snapshot),
            "--opening-request",
            str(self.opening_request_snapshot),
            "--base-manifest",
            str(self.base_manifest_snapshot),
            "--base-manifest-path",
            str(self.base_manifest_path),
            "--project-root",
            str(self.project_root),
            "--output-root",
            str(output_root),
            "--cell-id",
            cell_id,
            "--device",
            normalized_device,
            "--dtype",
            normalized_dtype,
            "--torch2pc-dir",
            str(torch2pc_dir),
            "--source-commit",
            source_commit,
            "--image-digest",
            image_digest,
        ]
        started_at = _utc_now()
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        wait_error: BaseException | None = None
        stdout = ""
        stderr = ""
        try:
            stdout, stderr = process.communicate()
        except BaseException as exc:
            wait_error = exc
            process.terminate()
            try:
                stdout, stderr = process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
        exited_at = _utc_now()
        if process.returncode is None:
            raise MatchedCellProcessError(f"child process has no exit code for {cell_id}")
        child_exit_code = process.returncode
        after = _attempt_directories(
            output_root=output_root,
            cell_id=cell_id,
            device=normalized_device,
            dtype=normalized_dtype,
        )
        created = sorted(after - before)
        attempt_dir = created[0] if len(created) == 1 else None
        terminal: dict[str, object] | None = None
        terminal_path: Path | None = None
        validation_error: str | None = None
        if attempt_dir is None:
            validation_error = (
                "child process must create exactly one attempt directory; "
                f"observed {len(created)} for {cell_id}"
            )
        else:
            try:
                terminal, terminal_path = _validated_child_terminal(
                    attempt_dir=attempt_dir,
                    cell=cell,
                    authorization_token=str(authorization["authorization_token"]),
                    matched_manifest_digest=str(matched_manifest["manifest_digest"]),
                    opening_request_digest=str(request["request_digest"]),
                    source_manifest_digest=str(base_manifest["manifest_digest"]),
                    source_commit=source_commit,
                    device=normalized_device,
                    dtype=normalized_dtype,
                    image_digest=image_digest,
                )
            except MatchedCellProcessError as exc:
                validation_error = str(exc)

        systemic_oom = _systemic_gpu_oom(terminal=terminal, stderr=stderr)
        process_record: dict[str, object] = {
            "schema_version": MATCHED_EXECUTION_SCHEMA_VERSION,
            "campaign_id": STAGE3B_CAMPAIGN_ID,
            "authorization_scope": MATCHED_AUTHORIZATION_SCOPE,
            "execution_scope": MATCHED_EXECUTION_PROCESS_SCOPE,
            "process_isolation_mode": MATCHED_EXECUTION_PROCESS_MODE,
            "cell_id": cell_id,
            "block_id": str(cell["block_id"]),
            "candidate_id": str(cell["candidate_id"]),
            "authorization_token": str(authorization["authorization_token"]),
            "matched_manifest_digest": str(matched_manifest["manifest_digest"]),
            "opening_request_digest": str(request["request_digest"]),
            "source_manifest_digest": str(base_manifest["manifest_digest"]),
            "source_commit": source_commit,
            "device": normalized_device,
            "dtype": normalized_dtype,
            "image_digest": image_digest,
            "parent_pid": os.getpid(),
            "child_pid": process.pid,
            "child_exit_code": child_exit_code,
            "child_started_at": started_at,
            "child_exited_at": exited_at,
            "attempt_directory": str(attempt_dir) if attempt_dir is not None else None,
            "request_record": (
                str(attempt_dir / "request.json") if attempt_dir is not None else None
            ),
            "request_record_sha256": (
                _sha256_file(attempt_dir / "request.json")
                if attempt_dir is not None and (attempt_dir / "request.json").is_file()
                else None
            ),
            "terminal_record": (str(terminal_path) if terminal_path is not None else None),
            "terminal_record_sha256": (
                _sha256_file(terminal_path) if terminal_path is not None else None
            ),
            "terminal_status": (str(terminal.get("status")) if terminal is not None else None),
            "terminal_validation_error": validation_error,
            "systemic_resource_failure": systemic_oom,
            "child_stdout_sha256": _sha256_text(stdout),
            "child_stderr_sha256": _sha256_text(stderr),
            "child_stdout_tail": _text_tail(stdout),
            "child_stderr_tail": _text_tail(stderr),
            "evidence": False,
            "full_lane_complete": False,
            "full_stage3b_campaign_complete": False,
            "results_publication_permitted": False,
            "test_dataset_access": False,
        }
        process_record_path = self.run_directory / "processes" / f"{_identifier()}-{cell_id}.json"
        if process_record_path.exists():
            raise MatchedCellProcessError(
                f"process telemetry already exists: {process_record_path}"
            )
        atomic_write_json(process_record_path, process_record)

        if wait_error is not None:
            raise wait_error
        if validation_error is not None or terminal is None:
            raise MatchedCellProcessError(
                validation_error or f"child terminal validation failed for {cell_id}"
            )
        status = str(terminal["status"])
        if status == "matched_cell_complete" and child_exit_code != 0:
            raise MatchedCellProcessError(
                f"completed child exited with code {child_exit_code}: {cell_id}"
            )
        if status == "matched_cell_failed" and child_exit_code == 0:
            raise MatchedCellProcessError(f"failed child exited successfully: {cell_id}")
        return {
            **terminal,
            "process_isolation": {
                "mode": MATCHED_EXECUTION_PROCESS_MODE,
                "parent_pid": os.getpid(),
                "child_pid": process.pid,
                "child_exit_code": child_exit_code,
                "record_path": str(process_record_path),
                "terminal_record_sha256": process_record["terminal_record_sha256"],
            },
            "systemic_resource_failure": systemic_oom,
        }


def _inspect_attempts(
    *,
    lane_root: Path,
    cell: Mapping[str, object],
    authorization_token: str,
    matched_manifest_digest: str,
    opening_request_digest: str,
    source_manifest_digest: str,
    source_commit: str,
    device: str,
    dtype: str,
    image_digest: str,
) -> _AttemptSummary:
    cell_id = str(cell["cell_id"])
    attempts_root = lane_root / "cells" / cell_id / "attempts"
    if not attempts_root.is_dir():
        return _AttemptSummary()

    attempt_count = 0
    failed_count = 0
    running_count = 0
    matching_success = False
    for attempt_dir in sorted(path for path in attempts_root.iterdir() if path.is_dir()):
        attempt_request = _load_json_object(attempt_dir / "request.json")
        if attempt_request is None or not _request_matches(
            attempt_request,
            cell=cell,
            authorization_token=authorization_token,
            matched_manifest_digest=matched_manifest_digest,
            opening_request_digest=opening_request_digest,
            source_manifest_digest=source_manifest_digest,
            source_commit=source_commit,
            device=device,
            dtype=dtype,
            image_digest=image_digest,
        ):
            continue
        attempt_count += 1
        completed = _load_json_object(attempt_dir / "completed.json")
        failed = _load_json_object(attempt_dir / "failed.json")
        started = _load_json_object(attempt_dir / "started.json")
        if completed is not None and completed.get("status") == "matched_cell_complete":
            matching_success = True
        elif failed is not None and failed.get("status") == "matched_cell_failed":
            failed_count += 1
        elif started is not None and started.get("status") == "matched_cell_running":
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
) -> MatchedCellState:
    if summary.matching_success:
        return "completed"
    if summary.attempt_count >= max_attempts and (summary.running_count or summary.failed_count):
        return "exhausted"
    if summary.running_count:
        return "retryable" if resume else "running"
    if summary.failed_count:
        return "retryable" if retry_failed else "failed"
    return "pending"


def _check_emergency_stop(path: Path) -> None:
    if path.exists():
        raise Stage3BExecutionError(f"matched campaign emergency stop is active: {path}")


def verify_matched_authorized_lane(
    authorization: Mapping[str, object],
    matched_manifest: Mapping[str, object],
    request: Mapping[str, object],
    base_manifest: Mapping[str, object],
    *,
    base_manifest_path: Path,
    project_root: Path,
    torch2pc_dir: Path,
    output_root: Path,
    source_commit: str,
    device: str,
    dtype: str,
    image_digest: str,
    probe: MatchedRuntimeProbe | None = None,
    verifier: AuthorizationVerifier = verify_matched_authorization_for_lane,
) -> dict[str, object]:
    """Verify the frozen matched authorization and ROCm/float32 lane."""

    validate_matched_campaign_authorization(authorization)
    validate_matched_manifest(matched_manifest)
    validate_matched_request(request)
    validate_manifest(base_manifest)
    validate_runner_inputs(matched_manifest, request)
    _matched_protocol(authorization)
    normalized_lane = _validated_lane(
        device=device,
        dtype=dtype,
        allow_engineering_control=probe is not None,
    )
    verification = verifier(
        authorization,
        matched_manifest,
        request,
        base_manifest,
        base_manifest_path=base_manifest_path,
        project_root=project_root,
        torch2pc_dir=torch2pc_dir,
        output_root=output_root,
        source_commit=source_commit,
        image_digest=image_digest,
        probe=probe,
    )
    if verification.get("authorization_verified") is not True:
        raise Stage3BExecutionError("matched lane authorization was not verified")
    if verification.get("execution_permitted") is not True:
        raise Stage3BExecutionError("matched lane execution is not permitted")
    if verification.get("measurements_allowed") is not True:
        raise Stage3BExecutionError("matched lane measurements are not permitted")
    if verification.get("evidence") is not False:
        raise Stage3BExecutionError("matched lane authorization must remain non-evidence")
    if verification.get("results_publication_permitted") is not False:
        raise Stage3BExecutionError("matched lane cannot permit result publication")
    if verification.get("test_dataset_access") is not False:
        raise Stage3BExecutionError("matched lane cannot permit test dataset access")
    if normalized_lane not in MATCHED_CANONICAL_LANES and probe is None:
        raise Stage3BExecutionError("matched production runner rejects engineering-control lanes")
    emergency_stop = Path(str(authorization["emergency_stop_path"]))
    _check_emergency_stop(emergency_stop)
    return verification


def plan_matched_authorized_lane(
    authorization: Mapping[str, object],
    matched_manifest: Mapping[str, object],
    request: Mapping[str, object],
    base_manifest: Mapping[str, object],
    *,
    base_manifest_path: Path,
    project_root: Path,
    output_root: Path,
    device: str,
    dtype: str,
    torch2pc_dir: Path,
    source_commit: str,
    image_digest: str,
    max_attempts: int = MATCHED_EXECUTION_DEFAULT_MAX_ATTEMPTS,
    resume: bool = False,
    retry_failed: bool = False,
    probe: MatchedRuntimeProbe | None = None,
    verifier: AuthorizationVerifier = verify_matched_authorization_for_lane,
) -> MatchedLanePlan:
    """Build a deterministic, resume-aware plan for one matched lane."""

    cells = _matched_cells(matched_manifest, request)
    validate_manifest(base_manifest)
    normalized_device, normalized_dtype = _validated_lane(
        device=device,
        dtype=dtype,
        allow_engineering_control=probe is not None,
    )
    clean_commit = _validated_source_commit(source_commit)
    bounded_attempts = _validated_max_attempts(max_attempts)
    resolved_root = validated_temporary_output_root(output_root)
    verification = verify_matched_authorized_lane(
        authorization,
        matched_manifest,
        request,
        base_manifest,
        base_manifest_path=base_manifest_path,
        project_root=project_root,
        torch2pc_dir=torch2pc_dir,
        output_root=resolved_root,
        source_commit=clean_commit,
        device=normalized_device,
        dtype=normalized_dtype,
        image_digest=image_digest,
        probe=probe,
        verifier=verifier,
    )
    token = str(verification["authorization_token"])
    matched_manifest_digest = str(matched_manifest["manifest_digest"])
    opening_request_digest = str(request["request_digest"])
    source_manifest_digest = str(base_manifest["manifest_digest"])
    normalized_image = str(verification["image_digest"])
    lane_root = _lane_root(
        resolved_root,
        device=normalized_device,
        dtype=normalized_dtype,
    )

    staged: list[tuple[dict[str, object], MatchedCellState, _AttemptSummary]] = []
    for cell in cells:
        summary = _inspect_attempts(
            lane_root=lane_root,
            cell=cell,
            authorization_token=token,
            matched_manifest_digest=matched_manifest_digest,
            opening_request_digest=opening_request_digest,
            source_manifest_digest=source_manifest_digest,
            source_commit=clean_commit,
            device=normalized_device,
            dtype=normalized_dtype,
            image_digest=normalized_image,
        )
        state = _state_from_attempts(
            summary,
            resume=resume,
            retry_failed=retry_failed,
            max_attempts=bounded_attempts,
        )
        staged.append((cell, state, summary))

    selected_ids = tuple(
        str(cell["cell_id"])
        for cell, state, _summary in staged
        if state in {"pending", "retryable"}
    )
    selected_set = set(selected_ids)
    planned = tuple(
        MatchedPlannedCell(
            cell_id=str(cell["cell_id"]),
            block_id=str(cell["block_id"]),
            block_order=int(cast(int, cell["block_order"])),
            candidate_order=int(cast(int, cell["candidate_order"])),
            candidate_id=str(cell["candidate_id"]),
            method=str(cell["method"]),
            depth=int(cast(int, cell["depth"])),
            width=int(cast(int, cell["width"])),
            batch_size=int(cast(int, cell["batch_size"])),
            model_seed=int(cast(int, cell["model_seed"])),
            state=state,
            attempt_count=summary.attempt_count,
            failed_attempt_count=summary.failed_count,
            running_attempt_count=summary.running_count,
            selected_for_execution=str(cell["cell_id"]) in selected_set,
        )
        for cell, state, summary in staged
    )
    return MatchedLanePlan(
        authorization_token=token,
        matched_manifest_digest=matched_manifest_digest,
        opening_request_digest=opening_request_digest,
        source_manifest_digest=source_manifest_digest,
        output_root=str(resolved_root),
        source_commit=clean_commit,
        device=normalized_device,
        dtype=normalized_dtype,
        image_digest=normalized_image,
        max_attempts=bounded_attempts,
        resume=resume,
        retry_failed=retry_failed,
        summary=dict(Counter(cell.state for cell in planned)),
        selected_cell_ids=selected_ids,
        cells=planned,
    )


def _process_is_alive(pid: int) -> bool:
    if pid < 1:
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
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        payload = _load_json_object(path)
        pid = int(cast(int, payload.get("pid", -1))) if payload is not None else -1
        if _process_is_alive(pid):
            raise Stage3BExecutionError(f"matched lane lock is active: {path}") from None
        if not resume:
            raise Stage3BExecutionError(
                "stale matched lane lock requires explicit --resume"
            ) from None
        path.unlink(missing_ok=True)
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        payload = {
            "pid": os.getpid(),
            "hostname": socket.gethostname(),
            "created_at": _utc_now(),
        }
        os.write(descriptor, (_canonical_json(payload) + "\n").encode("utf-8"))
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _resolve_device_dtype(
    *,
    device: str,
    dtype: str,
    allow_engineering_control: bool = False,
) -> tuple[torch.device, torch.dtype]:
    normalized_device, normalized_dtype = _validated_lane(
        device=device,
        dtype=dtype,
        allow_engineering_control=allow_engineering_control,
    )
    if normalized_device == "rocm":
        if not torch.cuda.is_available() or not getattr(torch.version, "hip", None):
            raise Stage3BExecutionError("matched ROCm execution requires an available HIP device")
        resolved_device = torch.device("cuda")
    else:
        resolved_device = torch.device("cpu")
    resolved_dtype = torch.float32 if normalized_dtype == "float32" else torch.float64
    return resolved_device, resolved_dtype


def _tensor_digest(tensor: Tensor) -> str:
    value = tensor.detach().cpu().contiguous()
    digest = hashlib.sha256()
    digest.update(str(value.dtype).encode("utf-8"))
    digest.update(str(tuple(value.shape)).encode("utf-8"))
    digest.update(value.numpy().tobytes())
    return digest.hexdigest()


def _state_dict_digest(state: Mapping[str, Tensor]) -> str:
    digest = hashlib.sha256()
    for name in sorted(state):
        digest.update(name.encode("utf-8"))
        digest.update(_tensor_digest(state[name]).encode("utf-8"))
    return digest.hexdigest()


def _aggregate_regions(
    records: Sequence[RegionMeasurement],
    *,
    candidate_id: str,
    repetition: int,
    step: int,
    method: str,
) -> tuple[RegionMeasurement, ...]:
    grouped: dict[str, list[RegionMeasurement]] = defaultdict(list)
    for record in records:
        grouped[record.region].append(record)
    if set(grouped) != STAGE3_PROFILE_REGIONS:
        raise Stage3BExecutionError(
            "matched measured gate did not expose all preregistered regions"
        )
    aggregated: list[RegionMeasurement] = []
    for region in sorted(grouped):
        values = grouped[region]
        aggregated.append(
            RegionMeasurement(
                candidate_id=candidate_id,
                method=method,
                repetition=repetition,
                step=step,
                region=region,
                host_time_us=sum(value.host_time_us for value in values),
                device_time_us=sum(value.device_time_us for value in values),
                peak_allocated_bytes=max(value.peak_allocated_bytes for value in values),
                peak_reserved_bytes=max(value.peak_reserved_bytes for value in values),
                vjp_calls=sum(value.vjp_calls for value in values),
                synchronization_points=sum(value.synchronization_points for value in values),
                saved_tensor_bytes=sum(value.saved_tensor_bytes for value in values),
                actual_inference_steps=sum(value.actual_inference_steps for value in values),
                non_finite_events=sum(value.non_finite_events for value in values),
            )
        )
    return tuple(aggregated)


def _execute_real_matched_cell(context: MatchedCellContext) -> MatchedCellResult:
    cell = context.cell
    candidate_id = str(cell["candidate_id"])
    adapter = adapter_for_candidate(candidate_id)
    method_text = str(cell["method"])
    if method_text not in MATCHED_EXECUTION_INFERENCE_STEPS:
        raise Stage3BExecutionError(f"unsupported matched method: {method_text}")
    method = cast(MethodName, method_text)
    depth = int(cast(int, cell["depth"]))
    width = int(cast(int, cell["width"]))
    batch_size = int(cast(int, cell["batch_size"]))
    model_seed = int(cast(int, cell["model_seed"]))
    block_id = str(cell["block_id"])
    architecture = f"mlp_d{depth}_w{width}"

    # Resolve candidate code before resetting the shared block state. Lazy
    # imports must not be able to perturb the model or inference RNG streams.
    pc_infer = load_candidate_pc_infer(candidate_id, context.torch2pc_dir)
    set_global_seed(model_seed, deterministic=True, warn_only=True)
    model = build_model(architecture, 10).to(dtype=context.dtype)
    model_state_sha256 = _state_dict_digest(cast(Mapping[str, Tensor], model.state_dict()))
    minibatch_seed = stable_int_seed(
        STAGE3B_CAMPAIGN_ID,
        block_id,
        "matched_synthetic_minibatch",
    )
    generator = torch.Generator(device="cpu")
    generator.manual_seed(minibatch_seed)
    inputs = torch.randn(
        (batch_size, 1, 28, 28),
        generator=generator,
        dtype=context.dtype,
    )
    targets = torch.randint(
        low=0,
        high=10,
        size=(batch_size,),
        generator=generator,
        dtype=torch.int64,
    )

    def optimizer_factory(candidate: nn.Module) -> torch.optim.Optimizer:
        return torch.optim.SGD(
            candidate.parameters(),
            lr=MATCHED_EXECUTION_LEARNING_RATE,
        )

    inference_steps = MATCHED_EXECUTION_INFERENCE_STEPS[method]
    gate_config = B0GateConfig(
        method=method,
        torch2pc_method=torch2pc_method_label(method),
        eta=MATCHED_EXECUTION_ETA,
        inference_steps=inference_steps,
        device=context.device,
        dtype=context.dtype,
    )

    region_records: list[RegionMeasurement] = []
    composite_records: list[dict[str, object]] = []
    integrity_records: list[dict[str, object]] = []
    warmup_gate_count = 0
    measured_gate_count = 0

    for protocol_step in iter_protocol_steps(context.protocol):
        _check_emergency_stop(context.emergency_stop_path)
        report = run_b0_non_perturbation_gate(
            model=model,
            optimizer_factory=optimizer_factory,
            loss_fn=nn.CrossEntropyLoss(),
            inputs=inputs,
            targets=targets,
            pc_infer=pc_infer,
            config=gate_config,
        )
        if not report.full_preregistered_gate_complete:
            raise Stage3BExecutionError("matched non-perturbation gate did not pass")
        if not protocol_step.measured:
            warmup_gate_count += 1
            continue

        measured_gate_count += 1
        aggregated = _aggregate_regions(
            report.region_measurements,
            candidate_id=candidate_id,
            repetition=protocol_step.repetition,
            step=protocol_step.step,
            method=method,
        )
        region_records.extend(aggregated)
        composite_records.append(
            {
                **report.measurement.to_record(),
                # The inherited B0 gate may label its aggregate with the
                # baseline candidate. The matched executor owns candidate
                # identity and must override that inherited label.
                "candidate_id": candidate_id,
                "repetition": protocol_step.repetition,
                "step": protocol_step.step,
            }
        )
        integrity_records.append(
            {
                "candidate_id": candidate_id,
                "repetition": protocol_step.repetition,
                "step": protocol_step.step,
                "comparison_count": len(report.comparisons),
                "minimum_cosine": min(comparison.cosine for comparison in report.comparisons),
                "maximum_relative_l2": max(
                    comparison.relative_l2 for comparison in report.comparisons
                ),
                "all_finite": all(comparison.finite for comparison in report.comparisons),
                "observed_inference_steps": report.observed_inference_steps,
                "configured_inference_steps": report.configured_inference_steps,
                "internal_region_attribution_ready": (report.internal_region_attribution_ready),
                "passed": report.full_preregistered_gate_complete,
            }
        )

    validate_profile_completeness(
        region_records,
        context.protocol,
        required_regions=MATCHED_EXECUTION_REQUIRED_REGIONS,
    )
    expected_warmup = context.protocol.warmup_steps * context.protocol.repetitions
    expected_measured = context.protocol.measured_steps * context.protocol.repetitions
    if warmup_gate_count != expected_warmup or measured_gate_count != expected_measured:
        raise Stage3BExecutionError("matched protocol gate counts are incomplete")

    torch2pc_source = context.torch2pc_dir / "TorchSeq2PC.py"
    return MatchedCellResult(
        resolved_config={
            "architecture": architecture,
            "num_classes": 10,
            "depth": depth,
            "width": width,
            "batch_size": batch_size,
            "model_seed": model_seed,
            "minibatch_seed": minibatch_seed,
            "block_id": block_id,
            "block_order": int(cast(int, cell["block_order"])),
            "candidate_id": candidate_id,
            "candidate_order": int(cast(int, cell["candidate_order"])),
            "adapter_module": adapter.module_name,
            "adapter_loader": adapter.loader_name,
            "method": method,
            "torch2pc_method": torch2pc_method_label(method),
            "eta": MATCHED_EXECUTION_ETA,
            "inference_steps": inference_steps,
            "optimizer": "SGD",
            "learning_rate": MATCHED_EXECUTION_LEARNING_RATE,
            "matched_protocol": dict(MATCHED_EXECUTION_FULL_PROTOCOL),
            "required_regions": list(MATCHED_EXECUTION_REQUIRED_REGIONS),
            "state_reset_policy": MATCHED_RUNNER_STATE_RESET_POLICY,
            "state_reconstruction": MATCHED_EXECUTION_STATE_RECONSTRUCTION,
        },
        environment={
            "project_source_commit": context.source_commit,
            "matched_manifest_digest": context.matched_manifest_digest,
            "opening_request_digest": context.opening_request_digest,
            "source_manifest_digest": context.source_manifest_digest,
            "authorization_token": context.authorization_token,
            "python_version": sys.version,
            "pytorch_version": torch.__version__,
            "hip_version": getattr(torch.version, "hip", None),
            "requested_device": context.requested_device,
            "resolved_device_type": context.device.type,
            "device_name": (
                torch.cuda.get_device_name(context.device)
                if context.device.type == "cuda"
                else "cpu"
            ),
            "dtype": context.dtype_name,
            "platform": platform.platform(),
            "hostname": socket.gethostname(),
            "container_image_digest": context.image_digest,
            "torch2pc_path": str(context.torch2pc_dir),
            "torch2pc_source_sha256": _sha256_file(torch2pc_source),
            "model_state_sha256": model_state_sha256,
            "synthetic_inputs_sha256": _tensor_digest(inputs),
            "synthetic_targets_sha256": _tensor_digest(targets),
        },
        measurements={
            "status": "matched_cell_complete",
            "execution_scope": MATCHED_EXECUTION_CELL_SCOPE,
            "candidate_id": candidate_id,
            "evidence": False,
            "full_cell_complete": True,
            "full_lane_complete": False,
            "full_stage3b_campaign_complete": False,
            "results_publication_permitted": False,
            "test_dataset_access": False,
            "warmup_gate_count": warmup_gate_count,
            "measured_gate_count": measured_gate_count,
            "region_record_count": len(region_records),
            "expected_region_record_count": (
                context.protocol.repetitions
                * context.protocol.measured_steps
                * len(MATCHED_EXECUTION_REQUIRED_REGIONS)
            ),
            "region_measurements": [record.to_record() for record in region_records],
            "composite_measurements": composite_records,
            "integrity_measurements": integrity_records,
            "validation": {
                "dataset": "synthetic_scaling_family",
                "test_loader_created": False,
                "test_evaluated": False,
                "profile_completeness_validated": True,
                "all_non_perturbation_gates_passed": True,
                "fresh_process_per_candidate": True,
                "block_state_reconstructed_from_shared_seeds": True,
            },
        },
    )


def execute_matched_cell(
    matched_manifest: Mapping[str, object],
    request: Mapping[str, object],
    base_manifest: Mapping[str, object],
    authorization: Mapping[str, object],
    *,
    output_root: Path,
    cell_id: str,
    device: str,
    dtype: str,
    project_root: Path,
    base_manifest_path: Path,
    torch2pc_dir: Path,
    source_commit: str,
    image_digest: str,
    executor: MatchedCellExecutor | None = None,
) -> dict[str, object]:
    """Execute one immutable matched cell attempt."""

    validate_matched_campaign_authorization(authorization)
    validate_matched_manifest(matched_manifest)
    validate_matched_request(request)
    validate_manifest(base_manifest)
    validate_runner_inputs(matched_manifest, request)
    resolved_root = validated_temporary_output_root(output_root)
    normalized_device, normalized_dtype = _validated_lane(
        device=device,
        dtype=dtype,
        allow_engineering_control=executor is not None,
    )
    resolved_device, resolved_dtype = _resolve_device_dtype(
        device=normalized_device,
        dtype=normalized_dtype,
        allow_engineering_control=executor is not None,
    )
    clean_commit = _validated_source_commit(source_commit)
    cell = _select_matched_cell(
        matched_manifest,
        request,
        cell_id=cell_id,
    )
    protocol = _matched_protocol(authorization)
    token = str(authorization["authorization_token"])
    matched_manifest_digest = str(matched_manifest["manifest_digest"])
    opening_request_digest = str(request["request_digest"])
    source_manifest_digest = str(base_manifest["manifest_digest"])
    emergency_stop = Path(str(authorization["emergency_stop_path"]))
    _check_emergency_stop(emergency_stop)
    freeze_record = cast(Mapping[str, object], authorization["freeze_record"])
    if project_root.expanduser().resolve() != Path(str(freeze_record["project_root"])).resolve():
        raise Stage3BExecutionError("matched cell project root differs from freeze")
    if (
        base_manifest_path.expanduser().resolve()
        != Path(str(freeze_record["base_manifest_path"])).resolve()
    ):
        raise Stage3BExecutionError("matched cell base manifest path differs from freeze")
    lane_root = _lane_root(
        resolved_root,
        device=normalized_device,
        dtype=normalized_dtype,
    )
    attempt_id = _identifier()
    attempt_dir = lane_root / "cells" / cell_id / "attempts" / attempt_id
    attempt_dir.mkdir(parents=True, exist_ok=False)
    attempt_request: dict[str, object] = {
        "schema_version": MATCHED_EXECUTION_SCHEMA_VERSION,
        "campaign_id": STAGE3B_CAMPAIGN_ID,
        "authorization_scope": MATCHED_AUTHORIZATION_SCOPE,
        "execution_scope": MATCHED_EXECUTION_CELL_SCOPE,
        "attempt_id": attempt_id,
        "cell_id": cell_id,
        "block_id": str(cell["block_id"]),
        "block_order": int(cast(int, cell["block_order"])),
        "candidate_id": str(cell["candidate_id"]),
        "candidate_order": int(cast(int, cell["candidate_order"])),
        "method": str(cell["method"]),
        "authorization_token": token,
        "matched_manifest_digest": matched_manifest_digest,
        "opening_request_digest": opening_request_digest,
        "source_manifest_digest": source_manifest_digest,
        "source_commit": clean_commit,
        "device": normalized_device,
        "dtype": normalized_dtype,
        "image_digest": image_digest,
        "matched_protocol": dict(MATCHED_EXECUTION_FULL_PROTOCOL),
        "state_reset_policy": MATCHED_RUNNER_STATE_RESET_POLICY,
        "state_reconstruction": MATCHED_EXECUTION_STATE_RECONSTRUCTION,
        "evidence": False,
        "full_cell_complete": False,
        "full_lane_complete": False,
        "full_stage3b_campaign_complete": False,
        "results_publication_permitted": False,
        "test_dataset_access": False,
    }
    atomic_write_json(attempt_dir / "request.json", attempt_request)
    atomic_write_json(
        attempt_dir / "started.json",
        {
            **attempt_request,
            "status": "matched_cell_running",
            "started_at": _utc_now(),
        },
    )
    context = MatchedCellContext(
        cell=cell,
        authorization_token=token,
        matched_manifest_digest=matched_manifest_digest,
        opening_request_digest=opening_request_digest,
        source_manifest_digest=source_manifest_digest,
        output_root=resolved_root,
        attempt_directory=attempt_dir,
        device=resolved_device,
        requested_device=normalized_device,
        dtype=resolved_dtype,
        dtype_name=normalized_dtype,
        torch2pc_dir=torch2pc_dir.expanduser().resolve(),
        source_commit=clean_commit,
        image_digest=image_digest,
        emergency_stop_path=emergency_stop,
        protocol=protocol,
    )
    selected_executor = executor or _execute_real_matched_cell
    try:
        result = selected_executor(context)
        atomic_write_json(
            attempt_dir / "resolved-config.json",
            dict(result.resolved_config),
        )
        atomic_write_json(
            attempt_dir / "environment.json",
            dict(result.environment),
        )
        atomic_write_json(
            attempt_dir / "measurements.json",
            dict(result.measurements),
        )
        completed = {
            **attempt_request,
            "status": "matched_cell_complete",
            "full_cell_complete": True,
            "completed_at": _utc_now(),
            "attempt_directory": str(attempt_dir),
        }
        atomic_write_json(attempt_dir / "completed.json", completed)
        return completed
    except Exception as exc:
        failed = {
            **attempt_request,
            "status": "matched_cell_failed",
            "failed_at": _utc_now(),
            "attempt_directory": str(attempt_dir),
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
        }
        atomic_write_json(attempt_dir / "failed.json", failed)
        _append_jsonl(
            resolved_root / "matched" / "failure-ledger.jsonl",
            failed,
        )
        raise


def _write_lane_state(
    path: Path,
    *,
    plan: MatchedLanePlan,
    status: str,
    completed_cell_count: int,
    failed_cell_count: int,
) -> None:
    atomic_write_json(
        path,
        {
            "schema_version": MATCHED_EXECUTION_SCHEMA_VERSION,
            "campaign_id": STAGE3B_CAMPAIGN_ID,
            "authorization_scope": MATCHED_AUTHORIZATION_SCOPE,
            "execution_scope": MATCHED_EXECUTION_SCOPE,
            "status": status,
            "authorization_token": plan.authorization_token,
            "matched_manifest_digest": plan.matched_manifest_digest,
            "opening_request_digest": plan.opening_request_digest,
            "source_manifest_digest": plan.source_manifest_digest,
            "source_commit": plan.source_commit,
            "device": plan.device,
            "dtype": plan.dtype,
            "image_digest": plan.image_digest,
            "matched_cell_count": len(plan.cells),
            "completed_cell_count": completed_cell_count,
            "failed_cell_count": failed_cell_count,
            "evidence": False,
            "full_stage3b_campaign_complete": False,
            "results_publication_permitted": False,
            "test_dataset_access": False,
            "updated_at": _utc_now(),
        },
    )


def execute_matched_authorized_lane(
    authorization: Mapping[str, object],
    matched_manifest: Mapping[str, object],
    request: Mapping[str, object],
    base_manifest: Mapping[str, object],
    *,
    base_manifest_path: Path,
    project_root: Path,
    output_root: Path,
    device: str,
    dtype: str,
    torch2pc_dir: Path,
    source_commit: str,
    image_digest: str,
    max_attempts: int = MATCHED_EXECUTION_DEFAULT_MAX_ATTEMPTS,
    resume: bool = False,
    retry_failed: bool = False,
    probe: MatchedRuntimeProbe | None = None,
    verifier: AuthorizationVerifier = verify_matched_authorization_for_lane,
    cell_runner: MatchedCellRunner | None = None,
    executor: MatchedCellExecutor | None = None,
) -> dict[str, object]:
    """Execute or resume all eligible cells in one authorized matched lane."""

    _validated_lane(
        device=device,
        dtype=dtype,
        allow_engineering_control=probe is not None and executor is not None,
    )
    plan = plan_matched_authorized_lane(
        authorization,
        matched_manifest,
        request,
        base_manifest,
        base_manifest_path=base_manifest_path,
        project_root=project_root,
        output_root=output_root,
        device=device,
        dtype=dtype,
        torch2pc_dir=torch2pc_dir,
        source_commit=source_commit,
        image_digest=image_digest,
        max_attempts=max_attempts,
        resume=resume,
        retry_failed=retry_failed,
        probe=probe,
        verifier=verifier,
    )
    states = Counter(cell.state for cell in plan.cells)
    if states["running"]:
        raise Stage3BExecutionError("matched lane contains interrupted attempts; use --resume")
    if states["failed"]:
        raise Stage3BExecutionError("matched lane contains failed attempts; use --retry-failed")
    if states["exhausted"]:
        raise Stage3BExecutionError(
            "matched lane contains exhausted cells; inspect failure records"
        )

    resolved_root = Path(plan.output_root)
    lane_root = _lane_root(
        resolved_root,
        device=plan.device,
        dtype=plan.dtype,
    )
    lock_path = (
        resolved_root
        / "matched"
        / "locks"
        / f"{_lane_name(device=plan.device, dtype=plan.dtype)}.lock"
    )
    _acquire_lane_lock(lock_path, resume=resume)
    run_id = _identifier()
    run_dir = lane_root / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    journal = resolved_root / "matched" / "campaign-journal.jsonl"
    lane_state = lane_root / "lane-state.json"
    production_process_isolation = cell_runner is None and probe is None and executor is None
    run_request: dict[str, object] = {
        "schema_version": MATCHED_EXECUTION_SCHEMA_VERSION,
        "campaign_id": STAGE3B_CAMPAIGN_ID,
        "authorization_scope": MATCHED_AUTHORIZATION_SCOPE,
        "execution_scope": MATCHED_EXECUTION_SCOPE,
        "run_id": run_id,
        "authorization_token": plan.authorization_token,
        "matched_manifest_digest": plan.matched_manifest_digest,
        "opening_request_digest": plan.opening_request_digest,
        "source_manifest_digest": plan.source_manifest_digest,
        "source_commit": plan.source_commit,
        "device": plan.device,
        "dtype": plan.dtype,
        "image_digest": plan.image_digest,
        "matched_protocol": dict(MATCHED_EXECUTION_FULL_PROTOCOL),
        "state_reset_policy": MATCHED_RUNNER_STATE_RESET_POLICY,
        "state_reconstruction": MATCHED_EXECUTION_STATE_RECONSTRUCTION,
        "selected_cell_ids": list(plan.selected_cell_ids),
        "resume": resume,
        "retry_failed": retry_failed,
        "max_attempts": max_attempts,
        "process_isolation_mode": (
            MATCHED_EXECUTION_PROCESS_MODE if production_process_isolation else None
        ),
        "evidence": False,
        "full_lane_complete": False,
        "full_stage3b_campaign_complete": False,
        "results_publication_permitted": False,
        "test_dataset_access": False,
    }
    atomic_write_json(run_dir / "request.json", run_request)
    atomic_write_json(run_dir / "plan.json", plan.to_record())
    selected_cell_runner = cell_runner
    if selected_cell_runner is None:
        if probe is not None or executor is not None:
            selected_cell_runner = execute_matched_cell
        else:
            child_inputs = run_dir / "child-inputs"
            authorization_snapshot = child_inputs / "authorization.json"
            matched_manifest_snapshot = child_inputs / "matched-manifest.json"
            opening_request_snapshot = child_inputs / "opening-request.json"
            base_manifest_snapshot = child_inputs / "base-manifest.json"
            atomic_write_json(authorization_snapshot, dict(authorization))
            atomic_write_json(matched_manifest_snapshot, dict(matched_manifest))
            atomic_write_json(opening_request_snapshot, dict(request))
            atomic_write_json(base_manifest_snapshot, dict(base_manifest))
            selected_cell_runner = MatchedSubprocessCellRunner(
                run_directory=run_dir,
                authorization_snapshot=authorization_snapshot,
                matched_manifest_snapshot=matched_manifest_snapshot,
                opening_request_snapshot=opening_request_snapshot,
                base_manifest_snapshot=base_manifest_snapshot,
                base_manifest_path=base_manifest_path.expanduser().resolve(),
                project_root=project_root.expanduser().resolve(),
            )
    started = {
        **run_request,
        "status": "matched_lane_running",
        "started_at": _utc_now(),
    }
    atomic_write_json(run_dir / "started.json", started)
    _append_jsonl(journal, started)
    _write_lane_state(
        lane_state,
        plan=plan,
        status="matched_lane_running",
        completed_cell_count=states["completed"],
        failed_cell_count=0,
    )

    results: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []
    systemic_stop: dict[str, object] | None = None
    emergency_stop = Path(str(authorization["emergency_stop_path"]))
    try:
        for cell_id in plan.selected_cell_ids:
            _check_emergency_stop(emergency_stop)
            try:
                result = selected_cell_runner(
                    matched_manifest,
                    request,
                    base_manifest,
                    authorization,
                    output_root=resolved_root,
                    cell_id=cell_id,
                    device=plan.device,
                    dtype=plan.dtype,
                    project_root=project_root,
                    base_manifest_path=base_manifest_path,
                    torch2pc_dir=torch2pc_dir,
                    source_commit=plan.source_commit,
                    image_digest=plan.image_digest,
                    executor=executor,
                )
                result_record = dict(result)
                result_status = result_record.get("status")
                if result_status == "matched_cell_complete":
                    results.append(result_record)
                    _append_jsonl(
                        journal,
                        {
                            "run_id": run_id,
                            "status": "matched_cell_complete",
                            "cell_id": cell_id,
                            "candidate_id": result_record.get("candidate_id"),
                            "attempt_id": result_record.get("attempt_id"),
                            "device": plan.device,
                            "dtype": plan.dtype,
                            "process_isolation": result_record.get("process_isolation"),
                            "recorded_at": _utc_now(),
                        },
                    )
                    continue
                if result_status != "matched_cell_failed":
                    raise MatchedCellProcessError(
                        f"cell runner returned invalid status for {cell_id}: {result_status}"
                    )
                failure = {
                    "cell_id": cell_id,
                    "candidate_id": result_record.get("candidate_id"),
                    "status": "matched_cell_failed",
                    "attempt_id": result_record.get("attempt_id"),
                    "attempt_directory": result_record.get("attempt_directory"),
                    "exception_type": result_record.get("exception_type"),
                    "exception_message": result_record.get("exception_message"),
                    "process_isolation": result_record.get("process_isolation"),
                    "systemic_resource_failure": bool(
                        result_record.get("systemic_resource_failure")
                    ),
                }
                failures.append(failure)
                _append_jsonl(
                    journal,
                    {
                        "run_id": run_id,
                        "device": plan.device,
                        "dtype": plan.dtype,
                        "recorded_at": _utc_now(),
                        **failure,
                    },
                )
                if failure["systemic_resource_failure"]:
                    systemic_stop = {
                        "reason": "systemic_gpu_out_of_memory",
                        "cell_id": cell_id,
                        "candidate_id": failure["candidate_id"],
                        "attempt_id": failure["attempt_id"],
                        "exception_type": failure["exception_type"],
                        "exception_message": failure["exception_message"],
                        "process_isolation": failure["process_isolation"],
                    }
                    break
            except MatchedCellProcessError:
                raise
            except Exception as exc:
                failure = {
                    "cell_id": cell_id,
                    "status": "matched_cell_failed",
                    "exception_type": type(exc).__name__,
                    "exception_message": str(exc),
                }
                failures.append(failure)
                _append_jsonl(
                    journal,
                    {
                        "run_id": run_id,
                        "device": plan.device,
                        "dtype": plan.dtype,
                        "recorded_at": _utc_now(),
                        **failure,
                    },
                )

        final_plan = plan_matched_authorized_lane(
            authorization,
            matched_manifest,
            request,
            base_manifest,
            base_manifest_path=base_manifest_path,
            project_root=project_root,
            output_root=resolved_root,
            device=plan.device,
            dtype=plan.dtype,
            torch2pc_dir=torch2pc_dir,
            source_commit=plan.source_commit,
            image_digest=plan.image_digest,
            max_attempts=max_attempts,
            resume=False,
            retry_failed=False,
            probe=probe,
            verifier=verifier,
        )
        final_states = Counter(cell.state for cell in final_plan.cells)
        lane_complete = final_states["completed"] == MATCHED_PROFILING_EXPECTED_CELL_COUNT
        status = "matched_lane_complete" if lane_complete else "matched_lane_incomplete"
        payload = {
            **run_request,
            "status": status,
            "execution_performed": bool(plan.selected_cell_ids),
            "executed_cell_count": len(results) + len(failures),
            "completed_this_run_count": len(results),
            "failed_this_run_count": len(failures),
            "completed_cell_count": final_states["completed"],
            "remaining_cell_count": (
                MATCHED_PROFILING_EXPECTED_CELL_COUNT - final_states["completed"]
            ),
            "results": results,
            "failures": failures,
            "stopped_early": systemic_stop is not None,
            "systemic_stop": systemic_stop,
            "full_lane_complete": lane_complete,
            "full_stage3b_campaign_complete": False,
            "completed_at": _utc_now(),
            "run_directory": str(run_dir),
        }
        atomic_write_json(run_dir / "results.json", payload)
        terminal_name = "completed.json" if lane_complete else "failed.json"
        atomic_write_json(run_dir / terminal_name, payload)
        _append_jsonl(journal, payload)
        _write_lane_state(
            lane_state,
            plan=final_plan,
            status=status,
            completed_cell_count=final_states["completed"],
            failed_cell_count=final_states["failed"] + final_states["exhausted"],
        )
        return payload
    except Exception as exc:
        failed = {
            **run_request,
            "status": "matched_lane_aborted",
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "aborted_at": _utc_now(),
            "run_directory": str(run_dir),
        }
        atomic_write_json(run_dir / "failed.json", failed)
        _append_jsonl(journal, failed)
        _write_lane_state(
            lane_state,
            plan=plan,
            status="matched_lane_aborted",
            completed_cell_count=states["completed"] + len(results),
            failed_cell_count=len(failures),
        )
        raise
    finally:
        lock_path.unlink(missing_ok=True)
