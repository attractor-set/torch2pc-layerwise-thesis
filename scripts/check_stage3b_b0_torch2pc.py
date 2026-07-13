#!/usr/bin/env python3
"""Run the non-evidence real-Torch2PC Stage 3B B0 equivalence gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from copy import deepcopy
from pathlib import Path
from typing import Any, cast

import torch
from torch import Tensor, nn

from torch2pc_thesis.data import build_dataloaders
from torch2pc_thesis.models import build_model
from torch2pc_thesis.pc_methods import load_pc_infer
from torch2pc_thesis.reproducibility import configure_threads, set_global_seed
from torch2pc_thesis.stage3b_b0_integration import (
    B0GateConfig,
    MethodName,
    run_b0_non_perturbation_gate,
    torch2pc_method_label,
)
from torch2pc_thesis.training import make_optimizer, resolve_device, resolve_dtype

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = Path("/tmp/stage3b-b0-torch2pc-gate.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--batch-index", type=int, default=0)
    parser.add_argument("--device", choices=("cpu", "gpu", "cuda", "rocm"))
    parser.add_argument("--dtype", choices=("float32", "float64"))
    parser.add_argument("--torch2pc-dir", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _source_commit() -> str:
    explicit_commit = os.environ.get("TORCH2PC_SOURCE_COMMIT", "").strip()
    if explicit_commit:
        return explicit_commit

    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    resolved_commit = completed.stdout.strip()
    if completed.returncode == 0 and resolved_commit:
        return resolved_commit

    raise RuntimeError(
        "source commit is unavailable; pass TORCH2PC_SOURCE_COMMIT when "
        "running from an image without .git metadata"
    )


def _load_checkpoint(path: Path) -> tuple[dict[str, Tensor], dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(path)
    loaded = torch.load(path, map_location="cpu", weights_only=False)
    if not isinstance(loaded, dict):
        raise RuntimeError("checkpoint must contain a mapping")
    state = loaded.get("state_dict")
    config = loaded.get("config")
    if not isinstance(state, dict) or not state:
        raise RuntimeError("checkpoint has no non-empty state_dict")
    if not all(isinstance(name, str) and isinstance(value, Tensor) for name, value in state.items()):
        raise RuntimeError("checkpoint state_dict must map strings to tensors")
    if not isinstance(config, dict):
        raise RuntimeError("checkpoint has no resolved config mapping")
    return cast(dict[str, Tensor], state), cast(dict[str, Any], config)


def _validation_batch(loader: Any, batch_index: int) -> tuple[Tensor, Tensor]:
    if batch_index < 0:
        raise ValueError("batch_index must be non-negative")
    for index, batch in enumerate(loader):
        if index != batch_index:
            continue
        if not isinstance(batch, tuple | list) or len(batch) != 2:
            raise RuntimeError("validation loader returned an unexpected batch")
        inputs, targets = batch
        if not isinstance(inputs, Tensor) or not isinstance(targets, Tensor):
            raise RuntimeError("validation batch must contain tensors")
        return inputs, targets
    raise RuntimeError(f"validation loader has no batch_index={batch_index}")


def _validated_output_path(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    tmp_root = Path("/tmp").resolve()
    if resolved == tmp_root or tmp_root not in resolved.parents:
        raise ValueError("Stage 3B gate output must be a file under /tmp")
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved


def main() -> None:
    args = parse_args()
    checkpoint_path = args.checkpoint.expanduser().resolve()
    state_dict, checkpoint_config = _load_checkpoint(checkpoint_path)
    config = deepcopy(checkpoint_config)
    config.setdefault("evaluation", {})["use_test"] = False

    method_text = str(config["method"]["name"]).lower()
    if method_text not in {"fixedpred", "strict"}:
        raise RuntimeError("B0 gate requires a FixedPred or Strict checkpoint")
    method = cast(MethodName, method_text)

    runtime = config["runtime"]
    device = resolve_device(str(args.device or runtime["device"]))
    dtype = resolve_dtype(str(args.dtype or runtime["dtype"]))
    torch2pc_dir = Path(
        args.torch2pc_dir or config["torch2pc"]["local_path"]
    ).expanduser().resolve()

    configure_threads(int(runtime["torch_threads"]))
    set_global_seed(
        int(config["reproducibility"]["model_seed"]),
        deterministic=bool(config["reproducibility"]["deterministic"]),
        warn_only=bool(
            config["reproducibility"].get("deterministic_warn_only", False)
        ),
    )

    bundle = build_dataloaders(config, include_test=False, download=False)
    inputs, targets = _validation_batch(bundle.validation, args.batch_index)
    model = build_model(
        str(config["model"]["architecture"]),
        int(config["model"]["num_classes"]),
    ).to(device=device, dtype=dtype)
    model.load_state_dict(state_dict)

    def optimizer_factory(candidate: nn.Module) -> torch.optim.Optimizer:
        return make_optimizer(candidate, config)

    gate_config = B0GateConfig(
        method=method,
        torch2pc_method=torch2pc_method_label(method),
        eta=float(config["method"]["eta"]),
        inference_steps=int(config["method"]["inference_steps"]),
        device=device,
        dtype=dtype,
    )
    report = run_b0_non_perturbation_gate(
        model=model,
        optimizer_factory=optimizer_factory,
        loss_fn=nn.CrossEntropyLoss(),
        inputs=inputs,
        targets=targets,
        pc_infer=load_pc_infer(torch2pc_dir),
        config=gate_config,
    )

    payload = {
        **report.to_record(),
        "status": "partial_pass" if report.passed else "failed",
        "source_commit": _source_commit(),
        "checkpoint": {
            "path": str(checkpoint_path),
            "sha256": _sha256(checkpoint_path),
        },
        "torch2pc": {
            "path": str(torch2pc_dir),
            "commit": str(config["torch2pc"].get("commit", "")),
        },
        "validation": {
            "dataset": str(config["data"]["dataset"]),
            "architecture": str(config["model"]["architecture"]),
            "model_seed": int(config["reproducibility"]["model_seed"]),
            "batch_index": args.batch_index,
            "batch_size": int(targets.shape[0]),
            "test_loader_created": False,
            "test_evaluated": False,
        },
    }
    output = _validated_output_path(args.output)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
