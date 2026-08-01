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
    FINAL_EXECUTION_OPERATOR_ACKNOWLEDGEMENT,
    canonical_json,
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
from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_callsite_implementation import (
    ADR_EN_RELATIVE,
    ADR_RU_RELATIVE,
    AUTHORING_MERGE_RECEIPT_RELATIVE,
    IMPLEMENTATION_RECORD_RELATIVE,
    MODULE_RELATIVE,
    PRODUCTION_CALLSITE_RELATIVE,
    PRODUCTION_CALLSITE_SYMBOL,
    REGISTRY_RELATIVE,
    SOURCE_REGISTRY_RELATIVE,
    TEST_RELATIVE,
    VERIFIER_RELATIVE,
    FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError,
    build_callsite_authoring_merge_validation_receipt,
    build_frozen_materialization_invocation_operation_callsite_implementation_record,
    canonical_verified_operation_result_json,
    load_callsite_authoring_merge_validation_receipt,
    load_canonical_prospective_operation,
    load_final_execution_acknowledgement_materialization_invocation_operation_callsite_implementation,
    verify_final_execution_acknowledgement_materialization_invocation_operation_callsite_implementation,
)
from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_implementation import (
    OPERATION_IMPLEMENTATION_SYMBOL,
    perform_final_execution_acknowledgement_materialization_invocation_operation,
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


def _script_module() -> ModuleType:
    path = ROOT / PRODUCTION_CALLSITE_RELATIVE
    spec = importlib.util.spec_from_file_location("qwake_callsite_under_test", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_operation(root: Path, name: str = "operation.json") -> Path:
    path = root / name
    path.write_text(canonical_json(_operation()), encoding="utf-8")
    return path


def _valid_result(tmp_path: Path):
    copied = _copy_repository(tmp_path, "result-source")
    return perform_final_execution_acknowledgement_materialization_invocation_operation(
        copied,
        _operation(),
    )


def test_frozen_records_are_exact() -> None:
    receipt = load_callsite_authoring_merge_validation_receipt(ROOT)
    implementation = load_final_execution_acknowledgement_materialization_invocation_operation_callsite_implementation(
        ROOT
    )
    assert receipt == build_callsite_authoring_merge_validation_receipt()
    assert implementation == build_frozen_materialization_invocation_operation_callsite_implementation_record(
        receipt
    )


def test_complete_package_verifies_without_effects() -> None:
    implementation = verify_final_execution_acknowledgement_materialization_invocation_operation_callsite_implementation(
        ROOT
    )
    assert implementation.gates.production_callsite_present is True
    assert implementation.gates.materialization_invocation_operation_performed is False
    assert not (ROOT / ACKNOWLEDGEMENT_RELATIVE).exists()


def test_exact_script_path_and_symbol_are_implemented() -> None:
    implementation = load_final_execution_acknowledgement_materialization_invocation_operation_callsite_implementation(
        ROOT
    )
    assert (ROOT / PRODUCTION_CALLSITE_RELATIVE).is_file()
    assert implementation.source.production_callsite_relative == (
        PRODUCTION_CALLSITE_RELATIVE.as_posix()
    )
    assert implementation.source.production_callsite_symbol == PRODUCTION_CALLSITE_SYMBOL


def test_merge_receipt_preserves_advanced_main_reconciliation() -> None:
    receipt = load_callsite_authoring_merge_validation_receipt(ROOT)
    assert receipt.original_base_commit == "23a86cc0769f20b4b7536e64250f3dee062aaa62"
    assert receipt.actual_first_parent_commit == "dc8dc200515959858d43b68984dbd87f27f3446c"
    assert receipt.merge_commit == "b27e252cf7c64e88d5d61bf7a23c70ffc5957959"
    assert receipt.merge_tree == "408c9cbbd97c35292ba8a9476c54d3fe0905f00e"
    assert receipt.automatic_merge_tree_verified is True


def test_contract_requires_explicit_inputs_and_one_delegate() -> None:
    contract = load_final_execution_acknowledgement_materialization_invocation_operation_callsite_implementation(
        ROOT
    ).contract
    assert contract.project_root_option_required == "--project-root"
    assert contract.operation_json_option_required == "--operation-json"
    assert contract.operation_delegate_call_limit == 1
    assert contract.exact_operation_delegate_symbol_required == OPERATION_IMPLEMENTATION_SYMBOL


def test_script_ast_has_exact_delegate_and_no_lower_level_calls() -> None:
    tree = ast.parse((ROOT / PRODUCTION_CALLSITE_RELATIVE).read_text(encoding="utf-8"))
    called = []
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_roots.add((node.module or "").split(".", 1)[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called.append(node.func.attr)
    delegate = OPERATION_IMPLEMENTATION_SYMBOL.rsplit(".", 1)[-1]
    assert called.count(delegate) == 1
    assert set(called).isdisjoint(
        {
            "invoke_final_execution_acknowledgement_materialization",
            "materialize_final_execution_acknowledgement",
            "persist_final_execution_acknowledgement",
            "probe_final_execution_acknowledgement_state",
        }
    )
    assert imported_roots.isdisjoint({"docker", "os", "subprocess"})
    assert "input" not in called


def test_missing_cli_inputs_fail_nonzero() -> None:
    module = _script_module()
    with pytest.raises(SystemExit) as exc_info:
        module.main([])
    assert exc_info.value.code == 2


def test_canonical_operation_round_trip(tmp_path: Path) -> None:
    operation_path = _write_operation(tmp_path)
    assert load_canonical_prospective_operation(tmp_path, operation_path) == _operation()


def test_noncanonical_operation_is_rejected_before_delegate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    module = _script_module()
    operation_path = tmp_path / "operation.json"
    operation_path.write_text(json.dumps(json.loads(canonical_json(_operation()))), encoding="utf-8")
    calls = 0

    def forbidden(*args, **kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError("delegate must not be called")

    monkeypatch.setattr(
        module,
        "perform_final_execution_acknowledgement_materialization_invocation_operation",
        forbidden,
    )
    result = module.main(
        ["--project-root", str(ROOT), "--operation-json", str(operation_path)]
    )
    captured = capsys.readouterr()
    assert result == 1
    assert calls == 0
    assert captured.out == ""
    assert captured.err.startswith("ERROR: operation JSON is not canonical")


def test_extra_operation_field_is_rejected(tmp_path: Path) -> None:
    payload = json.loads(canonical_json(_operation()))
    payload["unexpected"] = True
    path = tmp_path / "operation.json"
    path.write_text(canonical_json(payload), encoding="utf-8")
    with pytest.raises(
        FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError,
        match="field set differs",
    ):
        load_canonical_prospective_operation(tmp_path, path)


def test_operation_symlink_is_rejected(tmp_path: Path) -> None:
    source = _write_operation(tmp_path, "source.json")
    link = tmp_path / "operation.json"
    link.symlink_to(source.name)
    with pytest.raises(
        FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError,
        match="non-symlink",
    ):
        load_canonical_prospective_operation(tmp_path, link)


def test_success_prints_only_canonical_result_and_calls_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    module = _script_module()
    operation_path = _write_operation(tmp_path)
    valid = _valid_result(tmp_path)
    calls = 0

    def delegate(*args, **kwargs):
        nonlocal calls
        calls += 1
        return valid

    monkeypatch.setattr(
        module,
        "perform_final_execution_acknowledgement_materialization_invocation_operation",
        delegate,
    )
    result = module.main(
        ["--project-root", str(ROOT), "--operation-json", str(operation_path)]
    )
    captured = capsys.readouterr()
    assert result == 0
    assert calls == 1
    assert captured.out == canonical_verified_operation_result_json(valid)
    assert captured.err == ""


def test_delegate_failure_is_nonzero_without_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    module = _script_module()
    operation_path = _write_operation(tmp_path)
    calls = 0

    def failing(*args, **kwargs):
        nonlocal calls
        calls += 1
        raise RuntimeError("simulated operation failure")

    monkeypatch.setattr(
        module,
        "perform_final_execution_acknowledgement_materialization_invocation_operation",
        failing,
    )
    result = module.main(
        ["--project-root", str(ROOT), "--operation-json", str(operation_path)]
    )
    captured = capsys.readouterr()
    assert result == 1
    assert calls == 1
    assert captured.out == ""
    assert captured.err == "ERROR: simulated operation failure\n"


def test_invalid_result_is_not_emitted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    module = _script_module()
    operation_path = _write_operation(tmp_path)
    invalid = replace(_valid_result(tmp_path), automatic_retry_performed=True)
    monkeypatch.setattr(
        module,
        "perform_final_execution_acknowledgement_materialization_invocation_operation",
        lambda *args, **kwargs: invalid,
    )
    result = module.main(
        ["--project-root", str(ROOT), "--operation-json", str(operation_path)]
    )
    captured = capsys.readouterr()
    assert result == 1
    assert captured.out == ""
    assert "operation result differs: automatic_retry_performed" in captured.err


def test_fake_delegate_success_writes_no_result_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _script_module()
    operation_path = _write_operation(tmp_path)
    valid = _valid_result(tmp_path)
    before = {path.relative_to(tmp_path) for path in tmp_path.rglob("*")}
    monkeypatch.setattr(
        module,
        "perform_final_execution_acknowledgement_materialization_invocation_operation",
        lambda *args, **kwargs: valid,
    )
    assert module.main(
        ["--project-root", str(ROOT), "--operation-json", str(operation_path)]
    ) == 0
    after = {path.relative_to(tmp_path) for path in tmp_path.rglob("*")}
    assert after == before


def test_end_to_end_callsite_effects_are_isolated(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    copied = _copy_repository(tmp_path, "end-to-end")
    operation_path = copied / "operation.json"
    operation_path.write_text(canonical_json(_operation()), encoding="utf-8")
    module = _script_module()
    result = module.main(
        ["--project-root", str(copied), "--operation-json", str(operation_path)]
    )
    captured = capsys.readouterr()
    assert result == 0
    payload = json.loads(captured.out)
    assert payload["operation_performed"] is True
    assert payload["adapter_call_count"] == 1
    assert (copied / ACKNOWLEDGEMENT_RELATIVE).is_file()
    assert not (copied / LEGACY_EXECUTION_LEASE_RELATIVE).exists()
    assert not (copied / EXECUTION_LEASE_V2_RELATIVE).exists()
    assert not (copied / DURABLE_HOST_OUTCOME_RELATIVE).exists()


def test_valid_existing_target_is_canonical_success(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    copied = _copy_repository(tmp_path, "existing")
    operation_path = copied / "operation.json"
    operation_path.write_text(canonical_json(_operation()), encoding="utf-8")
    module = _script_module()
    assert module.main(
        ["--project-root", str(copied), "--operation-json", str(operation_path)]
    ) == 0
    capsys.readouterr()
    assert module.main(
        ["--project-root", str(copied), "--operation-json", str(operation_path)]
    ) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["outcome"] == "valid_existing"
    assert payload["materializer_called"] is False
    assert payload["writer_called"] is False


def test_source_registry_path_set_is_exact() -> None:
    paths = {
        line.split("  ", 1)[1]
        for line in (ROOT / SOURCE_REGISTRY_RELATIVE).read_text(encoding="utf-8").splitlines()
        if line
    }
    for relative in (
        IMPLEMENTATION_RECORD_RELATIVE,
        AUTHORING_MERGE_RECEIPT_RELATIVE,
        MODULE_RELATIVE,
        PRODUCTION_CALLSITE_RELATIVE,
        VERIFIER_RELATIVE,
        TEST_RELATIVE,
        ADR_RU_RELATIVE,
        ADR_EN_RELATIVE,
    ):
        assert relative.as_posix() in paths
    assert REGISTRY_RELATIVE.name == "SHA256SUMS"


def test_source_registry_rejects_script_drift(tmp_path: Path) -> None:
    copied = _copy_repository(tmp_path, "drift")
    path = copied / PRODUCTION_CALLSITE_RELATIVE
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(
        FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError,
        match="registry target hash differs",
    ):
        verify_final_execution_acknowledgement_materialization_invocation_operation_callsite_implementation(
            copied
        )


def test_existing_production_artifact_closes_verification(tmp_path: Path) -> None:
    copied = _copy_repository(tmp_path, "closed")
    target = copied / ACKNOWLEDGEMENT_RELATIVE
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("{}\n", encoding="utf-8")
    with pytest.raises(
        FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError,
        match="production boundary artifact exists",
    ):
        verify_final_execution_acknowledgement_materialization_invocation_operation_callsite_implementation(
            copied
        )


def test_gate_state_and_next_slice_remain_closed() -> None:
    implementation = load_final_execution_acknowledgement_materialization_invocation_operation_callsite_implementation(
        ROOT
    )
    gates = implementation.gates
    assert gates.callsite_authoring_post_merge_verified is True
    assert gates.materialization_invocation_operation_callsite_implemented is True
    assert gates.production_callsite_present is True
    assert gates.materialization_invocation_operation_performed is False
    assert gates.invocation_adapter_called is False
    assert gates.final_execution_acknowledgement_issued is False
    assert gates.runtime_execution_performed is False
    assert implementation.post_merge_next_slice.endswith("callsite-execution-authoring")
