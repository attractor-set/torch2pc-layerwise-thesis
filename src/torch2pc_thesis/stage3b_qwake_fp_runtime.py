"""Fail-closed QW-4B runtime-validation implementation contracts.

This module implements runtime identity probing, source/request binding,
authorization verification, matched P0/P1/P2 orchestration, and deterministic
engineering-report sealing.  It does not issue an authorization, choose seeds,
open a scientific campaign, or publish results.  A run is possible only when a
future frozen authorization object binds the exact preflight, source, image,
Torch2PC checkout, lane, cells, permissions, and output root.
"""

from __future__ import annotations

import hashlib
import importlib
import importlib.metadata
import json
import math
import platform
import re
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Final, Protocol, cast

from torch2pc_thesis.stage3b_qwake_core import Capability
from torch2pc_thesis.stage3b_qwake_fp_spec import (
    QWAKE_FP_SPECIAL_CASE_CONTRACT,
    QWakeFPPairId,
)
from torch2pc_thesis.stage3b_qwake_fp_validation import (
    QWAKE_FP_PRE_FREEZE_VALIDATION_REQUEST,
    DisabledCapabilityAudit,
    MatchedPairValidation,
    OracleIsolationRecord,
    PairArmId,
    PairArmRecord,
    PreFreezeValidationReport,
    RuntimeAdapterId,
    ValidationLane,
    build_pre_freeze_report,
    compare_matched_pair,
    validate_disabled_capability,
    validate_nested_observation_hashes,
    validate_oracle_isolation,
)

_RUNTIME_PREFLIGHT_SCHEMA_VERSION: Final = 1
_RUNTIME_AUTHORIZATION_SCHEMA_VERSION: Final = 1
_RUNTIME_REPORT_SCHEMA_VERSION: Final = 1
RUNTIME_PREFLIGHT_ID: Final = "stage3b-qwake-fp-runtime-preflight-v1"
RUNTIME_AUTHORIZATION_ID: Final = "stage3b-qwake-fp-runtime-authorization-v1"
RUNTIME_REPORT_ID: Final = "stage3b-qwake-fp-runtime-validation-report-v1"
RUNTIME_PREFLIGHT_STATUS: Final = (
    "runtime_preflight_passed_authorization_not_issued"
)
RUNTIME_AUTHORIZATION_STATUS: Final = "issued_single_runtime_validation_attempt"
RUNTIME_REPORT_STATUS: Final = "engineering_validation_sealed"
RUNTIME_OPERATOR_ACKNOWLEDGEMENT: Final = (
    "AUTHORIZE_QWAKE_FP_QW4B_SINGLE_ENGINEERING_VALIDATION_RUN"
)
RUNTIME_ENGINEERING_BATCH_ID: Final = "synthetic-engineering-batch-v1"
REQUEST_RELATIVE: Final = Path(
    "experiments/frozen/stage3b-qwake-fp-pre-freeze-validation-v1/request.json"
)
REQUEST_SUMS_RELATIVE: Final = REQUEST_RELATIVE.parent / "SHA256SUMS"
_COMMIT_PATTERN: Final = re.compile(r"^[0-9a-f]{40}$")
_SHA256_PATTERN: Final = re.compile(r"^sha256:[0-9a-f]{64}$")


class QWakeFPRuntimeError(RuntimeError):
    """Raised when runtime admission or engineering validation fails."""


class ArmOrder(StrEnum):
    """Balanced sequential arm orders admitted by the runtime runner."""

    REFERENCE_THEN_INSTRUMENTED = "reference_then_instrumented"
    INSTRUMENTED_THEN_REFERENCE = "instrumented_then_reference"

    @property
    def arms(self) -> tuple[PairArmId, PairArmId]:
        if self is ArmOrder.REFERENCE_THEN_INSTRUMENTED:
            return PairArmId.REFERENCE, PairArmId.INSTRUMENTED
        return PairArmId.INSTRUMENTED, PairArmId.REFERENCE


_RUNTIME_VALIDATION_CAPABILITIES: Final[frozenset[Capability]] = frozenset(
    {
        Capability.EXECUTE_FIXEDPRED,
        Capability.COLLECT_A0,
        Capability.COLLECT_A1,
        Capability.COLLECT_A2,
        Capability.RUN_ANALYTIC_EXACT,
        Capability.RUN_ANALYTIC_CONSERVATIVE,
        Capability.RUN_ANALYTIC_HEURISTIC,
        Capability.RUN_COST_DOMINANCE_CHECK,
        Capability.COMPUTE_CANONICAL_SUFFIX,
        Capability.COMPUTE_POST_ACTION_ORACLE,
        Capability.RUN_LIVE_ANALYTICS,
    }
)

RUNTIME_EFFECT_AUDIT_CAPABILITIES: Final[tuple[Capability, ...]] = (
    Capability.COLLECT_A0,
    Capability.COLLECT_A1,
    Capability.COLLECT_A2,
    Capability.RUN_LIVE_ANALYTICS,
    Capability.RUN_ANALYTIC_EXACT,
    Capability.RUN_ANALYTIC_CONSERVATIVE,
    Capability.RUN_ANALYTIC_HEURISTIC,
    Capability.RUN_COST_DOMINANCE_CHECK,
)

_BASE_ARM_CAPABILITIES: Final[frozenset[Capability]] = frozenset(
    {
        Capability.EXECUTE_FIXEDPRED,
        Capability.COMPUTE_CANONICAL_SUFFIX,
        Capability.COMPUTE_POST_ACTION_ORACLE,
    }
)


@dataclass(frozen=True)
class RuntimeValidationPermissionSet:
    """Engineering-only capability set with deny-all defaults."""

    capabilities: frozenset[Capability] = frozenset()

    def __post_init__(self) -> None:
        forbidden = self.capabilities - _RUNTIME_VALIDATION_CAPABILITIES
        if forbidden:
            names = ", ".join(sorted(item.value for item in forbidden))
            raise QWakeFPRuntimeError(
                f"runtime-validation permissions contain forbidden capabilities: {names}"
            )

    @classmethod
    def deny_all(cls) -> RuntimeValidationPermissionSet:
        return cls()

    @classmethod
    def complete(cls) -> RuntimeValidationPermissionSet:
        return cls(capabilities=_RUNTIME_VALIDATION_CAPABILITIES)

    def require(self, *capabilities: Capability) -> None:
        missing = tuple(item for item in capabilities if item not in self.capabilities)
        if missing:
            names = ", ".join(item.value for item in missing)
            raise QWakeFPRuntimeError(
                f"runtime-validation capability is not authorized: {names}"
            )


@dataclass(frozen=True)
class RuntimeProbe:
    """Stable runtime identity used by the future authorization."""

    lane: ValidationLane
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

    def __post_init__(self) -> None:
        for field_name in (
            "python_version",
            "python_implementation",
            "python_executable",
            "platform",
            "machine",
            "torch_version",
            "dtype",
        ):
            if not str(getattr(self, field_name)).strip():
                raise QWakeFPRuntimeError(f"runtime probe field is empty: {field_name}")
        if self.accelerator_count < 0:
            raise QWakeFPRuntimeError("accelerator_count must be non-negative")
        if self.lane is ValidationLane.CPU_FLOAT64_ENGINEERING:
            if self.dtype != "float64":
                raise QWakeFPRuntimeError("CPU engineering lane must use float64")
        else:
            if self.dtype != "float32":
                raise QWakeFPRuntimeError("ROCm canonical lane must use float32")
            if not self.accelerator_available or self.accelerator_count < 1:
                raise QWakeFPRuntimeError("ROCm lane requires an available accelerator")
            if not self.hip_version.strip():
                raise QWakeFPRuntimeError("ROCm lane requires a HIP runtime version")
            if not self.accelerator_name.strip():
                raise QWakeFPRuntimeError("ROCm lane requires an accelerator name")


class RuntimeProbeBackend(Protocol):
    """Injectable probe boundary used by unit tests and the live preflight."""

    def probe(self, lane: ValidationLane) -> RuntimeProbe:
        """Return the exact runtime identity for one lane."""


@dataclass(frozen=True)
class RuntimeSourceIdentity:
    """Source, request, Torch2PC, and image identity bound by preflight."""

    source_commit: str
    source_index_sha256: str
    torch2pc_commit: str
    image_digest: str
    request_sha256: str
    special_case_contract_sha256: str
    adapter_registry_sha256: str

    def __post_init__(self) -> None:
        _require_commit(self.source_commit, field_name="source_commit")
        _require_commit(self.torch2pc_commit, field_name="torch2pc_commit")
        for field_name in (
            "source_index_sha256",
            "image_digest",
            "request_sha256",
            "special_case_contract_sha256",
            "adapter_registry_sha256",
        ):
            _require_sha256(str(getattr(self, field_name)), field_name=field_name)


@dataclass(frozen=True)
class QWakeFPRuntimePreflight:
    """Non-computational preflight; authorization and execution remain closed."""

    schema_version: int
    preflight_id: str
    status: str
    captured_at_utc: str
    source_identity: RuntimeSourceIdentity
    runtime_probes: tuple[RuntimeProbe, ...]
    bound_adapter_ids: tuple[RuntimeAdapterId, ...]
    permissions: RuntimeValidationPermissionSet
    execution_authorization_present: bool
    runtime_validation_permitted: bool
    runtime_validation_performed: bool
    engineering_evidence_present: bool
    scientific_execution_open: bool
    image_freeze_permitted: bool
    test_dataset_access: bool
    preflight_sha256: str

    def __post_init__(self) -> None:
        if self.schema_version != _RUNTIME_PREFLIGHT_SCHEMA_VERSION:
            raise QWakeFPRuntimeError("runtime preflight schema_version must be 1")
        if self.preflight_id != RUNTIME_PREFLIGHT_ID:
            raise QWakeFPRuntimeError("unexpected runtime preflight id")
        if self.status != RUNTIME_PREFLIGHT_STATUS:
            raise QWakeFPRuntimeError("runtime preflight status is not closed")
        _require_utc(self.captured_at_utc, field_name="captured_at_utc")
        if tuple(probe.lane for probe in self.runtime_probes) != tuple(ValidationLane):
            raise QWakeFPRuntimeError("runtime preflight must bind CPU then ROCm")
        if self.bound_adapter_ids != tuple(RuntimeAdapterId):
            raise QWakeFPRuntimeError("runtime adapter registry is incomplete")
        if self.permissions.capabilities:
            raise QWakeFPRuntimeError("preflight permissions must deny all effects")
        if any(
            (
                self.execution_authorization_present,
                self.runtime_validation_permitted,
                self.runtime_validation_performed,
                self.engineering_evidence_present,
                self.scientific_execution_open,
                self.image_freeze_permitted,
                self.test_dataset_access,
            )
        ):
            raise QWakeFPRuntimeError("preflight cannot open execution or claims")
        _require_sha256(self.preflight_sha256, field_name="preflight_sha256")
        if self.preflight_sha256 != self.computed_sha256():
            raise QWakeFPRuntimeError("runtime preflight digest differs")

    def payload_without_digest(self) -> dict[str, object]:
        payload = cast(dict[str, object], _canonicalize(asdict(self)))
        payload.pop("preflight_sha256")
        return payload

    def computed_sha256(self) -> str:
        return _sha256_object(self.payload_without_digest())

    def canonical_json(self) -> str:
        return _canonical_json(self)


@dataclass(frozen=True)
class RuntimeCellSpec:
    """One authorized matched validation cell."""

    lane: ValidationLane
    pair_id: QWakeFPPairId
    model_seed: int
    batch_id: str
    arm_order: ArmOrder

    def __post_init__(self) -> None:
        if self.model_seed < 0:
            raise QWakeFPRuntimeError("model_seed must be non-negative")
        if not self.batch_id.strip():
            raise QWakeFPRuntimeError("batch_id cannot be empty")

    @property
    def cell_id(self) -> str:
        return (
            f"{self.lane.value}:{self.pair_id.value}:"
            f"seed-{self.model_seed}:{self.batch_id}"
        )


@dataclass(frozen=True)
class QWakeFPRuntimeAuthorization:
    """Future frozen single-attempt authorization schema."""

    schema_version: int
    authorization_id: str
    status: str
    issued_at_utc: str
    operator_acknowledgement: str
    preflight_sha256: str
    source_identity: RuntimeSourceIdentity
    static_validation_receipt_sha256: str
    receipt_chain_sha256: str
    permissions: RuntimeValidationPermissionSet
    cells: tuple[RuntimeCellSpec, ...]
    output_root: str
    output_root_absent_at_issue: bool
    execution_count: int
    scientific_execution_open: bool
    test_dataset_access: bool
    publication_permitted: bool
    image_freeze_permitted: bool
    authorization_sha256: str

    def __post_init__(self) -> None:
        if self.schema_version != _RUNTIME_AUTHORIZATION_SCHEMA_VERSION:
            raise QWakeFPRuntimeError("runtime authorization schema_version must be 1")
        if self.authorization_id != RUNTIME_AUTHORIZATION_ID:
            raise QWakeFPRuntimeError("unexpected runtime authorization id")
        if self.status != RUNTIME_AUTHORIZATION_STATUS:
            raise QWakeFPRuntimeError("runtime authorization status differs")
        _require_utc(self.issued_at_utc, field_name="issued_at_utc")
        if self.operator_acknowledgement != RUNTIME_OPERATOR_ACKNOWLEDGEMENT:
            raise QWakeFPRuntimeError("operator acknowledgement differs")
        _require_sha256(self.preflight_sha256, field_name="preflight_sha256")
        _require_sha256(
            self.static_validation_receipt_sha256,
            field_name="static_validation_receipt_sha256",
        )
        _require_sha256(
            self.receipt_chain_sha256,
            field_name="receipt_chain_sha256",
        )
        expected_chain = compute_runtime_receipt_chain_sha256(
            preflight_sha256=self.preflight_sha256,
            static_validation_receipt_sha256=(
                self.static_validation_receipt_sha256
            ),
        )
        if self.receipt_chain_sha256 != expected_chain:
            raise QWakeFPRuntimeError(
                "runtime authorization receipt chain differs"
            )
        if self.permissions != RuntimeValidationPermissionSet.complete():
            raise QWakeFPRuntimeError(
                "runtime authorization must use the exact engineering capability set"
            )
        expected_cell_count = len(ValidationLane) * len(QWakeFPPairId)
        if len(self.cells) != expected_cell_count:
            raise QWakeFPRuntimeError(
                "runtime authorization must contain exactly six cells"
            )
        if len(self.cells) != len({cell.cell_id for cell in self.cells}):
            raise QWakeFPRuntimeError("runtime authorization contains duplicate cells")
        lanes = {cell.lane for cell in self.cells}
        if lanes != set(ValidationLane):
            raise QWakeFPRuntimeError("authorization must contain CPU and ROCm lanes")
        for lane in ValidationLane:
            pairs = tuple(
                cell.pair_id for cell in self.cells if cell.lane is lane
            )
            if len(pairs) != len(QWakeFPPairId) or set(pairs) != set(QWakeFPPairId):
                raise QWakeFPRuntimeError(
                    "each lane must contain P0, P1, P2 exactly once"
                )
        identities = {(cell.model_seed, cell.batch_id) for cell in self.cells}
        if len(identities) != 1:
            raise QWakeFPRuntimeError(
                "all runtime-validation cells must share one seed and batch"
            )
        if any(cell.batch_id != RUNTIME_ENGINEERING_BATCH_ID for cell in self.cells):
            raise QWakeFPRuntimeError("runtime-validation batch id differs")
        output_path = Path(self.output_root)
        if (
            not self.output_root.strip()
            or output_path.is_absolute()
            or output_path == Path(".")
            or ".." in output_path.parts
        ):
            raise QWakeFPRuntimeError(
                "output_root must be a confined non-empty relative path"
            )
        if not self.output_root_absent_at_issue:
            raise QWakeFPRuntimeError("output root must be absent when authorization is issued")
        if self.execution_count != 1:
            raise QWakeFPRuntimeError("runtime authorization must allow one attempt")
        if any(
            (
                self.scientific_execution_open,
                self.test_dataset_access,
                self.publication_permitted,
                self.image_freeze_permitted,
            )
        ):
            raise QWakeFPRuntimeError(
                "runtime authorization cannot open science, publication, or image freeze"
            )
        _require_sha256(self.authorization_sha256, field_name="authorization_sha256")
        if self.authorization_sha256 != self.computed_sha256():
            raise QWakeFPRuntimeError("runtime authorization digest differs")

    def payload_without_digest(self) -> dict[str, object]:
        payload = cast(dict[str, object], _canonicalize(asdict(self)))
        payload.pop("authorization_sha256")
        return payload

    def computed_sha256(self) -> str:
        return _sha256_object(self.payload_without_digest())

    def canonical_json(self) -> str:
        return _canonical_json(self)


@dataclass(frozen=True)
class RuntimeArmExecution:
    """One backend arm result with oracle and disabled-effect audits."""

    record: PairArmRecord
    oracle_isolation: OracleIsolationRecord
    disabled_capability_audits: tuple[DisabledCapabilityAudit, ...]


class MatchedRuntimeBackend(Protocol):
    """State/RNG-restorable backend used by the matched runner."""

    def capture_initial_state(self) -> bytes:
        """Capture model, optimizer, and other mutable canonical state."""

    def restore_initial_state(self, state: bytes) -> None:
        """Restore the exact captured canonical state."""

    def capture_rng_state(self) -> bytes:
        """Capture every RNG stream used by the cell."""

    def restore_rng_state(self, state: bytes) -> None:
        """Restore every RNG stream used by the cell."""

    def run_arm(
        self,
        cell: RuntimeCellSpec,
        arm_id: PairArmId,
        permissions: RuntimeValidationPermissionSet,
    ) -> RuntimeArmExecution:
        """Execute one sequential arm after state and RNG restoration."""


@dataclass(frozen=True)
class RuntimeCellResult:
    """Validated result of one matched cell."""

    cell: RuntimeCellSpec
    reference: PairArmRecord
    instrumented: PairArmRecord
    pair_validation: MatchedPairValidation
    oracle_isolation_passed: bool
    disabled_capability_audits: tuple[DisabledCapabilityAudit, ...]

    @property
    def passed(self) -> bool:
        return (
            self.pair_validation.passed
            and self.oracle_isolation_passed
            and all(item.passed for item in self.disabled_capability_audits)
        )


@dataclass(frozen=True)
class RuntimeLaneReport:
    """All P0/P1/P2 cells and nesting checks for one lane."""

    lane: ValidationLane
    cells: tuple[RuntimeCellResult, ...]
    nested_observations_passed: bool

    def __post_init__(self) -> None:
        if tuple(item.cell.pair_id for item in self.cells) != tuple(QWakeFPPairId):
            raise QWakeFPRuntimeError("lane report must contain P0, P1, P2 in order")
        if any(item.cell.lane is not self.lane for item in self.cells):
            raise QWakeFPRuntimeError("lane report contains a foreign cell")

    @property
    def passed(self) -> bool:
        return self.nested_observations_passed and all(item.passed for item in self.cells)


@dataclass(frozen=True)
class QWakeFPRuntimeEngineeringReport:
    """Sealable engineering result; never scientific evidence."""

    schema_version: int
    report_id: str
    status: str
    request_sha256: str
    preflight_sha256: str
    authorization_sha256: str
    source_identity: RuntimeSourceIdentity
    lanes: tuple[RuntimeLaneReport, ...]
    manifest_integrity_passed: bool
    receipt_chain_passed: bool
    static_and_unit_passed: bool
    engineering_evidence_only: bool
    scientific_evidence: bool
    publication_permitted: bool
    image_freeze_eligible: bool

    def __post_init__(self) -> None:
        if self.schema_version != _RUNTIME_REPORT_SCHEMA_VERSION:
            raise QWakeFPRuntimeError("runtime report schema_version must be 1")
        if self.report_id != RUNTIME_REPORT_ID:
            raise QWakeFPRuntimeError("unexpected runtime report id")
        if self.status != RUNTIME_REPORT_STATUS:
            raise QWakeFPRuntimeError("runtime report status differs")
        for field_name in (
            "request_sha256",
            "preflight_sha256",
            "authorization_sha256",
        ):
            _require_sha256(str(getattr(self, field_name)), field_name=field_name)
        if tuple(item.lane for item in self.lanes) != tuple(ValidationLane):
            raise QWakeFPRuntimeError("runtime report must contain CPU then ROCm")
        if not self.engineering_evidence_only or self.scientific_evidence:
            raise QWakeFPRuntimeError("QW-4B report must remain engineering evidence")
        if self.publication_permitted:
            raise QWakeFPRuntimeError("QW-4B report cannot permit publication")
        expected_eligible = (
            all(item.passed for item in self.lanes)
            and self.manifest_integrity_passed
            and self.receipt_chain_passed
            and self.static_and_unit_passed
        )
        if self.image_freeze_eligible != expected_eligible:
            raise QWakeFPRuntimeError("image-freeze eligibility differs from gates")

    def canonical_json(self) -> str:
        return _canonical_json(self)

    def sha256(self) -> str:
        return _sha256_text(self.canonical_json())


@dataclass(frozen=True)
class RuntimeValidationSession:
    """Validated single-attempt runtime session."""

    preflight: QWakeFPRuntimePreflight
    authorization: QWakeFPRuntimeAuthorization
    permissions: RuntimeValidationPermissionSet
    output_root: Path


@dataclass(frozen=True)
class SealedRuntimeEngineeringReport:
    """Canonical report bytes and digest returned before filesystem sealing."""

    report: QWakeFPRuntimeEngineeringReport
    canonical_json: str
    sha256: str

    def __post_init__(self) -> None:
        if self.canonical_json != self.report.canonical_json():
            raise QWakeFPRuntimeError("sealed report JSON differs from the report")
        if self.sha256 != self.report.sha256():
            raise QWakeFPRuntimeError("sealed report digest differs")


def probe_runtime(
    lane: ValidationLane,
    *,
    backend: RuntimeProbeBackend | None = None,
) -> RuntimeProbe:
    """Probe one lane without executing a model or reading a dataset."""

    if backend is not None:
        probe = backend.probe(lane)
        if probe.lane is not lane:
            raise QWakeFPRuntimeError("probe backend returned the wrong lane")
        return probe
    torch = importlib.import_module("torch")
    torch_version = importlib.metadata.version("torch")
    torch_runtime_version = getattr(torch, "version", None)
    hip_version = str(getattr(torch_runtime_version, "hip", "") or "")
    accelerator = getattr(torch, "cuda", None)
    if accelerator is None:
        raise QWakeFPRuntimeError("PyTorch accelerator API is unavailable")
    available = bool(accelerator.is_available())
    count = int(accelerator.device_count()) if available else 0
    name = str(accelerator.get_device_name(0)) if count else ""
    dtype = "float64" if lane is ValidationLane.CPU_FLOAT64_ENGINEERING else "float32"
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
    )


def build_runtime_preflight(
    project_root: Path,
    torch2pc_dir: Path,
    *,
    source_commit: str,
    torch2pc_commit: str,
    image_digest: str,
    captured_at_utc: str,
    probe_backend: RuntimeProbeBackend | None = None,
) -> QWakeFPRuntimePreflight:
    """Build a non-computational, deny-all runtime preflight."""

    root = project_root.expanduser().resolve()
    checkout = torch2pc_dir.expanduser().resolve()
    _require_clean_checkout(root, expected_commit=source_commit, label="project")
    _require_clean_checkout(
        checkout,
        expected_commit=torch2pc_commit,
        label="Torch2PC",
    )
    request_sha256 = _verify_frozen_request(root)
    source_identity = RuntimeSourceIdentity(
        source_commit=source_commit,
        source_index_sha256=_source_index_sha256(root),
        torch2pc_commit=torch2pc_commit,
        image_digest=image_digest,
        request_sha256=request_sha256,
        special_case_contract_sha256=(
            f"sha256:{QWAKE_FP_SPECIAL_CASE_CONTRACT.sha256()}"
        ),
        adapter_registry_sha256=_adapter_registry_sha256(),
    )
    runtime_probes = tuple(
        probe_runtime(lane, backend=probe_backend)
        for lane in ValidationLane
    )
    bound_adapter_ids = tuple(RuntimeAdapterId)
    permissions = RuntimeValidationPermissionSet.deny_all()

    payload: dict[str, object] = {
        "schema_version": _RUNTIME_PREFLIGHT_SCHEMA_VERSION,
        "preflight_id": RUNTIME_PREFLIGHT_ID,
        "status": RUNTIME_PREFLIGHT_STATUS,
        "captured_at_utc": captured_at_utc,
        "source_identity": source_identity,
        "runtime_probes": runtime_probes,
        "bound_adapter_ids": bound_adapter_ids,
        "permissions": permissions,
        "execution_authorization_present": False,
        "runtime_validation_permitted": False,
        "runtime_validation_performed": False,
        "engineering_evidence_present": False,
        "scientific_execution_open": False,
        "image_freeze_permitted": False,
        "test_dataset_access": False,
    }
    return QWakeFPRuntimePreflight(
        schema_version=_RUNTIME_PREFLIGHT_SCHEMA_VERSION,
        preflight_id=RUNTIME_PREFLIGHT_ID,
        status=RUNTIME_PREFLIGHT_STATUS,
        captured_at_utc=captured_at_utc,
        source_identity=source_identity,
        runtime_probes=runtime_probes,
        bound_adapter_ids=bound_adapter_ids,
        permissions=permissions,
        execution_authorization_present=False,
        runtime_validation_permitted=False,
        runtime_validation_performed=False,
        engineering_evidence_present=False,
        scientific_execution_open=False,
        image_freeze_permitted=False,
        test_dataset_access=False,
        preflight_sha256=_sha256_object(payload),
    )


def validate_runtime_preflight(
    preflight: QWakeFPRuntimePreflight,
    project_root: Path,
    torch2pc_dir: Path,
    *,
    probe_backend: RuntimeProbeBackend | None = None,
) -> None:
    """Revalidate a preflight against the current source and runtime."""

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
        raise QWakeFPRuntimeError("project source index differs from preflight")
    if _verify_frozen_request(root) != preflight.source_identity.request_sha256:
        raise QWakeFPRuntimeError("frozen request differs from preflight")
    if _adapter_registry_sha256() != preflight.source_identity.adapter_registry_sha256:
        raise QWakeFPRuntimeError("runtime adapter registry differs from preflight")
    current_probes = tuple(
        probe_runtime(probe.lane, backend=probe_backend)
        for probe in preflight.runtime_probes
    )
    if current_probes != preflight.runtime_probes:
        raise QWakeFPRuntimeError("runtime probes differ from preflight")


def verify_static_validation_receipt(
    authorization: QWakeFPRuntimeAuthorization,
    receipt_path: Path,
) -> str:
    """Verify the exact static/unit receipt referenced by authorization."""

    path = receipt_path.expanduser().resolve()
    if path.is_symlink() or not path.is_file():
        raise QWakeFPRuntimeError(
            "static validation receipt must be a regular file"
        )
    observed = _sha256_bytes(path.read_bytes())
    if observed != authorization.static_validation_receipt_sha256:
        raise QWakeFPRuntimeError(
            "static validation receipt digest differs from authorization"
        )
    expected_chain = compute_runtime_receipt_chain_sha256(
        preflight_sha256=authorization.preflight_sha256,
        static_validation_receipt_sha256=observed,
    )
    if expected_chain != authorization.receipt_chain_sha256:
        raise QWakeFPRuntimeError(
            "static validation receipt chain differs from authorization"
        )
    return observed


def open_runtime_session(
    preflight: QWakeFPRuntimePreflight,
    authorization: QWakeFPRuntimeAuthorization,
    project_root: Path,
    torch2pc_dir: Path,
    *,
    probe_backend: RuntimeProbeBackend | None = None,
) -> RuntimeValidationSession:
    """Open one engineering session only after every frozen binding passes."""

    validate_runtime_preflight(
        preflight,
        project_root,
        torch2pc_dir,
        probe_backend=probe_backend,
    )
    if authorization.preflight_sha256 != preflight.preflight_sha256:
        raise QWakeFPRuntimeError("authorization preflight digest differs")
    if authorization.source_identity != preflight.source_identity:
        raise QWakeFPRuntimeError("authorization source identity differs")
    root = project_root.expanduser().resolve()
    output_root = (root / authorization.output_root).resolve(strict=False)
    if not output_root.is_relative_to(root):
        raise QWakeFPRuntimeError("authorized output root escapes the project")
    if output_root.exists():
        raise QWakeFPRuntimeError("authorized output root already exists")
    return RuntimeValidationSession(
        preflight=preflight,
        authorization=authorization,
        permissions=authorization.permissions,
        output_root=output_root,
    )


def execute_matched_cell(
    session: RuntimeValidationSession,
    backend: MatchedRuntimeBackend,
    cell: RuntimeCellSpec,
) -> RuntimeCellResult:
    """Run one matched cell sequentially from one captured state and RNG."""

    if cell not in session.authorization.cells:
        raise QWakeFPRuntimeError("cell is not present in the authorization")
    session.permissions.require(*_RUNTIME_VALIDATION_CAPABILITIES)
    initial_state = backend.capture_initial_state()
    rng_state = backend.capture_rng_state()
    if not initial_state or not rng_state:
        raise QWakeFPRuntimeError("backend returned an empty state or RNG snapshot")
    initial_sha256 = _sha256_bytes(initial_state)
    rng_sha256 = _sha256_bytes(rng_state)
    executions: dict[PairArmId, RuntimeArmExecution] = {}
    for arm_id in cell.arm_order.arms:
        backend.restore_initial_state(initial_state)
        backend.restore_rng_state(rng_state)
        arm_permissions = _permissions_for_arm(cell.pair_id, arm_id)
        if not arm_permissions.capabilities.issubset(session.permissions.capabilities):
            raise QWakeFPRuntimeError(
                "arm permissions exceed the authorized engineering capability set"
            )
        execution = backend.run_arm(cell, arm_id, arm_permissions)
        record = execution.record
        if record.pair_id is not cell.pair_id or record.arm_id is not arm_id:
            raise QWakeFPRuntimeError("backend returned the wrong pair arm")
        if record.lane is not cell.lane:
            raise QWakeFPRuntimeError("backend returned the wrong validation lane")
        if record.model_seed != cell.model_seed or record.batch_id != cell.batch_id:
            raise QWakeFPRuntimeError("backend returned the wrong cell identity")
        if record.initial_state_sha256 != initial_sha256:
            raise QWakeFPRuntimeError("backend initial-state hash differs")
        if record.rng_state_before_sha256 != rng_sha256:
            raise QWakeFPRuntimeError("backend RNG-before hash differs")
        validate_oracle_isolation(execution.oracle_isolation)
        expected_disabled = _expected_disabled_capabilities(arm_permissions)
        observed_disabled = tuple(
            audit.capability for audit in execution.disabled_capability_audits
        )
        if observed_disabled != expected_disabled:
            raise QWakeFPRuntimeError(
                "disabled capability audit registry differs from the arm permissions"
            )
        for audit in execution.disabled_capability_audits:
            validate_disabled_capability(audit)
        executions[arm_id] = execution
    reference = executions[PairArmId.REFERENCE]
    instrumented = executions[PairArmId.INSTRUMENTED]
    pair_validation = compare_matched_pair(reference.record, instrumented.record)
    audits = _merge_disabled_audits(
        reference.disabled_capability_audits,
        instrumented.disabled_capability_audits,
    )
    return RuntimeCellResult(
        cell=cell,
        reference=reference.record,
        instrumented=instrumented.record,
        pair_validation=pair_validation,
        oracle_isolation_passed=(
            reference.oracle_isolation.passed
            and instrumented.oracle_isolation.passed
        ),
        disabled_capability_audits=audits,
    )


def build_lane_report(
    lane: ValidationLane,
    cells: Sequence[RuntimeCellResult],
) -> RuntimeLaneReport:
    """Validate pair order and cumulative observation nesting for one lane."""

    lane_cells = tuple(cells)
    if len(lane_cells) != len(QWakeFPPairId):
        raise QWakeFPRuntimeError("lane report requires exactly P0, P1, P2")
    if any(item.cell.lane is not lane for item in lane_cells):
        raise QWakeFPRuntimeError("lane report contains a foreign cell")
    if {item.cell.pair_id for item in lane_cells} != set(QWakeFPPairId):
        raise QWakeFPRuntimeError("lane report pair registry differs")
    ordered = tuple(
        sorted(
            lane_cells,
            key=lambda item: tuple(QWakeFPPairId).index(item.cell.pair_id),
        )
    )
    nested = validate_nested_observation_hashes(
        ordered[0].instrumented,
        ordered[1].instrumented,
        ordered[2].instrumented,
    )
    return RuntimeLaneReport(
        lane=lane,
        cells=ordered,
        nested_observations_passed=nested,
    )


def build_engineering_report(
    session: RuntimeValidationSession,
    lane_reports: Sequence[RuntimeLaneReport],
    *,
    manifest_integrity_passed: bool,
    receipt_chain_passed: bool,
    static_and_unit_passed: bool,
) -> QWakeFPRuntimeEngineeringReport:
    """Build a deterministic two-lane engineering report."""

    lanes = tuple(lane_reports)
    eligible = (
        all(item.passed for item in lanes)
        and manifest_integrity_passed
        and receipt_chain_passed
        and static_and_unit_passed
    )
    return QWakeFPRuntimeEngineeringReport(
        schema_version=_RUNTIME_REPORT_SCHEMA_VERSION,
        report_id=RUNTIME_REPORT_ID,
        status=RUNTIME_REPORT_STATUS,
        request_sha256=session.preflight.source_identity.request_sha256,
        preflight_sha256=session.preflight.preflight_sha256,
        authorization_sha256=session.authorization.authorization_sha256,
        source_identity=session.preflight.source_identity,
        lanes=lanes,
        manifest_integrity_passed=manifest_integrity_passed,
        receipt_chain_passed=receipt_chain_passed,
        static_and_unit_passed=static_and_unit_passed,
        engineering_evidence_only=True,
        scientific_evidence=False,
        publication_permitted=False,
        image_freeze_eligible=eligible,
    )


def seal_engineering_report(
    report: QWakeFPRuntimeEngineeringReport,
) -> SealedRuntimeEngineeringReport:
    """Return canonical report bytes and digest without writing files."""

    return SealedRuntimeEngineeringReport(
        report=report,
        canonical_json=report.canonical_json(),
        sha256=report.sha256(),
    )


def to_pre_freeze_validation_report(
    report: QWakeFPRuntimeEngineeringReport,
) -> PreFreezeValidationReport:
    """Project the richer two-lane report onto the QW-4A freeze gate."""

    lane_map = {lane.lane: lane for lane in report.lanes}
    rocm = lane_map[ValidationLane.ROCM_FLOAT32_CANONICAL]
    all_audits = tuple(
        audit
        for lane in report.lanes
        for cell in lane.cells
        for audit in cell.disabled_capability_audits
    )
    return build_pre_freeze_report(
        pair_results=tuple(cell.pair_validation for cell in rocm.cells),
        nested_observations_passed=all(
            lane.nested_observations_passed for lane in report.lanes
        ),
        disabled_capability_audits=all_audits,
        oracle_isolation_passed=all(
            cell.oracle_isolation_passed
            for lane in report.lanes
            for cell in lane.cells
        ),
        manifest_integrity_passed=report.manifest_integrity_passed,
        receipt_chain_passed=report.receipt_chain_passed,
        static_and_unit_passed=report.static_and_unit_passed,
        cpu_smoke_passed=lane_map[ValidationLane.CPU_FLOAT64_ENGINEERING].passed,
        rocm_smoke_passed=rocm.passed,
    )


def compute_runtime_receipt_chain_sha256(
    *,
    preflight_sha256: str,
    static_validation_receipt_sha256: str,
) -> str:
    """Bind the static-validation receipt to one exact preflight."""

    _require_sha256(preflight_sha256, field_name="preflight_sha256")
    _require_sha256(
        static_validation_receipt_sha256,
        field_name="static_validation_receipt_sha256",
    )
    return _sha256_object(
        {
            "preflight_sha256": preflight_sha256,
            "static_validation_receipt_sha256": (
                static_validation_receipt_sha256
            ),
        }
    )


def compute_runtime_authorization_sha256(
    unsigned_payload: Mapping[str, object],
) -> str:
    """Compute the digest of a candidate authorization without issuing it."""

    if "authorization_sha256" in unsigned_payload:
        raise QWakeFPRuntimeError(
            "unsigned authorization payload cannot contain authorization_sha256"
        )
    return _sha256_object(dict(unsigned_payload))


def load_preflight(path: Path) -> QWakeFPRuntimePreflight:
    """Load a preflight JSON object using the strict runtime schema."""

    payload = _load_json(path)
    return _preflight_from_mapping(payload)


def load_authorization(path: Path) -> QWakeFPRuntimeAuthorization:
    """Load a future frozen authorization using the strict runtime schema."""

    payload = _load_json(path)
    return _authorization_from_mapping(payload)


def _preflight_from_mapping(value: Mapping[str, object]) -> QWakeFPRuntimePreflight:
    _require_exact_keys(
        value,
        {
            "schema_version",
            "preflight_id",
            "status",
            "captured_at_utc",
            "source_identity",
            "runtime_probes",
            "bound_adapter_ids",
            "permissions",
            "execution_authorization_present",
            "runtime_validation_permitted",
            "runtime_validation_performed",
            "engineering_evidence_present",
            "scientific_execution_open",
            "image_freeze_permitted",
            "test_dataset_access",
            "preflight_sha256",
        },
        "runtime preflight",
    )
    source = _source_identity_from_mapping(
        _mapping(value.get("source_identity"), "source_identity")
    )
    probes = tuple(
        _runtime_probe_from_mapping(_mapping(item, "runtime_probes[]"))
        for item in _sequence(value.get("runtime_probes"), "runtime_probes")
    )
    permissions = _permissions_from_mapping(
        _mapping(value.get("permissions"), "permissions")
    )
    adapters = tuple(
        RuntimeAdapterId(str(item))
        for item in _sequence(value.get("bound_adapter_ids"), "bound_adapter_ids")
    )
    return QWakeFPRuntimePreflight(
        schema_version=_integer(value.get("schema_version"), "schema_version"),
        preflight_id=_string(value.get("preflight_id"), "preflight_id"),
        status=_string(value.get("status"), "status"),
        captured_at_utc=_string(value.get("captured_at_utc"), "captured_at_utc"),
        source_identity=source,
        runtime_probes=probes,
        bound_adapter_ids=adapters,
        permissions=permissions,
        execution_authorization_present=_boolean(
            value.get("execution_authorization_present"),
            "execution_authorization_present",
        ),
        runtime_validation_permitted=_boolean(
            value.get("runtime_validation_permitted"),
            "runtime_validation_permitted",
        ),
        runtime_validation_performed=_boolean(
            value.get("runtime_validation_performed"),
            "runtime_validation_performed",
        ),
        engineering_evidence_present=_boolean(
            value.get("engineering_evidence_present"),
            "engineering_evidence_present",
        ),
        scientific_execution_open=_boolean(
            value.get("scientific_execution_open"),
            "scientific_execution_open",
        ),
        image_freeze_permitted=_boolean(
            value.get("image_freeze_permitted"),
            "image_freeze_permitted",
        ),
        test_dataset_access=_boolean(
            value.get("test_dataset_access"),
            "test_dataset_access",
        ),
        preflight_sha256=_string(
            value.get("preflight_sha256"),
            "preflight_sha256",
        ),
    )


def _authorization_from_mapping(value: Mapping[str, object]) -> QWakeFPRuntimeAuthorization:
    _require_exact_keys(
        value,
        {
            "schema_version",
            "authorization_id",
            "status",
            "issued_at_utc",
            "operator_acknowledgement",
            "preflight_sha256",
            "source_identity",
            "static_validation_receipt_sha256",
            "receipt_chain_sha256",
            "permissions",
            "cells",
            "output_root",
            "output_root_absent_at_issue",
            "execution_count",
            "scientific_execution_open",
            "test_dataset_access",
            "publication_permitted",
            "image_freeze_permitted",
            "authorization_sha256",
        },
        "runtime authorization",
    )
    cells = tuple(
        _cell_from_mapping(_mapping(item, "cells[]"))
        for item in _sequence(value.get("cells"), "cells")
    )
    return QWakeFPRuntimeAuthorization(
        schema_version=_integer(value.get("schema_version"), "schema_version"),
        authorization_id=_string(value.get("authorization_id"), "authorization_id"),
        status=_string(value.get("status"), "status"),
        issued_at_utc=_string(value.get("issued_at_utc"), "issued_at_utc"),
        operator_acknowledgement=_string(
            value.get("operator_acknowledgement"),
            "operator_acknowledgement",
        ),
        preflight_sha256=_string(value.get("preflight_sha256"), "preflight_sha256"),
        source_identity=_source_identity_from_mapping(
            _mapping(value.get("source_identity"), "source_identity")
        ),
        static_validation_receipt_sha256=_string(
            value.get("static_validation_receipt_sha256"),
            "static_validation_receipt_sha256",
        ),
        receipt_chain_sha256=_string(
            value.get("receipt_chain_sha256"),
            "receipt_chain_sha256",
        ),
        permissions=_permissions_from_mapping(
            _mapping(value.get("permissions"), "permissions")
        ),
        cells=cells,
        output_root=_string(value.get("output_root"), "output_root"),
        output_root_absent_at_issue=_boolean(
            value.get("output_root_absent_at_issue"),
            "output_root_absent_at_issue",
        ),
        execution_count=_integer(value.get("execution_count"), "execution_count"),
        scientific_execution_open=_boolean(
            value.get("scientific_execution_open"),
            "scientific_execution_open",
        ),
        test_dataset_access=_boolean(
            value.get("test_dataset_access"),
            "test_dataset_access",
        ),
        publication_permitted=_boolean(
            value.get("publication_permitted"),
            "publication_permitted",
        ),
        image_freeze_permitted=_boolean(
            value.get("image_freeze_permitted"),
            "image_freeze_permitted",
        ),
        authorization_sha256=_string(
            value.get("authorization_sha256"),
            "authorization_sha256",
        ),
    )


def _source_identity_from_mapping(value: Mapping[str, object]) -> RuntimeSourceIdentity:
    _require_exact_keys(
        value,
        {
            "source_commit",
            "source_index_sha256",
            "torch2pc_commit",
            "image_digest",
            "request_sha256",
            "special_case_contract_sha256",
            "adapter_registry_sha256",
        },
        "source_identity",
    )
    return RuntimeSourceIdentity(
        source_commit=_string(value.get("source_commit"), "source_commit"),
        source_index_sha256=_string(
            value.get("source_index_sha256"),
            "source_index_sha256",
        ),
        torch2pc_commit=_string(value.get("torch2pc_commit"), "torch2pc_commit"),
        image_digest=_string(value.get("image_digest"), "image_digest"),
        request_sha256=_string(value.get("request_sha256"), "request_sha256"),
        special_case_contract_sha256=_string(
            value.get("special_case_contract_sha256"),
            "special_case_contract_sha256",
        ),
        adapter_registry_sha256=_string(
            value.get("adapter_registry_sha256"),
            "adapter_registry_sha256",
        ),
    )


def _runtime_probe_from_mapping(value: Mapping[str, object]) -> RuntimeProbe:
    _require_exact_keys(
        value,
        {
            "lane",
            "python_version",
            "python_implementation",
            "python_executable",
            "platform",
            "machine",
            "torch_version",
            "hip_version",
            "accelerator_available",
            "accelerator_count",
            "accelerator_name",
            "dtype",
        },
        "runtime_probe",
    )
    return RuntimeProbe(
        lane=ValidationLane(_string(value.get("lane"), "lane")),
        python_version=_string(value.get("python_version"), "python_version"),
        python_implementation=_string(value.get("python_implementation"), "python_implementation"),
        python_executable=_string(value.get("python_executable"), "python_executable"),
        platform=_string(value.get("platform"), "platform"),
        machine=_string(value.get("machine"), "machine"),
        torch_version=_string(value.get("torch_version"), "torch_version"),
        hip_version=_string_allow_empty(value.get("hip_version"), "hip_version"),
        accelerator_available=_boolean(value.get("accelerator_available"), "accelerator_available"),
        accelerator_count=_integer(value.get("accelerator_count"), "accelerator_count"),
        accelerator_name=_string_allow_empty(value.get("accelerator_name"), "accelerator_name"),
        dtype=_string(value.get("dtype"), "dtype"),
    )


def _permissions_from_mapping(value: Mapping[str, object]) -> RuntimeValidationPermissionSet:
    _require_exact_keys(value, {"capabilities"}, "permissions")
    sequence = _sequence(value.get("capabilities"), "permissions.capabilities")
    return RuntimeValidationPermissionSet(
        capabilities=frozenset(Capability(str(item)) for item in sequence)
    )


def _cell_from_mapping(value: Mapping[str, object]) -> RuntimeCellSpec:
    _require_exact_keys(
        value,
        {"lane", "pair_id", "model_seed", "batch_id", "arm_order"},
        "runtime cell",
    )
    return RuntimeCellSpec(
        lane=ValidationLane(_string(value.get("lane"), "lane")),
        pair_id=QWakeFPPairId(_string(value.get("pair_id"), "pair_id")),
        model_seed=_integer(value.get("model_seed"), "model_seed"),
        batch_id=_string(value.get("batch_id"), "batch_id"),
        arm_order=ArmOrder(_string(value.get("arm_order"), "arm_order")),
    )


def _permissions_for_arm(
    pair_id: QWakeFPPairId,
    arm_id: PairArmId,
) -> RuntimeValidationPermissionSet:
    capabilities = set(_BASE_ARM_CAPABILITIES)
    if arm_id is PairArmId.INSTRUMENTED:
        capabilities.add(Capability.COLLECT_A0)
        capabilities.add(Capability.RUN_COST_DOMINANCE_CHECK)
        if pair_id in {QWakeFPPairId.P1, QWakeFPPairId.P2}:
            capabilities.add(Capability.COLLECT_A1)
        if pair_id is QWakeFPPairId.P2:
            capabilities.add(Capability.COLLECT_A2)
    return RuntimeValidationPermissionSet(capabilities=frozenset(capabilities))


def _expected_disabled_capabilities(
    permissions: RuntimeValidationPermissionSet,
) -> tuple[Capability, ...]:
    return tuple(
        capability
        for capability in RUNTIME_EFFECT_AUDIT_CAPABILITIES
        if capability not in permissions.capabilities
    )


def _merge_disabled_audits(
    first: Sequence[DisabledCapabilityAudit],
    second: Sequence[DisabledCapabilityAudit],
) -> tuple[DisabledCapabilityAudit, ...]:
    return tuple(first) + tuple(second)


def _adapter_registry_sha256() -> str:
    records: list[dict[str, str]] = []
    for contract in QWAKE_FP_PRE_FREEZE_VALIDATION_REQUEST.adapters:
        module = importlib.import_module(contract.module_name)
        symbol = getattr(module, contract.symbol_name, None)
        if not callable(symbol):
            raise QWakeFPRuntimeError(
                f"runtime adapter is not callable: {contract.module_name}:{contract.symbol_name}"
            )
        records.append(
            {
                "adapter_id": contract.adapter_id.value,
                "module_name": contract.module_name,
                "symbol_name": contract.symbol_name,
                "required_capability": contract.required_capability.value,
            }
        )
    return _sha256_object(records)


def _verify_frozen_request(project_root: Path) -> str:
    request = project_root / REQUEST_RELATIVE
    sums = project_root / REQUEST_SUMS_RELATIVE
    if request.is_symlink() or not request.is_file():
        raise QWakeFPRuntimeError("frozen validation request is missing")
    if sums.is_symlink() or not sums.is_file():
        raise QWakeFPRuntimeError("frozen validation SHA256SUMS is missing")
    digest = hashlib.sha256(request.read_bytes()).hexdigest()
    expected_line = f"{digest}  request.json\n"
    if sums.read_text(encoding="utf-8") != expected_line:
        raise QWakeFPRuntimeError("frozen validation request registry differs")
    if request.read_text(encoding="utf-8") != (
        QWAKE_FP_PRE_FREEZE_VALIDATION_REQUEST.canonical_json()
    ):
        raise QWakeFPRuntimeError("frozen validation request differs from Python")
    return f"sha256:{digest}"


def _source_index_sha256(project_root: Path) -> str:
    listing = _run_git(project_root, "ls-files", "-s")
    return _sha256_text(listing + "\n")


def _require_clean_checkout(
    checkout: Path,
    *,
    expected_commit: str,
    label: str,
) -> None:
    if not (checkout / ".git").exists():
        raise QWakeFPRuntimeError(f"{label} checkout is missing: {checkout}")
    observed = _run_git(checkout, "rev-parse", "HEAD")
    if observed != expected_commit:
        raise QWakeFPRuntimeError(
            f"{label} commit differs: expected={expected_commit}, observed={observed}"
        )
    if _run_git(checkout, "status", "--porcelain"):
        raise QWakeFPRuntimeError(f"{label} worktree must be clean")


def _run_git(checkout: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(checkout), *arguments],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip()
        raise QWakeFPRuntimeError(
            f"git {' '.join(arguments)} failed: {message}"
        )
    return completed.stdout.strip()


def _load_json(path: Path) -> Mapping[str, object]:
    if path.is_symlink() or not path.is_file():
        raise QWakeFPRuntimeError(f"JSON path must be a regular file: {path}")
    try:
        payload = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_object_from_pairs,
            parse_constant=_reject_json_constant,
        )
    except (OSError, json.JSONDecodeError, QWakeFPRuntimeError) as error:
        raise QWakeFPRuntimeError(f"cannot read JSON object: {path}") from error
    return _mapping(payload, str(path))


def _object_from_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise QWakeFPRuntimeError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> object:
    raise QWakeFPRuntimeError(f"non-finite JSON constant is forbidden: {value}")


def _require_exact_keys(
    value: Mapping[str, object],
    expected: set[str],
    field_name: str,
) -> None:
    observed = set(value)
    if observed != expected:
        missing = ",".join(sorted(expected - observed)) or "none"
        extra = ",".join(sorted(observed - expected)) or "none"
        raise QWakeFPRuntimeError(
            f"{field_name} keys differ: missing={missing}; extra={extra}"
        )


def _mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise QWakeFPRuntimeError(f"{field_name} must be an object")
    if any(not isinstance(key, str) for key in value):
        raise QWakeFPRuntimeError(f"{field_name} contains a non-string key")
    return cast(Mapping[str, object], value)


def _sequence(value: object, field_name: str) -> Sequence[object]:
    if not isinstance(value, list | tuple):
        raise QWakeFPRuntimeError(f"{field_name} must be an array")
    return cast(Sequence[object], value)


def _string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise QWakeFPRuntimeError(f"{field_name} must be a non-empty string")
    return value


def _string_allow_empty(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise QWakeFPRuntimeError(f"{field_name} must be a string")
    return value


def _integer(value: object, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise QWakeFPRuntimeError(f"{field_name} must be an integer")
    return value


def _boolean(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise QWakeFPRuntimeError(f"{field_name} must be boolean")
    return value


def _require_commit(value: str, *, field_name: str) -> None:
    if not _COMMIT_PATTERN.fullmatch(value):
        raise QWakeFPRuntimeError(
            f"{field_name} must be a 40-character lowercase commit"
        )


def _require_sha256(value: str, *, field_name: str) -> None:
    if not _SHA256_PATTERN.fullmatch(value):
        raise QWakeFPRuntimeError(f"{field_name} must be sha256:<64 lowercase hex>")


def _require_utc(value: str, *, field_name: str) -> None:
    if not value.endswith("Z"):
        raise QWakeFPRuntimeError(f"{field_name} must end in Z")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise QWakeFPRuntimeError(f"{field_name} must be ISO-8601 UTC") from error
    offset = parsed.utcoffset()
    if offset is None or offset.total_seconds() != 0:
        raise QWakeFPRuntimeError(f"{field_name} must use UTC")


def _canonicalize(value: object) -> object:
    if isinstance(value, StrEnum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return _canonicalize(asdict(cast(Any, value)))
    if isinstance(value, Mapping):
        return {
            str(key): _canonicalize(item)
            for key, item in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, tuple | list | set | frozenset):
        items = [_canonicalize(item) for item in value]
        if isinstance(value, set | frozenset):
            return sorted(items, key=lambda item: json.dumps(item, sort_keys=True))
        return items
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, float) and not math.isfinite(value):
        raise QWakeFPRuntimeError("non-finite runtime value is forbidden")
    return value


def _canonical_json(value: object) -> str:
    return json.dumps(
        _canonicalize(value),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"


def _sha256_object(value: object) -> str:
    return _sha256_text(_canonical_json(value))


def _sha256_text(value: str) -> str:
    return f"sha256:{hashlib.sha256(value.encode('utf-8')).hexdigest()}"


def _sha256_bytes(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"
