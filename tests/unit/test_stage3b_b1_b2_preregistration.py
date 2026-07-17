from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

ROOT = Path(__file__).resolve().parents[2]
PLANNED = ROOT / "experiments" / "planned"
BASE_COMMIT = "e4893545b89d0cfad76f3039c58a997b5c97820c"
THEORY_TAG = "stage3b-pc-tref-pc-catm-theory-v1"


def load_contract(candidate: str) -> dict[str, Any]:
    path = PLANNED / f"STAGE3B-{candidate}-CONTRACT.json"
    return cast(
        dict[str, Any],
        json.loads(path.read_text(encoding="utf-8")),
    )


@pytest.fixture(scope="module")
def contracts() -> dict[str, dict[str, Any]]:
    return {
        "B1": load_contract("B1"),
        "B2": load_contract("B2"),
    }


def test_contracts_are_preregistered_without_implementation_or_results(
    contracts: dict[str, dict[str, Any]],
) -> None:
    assert {
        name: contract["candidate"]["candidate_id"]
        for name, contract in contracts.items()
    } == {
        "B1": "isolated_layer_vjp",
        "B2": "composite_vjp",
    }

    for contract in contracts.values():
        assert contract["status"] == "preregistered"
        assert contract["implementation_present"] is False
        assert contract["results_present"] is False
        assert contract["preregistration_base"]["project_commit"] == BASE_COMMIT
        assert contract["preregistration_base"]["theory_tag"] == THEORY_TAG
        assert contract["equivalence_scope"]["test_split_access"] is False
        assert contract["pass_policy"]["test_split_access"] is False


def test_contracts_share_the_same_numerical_and_norm_boundaries(
    contracts: dict[str, dict[str, Any]],
) -> None:
    b1 = contracts["B1"]
    b2 = contracts["B2"]

    assert b1["threshold_profiles"] == b2["threshold_profiles"]
    assert b1["norm_contract"] == b2["norm_contract"]
    assert b1["state_restoration"] == b2["state_restoration"]
    assert b1["full_trajectory_endpoints"] == b2["full_trajectory_endpoints"]
    assert b1["optimizer_control"] == b2["optimizer_control"]

    assert b1["threshold_profiles"] == {
        "cpu_float64": {
            "min_cosine": 0.99999,
            "max_relative_l2": 1e-7,
            "max_abs": 1e-9,
            "zero_atol": 1e-12,
        },
        "rocm_float32": {
            "min_cosine": 0.999,
            "max_relative_l2": 1e-3,
            "max_abs": 1e-5,
            "zero_atol": 1e-7,
        },
    }


def test_equivalence_cardinalities_are_exact(
    contracts: dict[str, dict[str, Any]],
) -> None:
    for contract in contracts.values():
        scope = contract["equivalence_scope"]
        method_count = len(scope["methods"])
        smoke_pairs = (
            len(scope["smoke"]["lanes"])
            * method_count
            * len(scope["smoke"]["model_seeds"])
            * scope["smoke"]["batches_per_seed"]
        )
        confirmatory_pairs = (
            len(scope["confirmatory_equivalence"]["lanes"])
            * method_count
            * len(scope["confirmatory_equivalence"]["model_seeds"])
            * scope["confirmatory_equivalence"]["batches_per_seed"]
        )

        assert smoke_pairs == scope["smoke"]["matched_pairs"] == 12
        assert (
            confirmatory_pairs
            == scope["confirmatory_equivalence"]["matched_pairs"]
            == 120
        )
        assert scope["independent_unit"] == "model_seed"


def test_b1_structural_contract_is_isolated(
    contracts: dict[str, dict[str, Any]],
) -> None:
    structural = contracts["B1"]["candidate"]["structural_contract"]
    assert structural["one_graph_island_per_logical_upper_state_edge"] is True
    assert structural["cross_layer_composite_state_vjp"] is False
    assert structural["reference_vjp_helper_delegation_forbidden"] is True


def test_b2_requires_direct_b1_control(
    contracts: dict[str, dict[str, Any]],
) -> None:
    direct = contracts["B2"]["direct_comparison"]
    assert direct["required_control_candidate"] == "isolated_layer_vjp"
    assert direct["smoke_matched_triples"] == 12
    assert direct["smoke_pairwise_comparisons"] == 24
    assert direct["confirmatory_matched_triples"] == 120
    assert direct["confirmatory_pairwise_comparisons"] == 240
    assert direct["block_composite_variant_requires_new_preregistration"] is True
    assert direct["any_b1_b2_disagreement_blocks_b2"] is True


def test_profiling_lanes_and_observer_cost_are_separate(
    contracts: dict[str, dict[str, Any]],
) -> None:
    for contract in contracts.values():
        scope = contract["profiling_scope"]
        assert scope["cells_per_candidate"] == 96
        assert scope["measurement_lanes"]["primary_timing"][
            "observer_mode"
        ] == "no_hooks"
        assert scope["measurement_lanes"]["structural_counters"][
            "observer_mode"
        ] == "counters_only"
        assert scope["observer_cost_rule"][
            "not_subtracted_from_primary_timing"
        ] is True
        assert scope["hidden_scalar_score_forbidden"] is True


def test_pass_and_replacement_policies_are_immutable(
    contracts: dict[str, dict[str, Any]],
) -> None:
    for contract in contracts.values():
        policy = contract["pass_policy"]
        replacement = contract["replacement_policy"]
        assert policy["all_runs_must_pass"] is True
        assert policy["dangerous_miss_limit"] == 0
        assert policy["threshold_retuning_after_output"] is False
        assert policy["outlier_deletion"] is False
        assert replacement["scientific_failure_replacement"] is False
        assert replacement["original_failure_retained"] is True


def test_sequential_admission_and_gate_hierarchy(
    contracts: dict[str, dict[str, Any]],
) -> None:
    assert contracts["B1"]["execution_and_replacement"][
        "implementation_opens_after_tag"
    ] == "stage3b-b1-b2-prereg-v1"
    assert contracts["B2"]["execution_and_replacement"][
        "implementation_opens_after"
    ] == "sealed EQ-B1 evidence"
    assert contracts["B1"]["gate_hierarchy"]["equivalence"] == "EQ-B1"
    assert contracts["B2"]["gate_hierarchy"]["equivalence"] == "EQ-B2"
    for contract in contracts.values():
        assert contract["execution_and_replacement"]["test_split_access"] is False
        assert contract["execution_and_replacement"][
            "scientific_failure_retained"
        ] is True
