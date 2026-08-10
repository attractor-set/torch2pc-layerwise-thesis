#!/usr/bin/env python3
"""Verify Attempt-003 host-command materialization authoring.

The verifier is read-only. It validates the frozen authoring package, the prior
authorization/host-chain identities, the preflight evidence, the normalized
command template, and the closed non-execution boundary.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path

from torch2pc_thesis.stage3b_qwake_attempt_003_host_invocation_command_materialization import (
    AUTHORIZATION_SHA256,
    AUTHORIZED_BRANCH,
    AUTHORIZED_PARENT_HEAD,
    COMMAND_TEMPLATE_SHA256,
    CONTRACT_ID,
    CONTRACT_STATUS,
    HOST_INVOCATION_CONTRACT_SHA256,
    PREFLIGHT_CLAIMED_AT_UTC,
    PREFLIGHT_INVOCATION_SHA256,
    build_attempt_003_command_materialization_contract,
    build_preflight_invocation_evidence,
    command_template_sha256,
    load_attempt_003_command_materialization_contract,
    sha256_object,
)

AUTHORING_ID = (
    "stage3b-qwake-attempt-003-host-invocation-command-materialization-authoring-v1"
)
AUTHORING_STATUS = (
    "attempt_003_host_invocation_command_materialization_authored_not_materialized"
)
AUTHORING_ROOT = Path(
    "experiments/frozen/"
    "stage3b-qwake-attempt-003-host-invocation-command-materialization-authoring-v1"
)
AUTHORING_FILES = {
    "SHA256SUMS",
    "authoring.json",
    "contract.json",
    "source-SHA256SUMS",
}

MODULE = Path(
    "src/torch2pc_thesis/"
    "stage3b_qwake_attempt_003_host_invocation_command_materialization.py"
)
VERIFIER = Path(
    "scripts/"
    "verify_stage3b_qwake_attempt_003_host_invocation_command_materialization.py"
)
TEST = Path(
    "tests/unit/"
    "test_stage3b_qwake_attempt_003_host_invocation_command_materialization.py"
)
LANGUAGE_ROW = (
    "docs/decisions/"
    "ADR-117-stage3b-qwake-attempt-003-host-invocation-command-materialization-authoring.md,"
    "docs/decisions/"
    "ADR-117-stage3b-qwake-attempt-003-host-invocation-command-materialization-authoring_EN.md,"
    "required"
)

AUTH_ROOT = Path("experiments/frozen/stage3b-qwake-attempt-003-authorization-v1")
AUTH_FILE_SHA256 = {
    (AUTH_ROOT / "SHA256SUMS").as_posix():
        "06692c7dad5f5e7ee9551006b5951695c9fbb258b0725e2c99576f5154b4cc47",
    (AUTH_ROOT / "authorization.json").as_posix():
        "cc44b8631206ee89202b3e777a06371d2ff9a172cfdbcf747b822c3adb99f48e",
    (AUTH_ROOT / "source-SHA256SUMS").as_posix():
        "b3b3cc21e8443cf49291c5cb2306015e3e0d313c77ec1cb6df3ea62ad5212ef4",
}

HOST_CHAIN_CONTRACT = Path(
    "experiments/frozen/"
    "stage3b-qwake-attempt-003-host-invocation-chain-authoring-v1/contract.json"
)
HOST_CHAIN_CONTRACT_FILE_SHA256 = (
    "5c3b4be4ec01686e8ff3995c9ca4e32eb84dda4308a72ae919896ba624a3198e"
)
HOST_CHAIN_MODULE = Path(
    "src/torch2pc_thesis/stage3b_qwake_attempt_003_host_invocation_chain.py"
)
HOST_CHAIN_MODULE_SHA256 = (
    "19dfa0b73aeedd9e89bfaf7233a4ecdbbed591732618c660060d2ebe4508a990"
)

OUTPUT_ROOT = Path("results/stage-3/qwake-lc4-runtime-validation-v1-attempt-003")
EFFECT_PATHS = (
    OUTPUT_ROOT,
    Path(str(OUTPUT_ROOT) + ".execution-lease.json"),
    Path(str(OUTPUT_ROOT) + ".execution-lease-v2.json"),
    Path(str(OUTPUT_ROOT) + ".host-outcome.json"),
    Path(str(OUTPUT_ROOT) + ".host-invocation-command.json"),
)


class VerificationError(RuntimeError):
    pass


def _sha(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise VerificationError(f"regular file absent: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VerificationError(f"JSON invalid: {path}") from exc
    if not isinstance(value, dict):
        raise VerificationError(f"JSON object expected: {path}")
    return value


def _canonical_sha(value: dict[str, object], field: str) -> str:
    payload = dict(value)
    digest = payload.pop(field, None)
    if not isinstance(digest, str):
        raise VerificationError(f"semantic digest field absent: {field}")
    return sha256_object(payload)


def _verify_registry(
    registry: Path,
    root: Path,
    expected_names: set[str],
) -> None:
    lines = registry.read_text(encoding="utf-8").splitlines()
    observed: dict[str, str] = {}
    for line in lines:
        digest, separator, name = line.partition("  ")
        if not separator or len(digest) != 64:
            raise VerificationError(f"registry line malformed: {registry}")
        if name in observed:
            raise VerificationError(f"duplicate registry path: {name}")
        observed[name] = digest
    if set(observed) != expected_names:
        raise VerificationError(f"registry path set differs: {registry}")
    for name, expected in observed.items():
        if _sha(root / name) != expected:
            raise VerificationError(f"registry digest differs: {name}")


def _verify_closed(root: Path) -> None:
    for relative in EFFECT_PATHS:
        if os.path.lexists(root / relative):
            raise VerificationError(f"Attempt-003 effect exists: {relative}")
    parent = root / OUTPUT_ROOT.parent
    if parent.is_dir() and tuple(parent.glob(f".{OUTPUT_ROOT.name}.staging-*")):
        raise VerificationError("Attempt-003 staging tree exists")


def _verify_authorization(root: Path) -> None:
    for relative, expected in AUTH_FILE_SHA256.items():
        if _sha(root / relative) != expected:
            raise VerificationError(f"authorization file differs: {relative}")
    authorization = _json(root / AUTH_ROOT / "authorization.json")
    if authorization.get("authorization_sha256") != AUTHORIZATION_SHA256:
        raise VerificationError("authorization semantic SHA differs")
    exact = {
        "authorization_effective": True,
        "authorization_consumed": False,
        "attempt_started": False,
        "runtime_execution_started": False,
        "runtime_execution_performed": False,
        "scientific_execution_open": False,
        "test_dataset_access": False,
        "publication_permitted": False,
    }
    for name, expected in exact.items():
        if authorization.get(name) != expected:
            raise VerificationError(f"authorization state differs: {name}")


def _verify_prior_host_chain(root: Path) -> None:
    if _sha(root / HOST_CHAIN_CONTRACT) != HOST_CHAIN_CONTRACT_FILE_SHA256:
        raise VerificationError("prior host-chain contract file differs")
    if _sha(root / HOST_CHAIN_MODULE) != HOST_CHAIN_MODULE_SHA256:
        raise VerificationError("prior host-chain module differs")
    contract = _json(root / HOST_CHAIN_CONTRACT)
    if contract.get("contract_sha256") != HOST_INVOCATION_CONTRACT_SHA256:
        raise VerificationError("prior host-chain semantic SHA differs")
    exact = {
        "host_command_constructor_authored": True,
        "host_command_materialized": False,
        "host_process_spawner_present": False,
        "docker_run_implemented": False,
        "runtime_execution_permitted": False,
        "authorization_consumed": False,
        "attempt_started": False,
        "execution_lease_materialized": False,
        "runtime_execution_started": False,
        "runtime_execution_performed": False,
    }
    for name, expected in exact.items():
        if contract.get(name) != expected:
            raise VerificationError(f"prior host-chain state differs: {name}")


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
                raise VerificationError(
                    f"effectful authoring marker present: {marker}"
                )


def verify_authoring(root: Path) -> None:
    root = root.expanduser().resolve()
    _verify_closed(root)
    _verify_authorization(root)
    _verify_prior_host_chain(root)

    package = root / AUTHORING_ROOT
    if not package.is_dir() or package.is_symlink():
        raise VerificationError("authoring package root differs")
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

    source_registry = package / "source-SHA256SUMS"
    source_names = {
        line.partition("  ")[2]
        for line in source_registry.read_text(encoding="utf-8").splitlines()
        if line
    }
    if "" in source_names:
        raise VerificationError("source registry line malformed")
    _verify_registry(source_registry, root, source_names)

    contract = load_attempt_003_command_materialization_contract(
        package / "contract.json"
    )
    if contract != build_attempt_003_command_materialization_contract():
        raise VerificationError("command-materialization contract differs")
    if contract.get("contract_id") != CONTRACT_ID:
        raise VerificationError("contract id differs")
    if contract.get("status") != CONTRACT_STATUS:
        raise VerificationError("contract status differs")

    preflight = build_preflight_invocation_evidence(contract)
    if preflight.claimed_at_utc != PREFLIGHT_CLAIMED_AT_UTC:
        raise VerificationError("preflight claimed_at differs")
    if preflight.invocation_sha256 != PREFLIGHT_INVOCATION_SHA256:
        raise VerificationError("preflight invocation SHA differs")
    if command_template_sha256(preflight) != COMMAND_TEMPLATE_SHA256:
        raise VerificationError("command template SHA differs")

    authoring = _json(package / "authoring.json")
    if _canonical_sha(authoring, "authoring_sha256") != authoring.get(
        "authoring_sha256"
    ):
        raise VerificationError("authoring semantic digest differs")

    exact = {
        "schema_version": 1,
        "authoring_id": AUTHORING_ID,
        "status": AUTHORING_STATUS,
        "attempt_id": contract["attempt_id"],
        "authorized_parent_head": AUTHORIZED_PARENT_HEAD,
        "authorized_branch": AUTHORIZED_BRANCH,
        "authorization_sha256": AUTHORIZATION_SHA256,
        "authorization_issued": True,
        "authorization_used": False,
        "authorization_consumed": False,
        "attempt_started": False,
        "host_invocation_chain_authored": True,
        "host_command_constructor_authored": True,
        "command_materialization_contract_authored": True,
        "preflight_evidence_bound": True,
        "preflight_claimed_at_authoritative_for_execution": False,
        "preflight_invocation_sha256": PREFLIGHT_INVOCATION_SHA256,
        "command_template_sha256": COMMAND_TEMPLATE_SHA256,
        "authoritative_host_command_materialized": False,
        "command_persisted": False,
        "host_process_spawner_present": False,
        "docker_run_implemented": False,
        "runtime_execution_permitted": False,
        "execution_lease_materialized": False,
        "lease_or_outcome_created": False,
        "runtime_invoked": False,
        "model_code_invoked": False,
        "dataset_accessed": False,
        "repository_authoring_performed": True,
        "language_map_semantic_row_authored": True,
        "git_index_modified": False,
        "commit_created": False,
        "push_invoked": False,
        "remote_main_modified": False,
        "contract_id": CONTRACT_ID,
        "contract_sha256": contract["contract_sha256"],
        "module_sha256": "sha256:" + _sha(root / MODULE),
        "verifier_sha256": "sha256:" + _sha(root / VERIFIER),
        "test_sha256": "sha256:" + _sha(root / TEST),
        "post_merge_next_slice": "attempt003_host_invocation_command_materialization",
    }
    for name, expected in exact.items():
        if authoring.get(name) != expected:
            raise VerificationError(f"authoring field differs: {name}")

    lines = (root / "docs/language-map.csv").read_text(
        encoding="utf-8"
    ).splitlines()
    if lines.count(LANGUAGE_ROW) != 1:
        raise VerificationError("ADR-117 language-map row differs")

    _verify_pure_surfaces(root)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.project_root.expanduser().resolve()
    verify_authoring(root)
    contract = load_attempt_003_command_materialization_contract(
        root / AUTHORING_ROOT / "contract.json"
    )

    print("ATTEMPT_003_COMMAND_MATERIALIZATION_AUTHORING=true")
    print(f"COMMAND_MATERIALIZATION_CONTRACT_SHA256={contract['contract_sha256']}")
    print(f"PREFLIGHT_INVOCATION_SHA256={PREFLIGHT_INVOCATION_SHA256}")
    print(f"COMMAND_TEMPLATE_SHA256={COMMAND_TEMPLATE_SHA256}")
    print("PREFLIGHT_CLAIMED_AT_AUTHORITATIVE_FOR_EXECUTION=false")
    print("COMMAND_MATERIALIZATION_CONTRACT_AUTHORED=true")
    print("AUTHORITATIVE_HOST_COMMAND_MATERIALIZED=false")
    print("COMMAND_PERSISTED=false")
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
