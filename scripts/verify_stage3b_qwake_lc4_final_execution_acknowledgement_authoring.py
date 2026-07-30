#!/usr/bin/env python3
"""Verify the static QW-LC4-E final-execution acknowledgement authoring freeze."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
from typing import Any, cast

from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_authoring import (
    ADR_EN_RELATIVE,
    ADR_RU_RELATIVE,
    AUTHORING_BASE_COMMIT,
    AUTHORING_RECORD_RELATIVE,
    FINAL_EXECUTION_ACKNOWLEDGEMENT_AUTHORING_ID,
    FINAL_EXECUTION_ACKNOWLEDGEMENT_AUTHORING_STATUS,
    FINAL_EXECUTION_OPERATOR_ACKNOWLEDGEMENT,
    MODULE_RELATIVE,
    PACKAGE_RELATIVE,
    REGISTRY_RELATIVE,
    SOURCE_REGISTRY_RELATIVE,
    TEST_RELATIVE,
    VERIFIER_RELATIVE,
    WIRING_MERGE_RECEIPT_RELATIVE,
    build_final_execution_acknowledgement,
    load_wiring_merge_validation_receipt,
    verify_final_execution_acknowledgement_authoring,
)

_EXPECTED_PACKAGE_FILES = {
    "SHA256SUMS",
    "authoring.json",
    "source-SHA256SUMS",
    "wiring-merge-validation.json",
}
_EXPECTED_PACKAGE_REGISTRY_PATHS = {
    "authoring.json",
    "source-SHA256SUMS",
    "wiring-merge-validation.json",
}
_EXPECTED_SOURCE_PATHS = {
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-persistent-evidence-chain-v2-authoring-v1/chain.json",
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-persistent-evidence-chain-v2-implementation-v1/"
    "implementation.json",
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-lease-bound-host-invoker-wiring-v1/wiring.json",
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-lease-bound-host-invoker-wiring-v1/SHA256SUMS",
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-lease-bound-host-invoker-wiring-v1/source-SHA256SUMS",
    "src/torch2pc_thesis/stage3b_qwake_lc4_lease_bound_host_invoker_wiring.py",
    "scripts/verify_stage3b_qwake_lc4_lease_bound_host_invoker_wiring.py",
    "tests/unit/test_stage3b_qwake_lc4_lease_bound_host_invoker_wiring.py",
    "docs/decisions/"
    "ADR-085-stage3b-qwake-lc4-e-lease-bound-host-invoker-wiring.md",
    "docs/decisions/"
    "ADR-085-stage3b-qwake-lc4-e-lease-bound-host-invoker-wiring_EN.md",
    MODULE_RELATIVE.as_posix(),
    VERIFIER_RELATIVE.as_posix(),
    TEST_RELATIVE.as_posix(),
    ADR_RU_RELATIVE.as_posix(),
    ADR_EN_RELATIVE.as_posix(),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path("."))
    return parser.parse_args()


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8", errors="strict"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"JSON root differs: {path}")
    return cast(dict[str, Any], payload)


def _registry(path: Path, base: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="strict").splitlines():
        digest, relative = line.split("  ", 1)
        if relative in result:
            raise RuntimeError(f"duplicate registry path: {relative}")
        result[relative] = "sha256:" + digest
        if _sha256(base / relative) != result[relative]:
            raise RuntimeError(f"registry digest differs: {relative}")
    return result


def _verify_effect_free_ast(root: Path) -> None:
    tree = ast.parse(
        (root / MODULE_RELATIVE).read_text(encoding="utf-8", errors="strict")
    )
    forbidden_names = {
        "invoke_lease_bound_host_runtime",
        "invoke_one_shot_host_runtime",
        "persist_persistent_execution_lease_v2",
        "persist_durable_host_outcome_receipt",
        "inspect_local_image",
        "materialize_invocation_command",
    }
    forbidden_attributes = {
        "Popen",
        "run",
        "write_bytes",
        "write_text",
        "touch",
        "mkdir",
        "replace",
        "rename",
        "symlink_to",
        "hardlink_to",
        "unlink",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in forbidden_names:
                raise RuntimeError(f"forbidden authoring call: {node.func.id}")
            if (
                isinstance(node.func, ast.Attribute)
                and node.func.attr in forbidden_attributes
            ):
                raise RuntimeError(f"forbidden authoring call: {node.func.attr}")


def main() -> None:
    root = parse_args().project_root.expanduser().resolve()
    package = root / PACKAGE_RELATIVE
    if {path.name for path in package.iterdir()} != _EXPECTED_PACKAGE_FILES:
        raise RuntimeError("acknowledgement authoring package file set differs")
    package_registry = _registry(root / REGISTRY_RELATIVE, package)
    if set(package_registry) != _EXPECTED_PACKAGE_REGISTRY_PATHS:
        raise RuntimeError("acknowledgement package registry scope differs")
    source_registry = _registry(root / SOURCE_REGISTRY_RELATIVE, root)
    if set(source_registry) != _EXPECTED_SOURCE_PATHS:
        raise RuntimeError("acknowledgement source registry scope differs")

    receipt = _load(root / WIRING_MERGE_RECEIPT_RELATIVE)
    exact_receipt: dict[str, object] = {
        "receipt_id": (
            "stage3b-qwake-lc4-e-lease-bound-host-invoker-wiring-"
            "post-merge-validation-v1"
        ),
        "pr_number": 146,
        "head_commit": "1d4096a8086c9f9c32e1d14515ef3b702d2237ab",
        "base_commit": "0303a1514e2875a057ef1b20293a01b36a9c6b2b",
        "merge_commit": "2957d8f6975c88e7bdb23243e3915c7f51d4ba47",
        "merged_at_utc": "2026-07-30T14:37:25Z",
        "commit_count": 1,
        "file_count": 18,
        "focused_tests_passed": 39,
        "targeted_tests_passed": 240,
        "full_tests_passed": 1287,
        "full_test_warnings": 14,
        "required_ci_checks_passed": True,
        "runtime_boundary_closed": True,
    }
    for field_name, expected_value in exact_receipt.items():
        if receipt.get(field_name) != expected_value:
            raise RuntimeError(f"wiring merge receipt differs: {field_name}")
    reduced_receipt = dict(receipt)
    receipt_digest = reduced_receipt.pop("receipt_sha256", None)
    expected_receipt_digest = "sha256:" + hashlib.sha256(
        json.dumps(
            reduced_receipt,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    if receipt_digest != expected_receipt_digest:
        raise RuntimeError("wiring merge receipt semantic digest differs")

    record = _load(root / AUTHORING_RECORD_RELATIVE)
    if record.get("authoring_id") != FINAL_EXECUTION_ACKNOWLEDGEMENT_AUTHORING_ID:
        raise RuntimeError("acknowledgement authoring ID differs")
    if record.get("status") != FINAL_EXECUTION_ACKNOWLEDGEMENT_AUTHORING_STATUS:
        raise RuntimeError("acknowledgement authoring status differs")
    source = cast(dict[str, Any], record.get("source"))
    if source.get("authoring_base_commit") != AUTHORING_BASE_COMMIT:
        raise RuntimeError("acknowledgement authoring base differs")
    contract = cast(dict[str, Any], record.get("contract"))
    if contract.get("exact_operator_phrase_required") != (
        FINAL_EXECUTION_OPERATOR_ACKNOWLEDGEMENT
    ):
        raise RuntimeError("operator acknowledgement phrase differs")
    gates = cast(dict[str, Any], record.get("gates"))
    if gates.get("final_execution_acknowledgement_authored") is not True:
        raise RuntimeError("acknowledgement authoring gate differs")
    if gates.get("final_execution_acknowledgement_issued") is not False:
        raise RuntimeError("acknowledgement issuance gate differs")
    if gates.get("final_execution_acknowledged") is not False:
        raise RuntimeError("final acknowledgement gate differs")
    if gates.get("one_shot_engineering_invocation_permitted") is not False:
        raise RuntimeError("invocation permission gate differs")
    reduced_record = dict(record)
    record_digest = reduced_record.pop("authoring_sha256", None)
    expected_record_digest = "sha256:" + hashlib.sha256(
        json.dumps(
            reduced_record,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    if record_digest != expected_record_digest:
        raise RuntimeError("acknowledgement authoring semantic digest differs")

    authoring = verify_final_execution_acknowledgement_authoring(root)
    loaded_receipt = load_wiring_merge_validation_receipt(
        root / WIRING_MERGE_RECEIPT_RELATIVE
    )
    prospective = build_final_execution_acknowledgement(
        authoring,
        loaded_receipt,
        acknowledgement_phrase=FINAL_EXECUTION_OPERATOR_ACKNOWLEDGEMENT,
        operator_identity="verification-only-operator",
        acknowledged_at_utc="2026-07-30T15:00:30Z",
    )
    if prospective.execution_lease_materialized:
        raise RuntimeError("prospective acknowledgement materialized a lease")
    if prospective.authorization_consumed:
        raise RuntimeError("prospective acknowledgement consumed authorization")
    _verify_effect_free_ast(root)

    print("OK: QW-LC4-E final-execution acknowledgement authoring verified")
    print(f"FINAL_EXECUTION_ACKNOWLEDGEMENT_AUTHORING_ID={authoring.authoring_id}")
    print(f"FINAL_EXECUTION_ACKNOWLEDGEMENT_AUTHORING_SHA256={record_digest}")
    print("WIRING_POST_MERGE_VERIFIED=true")
    print("PERSISTENT_EVIDENCE_CHAIN_V2_PRESENT=true")
    print("PERSISTENT_LEASE_V2_IMPLEMENTATION_PRESENT=true")
    print("DURABLE_OUTCOME_WRITER_IMPLEMENTED=true")
    print("LEASE_BOUND_HOST_INVOKER_ENFORCED=true")
    print("FINAL_EXECUTION_ACKNOWLEDGEMENT_AUTHORED=true")
    print("FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUED=false")
    print("FINAL_EXECUTION_ACKNOWLEDGED=false")
    print("ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false")
    print("EXECUTION_LEASE_MATERIALIZED=false")
    print("DURABLE_HOST_OUTCOME_PRESENT=false")
    print("AUTHORIZATION_CONSUMED=false")
    print("RUNTIME_EXECUTION_STARTED=false")
    print("RUNTIME_EXECUTION_PERFORMED=false")
    print("IMAGE_INSPECTION_PERFORMED=false")
    print("INVOCATION_COMMAND_MATERIALIZED=false")
    print("DOCKER_RUN_PERFORMED=false")
    print("LOCAL_COMPUTE_EXECUTION_OPEN=false")


if __name__ == "__main__":
    main()
