#!/usr/bin/env python3
"""Verify attempt-003 materialization authoring or future materialized freeze."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, cast

from torch2pc_thesis.stage3b_qwake_attempt_003_contract import (
    ATTEMPT_003_AUTHORIZATION_ROOT,
    ATTEMPT_003_DURABLE_OUTCOME_RELATIVE,
    ATTEMPT_003_FREEZE_ROOT,
    ATTEMPT_003_LEASE_V1_RELATIVE,
    ATTEMPT_003_LEASE_V2_RELATIVE,
    ATTEMPT_003_OUTPUT_ROOT,
    verify_attempt_003_execution_freeze,
)

AUTHORING_ROOT = Path(
    "experiments/frozen/"
    "stage3b-qwake-attempt-003-execution-freeze-materialization-authoring-v1"
)
ADR_RU = Path(
    "docs/decisions/"
    "ADR-114-stage3b-qwake-attempt-003-"
    "execution-freeze-materialization-implementation.md"
)
ADR_EN = Path(
    "docs/decisions/"
    "ADR-114-stage3b-qwake-attempt-003-"
    "execution-freeze-materialization-implementation_EN.md"
)
SOURCE_BINDING = Path(
    "experiments/frozen/"
    "stage3b-qwake-attempt-003-source-binding-execution-freeze-authoring-v1/"
    "contract.json"
)
RUNTIME_REGISTRY = Path(
    "experiments/frozen/"
    "stage3b-qwake-attempt-003-clean-source-closure-implementation-authoring-v1/"
    "runtime-SHA256SUMS"
)
MATERIALIZER = Path(
    "scripts/materialize_stage3b_qwake_attempt_003_execution_freeze.py"
)
VERIFIER = Path(
    "scripts/verify_stage3b_qwake_attempt_003_execution_freeze_materialization.py"
)
TEST = Path(
    "tests/unit/test_stage3b_qwake_attempt_003_execution_freeze_materialization.py"
)
LANGUAGE_ROW = f"{ADR_RU.as_posix()},{ADR_EN.as_posix()},required"
AUTHORING_FILES = frozenset(
    {"SHA256SUMS", "authoring.json", "contract.json", "source-SHA256SUMS"}
)
MATERIALIZED_FILES = frozenset(
    {
        "SHA256SUMS",
        "execution.json",
        "identity.env",
        "image-build.log",
        "image-capture.json",
        "image-inspection.json",
        "materialization.json",
        "source-SHA256SUMS",
        "static-image-validation.json",
    }
)


class VerificationError(RuntimeError):
    pass


def _sha(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise VerificationError(f"regular file absent: {path}")
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise VerificationError(f"JSON root not object: {path}")
    return cast(dict[str, Any], value)


def _canonical_sha(value: dict[str, Any], field: str) -> str:
    payload = dict(value)
    payload.pop(field, None)
    encoded = (
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _registry(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        digest, sep, relative = raw.partition("  ")
        if not sep or len(digest) != 64 or not relative or relative in result:
            raise VerificationError(f"invalid registry: {path}")
        result[relative] = "sha256:" + digest
    return result


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
    forbidden = (
        root / ATTEMPT_003_AUTHORIZATION_ROOT,
        root / ATTEMPT_003_LEASE_V1_RELATIVE,
        root / ATTEMPT_003_LEASE_V2_RELATIVE,
        root / ATTEMPT_003_DURABLE_OUTCOME_RELATIVE,
        root / ATTEMPT_003_OUTPUT_ROOT,
    )
    if any(path.exists() for path in forbidden):
        raise VerificationError("attempt-003 effect boundary open")


def verify_authoring(project_root: Path) -> dict[str, Any]:
    root = project_root.expanduser().resolve()
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
        raise VerificationError("contract digest differs")
    if _canonical_sha(authoring, "authoring_sha256") != authoring.get(
        "authoring_sha256"
    ):
        raise VerificationError("authoring digest differs")

    for name, expected in {
        "source_commit": "541b34a57297d2c5a82851bd846b583d4904fba6",
        "wrapper_commit": "541b34a57297d2c5a82851bd846b583d4904fba6",
        "torch2pc_commit": "b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4",
        "execution_freeze_materialization_implemented": True,
        "execution_freeze_materialized": False,
        "image_built": False,
        "image_identity_materialized": False,
        "authorization_issued": False,
        "authorization_used": False,
        "runtime_invoked": False,
        "dataset_accessed": False,
        "no_replace_required": True,
        "atomic_rename_required": True,
        "future_receipt_file_count": 5,
        "future_materialized_package_file_count": 9,
    }.items():
        if contract.get(name) != expected:
            raise VerificationError(f"contract field differs: {name}")

    for name, expected in {
        "authorized_parent_head": "970303a9e7a947377a7e41dc13accb05972c3931",
        "repository_authoring_performed": True,
        "execution_freeze_materialization_implemented": True,
        "execution_freeze_materialized": False,
        "image_built": False,
        "image_identity_materialized": False,
        "authorization_issued": False,
        "authorization_used": False,
        "runtime_invoked": False,
        "commit_created": False,
        "push_invoked": False,
    }.items():
        if authoring.get(name) != expected:
            raise VerificationError(f"authoring field differs: {name}")

    expected_sources = {
        ADR_RU.as_posix(),
        ADR_EN.as_posix(),
        SOURCE_BINDING.as_posix(),
        RUNTIME_REGISTRY.as_posix(),
        (AUTHORING_ROOT / "authoring.json").as_posix(),
        (AUTHORING_ROOT / "contract.json").as_posix(),
        MATERIALIZER.as_posix(),
        VERIFIER.as_posix(),
        TEST.as_posix(),
    }
    _verify_registry(package / "source-SHA256SUMS", root, expected_sources)
    rows = (root / "docs/language-map.csv").read_text(encoding="utf-8").splitlines()
    if rows.count(LANGUAGE_ROW) != 1:
        raise VerificationError("ADR-114 language row differs")
    if (root / ATTEMPT_003_FREEZE_ROOT).exists():
        raise VerificationError("attempt-003 freeze unexpectedly exists")
    _closed(root)
    return authoring


def verify_materialized(project_root: Path) -> dict[str, Any]:
    root = project_root.expanduser().resolve()
    package = root / ATTEMPT_003_FREEZE_ROOT
    observed = {
        path.name
        for path in package.iterdir()
        if path.is_file() and not path.is_symlink()
    }
    if observed != MATERIALIZED_FILES:
        raise VerificationError("materialized package file set differs")
    _verify_registry(
        package / "SHA256SUMS",
        package,
        MATERIALIZED_FILES - {"SHA256SUMS"},
    )
    execution = _json(package / "execution.json")
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

    manifest = _json(package / "materialization.json")
    if manifest.get("source_commit") != freeze.source_commit:
        raise VerificationError("materialization source differs")
    if manifest.get("image_digest") != freeze.image_digest:
        raise VerificationError("materialization image differs")
    if manifest.get("freeze_sha256") != freeze.freeze_sha256:
        raise VerificationError("materialization freeze identity differs")
    expected_gates = {
        "immutable_execution_image_present": True,
        "execution_freeze_materialized": True,
        "attempt_003_authorization_present": False,
        "execution_lease_materialized": False,
        "durable_outcome_present": False,
        "runtime_execution_started": False,
        "runtime_execution_performed": False,
        "engineering_evidence_present": False,
        "scientific_execution_open": False,
        "test_dataset_access": False,
        "publication_permitted": False,
    }
    if manifest.get("gates") != expected_gates:
        raise VerificationError("materialization gates differ")
    _closed(root)
    return manifest


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
        print("ATTEMPT_003_MATERIALIZATION_IMPLEMENTATION_VERIFIED=true")
        print("IMAGE_BUILT=false")
        print("IMAGE_IDENTITY_MATERIALIZED=false")
        print("EXECUTION_FREEZE_MATERIALIZED=false")
    else:
        verify_materialized(args.project_root)
        print("ATTEMPT_003_EXECUTION_FREEZE_MATERIALIZED=true")
        print("IMAGE_IDENTITY_MATERIALIZED=true")
        print("EXECUTION_FREEZE_MATERIALIZED=true")
    print("AUTHORIZATION_ISSUED=false")
    print("AUTHORIZATION_USED=false")
    print("EXECUTION_LEASE_MATERIALIZED=false")
    print("RUNTIME_EXECUTION_STARTED=false")
    print("RUNTIME_EXECUTION_PERFORMED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
