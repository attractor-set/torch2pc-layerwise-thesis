from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import cast

import pytest

from torch2pc_thesis import stage3b_matched_profiling as matched

ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = ROOT / "experiments/frozen/stage3b-matched-profiling-v2"
MANIFEST_PATH = PACKAGE_ROOT / "manifest.json"
REQUEST_PATH = PACKAGE_ROOT / "request.json"
SHA256SUMS_PATH = PACKAGE_ROOT / "SHA256SUMS"
HISTORICAL_REQUEST = ROOT / (
    "experiments/planned/STAGE3B-B1-B2-MATCHED-PROFILING-REQUEST.json"
)
HISTORICAL_MANIFEST = ROOT / (
    "experiments/planned/STAGE3B-B1-B2-MATCHED-PROFILING-MANIFEST.json"
)

MANIFEST_SHA256 = "372881bd1f7df91e93a9b14ceb2e7642fe256b88637dca024fd8e6b9f66438fd"
REQUEST_SHA256 = "199339566ae5d5d7d45a471187d0ccb81c3e018c0a3c4ebb7f18f03775b3944c"
HISTORICAL_REQUEST_SHA256 = (
    "7c23c9ced5c838e7c3a2ad539d6a5839e986b79ca84ab9c16b14fecfaf819f5e"
)
HISTORICAL_MANIFEST_SHA256 = (
    "6950470b4188b8c85226649ec631c739eef9cb8a8ef0b3410a82fb0a5106b79d"
)


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return cast(dict[str, object], value)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_refrozen_package_has_exact_file_set_and_checksums() -> None:
    assert sorted(path.name for path in PACKAGE_ROOT.iterdir()) == [
        "SHA256SUMS",
        "manifest.json",
        "request.json",
    ]
    assert _sha256(MANIFEST_PATH) == MANIFEST_SHA256
    assert _sha256(REQUEST_PATH) == REQUEST_SHA256
    assert SHA256SUMS_PATH.read_text(encoding="utf-8").splitlines() == [
        f"{MANIFEST_SHA256}  manifest.json",
        f"{REQUEST_SHA256}  request.json",
    ]


def test_historical_v1_opening_remains_byte_identical() -> None:
    assert _sha256(HISTORICAL_REQUEST) == HISTORICAL_REQUEST_SHA256
    assert _sha256(HISTORICAL_MANIFEST) == HISTORICAL_MANIFEST_SHA256


def test_refrozen_manifest_and_request_are_valid_and_closed() -> None:
    manifest = _load(MANIFEST_PATH)
    request = _load(REQUEST_PATH)

    matched.validate_matched_manifest(manifest)
    matched.validate_matched_request(request)
    gate = matched.validate_matched_prelaunch_scientific_gate(
        manifest,
        request,
        project_root=ROOT,
    )

    assert manifest["manifest_id"] == (
        "stage3b-b1-b2-matched-profiling-manifest-v2"
    )
    assert manifest["selected_cell_count"] == 288
    assert manifest["refreeze_version"] == 2
    assert manifest["execution_performed"] is False
    assert manifest["evidence"] is False

    assert request["request_id"] == (
        "stage3b-b1-b2-matched-profiling-request-v2"
    )
    assert request["refreeze_version"] == 2
    assert request["scientific_admission"] == "open"
    assert request["matched_profiling_request_refrozen"] is True
    assert request["matched_profiling_execution_open"] is False
    assert request["runtime_authorization"] == "not_issued"
    assert request["measurements_allowed"] is False
    assert request["execution_performed"] is False
    assert request["evidence"] is False
    assert request["test_dataset_access"] is False

    prerequisites = cast(
        list[dict[str, object]],
        request["prerequisite_decisions"],
    )
    assert matched.decision_ids(prerequisites) == ("EQ-B1", "EQ-B2")
    assert all(record["scope"] == "confirmatory" for record in prerequisites)
    assert all(record["sealed"] is True for record in prerequisites)
    assert all(
        record["confirmatory_equivalence_executed"] is True
        for record in prerequisites
    )

    historical = cast(dict[str, object], request["historical_opening"])
    assert historical["retrospective_admission"] is False
    assert gate == {
        "status": "pass",
        "confirmatory_equivalence": True,
        "exact_counterbalance": True,
        "b1_pairs": 120,
        "b2_triples": 120,
        "b2_comparisons": 240,
    }


def test_refrozen_package_is_reproducible(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        matched,
        "require_opening_base_ancestor",
        lambda _root: None,
    )
    base_manifest_path = ROOT / "experiments/planned/STAGE3B-EXECUTION-MANIFEST.json"
    b1_contract_path = ROOT / "experiments/planned/STAGE3B-B1-CONTRACT.json"
    b2_contract_path = ROOT / "experiments/planned/STAGE3B-B2-CONTRACT.json"
    b1_admission_path = ROOT / (
        "results/stage-3/b1/stage3b-b1-confirmatory-ceebdce-v1/"
        "matched-profiling-admission.json"
    )
    b2_admission_path = ROOT / (
        "results/stage-3/b2/stage3b-b2-confirmatory-63885e5-v1/"
        "matched-profiling-admission.json"
    )

    base_manifest = matched.load_json_object(base_manifest_path)
    b1_contract = matched.load_json_object(b1_contract_path)
    b2_contract = matched.load_json_object(b2_contract_path)
    b1_admission = matched.load_json_object(b1_admission_path)
    b2_admission = matched.load_json_object(b2_admission_path)

    generated_manifest = matched.build_matched_manifest(
        base_manifest,
        b1_contract,
        b2_contract,
    )
    generated_request = matched.build_matched_request(
        project_root=ROOT,
        base_manifest_path=base_manifest_path,
        b1_contract_path=b1_contract_path,
        b2_contract_path=b2_contract_path,
        b1_decision_path=b1_admission_path,
        b2_decision_path=b2_admission_path,
        matched_manifest_path=MANIFEST_PATH,
        historical_request_path=HISTORICAL_REQUEST,
        historical_manifest_path=HISTORICAL_MANIFEST,
        base_manifest=base_manifest,
        b1_contract=b1_contract,
        b2_contract=b2_contract,
        b1_decision=b1_admission,
        b2_decision=b2_admission,
        matched_manifest=generated_manifest,
    )

    assert generated_manifest == _load(MANIFEST_PATH)
    assert generated_request == _load(REQUEST_PATH)


def test_status_and_roadmap_record_refreeze_but_keep_execution_closed() -> None:
    for name in ("STATUS.md", "STATUS_EN.md", "ROADMAP.md", "ROADMAP_EN.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "scientific_admission=open" in text
        assert "matched_profiling_request_refrozen=true" in text
        assert "matched_profiling_request_refresh_required=false" in text
        assert "matched_profiling_execution_complete=true" in text
        assert "matched_profiling_evidence=sealed" in text
        assert "matched_profiling_analysis_open=false" in text
        assert "runtime_authorization=issued_consumed" in text
        assert "measurements_allowed=false" in text
        assert "results_publication_permitted=true" in text
        assert "release_draft_required=false" in text
        assert "release_publication_permitted=true" in text
        assert "release_publication_complete=true" in text
        assert (
            "matched_profiling_analysis_publication_receipt_frozen=true"
            in text
        )
        assert "ex_if0_opened=false" in text
        assert "recursive_aggregate_execution_open=false" in text
