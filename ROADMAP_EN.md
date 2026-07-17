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

## Stage 15 — B1/B2 preregistration — complete

B1 `isolated_layer_vjp`, B2 `composite_vjp`, the shared overview, and ADR-014.
They are frozen. Publication tag `stage3b-b1-b2-prereg-v1` preserves those
definitions unchanged. `ECZ`, local sweeps, and `QWake-PC` are outside B1/B2
and cannot be retrofitted into them.

## Stage 16 — B1/B2 implementation and candidate gates — current stage

B1 implementation and the B1 equivalence smoke harness are merged into `main`.
The next permitted step is separate CPU `float64` and ROCm `float32` smoke
execution, full-trajectory aggregation, and sealed `EQ-B1`.

- B2 remains closed until positive sealed `EQ-B1`;
- shared profiling remains closed until positive `EQ-B1` and `EQ-B2`;
- scientific failures are retained;
- design-only future-policy updates do not block B1 smoke execution.

## Stage 17 — `EX-IF0`, passive diagnostics, and neutral branches

After `EQ-B1`, `EQ-B2`, and matched exact-candidate profiling, select an
admissible exact implementation and freeze `EX-IF0` before policy-label
creation. Then run `A11-OFF0`: collect passive PC-CATM representations and
branch an identical snapshot into the B1/B2-contract labels `stop`/`native_one`/`exact_one`.
Those branches remain offline labels and are not controller actions.

Active `ECZ` use is forbidden before `EX-IF0`. See the
[future-policy boundary](docs/stage3b-future-policy-boundary_EN.md).

## Stage 18 — `A11-OFF1`, ECZ-targeted local sweep, and offline screening

After `EX-IF0`, a separate preregistration may add the counterfactual branch
`local_sweep(block_id)`. `ECZ` may select only a candidate block; local-action
utility must pass a separate `exact_verification` gate against `full_exact`.

Screening is sequential:

1. `cost_feasibility`: total policy cost must remain below the corresponding
   full exact-sweep cost;
2. `safety`: exactly `zero_dangerous_misses` is allowed;
3. `net_efficiency`: diagnostics, predictor, local sweep, fallback, and
   control-plane costs are included;
4. Pareto screening selects `0–3` finalists and does not guarantee that any
   admissible candidate exists.

Only after separate predictor and controller preregistration is the
hierarchical policy evaluated in shadow mode:

```text
stop
→ ECZ-targeted local sweep
→ full exact sweep
→ fallback_exact
```

`controls_execution=false` remains in force until shadow safety and end-to-end
cost gates pass. `A-Max` is conditional and opens only after positive shadow
evidence. See the [QWake-PC design](docs/qwake-pc-design_EN.md) and
[ECZ local-sweep design](docs/ecz-targeted-local-sweep_EN.md).

## Stage 19 — final freeze and test evaluation

Freeze implementation, features, thresholds, predictor, fallback, and the
statistical plan before one final test evaluation.

## Stage 20 — thesis and article

Integrate Stage 1/2, Stage 3A, B0, `SI-MA0`, `SI-MA1`, B1/B2, and available
Scenario A results. Mark unexecuted extensions as future work.
