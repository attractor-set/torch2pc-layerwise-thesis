#!/usr/bin/env python3
"""Verify the production operation callsite without executing it."""

from __future__ import annotations

import argparse
from pathlib import Path

from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_callsite_implementation import (
    PRODUCTION_CALLSITE_RELATIVE,
    PRODUCTION_CALLSITE_SYMBOL,
    verify_final_execution_acknowledgement_materialization_invocation_operation_callsite_implementation,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    record = verify_final_execution_acknowledgement_materialization_invocation_operation_callsite_implementation(
        args.project_root
    )
    print("OK: QW-LC4-E acknowledgement materialization operation callsite implementation verified")
    print(
        "ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_OPERATION_CALLSITE_"
        f"IMPLEMENTATION_ID={record.implementation_id}"
    )
    print(
        "ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_OPERATION_CALLSITE_"
        f"IMPLEMENTATION_SHA256={record.implementation_sha256}"
    )
    print("ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_OPERATION_CALLSITE_AUTHORING_POST_MERGE_VERIFIED=true")
    print("MATERIALIZATION_INVOCATION_OPERATION_CONTRACT_AUTHORED=true")
    print("MATERIALIZATION_INVOCATION_OPERATION_IMPLEMENTED=true")
    print("MATERIALIZATION_INVOCATION_OPERATION_CALLSITE_CONTRACT_AUTHORED=true")
    print("MATERIALIZATION_INVOCATION_OPERATION_CALLSITE_IMPLEMENTED=true")
    print("PRODUCTION_CALLSITE_PRESENT=true")
    print(f"EXACT_PRODUCTION_CALLSITE_RELATIVE={PRODUCTION_CALLSITE_RELATIVE}")
    print(f"EXACT_PRODUCTION_CALLSITE_SYMBOL={PRODUCTION_CALLSITE_SYMBOL}")
    print("PROJECT_ROOT_OPTION=--project-root")
    print("OPERATION_JSON_OPTION=--operation-json")
    print("CANONICAL_PROSPECTIVE_OPERATION_JSON_REQUIRED=true")
    print("OPERATION_DELEGATE_CALL_LIMIT=1")
    print("OPERATION_RESULT_VALIDATION_REQUIRED=true")
    print("CANONICAL_RESULT_STDOUT_REQUIRED=true")
    print("RESULT_FILE_WRITE_FORBIDDEN=true")
    print("STDOUT_BEFORE_SUCCESS_FORBIDDEN=true")
    print("NONZERO_EXIT_ON_FAILURE_REQUIRED=true")
    print("STDIN_OPERATION_FORBIDDEN=true")
    print("ENVIRONMENT_FALLBACK_FORBIDDEN=true")
    print("INTERACTIVE_PROMPT_FORBIDDEN=true")
    print("STANDALONE_PREPROBE_FORBIDDEN=true")
    print("DIRECT_INVOCATION_ADAPTER_CALL_FORBIDDEN=true")
    print("DIRECT_MATERIALIZER_CALL_FORBIDDEN=true")
    print("DIRECT_WRITER_CALL_FORBIDDEN=true")
    print("AUTOMATIC_RETRY_FORBIDDEN=true")
    print("BLIND_RETRY_FORBIDDEN=true")
    print("MATERIALIZATION_INVOCATION_OPERATION_PERFORMED=false")
    print("INVOCATION_ADAPTER_CALLED=false")
    print("MATERIALIZATION_INVOKED=false")
    print("MATERIALIZER_CALLED=false")
    print("WRITER_CALLED=false")
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
