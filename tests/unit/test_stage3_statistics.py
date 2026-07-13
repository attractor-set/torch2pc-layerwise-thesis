from __future__ import annotations

import math

import pandas as pd
import pytest

from torch2pc_thesis.stage3_statistics import (
    GRADIENT_CONTROL_TARGETS,
    aggregate_gradient_seed_level,
    aggregate_representation_seed_level,
    comparison_statistics,
    exact_numerical_control,
    exact_sign_flip_test,
    holm_adjust,
    mean_confidence_interval,
    paired_differences,
    paired_effect_size_dz,
    rank_biserial_correlation,
)


def test_paired_differences_drop_missing_pairs() -> None:
    differences = paired_differences([1.0, 2.0, math.nan], [1.5, math.nan, 3.0])
    assert differences.tolist() == [0.5]


def test_exact_sign_flip_enumerates_all_sign_assignments() -> None:
    assert exact_sign_flip_test([1.0, 1.0, 1.0]) == pytest.approx(0.25)
    assert exact_sign_flip_test([-1.0, 1.0]) == pytest.approx(1.0)


def test_effect_sizes_handle_zero_variance() -> None:
    assert paired_effect_size_dz([0.0, 0.0, 0.0]) == 0.0
    assert math.isinf(paired_effect_size_dz([1.0, 1.0, 1.0]))
    assert rank_biserial_correlation([1.0, 2.0, 3.0]) == pytest.approx(1.0)
    assert rank_biserial_correlation([0.0, 0.0]) == 0.0


def test_mean_confidence_interval_is_degenerate_for_constant_values() -> None:
    assert mean_confidence_interval([2.0, 2.0, 2.0]) == (2.0, 2.0)


def test_holm_adjust_preserves_order_and_monotonicity() -> None:
    adjusted = holm_adjust([0.04, 0.01, 0.03])
    assert adjusted == pytest.approx([0.06, 0.03, 0.06])
    assert all(0.0 <= value <= 1.0 for value in adjusted)


def gradient_fixture() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for seed in (0, 1):
        for method, cosine in (("exact", 1.0), ("fixedpred", 0.9), ("strict", 0.8)):
            for batch_id in (0, 1):
                rows.append(
                    {
                        "dataset": "FashionMNIST",
                        "model": "lenet_classic",
                        "model_seed": seed,
                        "checkpoint_label": "final",
                        "batch_id": batch_id,
                        "method": method,
                        "scope": "top_level",
                        "unit": "0",
                        "cosine": cosine,
                        "cosine_defined": True,
                        "relative_l2": 1.0 - cosine,
                        "norm_ratio": cosine,
                        "sign_agreement": cosine,
                    }
                )
                rows.append({**rows[-1], "scope": "parameter", "unit": "0.0.weight"})
    return pd.DataFrame(rows)


def test_gradient_aggregation_uses_only_top_level_batches() -> None:
    result = aggregate_gradient_seed_level(gradient_fixture())
    assert len(result) == 2 * 3 * 1 * 4
    selected = result.loc[
        (result["model_seed"] == 0)
        & (result["method"] == "fixedpred")
        & (result["metric"] == "cosine")
    ].iloc[0]
    assert selected["value"] == pytest.approx(0.9)
    assert selected["n_observations"] == 2
    assert selected["n_missing"] == 0


def test_gradient_aggregation_is_order_independent() -> None:
    frame = gradient_fixture()
    first = aggregate_gradient_seed_level(frame)
    second = aggregate_gradient_seed_level(frame.sample(frac=1.0, random_state=7))
    pd.testing.assert_frame_equal(first, second)


def test_representation_aggregation_preserves_missing_rsa() -> None:
    frame = pd.DataFrame(
        [
            {
                "dataset": "FashionMNIST",
                "model": "lenet_classic",
                "model_seed": 0,
                "reference_label": "bp",
                "candidate_label": "fixedpred",
                "layer": 0,
                "cka": 0.95,
                "rsa_spearman": 0.0,
                "rsa_defined": False,
            }
        ]
    )
    result = aggregate_representation_seed_level(frame)
    rsa = result.loc[result["metric"] == "rsa_spearman"].iloc[0]
    assert math.isnan(float(rsa["value"]))
    assert rsa["n_observations"] == 0
    assert rsa["n_missing"] == 1


def test_comparison_statistics_pair_by_seed_and_apply_holm() -> None:
    seed_level = aggregate_gradient_seed_level(gradient_fixture())
    result = comparison_statistics(seed_level, targets=GRADIENT_CONTROL_TARGETS)
    assert set(result["method"]) == {"fixedpred", "strict"}
    assert set(result["n"]) == {2}
    assert result["p_value_holm"].between(0.0, 1.0).all()
    fixed_cosine = result.loc[
        (result["method"] == "fixedpred") & (result["metric"] == "cosine")
    ].iloc[0]
    assert fixed_cosine["reference"] == "bp_target"
    assert fixed_cosine["target_value"] == 1.0
    assert fixed_cosine["mean_difference"] == pytest.approx(-0.1)


def test_exact_numerical_control_uses_explicit_tolerances() -> None:
    seed_level = aggregate_gradient_seed_level(gradient_fixture())
    result = exact_numerical_control(
        seed_level,
        targets=GRADIENT_CONTROL_TARGETS,
        tolerances={metric: 1e-12 for metric in GRADIENT_CONTROL_TARGETS},
    )
    assert result["passed"].all()
    assert result["max_abs_error"].max() == pytest.approx(0.0)
