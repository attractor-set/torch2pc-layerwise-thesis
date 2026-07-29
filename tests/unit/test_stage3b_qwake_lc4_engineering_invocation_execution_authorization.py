# Validate the QW-LC4-E one-shot execution authorization record.

from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import pytest

from torch2pc_thesis import (
    stage3b_qwake_lc4_engineering_invocation_execution_authorization as authorization_module,
)
from torch2pc_thesis.stage3b_qwake_lc4_engineering_invocation_execution_authorization import (
    EXECUTION_AUTHORIZATION_ID,
    EXECUTION_AUTHORIZATION_STATUS,
    EXECUTION_BASE_COMMIT,
    QWakeLC4EngineeringInvocationExecutionAuthorizationError,
    build_engineering_invocation_execution_authorization,
    load_engineering_invocation_execution_authorization,
    verify_engineering_invocation_execution_authorization,
)

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / (
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-one-shot-engineering-invocation-"
    "execution-authorization-v1"
)
RECORD = PACKAGE / "authorization.json"
REGISTRY = PACKAGE / "SHA256SUMS"
MODULE = ROOT / (
    "src/torch2pc_thesis/"
    "stage3b_qwake_lc4_engineering_invocation_execution_authorization.py"
)
VERIFIER = ROOT / (
    "scripts/verify_stage3b_qwake_lc4_engineering_"
    "invocation_execution_authorization.py"
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


def test_execution_authorization_package_is_exact_and_canonical() -> None:
    assert sorted(path.name for path in PACKAGE.iterdir()) == [
        "SHA256SUMS",
        "authorization.json",
    ]
    expected, relative = REGISTRY.read_text(
        encoding="utf-8", errors="strict"
    ).strip().split("  ", 1)
    assert relative == "authorization.json"
    assert _sha256(RECORD) == "sha256:" + expected

    authorization = load_engineering_invocation_execution_authorization(
        RECORD
    )
    assert RECORD.read_text(encoding="utf-8") == (
        authorization.canonical_json()
    )
    assert authorization.authorization_id == EXECUTION_AUTHORIZATION_ID
    assert authorization.status == EXECUTION_AUTHORIZATION_STATUS
    assert authorization.source.execution_base_commit == EXECUTION_BASE_COMMIT


def test_execution_authorization_verifies_exact_operation_merge() -> None:
    authorization = verify_engineering_invocation_execution_authorization(ROOT)

    assert authorization.source.operation_pr_number == 139
    assert authorization.source.operation_head_commit == (
        "aa8886221e286a5881f2b720414859bb313c2867"
    )
    assert authorization.source.operation_parent_commit == (
        "28be77706bc86abaf34f86e9bdcbdcb9cc2810a8"
    )
    assert authorization.source.operation_sha256 == (
        "sha256:10a612ef1b765362b361ecea57923d00a9f7339c9d3f9e3b27337f92f15326e9"
    )
    assert authorization.source.image_repo_digest.endswith(
        "7da92b8f77f6dc37d42db832c5613ef6149dc488adc5b66465faa33e48ca021d"
    )


def test_execution_authorization_is_single_future_invocation() -> None:
    authorization = verify_engineering_invocation_execution_authorization(ROOT)
    contract = authorization.contract

    assert contract.invocation_count == 1
    assert contract.future_preexecution_verification_authorized is True
    assert contract.future_one_shot_engineering_invocation_authorized is True
    assert contract.preexecution_verification_same_process_required is True
    assert contract.immutable_image_inspection_count_required == 2
    assert contract.invocation_materialization_count_required == 2
    assert contract.subprocess_popen_call_limit == 1
    assert contract.canonical_argv_equality_required is True
    assert contract.authorization_unconsumed_required is True
    assert contract.execution_lease_absence_required is True
    assert contract.output_absence_required is True
    assert contract.runtime_staging_absence_required is True


def test_execution_authorization_keeps_branch_effects_closed() -> None:
    authorization = verify_engineering_invocation_execution_authorization(ROOT)
    gates = authorization.gates

    assert gates.execution_authorization_record_present is True
    assert gates.execution_authorization_issued is True
    assert gates.preexecution_verification_materialization_implemented is True
    assert gates.preexecution_identity_verified is False
    assert gates.one_shot_engineering_invocation_execution_open is True
    assert gates.one_shot_engineering_invocation_permitted is False
    assert gates.branch_runtime_execution_permitted is False
    assert gates.execution_lease_materialized is False
    assert gates.authorization_consumed is False
    assert gates.runtime_execution_started is False
    assert gates.runtime_execution_performed is False
    assert gates.image_inspection_performed is False
    assert gates.invocation_command_materialized is False
    assert gates.docker_run_performed is False
    assert not EXECUTION_LEASE.exists()
    assert not OUTPUT_ROOT.exists()
    assert not tuple(
        OUTPUT_ROOT.parent.glob(f".{OUTPUT_ROOT.name}.staging-*")
    )


def test_execution_authorization_rejects_open_effects() -> None:
    authorization = verify_engineering_invocation_execution_authorization(ROOT)

    with pytest.raises(
        QWakeLC4EngineeringInvocationExecutionAuthorizationError,
        match="opened a runtime effect",
    ):
        replace(
            authorization,
            gates=replace(
                authorization.gates,
                one_shot_engineering_invocation_permitted=True,
            ),
        ).require()

    with pytest.raises(
        QWakeLC4EngineeringInvocationExecutionAuthorizationError,
        match="opened a runtime effect",
    ):
        replace(
            authorization,
            gates=replace(
                authorization.gates,
                preexecution_identity_verified=True,
            ),
        ).require()


def test_execution_authorization_rejects_multiple_invocations() -> None:
    authorization = verify_engineering_invocation_execution_authorization(ROOT)

    with pytest.raises(
        QWakeLC4EngineeringInvocationExecutionAuthorizationError,
        match="not single-invocation",
    ):
        replace(
            authorization,
            contract=replace(
                authorization.contract,
                invocation_count=2,
            ),
        ).require()


def test_effect_boundary_rejects_lease_output_and_staging(
    tmp_path: Path,
) -> None:
    output = tmp_path / authorization_module.AUTHORIZED_OUTPUT_ROOT
    lease = tmp_path / authorization_module.EXECUTION_LEASE_RELATIVE

    lease.parent.mkdir(parents=True)
    lease.write_text("{}\n", encoding="utf-8")
    with pytest.raises(
        QWakeLC4EngineeringInvocationExecutionAuthorizationError,
        match="execution lease",
    ):
        authorization_module._require_effect_boundary_closed(tmp_path)

    lease.unlink()
    output.mkdir(parents=True)
    with pytest.raises(
        QWakeLC4EngineeringInvocationExecutionAuthorizationError,
        match="runtime output",
    ):
        authorization_module._require_effect_boundary_closed(tmp_path)

    output.rmdir()
    staging = output.parent / f".{output.name}.staging-synthetic"
    staging.mkdir()
    with pytest.raises(
        QWakeLC4EngineeringInvocationExecutionAuthorizationError,
        match="runtime staging",
    ):
        authorization_module._require_effect_boundary_closed(tmp_path)


def test_sources_are_effect_free_and_documented() -> None:
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
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
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
        "ADR-079-stage3b-qwake-lc4-e-one-shot-engineering-"
        "invocation-execution-authorization"
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
        "QW-LC4-E-one-shot-engineering-invocation-"
        "execution-authorization-commit"
    )
    assert payload["post_merge_next_slice"] == (
        "QW-LC4-E-one-shot-engineering-invocation-"
        "preexecution-verification"
    )


def test_builder_is_deterministic_and_matches_frozen_record() -> None:
    built = build_engineering_invocation_execution_authorization()
    frozen = load_engineering_invocation_execution_authorization(RECORD)
    assert built == frozen
