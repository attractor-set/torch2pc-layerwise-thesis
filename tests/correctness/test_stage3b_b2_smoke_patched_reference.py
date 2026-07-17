from __future__ import annotations

import copy
import subprocess
from pathlib import Path
from typing import Any, cast

import pytest
import torch
import torch.nn as nn

from torch2pc_thesis.stage3b_b1_isolated_vjp import (
    PATCHED_TORCH2PC_COMMIT,
    B1ObserverMode,
    load_b1_pc_infer,
)
from torch2pc_thesis.stage3b_b2_composite_vjp import (
    B2CounterCollector,
    load_b2_pc_infer,
    load_patched_reference,
)

TORCH2PC_DIR = Path("external/Torch2PC")


def _prepared_checkout() -> bool:
    if not (TORCH2PC_DIR / "TorchSeq2PC.py").is_file():
        return False
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=TORCH2PC_DIR,
        check=False,
        capture_output=True,
        text=True,
    )
    return (
        completed.returncode == 0
        and completed.stdout.strip() == PATCHED_TORCH2PC_COMMIT
    )


pytestmark = pytest.mark.skipif(
    not _prepared_checkout(),
    reason="prepared external/Torch2PC checkout is unavailable",
)


def _model() -> nn.Sequential:
    return nn.Sequential(
        nn.Linear(4, 5),
        nn.Tanh(),
        nn.Linear(5, 3),
    ).double()


def _clone_state(value: object) -> tuple[torch.Tensor | None, ...]:
    if not isinstance(value, list):
        raise AssertionError("expected Torch2PC list state")
    result: list[torch.Tensor | None] = []
    for item in value:
        if item is None:
            result.append(None)
        elif torch.is_tensor(item):
            result.append(cast(torch.Tensor, item).detach().clone())
        else:
            raise AssertionError("expected optional tensor state component")
    return tuple(result)


def _tensor_output(output: object) -> tuple[torch.Tensor | None, ...]:
    if not isinstance(output, tuple) or len(output) != 5:
        raise AssertionError("unexpected PCInfer output")
    vhat, loss, dldy, beliefs, epsilon = output
    assert torch.is_tensor(loss)
    assert torch.is_tensor(dldy)
    return (
        *_clone_state(vhat),
        cast(torch.Tensor, loss).detach().clone(),
        cast(torch.Tensor, dldy).detach().clone(),
        *_clone_state(beliefs),
        *_clone_state(epsilon),
    )


def _gradient_map(model: nn.Module) -> dict[str, torch.Tensor | None]:
    return {
        name: None if parameter.grad is None else parameter.grad.detach().clone()
        for name, parameter in model.named_parameters()
    }


def _assert_tensor_sequence_close(
    left: tuple[torch.Tensor | None, ...],
    right: tuple[torch.Tensor | None, ...],
) -> None:
    assert len(left) == len(right)
    for lhs, rhs in zip(left, right, strict=True):
        assert (lhs is None) == (rhs is None)
        if lhs is not None and rhs is not None:
            torch.testing.assert_close(lhs, rhs, rtol=1e-7, atol=1e-9)


def _assert_gradient_maps_close(
    left: dict[str, torch.Tensor | None],
    right: dict[str, torch.Tensor | None],
) -> None:
    assert left.keys() == right.keys()
    for name in left:
        lhs = left[name]
        rhs = right[name]
        assert (lhs is None) == (rhs is None)
        if lhs is not None and rhs is not None:
            torch.testing.assert_close(lhs, rhs, rtol=1e-7, atol=1e-9)


@pytest.mark.parametrize(
    ("method", "eta", "inference_steps"),
    [
        ("FixedPred", 0.1, 3),
        ("Strict", 0.05, 3),
    ],
)
def test_b2_smoke_triple_matches_patched_reference_and_b1(
    method: str,
    eta: float,
    inference_steps: int,
) -> None:
    torch.manual_seed(41)
    base = _model()
    inputs = torch.randn(8, 4, dtype=torch.float64)
    targets = torch.randint(0, 3, (8,))
    loss_fn = nn.CrossEntropyLoss()

    reference = load_patched_reference(TORCH2PC_DIR)
    reference_infer = cast(Any, reference).PCInfer
    b1_infer = load_b1_pc_infer(TORCH2PC_DIR)
    b2_infer = load_b2_pc_infer(TORCH2PC_DIR)

    reference_model = copy.deepcopy(base)
    b1_model = copy.deepcopy(base)
    b2_model = copy.deepcopy(base)

    reference_output = reference_infer(
        reference_model,
        loss_fn,
        inputs,
        targets,
        method,
        eta=eta,
        n=inference_steps,
    )
    b1_output = b1_infer(
        b1_model,
        loss_fn,
        inputs,
        targets,
        method,
        eta=eta,
        inference_steps=inference_steps,
        observer_mode=B1ObserverMode.NO_HOOKS,
    )
    collector = B2CounterCollector()
    b2_output = b2_infer(
        b2_model,
        loss_fn,
        inputs,
        targets,
        method,
        eta=eta,
        inference_steps=inference_steps,
        observer_mode=B1ObserverMode.COUNTERS_ONLY,
        event_sink=collector,
    )

    reference_tensors = _tensor_output(reference_output)
    b1_tensors = _tensor_output(b1_output)
    b2_tensors = _tensor_output(b2_output)
    _assert_tensor_sequence_close(reference_tensors, b2_tensors)
    _assert_tensor_sequence_close(b1_tensors, b2_tensors)
    _assert_gradient_maps_close(
        _gradient_map(reference_model),
        _gradient_map(b2_model),
    )
    _assert_gradient_maps_close(_gradient_map(b1_model), _gradient_map(b2_model))

    assert len(collector.events) == inference_steps
    assert all(event.candidate_id == "composite_vjp" for event in collector.events)
    assert all(event.composite_vjp_call_count == 1 for event in collector.events)
