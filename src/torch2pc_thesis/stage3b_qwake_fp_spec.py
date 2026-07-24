"""Frozen QW-2 contract for the bounded QWake-FP validation case.

The module is deliberately pure Python.  It binds the general QWake QW-1
contracts to one finite FixedPred special case without importing PyTorch,
Torch2PC, filesystem, subprocess, or GPU APIs, and without opening scientific
execution.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Final, cast

from torch2pc_thesis.stage3b_qwake_core import (
    ROLE_CAPABILITY_ALLOWLIST,
    ROLE_REQUIRED_RECEIPTS,
    AnalyticClass,
    CampaignRole,
    ObservationLevel,
)


class QWakeFPSpecError(ValueError):
    """Raised when the frozen QWake-FP special-case contract is inconsistent."""


class QWakeFPMethod(StrEnum):
    """Single method admitted to the bounded QWake-FP case."""

    FIXEDPRED = "fixedpred"


class QWakeFPExecutor(StrEnum):
    """Canonical implementation and fail-closed fallback."""

    STAGE2_BASELINE = "stage2_baseline"


class QWakeFPArchitecture(StrEnum):
    """Single sequential architecture in the mandatory validation scope."""

    LENET_CLASSIC = "lenet_classic"


class QWakeFPHorizonRule(StrEnum):
    """Rule defining the finite reference horizon."""

    REGISTERED_INFERENCE_STEPS = "registered_inference_steps"


class QWakeFPResponseComponent(StrEnum):
    """Components of the frozen task-relative endpoint response."""

    NAMED_PARAMETER_GRADIENTS = "named_parameter_gradients"
    ENDPOINT_BELIEFS = "endpoint_beliefs"
    ENDPOINT_LOSS = "endpoint_loss"


class QWakeFPAnalyticId(StrEnum):
    """Closed pre-action analytic registry for the bounded case."""

    ROSENBAUM_WAVEFRONT_STATUS_V1 = "rosenbaum_wavefront_status_v1"
    RESIDUAL_PERSISTENCE_V1 = "residual_persistence_v1"
    COST_DOMINANCE_V1 = "cost_dominance_v1"


class QWakeFPBaselineId(StrEnum):
    """Closed baseline registry used by offline C2 and confirmatory analysis."""

    B0_FULL_CANONICAL_SUFFIX = "B0_full_canonical_suffix"
    B1_FIXED_PREFIX = "B1_fixed_prefix"
    B2_RESIDUAL_THRESHOLD = "B2_registered_prediction_error_or_residual_threshold"
    B3_A0_ONLY = "B3_A0_only"
    B4_FIXED_OBSERVATION_CASCADE = "B4_fixed_A0_A1_A2_cascade"
    B5_FIXED_ANALYTIC_REGISTRY = "B5_fixed_analytic_registry"
    B6_FROZEN_QWAKE_FP = "B6_frozen_QWake_FP"
    B7_POST_ACTION_ORACLE = "B7_post_action_oracle_frontier"


class QWakeFPPairId(StrEnum):
    """Pre-freeze matched observer-validation pairs."""

    P0 = "P0"
    P1 = "P1"
    P2 = "P2"


@dataclass(frozen=True)
class ObservationSpec:
    """One cumulative deployable observation level."""

    level: ObservationLevel
    cumulative_fields: tuple[str, ...]
    tensor_value_reads: bool
    device_side_only: bool
    deterministic_sample_prefix_sizes: tuple[int, ...] = ()
    sample_index_rule: str | None = None

    def __post_init__(self) -> None:
        if not self.cumulative_fields:
            raise QWakeFPSpecError("observation fields cannot be empty")
        if len(self.cumulative_fields) != len(set(self.cumulative_fields)):
            raise QWakeFPSpecError("observation fields must be unique")
        if self.level is ObservationLevel.A0:
            if self.tensor_value_reads or self.device_side_only:
                raise QWakeFPSpecError("A0 must remain structural")
            if self.deterministic_sample_prefix_sizes or self.sample_index_rule:
                raise QWakeFPSpecError("A0 cannot define tensor sampling")
        if self.level is ObservationLevel.A1:
            if not self.tensor_value_reads or not self.device_side_only:
                raise QWakeFPSpecError("A1 must be device-side reductions")
            if self.deterministic_sample_prefix_sizes or self.sample_index_rule:
                raise QWakeFPSpecError("A1 cannot define local sampling")
        if self.level is ObservationLevel.A2:
            if not self.tensor_value_reads or not self.device_side_only:
                raise QWakeFPSpecError("A2 must be device-side local reductions")
            if not self.deterministic_sample_prefix_sizes or not self.sample_index_rule:
                raise QWakeFPSpecError("A2 requires a deterministic sample rule")
            if tuple(sorted(self.deterministic_sample_prefix_sizes)) != (
                self.deterministic_sample_prefix_sizes
            ):
                raise QWakeFPSpecError("A2 sample prefixes must be sorted")
            if any(size <= 0 for size in self.deterministic_sample_prefix_sizes):
                raise QWakeFPSpecError("A2 sample prefixes must be positive")


@dataclass(frozen=True)
class AnalyticSpec:
    """One registered analytic step with no implicit acceptance authority."""

    analytic_id: QWakeFPAnalyticId
    analytic_class: AnalyticClass
    minimum_observation: ObservationLevel
    output_fields: tuple[str, ...]
    may_directly_accept: bool
    role: str

    def __post_init__(self) -> None:
        if not self.output_fields:
            raise QWakeFPSpecError("analytic output fields cannot be empty")
        if self.may_directly_accept:
            raise QWakeFPSpecError(
                "QW-2 analytics cannot bypass frozen risk admission"
            )
        if not self.role.strip():
            raise QWakeFPSpecError("analytic role cannot be empty")


@dataclass(frozen=True)
class PairedValidationSpec:
    """One matched B0 versus instrumented observer contract."""

    pair_id: QWakeFPPairId
    reference: str
    instrumented: str
    cumulative_level: ObservationLevel
    required_equalities: tuple[str, ...]
    measured_outputs: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.reference != "B0":
            raise QWakeFPSpecError("paired reference must remain B0")
        if not self.required_equalities or not self.measured_outputs:
            raise QWakeFPSpecError("paired validation fields cannot be empty")


@dataclass(frozen=True)
class ThresholdProfile:
    """Frozen EX-IF0 numerical sufficiency profile."""

    lane: str
    max_abs: float
    max_relative_l2: float
    min_cosine: float
    zero_atol: float

    def __post_init__(self) -> None:
        if self.lane != "rocm_float32":
            raise QWakeFPSpecError("canonical threshold lane must be rocm_float32")
        if not 0 < self.max_abs < 1:
            raise QWakeFPSpecError("max_abs must be in (0, 1)")
        if not 0 < self.max_relative_l2 < 1:
            raise QWakeFPSpecError("max_relative_l2 must be in (0, 1)")
        if not 0 < self.min_cosine <= 1:
            raise QWakeFPSpecError("min_cosine must be in (0, 1]")
        if not 0 < self.zero_atol < self.max_abs:
            raise QWakeFPSpecError("zero_atol must be positive and below max_abs")


@dataclass(frozen=True)
class CostMappingSpec:
    """Non-overlapping mapping from raw edge measurements to decision costs."""

    raw_fields: tuple[str, ...]
    exclusive_time_categories: tuple[str, ...]
    primary_time_basis: str
    device_time_semantics: str
    memory_semantics: str
    d2h_and_trace_semantics: str
    selection_order: tuple[str, ...]

    def __post_init__(self) -> None:
        if len(self.exclusive_time_categories) != len(
            set(self.exclusive_time_categories)
        ):
            raise QWakeFPSpecError("time categories must be mutually exclusive")
        if self.selection_order != ("safety", "coverage", "cost"):
            raise QWakeFPSpecError("selection order must be safety, coverage, cost")


@dataclass(frozen=True)
class QWakeFPSpecialCaseContract:
    """Complete immutable QW-2 binding of QWake to the FixedPred case."""

    schema_version: int
    contract_id: str
    status: str
    method: QWakeFPMethod
    eta: float
    executor: QWakeFPExecutor
    architecture: QWakeFPArchitecture
    horizon_rule: QWakeFPHorizonRule
    decision_epoch: str
    snapshot_zero_semantics: str
    response_components: tuple[QWakeFPResponseComponent, ...]
    primary_defect: str
    sufficiency_rule: str
    stable_sufficiency_rule: str
    threshold_profile: ThresholdProfile
    observations: tuple[ObservationSpec, ...]
    analytics: tuple[AnalyticSpec, ...]
    cost_mapping: CostMappingSpec
    baselines: tuple[QWakeFPBaselineId, ...]
    paired_validation: tuple[PairedValidationSpec, ...]
    role_capabilities: tuple[tuple[str, tuple[str, ...]], ...]
    role_receipts: tuple[tuple[str, tuple[str, ...]], ...]
    scientific_execution_open: bool
    oracle_label_generation_open: bool
    feature_collection_permitted: bool
    policy_activation_permitted: bool
    test_dataset_access: bool
    generalization_claim: bool

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise QWakeFPSpecError("QW-2 schema_version must be 1")
        if self.contract_id != "stage3b-qwake-fp-special-case-v1":
            raise QWakeFPSpecError("unexpected QW-2 contract id")
        if self.status != "spec_frozen_execution_closed":
            raise QWakeFPSpecError("QW-2 status must keep execution closed")
        if self.method is not QWakeFPMethod.FIXEDPRED:
            raise QWakeFPSpecError("bounded QWake-FP admits FixedPred only")
        if self.eta != 1.0:
            raise QWakeFPSpecError("bounded QWake-FP requires eta=1")
        if self.executor is not QWakeFPExecutor.STAGE2_BASELINE:
            raise QWakeFPSpecError("canonical executor must remain stage2_baseline")
        if self.architecture is not QWakeFPArchitecture.LENET_CLASSIC:
            raise QWakeFPSpecError("mandatory architecture must remain lenet_classic")
        if tuple(spec.level for spec in self.observations) != tuple(ObservationLevel):
            raise QWakeFPSpecError("observation order must be exactly A0, A1, A2")
        previous: set[str] = set()
        for spec in self.observations:
            current = set(spec.cumulative_fields)
            if not previous.issubset(current):
                raise QWakeFPSpecError("observations must be cumulative and nested")
            previous = current
        forbidden_observation_tokens = {
            "oracle",
            "t_star",
            "reference_future",
            "sufficiency_margin",
        }
        for spec in self.observations:
            for field_name in spec.cumulative_fields:
                if any(token in field_name for token in forbidden_observation_tokens):
                    raise QWakeFPSpecError("oracle data cannot enter observations")
        if len(self.analytics) != len({item.analytic_id for item in self.analytics}):
            raise QWakeFPSpecError("analytic registry must be unique")
        if tuple(self.baselines) != tuple(QWakeFPBaselineId):
            raise QWakeFPSpecError("baseline registry must be complete and ordered")
        if tuple(item.pair_id for item in self.paired_validation) != tuple(
            QWakeFPPairId
        ):
            raise QWakeFPSpecError("paired validation must be exactly P0, P1, P2")
        closed_gates = (
            self.scientific_execution_open,
            self.oracle_label_generation_open,
            self.feature_collection_permitted,
            self.policy_activation_permitted,
            self.test_dataset_access,
            self.generalization_claim,
        )
        if any(closed_gates):
            raise QWakeFPSpecError("QW-2 cannot open execution or claims")
        expected_capabilities = _serialize_role_capabilities()
        expected_receipts = _serialize_role_receipts()
        if self.role_capabilities != expected_capabilities:
            raise QWakeFPSpecError("role capability mapping differs from QW-1")
        if self.role_receipts != expected_receipts:
            raise QWakeFPSpecError("role receipt mapping differs from QW-1")

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-safe canonical representation."""

        return cast(dict[str, object], _canonicalize(asdict(self)))

    def canonical_json(self) -> str:
        """Return stable pretty JSON used by the frozen artifact."""

        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ) + "\n"

    def sha256(self) -> str:
        """Return the digest of the canonical JSON bytes."""

        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


A0_FIELDS: Final[tuple[str, ...]] = (
    "snapshot_id",
    "compute_step",
    "reference_horizon_k_ref",
    "remaining_sweeps",
    "registered_layer_order",
    "registered_block_order",
    "acquired_analytic_ids",
    "diagnostic_budget_remaining_ns",
)

A1_FIELDS: Final[tuple[str, ...]] = A0_FIELDS + (
    "global_prediction_error_l2_sq",
    "global_state_delta_l2_sq",
    "per_layer_prediction_error_l2_sq",
    "per_layer_state_delta_l2_sq",
    "per_layer_prediction_error_max_abs",
    "per_layer_state_delta_max_abs",
)

A2_FIELDS: Final[tuple[str, ...]] = A1_FIELDS + (
    "sample_prefix_prediction_error_l2_sq",
    "sample_prefix_state_delta_l2_sq",
    "sample_prefix_belief_l2_sq",
    "sample_prefix_prediction_error_max_abs",
    "sample_prefix_state_delta_max_abs",
    "sample_prefix_belief_max_abs",
)

OBSERVATION_REGISTRY: Final[tuple[ObservationSpec, ...]] = (
    ObservationSpec(
        level=ObservationLevel.A0,
        cumulative_fields=A0_FIELDS,
        tensor_value_reads=False,
        device_side_only=False,
    ),
    ObservationSpec(
        level=ObservationLevel.A1,
        cumulative_fields=A1_FIELDS,
        tensor_value_reads=True,
        device_side_only=True,
    ),
    ObservationSpec(
        level=ObservationLevel.A2,
        cumulative_fields=A2_FIELDS,
        tensor_value_reads=True,
        device_side_only=True,
        deterministic_sample_prefix_sizes=(32, 128, 256),
        sample_index_rule=(
            "per-layer hash ranking without replacement over "
            "contract_id,model_seed,batch_id,layer_id,tensor_role"
        ),
    ),
)

ANALYTIC_REGISTRY: Final[tuple[AnalyticSpec, ...]] = (
    AnalyticSpec(
        analytic_id=QWakeFPAnalyticId.ROSENBAUM_WAVEFRONT_STATUS_V1,
        analytic_class=AnalyticClass.EXACT,
        minimum_observation=ObservationLevel.A0,
        output_fields=(
            "completed_component_prefix",
            "next_structurally_unfinished_component",
        ),
        may_directly_accept=False,
        role="analytic positive control for corrected Rosenbaum completion order",
    ),
    AnalyticSpec(
        analytic_id=QWakeFPAnalyticId.RESIDUAL_PERSISTENCE_V1,
        analytic_class=AnalyticClass.HEURISTIC,
        minimum_observation=ObservationLevel.A1,
        output_fields=(
            "prediction_error_nonincreasing",
            "state_delta_nonincreasing",
            "persistence_window_complete",
        ),
        may_directly_accept=False,
        role="registered residual baseline and diagnostic only",
    ),
    AnalyticSpec(
        analytic_id=QWakeFPAnalyticId.COST_DOMINANCE_V1,
        analytic_class=AnalyticClass.CONSERVATIVE,
        minimum_observation=ObservationLevel.A0,
        output_fields=(
            "candidate_acquisition_dominated",
            "lower_bound_remaining_suffix_ns",
            "upper_bound_acquisition_ns",
        ),
        may_directly_accept=False,
        role="cost-only pruning; never a sufficiency certificate",
    ),
)

PAIR_EQUALITIES: Final[tuple[str, ...]] = (
    "canonical_endpoint_response",
    "named_parameter_gradients",
    "endpoint_beliefs",
    "endpoint_loss",
    "transition_sequence",
    "rng_state_after",
    "snapshot_identity",
)

PAIR_MEASUREMENTS: Final[tuple[str, ...]] = (
    "observer_host_time_ns",
    "observer_device_time_ns",
    "observer_synchronization_count",
    "observer_d2h_bytes",
    "observer_temporary_memory_bytes",
    "observer_trace_bytes",
)

PAIRED_VALIDATION_REGISTRY: Final[tuple[PairedValidationSpec, ...]] = (
    PairedValidationSpec(
        pair_id=QWakeFPPairId.P0,
        reference="B0",
        instrumented="B0+A0",
        cumulative_level=ObservationLevel.A0,
        required_equalities=PAIR_EQUALITIES,
        measured_outputs=PAIR_MEASUREMENTS,
    ),
    PairedValidationSpec(
        pair_id=QWakeFPPairId.P1,
        reference="B0",
        instrumented="B0+A0+A1",
        cumulative_level=ObservationLevel.A1,
        required_equalities=PAIR_EQUALITIES,
        measured_outputs=PAIR_MEASUREMENTS,
    ),
    PairedValidationSpec(
        pair_id=QWakeFPPairId.P2,
        reference="B0",
        instrumented="B0+A0+A1+A2",
        cumulative_level=ObservationLevel.A2,
        required_equalities=PAIR_EQUALITIES,
        measured_outputs=PAIR_MEASUREMENTS,
    ),
)

THRESHOLD_PROFILE: Final[ThresholdProfile] = ThresholdProfile(
    lane="rocm_float32",
    max_abs=1e-5,
    max_relative_l2=1e-3,
    min_cosine=0.999,
    zero_atol=1e-7,
)

COST_MAPPING: Final[CostMappingSpec] = CostMappingSpec(
    raw_fields=(
        "host_time_ns",
        "device_time_ns",
        "synchronization_count",
        "d2h_bytes",
        "temporary_memory_bytes",
        "trace_bytes",
    ),
    exclusive_time_categories=(
        "compute_ns",
        "observer_ns",
        "diagnostic_ns",
        "control_ns",
        "fallback_ns",
    ),
    primary_time_basis=(
        "calibrated host critical-path allocation with each edge assigned to "
        "exactly one time category"
    ),
    device_time_semantics="auxiliary measurement; never added a second time",
    memory_semantics="maximum temporary_memory_bytes on the replayed path",
    d2h_and_trace_semantics="reported as raw vector components, not hidden in time",
    selection_order=("safety", "coverage", "cost"),
)


def _serialize_role_capabilities() -> tuple[tuple[str, tuple[str, ...]], ...]:
    return tuple(
        (
            role.value,
            tuple(sorted(capability.value for capability in ROLE_CAPABILITY_ALLOWLIST[role])),
        )
        for role in CampaignRole
    )


def _serialize_role_receipts() -> tuple[tuple[str, tuple[str, ...]], ...]:
    return tuple(
        (
            role.value,
            tuple(sorted(receipt.value for receipt in ROLE_REQUIRED_RECEIPTS[role])),
        )
        for role in CampaignRole
    )


def _canonicalize(value: object) -> object:
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, dict):
        return {
            str(key): _canonicalize(item)
            for key, item in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, tuple | list):
        return [_canonicalize(item) for item in value]
    return value


def build_qwake_fp_special_case_contract() -> QWakeFPSpecialCaseContract:
    """Build the single frozen QW-2 contract."""

    return QWakeFPSpecialCaseContract(
        schema_version=1,
        contract_id="stage3b-qwake-fp-special-case-v1",
        status="spec_frozen_execution_closed",
        method=QWakeFPMethod.FIXEDPRED,
        eta=1.0,
        executor=QWakeFPExecutor.STAGE2_BASELINE,
        architecture=QWakeFPArchitecture.LENET_CLASSIC,
        horizon_rule=QWakeFPHorizonRule.REGISTERED_INFERENCE_STEPS,
        decision_epoch="after S_t and before sweep t+1 for t in [0,K_ref]",
        snapshot_zero_semantics="initialized state before the first inference sweep",
        response_components=tuple(QWakeFPResponseComponent),
        primary_defect=(
            "r_Gamma(t)=max(max_abs/max_abs_limit,relative_l2/"
            "max_relative_l2_limit,(1-cosine)/(1-min_cosine)); "
            "structural_or_finite_failure=infinity"
        ),
        sufficiency_rule="M_star(t)=1-r_Gamma(t)>=0",
        stable_sufficiency_rule=(
            "t_star=min{t: sufficient(j)=true for every j in [t,K_ref]}"
        ),
        threshold_profile=THRESHOLD_PROFILE,
        observations=OBSERVATION_REGISTRY,
        analytics=ANALYTIC_REGISTRY,
        cost_mapping=COST_MAPPING,
        baselines=tuple(QWakeFPBaselineId),
        paired_validation=PAIRED_VALIDATION_REGISTRY,
        role_capabilities=_serialize_role_capabilities(),
        role_receipts=_serialize_role_receipts(),
        scientific_execution_open=False,
        oracle_label_generation_open=False,
        feature_collection_permitted=False,
        policy_activation_permitted=False,
        test_dataset_access=False,
        generalization_claim=False,
    )


QWAKE_FP_SPECIAL_CASE_CONTRACT: Final[QWakeFPSpecialCaseContract] = (
    build_qwake_fp_special_case_contract()
)
