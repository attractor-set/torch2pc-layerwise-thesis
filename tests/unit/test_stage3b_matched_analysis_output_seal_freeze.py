from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from torch2pc_thesis.stage3b_matched_analysis import (
    EXPECTED_OUTPUT_NAMES,
    validate_generated_analysis_output,
)

ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = ROOT / (
    "results/stage-3/analysis/matched/"
    "stage3b-matched-descriptive-analysis-70d6c3c-v1"
)
AUDIT_ROOT = ROOT / (
    "experiments/frozen/"
    "stage3b-matched-descriptive-analysis-output-audit-v1"
)
SEAL_ROOT = ROOT / (
    "experiments/frozen/"
    "stage3b-matched-descriptive-analysis-output-seal-v1"
)

EXPECTED_OUTPUT_REGISTRY_SHA256 = (
    "8baa1b55c21ed2b00bd849bbbe4f415d8b5f86d70bd9989d4ec4917765ead1da"
)
EXPECTED_METADATA_SHA256 = (
    "e2e81f00c1e6d21e9740ecf5c9d2389bdd31e1fd7929f5b6bda4b49ccada3a8b"
)
EXPECTED_SUMMARY_SHA256 = (
    "4f02d8f0297e3ced79110487d6837308f2da2de704083ce2be73f01c43a28f3a"
)
EXPECTED_DECISION_SHA256 = (
    "3ccd65cf86dbb26a306bcd97bba60bf9851fd7d4f20af3340d6795fb19ea3199"
)
EXPECTED_RECEIPT_SHA256 = (
    "997569220aa89261e0d375a70597bb8325186f1739a7977e3a211fce1ffcf8b2"
)
EXPECTED_AUDIT_SHA256 = (
    "a2bfbfc8f57cc681b535e8a8ab0e722fd745f49df9eab8094a6e70e8adb88123"
)
EXPECTED_AUDIT_REGISTRY_SHA256 = (
    "c7984a0559c8ee2c902583abd547dec84f23116b679cdf6cfae665ca167d00c6"
)
EXPECTED_SEAL_DIGEST = "dbb8983bd77490ca4feedc035ae31ca4cdd0764ecd89dab1b0c3d91aed0ad3cd"
EXPECTED_SEAL_SHA256 = "0558079a6757c84a58f76cdee8cbf6c3e302423c49b6eed34f365183d2977872"


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _digest(value: dict[str, Any]) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _registry(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        digest, name = line.split(maxsplit=1)
        result[name.removeprefix("*")] = digest
    return result


def test_exact_output_remains_the_registered_unsealed_package() -> None:
    assert sorted(path.name for path in OUTPUT_ROOT.iterdir()) == sorted(
        EXPECTED_OUTPUT_NAMES
    )
    assert all(path.is_file() and not path.is_symlink() for path in OUTPUT_ROOT.iterdir())
    assert _sha256(OUTPUT_ROOT / "SHA256SUMS") == EXPECTED_OUTPUT_REGISTRY_SHA256
    assert _sha256(OUTPUT_ROOT / "analysis_metadata.json") == EXPECTED_METADATA_SHA256
    assert _sha256(OUTPUT_ROOT / "analysis_summary.json") == EXPECTED_SUMMARY_SHA256
    assert _sha256(OUTPUT_ROOT / "engineering_decision.json") == EXPECTED_DECISION_SHA256
    validate_generated_analysis_output(OUTPUT_ROOT)
    metadata = _load(OUTPUT_ROOT / "analysis_metadata.json")
    assert metadata["analysis_output_evidence"] is False
    assert not (OUTPUT_ROOT / "seal.json").exists()
    assert not (OUTPUT_ROOT / "SEALED-SHA256SUMS").exists()


def test_output_registry_covers_all_eighteen_files() -> None:
    registry = _registry(OUTPUT_ROOT / "SHA256SUMS")
    assert set(registry) == set(EXPECTED_OUTPUT_NAMES) - {"SHA256SUMS"}
    for name, expected in registry.items():
        assert _sha256(OUTPUT_ROOT / name) == expected


def test_audit_package_is_exact_and_bound_to_output() -> None:
    assert sorted(path.name for path in AUDIT_ROOT.iterdir()) == [
        "OUTPUT-SHA256SUMS",
        "SHA256SUMS",
        "audit.json",
        "execution-receipt.json",
    ]
    assert all(path.is_file() and not path.is_symlink() for path in AUDIT_ROOT.iterdir())
    assert _sha256(AUDIT_ROOT / "audit.json") == EXPECTED_AUDIT_SHA256
    assert _sha256(AUDIT_ROOT / "execution-receipt.json") == EXPECTED_RECEIPT_SHA256
    assert _sha256(AUDIT_ROOT / "OUTPUT-SHA256SUMS") == EXPECTED_OUTPUT_REGISTRY_SHA256
    assert _sha256(AUDIT_ROOT / "SHA256SUMS") == EXPECTED_AUDIT_REGISTRY_SHA256
    assert (AUDIT_ROOT / "OUTPUT-SHA256SUMS").read_bytes() == (
        OUTPUT_ROOT / "SHA256SUMS"
    ).read_bytes()
    for name, expected in _registry(AUDIT_ROOT / "SHA256SUMS").items():
        assert _sha256(AUDIT_ROOT / name) == expected


def test_audit_semantics_remain_unsealed_and_publication_closed() -> None:
    audit = _load(AUDIT_ROOT / "audit.json")
    assert audit["status"] == "independent_audit_passed_output_unsealed"
    assert audit["project_commit"] == "72b95a284e8747a33b8c34d5929d4110aa4bfea1"
    assert audit["execution_receipt_sha256"] == EXPECTED_RECEIPT_SHA256
    assert audit["output_file_count"] == 18
    actual = _registry(OUTPUT_ROOT / "SHA256SUMS")
    actual["SHA256SUMS"] = EXPECTED_OUTPUT_REGISTRY_SHA256
    assert audit["output_sha256"] == dict(sorted(actual.items()))
    for key in (
        "analysis_output_sealed",
        "analysis_output_evidence",
        "results_publication_permitted",
        "release_publication_permitted",
        "superiority_claim_permitted",
        "test_dataset_access",
    ):
        assert audit[key] is False


def test_external_seal_package_identity_and_digest() -> None:
    assert sorted(path.name for path in SEAL_ROOT.iterdir()) == [
        "SHA256SUMS",
        "seal.json",
    ]
    assert all(path.is_file() and not path.is_symlink() for path in SEAL_ROOT.iterdir())
    assert _sha256(SEAL_ROOT / "seal.json") == EXPECTED_SEAL_SHA256
    assert (SEAL_ROOT / "SHA256SUMS").read_text(encoding="utf-8") == (
        f"{EXPECTED_SEAL_SHA256}  seal.json\n"
    )
    seal = _load(SEAL_ROOT / "seal.json")
    unsigned = dict(seal)
    seal_digest = unsigned.pop("seal_digest")
    assert seal_digest == EXPECTED_SEAL_DIGEST
    assert _digest(unsigned) == seal_digest


def test_external_seal_binds_execution_audit_and_output() -> None:
    seal = _load(SEAL_ROOT / "seal.json")
    audit = _load(AUDIT_ROOT / "audit.json")
    assert seal["status"] == "sealed_analysis_output_evidence"
    assert seal["execution_source_commit"] == audit["project_commit"]
    assert seal["request_digest"] == audit["request_digest"]
    assert seal["authorization_digest"] == audit["authorization_digest"]
    assert seal["runtime_preflight_digest"] == audit["runtime_preflight_digest"]
    assert seal["runtime_identity_digest"] == audit["runtime_identity_digest"]
    assert seal["execution_receipt_sha256"] == EXPECTED_RECEIPT_SHA256
    assert seal["audit_record_sha256"] == EXPECTED_AUDIT_SHA256
    assert seal["audit_package_registry_sha256"] == EXPECTED_AUDIT_REGISTRY_SHA256
    assert seal["output_root"] == audit["output_root"]
    assert seal["output_file_count"] == audit["output_file_count"] == 18
    assert seal["output_registry_sha256"] == EXPECTED_OUTPUT_REGISTRY_SHA256
    assert seal["analysis_metadata_sha256"] == EXPECTED_METADATA_SHA256
    assert seal["analysis_summary_sha256"] == EXPECTED_SUMMARY_SHA256
    assert seal["engineering_decision_sha256"] == EXPECTED_DECISION_SHA256


def test_seal_opens_evidence_only_and_keeps_publication_closed() -> None:
    boundary = _load(SEAL_ROOT / "seal.json")["claim_boundary"]
    for key in (
        "analysis_execution_performed",
        "analysis_results_present",
        "analysis_output_audited",
        "analysis_output_sealed",
        "analysis_output_evidence",
    ):
        assert boundary[key] is True
    for key in (
        "results_publication_permitted",
        "release_publication_permitted",
        "superiority_claim_permitted",
        "test_dataset_access",
        "ex_if0_opened",
        "policy_activation_permitted",
    ):
        assert boundary[key] is False
