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

## Stage 16 — exact candidates and [matched profiling](docs/glossary_EN.md#term-matched-profiling) — analysis executed and sealed, publication closed

Complete:

- B1 is implemented and sealed as confirmatory `EQ-B1` over 120/120 pairs;
- B2 is implemented and passed engineering smoke over 12/12 triples and 24/24
  comparisons;
- the candidate-aware matched-profiling runner is implemented;
- the fail-closed confirmatory-B2 requirement before production launch is
  frozen;
- confirmatory B2 is preregistered for 120 triples and 240 comparisons;
- confirmatory B2 is executed and sealed: 120/120 triples, 240/240 comparisons, `EQ-B2-CONFIRMATORY=pass`, and derived `EQ-B2`; evidence is preserved as `stage3b-b2-confirmatory-63885e5-v1`.

Current boundary:

```text
scientific_admission=open
candidate_aware_runner=complete
b2_confirmatory_decision=pass_sealed
b2_confirmatory_request_frozen=true
b2_confirmatory_admission=present
matched_profiling_request_refrozen=true
matched_profiling_request_refresh_required=false
matched_profiling_execution_open=false
matched_profiling_execution_complete=true
matched_profiling_runtime_validation=valid
matched_profiling_evidence=sealed
matched_profiling_analysis_protocol_frozen=true
matched_profiling_analysis_implementation_complete=true
matched_profiling_analysis_preexecution_hardening=complete
matched_profiling_analysis_execution_request_frozen=true
matched_profiling_analysis_runtime_preflight_implementation=complete
matched_profiling_analysis_runtime_preflight_frozen=true
matched_profiling_analysis_execution_authorization_present=true
matched_profiling_analysis_synthetic_validation=pass
matched_profiling_analysis_execution_open=false
matched_profiling_analysis_execution_complete=true
matched_profiling_analysis_results_present=true
matched_profiling_analysis_output_audited=true
matched_profiling_analysis_output_seal_frozen=true
matched_profiling_analysis_output_evidence=true
matched_profiling_analysis_publication_gate_frozen=true
matched_profiling_analysis_publication_action_complete=false
matched_profiling_analysis_open=false
runtime_authorization=issued_consumed
measurements_allowed=false
results_publication_permitted=false
release_draft_required=true
release_publication_permitted=false
full_stage3b_campaign_complete=false
```

Execution request `v1`, runtime preflight, and authorization were frozen before
computation. The single read-only attempt completed on verified `main`; the
18-file output, receipt, and independent audit are preserved without rerunning.
An external seal binds those artifacts and moves the unchanged output into
repository evidence without rewriting generated metadata.

Remaining Stage 16 transition; the publication gate is frozen:

1. execute the frozen fail-closed publication action: the remote release must
   be draft and non-immutable, analysis assets are uploaded before publication,
   and the successful action receives a separate receipt/status freeze.

Publication, superiority claims, and `EX-IF0` remain prohibited until that
action succeeds. Negative and mixed results must be retained.

## Stage 17 — `EX-IF0` and the recursive-aggregate oracle boundary

Only after the successful publication action, select and freeze B0 as the admissible exact
implementation through `EX-IF0`. Freeze the aggregate hierarchy and
counterfactual contract before label creation.

The initial temporal baseline `A11-OFF0` retains policy-neutral `stop`, `native_one`, and
`exact_one` branches. Identical snapshots then test preregistered nested
aggregates at a minimum of two scales: layers within a block and blocks within
the network. Every candidate records exact-reference regret, oracle margin
`M^*`, the complete cost vector, and provenance.

Stage decisions are:

- `E2`: existence of a cheaper sufficient partial aggregate;
- `E3`: state dependence of the oracle-optimal aggregate;
- `E5`: reuse of one normative semantics at two scales;
- `H0`: occupancy near the sufficiency boundary;
- `P0`: diagnostic opportunity without pre-action leakage.

A learned estimator, temperature, hysteresis, and `QWake-PC` do not control execution at
this stage. The independent unit is `model_seed`; the test split remains
closed.

## Stage 18 — `A11-OFF1`, margin estimator, predictor, and shadow recursive `QWake-PC`

This stage opens only after informative `E2/E3/P0` decisions. If `E3` fails, a
static aggregate replaces adaptive control.

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
