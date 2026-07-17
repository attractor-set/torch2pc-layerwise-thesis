# Stage 3B B1/B2: exact-candidate preregistration

[Русская версия](stage3b-b1-b2-preregistration.md)

## Decision

After final `SI-MA1` and theory tag `stage3b-pc-tref-pc-catm-theory-v1`, two
separate contracts are frozen:

- B1 — `isolated_layer_vjp`;
- B2 — `composite_vjp`.

The paired prose and JSON files in `experiments/planned/`, this overview, and
ADR-014 are normative. The package contains no implementation, ROCm [execution](glossary_EN.md#term-execution),
or [evidence](glossary_EN.md#term-evidence) and does not alter B0, `SI-MA0`, `SI-MA1`, or the theoretical
foundation.

## Sequential admission

After the publication tag, only B1 implementation is authorized. B2 remains
closed until sealed `EQ-B1`; the shared [matched profiling](glossary_EN.md#term-matched-profiling) matrix remains closed
until `EQ-B1` and `EQ-B2`. Negative results are retained, and replacement is
allowed only for documented infrastructure failure.

B2 v1 is only `composite_vjp`. Block/chunk composite is not an automatic
[fallback](glossary_EN.md#term-fallback) and requires a separate preregistration.

## Numerical and engineering boundaries

Every [candidate](glossary_EN.md#term-candidate) is compared with `stage2_baseline` from an identical snapshot.
The complete sequence of beliefs, errors, and registered [endpoints](glossary_EN.md#term-endpoint) is checked,
not only [endpoint](glossary_EN.md#term-endpoint) loss. Zero dangerous admissions are permitted.

Primary timing uses `no_hooks`; structural counters use a separate
`counters_only` lane. [Observer cost](glossary_EN.md#term-observer-cost) is reported separately and is never hidden-
subtracted. Cost-vector benefit cannot compensate for numerical, trajectory, or
safety failure.

## Boundary to estimator, oracle, and `QWake-PC`

B1/B2 are exact implementation candidates, not control policies. They define no
estimator, oracle, cheap iteration, hysteresis, or offline policy selection. A
future cheap loop means only a read-only diagnostic and decision loop between
full exact sweeps; before separate admission it remains in [shadow mode](glossary_EN.md#term-shadow-mode) and does
not modify beliefs.

The permitted sequence after immutable `EQ-B1`/`EQ-B2` is:

```text
EX-IF0
→ A11-OFF0 policy-neutral counterfactual traces
→ A11-OFF1 offline Pareto screening
→ separate predictor preregistration
→ shadow QWake-PC
```

`A11-OFF0` branches one snapshot into `stop`, `native_one`, and `exact_one`.
These are counterfactual offline-[dataset](glossary_EN.md#term-dataset) labels rather than active-controller
actions. `A11-OFF1` compares nested representations, regret, dangerous misses,
and the complete [cost vector](glossary_EN.md#term-cost-vector) on development splits with `model_seed` as the
independent unit; the test split remains closed.

Inertia may appear later only as a separately preregistered hysteresis policy
guard: distinct stop/wake thresholds, a required persistence count, and
emergency `fallback_exact`. It does not replace utility/regret estimation and is
outside B1/B2.

## Closed claims

Positive equivalence does not establish speedup, memory benefit, full training-
trajectory equivalence, transfer, estimator quality, hysteresis safety, active-
control safety, or test performance. `EX-IF0`, passive label creation, the
predictor, and active `QWake-PC` require their own admission decisions.
