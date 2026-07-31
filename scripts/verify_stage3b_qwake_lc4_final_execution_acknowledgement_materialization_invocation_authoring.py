#!/usr/bin/env python3
"""Verify QW-LC4-E acknowledgement materialization invocation authoring."""

from __future__ import annotations

import argparse
from pathlib import Path

from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_authoring import (
    FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_AUTHORING_ID,
    verify_final_execution_acknowledgement_materialization_invocation_authoring,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    authoring = (
        verify_final_execution_acknowledgement_materialization_invocation_authoring(
            args.project_root
        )
    )
    gates = authoring.gates
    contract = authoring.contract
    print(
        "OK: QW-LC4-E acknowledgement materialization invocation authoring "
        "verified"
    )
    print(
        "ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_AUTHORING_ID="
        f"{FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_AUTHORING_ID}"
    )
    print(
        "ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_AUTHORING_SHA256="
        f"{authoring.authoring_sha256}"
    )
    print("MATERIALIZATION_IMPLEMENTATION_POST_MERGE_VERIFIED=true")
    print("ACKNOWLEDGEMENT_MATERIALIZATION_IMPLEMENTED=true")
    print("MATERIALIZATION_INVOCATION_CONTRACT_AUTHORED=true")
    print(
        "MATERIALIZATION_INVOCATION_IMPLEMENTED="
        f"{str(gates.materialization_invocation_implemented).lower()}"
    )
    print(
        "MATERIALIZATION_INVOKED="
        f"{str(gates.materialization_invoked).lower()}"
    )
    print(f"MATERIALIZER_CALLED={str(gates.materializer_called).lower()}")
    print(f"WRITER_CALLED={str(gates.writer_called).lower()}")
    print(
        "AUTOMATIC_RETRY_FORBIDDEN="
        f"{str(contract.automatic_retry_forbidden).lower()}"
    )
    print(
        "BLIND_RETRY_FORBIDDEN="
        f"{str(contract.blind_retry_forbidden).lower()}"
    )
    print(
        "EXPLICIT_RECOVERY_PERMITTED="
        f"{str(contract.explicit_recovery_permitted).lower()}"
    )
    print(
        "RECOVERY_STATE_PROBE_REQUIRED="
        f"{str(contract.recovery_state_probe_required).lower()}"
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
