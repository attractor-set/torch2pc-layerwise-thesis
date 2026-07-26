"""Validate the frozen QW-LC0 semantics-and-scope contract."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[2]
FREEZE = ROOT / "experiments/frozen/stage3b-qwake-lc0-semantics-scope-v1"
CONTRACT_SHA256 = "sha256:e68e953aa3d5c425678d54b8dd3b756e706e5cc1a1c4862d4c0ba0bda19bf3c3"
CONTRACT_ID = "stage3b-qwake-lc0-semantics-scope-v1"


def _sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _contract() -> dict[str, Any]:
    return cast(
        dict[str, Any],
        json.loads((FREEZE / "contract.json").read_text(encoding="utf-8")),
    )


def test_lc0_freeze_inventory_and_checksum() -> None:
    assert sorted(path.name for path in FREEZE.iterdir()) == [
        "SHA256SUMS",
        "contract.json",
    ]
    assert _sha(FREEZE / "contract.json") == CONTRACT_SHA256
    expected = CONTRACT_SHA256.removeprefix("sha256:") + "  contract.json\n"
    assert (FREEZE / "SHA256SUMS").read_text(encoding="utf-8") == expected


def test_lc0_contract_separates_objects_and_equivalence() -> None:
    contract = _contract()
    assert contract["contract_id"] == CONTRACT_ID
    assert contract["status"] == "semantics_scope_frozen_execution_closed"
    objects = contract["objects"]
    assert objects["required_result"]["symbol"] == "R(a,s)"
    assert objects["computational_mechanism"]["symbol"] == "M(a)"
    assert objects["resource_trajectory"]["symbol"] == "Gamma(a,s)"
    assert objects["cost_vector"]["symbol"] == "C(a,s)=Phi(Gamma(a,s))"
    relations = contract["equivalence_relations"]
    assert relations["response_equivalence_implies_mechanism_equivalence"] is False
    assert relations["response_equivalence_implies_resource_equivalence"] is False
    assert relations["response_equivalence_implies_cost_equivalence"] is False


def test_lc0_action_family_and_candidate_are_bounded() -> None:
    contract = _contract()
    members = contract["action_family"]["members"]
    assert sorted(members) == ["ANALYTIC_COMPLETION", "LOCAL_SWEEP"]
    assert members["ANALYTIC_COMPLETION"]["direct_accept_frontier_permitted"] is False
    candidate = contract["first_analytic_candidate"]
    assert candidate["candidate_id"] == "fixedpred_eta1_wavefront_completion_v1"
    assert candidate["algorithm"] == "FixedPred"
    assert candidate["eta"] == 1
    assert candidate["architecture"] == "lenet_classic"
    assert candidate["executor"] == "stage2_baseline"
    assert candidate["correctness_status"] == "unvalidated_candidate"
    assert candidate["generalization_claim"] is False
    assert "Strict" in candidate["excluded"]
    assert "universal_symbolic_solver" in candidate["excluded"]
    assert "full_trajectory_reconstruction" in candidate["excluded"]


def test_lc0_defers_response_resource_and_validation_details() -> None:
    contract = _contract()
    assert contract["objects"]["required_result"]["canonical_serialization_deferred_to"] == "QW-LC1"
    assert contract["objects"]["resource_trajectory"]["measurement_schema_deferred_to"] == "QW-LC2"
    assert contract["objects"]["cost_vector"]["concrete_mapping_deferred_to"] == "QW-LC2"
    assert "matched_shadow_validation" in contract["deferred_freezes"]["QW-LC3"]
    assert contract["state_and_fallback"]["exact_reserve_action"] == "COMPLETE_SUFFIX"
    assert contract["state_and_fallback"]["exact_reserve_required"] is True


def test_lc0_claim_and_execution_boundaries_remain_closed() -> None:
    contract = _contract()
    forbidden = contract["claim_boundary"]["forbidden_claims"]
    assert "response_equivalence_established" in forbidden
    assert "cost_superiority_established" in forbidden
    assert "generalization_beyond_registered_special_case" in forbidden
    gates = contract["gates"]
    assert gates["qw_lc0_semantics_scope_frozen"] is True
    assert gates["qw_lc1_transition_permitted"] is False
    assert gates["qw_lc1_open"] is False
    assert gates["local_compute_implementation_open"] is False
    assert gates["local_compute_execution_open"] is False
    assert gates["feature_collection_permitted"] is False
    assert gates["oracle_label_generation_open"] is False
    assert gates["scientific_execution_open"] is False
    assert gates["test_dataset_access"] is False
    assert gates["publication_permitted"] is False


def test_current_status_exposes_lc0_freeze_boundary() -> None:
    markers = (
        "qwake_qw_lc0_semantics_scope_frozen=true",
        f"qwake_qw_lc0_contract_id={CONTRACT_ID}",
        f"qwake_qw_lc0_contract_sha256={CONTRACT_SHA256}",
        "qwake_qw_lc1_transition_permitted=false",
        "qwake_qw_lc1_open=false",
        "qwake_local_compute_implementation_open=false",
        "qwake_local_compute_execution_open=false",
        "feature_collection_permitted=false",
        "oracle_label_generation_open=false",
        "policy_activation_permitted=false",
        "qwake_scientific_image_freeze_permitted=false",
        "scientific_execution_open=false",
        "test_dataset_access=false",
        "publication_permitted=false",
        "qwake_next_slice=QW-LC0-repository-freeze",
        "qwake_post_merge_next_slice=QW-LC1",
    )
    for name, heading in (
        ("STATUS.md", "## `QW-LC0`: семантика и область зафиксированы"),
        ("STATUS_EN.md", "## `QW-LC0`: semantics and scope frozen"),
    ):
        text = (ROOT / name).read_text(encoding="utf-8")
        section = text[text.index(heading):]
        for marker in markers:
            assert marker in section, (name, marker)
