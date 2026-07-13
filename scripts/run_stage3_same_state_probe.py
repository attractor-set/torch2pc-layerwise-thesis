#!/usr/bin/env python3
"""Run a validation-only same-state layer-wise gradient probe."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd
import torch
import yaml

from torch2pc_thesis.data import build_dataloaders
from torch2pc_thesis.layerwise import (
    collect_gradient_vectors,
    compare_gradient_maps,
)
from torch2pc_thesis.models import build_model
from torch2pc_thesis.pc_methods import backward_for_method
from torch2pc_thesis.reproducibility import configure_threads, set_global_seed
from torch2pc_thesis.training import resolve_device, resolve_dtype


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument(
        "--probe-config",
        type=Path,
        default=Path("configs/stage3/layerwise_pilot.yaml"),
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--checkpoint-label", default="final")
    parser.add_argument("--device", default=None)
    parser.add_argument("--enforce-exact-control", action="store_true")
    return parser.parse_args()


def load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected a YAML mapping in {path}")
    return payload


def load_checkpoint(path: Path) -> dict[str, Any]:
    payload = torch.load(path, map_location="cpu", weights_only=False)
    if not isinstance(payload, dict):
        raise ValueError("checkpoint must be a dictionary")
    if "state_dict" not in payload or "config" not in payload:
        raise ValueError("checkpoint must contain state_dict and config")
    return payload


def materialize_validation_batches(
    config: dict[str, Any],
    *,
    count: int,
) -> tuple[list[tuple[torch.Tensor, torch.Tensor]], list[int]]:
    probe_config = copy.deepcopy(config)
    probe_config.setdefault("evaluation", {})["use_test"] = False
    probe_config["runtime"]["loader_workers"] = 0
    bundle = build_dataloaders(probe_config, include_test=False, download=False)

    batches: list[tuple[torch.Tensor, torch.Tensor]] = []
    source_indices: list[int] = []
    cursor = 0
    for batch_index, (inputs, targets) in enumerate(bundle.validation):
        if batch_index >= count:
            break
        batch_size = int(inputs.shape[0])
        batches.append((inputs.detach().cpu().clone(), targets.detach().cpu().clone()))
        selected_indices = bundle.validation_indices[cursor : cursor + batch_size]
        source_indices.extend(int(value) for value in selected_indices)
        cursor += batch_size
    if len(batches) != count:
        raise RuntimeError(f"requested {count} validation batches, collected {len(batches)}")
    return batches, source_indices


def source_index_hash(indices: list[int]) -> str:
    payload = ",".join(str(value) for value in indices).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_probe_model(
    config: dict[str, Any],
    state_dict: dict[str, torch.Tensor],
    *,
    device: torch.device,
    dtype: torch.dtype,
) -> torch.nn.Module:
    model = build_model(
        str(config["model"]["architecture"]),
        int(config["model"]["num_classes"]),
    )
    model.load_state_dict(state_dict, strict=True)
    model.to(device=device, dtype=dtype)
    model.eval()
    return model


def run_method(
    *,
    config: dict[str, Any],
    state_dict: dict[str, torch.Tensor],
    method: dict[str, Any],
    inputs: torch.Tensor,
    targets: torch.Tensor,
    device: torch.device,
    dtype: torch.dtype,
) -> tuple[float, dict[str, dict[str, torch.Tensor]]]:
    model = build_probe_model(config, state_dict, device=device, dtype=dtype)
    model.zero_grad(set_to_none=True)
    loss_fn = torch.nn.CrossEntropyLoss()
    loss = backward_for_method(
        model=model,
        loss_fn=loss_fn,
        inputs=inputs.to(device=device, dtype=dtype),
        targets=targets.to(device=device),
        method=str(method["name"]),
        torch2pc_dir=Path(config["torch2pc"]["local_path"]),
        eta=method.get("eta"),
        inference_steps=method.get("inference_steps"),
    )
    gradients = {
        scope: collect_gradient_vectors(model, scope=scope)
        for scope in ("top_level", "parameter")
    }
    return float(loss.detach().cpu().item()), gradients


def main() -> None:
    args = parse_args()
    probe = load_yaml(args.probe_config)
    checkpoint = load_checkpoint(args.checkpoint)
    config = copy.deepcopy(checkpoint["config"])
    state_dict = checkpoint["state_dict"]
    if not isinstance(config, dict) or not isinstance(state_dict, dict):
        raise ValueError("checkpoint config/state_dict have invalid types")

    same_state = probe["same_state"]
    methods = same_state["methods"]
    if not methods or methods[0]["name"] != "bp":
        raise ValueError("same_state.methods must start with BP as the reference")

    if args.device is not None:
        config["runtime"]["device"] = args.device
    device = resolve_device(str(config["runtime"]["device"]))
    dtype = resolve_dtype(str(config["runtime"]["dtype"]))
    configure_threads(int(config["runtime"]["torch_threads"]))
    set_global_seed(
        int(config["reproducibility"]["model_seed"]),
        deterministic=bool(config["reproducibility"]["deterministic"]),
        warn_only=bool(config["reproducibility"].get("deterministic_warn_only", False)),
    )

    batches, source_indices = materialize_validation_batches(
        config,
        count=int(same_state["validation_batches"]),
    )
    rows: list[dict[str, Any]] = []
    loss_rows: list[dict[str, Any]] = []

    for batch_id, (inputs, targets) in enumerate(batches):
        reference_loss, reference_gradients = run_method(
            config=config,
            state_dict=state_dict,
            method=methods[0],
            inputs=inputs,
            targets=targets,
            device=device,
            dtype=dtype,
        )
        loss_rows.append({"batch_id": batch_id, "method": "bp", "loss": reference_loss})

        for method in methods[1:]:
            method_name = str(method["name"])
            loss, candidate_gradients = run_method(
                config=config,
                state_dict=state_dict,
                method=method,
                inputs=inputs,
                targets=targets,
                device=device,
                dtype=dtype,
            )
            loss_rows.append({"batch_id": batch_id, "method": method_name, "loss": loss})
            for scope, reference_map in reference_gradients.items():
                comparisons = compare_gradient_maps(reference_map, candidate_gradients[scope])
                for unit, metrics in comparisons.items():
                    rows.append(
                        {
                            "dataset": config["data"]["dataset"],
                            "model": config["model"]["architecture"],
                            "model_seed": int(config["reproducibility"]["model_seed"]),
                            "checkpoint_label": args.checkpoint_label,
                            "batch_id": batch_id,
                            "method": method_name,
                            "scope": scope,
                            "unit": unit,
                            **metrics.to_dict(),
                        }
                    )

    args.output.mkdir(parents=True, exist_ok=True)
    metrics_frame = pd.DataFrame(rows)
    metrics_frame.to_csv(args.output / "gradient_metrics.csv", index=False)
    pd.DataFrame(loss_rows).to_csv(args.output / "method_losses.csv", index=False)

    summary_columns = [
        "cosine",
        "relative_l2",
        "norm_ratio",
        "reference_norm",
        "candidate_norm",
        "max_abs_difference",
        "sign_agreement",
    ]
    summary = (
        metrics_frame.groupby(
            ["dataset", "model", "model_seed", "checkpoint_label", "method", "scope", "unit"],
            as_index=False,
        )[summary_columns]
        .mean()
        .sort_values(["method", "scope", "unit"])
    )
    summary.to_csv(args.output / "gradient_summary.csv", index=False)

    exact_control = same_state["exact_control"]
    exact_rows = metrics_frame[
        (metrics_frame["method"] == "exact") & (metrics_frame["scope"] == "top_level")
    ]
    exact_passed = bool(
        not exact_rows.empty
        and exact_rows["cosine_defined"].all()
        and float(exact_rows["cosine"].min()) >= float(exact_control["min_cosine"])
        and float(exact_rows["relative_l2"].max()) <= float(exact_control["max_relative_l2"])
    )

    metadata = {
        "schema_version": 1,
        "probe_type": "same_state_gradient",
        "checkpoint": str(args.checkpoint.resolve()),
        "checkpoint_label": args.checkpoint_label,
        "dataset": config["data"]["dataset"],
        "model": config["model"]["architecture"],
        "model_seed": int(config["reproducibility"]["model_seed"]),
        "device": str(device),
        "dtype": str(dtype),
        "validation_batches": len(batches),
        "validation_samples": len(source_indices),
        "validation_source_indices_sha256": source_index_hash(source_indices),
        "optimizer_step_applied": False,
        "test_loader_created": False,
        "exact_control": {
            "passed": exact_passed,
            "min_cosine": float(exact_control["min_cosine"]),
            "max_relative_l2": float(exact_control["max_relative_l2"]),
        },
    }
    (args.output / "metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    if args.enforce_exact_control and not exact_passed:
        raise SystemExit("Exact-vs-BP numerical control failed; inspect gradient_metrics.csv")


if __name__ == "__main__":
    main()
