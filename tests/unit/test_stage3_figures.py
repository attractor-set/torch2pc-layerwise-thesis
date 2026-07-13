from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from torch2pc_thesis.stage3_figures import (
    FIGURE_FILENAMES,
    METADATA_FILENAME,
    cross_layer_mean_matrix,
    generate_stage3a_figures,
    normalized_layer_positions,
)

LAYERS = (0, 1, 3, 4, 5)
METHODS = ("fixedpred", "strict")
GRADIENT_METRICS = ("cosine", "relative_l2", "norm_ratio", "sign_agreement")
REPRESENTATION_METRICS = ("cka", "rsa_spearman")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_inputs(root: Path) -> tuple[Path, Path]:
    statistics_dir = root / "statistics"
    summaries_dir = root / "summaries"
    statistics_dir.mkdir(parents=True)
    summaries_dir.mkdir(parents=True)

    gradient_rows: list[dict[str, object]] = []
    representation_rows: list[dict[str, object]] = []
    cross_rows: list[dict[str, object]] = []
    for seed in range(10):
        for method_index, method in enumerate(METHODS):
            for layer_index, layer in enumerate(LAYERS):
                for metric_index, metric in enumerate(GRADIENT_METRICS):
                    gradient_rows.append(
                        {
                            "dataset": "fashion_mnist",
                            "model": "lenet_classic",
                            "checkpoint_label": "final",
                            "model_seed": seed,
                            "method": method,
                            "layer": layer,
                            "metric": metric,
                            "value": 0.25
                            + method_index * 0.1
                            + metric_index * 0.03
                            + layer_index * 0.02
                            + seed * 0.001,
                            "n_observations": 5,
                            "n_missing": 0,
                        }
                    )
                for metric_index, metric in enumerate(REPRESENTATION_METRICS):
                    representation_rows.append(
                        {
                            "dataset": "fashion_mnist",
                            "model": "lenet_classic",
                            "model_seed": seed,
                            "method": method,
                            "layer": layer,
                            "metric": metric,
                            "value": 0.55
                            + method_index * 0.08
                            + metric_index * 0.04
                            + layer_index * 0.015
                            + seed * 0.001,
                            "n_observations": 1,
                            "n_missing": 0,
                        }
                    )
            for reference_layer in LAYERS:
                for candidate_layer in LAYERS:
                    cross_rows.append(
                        {
                            "dataset": "fashion_mnist",
                            "model": "lenet_classic",
                            "model_seed": seed,
                            "reference_label": "bp",
                            "candidate_label": method,
                            "reference_layer": reference_layer,
                            "candidate_layer": candidate_layer,
                            "cka": 0.9
                            - abs(LAYERS.index(reference_layer) - LAYERS.index(candidate_layer))
                            * 0.1
                            - method_index * 0.02
                            + seed * 0.0001,
                        }
                    )

    pd.DataFrame(gradient_rows).to_csv(
        statistics_dir / "seed_level_gradient_metrics.csv", index=False
    )
    pd.DataFrame(representation_rows).to_csv(
        statistics_dir / "seed_level_representation_metrics.csv", index=False
    )
    pd.DataFrame(cross_rows).to_csv(summaries_dir / "all_cross_layer_cka.csv", index=False)
    return statistics_dir, summaries_dir


def test_normalized_layer_positions_uses_ordinal_order() -> None:
    positions = normalized_layer_positions(LAYERS)
    assert positions == {0: 0.0, 1: 0.25, 3: 0.5, 4: 0.75, 5: 1.0}


def test_cross_layer_mean_matrix_resolves_expected_schema() -> None:
    rows = [
        {
            "model_seed": seed,
            "reference_label": "bp",
            "candidate_label": "fixedpred",
            "reference_layer": reference_layer,
            "candidate_layer": candidate_layer,
            "cka": 0.8 + 0.01 * seed,
        }
        for seed in range(2)
        for reference_layer in (0, 1)
        for candidate_layer in (0, 1)
    ]
    matrix = cross_layer_mean_matrix(pd.DataFrame(rows), method="fixedpred")
    assert matrix.shape == (2, 2)
    assert matrix.loc[0, 0] == pytest.approx(0.805)


def test_generate_figures_writes_pdfs_and_metadata(tmp_path: Path) -> None:
    statistics_dir, summaries_dir = _write_inputs(tmp_path / "inputs")
    output_dir = tmp_path / "figures"
    counts = generate_stage3a_figures(
        statistics_dir,
        summaries_dir,
        output_dir,
        repo_root=tmp_path,
        source_commit="0123456789abcdef",
        generated_at_utc="2026-07-13T20:00:00Z",
    )

    assert set(counts) == {*FIGURE_FILENAMES, METADATA_FILENAME}
    for filename in FIGURE_FILENAMES:
        path = output_dir / filename
        assert path.read_bytes().startswith(b"%PDF")
        assert path.stat().st_size > 1_000

    metadata = json.loads((output_dir / METADATA_FILENAME).read_text(encoding="utf-8"))
    assert metadata["source_commit"] == "0123456789abcdef"
    assert metadata["settings"]["expected_seeds"] == list(range(10))
    assert metadata["settings"]["candidate_methods"] == list(METHODS)
    for filename in FIGURE_FILENAMES:
        assert metadata["outputs"][filename]["sha256"] == _sha256(output_dir / filename)


def test_generation_is_deterministic_for_fixed_provenance(tmp_path: Path) -> None:
    statistics_dir, summaries_dir = _write_inputs(tmp_path / "inputs")
    first = tmp_path / "first"
    second = tmp_path / "second"
    arguments = {
        "repo_root": tmp_path,
        "source_commit": "0123456789abcdef",
        "generated_at_utc": "2026-07-13T20:00:00Z",
    }
    generate_stage3a_figures(statistics_dir, summaries_dir, first, **arguments)
    generate_stage3a_figures(statistics_dir, summaries_dir, second, **arguments)

    for filename in (*FIGURE_FILENAMES, METADATA_FILENAME):
        assert _sha256(first / filename) == _sha256(second / filename)


def test_missing_metric_fails_before_plotting(tmp_path: Path) -> None:
    statistics_dir, summaries_dir = _write_inputs(tmp_path / "inputs")
    gradient_path = statistics_dir / "seed_level_gradient_metrics.csv"
    gradient = pd.read_csv(gradient_path)
    gradient.loc[gradient["metric"] != "cosine"].to_csv(gradient_path, index=False)

    with pytest.raises(ValueError, match="missing metrics: cosine"):
        generate_stage3a_figures(
            statistics_dir,
            summaries_dir,
            tmp_path / "figures",
            repo_root=tmp_path,
            source_commit="0123456789abcdef",
            generated_at_utc="2026-07-13T20:00:00Z",
        )
