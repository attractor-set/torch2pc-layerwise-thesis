# Research questions

[Русская версия](research-question.md)

This document records the **final `v1.0.0` dissertation questions and answers**.
Historical preregistration and protocol formulations remain in their frozen
files and are not treated as the current plan.

## Starting problem

Matching final quality between BP and predictive-coding regimes establishes
neither similarity of internal mechanism, equality of compute cost, nor the
ability to safely reduce residual computation. The dissertation therefore
separates three research questions.

## RQ1 — behavior and internal mechanism

> Under what registered conditions do PC regimes preserve the required final-
> quality surface relative to BP, and how close are their layer-wise gradients
> and representations to BP?

Final answer: C01 and C02 are `supported` within the studied domain. Stage 1/2
preserves the registered final-quality surface, while Stage 3A shows greater
observed FixedPred proximity to BP than Strict in gradient direction and
representations, together with reduced early-layer gradient norm.

## RQ2 — cost and computational organization

> Where is PC compute cost localized, and can exact alternative organizations
> pass functional/trajectory equivalence checks and a separate resource
> continuation criterion?

Final answer: C03–C06 are `supported`; C07 is `descriptive`.

- B0 localizes substantial cost to `state_inference`;
- `SI-MA0` retains the negative `COST-MA0` result;
- `SI-MA1` separately calibrates [observer cost](glossary_EN.md#term-observer-cost);
- B1 `isolated_layer_vjp` and B2 `composite_vjp` pass registered equivalence
  checks;
- [matched profiling](glossary_EN.md#term-matched-profiling) completes, but both
  [candidates](glossary_EN.md#term-candidate) receive `reject_or_revise` at the
  separate resource continuation criterion.

Numerical/trajectory equivalence therefore does not imply resource equivalence
and does not establish [baseline](glossary_EN.md#term-baseline) superiority.

## RQ3 — task-relative [QWake-FP](glossary_EN.md#term-qwake-fp) action

> Do preterminal states exist for which the registered analytic action is
> admissible relative to the exact suffix; can a non-zero subset be recognized
> from pre-action data with zero observed dangerous accepts; and does positive
> saving remain under frozen full decision-cost accounting?

The tested special case is [QWake-FP](glossary_EN.md#term-qwake-fp) for
`FixedPred`, `eta=1`, and `stage2_baseline`. Canonical early action replaces the
remaining iterative suffix with [analytic completion](glossary_EN.md#term-analytic-completion)
`fixedpred_eta1_wavefront_completion_v1`; exact
`complete_suffix_stage2_baseline_v1` remains the reference and
[fallback](glossary_EN.md#term-fallback) path.

The final answer has four parts:

1. **C08 `supported`**: the bounded calibration surface contains preterminal
   `EARLY_ADMISSIBLE` records and a non-zero selectively recognizable subset
   with zero observed dangerous accepts;
2. the best rule is `compute_step >= 5`, i.e. a **sufficient temporal FixedPred prefix**
   rather than demonstrating input-dependent adaptivity;
3. **C09 `rejected`**: none of 2,625 rules combines zero observed dangerous
   accepts, non-zero coverage, and positive aggregate net saving under frozen
   full decision-cost accounting;
4. **C10/C11 `not_tested`**: marginal [runtime](glossary_EN.md#term-runtime) cost
   of a minimal recognizer was not measured, and the original-chain C3 did not
   open.

Registered 216/756 coverage belongs to the full calibration surface and
contains 108 preterminal step-5 records plus 108 terminal-boundary step-6
records. Zero observed dangerous accepts does not establish population-level
safety.

## Theoretical framework

- [PC-TREF](glossary_EN.md#term-pc-tref) — distinct task-relative
  equivalence/sufficiency framework;
- [PC-CATM](glossary_EN.md#term-pc-catm) — distinct linked mechanistic
  diagnostic level;
- [QWake-PC](glossary_EN.md#term-qwake-pc) — general research control
  [architecture](glossary_EN.md#term-architecture);
- QWake-FP — bounded FixedPred implementation actually tested in the thesis.

PC-CATM motivates mechanism-aware features, but superiority of NCZ/ECZ/TNZ and
related channel/transport/compensation features was not directly established.
**Recursive spatial aggregates** and other extensions remain follow-up work.

## Generalization boundary

The dissertation does not claim universal PC/BP equivalence, universal
FixedPred superiority, population-level QWake-FP safety, input-dependent
adaptivity from C08, or economic non-viability of a minimal recognizer. Claims
remain bounded to the registered datasets, `lenet_classic`, Torch2PC, numeric
tolerances, seeds, and frozen hardware/software environments.
