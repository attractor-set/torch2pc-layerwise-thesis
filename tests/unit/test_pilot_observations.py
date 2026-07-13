from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts import generate_pilot_observations as exporter


def _row(run_directory: str) -> dict[str, str]:
    return {
        "run_id": "run-1",
        "experiment_id": "pilot-fashionmnist-bp-s40",
        "status": "completed",
        "stage": "pilot",
        "dataset": "FashionMNIST",
        "model": "lenet_classic",
        "method": "bp",
        "eta": "",
        "inference_steps": "",
        "model_seed": "40",
        "split_seed": "42",
        "config_sha256": "c" * 64,
        "git_commit": "a" * 40,
        "torch2pc_commit": "b" * 40,
        "run_directory": run_directory,
        "started_utc": "2026-07-13T00:00:00Z",
        "finished_utc": "2026-07-13T00:00:10Z",
        "test_evaluated": "false",
        "notes": "",
    }


def test_build_pilot_observations_exports_verified_metrics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lock_path = tmp_path / "environment-lock.json"
    lock_path.write_text(
        json.dumps(
            {
                "image_source_git_commit": "a" * 40,
                "torch2pc_commit": "b" * 40,
            }
        ),
        encoding="utf-8",
    )
    lock_sha = hashlib.sha256(lock_path.read_bytes()).hexdigest()
    run_directory = tmp_path / "results/runs/experiment/run-1"
    run_directory.mkdir(parents=True)
    row = _row(str(run_directory.relative_to(tmp_path)))
    environment = {
        "source_git_commit": row["git_commit"],
        "experiment_id": row["experiment_id"],
        "run_id": row["run_id"],
        "config_sha256": row["config_sha256"],
        "environment_lock_sha256": lock_sha,
    }
    (run_directory / "environment.json").write_text(json.dumps(environment), encoding="utf-8")
    base_path = tmp_path / "base.yaml"
    pilot_path = tmp_path / "pilot.yaml"
    registry_path = tmp_path / "registry.csv"
    base_path.write_text("{}\n", encoding="utf-8")
    pilot_path.write_text("{}\n", encoding="utf-8")
    registry_path.write_text("run_id\n", encoding="utf-8")
    key = (
        row["dataset"],
        row["model"],
        row["method"],
        row["model_seed"],
        row["eta"],
        row["inference_steps"],
    )

    monkeypatch.setattr(exporter, "latest_run_events", lambda _: [row])
    monkeypatch.setattr(exporter, "primary_attempts", lambda *args, **kwargs: {key: row})
    monkeypatch.setattr(exporter, "planned_matrix_keys", lambda *args: [key])
    monkeypatch.setattr(
        exporter,
        "verify_planned_matrix",
        lambda *args: {
            "planned_attempts": 1,
            "completed_config_seed_cells": 1,
            "failed_config_seed_cells": 0,
        },
    )
    monkeypatch.setattr(
        exporter,
        "verified_run_artifacts",
        lambda *args: (
            {
                "best_epoch": 3,
                "epochs_completed": 3,
                "model_parameter_count": 61706,
                "best_validation_metric": 0.75,
                "primary_metric": "macro_f1",
                "total_training_time_sec": 12.5,
                "test_evaluated": False,
            },
            environment,
        ),
    )

    records, provenance = exporter.build_pilot_observations(
        root=tmp_path,
        registry_path=registry_path,
        environment_lock_path=lock_path,
        base_config_path=base_path,
        pilot_config_path=pilot_path,
    )

    assert len(records) == 1
    assert records[0]["best_validation_metric"] == 0.75
    assert records[0]["environment_lock_sha256"] == lock_sha
    assert records[0]["test_evaluated"] == "false"
    assert provenance["matrix"]["planned_attempts"] == 1


def test_registered_run_directory_cannot_escape_repository(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="escapes the repository"):
        exporter._repository_path(tmp_path, "../outside")
