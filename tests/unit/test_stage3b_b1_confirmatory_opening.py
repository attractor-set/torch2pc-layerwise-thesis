from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
import torch

from scripts.export_stage3b_b1_shared_validation_batch import ExportError
from torch2pc_thesis.stage3b_b1_confirmatory import (
    B1_CONFIRMATORY_EXPECTED_PAIR_COUNT,
    B1_CONFIRMATORY_RECONCILE_ACKNOWLEDGEMENT,
    B1ConfirmatoryError,
    build_pair_specs,
    plan_confirmatory_lane,
    reconcile_orphaned_running_attempts,
    select_specs,
    validate_confirmatory_request,
)
from torch2pc_thesis.stage3b_b1_confirmatory_authorization import (
    B1_CONFIRMATORY_ENGINEERING_SMOKE_ACKNOWLEDGEMENT,
    B1_CONFIRMATORY_FREEZE_SCOPE,
    B1_CONFIRMATORY_OPERATOR_ACKNOWLEDGEMENT,
    B1_CONFIRMATORY_PREFLIGHT_SCOPE,
    issue_b1_confirmatory_authorization,
    validate_authorization,
    validate_lane_preflight,
)
from torch2pc_thesis.stage3b_b1_confirmatory_sealing import (
    B1ConfirmatorySealingError,
    seal_b1_confirmatory_campaign,
)
from torch2pc_thesis.stage3b_b1_equivalence import (
    atomic_write_json,
    canonical_json_digest,
    sha256_file,
)


def _request() -> dict[str, object]:
    resolved_config = {
        "data": {"dataset": "FashionMNIST"},
        "training": {"batch_size": 256},
    }
    request: dict[str, object] = {
        "schema_version": 1,
        "request_scope": "stage3b_b1_confirmatory_request",
        "campaign_id": "stage3b-b1-confirmatory-equivalence-v1",
        "request_id": "stage3b-b1-confirmatory-test-001",
        "scope": "confirmatory",
        "dataset": "FashionMNIST",
        "split": "validation",
        "architecture": "lenet_classic",
        "lanes": ["cpu_float64", "rocm_float32"],
        "methods": ["FixedPred", "Strict"],
        "model_seeds": [0, 1, 2],
        "validation_batch_indices": list(range(10)),
        "matched_pair_count": 120,
        "observer_mode": "no_hooks",
        "structural_observer_mode": "counters_only",
        "test_split_access": False,
        "training_mode": True,
        "max_attempts_per_pair": 2,
        "torch2pc_commit": "3" * 40,
        "contract_digest": "4" * 64,
        "resolved_config": resolved_config,
        "resolved_config_digest": canonical_json_digest(resolved_config),
        "run_seed_base": 731000,
        "optimizer": {"name": "SGD", "learning_rate": 0.001, "momentum": 0.0},
        "method_controls": {
            "FixedPred": {"eta": 0.1, "inference_steps": 10},
            "Strict": {"eta": 0.05, "inference_steps": 20},
        },
        "lane_controls": {
            "cpu_float64": {"device": "cpu", "dtype": "float64"},
            "rocm_float32": {"device": "cuda", "dtype": "float32"},
        },
        "checkpoints": {
            str(seed): {
                "path": f"results/checkpoint-seed-{seed}.pt",
                "sha256": str(seed + 5) * 64,
            }
            for seed in range(3)
        },
        "validation_batches": {
            str(index): {
                "path": f"experiments/frozen/batch-{index:03d}.pt",
                "sha256": f"{index:064x}",
                "content_sha256": f"{index + 100:064x}",
                "batch_index": index,
                "split": "validation",
                "batch_size": 256,
            }
            for index in range(10)
        },
        "evidence": False,
        "results_publication_permitted": False,
    }
    return request


def _freeze(
    request: dict[str, object],
    output_root: Path,
    *,
    execution_mode: str = "confirmatory",
) -> dict[str, object]:
    value: dict[str, object] = {
        "schema_version": 1,
        "campaign_id": "stage3b-b1-confirmatory-equivalence-v1",
        "freeze_scope": B1_CONFIRMATORY_FREEZE_SCOPE,
        "request_path": str((output_root / "request.json").resolve()),
        "request_digest": canonical_json_digest(request),
        "request_file_sha256": "5" * 64,
        "contract_digest": request["contract_digest"],
        "resolved_config_digest": request["resolved_config_digest"],
        "project_source_commit": "1" * 40,
        "torch2pc_commit": request["torch2pc_commit"],
        "torch2pc_path": str((output_root / "Torch2PC").resolve()),
        "torch2pc_commit_verification": "git_checkout",
        "torch2pc_source_sha256": "6" * 64,
        "source_image_digest": "sha256:" + "2" * 64,
        "execution_mode": execution_mode,
        "authorized_pair_count": 120 if execution_mode == "confirmatory" else 12,
        "canonical_lanes": ["cpu_float64", "rocm_float32"],
        "output_root": str(output_root.resolve()),
        "emergency_stop_path": str(output_root.resolve() / "EMERGENCY-STOP"),
        "minimum_free_bytes": 1,
        "observed_free_bytes": 2,
        "output_owner_uid": 1000,
        "output_owner_gid": 1000,
        "evidence": False,
        "full_confirmatory_campaign_complete": False,
        "results_publication_permitted": False,
        "test_dataset_access": False,
    }
    value["freeze_digest"] = _digest(value)
    return value


def _preflight(
    freeze: dict[str, object], lane: str, *, image: str | None = None
) -> dict[str, object]:
    value: dict[str, object] = {
        "schema_version": 1,
        "campaign_id": "stage3b-b1-confirmatory-equivalence-v1",
        "preflight_scope": B1_CONFIRMATORY_PREFLIGHT_SCOPE,
        "freeze_digest": freeze["freeze_digest"],
        "request_digest": freeze["request_digest"],
        "project_source_commit": freeze["project_source_commit"],
        "lane": lane,
        "image_digest": image or freeze["source_image_digest"],
        "execution_mode": freeze["execution_mode"],
        "runtime": {
            "python_version": "3.12.0",
            "pytorch_version": "2.9.0",
            "hip_version": "6.3" if lane == "rocm_float32" else None,
            "cuda_available": lane == "rocm_float32",
            "device_count": 1 if lane == "rocm_float32" else 0,
            "device_name": "AMD GPU" if lane == "rocm_float32" else "cpu",
            "platform": "Linux",
            "machine": "x86_64",
            "effective_uid": 1000,
            "effective_gid": 1000,
        },
        "output_root": freeze["output_root"],
        "minimum_free_bytes": freeze["minimum_free_bytes"],
        "evidence": False,
        "full_confirmatory_campaign_complete": False,
        "results_publication_permitted": False,
        "test_dataset_access": False,
    }
    value["lane_preflight_digest"] = _digest(value)
    return value


def _authorization(
    request: dict[str, object],
    output_root: Path,
    *,
    execution_mode: str = "confirmatory",
) -> dict[str, object]:
    freeze = _freeze(request, output_root, execution_mode=execution_mode)
    return issue_b1_confirmatory_authorization(
        freeze,
        [
            _preflight(freeze, "cpu_float64"),
            _preflight(freeze, "rocm_float32"),
        ],
        operator_acknowledgement=(
            B1_CONFIRMATORY_OPERATOR_ACKNOWLEDGEMENT
            if execution_mode == "confirmatory"
            else B1_CONFIRMATORY_ENGINEERING_SMOKE_ACKNOWLEDGEMENT
        ),
    )


def test_confirmatory_request_resolves_to_120_unique_pairs() -> None:
    request = _request()
    validate_confirmatory_request(request)
    specs = build_pair_specs(request)
    assert len(specs) == B1_CONFIRMATORY_EXPECTED_PAIR_COUNT
    assert len({spec.pair_id for spec in specs}) == 120
    assert len(select_specs(specs, lane="cpu_float64", engineering_smoke=False)) == 60
    assert len(select_specs(specs, lane="rocm_float32", engineering_smoke=True)) == 6


def test_confirmatory_request_rejects_batch_aliasing() -> None:
    request = _request()
    batches = copy.deepcopy(request["validation_batches"])
    assert isinstance(batches, dict)
    batches["1"]["content_sha256"] = batches["0"]["content_sha256"]
    request["validation_batches"] = batches
    with pytest.raises(B1ConfirmatoryError, match="distinct content"):
        validate_confirmatory_request(request)


def test_plan_requires_explicit_resume_and_retry_for_retryable_failure(
    tmp_path: Path,
) -> None:
    request = _request()
    pair_id = build_pair_specs(request)[0].pair_id
    attempt = tmp_path / "pairs" / pair_id / "attempts" / "attempt-001"
    attempt.mkdir(parents=True)
    atomic_write_json(attempt / "started.json", {"pair_id": pair_id})
    atomic_write_json(
        attempt / "failed.json",
        {"pair_id": pair_id, "retry_eligible": True, "failure_class": "infrastructure"},
    )
    with pytest.raises(B1ConfirmatoryError, match="explicit resume"):
        plan_confirmatory_lane(
            request,
            output_root=tmp_path,
            lane="cpu_float64",
            engineering_smoke=False,
            resume=False,
            retry_failed=False,
        )
    with pytest.raises(B1ConfirmatoryError, match="retryable failures"):
        plan_confirmatory_lane(
            request,
            output_root=tmp_path,
            lane="cpu_float64",
            engineering_smoke=False,
            resume=True,
            retry_failed=False,
        )
    resumed = plan_confirmatory_lane(
        request,
        output_root=tmp_path,
        lane="cpu_float64",
        engineering_smoke=False,
        resume=True,
        retry_failed=True,
    )
    assert pair_id in resumed.selected_pair_ids
    state = next(value for value in resumed.pairs if value.pair_id == pair_id)
    assert state.next_attempt_number == 2


def test_resume_selects_never_started_pending_pairs(tmp_path: Path) -> None:
    request = _request()
    specs = build_pair_specs(request)
    first = specs[0]
    _write_completed_attempt(
        tmp_path,
        pair_id=first.pair_id,
        attempt_number=1,
        request=request,
        authorization=_authorization(request, tmp_path),
    )
    plan = plan_confirmatory_lane(
        request,
        output_root=tmp_path,
        lane="cpu_float64",
        engineering_smoke=False,
        resume=True,
        retry_failed=False,
    )
    assert first.pair_id not in plan.selected_pair_ids
    assert len(plan.selected_pair_ids) == 59


def test_orphan_reconciliation_requires_no_lock_and_exact_provenance(
    tmp_path: Path,
) -> None:
    request = _request()
    authorization = _authorization(request, tmp_path)
    spec = build_pair_specs(request)[0]
    attempt = tmp_path / "pairs" / spec.pair_id / "attempts" / "attempt-001"
    attempt.mkdir(parents=True)
    atomic_write_json(
        attempt / "started.json",
        _provenance(
            pair_id=spec.pair_id,
            attempt_number=1,
            request=request,
            authorization=authorization,
        ),
    )
    reconciled = reconcile_orphaned_running_attempts(
        request,
        output_root=tmp_path,
        lane="cpu_float64",
        authorization_token=str(authorization["authorization_token"]),
        project_source_commit=str(authorization["project_source_commit"]),
        source_image_digest=str(authorization["image_digest"]),
        operator_acknowledgement=B1_CONFIRMATORY_RECONCILE_ACKNOWLEDGEMENT,
    )
    assert reconciled == [f"{spec.pair_id}/attempt-001"]
    failed = json.loads((attempt / "failed.json").read_text(encoding="utf-8"))
    assert failed["failure_class"] == "system_interruption"
    assert failed["retry_eligible"] is True


def test_authorization_requires_both_lanes_and_one_image(tmp_path: Path) -> None:
    request = _request()
    freeze = _freeze(request, tmp_path)
    cpu = _preflight(freeze, "cpu_float64")
    rocm = _preflight(freeze, "rocm_float32")
    authorization = issue_b1_confirmatory_authorization(
        freeze,
        [cpu, rocm],
        operator_acknowledgement=B1_CONFIRMATORY_OPERATOR_ACKNOWLEDGEMENT,
    )
    assert authorization["execution_permitted"] is True
    assert authorization["authorized_pair_count"] == 120
    assert authorization["authorization_digest"] != authorization["authorization_token"]
    with pytest.raises(B1ConfirmatoryError, match="exactly two"):
        issue_b1_confirmatory_authorization(
            freeze,
            [cpu],
            operator_acknowledgement=B1_CONFIRMATORY_OPERATOR_ACKNOWLEDGEMENT,
        )
    bad_rocm = _preflight(freeze, "rocm_float32", image="sha256:" + "9" * 64)
    with pytest.raises(B1ConfirmatoryError, match="one immutable image"):
        issue_b1_confirmatory_authorization(
            freeze,
            [cpu, bad_rocm],
            operator_acknowledgement=B1_CONFIRMATORY_OPERATOR_ACKNOWLEDGEMENT,
        )


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("project_source_commit", "9" * 40),
        ("torch2pc_commit", "8" * 40),
        ("image_digest", "sha256:" + "7" * 64),
        ("output_root", "/tmp/other-output-root"),
        ("emergency_stop_path", "/tmp/other-output-root/EMERGENCY-STOP"),
        ("minimum_free_bytes", 2),
        ("request_digest", "6" * 64),
    ],
)
def test_authorization_digest_rejects_mutated_bound_fields(
    tmp_path: Path,
    field: str,
    replacement: object,
) -> None:
    authorization = _authorization(_request(), tmp_path)
    authorization[field] = replacement
    with pytest.raises(B1ConfirmatoryError):
        validate_authorization(authorization)


def test_lane_preflight_requires_complete_record(tmp_path: Path) -> None:
    freeze = _freeze(_request(), tmp_path)
    preflight = _preflight(freeze, "cpu_float64")
    preflight.pop("runtime")
    preflight["lane_preflight_digest"] = _digest(
        {
            key: value
            for key, value in preflight.items()
            if key != "lane_preflight_digest"
        }
    )
    with pytest.raises(B1ConfirmatoryError, match="runtime probe"):
        validate_lane_preflight(preflight)


@pytest.mark.parametrize("field", ["project_source_commit", "output_root"])
def test_authorization_rejects_preflight_binding_mismatch(
    tmp_path: Path,
    field: str,
) -> None:
    request = _request()
    freeze = _freeze(request, tmp_path)
    cpu = _preflight(freeze, "cpu_float64")
    rocm = _preflight(freeze, "rocm_float32")
    cpu[field] = "9" * 40 if field == "project_source_commit" else "/tmp/other-root"
    cpu["lane_preflight_digest"] = _digest(
        {
            key: value
            for key, value in cpu.items()
            if key != "lane_preflight_digest"
        }
    )
    with pytest.raises(B1ConfirmatoryError, match=field):
        issue_b1_confirmatory_authorization(
            freeze,
            [cpu, rocm],
            operator_acknowledgement=B1_CONFIRMATORY_OPERATOR_ACKNOWLEDGEMENT,
        )


def test_rocm_preflight_requires_hip_device(tmp_path: Path) -> None:
    freeze = _freeze(_request(), tmp_path)
    preflight = _preflight(freeze, "rocm_float32")
    runtime = copy.deepcopy(preflight["runtime"])
    assert isinstance(runtime, dict)
    runtime["hip_version"] = None
    preflight["runtime"] = runtime
    preflight["lane_preflight_digest"] = _digest(
        {
            key: value
            for key, value in preflight.items()
            if key != "lane_preflight_digest"
        }
    )
    with pytest.raises(B1ConfirmatoryError, match="HIP runtime"):
        validate_lane_preflight(preflight)


def test_engineering_smoke_rejects_confirmatory_acknowledgement(
    tmp_path: Path,
) -> None:
    request = _request()
    freeze = _freeze(request, tmp_path, execution_mode="engineering_smoke")
    preflights = [
        _preflight(freeze, "cpu_float64"),
        _preflight(freeze, "rocm_float32"),
    ]
    with pytest.raises(B1ConfirmatoryError, match="acknowledgement"):
        issue_b1_confirmatory_authorization(
            freeze,
            preflights,
            operator_acknowledgement=B1_CONFIRMATORY_OPERATOR_ACKNOWLEDGEMENT,
        )


def test_engineering_smoke_authorization_is_domain_separated(
    tmp_path: Path,
) -> None:
    request = _request()
    authorization = _authorization(request, tmp_path, execution_mode="engineering_smoke")
    assert authorization["execution_mode"] == "engineering_smoke"
    assert authorization["authorized_pair_count"] == 12
    assert (
        authorization["operator_acknowledgement"]
        == B1_CONFIRMATORY_ENGINEERING_SMOKE_ACKNOWLEDGEMENT
    )


def test_sealing_accepts_retryable_failure_followed_by_success(tmp_path: Path) -> None:
    request = _request()
    authorization = _authorization(request, tmp_path)
    specs = build_pair_specs(request)
    for index, spec in enumerate(specs):
        if index == 0:
            _write_failed_attempt(
                tmp_path,
                pair_id=spec.pair_id,
                attempt_number=1,
                request=request,
                authorization=authorization,
                failure_class="infrastructure",
                retry_eligible=True,
            )
            _write_completed_attempt(
                tmp_path,
                pair_id=spec.pair_id,
                attempt_number=2,
                request=request,
                authorization=authorization,
            )
        else:
            _write_completed_attempt(
                tmp_path,
                pair_id=spec.pair_id,
                attempt_number=1,
                request=request,
                authorization=authorization,
            )
    decision = seal_b1_confirmatory_campaign(
        request,
        authorization,
        output_root=tmp_path,
    )
    assert decision["decision_id"] == "EQ-B1-CONFIRMATORY"
    assert decision["status"] == "pass"
    assert decision["registered_pair_count"] == 120
    assert decision["observed_pair_count"] == 120
    admission_path = tmp_path / "sealed" / "matched-profiling-admission.json"
    admission = json.loads(admission_path.read_text(encoding="utf-8"))
    assert admission["decision_id"] == "EQ-B1"
    assert admission["source_decision_id"] == "EQ-B1-CONFIRMATORY"
    assert admission["scope"] == "confirmatory"
    assert admission["confirmatory_equivalence_executed"] is True
    assert admission["matched_pairs_expected"] == 120
    assert admission["matched_pairs_observed"] == 120
    assert admission["failed_pairs"] == []
    assert admission["source_decision_sha256"] == sha256_file(tmp_path / "sealed" / "decision.json")
    checksum_registry = (tmp_path / "sealed" / "SHA256SUMS").read_text(encoding="utf-8")
    assert "matched-profiling-admission.json" in checksum_registry


def test_sealing_rejects_non_retryable_failure_history(tmp_path: Path) -> None:
    request = _request()
    authorization = _authorization(request, tmp_path)
    specs = build_pair_specs(request)
    first = specs[0]
    _write_failed_attempt(
        tmp_path,
        pair_id=first.pair_id,
        attempt_number=1,
        request=request,
        authorization=authorization,
        failure_class="correctness",
        retry_eligible=False,
    )
    _write_completed_attempt(
        tmp_path,
        pair_id=first.pair_id,
        attempt_number=2,
        request=request,
        authorization=authorization,
    )
    for spec in specs[1:]:
        _write_completed_attempt(
            tmp_path,
            pair_id=spec.pair_id,
            attempt_number=1,
            request=request,
            authorization=authorization,
        )
    with pytest.raises(B1ConfirmatorySealingError, match="non-retryable"):
        seal_b1_confirmatory_campaign(request, authorization, output_root=tmp_path)


def test_engineering_smoke_cannot_be_sealed_as_confirmatory(tmp_path: Path) -> None:
    request = _request()
    authorization = _authorization(request, tmp_path, execution_mode="engineering_smoke")
    with pytest.raises(B1ConfirmatorySealingError, match="engineering-smoke"):
        seal_b1_confirmatory_campaign(request, authorization, output_root=tmp_path)


def test_partial_production_campaign_cannot_be_sealed(tmp_path: Path) -> None:
    request = _request()
    authorization = _authorization(request, tmp_path)
    specs = select_specs(
        build_pair_specs(request),
        lane=None,
        engineering_smoke=True,
    )
    assert len(specs) == 12
    for spec in specs:
        _write_completed_attempt(
            tmp_path,
            pair_id=spec.pair_id,
            attempt_number=1,
            request=request,
            authorization=authorization,
        )
    with pytest.raises(B1ConfirmatorySealingError, match="no attempts"):
        seal_b1_confirmatory_campaign(request, authorization, output_root=tmp_path)


def _write_failed_attempt(
    root: Path,
    *,
    pair_id: str,
    attempt_number: int,
    request: dict[str, object],
    authorization: dict[str, object],
    failure_class: str,
    retry_eligible: bool,
) -> None:
    attempt = root / "pairs" / pair_id / "attempts" / f"attempt-{attempt_number:03d}"
    attempt.mkdir(parents=True)
    base = _provenance(
        pair_id=pair_id,
        attempt_number=attempt_number,
        request=request,
        authorization=authorization,
    )
    atomic_write_json(attempt / "started.json", base)
    atomic_write_json(
        attempt / "failed.json",
        {
            **base,
            "status": "failed",
            "failure_class": failure_class,
            "retry_eligible": retry_eligible,
        },
    )


def _write_completed_attempt(
    root: Path,
    *,
    pair_id: str,
    attempt_number: int,
    request: dict[str, object],
    authorization: dict[str, object],
) -> None:
    attempt = root / "pairs" / pair_id / "attempts" / f"attempt-{attempt_number:03d}"
    attempt.mkdir(parents=True)
    base = _provenance(
        pair_id=pair_id,
        attempt_number=attempt_number,
        request=request,
        authorization=authorization,
    )
    atomic_write_json(attempt / "started.json", base)
    result = attempt / "result"
    result.mkdir()
    gates = {
        gate_id: {"passed": True, "reasons": []}
        for gate_id in ("STRUCT-B1", "NUM-B1", "TRAJ-B1", "OBS-B1", "PROV-B1")
    }
    spec = next(spec for spec in build_pair_specs(request) if spec.pair_id == pair_id)
    attempt_id = f"attempt-{attempt_number:03d}"
    atomic_write_json(
        result / "pair.json",
        {
            "pair_id": pair_id,
            "pair_admissible": True,
            "gates": gates,
            "pair_spec": {
                "request_id": spec.request_id,
                "attempt_id": attempt_id,
                "lane": spec.lane,
                "method": spec.method,
                "model_seed": spec.model_seed,
                "batch_index": spec.batch_index,
                "run_seed": spec.run_seed,
                "training_mode": spec.training_mode,
                "resolved_config_digest": spec.resolved_config_digest,
                "source_image_digest": authorization["image_digest"],
            },
            "provenance": {
                "request_id": spec.request_id,
                "attempt_id": attempt_id,
                "resolved_config_digest": spec.resolved_config_digest,
                "source_image_digest": authorization["image_digest"],
                "checkpoint_sha256": spec.checkpoint.sha256,
                "batch_sha256": spec.batch.sha256,
                "torch2pc_commit": authorization["torch2pc_commit"],
            },
        },
    )
    (result / "trajectory-metrics.csv").write_text(
        "pair_id,component,passed\n" + f"{pair_id},trajectory,true\n",
        encoding="utf-8",
    )
    (result / "endpoint-metrics.csv").write_text(
        "pair_id,component,passed\n" + f"{pair_id},endpoint,true\n",
        encoding="utf-8",
    )
    (result / "structural-events.jsonl").write_text(
        json.dumps({"component": "state_vjp", "passed": True}) + "\n",
        encoding="utf-8",
    )
    files = (
        result / "pair.json",
        result / "trajectory-metrics.csv",
        result / "endpoint-metrics.csv",
        result / "structural-events.jsonl",
    )
    (result / "SHA256SUMS").write_text(
        "".join(f"{sha256_file(path)}  {path.name}\n" for path in files),
        encoding="utf-8",
    )
    atomic_write_json(
        attempt / "completed.json",
        {
            **base,
            "status": "completed",
            "pair_admissible": True,
            "result_sha256": sha256_file(result / "pair.json"),
        },
    )


def _provenance(
    *,
    pair_id: str,
    attempt_number: int,
    request: dict[str, object],
    authorization: dict[str, object],
) -> dict[str, Any]:
    spec = next(spec for spec in build_pair_specs(request) if spec.pair_id == pair_id)
    return {
        "campaign_id": "stage3b-b1-confirmatory-equivalence-v1",
        "pair_id": pair_id,
        "lane": spec.lane,
        "method": spec.method,
        "model_seed": spec.model_seed,
        "validation_batch_index": spec.batch_index,
        "attempt_id": f"attempt-{attempt_number:03d}",
        "attempt_number": attempt_number,
        "request_id": spec.request_id,
        "request_digest": canonical_json_digest(request),
        "project_source_commit": authorization["project_source_commit"],
        "source_image_digest": authorization["image_digest"],
        "authorization_token": authorization["authorization_token"],
        "resolved_config_digest": spec.resolved_config_digest,
        "checkpoint_sha256": spec.checkpoint.sha256,
        "batch_sha256": spec.batch.sha256,
        "evidence": False,
        "test_dataset_access": False,
    }


def _digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def test_plan_rejects_attempt_after_completed_terminal_state(tmp_path: Path) -> None:
    request = _request()
    pair_id = build_pair_specs(request)[0].pair_id
    first = tmp_path / "pairs" / pair_id / "attempts" / "attempt-001"
    second = tmp_path / "pairs" / pair_id / "attempts" / "attempt-002"
    first.mkdir(parents=True)
    second.mkdir(parents=True)
    atomic_write_json(first / "started.json", {"pair_id": pair_id})
    atomic_write_json(first / "completed.json", {"pair_id": pair_id})
    atomic_write_json(second / "started.json", {"pair_id": pair_id})
    with pytest.raises(B1ConfirmatoryError, match="completed attempt must be last"):
        plan_confirmatory_lane(
            request,
            output_root=tmp_path,
            lane="cpu_float64",
            engineering_smoke=False,
            resume=True,
            retry_failed=False,
        )


def test_plan_rejects_attempt_without_started_marker(tmp_path: Path) -> None:
    request = _request()
    pair_id = build_pair_specs(request)[0].pair_id
    attempt = tmp_path / "pairs" / pair_id / "attempts" / "attempt-001"
    attempt.mkdir(parents=True)
    with pytest.raises(B1ConfirmatoryError, match="lacks started marker"):
        plan_confirmatory_lane(
            request,
            output_root=tmp_path,
            lane="cpu_float64",
            engineering_smoke=False,
            resume=True,
            retry_failed=False,
        )


def test_plan_rejects_inconsistent_retry_classification(tmp_path: Path) -> None:
    request = _request()
    pair_id = build_pair_specs(request)[0].pair_id
    attempt = tmp_path / "pairs" / pair_id / "attempts" / "attempt-001"
    attempt.mkdir(parents=True)
    atomic_write_json(attempt / "started.json", {"pair_id": pair_id})
    atomic_write_json(
        attempt / "failed.json",
        {
            "pair_id": pair_id,
            "failure_class": "infrastructure",
            "retry_eligible": False,
        },
    )
    with pytest.raises(B1ConfirmatoryError, match="retry classification mismatch"):
        plan_confirmatory_lane(
            request,
            output_root=tmp_path,
            lane="cpu_float64",
            engineering_smoke=False,
            resume=True,
            retry_failed=True,
        )


def _write_batch_registry_fixture(
    root: Path,
) -> tuple[
    dict[str, Any],
    dict[int, Path],
    list[tuple[Path, dict[str, Any]]],
]:
    from scripts.export_stage3b_b1_confirmatory_validation_batches import (
        _content_digest,
    )
    from scripts.export_stage3b_b1_shared_validation_batch import sha256_json

    checkpoints: dict[int, Path] = {}
    sources: list[tuple[Path, dict[str, Any]]] = []
    source_records: list[dict[str, object]] = []
    for seed in range(3):
        checkpoint = root / "checkpoints" / f"seed-{seed}.pt"
        config = root / "configs" / f"seed-{seed}.json"
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
        config.parent.mkdir(parents=True, exist_ok=True)
        checkpoint.write_bytes(f"checkpoint-{seed}".encode())
        config.write_text(json.dumps({"seed": seed}), encoding="utf-8")
        checkpoints[seed] = checkpoint
        sources.append((config, {"seed": seed}))
        source_records.append(
            {
                "model_seed": seed,
                "checkpoint_path": checkpoint.relative_to(root).as_posix(),
                "checkpoint_sha256": sha256_file(checkpoint),
                "resolved_config_path": config.relative_to(root).as_posix(),
                "resolved_config_sha256": sha256_file(config),
            }
        )

    batch_records: list[dict[str, object]] = []
    for batch_index in range(10):
        inputs = torch.full((256, 1, 2, 2), float(batch_index))
        targets = torch.arange(256, dtype=torch.long) + batch_index
        content_sha256 = _content_digest(inputs, targets)
        artifact = root / "batches" / f"validation-batch-{batch_index:03d}.pt"
        manifest = root / "batches" / f"validation-batch-{batch_index:03d}.json"
        artifact.parent.mkdir(parents=True, exist_ok=True)
        torch.save(
            {
                "inputs": inputs,
                "targets": targets,
                "split": "validation",
                "dataset": "FashionMNIST",
                "batch_index": batch_index,
                "batch_size": 256,
                "content_sha256": content_sha256,
                "test_split_accessed": False,
            },
            artifact,
        )
        artifact_record = {
            "schema_version": 1,
            "artifact_type": "stage3b_b1_confirmatory_validation_batch",
            "artifact_path": artifact.relative_to(root).as_posix(),
            "artifact_sha256": sha256_file(artifact),
            "content_sha256": content_sha256,
            "dataset": "FashionMNIST",
            "split": "validation",
            "batch_index": batch_index,
            "batch_size": 256,
            "include_test": False,
            "test_split_accessed": False,
        }
        manifest.write_text(
            json.dumps(artifact_record, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        batch_records.append(
            {
                "batch_index": batch_index,
                "path": artifact.relative_to(root).as_posix(),
                "sha256": sha256_file(artifact),
                "content_sha256": content_sha256,
                "manifest_path": manifest.relative_to(root).as_posix(),
                "manifest_sha256": sha256_file(manifest),
                "split": "validation",
                "batch_size": 256,
            }
        )

    registry: dict[str, Any] = {
        "schema_version": 1,
        "artifact_type": "stage3b_b1_confirmatory_validation_batch_registry",
        "dataset": "FashionMNIST",
        "split": "validation",
        "batch_count": 10,
        "batch_size": 256,
        "batch_indices": list(range(10)),
        "distinct_paths_required": True,
        "distinct_content_digests_required": True,
        "include_test": False,
        "test_split_accessed": False,
        "sources": source_records,
        "batches": batch_records,
    }
    registry["registry_digest"] = sha256_json(registry)
    return registry, checkpoints, sources


def _refresh_registry_digest(registry: dict[str, Any]) -> None:
    from scripts.export_stage3b_b1_shared_validation_batch import sha256_json

    registry.pop("registry_digest", None)
    registry["registry_digest"] = sha256_json(registry)


def test_batch_registry_validates_artifacts_manifests_and_sources(
    tmp_path: Path,
) -> None:
    from scripts.freeze_stage3b_b1_confirmatory import _validate_batch_registry

    registry, checkpoints, sources = _write_batch_registry_fixture(tmp_path)
    batches = _validate_batch_registry(
        registry,
        root=tmp_path,
        checkpoints=checkpoints,
        sources=sources,
    )
    assert len(batches) == 10
    assert batches["0"]["batch_index"] == 0


def test_batch_registry_rejects_checkpoint_source_substitution(
    tmp_path: Path,
) -> None:
    from scripts.freeze_stage3b_b1_confirmatory import _validate_batch_registry

    registry, checkpoints, sources = _write_batch_registry_fixture(tmp_path)
    raw_sources = registry["sources"]
    assert isinstance(raw_sources, list)
    raw_sources[0]["checkpoint_sha256"] = "0" * 64
    _refresh_registry_digest(registry)
    with pytest.raises(ExportError, match="source mismatch"):
        _validate_batch_registry(
            registry,
            root=tmp_path,
            checkpoints=checkpoints,
            sources=sources,
        )


def test_batch_registry_rejects_rehashed_manifest_metadata_substitution(
    tmp_path: Path,
) -> None:
    from scripts.export_stage3b_b1_shared_validation_batch import ExportError
    from scripts.freeze_stage3b_b1_confirmatory import _validate_batch_registry

    registry, checkpoints, sources = _write_batch_registry_fixture(tmp_path)
    batches = registry["batches"]
    assert isinstance(batches, list)
    first = batches[0]
    manifest_path = tmp_path / str(first["manifest_path"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["split"] = "test"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    first["manifest_sha256"] = sha256_file(manifest_path)
    _refresh_registry_digest(registry)
    with pytest.raises(ExportError, match="manifest metadata mismatch"):
        _validate_batch_registry(
            registry,
            root=tmp_path,
            checkpoints=checkpoints,
            sources=sources,
        )


def test_batch_export_json_is_write_once_and_idempotent(tmp_path: Path) -> None:
    from scripts.export_stage3b_b1_confirmatory_validation_batches import (
        _write_or_verify_json,
    )

    path = tmp_path / "manifest.json"
    payload = {"batch_index": 0, "content_sha256": "a" * 64}
    _write_or_verify_json(path, payload)
    first_sha = sha256_file(path)
    _write_or_verify_json(path, payload)
    assert sha256_file(path) == first_sha
    with pytest.raises(ExportError, match="differs"):
        _write_or_verify_json(path, {**payload, "batch_index": 1})


def test_batch_export_rejects_existing_artifact_without_tensors(
    tmp_path: Path,
) -> None:
    from scripts.export_stage3b_b1_confirmatory_validation_batches import (
        _content_digest,
        _write_or_verify_artifact,
    )

    path = tmp_path / "batch.pt"
    inputs = torch.zeros((256, 1, 2, 2))
    targets = torch.zeros(256, dtype=torch.long)
    content_sha256 = _content_digest(inputs, targets)
    torch.save(
        {
            "inputs": "not-a-tensor",
            "targets": "not-a-tensor",
            "split": "validation",
            "batch_index": 0,
            "batch_size": 256,
            "content_sha256": content_sha256,
        },
        path,
    )
    with pytest.raises(ExportError, match="tensors are missing"):
        _write_or_verify_artifact(
            path,
            {
                "inputs": inputs,
                "targets": targets,
                "split": "validation",
                "batch_index": 0,
                "batch_size": 256,
                "content_sha256": content_sha256,
            },
        )
