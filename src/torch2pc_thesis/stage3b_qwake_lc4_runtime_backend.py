"""Bounded QW-LC4-E Torch runtime backend and future freeze guard.

Importing or constructing objects from this module has no runtime effects.  The
backend can run only after a separately materialized immutable execution freeze
is verified.  The implementation consumes only the frozen synthetic
engineering authorization, executes the registered 2 x 7 x 12 matched matrix
and 28 exact-reserve probes, and writes engineering evidence below the wrapper
staging directory.  It never loads a dataset, opens scientific execution, or
publishes evidence.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import random
import subprocess
import time
from collections.abc import Callable, Iterable, Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Final, Protocol, cast

import numpy as np
import torch
from torch import Tensor, nn

from torch2pc_thesis.models import build_model
from torch2pc_thesis.stage3b_qwake_lc4_bounded import (
    ANALYTIC_ACTION_ID,
    EXACT_REFERENCE_ACTION_ID,
    ArtifactRecord,
    BoundedArm,
    CanonicalResponse,
    CompletionResult,
    CostPair,
    CostVector,
    FallbackRecord,
    FixedPredFrontier,
    IntervalOwner,
    IntervalRecord,
    MemoryRecord,
    ObserverCalibration,
    OpaqueStateSnapshot,
    PairedCostAggregation,
    ResourceTrajectory,
    aggregate_paired_costs,
    analytic_wavefront_completion,
    capture_fixedpred_frontier,
    capture_rng_snapshot,
    compare_required_responses,
    complete_exact_suffix,
    map_resource_trajectory,
    materialize_required_response,
    pair_schedule,
    preserve_outer_rng,
    restore_rng_snapshot,
)
from torch2pc_thesis.stage3b_qwake_lc4_execution_admission import (
    AUTHORIZED_OUTPUT_ROOT,
)
from torch2pc_thesis.stage3b_qwake_lc4_execution_freeze import (
    EXECUTION_FREEZE_REQUEST_ID,
    ONE_SHOT_ENTRYPOINT_ID,
)
from torch2pc_thesis.stage3b_qwake_lc4_execution_freeze import (
    RUNTIME_BACKEND_CONTRACT_ID as RUNTIME_BACKEND_CONTRACT_ID,
)
from torch2pc_thesis.stage3b_qwake_lc4_execution_wrapper import (
    EXECUTION_LEASE_OPERATOR_ACKNOWLEDGEMENT,
    FROZEN_ADMISSION_SHA256,
    FROZEN_AUTHORIZATION_SHA256,
    FROZEN_TORCH2PC_COMMIT,
    ExecutionWrapperContract,
    ProspectiveExecutionLease,
    canonical_json,
    sha256_object,
)
from torch2pc_thesis.stage3b_qwake_lc4_execution_wrapper_implementation import (
    ExecutionWrapperOutcome,
    RuntimeBackendReceipt,
    RuntimeExecutionBackend,
    build_runtime_backend_receipt,
    claim_execution_lease,
    execute_authorized_runtime,
)
from torch2pc_thesis.stage3b_qwake_lc4_runtime_freeze import (
    RUNTIME_CANDIDATE_INDICES,
    RUNTIME_ENGINEERING_BATCH_ID,
    RUNTIME_MODEL_SEED,
    QWakeLC4RuntimeAuthorization,
    RuntimeArmOrder,
    RuntimeAuthorizationCell,
    RuntimeFrontierAdapter,
    RuntimeLane,
    load_runtime_authorization,
    runtime_authorization_cells,
)


class _ProcessMemoryInfo(Protocol):
    """Typed subset of psutil memory information used by the backend."""

    rss: int


class _ProcessHandle(Protocol):
    """Typed subset of a psutil process handle used by the backend."""

    def memory_full_info(self) -> _ProcessMemoryInfo:
        """Return full memory information for the current process."""

        ...


class _PsutilModule(Protocol):
    """Typed dynamic psutil surface without a repository stub dependency."""

    Process: Callable[[], _ProcessHandle]


_PSUTIL = cast(_PsutilModule, importlib.import_module("psutil"))

RUNTIME_BACKEND_IMPLEMENTATION_ID: Final = (
    "stage3b-qwake-lc4-e-runtime-backend-implementation-v1"
)
RUNTIME_BACKEND_IMPLEMENTATION_STATUS: Final = (
    "bounded_backend_and_entrypoint_materialized_execution_not_open"
)
RUNTIME_BACKEND_ID: Final = (
    "stage3b-qwake-lc4-e-bounded-torch-runtime-backend-v1"
)
RUNTIME_BACKEND_REPORT_ID: Final = (
    "stage3b-qwake-lc4-e-runtime-backend-report-v1"
)
MATERIALIZED_EXECUTION_FREEZE_ID: Final = (
    "stage3b-qwake-lc4-e-execution-freeze-v1"
)
MATERIALIZED_EXECUTION_FREEZE_STATUS: Final = (
    "immutable_backend_and_entrypoint_frozen_execution_not_started"
)
AUTHORING_MERGE_COMMIT: Final = (
    "49d691d497f4f719e82b271e9b9d441f9e4dfa63"
)
AUTHORING_HEAD_COMMIT: Final = (
    "1bad6419f3e413353f922d4ac2190bb5c52ac865"
)
AUTHORING_REQUEST_SHA256: Final = (
    "sha256:"
    "9b28943043082efe96fb313f94875ef18c7f8e7361d8c0eb1b8c140e82a1e312"
)
RUNTIME_AUTHORIZATION_RELATIVE: Final = Path(
    "experiments/frozen/stage3b-qwake-lc4-f-runtime-freeze-v1/"
    "authorization.json"
)
MATERIALIZED_EXECUTION_FREEZE_ROOT: Final = Path(
    "experiments/frozen/stage3b-qwake-lc4-e-execution-freeze-v1"
)
MATERIALIZED_EXECUTION_FREEZE_RELATIVE: Final = (
    MATERIALIZED_EXECUTION_FREEZE_ROOT / "execution.json"
)
MATERIALIZED_EXECUTION_FREEZE_REGISTRY_RELATIVE: Final = (
    MATERIALIZED_EXECUTION_FREEZE_ROOT / "SHA256SUMS"
)
RUNTIME_BACKEND_MODULE_RELATIVE: Final = Path(
    "src/torch2pc_thesis/stage3b_qwake_lc4_runtime_backend.py"
)
ONE_SHOT_ENTRYPOINT_RELATIVE: Final = Path(
    "scripts/run_stage3b_qwake_lc4_authorized_runtime.py"
)
_RUNTIME_REPORT_RELATIVE: Final = Path("runtime-backend-report.json")
_MATCHED_CELLS_RELATIVE: Final = Path("matched-cells.jsonl")
_RESERVE_PROBES_RELATIVE: Final = Path("reserve-probes.jsonl")
_AGGREGATES_RELATIVE: Final = Path("paired-cost-aggregates.json")
_IDENTITIES_RELATIVE: Final = Path("runtime-identities.json")
_BACKEND_RECEIPT_RELATIVE: Final = Path("runtime-backend-receipt.json")
_BACKEND_SUMS_RELATIVE: Final = Path("SHA256SUMS")
_EXPECTED_BACKEND_OUTPUT_FILE_COUNT: Final = 7
_SYNTHETIC_BATCH_SIZE: Final = 2
_SYNTHETIC_IMAGE_SHAPE: Final = (1, 32, 32)
_COMMIT_LENGTH: Final = 40
_SHA256_PREFIX_LENGTH: Final = 71

__all__ = [
    "AUTHORING_HEAD_COMMIT",
    "AUTHORING_MERGE_COMMIT",
    "AUTHORING_REQUEST_SHA256",
    "MATERIALIZED_EXECUTION_FREEZE_ID",
    "MATERIALIZED_EXECUTION_FREEZE_RELATIVE",
    "MATERIALIZED_EXECUTION_FREEZE_STATUS",
    "ONE_SHOT_ENTRYPOINT_ID",
    "RUNTIME_BACKEND_CONTRACT_ID",
    "RUNTIME_BACKEND_ID",
    "RUNTIME_BACKEND_IMPLEMENTATION_ID",
    "RUNTIME_BACKEND_IMPLEMENTATION_STATUS",
    "RUNTIME_BACKEND_REPORT_ID",
    "ArmExecutionRecord",
    "FrontierNormalizationRecord",
    "BoundedTorchMatrixExecutor",
    "MaterializedExecutionFreeze",
    "QWakeLC4RuntimeBackend",
    "QWakeLC4RuntimeBackendError",
    "ReserveProbeRecord",
    "RuntimeCellRecord",
    "RuntimeMatrixExecutor",
    "RuntimeMatrixResult",
    "execute_bounded_runtime_cell",
    "inspect_runtime_frontier_normalization",
    "load_materialized_execution_freeze",
    "run_one_shot_authorized_runtime",
    "verify_materialized_execution_freeze",
]


class QWakeLC4RuntimeBackendError(RuntimeError):
    """Raised when the bounded runtime backend cannot preserve its contract."""


@dataclass(frozen=True)
class MaterializedExecutionFreeze:
    """Future immutable execution freeze required before any lease claim."""

    schema_version: int
    freeze_id: str
    status: str
    source_commit: str
    wrapper_commit: str
    torch2pc_commit: str
    image_digest: str
    image_repo_digest: str
    backend_id: str
    backend_module_path: str
    backend_module_sha256: str
    entrypoint_id: str
    entrypoint_path: str
    entrypoint_sha256: str
    authoring_request_id: str
    authoring_request_sha256: str
    admission_sha256: str
    authorization_sha256: str
    execution_count: int
    concrete_runtime_backend_present: bool
    one_shot_entrypoint_present: bool
    immutable_execution_image_present: bool
    execution_freeze_materialized: bool
    runtime_execution_permitted: bool
    execution_lease_materialized: bool
    authorization_consumed: bool
    runtime_execution_started: bool
    runtime_execution_performed: bool
    engineering_evidence_present: bool
    scientific_execution_open: bool
    test_dataset_access: bool
    publication_permitted: bool
    local_compute_execution_open: bool
    freeze_sha256: str

    def require(self) -> None:
        if self.schema_version != 1:
            raise QWakeLC4RuntimeBackendError(
                "unexpected materialized execution-freeze schema"
            )
        exact: Mapping[str, object] = {
            "freeze_id": MATERIALIZED_EXECUTION_FREEZE_ID,
            "status": MATERIALIZED_EXECUTION_FREEZE_STATUS,
            "torch2pc_commit": FROZEN_TORCH2PC_COMMIT,
            "backend_id": RUNTIME_BACKEND_ID,
            "backend_module_path": RUNTIME_BACKEND_MODULE_RELATIVE.as_posix(),
            "entrypoint_id": ONE_SHOT_ENTRYPOINT_ID,
            "entrypoint_path": ONE_SHOT_ENTRYPOINT_RELATIVE.as_posix(),
            "authoring_request_id": EXECUTION_FREEZE_REQUEST_ID,
            "authoring_request_sha256": AUTHORING_REQUEST_SHA256,
            "admission_sha256": FROZEN_ADMISSION_SHA256,
            "authorization_sha256": FROZEN_AUTHORIZATION_SHA256,
            "execution_count": 1,
        }
        for field_name, expected in exact.items():
            if getattr(self, field_name) != expected:
                raise QWakeLC4RuntimeBackendError(
                    f"materialized execution-freeze field differs: {field_name}"
                )
        for value, field_name in (
            (self.source_commit, "source_commit"),
            (self.wrapper_commit, "wrapper_commit"),
            (self.torch2pc_commit, "torch2pc_commit"),
        ):
            _require_commit(value, field_name)
        if self.wrapper_commit != self.source_commit:
            raise QWakeLC4RuntimeBackendError(
                "execution-freeze wrapper and source commits differ"
            )
        for value, field_name in (
            (self.image_digest, "image_digest"),
            (self.backend_module_sha256, "backend_module_sha256"),
            (self.entrypoint_sha256, "entrypoint_sha256"),
            (self.authoring_request_sha256, "authoring_request_sha256"),
            (self.admission_sha256, "admission_sha256"),
            (self.authorization_sha256, "authorization_sha256"),
            (self.freeze_sha256, "freeze_sha256"),
        ):
            _require_sha256(value, field_name)
        if not self.image_repo_digest.strip():
            raise QWakeLC4RuntimeBackendError(
                "execution-freeze image repo digest is empty"
            )
        if not self.image_repo_digest.endswith(f"@{self.image_digest}"):
            raise QWakeLC4RuntimeBackendError(
                "execution-freeze image repo digest differs from image digest"
            )
        if not all(
            (
                self.concrete_runtime_backend_present,
                self.one_shot_entrypoint_present,
                self.immutable_execution_image_present,
                self.execution_freeze_materialized,
                self.runtime_execution_permitted,
            )
        ):
            raise QWakeLC4RuntimeBackendError(
                "materialized execution-freeze capability is incomplete"
            )
        if any(
            (
                self.execution_lease_materialized,
                self.authorization_consumed,
                self.runtime_execution_started,
                self.runtime_execution_performed,
                self.engineering_evidence_present,
                self.scientific_execution_open,
                self.test_dataset_access,
                self.publication_permitted,
                self.local_compute_execution_open,
            )
        ):
            raise QWakeLC4RuntimeBackendError(
                "materialized execution freeze contains a completed or scientific effect"
            )
        _verify_payload_digest(self, "freeze_sha256")

    def canonical_json(self) -> str:
        return canonical_json(self)


@dataclass(frozen=True)
class FrontierNormalizationRecord:
    """Pure canonicalization of eta=1 upper-wavefront roundoff."""

    lane: str
    candidate_index: int
    normalized_indices: tuple[int, ...]
    maximum_absolute_defect: float
    absolute_tolerance: float
    relative_tolerance: float
    raw_frontier_sha256: str
    canonical_frontier_sha256: str
    normalization_applied: bool
    normalization_sha256: str

    def require(self) -> None:
        if self.lane not in {item.value for item in RuntimeLane}:
            raise QWakeLC4RuntimeBackendError(
                "frontier-normalization lane is not registered"
            )
        if self.candidate_index not in RUNTIME_CANDIDATE_INDICES:
            raise QWakeLC4RuntimeBackendError(
                "frontier-normalization candidate index differs"
            )
        if self.maximum_absolute_defect < 0.0 or not np.isfinite(
            self.maximum_absolute_defect
        ):
            raise QWakeLC4RuntimeBackendError(
                "frontier-normalization defect is invalid"
            )
        if self.absolute_tolerance <= 0.0 or self.relative_tolerance <= 0.0:
            raise QWakeLC4RuntimeBackendError(
                "frontier-normalization tolerance is invalid"
            )
        for value, field_name in (
            (self.raw_frontier_sha256, "raw_frontier_sha256"),
            (self.canonical_frontier_sha256, "canonical_frontier_sha256"),
            (self.normalization_sha256, "normalization_sha256"),
        ):
            _require_sha256(value, field_name)
        if self.normalization_applied != bool(self.normalized_indices):
            raise QWakeLC4RuntimeBackendError(
                "frontier-normalization applied flag differs"
            )
        _verify_payload_digest(self, "normalization_sha256")


@dataclass(frozen=True)
class ArmExecutionRecord:
    """Serializable result for one exact or analytic matched arm."""

    arm: str
    action_id: str
    canonical_response_sha256: str
    component_manifest_sha256: str
    rng_before_sha256: str
    rng_after_sha256: str
    vjp_count: int
    fallback_invoked: bool
    cost_fields: tuple[tuple[str, int], ...]

    def require(self) -> None:
        if self.arm not in {item.value for item in BoundedArm}:
            raise QWakeLC4RuntimeBackendError("runtime arm is not registered")
        expected_action = (
            EXACT_REFERENCE_ACTION_ID
            if self.arm == BoundedArm.EXACT_REFERENCE.value
            else ANALYTIC_ACTION_ID
        )
        if self.action_id != expected_action:
            raise QWakeLC4RuntimeBackendError("runtime arm action id differs")
        for value, field_name in (
            (self.canonical_response_sha256, "canonical_response_sha256"),
            (self.component_manifest_sha256, "component_manifest_sha256"),
            (self.rng_before_sha256, "rng_before_sha256"),
            (self.rng_after_sha256, "rng_after_sha256"),
        ):
            _require_sha256(value, field_name)
        if self.vjp_count < 0:
            raise QWakeLC4RuntimeBackendError("runtime arm VJP count is negative")
        if self.fallback_invoked:
            raise QWakeLC4RuntimeBackendError(
                "normal matched runtime arm invoked fallback"
            )
        if not self.cost_fields:
            raise QWakeLC4RuntimeBackendError("runtime arm cost vector is empty")
        if any(value < 0 for _, value in self.cost_fields):
            raise QWakeLC4RuntimeBackendError(
                "runtime arm cost vector contains a negative field"
            )


@dataclass(frozen=True)
class RuntimeCellRecord:
    """Complete serializable matched-cell record."""

    position: int
    lane: str
    candidate_index: int
    repeat_index: int
    arm_order: tuple[str, str]
    opaque_state_ref: str
    exact_reference: ArmExecutionRecord
    analytic_candidate: ArmExecutionRecord
    response_defect: float
    response_passed: bool
    structural_equal: bool
    rng_post_match: bool
    cell_sha256: str

    def require(self, expected: RuntimeAuthorizationCell) -> None:
        expected_order = _cell_arm_order(expected)
        if self.position < 0:
            raise QWakeLC4RuntimeBackendError("runtime cell position is negative")
        if self.lane != expected.lane.value:
            raise QWakeLC4RuntimeBackendError("runtime cell lane differs")
        if self.candidate_index != expected.candidate_index:
            raise QWakeLC4RuntimeBackendError(
                "runtime cell candidate index differs"
            )
        if self.repeat_index != expected.repeat_index:
            raise QWakeLC4RuntimeBackendError("runtime cell repeat differs")
        if self.arm_order != tuple(item.value for item in expected_order):
            raise QWakeLC4RuntimeBackendError("runtime cell arm order differs")
        _require_sha256(self.opaque_state_ref, "opaque_state_ref")
        self.exact_reference.require()
        self.analytic_candidate.require()
        for value, field_name in (
            (self.structural_equal, "structural_equal"),
            (self.response_passed, "response_passed"),
            (self.rng_post_match, "rng_post_match"),
        ):
            if not isinstance(value, bool):
                raise QWakeLC4RuntimeBackendError(
                    f"runtime cell {field_name} is not boolean"
                )
        if self.response_defect < 0.0 or not np.isfinite(self.response_defect):
            raise QWakeLC4RuntimeBackendError(
                "runtime cell response defect is invalid"
            )
        _require_sha256(self.cell_sha256, "cell_sha256")
        _verify_payload_digest(self, "cell_sha256")

    def payload(self) -> Mapping[str, object]:
        return cast(Mapping[str, object], asdict(self))


@dataclass(frozen=True)
class ReserveProbeRecord:
    """Complete exact-reserve probe before or after one candidate group."""

    position: int
    lane: str
    candidate_index: int
    placement: str
    opaque_state_ref: str
    completed_suffix_indices: tuple[int, ...]
    no_skipped_indices: bool
    no_duplicate_indices: bool
    fallback_available: bool
    fallback_invoked: bool
    fallback_completed: bool
    fallback_response_sha256: str
    direct_reference_response_sha256: str
    rng_post_sha256: str
    passed: bool
    probe_sha256: str

    def require(self) -> None:
        if self.position < 0:
            raise QWakeLC4RuntimeBackendError("reserve-probe position is negative")
        if self.lane not in {item.value for item in RuntimeLane}:
            raise QWakeLC4RuntimeBackendError("reserve-probe lane is not registered")
        if self.candidate_index not in RUNTIME_CANDIDATE_INDICES:
            raise QWakeLC4RuntimeBackendError(
                "reserve-probe candidate index differs"
            )
        if self.placement not in {"before_repeat_zero", "after_repeat_eleven"}:
            raise QWakeLC4RuntimeBackendError(
                "reserve-probe placement is not registered"
            )
        for value, field_name in (
            (self.opaque_state_ref, "opaque_state_ref"),
            (self.fallback_response_sha256, "fallback_response_sha256"),
            (
                self.direct_reference_response_sha256,
                "direct_reference_response_sha256",
            ),
            (self.rng_post_sha256, "rng_post_sha256"),
            (self.probe_sha256, "probe_sha256"),
        ):
            _require_sha256(value, field_name)
        booleans = (
            self.no_skipped_indices,
            self.no_duplicate_indices,
            self.fallback_available,
            self.fallback_invoked,
            self.fallback_completed,
            self.passed,
        )
        if not all(isinstance(value, bool) for value in booleans):
            raise QWakeLC4RuntimeBackendError(
                "reserve-probe result contains a non-boolean field"
            )
        expected_pass = (
            self.no_skipped_indices
            and self.no_duplicate_indices
            and self.fallback_available
            and self.fallback_invoked
            and self.fallback_completed
            and self.fallback_response_sha256
            == self.direct_reference_response_sha256
        )
        if self.passed != expected_pass:
            raise QWakeLC4RuntimeBackendError(
                "reserve-probe pass flag differs from its evidence"
            )
        _verify_payload_digest(self, "probe_sha256")

    def payload(self) -> Mapping[str, object]:
        return cast(Mapping[str, object], asdict(self))


@dataclass(frozen=True)
class RuntimeMatrixResult:
    """Complete 168-cell engineering matrix and 28 reserve probes."""

    cells: tuple[RuntimeCellRecord, ...]
    reserve_probes: tuple[ReserveProbeRecord, ...]
    aggregates: tuple[Mapping[str, object], ...]

    def require(self, authorization: QWakeLC4RuntimeAuthorization) -> None:
        if len(self.cells) != len(authorization.cells):
            raise QWakeLC4RuntimeBackendError(
                "runtime matrix authorized cell count differs"
            )
        if len(self.reserve_probes) != 28:
            raise QWakeLC4RuntimeBackendError(
                "runtime matrix reserve-probe count differs"
            )
        for position, (record, expected_cell) in enumerate(
            zip(self.cells, authorization.cells, strict=True)
        ):
            if record.position != position:
                raise QWakeLC4RuntimeBackendError(
                    "runtime matrix cell positions are not contiguous"
                )
            record.require(expected_cell)
        for position, probe in enumerate(self.reserve_probes):
            if probe.position != position:
                raise QWakeLC4RuntimeBackendError(
                    "reserve-probe positions are not contiguous"
                )
            probe.require()
        if len(self.aggregates) != 14:
            raise QWakeLC4RuntimeBackendError(
                "runtime matrix aggregate count differs"
            )
        expected_aggregates = tuple(
            (lane, candidate_index)
            for lane in RuntimeLane
            for candidate_index in RUNTIME_CANDIDATE_INDICES
        )
        for position, (aggregate, expected_aggregate) in enumerate(
            zip(self.aggregates, expected_aggregates, strict=True)
        ):
            lane, candidate_index = expected_aggregate
            _require_aggregate_payload(
                aggregate,
                lane=lane,
                candidate_index=candidate_index,
                opaque_state_ref=self.cells[position * 12].opaque_state_ref,
            )


class RuntimeMatrixExecutor(Protocol):
    """Injected matrix execution surface used by the concrete backend."""

    def execute(
        self,
        authorization: QWakeLC4RuntimeAuthorization,
    ) -> RuntimeMatrixResult:
        """Execute and return the complete frozen engineering matrix."""

        ...


class BoundedTorchMatrixExecutor(RuntimeMatrixExecutor):
    """Concrete Torch executor for the frozen synthetic LC4 matrix."""

    def execute(
        self,
        authorization: QWakeLC4RuntimeAuthorization,
    ) -> RuntimeMatrixResult:
        if authorization.cells != runtime_authorization_cells():
            raise QWakeLC4RuntimeBackendError(
                "runtime authorization matrix differs from the frozen request"
            )
        if authorization.authorization_sha256 != FROZEN_AUTHORIZATION_SHA256:
            raise QWakeLC4RuntimeBackendError(
                "runtime authorization identity differs"
            )
        cells: list[RuntimeCellRecord] = []
        probes: list[ReserveProbeRecord] = []
        aggregates: list[Mapping[str, object]] = []
        cell_position = 0
        probe_position = 0

        grouped: dict[tuple[RuntimeLane, int], list[RuntimeAuthorizationCell]] = {}
        for cell in authorization.cells:
            grouped.setdefault((cell.lane, cell.candidate_index), []).append(cell)

        for lane in RuntimeLane:
            for candidate_index in RUNTIME_CANDIDATE_INDICES:
                group = grouped[(lane, candidate_index)]
                if tuple(item.repeat_index for item in group) != tuple(range(12)):
                    raise QWakeLC4RuntimeBackendError(
                        "runtime matrix group repeat order differs"
                    )
                with preserve_outer_rng():
                    snapshot, normalization = _build_snapshot(
                        lane, candidate_index
                    )
                    rng_snapshot = capture_rng_snapshot()
                    cost_pairs: list[CostPair] = []
                    for cell in group:
                        if cell.reserve_probe_before_repeat_zero:
                            probes.append(
                                _run_reserve_probe(
                                    snapshot,
                                    rng_snapshot,
                                    lane=lane,
                                    candidate_index=candidate_index,
                                    placement="before_repeat_zero",
                                    position=probe_position,
                                )
                            )
                            probe_position += 1
                        record, cost_pair = _run_matched_cell(
                            snapshot,
                            rng_snapshot,
                            cell,
                            position=cell_position,
                        )
                        cells.append(record)
                        cost_pairs.append(cost_pair)
                        cell_position += 1
                        if cell.reserve_probe_after_repeat_eleven:
                            probes.append(
                                _run_reserve_probe(
                                    snapshot,
                                    rng_snapshot,
                                    lane=lane,
                                    candidate_index=candidate_index,
                                    placement="after_repeat_eleven",
                                    position=probe_position,
                                )
                            )
                            probe_position += 1
                    aggregation = aggregate_paired_costs(cost_pairs)
                    aggregates.append(
                        _aggregation_payload(
                            lane,
                            candidate_index,
                            snapshot.opaque_state_ref,
                            aggregation,
                            normalization,
                        )
                    )

        result = RuntimeMatrixResult(
            cells=tuple(cells),
            reserve_probes=tuple(probes),
            aggregates=tuple(aggregates),
        )
        result.require(authorization)
        return result


class QWakeLC4RuntimeBackend(RuntimeExecutionBackend):
    """Wrapper-compatible backend guarded by an immutable execution freeze."""

    def __init__(
        self,
        *,
        project_root: Path,
        torch2pc_dir: Path,
        execution_freeze: MaterializedExecutionFreeze,
        matrix_executor: RuntimeMatrixExecutor | None = None,
    ) -> None:
        self.project_root = project_root.expanduser().resolve()
        self.torch2pc_dir = torch2pc_dir.expanduser().resolve()
        expected_torch2pc = (self.project_root / "external/Torch2PC").resolve()
        if self.torch2pc_dir != expected_torch2pc:
            raise QWakeLC4RuntimeBackendError(
                "runtime backend Torch2PC path differs from the project checkout"
            )
        self.execution_freeze = execution_freeze
        self.matrix_executor = (
            BoundedTorchMatrixExecutor()
            if matrix_executor is None
            else matrix_executor
        )

    @property
    def backend_id(self) -> str:
        return RUNTIME_BACKEND_ID

    def run(
        self,
        staging_root: Path,
        lease: ProspectiveExecutionLease,
        contract: ExecutionWrapperContract,
    ) -> RuntimeBackendReceipt:
        self.execution_freeze.require()
        verified = verify_materialized_execution_freeze(self.project_root)
        if verified != self.execution_freeze:
            raise QWakeLC4RuntimeBackendError(
                "runtime backend execution-freeze identity changed"
            )
        _require_git_commit(
            self.torch2pc_dir, self.execution_freeze.torch2pc_commit
        )
        lease.require()
        contract.require()
        if lease.wrapper_commit != self.execution_freeze.wrapper_commit:
            raise QWakeLC4RuntimeBackendError(
                "runtime backend lease wrapper commit differs"
            )
        if contract.wrapper_commit != self.execution_freeze.wrapper_commit:
            raise QWakeLC4RuntimeBackendError(
                "runtime backend contract wrapper commit differs"
            )
        if lease.authorization_sha256 != FROZEN_AUTHORIZATION_SHA256:
            raise QWakeLC4RuntimeBackendError(
                "runtime backend lease authorization differs"
            )
        if contract.authorization_sha256 != FROZEN_AUTHORIZATION_SHA256:
            raise QWakeLC4RuntimeBackendError(
                "runtime backend contract authorization differs"
            )
        root = staging_root.expanduser().resolve()
        if not root.is_dir() or root.is_symlink():
            raise QWakeLC4RuntimeBackendError(
                "runtime backend staging root is absent or non-directory"
            )
        if tuple(root.iterdir()):
            raise QWakeLC4RuntimeBackendError(
                "runtime backend staging root is not empty"
            )

        authorization = load_runtime_authorization(
            self.project_root / RUNTIME_AUTHORIZATION_RELATIVE
        )
        if authorization.authorization_sha256 != lease.authorization_sha256:
            raise QWakeLC4RuntimeBackendError(
                "runtime backend frozen authorization differs from lease"
            )
        matrix = self.matrix_executor.execute(authorization)
        matrix.require(authorization)

        cells_bytes = _jsonl_bytes(item.payload() for item in matrix.cells)
        probes_bytes = _jsonl_bytes(
            item.payload() for item in matrix.reserve_probes
        )
        aggregates_payload = {
            "schema_version": 1,
            "aggregate_id": "stage3b-qwake-lc4-e-paired-cost-aggregates-v1",
            "items": matrix.aggregates,
        }
        aggregates_bytes = canonical_json(aggregates_payload).encode("utf-8")
        identities_payload: dict[str, object] = {
            "schema_version": 1,
            "backend_id": self.backend_id,
            "execution_freeze_sha256": self.execution_freeze.freeze_sha256,
            "source_commit": self.execution_freeze.source_commit,
            "wrapper_commit": self.execution_freeze.wrapper_commit,
            "torch2pc_commit": self.execution_freeze.torch2pc_commit,
            "image_digest": self.execution_freeze.image_digest,
            "image_repo_digest": self.execution_freeze.image_repo_digest,
            "authorization_sha256": authorization.authorization_sha256,
            "lease_sha256": lease.lease_sha256,
            "wrapper_contract_sha256": contract.contract_sha256,
            "output_root": AUTHORIZED_OUTPUT_ROOT,
            "engineering_evidence_only": True,
            "scientific_execution_open": False,
            "test_dataset_access": False,
            "publication_permitted": False,
        }
        identities_bytes = canonical_json(identities_payload).encode("utf-8")
        all_response_comparisons_passed = all(
            item.response_passed for item in matrix.cells
        )
        all_rng_matches_passed = all(
            item.rng_post_match for item in matrix.cells
        )
        all_reserve_probes_passed = all(
            item.passed for item in matrix.reserve_probes
        )
        all_order_effect_gates_passed = all(
            item.get("order_effect_passed") is True
            for item in matrix.aggregates
        )
        all_pairs_complete = all(
            item.get("pair_complete") is True
            for item in matrix.aggregates
        )
        validation_passed = all(
            (
                all_response_comparisons_passed,
                all_rng_matches_passed,
                all_reserve_probes_passed,
                all_order_effect_gates_passed,
                all_pairs_complete,
            )
        )
        report_payload: dict[str, object] = {
            "schema_version": 1,
            "report_id": RUNTIME_BACKEND_REPORT_ID,
            "status": (
                "engineering_matrix_completed_validation_passed"
                if validation_passed
                else "engineering_matrix_completed_validation_failed"
            ),
            "backend_id": self.backend_id,
            "execution_freeze_sha256": self.execution_freeze.freeze_sha256,
            "authorization_sha256": authorization.authorization_sha256,
            "lease_sha256": lease.lease_sha256,
            "wrapper_contract_sha256": contract.contract_sha256,
            "authorized_cell_count": len(matrix.cells),
            "reserve_probe_count": len(matrix.reserve_probes),
            "aggregate_count": len(matrix.aggregates),
            "all_response_comparisons_passed": (
                all_response_comparisons_passed
            ),
            "all_rng_matches_passed": all_rng_matches_passed,
            "all_reserve_probes_passed": all_reserve_probes_passed,
            "all_order_effect_gates_passed": (
                all_order_effect_gates_passed
            ),
            "all_pairs_complete": all_pairs_complete,
            "validation_passed": validation_passed,
            "engineering_evidence_present": True,
            "scientific_execution_open": False,
            "test_dataset_access": False,
            "publication_permitted": False,
        }
        report_payload["report_sha256"] = sha256_object(report_payload)
        report_bytes = canonical_json(report_payload).encode("utf-8")

        initial_files = {
            _RUNTIME_REPORT_RELATIVE: report_bytes,
            _MATCHED_CELLS_RELATIVE: cells_bytes,
            _RESERVE_PROBES_RELATIVE: probes_bytes,
            _AGGREGATES_RELATIVE: aggregates_bytes,
            _IDENTITIES_RELATIVE: identities_bytes,
        }
        for relative, content in initial_files.items():
            _write_exclusive_regular(root / relative, content)

        receipt = build_runtime_backend_receipt(
            backend_id=self.backend_id,
            wrapper_commit=lease.wrapper_commit,
            lease_sha256=lease.lease_sha256,
            output_file_count=_EXPECTED_BACKEND_OUTPUT_FILE_COUNT,
        )
        _write_exclusive_regular(
            root / _BACKEND_RECEIPT_RELATIVE,
            receipt.canonical_json().encode("utf-8"),
        )
        sums = []
        for relative in sorted(
            (*initial_files, _BACKEND_RECEIPT_RELATIVE),
            key=lambda item: item.as_posix(),
        ):
            content = (root / relative).read_bytes()
            sums.append(f"{hashlib.sha256(content).hexdigest()}  {relative.as_posix()}\n")
        _write_exclusive_regular(
            root / _BACKEND_SUMS_RELATIVE,
            "".join(sums).encode("utf-8"),
        )
        observed_count = sum(1 for path in root.rglob("*") if path.is_file())
        if observed_count != _EXPECTED_BACKEND_OUTPUT_FILE_COUNT:
            raise QWakeLC4RuntimeBackendError(
                "runtime backend output file count differs"
            )
        return receipt


def inspect_runtime_frontier_normalization(
    lane: RuntimeLane,
    candidate_index: int,
) -> FrontierNormalizationRecord:
    """Return the pure runtime-frontier normalization record."""

    with preserve_outer_rng():
        _snapshot, normalization = _build_snapshot(lane, candidate_index)
    return normalization


def execute_bounded_runtime_cell(
    cell: RuntimeAuthorizationCell,
) -> RuntimeCellRecord:
    """Execute one in-memory cell for independent engineering validation."""

    with preserve_outer_rng():
        snapshot, _normalization = _build_snapshot(
            cell.lane, cell.candidate_index
        )
        rng_snapshot = capture_rng_snapshot()
        record, _cost_pair = _run_matched_cell(
            snapshot,
            rng_snapshot,
            cell,
            position=0,
        )
    return record


def load_materialized_execution_freeze(
    path: Path,
) -> MaterializedExecutionFreeze:
    """Load one canonical immutable execution-freeze record."""

    payload = _read_json_object(path)
    freeze = MaterializedExecutionFreeze(
        schema_version=_integer(payload.get("schema_version"), "schema_version"),
        freeze_id=_string(payload.get("freeze_id"), "freeze_id"),
        status=_string(payload.get("status"), "status"),
        source_commit=_string(payload.get("source_commit"), "source_commit"),
        wrapper_commit=_string(payload.get("wrapper_commit"), "wrapper_commit"),
        torch2pc_commit=_string(payload.get("torch2pc_commit"), "torch2pc_commit"),
        image_digest=_string(payload.get("image_digest"), "image_digest"),
        image_repo_digest=_string(
            payload.get("image_repo_digest"), "image_repo_digest"
        ),
        backend_id=_string(payload.get("backend_id"), "backend_id"),
        backend_module_path=_string(
            payload.get("backend_module_path"), "backend_module_path"
        ),
        backend_module_sha256=_string(
            payload.get("backend_module_sha256"), "backend_module_sha256"
        ),
        entrypoint_id=_string(payload.get("entrypoint_id"), "entrypoint_id"),
        entrypoint_path=_string(payload.get("entrypoint_path"), "entrypoint_path"),
        entrypoint_sha256=_string(
            payload.get("entrypoint_sha256"), "entrypoint_sha256"
        ),
        authoring_request_id=_string(
            payload.get("authoring_request_id"), "authoring_request_id"
        ),
        authoring_request_sha256=_string(
            payload.get("authoring_request_sha256"),
            "authoring_request_sha256",
        ),
        admission_sha256=_string(
            payload.get("admission_sha256"), "admission_sha256"
        ),
        authorization_sha256=_string(
            payload.get("authorization_sha256"), "authorization_sha256"
        ),
        execution_count=_integer(payload.get("execution_count"), "execution_count"),
        concrete_runtime_backend_present=_boolean(
            payload.get("concrete_runtime_backend_present"),
            "concrete_runtime_backend_present",
        ),
        one_shot_entrypoint_present=_boolean(
            payload.get("one_shot_entrypoint_present"),
            "one_shot_entrypoint_present",
        ),
        immutable_execution_image_present=_boolean(
            payload.get("immutable_execution_image_present"),
            "immutable_execution_image_present",
        ),
        execution_freeze_materialized=_boolean(
            payload.get("execution_freeze_materialized"),
            "execution_freeze_materialized",
        ),
        runtime_execution_permitted=_boolean(
            payload.get("runtime_execution_permitted"),
            "runtime_execution_permitted",
        ),
        execution_lease_materialized=_boolean(
            payload.get("execution_lease_materialized"),
            "execution_lease_materialized",
        ),
        authorization_consumed=_boolean(
            payload.get("authorization_consumed"), "authorization_consumed"
        ),
        runtime_execution_started=_boolean(
            payload.get("runtime_execution_started"), "runtime_execution_started"
        ),
        runtime_execution_performed=_boolean(
            payload.get("runtime_execution_performed"),
            "runtime_execution_performed",
        ),
        engineering_evidence_present=_boolean(
            payload.get("engineering_evidence_present"),
            "engineering_evidence_present",
        ),
        scientific_execution_open=_boolean(
            payload.get("scientific_execution_open"), "scientific_execution_open"
        ),
        test_dataset_access=_boolean(
            payload.get("test_dataset_access"), "test_dataset_access"
        ),
        publication_permitted=_boolean(
            payload.get("publication_permitted"), "publication_permitted"
        ),
        local_compute_execution_open=_boolean(
            payload.get("local_compute_execution_open"),
            "local_compute_execution_open",
        ),
        freeze_sha256=_string(payload.get("freeze_sha256"), "freeze_sha256"),
    )
    freeze.require()
    if path.read_bytes() != freeze.canonical_json().encode("utf-8"):
        raise QWakeLC4RuntimeBackendError(
            "materialized execution-freeze serialization differs"
        )
    return freeze


def verify_materialized_execution_freeze(
    project_root: Path,
) -> MaterializedExecutionFreeze:
    """Verify the future immutable execution freeze before lease claim."""

    root = project_root.expanduser().resolve()
    freeze_root = root / MATERIALIZED_EXECUTION_FREEZE_ROOT
    freeze_path = root / MATERIALIZED_EXECUTION_FREEZE_RELATIVE
    registry_path = root / MATERIALIZED_EXECUTION_FREEZE_REGISTRY_RELATIVE
    if not freeze_root.is_dir() or freeze_root.is_symlink():
        raise QWakeLC4RuntimeBackendError(
            "materialized execution-freeze package is absent"
        )
    if not freeze_path.is_file() or freeze_path.is_symlink():
        raise QWakeLC4RuntimeBackendError(
            "materialized execution-freeze record is absent"
        )
    if not registry_path.is_file() or registry_path.is_symlink():
        raise QWakeLC4RuntimeBackendError(
            "materialized execution-freeze registry is absent"
        )
    registry = _read_registry(registry_path)
    observed_files: set[str] = set()
    for target in freeze_root.rglob("*"):
        if target.is_symlink() or not target.is_file():
            raise QWakeLC4RuntimeBackendError(
                "materialized execution-freeze package contains a non-regular entry"
            )
        observed_files.add(target.relative_to(freeze_root).as_posix())
    expected_files = set(registry) | {"SHA256SUMS"}
    if observed_files != expected_files:
        raise QWakeLC4RuntimeBackendError(
            "materialized execution-freeze package file set differs"
        )
    if registry.get("execution.json") != _sha256_file(freeze_path):
        raise QWakeLC4RuntimeBackendError(
            "materialized execution-freeze registry digest differs"
        )
    for relative, expected in registry.items():
        target = freeze_root / relative
        if not target.is_file() or target.is_symlink():
            raise QWakeLC4RuntimeBackendError(
                "materialized execution-freeze package contains a non-regular file"
            )
        if _sha256_file(target) != expected:
            raise QWakeLC4RuntimeBackendError(
                f"materialized execution-freeze file digest differs: {relative}"
            )
    freeze = load_materialized_execution_freeze(freeze_path)
    module_path = root / freeze.backend_module_path
    entrypoint_path = root / freeze.entrypoint_path
    if _sha256_file(module_path) != freeze.backend_module_sha256:
        raise QWakeLC4RuntimeBackendError("runtime backend module digest differs")
    if _sha256_file(entrypoint_path) != freeze.entrypoint_sha256:
        raise QWakeLC4RuntimeBackendError("one-shot entrypoint digest differs")
    source_commit = os.environ.get("SOURCE_GIT_COMMIT", "").strip()
    if source_commit != freeze.source_commit:
        raise QWakeLC4RuntimeBackendError(
            "runtime image source commit differs from execution freeze"
        )
    if os.environ.get("EXPERIMENT_IMAGE_DIGEST", "").strip() != freeze.image_digest:
        raise QWakeLC4RuntimeBackendError(
            "runtime image digest differs from execution freeze"
        )
    if os.environ.get("EXPERIMENT_IMAGE_REPO_DIGEST", "").strip() != (
        freeze.image_repo_digest
    ):
        raise QWakeLC4RuntimeBackendError(
            "runtime image repo digest differs from execution freeze"
        )
    _require_git_commit(root / "external/Torch2PC", freeze.torch2pc_commit)
    return freeze


def run_one_shot_authorized_runtime(
    project_root: Path,
    torch2pc_dir: Path,
    *,
    claimed_at_utc: str,
    operator_acknowledgement: str,
) -> ExecutionWrapperOutcome:
    """Verify freeze, claim once, and execute in the same process."""

    root = project_root.expanduser().resolve()
    resolved_torch2pc = torch2pc_dir.expanduser().resolve()
    if resolved_torch2pc != (root / "external/Torch2PC").resolve():
        raise QWakeLC4RuntimeBackendError(
            "one-shot Torch2PC path differs from the project checkout"
        )
    freeze = verify_materialized_execution_freeze(root)
    if operator_acknowledgement != EXECUTION_LEASE_OPERATOR_ACKNOWLEDGEMENT:
        raise QWakeLC4RuntimeBackendError(
            "one-shot operator acknowledgement differs"
        )
    backend = QWakeLC4RuntimeBackend(
        project_root=root,
        torch2pc_dir=resolved_torch2pc,
        execution_freeze=freeze,
    )
    claim_execution_lease(
        root,
        claimed_at_utc=claimed_at_utc,
        wrapper_commit=freeze.wrapper_commit,
        operator_acknowledgement=operator_acknowledgement,
    )
    return execute_authorized_runtime(
        root,
        expected_wrapper_commit=freeze.wrapper_commit,
        backend=backend,
    )


def _build_snapshot(
    lane: RuntimeLane,
    candidate_index: int,
) -> tuple[OpaqueStateSnapshot, FrontierNormalizationRecord]:
    device, dtype = _lane_device_dtype(lane)
    torch.manual_seed(RUNTIME_MODEL_SEED)
    random.seed(RUNTIME_MODEL_SEED)
    np.random.seed(RUNTIME_MODEL_SEED)
    model = build_model("lenet_classic").to(device=device, dtype=dtype)
    inputs, targets = _synthetic_batch(RUNTIME_MODEL_SEED)
    inputs = inputs.to(device=device, dtype=dtype)
    targets = targets.to(device=device)
    loss_fn = nn.CrossEntropyLoss()
    raw_frontier = capture_fixedpred_frontier(
        model,
        loss_fn,
        inputs,
        targets,
        candidate_index=candidate_index,
    )
    frontier, normalization = _canonicalize_runtime_frontier(
        raw_frontier,
        lane,
    )
    adapter = RuntimeFrontierAdapter(lane)
    snapshot = adapter.capture(
        model,
        fixed=frontier.fixed,
        beliefs=frontier.beliefs,
        errors=frontier.errors,
        endpoint_loss=frontier.endpoint_loss,
        candidate_index=candidate_index,
        input_batch=inputs,
        target_batch=targets,
        model_seed=RUNTIME_MODEL_SEED,
        batch_id=RUNTIME_ENGINEERING_BATCH_ID,
        comparison_profile_id=lane.value,
        cost_profile_id="shadow_mechanism_v1",
        deterministic_runtime_controls={
            "data_classification": "synthetic_engineering_batch",
            "runtime_execution_permitted": True,
            "scientific_execution_open": False,
            "test_dataset_access": False,
            "publication_permitted": False,
            "deterministic_algorithms": True,
            "fixedpred_eta": 1,
            "model_id": "lenet_classic",
            "method_id": "stage2_baseline_fixedpred",
            "frontier_normalization_applied": (
                normalization.normalization_applied
            ),
            "frontier_normalization_max_abs": (
                normalization.maximum_absolute_defect
            ),
            "raw_frontier_sha256": normalization.raw_frontier_sha256,
            "canonical_frontier_sha256": (
                normalization.canonical_frontier_sha256
            ),
        },
    )
    return snapshot, normalization


def _canonicalize_runtime_frontier(
    frontier: FixedPredFrontier,
    lane: RuntimeLane,
) -> tuple[FixedPredFrontier, FrontierNormalizationRecord]:
    """Canonicalize only algebraically completed upper residuals."""

    raw_sha256 = _frontier_sha256(frontier)
    errors = [
        None if item is None else item.detach().clone()
        for item in frontier.errors
    ]
    depth = len(frontier.fixed) - 1
    boundary = depth - frontier.candidate_index
    absolute_tolerance = (
        1.0e-12
        if lane is RuntimeLane.CPU_FLOAT64_ENGINEERING
        else 1.0e-5
    )
    relative_tolerance = (
        1.0e-10
        if lane is RuntimeLane.CPU_FLOAT64_ENGINEERING
        else 1.0e-4
    )
    normalized: list[int] = []
    maximum_defect = 0.0
    for index in range(boundary + 1, len(frontier.fixed) - 1):
        error = errors[index]
        if error is None:
            raise QWakeLC4RuntimeBackendError(
                "completed runtime upper error is absent"
            )
        residual = frontier.fixed[index] - frontier.beliefs[index]
        defect = float(torch.max(torch.abs(error - residual)).item())
        maximum_defect = max(maximum_defect, defect)
        scale = max(
            float(torch.max(torch.abs(error)).item()),
            float(torch.max(torch.abs(residual)).item()),
            1.0,
        )
        if defect > absolute_tolerance + relative_tolerance * scale:
            raise QWakeLC4RuntimeBackendError(
                "runtime upper-wavefront defect exceeds canonical tolerance"
            )
        if not torch.equal(error, residual):
            errors[index] = residual.detach().clone()
            normalized.append(index)
    canonical = FixedPredFrontier(
        fixed=tuple(item.detach().clone() for item in frontier.fixed),
        beliefs=tuple(item.detach().clone() for item in frontier.beliefs),
        errors=tuple(errors),
        endpoint_loss=frontier.endpoint_loss.detach().clone(),
        candidate_index=frontier.candidate_index,
    )
    canonical_sha256 = _frontier_sha256(canonical)
    payload: dict[str, object] = {
        "lane": lane.value,
        "candidate_index": frontier.candidate_index,
        "normalized_indices": tuple(normalized),
        "maximum_absolute_defect": maximum_defect,
        "absolute_tolerance": absolute_tolerance,
        "relative_tolerance": relative_tolerance,
        "raw_frontier_sha256": raw_sha256,
        "canonical_frontier_sha256": canonical_sha256,
        "normalization_applied": bool(normalized),
    }
    record = FrontierNormalizationRecord(
        lane=lane.value,
        candidate_index=frontier.candidate_index,
        normalized_indices=tuple(normalized),
        maximum_absolute_defect=maximum_defect,
        absolute_tolerance=absolute_tolerance,
        relative_tolerance=relative_tolerance,
        raw_frontier_sha256=raw_sha256,
        canonical_frontier_sha256=canonical_sha256,
        normalization_applied=bool(normalized),
        normalization_sha256=sha256_object(payload),
    )
    record.require()
    return canonical, record


def _frontier_sha256(frontier: FixedPredFrontier) -> str:
    def tensor_entry(value: Tensor) -> Mapping[str, object]:
        detached = value.detach().cpu().contiguous()
        return {
            "shape": tuple(int(item) for item in detached.shape),
            "dtype": str(detached.dtype),
            "sha256": (
                "sha256:"
                + hashlib.sha256(detached.numpy().tobytes()).hexdigest()
            ),
        }

    payload = {
        "candidate_index": frontier.candidate_index,
        "fixed": tuple(tensor_entry(item) for item in frontier.fixed),
        "beliefs": tuple(tensor_entry(item) for item in frontier.beliefs),
        "errors": tuple(
            None if item is None else tensor_entry(item)
            for item in frontier.errors
        ),
        "endpoint_loss": tensor_entry(frontier.endpoint_loss),
    }
    return sha256_object(payload)


def _run_matched_cell(
    snapshot: OpaqueStateSnapshot,
    rng_snapshot: object,
    cell: RuntimeAuthorizationCell,
    *,
    position: int,
) -> tuple[RuntimeCellRecord, CostPair]:
    order = _cell_arm_order(cell)
    arm_records: dict[BoundedArm, ArmExecutionRecord] = {}
    responses: dict[BoundedArm, CanonicalResponse] = {}
    cost_vectors: dict[BoundedArm, CostVector] = {}
    with preserve_outer_rng():
        for arm in order:
            restore_rng_snapshot(cast(Any, rng_snapshot))
            rng_before = capture_rng_snapshot()
            model, frontier = snapshot.fork()
            completion, vector = _measure_completion(
                model,
                frontier,
                snapshot,
                arm,
                repeat_index=cell.repeat_index,
            )
            response = materialize_required_response(
                model,
                completion,
                state_id=snapshot.opaque_state_ref,
                comparison_profile_id=snapshot.comparison_profile_id,
            )
            rng_after = capture_rng_snapshot()
            responses[arm] = response
            arm_records[arm] = ArmExecutionRecord(
                arm=arm.value,
                action_id=completion.action_id,
                canonical_response_sha256=response.canonical_response_sha256,
                component_manifest_sha256=response.component_manifest_sha256,
                rng_before_sha256=rng_before.snapshot_sha256,
                rng_after_sha256=rng_after.snapshot_sha256,
                vjp_count=completion.vjp_count,
                fallback_invoked=completion.fallback_invoked,
                cost_fields=tuple(vector.active_values().items()),
            )
            cost_vectors[arm] = vector
    exact_response = arm_records[BoundedArm.EXACT_REFERENCE]
    analytic_response = arm_records[BoundedArm.ANALYTIC_CANDIDATE]
    arm_order = (order[0].value, order[1].value)

    comparison = compare_required_responses(
        responses[BoundedArm.EXACT_REFERENCE],
        responses[BoundedArm.ANALYTIC_CANDIDATE],
    )
    payload: dict[str, object] = {
        "position": position,
        "lane": cell.lane.value,
        "candidate_index": cell.candidate_index,
        "repeat_index": cell.repeat_index,
        "arm_order": arm_order,
        "opaque_state_ref": snapshot.opaque_state_ref,
        "exact_reference": asdict(exact_response),
        "analytic_candidate": asdict(analytic_response),
        "response_defect": comparison.response_defect,
        "response_passed": comparison.passed,
        "structural_equal": comparison.structural_equal,
        "rng_post_match": (
            exact_response.rng_before_sha256
            == analytic_response.rng_before_sha256
            and exact_response.rng_after_sha256
            == analytic_response.rng_after_sha256
        ),
    }
    record = RuntimeCellRecord(
        position=position,
        lane=cell.lane.value,
        candidate_index=cell.candidate_index,
        repeat_index=cell.repeat_index,
        arm_order=arm_order,
        opaque_state_ref=snapshot.opaque_state_ref,
        exact_reference=exact_response,
        analytic_candidate=analytic_response,
        response_defect=comparison.response_defect,
        response_passed=comparison.passed,
        structural_equal=comparison.structural_equal,
        rng_post_match=cast(bool, payload["rng_post_match"]),
        cell_sha256=sha256_object(payload),
    )
    record.require(cell)
    pair = CostPair(
        repeat_index=cell.repeat_index,
        arm_order=order,
        exact_reference=cost_vectors[BoundedArm.EXACT_REFERENCE],
        analytic_candidate=cost_vectors[BoundedArm.ANALYTIC_CANDIDATE],
    )
    return record, pair


def _measure_completion(
    model: nn.Sequential,
    frontier: FixedPredFrontier,
    snapshot: OpaqueStateSnapshot,
    arm: BoundedArm,
    *,
    repeat_index: int,
) -> tuple[CompletionResult, CostVector]:
    lane = RuntimeLane(snapshot.lane_profile_id)
    root_start = time.perf_counter_ns()
    memory_before = _memory_snapshot(lane)
    primary_start, event_pair = _primary_start(lane)
    completion = (
        complete_exact_suffix(model, frontier)
        if arm is BoundedArm.EXACT_REFERENCE
        else analytic_wavefront_completion(model, frontier)
    )
    primary_end = _primary_end(lane, primary_start, event_pair)
    root_end = max(time.perf_counter_ns(), root_start + 1)
    memory_after = _memory_snapshot(lane)
    allocated = max(memory_before[0], memory_after[0])
    reserved = max(memory_before[1], memory_after[1], allocated)
    primary_clock = (
        "host_process_time_ns"
        if lane is RuntimeLane.CPU_FLOAT64_ENGINEERING
        else "rocm_event_time_ns"
    )
    trajectory = ResourceTrajectory(
        trajectory_schema_id="stage3b-qwake-resource-trajectory-v1",
        action_id=completion.action_id,
        mechanism_id=(
            "complete_exact_suffix_stage2_baseline_v1"
            if arm is BoundedArm.EXACT_REFERENCE
            else "fixedpred_eta1_wavefront_completion_v1"
        ),
        opaque_state_ref=snapshot.opaque_state_ref,
        repeat_index=repeat_index,
        lane_profile_id=lane.value,
        cost_profile_id=snapshot.cost_profile_id,
        root_clock_domain="host_monotonic_ns",
        root_start_ns=root_start,
        root_end_ns=root_end,
        intervals=(
            IntervalRecord(
                position=0,
                owner=IntervalOwner.CORE_COMPUTE,
                lane=("cpu" if lane is RuntimeLane.CPU_FLOAT64_ENGINEERING else "rocm"),
                clock_domain=primary_clock,
                start_ns=0,
                end_ns=max(primary_end, 1),
                source=(
                    "time_process_time_ns"
                    if lane is RuntimeLane.CPU_FLOAT64_ENGINEERING
                    else "torch_cuda_event_elapsed_time"
                ),
            ),
        ),
        memory=(
            MemoryRecord(
                metric="peak_allocated_bytes",
                value_bytes=allocated,
                source=(
                    "psutil_process_uss"
                    if lane is RuntimeLane.CPU_FLOAT64_ENGINEERING
                    else "torch_cuda_max_memory_allocated"
                ),
            ),
            MemoryRecord(
                metric="peak_reserved_bytes",
                value_bytes=reserved,
                source=(
                    "psutil_process_rss"
                    if lane is RuntimeLane.CPU_FLOAT64_ENGINEERING
                    else "torch_cuda_max_memory_reserved"
                ),
            ),
        ),
        artifacts=cast(tuple[ArtifactRecord, ...], ()),
        observer_calibration=ObserverCalibration(
            pair_id=(
                f"{lane.value}:candidate-{snapshot.frontier.candidate_index}:"
                f"repeat-{repeat_index}"
            ),
            instrumented_latency_ns=0,
            control_latency_ns=0,
            raw_residual_ns=0,
            overclosure=False,
        ),
        fallback=FallbackRecord(
            fallback_available=True,
            fallback_invoked=False,
            fallback_completed=False,
        ),
    )
    return completion, map_resource_trajectory(trajectory)


def _run_reserve_probe(
    snapshot: OpaqueStateSnapshot,
    rng_snapshot: object,
    *,
    lane: RuntimeLane,
    candidate_index: int,
    placement: str,
    position: int,
) -> ReserveProbeRecord:
    with preserve_outer_rng():
        restore_rng_snapshot(cast(Any, rng_snapshot))
        fallback_model, fallback_frontier = snapshot.fork()
        fallback = complete_exact_suffix(
            fallback_model,
            fallback_frontier,
            fallback_invoked=True,
        )
        fallback_response = materialize_required_response(
            fallback_model,
            fallback,
            state_id=snapshot.opaque_state_ref,
            comparison_profile_id=snapshot.comparison_profile_id,
        )
        restore_rng_snapshot(cast(Any, rng_snapshot))
        direct_model, direct_frontier = snapshot.fork()
        direct = complete_exact_suffix(direct_model, direct_frontier)
        direct_response = materialize_required_response(
            direct_model,
            direct,
            state_id=snapshot.opaque_state_ref,
            comparison_profile_id=snapshot.comparison_profile_id,
        )
        rng_post = capture_rng_snapshot()
    completed = tuple(range(candidate_index + 1, len(direct_model) + 1))
    payload: dict[str, object] = {
        "position": position,
        "lane": lane.value,
        "candidate_index": candidate_index,
        "placement": placement,
        "opaque_state_ref": snapshot.opaque_state_ref,
        "completed_suffix_indices": completed,
        "no_skipped_indices": True,
        "no_duplicate_indices": len(completed) == len(set(completed)),
        "fallback_available": True,
        "fallback_invoked": True,
        "fallback_completed": True,
        "fallback_response_sha256": fallback_response.canonical_response_sha256,
        "direct_reference_response_sha256": (
            direct_response.canonical_response_sha256
        ),
        "rng_post_sha256": rng_post.snapshot_sha256,
        "passed": (
            fallback_response.canonical_response_sha256
            == direct_response.canonical_response_sha256
        ),
    }
    record = ReserveProbeRecord(
        position=position,
        lane=lane.value,
        candidate_index=candidate_index,
        placement=placement,
        opaque_state_ref=snapshot.opaque_state_ref,
        completed_suffix_indices=completed,
        no_skipped_indices=True,
        no_duplicate_indices=len(completed) == len(set(completed)),
        fallback_available=True,
        fallback_invoked=True,
        fallback_completed=True,
        fallback_response_sha256=fallback_response.canonical_response_sha256,
        direct_reference_response_sha256=(
            direct_response.canonical_response_sha256
        ),
        rng_post_sha256=rng_post.snapshot_sha256,
        passed=cast(bool, payload["passed"]),
        probe_sha256=sha256_object(payload),
    )
    record.require()
    return record


def _cell_arm_order(
    cell: RuntimeAuthorizationCell,
) -> tuple[BoundedArm, BoundedArm]:
    expected = pair_schedule()[cell.repeat_index]
    frozen = (
        (BoundedArm.EXACT_REFERENCE, BoundedArm.ANALYTIC_CANDIDATE)
        if cell.arm_order is RuntimeArmOrder.EXACT_THEN_ANALYTIC
        else (BoundedArm.ANALYTIC_CANDIDATE, BoundedArm.EXACT_REFERENCE)
    )
    if frozen != expected:
        raise QWakeLC4RuntimeBackendError(
            "runtime authorization arm order differs from LC3"
        )
    return frozen


def _aggregation_payload(
    lane: RuntimeLane,
    candidate_index: int,
    opaque_state_ref: str,
    aggregation: PairedCostAggregation,
    normalization: FrontierNormalizationRecord,
) -> Mapping[str, object]:
    payload: dict[str, object] = {
        "lane": lane.value,
        "candidate_index": candidate_index,
        "opaque_state_ref": opaque_state_ref,
        "aggregate_id": aggregation.aggregate_id,
        "field_summaries": tuple(
            (name, asdict(summary))
            for name, summary in aggregation.field_summaries
        ),
        "order_effect_passed": aggregation.order_effect_passed,
        "pair_complete": aggregation.pair_complete,
        "frontier_normalization": asdict(normalization),
    }
    payload["aggregate_sha256"] = sha256_object(payload)
    return payload



def _require_aggregate_payload(
    aggregate: Mapping[str, object],
    *,
    lane: RuntimeLane,
    candidate_index: int,
    opaque_state_ref: str,
) -> None:
    expected_keys = {
        "lane",
        "candidate_index",
        "opaque_state_ref",
        "aggregate_id",
        "field_summaries",
        "order_effect_passed",
        "pair_complete",
        "frontier_normalization",
        "aggregate_sha256",
    }
    if set(aggregate) != expected_keys:
        raise QWakeLC4RuntimeBackendError(
            "runtime matrix aggregate field set differs"
        )
    if aggregate.get("lane") != lane.value:
        raise QWakeLC4RuntimeBackendError(
            "runtime matrix aggregate lane differs"
        )
    if aggregate.get("candidate_index") != candidate_index:
        raise QWakeLC4RuntimeBackendError(
            "runtime matrix aggregate candidate differs"
        )
    if aggregate.get("opaque_state_ref") != opaque_state_ref:
        raise QWakeLC4RuntimeBackendError(
            "runtime matrix aggregate opaque state differs"
        )
    if aggregate.get("aggregate_id") != "stage3b-qwake-paired-aggregation-v1":
        raise QWakeLC4RuntimeBackendError(
            "runtime matrix aggregate id differs"
        )
    if aggregate.get("pair_complete") is not True:
        raise QWakeLC4RuntimeBackendError(
            "runtime matrix aggregate pair is incomplete"
        )
    if not isinstance(aggregate.get("order_effect_passed"), bool):
        raise QWakeLC4RuntimeBackendError(
            "runtime matrix aggregate order-effect result is not boolean"
        )
    summaries = aggregate.get("field_summaries")
    if not isinstance(summaries, tuple | list) or not summaries:
        raise QWakeLC4RuntimeBackendError(
            "runtime matrix aggregate summaries are absent"
        )
    normalization = aggregate.get("frontier_normalization")
    if not isinstance(normalization, Mapping):
        raise QWakeLC4RuntimeBackendError(
            "runtime matrix aggregate normalization is absent"
        )
    if normalization.get("lane") != lane.value:
        raise QWakeLC4RuntimeBackendError(
            "runtime matrix normalization lane differs"
        )
    if normalization.get("candidate_index") != candidate_index:
        raise QWakeLC4RuntimeBackendError(
            "runtime matrix normalization candidate differs"
        )
    normalization_payload = dict(normalization)
    normalization_digest = normalization_payload.pop(
        "normalization_sha256", None
    )
    if not isinstance(normalization_digest, str):
        raise QWakeLC4RuntimeBackendError(
            "runtime matrix normalization digest is absent"
        )
    _require_sha256(normalization_digest, "normalization_sha256")
    if normalization_digest != sha256_object(normalization_payload):
        raise QWakeLC4RuntimeBackendError(
            "runtime matrix normalization digest differs"
        )
    aggregate_payload = dict(aggregate)
    aggregate_digest = aggregate_payload.pop("aggregate_sha256", None)
    if not isinstance(aggregate_digest, str):
        raise QWakeLC4RuntimeBackendError(
            "runtime matrix aggregate digest is absent"
        )
    _require_sha256(aggregate_digest, "aggregate_sha256")
    if aggregate_digest != sha256_object(aggregate_payload):
        raise QWakeLC4RuntimeBackendError(
            "runtime matrix aggregate digest differs"
        )

def _lane_device_dtype(lane: RuntimeLane) -> tuple[torch.device, torch.dtype]:
    if lane is RuntimeLane.CPU_FLOAT64_ENGINEERING:
        return torch.device("cpu"), torch.float64
    if not torch.cuda.is_available() or not str(torch.version.hip or ""):
        raise QWakeLC4RuntimeBackendError("ROCm canonical lane is unavailable")
    return torch.device("cuda:0"), torch.float32


def _synthetic_batch(seed: int) -> tuple[Tensor, Tensor]:
    generator = torch.Generator(device="cpu")
    generator.manual_seed(seed + 17_042)
    inputs = torch.randn(
        (_SYNTHETIC_BATCH_SIZE, *_SYNTHETIC_IMAGE_SHAPE),
        generator=generator,
        dtype=torch.float64,
    )
    targets = torch.randint(
        0,
        10,
        (_SYNTHETIC_BATCH_SIZE,),
        generator=generator,
    )
    return inputs, targets


def _primary_start(
    lane: RuntimeLane,
) -> tuple[int, tuple[torch.cuda.Event, torch.cuda.Event] | None]:
    if lane is RuntimeLane.CPU_FLOAT64_ENGINEERING:
        return time.process_time_ns(), None
    torch.cuda.reset_peak_memory_stats()
    start = torch.cuda.Event(enable_timing=True)
    end = torch.cuda.Event(enable_timing=True)
    start.record()
    return 0, (start, end)


def _primary_end(
    lane: RuntimeLane,
    start: int,
    events: tuple[torch.cuda.Event, torch.cuda.Event] | None,
) -> int:
    if lane is RuntimeLane.CPU_FLOAT64_ENGINEERING:
        return max(time.process_time_ns() - start, 1)
    if events is None:
        raise QWakeLC4RuntimeBackendError("ROCm timing events are absent")
    first, second = events
    second.record()
    torch.cuda.synchronize()
    return max(int(first.elapsed_time(second) * 1_000_000), 1)


def _memory_snapshot(lane: RuntimeLane) -> tuple[int, int]:
    if lane is RuntimeLane.CPU_FLOAT64_ENGINEERING:
        info = _PSUTIL.Process().memory_full_info()
        allocated = int(getattr(info, "uss", info.rss))
        reserved = int(info.rss)
        return allocated, max(allocated, reserved)
    return (
        int(torch.cuda.max_memory_allocated()),
        int(torch.cuda.max_memory_reserved()),
    )


def _jsonl_bytes(values: Iterable[Mapping[str, object]]) -> bytes:
    return b"".join(
        canonical_json(value).encode("utf-8")
        for value in values
    )


def _write_exclusive_regular(path: Path, content: bytes) -> None:
    if path.exists() or path.is_symlink():
        raise QWakeLC4RuntimeBackendError(
            f"runtime backend output already exists: {path.name}"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL,
        0o600,
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def _read_json_object(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise QWakeLC4RuntimeBackendError(f"JSON file is absent: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise QWakeLC4RuntimeBackendError(f"invalid JSON file: {path}") from exc
    if not isinstance(value, dict):
        raise QWakeLC4RuntimeBackendError(f"JSON root is not an object: {path}")
    return cast(dict[str, Any], value)


def _read_registry(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        digest, separator, relative = line.partition("  ")
        if not separator or not relative or relative in result:
            raise QWakeLC4RuntimeBackendError(
                "materialized execution-freeze registry is invalid"
            )
        _require_sha256(f"sha256:{digest}", "registry_digest")
        result[relative] = f"sha256:{digest}"
    if not result:
        raise QWakeLC4RuntimeBackendError(
            "materialized execution-freeze registry is empty"
        )
    return result


def _sha256_file(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise QWakeLC4RuntimeBackendError(f"regular file is absent: {path}")
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _require_git_commit(root: Path, expected: str) -> None:
    if not root.is_dir() or root.is_symlink():
        raise QWakeLC4RuntimeBackendError("Torch2PC checkout is absent")
    completed = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0 or completed.stdout.strip() != expected:
        raise QWakeLC4RuntimeBackendError("Torch2PC checkout identity differs")
    status = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain"],
        check=False,
        capture_output=True,
        text=True,
    )
    if status.returncode != 0 or status.stdout.strip():
        raise QWakeLC4RuntimeBackendError("Torch2PC checkout is not clean")


def _verify_payload_digest(value: object, digest_field: str) -> None:
    payload = (
        asdict(cast(Any, value))
        if hasattr(value, "__dataclass_fields__")
        else value
    )
    if not isinstance(payload, dict):
        raise QWakeLC4RuntimeBackendError("digest payload is not a mapping")
    observed = dict(payload)
    expected = observed.pop(digest_field)
    if expected != sha256_object(observed):
        raise QWakeLC4RuntimeBackendError(f"{digest_field} differs")


def _require_commit(value: str, field_name: str) -> None:
    if len(value) != _COMMIT_LENGTH or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise QWakeLC4RuntimeBackendError(f"{field_name} is not a commit")


def _require_sha256(value: str, field_name: str) -> None:
    if len(value) != _SHA256_PREFIX_LENGTH or not value.startswith("sha256:"):
        raise QWakeLC4RuntimeBackendError(f"{field_name} is not SHA-256")
    if any(character not in "0123456789abcdef" for character in value[7:]):
        raise QWakeLC4RuntimeBackendError(f"{field_name} is not SHA-256")


def _string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise QWakeLC4RuntimeBackendError(f"{field_name} must be a string")
    return value


def _integer(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise QWakeLC4RuntimeBackendError(f"{field_name} must be an integer")
    return value


def _boolean(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise QWakeLC4RuntimeBackendError(f"{field_name} must be boolean")
    return value
