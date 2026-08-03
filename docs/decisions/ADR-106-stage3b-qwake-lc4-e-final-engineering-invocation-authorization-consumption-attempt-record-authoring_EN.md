# ADR-106: final engineering-invocation authorization consumption-attempt record authoring for `QW-LC4-E`

[Russian version](ADR-106-stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-record-authoring.md)

- **Status:** accepted as non-executing [attempt](../glossary_EN.md#term-attempt)-record authoring
- **Date:** 2026-08-03
- **Context:** `QW-LC4-E`
- **Predecessor:** ADR-105
- **Verified `main`:** `28b4627436244893195231f55f2d0d5fb2d1062e`

## Context

PR #173 with head `17af7d6f4473af846f2d293192082074cad99cf2` was merged into `main` as
`28b4627436244893195231f55f2d0d5fb2d1062e` at `2026-08-03T19:38:32Z`. Independent post-merge verification
confirmed the single-commit PR graph, two-parent merge graph, exact 13-file
scope, final-head checks, exact SHA-256 identities, twelve frozen packages, the
authorization verifier, `ruff`, four static checks, and 37 targeted tests.

The ADR-105 scope-freeze line is now complete through the derived fact
`consumption_attempt_scope_freeze_post_merge_verified=true`. The one-shot
authorization remains effective and unconsumed. The attempt record, command,
lease v2, durable host outcome, and [runtime](../glossary_EN.md#term-runtime) output are absent.

## Decision

Materialize the distinct canonical record `stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-v1`. The record marks only
`authorization_consumption_attempt_prepared=true`. It is not
[execution](../glossary_EN.md#term-execution), does not consume authorization,
and does not start the attempt.

The record binds:

- verified `main` `28b4627436244893195231f55f2d0d5fb2d1062e`;
- PR #173, its head, exact merge commit, and merge time;
- the frozen ADR-105 scope and exact SHA-256 identities;
- authorization `stage3b-qwake-lc4-e-final-engineering-invocation-authorization-v1` with semantic SHA-256 `sha256:629e87c79f03cd50f4b427d66b873802a06b36efe9def502b50232a474c18014`;
- operator `local-posix-account:dzmitry-prychyna` and separate phrase `AUTHORIZE_QWAKE_LC4_FINAL_ENGINEERING_INVOCATION_ONCE_AFTER_POST_MERGE_VERIFICATION`;
- the sole `invoke_lease_bound_host_runtime` entry point;
- output root, lease-v1/v2 paths, and durable host-outcome path;
- the future atomic boundary for consumption, attempt start, and exclusive
  durable lease-v2 creation.

## Prepared-record state

```text
AUTHORIZATION_CONSUMPTION_ATTEMPT_RECORD_AUTHORED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_RECORD_PRESENT=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_PREPARED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_POST_MERGE_VERIFIED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_ACTION_PERMITTED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_STARTED=false
```

`prepared=true` means that a verifiable intent and exact inputs exist. It does
not mean reservation, ownership, run, or authority consumption.

## Future atomic boundary

After this record's own merge and independent verification, a separate future
slice must first freeze the operational action. Only then may one indivisible
action:

1. consume the authorization;
2. mark the sole attempt started;
3. exclusively and durably create lease v2;
4. verify the exact persisted lease bytes;
5. call `invoke_lease_bound_host_runtime`.

Failure before the atomic transition consumes no authorization, starts no
attempt, and creates no lease. After the transition begins, retry is forbidden
for success, failure, or an uncertain outcome. Every terminal class requires a
durable host-outcome receipt.

## Immutable prohibitions for this slice

This slice does not:

- modify ADR-105 `scope.json` or ADR-104 `authorization.json`;
- consume authorization or start the attempt;
- materialize an invocation command;
- create lease v1/v2, output root, or durable host outcome;
- import or invoke the runtime entry point, Docker, model, or child process;
- open `QW-5`, test-data access, a scientific campaign, or publication.

Negative tests mutate temporary copies only. Frozen
[evidence](../glossary_EN.md#term-evidence) remains unchanged.

## Machine-readable surfaces

```text
src/torch2pc_thesis/stage3b_qwake_lc4_final_engineering_invocation_authorization_consumption_attempt.py
scripts/verify_stage3b_qwake_lc4_final_engineering_invocation_authorization_consumption_attempt.py
tests/unit/test_stage3b_qwake_lc4_final_engineering_invocation_authorization_consumption_attempt.py
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-v1/attempt.json
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-v1/source-SHA256SUMS
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-v1/SHA256SUMS
```

## Machine boundary

```text
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_RECORD_LINE_COMPLETE=true
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_POST_MERGE_VERIFIED=true
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_CONSUMED=false
FINAL_ENGINEERING_INVOCATION_PERMITTED=true
FINAL_ENGINEERING_INVOCATION_STARTED=false
FINAL_ENGINEERING_INVOCATION_PERFORMED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_SCOPE_FROZEN=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_SCOPE_FREEZE_POST_MERGE_VERIFIED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_RECORD_AUTHORING_ADMISSIBLE=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_RECORD_AUTHORED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_RECORD_PRESENT=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_PREPARED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_POST_MERGE_VERIFIED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_ACTION_PERMITTED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_STARTED=false
INVOCATION_COMMAND_MATERIALIZED=false
EXECUTION_LEASE_V1_PRESENT=false
EXECUTION_LEASE_V2_PRESENT=false
DURABLE_HOST_OUTCOME_PRESENT=false
RUNTIME_OUTPUT_PRESENT=false
EXTENSION_ENGINEERING_REPORT_PRESENT=false
QW_LC4_E_COMPLETE=false
QW5_TRANSITION_PERMITTED=false
QW5_SCIENTIFIC_IMAGE_FREEZE_OPEN=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
NEXT_SLICE=QW-LC4-E-final-engineering-invocation-authorization-consumption-attempt-record-authoring-commit
POST_MERGE_NEXT_SLICE=QW-LC4-E-final-engineering-invocation-authorization-consumption-attempt-atomic-transition-scope-freeze
```

## Consequences

The attempt record becomes canonical and prepared but remains ineffective for
the atomic action until its own merge and independent verification.
Authorization remains unconsumed; [local compute](../glossary_EN.md#term-local-compute)
and scientific capabilities remain closed.
