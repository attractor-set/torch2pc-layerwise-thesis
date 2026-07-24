"""QW-4A pre-freeze validation contracts for the bounded QWake-FP pipeline.

This module freezes the engineering validation request and provides pure,
backend-neutral comparators for future matched CPU/ROCm smoke artifacts.  It
performs no model execution, tensor reads, device synchronization, filesystem
writes, subprocess calls, network access, or scientific campaign opening.
Runtime adapters remain unbound until a separate QW-4B authorization/evidence
slice.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, is_dataclass
from enum import StrEnum
from typing import Any, Final, cast

from torch2pc_thesis.stage3b_qwake_core import (
    Capability,
    DecisionCost,
    EdgeMeasurement,
    ObservationLevel,
)
from torch2pc_thesis.stage3b_qwake_fp_pipeline import (
    CostCategory,
    map_edge_measurement,
)
from torch2pc_thesis.stage3b_qwake_fp_spec import (
    PAIRED_VALIDATION_REGISTRY,
    QWAKE_FP_SPECIAL_CASE_CONTRACT,
    QWakeFPPairId,
)


class QWakeFPValidationError(ValueError):
    """Raised when a QW-4A request or validation artifact violates the contract."""


class ValidationLane(StrEnum):
    """Engineering and canonical lanes required before image freeze."""

    CPU_FLOAT64_ENGINEERING = "cpu_float64_engineering"
    ROCM_FLOAT32_CANONICAL = "rocm_float32_canonical"


class ValidationGateId(StrEnum):
    """Closed set of pre-freeze gates."""

    STATIC_AND_UNIT = "static_and_unit"
    MANIFEST_INTEGRITY = "manifest_integrity"
    RECEIPT_CHAIN = "receipt_chain"
    PERMISSION_NEGATIVE = "permission_negative"
    P0_MATCHED = "P0_matched"
    P1_MATCHED = "P1_matched"
    P2_MATCHED = "P2_matched"
    NESTED_OBSERVATIONS = "nested_observations"
    ORACLE_ISOLATION = "oracle_isolation"
    COST_ACCOUNTING = "cost_accounting"
    CPU_SMOKE = "cpu_smoke"
    ROCM_SMOKE = "rocm_smoke"


class RuntimeAdapterId(StrEnum):
    """Finite runtime adapter boundary frozen before any adapter is bound."""

    CANONICAL_EXECUTOR = "canonical_executor"
    COLLECT_A0 = "collect_A0"
    COLLECT_A1 = "collect_A1"
    COLLECT_A2 = "collect_A2"
    RUN_REGISTERED_ANALYTICS = "run_registered_analytics"
    COMPUTE_POST_ACTION_ORACLE = "compute_post_action_oracle"
    RECORD_EDGE_COSTS = "record_edge_costs"


class AdapterBindingStatus(StrEnum):
    """Whether one adapter is already available for runtime invocation."""

    EXISTING_LOADER_UNAUTHORIZED = "existing_loader_runtime_unauthorized"
    UNBOUND = "unbound_runtime_adapter"


class PairArmId(StrEnum):
    """Matched pair arm identity."""

    REFERENCE = "reference"
    INSTRUMENTED = "instrumented"


_PAIR_BY_ID: Final = {item.pair_id: item for item in PAIRED_VALIDATION_REGISTRY}
_EXPECTED_LEVELS: Final[Mapping[QWakeFPPairId, tuple[ObservationLevel, ...]]] = {
    QWakeFPPairId.P0: (ObservationLevel.A0,),
    QWakeFPPairId.P1: (ObservationLevel.A0, ObservationLevel.A1),
    QWakeFPPairId.P2: (
        ObservationLevel.A0,
        ObservationLevel.A1,
        ObservationLevel.A2,
    ),
}
_FORBIDDEN_ORACLE_TOKENS: Final[tuple[str, ...]] = (
    "oracle",
    "t_star",
    "reference_future",
    "sufficiency_margin",
)


@dataclass(frozen=True)
class RuntimeAdapterContract:
    """One future runtime adapter and its current binding state."""

    adapter_id: RuntimeAdapterId
    module_name: str
    symbol_name: str
    lanes: tuple[ValidationLane, ...]
    binding_status: AdapterBindingStatus
    required_capability: Capability

    def __post_init__(self) -> None:
        if not self.module_name.strip() or not self.symbol_name.strip():
            raise QWakeFPValidationError("adapter module and symbol cannot be empty")
        if not self.lanes:
            raise QWakeFPValidationError("adapter must admit at least one lane")
        if len(self.lanes) != len(set(self.lanes)):
            raise QWakeFPValidationError("adapter lanes cannot be duplicated")


@dataclass(frozen=True)
class QWakeFPPreFreezeValidationRequest:
    """Immutable QW-4A request; execution remains fail-closed."""

    schema_version: int
    request_id: str
    status: str
    special_case_contract_id: str
    special_case_contract_sha256: str
    required_lanes: tuple[ValidationLane, ...]
    pair_ids: tuple[QWakeFPPairId, ...]
    required_gates: tuple[ValidationGateId, ...]
    equality_fields: tuple[str, ...]
    measurement_fields: tuple[str, ...]
    disabled_capability_audit_fields: tuple[str, ...]
    adapters: tuple[RuntimeAdapterContract, ...]
    scientific_execution_open: bool
    runtime_authorization_issued: bool
    evidence_generated: bool
    feature_collection_permitted: bool
    oracle_label_generation_open: bool
    test_dataset_access: bool
    image_freeze_permitted: bool

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise QWakeFPValidationError("QW-4A schema_version must be 1")
        if self.request_id != "stage3b-qwake-fp-pre-freeze-validation-v1":
            raise QWakeFPValidationError("unexpected QW-4A request id")
        if self.status != "request_frozen_execution_closed":
            raise QWakeFPValidationError("QW-4A request must keep execution closed")
        if self.special_case_contract_id != QWAKE_FP_SPECIAL_CASE_CONTRACT.contract_id:
            raise QWakeFPValidationError("QW-4A contract id differs from QW-2")
        _require_sha256(
            self.special_case_contract_sha256,
            field_name="special_case_contract_sha256",
        )
        if self.required_lanes != tuple(ValidationLane):
            raise QWakeFPValidationError("QW-4A lanes must be CPU then ROCm")
        if self.pair_ids != tuple(QWakeFPPairId):
            raise QWakeFPValidationError("QW-4A pairs must be exactly P0, P1, P2")
        if self.required_gates != tuple(ValidationGateId):
            raise QWakeFPValidationError("QW-4A gates must match the closed registry")
        expected_equalities = PAIRED_VALIDATION_REGISTRY[0].required_equalities
        expected_measurements = PAIRED_VALIDATION_REGISTRY[0].measured_outputs
        if self.equality_fields != expected_equalities:
            raise QWakeFPValidationError("QW-4A equality fields differ from QW-2")
        if self.measurement_fields != expected_measurements:
            raise QWakeFPValidationError("QW-4A measurements differ from QW-2")
        if tuple(item.adapter_id for item in self.adapters) != tuple(RuntimeAdapterId):
            raise QWakeFPValidationError("QW-4A adapter registry must be complete")
        if self.adapters[0].binding_status is not (
            AdapterBindingStatus.EXISTING_LOADER_UNAUTHORIZED
        ):
            raise QWakeFPValidationError("canonical loader must remain unauthorized")
        if any(
            item.binding_status is not AdapterBindingStatus.UNBOUND
            for item in self.adapters[1:]
        ):
            raise QWakeFPValidationError("QW-4A live adapters must remain unbound")
        closed = (
            self.scientific_execution_open,
            self.runtime_authorization_issued,
            self.evidence_generated,
            self.feature_collection_permitted,
            self.oracle_label_generation_open,
            self.test_dataset_access,
            self.image_freeze_permitted,
        )
        if any(closed):
            raise QWakeFPValidationError("QW-4A cannot open execution or image freeze")

    def to_dict(self) -> dict[str, object]:
        return cast(dict[str, object], _canonicalize(asdict(self)))

    def canonical_json(self) -> str:
        return _canonical_json(self)

    def sha256(self) -> str:
        return _sha256_text(self.canonical_json())


@dataclass(frozen=True)
class EffectAudit:
    """Observed effect counters for one component or matched arm."""

    invocation_count: int = 0
    tensor_read_count: int = 0
    temporary_allocation_count: int = 0
    synchronization_count: int = 0
    d2h_bytes: int = 0
    trace_bytes: int = 0
    output_count: int = 0

    def __post_init__(self) -> None:
        for name, value in asdict(self).items():
            if value < 0:
                raise QWakeFPValidationError(f"{name} must be non-negative")

    @property
    def all_zero(self) -> bool:
        return all(value == 0 for value in asdict(self).values())


@dataclass(frozen=True)
class DisabledCapabilityAudit:
    """Proof obligation that one disabled capability produced no effects."""

    capability: Capability
    enabled: bool
    effects: EffectAudit

    @property
    def passed(self) -> bool:
        return not self.enabled and self.effects.all_zero


@dataclass(frozen=True)
class PairArmRecord:
    """One immutable arm artifact produced by a future runtime adapter."""

    pair_id: QWakeFPPairId
    arm_id: PairArmId
    arm_label: str
    lane: ValidationLane
    model_seed: int
    batch_id: str
    initial_state_sha256: str
    rng_state_before_sha256: str
    equality_hashes: tuple[tuple[str, str], ...]
    observation_payload_sha256s: tuple[tuple[ObservationLevel, str], ...]
    observer_measurement: EdgeMeasurement
    observer_effects: EffectAudit

    def __post_init__(self) -> None:
        pair = _PAIR_BY_ID[self.pair_id]
        expected_label = (
            pair.reference if self.arm_id is PairArmId.REFERENCE else pair.instrumented
        )
        if self.arm_label != expected_label:
            raise QWakeFPValidationError("pair arm label differs from QW-2")
        if self.model_seed < 0 or not self.batch_id.strip():
            raise QWakeFPValidationError("pair seed and batch identity are invalid")
        _require_sha256(self.initial_state_sha256, field_name="initial_state_sha256")
        _require_sha256(
            self.rng_state_before_sha256,
            field_name="rng_state_before_sha256",
        )
        equality_names = tuple(name for name, _ in self.equality_hashes)
        if equality_names != pair.required_equalities:
            raise QWakeFPValidationError("pair equality fields differ from QW-2")
        for name, digest in self.equality_hashes:
            _require_sha256(digest, field_name=name)
        levels = tuple(level for level, _ in self.observation_payload_sha256s)
        expected_levels: tuple[ObservationLevel, ...] = ()
        if self.arm_id is PairArmId.INSTRUMENTED:
            expected_levels = _EXPECTED_LEVELS[self.pair_id]
        if levels != expected_levels:
            raise QWakeFPValidationError("pair observation levels are not exact")
        for level, digest in self.observation_payload_sha256s:
            _require_sha256(digest, field_name=f"{level.value}_payload_sha256")
        if self.arm_id is PairArmId.REFERENCE:
            if not self.observer_effects.all_zero:
                raise QWakeFPValidationError("B0 reference cannot contain observer effects")
            if self.observer_measurement != EdgeMeasurement():
                raise QWakeFPValidationError("B0 reference observer cost must be zero")
        else:
            if self.observer_effects.invocation_count < 1:
                raise QWakeFPValidationError("instrumented arm must invoke the observer")
            if self.observer_effects.output_count < len(expected_levels):
                raise QWakeFPValidationError("instrumented arm must emit all levels")
            if self.pair_id is QWakeFPPairId.P0 and (
                self.observer_effects.tensor_read_count != 0
                or self.observer_effects.temporary_allocation_count != 0
                or self.observer_effects.synchronization_count != 0
                or self.observer_effects.d2h_bytes != 0
            ):
                raise QWakeFPValidationError("A0 must remain structural and tensor-free")

    def equality_mapping(self) -> dict[str, str]:
        return dict(self.equality_hashes)

    def observation_mapping(self) -> dict[ObservationLevel, str]:
        return dict(self.observation_payload_sha256s)


@dataclass(frozen=True)
class MatchedPairValidation:
    """Pure comparison result for one B0 versus B0+AX pair."""

    pair_id: QWakeFPPairId
    lane: ValidationLane
    equality_mismatches: tuple[str, ...]
    initial_state_equal: bool
    rng_state_before_equal: bool
    observer_cost: DecisionCost
    passed: bool


@dataclass(frozen=True)
class OracleIsolationRecord:
    """Post-action ordering and access audit for oracle generation."""

    pre_action_field_names: tuple[str, ...]
    action_completed_ordinal: int
    oracle_created_ordinal: int
    oracle_read_before_action_count: int
    pre_action_oracle_access_count: int

    def __post_init__(self) -> None:
        if self.action_completed_ordinal < 0 or self.oracle_created_ordinal < 0:
            raise QWakeFPValidationError("oracle ordinals must be non-negative")
        if self.oracle_read_before_action_count < 0:
            raise QWakeFPValidationError("oracle read count must be non-negative")
        if self.pre_action_oracle_access_count < 0:
            raise QWakeFPValidationError("oracle access count must be non-negative")

    @property
    def passed(self) -> bool:
        fields_clean = all(
            not any(token in field for token in _FORBIDDEN_ORACLE_TOKENS)
            for field in self.pre_action_field_names
        )
        return (
            fields_clean
            and self.oracle_created_ordinal > self.action_completed_ordinal
            and self.oracle_read_before_action_count == 0
            and self.pre_action_oracle_access_count == 0
        )


@dataclass(frozen=True)
class PreFreezeValidationReport:
    """Engineering report required before QW-5 image freeze can be proposed."""

    schema_version: int
    request_sha256: str
    pair_results: tuple[MatchedPairValidation, ...]
    nested_observations_passed: bool
    disabled_capability_audits: tuple[DisabledCapabilityAudit, ...]
    oracle_isolation_passed: bool
    manifest_integrity_passed: bool
    receipt_chain_passed: bool
    static_and_unit_passed: bool
    cpu_smoke_passed: bool
    rocm_smoke_passed: bool
    scientific_evidence: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise QWakeFPValidationError("validation report schema_version must be 1")
        _require_sha256(self.request_sha256, field_name="request_sha256")
        if tuple(item.pair_id for item in self.pair_results) != tuple(QWakeFPPairId):
            raise QWakeFPValidationError("report must contain P0, P1, P2 in order")
        if self.scientific_evidence:
            raise QWakeFPValidationError("QW-4 report is engineering evidence only")

    @property
    def image_freeze_eligible(self) -> bool:
        return (
            all(item.passed for item in self.pair_results)
            and self.nested_observations_passed
            and all(item.passed for item in self.disabled_capability_audits)
            and self.oracle_isolation_passed
            and self.manifest_integrity_passed
            and self.receipt_chain_passed
            and self.static_and_unit_passed
            and self.cpu_smoke_passed
            and self.rocm_smoke_passed
        )


def build_pre_freeze_validation_request() -> QWakeFPPreFreezeValidationRequest:
    """Build the canonical execution-closed QW-4A request."""

    lanes = tuple(ValidationLane)
    adapters = (
        RuntimeAdapterContract(
            adapter_id=RuntimeAdapterId.CANONICAL_EXECUTOR,
            module_name="torch2pc_thesis.pc_methods",
            symbol_name="load_pc_infer",
            lanes=lanes,
            binding_status=AdapterBindingStatus.EXISTING_LOADER_UNAUTHORIZED,
            required_capability=Capability.EXECUTE_FIXEDPRED,
        ),
        RuntimeAdapterContract(
            adapter_id=RuntimeAdapterId.COLLECT_A0,
            module_name="torch2pc_thesis.stage3b_qwake_fp_runtime_adapter",
            symbol_name="collect_A0",
            lanes=lanes,
            binding_status=AdapterBindingStatus.UNBOUND,
            required_capability=Capability.COLLECT_A0,
        ),
        RuntimeAdapterContract(
            adapter_id=RuntimeAdapterId.COLLECT_A1,
            module_name="torch2pc_thesis.stage3b_qwake_fp_runtime_adapter",
            symbol_name="collect_A1",
            lanes=lanes,
            binding_status=AdapterBindingStatus.UNBOUND,
            required_capability=Capability.COLLECT_A1,
        ),
        RuntimeAdapterContract(
            adapter_id=RuntimeAdapterId.COLLECT_A2,
            module_name="torch2pc_thesis.stage3b_qwake_fp_runtime_adapter",
            symbol_name="collect_A2",
            lanes=lanes,
            binding_status=AdapterBindingStatus.UNBOUND,
            required_capability=Capability.COLLECT_A2,
        ),
        RuntimeAdapterContract(
            adapter_id=RuntimeAdapterId.RUN_REGISTERED_ANALYTICS,
            module_name="torch2pc_thesis.stage3b_qwake_fp_runtime_adapter",
            symbol_name="run_registered_analytics",
            lanes=lanes,
            binding_status=AdapterBindingStatus.UNBOUND,
            required_capability=Capability.RUN_ANALYTIC_EXACT,
        ),
        RuntimeAdapterContract(
            adapter_id=RuntimeAdapterId.COMPUTE_POST_ACTION_ORACLE,
            module_name="torch2pc_thesis.stage3b_qwake_fp_runtime_adapter",
            symbol_name="compute_post_action_oracle",
            lanes=lanes,
            binding_status=AdapterBindingStatus.UNBOUND,
            required_capability=Capability.COMPUTE_POST_ACTION_ORACLE,
        ),
        RuntimeAdapterContract(
            adapter_id=RuntimeAdapterId.RECORD_EDGE_COSTS,
            module_name="torch2pc_thesis.stage3b_qwake_fp_runtime_adapter",
            symbol_name="record_edge_costs",
            lanes=lanes,
            binding_status=AdapterBindingStatus.UNBOUND,
            required_capability=Capability.RUN_COST_DOMINANCE_CHECK,
        ),
    )
    return QWakeFPPreFreezeValidationRequest(
        schema_version=1,
        request_id="stage3b-qwake-fp-pre-freeze-validation-v1",
        status="request_frozen_execution_closed",
        special_case_contract_id=QWAKE_FP_SPECIAL_CASE_CONTRACT.contract_id,
        special_case_contract_sha256=(
            f"sha256:{QWAKE_FP_SPECIAL_CASE_CONTRACT.sha256()}"
        ),
        required_lanes=lanes,
        pair_ids=tuple(QWakeFPPairId),
        required_gates=tuple(ValidationGateId),
        equality_fields=PAIRED_VALIDATION_REGISTRY[0].required_equalities,
        measurement_fields=PAIRED_VALIDATION_REGISTRY[0].measured_outputs,
        disabled_capability_audit_fields=tuple(EffectAudit.__dataclass_fields__),
        adapters=adapters,
        scientific_execution_open=False,
        runtime_authorization_issued=False,
        evidence_generated=False,
        feature_collection_permitted=False,
        oracle_label_generation_open=False,
        test_dataset_access=False,
        image_freeze_permitted=False,
    )


def validate_request_payload(payload: Mapping[str, object]) -> None:
    """Fail closed unless a decoded request equals the canonical QW-4A request."""

    expected = build_pre_freeze_validation_request().to_dict()
    observed = cast(dict[str, object], _canonicalize(dict(payload)))
    if observed != expected:
        raise QWakeFPValidationError("validation request differs from canonical QW-4A")


def compare_matched_pair(
    reference: PairArmRecord,
    instrumented: PairArmRecord,
) -> MatchedPairValidation:
    """Compare one B0 arm with its exact cumulative observer arm."""

    if reference.arm_id is not PairArmId.REFERENCE:
        raise QWakeFPValidationError("first arm must be the B0 reference")
    if instrumented.arm_id is not PairArmId.INSTRUMENTED:
        raise QWakeFPValidationError("second arm must be instrumented")
    identity = (
        reference.pair_id,
        reference.lane,
        reference.model_seed,
        reference.batch_id,
    )
    observed_identity = (
        instrumented.pair_id,
        instrumented.lane,
        instrumented.model_seed,
        instrumented.batch_id,
    )
    if identity != observed_identity:
        raise QWakeFPValidationError("matched arms do not share cell identity")
    reference_hashes = reference.equality_mapping()
    instrumented_hashes = instrumented.equality_mapping()
    mismatches = tuple(
        name
        for name in _PAIR_BY_ID[reference.pair_id].required_equalities
        if reference_hashes[name] != instrumented_hashes[name]
    )
    initial_state_equal = (
        reference.initial_state_sha256 == instrumented.initial_state_sha256
    )
    rng_state_before_equal = (
        reference.rng_state_before_sha256 == instrumented.rng_state_before_sha256
    )
    observer_cost = validate_observer_cost_mapping(
        instrumented.observer_measurement
    )
    return MatchedPairValidation(
        pair_id=reference.pair_id,
        lane=reference.lane,
        equality_mismatches=mismatches,
        initial_state_equal=initial_state_equal,
        rng_state_before_equal=rng_state_before_equal,
        observer_cost=observer_cost,
        passed=(
            not mismatches
            and initial_state_equal
            and rng_state_before_equal
        ),
    )


def validate_nested_observation_hashes(
    p0: PairArmRecord,
    p1: PairArmRecord,
    p2: PairArmRecord,
) -> bool:
    """Verify that higher levels preserve already acquired observations."""

    arms = (p0, p1, p2)
    if tuple(item.pair_id for item in arms) != tuple(QWakeFPPairId):
        raise QWakeFPValidationError("nested validation requires P0, P1, P2")
    if any(item.arm_id is not PairArmId.INSTRUMENTED for item in arms):
        raise QWakeFPValidationError("nested validation requires instrumented arms")
    cell_identity = {
        (item.lane, item.model_seed, item.batch_id, item.initial_state_sha256)
        for item in arms
    }
    if len(cell_identity) != 1:
        raise QWakeFPValidationError("nested arms do not share one matched cell")
    maps = tuple(item.observation_mapping() for item in arms)
    return (
        maps[0][ObservationLevel.A0]
        == maps[1][ObservationLevel.A0]
        == maps[2][ObservationLevel.A0]
        and maps[1][ObservationLevel.A1] == maps[2][ObservationLevel.A1]
    )


def validate_disabled_capability(audit: DisabledCapabilityAudit) -> None:
    """Reject any disabled capability that produced a runtime effect."""

    if not audit.passed:
        raise QWakeFPValidationError(
            f"disabled capability produced effects: {audit.capability.value}"
        )


def validate_oracle_isolation(record: OracleIsolationRecord) -> None:
    """Reject oracle creation or access before canonical action completion."""

    if not record.passed:
        raise QWakeFPValidationError("post-action oracle isolation failed")


def validate_observer_cost_mapping(measurement: EdgeMeasurement) -> DecisionCost:
    """Map observer host time once and keep device time auxiliary."""

    mapped = map_edge_measurement(measurement, CostCategory.OBSERVER)
    if mapped.observer_ns != measurement.host_time_ns:
        raise QWakeFPValidationError("observer host time mapping is inconsistent")
    if mapped.total_time_ns != measurement.host_time_ns:
        raise QWakeFPValidationError("device time was double-counted")
    if mapped.memory_bytes != measurement.temporary_memory_bytes:
        raise QWakeFPValidationError("observer memory mapping is inconsistent")
    return mapped


def build_pre_freeze_report(
    *,
    pair_results: Sequence[MatchedPairValidation],
    nested_observations_passed: bool,
    disabled_capability_audits: Sequence[DisabledCapabilityAudit],
    oracle_isolation_passed: bool,
    manifest_integrity_passed: bool,
    receipt_chain_passed: bool,
    static_and_unit_passed: bool,
    cpu_smoke_passed: bool,
    rocm_smoke_passed: bool,
) -> PreFreezeValidationReport:
    """Build a deterministic engineering report from already produced artifacts."""

    return PreFreezeValidationReport(
        schema_version=1,
        request_sha256=build_pre_freeze_validation_request().sha256(),
        pair_results=tuple(pair_results),
        nested_observations_passed=nested_observations_passed,
        disabled_capability_audits=tuple(disabled_capability_audits),
        oracle_isolation_passed=oracle_isolation_passed,
        manifest_integrity_passed=manifest_integrity_passed,
        receipt_chain_passed=receipt_chain_passed,
        static_and_unit_passed=static_and_unit_passed,
        cpu_smoke_passed=cpu_smoke_passed,
        rocm_smoke_passed=rocm_smoke_passed,
    )


def _require_sha256(value: str, *, field_name: str) -> None:
    if len(value) != 71 or not value.startswith("sha256:"):
        raise QWakeFPValidationError(f"{field_name} must be sha256:<64 hex>")
    try:
        int(value[7:], 16)
    except ValueError as error:
        raise QWakeFPValidationError(
            f"{field_name} must be sha256:<64 hex>"
        ) from error
    if value[7:] != value[7:].lower():
        raise QWakeFPValidationError(f"{field_name} must use lowercase hex")


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
    if isinstance(value, tuple | list):
        return [_canonicalize(item) for item in value]
    return value


def _canonical_json(value: object) -> str:
    return json.dumps(
        _canonicalize(value),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"


def _sha256_text(value: str) -> str:
    return f"sha256:{hashlib.sha256(value.encode('utf-8')).hexdigest()}"


QWAKE_FP_PRE_FREEZE_VALIDATION_REQUEST: Final = (
    build_pre_freeze_validation_request()
)
