# ADR-033: freeze one-run Stage 3B descriptive-analysis authorization

[Русская версия](ADR-033-stage3b-matched-descriptive-analysis-execution-authorization-freeze.md)

- **Status:** accepted
- **Date:** 2026-07-22

## Context

[Execution](../glossary_EN.md#term-execution) request `v1` and the actual
[runtime](../glossary_EN.md#term-runtime) preflight are already frozen. The
preflight verified the exact environment identity and absent output root while
intentionally retaining `analysis_execution_permitted=false`. Transition to one
computational run requires a separate prospective decision made before result
inspection and bound to immutable request/preflight/runtime identities.

## Decision

Freeze the canonical
`experiments/frozen/stage3b-matched-descriptive-analysis-execution-authorization-v1/`
package with exactly three regular files:

1. `authorization.json`;
2. an exact `runtime-preflight.json` copy;
3. `SHA256SUMS`.

The authorization file SHA-256 is
`29f48ae7fe4f8ab92c465d939ee68c2142488bf8463f718d76c41361d9c6a76f`,
and its internal digest is
`5e4f570d81d373637244563afed9d1765fe0d17b3d726db9282b4104c37d83c0`.
It binds request digest `5c813e10…127a2e`, preflight digest
`428c9a7f…901cc`, runtime identity `e71f0f85…007d`, the exact operator
acknowledgement, and exactly one read-only
[attempt](../glossary_EN.md#term-attempt).

## Decision boundary

```text
execution_authorization_present=true
analysis_execution_permitted=true
analysis_execution_performed=false
execution_attempt_claimed=false
sealed_evidence_execution=false
analysis_results_present=false
results_publication_permitted=false
release_publication_permitted=false
test_dataset_access=false
```

Freezing authorization is not [evidence](../glossary_EN.md#term-evidence) of
execution. The branch and pull request do not activate the executor: the package
must merge into a clean `main`, after which a separate opening gate revalidates
its identity and the current environment.

## Invalidation

Authorization must not be used if the request, preflight, runtime identity, any
bound SHA-256, source evidence, output root, or operator boundary changes. An
existing output root or local attempt receipt also closes replay. A new
authorization requires a new package version and separate decision.

## Consequences

The next slice may only independently verify merged `main` and open one executor
invocation. Result publication remains a separate decision after validation of
the 18-file output contract and post-execution source SHA-256 verification.
