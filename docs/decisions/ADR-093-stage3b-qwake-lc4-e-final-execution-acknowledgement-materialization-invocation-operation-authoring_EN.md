# ADR-093: operator-operation authoring for final-acknowledgement materialization invocation in `QW-LC4-E`

[Russian version](ADR-093-stage3b-qwake-lc4-e-final-execution-acknowledgement-materialization-invocation-operation-authoring.md)

- **Status:** accepted as a pure contract for a future operator operation; no operation implementation
- **Date:** 2026-07-31
- **Base commit:** `0ace9f1025100fa29ff0af7523fde17674c4852b`

## Context

PR #153 implemented the bounded materialization invocation adapter and merged as
`0ace9f1025100fa29ff0af7523fde17674c4852b`. Independent verification confirmed
four successful CI checks, `144` focused, `345` targeted, and `1392` full tests
with `14` warnings. The adapter exists, but no production callsite,
acknowledgement, or other production artifact exists.

Adapter availability is not authorization for a concrete operation. One future
operator action must be bound to the exact prospective invocation without
confusing the [execution](../glossary_EN.md#term-execution)-acknowledgement phrase with the materialization-action
phrase.

## Decision

1. Add the authoring package
   `stage3b-qwake-lc4-e-final-execution-acknowledgement-materialization-invocation-operation-authoring-v1`.
2. Introduce the exact operation phrase
   `INVOKE_QWAKE_LC4_FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION`. It neither
   replaces nor duplicates the execution-acknowledgement phrase.
3. Bind the future operation to the exact prospective invocation, operator
   identity, and operation-authorization timestamp.
4. Require temporal ordering: the implementation merge precedes acknowledgement;
   operator acknowledgement is no later than operation authorization; operation
   authorization is no later than issuance; issuance is no later than
   materialization.
5. A future operation implementation may call only the exact library adapter and
   at most once. A standalone pre-call probe is forbidden: the adapter-owned
   probe remains authoritative and avoids a check/action gap.
6. Direct materializer and writer calls are forbidden.
7. Automatic and blind retry are forbidden. Explicit recovery is a new separately
   authorized operation with a fresh adapter-owned durable-state classification.
8. Authoring, import, and package verification create no acknowledgement, lease,
   outcome, command, Docker invocation, or [local compute](../glossary_EN.md#term-local-compute).

## Boundary

```text
ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_IMPLEMENTATION_POST_MERGE_VERIFIED=true
MATERIALIZATION_INVOCATION_IMPLEMENTED=true
MATERIALIZATION_INVOCATION_OPERATION_CONTRACT_AUTHORED=true
MATERIALIZATION_INVOCATION_OPERATION_IMPLEMENTED=false
MATERIALIZATION_INVOCATION_OPERATION_PERFORMED=false
INVOCATION_ADAPTER_CALLED=false
MATERIALIZATION_INVOKED=false
MATERIALIZER_CALLED=false
WRITER_CALLED=false
ADAPTER_OWNED_RECOVERY_PROBE_REQUIRED=true
STANDALONE_PREPROBE_FORBIDDEN=true
AUTOMATIC_RETRY_FORBIDDEN=true
BLIND_RETRY_FORBIDDEN=true
FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUED=false
FINAL_EXECUTION_ACKNOWLEDGED=false
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
DURABLE_HOST_OUTCOME_PRESENT=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```

## Consequences

A separate operation-implementation slice is required after merge and independent
verification. The contract itself neither permits nor performs materialization.
