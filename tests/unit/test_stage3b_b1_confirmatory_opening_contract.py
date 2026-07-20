from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OPENING = PROJECT_ROOT / "experiments/planned/STAGE3B-B1-CONFIRMATORY-OPENING.json"


def test_opening_contract_is_implementation_ready_but_execution_closed() -> None:
    payload = json.loads(OPENING.read_text(encoding="utf-8"))
    assert payload["opening_id"] == "stage3b-b1-confirmatory-opening-v1"
    assert payload["status"] == "implementation_ready_execution_closed"
    assert payload["registered_pair_count"] == 120
    assert payload["lanes"] == ["cpu_float64", "rocm_float32"]
    boundary = payload["execution_boundary"]
    assert boundary["frozen_batches_present"] is False
    assert boundary["frozen_request_present"] is False
    assert boundary["authorization_issued"] is False
    assert boundary["confirmatory_execution_started"] is False
    assert boundary["eq_b1_confirmatory_sealed"] is False
    assert boundary["eq_b2_open"] is False
    assert boundary["matched_profiling_open"] is False
    sealing = payload["sealing_requirements"]
    assert sealing["scientific_decision_id"] == "EQ-B1-CONFIRMATORY"
    assert sealing["matched_profiling_admission_decision_id"] == "EQ-B1"
    assert sealing["matched_profiling_expected_pairs"] == 120
    assert sealing["matched_profiling_observed_pairs"] == 120
    assert sealing["admission_binds_scientific_decision_sha256"] is True


def test_opening_contract_references_existing_runtime_components() -> None:
    payload = json.loads(OPENING.read_text(encoding="utf-8"))
    paths = list(payload["runtime_scripts"].values()) + list(payload["runtime_modules"].values())
    for relative in paths:
        assert (PROJECT_ROOT / relative).is_file(), relative


def test_engineering_smoke_is_non_evidence_and_not_sealable() -> None:
    payload = json.loads(OPENING.read_text(encoding="utf-8"))
    smoke = payload["engineering_smoke"]
    assert smoke["pair_count"] == 12
    assert smoke["dedicated_output_root_and_authorization_required"] is True
    assert smoke["authorization_domain_must_differ_from_confirmatory"] is True
    authorization = payload["authorization_requirements"]
    assert authorization["authorization_domains_separated"] is True
    assert authorization["confirmatory_authorized_pair_count"] == 120
    assert authorization["engineering_smoke_authorized_pair_count"] == 12
    assert authorization["confirmatory_execution_mode"] == "confirmatory"
    assert authorization["engineering_smoke_execution_mode"] == "engineering_smoke"
    assert smoke["evidence"] is False
    assert smoke["sealing_as_confirmatory_prohibited"] is True


def test_recovery_contract_is_fail_closed() -> None:
    payload = json.loads(OPENING.read_text(encoding="utf-8"))
    recovery = payload["recovery_contract"]
    assert recovery["max_attempts_per_pair"] == 2
    assert recovery["resume_selects_pending_pairs"] is True
    assert recovery["retry_failed_requires_resume"] is True
    assert set(recovery["retryable_failure_classes"]) == {
        "infrastructure",
        "operator_interruption",
        "system_interruption",
    }
    assert "correctness" in recovery["non_retryable_failure_classes"]
    assert "scientific" in recovery["non_retryable_failure_classes"]
