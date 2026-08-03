# ADR-100: `QW-LC4-E` final engineering-invocation admission-authoring scope freeze

[Russian version](ADR-100-stage3b-qwake-lc4-e-final-engineering-invocation-admission-authoring-scope-freeze.md)

- **Status:** accepted as a scope freeze; [execution](../glossary_EN.md#term-execution) remains closed
- **Date:** 2026-08-03
- **Context:** `QW-LC4-E`
- **Preceded by:** ADR-099
- **Base commit:** `5221a51160f8aeaca25a4d0bc36da4426bc498eb`

## Context

ADR-099 separated the completed final-acknowledgement materialization line from
the still-absent extension engineering report. The sealed
[evidence](../glossary_EN.md#term-evidence) contains the final acknowledgement,
the consumed authorization for a separate callsite, and the prohibition on
retrying it. It contains no persistent lease v2, durable host outcome, or
[runtime](../glossary_EN.md#term-runtime) output.

The repository already contains persistent evidence chain v2 and the sole
prospective entry point `invoke_lease_bound_host_runtime`. That entry point
supersedes the historical direct operation. Implementation presence does not
authorize a new [run](../glossary_EN.md#term-run): a separate admission-authoring
scope and a new authorization are required.

## Objective of this slice

This slice freezes only:

1. the exact admissible source identities;
2. the mandatory future engineering-invocation entry point;
3. the boundary of one new [attempt](../glossary_EN.md#term-attempt);
4. forbidden admission-authoring effects;
5. acceptance criteria for the future admission-authoring slice;
6. the separate authorization, execution, and reporting sequence.

It implements no admission schema, issues no authorization, and invokes no
runtime entry point.

## Admissible inputs

The future admission-authoring slice must bind unchanged:

- `main` after PR #167:
  `5221a51160f8aeaca25a4d0bc36da4426bc498eb`;
- Torch2PC:
  `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4`;
- the post-acknowledgement transition package and its SHA-256 registry;
- the five-file final-acknowledgement evidence package and terminal
  `verification.json`;
- the persistent evidence-chain-v2 implementation;
- the lease-bound host-invoker wiring;
- immutable image
  `torch2pc-layerwise-thesis@sha256:7da92b8f77f6dc37d42db832c5613ef6149dc488adc5b66465faa33e48ca021d`;
- output root
  `results/stage-3/qwake-lc4-runtime-validation-v1-attempt-001`;
- the prospective persistent-lease-v2 and durable-host-outcome paths.

Historical direct-operation and prior-authorization packages may be used only
to validate provenance and prevent reuse. They are not authority for the final
engineering invocation.

## Mandatory future operation entry point

The sole admissible prospective entry point is:

```text
module=src/torch2pc_thesis/stage3b_qwake_lc4_lease_bound_host_invoker_wiring.py
entrypoint=invoke_lease_bound_host_runtime
```

The future production layer must not call the lower host invoker, historical
direct operation, Docker, or `subprocess.Popen` directly. Exact persisted
lease-v2 bytes must exist before delegation. One durable host-outcome receipt is
required for every terminal class.

## New authorization boundary

The new authorization must:

1. have a new identifier and SHA-256;
2. differ from the historical engineering authorization and consumed
   acknowledgement-materialization authorization;
3. permit at most one attempt;
4. become effective only after merge and independent verification of the future
   admission-authoring slice;
5. be consumed atomically with attempt start and exclusive persistent-lease-v2
   creation;
6. forbid automatic, blind, and manual retry after consumption, lease creation,
   or an unknown outcome;
7. authorize neither `QW-5`, the scientific campaign, test-data access, nor
   publication.

This slice reserves no operator phrase and creates no authorization file.

## Forbidden effects of this slice

The slice must not:

- create or modify runtime-entry-point source code;
- create an admission schema, verifier, or admission unit tests;
- create an admission record or authorization;
- consume any authorization;
- create persistent lease v1 or v2;
- create a durable host-outcome receipt;
- inspect the local image;
- materialize an invocation command;
- create the output root or runtime staging files;
- invoke Docker, the model, or a child process;
- modify any existing frozen package;
- open `QW-5`, `C1`, `C2`, `C3`, `R`, test-data access, or publication.

## Acceptance criteria for future admission authoring

The future admission-authoring slice is acceptable only when:

1. a pure schema validates exact identities of every admissible input;
2. its verifier neither imports nor calls the runtime entry point;
3. negative tests use temporary repositories only;
4. direct lower-host-invoker calls remain forbidden;
5. the admission record preserves `authorization_issued=false`;
6. no lease, host outcome, runtime output, or output root exists;
7. every gate remains closed pending a separate authorization;
8. merge is followed by independent verification of the exact commit and
   registries.

## Machine-readable freeze

```text
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-admission-authoring-scope-freeze-v1/scope.json
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-admission-authoring-scope-freeze-v1/SHA256SUMS
```

## Sequence

```text
scope-freeze
→ admission-authoring
→ admission repository seal and independent verification
→ distinct one-shot authorization
→ atomic authorization consumption and persistent lease v2
→ invoke_lease_bound_host_runtime
→ durable host outcome
→ sealed extension engineering report
→ QW-5 eligibility decision
```

## Machine boundary

```text
FINAL_ENGINEERING_INVOCATION_ADMISSION_AUTHORING_SCOPE_FROZEN=true
FINAL_ENGINEERING_INVOCATION_ADMISSION_AUTHORED=false
FINAL_ENGINEERING_INVOCATION_ADMISSION_RECORD_PRESENT=false
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_ISSUED=false
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_CONSUMED=false
FINAL_ENGINEERING_INVOCATION_PERMITTED=false
FINAL_ENGINEERING_INVOCATION_STARTED=false
FINAL_ENGINEERING_INVOCATION_PERFORMED=false
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
NEXT_SLICE=QW-LC4-E-final-engineering-invocation-admission-authoring-scope-freeze-commit
POST_MERGE_NEXT_SLICE=QW-LC4-E-final-engineering-invocation-admission-authoring
```

## Consequences

This ADR is neither admission nor authorization. It freezes the minimum scope in
which future admission authoring can be implemented without reusing historical
permissions or bypassing the lease-bound host invoker.
