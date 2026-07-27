from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest

from torch2pc_thesis.stage3b_qwake_lc4_execution_admission import (
    AUTHORIZED_OUTPUT_ROOT,
    EXECUTION_ADMISSION_ID,
    EXECUTION_ADMISSION_STATUS,
    EXECUTION_LEASE_RELATIVE,
    EXECUTION_OPERATOR_ACKNOWLEDGEMENT,
    FROZEN_RUNTIME_MERGE_COMMIT,
    QWakeLC4ExecutionAdmissionError,
    build_execution_admission,
    load_execution_admission,
    validate_execution_admission,
    verify_frozen_runtime_package,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
AUTHORING_ROOT = (
    PROJECT_ROOT
    / "experiments/frozen/"
    "stage3b-qwake-lc4-e-execution-admission-authoring-v1"
)


def _admission(project_root: Path):
    frozen = verify_frozen_runtime_package(project_root)
    return build_execution_admission(
        frozen,
        admitted_at_utc="2026-07-27T19:00:00Z",
        control_plane_commit="a" * 40,
        operator_acknowledgement=EXECUTION_OPERATOR_ACKNOWLEDGEMENT,
        output_root_absent_at_admission=True,
        execution_lease_absent_at_admission=True,
    )


def test_frozen_runtime_package_is_exact() -> None:
    frozen = verify_frozen_runtime_package(PROJECT_ROOT)

    assert frozen.freeze_merge_commit == FROZEN_RUNTIME_MERGE_COMMIT
    assert frozen.output_root == AUTHORIZED_OUTPUT_ROOT
    assert frozen.execution_count == 1
    assert frozen.authorized_cell_count == 168
    assert frozen.runtime_execution_permitted is True
    assert frozen.runtime_execution_performed is False
    assert frozen.engineering_evidence_present is False
    assert frozen.scientific_execution_open is False
    assert frozen.test_dataset_access is False
    assert frozen.publication_permitted is False


def test_admission_round_trip_and_validation(tmp_path: Path) -> None:
    admission = _admission(PROJECT_ROOT)

    assert admission.admission_id == EXECUTION_ADMISSION_ID
    assert admission.status == EXECUTION_ADMISSION_STATUS
    assert admission.runtime_execution_permitted is True
    assert admission.runtime_execution_started is False
    assert admission.runtime_execution_performed is False
    assert admission.authorization_consumed is False

    path = tmp_path / "admission.json"
    path.write_text(admission.canonical_json(), encoding="utf-8")
    loaded = load_execution_admission(path)

    validate_execution_admission(
        loaded,
        verify_frozen_runtime_package(PROJECT_ROOT),
        tmp_path,
        expected_control_plane_commit="a" * 40,
    )
    assert loaded == admission


def test_wrong_operator_acknowledgement_fails_closed() -> None:
    frozen = verify_frozen_runtime_package(PROJECT_ROOT)

    with pytest.raises(
        QWakeLC4ExecutionAdmissionError,
        match="operator acknowledgement",
    ):
        build_execution_admission(
            frozen,
            admitted_at_utc="2026-07-27T19:00:00Z",
            control_plane_commit="a" * 40,
            operator_acknowledgement="ADMIT_SOMETHING_ELSE",
            output_root_absent_at_admission=True,
            execution_lease_absent_at_admission=True,
        )


def test_existing_output_or_lease_fails_closed(tmp_path: Path) -> None:
    admission = _admission(PROJECT_ROOT)
    frozen = verify_frozen_runtime_package(PROJECT_ROOT)

    output = tmp_path / AUTHORIZED_OUTPUT_ROOT
    output.mkdir(parents=True)

    with pytest.raises(
        QWakeLC4ExecutionAdmissionError,
        match="output root already exists",
    ):
        validate_execution_admission(
            admission,
            frozen,
            tmp_path,
            expected_control_plane_commit="a" * 40,
        )

    lease_root = tmp_path / "lease-case"
    lease = lease_root / EXECUTION_LEASE_RELATIVE
    lease.parent.mkdir(parents=True)
    lease.write_text("{}\n", encoding="utf-8")

    with pytest.raises(
        QWakeLC4ExecutionAdmissionError,
        match="execution lease already exists",
    ):
        validate_execution_admission(
            admission,
            frozen,
            lease_root,
            expected_control_plane_commit="a" * 40,
        )


def test_consumed_or_started_admission_fails_closed() -> None:
    admission = _admission(PROJECT_ROOT)

    with pytest.raises(QWakeLC4ExecutionAdmissionError):
        replace(admission, authorization_consumed=True).require()

    with pytest.raises(QWakeLC4ExecutionAdmissionError):
        replace(admission, runtime_execution_started=True).require()

    with pytest.raises(QWakeLC4ExecutionAdmissionError):
        replace(admission, runtime_execution_performed=True).require()


def test_admission_surfaces_do_not_expose_executor() -> None:
    module_text = (
        PROJECT_ROOT
        / "src/torch2pc_thesis/"
        "stage3b_qwake_lc4_execution_admission.py"
    ).read_text(encoding="utf-8")
    script_text = (
        PROJECT_ROOT
        / "scripts/verify_stage3b_qwake_lc4_execution_admission.py"
    ).read_text(encoding="utf-8")
    combined = module_text + "\n" + script_text

    forbidden_runtime_markers = (
        "def run_runtime_execution(",
        "def execute_matched_shadow(",
        "docker compose run",
        "write_result",
        "publish_result",
        "load_test_dataset",
    )
    assert all(
        marker not in combined
        for marker in forbidden_runtime_markers
    )

    for source in (module_text, script_text):
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported = tuple(alias.name for alias in node.names)
                assert all(
                    name != "torch" and not name.startswith("torch.")
                    for name in imported
                )
            if isinstance(node, ast.ImportFrom):
                imported_from = node.module or ""
                assert (
                    imported_from != "torch"
                    and not imported_from.startswith("torch.")
                )

    assert "RUNTIME_EXECUTION_STARTED=false" in script_text
    assert "RUNTIME_EXECUTION_PERFORMED=false" in script_text


def test_authoring_manifest_and_repository_documentation() -> None:
    registry = AUTHORING_ROOT / "SHA256SUMS"
    authoring = AUTHORING_ROOT / "authoring.json"

    assert registry.is_file()
    assert authoring.is_file()

    expected, relative = registry.read_text(
        encoding="utf-8"
    ).strip().split("  ", 1)
    assert relative == "authoring.json"
    assert hashlib.sha256(authoring.read_bytes()).hexdigest() == expected

    payload = json.loads(authoring.read_text(encoding="utf-8"))
    assert payload["authoring_id"] == (
        "stage3b-qwake-lc4-e-execution-admission-authoring-v1"
    )
    assert payload["status"] == (
        "execution_admission_authoring_materialized_execution_closed"
    )
    assert payload["source"]["base_commit"] == FROZEN_RUNTIME_MERGE_COMMIT
    assert payload["gates"]["qw_lc4_f_complete"] is True
    assert payload["gates"]["qw_lc4_e_branch_open"] is True
    assert payload["gates"]["execution_admission_implemented"] is True
    assert payload["gates"]["execution_admission_issued"] is False
    assert payload["gates"]["runtime_execution_permitted"] is False
    assert payload["gates"]["runtime_execution_started"] is False
    assert payload["gates"]["runtime_execution_performed"] is False

    marker = "ADR-064-stage3b-qwake-lc4-e-execution-admission-authoring"
    required = (
        PROJECT_ROOT / "STATUS.md",
        PROJECT_ROOT / "STATUS_EN.md",
        PROJECT_ROOT / "docs/qwake-local-compute-extension.md",
        PROJECT_ROOT / "docs/qwake-local-compute-extension_EN.md",
        PROJECT_ROOT / "docs/decisions/index.md",
        PROJECT_ROOT / "docs/decisions/index_EN.md",
        PROJECT_ROOT / "docs/language-map.csv",
        PROJECT_ROOT / "docs/research-log/2026-07.md",
        PROJECT_ROOT / "docs/research-log/2026-07_EN.md",
    )
    for path in required:
        assert marker in path.read_text(encoding="utf-8")
