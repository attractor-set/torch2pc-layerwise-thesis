#!/usr/bin/env python3
"""Verify the bounded QW-LC4-E acknowledgement materialization implementation."""

from __future__ import annotations

import argparse
from pathlib import Path

from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_materialization import (
    FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_IMPLEMENTATION_ID,
    verify_final_execution_acknowledgement_materialization_implementation,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    record = verify_final_execution_acknowledgement_materialization_implementation(
        args.project_root
    )
    print("OK: QW-LC4-E acknowledgement materialization implementation verified")
    print(
        "ACKNOWLEDGEMENT_MATERIALIZATION_IMPLEMENTATION_ID="
        f"{FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_IMPLEMENTATION_ID}"
    )
    print(
        "ACKNOWLEDGEMENT_MATERIALIZATION_IMPLEMENTATION_SHA256="
        f"{record.implementation_sha256}"
    )
    print("MATERIALIZATION_AUTHORING_POST_MERGE_VERIFIED=true")
    print("ACKNOWLEDGEMENT_MATERIALIZATION_CONTRACT_AUTHORED=true")
    print("ACKNOWLEDGEMENT_MATERIALIZATION_IMPLEMENTED=true")
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
    print("MATERIALIZER_CALLED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
