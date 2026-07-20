from __future__ import annotations

import json
from itertools import product
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = (
    ROOT
    / "experiments"
    / "planned"
    / "STAGE3B-B1-CONFIRMATORY-CONTRACT.json"
)


def _contract() -> dict[str, Any]:
    return cast(
        dict[str, Any],
        json.loads(CONTRACT_PATH.read_text(encoding="utf-8")),
    )


def test_confirmatory_b1_is_preregistered_but_execution_closed() -> None:
    contract = _contract()
    assert contract["status"] == "preregistered_execution_closed"
    boundary = contract["execution_boundary"]
    assert boundary == {
        "confirmatory_request_frozen": False,
        "eq_b1_confirmatory_sealed": False,
        "execution_started": False,
        "immutable_image_built": False,
        "matched_profiling_open": False,
        "results_present": False,
        "runtime_authorization_issued": False,
        "validation_batches_frozen": False,
    }


def test_confirmatory_matrix_resolves_to_exactly_120_unique_pairs() -> None:
    scope = _contract()["scientific_scope"]
    tuples = list(
        product(
            scope["lanes"],
            scope["methods"],
            scope["model_seeds"],
            scope["validation_batch_indices"],
        )
    )
    assert len(tuples) == len(set(tuples)) == 120
    assert scope["matched_pairs"] == 120
    assert scope["batches_per_seed"] == 10
    assert scope["independent_unit"] == "model_seed"


def test_confirmatory_uses_ten_distinct_validation_batch_indices() -> None:
    contract = _contract()
    scope = contract["scientific_scope"]
    freeze = contract["validation_batch_freeze"]
    assert scope["validation_batch_indices"] == list(range(10))
    assert freeze["batch_indices"] == list(range(10))
    assert freeze["distinct_batch_count"] == 10
    assert freeze["same_batch_may_not_fill_multiple_indices"] is True
    assert freeze["artifact_per_batch_required"] is True
    assert freeze["manifest_per_batch_required"] is True
    assert freeze["sha256_per_batch_required"] is True
    assert freeze["selected_before_execution"] is True
    assert freeze["include_test"] is False
    assert freeze["test_split_accessed"] is False


def test_pair_identity_covers_all_registered_factors() -> None:
    identity = _contract()["pair_identity"]
    assert identity["fields"] == [
        "lane",
        "method",
        "model_seed",
        "validation_batch_index",
    ]
    assert identity["unique_pair_ids_required"] == 120
    assert identity["deterministic_order"] == identity["fields"]


def test_thresholds_are_identical_to_the_b1_candidate_contract() -> None:
    confirmatory = _contract()
    candidate = json.loads(
        (ROOT / "experiments/planned/STAGE3B-B1-CONTRACT.json").read_text(
            encoding="utf-8"
        )
    )
    assert confirmatory["threshold_profiles"] == candidate["threshold_profiles"]
    assert confirmatory["state_restoration"] == candidate["state_restoration"]
    assert confirmatory["optimizer"] == candidate["optimizer_control"]


def test_attempt_lifecycle_is_append_only_and_fail_closed() -> None:
    lifecycle = _contract()["attempt_lifecycle"]
    assert lifecycle["append_only"] is True
    assert lifecycle["max_attempts_per_pair"] == 2
    assert lifecycle["retry_eligible_classes"] == [
        "infrastructure",
        "operator_interruption",
        "system_interruption",
    ]
    assert "correctness" in lifecycle["non_retryable_classes"]
    assert "scientific" in lifecycle["non_retryable_classes"]
    assert lifecycle["exactly_one_completed_attempt_per_pair_required"] is True
    assert lifecycle["multiple_completed_attempts_rejected"] is True


def test_positive_decision_requires_complete_confirmatory_evidence() -> None:
    decision = _contract()["decision_contract"]
    assert decision["decision_id"] == "EQ-B1-CONFIRMATORY"
    assert decision["scope"] == "confirmatory"
    assert decision["confirmatory_equivalence_executed"] is True
    assert decision["registered_pair_count"] == 120
    assert decision["observed_pair_count_required"] == 120
    assert decision["failed_pair_count_required"] == 0
    assert decision["sealed_required"] is True
    assert decision["status_required"] == "pass"


def test_confirmatory_b1_does_not_open_matched_profiling() -> None:
    contract = _contract()
    assert contract["execution_boundary"]["matched_profiling_open"] is False
    effect = contract["decision_contract"]["production_admission_effect"]
    assert "B2 confirmatory" in effect
    assert "does not open matched profiling" in effect
    assert "test split access" in contract["prohibited"]
    assert "treating 120 pairs as 120 independent statistical units" in contract[
        "prohibited"
    ]
