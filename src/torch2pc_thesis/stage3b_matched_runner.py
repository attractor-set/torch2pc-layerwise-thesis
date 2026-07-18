"""Candidate-aware planning primitives for matched Stage 3B profiling.

This module deliberately stops before runtime authorization and measurements.
It validates the admitted 288-cell B0/B1/B2 matrix, resolves the three
candidate loader symbols, and builds a non-evidence plan whose cells remain
blocked on a separate ROCm/float32 runtime freeze.
"""

from __future__ import annotations

import hashlib
import importlib
import json
from collections import Counter, defaultdict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Final, Literal, cast

from torch2pc_thesis.stage3b_execution import (
    STAGE3B_CAMPAIGN_ID,
    atomic_write_json,
    validated_plan_output_path,
    validated_temporary_output_root,
)
from torch2pc_thesis.stage3b_matched_profiling import (
    MATCHED_PROFILING_CANDIDATES,
    MATCHED_PROFILING_EXPECTED_CELL_COUNT,
    MatchedProfilingError,
    validate_matched_manifest,
    validate_matched_request,
)

MATCHED_RUNNER_SCHEMA_VERSION: Final[int] = 1
MATCHED_RUNNER_ID: Final[str] = "stage3b-b1-b2-matched-runner-v1"
MATCHED_RUNNER_EXPECTED_BLOCK_COUNT: Final[int] = 96
MATCHED_RUNNER_EXPECTED_CELLS_PER_BLOCK: Final[int] = 3
MATCHED_RUNNER_STATUS: Final[str] = (
    "runner_contract_ready_runtime_not_authorized"
)
MATCHED_RUNNER_DISPOSITION: Final[Literal["blocked_runtime_authorization"]] = "blocked_runtime_authorization"
MATCHED_RUNNER_STATE_RESET_POLICY: Final[str] = (
    "restore_model_optimizer_rng_and_minibatch_before_each_candidate"
)
MATCHED_RUNNER_OUTPUT_POLICY: Final[str] = (
    "temporary_plan_only_no_measurements_no_evidence"
)
MATCHED_RUNNER_METHOD_LABELS: Final[dict[str, str]] = {
    "fixedpred": "FixedPred",
    "strict": "Strict",
}
MATCHED_RUNNER_FUTURE_BOUNDARY: Final[dict[str, bool]] = {
    "ex_if0_open": False,
    "estimator_present": False,
    "ecz_active": False,
    "qwake_pc_active": False,
    "controller_actions_present": False,
    "offline_policy_selection_present": False,
}
MATCHED_RUNNER_EXPLICITLY_CLOSED: Final[frozenset[str]] = frozenset(
    {
        "EX-IF0",
        "estimator",
        "active ECZ",
        "QWake-PC",
        "controller actions",
        "offline policy selection",
        "test-split access",
    }
)

RunnerDisposition = Literal["blocked_runtime_authorization"]
CandidateLoader = Callable[..., object]
CandidateCallable = Callable[..., object]
MockExecutor = Callable[
    ["RunnerCellPlan", "CandidateAdapterSpec"], Mapping[str, object]
]
RestoreCallback = Callable[[object], None]


class MatchedRunnerError(MatchedProfilingError):
    """Raised when candidate-aware runner invariants are violated."""


@dataclass(frozen=True)
class CandidateAdapterSpec:
    """Lazy import contract for one admitted profiling candidate."""

    candidate_id: str
    module_name: str
    loader_name: str
    execution_role: str

    def to_record(self) -> dict[str, str]:
        return asdict(self)


CANDIDATE_ADAPTERS: Final[dict[str, CandidateAdapterSpec]] = {
    "stage2_baseline": CandidateAdapterSpec(
        candidate_id="stage2_baseline",
        module_name="torch2pc_thesis.pc_methods",
        loader_name="load_pc_infer",
        execution_role="patched_stage2_reference",
    ),
    "isolated_layer_vjp": CandidateAdapterSpec(
        candidate_id="isolated_layer_vjp",
        module_name="torch2pc_thesis.stage3b_b1_isolated_vjp",
        loader_name="load_b1_pc_infer",
        execution_role="b1_isolated_layer_state_vjp",
    ),
    "composite_vjp": CandidateAdapterSpec(
        candidate_id="composite_vjp",
        module_name="torch2pc_thesis.stage3b_b2_composite_vjp",
        loader_name="load_b2_pc_infer",
        execution_role="b2_composite_state_vjp",
    ),
}


@dataclass(frozen=True)
class RunnerCellPlan:
    """One candidate-aware cell that remains blocked on runtime freeze."""

    plan_index: int
    cell_id: str
    block_id: str
    block_order: int
    candidate_order: int
    candidate_id: str
    method: str
    method_label: str
    depth: int
    width: int
    batch_size: int
    model_seed: int
    adapter_module: str
    adapter_loader: str
    disposition: RunnerDisposition = MATCHED_RUNNER_DISPOSITION

    def to_record(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class MatchedRunnerPlan:
    """Serializable non-execution plan for all admitted matched cells."""

    matched_manifest_digest: str
    opening_request_digest: str
    output_root: str
    dispatch_verified: bool
    cells: tuple[RunnerCellPlan, ...]

    def to_record(self) -> dict[str, object]:
        summary = Counter(cell.disposition for cell in self.cells)
        payload: dict[str, object] = {
            "schema_version": MATCHED_RUNNER_SCHEMA_VERSION,
            "runner_id": MATCHED_RUNNER_ID,
            "campaign_id": STAGE3B_CAMPAIGN_ID,
            "status": MATCHED_RUNNER_STATUS,
            "evidence": False,
            "execution_performed": False,
            "mock_dispatch_exercised": False,
            "test_dataset_access": False,
            "full_stage3b_campaign_complete": False,
            "scientific_admission": "open",
            "runtime_authorization": "not_issued",
            "measurements_allowed": False,
            "matched_manifest_digest": self.matched_manifest_digest,
            "opening_request_digest": self.opening_request_digest,
            "output_root": self.output_root,
            "selected_cell_count": len(self.cells),
            "dispatch_verified": self.dispatch_verified,
            "state_reset_policy": MATCHED_RUNNER_STATE_RESET_POLICY,
            "output_policy": MATCHED_RUNNER_OUTPUT_POLICY,
            "candidate_adapters": {
                candidate_id: spec.to_record()
                for candidate_id, spec in sorted(CANDIDATE_ADAPTERS.items())
            },
            "summary": dict(sorted(summary.items())),
            "cells": [cell.to_record() for cell in self.cells],
        }
        return {**payload, "plan_digest": _digest(payload)}


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _require_mapping(value: object, *, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise MatchedRunnerError(f"{field} must be an object")
    for key in value:
        if not isinstance(key, str):
            raise MatchedRunnerError(f"{field} contains a non-string key")
    return cast(Mapping[str, object], value)


def _require_int(value: object, *, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise MatchedRunnerError(f"{field} must be an integer")
    return value


def _validate_opening_link(
    manifest: Mapping[str, object],
    request: Mapping[str, object],
) -> None:
    source_artifacts = _require_mapping(
        request.get("source_artifacts"),
        field="opening request source_artifacts",
    )
    matched_record = _require_mapping(
        source_artifacts.get("matched_manifest"),
        field="opening request matched_manifest",
    )
    if matched_record.get("manifest_digest") != manifest.get("manifest_digest"):
        raise MatchedRunnerError(
            "opening request does not reference the supplied matched manifest"
        )
    if matched_record.get("selected_cell_count") != manifest.get(
        "selected_cell_count"
    ):
        raise MatchedRunnerError(
            "opening request matched cell count differs from the manifest"
        )

    admitted = request.get("admitted_candidates")
    if admitted != list(MATCHED_PROFILING_CANDIDATES):
        raise MatchedRunnerError("opening request admitted candidate order changed")


def _validate_closed_boundaries(
    manifest: Mapping[str, object],
    request: Mapping[str, object],
) -> None:
    execution_policy = _require_mapping(
        manifest.get("execution_policy"),
        field="matched manifest execution_policy",
    )
    expected_execution_policy: dict[str, object] = {
        "scientific_admission": "open",
        "runtime_authorization": "not_issued",
        "measurements_allowed": False,
        "candidate_aware_runner_required": True,
        "rocm_float32_primary_lane_required": True,
        "temporary_output_only_until_runtime_freeze": True,
        "committed_measurements_present": False,
    }
    for key, expected in expected_execution_policy.items():
        if execution_policy.get(key) != expected:
            observed = execution_policy.get(key)
            raise MatchedRunnerError(
                "matched execution boundary changed: "
                f"{key}={observed!r}"
            )

    future_boundary = _require_mapping(
        manifest.get("future_policy_boundary"),
        field="matched manifest future_policy_boundary",
    )
    if dict(future_boundary) != MATCHED_RUNNER_FUTURE_BOUNDARY:
        raise MatchedRunnerError("future policy boundary changed or opened")

    closed = request.get("explicitly_closed")
    if (
        not isinstance(closed, list)
        or not all(isinstance(item, str) for item in closed)
        or set(closed) != MATCHED_RUNNER_EXPLICITLY_CLOSED
    ):
        raise MatchedRunnerError("opening request closed-boundary set changed")


def _validated_cells(
    manifest: Mapping[str, object],
) -> tuple[Mapping[str, object], ...]:
    raw_cells = manifest.get("cells")
    if not isinstance(raw_cells, list):
        raise MatchedRunnerError("matched manifest cells must be a list")
    if len(raw_cells) != MATCHED_PROFILING_EXPECTED_CELL_COUNT:
        raise MatchedRunnerError("matched runner requires exactly 288 cells")

    cells: list[Mapping[str, object]] = []
    for index, raw_cell in enumerate(raw_cells):
        cells.append(_require_mapping(raw_cell, field=f"matched cell {index}"))

    cell_ids = [str(cell.get("cell_id")) for cell in cells]
    if len(set(cell_ids)) != len(cell_ids):
        raise MatchedRunnerError("matched cell_id values must be unique")

    ordered_keys: list[tuple[int, int]] = []
    blocks: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for cell in cells:
        candidate_id = str(cell.get("candidate_id"))
        method = str(cell.get("method"))
        if candidate_id not in CANDIDATE_ADAPTERS:
            raise MatchedRunnerError(f"candidate has no runner adapter: {candidate_id}")
        if method not in MATCHED_RUNNER_METHOD_LABELS:
            raise MatchedRunnerError(f"unsupported matched runner method: {method}")
        if cell.get("candidate_gate_status") != "equivalence_gate_passed":
            raise MatchedRunnerError(
                f"candidate is not equivalence-admitted: {candidate_id}"
            )
        if cell.get("matched_profiling_eligible") is not True:
            raise MatchedRunnerError(
                f"candidate is not marked matched-profiling eligible: {candidate_id}"
            )

        block_order = _require_int(cell.get("block_order"), field="block_order")
        candidate_order = _require_int(
            cell.get("candidate_order"), field="candidate_order"
        )
        ordered_keys.append((block_order, candidate_order))
        blocks[str(cell.get("block_id"))].append(cell)

    if ordered_keys != sorted(ordered_keys):
        raise MatchedRunnerError(
            "matched cells do not preserve source block/candidate order"
        )
    if len(blocks) != MATCHED_RUNNER_EXPECTED_BLOCK_COUNT:
        raise MatchedRunnerError("matched runner requires exactly 96 blocks")

    expected_candidates = set(MATCHED_PROFILING_CANDIDATES)
    stable_fields = (
        "block_order",
        "method",
        "depth",
        "width",
        "batch_size",
        "model_seed",
    )
    for block_id, block_cells in blocks.items():
        if len(block_cells) != MATCHED_RUNNER_EXPECTED_CELLS_PER_BLOCK:
            raise MatchedRunnerError(
                f"matched block does not contain three candidates: {block_id}"
            )
        candidate_ids = {str(cell.get("candidate_id")) for cell in block_cells}
        if candidate_ids != expected_candidates:
            raise MatchedRunnerError(
                f"matched block candidate set changed: {block_id}"
            )
        candidate_orders = [
            _require_int(cell.get("candidate_order"), field="candidate_order")
            for cell in block_cells
        ]
        if len(set(candidate_orders)) != len(candidate_orders):
            raise MatchedRunnerError(
                f"matched block candidate order is not unique: {block_id}"
            )
        for field in stable_fields:
            values = {cell.get(field) for cell in block_cells}
            if len(values) != 1:
                raise MatchedRunnerError(
                    f"matched block field differs across candidates: {block_id}/{field}"
                )

    return tuple(cells)


def validate_runner_inputs(
    manifest: Mapping[str, object],
    request: Mapping[str, object],
) -> tuple[Mapping[str, object], ...]:
    """Validate opening artifacts and return the ordered matched cells."""
    validate_matched_manifest(manifest)
    validate_matched_request(request)
    if manifest.get("status") != (
        "scientific_admission_open_execution_not_authorized"
    ):
        raise MatchedRunnerError("matched manifest opening status changed")
    if request.get("status") != (
        "scientific_admission_open_execution_not_authorized"
    ):
        raise MatchedRunnerError("matched request opening status changed")
    _validate_opening_link(manifest, request)
    _validate_closed_boundaries(manifest, request)
    return _validated_cells(manifest)


def adapter_for_candidate(candidate_id: str) -> CandidateAdapterSpec:
    """Return the frozen adapter specification for one candidate."""
    try:
        return CANDIDATE_ADAPTERS[candidate_id]
    except KeyError as error:
        raise MatchedRunnerError(
            f"unsupported matched profiling candidate: {candidate_id}"
        ) from error


def resolve_candidate_loader(candidate_id: str) -> CandidateLoader:
    """Resolve one lazy loader symbol without creating or executing a model."""
    spec = adapter_for_candidate(candidate_id)
    module = importlib.import_module(spec.module_name)
    loader = getattr(module, spec.loader_name, None)
    if not callable(loader):
        raise MatchedRunnerError(
            f"candidate loader is unavailable: {spec.module_name}.{spec.loader_name}"
        )
    return cast(CandidateLoader, loader)


def verify_candidate_dispatch() -> tuple[str, ...]:
    """Require all three frozen loader symbols to be importable and callable."""
    verified: list[str] = []
    for candidate_id in MATCHED_PROFILING_CANDIDATES:
        spec = adapter_for_candidate(candidate_id)
        resolve_candidate_loader(candidate_id)
        verified.append(f"{spec.module_name}.{spec.loader_name}")
    return tuple(verified)


def load_candidate_pc_infer(
    candidate_id: str,
    torch2pc_dir: str | Path,
) -> CandidateCallable:
    """Load one candidate callable without running a profiling step."""
    loader = resolve_candidate_loader(candidate_id)
    candidate = loader(torch2pc_dir)
    if not callable(candidate):
        raise MatchedRunnerError(
            f"candidate loader did not return a callable: {candidate_id}"
        )
    return cast(CandidateCallable, candidate)


def build_matched_runner_plan(
    manifest: Mapping[str, object],
    request: Mapping[str, object],
    *,
    output_root: Path,
    verify_dispatch: bool = True,
) -> MatchedRunnerPlan:
    """Build a candidate-aware plan while keeping every cell execution-blocked."""
    cells = validate_runner_inputs(manifest, request)
    resolved_root = validated_temporary_output_root(output_root)
    if verify_dispatch:
        verify_candidate_dispatch()

    planned: list[RunnerCellPlan] = []
    for plan_index, cell in enumerate(cells):
        candidate_id = str(cell["candidate_id"])
        method = str(cell["method"])
        adapter = adapter_for_candidate(candidate_id)
        planned.append(
            RunnerCellPlan(
                plan_index=plan_index,
                cell_id=str(cell["cell_id"]),
                block_id=str(cell["block_id"]),
                block_order=_require_int(
                    cell.get("block_order"), field="block_order"
                ),
                candidate_order=_require_int(
                    cell.get("candidate_order"), field="candidate_order"
                ),
                candidate_id=candidate_id,
                method=method,
                method_label=MATCHED_RUNNER_METHOD_LABELS[method],
                depth=_require_int(cell.get("depth"), field="depth"),
                width=_require_int(cell.get("width"), field="width"),
                batch_size=_require_int(
                    cell.get("batch_size"), field="batch_size"
                ),
                model_seed=_require_int(
                    cell.get("model_seed"), field="model_seed"
                ),
                adapter_module=adapter.module_name,
                adapter_loader=adapter.loader_name,
            )
        )

    return MatchedRunnerPlan(
        matched_manifest_digest=str(manifest["manifest_digest"]),
        opening_request_digest=str(request["request_digest"]),
        output_root=str(resolved_root),
        dispatch_verified=verify_dispatch,
        cells=tuple(planned),
    )


def validate_runner_plan(plan: Mapping[str, object]) -> None:
    """Validate a serialized plan and its explicit non-execution boundary."""
    if plan.get("schema_version") != MATCHED_RUNNER_SCHEMA_VERSION:
        raise MatchedRunnerError("unsupported matched runner plan schema")
    if plan.get("runner_id") != MATCHED_RUNNER_ID:
        raise MatchedRunnerError("unexpected matched runner_id")
    if plan.get("campaign_id") != STAGE3B_CAMPAIGN_ID:
        raise MatchedRunnerError("unexpected matched runner campaign")
    if plan.get("status") != MATCHED_RUNNER_STATUS:
        raise MatchedRunnerError("matched runner plan status changed")
    if plan.get("evidence") is not False:
        raise MatchedRunnerError("matched runner plan cannot be evidence")
    if plan.get("execution_performed") is not False:
        raise MatchedRunnerError("matched runner plan cannot record execution")
    if plan.get("measurements_allowed") is not False:
        raise MatchedRunnerError("matched runner plan cannot authorize measurements")
    if plan.get("runtime_authorization") != "not_issued":
        raise MatchedRunnerError(
            "matched runner runtime authorization must be unissued"
        )
    if plan.get("test_dataset_access") is not False:
        raise MatchedRunnerError("matched runner plan cannot access test data")
    if plan.get("selected_cell_count") != MATCHED_PROFILING_EXPECTED_CELL_COUNT:
        raise MatchedRunnerError("matched runner plan cell count changed")
    if plan.get("state_reset_policy") != MATCHED_RUNNER_STATE_RESET_POLICY:
        raise MatchedRunnerError("matched runner state-reset policy changed")
    summary = _require_mapping(plan.get("summary"), field="matched runner summary")
    if summary != {MATCHED_RUNNER_DISPOSITION: MATCHED_PROFILING_EXPECTED_CELL_COUNT}:
        raise MatchedRunnerError(
            "matched runner plan contains an executable disposition"
        )

    supplied_digest = plan.get("plan_digest")
    if not isinstance(supplied_digest, str):
        raise MatchedRunnerError("matched runner plan_digest is required")
    payload = dict(plan)
    del payload["plan_digest"]
    if _digest(payload) != supplied_digest:
        raise MatchedRunnerError("matched runner plan_digest does not match content")


def write_matched_runner_plan(
    path: Path,
    *,
    output_root: Path,
    plan: MatchedRunnerPlan,
) -> Path:
    """Write one validated plan under the temporary output root."""
    resolved_path = validated_plan_output_path(path, output_root=output_root)
    record = plan.to_record()
    validate_runner_plan(record)
    atomic_write_json(resolved_path, record)
    return resolved_path


def _block_cells(
    plan: MatchedRunnerPlan,
    *,
    block_id: str,
) -> tuple[RunnerCellPlan, ...]:
    cells = tuple(cell for cell in plan.cells if cell.block_id == block_id)
    if len(cells) != MATCHED_RUNNER_EXPECTED_CELLS_PER_BLOCK:
        raise MatchedRunnerError(f"unknown or incomplete matched block: {block_id}")
    return cells


def run_mocked_block_dispatch(
    plan: MatchedRunnerPlan,
    *,
    block_id: str,
    state_snapshot: object,
    rng_snapshot: object,
    restore_state: RestoreCallback,
    restore_rng: RestoreCallback,
    executor: MockExecutor,
) -> dict[str, object]:
    """Exercise dispatch/restoration semantics without profiling measurements."""
    cells = _block_cells(plan, block_id=block_id)
    records: list[dict[str, object]] = []
    forbidden_result_keys = {
        "evidence",
        "measurements",
        "timing",
        "memory",
        "test_dataset_access",
    }

    for cell in cells:
        restore_state(state_snapshot)
        restore_rng(rng_snapshot)
        adapter = adapter_for_candidate(cell.candidate_id)
        raw_result = executor(cell, adapter)
        result = dict(raw_result)
        forbidden = sorted(forbidden_result_keys.intersection(result))
        if forbidden:
            raise MatchedRunnerError(
                f"mock executor returned measurement-like fields: {forbidden}"
            )
        records.append(
            {
                "cell_id": cell.cell_id,
                "block_id": cell.block_id,
                "candidate_id": cell.candidate_id,
                "candidate_order": cell.candidate_order,
                "adapter_module": adapter.module_name,
                "adapter_loader": adapter.loader_name,
                "mock_result": result,
            }
        )

    return {
        "schema_version": MATCHED_RUNNER_SCHEMA_VERSION,
        "runner_id": MATCHED_RUNNER_ID,
        "campaign_id": STAGE3B_CAMPAIGN_ID,
        "status": "mock_dispatch_passed_runtime_not_authorized",
        "evidence": False,
        "execution_performed": False,
        "mock_dispatch_exercised": True,
        "measurements_allowed": False,
        "measurements_recorded": False,
        "runtime_authorization": "not_issued",
        "test_dataset_access": False,
        "block_id": block_id,
        "state_restore_count": len(cells),
        "rng_restore_count": len(cells),
        "candidate_order": [cell.candidate_id for cell in cells],
        "records": records,
    }


def candidate_ids(cells: Sequence[RunnerCellPlan]) -> tuple[str, ...]:
    """Return candidate IDs in supplied order for tests and audit output."""
    return tuple(cell.candidate_id for cell in cells)
