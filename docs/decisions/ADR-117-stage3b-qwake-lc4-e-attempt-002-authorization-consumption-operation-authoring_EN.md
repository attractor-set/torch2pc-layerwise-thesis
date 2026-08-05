# ADR-117: attempt-002 authorization-consumption operation authoring

- Status: accepted
- Date: 2026-08-04
- Slice: `QW-LC4-E-attempt-002-authorization-consumption-operation-authoring`

## Context

The sixth PR #179 commit and its separate
[scope freeze](../glossary_EN.md#term-freeze) have been independently
verified. The one-shot authorization for
[attempt](../glossary_EN.md#term-attempt) 002 remains effective and
unconsumed. No lease, outcome, or
[execution](../glossary_EN.md#term-execution) has started.

The next transition must separate the one-shot operation definition from its
production call. Merely importing or possessing the module must not create a
process, container, output root, or terminal
[evidence](../glossary_EN.md#term-evidence).

## Decision

Author the distinct import-effect-free operation
`execute_attempt_002_authorization_consumption_operation_once`.

The operation:

1. accepts an explicit post-commit admission;
2. requires the exact implementation commit, a clean worktree, and the exact
   Torch2PC identity;
3. requires effective unconsumed authorization and absence of every
   attempt-002 effect artifact;
4. materializes one canonical in-memory claim;
5. calls exactly one injected delegated transition;
6. forbids automatic retry after failure or an unknown delegated outcome.

The module imports no `subprocess`, Docker client, or
[runtime](../glossary_EN.md#term-runtime) code. It creates
no production callsite, concrete process spawner, or external
[run](../glossary_EN.md#term-run).

## Verifiable boundary

The operation module, verifier, tests, and three-file package are authored.
Tests exercise only a synthetic delegated transition inside isolated temporary
repositories. They never use the project worktree as an effect target.

The authorization package and terminal attempt-001
[evidence](../glossary_EN.md#term-evidence) remain immutable.

```text
ATTEMPT_002_AUTHORIZATION_CONSUMPTION_OPERATION_SCOPE_FREEZE_POST_COMMIT_VERIFIED=true
ATTEMPT_002_AUTHORIZATION_CONSUMPTION_OPERATION_AUTHORING_ADMISSIBLE=true
ATTEMPT_002_AUTHORIZATION_CONSUMPTION_OPERATION_AUTHORED=true
ATTEMPT_002_AUTHORIZATION_CONSUMPTION_OPERATION_POST_COMMIT_VERIFIED=false
ATTEMPT_002_AUTHORIZATION_CONSUMPTION_OPERATION_INVOKED=false
PRODUCTION_CALLSITE_PRESENT=false
HOST_PROCESS_SPAWNER_PRESENT=false
ATTEMPT_002_AUTHORIZATION_CONSUMED=false
ATTEMPT_002_ATTEMPT_STARTED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
AUTHORIZATION_CONSUMPTION_PERMITTED=false
DO_NOT_MERGE_YET=true
```

## Consequences

The seventh commit must contain only the frozen seventeen paths. A separate
read-only audit is required after that commit. Authorization consumption, the
production operation call, and merging PR #179 remain forbidden until that
audit succeeds.
