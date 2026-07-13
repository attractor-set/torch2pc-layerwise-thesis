from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from torch2pc_thesis.stage3_aggregation import (
    aggregate_tables,
    enrich_with_provenance,
)


def write_representation_fixture(root: Path, seed: int) -> Path:
    directory = root / f"seed-{seed}" / "final" / "representations"
    directory.mkdir(parents=True)
    path = directory / "representation_metrics.csv"
    pd.DataFrame(
        [
            {
                "reference_label": "bp",
                "candidate_label": "fixedpred",
                "layer": "0",
                "cka": 0.9,
            }
        ]
    ).to_csv(path, index=False)
    (directory / "metadata.json").write_text(
        json.dumps(
            {
                "dataset": "FashionMNIST",
                "model": "lenet_classic",
                "model_seed": seed,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def test_enriches_representation_rows_from_metadata(tmp_path: Path) -> None:
    path = write_representation_fixture(tmp_path, seed=3)
    frame = enrich_with_provenance(pd.read_csv(path), path)

    assert frame.loc[0, "model_seed"] == 3
    assert frame.loc[0, "dataset"] == "FashionMNIST"
    assert frame.loc[0, "model"] == "lenet_classic"
    assert frame.loc[0, "source_file"] == path.as_posix()


def test_rejects_conflicting_existing_seed(tmp_path: Path) -> None:
    path = write_representation_fixture(tmp_path, seed=4)
    frame = pd.read_csv(path)
    frame.insert(0, "model_seed", 9)

    with pytest.raises(ValueError, match="conflicting 'model_seed'"):
        enrich_with_provenance(frame, path)


def test_aggregation_is_deterministic_and_excludes_output(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    output = raw / "combined"
    write_representation_fixture(raw, seed=0)
    write_representation_fixture(raw, seed=1)

    first = aggregate_tables(raw, output)
    first_bytes = (output / "all_representation_metrics.csv").read_bytes()
    second = aggregate_tables(raw, output)
    second_bytes = (output / "all_representation_metrics.csv").read_bytes()

    assert first["all_representation_metrics.csv"] == 2
    assert second["all_representation_metrics.csv"] == 2
    assert first_bytes == second_bytes
    assert b"\r\n" not in second_bytes
