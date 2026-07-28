#!/usr/bin/env python3
"""Verify the materialized QW-LC4-E execution freeze without runtime effects."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, cast

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

PACKAGE_ROOT = Path(
    "experiments/frozen/stage3b-qwake-lc4-e-execution-freeze-v1"
)
EXECUTION_JSON = PACKAGE_ROOT / "execution.json"
MATERIALIZATION_JSON = PACKAGE_ROOT / "materialization.json"
EXPECTED_SOURCE_COMMIT = "67a084c0b970ad79ad0692442f660085a73b080a"
EXPECTED_IMAGE_DIGEST = (
    "sha256:7da92b8f77f6dc37d42db832c5613ef6149dc488adc5b66465faa33e48ca021d"
)
EXPECTED_IMAGE_REPO_DIGEST = (
    "torch2pc-layerwise-thesis@"
    "sha256:7da92b8f77f6dc37d42db832c5613ef6149dc488adc5b66465faa33e48ca021d"
)
EXPECTED_MODULE_SHA256 = (
    "sha256:d9ad10efe959e19d7f1b6d61d8eddd1228cb9753fa9191823d5d1ded68e9fd72"
)
EXPECTED_ENTRYPOINT_SHA256 = (
    "sha256:504c3e614e199789b25c8b1927d0a35b1b95e1f3a5411e42db794fc93782cc79"
)
EXPECTED_SOURCE_REGISTRY_SHA256 = (
    "sha256:e45f0e404ab6d7918add28bfeef95c86b2a0f363b7f0d821b28115ff2c5475b3"
)
EXPECTED_FILES = frozenset(
    {
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
)


def _sha256(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise RuntimeError(f"regular file is absent: {path}")
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON root is not an object: {path}")
    return cast(dict[str, Any], value)


def _read_registry(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        digest, separator, relative = raw.partition("  ")
        if not separator or not relative or relative in result:
            raise RuntimeError("registry is invalid")
        result[relative] = "sha256:" + digest
    return result


def verify(project_root: Path) -> dict[str, Any]:
    root = project_root.expanduser().resolve()
    package = root / PACKAGE_ROOT
    if not package.is_dir() or package.is_symlink():
        raise RuntimeError("materialized execution-freeze package is absent")
    observed = {
        path.relative_to(package).as_posix()
        for path in package.rglob("*")
        if path.is_file() and not path.is_symlink()
    }
    if observed != EXPECTED_FILES:
        raise RuntimeError("materialized execution-freeze file set differs")
    registry = _read_registry(package / "SHA256SUMS")
    if set(registry) != EXPECTED_FILES - {"SHA256SUMS"}:
        raise RuntimeError("materialized execution-freeze registry differs")
    for relative, expected in registry.items():
        if _sha256(package / relative) != expected:
            raise RuntimeError(f"materialized file digest differs: {relative}")
    if _sha256(package / "source-SHA256SUMS") != EXPECTED_SOURCE_REGISTRY_SHA256:
        raise RuntimeError("source image-input registry identity differs")
    source_registry = _read_registry(package / "source-SHA256SUMS")
    if set(source_registry) != {
        "identity.env",
        "image-build.log",
        "image-capture.json",
        "image-inspection.json",
        "static-image-validation.json",
    }:
        raise RuntimeError("source image-input registry contents differ")
    for relative, expected in source_registry.items():
        if _sha256(package / relative) != expected:
            raise RuntimeError(f"source image input differs: {relative}")

    manifest = _read_json(root / MATERIALIZATION_JSON)
    if manifest.get("materialization_id") != (
        "stage3b-qwake-lc4-e-execution-freeze-materialization-v1"
    ):
        raise RuntimeError("materialization ID differs")
    if manifest.get("status") != (
        "immutable_image_and_execution_freeze_materialized_execution_not_started"
    ):
        raise RuntimeError("materialization status differs")
    gates = manifest.get("gates")
    if not isinstance(gates, dict):
        raise RuntimeError("materialization gates are absent")
    for gate in (
        "runtime_backend_implementation_merged",
        "concrete_runtime_backend_present",
        "one_shot_entrypoint_present",
        "immutable_execution_image_present",
        "execution_freeze_materialized",
        "execution_record_runtime_execution_permitted",
    ):
        if gates.get(gate) is not True:
            raise RuntimeError(f"materialization capability is absent: {gate}")
    for gate in (
        "branch_runtime_execution_permitted",
        "execution_lease_materialized",
        "authorization_consumed",
        "runtime_execution_started",
        "runtime_execution_performed",
        "engineering_evidence_present",
        "scientific_execution_open",
        "test_dataset_access",
        "publication_permitted",
        "local_compute_execution_open",
    ):
        if gates.get(gate) is not False:
            raise RuntimeError(f"materialization effect boundary is open: {gate}")

    old_values = {
        name: os.environ.get(name)
        for name in (
            "SOURCE_GIT_COMMIT",
            "EXPERIMENT_IMAGE_DIGEST",
            "EXPERIMENT_IMAGE_REPO_DIGEST",
        )
    }
    os.environ["SOURCE_GIT_COMMIT"] = EXPECTED_SOURCE_COMMIT
    os.environ["EXPERIMENT_IMAGE_DIGEST"] = EXPECTED_IMAGE_DIGEST
    os.environ["EXPERIMENT_IMAGE_REPO_DIGEST"] = EXPECTED_IMAGE_REPO_DIGEST
    try:
        freeze = verify_materialized_execution_freeze(root)
    finally:
        for name, previous in old_values.items():
            if previous is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = previous

    if freeze.freeze_id != MATERIALIZED_EXECUTION_FREEZE_ID:
        raise RuntimeError("execution-freeze ID differs")
    if freeze.status != MATERIALIZED_EXECUTION_FREEZE_STATUS:
        raise RuntimeError("execution-freeze status differs")
    if freeze.source_commit != EXPECTED_SOURCE_COMMIT:
        raise RuntimeError("execution-freeze source commit differs")
    if freeze.wrapper_commit != EXPECTED_SOURCE_COMMIT:
        raise RuntimeError("execution-freeze wrapper commit differs")
    if freeze.torch2pc_commit != FROZEN_TORCH2PC_COMMIT:
        raise RuntimeError("execution-freeze Torch2PC commit differs")
    if freeze.image_digest != EXPECTED_IMAGE_DIGEST:
        raise RuntimeError("execution-freeze image digest differs")
    if freeze.image_repo_digest != EXPECTED_IMAGE_REPO_DIGEST:
        raise RuntimeError("execution-freeze image repo digest differs")
    if freeze.backend_id != RUNTIME_BACKEND_ID:
        raise RuntimeError("execution-freeze backend ID differs")
    if freeze.backend_module_sha256 != EXPECTED_MODULE_SHA256:
        raise RuntimeError("execution-freeze backend digest differs")
    if freeze.entrypoint_id != ONE_SHOT_ENTRYPOINT_ID:
        raise RuntimeError("execution-freeze entrypoint ID differs")
    if freeze.entrypoint_sha256 != EXPECTED_ENTRYPOINT_SHA256:
        raise RuntimeError("execution-freeze entrypoint digest differs")
    if freeze.admission_sha256 != FROZEN_ADMISSION_SHA256:
        raise RuntimeError("execution-freeze admission digest differs")
    if freeze.authorization_sha256 != FROZEN_AUTHORIZATION_SHA256:
        raise RuntimeError("execution-freeze authorization digest differs")
    if (root / EXECUTION_LEASE_RELATIVE).exists():
        raise RuntimeError("execution lease is present")
    if (root / AUTHORIZED_OUTPUT_ROOT).exists():
        raise RuntimeError("runtime output is present")
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path("."))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = verify(args.project_root)
    print("OK: QW-LC4-E execution-freeze materialization verified")
    print(f"MATERIALIZATION_ID={manifest['materialization_id']}")
    print("IMMUTABLE_EXECUTION_IMAGE_PRESENT=true")
    print("EXECUTION_FREEZE_MATERIALIZED=true")
    print("EXECUTION_RECORD_RUNTIME_EXECUTION_PERMITTED=true")
    print("BRANCH_RUNTIME_EXECUTION_PERMITTED=false")
    print("EXECUTION_LEASE_MATERIALIZED=false")
    print("RUNTIME_EXECUTION_STARTED=false")
    print("RUNTIME_EXECUTION_PERFORMED=false")
    print("ENGINEERING_EVIDENCE_PRESENT=false")
    print("SCIENTIFIC_EXECUTION_OPEN=false")
    print("TEST_DATASET_ACCESS=false")
    print("PUBLICATION_PERMITTED=false")
    print("LOCAL_COMPUTE_EXECUTION_OPEN=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
