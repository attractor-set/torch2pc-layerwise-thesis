from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RECEIPT_ROOT = ROOT / (
    "experiments/frozen/"
    "stage3b-matched-descriptive-analysis-publication-receipt-v1"
)
RECEIPT_PATH = RECEIPT_ROOT / "receipt.json"
EXPECTED_RECEIPT_SHA256 = (
    "82467dcbf25776fff249500f229146ae3352fc9b61a17dbac86d96f588071336"
)
PUBLICATION_COMMIT = "d1e7574280bf0122cbecbb5b64ff2c66c0851907"
MAIN_COMMIT_AT_RECEIPT = "15cf36b3a38c3f68cc055bf0992f19aca0d9cb48"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_publication_receipt_is_content_addressed() -> None:
    assert RECEIPT_PATH.is_file()
    assert _sha256(RECEIPT_PATH) == EXPECTED_RECEIPT_SHA256
    assert (RECEIPT_ROOT / "SHA256SUMS").read_text(encoding="utf-8") == (
        f"{EXPECTED_RECEIPT_SHA256}  receipt.json\n"
    )


def test_publication_receipt_binds_successful_remote_action() -> None:
    receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))

    assert receipt["schema_version"] == 1
    assert receipt["receipt_id"] == (
        "stage3b-matched-descriptive-analysis-publication-receipt-v1"
    )
    assert receipt["status"] == "publication_action_complete"

    action = receipt["publication_action"]
    assert action["tag"] == (
        "stage3b-matched-descriptive-analysis-publication-v1"
    )
    assert action["commit"] == PUBLICATION_COMMIT
    assert action["commit_is_ancestor_of_main"] is True
    assert action["main_commit_at_receipt"] == MAIN_COMMIT_AT_RECEIPT

    run = receipt["workflow_run"]
    assert run["database_id"] == 29955946081
    assert run["status"] == "completed"
    assert run["conclusion"] == "success"
    assert run["head_sha"] == PUBLICATION_COMMIT
    assert len(run["artifacts"]) == 1
    assert run["artifacts"][0]["expired"] is False

    release = receipt["release"]
    assert release["id"] == 357542590
    assert release["tag"] == "stage3b-matched-profiling-evidence-v1"
    assert release["draft"] is False
    assert release["immutable"] is False
    assert release["prerelease"] is False
    assert release["published_at"] == "2026-07-22T21:02:17Z"

    required_assets = {
        "PUBLICATION-MANIFEST.json",
        "PUBLICATION-SHA256SUMS",
        "stage3b-matched-descriptive-analysis-audit-seal-v1.tar.gz",
        "stage3b-matched-descriptive-analysis-sealed-output-v1.tar.gz",
    }
    observed_assets = {asset["name"] for asset in release["assets"]}
    assert required_assets <= observed_assets


def test_publication_receipt_preserves_closed_research_boundaries() -> None:
    receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
    boundary = receipt["claim_boundary"]

    assert boundary == {
        "ex_if0_opened": False,
        "full_stage3b_campaign_complete": False,
        "policy_activation_permitted": False,
        "release_publication_complete": True,
        "release_publication_permitted": True,
        "results_publication_permitted": True,
        "superiority_claim_permitted": False,
        "test_dataset_access": False,
    }


def test_status_documents_match_publication_receipt_boundary() -> None:
    expected = {
        "matched_profiling_analysis_publication_action_complete=true",
        "matched_profiling_analysis_publication_receipt_frozen=true",
        "results_publication_permitted=true",
        "release_draft_required=false",
        "release_publication_permitted=true",
        "release_publication_complete=true",
        "recursive_aggregate_execution_open=false",
        "full_stage3b_campaign_complete=false",
    }

    for name in ("STATUS.md", "STATUS_EN.md", "ROADMAP.md", "ROADMAP_EN.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        for line in expected:
            assert line in text, f"{name} is missing {line}"
        assert "ex_if0_protocol_frozen=true" in text
        assert "ex_if0_opened=true" in text
        assert "ex_if0_complete=true" in text
        assert "exact_implementation_candidate=stage2_baseline" in text
        assert "minimum_sufficient_sweep_rule_frozen=true" in text
        assert "ex_if0_execution_permitted=false" in text
        assert "oracle_label_generation_open=false" in text
