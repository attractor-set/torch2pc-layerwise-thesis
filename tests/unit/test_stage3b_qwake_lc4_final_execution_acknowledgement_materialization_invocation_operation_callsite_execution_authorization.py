from __future__ import annotations

import ast
import importlib.util
import json
import shutil
from dataclasses import replace
from pathlib import Path
from types import ModuleType

import pytest

from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_authoring import (
    DURABLE_HOST_OUTCOME_RELATIVE,
    EXECUTION_LEASE_V2_RELATIVE,
    canonical_json,
    sha256_bytes,
)
from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_issuance_authoring import (
    ACKNOWLEDGEMENT_RELATIVE,
)
from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_issuance_implementation import (
    LEGACY_EXECUTION_LEASE_RELATIVE,
)
from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authorization import (
    ADR_EN_RELATIVE,
    ADR_RU_RELATIVE,
    AUTHORIZATION_RELATIVE,
    EXECUTION_AUTHORING_MERGE_RECEIPT_RELATIVE,
    EXECUTION_AUTHORIZATION_ID,
    EXECUTION_AUTHORIZATION_PHRASE,
    MODULE_RELATIVE,
    OPERATION_JSON_RELATIVE,
    PACKAGE_RELATIVE,
    REGISTRY_RELATIVE,
    SOURCE_REGISTRY_RELATIVE,
    TEST_RELATIVE,
    VERIFIER_RELATIVE,
    FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError,
    build_execution_authoring_merge_validation_receipt,
    build_expected_operation,
    build_frozen_execution_authorization,
    load_execution_authoring_merge_validation_receipt,
    load_execution_authorization,
    verify_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authorization,
)
from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_callsite_implementation import (
    PRODUCTION_CALLSITE_RELATIVE,
    load_canonical_prospective_operation,
)

ROOT = Path(__file__).resolve().parents[2]


def _copy_repository(tmp_path: Path, name: str = "repository") -> Path:
    target = tmp_path / name
    shutil.copytree(
        ROOT,
        target,
        ignore=shutil.ignore_patterns(
            ".git",
            ".mypy_cache",
            ".pytest_cache",
            ".ruff_cache",
            "__pycache__",
            "site",
            "site_ru",
            "site_en",
        ),
    )
    return target


def _verifier_module() -> ModuleType:
    path = ROOT / VERIFIER_RELATIVE
    spec = importlib.util.spec_from_file_location(
        "qwake_execution_authorization_verifier_under_test",
        path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_receipt_builder_matches_frozen_receipt() -> None:
    expected = build_execution_authoring_merge_validation_receipt()
    observed = load_execution_authoring_merge_validation_receipt(ROOT)
    assert observed == expected
    assert observed.pr_number == 164
    assert observed.merge_commit == "75936adac9ee100f9538f5af13a8ce312642ee0b"
    assert observed.file_count == 18
    assert observed.insertions == 1678
    assert observed.deletions == 0


def test_operation_json_is_exact_canonical_expected_operation() -> None:
    expected = build_expected_operation(ROOT)
    observed = load_canonical_prospective_operation(ROOT, OPERATION_JSON_RELATIVE)
    text = (ROOT / OPERATION_JSON_RELATIVE).read_text(encoding="utf-8")
    assert observed == expected
    assert text == canonical_json(expected)
    assert observed.operation_operator_identity == "dzmitry-prychyna"
    assert observed.operation_authorized_at_utc == "2026-08-02T15:51:00Z"
    assert observed.operation_performed is False
    assert observed.invocation_adapter_called is False


def test_authorization_builder_matches_frozen_authorization() -> None:
    receipt = build_execution_authoring_merge_validation_receipt()
    operation = build_expected_operation(ROOT)
    expected = build_frozen_execution_authorization(receipt, operation)
    observed = load_execution_authorization(ROOT)
    assert observed == expected
    assert observed.authorization_id == EXECUTION_AUTHORIZATION_ID
    assert observed.authorization_phrase == EXECUTION_AUTHORIZATION_PHRASE
    assert observed.operator_identity == "dzmitry-prychyna"


def test_authorization_json_is_canonical() -> None:
    receipt = load_execution_authoring_merge_validation_receipt(ROOT)
    operation = load_canonical_prospective_operation(ROOT, OPERATION_JSON_RELATIVE)
    authorization = load_execution_authorization(ROOT)
    assert (ROOT / AUTHORIZATION_RELATIVE).read_text(
        encoding="utf-8"
    ) == authorization.canonical_json(receipt, operation)


def test_authorization_pins_operation_json_sha256() -> None:
    authorization = load_execution_authorization(ROOT)
    operation_bytes = (ROOT / OPERATION_JSON_RELATIVE).read_bytes()
    assert authorization.source.operation_json_sha256 == sha256_bytes(operation_bytes)
    assert (
        authorization.contract.exact_operation_json_sha256_required
        == sha256_bytes(operation_bytes)
    )


def test_authorization_contract_is_single_use_and_merge_conditioned() -> None:
    contract = load_execution_authorization(ROOT).contract
    assert contract.authorization_single_use is True
    assert contract.authorization_consumption_required_at_attempt_start is True
    assert contract.authorization_consumption_atomic_with_attempt_start is True
    assert contract.authorization_consumption_forbidden_before_post_merge is True
    assert contract.authorization_effective_only_after_post_merge_verification is True
    assert contract.execution_commit_is_authorization_merge_commit is True
    assert contract.execution_attempt_limit == 1
    assert contract.automatic_retry_forbidden is True
    assert contract.blind_retry_forbidden is True
    assert contract.failure_after_consumption_retry_forbidden is True


def test_authorization_contract_pins_exact_callsite_and_argv() -> None:
    contract = load_execution_authorization(ROOT).contract
    assert contract.exact_production_callsite_relative_required == (
        PRODUCTION_CALLSITE_RELATIVE.as_posix()
    )
    assert contract.exact_argv_required is True
    assert contract.shell_interpretation_forbidden is True
    assert contract.cwd_exact_project_root_required is True
    argv = json.loads(contract.exact_argv_template_json_required)
    assert argv == [
        "python",
        PRODUCTION_CALLSITE_RELATIVE.as_posix(),
        "--project-root",
        "<VERIFIED_PROJECT_ROOT>",
        "--operation-json",
        OPERATION_JSON_RELATIVE.as_posix(),
    ]


def test_authorization_gates_are_issued_but_not_effective() -> None:
    gates = load_execution_authorization(ROOT).gates
    assert gates.execution_authoring_post_merge_verified is True
    assert gates.execution_authorization_record_present is True
    assert gates.execution_authorization_issued is True
    assert gates.canonical_operation_json_materialized is True
    assert gates.execution_authorization_post_merge_verified is False
    assert gates.callsite_execution_authorized is False
    assert gates.production_callsite_executed is False
    assert gates.callsite_execution_performed is False
    assert gates.authorization_consumed is False
    assert gates.runtime_execution_started is False
    assert gates.runtime_execution_performed is False


def test_full_authorization_verifier_passes_without_effects() -> None:
    result = verify_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authorization(
        ROOT
    )
    assert result.authorization_id == EXECUTION_AUTHORIZATION_ID
    assert not (ROOT / ACKNOWLEDGEMENT_RELATIVE).exists()
    assert not (ROOT / LEGACY_EXECUTION_LEASE_RELATIVE).exists()
    assert not (ROOT / EXECUTION_LEASE_V2_RELATIVE).exists()
    assert not (ROOT / DURABLE_HOST_OUTCOME_RELATIVE).exists()


def test_package_file_set_is_exact() -> None:
    observed = {
        path.name
        for path in (ROOT / PACKAGE_RELATIVE).iterdir()
        if path.is_file()
    }
    assert observed == {
        "SHA256SUMS",
        "authorization.json",
        "execution-authoring-merge-validation.json",
        "operation.json",
        "source-SHA256SUMS",
    }


def test_declared_repository_paths_are_regular_files() -> None:
    for relative in (
        AUTHORIZATION_RELATIVE,
        OPERATION_JSON_RELATIVE,
        EXECUTION_AUTHORING_MERGE_RECEIPT_RELATIVE,
        REGISTRY_RELATIVE,
        SOURCE_REGISTRY_RELATIVE,
        MODULE_RELATIVE,
        VERIFIER_RELATIVE,
        TEST_RELATIVE,
        ADR_RU_RELATIVE,
        ADR_EN_RELATIVE,
        PRODUCTION_CALLSITE_RELATIVE,
    ):
        path = ROOT / relative
        assert path.is_file()
        assert not path.is_symlink()


def test_verifier_cli_reports_closed_execution_boundary(capsys) -> None:
    module = _verifier_module()
    assert module.main(["--project-root", str(ROOT)]) == 0
    output = capsys.readouterr().out
    assert "EXECUTION_AUTHORIZATION_ISSUED=true" in output
    assert "CANONICAL_OPERATION_JSON_MATERIALIZED=true" in output
    assert "EXECUTION_AUTHORIZATION_POST_MERGE_VERIFIED=false" in output
    assert (
        "MATERIALIZATION_INVOCATION_OPERATION_CALLSITE_EXECUTION_AUTHORIZED=false"
        in output
    )
    assert "PRODUCTION_CALLSITE_EXECUTED=false" in output
    assert "AUTHORIZATION_CONSUMED=false" in output
    assert "RUNTIME_EXECUTION_PERFORMED=false" in output


def test_authorization_semantic_hash_tamper_fails(tmp_path: Path) -> None:
    copied = _copy_repository(tmp_path)
    path = copied / AUTHORIZATION_RELATIVE
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["operator_identity"] = "other-operator"
    path.write_text(canonical_json(payload), encoding="utf-8")
    with pytest.raises(
        FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError
    ):
        verify_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authorization(
            copied
        )


def test_operation_tamper_fails(tmp_path: Path) -> None:
    copied = _copy_repository(tmp_path)
    path = copied / OPERATION_JSON_RELATIVE
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["operation_operator_identity"] = "other-operator"
    path.write_text(canonical_json(payload), encoding="utf-8")
    with pytest.raises(FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError):
        verify_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authorization(
            copied
        )


def test_noncanonical_operation_json_fails(tmp_path: Path) -> None:
    copied = _copy_repository(tmp_path)
    path = copied / OPERATION_JSON_RELATIVE
    payload = json.loads(path.read_text(encoding="utf-8"))
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError):
        verify_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authorization(
            copied
        )


def test_symlink_operation_json_fails(tmp_path: Path) -> None:
    copied = _copy_repository(tmp_path)
    path = copied / OPERATION_JSON_RELATIVE
    target = path.with_name("operation-target.json")
    path.rename(target)
    path.symlink_to(target.name)
    with pytest.raises(FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError):
        verify_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authorization(
            copied
        )


@pytest.mark.parametrize(
    "relative",
    [
        ACKNOWLEDGEMENT_RELATIVE,
        LEGACY_EXECUTION_LEASE_RELATIVE,
        EXECUTION_LEASE_V2_RELATIVE,
        DURABLE_HOST_OUTCOME_RELATIVE,
    ],
)
def test_production_boundary_artifact_fails(
    tmp_path: Path,
    relative: Path,
) -> None:
    copied = _copy_repository(tmp_path, relative.name)
    target = copied / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("{}\n", encoding="utf-8")
    with pytest.raises(
        FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError
    ):
        verify_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authorization(
            copied
        )


def test_runtime_output_directory_fails(tmp_path: Path) -> None:
    copied = _copy_repository(tmp_path)
    target = copied / "results/stage-3/qwake-lc4-runtime-validation-v1-attempt-001"
    target.mkdir(parents=True)
    with pytest.raises(
        FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError
    ):
        verify_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authorization(
            copied
        )


def test_authorization_module_has_no_runtime_effect_callsite() -> None:
    tree = ast.parse((ROOT / MODULE_RELATIVE).read_text(encoding="utf-8"))
    forbidden = {
        "invoke_final_execution_acknowledgement_materialization",
        "perform_final_execution_acknowledgement_materialization_invocation_operation",
        "materialize_final_execution_acknowledgement",
        "persist_final_execution_acknowledgement",
        "Popen",
        "run",
    }
    observed: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            observed.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            observed.add(node.func.attr)
    assert forbidden.isdisjoint(observed)


def test_authorization_builder_rejects_operator_drift() -> None:
    receipt = build_execution_authoring_merge_validation_receipt()
    operation = build_expected_operation(ROOT)
    authorization = build_frozen_execution_authorization(receipt, operation)
    drifted = replace(authorization, operator_identity="other-operator")
    with pytest.raises(
        FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError
    ):
        drifted.require(receipt, operation)


def test_authorization_builder_rejects_consumed_gate() -> None:
    receipt = build_execution_authoring_merge_validation_receipt()
    operation = build_expected_operation(ROOT)
    authorization = build_frozen_execution_authorization(receipt, operation)
    drifted = replace(
        authorization,
        gates=replace(authorization.gates, authorization_consumed=True),
    )
    with pytest.raises(
        FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError
    ):
        drifted.require(receipt, operation)


def test_authorization_and_operation_files_do_not_imply_execution() -> None:
    authorization = load_execution_authorization(ROOT)
    operation = load_canonical_prospective_operation(ROOT, OPERATION_JSON_RELATIVE)
    assert authorization.gates.execution_authorization_issued is True
    assert authorization.gates.callsite_execution_authorized is False
    assert authorization.gates.production_callsite_executed is False
    assert operation.operation_performed is False
    assert operation.invocation_adapter_called is False
    assert operation.final_execution_acknowledgement_issued is False
