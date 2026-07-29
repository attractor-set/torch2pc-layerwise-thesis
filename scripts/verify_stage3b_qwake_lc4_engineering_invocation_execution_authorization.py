#!/usr/bin/env python3
"""Verify QW-LC4-E execution authorization without runtime effects."""

from __future__ import annotations

import argparse
from pathlib import Path

from torch2pc_thesis.stage3b_qwake_lc4_engineering_invocation_execution_authorization import (
    verify_engineering_invocation_execution_authorization,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path("."))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    authorization = verify_engineering_invocation_execution_authorization(
        args.project_root
    )
    print("OK: QW-LC4-E execution authorization verified")
    print(f"EXECUTION_AUTHORIZATION_ID={authorization.authorization_id}")
    print(
        "EXECUTION_AUTHORIZATION_SHA256="
        f"{authorization.authorization_sha256}"
    )
    print(f"EXECUTION_BASE_COMMIT={authorization.source.execution_base_commit}")
    print("REPOSITORY_FREEZE_COMPLETE=true")
    print("INVOCATION_ADMISSION_COMPLETE=true")
    print("INVOCATION_OPERATION_COMPLETE=true")
    print("EXECUTION_AUTHORIZATION_RECORD_PRESENT=true")
    print("EXECUTION_AUTHORIZATION_ISSUED=true")
    print("PREEXECUTION_VERIFICATION_MATERIALIZATION_IMPLEMENTED=true")
    print("PREEXECUTION_IDENTITY_VERIFIED=false")
    print("ONE_SHOT_ENGINEERING_INVOCATION_SLICE_OPEN=true")
    print("ONE_SHOT_ENGINEERING_INVOCATION_OPERATION_OPEN=true")
    print("ONE_SHOT_ENGINEERING_INVOCATION_EXECUTION_OPEN=true")
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
