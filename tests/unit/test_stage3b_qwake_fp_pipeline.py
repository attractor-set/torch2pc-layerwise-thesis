"""Unit and property-style guards for the QW-3 superset pipeline."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from torch2pc_thesis.stage3b_qwake_core import (
    AnalyticOutcome,
    CampaignRole,
    Capability,
    EdgeMeasurement,
    ExecutionContext,
    FrontierAction,
    FrontierActionKind,
    ObservationLevel,
    OracleLabel,
    PermissionSet,
    Provenance,
    QWakePermissionError,
    ReceiptKind,
    ReceiptReference,
)
from torch2pc_thesis.stage3b_qwake_fp_pipeline import (
    ABLATION_REGISTRY,
    BASELINE_REGISTRY,
    COMPONENT_REGISTRY,
    BaselineConfiguration,
    CostCategory,
    EvaluationClass,
    FrozenAnalyticOutput,
    FrozenPolicyManifest,
    MeasuredEdge,
    PipelineComponentId,
    PipelinePhase,
    PolicyPredicateKind,
    PolicyRule,
    QWakeFPAblationId,
    QWakeFPPipelineError,
    SealedTrajectoryDataset,
    TrajectorySnapshotRecord,
    aggregate_decision_cost,
    analyze_opportunity,
    apply_ablation,
    build_feature_vector,
    evaluate_baseline,
    evaluate_policy,
    interpret_policy,
    plan_component,
    render_publication_bundle,
    seal_payload,
)
from torch2pc_thesis.stage3b_qwake_fp_spec import (
    A0_FIELDS,
    A1_FIELDS,
    A2_FIELDS,
    QWAKE_FP_SPECIAL_CASE_CONTRACT,
    QWakeFPAnalyticId,
    QWakeFPBaselineId,
)

ROOT = Path(__file__).resolve().parents[2]
SHA_A = "sha256:" + "a" * 64
SHA_B = "sha256:" + "b" * 64
SHA_C = "sha256:" + "c" * 64
SHA_D = "sha256:" + "d" * 64
SHA_E = "sha256:" + "e" * 64
COMMIT = "1" * 40


def _provenance() -> Provenance:
    return Provenance(
        schema_version=1,
        source_identity="qw3-unit-test",
        request_sha256=SHA_A,
        manifest_sha256=SHA_B,
    )


def _context(
    role: CampaignRole,
    capabilities: frozenset[Capability],
) -> ExecutionContext:
    receipts: tuple[ReceiptReference, ...] = ()
    policy_sha: str | None = None
    if role is CampaignRole.C2_CALIBRATION:
        receipts = (ReceiptReference(ReceiptKind.C1_COLLECTION, SHA_A),)
    elif role is CampaignRole.C3_CONFIRMATORY:
        receipts = (
            ReceiptReference(ReceiptKind.C1_COLLECTION, SHA_A),
            ReceiptReference(ReceiptKind.C2_POLICY_FREEZE, SHA_B),
        )
        policy_sha = SHA_E
    elif role is CampaignRole.R_REPLICATION:
        receipts = (
            ReceiptReference(ReceiptKind.C1_COLLECTION, SHA_A),
            ReceiptReference(ReceiptKind.C2_POLICY_FREEZE, SHA_B),
            ReceiptReference(ReceiptKind.C3_CONFIRMATORY, SHA_C),
        )
        policy_sha = SHA_E
    return ExecutionContext(
        role=role,
        permissions=PermissionSet(role, capabilities),
        source_commit=COMMIT,
        image_digest=SHA_A,
        request_sha256=SHA_B,
        manifest_sha256=SHA_C,
        code_manifest_sha256=SHA_D,
        receipts=receipts,
        policy_manifest_sha256=policy_sha,
    )


def _feature_values(level: ObservationLevel, *, error: float = 0.1) -> dict[str, object]:
    fields = {
        ObservationLevel.A0: A0_FIELDS,
        ObservationLevel.A1: A1_FIELDS,
        ObservationLevel.A2: A2_FIELDS,
    }[level]
    values: dict[str, object] = {}
    for name in fields:
        if name == "snapshot_id":
            values[name] = "snapshot-0"
        elif name in {"registered_layer_order", "registered_block_order", "acquired_analytic_ids"}:
            values[name] = "frozen-order"
        elif name.endswith("_ns") or name in {
            "compute_step",
            "reference_horizon_k_ref",
            "remaining_sweeps",
        }:
            values[name] = 1
        else:
            values[name] = error
    return values


def _analytic(
    analytic_id: QWakeFPAnalyticId,
    outcome: AnalyticOutcome,
) -> FrozenAnalyticOutput:
    fields_by_id = {
        QWakeFPAnalyticId.ROSENBAUM_WAVEFRONT_STATUS_V1: (
            ("completed_component_prefix", "layer-0"),
            ("next_structurally_unfinished_component", "layer-1"),
        ),
        QWakeFPAnalyticId.RESIDUAL_PERSISTENCE_V1: (
            ("prediction_error_nonincreasing", True),
            ("state_delta_nonincreasing", True),
            ("persistence_window_complete", True),
        ),
        QWakeFPAnalyticId.COST_DOMINANCE_V1: (
            ("candidate_acquisition_dominated", False),
            ("lower_bound_remaining_suffix_ns", 100),
            ("upper_bound_acquisition_ns", 10),
        ),
    }
    return FrozenAnalyticOutput(
        analytic_id=analytic_id,
        outcome=outcome,
        fields=fields_by_id[analytic_id],
        measurement=EdgeMeasurement(host_time_ns=5),
    )


def _record(
    *,
    seed: int,
    level: ObservationLevel = ObservationLevel.A2,
    sufficient: bool = True,
    error: float = 0.1,
    remaining_suffix_ns: int = 100,
    analytics: tuple[FrozenAnalyticOutput, ...] = (),
) -> TrajectorySnapshotRecord:
    return TrajectorySnapshotRecord(
        model_seed=seed,
        batch_id="batch-0",
        snapshot_id="snapshot-0",
        compute_step=1,
        observation=build_feature_vector(level, _feature_values(level, error=error)),
        analytics=analytics,
        measured_edges=(
            MeasuredEdge(
                edge_id="observer",
                category=CostCategory.OBSERVER,
                measurement=EdgeMeasurement(
                    host_time_ns=10,
                    device_time_ns=7,
                    temporary_memory_bytes=16,
                ),
            ),
            MeasuredEdge(
                edge_id="control",
                category=CostCategory.CONTROL,
                measurement=EdgeMeasurement(host_time_ns=5),
            ),
        ),
        remaining_suffix_ns=remaining_suffix_ns,
        provenance=_provenance(),
        oracle_label=OracleLabel(
            snapshot_id="snapshot-0",
            response_sha256=SHA_E,
            defect=0.0 if sufficient else 2.0,
            sufficient=sufficient,
        ),
    )


def _dataset(*records: TrajectorySnapshotRecord) -> SealedTrajectoryDataset:
    return SealedTrajectoryDataset(
        schema_version=1,
        contract_id=QWAKE_FP_SPECIAL_CASE_CONTRACT.contract_id,
        records=tuple(sorted(records, key=lambda item: item.record_id)),
        source_receipt_sha256=SHA_D,
    )


def _policy(*rules: PolicyRule) -> FrozenPolicyManifest:
    return FrozenPolicyManifest(
        schema_version=1,
        policy_id="qwake-fp-unit-policy",
        contract_id=QWAKE_FP_SPECIAL_CASE_CONTRACT.contract_id,
        rules=rules,
        default_action=FrontierAction(FrontierActionKind.COMPLETE_SUFFIX),
    )


def test_pipeline_has_no_torch_runtime_or_effect_imports() -> None:
    module = __import__(
        "torch2pc_thesis.stage3b_qwake_fp_pipeline",
        fromlist=["stage3b_qwake_fp_pipeline"],
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
    assert imported_roots.isdisjoint(
        {"torch", "torch2pc", "subprocess", "pathlib", "os", "shutil", "socket"}
    )


def test_component_registry_is_closed_complete_and_unique() -> None:
    assert tuple(item.component_id for item in COMPONENT_REGISTRY) == tuple(
        PipelineComponentId
    )
    assert len({item.component_id for item in COMPONENT_REGISTRY}) == len(
        PipelineComponentId
    )
    assert all(item.input_schema and item.output_schema for item in COMPONENT_REGISTRY)


def test_live_components_are_effectful_and_c2_has_no_live_component() -> None:
    assert all(
        item.effectful
        for item in COMPONENT_REGISTRY
        if item.phase is PipelinePhase.LIVE
    )
    assert all(
        CampaignRole.C2_CALIBRATION not in item.allowed_roles
        for item in COMPONENT_REGISTRY
        if item.phase in {PipelinePhase.LIVE, PipelinePhase.POST_ACTION}
    )


def test_publication_component_is_embedded_but_unplannable() -> None:
    context = _context(CampaignRole.C1_COLLECTION, frozenset())
    with pytest.raises(QWakePermissionError, match="unavailable"):
        plan_component(context, PipelineComponentId.RENDER_PUBLICATION_EXPORT)


def test_component_planning_checks_effect_local_capabilities() -> None:
    denied = _context(CampaignRole.C1_COLLECTION, frozenset())
    with pytest.raises(QWakePermissionError, match="missing capabilities"):
        plan_component(denied, PipelineComponentId.COLLECT_A0)
    allowed = _context(
        CampaignRole.C1_COLLECTION,
        frozenset({Capability.EXECUTE_FIXEDPRED, Capability.COLLECT_A0}),
    )
    first = plan_component(allowed, PipelineComponentId.COLLECT_A0, (SHA_E,))
    second = plan_component(allowed, PipelineComponentId.COLLECT_A0, (SHA_E,))
    assert first == second
    assert first.plan_sha256.startswith("sha256:")


def test_feature_vectors_match_exact_cumulative_qw2_fields() -> None:
    for level in ObservationLevel:
        vector = build_feature_vector(level, _feature_values(level))
        assert tuple(name for name, _ in vector.fields) == {
            ObservationLevel.A0: A0_FIELDS,
            ObservationLevel.A1: A1_FIELDS,
            ObservationLevel.A2: A2_FIELDS,
        }[level]
    bad = _feature_values(ObservationLevel.A0)
    bad["oracle_label"] = True
    with pytest.raises(QWakeFPPipelineError, match="feature keys differ"):
        build_feature_vector(ObservationLevel.A0, bad)


def test_analytic_outputs_require_exact_registered_fields_and_level() -> None:
    analytic = _analytic(
        QWakeFPAnalyticId.RESIDUAL_PERSISTENCE_V1,
        AnalyticOutcome.UNRESOLVED,
    )
    with pytest.raises(QWakeFPPipelineError, match="requires A1"):
        _record(seed=0, level=ObservationLevel.A0, analytics=(analytic,))


def test_sealed_dataset_requires_oracle_unique_and_sorted_records() -> None:
    first = _record(seed=0)
    second = _record(seed=1)
    dataset = _dataset(first, second)
    assert dataset.sha256().startswith("sha256:")
    with pytest.raises(QWakeFPPipelineError, match="canonically sorted"):
        SealedTrajectoryDataset(
            schema_version=1,
            contract_id=QWAKE_FP_SPECIAL_CASE_CONTRACT.contract_id,
            records=(second, first),
            source_receipt_sha256=SHA_D,
        )
    no_oracle = TrajectorySnapshotRecord(
        model_seed=2,
        batch_id="batch-0",
        snapshot_id="snapshot-0",
        compute_step=1,
        observation=build_feature_vector(
            ObservationLevel.A0,
            _feature_values(ObservationLevel.A0),
        ),
        analytics=(),
        measured_edges=(),
        remaining_suffix_ns=10,
        provenance=_provenance(),
    )
    with pytest.raises(QWakeFPPipelineError, match="post-action oracle"):
        _dataset(no_oracle)


def test_cost_mapping_uses_host_time_once_and_memory_maximum() -> None:
    record = _record(seed=0)
    cost = aggregate_decision_cost(record.measured_edges)
    assert cost.observer_ns == 10
    assert cost.control_ns == 5
    assert cost.total_time_ns == 15
    assert cost.memory_bytes == 16


def test_policy_interpreter_is_deterministic_and_fail_closed() -> None:
    record = _record(seed=0, error=0.1)
    policy = _policy(
        PolicyRule(
            rule_id="accept-low-error",
            predicate=PolicyPredicateKind.FEATURE_LE,
            feature_name="global_prediction_error_l2_sq",
            threshold=0.2,
            action=FrontierAction(FrontierActionKind.ACCEPT_FRONTIER),
        )
    )
    assert interpret_policy(record, policy).kind is FrontierActionKind.ACCEPT_FRONTIER
    assert policy.sha256() == policy.sha256()
    strict = _policy(
        PolicyRule(
            rule_id="accept-very-low-error",
            predicate=PolicyPredicateKind.FEATURE_LE,
            feature_name="global_prediction_error_l2_sq",
            threshold=0.01,
            action=FrontierAction(FrontierActionKind.ACCEPT_FRONTIER),
        )
    )
    assert interpret_policy(record, strict).kind is FrontierActionKind.COMPLETE_SUFFIX


def test_policy_rejects_unregistered_oracle_feature_and_open_default() -> None:
    with pytest.raises(QWakeFPPipelineError, match="outside the QW-2 registry"):
        PolicyRule(
            rule_id="bad",
            predicate=PolicyPredicateKind.FEATURE_LE,
            feature_name="oracle_sufficient",
            threshold=1.0,
            action=FrontierAction(FrontierActionKind.ACCEPT_FRONTIER),
        )
    with pytest.raises(QWakeFPPipelineError, match="fail closed"):
        FrozenPolicyManifest(
            schema_version=1,
            policy_id="bad-default",
            contract_id=QWAKE_FP_SPECIAL_CASE_CONTRACT.contract_id,
            rules=(),
            default_action=FrontierAction(FrontierActionKind.ACCEPT_FRONTIER),
        )


def test_policy_evaluation_prioritizes_dangerous_acceptance() -> None:
    dataset = _dataset(_record(seed=0, sufficient=True), _record(seed=1, sufficient=False))
    policy = _policy(
        PolicyRule(
            rule_id="accept-all",
            predicate=PolicyPredicateKind.ALWAYS,
            action=FrontierAction(FrontierActionKind.ACCEPT_FRONTIER),
        )
    )
    summary = evaluate_policy(dataset, policy)
    assert summary.accepted_records == 2
    assert summary.dangerous_accepts == 1
    assert summary.result_class is EvaluationClass.UNSAFE


def test_safe_policy_reports_positive_net_saving() -> None:
    dataset = _dataset(_record(seed=0, sufficient=True, remaining_suffix_ns=100))
    policy = _policy(
        PolicyRule(
            rule_id="accept-all",
            predicate=PolicyPredicateKind.ALWAYS,
            action=FrontierAction(FrontierActionKind.ACCEPT_FRONTIER),
        )
    )
    summary = evaluate_policy(dataset, policy)
    assert summary.dangerous_accepts == 0
    assert summary.total_net_saving_ns == 85
    assert summary.result_class is EvaluationClass.SAFE_AND_BENEFICIAL


def test_opportunity_analysis_uses_post_action_labels_and_measured_cost() -> None:
    summary = analyze_opportunity(
        _dataset(_record(seed=0, sufficient=True, remaining_suffix_ns=100)),
        control_overhead_lower_bound_ns=20,
    )
    assert summary.exists_preterminal_sufficient_state is True
    assert summary.maximum_potential_saving_ns == 85
    assert summary.potential_avoided_cost_exceeds_control_overhead_lower_bound


def test_baseline_and_ablation_registries_are_exactly_frozen() -> None:
    assert tuple(QWakeFPBaselineId) == BASELINE_REGISTRY
    assert tuple(QWakeFPAblationId) == ABLATION_REGISTRY
    assert len(BASELINE_REGISTRY) == 8
    assert len(ABLATION_REGISTRY) == 5


def test_b0_and_b7_bound_the_baseline_replay() -> None:
    dataset = _dataset(_record(seed=0, sufficient=True))
    configuration = BaselineConfiguration()
    b0 = evaluate_baseline(
        dataset,
        QWakeFPBaselineId.B0_FULL_CANONICAL_SUFFIX,
        configuration,
    )
    b7 = evaluate_baseline(
        dataset,
        QWakeFPBaselineId.B7_POST_ACTION_ORACLE,
        configuration,
    )
    assert b0.accepted_records == 0
    assert b0.result_class is EvaluationClass.NO_NONTRIVIAL_COVERAGE
    assert b7.accepted_records == 1
    assert b7.dangerous_accepts == 0


def test_nested_ablation_removes_only_requested_policy_capability() -> None:
    policy = _policy(
        PolicyRule(
            rule_id="acquire-a1",
            predicate=PolicyPredicateKind.ALWAYS,
            action=FrontierAction(
                FrontierActionKind.ADVANCE_OBSERVATION,
                target_observation=ObservationLevel.A1,
            ),
        ),
        PolicyRule(
            rule_id="fallback",
            predicate=PolicyPredicateKind.ALWAYS,
            action=FrontierAction(FrontierActionKind.COMPLETE_SUFFIX),
        ),
    )
    ablated = apply_ablation(policy, QWakeFPAblationId.WITHOUT_A1)
    assert tuple(rule.rule_id for rule in ablated.rules) == ("fallback",)
    assert ablated.default_action.kind is FrontierActionKind.COMPLETE_SUFFIX


def test_sealing_and_publication_render_are_pure_and_deterministic() -> None:
    dataset = _dataset(_record(seed=0))
    first = seal_payload("trajectory_dataset", dataset)
    second = seal_payload("trajectory_dataset", dataset)
    assert first == second
    rendered = render_publication_bundle((first,), "bounded QWake-FP only")
    assert '"status": "rendered_not_published"' in rendered
    assert first.payload_sha256 in rendered


def test_qw3_documents_keep_execution_closed_and_point_to_qw4() -> None:
    documents = (
        ROOT / "STATUS.md",
        ROOT / "STATUS_EN.md",
        ROOT / "ROADMAP.md",
        ROOT / "ROADMAP_EN.md",
        ROOT / "docs/qwake-fp-experimental-plan.md",
        ROOT / "docs/qwake-fp-experimental-plan_EN.md",
    )
    required = (
        "qwake_fp_superset_pipeline_implemented=true",
        "qwake_fp_superset_pipeline_execution_open=false",
        "qwake_fp_live_adapters_bound=false",
        "qwake_fp_component_registry_closed=true",
        "qwake_fp_offline_replay_implemented=true",
        "QW-4",
    )
    for path in documents:
        text = path.read_text(encoding="utf-8")
        for marker in required:
            assert marker in text
    for path in (ROOT / "STATUS.md", ROOT / "STATUS_EN.md"):
        text = path.read_text(encoding="utf-8")
        assert "c1_collection_open=false" in text
        assert "c2_calibration_open=false" in text
        assert "c3_confirmatory_open=false" in text
        assert "policy_activation_permitted=false" in text
