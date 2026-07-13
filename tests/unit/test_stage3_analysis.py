from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from torch2pc_thesis.stage3_analysis import (
    build_stage3a_tables,
    generate_stage3a_tables,
    sha256_file,
)


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
    return pd.DataFrame(rows)


def representation_fixture() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for seed in (0, 1):
        for method, value in (("exact", 1.0), ("fixedpred", 0.95), ("strict", 0.85)):
            rows.append(
                {
                    "dataset": "FashionMNIST",
                    "model": "lenet_classic",
                    "model_seed": seed,
                    "reference_label": "bp",
                    "candidate_label": method,
                    "layer": 0,
                    "cka": value,
                    "rsa_spearman": value,
                    "rsa_defined": True,
                }
            )
    return pd.DataFrame(rows)


def test_build_stage3a_tables_generates_registered_outputs() -> None:
    tables = build_stage3a_tables(
        gradient_fixture(),
        representation_fixture(),
        expected_seeds=(0, 1),
    )
    assert set(tables) == {
        "seed_level_gradient_metrics.csv",
        "seed_level_representation_metrics.csv",
        "gradient_statistics.csv",
        "representation_statistics.csv",
        "exact_numerical_control.csv",
    }
    assert tables["seed_level_gradient_metrics.csv"].shape[0] == 24
    assert tables["seed_level_representation_metrics.csv"].shape[0] == 12
    gradient_statistics = tables["gradient_statistics.csv"]
    representation_statistics = tables["representation_statistics.csv"]
    assert gradient_statistics.shape[0] == 8
    assert representation_statistics.shape[0] == 4
    assert {
        "n_missing",
        "candidate_std",
        "candidate_min",
        "candidate_max",
    }.issubset(gradient_statistics.columns)
    assert gradient_statistics["n_missing"].eq(0).all()
    control = tables["exact_numerical_control.csv"]
    assert control.shape[0] == 6
    assert control["passed"].all()


def test_build_stage3a_tables_rejects_missing_seed() -> None:
    representation = representation_fixture()
    representation = representation.loc[
        ~(
            (representation["model_seed"] == 1)
            & (representation["candidate_label"] == "strict")
        )
    ]
    with pytest.raises(ValueError, match="frozen plan"):
        build_stage3a_tables(
            gradient_fixture(),
            representation,
            expected_seeds=(0, 1),
        )


def test_generate_stage3a_tables_is_deterministic(tmp_path: Path) -> None:
    summary_dir = tmp_path / "summaries"
    output_one = tmp_path / "one"
    output_two = tmp_path / "two"
    summary_dir.mkdir()
    gradient_fixture().to_csv(summary_dir / "all_gradient_metrics.csv", index=False)
    representation_fixture().to_csv(
        summary_dir / "all_representation_metrics.csv",
        index=False,
    )

    keyword_arguments = {
        "repo_root": tmp_path,
        "expected_seeds": (0, 1),
        "source_commit": "0123456789abcdef",
        "generated_at_utc": "2026-07-13T21:00:00Z",
    }
    first_counts = generate_stage3a_tables(
        summary_dir,
        output_one,
        **keyword_arguments,
    )
    second_counts = generate_stage3a_tables(
        summary_dir,
        output_two,
        **keyword_arguments,
    )

    assert first_counts == second_counts
    for path in sorted(output_one.iterdir()):
        counterpart = output_two / path.name
        assert counterpart.read_bytes() == path.read_bytes()

    metadata = json.loads((output_one / "analysis_metadata.json").read_text())
    assert metadata["source_commit"] == "0123456789abcdef"
    assert metadata["settings"]["expected_seeds"] == [0, 1]
    assert metadata["inputs"]["all_gradient_metrics.csv"]["sha256"] == sha256_file(
        summary_dir / "all_gradient_metrics.csv"
    )
