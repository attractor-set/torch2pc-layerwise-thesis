"""Execution-readiness primitives for the preregistered Stage 3B matrix."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Final, Literal, cast

STAGE3B_EXECUTION_SCHEMA_VERSION: Final[int] = 1
STAGE3B_CAMPAIGN_ID: Final[str] = "stage3b-profiling-locality-v1"
STAGE3B_PREREGISTRATION_TAG: Final[str] = "stage3b-profiling-prereg-v1"
STAGE3B_BOUNDARIES_TAG: Final[str] = "stage3b-pcinfer-boundaries-v1"
STAGE3B_TORCH2PC_COMMIT: Final[str] = "b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4"
STAGE3B_MANIFEST_RELATIVE_PATH: Final[Path] = Path(
    "experiments/planned/STAGE3B-EXECUTION-MANIFEST.json"
)

CANDIDATE_METHODS: Final[dict[str, tuple[str, ...]]] = {
    "stage2_baseline": ("fixedpred", "strict"),
    "fixedpred_finite_step_control": ("fixedpred",),
    "isolated_layer_vjp": ("fixedpred", "strict"),
    "composite_vjp": ("fixedpred", "strict"),
}
CANDIDATE_IDS: Final[tuple[str, ...]] = tuple(CANDIDATE_METHODS)
METHOD_CANDIDATES: Final[dict[str, tuple[str, ...]]] = {
    "fixedpred": (
        "stage2_baseline",
        "fixedpred_finite_step_control",
        "isolated_layer_vjp",
        "composite_vjp",
    ),
    "strict": (
        "stage2_baseline",
        "isolated_layer_vjp",
        "composite_vjp",
    ),
}
CANDIDATE_GATE_STATUS: Final[dict[str, str]] = {
    "stage2_baseline": "b0_region_gate_passed_smoke_only",
    "fixedpred_finite_step_control": "blocked_pending_a0_endpoint_gate",
    "isolated_layer_vjp": "blocked_pending_b1_full_trajectory_gate",
    "composite_vjp": "blocked_pending_b2_full_trajectory_gate",
}
DEPTHS: Final[tuple[int, ...]] = (4, 8, 16, 32)
WIDTHS: Final[tuple[int, ...]] = (64, 256)
BATCH_SIZES: Final[tuple[int, ...]] = (64, 256)
MODEL_SEEDS: Final[tuple[int, ...]] = (70, 71, 72)
WARMUP_STEPS: Final[int] = 20
MEASURED_STEPS: Final[int] = 50
REPETITIONS: Final[int] = 5

CellDisposition = Literal[
    "blocked_candidate_gate",
    "pending_smoke",
    "resume_incomplete",
    "retry_failed",
    "skip_completed",
]


class Stage3BExecutionError(RuntimeError):
    """Raised when Stage 3B execution-readiness invariants are violated."""


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class _Block:
    method: str
    depth: int
    width: int
    batch_size: int
    model_seed: int
    block_id: str
    hash_value: str


@dataclass(frozen=True)
class Stage3BCell:
    """One deterministic cell in the 336-cell Stage 3B matrix."""

    cell_id: str
    block_id: str
    block_order: int
    candidate_order: int
    candidate_id: str
    candidate_gate_status: str
    method: str
    depth: int
    width: int
    batch_size: int
    model_seed: int

    def to_record(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PlannedCell:
    """Dry-run disposition for one Stage 3B cell."""

    cell_id: str
    candidate_id: str
    method: str
    disposition: CellDisposition
    status_path: str

    def to_record(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DryRunPlan:
    """Validated dry-run plan without executing a profiling cell."""

    manifest_digest: str
    output_root: str
    selected_cell_count: int
    summary: dict[str, int]
    cells: tuple[PlannedCell, ...]

    def to_record(self) -> dict[str, object]:
        return {
            "schema_version": STAGE3B_EXECUTION_SCHEMA_VERSION,
            "campaign_id": STAGE3B_CAMPAIGN_ID,
            "evidence": False,
            "dry_run": True,
            "execution_performed": False,
            "manifest_digest": self.manifest_digest,
            "output_root": self.output_root,
            "selected_cell_count": self.selected_cell_count,
            "summary": dict(sorted(self.summary.items())),
            "cells": [cell.to_record() for cell in self.cells],
        }


def _block_payload(*, method: str, depth: int, width: int, batch_size: int, model_seed: int) -> dict[str, object]:
    return {
        "campaign_id": STAGE3B_CAMPAIGN_ID,
        "method": method,
        "depth": depth,
        "width": width,
        "batch_size": batch_size,
        "model_seed": model_seed,
    }


def _cell_payload(*, block_id: str, candidate_id: str) -> dict[str, object]:
    return {
        "campaign_id": STAGE3B_CAMPAIGN_ID,
        "block_id": block_id,
        "candidate_id": candidate_id,
        "protocol": {
            "warmup_steps": WARMUP_STEPS,
            "measured_steps": MEASURED_STEPS,
            "repetitions": REPETITIONS,
        },
    }


def _rotate(values: tuple[str, ...], offset: int) -> tuple[str, ...]:
    return values[offset:] + values[:offset]


def generate_cells() -> tuple[Stage3BCell, ...]:
    """Generate all cells with exactly counterbalanced hash-ranked candidate order."""
    blocks_by_method: dict[str, list[_Block]] = {
        method: [] for method in METHOD_CANDIDATES
    }
    for method in METHOD_CANDIDATES:
        for depth in DEPTHS:
            for width in WIDTHS:
                for batch_size in BATCH_SIZES:
                    for model_seed in MODEL_SEEDS:
                        payload = _block_payload(
                            method=method,
                            depth=depth,
                            width=width,
                            batch_size=batch_size,
                            model_seed=model_seed,
                        )
                        block_id = f"s3b-block-{_digest(payload)[:20]}"
                        blocks_by_method[method].append(
                            _Block(
                                method=method,
                                depth=depth,
                                width=width,
                                batch_size=batch_size,
                                model_seed=model_seed,
                                block_id=block_id,
                                hash_value=_digest(payload),
                            )
                        )

    cells: list[Stage3BCell] = []
    global_block_order = 0
    for method in sorted(blocks_by_method):
        candidates = METHOD_CANDIDATES[method]
        ranked_blocks = sorted(
            blocks_by_method[method], key=lambda block: block.hash_value
        )
        order_by_block = {
            block.block_id: _rotate(candidates, rank % len(candidates))
            for rank, block in enumerate(ranked_blocks)
        }
        canonical_blocks = sorted(
            blocks_by_method[method],
            key=lambda block: (
                block.depth,
                block.width,
                block.batch_size,
                block.model_seed,
            ),
        )
        for block in canonical_blocks:
            block_id = block.block_id
            for candidate_order, candidate_id in enumerate(order_by_block[block_id]):
                cell_id = f"s3b-cell-{_digest(_cell_payload(block_id=block_id, candidate_id=candidate_id))[:20]}"
                cells.append(
                    Stage3BCell(
                        cell_id=cell_id,
                        block_id=block_id,
                        block_order=global_block_order,
                        candidate_order=candidate_order,
                        candidate_id=candidate_id,
                        candidate_gate_status=CANDIDATE_GATE_STATUS[candidate_id],
                        method=method,
                        depth=block.depth,
                        width=block.width,
                        batch_size=block.batch_size,
                        model_seed=block.model_seed,
                    )
                )
            global_block_order += 1
    return tuple(cells)


def _manifest_without_digest() -> dict[str, object]:
    cells = generate_cells()
    return {
        "schema_version": STAGE3B_EXECUTION_SCHEMA_VERSION,
        "campaign_id": STAGE3B_CAMPAIGN_ID,
        "status": "execution_blocked_readiness_only",
        "evidence": False,
        "test_dataset_access": False,
        "full_matrix_execution_enabled": False,
        "preregistration_tag": STAGE3B_PREREGISTRATION_TAG,
        "instrumentation_base_tag": STAGE3B_BOUNDARIES_TAG,
        "torch2pc_source_commit": STAGE3B_TORCH2PC_COMMIT,
        "project_source_commit_policy": "record_exact_clean_commit_at_execution_freeze",
        "protocol": {
            "warmup_steps": WARMUP_STEPS,
            "measured_steps": MEASURED_STEPS,
            "repetitions": REPETITIONS,
            "independent_unit": "model_seed",
            "candidate_order": "exactly_counterbalanced_hash_ranked_rotation_within_method",
        },
        "matrix": {
            "depths": list(DEPTHS),
            "widths": list(WIDTHS),
            "batch_sizes": list(BATCH_SIZES),
            "model_seeds": list(MODEL_SEEDS),
            "candidate_methods": {
                candidate: list(methods)
                for candidate, methods in CANDIDATE_METHODS.items()
            },
            "expected_cell_count": 336,
        },
        "candidate_gates": dict(CANDIDATE_GATE_STATUS),
        "execution_policy": {
            "committed_outputs_allowed": False,
            "temporary_output_root": "/tmp",
            "completed_cell_requires_matching_manifest_digest": True,
            "incomplete_and_failed_attempts_are_preserved": True,
            "silent_overwrite": False,
            "b0_allowed_action": "single_cell_smoke_after_separate_runner_gate",
            "a0_b1_b2_allowed_action": "dry_run_only_until_candidate_gate",
        },
        "cells": [cell.to_record() for cell in cells],
    }


def generate_manifest() -> dict[str, object]:
    """Return the canonical committed Stage 3B execution manifest."""
    payload = _manifest_without_digest()
    return {**payload, "manifest_digest": _digest(payload)}


def validate_manifest(manifest: Mapping[str, object]) -> None:
    """Validate frozen matrix, digest, candidate constraints, and balance."""
    if manifest.get("schema_version") != STAGE3B_EXECUTION_SCHEMA_VERSION:
        raise Stage3BExecutionError("unsupported Stage 3B execution schema")
    if manifest.get("campaign_id") != STAGE3B_CAMPAIGN_ID:
        raise Stage3BExecutionError("unexpected Stage 3B campaign_id")
    supplied_digest = manifest.get("manifest_digest")
    if not isinstance(supplied_digest, str):
        raise Stage3BExecutionError("manifest_digest is required")
    digest_payload = dict(manifest)
    del digest_payload["manifest_digest"]
    if _digest(digest_payload) != supplied_digest:
        raise Stage3BExecutionError("manifest_digest does not match manifest content")

    raw_cells = manifest.get("cells")
    if not isinstance(raw_cells, list):
        raise Stage3BExecutionError("manifest cells must be a list")
    cells = [cast(dict[str, object], cell) for cell in raw_cells]
    if len(cells) != 336:
        raise Stage3BExecutionError(f"Stage 3B manifest must contain 336 cells, got {len(cells)}")

    cell_ids = [str(cell.get("cell_id")) for cell in cells]
    if len(set(cell_ids)) != len(cell_ids):
        raise Stage3BExecutionError("Stage 3B cell_id values must be unique")

    counts = Counter(str(cell.get("candidate_id")) for cell in cells)
    expected_counts = {
        "stage2_baseline": 96,
        "fixedpred_finite_step_control": 48,
        "isolated_layer_vjp": 96,
        "composite_vjp": 96,
    }
    if counts != expected_counts:
        raise Stage3BExecutionError(
            f"candidate cell counts differ from preregistration: {dict(counts)}"
        )

    for cell in cells:
        candidate_id = str(cell.get("candidate_id"))
        method = str(cell.get("method"))
        if candidate_id not in CANDIDATE_METHODS:
            raise Stage3BExecutionError(f"unknown candidate_id: {candidate_id}")
        if method not in CANDIDATE_METHODS[candidate_id]:
            raise Stage3BExecutionError(
                f"candidate/method pair is not preregistered: {candidate_id}/{method}"
            )

    for method, candidates in METHOD_CANDIDATES.items():
        method_cells = [cell for cell in cells if cell.get("method") == method]
        position_counts = Counter(
            (str(cell.get("candidate_id")), int(cast(int, cell.get("candidate_order"))))
            for cell in method_cells
        )
        expected_per_position = 48 // len(candidates)
        for candidate in candidates:
            for position in range(len(candidates)):
                if position_counts[(candidate, position)] != expected_per_position:
                    raise Stage3BExecutionError(
                        "candidate order is not exactly counterbalanced: "
                        f"method={method}, candidate={candidate}, position={position}"
                    )


def load_manifest(path: Path) -> dict[str, object]:
    """Load and validate a Stage 3B execution manifest."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise Stage3BExecutionError("manifest root must be an object")
    manifest = cast(dict[str, object], raw)
    validate_manifest(manifest)
    return manifest


def validated_temporary_output_root(path: Path) -> Path:
    """Resolve an output root and require it to stay under /tmp."""
    resolved = path.expanduser().resolve()
    temporary_root = Path("/tmp").resolve()
    if resolved == temporary_root or temporary_root not in resolved.parents:
        raise Stage3BExecutionError("Stage 3B readiness output must be under /tmp")
    return resolved




def validated_plan_output_path(path: Path, *, output_root: Path) -> Path:
    """Require a dry-run plan file to stay inside the validated output root."""
    resolved_root = validated_temporary_output_root(output_root)
    resolved_path = path.expanduser().resolve()
    if resolved_path == resolved_root or resolved_root not in resolved_path.parents:
        raise Stage3BExecutionError(
            "Stage 3B dry-run plan output must be a file under output_root"
        )
    return resolved_path

def atomic_write_json(path: Path, payload: Mapping[str, object]) -> None:
    """Atomically write JSON in the destination directory without partial files."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def _status_disposition(
    *, status_path: Path, cell_id: str, manifest_digest: str
) -> CellDisposition:
    if not status_path.exists():
        return "pending_smoke"
    try:
        raw = json.loads(status_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "resume_incomplete"
    if not isinstance(raw, dict):
        return "resume_incomplete"
    if raw.get("cell_id") != cell_id or raw.get("manifest_digest") != manifest_digest:
        return "resume_incomplete"
    status = raw.get("status")
    if status == "completed":
        return "skip_completed"
    if status == "failed":
        return "retry_failed"
    return "resume_incomplete"


def plan_dry_run(
    manifest: Mapping[str, object],
    *,
    output_root: Path,
    selected_cell_ids: Sequence[str] = (),
) -> DryRunPlan:
    """Build a resume-aware plan without executing or creating cell outputs."""
    validate_manifest(manifest)
    resolved_root = validated_temporary_output_root(output_root)
    manifest_digest = cast(str, manifest["manifest_digest"])
    raw_cells = cast(list[dict[str, object]], manifest["cells"])
    by_id = {str(cell["cell_id"]): cell for cell in raw_cells}

    if selected_cell_ids:
        unknown = sorted(set(selected_cell_ids) - set(by_id))
        if unknown:
            raise Stage3BExecutionError(f"unknown selected cell_id values: {unknown}")
        selected = [by_id[cell_id] for cell_id in selected_cell_ids]
    else:
        selected = raw_cells

    planned: list[PlannedCell] = []
    for cell in selected:
        cell_id = str(cell["cell_id"])
        candidate_id = str(cell["candidate_id"])
        method = str(cell["method"])
        status_path = resolved_root / "cells" / cell_id / "status.json"
        if candidate_id != "stage2_baseline":
            disposition: CellDisposition = "blocked_candidate_gate"
        else:
            disposition = _status_disposition(
                status_path=status_path,
                cell_id=cell_id,
                manifest_digest=manifest_digest,
            )
        planned.append(
            PlannedCell(
                cell_id=cell_id,
                candidate_id=candidate_id,
                method=method,
                disposition=disposition,
                status_path=str(status_path),
            )
        )

    summary = Counter(cell.disposition for cell in planned)
    return DryRunPlan(
        manifest_digest=manifest_digest,
        output_root=str(resolved_root),
        selected_cell_count=len(planned),
        summary={str(key): value for key, value in summary.items()},
        cells=tuple(planned),
    )
