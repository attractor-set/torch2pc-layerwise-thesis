from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from torch2pc_thesis.stage3b_matched_analysis import generate_matched_analysis
from torch2pc_thesis.stage3b_matched_sealing import (
    Stage3BMatchedSealingError,
    seal_matched_runtime,
    validate_sealed_matched_evidence,
)

SOURCE = "a" * 40
IMAGE = "sha256:" + "b" * 64
TOKEN = "c" * 64
MANIFEST_DIGEST = "d" * 64
SOURCE_MANIFEST_DIGEST = "e" * 64
OPENING_REQUEST_DIGEST = "f" * 64
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
        "manifest_digest": MANIFEST_DIGEST,
        "source_manifest_digest": SOURCE_MANIFEST_DIGEST,
        "protocol": {
            "warmup_steps": 1,
            "measured_steps": 2,
            "repetitions": 1,
            "independent_unit": "model_seed",
            "candidate_order": "test",
        },
        "cells": cells,
    }


def _write_attempt(
    root: Path,
    cell: dict[str, object],
    *,
    scale: float,
    attempt_name: str = "attempt-0",
) -> None:
    correctness_path = (
        root
        / "matched/lanes/rocm-float32/blocks"
        / str(cell["block_id"])
        / "cross-candidate-correctness.json"
    )
    correctness = {
        "schema_version": 1,
        "scope": "stage3b_matched_cross_candidate_correctness_v1",
        "status": "cross_candidate_correctness_passed",
        "block_id": cell["block_id"],
        "method": cell["method"],
        "depth": cell["depth"],
        "width": cell["width"],
        "batch_size": cell["batch_size"],
        "model_seed": cell["model_seed"],
        "authorization_token": TOKEN,
        "matched_manifest_digest": MANIFEST_DIGEST,
        "source_commit": SOURCE,
        "image_digest": IMAGE,
        "candidate_ids": list(CANDIDATES),
        "initial_state": {
            "model_state_sha256": "1" * 64,
            "synthetic_inputs_sha256": "2" * 64,
            "synthetic_targets_sha256": "3" * 64,
        },
        "pair_comparisons": [
            {
                "reference_id": "stage2_baseline",
                "candidate_id": candidate,
                "comparison_count": 1,
                "minimum_cosine": 1.0,
                "maximum_relative_l2": 0.0,
                "all_finite": True,
                "passed": True,
                "comparisons": [],
            }
            for candidate in ("isolated_layer_vjp", "composite_vjp")
        ],
        "passed": True,
        "untimed": True,
        "test_dataset_access": False,
        "evidence": False,
    }
    if not correctness_path.exists():
        correctness_path.parent.mkdir(parents=True)
        correctness_path.write_text(json.dumps(correctness), encoding="utf-8")
    attempt = (
        root
        / "matched/lanes/rocm-float32/cells"
        / str(cell["cell_id"])
        / "attempts"
        / attempt_name
    )
    attempt.mkdir(parents=True)
    shared = {
        "cell_id": cell["cell_id"],
        "block_id": cell["block_id"],
        "candidate_id": cell["candidate_id"],
        "method": cell["method"],
        "authorization_token": TOKEN,
        "matched_manifest_digest": MANIFEST_DIGEST,
        "opening_request_digest": OPENING_REQUEST_DIGEST,
        "source_manifest_digest": SOURCE_MANIFEST_DIGEST,
        "source_commit": SOURCE,
        "device": "rocm",
        "dtype": "float32",
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
        "block_correctness_path": str(correctness_path),
        "block_correctness_sha256": _sha(correctness_path),
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
        "block_correctness": correctness,
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
            "cross_candidate_correctness_gate_passed": True,
        },
    }
    (attempt / "measurements.json").write_text(
        json.dumps(measurements), encoding="utf-8"
    )


def _write_failed_attempt(
    root: Path,
    cell: dict[str, object],
    *,
    attempt_name: str,
    failure_class: str,
    retry_eligible: bool,
) -> None:
    attempt = (
        root
        / "matched/lanes/rocm-float32/cells"
        / str(cell["cell_id"])
        / "attempts"
        / attempt_name
    )
    attempt.mkdir(parents=True)
    shared = {
        "cell_id": cell["cell_id"],
        "block_id": cell["block_id"],
        "candidate_id": cell["candidate_id"],
        "method": cell["method"],
        "authorization_token": TOKEN,
        "matched_manifest_digest": MANIFEST_DIGEST,
        "opening_request_digest": OPENING_REQUEST_DIGEST,
        "source_manifest_digest": SOURCE_MANIFEST_DIGEST,
        "source_commit": SOURCE,
        "device": "rocm",
        "dtype": "float32",
        "image_digest": IMAGE,
    }
    (attempt / "request.json").write_text(json.dumps(shared), encoding="utf-8")
    (attempt / "started.json").write_text(
        json.dumps(shared | {"status": "matched_cell_running"}),
        encoding="utf-8",
    )
    (attempt / "failed.json").write_text(
        json.dumps(
            shared
            | {
                "status": "matched_cell_failed",
                "full_cell_complete": False,
                "failure_class": failure_class,
                "retry_eligible": retry_eligible,
            }
        ),
        encoding="utf-8",
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


def test_sealing_accepts_retryable_failure_followed_by_success(
    tmp_path: Path,
    monkeypatch,
) -> None:
    manifest = _manifest()
    monkeypatch.setattr(
        "torch2pc_thesis.stage3b_matched_sealing.validate_matched_manifest",
        lambda _manifest: None,
    )
    runtime = tmp_path / "runtime"
    for cell in manifest["cells"]:
        if cell["candidate_id"] == "stage2_baseline":
            _write_failed_attempt(
                runtime,
                cell,
                attempt_name="attempt-0",
                failure_class="infrastructure",
                retry_eligible=True,
            )
            _write_attempt(runtime, cell, scale=1.0, attempt_name="attempt-1")
        else:
            _write_attempt(runtime, cell, scale=1.0)

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

    assert seal["retried_cell_count"] == 1
    assert seal["attempt_history_count"] == 4
    history = [
        json.loads(line)
        for line in (evidence / "attempt-history.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert any(record["failure_class"] == "infrastructure" for record in history)


def test_sealing_rejects_non_retryable_failure_before_success(
    tmp_path: Path,
    monkeypatch,
) -> None:
    manifest = _manifest()
    monkeypatch.setattr(
        "torch2pc_thesis.stage3b_matched_sealing.validate_matched_manifest",
        lambda _manifest: None,
    )
    runtime = tmp_path / "runtime"
    for cell in manifest["cells"]:
        if cell["candidate_id"] == "stage2_baseline":
            _write_failed_attempt(
                runtime,
                cell,
                attempt_name="attempt-0",
                failure_class="correctness",
                retry_eligible=False,
            )
            _write_attempt(runtime, cell, scale=1.0, attempt_name="attempt-1")
        else:
            _write_attempt(runtime, cell, scale=1.0)

    with pytest.raises(Stage3BMatchedSealingError, match="non-retryable"):
        seal_matched_runtime(
            runtime,
            tmp_path / "evidence",
            manifest,
            expected_source_commit=SOURCE,
            expected_image_digest=IMAGE,
            expected_authorization_token=TOKEN,
            sealing_source_commit="e" * 40,
            sealed_at_utc="2026-07-19T00:00:00Z",
        )


def test_sealing_rejects_retry_history_with_mismatched_provenance(
    tmp_path: Path,
    monkeypatch,
) -> None:
    manifest = _manifest()
    monkeypatch.setattr(
        "torch2pc_thesis.stage3b_matched_sealing.validate_matched_manifest",
        lambda _manifest: None,
    )
    runtime = tmp_path / "runtime"
    for cell in manifest["cells"]:
        if cell["candidate_id"] == "stage2_baseline":
            _write_failed_attempt(
                runtime,
                cell,
                attempt_name="attempt-0",
                failure_class="infrastructure",
                retry_eligible=True,
            )
            bad_request = (
                runtime
                / "matched/lanes/rocm-float32/cells"
                / str(cell["cell_id"])
                / "attempts/attempt-0/request.json"
            )
            record = json.loads(bad_request.read_text(encoding="utf-8"))
            record["authorization_token"] = "0" * 64
            bad_request.write_text(json.dumps(record), encoding="utf-8")
            _write_attempt(runtime, cell, scale=1.0, attempt_name="attempt-1")
        else:
            _write_attempt(runtime, cell, scale=1.0)

    with pytest.raises(
        Stage3BMatchedSealingError,
        match="request.authorization_token",
    ):
        seal_matched_runtime(
            runtime,
            tmp_path / "evidence",
            manifest,
            expected_source_commit=SOURCE,
            expected_image_digest=IMAGE,
            expected_authorization_token=TOKEN,
            sealing_source_commit="e" * 40,
            sealed_at_utc="2026-07-19T00:00:00Z",
        )
