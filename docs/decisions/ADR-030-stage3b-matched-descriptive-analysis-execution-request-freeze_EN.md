# ADR-030: freeze the Stage 3B matched descriptive-analysis execution request

[Русская версия](ADR-030-stage3b-matched-descriptive-analysis-execution-request-freeze.md)

- **Status:** accepted
- **Date:** 2026-07-21

## Context

ADR-027 froze the post-collection/pre-analysis protocol, ADR-028 implemented
the registered engine, and ADR-029 removed mandatory risks before
[execution](../glossary_EN.md#term-execution). The sealed
[evidence](../glossary_EN.md#term-evidence) exists, but its public entrypoint
remains closed. Before [runtime](../glossary_EN.md#term-runtime) admission, the
project must independently freeze exactly what is requested, from which inputs,
and into which single output directory.

## Decision

Create the deterministic
`stage3b-matched-descriptive-analysis-execution-request-v1` package containing
`request.json` and `SHA256SUMS`.

The request binds immutable evidence, protocol, hardening-base commit, and
analysis-core identities, the exact 18-output inventory, and one new output
directory. It requires separate machine-readable authorization, runtime
preflight, a frozen `generated_at_utc`, before/after input verification, and at
most one [run](../glossary_EN.md#term-run).

## Decision boundary

```text
execution_request_frozen=true
execution_authorization_present=false
analysis_execution_permitted=false
analysis_execution_performed=false
analysis_results_present=false
results_publication_permitted=false
release_publication_permitted=false
```

The request builder reads no observed metric values and produces no result
claim. The request is not evidence, a decision, or a publication gate.

## Consequences

Benefits:

- authorization cannot silently change inputs, core, directory, or inventory;
- a second run and partial output become explicit fail-closed cases;
- future result provenance is prospectively bound to the frozen protocol.

Limitations:

- runtime identity is not frozen yet;
- execution remains impossible until a separate authorization merge;
- the draft release remains unpublished;
- the full Stage 3B program remains incomplete.
