"""Backend-neutral QWake-FP superset pipeline contracts for QW-3.

The module implements the finite orchestration, immutable trajectory schema,
offline replay, evaluation, cost mapping, and sealing layers required by the
bounded QWake-FP plan.  It deliberately performs no Torch2PC, Torch, GPU,
filesystem, subprocess, network, or publication side effects.  Live adapters
remain unbound and every effectful component must first cross the QW-1
role/capability boundary.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, is_dataclass
from enum import StrEnum
from typing import Any, Final, cast

from torch2pc_thesis.stage3b_qwake_core import (
    ROLE_CAPABILITY_ALLOWLIST,
    AnalyticOutcome,
    CampaignRole,
    Capability,
    DecisionCost,
    EdgeMeasurement,
    ExecutionContext,
    FrontierAction,
    FrontierActionKind,
    ObservationLevel,
    OracleLabel,
    Provenance,
    QWakePermissionError,
)
from torch2pc_thesis.stage3b_qwake_fp_spec import (
    A0_FIELDS,
    A1_FIELDS,
    A2_FIELDS,
    ANALYTIC_REGISTRY,
    QWAKE_FP_SPECIAL_CASE_CONTRACT,
    QWakeFPAnalyticId,
    QWakeFPBaselineId,
)

type Scalar = bool | int | float | str

_FORBIDDEN_PREACTION_TOKENS: Final[tuple[str, ...]] = (
    "oracle",
    "t_star",
    "reference_future",
    "sufficiency_margin",
)
_OBSERVATION_FIELDS: Final[Mapping[ObservationLevel, tuple[str, ...]]] = {
    ObservationLevel.A0: A0_FIELDS,
    ObservationLevel.A1: A1_FIELDS,
    ObservationLevel.A2: A2_FIELDS,
}
_OBSERVATION_RANK: Final[Mapping[ObservationLevel, int]] = {
    ObservationLevel.A0: 0,
    ObservationLevel.A1: 1,
    ObservationLevel.A2: 2,
}
_ANALYTIC_BY_ID: Final = {item.analytic_id: item for item in ANALYTIC_REGISTRY}


class QWakeFPPipelineError(ValueError):
    """Raised when a QW-3 pipeline contract is malformed or violated."""


class PipelinePhase(StrEnum):
    """Finite execution phases represented by the superset pipeline."""

    LIVE = "live"
    OFFLINE = "offline"
    POST_ACTION = "post_action"
    EXPORT = "export"


class PipelineComponentId(StrEnum):
    """Closed component registry embedded before the scientific image freeze."""

    COLLECT_A0 = "collect_a0"
    COLLECT_A1 = "collect_a1"
    COLLECT_A2 = "collect_a2"
    RUN_EXACT_ANALYTIC = "run_exact_analytic"
    RUN_CONSERVATIVE_ANALYTIC = "run_conservative_analytic"
    RUN_HEURISTIC_ANALYTIC = "run_heuristic_analytic"
    COMPLETE_CANONICAL_SUFFIX = "complete_canonical_suffix"
    COMPUTE_POST_ACTION_ORACLE = "compute_post_action_oracle"
    MAP_EDGE_COSTS = "map_edge_costs"
    ANALYZE_OPPORTUNITY = "analyze_opportunity"
    ANALYZE_RECOGNIZABILITY = "analyze_recognizability"
    INTERPRET_OFFLINE_POLICY = "interpret_offline_policy"
    INTERPRET_FROZEN_POLICY = "interpret_frozen_policy"
    REPLAY_BASELINES = "replay_baselines"
    REPLAY_ABLATIONS = "replay_ablations"
    EVALUATE_CONFIRMATORY_SHADOW = "evaluate_confirmatory_shadow"
    EVALUATE_REPLICATION = "evaluate_replication"
    SEAL_ARTIFACT = "seal_artifact"
    RENDER_PUBLICATION_EXPORT = "render_publication_export"


class CostCategory(StrEnum):
    """Exclusive host critical-path categories frozen by QW-2."""

    COMPUTE = "compute_ns"
    OBSERVER = "observer_ns"
    DIAGNOSTIC = "diagnostic_ns"
    CONTROL = "control_ns"
    FALLBACK = "fallback_ns"


class PolicyPredicateKind(StrEnum):
    """Finite predicates supported by the built-in policy interpreter."""

    ALWAYS = "always"
    FEATURE_LE = "feature_le"
    FEATURE_GE = "feature_ge"
    ANALYTIC_OUTCOME_IS = "analytic_outcome_is"
    OBSERVATION_LEVEL_AT_LEAST = "observation_level_at_least"


class QWakeFPAblationId(StrEnum):
    """Closed nested-ablation registry."""

    WITHOUT_A1 = "without_A1"
    WITHOUT_A2 = "without_A2"
    WITHOUT_ANALYTICS = "without_analytics"
    WITHOUT_ADAPTIVE_ORDER = "without_adaptive_order"
    WITHOUT_COST_DOMINANCE = "without_cost_dominance"


class EvaluationClass(StrEnum):
    """Bounded result classes admitted by the QWake-FP plan."""

    SAFE_AND_BENEFICIAL = "SAFE_AND_BENEFICIAL"
    SAFE_BUT_NOT_BENEFICIAL = "SAFE_BUT_NOT_BENEFICIAL"
    UNSAFE = "UNSAFE"
    NO_NONTRIVIAL_COVERAGE = "NO_NONTRIVIAL_COVERAGE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


@dataclass(frozen=True)
class PipelineComponentSpec:
    """One embedded component and its effect-local authorization contract."""

    component_id: PipelineComponentId
    phase: PipelinePhase
    allowed_roles: tuple[CampaignRole, ...]
    required_capabilities: tuple[Capability, ...]
    input_schema: str
    output_schema: str
    effectful: bool

    def __post_init__(self) -> None:
        if not self.input_schema or not self.output_schema:
            raise QWakeFPPipelineError("component schemas cannot be empty")
        if len(self.allowed_roles) != len(set(self.allowed_roles)):
            raise QWakeFPPipelineError("component roles cannot be duplicated")
        if len(self.required_capabilities) != len(set(self.required_capabilities)):
            raise QWakeFPPipelineError("component capabilities cannot be duplicated")
        for role in self.allowed_roles:
            forbidden = set(self.required_capabilities) - set(
                ROLE_CAPABILITY_ALLOWLIST[role]
            )
            if forbidden:
                names = ", ".join(sorted(item.value for item in forbidden))
                raise QWakeFPPipelineError(
                    f"component {self.component_id.value} requires forbidden "
                    f"capabilities for {role.value}: {names}"
                )
        if self.phase is PipelinePhase.LIVE and not self.effectful:
            raise QWakeFPPipelineError("live components must be marked effectful")
        if self.phase is PipelinePhase.OFFLINE and CampaignRole.C2_CALIBRATION not in (
            self.allowed_roles
        ) and self.component_id in {
            PipelineComponentId.ANALYZE_RECOGNIZABILITY,
            PipelineComponentId.REPLAY_BASELINES,
            PipelineComponentId.REPLAY_ABLATIONS,
        }:
            raise QWakeFPPipelineError("C2 offline components must admit C2")


@dataclass(frozen=True)
class PipelinePlan:
    """A pure plan proving authorization without executing a component."""

    component_id: PipelineComponentId
    role: CampaignRole
    input_artifact_sha256s: tuple[str, ...]
    request_sha256: str
    plan_sha256: str


@dataclass(frozen=True)
class FrozenFeatureVector:
    """Canonical pre-action feature vector with no oracle fields."""

    level: ObservationLevel
    fields: tuple[tuple[str, Scalar], ...]

    def __post_init__(self) -> None:
        names = tuple(name for name, _ in self.fields)
        expected = _OBSERVATION_FIELDS[self.level]
        if names != expected:
            raise QWakeFPPipelineError(
                f"{self.level.value} fields must exactly match the QW-2 registry"
            )
        for name, value in self.fields:
            if any(token in name for token in _FORBIDDEN_PREACTION_TOKENS):
                raise QWakeFPPipelineError("oracle data cannot enter pre-action features")
            _validate_scalar(value, field_name=name)

    def as_mapping(self) -> dict[str, Scalar]:
        return dict(self.fields)

    def value(self, field_name: str) -> Scalar:
        values = self.as_mapping()
        if field_name not in values:
            raise QWakeFPPipelineError(f"feature is unavailable: {field_name}")
        return values[field_name]


@dataclass(frozen=True)
class FrozenAnalyticOutput:
    """One registered analytic output attached to a snapshot."""

    analytic_id: QWakeFPAnalyticId
    outcome: AnalyticOutcome
    fields: tuple[tuple[str, Scalar], ...]
    measurement: EdgeMeasurement

    def __post_init__(self) -> None:
        spec = _ANALYTIC_BY_ID[self.analytic_id]
        names = tuple(name for name, _ in self.fields)
        if names != spec.output_fields:
            raise QWakeFPPipelineError(
                f"analytic {self.analytic_id.value} output differs from QW-2"
            )
        for name, value in self.fields:
            _validate_scalar(value, field_name=name)


@dataclass(frozen=True)
class MeasuredEdge:
    """One raw edge measurement assigned to exactly one time category."""

    edge_id: str
    category: CostCategory
    measurement: EdgeMeasurement

    def __post_init__(self) -> None:
        if not self.edge_id.strip():
            raise QWakeFPPipelineError("edge_id cannot be empty")


@dataclass(frozen=True)
class TrajectorySnapshotRecord:
    """One immutable C1/C3/R snapshot with post-action audit attached."""

    model_seed: int
    batch_id: str
    snapshot_id: str
    compute_step: int
    observation: FrozenFeatureVector
    analytics: tuple[FrozenAnalyticOutput, ...]
    measured_edges: tuple[MeasuredEdge, ...]
    remaining_suffix_ns: int
    provenance: Provenance
    oracle_label: OracleLabel | None = None

    def __post_init__(self) -> None:
        if self.model_seed < 0 or self.compute_step < 0:
            raise QWakeFPPipelineError("seed and compute_step must be non-negative")
        if not self.batch_id.strip() or not self.snapshot_id.strip():
            raise QWakeFPPipelineError("batch_id and snapshot_id cannot be empty")
        if self.remaining_suffix_ns < 0:
            raise QWakeFPPipelineError("remaining_suffix_ns must be non-negative")
        analytic_ids = tuple(item.analytic_id for item in self.analytics)
        if len(analytic_ids) != len(set(analytic_ids)):
            raise QWakeFPPipelineError("analytic outputs cannot be duplicated")
        for analytic in self.analytics:
            minimum = _ANALYTIC_BY_ID[analytic.analytic_id].minimum_observation
            if _OBSERVATION_RANK[self.observation.level] < _OBSERVATION_RANK[minimum]:
                raise QWakeFPPipelineError(
                    f"{analytic.analytic_id.value} requires {minimum.value}"
                )
        edge_ids = tuple(item.edge_id for item in self.measured_edges)
        if len(edge_ids) != len(set(edge_ids)):
            raise QWakeFPPipelineError("measured edge ids cannot be duplicated")
        if self.oracle_label is not None and (
            self.oracle_label.snapshot_id != self.snapshot_id
        ):
            raise QWakeFPPipelineError("oracle label must match snapshot_id")

    @property
    def record_id(self) -> str:
        return f"seed={self.model_seed}/batch={self.batch_id}/{self.snapshot_id}"

    def analytic_outcome(
        self,
        analytic_id: QWakeFPAnalyticId,
    ) -> AnalyticOutcome | None:
        for item in self.analytics:
            if item.analytic_id is analytic_id:
                return item.outcome
        return None


@dataclass(frozen=True)
class SealedTrajectoryDataset:
    """Self-contained immutable dataset accepted by offline C2."""

    schema_version: int
    contract_id: str
    records: tuple[TrajectorySnapshotRecord, ...]
    source_receipt_sha256: str

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise QWakeFPPipelineError("trajectory schema_version must be 1")
        if self.contract_id != QWAKE_FP_SPECIAL_CASE_CONTRACT.contract_id:
            raise QWakeFPPipelineError("trajectory contract_id differs from QW-2")
        if not self.records:
            raise QWakeFPPipelineError("sealed trajectory dataset cannot be empty")
        _require_sha256(self.source_receipt_sha256, field_name="source_receipt_sha256")
        record_ids = tuple(record.record_id for record in self.records)
        if len(record_ids) != len(set(record_ids)):
            raise QWakeFPPipelineError("trajectory record ids must be unique")
        if record_ids != tuple(sorted(record_ids)):
            raise QWakeFPPipelineError("trajectory records must be canonically sorted")
        for record in self.records:
            if record.oracle_label is None:
                raise QWakeFPPipelineError(
                    "sealed C1 trajectories require post-action oracle labels"
                )

    def canonical_json(self) -> str:
        return _canonical_json(self)

    def sha256(self) -> str:
        return _sha256_text(self.canonical_json())


@dataclass(frozen=True)
class PolicyRule:
    """One finite rule interpreted only over pre-action fields."""

    rule_id: str
    predicate: PolicyPredicateKind
    action: FrontierAction
    feature_name: str | None = None
    threshold: float | None = None
    analytic_id: QWakeFPAnalyticId | None = None
    analytic_outcome: AnalyticOutcome | None = None
    minimum_observation: ObservationLevel | None = None

    def __post_init__(self) -> None:
        if not self.rule_id.strip():
            raise QWakeFPPipelineError("policy rule_id cannot be empty")
        if self.action.kind not in {
            FrontierActionKind.ACCEPT_FRONTIER,
            FrontierActionKind.ADVANCE_OBSERVATION,
            FrontierActionKind.ADVANCE_ANALYTIC,
            FrontierActionKind.ADVANCE_COMPUTE,
            FrontierActionKind.COMPLETE_SUFFIX,
        }:
            raise QWakeFPPipelineError("policy action is outside the finite alphabet")
        if self.predicate in {
            PolicyPredicateKind.FEATURE_LE,
            PolicyPredicateKind.FEATURE_GE,
        }:
            if self.feature_name is None or self.threshold is None:
                raise QWakeFPPipelineError("feature predicates require name and threshold")
            if self.feature_name not in A2_FIELDS:
                raise QWakeFPPipelineError("policy feature is outside the QW-2 registry")
            if any(
                token in self.feature_name for token in _FORBIDDEN_PREACTION_TOKENS
            ):
                raise QWakeFPPipelineError("policy cannot inspect oracle fields")
            if not math.isfinite(self.threshold):
                raise QWakeFPPipelineError("policy threshold must be finite")
        elif self.predicate is PolicyPredicateKind.ANALYTIC_OUTCOME_IS:
            if self.analytic_id is None or self.analytic_outcome is None:
                raise QWakeFPPipelineError(
                    "analytic predicate requires analytic id and outcome"
                )
        elif self.predicate is PolicyPredicateKind.OBSERVATION_LEVEL_AT_LEAST:
            if self.minimum_observation is None:
                raise QWakeFPPipelineError(
                    "observation predicate requires minimum_observation"
                )
        elif self.predicate is not PolicyPredicateKind.ALWAYS:
            raise QWakeFPPipelineError("unsupported policy predicate")


@dataclass(frozen=True)
class FrozenPolicyManifest:
    """Immutable data-only policy consumed by the built-in interpreter."""

    schema_version: int
    policy_id: str
    contract_id: str
    rules: tuple[PolicyRule, ...]
    default_action: FrontierAction

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise QWakeFPPipelineError("policy schema_version must be 1")
        if not self.policy_id.strip():
            raise QWakeFPPipelineError("policy_id cannot be empty")
        if self.contract_id != QWAKE_FP_SPECIAL_CASE_CONTRACT.contract_id:
            raise QWakeFPPipelineError("policy contract_id differs from QW-2")
        rule_ids = tuple(rule.rule_id for rule in self.rules)
        if len(rule_ids) != len(set(rule_ids)):
            raise QWakeFPPipelineError("policy rule ids cannot be duplicated")
        if self.default_action.kind is not FrontierActionKind.COMPLETE_SUFFIX:
            raise QWakeFPPipelineError("policy default must fail closed to suffix")

    def canonical_json(self) -> str:
        return _canonical_json(self)

    def sha256(self) -> str:
        return _sha256_text(self.canonical_json())


@dataclass(frozen=True)
class BaselineConfiguration:
    """Finite parameters for deterministic B0-B7 replay."""

    fixed_prefix_step: int = 1
    a0_remaining_sweeps_threshold: int = 0
    a1_error_threshold: float = 0.0
    a2_error_threshold: float = 0.0

    def __post_init__(self) -> None:
        if self.fixed_prefix_step < 0 or self.a0_remaining_sweeps_threshold < 0:
            raise QWakeFPPipelineError("baseline integer thresholds must be non-negative")
        if self.a1_error_threshold < 0 or self.a2_error_threshold < 0:
            raise QWakeFPPipelineError("baseline error thresholds must be non-negative")


@dataclass(frozen=True)
class ShadowDecision:
    """One replayed or shadow decision with post-action audit."""

    record_id: str
    action_kind: FrontierActionKind
    accepted: bool
    oracle_sufficient: bool
    dangerous_accept: bool
    decision_cost: DecisionCost
    net_saving_ns: int


@dataclass(frozen=True)
class EvaluationSummary:
    """Seed-agnostic deterministic summary; seed-level inference is later."""

    evaluated_records: int
    accepted_records: int
    dangerous_accepts: int
    safe_accepts: int
    total_net_saving_ns: int
    coverage: float
    result_class: EvaluationClass
    decisions: tuple[ShadowDecision, ...]


@dataclass(frozen=True)
class OpportunitySummary:
    """Existence and upper-bound opportunity evidence from sealed trajectories."""

    evaluated_records: int
    sufficient_preterminal_records: int
    exists_preterminal_sufficient_state: bool
    maximum_potential_saving_ns: int
    potential_avoided_cost_exceeds_control_overhead_lower_bound: bool


@dataclass(frozen=True)
class SealedArtifact:
    """Pure canonical seal; persistence is an external effect."""

    artifact_kind: str
    schema_version: int
    payload_sha256: str
    canonical_json: str

    def __post_init__(self) -> None:
        if not self.artifact_kind.strip() or self.schema_version < 1:
            raise QWakeFPPipelineError("sealed artifact identity is invalid")
        _require_sha256(self.payload_sha256, field_name="payload_sha256")
        if self.payload_sha256 != _sha256_text(self.canonical_json):
            raise QWakeFPPipelineError("sealed artifact digest differs from payload")


COMPONENT_REGISTRY: Final[tuple[PipelineComponentSpec, ...]] = (
    PipelineComponentSpec(
        PipelineComponentId.COLLECT_A0,
        PipelinePhase.LIVE,
        (CampaignRole.C1_COLLECTION, CampaignRole.C3_CONFIRMATORY, CampaignRole.R_REPLICATION),
        (Capability.EXECUTE_FIXEDPRED, Capability.COLLECT_A0),
        "fixedpred_snapshot_v1",
        "qwake_a0_v1",
        True,
    ),
    PipelineComponentSpec(
        PipelineComponentId.COLLECT_A1,
        PipelinePhase.LIVE,
        (CampaignRole.C1_COLLECTION, CampaignRole.C3_CONFIRMATORY, CampaignRole.R_REPLICATION),
        (Capability.COLLECT_A1,),
        "qwake_a0_v1",
        "qwake_a1_v1",
        True,
    ),
    PipelineComponentSpec(
        PipelineComponentId.COLLECT_A2,
        PipelinePhase.LIVE,
        (CampaignRole.C1_COLLECTION, CampaignRole.C3_CONFIRMATORY, CampaignRole.R_REPLICATION),
        (Capability.COLLECT_A2,),
        "qwake_a1_v1",
        "qwake_a2_v1",
        True,
    ),
    PipelineComponentSpec(
        PipelineComponentId.RUN_EXACT_ANALYTIC,
        PipelinePhase.LIVE,
        (CampaignRole.C1_COLLECTION, CampaignRole.C3_CONFIRMATORY, CampaignRole.R_REPLICATION),
        (Capability.RUN_LIVE_ANALYTICS, Capability.RUN_ANALYTIC_EXACT),
        "qwake_snapshot_v1",
        "qwake_analytic_v1",
        True,
    ),
    PipelineComponentSpec(
        PipelineComponentId.RUN_CONSERVATIVE_ANALYTIC,
        PipelinePhase.LIVE,
        (CampaignRole.C1_COLLECTION, CampaignRole.C3_CONFIRMATORY, CampaignRole.R_REPLICATION),
        (Capability.RUN_LIVE_ANALYTICS, Capability.RUN_ANALYTIC_CONSERVATIVE),
        "qwake_snapshot_v1",
        "qwake_analytic_v1",
        True,
    ),
    PipelineComponentSpec(
        PipelineComponentId.RUN_HEURISTIC_ANALYTIC,
        PipelinePhase.LIVE,
        (CampaignRole.C1_COLLECTION, CampaignRole.C3_CONFIRMATORY, CampaignRole.R_REPLICATION),
        (Capability.RUN_LIVE_ANALYTICS, Capability.RUN_ANALYTIC_HEURISTIC),
        "qwake_snapshot_v1",
        "qwake_analytic_v1",
        True,
    ),
    PipelineComponentSpec(
        PipelineComponentId.COMPLETE_CANONICAL_SUFFIX,
        PipelinePhase.LIVE,
        (CampaignRole.C1_COLLECTION, CampaignRole.C3_CONFIRMATORY, CampaignRole.R_REPLICATION),
        (Capability.COMPUTE_CANONICAL_SUFFIX,),
        "qwake_snapshot_v1",
        "canonical_response_v1",
        True,
    ),
    PipelineComponentSpec(
        PipelineComponentId.COMPUTE_POST_ACTION_ORACLE,
        PipelinePhase.POST_ACTION,
        (CampaignRole.C1_COLLECTION, CampaignRole.C3_CONFIRMATORY, CampaignRole.R_REPLICATION),
        (Capability.COMPUTE_POST_ACTION_ORACLE, Capability.COMPUTE_NEW_ORACLE_LABELS),
        "canonical_response_v1",
        "qwake_oracle_label_v1",
        True,
    ),
    PipelineComponentSpec(
        PipelineComponentId.MAP_EDGE_COSTS,
        PipelinePhase.OFFLINE,
        tuple(CampaignRole),
        (),
        "edge_measurement_v1",
        "decision_cost_v1",
        False,
    ),
    PipelineComponentSpec(
        PipelineComponentId.ANALYZE_OPPORTUNITY,
        PipelinePhase.OFFLINE,
        (CampaignRole.C1_COLLECTION,),
        (Capability.RUN_OPPORTUNITY_ANALYSIS,),
        "sealed_trajectory_dataset_v1",
        "opportunity_summary_v1",
        False,
    ),
    PipelineComponentSpec(
        PipelineComponentId.ANALYZE_RECOGNIZABILITY,
        PipelinePhase.OFFLINE,
        (CampaignRole.C2_CALIBRATION,),
        (
            Capability.ACCESS_SEALED_C1_ARTIFACTS,
            Capability.RUN_OFFLINE_REPLAY,
            Capability.RUN_RECOGNIZABILITY_ANALYSIS,
        ),
        "sealed_trajectory_dataset_v1",
        "evaluation_summary_v1",
        False,
    ),
    PipelineComponentSpec(
        PipelineComponentId.INTERPRET_OFFLINE_POLICY,
        PipelinePhase.OFFLINE,
        (CampaignRole.C2_CALIBRATION,),
        (
            Capability.ACCESS_SEALED_C1_ARTIFACTS,
            Capability.RUN_OFFLINE_REPLAY,
        ),
        "qwake_snapshot_v1+candidate_policy_v1",
        "frontier_action_v1",
        False,
    ),
    PipelineComponentSpec(
        PipelineComponentId.INTERPRET_FROZEN_POLICY,
        PipelinePhase.OFFLINE,
        (CampaignRole.C3_CONFIRMATORY, CampaignRole.R_REPLICATION),
        (Capability.LOAD_FROZEN_POLICY,),
        "qwake_snapshot_v1+frozen_policy_v1",
        "frontier_action_v1",
        False,
    ),
    PipelineComponentSpec(
        PipelineComponentId.REPLAY_BASELINES,
        PipelinePhase.OFFLINE,
        (CampaignRole.C2_CALIBRATION,),
        (
            Capability.ACCESS_SEALED_C1_ARTIFACTS,
            Capability.RUN_OFFLINE_REPLAY,
            Capability.EVALUATE_BASELINES,
        ),
        "sealed_trajectory_dataset_v1",
        "baseline_evaluation_v1",
        False,
    ),
    PipelineComponentSpec(
        PipelineComponentId.REPLAY_ABLATIONS,
        PipelinePhase.OFFLINE,
        (CampaignRole.C2_CALIBRATION,),
        (
            Capability.ACCESS_SEALED_C1_ARTIFACTS,
            Capability.RUN_OFFLINE_REPLAY,
        ),
        "sealed_trajectory_dataset_v1+frozen_policy_v1",
        "ablation_evaluation_v1",
        False,
    ),
    PipelineComponentSpec(
        PipelineComponentId.EVALUATE_CONFIRMATORY_SHADOW,
        PipelinePhase.OFFLINE,
        (CampaignRole.C3_CONFIRMATORY,),
        (
            Capability.LOAD_FROZEN_POLICY,
            Capability.EXECUTE_SHADOW_POLICY,
            Capability.EVALUATE_CONFIRMATORY,
        ),
        "confirmatory_trajectory_v1+frozen_policy_v1",
        "evaluation_summary_v1",
        False,
    ),
    PipelineComponentSpec(
        PipelineComponentId.EVALUATE_REPLICATION,
        PipelinePhase.OFFLINE,
        (CampaignRole.R_REPLICATION,),
        (
            Capability.LOAD_FROZEN_POLICY,
            Capability.EXECUTE_SHADOW_POLICY,
            Capability.EVALUATE_REPLICATION,
        ),
        "replication_trajectory_v1+frozen_policy_v1",
        "evaluation_summary_v1",
        False,
    ),
    PipelineComponentSpec(
        PipelineComponentId.SEAL_ARTIFACT,
        PipelinePhase.EXPORT,
        tuple(CampaignRole),
        (Capability.SEAL_EVIDENCE,),
        "canonical_payload_v1",
        "sealed_artifact_v1",
        False,
    ),
    PipelineComponentSpec(
        PipelineComponentId.RENDER_PUBLICATION_EXPORT,
        PipelinePhase.EXPORT,
        (),
        (Capability.PUBLISH_RESULTS,),
        "sealed_evidence_bundle_v1",
        "publication_bundle_v1",
        False,
    ),
)

_COMPONENT_BY_ID: Final = {item.component_id: item for item in COMPONENT_REGISTRY}

BASELINE_REGISTRY: Final[tuple[QWakeFPBaselineId, ...]] = tuple(QWakeFPBaselineId)
ABLATION_REGISTRY: Final[tuple[QWakeFPAblationId, ...]] = tuple(QWakeFPAblationId)


def plan_component(
    context: ExecutionContext,
    component_id: PipelineComponentId,
    input_artifact_sha256s: Sequence[str] = (),
) -> PipelinePlan:
    """Authorize and canonically identify a component plan without executing it."""

    spec = _COMPONENT_BY_ID[component_id]
    if context.role not in spec.allowed_roles:
        raise QWakePermissionError(
            f"{component_id.value} is unavailable for {context.role.value}"
        )
    context.permissions.require(*spec.required_capabilities)
    inputs = tuple(input_artifact_sha256s)
    for digest in inputs:
        _require_sha256(digest, field_name="input artifact sha256")
    payload = {
        "component_id": component_id.value,
        "role": context.role.value,
        "inputs": inputs,
        "request_sha256": context.request_sha256,
        "manifest_sha256": context.manifest_sha256,
        "code_manifest_sha256": context.code_manifest_sha256,
    }
    plan_sha256 = _sha256_text(_canonical_json(payload))
    return PipelinePlan(
        component_id=component_id,
        role=context.role,
        input_artifact_sha256s=inputs,
        request_sha256=context.request_sha256,
        plan_sha256=plan_sha256,
    )


def build_feature_vector(
    level: ObservationLevel,
    values: Mapping[str, Scalar],
) -> FrozenFeatureVector:
    """Build one exact cumulative feature vector in QW-2 field order."""

    expected = _OBSERVATION_FIELDS[level]
    missing = set(expected) - set(values)
    extra = set(values) - set(expected)
    if missing or extra:
        raise QWakeFPPipelineError(
            f"feature keys differ from {level.value}; "
            f"missing={sorted(missing)}, extra={sorted(extra)}"
        )
    return FrozenFeatureVector(
        level=level,
        fields=tuple((name, values[name]) for name in expected),
    )


def map_edge_measurement(
    measurement: EdgeMeasurement,
    category: CostCategory,
) -> DecisionCost:
    """Map one raw edge to one exclusive decision-cost time category."""

    host_time_ns = measurement.host_time_ns
    memory_bytes = measurement.temporary_memory_bytes
    if category is CostCategory.COMPUTE:
        return DecisionCost(compute_ns=host_time_ns, memory_bytes=memory_bytes)
    if category is CostCategory.OBSERVER:
        return DecisionCost(observer_ns=host_time_ns, memory_bytes=memory_bytes)
    if category is CostCategory.DIAGNOSTIC:
        return DecisionCost(diagnostic_ns=host_time_ns, memory_bytes=memory_bytes)
    if category is CostCategory.CONTROL:
        return DecisionCost(control_ns=host_time_ns, memory_bytes=memory_bytes)
    if category is CostCategory.FALLBACK:
        return DecisionCost(fallback_ns=host_time_ns, memory_bytes=memory_bytes)
    raise QWakeFPPipelineError(f"unsupported cost category: {category.value}")


def aggregate_decision_cost(edges: Sequence[MeasuredEdge]) -> DecisionCost:
    """Aggregate exclusive edge costs without adding device time a second time."""

    mapped = tuple(map_edge_measurement(edge.measurement, edge.category) for edge in edges)
    return DecisionCost(
        compute_ns=sum(item.compute_ns for item in mapped),
        latency_ns=sum(item.latency_ns for item in mapped),
        memory_bytes=max((item.memory_bytes for item in mapped), default=0),
        diagnostic_ns=sum(item.diagnostic_ns for item in mapped),
        observer_ns=sum(item.observer_ns for item in mapped),
        control_ns=sum(item.control_ns for item in mapped),
        fallback_ns=sum(item.fallback_ns for item in mapped),
    )


def interpret_policy(
    record: TrajectorySnapshotRecord,
    policy: FrozenPolicyManifest,
) -> FrontierAction:
    """Interpret a frozen policy using pre-action fields only."""

    for rule in policy.rules:
        if _rule_matches(record, rule):
            return rule.action
    return policy.default_action


def interpret_baseline(
    record: TrajectorySnapshotRecord,
    baseline: QWakeFPBaselineId,
    configuration: BaselineConfiguration,
    policy: FrozenPolicyManifest | None = None,
) -> FrontierAction:
    """Return one deterministic B0-B7 action for a frozen record."""

    if baseline is QWakeFPBaselineId.B0_FULL_CANONICAL_SUFFIX:
        return FrontierAction(FrontierActionKind.COMPLETE_SUFFIX)
    if baseline is QWakeFPBaselineId.B1_FIXED_PREFIX:
        return _accept_or_suffix(record.compute_step >= configuration.fixed_prefix_step)
    if baseline is QWakeFPBaselineId.B2_RESIDUAL_THRESHOLD:
        outcome = record.analytic_outcome(QWakeFPAnalyticId.RESIDUAL_PERSISTENCE_V1)
        return _accept_or_suffix(outcome is AnalyticOutcome.CERTIFIED_ACCEPT)
    if baseline is QWakeFPBaselineId.B3_A0_ONLY:
        value = record.observation.value("remaining_sweeps")
        return _accept_or_suffix(
            _as_int(value, "remaining_sweeps")
            <= configuration.a0_remaining_sweeps_threshold
        )
    if baseline is QWakeFPBaselineId.B4_FIXED_OBSERVATION_CASCADE:
        if record.observation.level is not ObservationLevel.A2:
            return FrontierAction(FrontierActionKind.COMPLETE_SUFFIX)
        a1 = _as_float(
            record.observation.value("global_prediction_error_l2_sq"),
            "global_prediction_error_l2_sq",
        )
        a2 = _as_float(
            record.observation.value("sample_prefix_prediction_error_l2_sq"),
            "sample_prefix_prediction_error_l2_sq",
        )
        return _accept_or_suffix(
            a1 <= configuration.a1_error_threshold
            and a2 <= configuration.a2_error_threshold
        )
    if baseline is QWakeFPBaselineId.B5_FIXED_ANALYTIC_REGISTRY:
        outcomes = tuple(item.outcome for item in record.analytics)
        return _accept_or_suffix(
            bool(outcomes)
            and all(outcome is AnalyticOutcome.CERTIFIED_ACCEPT for outcome in outcomes)
        )
    if baseline is QWakeFPBaselineId.B6_FROZEN_QWAKE_FP:
        if policy is None:
            raise QWakeFPPipelineError("B6 requires a frozen policy manifest")
        return interpret_policy(record, policy)
    if baseline is QWakeFPBaselineId.B7_POST_ACTION_ORACLE:
        if record.oracle_label is None:
            raise QWakeFPPipelineError("B7 requires a post-action oracle label")
        return _accept_or_suffix(record.oracle_label.sufficient)
    raise QWakeFPPipelineError(f"unsupported baseline: {baseline.value}")


def analyze_opportunity(
    dataset: SealedTrajectoryDataset,
    control_overhead_lower_bound_ns: int,
) -> OpportunitySummary:
    """Compute bounded opportunity evidence from sealed C1 trajectories."""

    if control_overhead_lower_bound_ns < 0:
        raise QWakeFPPipelineError("control overhead lower bound must be non-negative")
    opportunities: list[int] = []
    for record in dataset.records:
        oracle = cast(OracleLabel, record.oracle_label)
        if oracle.sufficient and record.remaining_suffix_ns > 0:
            observer_cost = aggregate_decision_cost(record.measured_edges).total_time_ns
            opportunities.append(record.remaining_suffix_ns - observer_cost)
    maximum = max(opportunities, default=0)
    return OpportunitySummary(
        evaluated_records=len(dataset.records),
        sufficient_preterminal_records=len(opportunities),
        exists_preterminal_sufficient_state=bool(opportunities),
        maximum_potential_saving_ns=maximum,
        potential_avoided_cost_exceeds_control_overhead_lower_bound=(
            maximum > control_overhead_lower_bound_ns
        ),
    )


def evaluate_policy(
    dataset: SealedTrajectoryDataset,
    policy: FrozenPolicyManifest,
) -> EvaluationSummary:
    """Deterministically replay one frozen policy with post-action audit."""

    return _evaluate_actions(
        dataset,
        tuple(interpret_policy(record, policy) for record in dataset.records),
    )


def evaluate_baseline(
    dataset: SealedTrajectoryDataset,
    baseline: QWakeFPBaselineId,
    configuration: BaselineConfiguration,
    policy: FrozenPolicyManifest | None = None,
) -> EvaluationSummary:
    """Deterministically replay one registered baseline."""

    actions = tuple(
        interpret_baseline(record, baseline, configuration, policy)
        for record in dataset.records
    )
    return _evaluate_actions(dataset, actions)


def apply_ablation(
    policy: FrozenPolicyManifest,
    ablation: QWakeFPAblationId,
) -> FrozenPolicyManifest:
    """Return a deterministic nested ablation of one frozen policy."""

    def keep(rule: PolicyRule) -> bool:
        action = rule.action
        if ablation is QWakeFPAblationId.WITHOUT_A1:
            return not (
                action.kind is FrontierActionKind.ADVANCE_OBSERVATION
                and action.target_observation is ObservationLevel.A1
            )
        if ablation is QWakeFPAblationId.WITHOUT_A2:
            return not (
                action.kind is FrontierActionKind.ADVANCE_OBSERVATION
                and action.target_observation is ObservationLevel.A2
            )
        if ablation is QWakeFPAblationId.WITHOUT_ANALYTICS:
            return action.kind is not FrontierActionKind.ADVANCE_ANALYTIC
        if ablation is QWakeFPAblationId.WITHOUT_COST_DOMINANCE:
            return rule.analytic_id is not QWakeFPAnalyticId.COST_DOMINANCE_V1
        if ablation is QWakeFPAblationId.WITHOUT_ADAPTIVE_ORDER:
            return rule.predicate is PolicyPredicateKind.ALWAYS
        raise QWakeFPPipelineError(f"unsupported ablation: {ablation.value}")

    return FrozenPolicyManifest(
        schema_version=policy.schema_version,
        policy_id=f"{policy.policy_id}:{ablation.value}",
        contract_id=policy.contract_id,
        rules=tuple(rule for rule in policy.rules if keep(rule)),
        default_action=policy.default_action,
    )


def seal_payload(artifact_kind: str, payload: object) -> SealedArtifact:
    """Create a pure canonical seal without writing or publishing anything."""

    canonical = _canonical_json(payload)
    return SealedArtifact(
        artifact_kind=artifact_kind,
        schema_version=1,
        payload_sha256=_sha256_text(canonical),
        canonical_json=canonical,
    )


def render_publication_bundle(
    artifacts: Sequence[SealedArtifact],
    claim_boundary: str,
) -> str:
    """Render a deterministic bundle; this function does not publish it."""

    if not claim_boundary.strip():
        raise QWakeFPPipelineError("claim_boundary cannot be empty")
    payload = {
        "schema_version": 1,
        "status": "rendered_not_published",
        "claim_boundary": claim_boundary,
        "artifacts": tuple(
            {
                "artifact_kind": item.artifact_kind,
                "payload_sha256": item.payload_sha256,
            }
            for item in sorted(
                artifacts,
                key=lambda item: (item.artifact_kind, item.payload_sha256),
            )
        ),
    }
    return _canonical_json(payload)


def _rule_matches(record: TrajectorySnapshotRecord, rule: PolicyRule) -> bool:
    if rule.predicate is PolicyPredicateKind.ALWAYS:
        return True
    if rule.predicate is PolicyPredicateKind.OBSERVATION_LEVEL_AT_LEAST:
        minimum = cast(ObservationLevel, rule.minimum_observation)
        return _OBSERVATION_RANK[record.observation.level] >= _OBSERVATION_RANK[minimum]
    if rule.predicate is PolicyPredicateKind.ANALYTIC_OUTCOME_IS:
        analytic_id = cast(QWakeFPAnalyticId, rule.analytic_id)
        expected = cast(AnalyticOutcome, rule.analytic_outcome)
        return record.analytic_outcome(analytic_id) is expected
    feature_name = cast(str, rule.feature_name)
    threshold = cast(float, rule.threshold)
    value = _as_float(record.observation.value(feature_name), feature_name)
    if rule.predicate is PolicyPredicateKind.FEATURE_LE:
        return value <= threshold
    if rule.predicate is PolicyPredicateKind.FEATURE_GE:
        return value >= threshold
    raise QWakeFPPipelineError(f"unsupported predicate: {rule.predicate.value}")


def _evaluate_actions(
    dataset: SealedTrajectoryDataset,
    actions: Sequence[FrontierAction],
) -> EvaluationSummary:
    if len(actions) != len(dataset.records):
        raise QWakeFPPipelineError("action count differs from trajectory records")
    decisions: list[ShadowDecision] = []
    for record, action in zip(dataset.records, actions, strict=True):
        oracle = cast(OracleLabel, record.oracle_label)
        accepted = action.kind is FrontierActionKind.ACCEPT_FRONTIER
        dangerous = accepted and not oracle.sufficient
        cost = aggregate_decision_cost(record.measured_edges)
        net_saving = (
            record.remaining_suffix_ns - cost.total_time_ns
            if accepted and not dangerous
            else -cost.total_time_ns
        )
        decisions.append(
            ShadowDecision(
                record_id=record.record_id,
                action_kind=action.kind,
                accepted=accepted,
                oracle_sufficient=oracle.sufficient,
                dangerous_accept=dangerous,
                decision_cost=cost,
                net_saving_ns=net_saving,
            )
        )
    accepted_count = sum(item.accepted for item in decisions)
    dangerous_count = sum(item.dangerous_accept for item in decisions)
    safe_count = accepted_count - dangerous_count
    coverage = accepted_count / len(decisions) if decisions else 0.0
    total_saving = sum(item.net_saving_ns for item in decisions)
    if not decisions:
        result_class = EvaluationClass.INSUFFICIENT_EVIDENCE
    elif dangerous_count:
        result_class = EvaluationClass.UNSAFE
    elif accepted_count == 0:
        result_class = EvaluationClass.NO_NONTRIVIAL_COVERAGE
    elif total_saving > 0:
        result_class = EvaluationClass.SAFE_AND_BENEFICIAL
    else:
        result_class = EvaluationClass.SAFE_BUT_NOT_BENEFICIAL
    return EvaluationSummary(
        evaluated_records=len(decisions),
        accepted_records=accepted_count,
        dangerous_accepts=dangerous_count,
        safe_accepts=safe_count,
        total_net_saving_ns=total_saving,
        coverage=coverage,
        result_class=result_class,
        decisions=tuple(decisions),
    )


def _accept_or_suffix(condition: bool) -> FrontierAction:
    return FrontierAction(
        FrontierActionKind.ACCEPT_FRONTIER
        if condition
        else FrontierActionKind.COMPLETE_SUFFIX
    )


def _validate_scalar(value: Scalar, *, field_name: str) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise QWakeFPPipelineError(f"{field_name} must be finite")
    if not isinstance(value, bool | int | float | str):
        raise QWakeFPPipelineError(f"{field_name} has an unsupported scalar type")


def _as_float(value: Scalar, field_name: str) -> float:
    if isinstance(value, bool | str):
        raise QWakeFPPipelineError(f"{field_name} must be numeric")
    converted = float(value)
    if not math.isfinite(converted):
        raise QWakeFPPipelineError(f"{field_name} must be finite")
    return converted


def _as_int(value: Scalar, field_name: str) -> int:
    if isinstance(value, bool | float | str):
        raise QWakeFPPipelineError(f"{field_name} must be an integer")
    return value


def _require_sha256(value: str, *, field_name: str) -> None:
    if len(value) != 71 or not value.startswith("sha256:"):
        raise QWakeFPPipelineError(f"{field_name} must be sha256:<64 hex>")
    try:
        int(value[7:], 16)
    except ValueError as error:
        raise QWakeFPPipelineError(f"{field_name} must be sha256:<64 hex>") from error
    if value[7:] != value[7:].lower():
        raise QWakeFPPipelineError(f"{field_name} must use lowercase hex")


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
