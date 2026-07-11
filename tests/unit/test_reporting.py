import pandas as pd
import pytest

from torch2pc_thesis.reporting import build_paired_primary_analysis

COHORT = {
    "git_commit": "a" * 40,
    "torch2pc_commit": "b" * 40,
    "environment_lock_sha256": "c" * 64,
    "split_seed": "42",
}


def _final_frame(candidate_offset: float, seeds: range) -> pd.DataFrame:
    rows = []
    for seed in seeds:
        baseline = 0.80 + seed * 0.001
        for method, value in [
            ("bp", baseline),
            ("fixedpred", baseline + candidate_offset),
            ("strict", baseline - candidate_offset),
        ]:
            rows.append(
                {
                    **COHORT,
                    "run_id": f"{method}-{seed}",
                    "stage": "final",
                    "dataset": "FashionMNIST",
                    "model": "lenet_classic",
                    "method": method,
                    "model_seed": str(seed),
                    "test_macro_f1": value,
                }
            )
    return pd.DataFrame(rows)


def test_paired_primary_analysis_requires_minimum_pairs() -> None:
    result = build_paired_primary_analysis(_final_frame(0.002, range(3)))
    assert not result["confirmatory_complete"].any()
    assert result["sign_flip_p_holm"].isna().all()
    assert not result["equivalent_within_margin"].any()


def test_paired_primary_analysis_reports_equivalence_only_when_complete() -> None:
    result = build_paired_primary_analysis(_final_frame(0.002, range(10)))
    assert result["confirmatory_complete"].all()
    assert result["equivalent_within_margin"].all()
    assert result["sign_flip_p_holm"].notna().all()
    assert result["model"].eq("lenet_classic").all()


def test_paired_primary_analysis_rejects_mixed_source_cohorts() -> None:
    frame = _final_frame(0.002, range(10))
    frame.loc[0, "git_commit"] = "d" * 40
    with pytest.raises(RuntimeError, match="mixes git_commit"):
        build_paired_primary_analysis(frame)


def test_paired_primary_analysis_rejects_duplicate_seed_method() -> None:
    frame = _final_frame(0.002, range(10))
    duplicate = frame.iloc[[0]].copy()
    duplicate["run_id"] = "duplicate-run"
    with pytest.raises(RuntimeError, match="duplicate"):
        build_paired_primary_analysis(pd.concat([frame, duplicate], ignore_index=True))


def test_paired_primary_analysis_rejects_undeclared_contrast() -> None:
    with pytest.raises(RuntimeError, match="Unsupported primary contrast"):
        build_paired_primary_analysis(
            _final_frame(0.002, range(10)),
            contrasts=["fixedpred_vs_exact"],
        )


def _write_completed_run(tmp_path, *, corrupt_metrics: bool = False):
    import json

    from torch2pc_thesis.config import config_sha256
    from torch2pc_thesis.manifests import directory_manifest
    from torch2pc_thesis.reporting import _verified_run_artifacts

    run_directory = tmp_path / "run"
    run_directory.mkdir()
    config = {"project": {"name": "test"}}
    config_hash = config_sha256(config)
    row = {
        "run_id": "run-1",
        "experiment_id": "experiment-1",
        "git_commit": "a" * 40,
        "config_sha256": config_hash,
    }
    (run_directory / "resolved_config.json").write_text(
        json.dumps(config), encoding="utf-8"
    )
    (run_directory / "environment.json").write_text(
        json.dumps(
            {
                "source_git_commit": row["git_commit"],
                "experiment_id": row["experiment_id"],
                "run_id": row["run_id"],
                "config_sha256": config_hash,
            }
        ),
        encoding="utf-8",
    )
    (run_directory / "metrics.json").write_text(
        json.dumps({"test_evaluated": False}), encoding="utf-8"
    )
    for name in ["history.csv", "checkpoint.pt", "validation_predictions.npz"]:
        (run_directory / name).write_bytes(name.encode())
    manifest = directory_manifest(run_directory)
    (run_directory / "manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    if corrupt_metrics:
        (run_directory / "metrics.json").write_text(
            json.dumps({"test_evaluated": False, "changed": True}),
            encoding="utf-8",
        )
    return _verified_run_artifacts, run_directory, row


def test_completed_run_artifacts_are_verified(tmp_path) -> None:
    verifier, run_directory, row = _write_completed_run(tmp_path)
    metrics, environment = verifier(run_directory, row)
    assert metrics["test_evaluated"] is False
    assert environment["run_id"] == "run-1"


def test_completed_run_artifact_hash_mismatch_is_rejected(tmp_path) -> None:
    verifier, run_directory, row = _write_completed_run(
        tmp_path, corrupt_metrics=True
    )
    with pytest.raises(RuntimeError, match="(?:size|hash) mismatch"):
        verifier(run_directory, row)
