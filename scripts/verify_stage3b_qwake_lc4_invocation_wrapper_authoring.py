#!/usr/bin/env python3
"""Verify QW-LC4-E host invocation-wrapper authoring without effects."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path
from typing import cast

from torch2pc_thesis.stage3b_qwake_lc4_invocation_authorization import (
    AUTHORIZATION_ROOT_RELATIVE,
    EXECUTION_LEASE_RELATIVE,
)
from torch2pc_thesis.stage3b_qwake_lc4_invocation_wrapper import (
    AUTHORIZATION_HEAD_COMMIT,
    AUTHORIZATION_MERGE_COMMIT,
    INVOCATION_WRAPPER_CONTRACT_ID,
    build_one_shot_invocation_wrapper_contract,
    load_one_shot_invocation_wrapper_contract,
    validate_one_shot_invocation_wrapper_contract,
)

AUTHORING_ROOT_RELATIVE = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-one-shot-invocation-wrapper-authoring-v1"
)
MODULE_RELATIVE = Path(
    "src/torch2pc_thesis/stage3b_qwake_lc4_invocation_wrapper.py"
)
VERIFIER_RELATIVE = Path(
    "scripts/verify_stage3b_qwake_lc4_invocation_wrapper_authoring.py"
)
TEST_RELATIVE = Path(
    "tests/unit/test_stage3b_qwake_lc4_invocation_wrapper_authoring.py"
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    return parser


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _object(value: object, field_name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise RuntimeError(f"{field_name} is not an object")
    return cast(dict[str, object], value)


def _verify_authoring_package(root: Path) -> tuple[Path, Path, dict[str, object]]:
    package = root / AUTHORING_ROOT_RELATIVE
    authoring_json = package / "authoring.json"
    registry = package / "SHA256SUMS"
    if not package.is_dir() or package.is_symlink():
        raise RuntimeError("invocation-wrapper authoring package is absent")
    observed = {
        path.name
        for path in package.iterdir()
        if path.is_file() and not path.is_symlink()
    }
    if observed != {"SHA256SUMS", "authoring.json"}:
        raise RuntimeError("invocation-wrapper authoring package scope differs")
    expected, relative = registry.read_text(encoding="utf-8").strip().split("  ", 1)
    if relative != "authoring.json":
        raise RuntimeError("invocation-wrapper authoring registry path differs")
    if hashlib.sha256(authoring_json.read_bytes()).hexdigest() != expected:
        raise RuntimeError("invocation-wrapper authoring registry differs")
    payload = json.loads(authoring_json.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("invocation-wrapper authoring record is not an object")
    return authoring_json, registry, cast(dict[str, object], payload)


def main() -> int:
    args = _parser().parse_args()
    project_root = args.project_root.expanduser().resolve()
    lease_path = project_root / EXECUTION_LEASE_RELATIVE
    output_root = (
        project_root
        / "results/stage-3/qwake-lc4-runtime-validation-v1-attempt-001"
    )

    if lease_path.exists() or lease_path.is_symlink():
        raise RuntimeError("repository execution lease is already present")
    if output_root.exists() or output_root.is_symlink():
        raise RuntimeError("repository runtime output is already present")

    contract = build_one_shot_invocation_wrapper_contract(project_root)
    validate_one_shot_invocation_wrapper_contract(contract, project_root)

    with tempfile.TemporaryDirectory(
        prefix="qwake-lc4-e-invocation-wrapper-authoring-verifier-"
    ) as temporary_raw:
        contract_path = Path(temporary_raw) / "invocation-wrapper-contract.json"
        contract_path.write_text(contract.canonical_json(), encoding="utf-8")
        if load_one_shot_invocation_wrapper_contract(contract_path) != contract:
            raise RuntimeError("invocation-wrapper contract round trip differs")

    authoring_json, authoring_registry, authoring = _verify_authoring_package(
        project_root
    )
    if authoring.get("authoring_id") != (
        "stage3b-qwake-lc4-e-one-shot-invocation-wrapper-authoring-v1"
    ):
        raise RuntimeError("invocation-wrapper authoring id differs")
    if authoring.get("post_merge_next_slice") != (
        "QW-LC4-E-one-shot-invocation-wrapper-implementation"
    ):
        raise RuntimeError("invocation-wrapper post-merge slice differs")

    contracts = _object(authoring.get("contracts"), "contracts")
    expected_contracts: dict[str, object] = {
        "contract_id": contract.contract_id,
        "contract_sha256": contract.contract_sha256,
        "module_path": MODULE_RELATIVE.as_posix(),
        "module_sha256": _sha256(project_root / MODULE_RELATIVE),
        "verifier_path": VERIFIER_RELATIVE.as_posix(),
        "verifier_sha256": _sha256(project_root / VERIFIER_RELATIVE),
        "test_path": TEST_RELATIVE.as_posix(),
        "test_sha256": _sha256(project_root / TEST_RELATIVE),
        "mount_count": len(contract.mounts),
        "device_binding_count": len(contract.device_bindings),
        "tmpfs_target": contract.tmpfs_target,
        "tmpfs_required": True,
        "container_command_template_present": True,
        "image_reference_must_use_repo_digest": True,
        "image_identity_inspection_required": True,
        "image_source_label_verification_required": True,
        "network_disabled": True,
        "read_only_root_filesystem": True,
        "no_new_privileges": True,
        "drop_all_capabilities": True,
        "privileged_forbidden": True,
        "project_source_bind_forbidden": True,
        "test_dataset_mount_forbidden": True,
        "claim_and_execute_same_process_required": True,
        "no_retry_after_claim_required": True,
    }
    for field_name, expected in expected_contracts.items():
        if contracts.get(field_name) != expected:
            raise RuntimeError(
                f"invocation-wrapper authoring contract field differs: {field_name}"
            )

    gates = _object(authoring.get("gates"), "gates")
    expected_gates: dict[str, object] = {
        "invocation_authorization_post_merge_verified": True,
        "invocation_wrapper_authoring_branch_open": True,
        "invocation_wrapper_contract_present": True,
        "host_runtime_invoker_present": False,
        "image_inspection_implemented": False,
        "invocation_command_materialized": False,
        "branch_runtime_execution_permitted": False,
        "execution_lease_materialized": False,
        "authorization_consumed": False,
        "runtime_execution_started": False,
        "runtime_execution_performed": False,
        "engineering_evidence_present": False,
        "scientific_execution_open": False,
        "test_dataset_access": False,
        "publication_permitted": False,
        "local_compute_execution_open": False,
    }
    if gates != expected_gates:
        raise RuntimeError("invocation-wrapper authoring gates differ")

    source = _object(authoring.get("source"), "source")
    expected_source: dict[str, object] = {
        "authorization_head_commit": AUTHORIZATION_HEAD_COMMIT,
        "authorization_id": contract.authorization_id,
        "authorization_merge_commit": AUTHORIZATION_MERGE_COMMIT,
        "authorization_sha256": contract.authorization_sha256,
        "image_digest": contract.image_digest,
        "image_repo_digest": contract.image_repo_digest,
        "image_source_commit": contract.image_source_commit,
        "torch2pc_commit": contract.torch2pc_commit,
    }
    for field_name, expected in expected_source.items():
        if source.get(field_name) != expected:
            raise RuntimeError(
                f"invocation-wrapper authoring source field differs: {field_name}"
            )

    authorization_root = project_root / AUTHORIZATION_ROOT_RELATIVE
    if not authorization_root.is_dir():
        raise RuntimeError("invocation authorization package is absent")
    if lease_path.exists() or lease_path.is_symlink():
        raise RuntimeError("verifier materialized repository lease")
    if output_root.exists() or output_root.is_symlink():
        raise RuntimeError("verifier materialized repository output")

    print(f"INVOCATION_WRAPPER_CONTRACT_ID={INVOCATION_WRAPPER_CONTRACT_ID}")
    print(f"INVOCATION_WRAPPER_CONTRACT_SHA256={contract.contract_sha256}")
    print(f"AUTHORIZATION_MERGE_COMMIT={AUTHORIZATION_MERGE_COMMIT}")
    print(f"AUTHORIZATION_HEAD_COMMIT={AUTHORIZATION_HEAD_COMMIT}")
    print(f"AUTHORIZATION_SHA256={contract.authorization_sha256}")
    print(f"IMAGE_REPO_DIGEST={contract.image_repo_digest}")
    print(f"AUTHORING_JSON_SHA256={_sha256(authoring_json)}")
    print(f"AUTHORING_REGISTRY_SHA256={_sha256(authoring_registry)}")
    print("INVOCATION_AUTHORIZATION_POST_MERGE_VERIFIED=true")
    print("INVOCATION_WRAPPER_AUTHORING_BRANCH_OPEN=true")
    print("INVOCATION_WRAPPER_CONTRACT_PRESENT=true")
    print("CONTAINER_COMMAND_TEMPLATE_PRESENT=true")
    print(f"GPU_DEVICE_BINDING_COUNT={len(contract.device_bindings)}")
    print("TMPFS_REQUIRED=true")
    print(f"TMPFS_TARGET={contract.tmpfs_target}")
    print("HOST_RUNTIME_INVOKER_PRESENT=false")
    print("IMAGE_INSPECTION_IMPLEMENTED=false")
    print("INVOCATION_COMMAND_MATERIALIZED=false")
    print("BRANCH_RUNTIME_EXECUTION_PERMITTED=false")
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
