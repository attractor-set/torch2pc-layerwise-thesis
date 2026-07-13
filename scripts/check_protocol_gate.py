#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import yaml

from torch2pc_thesis.assets import verify_locked_prepared_assets


def load(path: Path) -> dict[str, object]:
    if not path.exists():
        raise RuntimeError(f"Required artifact is missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def config_records_sha256(records: object) -> str:
    if not isinstance(records, list) or not records:
        raise RuntimeError("Environment lock has no config file records")
    normalized: list[dict[str, str]] = []
    for item in records:
        if not isinstance(item, dict):
            raise RuntimeError("Invalid config file record in environment lock")
        normalized.append(
            {"path": str(item.get("path", "")), "sha256": str(item.get("sha256", ""))}
        )
    canonical = json.dumps(
        sorted(normalized, key=lambda item: item["path"]),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def verify_environment_lock() -> None:
    lock = load(Path("results/summaries/environment-lock.json"))
    base = yaml.safe_load(Path("configs/base.yaml").read_text(encoding="utf-8"))
    expected_torch2pc = str(base["torch2pc"]["commit"])
    if lock.get("torch2pc_commit") != expected_torch2pc:
        raise RuntimeError("Environment lock contains another Torch2PC commit")
    actual_torch2pc = subprocess.check_output(
        ["git", "-C", str(base["torch2pc"]["local_path"]), "rev-parse", "HEAD"],
        text=True,
    ).strip()
    if actual_torch2pc != expected_torch2pc:
        raise RuntimeError("Torch2PC checkout differs from the pinned commit")
    torch2pc_status = subprocess.check_output(
        ["git", "-C", str(base["torch2pc"]["local_path"]), "status", "--porcelain"],
        text=True,
    ).strip()
    if torch2pc_status:
        raise RuntimeError("Torch2PC worktree contains uncommitted changes")
    verify_locked_prepared_assets(lock, verify_hashes=True)
    for group in ["config_files", "source_files"]:
        for item in lock.get(group, []):
            path = Path(str(item["path"]))
            if not path.exists() or sha256(path) != item["sha256"]:
                raise RuntimeError(f"File differs from environment lock: {path}")
    expected_config_sha = config_records_sha256(lock.get("config_files"))
    if lock.get("config_sha256") != expected_config_sha:
        raise RuntimeError("Environment lock configuration-tree hash is invalid")
    for key in ["experiment_image", "base_image"]:
        image = lock.get(key, {})
        if not isinstance(image, dict) or not image.get("id"):
            raise RuntimeError(f"Immutable image ID is absent from environment lock: {key}")




def verify_final_runtime_worktree() -> None:
    raw = subprocess.check_output(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        text=True,
    )
    allowed_exact = {"experiments/registry.csv"}
    allowed_prefixes = ("results/runs/", "results/splits/")
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
            "Final stage found non-runtime worktree changes: "
            + "; ".join(unexpected)
        )

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["pilot", "final"])
    args = parser.parse_args()

    verify_environment_lock()

    environment_lock_path = Path("results/summaries/environment-lock.json")
    environment_lock = load(environment_lock_path)
    environment_lock_sha256 = sha256(environment_lock_path)
    expected_source_commit = str(environment_lock.get("image_source_git_commit", ""))
    expected_torch2pc_commit = str(environment_lock.get("torch2pc_commit", ""))
    for device in ["cpu", "gpu"]:
        value = load(Path(f"results/summaries/control_gate_{device}.json"))
        if value.get("environment_lock_sha256") != environment_lock_sha256:
            raise RuntimeError(
                f"Control gate was produced for another environment lock: device={device}"
            )
        if value.get("source_git_commit_observed") != expected_source_commit:
            raise RuntimeError(
                f"Control gate was produced by another source commit: device={device}"
            )
        if value.get("torch2pc_commit") != expected_torch2pc_commit:
            raise RuntimeError(
                f"Control gate was produced with another Torch2PC commit: device={device}"
            )
        if not value.get("gate_observed_within_thresholds"):
            raise RuntimeError(f"Control gate is outside thresholds for device={device}")

    if args.stage == "final":
        freeze = load(Path("results/summaries/pilot-freeze_manifest.json"))
        if freeze.get("milestone") != "pilot-freeze":
            raise RuntimeError("Unexpected pilot freeze artifact")
        for item in freeze.get("files", []):
            path = Path(str(item["path"]))
            actual = sha256(path)
            if actual != item["sha256"]:
                raise RuntimeError(
                    f"Frozen configuration changed: {path}; "
                    f"expected {item['sha256']}, observed {actual}"
                )
        plan_path = Path("results/summaries/final_execution_plan.json")
        plan = load(plan_path)
        if plan.get("stage") != "final":
            raise RuntimeError("Unexpected final execution plan stage")
        if plan.get("environment_lock_sha256") != environment_lock_sha256:
            raise RuntimeError("Final execution plan references another environment lock")
        if plan.get("source_git_commit") != expected_source_commit:
            raise RuntimeError("Final execution plan references another source commit")
        if plan.get("torch2pc_commit") != expected_torch2pc_commit:
            raise RuntimeError("Final execution plan references another Torch2PC commit")
        verify_final_runtime_worktree()
    print(f"Protocol prerequisites observed for stage={args.stage}")


if __name__ == "__main__":
    main()
