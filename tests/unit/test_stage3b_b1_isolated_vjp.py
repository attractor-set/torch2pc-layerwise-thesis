from __future__ import annotations

import copy
from types import SimpleNamespace
from typing import Any

import pytest
import torch
import torch.nn as nn

from torch2pc_thesis.stage3b_b1_isolated_vjp import (
    B1CounterCollector,
    B1ObserverMode,
    B1SweepSnapshot,
    fixedpred_isolated_layer_errors,
    isolated_layer_vjp,
    pc_infer_b1,
    strict_isolated_layer_errors,
)


def _model() -> nn.Sequential:
    return nn.Sequential(
        nn.Linear(4, 6),
        nn.Tanh(),
        nn.Linear(6, 5),
        nn.Tanh(),
        nn.Linear(5, 3),
    ).double()


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
    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("B1 delegated to a canonical state-inference helper")

    return SimpleNamespace(
        FwdPassPlus=_forward,
        SetPCGrads=_set_pc_grads,
        FixedPredPCPredErrs=forbidden,
        StrictPCPredErrs=forbidden,
    )


def _patched_fixedpred_reference(
    model: nn.Sequential,
    vhat: list[torch.Tensor],
    dldy: torch.Tensor,
    *,
    eta: float,
    inference_steps: int,
) -> tuple[list[torch.Tensor | None], list[torch.Tensor | None]]:
    fixed = [value.detach() for value in vhat]
    local_inputs: list[torch.Tensor] = []
    local_outputs: list[torch.Tensor] = []
    for layer_index, layer in enumerate(model):
        local_input = fixed[layer_index].detach().requires_grad_(True)
        local_inputs.append(local_input)
        local_outputs.append(layer(local_input))
    beliefs: list[torch.Tensor | None] = [value.clone() for value in fixed]
    epsilon: list[torch.Tensor | None] = [None] * (len(model) + 1)
    epsilon[-1] = dldy.detach()
    for sweep_index in range(inference_steps):
        retain_graph = sweep_index < inference_steps - 1
        for layer_index in reversed(range(len(model))):
            belief = beliefs[layer_index]
            upper_error = epsilon[layer_index + 1]
            assert belief is not None
            assert upper_error is not None
            epsilon[layer_index] = fixed[layer_index] - belief
            propagated = torch.autograd.grad(
                local_outputs[layer_index],
                local_inputs[layer_index],
                grad_outputs=upper_error,
                retain_graph=retain_graph,
            )[0]
            local_error = epsilon[layer_index]
            assert local_error is not None
            beliefs[layer_index] = belief + eta * (local_error - propagated)
        for layer_index in range(1, len(beliefs) - 1):
            belief = beliefs[layer_index]
            error = epsilon[layer_index]
            assert belief is not None
            assert error is not None
            beliefs[layer_index] = belief.detach()
            epsilon[layer_index] = error.detach()
    return beliefs, epsilon


def _patched_strict_reference(
    model: nn.Sequential,
    vinit: list[torch.Tensor],
    loss_fn: nn.Module,
    targets: torch.Tensor,
    *,
    eta: float,
    inference_steps: int,
) -> tuple[list[torch.Tensor | None], list[torch.Tensor | None]]:
    beliefs: list[torch.Tensor | None] = [
        value.detach().clone() for value in vinit
    ]
    epsilon: list[torch.Tensor | None] = [None] * (len(model) + 1)
    for _ in range(inference_steps):
        penultimate = beliefs[-2]
        assert penultimate is not None
        current_input: torch.Tensor | None = penultimate.detach().requires_grad_(True)
        current_output = model[-1](current_input)
        loss = loss_fn(current_output, targets)
        epsilon[-1] = torch.autograd.grad(loss, current_output, retain_graph=True)[0]
        for layer_index in reversed(range(1, len(model))):
            upper_error = epsilon[layer_index + 1]
            assert current_input is not None
            assert upper_error is not None
            propagated = torch.autograd.grad(
                current_output,
                current_input,
                grad_outputs=upper_error,
                retain_graph=False,
            )[0]
            lower_belief = beliefs[layer_index - 1]
            belief = beliefs[layer_index]
            assert lower_belief is not None
            assert belief is not None
            if layer_index == 1:
                with torch.no_grad():
                    lower_output = model[0](lower_belief)
                lower_input = None
            else:
                lower_input = lower_belief.detach().requires_grad_(True)
                lower_output = model[layer_index - 1](lower_input)
            epsilon[layer_index] = lower_output - belief
            local_error = epsilon[layer_index]
            assert local_error is not None
            beliefs[layer_index] = belief + eta * (local_error - propagated)
            current_input = lower_input
            current_output = lower_output
        for layer_index in range(1, len(beliefs) - 1):
            belief = beliefs[layer_index]
            error = epsilon[layer_index]
            assert belief is not None
            assert error is not None
            beliefs[layer_index] = belief.detach()
            epsilon[layer_index] = error.detach()
    return beliefs, epsilon


def _assert_state_equal(
    left: list[torch.Tensor | None],
    right: list[torch.Tensor | None],
) -> None:
    assert len(left) == len(right)
    for reference, candidate in zip(left, right, strict=True):
        if reference is None or candidate is None:
            assert reference is candidate
        else:
            torch.testing.assert_close(reference, candidate, rtol=0.0, atol=0.0)


def test_isolated_layer_vjp_matches_functional_vjp_without_parameter_grads() -> None:
    torch.manual_seed(3)
    layer = nn.Sequential(nn.Linear(4, 5), nn.Tanh()).double()
    layer_input = torch.randn(7, 4, dtype=torch.float64)
    cotangent = torch.randn(7, 5, dtype=torch.float64)

    _, expected = torch.autograd.functional.vjp(layer, layer_input, cotangent)
    observed = isolated_layer_vjp(
        layer,
        layer_input,
        cotangent,
        method="FixedPred",
        sweep_index=0,
        layer_index=0,
    )

    torch.testing.assert_close(observed, expected, rtol=0.0, atol=0.0)
    assert all(parameter.grad is None for parameter in layer.parameters())


def test_observer_modes_enforce_no_hooks_and_counters_only() -> None:
    layer = nn.Linear(2, 2).double()
    layer_input = torch.randn(3, 2, dtype=torch.float64)
    cotangent = torch.randn(3, 2, dtype=torch.float64)
    collector = B1CounterCollector()

    with pytest.raises(ValueError, match="no_hooks"):
        isolated_layer_vjp(
            layer,
            layer_input,
            cotangent,
            method="FixedPred",
            sweep_index=0,
            layer_index=0,
            event_sink=collector,
        )
    with pytest.raises(ValueError, match="requires"):
        isolated_layer_vjp(
            layer,
            layer_input,
            cotangent,
            method="FixedPred",
            sweep_index=0,
            layer_index=0,
            observer_mode=B1ObserverMode.COUNTERS_ONLY,
        )


def test_fixedpred_matches_patched_reference_full_trajectory() -> None:
    torch.manual_seed(5)
    model = _model()
    inputs = torch.randn(8, 4, dtype=torch.float64)
    targets = torch.randint(0, 3, (8,))
    vhat, _, dldy = _forward(model, nn.CrossEntropyLoss(), inputs, targets)

    expected_beliefs, expected_errors = _patched_fixedpred_reference(
        model,
        vhat,
        dldy,
        eta=0.1,
        inference_steps=4,
    )
    snapshots: list[B1SweepSnapshot] = []
    observed_beliefs, observed_errors = fixedpred_isolated_layer_errors(
        model,
        vhat,
        dldy,
        eta=0.1,
        inference_steps=4,
        trajectory_sink=snapshots.append,
    )

    _assert_state_equal(expected_beliefs, observed_beliefs)
    _assert_state_equal(expected_errors, observed_errors)
    assert [(snapshot.phase, snapshot.sweep_index) for snapshot in snapshots] == [
        ("initial", -1),
        ("after_sweep", 0),
        ("after_sweep", 1),
        ("after_sweep", 2),
        ("after_sweep", 3),
    ]
    assert all(value is None for value in snapshots[0].state_corrections)
    assert all(
        any(value is not None for value in snapshot.state_corrections)
        for snapshot in snapshots[1:]
    )


def test_strict_matches_patched_reference_full_trajectory() -> None:
    torch.manual_seed(7)
    model = _model()
    inputs = torch.randn(8, 4, dtype=torch.float64)
    targets = torch.randint(0, 3, (8,))
    vhat, _, _ = _forward(model, nn.CrossEntropyLoss(), inputs, targets)

    expected_beliefs, expected_errors = _patched_strict_reference(
        model,
        vhat,
        nn.CrossEntropyLoss(),
        targets,
        eta=0.05,
        inference_steps=3,
    )
    observed_beliefs, observed_errors = strict_isolated_layer_errors(
        model,
        vhat,
        nn.CrossEntropyLoss(),
        targets,
        eta=0.05,
        inference_steps=3,
    )

    _assert_state_equal(expected_beliefs, observed_beliefs)
    _assert_state_equal(expected_errors, observed_errors)


@pytest.mark.parametrize(("method", "eta"), [("FixedPred", 0.1), ("Strict", 0.05)])
def test_pc_infer_b1_preserves_reference_parameter_vjp(
    method: str,
    eta: float,
) -> None:
    torch.manual_seed(11)
    model = _model()
    expected_model = copy.deepcopy(model)
    inputs = torch.randn(8, 4, dtype=torch.float64)
    targets = torch.randint(0, 3, (8,))
    loss_fn = nn.CrossEntropyLoss()
    reference = _reference()

    vhat, _, dldy = _forward(expected_model, loss_fn, inputs, targets)
    if method == "FixedPred":
        beliefs, epsilon = _patched_fixedpred_reference(
            expected_model,
            vhat,
            dldy,
            eta=eta,
            inference_steps=3,
        )
        _set_pc_grads(expected_model, epsilon, inputs, vhat)
    else:
        beliefs, epsilon = _patched_strict_reference(
            expected_model,
            vhat,
            loss_fn,
            targets,
            eta=eta,
            inference_steps=3,
        )
        _set_pc_grads(expected_model, epsilon, inputs, beliefs)

    pc_infer_b1(
        reference,
        model,
        loss_fn,
        inputs,
        targets,
        method,
        eta=eta,
        inference_steps=3,
    )

    for expected, observed in zip(
        expected_model.parameters(),
        model.parameters(),
        strict=True,
    ):
        assert expected.grad is not None
        assert observed.grad is not None
        torch.testing.assert_close(expected.grad, observed.grad, rtol=0.0, atol=0.0)


def test_counters_report_one_graph_island_per_logical_edge() -> None:
    torch.manual_seed(13)
    model = _model()
    inputs = torch.randn(4, 4, dtype=torch.float64)
    targets = torch.randint(0, 3, (4,))
    vhat, _, dldy = _forward(model, nn.CrossEntropyLoss(), inputs, targets)
    collector = B1CounterCollector()

    fixedpred_isolated_layer_errors(
        model,
        vhat,
        dldy,
        eta=0.1,
        inference_steps=2,
        observer_mode=B1ObserverMode.COUNTERS_ONLY,
        event_sink=collector,
    )

    expected_edges = len(model) * 2
    assert collector.logical_edge_count == expected_edges
    assert collector.state_vjp_call_count == expected_edges
    assert collector.graph_island_count == expected_edges
    assert collector.graph_span == 1
    assert collector.graph_lifetimes == {"single_vjp_call"}


def test_pc_infer_b1_rejects_exact_and_non_sequential_models() -> None:
    inputs = torch.randn(2, 4, dtype=torch.float64)
    targets = torch.randint(0, 3, (2,))
    with pytest.raises(ValueError, match="FixedPred and Strict"):
        pc_infer_b1(
            _reference(),
            _model(),
            nn.CrossEntropyLoss(),
            inputs,
            targets,
            "Exact",
        )
    with pytest.raises(TypeError, match="Sequential"):
        pc_infer_b1(
            _reference(),
            nn.Linear(4, 3).double(),
            nn.CrossEntropyLoss(),
            inputs,
            targets,
            "FixedPred",
        )
