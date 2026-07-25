# ADR-046: full `QWake` documentation refactor and image-identity reset

[Русская версия](ADR-046-stage3b-qwake-documentation-refactor-and-image-reset.md)

- **Status:** accepted as `QW-4B-DOC-R1`;
- **Date:** 2026-07-24;
- **[Execution](../glossary_EN.md#term-execution):** not performed;
- **[Evidence](../glossary_EN.md#term-evidence):** absent.

## Context

The `QW-4B-F-v1` [candidate](../glossary_EN.md#term-candidate) successfully bound the old source identity,
container image, preflight, static-validation receipt, and single-[attempt](../glossary_EN.md#term-attempt)
authorization. Before execution, review found that the active plan conflated
response, computational method, and cost while retaining the old
`QW-5 → QW-6 → … → QW-10` sequence beside the new extension.

A local terminology correction could have passed documentation guards without
removing the conceptual inconsistency.

## Decision

1. Retire the old preflight, receipt, and authorization before execution and
   retain them only in an external audit record.
2. Do not rewrite historical `ADR-042`–`ADR-045` or previously sealed evidence.
3. Fully rewrite the active plan, roadmap, future-policy boundary, status, and
   research-log sections.
4. Freeze the separation of `R`, `M`, `Γ`, and `C`, two equivalence relations,
   and the `LOCAL_COMPUTE` family.
5. Replace the active sequence with:

```text
QW-4B-DOC-R1
→ new immutable baseline image
→ QW-4B-F-v2
→ QW-4B-E-v2
→ sealed baseline report
→ QW-LC0 → QW-LC1 → QW-LC2 → QW-LC3
→ QW-LC4-I → QW-LC4-F → QW-LC4-E
→ QW-5 → C1 → C2 → C3 → R
```

6. After the documentation refactor is merged, build a new immutable image and
   reissue the preflight, receipt, and single-attempt authorization.

## Claim boundary

The documentation refactor does not implement [analytic completion](../glossary_EN.md#term-analytic-completion), execute
`FixedPred`, create an engineering report, or open a scientific campaign. The
first analytic candidate remains a bounded future hypothesis.

```text
old_authorization_reuse_permitted=false
new_image_required=true
new_runtime_preflight_captured=false
new_runtime_authorization_issued=false
runtime_execution_performed=false
engineering_evidence_present=false
local_compute_implementation_open=false
scientific_image_freeze_permitted=false
```

## Consequences

The new image must identify the commit after `QW-4B-DOC-R1` merge. Any new
`QW-4B-F-v2` package binds only that commit and the new image digest. Old bytes
remain an audit record but are not an active authorization.
