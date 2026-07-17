# Roadmap

[Русская версия](ROADMAP.md)

The roadmap separates completed, permitted, and blocked work. Every transition
requires verified artifacts, preserved claim boundaries, and a separate
decision gate.

## Stages 1–10 — complete

Infrastructure and pilot, Stage 1/2, Stage 3A, Stage 3B B0 evidence, and B0
statistical/engineering analysis are complete. The test split remained closed
through Stage 3A and Stage 3B.

Publication tags include `stage3a-statistical-publication-v1`,
`stage3b-b0-evidence-v1`, and `stage3b-b0-analysis-evidence-v1`.

## Stage 11 — Scenario A and initial theory — complete

`ADR-012` froze PC-TREF Balanced Core, PC-CATM, and Scenario A. `ECZ` has the
single meaning `Error-Cancellation Zone`; B0 remains immutable.

## Stage 12 — validity controls and `SI-MA0` — complete

Shortcut/equivalence controls, observer non-interference, deterministic
mechanism controls, and `SI-MA0` mechanism attribution are complete.
`SI-MA0` passed `REC`, `OBS`, `VER`, and `CMP`, failed `COST`, and retained a
global failure. The uncovered residual motivated a separate observer-calibration
experiment rather than a frozen-contract change.

## Stage 13 — `SI-MA1` observer-calibrated closure — complete

- preregistration: `stage3b-si-ma1-prereg-v1`;
- implementation: `stage3b-si-ma1-implementation-v1`;
- confirmatory execution: `stage3b-si-ma1-confirmatory-execution-v1`;
- final decision: `stage3b-si-ma1-confirmatory-v1`;
- 10 model seeds and 180 matched blocks;
- one-sided bootstrap upper bound below threshold `0.01`;
- `CAL-COST-MA1=true`, `SI-MA1=pass`;
- `SI-MA0` unchanged and `ECZ` evaluator cost excluded.

## Stage 14 — theoretical freeze before B1/B2 — complete

Operational PC-TREF/PC-CATM semantics, regret, norm contracts, precision-
masked zero, the cost vector, and cost separation are published under ADR-013.

## Stage 15 — B1/B2 preregistration — current publication step

B1 `isolated_layer_vjp`, B2 `composite_vjp`, the shared overview, and ADR-014
are frozen. B1 implementation opens after the publication tag; B2 opens after
sealed `EQ-B1`. Block/chunk B2 requires a new protocol.

## Stage 16 — B1/B2 implementation and candidate gates

- implement B1 separately and pass deterministic/CPU controls;
- run controlled ROCm smoke and full-trajectory `EQ-B1`;
- after sealed `EQ-B1`, open B2 separately;
- run direct baseline/B2 and B1/B2 gates;
- open shared profiling only after `EQ-B1` and `EQ-B2`;
- retain negative and mixed results.

## Stage 17 — `EX-IF0`, passive diagnostics, and `A11-OFF0`

Freeze the selected exact implementation before label creation. Then collect
passive PC-CATM representations and branch an identical snapshot into policy-
neutral `stop`/`native_one`/`exact_one` outcomes while retaining utility/regret,
temporal history, feature cost, transitions, and provenance. The independent
unit is `model_seed`; the test split remains closed.

## Stage 18 — `A11-OFF1`, predictor, exact verification, and shadow `QWake-PC`

- run offline Pareto screening of nested $\phi_k$, features, and thresholds by
  regret, dangerous misses, and the complete cost vector;
- freeze representation, labels, split, Pareto rule, and fallback before
  confirmatory access;
- preregister the predictor separately with `model_seed` grouping;
- run counterfactual exact verification from an identical state;
- start in shadow mode;
- preregister hysteresis as stop/wake thresholds, persistence, and emergency
  `fallback_exact`, not as a substitute for utility;
- permit active allocation only after safety/end-to-end gates.

## Stage 19 — final freeze and test evaluation

Freeze implementation, features, thresholds, predictor, fallback, and the
statistical plan before one final test evaluation.

## Stage 20 — thesis and article

Integrate Stage 1/2, Stage 3A, B0, `SI-MA0`, `SI-MA1`, B1/B2, and available
Scenario A results. Mark unexecuted extensions as future work.
