from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from torch2pc_thesis.stage3b_qwake_lc4_execution_admission import (
    AUTHORIZED_OUTPUT_ROOT,
    EXECUTION_ADMISSION_ID,
    EXECUTION_ADMISSION_STATUS,
    EXECUTION_LEASE_RELATIVE,
    EXECUTION_OPERATOR_ACKNOWLEDGEMENT,
    load_execution_admission,
    validate_execution_admission,
    verify_frozen_runtime_package,
)

ROOT = Path(__file__).resolve().parents[2]
FREEZE = (
    ROOT
    / "experiments/frozen/"
    "stage3b-qwake-lc4-e-execution-admission-freeze-v1"
)
ADMISSION = FREEZE / "admission.json"
RECEIPT = FREEZE / "verification-receipt.json"
VALIDATION_LOG = FREEZE / "admission-validation.log"

CONTROL_PLANE = "bce821dff0729629db0ccb306d8f3fd1dd9a2e13"
PR_HEAD = "83a07683feb51913c7fcc7878a323e51a84da771"
MERGED_AT = datetime(
    2026,
    7,
    27,
    20,
    13,
    38,
    tzinfo=UTC,
)
FILES = {
    "SHA256SUMS",
    "admission-validation.log",
    "admission.json",
    "source-SHA256SUMS",
    "verification-receipt.json",
}
SOURCE_PATHS = {
    (
        "experiments/frozen/"
        "stage3b-qwake-lc4-e-execution-admission-authoring-v1/"
        "SHA256SUMS"
    ),
    (
        "experiments/frozen/"
        "stage3b-qwake-lc4-e-execution-admission-authoring-v1/"
        "authoring.json"
    ),
    (
        "experiments/frozen/"
        "stage3b-qwake-lc4-f-runtime-freeze-v1/SHA256SUMS"
    ),
    (
        "experiments/frozen/"
        "stage3b-qwake-lc4-f-runtime-freeze-v1/source-SHA256SUMS"
    ),
    "scripts/verify_stage3b_qwake_lc4_execution_admission.py",
    "src/torch2pc_thesis/stage3b_qwake_lc4_execution_admission.py",
    "tests/unit/test_stage3b_qwake_lc4_execution_admission.py",
}


def load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def check_registry(path: Path, base: Path) -> set[str]:
    observed = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", 1)
        target = base / relative
        assert target.is_file() and not target.is_symlink()
        assert hashlib.sha256(target.read_bytes()).hexdigest() == digest
        observed.add(relative)
    return observed


def test_scope_and_registries() -> None:
    entries = tuple(FREEZE.iterdir())
    assert {item.name for item in entries if item.is_file()} == FILES
    assert not any(item.is_dir() or item.is_symlink() for item in entries)
    assert check_registry(FREEZE / "SHA256SUMS", FREEZE) == {
        "admission-validation.log",
        "admission.json",
        "source-SHA256SUMS",
        "verification-receipt.json",
    }
    assert check_registry(
        FREEZE / "source-SHA256SUMS",
        ROOT,
    ) == SOURCE_PATHS


def test_admission_is_exact_and_unstarted() -> None:
    frozen = verify_frozen_runtime_package(ROOT)
    admission = load_execution_admission(ADMISSION)
    validate_execution_admission(
        admission,
        frozen,
        ROOT,
        expected_control_plane_commit=CONTROL_PLANE,
    )
    assert admission.admission_id == EXECUTION_ADMISSION_ID
    assert admission.status == EXECUTION_ADMISSION_STATUS
    assert admission.control_plane_commit == CONTROL_PLANE
    assert (
        admission.operator_acknowledgement
        == EXECUTION_OPERATOR_ACKNOWLEDGEMENT
    )
    assert admission.output_root_absent_at_admission is True
    assert admission.execution_lease_absent_at_admission is True
    assert admission.authorization_consumed is False
    assert admission.execution_count == 1
    assert admission.runtime_execution_permitted is True
    assert admission.runtime_execution_started is False
    assert admission.runtime_execution_performed is False
    assert admission.engineering_evidence_present is False
    assert admission.scientific_execution_open is False
    assert admission.test_dataset_access is False
    assert admission.publication_permitted is False
    admitted = datetime.fromisoformat(
        admission.admitted_at_utc.replace("Z", "+00:00")
    )
    assert admitted >= MERGED_AT
    assert not (ROOT / AUTHORIZED_OUTPUT_ROOT).exists()
    assert not (ROOT / EXECUTION_LEASE_RELATIVE).exists()


def test_receipt_and_validation_log() -> None:
    admission = load_execution_admission(ADMISSION)
    receipt = load_json(RECEIPT)
    assert receipt["receipt_id"] == (
        "stage3b-qwake-lc4-e-execution-admission-verification-v1"
    )
    assert receipt["slice"] == "QW-LC4-E-admission-freeze"
    assert receipt["status"] == (
        "execution_admission_frozen_execution_not_started"
    )
    source = receipt["source"]
    assert isinstance(source, dict)
    assert source["control_plane_merge_commit"] == CONTROL_PLANE
    assert source["control_plane_pr_head"] == PR_HEAD
    record = receipt["admission"]
    assert isinstance(record, dict)
    assert record["admission_id"] == admission.admission_id
    assert record["admission_sha256"] == admission.admission_sha256
    assert record["admitted_at_utc"] == admission.admitted_at_utc
    assert record["control_plane_commit"] == CONTROL_PLANE
    assert record["execution_count"] == 1
    assert record["output_root"] == AUTHORIZED_OUTPUT_ROOT
    assert record["admission_file_sha256"] == (
        "sha256:" + hashlib.sha256(ADMISSION.read_bytes()).hexdigest()
    )
    validation = receipt["validation"]
    assert isinstance(validation, dict)
    assert validation["validation_log_sha256"] == (
        "sha256:"
        + hashlib.sha256(VALIDATION_LOG.read_bytes()).hexdigest()
    )
    gates = receipt["gates"]
    assert isinstance(gates, dict)
    assert gates["execution_admission_issued"] is True
    assert gates["admission_record_runtime_execution_permitted"] is True
    assert gates["qw_lc4_e_execution_permitted"] is False
    for key in (
        "runtime_execution_started",
        "runtime_execution_performed",
        "engineering_evidence_present",
        "scientific_execution_open",
        "test_dataset_access",
        "publication_permitted",
        "local_compute_execution_open",
    ):
        assert gates[key] is False
    capabilities = receipt["capabilities"]
    assert isinstance(capabilities, dict)
    assert all(value is False for value in capabilities.values())
    log = VALIDATION_LOG.read_text(encoding="utf-8")
    for marker in (
        "EXIT_STATUS=0",
        "ADMISSION_VERIFIED=true",
        "RUNTIME_EXECUTION_PERMITTED=true",
        "RUNTIME_EXECUTION_STARTED=false",
        "RUNTIME_EXECUTION_PERFORMED=false",
    ):
        assert marker in log


def test_repository_documentation() -> None:
    marker = "ADR-065-stage3b-qwake-lc4-e-execution-admission-freeze"
    required = (
        ROOT / "STATUS.md",
        ROOT / "STATUS_EN.md",
        ROOT / "docs/qwake-local-compute-extension.md",
        ROOT / "docs/qwake-local-compute-extension_EN.md",
        ROOT / "docs/decisions/index.md",
        ROOT / "docs/decisions/index_EN.md",
        ROOT / "docs/language-map.csv",
        ROOT / "docs/research-log/2026-07.md",
        ROOT / "docs/research-log/2026-07_EN.md",
    )
    for path in required:
        assert marker in path.read_text(encoding="utf-8")
    for path in (ROOT / "STATUS.md", ROOT / "STATUS_EN.md"):
        text = path.read_text(encoding="utf-8")
        assert "ADMISSION_FREEZE_MATERIALIZED=true" in text
        assert "EXECUTION_ADMISSION_ISSUED=true" in text
        assert "ADMISSION_RECORD_RUNTIME_EXECUTION_PERMITTED=true" in text
        assert "QW_LC4_E_EXECUTION_PERMITTED=false" in text
        assert "RUNTIME_EXECUTION_STARTED=false" in text
        assert "RUNTIME_EXECUTION_PERFORMED=false" in text
        assert "LOCAL_COMPUTE_EXECUTION_OPEN=false" in text
