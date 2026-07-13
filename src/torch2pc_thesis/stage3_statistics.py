"""Statistical primitives for Stage 3A layer-wise confirmatory analysis."""

from __future__ import annotations

import itertools
import math
from collections.abc import Iterable, Mapping, Sequence
from typing import Final, cast

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from scipy import stats

GRADIENT_METRICS: Final[tuple[str, ...]] = (
    "cosine",
    "relative_l2",
    "norm_ratio",
    "sign_agreement",
)
REPRESENTATION_METRICS: Final[tuple[str, ...]] = (
    "cka",
    "rsa_spearman",
)
GRADIENT_CONTROL_TARGETS: Final[Mapping[str, float]] = {
    "cosine": 1.0,
    "relative_l2": 0.0,
    "norm_ratio": 1.0,
    "sign_agreement": 1.0,
}
REPRESENTATION_CONTROL_TARGETS: Final[Mapping[str, float]] = {
    "cka": 1.0,
    "rsa_spearman": 1.0,
}


def _finite_array(values: Iterable[float]) -> NDArray[np.float64]:
    """Return finite values as a one-dimensional float array."""
    array = np.asarray(list(values), dtype=np.float64).reshape(-1)
    finite = array[np.isfinite(array)]
    return cast(NDArray[np.float64], finite)


def paired_differences(
    reference: Iterable[float],
    candidate: Iterable[float],
) -> NDArray[np.float64]:
    """Return finite candidate-minus-reference paired differences."""
    reference_array = np.asarray(list(reference), dtype=np.float64).reshape(-1)
    candidate_array = np.asarray(list(candidate), dtype=np.float64).reshape(-1)
    if reference_array.shape != candidate_array.shape:
        raise ValueError("reference and candidate must have equal shapes")
    valid = np.isfinite(reference_array) & np.isfinite(candidate_array)
    differences = candidate_array[valid] - reference_array[valid]
    return cast(NDArray[np.float64], differences)


def exact_sign_flip_test(differences: Iterable[float]) -> float:
    """Calculate a two-sided exact sign-flip p-value for the mean difference."""
    values = _finite_array(differences)
    if values.size == 0:
        return math.nan
    observed = abs(float(np.mean(values)))
    extreme = 0
    tolerance = np.finfo(float).eps * max(1.0, observed) * 16.0
    for signs in itertools.product((-1.0, 1.0), repeat=int(values.size)):
        statistic = abs(float(np.mean(values * np.asarray(signs, dtype=float))))
        if statistic + tolerance >= observed:
            extreme += 1
    return float(extreme / (2 ** int(values.size)))


def paired_effect_size_dz(differences: Iterable[float]) -> float:
    """Calculate Cohen's dz from paired differences."""
    values = _finite_array(differences)
    if values.size == 0:
        return math.nan
    mean = float(np.mean(values))
    if values.size < 2:
        return math.nan
    standard_deviation = float(np.std(values, ddof=1))
    if standard_deviation == 0.0:
        if mean == 0.0:
            return 0.0
        return math.copysign(math.inf, mean)
    return mean / standard_deviation


def rank_biserial_correlation(differences: Iterable[float]) -> float:
    """Calculate paired rank-biserial correlation using signed ranks."""
    values = _finite_array(differences)
    nonzero = values[values != 0.0]
    if nonzero.size == 0:
        return 0.0
    ranks = np.asarray(stats.rankdata(np.abs(nonzero), method="average"), dtype=float)
    positive = float(np.sum(ranks[nonzero > 0.0]))
    negative = float(np.sum(ranks[nonzero < 0.0]))
    total = positive + negative
    return (positive - negative) / total if total else 0.0


def mean_confidence_interval(
    values: Iterable[float],
    *,
    confidence: float = 0.95,
) -> tuple[float, float]:
    """Calculate a two-sided Student-t confidence interval for the mean."""
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be between 0 and 1")
    array = _finite_array(values)
    if array.size == 0:
        return math.nan, math.nan
    mean = float(np.mean(array))
    if array.size == 1:
        return mean, mean
    standard_error = float(stats.sem(array))
    if standard_error == 0.0:
        return mean, mean
    critical = float(stats.t.ppf((1.0 + confidence) / 2.0, df=int(array.size) - 1))
    margin = critical * standard_error
    return mean - margin, mean + margin


def holm_adjust(p_values: Sequence[float]) -> list[float]:
    """Apply the step-down Holm correction while preserving input order."""
    if not p_values:
        return []
    values = np.asarray(p_values, dtype=float)
    if np.any(~np.isfinite(values)) or np.any((values < 0.0) | (values > 1.0)):
        raise ValueError("p-values must be finite and lie in [0, 1]")
    order = np.argsort(values, kind="stable")
    adjusted_sorted = np.empty_like(values)
    running = 0.0
    count = len(values)
    for rank, original_index in enumerate(order):
        adjusted_value = min(1.0, (count - rank) * float(values[original_index]))
        running = max(running, adjusted_value)
        adjusted_sorted[rank] = running
    adjusted_values = np.empty_like(values)
    for rank, original_index in enumerate(order):
        adjusted_values[original_index] = adjusted_sorted[rank]
    return [float(value) for value in adjusted_values]


def _require_columns(frame: pd.DataFrame, required: set[str]) -> None:
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"missing required columns: {', '.join(missing)}")


def aggregate_gradient_seed_level(frame: pd.DataFrame) -> pd.DataFrame:
    """Aggregate top-level batch metrics to one long-form value per seed and layer."""
    required = {
        "dataset",
        "model",
        "model_seed",
        "checkpoint_label",
        "batch_id",
        "method",
        "scope",
        "unit",
        "cosine",
        "cosine_defined",
        "relative_l2",
        "norm_ratio",
        "sign_agreement",
    }
    _require_columns(frame, required)
    top_level = frame.loc[frame["scope"] == "top_level"].copy()
    if top_level.empty:
        raise ValueError("gradient table contains no top_level observations")
    top_level["layer"] = pd.to_numeric(top_level["unit"], errors="raise").astype(int)
    top_level.loc[~top_level["cosine_defined"].astype(bool), "cosine"] = np.nan
    keys = [
        "dataset",
        "model",
        "checkpoint_label",
        "model_seed",
        "method",
        "layer",
    ]
    rows: list[dict[str, object]] = []
    for key, group in top_level.groupby(keys, sort=True, dropna=False):
        key_values = key if isinstance(key, tuple) else (key,)
        base = dict(zip(keys, key_values, strict=True))
        for metric in GRADIENT_METRICS:
            values = pd.to_numeric(group[metric], errors="coerce").to_numpy(dtype=float)
            finite = values[np.isfinite(values)]
            rows.append(
                {
                    **base,
                    "metric": metric,
                    "value": float(np.mean(finite)) if finite.size else math.nan,
                    "n_observations": int(finite.size),
                    "n_missing": int(values.size - finite.size),
                }
            )
    return pd.DataFrame(rows).sort_values(keys + ["metric"], ignore_index=True)


def aggregate_representation_seed_level(frame: pd.DataFrame) -> pd.DataFrame:
    """Convert corresponding-layer CKA/RSA observations to canonical long form."""
    required = {
        "dataset",
        "model",
        "model_seed",
        "reference_label",
        "candidate_label",
        "layer",
        "cka",
        "rsa_spearman",
        "rsa_defined",
    }
    _require_columns(frame, required)
    corresponding = frame.loc[frame["reference_label"] == "bp"].copy()
    if corresponding.empty:
        raise ValueError("representation table contains no BP reference observations")
    corresponding.loc[~corresponding["rsa_defined"].astype(bool), "rsa_spearman"] = np.nan
    keys = ["dataset", "model", "model_seed", "candidate_label", "layer"]
    rows: list[dict[str, object]] = []
    for _, row in corresponding.sort_values(keys).iterrows():
        base = {
            "dataset": row["dataset"],
            "model": row["model"],
            "model_seed": int(row["model_seed"]),
            "method": row["candidate_label"],
            "layer": int(row["layer"]),
        }
        for metric in REPRESENTATION_METRICS:
            value = float(row[metric]) if pd.notna(row[metric]) else math.nan
            rows.append(
                {
                    **base,
                    "metric": metric,
                    "value": value,
                    "n_observations": int(math.isfinite(value)),
                    "n_missing": int(not math.isfinite(value)),
                }
            )
    sort_columns = keys[:-2] + ["method", "layer", "metric"]
    return pd.DataFrame(rows).sort_values(sort_columns, ignore_index=True)


def comparison_statistics(
    seed_level: pd.DataFrame,
    *,
    targets: Mapping[str, float],
    candidate_methods: Sequence[str] = ("fixedpred", "strict"),
    confidence: float = 0.95,
) -> pd.DataFrame:
    """Compare seed-level candidate metrics with their registered BP targets."""
    required = {"dataset", "model", "model_seed", "method", "layer", "metric", "value"}
    _require_columns(seed_level, required)
    grouping = ["dataset", "model", "layer", "metric"]
    if "checkpoint_label" in seed_level.columns:
        grouping.insert(2, "checkpoint_label")
    output_rows: list[dict[str, object]] = []
    for method in candidate_methods:
        candidate = seed_level.loc[seed_level["method"] == method].copy()
        for key, group in candidate.groupby(grouping, sort=True, dropna=False):
            key_values = key if isinstance(key, tuple) else (key,)
            base = dict(zip(grouping, key_values, strict=True))
            metric = str(base["metric"])
            if metric not in targets:
                raise ValueError(f"missing registered target for metric: {metric}")
            target = float(targets[metric])
            values = _finite_array(group["value"])
            differences = values - target
            ci_low, ci_high = mean_confidence_interval(differences, confidence=confidence)
            output_rows.append(
                {
                    **base,
                    "method": method,
                    "reference": "bp_target",
                    "target_value": target,
                    "n": int(differences.size),
                    "candidate_mean": float(np.mean(values)) if values.size else math.nan,
                    "candidate_median": float(np.median(values)) if values.size else math.nan,
                    "mean_difference": (
                        float(np.mean(differences)) if differences.size else math.nan
                    ),
                    "median_difference": (
                        float(np.median(differences)) if differences.size else math.nan
                    ),
                    "difference_ci_low": ci_low,
                    "difference_ci_high": ci_high,
                    "cohen_dz": paired_effect_size_dz(differences),
                    "rank_biserial": rank_biserial_correlation(differences),
                    "p_value": exact_sign_flip_test(differences),
                }
            )
    result = pd.DataFrame(output_rows)
    if result.empty:
        return result
    result["p_value_holm"] = math.nan
    for _, indexes in result.groupby("method", sort=True).groups.items():
        index_list = list(indexes)
        adjusted = holm_adjust([float(result.loc[index, "p_value"]) for index in index_list])
        result.loc[index_list, "p_value_holm"] = adjusted
    sort_columns = [
        column
        for column in ["dataset", "model", "method", "layer", "metric"]
        if column in result
    ]
    return result.sort_values(sort_columns, ignore_index=True)


def exact_numerical_control(
    seed_level: pd.DataFrame,
    *,
    targets: Mapping[str, float],
    tolerances: Mapping[str, float],
    exact_method: str = "exact",
) -> pd.DataFrame:
    """Evaluate Exact against registered BP targets without hypothesis testing."""
    required = {"dataset", "model", "model_seed", "method", "layer", "metric", "value"}
    _require_columns(seed_level, required)
    exact = seed_level.loc[seed_level["method"] == exact_method].copy()
    grouping = ["dataset", "model", "layer", "metric"]
    if "checkpoint_label" in seed_level.columns:
        grouping.insert(2, "checkpoint_label")
    rows: list[dict[str, object]] = []
    for key, group in exact.groupby(grouping, sort=True, dropna=False):
        key_values = key if isinstance(key, tuple) else (key,)
        base = dict(zip(grouping, key_values, strict=True))
        metric = str(base["metric"])
        if metric not in targets or metric not in tolerances:
            raise ValueError(f"missing target or tolerance for metric: {metric}")
        target = float(targets[metric])
        tolerance = float(tolerances[metric])
        if tolerance < 0.0:
            raise ValueError(f"tolerance must be non-negative for metric: {metric}")
        values = _finite_array(group["value"])
        errors = np.abs(values - target)
        max_error = float(np.max(errors)) if errors.size else math.nan
        rows.append(
            {
                **base,
                "method": exact_method,
                "target_value": target,
                "absolute_tolerance": tolerance,
                "n": int(values.size),
                "mean_abs_error": float(np.mean(errors)) if errors.size else math.nan,
                "max_abs_error": max_error,
                "passed": bool(errors.size and max_error <= tolerance),
            }
        )
    return pd.DataFrame(rows).sort_values(grouping, ignore_index=True)
