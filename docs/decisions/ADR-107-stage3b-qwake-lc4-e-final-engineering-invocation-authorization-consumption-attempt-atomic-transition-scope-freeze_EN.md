# ADR-107: freeze the atomic authorization-consumption transition scope for the final `QW-LC4-E` engineering invocation

[Russian version](ADR-107-stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-atomic-transition-scope-freeze.md)

- **Status:** accepted as a non-executing atomic-transition scope freeze
- **Date:** 2026-08-03
- **Context:** `QW-LC4-E`
- **Preceded by:** ADR-106
- **Verified `main`:** `5890c755fcf5aa1ae6651f3b592705457b9a9b91`

## Context

PR #174 with head `bc153fb14eb73b18353739cacb5def31a8f4c70a` was merged into `main` as `5890c755fcf5aa1ae6651f3b592705457b9a9b91` at
`2026-08-03T21:20:24Z`. Independent post-merge verification confirmed the exact
one-commit PR graph, two-parent merge graph, 17-file scope, final-head checks,
exact SHA-256 identities, thirteen frozen packages, both standalone verifiers,
`ruff`, four static guards, and 47 targeted tests.

The prepared [attempt](../glossary_EN.md#term-attempt) record is now post-merge verified. Authorization remains
effective and unconsumed, and the attempt is prepared but not started. No
operational action may yet consume authorization, create lease v2, or invoke the
[runtime](../glossary_EN.md#term-runtime).

## Decision

Freeze the exact non-executing scope of the future atomic transition. The three
logical effects—authorization consumption, start of the single attempt, and
durable lease-v2 creation—are not written into three mutable objects. The sole
commit object is the atomic no-replace creation of the fully prepared canonical
lease-v2 file:

```text
results/stage-3/qwake-lc4-runtime-validation-v1-attempt-001.execution-lease-v2.json
```

`authorization_consumed=true` and `consumption_attempt_started=true` are
derived from this path containing the exact expected bytes as a regular `0600`
file with valid lease-v2 semantics. Immutable `authorization.json`,
`attempt.json`, and predecessor `scope.json` records are never rewritten.

## Exact commit protocol

The future implementation must use the already verified
`persist_persistent_execution_lease_v2` mechanism:

1. reverify exact authorization, attempt, [evidence](../glossary_EN.md#term-evidence)-chain, and runtime
   identities, the operator identity, and the distinct authorization phrase;
2. build canonical `PersistentExecutionLeaseV2` bytes in memory;
3. create a temporary regular file in the same directory with
   `O_CREAT|O_EXCL` and mode `0600`;
4. write all canonical bytes and `fsync` the temporary file;
5. create the exact final path with a no-replace hard link to the temporary
   inode;
6. `fsync` the parent directory;
7. reverify the final object's exact bytes, type, and mode.

Successful creation of the final hard link is the sole commit point. Before it,
authorization is unconsumed, the attempt is not started, and lease v2 is absent.
After it, all three logical effects are committed and retry is forbidden even
when the process stops before runtime invocation or terminal-outcome
persistence.

## Distinct operator acknowledgements

The new authorization phrase:

```text
AUTHORIZE_QWAKE_LC4_FINAL_ENGINEERING_INVOCATION_ONCE_AFTER_POST_MERGE_VERIFICATION
```

and the historical lease-v2 acknowledgement:

```text
CLAIM_QWAKE_LC4_ONE_SHOT_PERSISTENT_EVIDENCE_CHAIN_V2
```

are distinct mandatory values. The future operation must verify the former
before commit and build the lease with the exact latter value. Neither replaces
the other.

## Failure and recovery states

- failure before the final hard link does not consume authorization and permits
  a new attempt only when the final path is provably absent;
- an exact final file means the transition committed and retry is forbidden;
- a noncanonical, symbolic, partial, or ambiguous final object means unknown
  state: runtime is closed and retry is forbidden;
- failure after commit but before runtime means consumed authorization and a
  started attempt while runtime itself may remain not started;
- a missing durable outcome after commit is an unknown terminal outcome and
  never permits reinvocation;
- separate recovery may classify and persist an outcome but must not invoke the
  runtime again.

No-replace hard-link support and durable directory `fsync` semantics are
mandatory. Unsupported or ambiguous filesystem behavior fails closed.

## Runtime boundary

`invoke_lease_bound_host_runtime` occurs after the atomic commit and is not part
of it. Exact persisted lease-v2 bytes must be verified before invocation. No
shell command is materialized; direct Docker, historical operation, and lower
host-invoker calls remain forbidden.

## Future program surfaces

```text
src/torch2pc_thesis/stage3b_qwake_lc4_final_engineering_invocation_authorization_consumption_attempt_atomic_transition.py
scripts/verify_stage3b_qwake_lc4_final_engineering_invocation_authorization_consumption_attempt_atomic_transition.py
tests/unit/test_stage3b_qwake_lc4_final_engineering_invocation_authorization_consumption_attempt_atomic_transition.py
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-atomic-transition-v1/transition.json
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-atomic-transition-v1/source-SHA256SUMS
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-atomic-transition-v1/SHA256SUMS
```

This slice neither creates nor invokes those surfaces.

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
AUTHORIZATION_CONSUMPTION_ATTEMPT_RECORD_PRESENT=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_PREPARED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_POST_MERGE_VERIFIED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_SCOPE_FROZEN=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_SCOPE_RECORD_PRESENT=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_SCOPE_FREEZE_POST_MERGE_VERIFIED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_AUTHORING_ADMISSIBLE=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_AUTHORED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_ACTION_PERMITTED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_ACTION_COMMITTED=false
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
NEXT_SLICE=QW-LC4-E-final-engineering-invocation-authorization-consumption-attempt-atomic-transition-scope-freeze-commit
POST_MERGE_NEXT_SLICE=QW-LC4-E-final-engineering-invocation-authorization-consumption-attempt-atomic-transition-authoring
```

## Consequences

Atomicity is reduced to one durable commit object compatible with the existing
lease-bound host invoker. This ADR only freezes the contract. Authorization
remains unconsumed, the attempt remains not started, and `QW-5`, scientific
[execution](../glossary_EN.md#term-execution), [test-dataset access](../glossary_EN.md#term-test-dataset-access) to the test [dataset](../glossary_EN.md#term-dataset), and publication remain closed.
