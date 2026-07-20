from __future__ import annotations

import copy
import json
from pathlib import Path

from torch2pc_thesis.stage3b_b1_equivalence import (
    canonical_json_digest,
    sha256_file,
)
from torch2pc_thesis.stage3b_b2_smoke import (
    B1_ADMISSION_PATH,
    B1_ADMISSION_SHA256,
    B1_CONFIRMATORY_DECISION_PATH,
    B1_CONFIRMATORY_DECISION_SHA256,
    B1_EVIDENCE_COMMIT,
    build_pair_specs,
    load_and_validate_request,
)

ROOT = Path(__file__).resolve().parents[2]
V1_ROOT = ROOT / "experiments/frozen/stage3b-b2-smoke-confirmatory-b1-v1"
V2_ROOT = ROOT / "experiments/frozen/stage3b-b2-smoke-confirmatory-b1-v2"
V1_REQUEST_PATH = V1_ROOT / "request.json"
V2_REQUEST_PATH = V2_ROOT / "request.json"
SUPERSESSION_PATH = V2_ROOT / "supersession.json"
SHA256SUMS_PATH = V2_ROOT / "SHA256SUMS"

SOURCE_COMMIT = "c6c17d8c96981605471293fc28ba417b5c56595b"
V1_REQUEST_SHA256 = "e26e017afba6c04531c41d0065d11e4c51642d7dbde31fde084ce8bfbe6a20ec"
V1_IMAGE_TAG = "torch2pc-layerwise-thesis:b2-opening-c6c17d8c9698"
V1_IMAGE_DIGEST = "9a9af377d417fac9c1e3411b5b18672e7d074596b183f2fdd75d7996cac0a106"
V1_IMAGE_REVISION = "b55c37eb64d0659543bdd2294ddacb72f987b8d7"
V2_IMAGE_TAG = "torch2pc-layerwise-thesis:b2-opening-c6c17d8c9698-provenance-v2"
V2_IMAGE_DIGEST = "311f438035d379847ad9e036b70b79becd5d23b09b949e6f5fade895b303d186"
V2_IMAGE_CREATED_AT = "2026-07-20T12:01:29.526591173-03:00"
V2_REQUEST_SHA256 = "01048bb8c0b076a8674bddca595471ee9c5cb3a4ada69fabebd8d50a35a183ef"
SUPERSESSION_SHA256 = "ec2368bcbde5846ccadd6669b8b78681321c4d7b1cfd741bdc63f575ce77f715"
IMPLEMENTATION_CONTRACT_SHA256 = "883f509d73d90995cbb6dc3cc9036a1d499aab3e3d594897a7bbb32f3c8bea05"


def test_v1_request_is_retained_unchanged() -> None:
    assert sha256_file(V1_REQUEST_PATH) == V1_REQUEST_SHA256


def test_v2_request_is_valid_complete_and_bound_to_corrected_image() -> None:
    payload = load_and_validate_request(V2_REQUEST_PATH)

    assert sha256_file(V2_REQUEST_PATH) == V2_REQUEST_SHA256
    assert payload["request_id"] == "stage3b-b2-smoke-confirmatory-b1-v2"
    assert payload["attempt_id"] == "stage3b-b2-smoke-confirmatory-b1-attempt-002"
    assert payload["b1_evidence_commit"] == B1_EVIDENCE_COMMIT
    assert payload["execution_source_commit"] == SOURCE_COMMIT
    assert payload["source_image_tag"] == V2_IMAGE_TAG
    assert payload["source_image_digest"] == V2_IMAGE_DIGEST
    assert payload["source_image_created_at"] == V2_IMAGE_CREATED_AT
    assert payload["b1_confirmatory_decision"] == {
        "path": B1_CONFIRMATORY_DECISION_PATH,
        "sha256": B1_CONFIRMATORY_DECISION_SHA256,
    }
    assert payload["b1_admission"] == {
        "path": B1_ADMISSION_PATH,
        "sha256": B1_ADMISSION_SHA256,
    }
    assert payload["b2_implementation_contract"]["sha256"] == IMPLEMENTATION_CONTRACT_SHA256

    resolved = payload["resolved_config"]
    assert resolved["resolution_id"] == ("stage3b-b2-smoke-confirmatory-b1-resolved-v2")
    assert resolved["execution_source_commit"] == SOURCE_COMMIT
    assert resolved["execution_branch_base"] == SOURCE_COMMIT
    assert resolved["b1_evidence_commit"] == B1_EVIDENCE_COMMIT
    assert resolved["source_image_tag"] == V2_IMAGE_TAG
    assert resolved["source_image_digest"] == V2_IMAGE_DIGEST
    assert resolved["source_image_created_at"] == V2_IMAGE_CREATED_AT
    assert payload["resolved_config_digest"] == canonical_json_digest(resolved)

    specs = build_pair_specs(payload)
    assert len(specs) == 12
    assert len({spec.pair_id for spec in specs}) == 12


def test_v2_request_changes_only_registered_replacement_fields() -> None:
    v1 = json.loads(V1_REQUEST_PATH.read_text(encoding="utf-8"))
    v2 = json.loads(V2_REQUEST_PATH.read_text(encoding="utf-8"))

    normalized = copy.deepcopy(v2)
    normalized["request_id"] = v1["request_id"]
    normalized["attempt_id"] = v1["attempt_id"]
    normalized["source_image_tag"] = v1["source_image_tag"]
    normalized["source_image_digest"] = v1["source_image_digest"]
    normalized["source_image_created_at"] = v1["source_image_created_at"]
    normalized["resolved_config_digest"] = v1["resolved_config_digest"]

    normalized_resolved = normalized["resolved_config"]
    v1_resolved = v1["resolved_config"]
    normalized_resolved["resolution_id"] = v1_resolved["resolution_id"]
    normalized_resolved["source_image_tag"] = v1_resolved["source_image_tag"]
    normalized_resolved["source_image_digest"] = v1_resolved["source_image_digest"]
    normalized_resolved["source_image_created_at"] = v1_resolved["source_image_created_at"]

    assert normalized == v1


def test_supersession_record_documents_pre_execution_failure() -> None:
    payload = json.loads(SUPERSESSION_PATH.read_text(encoding="utf-8"))

    assert payload["record_type"] == "pre_execution_request_supersession"
    assert payload["status"] == "superseded_before_execution"
    assert payload["reason"] == {
        "classification": "infrastructure_failure",
        "code": "source_image_revision_mismatch",
        "detected_by": "pre_execution_fail_closed_gate",
        "preregistered_requirement": "source_image_revision_match_required",
        "expected_revision": SOURCE_COMMIT,
        "observed_revision": V1_IMAGE_REVISION,
        "environment_source_git_commit": V1_IMAGE_REVISION,
    }
    assert payload["execution_state"] == {
        "runner_execute_invoked": False,
        "attempt_root_created": False,
        "scientific_measurements_created": False,
    }

    superseded = payload["superseded_request"]
    assert superseded["sha256"] == sha256_file(V1_REQUEST_PATH)
    assert superseded["source_image_tag"] == V1_IMAGE_TAG
    assert superseded["source_image_digest"] == V1_IMAGE_DIGEST

    replacement = payload["replacement_request"]
    assert replacement["sha256"] == V2_REQUEST_SHA256
    assert replacement["source_image_tag"] == V2_IMAGE_TAG
    assert replacement["source_image_digest"] == V2_IMAGE_DIGEST
    assert replacement["source_image_revision"] == SOURCE_COMMIT
    assert replacement["source_image_created_at"] == V2_IMAGE_CREATED_AT

    assert payload["retention_policy"] == {
        "superseded_request_retained_unchanged": True,
        "new_attempt_id_required": True,
        "append_only": True,
    }


def test_v2_checksum_registry_is_exact() -> None:
    assert sha256_file(SUPERSESSION_PATH) == SUPERSESSION_SHA256

    fields = SHA256SUMS_PATH.read_text(encoding="utf-8").splitlines()

    assert fields == [
        f"{V2_REQUEST_SHA256}  request.json",
        f"{SUPERSESSION_SHA256}  supersession.json",
    ]


def test_v2_json_files_have_no_duplicate_keys() -> None:
    def reject_duplicate_keys(
        pairs: list[tuple[str, object]],
    ) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    for path in (V2_REQUEST_PATH, SUPERSESSION_PATH):
        json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=reject_duplicate_keys,
        )
