#!/usr/bin/env python3
"""Materialize attempt-003 execution freeze from immutable receipts only."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, cast

from torch2pc_thesis.stage3b_qwake_attempt_003_contract import (
    ATTEMPT_003_AUTHORIZATION_ROOT,
    ATTEMPT_003_BACKEND_RELATIVE,
    ATTEMPT_003_CONTRACT_RELATIVE,
    ATTEMPT_003_DURABLE_OUTCOME_RELATIVE,
    ATTEMPT_003_ENTRYPOINT_RELATIVE,
    ATTEMPT_003_FREEZE_ID,
    ATTEMPT_003_FREEZE_ROOT,
    ATTEMPT_003_FREEZE_STATUS,
    ATTEMPT_003_ID,
    ATTEMPT_003_LEASE_V1_RELATIVE,
    ATTEMPT_003_LEASE_V2_RELATIVE,
    ATTEMPT_003_OUTPUT_ROOT,
    ATTEMPT_003_WRAPPER_RELATIVE,
    AUTHORIZED_CELL_COUNT,
    RESERVE_PROBE_COUNT,
    SCIENTIFIC_RUNTIME_AUTHORIZATION_RELATIVE,
    Attempt003ExecutionFreeze,
    canonical_json,
    sha256_object,
    verify_attempt_003_execution_freeze,
)

SOURCE_BINDING = Path(
    "experiments/frozen/"
    "stage3b-qwake-attempt-003-source-binding-execution-freeze-authoring-v1/"
    "contract.json"
)
RUNTIME_REGISTRY = Path(
    "experiments/frozen/"
    "stage3b-qwake-attempt-003-clean-source-closure-implementation-authoring-v1/"
    "runtime-SHA256SUMS"
)
SOURCE_COMMIT = "541b34a57297d2c5a82851bd846b583d4904fba6"
TORCH2PC_COMMIT = "b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4"
BASE_IMAGE = (
    "rocm/pytorch@sha256:"
    "96a2fb24dec9896e2f8238178f0c49d0dcc4c7dcc597be09e4564316bd86d191"
)
RECEIPTS = frozenset(
    {
        "identity.env",
        "image-build.log",
        "image-capture.json",
        "image-inspection.json",
        "static-image-validation.json",
    }
)
PACKAGE_FILES = RECEIPTS | frozenset(
    {"SHA256SUMS", "execution.json", "materialization.json", "source-SHA256SUMS"}
)


class MaterializationError(RuntimeError):
    pass


def _sha(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise MaterializationError(f"regular file absent: {path}")
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise MaterializationError(f"JSON file absent: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise MaterializationError(f"JSON root not object: {path}")
    return cast(dict[str, Any], value)



def _semantic(value: dict[str, Any], field: str) -> str:
    payload = dict(value)
    payload.pop(field, None)
    return "sha256:" + hashlib.sha256(
        canonical_json(payload).encode("utf-8")
    ).hexdigest()


def _registry(entries: dict[str, str]) -> str:
    return "".join(
        f"{entries[name].removeprefix('sha256:')}  {name}\n"
        for name in sorted(entries)
    )


def _closed(root: Path) -> None:
    forbidden = (
        root / ATTEMPT_003_AUTHORIZATION_ROOT,
        root / ATTEMPT_003_LEASE_V1_RELATIVE,
        root / ATTEMPT_003_LEASE_V2_RELATIVE,
        root / ATTEMPT_003_DURABLE_OUTCOME_RELATIVE,
        root / ATTEMPT_003_OUTPUT_ROOT,
    )
    if any(path.exists() for path in forbidden):
        raise MaterializationError("attempt-003 effect boundary open")


def _binding(root: Path) -> dict[str, Any]:
    value = _json(root / SOURCE_BINDING)
    exact = {
        "source_commit": SOURCE_COMMIT,
        "wrapper_commit_required": SOURCE_COMMIT,
        "torch2pc_commit": TORCH2PC_COMMIT,
        "base_image": BASE_IMAGE,
        "future_oci_revision_required": SOURCE_COMMIT,
        "future_oci_base_image_required": BASE_IMAGE,
        "future_new_image_digest_required": True,
        "future_new_image_repo_digest_required": True,
        "future_nonexecuting_image_inspection_required": True,
    }
    for name, expected in exact.items():
        if value.get(name) != expected:
            raise MaterializationError(f"binding field differs: {name}")
    if _semantic(value, "contract_sha256") != value.get("contract_sha256"):
        raise MaterializationError("source-binding contract digest differs")
    if _sha(root / RUNTIME_REGISTRY) != value.get(
        "implementation_runtime_registry_file_sha256"
    ):
        raise MaterializationError("runtime registry identity differs")
    return value


def _receipts(root: Path, binding: dict[str, Any]) -> dict[str, Any]:
    root = root.expanduser().resolve()
    if not root.is_dir() or root.is_symlink():
        raise MaterializationError("receipt root invalid")
    observed = {
        path.name
        for path in root.iterdir()
        if path.is_file() and not path.is_symlink()
    }
    if observed != RECEIPTS or any(path.is_symlink() for path in root.iterdir()):
        raise MaterializationError("receipt file set differs")
    if not (root / "identity.env").read_bytes():
        raise MaterializationError("identity.env empty")
    if not (root / "image-build.log").read_bytes():
        raise MaterializationError("image-build.log empty")
    _json(root / "image-capture.json")
    inspection = _json(root / "image-inspection.json")
    static = _json(root / "static-image-validation.json")

    image_digest = inspection.get("image_digest")
    repo_digest = inspection.get("image_repo_digest")
    if (
        not isinstance(image_digest, str)
        or len(image_digest) != 71
        or not image_digest.startswith("sha256:")
    ):
        raise MaterializationError("image digest invalid")
    if (
        not isinstance(repo_digest, str)
        or repo_digest.count("@sha256:") != 1
        or not repo_digest.endswith(image_digest.removeprefix("sha256:"))
    ):
        raise MaterializationError("image repository digest invalid")

    for name, expected in {
        "oci_revision": SOURCE_COMMIT,
        "source_git_commit_env": SOURCE_COMMIT,
        "oci_base_image": BASE_IMAGE,
    }.items():
        if inspection.get(name) != expected:
            raise MaterializationError(f"inspection field differs: {name}")

    for name, expected in {
        "source_git_commit": SOURCE_COMMIT,
        "future_execution_freeze_id": ATTEMPT_003_FREEZE_ID,
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
    }.items():
        if static.get(name) != expected:
            raise MaterializationError(f"static validation differs: {name}")

    components = binding.get("future_execution_freeze_component_sha256")
    if not isinstance(components, dict) or len(components) != 4:
        raise MaterializationError("component binding differs")
    return inspection


def _freeze(
    root: Path,
    binding: dict[str, Any],
    inspection: dict[str, Any],
) -> Attempt003ExecutionFreeze:
    components = cast(
        dict[str, str],
        binding["future_execution_freeze_component_sha256"],
    )
    component_fields = {
        ATTEMPT_003_CONTRACT_RELATIVE.as_posix(): "contract_sha256",
        ATTEMPT_003_WRAPPER_RELATIVE.as_posix(): "wrapper_sha256",
        ATTEMPT_003_BACKEND_RELATIVE.as_posix(): "backend_sha256",
        ATTEMPT_003_ENTRYPOINT_RELATIVE.as_posix(): "entrypoint_sha256",
    }
    values: dict[str, str] = {}
    for relative, field in component_fields.items():
        observed = _sha(root / relative)
        if observed != components.get(relative):
            raise MaterializationError(f"runtime component differs: {relative}")
        values[field] = observed

    auth_relative = SCIENTIFIC_RUNTIME_AUTHORIZATION_RELATIVE.as_posix()
    if binding.get("scientific_authorization_relative") != auth_relative:
        raise MaterializationError("scientific authorization path differs")
    auth_path = root / SCIENTIFIC_RUNTIME_AUTHORIZATION_RELATIVE
    auth_file_sha = _sha(auth_path)
    if auth_file_sha != binding.get("scientific_authorization_file_sha256"):
        raise MaterializationError("scientific authorization file differs")
    auth = _json(auth_path)
    auth_sha = auth.get("authorization_sha256")
    if auth_sha != binding.get("scientific_authorization_sha256"):
        raise MaterializationError("scientific authorization identity differs")

    payload: dict[str, Any] = {
        "schema_version": 1,
        "freeze_id": ATTEMPT_003_FREEZE_ID,
        "status": ATTEMPT_003_FREEZE_STATUS,
        "attempt_id": ATTEMPT_003_ID,
        "source_commit": SOURCE_COMMIT,
        "wrapper_commit": SOURCE_COMMIT,
        "torch2pc_commit": TORCH2PC_COMMIT,
        "image_digest": inspection["image_digest"],
        "image_repo_digest": inspection["image_repo_digest"],
        **values,
        "scientific_authorization_relative": auth_relative,
        "scientific_authorization_sha256": auth_sha,
        "scientific_authorization_file_sha256": auth_file_sha,
        "output_root": ATTEMPT_003_OUTPUT_ROOT.as_posix(),
        "lease_v1_relative": ATTEMPT_003_LEASE_V1_RELATIVE.as_posix(),
        "lease_v2_relative": ATTEMPT_003_LEASE_V2_RELATIVE.as_posix(),
        "durable_outcome_relative": ATTEMPT_003_DURABLE_OUTCOME_RELATIVE.as_posix(),
        "authorized_cell_count": AUTHORIZED_CELL_COUNT,
        "reserve_probe_count": RESERVE_PROBE_COUNT,
        "execution_count": 1,
        "runtime_execution_started": False,
        "runtime_execution_performed": False,
        "engineering_evidence_present": False,
        "scientific_execution_open": False,
        "test_dataset_access": False,
        "publication_permitted": False,
    }
    payload["freeze_sha256"] = sha256_object(payload)
    freeze = Attempt003ExecutionFreeze(**payload)
    freeze.require()
    return freeze



def _verify_staging(
    staging: Path,
    root: Path,
    freeze: Attempt003ExecutionFreeze,
) -> None:
    package_entries: dict[str, str] = {}
    for raw in (staging / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, separator, relative = raw.partition("  ")
        if not separator or relative in package_entries:
            raise MaterializationError("staged package registry invalid")
        package_entries[relative] = "sha256:" + digest
    if set(package_entries) != PACKAGE_FILES - {"SHA256SUMS"}:
        raise MaterializationError("staged package path set differs")
    for relative, expected in package_entries.items():
        if _sha(staging / relative) != expected:
            raise MaterializationError(f"staged package digest differs: {relative}")

    source_entries: dict[str, str] = {}
    for raw in (staging / "source-SHA256SUMS").read_text(
        encoding="utf-8"
    ).splitlines():
        digest, separator, relative = raw.partition("  ")
        if not separator or relative in source_entries:
            raise MaterializationError("staged source registry invalid")
        source_entries[relative] = "sha256:" + digest
    expected_sources = {
        ATTEMPT_003_CONTRACT_RELATIVE.as_posix(): freeze.contract_sha256,
        ATTEMPT_003_WRAPPER_RELATIVE.as_posix(): freeze.wrapper_sha256,
        ATTEMPT_003_BACKEND_RELATIVE.as_posix(): freeze.backend_sha256,
        ATTEMPT_003_ENTRYPOINT_RELATIVE.as_posix(): freeze.entrypoint_sha256,
        SCIENTIFIC_RUNTIME_AUTHORIZATION_RELATIVE.as_posix(): (
            freeze.scientific_authorization_file_sha256
        ),
    }
    if source_entries != expected_sources:
        raise MaterializationError("staged source registry differs")
    for relative, expected in source_entries.items():
        if _sha(root / relative) != expected:
            raise MaterializationError(f"staged source differs: {relative}")


def materialize(project_root: Path, receipt_root: Path) -> Attempt003ExecutionFreeze:
    root = project_root.expanduser().resolve()
    destination = root / ATTEMPT_003_FREEZE_ROOT
    if destination.exists():
        raise MaterializationError("freeze destination exists")
    _closed(root)
    binding = _binding(root)
    receipts = receipt_root.expanduser().resolve()
    inspection = _receipts(receipts, binding)
    freeze = _freeze(root, binding, inspection)

    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(prefix=f".{destination.name}.staging-", dir=destination.parent)
    )
    try:
        for name in sorted(RECEIPTS):
            shutil.copyfile(receipts / name, staging / name)
        (staging / "execution.json").write_text(
            freeze.canonical_json(), encoding="utf-8"
        )
        sources = {
            ATTEMPT_003_CONTRACT_RELATIVE.as_posix(): freeze.contract_sha256,
            ATTEMPT_003_WRAPPER_RELATIVE.as_posix(): freeze.wrapper_sha256,
            ATTEMPT_003_BACKEND_RELATIVE.as_posix(): freeze.backend_sha256,
            ATTEMPT_003_ENTRYPOINT_RELATIVE.as_posix(): freeze.entrypoint_sha256,
            SCIENTIFIC_RUNTIME_AUTHORIZATION_RELATIVE.as_posix(): (
                freeze.scientific_authorization_file_sha256
            ),
        }
        (staging / "source-SHA256SUMS").write_text(
            _registry(sources), encoding="utf-8"
        )
        manifest = {
            "schema_version": 1,
            "materialization_id": (
                "stage3b-qwake-attempt-003-execution-freeze-materialization-v1"
            ),
            "status": (
                "corrected_image_and_attempt_003_execution_freeze_"
                "materialized_execution_not_started"
            ),
            "source_commit": freeze.source_commit,
            "image_digest": freeze.image_digest,
            "image_repo_digest": freeze.image_repo_digest,
            "freeze_sha256": freeze.freeze_sha256,
            "gates": {
                "immutable_execution_image_present": True,
                "execution_freeze_materialized": True,
                "attempt_003_authorization_present": False,
                "execution_lease_materialized": False,
                "durable_outcome_present": False,
                "runtime_execution_started": False,
                "runtime_execution_performed": False,
                "engineering_evidence_present": False,
                "scientific_execution_open": False,
                "test_dataset_access": False,
                "publication_permitted": False,
            },
        }
        (staging / "materialization.json").write_text(
            canonical_json(manifest), encoding="utf-8"
        )
        package = {
            name: _sha(staging / name)
            for name in sorted(PACKAGE_FILES - {"SHA256SUMS"})
        }
        (staging / "SHA256SUMS").write_text(_registry(package), encoding="utf-8")
        _verify_staging(staging, root, freeze)
        staging.rename(destination)
    except BaseException:
        if staging.exists():
            shutil.rmtree(staging)
        raise

    old = {
        "SOURCE_GIT_COMMIT": os.environ.get("SOURCE_GIT_COMMIT"),
        "EXPERIMENT_IMAGE_DIGEST": os.environ.get("EXPERIMENT_IMAGE_DIGEST"),
        "EXPERIMENT_IMAGE_REPO_DIGEST": os.environ.get("EXPERIMENT_IMAGE_REPO_DIGEST"),
    }
    os.environ["SOURCE_GIT_COMMIT"] = freeze.source_commit
    os.environ["EXPERIMENT_IMAGE_DIGEST"] = freeze.image_digest
    os.environ["EXPERIMENT_IMAGE_REPO_DIGEST"] = freeze.image_repo_digest
    try:
        verified = verify_attempt_003_execution_freeze(root)
    finally:
        for name, value in old.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
    if verified != freeze:
        raise MaterializationError("post-materialization identity differs")
    _closed(root)
    return freeze


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--receipt-root", type=Path, required=True)
    args = parser.parse_args()
    freeze = materialize(args.project_root, args.receipt_root)
    print("ATTEMPT_003_EXECUTION_FREEZE_MATERIALIZED=true")
    print(f"FREEZE_SHA256={freeze.freeze_sha256}")
    print("AUTHORIZATION_ISSUED=false")
    print("AUTHORIZATION_USED=false")
    print("EXECUTION_LEASE_MATERIALIZED=false")
    print("RUNTIME_EXECUTION_STARTED=false")
    print("RUNTIME_EXECUTION_PERFORMED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
