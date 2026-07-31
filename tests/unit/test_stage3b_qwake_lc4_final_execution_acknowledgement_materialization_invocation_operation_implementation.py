from __future__ import annotations

import ast
import shutil
from dataclasses import replace
from pathlib import Path

import pytest

import torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_implementation as implementation_module
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
    invoke_final_execution_acknowledgement_materialization,
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
from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_authoring import (
    AUTHORING_RECORD_RELATIVE as OPERATION_AUTHORING_RECORD_RELATIVE,
)
from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_authoring import (
    FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_OPERATION_PHRASE,
    build_prospective_acknowledgement_materialization_invocation_operation,
    load_final_execution_acknowledgement_materialization_invocation_operation_authoring,
    load_invocation_implementation_merge_validation_receipt,
)
from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_authoring import (
    IMPLEMENTATION_MERGE_RECEIPT_RELATIVE as OPERATION_AUTHORING_RECEIPT_RELATIVE,
)
from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_implementation import (
    AUTHORING_MERGE_RECEIPT_RELATIVE,
    FUTURE_PRODUCTION_CALLSITE_RELATIVE,
    IMPLEMENTATION_MODULE_RELATIVE,
    IMPLEMENTATION_PACKAGE_RELATIVE,
    IMPLEMENTATION_RECORD_RELATIVE,
    IMPLEMENTATION_SOURCE_REGISTRY_RELATIVE,
    FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError,
    build_authoring_merge_validation_receipt,
    build_frozen_materialization_invocation_operation_implementation_record,
    load_authoring_merge_validation_receipt,
    load_materialization_invocation_operation_implementation_record,
    perform_final_execution_acknowledgement_materialization_invocation_operation,
    verify_final_execution_acknowledgement_materialization_invocation_operation_implementation,
)

ROOT = Path(__file__).resolve().parents[2]


def _operation():
    invocation_receipt = load_materialization_implementation_merge_validation_receipt(
        ROOT / INVOCATION_AUTHORING_RECEIPT_RELATIVE
    )
    invocation_authoring = load_final_execution_acknowledgement_materialization_invocation_authoring(
        ROOT / INVOCATION_AUTHORING_RECORD_RELATIVE,
        invocation_receipt,
    )
    invocation = build_prospective_acknowledgement_materialization_invocation(
        invocation_authoring,
        invocation_receipt,
        acknowledgement_phrase=FINAL_EXECUTION_OPERATOR_ACKNOWLEDGEMENT,
        operator_identity="operator@example.invalid",
        acknowledged_at_utc="2026-07-31T14:20:00Z",
        issuer_identity="issuer@example.invalid",
        issued_at_utc="2026-07-31T14:22:00Z",
        materializer_identity="issuer@example.invalid",
        materialized_at_utc="2026-07-31T14:23:00Z",
    )
    operation_receipt = load_invocation_implementation_merge_validation_receipt(
        ROOT / OPERATION_AUTHORING_RECEIPT_RELATIVE
    )
    operation_authoring = load_final_execution_acknowledgement_materialization_invocation_operation_authoring(
        ROOT / OPERATION_AUTHORING_RECORD_RELATIVE,
        operation_receipt,
    )
    return build_prospective_acknowledgement_materialization_invocation_operation(
        operation_authoring,
        operation_receipt,
        invocation,
        operation_phrase=(
            FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_OPERATION_PHRASE
        ),
        operation_operator_identity="operator@example.invalid",
        operation_authorized_at_utc="2026-07-31T14:21:00Z",
    )


def _copy_minimal_repository(tmp_path: Path, name: str = "repository") -> Path:
    copied = tmp_path / name
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
    implementation = load_materialization_invocation_operation_implementation_record(
        ROOT / IMPLEMENTATION_RECORD_RELATIVE,
        receipt,
    )
    assert receipt == build_authoring_merge_validation_receipt()
    assert implementation == build_frozen_materialization_invocation_operation_implementation_record(
        receipt
    )
    assert implementation.gates.materialization_invocation_operation_implemented is True
    assert implementation.gates.materialization_invocation_operation_performed is False


def test_complete_package_verifies_without_effects() -> None:
    result = verify_final_execution_acknowledgement_materialization_invocation_operation_implementation(
        ROOT
    )
    assert result.gates.materialization_invocation_operation_implemented is True
    assert result.gates.invocation_adapter_called is False
    assert not (ROOT / ACKNOWLEDGEMENT_RELATIVE).exists()


def test_operation_materializes_through_adapter_in_isolated_copy(tmp_path: Path) -> None:
    copied = _copy_minimal_repository(tmp_path)
    result = perform_final_execution_acknowledgement_materialization_invocation_operation(
        copied, _operation()
    )
    assert result.operation_performed is True
    assert result.invocation_adapter_called is True
    assert result.adapter_call_count == 1
    assert result.outcome == "materialized"
    assert (copied / ACKNOWLEDGEMENT_RELATIVE).is_file()


def test_operation_does_not_create_other_runtime_artifacts(tmp_path: Path) -> None:
    copied = _copy_minimal_repository(tmp_path)
    perform_final_execution_acknowledgement_materialization_invocation_operation(
        copied, _operation()
    )
    assert not (copied / LEGACY_EXECUTION_LEASE_RELATIVE).exists()
    assert not (copied / EXECUTION_LEASE_V2_RELATIVE).exists()
    assert not (copied / DURABLE_HOST_OUTCOME_RELATIVE).exists()


def test_valid_existing_target_is_operation_success(tmp_path: Path) -> None:
    copied = _copy_minimal_repository(tmp_path)
    first = perform_final_execution_acknowledgement_materialization_invocation_operation(
        copied, _operation()
    )
    second = perform_final_execution_acknowledgement_materialization_invocation_operation(
        copied, _operation()
    )
    assert first.outcome == "materialized"
    assert second.outcome == "valid_existing"
    assert second.materializer_called is False
    assert second.writer_called is False


def test_operation_calls_adapter_exactly_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    copied = _copy_minimal_repository(tmp_path)
    calls = 0
    original = implementation_module._invoke_once

    def counted(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(implementation_module, "_invoke_once", counted)
    result = perform_final_execution_acknowledgement_materialization_invocation_operation(
        copied, _operation()
    )
    assert calls == 1
    assert result.adapter_call_count == 1


def test_operation_performs_no_standalone_preprobe() -> None:
    tree = ast.parse((ROOT / IMPLEMENTATION_MODULE_RELATIVE).read_text(encoding="utf-8"))
    calls = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "probe_final_execution_acknowledgement_state" not in calls


def test_adapter_failure_is_propagated_without_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def failing(*args, **kwargs):
        nonlocal calls
        calls += 1
        raise RuntimeError("simulated adapter failure")

    monkeypatch.setattr(implementation_module, "_invoke_once", failing)
    with pytest.raises(
        FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError,
        match="simulated adapter failure",
    ):
        perform_final_execution_acknowledgement_materialization_invocation_operation(
            ROOT, _operation()
        )
    assert calls == 1


def test_wrong_operation_phrase_is_rejected_before_adapter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def forbidden(*args, **kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError("adapter must not be called")

    monkeypatch.setattr(implementation_module, "_invoke_once", forbidden)
    drifted = replace(_operation(), operation_phrase="wrong")
    with pytest.raises(
        FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError
    ):
        perform_final_execution_acknowledgement_materialization_invocation_operation(
            ROOT, drifted
        )
    assert calls == 0


def test_operator_mismatch_is_rejected_before_adapter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def forbidden(*args, **kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError("adapter must not be called")

    monkeypatch.setattr(implementation_module, "_invoke_once", forbidden)
    drifted = replace(_operation(), operation_operator_identity="other@example.invalid")
    with pytest.raises(
        FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError
    ):
        perform_final_execution_acknowledgement_materialization_invocation_operation(
            ROOT, drifted
        )
    assert calls == 0


def test_authorization_time_drift_is_rejected_before_adapter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def forbidden(*args, **kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError("adapter must not be called")

    monkeypatch.setattr(implementation_module, "_invoke_once", forbidden)
    drifted = replace(
        _operation(), operation_authorized_at_utc="2026-07-31T14:22:01Z"
    )
    with pytest.raises(
        FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError
    ):
        perform_final_execution_acknowledgement_materialization_invocation_operation(
            ROOT, drifted
        )
    assert calls == 0


def test_invalid_adapter_result_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _copy_minimal_repository(tmp_path, "source")
    valid = invoke_final_execution_acknowledgement_materialization(
        source, _operation().invocation
    )
    invalid = replace(valid, automatic_retry_performed=True)
    target = _copy_minimal_repository(tmp_path, "target")
    monkeypatch.setattr(implementation_module, "_invoke_once", lambda *args: invalid)
    with pytest.raises(
        FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError,
        match="automatic retry",
    ):
        perform_final_execution_acknowledgement_materialization_invocation_operation(
            target, _operation()
        )


def test_invalid_existing_target_fails_closed(tmp_path: Path) -> None:
    copied = _copy_minimal_repository(tmp_path)
    target = copied / ACKNOWLEDGEMENT_RELATIVE
    target.write_text("{}\n", encoding="utf-8")
    with pytest.raises(
        FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError,
        match="existing final execution acknowledgement is invalid",
    ):
        perform_final_execution_acknowledgement_materialization_invocation_operation(
            copied, _operation()
        )


def test_source_registry_rejects_implementation_drift(tmp_path: Path) -> None:
    copied = _copy_minimal_repository(tmp_path)
    module = copied / IMPLEMENTATION_MODULE_RELATIVE
    module.write_text(module.read_text(encoding="utf-8") + "\n# drift\n", encoding="utf-8")
    with pytest.raises(
        FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError
    ):
        verify_final_execution_acknowledgement_materialization_invocation_operation_implementation(
            copied
        )


def test_existing_acknowledgement_closes_package_verification(tmp_path: Path) -> None:
    copied = _copy_minimal_repository(tmp_path)
    target = copied / ACKNOWLEDGEMENT_RELATIVE
    target.write_text("{}\n", encoding="utf-8")
    with pytest.raises(
        FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError,
        match="production boundary is open",
    ):
        verify_final_execution_acknowledgement_materialization_invocation_operation_implementation(
            copied
        )


def test_production_callsite_is_absent() -> None:
    assert not (ROOT / FUTURE_PRODUCTION_CALLSITE_RELATIVE).exists()


def test_implementation_ast_forbids_direct_effect_delegates() -> None:
    tree = ast.parse((ROOT / IMPLEMENTATION_MODULE_RELATIVE).read_text(encoding="utf-8"))
    forbidden = {
        "probe_final_execution_acknowledgement_state",
        "materialize_final_execution_acknowledgement",
        "persist_final_execution_acknowledgement",
    }
    observed: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            observed.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            observed.add(node.func.attr)
    assert observed.isdisjoint(forbidden)


def test_operation_result_preserves_closed_execution_boundary(tmp_path: Path) -> None:
    copied = _copy_minimal_repository(tmp_path)
    result = perform_final_execution_acknowledgement_materialization_invocation_operation(
        copied, _operation()
    )
    assert result.one_shot_engineering_invocation_permitted is False
    assert result.execution_lease_materialized is False
    assert result.durable_host_outcome_present is False
    assert result.authorization_consumed is False
