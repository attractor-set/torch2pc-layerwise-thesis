#!/usr/bin/env python3
"""Verify the final QW-LC4-E authorization without invoking runtime."""

from __future__ import annotations

import argparse
from pathlib import Path

from torch2pc_thesis.stage3b_qwake_lc4_final_engineering_invocation_authorization import (
    load_final_engineering_invocation_authorization,
    validate_final_engineering_invocation_authorization,
    verify_final_engineering_invocation_authorization_sources,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument("--authoring-base-commit", required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    source = verify_final_engineering_invocation_authorization_sources(
        args.project_root
    )
    authorization = load_final_engineering_invocation_authorization(
        args.authorization
    )
    validate_final_engineering_invocation_authorization(
        authorization,
        source,
        args.project_root,
        expected_authoring_base_commit=args.authoring_base_commit,
    )
    print("FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_VERIFIED=true")
    print("FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_AUTHORED=true")
    print("FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_RECORD_PRESENT=true")
    print("FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_ISSUED=true")
    print("FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_POST_MERGE_VERIFIED=false")
    print("FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_CONSUMED=false")
    print("FINAL_ENGINEERING_INVOCATION_PERMITTED=false")
    print("FINAL_ENGINEERING_INVOCATION_STARTED=false")
    print("FINAL_ENGINEERING_INVOCATION_PERFORMED=false")
    print("OPERATOR_PHRASE_RESERVED=true")
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
