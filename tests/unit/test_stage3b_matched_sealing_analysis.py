from __future__ import annotations

import hashlib
import json
from pathlib import Path

from torch2pc_thesis.stage3b_matched_analysis import generate_matched_analysis
from torch2pc_thesis.stage3b_matched_sealing import (
    seal_matched_runtime,
    validate_sealed_matched_evidence,
)

SOURCE = "a" * 40
IMAGE = "sha256:" + "b" * 64
TOKEN = "c" * 64
CANDIDATES = (
    "stage2_baseline",
    "isolated_layer_vjp",
    "composite_vjp",
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest() -> dict[str, object]:
    cells = []
    for order, candidate in enumerate(CANDIDATES):
        cells.append(
            {
                "cell_id": f"cell-{candidate}",
                "block_id": "block-0",
                "block_order": 0,
                "candidate_order": order,
                "candidate_id": candidate,
                "method": "fixedpred",
                "depth": 4,
                "width": 64,
                "batch_size": 64,
                "model_seed": 70,
            }
        )
    return {
        "manifest_digest": "d" * 64,
        "protocol": {
            "warmup_steps": 1,
            "measured_steps": 2,
            "repetitions": 1,
            "independent_unit": "model_seed",
            "candidate_order": "test",
        },
        "cells": cells,
    }


def _write_attempt(root: Path, cell: dict[str, object], *, scale: float) -> None:
    attempt = (
        root
        / "matched/lanes/rocm-float32/cells"
        / str(cell["cell_id"])
        / "attempts/attempt-0"
    )
    attempt.mkdir(parents=True)
    shared = {
        "cell_id": cell["cell_id"],
        "candidate_id": cell["candidate_id"],
        "method": cell["method"],
        "authorization_token": TOKEN,
        "source_commit": SOURCE,
        "image_digest": IMAGE,
    }
    (attempt / "request.json").write_text(
        json.dumps(shared), encoding="utf-8"
    )
    (attempt / "started.json").write_text(
        json.dumps(shared | {"status": "matched_cell_running"}),
        encoding="utf-8",
    )
    (attempt / "completed.json").write_text(
        json.dumps(shared | {"status": "matched_cell_complete"}),
        encoding="utf-8",
    )
    config = {
        **cell,
        "architecture": "mlp_d4_w64",
        "inference_steps": 2,
    }
    (attempt / "resolved-config.json").write_text(
        json.dumps(config), encoding="utf-8"
    )
    environment = {
        "project_source_commit": SOURCE,
        "container_image_digest": IMAGE,
        "authorization_token": TOKEN,
    }
    (attempt / "environment.json").write_text(
        json.dumps(environment), encoding="utf-8"
    )
    primary = []
    structural_timing = []
    observer = []
    structural = []
    integrity = []
    regions = []
    events = []
    for step in range(2):
        primary.append(
            {
                "candidate_id": cell["candidate_id"],
                "repetition": 0,
                "step": step,
                "measurement_lane": "primary_timing",
                "observer_mode": "no_hooks",
                "host_time_us": 100.0 * scale,
                "device_time_us": 80.0 * scale,
                "peak_allocated_bytes": int(1000 * scale),
                "peak_reserved_bytes": int(2000 * scale),
                "synchronization_points": 2,
            }
        )
        structural_timing.append(
            {
                **primary[-1],
                "measurement_lane": "structural_counters",
                "observer_mode": "counters_only",
                "host_time_us": 120.0 * scale,
                "device_time_us": 90.0 * scale,
            }
        )
        observer.append(
            {
                "candidate_id": cell["candidate_id"],
                "method": cell["method"],
                "repetition": 0,
                "step": step,
                "observer_cost_ms": 0.01,
            }
        )
        structural.append(
            {
                "candidate_id": cell["candidate_id"],
                "method": cell["method"],
                "repetition": 0,
                "step": step,
                "event_count": 1,
                "state_vjp_calls": 4,
                "logical_edge_count": 4,
                "graph_island_count": 1,
                "graph_module_sets": [[0]],
                "graph_span": 1,
                "dependency_radius": 1,
                "graph_lifetimes": ["single_vjp_call"],
                "freedom_points": ["single_vjp_call"],
                "feedback_operator": "exact_test",
                "orchestration_barriers": 0,
                "structural_source": "test",
                "fallback_validation_cost_ms": None,
                "fallback_validation_status": "not_applicable_before_ex_if0",
            }
        )
        integrity.append(
            {
                "candidate_id": cell["candidate_id"],
                "repetition": 0,
                "step": step,
                "passed": True,
            }
        )
        for region in (
            "initial_forward",
            "state_inference",
            "local_state_vjp",
            "parameter_vjp",
            "optimizer_step",
        ):
            regions.append(
                {
                    "candidate_id": cell["candidate_id"],
                    "method": cell["method"],
                    "repetition": 0,
                    "step": step,
                    "region": region,
                    "host_time_us": 1.0,
                    "device_time_us": 1.0,
                    "peak_allocated_bytes": 1,
                    "peak_reserved_bytes": 1,
                    "vjp_calls": 1,
                    "synchronization_points": 2,
                    "saved_tensor_bytes": 10,
                    "actual_inference_steps": 2,
                    "non_finite_events": 0,
                }
            )
        events.append(
            {
                "cell_id": cell["cell_id"],
                "block_id": cell["block_id"],
                "candidate_id": cell["candidate_id"],
                "method": cell["method"],
                "repetition": 0,
                "step": step,
                "dependency_radius": 1,
            }
        )
    event_path = attempt / "locality-events.jsonl"
    event_path.write_text(
        "".join(json.dumps(event) + "\n" for event in events),
        encoding="utf-8",
    )
    measurements = {
        "status": "matched_cell_complete",
        "evidence": False,
        "test_dataset_access": False,
        "warmup_gate_count": 1,
        "measured_gate_count": 2,
        "region_record_count": 10,
        "primary_timing_measurements": primary,
        "structural_timing_measurements": structural_timing,
        "observer_cost_measurements": observer,
        "structural_measurements": structural,
        "integrity_measurements": integrity,
        "region_measurements": regions,
        "locality_event_count": 2,
        "locality_events_sha256": _sha(event_path),
        "validation": {
            "dataset": "synthetic_scaling_family",
            "test_loader_created": False,
            "test_evaluated": False,
            "profile_completeness_validated": True,
            "measurement_lane_completeness_validated": True,
            "primary_timing_observer_mode": "no_hooks",
            "structural_counters_observer_mode": "counters_only",
            "observer_cost_reported_separately": True,
            "observer_cost_subtracted_from_primary_timing": False,
            "structural_locality_events_validated": True,
            "all_non_perturbation_gates_passed": True,
            "fresh_process_per_candidate": True,
            "block_state_reconstructed_from_shared_seeds": True,
        },
    }
    (attempt / "measurements.json").write_text(
        json.dumps(measurements), encoding="utf-8"
    )


def test_sealing_and_paired_analysis_are_fail_closed(
    tmp_path: Path,
    monkeypatch,
) -> None:
    manifest = _manifest()
    monkeypatch.setattr(
        "torch2pc_thesis.stage3b_matched_sealing.validate_matched_manifest",
        lambda _manifest: None,
    )
    runtime = tmp_path / "runtime"
    scales = {
        "stage2_baseline": 1.0,
        "isolated_layer_vjp": 0.8,
        "composite_vjp": 0.7,
    }
    for cell in manifest["cells"]:
        _write_attempt(
            runtime,
            cell,
            scale=scales[cell["candidate_id"]],
        )

    evidence = tmp_path / "evidence"
    seal = seal_matched_runtime(
        runtime,
        evidence,
        manifest,
        expected_source_commit=SOURCE,
        expected_image_digest=IMAGE,
        expected_authorization_token=TOKEN,
        sealing_source_commit="e" * 40,
        sealed_at_utc="2026-07-19T00:00:00Z",
    )

    assert seal["evidence"] is True
    assert seal["matched_cell_count"] == 3
    assert validate_sealed_matched_evidence(evidence)["status"] == "sealed"

    analysis = tmp_path / "analysis"
    summary = generate_matched_analysis(
        evidence,
        analysis,
        generated_at_utc="2026-07-19T00:01:00Z",
    )

    assert summary["matched_block_count"] == 1
    assert summary["paired_row_count"] == 2
    assert summary["ex_if0_opened"] is False
    assert summary["policy_activation_permitted"] is False
    assert (analysis / "paired_candidate_metrics.csv").is_file()
    assert (analysis / "SHA256SUMS").is_file()
