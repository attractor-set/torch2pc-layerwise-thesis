#!/usr/bin/env python3
"""Verify QW-LC4-E final acknowledgement issuance authoring."""

from __future__ import annotations

import argparse
from pathlib import Path

from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_issuance_authoring import (
    FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUANCE_AUTHORING_ID,
    verify_final_execution_acknowledgement_issuance_authoring,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    authoring = verify_final_execution_acknowledgement_issuance_authoring(
        args.project_root
    )
    gates = authoring.gates
    print("OK: QW-LC4-E acknowledgement-issuance authoring verified")
    print(
        "ACKNOWLEDGEMENT_ISSUANCE_AUTHORING_ID="
        f"{FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUANCE_AUTHORING_ID}"
    )
    print(
        "ACKNOWLEDGEMENT_ISSUANCE_AUTHORING_SHA256="
        f"{authoring.authoring_sha256}"
    )
    print("FINAL_EXECUTION_ACKNOWLEDGEMENT_AUTHORING_POST_MERGE_VERIFIED=true")
    print("PERSISTENT_EVIDENCE_CHAIN_V2_PRESENT=true")
    print("PERSISTENT_LEASE_V2_IMPLEMENTATION_PRESENT=true")
    print("DURABLE_OUTCOME_WRITER_IMPLEMENTED=true")
    print("LEASE_BOUND_HOST_INVOKER_ENFORCED=true")
    print("FINAL_EXECUTION_ACKNOWLEDGEMENT_AUTHORED=true")
    print("ACKNOWLEDGEMENT_ISSUANCE_CONTRACT_AUTHORED=true")
    print(
        "ACKNOWLEDGEMENT_ISSUANCE_IMPLEMENTED="
        f"{str(gates.acknowledgement_issuance_implemented).lower()}"
    )
    print(
        "FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUED="
        f"{str(gates.final_execution_acknowledgement_issued).lower()}"
    )
    print(
        "FINAL_EXECUTION_ACKNOWLEDGED="
        f"{str(gates.final_execution_acknowledged).lower()}"
    )
    print(
        "ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED="
        f"{str(gates.one_shot_engineering_invocation_permitted).lower()}"
    )
    print(
        "EXECUTION_LEASE_MATERIALIZED="
        f"{str(gates.execution_lease_materialized).lower()}"
    )
    print(
        "DURABLE_HOST_OUTCOME_PRESENT="
        f"{str(gates.durable_host_outcome_present).lower()}"
    )
    print(
        "AUTHORIZATION_CONSUMED="
        f"{str(gates.authorization_consumed).lower()}"
    )
    print(
        "RUNTIME_EXECUTION_STARTED="
        f"{str(gates.runtime_execution_started).lower()}"
    )
    print(
        "RUNTIME_EXECUTION_PERFORMED="
        f"{str(gates.runtime_execution_performed).lower()}"
    )
    print(
        "IMAGE_INSPECTION_PERFORMED="
        f"{str(gates.image_inspection_performed).lower()}"
    )
    print(
        "INVOCATION_COMMAND_MATERIALIZED="
        f"{str(gates.invocation_command_materialized).lower()}"
    )
    print(f"DOCKER_RUN_PERFORMED={str(gates.docker_run_performed).lower()}")
    print(
        "LOCAL_COMPUTE_EXECUTION_OPEN="
        f"{str(gates.local_compute_execution_open).lower()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
