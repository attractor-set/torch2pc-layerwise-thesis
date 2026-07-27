#!/usr/bin/env python3
"""Verify prospective QW-LC4-E lease/wrapper contracts without effects."""

from __future__ import annotations

import argparse
from pathlib import Path

from torch2pc_thesis.stage3b_qwake_lc4_execution_wrapper import (
    EXECUTION_LEASE_OPERATOR_ACKNOWLEDGEMENT,
    build_execution_wrapper_contract,
    build_prospective_execution_lease,
    validate_execution_wrapper_contract,
    validate_prospective_execution_lease,
    verify_unconsumed_frozen_admission,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--prospective-wrapper-commit", required=True)
    parser.add_argument("--claimed-at-utc", required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    project_root = args.project_root.expanduser().resolve()
    frozen = verify_unconsumed_frozen_admission(project_root)
    lease = build_prospective_execution_lease(
        frozen,
        claimed_at_utc=args.claimed_at_utc,
        wrapper_commit=args.prospective_wrapper_commit,
        operator_acknowledgement=(
            EXECUTION_LEASE_OPERATOR_ACKNOWLEDGEMENT
        ),
        output_root_absent_at_claim=True,
        execution_lease_absent_at_claim=True,
    )
    validate_prospective_execution_lease(
        lease,
        frozen,
        project_root,
        expected_wrapper_commit=args.prospective_wrapper_commit,
    )
    contract = build_execution_wrapper_contract(lease)
    validate_execution_wrapper_contract(contract, lease)

    print("FROZEN_ADMISSION_VERIFIED=true")
    print(f"PROSPECTIVE_LEASE_SHA256={lease.lease_sha256}")
    print(f"WRAPPER_CONTRACT_SHA256={contract.contract_sha256}")
    print("EXECUTION_LEASE_SCHEMA_IMPLEMENTED=true")
    print("EXECUTION_WRAPPER_CONTRACT_IMPLEMENTED=true")
    print("EXECUTION_LEASE_MATERIALIZED=false")
    print("EXECUTION_LEASE_WRITER_PRESENT=false")
    print("RUNTIME_EXECUTOR_PRESENT=false")
    print("QW_LC4_E_EXECUTION_PERMITTED=false")
    print("AUTHORIZATION_CONSUMED=false")
    print("RUNTIME_EXECUTION_STARTED=false")
    print("RUNTIME_EXECUTION_PERFORMED=false")
    print("ENGINEERING_EVIDENCE_PRESENT=false")
    print("SCIENTIFIC_EXECUTION_OPEN=false")
    print("TEST_DATASET_ACCESS=false")
    print("PUBLICATION_PERMITTED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
