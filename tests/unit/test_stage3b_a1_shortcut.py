from __future__ import annotations

import copy
from unittest.mock import patch

import pytest
import torch
import torch.nn as nn

from torch2pc_thesis.stage3b_a1_shortcut import (
    JointVjpDiagnostics,
    reduced_shortcut_backward,
)


def _reference_backward(
    model: nn.Module,
    inputs: torch.Tensor,
    targets: torch.Tensor,
) -> dict[str, torch.Tensor]:
    model.zero_grad(set_to_none=True)
    nn.CrossEntropyLoss()(model(inputs), targets).backward()
    gradients: dict[str, torch.Tensor] = {}
    for name, parameter in model.named_parameters():
        if parameter.requires_grad and parameter.grad is not None:
            gradients[name] = parameter.grad.detach().clone()
    return gradients


def _shortcut_gradients(
    model: nn.Sequential,
    inputs: torch.Tensor,
    targets: torch.Tensor,
) -> tuple[dict[str, torch.Tensor], JointVjpDiagnostics]:
    _, diagnostics = reduced_shortcut_backward(
        model,
        nn.CrossEntropyLoss(),
        inputs,
        targets,
    )
    gradients: dict[str, torch.Tensor] = {}
    for name, parameter in model.named_parameters():
        if parameter.requires_grad and parameter.grad is not None:
            gradients[name] = parameter.grad.detach().clone()
    return gradients, diagnostics


def test_joint_vjp_shortcut_matches_backward() -> None:
    torch.manual_seed(11)
    base = nn.Sequential(
        nn.Linear(5, 7),
        nn.Tanh(),
        nn.Linear(7, 3),
    ).double()
    inputs = torch.randn(8, 5, dtype=torch.float64)
    targets = torch.randint(0, 3, (8,))

    reference_model = copy.deepcopy(base)
    shortcut_model = copy.deepcopy(base)
    reference = _reference_backward(reference_model, inputs, targets)
    shortcut, diagnostics = _shortcut_gradients(shortcut_model, inputs, targets)

    assert reference.keys() == shortcut.keys()
    for name in reference:
        torch.testing.assert_close(shortcut[name], reference[name], rtol=1e-12, atol=1e-12)

    assert diagnostics.top_level_layers == 3
    assert diagnostics.joint_vjp_calls == 3
    assert diagnostics.one_call_per_layer is True
    assert diagnostics.parameterized_layers == 2
    assert diagnostics.parameter_components == 4


def test_joint_vjp_shortcut_calls_autograd_grad_once_per_layer() -> None:
    torch.manual_seed(13)
    model = nn.Sequential(
        nn.Linear(4, 6),
        nn.Tanh(),
        nn.Linear(6, 3),
    ).double()
    inputs = torch.randn(5, 4, dtype=torch.float64)
    targets = torch.randint(0, 3, (5,))

    with patch("torch.autograd.grad", wraps=torch.autograd.grad) as grad_mock:
        _, diagnostics = reduced_shortcut_backward(
            model,
            nn.CrossEntropyLoss(),
            inputs,
            targets,
        )

    assert grad_mock.call_count == len(model)
    assert diagnostics.joint_vjp_calls == len(model)
    assert diagnostics.one_call_per_layer is True


def test_joint_vjp_shortcut_handles_parameterless_layer() -> None:
    class Flatten(nn.Module):
        def forward(self, value: torch.Tensor) -> torch.Tensor:
            return torch.flatten(value, 1)

    torch.manual_seed(7)
    base = nn.Sequential(
        nn.Conv2d(1, 2, 3),
        nn.Tanh(),
        Flatten(),
        nn.Linear(2 * 4 * 4, 4),
    ).double()
    inputs = torch.randn(3, 1, 6, 6, dtype=torch.float64)
    targets = torch.randint(0, 4, (3,))

    reference = _reference_backward(copy.deepcopy(base), inputs, targets)
    shortcut_model = copy.deepcopy(base)
    shortcut, diagnostics = _shortcut_gradients(shortcut_model, inputs, targets)

    for name in reference:
        torch.testing.assert_close(shortcut[name], reference[name], rtol=1e-11, atol=1e-12)
    assert diagnostics.top_level_layers == 4
    assert diagnostics.joint_vjp_calls == 4
    assert diagnostics.parameterized_layers == 2


def test_joint_vjp_shortcut_accumulates_shared_parameters() -> None:
    torch.manual_seed(5)
    shared = nn.Linear(4, 4)
    base = nn.Sequential(
        shared,
        nn.Tanh(),
        shared,
        nn.Linear(4, 2),
    ).double()
    inputs = torch.randn(6, 4, dtype=torch.float64)
    targets = torch.randint(0, 2, (6,))

    reference = _reference_backward(copy.deepcopy(base), inputs, targets)
    shortcut_model = copy.deepcopy(base)
    shortcut, diagnostics = _shortcut_gradients(shortcut_model, inputs, targets)

    assert reference.keys() == shortcut.keys()
    for name in reference:
        torch.testing.assert_close(shortcut[name], reference[name], rtol=1e-11, atol=1e-12)
    assert diagnostics.one_call_per_layer is True


def test_joint_vjp_shortcut_rejects_non_sequential_model() -> None:
    model = nn.Linear(3, 2)
    inputs = torch.randn(2, 3)
    targets = torch.tensor([0, 1])

    with pytest.raises(TypeError, match="top-level nn.Sequential"):
        reduced_shortcut_backward(
            model,  # type: ignore[arg-type]
            nn.CrossEntropyLoss(),
            inputs,
            targets,
        )


def test_joint_vjp_shortcut_rejects_non_scalar_loss() -> None:
    model = nn.Sequential(nn.Linear(3, 2))
    inputs = torch.randn(2, 3)
    targets = torch.tensor([0, 1])

    with pytest.raises(ValueError, match="scalar reduced loss"):
        reduced_shortcut_backward(
            model,
            nn.CrossEntropyLoss(reduction="none"),
            inputs,
            targets,
        )
