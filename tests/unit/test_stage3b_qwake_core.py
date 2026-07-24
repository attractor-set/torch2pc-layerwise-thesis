"""Unit and property-style guards for the pure QWake QW-1 contract."""

from __future__ import annotations

import ast
from itertools import chain
from pathlib import Path

import pytest

from torch2pc_thesis.stage3b_qwake_core import (
    ROLE_CAPABILITY_ALLOWLIST,
    AdmissionProposal,
    AnalyticClass,
    AnalyticOutcome,
    AnalyticResult,
    CampaignRole,
    Capability,
    DecisionCost,
    EdgeMeasurement,
    ExecutionContext,
    FrontierAction,
    FrontierActionKind,
    FrontierState,
    ObservationLevel,
    ObservationSnapshot,
    OracleLabel,
    PermissionSet,
    Provenance,
    QWakeContractError,
    QWakePermissionError,
    QWakeTransitionError,
    ReceiptKind,
    ReceiptReference,
    TerminalOutcome,
    evaluate_admission,
    replay_admitted_decisions,
    transition_frontier,
)

SHA_A = "sha256:" + "a" * 64
SHA_B = "sha256:" + "b" * 64
SHA_C = "sha256:" + "c" * 64
SHA_D = "sha256:" + "d" * 64
SHA_E = "sha256:" + "e" * 64
COMMIT = "1" * 40


def _provenance() -> Provenance:
    return Provenance(
        schema_version=1,
        source_identity="unit-test",
        request_sha256=SHA_A,
        manifest_sha256=SHA_B,
    )


def _receipts(*kinds: ReceiptKind) -> tuple[ReceiptReference, ...]:
    digests = (SHA_A, SHA_B, SHA_C)
    return tuple(
        ReceiptReference(kind=kind, sha256=digests[index])
        for index, kind in enumerate(kinds)
    )


def _context(
    role: CampaignRole,
    capabilities: frozenset[Capability],
) -> ExecutionContext:
    receipts_by_role: dict[CampaignRole, tuple[ReceiptReference, ...]] = {
        CampaignRole.C1_COLLECTION: (),
        CampaignRole.C2_CALIBRATION: _receipts(ReceiptKind.C1_COLLECTION),
        CampaignRole.C3_CONFIRMATORY: _receipts(
            ReceiptKind.C1_COLLECTION,
            ReceiptKind.C2_POLICY_FREEZE,
        ),
        CampaignRole.R_REPLICATION: _receipts(
            ReceiptKind.C1_COLLECTION,
            ReceiptKind.C2_POLICY_FREEZE,
            ReceiptKind.C3_CONFIRMATORY,
        ),
    }
    receipts = receipts_by_role[role]
    return ExecutionContext(
        role=role,
        permissions=PermissionSet(role=role, capabilities=capabilities),
        source_commit=COMMIT,
        image_digest=SHA_A,
        request_sha256=SHA_B,
        manifest_sha256=SHA_C,
        code_manifest_sha256=SHA_D,
        receipts=receipts,
        policy_manifest_sha256=(
            SHA_E
            if role in {CampaignRole.C3_CONFIRMATORY, CampaignRole.R_REPLICATION}
            else None
        ),
    )


def _state(level: ObservationLevel = ObservationLevel.A0) -> FrontierState:
    return FrontierState(
        snapshot_id="snapshot-0",
        compute_step=0,
        observation_level=level,
        analytic_history=(),
        provenance=_provenance(),
    )


def _proposal(action: FrontierAction) -> AdmissionProposal:
    return AdmissionProposal(
        action=action,
        rationale="unit-test proposal",
        evidence_sha256=SHA_E,
    )


def test_qwake_core_has_no_torch_or_torch2pc_runtime_dependency() -> None:
    module = __import__(
        "torch2pc_thesis.stage3b_qwake_core",
        fromlist=["stage3b_qwake_core"],
    )
    source = module.__file__
    assert source is not None
    tree = ast.parse(Path(source).read_text(encoding="utf-8"))
    imported_roots = {
        alias.name.split(".", maxsplit=1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_roots.update(
        node.module.split(".", maxsplit=1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    )
    assert "torch" not in imported_roots
    assert "torch2pc" not in imported_roots


def test_permission_defaults_are_deny_all_for_every_role() -> None:
    for role in CampaignRole:
        permissions = PermissionSet.deny_all(role)
        assert permissions.capabilities == frozenset()
        for capability in Capability:
            assert not permissions.permits(capability)


def test_every_non_allowlisted_role_capability_pair_is_rejected() -> None:
    for role in CampaignRole:
        allowed = ROLE_CAPABILITY_ALLOWLIST[role]
        for capability in Capability:
            if capability in allowed:
                PermissionSet(role=role, capabilities=frozenset({capability}))
            else:
                with pytest.raises(QWakePermissionError):
                    PermissionSet(role=role, capabilities=frozenset({capability}))


def test_c2_allowlist_is_exactly_offline_only() -> None:
    expected = frozenset(
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
    assert ROLE_CAPABILITY_ALLOWLIST[CampaignRole.C2_CALIBRATION] == expected


def test_unknown_capability_and_role_values_fail_closed() -> None:
    with pytest.raises(QWakeContractError, match="unknown capability"):
        PermissionSet(  # type: ignore[arg-type]
            role=CampaignRole.C1_COLLECTION,
            capabilities=frozenset({"COLLECT_A0"}),
        )
    with pytest.raises(QWakeContractError, match="CampaignRole"):
        PermissionSet(role="C1_COLLECTION")  # type: ignore[arg-type]


def test_execution_context_requires_role_matching_permissions() -> None:
    with pytest.raises(QWakePermissionError, match="differs"):
        ExecutionContext(
            role=CampaignRole.C1_COLLECTION,
            permissions=PermissionSet.deny_all(CampaignRole.C2_CALIBRATION),
            source_commit=COMMIT,
            image_digest=SHA_A,
            request_sha256=SHA_B,
            manifest_sha256=SHA_C,
            code_manifest_sha256=SHA_D,
        )


def test_receipt_chain_is_required_by_role() -> None:
    with pytest.raises(QWakePermissionError, match="C1_COLLECTION"):
        ExecutionContext(
            role=CampaignRole.C2_CALIBRATION,
            permissions=PermissionSet.deny_all(CampaignRole.C2_CALIBRATION),
            source_commit=COMMIT,
            image_digest=SHA_A,
            request_sha256=SHA_B,
            manifest_sha256=SHA_C,
            code_manifest_sha256=SHA_D,
        )

    with pytest.raises(QWakePermissionError, match="C2_POLICY_FREEZE"):
        ExecutionContext(
            role=CampaignRole.C3_CONFIRMATORY,
            permissions=PermissionSet.deny_all(CampaignRole.C3_CONFIRMATORY),
            source_commit=COMMIT,
            image_digest=SHA_A,
            request_sha256=SHA_B,
            manifest_sha256=SHA_C,
            code_manifest_sha256=SHA_D,
            receipts=_receipts(ReceiptKind.C1_COLLECTION),
            policy_manifest_sha256=SHA_E,
        )

    with pytest.raises(QWakePermissionError, match="frozen policy"):
        ExecutionContext(
            role=CampaignRole.C3_CONFIRMATORY,
            permissions=PermissionSet.deny_all(CampaignRole.C3_CONFIRMATORY),
            source_commit=COMMIT,
            image_digest=SHA_A,
            request_sha256=SHA_B,
            manifest_sha256=SHA_C,
            code_manifest_sha256=SHA_D,
            receipts=_receipts(
                ReceiptKind.C1_COLLECTION,
                ReceiptKind.C2_POLICY_FREEZE,
            ),
        )


def test_malformed_identity_values_are_rejected() -> None:
    with pytest.raises(QWakeContractError, match="source_commit"):
        ExecutionContext(
            role=CampaignRole.C1_COLLECTION,
            permissions=PermissionSet.deny_all(CampaignRole.C1_COLLECTION),
            source_commit="short",
            image_digest=SHA_A,
            request_sha256=SHA_B,
            manifest_sha256=SHA_C,
            code_manifest_sha256=SHA_D,
        )
    with pytest.raises(QWakeContractError, match="image_digest"):
        ExecutionContext(
            role=CampaignRole.C1_COLLECTION,
            permissions=PermissionSet.deny_all(CampaignRole.C1_COLLECTION),
            source_commit=COMMIT,
            image_digest="sha256:bad",
            request_sha256=SHA_B,
            manifest_sha256=SHA_C,
            code_manifest_sha256=SHA_D,
        )


def test_c1_cannot_accept_frontier_and_missing_permissions_reject_admission() -> None:
    proposal = _proposal(FrontierAction(kind=FrontierActionKind.ACCEPT_FRONTIER))
    c1 = _context(CampaignRole.C1_COLLECTION, frozenset())
    decision = evaluate_admission(c1, proposal)
    assert not decision.admitted
    assert "cannot accept" in decision.reason

    advance = _proposal(
        FrontierAction(
            kind=FrontierActionKind.ADVANCE_OBSERVATION,
            target_observation=ObservationLevel.A1,
        )
    )
    denied = evaluate_admission(c1, advance)
    assert not denied.admitted
    assert denied.required_capabilities == (Capability.COLLECT_A1,)


def test_live_action_admission_requires_effect_local_capabilities() -> None:
    context = _context(
        CampaignRole.C1_COLLECTION,
        frozenset(
            {
                Capability.COLLECT_A1,
                Capability.RUN_LIVE_ANALYTICS,
                Capability.RUN_ANALYTIC_EXACT,
                Capability.EXECUTE_FIXEDPRED,
                Capability.COMPUTE_CANONICAL_SUFFIX,
            }
        ),
    )
    actions = (
        FrontierAction(
            kind=FrontierActionKind.ADVANCE_OBSERVATION,
            target_observation=ObservationLevel.A1,
        ),
        FrontierAction(
            kind=FrontierActionKind.ADVANCE_ANALYTIC,
            analytic_id="exact-certificate",
            analytic_class=AnalyticClass.EXACT,
        ),
        FrontierAction(
            kind=FrontierActionKind.ADVANCE_COMPUTE,
            next_snapshot_id="snapshot-1",
        ),
        FrontierAction(kind=FrontierActionKind.COMPLETE_SUFFIX),
    )
    for action in actions:
        assert evaluate_admission(context, _proposal(action)).admitted


def test_c2_actions_require_only_sealed_artifacts_and_offline_replay() -> None:
    context = _context(
        CampaignRole.C2_CALIBRATION,
        frozenset(
            {
                Capability.ACCESS_SEALED_C1_ARTIFACTS,
                Capability.RUN_OFFLINE_REPLAY,
            }
        ),
    )
    actions = (
        FrontierAction(kind=FrontierActionKind.ACCEPT_FRONTIER),
        FrontierAction(
            kind=FrontierActionKind.ADVANCE_OBSERVATION,
            target_observation=ObservationLevel.A1,
        ),
        FrontierAction(
            kind=FrontierActionKind.ADVANCE_ANALYTIC,
            analytic_id="offline-exact",
            analytic_class=AnalyticClass.EXACT,
        ),
        FrontierAction(
            kind=FrontierActionKind.ADVANCE_COMPUTE,
            next_snapshot_id="snapshot-1",
        ),
        FrontierAction(kind=FrontierActionKind.COMPLETE_SUFFIX),
    )
    expected = (
        Capability.ACCESS_SEALED_C1_ARTIFACTS,
        Capability.RUN_OFFLINE_REPLAY,
    )
    for action in actions:
        decision = evaluate_admission(context, _proposal(action))
        assert decision.admitted
        assert decision.required_capabilities == expected


def test_observation_transition_is_adjacent_and_monotone() -> None:
    context = _context(
        CampaignRole.C1_COLLECTION,
        frozenset({Capability.COLLECT_A1, Capability.COLLECT_A2}),
    )
    a1_decision = evaluate_admission(
        context,
        _proposal(
            FrontierAction(
                kind=FrontierActionKind.ADVANCE_OBSERVATION,
                target_observation=ObservationLevel.A1,
            )
        ),
    )
    state_a1 = transition_frontier(_state(), a1_decision)
    assert state_a1.observation_level is ObservationLevel.A1

    a2_decision = evaluate_admission(
        context,
        _proposal(
            FrontierAction(
                kind=FrontierActionKind.ADVANCE_OBSERVATION,
                target_observation=ObservationLevel.A2,
            )
        ),
    )
    state_a2 = transition_frontier(state_a1, a2_decision)
    assert state_a2.observation_level is ObservationLevel.A2

    with pytest.raises(QWakeTransitionError, match="adjacent"):
        transition_frontier(_state(), a2_decision)


def test_compute_transition_resets_observation_and_preserves_history() -> None:
    state = FrontierState(
        snapshot_id="snapshot-0",
        compute_step=3,
        observation_level=ObservationLevel.A2,
        analytic_history=("exact-certificate",),
        provenance=_provenance(),
    )
    context = _context(
        CampaignRole.C1_COLLECTION,
        frozenset({Capability.EXECUTE_FIXEDPRED}),
    )
    decision = evaluate_admission(
        context,
        _proposal(
            FrontierAction(
                kind=FrontierActionKind.ADVANCE_COMPUTE,
                next_snapshot_id="snapshot-1",
            )
        ),
    )
    after = transition_frontier(state, decision)
    assert after.compute_step == 4
    assert after.snapshot_id == "snapshot-1"
    assert after.observation_level is ObservationLevel.A0
    assert after.analytic_history == ("exact-certificate",)


def test_analytic_history_is_append_only_and_unique() -> None:
    context = _context(
        CampaignRole.C1_COLLECTION,
        frozenset(
            {
                Capability.RUN_LIVE_ANALYTICS,
                Capability.RUN_ANALYTIC_CONSERVATIVE,
            }
        ),
    )
    decision = evaluate_admission(
        context,
        _proposal(
            FrontierAction(
                kind=FrontierActionKind.ADVANCE_ANALYTIC,
                analytic_id="bound-1",
                analytic_class=AnalyticClass.CONSERVATIVE,
            )
        ),
    )
    state = transition_frontier(_state(), decision)
    assert state.analytic_history == ("bound-1",)
    with pytest.raises(QWakeTransitionError, match="twice"):
        transition_frontier(state, decision)


def test_rejected_or_terminal_states_cannot_transition() -> None:
    denied = evaluate_admission(
        _context(CampaignRole.C1_COLLECTION, frozenset()),
        _proposal(
            FrontierAction(
                kind=FrontierActionKind.ADVANCE_OBSERVATION,
                target_observation=ObservationLevel.A1,
            )
        ),
    )
    with pytest.raises(QWakeTransitionError, match="rejected"):
        transition_frontier(_state(), denied)

    terminal = FrontierState(
        snapshot_id="snapshot-0",
        compute_step=0,
        observation_level=ObservationLevel.A0,
        analytic_history=(),
        provenance=_provenance(),
        terminal_outcome=TerminalOutcome.ACCEPTED,
    )
    with pytest.raises(QWakeTransitionError, match="terminal"):
        transition_frontier(terminal, denied)


def test_deterministic_replay_has_stable_state_and_digest() -> None:
    context = _context(
        CampaignRole.C2_CALIBRATION,
        frozenset(
            {
                Capability.ACCESS_SEALED_C1_ARTIFACTS,
                Capability.RUN_OFFLINE_REPLAY,
            }
        ),
    )
    actions = (
        FrontierAction(
            kind=FrontierActionKind.ADVANCE_OBSERVATION,
            target_observation=ObservationLevel.A1,
        ),
        FrontierAction(
            kind=FrontierActionKind.ADVANCE_ANALYTIC,
            analytic_id="offline-bound",
            analytic_class=AnalyticClass.CONSERVATIVE,
        ),
        FrontierAction(
            kind=FrontierActionKind.ADVANCE_COMPUTE,
            next_snapshot_id="snapshot-1",
        ),
        FrontierAction(kind=FrontierActionKind.ACCEPT_FRONTIER),
    )
    decisions = tuple(
        evaluate_admission(context, _proposal(action)) for action in actions
    )
    first = replay_admitted_decisions(_state(), decisions)
    second = replay_admitted_decisions(_state(), decisions)
    assert first == second
    assert first.canonical_sha256() == second.canonical_sha256()
    assert first.final_state.terminal_outcome is TerminalOutcome.ACCEPTED


def test_action_shapes_are_closed_and_validated() -> None:
    with pytest.raises(QWakeContractError, match="target level"):
        FrontierAction(kind=FrontierActionKind.ADVANCE_OBSERVATION)
    with pytest.raises(QWakeContractError, match="analytic_id"):
        FrontierAction(kind=FrontierActionKind.ADVANCE_ANALYTIC)
    with pytest.raises(QWakeContractError, match="next_snapshot_id"):
        FrontierAction(kind=FrontierActionKind.ADVANCE_COMPUTE)
    with pytest.raises(QWakeContractError, match="not valid"):
        FrontierAction(
            kind=FrontierActionKind.ACCEPT_FRONTIER,
            next_snapshot_id="unexpected",
        )


def test_oracle_labels_are_post_action_only() -> None:
    OracleLabel(
        snapshot_id="snapshot-0",
        response_sha256=SHA_A,
        defect=0.0,
        sufficient=True,
    )
    with pytest.raises(QWakeContractError, match="post-action"):
        OracleLabel(
            snapshot_id="snapshot-0",
            response_sha256=SHA_A,
            defect=0.0,
            sufficient=True,
            post_action=False,
        )


def test_cost_vectors_reject_negative_or_boolean_values() -> None:
    EdgeMeasurement(host_time_ns=1, device_time_ns=2)
    cost = DecisionCost(compute_ns=2, observer_ns=3, fallback_ns=5)
    assert cost.total_time_ns == 10
    with pytest.raises(QWakeContractError, match="non-negative integer"):
        EdgeMeasurement(d2h_bytes=-1)
    with pytest.raises(QWakeContractError, match="non-negative integer"):
        DecisionCost(control_ns=-1)
    with pytest.raises(QWakeContractError, match="non-negative integer"):
        DecisionCost(compute_ns=True)  # type: ignore[arg-type]


def test_every_capability_occurs_in_exactly_the_expected_role_allowlists() -> None:
    memberships = {
        capability: frozenset(
            role
            for role, allowlist in ROLE_CAPABILITY_ALLOWLIST.items()
            if capability in allowlist
        )
        for capability in Capability
    }
    assert memberships[Capability.SELECT_POLICY] == frozenset(
        {CampaignRole.C2_CALIBRATION}
    )
    assert memberships[Capability.ACCESS_CONFIRMATORY_DATA] == frozenset(
        {CampaignRole.C3_CONFIRMATORY}
    )
    assert memberships[Capability.RETUNE_POLICY] == frozenset()
    assert memberships[Capability.PUBLISH_RESULTS] == frozenset()
    assert set(chain.from_iterable(ROLE_CAPABILITY_ALLOWLIST.values())) <= set(Capability)


def test_observation_and_analytic_records_bind_snapshot_and_provenance() -> None:
    measurement = EdgeMeasurement(host_time_ns=3, trace_bytes=7)
    observation = ObservationSnapshot(
        snapshot_id="snapshot-0",
        compute_step=0,
        level=ObservationLevel.A1,
        payload_sha256=SHA_C,
        measurement=measurement,
        provenance=_provenance(),
    )
    analytic = AnalyticResult(
        analytic_id="exact-certificate",
        snapshot_id=observation.snapshot_id,
        analytic_class=AnalyticClass.EXACT,
        outcome=AnalyticOutcome.CERTIFIED_CONTINUE,
        payload_sha256=SHA_D,
        measurement=measurement,
        provenance=observation.provenance,
    )
    assert observation.level is ObservationLevel.A1
    assert analytic.snapshot_id == observation.snapshot_id
    assert analytic.provenance == observation.provenance


def test_qw1_status_and_roadmap_remain_synchronized() -> None:
    root = Path(__file__).resolve().parents[2]
    required = (
        "qwake_core_contract_implemented=true",
        "qwake_permission_default=deny_all",
        "qwake_scientific_execution_open=false",
        "qwake_next_stage=QW-2",
    )
    for name in ("STATUS.md", "STATUS_EN.md"):
        text = (root / name).read_text(encoding="utf-8")
        for token in required:
            assert token in text, (name, token)
    for name in ("ROADMAP.md", "ROADMAP_EN.md"):
        text = (root / name).read_text(encoding="utf-8")
        assert "QW-1" in text
        assert "QW-2" in text
        assert "deny" in text.lower() or "запрещ" in text.lower()
