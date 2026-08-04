#!/usr/bin/env python3
"""Verify the one-shot attempt-002 authorization without consuming it."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Final, cast

from torch2pc_thesis.stage3b_qwake_lc4_attempt_002_contract import (
    ATTEMPT_002_AUTHORIZATION_ID,
    ATTEMPT_002_AUTHORIZATION_RELATIVE,
    ATTEMPT_002_AUTHORIZATION_ROOT,
    ATTEMPT_002_DURABLE_OUTCOME_RELATIVE,
    ATTEMPT_002_INVOCATION_ACKNOWLEDGEMENT,
    ATTEMPT_002_LEASE_V1_RELATIVE,
    ATTEMPT_002_LEASE_V2_RELATIVE,
    ATTEMPT_002_OUTPUT_ROOT,
    verify_unconsumed_attempt_002_authorization,
)
from torch2pc_thesis.stage3b_qwake_lc4_attempt_002_host_invocation_chain import (
    EXPECTED_FREEZE_SHA256,
    EXPECTED_IMAGE_DIGEST,
    EXPECTED_IMAGE_REPO_DIGEST,
    HOST_INVOCATION_CHAIN_AUTHORIZED_STATUS,
    build_attempt_002_host_invocation_chain_state,
    canonical_json,
    load_attempt_002_host_execution_freeze,
    sha256_object,
)

PACKAGE_ROOT: Final = ATTEMPT_002_AUTHORIZATION_ROOT
AUTHORIZATION_JSON: Final = ATTEMPT_002_AUTHORIZATION_RELATIVE
AUTHORING_JSON: Final = PACKAGE_ROOT / "authoring.json"
IDENTITY_ENV: Final = PACKAGE_ROOT / "identity.env"
PACKAGE_REGISTRY: Final = PACKAGE_ROOT / "SHA256SUMS"
SOURCE_REGISTRY: Final = PACKAGE_ROOT / "source-SHA256SUMS"
MODULE_RELATIVE: Final = Path(
    "src/torch2pc_thesis/"
    "stage3b_qwake_lc4_attempt_002_host_invocation_chain.py"
)
VERIFIER_RELATIVE: Final = Path(
    "scripts/verify_stage3b_qwake_lc4_attempt_002_authorization.py"
)
TEST_RELATIVE: Final = Path(
    "tests/unit/test_stage3b_qwake_lc4_attempt_002_authorization.py"
)
EXPECTED_PACKAGE_FILES: Final = frozenset(
    {
        "SHA256SUMS",
        "authorization.json",
        "authoring.json",
        "identity.env",
        "source-SHA256SUMS",
    }
)
EXPECTED_AUTHORIZATION_SHA256: Final = (
    "sha256:772ebf4a1d142a93e7375a1a2832992f97ab81d8a00c52b87892225afcf1571c"
)
EXPECTED_AUTHORING_SHA256: Final = (
    "sha256:8a70a70fa0696b782a1a6f537629f14540cfb32a33cbaa6d5ad731be2afa43de"
)
EXPECTED_PREAUTHORIZATION_STATE_SHA256: Final = (
    "sha256:a1a8211d88dbdb65a6ca8dab577dd196e525692ca6570c81392dee18ac7d86e1"
)
EXPECTED_POSTAUTHORIZATION_STATE_SHA256: Final = (
    "sha256:5be02c44c300fbbe1f3d289792cbe2e13aa0dd84fbcbe59ee64816ad9350f530"
)
EXPECTED_HOST_CONTRACT_SHA256: Final = (
    "sha256:f3bf69bb52f1b52039d601f9957285f0daa5a4789705243aca23ff88a6942905"
)
EXPECTED_HOST_IMAGE_BINDING_SHA256: Final = (
    "sha256:d6ffa2ac625ba1fe43ed4d14020feeae4fd84c31b4dce5b435e36cd88a1ab68c"
)
EXPECTED_SOURCE_HEAD: Final = "1e9c93882533cafda4891476ea8cf428ac718e7f"
EXPECTED_OPERATOR: Final = "dzmitry-prychyna"


class Attempt002AuthorizationVerificationError(RuntimeError):
    """Raised when authorization authoring does not remain fail closed."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path("."))
    return parser.parse_args()


def verify(project_root: Path) -> None:
    """Verify authorization, provenance, and the closed execution boundary."""

    root = project_root.expanduser().resolve()
    package = root / PACKAGE_ROOT
    _verify_package_shape(package)
    _verify_registry(root / PACKAGE_REGISTRY, package)
    _verify_registry(root / SOURCE_REGISTRY, root)

    freeze = load_attempt_002_host_execution_freeze(root)
    authorization = verify_unconsumed_attempt_002_authorization(root, freeze)
    if authorization.authorization_sha256 != EXPECTED_AUTHORIZATION_SHA256:
        raise Attempt002AuthorizationVerificationError(
            "authorization semantic digest differs"
        )
    authorization_bytes = (root / AUTHORIZATION_JSON).read_bytes()
    if authorization_bytes != authorization.canonical_json().encode("utf-8"):
        raise Attempt002AuthorizationVerificationError(
            "authorization record differs"
        )

    state = build_attempt_002_host_invocation_chain_state(root)
    state.require()
    if state.status != HOST_INVOCATION_CHAIN_AUTHORIZED_STATUS:
        raise Attempt002AuthorizationVerificationError(
            "authorized host-chain status differs"
        )
    if state.state_sha256 != EXPECTED_POSTAUTHORIZATION_STATE_SHA256:
        raise Attempt002AuthorizationVerificationError(
            "authorized host-chain state digest differs"
        )
    if not state.authorization_issued or state.authorization_consumed:
        raise Attempt002AuthorizationVerificationError(
            "authorization state is not issued-unconsumed"
        )

    authoring = _read_json(root / AUTHORING_JSON)
    _verify_authoring(authoring)
    identity = _read_identity_env(root / IDENTITY_ENV)
    _verify_identity(identity)
    _verify_source_ast(root / VERIFIER_RELATIVE)
    _verify_source_ast(root / MODULE_RELATIVE)
    _verify_effect_boundary(root)

    print(f"ATTEMPT_002_AUTHORIZATION_ID={ATTEMPT_002_AUTHORIZATION_ID}")
    print(
        "ATTEMPT_002_AUTHORIZATION_SHA256="
        f"{authorization.authorization_sha256}"
    )
    print(
        "ATTEMPT_002_HOST_INVOCATION_CHAIN_STATE_SHA256="
        f"{state.state_sha256}"
    )
    print("ATTEMPT_002_AUTHORIZATION_EFFECTIVE=true")
    print("ATTEMPT_002_AUTHORIZATION_CONSUMED=false")
    print("ATTEMPT_002_ATTEMPT_STARTED=false")
    print("HOST_PROCESS_SPAWNER_PRESENT=false")
    print("DOCKER_RUN_IMPLEMENTED=false")
    print("RUNTIME_EXECUTION_STARTED=false")
    print("RUNTIME_EXECUTION_PERFORMED=false")
    print("ATTEMPT_002_AUTHORIZATION_VERIFIED=true")


def _verify_authoring(record: Mapping[str, object]) -> None:
    exact: Mapping[str, object] = {
        "schema_version": 1,
        "authoring_id": (
            "stage3b-qwake-lc4-e-attempt-002-"
            "one-shot-authorization-authoring-v1"
        ),
        "status": (
            "one_shot_authorization_authored_unconsumed_"
            "execution_not_started"
        ),
        "source_head": EXPECTED_SOURCE_HEAD,
        "pr_number": 179,
        "authorization_id": ATTEMPT_002_AUTHORIZATION_ID,
        "authorization_sha256": EXPECTED_AUTHORIZATION_SHA256,
        "action_phrase": ATTEMPT_002_INVOCATION_ACKNOWLEDGEMENT,
        "operator_identity_kind": "local-posix-account",
        "operator_identity": EXPECTED_OPERATOR,
        "execution_freeze_sha256": EXPECTED_FREEZE_SHA256,
        "host_invocation_contract_sha256": EXPECTED_HOST_CONTRACT_SHA256,
        "preauthorization_host_invocation_chain_state_sha256": (
            EXPECTED_PREAUTHORIZATION_STATE_SHA256
        ),
        "postauthorization_host_invocation_chain_state_sha256": (
            EXPECTED_POSTAUTHORIZATION_STATE_SHA256
        ),
        "host_image_binding_sha256": EXPECTED_HOST_IMAGE_BINDING_SHA256,
        "image_digest": EXPECTED_IMAGE_DIGEST,
        "image_repo_digest": EXPECTED_IMAGE_REPO_DIGEST,
        "attempt_limit": 1,
        "authorization_effective": True,
        "authorization_consumed": False,
        "post_commit_verification_required_before_consumption": True,
        "authorization_consumption_permitted": False,
        "host_process_spawner_present": False,
        "docker_run_implemented": False,
        "container_created": False,
        "runtime_execution_started": False,
        "runtime_execution_performed": False,
        "automatic_retry_permitted": False,
        "blind_retry_permitted": False,
        "pr_merged": False,
        "qw5_opened": False,
        "authoring_sha256": EXPECTED_AUTHORING_SHA256,
    }
    if dict(record) != dict(exact):
        raise Attempt002AuthorizationVerificationError(
            "authorization authoring envelope differs"
        )
    payload = dict(record)
    payload.pop("authoring_sha256")
    if sha256_object(payload) != EXPECTED_AUTHORING_SHA256:
        raise Attempt002AuthorizationVerificationError(
            "authorization authoring digest differs"
        )


def _verify_identity(identity: Mapping[str, str]) -> None:
    expected = {
        "ATTEMPT_002_AUTHORIZATION_ID": ATTEMPT_002_AUTHORIZATION_ID,
        "ATTEMPT_002_AUTHORIZATION_SHA256": EXPECTED_AUTHORIZATION_SHA256,
        "ATTEMPT_002_AUTHORIZATION_EFFECTIVE": "true",
        "ATTEMPT_002_AUTHORIZATION_CONSUMED": "false",
        "ATTEMPT_002_ATTEMPT_STARTED": "false",
        "ATTEMPT_002_ACTION_PHRASE": ATTEMPT_002_INVOCATION_ACKNOWLEDGEMENT,
        "ATTEMPT_002_OPERATOR_IDENTITY_KIND": "local-posix-account",
        "ATTEMPT_002_OPERATOR_IDENTITY": EXPECTED_OPERATOR,
        "ATTEMPT_002_EXECUTION_COUNT": "1",
        "ATTEMPT_002_FREEZE_SHA256": EXPECTED_FREEZE_SHA256,
        "HOST_INVOCATION_CONTRACT_SHA256": EXPECTED_HOST_CONTRACT_SHA256,
        "PREAUTHORIZATION_HOST_CHAIN_STATE_SHA256": (
            EXPECTED_PREAUTHORIZATION_STATE_SHA256
        ),
        "POSTAUTHORIZATION_HOST_CHAIN_STATE_SHA256": (
            EXPECTED_POSTAUTHORIZATION_STATE_SHA256
        ),
        "HOST_IMAGE_BINDING_SHA256": EXPECTED_HOST_IMAGE_BINDING_SHA256,
        "IMAGE_DIGEST": EXPECTED_IMAGE_DIGEST,
        "IMAGE_REPO_DIGEST": EXPECTED_IMAGE_REPO_DIGEST,
        "SOURCE_HEAD": EXPECTED_SOURCE_HEAD,
        "POST_COMMIT_VERIFICATION_REQUIRED_BEFORE_CONSUMPTION": "true",
        "AUTHORIZATION_CONSUMPTION_PERMITTED": "false",
        "HOST_PROCESS_SPAWNER_PRESENT": "false",
        "DOCKER_RUN_IMPLEMENTED": "false",
        "CONTAINER_CREATED": "false",
        "RUNTIME_EXECUTION_STARTED": "false",
        "RUNTIME_EXECUTION_PERFORMED": "false",
        "AUTOMATIC_RETRY_PERMITTED": "false",
        "BLIND_RETRY_PERMITTED": "false",
        "PR_MERGED": "false",
        "QW5_OPENED": "false",
    }
    if dict(identity) != expected:
        raise Attempt002AuthorizationVerificationError(
            "authorization identity.env differs"
        )


def _verify_effect_boundary(root: Path) -> None:
    for relative in (
        ATTEMPT_002_OUTPUT_ROOT,
        ATTEMPT_002_LEASE_V1_RELATIVE,
        ATTEMPT_002_LEASE_V2_RELATIVE,
        ATTEMPT_002_DURABLE_OUTCOME_RELATIVE,
    ):
        if os.path.lexists(root / relative):
            raise Attempt002AuthorizationVerificationError(
                f"attempt-002 runtime effect exists: {relative}"
            )
    staging = (
        root
        / ATTEMPT_002_OUTPUT_ROOT.parent
        / f".{ATTEMPT_002_OUTPUT_ROOT.name}.staging-*"
    )
    if tuple(staging.parent.glob(staging.name)):
        raise Attempt002AuthorizationVerificationError(
            "attempt-002 staging effect exists"
        )


def _verify_source_ast(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    forbidden_imports = {"subprocess", "shlex", "signal", "threading"}
    forbidden_calls = {"Popen", "run", "call", "check_call", "system"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".", 1)[0] in forbidden_imports:
                    raise Attempt002AuthorizationVerificationError(
                        f"authorization imports executable surface: {alias.name}"
                    )
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module.split(".", 1)[0] in forbidden_imports:
                raise Attempt002AuthorizationVerificationError(
                    f"authorization imports executable surface: {module}"
                )
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in forbidden_calls
        ):
            raise Attempt002AuthorizationVerificationError(
                f"authorization contains process call: {node.func.id}"
            )
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in forbidden_calls
        ):
            raise Attempt002AuthorizationVerificationError(
                f"authorization contains process call: {node.func.attr}"
            )


def _verify_package_shape(package: Path) -> None:
    if not package.is_dir() or package.is_symlink():
        raise Attempt002AuthorizationVerificationError(
            "authorization package differs"
        )
    observed = {
        entry.name
        for entry in package.iterdir()
        if entry.is_file() and not entry.is_symlink()
    }
    nonregular = [
        entry.name
        for entry in package.iterdir()
        if not entry.is_file() or entry.is_symlink()
    ]
    if observed != EXPECTED_PACKAGE_FILES or nonregular:
        raise Attempt002AuthorizationVerificationError(
            "authorization package shape differs"
        )


def _read_json(path: Path) -> dict[str, object]:
    if not path.is_file() or path.is_symlink():
        raise Attempt002AuthorizationVerificationError(
            f"JSON file differs: {path}"
        )
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Attempt002AuthorizationVerificationError(
            f"JSON root differs: {path}"
        )
    if path.read_bytes() != canonical_json(value).encode("utf-8"):
        raise Attempt002AuthorizationVerificationError(
            f"JSON serialization differs: {path}"
        )
    return cast(dict[str, object], value)


def _read_identity_env(path: Path) -> dict[str, str]:
    if not path.is_file() or path.is_symlink():
        raise Attempt002AuthorizationVerificationError(
            "authorization identity.env differs"
        )
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        key, separator, value = line.partition("=")
        if separator != "=" or not key or key in result:
            raise Attempt002AuthorizationVerificationError(
                "authorization identity.env line differs"
            )
        result[key] = value
    return result


def _verify_registry(registry_path: Path, base: Path) -> None:
    if not registry_path.is_file() or registry_path.is_symlink():
        raise Attempt002AuthorizationVerificationError(
            f"registry differs: {registry_path}"
        )
    seen: set[str] = set()
    for line in registry_path.read_text(encoding="utf-8").splitlines():
        digest, separator, relative = line.partition("  ")
        if separator != "  " or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise Attempt002AuthorizationVerificationError(
                f"registry line differs: {registry_path}"
            )
        if relative in seen:
            raise Attempt002AuthorizationVerificationError(
                f"registry duplicate differs: {registry_path}"
            )
        seen.add(relative)
        path = base / relative
        if not path.is_file() or path.is_symlink():
            raise Attempt002AuthorizationVerificationError(
                f"registry source differs: {relative}"
            )
        observed = hashlib.sha256(path.read_bytes()).hexdigest()
        if observed != digest:
            raise Attempt002AuthorizationVerificationError(
                f"registry digest differs: {relative}"
            )


def main() -> int:
    try:
        verify(parse_args().project_root)
    except Attempt002AuthorizationVerificationError as exc:
        print(f"ERROR: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
