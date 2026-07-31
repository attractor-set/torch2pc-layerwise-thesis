from __future__ import annotations

import ast
import importlib
import shutil
from dataclasses import replace
from pathlib import Path

import pytest

import torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation as implementation_module
from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_authoring import (
    DURABLE_HOST_OUTCOME_RELATIVE,
    EXECUTION_LEASE_V2_RELATIVE,
    FINAL_EXECUTION_OPERATOR_ACKNOWLEDGEMENT,
)
from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_issuance_authoring import (
    ACKNOWLEDGEMENT_RELATIVE,
)
from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_issuance_implementation import (
    LEGACY_EXECUTION_LEASE_RELATIVE,
)
from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation import (
    AUTHORING_MERGE_RECEIPT_RELATIVE,
    IMPLEMENTATION_MODULE_RELATIVE,
    IMPLEMENTATION_PACKAGE_RELATIVE,
    IMPLEMENTATION_RECORD_RELATIVE,
    IMPLEMENTATION_SOURCE_REGISTRY_RELATIVE,
    AcknowledgementMaterializationInvocationImplementationError,
    build_authoring_merge_validation_receipt,
    build_frozen_materialization_invocation_implementation_record,
    invoke_final_execution_acknowledgement_materialization,
    load_authoring_merge_validation_receipt,
    load_materialization_invocation_implementation_record,
    probe_final_execution_acknowledgement_state,
    verify_final_execution_acknowledgement_materialization_invocation_implementation,
)
from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_authoring import (
    AUTHORING_RECORD_RELATIVE as INVOCATION_AUTHORING_RECORD_RELATIVE,
)
from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_authoring import (
    IMPLEMENTATION_MERGE_RECEIPT_RELATIVE as INVOCATION_AUTHORING_RECEIPT_RELATIVE,
)
from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_authoring import (
    build_prospective_acknowledgement_materialization_invocation,
    load_final_execution_acknowledgement_materialization_invocation_authoring,
    load_materialization_implementation_merge_validation_receipt,
)

ROOT = Path(__file__).resolve().parents[2]


def _invocation():
    receipt = load_materialization_implementation_merge_validation_receipt(
        ROOT / INVOCATION_AUTHORING_RECEIPT_RELATIVE
    )
    authoring = load_final_execution_acknowledgement_materialization_invocation_authoring(
        ROOT / INVOCATION_AUTHORING_RECORD_RELATIVE,
        receipt,
    )
    invocation = build_prospective_acknowledgement_materialization_invocation(
        authoring,
        receipt,
        acknowledgement_phrase=FINAL_EXECUTION_OPERATOR_ACKNOWLEDGEMENT,
        operator_identity="operator@example.invalid",
        acknowledged_at_utc="2026-07-31T01:15:00Z",
        issuer_identity="issuer@example.invalid",
        issued_at_utc="2026-07-31T01:16:00Z",
        materializer_identity="issuer@example.invalid",
        materialized_at_utc="2026-07-31T01:17:00Z",
    )
    return invocation


def _copy_minimal_repository(tmp_path: Path) -> Path:
    copied = tmp_path / "repository"
    copied.mkdir()
    pending: list[Path] = [
        path.relative_to(ROOT)
        for path in (ROOT / IMPLEMENTATION_PACKAGE_RELATIVE).iterdir()
    ]
    pending.append(IMPLEMENTATION_SOURCE_REGISTRY_RELATIVE)
    copied_paths: set[Path] = set()

    while pending:
        relative = pending.pop()
        if relative in copied_paths:
            continue
        source = ROOT / relative
        target = copied / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied_paths.add(relative)

        if source.name not in {"SHA256SUMS", "source-SHA256SUMS"}:
            continue
        for line in source.read_text(encoding="utf-8").splitlines():
            _, entry = line.split("  ", 1)
            child = relative.parent / entry if source.name == "SHA256SUMS" else Path(entry)
            if child not in copied_paths:
                pending.append(child)

    (copied / "results/stage-3").mkdir(parents=True, exist_ok=True)
    return copied


def test_frozen_records_are_exact() -> None:
    receipt = load_authoring_merge_validation_receipt(
        ROOT / AUTHORING_MERGE_RECEIPT_RELATIVE
    )
    implementation = load_materialization_invocation_implementation_record(
        ROOT / IMPLEMENTATION_RECORD_RELATIVE,
        receipt,
    )
    assert receipt == build_authoring_merge_validation_receipt()
    assert implementation == build_frozen_materialization_invocation_implementation_record(
        receipt
    )
    assert implementation.gates.materialization_invocation_implemented is True
    assert implementation.gates.materializer_called is False


def test_complete_package_verifies_without_effects() -> None:
    result = verify_final_execution_acknowledgement_materialization_invocation_implementation(
        ROOT
    )
    assert result.gates.materialization_invocation_implemented is True
    assert result.gates.materialization_invoked is False
    assert not (ROOT / ACKNOWLEDGEMENT_RELATIVE).exists()


def test_probe_classifies_absent_target_without_effects(tmp_path: Path) -> None:
    copied = _copy_minimal_repository(tmp_path)
    probe = probe_final_execution_acknowledgement_state(copied, _invocation())
    assert probe.state == "absent"
    assert probe.materializer_call_permitted is True
    assert not (copied / ACKNOWLEDGEMENT_RELATIVE).exists()


def test_adapter_materializes_once_after_absent_probe(tmp_path: Path) -> None:
    copied = _copy_minimal_repository(tmp_path)
    result = invoke_final_execution_acknowledgement_materialization(
        copied, _invocation()
    )
    assert result.outcome == "materialized"
    assert result.probe.state == "absent"
    assert result.materializer_called is True
    assert result.writer_called is True
    assert result.automatic_retry_performed is False
    assert (copied / ACKNOWLEDGEMENT_RELATIVE).is_file()


def test_adapter_does_not_create_other_runtime_artifacts(tmp_path: Path) -> None:
    copied = _copy_minimal_repository(tmp_path)
    invoke_final_execution_acknowledgement_materialization(copied, _invocation())
    assert not (copied / LEGACY_EXECUTION_LEASE_RELATIVE).exists()
    assert not (copied / EXECUTION_LEASE_V2_RELATIVE).exists()
    assert not (copied / DURABLE_HOST_OUTCOME_RELATIVE).exists()


def test_valid_existing_target_is_reused_without_materializer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    copied = _copy_minimal_repository(tmp_path)
    first = invoke_final_execution_acknowledgement_materialization(copied, _invocation())
    calls = 0

    def forbidden(*args, **kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError("materializer must not be recalled")

    monkeypatch.setattr(implementation_module, "_materialize_once", forbidden)
    second = invoke_final_execution_acknowledgement_materialization(copied, _invocation())
    assert first.materialization.persisted_sha256 == second.materialization.persisted_sha256
    assert second.outcome == "valid_existing"
    assert second.existing_valid_target_reused is True
    assert second.materializer_called is False
    assert calls == 0


def test_second_adapter_call_is_recovery_success_not_retry(tmp_path: Path) -> None:
    copied = _copy_minimal_repository(tmp_path)
    invoke_final_execution_acknowledgement_materialization(copied, _invocation())
    second = invoke_final_execution_acknowledgement_materialization(copied, _invocation())
    assert second.outcome == "valid_existing"
    assert second.automatic_retry_performed is False
    assert second.blind_retry_performed is False


def test_invalid_existing_target_fails_closed(tmp_path: Path) -> None:
    copied = _copy_minimal_repository(tmp_path)
    target = copied / ACKNOWLEDGEMENT_RELATIVE
    target.write_text("{}\n", encoding="utf-8")
    with pytest.raises(
        AcknowledgementMaterializationInvocationImplementationError,
        match="existing final execution acknowledgement is invalid",
    ):
        invoke_final_execution_acknowledgement_materialization(copied, _invocation())


def test_dangling_symbolic_target_fails_closed(tmp_path: Path) -> None:
    copied = _copy_minimal_repository(tmp_path)
    target = copied / ACKNOWLEDGEMENT_RELATIVE
    target.symlink_to(copied / "missing-acknowledgement")
    with pytest.raises(
        AcknowledgementMaterializationInvocationImplementationError,
        match="existing final execution acknowledgement is invalid",
    ):
        invoke_final_execution_acknowledgement_materialization(copied, _invocation())


def test_materializer_failure_is_not_retried(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    copied = _copy_minimal_repository(tmp_path)
    calls = 0

    def failing(*args, **kwargs):
        nonlocal calls
        calls += 1
        raise RuntimeError("simulated uncertain materializer failure")

    monkeypatch.setattr(implementation_module, "_materialize_once", failing)
    with pytest.raises(
        AcknowledgementMaterializationInvocationImplementationError,
        match="simulated uncertain materializer failure",
    ):
        invoke_final_execution_acknowledgement_materialization(copied, _invocation())
    assert calls == 1


def test_invocation_identity_drift_is_rejected(tmp_path: Path) -> None:
    copied = _copy_minimal_repository(tmp_path)
    drifted = replace(
        _invocation(), invocation_authoring_sha256="sha256:" + "0" * 64
    )
    with pytest.raises(
        AcknowledgementMaterializationInvocationImplementationError,
        match="prospective materialization invocation differs",
    ):
        invoke_final_execution_acknowledgement_materialization(copied, drifted)


def test_invocation_timestamp_drift_is_rejected(tmp_path: Path) -> None:
    copied = _copy_minimal_repository(tmp_path)
    drifted = replace(_invocation(), materialized_at_utc="2026-07-31T01:15:30Z")
    with pytest.raises(
        AcknowledgementMaterializationInvocationImplementationError,
        match="materialization timestamp is before issuance",
    ):
        invoke_final_execution_acknowledgement_materialization(copied, drifted)


@pytest.mark.parametrize(
    ("relative", "label"),
    (
        (
            Path("results/stage-3/qwake-lc4-runtime-validation-v1-attempt-001"),
            "authorized output root",
        ),
        (LEGACY_EXECUTION_LEASE_RELATIVE, "legacy execution lease"),
        (EXECUTION_LEASE_V2_RELATIVE, "persistent execution lease v2"),
        (DURABLE_HOST_OUTCOME_RELATIVE, "durable host outcome"),
    ),
)
def test_non_acknowledgement_boundary_collision_fails_closed(
    tmp_path: Path, relative: Path, label: str
) -> None:
    copied = _copy_minimal_repository(tmp_path)
    target = copied / relative
    if relative.suffix:
        target.write_text("{}\n", encoding="utf-8")
    else:
        target.mkdir()
    with pytest.raises(
        AcknowledgementMaterializationInvocationImplementationError,
        match=label,
    ):
        invoke_final_execution_acknowledgement_materialization(copied, _invocation())


def test_source_registry_rejects_implementation_drift(tmp_path: Path) -> None:
    copied = _copy_minimal_repository(tmp_path)
    target = copied / IMPLEMENTATION_MODULE_RELATIVE
    target.write_text(target.read_text(encoding="utf-8") + "\n# drift\n", encoding="utf-8")
    with pytest.raises(
        AcknowledgementMaterializationInvocationImplementationError,
        match="registry target digest differs",
    ):
        verify_final_execution_acknowledgement_materialization_invocation_implementation(
            copied
        )


def test_adapter_ast_has_one_materializer_and_no_writer_call() -> None:
    source = (ROOT / IMPLEMENTATION_MODULE_RELATIVE).read_text(encoding="utf-8")
    tree = ast.parse(source)
    calls = []
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.append(node.func.attr)
        if isinstance(node, ast.ImportFrom):
            imports.extend(alias.name for alias in node.names)
    assert calls.count("_materialize_once") == 1
    assert calls.count("_verify_persisted_once") == 1
    assert calls.count("_build_prospective_materialization") == 1
    assert "persist_final_execution_acknowledgement" not in imports


def test_repository_has_no_production_adapter_callsite() -> None:
    target = "invoke_final_execution_acknowledgement_materialization"
    allowed = (ROOT / IMPLEMENTATION_MODULE_RELATIVE).resolve()
    for path in (ROOT / "src").rglob("*.py"):
        if path.resolve() == allowed:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = node.func.id if isinstance(node.func, ast.Name) else (
                node.func.attr if isinstance(node.func, ast.Attribute) else ""
            )
            assert name != target


def test_import_has_no_effects() -> None:
    before = (ROOT / ACKNOWLEDGEMENT_RELATIVE).exists()
    importlib.reload(implementation_module)
    assert (ROOT / ACKNOWLEDGEMENT_RELATIVE).exists() is before
