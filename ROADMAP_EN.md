# Roadmap

[Русская версия](ROADMAP.md)

The roadmap separates completed, permitted, and blocked work. Every transition
requires verified artifacts, preserved claim boundaries, and a separate
admission decision.

## Stages 1–10 — complete

Infrastructure and pilot work, Stage 1/2, Stage 3A, Stage 3B B0 evidence, and
B0 statistical and engineering analysis are complete. The test dataset
remained closed.

## Stage 11 — Scenario A and initial theory — complete

`ADR-012` froze PC-TREF Balanced Core, PC-CATM, and Scenario A. `ECZ` has the
single meaning `Error-Cancellation Zone`; B0 remains an immutable baseline.

## Stage 12 — validity controls and `SI-MA0` — complete

Shortcut/equivalence controls, observer non-interference, deterministic
mechanism controls, and `SI-MA0` are complete. `REC`, `OBS`, `VER`, and `CMP`
passed, while `COST` failed; the negative global outcome is retained.

## Stage 13 — `SI-MA1` — complete

`SI-MA1` preregistration, implementation, confirmatory execution, and final
decision are complete. Across ten `model_seed` values and 180 matched blocks,
`CAL-COST-MA1=true` and `SI-MA1=pass`. The `SI-MA0` result remains unchanged,
and the cost of a future `ECZ` evaluator is excluded.

## Stage 14 — theoretical freeze before B1/B2 — complete

Operational PC-TREF/PC-CATM semantics, regret, norm contracts,
`precision-masked zero`, the cost vector, and cost separation are published
under `ADR-013`.

## Stage 15 — B1/B2 preregistration — complete

B1 `isolated_layer_vjp`, B2 `composite_vjp`, the shared overview, and
`ADR-014` are frozen. Publication tag: `stage3b-b1-b2-prereg-v1`. B2
`block`/`chunk` variants are outside this contract and require separate
preregistration.

## Stage 16 — exact candidates and [matched-profiling](docs/glossary_EN.md#term-matched-profiling) preparation — current

Complete:

- B1 is implemented and passed deterministic, CPU, and ROCm controls;
- sealed `EQ-B1` is positive;
- B2 was implemented after B1 admission and passed the registered controls;
- sealed `EQ-B2` is positive;
- scientific admission for shared matched profiling is open;
- the frozen 288-cell request and manifest are built and validated;
- the candidate-aware runner is implemented.

Current boundary:

```text
scientific_admission=open
candidate_aware_runner=complete
runtime_authorization=not_issued
measurements_allowed=false
```

The remaining transition within Stage 16 is the separate ROCm/float32 runtime
freeze already retained by the frozen request. Documentation does not replace
a separate admission decision and does not authorize measurements.

After authorized execution, Stage 16 must conclude with matched B0/B1/B2
analysis, completeness and integrity checks, and evidence sealing. Negative and
mixed results must be retained.

## Stage 17 — `EX-IF0`, passive diagnostics, and `A11-OFF0`

Only after matched profiling is complete and sealed, select and freeze the
admissible exact implementation before label creation. Then collect passive
PC-CATM representations and branch an identical `snapshot` into policy-neutral
`stop`, `native_one`, and `exact_one` outcomes. Exact reference creates oracle
skip regret, oracle margin $M^*$, and the one-step sufficiency boundary;
pre-action features remain separate and receive no permission to control
execution. Utility, decision regret, temporal history, feature cost,
transitions, and provenance are also retained. The independent unit remains
`model_seed`; the test dataset remains closed.

## Stage 18 — `A11-OFF1`, predictor, exact verification, and shadow `QWake-PC`

- run offline screening of nested representations, boundary estimators,
  first-order horizons, features, and thresholds by regret, dangerous misses,
  and the complete cost vector;
- freeze the representation, labels, split, Pareto rule, and [fallback](docs/glossary_EN.md#term-fallback) before
  confirmatory access;
- preregister the predictor separately with `model_seed` grouping;
- run counterfactual exact verification from an identical state;
- start in shadow mode;
- preregister hysteresis as stop and wake thresholds, confirmation persistence,
  and emergency `fallback_exact`;
- permit active allocation only after safety and end-to-end cost gates.

## Stage 19 — final freeze and test evaluation

Freeze the implementation, features, thresholds, predictor, fallback, and
statistical plan. Only then permit one final test-dataset evaluation.

## Stage 20 — thesis and article

Integrate Stage 1/2, Stage 3A, B0, `SI-MA0`, `SI-MA1`, B1/B2, and the
available Scenario A results. Mark unexecuted extensions as future work.

## Post-master's boundary — prospective PhD line

After the current critical path is complete, a separate `QWake-SPC` program may
move from QWake-PC
[spike-like control dynamics](docs/glossary_EN.md#term-spike-like-control-dynamics)
to native spikes, spike-native error transport, local learning, and
neuromorphic validation. This program is not Stage 21, does not open execution,
and does not change the master's-thesis completion criteria.
