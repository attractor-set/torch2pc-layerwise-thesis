from __future__ import annotations

from pathlib import Path

import torch

from torch2pc_thesis.stage3b_a1_obs_ni0 import ObserverArm
from torch2pc_thesis.stage3b_a1_obs_oh0 import ExecutionOrder
from torch2pc_thesis.stage3b_a1_obs_oh0_memory import (
    PAYLOAD_LIMIT_BYTES,
    MemoryExecutionResult,
    MemoryPairRecord,
    MemoryWorkerRequest,
    aggregate_memory_records,
    payload_memory_breakdown,
    read_proc_status_bytes,
)
from torch2pc_thesis.stage3b_a1_observer import ObserverPayload


def memory_result(
    *,
    arm: ObserverArm,
    seed: int,
    enabled: bool,
    payload: int = 1024,
    peak: int = 2048,
) -> MemoryExecutionResult:
    return MemoryExecutionResult(
        lane="cpu",
        arm=arm,
        observer_enabled=enabled,
        model_seed=seed,
        batch_index=0,
        source_git_commit="a" * 40,
        source_git_branch="research/test",
        experiment_image="example:1",
        device_name="cpu",
        dtype="torch.float64",
        payload_bytes=payload if enabled else 0,
        payload_records=12 if enabled else 0,
        payload_bytes_by_role={"layer_input": payload} if enabled else {},
        payload_bytes_by_layer={"0": payload} if enabled else {},
        observer_validation_passed=True,
        baseline_rss_bytes=10_000,
        peak_rss_bytes=10_000 + peak,
        final_rss_bytes=10_000 + peak,
        vm_hwm_bytes=20_000,
        incremental_peak_rss_bytes=peak,
        incremental_final_rss_bytes=peak,
        baseline_allocated_bytes=None,
        baseline_reserved_bytes=None,
        peak_allocated_bytes=None,
        peak_reserved_bytes=None,
        current_allocated_bytes=None,
        current_reserved_bytes=None,
        incremental_peak_allocated_bytes=None,
        incremental_peak_reserved_bytes=None,
    )


def test_memory_worker_request_round_trip() -> None:
    request = MemoryWorkerRequest(
        device="gpu",
        lane="rocm",
        arm=ObserverArm.JOINT_VJP,
        observer_enabled=True,
        model_seed=2,
        batch_index=9,
        source_git_commit="a" * 40,
        source_git_branch="research/test",
        experiment_image="example:1",
        rss_sampler_interval_ms=1.0,
    )
    assert MemoryWorkerRequest.from_dict(request.to_dict()) == request


def test_read_proc_status_bytes_parses_kilobytes(tmp_path: Path) -> None:
    status = tmp_path / "status"
    status.write_text("Name:\tpython\nVmRSS:\t123 kB\n", encoding="utf-8")
    assert read_proc_status_bytes("VmRSS", path=status) == 123 * 1024


def test_payload_memory_breakdown_is_exact() -> None:
    records = (
        ObserverPayload(
            key="layer-00:layer_input:00",
            layer_index=0,
            layer_name="0",
            role="layer_input",
            occurrence=0,
            tensor=torch.zeros(4, dtype=torch.float32),
            source_shape=(4,),
            source_dtype="torch.float32",
            source_device="cpu",
        ),
        ObserverPayload(
            key="layer-00:layer_output:00",
            layer_index=0,
            layer_name="0",
            role="layer_output",
            occurrence=0,
            tensor=torch.zeros(2, dtype=torch.float64),
            source_shape=(2,),
            source_dtype="torch.float64",
            source_device="cpu",
        ),
    )
    total, by_role, by_layer = payload_memory_breakdown(records)
    assert total == 32
    assert by_role == {"layer_input": 16, "layer_output": 16}
    assert by_layer == {"0": 32}


def test_memory_aggregation_passes_registered_cpu_bound() -> None:
    pairs = [
        MemoryPairRecord(
            order=ExecutionOrder.OFF_THEN_ON,
            reference=memory_result(
                arm=arm,
                seed=seed,
                enabled=False,
                peak=1000,
            ),
            candidate=memory_result(
                arm=arm,
                seed=seed,
                enabled=True,
                payload=1024,
                peak=2500,
            ),
        )
        for arm in ObserverArm
        for seed in (0, 1, 2)
    ]
    summaries = aggregate_memory_records(
        pairs,
        lane="cpu",
        model_seeds=[0, 1, 2],
    )
    assert all(item.passed for item in summaries.values())


def test_memory_aggregation_rejects_payload_over_limit() -> None:
    pairs = [
        MemoryPairRecord(
            order=ExecutionOrder.OFF_THEN_ON,
            reference=memory_result(
                arm=arm,
                seed=seed,
                enabled=False,
                peak=1000,
            ),
            candidate=memory_result(
                arm=arm,
                seed=seed,
                enabled=True,
                payload=PAYLOAD_LIMIT_BYTES + 1,
                peak=2000,
            ),
        )
        for arm in ObserverArm
        for seed in (0, 1, 2)
    ]
    summaries = aggregate_memory_records(
        pairs,
        lane="cpu",
        model_seeds=[0, 1, 2],
    )
    assert summaries[ObserverArm.FIXEDPRED].passed is False
