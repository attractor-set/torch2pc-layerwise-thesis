from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd
import pytest

from torch2pc_thesis.stage3_depth_analysis import (
    build_depth_seed_level,
    build_stage3a_depth_tables,
    depth_statistics,
    generate_stage3a_depth_tables,
    sha256_file,
)

LAYERS = (0, 1, 3, 4, 5)
GRADIENT_METRICS = ("cosine", "relative_l2", "norm_ratio", "sign_agreement")
REPRESENTATION_METRICS = ("cka", "rsa_spearman")


def seed_level_fixture(*, domain: str) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    metrics = GRADIENT_METRICS if domain == "gradient" else REPRESENTATION_METRICS
    for seed in (0, 1):
        for method in ("exact", "fixedpred", "strict"):
            for metric_index, metric in enumerate(metrics):
                for position, layer in enumerate(LAYERS):
                    depth = position / (len(LAYERS) - 1)
                    target = 0.0 if metric == "relative_l2" else 1.0
                    if method == "exact":
                        value = target
                    elif method == "fixedpred":
                        value = depth + seed * 0.01 + metric_index * 0.001
                    else:
                        value = 1.0 - depth - seed * 0.01 - metric_index * 0.001
                    row: dict[str, object] = {
                        "dataset": "FashionMNIST",
                        "model": "lenet_classic",
                        "model_seed": seed,
                        "method": method,
                        "layer": layer,
                        "metric": metric,
                        "value": value,
                        "n_observations": 1,
                        "n_missing": 0,
                    }
                    if domain == "gradient":
                        row["checkpoint_label"] = "final"
                    rows.append(row)
    return pd.DataFrame(rows)


def test_build_depth_seed_level_uses_ordinal_layer_order() -> None:
    result = build_depth_seed_level(seed_level_fixture(domain="gradient"), domain="gradient")
    fixed = result.loc[
        (result["model_seed"] == 0)
        & (result["method"] == "fixedpred")
        & (result["metric"] == "cosine")
    ].iloc[0]
    strict = result.loc[
        (result["model_seed"] == 0)
        & (result["method"] == "strict")
        & (result["metric"] == "cosine")
    ].iloc[0]
    exact = result.loc[
        (result["model_seed"] == 0)
        & (result["method"] == "exact")
        & (result["metric"] == "cosine")
    ].iloc[0]

    assert fixed["spearman_rho"] == pytest.approx(1.0)
    assert fixed["linear_slope"] == pytest.approx(1.0)
    assert strict["spearman_rho"] == pytest.approx(-1.0)
    assert strict["linear_slope"] == pytest.approx(-1.0)
    assert math.isnan(float(exact["spearman_rho"]))
    assert exact["linear_slope"] == pytest.approx(0.0)
    assert fixed["n_valid_layers"] == 5
    assert fixed["depth_min"] == pytest.approx(0.0)
    assert fixed["depth_max"] == pytest.approx(1.0)


def test_build_depth_seed_level_rejects_duplicate_layers() -> None:
    frame = seed_level_fixture(domain="gradient")
    duplicated = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="duplicate"):
        build_depth_seed_level(duplicated, domain="gradient")


def test_depth_statistics_use_seed_coefficients_and_holm_families() -> None:
    gradient = build_depth_seed_level(
        seed_level_fixture(domain="gradient"),
        domain="gradient",
    )
    result = depth_statistics(gradient)

    assert result.shape[0] == 16
    assert set(result["method"]) == {"fixedpred", "strict"}
    assert set(result["statistic"]) == {"spearman_rho", "linear_slope"}
    assert result["n"].eq(2).all()
    inferential = result.loc[result["statistic"] == "spearman_rho"]
    descriptive = result.loc[result["statistic"] == "linear_slope"]
    assert inferential["p_value_holm"].between(0.0, 1.0).all()
    assert descriptive["p_value"].isna().all()
    assert descriptive["p_value_holm"].isna().all()
    assert set(inferential["analysis_role"]) == {"confirmatory"}
    assert set(descriptive["analysis_role"]) == {"descriptive"}
    fixed_slope = result.loc[
        (result["method"] == "fixedpred")
        & (result["metric"] == "cosine")
        & (result["statistic"] == "linear_slope")
    ].iloc[0]
    assert fixed_slope["reference"] == "zero_depth_trend"
    assert fixed_slope["candidate_mean"] == pytest.approx(1.0)


def test_build_stage3a_depth_tables_validates_exact_control() -> None:
    tables, exact_control = build_stage3a_depth_tables(
        seed_level_fixture(domain="gradient"),
        seed_level_fixture(domain="representation"),
        expected_seeds=(0, 1),
    )

    assert tables["depth_seed_level.csv"].shape[0] == 36
    assert tables["depth_statistics.csv"].shape[0] == 24
    assert exact_control["rows"] == 12
    assert exact_control["max_abs_slope"] == pytest.approx(0.0)


def test_generate_stage3a_depth_tables_is_deterministic(tmp_path: Path) -> None:
    statistics_dir = tmp_path / "statistics"
    output_one = tmp_path / "one"
    output_two = tmp_path / "two"
    statistics_dir.mkdir()
    seed_level_fixture(domain="gradient").to_csv(
        statistics_dir / "seed_level_gradient_metrics.csv",
        index=False,
    )
    seed_level_fixture(domain="representation").to_csv(
        statistics_dir / "seed_level_representation_metrics.csv",
        index=False,
    )
    keyword_arguments = {
        "repo_root": tmp_path,
        "expected_seeds": (0, 1),
        "source_commit": "0123456789abcdef",
        "generated_at_utc": "2026-07-13T22:00:00Z",
    }

    first_counts = generate_stage3a_depth_tables(
        statistics_dir,
        output_one,
        **keyword_arguments,
    )
    second_counts = generate_stage3a_depth_tables(
        statistics_dir,
        output_two,
        **keyword_arguments,
    )

    assert first_counts == second_counts
    for path in sorted(output_one.iterdir()):
        counterpart = output_two / path.name
        assert counterpart.read_bytes() == path.read_bytes()

    metadata = json.loads((output_one / "depth_analysis_metadata.json").read_text())
    assert metadata["source_commit"] == "0123456789abcdef"
    assert metadata["settings"]["expected_seeds"] == [0, 1]
    assert metadata["outputs"]["depth_seed_level.csv"]["sha256"] == sha256_file(
        output_one / "depth_seed_level.csv"
    )
