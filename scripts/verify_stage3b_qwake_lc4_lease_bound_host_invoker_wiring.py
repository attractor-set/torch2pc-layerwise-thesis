#!/usr/bin/env python3
"""Verify the QW-LC4-E lease-bound host-invoker wiring freeze."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
from typing import Any, cast

from torch2pc_thesis.stage3b_qwake_lc4_lease_bound_host_invoker_wiring import (
    HISTORICAL_DIRECT_OPERATION_RELATIVE,
    LEASE_BOUND_HOST_INVOKER_WIRING_ID,
    LEASE_BOUND_HOST_INVOKER_WIRING_STATUS,
    WIRING_ADR_EN_RELATIVE,
    WIRING_ADR_RU_RELATIVE,
    WIRING_BASE_COMMIT,
    WIRING_MODULE_RELATIVE,
    WIRING_PACKAGE_RELATIVE,
    WIRING_RECORD_RELATIVE,
    WIRING_REGISTRY_RELATIVE,
    WIRING_SOURCE_REGISTRY_RELATIVE,
    WIRING_TEST_RELATIVE,
    WIRING_VERIFIER_RELATIVE,
    build_lease_bound_host_invoker_wiring_state,
    validate_lease_bound_host_invoker_wiring_state,
)

_EXPECTED_PACKAGE_FILES = {
    "SHA256SUMS",
    "implementation-merge-validation.json",
    "source-SHA256SUMS",
    "wiring.json",
}
_EXPECTED_SOURCE_PATHS = {
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-persistent-evidence-chain-v2-implementation-v1/"
    "SHA256SUMS",
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-persistent-evidence-chain-v2-implementation-v1/"
    "authoring-merge-validation.json",
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-persistent-evidence-chain-v2-implementation-v1/"
    "implementation.json",
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-persistent-evidence-chain-v2-implementation-v1/"
    "source-SHA256SUMS",
    "src/torch2pc_thesis/"
    "stage3b_qwake_lc4_persistent_evidence_chain_v2.py",
    "src/torch2pc_thesis/"
    "stage3b_qwake_lc4_persistent_evidence_chain_v2_implementation.py",
    "src/torch2pc_thesis/"
    "stage3b_qwake_lc4_host_runtime_invoker_implementation.py",
    HISTORICAL_DIRECT_OPERATION_RELATIVE.as_posix(),
    WIRING_MODULE_RELATIVE.as_posix(),
    WIRING_VERIFIER_RELATIVE.as_posix(),
    WIRING_TEST_RELATIVE.as_posix(),
    WIRING_ADR_RU_RELATIVE.as_posix(),
    WIRING_ADR_EN_RELATIVE.as_posix(),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path("."))
    return parser.parse_args()


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8", errors="strict"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"JSON root differs: {path}")
    return cast(dict[str, Any], payload)


def _registry(path: Path, base: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="strict").splitlines():
        digest, relative = line.split("  ", 1)
        if relative in result:
            raise RuntimeError(f"duplicate registry path: {relative}")
        result[relative] = "sha256:" + digest
        if _sha256(base / relative) != result[relative]:
            raise RuntimeError(f"registry digest differs: {relative}")
    return result


def _verify_direct_call_boundary(root: Path) -> None:
    allowed = {
        HISTORICAL_DIRECT_OPERATION_RELATIVE,
        WIRING_MODULE_RELATIVE,
    }
    observed: set[Path] = set()
    for path in (root / "src/torch2pc_thesis").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8", errors="strict"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                function = node.func
                direct_name = (
                    isinstance(function, ast.Name)
                    and function.id == "invoke_one_shot_host_runtime"
                )
                direct_attribute = (
                    isinstance(function, ast.Attribute)
                    and function.attr == "invoke_one_shot_host_runtime"
                )
                if direct_name or direct_attribute:
                    observed.add(path.relative_to(root))
    if observed != allowed:
        raise RuntimeError(
            "direct lower-level invoker call set differs: "
            + ", ".join(sorted(path.as_posix() for path in observed))
        )


def main() -> None:
    root = parse_args().project_root.expanduser().resolve()
    package = root / WIRING_PACKAGE_RELATIVE
    if {path.name for path in package.iterdir()} != _EXPECTED_PACKAGE_FILES:
        raise RuntimeError("wiring package file set differs")
    package_registry = _registry(root / WIRING_REGISTRY_RELATIVE, package)
    if set(package_registry) != {
        "implementation-merge-validation.json",
        "source-SHA256SUMS",
        "wiring.json",
    }:
        raise RuntimeError("wiring package registry scope differs")
    source_registry = _registry(root / WIRING_SOURCE_REGISTRY_RELATIVE, root)
    if set(source_registry) != _EXPECTED_SOURCE_PATHS:
        raise RuntimeError("wiring source registry scope differs")
    merge = _load(
        root / WIRING_PACKAGE_RELATIVE / "implementation-merge-validation.json"
    )
    exact_merge: dict[str, object] = {
        "pr_number": 145,
        "head_commit": "45488d8d6d96b6e4419d835479dacd5398aa30f5",
        "base_commit": "3d092440b0314f02072c9773cc91018bf2860744",
        "merge_commit": "0303a1514e2875a057ef1b20293a01b36a9c6b2b",
        "merged_at_utc": "2026-07-30T12:53:35Z",
        "commit_count": 1,
        "file_count": 18,
        "focused_tests_passed": 29,
        "targeted_tests_passed": 230,
        "full_tests_passed": 1277,
        "full_test_warnings": 14,
        "required_ci_checks_passed": True,
        "runtime_boundary_closed": True,
    }
    for field_name, expected_value in exact_merge.items():
        if merge.get(field_name) != expected_value:
            raise RuntimeError(f"implementation merge receipt differs: {field_name}")
    reduced_merge = dict(merge)
    merge_digest = reduced_merge.pop("receipt_sha256", None)
    expected_merge_digest = "sha256:" + hashlib.sha256(
        json.dumps(
            reduced_merge,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    if merge_digest != expected_merge_digest:
        raise RuntimeError("implementation merge receipt digest differs")
    record = _load(root / WIRING_RECORD_RELATIVE)
    if record.get("wiring_id") != LEASE_BOUND_HOST_INVOKER_WIRING_ID:
        raise RuntimeError("wiring ID differs")
    if record.get("status") != LEASE_BOUND_HOST_INVOKER_WIRING_STATUS:
        raise RuntimeError("wiring status differs")
    if record.get("wiring_base_commit") != WIRING_BASE_COMMIT:
        raise RuntimeError("wiring base differs")
    reduced = dict(record)
    digest = reduced.pop("wiring_sha256", None)
    expected = "sha256:" + hashlib.sha256(
        json.dumps(
            reduced,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    if digest != expected:
        raise RuntimeError("wiring semantic digest differs")
    _verify_direct_call_boundary(root)
    module_tree = ast.parse(
        (root / WIRING_MODULE_RELATIVE).read_text(
            encoding="utf-8", errors="strict"
        )
    )
    popen_calls = sum(
        1
        for node in ast.walk(module_tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "subprocess"
        and node.func.attr == "Popen"
    )
    if popen_calls != 1:
        raise RuntimeError("wiring Popen count differs")
    state = build_lease_bound_host_invoker_wiring_state(root)
    validate_lease_bound_host_invoker_wiring_state(state, root)
    print("OK: QW-LC4-E lease-bound host-invoker wiring verified")
    print(f"LEASE_BOUND_HOST_INVOKER_WIRING_ID={state.wiring_id}")
    print(f"LEASE_BOUND_HOST_INVOKER_WIRING_SHA256={record['wiring_sha256']}")
    print("PERSISTENT_LEASE_V2_IMPLEMENTATION_PRESENT=true")
    print("DURABLE_OUTCOME_WRITER_IMPLEMENTED=true")
    print("EXACT_PERSISTED_LEASE_VERIFIED_BEFORE_INVOCATION=true")
    print("FULL_STREAM_HASHING_REQUIRED=true")
    print("NO_RETRY_ENFORCED=true")
    print("HISTORICAL_DIRECT_OPERATION_SUPERSEDED=true")
    print("REPOSITORY_DIRECT_LOWER_LEVEL_CALL_FORBIDDEN=true")
    print("LEASE_BOUND_HOST_INVOKER_ENFORCED=true")
    print("FINAL_EXECUTION_ACKNOWLEDGED=false")
    print("ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false")
    print("EXECUTION_LEASE_MATERIALIZED=false")
    print("DURABLE_HOST_OUTCOME_PRESENT=false")
    print("AUTHORIZATION_CONSUMED=false")
    print("RUNTIME_EXECUTION_STARTED=false")
    print("RUNTIME_EXECUTION_PERFORMED=false")
    print("IMAGE_INSPECTION_PERFORMED=false")
    print("INVOCATION_COMMAND_MATERIALIZED=false")
    print("DOCKER_RUN_PERFORMED=false")
    print("LOCAL_COMPUTE_EXECUTION_OPEN=false")


if __name__ == "__main__":
    main()
