import pytest
import torch
import torch.nn as nn

from torch2pc_thesis.controls import (
    cosine,
    gradient_map_table,
    named_gradients,
    relative_l2,
)


def test_zero_gradient_vectors_are_treated_as_identical() -> None:
    zero = torch.zeros(4)
    assert cosine(zero, zero) == 1.0
    assert relative_l2(zero, zero) == 0.0


def test_nonzero_candidate_against_zero_reference_is_not_equivalent() -> None:
    zero = torch.zeros(4)
    candidate = torch.ones(4)
    assert cosine(zero, candidate) == 0.0
    assert relative_l2(zero, candidate) == float("inf")


def test_gradient_table_rejects_different_parameter_sets() -> None:
    with pytest.raises(RuntimeError, match="parameter sets differ"):
        gradient_map_table({"weight": torch.ones(2)}, {"bias": torch.ones(2)})


def test_named_gradients_rejects_missing_trainable_gradient() -> None:
    model = nn.Linear(2, 1)
    with pytest.raises(RuntimeError, match="Missing gradients"):
        named_gradients(model)


def test_structural_correction_check_observes_required_patterns(tmp_path) -> None:
    from torch2pc_thesis.controls import structural_correction_check

    source = tmp_path / "TorchSeq2PC.py"
    source.write_text(
        """
def StrictPCPredErrs(model, v, epsilon, n):
    for i in range(n):
        epsilon[layer] = model[layer-1](v[layer-1]) - v[layer]
        dv = epsilon[layer] - epsdfdv

def FixedPredPCPredErrs(model, vhat, v, epsilon):
    epsilon[layer] = vhat[layer] - v[layer]
    dv = epsilon[layer] - epsdfdv

def ExactPredErrs(vhat, epsilon, v):
    v[layer] = vhat[layer] - epsilon[layer]
""".lstrip(),
        encoding="utf-8",
    )

    result = structural_correction_check(source)
    assert result["check_kind"] == "source_pattern_observation"
    assert result["all_observed"] is True
