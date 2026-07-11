from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import torch
import torch.nn as nn


def load_pc_infer(torch2pc_dir: str | Path) -> Callable[..., Any]:
    path = Path(torch2pc_dir).resolve()
    if not (path / "TorchSeq2PC.py").exists():
        raise FileNotFoundError(f"Torch2PC checkout is missing: {path}")
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
    from TorchSeq2PC import PCInfer  # type: ignore[import-not-found]

    return cast(Callable[..., Any], PCInfer)


def backward_for_method(
    model: nn.Module,
    loss_fn: nn.Module,
    inputs: torch.Tensor,
    targets: torch.Tensor,
    *,
    method: str,
    torch2pc_dir: str | Path,
    eta: float | None = None,
    inference_steps: int | None = None,
) -> torch.Tensor:
    normalized = method.lower()
    if normalized == "bp":
        loss = loss_fn(model(inputs), targets)
        loss.backward()
        return loss

    mapping = {
        "exact": "Exact",
        "fixedpred": "FixedPred",
        "strict": "Strict",
    }
    try:
        torch2pc_method = mapping[normalized]
    except KeyError as exc:
        raise ValueError(f"Unknown training method: {method}") from exc

    pc_infer = load_pc_infer(torch2pc_dir)
    output = pc_infer(
        model,
        loss_fn,
        inputs,
        targets,
        torch2pc_method,
        eta=0.1 if eta is None else float(eta),
        n=20 if inference_steps is None else int(inference_steps),
    )
    if not isinstance(output, tuple | list) or len(output) < 2:
        raise RuntimeError("Torch2PC PCInfer returned an unexpected result structure")
    loss = output[1]
    if not torch.is_tensor(loss) or loss.ndim != 0:
        raise RuntimeError("Torch2PC PCInfer did not return a scalar tensor loss")
    return loss
