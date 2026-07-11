import numpy as np
import pytest

from torch2pc_thesis.data import _load_or_create_split


def test_existing_split_must_match_deterministic_reconstruction(tmp_path) -> None:
    path = tmp_path / "split.npz"
    expected = {
        "train_idx": np.array([0, 2], dtype=np.int64),
        "validation_idx": np.array([1], dtype=np.int64),
    }
    _load_or_create_split(path, expected)
    _load_or_create_split(path, expected)
    changed = {**expected, "train_idx": np.array([0, 3], dtype=np.int64)}
    with pytest.raises(RuntimeError, match="differs"):
        _load_or_create_split(path, changed)
