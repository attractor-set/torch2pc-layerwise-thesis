# ADR-012: PC-TREF Balanced Core, PC-CATM, and Scenario A

[Русская версия](ADR-012-pc-tref-pc-catm-scenario-a.md)

## Status

Accepted as a design decision. It does not mark new experiments as complete.

## Context

Stage 3A and Stage 3B B0 are complete. B0 identified `state_inference` as the
dominant region, with a median Strict/FixedPred device-time ratio of `2.327×`,
a peak-allocated-memory ratio of `1.328×`, and a saved-tensor ratio of
`11.998×` in the registered scope. The official post-B0 roadmap admitted B1/B2
but did not yet unify [mechanism attribution](../glossary_EN.md#term-mechanism-attribution), correction-zero diagnostics, and
adaptive inference into one realistic master's-thesis track.

## Decision

1. Adopt [PC-TREF](../glossary_EN.md#term-pc-tref) Balanced Core as the
   upper-level diagnostic-sufficiency framework.
2. Adopt [PC-CATM](../glossary_EN.md#term-pc-catm) as the mechanism operator
   model of correction aggregation and error transport.
3. Keep Scenario A as the single primary experimental path: shortcut and
   observer controls; deterministic controls; SI-MA0; B1/B2; `EX-IF0`; passive
   diagnostics; predictor; exact verification; shadow [QWake-PC](../glossary_EN.md#term-qwake-pc); conditional
   active full-sweep QWake-PC.
4. Compare nested diagnostic representations $\phi_0,\ldots,\phi_5$ on a
   cost-sufficiency frontier.
5. Keep `PNZ`, parameter tangent Gram diagnostics, and kernelized learning as a
   limited theoretical or exploratory extension.
6. Keep B0 immutable and the test split closed until a separate final freeze.

## Consequences

- the thesis remains centered on `state_inference` and safe exact-computation
  reduction;
- `A-Min`, `A-Core`, and `A-Max` define independent success levels;
- a negative active-QWake result does not invalidate mechanism attribution or
  diagnostic-sufficiency analysis;
- universal TREF, layer-aware skipping, active plasticity control, and
  kernel-preconditioned learning remain future work;
- `ECZ` has the single meaning `Error-Cancellation Zone`.

## Claim boundaries

This decision freezes the plan and terminology. Each stage requires its own
gates, and empirical claims are enabled only after corresponding [execution](../glossary_EN.md#term-execution) and
[evidence](../glossary_EN.md#term-evidence) publication.
