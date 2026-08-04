# ADR-108: authorization-consumption atomic-transition authoring

## Status

Accepted for a separate merge-required authoring slice. The operational effect remains closed.

## Context

[ADR-107](ADR-107-stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-atomic-transition-scope-freeze_EN.md) froze the only commit point: a no-replace hard-link creation of exact, already-fsynced persistent [execution](../glossary_EN.md#term-execution)-lease-v2 bytes. After PR #175 merged and independent verification passed, the scope freeze admits implementation authoring but not the atomic effect itself.

## Decision

Create the distinct `stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-atomic-transition-v1` package with:

- the atomic-transition module;
- a standalone verifier;
- tests, with effectful positive and negative cases restricted to temporary repository copies;
- canonical immutable `transition.json`;
- `source-SHA256SUMS` and `SHA256SUMS`.

The effectful entrypoint is `execute_final_engineering_invocation_atomic_transition_once`. Its presence does not authorize a call. The authoring verifier does not call the entrypoint and does not import `invoke_lease_bound_host_runtime`.

## Implemented commit protocol

A future call must:

1. receive independently established post-merge admission for the exact implementation merge commit;
2. verify the new authorization, prepared [attempt](../glossary_EN.md#term-attempt), ADR-107 scope, and operator identity;
3. verify the distinct authorization action phrase and lease-v2 acknowledgement;
4. build the existing exact persistent lease-v2 schema with `execution_commit` equal to the verified implementation merge commit;
5. reuse the audited writer with `O_CREAT|O_EXCL`, file `fsync`, `hard_link_no_replace`, directory `fsync`, exact-byte verification, and mode `0600` verification;
6. derive `authorization_consumed=true`, `attempt_started=true`, and `atomic_action_committed=true` only from exact final lease-v2 bytes.

[Runtime](../glossary_EN.md#term-runtime) invocation is after and outside this entrypoint. The module does not import the runtime invoker.

## Fail-closed states

- A failure before the commit point leaves authorization unconsumed, the [attempt](../glossary_EN.md#term-attempt) not started, and the final lease absent.
- An already existing exact lease means committed/no-retry.
- A non-equivalent, symbolic, partial, or ambiguous final object means `unknown_fail_closed`; runtime and retry are forbidden.
- A failure after exact lease appearance also means committed/no-retry.

## Authoring boundary

```text
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_POST_MERGE_VERIFIED=true
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_CONSUMED=false
FINAL_ENGINEERING_INVOCATION_STARTED=false
FINAL_ENGINEERING_INVOCATION_PERFORMED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_PREPARED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_POST_MERGE_VERIFIED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_SCOPE_FROZEN=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_SCOPE_FREEZE_POST_MERGE_VERIFIED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_AUTHORING_ADMISSIBLE=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_AUTHORED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_RECORD_PRESENT=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_POST_MERGE_VERIFIED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_OPERATION_SCOPE_FREEZE_ADMISSIBLE=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_ACTION_PERMITTED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_ACTION_COMMITTED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_STARTED=false
INVOCATION_COMMAND_MATERIALIZED=false
EXECUTION_LEASE_V1_PRESENT=false
EXECUTION_LEASE_V2_PRESENT=false
DURABLE_HOST_OUTCOME_PRESENT=false
RUNTIME_OUTPUT_PRESENT=false
QW5_TRANSITION_PERMITTED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
```

## Consequences

After ADR-108 merge and independent post-merge verification, only a separate non-executing `atomic-transition-operation-scope-freeze` is admissible. Neither ADR-108 authoring nor its merge consumes authorization or creates lease v2.
