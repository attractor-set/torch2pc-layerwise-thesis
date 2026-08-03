# ADR-103: final engineering-invocation one-shot authorization-authoring scope freeze for `QW-LC4-E`

[Russian version](ADR-103-stage3b-qwake-lc4-e-final-engineering-invocation-authorization-authoring-scope-freeze.md)

- **Status:** accepted as a scope freeze; [execution](../glossary_EN.md#term-execution) closed
- **Date:** 2026-08-03
- **Context:** `QW-LC4-E`
- **Predecessor:** ADR-102
- **Verified `main`:** `a5b96edb1f82485561e0f52d6a98432d55ae8609`

## Context

PR #170 with head `6201997a71428bdb873d95d76c5b0882be532b2a`
was merged into `main` as
`a5b96edb1f82485561e0f52d6a98432d55ae8609` at
`2026-08-03T16:16:32Z`. Independent post-merge verification confirmed the
single-commit PR graph, two-parent merge graph, exact 14-file scope, acceptable
final-head checks, `ruff`, four static checks, and 27 targeted tests.

The two-file admission repository seal remains an immutable pre-merge receipt
with `repository_seal_complete=false`. Its completion is derived from the exact
PR #170 merge and independent post-merge verification. This permits only a
separate freeze of the future new-authorization authoring scope. The
authorization, operator phrase, invocation command, and [runtime](../glossary_EN.md#term-runtime) artifacts
remain absent.

## Goal of this slice

This slice freezes only:

1. exact repository and [evidence](../glossary_EN.md#term-evidence) inputs for the future authorization;
2. the sole admissible future authoring surfaces;
3. mandatory fields and semantics of the new one-shot record;
4. its distinction from every historical authorization;
5. issuance, post-merge verification, consumption, and single
   [attempt](../glossary_EN.md#term-attempt) ordering;
6. forbidden effects of the current scope freeze;
7. acceptance criteria for future record authoring.

It creates no authorization schema, verifier, tests, authorization record, or
operator phrase.

## Admissible inputs

The future authorization-authoring slice must bind without modification:

- verified `main`
  `a5b96edb1f82485561e0f52d6a98432d55ae8609`;
- PR #170, its head
  `6201997a71428bdb873d95d76c5b0882be532b2a`, merge commit, and
  `2026-08-03T16:16:32Z` merge time;
- Torch2PC
  `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4`;
- the immutable admission repository seal and its exact SHA-256 identity;
- the canonical admission record, its internal `admission_sha256`, and its
  SHA-256 registries;
- immutable image
  `torch2pc-layerwise-thesis@sha256:7da92b8f77f6dc37d42db832c5613ef6149dc488adc5b66465faa33e48ca021d`;
- sole prospective entry point `invoke_lease_bound_host_runtime`;
- the output root, persistent lease v2, and durable host outcome paths already
  bound by the admission record.

The historical `QW-LC4-F` engineering authorization and consumed final
acknowledgement-materialization authorization are validation-only
[evidence](../glossary_EN.md#term-evidence) for non-reuse. They carry no
authority for the future invocation.

## Future authoring surfaces

Only the future separate record-authoring slice may create:

```text
src/torch2pc_thesis/stage3b_qwake_lc4_final_engineering_invocation_authorization.py
scripts/verify_stage3b_qwake_lc4_final_engineering_invocation_authorization.py
tests/unit/test_stage3b_qwake_lc4_final_engineering_invocation_authorization.py
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-v1/authorization.json
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-v1/source-SHA256SUMS
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-v1/SHA256SUMS
```

The schema and verifier must remain pure: they do not import the runtime entry
point, invoke Docker or a child process, or create runtime-boundary files.
Negative tests mutate temporary copies only.

## Future record contract

The future record must:

1. have a new identifier and its own semantic SHA-256;
2. bind an exact operator and separate action phrase;
3. bind verified `main`, the repository seal, admission record, Torch2PC,
   image, entry point, and all runtime-boundary paths;
4. permit at most one [attempt](../glossary_EN.md#term-attempt);
5. prohibit a shell, direct Docker use, direct lower-host invocation, and the
   historical runtime operation;
6. prohibit automatic, blind, and manual retry after consumption, lease-v2
   creation, or an unknown outcome;
7. require atomic consumption with attempt start and exclusive persistent
   lease-v2 creation;
8. require one durable host-outcome receipt for every terminal class;
9. remain ineffective until its own merge and independent post-merge
   verification;
10. not authorize `QW-5`, the scientific campaign, test-data access, or
    publication.

Future record materialization may set `authorization_issued=true`, but before
post-merge verification it must preserve
`authorization_post_merge_verified=false`,
`final_engineering_invocation_permitted=false`, and
`authorization_consumed=false`.

## Forbidden effects of this slice

The current slice forbids:

- creation of an authorization schema, verifier, tests, or authorization record;
- authorization issuance or consumption;
- reservation of an operator phrase;
- invocation-command materialization;
- creation of execution lease v1 or v2;
- creation of a durable host outcome;
- creation of the output root or runtime output;
- image inspection, Docker, model code, or a child process;
- modification of an existing frozen package;
- opening `QW-5`, `C1`, `C2`, `C3`, `R`, test-data access, or publication.

## Acceptance criteria for future authorization authoring

The future slice is accepted only if:

1. every admissible input is checked by exact identity;
2. the new record is canonical and has a verifiable semantic SHA-256;
3. the identifier, operator, and action phrase are unambiguous;
4. historical authorizations are explicitly non-reusable;
5. the record permits exactly one future attempt;
6. the record is issued but ineffective until independent post-merge
   verification;
7. the runtime entry point, Docker, and model code are neither imported nor
   invoked;
8. the lease, host outcome, output root, and runtime output remain absent;
9. negative tests operate only on temporary copies;
10. `QW-5` and scientific capabilities remain closed.

## Machine-readable freeze

```text
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-authoring-scope-freeze-v1/scope.json
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-authoring-scope-freeze-v1/SHA256SUMS
```

## Sequence

```text
authorization-authoring scope freeze
→ authorization record authoring
→ authorization merge and independent verification
→ atomic authorization consumption, attempt start, and lease v2
→ invoke_lease_bound_host_runtime
→ durable host outcome
→ sealed extension engineering report
→ QW-5 eligibility decision
```

## Machine boundary

```text
FINAL_ENGINEERING_INVOCATION_ADMISSION_REPOSITORY_SEAL_COMPLETE=true
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_AUTHORING_SCOPE_FROZEN=true
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_AUTHORED=false
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_RECORD_PRESENT=false
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_ISSUED=false
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_POST_MERGE_VERIFIED=false
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_CONSUMED=false
FINAL_ENGINEERING_INVOCATION_PERMITTED=false
FINAL_ENGINEERING_INVOCATION_STARTED=false
FINAL_ENGINEERING_INVOCATION_PERFORMED=false
OPERATOR_PHRASE_RESERVED=false
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
NEXT_SLICE=QW-LC4-E-final-engineering-invocation-authorization-authoring-scope-freeze-commit
POST_MERGE_NEXT_SLICE=QW-LC4-E-final-engineering-invocation-authorization-record-authoring
```

## Consequences

This ADR is not an authorization and does not permit a
[run](../glossary_EN.md#term-run). It only constrains future authoring to exact
inputs, surfaces, and one-shot semantics. [Local compute](../glossary_EN.md#term-local-compute)
and every scientific capability remain closed.
