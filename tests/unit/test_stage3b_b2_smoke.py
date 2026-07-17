from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from torch2pc_thesis.stage3b_b1_equivalence import canonical_json_digest
from torch2pc_thesis.stage3b_b1_isolated_vjp import PATCHED_TORCH2PC_COMMIT
from torch2pc_thesis.stage3b_b2_composite_vjp import B2StructuralEvent
from torch2pc_thesis.stage3b_b2_smoke import (
    B1_DECISION_COMMIT,
    B1_IMPLEMENTATION_COMMIT,
    B2_IMPLEMENTATION_COMMIT,
    B2_IMPLEMENTATION_TAG,
    CANDIDATE_ID,
    CONTROL_CANDIDATE_ID,
    EXPECTED_MATCHED_TRIPLES,
    EXPECTED_PAIRWISE_COMPARISONS,
    PROJECT_BASE_COMMIT,
    REFERENCE_ID,
    PairSpec,
    _structural_gate,
    aggregate_attempt,
    build_pair_specs,
    validate_request,
)

SHA = "a" * 64


def request_payload() -> dict[str, Any]:
    resolved_config = {
        "resolution_id": "stage3b-b2-smoke-resolved-v1",
        "dataset": "FashionMNIST",
        "candidate_id": CANDIDATE_ID,
    }
    assets = {
        str(seed): {"path": f"asset-{seed}.pt", "sha256": SHA} for seed in (0, 1, 2)
    }
    return {
        "schema_version": 1,
        "request_id": "stage3b-b2-smoke-v1",
        "attempt_id": "stage3b-b2-smoke-attempt-001",
        "scope": "smoke",
        "dataset": "FashionMNIST",
        "split": "validation",
        "architecture": "lenet_classic",
        "methods": ["FixedPred", "Strict"],
        "model_seeds": [0, 1, 2],
        "batches_per_seed": 1,
        "lanes": ["cpu_float64", "rocm_float32"],
        "matched_triples": EXPECTED_MATCHED_TRIPLES,
        "pairwise_comparisons": EXPECTED_PAIRWISE_COMPARISONS,
        "candidate_id": CANDIDATE_ID,
        "control_candidate_id": CONTROL_CANDIDATE_ID,
        "reference_id": REFERENCE_ID,
        "observer_mode": "no_hooks",
        "structural_observer_mode": "counters_only",
        "test_split_access": False,
        "dangerous_miss_limit": 0,
        "torch2pc_commit": PATCHED_TORCH2PC_COMMIT,
        "project_base_commit": PROJECT_BASE_COMMIT,
        "b1_implementation_commit": B1_IMPLEMENTATION_COMMIT,
        "b1_decision_commit": B1_DECISION_COMMIT,
        "b2_implementation_commit": B2_IMPLEMENTATION_COMMIT,
        "b2_implementation_tag": B2_IMPLEMENTATION_TAG,
        "resolved_config": resolved_config,
        "resolved_config_digest": canonical_json_digest(resolved_config),
        "source_image_digest": "b" * 64,
        "run_seed_base": 20260717,
        "training_mode": True,
        "optimizer": {
            "name": "SGD",
            "learning_rate": 0.001,
            "momentum": 0.0,
        },
        "lane_controls": {
            "cpu_float64": {"device": "cpu", "dtype": "float64"},
            "rocm_float32": {"device": "cuda", "dtype": "float32"},
        },
        "method_controls": {
            "FixedPred": {"eta": 0.1, "inference_steps": 10},
            "Strict": {"eta": 0.05, "inference_steps": 20},
        },
        "checkpoints": assets,
        "batches": assets,
        "b1_decision": {"path": "decision.json", "sha256": SHA},
        "b2_preregistration_contract": {
            "path": "prereg.json",
            "sha256": SHA,
        },
        "b2_implementation_contract": {
            "path": "implementation.json",
            "sha256": SHA,
        },
        "b2_harness_contract": {"path": "harness.json", "sha256": SHA},
    }


def test_request_resolves_registered_twelve_triples() -> None:
    payload = request_payload()
    validate_request(payload)
    specs = build_pair_specs(payload)

    assert len(specs) == 12
    assert len({spec.pair_id for spec in specs}) == 12
    assert [spec.lane for spec in specs[:6]] == ["cpu_float64"] * 6
    assert [spec.lane for spec in specs[6:]] == ["rocm_float32"] * 6
    assert {spec.method for spec in specs} == {"FixedPred", "Strict"}
    assert {spec.model_seed for spec in specs} == {0, 1, 2}


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("candidate_id", "other"),
        ("control_candidate_id", "other"),
        ("matched_triples", 11),
        ("pairwise_comparisons", 12),
        ("test_split_access", True),
        ("dangerous_miss_limit", 1),
        ("b2_implementation_commit", "0" * 40),
    ],
)
def test_request_rejects_scope_drift(key: str, value: object) -> None:
    payload = request_payload()
    payload[key] = value

    with pytest.raises(ValueError):
        validate_request(payload)


def test_request_rejects_resolved_config_digest_mismatch() -> None:
    payload = request_payload()
    payload["resolved_config"]["dataset"] = "MNIST"

    with pytest.raises(ValueError, match="resolved_config_digest"):
        validate_request(payload)


def test_structural_gate_accepts_one_full_composite_event_per_sweep() -> None:
    spec = build_pair_specs(request_payload())[0]
    events = [
        B2StructuralEvent(
            candidate_id="composite_vjp",
            method="FixedPred",
            sweep_index=sweep,
            layer_indices=(0, 1, 2),
            logical_edge_count=3,
        )
        for sweep in range(spec.method_control.inference_steps)
    ]

    gate = _structural_gate(spec, events, model_depth=3)

    assert gate.passed
    assert gate.reasons == ()


def test_structural_gate_rejects_partial_or_relabelled_graph() -> None:
    spec = build_pair_specs(request_payload())[0]
    events = [
        B2StructuralEvent(
            candidate_id="not-composite",
            method="FixedPred",
            sweep_index=sweep,
            layer_indices=(0, 1),
            logical_edge_count=2,
        )
        for sweep in range(spec.method_control.inference_steps)
    ]

    gate = _structural_gate(spec, events, model_depth=3)

    assert not gate.passed
    assert "candidate_id" in gate.reasons
    assert "graph_module_set" in gate.reasons


def _write_complete_pair(root: Path, spec: PairSpec, *, passed: bool = True) -> None:
    pair_dir = root / "pairs" / spec.pair_id
    pair_dir.mkdir(parents=True)
    gates: dict[str, dict[str, object]] = {
        gate_id: {"gate_id": gate_id, "passed": passed, "reasons": []}
        for gate_id in ("STRUCT-B2", "NUM-B2", "TRAJ-B2", "OBS-B2", "PROV-B2")
    }
    (pair_dir / "pair.json").write_text(
        json.dumps(
            {
                "pair_id": spec.pair_id,
                "gates": gates,
                "pair_admissible": passed,
            }
        ),
        encoding="utf-8",
    )
    for filename in (
        "trajectory-metrics.csv",
        "endpoint-metrics.csv",
        "direct-b1-b2-metrics.csv",
    ):
        (pair_dir / filename).write_text(
            f"pair_id,passed\n{spec.pair_id},{str(passed)}\n",
            encoding="utf-8",
        )
    (pair_dir / "structural-events.jsonl").write_text(
        json.dumps({"candidate_id": CANDIDATE_ID}) + "\n",
        encoding="utf-8",
    )


def test_aggregate_seals_positive_eq_b2(tmp_path: Path) -> None:
    request = request_payload()
    attempt_root = tmp_path / "attempt"
    for spec in build_pair_specs(request):
        _write_complete_pair(attempt_root, spec)

    decision = aggregate_attempt(request, attempt_root)

    assert decision["decision_id"] == "EQ-B2"
    assert decision["status"] == "pass"
    assert decision["sealed"] is True
    assert decision["matched_triples_observed"] == 12
    assert decision["pairwise_comparisons_observed"] == 24
    assert decision["failed_pairs"] == []
    assert (attempt_root / "direct-b1-b2-metrics.csv").is_file()
    assert (attempt_root / "SHA256SUMS").is_file()


@pytest.mark.parametrize("failed_index", [0, 11])
def test_aggregate_seals_negative_eq_b2(tmp_path: Path, failed_index: int) -> None:
    request = request_payload()
    attempt_root = tmp_path / "attempt"
    for index, spec in enumerate(build_pair_specs(request)):
        _write_complete_pair(attempt_root, spec, passed=index != failed_index)

    decision = aggregate_attempt(request, attempt_root)

    assert decision["status"] == "fail"
    assert len(decision["failed_pairs"]) == 1
    assert decision["sealed"] is True


def test_aggregate_is_append_only(tmp_path: Path) -> None:
    request = request_payload()
    attempt_root = tmp_path / "attempt"
    for spec in build_pair_specs(request):
        _write_complete_pair(attempt_root, spec)
    aggregate_attempt(request, attempt_root)

    with pytest.raises(FileExistsError, match="Append-only"):
        aggregate_attempt(request, attempt_root)


def test_aggregate_rejects_incomplete_attempt(tmp_path: Path) -> None:
    request = request_payload()
    attempt_root = tmp_path / "attempt"
    specs = build_pair_specs(request)
    for spec in specs[:-1]:
        _write_complete_pair(attempt_root, spec)

    with pytest.raises(RuntimeError, match="Incomplete B2 smoke attempt"):
        aggregate_attempt(request, attempt_root)
