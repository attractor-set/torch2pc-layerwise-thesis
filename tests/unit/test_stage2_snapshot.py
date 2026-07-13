from __future__ import annotations

from itertools import product

import pytest

from scripts.snapshot_stage2_results import validate_completed_cells


def rows() -> list[dict[str, str]]:
    values = []
    for dataset, method, seed in product(
        ["MNIST", "FashionMNIST"],
        ["bp", "exact", "fixedpred", "strict"],
        range(10),
    ):
        values.append(
            {
                "stage": "final_stage_2",
                "status": "completed",
                "dataset": dataset,
                "model": "lenet_classic",
                "method": method,
                "model_seed": str(seed),
                "test_evaluated": "true",
                "git_commit": "a" * 40,
                "torch2pc_commit": "b" * 40,
            }
        )
    return values


def test_validate_completed_stage2_matrix() -> None:
    result = validate_completed_cells(rows())
    assert result["completed_unique_cells"] == 80
    assert result["by_dataset"] == {"FashionMNIST": 40, "MNIST": 40}
    assert result["by_method"] == {
        "bp": 20,
        "exact": 20,
        "fixedpred": 20,
        "strict": 20,
    }


def test_validate_rejects_missing_cell() -> None:
    with pytest.raises(RuntimeError, match="incomplete or non-unique"):
        validate_completed_cells(rows()[:-1])
