#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

import yaml


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"Expected a YAML mapping: {path}")
    return value


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"Expected a JSON object: {path}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _method_parameters(method: str) -> dict[str, Any]:
    config = _load_yaml(Path(f"configs/methods/{method}.yaml"))
    method_config = config.get("method")
    if not isinstance(method_config, dict) or method_config.get("name") != method:
        raise RuntimeError(f"Invalid method configuration: {method}")
    return {
        "eta": method_config.get("eta"),
        "inference_steps": method_config.get("inference_steps"),
    }


def _method_order(
    methods: list[str],
    *,
    order_seed: int,
    dataset: str,
    model: str,
    model_seed: int,
) -> list[str]:
    def rank(method: str) -> str:
        material = f"{order_seed}|{dataset}|{model}|{model_seed}|{method}"
        return hashlib.sha256(material.encode("utf-8")).hexdigest()

    return sorted(methods, key=lambda method: (rank(method), method))


def build_final_execution_plan(
    base: dict[str, Any],
    final: dict[str, Any],
    environment_lock: dict[str, Any],
    *,
    environment_lock_sha256: str,
) -> dict[str, Any]:
    selection = final.get("selection")
    if not isinstance(selection, dict):
        raise RuntimeError("Final configuration has no selection mapping")
    policy = str(selection.get("execution_order", ""))
    if policy != "deterministic_hash_counterbalance":
        raise RuntimeError(f"Unsupported final execution order policy: {policy}")
    order_seed = int(selection.get("execution_order_seed", -1))
    if order_seed < 0:
        raise RuntimeError("Final execution_order_seed must be non-negative")

    seeds = [int(value) for value in selection.get("seeds", [])]
    expected_seeds = [int(value) for value in base["statistics"]["final_seeds"]]
    if seeds != expected_seeds:
        raise RuntimeError("Final selection.seeds differs from statistics.final_seeds")
    datasets = [str(value) for value in selection.get("datasets", [])]
    models = [str(value) for value in selection.get("models", [])]
    methods = [str(value) for value in selection.get("methods", [])]
    if not seeds or not datasets or not models or not methods:
        raise RuntimeError("Final execution matrix contains an empty dimension")

    config_tree_sha256 = environment_lock.get("config_sha256")
    if not isinstance(config_tree_sha256, str) or len(config_tree_sha256) != 64:
        raise RuntimeError("Environment lock has no valid configuration-tree hash")

    parameters = {method: _method_parameters(method) for method in methods}
    cells: list[dict[str, Any]] = []
    for dataset in datasets:
        for model in models:
            for model_seed in seeds:
                ordered_methods = _method_order(
                    methods,
                    order_seed=order_seed,
                    dataset=dataset,
                    model=model,
                    model_seed=model_seed,
                )
                for position, method in enumerate(ordered_methods):
                    cells.append(
                        {
                            "order_index": len(cells),
                            "within_seed_method_position": position,
                            "dataset": dataset,
                            "model": model,
                            "model_seed": model_seed,
                            "method": method,
                            **parameters[method],
                        }
                    )

    identities = {
        (cell["dataset"], cell["model"], cell["model_seed"], cell["method"])
        for cell in cells
    }
    if len(identities) != len(cells):
        raise RuntimeError("Final execution plan contains duplicate cells")
    expected_count = len(datasets) * len(models) * len(seeds) * len(methods)
    if len(cells) != expected_count:
        raise RuntimeError("Final execution plan has an unexpected cell count")

    return {
        "schema_version": 1,
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "stage": "final",
        "test_access": "once_per_completed_run_after_pilot_freeze",
        "execution_order_policy": policy,
        "execution_order_seed": order_seed,
        "planned_cells": len(cells),
        "source_git_commit": environment_lock.get("image_source_git_commit"),
        "torch2pc_commit": environment_lock.get("torch2pc_commit"),
        "environment_lock_sha256": environment_lock_sha256,
        "config_tree_sha256": config_tree_sha256,
        "dimensions": {
            "datasets": datasets,
            "models": models,
            "methods": methods,
            "seeds": seeds,
        },
        "cells": cells,
    }


def main() -> None:
    lock_path = Path("results/summaries/environment-lock.json")
    if not lock_path.is_file():
        raise RuntimeError("Environment lock is required before final-plan generation")
    base = _load_yaml(Path("configs/base.yaml"))
    final = _load_yaml(Path("configs/stages/final.yaml"))
    lock = _load_json(lock_path)
    plan = build_final_execution_plan(
        base,
        final,
        lock,
        environment_lock_sha256=_sha256(lock_path),
    )
    output = Path("results/summaries/final_execution_plan.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(plan, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": "final_execution_plan_created",
                "path": str(output),
                "planned_cells": plan["planned_cells"],
                "execution_order_policy": plan["execution_order_policy"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
