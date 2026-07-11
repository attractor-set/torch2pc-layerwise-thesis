from __future__ import annotations

import math
from typing import Any

import numpy as np
import numpy.typing as npt
import pandas as pd
from scipy import stats


def summarize_with_ci(
    frame: pd.DataFrame,
    group_columns: list[str],
    metric_columns: list[str],
    confidence: float = 0.95,
) -> pd.DataFrame:
    if not 0 < confidence < 1:
        raise ValueError("confidence must be in (0, 1)")
    records: list[dict[str, Any]] = []
    for keys, group in frame.groupby(group_columns, dropna=False):
        normalized_keys = keys if isinstance(keys, tuple) else (keys,)
        base = dict(zip(group_columns, normalized_keys, strict=True))
        for metric in metric_columns:
            values = group[metric].dropna().astype(float).to_numpy()
            if values.size and not np.isfinite(values).all():
                raise ValueError(f"Metric contains non-finite values: {metric}")
            count = len(values)
            mean = float(np.mean(values)) if count else np.nan
            std = float(np.std(values, ddof=1)) if count > 1 else np.nan
            if count > 1:
                critical = stats.t.ppf((1 + confidence) / 2, df=count - 1)
                half_width = float(critical * std / math.sqrt(count))
            else:
                half_width = np.nan
            records.append(
                {
                    **base,
                    "metric": metric,
                    "n": count,
                    "mean": mean,
                    "std": std,
                    "ci_low": mean - half_width if np.isfinite(half_width) else np.nan,
                    "ci_high": mean + half_width if np.isfinite(half_width) else np.nan,
                }
            )
    return pd.DataFrame(records)


def _finite_values(values: npt.ArrayLike) -> npt.NDArray[np.float64]:
    array = np.asarray(values, dtype=np.float64).reshape(-1)
    finite = array[np.isfinite(array)]
    return np.asarray(finite, dtype=np.float64)


def cohen_dz(differences: npt.ArrayLike) -> float:
    values = _finite_values(differences)
    if values.size < 2:
        return float("nan")
    mean = float(np.mean(values))
    standard_deviation = float(np.std(values, ddof=1))
    if standard_deviation == 0:
        if mean == 0:
            return 0.0
        return math.copysign(float("inf"), mean)
    return mean / standard_deviation


def mean_difference_ci(
    differences: npt.ArrayLike,
    *,
    confidence: float,
) -> tuple[float, float, float]:
    if not 0 < confidence < 1:
        raise ValueError("confidence must be in (0, 1)")
    values = _finite_values(differences)
    if values.size < 2:
        return float("nan"), float("nan"), float("nan")
    mean = float(values.mean())
    standard_error = float(stats.sem(values))
    critical = float(stats.t.ppf((1 + confidence) / 2, df=values.size - 1))
    half_width = critical * standard_error
    return mean, mean - half_width, mean + half_width


def equivalence_by_ci(
    differences: npt.ArrayLike,
    *,
    margin: float,
    alpha: float = 0.05,
) -> dict[str, float | bool | int]:
    if margin <= 0:
        raise ValueError("Equivalence margin must be positive")
    if not 0 < alpha < 0.5:
        raise ValueError("alpha must be in (0, 0.5)")
    values = _finite_values(differences)
    mean, low, high = mean_difference_ci(values, confidence=1 - 2 * alpha)
    equivalent = bool(values.size >= 2 and low > -margin and high < margin)
    return {
        "n": int(values.size),
        "mean_difference": mean,
        "tost_ci_low": low,
        "tost_ci_high": high,
        "margin": float(margin),
        "equivalent": equivalent,
    }


def exact_sign_flip_pvalue(differences: npt.ArrayLike) -> float:
    values = _finite_values(differences)
    values = values[values != 0]
    n = values.size
    if n == 0:
        return 1.0
    if n > 20:
        result = stats.wilcoxon(values, alternative="two-sided", zero_method="wilcox")
        return float(result.pvalue)
    observed = abs(float(values.mean()))
    extreme = 0
    total = 2**n
    for mask in range(total):
        signs = np.array([1.0 if mask & (1 << i) else -1.0 for i in range(n)])
        candidate = abs(float(np.mean(values * signs)))
        if candidate >= observed - 1e-15:
            extreme += 1
    return float(extreme / total)


def holm_adjust(p_values: list[float]) -> list[float]:
    values = np.asarray(p_values, dtype=float)
    if values.ndim != 1 or not np.isfinite(values).all():
        raise ValueError("p_values must be a finite one-dimensional sequence")
    if ((values < 0) | (values > 1)).any():
        raise ValueError("p_values must be in [0, 1]")
    order = np.argsort(values)
    adjusted = np.empty_like(values)
    running = 0.0
    count = len(values)
    for rank, index in enumerate(order):
        candidate = (count - rank) * values[index]
        running = max(running, candidate)
        adjusted[index] = min(running, 1.0)
    return [float(value) for value in adjusted]
