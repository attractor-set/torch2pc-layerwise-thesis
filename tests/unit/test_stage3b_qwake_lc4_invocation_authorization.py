from __future__ import annotations

import ast
import hashlib
from dataclasses import replace
from pathlib import Path

import pytest

from torch2pc_thesis.stage3b_qwake_lc4_invocation_authorization import (
    AUTHORIZATION_ROOT_RELATIVE,
    EXECUTION_LEASE_RELATIVE,
    INVOCATION_AUTHORIZATION_ID,
    INVOCATION_AUTHORIZATION_STATUS,
    QWakeLC4InvocationAuthorizationError,
    verify_invocation_authorization,
)

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / AUTHORIZATION_ROOT_RELATIVE
VERIFIER = ROOT / "scripts/verify_stage3b_qwake_lc4_invocation_authorization.py"
OUTPUT_ROOT = (
    ROOT
    / "results/stage-3/qwake-lc4-runtime-validation-v1-attempt-001"
)
EXPECTED_FILES = {
    "SHA256SUMS",
    "authorization.json",
    "identity.env",
    "source-SHA256SUMS",
}


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _registry(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        digest, separator, relative = raw.partition("  ")
        assert separator
        assert relative not in result
        result[relative] = "sha256:" + digest
    return result


def test_invocation_authorization_is_exact_and_effect_free() -> None:
    authorization = verify_invocation_authorization(ROOT)
    assert authorization.authorization_id == INVOCATION_AUTHORIZATION_ID
    assert authorization.status == INVOCATION_AUTHORIZATION_STATUS
    assert authorization.contract.invocation_count == 1
    assert authorization.contract.future_lease_claim_permitted is True
    assert authorization.contract.future_one_shot_invocation_permitted is True
    assert authorization.contract.future_runtime_execution_permitted is True
    assert authorization.gates.one_shot_invocation_authorized is True
    assert authorization.gates.branch_runtime_execution_permitted is False
    assert authorization.gates.execution_lease_materialized is False
    assert authorization.gates.authorization_consumed is False
    assert authorization.gates.runtime_execution_started is False
    assert authorization.gates.runtime_execution_performed is False


def test_authorization_package_and_registries_are_exact() -> None:
    observed = {
        path.relative_to(PACKAGE).as_posix()
        for path in PACKAGE.rglob("*")
        if path.is_file()
    }
    assert observed == EXPECTED_FILES
    package_registry = _registry(PACKAGE / "SHA256SUMS")
    assert set(package_registry) == EXPECTED_FILES - {"SHA256SUMS"}
    for relative, expected in package_registry.items():
        assert _sha256(PACKAGE / relative) == expected

    source_registry = _registry(PACKAGE / "source-SHA256SUMS")
    assert len(source_registry) == 14
    for relative, expected in source_registry.items():
        assert _sha256(ROOT / relative) == expected


def test_authorization_record_is_canonical_and_self_hashed() -> None:
    authorization = verify_invocation_authorization(ROOT)
    record = PACKAGE / "authorization.json"
    assert record.read_text(encoding="utf-8") == authorization.canonical_json()
    assert authorization.authorization_sha256.startswith("sha256:")
    assert len(authorization.authorization_sha256) == 71


def test_authorization_rejects_opened_effects_and_multiple_invocations() -> None:
    authorization = verify_invocation_authorization(ROOT)

    opened = replace(
        authorization,
        gates=replace(
            authorization.gates,
            runtime_execution_started=True,
        ),
    )
    with pytest.raises(
        QWakeLC4InvocationAuthorizationError,
        match="authorization effect is open",
    ):
        opened.require()

    multiple = replace(
        authorization,
        contract=replace(
            authorization.contract,
            invocation_count=2,
        ),
    )
    with pytest.raises(
        QWakeLC4InvocationAuthorizationError,
        match="invocation contract differs",
    ):
        multiple.require()


def test_authorization_contains_no_runtime_effect() -> None:
    assert not (ROOT / EXECUTION_LEASE_RELATIVE).exists()
    assert not OUTPUT_ROOT.exists()
    assert not any(
        OUTPUT_ROOT.parent.glob(f".{OUTPUT_ROOT.name}.staging-*")
    )


def test_verifier_cannot_claim_or_execute() -> None:
    tree = ast.parse(VERIFIER.read_text(encoding="utf-8"))
    names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    forbidden = {
        "run_one_shot_authorized_runtime",
        "claim_execution_lease",
        "execute_authorized_runtime",
        "materialize_execution_lease",
    }
    assert names.isdisjoint(forbidden)
