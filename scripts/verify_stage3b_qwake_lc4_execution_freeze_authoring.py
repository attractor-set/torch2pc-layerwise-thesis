#!/usr/bin/env python3
"""Verify QW-LC4-E execution-freeze authoring without runtime effects."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

from torch2pc_thesis.stage3b_qwake_lc4_execution_admission import (
    AUTHORIZED_OUTPUT_ROOT,
    EXECUTION_LEASE_RELATIVE,
)
from torch2pc_thesis.stage3b_qwake_lc4_execution_freeze import (
    EXECUTION_FREEZE_REQUEST_ID,
    IMPLEMENTATION_HEAD_COMMIT,
    IMPLEMENTATION_MERGE_COMMIT,
    ONE_SHOT_ENTRYPOINT_ID,
    RUNTIME_BACKEND_CONTRACT_ID,
    build_execution_freeze_request,
    load_execution_freeze_request,
    validate_execution_freeze_request,
)

AUTHORING_ROOT_RELATIVE = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-execution-freeze-authoring-v1"
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    return parser


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    args = _parser().parse_args()
    project_root = args.project_root.expanduser().resolve()
    repository_lease = project_root / EXECUTION_LEASE_RELATIVE
    repository_output = project_root / AUTHORIZED_OUTPUT_ROOT

    if repository_lease.exists() or repository_lease.is_symlink():
        raise RuntimeError("repository execution lease is already present")
    if repository_output.exists() or repository_output.is_symlink():
        raise RuntimeError("repository runtime output is already present")

    request = build_execution_freeze_request(project_root)
    validate_execution_freeze_request(request, project_root)

    with tempfile.TemporaryDirectory(
        prefix="qwake-lc4-e-execution-freeze-authoring-verifier-"
    ) as temporary_raw:
        request_path = Path(temporary_raw) / "execution-freeze-request.json"
        request_path.write_text(
            request.canonical_json(),
            encoding="utf-8",
        )
        if load_execution_freeze_request(request_path) != request:
            raise RuntimeError("execution-freeze request round trip differs")

    authoring_root = project_root / AUTHORING_ROOT_RELATIVE
    authoring_json = authoring_root / "authoring.json"
    authoring_registry = authoring_root / "SHA256SUMS"
    expected, relative = authoring_registry.read_text(
        encoding="utf-8"
    ).strip().split("  ", 1)
    if relative != "authoring.json":
        raise RuntimeError("authoring registry path differs")
    if hashlib.sha256(authoring_json.read_bytes()).hexdigest() != expected:
        raise RuntimeError("authoring registry identity differs")

    authoring = json.loads(authoring_json.read_text(encoding="utf-8"))
    if authoring["authoring_id"] != (
        "stage3b-qwake-lc4-e-execution-freeze-authoring-v1"
    ):
        raise RuntimeError("execution-freeze authoring id differs")
    if authoring["next_slice"] != (
        "QW-LC4-E-execution-freeze-authoring-commit"
    ):
        raise RuntimeError("execution-freeze next slice differs")
    if authoring["post_merge_next_slice"] != (
        "QW-LC4-E-runtime-backend-implementation"
    ):
        raise RuntimeError("execution-freeze post-merge slice differs")

    if repository_lease.exists() or repository_lease.is_symlink():
        raise RuntimeError("verifier materialized repository lease")
    if repository_output.exists() or repository_output.is_symlink():
        raise RuntimeError("verifier materialized repository output")

    print(f"EXECUTION_FREEZE_REQUEST_ID={EXECUTION_FREEZE_REQUEST_ID}")
    print(f"EXECUTION_FREEZE_REQUEST_SHA256={request.request_sha256}")
    print(f"IMPLEMENTATION_MERGE_COMMIT={IMPLEMENTATION_MERGE_COMMIT}")
    print(f"IMPLEMENTATION_HEAD_COMMIT={IMPLEMENTATION_HEAD_COMMIT}")
    print(f"RUNTIME_BACKEND_CONTRACT_ID={RUNTIME_BACKEND_CONTRACT_ID}")
    print(f"ONE_SHOT_ENTRYPOINT_ID={ONE_SHOT_ENTRYPOINT_ID}")
    print(f"AUTHORING_JSON_SHA256={_sha256(authoring_json)}")
    print(f"AUTHORING_REGISTRY_SHA256={_sha256(authoring_registry)}")
    print("LEASE_WRAPPER_IMPLEMENTATION_MERGED=true")
    print("EXECUTION_FREEZE_BRANCH_OPEN=true")
    print("EXECUTION_FREEZE_CONTRACT_MATERIALIZED=true")
    print("CONCRETE_RUNTIME_BACKEND_PRESENT=false")
    print("ONE_SHOT_ENTRYPOINT_PRESENT=false")
    print("IMMUTABLE_EXECUTION_IMAGE_PRESENT=false")
    print("EXECUTION_FREEZE_MATERIALIZED=false")
    print("EXECUTION_LEASE_MATERIALIZED=false")
    print("QW_LC4_E_EXECUTION_PERMITTED=false")
    print("AUTHORIZATION_CONSUMED=false")
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
