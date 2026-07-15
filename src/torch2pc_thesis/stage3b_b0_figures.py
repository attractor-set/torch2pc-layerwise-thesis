"""Deterministic publication figures for Stage 3B B0 engineering analysis."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Final, cast

import matplotlib

matplotlib.use("Agg", force=True)

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.figure import Figure

FIGURE_FILENAMES: Final[tuple[str, ...]] = (
    "paired_device_time_ratio_by_depth.pdf",
    "paired_peak_allocated_ratio_by_depth.pdf",
    "region_device_time_share.pdf",
    "scaling_multiplier_per_doubling.pdf",
)
METHOD_LABELS: Final[Mapping[str, str]] = {
    "fixedpred": "FixedPred",
    "strict": "Strict",
}


def _save_pdf(figure: Figure, path: Path, *, generated_at_utc: str, title: str) -> None:
    generated_at = datetime.fromisoformat(generated_at_utc.replace("Z", "+00:00"))
    if generated_at.tzinfo is None:
        generated_at = generated_at.replace(tzinfo=UTC)
    metadata = {
        "Title": title,
        "Author": "Torch2PC Layer-wise Thesis",
        "Subject": "Stage 3B B0 statistical and engineering analysis",
        "Creator": "torch2pc_thesis.stage3b_b0_figures",
        "Producer": f"Matplotlib {matplotlib.__version__}",
        "CreationDate": generated_at.astimezone(UTC),
        "ModDate": generated_at.astimezone(UTC),
    }
    figure.savefig(path, format="pdf", dpi=300, metadata=metadata)
    plt.close(figure)


def _ratio_by_depth(
    paired_configurations: pd.DataFrame,
    *,
    column: str,
    title: str,
    ylabel: str,
) -> Figure:
    figure, ax = plt.subplots(figsize=(6.6, 4.4), constrained_layout=True)
    for (width, batch_size), group in paired_configurations.groupby(
        ["width", "batch_size"], sort=True
    ):
        ordered = group.sort_values("depth")
        ax.plot(
            ordered["depth"].to_numpy(dtype=float),
            ordered[column].to_numpy(dtype=float),
            marker="o",
            linewidth=1.5,
            label=f"width={int(width)}, batch={int(batch_size)}",
        )
    ax.axhline(1.0, linestyle=":", linewidth=1.2, label="equal cost")
    ax.set_xscale("log", base=2)
    ax.set_xticks([4, 8, 16, 32], ["4", "8", "16", "32"])
    ax.set_xlabel("Depth")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False, fontsize=8)
    return cast(Figure, figure)


def _region_share_figure(region_summary: pd.DataFrame) -> Figure:
    ordered_regions = [
        "initial_forward",
        "state_inference",
        "local_state_vjp",
        "parameter_vjp",
        "optimizer_step",
    ]
    figure, ax = plt.subplots(figsize=(7.2, 4.4), constrained_layout=True)
    positions = np.arange(len(ordered_regions), dtype=float)
    bar_width = 0.36
    for offset, method in ((-bar_width / 2.0, "fixedpred"), (bar_width / 2.0, "strict")):
        subset = region_summary.loc[region_summary["method"] == method].set_index("region")
        values = np.asarray(
            [
                float(subset.loc[region, "device_time_share_of_region_sum_matrix_median"])
                for region in ordered_regions
            ],
            dtype=float,
        )
        ax.bar(
            positions + offset,
            values,
            width=bar_width,
            label=METHOD_LABELS[method],
        )
    ax.set_xticks(positions, [value.replace("_", "\n") for value in ordered_regions])
    ax.set_ylabel("Median share of summed region device time")
    ax.set_title("Stage 3B B0 device-time attribution by profiling region")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False)
    return cast(Figure, figure)


def _scaling_figure(scaling: pd.DataFrame) -> Figure:
    subset = scaling.loc[scaling["metric"].isin(("device_time", "peak_allocated"))].copy()
    labels = [
        "device/depth",
        "device/width",
        "device/batch",
        "memory/depth",
        "memory/width",
        "memory/batch",
    ]
    factor_label = {"depth": "depth", "width": "width", "batch_size": "batch"}
    metric_label = {"device_time": "device", "peak_allocated": "memory"}
    positions = np.arange(len(labels), dtype=float)
    bar_width = 0.36
    figure, ax = plt.subplots(figsize=(7.4, 4.5), constrained_layout=True)
    for offset, method in ((-bar_width / 2.0, "fixedpred"), (bar_width / 2.0, "strict")):
        method_rows = subset.loc[subset["method"] == method]
        values: list[float] = []
        for label in labels:
            metric_short, factor_short = label.split("/")
            metric = next(key for key, value in metric_label.items() if value == metric_short)
            factor = next(key for key, value in factor_label.items() if value == factor_short)
            row = method_rows.loc[
                (method_rows["metric"] == metric) & (method_rows["factor"] == factor)
            ]
            values.append(float(row["multiplier_per_doubling_median"].iloc[0]))
        ax.bar(positions + offset, values, width=bar_width, label=METHOD_LABELS[method])
    ax.axhline(1.0, linestyle=":", linewidth=1.2)
    ax.set_xticks(positions, [value.replace("/", "\n") for value in labels])
    ax.set_ylabel("Median multiplier per factor doubling")
    ax.set_title("Descriptive log2 main-effect scaling")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False)
    return cast(Figure, figure)


def generate_b0_figures(
    paired_configurations: pd.DataFrame,
    region_summary: pd.DataFrame,
    scaling_summary: pd.DataFrame,
    output_root: Path,
    *,
    generated_at_utc: str,
) -> dict[str, int]:
    """Generate four deterministic B0 analysis figures."""

    output_root.mkdir(parents=True, exist_ok=True)
    with matplotlib.rc_context(
        {
            "font.family": "DejaVu Sans",
            "pdf.compression": 9,
            "savefig.transparent": False,
        }
    ):
        device = _ratio_by_depth(
            paired_configurations,
            column="device_time_ratio_median",
            title="Strict relative to FixedPred: device time",
            ylabel="Strict / FixedPred median device time",
        )
        _save_pdf(
            device,
            output_root / FIGURE_FILENAMES[0],
            generated_at_utc=generated_at_utc,
            title="Strict relative to FixedPred: device time",
        )
        memory = _ratio_by_depth(
            paired_configurations,
            column="peak_allocated_ratio_median",
            title="Strict relative to FixedPred: peak allocated memory",
            ylabel="Strict / FixedPred peak allocated memory",
        )
        _save_pdf(
            memory,
            output_root / FIGURE_FILENAMES[1],
            generated_at_utc=generated_at_utc,
            title="Strict relative to FixedPred: peak allocated memory",
        )
        region = _region_share_figure(region_summary)
        _save_pdf(
            region,
            output_root / FIGURE_FILENAMES[2],
            generated_at_utc=generated_at_utc,
            title="Stage 3B B0 device-time attribution by profiling region",
        )
        scaling = _scaling_figure(scaling_summary)
        _save_pdf(
            scaling,
            output_root / FIGURE_FILENAMES[3],
            generated_at_utc=generated_at_utc,
            title="Descriptive log2 main-effect scaling",
        )
    return {filename: 1 for filename in FIGURE_FILENAMES}
