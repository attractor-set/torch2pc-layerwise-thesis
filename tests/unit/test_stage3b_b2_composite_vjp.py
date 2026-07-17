from __future__ import annotations

import copy
from types import SimpleNamespace
from typing import Any

import pytest
import torch
import torch.nn as nn

from torch2pc_thesis.stage3b_b1_isolated_vjp import (
    B1ObserverMode,
    B1SweepSnapshot,
)
from torch2pc_thesis.stage3b_b2_composite_vjp import (
    B2CounterCollector,
    composite_state_vjp,
    fixedpred_composite_errors,
    pc_infer_b2,
    strict_composite_errors,
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
        raise AssertionError("B2 delegated to a canonical state-inference helper")

    return SimpleNamespace(
        FwdPassPlus=_forward,
        SetPCGrads=_set_pc_grads,
        FixedPredPCPredErrs=forbidden,
        StrictPCPredErrs=forbidden,
    )


def _sequential_fixedpred_reference(
    model: nn.Sequential,
    vhat: list[torch.Tensor],
    dldy: torch.Tensor,
    *,
    eta: float,
    inference_steps: int,
) -> tuple[list[torch.Tensor | None], list[torch.Tensor | None]]:
    fixed = [value.detach() for value in vhat]
    beliefs: list[torch.Tensor | None] = [value.clone() for value in fixed]
    epsilon: list[torch.Tensor | None] = [None] * (len(model) + 1)
    epsilon[-1] = dldy.detach()
    for _ in range(inference_steps):
        for layer_index in reversed(range(len(model))):
            belief = beliefs[layer_index]
            upper_error = epsilon[layer_index + 1]
            assert belief is not None
            assert upper_error is not None
            epsilon[layer_index] = fixed[layer_index] - belief
            local_input = fixed[layer_index].detach().requires_grad_(True)
            local_output = model[layer_index](local_input)
            propagated = torch.autograd.grad(
                local_output,
                local_input,
                grad_outputs=upper_error,
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


def _sequential_strict_reference(
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
        output_input = penultimate.detach().requires_grad_(True)
        output = model[-1](output_input)
        loss = loss_fn(output, targets)
        epsilon[-1] = torch.autograd.grad(loss, output)[0].detach()
        for layer_index in reversed(range(1, len(model))):
            belief = beliefs[layer_index]
            upper_error = epsilon[layer_index + 1]
            lower_belief = beliefs[layer_index - 1]
            assert belief is not None
            assert upper_error is not None
            assert lower_belief is not None
            local_input = belief.detach().requires_grad_(True)
            local_output = model[layer_index](local_input)
            propagated = torch.autograd.grad(
                local_output,
                local_input,
                grad_outputs=upper_error,
            )[0]
            with torch.no_grad():
                lower_prediction = model[layer_index - 1](lower_belief)
            epsilon[layer_index] = lower_prediction - belief
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


def test_composite_state_vjp_matches_separate_edge_vjps() -> None:
    torch.manual_seed(3)
    layers = (
        nn.Sequential(nn.Linear(4, 5), nn.Tanh()).double(),
        nn.Sequential(nn.Linear(5, 3), nn.Sigmoid()).double(),
    )
    inputs = (
        torch.randn(7, 4, dtype=torch.float64),
        torch.randn(7, 5, dtype=torch.float64),
    )
    cotangents = (
        torch.randn(7, 5, dtype=torch.float64),
        torch.randn(7, 3, dtype=torch.float64),
    )

    expected: list[torch.Tensor] = []
    for layer, value, cotangent in zip(
        layers,
        inputs,
        cotangents,
        strict=True,
    ):
        local_input = value.detach().requires_grad_(True)
        expected.append(
            torch.autograd.grad(
                layer(local_input),
                local_input,
                grad_outputs=cotangent,
            )[0]
        )

    observed = composite_state_vjp(
        layers,
        inputs,
        cotangents,
        method="FixedPred",
        sweep_index=0,
        layer_indices=(0, 1),
    )

    for reference, candidate in zip(expected, observed, strict=True):
        torch.testing.assert_close(reference, candidate, rtol=0.0, atol=0.0)
    assert all(
        parameter.grad is None
        for layer in layers
        for parameter in layer.parameters()
    )


def test_composite_state_vjp_uses_one_autograd_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    torch.manual_seed(4)
    layers = (
        nn.Sequential(nn.Linear(4, 5), nn.Tanh()).double(),
        nn.Sequential(nn.Linear(5, 3), nn.Tanh()).double(),
    )
    layer_inputs = (
        torch.randn(6, 4, dtype=torch.float64),
        torch.randn(6, 5, dtype=torch.float64),
    )
    cotangents = (
        torch.randn(6, 5, dtype=torch.float64),
        torch.randn(6, 3, dtype=torch.float64),
    )
    original_grad = torch.autograd.grad
    call_count = 0

    def counting_grad(*args: Any, **kwargs: Any) -> Any:
        nonlocal call_count
        call_count += 1
        return original_grad(*args, **kwargs)

    monkeypatch.setattr(torch.autograd, "grad", counting_grad)

    observed = composite_state_vjp(
        layers,
        layer_inputs,
        cotangents,
        method="FixedPred",
        sweep_index=0,
        layer_indices=(0, 1),
    )

    assert len(observed) == 2
    assert call_count == 1


def test_composite_registration_fails_closed() -> None:
    layer = nn.Linear(2, 2).double()
    value = torch.randn(3, 2, dtype=torch.float64)
    cotangent = torch.randn(3, 2, dtype=torch.float64)

    with pytest.raises(ValueError, match="lengths"):
        composite_state_vjp(
            (layer,),
            (value,),
            (cotangent, cotangent),
            method="FixedPred",
            sweep_index=0,
            layer_indices=(0,),
        )
    with pytest.raises(ValueError, match="strictly increasing"):
        composite_state_vjp(
            (layer, layer),
            (value, value),
            (cotangent, cotangent),
            method="FixedPred",
            sweep_index=0,
            layer_indices=(1, 1),
        )
    with pytest.raises(ValueError, match="shape mismatch"):
        composite_state_vjp(
            (layer,),
            (value,),
            (torch.randn(3, 3, dtype=torch.float64),),
            method="FixedPred",
            sweep_index=0,
            layer_indices=(0,),
        )


def test_observer_modes_are_fail_closed() -> None:
    layer = nn.Linear(2, 2).double()
    value = torch.randn(3, 2, dtype=torch.float64)
    cotangent = torch.randn(3, 2, dtype=torch.float64)
    collector = B2CounterCollector()

    with pytest.raises(ValueError, match="no_hooks"):
        composite_state_vjp(
            (layer,),
            (value,),
            (cotangent,),
            method="FixedPred",
            sweep_index=0,
            layer_indices=(0,),
            event_sink=collector,
        )
    with pytest.raises(ValueError, match="requires"):
        composite_state_vjp(
            (layer,),
            (value,),
            (cotangent,),
            method="FixedPred",
            sweep_index=0,
            layer_indices=(0,),
            observer_mode=B1ObserverMode.COUNTERS_ONLY,
        )


@pytest.mark.parametrize("inference_steps", [1, 2, 3, 4])
def test_fixedpred_matches_sequential_reference_full_trajectory(
    inference_steps: int,
) -> None:
    torch.manual_seed(5)
    model = _model()
    inputs = torch.randn(8, 4, dtype=torch.float64)
    targets = torch.randint(0, 3, (8,))
    vhat, _, dldy = _forward(model, nn.CrossEntropyLoss(), inputs, targets)

    expected_beliefs, expected_errors = _sequential_fixedpred_reference(
        model,
        vhat,
        dldy,
        eta=0.1,
        inference_steps=inference_steps,
    )
    snapshots: list[B1SweepSnapshot] = []
    observed_beliefs, observed_errors = fixedpred_composite_errors(
        model,
        vhat,
        dldy,
        eta=0.1,
        inference_steps=inference_steps,
        trajectory_sink=snapshots.append,
    )

    _assert_state_equal(expected_beliefs, observed_beliefs)
    _assert_state_equal(expected_errors, observed_errors)
    assert [(snapshot.phase, snapshot.sweep_index) for snapshot in snapshots] == [
        ("initial", -1),
        *(
            ("after_sweep", sweep_index)
            for sweep_index in range(inference_steps)
        ),
    ]


@pytest.mark.parametrize("inference_steps", [1, 2, 3])
def test_strict_matches_sequential_reference_full_trajectory(
    inference_steps: int,
) -> None:
    torch.manual_seed(7)
    model = _model()
    inputs = torch.randn(8, 4, dtype=torch.float64)
    targets = torch.randint(0, 3, (8,))
    vhat, _, _ = _forward(model, nn.CrossEntropyLoss(), inputs, targets)

    expected_beliefs, expected_errors = _sequential_strict_reference(
        model,
        vhat,
        nn.CrossEntropyLoss(),
        targets,
        eta=0.05,
        inference_steps=inference_steps,
    )
    observed_beliefs, observed_errors = strict_composite_errors(
        model,
        vhat,
        nn.CrossEntropyLoss(),
        targets,
        eta=0.05,
        inference_steps=inference_steps,
    )

    _assert_state_equal(expected_beliefs, observed_beliefs)
    _assert_state_equal(expected_errors, observed_errors)


def test_fixedpred_emits_one_composite_event_per_sweep() -> None:
    torch.manual_seed(11)
    model = _model()
    inputs = torch.randn(4, 4, dtype=torch.float64)
    targets = torch.randint(0, 3, (4,))
    vhat, _, dldy = _forward(model, nn.CrossEntropyLoss(), inputs, targets)
    collector = B2CounterCollector()

    fixedpred_composite_errors(
        model,
        vhat,
        dldy,
        eta=0.1,
        inference_steps=2,
        observer_mode=B1ObserverMode.COUNTERS_ONLY,
        event_sink=collector,
    )

    assert len(collector.events) == 2
    assert collector.composite_vjp_call_count == 2
    assert collector.logical_edge_count == len(model) * 2
    assert collector.graph_module_sets == (tuple(range(len(model))),) * 2
    assert collector.graph_span == len(model)
    assert collector.graph_lifetimes == {"single_sweep_composite_vjp_call"}


def test_strict_emits_one_composite_event_per_sweep() -> None:
    torch.manual_seed(13)
    model = _model()
    inputs = torch.randn(4, 4, dtype=torch.float64)
    targets = torch.randint(0, 3, (4,))
    vhat, _, _ = _forward(model, nn.CrossEntropyLoss(), inputs, targets)
    collector = B2CounterCollector()

    strict_composite_errors(
        model,
        vhat,
        nn.CrossEntropyLoss(),
        targets,
        eta=0.05,
        inference_steps=3,
        observer_mode=B1ObserverMode.COUNTERS_ONLY,
        event_sink=collector,
    )

    expected_modules = tuple(range(1, len(model)))
    assert len(collector.events) == 3
    assert collector.composite_vjp_call_count == 3
    assert collector.logical_edge_count == (len(model) - 1) * 3
    assert collector.graph_module_sets == (expected_modules,) * 3
    assert collector.graph_span == len(model) - 1


@pytest.mark.parametrize(
    ("method", "eta"),
    [("FixedPred", 0.1), ("Strict", 0.05)],
)
def test_pc_infer_b2_preserves_parameter_vjp_boundary(
    method: str,
    eta: float,
) -> None:
    torch.manual_seed(17)
    reference_model = _model()
    candidate_model = copy.deepcopy(reference_model)
    inputs = torch.randn(8, 4, dtype=torch.float64)
    targets = torch.randint(0, 3, (8,))
    loss_fn = nn.CrossEntropyLoss()

    expected_vhat, expected_loss, expected_dldy = _forward(
        reference_model,
        loss_fn,
        inputs,
        targets,
    )
    if method == "FixedPred":
        expected_beliefs, expected_errors = _sequential_fixedpred_reference(
            reference_model,
            expected_vhat,
            expected_dldy,
            eta=eta,
            inference_steps=3,
        )
        _set_pc_grads(
            reference_model,
            expected_errors,
            inputs,
            expected_vhat,
        )
    else:
        expected_beliefs, expected_errors = _sequential_strict_reference(
            reference_model,
            expected_vhat,
            loss_fn,
            targets,
            eta=eta,
            inference_steps=3,
        )
        _set_pc_grads(
            reference_model,
            expected_errors,
            inputs,
            expected_beliefs,
        )

    observed = pc_infer_b2(
        _reference(),
        candidate_model,
        loss_fn,
        inputs,
        targets,
        method,
        eta=eta,
        inference_steps=3,
    )

    _assert_state_equal(expected_vhat, observed[0])
    torch.testing.assert_close(expected_loss, observed[1], rtol=0.0, atol=0.0)
    torch.testing.assert_close(expected_dldy, observed[2], rtol=0.0, atol=0.0)
    _assert_state_equal(expected_beliefs, observed[3])
    _assert_state_equal(expected_errors, observed[4])
    for reference_parameter, candidate_parameter in zip(
        reference_model.parameters(),
        candidate_model.parameters(),
        strict=True,
    ):
        assert reference_parameter.grad is not None
        assert candidate_parameter.grad is not None
        torch.testing.assert_close(
            reference_parameter.grad,
            candidate_parameter.grad,
            rtol=0.0,
            atol=0.0,
        )


def test_pc_infer_b2_rejects_unsupported_method() -> None:
    model = _model()
    inputs = torch.randn(4, 4, dtype=torch.float64)
    targets = torch.randint(0, 3, (4,))

    with pytest.raises(ValueError, match="only FixedPred and Strict"):
        pc_infer_b2(
            _reference(),
            model,
            nn.CrossEntropyLoss(),
            inputs,
            targets,
            "Exact",
        )
