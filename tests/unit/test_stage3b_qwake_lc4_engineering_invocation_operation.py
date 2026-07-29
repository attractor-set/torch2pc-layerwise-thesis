# Validate the QW-LC4-E one-shot engineering invocation operation record.

from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import pytest

from torch2pc_thesis import (
    stage3b_qwake_lc4_engineering_invocation_operation as operation_module,
)
from torch2pc_thesis.stage3b_qwake_lc4_engineering_invocation_operation import (
    INVOCATION_OPERATION_ID,
    INVOCATION_OPERATION_STATUS,
    OPERATION_BASE_COMMIT,
    REQUIRED_HOST_RESOURCE_KEYS,
    QWakeLC4EngineeringInvocationOperationError,
    load_engineering_invocation_operation,
    verify_engineering_invocation_operation,
)

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / (
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-one-shot-engineering-invocation-operation-v1"
)
RECORD = PACKAGE / "operation.json"
REGISTRY = PACKAGE / "SHA256SUMS"
MODULE = ROOT / (
    "src/torch2pc_thesis/"
    "stage3b_qwake_lc4_engineering_invocation_operation.py"
)
VERIFIER = ROOT / (
    "scripts/verify_stage3b_qwake_lc4_engineering_invocation_operation.py"
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


def test_operation_package_is_exact_canonical_and_self_hashed() -> None:
    assert sorted(path.name for path in PACKAGE.iterdir()) == [
        "SHA256SUMS",
        "operation.json",
    ]
    expected, relative = REGISTRY.read_text(
        encoding="utf-8", errors="strict"
    ).strip().split("  ", 1)
    assert relative == "operation.json"
    assert _sha256(RECORD) == "sha256:" + expected

    operation = load_engineering_invocation_operation(RECORD)
    assert RECORD.read_text(encoding="utf-8") == operation.canonical_json()
    assert operation.operation_id == INVOCATION_OPERATION_ID
    assert operation.status == INVOCATION_OPERATION_STATUS
    assert operation.source.operation_base_commit == OPERATION_BASE_COMMIT


def test_operation_verifies_exact_merged_sources() -> None:
    operation = verify_engineering_invocation_operation(ROOT)

    assert operation.source.admission_pr_number == 138
    assert operation.source.admission_head_commit == (
        "a26419057c133972b18a728575426ef510bcf360"
    )
    assert operation.source.admission_parent_commit == (
        "3454d12d3cc16c9c50977e2a598e2bc1a8768441"
    )
    assert operation.source.admission_sha256 == (
        "sha256:fe07bc20bf5866d84730df945c2ababc7b5f4f255648c5de6e3185ba4e37c01d"
    )
    assert operation.source.host_runtime_invoker_implementation_state_sha256 == (
        "sha256:1f5f31d4f220bbf074736f1de0b78a5dafa2849188ac337704d5cc704668fdf4"
    )
    assert operation.source.image_repo_digest.endswith(
        "7da92b8f77f6dc37d42db832c5613ef6149dc488adc5b66465faa33e48ca021d"
    )


def test_operation_records_exact_future_dynamic_requirements() -> None:
    operation = verify_engineering_invocation_operation(ROOT)
    checks = operation.checks

    assert checks.invocation_admission_complete is True
    assert checks.required_host_resource_keys == REQUIRED_HOST_RESOURCE_KEYS
    assert checks.immutable_image_inspection_count_required == 2
    assert checks.invocation_materialization_count_required == 2
    assert checks.subprocess_popen_call_limit == 1
    assert checks.canonical_argv_equality_required is True
    assert checks.authorization_unconsumed_required_at_execution is True
    assert checks.execution_lease_absence_required_at_execution is True
    assert checks.output_absence_required_at_execution is True
    assert checks.runtime_staging_absence_required_at_execution is True
    assert checks.no_retry_after_spawn_required is True
    assert checks.host_execution_lease_write_forbidden is True
    assert checks.preexecution_identity_checks_implemented is True
    assert checks.preexecution_identity_verified is False


def test_operation_keeps_every_runtime_effect_closed() -> None:
    operation = verify_engineering_invocation_operation(ROOT)
    gates = operation.gates

    assert gates.invocation_operation_record_present is True
    assert gates.one_shot_engineering_invocation_slice_open is True
    assert gates.one_shot_engineering_invocation_operation_open is True
    assert gates.one_shot_engineering_invocation_permitted is False
    assert gates.one_shot_engineering_invocation_performed is False
    assert gates.branch_runtime_execution_permitted is False
    assert gates.execution_lease_materialized is False
    assert gates.authorization_consumed is False
    assert gates.runtime_execution_started is False
    assert gates.runtime_execution_performed is False
    assert gates.image_inspection_performed is False
    assert gates.invocation_command_materialized is False
    assert gates.docker_run_performed is False
    assert gates.local_compute_execution_open is False
    assert not EXECUTION_LEASE.exists()
    assert not OUTPUT_ROOT.exists()
    assert not tuple(
        OUTPUT_ROOT.parent.glob(f".{OUTPUT_ROOT.name}.staging-*")
    )


def test_operation_rejects_open_effect_or_runtime_verification() -> None:
    operation = verify_engineering_invocation_operation(ROOT)

    with pytest.raises(
        QWakeLC4EngineeringInvocationOperationError,
        match="opened a runtime effect",
    ):
        replace(
            operation,
            gates=replace(
                operation.gates,
                one_shot_engineering_invocation_permitted=True,
            ),
        ).require()

    with pytest.raises(
        QWakeLC4EngineeringInvocationOperationError,
        match="verified during authoring",
    ):
        replace(
            operation,
            checks=replace(
                operation.checks,
                preexecution_identity_verified=True,
            ),
        ).require()


def test_operation_rejects_changed_source_identity() -> None:
    operation = verify_engineering_invocation_operation(ROOT)

    with pytest.raises(
        QWakeLC4EngineeringInvocationOperationError,
        match="source differs",
    ):
        replace(
            operation,
            source=replace(
                operation.source,
                operation_base_commit="0" * 40,
            ),
        ).require()


def test_effect_boundary_rejects_lease_output_and_staging(
    tmp_path: Path,
) -> None:
    output = tmp_path / operation_module.AUTHORIZED_OUTPUT_ROOT
    lease = tmp_path / operation_module.EXECUTION_LEASE_RELATIVE

    lease.parent.mkdir(parents=True)
    lease.write_text("{}\n", encoding="utf-8")
    with pytest.raises(
        QWakeLC4EngineeringInvocationOperationError,
        match="execution lease",
    ):
        operation_module._require_effect_boundary_closed(tmp_path)

    lease.unlink()
    output.mkdir(parents=True)
    with pytest.raises(
        QWakeLC4EngineeringInvocationOperationError,
        match="runtime output",
    ):
        operation_module._require_effect_boundary_closed(tmp_path)

    output.rmdir()
    staging = output.parent / f".{output.name}.staging-synthetic"
    staging.mkdir()
    with pytest.raises(
        QWakeLC4EngineeringInvocationOperationError,
        match="runtime staging",
    ):
        operation_module._require_effect_boundary_closed(tmp_path)


def test_operation_sources_are_effect_free_and_documented() -> None:
    forbidden_calls = {
        "invoke_one_shot_host_runtime",
        "inspect_local_immutable_image",
        "materialize_one_shot_invocation",
        "claim_execution_lease",
        "execute_authorized_runtime",
        "run_one_shot_authorized_runtime",
        "Popen",
        "run",
    }
    for path in (MODULE, VERIFIER):
        tree = ast.parse(path.read_text(encoding="utf-8", errors="strict"))
        called = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        attributes = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }
        assert called.isdisjoint(forbidden_calls)
        assert attributes.isdisjoint(forbidden_calls)

    combined = MODULE.read_text(encoding="utf-8") + VERIFIER.read_text(
        encoding="utf-8"
    )
    for marker in (
        "docker image inspect",
        "docker run",
        "subprocess.Popen",
        "invoke_one_shot_host_runtime(",
    ):
        assert marker not in combined

    decision_marker = (
        "ADR-078-stage3b-qwake-lc4-e-one-shot-engineering-"
        "invocation-operation"
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

    payload = _json(RECORD)
    assert payload["next_slice"] == (
        "QW-LC4-E-one-shot-engineering-invocation-operation-commit"
    )
    assert payload["post_merge_next_slice"] == (
        "QW-LC4-E-one-shot-engineering-invocation-execution"
    )
