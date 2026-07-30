#!/usr/bin/env python3
"""Verify QW-LC4-E persistent-evidence-chain-v2 persistence implementation."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, cast

from torch2pc_thesis.stage3b_qwake_lc4_persistent_evidence_chain_v2 import (
    DURABLE_HOST_OUTCOME_RELATIVE,
    EXECUTION_LEASE_V2_RELATIVE,
    verify_persistent_evidence_chain_v2,
)
from torch2pc_thesis.stage3b_qwake_lc4_persistent_evidence_chain_v2_implementation import (
    AUTHORING_HEAD_COMMIT,
    AUTHORING_MERGE_COMMIT,
    AUTHORING_MERGED_AT_UTC,
    AUTHORING_PARENT_COMMIT,
    AUTHORING_PR_NUMBER,
    IMPLEMENTATION_ADR_EN_RELATIVE,
    IMPLEMENTATION_ADR_RU_RELATIVE,
    IMPLEMENTATION_BASE_COMMIT,
    IMPLEMENTATION_MODULE_RELATIVE,
    IMPLEMENTATION_PACKAGE_RELATIVE,
    IMPLEMENTATION_RECORD_RELATIVE,
    IMPLEMENTATION_REGISTRY_RELATIVE,
    IMPLEMENTATION_SOURCE_REGISTRY_RELATIVE,
    IMPLEMENTATION_TEST_RELATIVE,
    IMPLEMENTATION_VERIFIER_RELATIVE,
    LEGACY_EXECUTION_LEASE_RELATIVE,
    PERSISTENT_EVIDENCE_CHAIN_V2_IMPLEMENTATION_ID,
    PERSISTENT_EVIDENCE_CHAIN_V2_IMPLEMENTATION_STATUS,
)

_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
_EXPECTED_PACKAGE_FILES = frozenset(
    {
        "SHA256SUMS",
        "authoring-merge-validation.json",
        "implementation.json",
        "source-SHA256SUMS",
    }
)
_EXPECTED_SOURCE_PATHS = frozenset(
    {
        "experiments/frozen/"
        "stage3b-qwake-lc4-e-persistent-evidence-chain-v2-authoring-v1/chain.json",
        "experiments/frozen/"
        "stage3b-qwake-lc4-e-persistent-evidence-chain-v2-authoring-v1/"
        "post-merge-validation.json",
        "experiments/frozen/"
        "stage3b-qwake-lc4-e-persistent-evidence-chain-v2-authoring-v1/"
        "source-SHA256SUMS",
        "src/torch2pc_thesis/"
        "stage3b_qwake_lc4_persistent_evidence_chain_v2.py",
        IMPLEMENTATION_MODULE_RELATIVE.as_posix(),
        IMPLEMENTATION_VERIFIER_RELATIVE.as_posix(),
        IMPLEMENTATION_TEST_RELATIVE.as_posix(),
        IMPLEMENTATION_ADR_RU_RELATIVE.as_posix(),
        IMPLEMENTATION_ADR_EN_RELATIVE.as_posix(),
    }
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path("."))
    return parser.parse_args()


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise RuntimeError(f"required JSON is absent or invalid: {path}")
    payload = json.loads(path.read_text(encoding="utf-8", errors="strict"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"JSON root differs: {path}")
    return cast(dict[str, Any], payload)


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _semantic_sha256(payload: dict[str, Any], field: str) -> str:
    reduced = dict(payload)
    reduced.pop(field)
    return "sha256:" + hashlib.sha256(_canonical(reduced)).hexdigest()


def _sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _registry(path: Path) -> dict[str, str]:
    if not path.is_file() or path.is_symlink():
        raise RuntimeError(f"registry is absent or invalid: {path}")
    result: dict[str, str] = {}
    for line in path.read_text(
        encoding="utf-8",
        errors="strict",
    ).splitlines():
        digest, relative = line.split("  ", 1)
        if relative in result:
            raise RuntimeError(f"duplicate registry path: {relative}")
        result[relative] = "sha256:" + digest
    return result


def _verify_package(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    package = root / IMPLEMENTATION_PACKAGE_RELATIVE
    if not package.is_dir() or package.is_symlink():
        raise RuntimeError("implementation package is absent or invalid")
    if frozenset(path.name for path in package.iterdir()) != _EXPECTED_PACKAGE_FILES:
        raise RuntimeError("implementation package file set differs")

    implementation_path = root / IMPLEMENTATION_RECORD_RELATIVE
    merge_path = root / (
        IMPLEMENTATION_PACKAGE_RELATIVE / "authoring-merge-validation.json"
    )
    source_registry_path = root / IMPLEMENTATION_SOURCE_REGISTRY_RELATIVE
    package_registry_path = root / IMPLEMENTATION_REGISTRY_RELATIVE

    implementation = _load_json(implementation_path)
    merge = _load_json(merge_path)
    package_registry = _registry(package_registry_path)
    expected_package_registry = {
        "authoring-merge-validation.json": _sha256_file(merge_path),
        "implementation.json": _sha256_file(implementation_path),
        "source-SHA256SUMS": _sha256_file(source_registry_path),
    }
    if package_registry != expected_package_registry:
        raise RuntimeError("implementation package registry differs")

    source_registry = _registry(source_registry_path)
    if frozenset(source_registry) != _EXPECTED_SOURCE_PATHS:
        raise RuntimeError("implementation source registry path set differs")
    for relative, expected in source_registry.items():
        observed = _sha256_file(root / relative)
        if observed != expected:
            raise RuntimeError(f"implementation source digest differs: {relative}")
    return implementation, merge


def _verify_records(
    implementation: dict[str, Any],
    merge: dict[str, Any],
    chain_sha256: str,
) -> None:
    exact_implementation: dict[str, object] = {
        "schema_version": 1,
        "implementation_id": PERSISTENT_EVIDENCE_CHAIN_V2_IMPLEMENTATION_ID,
        "status": PERSISTENT_EVIDENCE_CHAIN_V2_IMPLEMENTATION_STATUS,
        "implementation_base_commit": IMPLEMENTATION_BASE_COMMIT,
        "authoring_pr_number": AUTHORING_PR_NUMBER,
        "authoring_head_commit": AUTHORING_HEAD_COMMIT,
        "authoring_parent_commit": AUTHORING_PARENT_COMMIT,
        "authoring_merge_commit": AUTHORING_MERGE_COMMIT,
        "authoring_merged_at_utc": AUTHORING_MERGED_AT_UTC,
        "persistent_evidence_chain_v2_sha256": chain_sha256,
        "persistent_lease_v2_implementation_present": True,
        "durable_outcome_writer_implemented": True,
        "exclusive_no_overwrite": True,
        "canonical_json_required": True,
        "file_mode_0600_required": True,
        "file_fsync_required": True,
        "parent_directory_fsync_required": True,
        "symbolic_parent_forbidden": True,
        "preexisting_boundary_artifact_forbidden": True,
        "exact_persisted_lease_required_before_outcome": True,
        "temporary_cleanup_required": True,
        "lease_bound_host_invoker_enforced": False,
        "final_execution_acknowledged": False,
        "one_shot_engineering_invocation_permitted": False,
        "runtime_execution_performed": False,
        "docker_run_performed": False,
        "local_compute_execution_open": False,
    }
    for field, expected in exact_implementation.items():
        if implementation.get(field) != expected:
            raise RuntimeError(f"implementation record differs: {field}")
    digest = implementation.get("implementation_sha256")
    if not isinstance(digest, str) or _SHA256.fullmatch(digest) is None:
        raise RuntimeError("implementation semantic digest is invalid")
    if digest != _semantic_sha256(implementation, "implementation_sha256"):
        raise RuntimeError("implementation semantic digest differs")

    exact_merge: dict[str, object] = {
        "schema_version": 1,
        "receipt_id": (
            "stage3b-qwake-lc4-e-persistent-evidence-chain-v2-"
            "authoring-post-merge-validation-v1"
        ),
        "pr_number": AUTHORING_PR_NUMBER,
        "head_commit": AUTHORING_HEAD_COMMIT,
        "base_commit": AUTHORING_PARENT_COMMIT,
        "merge_commit": AUTHORING_MERGE_COMMIT,
        "merged_at_utc": AUTHORING_MERGED_AT_UTC,
        "commit_count": 1,
        "file_count": 18,
        "focused_tests_passed": 15,
        "targeted_tests_passed": 216,
        "full_tests_passed": 1263,
        "full_test_warnings": 14,
        "ruff_passed": True,
        "mypy_passed": True,
        "ru_mkdocs_passed": True,
        "en_mkdocs_passed": True,
        "runtime_boundary_closed": True,
    }
    for field, expected in exact_merge.items():
        if merge.get(field) != expected:
            raise RuntimeError(f"authoring merge receipt differs: {field}")
    receipt_sha256 = merge.get("receipt_sha256")
    if not isinstance(receipt_sha256, str) or _SHA256.fullmatch(receipt_sha256) is None:
        raise RuntimeError("authoring merge receipt digest is invalid")
    if receipt_sha256 != _semantic_sha256(merge, "receipt_sha256"):
        raise RuntimeError("authoring merge receipt digest differs")


def _verify_static_boundary(root: Path) -> None:
    module = root / IMPLEMENTATION_MODULE_RELATIVE
    tree = ast.parse(module.read_text(encoding="utf-8", errors="strict"))
    forbidden_imports = {
        "docker",
        "multiprocessing",
        "subprocess",
        "torch",
    }
    forbidden_calls = {
        "Popen",
        "call",
        "check_call",
        "check_output",
        "execv",
        "execve",
        "fork",
        "run",
        "spawn",
        "system",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".", 1)[0] in forbidden_imports:
                    raise RuntimeError("implementation imports execution dependency")
        if (
            isinstance(node, ast.ImportFrom)
            and node.module is not None
            and node.module.split(".", 1)[0] in forbidden_imports
        ):
            raise RuntimeError("implementation imports execution dependency")
        if isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name) and function.id in forbidden_calls:
                raise RuntimeError("implementation contains execution call")
            if isinstance(function, ast.Attribute) and function.attr in forbidden_calls:
                raise RuntimeError("implementation contains execution call")


def _verify_runtime_boundary(root: Path) -> None:
    chain = verify_persistent_evidence_chain_v2(root)
    output_root = root / chain.source.output_root
    paths = (
        output_root,
        root / LEGACY_EXECUTION_LEASE_RELATIVE,
        root / EXECUTION_LEASE_V2_RELATIVE,
        root / DURABLE_HOST_OUTCOME_RELATIVE,
    )
    for path in paths:
        if os.path.lexists(path):
            raise RuntimeError(f"runtime boundary artifact exists: {path}")


def main() -> int:
    args = parse_args()
    root = args.project_root.expanduser().resolve()
    chain = verify_persistent_evidence_chain_v2(root)
    implementation, merge = _verify_package(root)
    _verify_records(implementation, merge, chain.chain_sha256)
    _verify_static_boundary(root)
    _verify_runtime_boundary(root)

    print("OK: QW-LC4-E persistent evidence chain v2 implementation verified")
    print(
        "PERSISTENT_EVIDENCE_CHAIN_V2_IMPLEMENTATION_ID="
        f"{PERSISTENT_EVIDENCE_CHAIN_V2_IMPLEMENTATION_ID}"
    )
    print(
        "PERSISTENT_EVIDENCE_CHAIN_V2_IMPLEMENTATION_SHA256="
        f"{implementation['implementation_sha256']}"
    )
    print(f"AUTHORING_MERGE_COMMIT={AUTHORING_MERGE_COMMIT}")
    print("PERSISTENT_LEASE_V2_IMPLEMENTATION_PRESENT=true")
    print("DURABLE_OUTCOME_WRITER_IMPLEMENTED=true")
    print("EXCLUSIVE_NO_OVERWRITE_ENFORCED=true")
    print("FILE_AND_DIRECTORY_FSYNC_REQUIRED=true")
    print("SYMBOLIC_PARENT_FORBIDDEN=true")
    print("EXACT_PERSISTED_LEASE_REQUIRED_BEFORE_OUTCOME=true")
    print("LEASE_BOUND_HOST_INVOKER_ENFORCED=false")
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
