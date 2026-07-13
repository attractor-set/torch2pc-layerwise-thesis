"""Artifact generation for Stage 3A confirmatory statistical tables."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
import scipy

from torch2pc_thesis.stage3_statistics import (
    GRADIENT_CONTROL_TARGETS,
    REPRESENTATION_CONTROL_TARGETS,
    aggregate_gradient_seed_level,
    aggregate_representation_seed_level,
    comparison_statistics,
    exact_numerical_control,
)

EXPECTED_SEEDS: Final[tuple[int, ...]] = tuple(range(10))
EXPECTED_METHODS: Final[tuple[str, ...]] = ("exact", "fixedpred", "strict")
DEFAULT_CONFIDENCE: Final[float] = 0.95
DEFAULT_EXACT_TOLERANCE: Final[float] = 1e-12

GRADIENT_INPUT: Final[str] = "all_gradient_metrics.csv"
REPRESENTATION_INPUT: Final[str] = "all_representation_metrics.csv"

OUTPUT_FILENAMES: Final[tuple[str, ...]] = (
    "seed_level_gradient_metrics.csv",
    "seed_level_representation_metrics.csv",
    "gradient_statistics.csv",
    "representation_statistics.csv",
    "exact_numerical_control.csv",
)


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve_source_commit(repo_root: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _resolve_generated_at(generated_at_utc: str | None) -> str:
    if generated_at_utc is not None:
        return generated_at_utc
    source_date_epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if source_date_epoch is not None:
        timestamp = int(source_date_epoch)
        return datetime.fromtimestamp(timestamp, tz=UTC).isoformat().replace("+00:00", "Z")
    return datetime.now(tz=UTC).isoformat().replace("+00:00", "Z")


def _validate_expected_seeds(
    frame: pd.DataFrame,
    *,
    label: str,
    expected_seeds: Sequence[int],
) -> None:
    expected = tuple(sorted(int(seed) for seed in expected_seeds))
    for method in EXPECTED_METHODS:
        method_rows = frame.loc[frame["method"] == method]
        actual = tuple(sorted(int(seed) for seed in method_rows["model_seed"].unique()))
        if actual != expected:
            raise ValueError(
                f"{label} seeds for {method} differ from the frozen plan: "
                f"expected={expected}, actual={actual}"
            )


def _control_table(
    gradient_seed_level: pd.DataFrame,
    representation_seed_level: pd.DataFrame,
    *,
    exact_tolerance: float,
) -> pd.DataFrame:
    if exact_tolerance < 0.0:
        raise ValueError("exact_tolerance must be non-negative")
    gradient_tolerances = {
        metric: exact_tolerance for metric in GRADIENT_CONTROL_TARGETS
    }
    representation_tolerances = {
        metric: exact_tolerance for metric in REPRESENTATION_CONTROL_TARGETS
    }
    gradient = exact_numerical_control(
        gradient_seed_level,
        targets=GRADIENT_CONTROL_TARGETS,
        tolerances=gradient_tolerances,
    ).assign(domain="gradient")
    representation = exact_numerical_control(
        representation_seed_level,
        targets=REPRESENTATION_CONTROL_TARGETS,
        tolerances=representation_tolerances,
    ).assign(domain="representation")
    control = pd.concat([gradient, representation], ignore_index=True, sort=False)
    ordered = ["domain"] + [column for column in control.columns if column != "domain"]
    return control.loc[:, ordered].sort_values(
        ["domain", "dataset", "model", "layer", "metric"],
        ignore_index=True,
    )


def build_stage3a_tables(
    gradient_frame: pd.DataFrame,
    representation_frame: pd.DataFrame,
    *,
    expected_seeds: Sequence[int] = EXPECTED_SEEDS,
    confidence: float = DEFAULT_CONFIDENCE,
    exact_tolerance: float = DEFAULT_EXACT_TOLERANCE,
) -> dict[str, pd.DataFrame]:
    """Build all deterministic Stage 3A statistical tables in memory."""
    gradient_seed_level = aggregate_gradient_seed_level(gradient_frame)
    representation_seed_level = aggregate_representation_seed_level(representation_frame)

    _validate_expected_seeds(
        gradient_seed_level,
        label="gradient",
        expected_seeds=expected_seeds,
    )
    _validate_expected_seeds(
        representation_seed_level,
        label="representation",
        expected_seeds=expected_seeds,
    )

    gradient_statistics = comparison_statistics(
        gradient_seed_level,
        targets=GRADIENT_CONTROL_TARGETS,
        confidence=confidence,
    )
    representation_statistics = comparison_statistics(
        representation_seed_level,
        targets=REPRESENTATION_CONTROL_TARGETS,
        confidence=confidence,
    )
    exact_control = _control_table(
        gradient_seed_level,
        representation_seed_level,
        exact_tolerance=exact_tolerance,
    )

    expected_n = len(tuple(expected_seeds))
    if exact_control.empty:
        raise ValueError("Exact numerical control produced no rows")
    if not bool((exact_control["n"] == expected_n).all()):
        raise ValueError("Exact numerical control does not contain every expected seed")
    if not bool(exact_control["passed"].all()):
        failed = exact_control.loc[~exact_control["passed"].astype(bool)]
        details = failed[["domain", "layer", "metric", "max_abs_error"]].to_dict(
            orient="records"
        )
        raise ValueError(f"Exact numerical control failed: {details}")

    return {
        "seed_level_gradient_metrics.csv": gradient_seed_level,
        "seed_level_representation_metrics.csv": representation_seed_level,
        "gradient_statistics.csv": gradient_statistics,
        "representation_statistics.csv": representation_statistics,
        "exact_numerical_control.csv": exact_control,
    }


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(
        path,
        index=False,
        lineterminator="\n",
        na_rep="",
        float_format="%.17g",
    )


def generate_stage3a_tables(
    summary_dir: Path,
    output_dir: Path,
    *,
    repo_root: Path,
    expected_seeds: Sequence[int] = EXPECTED_SEEDS,
    confidence: float = DEFAULT_CONFIDENCE,
    exact_tolerance: float = DEFAULT_EXACT_TOLERANCE,
    source_commit: str | None = None,
    generated_at_utc: str | None = None,
) -> dict[str, int]:
    """Generate CSV outputs and a provenance-rich JSON metadata file."""
    gradient_path = summary_dir / GRADIENT_INPUT
    representation_path = summary_dir / REPRESENTATION_INPUT
    for path in (gradient_path, representation_path):
        if not path.is_file():
            raise FileNotFoundError(path)

    gradient_frame = pd.read_csv(gradient_path)
    representation_frame = pd.read_csv(representation_path)
    tables = build_stage3a_tables(
        gradient_frame,
        representation_frame,
        expected_seeds=expected_seeds,
        confidence=confidence,
        exact_tolerance=exact_tolerance,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    for filename in OUTPUT_FILENAMES:
        _write_csv(tables[filename], output_dir / filename)

    resolved_commit = source_commit or _resolve_source_commit(repo_root)
    resolved_time = _resolve_generated_at(generated_at_utc)
    output_metadata = {
        filename: {
            "rows": int(len(tables[filename])),
            "sha256": sha256_file(output_dir / filename),
        }
        for filename in OUTPUT_FILENAMES
    }
    metadata: dict[str, object] = {
        "schema_version": 1,
        "analysis": "stage3a-layerwise-confirmatory-statistics",
        "generated_at_utc": resolved_time,
        "source_commit": resolved_commit,
        "inputs": {
            GRADIENT_INPUT: {
                "rows": int(len(gradient_frame)),
                "sha256": sha256_file(gradient_path),
            },
            REPRESENTATION_INPUT: {
                "rows": int(len(representation_frame)),
                "sha256": sha256_file(representation_path),
            },
        },
        "outputs": output_metadata,
        "settings": {
            "independent_unit": "model_seed",
            "expected_seeds": [int(seed) for seed in expected_seeds],
            "candidate_methods": ["fixedpred", "strict"],
            "confidence": confidence,
            "exact_sign_flip": "two-sided exhaustive sign assignments of mean differences",
            "holm_families": [
                "gradient/fixedpred",
                "gradient/strict",
                "representation/fixedpred",
                "representation/strict",
            ],
            "exact_absolute_tolerance": exact_tolerance,
        },
        "software": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
        },
    }
    metadata_path = output_dir / "analysis_metadata.json"
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    counts = {filename: int(len(tables[filename])) for filename in OUTPUT_FILENAMES}
    counts[metadata_path.name] = 1
    return counts
