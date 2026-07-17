from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
import torch
import torch.nn as nn

from torch2pc_thesis.stage3b_b1_equivalence import (
    THRESHOLD_PROFILES,
    compare_tensor_maps,
    flatten_trajectory,
)
from torch2pc_thesis.stage3b_b1_isolated_vjp import B1SweepSnapshot, pc_infer_b1
from torch2pc_thesis.stage3b_b1_reference_trace import reference_pc_infer_with_trace


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
    return SimpleNamespace(FwdPassPlus=_forward, SetPCGrads=_set_pc_grads)


@pytest.mark.parametrize(("method", "eta"), [("FixedPred", 0.1), ("Strict", 0.05)])
def test_reference_trace_matches_isolated_candidate(
    method: str,
    eta: float,
) -> None:
    torch.manual_seed(17)
    reference_model = _model()
    candidate_model = _model()
    candidate_model.load_state_dict(reference_model.state_dict())
    inputs = torch.randn(8, 4, dtype=torch.float64)
    targets = torch.randint(0, 3, (8,))
    loss_fn = nn.CrossEntropyLoss()
    reference_snapshots: list[B1SweepSnapshot] = []
    candidate_snapshots: list[B1SweepSnapshot] = []

    reference_pc_infer_with_trace(
        _reference(),
        reference_model,
        loss_fn,
        inputs,
        targets,
        method,
        eta=eta,
        inference_steps=3,
        trajectory_sink=reference_snapshots.append,
    )
    pc_infer_b1(
        _reference(),
        candidate_model,
        loss_fn,
        inputs,
        targets,
        method,
        eta=eta,
        inference_steps=3,
        trajectory_sink=candidate_snapshots.append,
    )

    metrics = compare_tensor_maps(
        flatten_trajectory(reference_snapshots),
        flatten_trajectory(candidate_snapshots),
        THRESHOLD_PROFILES["cpu_float64"],
    )
    assert metrics
    assert all(metric.passed for metric in metrics)
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
