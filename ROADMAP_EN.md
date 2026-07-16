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

## Stage 14 — theoretical freeze before B1/B2 — current publication step

- separate partition-based quotient from nontransitive threshold proximity;
- define required equivalence and safety through decision regret;
- formalize task-relative defect;
- freeze precision-masked zero and explicit norm contracts;
- use a cost vector and preregistered scalarization/Pareto rule;
- separate diagnostic-mechanism, observer, and control-plane costs;
- record the decision in `ADR-013`;
- update paired documentation without changing sealed evidence.

After merge and tagging, the B1/B2 theoretical prerequisite is satisfied.

## Stage 15 — B1/B2 preregistration — next

Prepare separate candidate contracts for B1 isolated-layer probes and B2
composite/block-composite probes. Each contract freezes the reference and
candidate boundary, state/belief/RNG restoration, numerical-equivalence
endpoints and tolerances, norm contracts, decision-regret and fallback
semantics, the cost vector and primary selection rule, execution matrix,
independent unit, replacement policy, and immutable provenance layout.
Preregistration is not implementation permission.

## Stage 16 — B1/B2 implementation and candidate gates

After tagged preregistration, implement candidates on a separate branch, run
deterministic and CPU structural tests, controlled ROCm smoke, and numerical
equivalence before full profiling. Retain negative and mixed results.
Confirmatory execution requires another decision gate.

## Stage 17 — `EX-IF0` and passive diagnostics

Freeze the selected exact implementation before label creation. Then collect
passive PC-CATM representations and compare preregistered $\phi_k$ levels on a
regret/cost frontier.

## Stage 18 — predictor, exact verification, and `QWake-PC`

Use model-seed splits, counterfactual exact verification from identical state,
shadow mode first, and active full-sweep allocation only after safety and
end-to-end runtime gates. Measure control-plane cost separately.

## Stage 19 — final freeze and test evaluation

Freeze implementation, features, thresholds, predictor, fallback, and the
statistical plan before one final test evaluation.

## Stage 20 — thesis and article

Integrate Stage 1/2, Stage 3A, B0, `SI-MA0`, `SI-MA1`, B1/B2, and available
Scenario A results. Mark unexecuted extensions as future work.
