from __future__ import annotations

import json
import shutil
import tarfile
from pathlib import Path

import pytest

from torch2pc_thesis.stage3b_matched_publication import (
    ANALYSIS_OUTPUT_ROOT,
    MATCHED_EVIDENCE_RELEASE_TAG,
    PUBLICATION_ACTION_TAG,
    PUBLICATION_GATE_ID,
    PUBLICATION_GATE_ROOT,
    Stage3BMatchedPublicationError,
    package_publication_assets,
    sha256_file,
    validate_publication_inputs,
)

ROOT = Path(__file__).resolve().parents[2]
PUBLICATION_WORKFLOW = (
    ROOT / ".github/workflows/stage3b-matched-analysis-publication.yml"
)
DRAFT_WORKFLOW = ROOT / ".github/workflows/stage3b-matched-evidence-release.yml"


def test_publication_gate_validates_exact_sealed_inputs() -> None:
    result = validate_publication_inputs(ROOT)

    gate = result["gate"]
    assert isinstance(gate, dict)
    assert gate["gate_id"] == PUBLICATION_GATE_ID
    assert gate["publication_action_tag"] == PUBLICATION_ACTION_TAG
    assert gate["evidence_release_tag"] == MATCHED_EVIDENCE_RELEASE_TAG
    assert gate["required_remote_release_state_before_action"] == "draft"
    assert gate["claim_boundary_after_successful_action"] == {
        "ex_if0_opened": False,
        "full_stage3b_campaign_complete": False,
        "policy_activation_permitted": False,
        "release_publication_permitted": True,
        "results_publication_permitted": True,
        "superiority_claim_permitted": False,
        "test_dataset_access": False,
    }


def test_publication_packaging_is_reproducible_and_bounded(
    tmp_path: Path,
) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    kwargs = {
        "publication_tag": PUBLICATION_ACTION_TAG,
        "publication_commit": "f" * 40,
    }
    result = package_publication_assets(ROOT, first, **kwargs)
    package_publication_assets(ROOT, second, **kwargs)

    assert result["status"] == "publication_assets_ready"
    assert result["results_publication_permitted"] is True
    assert result["release_publication_permitted"] is True
    assert result["release_publication_complete"] is False
    assert result["superiority_claim_permitted"] is False
    assert result["ex_if0_opened"] is False

    expected = {
        "stage3b-matched-descriptive-analysis-sealed-output-v1.tar.gz",
        "stage3b-matched-descriptive-analysis-audit-seal-v1.tar.gz",
        "PUBLICATION-NOTES.md",
        "PUBLICATION-MANIFEST.json",
        "PUBLICATION-SHA256SUMS",
    }
    assert {path.name for path in first.iterdir()} == expected
    assert {path.name for path in second.iterdir()} == expected
    for name in expected:
        assert (first / name).read_bytes() == (second / name).read_bytes()

    manifest = json.loads(
        (first / "PUBLICATION-MANIFEST.json").read_text(encoding="utf-8")
    )
    assert manifest["publication_gate_id"] == PUBLICATION_GATE_ID
    assert manifest["publication_action_commit"] == "f" * 40
    assert manifest["results_publication_permitted"] is True
    assert manifest["release_publication_complete"] is False
    assert manifest["superiority_claim_permitted"] is False
    assert manifest["ex_if0_opened"] is False

    registry = (first / "PUBLICATION-SHA256SUMS").read_text(
        encoding="utf-8"
    )
    assert len(registry.splitlines()) == 4
    for line in registry.splitlines():
        digest, name = line.split(maxsplit=1)
        assert sha256_file(first / name) == digest

    analysis_archive = first / (
        "stage3b-matched-descriptive-analysis-sealed-output-v1.tar.gz"
    )
    with tarfile.open(analysis_archive, mode="r:gz") as handle:
        names = set(handle.getnames())
    assert len(names) == 18
    assert any(name.endswith("/REPORT.md") for name in names)
    assert any(name.endswith("/engineering_decision.json") for name in names)
    assert any(name.endswith("/SHA256SUMS") for name in names)


def test_publication_gate_rejects_tampered_output(tmp_path: Path) -> None:
    project = tmp_path / "project"
    shutil.copytree(ROOT, project)
    report = project / ANALYSIS_OUTPUT_ROOT / "REPORT.md"
    report.write_text("tampered\n", encoding="utf-8")

    with pytest.raises(
        Stage3BMatchedPublicationError,
        match="checksum verification failed",
    ):
        validate_publication_inputs(project)


def test_publication_gate_rejects_tampered_gate(tmp_path: Path) -> None:
    project = tmp_path / "project"
    shutil.copytree(ROOT, project)
    gate_path = project / PUBLICATION_GATE_ROOT / "gate.json"
    gate = json.loads(gate_path.read_text(encoding="utf-8"))
    gate["claim_boundary_after_successful_action"][
        "superiority_claim_permitted"
    ] = True
    gate_path.write_text(
        json.dumps(gate, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        Stage3BMatchedPublicationError,
        match="checksum verification failed",
    ):
        validate_publication_inputs(project)


def test_publication_packager_rejects_wrong_tag(tmp_path: Path) -> None:
    with pytest.raises(
        Stage3BMatchedPublicationError,
        match="unexpected publication tag",
    ):
        package_publication_assets(
            ROOT,
            tmp_path / "output",
            publication_tag="wrong-tag",
            publication_commit="f" * 40,
        )


def test_publication_workflow_is_fail_closed_and_uploads_before_publish() -> None:
    text = PUBLICATION_WORKFLOW.read_text(encoding="utf-8")

    assert f'"{PUBLICATION_ACTION_TAG}"' in text
    assert f"EVIDENCE_RELEASE_TAG: {MATCHED_EVIDENCE_RELEASE_TAG}" in text
    assert 'repos/$GITHUB_REPOSITORY/releases?per_page=100' in text
    assert 'releases/tags/$EVIDENCE_RELEASE_TAG' not in text
    assert 'assert len(matches) == 1' in text
    assert 'assert state["draft"] is True' in text
    assert 'assert state.get("immutable") is False' in text
    assert "gh release upload" in text
    assert "gh release edit" in text
    assert text.index("gh release upload") < text.index("--draft=false")
    assert "--latest=false" in text
    assert 'assert state["isDraft"] is False' in text
    assert "EX-IF0" not in text


def test_draft_release_workflow_reasserts_draft_for_existing_release() -> None:
    text = DRAFT_WORKFLOW.read_text(encoding="utf-8")

    existing = text.index(
        'if gh release view "$GITHUB_REF_NAME" >/dev/null 2>&1; then'
    )
    force_draft = text.index(
        'gh release edit "$GITHUB_REF_NAME" --draft --latest=false',
        existing,
    )
    upload = text.index("gh release upload", force_draft)
    assert existing < force_draft < upload
    assert "--latest=false" in text
