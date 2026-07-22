# ADR-034: Freeze the sealed Stage 3B descriptive-analysis output

[Русская версия](ADR-034-stage3b-matched-descriptive-analysis-output-seal-freeze.md)

- **Status:** accepted
- **Date:** 2026-07-22

## Context

The single authorized [execution attempt](../glossary_EN.md#term-attempt) completed on `main@72b95a284e8747a33b8c34d5929d4110aa4bfea1`. It produced the exact 18-file output, and a separate read-only audit preserved the canonical receipt, SHA-256 map, and audit record. The generated output intentionally retains `analysis_output_evidence=false`: that field describes the immediate post-computation state and must not be rewritten after results are observed.

Moving the unchanged output into repository [evidence](../glossary_EN.md#term-evidence) therefore requires a separate technical seal that binds output, receipt, and audit without changing any of the 18 files or opening publication or superiority claims.

## Decision

1. Preserve the exact 18-file output at its original `results/.../stage3b-matched-descriptive-analysis-70d6c3c-v1` path without adding `seal.json` inside that directory.
2. Preserve the independent audit package at `experiments/frozen/stage3b-matched-descriptive-analysis-output-audit-v1`.
3. Create `experiments/frozen/stage3b-matched-descriptive-analysis-output-seal-v1` containing `seal.json` and `SHA256SUMS`.
4. Bind the seal to the execution source commit, request, authorization, [runtime](../glossary_EN.md#term-runtime) preflight, runtime identity, execution receipt, audit record, audit registry, and output registry.
5. Treat the output as sealed evidence only through the external seal. The internal `analysis_metadata.json`, `analysis_summary.json`, and `engineering_decision.json` remain byte-identical.
6. Retain `results_publication_permitted=false`, `release_publication_permitted=false`, `superiority_claim_permitted=false`, `test_dataset_access=false`, `ex_if0_opened=false`, and `policy_activation_permitted=false`.

## Rationale

The external seal separates irreversible computation from subsequent provenance preservation. It prevents post hoc metadata mutation, retains the exact 18-file contract, and creates a machine-checkable chain:

```text
sealed source → authorized execution → receipt → exact output → independent audit → external seal
```

The seal establishes integrity and provenance. It does not establish publication readiness, statistical superiority, test-split access, or permission for active policy control.

## Consequences

- the single execution attempt remains consumed;
- the 18-file output becomes repository evidence after merge and clean-`main` verification;
- the audit and seal receive separate frozen identities;
- publication requires a separate decision and is not implied by sealing;
- any output/audit/receipt/seal mismatch closes the next transition;
- recomputation or result mutation is prohibited.

## Rejected alternatives

- **Add `seal.json` inside the output root.** This violates the registered exact 18-file inventory.
- **Rewrite `analysis_metadata.json` to `analysis_output_evidence=true`.** This changes the result after computation and destroys the original boundary.
- **Treat the audit alone as the seal.** The audit records successful validation of an unsealed output but does not make the separate repository-evidence decision.
- **Open publication during sealing.** The execution request does not support this and requires a separate publication gate.
