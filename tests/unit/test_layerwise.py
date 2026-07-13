from __future__ import annotations

import math

import numpy as np
import pytest
import torch
from torch import nn

from torch2pc_thesis.layerwise import (
    capture_activations,
    collect_gradient_vectors,
    compare_gradient_vectors,
    compare_representations,
    cross_layer_cka,
)


def test_identical_gradient_metrics() -> None:
    vector = torch.tensor([1.0, -2.0, 3.0])
    metrics = compare_gradient_vectors(vector, vector.clone())

    assert metrics.cosine == pytest.approx(1.0)
    assert metrics.relative_l2 == pytest.approx(0.0)
    assert metrics.norm_ratio == pytest.approx(1.0)
    assert metrics.sign_agreement == pytest.approx(1.0)


def test_opposite_gradient_metrics() -> None:
    vector = torch.tensor([1.0, -2.0, 3.0])
    metrics = compare_gradient_vectors(vector, -vector)

    assert metrics.cosine == pytest.approx(-1.0)
    assert metrics.relative_l2 == pytest.approx(2.0)
    assert metrics.sign_agreement == pytest.approx(0.0)


def test_zero_gradient_has_undefined_cosine() -> None:
    metrics = compare_gradient_vectors(torch.zeros(3), torch.zeros(3))

    assert not metrics.cosine_defined
    assert math.isnan(metrics.cosine)
    assert metrics.relative_l2 == pytest.approx(0.0)


def test_collect_gradient_vectors_by_top_level_module() -> None:
    model = nn.Sequential(nn.Linear(3, 4), nn.Tanh(), nn.Linear(4, 2))
    model(torch.ones(2, 3)).sum().backward()

    vectors = collect_gradient_vectors(model, scope="top_level")

    assert list(vectors) == ["0", "2"]
    assert vectors["0"].numel() == 16
    assert vectors["2"].numel() == 10


def test_capture_activations_preserves_sample_axis() -> None:
    torch.manual_seed(0)
    model = nn.Sequential(nn.Linear(3, 4), nn.Tanh(), nn.Linear(4, 2))
    inputs = [torch.randn(3, 3), torch.randn(2, 3)]

    activations = capture_activations(
        model,
        inputs,
        layer_names=["0", "2"],
        device=torch.device("cpu"),
        dtype=torch.float32,
        max_samples=4,
    )

    assert activations["0"].shape == (4, 4)
    assert activations["2"].shape == (4, 2)


def test_identical_representations_have_unit_similarity() -> None:
    rng = np.random.default_rng(0)
    values = rng.normal(size=(20, 5))

    metrics = compare_representations(values, values.copy())

    assert metrics.cka == pytest.approx(1.0)
    assert metrics.rsa_spearman == pytest.approx(1.0)
    assert metrics.rsa_defined


def test_cross_layer_cka_contains_full_matrix() -> None:
    rng = np.random.default_rng(0)
    reference = {"a": rng.normal(size=(10, 3)), "b": rng.normal(size=(10, 4))}
    candidate = {"x": rng.normal(size=(10, 2)), "y": rng.normal(size=(10, 5))}

    matrix = cross_layer_cka(reference, candidate)

    assert set(matrix) == {("a", "x"), ("a", "y"), ("b", "x"), ("b", "y")}
