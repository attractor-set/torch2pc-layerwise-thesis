#!/usr/bin/env python3
"""Verify QW-LC4-E persistent-evidence-chain-v2 authoring without effects."""

from __future__ import annotations

import argparse
from pathlib import Path

from torch2pc_thesis.stage3b_qwake_lc4_persistent_evidence_chain_v2 import (
    verify_persistent_evidence_chain_v2,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path("."))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    chain = verify_persistent_evidence_chain_v2(args.project_root)
    print("OK: QW-LC4-E persistent evidence chain v2 verified")
    print(f"PERSISTENT_EVIDENCE_CHAIN_V2_ID={chain.chain_id}")
    print(f"PERSISTENT_EVIDENCE_CHAIN_V2_SHA256={chain.chain_sha256}")
    print(
        "IDENTITY_REPAIR_MERGE_COMMIT="
        f"{chain.source.identity_repair_merge_commit}"
    )
    print("CORRECTED_FULL_VALIDATION_RECEIPT_PRESENT=true")
    print("RUNTIME_OPERATION_IDENTITY_REPAIR_MERGED=true")
    print("LATEST_AUTHORIZATION_BOUND_IN_PERSISTENT_LEASE_TEMPLATE=true")
    print("DURABLE_NEGATIVE_HOST_OUTCOME_DEFINED=true")
    print("PERSISTENT_LEASE_V2_IMPLEMENTATION_PRESENT=false")
    print("DURABLE_OUTCOME_WRITER_IMPLEMENTED=false")
    print("LEASE_BOUND_HOST_INVOKER_ENFORCED=false")
    print("FINAL_EXECUTION_ACKNOWLEDGED=false")
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
