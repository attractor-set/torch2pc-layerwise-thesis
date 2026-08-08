#!/usr/bin/env python3
"""Materialize the one-shot attempt-003 authorization without runtime effects."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pwd
import shutil
import tempfile
from pathlib import Path
from typing import Any, cast

from torch2pc_thesis.stage3b_qwake_attempt_003_contract import (
    ATTEMPT_003_AUTHORIZATION_ID,
    ATTEMPT_003_AUTHORIZATION_ROOT,
    ATTEMPT_003_AUTHORIZATION_STATUS,
    ATTEMPT_003_BACKEND_RELATIVE,
    ATTEMPT_003_CONTRACT_RELATIVE,
    ATTEMPT_003_DURABLE_OUTCOME_RELATIVE,
    ATTEMPT_003_ENTRYPOINT_RELATIVE,
    ATTEMPT_003_FREEZE_RELATIVE,
    ATTEMPT_003_FREEZE_ROOT,
    ATTEMPT_003_ID,
    ATTEMPT_003_INVOCATION_ACKNOWLEDGEMENT,
    ATTEMPT_003_LEASE_V1_RELATIVE,
    ATTEMPT_003_LEASE_V2_RELATIVE,
    ATTEMPT_003_OUTPUT_ROOT,
    ATTEMPT_003_WRAPPER_RELATIVE,
    SCIENTIFIC_RUNTIME_AUTHORIZATION_RELATIVE,
    Attempt003Authorization,
    Attempt003ContractError,
    Attempt003ExecutionFreeze,
    canonical_json,
    sha256_object,
    verify_attempt_003_execution_freeze,
    verify_unconsumed_attempt_003_authorization,
)

EXPECTED_FREEZE_SHA256 = (
    "sha256:82e7509a0d2627f8b91daa34049307da573619b740a2022b72b922edcd07898e"
)
PACKAGE_FILES = frozenset(
    {"SHA256SUMS", "authorization.json", "source-SHA256SUMS"}
)
AUTHORIZATION_SOURCE_SHA256 = {
    ATTEMPT_003_FREEZE_RELATIVE.as_posix(): (
        "sha256:a51f55c62f00dcb643b8c7bd0840762936f710ab53977e9ea4d64b898a9b3b10"
    ),
    (ATTEMPT_003_FREEZE_ROOT / "SHA256SUMS").as_posix(): (
        "sha256:b290123eaeb8b2d30b9ae07bcd5f25c6d0ee776c5f3c195ab5243208b2159d0f"
    ),
    (ATTEMPT_003_FREEZE_ROOT / "source-SHA256SUMS").as_posix(): (
        "sha256:ce9697c3aeb182448bdac072b5d3832eb395340cf5ec61e19440dc139b483ad8"
    ),
    SCIENTIFIC_RUNTIME_AUTHORIZATION_RELATIVE.as_posix(): (
        "sha256:a380cffcfa73cb2dcf984a3cc7de013cb50d79f075677ad5e762417486f06ebd"
    ),
    ATTEMPT_003_ENTRYPOINT_RELATIVE.as_posix(): (
        "sha256:daa48a670c8e6d377318f4b8a7a5895ac573b567ef2be1760728df30e1ccc99f"
    ),
    ATTEMPT_003_CONTRACT_RELATIVE.as_posix(): (
        "sha256:dfa27b82bacbc3b1c68b260f555aa1c52bef8aaedc2731f7897d5ed523869ff5"
    ),
    ATTEMPT_003_WRAPPER_RELATIVE.as_posix(): (
        "sha256:5c9c4f12a3bfe18de259a127394f9c751b12f9e5275fa88e38e2ab58a592e20d"
    ),
    ATTEMPT_003_BACKEND_RELATIVE.as_posix(): (
        "sha256:ea57441bd7683d29e0734cd570d4df65f297ffbbc6c4cd376711a7f660b3a335"
    ),
}


class AuthorizationMaterializationError(RuntimeError):
    """Raised when attempt-003 authorization issuance cannot proceed safely."""


def _sha(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise AuthorizationMaterializationError(f"regular file absent: {path}")
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise AuthorizationMaterializationError(f"JSON file absent: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AuthorizationMaterializationError(f"JSON root not object: {path}")
    return cast(dict[str, Any], value)


def _registry(entries: dict[str, str]) -> str:
    return "".join(
        f"{entries[name].removeprefix('sha256:')}  {name}\n"
        for name in sorted(entries)
    )


def _load_registry(path: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        digest, sep, relative = raw.partition("  ")
        if (
            not sep
            or len(digest) != 64
            or not relative
            or relative in entries
        ):
            raise AuthorizationMaterializationError(
                f"invalid registry line: {path}"
            )
        entries[relative] = "sha256:" + digest
    return entries


def _closed(root: Path, *, require_authorization_absent: bool) -> None:
    if require_authorization_absent and os.path.lexists(
        root / ATTEMPT_003_AUTHORIZATION_ROOT
    ):
        raise AuthorizationMaterializationError(
            "attempt-003 authorization destination already exists"
        )
    for relative in (
        ATTEMPT_003_OUTPUT_ROOT,
        ATTEMPT_003_LEASE_V1_RELATIVE,
        ATTEMPT_003_LEASE_V2_RELATIVE,
        ATTEMPT_003_DURABLE_OUTCOME_RELATIVE,
    ):
        if os.path.lexists(root / relative):
            raise AuthorizationMaterializationError(
                f"attempt-003 effect already exists: {relative}"
            )
    staging_pattern = f".{ATTEMPT_003_OUTPUT_ROOT.name}.staging-*"
    if tuple((root / ATTEMPT_003_OUTPUT_ROOT.parent).glob(staging_pattern)):
        raise AuthorizationMaterializationError(
            "attempt-003 output staging already exists"
        )


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
        try:
            freeze = verify_attempt_003_execution_freeze(root)
        except Attempt003ContractError as exc:
            raise AuthorizationMaterializationError(
                "attempt-003 execution-freeze verification failed"
            ) from exc
    finally:
        for name, value in old.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
    if freeze.freeze_sha256 != EXPECTED_FREEZE_SHA256:
        raise AuthorizationMaterializationError(
            "attempt-003 execution-freeze identity differs"
        )
    return freeze


def _verify_authorization_sources(root: Path) -> None:
    for relative, expected in AUTHORIZATION_SOURCE_SHA256.items():
        observed = _sha(root / relative)
        if observed != expected:
            raise AuthorizationMaterializationError(
                f"authorization source identity differs: {relative}"
            )


def _operator_identity() -> str:
    try:
        identity = pwd.getpwuid(os.getuid()).pw_name
    except KeyError as exc:
        raise AuthorizationMaterializationError(
            "current POSIX account cannot be resolved"
        ) from exc
    if not identity:
        raise AuthorizationMaterializationError(
            "current POSIX account identity is empty"
        )
    return identity


def build_authorization(
    freeze: Attempt003ExecutionFreeze,
    *,
    operator_identity: str,
    action_phrase: str,
) -> Attempt003Authorization:
    expected_operator = _operator_identity()
    if operator_identity != expected_operator:
        raise AuthorizationMaterializationError(
            "operator identity differs from current local POSIX account"
        )
    if action_phrase != ATTEMPT_003_INVOCATION_ACKNOWLEDGEMENT:
        raise AuthorizationMaterializationError(
            "attempt-003 authorization action phrase differs"
        )

    payload: dict[str, object] = {
        "schema_version": 1,
        "authorization_id": ATTEMPT_003_AUTHORIZATION_ID,
        "status": ATTEMPT_003_AUTHORIZATION_STATUS,
        "attempt_id": ATTEMPT_003_ID,
        "freeze_sha256": freeze.freeze_sha256,
        "operator_identity_kind": "local-posix-account",
        "operator_identity": operator_identity,
        "action_phrase": action_phrase,
        "execution_count": 1,
        "authorization_effective": True,
        "authorization_consumed": False,
        "attempt_started": False,
        "runtime_execution_started": False,
        "runtime_execution_performed": False,
        "retry_permitted": False,
        "scientific_execution_open": False,
        "test_dataset_access": False,
        "publication_permitted": False,
    }
    authorization = Attempt003Authorization(
        **payload,
        authorization_sha256=sha256_object(payload),
    )
    authorization.require(freeze)
    return authorization


def _verify_staging(
    staging: Path,
    root: Path,
    freeze: Attempt003ExecutionFreeze,
    authorization: Attempt003Authorization,
) -> None:
    observed = {
        path.name
        for path in staging.iterdir()
        if path.is_file() and not path.is_symlink()
    }
    if observed != PACKAGE_FILES or any(
        path.is_symlink() for path in staging.iterdir()
    ):
        raise AuthorizationMaterializationError(
            "authorization staging package file set differs"
        )

    serialized = staging / "authorization.json"
    parsed = _json(serialized)
    if serialized.read_bytes() != canonical_json(parsed).encode("utf-8"):
        raise AuthorizationMaterializationError(
            "authorization JSON serialization differs"
        )
    staged_authorization = Attempt003Authorization(
        **cast(dict[str, Any], parsed)
    )
    staged_authorization.require(freeze)
    if staged_authorization != authorization:
        raise AuthorizationMaterializationError(
            "staged authorization identity differs"
        )

    sources = _load_registry(staging / "source-SHA256SUMS")
    if sources != AUTHORIZATION_SOURCE_SHA256:
        raise AuthorizationMaterializationError(
            "authorization source registry differs"
        )
    for relative, expected in sources.items():
        if _sha(root / relative) != expected:
            raise AuthorizationMaterializationError(
                f"registered authorization source differs: {relative}"
            )

    package = _load_registry(staging / "SHA256SUMS")
    expected_package = {
        "authorization.json": _sha(staging / "authorization.json"),
        "source-SHA256SUMS": _sha(staging / "source-SHA256SUMS"),
    }
    if package != expected_package:
        raise AuthorizationMaterializationError(
            "authorization package registry differs"
        )


def materialize(
    project_root: Path,
    *,
    operator_identity: str,
    action_phrase: str,
) -> Attempt003Authorization:
    root = project_root.expanduser().resolve()
    destination = root / ATTEMPT_003_AUTHORIZATION_ROOT
    if os.path.lexists(destination):
        raise AuthorizationMaterializationError(
            "authorization destination already exists"
        )

    _closed(root, require_authorization_absent=True)
    freeze = _verify_freeze(root)
    _verify_authorization_sources(root)
    authorization = build_authorization(
        freeze,
        operator_identity=operator_identity,
        action_phrase=action_phrase,
    )

    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(
            prefix=f".{destination.name}.staging-",
            dir=destination.parent,
        )
    )
    try:
        (staging / "authorization.json").write_text(
            authorization.canonical_json(),
            encoding="utf-8",
        )
        (staging / "source-SHA256SUMS").write_text(
            _registry(AUTHORIZATION_SOURCE_SHA256),
            encoding="utf-8",
        )
        package_entries = {
            "authorization.json": _sha(staging / "authorization.json"),
            "source-SHA256SUMS": _sha(staging / "source-SHA256SUMS"),
        }
        (staging / "SHA256SUMS").write_text(
            _registry(package_entries),
            encoding="utf-8",
        )
        _verify_staging(staging, root, freeze, authorization)
        staging.rename(destination)
    except BaseException:
        if staging.exists():
            shutil.rmtree(staging)
        raise

    verified = verify_unconsumed_attempt_003_authorization(root, freeze)
    if verified != authorization:
        raise AuthorizationMaterializationError(
            "post-materialization authorization identity differs"
        )
    _closed(root, require_authorization_absent=False)
    return authorization


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--operator-identity", required=True)
    parser.add_argument("--action-phrase", required=True)
    args = parser.parse_args()

    authorization = materialize(
        args.project_root,
        operator_identity=args.operator_identity,
        action_phrase=args.action_phrase,
    )
    print("ATTEMPT_003_AUTHORIZATION_ISSUED=true")
    print(f"AUTHORIZATION_SHA256={authorization.authorization_sha256}")
    print("AUTHORIZATION_USED=false")
    print("EXECUTION_LEASE_MATERIALIZED=false")
    print("RUNTIME_EXECUTION_STARTED=false")
    print("RUNTIME_EXECUTION_PERFORMED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
