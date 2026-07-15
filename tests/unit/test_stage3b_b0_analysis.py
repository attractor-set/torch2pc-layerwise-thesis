"""Regression tests for sealed Stage 3B B0 statistical analysis."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pandas as pd
import pytest

from torch2pc_thesis.stage3b_b0_analysis import (
    B0AnalysisContract,
    Stage3BB0AnalysisError,
    generate_stage3b_b0_analysis,
    load_b0_evidence,
    sha256_file,
    verify_sealed_evidence,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_ROOT = REPO_ROOT / "results/stage-3/profiling/b0/sealed-v1"
SOURCE_COMMIT = "ac21d1fe80fa7bcdda64ae23f6fa61c9a57f0231"
GENERATED_AT = "2026-07-15T02:20:00Z"
EXPECTED_OUTPUTS = {
    "SHA256SUMS",
    "analysis_metadata.json",
    "analysis_summary.json",
    "paired_configuration_summary.csv",
    "paired_device_time_ratio_by_depth.pdf",
    "paired_matrix_summary.csv",
    "paired_peak_allocated_ratio_by_depth.pdf",
    "region_configuration_summary.csv",
    "region_device_time_share.pdf",
    "region_matrix_summary.csv",
    "region_paired_configuration_summary.csv",
    "region_seed_attribution.csv",
    "report.md",
    "report_EN.md",
    "scaling_multiplier_per_doubling.pdf",
    "scaling_seed_effects.csv",
    "scaling_summary.csv",
}


def _tree_digests(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): sha256_file(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _rewrite_inventory(root: Path) -> None:
    entries = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS":
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            entries.append(f"{digest}  ./{path.relative_to(root)}")
    (root / "SHA256SUMS").write_text("\n".join(entries) + "\n", encoding="utf-8")


def _generate(output: Path) -> dict[str, int]:
    return generate_stage3b_b0_analysis(
        EVIDENCE_ROOT,
        output,
        repo_root=REPO_ROOT,
        source_commit=SOURCE_COMMIT,
        generated_at_utc=GENERATED_AT,
    )


def test_load_published_b0_evidence_accepts_frozen_matrix() -> None:
    evidence = load_b0_evidence(EVIDENCE_ROOT)
    contract = B0AnalysisContract()

    assert len(evidence.cell_metrics) == contract.expected_cell_count == 96
    assert len(evidence.region_metrics) == contract.expected_region_count == 480
    assert len(evidence.paired_metrics) == contract.expected_pair_count == 48
    assert len(evidence.configuration_metrics) == contract.expected_configuration_count == 32
    assert evidence.seal["full_b0_campaign_complete"] is True
    assert evidence.seal["full_stage3b_campaign_complete"] is False
    assert evidence.seal["test_dataset_access"] is False


def test_generate_analysis_creates_bounded_artifacts_and_preserves_input(
    tmp_path: Path,
) -> None:
    before = _tree_digests(EVIDENCE_ROOT)
    output = tmp_path / "analysis"

    counts = _generate(output)

    assert set(path.name for path in output.iterdir()) == EXPECTED_OUTPUTS
    assert counts["paired_configuration_summary.csv"] == 16
    assert counts["paired_matrix_summary.csv"] == 4
    assert counts["region_seed_attribution.csv"] == 480
    assert counts["region_configuration_summary.csv"] == 160
    assert counts["region_matrix_summary.csv"] == 10
    assert counts["region_paired_configuration_summary.csv"] == 80
    assert counts["scaling_seed_effects.csv"] == 72
    assert counts["scaling_summary.csv"] == 24
    assert verify_sealed_evidence(EVIDENCE_ROOT)
    assert _tree_digests(EVIDENCE_ROOT) == before

    summary = json.loads((output / "analysis_summary.json").read_text(encoding="utf-8"))
    assert summary["status"] == "analysis_complete"
    assert summary["full_b0_campaign_complete"] is True
    assert summary["full_stage3b_campaign_complete"] is False
    assert summary["statistical_unit"] == "model_seed"
    assert summary["inferential_scope"] == "descriptive_engineering_analysis_n3"
    assert (
        summary["decision_gate"]["b1_b2_candidate_specific_equivalence_work"]
        == "continue"
    )
    assert (
        summary["decision_gate"]["full_b1_b2_matched_profiling"]
        == "blocked_pending_candidate_specific_gates"
    )
    assert summary["locality_coverage"]["structural_locality_claims_supported"] is False
    assert summary["decision_gate"]["new_b0_execution"] == "not_required"
    assert summary["saved_tensor_analysis"][
        "state_inference_strict_to_fixedpred_ratio"
    ] > 10.0

    paired = pd.read_csv(output / "paired_matrix_summary.csv")
    assert bool(paired["all_configuration_medians_strict_greater"].all())
    assert float(
        paired.loc[paired["metric"] == "device_time", "configuration_median_ratio"].iloc[0]
    ) > 2.0

    for csv_path in output.glob("*.csv"):
        data = csv_path.read_bytes()
        assert b"\r\n" not in data
        assert data.endswith(b"\n")

    assert "n=3" in (output / "report.md").read_text(encoding="utf-8")
    assert "n=3" in (output / "report_EN.md").read_text(encoding="utf-8")


def test_analysis_outputs_are_deterministic_for_fixed_provenance(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"

    _generate(first)
    _generate(second)

    assert _tree_digests(first) == _tree_digests(second)


def test_checksum_tampering_is_detected(tmp_path: Path) -> None:
    copied = tmp_path / "sealed-v1"
    shutil.copytree(EVIDENCE_ROOT, copied)
    with (copied / "paired_method_metrics.csv").open("a", encoding="utf-8") as handle:
        handle.write("tampered\n")

    with pytest.raises(Stage3BB0AnalysisError, match="checksum mismatch"):
        load_b0_evidence(copied)


def test_claim_boundary_tampering_is_detected_even_with_rewritten_inventory(
    tmp_path: Path,
) -> None:
    copied = tmp_path / "sealed-v1"
    shutil.copytree(EVIDENCE_ROOT, copied)
    seal_path = copied / "seal.json"
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    seal["full_stage3b_campaign_complete"] = True
    seal_path.write_text(json.dumps(seal, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _rewrite_inventory(copied)

    with pytest.raises(Stage3BB0AnalysisError, match="claim boundary mismatch"):
        load_b0_evidence(copied)


def test_identity_tampering_is_detected_even_with_rewritten_inventory(
    tmp_path: Path,
) -> None:
    copied = tmp_path / "sealed-v1"
    shutil.copytree(EVIDENCE_ROOT, copied)
    seal_path = copied / "seal.json"
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    seal["source_commit"] = "0" * 40
    seal_path.write_text(json.dumps(seal, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _rewrite_inventory(copied)

    with pytest.raises(Stage3BB0AnalysisError, match="identity mismatch"):
        load_b0_evidence(copied)


def test_output_cannot_be_created_inside_sealed_input(tmp_path: Path) -> None:
    copied = tmp_path / "sealed-v1"
    shutil.copytree(EVIDENCE_ROOT, copied)

    with pytest.raises(Stage3BB0AnalysisError, match="outside sealed-v1"):
        generate_stage3b_b0_analysis(
            copied,
            copied / "analysis-v1",
            repo_root=REPO_ROOT,
            source_commit=SOURCE_COMMIT,
            generated_at_utc=GENERATED_AT,
        )
