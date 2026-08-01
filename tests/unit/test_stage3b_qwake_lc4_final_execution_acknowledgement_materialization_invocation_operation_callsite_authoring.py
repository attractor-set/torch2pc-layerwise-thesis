from __future__ import annotations

import ast
import json
import shutil
from pathlib import Path

import pytest

from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_callsite_authoring import (
    ADR_EN_RELATIVE,
    ADR_RU_RELATIVE,
    CALLSITE_AUTHORING_BASE_COMMIT,
    IMPLEMENTATION_MERGE_RECEIPT_RELATIVE,
    MODULE_RELATIVE,
    OPERATION_IMPLEMENTATION_HEAD_COMMIT,
    OPERATION_IMPLEMENTATION_MERGE_COMMIT,
    OPERATION_IMPLEMENTATION_PARENT_COMMIT,
    OPERATION_IMPLEMENTATION_PR_NUMBER,
    OPERATION_IMPLEMENTATION_SHA256,
    OPERATION_JSON_OPTION,
    PACKAGE_RELATIVE,
    PRODUCTION_CALLSITE_SYMBOL,
    PROJECT_ROOT_OPTION,
    REGISTRY_RELATIVE,
    SOURCE_REGISTRY_RELATIVE,
    TEST_RELATIVE,
    VERIFIER_RELATIVE,
    FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringError,
    build_frozen_materialization_invocation_operation_callsite_authoring_record,
    build_operation_implementation_merge_validation_receipt,
    load_final_execution_acknowledgement_materialization_invocation_operation_callsite_authoring,
    load_operation_implementation_merge_validation_receipt,
    verify_final_execution_acknowledgement_materialization_invocation_operation_callsite_authoring,
)
from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_implementation import (
    FUTURE_PRODUCTION_CALLSITE_RELATIVE,
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
    receipt = build_operation_implementation_merge_validation_receipt()
    authoring = build_frozen_materialization_invocation_operation_callsite_authoring_record(
        receipt
    )
    assert load_operation_implementation_merge_validation_receipt(ROOT) == receipt
    assert (
        load_final_execution_acknowledgement_materialization_invocation_operation_callsite_authoring(
            ROOT
        )
        == authoring
    )


def test_complete_package_verifies_without_effects() -> None:
    authoring = verify_final_execution_acknowledgement_materialization_invocation_operation_callsite_authoring(
        ROOT
    )
    assert authoring.gates.production_callsite_present is False
    assert authoring.gates.materialization_invocation_operation_performed is False


def test_exact_production_callsite_path_is_frozen_and_absent() -> None:
    authoring = load_final_execution_acknowledgement_materialization_invocation_operation_callsite_authoring(
        ROOT
    )
    assert authoring.source.production_callsite_relative == (
        FUTURE_PRODUCTION_CALLSITE_RELATIVE.as_posix()
    )
    assert not (ROOT / FUTURE_PRODUCTION_CALLSITE_RELATIVE).exists()


def test_exact_production_callsite_symbol_is_frozen() -> None:
    authoring = load_final_execution_acknowledgement_materialization_invocation_operation_callsite_authoring(
        ROOT
    )
    assert authoring.source.production_callsite_symbol == PRODUCTION_CALLSITE_SYMBOL
    assert authoring.contract.exact_production_callsite_symbol_required == (
        PRODUCTION_CALLSITE_SYMBOL
    )


def test_exact_operation_delegate_is_frozen() -> None:
    authoring = load_final_execution_acknowledgement_materialization_invocation_operation_callsite_authoring(
        ROOT
    )
    assert authoring.source.operation_implementation_symbol == OPERATION_IMPLEMENTATION_SYMBOL
    assert authoring.contract.exact_operation_delegate_symbol_required == (
        OPERATION_IMPLEMENTATION_SYMBOL
    )


def test_explicit_cli_inputs_are_required() -> None:
    contract = load_final_execution_acknowledgement_materialization_invocation_operation_callsite_authoring(
        ROOT
    ).contract
    assert contract.project_root_option_required == PROJECT_ROOT_OPTION
    assert contract.operation_json_option_required == OPERATION_JSON_OPTION
    assert contract.canonical_prospective_operation_json_required is True
    assert contract.explicit_operation_file_required is True


def test_implicit_input_channels_are_forbidden() -> None:
    contract = load_final_execution_acknowledgement_materialization_invocation_operation_callsite_authoring(
        ROOT
    ).contract
    assert contract.stdin_operation_forbidden is True
    assert contract.environment_fallback_forbidden is True
    assert contract.interactive_prompt_forbidden is True


def test_callsite_may_delegate_exactly_once() -> None:
    contract = load_final_execution_acknowledgement_materialization_invocation_operation_callsite_authoring(
        ROOT
    ).contract
    assert contract.operation_delegate_call_limit == 1
    assert contract.automatic_retry_forbidden is True
    assert contract.blind_retry_forbidden is True


def test_direct_lower_level_calls_are_forbidden() -> None:
    contract = load_final_execution_acknowledgement_materialization_invocation_operation_callsite_authoring(
        ROOT
    ).contract
    assert contract.standalone_preprobe_forbidden is True
    assert contract.direct_invocation_adapter_call_forbidden is True
    assert contract.direct_materializer_call_forbidden is True
    assert contract.direct_writer_call_forbidden is True


def test_result_and_exit_contract_is_exact() -> None:
    contract = load_final_execution_acknowledgement_materialization_invocation_operation_callsite_authoring(
        ROOT
    ).contract
    assert contract.canonical_result_stdout_required is True
    assert contract.result_file_write_forbidden is True
    assert contract.exit_zero_only_after_verified_result is True
    assert contract.nonzero_exit_on_failure_required is True


def test_source_binds_exact_pr155_merge() -> None:
    source = load_final_execution_acknowledgement_materialization_invocation_operation_callsite_authoring(
        ROOT
    ).source
    assert source.callsite_authoring_base_commit == CALLSITE_AUTHORING_BASE_COMMIT
    assert source.operation_implementation_pr_number == OPERATION_IMPLEMENTATION_PR_NUMBER
    assert source.operation_implementation_head_commit == OPERATION_IMPLEMENTATION_HEAD_COMMIT
    assert source.operation_implementation_parent_commit == OPERATION_IMPLEMENTATION_PARENT_COMMIT
    assert source.operation_implementation_merge_commit == OPERATION_IMPLEMENTATION_MERGE_COMMIT
    assert source.operation_implementation_sha256 == OPERATION_IMPLEMENTATION_SHA256


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
        FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringError
    ):
        verify_final_execution_acknowledgement_materialization_invocation_operation_callsite_authoring(
            root
        )


def test_receipt_drift_is_rejected(tmp_path: Path) -> None:
    root = _isolated_copy(tmp_path)
    path = root / IMPLEMENTATION_MERGE_RECEIPT_RELATIVE
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["required_ci_checks_total"] = 3
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(
        FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringError
    ):
        verify_final_execution_acknowledgement_materialization_invocation_operation_callsite_authoring(
            root
        )


def test_existing_production_callsite_fails_closed(tmp_path: Path) -> None:
    root = _isolated_copy(tmp_path)
    path = root / FUTURE_PRODUCTION_CALLSITE_RELATIVE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("def main():\n    return 0\n", encoding="utf-8")
    with pytest.raises(
        FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringError
    ):
        verify_final_execution_acknowledgement_materialization_invocation_operation_callsite_authoring(
            root
        )


def test_existing_acknowledgement_fails_closed(tmp_path: Path) -> None:
    root = _isolated_copy(tmp_path)
    path = root / "results/stage-3/qwake-lc4-runtime-validation-v1-attempt-001.final-execution-acknowledgement.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{}\n", encoding="utf-8")
    with pytest.raises(
        FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringError
    ):
        verify_final_execution_acknowledgement_materialization_invocation_operation_callsite_authoring(
            root
        )


def test_authoring_ast_contains_no_runtime_delegate_call() -> None:
    tree = ast.parse((ROOT / MODULE_RELATIVE).read_text(encoding="utf-8"))
    called = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert OPERATION_IMPLEMENTATION_SYMBOL.rsplit(".", 1)[-1] not in called
    assert "invoke_final_execution_acknowledgement_materialization" not in called
    assert "materialize_final_execution_acknowledgement" not in called
    assert "persist_final_execution_acknowledgement" not in called


def test_gate_and_next_slice_state_is_closed() -> None:
    authoring = load_final_execution_acknowledgement_materialization_invocation_operation_callsite_authoring(
        ROOT
    )
    gates = authoring.gates
    assert gates.operation_implementation_post_merge_verified is True
    assert gates.materialization_invocation_operation_callsite_contract_authored is True
    assert gates.materialization_invocation_operation_callsite_implemented is False
    assert gates.production_callsite_present is False
    assert gates.materialization_invocation_operation_performed is False
    assert gates.invocation_adapter_called is False
    assert gates.final_execution_acknowledgement_issued is False
    assert gates.execution_lease_materialized is False
    assert gates.runtime_execution_performed is False
    assert authoring.post_merge_next_slice.endswith("callsite-implementation")
