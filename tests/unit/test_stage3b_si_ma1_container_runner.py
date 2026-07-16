from __future__ import annotations

from pathlib import Path

import pytest

from scripts.run_stage3b_si_ma1_container import (
    build_container_command,
    read_dotenv,
    validate_confirmatory_output_path,
    validate_repo_relative,
    validate_summary,
)
from torch2pc_thesis.stage3b_si_ma1 import PREREGISTRATION_COMMIT


def test_read_dotenv(tmp_path: Path) -> None:
    path = tmp_path / ".env"
    path.write_text(
        "# comment\nEXPERIMENT_IMAGE='example:tag'\nSOURCE_GIT_COMMIT=abc\n",
        encoding="utf-8",
    )
    assert read_dotenv(path) == {
        "EXPERIMENT_IMAGE": "example:tag",
        "SOURCE_GIT_COMMIT": "abc",
    }


@pytest.mark.parametrize(
    "path",
    [
        Path("/tmp/checkpoint.pt"),
        Path("../results/checkpoint.pt"),
        Path("configs/value.yaml"),
    ],
)
def test_validate_repo_relative_rejects_unsafe_paths(path: Path) -> None:
    with pytest.raises(ValueError):
        validate_repo_relative(path, root="results")


def test_validate_confirmatory_output_path() -> None:
    validate_confirmatory_output_path(
        Path(
            "results/stage-3/si-ma1/working/confirmatory/"
            "seed-4/attempt-primary"
        ),
        model_seed=4,
    )


def test_build_container_command_freezes_provenance() -> None:
    command = build_container_command(
        device="gpu",
        scope="confirmatory",
        checkpoint=Path("results/checkpoints/strict.pt"),
        model_seed=2,
        max_batches=3,
        output_dir=Path(
            "results/stage-3/si-ma1/working/confirmatory/"
            "seed-2/attempt-primary"
        ),
        attempt_id="attempt-2",
        head="1" * 40,
        branch="research/si-ma1",
        image="example:tag",
        image_revision="1" * 40,
        prereg_commit=PREREGISTRATION_COMMIT,
    )
    assert "control-gpu" in command
    assert "scripts/run_stage3b_si_ma1.py" in command
    assert f"SI_MA1_PREREG_COMMIT={PREREGISTRATION_COMMIT}" in command
    assert "TORCH2PC_EXECUTION_LANE=rocm" in command


def test_validate_summary_defers_cohort_decision() -> None:
    expected_counts = {
        "model_seed_batch_pairs": 3,
        "matched_blocks": 18,
        "arm_blocks": 54,
        "arm_timing_records": 2700,
        "live_region_timing_records": 6300,
        "numerical_comparison_rows": 36,
        "topology_comparison_rows": 18,
        "block_summary_rows": 18,
        "seed_summary_rows": 1,
        "order_seed_value_rows": 6,
    }
    summary = {
        "contract_id": "stage3b-si-ma1-v1",
        "implementation_schema_id": "stage3b-si-ma1-implementation-v1",
        "scope": "confirmatory",
        "lane": "rocm",
        "model_seed": 2,
        "source_git_commit": "1" * 40,
        "source_git_branch": "research/si-ma1",
        "experiment_image": "example:tag",
        "image_revision": "1" * 40,
        "si_ma1_prereg_commit": PREREGISTRATION_COMMIT,
        "expected_counts": expected_counts,
        "observed_counts": expected_counts,
        "gates": {
            "prerequisites_verified": True,
            "NUM-MA1-cell": True,
            "TOPO-MA1-cell": True,
            "BAL-MA1-cell": True,
            "CMP-MA1-cell": True,
            "CAL-COST-MA1": None,
        },
        "confirmatory_decision_made": False,
        "si_ma1_passed": None,
    }
    validate_summary(
        summary,
        scope="confirmatory",
        lane="rocm",
        model_seed=2,
        max_batches=3,
        head="1" * 40,
        branch="research/si-ma1",
        image="example:tag",
        image_revision="1" * 40,
        prereg_commit=PREREGISTRATION_COMMIT,
    )
