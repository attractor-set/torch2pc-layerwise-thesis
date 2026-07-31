# ADR-092: final-acknowledgement materialization invocation implementation for `QW-LC4-E`

[Russian version](ADR-092-stage3b-qwake-lc4-e-final-execution-acknowledgement-materialization-invocation-implementation.md)

- **Status:** accepted as a bounded library implementation; no production callsite
- **Date:** 2026-07-31
- **Base commit:** `febfba65d2f200fd2163928643eadd807a6b4d21`

## Context

PR #152 froze the materialization invocation contract and merged as
`febfba65d2f200fd2163928643eadd807a6b4d21`. Independent verification confirmed
four successful CI checks, `124` focused, `325` targeted, and `1372` full tests
with `14` warnings. The final acknowledgement and every other production
artifact remained absent.

The contract requires durable-state classification before the materializer can
be called. This distinguishes a first operation from recovery after an uncertain
response: an already persisted valid file must not be created again.

## Decision

1. Add the implementation package
   `stage3b-qwake-lc4-e-final-execution-acknowledgement-materialization-invocation-implementation-v1`.
2. Implement the library adapter
   `invoke_final_execution_acknowledgement_materialization` without adding a
   production callsite.
3. Classify the exact target before any possible materializer call:
   - an absent target permits exactly one materializer delegation;
   - a valid existing target is treated as completed after exact-byte
     verification, without another materializer call;
   - an invalid existing target fails closed.
4. Use the exact pure prospective-materialization builder, exact materializer,
   and existing persisted-acknowledgement verifier. A direct writer call is
   forbidden.
5. Forbid automatic and blind retry. A materializer error is propagated
   immediately; this implementation performs no second call.
6. Permit explicit recovery only as a new separately authorized operation with
   a fresh durable-state probe.
7. Permit writes only in isolated temporary repository copies used by tests.
   Package verification, import, and static tests remain effect free.
8. Do not create a lease, outcome receipt, command, Docker invocation, or
   execute [local compute](../glossary_EN.md#term-local-compute).

## Boundary

```text
ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_AUTHORING_POST_MERGE_VERIFIED=true
MATERIALIZATION_INVOCATION_CONTRACT_AUTHORED=true
MATERIALIZATION_INVOCATION_IMPLEMENTED=true
MATERIALIZATION_INVOKED=false
MATERIALIZER_CALLED=false
WRITER_CALLED=false
AUTOMATIC_RETRY_FORBIDDEN=true
BLIND_RETRY_FORBIDDEN=true
EXPLICIT_RECOVERY_PERMITTED=true
RECOVERY_STATE_PROBE_REQUIRED=true
VALID_EXISTING_TARGET_TREATED_AS_SUCCESS=true
INVALID_EXISTING_TARGET_FAIL_CLOSED=true
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

A separate authoring slice for the actual operator-bound operation is required
after merge and independent verification. The adapter alone neither authorizes
materialization nor acknowledges [execution](../glossary_EN.md#term-execution).
