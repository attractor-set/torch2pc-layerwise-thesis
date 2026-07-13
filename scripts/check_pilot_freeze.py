#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

import yaml

if __package__:
    from scripts.select_pilot import PilotKey, experiment_key, planned_matrix_keys
else:
    from select_pilot import PilotKey, experiment_key, planned_matrix_keys

REQUIRED_OBSERVATION_COLUMNS = {
    "run_id",
    "experiment_id",
    "stage",
    "dataset",
    "model",
    "method",
    "eta",
    "inference_steps",
    "model_seed",
    "split_seed",
    "status",
    "git_commit",
    "torch2pc_commit",
    "environment_lock_sha256",
    "test_evaluated",
}


def _json_object(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"Expected a JSON object: {path}")
    return value


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        fieldnames = set(reader.fieldnames or [])
        missing = REQUIRED_OBSERVATION_COLUMNS - fieldnames
        if missing:
            raise RuntimeError(f"Pilot observations are missing columns: {sorted(missing)}")
        return list(reader)


def _latest_registry_events(path: Path) -> dict[str, dict[str, str]]:
    latest: dict[str, dict[str, str]] = {}
    with path.open("r", newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            latest[row["run_id"]] = row
    return latest


def _verify_provenance(
    selection: dict[str, object],
    observations: list[dict[str, str]],
) -> dict[str, str]:
    provenance = selection.get("provenance")
    if not isinstance(provenance, dict):
        raise RuntimeError("Pilot selection report is missing provenance")
    required = {
        "source_git_commit",
        "torch2pc_commit",
        "environment_lock_sha256",
    }
    missing = required - set(provenance)
    if missing:
        raise RuntimeError(f"Pilot selection provenance is incomplete: {sorted(missing)}")
    normalized = {key: str(provenance[key]) for key in required}
    for row in observations:
        if row["git_commit"] != normalized["source_git_commit"]:
            raise RuntimeError("Pilot observations mix source Git commits")
        if row["torch2pc_commit"] != normalized["torch2pc_commit"]:
            raise RuntimeError("Pilot observations mix Torch2PC commits")
        if row["environment_lock_sha256"] != normalized["environment_lock_sha256"]:
            raise RuntimeError("Pilot observations mix environment locks")
    return normalized


def _indexed_observations(
    observations: list[dict[str, str]],
) -> dict[PilotKey, dict[str, str]]:
    indexed: dict[PilotKey, dict[str, str]] = {}
    for row in observations:
        if row["stage"] != "pilot":
            raise RuntimeError("Pilot observations contain another stage")
        if row["status"] not in {"completed", "failed"}:
            raise RuntimeError("Pilot observations contain a non-terminal status")
        if row["test_evaluated"].lower() == "true":
            raise RuntimeError("Pilot observations contain test evaluation")
        key = experiment_key(row)
        if key in indexed:
            raise RuntimeError(f"Duplicate pilot observation: {key}")
        indexed[key] = row
    return indexed


def _verify_registry_rows(
    observations: list[dict[str, str]],
    registry_path: Path,
) -> None:
    registry = _latest_registry_events(registry_path)
    checked_fields = [
        "experiment_id",
        "status",
        "stage",
        "dataset",
        "model",
        "method",
        "eta",
        "inference_steps",
        "model_seed",
        "split_seed",
        "git_commit",
        "torch2pc_commit",
        "test_evaluated",
    ]
    for observation in observations:
        row = registry.get(observation["run_id"])
        if row is None:
            raise RuntimeError(
                f"Pilot observation is absent from registry: {observation['run_id']}"
            )
        for field in checked_fields:
            if row[field] != observation[field]:
                raise RuntimeError(
                    f"Registry disagrees with pilot observation for {field}: "
                    f"{observation['run_id']}"
                )


def main() -> None:
    selection_path = Path("results/summaries/pilot_selection.json")
    observations_path = Path("results/summaries/pilot_observations.csv")
    registry_path = Path("experiments/registry.csv")
    for path in [selection_path, observations_path, registry_path]:
        if not path.is_file():
            raise RuntimeError(f"Required pilot evidence is missing: {path}")

    selection = _json_object(selection_path)
    if selection.get("test_evaluated") is not False:
        raise RuntimeError("Pilot selection report has an unexpected test flag")

    observations = _read_csv(observations_path)
    if not observations:
        raise RuntimeError("Pilot observations are empty")
    provenance = _verify_provenance(selection, observations)
    indexed = _indexed_observations(observations)
    _verify_registry_rows(observations, registry_path)

    base = yaml.safe_load(Path("configs/base.yaml").read_text(encoding="utf-8"))
    pilot_stage = yaml.safe_load(Path("configs/stages/pilot.yaml").read_text(encoding="utf-8"))
    expected_keys = planned_matrix_keys(base, pilot_stage)
    missing = [key for key in expected_keys if key not in indexed]
    extra = [key for key in indexed if key not in set(expected_keys)]
    if missing or extra:
        raise RuntimeError(
            f"Pilot observations do not match the planned matrix: "
            f"missing={missing[:10]}, extra={extra[:10]}"
        )

    completed = [indexed[key] for key in expected_keys if indexed[key]["status"] == "completed"]
    failed = len(expected_keys) - len(completed)
    matrix = selection.get("pilot_matrix")
    if not isinstance(matrix, dict):
        raise RuntimeError("Pilot selection report is missing matrix status")
    expected_matrix = {
        "planned_attempts": len(expected_keys),
        "completed_config_seed_cells": len(completed),
        "failed_config_seed_cells": failed,
    }
    for key, value in expected_matrix.items():
        if int(matrix.get(key, -1)) != value:
            raise RuntimeError(f"Pilot selection matrix disagrees for {key}")

    expected_seeds = {str(value) for value in base["statistics"]["pilot_seeds"]}
    datasets = {
        str(base["statistics"]["primary_dataset"]),
        str(base["statistics"]["secondary_dataset"]),
    }
    minimum_success_rate = float(pilot_stage["selection"]["minimum_success_rate"])
    minimum_completed = math.ceil(len(expected_seeds) * minimum_success_rate)
    primary_dataset = str(base["statistics"]["primary_dataset"])
    secondary_dataset = str(base["statistics"]["secondary_dataset"])
    models = [str(value) for value in pilot_stage["selection"]["models"]]
    if len(models) != 1:
        raise RuntimeError("Pilot freeze currently requires exactly one model architecture")
    primary_model = models[0]
    if selection.get("selection_model") != primary_model:
        raise RuntimeError("Pilot selection report has an unexpected model")

    completed_counts: dict[str, int] = {}
    for dataset in datasets:
        observed_bp = {
            row["model_seed"]
            for row in completed
            if row["method"] == "bp" and row["dataset"] == dataset and row["model"] == primary_model
        }
        completed_counts[f"{dataset}/bp"] = len(observed_bp)
    if completed_counts[f"{primary_dataset}/bp"] < minimum_completed:
        raise RuntimeError(
            f"BP pilot success rate is below the threshold for {primary_dataset}: "
            f"required {minimum_completed}, "
            f"observed {completed_counts[f'{primary_dataset}/bp']}"
        )

    selected = selection.get("selected")
    if not isinstance(selected, dict):
        raise RuntimeError("Pilot selection report is missing selected parameters")
    applied: dict[str, object] = {}
    for method in ["fixedpred", "strict"]:
        selected_method = selected.get(method)
        if not isinstance(selected_method, dict):
            raise RuntimeError(f"Pilot selection is missing method={method}")
        config = yaml.safe_load(Path(f"configs/methods/{method}.yaml").read_text(encoding="utf-8"))
        eta = str(config["method"]["eta"])
        steps = str(config["method"]["inference_steps"])
        if float(eta) != float(selected_method["eta"]) or int(steps) != int(
            selected_method["inference_steps"]
        ):
            raise RuntimeError(f"Configured {method} parameters do not match pilot_selection.json")
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

    final_stage = yaml.safe_load(Path("configs/stages/final.yaml").read_text(encoding="utf-8"))
    final_seeds = [int(value) for value in final_stage["selection"]["seeds"]]
    configured_final_seeds = [int(value) for value in base["statistics"]["final_seeds"]]
    if final_seeds != configured_final_seeds:
        raise RuntimeError("Final selection.seeds must exactly match statistics.final_seeds")
    minimum = int(base["statistics"]["minimum_primary_pairs"])
    if len(final_seeds) < minimum:
        raise RuntimeError(
            f"Final seed count {len(final_seeds)} is below the pre-specified minimum {minimum}"
        )
    planning = selection.get("planning")
    if not isinstance(planning, dict):
        raise RuntimeError("Pilot selection report is missing planning data")
    advisory = int(planning.get("maximum_advisory_pairs", minimum))
    if len(final_seeds) < advisory:
        raise RuntimeError(
            f"Final seed count {len(final_seeds)} is below the pilot planning estimate "
            f"{advisory}; update both statistics.final_seeds and final selection.seeds "
            "before freezing"
        )

    result = {
        "status": "ready_for_freeze",
        "terminal_pilot_attempts": len(expected_keys),
        "completed_pilot_attempts": len(completed),
        "failed_pilot_attempts": failed,
        "selection_model": primary_model,
        "pilot_provenance": provenance,
        "pilot_observations_sha256": hashlib.sha256(observations_path.read_bytes()).hexdigest(),
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
