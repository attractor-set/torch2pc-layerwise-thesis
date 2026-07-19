# ADR-017: Stage 3B 288-cell prelaunch correctness repair

[Русская версия](ADR-017-stage3b-288cell-correctness-repair.md)

- Status: accepted
- Date: 2026-07-19

## Context

The prelaunch audit of the matched B0/B1/B2 campaign found four independent
risks: retry/resume was incompatible with sealing, smoke equivalence could open
[profiling](../glossary_EN.md#term-profiling) without confirmatory
[evidence](../glossary_EN.md#term-evidence), the three-[candidate](../glossary_EN.md#term-candidate)
FixedPred order was not exactly balanced, and the
[scaling](../glossary_EN.md#term-scaling) matrix had no separate cross-candidate
correctness check.

Two previous [attempts](../glossary_EN.md#term-attempt) showed that
[runtime](../glossary_EN.md#term-runtime) authorization and a successful dry run
alone are insufficient for an evidence-producing campaign.

## Decision

1. [Attempt](../glossary_EN.md#term-attempt) history remains append-only.
2. Retry is allowed only for explicitly classified infrastructure or operator
   interruptions. Unknown, scientific, and correctness failures are
   non-retryable.
3. Sealing accepts retryable failures or interruptions before one final
   successful attempt, while rejecting non-retryable failures, multiple
   successful attempts, unfinished attempts, or a success that is not last.
4. Production [execution](../glossary_EN.md#term-execution) requires confirmatory
   EQ-B1 with 120/120 pairs and confirmatory EQ-B2 with 120/120 triples and
   240/240 comparisons. Engineering CPU tests do not open the production gate.
5. Each method uses all six permutations of the three candidates eight times:
   every candidate occupies every position 16 times and every pairwise
   precedence occurs 24 times.
6. Each block receives a separate untimed cross-candidate correctness probe
   before measurement. It compares no-hooks snapshots of `stage2_baseline`
   against `isolated_layer_vjp` and `composite_vjp` under the same
   [model seed](../glossary_EN.md#term-model-seed) and synthetic minibatch.
7. A correctness failure is non-retryable, stops the campaign, and requires a
   new source commit and output root.
8. Sealing requires one block-level correctness record per block and preserves
   attempt history and correctness records in the evidence bundle.

## Consequences

- previously issued authorization envelopes and output roots cannot be reused
  after the manifest, source, or image digest changes;
- existing smoke decisions remain immutable historical artifacts but cannot open
  production execution;
- confirmatory B1/B2 evidence must be executed and sealed before a new freeze;
- observer timing and the correctness probe remain separate; the probe is not
  included in primary timing;
- recovery remains available only for explicitly retryable events.

## GO criterion

The 288-cell lane may run only after confirmatory equivalence, exact
counterbalance, an untimed cross-candidate smoke, retry/sealing integration
smoke, a new immutable image, a new freeze, preflight, authorization, and a dry
run on a new empty output root all pass.
