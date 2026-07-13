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


def test_two_torch2pc_implementations_can_be_loaded_independently(tmp_path) -> None:
    from torch2pc_thesis.pc_methods import load_pc_infer

    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    (first / "TorchSeq2PC.py").write_text(
        "def PCInfer(*args, **kwargs):\n    return 'first'\n", encoding="utf-8"
    )
    (second / "TorchSeq2PC.py").write_text(
        "def PCInfer(*args, **kwargs):\n    return 'second'\n", encoding="utf-8"
    )

    assert load_pc_infer(first)() == "first"
    assert load_pc_infer(second)() == "second"


def test_structural_correction_check_accepts_optimized_aliases(tmp_path) -> None:
    from torch2pc_thesis.controls import structural_correction_check

    source = tmp_path / "TorchSeq2PC.py"
    source.write_text(
        """
def StrictPCPredErrs(model, v, epsilon, n):
    for i in range(n):
        epsilon[layer] = lower_output - v[layer]
        dv = epsilon[layer] - epsdfdv

def FixedPredPCPredErrs(model, fixed, v, epsilon):
    epsilon[layer] = fixed[layer] - v[layer]
    dv = epsilon[layer] - epsdfdv

def ExactPredErrs(vhat, epsilon, v):
    v[layer] = vhat[layer] - epsilon[layer]
""".lstrip(),
        encoding="utf-8",
    )

    assert structural_correction_check(source)["all_observed"] is True


def test_state_comparison_accepts_identical_implementations(tmp_path) -> None:
    from torch2pc_thesis.controls import implementation_state_comparison

    source = tmp_path / "implementation"
    source.mkdir()
    (source / "TorchSeq2PC.py").write_text(
        """
import torch

def PCInfer(model, loss_fn, inputs, targets, method, eta=.1, n=20):
    output = model(inputs)
    loss = loss_fn(output, targets)
    dldy = torch.autograd.grad(loss, output, retain_graph=True)[0]
    loss.backward()
    values = [inputs, output]
    errors = [None, dldy]
    return values, loss, dldy, values, errors
""".lstrip(),
        encoding="utf-8",
    )
    model = nn.Sequential(nn.Linear(2, 2)).double()
    inputs = torch.randn(4, 2, dtype=torch.float64)
    targets = torch.randint(0, 2, (4,))
    result = implementation_state_comparison(
        model,
        inputs,
        targets,
        reference_torch2pc_dir=source,
        candidate_torch2pc_dir=source,
        method="exact",
        seed=0,
    )
    assert result["max_abs"].max() == 0.0
    assert result["relative_l2"].max() == 0.0
