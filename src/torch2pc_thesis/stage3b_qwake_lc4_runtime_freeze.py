"""Fail-closed QW-LC4-F runtime-freeze authoring contracts.

The module binds the bounded QW-LC4-I implementation to a concrete runtime
adapter, immutable source/image identities, deny-all preflight state, and a
single-attempt engineering authorization schema.  It deliberately provides no
runtime executor, no dataset loader, no output writer, and no scientific
adjudicator.  QW-LC4-E must add and separately authorize every effectful path.
"""

from __future__ import annotations

import hashlib
import importlib
import importlib.metadata
import json
import platform
import re
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Final, cast

import torch
from torch import Tensor, nn

from torch2pc_thesis.stage3b_qwake_lc4_bounded import (
    ANALYTIC_ACTION_ID,
    EXACT_REFERENCE_ACTION_ID,
    LC4_IMPLEMENTATION_ID,
    PAIR_COUNT,
    FixedPredFrontier,
    OpaqueStateSnapshot,
    RegisteredDomain,
    capture_opaque_state,
    pair_schedule,
)

RUNTIME_FREEZE_REQUEST_ID: Final = (
    "stage3b-qwake-lc4-f-runtime-freeze-request-v1"
)
RUNTIME_PREFLIGHT_ID: Final = "stage3b-qwake-lc4-runtime-preflight-v1"
RUNTIME_AUTHORIZATION_ID: Final = (
    "stage3b-qwake-lc4-runtime-authorization-v1"
)
RUNTIME_FREEZE_ID: Final = "stage3b-qwake-lc4-f-runtime-freeze-v1"
RUNTIME_OPERATOR_ACKNOWLEDGEMENT: Final = (
    "AUTHORIZE_QWAKE_LC4_SINGLE_ENGINEERING_MATCHED_SHADOW_RUN"
)
RUNTIME_ENGINEERING_BATCH_ID: Final = "synthetic-engineering-batch-v1"
RUNTIME_MODEL_SEED: Final = 0
RUNTIME_CANDIDATE_INDICES: Final = tuple(range(7))
RUNTIME_OUTPUT_ROOT: Final = Path(
    "results/stage-3/qwake-lc4-runtime-validation-v1-attempt-001"
)
REQUEST_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-f-runtime-freeze-request-v1/request.json"
)
REQUEST_SUMS_RELATIVE: Final = REQUEST_RELATIVE.parent / "SHA256SUMS"
IMPLEMENTATION_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-i-bounded-implementation-v1/implementation.json"
)
IMPLEMENTATION_SUMS_RELATIVE: Final = IMPLEMENTATION_RELATIVE.parent / "SHA256SUMS"
LC3_CONTRACT_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc3-matched-shadow-validation-contract-v1/contract.json"
)
LC3_CONTRACT_SUMS_RELATIVE: Final = LC3_CONTRACT_RELATIVE.parent / "SHA256SUMS"
_COMMIT_PATTERN: Final = re.compile(r"^[0-9a-f]{40}$")
_SHA256_PATTERN: Final = re.compile(r"^sha256:[0-9a-f]{64}$")

__all__ = [
    "RUNTIME_AUTHORIZATION_ID",
    "RUNTIME_CANDIDATE_INDICES",
    "RUNTIME_ENGINEERING_BATCH_ID",
    "RUNTIME_FREEZE_ID",
    "RUNTIME_FREEZE_REQUEST_ID",
    "RUNTIME_MODEL_SEED",
    "RUNTIME_OPERATOR_ACKNOWLEDGEMENT",
    "RUNTIME_OUTPUT_ROOT",
    "RUNTIME_PREFLIGHT_ID",
    "QWakeLC4RuntimeFreezeError",
    "RuntimeAdapterId",
    "RuntimeArmOrder",
    "RuntimeAuthorizationCell",
    "RuntimeFreezePermissionSet",
    "RuntimeLane",
    "RuntimeProbe",
    "RuntimeSourceIdentity",
    "QWakeLC4RuntimeAuthorization",
    "QWakeLC4RuntimePreflight",
    "RuntimeFrontierAdapter",
    "adapter_registry_sha256",
    "build_runtime_authorization",
    "build_runtime_preflight",
    "canonical_json",
    "load_runtime_authorization",
    "load_runtime_preflight",
    "probe_runtime",
    "runtime_authorization_cells",
    "sha256_object",
    "validate_runtime_authorization",
    "validate_runtime_preflight",
    "verify_frozen_request",
]


class QWakeLC4RuntimeFreezeError(RuntimeError):
    """Raised when a QW-LC4-F freeze invariant fails closed."""


class RuntimeLane(StrEnum):
    """Registered engineering lanes; cross-lane comparison is forbidden."""

    CPU_FLOAT64_ENGINEERING = "cpu_float64_engineering"
    ROCM_FLOAT32_CANONICAL = "rocm_float32_canonical"


class RuntimeArmOrder(StrEnum):
    """Balanced arm order encoded in each frozen repeat cell."""

    EXACT_THEN_ANALYTIC = "exact_reference_then_analytic_candidate"
    ANALYTIC_THEN_EXACT = "analytic_candidate_then_exact_reference"


class RuntimeAdapterId(StrEnum):
    """Complete adapter registry required by the QW-LC3 contract."""

    CAPTURE_FIXEDPRED_FRONTIER = "capture_fixedpred_frontier"
    CAPTURE_OPAQUE_STATE = "capture_opaque_state"
    RESTORE_REGISTERED_RNG = "restore_registered_rng"
    RUN_EXACT_REFERENCE = "run_complete_exact_suffix"
    RUN_ANALYTIC_CANDIDATE = "run_analytic_wavefront_completion"
    MATERIALIZE_REQUIRED_RESPONSE = "materialize_required_response"
    COMPARE_REQUIRED_RESPONSE = "compare_required_responses"
    MAP_RESOURCE_TRAJECTORY = "map_resource_trajectory"
    RUN_RESERVE_PROBE = "run_complete_exact_reserve_probe"
    AGGREGATE_PAIRED_COSTS = "aggregate_paired_costs"


_ALLOWED_RUNTIME_CAPABILITIES: Final[frozenset[str]] = frozenset(
    {
        "CAPTURE_FIXEDPRED_FRONTIER",
        "CAPTURE_OPAQUE_STATE",
        "RESTORE_REGISTERED_RNG",
        "RUN_EXACT_REFERENCE",
        "RUN_ANALYTIC_CANDIDATE",
        "MATERIALIZE_REQUIRED_RESPONSE",
        "COMPARE_REQUIRED_RESPONSE",
        "MAP_RESOURCE_TRAJECTORY",
        "RUN_RESERVE_PROBE",
        "AGGREGATE_PAIRED_COSTS",
        "WRITE_ENGINEERING_EVIDENCE",
    }
)


@dataclass(frozen=True)
class RuntimeFreezePermissionSet:
    """Engineering-only capability set with deny-all defaults."""

    capabilities: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        forbidden = self.capabilities - _ALLOWED_RUNTIME_CAPABILITIES
        if forbidden:
            names = ", ".join(sorted(forbidden))
            raise QWakeLC4RuntimeFreezeError(
                f"runtime-freeze authorization contains forbidden capabilities: {names}"
            )

    @classmethod
    def deny_all(cls) -> RuntimeFreezePermissionSet:
        return cls()

    @classmethod
    def complete_engineering(cls) -> RuntimeFreezePermissionSet:
        return cls(capabilities=_ALLOWED_RUNTIME_CAPABILITIES)

    def require(self, *capabilities: str) -> None:
        missing = tuple(item for item in capabilities if item not in self.capabilities)
        if missing:
            names = ", ".join(missing)
            raise QWakeLC4RuntimeFreezeError(
                f"runtime capability is not authorized: {names}"
            )


@dataclass(frozen=True)
class RuntimeProbe:
    """Non-model runtime identity captured by QW-LC4-F."""

    lane: RuntimeLane
    python_version: str
    python_implementation: str
    python_executable: str
    platform: str
    machine: str
    torch_version: str
    hip_version: str
    accelerator_available: bool
    accelerator_count: int
    accelerator_name: str
    dtype: str
    memory_source: str
    clock_source: str

    def __post_init__(self) -> None:
        for field_name in (
            "python_version",
            "python_implementation",
            "python_executable",
            "platform",
            "machine",
            "torch_version",
            "dtype",
            "memory_source",
            "clock_source",
        ):
            if not str(getattr(self, field_name)).strip():
                raise QWakeLC4RuntimeFreezeError(
                    f"runtime probe field is empty: {field_name}"
                )
        if self.accelerator_count < 0:
            raise QWakeLC4RuntimeFreezeError(
                "accelerator_count must be non-negative"
            )
        if (
            self.lane is RuntimeLane.CPU_FLOAT64_ENGINEERING
            and self.dtype != "float64"
        ):
            raise QWakeLC4RuntimeFreezeError(
                "CPU engineering lane must use float64"
            )
        if (
            self.lane is RuntimeLane.ROCM_FLOAT32_CANONICAL
            and self.dtype != "float32"
        ):
            raise QWakeLC4RuntimeFreezeError(
                "ROCm canonical lane must use float32"
            )
        if (
            self.lane is RuntimeLane.ROCM_FLOAT32_CANONICAL
            and (not self.accelerator_available or self.accelerator_count < 1)
        ):
            raise QWakeLC4RuntimeFreezeError(
                "ROCm canonical lane requires an available accelerator"
            )
        if (
            self.lane is RuntimeLane.ROCM_FLOAT32_CANONICAL
            and (not self.hip_version.strip() or not self.accelerator_name.strip())
        ):
            raise QWakeLC4RuntimeFreezeError(
                "ROCm canonical lane requires HIP and accelerator identities"
            )


@dataclass(frozen=True)
class RuntimeSourceIdentity:
    """Immutable source, image, implementation, and contract identity."""

    source_commit: str
    source_index_sha256: str
    torch2pc_commit: str
    image_digest: str
    image_repo_digest: str
    request_sha256: str
    implementation_source_sha256: str
    implementation_manifest_sha256: str
    implementation_registry_sha256: str
    lc3_contract_sha256: str
    lc3_contract_registry_sha256: str
    adapter_registry_sha256: str

    def __post_init__(self) -> None:
        _require_commit(self.source_commit, field_name="source_commit")
        _require_commit(self.torch2pc_commit, field_name="torch2pc_commit")
        for field_name in (
            "source_index_sha256",
            "image_digest",
            "request_sha256",
            "implementation_source_sha256",
            "implementation_manifest_sha256",
            "implementation_registry_sha256",
            "lc3_contract_sha256",
            "lc3_contract_registry_sha256",
            "adapter_registry_sha256",
        ):
            _require_sha256(str(getattr(self, field_name)), field_name=field_name)
        expected_repo_suffix = self.image_digest.removeprefix("sha256:")
        if not self.image_repo_digest.endswith(f"@sha256:{expected_repo_suffix}"):
            raise QWakeLC4RuntimeFreezeError(
                "image_repo_digest is not bound to image_digest"
            )


@dataclass(frozen=True)
class QWakeLC4RuntimePreflight:
    """Deny-all, non-computational runtime preflight."""

    schema_version: int
    preflight_id: str
    status: str
    captured_at_utc: str
    source_identity: RuntimeSourceIdentity
    runtime_probes: tuple[RuntimeProbe, ...]
    bound_adapter_ids: tuple[RuntimeAdapterId, ...]
    permissions: RuntimeFreezePermissionSet
    execution_authorization_present: bool
    runtime_execution_permitted: bool
    runtime_execution_performed: bool
    engineering_evidence_present: bool
    scientific_execution_open: bool
    test_dataset_access: bool
    publication_permitted: bool
    image_freeze_permitted: bool
    output_root: str
    output_root_absent: bool
    preflight_sha256: str

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise QWakeLC4RuntimeFreezeError(
                "runtime preflight schema_version must be 1"
            )
        if self.preflight_id != RUNTIME_PREFLIGHT_ID:
            raise QWakeLC4RuntimeFreezeError("unexpected runtime preflight id")
        if self.status != "runtime_preflight_passed_authorization_not_issued":
            raise QWakeLC4RuntimeFreezeError("runtime preflight is not closed")
        _require_utc(self.captured_at_utc, field_name="captured_at_utc")
        if tuple(probe.lane for probe in self.runtime_probes) != tuple(RuntimeLane):
            raise QWakeLC4RuntimeFreezeError(
                "runtime preflight must bind CPU then ROCm"
            )
        if self.bound_adapter_ids != tuple(RuntimeAdapterId):
            raise QWakeLC4RuntimeFreezeError(
                "runtime adapter registry is incomplete"
            )
        if self.permissions.capabilities:
            raise QWakeLC4RuntimeFreezeError(
                "runtime preflight permissions must deny all effects"
            )
        if any(
            (
                self.execution_authorization_present,
                self.runtime_execution_permitted,
                self.runtime_execution_performed,
                self.engineering_evidence_present,
                self.scientific_execution_open,
                self.test_dataset_access,
                self.publication_permitted,
                self.image_freeze_permitted,
            )
        ):
            raise QWakeLC4RuntimeFreezeError(
                "runtime preflight opened a forbidden capability"
            )
        if self.output_root != RUNTIME_OUTPUT_ROOT.as_posix():
            raise QWakeLC4RuntimeFreezeError("unexpected runtime output root")
        if not self.output_root_absent:
            raise QWakeLC4RuntimeFreezeError(
                "runtime output root must be absent at preflight"
            )
        _require_sha256(self.preflight_sha256, field_name="preflight_sha256")
        if self.preflight_sha256 != sha256_object(self._payload_without_digest()):
            raise QWakeLC4RuntimeFreezeError("runtime preflight digest differs")

    def _payload_without_digest(self) -> Mapping[str, object]:
        payload = asdict(self)
        payload.pop("preflight_sha256")
        return cast(Mapping[str, object], payload)

    def canonical_json(self) -> str:
        return canonical_json(self)


@dataclass(frozen=True)
class RuntimeAuthorizationCell:
    """One exact lane/candidate/repeat cell in the future E attempt."""

    lane: RuntimeLane
    model_seed: int
    batch_id: str
    candidate_index: int
    repeat_index: int
    arm_order: RuntimeArmOrder
    reserve_probe_before_repeat_zero: bool
    reserve_probe_after_repeat_eleven: bool

    def __post_init__(self) -> None:
        if self.model_seed != RUNTIME_MODEL_SEED:
            raise QWakeLC4RuntimeFreezeError("unexpected runtime model seed")
        if self.batch_id != RUNTIME_ENGINEERING_BATCH_ID:
            raise QWakeLC4RuntimeFreezeError("unexpected runtime batch id")
        if self.candidate_index not in RUNTIME_CANDIDATE_INDICES:
            raise QWakeLC4RuntimeFreezeError(
                "candidate_index is outside the frozen runtime matrix"
            )
        if not 0 <= self.repeat_index < PAIR_COUNT:
            raise QWakeLC4RuntimeFreezeError(
                "repeat_index is outside the frozen schedule"
            )
        expected_order = (
            RuntimeArmOrder.EXACT_THEN_ANALYTIC
            if self.repeat_index % 2 == 0
            else RuntimeArmOrder.ANALYTIC_THEN_EXACT
        )
        if self.arm_order is not expected_order:
            raise QWakeLC4RuntimeFreezeError(
                "runtime cell arm order differs from the LC3 schedule"
            )
        if self.reserve_probe_before_repeat_zero != (self.repeat_index == 0):
            raise QWakeLC4RuntimeFreezeError(
                "before-repeat reserve probe placement differs"
            )
        if self.reserve_probe_after_repeat_eleven != (
            self.repeat_index == PAIR_COUNT - 1
        ):
            raise QWakeLC4RuntimeFreezeError(
                "after-repeat reserve probe placement differs"
            )


@dataclass(frozen=True)
class QWakeLC4RuntimeAuthorization:
    """Single-attempt engineering authorization; never scientific evidence."""

    schema_version: int
    authorization_id: str
    status: str
    issued_at_utc: str
    operator_acknowledgement: str
    preflight_sha256: str
    source_identity: RuntimeSourceIdentity
    permissions: RuntimeFreezePermissionSet
    cells: tuple[RuntimeAuthorizationCell, ...]
    output_root: str
    output_root_absent_at_issue: bool
    execution_count: int
    runtime_execution_permitted: bool
    runtime_execution_performed: bool
    engineering_evidence_present: bool
    scientific_execution_open: bool
    test_dataset_access: bool
    publication_permitted: bool
    image_freeze_permitted: bool
    authorization_sha256: str

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise QWakeLC4RuntimeFreezeError(
                "runtime authorization schema_version must be 1"
            )
        if self.authorization_id != RUNTIME_AUTHORIZATION_ID:
            raise QWakeLC4RuntimeFreezeError(
                "unexpected runtime authorization id"
            )
        if self.status != "issued_single_engineering_attempt_execution_not_performed":
            raise QWakeLC4RuntimeFreezeError(
                "runtime authorization status differs"
            )
        _require_utc(self.issued_at_utc, field_name="issued_at_utc")
        if self.operator_acknowledgement != RUNTIME_OPERATOR_ACKNOWLEDGEMENT:
            raise QWakeLC4RuntimeFreezeError(
                "runtime operator acknowledgement differs"
            )
        _require_sha256(self.preflight_sha256, field_name="preflight_sha256")
        if self.permissions != RuntimeFreezePermissionSet.complete_engineering():
            raise QWakeLC4RuntimeFreezeError(
                "runtime authorization capability set is incomplete"
            )
        if self.cells != runtime_authorization_cells():
            raise QWakeLC4RuntimeFreezeError(
                "runtime authorization matrix differs from the frozen request"
            )
        if self.output_root != RUNTIME_OUTPUT_ROOT.as_posix():
            raise QWakeLC4RuntimeFreezeError("unexpected authorization output root")
        if not self.output_root_absent_at_issue:
            raise QWakeLC4RuntimeFreezeError(
                "authorization output root must be absent at issue"
            )
        if self.execution_count != 1 or not self.runtime_execution_permitted:
            raise QWakeLC4RuntimeFreezeError(
                "authorization must permit exactly one engineering attempt"
            )
        if any(
            (
                self.runtime_execution_performed,
                self.engineering_evidence_present,
                self.scientific_execution_open,
                self.test_dataset_access,
                self.publication_permitted,
                self.image_freeze_permitted,
            )
        ):
            raise QWakeLC4RuntimeFreezeError(
                "runtime authorization opened a forbidden capability"
            )
        _require_sha256(
            self.authorization_sha256,
            field_name="authorization_sha256",
        )
        if self.authorization_sha256 != sha256_object(
            self._payload_without_digest()
        ):
            raise QWakeLC4RuntimeFreezeError(
                "runtime authorization digest differs"
            )

    def _payload_without_digest(self) -> Mapping[str, object]:
        payload = asdict(self)
        payload.pop("authorization_sha256")
        return cast(Mapping[str, object], payload)

    def canonical_json(self) -> str:
        return canonical_json(self)


class RuntimeFrontierAdapter:
    """Bind a registered lenet-classic FixedPred frontier to QW-LC4-I."""

    def __init__(self, lane: RuntimeLane) -> None:
        self.lane = lane

    def capture(
        self,
        model: nn.Sequential,
        *,
        fixed: Sequence[Tensor],
        beliefs: Sequence[Tensor],
        errors: Sequence[Tensor | None],
        endpoint_loss: Tensor,
        candidate_index: int,
        input_batch: Tensor,
        target_batch: Tensor,
        model_seed: int,
        batch_id: str,
        comparison_profile_id: str,
        cost_profile_id: str,
        deterministic_runtime_controls: Mapping[str, object],
    ) -> OpaqueStateSnapshot:
        """Capture only supplied runtime state; never execute model computation."""

        self._validate_model(model)
        self._validate_lane_tensors(
            tuple(fixed) + tuple(beliefs) + tuple(
                item for item in errors if item is not None
            ) + (endpoint_loss, input_batch)
        )
        if target_batch.device != input_batch.device:
            raise QWakeLC4RuntimeFreezeError(
                "target and input batches must share a device"
            )
        if model_seed != RUNTIME_MODEL_SEED:
            raise QWakeLC4RuntimeFreezeError("unexpected runtime model seed")
        if batch_id != RUNTIME_ENGINEERING_BATCH_ID:
            raise QWakeLC4RuntimeFreezeError("unexpected runtime batch id")
        frontier = FixedPredFrontier(
            fixed=tuple(item.detach().clone() for item in fixed),
            beliefs=tuple(item.detach().clone() for item in beliefs),
            errors=tuple(
                None if item is None else item.detach().clone()
                for item in errors
            ),
            endpoint_loss=endpoint_loss.detach().clone(),
            candidate_index=candidate_index,
        )
        runtime_controls = {
            str(key): _runtime_scalar(value, field_name=str(key))
            for key, value in deterministic_runtime_controls.items()
        }
        runtime_controls.update(
            {
                "model_seed": model_seed,
                "batch_id": batch_id,
            }
        )
        return capture_opaque_state(
            model,
            input_batch,
            target_batch,
            frontier,
            domain=RegisteredDomain(),
            lane_profile_id=self.lane.value,
            comparison_profile_id=comparison_profile_id,
            cost_profile_id=cost_profile_id,
            runtime_controls=runtime_controls,
        )

    def _validate_model(self, model: nn.Sequential) -> None:
        if not isinstance(model, nn.Sequential) or len(model) != 6:
            raise QWakeLC4RuntimeFreezeError(
                "runtime adapter requires six-block lenet_classic"
            )

    def _validate_lane_tensors(self, values: Sequence[Tensor]) -> None:
        expected_dtype = (
            torch.float64
            if self.lane is RuntimeLane.CPU_FLOAT64_ENGINEERING
            else torch.float32
        )
        for value in values:
            if value.dtype != expected_dtype:
                raise QWakeLC4RuntimeFreezeError(
                    "runtime tensor dtype differs from lane profile"
                )
            if (
                self.lane is RuntimeLane.CPU_FLOAT64_ENGINEERING
                and value.device.type != "cpu"
            ):
                raise QWakeLC4RuntimeFreezeError(
                    "CPU engineering tensors must be on CPU"
                )
            if (
                self.lane is RuntimeLane.ROCM_FLOAT32_CANONICAL
                and value.device.type not in {"cuda", "hip"}
            ):
                raise QWakeLC4RuntimeFreezeError(
                    "ROCm canonical tensors must use the accelerator device"
                )


def runtime_authorization_cells() -> tuple[RuntimeAuthorizationCell, ...]:
    """Return the exact 2 x 7 x 12 matched runtime matrix."""

    orders = pair_schedule()
    cells: list[RuntimeAuthorizationCell] = []
    for lane in RuntimeLane:
        for candidate_index in RUNTIME_CANDIDATE_INDICES:
            for repeat_index, order in enumerate(orders):
                arm_order = (
                    RuntimeArmOrder.EXACT_THEN_ANALYTIC
                    if order[0].value == "exact_reference"
                    else RuntimeArmOrder.ANALYTIC_THEN_EXACT
                )
                cells.append(
                    RuntimeAuthorizationCell(
                        lane=lane,
                        model_seed=RUNTIME_MODEL_SEED,
                        batch_id=RUNTIME_ENGINEERING_BATCH_ID,
                        candidate_index=candidate_index,
                        repeat_index=repeat_index,
                        arm_order=arm_order,
                        reserve_probe_before_repeat_zero=(repeat_index == 0),
                        reserve_probe_after_repeat_eleven=(
                            repeat_index == PAIR_COUNT - 1
                        ),
                    )
                )
    return tuple(cells)


def probe_runtime(lane: RuntimeLane) -> RuntimeProbe:
    """Probe identities without executing a model or reading a dataset."""

    imported_torch = importlib.import_module("torch")
    torch_version = importlib.metadata.version("torch")
    torch_runtime_version = getattr(imported_torch, "version", None)
    hip_version = str(getattr(torch_runtime_version, "hip", "") or "")
    accelerator = getattr(imported_torch, "cuda", None)
    if accelerator is None:
        raise QWakeLC4RuntimeFreezeError("PyTorch accelerator API is unavailable")
    available = bool(accelerator.is_available())
    count = int(accelerator.device_count()) if available else 0
    name = str(accelerator.get_device_name(0)) if count else ""
    dtype = (
        "float64"
        if lane is RuntimeLane.CPU_FLOAT64_ENGINEERING
        else "float32"
    )
    memory_source = (
        "psutil_process_rss_and_uss"
        if lane is RuntimeLane.CPU_FLOAT64_ENGINEERING
        else "torch_cuda_max_memory_allocated_and_reserved"
    )
    return RuntimeProbe(
        lane=lane,
        python_version=platform.python_version(),
        python_implementation=platform.python_implementation(),
        python_executable=str(Path(sys.executable).resolve()),
        platform=platform.platform(),
        machine=platform.machine(),
        torch_version=torch_version,
        hip_version=hip_version,
        accelerator_available=available,
        accelerator_count=count,
        accelerator_name=name,
        dtype=dtype,
        memory_source=memory_source,
        clock_source="time_perf_counter_ns_monotonic",
    )


def build_runtime_preflight(
    project_root: Path,
    torch2pc_dir: Path,
    *,
    source_commit: str,
    torch2pc_commit: str,
    image_digest: str,
    image_repo_digest: str,
    captured_at_utc: str,
    runtime_probes: tuple[RuntimeProbe, ...] | None = None,
) -> QWakeLC4RuntimePreflight:
    """Build a deny-all preflight from a clean immutable checkout."""

    root = project_root.expanduser().resolve()
    checkout = torch2pc_dir.expanduser().resolve()
    _require_clean_checkout(root, expected_commit=source_commit, label="project")
    _require_clean_checkout(
        checkout,
        expected_commit=torch2pc_commit,
        label="Torch2PC",
    )
    request_sha256 = verify_frozen_request(root)
    implementation = _verify_implementation_package(root)
    contract = _verify_lc3_contract(root)
    source_identity = RuntimeSourceIdentity(
        source_commit=source_commit,
        source_index_sha256=_source_index_sha256(root),
        torch2pc_commit=torch2pc_commit,
        image_digest=image_digest,
        image_repo_digest=image_repo_digest,
        request_sha256=request_sha256,
        implementation_source_sha256=implementation["source"],
        implementation_manifest_sha256=implementation["manifest"],
        implementation_registry_sha256=implementation["registry"],
        lc3_contract_sha256=contract["contract"],
        lc3_contract_registry_sha256=contract["registry"],
        adapter_registry_sha256=adapter_registry_sha256(),
    )
    probes = (
        tuple(probe_runtime(lane) for lane in RuntimeLane)
        if runtime_probes is None
        else runtime_probes
    )
    output_root = root / RUNTIME_OUTPUT_ROOT
    payload: dict[str, object] = {
        "schema_version": 1,
        "preflight_id": RUNTIME_PREFLIGHT_ID,
        "status": "runtime_preflight_passed_authorization_not_issued",
        "captured_at_utc": captured_at_utc,
        "source_identity": source_identity,
        "runtime_probes": probes,
        "bound_adapter_ids": tuple(RuntimeAdapterId),
        "permissions": RuntimeFreezePermissionSet.deny_all(),
        "execution_authorization_present": False,
        "runtime_execution_permitted": False,
        "runtime_execution_performed": False,
        "engineering_evidence_present": False,
        "scientific_execution_open": False,
        "test_dataset_access": False,
        "publication_permitted": False,
        "image_freeze_permitted": False,
        "output_root": RUNTIME_OUTPUT_ROOT.as_posix(),
        "output_root_absent": not output_root.exists(),
    }
    return QWakeLC4RuntimePreflight(
        schema_version=1,
        preflight_id=RUNTIME_PREFLIGHT_ID,
        status="runtime_preflight_passed_authorization_not_issued",
        captured_at_utc=captured_at_utc,
        source_identity=source_identity,
        runtime_probes=probes,
        bound_adapter_ids=tuple(RuntimeAdapterId),
        permissions=RuntimeFreezePermissionSet.deny_all(),
        execution_authorization_present=False,
        runtime_execution_permitted=False,
        runtime_execution_performed=False,
        engineering_evidence_present=False,
        scientific_execution_open=False,
        test_dataset_access=False,
        publication_permitted=False,
        image_freeze_permitted=False,
        output_root=RUNTIME_OUTPUT_ROOT.as_posix(),
        output_root_absent=not output_root.exists(),
        preflight_sha256=sha256_object(payload),
    )


def validate_runtime_preflight(
    preflight: QWakeLC4RuntimePreflight,
    project_root: Path,
    torch2pc_dir: Path,
    *,
    runtime_probes: tuple[RuntimeProbe, ...] | None = None,
) -> None:
    """Revalidate source and runtime identities without model execution."""

    root = project_root.expanduser().resolve()
    checkout = torch2pc_dir.expanduser().resolve()
    _require_clean_checkout(
        root,
        expected_commit=preflight.source_identity.source_commit,
        label="project",
    )
    _require_clean_checkout(
        checkout,
        expected_commit=preflight.source_identity.torch2pc_commit,
        label="Torch2PC",
    )
    if _source_index_sha256(root) != preflight.source_identity.source_index_sha256:
        raise QWakeLC4RuntimeFreezeError(
            "project source index differs from preflight"
        )
    if verify_frozen_request(root) != preflight.source_identity.request_sha256:
        raise QWakeLC4RuntimeFreezeError("frozen request differs from preflight")
    implementation = _verify_implementation_package(root)
    if implementation["source"] != preflight.source_identity.implementation_source_sha256:
        raise QWakeLC4RuntimeFreezeError(
            "implementation source differs from preflight"
        )
    if implementation["manifest"] != preflight.source_identity.implementation_manifest_sha256:
        raise QWakeLC4RuntimeFreezeError(
            "implementation manifest differs from preflight"
        )
    if implementation["registry"] != preflight.source_identity.implementation_registry_sha256:
        raise QWakeLC4RuntimeFreezeError(
            "implementation registry differs from preflight"
        )
    contract = _verify_lc3_contract(root)
    if contract["contract"] != preflight.source_identity.lc3_contract_sha256:
        raise QWakeLC4RuntimeFreezeError("LC3 contract differs from preflight")
    if contract["registry"] != preflight.source_identity.lc3_contract_registry_sha256:
        raise QWakeLC4RuntimeFreezeError(
            "LC3 contract registry differs from preflight"
        )
    if adapter_registry_sha256() != preflight.source_identity.adapter_registry_sha256:
        raise QWakeLC4RuntimeFreezeError(
            "runtime adapter registry differs from preflight"
        )
    current_probes = (
        tuple(probe_runtime(lane) for lane in RuntimeLane)
        if runtime_probes is None
        else runtime_probes
    )
    if current_probes != preflight.runtime_probes:
        raise QWakeLC4RuntimeFreezeError("runtime probes differ from preflight")
    if (root / RUNTIME_OUTPUT_ROOT).exists():
        raise QWakeLC4RuntimeFreezeError(
            "runtime output root exists during preflight validation"
        )


def build_runtime_authorization(
    preflight: QWakeLC4RuntimePreflight,
    *,
    issued_at_utc: str,
    operator_acknowledgement: str,
    output_root_absent_at_issue: bool,
) -> QWakeLC4RuntimeAuthorization:
    """Issue a single-attempt engineering authorization from exact preflight."""

    if operator_acknowledgement != RUNTIME_OPERATOR_ACKNOWLEDGEMENT:
        raise QWakeLC4RuntimeFreezeError(
            "operator acknowledgement does not authorize QW-LC4"
        )
    payload: dict[str, object] = {
        "schema_version": 1,
        "authorization_id": RUNTIME_AUTHORIZATION_ID,
        "status": "issued_single_engineering_attempt_execution_not_performed",
        "issued_at_utc": issued_at_utc,
        "operator_acknowledgement": operator_acknowledgement,
        "preflight_sha256": preflight.preflight_sha256,
        "source_identity": preflight.source_identity,
        "permissions": RuntimeFreezePermissionSet.complete_engineering(),
        "cells": runtime_authorization_cells(),
        "output_root": RUNTIME_OUTPUT_ROOT.as_posix(),
        "output_root_absent_at_issue": output_root_absent_at_issue,
        "execution_count": 1,
        "runtime_execution_permitted": True,
        "runtime_execution_performed": False,
        "engineering_evidence_present": False,
        "scientific_execution_open": False,
        "test_dataset_access": False,
        "publication_permitted": False,
        "image_freeze_permitted": False,
    }
    return QWakeLC4RuntimeAuthorization(
        schema_version=1,
        authorization_id=RUNTIME_AUTHORIZATION_ID,
        status="issued_single_engineering_attempt_execution_not_performed",
        issued_at_utc=issued_at_utc,
        operator_acknowledgement=operator_acknowledgement,
        preflight_sha256=preflight.preflight_sha256,
        source_identity=preflight.source_identity,
        permissions=RuntimeFreezePermissionSet.complete_engineering(),
        cells=runtime_authorization_cells(),
        output_root=RUNTIME_OUTPUT_ROOT.as_posix(),
        output_root_absent_at_issue=output_root_absent_at_issue,
        execution_count=1,
        runtime_execution_permitted=True,
        runtime_execution_performed=False,
        engineering_evidence_present=False,
        scientific_execution_open=False,
        test_dataset_access=False,
        publication_permitted=False,
        image_freeze_permitted=False,
        authorization_sha256=sha256_object(payload),
    )


def validate_runtime_authorization(
    authorization: QWakeLC4RuntimeAuthorization,
    preflight: QWakeLC4RuntimePreflight,
    project_root: Path,
    torch2pc_dir: Path,
    *,
    runtime_probes: tuple[RuntimeProbe, ...] | None = None,
) -> None:
    """Verify authorization identity while keeping execution unperformed."""

    validate_runtime_preflight(
        preflight,
        project_root,
        torch2pc_dir,
        runtime_probes=runtime_probes,
    )
    if authorization.preflight_sha256 != preflight.preflight_sha256:
        raise QWakeLC4RuntimeFreezeError(
            "authorization is not bound to preflight"
        )
    if authorization.source_identity != preflight.source_identity:
        raise QWakeLC4RuntimeFreezeError(
            "authorization source identity differs from preflight"
        )
    if not authorization.output_root_absent_at_issue:
        raise QWakeLC4RuntimeFreezeError(
            "authorization output root existed at issue"
        )


def load_runtime_preflight(path: Path) -> QWakeLC4RuntimePreflight:
    """Load and strictly validate a canonical preflight JSON file."""

    payload = _read_json_object(path)
    return QWakeLC4RuntimePreflight(
        schema_version=int(payload["schema_version"]),
        preflight_id=str(payload["preflight_id"]),
        status=str(payload["status"]),
        captured_at_utc=str(payload["captured_at_utc"]),
        source_identity=_source_identity_from_dict(
            _as_mapping(payload["source_identity"], "source_identity")
        ),
        runtime_probes=tuple(
            _probe_from_dict(_as_mapping(item, "runtime_probe"))
            for item in _as_sequence(payload["runtime_probes"], "runtime_probes")
        ),
        bound_adapter_ids=tuple(
            RuntimeAdapterId(str(item))
            for item in _as_sequence(
                payload["bound_adapter_ids"],
                "bound_adapter_ids",
            )
        ),
        permissions=_permissions_from_dict(
            _as_mapping(payload["permissions"], "permissions")
        ),
        execution_authorization_present=bool(
            payload["execution_authorization_present"]
        ),
        runtime_execution_permitted=bool(payload["runtime_execution_permitted"]),
        runtime_execution_performed=bool(payload["runtime_execution_performed"]),
        engineering_evidence_present=bool(payload["engineering_evidence_present"]),
        scientific_execution_open=bool(payload["scientific_execution_open"]),
        test_dataset_access=bool(payload["test_dataset_access"]),
        publication_permitted=bool(payload["publication_permitted"]),
        image_freeze_permitted=bool(payload["image_freeze_permitted"]),
        output_root=str(payload["output_root"]),
        output_root_absent=bool(payload["output_root_absent"]),
        preflight_sha256=str(payload["preflight_sha256"]),
    )


def load_runtime_authorization(path: Path) -> QWakeLC4RuntimeAuthorization:
    """Load and strictly validate a canonical authorization JSON file."""

    payload = _read_json_object(path)
    return QWakeLC4RuntimeAuthorization(
        schema_version=int(payload["schema_version"]),
        authorization_id=str(payload["authorization_id"]),
        status=str(payload["status"]),
        issued_at_utc=str(payload["issued_at_utc"]),
        operator_acknowledgement=str(payload["operator_acknowledgement"]),
        preflight_sha256=str(payload["preflight_sha256"]),
        source_identity=_source_identity_from_dict(
            _as_mapping(payload["source_identity"], "source_identity")
        ),
        permissions=_permissions_from_dict(
            _as_mapping(payload["permissions"], "permissions")
        ),
        cells=tuple(
            _cell_from_dict(_as_mapping(item, "authorization_cell"))
            for item in _as_sequence(payload["cells"], "cells")
        ),
        output_root=str(payload["output_root"]),
        output_root_absent_at_issue=bool(payload["output_root_absent_at_issue"]),
        execution_count=int(payload["execution_count"]),
        runtime_execution_permitted=bool(payload["runtime_execution_permitted"]),
        runtime_execution_performed=bool(payload["runtime_execution_performed"]),
        engineering_evidence_present=bool(payload["engineering_evidence_present"]),
        scientific_execution_open=bool(payload["scientific_execution_open"]),
        test_dataset_access=bool(payload["test_dataset_access"]),
        publication_permitted=bool(payload["publication_permitted"]),
        image_freeze_permitted=bool(payload["image_freeze_permitted"]),
        authorization_sha256=str(payload["authorization_sha256"]),
    )


def verify_frozen_request(project_root: Path) -> str:
    """Verify the exact static QW-LC4-F request and return its digest."""

    root = project_root.expanduser().resolve()
    request_path = root / REQUEST_RELATIVE
    sums_path = root / REQUEST_SUMS_RELATIVE
    _require_regular_file(request_path, label="runtime-freeze request")
    _require_regular_file(sums_path, label="runtime-freeze request registry")
    registry = _read_registry(sums_path)
    if registry != {"request.json": _sha256_file(request_path).removeprefix("sha256:")}:
        raise QWakeLC4RuntimeFreezeError(
            "runtime-freeze request registry differs"
        )
    payload = _read_json_object(request_path)
    if payload.get("request_id") != RUNTIME_FREEZE_REQUEST_ID:
        raise QWakeLC4RuntimeFreezeError("unexpected runtime-freeze request id")
    matrix = _as_mapping(payload.get("runtime_matrix"), "runtime_matrix")
    if matrix.get("lanes") != [item.value for item in RuntimeLane]:
        raise QWakeLC4RuntimeFreezeError("runtime request lanes differ")
    if matrix.get("candidate_indices") != list(RUNTIME_CANDIDATE_INDICES):
        raise QWakeLC4RuntimeFreezeError(
            "runtime request candidate indices differ"
        )
    if matrix.get("pair_count_per_cell") != PAIR_COUNT:
        raise QWakeLC4RuntimeFreezeError("runtime request pair count differs")
    if matrix.get("authorization_cell_count") != len(
        runtime_authorization_cells()
    ):
        raise QWakeLC4RuntimeFreezeError(
            "runtime request authorization cell count differs"
        )
    return _sha256_file(request_path)


def adapter_registry_sha256() -> str:
    """Digest the ordered runtime adapter registry and action identities."""

    payload = {
        "adapter_ids": [item.value for item in RuntimeAdapterId],
        "analytic_action_id": ANALYTIC_ACTION_ID,
        "exact_reference_action_id": EXACT_REFERENCE_ACTION_ID,
        "implementation_id": LC4_IMPLEMENTATION_ID,
        "frontier_adapter": (
            "six_block_lenet_classic_supplied_state_no_execution_v1"
        ),
    }
    return sha256_object(payload)


def canonical_json(value: object) -> str:
    """Return deterministic UTF-8 JSON text with a trailing newline."""

    return json.dumps(
        _canonicalize(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ) + "\n"


def sha256_object(value: object) -> str:
    """Return a prefixed SHA-256 over canonical JSON bytes."""

    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _verify_implementation_package(root: Path) -> dict[str, str]:
    manifest_path = root / IMPLEMENTATION_RELATIVE
    registry_path = root / IMPLEMENTATION_SUMS_RELATIVE
    source_path = root / "src/torch2pc_thesis/stage3b_qwake_lc4_bounded.py"
    for path, label in (
        (manifest_path, "QW-LC4-I implementation manifest"),
        (registry_path, "QW-LC4-I implementation registry"),
        (source_path, "QW-LC4-I implementation source"),
    ):
        _require_regular_file(path, label=label)
    registry = _read_registry(registry_path)
    if registry != {"implementation.json": _sha256_file(manifest_path).removeprefix("sha256:")}:
        raise QWakeLC4RuntimeFreezeError(
            "QW-LC4-I implementation registry differs"
        )
    manifest = _read_json_object(manifest_path)
    module = _as_mapping(manifest.get("module"), "module")
    source_sha = _sha256_file(source_path)
    if module.get("sha256") != source_sha:
        raise QWakeLC4RuntimeFreezeError(
            "QW-LC4-I source digest differs from manifest"
        )
    return {
        "source": source_sha,
        "manifest": _sha256_file(manifest_path),
        "registry": _sha256_file(registry_path),
    }


def _verify_lc3_contract(root: Path) -> dict[str, str]:
    contract_path = root / LC3_CONTRACT_RELATIVE
    registry_path = root / LC3_CONTRACT_SUMS_RELATIVE
    _require_regular_file(contract_path, label="QW-LC3 contract")
    _require_regular_file(registry_path, label="QW-LC3 contract registry")
    registry = _read_registry(registry_path)
    if registry != {"contract.json": _sha256_file(contract_path).removeprefix("sha256:")}:
        raise QWakeLC4RuntimeFreezeError("QW-LC3 contract registry differs")
    contract = _read_json_object(contract_path)
    if contract.get("contract_id") != (
        "stage3b-qwake-lc3-matched-shadow-validation-contract-v1"
    ):
        raise QWakeLC4RuntimeFreezeError("unexpected QW-LC3 contract id")
    return {
        "contract": _sha256_file(contract_path),
        "registry": _sha256_file(registry_path),
    }


def _source_index_sha256(root: Path) -> str:
    result = _run_git(root, "ls-files", "-s")
    return "sha256:" + hashlib.sha256(result.encode("utf-8")).hexdigest()


def _require_clean_checkout(root: Path, *, expected_commit: str, label: str) -> None:
    _require_commit(expected_commit, field_name=f"{label}_commit")
    observed_commit = _run_git(root, "rev-parse", "HEAD").strip()
    if observed_commit != expected_commit:
        raise QWakeLC4RuntimeFreezeError(
            f"{label} checkout commit differs: {observed_commit}"
        )
    status = _run_git(root, "status", "--porcelain")
    if status:
        raise QWakeLC4RuntimeFreezeError(f"{label} checkout is not clean")


def _run_git(root: Path, *arguments: str) -> str:
    try:
        completed = subprocess.run(
            ("git", "-C", str(root), *arguments),
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise QWakeLC4RuntimeFreezeError(
            f"git command failed for {root}: {' '.join(arguments)}"
        ) from exc
    return completed.stdout.rstrip("\n")


def _read_registry(path: Path) -> dict[str, str]:
    registry: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip():
            continue
        try:
            digest, name = raw_line.split("  ", 1)
        except ValueError as exc:
            raise QWakeLC4RuntimeFreezeError(
                f"invalid SHA256SUMS line in {path}"
            ) from exc
        if not re.fullmatch(r"[0-9a-f]{64}", digest) or not name:
            raise QWakeLC4RuntimeFreezeError(
                f"invalid SHA256SUMS entry in {path}"
            )
        if name in registry:
            raise QWakeLC4RuntimeFreezeError(
                f"duplicate SHA256SUMS entry in {path}: {name}"
            )
        registry[name] = digest
    return registry


def _read_json_object(path: Path) -> dict[str, Any]:
    _require_regular_file(path, label="JSON input")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise QWakeLC4RuntimeFreezeError(f"invalid JSON file: {path}") from exc
    if not isinstance(payload, dict):
        raise QWakeLC4RuntimeFreezeError(f"JSON root must be an object: {path}")
    return cast(dict[str, Any], payload)


def _require_regular_file(path: Path, *, label: str) -> None:
    if path.is_symlink() or not path.is_file():
        raise QWakeLC4RuntimeFreezeError(
            f"{label} must be a regular non-symlink file: {path}"
        )


def _sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _require_commit(value: str, *, field_name: str) -> None:
    if _COMMIT_PATTERN.fullmatch(value) is None:
        raise QWakeLC4RuntimeFreezeError(
            f"{field_name} must be a lowercase 40-hex commit"
        )


def _require_sha256(value: str, *, field_name: str) -> None:
    if _SHA256_PATTERN.fullmatch(value) is None:
        raise QWakeLC4RuntimeFreezeError(
            f"{field_name} must be a prefixed SHA-256"
        )


def _require_utc(value: str, *, field_name: str) -> None:
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise QWakeLC4RuntimeFreezeError(
            f"{field_name} must use YYYY-MM-DDTHH:MM:SSZ"
        ) from exc
    if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != value:
        raise QWakeLC4RuntimeFreezeError(f"{field_name} is not canonical UTC")


def _runtime_scalar(value: object, *, field_name: str) -> str | int | float | bool | None:
    if value is None or isinstance(value, str | int | float | bool):
        return value
    raise QWakeLC4RuntimeFreezeError(
        f"runtime control must be scalar: {field_name}"
    )


def _runtime_int(value: object, *, field_name: str) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    raise QWakeLC4RuntimeFreezeError(f"{field_name} must be an integer")


def _source_identity_from_dict(payload: Mapping[str, object]) -> RuntimeSourceIdentity:
    return RuntimeSourceIdentity(
        source_commit=str(payload["source_commit"]),
        source_index_sha256=str(payload["source_index_sha256"]),
        torch2pc_commit=str(payload["torch2pc_commit"]),
        image_digest=str(payload["image_digest"]),
        image_repo_digest=str(payload["image_repo_digest"]),
        request_sha256=str(payload["request_sha256"]),
        implementation_source_sha256=str(
            payload["implementation_source_sha256"]
        ),
        implementation_manifest_sha256=str(
            payload["implementation_manifest_sha256"]
        ),
        implementation_registry_sha256=str(
            payload["implementation_registry_sha256"]
        ),
        lc3_contract_sha256=str(payload["lc3_contract_sha256"]),
        lc3_contract_registry_sha256=str(
            payload["lc3_contract_registry_sha256"]
        ),
        adapter_registry_sha256=str(payload["adapter_registry_sha256"]),
    )


def _probe_from_dict(payload: Mapping[str, object]) -> RuntimeProbe:
    return RuntimeProbe(
        lane=RuntimeLane(str(payload["lane"])),
        python_version=str(payload["python_version"]),
        python_implementation=str(payload["python_implementation"]),
        python_executable=str(payload["python_executable"]),
        platform=str(payload["platform"]),
        machine=str(payload["machine"]),
        torch_version=str(payload["torch_version"]),
        hip_version=str(payload["hip_version"]),
        accelerator_available=bool(payload["accelerator_available"]),
        accelerator_count=_runtime_int(
            payload["accelerator_count"], field_name="accelerator_count"
        ),
        accelerator_name=str(payload["accelerator_name"]),
        dtype=str(payload["dtype"]),
        memory_source=str(payload["memory_source"]),
        clock_source=str(payload["clock_source"]),
    )


def _permissions_from_dict(payload: Mapping[str, object]) -> RuntimeFreezePermissionSet:
    capabilities = _as_sequence(payload.get("capabilities"), "capabilities")
    return RuntimeFreezePermissionSet(
        capabilities=frozenset(str(item) for item in capabilities)
    )


def _cell_from_dict(payload: Mapping[str, object]) -> RuntimeAuthorizationCell:
    return RuntimeAuthorizationCell(
        lane=RuntimeLane(str(payload["lane"])),
        model_seed=_runtime_int(
            payload["model_seed"], field_name="model_seed"
        ),
        batch_id=str(payload["batch_id"]),
        candidate_index=_runtime_int(
            payload["candidate_index"], field_name="candidate_index"
        ),
        repeat_index=_runtime_int(
            payload["repeat_index"], field_name="repeat_index"
        ),
        arm_order=RuntimeArmOrder(str(payload["arm_order"])),
        reserve_probe_before_repeat_zero=bool(
            payload["reserve_probe_before_repeat_zero"]
        ),
        reserve_probe_after_repeat_eleven=bool(
            payload["reserve_probe_after_repeat_eleven"]
        ),
    )


def _as_mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise QWakeLC4RuntimeFreezeError(f"{field_name} must be an object")
    return cast(Mapping[str, object], value)


def _as_sequence(value: object, field_name: str) -> Sequence[object]:
    if not isinstance(value, list):
        raise QWakeLC4RuntimeFreezeError(f"{field_name} must be an array")
    return cast(Sequence[object], value)


def _canonicalize(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _canonicalize(asdict(value))
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, Mapping):
        return {
            str(key): _canonicalize(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, tuple | list):
        return [_canonicalize(item) for item in value]
    if isinstance(value, set | frozenset):
        return [
            _canonicalize(item)
            for item in sorted(value, key=lambda item: str(item))
        ]
    if value is None or isinstance(value, str | int | float | bool):
        return value
    raise QWakeLC4RuntimeFreezeError(
        f"value is not canonically serializable: {type(value).__name__}"
    )
