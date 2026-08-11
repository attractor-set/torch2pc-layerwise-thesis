from __future__ import annotations

import ast
from pathlib import Path

import pytest

from torch2pc_thesis.stage3b_qwake_attempt_005_contract import (
    ATTEMPT_005_ID,
    ATTEMPT_005_INVOCATION_ACKNOWLEDGEMENT,
    ATTEMPT_005_LEASE_ACKNOWLEDGEMENT,
    ATTEMPT_005_OUTPUT_ROOT,
    EXPECTED_GENERIC_RUNTIME_BACKEND_SHA256,
)
from torch2pc_thesis.stage3b_qwake_attempt_005_lane_isolation import (
    ENABLE_ENV,
    INTERNAL_LANE_WORKER_COUNT,
    ROCM_CPU_AFFINITY,
    ROCM_THREAD_ENV,
    WARMUP_CELL_COUNT_PER_LANE,
    WARMUP_REPEAT_INDICES,
    _warmup_cells,
    _worker_env,
    attempt005_lane_isolation_evidence,
)
from torch2pc_thesis.stage3b_qwake_lc4_runtime_freeze import (
    RuntimeLane,
    load_runtime_authorization,
)

ROOT = Path(__file__).resolve().parents[2]
AUTHORIZATION = (
    ROOT
    / "experiments/frozen/stage3b-qwake-lc4-f-runtime-freeze-v1/authorization.json"
)
HOST = ROOT / "scripts/run_stage3b_qwake_attempt_005_host_one_shot.py"
GENERIC_BACKEND = (
    ROOT / "src/torch2pc_thesis/stage3b_qwake_lc4_runtime_backend.py"
)


def test_attempt005_identity_namespace_is_distinct() -> None:
    assert ATTEMPT_005_ID.endswith("attempt-005")
    assert ATTEMPT_005_OUTPUT_ROOT.as_posix().endswith("attempt-005")
    assert ATTEMPT_005_INVOCATION_ACKNOWLEDGEMENT == (
        "AUTHORIZE_QWAKE_LC4_ATTEMPT_005_ONE_SHOT_ENGINEERING_INVOCATION"
    )
    assert ATTEMPT_005_LEASE_ACKNOWLEDGEMENT == (
        "CLAIM_QWAKE_LC4_ATTEMPT_005_FROM_LANE_ISOLATED_EXECUTION_FREEZE"
    )


def test_attempt005_warmups_are_two_reserve_free_cells_per_candidate_per_lane() -> None:
    authorization = load_runtime_authorization(AUTHORIZATION)
    for lane in RuntimeLane:
        warmups = _warmup_cells(authorization, lane)
        assert len(warmups) == WARMUP_CELL_COUNT_PER_LANE
        assert {item.repeat_index for item in warmups} == set(WARMUP_REPEAT_INDICES)
        assert all(not item.reserve_probe_before_repeat_zero for item in warmups)
        assert all(not item.reserve_probe_after_repeat_eleven for item in warmups)


def test_attempt005_worker_environments_are_lane_local(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENABLE_ENV, "1")
    monkeypatch.setenv("QWAKE_ATTEMPT_004_CPU_STABILIZATION", "leak")

    cpu = _worker_env(RuntimeLane.CPU_FLOAT64_ENGINEERING)
    rocm = _worker_env(RuntimeLane.ROCM_FLOAT32_CANONICAL)

    assert cpu["QWAKE_ATTEMPT_004_CPU_STABILIZATION"] == "1"
    assert {cpu[key] for key in ROCM_THREAD_ENV} == {"1"}
    assert "QWAKE_ATTEMPT_004_CPU_STABILIZATION" not in rocm
    assert {rocm[key] for key in ROCM_THREAD_ENV} == {"8"}
    assert rocm["HIP_VISIBLE_DEVICES"] == "0"


def test_attempt005_profile_preserves_frozen_measurement_contract() -> None:
    evidence = attempt005_lane_isolation_evidence()
    assert evidence["lane_process_isolation"] is True
    assert evidence["internal_lane_worker_count"] == INTERNAL_LANE_WORKER_COUNT == 2
    assert evidence["measured_authorized_cell_count"] == 168
    assert evidence["reserve_probe_count"] == 28
    assert evidence["aggregate_count"] == 14
    assert evidence["measured_pair_count_per_candidate"] == 12
    assert evidence["order_effect_tolerance_unchanged"] is True
    assert evidence["cpu_primary_clock"] == "time_process_time_ns"
    assert evidence["rocm_primary_clock"] == "rocm_event_time_ns"
    assert evidence["cpu_worker_affinity"] == [0]
    assert evidence["rocm_worker_affinity"] == list(ROCM_CPU_AFFINITY)
    assert evidence["warmup_included_in_measured_matrix"] is False
    assert evidence["cross_lane_comparison_permitted"] is False
    assert evidence["single_combined_runtime_report_required"] is True


def test_attempt005_host_has_one_external_popen_and_parent_cpuset_0_7() -> None:
    text = HOST.read_text(encoding="utf-8")
    tree = ast.parse(text)
    popen_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "subprocess"
        and node.func.attr == "Popen"
    ]
    assert len(popen_calls) == 1
    assert 'CPUSET_CPUS: Final = "0-7"' in text
    assert "LANE_ISOLATION_ENABLE_ENV" in text
    assert "AUTOMATIC_RETRY_PERFORMED=false" in text


def test_historical_generic_backend_identity_is_unchanged() -> None:
    import hashlib

    observed = "sha256:" + hashlib.sha256(GENERIC_BACKEND.read_bytes()).hexdigest()
    assert observed == EXPECTED_GENERIC_RUNTIME_BACKEND_SHA256
