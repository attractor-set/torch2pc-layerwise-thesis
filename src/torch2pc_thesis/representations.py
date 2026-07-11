from __future__ import annotations

import numpy as np
from scipy import stats


def center_features(features: np.ndarray) -> np.ndarray:
    return features - features.mean(axis=0, keepdims=True)


def linear_cka(left: np.ndarray, right: np.ndarray, epsilon: float = 1e-12) -> float:
    x = center_features(left)
    y = center_features(right)
    numerator = np.linalg.norm(x.T @ y, ord="fro") ** 2
    denominator = (
        np.linalg.norm(x.T @ x, ord="fro")
        * np.linalg.norm(y.T @ y, ord="fro")
        + epsilon
    )
    return float(numerator / denominator)


def upper_triangle_vector(matrix: np.ndarray) -> np.ndarray:
    indices = np.triu_indices_from(matrix, k=1)
    return matrix[indices]


def rsa_spearman(left: np.ndarray, right: np.ndarray) -> float:
    left_rdm = 1.0 - np.corrcoef(left)
    right_rdm = 1.0 - np.corrcoef(right)
    coefficient = stats.spearmanr(
        upper_triangle_vector(left_rdm),
        upper_triangle_vector(right_rdm),
    ).statistic
    return float(coefficient)
