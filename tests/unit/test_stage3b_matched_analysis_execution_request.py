from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from torch2pc_thesis.stage3b_matched_analysis import (
    EXPECTED_OUTPUT_NAMES,
    Stage3BMatchedAnalysisError,
    generate_matched_analysis,
)
from torch2pc_thesis.stage3b_matched_analysis_execution_request import (
    ANALYSIS_MODULE_RELATIVE,
    EXPECTED_ANALYSIS_MODULE_SHA256,
    EXPECTED_PROTOCOL_REGISTRY_SHA256,
    EXPECTED_PROTOCOL_SHA256,
    OUTPUT_ROOT_RELATIVE,
    REQUEST_BASE_COMMIT,
    REQUEST_ID,
    REQUEST_ROOT_RELATIVE,
    Stage3BMatchedAnalysisExecutionRequestError,
    build_execution_request,
    canonical_json_digest,
    sha256_file,
    validate_execution_request,
    write_execution_request_package,
)

ROOT = Path(__file__).resolve().parents[2]
REQUEST_ROOT = ROOT / REQUEST_ROOT_RELATIVE


def _load_request() -> dict[str, object]:
    value = json.loads(
        (REQUEST_ROOT / "request.json").read_text(encoding="utf-8")
    )
    assert isinstance(value, dict)
    return value


def _keys(value: object) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, nested in value.items():
            found.add(str(key))
            found.update(_keys(nested))
    elif isinstance(value, list):
        for nested in value:
            found.update(_keys(nested))
    return found


def _mapping(value: Any) -> dict[str, Any]:
    assert isinstance(value, dict)
    return value


def test_frozen_execution_request_rebuilds_exactly() -> None:
    request = _load_request()

    validate_execution_request(request, ROOT)
    assert request == build_execution_request(ROOT)
    assert request["request_id"] == REQUEST_ID

    request_without_digest = dict(request)
    digest = request_without_digest.pop("request_digest")
    assert digest == canonical_json_digest(request_without_digest)

    registry = (REQUEST_ROOT / "SHA256SUMS").read_text(
        encoding="utf-8"
    )
    expected_request_sha = hashlib.sha256(
        (REQUEST_ROOT / "request.json").read_bytes()
    ).hexdigest()
    assert registry == f"{expected_request_sha}  request.json\n"


def test_request_package_check_and_clean_rebuild(tmp_path: Path) -> None:
    write_execution_request_package(ROOT, REQUEST_ROOT, check=True)

    output_root = tmp_path / "frozen"
    rebuilt = write_execution_request_package(ROOT, output_root)

    assert rebuilt == _load_request()
    assert (output_root / "request.json").read_bytes() == (
        REQUEST_ROOT / "request.json"
    ).read_bytes()
    assert (output_root / "SHA256SUMS").read_bytes() == (
        REQUEST_ROOT / "SHA256SUMS"
    ).read_bytes()


def test_request_freezes_identity_without_authorization() -> None:
    request = _load_request()
    boundary = _mapping(request["claim_boundary"])
    protocol = _mapping(request["protocol"])
    implementation = _mapping(request["implementation"])

    assert request["request_base_commit"] == REQUEST_BASE_COMMIT
    assert boundary["execution_request_frozen"] is True
    assert boundary["execution_authorization_present"] is False
    assert boundary["analysis_execution_permitted"] is False
    assert boundary["analysis_execution_performed"] is False
    assert boundary["analysis_results_present"] is False
    assert boundary["request_builder_uses_observed_metric_values"] is False
    assert boundary["results_publication_permitted"] is False
    assert boundary["release_publication_permitted"] is False
    assert boundary["test_dataset_access"] is False

    assert protocol["sha256"] == EXPECTED_PROTOCOL_SHA256
    assert (
        protocol["registry_sha256"]
        == EXPECTED_PROTOCOL_REGISTRY_SHA256
    )
    analysis_module = _mapping(implementation["analysis_module"])
    assert analysis_module["path"] == ANALYSIS_MODULE_RELATIVE.as_posix()
    assert analysis_module["sha256"] == EXPECTED_ANALYSIS_MODULE_SHA256
    assert sha256_file(ROOT / ANALYSIS_MODULE_RELATIVE) == (
        EXPECTED_ANALYSIS_MODULE_SHA256
    )


def test_request_freezes_single_output_root_and_exact_inventory() -> None:
    request = _load_request()
    execution = _mapping(request["requested_execution"])
    output = _mapping(request["output_contract"])

    assert execution["mode"] == "single_authorized_read_only_run"
    assert execution["maximum_execution_count"] == 1
    assert execution["authorization_status"] == "not_issued"
    assert execution["authorization_required"] is True
    assert execution["dry_run_must_not_compute_metric_values"] is True

    assert output["root"] == OUTPUT_ROOT_RELATIVE.as_posix()
    assert output["root_policy"] == (
        "must_not_exist_before_authorized_execution"
    )
    assert output["expected_top_level_file_count"] == 18
    assert output["expected_top_level_files"] == list(
        EXPECTED_OUTPUT_NAMES
    )
    assert output["results_publication_permitted"] is False


def test_request_binds_exact_sealed_evidence_without_results() -> None:
    request = _load_request()
    source = _mapping(request["source_evidence"])

    assert source["access_mode"] == "read_only"
    assert source["release_tag"] == (
        "stage3b-matched-profiling-evidence-v1"
    )
    expected_sha = _mapping(source["expected_sha256"])
    assert len(expected_sha) == 9
    assert expected_sha["profiling_cells.csv"] == (
        "91f5bf665778f2edefbcdcfa9572df771b1288274e902123e303b59c71733373"
    )
    assert expected_sha["locality_events.jsonl.zst"] == (
        "59a1479d66f170970b4d0f2b0712b8a825ccca01eab677c887a9046fc4c16f76"
    )

    forbidden = {
        "observed_speedup",
        "observed_median",
        "winner",
        "selected_candidate",
        "candidate_decisions",
        "engineering_decision",
        "p_value",
        "confidence_interval",
    }
    assert _keys(request).isdisjoint(forbidden)


def test_sealed_evidence_execution_remains_closed(tmp_path: Path) -> None:
    with pytest.raises(
        Stage3BMatchedAnalysisError,
        match="execution is closed",
    ):
        generate_matched_analysis(
            tmp_path / "sealed-evidence",
            tmp_path / "analysis-output",
            generated_at_utc="2026-07-21T00:00:00Z",
        )


def test_request_validation_rejects_authorization_tampering() -> None:
    request = _load_request()
    tampered = json.loads(json.dumps(request))
    tampered["claim_boundary"]["analysis_execution_permitted"] = True

    with pytest.raises(
        Stage3BMatchedAnalysisExecutionRequestError,
        match="differs from deterministic builder",
    ):
        validate_execution_request(tampered, ROOT)
