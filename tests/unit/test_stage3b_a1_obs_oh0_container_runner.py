from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path("scripts/run_stage3b_a1_obs_oh0_container.py")
SPEC = importlib.util.spec_from_file_location("obs_oh0_container_runner", SCRIPT)
assert SPEC is not None
assert SPEC.loader is not None
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


def test_read_dotenv_ignores_comments_and_strips_quotes(tmp_path: Path) -> None:
    path = tmp_path / ".env"
    path.write_text(
        "# comment\nEXPERIMENT_IMAGE='example:1'\nSOURCE_GIT_COMMIT=abc\n",
        encoding="utf-8",
    )
    assert runner.read_dotenv(path) == {
        "EXPERIMENT_IMAGE": "example:1",
        "SOURCE_GIT_COMMIT": "abc",
    }


def test_controlled_compose_environment_overrides_provenance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EXPERIMENT_IMAGE", "stale:old")
    monkeypatch.setenv("SOURCE_GIT_COMMIT", "b" * 40)
    monkeypatch.setenv("SOURCE_GIT_BRANCH", "stale")
    monkeypatch.setenv("UNRELATED_VALUE", "preserved")

    environment = runner.controlled_compose_environment(
        head="a" * 40,
        branch="research/current",
        image="controlled:current",
    )

    assert environment["EXPERIMENT_IMAGE"] == "controlled:current"
    assert environment["SOURCE_GIT_COMMIT"] == "a" * 40
    assert environment["SOURCE_GIT_BRANCH"] == "research/current"
    assert environment["UNRELATED_VALUE"] == "preserved"


@pytest.mark.parametrize(
    "path",
    [
        Path("/tmp/absolute"),
        Path("results/../escape"),
        Path("working/output"),
    ],
)
def test_validate_output_dir_rejects_unsafe_paths(path: Path) -> None:
    with pytest.raises(ValueError):
        runner.validate_output_dir(path)


def test_validate_output_dir_accepts_results_path() -> None:
    runner.validate_output_dir(
        Path(
            "results/stage-3/a1-shortcut-observer-controls/working/obs-oh0-cpu"
        )
    )


def test_validate_summary_accepts_registered_smoke_counts() -> None:
    summary = {
        "control_id": "OBS-OH0",
        "benchmark_schema_id": runner.BENCHMARK_SCHEMA_ID,
        "observer_schema_id": runner.OBSERVER_SCHEMA_ID,
        "passed": True,
        "scope": "smoke",
        "execution_environment": {
            "controlled_container": True,
            "lane": "cpu",
            "source_git_commit": "a" * 40,
            "source_git_branch": "research/current",
        },
        "model_seeds": [0, 1, 2],
        "batches_per_seed": 1,
        "timing_repeats": 3,
        "warmup_pairs_per_lane_arm": 1,
        "aggregate": {
            "warmup_timing_pairs": 2,
            "measured_timing_pairs": 18,
            "timed_executions": 36,
            "memory_pairs": 6,
            "memory_workers": 12,
        },
        "guards": {"runs": 6, "passed": True},
        "structural_passed": True,
    }
    runner.validate_summary(
        summary,
        lane="cpu",
        head="a" * 40,
        branch="research/current",
        max_batches=1,
        timing_repeats=3,
        warmup_pairs=1,
        execution_scope="smoke",
    )


def test_validate_execution_scope_enforces_registered_counts() -> None:
    smoke = runner.argparse.Namespace(
        execution_scope="smoke",
        max_batches=1,
        timing_repeats=3,
        warmup_pairs=1,
    )
    runner.validate_execution_scope(smoke)

    invalid = runner.argparse.Namespace(
        execution_scope="confirmatory",
        max_batches=1,
        timing_repeats=3,
        warmup_pairs=1,
    )
    with pytest.raises(ValueError):
        runner.validate_execution_scope(invalid)


def test_validate_summary_rejects_scope_mismatch() -> None:
    summary = {
        "control_id": "OBS-OH0",
        "benchmark_schema_id": runner.BENCHMARK_SCHEMA_ID,
        "observer_schema_id": runner.OBSERVER_SCHEMA_ID,
        "passed": True,
        "scope": "development",
    }
    with pytest.raises(RuntimeError, match="execution scope"):
        runner.validate_summary(
            summary,
            lane="cpu",
            head="a" * 40,
            branch="research/current",
            max_batches=1,
            timing_repeats=3,
            warmup_pairs=1,
            execution_scope="smoke",
        )
