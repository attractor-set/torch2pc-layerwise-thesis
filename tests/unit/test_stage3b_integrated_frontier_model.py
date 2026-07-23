"""Regression guards for the Stage 3B integrated frontier design."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = (
    ROOT / "docs/stage3b-integrated-frontier-model.md",
    ROOT / "docs/stage3b-integrated-frontier-model_EN.md",
    ROOT / "docs/decisions/ADR-040-stage3b-integrated-frontier-model.md",
    ROOT / "docs/decisions/ADR-040-stage3b-integrated-frontier-model_EN.md",
)

def test_frontier_action_alphabet_and_roles_are_frozen() -> None:
    required = (
        "frontier_action_alphabet=ACCEPT_FRONTIER,ADVANCE_FRONTIER,COMPLETE_SUFFIX",
        "observation_level_order=A0,A1,A2,O",
        "pc_tref_role=admission_semantics",
        "pc_catm_role=mechanism_evidence",
        "qwake_pc_role=frontier_orchestration",
    )
    for path in DOCS:
        text = path.read_text(encoding="utf-8")
        for token in required:
            assert token in text, (path, token)

def test_dus_mapping_and_frontier_edges_are_explicit() -> None:
    for path in DOCS[:2]:
        text = path.read_text(encoding="utf-8")
        for token in (
            "DONE", "UNKNOWN", "SWEEP", "ADVANCE_FRONTIER(observation)",
            "ADVANCE_FRONTIER(compute)", "COMPLETE_SUFFIX",
            "R_A0 = A0", "R_A1 = A0 + A1", "R_A2 = A0 + A1 + A2",
        ):
            assert token in text, (path, token)

def test_sampling_cost_and_non_interference_are_frozen() -> None:
    required = (
        "nested_deterministic_sampling_required=true",
        "pre_action_post_action_separation_required=true",
        "observer_non_interference_required=true",
        "frontier_edge_cost_vector_required=true",
        "oracle_cost_separate_from_deployable_cost=true",
        "observer_rng_mutations=0",
        "post_action_feature_leakage=0",
    )
    for path in DOCS[:2]:
        text = path.read_text(encoding="utf-8")
        for token in required:
            assert token in text, (path, token)

def test_execution_and_collection_remain_closed() -> None:
    required = (
        "integrated_frontier_controls_execution=false",
        "oracle_label_generation_open=false",
        "feature_collection_permitted=false",
        "a11_off0_execution_open=false",
        "recursive_aggregate_execution_open=false",
        "policy_activation_permitted=false",
        "test_dataset_access=false",
        "full_stage3b_campaign_complete=false",
    )
    for path in DOCS:
        text = path.read_text(encoding="utf-8")
        for token in required:
            assert token in text, (path, token)

def test_adr039_is_not_modified_by_successor_patch() -> None:
    path = (
        ROOT
        / "docs"
        / "decisions"
        / "ADR-039-stage3b-fixedpred-sufficiency-dus-design.md"
    )
    text = path.read_text(encoding="utf-8")
    assert "frontier_action_alphabet" not in text
    assert "ADR-040" not in text
