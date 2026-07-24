"""Pure QWake state, permission, admission, and replay contracts.

This module deliberately has no Torch, Torch2PC, filesystem, subprocess, or GPU
imports.  It defines the QW-1 contract only; it does not open any scientific
execution capability.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Final, Self

_SHA256_PATTERN: Final[re.Pattern[str]] = re.compile(r"^sha256:[0-9a-f]{64}$")
_COMMIT_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[0-9a-f]{40}$")


class QWakeContractError(ValueError):
    """Raised when a pure QWake contract is malformed or violated."""


class QWakePermissionError(QWakeContractError):
    """Raised when a capability is not permitted by the execution context."""


class QWakeTransitionError(QWakeContractError):
    """Raised when a frontier transition violates the pure state contract."""


class ObservationLevel(StrEnum):
    """Deployable nested observation levels."""

    A0 = "A0"
    A1 = "A1"
    A2 = "A2"

    def next_level(self) -> ObservationLevel | None:
        return {
            ObservationLevel.A0: ObservationLevel.A1,
            ObservationLevel.A1: ObservationLevel.A2,
            ObservationLevel.A2: None,
        }[self]


class AnalyticClass(StrEnum):
    """Frozen analytic classes used by the general QWake contract."""

    EXACT = "exact"
    CONSERVATIVE = "conservative"
    HEURISTIC = "heuristic"


class AnalyticOutcome(StrEnum):
    """Outcome reported by one registered analytic step."""

    CERTIFIED_ACCEPT = "certified_accept"
    CERTIFIED_CONTINUE = "certified_continue"
    UNRESOLVED = "unresolved"


class FrontierActionKind(StrEnum):
    """Finite QWake frontier action registry."""

    ACCEPT_FRONTIER = "accept_frontier"
    ADVANCE_OBSERVATION = "advance_observation"
    ADVANCE_ANALYTIC = "advance_analytic"
    ADVANCE_COMPUTE = "advance_compute"
    COMPLETE_SUFFIX = "complete_suffix"


class TerminalOutcome(StrEnum):
    """Terminal frontier outcomes."""

    ACCEPTED = "accepted"
    SUFFIX_COMPLETED = "suffix_completed"


class CampaignRole(StrEnum):
    """Protocol roles frozen by ADR-042."""

    C1_COLLECTION = "C1_COLLECTION"
    C2_CALIBRATION = "C2_CALIBRATION"
    C3_CONFIRMATORY = "C3_CONFIRMATORY"
    R_REPLICATION = "R_REPLICATION"


class Capability(StrEnum):
    """Closed capability registry for the QWake superset image."""

    COLLECT_A0 = "COLLECT_A0"
    COLLECT_A1 = "COLLECT_A1"
    COLLECT_A2 = "COLLECT_A2"
    RUN_ANALYTIC_EXACT = "RUN_ANALYTIC_EXACT"
    RUN_ANALYTIC_CONSERVATIVE = "RUN_ANALYTIC_CONSERVATIVE"
    RUN_ANALYTIC_HEURISTIC = "RUN_ANALYTIC_HEURISTIC"
    RUN_COST_DOMINANCE_CHECK = "RUN_COST_DOMINANCE_CHECK"
    COMPUTE_CANONICAL_SUFFIX = "COMPUTE_CANONICAL_SUFFIX"
    COMPUTE_POST_ACTION_ORACLE = "COMPUTE_POST_ACTION_ORACLE"
    COMPUTE_NEW_ORACLE_LABELS = "COMPUTE_NEW_ORACLE_LABELS"
    EXECUTE_FIXEDPRED = "EXECUTE_FIXEDPRED"
    RUN_LIVE_ANALYTICS = "RUN_LIVE_ANALYTICS"
    ACCESS_DESIGN_DATA = "ACCESS_DESIGN_DATA"
    ACCESS_CALIBRATION_DATA = "ACCESS_CALIBRATION_DATA"
    ACCESS_CONFIRMATORY_DATA = "ACCESS_CONFIRMATORY_DATA"
    ACCESS_REPLICATION_DATA = "ACCESS_REPLICATION_DATA"
    ACCESS_SEALED_C1_ARTIFACTS = "ACCESS_SEALED_C1_ARTIFACTS"
    RUN_OFFLINE_REPLAY = "RUN_OFFLINE_REPLAY"
    RUN_OPPORTUNITY_ANALYSIS = "RUN_OPPORTUNITY_ANALYSIS"
    RUN_RECOGNIZABILITY_ANALYSIS = "RUN_RECOGNIZABILITY_ANALYSIS"
    EVALUATE_BASELINES = "EVALUATE_BASELINES"
    SELECT_POLICY = "SELECT_POLICY"
    FREEZE_POLICY = "FREEZE_POLICY"
    LOAD_FROZEN_POLICY = "LOAD_FROZEN_POLICY"
    RETUNE_POLICY = "RETUNE_POLICY"
    EXECUTE_SHADOW_POLICY = "EXECUTE_SHADOW_POLICY"
    EVALUATE_CONFIRMATORY = "EVALUATE_CONFIRMATORY"
    EVALUATE_REPLICATION = "EVALUATE_REPLICATION"
    SEAL_EVIDENCE = "SEAL_EVIDENCE"
    PUBLISH_RESULTS = "PUBLISH_RESULTS"


class ReceiptKind(StrEnum):
    """Sealed receipt kinds needed to open later protocol roles."""

    C1_COLLECTION = "C1_COLLECTION"
    C2_POLICY_FREEZE = "C2_POLICY_FREEZE"
    C3_CONFIRMATORY = "C3_CONFIRMATORY"


_ANALYTIC_CAPABILITY: Final[Mapping[AnalyticClass, Capability]] = {
    AnalyticClass.EXACT: Capability.RUN_ANALYTIC_EXACT,
    AnalyticClass.CONSERVATIVE: Capability.RUN_ANALYTIC_CONSERVATIVE,
    AnalyticClass.HEURISTIC: Capability.RUN_ANALYTIC_HEURISTIC,
}

_C1_CAPABILITIES: Final[frozenset[Capability]] = frozenset(
    {
        Capability.COLLECT_A0,
        Capability.COLLECT_A1,
        Capability.COLLECT_A2,
        Capability.RUN_ANALYTIC_EXACT,
        Capability.RUN_ANALYTIC_CONSERVATIVE,
        Capability.RUN_ANALYTIC_HEURISTIC,
        Capability.RUN_COST_DOMINANCE_CHECK,
        Capability.COMPUTE_CANONICAL_SUFFIX,
        Capability.COMPUTE_POST_ACTION_ORACLE,
        Capability.COMPUTE_NEW_ORACLE_LABELS,
        Capability.EXECUTE_FIXEDPRED,
        Capability.RUN_LIVE_ANALYTICS,
        Capability.ACCESS_DESIGN_DATA,
        Capability.ACCESS_CALIBRATION_DATA,
        Capability.RUN_OPPORTUNITY_ANALYSIS,
        Capability.SEAL_EVIDENCE,
    }
)

_C2_CAPABILITIES: Final[frozenset[Capability]] = frozenset(
    {
        Capability.ACCESS_SEALED_C1_ARTIFACTS,
        Capability.RUN_OFFLINE_REPLAY,
        Capability.RUN_RECOGNIZABILITY_ANALYSIS,
        Capability.EVALUATE_BASELINES,
        Capability.SELECT_POLICY,
        Capability.FREEZE_POLICY,
        Capability.SEAL_EVIDENCE,
    }
)

_C3_CAPABILITIES: Final[frozenset[Capability]] = frozenset(
    {
        Capability.COLLECT_A0,
        Capability.COLLECT_A1,
        Capability.COLLECT_A2,
        Capability.RUN_ANALYTIC_EXACT,
        Capability.RUN_ANALYTIC_CONSERVATIVE,
        Capability.RUN_ANALYTIC_HEURISTIC,
        Capability.RUN_COST_DOMINANCE_CHECK,
        Capability.COMPUTE_CANONICAL_SUFFIX,
        Capability.COMPUTE_POST_ACTION_ORACLE,
        Capability.COMPUTE_NEW_ORACLE_LABELS,
        Capability.EXECUTE_FIXEDPRED,
        Capability.RUN_LIVE_ANALYTICS,
        Capability.ACCESS_CONFIRMATORY_DATA,
        Capability.LOAD_FROZEN_POLICY,
        Capability.EXECUTE_SHADOW_POLICY,
        Capability.EVALUATE_CONFIRMATORY,
        Capability.SEAL_EVIDENCE,
    }
)

_R_CAPABILITIES: Final[frozenset[Capability]] = frozenset(
    {
        Capability.COLLECT_A0,
        Capability.COLLECT_A1,
        Capability.COLLECT_A2,
        Capability.RUN_ANALYTIC_EXACT,
        Capability.RUN_ANALYTIC_CONSERVATIVE,
        Capability.RUN_ANALYTIC_HEURISTIC,
        Capability.RUN_COST_DOMINANCE_CHECK,
        Capability.COMPUTE_CANONICAL_SUFFIX,
        Capability.COMPUTE_POST_ACTION_ORACLE,
        Capability.COMPUTE_NEW_ORACLE_LABELS,
        Capability.EXECUTE_FIXEDPRED,
        Capability.RUN_LIVE_ANALYTICS,
        Capability.ACCESS_REPLICATION_DATA,
        Capability.LOAD_FROZEN_POLICY,
        Capability.EXECUTE_SHADOW_POLICY,
        Capability.EVALUATE_REPLICATION,
        Capability.SEAL_EVIDENCE,
    }
)

ROLE_CAPABILITY_ALLOWLIST: Final[Mapping[CampaignRole, frozenset[Capability]]] = {
    CampaignRole.C1_COLLECTION: _C1_CAPABILITIES,
    CampaignRole.C2_CALIBRATION: _C2_CAPABILITIES,
    CampaignRole.C3_CONFIRMATORY: _C3_CAPABILITIES,
    CampaignRole.R_REPLICATION: _R_CAPABILITIES,
}

ROLE_REQUIRED_RECEIPTS: Final[Mapping[CampaignRole, frozenset[ReceiptKind]]] = {
    CampaignRole.C1_COLLECTION: frozenset(),
    CampaignRole.C2_CALIBRATION: frozenset({ReceiptKind.C1_COLLECTION}),
    CampaignRole.C3_CONFIRMATORY: frozenset(
        {ReceiptKind.C1_COLLECTION, ReceiptKind.C2_POLICY_FREEZE}
    ),
    CampaignRole.R_REPLICATION: frozenset(
        {
            ReceiptKind.C1_COLLECTION,
            ReceiptKind.C2_POLICY_FREEZE,
            ReceiptKind.C3_CONFIRMATORY,
        }
    ),
}


@dataclass(frozen=True)
class Provenance:
    """Stable identity carried by pure QWake records."""

    schema_version: int
    source_identity: str
    request_sha256: str
    manifest_sha256: str

    def __post_init__(self) -> None:
        if self.schema_version < 1:
            raise QWakeContractError("provenance schema_version must be positive")
        _require_nonempty(self.source_identity, field_name="source_identity")
        _require_sha256(self.request_sha256, field_name="request_sha256")
        _require_sha256(self.manifest_sha256, field_name="manifest_sha256")


@dataclass(frozen=True)
class EdgeMeasurement:
    """Measured cost of one frontier edge."""

    host_time_ns: int = 0
    device_time_ns: int = 0
    synchronization_count: int = 0
    d2h_bytes: int = 0
    temporary_memory_bytes: int = 0
    trace_bytes: int = 0

    def __post_init__(self) -> None:
        _require_nonnegative_ints(asdict(self))


@dataclass(frozen=True)
class DecisionCost:
    """Decision-facing cost vector kept separate from raw edge measurement."""

    compute_ns: int = 0
    latency_ns: int = 0
    memory_bytes: int = 0
    diagnostic_ns: int = 0
    observer_ns: int = 0
    control_ns: int = 0
    fallback_ns: int = 0

    def __post_init__(self) -> None:
        _require_nonnegative_ints(asdict(self))

    @property
    def total_time_ns(self) -> int:
        return (
            self.compute_ns
            + self.latency_ns
            + self.diagnostic_ns
            + self.observer_ns
            + self.control_ns
            + self.fallback_ns
        )


@dataclass(frozen=True)
class ObservationSnapshot:
    """One immutable pre-action observation at a frontier snapshot."""

    snapshot_id: str
    compute_step: int
    level: ObservationLevel
    payload_sha256: str
    measurement: EdgeMeasurement
    provenance: Provenance

    def __post_init__(self) -> None:
        _require_nonempty(self.snapshot_id, field_name="snapshot_id")
        if self.compute_step < 0:
            raise QWakeContractError("compute_step must be non-negative")
        _require_sha256(self.payload_sha256, field_name="payload_sha256")


@dataclass(frozen=True)
class AnalyticResult:
    """One immutable output from a registered analytic step."""

    analytic_id: str
    snapshot_id: str
    analytic_class: AnalyticClass
    outcome: AnalyticOutcome
    payload_sha256: str
    measurement: EdgeMeasurement
    provenance: Provenance

    def __post_init__(self) -> None:
        _require_nonempty(self.analytic_id, field_name="analytic_id")
        _require_nonempty(self.snapshot_id, field_name="snapshot_id")
        _require_sha256(self.payload_sha256, field_name="payload_sha256")


@dataclass(frozen=True)
class OracleLabel:
    """Post-action task-relative oracle label.

    The contract rejects any attempt to represent an oracle label as a
    pre-action feature.
    """

    snapshot_id: str
    response_sha256: str
    defect: float
    sufficient: bool
    post_action: bool = True

    def __post_init__(self) -> None:
        _require_nonempty(self.snapshot_id, field_name="snapshot_id")
        _require_sha256(self.response_sha256, field_name="response_sha256")
        if self.defect < 0:
            raise QWakeContractError("oracle defect must be non-negative")
        if not self.post_action:
            raise QWakeContractError("oracle labels must remain post-action")


@dataclass(frozen=True)
class FrontierState:
    """Pure immutable state of the QWake frontier."""

    snapshot_id: str
    compute_step: int
    observation_level: ObservationLevel
    analytic_history: tuple[str, ...]
    provenance: Provenance
    terminal_outcome: TerminalOutcome | None = None

    def __post_init__(self) -> None:
        _require_nonempty(self.snapshot_id, field_name="snapshot_id")
        if self.compute_step < 0:
            raise QWakeContractError("compute_step must be non-negative")
        if len(self.analytic_history) != len(set(self.analytic_history)):
            raise QWakeContractError("analytic_history cannot contain duplicates")
        for analytic_id in self.analytic_history:
            _require_nonempty(analytic_id, field_name="analytic_history entry")

    @property
    def is_terminal(self) -> bool:
        return self.terminal_outcome is not None


@dataclass(frozen=True)
class FrontierAction:
    """One finite action proposal at the QWake frontier."""

    kind: FrontierActionKind
    target_observation: ObservationLevel | None = None
    analytic_id: str | None = None
    analytic_class: AnalyticClass | None = None
    next_snapshot_id: str | None = None

    def __post_init__(self) -> None:
        if self.kind is FrontierActionKind.ADVANCE_OBSERVATION:
            if self.target_observation is None:
                raise QWakeContractError("observation advance requires a target level")
            self._require_absent("analytic_id", self.analytic_id)
            self._require_absent("analytic_class", self.analytic_class)
            self._require_absent("next_snapshot_id", self.next_snapshot_id)
        elif self.kind is FrontierActionKind.ADVANCE_ANALYTIC:
            if self.analytic_id is None or self.analytic_class is None:
                raise QWakeContractError(
                    "analytic advance requires analytic_id and analytic_class"
                )
            _require_nonempty(self.analytic_id, field_name="analytic_id")
            self._require_absent("target_observation", self.target_observation)
            self._require_absent("next_snapshot_id", self.next_snapshot_id)
        elif self.kind is FrontierActionKind.ADVANCE_COMPUTE:
            if self.next_snapshot_id is None:
                raise QWakeContractError("compute advance requires next_snapshot_id")
            _require_nonempty(self.next_snapshot_id, field_name="next_snapshot_id")
            self._require_absent("target_observation", self.target_observation)
            self._require_absent("analytic_id", self.analytic_id)
            self._require_absent("analytic_class", self.analytic_class)
        else:
            self._require_absent("target_observation", self.target_observation)
            self._require_absent("analytic_id", self.analytic_id)
            self._require_absent("analytic_class", self.analytic_class)
            self._require_absent("next_snapshot_id", self.next_snapshot_id)

    @staticmethod
    def _require_absent(field_name: str, value: object | None) -> None:
        if value is not None:
            raise QWakeContractError(f"{field_name} is not valid for this action")


@dataclass(frozen=True)
class AdmissionProposal:
    """A policy proposal that has not yet crossed the permission boundary."""

    action: FrontierAction
    rationale: str
    evidence_sha256: str

    def __post_init__(self) -> None:
        _require_nonempty(self.rationale, field_name="rationale")
        _require_sha256(self.evidence_sha256, field_name="evidence_sha256")


@dataclass(frozen=True)
class AdmissionDecision:
    """Fail-closed result of applying permissions to one proposal."""

    proposal: AdmissionProposal
    admitted: bool
    reason: str
    required_capabilities: tuple[Capability, ...]

    def __post_init__(self) -> None:
        _require_nonempty(self.reason, field_name="reason")
        if len(self.required_capabilities) != len(set(self.required_capabilities)):
            raise QWakeContractError("required_capabilities cannot contain duplicates")


@dataclass(frozen=True)
class ReceiptReference:
    """Reference to one previously sealed protocol receipt."""

    kind: ReceiptKind
    sha256: str

    def __post_init__(self) -> None:
        _require_sha256(self.sha256, field_name="receipt sha256")


@dataclass(frozen=True)
class PermissionSet:
    """Role-bound capability set with deny-all defaults."""

    role: CampaignRole
    capabilities: frozenset[Capability] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if not isinstance(self.role, CampaignRole):
            raise QWakeContractError("permission role must be a CampaignRole")
        for capability in self.capabilities:
            if not isinstance(capability, Capability):
                raise QWakeContractError("permissions contain an unknown capability")
        allowed = ROLE_CAPABILITY_ALLOWLIST[self.role]
        forbidden = self.capabilities - allowed
        if forbidden:
            names = ", ".join(sorted(capability.value for capability in forbidden))
            raise QWakePermissionError(
                f"capabilities are forbidden for {self.role.value}: {names}"
            )

    @classmethod
    def deny_all(cls, role: CampaignRole) -> Self:
        """Construct an explicit fail-closed role context."""

        return cls(role=role)

    def permits(self, capability: Capability) -> bool:
        return capability in self.capabilities

    def require(self, *capabilities: Capability) -> None:
        missing = tuple(
            capability
            for capability in capabilities
            if capability not in self.capabilities
        )
        if missing:
            names = ", ".join(capability.value for capability in missing)
            raise QWakePermissionError(
                f"missing capabilities for {self.role.value}: {names}"
            )


@dataclass(frozen=True)
class ExecutionContext:
    """Pure role, identity, permission, and receipt binding."""

    role: CampaignRole
    permissions: PermissionSet
    source_commit: str
    image_digest: str
    request_sha256: str
    manifest_sha256: str
    code_manifest_sha256: str
    receipts: tuple[ReceiptReference, ...] = ()
    policy_manifest_sha256: str | None = None

    def __post_init__(self) -> None:
        if self.permissions.role is not self.role:
            raise QWakePermissionError("execution role differs from permission role")
        if not _COMMIT_PATTERN.fullmatch(self.source_commit):
            raise QWakeContractError("source_commit must be an exact 40-character hash")
        _require_sha256(self.image_digest, field_name="image_digest")
        _require_sha256(self.request_sha256, field_name="request_sha256")
        _require_sha256(self.manifest_sha256, field_name="manifest_sha256")
        _require_sha256(
            self.code_manifest_sha256,
            field_name="code_manifest_sha256",
        )
        receipt_kinds = tuple(receipt.kind for receipt in self.receipts)
        if len(receipt_kinds) != len(set(receipt_kinds)):
            raise QWakeContractError("receipt kinds cannot be duplicated")
        required = ROLE_REQUIRED_RECEIPTS[self.role]
        missing = required - set(receipt_kinds)
        if missing:
            names = ", ".join(sorted(kind.value for kind in missing))
            raise QWakePermissionError(
                f"missing sealed receipts for {self.role.value}: {names}"
            )
        if self.role in {
            CampaignRole.C3_CONFIRMATORY,
            CampaignRole.R_REPLICATION,
        }:
            if self.policy_manifest_sha256 is None:
                raise QWakePermissionError(
                    f"{self.role.value} requires a frozen policy manifest"
                )
            _require_sha256(
                self.policy_manifest_sha256,
                field_name="policy_manifest_sha256",
            )
        elif self.policy_manifest_sha256 is not None:
            _require_sha256(
                self.policy_manifest_sha256,
                field_name="policy_manifest_sha256",
            )


@dataclass(frozen=True)
class ReplayStep:
    """One deterministic replay result."""

    before: FrontierState
    decision: AdmissionDecision
    after: FrontierState


@dataclass(frozen=True)
class ReplayTrace:
    """Immutable deterministic replay trace."""

    initial_state: FrontierState
    steps: tuple[ReplayStep, ...]

    @property
    def final_state(self) -> FrontierState:
        return self.steps[-1].after if self.steps else self.initial_state

    def canonical_sha256(self) -> str:
        payload = _canonicalize(asdict(self))
        encoded = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
        return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def evaluate_admission(
    context: ExecutionContext,
    proposal: AdmissionProposal,
) -> AdmissionDecision:
    """Apply role-local capability requirements without executing an effect."""

    required: tuple[Capability, ...] = ()
    try:
        required = required_capabilities_for_action(context.role, proposal.action)
        context.permissions.require(*required)
    except QWakePermissionError as error:
        return AdmissionDecision(
            proposal=proposal,
            admitted=False,
            reason=str(error),
            required_capabilities=required,
        )
    return AdmissionDecision(
        proposal=proposal,
        admitted=True,
        reason="permission contract satisfied",
        required_capabilities=required,
    )


def required_capabilities_for_action(
    role: CampaignRole,
    action: FrontierAction,
) -> tuple[Capability, ...]:
    """Return the closed role-local capability requirements for an action."""

    if role is CampaignRole.C2_CALIBRATION:
        return (
            Capability.ACCESS_SEALED_C1_ARTIFACTS,
            Capability.RUN_OFFLINE_REPLAY,
        )

    if action.kind is FrontierActionKind.ACCEPT_FRONTIER:
        if role is CampaignRole.C1_COLLECTION:
            raise QWakePermissionError("C1_COLLECTION cannot accept a policy frontier")
        return (Capability.EXECUTE_SHADOW_POLICY,)

    if action.kind is FrontierActionKind.ADVANCE_OBSERVATION:
        target_observation = action.target_observation
        if target_observation is None:
            raise QWakePermissionError("observation action has no target level")
        capability = {
            ObservationLevel.A0: Capability.COLLECT_A0,
            ObservationLevel.A1: Capability.COLLECT_A1,
            ObservationLevel.A2: Capability.COLLECT_A2,
        }[target_observation]
        return (capability,)

    if action.kind is FrontierActionKind.ADVANCE_ANALYTIC:
        analytic_class = action.analytic_class
        if analytic_class is None:
            raise QWakePermissionError("analytic action has no analytic class")
        return (
            Capability.RUN_LIVE_ANALYTICS,
            _ANALYTIC_CAPABILITY[analytic_class],
        )

    if action.kind is FrontierActionKind.ADVANCE_COMPUTE:
        return (Capability.EXECUTE_FIXEDPRED,)

    if action.kind is FrontierActionKind.COMPLETE_SUFFIX:
        return (Capability.COMPUTE_CANONICAL_SUFFIX,)

    raise QWakePermissionError(f"unsupported frontier action: {action.kind}")


def transition_frontier(
    state: FrontierState,
    decision: AdmissionDecision,
) -> FrontierState:
    """Apply one admitted action as a deterministic pure state transition."""

    if state.is_terminal:
        raise QWakeTransitionError("terminal frontier states cannot transition")
    if not decision.admitted:
        raise QWakeTransitionError("rejected admission decisions cannot transition")

    action = decision.proposal.action
    if action.kind is FrontierActionKind.ACCEPT_FRONTIER:
        return FrontierState(
            snapshot_id=state.snapshot_id,
            compute_step=state.compute_step,
            observation_level=state.observation_level,
            analytic_history=state.analytic_history,
            provenance=state.provenance,
            terminal_outcome=TerminalOutcome.ACCEPTED,
        )

    if action.kind is FrontierActionKind.COMPLETE_SUFFIX:
        return FrontierState(
            snapshot_id=state.snapshot_id,
            compute_step=state.compute_step,
            observation_level=state.observation_level,
            analytic_history=state.analytic_history,
            provenance=state.provenance,
            terminal_outcome=TerminalOutcome.SUFFIX_COMPLETED,
        )

    if action.kind is FrontierActionKind.ADVANCE_OBSERVATION:
        target_observation = action.target_observation
        if target_observation is None:
            raise QWakeTransitionError("observation action has no target level")
        expected = state.observation_level.next_level()
        if target_observation is not expected:
            raise QWakeTransitionError(
                "observation transitions must be adjacent and monotone within a snapshot"
            )
        return FrontierState(
            snapshot_id=state.snapshot_id,
            compute_step=state.compute_step,
            observation_level=target_observation,
            analytic_history=state.analytic_history,
            provenance=state.provenance,
        )

    if action.kind is FrontierActionKind.ADVANCE_ANALYTIC:
        analytic_id = action.analytic_id
        if analytic_id is None:
            raise QWakeTransitionError("analytic action has no analytic id")
        if analytic_id in state.analytic_history:
            raise QWakeTransitionError("an analytic step cannot be acquired twice")
        return FrontierState(
            snapshot_id=state.snapshot_id,
            compute_step=state.compute_step,
            observation_level=state.observation_level,
            analytic_history=(*state.analytic_history, analytic_id),
            provenance=state.provenance,
        )

    if action.kind is FrontierActionKind.ADVANCE_COMPUTE:
        next_snapshot_id = action.next_snapshot_id
        if next_snapshot_id is None:
            raise QWakeTransitionError("compute action has no next snapshot id")
        if next_snapshot_id == state.snapshot_id:
            raise QWakeTransitionError("compute advance requires a new snapshot id")
        return FrontierState(
            snapshot_id=next_snapshot_id,
            compute_step=state.compute_step + 1,
            observation_level=ObservationLevel.A0,
            analytic_history=state.analytic_history,
            provenance=state.provenance,
        )

    raise QWakeTransitionError(f"unsupported frontier action: {action.kind}")


def replay_admitted_decisions(
    initial_state: FrontierState,
    decisions: Sequence[AdmissionDecision],
) -> ReplayTrace:
    """Replay an immutable sequence of admitted decisions deterministically."""

    state = initial_state
    steps: list[ReplayStep] = []
    for decision in decisions:
        next_state = transition_frontier(state, decision)
        steps.append(ReplayStep(before=state, decision=decision, after=next_state))
        state = next_state
    return ReplayTrace(initial_state=initial_state, steps=tuple(steps))


def capability_names(capabilities: Iterable[Capability]) -> tuple[str, ...]:
    """Return a deterministic presentation order for a capability set."""

    return tuple(sorted(capability.value for capability in capabilities))


def _require_nonempty(value: str, *, field_name: str) -> None:
    if not value.strip():
        raise QWakeContractError(f"{field_name} must be non-empty")


def _require_sha256(value: str, *, field_name: str) -> None:
    if not _SHA256_PATTERN.fullmatch(value):
        raise QWakeContractError(f"{field_name} must be sha256:<64 lowercase hex>")


def _require_nonnegative_ints(values: Mapping[str, object]) -> None:
    for field_name, value in values.items():
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise QWakeContractError(f"{field_name} must be a non-negative integer")


def _canonicalize(value: object) -> object:
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, Mapping):
        return {
            str(key): _canonicalize(item)
            for key, item in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, tuple | list):
        return [_canonicalize(item) for item in value]
    return value
