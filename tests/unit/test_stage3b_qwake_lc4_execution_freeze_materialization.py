from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

import pytest

import torch2pc_thesis.stage3b_qwake_lc4_runtime_backend as backend_module
from torch2pc_thesis.stage3b_qwake_lc4_execution_admission import (
    AUTHORIZED_OUTPUT_ROOT,
    EXECUTION_LEASE_RELATIVE,
)
from torch2pc_thesis.stage3b_qwake_lc4_execution_wrapper import (
    FROZEN_ADMISSION_SHA256,
    FROZEN_AUTHORIZATION_SHA256,
    FROZEN_TORCH2PC_COMMIT,
)
from torch2pc_thesis.stage3b_qwake_lc4_runtime_backend import (
    MATERIALIZED_EXECUTION_FREEZE_ID,
    MATERIALIZED_EXECUTION_FREEZE_STATUS,
    ONE_SHOT_ENTRYPOINT_ID,
    RUNTIME_BACKEND_ID,
    verify_materialized_execution_freeze,
)

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = (
    ROOT
    / "experiments/frozen/stage3b-qwake-lc4-e-execution-freeze-v1"
)
EXECUTION = PACKAGE / "execution.json"
MATERIALIZATION = PACKAGE / "materialization.json"
VERIFIER = (
    ROOT
    / "scripts/verify_stage3b_qwake_lc4_execution_freeze_materialization.py"
)
SOURCE_COMMIT = "67a084c0b970ad79ad0692442f660085a73b080a"
IMAGE_DIGEST = (
    "sha256:7da92b8f77f6dc37d42db832c5613ef6149dc488adc5b66465faa33e48ca021d"
)
IMAGE_REPO_DIGEST = (
    "torch2pc-layerwise-thesis@"
    "sha256:7da92b8f77f6dc37d42db832c5613ef6149dc488adc5b66465faa33e48ca021d"
)
EXPECTED_FILES = {
    "SHA256SUMS",
    "execution.json",
    "identity.env",
    "image-build.log",
    "image-capture.json",
    "image-inspection.json",
    "materialization.json",
    "source-SHA256SUMS",
    "static-image-validation.json",
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


def test_materialized_execution_freeze_loads_and_binds_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SOURCE_GIT_COMMIT", SOURCE_COMMIT)
    monkeypatch.setenv("EXPERIMENT_IMAGE_DIGEST", IMAGE_DIGEST)
    monkeypatch.setenv("EXPERIMENT_IMAGE_REPO_DIGEST", IMAGE_REPO_DIGEST)
    monkeypatch.setattr(
        backend_module,
        "_require_git_commit",
        lambda _root, _expected: None,
    )
    freeze = verify_materialized_execution_freeze(ROOT)
    assert freeze.freeze_id == MATERIALIZED_EXECUTION_FREEZE_ID
    assert freeze.status == MATERIALIZED_EXECUTION_FREEZE_STATUS
    assert freeze.source_commit == SOURCE_COMMIT
    assert freeze.wrapper_commit == SOURCE_COMMIT
    assert freeze.torch2pc_commit == FROZEN_TORCH2PC_COMMIT
    assert freeze.image_digest == IMAGE_DIGEST
    assert freeze.image_repo_digest == IMAGE_REPO_DIGEST
    assert freeze.backend_id == RUNTIME_BACKEND_ID
    assert freeze.entrypoint_id == ONE_SHOT_ENTRYPOINT_ID
    assert freeze.admission_sha256 == FROZEN_ADMISSION_SHA256
    assert freeze.authorization_sha256 == FROZEN_AUTHORIZATION_SHA256
    assert freeze.execution_freeze_materialized is True
    assert freeze.runtime_execution_permitted is True
    assert freeze.execution_lease_materialized is False
    assert freeze.runtime_execution_started is False
    assert freeze.runtime_execution_performed is False


def test_materialized_package_and_source_registries_are_exact() -> None:
    observed = {
        path.relative_to(PACKAGE).as_posix()
        for path in PACKAGE.rglob("*")
        if path.is_file()
    }
    assert observed == EXPECTED_FILES
    registry = _registry(PACKAGE / "SHA256SUMS")
    assert set(registry) == EXPECTED_FILES - {"SHA256SUMS"}
    for relative, expected in registry.items():
        assert _sha256(PACKAGE / relative) == expected
    source = _registry(PACKAGE / "source-SHA256SUMS")
    assert set(source) == {
        "identity.env",
        "image-build.log",
        "image-capture.json",
        "image-inspection.json",
        "static-image-validation.json",
    }
    for relative, expected in source.items():
        assert _sha256(PACKAGE / relative) == expected


def test_materialization_manifest_preserves_branch_boundary() -> None:
    manifest = json.loads(MATERIALIZATION.read_text(encoding="utf-8"))
    assert manifest["materialization_id"] == (
        "stage3b-qwake-lc4-e-execution-freeze-materialization-v1"
    )
    assert manifest["source"]["base_commit"] == SOURCE_COMMIT
    assert manifest["image"]["image_digest"] == IMAGE_DIGEST
    assert manifest["image"]["image_repo_digest"] == IMAGE_REPO_DIGEST
    assert manifest["package"]["package_file_count"] == 9
    gates = manifest["gates"]
    assert gates["immutable_execution_image_present"] is True
    assert gates["execution_freeze_materialized"] is True
    assert gates["execution_record_runtime_execution_permitted"] is True
    assert gates["branch_runtime_execution_permitted"] is False
    assert gates["execution_lease_materialized"] is False
    assert gates["authorization_consumed"] is False
    assert gates["runtime_execution_started"] is False
    assert gates["runtime_execution_performed"] is False
    assert gates["engineering_evidence_present"] is False
    assert gates["scientific_execution_open"] is False
    assert gates["test_dataset_access"] is False
    assert gates["publication_permitted"] is False
    assert gates["local_compute_execution_open"] is False


def test_materialization_contains_no_runtime_effect() -> None:
    assert not (ROOT / EXECUTION_LEASE_RELATIVE).exists()
    assert not (ROOT / AUTHORIZED_OUTPUT_ROOT).exists()
    output_root = Path(AUTHORIZED_OUTPUT_ROOT)
    assert not any(
        (ROOT / output_root.parent).glob(
            f".{output_root.name}.staging-*"
        )
    )


def test_materialization_verifier_does_not_invoke_execution() -> None:
    tree = ast.parse(VERIFIER.read_text(encoding="utf-8"))
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    forbidden = {
        "run_one_shot_authorized_runtime",
        "claim_execution_lease",
        "execute_authorized_runtime",
    }
    assert called_names.isdisjoint(forbidden)
    execution = json.loads(EXECUTION.read_text(encoding="utf-8"))
    assert execution["runtime_execution_permitted"] is True
    assert execution["execution_lease_materialized"] is False
    assert execution["runtime_execution_started"] is False
    assert execution["runtime_execution_performed"] is False
