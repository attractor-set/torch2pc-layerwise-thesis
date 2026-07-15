from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import pytest
import torch
import torch.nn as nn

import torch2pc_thesis.stage3b_a1_controls as controls
from torch2pc_thesis.stage3b_a1_controls import (
    EquivalenceThresholds,
    ObserverMode,
    ObserverSnapshot,
    ZeroRelation,
    compare_observer_snapshots,
    compare_tensor,
    evaluate_eq_s0,
    validate_execution_lane,
)


def thresholds() -> EquivalenceThresholds:
    return EquivalenceThresholds(min_cosine=0.999, max_relative_l2=1e-6)


def test_compare_tensor_marks_two_zero_tensors_as_zero_match() -> None:
    result = compare_tensor("zero", torch.zeros(3), torch.zeros(3), thresholds())

    assert result.zero_relation is ZeroRelation.BOTH_ZERO
    assert result.cosine is None
    assert result.relative_l2 is None
    assert result.passed


def test_compare_tensor_rejects_one_sided_zero() -> None:
    result = compare_tensor("one-sided", torch.zeros(2), torch.ones(2), thresholds())

    assert result.zero_relation is ZeroRelation.REFERENCE_ZERO
    assert not result.passed


def test_compare_tensor_rejects_nonfinite_values() -> None:
    result = compare_tensor("nan", torch.ones(1), torch.tensor([float("nan")]), thresholds())

    assert not result.finite
    assert not result.passed


def test_compare_observer_snapshots_compares_semantic_outputs() -> None:
    reference = ObserverSnapshot(
        mode=ObserverMode.NO_HOOKS,
        gradients={"weight": torch.tensor([1.0, 2.0])},
        parameters={"weight": torch.tensor([3.0, 4.0])},
        loss=torch.tensor(0.5),
        errors={"layer-1": torch.zeros(2)},
    )
    candidate = ObserverSnapshot(
        mode=ObserverMode.COUNTERS_ONLY,
        gradients={"weight": torch.tensor([1.0, 2.0])},
        parameters={"weight": torch.tensor([3.0, 4.0])},
        loss=torch.tensor(0.5),
        errors={"layer-1": torch.zeros(2)},
    )

    result = compare_observer_snapshots(reference, candidate, thresholds())

    assert result.passed
    assert len(result.records) == 4


def test_evaluate_eq_s0_accepts_matching_gradient_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_seed(seed: int) -> None:
        assert seed == 7

    def fake_backward(
        model: nn.Module,
        inputs: torch.Tensor,
        targets: torch.Tensor,
        *,
        method: str,
        torch2pc_dir: str | Path,
        eta: float | None,
        inference_steps: int | None,
    ) -> None:
        del targets, torch2pc_dir
        if method == "fixedpred":
            assert eta == 1.0
            assert inference_steps == len(model)
        output = model(inputs)
        output.sum().backward()

    monkeypatch.setattr(controls, "_set_global_seed", fake_seed)
    monkeypatch.setattr(controls, "_run_backward", fake_backward)
    model = nn.Sequential(nn.Linear(2, 3), nn.Linear(3, 2))
    inputs = torch.tensor([[1.0, -1.0]])
    targets = torch.tensor([0])

    def optimizer_factory(parameters: Iterable[nn.Parameter]) -> torch.optim.Optimizer:
        return torch.optim.SGD(parameters, lr=0.01, momentum=0.9)

    result = evaluate_eq_s0(
        model,
        inputs,
        targets,
        torch2pc_dir=Path("unused"),
        seed=7,
        thresholds=thresholds(),
        optimizer_factory=optimizer_factory,
    )

    assert result.inference_steps == len(model)
    assert result.gradient_passed
    assert result.parameter_step_passed
    assert result.optimizer_state_passed
    assert result.passed


def test_evaluate_eq_s0_rejects_gradient_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(controls, "_set_global_seed", lambda seed: None)

    def fake_backward(
        model: nn.Module,
        inputs: torch.Tensor,
        targets: torch.Tensor,
        *,
        method: str,
        torch2pc_dir: str | Path,
        eta: float | None,
        inference_steps: int | None,
    ) -> None:
        del targets, torch2pc_dir, eta, inference_steps
        scale = 2.0 if method == "fixedpred" else 1.0
        (model(inputs).sum() * scale).backward()

    monkeypatch.setattr(controls, "_run_backward", fake_backward)
    model = nn.Sequential(nn.Linear(2, 2))

    result = evaluate_eq_s0(
        model,
        torch.tensor([[1.0, 2.0]]),
        torch.tensor([0]),
        torch2pc_dir=Path("unused"),
        seed=1,
        thresholds=thresholds(),
        optimizer_factory=lambda parameters: torch.optim.SGD(parameters, lr=0.01),
    )

    assert not result.gradient_passed
    assert not result.passed


def test_gpu_execution_lane_rejects_host_execution() -> None:
    with pytest.raises(RuntimeError, match="controlled Docker/ROCm lane"):
        validate_execution_lane(
            device="gpu",
            controlled_container=False,
            lane=None,
            source_git_commit=None,
            hip_version="7.2.1",
            cuda_available=True,
            torch_version="2.9.1",
        )


def test_gpu_execution_lane_accepts_controlled_rocm() -> None:
    commit = "a" * 40
    result = validate_execution_lane(
        device="gpu",
        controlled_container=True,
        lane="rocm",
        source_git_commit=commit,
        hip_version="7.2.1",
        cuda_available=True,
        torch_version="2.9.1",
    )

    assert result["controlled_container"] is True
    assert result["lane"] == "rocm"
    assert result["source_git_commit"] == commit
    assert result["torch_hip_version"] == "7.2.1"


def test_controlled_execution_requires_full_source_commit() -> None:
    with pytest.raises(RuntimeError, match="full SOURCE_GIT_COMMIT"):
        validate_execution_lane(
            device="cpu",
            controlled_container=True,
            lane="cpu",
            source_git_commit="short",
            hip_version=None,
            cuda_available=False,
            torch_version="2.9.1",
        )
