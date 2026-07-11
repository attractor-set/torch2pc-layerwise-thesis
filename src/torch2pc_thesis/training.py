from __future__ import annotations

import copy
import time
from pathlib import Path
from typing import Any

import numpy as np
import numpy.typing as npt
import pandas as pd
import torch
import torch.nn as nn

from torch2pc_thesis.data import build_dataloaders
from torch2pc_thesis.manifests import write_json
from torch2pc_thesis.metrics import (
    ensure_finite_parameters,
    ensure_finite_tensor,
    evaluate_classifier,
    gradient_diagnostics,
)
from torch2pc_thesis.models import build_model, count_parameters
from torch2pc_thesis.pc_methods import backward_for_method
from torch2pc_thesis.reproducibility import configure_threads, set_global_seed


def resolve_device(value: str) -> torch.device:
    normalized = value.lower()
    if normalized in {"gpu", "cuda", "rocm"}:
        if not torch.cuda.is_available():
            raise RuntimeError("GPU requested but PyTorch cannot access ROCm/CUDA")
        return torch.device("cuda")
    if normalized == "cpu":
        return torch.device("cpu")
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def resolve_dtype(value: str) -> torch.dtype:
    mapping = {"float32": torch.float32, "float64": torch.float64}
    try:
        return mapping[value]
    except KeyError as exc:
        raise ValueError(f"Unsupported dtype: {value}") from exc


def make_optimizer(model: nn.Module, config: dict[str, Any]) -> torch.optim.Optimizer:
    name = str(config["training"]["optimizer"]).lower()
    learning_rate = float(config["training"]["learning_rate"])
    if name == "adam":
        return torch.optim.Adam(model.parameters(), lr=learning_rate)
    if name == "sgd":
        return torch.optim.SGD(
            model.parameters(),
            lr=learning_rate,
            momentum=float(config["training"].get("momentum", 0.9)),
        )
    raise ValueError(f"Unknown optimizer: {name}")


def train_one_epoch(
    model: nn.Module,
    loader: Any,
    optimizer: torch.optim.Optimizer,
    config: dict[str, Any],
    device: torch.device,
    dtype: torch.dtype,
) -> dict[str, float]:
    model.train()
    method_cfg = config["method"]
    torch2pc_dir = config["torch2pc"]["local_path"]
    loss_fn = nn.CrossEntropyLoss()
    total_loss = 0.0
    total_samples = 0
    max_gradient_l2 = 0.0
    max_gradient_abs = 0.0
    start = time.perf_counter()

    for batch_index, (inputs, targets) in enumerate(loader):
        max_batches = config["training"].get("max_batches")
        if max_batches is not None and batch_index >= int(max_batches):
            break
        inputs = inputs.to(device=device, dtype=dtype)
        targets = targets.to(device=device)
        optimizer.zero_grad(set_to_none=True)

        loss = backward_for_method(
            model,
            loss_fn,
            inputs,
            targets,
            method=str(method_cfg["name"]),
            torch2pc_dir=torch2pc_dir,
            eta=method_cfg.get("eta"),
            inference_steps=method_cfg.get("inference_steps"),
        )
        ensure_finite_tensor("training_loss", loss)
        diagnostics = gradient_diagnostics(model)
        max_gradient_l2 = max(max_gradient_l2, diagnostics["gradient_l2"])
        max_gradient_abs = max(max_gradient_abs, diagnostics["gradient_max_abs"])
        optimizer.step()
        ensure_finite_parameters(model)

        batch_size = int(targets.shape[0])
        total_loss += float(loss.item()) * batch_size
        total_samples += batch_size

    if device.type == "cuda":
        torch.cuda.synchronize()
    if total_samples == 0:
        raise RuntimeError("Training loader produced no samples")
    return {
        "train_loss": total_loss / total_samples,
        "epoch_time_sec": time.perf_counter() - start,
        "train_samples": float(total_samples),
        "max_gradient_l2": max_gradient_l2,
        "max_gradient_abs": max_gradient_abs,
    }



def save_predictions(
    path: Path,
    evaluation: dict[str, Any],
    source_indices: npt.ArrayLike,
) -> None:
    y_true = np.asarray(evaluation["y_true"], dtype=np.int64)
    y_pred = np.asarray(evaluation["y_pred"], dtype=np.int64)
    probabilities = np.asarray(evaluation["probabilities"], dtype=np.float32)
    indices = np.asarray(source_indices, dtype=np.int64)
    if not (len(indices) == len(y_true) == len(y_pred) == len(probabilities)):
        raise RuntimeError("Prediction artifact length does not match source indices")
    np.savez_compressed(
        path,
        source_index=indices,
        y_true=y_true,
        y_pred=y_pred,
        probabilities=probabilities,
    )

def run_training(config: dict[str, Any], run_directory: str | Path) -> dict[str, Any]:
    run_dir = Path(run_directory)
    if not run_dir.is_dir():
        raise RuntimeError(f"Run directory must be prepared before training: {run_dir}")

    configure_threads(int(config["runtime"]["torch_threads"]))
    set_global_seed(
        int(config["reproducibility"]["model_seed"]),
        deterministic=bool(config["reproducibility"]["deterministic"]),
        warn_only=bool(config["reproducibility"].get("deterministic_warn_only", False)),
    )
    device = resolve_device(str(config["runtime"]["device"]))
    dtype = resolve_dtype(str(config["runtime"]["dtype"]))
    use_test = bool(config["evaluation"]["use_test"])
    bundle = build_dataloaders(config, include_test=use_test, download=False)
    model = build_model(
        str(config["model"]["architecture"]),
        int(config["model"]["num_classes"]),
    ).to(device=device, dtype=dtype)
    optimizer = make_optimizer(model, config)

    best_metric = float("-inf")
    best_epoch = -1
    best_state: dict[str, Any] | None = None
    patience = int(config["training"]["early_stopping_patience"])
    without_improvement = 0
    history: list[dict[str, float | int]] = []

    for epoch in range(1, int(config["training"]["epochs"]) + 1):
        training = train_one_epoch(model, bundle.train, optimizer, config, device, dtype)
        validation = evaluate_classifier(model, bundle.validation, device, dtype=dtype)
        row: dict[str, float | int] = {
            "epoch": epoch,
            **training,
            "validation_loss": float(validation["loss"]),
            "validation_accuracy": float(validation["accuracy"]),
            "validation_macro_f1": float(validation["macro_f1"]),
        }
        history.append(row)
        metric_name = str(config["training"]["primary_metric"])
        score = float(validation[metric_name])
        if score > best_metric + 1e-12:
            best_metric = score
            best_epoch = epoch
            best_state = copy.deepcopy(model.state_dict())
            without_improvement = 0
        else:
            without_improvement += 1
        if without_improvement >= patience:
            break

    if best_state is None:
        raise RuntimeError("No valid checkpoint was produced")

    model.load_state_dict(best_state)
    best_validation = evaluate_classifier(model, bundle.validation, device, dtype=dtype)
    save_predictions(
        run_dir / "validation_predictions.npz",
        best_validation,
        bundle.validation_indices,
    )
    checkpoint_path = run_dir / "checkpoint.pt"
    torch.save(
        {
            "state_dict": best_state,
            "best_epoch": best_epoch,
            "best_validation_metric": best_metric,
            "config": config,
        },
        checkpoint_path,
    )
    pd.DataFrame(history).to_csv(run_dir / "history.csv", index=False)

    metrics: dict[str, Any] = {
        "best_epoch": best_epoch,
        "epochs_completed": len(history),
        "model_parameter_count": count_parameters(model),
        "best_validation_metric": best_metric,
        "primary_metric": str(config["training"]["primary_metric"]),
        "test_evaluated": False,
        "total_training_time_sec": float(sum(float(row["epoch_time_sec"]) for row in history)),
        "split_files": [str(path) for path in bundle.split_files],
        "split_sha256": bundle.split_sha256,
    }
    if use_test:
        if bundle.test is None:
            raise RuntimeError("Test evaluation was requested but the test loader is absent")
        test = evaluate_classifier(model, bundle.test, device, dtype=dtype)
        if bundle.test_indices is None:
            raise RuntimeError("Test source indices are absent")
        save_predictions(run_dir / "test_predictions.npz", test, bundle.test_indices)
        metrics.update(
            {
                "test_evaluated": True,
                "test_loss": float(test["loss"]),
                "test_accuracy": float(test["accuracy"]),
                "test_macro_f1": float(test["macro_f1"]),
            }
        )

    write_json(metrics, run_dir / "metrics.json")
    return metrics
