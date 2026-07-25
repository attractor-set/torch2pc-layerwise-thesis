"""Validate the QWake documentation refactor and local-compute boundary."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / (
    "experiments/planned/"
    "STAGE3B-QWAKE-LOCAL-COMPUTE-CONTRACT.json"
)


def _contract() -> dict[str, Any]:
    return cast(
        dict[str, Any],
        json.loads(CONTRACT.read_text(encoding="utf-8")),
    )


def test_local_compute_contract_separates_result_mechanism_and_cost() -> None:
    contract = _contract()
    assert contract["objects"] == {
        "required_result": "R(a,s)",
        "computational_mechanism": "M(a)",
        "resource_trajectory": "Gamma(a,s)",
        "cost_vector": "C(a,s)=Phi(Gamma(a,s))",
    }
    assert (
        contract["equivalence_relations"]
        ["response_equivalence_implies_cost_equivalence"]
        is False
    )
    assert contract["action_family"] == {
        "name": "LOCAL_COMPUTE",
        "members": ["LOCAL_SWEEP", "ANALYTIC_COMPLETION"],
    }


def test_first_analytic_candidate_is_bounded() -> None:
    candidate = _contract()["first_analytic_candidate"]
    assert candidate["candidate_id"] == (
        "fixedpred_eta1_wavefront_completion_v1"
    )
    assert candidate["algorithm"] == "FixedPred"
    assert candidate["eta"] == 1
    assert candidate["architecture"] == "lenet_classic"
    assert candidate["executor"] == "stage2_baseline"
    assert candidate["mode"] == "shadow_post_action_validation"
    assert "Strict" in candidate["excluded"]
    assert "universal_symbolic_solver" in candidate["excluded"]
    assert "full_trajectory_reconstruction" in candidate["excluded"]


def test_stage_sequence_places_extension_before_scientific_image() -> None:
    sequence = _contract()["stage_sequence"]
    expected = [
        "QW-4B-DOC-R1",
        "QW-4B-NEW-IMAGE",
        "QW-4B-F-v2",
        "QW-4B-E-v2",
        "QW-LC0",
        "QW-LC1",
        "QW-LC2",
        "QW-LC3",
        "QW-LC4-I",
        "QW-LC4-F",
        "QW-LC4-E",
        "QW-5",
        "C1",
        "C2",
        "C3",
        "R",
    ]
    assert sequence == expected
    assert sequence.index("QW-LC4-E") < sequence.index("QW-5")
    assert sequence.index("QW-5") < sequence.index("C1")


def test_old_authorization_and_all_execution_gates_remain_closed() -> None:
    contract = _contract()
    retired = contract["retired_runtime_identity"]
    assert retired["old_authorization_reuse_permitted"] is False
    assert retired["runtime_execution_performed"] is False
    assert retired["engineering_evidence_present"] is False
    assert retired["new_image_required"] is True

    assert all(value is False for value in contract["gates"].values())


def test_active_documents_use_one_sequence_and_no_active_qw6_qw10() -> None:
    documents = (
        "ROADMAP.md",
        "ROADMAP_EN.md",
        "docs/qwake-fp-experimental-plan.md",
        "docs/qwake-fp-experimental-plan_EN.md",
        "docs/stage3b-future-policy-boundary.md",
        "docs/stage3b-future-policy-boundary_EN.md",
    )
    required = (
        "QW-4B-DOC-R1",
        "QW-4B-F-v2",
        "QW-4B-E-v2",
        "QW-LC0",
        "QW-LC4-E",
        "QW-5",
        "C1",
        "C2",
        "C3",
        "R",
    )
    for name in documents:
        text = (ROOT / name).read_text(encoding="utf-8")
        for token in required:
            assert token in text

    for name in (
        "docs/qwake-fp-experimental-plan.md",
        "docs/qwake-fp-experimental-plan_EN.md",
    ):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "### `QW-6`" not in text
        assert "### `QW-7`" not in text
        assert "### `QW-8`" not in text
        assert "### `QW-9`" not in text
        assert "### `QW-10`" not in text


def test_status_preserves_historical_new_image_requirement() -> None:
    markers = (
        "qwake_documentation_refactor_complete=true",
        "qwake_old_runtime_authorization_retired=true",
        "qwake_old_runtime_authorization_reuse_permitted=false",
        "qwake_new_image_required=true",
        "qwake_new_runtime_preflight_captured=false",
        "qwake_new_runtime_authorization_issued=false",
        "qwake_runtime_validation_performed=false",
        "qwake_engineering_evidence_present=false",
        "qwake_local_compute_implementation_open=false",
        "qwake_local_compute_execution_open=false",
        "qwake_scientific_image_freeze_permitted=false",
        "qwake_next_slice=QW-4B-new-image",
        "qwake_post_baseline_next_slice=QW-LC0",
    )
    for name in ("STATUS.md", "STATUS_EN.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        historical = text[text.index("## `QW-4B-DOC-R1`"):text.index("## `QW-4B-F-v2`")]
        for marker in markers:
            assert marker in historical


def test_current_status_records_freeze_without_execution() -> None:
    markers = (
        "qwake_new_image_required=false",
        "qwake_new_image_built=true",
        "qwake_new_runtime_preflight_captured=true",
        "qwake_new_runtime_authorization_issued=true",
        "qwake_runtime_authorization_verified=true",
        "qwake_runtime_validation_permitted=true",
        "qwake_runtime_execution_performed=false",
        "qwake_runtime_validation_performed=false",
        "qwake_engineering_evidence_present=false",
        "qwake_frozen_authorized_cell_count=6",
        "qwake_frozen_execution_count=1",
        "qwake_authorized_output_root_absent=true",
        "qwake_scientific_image_freeze_permitted=false",
        "qwake_local_compute_implementation_open=false",
        "qwake_local_compute_execution_open=false",
        "qwake_next_slice=QW-4B-E-v2",
        "qwake_post_baseline_next_slice=QW-LC0",
    )
    for name in ("STATUS.md", "STATUS_EN.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        current = text[text.index("## `QW-4B-F-v2`"):]
        for marker in markers:
            assert marker in current


def test_refactored_plans_preserve_baseline_and_offline_guards() -> None:
    required = (
        "P0: B0 <-> B0+A0",
        "P1: B0 <-> B0+A0+A1",
        "P2: B0 <-> B0+A0+A1+A2",
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
        "qwake_old_runtime_authorization_reuse_permitted=false",
        "qwake_runtime_execution_performed=false",
        "qwake_fp_execution_permitted=false",
        "full_stage3b_campaign_complete=false",
    )
    for name in (
        "docs/qwake-fp-experimental-plan.md",
        "docs/qwake-fp-experimental-plan_EN.md",
    ):
        text = (ROOT / name).read_text(encoding="utf-8")
        for marker in required:
            assert marker in text, (name, marker)

    for name in ("ROADMAP.md", "ROADMAP_EN.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        for marker in required[:3]:
            assert marker in text, (name, marker)
