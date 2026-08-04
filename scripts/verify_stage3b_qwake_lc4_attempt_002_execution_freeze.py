#!/usr/bin/env python3
"""Verify the corrected attempt-002 image identity and execution freeze."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Final, cast

from torch2pc_thesis.stage3b_qwake_lc4_attempt_002_contract import (
    ATTEMPT_002_AUTHORIZATION_ROOT,
    ATTEMPT_002_DURABLE_OUTCOME_RELATIVE,
    ATTEMPT_002_FREEZE_ID,
    ATTEMPT_002_FREEZE_STATUS,
    ATTEMPT_002_ID,
    ATTEMPT_002_LEASE_V1_RELATIVE,
    ATTEMPT_002_LEASE_V2_RELATIVE,
    ATTEMPT_002_OUTPUT_ROOT,
    Attempt002ExecutionFreeze,
    canonical_json,
    sha256_object,
)

PACKAGE_ROOT: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-attempt-002-execution-freeze-v1"
)
EXECUTION_JSON: Final = PACKAGE_ROOT / "execution.json"
IMAGE_IDENTITY_JSON: Final = PACKAGE_ROOT / "image-identity.json"
CAPTURE_REFERENCE_JSON: Final = PACKAGE_ROOT / "capture-reference.json"
MATERIALIZATION_JSON: Final = PACKAGE_ROOT / "materialization.json"
IDENTITY_ENV: Final = PACKAGE_ROOT / "identity.env"
PACKAGE_REGISTRY: Final = PACKAGE_ROOT / "SHA256SUMS"
SOURCE_REGISTRY: Final = PACKAGE_ROOT / "source-SHA256SUMS"

SOURCE_COMMIT: Final = "02afcc3e79b2d456cc3f1c075d4d792a0be608f7"
TORCH2PC_COMMIT: Final = "b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4"
BASE_IMAGE: Final = (
    "rocm/pytorch@"
    "sha256:96a2fb24dec9896e2f8238178f0c49d0dcc4c7dcc597be09e4564316bd86d191"
)
IMAGE_TAG: Final = (
    "torch2pc-layerwise-thesis:"
    "0.1.0-qw-lc4-e-attempt-002-02afcc3e79b2"
)
IMAGE_DIGEST: Final = (
    "sha256:f78fdbc699f3d00347d1dfdb78c03dd3df3957371f64eca9488de7cc06ce2b1d"
)
IMAGE_REPO_DIGEST: Final = "torch2pc-layerwise-thesis@" + IMAGE_DIGEST
IMAGE_SIZE_BYTES: Final = 10906632054
CAPTURE_ID: Final = (
    "stage3b-qwake-lc4-e-attempt-002-corrected-image-capture-v1"
)
CAPTURE_SHA256: Final = (
    "sha256:2aa105d8c13ef2408e674c08d7210c318a4baebf090b351ceb80ea1cf3de3902"
)
CAPTURE_DIRECTORY_NAME: Final = (
    "qwake-lc4-attempt-002-corrected-image-02afcc3e79b2-v1"
)
SCIENTIFIC_AUTHORIZATION_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-f-runtime-freeze-v1/authorization.json"
)
SCIENTIFIC_AUTHORIZATION_SHA256: Final = (
    "sha256:d11b662a5c5eeada5333e69c6fddf2e50726c01b4d8c78a556a68167dbdd301e"
)
SCIENTIFIC_AUTHORIZATION_FILE_SHA256: Final = (
    "sha256:a380cffcfa73cb2dcf984a3cc7de013cb50d79f075677ad5e762417486f06ebd"
)

CONTRACT_SHA256: Final = (
    "sha256:6b114ee4ba973f58116c7823f524b4fa07fca1961ac563e6ee5af7a1d78dbfd7"
)
WRAPPER_SHA256: Final = (
    "sha256:cb283a771fef7ca30adec53d277311735194b5418a9da8dd19b3d0ae219efbe1"
)
BACKEND_SHA256: Final = (
    "sha256:f715ff687471b7b67308df723d93cd4548a0ca9a81dc0845962871a319e2f14c"
)
ENTRYPOINT_SHA256: Final = (
    "sha256:70563fc847ddd5606b15a54b15a5b013ec4d6905667d78ce86516cd475efd5ac"
)
FREEZE_SHA256: Final = (
    "sha256:09ca6e2b70fe1c7352c35d694952b4ea199e85dd816588f29454a4157b711f5c"
)
IMAGE_IDENTITY_SHA256: Final = (
    "sha256:11f15e3e92680632221bd879ba8aff680f171fb4af2d212afb2aca4763addb3a"
)
CAPTURE_REFERENCE_SHA256: Final = (
    "sha256:89f6e9c94575fca5d5152d85cabcebbe154ac590205bb3516e0bc07b5607a7a5"
)
MATERIALIZATION_SHA256: Final = (
    "sha256:87077e8108e5754438f454ebd625b6843fcb3266ba1836cd22237fb2ea7d9fd3"
)

EXPECTED_PACKAGE_FILES: Final = (
    "SHA256SUMS",
    "capture-reference.json",
    "execution.json",
    "identity.env",
    "image-identity.json",
    "materialization.json",
    "source-SHA256SUMS",
)
EXPECTED_PACKAGE_REGISTRY_PATHS: Final = (
    "capture-reference.json",
    "execution.json",
    "identity.env",
    "image-identity.json",
    "materialization.json",
    "source-SHA256SUMS",
)
EXPECTED_SOURCE_PATHS: Final = (
    ".dockerignore",
    "Dockerfile.rocm",
    "experiments/frozen/"
    "stage3b-qwake-lc4-f-runtime-freeze-v1/authorization.json",
    "pyproject.toml",
    "requirements/rocm.txt",
    "scripts/container_entrypoint.sh",
    "scripts/run_stage3b_qwake_lc4_attempt_002_authorized_runtime.py",
    "scripts/verify_stage3b_qwake_lc4_attempt_002_execution_freeze.py",
    "src/torch2pc_thesis/stage3b_qwake_lc4_attempt_002_contract.py",
    "src/torch2pc_thesis/"
    "stage3b_qwake_lc4_attempt_002_execution_wrapper.py",
    "src/torch2pc_thesis/stage3b_qwake_lc4_attempt_002_runtime_backend.py",
    "tests/unit/test_stage3b_qwake_lc4_attempt_002_execution_freeze.py",
)
OLD_IMAGE_DIGEST: Final = (
    "sha256:7da92b8f77f6dc37d42db832c5613ef6149dc488adc5b66465faa33e48ca021d"
)
OLD_ATTEMPT_PATH: Final = (
    "results/stage-3/qwake-lc4-runtime-validation-v1-attempt-001"
)


class Attempt002ExecutionFreezeVerificationError(RuntimeError):
    """Raised when the corrected execution freeze fails closed."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path("."))
    return parser.parse_args()


def verify(project_root: Path) -> None:
    """Verify every committed freeze identity without runtime effects."""

    root = project_root.expanduser().resolve()
    package = root / PACKAGE_ROOT
    _verify_package_shape(package)
    _verify_registry(package / "SHA256SUMS", package, EXPECTED_PACKAGE_REGISTRY_PATHS)
    _verify_registry(root / SOURCE_REGISTRY, root, EXPECTED_SOURCE_PATHS)

    execution = _read_json(root / EXECUTION_JSON)
    freeze = Attempt002ExecutionFreeze(**cast(dict[str, Any], execution))
    freeze.require()
    _verify_freeze(freeze)

    image_identity = _read_json(root / IMAGE_IDENTITY_JSON)
    _verify_image_identity(image_identity, freeze)

    capture_reference = _read_json(root / CAPTURE_REFERENCE_JSON)
    _verify_capture_reference(capture_reference, freeze)

    materialization = _read_json(root / MATERIALIZATION_JSON)
    _verify_materialization(
        materialization,
        freeze,
        image_identity,
        capture_reference,
    )

    identity = _read_identity_env(root / IDENTITY_ENV)
    _verify_identity_env(
        identity,
        freeze,
        image_identity,
        capture_reference,
        materialization,
    )

    scientific_authorization = _read_json(
        root / SCIENTIFIC_AUTHORIZATION_RELATIVE
    )
    if (
        scientific_authorization.get("authorization_sha256")
        != SCIENTIFIC_AUTHORIZATION_SHA256
    ):
        raise Attempt002ExecutionFreezeVerificationError(
            "scientific authorization semantic identity differs"
        )
    if (
        _sha256_file(root / SCIENTIFIC_AUTHORIZATION_RELATIVE)
        != SCIENTIFIC_AUTHORIZATION_FILE_SHA256
    ):
        raise Attempt002ExecutionFreezeVerificationError(
            "scientific authorization file identity differs"
        )

    package_text = "\n".join(
        (package / name).read_text(encoding="utf-8")
        for name in EXPECTED_PACKAGE_FILES
    )
    if OLD_IMAGE_DIGEST in package_text or OLD_ATTEMPT_PATH in package_text:
        raise Attempt002ExecutionFreezeVerificationError(
            "historical image or attempt path leaked into corrected freeze"
        )
    if str(root) in package_text or "/home/" in package_text:
        raise Attempt002ExecutionFreezeVerificationError(
            "host absolute path leaked into corrected freeze"
        )

    _verify_effect_boundary(root)


def _verify_package_shape(package: Path) -> None:
    if not package.is_dir() or package.is_symlink():
        raise Attempt002ExecutionFreezeVerificationError(
            "execution-freeze package directory differs"
        )
    observed = tuple(
        sorted(
            entry.name
            for entry in package.iterdir()
            if entry.is_file() and not entry.is_symlink()
        )
    )
    if observed != EXPECTED_PACKAGE_FILES:
        raise Attempt002ExecutionFreezeVerificationError(
            "execution-freeze package file set differs"
        )
    if any(entry.is_symlink() for entry in package.iterdir()):
        raise Attempt002ExecutionFreezeVerificationError(
            "execution-freeze package contains a symlink"
        )


def _verify_freeze(freeze: Attempt002ExecutionFreeze) -> None:
    exact: Mapping[str, object] = {
        "freeze_id": ATTEMPT_002_FREEZE_ID,
        "status": ATTEMPT_002_FREEZE_STATUS,
        "attempt_id": ATTEMPT_002_ID,
        "source_commit": SOURCE_COMMIT,
        "wrapper_commit": SOURCE_COMMIT,
        "torch2pc_commit": TORCH2PC_COMMIT,
        "image_digest": IMAGE_DIGEST,
        "image_repo_digest": IMAGE_REPO_DIGEST,
        "contract_sha256": CONTRACT_SHA256,
        "wrapper_sha256": WRAPPER_SHA256,
        "backend_sha256": BACKEND_SHA256,
        "entrypoint_sha256": ENTRYPOINT_SHA256,
        "scientific_authorization_sha256": (
            SCIENTIFIC_AUTHORIZATION_SHA256
        ),
        "scientific_authorization_file_sha256": (
            SCIENTIFIC_AUTHORIZATION_FILE_SHA256
        ),
        "freeze_sha256": FREEZE_SHA256,
    }
    for field_name, expected in exact.items():
        if getattr(freeze, field_name) != expected:
            raise Attempt002ExecutionFreezeVerificationError(
                f"attempt-002 freeze {field_name} differs"
            )


def _verify_image_identity(
    value: dict[str, object],
    freeze: Attempt002ExecutionFreeze,
) -> None:
    digest = value.pop("identity_sha256", None)
    if digest != sha256_object(value) or digest != IMAGE_IDENTITY_SHA256:
        raise Attempt002ExecutionFreezeVerificationError(
            "host image identity digest differs"
        )
    exact: Mapping[str, object] = {
        "schema_version": 1,
        "record_id": (
            "stage3b-qwake-lc4-e-attempt-002-host-image-identity-v1"
        ),
        "status": (
            "corrected_image_built_inspected_twice_container_not_created"
        ),
        "capture_id": CAPTURE_ID,
        "capture_sha256": CAPTURE_SHA256,
        "capture_directory_name": CAPTURE_DIRECTORY_NAME,
        "source_commit": SOURCE_COMMIT,
        "wrapper_commit": SOURCE_COMMIT,
        "torch2pc_commit": TORCH2PC_COMMIT,
        "base_image": BASE_IMAGE,
        "image_tag": IMAGE_TAG,
        "image_id": IMAGE_DIGEST,
        "image_digest": freeze.image_digest,
        "image_repo_digest": freeze.image_repo_digest,
        "image_size_bytes": IMAGE_SIZE_BYTES,
        "architecture": "amd64",
        "os": "linux",
        "oci_revision": SOURCE_COMMIT,
        "oci_base_image": BASE_IMAGE,
        "container_source_commit": SOURCE_COMMIT,
        "container_entrypoint": [
            "/usr/bin/tini",
            "--",
            "/workspace/scripts/container_entrypoint.sh",
        ],
        "container_workdir": "/workspace",
        "attempt_002_entrypoint_sha256": ENTRYPOINT_SHA256,
        "attempt_002_contract_sha256": CONTRACT_SHA256,
        "attempt_002_wrapper_sha256": WRAPPER_SHA256,
        "attempt_002_backend_sha256": BACKEND_SHA256,
        "build_invocation_count": 1,
        "image_inspection_count": 2,
        "automatic_build_retry_performed": False,
        "docker_run_invoked": False,
        "container_created": False,
        "runtime_execution_started": False,
        "runtime_execution_performed": False,
        "model_code_invoked": False,
        "attempt_002_created": False,
        "attempt_002_authorization_issued": False,
        "scientific_execution_open": False,
        "test_dataset_access": False,
        "publication_permitted": False,
    }
    for key, expected in exact.items():
        if value.get(key) != expected:
            raise Attempt002ExecutionFreezeVerificationError(
                f"host image identity {key} differs"
            )


def _verify_capture_reference(
    value: dict[str, object],
    freeze: Attempt002ExecutionFreeze,
) -> None:
    digest = value.pop("reference_sha256", None)
    if digest != sha256_object(value) or digest != CAPTURE_REFERENCE_SHA256:
        raise Attempt002ExecutionFreezeVerificationError(
            "capture reference digest differs"
        )
    exact: Mapping[str, object] = {
        "schema_version": 1,
        "reference_id": (
            "stage3b-qwake-lc4-e-attempt-002-image-capture-reference-v1"
        ),
        "status": (
            "external_capture_preserved_and_normalized_identity_recorded"
        ),
        "capture_id": CAPTURE_ID,
        "capture_sha256": CAPTURE_SHA256,
        "capture_directory_name": CAPTURE_DIRECTORY_NAME,
        "capture_location_kind": "external-local-preserved-directory",
        "capture_directory_absolute_path_recorded": False,
        "capture_directory_copied_into_repository": False,
        "source_commit": SOURCE_COMMIT,
        "image_digest": freeze.image_digest,
        "image_repo_digest": freeze.image_repo_digest,
        "build_invocation_count": 1,
        "image_inspection_count": 2,
        "docker_run_invoked": False,
        "container_created": False,
        "runtime_execution_started": False,
        "runtime_execution_performed": False,
        "attempt_002_created": False,
        "attempt_002_authorization_issued": False,
    }
    for key, expected in exact.items():
        if value.get(key) != expected:
            raise Attempt002ExecutionFreezeVerificationError(
                f"capture reference {key} differs"
            )
    if "/" in CAPTURE_DIRECTORY_NAME or "\\" in CAPTURE_DIRECTORY_NAME:
        raise Attempt002ExecutionFreezeVerificationError(
            "capture directory name is not a basename"
        )


def _verify_materialization(
    value: dict[str, object],
    freeze: Attempt002ExecutionFreeze,
    image_identity: dict[str, object],
    capture_reference: dict[str, object],
) -> None:
    digest = value.pop("materialization_sha256", None)
    if digest != sha256_object(value) or digest != MATERIALIZATION_SHA256:
        raise Attempt002ExecutionFreezeVerificationError(
            "execution-freeze materialization digest differs"
        )
    exact: Mapping[str, object] = {
        "schema_version": 1,
        "materialization_id": (
            "stage3b-qwake-lc4-e-attempt-002-"
            "execution-freeze-materialization-v1"
        ),
        "status": (
            "corrected_image_identity_and_execution_freeze_"
            "materialized_authorization_absent"
        ),
        "source_commit": SOURCE_COMMIT,
        "wrapper_commit": SOURCE_COMMIT,
        "torch2pc_commit": TORCH2PC_COMMIT,
        "capture_sha256": CAPTURE_SHA256,
        "image_identity_sha256": IMAGE_IDENTITY_SHA256,
        "capture_reference_sha256": CAPTURE_REFERENCE_SHA256,
        "execution_freeze_sha256": freeze.freeze_sha256,
        "image_digest": freeze.image_digest,
        "image_repo_digest": freeze.image_repo_digest,
        "immutable_corrected_image_present": True,
        "host_image_identity_record_present": True,
        "execution_freeze_materialized": True,
        "attempt_002_authorization_issued": False,
        "attempt_002_authorization_consumed": False,
        "attempt_002_started": False,
        "attempt_002_lease_v1_present": False,
        "attempt_002_lease_v2_present": False,
        "attempt_002_durable_outcome_present": False,
        "runtime_execution_started": False,
        "runtime_execution_performed": False,
        "engineering_evidence_present": False,
        "scientific_execution_open": False,
        "test_dataset_access": False,
        "publication_permitted": False,
        "corrected_host_invocation_stack_authored": False,
        "authorization_authoring_admissible": False,
    }
    for key, expected in exact.items():
        if value.get(key) != expected:
            raise Attempt002ExecutionFreezeVerificationError(
                f"execution-freeze materialization {key} differs"
            )
    if image_identity.get("capture_sha256") != value["capture_sha256"]:
        raise Attempt002ExecutionFreezeVerificationError(
            "image identity and materialization capture differ"
        )
    if capture_reference.get("capture_sha256") != value["capture_sha256"]:
        raise Attempt002ExecutionFreezeVerificationError(
            "capture reference and materialization differ"
        )


def _verify_identity_env(
    identity: dict[str, str],
    freeze: Attempt002ExecutionFreeze,
    image_identity: dict[str, object],
    capture_reference: dict[str, object],
    materialization: dict[str, object],
) -> None:
    exact = {
        "CAPTURE_ID": CAPTURE_ID,
        "CAPTURE_SHA256": CAPTURE_SHA256,
        "CAPTURE_DIRECTORY_NAME": CAPTURE_DIRECTORY_NAME,
        "SOURCE_COMMIT": SOURCE_COMMIT,
        "WRAPPER_COMMIT": SOURCE_COMMIT,
        "TORCH2PC_COMMIT": TORCH2PC_COMMIT,
        "BASE_IMAGE": BASE_IMAGE,
        "IMAGE_TAG": IMAGE_TAG,
        "IMAGE_ID": IMAGE_DIGEST,
        "IMAGE_DIGEST": freeze.image_digest,
        "IMAGE_REPO_DIGEST": freeze.image_repo_digest,
        "IMAGE_SIZE_BYTES": str(IMAGE_SIZE_BYTES),
        "OCI_REVISION": SOURCE_COMMIT,
        "OCI_BASE_IMAGE": BASE_IMAGE,
        "CONTAINER_SOURCE_COMMIT": SOURCE_COMMIT,
        "CONTRACT_SHA256": CONTRACT_SHA256,
        "WRAPPER_SHA256": WRAPPER_SHA256,
        "BACKEND_SHA256": BACKEND_SHA256,
        "ENTRYPOINT_SHA256": ENTRYPOINT_SHA256,
        "SCIENTIFIC_AUTHORIZATION_SHA256": (
            SCIENTIFIC_AUTHORIZATION_SHA256
        ),
        "SCIENTIFIC_AUTHORIZATION_FILE_SHA256": (
            SCIENTIFIC_AUTHORIZATION_FILE_SHA256
        ),
        "FREEZE_SHA256": freeze.freeze_sha256,
        "IMAGE_IDENTITY_SHA256": IMAGE_IDENTITY_SHA256,
        "CAPTURE_REFERENCE_SHA256": CAPTURE_REFERENCE_SHA256,
        "MATERIALIZATION_SHA256": MATERIALIZATION_SHA256,
        "BUILD_INVOCATION_COUNT": "1",
        "IMAGE_INSPECTION_COUNT": "2",
        "DOCKER_RUN_INVOKED": "false",
        "CONTAINER_CREATED": "false",
        "EXECUTION_FREEZE_MATERIALIZED": "true",
        "ATTEMPT_002_AUTHORIZATION_ISSUED": "false",
        "ATTEMPT_002_LEASE_V1_PRESENT": "false",
        "ATTEMPT_002_LEASE_V2_PRESENT": "false",
        "ATTEMPT_002_DURABLE_OUTCOME_PRESENT": "false",
        "RUNTIME_EXECUTION_STARTED": "false",
        "RUNTIME_EXECUTION_PERFORMED": "false",
        "SCIENTIFIC_EXECUTION_OPEN": "false",
        "TEST_DATASET_ACCESS": "false",
        "PUBLICATION_PERMITTED": "false",
    }
    if identity != exact:
        raise Attempt002ExecutionFreezeVerificationError(
            "identity.env differs"
        )
    if image_identity.get("identity_sha256") not in (None, IMAGE_IDENTITY_SHA256):
        raise Attempt002ExecutionFreezeVerificationError(
            "image identity digest relation differs"
        )
    if (
        capture_reference.get("reference_sha256")
        not in (None, CAPTURE_REFERENCE_SHA256)
    ):
        raise Attempt002ExecutionFreezeVerificationError(
            "capture reference digest relation differs"
        )
    if (
        materialization.get("materialization_sha256")
        not in (None, MATERIALIZATION_SHA256)
    ):
        raise Attempt002ExecutionFreezeVerificationError(
            "materialization digest relation differs"
        )


def _verify_effect_boundary(root: Path) -> None:
    paths = (
        ATTEMPT_002_OUTPUT_ROOT,
        ATTEMPT_002_LEASE_V1_RELATIVE,
        ATTEMPT_002_LEASE_V2_RELATIVE,
        ATTEMPT_002_DURABLE_OUTCOME_RELATIVE,
        ATTEMPT_002_AUTHORIZATION_ROOT,
    )
    for relative in paths:
        if os.path.lexists(root / relative):
            raise Attempt002ExecutionFreezeVerificationError(
                f"attempt-002 effect boundary is open: {relative}"
            )
    staging_pattern = f".{ATTEMPT_002_OUTPUT_ROOT.name}.staging-*"
    if tuple((root / ATTEMPT_002_OUTPUT_ROOT.parent).glob(staging_pattern)):
        raise Attempt002ExecutionFreezeVerificationError(
            "attempt-002 staging exists"
        )


def _read_json(path: Path) -> dict[str, object]:
    if not path.is_file() or path.is_symlink():
        raise Attempt002ExecutionFreezeVerificationError(
            f"regular JSON file is absent: {path}"
        )
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Attempt002ExecutionFreezeVerificationError(
            f"invalid JSON file: {path}"
        ) from exc
    if not isinstance(value, dict):
        raise Attempt002ExecutionFreezeVerificationError(
            f"JSON root is not an object: {path}"
        )
    if path.read_bytes() != canonical_json(value).encode("utf-8"):
        raise Attempt002ExecutionFreezeVerificationError(
            f"JSON serialization differs: {path}"
        )
    return cast(dict[str, object], value)


def _read_identity_env(path: Path) -> dict[str, str]:
    if not path.is_file() or path.is_symlink():
        raise Attempt002ExecutionFreezeVerificationError(
            "identity.env is absent"
        )
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or "=" not in line:
            raise Attempt002ExecutionFreezeVerificationError(
                "identity.env line shape differs"
            )
        key, value = line.split("=", 1)
        if not key or key in result:
            raise Attempt002ExecutionFreezeVerificationError(
                "identity.env key differs"
            )
        result[key] = value
    return result


def _verify_registry(
    registry_path: Path,
    base: Path,
    expected_paths: tuple[str, ...],
) -> None:
    if not registry_path.is_file() or registry_path.is_symlink():
        raise Attempt002ExecutionFreezeVerificationError(
            f"regular registry is absent: {registry_path}"
        )
    observed: list[str] = []
    for line in registry_path.read_text(encoding="utf-8").splitlines():
        parts = line.split("  ", 1)
        if len(parts) != 2:
            raise Attempt002ExecutionFreezeVerificationError(
                "registry line shape differs"
            )
        expected_digest, relative = parts
        if relative in observed:
            raise Attempt002ExecutionFreezeVerificationError(
                "registry path is duplicated"
            )
        observed.append(relative)
        candidate = (base / relative).resolve()
        try:
            candidate.relative_to(base.resolve())
        except ValueError as exc:
            raise Attempt002ExecutionFreezeVerificationError(
                "registry path escapes base"
            ) from exc
        if _sha256_file(candidate) != f"sha256:{expected_digest}":
            raise Attempt002ExecutionFreezeVerificationError(
                f"registry identity differs: {relative}"
            )
    if tuple(observed) != expected_paths:
        raise Attempt002ExecutionFreezeVerificationError(
            "registry path order or set differs"
        )


def _sha256_file(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise Attempt002ExecutionFreezeVerificationError(
            f"regular file is absent: {path}"
        )
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    args = parse_args()
    verify(args.project_root)
    print("OK: attempt-002 corrected image identity verified")
    print("OK: attempt-002 execution freeze verified")
    print(f"IMAGE_DIGEST={IMAGE_DIGEST}")
    print(f"IMAGE_REPO_DIGEST={IMAGE_REPO_DIGEST}")
    print(f"FREEZE_SHA256={FREEZE_SHA256}")
    print("ATTEMPT_002_AUTHORIZATION_ISSUED=false")
    print("ATTEMPT_002_RUNTIME_STARTED=false")
    print("RUNTIME_EXECUTION_PERFORMED=false")
    print("SCIENTIFIC_EXECUTION_OPEN=false")
    print("TEST_DATASET_ACCESS=false")
    print("PUBLICATION_PERMITTED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
