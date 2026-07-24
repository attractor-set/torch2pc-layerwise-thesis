"""Regression guards for the frozen QW-2 QWake-FP special-case contract."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

from torch2pc_thesis.stage3b_qwake_core import (
    ROLE_CAPABILITY_ALLOWLIST,
    ROLE_REQUIRED_RECEIPTS,
    AnalyticClass,
    CampaignRole,
    Capability,
    ObservationLevel,
)
from torch2pc_thesis.stage3b_qwake_fp_spec import (
    A0_FIELDS,
    A1_FIELDS,
    A2_FIELDS,
    ANALYTIC_REGISTRY,
    OBSERVATION_REGISTRY,
    PAIRED_VALIDATION_REGISTRY,
    QWAKE_FP_SPECIAL_CASE_CONTRACT,
    QWakeFPAnalyticId,
    QWakeFPArchitecture,
    QWakeFPBaselineId,
    QWakeFPExecutor,
    QWakeFPMethod,
    QWakeFPPairId,
    QWakeFPResponseComponent,
    build_qwake_fp_special_case_contract,
)

ROOT = Path(__file__).resolve().parents[2]
FROZEN_DIR = ROOT / "experiments/frozen/stage3b-qwake-fp-special-case-v1"
CONTRACT_PATH = FROZEN_DIR / "contract.json"
SUMS_PATH = FROZEN_DIR / "SHA256SUMS"


def test_qwake_fp_spec_has_no_torch_or_runtime_dependency() -> None:
    module = __import__(
        "torch2pc_thesis.stage3b_qwake_fp_spec",
        fromlist=["stage3b_qwake_fp_spec"],
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
    forbidden = {"subprocess", "pathlib", "os", "shutil"}
    assert imported_roots.isdisjoint(forbidden)


def test_special_case_identity_is_exactly_bounded() -> None:
    contract = QWAKE_FP_SPECIAL_CASE_CONTRACT
    assert contract.method is QWakeFPMethod.FIXEDPRED
    assert contract.eta == 1.0
    assert contract.executor is QWakeFPExecutor.STAGE2_BASELINE
    assert contract.architecture is QWakeFPArchitecture.LENET_CLASSIC
    assert contract.response_components == tuple(QWakeFPResponseComponent)
    assert "K_ref" in contract.decision_epoch
    assert "every j in [t,K_ref]" in contract.stable_sufficiency_rule
    assert contract.generalization_claim is False


def test_observations_are_exactly_nested_a0_a1_a2() -> None:
    assert tuple(item.level for item in OBSERVATION_REGISTRY) == tuple(
        ObservationLevel
    )
    assert OBSERVATION_REGISTRY[0].cumulative_fields == A0_FIELDS
    assert OBSERVATION_REGISTRY[1].cumulative_fields == A1_FIELDS
    assert OBSERVATION_REGISTRY[2].cumulative_fields == A2_FIELDS
    assert set(A0_FIELDS) < set(A1_FIELDS) < set(A2_FIELDS)
    assert OBSERVATION_REGISTRY[0].tensor_value_reads is False
    assert OBSERVATION_REGISTRY[1].device_side_only is True
    assert OBSERVATION_REGISTRY[2].deterministic_sample_prefix_sizes == (
        32,
        128,
        256,
    )
    assert OBSERVATION_REGISTRY[2].sample_index_rule is not None


def test_observations_do_not_contain_post_action_oracle_data() -> None:
    forbidden = ("oracle", "t_star", "reference_future", "sufficiency_margin")
    for spec in OBSERVATION_REGISTRY:
        for field_name in spec.cumulative_fields:
            assert not any(token in field_name for token in forbidden)


def test_analytic_registry_is_closed_and_cannot_directly_accept() -> None:
    assert tuple(item.analytic_id for item in ANALYTIC_REGISTRY) == tuple(
        QWakeFPAnalyticId
    )
    assert len({item.analytic_id for item in ANALYTIC_REGISTRY}) == 3
    assert all(item.may_directly_accept is False for item in ANALYTIC_REGISTRY)
    by_id = {item.analytic_id: item for item in ANALYTIC_REGISTRY}
    assert (
        by_id[QWakeFPAnalyticId.ROSENBAUM_WAVEFRONT_STATUS_V1].analytic_class
        is AnalyticClass.EXACT
    )
    assert (
        by_id[QWakeFPAnalyticId.RESIDUAL_PERSISTENCE_V1].analytic_class
        is AnalyticClass.HEURISTIC
    )
    assert (
        by_id[QWakeFPAnalyticId.COST_DOMINANCE_V1].analytic_class
        is AnalyticClass.CONSERVATIVE
    )


def test_baseline_registry_is_exactly_b0_through_b7() -> None:
    assert QWAKE_FP_SPECIAL_CASE_CONTRACT.baselines == tuple(QWakeFPBaselineId)
    assert len(QWAKE_FP_SPECIAL_CASE_CONTRACT.baselines) == 8
    assert QWAKE_FP_SPECIAL_CASE_CONTRACT.baselines[0].value.startswith("B0_")
    assert QWAKE_FP_SPECIAL_CASE_CONTRACT.baselines[-1].value.startswith("B7_")


def test_pre_freeze_validation_is_exactly_three_matched_pairs() -> None:
    assert tuple(item.pair_id for item in PAIRED_VALIDATION_REGISTRY) == tuple(
        QWakeFPPairId
    )
    assert tuple(item.reference for item in PAIRED_VALIDATION_REGISTRY) == (
        "B0",
        "B0",
        "B0",
    )
    assert tuple(item.instrumented for item in PAIRED_VALIDATION_REGISTRY) == (
        "B0+A0",
        "B0+A0+A1",
        "B0+A0+A1+A2",
    )
    for item in PAIRED_VALIDATION_REGISTRY:
        assert "canonical_endpoint_response" in item.required_equalities
        assert "rng_state_after" in item.required_equalities
        assert "observer_host_time_ns" in item.measured_outputs


def test_cost_mapping_prevents_double_counting() -> None:
    mapping = QWAKE_FP_SPECIAL_CASE_CONTRACT.cost_mapping
    assert len(mapping.exclusive_time_categories) == len(
        set(mapping.exclusive_time_categories)
    )
    assert "exactly one" in mapping.primary_time_basis
    assert "never added a second time" in mapping.device_time_semantics
    assert mapping.selection_order == ("safety", "coverage", "cost")


def test_role_and_receipt_mapping_are_inherited_from_qw1() -> None:
    role_capabilities = dict(QWAKE_FP_SPECIAL_CASE_CONTRACT.role_capabilities)
    role_receipts = dict(QWAKE_FP_SPECIAL_CASE_CONTRACT.role_receipts)
    for role in CampaignRole:
        assert role_capabilities[role.value] == tuple(
            sorted(item.value for item in ROLE_CAPABILITY_ALLOWLIST[role])
        )
        assert role_receipts[role.value] == tuple(
            sorted(item.value for item in ROLE_REQUIRED_RECEIPTS[role])
        )
    c2 = set(role_capabilities[CampaignRole.C2_CALIBRATION.value])
    assert Capability.EXECUTE_FIXEDPRED.value not in c2
    assert Capability.ACCESS_CONFIRMATORY_DATA.value not in c2
    assert Capability.RUN_OFFLINE_REPLAY.value in c2


def test_all_scientific_gates_remain_closed() -> None:
    contract = QWAKE_FP_SPECIAL_CASE_CONTRACT
    assert contract.scientific_execution_open is False
    assert contract.oracle_label_generation_open is False
    assert contract.feature_collection_permitted is False
    assert contract.policy_activation_permitted is False
    assert contract.test_dataset_access is False


def test_contract_builder_is_deterministic() -> None:
    first = build_qwake_fp_special_case_contract()
    second = build_qwake_fp_special_case_contract()
    assert first == second
    assert first.canonical_json() == second.canonical_json()
    assert first.sha256() == second.sha256()


def test_frozen_contract_matches_canonical_python_spec() -> None:
    expected = QWAKE_FP_SPECIAL_CASE_CONTRACT.canonical_json()
    assert CONTRACT_PATH.read_text(encoding="utf-8") == expected
    parsed = json.loads(expected)
    assert parsed["contract_id"] == "stage3b-qwake-fp-special-case-v1"
    assert parsed["status"] == "spec_frozen_execution_closed"


def test_sha256s_seal_matches_frozen_contract() -> None:
    expected = hashlib.sha256(CONTRACT_PATH.read_bytes()).hexdigest()
    assert SUMS_PATH.read_text(encoding="utf-8") == f"{expected}  contract.json\n"
    assert expected == QWAKE_FP_SPECIAL_CASE_CONTRACT.sha256()


def test_qw2_documents_freeze_the_same_contract_and_keep_execution_closed() -> None:
    documents = (
        ROOT / "docs/decisions/ADR-043-stage3b-qwake-fp-special-case-contract.md",
        ROOT / "docs/decisions/ADR-043-stage3b-qwake-fp-special-case-contract_EN.md",
        ROOT / "STATUS.md",
        ROOT / "STATUS_EN.md",
    )
    required = (
        "qwake_fp_special_case_contract_frozen=true",
        "qwake_fp_special_case_contract_id=stage3b-qwake-fp-special-case-v1",
        "qwake_fp_method=fixedpred",
        "qwake_fp_eta=1",
        "qwake_fp_canonical_executor=stage2_baseline",
        "qwake_fp_architecture=lenet_classic",
        "qwake_fp_observation_registry=A0,A1,A2",
        "qwake_fp_baseline_registry=B0,B1,B2,B3,B4,B5,B6,B7",
        "qwake_fp_paired_validation=P0,P1,P2",
        "qwake_fp_scientific_execution_open=false",
        "oracle_label_generation_open=false",
        "feature_collection_permitted=false",
        "policy_activation_permitted=false",
        "test_dataset_access=false",
        "qwake_next_stage=QW-3",
    )
    for path in documents:
        text = path.read_text(encoding="utf-8")
        for token in required:
            assert token in text, (path, token)


def test_qw2_roadmap_and_plan_point_to_qw3_without_opening_campaigns() -> None:
    for path in (
        ROOT / "ROADMAP.md",
        ROOT / "ROADMAP_EN.md",
        ROOT / "docs/qwake-fp-experimental-plan.md",
        ROOT / "docs/qwake-fp-experimental-plan_EN.md",
    ):
        text = path.read_text(encoding="utf-8")
        assert "QW-2" in text
        assert "QW-3" in text
        assert "stage3b-qwake-fp-special-case-v1" in text
    for path in (ROOT / "STATUS.md", ROOT / "STATUS_EN.md"):
        text = path.read_text(encoding="utf-8")
        assert "c1_collection_open=false" in text
        assert "c2_calibration_open=false" in text
        assert "c3_confirmatory_open=false" in text
        assert "replication_open=false" in text
