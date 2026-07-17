# Realistic master's thesis plan

[Русская версия](masters-thesis-plan.md)

## 1. Current point

As of 16 July 2026, Stage 1/2, Stage 3A, Stage 3B B0, `SI-MA0`, and `SI-MA1`
are complete. The final `SI-MA1` result is published under
`stage3b-si-ma1-confirmatory-v1`: `CAL-COST-MA1=true`, while the negative
`COST-MA0` result remains unchanged. B0 and both SI experiments are immutable
[evidence](glossary_EN.md#term-evidence) packages.

The B1/B2 theoretical prerequisite is complete and published. This package
freezes separate B1/B2 contracts; after its publication tag, B1 implementation
is authorized.

## 2. Primary scientific line

1. [PC-TREF](pc-tref-balanced-core_EN.md) defines [task-relative equivalence](glossary_EN.md#term-task-relative-equivalence),
   [diagnostic quotient](glossary_EN.md#term-diagnostic-quotient), regret, and sufficiency boundaries.
2. [PC-CATM](pc-catm-operator-model_EN.md) defines canonical correction
   channels, `NCZ`, `ECZ`, `TNZ`, [state-error transport](glossary_EN.md#term-state-transport), and measurement norm
   contracts.
3. [Scenario A](stage3b-primary-scenario-a_EN.md) turns the theory into validity
   controls, exact candidates, [passive diagnostics](glossary_EN.md#term-passive-diagnostics), a predictor, exact
   verification, and a controller.

## 3. Mandatory scope

### Completed

- reproducible ROCm/Docker environment and frozen baselines;
- Stage 3A layer-wise evidence;
- B0 [execution](glossary_EN.md#term-execution), sealing, and engineering analysis;
- shortcut/observer/mechanism controls;
- `SI-MA0` and corrective `SI-MA1`;
- operational `PC-TREF`/`PC-CATM` semantics and ADR-013.

### Required before the main defense

- [candidate](glossary_EN.md#term-candidate)-specific B1/B2 preregistration and gates;
- `EX-IF0`, freezing the admissible exact implementation;
- passive PC-CATM diagnostics and registered-representation comparison;
- a [local predictor](glossary_EN.md#term-local-predictor) with `model_seed` splits;
- [counterfactual exact verification](glossary_EN.md#term-exact-verification);
- shadow-mode and final end-to-end evaluation;
- one final test evaluation after complete freeze.

### Limited extension

`PNZ`, additional architectures or datasets, and active `QWake-PC` are included
only if the mandatory path remains protected and a separate protocol exists.

## 4. Completion levels

### `A-Min`

The theoretical package, B1/B2 candidate gates, passive diagnostics, and
representation comparison are published. Negative candidate results are a
valid completion of the mechanistic contribution.

### `A-Core`

An admissible B1/B2 path, `EX-IF0`, predictor, counterfactual exact verification,
and shadow controller with regret/cost analysis are also complete.

### `A-Max`

Active control and broader transfer are added only after safety and end-to-end
gates.

## 5. Work sequence

### July–August 2026

- publish the theoretical package and ADR-013;
- prepare separate B1/B2 preregistration contracts;
- freeze numerical equivalence, regret, norms, [cost vector](glossary_EN.md#term-cost-vector), and stop rules;
- implement deterministic/unit controls after tagged preregistration.

### September–October 2026

- run controlled ROCm smoke and candidate-specific equivalence gates;
- make separate admission decisions for full [profiling](glossary_EN.md#term-profiling);
- run matched B1/B2 confirmatory campaigns for admitted candidates;
- freeze `EX-IF0`.

### November 2026 – January 2027

- collect passive PC-CATM features;
- run policy-neutral `A11-OFF0` with `stop`/`native_one`/`exact_one` branches;
- run offline `A11-OFF1` on the regret–cost frontier;
- freeze the representation and label protocol;
- preregister and train the predictor only on development splits by `model_seed`.

### February–March 2027

- run counterfactual exact verification;
- evaluate dangerous misses, unnecessary wakes, [fallback](glossary_EN.md#term-fallback), and tail latency;
- evaluate shadow-mode `QWake-PC` without changing the primary path.

### April–May 2027

- freeze final implementation, thresholds, and predictor [configuration](glossary_EN.md#term-configuration);
- run the one final test evaluation;
- close evidence manifests, bilingual reports, and claim boundaries.

### June 2027

- consolidate the thesis, article, limitations, and future work;
- perform a reproducible release audit.

## 6. Writing in parallel

The `PC-TREF`/`PC-CATM` theory, Stage 3A, B0, `SI-MA0`, and `SI-MA1` chapters
can be written now. B1/B2 and control chapters are updated only after their
frozen evidence packages.

## 7. Primary endpoints

- candidate/reference numerical equivalence;
- [decision regret](glossary_EN.md#term-decision-regret) and dangerous-miss rate;
- gradient and representation endpoints;
- device/wall time, memory, [saved tensors](glossary_EN.md#term-saved-tensors), and tail latency;
- diagnostic-mechanism, observer, control-plane, and fallback costs;
- end-to-end utility relative to the frozen exact reference.

## 8. Statistical contract

The independent unit is `model_seed`. Nested observations are reduced to
seed-level. Primary estimand, direction, bootstrap seed/replications,
multiplicity, and threshold are frozen in advance. The test split is not used
for selection.

## 9. Risk control

- B2 failure leaves B1 or canonical Strict;
- failure of both candidates remains a valid negative result;
- weak diagnostics leave a descriptive PC-CATM analysis;
- high regret or [control-plane cost](glossary_EN.md#term-control-plane-cost) blocks active control;
- the timeline protects `A-Min` before `A-Core`.

## 10. Contribution boundary

The intended contribution is a registered, mechanism-interpretable, cost-aware
test of which state distinctions must be preserved for a computational decision
under bounded regret. The thesis does not claim a global theory of zero or
universal representation minimality.
