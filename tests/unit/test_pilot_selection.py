from scripts.select_pilot import experiment_key, primary_attempts


def _event(run_id: str, status: str, started: str) -> dict[str, str]:
    return {
        "run_id": run_id,
        "experiment_id": "exp-1",
        "status": status,
        "stage": "pilot",
        "dataset": "FashionMNIST",
        "model": "lenet_classic",
        "method": "strict",
        "model_seed": "40",
        "eta": "0.05",
        "inference_steps": "20",
        "started_utc": started,
    }


def test_first_terminal_attempt_defines_pilot_success_cell() -> None:
    failure = _event("run-a", "failed", "2026-07-10T00:00:00Z")
    success = _event("run-b", "completed", "2026-07-10T01:00:00Z")
    selected = primary_attempts([success, failure])
    assert selected[experiment_key(failure)]["status"] == "failed"


def test_pilot_attempts_are_filtered_by_environment_cohort(tmp_path) -> None:
    current_run = tmp_path / "current"
    previous_run = tmp_path / "previous"
    current_run.mkdir()
    previous_run.mkdir()
    (current_run / "environment.json").write_text(
        '{"environment_lock_sha256": "lock-current"}\n',
        encoding="utf-8",
    )
    (previous_run / "environment.json").write_text(
        '{"environment_lock_sha256": "lock-previous"}\n',
        encoding="utf-8",
    )

    current = {
        **_event("run-current", "completed", "2026-07-10T02:00:00Z"),
        "git_commit": "source-current",
        "torch2pc_commit": "torch-current",
        "run_directory": str(current_run),
    }
    previous = {
        **_event("run-previous", "completed", "2026-07-10T01:00:00Z"),
        "git_commit": "source-previous",
        "torch2pc_commit": "torch-current",
        "run_directory": str(previous_run),
    }

    selected = primary_attempts(
        [previous, current],
        source_commit="source-current",
        torch2pc_commit="torch-current",
        environment_lock_sha256="lock-current",
    )

    assert list(selected.values()) == [current]


def test_planned_pilot_matrix_contains_all_96_cells() -> None:
    from pathlib import Path

    import yaml

    from scripts.select_pilot import planned_matrix_keys

    base = yaml.safe_load(Path("configs/base.yaml").read_text(encoding="utf-8"))
    pilot = yaml.safe_load(
        Path("configs/stages/pilot.yaml").read_text(encoding="utf-8")
    )
    keys = planned_matrix_keys(base, pilot)
    assert len(keys) == 96
    assert len(set(keys)) == 96
