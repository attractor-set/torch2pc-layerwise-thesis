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

## Stage 16 — exact candidates and [matched profiling](docs/glossary_EN.md#term-matched-profiling) — analysis published and receipt frozen

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
matched_profiling_analysis_publication_action_complete=true
matched_profiling_analysis_publication_receipt_frozen=true
matched_profiling_analysis_open=false
runtime_authorization=issued_consumed
measurements_allowed=false
results_publication_permitted=true
release_draft_required=false
release_publication_permitted=true
release_publication_complete=true
ex_if0_protocol_frozen=true
ex_if0_opened=true
ex_if0_complete=true
exact_implementation_frozen=true
exact_implementation_candidate=stage2_baseline
minimum_sufficient_sweep_rule_frozen=true
ex_if0_execution_permitted=false
oracle_label_generation_open=false
feature_collection_permitted=false
a11_off0_execution_open=false
recursive_aggregate_execution_open=false
policy_activation_permitted=false
test_dataset_access=false
full_stage3b_campaign_complete=false
```

Execution request `v1`, runtime preflight, and authorization were frozen before
computation. The single read-only attempt completed on verified `main`; the
18-file output, receipt, and independent audit are preserved without rerunning.
An external seal binds those artifacts and moves the unchanged output into
repository evidence without rewriting generated metadata.

Stage 16 is complete: the fail-closed publication action succeeded, and the
exact remote receipt/status is frozen without rerunning the analysis.
Superiority claims, policy activation, and test access remain closed. Negative
and mixed results are retained.

## Stage 17

<!-- BEGIN STAGE3B-DUS-FUTURE-POLICY-COMPATIBILITY -->
### Compatible future-policy boundary

`EX-IF0` retains the canonical exact reference and fail-closed fallback.
`A11-OFF0` remains the policy-neutral snapshot and oracle-collection stage.
`A11-OFF1` may open only after informative gates; its predictor is evaluated
only in shadow mode and does not control execution.
<!-- END STAGE3B-DUS-FUTURE-POLICY-COMPATIBILITY -->
 — `EX-IF0` and the recursive-aggregate oracle boundary

The `EX-IF0 v1` design freeze is complete: `stage2_baseline` is selected as the
canonical exact reference and fail-closed fallback for `FixedPred` and `Strict`.
The decision epoch, full configuration-specific reference horizon,
task-relative endpoint, `rocm_float32` threshold profile, and full-suffix rule
for the minimum stably sufficient sweep are frozen. Execution and label
generation remain closed.

The next separate contract must freeze concrete spatial hierarchy membership
and `A11-OFF0` snapshot branching before labels are generated. The temporal
baseline retains policy-neutral `stop`, `native_one`, and `exact_one` branches;
under `v1`, the two one-step branches are an identity control for the selected
`stage2_baseline`. Identical snapshots then test preregistered nested aggregates
at a minimum of two scales: layers within a block and blocks within the network.
Every candidate records exact-reference regret, oracle margin `M^*`, the
complete cost vector, and provenance.

Stage decisions are:

- `E2`: existence of a cheaper sufficient partial aggregate;
- `E3`: state dependence of the oracle-optimal aggregate;
- `E5`: reuse of one normative semantics at two scales;
- `H0`: occupancy near the sufficiency boundary;
- `P0`: diagnostic opportunity without pre-action leakage.

A learned estimator, temperature, hysteresis, and `QWake-PC` do not control execution at
this stage. The independent unit is `model_seed`; the test split remains
closed.


## Stage 18 — `DUS-0` and `DUS-1`: freeze and refactoring

ADR-041 supplies current corrective semantics above unchanged ADR-039 and
ADR-040. The deployable observation axis is `A0 -> A1 -> A2`, while `O` is a
separate post-action oracle. ADVANCE_FRONTIER has OBSERVATION, ANALYTIC, and
COMPUTE kinds; `controls_execution=false`.

The mandatory thesis path is bounded to temporal FixedPred, a finite analytic
registry, deterministic shadow replay, and the canonical suffix. Recursive
spatial aggregates and active control are conditional.

ADR-039 freezes FixedPred, `stage2_baseline`, the EX-IF0 oracle,
the [Rosenbaum wavefront
control](docs/glossary_EN.md#term-rosenbaum-wavefront-control), and
[D/U/S decision semantics](docs/glossary_EN.md#term-dus-decision-semantics).

The first slice is limited to the new `stage3b_sufficiency` namespace,
separation of oracle, pre-action features, policy, and cost accounting,
schemas, pure types, synthetic tests, a finite deterministic analytic registry
with exact, conservative, and heuristic result classes, explicit mapping from
edge measurements to decision cost without double counting, non-interference,
local-monotonicity, and provenance checks.

Scientific execution remains closed.

## Stage 19 — `DUS-2` and `DUS-3`: positive control and contract

Test the Rosenbaum special case as an analytic component-completion positive
control. Then freeze A11-OFF0, the snapshot schema, temporal prefixes, optional
spatial aggregates, endpoint, cost fields, seeds, and the no-test boundary.

## Stage 20 — `DUS-4`–`DUS-7`: collector and oracle

Implement the policy-neutral collector, then separately freeze runtime
preflight and authorization. After authorized collection:

- retain pre-action representations;
- execute the full canonical suffix;
- compute `M^*(t)` and `t^*`;
- measure the complete cost vector;
- retain provenance;
- freeze estimands, thresholds, the risk-control procedure, and
  negative-result rules before comparative analysis.

No policy controls execution.

## Stage 21 — `DUS-8` and `DUS-9`: opportunity and representations

First determine whether an early sufficient prefix exists, is state-dependent,
is cheaply observable, and is economically feasible.

Then compare nested representations in the order dangerous DONE, safe
coverage, UNKNOWN burden, diagnostic cost, and context stability.

Use a static alternative if state dependence is absent.

## Stage 22 — `DUS-10`: deterministic shadow replay

Compare a fixed cascade, cheapest-first, greedy quality, greedy quality per
cost, all metrics, and an offline oracle sequence.

```text
controls_execution=false
```

The greedy policy is not treated as globally optimal.

## Stage 23 — conditional final freeze

Confirmatory evaluation opens only after nonzero safe coverage, admissible
dangerous-DONE risk, observer non-interference, cost feasibility, and
`model_seed` stability.

One final test evaluation requires a separate final freeze.

## Stage 24 — thesis and article

Integrate Stage 1/2, Stage 3A, B0, SI-MA0, SI-MA1, B1/B2, EX-IF0, and D/U/S
results. Mark unexecuted spatial, learned, and active extensions as future
work.

## Post-master's boundary — prospective PhD line

After the current critical path is complete, a separate `QWake-SPC` program may
move from QWake-PC
[spike-like control dynamics](docs/glossary_EN.md#term-spike-like-control-dynamics)
to native spikes, spike-native error transport, local learning, and
neuromorphic validation. This program is not Stage 21, does not open execution,
and does not change the master's-thesis completion criteria.
