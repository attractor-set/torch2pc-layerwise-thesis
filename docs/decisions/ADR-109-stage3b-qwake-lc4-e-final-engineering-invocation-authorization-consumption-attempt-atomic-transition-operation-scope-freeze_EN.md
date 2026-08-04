# ADR-109: freeze the operational scope of the `QW-LC4-E` authorization-consumption atomic transition

[Русская версия](ADR-109-stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-atomic-transition-operation-scope-freeze.md)

- **Status:** accepted as a non-executing freeze of the future operation scope
- **Date:** 2026-08-04
- **Context:** `QW-LC4-E`

## Context

[ADR-108](ADR-108-stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-atomic-transition-authoring_EN.md) implemented `execute_final_engineering_invocation_atomic_transition_once` while leaving its production invocation closed. After PR #176 merged as `3a0cf60e37de80cffdbc397616db6ad437a734e0` and independent verification completed, the transition is post-merge verified. Authorization remains unconsumed, the [attempt](../glossary_EN.md#term-attempt) remains not started, and the final lease v2 remains absent.

## Decision

Freeze the exact future operator-operation scope without performing it. Future operation authoring must construct `AtomicTransitionAdmission` with exactly:

```text
transition_post_merge_verified=true
implementation_merge_commit=3a0cf60e37de80cffdbc397616db6ad437a734e0
operator_identity_kind=local-posix-account
operator_identity=dzmitry-prychyna
authorization_action_phrase=AUTHORIZE_QWAKE_LC4_FINAL_ENGINEERING_INVOCATION_ONCE_AFTER_POST_MERGE_VERIFICATION
persistent_lease_acknowledgement=CLAIM_QWAKE_LC4_ONE_SHOT_PERSISTENT_EVIDENCE_CHAIN_V2
```

After admission construction, at most one future production call to the existing atomic-transition entrypoint is allowed. The only additional argument is `claimed_at_utc`; it must be obtained once after operation admission, use exact UTC `Z` form, and must not be reused after commit or an unknown outcome.

## Preflight order

1. prove post-merge verification for the exact future operation package;
2. verify a clean exact repository and the frozen `Torch2PC` identity;
3. verify immutable transition, authorization, and attempt packages;
4. confirm effective unconsumed authorization and the prepared not-started attempt;
5. verify operator identity and both distinct required phrases;
6. prove absence of the output root, lease v1, lease v2, and durable outcome;
7. obtain one `claimed_at_utc` value;
8. build the exact `AtomicTransitionAdmission`;
9. invoke the atomic-transition entrypoint at most once.

## Effect boundary

This ADR creates only `scope.json` and its registry. It creates no operation module, verifier, tests, or operation record. It does not invoke the atomic transition or persistent writer and creates no lease v2.

The future operation commits only the atomic transition. `invoke_lease_bound_host_runtime` remains after and outside it. Shell-command materialization, direct Docker invocation, and automatic retry are forbidden.

## States

- before operation, authorization is unconsumed, the attempt is not started, and lease v2 is absent;
- a pre-commit failure with proven final-object absence creates no committed effect, but does not permit automatic retry;
- exact lease v2 simultaneously denotes consumed authorization, a started attempt, and committed atomic action; retry is forbidden;
- an invalid or ambiguous final object means `unknown_fail_closed`: [runtime](../glossary_EN.md#term-runtime) invocation and retry are forbidden;
- runtime [execution](../glossary_EN.md#term-execution) does not start inside the atomic operation.

## Future operation-authoring surfaces

```text
src/torch2pc_thesis/stage3b_qwake_lc4_final_engineering_invocation_authorization_consumption_attempt_atomic_transition_operation.py
scripts/verify_stage3b_qwake_lc4_final_engineering_invocation_authorization_consumption_attempt_atomic_transition_operation.py
tests/unit/test_stage3b_qwake_lc4_final_engineering_invocation_authorization_consumption_attempt_atomic_transition_operation.py
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-atomic-transition-operation-v1/operation.json
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-atomic-transition-operation-v1/source-SHA256SUMS
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-atomic-transition-operation-v1/SHA256SUMS
```

This slice creates none of those surfaces.

## Machine boundary

```text
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_POST_MERGE_VERIFIED=true
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_CONSUMED=false
FINAL_ENGINEERING_INVOCATION_PERMITTED=true
FINAL_ENGINEERING_INVOCATION_STARTED=false
FINAL_ENGINEERING_INVOCATION_PERFORMED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_PREPARED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_POST_MERGE_VERIFIED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_SCOPE_FREEZE_POST_MERGE_VERIFIED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_AUTHORED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_POST_MERGE_VERIFIED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_OPERATION_SCOPE_FREEZE_ADMISSIBLE=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_OPERATION_SCOPE_FROZEN=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_OPERATION_SCOPE_RECORD_PRESENT=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_OPERATION_SCOPE_FREEZE_POST_MERGE_VERIFIED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_OPERATION_AUTHORING_ADMISSIBLE=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_OPERATION_AUTHORED=false
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
NEXT_SLICE=QW-LC4-E-final-engineering-invocation-authorization-consumption-attempt-atomic-transition-operation-scope-freeze-commit
POST_MERGE_NEXT_SLICE=QW-LC4-E-final-engineering-invocation-authorization-consumption-attempt-atomic-transition-operation-authoring
```

## Consequences

After ADR-109 merges and is independently verified, only separate non-executing operator-operation authoring becomes admissible. The atomic effect, runtime, `QW-5`, [test-dataset access](../glossary_EN.md#term-test-dataset-access), and publication remain closed.
