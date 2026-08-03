# ADR-105: final engineering-invocation authorization consumption-attempt scope freeze for `QW-LC4-E`

[Russian version](ADR-105-stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-scope-freeze.md)

- **Status:** accepted as a scope freeze; [execution](../glossary_EN.md#term-execution) not started
- **Date:** 2026-08-03
- **Context:** `QW-LC4-E`
- **Predecessor:** ADR-104
- **Verified `main`:** `47bb24dc8fa95292be33428ba8bc7ee598c49b1e`

## Context

PR #172 with head `220ce31235a28d1583f90cde5acd8f87ca5c2752`
was merged into `main` as
`47bb24dc8fa95292be33428ba8bc7ee598c49b1e` at
`2026-08-03T18:18:06Z`. Independent post-merge verification confirmed the
single-commit PR graph, two-parent merge graph, exact 17-file scope, final-head
checks, exact SHA-256 identities, eleven frozen packages, the standalone
authorization verifier, `ruff`, four static checks, and 37 targeted tests.

The canonical authorization record remains an immutable pre-merge document
with `authorization_post_merge_verified=false` and
`final_engineering_invocation_permitted=false`. Effective one-shot authority is
derived only from the exact PR #172 merge and independent post-merge
verification. The current derived state therefore has
`authorization_post_merge_verified=true`,
`final_engineering_invocation_permitted=true`, and
`authorization_consumed=false`.

Effective authority is not consumption. The [attempt](../glossary_EN.md#term-attempt), invocation command,
persistent lease v2, durable host outcome, and [runtime](../glossary_EN.md#term-runtime) output remain absent.

## Goal of this slice

This slice freezes only:

1. exact inputs for future authoring of one consumption attempt;
2. the sole admissible future attempt-record surfaces;
3. the distinction between record preparation and the atomic operational
   boundary;
4. exact-operator and separate-action-phrase preconditions;
5. atomic authorization consumption, attempt start, and exclusive persistent
   lease-v2 creation;
6. failure classes before and after the atomic boundary;
7. retry prohibition after consumption, lease creation, or uncertain outcome;
8. forbidden effects of the current scope freeze;
9. acceptance criteria for the future attempt-record authoring slice.

It creates no attempt schema, verifier, tests, or attempt record and does not
consume the authorization.

## Admissible inputs

The future attempt-record authoring slice must bind without modification:

- verified `main`
  `47bb24dc8fa95292be33428ba8bc7ee598c49b1e`;
- PR #172, its head
  `220ce31235a28d1583f90cde5acd8f87ca5c2752`, merge commit, and time
  `2026-08-03T18:18:06Z`;
- Torch2PC
  `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4`;
- authorization
  `stage3b-qwake-lc4-e-final-engineering-invocation-authorization-v1` with
  semantic SHA-256
  `sha256:629e87c79f03cd50f4b427d66b873802a06b36efe9def502b50232a474c18014`;
- operator `local-posix-account:dzmitry-prychyna` and separate phrase
  `AUTHORIZE_QWAKE_LC4_FINAL_ENGINEERING_INVOCATION_ONCE_AFTER_POST_MERGE_VERIFICATION`;
- the canonical admission record, repository seal, immutable image, and sole
  entry point `invoke_lease_bound_host_runtime`;
- output root
  `results/stage-3/qwake-lc4-runtime-validation-v1-attempt-001`;
- persistent lease v2
  `results/stage-3/qwake-lc4-runtime-validation-v1-attempt-001.execution-lease-v2.json`;
- durable host outcome
  `results/stage-3/qwake-lc4-runtime-validation-v1-attempt-001.host-outcome.json`.

Historical authorizations are not authority sources. They are admissible only
as [evidence](../glossary_EN.md#term-evidence) of reuse prohibition.

## Future authoring surfaces

Only the future separate attempt-record authoring slice may create:

```text
src/torch2pc_thesis/stage3b_qwake_lc4_final_engineering_invocation_authorization_consumption_attempt.py
scripts/verify_stage3b_qwake_lc4_final_engineering_invocation_authorization_consumption_attempt.py
tests/unit/test_stage3b_qwake_lc4_final_engineering_invocation_authorization_consumption_attempt.py
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-v1/attempt.json
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-v1/source-SHA256SUMS
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-v1/SHA256SUMS
```

The schema and verifier must remain pure: they may not import the runtime entry
point, invoke Docker or a child process, or create operational artifacts.
Negative tests may mutate temporary copies only.

## Future attempt-record contract

The future record must:

1. have a new attempt identifier and its own semantic SHA-256;
2. bind the exact authorization, operator, action phrase, verified `main`,
   admission, image, runtime entry point, and all operational-boundary paths;
3. set `consumption_attempt_prepared=true` while preserving
   `authorization_consumed=false`, `consumption_attempt_started=false`,
   `invocation_command_materialized=false`, and absence of lease v2;
4. remain ineffective as permission for the atomic action until its own merge
   and independent post-merge verification;
5. forbid shell invocation, direct Docker, direct lower-invoker calls, and the
   historical operation;
6. require the exact operator and exact separate phrase at the future
   operational boundary;
7. permit only one atomic operation: authorization consumption, [attempt](../glossary_EN.md#term-attempt)
   start, and exclusive durable lease-v2 creation must be one indivisible
   transition before the runtime entry point;
8. permit failure before the atomic transition without consumption, attempt
   start, or lease creation;
9. forbid every retry after the atomic transition begins, regardless of
   success, failure, or uncertain outcome;
10. require one durable host-outcome receipt for every terminal class;
11. grant no `QW-5`, scientific-campaign, test-[dataset](../glossary_EN.md#term-dataset), or publication
    authority.

Materializing the future attempt record is preparation, not consumption.
Consumption is admissible only in a separate future operational action after
the attempt record has merged and passed independent post-merge verification.

## Forbidden effects of this slice

The current slice forbids:

- modifying the canonical authorization record;
- creating an attempt schema, verifier, tests, or attempt record;
- consuming the authorization or starting the attempt;
- materializing an invocation command;
- creating persistent lease v1 or v2;
- creating a durable host outcome;
- creating the output root or runtime output;
- image inspection, Docker, model, or child-process execution;
- modifying an existing frozen package;
- opening `QW-5`, `C1`, `C2`, `C3`, `R`, test-data access, or publication.

## Acceptance criteria for future attempt-record authoring

The future slice is accepted only if:

1. every input is verified by exact identity and SHA-256;
2. the attempt record is canonical and has a verifiable semantic SHA-256;
3. the authorization is provably post-merge verified, effective, and
   unconsumed;
4. record preparation does not modify the authorization or start the attempt;
5. command, lease v2, host outcome, output root, and runtime output remain
   absent;
6. the atomic operational boundary and failure classes are unambiguous;
7. retry after consumption, lease creation, or uncertain outcome is forbidden;
8. the runtime entry point, Docker, and model are not imported or invoked;
9. negative tests operate only on temporary copies;
10. `QW-5` and scientific capabilities remain closed.

## Machine-readable freeze

```text
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-scope-freeze-v1/scope.json
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-scope-freeze-v1/SHA256SUMS
```

## Sequence

```text
authorization consumption-attempt scope freeze
→ consumption-attempt record authoring
→ attempt-record merge and independent verification
→ atomic authorization consumption, attempt start, and exclusive lease v2
→ invoke_lease_bound_host_runtime
→ durable host outcome
→ sealed extension engineering report
→ QW-5 eligibility decision
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
AUTHORIZATION_CONSUMPTION_ATTEMPT_RECORD_PRESENT=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_PREPARED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_POST_MERGE_VERIFIED=false
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
NEXT_SLICE=QW-LC4-E-final-engineering-invocation-authorization-consumption-attempt-scope-freeze-commit
POST_MERGE_NEXT_SLICE=QW-LC4-E-final-engineering-invocation-authorization-consumption-attempt-record-authoring
```

## Consequences

This ADR does not consume the authorization and is not a [run](../glossary_EN.md#term-run).
It only constrains future attempt-record preparation to exact inputs, surfaces,
and atomic semantics. Effective authority remains unconsumed, while
[local compute](../glossary_EN.md#term-local-compute) and all scientific
capabilities remain closed.
