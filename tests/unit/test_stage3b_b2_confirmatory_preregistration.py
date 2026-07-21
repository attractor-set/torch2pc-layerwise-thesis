from __future__ import annotations

import hashlib
import json
from itertools import product
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "experiments/planned/STAGE3B-B2-CONFIRMATORY-CONTRACT.json"


def _contract() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(CONTRACT_PATH.read_text(encoding="utf-8")))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_confirmatory_b2_is_preregistered_but_execution_closed() -> None:
    contract = _contract()
    assert contract["status"] == "preregistered_execution_closed"
    assert contract["execution_boundary"] == {
        "confirmatory_request_frozen": False,
        "immutable_image_built": False,
        "runtime_authorization_issued": False,
        "execution_started": False,
        "eq_b2_confirmatory_sealed": False,
        "derived_eq_b2_admission_present": False,
        "matched_profiling_refrozen": False,
        "matched_profiling_execution_open": False,
        "results_present": False,
    }


def test_confirmatory_matrix_resolves_to_120_unique_triples() -> None:
    scope = _contract()["scientific_scope"]
    triples = list(
        product(
            scope["lanes"],
            scope["methods"],
            scope["model_seeds"],
            scope["validation_batch_indices"],
        )
    )
    assert len(triples) == len(set(triples)) == 120
    assert scope["matched_triples"] == 120
    assert scope["pairwise_comparisons"] == 240
    assert scope["independent_unit"] == "model_seed"


def test_each_triple_has_exactly_two_registered_comparisons() -> None:
    comparison = _contract()["comparison_contract"]
    assert comparison["comparisons"] == [
        ["stage2_baseline", "composite_vjp"],
        ["isolated_layer_vjp", "composite_vjp"],
    ]
    assert comparison["comparisons_per_triple"] == 2
    assert comparison["registered_comparison_count"] == 240
    assert comparison["any_registered_disagreement_blocks_b2"] is True


def test_confirmatory_b2_reuses_exact_b1_inputs() -> None:
    reuse = _contract()["input_reuse"]
    assert reuse["new_validation_batch_selection"] is False
    assert reuse["exact_b1_validation_batch_reuse_required"] is True
    registry = reuse["validation_batch_registry"]
    request = reuse["b1_frozen_request"]
    assert registry["batch_indices"] == list(range(10))
    assert registry["batch_count"] == 10
    assert request["checkpoint_count"] == 3
    for item in (registry, request):
        path = ROOT / item["path"]
        assert path.is_file()
        assert _sha256(path) == item["sha256"]
    assert reuse["test_split_access"] is False


def test_preregistered_prerequisites_match_sealed_files() -> None:
    base = _contract()["preregistration_base"]
    for key in (
        "b1_confirmatory_decision",
        "b1_confirmatory_admission",
        "b2_smoke_decision",
        "b2_candidate_contract",
        "b2_implementation_contract",
    ):
        item = base[key]
        path = ROOT / item["path"]
        assert path.is_file()
        assert _sha256(path) == item["sha256"]
    assert base["b2_smoke_decision"]["production_admission"] is False


def test_thresholds_and_state_restoration_are_inherited_without_retuning() -> None:
    confirmatory = _contract()
    b2 = json.loads(
        (ROOT / "experiments/planned/STAGE3B-B2-CONTRACT.json").read_text(
            encoding="utf-8"
        )
    )
    assert confirmatory["threshold_profiles"] == b2["threshold_profiles"]
    assert confirmatory["state_restoration"] == b2["state_restoration"]
    assert confirmatory["pass_policy"]["threshold_retuning_after_output"] is False


def test_attempt_lifecycle_is_append_only_and_fail_closed() -> None:
    lifecycle = _contract()["attempt_lifecycle"]
    assert lifecycle["append_only"] is True
    assert lifecycle["max_attempts_per_triple"] == 2
    assert lifecycle["retry_eligible_classes"] == [
        "infrastructure",
        "operator_interruption",
        "system_interruption",
    ]
    assert lifecycle["non_retryable_classes"] == [
        "correctness",
        "scientific",
        "provenance",
        "unknown",
    ]
    assert lifecycle["exactly_one_completed_attempt_per_triple_required"] is True
    assert lifecycle["multiple_completed_attempts_rejected"] is True


def test_positive_decision_requires_complete_confirmatory_evidence() -> None:
    decision = _contract()["decision_contract"]
    assert decision["decision_id"] == "EQ-B2-CONFIRMATORY"
    assert decision["scope"] == "confirmatory"
    assert decision["confirmatory_equivalence_executed"] is True
    assert decision["matched_triples_expected"] == 120
    assert decision["matched_triples_observed_required"] == 120
    assert decision["pairwise_comparisons_expected"] == 240
    assert decision["pairwise_comparisons_observed_required"] == 240
    assert decision["failed_pair_count_required"] == 0
    assert decision["sealed_required"] is True
    assert decision["status_required"] == "pass"
    assert decision["derived_admission_decision_id"] == "EQ-B2"


def test_existing_matched_request_is_retained_but_not_production_admissible() -> None:
    existing = _contract()["existing_matched_profiling_artifacts"]
    assert existing["retained_unchanged"] is True
    assert existing["production_launch_admissible"] is False
    assert existing["replacement_after_confirmatory_b2"] == "new versioned freeze required"
    assert "modifying the existing matched-profiling request in place" in _contract()[
        "prohibited"
    ]


def test_status_and_roadmap_report_post_confirmatory_b2_boundary() -> None:
    for name in ("STATUS.md", "STATUS_EN.md", "ROADMAP.md", "ROADMAP_EN.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "scientific_admission=open" in text
        assert "b2_confirmatory_admission=present" in text
        assert "matched_profiling_request_refrozen=true" in text
        assert "matched_profiling_request_refresh_required=false" in text
        assert "matched_profiling_execution_complete=true" in text
        assert "matched_profiling_evidence=sealed" in text
        assert "matched_profiling_analysis_open=false" in text
        assert "runtime_authorization=issued_consumed" in text
        assert "measurements_allowed=false" in text
        assert "results_publication_permitted=false" in text
