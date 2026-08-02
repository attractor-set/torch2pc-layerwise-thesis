#!/usr/bin/env python3
"""Verify QW-LC4-E production-callsite execution authoring."""

from __future__ import annotations

import argparse
from pathlib import Path

from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authoring import (
    verify_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authoring,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    args = parser.parse_args()

    authoring = verify_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authoring(
        args.project_root
    )
    contract = authoring.contract
    gates = authoring.gates

    print("OK: QW-LC4-E acknowledgement materialization operation callsite execution authoring verified")
    print(f"ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_OPERATION_CALLSITE_EXECUTION_AUTHORING_ID={authoring.authoring_id}")
    print(f"ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_OPERATION_CALLSITE_EXECUTION_AUTHORING_SHA256={authoring.authoring_sha256}")
    print("ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_OPERATION_CALLSITE_IMPLEMENTATION_POST_MERGE_VERIFIED=true")
    print("MATERIALIZATION_INVOCATION_OPERATION_CALLSITE_IMPLEMENTED=true")
    print("PRODUCTION_CALLSITE_PRESENT=true")
    print("MATERIALIZATION_INVOCATION_OPERATION_CALLSITE_EXECUTION_CONTRACT_AUTHORED=true")
    print("MATERIALIZATION_INVOCATION_OPERATION_CALLSITE_EXECUTION_AUTHORIZED=false")
    print("PRODUCTION_CALLSITE_EXECUTED=false")
    print("MATERIALIZATION_INVOCATION_OPERATION_CALLSITE_EXECUTION_PERFORMED=false")
    print(f"EXACT_PRODUCTION_CALLSITE_RELATIVE={contract.exact_production_callsite_relative_required}")
    print(f"EXACT_PRODUCTION_CALLSITE_SYMBOL={contract.exact_production_callsite_symbol_required}")
    print(f"EXACT_OPERATION_DELEGATE_SYMBOL={contract.exact_operation_delegate_symbol_required}")
    print(f"EXACT_EXECUTION_PHRASE={contract.exact_execution_phrase_required}")
    print(f"FUTURE_EXECUTION_AUTHORIZATION_RELATIVE={contract.exact_future_authorization_relative_required}")
    print(f"FUTURE_OPERATION_JSON_RELATIVE={contract.exact_future_operation_json_relative_required}")
    print(f"PROJECT_ROOT_OPTION={contract.project_root_option_required}")
    print(f"OPERATION_JSON_OPTION={contract.operation_json_option_required}")
    print("EXECUTION_AUTHORIZATION_SEPARATE=true")
    print("EXECUTION_AUTHORIZATION_POST_MERGE_VERIFICATION_REQUIRED=true")
    print("OPERATION_JSON_SHA256_PINNING_REQUIRED=true")
    print("EXACT_ARGV_REQUIRED=true")
    print("SHELL_INTERPRETATION_FORBIDDEN=true")
    print("CWD_EXACT_PROJECT_ROOT_REQUIRED=true")
    print(f"EXECUTION_ATTEMPT_LIMIT={contract.execution_attempt_limit}")
    print("AUTOMATIC_RETRY_FORBIDDEN=true")
    print("BLIND_RETRY_FORBIDDEN=true")
    print("ACKNOWLEDGEMENT_ABSENCE_REQUIRED_BEFORE_ATTEMPT=true")
    print("RUNTIME_OUTPUT_ABSENCE_REQUIRED_BEFORE_ATTEMPT=true")
    print("RUNTIME_STAGING_ABSENCE_REQUIRED_BEFORE_ATTEMPT=true")
    print("SUCCESS_REQUIRES_SINGLE_CANONICAL_STDOUT_OBJECT=true")
    print("RESULT_FILE_WRITE_FORBIDDEN=true")
    print("AUTHORING_EFFECTS_FORBIDDEN=true")
    print("PRODUCTION_CALLSITE_EXECUTION_FORBIDDEN=true")
    print("OPERATION_PERFORMANCE_FORBIDDEN=true")
    print(f"MATERIALIZATION_INVOCATION_OPERATION_PERFORMED={str(gates.materialization_invocation_operation_performed).lower()}")
    print(f"INVOCATION_ADAPTER_CALLED={str(gates.invocation_adapter_called).lower()}")
    print(f"MATERIALIZATION_INVOKED={str(gates.materialization_invoked).lower()}")
    print(f"MATERIALIZER_CALLED={str(gates.materializer_called).lower()}")
    print(f"WRITER_CALLED={str(gates.writer_called).lower()}")
    print(f"FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUED={str(gates.final_execution_acknowledgement_issued).lower()}")
    print(f"FINAL_EXECUTION_ACKNOWLEDGED={str(gates.final_execution_acknowledged).lower()}")
    print(f"EXECUTION_LEASE_MATERIALIZED={str(gates.execution_lease_materialized).lower()}")
    print(f"DURABLE_HOST_OUTCOME_PRESENT={str(gates.durable_host_outcome_present).lower()}")
    print(f"AUTHORIZATION_CONSUMED={str(gates.authorization_consumed).lower()}")
    print(f"RUNTIME_EXECUTION_STARTED={str(gates.runtime_execution_started).lower()}")
    print(f"RUNTIME_EXECUTION_PERFORMED={str(gates.runtime_execution_performed).lower()}")
    print(f"IMAGE_INSPECTION_PERFORMED={str(gates.image_inspection_performed).lower()}")
    print(f"INVOCATION_COMMAND_MATERIALIZED={str(gates.invocation_command_materialized).lower()}")
    print(f"DOCKER_RUN_PERFORMED={str(gates.docker_run_performed).lower()}")
    print(f"LOCAL_COMPUTE_EXECUTION_OPEN={str(gates.local_compute_execution_open).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
