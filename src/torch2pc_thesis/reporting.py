from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from torch2pc_thesis.registry import completed_experiments
from torch2pc_thesis.statistics import (
    cohen_dz,
    equivalence_by_ci,
    exact_sign_flip_pvalue,
    holm_adjust,
    mean_difference_ci,
    summarize_with_ci,
)


def collect_metrics(
    registry_path: str | Path,
    project_root: str | Path = ".",
) -> pd.DataFrame:
    root = Path(project_root)
    records: list[dict[str, Any]] = []
    for row in completed_experiments(registry_path):
        metrics_path = root / row["run_directory"] / "metrics.json"
        if not metrics_path.exists():
            continue
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        records.append({**row, **metrics})
    return pd.DataFrame(records)



def build_paired_primary_analysis(
    final: pd.DataFrame,
    *,
    primary_dataset: str = "FashionMNIST",
    primary_metric: str = "test_macro_f1",
    margin: float = 0.01,
    alpha: float = 0.05,
    minimum_pairs: int = 10,
) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    primary = final[
        (final["stage"] == "final")
        & (final["dataset"] == primary_dataset)
        & final[primary_metric].notna()
    ].copy()
    baseline = primary[primary["method"] == "bp"][
        ["model", "model_seed", primary_metric]
    ].rename(columns={primary_metric: "baseline_value"})

    for method in ["fixedpred", "strict"]:
        candidate = primary[primary["method"] == method][
            ["model", "model_seed", primary_metric]
        ].rename(columns={primary_metric: "candidate_value"})
        paired = baseline.merge(candidate, on=["model", "model_seed"], how="inner")
        differences = (
            paired["candidate_value"].astype(float)
            - paired["baseline_value"].astype(float)
        ).to_numpy()
        mean, ci_low, ci_high = mean_difference_ci(
            differences, confidence=1 - alpha
        )
        equivalence = equivalence_by_ci(
            differences, margin=margin, alpha=alpha
        )
        complete = len(differences) >= minimum_pairs
        records.append(
            {
                "dataset": primary_dataset,
                "contrast": f"{method}_vs_bp",
                "metric": primary_metric,
                "n_pairs": int(len(differences)),
                "minimum_pairs": int(minimum_pairs),
                "confirmatory_complete": complete,
                "analysis_status": "confirmatory" if complete else "incomplete",
                "mean_difference": mean,
                "ci95_low": ci_low,
                "ci95_high": ci_high,
                "cohen_dz": cohen_dz(differences),
                "sign_flip_p_raw": (
                    exact_sign_flip_pvalue(differences) if complete else float("nan")
                ),
                "equivalence_margin": margin,
                "tost_ci90_low": equivalence["tost_ci_low"],
                "tost_ci90_high": equivalence["tost_ci_high"],
                "equivalent_within_margin": bool(
                    complete and equivalence["equivalent"]
                ),
            }
        )
    result = pd.DataFrame(records)
    if not result.empty:
        valid = result["sign_flip_p_raw"].notna()
        result["sign_flip_p_holm"] = float("nan")
        if valid.any():
            result.loc[valid, "sign_flip_p_holm"] = holm_adjust(
                result.loc[valid, "sign_flip_p_raw"].astype(float).tolist()
            )
    return result

def write_latex_table(frame: pd.DataFrame, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        frame.to_latex(index=False, float_format=lambda value: f"{value:.4f}"),
        encoding="utf-8",
    )
    return output


def build_primary_assets(
    registry_path: str | Path = "experiments/registry.csv",
    config_path: str | Path = "configs/base.yaml",
) -> dict[str, str]:
    base_config = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    statistics = base_config["statistics"]
    metrics = collect_metrics(registry_path)
    summary_dir = Path("results/summaries")
    table_dir = Path("results/tables")
    summary_dir.mkdir(parents=True, exist_ok=True)
    table_dir.mkdir(parents=True, exist_ok=True)

    metrics_path = summary_dir / "registered_metrics.csv"
    metrics.to_csv(metrics_path, index=False)
    outputs = {"metrics": str(metrics_path)}
    if metrics.empty:
        return outputs

    validation_columns = [
        column
        for column in ["best_validation_metric"]
        if column in metrics.columns
    ]
    if validation_columns:
        validation = summarize_with_ci(
            metrics,
            ["stage", "dataset", "model", "method", "eta", "inference_steps"],
            validation_columns,
        )
        path = summary_dir / "validation_summary.csv"
        validation.to_csv(path, index=False)
        outputs["validation_summary"] = str(path)

    final = metrics[
        metrics.get("test_evaluated", False).astype(str).str.lower().eq("true")
    ].copy()
    test_columns = [
        column for column in ["test_accuracy", "test_macro_f1"] if column in final.columns
    ]
    if not final.empty and test_columns:
        summary = summarize_with_ci(
            final,
            ["dataset", "model", "method", "eta", "inference_steps"],
            test_columns,
        )
        summary_path = summary_dir / "primary_test_summary.csv"
        summary.to_csv(summary_path, index=False)
        latex_path = write_latex_table(summary, table_dir / "primary_test_summary.tex")
        outputs.update({"test_summary": str(summary_path), "latex": str(latex_path)})

        paired = build_paired_primary_analysis(
            final,
            primary_dataset=str(statistics["primary_dataset"]),
            primary_metric="test_macro_f1",
            margin=float(statistics["equivalence_margin_macro_f1"]),
            alpha=float(statistics["alpha"]),
            minimum_pairs=int(statistics["minimum_primary_pairs"]),
        )
        paired_path = summary_dir / "primary_paired_analysis.csv"
        paired.to_csv(paired_path, index=False)
        paired_latex = write_latex_table(
            paired, table_dir / "primary_paired_analysis.tex"
        )
        outputs.update(
            {
                "paired_primary_analysis": str(paired_path),
                "paired_primary_latex": str(paired_latex),
            }
        )
    return outputs
