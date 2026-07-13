#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from torch2pc_thesis.assets import verify_locked_prepared_assets
from torch2pc_thesis.config import resolve_config


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError(f"Required Stage 2 artifact is missing: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"Expected JSON object: {path}")
    return value


def git_output(path: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(path), *args], text=True
    ).strip()


def verify_runtime_worktree(registry: str, runs: str) -> None:
    raw = subprocess.check_output(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        text=True,
    )
    allowed_exact = {registry}
    allowed_prefixes = (f"{runs.rstrip('/')}/", "results/splits/")
    unexpected: list[str] = []
    for line in raw.splitlines():
        if len(line) < 4:
            continue
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if path in allowed_exact or path.startswith(allowed_prefixes):
            continue
        unexpected.append(line)
    if unexpected:
        raise RuntimeError(
            "Stage 2 found non-runtime worktree changes: " + "; ".join(unexpected)
        )


def main() -> None:
    config = resolve_config("configs", stage="final_stage_2", method="exact")
    lock_path = Path(config["protocol"]["environment_lock"])
    lock = load(lock_path)
    lock_sha = sha256(lock_path)
    source_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True
    ).strip()
    image_source_commit = str(lock.get("image_source_git_commit", ""))
    lock_source_commit = str(lock.get("source_git_commit_at_lock_creation", ""))
    if image_source_commit != lock_source_commit:
        raise RuntimeError("Stage 2 lock source and image revisions differ")
    try:
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", image_source_commit, source_commit],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            "Current branch is not descended from the locked execution commit"
        ) from exc

    candidate_path = Path(config["torch2pc"]["local_path"])
    candidate_commit = str(config["torch2pc"]["commit"])
    reference_path = Path(config["comparison"]["original_torch2pc_path"])
    reference_commit = str(config["comparison"]["original_torch2pc_commit"])
    if git_output(candidate_path, "rev-parse", "HEAD") != candidate_commit:
        raise RuntimeError("Candidate Torch2PC checkout differs from the pin")
    if git_output(reference_path, "rev-parse", "HEAD") != reference_commit:
        raise RuntimeError("Reference Torch2PC checkout differs from Stage 1")
    if git_output(candidate_path, "status", "--porcelain"):
        raise RuntimeError("Candidate Torch2PC worktree is dirty")
    if git_output(reference_path, "status", "--porcelain"):
        raise RuntimeError("Reference Torch2PC worktree is dirty")
    if lock.get("torch2pc_commit") != candidate_commit:
        raise RuntimeError("Stage 2 lock contains another candidate commit")
    if lock.get("torch2pc_reference_commit") != reference_commit:
        raise RuntimeError("Stage 2 lock contains another reference commit")

    verify_locked_prepared_assets(lock, verify_hashes=True)
    for group in ["config_files", "source_files"]:
        records = lock.get(group)
        if not isinstance(records, list) or not records:
            raise RuntimeError(f"Stage 2 lock has no {group}")
        for item in records:
            path = Path(str(item["path"]))
            if not path.is_file() or sha256(path) != str(item["sha256"]):
                raise RuntimeError(f"File differs from Stage 2 lock: {path}")

    for device in ["cpu", "gpu"]:
        gate = load(Path(config["protocol"][f"control_gate_{device}"]))
        if gate.get("environment_lock_sha256") != lock_sha:
            raise RuntimeError(f"Stage 2 {device} gate references another lock")
        if gate.get("torch2pc_commit") != candidate_commit:
            raise RuntimeError(f"Stage 2 {device} gate used another candidate")
        if gate.get("torch2pc_reference_commit") != reference_commit:
            raise RuntimeError(f"Stage 2 {device} gate used another reference")
        if not gate.get("gate_observed_within_thresholds"):
            raise RuntimeError(f"Stage 2 {device} gate is outside thresholds")

    freeze = load(Path(config["protocol"]["freeze_manifest"]))
    if freeze.get("milestone") != "stage-2-freeze":
        raise RuntimeError("Unexpected Stage 2 freeze milestone")
    if freeze.get("environment_lock_sha256") != lock_sha:
        raise RuntimeError("Stage 2 freeze references another lock")
    for item in freeze.get("files", []):
        path = Path(str(item["path"]))
        if not path.is_file() or sha256(path) != str(item["sha256"]):
            raise RuntimeError(f"Frozen Stage 2 file changed: {path}")

    plan = load(Path(config["protocol"]["execution_plan"]))
    if plan.get("stage") != "final_stage_2":
        raise RuntimeError("Unexpected Stage 2 execution plan")
    if plan.get("planned_cells") != 80:
        raise RuntimeError("Stage 2 execution plan must contain 80 cells")
    if plan.get("environment_lock_sha256") != lock_sha:
        raise RuntimeError("Stage 2 plan references another lock")
    if plan.get("torch2pc_commit") != candidate_commit:
        raise RuntimeError("Stage 2 plan references another candidate")

    verify_runtime_worktree(
        str(config["paths"]["registry"]), str(config["paths"]["runs"])
    )
    print("Protocol prerequisites observed for stage=final_stage_2")


if __name__ == "__main__":
    main()
