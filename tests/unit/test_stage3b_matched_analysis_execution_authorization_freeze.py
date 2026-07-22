from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
AUTH_ROOT = ROOT / (
    "experiments/frozen/"
    "stage3b-matched-descriptive-analysis-execution-authorization-v1"
)
PREFLIGHT_ROOT = ROOT / (
    "experiments/frozen/"
    "stage3b-matched-descriptive-analysis-runtime-preflight-v1"
)
REQUEST_PATH = ROOT / (
    "experiments/frozen/"
    "stage3b-matched-descriptive-analysis-execution-request-v1/request.json"
)
OUTPUT_ROOT = ROOT / (
    "results/stage-3/analysis/matched/"
    "stage3b-matched-descriptive-analysis-70d6c3c-v1"
)

EXPECTED_AUTHORIZATION_SHA256 = (
    "29f48ae7fe4f8ab92c465d939ee68c2142488bf8463f718d76c41361d9c6a76f"
)
EXPECTED_PREFLIGHT_SHA256 = (
    "1722cce133e047512c2b587c9d8fba15e95457653afd2fa496f295d3b1bbced0"
)
EXPECTED_AUTHORIZATION_DIGEST = (
    "5e4f570d81d373637244563afed9d1765fe0d17b3d726db9282b4104c37d83c0"
)
EXPECTED_ACKNOWLEDGEMENT = (
    "AUTHORIZE_STAGE3B_MATCHED_DESCRIPTIVE_ANALYSIS_SINGLE_READ_ONLY_RUN"
)


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_authorization_package_inventory_and_registry() -> None:
    entries = sorted(path.name for path in AUTH_ROOT.iterdir())
    assert entries == ["SHA256SUMS", "authorization.json", "runtime-preflight.json"]
    assert all(path.is_file() and not path.is_symlink() for path in AUTH_ROOT.iterdir())

    expected = (
        f"{EXPECTED_AUTHORIZATION_SHA256}  authorization.json\n"
        f"{EXPECTED_PREFLIGHT_SHA256}  runtime-preflight.json\n"
    )
    assert (AUTH_ROOT / "SHA256SUMS").read_text(encoding="utf-8") == expected
    assert _sha256(AUTH_ROOT / "authorization.json") == EXPECTED_AUTHORIZATION_SHA256
    assert _sha256(AUTH_ROOT / "runtime-preflight.json") == EXPECTED_PREFLIGHT_SHA256


def test_authorization_copy_matches_frozen_preflight() -> None:
    assert (AUTH_ROOT / "runtime-preflight.json").read_bytes() == (
        PREFLIGHT_ROOT / "runtime-preflight.json"
    ).read_bytes()


def test_authorization_digest_and_bindings() -> None:
    authorization = _load(AUTH_ROOT / "authorization.json")
    preflight = _load(AUTH_ROOT / "runtime-preflight.json")
    request = _load(REQUEST_PATH)

    unsigned = dict(authorization)
    authorization_digest = unsigned.pop("authorization_digest")
    assert authorization_digest == EXPECTED_AUTHORIZATION_DIGEST
    assert _digest(unsigned) == authorization_digest

    assert authorization["request_id"] == request["request_id"]
    assert authorization["request_digest"] == request["request_digest"]
    assert authorization["preflight_id"] == preflight["preflight_id"]
    assert authorization["preflight_digest"] == preflight["preflight_digest"]
    assert authorization["runtime_identity_digest"] == preflight["runtime_identity"][
        "runtime_identity_digest"
    ]
    assert authorization["output_root"] == request["output_contract"]["root"]
    assert authorization["output_root"] == preflight["output_contract"]["root"]


def test_authorization_scope_and_closed_claims() -> None:
    authorization = _load(AUTH_ROOT / "authorization.json")
    boundary = authorization["claim_boundary"]

    assert authorization["operator_acknowledgement"] == EXPECTED_ACKNOWLEDGEMENT
    assert authorization["execution_count"] == 1
    assert authorization["authorization_package_must_be_frozen"] is True
    assert authorization["output_root_absent_at_issue"] is True
    assert authorization["source_sha256_verified_at_issue"] is True
    assert authorization["source_sha256_verification_required_after_execution"] is True
    assert authorization["network_access_required"] is False

    assert boundary["execution_authorization_present"] is True
    assert boundary["analysis_execution_permitted"] is True
    assert boundary["analysis_execution_performed"] is False
    assert boundary["analysis_results_present"] is False
    assert boundary["results_publication_permitted"] is False
    assert boundary["release_publication_permitted"] is False
    assert boundary["test_dataset_access"] is False


def test_authorization_freeze_does_not_contain_results() -> None:
    assert not OUTPUT_ROOT.exists()
