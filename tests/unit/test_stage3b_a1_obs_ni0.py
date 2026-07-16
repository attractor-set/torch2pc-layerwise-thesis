from __future__ import annotations

from pathlib import Path

import torch
import torch.nn as nn

from torch2pc_thesis.stage3b_a1_controls import EquivalenceThresholds
from torch2pc_thesis.stage3b_a1_obs_ni0 import (
    ObserverArm,
    capture_rng_snapshot,
    evaluate_obs_ni0,
    restore_rng_snapshot,
    rng_snapshots_equal,
)


def test_rng_snapshot_round_trip_restores_all_available_states() -> None:
    torch.manual_seed(17)
    snapshot = capture_rng_snapshot()
    torch.rand(5)
    restore_rng_snapshot(snapshot)
    restored = capture_rng_snapshot()
    assert rng_snapshots_equal(snapshot, restored)


def test_obs_ni0_passes_for_deterministic_toy_model(
    monkeypatch,
) -> None:
    from torch2pc_thesis import pc_methods

    def fake_backward_for_method(
        model: nn.Module,
        loss_fn: nn.Module,
        inputs: torch.Tensor,
        targets: torch.Tensor,
        **_kwargs: object,
    ) -> None:
        model(inputs)
        model(inputs)
        loss_fn(model(inputs), targets).backward()

    monkeypatch.setattr(pc_methods, "backward_for_method", fake_backward_for_method)

    torch.manual_seed(5)
    model = nn.Sequential(
        nn.Linear(4, 5),
        nn.Tanh(),
        nn.Linear(5, 3),
    ).to(dtype=torch.float64)
    inputs = torch.randn(3, 4, dtype=torch.float64)
    targets = torch.tensor([0, 1, 2])

    result = evaluate_obs_ni0(
        model,
        inputs,
        targets,
        torch2pc_dir=Path("external/Torch2PC"),
        seed=11,
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

    assert result.passed is True
    assert {arm.arm for arm in result.arms} == set(ObserverArm)
    assert len(result.endpoint_records_frame()) == 16
    assert len(result.payload_records_frame()) == 12
    for arm in result.arms:
        assert arm.gradient_passed is True
        assert arm.parameter_step_passed is True
        assert arm.rng_passed is True
        assert arm.observer_validation.passed is True
        assert arm.observer_validation.expected_records == 6
        assert arm.observer_validation.observed_records == 6
        assert arm.observer_validation.balanced_forward_calls is True
        assert arm.observer_validation.input_call_counts == (
            (3, 3, 3) if arm.arm is ObserverArm.FIXEDPRED else (1, 1, 1)
        )
        assert arm.observer_validation.output_call_counts == (
            (3, 3, 3) if arm.arm is ObserverArm.FIXEDPRED else (1, 1, 1)
        )
        assert arm.inputs_passed is True
        assert arm.buffers_passed is True
