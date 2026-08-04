#!/usr/bin/env python3
"""Verify the pure attempt-002 host invocation chain authoring package."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Final, cast

from torch2pc_thesis.stage3b_qwake_lc4_attempt_002_contract import (
    ATTEMPT_002_AUTHORIZATION_ROOT,
    ATTEMPT_002_DURABLE_OUTCOME_RELATIVE,
    ATTEMPT_002_LEASE_V1_RELATIVE,
    ATTEMPT_002_LEASE_V2_RELATIVE,
    ATTEMPT_002_OUTPUT_ROOT,
)
from torch2pc_thesis.stage3b_qwake_lc4_attempt_002_host_invocation_chain import (
    EXPECTED_IMAGE_DIGEST,
    EXPECTED_IMAGE_IDENTITY_SHA256,
    EXPECTED_IMAGE_REPO_DIGEST,
    EXPECTED_SOURCE_COMMIT,
    EXPECTED_TORCH2PC_COMMIT,
    HOST_INVOCATION_CHAIN_ID,
    HOST_INVOCATION_CHAIN_STATUS,
    build_attempt_002_host_invocation_chain_state,
    build_attempt_002_host_invocation_contract,
    canonical_json,
    load_attempt_002_host_image_identity,
    sha256_object,
)

PACKAGE_ROOT: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-attempt-002-host-invocation-chain-v1"
)
AUTHORING_JSON: Final = PACKAGE_ROOT / "authoring.json"
HOST_IMAGE_JSON: Final = PACKAGE_ROOT / "host-image-identity.json"
HOST_CONTRACT_JSON: Final = PACKAGE_ROOT / "host-invocation-contract.json"
IDENTITY_ENV: Final = PACKAGE_ROOT / "identity.env"
PACKAGE_REGISTRY: Final = PACKAGE_ROOT / "SHA256SUMS"
SOURCE_REGISTRY: Final = PACKAGE_ROOT / "source-SHA256SUMS"
MODULE_RELATIVE: Final = Path(
    "src/torch2pc_thesis/"
    "stage3b_qwake_lc4_attempt_002_host_invocation_chain.py"
)
VERIFIER_RELATIVE: Final = Path(
    "scripts/verify_stage3b_qwake_lc4_attempt_002_host_invocation_chain.py"
)
TEST_RELATIVE: Final = Path(
    "tests/unit/test_stage3b_qwake_lc4_attempt_002_host_invocation_chain.py"
)
ADR_RU_RELATIVE: Final = Path(
    "docs/decisions/ADR-114-stage3b-qwake-lc4-e-attempt-002-host-invocation-chain.md"
)
ADR_EN_RELATIVE: Final = Path(
    "docs/decisions/ADR-114-stage3b-qwake-lc4-e-attempt-002-host-invocation-chain_EN.md"
)
FREEZE_EXECUTION_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-attempt-002-execution-freeze-v1/execution.json"
)
FREEZE_IMAGE_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-attempt-002-execution-freeze-v1/image-identity.json"
)
FREEZE_MATERIALIZATION_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-attempt-002-execution-freeze-v1/materialization.json"
)
ATTEMPT_002_CONTRACT_RELATIVE: Final = Path(
    "src/torch2pc_thesis/stage3b_qwake_lc4_attempt_002_contract.py"
)
ATTEMPT_002_ENTRYPOINT_RELATIVE: Final = Path(
    "scripts/run_stage3b_qwake_lc4_attempt_002_authorized_runtime.py"
)

EXPECTED_PACKAGE_FILES: Final = (
    "SHA256SUMS",
    "authoring.json",
    "host-image-identity.json",
    "host-invocation-contract.json",
    "identity.env",
    "source-SHA256SUMS",
)
EXPECTED_PACKAGE_REGISTRY_PATHS: Final = (
    "authoring.json",
    "host-image-identity.json",
    "host-invocation-contract.json",
    "identity.env",
    "source-SHA256SUMS",
)
EXPECTED_SOURCE_PATHS: Final = tuple(
    sorted(
        path.as_posix()
        for path in (
            ADR_RU_RELATIVE,
            ADR_EN_RELATIVE,
            FREEZE_EXECUTION_RELATIVE,
            FREEZE_IMAGE_RELATIVE,
            FREEZE_MATERIALIZATION_RELATIVE,
            ATTEMPT_002_CONTRACT_RELATIVE,
            ATTEMPT_002_ENTRYPOINT_RELATIVE,
            MODULE_RELATIVE,
            VERIFIER_RELATIVE,
            TEST_RELATIVE,
        )
    )
)
EXPECTED_FREEZE_SHA256: Final = (
    "sha256:09ca6e2b70fe1c7352c35d694952b4ea199e85dd816588f29454a4157b711f5c"
)
EXPECTED_CONTRACT_SHA256: Final = (
    "sha256:f3bf69bb52f1b52039d601f9957285f0daa5a4789705243aca23ff88a6942905"
)
EXPECTED_HOST_IMAGE_BINDING_SHA256: Final = (
    "sha256:d6ffa2ac625ba1fe43ed4d14020feeae4fd84c31b4dce5b435e36cd88a1ab68c"
)
EXPECTED_AUTHORING_SHA256: Final = (
    "sha256:dc5a092c322506258466f3da106750d4f0d6d08e3dd10a4225e67b773bd54860"
)
EXPECTED_STATE_SHA256: Final = (
    "sha256:a1a8211d88dbdb65a6ca8dab577dd196e525692ca6570c81392dee18ac7d86e1"
)
EXPECTED_SOURCE_HEAD: Final = "2f346498a28377d355b88560aa099890f829af46"
OLD_IMAGE_DIGEST: Final = (
    "sha256:7da92b8f77f6dc37d42db832c5613ef6149dc488adc5b66465faa33e48ca021d"
)
OLD_ATTEMPT_PATH: Final = (
    "results/stage-3/qwake-lc4-runtime-validation-v1-attempt-001"
)


class Attempt002HostInvocationChainVerificationError(RuntimeError):
    """Raised when host-chain authoring differs from the exact contract."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path("."))
    return parser.parse_args()


def verify(project_root: Path) -> None:
    """Verify the complete pure host chain with all effects closed."""

    root = project_root.expanduser().resolve()
    package = root / PACKAGE_ROOT
    _verify_package_shape(package)
    _verify_registry(
        root / PACKAGE_REGISTRY,
        package,
        EXPECTED_PACKAGE_REGISTRY_PATHS,
    )
    _verify_registry(
        root / SOURCE_REGISTRY,
        root,
        EXPECTED_SOURCE_PATHS,
    )

    contract = build_attempt_002_host_invocation_contract(root)
    if contract.contract_sha256 != EXPECTED_CONTRACT_SHA256:
        raise Attempt002HostInvocationChainVerificationError(
            "host invocation contract semantic digest differs"
        )
    contract_bytes = (root / HOST_CONTRACT_JSON).read_bytes()
    if contract_bytes != contract.canonical_json().encode("utf-8"):
        raise Attempt002HostInvocationChainVerificationError(
            "host invocation contract record differs"
        )

    image_identity = load_attempt_002_host_image_identity(root)
    host_image = _read_json(root / HOST_IMAGE_JSON)
    _verify_host_image_binding(host_image, image_identity.identity_sha256)

    state = build_attempt_002_host_invocation_chain_state(root)
    if state.state_sha256 != EXPECTED_STATE_SHA256:
        raise Attempt002HostInvocationChainVerificationError(
            "host invocation chain state digest differs"
        )
    authoring = _read_json(root / AUTHORING_JSON)
    _verify_authoring(authoring, state.contract_sha256)

    identity_env = _read_identity_env(root / IDENTITY_ENV)
    _verify_identity_env(identity_env)
    _verify_source_ast(root / MODULE_RELATIVE)
    _verify_package_text(package, root)
    _verify_effect_boundary(root)

    print(f"HOST_INVOCATION_CHAIN_ID={HOST_INVOCATION_CHAIN_ID}")
    print(f"HOST_INVOCATION_CONTRACT_SHA256={contract.contract_sha256}")
    print(f"HOST_INVOCATION_CHAIN_STATE_SHA256={state.state_sha256}")
    print("HOST_IMAGE_IDENTITY_PRESENT=true")
    print("HOST_COMMAND_MATERIALIZATION_PRESENT=true")
    print("HOST_PROCESS_SPAWNER_PRESENT=false")
    print("DOCKER_RUN_IMPLEMENTED=false")
    print("DOCKER_RUN_INVOKED=false")
    print("ATTEMPT_002_AUTHORIZATION_AUTHORING_ADMISSIBLE=true")
    print("ATTEMPT_002_AUTHORIZATION_ISSUED=false")
    print("ATTEMPT_002_AUTHORIZATION_CONSUMED=false")
    print("ATTEMPT_002_LEASE_V1_PRESENT=false")
    print("ATTEMPT_002_LEASE_V2_PRESENT=false")
    print("ATTEMPT_002_DURABLE_OUTCOME_PRESENT=false")
    print("RUNTIME_EXECUTION_STARTED=false")
    print("RUNTIME_EXECUTION_PERFORMED=false")
    print("HOST_INVOCATION_CHAIN_VERIFIED=true")


def _verify_package_shape(package: Path) -> None:
    if not package.is_dir() or package.is_symlink():
        raise Attempt002HostInvocationChainVerificationError(
            "host invocation package directory differs"
        )
    observed = tuple(
        sorted(
            entry.name
            for entry in package.iterdir()
            if entry.is_file() and not entry.is_symlink()
        )
    )
    if observed != EXPECTED_PACKAGE_FILES:
        raise Attempt002HostInvocationChainVerificationError(
            "host invocation package file set differs"
        )
    if any(entry.is_symlink() for entry in package.iterdir()):
        raise Attempt002HostInvocationChainVerificationError(
            "host invocation package contains a symlink"
        )


def _verify_host_image_binding(
    record: Mapping[str, object],
    source_identity_sha256: str,
) -> None:
    exact: Mapping[str, object] = {
        "schema_version": 1,
        "record_id": (
            "stage3b-qwake-lc4-e-attempt-002-host-image-binding-v1"
        ),
        "status": (
            "corrected_image_identity_bound_to_pure_host_invocation_chain"
        ),
        "source_image_identity_sha256": source_identity_sha256,
        "execution_freeze_sha256": EXPECTED_FREEZE_SHA256,
        "source_commit": EXPECTED_SOURCE_COMMIT,
        "torch2pc_commit": EXPECTED_TORCH2PC_COMMIT,
        "image_digest": EXPECTED_IMAGE_DIGEST,
        "image_repo_digest": EXPECTED_IMAGE_REPO_DIGEST,
        "local_image_inspection_required": True,
        "image_reference_must_use_repo_digest": True,
        "docker_build_invoked": False,
        "docker_run_invoked": False,
        "container_created": False,
        "runtime_execution_started": False,
        "runtime_execution_performed": False,
        "record_sha256": EXPECTED_HOST_IMAGE_BINDING_SHA256,
    }
    for field_name, expected in exact.items():
        if record.get(field_name) != expected:
            raise Attempt002HostInvocationChainVerificationError(
                f"host image binding differs: {field_name}"
            )
    payload = dict(record)
    payload.pop("record_sha256", None)
    if sha256_object(payload) != EXPECTED_HOST_IMAGE_BINDING_SHA256:
        raise Attempt002HostInvocationChainVerificationError(
            "host image binding digest differs"
        )


def _verify_authoring(
    record: Mapping[str, object],
    contract_sha256: str,
) -> None:
    exact: Mapping[str, object] = {
        "schema_version": 1,
        "authoring_id": HOST_INVOCATION_CHAIN_ID,
        "status": HOST_INVOCATION_CHAIN_STATUS,
        "source_head": EXPECTED_SOURCE_HEAD,
        "execution_freeze_sha256": EXPECTED_FREEZE_SHA256,
        "source_image_identity_sha256": EXPECTED_IMAGE_IDENTITY_SHA256,
        "host_image_binding_sha256": EXPECTED_HOST_IMAGE_BINDING_SHA256,
        "host_invocation_contract_sha256": contract_sha256,
        "host_image_identity_present": True,
        "host_invocation_contract_present": True,
        "host_command_materialization_present": True,
        "host_process_spawner_present": False,
        "docker_run_implemented": False,
        "authorization_authoring_admissible": True,
        "authorization_issued": False,
        "authorization_consumed": False,
        "lease_v1_present": False,
        "lease_v2_present": False,
        "durable_outcome_present": False,
        "runtime_execution_started": False,
        "runtime_execution_performed": False,
        "scientific_execution_open": False,
        "test_dataset_access": False,
        "publication_permitted": False,
        "authoring_sha256": EXPECTED_AUTHORING_SHA256,
    }
    for field_name, expected in exact.items():
        if record.get(field_name) != expected:
            raise Attempt002HostInvocationChainVerificationError(
                f"host invocation authoring differs: {field_name}"
            )
    payload = dict(record)
    payload.pop("authoring_sha256", None)
    if sha256_object(payload) != EXPECTED_AUTHORING_SHA256:
        raise Attempt002HostInvocationChainVerificationError(
            "host invocation authoring digest differs"
        )


def _verify_identity_env(identity: Mapping[str, str]) -> None:
    exact = {
        "AUTHORING_ID": HOST_INVOCATION_CHAIN_ID,
        "AUTHORING_SHA256": EXPECTED_AUTHORING_SHA256,
        "SOURCE_HEAD": EXPECTED_SOURCE_HEAD,
        "EXECUTION_FREEZE_SHA256": EXPECTED_FREEZE_SHA256,
        "SOURCE_IMAGE_IDENTITY_SHA256": EXPECTED_IMAGE_IDENTITY_SHA256,
        "HOST_IMAGE_BINDING_SHA256": EXPECTED_HOST_IMAGE_BINDING_SHA256,
        "HOST_INVOCATION_CONTRACT_SHA256": EXPECTED_CONTRACT_SHA256,
        "IMAGE_DIGEST": EXPECTED_IMAGE_DIGEST,
        "IMAGE_REPO_DIGEST": EXPECTED_IMAGE_REPO_DIGEST,
        "HOST_IMAGE_IDENTITY_PRESENT": "true",
        "HOST_INVOCATION_CONTRACT_PRESENT": "true",
        "HOST_COMMAND_MATERIALIZATION_PRESENT": "true",
        "HOST_PROCESS_SPAWNER_PRESENT": "false",
        "DOCKER_BUILD_INVOKED": "false",
        "DOCKER_RUN_IMPLEMENTED": "false",
        "DOCKER_RUN_INVOKED": "false",
        "CONTAINER_CREATED": "false",
        "ATTEMPT_002_AUTHORIZATION_AUTHORING_ADMISSIBLE": "true",
        "ATTEMPT_002_AUTHORIZATION_ISSUED": "false",
        "ATTEMPT_002_AUTHORIZATION_CONSUMED": "false",
        "ATTEMPT_002_LEASE_V1_PRESENT": "false",
        "ATTEMPT_002_LEASE_V2_PRESENT": "false",
        "ATTEMPT_002_DURABLE_OUTCOME_PRESENT": "false",
        "RUNTIME_EXECUTION_STARTED": "false",
        "RUNTIME_EXECUTION_PERFORMED": "false",
        "SCIENTIFIC_EXECUTION_OPEN": "false",
        "TEST_DATASET_ACCESS": "false",
        "PUBLICATION_PERMITTED": "false",
    }
    if dict(identity) != exact:
        raise Attempt002HostInvocationChainVerificationError(
            "host invocation identity.env differs"
        )


def _verify_source_ast(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    forbidden_imports = {"subprocess", "shlex", "signal", "threading"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".", 1)[0] in forbidden_imports:
                    raise Attempt002HostInvocationChainVerificationError(
                        f"host chain imports executable surface: {alias.name}"
                    )
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module.split(".", 1)[0] in forbidden_imports:
                raise Attempt002HostInvocationChainVerificationError(
                    f"host chain imports executable surface: {module}"
                )
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in {"Popen", "run", "call", "check_call"}
        ):
            raise Attempt002HostInvocationChainVerificationError(
                f"host chain contains process call: {node.func.attr}"
            )
    if "shell=True" in source or "os.system" in source:
        raise Attempt002HostInvocationChainVerificationError(
            "host chain contains shell execution"
        )


def _verify_package_text(package: Path, root: Path) -> None:
    text = "\n".join(
        entry.read_text(encoding="utf-8")
        for entry in package.iterdir()
        if entry.is_file() and entry.suffix in {".json", ".env"}
    )
    if OLD_IMAGE_DIGEST in text or OLD_ATTEMPT_PATH in text:
        raise Attempt002HostInvocationChainVerificationError(
            "historical attempt identity leaked into host chain"
        )
    if str(root) in text or "/home/" in text:
        raise Attempt002HostInvocationChainVerificationError(
            "host absolute path leaked into host chain"
        )


def _verify_effect_boundary(root: Path) -> None:
    for relative in (
        ATTEMPT_002_AUTHORIZATION_ROOT,
        ATTEMPT_002_OUTPUT_ROOT,
        ATTEMPT_002_LEASE_V1_RELATIVE,
        ATTEMPT_002_LEASE_V2_RELATIVE,
        ATTEMPT_002_DURABLE_OUTCOME_RELATIVE,
    ):
        if os.path.lexists(root / relative):
            raise Attempt002HostInvocationChainVerificationError(
                f"attempt-002 effect already exists: {relative}"
            )


def _verify_registry(
    registry_path: Path,
    base: Path,
    expected_paths: Sequence[str],
) -> None:
    if not registry_path.is_file() or registry_path.is_symlink():
        raise Attempt002HostInvocationChainVerificationError(
            f"registry differs: {registry_path}"
        )
    observed: list[str] = []
    for line in registry_path.read_text(encoding="utf-8").splitlines():
        digest, separator, relative = line.partition("  ")
        if separator != "  " or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise Attempt002HostInvocationChainVerificationError(
                f"registry line differs: {registry_path}"
            )
        target = (base / relative).resolve()
        try:
            target.relative_to(base.resolve())
        except ValueError as exc:
            raise Attempt002HostInvocationChainVerificationError(
                f"registry path leaves base: {relative}"
            ) from exc
        if not target.is_file() or target.is_symlink():
            raise Attempt002HostInvocationChainVerificationError(
                f"registry target differs: {relative}"
            )
        if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            raise Attempt002HostInvocationChainVerificationError(
                f"registry target digest differs: {relative}"
            )
        observed.append(relative)
    if tuple(observed) != tuple(expected_paths):
        raise Attempt002HostInvocationChainVerificationError(
            f"registry path set differs: {registry_path}"
        )


def _read_json(path: Path) -> dict[str, object]:
    if not path.is_file() or path.is_symlink():
        raise Attempt002HostInvocationChainVerificationError(
            f"JSON file differs: {path}"
        )
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise Attempt002HostInvocationChainVerificationError(
            f"JSON file is invalid: {path}"
        ) from exc
    if not isinstance(value, dict):
        raise Attempt002HostInvocationChainVerificationError(
            f"JSON root differs: {path}"
        )
    if path.read_bytes() != canonical_json(value).encode("utf-8"):
        raise Attempt002HostInvocationChainVerificationError(
            f"JSON serialization differs: {path}"
        )
    return cast(dict[str, object], value)


def _read_identity_env(path: Path) -> dict[str, str]:
    if not path.is_file() or path.is_symlink():
        raise Attempt002HostInvocationChainVerificationError(
            "identity.env differs"
        )
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        key, separator, value = line.partition("=")
        if separator != "=" or not key or key in result:
            raise Attempt002HostInvocationChainVerificationError(
                "identity.env line differs"
            )
        result[key] = value
    return result


def main() -> int:
    try:
        verify(parse_args().project_root)
    except Attempt002HostInvocationChainVerificationError as exc:
        print(f"ERROR: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
