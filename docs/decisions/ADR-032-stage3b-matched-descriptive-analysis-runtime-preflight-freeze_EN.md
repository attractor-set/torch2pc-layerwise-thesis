# ADR-032: freeze the actual `Stage 3B` descriptive-analysis runtime preflight

[Русская версия](ADR-032-stage3b-matched-descriptive-analysis-runtime-preflight-freeze.md)

- **Status:** accepted
- **Date:** 2026-07-22

## Context

ADR-031 implemented fail-closed [runtime](../glossary_EN.md#term-runtime)
preflight but did not freeze an actual environment. After the implementation
was merged at `272a9258f70320416ff97c3da076435fd5334bc4`, a non-computational
[candidate](../glossary_EN.md#term-candidate) file was captured from a clean
tree. It did not parse observed metric values or create the output root,
authorization, or an [execution](../glossary_EN.md#term-execution)
[attempt](../glossary_EN.md#term-attempt) receipt.

## Decision

Freeze the exact candidate file as
`experiments/frozen/stage3b-matched-descriptive-analysis-runtime-preflight-v1/runtime-preflight.json`
with a separate `SHA256SUMS`. The file SHA-256 is
`1722cce133e047512c2b587c9d8fba15e95457653afd2fa496f295d3b1bbced0`,
and its internal digests are:

- `preflight_digest=428c9a7fdc1baf2b86a033a12189b9b98cce4e41dbb6e87cb73d42f4e9e901cc`;
- `runtime_identity_digest=e71f0f8539231e466291843e919b412d44ec6022e4dce863785142b67abe007d`;
- `request_digest=5c813e101c17210443b63b6499c7c6fed88fe34029f438942b71ad9faf127a2e`.

Static validation confirms canonical `JSON`, the exact 11 runtime-bound files,
9 sealed-source SHA-256 identities, 18 unique output names, and closed claim
boundaries. The host-specific runtime probe will be checked again by the future
authorization verifier before [execution](../glossary_EN.md#term-execution).

## Decision boundary

```text
runtime_preflight_implemented=true
runtime_preflight_frozen=true
execution_authorization_present=false
execution_attempt_claimed=false
sealed_evidence_execution=false
analysis_results_present=false
results_publication_permitted=false
release_publication_permitted=false
```

The preflight freeze is not authorization. The executor remains closed.

## Consequences

A separate next slice may create machine-readable authorization that binds this
preflight, the execution request, and runtime identity byte-for-byte. Execution,
result creation, and draft-release publication remain prohibited until that
authorization is merged.
