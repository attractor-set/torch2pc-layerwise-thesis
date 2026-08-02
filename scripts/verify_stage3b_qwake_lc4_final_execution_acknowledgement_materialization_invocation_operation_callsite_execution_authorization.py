#!/usr/bin/env python3
"""Verify the frozen callsite execution authorization without effects."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authorization import (
    AUTHORIZATION_RELATIVE,
    OPERATION_JSON_RELATIVE,
    verify_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authorization,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Verify one unconsumed final acknowledgement materialization "
            "operation-callsite execution authorization."
        )
    )
    parser.add_argument("--project-root", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    authorization = verify_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authorization(
        args.project_root
    )
    print(
        "OK: QW-LC4-E acknowledgement materialization operation callsite "
        "execution authorization verified"
    )
    print(f"EXECUTION_AUTHORIZATION_ID={authorization.authorization_id}")
    print(f"EXECUTION_AUTHORIZATION_SHA256={authorization.authorization_sha256}")
    print(f"EXECUTION_AUTHORIZATION_PHRASE={authorization.authorization_phrase}")
    print(f"EXECUTION_AUTHORIZATION_OPERATOR_IDENTITY={authorization.operator_identity}")
    print(
        "EXECUTION_AUTHORIZATION_ISSUED_AT_UTC="
        f"{authorization.authorization_issued_at_utc}"
    )
    print(f"EXECUTION_AUTHORIZATION_RELATIVE={AUTHORIZATION_RELATIVE.as_posix()}")
    print(f"CANONICAL_OPERATION_JSON_RELATIVE={OPERATION_JSON_RELATIVE.as_posix()}")
    print(
        "CANONICAL_OPERATION_JSON_SHA256="
        f"{authorization.source.operation_json_sha256}"
    )
    print("EXECUTION_AUTHORING_POST_MERGE_VERIFIED=true")
    print("EXECUTION_AUTHORIZATION_RECORD_PRESENT=true")
    print("EXECUTION_AUTHORIZATION_ISSUED=true")
    print("CANONICAL_OPERATION_JSON_MATERIALIZED=true")
    print("EXECUTION_AUTHORIZATION_POST_MERGE_VERIFIED=false")
    print("MATERIALIZATION_INVOCATION_OPERATION_CALLSITE_EXECUTION_AUTHORIZED=false")
    print("PRODUCTION_CALLSITE_PRESENT=true")
    print("PRODUCTION_CALLSITE_EXECUTED=false")
    print("MATERIALIZATION_INVOCATION_OPERATION_CALLSITE_EXECUTION_PERFORMED=false")
    print("AUTHORIZATION_SINGLE_USE=true")
    print("AUTHORIZATION_CONSUMPTION_REQUIRED_AT_ATTEMPT_START=true")
    print("AUTHORIZATION_EFFECTIVE_ONLY_AFTER_POST_MERGE_VERIFICATION=true")
    print("EXECUTION_COMMIT_IS_AUTHORIZATION_MERGE_COMMIT=true")
    print("EXACT_ARGV_REQUIRED=true")
    print("SHELL_INTERPRETATION_FORBIDDEN=true")
    print("CWD_EXACT_PROJECT_ROOT_REQUIRED=true")
    print("EXECUTION_ATTEMPT_LIMIT=1")
    print("AUTOMATIC_RETRY_FORBIDDEN=true")
    print("BLIND_RETRY_FORBIDDEN=true")
    print("FAILURE_AFTER_CONSUMPTION_RETRY_FORBIDDEN=true")
    print("PRODUCTION_CALLSITE_EXECUTION_FORBIDDEN=true")
    print("OPERATION_PERFORMANCE_FORBIDDEN=true")
    print("MATERIALIZATION_INVOCATION_OPERATION_PERFORMED=false")
    print("INVOCATION_ADAPTER_CALLED=false")
    print("MATERIALIZATION_INVOKED=false")
    print("MATERIALIZER_CALLED=false")
    print("WRITER_CALLED=false")
    print("FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUED=false")
    print("FINAL_EXECUTION_ACKNOWLEDGED=false")
    print("EXECUTION_LEASE_MATERIALIZED=false")
    print("DURABLE_HOST_OUTCOME_PRESENT=false")
    print("AUTHORIZATION_CONSUMED=false")
    print("RUNTIME_EXECUTION_STARTED=false")
    print("RUNTIME_EXECUTION_PERFORMED=false")
    print("IMAGE_INSPECTION_PERFORMED=false")
    print("INVOCATION_COMMAND_MATERIALIZED=false")
    print("DOCKER_RUN_PERFORMED=false")
    print("LOCAL_COMPUTE_EXECUTION_OPEN=false")
    print(f"NEXT_SLICE={authorization.next_slice}")
    print(f"POST_MERGE_NEXT_SLICE={authorization.post_merge_next_slice}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
