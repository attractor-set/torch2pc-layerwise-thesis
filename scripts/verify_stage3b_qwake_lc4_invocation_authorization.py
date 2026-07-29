#!/usr/bin/env python3
"""Verify QW-LC4-E invocation authorization without effects."""

from __future__ import annotations

import argparse
from pathlib import Path

from torch2pc_thesis.stage3b_qwake_lc4_invocation_authorization import (
    verify_invocation_authorization,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path("."))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    authorization = verify_invocation_authorization(args.project_root)
    print("OK: QW-LC4-E one-shot invocation authorization verified")
    print(f"AUTHORIZATION_ID={authorization.authorization_id}")
    print(f"AUTHORIZATION_SHA256={authorization.authorization_sha256}")
    print("ONE_SHOT_INVOCATION_AUTHORIZED=true")
    print("FUTURE_LEASE_CLAIM_AUTHORIZED=true")
    print("FUTURE_RUNTIME_EXECUTION_AUTHORIZED=true")
    print("BRANCH_RUNTIME_EXECUTION_PERMITTED=false")
    print("EXECUTION_LEASE_MATERIALIZED=false")
    print("AUTHORIZATION_CONSUMED=false")
    print("RUNTIME_EXECUTION_STARTED=false")
    print("RUNTIME_EXECUTION_PERFORMED=false")
    print("ENGINEERING_EVIDENCE_PRESENT=false")
    print("SCIENTIFIC_EXECUTION_OPEN=false")
    print("TEST_DATASET_ACCESS=false")
    print("PUBLICATION_PERMITTED=false")
    print("LOCAL_COMPUTE_EXECUTION_OPEN=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
