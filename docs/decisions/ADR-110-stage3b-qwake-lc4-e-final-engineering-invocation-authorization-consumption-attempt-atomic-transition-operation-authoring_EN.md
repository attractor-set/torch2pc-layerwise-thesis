# ADR-110: combined authoring of the one-shot `QW-LC4-E` atomic-transition operation

[Русская версия](ADR-110-stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-atomic-transition-operation-authoring.md)

- **Status:** accepted as non-executing operation and admission authoring
- **Date:** 2026-08-04
- **Context:** `QW-LC4-E`

## Context

[ADR-109](ADR-109-stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-atomic-transition-operation-scope-freeze_EN.md) froze the exact future operator-operation scope. PR #177 merged as `e33448d10ced2bffd1e48449e6da46b2de938141` with head `b3aa449c138285ce065a3a2920fac19f15134207` at `2026-08-04T02:14:33Z` and passed independent verification. Authorization remains unconsumed, the [attempt](../glossary_EN.md#term-attempt) remains not started, and lease v2 is absent.

To stop excessive process fragmentation, the operation module, immutable record, admission contract, verifier, and tests are combined in one non-executing PR. Separate implementation and admission PRs are not required after it.

## Decision

Add the entrypoint:

```text
execute_final_engineering_invocation_atomic_transition_operation_once
```

It accepts `project_root` and `AtomicTransitionOperationAdmission`. Admission must prove:

```text
operation_post_merge_verified=true
operation_implementation_merge_commit=<exact future ADR-110 merge commit>
repository_head=<the same commit>
worktree_and_index_clean=true
torch2pc_head=b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4
operator_identity_kind=local-posix-account
operator_identity=dzmitry-prychyna
authorization_action_phrase=AUTHORIZE_QWAKE_LC4_FINAL_ENGINEERING_INVOCATION_ONCE_AFTER_POST_MERGE_VERIFICATION
persistent_lease_acknowledgement=CLAIM_QWAKE_LC4_ONE_SHOT_PERSISTENT_EVIDENCE_CHAIN_V2
```

After full admission the wrapper:

1. verifies the immutable ADR-110 package and bound source identities;
2. verifies the immutable ADR-109 scope and ADR-108 transition;
3. classifies existing final objects before obtaining time;
4. obtains exactly one UTC `claimed_at_utc` value with a `Z` suffix;
5. builds the exact `AtomicTransitionAdmission` with `implementation_merge_commit=3a0cf60e37de80cffdbc397616db6ad437a734e0`;
6. delegates exactly one call to `execute_final_engineering_invocation_atomic_transition_once`;
7. returns the verified state without starting [runtime](../glossary_EN.md#term-runtime).

## Combined admission contract

The admission contract is in the same module and immutable record as the wrapper. Independent verification of the future merge must supply the exact ADR-110 merge commit as both `operation_implementation_merge_commit` and `repository_head`. `e33448d10ced2bffd1e48449e6da46b2de938141` is not accepted as the terminal operation-implementation identity.

The clean-worktree Boolean does not replace external verification. The production procedure must independently prove the exact clean `HEAD`, index, worktree, and frozen `Torch2PC`, then construct admission from those verified values.

## One-shot states

- an exact lease v2 already present before wrapper invocation means the transition is already committed; the clock is not read, delegation does not occur, and retry is forbidden;
- an inexact, symbolic, incorrectly protected, or ambiguous lease v2 means `unknown_fail_closed`; the clock is not read, [runtime](../glossary_EN.md#term-runtime) invocation and retry are forbidden;
- a pre-existing output root, lease v1, or durable outcome makes the boundary ambiguous and closes the operation;
- a pre-commit failure with proven final-object absence does not permit automatic retry;
- success creates exact lease v2, from which authorization consumption, attempt start, and atomic-action commit are derived;
- `invoke_lease_bound_host_runtime` remains a separate later action and is not called by the wrapper.

## Current PR boundary

This PR creates the module, verifier, tests, `operation.json`, `source-SHA256SUMS`, `SHA256SUMS`, and bilingual documentation. It does not invoke the production operation, transition, or writer. Effectful tests run only in temporary repository copies.

```text
AUTHORIZATION_CONSUMED=false
CONSUMPTION_ATTEMPT_STARTED=false
ATOMIC_TRANSITION_OPERATION_SCOPE_FREEZE_POST_MERGE_VERIFIED=true
ATOMIC_TRANSITION_OPERATION_AUTHORING_ADMISSIBLE=true
ATOMIC_TRANSITION_OPERATION_AUTHORED=true
ATOMIC_TRANSITION_OPERATION_MODULE_CREATED=true
ATOMIC_TRANSITION_OPERATION_VERIFIER_CREATED=true
ATOMIC_TRANSITION_OPERATION_TESTS_CREATED=true
ATOMIC_TRANSITION_OPERATION_RECORD_CREATED=true
COMBINED_OPERATION_ADMISSION_CONTRACT_CREATED=true
ATOMIC_TRANSITION_OPERATION_POST_MERGE_VERIFIED=false
CONSUMPTION_ATTEMPT_ATOMIC_ACTION_PERMITTED=false
CONSUMPTION_ATTEMPT_ATOMIC_ACTION_COMMITTED=false
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

After ADR-110 merges and passes independent verification, no separate admission PR is required. The next admissible action is one externally initiated fail-closed atomic-transition operation. It still does not include runtime [execution](../glossary_EN.md#term-execution): after durable lease-v2 commit, a separate decision is required before invoking the lease-bound host runtime.
