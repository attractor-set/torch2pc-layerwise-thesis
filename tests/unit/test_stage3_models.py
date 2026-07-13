from __future__ import annotations

import pytest
import torch

from torch2pc_thesis.models import build_model, make_scaling_mlp


def test_scaling_mlp_family_has_declared_module_depth() -> None:
    for depth in (4, 8, 16, 32):
        model = build_model(f"mlp_d{depth}_w64")
        assert len(model) == depth
        output = model(torch.zeros(2, 1, 28, 28))
        assert output.shape == (2, 10)


def test_scaling_mlp_rejects_invalid_shape_parameters() -> None:
    with pytest.raises(ValueError, match="depth"):
        make_scaling_mlp(1, 64)
    with pytest.raises(ValueError, match="width"):
        make_scaling_mlp(4, 0)
