from __future__ import annotations

import ast
import shutil
from dataclasses import replace
from pathlib import Path

import pytest

from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_authoring import (
    ADR_EN_RELATIVE,
    ADR_RU_RELATIVE,
    AUTHORING_BASE_COMMIT,
    AUTHORING_RECORD_RELATIVE,
    AUTHORIZED_OUTPUT_ROOT,
    DURABLE_HOST_OUTCOME_RELATIVE,
    EXECUTION_LEASE_V2_RELATIVE,
    FINAL_EXECUTION_ACKNOWLEDGEMENT_AUTHORING_ID,
    FINAL_EXECUTION_OPERATOR_ACKNOWLEDGEMENT,
    MODULE_RELATIVE,
    PACKAGE_RELATIVE,
    SOURCE_REGISTRY_RELATIVE,
    TEST_RELATIVE,
    VERIFIER_RELATIVE,
    WIRING_MERGE_COMMIT,
    WIRING_MERGE_RECEIPT_RELATIVE,
    FinalExecutionAcknowledgementAuthoringError,
    build_final_execution_acknowledgement,
    load_final_execution_acknowledgement_authoring,
    load_wiring_merge_validation_receipt,
    sha256_bytes,
    verify_final_execution_acknowledgement_authoring,
)

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / PACKAGE_RELATIVE
AUTHORING_RECORD = ROOT / AUTHORING_RECORD_RELATIVE
MERGE_RECEIPT = ROOT / WIRING_MERGE_RECEIPT_RELATIVE
SOURCE_REGISTRY = ROOT / SOURCE_REGISTRY_RELATIVE
LEASE_V2 = ROOT / EXECUTION_LEASE_V2_RELATIVE
OUTCOME = ROOT / DURABLE_HOST_OUTCOME_RELATIVE


def _registry(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="strict").splitlines():
        digest, relative = line.split("  ", 1)
        result[relative] = "sha256:" + digest
    return result


def _records():
    receipt = load_wiring_merge_validation_receipt(MERGE_RECEIPT)
    authoring = load_final_execution_acknowledgement_authoring(
        AUTHORING_RECORD,
        receipt,
    )
    return receipt, authoring


def _copy_minimal_repository(destination: Path) -> Path:
    copied = destination / "repo"
    paths = set(_registry(SOURCE_REGISTRY))
    paths.update(
        {
            (PACKAGE_RELATIVE / "SHA256SUMS").as_posix(),
            (PACKAGE_RELATIVE / "source-SHA256SUMS").as_posix(),
            (PACKAGE_RELATIVE / "authoring.json").as_posix(),
            (PACKAGE_RELATIVE / "wiring-merge-validation.json").as_posix(),
        }
    )
    for relative in sorted(paths):
        source = ROOT / relative
        target = copied / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return copied


def test_authoring_package_is_exact_and_registered() -> None:
    assert sorted(path.name for path in PACKAGE.iterdir()) == [
        "SHA256SUMS",
        "authoring.json",
        "source-SHA256SUMS",
        "wiring-merge-validation.json",
    ]
    registry = _registry(PACKAGE / "SHA256SUMS")
    assert registry == {
        "authoring.json": sha256_bytes(AUTHORING_RECORD.read_bytes()),
        "source-SHA256SUMS": sha256_bytes(SOURCE_REGISTRY.read_bytes()),
        "wiring-merge-validation.json": sha256_bytes(MERGE_RECEIPT.read_bytes()),
    }


def test_authoring_and_merge_receipt_are_canonical() -> None:
    receipt, authoring = _records()
    assert MERGE_RECEIPT.read_text(encoding="utf-8") == receipt.canonical_json()
    assert AUTHORING_RECORD.read_text(encoding="utf-8") == authoring.canonical_json(
        receipt
    )
    assert authoring.authoring_id == FINAL_EXECUTION_ACKNOWLEDGEMENT_AUTHORING_ID
    assert authoring.source.authoring_base_commit == AUTHORING_BASE_COMMIT
    assert authoring.source.wiring_merge_commit == WIRING_MERGE_COMMIT


def test_complete_execution_identity_chain_is_bound() -> None:
    authoring = verify_final_execution_acknowledgement_authoring(ROOT)
    source = authoring.source
    assert source.wiring_pr_number == 146
    assert source.invocation_count == 1
    assert source.invocation_authorization_sha256.startswith("sha256:")
    assert source.execution_authorization_sha256.startswith("sha256:")
    assert source.preexecution_verification_sha256.startswith("sha256:")
    assert source.runtime_operation_sha256.startswith("sha256:")
    assert source.identity_repair_sha256.startswith("sha256:")
    assert source.image_repo_digest.startswith("torch2pc-layerwise-thesis@sha256:")


def test_authoring_is_not_an_issued_acknowledgement() -> None:
    _, authoring = _records()
    assert authoring.gates.final_execution_acknowledgement_authored is True
    assert authoring.gates.final_execution_acknowledgement_issued is False
    assert authoring.gates.final_execution_acknowledged is False
    assert authoring.gates.one_shot_engineering_invocation_permitted is False
    assert authoring.gates.execution_lease_materialized is False
    assert authoring.gates.authorization_consumed is False


def test_prospective_acknowledgement_is_pure_and_complete() -> None:
    receipt, authoring = _records()
    result = build_final_execution_acknowledgement(
        authoring,
        receipt,
        acknowledgement_phrase=FINAL_EXECUTION_OPERATOR_ACKNOWLEDGEMENT,
        operator_identity="operator@example.invalid",
        acknowledged_at_utc="2026-07-30T15:00:30Z",
    )
    assert result.acknowledgement_authoring_sha256 == authoring.authoring_sha256
    assert result.wiring_merge_commit == WIRING_MERGE_COMMIT
    assert result.invocation_count == 1
    assert result.single_attempt_only is True
    assert result.retry_permitted is False
    assert result.execution_lease_materialized is False
    assert result.authorization_consumed is False
    assert not LEASE_V2.exists()
    assert not OUTCOME.exists()


def test_prospective_acknowledgement_rejects_wrong_phrase() -> None:
    receipt, authoring = _records()
    with pytest.raises(
        FinalExecutionAcknowledgementAuthoringError,
        match="phrase differs",
    ):
        build_final_execution_acknowledgement(
            authoring,
            receipt,
            acknowledgement_phrase="ACKNOWLEDGE_SOMETHING_ELSE",
            operator_identity="operator@example.invalid",
            acknowledged_at_utc="2026-07-30T15:00:30Z",
        )


def test_prospective_acknowledgement_rejects_bad_operator_or_time() -> None:
    receipt, authoring = _records()
    with pytest.raises(
        FinalExecutionAcknowledgementAuthoringError,
        match="operator identity",
    ):
        build_final_execution_acknowledgement(
            authoring,
            receipt,
            acknowledgement_phrase=FINAL_EXECUTION_OPERATOR_ACKNOWLEDGEMENT,
            operator_identity="",
            acknowledged_at_utc="2026-07-30T15:00:30Z",
        )
    with pytest.raises(
        FinalExecutionAcknowledgementAuthoringError,
        match="not after wiring merge",
    ):
        build_final_execution_acknowledgement(
            authoring,
            receipt,
            acknowledgement_phrase=FINAL_EXECUTION_OPERATOR_ACKNOWLEDGEMENT,
            operator_identity="operator@example.invalid",
            acknowledged_at_utc="2026-07-30T14:37:25Z",
        )


def test_prospective_acknowledgement_rejects_identity_drift() -> None:
    receipt, authoring = _records()
    result = build_final_execution_acknowledgement(
        authoring,
        receipt,
        acknowledgement_phrase=FINAL_EXECUTION_OPERATOR_ACKNOWLEDGEMENT,
        operator_identity="operator@example.invalid",
        acknowledged_at_utc="2026-07-30T15:00:30Z",
    )
    with pytest.raises(
        FinalExecutionAcknowledgementAuthoringError,
        match="prospective acknowledgement differs",
    ):
        replace(
            result,
            lease_bound_host_invoker_wiring_sha256="sha256:" + "0" * 64,
        ).require(authoring, receipt)


def test_source_registry_rejects_authoring_source_drift(tmp_path: Path) -> None:
    copied = _copy_minimal_repository(tmp_path)
    target = copied / MODULE_RELATIVE
    target.write_text(
        target.read_text(encoding="utf-8") + "\n# drift\n",
        encoding="utf-8",
    )
    with pytest.raises(
        FinalExecutionAcknowledgementAuthoringError,
        match="registry digest differs",
    ):
        verify_final_execution_acknowledgement_authoring(copied)


def test_existing_runtime_boundary_artifact_closes_authoring(tmp_path: Path) -> None:
    copied = _copy_minimal_repository(tmp_path)
    lease = copied / EXECUTION_LEASE_V2_RELATIVE
    lease.parent.mkdir(parents=True, exist_ok=True)
    lease.write_text("{}\n", encoding="utf-8")
    with pytest.raises(
        FinalExecutionAcknowledgementAuthoringError,
        match="execution lease v2 exists",
    ):
        verify_final_execution_acknowledgement_authoring(copied)


def test_authoring_module_and_verifier_contain_no_runtime_effect_call() -> None:
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
    assert AUTHORIZED_OUTPUT_ROOT not in {
        path.as_posix() for path in ROOT.glob("results/stage-3/*")
    }
