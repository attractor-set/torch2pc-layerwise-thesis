from __future__ import annotations

from dataclasses import replace

import pandas as pd
import pytest
import torch
import torch.nn as nn

from torch2pc_thesis import pc_methods
from torch2pc_thesis.stage3b_a1_controls import EquivalenceThresholds
from torch2pc_thesis.stage3b_a1_eq_s2 import evaluate_eq_s2


def _fake_fixedpred_backward(
    model: nn.Module,
    loss_fn: nn.Module,
    inputs: torch.Tensor,
    targets: torch.Tensor,
    *,
    method: str,
    torch2pc_dir: object,
    eta: float | None,
    inference_steps: int | None,
) -> None:
    del torch2pc_dir
    assert method == "fixedpred"
    assert eta == 1.0
    assert inference_steps == len(model)  # type: ignore[arg-type]
    loss_fn(model(inputs), targets).backward()


def _base_model() -> nn.Sequential:
    return nn.Sequential(
        nn.Linear(5, 7),
        nn.Tanh(),
        nn.Linear(7, 3),
    ).double()


def test_eq_s2_matches_fixedpred_endpoint_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(pc_methods, "backward_for_method", _fake_fixedpred_backward)
    torch.manual_seed(29)
    model = _base_model()
    inputs = torch.randn(8, 5, dtype=torch.float64)
    targets = torch.randint(0, 3, (8,))
    thresholds = EquivalenceThresholds(
        min_cosine=0.99999,
        max_relative_l2=1e-7,
        zero_atol=1e-12,
    )

    result = evaluate_eq_s2(
        model,
        inputs,
        targets,
        torch2pc_dir="unused",
        seed=29,
        thresholds=thresholds,
        optimizer_factory=lambda parameters: torch.optim.SGD(
            parameters,
            lr=1e-3,
            momentum=0.0,
        ),
    )

    assert result.control_id == "EQ-S2"
    assert result.inference_steps == len(model)
    assert result.eta == 1.0
    assert result.gradient_passed is True
    assert result.parameter_step_passed is True
    assert result.optimizer_state_passed is True
    assert result.structural_contract_passed is True
    assert result.passed is True
    assert result.shortcut_diagnostics.joint_vjp_calls == len(model)


def test_eq_s2_records_frame_has_registered_endpoints(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(pc_methods, "backward_for_method", _fake_fixedpred_backward)
    torch.manual_seed(31)
    model = _base_model()
    result = evaluate_eq_s2(
        model,
        torch.randn(4, 5, dtype=torch.float64),
        torch.randint(0, 3, (4,)),
        torch2pc_dir="unused",
        seed=31,
        thresholds=EquivalenceThresholds(
            min_cosine=0.99999,
            max_relative_l2=1e-7,
            zero_atol=1e-12,
        ),
        optimizer_factory=lambda parameters: torch.optim.SGD(
            parameters,
            lr=1e-3,
            momentum=0.0,
        ),
    )

    frame = result.records_frame()
    assert isinstance(frame, pd.DataFrame)
    counts = frame.groupby("comparison_kind").size().to_dict()
    assert counts == {
        "endpoint_gradient": 4,
        "parameter_after_optimizer_step": 4,
    }


def test_eq_s2_fails_when_structural_contract_is_broken(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(pc_methods, "backward_for_method", _fake_fixedpred_backward)
    torch.manual_seed(37)
    model = _base_model()
    result = evaluate_eq_s2(
        model,
        torch.randn(3, 5, dtype=torch.float64),
        torch.randint(0, 3, (3,)),
        torch2pc_dir="unused",
        seed=37,
        thresholds=EquivalenceThresholds(
            min_cosine=0.99999,
            max_relative_l2=1e-7,
            zero_atol=1e-12,
        ),
        optimizer_factory=lambda parameters: torch.optim.SGD(parameters, lr=1e-3),
    )

    broken_diagnostics = replace(
        result.shortcut_diagnostics,
        joint_vjp_calls=result.shortcut_diagnostics.joint_vjp_calls - 1,
    )
    broken = replace(result, shortcut_diagnostics=broken_diagnostics)
    assert broken.structural_contract_passed is False
    assert broken.passed is False


def test_eq_s2_rejects_non_sequential_model() -> None:
    model = nn.Linear(3, 2)
    with pytest.raises(TypeError, match="top-level nn.Sequential"):
        evaluate_eq_s2(
            model,  # type: ignore[arg-type]
            torch.randn(2, 3),
            torch.tensor([0, 1]),
            torch2pc_dir="unused",
            seed=1,
            thresholds=EquivalenceThresholds(
                min_cosine=0.99,
                max_relative_l2=0.01,
            ),
            optimizer_factory=lambda parameters: torch.optim.SGD(parameters, lr=1e-3),
        )
