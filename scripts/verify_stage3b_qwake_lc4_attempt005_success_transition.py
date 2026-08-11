#!/usr/bin/env python3
"""Verify the immutable Attempt-005 success -> QW-5 transition receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, cast

PACKAGE_RELATIVE = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-attempt-005-success-transition-v1"
)
RECEIPT_RELATIVE = PACKAGE_RELATIVE / "receipt.json"
REGISTRY_RELATIVE = PACKAGE_RELATIVE / "SHA256SUMS"

MAIN_COMMIT = "7168d6ebf3fbc27f5b85e1e44a7e8252f28038b0"
MAIN_TREE = "170503e1f1be147be13c90f43c1012e8bb291b18"
REPORT_SHA256 = (
    "sha256:51cdc39650ed82ff896165fb81fefdb43a35c7a78b3dcc46d5f6627e601aa18d"
)


class TransitionVerificationError(RuntimeError):
    pass


def _sha(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise TransitionVerificationError(f"regular file required: {path}")
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        json.loads(path.read_text(encoding="utf-8", errors="strict")),
    )


def _verify_registry(root: Path) -> None:
    registry = root / REGISTRY_RELATIVE
    lines = registry.read_text(encoding="utf-8", errors="strict").splitlines()
    if len(lines) != 1:
        raise TransitionVerificationError("transition registry must contain one line")
    digest, sep, relative = lines[0].partition("  ")
    if sep != "  " or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise TransitionVerificationError("transition registry line is malformed")
    if relative != "receipt.json":
        raise TransitionVerificationError("transition registry path differs")
    if _sha(root / PACKAGE_RELATIVE / relative) != "sha256:" + digest:
        raise TransitionVerificationError("transition registry digest differs")


def verify(root: Path) -> None:
    receipt = _load(root / RECEIPT_RELATIVE)
    _verify_registry(root)

    exact = {
        "schema_version": 1,
        "transition_id": "stage3b-qwake-lc4-e-attempt-005-success-transition-v1",
        "main_commit": MAIN_COMMIT,
        "main_tree": MAIN_TREE,
        "attempt_id": "stage3b-qwake-lc4-runtime-validation-v1-attempt-005",
        "attempt_terminal": True,
        "attempt_retry_permitted": False,
        "report_status": "engineering_matrix_completed_validation_passed",
        "validation_passed": True,
        "authorized_cell_count": 168,
        "reserve_probe_count": 28,
        "aggregate_count": 14,
        "all_response_comparisons_passed": True,
        "all_rng_matches_passed": True,
        "all_reserve_probes_passed": True,
        "all_order_effect_gates_passed": True,
        "all_pairs_complete": True,
        "order_effect_failure_count": 0,
        "cpu_order_effect_pass_count": 7,
        "rocm_order_effect_pass_count": 7,
        "host_child_spawn_count": 1,
        "host_return_code": 0,
        "host_timed_out": False,
        "host_automatic_retry_performed": False,
        "authorization_consumed": True,
        "attempt_started": True,
        "runtime_output_present": True,
        "execution_lease_v2_present": False,
        "backend_sha256s_verified": True,
        "engineering_evidence_present": True,
        "qw_lc4_e_complete": True,
        "qw5_transition_permitted": True,
        "qw5_open": True,
        "qw5_scientific_image_freeze_open": True,
        "qw5_image_frozen": False,
        "scientific_execution_open": False,
        "c1_collection_open": False,
        "c2_calibration_open": False,
        "c3_confirmatory_open": False,
        "replication_open": False,
        "test_dataset_access": False,
        "publication_permitted": False,
        "local_compute_execution_open": False,
        "runtime_rerun_performed": False,
        "next_slice": "QW-5-scientific-image-freeze",
    }
    for key, expected in exact.items():
        if receipt.get(key) != expected:
            raise TransitionVerificationError(f"receipt field differs: {key}")

    if receipt.get("runtime_report_semantic_sha256") != REPORT_SHA256:
        raise TransitionVerificationError("Attempt-005 report identity differs")

    sha_fields = [
        key for key in receipt if key.endswith("_sha256")
    ]
    for key in sha_fields:
        value = receipt[key]
        if not isinstance(value, str) or re.fullmatch(
            r"sha256:[0-9a-f]{64}", value
        ) is None:
            raise TransitionVerificationError(f"malformed sha256 field: {key}")

    for name, heading in (
        ("STATUS.md", "## `QW-LC4-E`: Attempt-005 terminal PASS"),
        ("STATUS_EN.md", "## `QW-LC4-E`: Attempt-005 terminal PASS"),
    ):
        text = (root / name).read_text(encoding="utf-8", errors="strict")
        if heading not in text:
            raise TransitionVerificationError(f"status section absent: {name}")
        section = text[text.rindex(heading) :]
        for marker in (
            "ATTEMPT_005_VALIDATION_PASSED=true",
            "QW_LC4_E_COMPLETE=true",
            "QW5_TRANSITION_PERMITTED=true",
            "QW5_SCIENTIFIC_IMAGE_FREEZE_OPEN=true",
            "QW5_IMAGE_FROZEN=false",
            "SCIENTIFIC_EXECUTION_OPEN=false",
            "TEST_DATASET_ACCESS=false",
            "PUBLICATION_PERMITTED=false",
            "NEXT_SLICE=QW-5-scientific-image-freeze",
        ):
            if marker not in section:
                raise TransitionVerificationError(
                    f"status marker absent: {name}: {marker}"
                )

    print("ATTEMPT005_TERMINAL_VALIDATION_BOUND=true")
    print("QW_LC4_E_COMPLETE=true")
    print("QW5_TRANSITION_PERMITTED=true")
    print("QW5_SCIENTIFIC_IMAGE_FREEZE_OPEN=true")
    print("QW5_IMAGE_FROZEN=false")
    print("SCIENTIFIC_EXECUTION_OPEN=false")
    print("C1_COLLECTION_OPEN=false")
    print("C2_CALIBRATION_OPEN=false")
    print("C3_CONFIRMATORY_OPEN=false")
    print("REPLICATION_OPEN=false")
    print("TEST_DATASET_ACCESS=false")
    print("PUBLICATION_PERMITTED=false")
    print("NEXT_SLICE=QW-5-scientific-image-freeze")
    print("ATTEMPT005_SUCCESS_TRANSITION_VERIFICATION=PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path("."))
    args = parser.parse_args()
    verify(args.project_root.expanduser().resolve())


if __name__ == "__main__":
    main()
