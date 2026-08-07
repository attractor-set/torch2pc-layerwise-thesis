from __future__ import annotations

import ast
import importlib.util
import json
import shutil
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]
MATERIALIZER = (
    ROOT / "scripts/materialize_stage3b_qwake_attempt_003_execution_freeze.py"
)
VERIFIER = (
    ROOT
    / "scripts/verify_stage3b_qwake_attempt_003_execution_freeze_materialization.py"
)
FREEZE_RELATIVE = Path(
    "experiments/frozen/stage3b-qwake-attempt-003-execution-freeze-v1"
)
SOURCE_COMMIT = "541b34a57297d2c5a82851bd846b583d4904fba6"
BASE_IMAGE = (
    "rocm/pytorch@sha256:"
    "96a2fb24dec9896e2f8238178f0c49d0dcc4c7dcc597be09e4564316bd86d191"
)
IMAGE_DIGEST = "sha256:" + "7" * 64
IMAGE_REPO_DIGEST = "torch2pc-layerwise-thesis@" + IMAGE_DIGEST


def _load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _copy(root: Path, relative: str) -> None:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / relative, target)


def _project(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    for relative in (
        "src/torch2pc_thesis/stage3b_qwake_attempt_003_contract.py",
        "src/torch2pc_thesis/stage3b_qwake_attempt_003_execution_wrapper.py",
        "src/torch2pc_thesis/stage3b_qwake_attempt_003_runtime_backend.py",
        "scripts/run_stage3b_qwake_attempt_003_authorized_runtime.py",
        "experiments/frozen/stage3b-qwake-lc4-f-runtime-freeze-v1/authorization.json",
        "experiments/frozen/"
        "stage3b-qwake-attempt-003-source-binding-execution-freeze-authoring-v1/"
        "contract.json",
        "experiments/frozen/"
        "stage3b-qwake-attempt-003-clean-source-closure-implementation-"
        "authoring-v1/runtime-SHA256SUMS",
    ):
        _copy(root, relative)
    return root


def _receipts(tmp_path: Path) -> Path:
    root = tmp_path / "receipts"
    root.mkdir()
    (root / "identity.env").write_text("receipt=true\n", encoding="utf-8")
    (root / "image-build.log").write_text("synthetic receipt\n", encoding="utf-8")
    (root / "image-capture.json").write_text(
        json.dumps({"schema_version": 1}, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    inspection = {
        "schema_version": 1,
        "image_digest": IMAGE_DIGEST,
        "image_repo_digest": IMAGE_REPO_DIGEST,
        "oci_revision": SOURCE_COMMIT,
        "source_git_commit_env": SOURCE_COMMIT,
        "oci_base_image": BASE_IMAGE,
    }
    (root / "image-inspection.json").write_text(
        json.dumps(inspection, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    static = {
        "schema_version": 1,
        "source_git_commit": SOURCE_COMMIT,
        "future_execution_freeze_id": (
            "stage3b-qwake-attempt-003-execution-freeze-v1"
        ),
        "execution_freeze_present": False,
        "execution_lease_present": False,
        "runtime_output_present": False,
        "runtime_execution_started": False,
        "runtime_execution_performed": False,
        "engineering_evidence_present": False,
        "scientific_execution_open": False,
        "test_dataset_access": False,
        "publication_permitted": False,
        "local_compute_execution_open": False,
    }
    (root / "static-image-validation.json").write_text(
        json.dumps(static, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return root


def test_authoring_verifies_and_freeze_is_absent() -> None:
    verifier = _load("attempt003_materialization_verifier_authoring", VERIFIER)
    verifier.verify_authoring(ROOT)
    assert not (ROOT / FREEZE_RELATIVE).exists()


def test_materializer_contains_no_execution_or_container_effect_calls() -> None:
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
    called = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert called.isdisjoint(
        {
            "materialize_attempt_003_lease",
            "run_claimed_attempt_003",
            "run_attempt_003_authorized_runtime",
            "execute_authorized_runtime",
        }
    )


def test_materialize_and_verify_in_isolated_tree(tmp_path: Path) -> None:
    materializer = _load("attempt003_materializer_ok", MATERIALIZER)
    verifier = _load("attempt003_materialization_verifier_ok", VERIFIER)
    project = _project(tmp_path)
    receipts = _receipts(tmp_path)

    freeze = materializer.materialize(project, receipts)
    manifest = verifier.verify_materialized(project)

    assert freeze.source_commit == SOURCE_COMMIT
    assert freeze.wrapper_commit == SOURCE_COMMIT
    assert freeze.image_digest == IMAGE_DIGEST
    assert freeze.image_repo_digest == IMAGE_REPO_DIGEST
    assert freeze.runtime_execution_started is False
    assert freeze.runtime_execution_performed is False
    assert manifest["gates"]["attempt_003_authorization_present"] is False


def test_materializer_is_no_replace(tmp_path: Path) -> None:
    materializer = _load("attempt003_materializer_repeat", MATERIALIZER)
    project = _project(tmp_path)
    receipts = _receipts(tmp_path)
    materializer.materialize(project, receipts)

    with pytest.raises(materializer.MaterializationError):
        materializer.materialize(project, receipts)


def test_wrong_oci_revision_fails_before_materialization(tmp_path: Path) -> None:
    materializer = _load("attempt003_materializer_bad_revision", MATERIALIZER)
    project = _project(tmp_path)
    receipts = _receipts(tmp_path)
    path = receipts / "image-inspection.json"
    inspection = json.loads(path.read_text(encoding="utf-8"))
    inspection["oci_revision"] = "0" * 40
    path.write_text(
        json.dumps(inspection, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(materializer.MaterializationError):
        materializer.materialize(project, receipts)
    assert not (project / FREEZE_RELATIVE).exists()


def test_mismatched_repository_digest_fails_closed(tmp_path: Path) -> None:
    materializer = _load("attempt003_materializer_bad_repo", MATERIALIZER)
    project = _project(tmp_path)
    receipts = _receipts(tmp_path)
    path = receipts / "image-inspection.json"
    inspection = json.loads(path.read_text(encoding="utf-8"))
    inspection["image_repo_digest"] = (
        "torch2pc-layerwise-thesis@sha256:" + "8" * 64
    )
    path.write_text(
        json.dumps(inspection, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(materializer.MaterializationError):
        materializer.materialize(project, receipts)
    assert not (project / FREEZE_RELATIVE).exists()
