from __future__ import annotations

import ast
import json
import shutil
from pathlib import Path

import pytest

from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authoring import (
    ADR_EN_RELATIVE,
    ADR_RU_RELATIVE,
    AUTHORING_RECORD_RELATIVE,
    CALLSITE_EXECUTION_AUTHORING_BASE_COMMIT,
    CALLSITE_EXECUTION_PHRASE,
    CALLSITE_IMPLEMENTATION_HEAD_COMMIT,
    CALLSITE_IMPLEMENTATION_MERGE_COMMIT,
    CALLSITE_IMPLEMENTATION_PARENT_COMMIT,
    CALLSITE_IMPLEMENTATION_PR_NUMBER,
    CALLSITE_IMPLEMENTATION_SHA256,
    FUTURE_EXECUTION_AUTHORIZATION_RELATIVE,
    FUTURE_OPERATION_JSON_RELATIVE,
    IMPLEMENTATION_MERGE_RECEIPT_RELATIVE,
    MODULE_RELATIVE,
    PACKAGE_RELATIVE,
    REGISTRY_RELATIVE,
    SOURCE_REGISTRY_RELATIVE,
    TEST_RELATIVE,
    VERIFIER_RELATIVE,
    FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringError,
    build_callsite_implementation_merge_validation_receipt,
    build_frozen_materialization_invocation_operation_callsite_execution_authoring_record,
    load_callsite_implementation_merge_validation_receipt,
    load_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authoring,
    verify_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authoring,
)
from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_callsite_implementation import (
    PRODUCTION_CALLSITE_RELATIVE,
    PRODUCTION_CALLSITE_SYMBOL,
)
from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_implementation import (
    OPERATION_IMPLEMENTATION_SYMBOL,
)

ROOT = Path(__file__).resolve().parents[2]


def _isolated_copy(tmp_path: Path) -> Path:
    target = tmp_path / "repository"
    shutil.copytree(
        ROOT,
        target,
        ignore=shutil.ignore_patterns(
            ".git",
            ".mypy_cache",
            ".pytest_cache",
            ".ruff_cache",
            "__pycache__",
            "site_ru",
            "site_en",
        ),
    )
    return target


def test_frozen_records_are_exact() -> None:
    receipt = build_callsite_implementation_merge_validation_receipt()
    authoring = build_frozen_materialization_invocation_operation_callsite_execution_authoring_record(
        receipt
    )
    assert load_callsite_implementation_merge_validation_receipt(ROOT) == receipt
    assert (
        load_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authoring(
            ROOT
        )
        == authoring
    )


def test_complete_package_verifies_without_effects() -> None:
    authoring = verify_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authoring(
        ROOT
    )
    assert authoring.gates.production_callsite_present is True
    assert authoring.gates.production_callsite_executed is False
    assert authoring.gates.callsite_execution_authorized is False


def test_source_binds_exact_pr163_merge() -> None:
    source = load_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authoring(
        ROOT
    ).source
    assert source.execution_authoring_base_commit == CALLSITE_EXECUTION_AUTHORING_BASE_COMMIT
    assert source.callsite_implementation_pr_number == CALLSITE_IMPLEMENTATION_PR_NUMBER
    assert source.callsite_implementation_head_commit == CALLSITE_IMPLEMENTATION_HEAD_COMMIT
    assert source.callsite_implementation_parent_commit == CALLSITE_IMPLEMENTATION_PARENT_COMMIT
    assert source.callsite_implementation_merge_commit == CALLSITE_IMPLEMENTATION_MERGE_COMMIT
    assert source.callsite_implementation_sha256 == CALLSITE_IMPLEMENTATION_SHA256


def test_exact_production_callsite_and_delegate_are_frozen() -> None:
    authoring = load_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authoring(
        ROOT
    )
    assert authoring.source.production_callsite_relative == PRODUCTION_CALLSITE_RELATIVE.as_posix()
    assert authoring.source.production_callsite_symbol == PRODUCTION_CALLSITE_SYMBOL
    assert authoring.source.operation_implementation_symbol == OPERATION_IMPLEMENTATION_SYMBOL
    assert authoring.contract.exact_production_callsite_relative_required == PRODUCTION_CALLSITE_RELATIVE.as_posix()
    assert authoring.contract.exact_production_callsite_symbol_required == PRODUCTION_CALLSITE_SYMBOL
    assert authoring.contract.exact_operation_delegate_symbol_required == OPERATION_IMPLEMENTATION_SYMBOL


def test_execution_phrase_is_exact_and_distinct() -> None:
    authoring = load_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authoring(
        ROOT
    )
    assert authoring.source.execution_phrase == CALLSITE_EXECUTION_PHRASE
    assert authoring.contract.exact_execution_phrase_required == CALLSITE_EXECUTION_PHRASE
    assert authoring.contract.execution_phrase_distinct_from_operation_phrase is True


def test_future_authorization_and_operation_paths_are_exact_and_absent() -> None:
    authoring = load_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authoring(
        ROOT
    )
    assert authoring.source.future_execution_authorization_relative == FUTURE_EXECUTION_AUTHORIZATION_RELATIVE.as_posix()
    assert authoring.source.future_operation_json_relative == FUTURE_OPERATION_JSON_RELATIVE.as_posix()
    assert not (ROOT / FUTURE_EXECUTION_AUTHORIZATION_RELATIVE).exists()
    assert not (ROOT / FUTURE_OPERATION_JSON_RELATIVE).exists()


def test_authorization_is_separate_and_explicit() -> None:
    contract = load_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authoring(
        ROOT
    ).contract
    assert contract.explicit_execution_operator_identity_required is True
    assert contract.explicit_execution_authorized_at_utc_required is True
    assert contract.execution_authorization_separate is True
    assert contract.execution_authorization_post_merge_verification_required is True
    assert contract.operation_json_materialization_separate is True


def test_exact_argv_and_no_shell_are_required() -> None:
    contract = load_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authoring(
        ROOT
    ).contract
    assert contract.project_root_option_required == "--project-root"
    assert contract.operation_json_option_required == "--operation-json"
    assert contract.exact_argv_required is True
    assert contract.shell_interpretation_forbidden is True
    assert contract.cwd_exact_project_root_required is True


def test_single_attempt_and_no_retry_are_required() -> None:
    contract = load_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authoring(
        ROOT
    ).contract
    assert contract.execution_attempt_limit == 1
    assert contract.automatic_retry_forbidden is True
    assert contract.blind_retry_forbidden is True


def test_dynamic_preconditions_are_reverified_immediately_before_attempt() -> None:
    contract = load_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authoring(
        ROOT
    ).contract
    assert contract.exact_execution_commit_required is True
    assert contract.exact_torch2pc_commit_required is True
    assert contract.clean_worktree_required is True
    assert contract.clean_index_required is True
    assert contract.production_callsite_hash_reverification_required is True
    assert contract.operation_json_hash_reverification_required is True
    assert contract.acknowledgement_absence_required_before_attempt is True
    assert contract.runtime_output_absence_required_before_attempt is True
    assert contract.runtime_staging_absence_required_before_attempt is True


def test_result_contract_is_exact() -> None:
    contract = load_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authoring(
        ROOT
    ).contract
    assert contract.success_requires_zero_exit is True
    assert contract.success_requires_single_canonical_stdout_object is True
    assert contract.stdout_before_success_forbidden is True
    assert contract.result_file_write_forbidden is True
    assert contract.nonzero_exit_on_failure_required is True


def test_authoring_effects_are_forbidden() -> None:
    contract = load_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authoring(
        ROOT
    ).contract
    assert contract.authoring_effects_forbidden is True
    assert contract.production_callsite_execution_forbidden is True
    assert contract.operation_performance_forbidden is True
    assert contract.authorization_consumption_forbidden is True
    assert contract.subprocess_forbidden is True
    assert contract.docker_forbidden is True
    assert contract.local_compute_forbidden is True


def test_package_and_source_path_sets_are_exact() -> None:
    package_files = {path.name for path in (ROOT / PACKAGE_RELATIVE).iterdir()}
    assert package_files == {
        "SHA256SUMS",
        "authoring.json",
        "implementation-merge-validation.json",
        "source-SHA256SUMS",
    }
    source_paths = {
        line.split("  ", 1)[1]
        for line in (ROOT / SOURCE_REGISTRY_RELATIVE).read_text(encoding="utf-8").splitlines()
        if line
    }
    for relative in (
        MODULE_RELATIVE,
        VERIFIER_RELATIVE,
        TEST_RELATIVE,
        ADR_RU_RELATIVE,
        ADR_EN_RELATIVE,
    ):
        assert relative.as_posix() in source_paths
    assert REGISTRY_RELATIVE.name == "SHA256SUMS"


def test_source_registry_rejects_authoring_module_drift(tmp_path: Path) -> None:
    root = _isolated_copy(tmp_path)
    path = root / MODULE_RELATIVE
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(
        FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringError
    ):
        verify_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authoring(
            root
        )


def test_receipt_drift_is_rejected(tmp_path: Path) -> None:
    root = _isolated_copy(tmp_path)
    path = root / IMPLEMENTATION_MERGE_RECEIPT_RELATIVE
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["required_ci_checks_total"] = 3
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(
        FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringError
    ):
        verify_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authoring(
            root
        )


def test_missing_production_callsite_fails_closed(tmp_path: Path) -> None:
    root = _isolated_copy(tmp_path)
    (root / PRODUCTION_CALLSITE_RELATIVE).unlink()
    with pytest.raises(
        FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringError
    ):
        verify_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authoring(
            root
        )


def test_existing_future_authorization_fails_closed(tmp_path: Path) -> None:
    root = _isolated_copy(tmp_path)
    path = root / FUTURE_EXECUTION_AUTHORIZATION_RELATIVE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{}\n", encoding="utf-8")
    with pytest.raises(
        FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringError
    ):
        verify_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authoring(
            root
        )


def test_existing_acknowledgement_fails_closed(tmp_path: Path) -> None:
    root = _isolated_copy(tmp_path)
    path = root / "results/stage-3/qwake-lc4-runtime-validation-v1-attempt-001.final-execution-acknowledgement.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{}\n", encoding="utf-8")
    with pytest.raises(
        FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringError
    ):
        verify_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authoring(
            root
        )


def test_authoring_ast_contains_no_execution_or_operation_call() -> None:
    tree = ast.parse((ROOT / MODULE_RELATIVE).read_text(encoding="utf-8"))
    called = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "main" not in called
    assert OPERATION_IMPLEMENTATION_SYMBOL.rsplit(".", 1)[-1] not in called
    assert "invoke_final_execution_acknowledgement_materialization" not in called
    assert "materialize_final_execution_acknowledgement" not in called
    assert "persist_final_execution_acknowledgement" not in called


def test_gate_and_next_slice_state_is_closed() -> None:
    authoring = load_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authoring(
        ROOT
    )
    gates = authoring.gates
    assert gates.callsite_implementation_post_merge_verified is True
    assert gates.callsite_execution_contract_authored is True
    assert gates.callsite_execution_authorized is False
    assert gates.production_callsite_present is True
    assert gates.production_callsite_executed is False
    assert gates.callsite_execution_performed is False
    assert gates.materialization_invocation_operation_performed is False
    assert gates.invocation_adapter_called is False
    assert gates.final_execution_acknowledgement_issued is False
    assert gates.runtime_execution_performed is False
    assert authoring.post_merge_next_slice.endswith("callsite-execution-authorization")


def test_authoring_record_path_is_frozen() -> None:
    assert AUTHORING_RECORD_RELATIVE == PACKAGE_RELATIVE / "authoring.json"
