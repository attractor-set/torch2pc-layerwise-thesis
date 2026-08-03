# ADR-104: author the canonical one-shot authorization for the final `QW-LC4-E` engineering invocation

[Russian version](ADR-104-stage3b-qwake-lc4-e-final-engineering-invocation-authorization-record-authoring.md)

- **Status:** accepted as record authoring; [execution](../glossary_EN.md#term-execution) closed
- **Date:** 2026-08-03
- **Context:** `QW-LC4-E`
- **Preceded by:** ADR-103
- **Verified `main`:** `61f190db2fbd4bf0ee8a58cac8b6841fbecc6cdd`

## Context

PR #171 with head `6093a18156036d8aa470c88844b0580cd3926c4e` was merged into `main` as
`61f190db2fbd4bf0ee8a58cac8b6841fbecc6cdd` at `2026-08-03T17:17:04Z`. Independent post-merge verification
recorded the one-commit PR graph, two-parent merge graph, exact 13-file scope,
successful final-head checks, `ruff`, four static checks, and 27 targeted tests.

The immutable ADR-103 scope freeze is complete through its own merge and
independent post-merge verification. Authoring a new authorization record is
therefore admissible. This authoring does not open a [run](../glossary_EN.md#term-run):
the record remains ineffective until its own merge and independent post-merge
verification.

## Decision

Create a separate canonical record:

```text
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-v1/authorization.json
```

The record has identifier:

```text
stage3b-qwake-lc4-e-final-engineering-invocation-authorization-v1
```

and binds:

- verified `main` `61f190db2fbd4bf0ee8a58cac8b6841fbecc6cdd`;
- PR #171, its head `6093a18156036d8aa470c88844b0580cd3926c4e`, and `2026-08-03T17:17:04Z`;
- Torch2PC `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4`;
- the immutable ADR-103 scope freeze;
- the admission repository seal and canonical admission record;
- immutable image
  `torch2pc-layerwise-thesis@sha256:7da92b8f77f6dc37d42db832c5613ef6149dc488adc5b66465faa33e48ca021d`;
- sole prospective entrypoint `invoke_lease_bound_host_runtime`;
- output root, persistent lease v2, and durable host outcome paths.

## Operator and separate action phrase

The record binds the exact operator:

```text
identity_kind=local-posix-account
identity=dzmitry-prychyna
```

The separate action phrase is:

```text
AUTHORIZE_QWAKE_LC4_FINAL_ENGINEERING_INVOCATION_ONCE_AFTER_POST_MERGE_VERIFICATION
```

The phrase is reserved only by this record. It is not a command and cannot be
used before independent verification of the future merge.

## One-shot contract

The record admits no more than one future [attempt](../glossary_EN.md#term-attempt)
and requires:

1. separate post-merge verification before effective authority exists;
2. atomic authorization consumption with attempt start and exclusive
   persistent lease-v2 creation;
3. one durable host outcome for every terminal class;
4. no retry after consumption, lease creation, or uncertain outcome;
5. no shell, direct Docker, direct lower invoker, or historical operation;
6. no reuse of the engineering or acknowledgement authorizations;
7. `QW-5`, [test-dataset access](../glossary_EN.md#term-test-dataset-access), and publication to remain closed.

## Program surfaces

This slice creates:

```text
src/torch2pc_thesis/stage3b_qwake_lc4_final_engineering_invocation_authorization.py
scripts/verify_stage3b_qwake_lc4_final_engineering_invocation_authorization.py
tests/unit/test_stage3b_qwake_lc4_final_engineering_invocation_authorization.py
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-v1/authorization.json
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-v1/source-SHA256SUMS
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-v1/SHA256SUMS
```

The schema and verifier do not import the [runtime](../glossary_EN.md#term-runtime) entrypoint, invoke Docker,
start a child process, or create runtime artifacts. Negative tests mutate only
temporary copies.

## Issuance state

The record states:

```text
authorization_issued=true
authorization_post_merge_verified=false
final_engineering_invocation_permitted=false
authorization_consumed=false
```

Record issuance therefore is not yet invocation authority.

## Forbidden effects

This slice does not:

- materialize an invocation command;
- consume authorization;
- create persistent lease v1 or v2;
- create a durable host outcome;
- create the output root or runtime output;
- inspect the image;
- invoke Docker, model code, runtime entrypoint, or a child process;
- open `QW-5`, a scientific campaign, test-dataset access, or publication;
- modify an existing frozen package.

## Machine-readable package

```text
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-v1/authorization.json
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-v1/source-SHA256SUMS
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-v1/SHA256SUMS
```

Internal `authorization_sha256` is computed over the canonical object without
the hash field itself. `SHA256SUMS` binds the record and source registry.

## Machine boundary

```text
FINAL_ENGINEERING_INVOCATION_ADMISSION_REPOSITORY_SEAL_COMPLETE=true
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_AUTHORING_SCOPE_FREEZE_COMPLETE=true
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_AUTHORED=true
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_RECORD_PRESENT=true
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_ISSUED=true
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_POST_MERGE_VERIFIED=false
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_CONSUMED=false
FINAL_ENGINEERING_INVOCATION_PERMITTED=false
FINAL_ENGINEERING_INVOCATION_STARTED=false
FINAL_ENGINEERING_INVOCATION_PERFORMED=false
OPERATOR_PHRASE_RESERVED=true
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
NEXT_SLICE=QW-LC4-E-final-engineering-invocation-authorization-record-authoring-commit
POST_MERGE_NEXT_SLICE=QW-LC4-E-final-engineering-invocation-authorization-consumption-attempt-scope-freeze
```

## Sequence

```text
authorization record authoring
→ merge and independent post-merge verification
→ authorization consumption/attempt scope freeze
→ atomic consumption, attempt start, and lease v2
→ invoke_lease_bound_host_runtime
→ durable host outcome
→ sealed extension engineering report
→ QW-5 eligibility decision
```

## Consequences

The new record is distinct from historical authorizations, canonical, and
bound to the exact operator. Before future post-merge verification it does not
permit [execution](../glossary_EN.md#term-execution), [local compute](../glossary_EN.md#term-local-compute),
or a scientific campaign.
