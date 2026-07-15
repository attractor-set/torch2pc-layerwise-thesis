from __future__ import annotations

from pathlib import Path

import pytest
import torch
import torch.nn as nn

from torch2pc_thesis.stage3b_a1_obs_ni0 import ObserverArm
from torch2pc_thesis.stage3b_a1_obs_oh0 import (
    BENCHMARK_SCHEMA_ID,
    ExecutionOrder,
    TimedExecution,
    TimingPairRecord,
    TimingPhase,
    aggregate_timing_records,
    benchmark_schema_manifest,
    execution_order_for,
    run_timing_pair,
)
from torch2pc_thesis.stage3b_a1_observer import ObserverValidation


def validation(records: int = 6) -> ObserverValidation:
    return ObserverValidation(
        observer_schema_id="stage3b-a1-obs-ni0-first-forward-io-v1",
        top_level_layers=3,
        expected_records=records,
        observed_records=records,
        input_call_counts=(3, 3, 3),
        output_call_counts=(3, 3, 3),
        complete=True,
        balanced_forward_calls=True,
        unique_keys=True,
        detached=True,
        finite=True,
        metadata_preserved=True,
        cleanup_complete=True,
        setup_rng_unchanged=True,
    )


def execution(enabled: bool, elapsed: int) -> TimedExecution:
    return TimedExecution(
        observer_enabled=enabled,
        elapsed_ns=elapsed,
        payload_bytes=128 if enabled else 0,
        observer_validation=validation() if enabled else None,
        shortcut_diagnostics=None,
    )


def record(
    *,
    arm: ObserverArm,
    seed: int,
    repeat: int,
    ratio_numerator: int,
) -> TimingPairRecord:
    return TimingPairRecord(
        phase=TimingPhase.MEASURED,
        lane="cpu",
        arm=arm,
        model_seed=seed,
        batch_index=0,
        repeat_index=repeat,
        order=execution_order_for(
            arm=arm,
            model_seed=seed,
            batch_index=0,
            repeat_index=repeat,
        ),
        reference=execution(False, 100),
        candidate=execution(True, ratio_numerator),
    )


def test_execution_order_uses_registered_parity_rule() -> None:
    assert execution_order_for(
        arm=ObserverArm.FIXEDPRED,
        model_seed=0,
        batch_index=0,
        repeat_index=0,
    ) is ExecutionOrder.OFF_THEN_ON
    assert execution_order_for(
        arm=ObserverArm.JOINT_VJP,
        model_seed=0,
        batch_index=0,
        repeat_index=0,
    ) is ExecutionOrder.ON_THEN_OFF
    assert execution_order_for(
        arm=ObserverArm.FIXEDPRED,
        model_seed=1,
        batch_index=0,
        repeat_index=0,
    ) is ExecutionOrder.ON_THEN_OFF


def test_benchmark_schema_freezes_counts_and_ids() -> None:
    schema = benchmark_schema_manifest(
        execution_scope="confirmatory",
        top_level_layers=6,
        model_seeds=[0, 1, 2],
        batches_per_seed=10,
        timing_repeats=3,
        warmup_pairs=3,
        rss_sampler_interval_ms=1.0,
    )
    assert schema["benchmark_schema_id"] == BENCHMARK_SCHEMA_ID
    assert schema["execution_scope"] == "confirmatory"
    assert schema["expected_measured_timing_pairs_per_lane"] == 180
    assert schema["expected_memory_pairs_per_lane"] == 60
    assert schema["observer_schema"]["expected_records_per_arm_run"] == 12


def test_run_timing_pair_preserves_observer_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from torch2pc_thesis import pc_methods

    def fake_backward_for_method(
        model: nn.Module,
        loss_fn: nn.Module,
        inputs: torch.Tensor,
        targets: torch.Tensor,
        **_kwargs: object,
    ) -> None:
        model(inputs)
        model(inputs)
        loss_fn(model(inputs), targets).backward()

    monkeypatch.setattr(pc_methods, "backward_for_method", fake_backward_for_method)
    torch.manual_seed(4)
    model = nn.Sequential(
        nn.Linear(4, 5),
        nn.Tanh(),
        nn.Linear(5, 3),
    ).to(dtype=torch.float64)
    inputs = torch.randn(3, 4, dtype=torch.float64)
    targets = torch.tensor([0, 1, 2])

    result = run_timing_pair(
        model,
        inputs,
        targets,
        phase=TimingPhase.MEASURED,
        lane="cpu",
        arm=ObserverArm.FIXEDPRED,
        model_seed=0,
        batch_index=0,
        repeat_index=0,
        torch2pc_dir=Path("external/Torch2PC"),
        device=torch.device("cpu"),
    )

    assert result.passed_structure is True
    assert result.reference.elapsed_ns > 0
    assert result.candidate.elapsed_ns > 0
    assert result.candidate.payload_bytes > 0
    assert result.candidate.observer_validation is not None
    assert result.candidate.observer_validation.observed_records == 6
    assert result.candidate.observer_validation.cleanup_complete is True


def test_runtime_aggregation_uses_seed_medians() -> None:
    records = [
        record(arm=arm, seed=seed, repeat=repeat, ratio_numerator=120)
        for arm in ObserverArm
        for seed in (0, 1, 2)
        for repeat in (0, 1, 2)
    ]
    summaries = aggregate_timing_records(records, model_seeds=[0, 1, 2])
    assert all(item.passed for item in summaries.values())
    assert summaries[ObserverArm.FIXEDPRED].primary_runtime_ratio == 1.2


def test_runtime_aggregation_rejects_seed_budget_exceedance() -> None:
    records = [
        record(
            arm=arm,
            seed=seed,
            repeat=repeat,
            ratio_numerator=140 if seed == 2 else 120,
        )
        for arm in ObserverArm
        for seed in (0, 1, 2)
        for repeat in (0, 1, 2)
    ]
    summaries = aggregate_timing_records(records, model_seeds=[0, 1, 2])
    assert summaries[ObserverArm.FIXEDPRED].primary_budget_passed is True
    assert summaries[ObserverArm.FIXEDPRED].seed_budget_passed is False
    assert summaries[ObserverArm.FIXEDPRED].passed is False
