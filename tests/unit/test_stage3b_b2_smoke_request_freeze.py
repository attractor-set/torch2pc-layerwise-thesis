from __future__ import annotations

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
REQUEST_ROOT = (
    ROOT
    / "experiments/frozen/"
    "stage3b-b2-smoke-confirmatory-b1-v1"
)
REQUEST_PATH = REQUEST_ROOT / "request.json"
SHA256SUMS_PATH = REQUEST_ROOT / "SHA256SUMS"

SOURCE_COMMIT = "c6c17d8c96981605471293fc28ba417b5c56595b"
IMAGE_TAG = "torch2pc-layerwise-thesis:b2-opening-c6c17d8c9698"
IMAGE_DIGEST = (
    "9a9af377d417fac9c1e3411b5b18672e7d074596b183f2fdd75d7996cac0a106"
)
IMAGE_CREATED_AT = "2026-07-20T11:06:36.372742218-03:00"
IMPLEMENTATION_CONTRACT_SHA256 = (
    "883f509d73d90995cbb6dc3cc9036a1d499aab3e3d594897a7bbb32f3c8bea05"
)


def test_frozen_confirmatory_b1_request_is_valid_and_complete() -> None:
    payload = load_and_validate_request(REQUEST_PATH)

    assert payload["request_id"] == "stage3b-b2-smoke-confirmatory-b1-v1"
    assert (
        payload["attempt_id"]
        == "stage3b-b2-smoke-confirmatory-b1-attempt-001"
    )
    assert payload["b1_evidence_commit"] == B1_EVIDENCE_COMMIT
    assert payload["execution_source_commit"] == SOURCE_COMMIT
    assert payload["source_image_tag"] == IMAGE_TAG
    assert payload["source_image_digest"] == IMAGE_DIGEST
    assert payload["source_image_created_at"] == IMAGE_CREATED_AT
    assert payload["b1_confirmatory_decision"] == {
        "path": B1_CONFIRMATORY_DECISION_PATH,
        "sha256": B1_CONFIRMATORY_DECISION_SHA256,
    }
    assert payload["b1_admission"] == {
        "path": B1_ADMISSION_PATH,
        "sha256": B1_ADMISSION_SHA256,
    }
    assert (
        payload["b2_implementation_contract"]["sha256"]
        == IMPLEMENTATION_CONTRACT_SHA256
    )
    assert "b1_decision" not in payload
    assert "b1_decision_commit" not in payload

    resolved = payload["resolved_config"]
    assert resolved["execution_source_commit"] == SOURCE_COMMIT
    assert resolved["execution_branch_base"] == SOURCE_COMMIT
    assert resolved["b1_evidence_commit"] == B1_EVIDENCE_COMMIT
    assert resolved["source_image_tag"] == IMAGE_TAG
    assert resolved["source_image_digest"] == IMAGE_DIGEST
    assert resolved["source_image_created_at"] == IMAGE_CREATED_AT
    assert payload["resolved_config_digest"] == canonical_json_digest(resolved)

    contracts = resolved["contracts"]
    assert "b1_decision" not in contracts
    assert contracts["b1_confirmatory_decision"] == {
        "path": B1_CONFIRMATORY_DECISION_PATH,
        "sha256": B1_CONFIRMATORY_DECISION_SHA256,
    }
    assert contracts["b1_admission"] == {
        "path": B1_ADMISSION_PATH,
        "sha256": B1_ADMISSION_SHA256,
    }
    assert (
        contracts["b2_implementation_contract"]["sha256"]
        == IMPLEMENTATION_CONTRACT_SHA256
    )

    specs = build_pair_specs(payload)
    assert len(specs) == 12
    assert len({spec.pair_id for spec in specs}) == 12


def test_frozen_request_checksum_registry_is_exact() -> None:
    fields = SHA256SUMS_PATH.read_text(encoding="utf-8").strip().split()

    assert fields == [sha256_file(REQUEST_PATH), "request.json"]


def test_frozen_request_json_has_no_duplicate_keys() -> None:
    def reject_duplicate_keys(
        pairs: list[tuple[str, object]],
    ) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    json.loads(
        REQUEST_PATH.read_text(encoding="utf-8"),
        object_pairs_hook=reject_duplicate_keys,
    )
