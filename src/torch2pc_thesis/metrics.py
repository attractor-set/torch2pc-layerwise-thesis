from __future__ import annotations

from typing import Any

import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import accuracy_score, f1_score
from torch.utils.data import DataLoader


def ensure_finite_tensor(name: str, value: torch.Tensor) -> None:
    if not torch.isfinite(value).all():
        raise FloatingPointError(f"Non-finite values detected in {name}")


def ensure_finite_parameters(model: nn.Module) -> None:
    for name, parameter in model.named_parameters():
        ensure_finite_tensor(f"parameter:{name}", parameter.detach())


def gradient_diagnostics(model: nn.Module) -> dict[str, float]:
    squared_norm = 0.0
    max_abs = 0.0
    tensors = 0
    for name, parameter in model.named_parameters():
        if parameter.grad is None:
            continue
        ensure_finite_tensor(f"gradient:{name}", parameter.grad)
        gradient = parameter.grad.detach().float()
        squared_norm += float(torch.sum(gradient * gradient).item())
        max_abs = max(max_abs, float(torch.max(torch.abs(gradient)).item()))
        tensors += 1
    if tensors == 0:
        raise RuntimeError("No parameter gradients were produced")
    return {
        "gradient_l2": float(squared_norm**0.5),
        "gradient_max_abs": max_abs,
        "gradient_tensors": float(tensors),
    }


def evaluate_classifier(
    model: nn.Module,
    loader: DataLoader[Any],
    device: torch.device,
    *,
    dtype: torch.dtype,
) -> dict[str, Any]:
    model.eval()
    loss_fn = nn.CrossEntropyLoss(reduction="sum")
    total_loss = 0.0
    y_true: list[int] = []
    y_pred: list[int] = []
    probabilities: list[np.ndarray] = []

    with torch.no_grad():
        for inputs, targets in loader:
            inputs = inputs.to(device=device, dtype=dtype)
            targets = targets.to(device=device)
            logits = model(inputs)
            ensure_finite_tensor("evaluation_logits", logits)
            loss = loss_fn(logits, targets)
            total_loss += float(loss.item())
            probability = torch.softmax(logits, dim=1)
            predictions = probability.argmax(dim=1)
            y_true.extend(targets.cpu().tolist())
            y_pred.extend(predictions.cpu().tolist())
            probabilities.append(probability.cpu().numpy())

    if not y_true:
        raise RuntimeError("Evaluation loader produced no samples")
    return {
        "loss": total_loss / len(y_true),
        "accuracy": accuracy_score(y_true, y_pred),
        "macro_f1": f1_score(y_true, y_pred, average="macro"),
        "y_true": np.asarray(y_true),
        "y_pred": np.asarray(y_pred),
        "probabilities": np.concatenate(probabilities, axis=0),
    }
