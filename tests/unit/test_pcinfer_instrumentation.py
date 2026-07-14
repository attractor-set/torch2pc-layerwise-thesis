from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

import pytest
import torch
from torch import Tensor, nn

from torch2pc_thesis.pcinfer_instrumentation import (
    instrument_pcinfer,
    supports_pcinfer_instrumentation,
)
from torch2pc_thesis.profiling import STAGE3_PROFILE_REGIONS, Stage3ProfilingError
from torch2pc_thesis.stage3b_b0_integration import (
    B0GateConfig,
    MethodName,
    run_b0_non_perturbation_gate,
    torch2pc_method_label,
)
from torch2pc_thesis.stage3b_profiling import Stage3BProfiler

_FAKE_TORCH2PC = r'''
import torch


def FwdPassPlus(model, LossFun, X, Y):
    depth_plus_one = len(model) + 1
    vhat = [None] * depth_plus_one
    vhat[0] = X
    for layer in range(1, depth_plus_one):
        vhat[layer] = model[layer - 1](vhat[layer - 1])
    loss = LossFun(vhat[-1], Y)
    dLdy = torch.autograd.grad(loss, vhat[-1])[0]
    return vhat, loss, dLdy


def FixedPredPCPredErrs(model, vhat, dLdy, eta=1, n=None):
    depth_plus_one = len(model) + 1
    if n is None:
        n = len(model)
    fixed = [activation.detach() for activation in vhat]
    linear_inputs = []
    linear_outputs = []
    for layer in range(depth_plus_one - 1):
        linear_input = fixed[layer].detach().requires_grad_(True)
        linear_inputs.append(linear_input)
        linear_outputs.append(model[layer](linear_input))
    epsilon = [None] * depth_plus_one
    epsilon[-1] = dLdy.detach()
    v = [activation.clone() for activation in fixed]
    for iteration in range(n):
        retain_graph = iteration < n - 1
        for layer in reversed(range(depth_plus_one - 1)):
            epsilon[layer] = fixed[layer] - v[layer]
            epsdfdv = torch.autograd.grad(
                linear_outputs[layer],
                linear_inputs[layer],
                grad_outputs=epsilon[layer + 1],
                retain_graph=retain_graph,
            )[0]
            v[layer] = v[layer] + eta * (epsilon[layer] - epsdfdv)
        for layer in range(1, depth_plus_one - 1):
            v[layer] = v[layer].detach()
            epsilon[layer] = epsilon[layer].detach()
    return v, epsilon


def StrictPCPredErrs(model, vinit, LossFun, Y, eta, n):
    depth_plus_one = len(model) + 1
    epsilon = [None] * depth_plus_one
    v = [activation.detach().clone() for activation in vinit]
    for _ in range(n):
        current_input = v[-2].detach().requires_grad_(True)
        current_output = model[-1](current_input)
        loss = LossFun(current_output, Y)
        epsilon[-1] = torch.autograd.grad(
            loss,
            current_output,
            retain_graph=True,
        )[0]
        for layer in reversed(range(1, depth_plus_one - 1)):
            epsdfdv = torch.autograd.grad(
                current_output,
                current_input,
                grad_outputs=epsilon[layer + 1],
                retain_graph=False,
            )[0]
            if layer == 1:
                lower_output = model[0](v[0])
                lower_input = None
            else:
                lower_input = v[layer - 1].detach().requires_grad_(True)
                lower_output = model[layer - 1](lower_input)
            epsilon[layer] = lower_output - v[layer]
            v[layer] = v[layer] + eta * (epsilon[layer] - epsdfdv)
            current_input = lower_input
            current_output = lower_output
        for layer in range(1, depth_plus_one - 1):
            v[layer] = v[layer].detach()
            epsilon[layer] = epsilon[layer].detach()
    return v, epsilon


def SetPCGrads(model, epsilon, X, v=None):
    depth_plus_one = len(model) + 1
    if v is None:
        v = [None] * depth_plus_one
        v[0] = X
        for layer in range(1, depth_plus_one):
            v[layer] = model[layer - 1](v[layer - 1])
    for layer in range(depth_plus_one - 1):
        parameters = tuple(model[layer].parameters())
        if not parameters:
            continue
        vtemp0 = v[layer].detach()
        vtemp1 = model[layer](vtemp0)
        gradients = torch.autograd.grad(
            vtemp1,
            parameters,
            grad_outputs=epsilon[layer + 1],
            allow_unused=True,
            retain_graph=False,
        )
        for parameter, gradient in zip(parameters, gradients):
            parameter.grad = gradient


def PCInfer(model, LossFun, X, Y, ErrType, eta=0.1, n=20, vinit=None):
    vhat, loss, dLdy = FwdPassPlus(model, LossFun, X, Y)
    if ErrType == "FixedPred":
        v, epsilon = FixedPredPCPredErrs(model, vhat, dLdy, eta, n)
        SetPCGrads(model, epsilon, X, vhat)
    elif ErrType == "Strict":
        if vinit is None:
            vinit = vhat
        v, epsilon = StrictPCPredErrs(model, vinit, LossFun, Y, eta, n)
        SetPCGrads(model, epsilon, X, v)
    else:
        raise ValueError("unsupported fake method")
    return vhat, loss, dLdy, v, epsilon
'''


def _fake_pc_infer() -> tuple[Callable[..., Any], dict[str, Any]]:
    namespace: dict[str, Any] = {}
    exec(_FAKE_TORCH2PC, namespace)
    return cast(Callable[..., Any], namespace["PCInfer"]), namespace


def _model() -> nn.Sequential:
    return nn.Sequential(
        nn.Linear(4, 6),
        nn.Tanh(),
        nn.Linear(6, 3),
    ).to(dtype=torch.float64)


def _batch() -> tuple[Tensor, Tensor]:
    torch.manual_seed(41)
    return (
        torch.randn(8, 4, dtype=torch.float64),
        torch.randint(0, 3, (8,)),
    )


def _optimizer_factory(model: nn.Module) -> torch.optim.Optimizer:
    return torch.optim.SGD(model.parameters(), lr=0.01)


def test_support_detection_rejects_ordinary_callable() -> None:
    assert supports_pcinfer_instrumentation(lambda: None) is False


def test_instrumentation_rejects_missing_namespace_boundaries() -> None:
    profiler = Stage3BProfiler(device="cpu", method="fixedpred")
    with pytest.raises(Stage3ProfilingError, match="missing"), instrument_pcinfer(
        lambda: None,
        profiler=profiler,
        configured_inference_steps=2,
    ):
        pass


@pytest.mark.parametrize(
    ("method", "label", "local_calls", "state_calls"),
    [
        ("fixedpred", "FixedPred", 6, 6),
        ("strict", "Strict", 4, 6),
    ],
)
def test_instrumentation_observes_boundaries_and_steps(
    method: str,
    label: str,
    local_calls: int,
    state_calls: int,
) -> None:
    pc_infer, namespace = _fake_pc_infer()
    originals = {
        name: namespace[name]
        for name in (
            "torch",
            "FwdPassPlus",
            "FixedPredPCPredErrs",
            "StrictPCPredErrs",
            "SetPCGrads",
        )
    }
    profiler = Stage3BProfiler(device="cpu", method=method)
    model = _model()
    inputs, targets = _batch()

    with instrument_pcinfer(
        pc_infer,
        profiler=profiler,
        configured_inference_steps=2,
    ) as observer:
        assert namespace["torch"] is not originals["torch"]
        pc_infer(
            model,
            nn.CrossEntropyLoss(),
            inputs,
            targets,
            label,
            eta=0.05,
            n=2,
        )

    summary = observer.summary()
    assert summary.actual_inference_steps == 2
    assert summary.initial_forward_autograd_calls == 1
    assert summary.state_autograd_calls == state_calls
    assert summary.local_state_vjp_calls == local_calls
    assert summary.parameter_vjp_calls == 2
    assert {record.region for record in profiler.records} == {
        "initial_forward",
        "state_inference",
        "local_state_vjp",
        "parameter_vjp",
    }
    assert sum(
        record.actual_inference_steps
        for record in profiler.records
        if record.region == "state_inference"
    ) == 2
    for name, original in originals.items():
        assert namespace[name] is original


def test_instrumentation_restores_namespace_after_failure() -> None:
    pc_infer, namespace = _fake_pc_infer()
    original_torch = namespace["torch"]
    original_state = namespace["FixedPredPCPredErrs"]
    profiler = Stage3BProfiler(device="cpu", method="fixedpred")
    model = _model()
    inputs, targets = _batch()

    with pytest.raises(Stage3ProfilingError, match="configured count"), instrument_pcinfer(
        pc_infer,
        profiler=profiler,
        configured_inference_steps=3,
    ):
        pc_infer(
            model,
            nn.CrossEntropyLoss(),
            inputs,
            targets,
            "FixedPred",
            eta=0.05,
            n=2,
        )

    assert namespace["torch"] is original_torch
    assert namespace["FixedPredPCPredErrs"] is original_state


@pytest.mark.parametrize(("method", "label"), [("fixedpred", "FixedPred"), ("strict", "Strict")])
def test_b0_gate_completes_internal_attribution(
    method: MethodName,
    label: str,
) -> None:
    pc_infer, _ = _fake_pc_infer()
    inputs, targets = _batch()
    report = run_b0_non_perturbation_gate(
        model=_model(),
        optimizer_factory=_optimizer_factory,
        loss_fn=nn.CrossEntropyLoss(),
        inputs=inputs,
        targets=targets,
        pc_infer=pc_infer,
        config=B0GateConfig(
            method=method,
            torch2pc_method=label,
            eta=0.05,
            inference_steps=2,
            device=torch.device("cpu"),
            dtype=torch.float64,
        ),
    )

    assert report.passed is True
    assert report.observed_inference_steps == 2
    assert report.actual_inference_step_count_observed is True
    assert report.internal_region_attribution_ready is True
    assert report.full_preregistered_gate_complete is True
    assert {
        record.region for record in report.region_measurements
    } == STAGE3_PROFILE_REGIONS
    record = report.to_record()
    assert record["measurement_scope"] == (
        "pcinfer_internal_regions_plus_optimizer_step"
    )
    assert record["evidence"] is False
    assert record["full_preregistered_gate_complete"] is True


def test_method_label_stays_consistent_with_instrumented_gate() -> None:
    assert torch2pc_method_label("fixedpred") == "FixedPred"
    assert torch2pc_method_label("strict") == "Strict"
