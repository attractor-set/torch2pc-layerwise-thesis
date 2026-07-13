"""Depth-trend analysis for Stage 3A layer-wise confirmatory metrics."""

from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import subprocess
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
import scipy
from numpy.typing import NDArray
from scipy import stats

from torch2pc_thesis.stage3_statistics import (
    GRADIENT_METRICS,
    REPRESENTATION_METRICS,
    exact_sign_flip_test,
    holm_adjust,
    mean_confidence_interval,
    paired_effect_size_dz,
    rank_biserial_correlation,
)

EXPECTED_SEEDS: Final[tuple[int, ...]] = tuple(range(10))
EXPECTED_METHODS: Final[tuple[str, ...]] = ("exact", "fixedpred", "strict")
CANDIDATE_METHODS: Final[tuple[str, ...]] = ("fixedpred", "strict")
DEPTH_STATISTICS: Final[tuple[str, ...]] = ("spearman_rho", "linear_slope")
DEFAULT_CONFIDENCE: Final[float] = 0.95
DEFAULT_EXACT_TOLERANCE: Final[float] = 1e-12
EXPECTED_METRICS_BY_DOMAIN: Final[dict[str, tuple[str, ...]]] = {
    "gradient": GRADIENT_METRICS,
    "representation": REPRESENTATION_METRICS,
}

GRADIENT_INPUT: Final[str] = "seed_level_gradient_metrics.csv"
REPRESENTATION_INPUT: Final[str] = "seed_level_representation_metrics.csv"
DEPTH_OUTPUT_FILENAMES: Final[tuple[str, ...]] = (
    "depth_seed_level.csv",
    "depth_statistics.csv",
)
METADATA_FILENAME: Final[str] = "depth_analysis_metadata.json"


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_columns(frame: pd.DataFrame, required: set[str]) -> None:
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"missing required columns: {', '.join(missing)}")


def _normalized_depth(layer_values: pd.Series) -> NDArray[np.float64]:
    layers = sorted(int(layer) for layer in layer_values.unique())
    if len(layers) < 2:
        raise ValueError("depth analysis requires at least two distinct layers")
    denominator = float(len(layers) - 1)
    depth_by_layer = {layer: index / denominator for index, layer in enumerate(layers)}
    return np.asarray(
        [depth_by_layer[int(layer)] for layer in layer_values],
        dtype=np.float64,
    )


def _linear_slope(
    depth: NDArray[np.float64],
    values: NDArray[np.float64],
) -> float:
    centered_depth = depth - float(np.mean(depth))
    centered_values = values - float(np.mean(values))
    denominator = float(np.sum(centered_depth * centered_depth))
    if denominator == 0.0:
        return math.nan
    return float(np.sum(centered_depth * centered_values) / denominator)


def _spearman_rho(
    depth: NDArray[np.float64],
    values: NDArray[np.float64],
) -> float:
    if np.all(values == values[0]):
        return math.nan
    result = stats.spearmanr(depth, values)
    return float(result.statistic)


def build_depth_seed_level(
    seed_level: pd.DataFrame,
    *,
    domain: str,
) -> pd.DataFrame:
    """Calculate one depth-trend record per seed, method, and metric."""
    required = {
        "dataset",
        "model",
        "model_seed",
        "method",
        "layer",
        "metric",
        "value",
    }
    _require_columns(seed_level, required)
    if not domain:
        raise ValueError("domain must be non-empty")

    identity_columns = [
        "dataset",
        "model",
        "model_seed",
        "method",
        "layer",
        "metric",
    ]
    if "checkpoint_label" in seed_level.columns:
        identity_columns.insert(2, "checkpoint_label")
    if bool(seed_level.duplicated(identity_columns, keep=False).any()):
        raise ValueError("seed-level table contains duplicate layer observations")

    grouping = ["dataset", "model", "model_seed", "method", "metric"]
    if "checkpoint_label" in seed_level.columns:
        grouping.insert(2, "checkpoint_label")

    rows: list[dict[str, object]] = []
    for key, group in seed_level.groupby(grouping, sort=True, dropna=False):
        key_values = key if isinstance(key, tuple) else (key,)
        base = dict(zip(grouping, key_values, strict=True))
        ordered = group.sort_values("layer", kind="stable")
        depth = _normalized_depth(ordered["layer"])
        raw_values = pd.to_numeric(ordered["value"], errors="coerce").to_numpy(
            dtype=np.float64
        )
        valid = np.isfinite(raw_values)
        valid_depth = depth[valid]
        values = raw_values[valid]

        if values.size >= 2:
            spearman_rho = _spearman_rho(valid_depth, values)
            linear_slope = _linear_slope(valid_depth, values)
            depth_min = float(np.min(valid_depth))
            depth_max = float(np.max(valid_depth))
            value_min = float(np.min(values))
            value_max = float(np.max(values))
        else:
            spearman_rho = math.nan
            linear_slope = math.nan
            depth_min = math.nan
            depth_max = math.nan
            value_min = math.nan
            value_max = math.nan

        rows.append(
            {
                "domain": domain,
                **base,
                "n_layers": int(raw_values.size),
                "n_valid_layers": int(values.size),
                "n_missing_layers": int(raw_values.size - values.size),
                "depth_min": depth_min,
                "depth_max": depth_max,
                "value_min": value_min,
                "value_max": value_max,
                "spearman_rho": spearman_rho,
                "linear_slope": linear_slope,
            }
        )

    if not rows:
        return pd.DataFrame()
    result = pd.DataFrame(rows)
    sort_columns = [
        column
        for column in [
            "domain",
            "dataset",
            "model",
            "checkpoint_label",
            "model_seed",
            "method",
            "metric",
        ]
        if column in result.columns
    ]
    return result.sort_values(sort_columns, ignore_index=True)


def combine_depth_seed_level(
    gradient_seed_level: pd.DataFrame,
    representation_seed_level: pd.DataFrame,
) -> pd.DataFrame:
    """Combine gradient and representation depth trends into canonical form."""
    gradient = build_depth_seed_level(gradient_seed_level, domain="gradient")
    representation = build_depth_seed_level(
        representation_seed_level,
        domain="representation",
    )
    combined = pd.concat([gradient, representation], ignore_index=True, sort=False)
    sort_columns = [
        "domain",
        "dataset",
        "model",
        "checkpoint_label",
        "model_seed",
        "method",
        "metric",
    ]
    present = [column for column in sort_columns if column in combined.columns]
    return combined.sort_values(present, ignore_index=True)


def _validate_expected_coverage(
    depth_seed_level: pd.DataFrame,
    *,
    expected_seeds: Sequence[int],
) -> None:
    expected = tuple(sorted(int(seed) for seed in expected_seeds))
    for domain, expected_metrics in EXPECTED_METRICS_BY_DOMAIN.items():
        domain_rows = depth_seed_level.loc[depth_seed_level["domain"] == domain]
        if domain_rows.empty:
            raise ValueError(f"depth analysis is missing domain: {domain}")
        actual_methods = set(str(method) for method in domain_rows["method"].unique())
        missing_methods = sorted(set(EXPECTED_METHODS) - actual_methods)
        if missing_methods:
            raise ValueError(
                f"depth analysis is missing {domain} methods: {', '.join(missing_methods)}"
            )
        actual_metrics = set(str(metric) for metric in domain_rows["metric"].unique())
        missing_metrics = sorted(set(expected_metrics) - actual_metrics)
        unexpected_metrics = sorted(actual_metrics - set(expected_metrics))
        if missing_metrics or unexpected_metrics:
            raise ValueError(
                f"depth {domain} metrics differ from the frozen plan: "
                f"missing={missing_metrics}, unexpected={unexpected_metrics}"
            )
        for method in EXPECTED_METHODS:
            for metric in expected_metrics:
                group = domain_rows.loc[
                    (domain_rows["method"] == method)
                    & (domain_rows["metric"] == metric)
                ]
                actual = tuple(
                    sorted(int(seed) for seed in group["model_seed"].unique())
                )
                if actual != expected:
                    raise ValueError(
                        "depth seeds differ from the frozen plan: "
                        f"domain={domain}, method={method}, metric={metric}, "
                        f"expected={expected}, actual={actual}"
                    )
    if bool((depth_seed_level["n_valid_layers"] < 2).any()):
        raise ValueError("depth analysis contains groups with fewer than two valid layers")
    candidate = depth_seed_level.loc[
        depth_seed_level["method"].isin(CANDIDATE_METHODS)
    ]
    for statistic in DEPTH_STATISTICS:
        values = pd.to_numeric(candidate[statistic], errors="coerce").to_numpy(
            dtype=np.float64
        )
        if np.any(~np.isfinite(values)):
            raise ValueError(
                f"candidate depth statistic contains undefined values: {statistic}"
            )


def depth_statistics(
    depth_seed_level: pd.DataFrame,
    *,
    candidate_methods: Sequence[str] = CANDIDATE_METHODS,
    confidence: float = DEFAULT_CONFIDENCE,
) -> pd.DataFrame:
    """Analyze seed-level depth coefficients relative to a zero trend."""
    required = {
        "domain",
        "dataset",
        "model",
        "model_seed",
        "method",
        "metric",
        "spearman_rho",
        "linear_slope",
    }
    _require_columns(depth_seed_level, required)
    grouping = ["domain", "dataset", "model", "metric"]
    if "checkpoint_label" in depth_seed_level.columns:
        grouping.insert(3, "checkpoint_label")

    rows: list[dict[str, object]] = []
    for method in candidate_methods:
        candidate = depth_seed_level.loc[depth_seed_level["method"] == method]
        for key, group in candidate.groupby(grouping, sort=True, dropna=False):
            key_values = key if isinstance(key, tuple) else (key,)
            base = dict(zip(grouping, key_values, strict=True))
            for statistic in DEPTH_STATISTICS:
                raw_values = pd.to_numeric(group[statistic], errors="coerce").to_numpy(
                    dtype=np.float64
                )
                values = raw_values[np.isfinite(raw_values)]
                ci_low, ci_high = mean_confidence_interval(values, confidence=confidence)
                inferential = statistic == "spearman_rho"
                rows.append(
                    {
                        **base,
                        "method": method,
                        "statistic": statistic,
                        "analysis_role": (
                            "confirmatory" if inferential else "descriptive"
                        ),
                        "reference": "zero_depth_trend",
                        "target_value": 0.0,
                        "n": int(values.size),
                        "n_missing": int(raw_values.size - values.size),
                        "candidate_mean": (
                            float(np.mean(values)) if values.size else math.nan
                        ),
                        "candidate_median": (
                            float(np.median(values)) if values.size else math.nan
                        ),
                        "candidate_std": (
                            float(np.std(values, ddof=1)) if values.size > 1 else math.nan
                        ),
                        "candidate_min": (
                            float(np.min(values)) if values.size else math.nan
                        ),
                        "candidate_max": (
                            float(np.max(values)) if values.size else math.nan
                        ),
                        "mean_difference": (
                            float(np.mean(values)) if values.size else math.nan
                        ),
                        "median_difference": (
                            float(np.median(values)) if values.size else math.nan
                        ),
                        "difference_ci_low": ci_low,
                        "difference_ci_high": ci_high,
                        "cohen_dz": (
                            paired_effect_size_dz(values) if inferential else math.nan
                        ),
                        "rank_biserial": (
                            rank_biserial_correlation(values)
                            if inferential
                            else math.nan
                        ),
                        "p_value": (
                            exact_sign_flip_test(values) if inferential else math.nan
                        ),
                    }
                )

    result = pd.DataFrame(rows)
    if result.empty:
        return result
    result["p_value_holm"] = math.nan
    inferential_rows = result.loc[result["statistic"] == "spearman_rho"]
    family_columns = ["domain", "method"]
    for _, indexes in inferential_rows.groupby(family_columns, sort=True).groups.items():
        index_list = list(indexes)
        adjusted = holm_adjust([float(result.loc[index, "p_value"]) for index in index_list])
        result.loc[index_list, "p_value_holm"] = adjusted
    sort_columns = [
        column
        for column in [
            "domain",
            "dataset",
            "model",
            "method",
            "metric",
            "statistic",
        ]
        if column in result.columns
    ]
    return result.sort_values(sort_columns, ignore_index=True)


def _validate_exact_depth_control(
    depth_seed_level: pd.DataFrame,
    *,
    tolerance: float,
) -> dict[str, float | int]:
    if tolerance < 0.0:
        raise ValueError("exact_tolerance must be non-negative")
    exact = depth_seed_level.loc[depth_seed_level["method"] == "exact"].copy()
    if exact.empty:
        raise ValueError("depth analysis contains no Exact rows")
    value_ranges = pd.to_numeric(
        exact["value_max"] - exact["value_min"],
        errors="coerce",
    ).to_numpy(dtype=np.float64)
    slopes = pd.to_numeric(exact["linear_slope"], errors="coerce").to_numpy(
        dtype=np.float64
    )
    if np.any(~np.isfinite(value_ranges)) or np.any(~np.isfinite(slopes)):
        raise ValueError("Exact depth control contains undefined ranges or slopes")
    max_range = float(np.max(np.abs(value_ranges)))
    max_slope = float(np.max(np.abs(slopes)))
    if max_range > tolerance or max_slope > tolerance:
        raise ValueError(
            "Exact depth control failed: "
            f"max_value_range={max_range}, max_abs_slope={max_slope}, "
            f"tolerance={tolerance}"
        )
    return {
        "rows": int(len(exact)),
        "max_value_range": max_range,
        "max_abs_slope": max_slope,
        "absolute_tolerance": tolerance,
    }


def build_stage3a_depth_tables(
    gradient_seed_level: pd.DataFrame,
    representation_seed_level: pd.DataFrame,
    *,
    expected_seeds: Sequence[int] = EXPECTED_SEEDS,
    confidence: float = DEFAULT_CONFIDENCE,
    exact_tolerance: float = DEFAULT_EXACT_TOLERANCE,
) -> tuple[dict[str, pd.DataFrame], dict[str, float | int]]:
    """Build deterministic Stage 3A depth tables in memory."""
    combined = combine_depth_seed_level(
        gradient_seed_level,
        representation_seed_level,
    )
    _validate_expected_coverage(combined, expected_seeds=expected_seeds)
    exact_control = _validate_exact_depth_control(
        combined,
        tolerance=exact_tolerance,
    )
    statistics_frame = depth_statistics(combined, confidence=confidence)
    expected_n = len(tuple(expected_seeds))
    if statistics_frame.empty or not bool(statistics_frame["n"].eq(expected_n).all()):
        raise ValueError("depth statistics do not contain every expected seed")
    return (
        {
            "depth_seed_level.csv": combined,
            "depth_statistics.csv": statistics_frame,
        },
        exact_control,
    )


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(
        path,
        index=False,
        lineterminator="\n",
        na_rep="",
        float_format="%.17g",
    )


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
        timestamp = int(source_date_epoch)
        return datetime.fromtimestamp(timestamp, tz=UTC).isoformat().replace("+00:00", "Z")
    return datetime.now(tz=UTC).isoformat().replace("+00:00", "Z")


def generate_stage3a_depth_tables(
    statistics_dir: Path,
    output_dir: Path,
    *,
    repo_root: Path,
    expected_seeds: Sequence[int] = EXPECTED_SEEDS,
    confidence: float = DEFAULT_CONFIDENCE,
    exact_tolerance: float = DEFAULT_EXACT_TOLERANCE,
    source_commit: str | None = None,
    generated_at_utc: str | None = None,
) -> dict[str, int]:
    """Generate depth CSV outputs and provenance-rich metadata."""
    gradient_path = statistics_dir / GRADIENT_INPUT
    representation_path = statistics_dir / REPRESENTATION_INPUT
    for path in (gradient_path, representation_path):
        if not path.is_file():
            raise FileNotFoundError(path)

    gradient_frame = pd.read_csv(gradient_path)
    representation_frame = pd.read_csv(representation_path)
    tables, exact_control = build_stage3a_depth_tables(
        gradient_frame,
        representation_frame,
        expected_seeds=expected_seeds,
        confidence=confidence,
        exact_tolerance=exact_tolerance,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    for filename in DEPTH_OUTPUT_FILENAMES:
        _write_csv(tables[filename], output_dir / filename)

    resolved_commit = source_commit or _resolve_source_commit(repo_root)
    resolved_time = _resolve_generated_at(generated_at_utc)
    output_metadata = {
        filename: {
            "rows": int(len(tables[filename])),
            "sha256": sha256_file(output_dir / filename),
        }
        for filename in DEPTH_OUTPUT_FILENAMES
    }
    metadata: dict[str, object] = {
        "schema_version": 1,
        "analysis": "stage3a-layerwise-depth-trends",
        "generated_at_utc": resolved_time,
        "source_commit": resolved_commit,
        "inputs": {
            GRADIENT_INPUT: {
                "rows": int(len(gradient_frame)),
                "sha256": sha256_file(gradient_path),
            },
            REPRESENTATION_INPUT: {
                "rows": int(len(representation_frame)),
                "sha256": sha256_file(representation_path),
            },
        },
        "outputs": output_metadata,
        "settings": {
            "independent_unit": "model_seed",
            "expected_seeds": [int(seed) for seed in expected_seeds],
            "candidate_methods": list(CANDIDATE_METHODS),
            "confidence": confidence,
            "depth_mapping": "ordinal layer rank mapped to [0, 1] within each group",
            "seed_level_statistics": list(DEPTH_STATISTICS),
            "confirmatory_statistic": "spearman_rho",
            "descriptive_statistic": "linear_slope",
            "exact_sign_flip": "two-sided exhaustive sign assignments relative to zero",
            "holm_family_keys": ["domain", "method"],
            "exact_absolute_tolerance": exact_tolerance,
        },
        "exact_control": exact_control,
        "software": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
        },
    }
    metadata_path = output_dir / METADATA_FILENAME
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    counts = {
        filename: int(len(tables[filename])) for filename in DEPTH_OUTPUT_FILENAMES
    }
    counts[METADATA_FILENAME] = 1
    return counts
