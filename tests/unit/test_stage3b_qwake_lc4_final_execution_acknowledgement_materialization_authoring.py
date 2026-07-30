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
    load_final_execution_acknowledgement_authoring,
    load_wiring_merge_validation_receipt,
)
from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_issuance_authoring import (
    ACKNOWLEDGEMENT_RELATIVE,
    AUTHORING_MERGE_RECEIPT_RELATIVE,
    AUTHORING_RECORD_RELATIVE,
    UPSTREAM_AUTHORING_RECORD_RELATIVE,
    UPSTREAM_WIRING_RECEIPT_RELATIVE,
    load_acknowledgement_authoring_merge_validation_receipt,
    load_final_execution_acknowledgement_issuance_authoring,
)
from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_issuance_implementation import (
    LEGACY_EXECUTION_LEASE_RELATIVE,
)
from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_materialization_authoring import (
    ADR_EN_RELATIVE,
    ADR_RU_RELATIVE,
    IMPLEMENTATION_MERGE_RECEIPT_RELATIVE,
    MODULE_RELATIVE,
    PACKAGE_RELATIVE,
    SOURCE_REGISTRY_RELATIVE,
    TEST_RELATIVE,
    VERIFIER_RELATIVE,
    FinalExecutionAcknowledgementMaterializationAuthoringError,
    build_acknowledgement_issuance_implementation_merge_validation_receipt,
    build_frozen_materialization_authoring_record,
    build_prospective_acknowledgement_materialization,
    load_acknowledgement_issuance_implementation_merge_validation_receipt,
    load_final_execution_acknowledgement_materialization_authoring,
    verify_final_execution_acknowledgement_materialization_authoring,
)
from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_materialization_authoring import (
    AUTHORING_RECORD_RELATIVE as MATERIALIZATION_AUTHORING_RECORD_RELATIVE,
)

ROOT = Path(__file__).resolve().parents[2]


def _records():
    receipt = load_acknowledgement_issuance_implementation_merge_validation_receipt(
        ROOT / IMPLEMENTATION_MERGE_RECEIPT_RELATIVE
    )
    authoring = load_final_execution_acknowledgement_materialization_authoring(
        ROOT / MATERIALIZATION_AUTHORING_RECORD_RELATIVE,
        receipt,
    )
    issuance_receipt = load_acknowledgement_authoring_merge_validation_receipt(
        ROOT / AUTHORING_MERGE_RECEIPT_RELATIVE
    )
    issuance_authoring = load_final_execution_acknowledgement_issuance_authoring(
        ROOT / AUTHORING_RECORD_RELATIVE,
        issuance_receipt,
    )
    upstream_receipt = load_wiring_merge_validation_receipt(
        ROOT / UPSTREAM_WIRING_RECEIPT_RELATIVE
    )
    upstream_authoring = load_final_execution_acknowledgement_authoring(
        ROOT / UPSTREAM_AUTHORING_RECORD_RELATIVE,
        upstream_receipt,
    )
    return (
        receipt,
        authoring,
        issuance_receipt,
        issuance_authoring,
        upstream_receipt,
        upstream_authoring,
    )


def _materialization(**overrides: str):
    (
        receipt,
        authoring,
        issuance_receipt,
        issuance_authoring,
        upstream_receipt,
        upstream_authoring,
    ) = _records()
    values = {
        "acknowledgement_phrase": FINAL_EXECUTION_OPERATOR_ACKNOWLEDGEMENT,
        "operator_identity": "operator@example.invalid",
        "acknowledged_at_utc": "2026-07-30T19:25:00Z",
        "issuer_identity": "issuer@example.invalid",
        "issued_at_utc": "2026-07-30T19:26:00Z",
        "materializer_identity": "issuer@example.invalid",
        "materialized_at_utc": "2026-07-30T19:27:00Z",
    }
    values.update(overrides)
    result = build_prospective_acknowledgement_materialization(
        authoring,
        receipt,
        issuance_authoring,
        issuance_receipt,
        upstream_authoring,
        upstream_receipt,
        **values,
    )
    return result, _records()


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
    receipt, authoring, *_ = _records()
    assert receipt == (
        build_acknowledgement_issuance_implementation_merge_validation_receipt()
    )
    assert authoring == build_frozen_materialization_authoring_record(receipt)
    assert authoring.gates.acknowledgement_materialization_contract_authored is True
    assert authoring.gates.final_execution_acknowledgement_issued is False


def test_complete_package_verifies_without_effects() -> None:
    result = verify_final_execution_acknowledgement_materialization_authoring(ROOT)
    assert result.gates.acknowledgement_issuance_implemented is True
    assert result.gates.acknowledgement_materialization_implemented is False
    assert not (ROOT / ACKNOWLEDGEMENT_RELATIVE).exists()
    assert not (ROOT / EXECUTION_LEASE_V2_RELATIVE).exists()
    assert not (ROOT / DURABLE_HOST_OUTCOME_RELATIVE).exists()


def test_prospective_materialization_is_pure_and_complete() -> None:
    result, records = _materialization()
    (
        receipt,
        authoring,
        issuance_receipt,
        issuance_authoring,
        upstream_receipt,
        upstream_authoring,
    ) = records
    result.require(
        authoring,
        receipt,
        issuance_authoring,
        issuance_receipt,
        upstream_authoring,
        upstream_receipt,
    )
    assert result.acknowledgement_materialized is False
    assert result.retry_permitted is False
    assert result.materializer_identity == result.issuance.issuer_identity
    assert not (ROOT / ACKNOWLEDGEMENT_RELATIVE).exists()


def test_materialization_rejects_wrong_phrase() -> None:
    with pytest.raises(FinalExecutionAcknowledgementMaterializationAuthoringError):
        _materialization(acknowledgement_phrase="wrong")


def test_materialization_rejects_empty_materializer() -> None:
    with pytest.raises(FinalExecutionAcknowledgementMaterializationAuthoringError):
        _materialization(materializer_identity="")


def test_materialization_rejects_materializer_not_equal_to_issuer() -> None:
    with pytest.raises(FinalExecutionAcknowledgementMaterializationAuthoringError):
        _materialization(materializer_identity="other@example.invalid")


def test_materialization_rejects_acknowledgement_before_implementation_merge() -> None:
    with pytest.raises(FinalExecutionAcknowledgementMaterializationAuthoringError):
        _materialization(acknowledged_at_utc="2026-07-30T19:19:46Z")


def test_materialization_rejects_issuance_before_acknowledgement() -> None:
    with pytest.raises(FinalExecutionAcknowledgementMaterializationAuthoringError):
        _materialization(issued_at_utc="2026-07-30T19:24:00Z")


def test_materialization_rejects_materialization_before_issuance() -> None:
    with pytest.raises(FinalExecutionAcknowledgementMaterializationAuthoringError):
        _materialization(materialized_at_utc="2026-07-30T19:25:30Z")


def test_materialization_rejects_identity_drift() -> None:
    result, records = _materialization()
    (
        receipt,
        authoring,
        issuance_receipt,
        issuance_authoring,
        upstream_receipt,
        upstream_authoring,
    ) = records
    altered = replace(result, acknowledgement_relative="wrong.json")
    with pytest.raises(FinalExecutionAcknowledgementMaterializationAuthoringError):
        altered.require(
            authoring,
            receipt,
            issuance_authoring,
            issuance_receipt,
            upstream_authoring,
            upstream_receipt,
        )


def test_source_registry_rejects_materialization_source_drift(tmp_path: Path) -> None:
    copied = _copy_minimal_repository(tmp_path)
    module = copied / MODULE_RELATIVE
    module.write_text(
        module.read_text(encoding="utf-8") + "\n# drift\n",
        encoding="utf-8",
    )
    with pytest.raises(FinalExecutionAcknowledgementMaterializationAuthoringError):
        verify_final_execution_acknowledgement_materialization_authoring(copied)


def test_existing_acknowledgement_closes_authoring(tmp_path: Path) -> None:
    copied = _copy_minimal_repository(tmp_path)
    target = copied / ACKNOWLEDGEMENT_RELATIVE
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("{}", encoding="utf-8")
    with pytest.raises(FinalExecutionAcknowledgementMaterializationAuthoringError):
        verify_final_execution_acknowledgement_materialization_authoring(copied)


def test_authoring_module_and_verifier_are_effect_free() -> None:
    forbidden_names = {
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
    assert not (ROOT / LEGACY_EXECUTION_LEASE_RELATIVE).exists()
