"""Descriptive paired analysis for sealed Stage 3B matched evidence."""

from __future__ import annotations

import csv
import json
import math
import statistics
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Final, cast

from torch2pc_thesis.stage3b_matched_sealing import (
    Stage3BMatchedSealingError,
    sha256_file,
    validate_sealed_matched_evidence,
)

MATCHED_ANALYSIS_SCHEMA_VERSION: Final[int] = 1
MATCHED_BASELINE: Final[str] = "stage2_baseline"
MATCHED_CANDIDATES: Final[tuple[str, ...]] = ("isolated_layer_vjp", "composite_vjp")
MATCHED_CONTINUATION_THRESHOLDS: Final[dict[str, float]] = {
    "fixedpred": 0.15,
    "strict": 0.20,
}
MATCHED_MAX_MEMORY_GROWTH: Final[float] = 0.15


class Stage3BMatchedAnalysisError(RuntimeError):
    """Raised when sealed matched evidence cannot support the analysis."""


def _read_csv(path: Path) -> list[dict[str, str]]:
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
    except OSError as exc:
        raise Stage3BMatchedAnalysisError(f"cannot read table: {path}") from exc
    if not rows:
        raise Stage3BMatchedAnalysisError(f"table is empty: {path}")
    return rows


def _number(row: Mapping[str, str], key: str) -> float:
    try:
        value = float(row[key])
    except (KeyError, ValueError) as exc:
        raise Stage3BMatchedAnalysisError(f"invalid numeric field: {key}") from exc
    if not math.isfinite(value):
        raise Stage3BMatchedAnalysisError(f"non-finite numeric field: {key}")
    return value


def _ratio(candidate: float, baseline: float, *, label: str) -> float:
    if baseline <= 0.0:
        raise Stage3BMatchedAnalysisError(f"baseline {label} must be positive")
    return candidate / baseline


def _median(values: Sequence[float]) -> float:
    if not values:
        raise Stage3BMatchedAnalysisError("cannot calculate an empty median")
    return float(statistics.median(values))


def _write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    if not rows:
        raise Stage3BMatchedAnalysisError(f"cannot write empty table: {path}")
    columns = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def generate_matched_analysis(
    evidence_root: Path,
    output_root: Path,
    *,
    generated_at_utc: str | None = None,
) -> dict[str, object]:
    """Generate block-paired descriptive comparisons without pseudo-replication."""

    try:
        seal = validate_sealed_matched_evidence(evidence_root)
    except Stage3BMatchedSealingError as exc:
        raise Stage3BMatchedAnalysisError(str(exc)) from exc
    cells = _read_csv(evidence_root / "profiling_cells.csv")
    by_block: defaultdict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    for row in cells:
        block_id = row["block_id"]
        candidate_id = row["candidate_id"]
        if candidate_id in by_block[block_id]:
            raise Stage3BMatchedAnalysisError(
                f"duplicate candidate in matched block: {block_id}/{candidate_id}"
            )
        by_block[block_id][candidate_id] = row
    required = {MATCHED_BASELINE, *MATCHED_CANDIDATES}
    paired: list[dict[str, object]] = []
    for block_id, candidates in sorted(by_block.items()):
        if set(candidates) != required:
            raise Stage3BMatchedAnalysisError(
                f"matched block candidate coverage differs: {block_id}"
            )
        baseline = candidates[MATCHED_BASELINE]
        for candidate_id in MATCHED_CANDIDATES:
            candidate = candidates[candidate_id]
            for key in ("method", "depth", "width", "batch_size", "model_seed"):
                if candidate[key] != baseline[key]:
                    raise Stage3BMatchedAnalysisError(
                        f"matched block identity differs: {block_id}/{key}"
                    )
            device_ratio = _ratio(
                _number(candidate, "primary_device_time_us"),
                _number(baseline, "primary_device_time_us"),
                label="device time",
            )
            host_ratio = _ratio(
                _number(candidate, "primary_host_time_us"),
                _number(baseline, "primary_host_time_us"),
                label="host time",
            )
            allocated_ratio = _ratio(
                _number(candidate, "primary_peak_allocated_bytes"),
                _number(baseline, "primary_peak_allocated_bytes"),
                label="peak allocated memory",
            )
            reserved_ratio = _ratio(
                _number(candidate, "primary_peak_reserved_bytes"),
                _number(baseline, "primary_peak_reserved_bytes"),
                label="peak reserved memory",
            )
            paired.append(
                {
                    "block_id": block_id,
                    "candidate_id": candidate_id,
                    "method": candidate["method"],
                    "depth": int(candidate["depth"]),
                    "width": int(candidate["width"]),
                    "batch_size": int(candidate["batch_size"]),
                    "model_seed": int(candidate["model_seed"]),
                    "device_time_ratio_to_baseline": device_ratio,
                    "device_time_reduction": 1.0 - device_ratio,
                    "host_time_ratio_to_baseline": host_ratio,
                    "host_time_reduction": 1.0 - host_ratio,
                    "peak_allocated_ratio_to_baseline": allocated_ratio,
                    "peak_allocated_growth": allocated_ratio - 1.0,
                    "peak_reserved_ratio_to_baseline": reserved_ratio,
                    "peak_reserved_growth": reserved_ratio - 1.0,
                    "observer_cost_ms": _number(candidate, "observer_cost_ms"),
                    "state_vjp_ratio_to_baseline": _ratio(
                        _number(candidate, "state_vjp_calls"),
                        _number(baseline, "state_vjp_calls"),
                        label="state VJP calls",
                    ),
                    "graph_span": int(candidate["graph_span"]),
                    "dependency_radius": int(candidate["dependency_radius"]),
                    "fallback_validation_status": candidate["fallback_validation_status"],
                }
            )
    grouped: defaultdict[tuple[str, str], list[Mapping[str, object]]] = defaultdict(list)
    for paired_row in paired:
        grouped[
            (str(paired_row["candidate_id"]), str(paired_row["method"]))
        ].append(paired_row)
    summaries: list[dict[str, object]] = []
    decisions: list[dict[str, object]] = []
    for (candidate_id, method), rows in sorted(grouped.items()):
        device_reduction = _median([float(cast(Any, row["device_time_reduction"])) for row in rows])
        allocated_growth = _median([float(cast(Any, row["peak_allocated_growth"])) for row in rows])
        reserved_growth = _median([float(cast(Any, row["peak_reserved_growth"])) for row in rows])
        threshold = MATCHED_CONTINUATION_THRESHOLDS[method]
        eligible = bool(
            device_reduction >= threshold
            and max(allocated_growth, reserved_growth) <= MATCHED_MAX_MEMORY_GROWTH
        )
        summaries.append(
            {
                "candidate_id": candidate_id,
                "method": method,
                "matched_block_count": len(rows),
                "median_device_time_reduction": device_reduction,
                "median_host_time_reduction": _median([float(cast(Any, row["host_time_reduction"])) for row in rows]),
                "median_peak_allocated_growth": allocated_growth,
                "median_peak_reserved_growth": reserved_growth,
                "median_observer_cost_ms": _median([float(cast(Any, row["observer_cost_ms"])) for row in rows]),
                "median_state_vjp_ratio_to_baseline": _median([float(cast(Any, row["state_vjp_ratio_to_baseline"])) for row in rows]),
                "maximum_graph_span": max(int(cast(Any, row["graph_span"])) for row in rows),
                "maximum_dependency_radius": max(int(cast(Any, row["dependency_radius"])) for row in rows),
                "engineering_continuation_threshold": threshold,
                "engineering_continuation_eligible": eligible,
            }
        )
        decisions.append(
            {
                "candidate_id": candidate_id,
                "method": method,
                "status": "eligible_for_next_registered_screen" if eligible else "stop_or_revise",
                "ex_if0_opened": False,
                "policy_activation_permitted": False,
                "reason": (
                    "registered timing and memory continuation conditions passed"
                    if eligible
                    else "one or more registered timing or memory conditions failed"
                ),
            }
        )
    destination = output_root.expanduser().resolve()
    if destination.exists() and any(destination.iterdir()):
        raise Stage3BMatchedAnalysisError(f"output root is not empty: {destination}")
    destination.mkdir(parents=True, exist_ok=True)
    _write_csv(destination / "paired_candidate_metrics.csv", paired)
    _write_csv(destination / "candidate_method_summary.csv", summaries)
    summary = {
        "schema_version": MATCHED_ANALYSIS_SCHEMA_VERSION,
        "scope": "stage3b_b1_b2_matched_descriptive_analysis_v1",
        "source_seal": seal,
        "generated_at_utc": generated_at_utc,
        "independent_unit": "model_seed",
        "matched_block_count": len(by_block),
        "paired_row_count": len(paired),
        "statistical_claim_boundary": (
            "descriptive engineering analysis; no p-values or superiority claim at n=3"
        ),
        "aggregation_order": ["measured_steps_to_repetition", "repetitions_to_cell", "paired_cells_within_block", "descriptive_summary_across_model_seed"],
        "primary_timing_lane": "no_hooks",
        "observer_cost_reported_separately": True,
        "fallback_validation_status": "not_applicable_before_ex_if0",
        "decisions": decisions,
        "ex_if0_opened": False,
        "policy_activation_permitted": False,
        "results_publication_permitted": False,
        "test_dataset_access": False,
    }
    (destination / "analysis_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    names = (
        "paired_candidate_metrics.csv",
        "candidate_method_summary.csv",
        "analysis_summary.json",
    )
    (destination / "SHA256SUMS").write_text(
        "\n".join(f"{sha256_file(destination / name)}  {name}" for name in names) + "\n",
        encoding="utf-8",
    )
    return summary
