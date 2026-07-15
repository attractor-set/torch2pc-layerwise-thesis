from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path("scripts/run_stage3b_a1_obs_ni0_container.py")
SPEC = importlib.util.spec_from_file_location("obs_ni0_container_runner", SCRIPT)
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


def test_controlled_compose_environment_overrides_inherited_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EXPERIMENT_IMAGE", "stale:old")
    monkeypatch.setenv("SOURCE_GIT_COMMIT", "b" * 40)
    monkeypatch.setenv("UNRELATED_VALUE", "preserved")

    environment = runner.controlled_compose_environment(
        head="a" * 40,
        image="controlled:current",
    )

    assert environment["EXPERIMENT_IMAGE"] == "controlled:current"
    assert environment["SOURCE_GIT_COMMIT"] == "a" * 40
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
            "results/stage-3/a1-shortcut-observer-controls/working/obs-ni0-cpu"
        )
    )
