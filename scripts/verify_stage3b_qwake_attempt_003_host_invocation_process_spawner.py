#!/usr/bin/env python3
"""Verify Attempt-003 host process-spawner implementation authoring.

The verifier is read-only. It validates the implementation contract, frozen
authoring package, exact prior command-materialization dependencies, immutable
authorization, and the already-reconciled durable command record. It never
calls the executable spawn function.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
from typing import cast

import torch2pc_thesis.stage3b_qwake_attempt_003_host_invocation_process_spawner as spawner

AUTHORING_ROOT = Path(
    "experiments/frozen/"
    "stage3b-qwake-attempt-003-host-invocation-process-spawner-v1"
)
AUTHORING_FILES = {
    "SHA256SUMS",
    "authoring.json",
    "contract.json",
    "source-SHA256SUMS",
}
MODULE = Path(
    "src/torch2pc_thesis/"
    "stage3b_qwake_attempt_003_host_invocation_process_spawner.py"
)
VERIFIER = Path(
    "scripts/verify_stage3b_qwake_attempt_003_host_invocation_process_spawner.py"
)
TEST = Path(
    "tests/unit/"
    "test_stage3b_qwake_attempt_003_host_invocation_process_spawner.py"
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

COMMAND_PACKAGE = Path(
    "experiments/frozen/"
    "stage3b-qwake-attempt-003-host-invocation-command-materialization-authoring-v1"
)
COMMAND_DEPENDENCY_SHA256 = {
    (COMMAND_PACKAGE / "SHA256SUMS").as_posix():
        "4ee21a9430cd41c20c71fd8216a8180d69be12b131432c42efb387280def9511",
    (COMMAND_PACKAGE / "authoring.json").as_posix():
        "845c0fd9c86e056679c573f58e7abd55e59619b29e6061bfb9e7d1485c0b2d43",
    (COMMAND_PACKAGE / "contract.json").as_posix():
        "525bb4769cc8d4e991f2e72993f2fdacd000d1d7512690536df13fde0386ccf5",
    (COMMAND_PACKAGE / "source-SHA256SUMS").as_posix():
        "e3f78fcace40e8219d667996d5027db046bbb0f3a28c7db06c5ee30886dc8bbf",
    "src/torch2pc_thesis/stage3b_qwake_attempt_003_host_invocation_command_materialization.py":
        "134eec13d37667b2ca779f50a4c99a8f283b59b2fbfc36dedd765f5ce1c3c990",
}

LANGUAGE_ROW = (
    "docs/decisions/"
    "ADR-118-stage3b-qwake-attempt-003-host-invocation-process-spawner-authoring.md,"
    "docs/decisions/"
    "ADR-118-stage3b-qwake-attempt-003-host-invocation-process-spawner-authoring_EN.md,"
    "required"
)


class VerificationError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise VerificationError(f"regular file absent: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VerificationError(f"JSON invalid: {path}") from exc
    if not isinstance(value, dict):
        raise VerificationError(f"JSON object expected: {path}")
    return cast(dict[str, object], value)


def verify_registry(
    registry: Path,
    base: Path,
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
        if sha256_file(base / name) != expected:
            raise VerificationError(f"registry digest differs: {name}")


def verify_authorization(root: Path) -> None:
    for relative, expected in AUTH_FILE_SHA256.items():
        if sha256_file(root / relative) != expected:
            raise VerificationError(f"authorization file differs: {relative}")
    authorization = read_json(root / AUTH_ROOT / "authorization.json")
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


def verify_implementation_ast(root: Path) -> None:
    source = (root / MODULE).read_text(encoding="utf-8")
    tree = ast.parse(source)

    subprocess_imports = 0
    popen_calls: list[ast.Call] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            subprocess_imports += sum(
                1 for alias in node.names if alias.name == "subprocess"
            )
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "subprocess"
            and node.func.attr == "Popen"
        ):
            popen_calls.append(node)

    if subprocess_imports != 1:
        raise VerificationError("subprocess import count differs")
    if len(popen_calls) != 1:
        raise VerificationError("subprocess.Popen call count differs")

    keywords = {item.arg: item.value for item in popen_calls[0].keywords}
    required_false = ("shell",)
    required_true = ("start_new_session", "close_fds")
    for name in required_false:
        value = keywords.get(name)
        if not isinstance(value, ast.Constant) or value.value is not False:
            raise VerificationError(f"Popen {name} control differs")
    for name in required_true:
        value = keywords.get(name)
        if not isinstance(value, ast.Constant) or value.value is not True:
            raise VerificationError(f"Popen {name} control differs")

    forbidden = (
        "os.system(",
        "shell=True",
        "subprocess.run(",
        "subprocess.call(",
        "subprocess.check_call(",
        "subprocess.check_output(",
    )
    for marker in forbidden:
        if marker in source:
            raise VerificationError(f"forbidden process surface present: {marker}")


def verify_authoring(
    root: Path,
    execution_root: Path | None,
) -> None:
    verify_authorization(root)

    for relative, expected in COMMAND_DEPENDENCY_SHA256.items():
        if sha256_file(root / relative) != expected:
            raise VerificationError(f"command dependency differs: {relative}")

    package = root / AUTHORING_ROOT
    if not package.is_dir() or package.is_symlink():
        raise VerificationError("authoring package root differs")
    observed_files = {
        path.name
        for path in package.iterdir()
        if path.is_file() and not path.is_symlink()
    }
    if observed_files != AUTHORING_FILES:
        raise VerificationError("authoring package file set differs")

    verify_registry(
        package / "SHA256SUMS",
        package,
        AUTHORING_FILES - {"SHA256SUMS"},
    )

    source_registry = package / "source-SHA256SUMS"
    names = {
        line.partition("  ")[2]
        for line in source_registry.read_text(encoding="utf-8").splitlines()
        if line
    }
    if "" in names:
        raise VerificationError("source registry line malformed")
    verify_registry(source_registry, root, names)

    contract = spawner.load_attempt_003_process_spawner_contract(
        package / "contract.json"
    )
    expected_contract = spawner.build_attempt_003_process_spawner_contract()
    if contract != expected_contract:
        raise VerificationError("process-spawner contract differs")

    authoring = read_json(package / "authoring.json")
    payload = dict(authoring)
    observed_authoring_sha = payload.pop("authoring_sha256", None)
    if observed_authoring_sha != spawner.sha256_object(payload):
        raise VerificationError("authoring semantic SHA differs")

    exact = {
        "schema_version": 1,
        "status": "attempt_003_process_spawner_implemented_not_invoked",
        "authorized_parent_head": spawner.AUTHORIZED_PARENT_HEAD,
        "authorized_parent_tree": spawner.AUTHORIZED_PARENT_TREE,
        "authorized_branch": spawner.AUTHORIZED_BRANCH,
        "command_record_sha256": spawner.COMMAND_RECORD_SHA256,
        "command_record_file_sha256": spawner.COMMAND_RECORD_FILE_SHA256,
        "invocation_sha256": spawner.INVOCATION_SHA256,
        "authoritative_host_command_materialized": True,
        "command_persisted": True,
        "process_spawner_contract_present": True,
        "host_process_spawner_present": True,
        "host_process_spawner_executable": True,
        "host_process_spawned": False,
        "docker_run_implemented": True,
        "docker_run_invoked": False,
        "authorization_used": False,
        "authorization_consumed": False,
        "attempt_started": False,
        "execution_lease_materialized": False,
        "runtime_execution_permitted": False,
        "runtime_execution_started": False,
        "runtime_execution_performed": False,
        "runtime_invoked": False,
        "model_code_invoked": False,
        "dataset_accessed": False,
        "publication_permitted": False,
    }
    for name, expected in exact.items():
        if authoring.get(name) != expected:
            raise VerificationError(f"authoring field differs: {name}")
    if authoring.get("contract_sha256") != contract.get("contract_sha256"):
        raise VerificationError("authoring contract SHA differs")
    if authoring.get("module_sha256") != "sha256:" + sha256_file(root / MODULE):
        raise VerificationError("authoring module SHA differs")
    if authoring.get("verifier_sha256") != "sha256:" + sha256_file(root / VERIFIER):
        raise VerificationError("authoring verifier SHA differs")
    if authoring.get("test_sha256") != "sha256:" + sha256_file(root / TEST):
        raise VerificationError("authoring test SHA differs")

    language_lines = (root / "docs/language-map.csv").read_text(
        encoding="utf-8"
    ).splitlines()
    if language_lines.count(LANGUAGE_ROW) != 1:
        raise VerificationError("ADR-118 language-map row differs")

    verify_implementation_ast(root)

    if execution_root is not None:
        command = spawner.load_persisted_attempt_003_host_command(
            execution_root,
            contract,
        )
        command.require()
        root_execution = execution_root.expanduser().resolve()
        for relative in (
            spawner.OUTPUT_ROOT,
            spawner.LEASE_V1,
            spawner.LEASE_V2,
            spawner.HOST_OUTCOME,
        ):
            if os.path.lexists(root_execution / relative):
                raise VerificationError(
                    f"runtime effect exists during implementation validation: {relative}"
                )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--execution-root", type=Path)
    args = parser.parse_args()
    root = args.project_root.expanduser().resolve()
    verify_authoring(root, args.execution_root)

    contract = spawner.load_attempt_003_process_spawner_contract(
        root / AUTHORING_ROOT / "contract.json"
    )
    print("ATTEMPT_003_PROCESS_SPAWNER_IMPLEMENTATION=true")
    print(f"PROCESS_SPAWNER_CONTRACT_SHA256={contract['contract_sha256']}")
    print(f"COMMAND_RECORD_SHA256={spawner.COMMAND_RECORD_SHA256}")
    print(f"COMMAND_RECORD_FILE_SHA256={spawner.COMMAND_RECORD_FILE_SHA256}")
    print(f"INVOCATION_SHA256={spawner.INVOCATION_SHA256}")
    print("HOST_PROCESS_SPAWNER_PRESENT=true")
    print("HOST_PROCESS_SPAWNER_EXECUTABLE=true")
    print("HOST_PROCESS_SPAWNED=false")
    print("DOCKER_RUN_IMPLEMENTED=true")
    print("DOCKER_RUN_INVOKED=false")
    print("AUTHORIZATION_CONSUMED=false")
    print("ATTEMPT_STARTED=false")
    print("EXECUTION_LEASE_MATERIALIZED=false")
    print("RUNTIME_EXECUTION_PERMITTED=false")
    print("RUNTIME_INVOKED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
