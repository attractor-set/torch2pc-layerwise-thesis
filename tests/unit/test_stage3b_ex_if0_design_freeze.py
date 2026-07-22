"""Regression guards for the Stage 3B EX-IF0 design freeze."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FREEZE_ROOT = ROOT / "experiments" / "frozen" / "stage3b-ex-if0-design-v1"
CONTRACT_PATH = FREEZE_ROOT / "contract.json"
SHA_PATH = FREEZE_ROOT / "SHA256SUMS"
DOCS = (
    ROOT / "experiments" / "planned" / "STAGE3B-EX-IF0.md",
    ROOT / "experiments" / "planned" / "STAGE3B-EX-IF0_EN.md",
)
ADR_DOCS = (
    ROOT
    / "docs"
    / "decisions"
    / "ADR-038-stage3b-ex-if0-exact-implementation-and-oracle-sweep-boundary.md",
    ROOT
    / "docs"
    / "decisions"
    / "ADR-038-stage3b-ex-if0-exact-implementation-and-oracle-sweep-boundary_EN.md",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _contract() -> dict[str, object]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_ex_if0_contract_is_checksum_frozen() -> None:
    line = SHA_PATH.read_text(encoding="utf-8").strip()
    digest, relative = line.split("  ", maxsplit=1)
    assert relative == "contract.json"
    assert digest == _sha256(CONTRACT_PATH)


def test_ex_if0_selects_b0_without_superiority_claim() -> None:
    contract = _contract()
    selection = contract["exact_implementation_selection"]
    assert isinstance(selection, dict)
    assert selection["selected_candidate_id"] == "stage2_baseline"
    assert selection["selected_methods"] == ["fixedpred", "strict"]
    assert selection["selected_role"] == (
        "canonical_exact_reference_and_fail_closed_fallback"
    )
    assert selection["selection_is_superiority_claim"] is False

    rejected = selection["rejected_or_revise_candidates"]
    assert isinstance(rejected, list)
    assert {item["candidate_id"] for item in rejected} == {
        "isolated_layer_vjp",
        "composite_vjp",
    }
    assert all(item["fixedpred_status"] == "reject_or_revise" for item in rejected)
    assert all(item["strict_status"] == "reject_or_revise" for item in rejected)


def test_ex_if0_required_source_digests_match_repository() -> None:
    sources = _contract()["required_sources"]
    assert isinstance(sources, dict)
    for source_id, record in sources.items():
        assert isinstance(record, dict), source_id
        path = ROOT / str(record["path"])
        assert path.is_file(), source_id
        assert _sha256(path) == record["sha256"], source_id


def test_minimum_stably_sufficient_sweep_rule_is_frozen() -> None:
    contract = _contract()
    sweep = contract["minimum_stably_sufficient_sweep_contract"]
    assert isinstance(sweep, dict)
    assert sweep["stable_rule"] == "full_suffix_stability"
    assert sweep["sufficiency_margin"] == "M_star(t)=1-r_Gamma(t)"
    assert sweep["sufficiency_rule"] == "M_star(t)>=0"
    assert sweep["minimum_rule"] == (
        "t_star=min{t: sufficient(j)=true for every j in [t,K_ref]}"
    )
    assert sweep["reference_self_check"] == (
        "S_K_ref must be sufficient by identity"
    )
    assert sweep["regret_aggregation"] == (
        "maximum normalized violation across all registered components; "
        "no averaging"
    )

    thresholds = sweep["threshold_profile"]
    assert thresholds == {
        "lane": "rocm_float32",
        "max_abs": 1e-05,
        "max_relative_l2": 0.001,
        "min_cosine": 0.999,
        "source": "registered B1/B2 ROCm float32 equivalence profile",
        "zero_atol": 1e-07,
    }


def test_decision_epoch_and_feature_label_boundary_prevent_leakage() -> None:
    contract = _contract()
    epoch = contract["decision_epoch_contract"]
    separation = contract["feature_label_separation"]
    assert isinstance(epoch, dict)
    assert isinstance(separation, dict)
    assert epoch["decision_point"] == (
        "after snapshot S_t is complete and before sweep t+1"
    )
    assert epoch["reference_future_visible_to_features"] is False
    assert separation["pre_action_features_may_include_reference_future"] is False
    assert separation["pre_action_features_may_include_t_star"] is False
    assert separation["pre_action_features_may_include_oracle_margin"] is False
    assert "minimum_stably_sufficient_sweep_t_star" in separation[
        "post_action_oracle_fields"
    ]


def test_counterfactual_labels_remain_offline_and_alias_controlled() -> None:
    branches = _contract()["counterfactual_branch_contract"]
    assert isinstance(branches, dict)
    assert branches["branch_labels"] == ["stop", "native_one", "exact_one"]
    assert branches["branch_labels_are_controller_actions"] is False
    assert branches["native_one_implementation"] == "stage2_baseline"
    assert branches["exact_one_implementation"] == "stage2_baseline"
    assert branches["native_one_exact_one_identity_expected"] is True
    assert branches["physical_execution_deduplication_permitted"] is True


def test_ex_if0_opens_design_but_keeps_execution_closed() -> None:
    boundary = _contract()["claim_boundary"]
    assert isinstance(boundary, dict)
    assert boundary["ex_if0_opened"] is True
    assert boundary["ex_if0_complete"] is True
    assert boundary["exact_implementation_frozen"] is True
    for field in (
        "ex_if0_execution_permitted",
        "oracle_label_generation_open",
        "feature_collection_permitted",
        "recursive_aggregate_execution_open",
        "a11_off0_execution_open",
        "policy_activation_permitted",
        "test_dataset_access",
        "full_stage3b_campaign_complete",
    ):
        assert boundary[field] is False, field

    required_markers = (
        "ex_if0_protocol_frozen=true",
        "ex_if0_opened=true",
        "ex_if0_complete=true",
        "exact_implementation_frozen=true",
        "exact_implementation_candidate=stage2_baseline",
        "minimum_sufficient_sweep_rule_frozen=true",
        "ex_if0_execution_permitted=false",
        "oracle_label_generation_open=false",
        "feature_collection_permitted=false",
        "a11_off0_execution_open=false",
        "recursive_aggregate_execution_open=false",
        "policy_activation_permitted=false",
        "test_dataset_access=false",
        "full_stage3b_campaign_complete=false",
    )
    for name in ("STATUS.md", "STATUS_EN.md", "ROADMAP.md", "ROADMAP_EN.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        for marker in required_markers:
            assert marker in text, (name, marker)


def test_ex_if0_docs_and_adr_are_registered_language_pairs() -> None:
    language_map = (ROOT / "docs" / "language-map.csv").read_text(
        encoding="utf-8"
    )
    assert (
        "experiments/planned/STAGE3B-EX-IF0.md,"
        "experiments/planned/STAGE3B-EX-IF0_EN.md,required"
    ) in language_map
    assert (
        "docs/decisions/ADR-038-stage3b-ex-if0-exact-implementation-and-oracle-sweep-boundary.md,"
        "docs/decisions/ADR-038-stage3b-ex-if0-exact-implementation-and-oracle-sweep-boundary_EN.md,required"
    ) in language_map

    for path in DOCS + ADR_DOCS:
        text = path.read_text(encoding="utf-8")
        assert "stage2_baseline" in text
        assert "M^*" in text
        assert "suffix" in text.lower() or "суффикс" in text.lower()
        assert "execution" in text.lower() or "выполн" in text.lower()
