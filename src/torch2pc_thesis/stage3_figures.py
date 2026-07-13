"""Publication figures for Stage 3A layer-wise confirmatory analysis."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Final, cast

import matplotlib

matplotlib.use("Agg", force=True)

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from numpy.typing import NDArray

from torch2pc_thesis.stage3_statistics import (
    GRADIENT_CONTROL_TARGETS,
    GRADIENT_METRICS,
    REPRESENTATION_CONTROL_TARGETS,
    REPRESENTATION_METRICS,
    mean_confidence_interval,
)

EXPECTED_SEEDS: Final[tuple[int, ...]] = tuple(range(10))
CANDIDATE_METHODS: Final[tuple[str, ...]] = ("fixedpred", "strict")
DEFAULT_CONFIDENCE: Final[float] = 0.95

GRADIENT_INPUT: Final[str] = "seed_level_gradient_metrics.csv"
REPRESENTATION_INPUT: Final[str] = "seed_level_representation_metrics.csv"
CROSS_LAYER_INPUT: Final[str] = "all_cross_layer_cka.csv"
METADATA_FILENAME: Final[str] = "figure_metadata.json"

GRADIENT_FIGURES: Final[Mapping[str, tuple[str, str]]] = {
    "cosine": ("gradient_cosine_by_depth.pdf", "Gradient cosine similarity"),
    "relative_l2": ("gradient_relative_l2_by_depth.pdf", "Gradient relative L2"),
    "norm_ratio": ("gradient_norm_ratio_by_depth.pdf", "Gradient norm ratio"),
    "sign_agreement": ("gradient_sign_agreement_by_depth.pdf", "Gradient sign agreement"),
}
REPRESENTATION_FIGURES: Final[Mapping[str, tuple[str, str]]] = {
    "cka": ("representation_cka_by_depth.pdf", "Corresponding-layer linear CKA"),
    "rsa_spearman": (
        "representation_rsa_by_depth.pdf",
        "Corresponding-layer RSA (Spearman)",
    ),
}
CROSS_LAYER_FIGURES: Final[Mapping[str, str]] = {
    "fixedpred": "cross_layer_cka_fixedpred.pdf",
    "strict": "cross_layer_cka_strict.pdf",
}
FIGURE_FILENAMES: Final[tuple[str, ...]] = (
    *(filename for filename, _ in GRADIENT_FIGURES.values()),
    *(filename for filename, _ in REPRESENTATION_FIGURES.values()),
    *CROSS_LAYER_FIGURES.values(),
)

_METHOD_LABELS: Final[Mapping[str, str]] = {
    "fixedpred": "FixedPred",
    "strict": "Strict",
}
_METHOD_LINESTYLES: Final[Mapping[str, str]] = {
    "fixedpred": "-",
    "strict": "--",
}
_METHOD_MARKERS: Final[Mapping[str, str]] = {
    "fixedpred": "o",
    "strict": "s",
}


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of a file."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_columns(frame: pd.DataFrame, required: set[str]) -> None:
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"missing required columns: {', '.join(missing)}")


def normalized_layer_positions(layers: Sequence[int]) -> dict[int, float]:
    """Map ordered layer identifiers to ordinal depth in the interval [0, 1]."""

    ordered = sorted({int(layer) for layer in layers})
    if len(ordered) < 2:
        raise ValueError("figure generation requires at least two distinct layers")
    denominator = float(len(ordered) - 1)
    return {layer: index / denominator for index, layer in enumerate(ordered)}


def _finite_values(values: pd.Series) -> NDArray[np.float64]:
    numeric = pd.to_numeric(values, errors="coerce").to_numpy(dtype=np.float64)
    finite = numeric[np.isfinite(numeric)]
    return cast(NDArray[np.float64], finite)


def _validate_seed_level(
    frame: pd.DataFrame,
    *,
    metrics: Sequence[str],
    expected_seeds: Sequence[int],
) -> None:
    required = {"model_seed", "method", "layer", "metric", "value"}
    _require_columns(frame, required)

    expected_seed_tuple = tuple(sorted(int(seed) for seed in expected_seeds))
    actual_metrics = set(str(metric) for metric in frame["metric"].unique())
    missing_metrics = sorted(set(metrics) - actual_metrics)
    if missing_metrics:
        raise ValueError(f"seed-level table is missing metrics: {', '.join(missing_metrics)}")

    for method in CANDIDATE_METHODS:
        for metric in metrics:
            group = frame.loc[
                (frame["method"] == method) & (frame["metric"] == metric)
            ]
            if group.empty:
                raise ValueError(f"missing figure data for method={method}, metric={metric}")
            seeds = tuple(sorted(int(seed) for seed in group["model_seed"].unique()))
            if seeds != expected_seed_tuple:
                raise ValueError(
                    "figure seeds differ from the frozen plan: "
                    f"method={method}, metric={metric}, "
                    f"expected={expected_seed_tuple}, actual={seeds}"
                )
            if bool(group["value"].isna().any()):
                raise ValueError(
                    f"figure data contains missing values: method={method}, metric={metric}"
                )


def _metric_summary(
    frame: pd.DataFrame,
    *,
    method: str,
    metric: str,
    confidence: float,
) -> tuple[list[int], NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    subset = frame.loc[(frame["method"] == method) & (frame["metric"] == metric)].copy()
    layers = sorted(int(layer) for layer in subset["layer"].unique())
    means: list[float] = []
    lows: list[float] = []
    highs: list[float] = []
    for layer in layers:
        values = _finite_values(subset.loc[subset["layer"] == layer, "value"])
        if values.size == 0:
            raise ValueError(f"no finite values for method={method}, metric={metric}, layer={layer}")
        low, high = mean_confidence_interval(values, confidence=confidence)
        means.append(float(np.mean(values)))
        lows.append(low)
        highs.append(high)
    return (
        layers,
        np.asarray(means, dtype=np.float64),
        np.asarray(lows, dtype=np.float64),
        np.asarray(highs, dtype=np.float64),
    )


def _plot_seed_trajectories(
    ax: Axes,
    frame: pd.DataFrame,
    *,
    method: str,
    metric: str,
    depth_by_layer: Mapping[int, float],
) -> None:
    subset = frame.loc[(frame["method"] == method) & (frame["metric"] == metric)]
    for _, seed_rows in subset.groupby("model_seed", sort=True):
        ordered = seed_rows.sort_values("layer", kind="stable")
        x = np.asarray(
            [depth_by_layer[int(layer)] for layer in ordered["layer"]],
            dtype=np.float64,
        )
        y = pd.to_numeric(ordered["value"], errors="coerce").to_numpy(dtype=np.float64)
        ax.plot(
            x,
            y,
            color="0.70",
            alpha=0.22,
            linewidth=0.65,
            linestyle=_METHOD_LINESTYLES[method],
            label="_nolegend_",
        )


def _plot_metric_by_depth(
    frame: pd.DataFrame,
    *,
    metric: str,
    title: str,
    target: float,
    confidence: float,
) -> Figure:
    metric_rows = frame.loc[frame["metric"] == metric]
    layers = sorted(int(layer) for layer in metric_rows["layer"].unique())
    depth_by_layer = normalized_layer_positions(layers)
    depth = np.asarray([depth_by_layer[layer] for layer in layers], dtype=np.float64)

    figure, ax = plt.subplots(figsize=(6.4, 4.2), constrained_layout=True)
    for method in CANDIDATE_METHODS:
        _plot_seed_trajectories(
            ax,
            frame,
            method=method,
            metric=metric,
            depth_by_layer=depth_by_layer,
        )
        method_layers, means, lows, highs = _metric_summary(
            frame,
            method=method,
            metric=metric,
            confidence=confidence,
        )
        if method_layers != layers:
            raise ValueError(f"layer coverage differs between candidate methods for metric={metric}")
        line = ax.plot(
            depth,
            means,
            marker=_METHOD_MARKERS[method],
            linewidth=2.0,
            markersize=4.5,
            linestyle=_METHOD_LINESTYLES[method],
            label=_METHOD_LABELS[method],
        )[0]
        ax.fill_between(depth, lows, highs, color=line.get_color(), alpha=0.16)

    ax.axhline(target, color="0.20", linestyle=":", linewidth=1.2, label="BP target")
    ax.set_title(title)
    ax.set_xlabel("Layer (ordinal depth from input to output)")
    ax.set_ylabel(title)
    ax.set_xticks(depth, [str(layer) for layer in layers])
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False)
    return cast(Figure, figure)


def _resolve_column(frame: pd.DataFrame, candidates: Sequence[str], *, role: str) -> str:
    for candidate in candidates:
        if candidate in frame.columns:
            return candidate
    raise ValueError(f"cross-layer CKA table has no {role} column; tried {list(candidates)}")


def cross_layer_mean_matrix(frame: pd.DataFrame, *, method: str) -> pd.DataFrame:
    """Return the seed-mean cross-layer CKA matrix for one candidate method."""

    method_column = _resolve_column(
        frame,
        ("candidate_label", "candidate_method", "method"),
        role="candidate method",
    )
    reference_layer = _resolve_column(
        frame,
        ("reference_layer", "bp_layer", "layer_reference", "layer_a"),
        role="reference layer",
    )
    candidate_layer = _resolve_column(
        frame,
        ("candidate_layer", "method_layer", "layer_candidate", "layer_b"),
        role="candidate layer",
    )
    cka_column = _resolve_column(frame, ("cka", "linear_cka"), role="CKA value")

    subset = frame.loc[frame[method_column] == method].copy()
    if "reference_label" in subset.columns:
        subset = subset.loc[subset["reference_label"] == "bp"]
    if subset.empty:
        raise ValueError(f"cross-layer CKA table contains no rows for method={method}")

    subset[reference_layer] = pd.to_numeric(subset[reference_layer], errors="raise").astype(int)
    subset[candidate_layer] = pd.to_numeric(subset[candidate_layer], errors="raise").astype(int)
    subset[cka_column] = pd.to_numeric(subset[cka_column], errors="coerce")
    if bool(subset[cka_column].isna().any()):
        raise ValueError(f"cross-layer CKA contains undefined values for method={method}")

    matrix = subset.pivot_table(
        index=reference_layer,
        columns=candidate_layer,
        values=cka_column,
        aggfunc="mean",
        sort=True,
    )
    matrix = matrix.sort_index(axis=0).sort_index(axis=1)
    if matrix.empty or matrix.shape[0] != matrix.shape[1]:
        raise ValueError(f"cross-layer CKA matrix must be non-empty and square for method={method}")
    if bool(matrix.isna().any().any()):
        raise ValueError(f"cross-layer CKA matrix is incomplete for method={method}")
    return matrix


def _plot_cross_layer_heatmap(matrix: pd.DataFrame, *, method: str) -> Figure:
    values = matrix.to_numpy(dtype=np.float64)
    figure, ax = plt.subplots(figsize=(5.2, 4.6), constrained_layout=True)
    image = ax.imshow(values, vmin=0.0, vmax=1.0, aspect="equal", cmap="viridis")
    for row in range(values.shape[0]):
        for column in range(values.shape[1]):
            value = float(values[row, column])
            ax.text(
                column,
                row,
                f"{value:.2f}",
                ha="center",
                va="center",
                fontsize=7.5,
                color="white" if value < 0.55 else "black",
            )
    ax.set_xticks(range(len(matrix.columns)), [str(value) for value in matrix.columns])
    ax.set_yticks(range(len(matrix.index)), [str(value) for value in matrix.index])
    ax.set_xlabel(f"{_METHOD_LABELS[method]} layer")
    ax.set_ylabel("BP reference layer")
    ax.set_title(f"Cross-layer linear CKA: {_METHOD_LABELS[method]} vs BP")
    figure.colorbar(image, ax=ax, label="Mean linear CKA across seeds")
    return cast(Figure, figure)


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


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _save_pdf(figure: Figure, path: Path, *, generated_at_utc: str, title: str) -> None:
    generated_at = _parse_utc(generated_at_utc)
    metadata = {
        "Title": title,
        "Author": "Torch2PC Layer-wise Thesis",
        "Subject": "Stage 3A layer-wise confirmatory analysis",
        "Creator": "torch2pc_thesis.stage3_figures",
        "Producer": f"Matplotlib {matplotlib.__version__}",
        "CreationDate": generated_at,
        "ModDate": generated_at,
    }
    figure.savefig(path, format="pdf", dpi=300, metadata=metadata)
    plt.close(figure)


def generate_stage3a_figures(
    statistics_dir: Path,
    summaries_dir: Path,
    output_dir: Path,
    *,
    repo_root: Path,
    expected_seeds: Sequence[int] = EXPECTED_SEEDS,
    confidence: float = DEFAULT_CONFIDENCE,
    source_commit: str | None = None,
    generated_at_utc: str | None = None,
) -> dict[str, int]:
    """Generate deterministic Stage 3A publication figures and metadata."""

    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be between 0 and 1")

    gradient_path = statistics_dir / GRADIENT_INPUT
    representation_path = statistics_dir / REPRESENTATION_INPUT
    cross_layer_path = summaries_dir / CROSS_LAYER_INPUT
    input_paths = (gradient_path, representation_path, cross_layer_path)
    for path in input_paths:
        if not path.is_file():
            raise FileNotFoundError(path)

    gradient = pd.read_csv(gradient_path)
    representation = pd.read_csv(representation_path)
    cross_layer = pd.read_csv(cross_layer_path)
    _validate_seed_level(
        gradient,
        metrics=GRADIENT_METRICS,
        expected_seeds=expected_seeds,
    )
    _validate_seed_level(
        representation,
        metrics=REPRESENTATION_METRICS,
        expected_seeds=expected_seeds,
    )

    resolved_commit = source_commit or _resolve_source_commit(repo_root)
    resolved_time = _resolve_generated_at(generated_at_utc)
    output_dir.mkdir(parents=True, exist_ok=True)

    with matplotlib.rc_context(
        {
            "font.family": "DejaVu Sans",
            "pdf.compression": 9,
            "savefig.transparent": False,
        }
    ):
        for metric, (filename, title) in GRADIENT_FIGURES.items():
            figure = _plot_metric_by_depth(
                gradient,
                metric=metric,
                title=title,
                target=float(GRADIENT_CONTROL_TARGETS[metric]),
                confidence=confidence,
            )
            _save_pdf(
                figure,
                output_dir / filename,
                generated_at_utc=resolved_time,
                title=title,
            )

        for metric, (filename, title) in REPRESENTATION_FIGURES.items():
            figure = _plot_metric_by_depth(
                representation,
                metric=metric,
                title=title,
                target=float(REPRESENTATION_CONTROL_TARGETS[metric]),
                confidence=confidence,
            )
            _save_pdf(
                figure,
                output_dir / filename,
                generated_at_utc=resolved_time,
                title=title,
            )

        for method, filename in CROSS_LAYER_FIGURES.items():
            matrix = cross_layer_mean_matrix(cross_layer, method=method)
            title = f"Cross-layer linear CKA: {_METHOD_LABELS[method]} vs BP"
            figure = _plot_cross_layer_heatmap(matrix, method=method)
            _save_pdf(
                figure,
                output_dir / filename,
                generated_at_utc=resolved_time,
                title=title,
            )

    outputs = {
        filename: {
            "sha256": sha256_file(output_dir / filename),
            "size_bytes": int((output_dir / filename).stat().st_size),
        }
        for filename in FIGURE_FILENAMES
    }
    metadata: dict[str, object] = {
        "schema_version": 1,
        "analysis": "stage3a-layerwise-publication-figures",
        "generated_at_utc": resolved_time,
        "source_commit": resolved_commit,
        "inputs": {
            GRADIENT_INPUT: {
                "rows": int(len(gradient)),
                "sha256": sha256_file(gradient_path),
            },
            REPRESENTATION_INPUT: {
                "rows": int(len(representation)),
                "sha256": sha256_file(representation_path),
            },
            CROSS_LAYER_INPUT: {
                "rows": int(len(cross_layer)),
                "sha256": sha256_file(cross_layer_path),
            },
        },
        "outputs": outputs,
        "settings": {
            "independent_unit": "model_seed",
            "expected_seeds": [int(seed) for seed in expected_seeds],
            "candidate_methods": list(CANDIDATE_METHODS),
            "confidence": confidence,
            "central_summary": "mean across model seeds",
            "uncertainty_band": "two-sided Student-t confidence interval across seeds",
            "seed_trajectories": True,
            "depth_mapping": "ordinal layer rank mapped to [0, 1]",
            "bp_targets": {
                **{key: float(value) for key, value in GRADIENT_CONTROL_TARGETS.items()},
                **{key: float(value) for key, value in REPRESENTATION_CONTROL_TARGETS.items()},
            },
            "cross_layer_aggregation": "arithmetic mean across model seeds",
            "format": "PDF",
            "dpi": 300,
        },
        "software": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
            "matplotlib": matplotlib.__version__,
        },
    }
    (output_dir / METADATA_FILENAME).write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    counts = {filename: 1 for filename in FIGURE_FILENAMES}
    counts[METADATA_FILENAME] = 1
    return counts
