from __future__ import annotations

import ast
import shutil
from dataclasses import replace
from pathlib import Path

import pytest

from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_authoring import (
    FINAL_EXECUTION_OPERATOR_ACKNOWLEDGEMENT,
    FinalExecutionAcknowledgementAuthoringError,
    load_final_execution_acknowledgement_authoring,
    load_wiring_merge_validation_receipt,
)
from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_issuance_authoring import (
    ACKNOWLEDGEMENT_RELATIVE,
    ADR_EN_RELATIVE,
    ADR_RU_RELATIVE,
    AUTHORING_MERGE_RECEIPT_RELATIVE,
    AUTHORING_RECORD_RELATIVE,
    DURABLE_HOST_OUTCOME_RELATIVE,
    EXECUTION_LEASE_V2_RELATIVE,
    MODULE_RELATIVE,
    PACKAGE_RELATIVE,
    SOURCE_REGISTRY_RELATIVE,
    TEST_RELATIVE,
    UPSTREAM_AUTHORING_RECORD_RELATIVE,
    UPSTREAM_WIRING_RECEIPT_RELATIVE,
    VERIFIER_RELATIVE,
    FinalExecutionAcknowledgementIssuanceAuthoringError,
    build_acknowledgement_authoring_merge_validation_receipt,
    build_frozen_issuance_authoring_record,
    build_prospective_acknowledgement_issuance,
    load_acknowledgement_authoring_merge_validation_receipt,
    load_final_execution_acknowledgement_issuance_authoring,
    verify_final_execution_acknowledgement_issuance_authoring,
)

ROOT = Path(__file__).resolve().parents[2]


def _records():
    receipt = load_acknowledgement_authoring_merge_validation_receipt(
        ROOT / AUTHORING_MERGE_RECEIPT_RELATIVE
    )
    authoring = load_final_execution_acknowledgement_issuance_authoring(
        ROOT / AUTHORING_RECORD_RELATIVE,
        receipt,
    )
    upstream_receipt = load_wiring_merge_validation_receipt(
        ROOT / UPSTREAM_WIRING_RECEIPT_RELATIVE
    )
    upstream_authoring = load_final_execution_acknowledgement_authoring(
        ROOT / UPSTREAM_AUTHORING_RECORD_RELATIVE,
        upstream_receipt,
    )
    return receipt, authoring, upstream_receipt, upstream_authoring


def _copy_minimal_repository(tmp_path: Path) -> Path:
    copied = tmp_path / "repository"
    copied.mkdir()
    source_paths = {}
    for line in (ROOT / SOURCE_REGISTRY_RELATIVE).read_text(
        encoding="utf-8"
    ).splitlines():
        _, relative = line.split("  ", 1)
        source_paths[relative] = None
    upstream_registry = (
        ROOT / UPSTREAM_AUTHORING_RECORD_RELATIVE.parent / "source-SHA256SUMS"
    )
    for line in upstream_registry.read_text(encoding="utf-8").splitlines():
        _, relative = line.split("  ", 1)
        source_paths[relative] = None
    for relative in source_paths:
        source = ROOT / relative
        target = copied / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    target_package = copied / PACKAGE_RELATIVE
    target_package.mkdir(parents=True, exist_ok=True)
    for source in (ROOT / PACKAGE_RELATIVE).iterdir():
        shutil.copy2(source, target_package / source.name)
    return copied


def test_frozen_records_are_exact() -> None:
    receipt, authoring, _, _ = _records()
    assert receipt == build_acknowledgement_authoring_merge_validation_receipt()
    assert authoring == build_frozen_issuance_authoring_record(receipt)
    assert authoring.gates.acknowledgement_issuance_contract_authored is True
    assert authoring.gates.acknowledgement_issuance_implemented is False
    assert authoring.gates.final_execution_acknowledgement_issued is False


def test_complete_package_verifies_without_effects() -> None:
    result = verify_final_execution_acknowledgement_issuance_authoring(ROOT)
    assert result.gates.final_execution_acknowledgement_issued is False
    assert not (ROOT / ACKNOWLEDGEMENT_RELATIVE).exists()
    assert not (ROOT / EXECUTION_LEASE_V2_RELATIVE).exists()
    assert not (ROOT / DURABLE_HOST_OUTCOME_RELATIVE).exists()


def test_prospective_issuance_is_pure_and_complete() -> None:
    receipt, authoring, upstream_receipt, upstream_authoring = _records()
    result = build_prospective_acknowledgement_issuance(
        authoring,
        receipt,
        upstream_authoring,
        upstream_receipt,
        acknowledgement_phrase=FINAL_EXECUTION_OPERATOR_ACKNOWLEDGEMENT,
        operator_identity="operator@example.invalid",
        acknowledged_at_utc="2026-07-30T16:10:00Z",
        issuer_identity="issuer@example.invalid",
        issued_at_utc="2026-07-30T16:11:00Z",
    )
    assert result.acknowledgement.operator_identity == "operator@example.invalid"
    assert result.issuer_identity == "issuer@example.invalid"
    assert result.exclusive_no_overwrite is True
    assert result.acknowledgement_materialized is False
    assert result.one_shot_engineering_invocation_permitted is False
    assert not (ROOT / ACKNOWLEDGEMENT_RELATIVE).exists()


def test_prospective_issuance_rejects_wrong_phrase() -> None:
    receipt, authoring, upstream_receipt, upstream_authoring = _records()
    with pytest.raises(FinalExecutionAcknowledgementAuthoringError):
        build_prospective_acknowledgement_issuance(
            authoring,
            receipt,
            upstream_authoring,
            upstream_receipt,
            acknowledgement_phrase="WRONG",
            operator_identity="operator@example.invalid",
            acknowledged_at_utc="2026-07-30T16:10:00Z",
            issuer_identity="issuer@example.invalid",
            issued_at_utc="2026-07-30T16:11:00Z",
        )


def test_prospective_issuance_rejects_empty_issuer() -> None:
    receipt, authoring, upstream_receipt, upstream_authoring = _records()
    with pytest.raises(
        FinalExecutionAcknowledgementIssuanceAuthoringError,
        match="issuer identity",
    ):
        build_prospective_acknowledgement_issuance(
            authoring,
            receipt,
            upstream_authoring,
            upstream_receipt,
            acknowledgement_phrase=FINAL_EXECUTION_OPERATOR_ACKNOWLEDGEMENT,
            operator_identity="operator@example.invalid",
            acknowledged_at_utc="2026-07-30T16:10:00Z",
            issuer_identity="",
            issued_at_utc="2026-07-30T16:11:00Z",
        )


def test_prospective_issuance_rejects_time_before_authoring_merge() -> None:
    receipt, authoring, upstream_receipt, upstream_authoring = _records()
    with pytest.raises(
        FinalExecutionAcknowledgementIssuanceAuthoringError,
        match="not after authoring merge",
    ):
        build_prospective_acknowledgement_issuance(
            authoring,
            receipt,
            upstream_authoring,
            upstream_receipt,
            acknowledgement_phrase=FINAL_EXECUTION_OPERATOR_ACKNOWLEDGEMENT,
            operator_identity="operator@example.invalid",
            acknowledged_at_utc="2026-07-30T16:03:05Z",
            issuer_identity="issuer@example.invalid",
            issued_at_utc="2026-07-30T16:11:00Z",
        )


def test_prospective_issuance_rejects_issue_before_acknowledgement() -> None:
    receipt, authoring, upstream_receipt, upstream_authoring = _records()
    with pytest.raises(
        FinalExecutionAcknowledgementIssuanceAuthoringError,
        match="before acknowledgement",
    ):
        build_prospective_acknowledgement_issuance(
            authoring,
            receipt,
            upstream_authoring,
            upstream_receipt,
            acknowledgement_phrase=FINAL_EXECUTION_OPERATOR_ACKNOWLEDGEMENT,
            operator_identity="operator@example.invalid",
            acknowledged_at_utc="2026-07-30T16:11:00Z",
            issuer_identity="issuer@example.invalid",
            issued_at_utc="2026-07-30T16:10:00Z",
        )


def test_prospective_issuance_rejects_identity_drift() -> None:
    receipt, authoring, upstream_receipt, upstream_authoring = _records()
    result = build_prospective_acknowledgement_issuance(
        authoring,
        receipt,
        upstream_authoring,
        upstream_receipt,
        acknowledgement_phrase=FINAL_EXECUTION_OPERATOR_ACKNOWLEDGEMENT,
        operator_identity="operator@example.invalid",
        acknowledged_at_utc="2026-07-30T16:10:00Z",
        issuer_identity="issuer@example.invalid",
        issued_at_utc="2026-07-30T16:11:00Z",
    )
    with pytest.raises(
        FinalExecutionAcknowledgementIssuanceAuthoringError,
        match="prospective issuance differs",
    ):
        replace(result, acknowledgement_relative="wrong.json").require(
            authoring,
            receipt,
            upstream_authoring,
            upstream_receipt,
        )


def test_source_registry_rejects_issuance_source_drift(tmp_path: Path) -> None:
    copied = _copy_minimal_repository(tmp_path)
    target = copied / MODULE_RELATIVE
    target.write_text(
        target.read_text(encoding="utf-8") + "\n# drift\n",
        encoding="utf-8",
    )
    with pytest.raises(
        FinalExecutionAcknowledgementIssuanceAuthoringError,
        match="registry digest differs",
    ):
        verify_final_execution_acknowledgement_issuance_authoring(copied)


def test_existing_acknowledgement_closes_authoring(tmp_path: Path) -> None:
    copied = _copy_minimal_repository(tmp_path)
    target = copied / ACKNOWLEDGEMENT_RELATIVE
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("{}\n", encoding="utf-8")
    with pytest.raises(
        FinalExecutionAcknowledgementIssuanceAuthoringError,
        match="final execution acknowledgement exists",
    ):
        verify_final_execution_acknowledgement_issuance_authoring(copied)


def test_authoring_module_and_verifier_are_effect_free() -> None:
    module_tree = ast.parse((ROOT / MODULE_RELATIVE).read_text(encoding="utf-8"))
    verifier_tree = ast.parse((ROOT / VERIFIER_RELATIVE).read_text(encoding="utf-8"))
    forbidden = {
        "invoke_lease_bound_host_runtime",
        "invoke_one_shot_host_runtime",
        "persist_persistent_execution_lease_v2",
        "persist_durable_host_outcome_receipt",
        "inspect_local_image",
        "materialize_invocation_command",
    }
    for tree in (module_tree, verifier_tree):
        calls = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        assert calls.isdisjoint(forbidden)
    assert (ROOT / ADR_RU_RELATIVE).is_file()
    assert (ROOT / ADR_EN_RELATIVE).is_file()
    assert (ROOT / TEST_RELATIVE).is_file()
