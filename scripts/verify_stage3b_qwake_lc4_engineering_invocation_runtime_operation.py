#!/usr/bin/env python3
"""Verify the QW-LC4-E runtime-operation contract without effects."""

from __future__ import annotations

import argparse
from pathlib import Path

from torch2pc_thesis.stage3b_qwake_lc4_engineering_invocation_runtime_operation import (
    verify_engineering_invocation_runtime_operation,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path("."))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    operation = verify_engineering_invocation_runtime_operation(
        args.project_root
    )
    print("OK: QW-LC4-E runtime-operation contract verified")
    print(f"RUNTIME_OPERATION_ID={operation.operation_id}")
    print(f"RUNTIME_OPERATION_SHA256={operation.operation_sha256}")
    print(
        "RUNTIME_OPERATION_BASE_COMMIT="
        f"{operation.source.runtime_operation_base_commit}"
    )
    print("EXECUTION_AUTHORIZATION_COMPLETE=true")
    print("PREEXECUTION_VERIFICATION_COMPLETE=true")
    print("PREEXECUTION_STATIC_CONTRACT_VERIFIED=true")
    print("RUNTIME_OPERATION_RECORD_PRESENT=true")
    print("RUNTIME_OPERATION_EXECUTOR_ENTRYPOINT_IMPLEMENTED=true")
    print("RUNTIME_OPERATION_STATIC_CONTRACT_VERIFIED=true")
    print("ONE_SHOT_ENGINEERING_INVOCATION_RUNTIME_OPERATION_SLICE_OPEN=true")
    print("ONE_SHOT_ENGINEERING_INVOCATION_RUNTIME_OPERATION_OPEN=true")
    print("PREEXECUTION_IDENTITY_VERIFIED=false")
    print("ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false")
    print("ONE_SHOT_ENGINEERING_INVOCATION_PERFORMED=false")
    print("BRANCH_RUNTIME_EXECUTION_PERMITTED=false")
    print("EXECUTION_LEASE_MATERIALIZED=false")
    print("AUTHORIZATION_CONSUMED=false")
    print("RUNTIME_EXECUTION_STARTED=false")
    print("RUNTIME_EXECUTION_PERFORMED=false")
    print("ENGINEERING_EVIDENCE_PRESENT=false")
    print("SCIENTIFIC_EXECUTION_OPEN=false")
    print("TEST_DATASET_ACCESS=false")
    print("PUBLICATION_PERMITTED=false")
    print("IMAGE_INSPECTION_PERFORMED=false")
    print("INVOCATION_COMMAND_MATERIALIZED=false")
    print("DOCKER_RUN_PERFORMED=false")
    print("LOCAL_COMPUTE_EXECUTION_OPEN=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
