from __future__ import annotations

import json
from pathlib import Path

CONTRACT = Path("experiments/planned/STAGE3B-B2-SMOKE-HARNESS-CONTRACT.json")


def test_b2_smoke_harness_contract_freezes_registered_scope() -> None:
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))

    assert payload["contract_id"] == "stage3b-b2-smoke-harness-v1"
    assert payload["status"] == "implementation_only"
    assert payload["candidate_id"] == "composite_vjp"
    assert payload["required_control_candidate_id"] == "isolated_layer_vjp"
    assert payload["reference_id"] == "stage2_baseline"

    matrix = payload["matrix"]
    assert matrix == {
        "dataset": "FashionMNIST",
        "architecture": "lenet_classic",
        "methods": ["FixedPred", "Strict"],
        "model_seeds": [0, 1, 2],
        "batches_per_seed": 1,
        "lanes": ["cpu_float64", "rocm_float32"],
        "matched_triples": 12,
        "pairwise_comparisons": 24,
        "split": "validation",
        "test_split_access": False,
    }


def test_b2_smoke_harness_contract_freezes_structural_boundary() -> None:
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    structural = payload["structural_invariants"]

    assert structural["composite_state_vjp_calls_per_sweep"] == 1
    assert structural["isolated_state_vjp_calls_per_sweep"] == 0
    assert structural["block_or_chunk_fallback_calls"] == 0
    assert structural["parameter_vjp_path"] == "SetPCGrads"
    assert structural["state_update_order"] == "reverse_layer_order"
    assert structural["graph_lifetime"] == "single_sweep_composite_vjp_call"


def test_b2_smoke_harness_contract_requires_direct_b1_b2_evidence() -> None:
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))

    assert payload["comparison_plan"] == {
        "primary": "stage2_baseline_vs_composite_vjp",
        "required_direct_control": "isolated_layer_vjp_vs_composite_vjp",
    }
    assert "direct-b1-b2-metrics.csv" in payload["required_pair_artifacts"]
    assert "direct-b1-b2-metrics.csv" in payload["required_attempt_artifacts"]
    assert payload["gate_order"] == [
        "STRUCT-B2",
        "NUM-B2",
        "TRAJ-B2",
        "OBS-B2",
        "PROV-B2",
        "EQ-B2",
    ]


def test_b2_smoke_harness_contract_forbids_execution_evidence() -> None:
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    forbidden = set(payload["forbidden_in_this_change"])

    assert {
        "sealed_request",
        "execution_results",
        "profiling_results",
        "performance_claims",
        "b2_candidate_changes",
        "b1_evidence_changes",
        "test_split_access",
    } <= forbidden
