from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest


def load_runner() -> ModuleType:
    path = Path("scripts/run_stage3b_a1_mechanism_controls_container.py")
    spec = importlib.util.spec_from_file_location("mechanism_container_runner", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def passing_summary() -> dict[str, object]:
    return {
        "control_id": "MECH-C0",
        "contract_id": "stage3b-a1-mechanism-controls-v1",
        "implementation_schema_id": (
            "stage3b-a1-mechanism-controls-implementation-v1"
        ),
        "scope": "smoke",
        "lane": "cpu",
        "source_git_commit": "a" * 40,
        "source_git_branch": "research/test",
        "experiment_image": "torch2pc:test",
        "image_revision": "a" * 40,
        "geo_c0_passed": True,
        "tr_c0_passed": True,
        "tmp_c0_passed": True,
        "jac_c0_passed": True,
        "core_passed": True,
        "pnz_l0_passed": True,
        "si_ma0_open": True,
        "passed": True,
        "expected_counts": {
            "geometry_records": 8,
            "transport_records": 10,
            "temporal_event_records": 36,
            "temporal_summary_records": 1,
            "block_probe_records": 20,
            "pnz_records": 1,
        },
        "observed_counts": {
            "geometry_records": 8,
            "transport_records": 10,
            "temporal_event_records": 36,
            "temporal_summary_records": 1,
            "block_probe_records": 20,
            "pnz_records": 1,
        },
    }


def test_output_dir_must_be_under_results() -> None:
    runner = load_runner()
    runner.validate_output_dir(
        Path("results/stage-3/a1-shortcut-observer-controls/working/test")
    )
    with pytest.raises(ValueError):
        runner.validate_output_dir(Path("/tmp/result"))
    with pytest.raises(ValueError):
        runner.validate_output_dir(Path("other/result"))
    with pytest.raises(ValueError):
        runner.validate_output_dir(Path("results/../other"))


def test_controlled_compose_environment_overrides_stale_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = load_runner()
    monkeypatch.setenv("SOURCE_GIT_COMMIT", "stale")
    monkeypatch.setenv("SOURCE_GIT_BRANCH", "stale")
    monkeypatch.setenv("EXPERIMENT_IMAGE", "stale")
    monkeypatch.setenv("IMAGE_REVISION", "stale")
    environment = runner.controlled_compose_environment(
        head="a" * 40,
        branch="research/test",
        image="torch2pc:test",
        image_revision="a" * 40,
    )
    assert environment["SOURCE_GIT_COMMIT"] == "a" * 40
    assert environment["SOURCE_GIT_BRANCH"] == "research/test"
    assert environment["EXPERIMENT_IMAGE"] == "torch2pc:test"
    assert environment["IMAGE_REVISION"] == "a" * 40


def test_validate_summary_accepts_registered_smoke() -> None:
    runner = load_runner()
    runner.validate_summary(
        passing_summary(),
        scope="smoke",
        lane="cpu",
        head="a" * 40,
        branch="research/test",
        image="torch2pc:test",
        image_revision="a" * 40,
    )


def test_validate_summary_rejects_closed_si_ma0() -> None:
    runner = load_runner()
    summary = passing_summary()
    summary["si_ma0_open"] = False
    with pytest.raises(RuntimeError, match="si_ma0_open"):
        runner.validate_summary(
            summary,
            scope="smoke",
            lane="cpu",
            head="a" * 40,
            branch="research/test",
            image="torch2pc:test",
            image_revision="a" * 40,
        )


def test_validate_records_rejects_duplicate_keys() -> None:
    runner = load_runner()
    row = {
        "record_key": "same",
        "sub_gate": "PNZ-L0",
        "contract_id": "stage3b-a1-mechanism-controls-v1",
        "implementation_schema_id": (
            "stage3b-a1-mechanism-controls-implementation-v1"
        ),
        "source_git_commit": "a" * 40,
        "source_git_branch": "research/test",
        "experiment_image": "torch2pc:test",
        "image_revision": "a" * 40,
        "finite": "True",
        "passed": "True",
    }
    with pytest.raises(RuntimeError, match="keys"):
        runner.validate_records(
            [row, row.copy()],
            expected_count=2,
            expected_sub_gate="PNZ-L0",
            head="a" * 40,
            branch="research/test",
            image="torch2pc:test",
            image_revision="a" * 40,
        )
