from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from torch2pc_thesis.config import config_sha256
from torch2pc_thesis.manifests import sha256_file
from torch2pc_thesis.registry import completed_experiments
from torch2pc_thesis.statistics import (
    cohen_dz,
    equivalence_by_ci,
    exact_sign_flip_pvalue,
    holm_adjust,
    mean_difference_ci,
    summarize_with_ci,
)

COHORT_COLUMNS = [
    "git_commit",
    "torch2pc_commit",
    "environment_lock_sha256",
    "split_seed",
]
PAIRING_KEY = ["dataset", "model", "method", "model_seed"]


def _json_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"Expected a JSON object: {path}")
    return value




def verified_run_artifacts(
    run_directory: Path,
    row: dict[str, str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    required_paths = {
        "metrics.json": run_directory / "metrics.json",
        "environment.json": run_directory / "environment.json",
        "resolved_config.json": run_directory / "resolved_config.json",
        "manifest.json": run_directory / "manifest.json",
    }
    missing = [name for name, path in required_paths.items() if not path.is_file()]
    if missing:
        raise RuntimeError(
            f"Completed run is missing required artifacts {missing}: {run_directory}"
        )

    metrics = _json_object(required_paths["metrics.json"])
    environment = _json_object(required_paths["environment.json"])
    resolved_config = _json_object(required_paths["resolved_config.json"])
    manifest = _json_object(required_paths["manifest.json"])

    expected_identity = {
        "source_git_commit": row["git_commit"],
        "experiment_id": row["experiment_id"],
        "run_id": row["run_id"],
        "config_sha256": row["config_sha256"],
    }
    for key, expected in expected_identity.items():
        if str(environment.get(key, "")) != expected:
            raise RuntimeError(
                f"Environment artifact disagrees with registry for {key}: "
                f"{run_directory}"
            )
    if config_sha256(resolved_config) != row["config_sha256"]:
        raise RuntimeError(f"Resolved configuration hash mismatch: {run_directory}")

    file_records = manifest.get("files")
    if not isinstance(file_records, list) or not file_records:
        raise RuntimeError(f"Run manifest contains no file records: {run_directory}")
    indexed: dict[str, dict[str, Any]] = {}
    for item in file_records:
        if not isinstance(item, dict):
            raise RuntimeError(f"Invalid run manifest record: {run_directory}")
        relative = str(item.get("path", ""))
        if not relative or relative in indexed:
            raise RuntimeError(f"Duplicate or empty run manifest path: {run_directory}")
        indexed[relative] = item

    expected_files = {
        "environment.json",
        "resolved_config.json",
        "metrics.json",
        "history.csv",
        "checkpoint.pt",
        "validation_predictions.npz",
    }
    if bool(metrics.get("test_evaluated", False)):
        expected_files.add("test_predictions.npz")
    absent_from_manifest = sorted(expected_files - set(indexed))
    if absent_from_manifest:
        raise RuntimeError(
            f"Run manifest omits required files {absent_from_manifest}: {run_directory}"
        )
    for relative, item in indexed.items():
        path = run_directory / relative
        resolved = path.resolve()
        try:
            resolved.relative_to(run_directory.resolve())
        except ValueError as exc:
            raise RuntimeError(
                f"Run manifest path escapes its run directory: {relative}"
            ) from exc
        if not path.is_file():
            raise RuntimeError(f"Run artifact is missing: {path}")
        if path.stat().st_size != int(item.get("bytes", -1)):
            raise RuntimeError(f"Run artifact size mismatch: {path}")
        if sha256_file(path) != str(item.get("sha256", "")):
            raise RuntimeError(f"Run artifact hash mismatch: {path}")
    return metrics, environment


# Backward-compatible internal name retained for existing callers and tests.
_verified_run_artifacts = verified_run_artifacts


def collect_metrics(
    registry_path: str | Path,
    project_root: str | Path = ".",
) -> pd.DataFrame:
    root = Path(project_root)
    records: list[dict[str, Any]] = []
    root_resolved = root.resolve()
    for row in completed_experiments(registry_path):
        run_directory = (root / row["run_directory"]).resolve()
        try:
            run_directory.relative_to(root_resolved)
        except ValueError as exc:
            raise RuntimeError(
                f"Registered run directory escapes the project root: {run_directory}"
            ) from exc
        metrics, environment = verified_run_artifacts(run_directory, row)
        registry_test = row["test_evaluated"].lower() == "true"
        if bool(metrics.get("test_evaluated", False)) != registry_test:
            raise RuntimeError(
                f"Registry and metrics disagree about test access: {run_directory}"
            )
        records.append(
            {
                **row,
                **metrics,
                "environment_lock_sha256": environment.get(
                    "environment_lock_sha256"
                ),
            }
        )
    return pd.DataFrame(records)


def _validate_confirmatory_cohort(primary: pd.DataFrame) -> None:
    missing = [column for column in COHORT_COLUMNS if column not in primary.columns]
    if missing:
        raise RuntimeError(f"Confirmatory cohort metadata is missing: {missing}")
    for column in COHORT_COLUMNS:
        values = primary[column].dropna().astype(str)
        if values.empty or values.nunique() != 1:
            observed = sorted(values.unique().tolist())
            raise RuntimeError(
                f"Confirmatory analysis mixes {column} values: {observed}"
            )
    duplicated = primary.duplicated(PAIRING_KEY, keep=False)
    if duplicated.any():
        conflicts = primary.loc[duplicated, PAIRING_KEY + ["run_id"]]
        raise RuntimeError(
            "Confirmatory analysis contains duplicate method/seed observations: "
            f"{conflicts.to_dict(orient='records')}"
        )


def build_paired_primary_analysis(
    final: pd.DataFrame,
    *,
    primary_dataset: str = "FashionMNIST",
    primary_model: str = "lenet_classic",
    primary_metric: str = "test_macro_f1",
    contrasts: list[str] | None = None,
    margin: float = 0.01,
    alpha: float = 0.05,
    minimum_pairs: int = 10,
    stage_name: str = "final",
) -> pd.DataFrame:
    if primary_metric not in final.columns:
        raise RuntimeError(f"Primary metric is absent: {primary_metric}")
    records: list[dict[str, Any]] = []
    primary = final[
        (final["stage"] == stage_name)
        & (final["dataset"] == primary_dataset)
        & (final["model"] == primary_model)
        & final[primary_metric].notna()
    ].copy()
    if primary.empty:
        return pd.DataFrame()
    _validate_confirmatory_cohort(primary)

    baseline = primary[primary["method"] == "bp"][
        ["model", "model_seed", primary_metric]
    ].rename(columns={primary_metric: "baseline_value"})

    contrast_names = contrasts or ["fixedpred_vs_bp", "strict_vs_bp"]
    methods: list[str] = []
    for contrast in contrast_names:
        suffix = "_vs_bp"
        if not contrast.endswith(suffix):
            raise RuntimeError(f"Unsupported primary contrast: {contrast}")
        methods.append(contrast[: -len(suffix)])

    for method in methods:
        candidate = primary[primary["method"] == method][
            ["model", "model_seed", primary_metric]
        ].rename(columns={primary_metric: "candidate_value"})
        paired = baseline.merge(
            candidate,
            on=["model", "model_seed"],
            how="inner",
            validate="one_to_one",
        ).sort_values(["model", "model_seed"])
        differences = (
            paired["candidate_value"].astype(float)
            - paired["baseline_value"].astype(float)
        ).to_numpy()
        if not pd.Series(differences).map(lambda value: math.isfinite(float(value))).all():
            raise RuntimeError(f"Non-finite paired difference for method={method}")
        mean, ci_low, ci_high = mean_difference_ci(differences, confidence=1 - alpha)
        equivalence = equivalence_by_ci(differences, margin=margin, alpha=alpha)
        complete = len(differences) >= minimum_pairs
        records.append(
            {
                "dataset": primary_dataset,
                "model": primary_model,
                "contrast": f"{method}_vs_bp",
                "metric": primary_metric,
                "n_pairs": int(len(differences)),
                "paired_model_seeds": ",".join(
                    paired["model_seed"].astype(str).tolist()
                ),
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
    *,
    stage_name: str = "final",
    summary_dir_path: str | Path = "results/summaries",
    table_dir_path: str | Path = "results/tables",
) -> dict[str, str]:
    base_config = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    statistics = base_config["statistics"]
    metrics = collect_metrics(registry_path)
    summary_dir = Path(summary_dir_path)
    table_dir = Path(table_dir_path)
    summary_dir.mkdir(parents=True, exist_ok=True)
    table_dir.mkdir(parents=True, exist_ok=True)

    metrics_path = summary_dir / "registered_metrics.csv"
    metrics.to_csv(metrics_path, index=False)
    outputs = {"metrics": str(metrics_path)}
    if metrics.empty:
        return outputs

    if "best_validation_metric" in metrics.columns:
        validation = summarize_with_ci(
            metrics,
            ["stage", "dataset", "model", "method", "eta", "inference_steps"],
            ["best_validation_metric"],
        )
        path = summary_dir / "validation_summary.csv"
        validation.to_csv(path, index=False)
        outputs["validation_summary"] = str(path)

    if "test_evaluated" not in metrics.columns:
        return outputs
    final = metrics[
        metrics["test_evaluated"].astype(str).str.lower().eq("true")
        & metrics["stage"].astype(str).eq(stage_name)
    ].copy()
    test_columns = [
        column for column in ["test_accuracy", "test_macro_f1"] if column in final.columns
    ]
    if not final.empty:
        computational_columns = [
            column
            for column in [
                "total_training_time_sec",
                "mean_epoch_time_sec",
                "median_epoch_time_sec",
                "peak_gpu_memory_allocated_bytes",
                "peak_gpu_memory_reserved_bytes",
            ]
            if column in final.columns
        ]
        if computational_columns:
            computational = summarize_with_ci(
                final,
                ["dataset", "model", "method", "eta", "inference_steps"],
                computational_columns,
            )
            computational_path = summary_dir / "computational_summary.csv"
            computational.to_csv(computational_path, index=False)
            outputs["computational_summary"] = str(computational_path)

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

        configured_metric = str(statistics["primary_metric"])
        primary_metric = f"test_{configured_metric}"
        paired = build_paired_primary_analysis(
            final,
            primary_dataset=str(statistics["primary_dataset"]),
            primary_model=str(statistics["primary_model"]),
            primary_metric=primary_metric,
            contrasts=[str(value) for value in statistics["primary_contrasts"]],
            margin=float(statistics["equivalence_margin_macro_f1"]),
            alpha=float(statistics["alpha"]),
            minimum_pairs=int(statistics["minimum_primary_pairs"]),
            stage_name=stage_name,
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
