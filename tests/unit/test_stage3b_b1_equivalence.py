from __future__ import annotations

import math

import torch

from torch2pc_thesis.stage3b_b1_equivalence import (
    THRESHOLD_PROFILES,
    compare_optional_tensors,
    compare_tensors,
    flatten_trajectory,
)
from torch2pc_thesis.stage3b_b1_isolated_vjp import B1SweepSnapshot


def test_threshold_profiles_match_preregistration() -> None:
    cpu = THRESHOLD_PROFILES["cpu_float64"]
    rocm = THRESHOLD_PROFILES["rocm_float32"]
    assert (cpu.min_cosine, cpu.max_relative_l2, cpu.max_abs, cpu.zero_atol) == (
        0.99999,
        1.0e-7,
        1.0e-9,
        1.0e-12,
    )
    assert (rocm.min_cosine, rocm.max_relative_l2, rocm.max_abs, rocm.zero_atol) == (
        0.999,
        1.0e-3,
        1.0e-5,
        1.0e-7,
    )


def test_zero_safe_metric_passes_two_zero_tensors() -> None:
    profile = THRESHOLD_PROFILES["cpu_float64"]
    metric = compare_tensors(
        "zero",
        torch.zeros(4, dtype=torch.float64),
        torch.zeros(4, dtype=torch.float64),
        profile,
    )
    assert metric.passed
    assert metric.cosine is None
    assert metric.zero_case == "both_zero"


def test_zero_safe_metric_rejects_one_active_tensor() -> None:
    profile = THRESHOLD_PROFILES["cpu_float64"]
    metric = compare_tensors(
        "one-active",
        torch.zeros(4, dtype=torch.float64),
        torch.tensor([1.0, 0.0, 0.0, 0.0], dtype=torch.float64),
        profile,
    )
    assert not metric.passed
    assert metric.zero_case == "one_zero"


def test_metric_rejects_non_finite_values() -> None:
    profile = THRESHOLD_PROFILES["cpu_float64"]
    metric = compare_tensors(
        "non-finite",
        torch.tensor([math.nan], dtype=torch.float64),
        torch.tensor([math.nan], dtype=torch.float64),
        profile,
    )
    assert not metric.passed
    assert not metric.finite


def test_optional_metric_requires_presence_match() -> None:
    profile = THRESHOLD_PROFILES["cpu_float64"]
    assert compare_optional_tensors("missing", None, None, profile).passed
    assert not compare_optional_tensors(
        "mismatch",
        None,
        torch.zeros(1),
        profile,
    ).passed


def test_flatten_trajectory_preserves_layer_sweep_and_component_names() -> None:
    snapshot = B1SweepSnapshot(
        method="FixedPred",
        phase="after_sweep",
        sweep_index=2,
        beliefs=(torch.ones(1), None),
        prediction_errors=(None, torch.ones(1)),
        state_corrections=(torch.zeros(1), None),
    )
    flattened = flatten_trajectory([snapshot])
    assert set(flattened) == {
        "trajectory/after_sweep/sweep_2/beliefs/layer_0",
        "trajectory/after_sweep/sweep_2/beliefs/layer_1",
        "trajectory/after_sweep/sweep_2/prediction_errors/layer_0",
        "trajectory/after_sweep/sweep_2/prediction_errors/layer_1",
        "trajectory/after_sweep/sweep_2/state_corrections/layer_0",
        "trajectory/after_sweep/sweep_2/state_corrections/layer_1",
    }
