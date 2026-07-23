"""Regression guards for the bounded QWake-FP scope freeze."""

from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

RU_DOCS = (
    ROOT / "docs/decisions/ADR-042-stage3b-qwake-fp-bounded-validation-and-single-image-gating.md",
    ROOT / "docs/qwake-fp-experimental-plan.md",
    ROOT / "docs/stage3b-integrated-frontier-model.md",
    ROOT / "STATUS.md",
    ROOT / "README.md",
)
EN_DOCS = (
    ROOT / "docs/decisions/ADR-042-stage3b-qwake-fp-bounded-validation-and-single-image-gating_EN.md",
    ROOT / "docs/qwake-fp-experimental-plan_EN.md",
    ROOT / "docs/stage3b-integrated-frontier-model_EN.md",
    ROOT / "STATUS_EN.md",
    ROOT / "README_EN.md",
)
CURRENT_DOCS = RU_DOCS + EN_DOCS
ADR_DOCS = (RU_DOCS[0], EN_DOCS[0])
PLAN_DOCS = (RU_DOCS[1], EN_DOCS[1])
NORMATIVE_DOCS = ADR_DOCS + PLAN_DOCS

HISTORICAL_DIGESTS = {
    ROOT / "docs/decisions/ADR-039-stage3b-fixedpred-sufficiency-dus-design.md": (
        "7292fc1c8d2a9a87c003162f5be4993a30896fc0b86318bf9fdbf78406cbea85"
    ),
    ROOT / "docs/decisions/ADR-039-stage3b-fixedpred-sufficiency-dus-design_EN.md": (
        "ee180a557222172acf4bc4798adf3fd92e1ccec349af3485d06ca732c264774f"
    ),
    ROOT / "docs/decisions/ADR-040-stage3b-integrated-frontier-model.md": (
        "ab8968e5be80e60b4ef18b57126b90817c94317df8e543d9604506d4219f687f"
    ),
    ROOT / "docs/decisions/ADR-040-stage3b-integrated-frontier-model_EN.md": (
        "917ac3002854c347896514fc71da728b5b19b375de90770fcff080a1fbe89824"
    ),
    ROOT
    / "docs/decisions/ADR-041-stage3b-integrated-frontier-corrective-semantics.md": (
        "edeba8e9336c3642ba7a426e4e1ee69f4982ab6a154acd155ef6b4a0400feb3e"
    ),
    ROOT
    / "docs/decisions/ADR-041-stage3b-integrated-frontier-corrective-semantics_EN.md": (
        "67d1e8880702207f375d2bee1775ab145a560bb9c16eb892f2f2584dd84b7eaa"
    ),
}


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_adr_039_through_041_remain_byte_identical() -> None:
    for path, expected in HISTORICAL_DIGESTS.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, path


def test_qwake_pc_and_qwake_fp_claim_levels_are_separate() -> None:
    required = (
        "qwake_general_specification_frozen=true",
        "qwake_fp_only_mandatory_implementation=true",
        "qwake_fp_validation_case=corrected_rosenbaum_fixedpred_eta1",
        "qwake_fp_canonical_executor=stage2_baseline",
        "qwake_fp_mode=shadow_only",
        "qwake_fp_generalization_claim=false",
    )
    for path in ADR_DOCS:
        text = _text(path)
        for token in required:
            assert token in text, (path, token)


def test_single_image_and_campaign_roles_are_frozen() -> None:
    required = (
        "execution_image_strategy=single_immutable_superset_image",
        "same_image_digest_required_across_c1_c2_c3_r=true",
        "executable_code_changes_after_image_freeze=false",
        "campaign_roles=C1_COLLECTION,C2_CALIBRATION,C3_CONFIRMATORY,R_REPLICATION",
        "stage_activation=fail_closed_permission_manifest",
    )
    for path in ADR_DOCS:
        text = _text(path)
        for token in required:
            assert token in text, (path, token)


def test_permission_gates_are_effect_local_and_fail_closed() -> None:
    required = (
        "permission_checks_at_effect_boundaries=true",
        "disabled_capability_executes=false",
        "manifest_arbitrary_code_loading=false",
        "manifest_shell_command_loading=false",
        "policy_representation=frozen_data_manifest",
        "policy_interpreter_embedded_in_image=true",
    )
    for path in ADR_DOCS:
        text = _text(path)
        for token in required:
            assert token in text, (path, token)


def test_calibration_and_confirmatory_permissions_cannot_mix() -> None:
    required = (
        "policy_selection_permitted_role=C2_CALIBRATION",
        "confirmatory_access_permitted_role=C3_CONFIRMATORY",
        "policy_selection_with_confirmatory_access_forbidden=true",
        "SELECT_POLICY + ACCESS_CONFIRMATORY_DATA",
        "C3_CONFIRMATORY + FREEZE_POLICY",
    )
    for path in ADR_DOCS:
        text = _text(path)
        for token in required:
            assert token in text, (path, token)


def test_publication_strength_requirements_are_explicit() -> None:
    required = (
        "untouched_confirmatory_seeds_required=true",
        "replication_without_retuning_required=true",
        "publication_baselines_required=true",
        "nested_ablation_required=true",
        "trajectory_benchmark_planned=true",
        "safety_precedes_coverage_precedes_cost=true",
    )
    for path in ADR_DOCS:
        text = _text(path)
        for token in required:
            assert token in text, (path, token)


def test_all_scientific_execution_gates_remain_closed() -> None:
    required = (
        "qwake_fp_execution_permitted=false",
        "c1_collection_open=false",
        "c2_calibration_open=false",
        "c3_confirmatory_open=false",
        "replication_open=false",
        "oracle_label_generation_open=false",
        "feature_collection_permitted=false",
        "policy_activation_permitted=false",
        "test_dataset_access=false",
        "full_stage3b_campaign_complete=false",
    )
    for path in NORMATIVE_DOCS:
        text = _text(path)
        for token in required:
            assert token in text, (path, token)


def test_roadmap_uses_one_pre_freeze_implementation_path() -> None:
    for name in ("ROADMAP.md", "ROADMAP_EN.md"):
        text = _text(ROOT / name)
        for stage in range(0, 11):
            assert f"QW-{stage}" in text, (name, stage)
        assert "C1_COLLECTION" in text
        assert "C2_CALIBRATION" in text
        assert "C3_CONFIRMATORY" in text
        assert "R_REPLICATION" in text
        assert "superset" in text.lower()
        assert "image" in text.lower()


def test_scope_freeze_does_not_add_pdca_or_deming_layer() -> None:
    forbidden = ("PDCA", "Deming", "Деминг", "цикл Деминга")
    for path in NORMATIVE_DOCS:
        text = _text(path)
        for token in forbidden:
            assert token not in text, (path, token)


def test_c2_is_strictly_offline_over_sealed_c1_artifacts() -> None:
    required = (
        "c2_execution_mode=offline_only",
        "c2_input_artifacts=sealed_c1_trajectory_dataset",
        "c2_live_fixedpred_execution_permitted=false",
        "c2_new_observation_collection_permitted=false",
        "c2_new_oracle_generation_permitted=false",
        "c2_policy_selection_from_frozen_artifacts_only=true",
        "ACCESS_SEALED_C1_ARTIFACTS",
        "RUN_OFFLINE_REPLAY",
        "EXECUTE_FIXEDPRED",
        "COMPUTE_NEW_ORACLE_LABELS",
    )
    for path in NORMATIVE_DOCS:
        text = _text(path)
        for token in required:
            assert token in text, (path, token)


def test_pre_freeze_validation_uses_three_matched_observer_pairs() -> None:
    required = (
        "P0: B0 <-> B0+A0",
        "P1: B0 <-> B0+A0+A1",
        "P2: B0 <-> B0+A0+A1+A2",
    )
    for path in PLAN_DOCS + (ROOT / "ROADMAP.md", ROOT / "ROADMAP_EN.md"):
        text = _text(path)
        for token in required:
            assert token in text, (path, token)
