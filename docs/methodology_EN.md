# Methodology

[Русская версия](methodology.md)

This document describes the completed `v1.0.0` dissertation methodology.
Historical protocols and authorizations remain in their own files; publication
does not open a new scientific [execution](glossary_EN.md#term-execution).

## Research principle

The work follows a protocol-first sequence: question → operational definition →
frozen test → measurement → registered claim status. A result at one level is
not automatically transferred to another.

The primary [independent statistical unit](glossary_EN.md#term-statistical-unit)
is an independently trained model with its own `model_seed`; images, batches,
and layers are not treated as independent model replications.

## Experimental-program sequence

1. C0/C1 — structural and numerical implementation controls;
2. pilot [configuration](glossary_EN.md#term-configuration) selection without final test evaluation;
3. Stage 1 — final quality and registered equivalence;
4. Stage 2 — quality-surface reproduction and timing;
5. Stage 3A — layer-wise gradients and representation similarity;
6. Stage 3B B0 — [profiling](glossary_EN.md#term-profiling) and cost localization;
7. SI-MA0/SI-MA1 — decomposition of `state_inference` and [observer cost](glossary_EN.md#term-observer-cost);
8. B1/B2 — exact alternative computational organizations and equivalence checks;
9. [matched profiling](glossary_EN.md#term-matched-profiling) of B0/B1/B2 plus a
   separate resource continuation criterion;
10. [QWake-FP](glossary_EN.md#term-qwake-fp) C1/C2 — action admissibility, recognizability, and economics;
11. T21–T24 — terminology, structure, and scientific-semantic closure of the
    manuscript without another scientific execution.

## Stage 3B: correctness and cost are separate

B1/B2 remain [candidates](glossary_EN.md#term-candidate) after passing numerical
checks. Functional/trajectory equivalence is evaluated separately from the
resource continuation criterion. Passing B1/B2 therefore does not establish
superiority over the [baseline](glossary_EN.md#term-baseline), while
`reject_or_revise` at the resource criterion does not undo passed numerical
equivalence.

## QWake-FP operational semantics

[QWake-FP](glossary_EN.md#term-qwake-fp) is the bounded implementation of the
general [QWake-PC](glossary_EN.md#term-qwake-pc). Each pre-action state is
compared through two paths:

```text
state
├─ fixedpred_eta1_wavefront_completion_v1
│  └─ candidate required response
└─ complete_suffix_stage2_baseline_v1
   └─ exact required response
```

The first path uses [analytic completion](glossary_EN.md#term-analytic-completion);
the second is the exact reference and [fallback](glossary_EN.md#term-fallback).
`EARLY_ADMISSIBLE` means that the registered analytic action is admissible with
respect to the required response of the exact suffix; it does not mean that all
further computation disappears. Analytic-completion cost is included in the
measured compute cost.

## QWake-FP C2 evaluation

The frozen family contains 2,625 scalar rules. Each rule is evaluated
separately for dangerous accepts, coverage, full decision cost, and aggregate
saving relative to the registered residual-compute estimand.

Decision order is dangerous-accept constraint → non-zero coverage → net
economics. The best zero-observed-danger rule is `compute_step >= 5`; it is a
temporal fixed-prefix boundary. Its 216/756 coverage contains 108 preterminal
step-5 records and 108 terminal-boundary step-6 records.

## Claim statuses

Descriptive analysis is not retrospectively relabeled as confirmatory
[evidence](glossary_EN.md#term-evidence). The final registry uses only
`supported`, `rejected`, `descriptive`, and `not_tested`.

For QWake, four distinct boundaries are preserved: C08 `supported` for bounded
selective recognizability on the frozen calibration surface; C09 `rejected`
under full decision-cost accounting; C10 `not_tested`, because marginal cost of
a minimal recognizer is a different estimand and was not measured; and C11
`not_tested`, because confirmatory C3 was not opened by the original protocol.

## Limitations

Claims are bounded to registered datasets, the `lenet_classic`
[architecture](glossary_EN.md#term-architecture), Torch2PC, seeds, numerical
tolerances, and frozen hardware/software environments. PC-CATM has a
mechanistic diagnostic status: superiority of its mechanism-aware features was
not directly tested. Zero observed dangerous accepts on the finite calibration
surface does not establish population-level safety.
