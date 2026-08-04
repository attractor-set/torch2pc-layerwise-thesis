from __future__ import annotations

import ast
import json
import os
import shutil
import stat
from dataclasses import replace
from pathlib import Path

import pytest

from torch2pc_thesis.stage3b_qwake_lc4_final_engineering_invocation_authorization import (
    AUTHORIZATION_ACTION_PHRASE,
)
from torch2pc_thesis.stage3b_qwake_lc4_final_engineering_invocation_authorization_consumption_attempt_atomic_transition import (
    ATOMIC_ENTRYPOINT,
    ATOMIC_TRANSITION_ID,
    ATOMIC_TRANSITION_STATUS,
    AUTHORING_BASE_COMMIT,
    EXECUTION_LEASE_V2_RELATIVE,
    OPERATOR_IDENTITY,
    OPERATOR_IDENTITY_KIND,
    AtomicTransitionCommittedError,
    AtomicTransitionError,
    AtomicTransitionUnknownStateError,
    build_atomic_transition_admission,
    build_atomic_transition_record,
    execute_final_engineering_invocation_atomic_transition_once,
    load_atomic_transition,
    validate_atomic_transition,
    verify_atomic_transition_sources,
)
from torch2pc_thesis.stage3b_qwake_lc4_persistent_evidence_chain_v2 import (
    PERSISTENT_LEASE_V2_OPERATOR_ACKNOWLEDGEMENT,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = PROJECT_ROOT / (
    "src/torch2pc_thesis/stage3b_qwake_lc4_final_engineering_invocation_"
    "authorization_consumption_attempt_atomic_transition.py"
)
VERIFIER_PATH = PROJECT_ROOT / (
    "scripts/verify_stage3b_qwake_lc4_final_engineering_invocation_"
    "authorization_consumption_attempt_atomic_transition.py"
)
PACKAGE_ROOT = PROJECT_ROOT / (
    "experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-"
    "authorization-consumption-attempt-atomic-transition-v1"
)


def _record():
    return build_atomic_transition_record(
        authored_at_utc="2026-08-04T00:18:00Z",
        authoring_base_commit=AUTHORING_BASE_COMMIT,
    )


def _admission(*, verified: bool = True, commit: str = "f" * 40):
    return build_atomic_transition_admission(
        transition_post_merge_verified=verified,
        implementation_merge_commit=commit,
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


def test_source_packages_and_transition_record_are_exact() -> None:
    source = verify_atomic_transition_sources(PROJECT_ROOT)
    assert source.atomic_scope_pr_number == 175
    record = load_atomic_transition(PACKAGE_ROOT / "transition.json")
    validate_atomic_transition(
        record,
        source,
        PROJECT_ROOT,
        expected_authoring_base_commit=AUTHORING_BASE_COMMIT,
    )
    assert record.transition_id == ATOMIC_TRANSITION_ID
    assert record.status == ATOMIC_TRANSITION_STATUS
    assert record.contract.atomic_entrypoint == ATOMIC_ENTRYPOINT


def test_record_round_trip_and_closed_authoring_boundary(tmp_path: Path) -> None:
    record = _record()
    path = tmp_path / "transition.json"
    path.write_text(record.canonical_json(), encoding="utf-8")
    loaded = load_atomic_transition(path)
    assert loaded == record
    assert loaded.gates.atomic_transition_authored is True
    assert loaded.gates.atomic_action_permitted is False
    assert loaded.gates.atomic_action_committed is False
    assert loaded.gates.consumption_attempt_started is False


def test_record_mutations_fail_closed() -> None:
    record = _record()
    with pytest.raises(AtomicTransitionError, match="semantic SHA-256 differs"):
        replace(record, authored_at_utc="2026-08-04T00:19:00Z").require()
    with pytest.raises(AtomicTransitionError):
        replace(
            record,
            gates=replace(record.gates, atomic_action_permitted=True),
        ).require()
    with pytest.raises(AtomicTransitionError):
        replace(
            record,
            boundary=replace(record.boundary, authorization_consumed=True),
        ).require()


def test_admission_requires_post_merge_and_exact_operator() -> None:
    with pytest.raises(AtomicTransitionError, match="post-merge"):
        _admission(verified=False)
    with pytest.raises(AtomicTransitionError, match="not terminal"):
        _admission(commit=AUTHORING_BASE_COMMIT)
    with pytest.raises(AtomicTransitionError, match="identity differs"):
        build_atomic_transition_admission(
            transition_post_merge_verified=True,
            implementation_merge_commit="f" * 40,
            operator_identity_kind=OPERATOR_IDENTITY_KIND,
            operator_identity="different",
            authorization_action_phrase=AUTHORIZATION_ACTION_PHRASE,
            persistent_lease_acknowledgement=(
                PERSISTENT_LEASE_V2_OPERATOR_ACKNOWLEDGEMENT
            ),
        )


def test_atomic_transition_commits_exact_lease_only_in_temporary_repo(
    tmp_path: Path,
) -> None:
    root = _sandbox(tmp_path)
    result = execute_final_engineering_invocation_atomic_transition_once(
        root,
        admission=_admission(),
        claimed_at_utc="2026-08-04T01:00:00Z",
    )
    target = root / EXECUTION_LEASE_V2_RELATIVE
    assert target.is_file()
    assert not target.is_symlink()
    assert stat.S_IMODE(target.stat().st_mode) == 0o600
    assert target.read_text(encoding="utf-8") == result.lease.canonical_json()
    assert result.authorization_consumed is True
    assert result.attempt_started is True
    assert result.atomic_action_committed is True
    assert result.runtime_execution_started is False
    assert result.retry_permitted is False
    assert not (root / result.lease.output_root).exists()


def test_exact_existing_commit_forbids_retry(tmp_path: Path) -> None:
    root = _sandbox(tmp_path)
    admission = _admission()
    execute_final_engineering_invocation_atomic_transition_once(
        root,
        admission=admission,
        claimed_at_utc="2026-08-04T01:01:00Z",
    )
    with pytest.raises(AtomicTransitionCommittedError, match="retry forbidden"):
        execute_final_engineering_invocation_atomic_transition_once(
            root,
            admission=admission,
            claimed_at_utc="2026-08-04T01:01:00Z",
        )


def test_invalid_existing_final_object_is_unknown_fail_closed(
    tmp_path: Path,
) -> None:
    root = _sandbox(tmp_path)
    target = root / EXECUTION_LEASE_V2_RELATIVE
    target.write_text("{}\n", encoding="utf-8")
    target.chmod(0o600)
    with pytest.raises(AtomicTransitionUnknownStateError, match="retry forbidden"):
        execute_final_engineering_invocation_atomic_transition_once(
            root,
            admission=_admission(),
            claimed_at_utc="2026-08-04T01:02:00Z",
        )


def test_precommit_failure_leaves_lease_absent(tmp_path: Path) -> None:
    root = _sandbox(tmp_path)
    bad = replace(_admission(), transition_post_merge_verified=False)
    with pytest.raises(AtomicTransitionError, match="post-merge"):
        execute_final_engineering_invocation_atomic_transition_once(
            root,
            admission=bad,
            claimed_at_utc="2026-08-04T01:03:00Z",
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
                    and alias.name != "torch" and not alias.name.startswith("torch.")
                    and "lease_bound_host_invoker_wiring" not in alias.name
                    for alias in node.names
                )
            if isinstance(node, ast.ImportFrom):
                imported_from = node.module or ""
                assert imported_from != "subprocess"
                assert imported_from != "torch"
                assert not imported_from.startswith("torch.")
                assert "lease_bound_host_invoker_wiring" not in imported_from


def test_frozen_transition_package_is_canonical() -> None:
    expected = {"transition.json", "source-SHA256SUMS", "SHA256SUMS"}
    assert {path.name for path in PACKAGE_ROOT.iterdir()} == expected
    registry = {}
    for line in (PACKAGE_ROOT / "SHA256SUMS").read_text(
        encoding="utf-8"
    ).splitlines():
        digest, relative = line.split("  ", 1)
        registry[relative] = digest
    assert set(registry) == {"transition.json", "source-SHA256SUMS"}
    for relative, digest in registry.items():
        assert __import__("hashlib").sha256(
            (PACKAGE_ROOT / relative).read_bytes()
        ).hexdigest() == digest
    raw = (PACKAGE_ROOT / "transition.json").read_text(encoding="utf-8")
    assert raw == load_atomic_transition(
        PACKAGE_ROOT / "transition.json"
    ).canonical_json()
    assert json.loads(raw)["gates"]["atomic_action_permitted"] is False
