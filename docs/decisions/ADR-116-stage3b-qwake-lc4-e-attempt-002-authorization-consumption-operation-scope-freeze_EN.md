# ADR-116: attempt-002 authorization-consumption operation scope freeze

- Status: accepted
- Date: 2026-08-04
- Slice: `QW-LC4-E-attempt-002-authorization-consumption-operation-scope-freeze`

## Context

The fifth PR #179 commit has been independently verified. The one-shot
authorization for [attempt](../glossary_EN.md#term-attempt) 002 exists, is
effective, and remains unconsumed. No process, lease, outcome, or
[execution](../glossary_EN.md#term-execution) has started.

Authoring the operation without a separate [scope freeze](../glossary_EN.md#term-freeze)
would mix the decision about admissible files with implementation of the
transition. A distinct immutable scope record is therefore required before any
operation module.

## Decision

Create the two-file package `experiments/frozen/stage3b-qwake-lc4-e-attempt-002-authorization-consumption-operation-scope-freeze-v1`:

1. `scope.json` — the canonical record of the admissible future stage;
2. `SHA256SUMS` — the checksum of the exact `scope.json` bytes.

The current slice changes exactly thirteen documentation and package paths. It
does not create the operation module, operation verifier, operation tests, or
operation package.

## Frozen future scope

The next stage may change only the seventeen paths enumerated in `scope.json`.
They cover:

- bilingual `ADR-117`;
- status, index, language-map, extension, and research-log updates;
- one operation module, one verifier, and one test file;
- the operation package containing `operation.json`, `source-SHA256SUMS`, and
  `SHA256SUMS`.

Any additional path requires a new decision and a new scope freeze.

## Required future-authoring properties

The future operation-authoring stage must:

1. remain import-effect free;
2. contain no production callsite;
3. start no process, container, or [runtime](../glossary_EN.md#term-runtime);
4. consume no authorization and create no lease, outcome, or output root;
5. exercise effectful behavior only in isolated temporary repositories;
6. fail closed on any identity or state mismatch;
7. leave the authorization package and terminal attempt-001
   [evidence](../glossary_EN.md#term-evidence) unchanged.

## Current boundary

```text
ATTEMPT_002_AUTHORIZATION_POST_COMMIT_VERIFIED=true
ATTEMPT_002_AUTHORIZATION_EFFECTIVE=true
ATTEMPT_002_AUTHORIZATION_CONSUMED=false
ATTEMPT_002_ATTEMPT_STARTED=false
ATTEMPT_002_AUTHORIZATION_CONSUMPTION_OPERATION_SCOPE_FROZEN=true
ATTEMPT_002_AUTHORIZATION_CONSUMPTION_OPERATION_AUTHORED=false
ATTEMPT_002_AUTHORIZATION_CONSUMPTION_OPERATION_INVOKED=false
HOST_PROCESS_SPAWNER_PRESENT=false
DOCKER_RUN_IMPLEMENTED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
AUTHORIZATION_CONSUMPTION_PERMITTED=false
DO_NOT_MERGE_YET=true
```

## Consequences

After a separate commit and independent verification of this scope freeze,
`ADR-117` may author the exact operation module. The presence of that module
will still not permit its production call, authorization consumption, or
execution start.
