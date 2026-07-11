#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import yaml


def load(path: Path) -> dict[str, object]:
    if not path.exists():
        raise RuntimeError(f"Required artifact is missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()



def verify_environment_lock() -> None:
    lock = load(Path("results/summaries/environment-lock.json"))
    base = yaml.safe_load(Path("configs/base.yaml").read_text(encoding="utf-8"))
    expected_torch2pc = str(base["torch2pc"]["commit"])
    if lock.get("torch2pc_commit") != expected_torch2pc:
        raise RuntimeError("Environment lock contains another Torch2PC commit")
    for group in ["config_files", "source_files"]:
        for item in lock.get(group, []):
            path = Path(str(item["path"]))
            if not path.exists() or sha256(path) != item["sha256"]:
                raise RuntimeError(f"File differs from environment lock: {path}")
    for key in ["experiment_image", "base_image"]:
        image = lock.get(key, {})
        if not isinstance(image, dict) or not image.get("id"):
            raise RuntimeError(f"Immutable image ID is absent from environment lock: {key}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["pilot", "final"])
    args = parser.parse_args()

    verify_environment_lock()

    environment_lock_path = Path("results/summaries/environment-lock.json")
    environment_lock_sha256 = sha256(environment_lock_path)
    for device in ["cpu", "gpu"]:
        value = load(Path(f"results/summaries/control_gate_{device}.json"))
        if value.get("environment_lock_sha256") != environment_lock_sha256:
            raise RuntimeError(
                f"Control gate was produced for another environment lock: device={device}"
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
        status = subprocess.check_output(
            ["git", "status", "--porcelain"], text=True
        ).strip()
        if status:
            raise RuntimeError("Final stage requires a clean Git working tree")
    print(f"Protocol prerequisites observed for stage={args.stage}")


if __name__ == "__main__":
    main()
