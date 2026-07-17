from __future__ import annotations

import copy
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import pytest
import torch
import torch.nn as nn

from torch2pc_thesis.stage3b_b1_isolated_vjp import (
    PATCHED_TORCH2PC_COMMIT,
    load_b1_pc_infer,
    load_patched_reference,
)

TORCH2PC_DIR = Path("external/Torch2PC")


def _require_patched_checkout() -> None:
    if not (TORCH2PC_DIR / ".git").is_dir():
        pytest.skip("prepared external/Torch2PC checkout is unavailable")
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=TORCH2PC_DIR,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        pytest.skip("unable to resolve external/Torch2PC revision")
    observed = completed.stdout.strip()
    if observed != PATCHED_TORCH2PC_COMMIT:
        pytest.skip(
            "correctness test requires patched Torch2PC "
            f"{PATCHED_TORCH2PC_COMMIT}; observed {observed}"
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
    reference: Any,
    candidate: Any,
) -> None:
    assert isinstance(reference, list)
    assert isinstance(candidate, list)
    assert len(reference) == len(candidate)
    for left, right in zip(reference, candidate, strict=True):
        if left is None or right is None:
            assert left is right
            continue
        assert torch.is_tensor(left)
        assert torch.is_tensor(right)
        torch.testing.assert_close(left, right, rtol=1e-10, atol=1e-12)


@pytest.mark.correctness
@pytest.mark.parametrize(("method", "eta"), [("FixedPred", 0.1), ("Strict", 0.05)])
def test_b1_matches_actual_patched_torch2pc(
    method: str,
    eta: float,
) -> None:
    _require_patched_checkout()
    torch.manual_seed(20260716)
    base = _model()
    reference_model = copy.deepcopy(base)
    candidate_model = copy.deepcopy(base)
    inputs = torch.randn(8, 4, dtype=torch.float64)
    targets = torch.randint(0, 3, (8,))
    loss_fn = nn.CrossEntropyLoss()

    reference_module = load_patched_reference(TORCH2PC_DIR)
    reference_infer = cast(
        Callable[..., tuple[Any, ...]],
        cast(Any, reference_module).PCInfer,
    )
    candidate_infer = load_b1_pc_infer(TORCH2PC_DIR)

    reference = reference_infer(
        reference_model,
        loss_fn,
        inputs,
        targets,
        method,
        eta=eta,
        n=3,
    )
    candidate = candidate_infer(
        candidate_model,
        loss_fn,
        inputs,
        targets,
        method,
        eta=eta,
        inference_steps=3,
    )

    torch.testing.assert_close(reference[1], candidate[1], rtol=0.0, atol=0.0)
    torch.testing.assert_close(reference[2], candidate[2], rtol=0.0, atol=0.0)
    _assert_state_close(reference[0], candidate[0])
    _assert_state_close(reference[3], candidate[3])
    _assert_state_close(reference[4], candidate[4])

    for left, right in zip(
        reference_model.parameters(),
        candidate_model.parameters(),
        strict=True,
    ):
        assert left.grad is not None
        assert right.grad is not None
        torch.testing.assert_close(left.grad, right.grad, rtol=1e-10, atol=1e-12)
