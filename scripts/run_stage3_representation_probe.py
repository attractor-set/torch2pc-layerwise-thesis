#!/usr/bin/env python3
"""Run validation-only layer-wise CKA/RSA probes for aligned checkpoints."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
import yaml

from torch2pc_thesis.data import build_dataloaders
from torch2pc_thesis.layerwise import (
    capture_activations,
    corresponding_representation_metrics,
    cross_layer_cka,
)
from torch2pc_thesis.models import build_model
from torch2pc_thesis.reproducibility import configure_threads, set_global_seed
from torch2pc_thesis.training import resolve_device, resolve_dtype


def parse_checkpoint(value: str) -> tuple[str, Path]:
    label, separator, path = value.partition("=")
    if not separator or not label or not path:
        raise argparse.ArgumentTypeError("checkpoint must use LABEL=PATH")
    return label, Path(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", action="append", type=parse_checkpoint, required=True)
    parser.add_argument(
        "--probe-config",
        type=Path,
        default=Path("configs/stage3/layerwise_pilot.yaml"),
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", default=None)
    return parser.parse_args()


def load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected a YAML mapping in {path}")
    return payload


def load_checkpoint(path: Path) -> dict[str, Any]:
    payload = torch.load(path, map_location="cpu", weights_only=False)
    if not isinstance(payload, dict) or "state_dict" not in payload or "config" not in payload:
        raise ValueError(f"invalid checkpoint: {path}")
    return payload


def compatibility_signature(config: dict[str, Any]) -> tuple[Any, ...]:
    return (
        config["data"]["dataset"],
        config["model"]["architecture"],
        int(config["reproducibility"]["split_seed"]),
        int(config["reproducibility"]["model_seed"]),
        float(config["data"]["validation_fraction"]),
    )


def materialize_validation_inputs(
    config: dict[str, Any],
    *,
    max_samples: int,
) -> tuple[list[torch.Tensor], list[int]]:
    probe_config = copy.deepcopy(config)
    probe_config.setdefault("evaluation", {})["use_test"] = False
    probe_config["runtime"]["loader_workers"] = 0
    bundle = build_dataloaders(probe_config, include_test=False, download=False)

    batches: list[torch.Tensor] = []
    source_indices: list[int] = []
    cursor = 0
    for inputs, _targets in bundle.validation:
        remaining = max_samples - len(source_indices)
        if remaining <= 0:
            break
        selected = inputs[:remaining].detach().cpu().clone()
        selected_count = int(selected.shape[0])
        batches.append(selected)
        source_indices.extend(
            int(value) for value in bundle.validation_indices[cursor : cursor + selected_count]
        )
        cursor += int(inputs.shape[0])
    if len(source_indices) != max_samples:
        raise RuntimeError(f"requested {max_samples} samples, collected {len(source_indices)}")
    return batches, source_indices


def source_index_hash(indices: list[int]) -> str:
    payload = ",".join(str(value) for value in indices).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def main() -> None:
    args = parse_args()
    probe = load_yaml(args.probe_config)
    representation_config = probe["representations"]
    checkpoints = dict(args.checkpoint)
    if len(checkpoints) != len(args.checkpoint):
        raise ValueError("checkpoint labels must be unique")

    reference_label = str(representation_config["reference_label"])
    if reference_label not in checkpoints:
        raise ValueError(f"reference checkpoint label {reference_label!r} is missing")

    loaded = {label: load_checkpoint(path) for label, path in checkpoints.items()}
    reference_config = copy.deepcopy(loaded[reference_label]["config"])
    reference_signature = compatibility_signature(reference_config)
    for label, payload in loaded.items():
        signature = compatibility_signature(payload["config"])
        if signature != reference_signature:
            raise ValueError(
                f"checkpoint {label!r} is incompatible with the reference: "
                f"{signature} != {reference_signature}"
            )

    if args.device is not None:
        reference_config["runtime"]["device"] = args.device
    device = resolve_device(str(reference_config["runtime"]["device"]))
    dtype = resolve_dtype(str(reference_config["runtime"]["dtype"]))
    configure_threads(int(reference_config["runtime"]["torch_threads"]))
    set_global_seed(
        int(reference_config["reproducibility"]["model_seed"]),
        deterministic=bool(reference_config["reproducibility"]["deterministic"]),
        warn_only=bool(
            reference_config["reproducibility"].get("deterministic_warn_only", False)
        ),
    )

    max_samples = int(representation_config["validation_samples"])
    layer_names = [str(name) for name in representation_config["layer_names"]]
    batches, source_indices = materialize_validation_inputs(
        reference_config,
        max_samples=max_samples,
    )

    args.output.mkdir(parents=True, exist_ok=True)
    activations: dict[str, dict[str, np.ndarray]] = {}
    for label, payload in loaded.items():
        config = payload["config"]
        model = build_model(
            str(config["model"]["architecture"]),
            int(config["model"]["num_classes"]),
        )
        model.load_state_dict(payload["state_dict"], strict=True)
        model.to(device=device, dtype=dtype)
        activations[label] = capture_activations(
            model,
            batches,
            layer_names=layer_names,
            device=device,
            dtype=dtype,
            max_samples=max_samples,
        )
        np.savez_compressed(
            args.output / f"activations_{label}.npz",
            **{f"layer_{name}": values for name, values in activations[label].items()},
        )

    reference = activations[reference_label]
    metric_rows: list[dict[str, Any]] = []
    cross_rows: list[dict[str, Any]] = []
    for label, candidate in activations.items():
        if label == reference_label:
            continue
        metrics = corresponding_representation_metrics(reference, candidate)
        for layer_name, values in metrics.items():
            metric_rows.append(
                {
                    "reference_label": reference_label,
                    "candidate_label": label,
                    "layer": layer_name,
                    **values.to_dict(),
                }
            )
        if bool(representation_config["compute_cross_layer_cka"]):
            for (reference_layer, candidate_layer), value in cross_layer_cka(
                reference,
                candidate,
            ).items():
                cross_rows.append(
                    {
                        "reference_label": reference_label,
                        "candidate_label": label,
                        "reference_layer": reference_layer,
                        "candidate_layer": candidate_layer,
                        "cka": value,
                    }
                )

    pd.DataFrame(metric_rows).to_csv(args.output / "representation_metrics.csv", index=False)
    pd.DataFrame(cross_rows).to_csv(args.output / "cross_layer_cka.csv", index=False)

    metadata = {
        "schema_version": 1,
        "probe_type": "representations",
        "reference_label": reference_label,
        "checkpoints": {label: str(path.resolve()) for label, path in checkpoints.items()},
        "dataset": reference_config["data"]["dataset"],
        "model": reference_config["model"]["architecture"],
        "model_seed": int(reference_config["reproducibility"]["model_seed"]),
        "device": str(device),
        "dtype": str(dtype),
        "layers": layer_names,
        "validation_samples": len(source_indices),
        "validation_source_indices_sha256": source_index_hash(source_indices),
        "test_loader_created": False,
        "timing_results_valid": False,
    }
    (args.output / "metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
