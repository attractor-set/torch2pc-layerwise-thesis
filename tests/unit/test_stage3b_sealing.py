from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

import torch2pc_thesis.stage3b_sealing as sealing
from torch2pc_thesis.stage3b_sealing import (
    B0SealingContract,
    Stage3BSealingError,
    seal_b0_archive,
    validate_b0_archive,
    verify_archive_inventory,
)

SOURCE_COMMIT = "9" * 40
SEALING_COMMIT = "a" * 40
IMAGE_DIGEST = "sha256:" + "7" * 64
MANIFEST_DIGEST = "6" * 64
AUTHORIZATION_TOKEN = "5" * 64
TORCH2PC_DIGEST = "4" * 64
SOURCE_OUTPUT_ROOT = Path("/tmp/stage3b-b0-source")
REQUIRED_REGIONS = tuple(sorted(sealing.STAGE3_PROFILE_REGIONS))
CONTRACT = B0SealingContract(
    expected_cell_count=2,
    methods=("fixedpred", "strict"),
    depths=(4,),
    widths=(64,),
    batch_sizes=(64,),
    model_seeds=(70,),
    warmup_steps=1,
    measured_steps=2,
    repetitions=1,
    required_regions=REQUIRED_REGIONS,
)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_inventory(root: Path) -> str:
    entries = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS":
            entries.append(f"{_sha256(path)}  ./{path.relative_to(root)}")
    inventory = root / "SHA256SUMS"
    inventory.write_text("\n".join(entries) + "\n", encoding="utf-8")
    return _sha256(inventory)


def _request(*, cell: dict[str, object], attempt_id: str) -> dict[str, object]:
    return {
        "schema_version": 1,
        "campaign_id": sealing.STAGE3B_CAMPAIGN_ID,
        "authorization_scope": sealing.B0_AUTHORIZATION_SCOPE,
        "execution_scope": sealing.B0_CANONICAL_CELL_SCOPE,
        "attempt_id": attempt_id,
        "cell_id": cell["cell_id"],
        "block_id": cell["block_id"],
        "candidate_id": sealing.B0_CANDIDATE_ID,
        "method": cell["method"],
        "authorization_token": AUTHORIZATION_TOKEN,
        "manifest_digest": MANIFEST_DIGEST,
        "source_commit": SOURCE_COMMIT,
        "device": "rocm",
        "dtype": "float32",
        "image_digest": IMAGE_DIGEST,
        "canonical_protocol": CONTRACT.protocol_record,
        "evidence": False,
        "full_cell_complete": False,
        "full_lane_complete": False,
        "full_campaign_complete": False,
        "results_publication_permitted": False,
        "test_dataset_access": False,
    }


def _measurements(method: str) -> dict[str, object]:
    inference_steps = sealing.B0_CANONICAL_INFERENCE_STEPS[method]
    composite = []
    integrity = []
    regions = []
    for step in range(CONTRACT.measured_steps):
        composite.append(
            {
                "repetition": 0,
                "step": step,
                "host_time_us": 100.0 + step + (50.0 if method == "strict" else 0.0),
                "device_time_us": 90.0 + step + (45.0 if method == "strict" else 0.0),
                "peak_allocated_bytes": 1000 + step + (500 if method == "strict" else 0),
                "peak_reserved_bytes": 2000 + step + (500 if method == "strict" else 0),
                "synchronization_points": 2,
            }
        )
        integrity.append(
            {
                "repetition": 0,
                "step": step,
                "all_finite": True,
                "comparison_count": 3,
                "configured_inference_steps": inference_steps,
                "internal_region_attribution_ready": True,
                "maximum_relative_l2": 0.0,
                "minimum_cosine": 1.0,
                "observed_inference_steps": inference_steps,
                "passed": True,
            }
        )
        for region in REQUIRED_REGIONS:
            regions.append(
                {
                    "schema_version": 1,
                    "candidate_id": sealing.B0_CANDIDATE_ID,
                    "method": method,
                    "repetition": 0,
                    "step": step,
                    "region": region,
                    "host_time_us": 10.0 + step,
                    "device_time_us": 9.0 + step,
                    "peak_allocated_bytes": 100,
                    "peak_reserved_bytes": 200,
                    "vjp_calls": 1,
                    "synchronization_points": 2,
                    "saved_tensor_bytes": 300,
                    "actual_inference_steps": (
                        inference_steps if region == "state_inference" else 0
                    ),
                    "non_finite_events": 0,
                }
            )
    return {
        "status": "canonical_cell_complete",
        "execution_scope": sealing.B0_CANONICAL_CELL_SCOPE,
        "evidence": False,
        "full_cell_complete": True,
        "full_lane_complete": False,
        "full_campaign_complete": False,
        "results_publication_permitted": False,
        "test_dataset_access": False,
        "warmup_gate_count": CONTRACT.warmup_steps * CONTRACT.repetitions,
        "measured_gate_count": CONTRACT.measured_steps * CONTRACT.repetitions,
        "expected_region_record_count": len(regions),
        "region_record_count": len(regions),
        "composite_measurements": composite,
        "integrity_measurements": integrity,
        "region_measurements": regions,
        "validation": {
            "all_non_perturbation_gates_passed": True,
            "dataset": "synthetic_scaling_family",
            "profile_completeness_validated": True,
            "test_evaluated": False,
            "test_loader_created": False,
        },
    }


def _build_archive(
    tmp_path: Path,
    *,
    systemic_failure: bool = False,
) -> tuple[Path, str]:
    root = tmp_path / "archive"
    auth_root = root / "authorization"
    lane_root = root / "canonical" / "lanes" / "rocm-float32"
    run_id = "run-1"
    run_root = lane_root / "runs" / run_id

    cells = [
        {
            "cell_id": "cell-fixedpred",
            "block_id": "block-fixedpred",
            "candidate_id": sealing.B0_CANDIDATE_ID,
            "method": "fixedpred",
            "depth": 4,
            "width": 64,
            "batch_size": 64,
            "model_seed": 70,
        },
        {
            "cell_id": "cell-strict",
            "block_id": "block-strict",
            "candidate_id": sealing.B0_CANDIDATE_ID,
            "method": "strict",
            "depth": 4,
            "width": 64,
            "batch_size": 64,
            "model_seed": 70,
        },
    ]
    manifest = {
        "schema_version": 1,
        "campaign_id": sealing.STAGE3B_CAMPAIGN_ID,
        "manifest_digest": MANIFEST_DIGEST,
        "cells": cells,
    }
    freeze = {
        "campaign_id": sealing.STAGE3B_CAMPAIGN_ID,
        "manifest_digest": MANIFEST_DIGEST,
        "project_source_commit": SOURCE_COMMIT,
        "output_root": str(SOURCE_OUTPUT_ROOT),
        "torch2pc_source_sha256": TORCH2PC_DIGEST,
        "canonical_protocol": CONTRACT.protocol_record,
        "evidence": False,
        "full_campaign_complete": False,
        "test_dataset_access": False,
    }
    preflight = {
        "campaign_id": sealing.STAGE3B_CAMPAIGN_ID,
        "image_digest": IMAGE_DIGEST,
        "runtime": {
            "device_name": "AMD Radeon RX 7700 XT",
            "hip_version": "7.2",
            "pytorch_version": "2.9.1+rocm7.2",
        },
        "evidence": False,
        "full_campaign_complete": False,
    }
    authorization = {
        "campaign_id": sealing.STAGE3B_CAMPAIGN_ID,
        "manifest_digest": MANIFEST_DIGEST,
        "project_source_commit": SOURCE_COMMIT,
        "authorization_token": AUTHORIZATION_TOKEN,
        "authorized_cell_count": 2,
        "canonical_execution_count": 2,
        "canonical_protocol": CONTRACT.protocol_record,
        "evidence": False,
        "full_campaign_complete": False,
        "results_publication_permitted": False,
        "test_dataset_access": False,
    }
    _write_json(auth_root / "project-freeze.json", freeze)
    _write_json(auth_root / "rocm-float32-preflight.json", preflight)
    _write_json(auth_root / "campaign-authorization.json", authorization)
    _write_json(run_root / "child-inputs" / "manifest.json", manifest)
    _write_json(run_root / "child-inputs" / "authorization.json", authorization)

    results = []
    for index, cell in enumerate(cells, start=1):
        cell_id = str(cell["cell_id"])
        attempt_id = f"attempt-{index}"
        relative_attempt = Path(
            "canonical/lanes/rocm-float32/cells"
        ) / cell_id / "attempts" / attempt_id
        attempt_root = root / relative_attempt
        source_attempt = SOURCE_OUTPUT_ROOT / relative_attempt
        request = _request(cell=cell, attempt_id=attempt_id)
        started = {**request, "status": "canonical_cell_running", "started_at": "2026-01-01T00:00:00Z"}
        terminal = {
            **request,
            "status": "canonical_cell_complete",
            "full_cell_complete": True,
            "completed_at": "2026-01-01T00:01:00Z",
            "attempt_directory": str(source_attempt),
        }
        resolved = {
            "method": cell["method"],
            "depth": 4,
            "width": 64,
            "batch_size": 64,
            "model_seed": 70,
            "canonical_protocol": CONTRACT.protocol_record,
            "required_regions": list(REQUIRED_REGIONS),
            "inference_steps": sealing.B0_CANONICAL_INFERENCE_STEPS[str(cell["method"])],
        }
        environment = {
            "project_source_commit": SOURCE_COMMIT,
            "container_image_digest": IMAGE_DIGEST,
            "manifest_digest": MANIFEST_DIGEST,
            "authorization_token": AUTHORIZATION_TOKEN,
            "torch2pc_source_sha256": TORCH2PC_DIGEST,
            "requested_device": "rocm",
            "resolved_device_type": "cuda",
            "dtype": "float32",
            "hip_version": "7.2",
            "device_name": "AMD Radeon RX 7700 XT",
            "pytorch_version": "2.9.1+rocm7.2",
            "model_state_sha256": "1" * 64,
            "synthetic_inputs_sha256": "2" * 64,
            "synthetic_targets_sha256": "3" * 64,
        }
        _write_json(attempt_root / "request.json", request)
        _write_json(attempt_root / "started.json", started)
        _write_json(attempt_root / "resolved-config.json", resolved)
        _write_json(attempt_root / "environment.json", environment)
        _write_json(attempt_root / "measurements.json", _measurements(str(cell["method"])))
        _write_json(attempt_root / "completed.json", terminal)

        process_relative = Path("canonical/lanes/rocm-float32/runs") / run_id / "processes" / f"{cell_id}.json"
        process_path = root / process_relative
        process_source = SOURCE_OUTPUT_ROOT / process_relative
        process = {
            "schema_version": 1,
            "campaign_id": sealing.STAGE3B_CAMPAIGN_ID,
            "authorization_scope": sealing.B0_AUTHORIZATION_SCOPE,
            "execution_scope": sealing.B0_CANONICAL_PROCESS_SCOPE,
            "process_isolation_mode": sealing.B0_CANONICAL_PROCESS_MODE,
            "cell_id": cell_id,
            "authorization_token": AUTHORIZATION_TOKEN,
            "manifest_digest": MANIFEST_DIGEST,
            "source_commit": SOURCE_COMMIT,
            "device": "rocm",
            "dtype": "float32",
            "image_digest": IMAGE_DIGEST,
            "parent_pid": 10,
            "child_pid": 10 + index,
            "child_exit_code": 0,
            "attempt_directory": str(source_attempt),
            "request_record": str(source_attempt / "request.json"),
            "request_record_sha256": _sha256(attempt_root / "request.json"),
            "terminal_record": str(source_attempt / "completed.json"),
            "terminal_record_sha256": _sha256(attempt_root / "completed.json"),
            "terminal_status": "canonical_cell_complete",
            "terminal_validation_error": None,
            "systemic_resource_failure": systemic_failure and index == 1,
            "child_stdout_sha256": "8" * 64,
            "child_stderr_sha256": hashlib.sha256(b"").hexdigest(),
            "child_stdout_tail": "complete\n",
            "child_stderr_tail": "",
            "evidence": False,
            "full_lane_complete": False,
            "full_campaign_complete": False,
            "results_publication_permitted": False,
            "test_dataset_access": False,
        }
        _write_json(process_path, process)
        results.append(
            {
                **terminal,
                "process_isolation": {
                    "mode": sealing.B0_CANONICAL_PROCESS_MODE,
                    "parent_pid": 10,
                    "child_pid": 10 + index,
                    "child_exit_code": 0,
                    "record_path": str(process_source),
                    "terminal_record_sha256": _sha256(attempt_root / "completed.json"),
                },
                "systemic_resource_failure": systemic_failure and index == 1,
            }
        )

    run = {
        "schema_version": 1,
        "campaign_id": sealing.STAGE3B_CAMPAIGN_ID,
        "authorization_scope": sealing.B0_AUTHORIZATION_SCOPE,
        "execution_scope": sealing.B0_CANONICAL_SCOPE,
        "authorization_token": AUTHORIZATION_TOKEN,
        "manifest_digest": MANIFEST_DIGEST,
        "source_commit": SOURCE_COMMIT,
        "device": "rocm",
        "dtype": "float32",
        "image_digest": IMAGE_DIGEST,
        "canonical_protocol": CONTRACT.protocol_record,
        "run_id": run_id,
        "completed_at": "2026-01-01T00:02:00Z",
        "status": "lane_complete",
        "execution_performed": True,
        "executed_cell_count": 2,
        "completed_this_run_count": 2,
        "failed_this_run_count": 0,
        "completed_cell_count": 2,
        "remaining_cell_count": 0,
        "failures": [],
        "stopped_early": False,
        "systemic_stop": None,
        "full_lane_complete": True,
        "full_campaign_complete": False,
        "evidence": False,
        "results_publication_permitted": False,
        "test_dataset_access": False,
        "process_isolation_mode": sealing.B0_CANONICAL_PROCESS_MODE,
        "selected_cell_ids": [cell["cell_id"] for cell in cells],
        "results": results,
    }
    _write_json(run_root / "completed.json", run)
    _write_json(run_root / "results.json", run)
    _write_json(run_root / "request.json", {"run_id": run_id})
    _write_json(run_root / "plan.json", {"run_id": run_id})
    _write_json(run_root / "started.json", {"run_id": run_id})
    lane_state = {
        "campaign_id": sealing.STAGE3B_CAMPAIGN_ID,
        "manifest_digest": MANIFEST_DIGEST,
        "authorization_token": AUTHORIZATION_TOKEN,
        "source_commit": SOURCE_COMMIT,
        "image_digest": IMAGE_DIGEST,
        "device": "rocm",
        "dtype": "float32",
        "status": "lane_complete",
        "completed_cell_count": 2,
        "failed_cell_count": 0,
        "full_lane_complete": True,
        "full_campaign_complete": False,
        "evidence": False,
        "results_publication_permitted": False,
        "test_dataset_access": False,
    }
    _write_json(lane_root / "lane-state.json", lane_state)
    return root, _write_inventory(root)


def _disable_upstream_schema_validators(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sealing, "validate_project_freeze", lambda _record: None)
    monkeypatch.setattr(sealing, "validate_lane_preflight", lambda _record: None)
    monkeypatch.setattr(sealing, "validate_campaign_authorization", lambda _record: None)
    monkeypatch.setattr(sealing, "validate_manifest", lambda _record: None)


def test_seal_archive_creates_compact_evidence_and_preserves_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _disable_upstream_schema_validators(monkeypatch)
    archive, inventory_digest = _build_archive(tmp_path)
    original_inventory = (archive / "SHA256SUMS").read_bytes()
    output = tmp_path / "sealed"

    bundle = seal_b0_archive(
        archive,
        output,
        expected_source_commit=SOURCE_COMMIT,
        expected_image_digest=IMAGE_DIGEST,
        expected_archive_inventory_sha256=inventory_digest,
        sealing_source_commit=SEALING_COMMIT,
        contract=CONTRACT,
    )

    assert bundle.output_root == output.resolve()
    assert len(bundle.seal_digest) == 64
    assert (archive / "SHA256SUMS").read_bytes() == original_inventory
    verify_archive_inventory(
        archive,
        expected_inventory_sha256=inventory_digest,
    )
    seal = json.loads((output / "seal.json").read_text(encoding="utf-8"))
    validation = json.loads((output / "validation.json").read_text(encoding="utf-8"))
    assert seal["status"] == "sealed"
    assert seal["evidence"] is True
    assert seal["full_b0_campaign_complete"] is True
    assert seal["full_stage3b_campaign_complete"] is False
    assert seal["results_publication_permitted"] is True
    assert seal["sealing_source_commit"] == SEALING_COMMIT
    assert validation["counts"]["cells"] == 2
    assert validation["counts"]["process_records"] == 2
    assert sum(1 for _ in (output / "cell_metrics.csv").read_text().splitlines()) == 3
    assert sum(1 for _ in (output / "region_metrics.csv").read_text().splitlines()) == 11
    assert sum(1 for _ in (output / "paired_method_metrics.csv").read_text().splitlines()) == 2
    assert sum(1 for _ in (output / "configuration_metrics.csv").read_text().splitlines()) == 3


def test_validate_archive_rejects_systemic_resource_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _disable_upstream_schema_validators(monkeypatch)
    archive, inventory_digest = _build_archive(tmp_path, systemic_failure=True)

    with pytest.raises(Stage3BSealingError, match="systemic_resource_failure"):
        validate_b0_archive(
            archive,
            expected_source_commit=SOURCE_COMMIT,
            expected_image_digest=IMAGE_DIGEST,
            expected_archive_inventory_sha256=inventory_digest,
            contract=CONTRACT,
        )


def test_archive_inventory_detects_tampering(tmp_path: Path) -> None:
    root = tmp_path / "archive"
    root.mkdir()
    (root / "record.json").write_text("{}\n", encoding="utf-8")
    digest = _write_inventory(root)
    (root / "record.json").write_text('{"tampered": true}\n', encoding="utf-8")

    with pytest.raises(Stage3BSealingError, match="checksum differs"):
        verify_archive_inventory(root, expected_inventory_sha256=digest)


def test_sealing_rejects_output_inside_immutable_archive(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _disable_upstream_schema_validators(monkeypatch)
    archive, inventory_digest = _build_archive(tmp_path)

    with pytest.raises(Stage3BSealingError, match="separate trees"):
        seal_b0_archive(
            archive,
            archive / "derived",
            expected_source_commit=SOURCE_COMMIT,
            expected_image_digest=IMAGE_DIGEST,
            expected_archive_inventory_sha256=inventory_digest,
            sealing_source_commit=SEALING_COMMIT,
            contract=CONTRACT,
        )


def test_resealing_same_archive_produces_same_content_addressed_seal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _disable_upstream_schema_validators(monkeypatch)
    archive, inventory_digest = _build_archive(tmp_path)

    first = seal_b0_archive(
        archive,
        tmp_path / "sealed-a",
        expected_source_commit=SOURCE_COMMIT,
        expected_image_digest=IMAGE_DIGEST,
        expected_archive_inventory_sha256=inventory_digest,
        sealing_source_commit=SEALING_COMMIT,
        contract=CONTRACT,
    )
    second = seal_b0_archive(
        archive,
        tmp_path / "sealed-b",
        expected_source_commit=SOURCE_COMMIT,
        expected_image_digest=IMAGE_DIGEST,
        expected_archive_inventory_sha256=inventory_digest,
        sealing_source_commit=SEALING_COMMIT,
        contract=CONTRACT,
    )

    assert first.seal_digest == second.seal_digest
    for filename in (
        "validation.json",
        "metric-definitions.json",
        "cell_metrics.csv",
        "region_metrics.csv",
        "paired_method_metrics.csv",
        "configuration_metrics.csv",
        "seal.json",
        "SHA256SUMS",
    ):
        assert (first.output_root / filename).read_bytes() == (
            second.output_root / filename
        ).read_bytes()
