from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path
from types import ModuleType

import pytest

from torch2pc_thesis.stage3b_qwake_lc4_attempt_002_contract import (
    ATTEMPT_002_LEASE_V1_RELATIVE,
    Attempt002ContractError,
    canonical_json,
    verify_attempt_002_execution_freeze,
)

PACKAGE = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-attempt-002-execution-freeze-v1"
)
VERIFIER = Path(
    "scripts/verify_stage3b_qwake_lc4_attempt_002_execution_freeze.py"
)
SOURCE_PATHS = (
    Path(".dockerignore"),
    Path("Dockerfile.rocm"),
    Path(
        "experiments/frozen/"
        "stage3b-qwake-lc4-f-runtime-freeze-v1/authorization.json"
    ),
    Path("pyproject.toml"),
    Path("requirements/rocm.txt"),
    Path("scripts/container_entrypoint.sh"),
    Path("scripts/run_stage3b_qwake_lc4_attempt_002_authorized_runtime.py"),
    VERIFIER,
    Path(
        "src/torch2pc_thesis/"
        "stage3b_qwake_lc4_attempt_002_contract.py"
    ),
    Path(
        "src/torch2pc_thesis/"
        "stage3b_qwake_lc4_attempt_002_execution_wrapper.py"
    ),
    Path(
        "src/torch2pc_thesis/"
        "stage3b_qwake_lc4_attempt_002_runtime_backend.py"
    ),
    Path(
        "tests/unit/"
        "test_stage3b_qwake_lc4_attempt_002_execution_freeze.py"
    ),
)


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_verifier(root: Path) -> ModuleType:
    path = root / VERIFIER
    spec = importlib.util.spec_from_file_location(
        "attempt_002_execution_freeze_verifier",
        path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("verifier import specification differs")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _copy_fixture(tmp_path: Path) -> Path:
    source = _repository_root()
    destination = tmp_path / "repository"
    shutil.copytree(source / PACKAGE, destination / PACKAGE)
    for relative in SOURCE_PATHS:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / relative, target)
    return destination


def test_committed_attempt_002_execution_freeze_verifies() -> None:
    root = _repository_root()
    verifier = _load_verifier(root)
    verifier.verify(root)


def test_contract_loader_accepts_exact_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _repository_root()
    execution = json.loads((root / PACKAGE / "execution.json").read_text())
    monkeypatch.setenv("SOURCE_GIT_COMMIT", execution["source_commit"])
    monkeypatch.setenv(
        "EXPERIMENT_IMAGE_DIGEST",
        execution["image_digest"],
    )
    monkeypatch.setenv(
        "EXPERIMENT_IMAGE_REPO_DIGEST",
        execution["image_repo_digest"],
    )
    freeze = verify_attempt_002_execution_freeze(root)
    assert freeze.freeze_sha256 == execution["freeze_sha256"]


def test_contract_loader_rejects_wrong_image_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _repository_root()
    execution = json.loads((root / PACKAGE / "execution.json").read_text())
    monkeypatch.setenv("SOURCE_GIT_COMMIT", execution["source_commit"])
    monkeypatch.setenv(
        "EXPERIMENT_IMAGE_DIGEST",
        "sha256:" + "0" * 64,
    )
    monkeypatch.setenv(
        "EXPERIMENT_IMAGE_REPO_DIGEST",
        execution["image_repo_digest"],
    )
    with pytest.raises(Attempt002ContractError):
        verify_attempt_002_execution_freeze(root)


def test_verifier_rejects_mutated_image_identity(tmp_path: Path) -> None:
    root = _copy_fixture(tmp_path)
    path = root / PACKAGE / "image-identity.json"
    value = json.loads(path.read_text())
    value["image_size_bytes"] += 1
    path.write_text(canonical_json(value), encoding="utf-8")
    verifier = _load_verifier(root)
    with pytest.raises(
        verifier.Attempt002ExecutionFreezeVerificationError,
    ):
        verifier.verify(root)


def test_verifier_rejects_mutated_runtime_source(tmp_path: Path) -> None:
    root = _copy_fixture(tmp_path)
    path = (
        root
        / "src/torch2pc_thesis/"
        "stage3b_qwake_lc4_attempt_002_runtime_backend.py"
    )
    path.write_text(path.read_text() + "\n", encoding="utf-8")
    verifier = _load_verifier(root)
    with pytest.raises(
        verifier.Attempt002ExecutionFreezeVerificationError,
    ):
        verifier.verify(root)


def test_verifier_rejects_existing_attempt_002_lease(
    tmp_path: Path,
) -> None:
    root = _copy_fixture(tmp_path)
    lease = root / ATTEMPT_002_LEASE_V1_RELATIVE
    lease.parent.mkdir(parents=True, exist_ok=True)
    lease.write_text("{}\n", encoding="utf-8")
    verifier = _load_verifier(root)
    with pytest.raises(
        verifier.Attempt002ExecutionFreezeVerificationError,
    ):
        verifier.verify(root)
