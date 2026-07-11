from __future__ import annotations

import numpy as np
import numpy.typing as npt
from scipy import stats

from torch2pc_thesis.array_types import FloatArray


def _finite_matrix(name: str, values: npt.ArrayLike, *, minimum_rows: int = 2) -> FloatArray:
    matrix: FloatArray = np.asarray(values, dtype=np.float64)
    if matrix.ndim != 2:
        raise ValueError(f"{name} must be a two-dimensional matrix")
    if matrix.shape[0] < minimum_rows:
        raise ValueError(f"{name} must contain at least {minimum_rows} observations")
    if matrix.shape[1] < 1:
        raise ValueError(f"{name} must contain at least one feature")
    if not np.isfinite(matrix).all():
        raise ValueError(f"{name} contains non-finite values")
    return matrix


def center_features(features: npt.ArrayLike) -> FloatArray:
    values = _finite_matrix("features", features)
    mean: FloatArray = np.asarray(values.mean(axis=0, keepdims=True), dtype=np.float64)
    centered: FloatArray = np.subtract(values, mean)
    return centered


def linear_cka(left: npt.ArrayLike, right: npt.ArrayLike, epsilon: float = 1e-12) -> float:
    if epsilon <= 0:
        raise ValueError("epsilon must be positive")
    x = center_features(left)
    y = center_features(right)
    if x.shape[0] != y.shape[0]:
        raise ValueError("CKA inputs must contain the same observations")
    numerator = float(np.linalg.norm(x.T @ y, ord="fro") ** 2)
    denominator = float(
        np.linalg.norm(x.T @ x, ord="fro") * np.linalg.norm(y.T @ y, ord="fro")
    )
    if denominator <= epsilon:
        raise ValueError("CKA is undefined for a degenerate representation")
    return numerator / denominator


def upper_triangle_vector(matrix: npt.ArrayLike) -> FloatArray:
    values = _finite_matrix("matrix", matrix)
    if values.shape[0] != values.shape[1]:
        raise ValueError("matrix must be square")
    indices = np.triu_indices_from(values, k=1)
    vector: FloatArray = np.asarray(values[indices], dtype=np.float64)
    return vector


def rsa_spearman(left: npt.ArrayLike, right: npt.ArrayLike) -> float:
    x = _finite_matrix("left", left, minimum_rows=3)
    y = _finite_matrix("right", right, minimum_rows=3)
    if x.shape[0] != y.shape[0]:
        raise ValueError("RSA inputs must contain the same observations")
    left_rdm: FloatArray = np.asarray(1.0 - np.corrcoef(x), dtype=np.float64)
    right_rdm: FloatArray = np.asarray(1.0 - np.corrcoef(y), dtype=np.float64)
    if not np.isfinite(left_rdm).all() or not np.isfinite(right_rdm).all():
        raise ValueError("RSA is undefined for a degenerate representation")
    coefficient = stats.spearmanr(
        upper_triangle_vector(left_rdm),
        upper_triangle_vector(right_rdm),
    ).statistic
    if not np.isfinite(coefficient):
        raise ValueError("RSA produced a non-finite coefficient")
    return float(coefficient)
