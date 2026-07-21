from __future__ import annotations

import csv
import json
import shutil
import statistics
import subprocess
from collections import defaultdict
from pathlib import Path

import pytest

from torch2pc_thesis.stage3b_matched_analysis import (
    EXPECTED_OUTPUT_NAMES,
    Stage3BMatchedAnalysisError,
    _analysis_source_profile,
    _locality_stream,
    generate_matched_analysis,
    generate_synthetic_matched_analysis,
    validate_generated_analysis_output,
)
from torch2pc_thesis.stage3b_matched_analysis_protocol import (
    ALL_CANDIDATES,
    BATCH_SIZES,
    DEPTHS,
    METHODS,
    MODEL_SEEDS,
    WIDTHS,
)


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    assert rows
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def _candidate_ratios(candidate: str, method: str) -> dict[str, float]:
    if candidate == "stage2_baseline":
        return {
            "device": 1.0,
            "host": 1.0,
            "allocated": 1.0,
            "reserved": 1.0,
            "saved": 1.0,
            "state_vjp": 1.0,
            "graph_span": 1.0,
            "dependency": 1.0,
        }
    if candidate == "isolated_layer_vjp":
        return {
            "device": 0.80 if method == "fixedpred" else 0.75,
            "host": 0.82 if method == "fixedpred" else 0.78,
            "allocated": 1.05,
            "reserved": 1.04,
            "saved": 0.80,
            "state_vjp": 0.80,
            "graph_span": 0.80,
            "dependency": 0.80,
        }
    return {
        "device": 0.90 if method == "fixedpred" else 0.85,
        "host": 0.88 if method == "fixedpred" else 0.84,
        "allocated": 0.85,
        "reserved": 0.86,
        "saved": 0.60,
        "state_vjp": 0.60,
        "graph_span": 0.60,
        "dependency": 0.60,
    }


def _write_full_synthetic_fixture(root: Path) -> None:
    root.mkdir()
    marker = {
        "schema_version": 1,
        "synthetic_fixture": True,
        "fixture_id": "stage3b-matched-analysis-full-matrix-v1",
        "generated_by": "test_stage3b_matched_analysis_implementation",
        "test_dataset_access": False,
        "matched_cell_count": 288,
        "matched_block_count": 96,
        "repetition_count": 1440,
    }
    (root / ".synthetic-stage3b-analysis-fixture.json").write_text(
        json.dumps(marker, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    cells: list[dict[str, object]] = []
    repetitions: list[dict[str, object]] = []
    locality_lines: list[str] = []
    block_order = 0
    for method in METHODS:
        for depth in DEPTHS:
            for width in WIDTHS:
                for batch_size in BATCH_SIZES:
                    for seed in MODEL_SEEDS:
                        block_id = f"block-{block_order:03d}"
                        baseline_device = float(depth * width * batch_size)
                        baseline_host = baseline_device * 1.2
                        seed_factor = 1.0 + (seed - 71) * 0.002
                        depth_factor = (depth / 4.0) ** 0.01
                        width_factor = (width / 64.0) ** 0.005
                        batch_factor = (batch_size / 64.0) ** 0.005
                        scale_factor = seed_factor * depth_factor * width_factor * batch_factor
                        for candidate in ALL_CANDIDATES:
                            ratios = _candidate_ratios(candidate, method)
                            cell_id = f"cell-{block_order:03d}-{candidate}"
                            candidate_factor = (
                                1.0 if candidate == "stage2_baseline" else scale_factor
                            )
                            cell = {
                                "cell_id": cell_id,
                                "block_id": block_id,
                                "candidate_id": candidate,
                                "method": method,
                                "depth": depth,
                                "width": width,
                                "batch_size": batch_size,
                                "model_seed": seed,
                                "primary_host_time_us": baseline_host
                                * ratios["host"]
                                * candidate_factor,
                                "primary_device_time_us": baseline_device
                                * ratios["device"]
                                * candidate_factor,
                                "primary_peak_allocated_bytes": 1_000_000.0
                                * ratios["allocated"],
                                "primary_peak_reserved_bytes": 1_200_000.0 * ratios["reserved"],
                                "observer_cost_ms": (
                                    0.05 if candidate == "stage2_baseline" else 0.08
                                ),
                                "saved_tensor_bytes": 100_000.0 * ratios["saved"],
                                "state_vjp_calls": 100.0 * ratios["state_vjp"],
                                "graph_span": 100.0 * ratios["graph_span"],
                                "dependency_radius": 100.0 * ratios["dependency"],
                                "graph_lifetimes": "synthetic",
                                "feedback_operator": "synthetic",
                                "fallback_validation_cost_ms": "",
                                "fallback_validation_status": "not_applicable_before_ex_if0",
                            }
                            cells.append(cell)
                            for repetition in range(5):
                                repetitions.append(
                                    {
                                        "cell_id": cell_id,
                                        "block_id": block_id,
                                        "candidate_id": candidate,
                                        "method": method,
                                        "depth": depth,
                                        "width": width,
                                        "batch_size": batch_size,
                                        "model_seed": seed,
                                        "repetition": repetition,
                                        "primary_host_time_median_us": cell[
                                            "primary_host_time_us"
                                        ],
                                        "primary_device_time_median_us": cell[
                                            "primary_device_time_us"
                                        ],
                                        "primary_peak_allocated_max_bytes": cell[
                                            "primary_peak_allocated_bytes"
                                        ],
                                        "primary_peak_reserved_max_bytes": cell[
                                            "primary_peak_reserved_bytes"
                                        ],
                                        "observer_cost_median_ms": cell["observer_cost_ms"],
                                        "saved_tensor_bytes_median": cell["saved_tensor_bytes"],
                                        "state_vjp_calls_median": cell["state_vjp_calls"],
                                        "graph_span_max": cell["graph_span"],
                                        "dependency_radius_max": cell["dependency_radius"],
                                        "graph_lifetimes": cell["graph_lifetimes"],
                                        "feedback_operator": cell["feedback_operator"],
                                        "fallback_validation_cost_ms": cell[
                                            "fallback_validation_cost_ms"
                                        ],
                                        "fallback_validation_status": cell[
                                            "fallback_validation_status"
                                        ],
                                    }
                                )
                                for step in range(2):
                                    modules = (
                                        list(range(depth))
                                        if candidate == "stage2_baseline"
                                        else list(range(max(1, depth // 2)))
                                    )
                                    event = {
                                        "cell_id": cell_id,
                                        "block_id": block_id,
                                        "candidate_id": candidate,
                                        "method": method,
                                        "repetition": repetition,
                                        "step": step,
                                        "logical_edge_count": len(modules),
                                        "graph_island_count": 1,
                                        "graph_module_set": modules,
                                        "graph_lifetime": (
                                            "reused_across_inference_sweeps"
                                            if method == "fixedpred"
                                            else "single_vjp_call"
                                        ),
                                        "orchestration_barriers": (
                                            0 if candidate != "composite_vjp" else 1
                                        ),
                                    }
                                    locality_lines.append(json.dumps(event, sort_keys=True) + "\n")
                        block_order += 1

    assert len(cells) == 288
    assert len(repetitions) == 1440
    assert block_order == 96
    _write_csv(root / "profiling_cells.csv", cells)
    _write_csv(root / "profiling_repetitions.csv", repetitions)

    grouped: defaultdict[tuple[str, str, int, int, int], list[dict[str, object]]] = (
        defaultdict(list)
    )
    for cell in cells:
        grouped[
            (
                str(cell["candidate_id"]),
                str(cell["method"]),
                int(cell["depth"]),
                int(cell["width"]),
                int(cell["batch_size"]),
            )
        ].append(cell)
    summary_rows: list[dict[str, object]] = []
    for (candidate, method, depth, width, batch_size), rows in sorted(grouped.items()):
        summary_rows.append(
            {
                "candidate_id": candidate,
                "method": method,
                "depth": depth,
                "width": width,
                "batch_size": batch_size,
                "model_seed_count": 3,
                "primary_host_time_median_us": statistics.median(
                    float(row["primary_host_time_us"]) for row in rows
                ),
                "primary_device_time_median_us": statistics.median(
                    float(row["primary_device_time_us"]) for row in rows
                ),
                "primary_peak_allocated_median_bytes": statistics.median(
                    float(row["primary_peak_allocated_bytes"]) for row in rows
                ),
                "primary_peak_reserved_median_bytes": statistics.median(
                    float(row["primary_peak_reserved_bytes"]) for row in rows
                ),
                "observer_cost_median_ms": statistics.median(
                    float(row["observer_cost_ms"]) for row in rows
                ),
                "saved_tensor_bytes_median": statistics.median(
                    float(row["saved_tensor_bytes"]) for row in rows
                ),
                "state_vjp_calls_median": statistics.median(
                    float(row["state_vjp_calls"]) for row in rows
                ),
                "graph_span_max": max(float(row["graph_span"]) for row in rows),
                "dependency_radius_max": max(
                    float(row["dependency_radius"]) for row in rows
                ),
            }
        )
    assert len(summary_rows) == 96
    _write_csv(root / "profiling_summary.csv", summary_rows)
    (root / "locality_events.jsonl").write_text(
        "".join(locality_lines),
        encoding="utf-8",
    )


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_registered_engine_generates_exact_synthetic_output_contract(
    tmp_path: Path,
) -> None:
    fixture = tmp_path / "fixture"
    _write_full_synthetic_fixture(fixture)
    output = tmp_path / "analysis"

    source_hashes_before = {
        path.name: path.read_bytes() for path in fixture.iterdir() if path.is_file()
    }
    summary = generate_synthetic_matched_analysis(
        fixture,
        output,
        generated_at_utc="2026-07-21T20:00:00Z",
    )
    source_hashes_after = {
        path.name: path.read_bytes() for path in fixture.iterdir() if path.is_file()
    }

    assert source_hashes_after == source_hashes_before
    assert set(path.name for path in output.iterdir()) == set(EXPECTED_OUTPUT_NAMES)
    assert len(_read_csv(output / "paired_block_metrics.csv")) == 192
    assert len(_read_csv(output / "configuration_summary.csv")) == 64
    candidate_method = _read_csv(output / "candidate_method_summary.csv")
    assert len(candidate_method) == 4
    assert len(_read_csv(output / "pareto_membership.csv")) == 96
    assert len(_read_csv(output / "locality_cell_summary.csv")) == 288
    assert len(_read_csv(output / "scaling_seed_effects.csv")) == 84
    assert summary["status"] == "synthetic_implementation_validation_only"
    assert summary["source_kind"] == "synthetic_fixture"
    assert summary["analysis_execution_authorized"] is False

    status = {(row["candidate_id"], row["method"]): row["status"] for row in candidate_method}
    assert status[("isolated_layer_vjp", "fixedpred")] == "retain"
    assert status[("isolated_layer_vjp", "strict")] == "retain"
    assert status[("composite_vjp", "fixedpred")] == "reject_or_revise"
    assert status[("composite_vjp", "strict")] == "reject_or_revise"

    metadata = validate_generated_analysis_output(output)
    assert metadata["analysis_execution_authorized"] is False
    assert metadata["analysis_output_evidence"] is False
    assert metadata["results_publication_permitted"] is False
    assert metadata["test_dataset_access"] is False

    checksums = (output / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
    assert len(checksums) == 17
    assert all((output / line.split(maxsplit=1)[1]).is_file() for line in checksums)
    for name in (
        "device_time_ratio_heatmap.pdf",
        "peak_memory_ratio_heatmap.pdf",
        "structural_cost_ratio_heatmap.pdf",
        "scaling_effects.pdf",
        "pareto_membership.pdf",
        "seed_consistency.pdf",
    ):
        assert (output / name).read_bytes().startswith(b"%PDF-")


def test_synthetic_outputs_are_deterministic_for_fixed_provenance(
    tmp_path: Path,
) -> None:
    fixture = tmp_path / "fixture"
    _write_full_synthetic_fixture(fixture)
    first = tmp_path / "analysis-first"
    second = tmp_path / "analysis-second"

    generate_synthetic_matched_analysis(
        fixture,
        first,
        generated_at_utc="2026-07-21T20:00:00Z",
    )
    generate_synthetic_matched_analysis(
        fixture,
        second,
        generated_at_utc="2026-07-21T20:00:00Z",
    )

    assert {path.name for path in first.iterdir()} == set(EXPECTED_OUTPUT_NAMES)
    for name in EXPECTED_OUTPUT_NAMES:
        assert (first / name).read_bytes() == (second / name).read_bytes()


def test_compressed_locality_stream_reads_real_zstandard_frame(
    tmp_path: Path,
) -> None:
    zstd = shutil.which("zstd")
    assert zstd is not None
    plain = tmp_path / "locality_events.jsonl"
    archive = tmp_path / "locality_events.jsonl.zst"
    record = {
        "cell_id": "cell-0",
        "block_id": "block-0",
        "candidate_id": "stage2_baseline",
        "method": "fixedpred",
        "repetition": 0,
        "step": 0,
        "logical_edge_count": 1,
        "graph_island_count": 1,
        "graph_module_set": [0],
        "graph_lifetime": "single_vjp_call",
        "orchestration_barriers": 0,
    }
    plain.write_text(json.dumps(record) + "\n", encoding="utf-8")
    subprocess.run(
        [zstd, "-q", "-f", str(plain), "-o", str(archive)],
        check=True,
    )

    assert list(_locality_stream(archive)) == [record]


def test_synthetic_engine_is_fail_closed_for_existing_output_root(
    tmp_path: Path,
) -> None:
    fixture = tmp_path / "fixture"
    _write_full_synthetic_fixture(fixture)
    output = tmp_path / "analysis"
    output.mkdir()

    with pytest.raises(
        Stage3BMatchedAnalysisError,
        match="must not already exist",
    ):
        generate_synthetic_matched_analysis(
            fixture,
            output,
            generated_at_utc="2026-07-21T20:00:00Z",
        )


def test_synthetic_engine_rejects_missing_registered_cell(
    tmp_path: Path,
) -> None:
    fixture = tmp_path / "fixture"
    _write_full_synthetic_fixture(fixture)
    rows = _read_csv(fixture / "profiling_cells.csv")
    _write_csv(fixture / "profiling_cells.csv", [dict(row) for row in rows[:-1]])

    with pytest.raises(Stage3BMatchedAnalysisError, match="cell row count differs"):
        generate_synthetic_matched_analysis(
            fixture,
            tmp_path / "analysis",
            generated_at_utc="2026-07-21T20:00:00Z",
        )


def test_sealed_evidence_entrypoint_remains_execution_closed(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        Stage3BMatchedAnalysisError,
        match="execution is closed",
    ):
        generate_matched_analysis(
            tmp_path / "sealed-evidence",
            tmp_path / "analysis",
            generated_at_utc="2026-07-21T20:00:00Z",
        )

def test_source_profiles_separate_synthetic_and_authorized_provenance() -> None:
    synthetic = _analysis_source_profile("synthetic_fixture")
    sealed = _analysis_source_profile("sealed_evidence")

    assert synthetic.execution_authorized is False
    assert synthetic.metadata_status == "generated_unsealed_synthetic_implementation_output"
    assert synthetic.summary_status == "synthetic_implementation_validation_only"
    assert sealed.execution_authorized is True
    assert sealed.metadata_status == "generated_unsealed_authorized_analysis_output"
    assert sealed.summary_status == "generated_unsealed_authorized_descriptive_analysis"

    with pytest.raises(Stage3BMatchedAnalysisError, match="unsupported analysis source kind"):
        _analysis_source_profile("unknown")


def test_synthetic_engine_rejects_repetition_identity_mismatch(
    tmp_path: Path,
) -> None:
    fixture = tmp_path / "fixture"
    _write_full_synthetic_fixture(fixture)
    rows = _read_csv(fixture / "profiling_repetitions.csv")
    rows[0]["candidate_id"] = "composite_vjp"
    _write_csv(fixture / "profiling_repetitions.csv", [dict(row) for row in rows])

    with pytest.raises(Stage3BMatchedAnalysisError, match="repetition identity differs"):
        generate_synthetic_matched_analysis(
            fixture,
            tmp_path / "analysis",
            generated_at_utc="2026-07-21T20:00:00Z",
        )


def test_synthetic_engine_rejects_repetition_aggregate_mismatch(
    tmp_path: Path,
) -> None:
    fixture = tmp_path / "fixture"
    _write_full_synthetic_fixture(fixture)
    rows = _read_csv(fixture / "profiling_repetitions.csv")
    target_cell = rows[0]["cell_id"]
    for row in rows:
        if row["cell_id"] == target_cell:
            row["primary_device_time_median_us"] = str(
                float(row["primary_device_time_median_us"]) * 2.0
            )
    _write_csv(fixture / "profiling_repetitions.csv", [dict(row) for row in rows])

    with pytest.raises(Stage3BMatchedAnalysisError, match="compact aggregate differs"):
        generate_synthetic_matched_analysis(
            fixture,
            tmp_path / "analysis",
            generated_at_utc="2026-07-21T20:00:00Z",
        )


def test_synthetic_engine_rejects_profiling_summary_mismatch(
    tmp_path: Path,
) -> None:
    fixture = tmp_path / "fixture"
    _write_full_synthetic_fixture(fixture)
    rows = _read_csv(fixture / "profiling_summary.csv")
    rows[0]["primary_device_time_median_us"] = str(
        float(rows[0]["primary_device_time_median_us"]) * 2.0
    )
    _write_csv(fixture / "profiling_summary.csv", [dict(row) for row in rows])

    with pytest.raises(Stage3BMatchedAnalysisError, match="compact aggregate differs"):
        generate_synthetic_matched_analysis(
            fixture,
            tmp_path / "analysis",
            generated_at_utc="2026-07-21T20:00:00Z",
        )
