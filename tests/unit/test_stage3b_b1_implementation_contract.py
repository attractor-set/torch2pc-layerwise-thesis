from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[2]
PLANNED = ROOT / "experiments" / "planned"


def _load(name: str) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        json.loads((PLANNED / name).read_text(encoding="utf-8")),
    )


def test_b1_implementation_is_opt_in_and_pinned() -> None:
    implementation = _load("STAGE3B-B1-IMPLEMENTATION-CONTRACT.json")
    assert implementation["status"] == "implementation_ready_not_executed"
    assert implementation["project_base"]["preregistration_tag"] == (
        "stage3b-b1-b2-prereg-v1"
    )
    assert implementation["project_base"]["torch2pc_commit"] == (
        "b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4"
    )
    assert implementation["candidate"] == {
        "candidate_id": "isolated_layer_vjp",
        "module": "torch2pc_thesis.stage3b_b1_isolated_vjp",
        "entry_point": "load_b1_pc_infer",
        "opt_in_only": True,
        "canonical_reference_modified": False,
        "methods": ["FixedPred", "Strict"],
        "exact_supported": False,
    }


def test_b1_preserves_reference_parameter_vjp_boundary() -> None:
    implementation = _load("STAGE3B-B1-IMPLEMENTATION-CONTRACT.json")
    boundary = implementation["reference_boundary"]
    assert boundary["delegated_functions"] == ["FwdPassPlus", "SetPCGrads"]
    assert boundary["state_inference_helpers_delegated"] is False
    assert boundary["loss_backward_delegated"] is False
    assert boundary["parameter_vjp_path_unchanged"] is True
    structural = implementation["structural_contract"]
    assert structural["one_graph_island_per_logical_upper_state_edge"] is True
    assert structural["cross_layer_composite_state_vjp"] is False
    assert structural["graph_span"] == 1
    assert structural["graph_lifetime"] == "single_vjp_call"


def test_implementation_does_not_open_execution_or_b2() -> None:
    implementation = _load("STAGE3B-B1-IMPLEMENTATION-CONTRACT.json")
    execution = implementation["execution_boundary"]
    assert execution["synthetic_unit_tests_allowed"] is True
    assert execution["registered_cpu_smoke_executed"] is False
    assert execution["registered_rocm_smoke_executed"] is False
    assert execution["confirmatory_equivalence_executed"] is False
    assert execution["matched_profiling_executed"] is False
    assert execution["b2_implementation_present"] is False
    assert execution["results_present"] is False
    assert execution["test_split_access"] is False


def test_preregistration_contract_remains_immutable() -> None:
    preregistration = _load("STAGE3B-B1-CONTRACT.json")
    assert preregistration["status"] == "preregistered"
    assert preregistration["implementation_present"] is False
    assert preregistration["results_present"] is False
    assert preregistration["candidate"]["candidate_id"] == "isolated_layer_vjp"
