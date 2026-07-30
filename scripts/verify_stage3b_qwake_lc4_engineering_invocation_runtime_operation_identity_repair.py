#!/usr/bin/env python3
"""Verify the QW-LC4-E runtime-operation identity repair without effects."""

from __future__ import annotations

import argparse
from pathlib import Path

from torch2pc_thesis.stage3b_qwake_lc4_engineering_invocation_runtime_operation_identity_repair import (
    verify_runtime_operation_identity_repair,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path("."))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repair = verify_runtime_operation_identity_repair(args.project_root)
    print("OK: QW-LC4-E runtime-operation identity repair verified")
    print(f"IDENTITY_REPAIR_ID={repair.repair_id}")
    print(f"IDENTITY_REPAIR_SHA256={repair.repair_sha256}")
    print(
        "RUNTIME_OPERATION_MERGE_COMMIT="
        f"{repair.source.runtime_operation_merge_commit}"
    )
    print(
        "CORRECTED_RUNTIME_OPERATION_MODULE_SHA256="
        f"{repair.bound_sources.runtime_operation_module_sha256}"
    )
    print("HISTORICAL_RUNTIME_OPERATION_PACKAGE_PRESERVED=true")
    print("CORRECTED_MODULE_IDENTITY_FROZEN=true")
    print("RUNTIME_OPERATION_SELF_IDENTITY_VERIFIED=true")
    print("CORRECTED_FULL_VALIDATION_RECEIPT_PRESENT=false")
    print("RUNTIME_OPERATION_IDENTITY_REPAIR_MERGED=false")
    print("LATEST_AUTHORIZATION_BOUND_IN_PERSISTENT_LEASE=false")
    print("DURABLE_NEGATIVE_HOST_OUTCOME_DEFINED=false")
    print("FINAL_EXECUTION_ACKNOWLEDGED=false")
    print("PREEXECUTION_IDENTITY_VERIFIED=false")
    print("ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false")
    print("EXECUTION_LEASE_MATERIALIZED=false")
    print("AUTHORIZATION_CONSUMED=false")
    print("RUNTIME_EXECUTION_STARTED=false")
    print("RUNTIME_EXECUTION_PERFORMED=false")
    print("IMAGE_INSPECTION_PERFORMED=false")
    print("INVOCATION_COMMAND_MATERIALIZED=false")
    print("DOCKER_RUN_PERFORMED=false")
    print("LOCAL_COMPUTE_EXECUTION_OPEN=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
