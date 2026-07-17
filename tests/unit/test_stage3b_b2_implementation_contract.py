from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[2]
PLANNED = ROOT / "experiments" / "planned"


def _load(path: Path) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        json.loads(path.read_text(encoding="utf-8")),
    )


def test_b2_implementation_is_opt_in_and_pinned() -> None:
    implementation = _load(PLANNED / "STAGE3B-B2-IMPLEMENTATION-CONTRACT.json")
    assert implementation["status"] == "implementation_ready_not_executed"
    assert implementation["project_base"] == {
        "main_merge_commit_short": "1a90644",
        "eq_b1_decision_commit_short": "7c8df38",
        "preregistration_tag": "stage3b-b1-b2-prereg-v1",
        "torch2pc_commit": (
            "b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4"
        ),
    }
    assert implementation["candidate"] == {
        "candidate_id": "composite_vjp",
        "module": "torch2pc_thesis.stage3b_b2_composite_vjp",
        "entry_point": "load_b2_pc_infer",
        "opt_in_only": True,
        "canonical_reference_modified": False,
        "methods": ["FixedPred", "Strict"],
        "exact_supported": False,
    }


def test_b2_opening_gate_is_positive_sealed_eq_b1() -> None:
    implementation = _load(PLANNED / "STAGE3B-B2-IMPLEMENTATION-CONTRACT.json")
    gate = implementation["opening_gate"]
    assert gate == {
        "decision_id": "EQ-B1",
        "required_status": "pass",
        "required_sealed": True,
        "evidence_path": (
            "results/stage-3/b1/"
            "stage3b-b1-smoke-attempt-001/decision.json"
        ),
    }

    decision_path = ROOT / gate["evidence_path"]
    assert decision_path.is_file()
    decision = _load(decision_path)
    assert decision["decision_id"] == "EQ-B1"
    assert decision["status"] == "pass"
    assert decision["sealed"] is True


def test_b2_structural_contract_matches_preregistration() -> None:
    implementation = _load(PLANNED / "STAGE3B-B2-IMPLEMENTATION-CONTRACT.json")
    structural = implementation["structural_contract"]
    assert structural["one_composite_state_vjp_per_sweep"] is True
    assert structural[
        "registered_outputs_and_inputs_cover_all_logical_upper_state_edges"
    ] is True
    assert structural["per_layer_state_vjp_calls"] is False
    assert structural["chunked_or_block_composite_fallback"] is False
    assert structural["layer_update_order_matches_reference"] is True
    assert structural["state_snapshot_version_matches_reference"] is True
    assert structural["graph_lifetime"] == "single_sweep_composite_vjp_call"
    assert structural["events"] == [
        "logical_edge_count",
        "composite_vjp_call_count",
        "graph_module_set",
        "graph_span",
        "graph_lifetime",
    ]


def test_b2_preserves_reference_and_future_policy_boundaries() -> None:
    implementation = _load(PLANNED / "STAGE3B-B2-IMPLEMENTATION-CONTRACT.json")
    boundary = implementation["reference_boundary"]
    assert boundary["delegated_functions"] == ["FwdPassPlus", "SetPCGrads"]
    assert boundary["state_inference_helpers_delegated"] is False
    assert boundary["loss_backward_delegated"] is False
    assert boundary["parameter_vjp_path_unchanged"] is True

    execution = implementation["execution_boundary"]
    assert execution["registered_cpu_smoke_executed"] is False
    assert execution["registered_rocm_smoke_executed"] is False
    assert execution["confirmatory_equivalence_executed"] is False
    assert execution["matched_profiling_executed"] is False
    assert execution["results_present"] is False
    assert execution["test_split_access"] is False

    future = implementation["future_policy_boundary"]
    assert not any(future.values())


def test_preregistered_b2_contract_remains_immutable() -> None:
    preregistration = _load(PLANNED / "STAGE3B-B2-CONTRACT.json")
    assert preregistration["status"] == "preregistered"
    assert preregistration["implementation_present"] is False
    assert preregistration["results_present"] is False
    assert preregistration["candidate"]["candidate_id"] == "composite_vjp"
    structural = preregistration["candidate"]["structural_contract"]
    assert structural["one_composite_state_vjp_per_sweep"] is True
    assert structural["per_layer_state_vjp_calls_forbidden"] is True
    assert structural["chunked_or_block_composite_fallback_forbidden"] is True
