"""Registered descriptive analysis for Stage 3B matched profiling.

The computational engine is implemented and validated against synthetic fixtures.
Execution against the immutable sealed evidence remains fail-closed until a separate
machine-readable authorization is merged.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import shutil
import statistics
import subprocess
import tempfile
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Final, cast

import matplotlib
import numpy as np

matplotlib.use("Agg")
from matplotlib import pyplot as plt  # noqa: E402

from torch2pc_thesis.stage3b_matched_analysis_protocol import (
    ALL_CANDIDATES,
    BASELINE,
    BATCH_SIZES,
    CANDIDATES,
    DEPTHS,
    FIXEDPRED_MIN_DEVICE_REDUCTION,
    MAX_DEVICE_REGRESSION,
    MAX_PEAK_MEMORY_GROWTH,
    METHODS,
    MODEL_SEEDS,
    PARETO_EPSILON,
    STRICT_MIN_DEVICE_REDUCTION,
    WIDTHS,
)

ANALYSIS_SCHEMA_VERSION: Final[int] = 2
MATCHED_CONTINUATION_THRESHOLDS: Final[dict[str, float]] = {
    "fixedpred": FIXEDPRED_MIN_DEVICE_REDUCTION,
    "strict": STRICT_MIN_DEVICE_REDUCTION,
}
MATCHED_MAX_MEMORY_GROWTH: Final[float] = MAX_PEAK_MEMORY_GROWTH
ANALYSIS_SCOPE: Final[str] = "stage3b_matched_descriptive_analysis_v1"
SYNTHETIC_MARKER_NAME: Final[str] = ".synthetic-stage3b-analysis-fixture.json"
LOCALITY_PLAIN_NAME: Final[str] = "locality_events.jsonl"
LOCALITY_ZSTD_NAME: Final[str] = "locality_events.jsonl.zst"
EXPECTED_OUTPUT_NAMES: Final[tuple[str, ...]] = (
    "paired_block_metrics.csv",
    "configuration_summary.csv",
    "candidate_method_summary.csv",
    "pareto_membership.csv",
    "locality_cell_summary.csv",
    "scaling_seed_effects.csv",
    "analysis_metadata.json",
    "analysis_summary.json",
    "engineering_decision.json",
    "REPORT.md",
    "REPORT_EN.md",
    "device_time_ratio_heatmap.pdf",
    "peak_memory_ratio_heatmap.pdf",
    "structural_cost_ratio_heatmap.pdf",
    "scaling_effects.pdf",
    "pareto_membership.pdf",
    "seed_consistency.pdf",
    "SHA256SUMS",
)
PARETO_METRICS: Final[tuple[str, ...]] = (
    "device_time_ratio_to_baseline",
    "peak_allocated_ratio_to_baseline",
    "peak_reserved_ratio_to_baseline",
    "saved_tensor_bytes_ratio_to_baseline",
    "state_vjp_calls_ratio_to_baseline",
    "graph_span_ratio_to_baseline",
    "dependency_radius_ratio_to_baseline",
)
CELL_METRIC_COLUMNS: Final[dict[str, str]] = {
    "device_time_ratio_to_baseline": "primary_device_time_us",
    "host_time_ratio_to_baseline": "primary_host_time_us",
    "peak_allocated_ratio_to_baseline": "primary_peak_allocated_bytes",
    "peak_reserved_ratio_to_baseline": "primary_peak_reserved_bytes",
    "saved_tensor_bytes_ratio_to_baseline": "saved_tensor_bytes",
    "state_vjp_calls_ratio_to_baseline": "state_vjp_calls",
    "graph_span_ratio_to_baseline": "graph_span",
    "dependency_radius_ratio_to_baseline": "dependency_radius",
}
REQUIRED_CELL_COLUMNS: Final[tuple[str, ...]] = (
    "cell_id",
    "block_id",
    "candidate_id",
    "method",
    "depth",
    "width",
    "batch_size",
    "model_seed",
    "primary_host_time_us",
    "primary_device_time_us",
    "primary_peak_allocated_bytes",
    "primary_peak_reserved_bytes",
    "observer_cost_ms",
    "saved_tensor_bytes",
    "state_vjp_calls",
    "graph_span",
    "dependency_radius",
    "fallback_validation_status",
)
REQUIRED_REPETITION_COLUMNS: Final[tuple[str, ...]] = (
    "cell_id",
    "block_id",
    "candidate_id",
    "method",
    "depth",
    "width",
    "batch_size",
    "model_seed",
    "repetition",
    "primary_host_time_median_us",
    "primary_device_time_median_us",
    "primary_peak_allocated_max_bytes",
    "primary_peak_reserved_max_bytes",
    "observer_cost_median_ms",
    "saved_tensor_bytes_median",
    "state_vjp_calls_median",
    "graph_span_max",
    "dependency_radius_max",
    "graph_lifetimes",
    "feedback_operator",
    "fallback_validation_cost_ms",
    "fallback_validation_status",
)
REQUIRED_SUMMARY_COLUMNS: Final[tuple[str, ...]] = (
    "candidate_id",
    "method",
    "depth",
    "width",
    "batch_size",
    "model_seed_count",
    "primary_host_time_median_us",
    "primary_device_time_median_us",
    "primary_peak_allocated_median_bytes",
    "primary_peak_reserved_median_bytes",
    "observer_cost_median_ms",
    "saved_tensor_bytes_median",
    "state_vjp_calls_median",
    "graph_span_max",
    "dependency_radius_max",
)
REQUIRED_LOCALITY_FIELDS: Final[tuple[str, ...]] = (
    "cell_id",
    "block_id",
    "candidate_id",
    "method",
    "repetition",
    "step",
    "logical_edge_count",
    "graph_island_count",
    "graph_module_set",
    "graph_lifetime",
    "orchestration_barriers",
)


class Stage3BMatchedAnalysisError(RuntimeError):
    """Raised when registered descriptive analysis cannot be completed safely."""


@dataclass(frozen=True)
class AnalysisInputPaths:
    """Compact and locality inputs consumed by the registered engine."""

    cells: Path
    repetitions: Path
    summary: Path
    locality: Path


@dataclass(frozen=True)
class SyntheticFixtureIdentity:
    """Verified marker for a synthetic-only implementation fixture."""

    fixture_id: str
    generated_by: str


@dataclass(frozen=True)
class AnalysisSourceProfile:
    """Source-specific provenance emitted by the shared analysis engine."""

    metadata_status: str
    summary_status: str
    execution_authorized: bool


def _analysis_source_profile(source_kind: str) -> AnalysisSourceProfile:
    if source_kind == "synthetic_fixture":
        return AnalysisSourceProfile(
            metadata_status="generated_unsealed_synthetic_implementation_output",
            summary_status="synthetic_implementation_validation_only",
            execution_authorized=False,
        )
    if source_kind == "sealed_evidence":
        return AnalysisSourceProfile(
            metadata_status="generated_unsealed_authorized_analysis_output",
            summary_status="generated_unsealed_authorized_descriptive_analysis",
            execution_authorized=True,
        )
    raise Stage3BMatchedAnalysisError(f"unsupported analysis source kind: {source_kind}")


def sha256_file(path: Path) -> str:
    """Return SHA-256 without loading the whole file into memory."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_bytes(value: Mapping[str, object]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _read_csv(path: Path, required: Sequence[str]) -> list[dict[str, str]]:
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            columns = tuple(reader.fieldnames or ())
            rows = list(reader)
    except OSError as exc:
        raise Stage3BMatchedAnalysisError(f"cannot read CSV: {path}") from exc
    missing = sorted(set(required) - set(columns))
    if missing:
        raise Stage3BMatchedAnalysisError(f"CSV columns missing in {path}: {missing}")
    if not rows:
        raise Stage3BMatchedAnalysisError(f"CSV is empty: {path}")
    return rows


def _write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    if not rows:
        raise Stage3BMatchedAnalysisError(f"cannot write empty CSV: {path}")
    columns = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            if list(row.keys()) != columns:
                raise Stage3BMatchedAnalysisError(f"CSV schema differs within table: {path}")
            writer.writerow(row)


def _finite_number(row: Mapping[str, str], key: str) -> float:
    try:
        value = float(row[key])
    except (KeyError, ValueError) as exc:
        raise Stage3BMatchedAnalysisError(f"invalid numeric field: {key}") from exc
    if not math.isfinite(value):
        raise Stage3BMatchedAnalysisError(f"non-finite numeric field: {key}")
    return value


def _integer(row: Mapping[str, str], key: str) -> int:
    value = _finite_number(row, key)
    integer = int(value)
    if value != float(integer):
        raise Stage3BMatchedAnalysisError(f"field is not integral: {key}")
    return integer


def _positive_ratio(candidate: float, baseline: float, *, label: str) -> float:
    if baseline <= 0.0:
        raise Stage3BMatchedAnalysisError(f"baseline denominator is nonpositive: {label}")
    ratio = candidate / baseline
    if not math.isfinite(ratio) or ratio <= 0.0:
        raise Stage3BMatchedAnalysisError(f"invalid positive ratio: {label}")
    return ratio


def _median(values: Sequence[float]) -> float:
    if not values:
        raise Stage3BMatchedAnalysisError("cannot calculate an empty median")
    return float(statistics.median(values))


def _minimum(values: Sequence[float]) -> float:
    if not values:
        raise Stage3BMatchedAnalysisError("cannot calculate an empty minimum")
    return min(values)


def _maximum(values: Sequence[float]) -> float:
    if not values:
        raise Stage3BMatchedAnalysisError("cannot calculate an empty maximum")
    return max(values)


def _load_synthetic_marker(root: Path) -> SyntheticFixtureIdentity:
    marker = root / SYNTHETIC_MARKER_NAME
    try:
        raw = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Stage3BMatchedAnalysisError(
            f"synthetic fixture marker is missing or invalid: {marker}"
        ) from exc
    if not isinstance(raw, dict):
        raise Stage3BMatchedAnalysisError("synthetic fixture marker must be an object")
    expected = {
        "schema_version": 1,
        "synthetic_fixture": True,
        "test_dataset_access": False,
        "matched_cell_count": 288,
        "matched_block_count": 96,
        "repetition_count": 1440,
    }
    for key, value in expected.items():
        if raw.get(key) != value:
            raise Stage3BMatchedAnalysisError(
                f"synthetic fixture marker differs for {key}: {raw.get(key)!r}"
            )
    fixture_id = raw.get("fixture_id")
    generated_by = raw.get("generated_by")
    if not isinstance(fixture_id, str) or not fixture_id:
        raise Stage3BMatchedAnalysisError("synthetic fixture_id is required")
    if not isinstance(generated_by, str) or not generated_by:
        raise Stage3BMatchedAnalysisError("synthetic generated_by is required")
    return SyntheticFixtureIdentity(fixture_id=fixture_id, generated_by=generated_by)


def synthetic_input_paths(root: Path) -> AnalysisInputPaths:
    """Resolve a validated synthetic fixture input set."""

    resolved = root.expanduser().resolve()
    _load_synthetic_marker(resolved)
    locality = resolved / LOCALITY_PLAIN_NAME
    return AnalysisInputPaths(
        cells=resolved / "profiling_cells.csv",
        repetitions=resolved / "profiling_repetitions.csv",
        summary=resolved / "profiling_summary.csv",
        locality=locality,
    )


def _assert_close(observed: float, expected: float, *, label: str) -> None:
    if not math.isclose(observed, expected, rel_tol=1e-12, abs_tol=1e-9):
        raise Stage3BMatchedAnalysisError(
            f"compact aggregate differs for {label}: {observed!r} != {expected!r}"
        )


def _validate_repetition_consistency(
    cells: Sequence[Mapping[str, str]],
    repetitions: Sequence[Mapping[str, str]],
) -> None:
    cells_by_id = {row["cell_id"]: row for row in cells}
    repetitions_by_cell: defaultdict[str, list[Mapping[str, str]]] = defaultdict(list)
    for repetition in repetitions:
        cell_id = repetition["cell_id"]
        cell = cells_by_id.get(cell_id)
        if cell is None:
            raise Stage3BMatchedAnalysisError(f"repetition references unknown cell: {cell_id}")
        repetitions_by_cell[cell_id].append(repetition)
        for key in (
            "block_id",
            "candidate_id",
            "method",
            "depth",
            "width",
            "batch_size",
            "model_seed",
            "graph_lifetimes",
            "feedback_operator",
            "fallback_validation_cost_ms",
            "fallback_validation_status",
        ):
            if repetition[key] != cell[key]:
                raise Stage3BMatchedAnalysisError(
                    f"repetition identity differs: {cell_id}/{key}"
                )

    aggregation_spec: tuple[tuple[str, str, str], ...] = (
        ("primary_host_time_us", "primary_host_time_median_us", "median"),
        ("primary_device_time_us", "primary_device_time_median_us", "median"),
        (
            "primary_peak_allocated_bytes",
            "primary_peak_allocated_max_bytes",
            "maximum",
        ),
        (
            "primary_peak_reserved_bytes",
            "primary_peak_reserved_max_bytes",
            "maximum",
        ),
        ("observer_cost_ms", "observer_cost_median_ms", "median"),
        ("saved_tensor_bytes", "saved_tensor_bytes_median", "median"),
        ("state_vjp_calls", "state_vjp_calls_median", "median"),
        ("graph_span", "graph_span_max", "maximum"),
        ("dependency_radius", "dependency_radius_max", "maximum"),
    )
    for cell_id, cell in cells_by_id.items():
        rows = repetitions_by_cell[cell_id]
        if len(rows) != 5:
            raise Stage3BMatchedAnalysisError(
                f"repetition count differs within cell: {cell_id}/{len(rows)}"
            )
        indices = {_integer(row, "repetition") for row in rows}
        if indices != set(range(5)):
            raise Stage3BMatchedAnalysisError(
                f"repetition indices differ within cell: {cell_id}"
            )
        for cell_column, repetition_column, reducer in aggregation_spec:
            values = [_finite_number(row, repetition_column) for row in rows]
            expected = _median(values) if reducer == "median" else _maximum(values)
            _assert_close(
                _finite_number(cell, cell_column),
                expected,
                label=f"{cell_id}/{cell_column}",
            )


def _validate_summary_consistency(
    cells: Sequence[Mapping[str, str]],
    summary: Sequence[Mapping[str, str]],
) -> None:
    if len(summary) != 96:
        raise Stage3BMatchedAnalysisError(f"profiling summary row count differs: {len(summary)}")

    configuration_cells: defaultdict[
        tuple[str, str, int, int, int], list[Mapping[str, str]]
    ] = defaultdict(list)
    for cell in cells:
        configuration_cells[
            (
                cell["candidate_id"],
                cell["method"],
                _integer(cell, "depth"),
                _integer(cell, "width"),
                _integer(cell, "batch_size"),
            )
        ].append(cell)

    summary_by_key: dict[tuple[str, str, int, int, int], Mapping[str, str]] = {}
    for row in summary:
        key = (
            row["candidate_id"],
            row["method"],
            _integer(row, "depth"),
            _integer(row, "width"),
            _integer(row, "batch_size"),
        )
        if key in summary_by_key:
            raise Stage3BMatchedAnalysisError(f"duplicate profiling summary row: {key}")
        summary_by_key[key] = row

    if set(summary_by_key) != set(configuration_cells):
        raise Stage3BMatchedAnalysisError("profiling summary configuration coverage differs")

    aggregation_spec: tuple[tuple[str, str, str], ...] = (
        ("primary_host_time_median_us", "primary_host_time_us", "median"),
        ("primary_device_time_median_us", "primary_device_time_us", "median"),
        (
            "primary_peak_allocated_median_bytes",
            "primary_peak_allocated_bytes",
            "median",
        ),
        (
            "primary_peak_reserved_median_bytes",
            "primary_peak_reserved_bytes",
            "median",
        ),
        ("observer_cost_median_ms", "observer_cost_ms", "median"),
        ("saved_tensor_bytes_median", "saved_tensor_bytes", "median"),
        ("state_vjp_calls_median", "state_vjp_calls", "median"),
        ("graph_span_max", "graph_span", "maximum"),
        ("dependency_radius_max", "dependency_radius", "maximum"),
    )
    for key, cell_rows in configuration_cells.items():
        summary_row = summary_by_key[key]
        seeds = {_integer(row, "model_seed") for row in cell_rows}
        if seeds != set(MODEL_SEEDS) or _integer(summary_row, "model_seed_count") != 3:
            raise Stage3BMatchedAnalysisError(
                f"profiling summary seed coverage differs: {key}"
            )
        for summary_column, cell_column, reducer in aggregation_spec:
            values = [_finite_number(row, cell_column) for row in cell_rows]
            expected = _median(values) if reducer == "median" else _maximum(values)
            _assert_close(
                _finite_number(summary_row, summary_column),
                expected,
                label=f"summary/{key}/{summary_column}",
            )


def _validate_compact_matrix(
    cells: Sequence[Mapping[str, str]],
    repetitions: Sequence[Mapping[str, str]],
    summary: Sequence[Mapping[str, str]],
) -> None:
    if len(cells) != 288:
        raise Stage3BMatchedAnalysisError(f"cell row count differs: {len(cells)}")
    if len(repetitions) != 1440:
        raise Stage3BMatchedAnalysisError(f"repetition row count differs: {len(repetitions)}")
    cell_ids = [row["cell_id"] for row in cells]
    if len(set(cell_ids)) != 288:
        raise Stage3BMatchedAnalysisError("cell IDs are not unique")
    block_ids = {row["block_id"] for row in cells}
    if len(block_ids) != 96:
        raise Stage3BMatchedAnalysisError("matched block count differs")
    if Counter(row["candidate_id"] for row in cells) != Counter(
        {candidate: 96 for candidate in ALL_CANDIDATES}
    ):
        raise Stage3BMatchedAnalysisError("candidate matrix differs")
    if Counter(row["method"] for row in cells) != Counter({method: 144 for method in METHODS}):
        raise Stage3BMatchedAnalysisError("method matrix differs")
    if Counter(_integer(row, "model_seed") for row in cells) != Counter(
        {seed: 96 for seed in MODEL_SEEDS}
    ):
        raise Stage3BMatchedAnalysisError("model-seed matrix differs")

    expected_configurations = {
        (method, depth, width, batch_size, seed)
        for method in METHODS
        for depth in DEPTHS
        for width in WIDTHS
        for batch_size in BATCH_SIZES
        for seed in MODEL_SEEDS
    }
    observed_configurations = {
        (
            row["method"],
            _integer(row, "depth"),
            _integer(row, "width"),
            _integer(row, "batch_size"),
            _integer(row, "model_seed"),
        )
        for row in cells
    }
    if observed_configurations != expected_configurations:
        raise Stage3BMatchedAnalysisError("configuration coverage differs")

    block_candidates: defaultdict[str, set[str]] = defaultdict(set)
    for row in cells:
        block_candidates[row["block_id"]].add(row["candidate_id"])
        for metric_column in CELL_METRIC_COLUMNS.values():
            _finite_number(row, metric_column)
        _finite_number(row, "observer_cost_ms")
    if any(value != set(ALL_CANDIDATES) for value in block_candidates.values()):
        raise Stage3BMatchedAnalysisError("candidate coverage differs within a block")

    repetition_keys = {(row["cell_id"], _integer(row, "repetition")) for row in repetitions}
    if len(repetition_keys) != 1440:
        raise Stage3BMatchedAnalysisError("repetition keys are not unique")
    if Counter(_integer(row, "repetition") for row in repetitions) != Counter(
        {index: 288 for index in range(5)}
    ):
        raise Stage3BMatchedAnalysisError("repetition coverage differs")
    if {row["cell_id"] for row in repetitions} != set(cell_ids):
        raise Stage3BMatchedAnalysisError("repetition cells differ from compact cells")

    _validate_repetition_consistency(cells, repetitions)
    _validate_summary_consistency(cells, summary)


def _paired_rows(cells: Sequence[Mapping[str, str]]) -> list[dict[str, object]]:
    by_block: defaultdict[str, dict[str, Mapping[str, str]]] = defaultdict(dict)
    for row in cells:
        block_id = row["block_id"]
        candidate_id_from_row = row["candidate_id"]
        if candidate_id_from_row in by_block[block_id]:
            raise Stage3BMatchedAnalysisError(
                f"duplicate candidate in block: {block_id}/{candidate_id_from_row}"
            )
        by_block[block_id][candidate_id_from_row] = row

    rows: list[dict[str, object]] = []
    for block_id in sorted(by_block):
        alternatives = by_block[block_id]
        if set(alternatives) != set(ALL_CANDIDATES):
            raise Stage3BMatchedAnalysisError(f"block candidate set differs: {block_id}")
        baseline = alternatives[BASELINE]
        identity = {
            "method": baseline["method"],
            "depth": _integer(baseline, "depth"),
            "width": _integer(baseline, "width"),
            "batch_size": _integer(baseline, "batch_size"),
            "model_seed": _integer(baseline, "model_seed"),
        }
        for candidate_id in CANDIDATES:
            candidate_row = alternatives[candidate_id]
            for key, expected in identity.items():
                observed: object
                if key in {"depth", "width", "batch_size", "model_seed"}:
                    observed = _integer(candidate_row, key)
                else:
                    observed = candidate_row[key]
                if observed != expected:
                    raise Stage3BMatchedAnalysisError(
                        f"matched identity differs: {block_id}/{candidate_id}/{key}"
                    )
            ratios = {
                ratio_name: _positive_ratio(
                    _finite_number(candidate_row, source_column),
                    _finite_number(baseline, source_column),
                    label=f"{block_id}/{candidate_id}/{source_column}",
                )
                for ratio_name, source_column in CELL_METRIC_COLUMNS.items()
            }
            device_ratio = ratios["device_time_ratio_to_baseline"]
            allocated_ratio = ratios["peak_allocated_ratio_to_baseline"]
            reserved_ratio = ratios["peak_reserved_ratio_to_baseline"]
            rows.append(
                {
                    "block_id": block_id,
                    "candidate_id": candidate_id,
                    **identity,
                    **ratios,
                    "device_time_reduction": 1.0 - device_ratio,
                    "device_speedup": 1.0 / device_ratio,
                    "peak_allocated_growth": allocated_ratio - 1.0,
                    "peak_reserved_growth": reserved_ratio - 1.0,
                    "candidate_observer_cost_ms": _finite_number(candidate_row, "observer_cost_ms"),
                    "baseline_observer_cost_ms": _finite_number(baseline, "observer_cost_ms"),
                    "fallback_validation_status": candidate_row["fallback_validation_status"],
                }
            )
    if len(rows) != 192:
        raise Stage3BMatchedAnalysisError(f"paired row count differs: {len(rows)}")
    return rows


def _metric_summary(values: Sequence[float], prefix: str) -> dict[str, object]:
    return {
        f"median_{prefix}": _median(values),
        f"minimum_{prefix}": _minimum(values),
        f"maximum_{prefix}": _maximum(values),
    }


def _configuration_seed_groups(
    paired: Sequence[Mapping[str, object]],
) -> dict[tuple[str, str, int, int, int], list[Mapping[str, object]]]:
    grouped: defaultdict[tuple[str, str, int, int, int], list[Mapping[str, object]]] = defaultdict(
        list
    )
    for row in paired:
        grouped[
            (
                str(row["candidate_id"]),
                str(row["method"]),
                int(cast(int, row["depth"])),
                int(cast(int, row["width"])),
                int(cast(int, row["batch_size"])),
            )
        ].append(row)
    if len(grouped) != 64:
        raise Stage3BMatchedAnalysisError(f"candidate configuration count differs: {len(grouped)}")
    if any(len(rows) != 3 for rows in grouped.values()):
        raise Stage3BMatchedAnalysisError("configuration seed coverage differs")
    return dict(grouped)


def _pareto_membership(
    grouped: Mapping[tuple[str, str, int, int, int], Sequence[Mapping[str, object]]],
) -> list[dict[str, object]]:
    by_configuration: defaultdict[tuple[str, int, int, int], dict[str, tuple[float, ...]]] = (
        defaultdict(dict)
    )
    for (candidate, method, depth, width, batch), rows in grouped.items():
        by_configuration[(method, depth, width, batch)][candidate] = tuple(
            _median([float(cast(float, row[metric])) for row in rows]) for metric in PARETO_METRICS
        )
    for config in by_configuration.values():
        config[BASELINE] = tuple(1.0 for _ in PARETO_METRICS)

    output: list[dict[str, object]] = []
    for (method, depth, width, batch), vectors in sorted(by_configuration.items()):
        if set(vectors) != set(ALL_CANDIDATES):
            raise Stage3BMatchedAnalysisError("Pareto alternatives differ")
        for alternative in ALL_CANDIDATES:
            vector = vectors[alternative]
            dominated_by = []
            for other in ALL_CANDIDATES:
                if other == alternative:
                    continue
                other_vector = vectors[other]
                all_not_worse = all(
                    left <= right + PARETO_EPSILON
                    for left, right in zip(other_vector, vector, strict=True)
                )
                at_least_one_better = any(
                    left < right - PARETO_EPSILON
                    for left, right in zip(other_vector, vector, strict=True)
                )
                if all_not_worse and at_least_one_better:
                    dominated_by.append(other)
            output.append(
                {
                    "candidate_id": alternative,
                    "method": method,
                    "depth": depth,
                    "width": width,
                    "batch_size": batch,
                    **{
                        f"median_{metric}": value
                        for metric, value in zip(PARETO_METRICS, vector, strict=True)
                    },
                    "dominated_by_count": len(dominated_by),
                    "dominated_by_json": json.dumps(sorted(dominated_by), separators=(",", ":")),
                    "pareto_admissible": len(dominated_by) == 0,
                }
            )
    if len(output) != 96:
        raise Stage3BMatchedAnalysisError(f"Pareto membership row count differs: {len(output)}")
    return output


def _configuration_rows(
    grouped: Mapping[tuple[str, str, int, int, int], Sequence[Mapping[str, object]]],
    pareto: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    pareto_lookup = {
        (
            str(row["candidate_id"]),
            str(row["method"]),
            int(cast(int, row["depth"])),
            int(cast(int, row["width"])),
            int(cast(int, row["batch_size"])),
        ): bool(row["pareto_admissible"])
        for row in pareto
    }
    output: list[dict[str, object]] = []
    for key, seed_rows in sorted(grouped.items()):
        candidate, method, depth, width, batch = key
        device_ratios = [
            float(cast(float, row["device_time_ratio_to_baseline"])) for row in seed_rows
        ]
        allocated = [
            float(cast(float, row["peak_allocated_ratio_to_baseline"])) for row in seed_rows
        ]
        reserved = [float(cast(float, row["peak_reserved_ratio_to_baseline"])) for row in seed_rows]
        threshold = (
            FIXEDPRED_MIN_DEVICE_REDUCTION if method == "fixedpred" else STRICT_MIN_DEVICE_REDUCTION
        )
        median_device_ratio = _median(device_ratios)
        median_reduction = 1.0 - median_device_ratio
        timing_threshold_passed = median_reduction >= threshold
        seed_regression_passed = max(device_ratios) <= 1.0 + MAX_DEVICE_REGRESSION
        allocated_passed = _median(allocated) <= 1.0 + MAX_PEAK_MEMORY_GROWTH
        reserved_passed = _median(reserved) <= 1.0 + MAX_PEAK_MEMORY_GROWTH
        pareto_admissible = pareto_lookup[key]
        row: dict[str, object] = {
            "candidate_id": candidate,
            "method": method,
            "depth": depth,
            "width": width,
            "batch_size": batch,
            "model_seed_count": len(seed_rows),
            "device_improvement_seed_count": sum(value < 1.0 for value in device_ratios),
            "device_nonregression_seed_count": sum(
                value <= 1.0 + MAX_DEVICE_REGRESSION for value in device_ratios
            ),
        }
        for metric in (
            "device_time_ratio_to_baseline",
            "host_time_ratio_to_baseline",
            *PARETO_METRICS[1:],
        ):
            values = [float(cast(float, seed_row[metric])) for seed_row in seed_rows]
            row.update(_metric_summary(values, metric))
        row.update(
            {
                "median_device_time_reduction": median_reduction,
                "minimum_device_time_reduction": 1.0 - max(device_ratios),
                "maximum_device_time_reduction": 1.0 - min(device_ratios),
                "maximum_seed_device_time_ratio": max(device_ratios),
                "method_device_reduction_threshold": threshold,
                "timing_threshold_passed": timing_threshold_passed,
                "seed_regression_limit_passed": seed_regression_passed,
                "allocated_memory_limit_passed": allocated_passed,
                "reserved_memory_limit_passed": reserved_passed,
                "pareto_admissible": pareto_admissible,
                "configuration_qualified": all(
                    (
                        timing_threshold_passed,
                        seed_regression_passed,
                        allocated_passed,
                        reserved_passed,
                        pareto_admissible,
                    )
                ),
            }
        )
        output.append(row)
    if len(output) != 64:
        raise Stage3BMatchedAnalysisError(f"configuration summary row count differs: {len(output)}")
    return output


def _leave_one_seed_out(
    rows: Sequence[Mapping[str, object]],
) -> dict[str, float]:
    by_configuration: defaultdict[tuple[int, int, int], dict[int, float]] = defaultdict(dict)
    for row in rows:
        configuration = (
            int(cast(int, row["depth"])),
            int(cast(int, row["width"])),
            int(cast(int, row["batch_size"])),
        )
        seed = int(cast(int, row["model_seed"]))
        if seed in by_configuration[configuration]:
            raise Stage3BMatchedAnalysisError("duplicate seed in leave-one-seed-out configuration")
        by_configuration[configuration][seed] = float(
            cast(float, row["device_time_ratio_to_baseline"])
        )
    if len(by_configuration) != 16:
        raise Stage3BMatchedAnalysisError("leave-one-seed-out configuration count differs")
    output: dict[str, float] = {}
    for omitted in MODEL_SEEDS:
        configuration_medians = []
        for seed_values in by_configuration.values():
            if set(seed_values) != set(MODEL_SEEDS):
                raise Stage3BMatchedAnalysisError("leave-one-seed-out seed coverage differs")
            retained = [value for seed, value in seed_values.items() if seed != omitted]
            configuration_medians.append(_median(retained))
        output[str(omitted)] = 1.0 - _median(configuration_medians)
    return output


def _candidate_method_rows(
    configurations: Sequence[Mapping[str, object]],
    paired: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    config_groups: defaultdict[tuple[str, str], list[Mapping[str, object]]] = defaultdict(list)
    paired_groups: defaultdict[tuple[str, str], list[Mapping[str, object]]] = defaultdict(list)
    for row in configurations:
        config_groups[(str(row["candidate_id"]), str(row["method"]))].append(row)
    for row in paired:
        paired_groups[(str(row["candidate_id"]), str(row["method"]))].append(row)

    output: list[dict[str, object]] = []
    for key in sorted(config_groups):
        candidate, method = key
        rows = config_groups[key]
        qualified = sum(bool(row["configuration_qualified"]) for row in rows)
        status = (
            "retain" if qualified == 16 else "conditional" if qualified > 0 else "reject_or_revise"
        )
        summary: dict[str, object] = {
            "candidate_id": candidate,
            "method": method,
            "configuration_count": len(rows),
            "qualified_configuration_count": qualified,
            "pareto_admissible_configuration_count": sum(
                bool(row["pareto_admissible"]) for row in rows
            ),
            "status": status,
            "leave_one_seed_out_device_time_reduction_json": json.dumps(
                _leave_one_seed_out(paired_groups[key]),
                sort_keys=True,
                separators=(",", ":"),
            ),
        }
        for metric in (
            "median_device_time_ratio_to_baseline",
            "median_host_time_ratio_to_baseline",
            "median_peak_allocated_ratio_to_baseline",
            "median_peak_reserved_ratio_to_baseline",
            "median_saved_tensor_bytes_ratio_to_baseline",
            "median_state_vjp_calls_ratio_to_baseline",
            "median_graph_span_ratio_to_baseline",
            "median_dependency_radius_ratio_to_baseline",
        ):
            values = [float(cast(float, row[metric])) for row in rows]
            summary.update(_metric_summary(values, f"configuration_{metric}"))
        device_reductions = [
            float(cast(float, row["median_device_time_reduction"])) for row in rows
        ]
        summary.update(_metric_summary(device_reductions, "configuration_device_time_reduction"))
        summary["minimum_device_improvement_seed_count"] = min(
            int(cast(int, row["device_improvement_seed_count"])) for row in rows
        )
        output.append(summary)
    if len(output) != 4:
        raise Stage3BMatchedAnalysisError(
            f"candidate-method summary row count differs: {len(output)}"
        )
    return output


def _locality_stream(path: Path) -> Iterable[dict[str, object]]:
    if path.name.endswith(".zst"):
        command = ["zstd", "--long=27", "-dc", str(path)]
        try:
            process = subprocess.Popen(  # noqa: S603
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
            )
        except OSError as exc:
            raise Stage3BMatchedAnalysisError("cannot start zstd decoder") from exc
        if process.stdout is None:
            raise Stage3BMatchedAnalysisError("zstd stdout is unavailable")
        try:
            yield from _parse_locality_lines(process.stdout, path)
        except Exception:
            process.kill()
            process.wait()
            raise
        finally:
            process.stdout.close()
        stderr = process.stderr.read() if process.stderr is not None else ""
        return_code = process.wait()
        if return_code != 0:
            raise Stage3BMatchedAnalysisError(f"zstd locality decoding failed: {stderr.strip()}")
        return
    try:
        with path.open(encoding="utf-8") as handle:
            yield from _parse_locality_lines(handle, path)
    except OSError as exc:
        raise Stage3BMatchedAnalysisError(f"cannot read locality stream: {path}") from exc


def _object_int(value: object, *, label: str) -> int:
    if isinstance(value, bool):
        raise Stage3BMatchedAnalysisError(f"invalid integer field: {label}")
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError as exc:
            raise Stage3BMatchedAnalysisError(f"invalid integer field: {label}") from exc
    raise Stage3BMatchedAnalysisError(f"invalid integer field: {label}")


def _object_float(value: object, *, label: str) -> float:
    if isinstance(value, bool):
        raise Stage3BMatchedAnalysisError(f"invalid numeric field: {label}")
    if isinstance(value, int | float | str):
        try:
            number = float(value)
        except ValueError as exc:
            raise Stage3BMatchedAnalysisError(f"invalid numeric field: {label}") from exc
        if math.isfinite(number):
            return number
    raise Stage3BMatchedAnalysisError(f"invalid numeric field: {label}")


def _parse_locality_lines(
    handle: IO[str],
    path: Path,
) -> Iterable[dict[str, object]]:
    for line_number, line in enumerate(handle, start=1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise Stage3BMatchedAnalysisError(
                f"invalid locality JSON at {path}:{line_number}"
            ) from exc
        if not isinstance(raw, dict):
            raise Stage3BMatchedAnalysisError(
                f"locality record is not an object at {path}:{line_number}"
            )
        record = cast(dict[str, object], raw)
        missing = sorted(set(REQUIRED_LOCALITY_FIELDS) - set(record))
        if missing:
            raise Stage3BMatchedAnalysisError(
                f"locality fields missing at {path}:{line_number}: {missing}"
            )
        yield record


def _locality_rows(
    cells: Sequence[Mapping[str, str]],
    locality_path: Path,
) -> list[dict[str, object]]:
    cell_lookup = {row["cell_id"]: row for row in cells}
    state: dict[str, dict[str, object]] = {
        cell_id: {
            "event_count": 0,
            "measured_steps": set(),
            "logical_edges": [],
            "module_ids": set(),
            "maximum_graph_island_count": 0,
            "orchestration_barriers": 0,
            "lifetimes": Counter(),
        }
        for cell_id in cell_lookup
    }
    for event in _locality_stream(locality_path):
        cell_id = str(event["cell_id"])
        if cell_id not in cell_lookup:
            raise Stage3BMatchedAnalysisError(f"locality event references unknown cell: {cell_id}")
        cell = cell_lookup[cell_id]
        for key in ("block_id", "candidate_id", "method"):
            if str(event[key]) != cell[key]:
                raise Stage3BMatchedAnalysisError(f"locality identity differs: {cell_id}/{key}")
        current = state[cell_id]
        current["event_count"] = int(cast(int, current["event_count"])) + 1
        measured_steps = cast(set[tuple[int, int]], current["measured_steps"])
        measured_steps.add(
            (
                _object_int(event["repetition"], label="repetition"),
                _object_int(event["step"], label="step"),
            )
        )
        logical_edges = cast(list[float], current["logical_edges"])
        logical_value = _object_float(event["logical_edge_count"], label="logical_edge_count")
        if not math.isfinite(logical_value) or logical_value < 0.0:
            raise Stage3BMatchedAnalysisError("invalid locality logical_edge_count")
        logical_edges.append(logical_value)
        modules_raw = event["graph_module_set"]
        if not isinstance(modules_raw, list):
            raise Stage3BMatchedAnalysisError("graph_module_set must be a list")
        module_ids = cast(set[int], current["module_ids"])
        for module in modules_raw:
            module_id = _object_int(module, label="graph_module_set")
            if module_id < 0 or module_id >= _integer(cell, "depth"):
                raise Stage3BMatchedAnalysisError(
                    f"graph module outside depth: {cell_id}/{module_id}"
                )
            module_ids.add(module_id)
        islands = _object_int(event["graph_island_count"], label="graph_island_count")
        if islands < 0:
            raise Stage3BMatchedAnalysisError("negative graph island count")
        current["maximum_graph_island_count"] = max(
            int(cast(int, current["maximum_graph_island_count"])), islands
        )
        barriers = _object_int(event["orchestration_barriers"], label="orchestration_barriers")
        if barriers < 0:
            raise Stage3BMatchedAnalysisError("negative orchestration barrier count")
        current["orchestration_barriers"] = (
            int(cast(int, current["orchestration_barriers"])) + barriers
        )
        lifetimes = cast(Counter[str], current["lifetimes"])
        lifetimes[str(event["graph_lifetime"])] += 1

    output: list[dict[str, object]] = []
    for cell_id in sorted(cell_lookup):
        cell = cell_lookup[cell_id]
        current = state[cell_id]
        event_count = int(cast(int, current["event_count"]))
        measured_steps = cast(set[tuple[int, int]], current["measured_steps"])
        if event_count < 1 or not measured_steps:
            raise Stage3BMatchedAnalysisError(f"locality coverage missing for cell: {cell_id}")
        logical_edges = cast(list[float], current["logical_edges"])
        module_ids = cast(set[int], current["module_ids"])
        lifetimes = cast(Counter[str], current["lifetimes"])
        output.append(
            {
                "cell_id": cell_id,
                "block_id": cell["block_id"],
                "candidate_id": cell["candidate_id"],
                "method": cell["method"],
                "depth": _integer(cell, "depth"),
                "width": _integer(cell, "width"),
                "batch_size": _integer(cell, "batch_size"),
                "model_seed": _integer(cell, "model_seed"),
                "event_count": event_count,
                "measured_step_count": len(measured_steps),
                "event_count_per_measured_step": event_count / len(measured_steps),
                "median_logical_edge_count_per_event": _median(logical_edges),
                "graph_module_coverage_fraction": len(module_ids) / _integer(cell, "depth"),
                "maximum_graph_island_count": int(cast(int, current["maximum_graph_island_count"])),
                "orchestration_barriers_per_measured_step": int(
                    cast(int, current["orchestration_barriers"])
                )
                / len(measured_steps),
                "graph_lifetime_distribution_json": json.dumps(
                    dict(sorted(lifetimes.items())),
                    sort_keys=True,
                    separators=(",", ":"),
                ),
            }
        )
    if len(output) != 288:
        raise Stage3BMatchedAnalysisError(f"locality summary row count differs: {len(output)}")
    return output


def _fit_scaling(
    rows: Sequence[Mapping[str, object]],
    metric: str,
) -> tuple[float, float, float, float, float, float, float, float, float]:
    x = np.array(
        [
            [
                1.0,
                math.log2(int(cast(int, row["depth"]))),
                math.log2(int(cast(int, row["width"]))),
                math.log2(int(cast(int, row["batch_size"]))),
            ]
            for row in rows
        ],
        dtype=float,
    )
    y = np.array(
        [math.log2(float(cast(float, row[metric]))) for row in rows],
        dtype=float,
    )
    coefficients, _residuals, rank, _singular = np.linalg.lstsq(x, y, rcond=None)
    if int(rank) != 4:
        raise Stage3BMatchedAnalysisError("scaling design matrix is rank deficient")
    predicted = x @ coefficients
    residual = y - predicted
    total = float(np.sum((y - np.mean(y)) ** 2))
    squared = float(np.sum(residual**2))
    r_squared = (1.0 if squared <= 1.0e-20 else 0.0) if total <= 1.0e-24 else 1.0 - squared / total
    intercept, beta_depth, beta_width, beta_batch = [float(value) for value in coefficients]
    return (
        intercept,
        beta_depth,
        beta_width,
        beta_batch,
        2.0**beta_depth,
        2.0**beta_width,
        2.0**beta_batch,
        r_squared,
        float(np.max(np.abs(residual))),
    )


def _scaling_rows(
    paired: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    grouped: defaultdict[tuple[str, str, int], list[Mapping[str, object]]] = defaultdict(list)
    for row in paired:
        grouped[
            (
                str(row["candidate_id"]),
                str(row["method"]),
                int(cast(int, row["model_seed"])),
            )
        ].append(row)
    output: list[dict[str, object]] = []
    for (candidate, method, seed), rows in sorted(grouped.items()):
        if len(rows) != 16:
            raise Stage3BMatchedAnalysisError("scaling configuration count differs")
        for metric in PARETO_METRICS:
            (
                intercept,
                beta_depth,
                beta_width,
                beta_batch,
                multiplier_depth,
                multiplier_width,
                multiplier_batch,
                r_squared,
                maximum_residual,
            ) = _fit_scaling(rows, metric)
            output.append(
                {
                    "candidate_id": candidate,
                    "method": method,
                    "model_seed": seed,
                    "metric": metric,
                    "configuration_count": len(rows),
                    "intercept_log2": intercept,
                    "beta_log2_depth": beta_depth,
                    "beta_log2_width": beta_width,
                    "beta_log2_batch_size": beta_batch,
                    "multiplier_per_depth_doubling": multiplier_depth,
                    "multiplier_per_width_doubling": multiplier_width,
                    "multiplier_per_batch_doubling": multiplier_batch,
                    "r_squared": r_squared,
                    "maximum_absolute_log2_residual": maximum_residual,
                }
            )
    if len(output) != 84:
        raise Stage3BMatchedAnalysisError(f"scaling row count differs: {len(output)}")
    return output


def _overall_decisions(
    candidate_method: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    by_candidate: defaultdict[str, dict[str, str]] = defaultdict(dict)
    for row in candidate_method:
        by_candidate[str(row["candidate_id"])][str(row["method"])] = str(row["status"])
    candidate_records = []
    for candidate in CANDIDATES:
        methods = by_candidate[candidate]
        if set(methods) != set(METHODS):
            raise Stage3BMatchedAnalysisError("candidate method decision coverage differs")
        statuses = [methods[method] for method in METHODS]
        if all(status == "retain" for status in statuses):
            overall = "retain"
        elif any(status in {"retain", "conditional"} for status in statuses):
            overall = "conditional"
        else:
            overall = "reject_or_revise"
        candidate_records.append(
            {
                "candidate_id": candidate,
                "method_statuses": dict(sorted(methods.items())),
                "status": overall,
            }
        )
    return {
        "schema_version": ANALYSIS_SCHEMA_VERSION,
        "scope": "stage3b_matched_engineering_continuation_v1",
        "decision_scope": "engineering_continuation_not_superiority",
        "baseline_role": "mandatory_fallback_not_classified",
        "candidate_decisions": candidate_records,
        "ex_if0_opened": False,
        "policy_activation_permitted": False,
        "superiority_claim_permitted": False,
        "results_publication_permitted": False,
        "release_publication_permitted": False,
        "test_dataset_access": False,
    }


def _figure_metadata() -> dict[str, object]:
    return {
        "Creator": "torch2pc-layerwise-thesis",
        "Producer": "matplotlib",
        "CreationDate": None,
        "ModDate": None,
    }


def _save_figure(path: Path) -> None:
    plt.tight_layout()
    plt.savefig(path, format="pdf", metadata=_figure_metadata())
    plt.close()


def _heatmap(
    path: Path,
    rows: Sequence[Mapping[str, object]],
    metric: str,
    title: str,
) -> None:
    labels = [f"{candidate}/{method}" for candidate in CANDIDATES for method in METHODS]
    columns = [
        (depth, width, batch) for depth in DEPTHS for width in WIDTHS for batch in BATCH_SIZES
    ]
    lookup = {
        (
            str(row["candidate_id"]),
            str(row["method"]),
            int(cast(int, row["depth"])),
            int(cast(int, row["width"])),
            int(cast(int, row["batch_size"])),
        ): float(cast(float, row[metric]))
        for row in rows
    }
    matrix = np.array(
        [
            [lookup[(candidate, method, depth, width, batch)] for depth, width, batch in columns]
            for candidate in CANDIDATES
            for method in METHODS
        ],
        dtype=float,
    )
    plt.figure(figsize=(12, 3.5))
    image = plt.imshow(matrix, aspect="auto")
    plt.colorbar(image, label="ratio to baseline")
    plt.yticks(range(len(labels)), labels)
    plt.xticks(
        range(len(columns)),
        [f"d{d}/w{w}/b{b}" for d, w, b in columns],
        rotation=65,
        ha="right",
        fontsize=7,
    )
    plt.title(title)
    _save_figure(path)


def _plot_figures(
    root: Path,
    configurations: Sequence[Mapping[str, object]],
    pareto: Sequence[Mapping[str, object]],
    scaling: Sequence[Mapping[str, object]],
) -> None:
    _heatmap(
        root / "device_time_ratio_heatmap.pdf",
        configurations,
        "median_device_time_ratio_to_baseline",
        "Median device-time ratio by registered configuration",
    )

    memory_rows = []
    structural_rows = []
    for row in configurations:
        memory_rows.append(
            {
                **row,
                "combined_memory": max(
                    float(cast(float, row["median_peak_allocated_ratio_to_baseline"])),
                    float(cast(float, row["median_peak_reserved_ratio_to_baseline"])),
                ),
            }
        )
        structural_rows.append(
            {
                **row,
                "combined_structural": _median(
                    [float(cast(float, row[f"median_{metric}"])) for metric in PARETO_METRICS[3:]]
                ),
            }
        )
    _heatmap(
        root / "peak_memory_ratio_heatmap.pdf",
        memory_rows,
        "combined_memory",
        "Maximum of allocated and reserved peak-memory ratios",
    )
    _heatmap(
        root / "structural_cost_ratio_heatmap.pdf",
        structural_rows,
        "combined_structural",
        "Median structural-cost ratio across registered dimensions",
    )

    plt.figure(figsize=(10, 5))
    grouped_scaling: defaultdict[str, list[float]] = defaultdict(list)
    for row in scaling:
        label = f"{row['candidate_id']}/{row['method']}"
        grouped_scaling[label].append(float(cast(float, row["multiplier_per_depth_doubling"])))
    labels = sorted(grouped_scaling)
    plt.boxplot([grouped_scaling[label] for label in labels], tick_labels=labels)
    plt.ylabel("multiplier per depth doubling")
    plt.title("Descriptive scaling sensitivity across metrics and seeds")
    _save_figure(root / "scaling_effects.pdf")

    plt.figure(figsize=(8, 4))
    pareto_counts = Counter(
        str(row["candidate_id"]) for row in pareto if bool(row["pareto_admissible"])
    )
    alternatives = list(ALL_CANDIDATES)
    plt.bar(alternatives, [pareto_counts[value] for value in alternatives])
    plt.ylabel("Pareto-admissible configurations")
    plt.title("Pareto membership across 32 method/configuration cells")
    plt.xticks(rotation=20, ha="right")
    _save_figure(root / "pareto_membership.pdf")

    _heatmap(
        root / "seed_consistency.pdf",
        configurations,
        "device_improvement_seed_count",
        "Seed directional consistency for device-time improvement",
    )


def _write_reports(
    root: Path,
    candidate_method: Sequence[Mapping[str, object]],
    decisions: Mapping[str, object],
    *,
    source_kind: str,
) -> None:
    source_label_en = (
        "a synthetic implementation fixture"
        if source_kind == "synthetic_fixture"
        else "an authorized read-only evidence source"
    )
    source_label_ru = (
        "синтетической фикстуре реализации"
        if source_kind == "synthetic_fixture"
        else "авторизованном неизменяемом источнике доказательств"
    )
    lines_en = [
        "# Stage 3B matched descriptive analysis",
        "",
        f"Status: generated from {source_label_en}; output remains unsealed.",
        "",
        "## Candidate × method continuation summary",
        "",
        "| Candidate | Method | Qualified configurations | Status |",
        "|---|---:|---:|---|",
    ]
    lines_ru = [
        "# Описательный анализ сопоставленного профилирования Stage 3B",
        "",
        f"Статус: сформировано на {source_label_ru}; выход ещё не запечатан.",
        "",
        "## Сводка продолжения по кандидату и методу",
        "",
        "| Кандидат | Метод | Квалифицированные конфигурации | Статус |",
        "|---|---:|---:|---|",
    ]
    for row in candidate_method:
        values = (
            str(row["candidate_id"]),
            str(row["method"]),
            str(row["qualified_configuration_count"]),
            str(row["status"]),
        )
        lines_en.append(f"| {values[0]} | {values[1]} | {values[2]}/16 | {values[3]} |")
        lines_ru.append(f"| {values[0]} | {values[1]} | {values[2]}/16 | {values[3]} |")
    boundary_en = [
        "",
        "## Claim boundary",
        "",
        "This is a descriptive engineering continuation screen. It does not open EX-IF0, activate a policy, permit superiority language, or permit publication.",
    ]
    boundary_ru = [
        "",
        "## Граница утверждений",
        "",
        "Это описательный инженерный экран продолжения. Он не открывает EX-IF0, не активирует политику, не разрешает утверждение о превосходстве и не разрешает публикацию.",
    ]
    lines_en.extend(boundary_en)
    lines_ru.extend(boundary_ru)
    candidate_decisions = cast(list[dict[str, object]], decisions["candidate_decisions"])
    lines_en.extend(["", "## Candidate decisions", ""])
    lines_ru.extend(["", "## Решения по кандидатам", ""])
    for record in candidate_decisions:
        lines_en.append(f"- `{record['candidate_id']}`: `{record['status']}`")
        lines_ru.append(f"- `{record['candidate_id']}`: `{record['status']}`")
    (root / "REPORT.md").write_text("\n".join(lines_ru) + "\n", encoding="utf-8")
    (root / "REPORT_EN.md").write_text("\n".join(lines_en) + "\n", encoding="utf-8")


def _verify_output_inventory(root: Path) -> None:
    observed = {path.name for path in root.iterdir() if path.is_file()}
    expected = set(EXPECTED_OUTPUT_NAMES)
    if observed != expected:
        raise Stage3BMatchedAnalysisError(
            f"analysis output inventory differs: {sorted(observed ^ expected)}"
        )
    expected_rows = {
        "paired_block_metrics.csv": 192,
        "configuration_summary.csv": 64,
        "candidate_method_summary.csv": 4,
        "pareto_membership.csv": 96,
        "locality_cell_summary.csv": 288,
        "scaling_seed_effects.csv": 84,
    }
    for name, expected_count in expected_rows.items():
        rows = _read_csv(root / name, ())
        if len(rows) != expected_count:
            raise Stage3BMatchedAnalysisError(
                f"registered row count differs for {name}: {len(rows)}"
            )
    for name in EXPECTED_OUTPUT_NAMES:
        path = root / name
        if path.stat().st_size <= 0:
            raise Stage3BMatchedAnalysisError(f"analysis output is empty: {name}")
    for name in (
        "device_time_ratio_heatmap.pdf",
        "peak_memory_ratio_heatmap.pdf",
        "structural_cost_ratio_heatmap.pdf",
        "scaling_effects.pdf",
        "pareto_membership.pdf",
        "seed_consistency.pdf",
    ):
        if not (root / name).read_bytes().startswith(b"%PDF-"):
            raise Stage3BMatchedAnalysisError(f"invalid PDF output: {name}")


def _write_checksum_registry(root: Path) -> None:
    names = sorted(name for name in EXPECTED_OUTPUT_NAMES if name != "SHA256SUMS")
    content = "".join(f"{sha256_file(root / name)}  {name}\n" for name in names)
    (root / "SHA256SUMS").write_text(content, encoding="utf-8")


def validate_generated_analysis_output(root: Path) -> dict[str, object]:
    """Validate an unsealed 18-file output package and its claim boundary."""

    resolved = root.expanduser().resolve()
    if not resolved.is_dir():
        raise Stage3BMatchedAnalysisError(f"analysis output root is missing: {resolved}")
    _verify_output_inventory(resolved)
    registry = resolved / "SHA256SUMS"
    observed_names: set[str] = set()
    for line_number, raw_line in enumerate(
        registry.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        parts = raw_line.split(maxsplit=1)
        if len(parts) != 2:
            raise Stage3BMatchedAnalysisError(f"invalid analysis checksum line {line_number}")
        digest, name = parts
        name = name.removeprefix("*")
        if name in observed_names:
            raise Stage3BMatchedAnalysisError(f"duplicate analysis checksum entry: {name}")
        observed_names.add(name)
        path = resolved / name
        if not path.is_file() or sha256_file(path) != digest:
            raise Stage3BMatchedAnalysisError(f"analysis checksum failed: {name}")
    expected_names = set(EXPECTED_OUTPUT_NAMES) - {"SHA256SUMS"}
    if observed_names != expected_names:
        raise Stage3BMatchedAnalysisError("analysis checksum inventory differs")
    try:
        metadata_raw = json.loads((resolved / "analysis_metadata.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Stage3BMatchedAnalysisError("analysis metadata is unreadable") from exc
    if not isinstance(metadata_raw, dict):
        raise Stage3BMatchedAnalysisError("analysis metadata must be an object")
    metadata = cast(dict[str, object], metadata_raw)
    source_kind = metadata.get("source_kind")
    if not isinstance(source_kind, str):
        raise Stage3BMatchedAnalysisError("analysis metadata source_kind is invalid")
    source_profile = _analysis_source_profile(source_kind)
    if metadata.get("status") != source_profile.metadata_status:
        raise Stage3BMatchedAnalysisError("analysis metadata source status differs")
    if metadata.get("analysis_execution_authorized") is not source_profile.execution_authorized:
        raise Stage3BMatchedAnalysisError(
            "analysis metadata execution authorization differs"
        )
    source_identity = metadata.get("source_identity")
    if not isinstance(source_identity, dict) or not source_identity:
        raise Stage3BMatchedAnalysisError("analysis metadata source identity is invalid")
    try:
        summary_raw = json.loads(
            (resolved / "analysis_summary.json").read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise Stage3BMatchedAnalysisError("analysis summary is unreadable") from exc
    if not isinstance(summary_raw, dict):
        raise Stage3BMatchedAnalysisError("analysis summary must be an object")
    if summary_raw.get("status") != source_profile.summary_status:
        raise Stage3BMatchedAnalysisError("analysis summary source status differs")
    if summary_raw.get("source_kind") != source_kind:
        raise Stage3BMatchedAnalysisError("analysis summary source kind differs")
    if (
        summary_raw.get("analysis_execution_authorized")
        is not source_profile.execution_authorized
    ):
        raise Stage3BMatchedAnalysisError(
            "analysis summary execution authorization differs"
        )
    expected_boundary = {
        "source_evidence_read_only": True,
        "analysis_output_evidence": False,
        "results_publication_permitted": False,
        "release_publication_permitted": False,
        "test_dataset_access": False,
        "ex_if0_opened": False,
        "policy_activation_permitted": False,
        "superiority_claim_permitted": False,
    }
    for key, expected in expected_boundary.items():
        if metadata.get(key) is not expected:
            raise Stage3BMatchedAnalysisError(f"analysis metadata boundary differs: {key}")
    return metadata


def _generate_engine(
    inputs: AnalysisInputPaths,
    output_root: Path,
    *,
    source_kind: str,
    source_identity: Mapping[str, object],
    generated_at_utc: str,
) -> dict[str, object]:
    destination = output_root.expanduser().resolve()
    if destination.exists():
        raise Stage3BMatchedAnalysisError(
            f"registered output root must not already exist: {destination}"
        )
    parent = destination.parent
    parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{destination.name}.", dir=parent))
    input_paths = {
        "profiling_cells.csv": inputs.cells,
        "profiling_repetitions.csv": inputs.repetitions,
        "profiling_summary.csv": inputs.summary,
        inputs.locality.name: inputs.locality,
    }
    input_sha256_before = {name: sha256_file(path) for name, path in sorted(input_paths.items())}
    try:
        cells = _read_csv(inputs.cells, REQUIRED_CELL_COLUMNS)
        repetitions = _read_csv(inputs.repetitions, REQUIRED_REPETITION_COLUMNS)
        summary_rows = _read_csv(inputs.summary, REQUIRED_SUMMARY_COLUMNS)
        _validate_compact_matrix(cells, repetitions, summary_rows)
        source_profile = _analysis_source_profile(source_kind)
        paired = _paired_rows(cells)
        groups = _configuration_seed_groups(paired)
        pareto = _pareto_membership(groups)
        configurations = _configuration_rows(groups, pareto)
        candidate_method = _candidate_method_rows(configurations, paired)
        locality = _locality_rows(cells, inputs.locality)
        scaling = _scaling_rows(paired)
        decisions = _overall_decisions(candidate_method)

        _write_csv(temporary / "paired_block_metrics.csv", paired)
        _write_csv(temporary / "configuration_summary.csv", configurations)
        _write_csv(temporary / "candidate_method_summary.csv", candidate_method)
        _write_csv(temporary / "pareto_membership.csv", pareto)
        _write_csv(temporary / "locality_cell_summary.csv", locality)
        _write_csv(temporary / "scaling_seed_effects.csv", scaling)

        metadata: dict[str, object] = {
            "schema_version": ANALYSIS_SCHEMA_VERSION,
            "scope": ANALYSIS_SCOPE,
            "status": source_profile.metadata_status,
            "generated_at_utc": generated_at_utc,
            "source_kind": source_kind,
            "source_identity": dict(source_identity),
            "input_sha256": input_sha256_before,
            "independent_unit": "model_seed",
            "model_seed_count": 3,
            "matched_cell_count": 288,
            "matched_block_count": 96,
            "repetition_count": 1440,
            "paired_row_count": 192,
            "configuration_row_count": 64,
            "candidate_method_row_count": 4,
            "pareto_row_count": 96,
            "locality_row_count": 288,
            "scaling_row_count": 84,
            "aggregation_order": [
                "measured_steps_to_repetition",
                "repetitions_to_cell",
                "candidate_to_baseline_within_matched_block",
                "model_seeds_within_configuration",
                "configurations_within_candidate_method",
            ],
            "source_evidence_read_only": True,
            "analysis_output_evidence": False,
            "analysis_execution_authorized": source_profile.execution_authorized,
            "results_publication_permitted": False,
            "release_publication_permitted": False,
            "test_dataset_access": False,
            "ex_if0_opened": False,
            "policy_activation_permitted": False,
            "superiority_claim_permitted": False,
        }
        summary: dict[str, object] = {
            "schema_version": ANALYSIS_SCHEMA_VERSION,
            "scope": ANALYSIS_SCOPE,
            "status": source_profile.summary_status,
            "source_kind": source_kind,
            "analysis_execution_authorized": source_profile.execution_authorized,
            "candidate_method_summary": [dict(row) for row in candidate_method],
            "candidate_decisions": decisions["candidate_decisions"],
            "pareto_admissible_counts": dict(
                sorted(
                    Counter(
                        str(row["candidate_id"]) for row in pareto if bool(row["pareto_admissible"])
                    ).items()
                )
            ),
            "p_values_computed": False,
            "bootstrap_confidence_intervals_computed": False,
            "results_publication_permitted": False,
            "superiority_claim_permitted": False,
        }
        (temporary / "analysis_metadata.json").write_bytes(_json_bytes(metadata))
        (temporary / "analysis_summary.json").write_bytes(_json_bytes(summary))
        (temporary / "engineering_decision.json").write_bytes(_json_bytes(decisions))
        _write_reports(
            temporary,
            candidate_method,
            decisions,
            source_kind=source_kind,
        )
        _plot_figures(temporary, configurations, pareto, scaling)
        _write_checksum_registry(temporary)
        _verify_output_inventory(temporary)
        input_sha256_after = {name: sha256_file(path) for name, path in sorted(input_paths.items())}
        if input_sha256_after != input_sha256_before:
            raise Stage3BMatchedAnalysisError("analysis input changed during read-only execution")
        temporary.rename(destination)
        return summary
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def generate_synthetic_matched_analysis(
    fixture_root: Path,
    output_root: Path,
    *,
    generated_at_utc: str,
) -> dict[str, object]:
    """Run the registered engine only on a marked full synthetic fixture."""

    resolved = fixture_root.expanduser().resolve()
    identity = _load_synthetic_marker(resolved)
    inputs = synthetic_input_paths(resolved)
    return _generate_engine(
        inputs,
        output_root,
        source_kind="synthetic_fixture",
        source_identity={
            "fixture_id": identity.fixture_id,
            "generated_by": identity.generated_by,
        },
        generated_at_utc=generated_at_utc,
    )


def generate_matched_analysis(
    evidence_root: Path,
    output_root: Path,
    *,
    generated_at_utc: str | None = None,
) -> dict[str, object]:
    """Remain fail-closed for sealed evidence until execution authorization exists."""

    del evidence_root, output_root, generated_at_utc
    raise Stage3BMatchedAnalysisError(
        "sealed-evidence analysis execution is closed; "
        "merge a separate machine-readable execution authorization first"
    )
