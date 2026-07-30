# Validate the QW-LC4-E bounded runtime-operation contract.

from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import pytest

from torch2pc_thesis import (
    stage3b_qwake_lc4_engineering_invocation_runtime_operation as operation_module,
)
from torch2pc_thesis.stage3b_qwake_lc4_engineering_invocation_runtime_operation import (
    RUNTIME_OPERATION_BASE_COMMIT,
    RUNTIME_OPERATION_EXECUTION_ACKNOWLEDGEMENT,
    RUNTIME_OPERATION_ID,
    RUNTIME_OPERATION_STATUS,
    QWakeLC4EngineeringInvocationRuntimeOperationError,
    build_engineering_invocation_runtime_operation,
    execute_one_shot_engineering_invocation_runtime_operation,
    load_engineering_invocation_runtime_operation,
    verify_engineering_invocation_runtime_operation,
)
from torch2pc_thesis.stage3b_qwake_lc4_host_runtime_invoker_implementation import (
    HostRuntimeInvocationOutcome,
)
from torch2pc_thesis.stage3b_qwake_lc4_invocation_authorization import (
    INVOCATION_OPERATOR_ACKNOWLEDGEMENT,
)

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / (
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-one-shot-engineering-invocation-"
    "runtime-operation-v1"
)
RECORD = PACKAGE / "operation.json"
REGISTRY = PACKAGE / "SHA256SUMS"
MODULE = ROOT / (
    "src/torch2pc_thesis/"
    "stage3b_qwake_lc4_engineering_invocation_runtime_operation.py"
)
VERIFIER = ROOT / (
    "scripts/verify_stage3b_qwake_lc4_engineering_invocation_"
    "runtime_operation.py"
)
EXECUTION_LEASE = ROOT / (
    "results/stage-3/"
    "qwake-lc4-runtime-validation-v1-attempt-001.execution-lease.json"
)
OUTPUT_ROOT = ROOT / (
    "results/stage-3/qwake-lc4-runtime-validation-v1-attempt-001"
)


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        json.loads(path.read_text(encoding="utf-8", errors="strict")),
    )


def _resources() -> dict[str, str]:
    return {
        "HOST_UID": "1000",
        "HOST_GID": "1000",
        "VIDEO_GID": "44",
        "RENDER_GID": "109",
        "HIP_VISIBLE_DEVICES": "0",
        "CPUSET_GPU": "0-7",
        "MEM_LIMIT": "48g",
        "SHM_SIZE": "8gb",
        "TMPFS_SIZE": "8g",
        "OMP_NUM_THREADS": "4",
        "MKL_NUM_THREADS": "4",
        "OPENBLAS_NUM_THREADS": "4",
        "NUMEXPR_NUM_THREADS": "4",
    }


def _execute_kwargs() -> dict[str, object]:
    return {
        "host_resources": _resources(),
        "claimed_at_utc": "2026-07-29T23:30:00Z",
        "invocation_operator_acknowledgement": (
            INVOCATION_OPERATOR_ACKNOWLEDGEMENT
        ),
        "runtime_operation_acknowledgement": (
            RUNTIME_OPERATION_EXECUTION_ACKNOWLEDGEMENT
        ),
        "runtime_execution_permitted": True,
    }


def test_runtime_operation_package_is_exact_canonical_and_self_hashed() -> None:
    assert sorted(path.name for path in PACKAGE.iterdir()) == [
        "SHA256SUMS",
        "operation.json",
    ]
    expected, relative = REGISTRY.read_text(
        encoding="utf-8", errors="strict"
    ).strip().split("  ", 1)
    assert relative == "operation.json"
    assert _sha256(RECORD) == "sha256:" + expected

    operation = load_engineering_invocation_runtime_operation(RECORD)
    assert RECORD.read_text(encoding="utf-8") == operation.canonical_json()
    assert operation.operation_id == RUNTIME_OPERATION_ID
    assert operation.status == RUNTIME_OPERATION_STATUS
    assert operation.source.runtime_operation_base_commit == (
        RUNTIME_OPERATION_BASE_COMMIT
    )


def test_runtime_operation_verifies_exact_preexecution_and_invoker() -> None:
    operation = verify_engineering_invocation_runtime_operation(ROOT)
    source = operation.source

    assert source.preexecution_pr_number == 141
    assert source.preexecution_head_commit == (
        "bb888b900401894441f37fdbbe21c1e25c288366"
    )
    assert source.preexecution_parent_commit == (
        "49c4b97e93b47cefbf35576736927ece02c9402b"
    )
    assert source.preexecution_verification_sha256 == (
        "sha256:833371b427a5c8a6e602d675711b85b2edc68441b9e5be191321a2911bce6128"
    )
    assert source.host_runtime_invoker_implementation_state_sha256 == (
        "sha256:1f5f31d4f220bbf074736f1de0b78a5dafa2849188ac337704d5cc704668fdf4"
    )
    assert source.image_repo_digest.endswith(
        "7da92b8f77f6dc37d42db832c5613ef6149dc488adc5b66465faa33e48ca021d"
    )


def test_runtime_operation_contract_is_exact_and_delegated() -> None:
    contract = verify_engineering_invocation_runtime_operation(ROOT).contract

    assert contract.runtime_operation_entrypoint == (
        "execute_one_shot_engineering_invocation_runtime_operation"
    )
    assert contract.delegated_host_runtime_entrypoint == (
        "invoke_one_shot_host_runtime"
    )
    assert contract.invocation_count == 1
    assert contract.host_runtime_invoker_call_count == 1
    assert len(contract.required_host_resource_keys) == 13
    assert contract.image_inspection_count_required == 2
    assert contract.invocation_materialization_count_required == 2
    assert contract.subprocess_popen_call_limit == 1
    assert contract.operation_direct_image_inspection_call_count == 0
    assert contract.operation_direct_materialization_call_count == 0
    assert contract.operation_direct_process_spawn_call_count == 0
    assert contract.verifier_executor_call_count == 0


def test_runtime_operation_gates_are_open_only_for_authoring() -> None:
    operation = verify_engineering_invocation_runtime_operation(ROOT)
    gates = operation.gates

    assert gates.runtime_operation_record_present is True
    assert gates.runtime_operation_executor_entrypoint_implemented is True
    assert gates.runtime_operation_static_contract_verified is True
    assert gates.runtime_operation_slice_open is True
    assert gates.runtime_operation_open is True
    assert gates.preexecution_identity_verified is False
    assert gates.one_shot_engineering_invocation_permitted is False
    assert gates.branch_runtime_execution_permitted is False
    assert gates.execution_lease_materialized is False
    assert gates.runtime_execution_started is False
    assert gates.runtime_execution_performed is False
    assert gates.image_inspection_performed is False
    assert gates.invocation_command_materialized is False
    assert gates.docker_run_performed is False
    assert gates.local_compute_execution_open is False

    with pytest.raises(
        QWakeLC4EngineeringInvocationRuntimeOperationError,
        match="opened a runtime effect",
    ):
        replace(
            operation,
            gates=replace(
                operation.gates,
                branch_runtime_execution_permitted=True,
            ),
        ).require()


def test_runtime_operation_rejects_changed_source_or_contract() -> None:
    operation = verify_engineering_invocation_runtime_operation(ROOT)

    with pytest.raises(
        QWakeLC4EngineeringInvocationRuntimeOperationError,
        match="source differs",
    ):
        replace(
            operation,
            source=replace(
                operation.source,
                runtime_operation_base_commit="0" * 40,
            ),
        ).require()

    with pytest.raises(
        QWakeLC4EngineeringInvocationRuntimeOperationError,
        match="contract differs",
    ):
        replace(
            operation,
            contract=replace(
                operation.contract,
                host_runtime_invoker_call_count=2,
            ),
        ).require()


def test_runtime_operation_effect_boundary_rejects_existing_effects(
    tmp_path: Path,
) -> None:
    output = tmp_path / operation_module.AUTHORIZED_OUTPUT_ROOT
    lease = tmp_path / operation_module.EXECUTION_LEASE_RELATIVE

    lease.parent.mkdir(parents=True)
    lease.write_text("{}\n", encoding="utf-8")
    with pytest.raises(
        QWakeLC4EngineeringInvocationRuntimeOperationError,
        match="execution lease",
    ):
        operation_module._require_effect_boundary_closed(tmp_path)

    lease.unlink()
    output.mkdir(parents=True)
    with pytest.raises(
        QWakeLC4EngineeringInvocationRuntimeOperationError,
        match="runtime output",
    ):
        operation_module._require_effect_boundary_closed(tmp_path)

    output.rmdir()
    staging = output.parent / f".{output.name}.staging-synthetic"
    staging.mkdir()
    with pytest.raises(
        QWakeLC4EngineeringInvocationRuntimeOperationError,
        match="runtime staging",
    ):
        operation_module._require_effect_boundary_closed(tmp_path)


def test_executor_rejects_closed_permission_before_delegation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called = False

    def fake_invoker(*args: object, **kwargs: object) -> HostRuntimeInvocationOutcome:
        nonlocal called
        called = True
        raise AssertionError("invoker must not be called")

    monkeypatch.setattr(
        operation_module,
        "invoke_one_shot_host_runtime",
        fake_invoker,
    )
    kwargs = _execute_kwargs()
    kwargs["runtime_execution_permitted"] = False

    with pytest.raises(
        QWakeLC4EngineeringInvocationRuntimeOperationError,
        match="permission is closed",
    ):
        execute_one_shot_engineering_invocation_runtime_operation(
            ROOT,
            **cast(Any, kwargs),
        )
    assert called is False


def test_executor_rejects_wrong_operation_acknowledgement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called = False

    def fake_invoker(*args: object, **kwargs: object) -> HostRuntimeInvocationOutcome:
        nonlocal called
        called = True
        raise AssertionError("invoker must not be called")

    monkeypatch.setattr(
        operation_module,
        "invoke_one_shot_host_runtime",
        fake_invoker,
    )
    kwargs = _execute_kwargs()
    kwargs["runtime_operation_acknowledgement"] = "WRONG"

    with pytest.raises(
        QWakeLC4EngineeringInvocationRuntimeOperationError,
        match="execution acknowledgement differs",
    ):
        execute_one_shot_engineering_invocation_runtime_operation(
            ROOT,
            **cast(Any, kwargs),
        )
    assert called is False


def test_executor_rejects_invalid_claim_resources_or_invocation_ack() -> None:
    kwargs = _execute_kwargs()
    kwargs["claimed_at_utc"] = "2026-07-29T23:21:31Z"
    with pytest.raises(
        QWakeLC4EngineeringInvocationRuntimeOperationError,
        match="does not follow",
    ):
        execute_one_shot_engineering_invocation_runtime_operation(
            ROOT,
            **cast(Any, kwargs),
        )

    kwargs = _execute_kwargs()
    resources = _resources()
    resources.pop("HOST_UID")
    kwargs["host_resources"] = resources
    with pytest.raises(
        QWakeLC4EngineeringInvocationRuntimeOperationError,
        match="host resource keys differ",
    ):
        execute_one_shot_engineering_invocation_runtime_operation(
            ROOT,
            **cast(Any, kwargs),
        )

    kwargs = _execute_kwargs()
    kwargs["invocation_operator_acknowledgement"] = "WRONG"
    with pytest.raises(
        QWakeLC4EngineeringInvocationRuntimeOperationError,
        match="invocation operator acknowledgement differs",
    ):
        execute_one_shot_engineering_invocation_runtime_operation(
            ROOT,
            **cast(Any, kwargs),
        )


def test_executor_delegates_exactly_once_with_exact_arguments(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sentinel = cast(HostRuntimeInvocationOutcome, object())
    calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def fake_invoker(*args: object, **kwargs: object) -> HostRuntimeInvocationOutcome:
        calls.append((args, dict(kwargs)))
        return sentinel

    monkeypatch.setattr(
        operation_module,
        "invoke_one_shot_host_runtime",
        fake_invoker,
    )
    kwargs = _execute_kwargs()
    outcome = execute_one_shot_engineering_invocation_runtime_operation(
        ROOT,
        **cast(Any, kwargs),
    )

    assert outcome is sentinel
    assert len(calls) == 1
    args, delegated = calls[0]
    assert args == (ROOT.resolve(),)
    assert delegated == {
        "host_resources": kwargs["host_resources"],
        "claimed_at_utc": kwargs["claimed_at_utc"],
        "operator_acknowledgement": (
            kwargs["invocation_operator_acknowledgement"]
        ),
    }


def test_runtime_operation_sources_have_exact_effect_call_graph() -> None:
    module_tree = ast.parse(
        MODULE.read_text(encoding="utf-8", errors="strict")
    )
    executor = next(
        node
        for node in module_tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name
        == "execute_one_shot_engineering_invocation_runtime_operation"
    )
    direct = [
        node.func.id
        for node in ast.walk(executor)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    ]
    assert direct.count("invoke_one_shot_host_runtime") == 1
    forbidden = {
        "inspect_local_immutable_image",
        "materialize_one_shot_invocation",
        "claim_execution_lease",
        "run_one_shot_authorized_runtime",
        "Popen",
        "run",
    }
    assert set(direct).isdisjoint(forbidden)

    verifier_tree = ast.parse(
        VERIFIER.read_text(encoding="utf-8", errors="strict")
    )
    verifier_calls = {
        node.func.id
        for node in ast.walk(verifier_tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert (
        "execute_one_shot_engineering_invocation_runtime_operation"
        not in verifier_calls
    )


def test_runtime_operation_record_is_reconstructible_and_documented() -> None:
    built = build_engineering_invocation_runtime_operation()
    frozen = load_engineering_invocation_runtime_operation(RECORD)
    assert built == frozen

    payload = _json(RECORD)
    assert payload["next_slice"] == (
        "QW-LC4-E-one-shot-engineering-invocation-"
        "runtime-operation-commit"
    )
    assert payload["post_merge_next_slice"] == (
        "QW-LC4-E-one-shot-engineering-invocation-"
        "runtime-operation-execution"
    )
    assert not EXECUTION_LEASE.exists()
    assert not OUTPUT_ROOT.exists()
    assert not tuple(
        OUTPUT_ROOT.parent.glob(f".{OUTPUT_ROOT.name}.staging-*")
    )

    decision_marker = (
        "ADR-081-stage3b-qwake-lc4-e-one-shot-engineering-"
        "invocation-runtime-operation"
    )
    required = (
        ROOT / "STATUS.md",
        ROOT / "STATUS_EN.md",
        ROOT / "docs/qwake-local-compute-extension.md",
        ROOT / "docs/qwake-local-compute-extension_EN.md",
        ROOT / "docs/decisions/index.md",
        ROOT / "docs/decisions/index_EN.md",
        ROOT / "docs/language-map.csv",
        ROOT / "docs/research-log/2026-07.md",
        ROOT / "docs/research-log/2026-07_EN.md",
    )
    for path in required:
        assert decision_marker in path.read_text(
            encoding="utf-8", errors="strict"
        )
