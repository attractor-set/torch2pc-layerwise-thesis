from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import pytest

from torch2pc_thesis.stage3b_si_ma0_aggregation import (
    BOOTSTRAP_REPEATS,
    CONTRACT_ID,
    EXPECTED_SEEDS,
    REGIONS,
    AggregationError,
    Cell,
    analyze_timing,
    bootstrap_interval,
    compute_global_gates,
    percentile,
    render_report_en,
    render_report_ru,
    verify_manifest,
)


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def make_timing_cells(tmp_path: Path, *, residual: float) -> tuple[Cell, ...]:
    cells: list[Cell] = []
    total_ms = 100.0
    attributed_ms = total_ms * (1.0 - residual)
    region_ms = attributed_ms / len(REGIONS)
    for seed in EXPECTED_SEEDS:
        root = tmp_path / f"seed-{seed}"
        root.mkdir()
        total_rows: list[dict[str, object]] = []
        region_rows: list[dict[str, object]] = []
        for batch_id in range(3):
            for repetition in range(5):
                for measured_step in range(50):
                    total_rows.append(
                        {
                            "model_seed": seed,
                            "batch_id": batch_id,
                            "timing_repetition": repetition,
                            "measured_step": measured_step,
                            "total_device_time_ms": total_ms,
                            "exclusive_region_time_sum_ms": attributed_ms,
                            "accounting_residual": residual,
                            "finite": True,
                            "nonnegative": True,
                        }
                    )
                    for region in REGIONS:
                        region_rows.append(
                            {
                                "model_seed": seed,
                                "batch_id": batch_id,
                                "timing_repetition": repetition,
                                "measured_step": measured_step,
                                "region": region,
                                "duration_ms": region_ms,
                                "finite": True,
                                "nonnegative": True,
                            }
                        )
        write_csv(root / "si_ma0_total_timing_records.csv", total_rows)
        write_csv(root / "si_ma0_region_timing_records.csv", region_rows)
        cells.append(
            Cell(
                seed=seed,
                root=root,
                summary={},
                environment={},
                decision={},
                attempts=(),
                manifest_sha256="0" * 64,
            )
        )
    return tuple(cells)


def test_percentile_uses_linear_interpolation() -> None:
    assert percentile([0.0, 10.0], 0.25) == pytest.approx(2.5)
    assert percentile([0.0, 10.0], 0.50) == pytest.approx(5.0)
    assert percentile([0.0, 10.0], 0.75) == pytest.approx(7.5)


def test_bootstrap_interval_is_deterministic() -> None:
    values = [0.1, 0.2, 0.3, 0.4]
    first = bootstrap_interval(values, statistic="median", repeats=100, seed=7)
    second = bootstrap_interval(values, statistic="median", repeats=100, seed=7)
    assert first == second
    assert first[0] <= 0.25 <= first[1]


def test_verify_manifest_accepts_exact_artifacts(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("evidence\n", encoding="utf-8")
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    (tmp_path / "SHA256SUMS").write_text(
        f"{digest}  artifact.txt\n",
        encoding="utf-8",
    )
    manifest_digest = verify_manifest(tmp_path)
    assert len(manifest_digest) == 64


def test_verify_manifest_rejects_mismatch(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("changed\n", encoding="utf-8")
    (tmp_path / "SHA256SUMS").write_text(
        f"{'0' * 64}  artifact.txt\n",
        encoding="utf-8",
    )
    with pytest.raises(AggregationError, match="checksum mismatch"):
        verify_manifest(tmp_path)


def test_analyze_timing_reproduces_strict_cost_failure(tmp_path: Path) -> None:
    cells = make_timing_cells(tmp_path, residual=0.16)
    seed_rows, statistics_rows, accounting, details = analyze_timing(cells)

    assert len(seed_rows) == 80
    assert len(statistics_rows) == 8
    assert accounting["counts"]["measured_steps"] == 7500
    assert accounting["counts"]["repetition_aggregates"] == 150
    assert accounting["passing_measured_step_fraction"] == 0.0
    assert accounting["passing_repetition_fraction"] == 0.0
    assert accounting["accounting_residual"]["median"] == pytest.approx(0.16)
    assert accounting["cost_ma0_passed"] is False
    assert details["cost_ma0_passed"] is False

    residual_row = next(
        row for row in statistics_rows if row["region"] == "unattributed_residual"
    )
    assert residual_row["median"] == pytest.approx(0.16)
    assert residual_row["bootstrap_repeats"] == BOOTSTRAP_REPEATS


def test_global_gate_is_conjunction() -> None:
    cells = tuple(
        Cell(
            seed=seed,
            root=Path(f"seed-{seed}"),
            summary={
                "rec_ma0_cell_passed": True,
                "obs_ma0_cell_passed": True,
                "ver_ma0_cell_passed": True,
                "cmp_ma0_cell_passed": True,
            },
            environment={},
            decision={},
            attempts=(),
            manifest_sha256="0" * 64,
        )
        for seed in EXPECTED_SEEDS
    )
    gates = compute_global_gates(
        cells,
        prerequisites_verified=True,
        cost_ma0_passed=False,
        counts_verified=True,
        provenance_verified=True,
    )
    assert gates == {
        "prerequisites_verified": True,
        "REC-MA0": True,
        "OBS-MA0": True,
        "VER-MA0": True,
        "COST-MA0": False,
        "CMP-MA0": True,
    }
    assert not all(gates.values())


def test_reports_keep_obs_oh0_context_descriptive() -> None:
    summary = {
        "execution_source_commit": "a" * 40,
        "si_ma0_passed": False,
        "decision_state": "fail",
        "gates": {
            "prerequisites_verified": True,
            "REC-MA0": True,
            "OBS-MA0": True,
            "VER-MA0": True,
            "COST-MA0": False,
            "CMP-MA0": True,
        },
        "accounting_residual_statistics": {
            "passing_measured_step_fraction": 0.0,
            "passing_repetition_fraction": 0.0,
            "accounting_residual": {"median": 0.16, "mean": 0.164},
        },
    }
    cost_rows = [
        {
            "region": region,
            "median": 0.1,
            "q1": 0.09,
            "q3": 0.11,
            "bootstrap_95_ci_low": 0.08,
            "bootstrap_95_ci_high": 0.12,
        }
        for region in (*REGIONS, "unattributed_residual")
    ]
    context = {
        "runtime_overheads": {
            "primary_runtime_ratio": 0.1376,
            "off_first_median_runtime_ratio": 0.1628,
        }
    }
    ru = render_report_ru(
        summary=summary,
        cost_rows=cost_rows,
        obs_context=context,
    )
    en = render_report_en(
        summary=summary,
        cost_rows=cost_rows,
        obs_context=context,
    )
    assert CONTRACT_ID in ru
    assert CONTRACT_ID in en
    assert "не изменяет frozen COST-MA0" in ru
    assert "does not override the frozen COST-MA0" in en
    assert '\n"' not in ru
    assert '\n"' not in en


def test_contract_id_is_frozen_v2() -> None:
    assert CONTRACT_ID == "stage3b-si-ma0-v2"
