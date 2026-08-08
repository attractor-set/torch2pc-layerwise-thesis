from __future__ import annotations

import ast
import importlib.util
import os
import pwd
import shutil
from pathlib import Path
from types import ModuleType

import pytest

from torch2pc_thesis.stage3b_qwake_attempt_003_contract import (
    ATTEMPT_003_AUTHORIZATION_ROOT,
    ATTEMPT_003_INVOCATION_ACKNOWLEDGEMENT,
)

ROOT = Path(__file__).resolve().parents[2]
MATERIALIZER = (
    ROOT / "scripts/materialize_stage3b_qwake_attempt_003_authorization.py"
)
VERIFIER = (
    ROOT
    / "scripts/verify_stage3b_qwake_attempt_003_authorization_materialization.py"
)
PROJECT_PATHS = (
    "docs/decisions/"
    "ADR-115-stage3b-qwake-attempt-003-authorization-materialization-authoring.md",
    "docs/decisions/"
    "ADR-115-stage3b-qwake-attempt-003-authorization-materialization-authoring_EN.md",
    "docs/language-map.csv",
    "experiments/frozen/"
    "stage3b-qwake-attempt-003-authorization-materialization-authoring-v1/"
    "SHA256SUMS",
    "experiments/frozen/"
    "stage3b-qwake-attempt-003-authorization-materialization-authoring-v1/"
    "authoring.json",
    "experiments/frozen/"
    "stage3b-qwake-attempt-003-authorization-materialization-authoring-v1/"
    "contract.json",
    "experiments/frozen/"
    "stage3b-qwake-attempt-003-authorization-materialization-authoring-v1/"
    "source-SHA256SUMS",
    "experiments/frozen/"
    "stage3b-qwake-attempt-003-execution-freeze-v1/SHA256SUMS",
    "experiments/frozen/"
    "stage3b-qwake-attempt-003-execution-freeze-v1/execution.json",
    "experiments/frozen/"
    "stage3b-qwake-attempt-003-execution-freeze-v1/identity.env",
    "experiments/frozen/"
    "stage3b-qwake-attempt-003-execution-freeze-v1/image-build.log",
    "experiments/frozen/"
    "stage3b-qwake-attempt-003-execution-freeze-v1/image-capture.json",
    "experiments/frozen/"
    "stage3b-qwake-attempt-003-execution-freeze-v1/image-inspection.json",
    "experiments/frozen/"
    "stage3b-qwake-attempt-003-execution-freeze-v1/materialization.json",
    "experiments/frozen/"
    "stage3b-qwake-attempt-003-execution-freeze-v1/source-SHA256SUMS",
    "experiments/frozen/"
    "stage3b-qwake-attempt-003-execution-freeze-v1/static-image-validation.json",
    "experiments/frozen/"
    "stage3b-qwake-lc4-f-runtime-freeze-v1/authorization.json",
    "scripts/materialize_stage3b_qwake_attempt_003_authorization.py",
    "scripts/run_stage3b_qwake_attempt_003_authorized_runtime.py",
    "scripts/verify_stage3b_qwake_attempt_003_authorization_materialization.py",
    "src/torch2pc_thesis/stage3b_qwake_attempt_003_contract.py",
    "src/torch2pc_thesis/stage3b_qwake_attempt_003_execution_wrapper.py",
    "src/torch2pc_thesis/stage3b_qwake_attempt_003_runtime_backend.py",
    "tests/unit/test_stage3b_qwake_attempt_003_authorization_materialization.py",
)


def _operator_identity() -> str:
    return pwd.getpwuid(os.getuid()).pw_name


def _load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _project(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    for relative in PROJECT_PATHS:
        source = ROOT / relative
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    return root


def test_authoring_verifies_in_isolated_tree_without_authorization(
    tmp_path: Path,
) -> None:
    verifier = _load("attempt003_authorization_verifier_authoring", VERIFIER)
    project = _project(tmp_path)

    record = verifier.verify_authoring(project)

    assert record["authorization_issued"] is False
    assert not (project / ATTEMPT_003_AUTHORIZATION_ROOT).exists()


def test_materializer_contains_no_runtime_or_container_effect_calls() -> None:
    tree = ast.parse(MATERIALIZER.read_text(encoding="utf-8"))
    imported = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported |= {
        (node.module or "").split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    assert imported.isdisjoint({"subprocess", "docker"})

    forbidden_calls = {
        "materialize_attempt_003_lease",
        "run_claimed_attempt_003",
        "run_attempt_003_authorized_runtime",
        "execute_authorized_runtime",
    }
    called = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert called.isdisjoint(forbidden_calls)


def test_materialize_and_verify_in_isolated_tree(tmp_path: Path) -> None:
    materializer = _load("attempt003_authorization_materializer_ok", MATERIALIZER)
    verifier = _load("attempt003_authorization_verifier_ok", VERIFIER)
    project = _project(tmp_path)
    operator = _operator_identity()

    authorization = materializer.materialize(
        project,
        operator_identity=operator,
        action_phrase=ATTEMPT_003_INVOCATION_ACKNOWLEDGEMENT,
    )
    verified = verifier.verify_materialized(project)

    assert authorization.authorization_effective is True
    assert authorization.authorization_consumed is False
    assert authorization.attempt_started is False
    assert authorization.retry_permitted is False
    assert verified["authorization_sha256"] == authorization.authorization_sha256


def test_materializer_is_no_replace(tmp_path: Path) -> None:
    materializer = _load(
        "attempt003_authorization_materializer_repeat",
        MATERIALIZER,
    )
    project = _project(tmp_path)
    operator = _operator_identity()

    materializer.materialize(
        project,
        operator_identity=operator,
        action_phrase=ATTEMPT_003_INVOCATION_ACKNOWLEDGEMENT,
    )

    with pytest.raises(materializer.AuthorizationMaterializationError):
        materializer.materialize(
            project,
            operator_identity=operator,
            action_phrase=ATTEMPT_003_INVOCATION_ACKNOWLEDGEMENT,
        )


def test_wrong_action_phrase_fails_before_authorization(tmp_path: Path) -> None:
    materializer = _load(
        "attempt003_authorization_materializer_bad_phrase",
        MATERIALIZER,
    )
    project = _project(tmp_path)

    with pytest.raises(materializer.AuthorizationMaterializationError):
        materializer.materialize(
            project,
            operator_identity=_operator_identity(),
            action_phrase="NOT_AUTHORIZED",
        )

    assert not (project / ATTEMPT_003_AUTHORIZATION_ROOT).exists()


def test_wrong_operator_identity_fails_before_authorization(tmp_path: Path) -> None:
    materializer = _load(
        "attempt003_authorization_materializer_bad_operator",
        MATERIALIZER,
    )
    project = _project(tmp_path)

    with pytest.raises(materializer.AuthorizationMaterializationError):
        materializer.materialize(
            project,
            operator_identity="definitely-not-the-current-posix-account",
            action_phrase=ATTEMPT_003_INVOCATION_ACKNOWLEDGEMENT,
        )

    assert not (project / ATTEMPT_003_AUTHORIZATION_ROOT).exists()


def test_changed_frozen_source_fails_before_authorization(tmp_path: Path) -> None:
    materializer = _load(
        "attempt003_authorization_materializer_bad_source",
        MATERIALIZER,
    )
    project = _project(tmp_path)
    source = (
        project
        / "scripts/run_stage3b_qwake_attempt_003_authorized_runtime.py"
    )
    source.write_text(
        source.read_text(encoding="utf-8") + "\n",
        encoding="utf-8",
    )

    with pytest.raises(materializer.AuthorizationMaterializationError):
        materializer.materialize(
            project,
            operator_identity=_operator_identity(),
            action_phrase=ATTEMPT_003_INVOCATION_ACKNOWLEDGEMENT,
        )

    assert not (project / ATTEMPT_003_AUTHORIZATION_ROOT).exists()
