from __future__ import annotations

import copy
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import pytest
import torch
import torch.nn as nn

from torch2pc_thesis.stage3b_b1_isolated_vjp import load_b1_pc_infer
from torch2pc_thesis.stage3b_b2_composite_vjp import (
    load_b2_pc_infer,
    load_patched_reference,
)

ROOT = Path(__file__).resolve().parents[2]
TORCH2PC_DIR = ROOT / "external" / "Torch2PC"
EXPECTED_COMMIT = "b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4"


def _prepared_reference_available() -> bool:
    if not (TORCH2PC_DIR / ".git").exists():
        return False
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=TORCH2PC_DIR,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode == 0 and completed.stdout.strip() == EXPECTED_COMMIT


pytestmark = pytest.mark.skipif(
    not _prepared_reference_available(),
    reason="prepared external/Torch2PC checkout is unavailable",
)


def _model() -> nn.Sequential:
    return nn.Sequential(
        nn.Linear(4, 6),
        nn.Tanh(),
        nn.Linear(6, 5),
        nn.Tanh(),
        nn.Linear(5, 3),
    ).double()


def _assert_state_close(
    reference: list[torch.Tensor | None],
    candidate: list[torch.Tensor | None],
) -> None:
    assert len(reference) == len(candidate)
    for left, right in zip(reference, candidate, strict=True):
        if left is None or right is None:
            assert left is right
        else:
            torch.testing.assert_close(left, right, rtol=1e-10, atol=1e-12)


@pytest.mark.parametrize(
    ("method", "eta"),
    [("FixedPred", 0.1), ("Strict", 0.05)],
)
def test_b2_matches_patched_reference_and_admitted_b1(
    method: str,
    eta: float,
) -> None:
    torch.manual_seed(23)
    reference_model = _model()
    b1_model = copy.deepcopy(reference_model)
    b2_model = copy.deepcopy(reference_model)
    inputs = torch.randn(8, 4, dtype=torch.float64)
    targets = torch.randint(0, 3, (8,))
    loss_fn = nn.CrossEntropyLoss()

    reference_module = load_patched_reference(TORCH2PC_DIR)
    reference_infer = cast(
        Callable[..., tuple[Any, ...]],
        cast(Any, reference_module).PCInfer,
    )
    b1_infer = load_b1_pc_infer(TORCH2PC_DIR)
    b2_infer = load_b2_pc_infer(TORCH2PC_DIR)

    reference = reference_infer(
        reference_model,
        loss_fn,
        inputs,
        targets,
        method,
        eta=eta,
        n=3,
    )
    b1 = b1_infer(
        b1_model,
        loss_fn,
        inputs,
        targets,
        method,
        eta=eta,
        inference_steps=3,
    )
    b2 = b2_infer(
        b2_model,
        loss_fn,
        inputs,
        targets,
        method,
        eta=eta,
        inference_steps=3,
    )

    for candidate in (b1, b2):
        torch.testing.assert_close(reference[1], candidate[1], rtol=0.0, atol=0.0)
        torch.testing.assert_close(reference[2], candidate[2], rtol=0.0, atol=0.0)
        _assert_state_close(reference[0], candidate[0])
        _assert_state_close(reference[3], candidate[3])
        _assert_state_close(reference[4], candidate[4])

    _assert_state_close(b1[3], b2[3])
    _assert_state_close(b1[4], b2[4])

    for reference_parameter, b1_parameter, b2_parameter in zip(
        reference_model.parameters(),
        b1_model.parameters(),
        b2_model.parameters(),
        strict=True,
    ):
        assert reference_parameter.grad is not None
        assert b1_parameter.grad is not None
        assert b2_parameter.grad is not None
        torch.testing.assert_close(
            reference_parameter.grad,
            b1_parameter.grad,
            rtol=1e-10,
            atol=1e-12,
        )
        torch.testing.assert_close(
            reference_parameter.grad,
            b2_parameter.grad,
            rtol=1e-10,
            atol=1e-12,
        )
