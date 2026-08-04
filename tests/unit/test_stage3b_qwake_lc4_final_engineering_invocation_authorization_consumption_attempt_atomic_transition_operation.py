from __future__ import annotations

import ast
import json
import os
import shutil
import stat
from dataclasses import replace
from pathlib import Path

import pytest

import torch2pc_thesis.stage3b_qwake_lc4_final_engineering_invocation_authorization_consumption_attempt_atomic_transition_operation as operation_module
from torch2pc_thesis.stage3b_qwake_lc4_final_engineering_invocation_authorization import (
    AUTHORIZATION_ACTION_PHRASE,
)
from torch2pc_thesis.stage3b_qwake_lc4_final_engineering_invocation_authorization_consumption_attempt_atomic_transition import (
    EXECUTION_LEASE_V2_RELATIVE,
    OUTPUT_ROOT,
)
from torch2pc_thesis.stage3b_qwake_lc4_final_engineering_invocation_authorization_consumption_attempt_atomic_transition_operation import (
    FROZEN_TORCH2PC_COMMIT,
    OPERATION_AUTHORING_BASE_COMMIT,
    OPERATION_ENTRYPOINT,
    OPERATION_ID,
    OPERATION_STATUS,
    OPERATOR_IDENTITY,
    OPERATOR_IDENTITY_KIND,
    AtomicTransitionOperationCommittedError,
    AtomicTransitionOperationError,
    AtomicTransitionOperationUnknownStateError,
    build_atomic_transition_operation_admission,
    build_atomic_transition_operation_record,
    execute_final_engineering_invocation_atomic_transition_operation_once,
    load_atomic_transition_operation,
    validate_atomic_transition_operation,
    verify_atomic_transition_operation_sources,
)
from torch2pc_thesis.stage3b_qwake_lc4_persistent_evidence_chain_v2 import (
    PERSISTENT_LEASE_V2_OPERATOR_ACKNOWLEDGEMENT,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = PROJECT_ROOT / (
    "src/torch2pc_thesis/stage3b_qwake_lc4_final_engineering_invocation_"
    "authorization_consumption_attempt_atomic_transition_operation.py"
)
VERIFIER_PATH = PROJECT_ROOT / (
    "scripts/verify_stage3b_qwake_lc4_final_engineering_invocation_"
    "authorization_consumption_attempt_atomic_transition_operation.py"
)
PACKAGE_ROOT = PROJECT_ROOT / (
    "experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-"
    "authorization-consumption-attempt-atomic-transition-operation-v1"
)


def _record():
    return build_atomic_transition_operation_record(
        authored_at_utc="2026-08-04T02:29:00Z",
        authoring_base_commit=OPERATION_AUTHORING_BASE_COMMIT,
    )


def _admission(
    *,
    verified: bool = True,
    merge_commit: str = "f" * 40,
    clean: bool = True,
):
    return build_atomic_transition_operation_admission(
        operation_post_merge_verified=verified,
        operation_implementation_merge_commit=merge_commit,
        repository_head=merge_commit,
        worktree_and_index_clean=clean,
        torch2pc_head=FROZEN_TORCH2PC_COMMIT,
        operator_identity_kind=OPERATOR_IDENTITY_KIND,
        operator_identity=OPERATOR_IDENTITY,
        authorization_action_phrase=AUTHORIZATION_ACTION_PHRASE,
        persistent_lease_acknowledgement=(
            PERSISTENT_LEASE_V2_OPERATOR_ACKNOWLEDGEMENT
        ),
    )


def _sandbox(tmp_path: Path) -> Path:
    root = tmp_path / "repository"
    root.mkdir()
    for relative in (
        Path("docs"),
        Path("experiments/frozen"),
        Path("scripts"),
        Path("src"),
        Path("tests"),
    ):
        shutil.copytree(
            PROJECT_ROOT / relative,
            root / relative,
            copy_function=os.link,
        )
    (root / "external/Torch2PC").mkdir(parents=True)
    (root / "results/stage-3").mkdir(parents=True)
    return root


def test_source_packages_and_operation_record_are_exact() -> None:
    source = verify_atomic_transition_operation_sources(PROJECT_ROOT)
    assert source.scope_pr_number == 177
    record = load_atomic_transition_operation(PACKAGE_ROOT / "operation.json")
    validate_atomic_transition_operation(
        record,
        source,
        PROJECT_ROOT,
        expected_authoring_base_commit=OPERATION_AUTHORING_BASE_COMMIT,
    )
    assert record.operation_id == OPERATION_ID
    assert record.status == OPERATION_STATUS
    assert record.contract.operation_entrypoint == OPERATION_ENTRYPOINT


def test_record_round_trip_and_closed_authoring_boundary(tmp_path: Path) -> None:
    record = _record()
    path = tmp_path / "operation.json"
    path.write_text(record.canonical_json(), encoding="utf-8")
    loaded = load_atomic_transition_operation(path)
    assert loaded == record
    assert loaded.gates.operation_authored is True
    assert loaded.gates.operation_post_merge_verified is False
    assert loaded.gates.atomic_action_permitted is False
    assert loaded.boundary.operation_invoked is False


def test_record_mutations_fail_closed() -> None:
    record = _record()
    with pytest.raises(
        AtomicTransitionOperationError,
        match="semantic SHA-256 differs",
    ):
        replace(record, authored_at_utc="2026-08-04T02:30:00Z").require()
    with pytest.raises(AtomicTransitionOperationError):
        replace(
            record,
            gates=replace(record.gates, atomic_action_permitted=True),
        ).require()
    with pytest.raises(AtomicTransitionOperationError):
        replace(
            record,
            boundary=replace(record.boundary, operation_invoked=True),
        ).require()


def test_admission_requires_merged_operation_and_exact_repository() -> None:
    with pytest.raises(AtomicTransitionOperationError, match="post-merge"):
        _admission(verified=False)
    with pytest.raises(AtomicTransitionOperationError, match="not terminal"):
        _admission(merge_commit=OPERATION_AUTHORING_BASE_COMMIT)
    with pytest.raises(AtomicTransitionOperationError, match="not clean"):
        _admission(clean=False)
    with pytest.raises(AtomicTransitionOperationError, match="repository head"):
        build_atomic_transition_operation_admission(
            operation_post_merge_verified=True,
            operation_implementation_merge_commit="f" * 40,
            repository_head="e" * 40,
            worktree_and_index_clean=True,
            torch2pc_head=FROZEN_TORCH2PC_COMMIT,
            operator_identity_kind=OPERATOR_IDENTITY_KIND,
            operator_identity=OPERATOR_IDENTITY,
            authorization_action_phrase=AUTHORIZATION_ACTION_PHRASE,
            persistent_lease_acknowledgement=(
                PERSISTENT_LEASE_V2_OPERATOR_ACKNOWLEDGEMENT
            ),
        )


def test_operation_materializes_one_time_and_delegates_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _sandbox(tmp_path)
    clock_calls = 0

    def clock() -> str:
        nonlocal clock_calls
        clock_calls += 1
        return "2026-08-04T03:00:00Z"

    delegated_calls = 0
    original = operation_module.execute_final_engineering_invocation_atomic_transition_once

    def delegated(*args, **kwargs):
        nonlocal delegated_calls
        delegated_calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(operation_module, "_utc_now_z", clock)
    monkeypatch.setattr(
        operation_module,
        "execute_final_engineering_invocation_atomic_transition_once",
        delegated,
    )
    result = execute_final_engineering_invocation_atomic_transition_operation_once(
        root,
        admission=_admission(),
    )
    target = root / EXECUTION_LEASE_V2_RELATIVE
    assert clock_calls == 1
    assert delegated_calls == 1
    assert result.claimed_at_utc == "2026-08-04T03:00:00Z"
    assert result.delegated_transition_call_count == 1
    assert target.is_file()
    assert not target.is_symlink()
    assert stat.S_IMODE(target.stat().st_mode) == 0o600
    assert target.read_text(encoding="utf-8") == (
        result.transition_result.lease.canonical_json()
    )
    assert result.transition_result.authorization_consumed is True
    assert result.transition_result.attempt_started is True
    assert result.transition_result.atomic_action_committed is True
    assert result.runtime_execution_started is False
    assert result.retry_permitted is False
    assert not (root / OUTPUT_ROOT).exists()


def test_exact_existing_commit_forbids_retry_before_clock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _sandbox(tmp_path)
    monkeypatch.setattr(
        operation_module,
        "_utc_now_z",
        lambda: "2026-08-04T03:01:00Z",
    )
    execute_final_engineering_invocation_atomic_transition_operation_once(
        root,
        admission=_admission(),
    )

    def forbidden_clock() -> str:
        raise AssertionError("clock must not be called after commit")

    monkeypatch.setattr(operation_module, "_utc_now_z", forbidden_clock)
    with pytest.raises(
        AtomicTransitionOperationCommittedError,
        match="retry forbidden",
    ):
        execute_final_engineering_invocation_atomic_transition_operation_once(
            root,
            admission=_admission(),
        )


def test_invalid_existing_lease_is_unknown_before_clock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _sandbox(tmp_path)
    target = root / EXECUTION_LEASE_V2_RELATIVE
    target.write_text("{}\n", encoding="utf-8")
    target.chmod(0o600)

    def forbidden_clock() -> str:
        raise AssertionError("clock must not be called for unknown state")

    monkeypatch.setattr(operation_module, "_utc_now_z", forbidden_clock)
    with pytest.raises(
        AtomicTransitionOperationUnknownStateError,
        match="retry forbidden",
    ):
        execute_final_engineering_invocation_atomic_transition_operation_once(
            root,
            admission=_admission(),
        )


def test_other_boundary_object_is_unknown_before_clock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _sandbox(tmp_path)
    (root / OUTPUT_ROOT).mkdir(parents=True)

    def forbidden_clock() -> str:
        raise AssertionError("clock must not be called for ambiguous boundary")

    monkeypatch.setattr(operation_module, "_utc_now_z", forbidden_clock)
    with pytest.raises(
        AtomicTransitionOperationUnknownStateError,
        match="retry forbidden",
    ):
        execute_final_engineering_invocation_atomic_transition_operation_once(
            root,
            admission=_admission(),
        )


def test_failed_admission_does_not_materialize_time_or_lease(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _sandbox(tmp_path)

    def forbidden_clock() -> str:
        raise AssertionError("clock must not be called before admission")

    monkeypatch.setattr(operation_module, "_utc_now_z", forbidden_clock)
    bad = replace(_admission(), operation_post_merge_verified=False)
    with pytest.raises(AtomicTransitionOperationError, match="post-merge"):
        execute_final_engineering_invocation_atomic_transition_operation_once(
            root,
            admission=bad,
        )
    assert not (root / EXECUTION_LEASE_V2_RELATIVE).exists()


def test_authoring_surfaces_do_not_import_or_call_runtime() -> None:
    module_text = MODULE_PATH.read_text(encoding="utf-8")
    verifier_text = VERIFIER_PATH.read_text(encoding="utf-8")
    assert "stage3b_qwake_lc4_lease_bound_host_invoker_wiring import" not in module_text
    assert "subprocess" not in module_text
    assert "docker run" not in module_text
    assert "import torch" not in module_text
    for source_text in (module_text, verifier_text):
        tree = ast.parse(source_text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(
                    alias.name != "subprocess"
                    and alias.name != "torch"
                    and not alias.name.startswith("torch.")
                    and "lease_bound_host_invoker_wiring" not in alias.name
                    for alias in node.names
                )
            if isinstance(node, ast.ImportFrom):
                imported_from = node.module or ""
                assert imported_from != "subprocess"
                assert imported_from != "torch"
                assert not imported_from.startswith("torch.")
                assert "lease_bound_host_invoker_wiring" not in imported_from


def test_frozen_operation_package_is_canonical() -> None:
    expected = {"operation.json", "source-SHA256SUMS", "SHA256SUMS"}
    assert {path.name for path in PACKAGE_ROOT.iterdir()} == expected
    registry = {}
    for line in (PACKAGE_ROOT / "SHA256SUMS").read_text(
        encoding="utf-8"
    ).splitlines():
        digest, relative = line.split("  ", 1)
        registry[relative] = digest
    assert set(registry) == {"operation.json", "source-SHA256SUMS"}
    for relative, digest in registry.items():
        assert __import__("hashlib").sha256(
            (PACKAGE_ROOT / relative).read_bytes()
        ).hexdigest() == digest
    raw = (PACKAGE_ROOT / "operation.json").read_text(encoding="utf-8")
    assert raw == load_atomic_transition_operation(
        PACKAGE_ROOT / "operation.json"
    ).canonical_json()
    mapping = json.loads(raw)
    assert mapping["gates"]["atomic_action_permitted"] is False
    assert mapping["boundary"]["operation_invoked"] is False
