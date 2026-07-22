# ADR-038: `EX-IF0`, exact implementation, and oracle sweep boundary

[Русская версия](ADR-038-stage3b-ex-if0-exact-implementation-and-oracle-sweep-boundary.md)

- **Status:** accepted as a design freeze without [execution](../glossary_EN.md#term-execution) permission
- **Date:** 2026-07-22

## Context

B1 `isolated_layer_vjp` and B2 `composite_vjp` passed their registered numerical gates, but the published matched analysis retained both candidates as `reject_or_revise` for `FixedPred` and `Strict`. The publication receipt is frozen. The next mandatory transition is the [exact-implementation freeze](../glossary_EN.md#term-exact-implementation-freeze) before counterfactual labels, features, and predictor work.

The subsequent study also requires an unambiguous definition of the minimum stably sufficient sweep relative to the full exact [endpoint](../glossary_EN.md#term-endpoint). Without a frozen decision epoch, reference trajectory, thresholds, and suffix rule, that label would be exposed to post-hoc retuning.

## Decision

1. Select `stage2_baseline` as the canonical exact reference and fail-closed [fallback](../glossary_EN.md#term-fallback) for `FixedPred` and `Strict`.
2. Do not interpret this selection as a superiority claim. It follows from the [baseline](../glossary_EN.md#term-baseline)'s mandatory fallback role and the B1/B2 `reject_or_revise` decisions.
3. Freeze `experiments/frozen/stage3b-ex-if0-design-v1/contract.json` and its SHA-256 as the machine-readable source of truth.
4. Place the decision epoch after `S_t` completes and before sweep `t+1`, including `S_0` before the first sweep.
5. Use the full [configuration](../glossary_EN.md#term-configuration)-specific B0 trajectory with unchanged `inference_steps` as exact reference.
6. Define the task-relative endpoint through named parameter gradients, endpoint beliefs, endpoint loss, and mandatory structural, finite-value, and provenance guards.
7. Freeze the existing B1/B2 `rocm_float32` profile (`max_abs=1e-5`, `max_relative_l2=1e-3`, `min_cosine=0.999`, `zero_atol=1e-7`) without retuning after labels.
8. Define dimensionless regret as the maximum normalized violation and the [oracle sufficiency margin](../glossary_EN.md#term-oracle-sufficiency-margin) as `M^*(t)=1-r_Gamma(t)`.
9. Define the minimum stably sufficient sweep through a full suffix rule: every endpoint from `t` through `K_ref` must remain sufficient.
10. Retain `stop`, `native_one`, and `exact_one` only as post-action offline labels. Under `v1`, both one-step branches use `stage2_baseline` and must pass an identity control.
11. Strictly separate pre-action features from post-action oracle labels.
12. Mark `EX-IF0` complete as a design freeze while keeping execution, oracle-label generation, feature collection, `A11-OFF0`, policy activation, and test access closed.

## Rationale

Selecting B0 minimizes changes to the validated compute path and respects the published engineering decisions. The frozen sufficiency rule prevents choosing a convenient threshold after trajectory inspection.

Full suffix stability is more conservative than the first threshold crossing and directly checks persistence of a proposed stop. If only `K_ref` is sufficient, that is an admissible negative result rather than a reason to retune thresholds.

## Consequences

- `ex_if0_opened=true`, `ex_if0_complete=true`, and `exact_implementation_frozen=true`;
- `stage2_baseline` becomes the canonical exact reference for later oracle branches;
- B1/B2 remain published `reject_or_revise` candidates rather than being removed from the [evidence](../glossary_EN.md#term-evidence) chain;
- concrete spatial aggregate membership must be frozen by the next contract before label generation;
- this ADR authorizes no new computation or labels;
- a future [dangerous miss](../glossary_EN.md#term-dangerous-miss) is `stop` when `M^*(t)<0`;
- a negative early-sufficiency result must be retained.

## Rejected alternatives

- **Select B1 or B2 despite `reject_or_revise`.** This would contradict the published continuation screen.
- **Leave exact implementation undefined until predictor training.** Oracle labels would be ambiguous.
- **Use the first threshold crossing.** It does not protect against later boundary exit.
- **Tune thresholds after observing `t^*`.** This creates post-hoc leakage.
- **Collect features or activate stopping immediately.** This conflates oracle definition, diagnostics, and control admission.
