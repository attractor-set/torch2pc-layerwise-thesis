from __future__ import annotations

import csv
from pathlib import Path

import pytest

from scripts.run_stage3b_si_ma0_container import (
    read_dotenv,
    validate_record_counts,
    validate_repo_relative,
    validate_summary,
)
from torch2pc_thesis.stage3b_si_ma0 import (
    CONTRACT_ID,
    IMPLEMENTATION_SCHEMA_ID,
    expected_record_counts,
)


def write_rows(path: Path, count: int) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["record_key"])
        writer.writeheader()
        for index in range(count):
            writer.writerow({"record_key": f"record-{index}"})


def test_read_dotenv(tmp_path: Path) -> None:
    path = tmp_path / ".env"
    path.write_text(
        "\n".join(
            [
                "# comment",
                "EXPERIMENT_IMAGE='example@sha256:abc'",
                'SOURCE_GIT_COMMIT="deadbeef"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    assert read_dotenv(path) == {
        "EXPERIMENT_IMAGE": "example@sha256:abc",
        "SOURCE_GIT_COMMIT": "deadbeef",
    }


@pytest.mark.parametrize(
    "path",
    [
        Path("/tmp/output"),
        Path("../results/output"),
        Path("scripts/output"),
    ],
)
def test_validate_repo_relative_rejects_unsafe_paths(path: Path) -> None:
    with pytest.raises(ValueError):
        validate_repo_relative(path, root="results")


def test_validate_repo_relative_accepts_results_path() -> None:
    validate_repo_relative(
        Path("results/stage-3/si-ma0/working/smoke"),
        root="results",
    )


def test_validate_summary_accepts_smoke_payload() -> None:
    counts = expected_record_counts(
        model_count=1,
        batch_count=1,
        inference_steps=20,
        updated_state_layers=5,
    )
    summary = {
        "contract_id": CONTRACT_ID,
        "implementation_schema_id": IMPLEMENTATION_SCHEMA_ID,
        "scope": "smoke",
        "lane": "cpu",
        "source_git_commit": "a" * 40,
        "source_git_branch": "research/stage3b-si-ma0-implementation",
        "experiment_image": "image@sha256:abc",
        "image_revision": "a" * 40,
        "model_seed": 0,
        "expected_counts": counts,
        "observed_counts": counts,
        "rec_ma0_smoke_passed": True,
        "obs_ma0_smoke_passed": True,
        "ver_ma0_smoke_passed": True,
        "cost_ma0_timer_operational": True,
        "cmp_ma0_smoke_passed": True,
        "confirmatory_decision_made": False,
        "si_ma0_passed": None,
        "dataset_loader_used": True,
        "test_split_access": False,
        "passed": True,
    }
    validate_summary(
        summary,
        scope="smoke",
        lane="cpu",
        model_seed=0,
        max_batches=1,
        head="a" * 40,
        branch="research/stage3b-si-ma0-implementation",
        image="image@sha256:abc",
        image_revision="a" * 40,
    )


def test_validate_summary_rejects_confirmatory_claim() -> None:
    counts = expected_record_counts(
        model_count=1,
        batch_count=1,
        inference_steps=20,
        updated_state_layers=5,
    )
    summary = {
        "contract_id": CONTRACT_ID,
        "implementation_schema_id": IMPLEMENTATION_SCHEMA_ID,
        "scope": "smoke",
        "lane": "cpu",
        "source_git_commit": "a" * 40,
        "source_git_branch": "branch",
        "experiment_image": "image",
        "image_revision": "a" * 40,
        "model_seed": 0,
        "expected_counts": counts,
        "observed_counts": counts,
        "rec_ma0_smoke_passed": True,
        "obs_ma0_smoke_passed": True,
        "ver_ma0_smoke_passed": True,
        "cost_ma0_timer_operational": True,
        "cmp_ma0_smoke_passed": True,
        "confirmatory_decision_made": True,
        "si_ma0_passed": True,
        "dataset_loader_used": True,
        "test_split_access": False,
        "passed": True,
    }
    with pytest.raises(RuntimeError, match="confirmatory decision"):
        validate_summary(
            summary,
            scope="smoke",
            lane="cpu",
            model_seed=0,
            max_batches=1,
            head="a" * 40,
            branch="branch",
            image="image",
            image_revision="a" * 40,
        )


def test_validate_record_counts(tmp_path: Path) -> None:
    counts = expected_record_counts(
        model_count=1,
        batch_count=1,
        inference_steps=20,
        updated_state_layers=5,
    )
    write_rows(
        tmp_path / "si_ma0_event_records.csv",
        counts["state_update_events"],
    )
    write_rows(
        tmp_path / "si_ma0_output_error_records.csv",
        counts["output_error_records"],
    )
    write_rows(
        tmp_path / "si_ma0_mode_comparisons.csv",
        counts["mode_comparisons"],
    )
    validate_record_counts(tmp_path, max_batches=1)
