#!/usr/bin/env python3
"""Verify final QW-LC4-E invocation admission without invoking runtime."""

from __future__ import annotations

import argparse
from pathlib import Path

from torch2pc_thesis.stage3b_qwake_lc4_final_engineering_invocation_admission import (
    load_final_engineering_invocation_admission,
    validate_final_engineering_invocation_admission,
    verify_final_engineering_invocation_sources,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--admission", type=Path, required=True)
    parser.add_argument("--authoring-base-commit", required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    source = verify_final_engineering_invocation_sources(args.project_root)
    admission = load_final_engineering_invocation_admission(args.admission)
    validate_final_engineering_invocation_admission(
        admission,
        source,
        args.project_root,
        expected_authoring_base_commit=args.authoring_base_commit,
    )
    print("FINAL_ENGINEERING_INVOCATION_ADMISSION_VERIFIED=true")
    print("FINAL_ENGINEERING_INVOCATION_ADMISSION_AUTHORED=true")
    print("FINAL_ENGINEERING_INVOCATION_ADMISSION_RECORD_PRESENT=true")
    print("FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_ISSUED=false")
    print("FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_CONSUMED=false")
    print("FINAL_ENGINEERING_INVOCATION_PERMITTED=false")
    print("FINAL_ENGINEERING_INVOCATION_STARTED=false")
    print("FINAL_ENGINEERING_INVOCATION_PERFORMED=false")
    print("EXECUTION_LEASE_V1_PRESENT=false")
    print("EXECUTION_LEASE_V2_PRESENT=false")
    print("DURABLE_HOST_OUTCOME_PRESENT=false")
    print("RUNTIME_OUTPUT_PRESENT=false")
    print("QW5_TRANSITION_PERMITTED=false")
    print("LOCAL_COMPUTE_EXECUTION_OPEN=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
