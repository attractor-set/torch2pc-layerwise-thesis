# Validate the QW-LC0 post-merge transition receipt.

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[2]
TRANSITION = ROOT / (
    "experiments/frozen/"
    "stage3b-qwake-fp-runtime-validation-post-merge-v2"
)
OUTPUT = ROOT / (
    "results/stage-3/"
    "qwake-fp-runtime-validation-v2-attempt-001"
)
AUDIT = ROOT / (
    "experiments/frozen/"
    "stage3b-qwake-fp-runtime-validation-evidence-v2"
)
SEAL = ROOT / (
    "experiments/frozen/"
    "stage3b-qwake-fp-runtime-validation-output-seal-v2"
)

MAIN_COMMIT = "4f23b752a40ae05de9fc7ee49c9962c44083b71d"
SEAL_COMMIT = "26bc0ef635e13dba719d3356fe17382f0037d1df"
SEAL_PARENT = "c96a5f17265a522f60ccb9bd0dcd2184378d1b2a"
REPORT_SHA256 = "sha256:54dba01d47814dc00fa53bd69c00865bd1c47754c017c7482c895162d3a86b82"
AUDIT_REGISTRY_SHA256 = "sha256:904f128a7db6cb8bf7f641bf1dcd8e6f3004884a16c90b21772248e3cb80852f"
AUDIT_MANIFEST_SHA256 = "sha256:2e4d1e7ff0a5d8702350e8f83eb1c671c9f23ee4abe85fc81cc1932e65aa2fa2"
ADJUDICATION_SHA256 = "sha256:8bfc1e5a4d7ba736e09dcc712334a55e9b83b4145edbc069d00eaba5e589c8f8"
SEAL_SHA256 = "sha256:38fff1dee19874fb7d01163a8355672473ba6ad890029ccfd3cf0c5218987cc4"
SEAL_REGISTRY_SHA256 = "sha256:e4ff3a5811863a2a8a34d3d86316ad84a5de0e4f5f5852949ae8e006704814c2"
RECEIPT_FILE_SHA256 = "2f0833b3395c4499aece489ba7aadb3003e27f6c2b86fb00d08179d54d2721e9"


def _sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def _json(path: Path) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        json.loads(path.read_text(encoding="utf-8")),
    )


def test_transition_package_inventory_and_checksum() -> None:
    assert sorted(path.name for path in TRANSITION.iterdir()) == [
        "SHA256SUMS",
        "receipt.json",
    ]
    receipt = TRANSITION / "receipt.json"
    assert _sha(receipt) == "sha256:" + RECEIPT_FILE_SHA256
    registry = (
        TRANSITION / "SHA256SUMS"
    ).read_text(encoding="utf-8")
    assert registry == RECEIPT_FILE_SHA256 + "  receipt.json\n"


def test_receipt_binds_merge_and_immutable_evidence() -> None:
    receipt = _json(TRANSITION / "receipt.json")
    assert receipt["status"] == (
        "repository_evidence_verified_on_main_"
        "qw_lc0_transition_open"
    )
    assert receipt["pr_number"] == 110
    assert receipt["merge_method"] == "merge-commit"
    assert receipt["main_commit"] == MAIN_COMMIT
    assert receipt["main_first_parent"] == SEAL_PARENT
    assert receipt["seal_commit"] == SEAL_COMMIT
    assert receipt["runtime_report_sha256"] == REPORT_SHA256
    assert (
        receipt["audit_package_registry_sha256"]
        == AUDIT_REGISTRY_SHA256
    )
    assert (
        receipt["audit_manifest_sha256"]
        == AUDIT_MANIFEST_SHA256
    )
    assert (
        receipt["adjudication_v3_sha256"]
        == ADJUDICATION_SHA256
    )
    assert receipt["seal_sha256"] == SEAL_SHA256
    assert (
        receipt["seal_registry_sha256"]
        == SEAL_REGISTRY_SHA256
    )

    assert _sha(
        OUTPUT / "runtime-validation-report.json"
    ) == REPORT_SHA256
    assert _sha(
        AUDIT / "SHA256SUMS"
    ) == AUDIT_REGISTRY_SHA256
    assert _sha(
        AUDIT / "manifest.json"
    ) == AUDIT_MANIFEST_SHA256
    assert _sha(
        AUDIT / "post-execution-adjudication-v3.json"
    ) == ADJUDICATION_SHA256
    assert _sha(SEAL / "seal.json") == SEAL_SHA256
    assert _sha(
        SEAL / "SHA256SUMS"
    ) == SEAL_REGISTRY_SHA256


def test_transition_opens_only_qw_lc0_documentation() -> None:
    receipt = _json(TRANSITION / "receipt.json")
    assert receipt["repository_evidence_sealed"] is True
    assert receipt["post_merge_verification_passed"] is True
    assert receipt["authorization_consumed"] is True
    assert receipt["retry_permitted"] is False
    assert receipt["runtime_rerun_performed"] is False
    assert receipt["engineering_evidence_present"] is True
    assert receipt["image_freeze_eligible"] is True
    assert receipt["scientific_evidence"] is False
    assert receipt["scientific_execution_open"] is False
    assert receipt["test_dataset_access"] is False
    assert receipt["publication_permitted"] is False
    assert receipt["qw_lc0_transition_permitted"] is True
    assert receipt["qw_lc0_open"] is True
    assert receipt["qw_lc0_semantics_scope_frozen"] is False
    assert receipt["local_compute_implementation_open"] is False
    assert receipt["local_compute_execution_open"] is False
    assert receipt["next_slice"] == "QW-LC0"
    assert receipt["post_lc0_next_slice"] == "QW-LC1"


def test_status_and_adr_expose_current_transition_boundary() -> None:
    markers = (
        "qwake_qw4b_e_v2_repository_evidence_sealed=true",
        f"qwake_qw4b_e_v2_repository_seal_commit={SEAL_COMMIT}",
        f"qwake_qw4b_e_v2_repository_merge_commit={MAIN_COMMIT}",
        "qwake_qw4b_e_v2_post_merge_verification_passed=true",
        "qwake_qw_lc0_transition_permitted=true",
        "qwake_qw_lc0_open=true",
        "qwake_qw_lc0_semantics_scope_frozen=false",
        "qwake_local_compute_implementation_open=false",
        "qwake_local_compute_execution_open=false",
        "qwake_scientific_image_freeze_permitted=false",
        "test_dataset_access=false",
        "publication_permitted=false",
        "qwake_next_slice=QW-LC0",
        "qwake_post_lc0_next_slice=QW-LC1",
    )
    sections = (
        ("STATUS.md", "## `QW-LC0`: post-merge переход открыт"),
        ("STATUS_EN.md", "## `QW-LC0`: post-merge transition opened"),
        (
            "docs/decisions/"
            "ADR-049-stage3b-qwake-lc0-post-merge-transition.md",
            "# ADR-049:",
        ),
        (
            "docs/decisions/"
            "ADR-049-stage3b-qwake-lc0-post-merge-transition_EN.md",
            "# ADR-049:",
        ),
    )
    for name, heading in sections:
        text = (ROOT / name).read_text(encoding="utf-8")
        current = text[text.index(heading):]
        for marker in markers:
            assert marker in current, (name, marker)
