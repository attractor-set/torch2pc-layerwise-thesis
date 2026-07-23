"""Regression guards for the corrected Stage 3B frontier design."""

from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CURRENT_DOCS = (
    ROOT / "docs/stage3b-integrated-frontier-model.md",
    ROOT / "docs/stage3b-integrated-frontier-model_EN.md",
    ROOT
    / "docs/decisions/ADR-041-stage3b-integrated-frontier-corrective-semantics.md",
    ROOT
    / "docs/decisions/ADR-041-stage3b-integrated-frontier-corrective-semantics_EN.md",
)

HISTORICAL_DIGESTS = {
    ROOT
    / "docs/decisions/ADR-039-stage3b-fixedpred-sufficiency-dus-design.md": (
        "7292fc1c8d2a9a87c003162f5be4993a30896fc0b86318bf9fdbf78406cbea85"
    ),
    ROOT
    / "docs/decisions/ADR-039-stage3b-fixedpred-sufficiency-dus-design_EN.md": (
        "ee180a557222172acf4bc4798adf3fd92e1ccec349af3485d06ca732c264774f"
    ),
    ROOT / "docs/decisions/ADR-040-stage3b-integrated-frontier-model.md": (
        "ab8968e5be80e60b4ef18b57126b90817c94317df8e543d9604506d4219f687f"
    ),
    ROOT / "docs/decisions/ADR-040-stage3b-integrated-frontier-model_EN.md": (
        "917ac3002854c347896514fc71da728b5b19b375de90770fcff080a1fbe89824"
    ),
}


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_historical_adr_files_remain_byte_identical() -> None:
    for path, expected in HISTORICAL_DIGESTS.items():
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual == expected, path


def test_current_action_and_transition_alphabets_are_frozen() -> None:
    required = (
        "frontier_action_alphabet=ACCEPT_FRONTIER,ADVANCE_FRONTIER,COMPLETE_SUFFIX",
        "frontier_advance_kinds=OBSERVATION,ANALYTIC,COMPUTE",
        "frontier_state_schema=F(t,A_i,H)",
        "analytic_registry_finite_and_frozen=true",
        "analytic_steps_pre_action_only=true",
        "analytic_step_is_not_free=true",
        "oracle_is_analytic_step=false",
    )
    for path in CURRENT_DOCS:
        text = _text(path)
        for token in required:
            assert token in text, (path, token)


def test_deployable_observation_and_oracle_are_separate() -> None:
    required = (
        "deployable_observation_level_order=A0,A1,A2",
        "oracle_level=O",
        "oracle_availability=post_action_only",
        "oracle_is_frontier_action=false",
    )
    for path in CURRENT_DOCS:
        text = _text(path)
        assert "observation_level_order=A0,A1,A2,O" not in text
        for token in required:
            assert token in text, (path, token)


def test_snapshot_local_monotonicity_is_explicit() -> None:
    required = (
        "within_snapshot_observation_monotone=true",
        "within_snapshot_analytic_history_monotone=true",
        "compute_transition_resets_current_observation=A0",
        "acquisition_history_append_only=true",
        "provenance_monotone=true",
    )
    for path in CURRENT_DOCS:
        text = _text(path)
        for token in required:
            assert token in text, (path, token)


def test_admission_semantics_do_not_conflate_done_and_candidate() -> None:
    required = (
        "done_semantics=admitted_shadow_outcome",
        "accept_candidate_is_action=false",
        "accept_frontier_requires_positive_admission=true",
        "heuristic_analytic_direct_accept=false",
        "statistical_estimate_requires_frozen_risk_admission=true",
    )
    for path in CURRENT_DOCS:
        text = _text(path)
        for token in required:
            assert token in text, (path, token)


def test_measurement_and_decision_costs_are_separate() -> None:
    required = (
        "edge_measurement_vector_required=true",
        "decision_cost_vector_required=true",
        "measurement_to_decision_cost_mapping_required=true",
        "implicit_cost_scalarization_forbidden=true",
        "cost_double_counting_forbidden=true",
    )
    for path in CURRENT_DOCS:
        text = _text(path)
        for token in required:
            assert token in text, (path, token)


def test_mandatory_scope_is_temporal_and_execution_remains_closed() -> None:
    required = (
        "mandatory_thesis_scope=temporal_fixedpred_prefix",
        "recursive_multiscale_scope=conditional_extension",
        "active_control_scope=outside_mandatory_core",
        "integrated_frontier_controls_execution=false",
        "oracle_label_generation_open=false",
        "feature_collection_permitted=false",
        "recursive_aggregate_execution_open=false",
        "policy_activation_permitted=false",
        "test_dataset_access=false",
        "full_stage3b_campaign_complete=false",
    )
    for path in CURRENT_DOCS:
        text = _text(path)
        for token in required:
            assert token in text, (path, token)


def test_research_question_matches_mandatory_temporal_scope() -> None:
    ru = _text(ROOT / "docs/research-question.md")
    en = _text(ROOT / "docs/research-question_EN.md")
    assert "временной префикс `FixedPred`" in ru
    assert "Рекурсивные пространственные агрегаты" in ru
    assert "sufficient temporal FixedPred prefix" in en
    assert "Recursive spatial aggregates" in en


def test_readme_publication_status_matches_status_contract() -> None:
    required = (
        "matched_profiling_analysis_publication_action_complete=true",
        "matched_profiling_analysis_publication_receipt_frozen=true",
        "results_publication_permitted=true",
        "release_draft_required=false",
        "release_publication_permitted=true",
        "release_publication_complete=true",
    )
    for name in ("README.md", "README_EN.md", "STATUS.md", "STATUS_EN.md"):
        text = _text(ROOT / name)
        for token in required:
            assert token in text, (name, token)
