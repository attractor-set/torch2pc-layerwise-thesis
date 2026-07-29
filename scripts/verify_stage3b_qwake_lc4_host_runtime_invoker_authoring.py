#!/usr/bin/env python3
"""Verify the pure QW-LC4-E host-runtime-invoker authoring slice."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from torch2pc_thesis.stage3b_qwake_lc4_host_runtime_invoker import (
    AUTHORING_BASE_COMMIT,
    AUTHORIZED_OUTPUT_ROOT,
    EXECUTION_LEASE_RELATIVE,
    HOST_RUNTIME_INVOKER_CONTRACT_ID,
    WRAPPER_IMPLEMENTATION_HEAD_COMMIT,
    WRAPPER_IMPLEMENTATION_MERGE_COMMIT,
    build_host_runtime_invoker_contract,
    validate_host_runtime_invoker_contract,
)

AUTHORING_ROOT_RELATIVE = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-authoring-v1"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path("."))
    return parser.parse_args()


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _verify_authoring_record(root: Path, contract_sha256: str) -> tuple[str, str]:
    package = root / AUTHORING_ROOT_RELATIVE
    record = package / "authoring.json"
    registry = package / "SHA256SUMS"
    if not record.is_file() or record.is_symlink():
        raise RuntimeError("authoring record is absent or non-regular")
    if not registry.is_file() or registry.is_symlink():
        raise RuntimeError("authoring registry is absent or non-regular")
    lines = tuple(
        line
        for line in registry.read_text(encoding="utf-8").splitlines()
        if line
    )
    if len(lines) != 1:
        raise RuntimeError("authoring registry scope differs")
    digest, relative = lines[0].split("  ", 1)
    if relative != "authoring.json":
        raise RuntimeError("authoring registry path differs")
    if "sha256:" + digest != _sha256(record):
        raise RuntimeError("authoring record digest differs")
    payload = json.loads(record.read_text(encoding="utf-8"))
    if payload["contracts"]["contract_sha256"] != contract_sha256:
        raise RuntimeError("authoring contract digest differs")
    if payload["gates"]["host_runtime_invoker_present"] is not False:
        raise RuntimeError("authoring record opens host invoker")
    if payload["gates"]["runtime_execution_performed"] is not False:
        raise RuntimeError("authoring record opens runtime")
    return _sha256(record), _sha256(registry)


def main() -> int:
    args = parse_args()
    root = args.project_root.expanduser().resolve()
    contract = build_host_runtime_invoker_contract(root)
    validate_host_runtime_invoker_contract(contract, root)
    authoring_sha256, registry_sha256 = _verify_authoring_record(
        root,
        contract.contract_sha256,
    )

    lease_path = root / EXECUTION_LEASE_RELATIVE
    output_root = root / AUTHORIZED_OUTPUT_ROOT
    staging = tuple(output_root.parent.glob(f".{output_root.name}.staging-*"))
    if lease_path.exists() or lease_path.is_symlink():
        raise RuntimeError("execution lease was materialized")
    if output_root.exists() or output_root.is_symlink():
        raise RuntimeError("runtime output was materialized")
    if staging:
        raise RuntimeError("runtime staging tree was materialized")

    print(f"HOST_RUNTIME_INVOKER_CONTRACT_ID={HOST_RUNTIME_INVOKER_CONTRACT_ID}")
    print(f"HOST_RUNTIME_INVOKER_CONTRACT_SHA256={contract.contract_sha256}")
    print(f"AUTHORING_BASE_COMMIT={AUTHORING_BASE_COMMIT}")
    print(
        "WRAPPER_IMPLEMENTATION_HEAD_COMMIT="
        f"{WRAPPER_IMPLEMENTATION_HEAD_COMMIT}"
    )
    print(
        "WRAPPER_IMPLEMENTATION_MERGE_COMMIT="
        f"{WRAPPER_IMPLEMENTATION_MERGE_COMMIT}"
    )
    print(f"AUTHORING_JSON_SHA256={authoring_sha256}")
    print(f"AUTHORING_REGISTRY_SHA256={registry_sha256}")
    print("HOST_RUNTIME_INVOKER_CONTRACT_PRESENT=true")
    print("HOST_RUNTIME_INVOKER_PRESENT=false")
    print("HOST_RUNTIME_INVOKER_EXECUTABLE=false")
    print("HOST_DOCKER_RUN_IMPLEMENTED=false")
    print("EXACT_ARGV_ONLY=true")
    print("SHELL_INTERPRETATION_FORBIDDEN=true")
    print("EXECUTION_ATTEMPT_LIMIT=1")
    print("LEASE_CLAIM_OWNER=container_entrypoint_same_process_as_runtime")
    print("HOST_EXECUTION_LEASE_WRITE_FORBIDDEN=true")
    print("POST_CLAIM_REVALIDATION_REQUIRED=true")
    print("AUTOMATIC_RETRY_AFTER_SPAWN_FORBIDDEN=true")
    print("EXECUTION_LEASE_MATERIALIZED=false")
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
