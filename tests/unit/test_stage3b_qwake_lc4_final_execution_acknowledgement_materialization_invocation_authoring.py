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
    ADR_EN_RELATIVE,
    ADR_RU_RELATIVE,
    AUTHORING_RECORD_RELATIVE,
    IMPLEMENTATION_MERGE_RECEIPT_RELATIVE,
    MODULE_RELATIVE,
    PACKAGE_RELATIVE,
    SOURCE_REGISTRY_RELATIVE,
    TEST_RELATIVE,
    VERIFIER_RELATIVE,
    FinalExecutionAcknowledgementMaterializationInvocationAuthoringError,
    build_frozen_materialization_invocation_authoring_record,
    build_materialization_implementation_merge_validation_receipt,
    build_prospective_acknowledgement_materialization_invocation,
    load_final_execution_acknowledgement_materialization_invocation_authoring,
    load_materialization_implementation_merge_validation_receipt,
    verify_final_execution_acknowledgement_materialization_invocation_authoring,
)

ROOT = Path(__file__).resolve().parents[2]


def _records():
    receipt = load_materialization_implementation_merge_validation_receipt(
        ROOT / IMPLEMENTATION_MERGE_RECEIPT_RELATIVE
    )
    authoring = (
        load_final_execution_acknowledgement_materialization_invocation_authoring(
            ROOT / AUTHORING_RECORD_RELATIVE,
            receipt,
        )
    )
    return receipt, authoring


def _invocation(**overrides: str):
    receipt, authoring = _records()
    values = {
        "acknowledgement_phrase": FINAL_EXECUTION_OPERATOR_ACKNOWLEDGEMENT,
        "operator_identity": "operator@example.invalid",
        "acknowledged_at_utc": "2026-07-30T22:45:00Z",
        "issuer_identity": "issuer@example.invalid",
        "issued_at_utc": "2026-07-30T22:46:00Z",
        "materializer_identity": "issuer@example.invalid",
        "materialized_at_utc": "2026-07-30T22:47:00Z",
    }
    values.update(overrides)
    result = build_prospective_acknowledgement_materialization_invocation(
        authoring,
        receipt,
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
            child = (
                relative.parent / entry
                if source.name == "SHA256SUMS"
                else Path(entry)
            )
            if child not in copied_paths:
                pending.append(child)

    (copied / "results/stage-3").mkdir(parents=True, exist_ok=True)
    return copied


def test_frozen_records_are_exact() -> None:
    receipt, authoring = _records()
    assert receipt == build_materialization_implementation_merge_validation_receipt()
    assert authoring == build_frozen_materialization_invocation_authoring_record(
        receipt
    )
    assert authoring.gates.materialization_invocation_contract_authored is True
    assert authoring.gates.materialization_invocation_implemented is False


def test_complete_package_verifies_without_effects() -> None:
    result = verify_final_execution_acknowledgement_materialization_invocation_authoring(
        ROOT
    )
    assert result.gates.acknowledgement_materialization_implemented is True
    assert result.gates.materialization_invoked is False
    assert not (ROOT / ACKNOWLEDGEMENT_RELATIVE).exists()
    assert not (ROOT / EXECUTION_LEASE_V2_RELATIVE).exists()
    assert not (ROOT / DURABLE_HOST_OUTCOME_RELATIVE).exists()


def test_prospective_invocation_is_pure_and_complete() -> None:
    result, receipt, authoring = _invocation()
    result.require(authoring, receipt)
    assert result.materializer_call_limit == 1
    assert result.automatic_retry_permitted is False
    assert result.blind_retry_permitted is False
    assert result.explicit_recovery_permitted is True
    assert result.materialization_invoked is False
    assert not (ROOT / ACKNOWLEDGEMENT_RELATIVE).exists()


def test_invocation_rejects_wrong_phrase() -> None:
    with pytest.raises(
        FinalExecutionAcknowledgementMaterializationInvocationAuthoringError
    ):
        _invocation(acknowledgement_phrase="wrong")


def test_invocation_rejects_empty_operator() -> None:
    with pytest.raises(
        FinalExecutionAcknowledgementMaterializationInvocationAuthoringError
    ):
        _invocation(operator_identity="")


def test_invocation_rejects_empty_issuer() -> None:
    with pytest.raises(
        FinalExecutionAcknowledgementMaterializationInvocationAuthoringError
    ):
        _invocation(issuer_identity="", materializer_identity="")


def test_invocation_rejects_materializer_not_equal_to_issuer() -> None:
    with pytest.raises(
        FinalExecutionAcknowledgementMaterializationInvocationAuthoringError
    ):
        _invocation(materializer_identity="other@example.invalid")


def test_invocation_rejects_acknowledgement_not_after_merge() -> None:
    with pytest.raises(
        FinalExecutionAcknowledgementMaterializationInvocationAuthoringError
    ):
        _invocation(acknowledged_at_utc="2026-07-30T22:40:10Z")


def test_invocation_rejects_issuance_before_acknowledgement() -> None:
    with pytest.raises(
        FinalExecutionAcknowledgementMaterializationInvocationAuthoringError
    ):
        _invocation(issued_at_utc="2026-07-30T22:44:00Z")


def test_invocation_rejects_materialization_before_issuance() -> None:
    with pytest.raises(
        FinalExecutionAcknowledgementMaterializationInvocationAuthoringError
    ):
        _invocation(materialized_at_utc="2026-07-30T22:45:30Z")


def test_invocation_rejects_identity_drift() -> None:
    result, receipt, authoring = _invocation()
    altered = replace(result, acknowledgement_relative="wrong.json")
    with pytest.raises(
        FinalExecutionAcknowledgementMaterializationInvocationAuthoringError
    ):
        altered.require(authoring, receipt)


def test_recovery_contract_is_explicit_not_automatic() -> None:
    _, authoring = _records()
    contract = authoring.contract
    assert contract.automatic_retry_forbidden is True
    assert contract.blind_retry_forbidden is True
    assert contract.explicit_recovery_permitted is True
    assert contract.recovery_state_probe_required is True
    assert contract.absent_target_requires_new_explicit_authorization is True
    assert contract.valid_existing_target_treated_as_success is True
    assert contract.invalid_existing_target_fail_closed is True
    assert contract.target_exists_materializer_recall_forbidden is True


def test_source_registry_rejects_authoring_source_drift(tmp_path: Path) -> None:
    copied = _copy_minimal_repository(tmp_path)
    module = copied / MODULE_RELATIVE
    module.write_text(
        module.read_text(encoding="utf-8") + "\n# drift\n",
        encoding="utf-8",
    )
    with pytest.raises(
        FinalExecutionAcknowledgementMaterializationInvocationAuthoringError
    ):
        verify_final_execution_acknowledgement_materialization_invocation_authoring(
            copied
        )


def test_existing_acknowledgement_closes_authoring(tmp_path: Path) -> None:
    copied = _copy_minimal_repository(tmp_path)
    target = copied / ACKNOWLEDGEMENT_RELATIVE
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("{}", encoding="utf-8")
    with pytest.raises(
        FinalExecutionAcknowledgementMaterializationInvocationAuthoringError
    ):
        verify_final_execution_acknowledgement_materialization_invocation_authoring(
            copied
        )


def test_existing_legacy_lease_closes_authoring(tmp_path: Path) -> None:
    copied = _copy_minimal_repository(tmp_path)
    target = copied / LEGACY_EXECUTION_LEASE_RELATIVE
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("{}", encoding="utf-8")
    with pytest.raises(
        FinalExecutionAcknowledgementMaterializationInvocationAuthoringError
    ):
        verify_final_execution_acknowledgement_materialization_invocation_authoring(
            copied
        )


def test_authoring_module_and_verifier_are_effect_free() -> None:
    forbidden_names = {
        "materialize_final_execution_acknowledgement",
        "persist_final_execution_acknowledgement",
        "invoke_lease_bound_host_runtime",
        "materialize_invocation_command",
    }
    for relative in (MODULE_RELATIVE, VERIFIER_RELATIVE):
        tree = ast.parse((ROOT / relative).read_text(encoding="utf-8"))
        calls = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        assert calls.isdisjoint(forbidden_names)
    for relative in (MODULE_RELATIVE, VERIFIER_RELATIVE, TEST_RELATIVE):
        assert (ROOT / relative).is_file()
    for relative in (ADR_RU_RELATIVE, ADR_EN_RELATIVE):
        assert (ROOT / relative).is_file()
    assert not (ROOT / ACKNOWLEDGEMENT_RELATIVE).exists()
