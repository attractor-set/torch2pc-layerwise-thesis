from __future__ import annotations

import ast
import shutil
from dataclasses import replace
from pathlib import Path

import pytest

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
    ADR_EN_RELATIVE,
    ADR_RU_RELATIVE,
    AUTHORING_RECORD_RELATIVE,
    FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_OPERATION_PHRASE,
    FUTURE_OPERATION_IMPLEMENTATION_RELATIVE,
    IMPLEMENTATION_MERGE_RECEIPT_RELATIVE,
    MODULE_RELATIVE,
    PACKAGE_RELATIVE,
    SOURCE_REGISTRY_RELATIVE,
    TEST_RELATIVE,
    VERIFIER_RELATIVE,
    FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError,
    build_frozen_materialization_invocation_operation_authoring_record,
    build_invocation_implementation_merge_validation_receipt,
    build_prospective_acknowledgement_materialization_invocation_operation,
    load_final_execution_acknowledgement_materialization_invocation_operation_authoring,
    load_invocation_implementation_merge_validation_receipt,
    verify_final_execution_acknowledgement_materialization_invocation_operation_authoring,
)

ROOT = Path(__file__).resolve().parents[2]


def _records():
    receipt = load_invocation_implementation_merge_validation_receipt(
        ROOT / IMPLEMENTATION_MERGE_RECEIPT_RELATIVE
    )
    authoring = load_final_execution_acknowledgement_materialization_invocation_operation_authoring(
        ROOT / AUTHORING_RECORD_RELATIVE,
        receipt,
    )
    return receipt, authoring


def _invocation(**overrides: str):
    upstream_receipt = load_materialization_implementation_merge_validation_receipt(
        ROOT / INVOCATION_AUTHORING_RECEIPT_RELATIVE
    )
    upstream_authoring = load_final_execution_acknowledgement_materialization_invocation_authoring(
        ROOT / INVOCATION_AUTHORING_RECORD_RELATIVE,
        upstream_receipt,
    )
    values = {
        "acknowledgement_phrase": FINAL_EXECUTION_OPERATOR_ACKNOWLEDGEMENT,
        "operator_identity": "operator@example.invalid",
        "acknowledged_at_utc": "2026-07-31T04:00:00Z",
        "issuer_identity": "issuer@example.invalid",
        "issued_at_utc": "2026-07-31T04:02:00Z",
        "materializer_identity": "issuer@example.invalid",
        "materialized_at_utc": "2026-07-31T04:03:00Z",
    }
    values.update(overrides)
    return build_prospective_acknowledgement_materialization_invocation(
        upstream_authoring,
        upstream_receipt,
        **values,
    )


def _operation(invocation=None, **overrides: str):
    receipt, authoring = _records()
    if invocation is None:
        invocation = _invocation()
    values = {
        "operation_phrase": FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_OPERATION_PHRASE,
        "operation_operator_identity": "operator@example.invalid",
        "operation_authorized_at_utc": "2026-07-31T04:01:00Z",
    }
    values.update(overrides)
    result = build_prospective_acknowledgement_materialization_invocation_operation(
        authoring,
        receipt,
        invocation,
        **values,
    )
    return result, receipt, authoring


def _copy_minimal_repository(tmp_path: Path) -> Path:
    copied = tmp_path / "repository"
    copied.mkdir()
    pending: list[Path] = [
        path.relative_to(ROOT) for path in (ROOT / PACKAGE_RELATIVE).iterdir()
    ]
    pending.append(SOURCE_REGISTRY_RELATIVE)
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
    receipt, authoring = _records()
    assert receipt == build_invocation_implementation_merge_validation_receipt()
    assert authoring == build_frozen_materialization_invocation_operation_authoring_record(receipt)
    assert authoring.gates.materialization_invocation_operation_contract_authored is True
    assert authoring.gates.materialization_invocation_operation_implemented is False


def test_complete_package_verifies_without_effects() -> None:
    result = verify_final_execution_acknowledgement_materialization_invocation_operation_authoring(ROOT)
    assert result.gates.materialization_invocation_implemented is True
    assert result.gates.invocation_adapter_called is False
    assert not (ROOT / ACKNOWLEDGEMENT_RELATIVE).exists()
    assert not (ROOT / EXECUTION_LEASE_V2_RELATIVE).exists()
    assert not (ROOT / DURABLE_HOST_OUTCOME_RELATIVE).exists()


def test_prospective_operation_is_pure_and_complete() -> None:
    result, receipt, authoring = _operation()
    result.require(authoring, receipt)
    assert result.adapter_call_limit == 1
    assert result.standalone_preprobe_permitted is False
    assert result.operation_performed is False
    assert result.invocation_adapter_called is False
    assert not (ROOT / ACKNOWLEDGEMENT_RELATIVE).exists()


def test_operation_phrase_is_distinct_from_acknowledgement_phrase() -> None:
    assert FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_OPERATION_PHRASE != FINAL_EXECUTION_OPERATOR_ACKNOWLEDGEMENT


def test_operation_rejects_wrong_phrase() -> None:
    with pytest.raises(FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError):
        _operation(operation_phrase="wrong")


def test_operation_rejects_empty_operator() -> None:
    with pytest.raises(FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError):
        _operation(operation_operator_identity="")


def test_operation_rejects_operator_mismatch() -> None:
    with pytest.raises(FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError):
        _operation(operation_operator_identity="other@example.invalid")


def test_operation_rejects_authorization_before_merge() -> None:
    with pytest.raises(FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError):
        _operation(operation_authorized_at_utc="2026-07-31T03:55:42Z")


def test_operation_rejects_authorization_before_acknowledgement() -> None:
    with pytest.raises(FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError):
        _operation(operation_authorized_at_utc="2026-07-31T03:59:59Z")


def test_operation_rejects_authorization_after_issuance() -> None:
    with pytest.raises(FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError):
        _operation(operation_authorized_at_utc="2026-07-31T04:02:01Z")


def test_operation_rejects_invocation_identity_drift() -> None:
    invocation = replace(_invocation(), acknowledgement_relative="wrong.json")
    with pytest.raises(FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError):
        _operation(invocation=invocation)


def test_operation_rejects_invocation_effect_drift() -> None:
    invocation = replace(_invocation(), materializer_called=True)
    with pytest.raises(FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError):
        _operation(invocation=invocation)


def test_operation_rejects_operation_identity_drift() -> None:
    result, receipt, authoring = _operation()
    altered = replace(result, invocation_adapter_symbol="wrong")
    with pytest.raises(FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError):
        altered.require(authoring, receipt)


def test_operation_recovery_contract_is_explicit() -> None:
    _, authoring = _records()
    contract = authoring.contract
    assert contract.adapter_owned_recovery_probe_required is True
    assert contract.standalone_preprobe_forbidden is True
    assert contract.automatic_retry_forbidden is True
    assert contract.blind_retry_forbidden is True
    assert contract.explicit_recovery_permitted is True
    assert contract.valid_existing_target_treated_as_success is True
    assert contract.invalid_existing_target_fail_closed is True


def test_source_registry_rejects_operation_authoring_drift(tmp_path: Path) -> None:
    copied = _copy_minimal_repository(tmp_path)
    module = copied / MODULE_RELATIVE
    module.write_text(module.read_text(encoding="utf-8") + "\n# drift\n", encoding="utf-8")
    with pytest.raises(FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError):
        verify_final_execution_acknowledgement_materialization_invocation_operation_authoring(copied)


def test_existing_acknowledgement_closes_operation_authoring(tmp_path: Path) -> None:
    copied = _copy_minimal_repository(tmp_path)
    target = copied / ACKNOWLEDGEMENT_RELATIVE
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("{}", encoding="utf-8")
    with pytest.raises(FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError):
        verify_final_execution_acknowledgement_materialization_invocation_operation_authoring(copied)


def test_existing_legacy_lease_closes_operation_authoring(tmp_path: Path) -> None:
    copied = _copy_minimal_repository(tmp_path)
    target = copied / LEGACY_EXECUTION_LEASE_RELATIVE
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("{}", encoding="utf-8")
    with pytest.raises(FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError):
        verify_final_execution_acknowledgement_materialization_invocation_operation_authoring(copied)


def test_authoring_module_and_verifier_are_effect_free_and_future_operation_absent() -> None:
    forbidden = {
        "invoke_final_execution_acknowledgement_materialization",
        "probe_final_execution_acknowledgement_state",
        "materialize_final_execution_acknowledgement",
        "persist_final_execution_acknowledgement",
    }
    for relative in (MODULE_RELATIVE, VERIFIER_RELATIVE):
        tree = ast.parse((ROOT / relative).read_text(encoding="utf-8"))
        calls = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        assert calls.isdisjoint(forbidden)
    for relative in (MODULE_RELATIVE, VERIFIER_RELATIVE, TEST_RELATIVE, ADR_RU_RELATIVE, ADR_EN_RELATIVE):
        assert (ROOT / relative).is_file()
    assert not (ROOT / FUTURE_OPERATION_IMPLEMENTATION_RELATIVE).exists()
    assert not (ROOT / ACKNOWLEDGEMENT_RELATIVE).exists()
