#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import time
from pathlib import Path
from typing import Any

import yaml


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"Expected JSON object: {path}")
    return value


def main() -> None:
    if subprocess.check_output(["git", "status", "--porcelain"], text=True).strip():
        raise RuntimeError(
            "Commit the Stage 2 configuration, lock, controls, and execution plan "
            "before creating the freeze manifest"
        )

    stage_config_path = Path("configs/stages/final_stage_2.yaml")
    stage_config = yaml.safe_load(stage_config_path.read_text(encoding="utf-8"))
    lock_path = Path(stage_config["protocol"]["environment_lock"])
    plan_path = Path(stage_config["protocol"]["execution_plan"])
    gate_paths = [
        Path(stage_config["protocol"]["control_gate_cpu"]),
        Path(stage_config["protocol"]["control_gate_gpu"]),
    ]
    files = [
        Path("configs/base.yaml"),
        *sorted(Path("configs/methods").glob("*.yaml")),
        stage_config_path,
        Path("docs/stage-2-protocol.md"),
        Path("docs/stage-2-protocol_EN.md"),
        Path("experiments/registry-final-80-completed.csv"),
        Path("experiments/registry-final-80-completed.sha256"),
        lock_path,
        plan_path,
        *gate_paths,
    ]
    missing = [str(path) for path in files if not path.is_file()]
    if missing:
        raise RuntimeError(f"Stage 2 freeze evidence is missing: {missing}")

    lock = load_json(lock_path)
    plan = load_json(plan_path)
    if plan.get("stage") != "final_stage_2" or plan.get("planned_cells") != 80:
        raise RuntimeError("Stage 2 execution plan is not the frozen 80-cell design")
    if plan.get("environment_lock_sha256") != sha256(lock_path):
        raise RuntimeError("Stage 2 plan references another environment lock")

    selected: dict[str, Any] = {}
    for method in ["fixedpred", "strict"]:
        value = yaml.safe_load(Path(f"configs/methods/{method}.yaml").read_text(encoding="utf-8"))
        selected[method] = value["method"]

    manifest = {
        "schema_version": 1,
        "milestone": "stage-2-freeze",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip(),
        "image_source_git_commit": lock.get("image_source_git_commit"),
        "environment_lock_sha256": sha256(lock_path),
        "torch2pc_commit": lock.get("torch2pc_commit"),
        "torch2pc_reference_commit": lock.get("torch2pc_reference_commit"),
        "selected_method_parameters": selected,
        "planned_cells": plan["planned_cells"],
        "files": [{"path": str(path), "sha256": sha256(path)} for path in files],
    }
    output = Path(stage_config["protocol"]["freeze_manifest"])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(output)


if __name__ == "__main__":
    main()
