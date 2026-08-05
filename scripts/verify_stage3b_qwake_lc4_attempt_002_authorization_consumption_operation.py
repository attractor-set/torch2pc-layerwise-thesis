#!/usr/bin/env python3
"""Verify the non-executing attempt-002 consumption-operation authoring."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import stat
from pathlib import Path
from typing import Final

from torch2pc_thesis.stage3b_qwake_lc4_attempt_002_authorization_consumption_operation import (
    EXPECTED_AUTHORIZATION_SHA256,
    EXPECTED_HOST_INVOCATION_CHAIN_STATE_SHA256,
    EXPECTED_SCOPE_RECORD_SHA256,
    EXPECTED_TORCH2PC_COMMIT,
    OPERATION_ENTRYPOINT,
    OPERATION_ID,
    OPERATION_STATUS,
    canonical_json,
)

EXPECTED_AUTHORING_BASE_COMMIT: Final = (
    "fbc73df11779c987ae07e823f124130efd696da4"
)
EXPECTED_OPERATION_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-attempt-002-authorization-consumption-operation-v1/"
    "operation.json"
)
EXPECTED_MODULE_RELATIVE: Final = Path(
    "src/torch2pc_thesis/"
    "stage3b_qwake_lc4_attempt_002_authorization_consumption_operation.py"
)
EXPECTED_VERIFIER_RELATIVE: Final = Path(
    "scripts/"
    "verify_stage3b_qwake_lc4_attempt_002_authorization_consumption_operation.py"
)
EXPECTED_TEST_RELATIVE: Final = Path(
    "tests/unit/"
    "test_stage3b_qwake_lc4_attempt_002_authorization_consumption_operation.py"
)
EXPECTED_SCOPE_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-attempt-002-authorization-consumption-"
    "operation-scope-freeze-v1/scope.json"
)
ATTEMPT_001_HASHES: Final = {
    Path(
        "results/stage-3/"
        "qwake-lc4-runtime-validation-v1-attempt-001.execution-lease.json"
    ): "17b28c9f2dfa08f2dc6dd40e7f48c0e495e4237568fe9eeeffdeac8e5dec4532",
    Path(
        "results/stage-3/"
        "qwake-lc4-runtime-validation-v1-attempt-001.execution-lease-v2.json"
    ): "ba4c75158b2494089c64787da271da1f28bd4572bc7c36b356a2c957a8c806f2",
    Path(
        "results/stage-3/"
        "qwake-lc4-runtime-validation-v1-attempt-001.host-outcome.json"
    ): "9004103dd1a54299a8e217422f7b2c36d47f4bca5b9a81dd8f36f99cd9b6cf66",
}
FORBIDDEN_EFFECT_PATHS: Final = (
    Path("results/stage-3/qwake-lc4-runtime-validation-v1-attempt-002"),
    Path(
        "results/stage-3/"
        "qwake-lc4-runtime-validation-v1-attempt-002.execution-lease.json"
    ),
    Path(
        "results/stage-3/"
        "qwake-lc4-runtime-validation-v1-attempt-002.execution-lease-v2.json"
    ),
    Path(
        "results/stage-3/"
        "qwake-lc4-runtime-validation-v1-attempt-002.host-outcome.json"
    ),
)
EXPECTED_ALLOWED_PATHS: Final = (
    "STATUS.md",
    "STATUS_EN.md",
    "docs/decisions/"
    "ADR-117-stage3b-qwake-lc4-e-attempt-002-authorization-consumption-"
    "operation-authoring.md",
    "docs/decisions/"
    "ADR-117-stage3b-qwake-lc4-e-attempt-002-authorization-consumption-"
    "operation-authoring_EN.md",
    "docs/decisions/index.md",
    "docs/decisions/index_EN.md",
    "docs/language-map.csv",
    "docs/qwake-local-compute-extension.md",
    "docs/qwake-local-compute-extension_EN.md",
    "docs/research-log/2026-07.md",
    "docs/research-log/2026-07_EN.md",
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-attempt-002-authorization-consumption-operation-v1/"
    "SHA256SUMS",
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-attempt-002-authorization-consumption-operation-v1/"
    "operation.json",
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-attempt-002-authorization-consumption-operation-v1/"
    "source-SHA256SUMS",
    EXPECTED_VERIFIER_RELATIVE.as_posix(),
    EXPECTED_MODULE_RELATIVE.as_posix(),
    EXPECTED_TEST_RELATIVE.as_posix(),
)
REQUIRED_PROPERTIES: Final = (
    "import_effect_free",
    "production_callsite_absent",
    "operation_entrypoint_not_invoked_by_authoring",
    "authorization_consumption_not_performed_by_authoring",
    "tests_use_isolated_temporary_repositories_only",
    "authorization_package_immutable",
    "attempt_001_terminal_evidence_immutable",
    "no_process_spawn",
    "no_docker_build_or_run",
    "no_runtime_invocation",
    "no_lease_outcome_or_output_creation",
    "fail_closed_on_identity_or_state_mismatch",
    "single_use_consumption_semantics_declared_but_not_executed",
)


class VerificationError(RuntimeError):
    """Raised when the authored operation differs."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _regular_file(root: Path, relative: Path) -> Path:
    path = root / relative
    metadata = path.lstat()
    if path.is_symlink() or not stat.S_ISREG(metadata.st_mode):
        raise VerificationError(f"not an exact regular file: {relative}")
    return path


def _parse_registry(root: Path, relative: Path) -> dict[str, str]:
    path = _regular_file(root, relative)
    records: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        digest, separator, name = line.partition("  ")
        if (
            separator != "  "
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
            or not name
            or name in records
        ):
            raise VerificationError(f"invalid registry line: {relative}")
        records[name] = digest
    return records


def _verify_registry(root: Path, relative: Path) -> dict[str, str]:
    records = _parse_registry(root, relative)
    for name, expected in records.items():
        candidate = _regular_file(root, Path(name))
        if _sha256(candidate) != expected:
            raise VerificationError(f"registry hash mismatch: {name}")
    return records


def _verify_operation_record(
    root: Path,
    operation_relative: Path,
    authoring_base_commit: str,
) -> dict[str, object]:
    path = _regular_file(root, operation_relative)
    record = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(record, dict):
        raise VerificationError("operation record is not an object")

    observed = record.get("operation_sha256")
    reduced = dict(record)
    reduced.pop("operation_sha256", None)
    expected = "sha256:" + hashlib.sha256(
        canonical_json(reduced).encode("utf-8")
    ).hexdigest()
    if observed != expected:
        raise VerificationError("operation self-hash differs")

    source = record.get("source")
    contract = record.get("contract")
    gates = record.get("gates")
    boundary = record.get("boundary")
    next_gate = record.get("next_gate")
    if not all(
        isinstance(item, dict)
        for item in (source, contract, gates, boundary, next_gate)
    ):
        raise VerificationError("operation sections differ")
    assert isinstance(source, dict)
    assert isinstance(contract, dict)
    assert isinstance(gates, dict)
    assert isinstance(boundary, dict)
    assert isinstance(next_gate, dict)

    checks = (
        record.get("schema_version") == 1,
        record.get("operation_id") == OPERATION_ID,
        record.get("status") == OPERATION_STATUS,
        record.get("authoring_base_commit") == authoring_base_commit,
        record.get("authored_at_utc") == "2026-08-05T00:25:00Z",
        source.get("pull_request_number") == 179,
        source.get("scope_freeze_commit") == authoring_base_commit,
        source.get("scope_record_sha256") == EXPECTED_SCOPE_RECORD_SHA256,
        source.get("scope_freeze_post_commit_verified") is True,
        source.get("torch2pc_commit") == EXPECTED_TORCH2PC_COMMIT,
        source.get("authorization_sha256") == EXPECTED_AUTHORIZATION_SHA256,
        source.get("authorization_effective") is True,
        source.get("authorization_consumed") is False,
        source.get("attempt_started") is False,
        source.get("host_invocation_chain_state_sha256")
        == EXPECTED_HOST_INVOCATION_CHAIN_STATE_SHA256,
        contract.get("operation_entrypoint") == OPERATION_ENTRYPOINT,
        contract.get("delegated_transition_call_limit") == 1,
        contract.get("operation_record_is_nonexecuting") is True,
        contract.get("import_effect_free") is True,
        contract.get("production_callsite_absent") is True,
        contract.get("post_commit_verification_required_before_invocation")
        is True,
        contract.get("repository_head_must_equal_operation_commit") is True,
        contract.get("clean_worktree_and_index_required") is True,
        contract.get("claim_materialized_once_inside_operation") is True,
        contract.get("automatic_retry_forbidden") is True,
        contract.get("direct_process_spawn_forbidden") is True,
        contract.get("direct_docker_call_forbidden") is True,
        contract.get("direct_runtime_call_forbidden") is True,
        contract.get("tests_use_temporary_repositories_only") is True,
        gates.get("scope_freeze_post_commit_verified") is True,
        gates.get("operation_authoring_admissible") is True,
        gates.get("operation_authored") is True,
        gates.get("operation_post_commit_verified") is False,
        gates.get("authorization_consumption_permitted") is False,
        gates.get("authorization_consumed") is False,
        gates.get("attempt_started") is False,
        gates.get("production_invocation_permitted") is False,
        gates.get("merge_permitted") is False,
        boundary.get("operation_module_created") is True,
        boundary.get("operation_verifier_created") is True,
        boundary.get("operation_tests_created") is True,
        boundary.get("operation_package_created") is True,
        boundary.get("operation_entrypoint_invoked") is False,
        boundary.get("delegated_transition_invoked") is False,
        boundary.get("authorization_consumed") is False,
        boundary.get("attempt_started") is False,
        boundary.get("output_root_present") is False,
        boundary.get("lease_v1_present") is False,
        boundary.get("lease_v2_present") is False,
        boundary.get("durable_outcome_present") is False,
        boundary.get("process_spawned") is False,
        boundary.get("docker_run_invoked") is False,
        boundary.get("runtime_invoked") is False,
        next_gate.get("operation_authoring_commit_required") is True,
        next_gate.get("operation_post_commit_audit_required") is True,
        next_gate.get("authorization_consumption_permitted") is False,
        next_gate.get("production_invocation_permitted") is False,
        next_gate.get("merge_permitted") is False,
    )
    if not all(checks):
        raise VerificationError("operation record semantics differ")
    return record


def _verify_scope(root: Path, authoring_base_commit: str) -> None:
    scope_path = _regular_file(root, EXPECTED_SCOPE_RELATIVE)
    scope = json.loads(scope_path.read_text(encoding="utf-8"))
    future = scope["future_operation"]
    required = future["required_properties"]
    if scope["source"]["authoring_base_commit"] != (
        "b5b29be5802641287e6e29bb42240ad9e41744b4"
    ):
        raise VerificationError("scope authoring base differs")
    if scope["future_operation"]["future_commit_ordinal"] != 7:
        raise VerificationError("future commit ordinal differs")
    if future["allowed_path_count"] != 17:
        raise VerificationError("allowed path count differs")
    if tuple(future["allowed_paths"]) != EXPECTED_ALLOWED_PATHS:
        raise VerificationError("allowed paths differ")
    if tuple(required) != REQUIRED_PROPERTIES:
        raise VerificationError("required properties differ")
    if authoring_base_commit != EXPECTED_AUTHORING_BASE_COMMIT:
        raise VerificationError("authoring base differs")


def _verify_module_static(root: Path) -> None:
    module = _regular_file(root, EXPECTED_MODULE_RELATIVE)
    tree = ast.parse(module.read_text(encoding="utf-8"))
    forbidden_imports = {"subprocess", "socket", "shutil", "docker"}
    forbidden_calls = {
        "Popen",
        "run",
        "call",
        "check_call",
        "check_output",
        "system",
        "fork",
        "spawn",
        "execv",
        "execve",
    }
    delegated_calls = 0
    entrypoint_found = False

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name.split(".")[0] in forbidden_imports for alias in node.names):
                raise VerificationError("forbidden module import")
        elif isinstance(node, ast.ImportFrom):
            if (
                node.module is not None
                and node.module.split(".")[0] in forbidden_imports
            ):
                raise VerificationError("forbidden from-import")
        elif isinstance(node, ast.FunctionDef):
            if node.name == OPERATION_ENTRYPOINT:
                entrypoint_found = True
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in forbidden_calls:
                    raise VerificationError("forbidden direct effect call")
                if node.func.id == "delegated_transition":
                    delegated_calls += 1
            elif isinstance(node.func, ast.Attribute):
                if node.func.attr in forbidden_calls:
                    raise VerificationError("forbidden direct effect call")

    if not entrypoint_found or delegated_calls != 1:
        raise VerificationError("single delegated call structure differs")

    for base in (root / "src", root / "scripts"):
        for candidate in base.rglob("*.py"):
            relative = candidate.relative_to(root)
            if relative in {
                EXPECTED_MODULE_RELATIVE,
                EXPECTED_VERIFIER_RELATIVE,
            }:
                continue
            if OPERATION_ENTRYPOINT in candidate.read_text(
                encoding="utf-8",
                errors="strict",
            ):
                raise VerificationError(
                    f"production callsite present: {relative}"
                )


def _verify_closed_boundary(root: Path) -> None:
    for relative in FORBIDDEN_EFFECT_PATHS:
        candidate = root / relative
        if candidate.exists() or candidate.is_symlink():
            raise VerificationError(
                f"attempt-002 effect path present: {relative}"
            )
    for relative, expected in ATTEMPT_001_HASHES.items():
        candidate = root / relative
        if not candidate.exists() and not candidate.is_symlink():
            continue
        candidate = _regular_file(root, relative)
        if _sha256(candidate) != expected:
            raise VerificationError(
                f"attempt-001 evidence differs: {relative}"
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--operation",
        type=Path,
        default=EXPECTED_OPERATION_RELATIVE,
    )
    parser.add_argument(
        "--authoring-base-commit",
        default=EXPECTED_AUTHORING_BASE_COMMIT,
    )
    args = parser.parse_args()

    root = args.project_root.resolve(strict=True)
    operation_relative = args.operation
    if operation_relative.is_absolute():
        operation_relative = operation_relative.relative_to(root)

    _verify_scope(root, args.authoring_base_commit)
    record = _verify_operation_record(
        root,
        operation_relative,
        args.authoring_base_commit,
    )
    package_root = operation_relative.parent
    package_records = _verify_registry(
        root,
        package_root / "SHA256SUMS",
    )
    source_records = _verify_registry(
        root,
        package_root / "source-SHA256SUMS",
    )
    expected_package_names = {
        operation_relative.as_posix(),
        (package_root / "source-SHA256SUMS").as_posix(),
    }
    if set(package_records) != expected_package_names:
        raise VerificationError("operation package registry surface differs")
    if EXPECTED_MODULE_RELATIVE.as_posix() not in source_records:
        raise VerificationError("module missing from source registry")
    if EXPECTED_VERIFIER_RELATIVE.as_posix() not in source_records:
        raise VerificationError("verifier missing from source registry")
    if EXPECTED_TEST_RELATIVE.as_posix() not in source_records:
        raise VerificationError("tests missing from source registry")

    _verify_module_static(root)
    _verify_closed_boundary(root)

    print(f"ATTEMPT_002_AUTHORIZATION_CONSUMPTION_OPERATION_ID={record['operation_id']}")
    print(
        "ATTEMPT_002_AUTHORIZATION_CONSUMPTION_OPERATION_SHA256="
        f"{record['operation_sha256']}"
    )
    print(
        "ATTEMPT_002_AUTHORIZATION_CONSUMPTION_OPERATION_SCOPE_FREEZE_"
        "POST_COMMIT_VERIFIED=true"
    )
    print(
        "ATTEMPT_002_AUTHORIZATION_CONSUMPTION_OPERATION_"
        "AUTHORING_ADMISSIBLE=true"
    )
    print(
        "ATTEMPT_002_AUTHORIZATION_CONSUMPTION_OPERATION_AUTHORED=true"
    )
    print(
        "ATTEMPT_002_AUTHORIZATION_CONSUMPTION_OPERATION_"
        "POST_COMMIT_VERIFIED=false"
    )
    print(
        "ATTEMPT_002_AUTHORIZATION_CONSUMPTION_OPERATION_INVOKED=false"
    )
    print("PRODUCTION_CALLSITE_PRESENT=false")
    print("HOST_PROCESS_SPAWNER_PRESENT=false")
    print("DOCKER_RUN_INVOKED=false")
    print("RUNTIME_EXECUTION_STARTED=false")
    print("RUNTIME_EXECUTION_PERFORMED=false")
    print("ATTEMPT_002_AUTHORIZATION_CONSUMED=false")
    print("ATTEMPT_002_ATTEMPT_STARTED=false")
    print("AUTHORIZATION_CONSUMPTION_PERMITTED=false")
    print("ATTEMPT_002_AUTHORIZATION_CONSUMPTION_OPERATION_VERIFIED=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
