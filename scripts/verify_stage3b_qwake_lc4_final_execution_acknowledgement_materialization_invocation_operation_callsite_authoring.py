#!/usr/bin/env python3
"""Verify QW-LC4-E invocation-operation callsite authoring."""

from __future__ import annotations

import argparse
from pathlib import Path

from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_callsite_authoring import (
    verify_final_execution_acknowledgement_materialization_invocation_operation_callsite_authoring,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    args = parser.parse_args()

    authoring = verify_final_execution_acknowledgement_materialization_invocation_operation_callsite_authoring(
        args.project_root
    )
    contract = authoring.contract
    gates = authoring.gates

    print("OK: QW-LC4-E acknowledgement materialization invocation operation callsite authoring verified")
    print(f"ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_OPERATION_CALLSITE_AUTHORING_ID={authoring.authoring_id}")
    print(f"ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_OPERATION_CALLSITE_AUTHORING_SHA256={authoring.authoring_sha256}")
    print("ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_OPERATION_IMPLEMENTATION_POST_MERGE_VERIFIED=true")
    print("MATERIALIZATION_INVOCATION_OPERATION_CONTRACT_AUTHORED=true")
    print("MATERIALIZATION_INVOCATION_OPERATION_IMPLEMENTED=true")
    print("MATERIALIZATION_INVOCATION_OPERATION_CALLSITE_CONTRACT_AUTHORED=true")
    print("MATERIALIZATION_INVOCATION_OPERATION_CALLSITE_IMPLEMENTED=false")
    print("PRODUCTION_CALLSITE_PRESENT=false")
    print("MATERIALIZATION_INVOCATION_OPERATION_PERFORMED=false")
    print("OPERATION_DELEGATE_CALL_LIMIT=1")
    print(f"EXACT_PRODUCTION_CALLSITE_RELATIVE={contract.exact_production_callsite_relative_required}")
    print(f"EXACT_PRODUCTION_CALLSITE_SYMBOL={contract.exact_production_callsite_symbol_required}")
    print(f"EXACT_OPERATION_DELEGATE_SYMBOL={contract.exact_operation_delegate_symbol_required}")
    print(f"PROJECT_ROOT_OPTION={contract.project_root_option_required}")
    print(f"OPERATION_JSON_OPTION={contract.operation_json_option_required}")
    print("CANONICAL_PROSPECTIVE_OPERATION_JSON_REQUIRED=true")
    print("STDIN_OPERATION_FORBIDDEN=true")
    print("ENVIRONMENT_FALLBACK_FORBIDDEN=true")
    print("INTERACTIVE_PROMPT_FORBIDDEN=true")
    print("STANDALONE_PREPROBE_FORBIDDEN=true")
    print("DIRECT_INVOCATION_ADAPTER_CALL_FORBIDDEN=true")
    print("DIRECT_MATERIALIZER_CALL_FORBIDDEN=true")
    print("DIRECT_WRITER_CALL_FORBIDDEN=true")
    print("AUTOMATIC_RETRY_FORBIDDEN=true")
    print("BLIND_RETRY_FORBIDDEN=true")
    print("CANONICAL_RESULT_STDOUT_REQUIRED=true")
    print("RESULT_FILE_WRITE_FORBIDDEN=true")
    print("CALLSITE_IMPLEMENTATION_SEPARATE=true")
    print("OPERATION_PERFORMANCE_SEPARATE=true")
    print(f"INVOCATION_ADAPTER_CALLED={str(gates.invocation_adapter_called).lower()}")
    print(f"MATERIALIZATION_INVOKED={str(gates.materialization_invoked).lower()}")
    print(f"MATERIALIZER_CALLED={str(gates.materializer_called).lower()}")
    print(f"WRITER_CALLED={str(gates.writer_called).lower()}")
    print(f"FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUED={str(gates.final_execution_acknowledgement_issued).lower()}")
    print(f"FINAL_EXECUTION_ACKNOWLEDGED={str(gates.final_execution_acknowledged).lower()}")
    print(f"ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED={str(gates.one_shot_engineering_invocation_permitted).lower()}")
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
