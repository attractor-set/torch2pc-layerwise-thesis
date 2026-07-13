"""Aggregation helpers for Stage 3 layer-wise diagnostic artifacts."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any, Final

import pandas as pd

SEED_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(?:^|/)seed-(?P<seed>\d+)(?:/|$)"
)

TABLE_PATTERNS: Final[dict[str, str]] = {
    "all_gradient_metrics.csv": "gradient_metrics.csv",
    "all_gradient_summaries.csv": "gradient_summary.csv",
    "all_representation_metrics.csv": "representation_metrics.csv",
    "all_cross_layer_cka.csv": "cross_layer_cka.csv",
}

PROVENANCE_COLUMNS: Final[tuple[str, ...]] = (
    "dataset",
    "model",
    "model_seed",
    "checkpoint_label",
)


def _normalise_scalar(value: Any) -> Any:
    """Normalise JSON/CSV scalar values before consistency comparisons."""

    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return str(value)


def recover_seed_from_path(path: Path) -> int | None:
    """Recover ``model_seed`` from a canonical ``seed-N`` path component."""

    match = SEED_PATTERN.search(path.as_posix())
    return int(match.group("seed")) if match is not None else None


def load_sibling_metadata(path: Path) -> dict[str, Any]:
    """Load the ``metadata.json`` stored beside a raw Stage 3 CSV."""

    metadata_path = path.with_name("metadata.json")
    if not metadata_path.is_file():
        return {}

    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"metadata must be a JSON object: {metadata_path}")
    return payload


def _validate_existing_column(
    frame: pd.DataFrame,
    *,
    column: str,
    expected: Any,
    source: Path,
) -> None:
    """Reject provenance columns that conflict with sibling metadata."""

    observed = {
        _normalise_scalar(value)
        for value in frame[column].dropna().unique().tolist()
    }
    expected_value = _normalise_scalar(expected)

    if observed and observed != {expected_value}:
        raise ValueError(
            f"conflicting {column!r} values in {source}: "
            f"observed={sorted(map(str, observed))}, expected={expected_value!r}"
        )


def enrich_with_provenance(frame: pd.DataFrame, path: Path) -> pd.DataFrame:
    """Add stable source and model provenance to one raw Stage 3 table."""

    enriched = frame.copy()
    source_file = path.as_posix()

    if "source_file" in enriched.columns:
        _validate_existing_column(
            enriched,
            column="source_file",
            expected=source_file,
            source=path,
        )
    else:
        enriched.insert(0, "source_file", source_file)

    metadata = load_sibling_metadata(path)
    seed_from_path = recover_seed_from_path(path)
    if "model_seed" not in metadata and seed_from_path is not None:
        metadata["model_seed"] = seed_from_path

    insertion_index = 1
    for column in PROVENANCE_COLUMNS:
        if column not in metadata:
            continue

        expected = metadata[column]
        if column in enriched.columns:
            _validate_existing_column(
                enriched,
                column=column,
                expected=expected,
                source=path,
            )
            continue

        enriched.insert(insertion_index, column, expected)
        insertion_index += 1

    return enriched


def concatenate_tables(paths: Iterable[Path]) -> pd.DataFrame:
    """Read, enrich, and concatenate raw Stage 3 CSV tables."""

    frames = [
        enrich_with_provenance(pd.read_csv(path), path)
        for path in sorted(paths)
    ]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def discover_tables(root: Path, output: Path) -> dict[str, list[Path]]:
    """Find raw inputs while excluding the output tree itself."""

    resolved_output = output.resolve()
    discovered: dict[str, list[Path]] = {}

    for output_name, raw_name in TABLE_PATTERNS.items():
        paths: list[Path] = []
        for path in root.rglob(raw_name):
            resolved = path.resolve()
            if resolved == resolved_output or resolved_output in resolved.parents:
                continue
            paths.append(path)
        discovered[output_name] = sorted(paths)

    return discovered


def aggregate_tables(root: Path, output: Path) -> Mapping[str, int]:
    """Build all published Stage 3 aggregate CSV tables deterministically."""

    output.mkdir(parents=True, exist_ok=True)
    row_counts: dict[str, int] = {}

    for filename, paths in discover_tables(root, output).items():
        frame = concatenate_tables(paths)
        destination = output / filename
        frame.to_csv(destination, index=False, lineterminator="\n")
        row_counts[filename] = len(frame)

    return row_counts
