# Validate the QW-LC4-E pre-execution verification contract.

from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import pytest

from torch2pc_thesis import (
    stage3b_qwake_lc4_engineering_invocation_preexecution_verification as verification_module,
)
from torch2pc_thesis.stage3b_qwake_lc4_engineering_invocation_preexecution_verification import (
    PREEXECUTION_BASE_COMMIT,
    PREEXECUTION_VERIFICATION_ID,
    PREEXECUTION_VERIFICATION_STATUS,
    QWakeLC4EngineeringInvocationPreexecutionVerificationError,
    build_engineering_invocation_preexecution_verification,
    load_engineering_invocation_preexecution_verification,
    verify_engineering_invocation_preexecution_verification,
)

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / (
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-one-shot-engineering-invocation-"
    "preexecution-verification-v1"
)
RECORD = PACKAGE / "verification.json"
REGISTRY = PACKAGE / "SHA256SUMS"
MODULE = ROOT / (
    "src/torch2pc_thesis/"
    "stage3b_qwake_lc4_engineering_invocation_preexecution_verification.py"
)
VERIFIER = ROOT / (
    "scripts/verify_stage3b_qwake_lc4_engineering_invocation_"
    "preexecution_verification.py"
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


def test_preexecution_package_is_exact_canonical_and_self_hashed() -> None:
    assert sorted(path.name for path in PACKAGE.iterdir()) == [
        "SHA256SUMS",
        "verification.json",
    ]
    expected, relative = REGISTRY.read_text(
        encoding="utf-8", errors="strict"
    ).strip().split("  ", 1)
    assert relative == "verification.json"
    assert _sha256(RECORD) == "sha256:" + expected

    verification = load_engineering_invocation_preexecution_verification(RECORD)
    assert RECORD.read_text(encoding="utf-8") == verification.canonical_json()
    assert verification.verification_id == PREEXECUTION_VERIFICATION_ID
    assert verification.status == PREEXECUTION_VERIFICATION_STATUS
    assert verification.source.preexecution_base_commit == PREEXECUTION_BASE_COMMIT


def test_preexecution_verifies_exact_merged_authorization_and_invoker() -> None:
    verification = verify_engineering_invocation_preexecution_verification(ROOT)
    source = verification.source

    assert source.authorization_pr_number == 140
    assert source.authorization_head_commit == (
        "9b7074cbb602fff77ad6770ea4978d3bdc73003b"
    )
    assert source.authorization_parent_commit == (
        "b0f6729e8fd1cb1aa172eef488dc56e36b335173"
    )
    assert source.execution_authorization_sha256 == (
        "sha256:ff136538faee0d7952dc444e521d7ec760c7d54cd38406cb9b19ff1e00d9437b"
    )
    assert source.host_runtime_invoker_implementation_state_sha256 == (
        "sha256:1f5f31d4f220bbf074736f1de0b78a5dafa2849188ac337704d5cc704668fdf4"
    )
    assert source.image_repo_digest.endswith(
        "7da92b8f77f6dc37d42db832c5613ef6149dc488adc5b66465faa33e48ca021d"
    )


def test_preexecution_contract_delegates_exact_same_process_sequence() -> None:
    verification = verify_engineering_invocation_preexecution_verification(ROOT)
    contract = verification.contract

    assert contract.direct_runtime_entrypoint_required == (
        "invoke_one_shot_host_runtime"
    )
    assert contract.runtime_entrypoint_call_count == 1
    assert contract.preexecution_and_spawn_same_process_required is True
    assert len(contract.required_host_resource_keys) == 13
    assert contract.image_inspection_count_required == 2
    assert contract.invocation_materialization_count_required == 2
    assert contract.image_inspection_equality_required is True
    assert contract.canonical_argv_equality_required is True
    assert contract.subprocess_popen_call_limit == 1
    assert contract.verifier_image_inspection_call_count == 0
    assert contract.verifier_invocation_materialization_call_count == 0
    assert contract.verifier_process_spawn_call_count == 0


def test_preexecution_keeps_dynamic_identity_and_effects_closed() -> None:
    verification = verify_engineering_invocation_preexecution_verification(ROOT)
    gates = verification.gates

    assert gates.preexecution_verification_record_present is True
    assert gates.preexecution_verifier_implemented is True
    assert gates.preexecution_static_contract_verified is True
    assert gates.preexecution_verification_slice_open is True
    assert gates.preexecution_identity_verified is False
    assert gates.one_shot_engineering_invocation_runtime_operation_open is False
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


def test_preexecution_rejects_open_runtime_gate() -> None:
    verification = verify_engineering_invocation_preexecution_verification(ROOT)

    with pytest.raises(
        QWakeLC4EngineeringInvocationPreexecutionVerificationError,
        match="opened a runtime effect",
    ):
        replace(
            verification,
            gates=replace(
                verification.gates,
                preexecution_identity_verified=True,
            ),
        ).require()


def test_preexecution_rejects_changed_source_identity() -> None:
    verification = verify_engineering_invocation_preexecution_verification(ROOT)

    with pytest.raises(
        QWakeLC4EngineeringInvocationPreexecutionVerificationError,
        match="source differs",
    ):
        replace(
            verification,
            source=replace(
                verification.source,
                preexecution_base_commit="0" * 40,
            ),
        ).require()


def test_preexecution_rejects_changed_dynamic_count() -> None:
    verification = verify_engineering_invocation_preexecution_verification(ROOT)

    with pytest.raises(
        QWakeLC4EngineeringInvocationPreexecutionVerificationError,
        match="contract differs",
    ):
        replace(
            verification,
            contract=replace(
                verification.contract,
                image_inspection_count_required=1,
            ),
        ).require()


def test_effect_boundary_rejects_lease_output_and_staging(
    tmp_path: Path,
) -> None:
    output = tmp_path / verification_module.AUTHORIZED_OUTPUT_ROOT
    lease = tmp_path / verification_module.EXECUTION_LEASE_RELATIVE

    lease.parent.mkdir(parents=True)
    lease.write_text("{}\n", encoding="utf-8")
    with pytest.raises(
        QWakeLC4EngineeringInvocationPreexecutionVerificationError,
        match="execution lease",
    ):
        verification_module._require_effect_boundary_closed(tmp_path)

    lease.unlink()
    output.mkdir(parents=True)
    with pytest.raises(
        QWakeLC4EngineeringInvocationPreexecutionVerificationError,
        match="runtime output",
    ):
        verification_module._require_effect_boundary_closed(tmp_path)

    output.rmdir()
    staging = output.parent / f".{output.name}.staging-synthetic"
    staging.mkdir()
    with pytest.raises(
        QWakeLC4EngineeringInvocationPreexecutionVerificationError,
        match="runtime staging",
    ):
        verification_module._require_effect_boundary_closed(tmp_path)


def test_preexecution_sources_do_not_call_runtime_effects() -> None:
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


def test_preexecution_record_is_reconstructible_and_documented() -> None:
    built = build_engineering_invocation_preexecution_verification()
    frozen = load_engineering_invocation_preexecution_verification(RECORD)
    assert built == frozen

    payload = _json(RECORD)
    assert payload["next_slice"] == (
        "QW-LC4-E-one-shot-engineering-invocation-"
        "preexecution-verification-commit"
    )
    assert payload["post_merge_next_slice"] == (
        "QW-LC4-E-one-shot-engineering-invocation-runtime-operation"
    )

    decision_marker = (
        "ADR-080-stage3b-qwake-lc4-e-one-shot-engineering-"
        "invocation-preexecution-verification"
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
