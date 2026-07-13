from torch2pc_thesis.registry import (
    RegistryEntry,
    append_entry,
    completed_runs,
    latest_by_run_id,
)


def test_registry_tracks_independent_run_attempts(tmp_path) -> None:
    path = tmp_path / "registry.csv"
    common = dict(
        experiment_id="exp-a",
        stage="smoke",
        dataset="MNIST",
        model="lenet_classic",
        method="bp",
        eta="",
        inference_steps="",
        model_seed=0,
        split_seed=42,
        config_sha256="a" * 64,
        git_commit="b" * 40,
        torch2pc_commit="",
        started_utc="2026-07-10T00:00:00Z",
    )
    append_entry(
        path,
        RegistryEntry(
            run_id="run-1",
            status="running",
            run_directory="results/runs/exp-a/run-1",
            **common,
        ),
    )
    append_entry(
        path,
        RegistryEntry(
            run_id="run-1",
            status="completed",
            run_directory="results/runs/exp-a/run-1",
            finished_utc="2026-07-10T00:01:00Z",
            **common,
        ),
    )
    append_entry(
        path,
        RegistryEntry(
            run_id="run-2",
            status="failed",
            run_directory="results/runs/exp-a/run-2",
            finished_utc="2026-07-10T00:02:00Z",
            **common,
        ),
    )

    latest = latest_by_run_id(path)
    assert latest["run-1"]["status"] == "completed"
    assert latest["run-2"]["status"] == "failed"
    assert [row["run_id"] for row in completed_runs(path)] == ["run-1"]
    assert b"\r\n" not in path.read_bytes()


def test_completed_experiments_do_not_count_successful_reruns_as_new_replications(tmp_path) -> None:
    from torch2pc_thesis.registry import completed_experiments

    path = tmp_path / "registry.csv"
    common = dict(
        experiment_id="exp-a",
        stage="final",
        dataset="FashionMNIST",
        model="lenet_classic",
        method="bp",
        eta="",
        inference_steps="",
        model_seed=0,
        split_seed=42,
        config_sha256="a" * 64,
        git_commit="b" * 40,
        torch2pc_commit="c" * 40,
    )
    for run_id, started in [
        ("run-1", "2026-07-10T00:00:00Z"),
        ("run-2", "2026-07-10T01:00:00Z"),
    ]:
        append_entry(
            path,
            RegistryEntry(
                run_id=run_id,
                status="completed",
                run_directory=f"results/runs/exp-a/{run_id}",
                started_utc=started,
                finished_utc=started,
                test_evaluated="true",
                **common,
            ),
        )

    selected = completed_experiments(path)
    assert len(selected) == 1
    assert selected[0]["run_id"] == "run-1"
