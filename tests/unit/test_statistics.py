import numpy as np

from torch2pc_thesis.statistics import (
    cohen_dz,
    equivalence_by_ci,
    exact_sign_flip_pvalue,
    holm_adjust,
)


def test_cohen_dz_positive() -> None:
    assert cohen_dz(np.array([1.0, 2.0, 3.0])) > 0


def test_holm_adjust_is_bounded() -> None:
    adjusted = holm_adjust([0.01, 0.04, 0.20])
    assert all(0 <= value <= 1 for value in adjusted)


def test_equivalence_requires_interval_inside_margin() -> None:
    result = equivalence_by_ci(
        np.array([0.001, -0.001, 0.002, -0.002, 0.0]),
        margin=0.01,
    )
    assert result["equivalent"] is True


def test_exact_sign_flip_detects_zero_centered_difference() -> None:
    p_value = exact_sign_flip_pvalue(np.array([-1.0, -0.5, 0.5, 1.0]))
    assert p_value == 1.0
