from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from torch2pc_thesis.reporting import collect_metrics
from torch2pc_thesis.statistics import summarize_with_ci

PAIR_KEY = ["dataset", "model", "method", "model_seed"]
BLOCK_KEY = ["dataset", "model", "model_seed"]


def _cohort(
    registry: str | Path,
    *,
    stage: str,
    label: str,
) -> pd.DataFrame:
    frame = collect_metrics(registry)
    frame = frame[
        frame["stage"].astype(str).eq(stage)
        & frame["test_evaluated"].astype(str).str.lower().eq("true")
    ].copy()
    if frame.empty:
        raise RuntimeError(f"No completed test runs for {label}")
    duplicated = frame.duplicated(PAIR_KEY, keep=False)
    if duplicated.any():
        raise RuntimeError(f"Duplicate paired cells in {label}")
    frame["implementation_variant"] = label
    return frame


def _runtime_slowdown(frame: pd.DataFrame) -> pd.DataFrame:
    required = "total_training_time_sec"
    if required not in frame.columns:
        raise RuntimeError("Training time is absent from the cohort")
    baseline = frame[frame["method"] == "bp"][
        BLOCK_KEY + [required]
    ].rename(columns={required: "bp_training_time_sec"})
    result = frame.merge(baseline, on=BLOCK_KEY, how="left", validate="many_to_one")
    if result["bp_training_time_sec"].isna().any():
        raise RuntimeError("A paired block has no BP timing baseline")
    result["runtime_over_bp"] = (
        result[required].astype(float) / result["bp_training_time_sec"].astype(float)
    )
    return result


def _difference_in_differences(
    reference: pd.DataFrame,
    candidate: pd.DataFrame,
) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for dataset in sorted(set(reference["dataset"]) & set(candidate["dataset"])):
        for model in sorted(set(reference["model"]) & set(candidate["model"])):
            ref_block = reference[
                (reference["dataset"] == dataset) & (reference["model"] == model)
            ]
            cand_block = candidate[
                (candidate["dataset"] == dataset) & (candidate["model"] == model)
            ]
            for seed in sorted(set(ref_block["model_seed"]) & set(cand_block["model_seed"])):
                ref_seed = ref_block[ref_block["model_seed"] == seed].set_index("method")
                cand_seed = cand_block[cand_block["model_seed"] == seed].set_index("method")
                if "bp" not in ref_seed.index or "bp" not in cand_seed.index:
                    raise RuntimeError("Difference-in-differences requires BP in every block")
                for method in ["exact", "fixedpred", "strict"]:
                    if method not in ref_seed.index or method not in cand_seed.index:
                        raise RuntimeError(f"Missing method={method} in paired block")
                    quality_reference = float(ref_seed.loc[method, "test_macro_f1"]) - float(
                        ref_seed.loc["bp", "test_macro_f1"]
                    )
                    quality_candidate = float(cand_seed.loc[method, "test_macro_f1"]) - float(
                        cand_seed.loc["bp", "test_macro_f1"]
                    )
                    runtime_reference = float(ref_seed.loc[method, "runtime_over_bp"])
                    runtime_candidate = float(cand_seed.loc[method, "runtime_over_bp"])
                    records.append(
                        {
                            "dataset": dataset,
                            "model": model,
                            "model_seed": seed,
                            "method": method,
                            "quality_contrast_reference": quality_reference,
                            "quality_contrast_candidate": quality_candidate,
                            "quality_difference_in_differences": (
                                quality_candidate - quality_reference
                            ),
                            "runtime_over_bp_reference": runtime_reference,
                            "runtime_over_bp_candidate": runtime_candidate,
                            "runtime_slowdown_change": (
                                runtime_candidate - runtime_reference
                            ),
                            "runtime_slowdown_ratio": (
                                runtime_candidate / runtime_reference
                            ),
                        }
                    )
    return pd.DataFrame(records)


def build_cross_version_assets(
    reference_registry: str | Path,
    candidate_registry: str | Path,
    output_dir: str | Path = "results/cross-version",
) -> dict[str, str]:
    reference = _runtime_slowdown(
        _cohort(reference_registry, stage="final", label="original")
    )
    candidate = _runtime_slowdown(
        _cohort(candidate_registry, stage="final_stage_2", label="patched")
    )
    reference_keys = set(map(tuple, reference[PAIR_KEY].to_numpy()))
    candidate_keys = set(map(tuple, candidate[PAIR_KEY].to_numpy()))
    if reference_keys != candidate_keys:
        missing_candidate = sorted(reference_keys - candidate_keys)
        missing_reference = sorted(candidate_keys - reference_keys)
        raise RuntimeError(
            "Stage 1 and Stage 2 matrices differ: "
            f"missing_candidate={missing_candidate}, missing_reference={missing_reference}"
        )

    columns = PAIR_KEY + [
        "test_accuracy",
        "test_macro_f1",
        "total_training_time_sec",
        "mean_epoch_time_sec",
        "median_epoch_time_sec",
        "peak_gpu_memory_allocated_bytes",
        "peak_gpu_memory_reserved_bytes",
        "runtime_over_bp",
    ]
    available = [column for column in columns if column in reference.columns and column in candidate.columns]
    paired = reference[available].merge(
        candidate[available],
        on=PAIR_KEY,
        how="inner",
        validate="one_to_one",
        suffixes=("_original", "_patched"),
    )
    metric_names = [column for column in available if column not in PAIR_KEY]
    for metric in metric_names:
        paired[f"{metric}_difference"] = (
            paired[f"{metric}_patched"].astype(float)
            - paired[f"{metric}_original"].astype(float)
        )
        denominator = paired[f"{metric}_original"].astype(float)
        paired[f"{metric}_ratio"] = np.where(
            denominator != 0,
            paired[f"{metric}_patched"].astype(float) / denominator,
            np.nan,
        )

    difference_columns = [
        column for column in paired.columns if column.endswith("_difference")
    ]
    ratio_columns = [column for column in paired.columns if column.endswith("_ratio")]
    summary = summarize_with_ci(
        paired,
        ["dataset", "model", "method"],
        difference_columns + ratio_columns,
    )
    did = _difference_in_differences(reference, candidate)
    did_summary = summarize_with_ci(
        did,
        ["dataset", "model", "method"],
        [
            "quality_difference_in_differences",
            "runtime_slowdown_change",
            "runtime_slowdown_ratio",
        ],
    )

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    pair_path = destination / "cross_version_pair_records.csv"
    summary_path = destination / "cross_version_summary.csv"
    did_path = destination / "difference_in_differences_records.csv"
    did_summary_path = destination / "difference_in_differences_summary.csv"
    paired.to_csv(pair_path, index=False)
    summary.to_csv(summary_path, index=False)
    did.to_csv(did_path, index=False)
    did_summary.to_csv(did_summary_path, index=False)
    return {
        "paired_records": str(pair_path),
        "summary": str(summary_path),
        "difference_in_differences_records": str(did_path),
        "difference_in_differences_summary": str(did_summary_path),
    }
