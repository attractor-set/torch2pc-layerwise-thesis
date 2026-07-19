from __future__ import annotations

import importlib
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest
import torch
import torch.nn as nn

from torch2pc_thesis.stage3b_b0_integration import (
    B0GateConfig,
    run_b0_non_perturbation_gate,
)


def _model() -> nn.Sequential:
    return nn.Sequential(
        nn.Linear(4, 6),
        nn.Tanh(),
        nn.Linear(6, 3),
    ).double()


def _batch() -> tuple[torch.Tensor, torch.Tensor]:
    generator = torch.Generator(device="cpu")
    generator.manual_seed(17)
    return (
        torch.randn(5, 4, dtype=torch.float64, generator=generator),
        torch.randint(0, 3, (5,), generator=generator),
    )


def _forward(
    model: nn.Sequential,
    loss_fn: nn.Module,
    inputs: torch.Tensor,
    targets: torch.Tensor,
) -> tuple[list[torch.Tensor], torch.Tensor, torch.Tensor]:
    values = [inputs]
    for layer in model:
        values.append(layer(values[-1]))
    loss = loss_fn(values[-1], targets)
    dldy = torch.autograd.grad(loss, values[-1])[0]
    return values, loss, dldy


def _set_pc_grads(
    model: nn.Sequential,
    epsilon: list[torch.Tensor | None],
    inputs: torch.Tensor,
    beliefs: list[torch.Tensor | None] | None = None,
) -> None:
    values = beliefs
    if values is None:
        values = [inputs]
        for layer in model:
            previous = values[-1]
            assert previous is not None
            values.append(layer(previous))
    for layer_index, layer in enumerate(model):
        parameters = tuple(layer.parameters())
        if not parameters:
            continue
        layer_input = values[layer_index]
        upper_error = epsilon[layer_index + 1]
        assert layer_input is not None
        assert upper_error is not None
        output = layer(layer_input.detach())
        gradients = torch.autograd.grad(
            output,
            parameters,
            grad_outputs=upper_error,
            allow_unused=True,
        )
        for parameter, gradient in zip(parameters, gradients, strict=True):
            parameter.grad = gradient


def _reference() -> Any:
    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("candidate delegated to canonical state inference")

    return SimpleNamespace(
        FwdPassPlus=_forward,
        SetPCGrads=_set_pc_grads,
        FixedPredPCPredErrs=forbidden,
        StrictPCPredErrs=forbidden,
    )


@pytest.mark.parametrize(
    (
        "module_name",
        "loader_name",
        "candidate_id",
        "method",
        "expected_local_calls",
        "expected_state_calls",
    ),
    (
        (
            "torch2pc_thesis.stage3b_b1_isolated_vjp",
            "load_b1_pc_infer",
            "isolated_layer_vjp",
            "fixedpred",
            6,
            6,
        ),
        (
            "torch2pc_thesis.stage3b_b1_isolated_vjp",
            "load_b1_pc_infer",
            "isolated_layer_vjp",
            "strict",
            4,
            6,
        ),
        (
            "torch2pc_thesis.stage3b_b2_composite_vjp",
            "load_b2_pc_infer",
            "composite_vjp",
            "fixedpred",
            2,
            2,
        ),
        (
            "torch2pc_thesis.stage3b_b2_composite_vjp",
            "load_b2_pc_infer",
            "composite_vjp",
            "strict",
            2,
            4,
        ),
    ),
)
def test_native_candidate_gate_exposes_complete_regions(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    module_name: str,
    loader_name: str,
    candidate_id: str,
    method: str,
    expected_local_calls: int,
    expected_state_calls: int,
) -> None:
    module = importlib.import_module(module_name)
    monkeypatch.setattr(
        module,
        "load_patched_reference",
        lambda *_args, **_kwargs: _reference(),
    )
    adapter = getattr(module, loader_name)(tmp_path)
    inputs, targets = _batch()

    report = run_b0_non_perturbation_gate(
        model=_model(),
        optimizer_factory=lambda model: torch.optim.SGD(
            model.parameters(),
            lr=0.01,
        ),
        loss_fn=nn.CrossEntropyLoss(),
        inputs=inputs,
        targets=targets,
        pc_infer=adapter,
        config=B0GateConfig(
            method=method,
            torch2pc_method=("FixedPred" if method == "fixedpred" else "Strict"),
            eta=0.05,
            inference_steps=2,
            device=torch.device("cpu"),
            dtype=torch.float64,
        ),
    )

    assert cast(Any, adapter).__stage3b_candidate_id__ == candidate_id
    assert report.passed is True
    assert report.internal_region_attribution_ready is True
    assert report.actual_inference_step_count_observed is True
    assert report.full_preregistered_gate_complete is True
    assert report.structural_measurement_ready is True
    assert report.primary_measurement is not None
    assert report.structural_measurement is not None
    assert report.structural_measurement.event_count == expected_local_calls
    assert len(report.locality_events) == expected_local_calls
    assert report.completeness_failures == ()
    assert report.observed_inference_steps == 2
    assert report.instrumentation is not None
    assert report.instrumentation.actual_inference_steps == 2
    assert report.instrumentation.initial_forward_autograd_calls == 1
    assert report.instrumentation.local_state_vjp_calls == expected_local_calls
    assert report.instrumentation.state_autograd_calls == expected_state_calls
    assert report.instrumentation.parameter_vjp_calls == 1

    counts = Counter(record.region for record in report.region_measurements)
    assert counts == {
        "initial_forward": 1,
        "state_inference": 1,
        "local_state_vjp": expected_local_calls,
        "parameter_vjp": 1,
        "optimizer_step": 1,
    }
    assert {
        record.candidate_id
        for record in report.region_measurements
    } == {candidate_id}
    state_record = next(
        record
        for record in report.region_measurements
        if record.region == "state_inference"
    )
    assert state_record.actual_inference_steps == 2
    assert state_record.vjp_calls == expected_state_calls


def test_report_exposes_completeness_failure_reason() -> None:
    from torch2pc_thesis.pcinfer_instrumentation import (
        PCInferInstrumentationSummary,
    )
    from torch2pc_thesis.stage3b_b0_integration import (
        B0CompositeMeasurement,
        B0GateReport,
    )

    report = B0GateReport(
        method="fixedpred",
        configured_inference_steps=2,
        comparisons=(),
        measurement=B0CompositeMeasurement(
            host_time_us=0.0,
            device_time_us=0.0,
            peak_allocated_bytes=0,
            peak_reserved_bytes=0,
            synchronization_points=0,
        ),
        observed_inference_steps=1,
        instrumentation=PCInferInstrumentationSummary(
            actual_inference_steps=1,
            initial_forward_autograd_calls=1,
            state_autograd_calls=1,
            local_state_vjp_calls=1,
            parameter_vjp_calls=1,
        ),
    )

    assert report.completeness_failures == (
        "internal_region_attribution",
        "inference_step_observation",
    )
    assert report.to_record()["completeness_failures"] == [
        "internal_region_attribution",
        "inference_step_observation",
    ]
