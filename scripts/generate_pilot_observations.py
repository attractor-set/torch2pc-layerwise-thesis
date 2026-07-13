#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

if __package__:
    from scripts.select_pilot import (
        latest_run_events,
        planned_matrix_keys,
        primary_attempts,
        verify_planned_matrix,
    )
else:
    from select_pilot import (
        latest_run_events,
        planned_matrix_keys,
        primary_attempts,
        verify_planned_matrix,
    )
from torch2pc_thesis.reporting import verified_run_artifacts

OBSERVATION_FIELDS = [
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
    "best_epoch",
    "epochs_completed",
    "model_parameter_count",
    "best_validation_metric",
    "primary_metric",
    "total_training_time_sec",
    "started_utc",
    "finished_utc",
    "config_sha256",
    "git_commit",
    "torch2pc_commit",
    "environment_lock_sha256",
    "run_directory",
    "test_evaluated",
    "failure_type",
    "failure_message",
]


def _json_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"Expected a JSON object: {path}")
    return value


def _repository_path(root: Path, value: str) -> Path:
    path = (root / value).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise RuntimeError(f"Registered run directory escapes the repository: {value}") from exc
    return path


def _verify_environment(
    run_directory: Path,
    row: dict[str, str],
    expected_lock_sha256: str,
) -> dict[str, Any]:
    path = run_directory / "environment.json"
    if not path.is_file():
        raise RuntimeError(f"Environment artifact is missing: {path}")
    environment = _json_object(path)
    expected = {
        "source_git_commit": row["git_commit"],
        "experiment_id": row["experiment_id"],
        "run_id": row["run_id"],
        "config_sha256": row["config_sha256"],
        "environment_lock_sha256": expected_lock_sha256,
    }
    for key, value in expected.items():
        if str(environment.get(key, "")) != value:
            raise RuntimeError(
                f"Environment artifact disagrees with registry for {key}: {run_directory}"
            )
    return environment


def _failed_details(run_directory: Path) -> tuple[str, str]:
    path = run_directory / "failure.json"
    if not path.is_file():
        raise RuntimeError(f"Failed pilot run is missing failure.json: {run_directory}")
    failure = _json_object(path)
    return str(failure.get("exception_type", "")), str(failure.get("message", ""))


def build_pilot_observations(
    *,
    root: Path,
    registry_path: Path,
    environment_lock_path: Path,
    base_config_path: Path,
    pilot_config_path: Path,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    environment_lock = _json_object(environment_lock_path)
    environment_lock_sha256 = hashlib.sha256(environment_lock_path.read_bytes()).hexdigest()
    source_commit = str(environment_lock["image_source_git_commit"])
    torch2pc_commit = str(environment_lock["torch2pc_commit"])

    base_config = yaml.safe_load(base_config_path.read_text(encoding="utf-8"))
    pilot_config = yaml.safe_load(pilot_config_path.read_text(encoding="utf-8"))
    events = latest_run_events(registry_path)
    attempts = primary_attempts(
        events,
        source_commit=source_commit,
        torch2pc_commit=torch2pc_commit,
        environment_lock_sha256=environment_lock_sha256,
    )
    matrix_status = verify_planned_matrix(attempts, base_config, pilot_config)

    records: list[dict[str, object]] = []
    for key in planned_matrix_keys(base_config, pilot_config):
        row = attempts[key]
        if row.get("test_evaluated", "false").lower() == "true":
            raise RuntimeError(f"Pilot registry reports test access: {row['run_id']}")
        run_directory = _repository_path(root, row["run_directory"])
        environment = _verify_environment(run_directory, row, environment_lock_sha256)

        metrics: dict[str, Any] = {}
        failure_type = ""
        failure_message = ""
        if row["status"] == "completed":
            metrics, verified_environment = verified_run_artifacts(run_directory, row)
            if verified_environment.get("environment_lock_sha256") != environment_lock_sha256:
                raise RuntimeError(f"Pilot run belongs to another environment: {run_directory}")
            if bool(metrics.get("test_evaluated", False)):
                raise RuntimeError(f"Pilot metrics report test access: {run_directory}")
        else:
            failure_type, failure_message = _failed_details(run_directory)

        records.append(
            {
                "run_id": row["run_id"],
                "experiment_id": row["experiment_id"],
                "stage": row["stage"],
                "dataset": row["dataset"],
                "model": row["model"],
                "method": row["method"],
                "eta": row["eta"],
                "inference_steps": row["inference_steps"],
                "model_seed": row["model_seed"],
                "split_seed": row["split_seed"],
                "status": row["status"],
                "best_epoch": metrics.get("best_epoch", ""),
                "epochs_completed": metrics.get("epochs_completed", ""),
                "model_parameter_count": metrics.get("model_parameter_count", ""),
                "best_validation_metric": metrics.get("best_validation_metric", ""),
                "primary_metric": metrics.get("primary_metric", ""),
                "total_training_time_sec": metrics.get("total_training_time_sec", ""),
                "started_utc": row["started_utc"],
                "finished_utc": row["finished_utc"],
                "config_sha256": row["config_sha256"],
                "git_commit": row["git_commit"],
                "torch2pc_commit": row["torch2pc_commit"],
                "environment_lock_sha256": str(environment.get("environment_lock_sha256", "")),
                "run_directory": row["run_directory"],
                "test_evaluated": "false",
                "failure_type": failure_type,
                "failure_message": failure_message,
            }
        )

    provenance = {
        "source_git_commit": source_commit,
        "torch2pc_commit": torch2pc_commit,
        "environment_lock_sha256": environment_lock_sha256,
        "matrix": matrix_status,
    }
    return records, provenance


def write_observations(path: Path, records: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=OBSERVATION_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)
    temporary.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export the complete, verified validation-only pilot cohort."
    )
    parser.add_argument("--registry", default="experiments/registry.csv")
    parser.add_argument("--environment-lock", default="results/summaries/environment-lock.json")
    parser.add_argument("--base-config", default="configs/base.yaml")
    parser.add_argument("--pilot-config", default="configs/stages/pilot.yaml")
    parser.add_argument("--output", default="results/summaries/pilot_observations.csv")
    args = parser.parse_args()

    root = Path.cwd().resolve()
    records, provenance = build_pilot_observations(
        root=root,
        registry_path=Path(args.registry),
        environment_lock_path=Path(args.environment_lock),
        base_config_path=Path(args.base_config),
        pilot_config_path=Path(args.pilot_config),
    )
    output = Path(args.output)
    write_observations(output, records)
    result = {
        "status": "pilot_observations_exported",
        "output": str(output),
        "rows": len(records),
        "completed": sum(record["status"] == "completed" for record in records),
        "failed": sum(record["status"] == "failed" for record in records),
        "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "provenance": provenance,
        "test_evaluated": False,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
