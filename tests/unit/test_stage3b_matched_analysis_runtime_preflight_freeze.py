from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from torch2pc_thesis.stage3b_matched_analysis_execution_request import (
    canonical_json_digest,
    sha256_file,
)

ROOT = Path(__file__).resolve().parents[2]
FREEZE_ROOT = ROOT / (
    "experiments/frozen/"
    "stage3b-matched-descriptive-analysis-runtime-preflight-v1"
)
PREFLIGHT_PATH = FREEZE_ROOT / "runtime-preflight.json"
EXPECTED_FILE_SHA256 = (
    "1722cce133e047512c2b587c9d8fba15"
    "e95457653afd2fa496f295d3b1bbced0"
)
EXPECTED_SOURCE_COMMIT = "272a9258f70320416ff97c3da076435fd5334bc4"


def _mapping(value: Any) -> dict[str, Any]:
    assert isinstance(value, dict)
    return value


def _load() -> dict[str, Any]:
    value = json.loads(PREFLIGHT_PATH.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_frozen_runtime_preflight_file_and_registry_are_exact() -> None:
    assert sha256_file(PREFLIGHT_PATH) == EXPECTED_FILE_SHA256
    assert (FREEZE_ROOT / "SHA256SUMS").read_text(encoding="utf-8") == (
        f"{EXPECTED_FILE_SHA256}  runtime-preflight.json\n"
    )
    assert set(path.name for path in FREEZE_ROOT.iterdir()) == {
        "runtime-preflight.json",
        "SHA256SUMS",
    }


def test_frozen_runtime_preflight_internal_digests_recompute() -> None:
    preflight = _load()
    payload = dict(preflight)
    digest = payload.pop("preflight_digest")
    assert digest == canonical_json_digest(payload)

    identity = _mapping(preflight["runtime_identity"])
    identity_payload = dict(identity)
    identity_digest = identity_payload.pop("runtime_identity_digest")
    assert identity_digest == canonical_json_digest(identity_payload)


def test_frozen_runtime_preflight_binds_current_files_and_request() -> None:
    preflight = _load()
    identity = _mapping(preflight["runtime_identity"])
    assert identity["source_commit"] == EXPECTED_SOURCE_COMMIT
    assert preflight["request_digest"] == identity["request_digest"]
    assert preflight["request_id"] == identity["request_id"]

    bound = _mapping(identity["bound_files_sha256"])
    assert len(bound) == 11
    for relative, expected in bound.items():
        assert sha256_file(ROOT / relative) == expected


def test_frozen_runtime_preflight_binds_sealed_source_and_output_contract() -> None:
    preflight = _load()
    source = _mapping(preflight["source_evidence"])
    verified = _mapping(source["verified_sha256"])
    evidence_root = ROOT / source["root"]
    assert source["access_mode"] == "read_only"
    assert source["observed_metric_values_read"] is False
    assert source["zstandard_frame_tested"] is True
    assert len(verified) == 9
    for name, expected in verified.items():
        assert sha256_file(evidence_root / name) == expected

    output = _mapping(preflight["output_contract"])
    names = output["expected_top_level_files"]
    assert isinstance(names, list)
    assert output["expected_top_level_file_count"] == 18
    assert len(names) == 18
    assert len(set(names)) == 18
    assert output["root_absent"] is True
    assert not (ROOT / output["root"]).exists()


def test_frozen_runtime_preflight_keeps_execution_closed() -> None:
    preflight = _load()
    boundary = _mapping(preflight["claim_boundary"])
    for key in (
        "runtime_preflight_implemented",
        "runtime_preflight_passed",
        "source_evidence_read_only",
    ):
        assert boundary[key] is True
    for key in (
        "execution_authorization_present",
        "analysis_execution_permitted",
        "analysis_execution_performed",
        "analysis_results_present",
        "results_publication_permitted",
        "release_publication_permitted",
        "observed_metric_values_read",
        "test_dataset_access",
    ):
        assert boundary[key] is False
    assert not (FREEZE_ROOT / "authorization.json").exists()
