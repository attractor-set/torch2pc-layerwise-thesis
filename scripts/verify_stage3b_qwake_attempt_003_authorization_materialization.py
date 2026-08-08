#!/usr/bin/env python3
"""Verify attempt-003 authorization materialization authoring or issuance."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, cast

from torch2pc_thesis.stage3b_qwake_attempt_003_contract import (
    ATTEMPT_003_AUTHORIZATION_ID,
    ATTEMPT_003_AUTHORIZATION_ROOT,
    ATTEMPT_003_AUTHORIZATION_STATUS,
    ATTEMPT_003_DURABLE_OUTCOME_RELATIVE,
    ATTEMPT_003_FREEZE_RELATIVE,
    ATTEMPT_003_ID,
    ATTEMPT_003_INVOCATION_ACKNOWLEDGEMENT,
    ATTEMPT_003_LEASE_V1_RELATIVE,
    ATTEMPT_003_LEASE_V2_RELATIVE,
    ATTEMPT_003_OUTPUT_ROOT,
    Attempt003ExecutionFreeze,
    canonical_json,
    verify_attempt_003_execution_freeze,
    verify_unconsumed_attempt_003_authorization,
)

AUTHORING_ROOT = Path(
    "experiments/frozen/"
    "stage3b-qwake-attempt-003-authorization-materialization-authoring-v1"
)
ADR_RU = Path(
    "docs/decisions/"
    "ADR-115-stage3b-qwake-attempt-003-authorization-materialization-authoring.md"
)
ADR_EN = Path(
    "docs/decisions/"
    "ADR-115-stage3b-qwake-attempt-003-authorization-materialization-authoring_EN.md"
)
MATERIALIZER = Path(
    "scripts/materialize_stage3b_qwake_attempt_003_authorization.py"
)
VERIFIER = Path(
    "scripts/verify_stage3b_qwake_attempt_003_authorization_materialization.py"
)
TEST = Path(
    "tests/unit/test_stage3b_qwake_attempt_003_authorization_materialization.py"
)
LANGUAGE_ROW = f"{ADR_RU.as_posix()},{ADR_EN.as_posix()},required"
EXPECTED_PARENT = "8e1754d1859796bc809c27c078e7b0b180a685ba"
EXPECTED_FREEZE_SHA256 = (
    "sha256:82e7509a0d2627f8b91daa34049307da573619b740a2022b72b922edcd07898e"
)
AUTHORING_FILES = frozenset(
    {"SHA256SUMS", "authoring.json", "contract.json", "source-SHA256SUMS"}
)
AUTHORIZATION_FILES = frozenset(
    {"SHA256SUMS", "authorization.json", "source-SHA256SUMS"}
)
AUTHORIZATION_SOURCE_SHA256 = {
    "experiments/frozen/stage3b-qwake-attempt-003-execution-freeze-v1/execution.json": (
        "sha256:a51f55c62f00dcb643b8c7bd0840762936f710ab53977e9ea4d64b898a9b3b10"
    ),
    "experiments/frozen/stage3b-qwake-attempt-003-execution-freeze-v1/SHA256SUMS": (
        "sha256:b290123eaeb8b2d30b9ae07bcd5f25c6d0ee776c5f3c195ab5243208b2159d0f"
    ),
    (
        "experiments/frozen/stage3b-qwake-attempt-003-execution-freeze-v1/"
        "source-SHA256SUMS"
    ): "sha256:ce9697c3aeb182448bdac072b5d3832eb395340cf5ec61e19440dc139b483ad8",
    "experiments/frozen/stage3b-qwake-lc4-f-runtime-freeze-v1/authorization.json": (
        "sha256:a380cffcfa73cb2dcf984a3cc7de013cb50d79f075677ad5e762417486f06ebd"
    ),
    "scripts/run_stage3b_qwake_attempt_003_authorized_runtime.py": (
        "sha256:daa48a670c8e6d377318f4b8a7a5895ac573b567ef2be1760728df30e1ccc99f"
    ),
    "src/torch2pc_thesis/stage3b_qwake_attempt_003_contract.py": (
        "sha256:dfa27b82bacbc3b1c68b260f555aa1c52bef8aaedc2731f7897d5ed523869ff5"
    ),
    "src/torch2pc_thesis/stage3b_qwake_attempt_003_execution_wrapper.py": (
        "sha256:5c9c4f12a3bfe18de259a127394f9c751b12f9e5275fa88e38e2ab58a592e20d"
    ),
    "src/torch2pc_thesis/stage3b_qwake_attempt_003_runtime_backend.py": (
        "sha256:ea57441bd7683d29e0734cd570d4df65f297ffbbc6c4cd376711a7f660b3a335"
    ),
}


class VerificationError(RuntimeError):
    """Raised when authorization authoring or issuance verification fails."""


def _sha(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise VerificationError(f"regular file absent: {path}")
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise VerificationError(f"JSON file absent: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise VerificationError(f"JSON root not object: {path}")
    return cast(dict[str, Any], value)


def _canonical_sha(value: dict[str, Any], field: str) -> str:
    payload = dict(value)
    payload.pop(field, None)
    return "sha256:" + hashlib.sha256(
        canonical_json(payload).encode("utf-8")
    ).hexdigest()


def _registry(path: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        digest, sep, relative = raw.partition("  ")
        if (
            not sep
            or len(digest) != 64
            or not relative
            or relative in entries
        ):
            raise VerificationError(f"invalid registry: {path}")
        entries[relative] = "sha256:" + digest
    return entries


def _verify_registry(
    path: Path,
    base: Path,
    expected: set[str] | frozenset[str],
) -> None:
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
            raise VerificationError(
                f"attempt-003 effect already exists: {relative}"
            )
    staging_pattern = f".{ATTEMPT_003_OUTPUT_ROOT.name}.staging-*"
    if tuple((root / ATTEMPT_003_OUTPUT_ROOT.parent).glob(staging_pattern)):
        raise VerificationError("attempt-003 output staging already exists")


def _verify_freeze(root: Path) -> Attempt003ExecutionFreeze:
    execution = _json(root / ATTEMPT_003_FREEZE_RELATIVE)
    old = {
        "SOURCE_GIT_COMMIT": os.environ.get("SOURCE_GIT_COMMIT"),
        "EXPERIMENT_IMAGE_DIGEST": os.environ.get("EXPERIMENT_IMAGE_DIGEST"),
        "EXPERIMENT_IMAGE_REPO_DIGEST": os.environ.get(
            "EXPERIMENT_IMAGE_REPO_DIGEST"
        ),
    }
    os.environ["SOURCE_GIT_COMMIT"] = cast(str, execution["source_commit"])
    os.environ["EXPERIMENT_IMAGE_DIGEST"] = cast(str, execution["image_digest"])
    os.environ["EXPERIMENT_IMAGE_REPO_DIGEST"] = cast(
        str,
        execution["image_repo_digest"],
    )
    try:
        freeze = verify_attempt_003_execution_freeze(root)
    finally:
        for name, value in old.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
    if freeze.freeze_sha256 != EXPECTED_FREEZE_SHA256:
        raise VerificationError("attempt-003 execution-freeze identity differs")
    return freeze


def _verify_authoring_package(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
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

    contract = _json(package / "contract.json")
    authoring = _json(package / "authoring.json")
    if _canonical_sha(contract, "contract_sha256") != contract.get(
        "contract_sha256"
    ):
        raise VerificationError("authoring contract digest differs")
    if _canonical_sha(authoring, "authoring_sha256") != authoring.get(
        "authoring_sha256"
    ):
        raise VerificationError("authoring record digest differs")

    contract_exact = {
        "schema_version": 1,
        "contract_id": (
            "stage3b-qwake-attempt-003-authorization-materialization-contract-v1"
        ),
        "attempt_id": ATTEMPT_003_ID,
        "authorized_parent_head": EXPECTED_PARENT,
        "freeze_sha256": EXPECTED_FREEZE_SHA256,
        "authorization_id": ATTEMPT_003_AUTHORIZATION_ID,
        "authorization_status": ATTEMPT_003_AUTHORIZATION_STATUS,
        "action_phrase": ATTEMPT_003_INVOCATION_ACKNOWLEDGEMENT,
        "execution_count": 1,
        "operator_identity_kind": "local-posix-account",
        "operator_identity_bound_at_issuance": True,
        "authorization_effective_on_materialization": True,
        "authorization_consumed": False,
        "attempt_started": False,
        "runtime_execution_started": False,
        "runtime_execution_performed": False,
        "retry_permitted": False,
        "scientific_execution_open": False,
        "test_dataset_access": False,
        "publication_permitted": False,
        "future_authorization_package_file_count": 3,
        "future_authorization_package_files": [
            "SHA256SUMS",
            "authorization.json",
            "source-SHA256SUMS",
        ],
        "no_replace_required": True,
        "atomic_rename_required": True,
        "authorization_materialization_implemented": True,
        "authorization_issued": False,
        "authorization_used": False,
        "lease_or_outcome_created": False,
        "docker_build_invoked": False,
        "docker_run_invoked": False,
        "runtime_invoked": False,
        "model_code_invoked": False,
        "dataset_accessed": False,
        "commit_created": False,
        "push_invoked": False,
        "remote_main_modified": False,
    }
    for name, expected in contract_exact.items():
        if contract.get(name) != expected:
            raise VerificationError(f"authoring contract field differs: {name}")

    if authoring.get("contract_sha256") != contract.get("contract_sha256"):
        raise VerificationError("authoring contract binding differs")
    authoring_exact = {
        "schema_version": 1,
        "authoring_id": (
            "stage3b-qwake-attempt-003-authorization-materialization-authoring-v1"
        ),
        "status": (
            "attempt_003_authorization_materialization_authored_"
            "authorization_not_issued"
        ),
        "attempt_id": ATTEMPT_003_ID,
        "authorized_parent_head": EXPECTED_PARENT,
        "authorized_branch": (
            "research/stage3b-qwake-attempt-003-authorization-"
            "materialization-authoring"
        ),
        "repository_authoring_performed": True,
        "authorization_materialization_implemented": True,
        "authorization_issued": False,
        "authorization_used": False,
        "lease_or_outcome_created": False,
        "runtime_invoked": False,
        "model_code_invoked": False,
        "dataset_accessed": False,
        "git_index_modified": False,
        "commit_created": False,
        "push_invoked": False,
        "remote_main_modified": False,
        "language_map_semantic_row_authored": True,
    }
    for name, expected in authoring_exact.items():
        if authoring.get(name) != expected:
            raise VerificationError(f"authoring record field differs: {name}")

    expected_sources = {
        ADR_RU.as_posix(),
        ADR_EN.as_posix(),
        (AUTHORING_ROOT / "authoring.json").as_posix(),
        (AUTHORING_ROOT / "contract.json").as_posix(),
        MATERIALIZER.as_posix(),
        VERIFIER.as_posix(),
        TEST.as_posix(),
        *AUTHORIZATION_SOURCE_SHA256.keys(),
    }
    _verify_registry(
        package / "source-SHA256SUMS",
        root,
        set(expected_sources),
    )

    rows = (
        root / "docs/language-map.csv"
    ).read_text(encoding="utf-8").splitlines()
    if rows.count(LANGUAGE_ROW) != 1:
        raise VerificationError("ADR-115 language row differs")

    return contract, authoring


def verify_authoring(project_root: Path) -> dict[str, Any]:
    root = project_root.expanduser().resolve()
    _verify_authoring_package(root)
    _verify_freeze(root)
    if os.path.lexists(root / ATTEMPT_003_AUTHORIZATION_ROOT):
        raise VerificationError("attempt-003 authorization unexpectedly exists")
    _closed(root)
    return _json(root / AUTHORING_ROOT / "authoring.json")


def verify_materialized(project_root: Path) -> dict[str, Any]:
    root = project_root.expanduser().resolve()
    _verify_authoring_package(root)
    freeze = _verify_freeze(root)
    package = root / ATTEMPT_003_AUTHORIZATION_ROOT
    observed = {
        path.name
        for path in package.iterdir()
        if path.is_file() and not path.is_symlink()
    }
    if observed != AUTHORIZATION_FILES:
        raise VerificationError("authorization package file set differs")
    _verify_registry(
        package / "SHA256SUMS",
        package,
        AUTHORIZATION_FILES - {"SHA256SUMS"},
    )
    sources = _registry(package / "source-SHA256SUMS")
    if sources != AUTHORIZATION_SOURCE_SHA256:
        raise VerificationError("authorization source registry differs")
    for relative, expected in sources.items():
        if _sha(root / relative) != expected:
            raise VerificationError(
                f"authorization source digest differs: {relative}"
            )
    authorization = verify_unconsumed_attempt_003_authorization(root, freeze)
    _closed(root)
    return cast(dict[str, Any], json.loads(authorization.canonical_json()))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument(
        "--mode",
        choices=("authoring", "materialized"),
        default="authoring",
    )
    args = parser.parse_args()
    if args.mode == "authoring":
        verify_authoring(args.project_root)
        print("ATTEMPT_003_AUTHORIZATION_MATERIALIZATION_AUTHORED=true")
        print("ATTEMPT_003_AUTHORIZATION_ISSUED=false")
    else:
        authorization = verify_materialized(args.project_root)
        print("ATTEMPT_003_AUTHORIZATION_MATERIALIZED=true")
        print(f"AUTHORIZATION_SHA256={authorization['authorization_sha256']}")
        print("ATTEMPT_003_AUTHORIZATION_ISSUED=true")
    print("AUTHORIZATION_USED=false")
    print("EXECUTION_LEASE_MATERIALIZED=false")
    print("RUNTIME_EXECUTION_STARTED=false")
    print("RUNTIME_EXECUTION_PERFORMED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
