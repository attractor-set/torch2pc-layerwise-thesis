#!/usr/bin/env python3
"""Verify QW-LC4-E image inspection and argv materialization without execution."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from torch2pc_thesis.stage3b_qwake_lc4_invocation_authorization import (
    AUTHORIZED_OUTPUT_ROOT,
    EXECUTION_LEASE_RELATIVE,
    INVOCATION_OPERATOR_ACKNOWLEDGEMENT,
)
from torch2pc_thesis.stage3b_qwake_lc4_invocation_wrapper import (
    build_one_shot_invocation_wrapper_contract,
)
from torch2pc_thesis.stage3b_qwake_lc4_invocation_wrapper_implementation import (
    FIXTURE_CLAIMED_AT_UTC,
    INVOCATION_WRAPPER_IMPLEMENTATION_ID,
    inspect_local_immutable_image,
    materialize_one_shot_invocation,
    validate_materialized_one_shot_invocation,
)

IMPLEMENTATION_ROOT_RELATIVE = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-one-shot-invocation-wrapper-implementation-v1"
)
IMPLEMENTATION_RELATIVE = IMPLEMENTATION_ROOT_RELATIVE / "implementation.json"
REGISTRY_RELATIVE = IMPLEMENTATION_ROOT_RELATIVE / "SHA256SUMS"
MODULE_RELATIVE = Path(
    "src/torch2pc_thesis/"
    "stage3b_qwake_lc4_invocation_wrapper_implementation.py"
)
VERIFIER_RELATIVE = Path(
    "scripts/verify_stage3b_qwake_lc4_invocation_wrapper_implementation.py"
)
TEST_RELATIVE = Path(
    "tests/unit/test_stage3b_qwake_lc4_invocation_wrapper_implementation.py"
)
FIXTURE_RESOURCES = {
    "HOST_UID": "1000",
    "HOST_GID": "1000",
    "VIDEO_GID": "44",
    "RENDER_GID": "109",
    "HIP_VISIBLE_DEVICES": "0",
    "CPUSET_GPU": "0-7",
    "MEM_LIMIT": "48g",
    "SHM_SIZE": "8gb",
    "TMPFS_SIZE": "8g",
    "OMP_NUM_THREADS": "4",
    "MKL_NUM_THREADS": "4",
    "OPENBLAS_NUM_THREADS": "4",
    "NUMEXPR_NUM_THREADS": "4",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path("."))
    return parser.parse_args()


def _sha256_file(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise RuntimeError(f"required regular file is absent: {path}")
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _as_mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise RuntimeError(f"{field_name} is not an object")
    return cast(Mapping[str, object], value)


def _load_implementation_record(root: Path) -> Mapping[str, object]:
    implementation_path = root / IMPLEMENTATION_RELATIVE
    registry_path = root / REGISTRY_RELATIVE
    if not registry_path.is_file() or registry_path.is_symlink():
        raise RuntimeError("implementation registry is absent or non-regular")
    lines = registry_path.read_text(encoding="utf-8").splitlines()
    if len(lines) != 1 or "  " not in lines[0]:
        raise RuntimeError("implementation registry differs")
    expected_digest, relative = lines[0].split("  ", 1)
    if relative != "implementation.json":
        raise RuntimeError("implementation registry path differs")
    if expected_digest != _sha256_file(implementation_path).removeprefix(
        "sha256:"
    ):
        raise RuntimeError("implementation registry digest differs")
    try:
        raw: Any = json.loads(implementation_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("implementation record cannot be decoded") from exc
    return _as_mapping(raw, "implementation record")


def _require_record(root: Path, record: Mapping[str, object]) -> None:
    contracts = _as_mapping(record.get("contracts"), "contracts")
    gates = _as_mapping(record.get("gates"), "gates")
    exact: Mapping[str, object] = {
        "implementation_id": INVOCATION_WRAPPER_IMPLEMENTATION_ID,
        "status": (
            "image_inspection_and_command_materialization_implemented_"
            "runtime_invoker_absent"
        ),
    }
    for field_name, expected in exact.items():
        if record.get(field_name) != expected:
            raise RuntimeError(f"implementation record differs: {field_name}")
    expected_hashes = {
        "module_sha256": _sha256_file(root / MODULE_RELATIVE),
        "verifier_sha256": _sha256_file(root / VERIFIER_RELATIVE),
        "test_sha256": _sha256_file(root / TEST_RELATIVE),
    }
    for field_name, expected in expected_hashes.items():
        if contracts.get(field_name) != expected:
            raise RuntimeError(f"implementation code digest differs: {field_name}")
    expected_gates: Mapping[str, object] = {
        "image_inspection_implemented": True,
        "invocation_command_materialized": True,
        "invocation_command_persisted": False,
        "host_runtime_invoker_present": False,
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
    for field_name, expected in expected_gates.items():
        if gates.get(field_name) != expected:
            raise RuntimeError(f"implementation gate differs: {field_name}")


def _require_effect_absence(root: Path) -> None:
    lease = root / EXECUTION_LEASE_RELATIVE
    output = root / AUTHORIZED_OUTPUT_ROOT
    if lease.exists() or lease.is_symlink():
        raise RuntimeError("execution lease was materialized")
    if output.exists() or output.is_symlink():
        raise RuntimeError("runtime output was materialized")
    staging = tuple(output.parent.glob(f".{output.name}.staging-*"))
    if staging:
        raise RuntimeError("runtime staging tree was materialized")


def main() -> int:
    args = parse_args()
    root = args.project_root.expanduser().resolve()
    _require_effect_absence(root)
    record = _load_implementation_record(root)
    _require_record(root, record)
    contract = build_one_shot_invocation_wrapper_contract(root)
    inspection = inspect_local_immutable_image(root)
    materialized = materialize_one_shot_invocation(
        root,
        image_inspection=inspection,
        host_resources=FIXTURE_RESOURCES,
        claimed_at_utc=FIXTURE_CLAIMED_AT_UTC,
        operator_acknowledgement=INVOCATION_OPERATOR_ACKNOWLEDGEMENT,
    )
    validate_materialized_one_shot_invocation(
        materialized,
        root,
        image_inspection=inspection,
        host_resources=FIXTURE_RESOURCES,
        claimed_at_utc=FIXTURE_CLAIMED_AT_UTC,
        operator_acknowledgement=INVOCATION_OPERATOR_ACKNOWLEDGEMENT,
    )
    _require_effect_absence(root)

    print(f"INVOCATION_WRAPPER_IMPLEMENTATION_ID={materialized.implementation_id}")
    print(f"INVOCATION_WRAPPER_CONTRACT_ID={contract.contract_id}")
    print(f"INVOCATION_WRAPPER_CONTRACT_SHA256={contract.contract_sha256}")
    print(f"IMAGE_REFERENCE={inspection.image_reference}")
    print(f"IMAGE_ID={inspection.image_id}")
    print(f"IMAGE_INSPECTION_SHA256={inspection.inspection_sha256}")
    print(f"INVOCATION_COMMAND_SHA256={materialized.command_sha256}")
    print(f"INVOCATION_ARGV_LENGTH={len(materialized.argv)}")
    print(f"INVOCATION_MOUNT_COUNT={len(materialized.mounts)}")
    print("IMAGE_INSPECTION_IMPLEMENTED=true")
    print("INVOCATION_COMMAND_MATERIALIZED=true")
    print("INVOCATION_COMMAND_PERSISTED=false")
    print("HOST_RUNTIME_INVOKER_PRESENT=false")
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
