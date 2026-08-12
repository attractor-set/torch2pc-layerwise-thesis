from __future__ import annotations

import ast
import hashlib
from dataclasses import replace
from pathlib import Path

import pytest
import torch

from torch2pc_thesis.stage3b_qwake_core import (
    CampaignRole,
    EdgeMeasurement,
    FrontierAction,
    FrontierActionKind,
    ObservationLevel,
    OracleLabel,
    Provenance,
    ReceiptKind,
)
from torch2pc_thesis.stage3b_qwake_fp_pipeline import (
    CostCategory,
    FrozenFeatureVector,
    FrozenPolicyManifest,
    MeasuredEdge,
    PolicyPredicateKind,
    PolicyRule,
    QWakeFPPipelineError,
    SealedTrajectoryDataset,
    TrajectorySnapshotRecord,
    build_feature_vector,
)
from torch2pc_thesis.stage3b_qwake_fp_spec import (
    A2_FIELDS,
    QWAKE_FP_SPECIAL_CASE_CONTRACT,
)
from torch2pc_thesis.stage3b_qwake_scientific_campaign import (
    ROLE_COMPONENT_SEQUENCE,
    ArtifactBinding,
    ProtocolReceiptBinding,
    ScientificBatchSpec,
    ScientificCampaignAuthorization,
    ScientificCampaignError,
    ScientificCampaignRequest,
    ScientificDataPartition,
    ScientificDatasetBinding,
    ScientificHostClaim,
    load_scientific_request,
)
from torch2pc_thesis.stage3b_qwake_scientific_runtime import (
    CampaignExecutionReceipt,
    _collect_model_batch,
    _execution_context,
    _plan_campaign_components,
    _verify_predecessor_receipts,
    select_c2_policy,
)

SHA_A = "sha256:" + "a" * 64
SHA_B = "sha256:" + "b" * 64
SHA_C = "sha256:" + "c" * 64
SHA_D = "sha256:" + "d" * 64
COMMIT = "1" * 40


def _binding(partition: ScientificDataPartition) -> ScientificDatasetBinding:
    return ScientificDatasetBinding(
        dataset_name="FashionMNIST",
        dataset_root="data",
        split=ArtifactBinding("results/splits/frozen.npz", SHA_A),
        dataset_assets=(
            ArtifactBinding("data/FashionMNIST/raw/train-images-idx3-ubyte", SHA_B),
            ArtifactBinding("data/FashionMNIST/raw/train-labels-idx1-ubyte", SHA_C),
        ),
        split_key="validation_idx",
        partition=partition,
        batches=(ScientificBatchSpec("batch-000", (0, 1)),),
    )


def _receipts(role: CampaignRole) -> tuple[ProtocolReceiptBinding, ...]:
    items: list[ProtocolReceiptBinding] = []
    if role in {
        CampaignRole.C2_CALIBRATION,
        CampaignRole.C3_CONFIRMATORY,
        CampaignRole.R_REPLICATION,
    }:
        items.append(
            ProtocolReceiptBinding(
                ReceiptKind.C1_COLLECTION,
                "results/receipts/c1.json",
                SHA_A,
                SHA_D,
            )
        )
    if role in {CampaignRole.C3_CONFIRMATORY, CampaignRole.R_REPLICATION}:
        items.append(
            ProtocolReceiptBinding(
                ReceiptKind.C2_POLICY_FREEZE,
                "results/receipts/c2.json",
                SHA_B,
                SHA_D,
            )
        )
    if role is CampaignRole.R_REPLICATION:
        items.append(
            ProtocolReceiptBinding(
                ReceiptKind.C3_CONFIRMATORY,
                "results/receipts/c3.json",
                SHA_C,
                SHA_D,
            )
        )
    return tuple(sorted(items, key=lambda item: item.kind.value))


def _request(role: CampaignRole = CampaignRole.C1_COLLECTION) -> ScientificCampaignRequest:
    dataset = None
    sealed = None
    candidates: tuple[ArtifactBinding, ...] = ()
    policy = None
    seeds: tuple[int, ...] = ()
    if role is CampaignRole.C1_COLLECTION:
        dataset = _binding(ScientificDataPartition.DESIGN)
        seeds = (0,)
    elif role is CampaignRole.C2_CALIBRATION:
        sealed = ArtifactBinding("results/sealed/c1.json", SHA_A)
        candidates = (ArtifactBinding("results/policies/p0.json", SHA_B),)
    elif role is CampaignRole.C3_CONFIRMATORY:
        dataset = _binding(ScientificDataPartition.CONFIRMATORY)
        sealed = ArtifactBinding("results/sealed/c1.json", SHA_A)
        policy = ArtifactBinding("results/policies/frozen.json", SHA_B)
        seeds = (10,)
    else:
        dataset = _binding(ScientificDataPartition.REPLICATION)
        sealed = ArtifactBinding("results/sealed/c1.json", SHA_A)
        policy = ArtifactBinding("results/policies/frozen.json", SHA_B)
        seeds = (20,)
    return ScientificCampaignRequest.create(
        role=role,
        source_commit=COMMIT,
        image_digest=SHA_A,
        manifest_sha256=SHA_B,
        code_manifest_sha256=SHA_C,
        dataset=dataset,
        sealed_c1_dataset=sealed,
        candidate_policies=candidates,
        frozen_policy=policy,
        predecessor_receipts=_receipts(role),
        model_seeds=seeds,
        output_root=f"results/scientific/{role.value}",
        control_overhead_lower_bound_ns=0,
    )


def _authorization(request: ScientificCampaignRequest) -> ScientificCampaignAuthorization:
    return ScientificCampaignAuthorization.issue(
        request,
        issued_at_utc="2026-08-11T20:00:00Z",
    )


def test_role_sequences_and_data_boundaries_are_closed() -> None:
    for role in CampaignRole:
        request = _request(role)
        assert request.component_sequence == ROLE_COMPONENT_SEQUENCE[role]
        assert request.test_dataset_access is False
        assert request.publication_permitted is False
        assert request.arbitrary_code_loading is False
        assert request.shell_command_loading is False
    c2 = _request(CampaignRole.C2_CALIBRATION)
    assert c2.dataset is None
    assert c2.model_seeds == ()


def test_request_json_roundtrip_preserves_artifact_and_receipt_bindings(
    tmp_path: Path,
) -> None:
    request = _request(CampaignRole.C3_CONFIRMATORY)
    path = tmp_path / "request.json"
    path.write_text(request.canonical_json(), encoding="utf-8")

    loaded = load_scientific_request(path)

    assert loaded == request
    assert loaded.sealed_c1_dataset == request.sealed_c1_dataset
    assert loaded.frozen_policy == request.frozen_policy
    assert loaded.predecessor_receipts == request.predecessor_receipts


def test_request_rejects_wrong_role_sequence_and_wrong_partition() -> None:
    request = _request()
    with pytest.raises(ScientificCampaignError, match="component sequence"):
        replace(request, component_sequence=request.component_sequence[:-1])
    with pytest.raises(ScientificCampaignError, match="design data"):
        replace(request, dataset=_binding(ScientificDataPartition.CONFIRMATORY))


def test_authorization_is_exact_one_shot_and_request_bound() -> None:
    request = _request()
    authorization = _authorization(request)
    authorization.require_request(request)
    with pytest.raises(ScientificCampaignError, match="exactly one"):
        replace(authorization, execution_count=2)
    other_request = ScientificCampaignRequest.create(
        role=CampaignRole.C1_COLLECTION,
        source_commit=COMMIT,
        image_digest=SHA_A,
        manifest_sha256=SHA_B,
        code_manifest_sha256=SHA_C,
        dataset=_binding(ScientificDataPartition.DESIGN),
        model_seeds=(0,),
        output_root="results/scientific/C1_COLLECTION-other",
    )
    with pytest.raises(ScientificCampaignError, match="request identity"):
        authorization.require_request(other_request)


def test_pipeline_accepts_registered_structured_observation_values() -> None:
    values: dict[str, object] = {}
    for name in A2_FIELDS:
        if name == "snapshot_id":
            values[name] = "snapshot-0"
        elif name in {"registered_layer_order", "registered_block_order"}:
            values[name] = (0, 1, 2)
        elif name == "acquired_analytic_ids":
            values[name] = ()
        elif name.startswith("per_layer_"):
            values[name] = (1.0, 2.0)
        elif name.startswith("sample_prefix_"):
            values[name] = {"32": (1.0, 2.0), "128": (1.5, 2.5), "256": (2.0, 3.0)}
        elif name in {
            "compute_step",
            "reference_horizon_k_ref",
            "remaining_sweeps",
            "diagnostic_budget_remaining_ns",
        }:
            values[name] = 1
        else:
            values[name] = 0.5
    vector = build_feature_vector(ObservationLevel.A2, values)
    assert isinstance(vector.value("sample_prefix_prediction_error_l2_sq"), dict)
    with pytest.raises(QWakeFPPipelineError, match="registered scalar feature"):
        PolicyRule(
            rule_id="invalid-structured-threshold",
            predicate=PolicyPredicateKind.FEATURE_LE,
            feature_name="sample_prefix_prediction_error_l2_sq",
            threshold=1.0,
            action=FrontierAction(FrontierActionKind.ACCEPT_FRONTIER),
        )


def test_synthetic_cpu_mechanism_builds_complete_sealed_trajectory() -> None:
    request = _request()
    authorization = _authorization(request)
    generator = torch.Generator(device="cpu")
    generator.manual_seed(123)
    inputs = torch.randn((2, 1, 32, 32), generator=generator, dtype=torch.float32)
    targets = torch.tensor((1, 2), dtype=torch.long)
    records = _collect_model_batch(
        request,
        authorization,
        model_seed=0,
        batch=ScientificBatchSpec("batch-000", (0, 1)),
        inputs=inputs,
        targets=targets,
        device=torch.device("cpu"),
    )
    assert len(records) == 7  # lenet_classic has six registered modules => t=0..6
    assert tuple(record.compute_step for record in records) == tuple(range(7))
    assert all(record.observation.level is ObservationLevel.A2 for record in records)
    assert all(len(record.analytics) == 3 for record in records)
    assert all(record.oracle_label is not None for record in records)
    dataset = SealedTrajectoryDataset(
        schema_version=1,
        contract_id=QWAKE_FP_SPECIAL_CASE_CONTRACT.contract_id,
        records=tuple(sorted(records, key=lambda item: item.record_id)),
        source_receipt_sha256=authorization.authorization_sha256,
    )
    assert dataset.sha256().startswith("sha256:")
    assert any(record.oracle_label.sufficient for record in dataset.records if record.oracle_label)


def _manual_dataset() -> SealedTrajectoryDataset:
    feature = FrozenFeatureVector(
        ObservationLevel.A2,
        tuple(
            (name, (
                "snapshot-0" if name == "snapshot_id" else
                1 if name in {"compute_step", "reference_horizon_k_ref", "remaining_sweeps", "diagnostic_budget_remaining_ns"} else
                "frozen" if name in {"registered_layer_order", "registered_block_order", "acquired_analytic_ids"} else
                0.01
            ))
            for name in A2_FIELDS
        ),
    )
    record = TrajectorySnapshotRecord(
        model_seed=0,
        batch_id="batch-0",
        snapshot_id="snapshot-0",
        compute_step=1,
        observation=feature,
        analytics=(),
        measured_edges=(MeasuredEdge("control", CostCategory.CONTROL, EdgeMeasurement(host_time_ns=1)),),
        remaining_suffix_ns=100,
        provenance=Provenance(1, "unit", SHA_A, SHA_B),
        oracle_label=OracleLabel("snapshot-0", SHA_C, 0.0, True),
    )
    return SealedTrajectoryDataset(1, QWAKE_FP_SPECIAL_CASE_CONTRACT.contract_id, (record,), SHA_D)


def test_c2_selection_is_safety_then_coverage_then_cost_and_has_negative_result() -> None:
    dataset = _manual_dataset()
    safe = FrozenPolicyManifest(
        1,
        "safe",
        QWAKE_FP_SPECIAL_CASE_CONTRACT.contract_id,
        (
            PolicyRule(
                "accept-low-error",
                PolicyPredicateKind.FEATURE_LE,
                FrontierAction(FrontierActionKind.ACCEPT_FRONTIER),
                feature_name="global_prediction_error_l2_sq",
                threshold=0.1,
            ),
        ),
        FrontierAction(FrontierActionKind.COMPLETE_SUFFIX),
    )
    closed = FrozenPolicyManifest(
        1,
        "closed",
        QWAKE_FP_SPECIAL_CASE_CONTRACT.contract_id,
        (),
        FrontierAction(FrontierActionKind.COMPLETE_SUFFIX),
    )
    selected = select_c2_policy(dataset, (closed, safe))
    assert selected.status == "selected_safe_coverage_cost_order"
    assert selected.selected_policy_id == "safe"
    negative = select_c2_policy(dataset, (closed,))
    assert negative.status == "bounded_negative_no_safe_beneficial_policy"
    assert negative.selected_policy_sha256 is None


def test_production_entrypoint_has_no_dynamic_code_or_shell_surface() -> None:
    root = Path(__file__).resolve().parents[2]
    source = (root / "scripts/run_stage3b_qwake_scientific_campaign.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    calls = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert calls.isdisjoint({"exec", "eval", "compile", "__import__"})
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
    assert imported_roots.isdisjoint({"subprocess", "shlex", "importlib"})


def test_host_claim_is_exact_one_shot_binding() -> None:
    request = _request()
    authorization = _authorization(request)
    claim = ScientificHostClaim.create(request, authorization)
    claim.require(request, authorization)
    assert claim.docker_run_count == 1
    assert claim.automatic_retry_permitted is False
    assert claim.test_dataset_access is False
    assert claim.publication_permitted is False
    other_request = ScientificCampaignRequest.create(
        role=CampaignRole.C1_COLLECTION,
        source_commit=COMMIT,
        image_digest=SHA_A,
        manifest_sha256=SHA_B,
        code_manifest_sha256=SHA_C,
        dataset=_binding(ScientificDataPartition.DESIGN),
        model_seeds=(0,),
        output_root="results/scientific/C1_COLLECTION-other-claim",
    )
    with pytest.raises(ScientificCampaignError, match="host claim request_sha256"):
        claim.require(other_request, _authorization(other_request))


def test_component_planning_binds_exact_role_sequence() -> None:
    request = _request()
    context = _execution_context(request, ())
    plans = _plan_campaign_components(context, request)
    assert tuple(plan.component_id for plan in plans) == request.component_sequence
    assert all(plan.request_sha256 == request.request_sha256 for plan in plans)
    assert all(plan.plan_sha256.startswith("sha256:") for plan in plans)


def test_request_namespaces_cannot_overlay_executable_source() -> None:
    with pytest.raises(ScientificCampaignError, match="must remain under"):
        ArtifactBinding("src/torch2pc_thesis/injected.py", SHA_A)
    request = _request()
    with pytest.raises(ScientificCampaignError, match="output_root"):
        ScientificCampaignRequest.create(
            role=CampaignRole.C1_COLLECTION,
            source_commit=COMMIT,
            image_digest=SHA_A,
            manifest_sha256=SHA_B,
            code_manifest_sha256=SHA_C,
            dataset=request.dataset,
            model_seeds=(0,),
            output_root="src/scientific-output",
        )


def test_predecessor_receipt_binds_exact_c1_artifact(tmp_path: Path) -> None:
    artifact_path = tmp_path / "results/sealed/c1.json"
    artifact_path.parent.mkdir(parents=True)
    artifact_path.write_text("{}\n", encoding="utf-8")
    artifact_sha = "sha256:" + hashlib.sha256(artifact_path.read_bytes()).hexdigest()

    provisional = CampaignExecutionReceipt(
        schema_version=1,
        role=CampaignRole.C1_COLLECTION,
        protocol_receipt_kind=ReceiptKind.C1_COLLECTION,
        source_commit=COMMIT,
        request_sha256=SHA_A,
        authorization_sha256=SHA_B,
        image_digest=SHA_A,
        output_root="results/scientific/C1_COLLECTION",
        status="scientific_execution_sealed",
        primary_artifact_name="trajectory-dataset.json",
        primary_artifact_sha256=artifact_sha,
        artifact_sha256s=(("trajectory-dataset.json", artifact_sha),),
        component_plan_sha256s=(("seal_artifact", SHA_C),),
        scientific_execution_performed=True,
        test_dataset_access=False,
        publication_permitted=False,
        receipt_sha256=SHA_D,
    )
    receipt = replace(provisional, receipt_sha256=provisional.computed_sha256())
    receipt.require()
    receipt_path = tmp_path / "results/receipts/c1.json"
    receipt_path.parent.mkdir(parents=True)
    receipt_path.write_text(receipt.canonical_json(), encoding="utf-8")
    receipt_file_sha = "sha256:" + hashlib.sha256(receipt_path.read_bytes()).hexdigest()

    request = ScientificCampaignRequest.create(
        role=CampaignRole.C2_CALIBRATION,
        source_commit=COMMIT,
        image_digest=SHA_A,
        manifest_sha256=SHA_B,
        code_manifest_sha256=SHA_C,
        dataset=None,
        sealed_c1_dataset=ArtifactBinding("results/sealed/c1.json", artifact_sha),
        candidate_policies=(ArtifactBinding("results/policies/p0.json", SHA_B),),
        predecessor_receipts=(
            ProtocolReceiptBinding(
                ReceiptKind.C1_COLLECTION,
                "results/receipts/c1.json",
                receipt.receipt_sha256,
                receipt_file_sha,
            ),
        ),
        output_root="results/scientific/C2_CALIBRATION",
    )
    refs = _verify_predecessor_receipts(tmp_path, request)
    assert tuple(item.kind for item in refs) == (ReceiptKind.C1_COLLECTION,)
    context = _execution_context(request, refs)
    assert tuple(plan.component_id for plan in _plan_campaign_components(context, request)) == request.component_sequence


def test_host_launcher_has_fixed_docker_command_surface() -> None:
    root = Path(__file__).resolve().parents[2]
    source = (root / "scripts/run_stage3b_qwake_scientific_campaign_host.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    string_literals = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    assert "--network=none" in string_literals
    assert "--read-only" in string_literals
    assert "--cap-drop=ALL" in string_literals
    assert "/workspace/scripts/run_stage3b_qwake_scientific_campaign.py" in string_literals
    assert "docker build" not in source
    assert "docker pull" not in source
    assert "shell=True" not in source
