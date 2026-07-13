#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

import pandas as pd
import torch
import yaml

from torch2pc_thesis.assets import verify_locked_prepared_assets
from torch2pc_thesis.config import resolve_config
from torch2pc_thesis.controls import (
    exact_vs_bp,
    fixedpred_vs_exact,
    implementation_state_comparison,
    structural_correction_check,
)
from torch2pc_thesis.data import build_dataloaders
from torch2pc_thesis.models import build_model
from torch2pc_thesis.reproducibility import configure_threads, set_global_seed


def git_output(path: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(path), *args], text=True).strip()


def method_parameters(name: str) -> tuple[float | None, int | None]:
    value = yaml.safe_load(Path(f"configs/methods/{name}.yaml").read_text(encoding="utf-8"))[
        "method"
    ]
    eta = None if value.get("eta") is None else float(value["eta"])
    steps = None if value.get("inference_steps") is None else int(value["inference_steps"])
    return eta, steps


def summarize(frame: pd.DataFrame) -> dict[str, float]:
    return {
        "min_cosine": float(frame["cosine"].min()),
        "max_relative_l2": float(frame["relative_l2"].max()),
        "max_abs": float(frame["max_abs"].max()),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("device", choices=["cpu", "gpu"])
    args = parser.parse_args()

    config = resolve_config("configs", stage="final_stage_2", method="exact")
    config["runtime"]["device"] = args.device
    config["runtime"]["dtype"] = "float64" if args.device == "cpu" else "float32"
    device = torch.device("cpu" if args.device == "cpu" else "cuda")
    dtype = torch.float64 if args.device == "cpu" else torch.float32
    if args.device == "gpu" and not torch.cuda.is_available():
        raise RuntimeError("ROCm GPU is not visible")
    configure_threads(1 if args.device == "cpu" else int(config["runtime"]["torch_threads"]))

    candidate_path = Path(config["torch2pc"]["local_path"])
    candidate_commit = str(config["torch2pc"]["commit"])
    reference_path = Path(config["comparison"]["original_torch2pc_path"])
    reference_commit = str(config["comparison"]["original_torch2pc_commit"])
    if git_output(candidate_path, "rev-parse", "HEAD") != candidate_commit:
        raise RuntimeError("Candidate Torch2PC checkout differs from the Stage 2 pin")
    if git_output(reference_path, "rev-parse", "HEAD") != reference_commit:
        raise RuntimeError("Reference Torch2PC checkout differs from the Stage 1 pin")
    if git_output(candidate_path, "status", "--porcelain"):
        raise RuntimeError("Candidate Torch2PC worktree is dirty")
    if git_output(reference_path, "status", "--porcelain"):
        raise RuntimeError("Reference Torch2PC worktree is dirty")

    lock_path = Path(config["protocol"]["environment_lock"])
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    lock_sha256 = hashlib.sha256(lock_path.read_bytes()).hexdigest()
    source_commit = os.environ.get("SOURCE_GIT_COMMIT", "").strip()
    if not re.fullmatch(r"[0-9a-f]{40}", source_commit):
        raise RuntimeError("Container does not expose a valid SOURCE_GIT_COMMIT")
    if lock.get("image_source_git_commit") != source_commit:
        raise RuntimeError("Container source commit differs from Stage 2 lock")
    if lock.get("torch2pc_commit") != candidate_commit:
        raise RuntimeError("Stage 2 lock contains another candidate commit")
    if lock.get("torch2pc_reference_commit") != reference_commit:
        raise RuntimeError("Stage 2 lock contains another reference commit")
    verify_locked_prepared_assets(lock, verify_hashes=True)

    control_cfg = config["controls"]
    model_seeds = [int(value) for value in control_cfg["model_seeds"]]
    control_batches = int(control_cfg["batches_per_seed"])
    cross_batches = int(control_cfg.get("stage2_cross_version_batches_per_seed", 1))
    if cross_batches < 1 or cross_batches > control_batches:
        raise RuntimeError("Invalid Stage 2 cross-version batch count")

    records_c0: list[pd.DataFrame] = []
    records_c1: list[pd.DataFrame] = []
    records_cross: list[pd.DataFrame] = []
    for model_seed in model_seeds:
        set_global_seed(model_seed, warn_only=False)
        bundle = build_dataloaders(config, include_test=False, download=False)
        batches = []
        for batch_index, (inputs, targets) in enumerate(bundle.train):
            if batch_index >= control_batches:
                break
            batches.append((batch_index, inputs, targets))
        if len(batches) != control_batches:
            raise RuntimeError("The control loader produced too few batches")

        base_model = build_model("lenet_classic").to(device=device, dtype=dtype)
        for batch_index, inputs, targets in batches:
            inputs = inputs.to(device=device, dtype=dtype)
            targets = targets.to(device=device)
            c0 = exact_vs_bp(
                base_model,
                inputs,
                targets,
                torch2pc_dir=candidate_path,
                seed=model_seed,
            )
            c0.insert(0, "batch_index", batch_index)
            c0.insert(0, "model_seed", model_seed)
            records_c0.append(c0)

            c1 = fixedpred_vs_exact(
                base_model,
                inputs,
                targets,
                torch2pc_dir=candidate_path,
                seed=model_seed,
            )
            c1.insert(0, "batch_index", batch_index)
            c1.insert(0, "model_seed", model_seed)
            records_c1.append(c1)

            if batch_index >= cross_batches:
                continue
            for method in ["exact", "fixedpred", "strict"]:
                eta, steps = method_parameters(method)
                comparison = implementation_state_comparison(
                    base_model,
                    inputs,
                    targets,
                    reference_torch2pc_dir=reference_path,
                    candidate_torch2pc_dir=candidate_path,
                    method=method,
                    seed=model_seed,
                    eta=eta,
                    inference_steps=steps,
                )
                comparison.insert(0, "batch_index", batch_index)
                comparison.insert(0, "model_seed", model_seed)
                records_cross.append(comparison)

    c0_frame = pd.concat(records_c0, ignore_index=True)
    c1_frame = pd.concat(records_c1, ignore_index=True)
    cross_frame = pd.concat(records_cross, ignore_index=True)
    thresholds = control_cfg["thresholds"][args.device]
    source_check = structural_correction_check(candidate_path / "TorchSeq2PC.py")
    cross_by_method = {
        method: summarize(group) for method, group in cross_frame.groupby("method", sort=True)
    }
    summary = {
        "device": args.device,
        "dtype": str(dtype),
        "source_git_commit_observed": source_commit,
        "environment_lock_sha256": lock_sha256,
        "torch2pc_commit": candidate_commit,
        "torch2pc_reference_commit": reference_commit,
        "model_seeds": model_seeds,
        "batches_per_seed": control_batches,
        "cross_version_batches_per_seed": cross_batches,
        "structural_source_check": source_check,
        "C0_exact_vs_bp": summarize(c0_frame),
        "C1_fixedpred_vs_exact": summarize(c1_frame),
        "C2_C3_original_vs_patched": cross_by_method,
        "thresholds": thresholds,
    }
    checks = [summary["C0_exact_vs_bp"], summary["C1_fixedpred_vs_exact"]]
    checks.extend(cross_by_method.values())
    summary["gate_observed_within_thresholds"] = bool(
        source_check["all_observed"]
        and all(
            item["min_cosine"] >= float(thresholds["min_cosine"])
            and item["max_relative_l2"] <= float(thresholds["max_relative_l2"])
            for item in checks
        )
    )
    summary["interpretation"] = (
        "Patched Torch2PC passed BP/Exact, FixedPred/Exact, and original/patched "
        "state-gradient equivalence controls for this pinned environment."
        if summary["gate_observed_within_thresholds"]
        else "At least one Stage 2 control is outside the pre-specified thresholds."
    )

    output_dir = Path(config["paths"]["summaries"])
    output_dir.mkdir(parents=True, exist_ok=True)
    c0_frame.to_csv(output_dir / f"C0_exact_vs_bp_{args.device}.csv", index=False)
    c1_frame.to_csv(output_dir / f"C1_fixedpred_vs_exact_{args.device}.csv", index=False)
    cross_frame.to_csv(output_dir / f"C2_C3_original_vs_patched_{args.device}.csv", index=False)
    gate_path = Path(config["protocol"][f"control_gate_{args.device}"])
    gate_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if not summary["gate_observed_within_thresholds"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
