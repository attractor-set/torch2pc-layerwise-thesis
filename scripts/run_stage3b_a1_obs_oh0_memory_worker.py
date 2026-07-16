#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any

import torch

from torch2pc_thesis.config import resolve_config
from torch2pc_thesis.data import build_dataloaders
from torch2pc_thesis.models import build_model
from torch2pc_thesis.reproducibility import configure_threads, set_global_seed
from torch2pc_thesis.stage3b_a1_controls import validate_execution_lane
from torch2pc_thesis.stage3b_a1_obs_oh0_memory import (
    MemoryWorkerRequest,
    measure_memory_execution,
)


def git_output(path: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(path), *args],
        text=True,
    ).strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run one isolated OBS-OH0 memory execution."
    )
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def load_batch(
    config: dict[str, Any],
    *,
    model_seed: int,
    batch_index: int,
    device: torch.device,
    dtype: torch.dtype,
) -> tuple[torch.nn.Sequential, torch.Tensor, torch.Tensor]:
    set_global_seed(model_seed, warn_only=False)
    bundle = build_dataloaders(config, include_test=False, download=False)
    model = build_model("lenet_classic").to(device=device, dtype=dtype)
    for current_index, (inputs, targets) in enumerate(bundle.train):
        if current_index == batch_index:
            if not isinstance(model, torch.nn.Sequential):
                raise TypeError("OBS-OH0 requires a top-level nn.Sequential model")
            return (
                model,
                inputs.to(device=device, dtype=dtype),
                targets.to(device=device),
            )
    raise RuntimeError("The training loader produced too few OBS-OH0 batches")


def main() -> None:
    args = parse_args()
    request_data = json.loads(args.request.read_text(encoding="utf-8"))
    if not isinstance(request_data, dict):
        raise TypeError("OBS-OH0 memory request must be a JSON object")
    request = MemoryWorkerRequest.from_dict(request_data)

    controlled_container = os.environ.get("TORCH2PC_CONTROLLED_CONTAINER") == "1"
    execution_environment = validate_execution_lane(
        device=request.device,
        controlled_container=controlled_container,
        lane=os.environ.get("TORCH2PC_EXECUTION_LANE"),
        source_git_commit=os.environ.get("SOURCE_GIT_COMMIT"),
        hip_version=getattr(torch.version, "hip", None),
        cuda_available=torch.cuda.is_available(),
        torch_version=torch.__version__,
    )
    if execution_environment["lane"] != request.lane:
        raise RuntimeError("OBS-OH0 memory request lane differs from execution lane")
    if execution_environment["source_git_commit"] != request.source_git_commit:
        raise RuntimeError("OBS-OH0 memory request source commit mismatch")
    if os.environ.get("SOURCE_GIT_BRANCH") != request.source_git_branch:
        raise RuntimeError("OBS-OH0 memory request source branch mismatch")
    if os.environ.get("EXPERIMENT_IMAGE") != request.experiment_image:
        raise RuntimeError("OBS-OH0 memory request image mismatch")

    config: dict[str, Any] = resolve_config(
        "configs",
        stage="final_stage_2",
        method="exact",
    )
    config["runtime"]["device"] = request.device
    config["runtime"]["dtype"] = (
        "float64" if request.device == "cpu" else "float32"
    )
    device = torch.device("cpu" if request.device == "cpu" else "cuda")
    dtype = torch.float64 if request.device == "cpu" else torch.float32
    configure_threads(
        1
        if request.device == "cpu"
        else int(config["runtime"]["torch_threads"])
    )

    torch2pc_path = Path(config["torch2pc"]["local_path"])
    torch2pc_commit = str(config["torch2pc"]["commit"])
    if git_output(torch2pc_path, "rev-parse", "HEAD") != torch2pc_commit:
        raise RuntimeError("Torch2PC checkout differs from the pinned candidate commit")
    if git_output(torch2pc_path, "status", "--porcelain"):
        raise RuntimeError("Torch2PC worktree is dirty")

    model, inputs, targets = load_batch(
        config,
        model_seed=request.model_seed,
        batch_index=request.batch_index,
        device=device,
        dtype=dtype,
    )
    result = measure_memory_execution(
        model,
        inputs,
        targets,
        request=request,
        torch2pc_dir=torch2pc_path,
        device=device,
        dtype=dtype,
        device_name=(
            torch.cuda.get_device_name(0)
            if request.device == "gpu"
            else "cpu"
        ),
    )
    if not result.valid:
        raise RuntimeError("OBS-OH0 isolated memory result is invalid")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
