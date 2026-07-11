#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import yaml


def latest_run_events(registry: Path) -> list[dict[str, str]]:
    latest: dict[str, dict[str, str]] = {}
    with registry.open("r", newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            latest[row["run_id"]] = row
    return list(latest.values())


def experiment_key(row: dict[str, str]) -> tuple[str, str, str, str, str]:
    return (
        row["dataset"],
        row["method"],
        row["model_seed"],
        row["eta"],
        row["inference_steps"],
    )


def primary_attempts(events: list[dict[str, str]]) -> dict[tuple[str, str, str, str, str], dict[str, str]]:
    selected: dict[tuple[str, str, str, str, str], dict[str, str]] = {}
    terminal = [
        row for row in events
        if row["stage"] == "pilot" and row["status"] in {"completed", "failed"}
    ]
    for row in sorted(terminal, key=lambda item: (item["started_utc"], item["run_id"])):
        key = experiment_key(row)
        current = selected.get(key)
        if current is None or (current["status"] != "completed" and row["status"] == "completed"):
            selected[key] = row
    return selected


def verify_planned_matrix(
    attempts: dict[tuple[str, str, str, str, str], dict[str, str]],
    base_config: dict[str, object],
) -> dict[str, object]:
    seeds = [str(value) for value in base_config["statistics"]["pilot_seeds"]]
    datasets = [
        str(base_config["statistics"]["primary_dataset"]),
        str(base_config["statistics"]["secondary_dataset"]),
    ]
    expected: list[tuple[str, str, str, str, str]] = []
    for dataset in datasets:
        for seed in seeds:
            expected.append((dataset, "bp", seed, "", ""))
        for method in ["fixedpred", "strict"]:
            config = yaml.safe_load(
                Path(f"configs/methods/{method}.yaml").read_text(encoding="utf-8")
            )
            for item in config.get("search", {}).get("grid", []):
                for seed in seeds:
                    expected.append(
                        (
                            dataset, method, seed, str(item["eta"]),
                            str(item["inference_steps"]),
                        )
                    )
    missing = [key for key in expected if key not in attempts]
    if missing:
        preview = missing[:10]
        raise RuntimeError(
            f"Pilot matrix is incomplete: {len(missing)} planned terminal attempts are missing; "
            f"first={preview}"
        )
    completed = sum(attempts[key]["status"] == "completed" for key in expected)
    failed = len(expected) - completed
    return {
        "planned_attempts": len(expected),
        "completed_config_seed_cells": completed,
        "failed_config_seed_cells": failed,
    }


def load_metrics(row: dict[str, str]) -> dict[str, object]:
    path = Path(row["run_directory"]) / "metrics.json"
    if not path.exists():
        raise RuntimeError(f"Metrics are missing: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("test_evaluated"):
        raise RuntimeError(f"Pilot test access observed: {path}")
    return value


def planning_pairs(
    frame: pd.DataFrame,
    selected: dict[str, dict[str, object]],
    primary_dataset: str,
) -> dict[str, object]:
    estimates = []
    for method, params in selected.items():
        candidate = frame[
            (frame["dataset"] == primary_dataset)
            & (frame["method"] == method)
            & (frame["eta"] == str(params["eta"]))
            & (frame["inference_steps"] == str(params["inference_steps"]))
        ]
        baseline = frame[
            (frame["dataset"] == primary_dataset) & (frame["method"] == "bp")
        ]
        merged = candidate.merge(
            baseline,
            on=["dataset", "model_seed"],
            suffixes=("_pc", "_bp"),
        )
        differences = (
            merged["best_validation_metric_pc"].astype(float)
            - merged["best_validation_metric_bp"].astype(float)
        ).to_numpy()
        if len(differences) >= 2:
            sd = float(np.std(differences, ddof=1))
            target_half_width = 0.01
            approximate_n = math.ceil((1.96 * sd / target_half_width) ** 2)
            approximate_n = max(10, min(30, approximate_n))
        else:
            sd = float("nan")
            approximate_n = 10
        estimates.append({
            "method": method,
            "pilot_pairs": int(len(differences)),
            "paired_difference_sd": sd,
            "target_95_ci_half_width": 0.01,
            "advisory_final_pairs": approximate_n,
        })
    return {
        "scope": "planning estimate from validation pilot; not a final power guarantee",
        "estimates": estimates,
        "maximum_advisory_pairs": max(item["advisory_final_pairs"] for item in estimates),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    base_config = yaml.safe_load(Path("configs/base.yaml").read_text(encoding="utf-8"))
    primary_dataset = str(base_config["statistics"]["primary_dataset"])
    events = latest_run_events(Path("experiments/registry.csv"))
    attempts = primary_attempts(events)
    matrix_status = verify_planned_matrix(attempts, base_config)
    rows = [row for row in attempts.values() if row["status"] == "completed"]
    records = []
    for row in rows:
        metrics = load_metrics(row)
        records.append({
            **row,
            "best_validation_metric": float(metrics["best_validation_metric"]),
            "total_training_time_sec": float(metrics["total_training_time_sec"]),
        })
    frame = pd.DataFrame(records)
    if frame.empty:
        raise RuntimeError("No completed pilot observations were found")

    expected_seeds = {str(value) for value in base_config["statistics"]["pilot_seeds"]}
    expected = len(expected_seeds)
    summaries = []
    selected: dict[str, dict[str, object]] = {}
    for method in ["fixedpred", "strict"]:
        subset = frame[
            (frame["method"] == method) & (frame["dataset"] == primary_dataset)
        ].copy()
        grouped = (
            subset.groupby(["eta", "inference_steps"], dropna=False)
            .agg(
                completed=("run_id", "count"),
                mean_validation=("best_validation_metric", "mean"),
                std_validation=("best_validation_metric", "std"),
                mean_time_sec=("total_training_time_sec", "mean"),
            )
            .reset_index()
        )
        grouped["success_rate"] = grouped["completed"] / expected
        eligible = grouped[grouped["success_rate"] >= 2 / 3].copy()
        if eligible.empty:
            raise RuntimeError(f"No eligible pilot candidate for method={method}")
        eligible = eligible.sort_values(
            ["success_rate", "mean_validation", "mean_time_sec", "inference_steps", "eta"],
            ascending=[False, False, True, True, True],
        )
        winner = eligible.iloc[0]
        selected[method] = {
            "eta": float(winner["eta"]),
            "inference_steps": int(winner["inference_steps"]),
            "selection_rule": (
                "higher success rate on the primary dataset; then higher mean "
                "validation macro F1; then lower mean training time, inference "
                "steps, and eta"
            ),
        }
        eligible.insert(0, "method", method)
        summaries.append(eligible)

    summary = pd.concat(summaries, ignore_index=True)
    output_dir = Path("results/summaries")
    output_dir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(output_dir / "pilot_candidate_summary.csv", index=False)
    result = {
        "status": "selection_observed",
        "selection_dataset": primary_dataset,
        "pilot_matrix": matrix_status,
        "selected": selected,
        "test_evaluated": False,
        "planning": planning_pairs(frame, selected, primary_dataset),
    }
    (output_dir / "pilot_selection.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    if args.apply:
        for method, params in selected.items():
            path = Path(f"configs/methods/{method}.yaml")
            config = yaml.safe_load(path.read_text(encoding="utf-8"))
            config["method"]["eta"] = params["eta"]
            config["method"]["inference_steps"] = params["inference_steps"]
            path.write_text(
                yaml.safe_dump(config, sort_keys=False, allow_unicode=True),
                encoding="utf-8",
            )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
