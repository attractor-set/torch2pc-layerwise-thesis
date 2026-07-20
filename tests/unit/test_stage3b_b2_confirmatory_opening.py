from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from torch2pc_thesis.stage3b_b1_equivalence import (
    atomic_write_json,
    canonical_json_digest,
    sha256_file,
)
from torch2pc_thesis.stage3b_b2_confirmatory import (
    B2_CONFIRMATORY_CAMPAIGN_ID,
    B2_CONFIRMATORY_ENGINEERING_SMOKE_COMPARISON_COUNT,
    B2_CONFIRMATORY_ENGINEERING_SMOKE_TRIPLE_COUNT,
    B2_CONFIRMATORY_EXPECTED_COMPARISON_COUNT,
    B2_CONFIRMATORY_EXPECTED_TRIPLE_COUNT,
    B2ConfirmatoryError,
    B2ConfirmatoryScientificError,
    build_triple_specs,
    plan_confirmatory_lane,
    validate_confirmatory_request,
)
from torch2pc_thesis.stage3b_b2_confirmatory_authorization import (
    B2_CONFIRMATORY_ENGINEERING_SMOKE_ACKNOWLEDGEMENT,
    B2_CONFIRMATORY_OPERATOR_ACKNOWLEDGEMENT,
    issue_b2_confirmatory_authorization,
    validate_authorization,
    validate_freeze_record,
    validate_lane_preflight,
)
from torch2pc_thesis.stage3b_b2_confirmatory_sealing import (
    B2ConfirmatorySealingError,
    seal_b2_confirmatory_campaign,
)

SHA = "a" * 64
COMMIT = "b" * 40
IMAGE = "sha256:" + "c" * 64
OUTPUT_ROOT = "/tmp/torch2pc-stage3b-b2-confirmatory-test"


def _digest_for(index: int) -> str:
    return hashlib.sha256(f"asset-{index}".encode()).hexdigest()


def request_payload() -> dict[str, Any]:
    resolved_config = {
        "architecture": "lenet_classic",
        "dataset": "FashionMNIST",
        "split": "validation",
        "training_mode": True,
        "candidate_id": "composite_vjp",
        "control_candidate_id": "isolated_layer_vjp",
        "reference_id": "stage2_baseline",
        "optimizer": {
            "name": "SGD",
            "learning_rate": 0.001,
            "momentum": 0.0,
        },
        "method_controls": {
            "FixedPred": {"eta": 0.1, "inference_steps": 10},
            "Strict": {"eta": 0.05, "inference_steps": 20},
        },
        "lane_controls": {
            "cpu_float64": {"device": "cpu", "dtype": "float64"},
            "rocm_float32": {"device": "cuda", "dtype": "float32"},
        },
        "b1_resolved_config_digest": SHA,
    }
    checkpoints = {
        str(seed): {
            "path": f"checkpoint-{seed}.pt",
            "sha256": _digest_for(seed),
        }
        for seed in (0, 1, 2)
    }
    batches = {
        str(index): {
            "batch_index": index,
            "batch_size": 256,
            "split": "validation",
            "path": f"validation-batch-{index:03d}.pt",
            "sha256": _digest_for(100 + index),
            "content_sha256": _digest_for(200 + index),
        }
        for index in range(10)
    }
    asset = lambda name, offset: {  # noqa: E731
        "path": name,
        "sha256": _digest_for(offset),
    }
    return {
        "schema_version": 1,
        "request_scope": "stage3b_b2_confirmatory_request",
        "campaign_id": B2_CONFIRMATORY_CAMPAIGN_ID,
        "request_id": "stage3b-b2-confirmatory-120-v1",
        "scope": "confirmatory",
        "dataset": "FashionMNIST",
        "split": "validation",
        "architecture": "lenet_classic",
        "lanes": ["cpu_float64", "rocm_float32"],
        "methods": ["FixedPred", "Strict"],
        "model_seeds": [0, 1, 2],
        "validation_batch_indices": list(range(10)),
        "matched_triple_count": 120,
        "pairwise_comparison_count": 240,
        "candidate_id": "composite_vjp",
        "control_candidate_id": "isolated_layer_vjp",
        "reference_id": "stage2_baseline",
        "observer_mode": "no_hooks",
        "structural_observer_mode": "counters_only",
        "test_split_access": False,
        "dangerous_miss_limit": 0,
        "training_mode": True,
        "max_attempts_per_triple": 2,
        "torch2pc_commit": COMMIT,
        "contract_path": "confirmatory-contract.json",
        "contract_digest": SHA,
        "resolved_config": resolved_config,
        "resolved_config_digest": canonical_json_digest(resolved_config),
        "run_seed_base": 732000,
        "optimizer": {
            "name": "SGD",
            "learning_rate": 0.001,
            "momentum": 0.0,
        },
        "method_controls": {
            "FixedPred": {"eta": 0.1, "inference_steps": 10},
            "Strict": {"eta": 0.05, "inference_steps": 20},
        },
        "lane_controls": {
            "cpu_float64": {"device": "cpu", "dtype": "float64"},
            "rocm_float32": {"device": "cuda", "dtype": "float32"},
        },
        "checkpoints": checkpoints,
        "validation_batches": batches,
        "b1_confirmatory_decision": asset("b1-decision.json", 300),
        "b1_admission": asset("b1-admission.json", 301),
        "b1_frozen_request": asset("b1-request.json", 302),
        "b1_batch_registry": asset("b1-batches.json", 303),
        "b2_confirmatory_contract": asset("b2-confirmatory.json", 304),
        "b2_candidate_contract": asset("b2-candidate.json", 305),
        "b2_implementation_contract": asset("b2-implementation.json", 306),
        "b2_harness_contract": asset("b2-harness.json", 307),
        "execution_boundary": {
            "request_frozen": True,
            "runtime_authorization_issued": False,
            "execution_started": False,
            "results_present": False,
            "eq_b2_confirmatory_sealed": False,
            "derived_eq_b2_admission_present": False,
            "matched_profiling_refrozen": False,
            "matched_profiling_execution_open": False,
        },
        "evidence": False,
        "results_publication_permitted": False,
    }


def _freeze_record(
    *,
    execution_mode: str,
    request_digest: str = SHA,
    output_root: str = OUTPUT_ROOT,
) -> dict[str, Any]:
    authorized_triples = (
        B2_CONFIRMATORY_EXPECTED_TRIPLE_COUNT
        if execution_mode == "confirmatory"
        else B2_CONFIRMATORY_ENGINEERING_SMOKE_TRIPLE_COUNT
    )
    authorized_comparisons = (
        B2_CONFIRMATORY_EXPECTED_COMPARISON_COUNT
        if execution_mode == "confirmatory"
        else B2_CONFIRMATORY_ENGINEERING_SMOKE_COMPARISON_COUNT
    )
    value: dict[str, Any] = {
        "schema_version": 1,
        "campaign_id": B2_CONFIRMATORY_CAMPAIGN_ID,
        "freeze_scope": "stage3b_b2_confirmatory_project_freeze",
        "project_source_commit": COMMIT,
        "request_path": "/tmp/request.json",
        "request_digest": request_digest,
        "request_file_sha256": SHA,
        "contract_digest": SHA,
        "resolved_config_digest": SHA,
        "source_image_digest": IMAGE,
        "execution_mode": execution_mode,
        "authorized_triple_count": authorized_triples,
        "authorized_comparison_count": authorized_comparisons,
        "canonical_lanes": ["cpu_float64", "rocm_float32"],
        "output_root": output_root,
        "minimum_free_bytes": 1,
        "observed_free_bytes": 2,
        "output_owner_uid": 1000,
        "output_owner_gid": 1000,
        "emergency_stop_path": output_root + "/EMERGENCY-STOP",
        "torch2pc_path": "/tmp/Torch2PC",
        "torch2pc_commit": COMMIT,
        "torch2pc_commit_verification": "git_checkout",
        "torch2pc_source_sha256": SHA,
        "evidence": False,
        "full_confirmatory_campaign_complete": False,
        "results_publication_permitted": False,
        "test_dataset_access": False,
    }
    value["freeze_digest"] = _authorization_digest(value)
    return value


def _preflight(
    freeze: dict[str, Any],
    lane: str,
) -> dict[str, Any]:
    runtime = {
        "python_version": "3.12.0",
        "pytorch_version": "2.7.0",
        "hip_version": "6.3" if lane == "rocm_float32" else None,
        "cuda_available": lane == "rocm_float32",
        "device_count": 1 if lane == "rocm_float32" else 0,
        "device_name": "AMD GPU" if lane == "rocm_float32" else "cpu",
        "platform": "Linux",
        "machine": "x86_64",
        "effective_uid": 1000,
        "effective_gid": 1000,
    }
    value: dict[str, Any] = {
        "schema_version": 1,
        "campaign_id": B2_CONFIRMATORY_CAMPAIGN_ID,
        "preflight_scope": "stage3b_b2_confirmatory_lane_preflight",
        "freeze_digest": freeze["freeze_digest"],
        "request_digest": freeze["request_digest"],
        "project_source_commit": COMMIT,
        "image_digest": IMAGE,
        "execution_mode": freeze["execution_mode"],
        "lane": lane,
        "runtime": runtime,
        "output_root": freeze["output_root"],
        "minimum_free_bytes": 1,
        "evidence": False,
        "full_confirmatory_campaign_complete": False,
        "results_publication_permitted": False,
        "test_dataset_access": False,
    }
    value["lane_preflight_digest"] = _authorization_digest(value)
    return value


def _authorization_digest(value: dict[str, Any]) -> str:
    import torch2pc_thesis.stage3b_b2_confirmatory_authorization as auth

    return auth._digest(value)


def test_request_resolves_registered_120_triples() -> None:
    payload = request_payload()
    validate_confirmatory_request(payload)
    specs = build_triple_specs(payload)

    assert len(specs) == 120
    assert len({spec.pair_id for spec in specs}) == 120
    assert specs[0].pair_id == "cpu_float64__fixedpred__seed-0__batch-0"
    assert specs[-1].pair_id == "rocm_float32__strict__seed-2__batch-9"
    assert len({spec.batch.path for spec in specs}) == 10
    assert len({spec.checkpoint.path for spec in specs}) == 3


def test_plan_reports_120_triples_and_240_comparisons(tmp_path: Path) -> None:
    plan = plan_confirmatory_lane(
        request_payload(),
        output_root=tmp_path,
        lane=None,
        engineering_smoke=False,
        resume=False,
        retry_failed=False,
    )

    assert plan.triple_count == 120
    assert plan.pairwise_comparison_count == 240
    assert len(plan.selected_triple_ids) == 120
    assert plan.summary == {"pending": 120}


def test_engineering_smoke_selects_12_triples() -> None:
    plan = plan_confirmatory_lane(
        request_payload(),
        output_root=Path("/tmp/unused-b2-confirmatory-plan"),
        lane=None,
        engineering_smoke=True,
        resume=False,
        retry_failed=False,
    )

    assert plan.triple_count == 12
    assert plan.pairwise_comparison_count == 24
    assert all(identifier.endswith("__batch-0") for identifier in plan.selected_triple_ids)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("scope", "smoke"),
        ("matched_triple_count", 12),
        ("pairwise_comparison_count", 24),
        ("candidate_id", "isolated_layer_vjp"),
        ("test_split_access", True),
        ("dangerous_miss_limit", 1),
        ("max_attempts_per_triple", 3),
    ],
)
def test_request_rejects_scope_drift(key: str, value: object) -> None:
    payload = request_payload()
    payload[key] = value

    with pytest.raises(B2ConfirmatoryError):
        validate_confirmatory_request(payload)


def test_request_rejects_duplicate_batch_paths() -> None:
    payload = request_payload()
    payload["validation_batches"]["1"]["path"] = payload["validation_batches"]["0"]["path"]

    with pytest.raises(B2ConfirmatoryError, match="distinct paths"):
        validate_confirmatory_request(payload)


def test_request_rejects_resolved_config_drift() -> None:
    payload = request_payload()
    payload["resolved_config"]["dataset"] = "MNIST"

    with pytest.raises(B2ConfirmatoryError, match="resolved_config_digest"):
        validate_confirmatory_request(payload)


def test_retryable_failure_requires_explicit_resume(tmp_path: Path) -> None:
    spec = build_triple_specs(request_payload())[0]
    attempt = tmp_path / "triples" / spec.pair_id / "attempts" / "attempt-001"
    attempt.mkdir(parents=True)
    (attempt / "started.json").write_text("{}\n", encoding="utf-8")
    (attempt / "failed.json").write_text(
        json.dumps(
            {
                "failure_class": "infrastructure",
                "retry_eligible": True,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(B2ConfirmatoryError, match="--resume --retry-failed"):
        plan_confirmatory_lane(
            request_payload(),
            output_root=tmp_path,
            lane="cpu_float64",
            engineering_smoke=False,
            resume=True,
            retry_failed=False,
        )


def test_non_retryable_failure_blocks_campaign(tmp_path: Path) -> None:
    spec = build_triple_specs(request_payload())[0]
    attempt = tmp_path / "triples" / spec.pair_id / "attempts" / "attempt-001"
    attempt.mkdir(parents=True)
    (attempt / "started.json").write_text("{}\n", encoding="utf-8")
    (attempt / "failed.json").write_text(
        json.dumps(
            {
                "failure_class": "correctness",
                "retry_eligible": False,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(B2ConfirmatoryScientificError):
        plan_confirmatory_lane(
            request_payload(),
            output_root=tmp_path,
            lane="cpu_float64",
            engineering_smoke=False,
            resume=True,
            retry_failed=True,
        )


@pytest.mark.parametrize("execution_mode", ["confirmatory", "engineering_smoke"])
def test_authorization_records_validate(execution_mode: str) -> None:
    freeze = _freeze_record(execution_mode=execution_mode)
    preflights = [
        _preflight(freeze, "cpu_float64"),
        _preflight(freeze, "rocm_float32"),
    ]
    acknowledgement = (
        B2_CONFIRMATORY_OPERATOR_ACKNOWLEDGEMENT
        if execution_mode == "confirmatory"
        else B2_CONFIRMATORY_ENGINEERING_SMOKE_ACKNOWLEDGEMENT
    )

    validate_freeze_record(freeze)
    for preflight in preflights:
        validate_lane_preflight(preflight)
    authorization = issue_b2_confirmatory_authorization(
        freeze,
        preflights,
        operator_acknowledgement=acknowledgement,
    )
    validate_authorization(authorization)

    expected_triples = 120 if execution_mode == "confirmatory" else 12
    expected_comparisons = 240 if execution_mode == "confirmatory" else 24
    assert authorization["authorized_triple_count"] == expected_triples
    assert authorization["authorized_comparison_count"] == expected_comparisons


def test_smoke_acknowledgement_cannot_authorize_confirmatory() -> None:
    freeze = _freeze_record(execution_mode="confirmatory")
    preflights = [
        _preflight(freeze, "cpu_float64"),
        _preflight(freeze, "rocm_float32"),
    ]

    with pytest.raises(B2ConfirmatoryError, match="acknowledgement"):
        issue_b2_confirmatory_authorization(
            freeze,
            preflights,
            operator_acknowledgement=(
                B2_CONFIRMATORY_ENGINEERING_SMOKE_ACKNOWLEDGEMENT
            ),
        )


def test_duplicate_lane_preflight_is_rejected() -> None:
    freeze = _freeze_record(execution_mode="confirmatory")
    cpu = _preflight(freeze, "cpu_float64")

    with pytest.raises(B2ConfirmatoryError, match="duplicate lane"):
        issue_b2_confirmatory_authorization(
            freeze,
            [cpu, cpu],
            operator_acknowledgement=B2_CONFIRMATORY_OPERATOR_ACKNOWLEDGEMENT,
        )


def _authorization_for_request(
    request: dict[str, Any],
    output_root: Path,
    *,
    execution_mode: str,
) -> dict[str, Any]:
    freeze = _freeze_record(
        execution_mode=execution_mode,
        request_digest=canonical_json_digest(request),
        output_root=str(output_root.resolve()),
    )
    preflights = [
        _preflight(freeze, "cpu_float64"),
        _preflight(freeze, "rocm_float32"),
    ]
    acknowledgement = (
        B2_CONFIRMATORY_OPERATOR_ACKNOWLEDGEMENT
        if execution_mode == "confirmatory"
        else B2_CONFIRMATORY_ENGINEERING_SMOKE_ACKNOWLEDGEMENT
    )
    return issue_b2_confirmatory_authorization(
        freeze,
        preflights,
        operator_acknowledgement=acknowledgement,
    )


def _write_synthetic_completed_triple(
    output_root: Path,
    spec: Any,
    request: dict[str, Any],
    authorization: dict[str, Any],
) -> None:
    attempt_dir = (
        output_root
        / "triples"
        / spec.pair_id
        / "attempts"
        / "attempt-001"
    )
    result_dir = attempt_dir / "result"
    result_dir.mkdir(parents=True)
    provenance = {
        "schema_version": 1,
        "campaign_id": B2_CONFIRMATORY_CAMPAIGN_ID,
        "triple_id": spec.pair_id,
        "lane": spec.lane,
        "method": spec.method,
        "model_seed": spec.model_seed,
        "validation_batch_index": spec.batch_index,
        "attempt_id": "attempt-001",
        "attempt_number": 1,
        "request_id": spec.request_id,
        "request_digest": canonical_json_digest(request),
        "project_source_commit": authorization["project_source_commit"],
        "authorization_token": authorization["authorization_token"],
        "source_image_digest": authorization["image_digest"],
        "resolved_config_digest": spec.resolved_config_digest,
        "checkpoint_sha256": spec.checkpoint.sha256,
        "batch_sha256": spec.batch.sha256,
        "b1_confirmatory_decision_sha256": (
            spec.b1_confirmatory_decision.sha256
        ),
        "b1_admission_sha256": spec.b1_admission.sha256,
        "b2_candidate_contract_sha256": (
            spec.b2_preregistration_contract.sha256
        ),
        "b2_implementation_contract_sha256": (
            spec.b2_implementation_contract.sha256
        ),
        "b2_harness_contract_sha256": spec.b2_harness_contract.sha256,
        "evidence": False,
        "test_dataset_access": False,
    }
    atomic_write_json(attempt_dir / "started.json", provenance)
    triple = {
        "pair_id": spec.pair_id,
        "triple_id": spec.pair_id,
        "pairwise_comparison_count": 2,
        "pair_spec": {
            "lane": spec.lane,
            "method": spec.method,
            "model_seed": spec.model_seed,
            "batch_index": spec.batch_index,
        },
        "comparison_plan": {
            "primary": "stage2_baseline_vs_composite_vjp",
            "required_direct_control": (
                "isolated_layer_vjp_vs_composite_vjp"
            ),
        },
        "gates": {
            gate_id: {"gate_id": gate_id, "passed": True, "reasons": []}
            for gate_id in (
                "STRUCT-B2",
                "NUM-B2",
                "TRAJ-B2",
                "OBS-B2",
                "PROV-B2",
            )
        },
        "pair_admissible": True,
        "structural_summary": {
            "sweeps_observed": 1,
            "composite_vjp_call_count": 1,
            "isolated_state_vjp_call_count": 0,
            "block_or_chunk_fallback_call_count": 0,
        },
        "provenance": {
            "request_id": spec.request_id,
            "resolved_config_digest": spec.resolved_config_digest,
            "source_image_digest": authorization["image_digest"],
            "torch2pc_commit": authorization["torch2pc_commit"],
            "checkpoint_sha256": spec.checkpoint.sha256,
            "batch_sha256": spec.batch.sha256,
            "b1_confirmatory_decision_sha256": (
                spec.b1_confirmatory_decision.sha256
            ),
            "b1_admission_sha256": spec.b1_admission.sha256,
            "b2_preregistration_contract_sha256": (
                spec.b2_preregistration_contract.sha256
            ),
            "b2_implementation_contract_sha256": (
                spec.b2_implementation_contract.sha256
            ),
            "b2_harness_contract_sha256": spec.b2_harness_contract.sha256,
        },
    }
    atomic_write_json(result_dir / "triple.json", triple)
    for filename in (
        "trajectory-metrics.csv",
        "endpoint-metrics.csv",
        "direct-b1-b2-metrics.csv",
    ):
        (result_dir / filename).write_text(
            f"triple_id,value\n{spec.pair_id},1\n",
            encoding="utf-8",
        )
    (result_dir / "structural-events.jsonl").write_text(
        json.dumps({"sweep": 0, "composite_vjp_call_count": 1}) + "\n",
        encoding="utf-8",
    )
    result_files = (
        result_dir / "triple.json",
        result_dir / "trajectory-metrics.csv",
        result_dir / "endpoint-metrics.csv",
        result_dir / "direct-b1-b2-metrics.csv",
        result_dir / "structural-events.jsonl",
    )
    (result_dir / "SHA256SUMS").write_text(
        "".join(
            f"{sha256_file(path)}  {path.name}\n" for path in result_files
        ),
        encoding="utf-8",
    )
    atomic_write_json(
        attempt_dir / "completed.json",
        {
            **provenance,
            "status": "completed",
            "triple_admissible": True,
            "pairwise_comparison_count": 2,
            "result_sha256": sha256_file(result_dir / "triple.json"),
        },
    )


def test_engineering_smoke_cannot_be_sealed_as_confirmatory(
    tmp_path: Path,
) -> None:
    request = request_payload()
    authorization = _authorization_for_request(
        request,
        tmp_path,
        execution_mode="engineering_smoke",
    )

    with pytest.raises(B2ConfirmatorySealingError, match="engineering-smoke"):
        seal_b2_confirmatory_campaign(
            request,
            authorization,
            output_root=tmp_path,
        )


def test_complete_synthetic_campaign_seals_120_triples_and_240_comparisons(
    tmp_path: Path,
) -> None:
    request = request_payload()
    authorization = _authorization_for_request(
        request,
        tmp_path,
        execution_mode="confirmatory",
    )
    for spec in build_triple_specs(request):
        _write_synthetic_completed_triple(
            tmp_path,
            spec,
            request,
            authorization,
        )

    decision = seal_b2_confirmatory_campaign(
        request,
        authorization,
        output_root=tmp_path,
    )

    assert decision["decision_id"] == "EQ-B2-CONFIRMATORY"
    assert decision["scope"] == "confirmatory"
    assert decision["matched_triples_observed"] == 120
    assert decision["pairwise_comparisons_observed"] == 240
    assert decision["failed_pair_count"] == 0
    assert decision["sealed"] is True
    admission = json.loads(
        (tmp_path / "sealed/matched-profiling-admission.json").read_text(
            encoding="utf-8"
        )
    )
    assert admission["decision_id"] == "EQ-B2"
    assert admission["source_decision_id"] == "EQ-B2-CONFIRMATORY"
    assert admission["matched_triples_observed"] == 120
    assert admission["pairwise_comparisons_observed"] == 240
    assert admission["production_admission_effect"].endswith(
        "does not authorize 288-cell execution"
    )
