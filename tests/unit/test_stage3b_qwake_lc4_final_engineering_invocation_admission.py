from __future__ import annotations

import ast
import hashlib
import json
import shutil
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from torch2pc_thesis.stage3b_qwake_lc4_final_engineering_invocation_admission import (
    DURABLE_HOST_OUTCOME_RELATIVE,
    EXECUTION_LEASE_V1_RELATIVE,
    EXECUTION_LEASE_V2_RELATIVE,
    FINAL_ENGINEERING_INVOCATION_ADMISSION_ID,
    FINAL_ENGINEERING_INVOCATION_ADMISSION_STATUS,
    OUTPUT_ROOT,
    RUNTIME_ENTRYPOINT,
    SCOPE_FREEZE_MERGE_COMMIT,
    FinalEngineeringInvocationAdmissionError,
    build_final_engineering_invocation_admission,
    load_final_engineering_invocation_admission,
    validate_final_engineering_invocation_admission,
    verify_final_engineering_invocation_sources,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = (
    PROJECT_ROOT
    / "experiments/frozen/"
    "stage3b-qwake-lc4-e-final-engineering-invocation-admission-authoring-v1"
)
MODULE_PATH = (
    PROJECT_ROOT
    / "src/torch2pc_thesis/"
    "stage3b_qwake_lc4_final_engineering_invocation_admission.py"
)
VERIFIER_PATH = (
    PROJECT_ROOT
    / "scripts/verify_stage3b_qwake_lc4_final_engineering_invocation_admission.py"
)


def _admission():
    return build_final_engineering_invocation_admission(
        authored_at_utc="2026-08-03T12:30:00Z",
        authoring_base_commit=SCOPE_FREEZE_MERGE_COMMIT,
    )


def test_source_packages_and_semantics_are_exact() -> None:
    source = verify_final_engineering_invocation_sources(PROJECT_ROOT)

    assert source.scope_freeze_merge_commit == SCOPE_FREEZE_MERGE_COMMIT
    assert source.scope_freeze_pr_number == 168
    assert source.runtime_entrypoint_module_sha256.startswith("sha256:")


def test_admission_round_trip_and_validation(tmp_path: Path) -> None:
    admission = _admission()

    assert admission.admission_id == FINAL_ENGINEERING_INVOCATION_ADMISSION_ID
    assert admission.status == FINAL_ENGINEERING_INVOCATION_ADMISSION_STATUS
    assert admission.gates.final_engineering_invocation_admission_authored is True
    assert admission.gates.final_engineering_invocation_admission_record_present is True
    assert admission.gates.final_engineering_invocation_authorization_issued is False
    assert admission.gates.final_engineering_invocation_permitted is False

    path = tmp_path / "admission.json"
    path.write_text(admission.canonical_json(), encoding="utf-8")
    loaded = load_final_engineering_invocation_admission(path)

    validate_final_engineering_invocation_admission(
        loaded,
        verify_final_engineering_invocation_sources(PROJECT_ROOT),
        tmp_path,
        expected_authoring_base_commit=SCOPE_FREEZE_MERGE_COMMIT,
    )
    assert loaded == admission


def test_wrong_identity_and_open_gate_fail_closed() -> None:
    admission = _admission()

    with pytest.raises(FinalEngineeringInvocationAdmissionError):
        replace(
            admission,
            authoring_base_commit="a" * 40,
        ).require()

    with pytest.raises(FinalEngineeringInvocationAdmissionError):
        replace(
            admission,
            gates=replace(
                admission.gates,
                final_engineering_invocation_authorization_issued=True,
            ),
        ).require()

    with pytest.raises(FinalEngineeringInvocationAdmissionError):
        replace(
            admission,
            boundary=replace(
                admission.boundary,
                operator_phrase_reserved=True,
            ),
        ).require()


def test_existing_runtime_boundary_paths_fail_closed(tmp_path: Path) -> None:
    admission = _admission()
    source = verify_final_engineering_invocation_sources(PROJECT_ROOT)

    for relative in (
        Path(OUTPUT_ROOT),
        EXECUTION_LEASE_V1_RELATIVE,
        EXECUTION_LEASE_V2_RELATIVE,
        DURABLE_HOST_OUTCOME_RELATIVE,
    ):
        case_root = tmp_path / relative.name
        target = case_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if relative == Path(OUTPUT_ROOT):
            target.mkdir()
        else:
            target.write_text("{}\n", encoding="utf-8")

        with pytest.raises(
            FinalEngineeringInvocationAdmissionError,
            match="runtime boundary path already exists",
        ):
            validate_final_engineering_invocation_admission(
                admission,
                source,
                case_root,
                expected_authoring_base_commit=SCOPE_FREEZE_MERGE_COMMIT,
            )


def test_negative_source_mutation_uses_temporary_copy(tmp_path: Path) -> None:
    source_scope = PROJECT_ROOT / (
        "experiments/frozen/"
        "stage3b-qwake-lc4-e-final-engineering-invocation-admission-"
        "authoring-scope-freeze-v1"
    )
    copied_root = tmp_path / "repository"
    copied_scope = copied_root / source_scope.relative_to(PROJECT_ROOT)
    copied_scope.parent.mkdir(parents=True)
    shutil.copytree(source_scope, copied_scope)

    scope_json = copied_scope / "scope.json"
    scope_json.write_text(scope_json.read_text(encoding="utf-8") + " ", encoding="utf-8")

    with pytest.raises(
        FinalEngineeringInvocationAdmissionError,
        match="package registry digest differs",
    ):
        verify_final_engineering_invocation_sources(copied_root)


def test_admission_surfaces_do_not_import_or_invoke_runtime() -> None:
    module_text = MODULE_PATH.read_text(encoding="utf-8")
    verifier_text = VERIFIER_PATH.read_text(encoding="utf-8")
    combined = module_text + "\n" + verifier_text

    forbidden_markers = (
        "subprocess.Popen(",
        "docker run",
        "docker image inspect",
        "import torch",
        "from torch import",
        "stage3b_qwake_lc4_lease_bound_host_invoker_wiring import",
        f"{RUNTIME_ENTRYPOINT}(",
    )
    assert all(marker not in combined for marker in forbidden_markers)
    assert "stage3b_qwake_lc4_lease_bound_host_invoker_wiring.py" in module_text
    assert RUNTIME_ENTRYPOINT in module_text

    for source_text in (module_text, verifier_text):
        tree = ast.parse(source_text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported = tuple(alias.name for alias in node.names)
                assert all(
                    name != "torch"
                    and not name.startswith("torch.")
                    and "lease_bound_host_invoker_wiring" not in name
                    for name in imported
                )
            if isinstance(node, ast.ImportFrom):
                imported_from = node.module or ""
                assert imported_from != "torch"
                assert not imported_from.startswith("torch.")
                assert "lease_bound_host_invoker_wiring" not in imported_from


def test_frozen_admission_package_and_verifier() -> None:
    admission_path = PACKAGE_ROOT / "admission.json"
    source_registry = PACKAGE_ROOT / "source-SHA256SUMS"
    registry = PACKAGE_ROOT / "SHA256SUMS"

    assert admission_path.is_file()
    assert source_registry.is_file()
    assert registry.is_file()

    registry_entries = {}
    for line in registry.read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", 1)
        registry_entries[relative] = digest
    assert set(registry_entries) == {"admission.json", "source-SHA256SUMS"}
    assert hashlib.sha256(admission_path.read_bytes()).hexdigest() == registry_entries[
        "admission.json"
    ]
    assert hashlib.sha256(source_registry.read_bytes()).hexdigest() == registry_entries[
        "source-SHA256SUMS"
    ]

    loaded = load_final_engineering_invocation_admission(admission_path)
    assert loaded.admission_id == FINAL_ENGINEERING_INVOCATION_ADMISSION_ID

    completed = subprocess.run(
        [
            sys.executable,
            str(VERIFIER_PATH),
            "--project-root",
            str(PROJECT_ROOT),
            "--admission",
            str(admission_path),
            "--authoring-base-commit",
            SCOPE_FREEZE_MERGE_COMMIT,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "FINAL_ENGINEERING_INVOCATION_ADMISSION_VERIFIED=true" in completed.stdout
    assert "FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_ISSUED=false" in completed.stdout
    assert "FINAL_ENGINEERING_INVOCATION_PERMITTED=false" in completed.stdout


def test_repository_documentation_records_admission_authoring() -> None:
    marker = "ADR-101-stage3b-qwake-lc4-e-final-engineering-invocation-admission-authoring"
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

    payload = json.loads((PACKAGE_ROOT / "admission.json").read_text(encoding="utf-8"))
    gates = payload["gates"]
    assert gates["final_engineering_invocation_admission_authored"] is True
    assert gates["final_engineering_invocation_admission_record_present"] is True
    assert gates["final_engineering_invocation_authorization_issued"] is False
    assert gates["final_engineering_invocation_authorization_consumed"] is False
    assert gates["final_engineering_invocation_permitted"] is False
    assert gates["final_engineering_invocation_started"] is False
    assert gates["final_engineering_invocation_performed"] is False
    assert gates["qw5_transition_permitted"] is False
