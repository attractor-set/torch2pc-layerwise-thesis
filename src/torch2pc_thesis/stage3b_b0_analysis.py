"""Read-only statistical and engineering analysis for sealed Stage 3B B0 evidence."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import platform
import subprocess
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final, cast

import numpy as np
import pandas as pd
import scipy

B0_ANALYSIS_SCOPE: Final[str] = "stage3b_b0_statistical_engineering_analysis_v1"
EXPECTED_SEAL_DIGEST: Final[str] = "6a3d61838810e559a39f13e6ac39d6b22624c21d72523bddb55c33e83063c93e"
EXPECTED_EXECUTION_COMMIT: Final[str] = "95c25d35224abd5e741f1df9327662ff2fde23ad"
EXPECTED_SEALING_COMMIT: Final[str] = "caa226cc1cd5d4aa0f9772c1fb997f7388d60730"
EXPECTED_ARCHIVE_INVENTORY_SHA256: Final[str] = (
    "9abc6434b0f59b510e14ef0ad09d5c3b92a4a9472a90974cb92cdb1657e232ed"
)
EXPECTED_IMAGE_DIGEST: Final[str] = (
    "sha256:70b33afe8ee4d54bba27df7c4601a7148b9ab0f72e2260ef54a7432c3d246f29"
)
DEFAULT_METHODS: Final[tuple[str, ...]] = ("fixedpred", "strict")
DEFAULT_DEPTHS: Final[tuple[int, ...]] = (4, 8, 16, 32)
DEFAULT_WIDTHS: Final[tuple[int, ...]] = (64, 256)
DEFAULT_BATCH_SIZES: Final[tuple[int, ...]] = (64, 256)
DEFAULT_MODEL_SEEDS: Final[tuple[int, ...]] = (70, 71, 72)
REQUIRED_REGIONS: Final[tuple[str, ...]] = (
    "initial_forward",
    "local_state_vjp",
    "optimizer_step",
    "parameter_vjp",
    "state_inference",
)
INPUT_TABLES: Final[tuple[str, ...]] = (
    "cell_metrics.csv",
    "region_metrics.csv",
    "paired_method_metrics.csv",
    "configuration_metrics.csv",
)
OUTPUT_TABLES: Final[tuple[str, ...]] = (
    "paired_configuration_summary.csv",
    "paired_matrix_summary.csv",
    "region_seed_attribution.csv",
    "region_configuration_summary.csv",
    "region_matrix_summary.csv",
    "region_paired_configuration_summary.csv",
    "scaling_seed_effects.csv",
    "scaling_summary.csv",
)
PAIR_METRICS: Final[Mapping[str, str]] = {
    "device_time": "strict_to_fixedpred_device_time_median_ratio",
    "host_time": "strict_to_fixedpred_host_time_median_ratio",
    "peak_allocated": "strict_to_fixedpred_peak_allocated_ratio",
    "peak_reserved": "strict_to_fixedpred_peak_reserved_ratio",
}
SCALING_METRICS: Final[Mapping[str, str]] = {
    "device_time": "composite_device_time_median_us",
    "host_time": "composite_host_time_median_us",
    "peak_allocated": "composite_peak_allocated_max_bytes",
    "peak_reserved": "composite_peak_reserved_max_bytes",
}
SCALING_FACTORS: Final[tuple[str, ...]] = ("depth", "width", "batch_size")
STRUCTURAL_LOCALITY_FIELDS: Final[tuple[str, ...]] = (
    "dependency_radius",
    "graph_span",
    "graph_modules",
    "independent_lifetime",
    "feedback_operator",
    "orchestration_barriers",
)


class Stage3BB0AnalysisError(RuntimeError):
    """Raised when sealed B0 evidence violates the analysis contract."""


@dataclass(frozen=True)
class B0AnalysisContract:
    """Frozen matrix and claim boundary for the B0 analysis."""

    methods: tuple[str, ...] = DEFAULT_METHODS
    depths: tuple[int, ...] = DEFAULT_DEPTHS
    widths: tuple[int, ...] = DEFAULT_WIDTHS
    batch_sizes: tuple[int, ...] = DEFAULT_BATCH_SIZES
    model_seeds: tuple[int, ...] = DEFAULT_MODEL_SEEDS
    regions: tuple[str, ...] = REQUIRED_REGIONS
    expected_seal_digest: str = EXPECTED_SEAL_DIGEST
    expected_execution_commit: str = EXPECTED_EXECUTION_COMMIT
    expected_sealing_commit: str = EXPECTED_SEALING_COMMIT
    expected_archive_inventory_sha256: str = EXPECTED_ARCHIVE_INVENTORY_SHA256
    expected_image_digest: str = EXPECTED_IMAGE_DIGEST
    fixedpred_continuation_threshold: float = 0.15
    strict_continuation_threshold: float = 0.20

    @property
    def expected_cell_count(self) -> int:
        return (
            len(self.methods)
            * len(self.depths)
            * len(self.widths)
            * len(self.batch_sizes)
            * len(self.model_seeds)
        )

    @property
    def expected_pair_count(self) -> int:
        return (
            len(self.depths)
            * len(self.widths)
            * len(self.batch_sizes)
            * len(self.model_seeds)
        )

    @property
    def expected_configuration_count(self) -> int:
        return (
            len(self.methods)
            * len(self.depths)
            * len(self.widths)
            * len(self.batch_sizes)
        )

    @property
    def expected_region_count(self) -> int:
        return self.expected_cell_count * len(self.regions)


@dataclass(frozen=True)
class B0Evidence:
    """Validated sealed evidence loaded into analysis-ready tables."""

    root: Path
    seal: dict[str, object]
    validation: dict[str, object]
    metric_definitions: dict[str, object]
    cell_metrics: pd.DataFrame
    region_metrics: pd.DataFrame
    paired_metrics: pd.DataFrame
    configuration_metrics: pd.DataFrame
    input_sha256: dict[str, str]


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of a file."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise Stage3BB0AnalysisError(f"expected a JSON object: {path}")
    return cast(dict[str, object], payload)


def _require_columns(frame: pd.DataFrame, required: set[str], *, table: str) -> None:
    missing = sorted(required - set(frame.columns))
    if missing:
        raise Stage3BB0AnalysisError(
            f"{table} is missing required columns: {', '.join(missing)}"
        )


def _finite_numeric(frame: pd.DataFrame, columns: Iterable[str], *, table: str) -> None:
    for column in columns:
        numeric = pd.to_numeric(frame[column], errors="coerce").to_numpy(dtype=float)
        if not bool(np.isfinite(numeric).all()):
            raise Stage3BB0AnalysisError(
                f"{table} contains non-finite numeric values in column {column}"
            )


def _read_checksum_inventory(path: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            raise Stage3BB0AnalysisError(
                f"invalid SHA256SUMS line {line_number}: {raw_line!r}"
            )
        digest, raw_name = parts
        relative_name = raw_name.removeprefix("*").removeprefix("./")
        if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
            raise Stage3BB0AnalysisError(
                f"invalid SHA-256 digest at line {line_number}: {digest}"
            )
        if relative_name in entries:
            raise Stage3BB0AnalysisError(f"duplicate SHA256SUMS entry: {relative_name}")
        entries[relative_name] = digest
    if not entries:
        raise Stage3BB0AnalysisError("SHA256SUMS is empty")
    return entries


def verify_sealed_evidence(root: Path) -> dict[str, str]:
    """Verify exact sealed-v1 file inventory and return observed digests."""

    resolved = root.resolve()
    inventory_path = resolved / "SHA256SUMS"
    if not inventory_path.is_file():
        raise Stage3BB0AnalysisError(f"missing checksum inventory: {inventory_path}")
    expected = _read_checksum_inventory(inventory_path)
    actual_names = {
        str(path.relative_to(resolved))
        for path in resolved.rglob("*")
        if path.is_file() and path.name != "SHA256SUMS"
    }
    if actual_names != set(expected):
        missing = sorted(set(expected) - actual_names)
        unexpected = sorted(actual_names - set(expected))
        raise Stage3BB0AnalysisError(
            f"sealed evidence inventory mismatch: missing={missing}, unexpected={unexpected}"
        )
    observed: dict[str, str] = {}
    for relative_name, expected_digest in sorted(expected.items()):
        path = resolved / relative_name
        digest = sha256_file(path)
        if digest != expected_digest:
            raise Stage3BB0AnalysisError(
                f"checksum mismatch for {relative_name}: expected={expected_digest}, observed={digest}"
            )
        observed[relative_name] = digest
    observed["SHA256SUMS"] = sha256_file(inventory_path)
    return observed


def _validate_claim_boundary(
    seal: Mapping[str, object], validation: Mapping[str, object]
) -> None:
    required_seal = {
        "status": "sealed",
        "evidence": True,
        "full_b0_campaign_complete": True,
        "full_stage3b_campaign_complete": False,
        "results_publication_permitted": True,
        "source_records_evidence": False,
        "test_dataset_access": False,
    }
    for key, expected in required_seal.items():
        if seal.get(key) != expected:
            raise Stage3BB0AnalysisError(
                f"seal claim boundary mismatch for {key}: expected={expected!r}, observed={seal.get(key)!r}"
            )
    if validation.get("status") != "validation_passed":
        raise Stage3BB0AnalysisError("validation record is not validation_passed")
    if validation.get("test_dataset_access") is not False:
        raise Stage3BB0AnalysisError("validation record reports test dataset access")
    if validation.get("source_records_evidence") is not False:
        raise Stage3BB0AnalysisError("source canonical records unexpectedly claim evidence")


def _validate_matrix(
    evidence: B0Evidence,
    *,
    contract: B0AnalysisContract,
) -> None:
    cells = evidence.cell_metrics
    regions = evidence.region_metrics
    paired = evidence.paired_metrics
    configurations = evidence.configuration_metrics

    cell_keys = ["method", "depth", "width", "batch_size", "model_seed"]
    expected_cells = {
        (method, depth, width, batch_size, seed)
        for method in contract.methods
        for depth in contract.depths
        for width in contract.widths
        for batch_size in contract.batch_sizes
        for seed in contract.model_seeds
    }
    observed_cells = {
        (
            str(row.method),
            int(row.depth),
            int(row.width),
            int(row.batch_size),
            int(row.model_seed),
        )
        for row in cells[cell_keys].itertuples(index=False)
    }
    if len(cells) != contract.expected_cell_count or observed_cells != expected_cells:
        raise Stage3BB0AnalysisError(
            "cell matrix differs from the frozen B0 contract: "
            f"rows={len(cells)}, expected={contract.expected_cell_count}"
        )
    if bool(cells.duplicated(cell_keys).any()) or not cells["cell_id"].is_unique:
        raise Stage3BB0AnalysisError("cell_metrics contains duplicate cells")

    pair_keys = ["depth", "width", "batch_size", "model_seed"]
    expected_pairs = {
        (depth, width, batch_size, seed)
        for depth in contract.depths
        for width in contract.widths
        for batch_size in contract.batch_sizes
        for seed in contract.model_seeds
    }
    observed_pairs = {
        (int(row.depth), int(row.width), int(row.batch_size), int(row.model_seed))
        for row in paired[pair_keys].itertuples(index=False)
    }
    if len(paired) != contract.expected_pair_count or observed_pairs != expected_pairs:
        raise Stage3BB0AnalysisError(
            "paired matrix differs from the frozen B0 contract: "
            f"rows={len(paired)}, expected={contract.expected_pair_count}"
        )
    if bool(paired.duplicated(pair_keys).any()):
        raise Stage3BB0AnalysisError("paired_method_metrics contains duplicate pairs")

    configuration_keys = ["method", "depth", "width", "batch_size"]
    if len(configurations) != contract.expected_configuration_count:
        raise Stage3BB0AnalysisError(
            "configuration matrix differs from the frozen B0 contract: "
            f"rows={len(configurations)}, expected={contract.expected_configuration_count}"
        )
    if bool(configurations.duplicated(configuration_keys).any()):
        raise Stage3BB0AnalysisError("configuration_metrics contains duplicate configurations")
    if set(pd.to_numeric(configurations["seed_count"], errors="raise").astype(int)) != {
        len(contract.model_seeds)
    }:
        raise Stage3BB0AnalysisError("configuration_metrics seed_count differs from contract")

    region_keys = ["cell_id", "region"]
    if len(regions) != contract.expected_region_count:
        raise Stage3BB0AnalysisError(
            "region matrix differs from the frozen B0 contract: "
            f"rows={len(regions)}, expected={contract.expected_region_count}"
        )
    if bool(regions.duplicated(region_keys).any()):
        raise Stage3BB0AnalysisError("region_metrics contains duplicate cell-region rows")
    counts = regions.groupby("cell_id", sort=True)["region"].agg(
        lambda values: tuple(sorted(str(value) for value in values))
    )
    expected_regions = tuple(sorted(contract.regions))
    if any(value != expected_regions for value in counts):
        raise Stage3BB0AnalysisError("one or more cells lack the required profiling regions")
    if set(regions["cell_id"]) != set(cells["cell_id"]):
        raise Stage3BB0AnalysisError("region_metrics cell IDs differ from cell_metrics")

    integrity_columns = {
        "integrity_all_passed",
        "region_non_finite_events_total",
        "integrity_maximum_relative_l2",
        "integrity_minimum_cosine",
    }
    _require_columns(cells, integrity_columns, table="cell_metrics.csv")
    if not bool(cells["integrity_all_passed"].astype(bool).all()):
        raise Stage3BB0AnalysisError("one or more B0 integrity gates failed")
    if not bool((pd.to_numeric(cells["region_non_finite_events_total"]) == 0).all()):
        raise Stage3BB0AnalysisError("one or more B0 cells report non-finite region events")

    counts_record = evidence.validation.get("counts")
    if not isinstance(counts_record, dict):
        raise Stage3BB0AnalysisError("validation counts record is missing")
    expected_validation_counts = {
        "cells": contract.expected_cell_count,
        "completed_attempts": contract.expected_cell_count,
        "failed_attempts": 0,
        "process_records": contract.expected_cell_count,
        "unique_child_pids": contract.expected_cell_count,
    }
    for key, expected in expected_validation_counts.items():
        if counts_record.get(key) != expected:
            raise Stage3BB0AnalysisError(
                f"validation count mismatch for {key}: expected={expected}, observed={counts_record.get(key)}"
            )


def load_b0_evidence(
    root: Path,
    *,
    contract: B0AnalysisContract | None = None,
) -> B0Evidence:
    """Load and validate the published sealed-v1 B0 evidence."""

    resolved_contract = contract or B0AnalysisContract()
    resolved = root.resolve()
    digests = verify_sealed_evidence(resolved)
    seal = _load_json(resolved / "seal.json")
    validation = _load_json(resolved / "validation.json")
    metric_definitions = _load_json(resolved / "metric-definitions.json")
    _validate_claim_boundary(seal, validation)
    expected_identity = {
        "seal_digest": resolved_contract.expected_seal_digest,
        "source_commit": resolved_contract.expected_execution_commit,
        "sealing_source_commit": resolved_contract.expected_sealing_commit,
        "source_archive_inventory_sha256": (
            resolved_contract.expected_archive_inventory_sha256
        ),
        "image_digest": resolved_contract.expected_image_digest,
    }
    for key, expected in expected_identity.items():
        if seal.get(key) != expected:
            raise Stage3BB0AnalysisError(
                f"sealed B0 identity mismatch for {key}: "
                f"expected={expected!r}, observed={seal.get(key)!r}"
            )

    frames = {name: pd.read_csv(resolved / name) for name in INPUT_TABLES}
    cell = frames["cell_metrics.csv"]
    region = frames["region_metrics.csv"]
    paired = frames["paired_method_metrics.csv"]
    configuration = frames["configuration_metrics.csv"]

    _require_columns(
        cell,
        {
            "cell_id",
            "method",
            "depth",
            "width",
            "batch_size",
            "model_seed",
            *SCALING_METRICS.values(),
        },
        table="cell_metrics.csv",
    )
    _require_columns(
        paired,
        {"depth", "width", "batch_size", "model_seed", *PAIR_METRICS.values()},
        table="paired_method_metrics.csv",
    )
    _require_columns(
        region,
        {
            "cell_id",
            "method",
            "depth",
            "width",
            "batch_size",
            "model_seed",
            "region",
            "host_time_median_us",
            "device_time_median_us",
            "peak_allocated_max_bytes",
            "peak_reserved_max_bytes",
            "vjp_calls_total",
            "synchronization_points_total",
            "saved_tensor_bytes_mean",
            "saved_tensor_bytes_max",
            "actual_inference_steps_total",
            "non_finite_events_total",
        },
        table="region_metrics.csv",
    )
    _require_columns(
        configuration,
        {"method", "depth", "width", "batch_size", "seed_count"},
        table="configuration_metrics.csv",
    )
    _finite_numeric(cell, SCALING_METRICS.values(), table="cell_metrics.csv")
    _finite_numeric(paired, PAIR_METRICS.values(), table="paired_method_metrics.csv")
    _finite_numeric(
        region,
        (
            "host_time_median_us",
            "device_time_median_us",
            "peak_allocated_max_bytes",
            "peak_reserved_max_bytes",
            "vjp_calls_total",
            "synchronization_points_total",
            "saved_tensor_bytes_mean",
            "saved_tensor_bytes_max",
            "actual_inference_steps_total",
            "non_finite_events_total",
        ),
        table="region_metrics.csv",
    )

    evidence = B0Evidence(
        root=resolved,
        seal=seal,
        validation=validation,
        metric_definitions=metric_definitions,
        cell_metrics=cell,
        region_metrics=region,
        paired_metrics=paired,
        configuration_metrics=configuration,
        input_sha256=digests,
    )
    _validate_matrix(evidence, contract=resolved_contract)
    return evidence


def _median_min_max(values: pd.Series) -> tuple[float, float, float]:
    numeric = pd.to_numeric(values, errors="coerce").to_numpy(dtype=float)
    finite = numeric[np.isfinite(numeric)]
    if finite.size == 0:
        return math.nan, math.nan, math.nan
    return float(np.median(finite)), float(np.min(finite)), float(np.max(finite))


def paired_configuration_summary(
    paired: pd.DataFrame,
    *,
    expected_seed_count: int,
) -> pd.DataFrame:
    """Summarize Strict/FixedPred paired effects within each configuration."""

    keys = ["depth", "width", "batch_size"]
    rows: list[dict[str, object]] = []
    for key, group in paired.groupby(keys, sort=True, dropna=False):
        key_values = key if isinstance(key, tuple) else (key,)
        if len(group) != expected_seed_count:
            raise Stage3BB0AnalysisError(
                f"paired configuration {key_values} has {len(group)} seeds; expected {expected_seed_count}"
            )
        row: dict[str, object] = {
            **dict(zip(keys, key_values, strict=True)),
            "seed_count": int(len(group)),
        }
        for metric_name, column in PAIR_METRICS.items():
            median, minimum, maximum = _median_min_max(group[column])
            row[f"{metric_name}_ratio_median"] = median
            row[f"{metric_name}_ratio_min"] = minimum
            row[f"{metric_name}_ratio_max"] = maximum
            row[f"{metric_name}_percent_change_median"] = (median - 1.0) * 100.0
            row[f"{metric_name}_all_seeds_strict_greater"] = bool(
                (pd.to_numeric(group[column], errors="raise") > 1.0).all()
            )
        rows.append(row)
    return pd.DataFrame(rows).sort_values(keys, ignore_index=True)


def paired_matrix_summary(configuration_summary: pd.DataFrame) -> pd.DataFrame:
    """Summarize configuration-level medians without treating cells as replicates."""

    rows: list[dict[str, object]] = []
    for metric_name in PAIR_METRICS:
        column = f"{metric_name}_ratio_median"
        median, minimum, maximum = _median_min_max(configuration_summary[column])
        rows.append(
            {
                "metric": metric_name,
                "comparison": "strict_relative_to_fixedpred",
                "configuration_count": int(len(configuration_summary)),
                "seed_count_per_configuration": int(
                    configuration_summary["seed_count"].iloc[0]
                ),
                "configuration_median_ratio": median,
                "configuration_min_ratio": minimum,
                "configuration_max_ratio": maximum,
                "configuration_median_percent_change": (median - 1.0) * 100.0,
                "all_configuration_medians_strict_greater": bool(
                    (configuration_summary[column] > 1.0).all()
                ),
                "inference_scope": "descriptive_engineering_matrix",
            }
        )
    return pd.DataFrame(rows)


def region_seed_attribution(evidence: B0Evidence) -> pd.DataFrame:
    """Create normalized region attribution at the independent seed-cell level."""

    region = evidence.region_metrics.copy()
    cell_columns = [
        "cell_id",
        "composite_host_time_median_us",
        "composite_device_time_median_us",
    ]
    region = region.merge(
        evidence.cell_metrics[cell_columns],
        on="cell_id",
        validate="many_to_one",
    )
    region["host_region_sum_us"] = region.groupby("cell_id", sort=True)[
        "host_time_median_us"
    ].transform("sum")
    region["device_region_sum_us"] = region.groupby("cell_id", sort=True)[
        "device_time_median_us"
    ].transform("sum")
    if bool((region[["host_region_sum_us", "device_region_sum_us"]] <= 0.0).any().any()):
        raise Stage3BB0AnalysisError("region time sums must be positive")
    region["host_time_share_of_region_sum"] = (
        region["host_time_median_us"] / region["host_region_sum_us"]
    )
    region["device_time_share_of_region_sum"] = (
        region["device_time_median_us"] / region["device_region_sum_us"]
    )
    region["host_time_to_composite_ratio"] = (
        region["host_time_median_us"] / region["composite_host_time_median_us"]
    )
    region["device_time_to_composite_ratio"] = (
        region["device_time_median_us"] / region["composite_device_time_median_us"]
    )
    columns = [
        "cell_id",
        "method",
        "depth",
        "width",
        "batch_size",
        "model_seed",
        "region",
        "host_time_median_us",
        "device_time_median_us",
        "host_time_share_of_region_sum",
        "device_time_share_of_region_sum",
        "host_time_to_composite_ratio",
        "device_time_to_composite_ratio",
        "peak_allocated_max_bytes",
        "peak_reserved_max_bytes",
        "vjp_calls_total",
        "synchronization_points_total",
        "saved_tensor_bytes_mean",
        "saved_tensor_bytes_max",
        "actual_inference_steps_total",
        "non_finite_events_total",
    ]
    return region[columns].sort_values(
        ["method", "depth", "width", "batch_size", "model_seed", "region"],
        ignore_index=True,
    )


def region_configuration_summary(
    attribution: pd.DataFrame,
    *,
    expected_seed_count: int,
) -> pd.DataFrame:
    """Aggregate region measurements across three model seeds per configuration."""

    keys = ["method", "depth", "width", "batch_size", "region"]
    metrics = (
        "host_time_median_us",
        "device_time_median_us",
        "host_time_share_of_region_sum",
        "device_time_share_of_region_sum",
        "host_time_to_composite_ratio",
        "device_time_to_composite_ratio",
        "peak_allocated_max_bytes",
        "peak_reserved_max_bytes",
        "vjp_calls_total",
        "synchronization_points_total",
        "saved_tensor_bytes_mean",
        "saved_tensor_bytes_max",
        "actual_inference_steps_total",
    )
    rows: list[dict[str, object]] = []
    for key, group in attribution.groupby(keys, sort=True, dropna=False):
        key_values = key if isinstance(key, tuple) else (key,)
        if len(group) != expected_seed_count:
            raise Stage3BB0AnalysisError(
                f"region configuration {key_values} has {len(group)} seeds; expected {expected_seed_count}"
            )
        row: dict[str, object] = {
            **dict(zip(keys, key_values, strict=True)),
            "seed_count": int(len(group)),
        }
        for metric in metrics:
            median, minimum, maximum = _median_min_max(group[metric])
            row[f"{metric}_median"] = median
            row[f"{metric}_min"] = minimum
            row[f"{metric}_max"] = maximum
        rows.append(row)
    return pd.DataFrame(rows).sort_values(keys, ignore_index=True)


def region_matrix_summary(configuration_summary: pd.DataFrame) -> pd.DataFrame:
    """Summarize region attribution across the fixed engineering matrix."""

    keys = ["method", "region"]
    source_metrics = (
        "host_time_median_us_median",
        "device_time_median_us_median",
        "host_time_share_of_region_sum_median",
        "device_time_share_of_region_sum_median",
        "vjp_calls_total_median",
        "saved_tensor_bytes_mean_median",
        "saved_tensor_bytes_max_median",
        "actual_inference_steps_total_median",
    )
    rows: list[dict[str, object]] = []
    for key, group in configuration_summary.groupby(keys, sort=True, dropna=False):
        key_values = key if isinstance(key, tuple) else (key,)
        row: dict[str, object] = {
            **dict(zip(keys, key_values, strict=True)),
            "configuration_count": int(len(group)),
            "seed_count_per_configuration": int(group["seed_count"].iloc[0]),
        }
        for metric in source_metrics:
            median, minimum, maximum = _median_min_max(group[metric])
            output_name = metric.removesuffix("_median")
            row[f"{output_name}_matrix_median"] = median
            row[f"{output_name}_matrix_min"] = minimum
            row[f"{output_name}_matrix_max"] = maximum
        rows.append(row)
    result = pd.DataFrame(rows)
    result["device_share_rank_within_method"] = result.groupby("method", sort=True)[
        "device_time_share_of_region_sum_matrix_median"
    ].rank(method="dense", ascending=False).astype(int)
    return result.sort_values(
        ["method", "device_share_rank_within_method", "region"], ignore_index=True
    )


def region_paired_configuration_summary(
    attribution: pd.DataFrame,
    *,
    expected_seed_count: int,
) -> pd.DataFrame:
    """Pair Strict and FixedPred region costs within seed and configuration."""

    keys = ["depth", "width", "batch_size", "model_seed", "region"]
    value_columns = [
        "device_time_median_us",
        "host_time_median_us",
        "device_time_share_of_region_sum",
        "host_time_share_of_region_sum",
        "vjp_calls_total",
        "saved_tensor_bytes_mean",
    ]
    fixedpred = attribution.loc[attribution["method"] == "fixedpred", keys + value_columns]
    strict = attribution.loc[attribution["method"] == "strict", keys + value_columns]
    pairs = fixedpred.merge(
        strict,
        on=keys,
        suffixes=("_fixedpred", "_strict"),
        validate="one_to_one",
    )
    ratio_metrics = (
        "device_time_median_us",
        "host_time_median_us",
        "device_time_share_of_region_sum",
        "host_time_share_of_region_sum",
    )
    for metric in ratio_metrics:
        denominator = pd.to_numeric(pairs[f"{metric}_fixedpred"], errors="raise")
        numerator = pd.to_numeric(pairs[f"{metric}_strict"], errors="raise")
        if bool((denominator <= 0.0).any()):
            raise Stage3BB0AnalysisError(
                f"cannot calculate Strict/FixedPred region ratio for non-positive {metric}"
            )
        pairs[f"strict_to_fixedpred_{metric}_ratio"] = numerator / denominator
    pairs["strict_minus_fixedpred_vjp_calls_total"] = (
        pd.to_numeric(pairs["vjp_calls_total_strict"], errors="raise")
        - pd.to_numeric(pairs["vjp_calls_total_fixedpred"], errors="raise")
    )
    config_keys = ["depth", "width", "batch_size", "region"]
    rows: list[dict[str, object]] = []
    ratio_columns = [
        f"strict_to_fixedpred_{metric}_ratio" for metric in ratio_metrics
    ]
    summary_columns = [*ratio_columns, "strict_minus_fixedpred_vjp_calls_total"]
    for key, group in pairs.groupby(config_keys, sort=True, dropna=False):
        key_values = key if isinstance(key, tuple) else (key,)
        if len(group) != expected_seed_count:
            raise Stage3BB0AnalysisError(
                f"paired region configuration {key_values} has {len(group)} seeds; expected {expected_seed_count}"
            )
        row: dict[str, object] = {
            **dict(zip(config_keys, key_values, strict=True)),
            "seed_count": int(len(group)),
        }
        for metric in summary_columns:
            median, minimum, maximum = _median_min_max(group[metric])
            row[f"{metric}_median"] = median
            row[f"{metric}_min"] = minimum
            row[f"{metric}_max"] = maximum
        rows.append(row)
    return pd.DataFrame(rows).sort_values(config_keys, ignore_index=True)


def _fit_log2_main_effects(
    frame: pd.DataFrame,
    *,
    metric_column: str,
) -> tuple[dict[str, float], float, float]:
    values = pd.to_numeric(frame[metric_column], errors="coerce").to_numpy(dtype=float)
    if not bool(np.isfinite(values).all()) or bool((values <= 0.0).any()):
        raise Stage3BB0AnalysisError(
            f"scaling metric {metric_column} must contain positive finite values"
        )
    design = np.column_stack(
        [
            np.ones(len(frame), dtype=float),
            np.log2(pd.to_numeric(frame["depth"], errors="raise").to_numpy(dtype=float)),
            np.log2(pd.to_numeric(frame["width"], errors="raise").to_numpy(dtype=float)),
            np.log2(
                pd.to_numeric(frame["batch_size"], errors="raise").to_numpy(dtype=float)
            ),
        ]
    )
    target = np.log2(values)
    coefficients, _, rank, _ = np.linalg.lstsq(design, target, rcond=None)
    if int(rank) != design.shape[1]:
        raise Stage3BB0AnalysisError("scaling design matrix is rank deficient")
    fitted = design @ coefficients
    residuals = target - fitted
    total = float(np.sum((target - float(np.mean(target))) ** 2))
    residual_sum = float(np.sum(residuals**2))
    r_squared = 1.0 - residual_sum / total if total > 0.0 else 1.0
    effects = {
        factor: float(coefficients[index])
        for index, factor in enumerate(SCALING_FACTORS, start=1)
    }
    return effects, r_squared, float(np.max(np.abs(residuals)))


def scaling_seed_effects(
    cells: pd.DataFrame,
    *,
    contract: B0AnalysisContract,
) -> pd.DataFrame:
    """Fit descriptive log2 main-effect scaling models per method and seed."""

    expected_rows = len(contract.depths) * len(contract.widths) * len(contract.batch_sizes)
    rows: list[dict[str, object]] = []
    for method in contract.methods:
        for seed in contract.model_seeds:
            subset = cells.loc[
                (cells["method"] == method) & (cells["model_seed"] == seed)
            ].copy()
            if len(subset) != expected_rows:
                raise Stage3BB0AnalysisError(
                    f"scaling subset method={method}, seed={seed} has {len(subset)} rows; expected {expected_rows}"
                )
            for metric_name, metric_column in SCALING_METRICS.items():
                effects, r_squared, max_residual = _fit_log2_main_effects(
                    subset,
                    metric_column=metric_column,
                )
                for factor in SCALING_FACTORS:
                    elasticity = effects[factor]
                    rows.append(
                        {
                            "method": method,
                            "model_seed": int(seed),
                            "metric": metric_name,
                            "factor": factor,
                            "elasticity_log2": elasticity,
                            "multiplier_per_doubling": float(2.0**elasticity),
                            "r_squared": r_squared,
                            "max_abs_log2_residual": max_residual,
                            "model": "log2_main_effects_without_interactions",
                        }
                    )
    return pd.DataFrame(rows).sort_values(
        ["method", "metric", "factor", "model_seed"], ignore_index=True
    )


def scaling_summary(seed_effects: pd.DataFrame) -> pd.DataFrame:
    """Summarize scaling coefficients across the three independent seeds."""

    keys = ["method", "metric", "factor"]
    rows: list[dict[str, object]] = []
    for key, group in seed_effects.groupby(keys, sort=True, dropna=False):
        key_values = key if isinstance(key, tuple) else (key,)
        row: dict[str, object] = {
            **dict(zip(keys, key_values, strict=True)),
            "seed_count": int(group["model_seed"].nunique()),
            "model": str(group["model"].iloc[0]),
        }
        for metric in (
            "elasticity_log2",
            "multiplier_per_doubling",
            "r_squared",
            "max_abs_log2_residual",
        ):
            median, minimum, maximum = _median_min_max(group[metric])
            row[f"{metric}_median"] = median
            row[f"{metric}_min"] = minimum
            row[f"{metric}_max"] = maximum
        rows.append(row)
    return pd.DataFrame(rows).sort_values(keys, ignore_index=True)


def _vjp_attribution_proxy(
    configuration_summary: pd.DataFrame,
    *,
    method: str,
) -> tuple[float, float, float]:
    subset = configuration_summary.loc[configuration_summary["method"] == method]
    pivot = subset.pivot_table(
        index=["depth", "width", "batch_size"],
        columns="region",
        values="device_time_share_of_region_sum_median",
        aggfunc="first",
    )
    required = {"local_state_vjp", "parameter_vjp", "state_inference"}
    if not required.issubset(pivot.columns):
        raise Stage3BB0AnalysisError(
            f"region summary lacks decision-gate regions for method={method}"
        )
    vjp_fraction = pivot["local_state_vjp"] + pivot["parameter_vjp"]
    state_fraction = pivot["state_inference"]
    fraction_median = float(np.median(vjp_fraction.to_numpy(dtype=float)))
    state_median = float(np.median(state_fraction.to_numpy(dtype=float)))
    if not 0.0 <= fraction_median < 1.0:
        raise Stage3BB0AnalysisError("VJP attribution fraction must lie in [0, 1)")
    amdahl_proxy = 1.0 / (1.0 - fraction_median)
    return fraction_median, state_median, amdahl_proxy


def analysis_summary(
    evidence: B0Evidence,
    *,
    paired_summary: pd.DataFrame,
    region_configurations: pd.DataFrame,
    region_summary: pd.DataFrame,
    scaling: pd.DataFrame,
    contract: B0AnalysisContract,
) -> dict[str, object]:
    """Build bounded findings and engineering continuation gates."""

    pair_by_metric = paired_summary.set_index("metric")
    bottlenecks: dict[str, object] = {}
    continuation_passed: dict[str, bool] = {}
    for method, threshold in (
        ("fixedpred", contract.fixedpred_continuation_threshold),
        ("strict", contract.strict_continuation_threshold),
    ):
        method_regions = region_summary.loc[region_summary["method"] == method].sort_values(
            "device_share_rank_within_method"
        )
        dominant = method_regions.iloc[0]
        saved_tensor_dominant = method_regions.sort_values(
            ["saved_tensor_bytes_mean_matrix_median", "region"],
            ascending=[False, True],
            kind="stable",
        ).iloc[0]
        vjp_fraction, state_fraction, amdahl_proxy = _vjp_attribution_proxy(
            region_configurations,
            method=method,
        )
        speedup_fraction = amdahl_proxy - 1.0
        passed = speedup_fraction >= threshold
        continuation_passed[method] = passed
        bottlenecks[method] = {
            "dominant_device_region": str(dominant["region"]),
            "dominant_device_region_share_median": float(
                dominant["device_time_share_of_region_sum_matrix_median"]
            ),
            "dominant_saved_tensor_region": str(saved_tensor_dominant["region"]),
            "dominant_saved_tensor_bytes_mean_median": float(
                saved_tensor_dominant["saved_tensor_bytes_mean_matrix_median"]
            ),
            "state_inference_share_median": state_fraction,
            "vjp_region_share_median": vjp_fraction,
            "vjp_region_amdahl_upper_bound_proxy": amdahl_proxy,
            "vjp_region_upper_bound_speedup_fraction": speedup_fraction,
            "continuation_threshold": threshold,
            "continuation_threshold_passed": passed,
        }

    available_columns = set(evidence.cell_metrics.columns) | set(evidence.region_metrics.columns)
    missing_locality_fields = sorted(set(STRUCTURAL_LOCALITY_FIELDS) - available_columns)
    scaling_records: list[dict[str, object]] = []
    for row in scaling.itertuples(index=False):
        scaling_records.append(
            {
                "method": str(row.method),
                "metric": str(row.metric),
                "factor": str(row.factor),
                "multiplier_per_doubling_median": float(
                    row.multiplier_per_doubling_median
                ),
                "multiplier_per_doubling_min": float(row.multiplier_per_doubling_min),
                "multiplier_per_doubling_max": float(row.multiplier_per_doubling_max),
                "r_squared_median": float(row.r_squared_median),
            }
        )

    state_saved = region_summary.loc[region_summary["region"] == "state_inference"].set_index(
        "method"
    )["saved_tensor_bytes_mean_matrix_median"]
    fixedpred_state_saved = float(state_saved.loc["fixedpred"])
    strict_state_saved = float(state_saved.loc["strict"])
    if fixedpred_state_saved <= 0.0:
        raise Stage3BB0AnalysisError(
            "FixedPred state_inference saved-tensor baseline must be positive"
        )

    return {
        "schema_version": 1,
        "scope": B0_ANALYSIS_SCOPE,
        "status": "analysis_complete",
        "evidence": True,
        "full_b0_campaign_complete": True,
        "full_stage3b_campaign_complete": False,
        "results_publication_permitted": True,
        "test_dataset_access": False,
        "statistical_unit": "model_seed",
        "independent_seed_count_per_configuration": len(contract.model_seeds),
        "inferential_scope": "descriptive_engineering_analysis_n3",
        "source": {
            "seal_digest": evidence.seal["seal_digest"],
            "execution_commit": evidence.seal["source_commit"],
            "sealing_source_commit": evidence.seal["sealing_source_commit"],
            "archive_inventory_sha256": evidence.seal[
                "source_archive_inventory_sha256"
            ],
        },
        "paired_strict_relative_to_fixedpred": {
            str(metric): {
                "configuration_median_ratio": float(row["configuration_median_ratio"]),
                "configuration_min_ratio": float(row["configuration_min_ratio"]),
                "configuration_max_ratio": float(row["configuration_max_ratio"]),
                "all_configuration_medians_strict_greater": bool(
                    row["all_configuration_medians_strict_greater"]
                ),
            }
            for metric, row in pair_by_metric.iterrows()
        },
        "bottlenecks": bottlenecks,
        "saved_tensor_analysis": {
            "state_inference_fixedpred_bytes_mean_median": fixedpred_state_saved,
            "state_inference_strict_bytes_mean_median": strict_state_saved,
            "state_inference_strict_to_fixedpred_ratio": (
                strict_state_saved / fixedpred_state_saved
            ),
            "interpretation": (
                "Strict retains substantially more saved-tensor bytes in state_inference "
                "within the published B0 matrix."
            ),
        },
        "scaling": scaling_records,
        "locality_coverage": {
            "structural_locality_claims_supported": not missing_locality_fields,
            "missing_structural_fields": missing_locality_fields,
            "interpretation": (
                "B0 sealed aggregates support region-cost attribution but do not support "
                "dependency-radius, graph-span, lifetime, feedback-operator, or orchestration-locality claims."
            ),
        },
        "decision_gate": {
            "b1_b2_candidate_specific_equivalence_work": (
                "continue" if all(continuation_passed.values()) else "hold"
            ),
            "full_b1_b2_matched_profiling": "blocked_pending_candidate_specific_gates",
            "locality_claims": (
                "available" if not missing_locality_fields else "blocked_by_missing_structural_evidence"
            ),
            "new_b0_execution": "not_required",
            "reason": (
                "The normalized VJP-region Amdahl proxy exceeds the registered engineering "
                "continuation threshold for both methods, while structural locality evidence "
                "remains incomplete."
            ),
        },
        "limitations": [
            "Three independent model seeds per configuration; discrete p-values are not used for superiority claims.",
            "Configuration cells are controlled engineering conditions, not additional independent biological or population replicates.",
            "Region medians are normalized within the sum of region medians because region timings are not assumed to be additive to the composite median.",
            "Log2 scaling models are descriptive main-effect summaries without interaction terms.",
            "Results are bounded to the published ROCm/float32 synthetic scaling matrix and pinned implementation.",
        ],
    }


def _resolve_source_commit(repo_root: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _resolve_generated_at(generated_at_utc: str | None) -> str:
    if generated_at_utc is not None:
        return generated_at_utc
    source_date_epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if source_date_epoch is not None:
        return datetime.fromtimestamp(int(source_date_epoch), tz=UTC).isoformat().replace(
            "+00:00", "Z"
        )
    return datetime.now(tz=UTC).isoformat().replace("+00:00", "Z")


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(
        path,
        index=False,
        encoding="utf-8",
        lineterminator="\n",
        float_format="%.12g",
        quoting=csv.QUOTE_MINIMAL,
    )


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_sha256sums(root: Path) -> None:
    paths = sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.name != "SHA256SUMS"
    )
    lines = [f"{sha256_file(path)}  ./{path.relative_to(root)}" for path in paths]
    (root / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate_stage3b_b0_analysis(
    evidence_root: Path,
    output_root: Path,
    *,
    repo_root: Path,
    source_commit: str | None = None,
    generated_at_utc: str | None = None,
    contract: B0AnalysisContract | None = None,
) -> dict[str, int]:
    """Generate deterministic B0 statistical tables, figures, reports, and metadata."""

    resolved_contract = contract or B0AnalysisContract()
    if output_root.resolve().is_relative_to(evidence_root.resolve()):
        raise Stage3BB0AnalysisError("analysis output must be outside sealed-v1 input")
    if output_root.exists():
        raise Stage3BB0AnalysisError(f"analysis output already exists: {output_root}")

    evidence = load_b0_evidence(evidence_root, contract=resolved_contract)
    source_inventory_before = verify_sealed_evidence(evidence_root)

    paired_config = paired_configuration_summary(
        evidence.paired_metrics,
        expected_seed_count=len(resolved_contract.model_seeds),
    )
    paired_matrix = paired_matrix_summary(paired_config)
    region_seed = region_seed_attribution(evidence)
    region_config = region_configuration_summary(
        region_seed,
        expected_seed_count=len(resolved_contract.model_seeds),
    )
    region_matrix = region_matrix_summary(region_config)
    region_paired = region_paired_configuration_summary(
        region_seed,
        expected_seed_count=len(resolved_contract.model_seeds),
    )
    scaling_seed = scaling_seed_effects(evidence.cell_metrics, contract=resolved_contract)
    scaling_matrix = scaling_summary(scaling_seed)
    summary = analysis_summary(
        evidence,
        paired_summary=paired_matrix,
        region_configurations=region_config,
        region_summary=region_matrix,
        scaling=scaling_matrix,
        contract=resolved_contract,
    )

    output_root.mkdir(parents=True, exist_ok=False)
    tables: dict[str, pd.DataFrame] = {
        "paired_configuration_summary.csv": paired_config,
        "paired_matrix_summary.csv": paired_matrix,
        "region_seed_attribution.csv": region_seed,
        "region_configuration_summary.csv": region_config,
        "region_matrix_summary.csv": region_matrix,
        "region_paired_configuration_summary.csv": region_paired,
        "scaling_seed_effects.csv": scaling_seed,
        "scaling_summary.csv": scaling_matrix,
    }
    for filename, frame in tables.items():
        _write_csv(frame, output_root / filename)
    _write_json(output_root / "analysis_summary.json", summary)

    from torch2pc_thesis.stage3b_b0_figures import generate_b0_figures
    from torch2pc_thesis.stage3b_b0_reporting import write_b0_reports

    resolved_commit = source_commit or _resolve_source_commit(repo_root)
    resolved_time = _resolve_generated_at(generated_at_utc)
    figure_counts = generate_b0_figures(
        paired_config,
        region_matrix,
        scaling_matrix,
        output_root,
        generated_at_utc=resolved_time,
    )
    report_counts = write_b0_reports(
        summary,
        paired_config,
        region_matrix,
        scaling_matrix,
        output_root,
    )

    generated_names = [
        *OUTPUT_TABLES,
        "analysis_summary.json",
        *figure_counts,
        *report_counts,
    ]
    try:
        source_evidence_path = str(evidence.root.relative_to(repo_root.resolve()))
    except ValueError:
        source_evidence_path = str(evidence.root)

    metadata: dict[str, object] = {
        "schema_version": 1,
        "scope": B0_ANALYSIS_SCOPE,
        "generated_at_utc": resolved_time,
        "analysis_source_commit": resolved_commit,
        "source_evidence": {
            "path": source_evidence_path,
            "seal_digest": evidence.seal["seal_digest"],
            "source_commit": evidence.seal["source_commit"],
            "sealing_source_commit": evidence.seal["sealing_source_commit"],
            "source_archive_inventory_sha256": evidence.seal[
                "source_archive_inventory_sha256"
            ],
            "files": source_inventory_before,
        },
        "contract": {
            "statistical_unit": "model_seed",
            "methods": list(resolved_contract.methods),
            "depths": list(resolved_contract.depths),
            "widths": list(resolved_contract.widths),
            "batch_sizes": list(resolved_contract.batch_sizes),
            "model_seeds": list(resolved_contract.model_seeds),
            "regions": list(resolved_contract.regions),
            "expected_seal_digest": resolved_contract.expected_seal_digest,
            "expected_execution_commit": resolved_contract.expected_execution_commit,
            "expected_sealing_commit": resolved_contract.expected_sealing_commit,
            "expected_archive_inventory_sha256": (
                resolved_contract.expected_archive_inventory_sha256
            ),
            "expected_image_digest": resolved_contract.expected_image_digest,
            "inferential_scope": "descriptive_engineering_analysis_n3",
            "exact_sign_flip_tests": False,
            "full_stage3b_campaign_complete": False,
        },
        "outputs": {
            name: {
                "sha256": sha256_file(output_root / name),
                "size_bytes": int((output_root / name).stat().st_size),
            }
            for name in sorted(generated_names)
        },
        "software": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
        },
    }
    _write_json(output_root / "analysis_metadata.json", metadata)
    _write_sha256sums(output_root)

    source_inventory_after = verify_sealed_evidence(evidence_root)
    if source_inventory_after != source_inventory_before:
        raise Stage3BB0AnalysisError("sealed-v1 input changed during analysis")

    counts = {filename: int(len(frame)) for filename, frame in tables.items()}
    counts["analysis_summary.json"] = 1
    counts["analysis_metadata.json"] = 1
    counts["SHA256SUMS"] = len(_read_checksum_inventory(output_root / "SHA256SUMS"))
    counts.update(figure_counts)
    counts.update(report_counts)
    return counts
