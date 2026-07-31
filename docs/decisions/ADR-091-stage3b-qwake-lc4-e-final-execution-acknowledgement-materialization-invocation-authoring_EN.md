# ADR-091: final-acknowledgement materialization invocation authoring for `QW-LC4-E`

[Russian version](ADR-091-stage3b-qwake-lc4-e-final-execution-acknowledgement-materialization-invocation-authoring.md)

- **Status:** accepted as a static invocation contract; materializer not called
- **Date:** 2026-07-30
- **Base commit:** `7d5e5058af6a845cf4a6add2e7fe199894f48b24`

## Context

PR #151 implemented the narrow final-acknowledgement materializer, was merged as
`7d5e5058af6a845cf4a6add2e7fe199894f48b24`, and passed independent
post-merge verification. On an explicit call, the implementation delegates
exactly one write to the existing atomic writer and reverifies the persisted
bytes exactly once. No production callsite or acknowledgement file exists.

The next slice must define the sole admissible invocation without combining the
adapter implementation with the durable state change. A failure after the write
but before the caller receives the result is especially important: a blind
retry would make the already-performed effect ambiguous.

## Decision

1. Add the static package
   `stage3b-qwake-lc4-e-final-execution-acknowledgement-materialization-invocation-authoring-v1`.
2. Bind it to the exact PR #151 merge verification: head, base, merge, timestamp,
   `18` files, `1997` additions, `108` focused, `309` targeted, and `1356` full
   tests with `14` warnings and four successful CI checks.
3. Freeze the exact pure prospective-materialization builder and sole
   materializer symbols. A direct writer call from the future invocation
   adapter is forbidden.
4. Require the explicit operator phrase, operator/issuer/materializer
   identities, and ordered UTC timestamps. The issuer and materializer must be
   the same identity.
5. Limit the future adapter to one materializer call and forbid a production
   callsite in this authoring slice.
6. Forbid automatic and blind retry. This does not forbid explicit recovery
   after durable-state inspection:
   - if the target is absent, another [attempt](../glossary_EN.md#term-attempt) requires separate explicit
     authorization;
   - if the target exists and passes exact verification, the operation is
     treated as successful without calling the materializer again;
   - if the target exists but fails verification, the system fails closed and
     requires a separate recovery procedure.
7. Do not call the materializer or writer, persist the acknowledgement,
   materialize a lease, persist an outcome, inspect an image, materialize a
   command, invoke Docker, or execute [local compute](../glossary_EN.md#term-local-compute) in this slice.

## Boundary

```text
MATERIALIZATION_IMPLEMENTATION_POST_MERGE_VERIFIED=true
ACKNOWLEDGEMENT_MATERIALIZATION_IMPLEMENTED=true
MATERIALIZATION_INVOCATION_CONTRACT_AUTHORED=true
MATERIALIZATION_INVOCATION_IMPLEMENTED=false
MATERIALIZATION_INVOKED=false
MATERIALIZER_CALLED=false
WRITER_CALLED=false
AUTOMATIC_RETRY_FORBIDDEN=true
BLIND_RETRY_FORBIDDEN=true
EXPLICIT_RECOVERY_PERMITTED=true
RECOVERY_STATE_PROBE_REQUIRED=true
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

After ADR-091 is merged and independently verified, a separate invocation-adapter
implementation slice may open. Even that implementation must not automatically
call the materializer: the actual operator-bound materialization remains a
separate one-shot operation preceded by durable-state inspection.
