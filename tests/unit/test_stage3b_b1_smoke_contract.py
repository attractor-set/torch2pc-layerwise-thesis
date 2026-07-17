from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "experiments/planned/STAGE3B-B1-SMOKE-HARNESS-CONTRACT.json"


def test_smoke_harness_contract_freezes_scope_without_execution() -> None:
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert payload["status"] == "harness_ready_execution_not_started"
    assert payload["scope"]["matched_pairs"] == 12
    assert payload["scope"]["test_split_access"] is False
    assert payload["scope"]["methods"] == ["FixedPred", "Strict"]
    assert payload["scope"]["model_seeds"] == [0, 1, 2]
    assert payload["scope"]["lanes"] == ["cpu_float64", "rocm_float32"]
    assert payload["dangerous_miss_limit"] == 0
    assert payload["execution_boundary"] == {
        "registered_cpu_smoke_executed": False,
        "registered_rocm_smoke_executed": False,
        "eq_b1_sealed": False,
        "results_present": False,
        "b2_implementation_present": False,
        "matched_profiling_executed": False,
        "future_policy_work_present": False,
    }


def test_smoke_harness_contract_requires_sealed_request_before_execution() -> None:
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    request_rule = payload["request_rule"]
    assert request_rule["sealed_before_execution"] is True
    assert request_rule["threshold_retuning_after_output"] is False
    assert request_rule["eta_and_inference_steps_must_come_from_resolved_training_metadata"] is True
