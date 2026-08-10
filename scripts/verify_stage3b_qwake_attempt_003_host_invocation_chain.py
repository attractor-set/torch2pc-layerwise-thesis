#!/usr/bin/env python3
"""Verify Attempt-003 host invocation-chain authoring without execution."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
from typing import Any, cast

from torch2pc_thesis.stage3b_qwake_attempt_003_contract import (
    ATTEMPT_003_DURABLE_OUTCOME_RELATIVE,
    ATTEMPT_003_FREEZE_RELATIVE,
    ATTEMPT_003_LEASE_V1_RELATIVE,
    ATTEMPT_003_LEASE_V2_RELATIVE,
    ATTEMPT_003_OUTPUT_ROOT,
    verify_attempt_003_execution_freeze,
    verify_unconsumed_attempt_003_authorization,
)
from torch2pc_thesis.stage3b_qwake_attempt_003_host_invocation_chain import (
    AUTHORIZATION_SHA256,
    AUTHORIZED_PARENT_HEAD,
    FREEZE_SHA256,
    HOST_INVOCATION_CONTRACT_ID,
    HOST_INVOCATION_STATUS,
    build_attempt_003_host_invocation_contract,
    canonical_json,
    load_attempt_003_host_invocation_contract,
)

AUTHORING_ROOT = Path(
    "experiments/frozen/"
    "stage3b-qwake-attempt-003-host-invocation-chain-authoring-v1"
)
ADR_RU = Path(
    "docs/decisions/ADR-116-stage3b-qwake-attempt-003-host-invocation-chain-authoring.md"
)
ADR_EN = Path(
    "docs/decisions/ADR-116-stage3b-qwake-attempt-003-host-invocation-chain-authoring_EN.md"
)
MODULE = Path(
    "src/torch2pc_thesis/stage3b_qwake_attempt_003_host_invocation_chain.py"
)
VERIFIER = Path(
    "scripts/verify_stage3b_qwake_attempt_003_host_invocation_chain.py"
)
TEST = Path(
    "tests/unit/test_stage3b_qwake_attempt_003_host_invocation_chain.py"
)
LANGUAGE_ROW = f"{ADR_RU.as_posix()},{ADR_EN.as_posix()},required"
AUTHORIZED_BRANCH = "research/stage3b-qwake-attempt-003-host-invocation-chain-authoring"
AUTHORING_ID = "stage3b-qwake-attempt-003-host-invocation-chain-authoring-v1"
AUTHORING_STATUS = "attempt_003_host_invocation_chain_authored_execution_not_permitted"

IMPLEMENTATION_RECORD = Path(
    "experiments/frozen/"
    "stage3b-qwake-attempt-003-clean-source-closure-implementation-authoring-v1/"
    "implementation.json"
)
SOURCE_BINDING_CONTRACT = Path(
    "experiments/frozen/"
    "stage3b-qwake-attempt-003-source-binding-execution-freeze-authoring-v1/"
    "contract.json"
)
FREEZE_ROOT = Path("experiments/frozen/stage3b-qwake-attempt-003-execution-freeze-v1")
AUTH_ROOT = Path("experiments/frozen/stage3b-qwake-attempt-003-authorization-v1")
ENTRYPOINT = Path("scripts/run_stage3b_qwake_attempt_003_authorized_runtime.py")
RUNTIME_CONTRACT = Path("src/torch2pc_thesis/stage3b_qwake_attempt_003_contract.py")
WRAPPER = Path("src/torch2pc_thesis/stage3b_qwake_attempt_003_execution_wrapper.py")
BACKEND = Path("src/torch2pc_thesis/stage3b_qwake_attempt_003_runtime_backend.py")

AUTHORING_FILES = frozenset(
    {"SHA256SUMS", "authoring.json", "contract.json", "source-SHA256SUMS"}
)
SOURCE_PATHS = frozenset(
    {
        ADR_RU.as_posix(),
        ADR_EN.as_posix(),
        (AUTHORING_ROOT / "authoring.json").as_posix(),
        (AUTHORING_ROOT / "contract.json").as_posix(),
        IMPLEMENTATION_RECORD.as_posix(),
        SOURCE_BINDING_CONTRACT.as_posix(),
        (FREEZE_ROOT / "SHA256SUMS").as_posix(),
        (FREEZE_ROOT / "execution.json").as_posix(),
        (FREEZE_ROOT / "image-inspection.json").as_posix(),
        (FREEZE_ROOT / "source-SHA256SUMS").as_posix(),
        (AUTH_ROOT / "SHA256SUMS").as_posix(),
        (AUTH_ROOT / "authorization.json").as_posix(),
        (AUTH_ROOT / "source-SHA256SUMS").as_posix(),
        ENTRYPOINT.as_posix(),
        RUNTIME_CONTRACT.as_posix(),
        WRAPPER.as_posix(),
        BACKEND.as_posix(),
        MODULE.as_posix(),
        VERIFIER.as_posix(),
        TEST.as_posix(),
    }
)
IMMUTABLE_SHA256 = {
    IMPLEMENTATION_RECORD.as_posix(): "06ea2a9133cc9c008017e7cc7ca3c38e4d88a6ad6da05a44b361846a335e8342",
    SOURCE_BINDING_CONTRACT.as_posix(): "7b7e6ab40c5a77bb88e1c6ff18fca341fe87df6af7285c7916d8de8c5253d333",
    (FREEZE_ROOT / "SHA256SUMS").as_posix(): "b290123eaeb8b2d30b9ae07bcd5f25c6d0ee776c5f3c195ab5243208b2159d0f",
    (FREEZE_ROOT / "execution.json").as_posix(): "a51f55c62f00dcb643b8c7bd0840762936f710ab53977e9ea4d64b898a9b3b10",
    (FREEZE_ROOT / "image-inspection.json").as_posix(): "6ee5253262dc3bf6c00238b34832386d566b8e12fd503be6eae8fd65586ac6d5",
    (FREEZE_ROOT / "source-SHA256SUMS").as_posix(): "ce9697c3aeb182448bdac072b5d3832eb395340cf5ec61e19440dc139b483ad8",
    (AUTH_ROOT / "SHA256SUMS").as_posix(): "06692c7dad5f5e7ee9551006b5951695c9fbb258b0725e2c99576f5154b4cc47",
    (AUTH_ROOT / "authorization.json").as_posix(): "cc44b8631206ee89202b3e777a06371d2ff9a172cfdbcf747b822c3adb99f48e",
    (AUTH_ROOT / "source-SHA256SUMS").as_posix(): "b3b3cc21e8443cf49291c5cb2306015e3e0d313c77ec1cb6df3ea62ad5212ef4",
    ENTRYPOINT.as_posix(): "daa48a670c8e6d377318f4b8a7a5895ac573b567ef2be1760728df30e1ccc99f",
    RUNTIME_CONTRACT.as_posix(): "dfa27b82bacbc3b1c68b260f555aa1c52bef8aaedc2731f7897d5ed523869ff5",
    WRAPPER.as_posix(): "5c9c4f12a3bfe18de259a127394f9c751b12f9e5275fa88e38e2ab58a592e20d",
    BACKEND.as_posix(): "ea57441bd7683d29e0734cd570d4df65f297ffbbc6c4cd376711a7f660b3a335",
}


class VerificationError(RuntimeError):
    pass


def _sha(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise VerificationError(f"regular file absent: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise VerificationError(f"JSON file absent: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise VerificationError(f"JSON root not object: {path}")
    if path.read_bytes() != canonical_json(value).encode("utf-8"):
        raise VerificationError(f"JSON serialization differs: {path}")
    return cast(dict[str, Any], value)


def _canonical_sha(value: dict[str, Any], field: str) -> str:
    payload = dict(value)
    payload.pop(field, None)
    return "sha256:" + hashlib.sha256(
        canonical_json(payload).encode("utf-8")
    ).hexdigest()


def _registry(path: Path) -> dict[str, str]:
    if not path.is_file() or path.is_symlink():
        raise VerificationError(f"registry absent: {path}")
    entries: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        digest, sep, relative = raw.partition("  ")
        if not sep or len(digest) != 64 or relative in entries or not relative:
            raise VerificationError(f"invalid registry: {path}")
        entries[relative] = digest
    return entries


def _verify_registry(path: Path, base: Path, expected: set[str] | frozenset[str]) -> None:
    entries = _registry(path)
    if set(entries) != set(expected):
        raise VerificationError(f"registry path set differs: {path}")
    for relative, digest in entries.items():
        if _sha(base / relative) != digest:
            raise VerificationError(f"registered digest differs: {relative}")


def _closed(root: Path) -> None:
    for relative in (
        ATTEMPT_003_OUTPUT_ROOT,
        ATTEMPT_003_LEASE_V1_RELATIVE,
        ATTEMPT_003_LEASE_V2_RELATIVE,
        ATTEMPT_003_DURABLE_OUTCOME_RELATIVE,
    ):
        if os.path.lexists(root / relative):
            raise VerificationError(f"attempt-003 effect already exists: {relative}")
    pattern = f".{ATTEMPT_003_OUTPUT_ROOT.name}.staging-*"
    if tuple((root / ATTEMPT_003_OUTPUT_ROOT.parent).glob(pattern)):
        raise VerificationError("attempt-003 staging already exists")


def _verify_unconsumed_authorization(root: Path) -> None:
    execution = _json(root / ATTEMPT_003_FREEZE_RELATIVE)
    old = {
        "SOURCE_GIT_COMMIT": os.environ.get("SOURCE_GIT_COMMIT"),
        "EXPERIMENT_IMAGE_DIGEST": os.environ.get("EXPERIMENT_IMAGE_DIGEST"),
        "EXPERIMENT_IMAGE_REPO_DIGEST": os.environ.get("EXPERIMENT_IMAGE_REPO_DIGEST"),
    }
    os.environ["SOURCE_GIT_COMMIT"] = cast(str, execution["source_commit"])
    os.environ["EXPERIMENT_IMAGE_DIGEST"] = cast(str, execution["image_digest"])
    os.environ["EXPERIMENT_IMAGE_REPO_DIGEST"] = cast(str, execution["image_repo_digest"])
    try:
        freeze = verify_attempt_003_execution_freeze(root)
        authorization = verify_unconsumed_attempt_003_authorization(root, freeze)
    finally:
        for name, value in old.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
    if freeze.freeze_sha256 != FREEZE_SHA256:
        raise VerificationError("execution freeze semantic SHA differs")
    if authorization.authorization_sha256 != AUTHORIZATION_SHA256:
        raise VerificationError("authorization semantic SHA differs")


def _verify_historical_records(root: Path) -> None:
    implementation = _json(root / IMPLEMENTATION_RECORD)
    binding = _json(root / SOURCE_BINDING_CONTRACT)
    if implementation.get("host_invocation_chain_authored") is not False:
        raise VerificationError("historical implementation host-chain state differs")
    if binding.get("host_invocation_chain_authored") is not False:
        raise VerificationError("historical source-binding host-chain state differs")
    if binding.get("future_torch2pc_readonly_mount_required") is not True:
        raise VerificationError("historical Torch2PC readonly-mount requirement differs")


def _verify_pure_surfaces(root: Path) -> None:
    for relative in (MODULE, VERIFIER):
        source = (root / relative).read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import) and any(
                alias.name == "subprocess" for alias in node.names
            ):
                raise VerificationError("process-spawner import is present")
            if isinstance(node, ast.ImportFrom) and node.module == "subprocess":
                raise VerificationError("process-spawner import is present")
        for marker in ("Popen" + "(", "os.system" + "(", "shell" + "=True"):
            if marker in source:
                raise VerificationError(f"effectful authoring marker present: {marker}")


def verify_authoring(root: Path) -> None:
    root = root.expanduser().resolve()
    _closed(root)
    _verify_unconsumed_authorization(root)
    _verify_historical_records(root)

    for relative, expected in IMMUTABLE_SHA256.items():
        if _sha(root / relative) != expected:
            raise VerificationError(f"immutable source differs: {relative}")

    package = root / AUTHORING_ROOT
    observed = {
        path.name
        for path in package.iterdir()
        if path.is_file() and not path.is_symlink()
    }
    if observed != AUTHORING_FILES:
        raise VerificationError("authoring package file set differs")
    _verify_registry(
        package / "SHA256SUMS",
        package,
        AUTHORING_FILES - {"SHA256SUMS"},
    )
    _verify_registry(package / "source-SHA256SUMS", root, SOURCE_PATHS)

    contract = load_attempt_003_host_invocation_contract(package / "contract.json")
    expected_contract = build_attempt_003_host_invocation_contract()
    if contract != expected_contract:
        raise VerificationError("host invocation contract differs from pure builder")
    if contract.contract_id != HOST_INVOCATION_CONTRACT_ID:
        raise VerificationError("host invocation contract id differs")
    if contract.status != HOST_INVOCATION_STATUS:
        raise VerificationError("host invocation contract status differs")

    authoring = _json(package / "authoring.json")
    if _canonical_sha(authoring, "authoring_sha256") != authoring.get("authoring_sha256"):
        raise VerificationError("authoring semantic digest differs")
    exact = {
        "schema_version": 1,
        "authoring_id": AUTHORING_ID,
        "status": AUTHORING_STATUS,
        "attempt_id": contract.attempt_id,
        "authorized_parent_head": AUTHORIZED_PARENT_HEAD,
        "authorized_branch": AUTHORIZED_BRANCH,
        "freeze_sha256": FREEZE_SHA256,
        "authorization_sha256": AUTHORIZATION_SHA256,
        "authorization_issued": True,
        "authorization_used": False,
        "authorization_consumed": False,
        "attempt_started": False,
        "host_invocation_chain_authored": True,
        "host_command_constructor_authored": True,
        "host_command_materialized": False,
        "host_process_spawner_present": False,
        "docker_run_implemented": False,
        "runtime_execution_permitted": False,
        "lease_or_outcome_created": False,
        "runtime_invoked": False,
        "model_code_invoked": False,
        "dataset_accessed": False,
        "historical_records_rewritten": False,
        "repository_authoring_performed": True,
        "language_map_semantic_row_authored": True,
        "git_index_modified": False,
        "commit_created": False,
        "push_invoked": False,
        "remote_main_modified": False,
        "contract_id": HOST_INVOCATION_CONTRACT_ID,
        "contract_sha256": contract.contract_sha256,
        "module_sha256": "sha256:" + _sha(root / MODULE),
        "verifier_sha256": "sha256:" + _sha(root / VERIFIER),
        "test_sha256": "sha256:" + _sha(root / TEST),
        "post_merge_next_slice": "attempt003_host_invocation_command_materialization",
    }
    for name, expected in exact.items():
        if authoring.get(name) != expected:
            raise VerificationError(f"authoring field differs: {name}")

    language_lines = (root / "docs/language-map.csv").read_text(encoding="utf-8").splitlines()
    if language_lines.count(LANGUAGE_ROW) != 1:
        raise VerificationError("ADR-116 language-map row differs")
    _verify_pure_surfaces(root)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.project_root.expanduser().resolve()
    verify_authoring(root)
    contract = load_attempt_003_host_invocation_contract(root / AUTHORING_ROOT / "contract.json")
    print("ATTEMPT_003_HOST_INVOCATION_CHAIN_AUTHORING=true")
    print(f"HOST_INVOCATION_CONTRACT_SHA256={contract.contract_sha256}")
    print("HISTORICAL_IMPLEMENTATION_HOST_INVOCATION_CHAIN_AUTHORED=false")
    print("HISTORICAL_SOURCE_BINDING_HOST_INVOCATION_CHAIN_AUTHORED=false")
    print("HOST_INVOCATION_CHAIN_AUTHORED=true")
    print("HOST_COMMAND_CONSTRUCTOR_AUTHORED=true")
    print("HOST_COMMAND_MATERIALIZED=false")
    print("HOST_PROCESS_SPAWNER_PRESENT=false")
    print("DOCKER_RUN_IMPLEMENTED=false")
    print("AUTHORIZATION_ISSUED=true")
    print("AUTHORIZATION_USED=false")
    print("AUTHORIZATION_CONSUMED=false")
    print("ATTEMPT_STARTED=false")
    print("EXECUTION_LEASE_MATERIALIZED=false")
    print("RUNTIME_EXECUTION_STARTED=false")
    print("RUNTIME_EXECUTION_PERFORMED=false")
    print("RUNTIME_EXECUTION_PERMITTED=false")
    print("MODEL_CODE_INVOKED=false")
    print("DATASET_ACCESSED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
