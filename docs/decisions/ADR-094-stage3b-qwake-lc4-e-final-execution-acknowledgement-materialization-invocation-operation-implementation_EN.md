# ADR-094: final-acknowledgement materialization invocation-operation implementation for `QW-LC4-E`

[Russian version](ADR-094-stage3b-qwake-lc4-e-final-execution-acknowledgement-materialization-invocation-operation-implementation.md)

- **Status:** accepted as a bounded library implementation; no production callsite
- **Date:** 2026-07-31
- **Base commit:** `5ee6d2346e558be19cfdf79e8a77b0568475bf4c`

## Context

PR #154 froze the distinct operator-operation contract and merged as
`5ee6d2346e558be19cfdf79e8a77b0568475bf4c`. Independent verification confirmed
four successful CI checks, `162` focused, `363` targeted, and `1410` full tests
with `14` warnings. No operation, final acknowledgement, or other production
artifact existed.

The contract requires implementation to accept an already built operation
object, verify its phrase, operator, time, and exact prospective invocation, and
then call only the existing adapter. A standalone durable-state probe is
forbidden because the adapter owns that classification.

## Decision

1. Add the implementation package
   `stage3b-qwake-lc4-e-final-execution-acknowledgement-materialization-invocation-operation-implementation-v1`.
2. Implement the library function
   `perform_final_execution_acknowledgement_materialization_invocation_operation`.
3. Validate the complete prospective operation through the frozen ADR-093
   contract before delegation.
4. Delegate exactly once to
   `invoke_final_execution_acknowledgement_materialization`.
5. Do not perform a standalone probe, directly call the materializer or writer,
   or add a production callsite.
6. Accept both valid adapter outcomes: new materialization and exact reuse of an
   already existing acknowledgement.
7. Propagate adapter failure immediately without automatic or blind retry.
8. Permit effectful tests only inside isolated temporary repository copies.
   Package verification and import remain effect free.
9. Do not create a lease, outcome receipt, command, Docker invocation, or
   execute [local compute](../glossary_EN.md#term-local-compute).

## Boundary

```text
ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_OPERATION_AUTHORING_POST_MERGE_VERIFIED=true
MATERIALIZATION_INVOCATION_OPERATION_CONTRACT_AUTHORED=true
MATERIALIZATION_INVOCATION_OPERATION_IMPLEMENTED=true
MATERIALIZATION_INVOCATION_OPERATION_PERFORMED=false
INVOCATION_ADAPTER_CALLED=false
ADAPTER_CALL_LIMIT=1
STANDALONE_PREPROBE_FORBIDDEN=true
DIRECT_MATERIALIZER_CALL_FORBIDDEN=true
DIRECT_WRITER_CALL_FORBIDDEN=true
AUTOMATIC_RETRY_FORBIDDEN=true
BLIND_RETRY_FORBIDDEN=true
VALID_EXISTING_TARGET_TREATED_AS_SUCCESS=true
INVALID_EXISTING_TARGET_FAIL_CLOSED=true
PRODUCTION_CALLSITE_PRESENT=false
MATERIALIZATION_INVOKED=false
MATERIALIZER_CALLED=false
WRITER_CALLED=false
FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUED=false
FINAL_EXECUTION_ACKNOWLEDGED=false
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
DURABLE_HOST_OUTCOME_PRESENT=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
IMAGE_INSPECTION_PERFORMED=false
INVOCATION_COMMAND_MATERIALIZED=false
DOCKER_RUN_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```

## Consequences

A separate production-callsite authoring slice is required after merge and
independent verification. The library function alone neither permits nor
performs acknowledgement materialization or [execution](../glossary_EN.md#term-execution).
