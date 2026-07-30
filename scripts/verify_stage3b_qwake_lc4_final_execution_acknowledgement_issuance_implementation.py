#!/usr/bin/env python3
"""Verify the QW-LC4-E acknowledgement-issuance implementation freeze."""

from __future__ import annotations

import argparse
from pathlib import Path

from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_issuance_implementation import (
    verify_final_execution_acknowledgement_issuance_implementation,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    args = parser.parse_args()

    record = verify_final_execution_acknowledgement_issuance_implementation(
        args.project_root
    )
    print(
        "ACKNOWLEDGEMENT_ISSUANCE_IMPLEMENTATION_SHA256="
        f"{record.implementation_sha256}"
    )
    print("ACKNOWLEDGEMENT_ISSUANCE_AUTHORING_POST_MERGE_VERIFIED=true")
    print("FINAL_EXECUTION_ACKNOWLEDGEMENT_AUTHORING_POST_MERGE_VERIFIED=true")
    print("PERSISTENT_EVIDENCE_CHAIN_V2_PRESENT=true")
    print("PERSISTENT_LEASE_V2_IMPLEMENTATION_PRESENT=true")
    print("DURABLE_OUTCOME_WRITER_IMPLEMENTED=true")
    print("LEASE_BOUND_HOST_INVOKER_ENFORCED=true")
    print("FINAL_EXECUTION_ACKNOWLEDGEMENT_AUTHORED=true")
    print("ACKNOWLEDGEMENT_ISSUANCE_CONTRACT_AUTHORED=true")
    print("ACKNOWLEDGEMENT_ISSUANCE_IMPLEMENTED=true")
    print("FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUED=false")
    print("FINAL_EXECUTION_ACKNOWLEDGED=false")
    print("ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false")
    print("EXECUTION_LEASE_MATERIALIZED=false")
    print("DURABLE_HOST_OUTCOME_PRESENT=false")
    print("AUTHORIZATION_CONSUMED=false")
    print("RUNTIME_EXECUTION_STARTED=false")
    print("RUNTIME_EXECUTION_PERFORMED=false")
    print("IMAGE_INSPECTION_PERFORMED=false")
    print("INVOCATION_COMMAND_MATERIALIZED=false")
    print("DOCKER_RUN_PERFORMED=false")
    print("LOCAL_COMPUTE_EXECUTION_OPEN=false")
    print("OK: acknowledgement-issuance implementation freeze verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
