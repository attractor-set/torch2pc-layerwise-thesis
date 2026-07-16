from __future__ import annotations

import csv
from pathlib import Path

import pytest

from torch2pc_thesis.stage3b_si_ma1_aggregation import (
    BOOTSTRAP_REPEATS,
    BOOTSTRAP_SEED,
    EXCESS_MARGIN,
    SIMA1AggregationError,
    bootstrap_median,
    build_order_sensitivity_rows,
    concatenate_csvs,
    recompute_seed_values,
    validate_seed_values,
)

SEED_VALUES = [
    -0.18797248545840936,
    -0.1911865144475936,
    -0.18016698531213707,
    -0.19069109346537144,
    -0.19057905328028377,
    -0.19019312702398197,
    -0.1957111993747536,
    -0.20117356769581987,
    -0.18862187616037485,
    -0.20788127820454141,
]


def block_rows() -> list[dict[str, str]]:
    orders = ("ABC", "BCA", "CAB", "ACB", "CBA", "BAC")
    rows: list[dict[str, str]] = []
    for seed, d_seed in enumerate(SEED_VALUES):
        for batch in range(3):
            for order in orders:
                rows.append(
                    {
                        "model_seed": str(seed),
                        "batch_id": str(batch),
                        "order": order,
                        "calibrated_excess_gap": str(d_seed),
                    }
                )
    return rows


def test_registered_bootstrap_is_deterministic_and_passes() -> None:
    first = bootstrap_median(SEED_VALUES)
    second = bootstrap_median(SEED_VALUES)

    assert first == second
    assert first.repeats == BOOTSTRAP_REPEATS
    assert first.seed == BOOTSTRAP_SEED
    assert first.observed == pytest.approx(-0.1906350733728276)
    assert first.upper_one_sided_95 == pytest.approx(
        -0.18862187616037485
    )
    assert first.upper_one_sided_95 <= EXCESS_MARGIN


def test_bootstrap_requires_exact_frozen_parameters() -> None:
    with pytest.raises(SIMA1AggregationError, match="exactly ten"):
        bootstrap_median(SEED_VALUES[:-1])

    with pytest.raises(SIMA1AggregationError, match="frozen"):
        bootstrap_median(SEED_VALUES, repeats=100)

    with pytest.raises(SIMA1AggregationError, match="frozen"):
        bootstrap_median(SEED_VALUES, seed=1)


def test_recompute_seed_values_uses_eighteen_signed_blocks() -> None:
    observed = recompute_seed_values(block_rows())

    assert observed == pytest.approx(
        {seed: value for seed, value in enumerate(SEED_VALUES)}
    )
    assert all(value < 0 for value in observed.values())


def test_recompute_seed_values_rejects_missing_block() -> None:
    rows = block_rows()
    rows.pop()

    with pytest.raises(SIMA1AggregationError, match="18 matched blocks"):
        recompute_seed_values(rows)


def test_validate_seed_values_rejects_summary_drift() -> None:
    recomputed = {seed: value for seed, value in enumerate(SEED_VALUES)}
    recorded = dict(recomputed)
    recorded[4] += 1e-6

    with pytest.raises(SIMA1AggregationError, match="seed 4"):
        validate_seed_values(recomputed, recorded)


def test_order_sensitivity_is_non_authorizing() -> None:
    rows = build_order_sensitivity_rows(block_rows())

    assert len(rows) == 12
    assert {row["analysis"] for row in rows} == {
        "order_stratified",
        "leave_one_order_out",
    }
    assert {row["order"] for row in rows} == {
        "ABC",
        "BCA",
        "CAB",
        "ACB",
        "CBA",
        "BAC",
    }
    assert all(row["authorizes_primary_decision"] is False for row in rows)


def test_concatenate_csvs_preserves_one_header(tmp_path: Path) -> None:
    paths: list[Path] = []
    for index in range(2):
        path = tmp_path / f"input-{index}.csv"
        path.write_text(
            "model_seed,value\n"
            f"{index},{index + 0.5}\n",
            encoding="utf-8",
            newline="\n",
        )
        paths.append(path)
    destination = tmp_path / "combined.csv"

    assert concatenate_csvs(paths, destination) == 2

    with destination.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows == [
        {"model_seed": "0", "value": "0.5"},
        {"model_seed": "1", "value": "1.5"},
    ]


def test_concatenate_csvs_rejects_schema_drift(tmp_path: Path) -> None:
    first = tmp_path / "first.csv"
    second = tmp_path / "second.csv"
    first.write_text("a,b\n1,2\n", encoding="utf-8")
    second.write_text("a,c\n1,2\n", encoding="utf-8")

    with pytest.raises(SIMA1AggregationError, match="schema mismatch"):
        concatenate_csvs([first, second], tmp_path / "combined.csv")
