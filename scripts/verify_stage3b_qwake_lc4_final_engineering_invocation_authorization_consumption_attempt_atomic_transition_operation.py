#!/usr/bin/env python3
"""Verify the non-executing QW-LC4-E atomic-transition operation package."""

from __future__ import annotations

import argparse
from pathlib import Path

from torch2pc_thesis.stage3b_qwake_lc4_final_engineering_invocation_authorization_consumption_attempt_atomic_transition_operation import (
    OPERATION_AUTHORING_BASE_COMMIT,
    OPERATION_RECORD_RELATIVE,
    load_atomic_transition_operation,
    validate_atomic_transition_operation,
    verify_atomic_transition_operation_sources,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--operation", type=Path)
    parser.add_argument(
        "--authoring-base-commit",
        default=OPERATION_AUTHORING_BASE_COMMIT,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.project_root.expanduser().resolve()
    operation_path = args.operation or (root / OPERATION_RECORD_RELATIVE)
    source = verify_atomic_transition_operation_sources(root)
    operation = load_atomic_transition_operation(operation_path)
    validate_atomic_transition_operation(
        operation,
        source,
        root,
        expected_authoring_base_commit=args.authoring_base_commit,
    )
    print("ATOMIC_TRANSITION_OPERATION_VERIFIED=true")
    print("ATOMIC_TRANSITION_OPERATION_AUTHORED=true")
    print("ATOMIC_TRANSITION_OPERATION_MODULE_CREATED=true")
    print("ATOMIC_TRANSITION_OPERATION_VERIFIER_CREATED=true")
    print("ATOMIC_TRANSITION_OPERATION_TESTS_CREATED=true")
    print("ATOMIC_TRANSITION_OPERATION_RECORD_CREATED=true")
    print("COMBINED_OPERATION_ADMISSION_CONTRACT_CREATED=true")
    print("ATOMIC_TRANSITION_OPERATION_POST_MERGE_VERIFIED=false")
    print("CONSUMPTION_ATTEMPT_ATOMIC_ACTION_PERMITTED=false")
    print("CONSUMPTION_ATTEMPT_ATOMIC_ACTION_COMMITTED=false")
    print("AUTHORIZATION_CONSUMED=false")
    print("CONSUMPTION_ATTEMPT_STARTED=false")
    print("EXECUTION_LEASE_V2_PRESENT=false")
    print("RUNTIME_OUTPUT_PRESENT=false")
    print("QW5_TRANSITION_PERMITTED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
