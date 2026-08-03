from __future__ import annotations

import ast
import hashlib
import json
import shutil
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from torch2pc_thesis.stage3b_qwake_lc4_final_engineering_invocation_authorization_consumption_attempt import (
    ATTEMPT_ID,
    ATTEMPT_STATUS,
    DURABLE_HOST_OUTCOME_RELATIVE,
    EXECUTION_LEASE_V1_RELATIVE,
    EXECUTION_LEASE_V2_RELATIVE,
    OPERATOR_ACTION_PHRASE,
    OPERATOR_IDENTITY,
    OUTPUT_ROOT,
    RUNTIME_ENTRYPOINT,
    SCOPE_FREEZE_MERGE_COMMIT,
    ConsumptionAttemptError,
    build_consumption_attempt,
    load_consumption_attempt,
    validate_consumption_attempt,
    verify_consumption_attempt_sources,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = PROJECT_ROOT / (
    "src/torch2pc_thesis/"
    "stage3b_qwake_lc4_final_engineering_invocation_authorization_"
    "consumption_attempt.py"
)
VERIFIER_PATH = PROJECT_ROOT / (
    "scripts/verify_stage3b_qwake_lc4_final_engineering_invocation_"
    "authorization_consumption_attempt.py"
)
PACKAGE_ROOT = PROJECT_ROOT / (
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-final-engineering-invocation-authorization-"
    "consumption-attempt-v1"
)


def _attempt():
    return build_consumption_attempt(
        attempt_prepared_at_utc="2026-08-03T19:53:00Z",
        authoring_base_commit=SCOPE_FREEZE_MERGE_COMMIT,
    )


def test_source_packages_and_semantics_are_exact() -> None:
    source = verify_consumption_attempt_sources(PROJECT_ROOT)
    assert source.scope_freeze_pr_number == 173
    assert source.scope_freeze_merge_commit == SCOPE_FREEZE_MERGE_COMMIT
    assert source.runtime_entrypoint_module_sha256.startswith("sha256:")


def test_attempt_round_trip_and_prepared_boundary(tmp_path: Path) -> None:
    attempt = _attempt()
    assert attempt.attempt_id == ATTEMPT_ID
    assert attempt.status == ATTEMPT_STATUS
    assert attempt.operator.identity == OPERATOR_IDENTITY
    assert attempt.operator.action_phrase == OPERATOR_ACTION_PHRASE
    assert attempt.gates.authorization_consumption_attempt_prepared is True
    assert attempt.gates.final_engineering_invocation_authorization_consumed is False
    assert attempt.gates.authorization_consumption_attempt_started is False
    assert (
        attempt.gates.authorization_consumption_attempt_atomic_action_permitted
        is False
    )

    path = tmp_path / "attempt.json"
    path.write_text(attempt.canonical_json(), encoding="utf-8")
    loaded = load_consumption_attempt(path)
    validate_consumption_attempt(
        loaded,
        verify_consumption_attempt_sources(PROJECT_ROOT),
        tmp_path,
        expected_authoring_base_commit=SCOPE_FREEZE_MERGE_COMMIT,
    )
    assert loaded == attempt


def test_semantic_hash_mutation_fails_closed() -> None:
    with pytest.raises(ConsumptionAttemptError, match="semantic SHA-256 differs"):
        replace(
            _attempt(),
            attempt_prepared_at_utc="2026-08-03T19:54:00Z",
        ).require()


def test_operator_and_phrase_mutations_fail_closed() -> None:
    attempt = _attempt()
    with pytest.raises(ConsumptionAttemptError):
        replace(
            attempt,
            operator=replace(attempt.operator, identity="different-operator"),
        ).require()
    with pytest.raises(ConsumptionAttemptError):
        replace(
            attempt,
            operator=replace(attempt.operator, action_phrase="DIFFERENT_PHRASE"),
        ).require()


def test_atomic_action_cannot_open_during_record_authoring() -> None:
    attempt = _attempt()
    for field_name in (
        "final_engineering_invocation_authorization_consumed",
        "final_engineering_invocation_started",
        "final_engineering_invocation_performed",
        "authorization_consumption_attempt_post_merge_verified",
        "authorization_consumption_attempt_atomic_action_permitted",
        "authorization_consumption_attempt_started",
        "invocation_command_materialized",
        "execution_lease_v2_present",
        "durable_host_outcome_present",
        "runtime_output_present",
        "qw5_transition_permitted",
    ):
        with pytest.raises(ConsumptionAttemptError):
            replace(
                attempt,
                gates=replace(attempt.gates, **{field_name: True}),
            ).require()


def test_existing_runtime_boundary_paths_fail_closed(tmp_path: Path) -> None:
    attempt = _attempt()
    source = verify_consumption_attempt_sources(PROJECT_ROOT)
    for relative in (
        Path(OUTPUT_ROOT),
        EXECUTION_LEASE_V1_RELATIVE,
        EXECUTION_LEASE_V2_RELATIVE,
        DURABLE_HOST_OUTCOME_RELATIVE,
    ):
        case_root = tmp_path / relative.name
        target = case_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if relative == Path(OUTPUT_ROOT):
            target.mkdir()
        else:
            target.write_text("{}\n", encoding="utf-8")
        with pytest.raises(ConsumptionAttemptError, match="already exists"):
            validate_consumption_attempt(
                attempt,
                source,
                case_root,
                expected_authoring_base_commit=SCOPE_FREEZE_MERGE_COMMIT,
            )


def test_negative_source_mutation_uses_temporary_copy(tmp_path: Path) -> None:
    source_scope = PROJECT_ROOT / (
        "experiments/frozen/"
        "stage3b-qwake-lc4-e-final-engineering-invocation-authorization-"
        "consumption-attempt-scope-freeze-v1"
    )
    copied_root = tmp_path / "repository"
    copied_scope = copied_root / source_scope.relative_to(PROJECT_ROOT)
    copied_scope.parent.mkdir(parents=True)
    shutil.copytree(source_scope, copied_scope)
    scope_json = copied_scope / "scope.json"
    scope_json.write_text(
        scope_json.read_text(encoding="utf-8") + " ",
        encoding="utf-8",
    )
    with pytest.raises(ConsumptionAttemptError, match="registry digest differs"):
        verify_consumption_attempt_sources(copied_root)


def test_attempt_surfaces_do_not_import_or_invoke_runtime() -> None:
    module_text = MODULE_PATH.read_text(encoding="utf-8")
    verifier_text = VERIFIER_PATH.read_text(encoding="utf-8")
    combined = module_text + "\n" + verifier_text
    forbidden = (
        "subprocess.Popen(",
        "subprocess.run(",
        "docker run",
        "docker image inspect",
        "import torch",
        "from torch import",
        "stage3b_qwake_lc4_lease_bound_host_invoker_wiring import",
        f"{RUNTIME_ENTRYPOINT}(",
    )
    assert all(marker not in combined for marker in forbidden)
    assert "stage3b_qwake_lc4_lease_bound_host_invoker_wiring.py" in module_text
    assert RUNTIME_ENTRYPOINT in module_text
    for source_text in (module_text, verifier_text):
        tree = ast.parse(source_text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported = tuple(alias.name for alias in node.names)
                assert all(
                    name != "torch"
                    and not name.startswith("torch.")
                    and "lease_bound_host_invoker_wiring" not in name
                    for name in imported
                )
            if isinstance(node, ast.ImportFrom):
                imported_from = node.module or ""
                assert imported_from != "torch"
                assert not imported_from.startswith("torch.")
                assert "lease_bound_host_invoker_wiring" not in imported_from


def test_frozen_attempt_package_and_verifier() -> None:
    attempt_path = PACKAGE_ROOT / "attempt.json"
    source_registry = PACKAGE_ROOT / "source-SHA256SUMS"
    registry = PACKAGE_ROOT / "SHA256SUMS"
    assert attempt_path.is_file()
    assert source_registry.is_file()
    assert registry.is_file()

    entries = {}
    for line in registry.read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", 1)
        entries[relative] = digest
    assert set(entries) == {"attempt.json", "source-SHA256SUMS"}
    assert hashlib.sha256(attempt_path.read_bytes()).hexdigest() == entries[
        "attempt.json"
    ]
    assert hashlib.sha256(source_registry.read_bytes()).hexdigest() == entries[
        "source-SHA256SUMS"
    ]

    loaded = load_consumption_attempt(attempt_path)
    assert loaded.attempt_id == ATTEMPT_ID
    completed = subprocess.run(
        [
            sys.executable,
            str(VERIFIER_PATH),
            "--project-root",
            str(PROJECT_ROOT),
            "--attempt",
            str(attempt_path),
            "--authoring-base-commit",
            SCOPE_FREEZE_MERGE_COMMIT,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "AUTHORIZATION_CONSUMPTION_ATTEMPT_VERIFIED=true" in completed.stdout
    assert "AUTHORIZATION_CONSUMPTION_ATTEMPT_PREPARED=true" in completed.stdout
    assert (
        "AUTHORIZATION_CONSUMPTION_ATTEMPT_POST_MERGE_VERIFIED=false"
        in completed.stdout
    )
    assert "FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_CONSUMED=false" in completed.stdout


def test_repository_documentation_records_attempt_authoring() -> None:
    marker = (
        "ADR-106-stage3b-qwake-lc4-e-final-engineering-invocation-"
        "authorization-consumption-attempt-record-authoring"
    )
    required = (
        PROJECT_ROOT / "STATUS.md",
        PROJECT_ROOT / "STATUS_EN.md",
        PROJECT_ROOT / "docs/qwake-local-compute-extension.md",
        PROJECT_ROOT / "docs/qwake-local-compute-extension_EN.md",
        PROJECT_ROOT / "docs/decisions/index.md",
        PROJECT_ROOT / "docs/decisions/index_EN.md",
        PROJECT_ROOT / "docs/language-map.csv",
        PROJECT_ROOT / "docs/research-log/2026-07.md",
        PROJECT_ROOT / "docs/research-log/2026-07_EN.md",
    )
    for path in required:
        assert marker in path.read_text(encoding="utf-8")

    payload = json.loads(
        (PACKAGE_ROOT / "attempt.json").read_text(encoding="utf-8")
    )
    gates = payload["gates"]
    assert gates["authorization_consumption_attempt_prepared"] is True
    assert gates["final_engineering_invocation_authorization_consumed"] is False
    assert gates["authorization_consumption_attempt_started"] is False
