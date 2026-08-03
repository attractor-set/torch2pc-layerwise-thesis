#!/usr/bin/env python3
"""Verify the prepared QW-LC4-E consumption attempt without runtime."""

from __future__ import annotations

import argparse
from pathlib import Path

from torch2pc_thesis.stage3b_qwake_lc4_final_engineering_invocation_authorization_consumption_attempt import (
    load_consumption_attempt,
    validate_consumption_attempt,
    verify_consumption_attempt_sources,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--attempt", type=Path, required=True)
    parser.add_argument("--authoring-base-commit", required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    source = verify_consumption_attempt_sources(args.project_root)
    attempt = load_consumption_attempt(args.attempt)
    validate_consumption_attempt(
        attempt,
        source,
        args.project_root,
        expected_authoring_base_commit=args.authoring_base_commit,
    )
    print("AUTHORIZATION_CONSUMPTION_ATTEMPT_VERIFIED=true")
    print("AUTHORIZATION_CONSUMPTION_ATTEMPT_RECORD_AUTHORED=true")
    print("AUTHORIZATION_CONSUMPTION_ATTEMPT_RECORD_PRESENT=true")
    print("AUTHORIZATION_CONSUMPTION_ATTEMPT_PREPARED=true")
    print("AUTHORIZATION_CONSUMPTION_ATTEMPT_POST_MERGE_VERIFIED=false")
    print("AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_ACTION_PERMITTED=false")
    print("AUTHORIZATION_CONSUMPTION_ATTEMPT_STARTED=false")
    print("FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_CONSUMED=false")
    print("FINAL_ENGINEERING_INVOCATION_STARTED=false")
    print("FINAL_ENGINEERING_INVOCATION_PERFORMED=false")
    print("INVOCATION_COMMAND_MATERIALIZED=false")
    print("EXECUTION_LEASE_V1_PRESENT=false")
    print("EXECUTION_LEASE_V2_PRESENT=false")
    print("DURABLE_HOST_OUTCOME_PRESENT=false")
    print("RUNTIME_OUTPUT_PRESENT=false")
    print("QW5_TRANSITION_PERMITTED=false")
    print("LOCAL_COMPUTE_EXECUTION_OPEN=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
