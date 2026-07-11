#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import yaml


def primary_terminal_events(path: Path) -> list[dict[str, str]]:
    latest: dict[str, dict[str, str]] = {}
    with path.open("r", newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            latest[row["run_id"]] = row
    terminal = [
        row for row in latest.values() if row["status"] in {"completed", "failed"}
    ]
    selected: dict[str, dict[str, str]] = {}
    for row in sorted(terminal, key=lambda item: (item["started_utc"], item["run_id"])):
        selected.setdefault(row["experiment_id"], row)
    return list(selected.values())


def main() -> None:
    attempts = [
        row
        for row in primary_terminal_events(Path("experiments/registry.csv"))
        if row["stage"] == "pilot"
    ]
    if not attempts:
        raise RuntimeError("No terminal pilot attempts were found")
    if any(row["test_evaluated"].lower() == "true" for row in attempts):
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

    completed = [row for row in attempts if row["status"] == "completed"]
    primary_dataset = str(base["statistics"]["primary_dataset"])
    secondary_dataset = str(base["statistics"]["secondary_dataset"])
    models = [str(value) for value in pilot_stage["selection"]["models"]]
    if len(models) != 1:
        raise RuntimeError(
            "Pilot freeze currently requires exactly one model architecture"
        )
    primary_model = models[0]
    if selection.get("selection_model") != primary_model:
        raise RuntimeError("Pilot selection report has an unexpected model")
    completed_counts: dict[str, int] = {}
    for dataset in datasets:
        observed_bp = {
            row["model_seed"]
            for row in completed
            if row["method"] == "bp"
            and row["dataset"] == dataset
            and row["model"] == primary_model
        }
        completed_counts[f"{dataset}/bp"] = len(observed_bp)
    if completed_counts[f"{primary_dataset}/bp"] < minimum_completed:
        raise RuntimeError(
            f"BP pilot success rate is below the threshold for {primary_dataset}: "
            f"required {minimum_completed}, "
            f"observed {completed_counts[f'{primary_dataset}/bp']}"
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
                for row in completed
                if row["method"] == method
                and row["dataset"] == dataset
                and row["model"] == primary_model
                and float(row["eta"]) == float(eta)
                and int(row["inference_steps"]) == int(steps)
            }
            completed_counts[f"{dataset}/{method}"] = len(observed)
            if dataset == primary_dataset and len(observed) < minimum_completed:
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
    advisory = int(selection.get("planning", {}).get("maximum_advisory_pairs", minimum))
    if len(final_seeds) < advisory:
        raise RuntimeError(
            f"Final seed count {len(final_seeds)} is below the pilot planning estimate "
            f"{advisory}; update both statistics.final_seeds and final selection.seeds "
            "before freezing"
        )

    result = {
        "status": "ready_for_freeze",
        "terminal_pilot_attempts": len(attempts),
        "completed_pilot_attempts": len(completed),
        "selection_model": primary_model,
        "applied_method_parameters": applied,
        "minimum_pilot_completed_per_cell": minimum_completed,
        "completed_pilot_counts": completed_counts,
        "secondary_dataset_status": {
            "dataset": secondary_dataset,
            "role": "descriptive_only_for_selection",
        },
        "final_seed_count": len(final_seeds),
        "pilot_advisory_final_pairs": advisory,
        "test_evaluated_in_pilot": False,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
