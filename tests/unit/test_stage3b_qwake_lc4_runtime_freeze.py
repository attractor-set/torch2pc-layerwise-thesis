from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

import pytest
import torch
from torch import nn

import torch2pc_thesis.stage3b_qwake_lc4_runtime_freeze as runtime
from torch2pc_thesis.stage3b_qwake_lc4_bounded import capture_fixedpred_frontier
from torch2pc_thesis.stage3b_qwake_lc4_runtime_freeze import (
    RUNTIME_AUTHORIZATION_ID,
    RUNTIME_CANDIDATE_INDICES,
    RUNTIME_ENGINEERING_BATCH_ID,
    RUNTIME_FREEZE_REQUEST_ID,
    RUNTIME_MODEL_SEED,
    RUNTIME_OPERATOR_ACKNOWLEDGEMENT,
    RUNTIME_OUTPUT_ROOT,
    RUNTIME_PREFLIGHT_ID,
    QWakeLC4RuntimeFreezeError,
    QWakeLC4RuntimePreflight,
    RuntimeAdapterId,
    RuntimeArmOrder,
    RuntimeFreezePermissionSet,
    RuntimeFrontierAdapter,
    RuntimeLane,
    RuntimeProbe,
    RuntimeSourceIdentity,
    adapter_registry_sha256,
    build_runtime_authorization,
    build_runtime_preflight,
    canonical_json,
    load_runtime_authorization,
    load_runtime_preflight,
    runtime_authorization_cells,
    sha256_object,
    verify_frozen_request,
)

ROOT = Path(__file__).resolve().parents[2]
REQUEST_ROOT = ROOT / (
    "experiments/frozen/"
    "stage3b-qwake-lc4-f-runtime-freeze-request-v1"
)
EXPECTED_REQUEST_SHA = (
    "sha256:"
    "bc4e36f9265837dc0a36f0eca039b057a5113c4ef872f72e1698db5bc4930506"
)


def _digest(character: str) -> str:
    return "sha256:" + character * 64


def _source_identity() -> RuntimeSourceIdentity:
    return RuntimeSourceIdentity(
        source_commit="a" * 40,
        source_index_sha256=_digest("1"),
        torch2pc_commit="b" * 40,
        image_digest=_digest("2"),
        image_repo_digest="example.invalid/image@" + _digest("2"),
        request_sha256=_digest("3"),
        implementation_source_sha256=_digest("4"),
        implementation_manifest_sha256=_digest("5"),
        implementation_registry_sha256=_digest("6"),
        lc3_contract_sha256=_digest("7"),
        lc3_contract_registry_sha256=_digest("8"),
        adapter_registry_sha256=_digest("9"),
    )


def _probes() -> tuple[RuntimeProbe, ...]:
    return (
        RuntimeProbe(
            lane=RuntimeLane.CPU_FLOAT64_ENGINEERING,
            python_version="3.12.3",
            python_implementation="CPython",
            python_executable="/usr/bin/python3.12",
            platform="Linux-test",
            machine="x86_64",
            torch_version="2.9.1+rocm7.2.1",
            hip_version="7.2",
            accelerator_available=True,
            accelerator_count=1,
            accelerator_name="AMD Radeon RX 7700 XT",
            dtype="float64",
            memory_source="psutil_process_rss_and_uss",
            clock_source="time_perf_counter_ns_monotonic",
        ),
        RuntimeProbe(
            lane=RuntimeLane.ROCM_FLOAT32_CANONICAL,
            python_version="3.12.3",
            python_implementation="CPython",
            python_executable="/usr/bin/python3.12",
            platform="Linux-test",
            machine="x86_64",
            torch_version="2.9.1+rocm7.2.1",
            hip_version="7.2",
            accelerator_available=True,
            accelerator_count=1,
            accelerator_name="AMD Radeon RX 7700 XT",
            dtype="float32",
            memory_source="torch_cuda_max_memory_allocated_and_reserved",
            clock_source="time_perf_counter_ns_monotonic",
        ),
    )


def _preflight() -> QWakeLC4RuntimePreflight:
    payload: dict[str, object] = {
        "schema_version": 1,
        "preflight_id": RUNTIME_PREFLIGHT_ID,
        "status": "runtime_preflight_passed_authorization_not_issued",
        "captured_at_utc": "2026-07-27T15:00:00Z",
        "source_identity": _source_identity(),
        "runtime_probes": _probes(),
        "bound_adapter_ids": tuple(RuntimeAdapterId),
        "permissions": RuntimeFreezePermissionSet.deny_all(),
        "execution_authorization_present": False,
        "runtime_execution_permitted": False,
        "runtime_execution_performed": False,
        "engineering_evidence_present": False,
        "scientific_execution_open": False,
        "test_dataset_access": False,
        "publication_permitted": False,
        "image_freeze_permitted": False,
        "output_root": RUNTIME_OUTPUT_ROOT.as_posix(),
        "output_root_absent": True,
    }
    return QWakeLC4RuntimePreflight(
        **payload,
        preflight_sha256=sha256_object(payload),
    )


def _write_json(path: Path, value: object) -> None:
    path.write_text(canonical_json(value), encoding="utf-8")


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_frozen_request_inventory_digest_and_closed_semantics() -> None:
    assert sorted(path.name for path in REQUEST_ROOT.iterdir()) == [
        "SHA256SUMS",
        "request.json",
    ]
    request_path = REQUEST_ROOT / "request.json"
    observed = "sha256:" + hashlib.sha256(request_path.read_bytes()).hexdigest()
    assert observed == EXPECTED_REQUEST_SHA
    assert verify_frozen_request(ROOT) == EXPECTED_REQUEST_SHA
    payload = _load_json(request_path)
    assert payload["request_id"] == RUNTIME_FREEZE_REQUEST_ID
    assert payload["status"] == (
        "runtime_freeze_request_materialized_execution_closed"
    )
    assert payload["runtime_matrix"] == {
        "authorization_cell_count": 168,
        "batch_id": RUNTIME_ENGINEERING_BATCH_ID,
        "candidate_indices": list(RUNTIME_CANDIDATE_INDICES),
        "lanes": [item.value for item in RuntimeLane],
        "matched_pair_count": 168,
        "model_seed": RUNTIME_MODEL_SEED,
        "pair_count_per_cell": 12,
        "reserve_probe_count": 28,
        "reserve_probe_positions": [
            "before_repeat_0",
            "after_repeat_11",
        ],
        "runtime_cell_count": 14,
    }
    assert payload["execution"]["runtime_execution_performed"] is False
    assert payload["execution"]["scientific_execution_open"] is False
    assert payload["execution"]["test_dataset_access"] is False
    assert payload["execution"]["publication_permitted"] is False


def test_runtime_authorization_matrix_is_exact_and_balanced() -> None:
    cells = runtime_authorization_cells()
    assert len(cells) == 2 * 7 * 12
    assert Counter(cell.lane for cell in cells) == {
        RuntimeLane.CPU_FLOAT64_ENGINEERING: 84,
        RuntimeLane.ROCM_FLOAT32_CANONICAL: 84,
    }
    assert Counter(cell.candidate_index for cell in cells) == {
        index: 24 for index in RUNTIME_CANDIDATE_INDICES
    }
    assert Counter(cell.repeat_index for cell in cells) == {
        index: 14 for index in range(12)
    }
    assert Counter(cell.arm_order for cell in cells) == {
        RuntimeArmOrder.EXACT_THEN_ANALYTIC: 84,
        RuntimeArmOrder.ANALYTIC_THEN_EXACT: 84,
    }
    assert sum(cell.reserve_probe_before_repeat_zero for cell in cells) == 14
    assert sum(cell.reserve_probe_after_repeat_eleven for cell in cells) == 14


def test_preflight_and_authorization_round_trip(tmp_path: Path) -> None:
    preflight = _preflight()
    authorization = build_runtime_authorization(
        preflight,
        issued_at_utc="2026-07-27T15:01:00Z",
        operator_acknowledgement=RUNTIME_OPERATOR_ACKNOWLEDGEMENT,
        output_root_absent_at_issue=True,
    )
    assert authorization.authorization_id == RUNTIME_AUTHORIZATION_ID
    assert authorization.preflight_sha256 == preflight.preflight_sha256
    assert authorization.source_identity == preflight.source_identity
    assert authorization.permissions == (
        RuntimeFreezePermissionSet.complete_engineering()
    )
    assert authorization.runtime_execution_permitted is True
    assert authorization.runtime_execution_performed is False
    assert authorization.engineering_evidence_present is False
    assert authorization.scientific_execution_open is False
    assert authorization.test_dataset_access is False
    assert authorization.publication_permitted is False
    assert authorization.image_freeze_permitted is False

    preflight_path = tmp_path / "preflight.json"
    authorization_path = tmp_path / "authorization.json"
    _write_json(preflight_path, preflight)
    _write_json(authorization_path, authorization)
    assert load_runtime_preflight(preflight_path) == preflight
    assert load_runtime_authorization(authorization_path) == authorization


def test_preflight_rejects_open_capabilities() -> None:
    preflight = _preflight()
    payload = dict(vars(preflight))
    payload.pop("preflight_sha256")
    payload["runtime_execution_permitted"] = True
    with pytest.raises(QWakeLC4RuntimeFreezeError):
        QWakeLC4RuntimePreflight(
            **payload,
            preflight_sha256=sha256_object(payload),
        )


def test_authorization_requires_exact_acknowledgement() -> None:
    with pytest.raises(QWakeLC4RuntimeFreezeError):
        build_runtime_authorization(
            _preflight(),
            issued_at_utc="2026-07-27T15:01:00Z",
            operator_acknowledgement="AUTHORIZE_SOMETHING_ELSE",
            output_root_absent_at_issue=True,
        )


def test_adapter_registry_is_stable_and_complete() -> None:
    assert [item.value for item in RuntimeAdapterId] == [
        "capture_fixedpred_frontier",
        "capture_opaque_state",
        "restore_registered_rng",
        "run_complete_exact_suffix",
        "run_analytic_wavefront_completion",
        "materialize_required_response",
        "compare_required_responses",
        "map_resource_trajectory",
        "run_complete_exact_reserve_probe",
        "aggregate_paired_costs",
    ]
    assert adapter_registry_sha256() == (
        "sha256:40397474de6c97663ac44c718d4c52846a4ba077bc5343a0d10114afd576bbde"
    )


def test_build_preflight_binds_all_identities(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    torch2pc = tmp_path / "Torch2PC"
    project.mkdir()
    torch2pc.mkdir()
    monkeypatch.setattr(runtime, "_require_clean_checkout", lambda *args, **kwargs: None)
    monkeypatch.setattr(runtime, "verify_frozen_request", lambda root: _digest("3"))
    monkeypatch.setattr(
        runtime,
        "_verify_implementation_package",
        lambda root: {
            "source": _digest("4"),
            "manifest": _digest("5"),
            "registry": _digest("6"),
        },
    )
    monkeypatch.setattr(
        runtime,
        "_verify_lc3_contract",
        lambda root: {
            "contract": _digest("7"),
            "registry": _digest("8"),
        },
    )
    monkeypatch.setattr(runtime, "_source_index_sha256", lambda root: _digest("1"))
    monkeypatch.setattr(runtime, "adapter_registry_sha256", lambda: _digest("9"))

    preflight = build_runtime_preflight(
        project,
        torch2pc,
        source_commit="a" * 40,
        torch2pc_commit="b" * 40,
        image_digest=_digest("2"),
        image_repo_digest="example.invalid/image@" + _digest("2"),
        captured_at_utc="2026-07-27T15:00:00Z",
        runtime_probes=_probes(),
    )
    assert preflight.source_identity == _source_identity()
    assert preflight.permissions == RuntimeFreezePermissionSet.deny_all()
    assert preflight.bound_adapter_ids == tuple(RuntimeAdapterId)
    assert preflight.output_root_absent is True


def test_cpu_frontier_adapter_captures_supplied_state_without_mutation() -> None:
    torch.manual_seed(11)
    dtype = torch.float64
    model = nn.Sequential(
        nn.Linear(4, 4),
        nn.Tanh(),
        nn.Linear(4, 4),
        nn.Tanh(),
        nn.Linear(4, 3),
        nn.Identity(),
    ).to(dtype=dtype)
    inputs = torch.randn(2, 4, dtype=dtype)
    targets = torch.tensor([0, 2])
    frontier = capture_fixedpred_frontier(
        model,
        nn.CrossEntropyLoss(),
        inputs,
        targets,
        candidate_index=2,
    )
    before = tuple(item.detach().clone() for item in frontier.beliefs)
    snapshot = RuntimeFrontierAdapter(
        RuntimeLane.CPU_FLOAT64_ENGINEERING
    ).capture(
        model,
        fixed=frontier.fixed,
        beliefs=frontier.beliefs,
        errors=frontier.errors,
        endpoint_loss=frontier.endpoint_loss,
        candidate_index=frontier.candidate_index,
        input_batch=inputs,
        target_batch=targets,
        model_seed=RUNTIME_MODEL_SEED,
        batch_id=RUNTIME_ENGINEERING_BATCH_ID,
        comparison_profile_id="cpu-f64-response-v1",
        cost_profile_id="cpu-f64-cost-v1",
        deterministic_runtime_controls={
            "deterministic_algorithms": True,
            "torch_num_threads": 1,
        },
    )
    assert snapshot.frontier.candidate_index == 2
    assert snapshot.lane_profile_id == RuntimeLane.CPU_FLOAT64_ENGINEERING.value
    assert snapshot.opaque_state_ref.startswith("sha256:")
    assert all(
        torch.equal(observed, expected)
        for observed, expected in zip(frontier.beliefs, before, strict=True)
    )


def test_frontier_adapter_rejects_wrong_lane_dtype() -> None:
    model = nn.Sequential(*(nn.Identity() for _ in range(6)))
    value = torch.zeros(1, dtype=torch.float32)
    with pytest.raises(QWakeLC4RuntimeFreezeError):
        RuntimeFrontierAdapter(RuntimeLane.CPU_FLOAT64_ENGINEERING).capture(
            model,
            fixed=(value,) * 7,
            beliefs=(value,) * 7,
            errors=(value,) * 7,
            endpoint_loss=value.squeeze(),
            candidate_index=0,
            input_batch=value,
            target_batch=torch.zeros(1, dtype=torch.long),
            model_seed=RUNTIME_MODEL_SEED,
            batch_id=RUNTIME_ENGINEERING_BATCH_ID,
            comparison_profile_id="comparison-v1",
            cost_profile_id="cost-v1",
            deterministic_runtime_controls={},
        )


def test_authoring_manifest_binds_code_request_and_closed_gates() -> None:
    authoring_root = ROOT / (
        "experiments/frozen/"
        "stage3b-qwake-lc4-f-runtime-freeze-authoring-v1"
    )
    manifest_path = authoring_root / "authoring.json"
    registry_path = authoring_root / "SHA256SUMS"
    assert hashlib.sha256(manifest_path.read_bytes()).hexdigest() == (
        "c0a11996708b091e737a0bfa60e2a000f65b9e9f0971e8c3041838f25922860a"
    )
    assert hashlib.sha256(registry_path.read_bytes()).hexdigest() == (
        "a59af6fe70612277ceaecba9a86a2dc49dcb2612154993d9c7cc10d8c3bcb7f4"
    )
    assert registry_path.read_text(encoding="utf-8") == (
        "c0a11996708b091e737a0bfa60e2a000f65b9e9f0971e8c3041838f25922860a"
        "  authoring.json\n"
    )
    payload = _load_json(manifest_path)
    assert payload["authoring_id"] == (
        "stage3b-qwake-lc4-f-runtime-freeze-authoring-v1"
    )
    assert payload["status"] == (
        "runtime_freeze_authoring_materialized_execution_closed"
    )
    assert payload["module"]["sha256"] == (
        "sha256:003759e0eac5062e34b0ead1f24c1e1babb09f096023539ac3303a2af9957a7c"
    )
    assert payload["scripts"]["preflight"]["sha256"] == (
        "sha256:8f014be2a41b4fe726da0ad7cf5c36ced9a4dc2359514705f15ae924a0a262ff"
    )
    assert payload["scripts"]["authorization"]["sha256"] == (
        "sha256:c6a2454e2f7b8aaadd3c67badf7b70d605a59c422dffcbf07a1b2c88b5e3cf64"
    )
    assert payload["scripts"]["seal"]["sha256"] == (
        "sha256:eb74d56fd09857a91906e904c3be44dc6afe3bc050b63d353d53a2b956a873a0"
    )
    assert payload["request"]["sha256"] == EXPECTED_REQUEST_SHA
    assert payload["gates"]["qw_lc4_i_complete"] is True
    assert payload["gates"]["qw_lc4_f_authoring_materialized"] is True
    assert payload["gates"]["qw_lc4_f_request_frozen"] is True
    assert payload["gates"]["qw_lc4_f_materialized"] is False
    assert payload["gates"]["qw_lc4_f_complete"] is False
    assert payload["gates"]["qw_lc4_e_branch_permitted"] is False
    assert payload["gates"]["local_compute_execution_open"] is False
    assert payload["gates"]["scientific_execution_open"] is False
    assert payload["gates"]["test_dataset_access"] is False
    assert payload["gates"]["publication_permitted"] is False


def test_authoring_surfaces_do_not_expose_runtime_executor() -> None:
    module_text = (
        ROOT / "src/torch2pc_thesis/stage3b_qwake_lc4_runtime_freeze.py"
    ).read_text(encoding="utf-8")
    script_paths = (
        ROOT / "scripts/preflight_stage3b_qwake_lc4_runtime.py",
        ROOT / "scripts/authorize_stage3b_qwake_lc4_runtime.py",
        ROOT / "scripts/seal_stage3b_qwake_lc4_runtime_freeze.py",
    )
    combined = module_text + "\n" + "\n".join(
        path.read_text(encoding="utf-8") for path in script_paths
    )
    forbidden_definitions = (
        "def run_runtime_execution(",
        "def execute_matched_shadow(",
        "def load_test_dataset(",
        "def publish_result(",
        "def adjudicate_scientific_result(",
    )
    assert all(item not in combined for item in forbidden_definitions)
    assert "runtime_execution_performed=False" in module_text
    assert "scientific_execution_open=False" in module_text
