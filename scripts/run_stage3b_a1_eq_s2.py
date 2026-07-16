#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any

import pandas as pd
import torch

from torch2pc_thesis.config import resolve_config
from torch2pc_thesis.data import build_dataloaders
from torch2pc_thesis.models import build_model
from torch2pc_thesis.reproducibility import configure_threads, set_global_seed
from torch2pc_thesis.stage3b_a1_controls import (
    EquivalenceThresholds,
    validate_execution_lane,
)
from torch2pc_thesis.stage3b_a1_eq_s2 import evaluate_eq_s2


def git_output(path: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(path), *args],
        text=True,
    ).strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run Stage 3B EQ-S2: iterative FixedPred versus the opt-in "
            "joint-VJP reduced shortcut."
        )
    )
    parser.add_argument("device", choices=["cpu", "gpu"])
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(
            "results/stage-3/a1-shortcut-observer-controls/working/eq-s2"
        ),
    )
    parser.add_argument("--optimizer-lr", type=float, default=1e-3)
    parser.add_argument("--max-batches", type=int, default=1)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.optimizer_lr <= 0:
        raise ValueError("--optimizer-lr must be positive")
    if args.max_batches < 1:
        raise ValueError("--max-batches must be at least one")

    controlled_container = os.environ.get("TORCH2PC_CONTROLLED_CONTAINER") == "1"
    execution_lane = os.environ.get("TORCH2PC_EXECUTION_LANE")
    execution_environment = validate_execution_lane(
        device=args.device,
        controlled_container=controlled_container,
        lane=execution_lane,
        source_git_commit=os.environ.get("SOURCE_GIT_COMMIT"),
        hip_version=getattr(torch.version, "hip", None),
        cuda_available=torch.cuda.is_available(),
        torch_version=torch.__version__,
    )

    config: dict[str, Any] = resolve_config(
        "configs",
        stage="final_stage_2",
        method="exact",
    )
    config["runtime"]["device"] = args.device
    config["runtime"]["dtype"] = "float64" if args.device == "cpu" else "float32"

    device = torch.device("cpu" if args.device == "cpu" else "cuda")
    dtype = torch.float64 if args.device == "cpu" else torch.float32
    execution_environment["experiment_image"] = os.environ.get("EXPERIMENT_IMAGE")
    execution_environment["device_name"] = (
        torch.cuda.get_device_name(0) if args.device == "gpu" else "cpu"
    )

    configure_threads(
        1 if args.device == "cpu" else int(config["runtime"]["torch_threads"])
    )

    torch2pc_path = Path(config["torch2pc"]["local_path"])
    torch2pc_commit = str(config["torch2pc"]["commit"])
    if git_output(torch2pc_path, "rev-parse", "HEAD") != torch2pc_commit:
        raise RuntimeError("Torch2PC checkout differs from the pinned candidate commit")
    if git_output(torch2pc_path, "status", "--porcelain"):
        raise RuntimeError("Torch2PC worktree is dirty")

    thresholds_cfg = config["controls"]["thresholds"][args.device]
    thresholds = EquivalenceThresholds(
        min_cosine=float(thresholds_cfg["min_cosine"]),
        max_relative_l2=float(thresholds_cfg["max_relative_l2"]),
        zero_atol=1e-12 if args.device == "cpu" else 1e-7,
    )

    model_seeds = [int(value) for value in config["controls"]["model_seeds"]]
    records: list[pd.DataFrame] = []
    summaries: list[dict[str, Any]] = []

    for model_seed in model_seeds:
        set_global_seed(model_seed, warn_only=False)
        bundle = build_dataloaders(config, include_test=False, download=False)
        base_model = build_model("lenet_classic").to(device=device, dtype=dtype)
        processed = 0

        for batch_index, (inputs, targets) in enumerate(bundle.train):
            if processed >= args.max_batches:
                break

            result = evaluate_eq_s2(
                base_model,
                inputs.to(device=device, dtype=dtype),
                targets.to(device=device),
                torch2pc_dir=torch2pc_path,
                seed=model_seed,
                thresholds=thresholds,
                optimizer_factory=lambda parameters: torch.optim.SGD(
                    parameters,
                    lr=args.optimizer_lr,
                    momentum=0.0,
                ),
            )

            frame = result.records_frame()
            frame.insert(0, "batch_index", batch_index)
            frame.insert(0, "model_seed", model_seed)
            records.append(frame)

            run_summary = result.to_summary_dict()
            run_summary["batch_index"] = batch_index
            summaries.append(run_summary)
            processed += 1

        if processed != args.max_batches:
            raise RuntimeError("The training loader produced too few EQ-S2 batches")

    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    records_frame = pd.concat(records, ignore_index=True)

    summary = {
        "control_id": "EQ-S2",
        "scope": (
            "Iterative FixedPred with eta=1 and n=len(model) versus the "
            "opt-in one-joint-VJP-per-layer reduced shortcut"
        ),
        "reference_contract": {
            "method": "fixedpred",
            "eta": 1.0,
            "inference_steps": "len(model)",
            "initialization": "feed-forward",
            "iterative_loop_used": True,
        },
        "candidate_contract": {
            "top_level_model_type": "torch.nn.Sequential",
            "forward_graph_policy": "detached graph island per top-level layer",
            "reverse_policy": "one joint state-and-parameter VJP per layer",
            "loss_backward_used_by_candidate": False,
            "iterative_fixedpred_loop_used_by_candidate": False,
        },
        "observer_mode": "no_hooks",
        "device": args.device,
        "dtype": str(dtype),
        "torch2pc_commit": torch2pc_commit,
        "execution_environment": execution_environment,
        "optimizer": {
            "name": "SGD",
            "lr": args.optimizer_lr,
            "momentum": 0.0,
        },
        "thresholds": {
            "min_cosine": thresholds.min_cosine,
            "max_relative_l2": thresholds.max_relative_l2,
            "zero_atol": thresholds.zero_atol,
        },
        "model_seeds": model_seeds,
        "batches_per_seed": args.max_batches,
        "runs": summaries,
        "passed": all(bool(item["passed"]) for item in summaries),
        "claim_boundary": (
            "This gate concerns iterative-FixedPred/reduced-shortcut endpoint "
            "gradients and one stateless SGD step in the pinned environment. "
            "It does not establish hidden-state trajectory equivalence, full "
            "training-trajectory equivalence, runtime or memory benefit, or "
            "observer non-interference."
        ),
    }

    records_frame.to_csv(output_dir / "eq_s2_records.csv", index=False)
    (output_dir / "eq_s2_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if not summary["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
