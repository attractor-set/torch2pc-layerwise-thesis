import numpy as np

from torch2pc_thesis.representations import linear_cka


def test_linear_cka_identity() -> None:
    rng = np.random.default_rng(42)
    values = rng.normal(size=(50, 8))
    assert abs(linear_cka(values, values) - 1.0) < 1e-10
