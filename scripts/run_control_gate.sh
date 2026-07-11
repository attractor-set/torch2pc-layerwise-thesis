#!/usr/bin/env bash
set -euo pipefail
cd /workspace
device="${1:?cpu or gpu}"

python - "$device" <<'INNERPY'
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
import sys
import pandas as pd
import torch

from torch2pc_thesis.assets import verify_locked_prepared_assets
from torch2pc_thesis.config import resolve_config
from torch2pc_thesis.controls import (
    exact_vs_bp,
    fixedpred_vs_exact,
    structural_correction_check,
)
from torch2pc_thesis.data import build_dataloaders
from torch2pc_thesis.models import build_model
from torch2pc_thesis.reproducibility import configure_threads, set_global_seed

device_name = sys.argv[1]
config = resolve_config("configs", stage="correctness", method="exact")
config["runtime"]["device"] = device_name
config["runtime"]["dtype"] = "float64" if device_name == "cpu" else "float32"

device = torch.device("cpu" if device_name == "cpu" else "cuda")
dtype = torch.float64 if device_name == "cpu" else torch.float32
if device_name != "cpu" and not torch.cuda.is_available():
    raise RuntimeError("ROCm GPU is not visible")

configure_threads(1 if device_name == "cpu" else int(config["runtime"]["torch_threads"]))
expected_commit = str(config["torch2pc"].get("commit", ""))
if not re.fullmatch(r"[0-9a-f]{40}", expected_commit):
    raise RuntimeError("Pin a full Torch2PC commit before running controls")
actual_commit = subprocess.check_output(
    ["git", "-C", "external/Torch2PC", "rev-parse", "HEAD"], text=True
).strip()
if actual_commit != expected_commit:
    raise RuntimeError(
        f"Torch2PC checkout mismatch: expected {expected_commit}, found {actual_commit}"
    )
environment_lock_path = Path("results/summaries/environment-lock.json")
if not environment_lock_path.exists():
    raise RuntimeError("Environment lock is required before control execution")
environment_lock = json.loads(environment_lock_path.read_text(encoding="utf-8"))
if not isinstance(environment_lock, dict):
    raise RuntimeError("Environment lock must contain a JSON object")
environment_lock_sha256 = hashlib.sha256(environment_lock_path.read_bytes()).hexdigest()
source_commit = os.environ.get("SOURCE_GIT_COMMIT", "").strip()
if not re.fullmatch(r"[0-9a-f]{40}", source_commit):
    raise RuntimeError("Container does not expose a valid SOURCE_GIT_COMMIT")
if environment_lock.get("image_source_git_commit") != source_commit:
    raise RuntimeError("Container source commit differs from the environment lock")
if environment_lock.get("torch2pc_commit") != expected_commit:
    raise RuntimeError("Environment lock contains another Torch2PC commit")
verify_locked_prepared_assets(environment_lock, verify_hashes=True)
worktree_status = subprocess.check_output(
    ["git", "-C", "external/Torch2PC", "status", "--porcelain"], text=True
).strip()
if worktree_status:
    raise RuntimeError("Torch2PC worktree contains uncommitted changes")
source_check = structural_correction_check("external/Torch2PC/TorchSeq2PC.py")
control_cfg = config["controls"]
model_seeds = [int(value) for value in control_cfg["model_seeds"]]
control_batches = int(control_cfg["batches_per_seed"])
records_c0 = []
records_c1 = []

for model_seed in model_seeds:
    set_global_seed(model_seed, warn_only=False)
    bundle = build_dataloaders(config, include_test=False, download=False)
    batches = []
    for batch_index, (inputs, targets) in enumerate(bundle.train):
        if batch_index >= control_batches:
            break
        batches.append((batch_index, inputs, targets))
    if len(batches) != control_batches:
        raise RuntimeError(
            f"Requested {control_batches} control batches, observed {len(batches)}"
        )

    base_model = build_model("lenet_classic").to(device=device, dtype=dtype)
    for batch_index, inputs, targets in batches:
        inputs = inputs.to(device=device, dtype=dtype)
        targets = targets.to(device=device)
        c0 = exact_vs_bp(
            base_model,
            inputs,
            targets,
            torch2pc_dir="external/Torch2PC",
            seed=model_seed,
        )
        c0.insert(0, "batch_index", batch_index)
        c0.insert(0, "model_seed", model_seed)
        records_c0.append(c0)

        c1 = fixedpred_vs_exact(
            base_model,
            inputs,
            targets,
            torch2pc_dir="external/Torch2PC",
            seed=model_seed,
        )
        c1.insert(0, "batch_index", batch_index)
        c1.insert(0, "model_seed", model_seed)
        records_c1.append(c1)

c0_frame = pd.concat(records_c0, ignore_index=True)
c1_frame = pd.concat(records_c1, ignore_index=True)
thresholds = control_cfg["thresholds"][device_name]
summary = {
    "device": device_name,
    "torch2pc_commit": actual_commit,
    "source_git_commit_observed": source_commit,
    "environment_lock_sha256": environment_lock_sha256,
    "dtype": str(dtype),
    "model_seeds": model_seeds,
    "batches_per_seed": control_batches,
    "structural_source_check": source_check,
    "C0_exact_vs_bp": {
        "min_cosine": float(c0_frame["cosine"].min()),
        "max_relative_l2": float(c0_frame["relative_l2"].max()),
        "max_abs": float(c0_frame["max_abs"].max()),
    },
    "C1_fixedpred_vs_exact": {
        "min_cosine": float(c1_frame["cosine"].min()),
        "max_relative_l2": float(c1_frame["relative_l2"].max()),
        "max_abs": float(c1_frame["max_abs"].max()),
    },
    "thresholds": thresholds,
}
summary["gate_observed_within_thresholds"] = bool(
    source_check["all_observed"]
    and summary["C0_exact_vs_bp"]["min_cosine"] >= float(thresholds["min_cosine"])
    and summary["C0_exact_vs_bp"]["max_relative_l2"] <= float(thresholds["max_relative_l2"])
    and summary["C1_fixedpred_vs_exact"]["min_cosine"] >= float(thresholds["min_cosine"])
    and summary["C1_fixedpred_vs_exact"]["max_relative_l2"] <= float(thresholds["max_relative_l2"])
)
summary["interpretation"] = (
    "The observations satisfy the pre-specified numerical thresholds. "
    "This is an implementation control for the pinned environment, not a general proof."
    if summary["gate_observed_within_thresholds"]
    else
    "At least one observation falls outside the pre-specified thresholds. "
    "Pilot and final stages remain blocked pending investigation."
)

output = Path(f"results/summaries/control_gate_{device_name}.json")
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
c0_frame.to_csv(f"results/summaries/C0_exact_vs_bp_{device_name}.csv", index=False)
c1_frame.to_csv(f"results/summaries/C1_fixedpred_vs_exact_{device_name}.csv", index=False)
print(json.dumps(summary, ensure_ascii=False, indent=2))
if not summary["gate_observed_within_thresholds"]:
    raise SystemExit(1)
INNERPY
