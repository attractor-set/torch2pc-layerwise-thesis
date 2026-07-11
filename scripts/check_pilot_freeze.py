#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import yaml


def completed_events(path: Path) -> list[dict[str, str]]:
    latest: dict[str, dict[str, str]] = {}
    with path.open("r", newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            latest[row["run_id"]] = row
    completed = [row for row in latest.values() if row["status"] == "completed"]
    selected: dict[str, dict[str, str]] = {}
    for row in sorted(completed, key=lambda item: (item["started_utc"], item["run_id"])):
        selected.setdefault(row["experiment_id"], row)
    return list(selected.values())


def main() -> None:
    rows = [
        row
        for row in completed_events(Path("experiments/registry.csv"))
        if row["stage"] == "pilot"
    ]
    if not rows:
        raise RuntimeError("No completed pilot runs were found")
    if any(row["test_evaluated"].lower() == "true" for row in rows):
        raise RuntimeError("Pilot registry contains test evaluation")

    selection_path = Path("results/summaries/pilot_selection.json")
    if not selection_path.exists():
        raise RuntimeError("Pilot selection report is missing")
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    if selection.get("test_evaluated") is not False:
        raise RuntimeError("Pilot selection report has an unexpected test flag")

    base = yaml.safe_load(Path("configs/base.yaml").read_text(encoding="utf-8"))
    pilot_stage = yaml.safe_load(
        Path("configs/stages/pilot.yaml").read_text(encoding="utf-8")
    )
    expected_seeds = {str(value) for value in base["statistics"]["pilot_seeds"]}
    datasets = {
        str(base["statistics"]["primary_dataset"]),
        str(base["statistics"]["secondary_dataset"]),
    }
    minimum_success_rate = float(pilot_stage["selection"]["minimum_success_rate"])
    minimum_completed = math.ceil(len(expected_seeds) * minimum_success_rate)

    completed_counts: dict[str, int] = {}
    for dataset in datasets:
        observed_bp = {
            row["model_seed"]
            for row in rows
            if row["method"] == "bp" and row["dataset"] == dataset
        }
        completed_counts[f"{dataset}/bp"] = len(observed_bp)
        if len(observed_bp) < minimum_completed:
            raise RuntimeError(
                f"BP pilot success rate is below the threshold for {dataset}: "
                f"required {minimum_completed}, observed {len(observed_bp)}"
            )

    applied: dict[str, object] = {}
    for method in ["fixedpred", "strict"]:
        selected = selection["selected"][method]
        config = yaml.safe_load(
            Path(f"configs/methods/{method}.yaml").read_text(encoding="utf-8")
        )
        eta = str(config["method"]["eta"])
        steps = str(config["method"]["inference_steps"])
        if float(eta) != float(selected["eta"]) or int(steps) != int(
            selected["inference_steps"]
        ):
            raise RuntimeError(
                f"Configured {method} parameters do not match pilot_selection.json"
            )
        applied[method] = {"eta": eta, "inference_steps": steps}
        for dataset in datasets:
            observed = {
                row["model_seed"]
                for row in rows
                if row["method"] == method
                and row["dataset"] == dataset
                and float(row["eta"]) == float(eta)
                and int(row["inference_steps"]) == int(steps)
            }
            completed_counts[f"{dataset}/{method}"] = len(observed)
            if len(observed) < minimum_completed:
                raise RuntimeError(
                    f"Selected pilot success rate is below the threshold for "
                    f"{dataset}/{method}: required {minimum_completed}, "
                    f"observed {len(observed)}"
                )

    final_stage = yaml.safe_load(
        Path("configs/stages/final.yaml").read_text(encoding="utf-8")
    )
    final_seeds = final_stage["selection"]["seeds"]
    minimum = int(base["statistics"]["minimum_primary_pairs"])
    if len(final_seeds) < minimum:
        raise RuntimeError(
            f"Final seed count {len(final_seeds)} is below the pre-specified minimum {minimum}"
        )

    result = {
        "status": "ready_for_freeze",
        "completed_pilot_attempts": len(rows),
        "applied_method_parameters": applied,
        "minimum_pilot_completed_per_cell": minimum_completed,
        "completed_pilot_counts": completed_counts,
        "final_seed_count": len(final_seeds),
        "test_evaluated_in_pilot": False,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
