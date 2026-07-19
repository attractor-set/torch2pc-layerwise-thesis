# ADR-015: Stage 3B matched measurement-lane separation and sealing

[Russian version](ADR-015-stage3b-matched-measurement-sealing.md)

- Status: accepted for implementation
- Date: 2026-07-19

## Context

The frozen B0/B1/B2 matched protocol requires two distinct measurement lanes:
`primary_timing` in `no_hooks` mode and `structural_counters` in
`counters_only` mode. The previous executor stored composite timing only for
the instrumented arm. Per-region synchronization and [observer cost](../glossary_EN.md#term-observer-cost) could
therefore be mixed into primary [runtime](../glossary_EN.md#term-runtime), while graph/locality events were not
persisted as a complete artifact contract.

The existing sealing pipeline was also limited to the 96-cell B0 archive and
could not validate 288 matched cells, three candidates, and paired block
structure.

## Decision

1. One gate runs two arms from the same model/RNG state:
   - the no-hooks arm produces primary timing and memory;
   - the counters-only arm produces region attribution, structural counters,
     and locality events.
2. Numerical non-perturbation compares those arms under the unchanged frozen
   thresholds.
3. Observer cost is published as the signed structural-minus-primary
   difference and is never silently subtracted from primary timing.
4. Locality events are appended to `locality-events.jsonl` in each [attempt](../glossary_EN.md#term-attempt);
   `measurements.json` stores the count and SHA-256.
5. `fallback_validation_cost_ms` remains `null` with explicit status
   `not_applicable_before_ex_if0`.
6. A matched-specific sealing pipeline validates terminal uniqueness,
   288-cell/[candidate](../glossary_EN.md#term-candidate)/block completeness, both lanes, integrity gates, and the
   event stream before producing a compact SHA-256 [evidence](../glossary_EN.md#term-evidence) bundle.
7. Analysis remains descriptive with three model seeds, uses matched blocks,
   and does not automatically open EX-IF0 or activate a policy.

## Consequences

- Any runtime started before this decision is merged is incompatible with the
  new measurement schema and cannot be resumed or sealed as complete matched
  evidence.
- Gate runtime does not add a third inference arm: the existing no-hooks
  reference arm becomes the primary timing lane.
- Structural timing remains diagnostic and is not interpreted as primary
  algorithm runtime.
- Publication permission remains a separate provenance transition after
  sealing and analysis.
