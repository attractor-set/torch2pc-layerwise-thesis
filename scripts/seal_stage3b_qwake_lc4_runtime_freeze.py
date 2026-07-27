#!/usr/bin/env python3
"""Seal QW-LC4-F identities and receipts without executing the mechanism."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any, cast

from torch2pc_thesis.stage3b_qwake_lc4_runtime_freeze import (
    RUNTIME_FREEZE_ID,
    RUNTIME_OUTPUT_ROOT,
    canonical_json,
    load_runtime_authorization,
    load_runtime_preflight,
    validate_runtime_authorization,
)

SOURCE_FILES = (
    "src/torch2pc_thesis/stage3b_qwake_lc4_bounded.py",
    "src/torch2pc_thesis/stage3b_qwake_lc4_runtime_freeze.py",
    "scripts/preflight_stage3b_qwake_lc4_runtime.py",
    "scripts/authorize_stage3b_qwake_lc4_runtime.py",
    "scripts/seal_stage3b_qwake_lc4_runtime_freeze.py",
    "tests/unit/test_stage3b_qwake_lc4_bounded_implementation.py",
    "tests/unit/test_stage3b_qwake_lc4_runtime_freeze.py",
    "experiments/frozen/stage3b-qwake-lc4-f-runtime-freeze-request-v1/request.json",
    "experiments/frozen/stage3b-qwake-lc4-f-runtime-freeze-request-v1/SHA256SUMS",
    "experiments/frozen/stage3b-qwake-lc4-f-runtime-freeze-authoring-v1/authoring.json",
    "experiments/frozen/stage3b-qwake-lc4-f-runtime-freeze-authoring-v1/SHA256SUMS",
    "experiments/frozen/stage3b-qwake-lc4-i-bounded-implementation-v1/implementation.json",
    "experiments/frozen/stage3b-qwake-lc4-i-bounded-implementation-v1/SHA256SUMS",
    "experiments/frozen/stage3b-qwake-lc3-matched-shadow-validation-contract-v1/contract.json",
    "experiments/frozen/stage3b-qwake-lc3-matched-shadow-validation-contract-v1/SHA256SUMS",
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--torch2pc-dir", type=Path, required=True)
    parser.add_argument("--preflight", type=Path, required=True)
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument("--static-validation-log", type=Path, required=True)
    parser.add_argument("--static-validation-receipt", type=Path, required=True)
    parser.add_argument("--image-build-log", type=Path, required=True)
    parser.add_argument("--materialized-at-utc", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _regular(path: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    if resolved.is_symlink() or not resolved.is_file():
        raise SystemExit(f"{label} must be a regular file: {resolved}")
    return resolved


def _load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SystemExit(f"invalid JSON file: {path}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"JSON root must be an object: {path}")
    return cast(dict[str, Any], value)


def _validate_static_receipt(
    receipt: dict[str, Any],
    *,
    preflight_sha256: str,
    source_commit: str,
    torch2pc_commit: str,
    image_digest: str,
    validation_log_sha256: str,
) -> None:
    expected = {
        "receipt_id": "stage3b-qwake-lc4-static-validation-receipt-v1",
        "schema_version": 1,
        "status": "static_and_unit_validation_passed",
        "all_checks_passed": True,
        "preflight_sha256": preflight_sha256,
        "source_commit": source_commit,
        "torch2pc_commit": torch2pc_commit,
        "image_digest": image_digest,
        "validation_log_sha256": f"sha256:{validation_log_sha256}",
        "runtime_execution_performed": False,
        "engineering_evidence_present": False,
        "scientific_execution_open": False,
        "test_dataset_access": False,
        "publication_permitted": False,
        "image_freeze_permitted": False,
    }
    for key, value in expected.items():
        if receipt.get(key) != value:
            raise SystemExit(f"static validation receipt field differs: {key}")
    checks = receipt.get("checks")
    if not isinstance(checks, list) or not checks:
        raise SystemExit("static validation receipt checks are absent")
    if not all(
        isinstance(item, dict) and item.get("passed") is True
        for item in checks
    ):
        raise SystemExit("static validation receipt contains a failed check")


def main() -> int:
    args = _parser().parse_args()
    root = args.project_root.expanduser().resolve()
    output = args.output_dir.expanduser().resolve()
    if output.exists() or output.is_symlink():
        raise SystemExit(f"refusing to overwrite freeze directory: {output}")

    preflight_path = _regular(args.preflight, "preflight")
    authorization_path = _regular(args.authorization, "authorization")
    static_log = _regular(args.static_validation_log, "static validation log")
    static_receipt_path = _regular(
        args.static_validation_receipt,
        "static validation receipt",
    )
    image_build_log = _regular(args.image_build_log, "image build log")

    preflight = load_runtime_preflight(preflight_path)
    authorization = load_runtime_authorization(authorization_path)
    validate_runtime_authorization(
        authorization,
        preflight,
        root,
        args.torch2pc_dir,
    )
    static_receipt = _load_object(static_receipt_path)
    _validate_static_receipt(
        static_receipt,
        preflight_sha256=preflight.preflight_sha256,
        source_commit=preflight.source_identity.source_commit,
        torch2pc_commit=preflight.source_identity.torch2pc_commit,
        image_digest=preflight.source_identity.image_digest,
        validation_log_sha256=_sha256(static_log),
    )

    output.mkdir(parents=True)
    copies = {
        "preflight.json": preflight_path,
        "authorization.json": authorization_path,
        "static-validation.log": static_log,
        "static-validation-receipt.json": static_receipt_path,
        "image-build.log": image_build_log,
    }
    for name, source in copies.items():
        shutil.copyfile(source, output / name)

    source_entries: list[str] = []
    for relative in SOURCE_FILES:
        path = root / relative
        if path.is_symlink() or not path.is_file():
            raise SystemExit(f"source registry file is absent: {relative}")
        source_entries.append(f"{_sha256(path)}  {relative}")
    (output / "source-SHA256SUMS").write_text(
        "\n".join(source_entries) + "\n",
        encoding="utf-8",
    )

    verification_receipt = {
        "schema_version": 1,
        "receipt_id": "stage3b-qwake-lc4-authorization-verification-receipt-v1",
        "status": "authorization_verified_execution_not_performed",
        "materialized_at_utc": args.materialized_at_utc,
        "preflight_sha256": preflight.preflight_sha256,
        "authorization_sha256": authorization.authorization_sha256,
        "source_identity": preflight.source_identity,
        "authorized_cell_count": len(authorization.cells),
        "output_root": RUNTIME_OUTPUT_ROOT.as_posix(),
        "runtime_execution_permitted": True,
        "runtime_execution_performed": False,
        "engineering_evidence_present": False,
        "scientific_execution_open": False,
        "test_dataset_access": False,
        "publication_permitted": False,
        "image_freeze_permitted": False,
    }
    (output / "authorization-verification-receipt.json").write_text(
        canonical_json(verification_receipt),
        encoding="utf-8",
    )

    identity_lines = (
        f"SOURCE_COMMIT={preflight.source_identity.source_commit}\n"
        f"TORCH2PC_COMMIT={preflight.source_identity.torch2pc_commit}\n"
        f"IMAGE_DIGEST={preflight.source_identity.image_digest}\n"
        f"IMAGE_REPO_DIGEST={preflight.source_identity.image_repo_digest}\n"
        f"PREFLIGHT_SHA256={preflight.preflight_sha256}\n"
        f"AUTHORIZATION_SHA256={authorization.authorization_sha256}\n"
    )
    (output / "identity.env").write_text(identity_lines, encoding="utf-8")

    manifest = {
        "schema_version": 1,
        "freeze_id": RUNTIME_FREEZE_ID,
        "slice": "QW-LC4-F",
        "status": "runtime_authorization_frozen_execution_not_performed",
        "materialized_at_utc": args.materialized_at_utc,
        "source_commit": preflight.source_identity.source_commit,
        "torch2pc_commit": preflight.source_identity.torch2pc_commit,
        "image_digest": preflight.source_identity.image_digest,
        "image_repo_digest": preflight.source_identity.image_repo_digest,
        "request_sha256": preflight.source_identity.request_sha256,
        "implementation_source_sha256": (
            preflight.source_identity.implementation_source_sha256
        ),
        "implementation_manifest_sha256": (
            preflight.source_identity.implementation_manifest_sha256
        ),
        "implementation_registry_sha256": (
            preflight.source_identity.implementation_registry_sha256
        ),
        "lc3_contract_sha256": preflight.source_identity.lc3_contract_sha256,
        "lc3_contract_registry_sha256": (
            preflight.source_identity.lc3_contract_registry_sha256
        ),
        "adapter_registry_sha256": (
            preflight.source_identity.adapter_registry_sha256
        ),
        "preflight_sha256": preflight.preflight_sha256,
        "authorization_sha256": authorization.authorization_sha256,
        "authorized_cell_count": len(authorization.cells),
        "runtime_cell_count": 14,
        "matched_pair_count": 168,
        "reserve_probe_count": 28,
        "execution_count": 1,
        "authorized_output_root": RUNTIME_OUTPUT_ROOT.as_posix(),
        "runtime_execution_permitted": True,
        "runtime_execution_performed": False,
        "engineering_evidence_present": False,
        "scientific_execution_open": False,
        "test_dataset_access": False,
        "publication_permitted": False,
        "image_freeze_permitted": False,
        "next_slice": "QW-LC4-F-merge",
        "post_merge_next_slice": "QW-LC4-E",
    }
    (output / "manifest.json").write_text(
        canonical_json(manifest),
        encoding="utf-8",
    )

    package_names = sorted(path.name for path in output.iterdir())
    sums = [
        f"{_sha256(output / name)}  {name}"
        for name in package_names
        if name != "SHA256SUMS"
    ]
    (output / "SHA256SUMS").write_text(
        "\n".join(sums) + "\n",
        encoding="utf-8",
    )
    print(f"FREEZE_DIR={output}")
    print(f"FREEZE_ID={RUNTIME_FREEZE_ID}")
    print(f"PREFLIGHT_SHA256={preflight.preflight_sha256}")
    print(f"AUTHORIZATION_SHA256={authorization.authorization_sha256}")
    print(f"AUTHORIZED_CELL_COUNT={len(authorization.cells)}")
    print("RUNTIME_EXECUTION_PERFORMED=false")
    print("SCIENTIFIC_EXECUTION_OPEN=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
