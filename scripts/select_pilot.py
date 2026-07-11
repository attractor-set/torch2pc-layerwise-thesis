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


PilotKey = tuple[str, str, str, str, str, str]


def experiment_key(row: dict[str, str]) -> PilotKey:
    return (
        row["dataset"],
        row["model"],
        row["method"],
        row["model_seed"],
        row["eta"],
        row["inference_steps"],
    )


def primary_attempts(events: list[dict[str, str]]) -> dict[PilotKey, dict[str, str]]:
    selected: dict[PilotKey, dict[str, str]] = {}
    terminal = [
        row for row in events
        if row["stage"] == "pilot" and row["status"] in {"completed", "failed"}
    ]
    for row in sorted(terminal, key=lambda item: (item["started_utc"], item["run_id"])):
        key = experiment_key(row)
        selected.setdefault(key, row)
    return selected


def verify_planned_matrix(
    attempts: dict[PilotKey, dict[str, str]],
    base_config: dict[str, object],
    pilot_config: dict[str, object],
) -> dict[str, object]:
    seeds = [str(value) for value in base_config["statistics"]["pilot_seeds"]]
    datasets = [
        str(base_config["statistics"]["primary_dataset"]),
        str(base_config["statistics"]["secondary_dataset"]),
    ]
    selection = pilot_config["selection"]
    models = [str(value) for value in selection["models"]]
    methods = [str(value) for value in selection["methods"]]
    expected: list[PilotKey] = []
    for dataset in datasets:
        for model in models:
            for method in methods:
                if method in {"bp", "exact"}:
                    for seed in seeds:
                        expected.append((dataset, model, method, seed, "", ""))
                    continue
                config = yaml.safe_load(
                    Path(f"configs/methods/{method}.yaml").read_text(encoding="utf-8")
                )
                grid = config.get("search", {}).get("grid", [])
                if not grid:
                    raise RuntimeError(f"Pilot search grid is empty for method={method}")
                for item in grid:
                    for seed in seeds:
                        expected.append(
                            (
                                dataset,
                                model,
                                method,
                                seed,
                                str(item["eta"]),
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
    primary_model: str,
) -> dict[str, object]:
    estimates = []
    for method, params in selected.items():
        candidate = frame[
            (frame["dataset"] == primary_dataset)
            & (frame["model"] == primary_model)
            & (frame["method"] == method)
            & (frame["eta"] == str(params["eta"]))
            & (frame["inference_steps"] == str(params["inference_steps"]))
        ]
        baseline = frame[
            (frame["dataset"] == primary_dataset)
            & (frame["model"] == primary_model)
            & (frame["method"] == "bp")
        ]
        merged = candidate.merge(
            baseline,
            on=["dataset", "model", "model_seed"],
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
    pilot_config = yaml.safe_load(
        Path("configs/stages/pilot.yaml").read_text(encoding="utf-8")
    )
    minimum_success_rate = float(pilot_config["selection"]["minimum_success_rate"])
    models = [str(value) for value in pilot_config["selection"]["models"]]
    if len(models) != 1:
        raise RuntimeError(
            "Pilot selection currently requires exactly one model architecture"
        )
    primary_model = models[0]
    events = latest_run_events(Path("experiments/registry.csv"))
    attempts = primary_attempts(events)
    matrix_status = verify_planned_matrix(attempts, base_config, pilot_config)
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
            (frame["method"] == method)
            & (frame["dataset"] == primary_dataset)
            & (frame["model"] == primary_model)
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
        eligible = grouped[grouped["success_rate"] >= minimum_success_rate].copy()
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
                "validation macro F1; then lower mean measured training time, "
                "inference steps, and eta"
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
        "selection_model": primary_model,
        "pilot_matrix": matrix_status,
        "selected": selected,
        "test_evaluated": False,
        "planning": planning_pairs(frame, selected, primary_dataset, primary_model),
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
