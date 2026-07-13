from __future__ import annotations

from copy import deepcopy

import pytest
import torch
from torch import Tensor, nn

from torch2pc_thesis.profiling import ProfilingProtocol, Stage3ProfilingError
from torch2pc_thesis.stage3b_profiling import (
    NonPerturbationThresholds,
    ProfilingCounters,
    RegionMeasurement,
    Stage3BProfiler,
    assert_non_perturbing,
    compare_named_tensors,
    iter_protocol_steps,
    snapshot_named_tensors,
    thresholds_for_device,
    validate_profile_completeness,
)


def _record(*, repetition: int, step: int, region: str) -> RegionMeasurement:
    return RegionMeasurement(
        candidate_id="stage2_baseline",
        method="fixedpred",
        repetition=repetition,
        step=step,
        region=region,
        host_time_us=1.0,
        device_time_us=0.0,
        peak_allocated_bytes=0,
        peak_reserved_bytes=0,
        vjp_calls=0,
        synchronization_points=0,
        saved_tensor_bytes=0,
        actual_inference_steps=1,
        non_finite_events=0,
    )


def test_protocol_iterator_preserves_warmup_measurement_and_repetition_order() -> None:
    protocol = ProfilingProtocol(warmup_steps=2, measured_steps=3, repetitions=2)
    steps = list(iter_protocol_steps(protocol))

    assert len(steps) == 10
    assert [(step.repetition, step.kind, step.step) for step in steps[:5]] == [
        (0, "warmup", 0),
        (0, "warmup", 1),
        (0, "measured", 0),
        (0, "measured", 1),
        (0, "measured", 2),
    ]
    assert steps[-1].repetition == 1
    assert steps[-1].measured is True


def test_cpu_region_records_counters_without_device_timing() -> None:
    profiler = Stage3BProfiler(device="cpu", method="strict")

    with profiler.region("parameter_vjp", repetition=0, step=0) as counters:
        counters.vjp_calls = 2
        counters.saved_tensor_bytes = 128

    [record] = profiler.records
    assert record.method == "strict"
    assert record.host_time_us >= 0.0
    assert record.device_time_us == 0.0
    assert record.vjp_calls == 2
    assert record.saved_tensor_bytes == 128
    assert record.synchronization_points == 0


def test_warmup_region_is_not_persisted() -> None:
    profiler = Stage3BProfiler(device="cpu", method="fixedpred")

    with profiler.region(
        "state_inference", repetition=0, step=0, measured=False
    ) as counters:
        counters.actual_inference_steps = 1

    assert profiler.records == ()


def test_negative_counter_is_rejected_after_region_execution() -> None:
    profiler = Stage3BProfiler(device="cpu", method="fixedpred")

    with (
        pytest.raises(Stage3ProfilingError, match="vjp_calls"),
        profiler.region("parameter_vjp", repetition=0, step=0) as counters,
    ):
        counters.vjp_calls = -1


def test_profile_completeness_accepts_all_required_regions() -> None:
    protocol = ProfilingProtocol(warmup_steps=0, measured_steps=2, repetitions=1)
    records = [
        _record(repetition=0, step=step, region=region)
        for step in range(2)
        for region in (
            "initial_forward",
            "state_inference",
            "local_state_vjp",
            "parameter_vjp",
            "optimizer_step",
        )
    ]

    validate_profile_completeness(records, protocol)


def test_profile_completeness_rejects_missing_region() -> None:
    protocol = ProfilingProtocol(warmup_steps=0, measured_steps=1, repetitions=1)
    records = [
        _record(repetition=0, step=0, region="initial_forward"),
        _record(repetition=0, step=0, region="state_inference"),
    ]

    with pytest.raises(Stage3ProfilingError, match="missing"):
        validate_profile_completeness(records, protocol)


def test_thresholds_are_locked_to_preregistered_device_dtype_pairs() -> None:
    cpu = thresholds_for_device("cpu", torch.float64)
    assert cpu.min_cosine == pytest.approx(0.99999)
    assert cpu.max_relative_l2 == pytest.approx(1e-7)

    with pytest.raises(Stage3ProfilingError, match="frozen"):
        thresholds_for_device("cpu", torch.float32)


def test_tensor_comparison_handles_identical_zero_tensors() -> None:
    thresholds = NonPerturbationThresholds(min_cosine=0.99999, max_relative_l2=1e-7)
    comparisons = compare_named_tensors(
        {"zero": torch.zeros(3, dtype=torch.float64)},
        {"zero": torch.zeros(3, dtype=torch.float64)},
        thresholds=thresholds,
    )

    [comparison] = comparisons
    assert comparison.cosine == 1.0
    assert comparison.relative_l2 == 0.0
    assert comparison.passed is True


def test_non_perturbation_gate_reports_tensor_failure() -> None:
    thresholds = NonPerturbationThresholds(min_cosine=0.99999, max_relative_l2=1e-7)

    with pytest.raises(Stage3ProfilingError, match="non-perturbation gate failed"):
        assert_non_perturbing(
            {"value": torch.tensor([1.0, 0.0], dtype=torch.float64)},
            {"value": torch.tensor([0.0, 1.0], dtype=torch.float64)},
            thresholds=thresholds,
        )


def test_snapshot_is_detached_and_has_independent_storage() -> None:
    source = torch.tensor([1.0, 2.0], requires_grad=True)
    snapshot = snapshot_named_tensors({"source": source})

    source.data.add_(10.0)
    assert snapshot["source"].requires_grad is False
    assert snapshot["source"].tolist() == [1.0, 2.0]


def _run_linear_step(
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    inputs: Tensor,
    targets: Tensor,
    profiler: Stage3BProfiler | None,
) -> dict[str, Tensor]:
    optimizer.zero_grad(set_to_none=True)
    if profiler is None:
        predictions = model(inputs)
        loss = torch.mean((predictions - targets) ** 2)
        loss.backward()
        optimizer.step()
    else:
        with profiler.region("initial_forward", repetition=0, step=0):
            predictions = model(inputs)
        with profiler.region("state_inference", repetition=0, step=0) as counters:
            loss = torch.mean((predictions - targets) ** 2)
            counters.actual_inference_steps = 1
        with profiler.region("local_state_vjp", repetition=0, step=0):
            loss = loss + torch.zeros((), dtype=loss.dtype)
        with profiler.region("parameter_vjp", repetition=0, step=0) as counters:
            loss.backward()
            counters.vjp_calls = 1
        with profiler.region("optimizer_step", repetition=0, step=0):
            optimizer.step()

    values: dict[str, Tensor] = {}
    for name, parameter in model.named_parameters():
        values[f"parameter::{name}"] = parameter
        assert parameter.grad is not None
        values[f"gradient::{name}"] = parameter.grad
    return snapshot_named_tensors(values)


def test_instrumentation_preserves_cpu_float64_update() -> None:
    torch.manual_seed(19)
    inputs = torch.randn(8, 4, dtype=torch.float64)
    targets = torch.randn(8, 2, dtype=torch.float64)
    reference_model = nn.Linear(4, 2, dtype=torch.float64)
    instrumented_model = deepcopy(reference_model)
    reference_optimizer = torch.optim.SGD(reference_model.parameters(), lr=0.05)
    instrumented_optimizer = torch.optim.SGD(instrumented_model.parameters(), lr=0.05)

    reference = _run_linear_step(
        reference_model, reference_optimizer, inputs, targets, None
    )
    profiler = Stage3BProfiler(device="cpu", method="fixedpred")
    instrumented = _run_linear_step(
        instrumented_model,
        instrumented_optimizer,
        inputs,
        targets,
        profiler,
    )

    comparisons = assert_non_perturbing(
        reference,
        instrumented,
        thresholds=thresholds_for_device("cpu", torch.float64),
    )
    validate_profile_completeness(
        profiler.records,
        ProfilingProtocol(warmup_steps=0, measured_steps=1, repetitions=1),
    )
    assert all(comparison.passed for comparison in comparisons)


def test_counter_validation_rejects_negative_values() -> None:
    counters = ProfilingCounters(non_finite_events=-1)
    with pytest.raises(Stage3ProfilingError, match="non_finite_events"):
        counters.validate()
