# Stage 3B integrated frontier model

[Русская версия](stage3b-integrated-frontier-model.md)

**Status:** consolidated design freeze under ADR-041; [execution](glossary_EN.md#term-execution), oracle-label generation, feature collection, and control remain closed.

## 1. Purpose and normative hierarchy

This document consolidates the current semantics for FixedPred sufficiency,
observation cost, cheap analytic steps, and future [QWake-PC](glossary_EN.md#term-qwake-pc) orchestration. It
does not alter FixedPred dynamics, the `stage2_baseline` exact reference, or
EX-IF0.

```text
ADR-039 = DONE / UNKNOWN / SWEEP outcomes
ADR-040 = historical first integrated-frontier freeze
ADR-041 = current transition, admission, cost, and scope semantics
```

ADR-039 and ADR-040 are not rewritten. ADR-041 governs the fields it explicitly
refines.

## 2. Architectural separation

```text
PC-TREF  = sufficiency, bounded regret, and admission semantics
PC-CATM  = mechanism model and interpretable [evidence](glossary_EN.md#term-evidence) source
QWake-PC = future orchestration of registered transitions
executor = canonical stage2_baseline trajectory
```

PC-TREF decides whether the current frontier may be accepted relative to the
registered [endpoint](glossary_EN.md#term-endpoint). PC-CATM may provide features, exact identities, or
conservative bounds but cannot authorize an action by itself. QWake-PC selects
only preregistered transitions and remains `controls_execution=false` pending a
separate decision.

## 3. Frontier state

For the mandatory temporal path:

```math
\mathcal F_{t,i,H}=\left(
S_t,R_{A_i},H,B^{\mathrm{compute}}_{\mathrm{rem}},
B^{\mathrm{diag}}_{\mathrm{rem}},P
\right).
```

Here, $S_t$ is the immutable snapshot after $t$ canonical sweeps, $R_{A_i}$ is
cumulative pre-action representation, $H$ is append-only analytic-result and
certificate history, the two budgets separate further compute from [evidence](glossary_EN.md#term-evidence)
acquisition, and $P$ retains model, data, RNG, graph, and implementation
provenance.

The mandatory core uses temporal prefixes of one `stage2_baseline` only.
Spatial recursive aggregates remain conditional.

## 4. Observation and oracle

The deployable observation axis has exactly three nested levels:

```text
A0 -> A1 -> A2
```

A0 contains structural fields without tensor-value reads. A1 adds a finite set
of cheap device-side reductions. A2 adds local reductions on a nested
deterministic subsample.

```text
R_A0 = A0
R_A1 = A0 + A1
R_A2 = A0 + A1 + A2
```

O is not a fourth observation level. It is produced after the action by the full
canonical suffix, is excluded from deployable representation, is not a
transition, and is never exposed to the shadow controller.

## 5. Action and transition alphabet

The top-level alphabet remains:

```text
ACCEPT_FRONTIER
ADVANCE_FRONTIER
COMPLETE_SUFFIX
```

ADVANCE_FRONTIER performs exactly one adjacent transition kind:

```text
OBSERVATION = acquire the next A-level at fixed S_t
ANALYTIC    = run one registered pre-action analytic step
COMPUTE     = execute one next canonical sweep
```

An analytic step may occur before the first sweep, between sweeps, or instead
of the next sweep when its inputs are pre-action, it belongs to a finite frozen
registry, and its cost is measured. O is not an analytic step.

COMPLETE_SUFFIX executes the full remaining `stage2_baseline` and is the sole
fail-closed [fallback](glossary_EN.md#term-fallback).

## 6. Analytic results and admission

Three result classes are distinct:

1. an exact certificate;
2. a conservative certified bound;
3. a statistical or heuristic estimate.

An exact or conservative certificate may support PC-TREF admission. A
statistical estimate requires a separately frozen risk-control procedure and
cannot directly authorize ACCEPT_FRONTIER.

`accept_candidate` is an admission record, not an action. Positive admission
produces the ADR-039 outcome DONE, whose shadow action interpretation is then
ACCEPT_FRONTIER.

```text
accept_candidate -> PC-TREF admission -> DONE -> ACCEPT_FRONTIER
```

UNKNOWN remains an epistemic state. Historical SWEEP means one next canonical
sweep and maps to `ADVANCE_FRONTIER(kind=COMPUTE)`.

## 7. Monotonicity and transition graph

Monotonicity is local to one snapshot: A0 -> A1 -> A2 cannot roll back, H only
expands, and provenance is not rewritten.

A COMPUTE transition creates a new snapshot whose **current** observation is A0
while retaining append-only acquisition history and provenance:

```text
F(t,Ai,H) --COMPUTE--> F(t+1,A0,H')
```

The mandatory graph contains:

```text
F(t,A0,H) --OBSERVATION:A1--> F(t,A1,H)
F(t,A1,H) --OBSERVATION:A2--> F(t,A2,H)
F(t,Ai,H) --ANALYTIC:h_j----> F(t,Ai,H+{h_j})
F(t,Ai,H) --COMPUTE---------> F(t+1,A0,H')
F(t,Ai,H) --admitted-------> terminal_shadow_accept
F(t,Ai,H) --full_suffix----> terminal_canonical_reference
```

Unknown, unavailable, contract-invalid, or budget-exhausted states fail closed
through COMPLETE_SUFFIX.

## 8. Two cost levels

Raw edge measurements are retained losslessly:

```text
edge_measurement_vector =
  host_elapsed_ns,
  device_elapsed_ns,
  synchronization_events,
  device_to_host_bytes,
  temporary_peak_bytes,
  persistent_trace_bytes,
  acquisition_count
```

The decision [cost vector](glossary_EN.md#term-cost-vector) retains semantic categories:

```text
decision_cost_vector =
  compute,
  latency,
  memory,
  diagnostic,
  observer,
  control,
  fallback
```

A mapping `g` between them is frozen before analysis. Raw fields are not
implicitly summed, no quantity is counted twice, and scalarization requires a
separate registered rule. O-generation cost is research-labeling cost and is
excluded from deployable diagnostic cost.

## 9. Non-interference and time boundary

Observation and analytics are read-only and cannot change state, parameters,
buffers, gradients, RNG, the autograd path, or the canonical branch.

```text
observer_state_mutations=0
observer_parameter_mutations=0
observer_buffer_mutations=0
observer_rng_mutations=0
observer_autograd_path_changes=0
observer_interference_events=0
post_action_feature_leakage=0
```

M*, t*, the final endpoint, realized next-sweep utility, and the oracle-optimal
transition are unavailable before action.

## 10. Mandatory comparisons

```text
B0 full_canonical_suffix
B1 fixed_sweep_budget
B2 registered_prediction_error_or_residual_threshold
B3 A0_only
B4 fixed_A0_A1_A2_cascade
B5 deterministic_analytic_registry
B6 cheapest_first_frontier
B7 offline_oracle_upper_bound
```

B2 distinguishes the frontier from simple prediction-error early stopping. B7
is not deployable and supplies an opportunity upper bound only.

## 11. Novelty boundary

Adaptive stopping, active feature acquisition, selective prediction,
metareasoning, and analytic certification are prior research directions. The
project does not claim priority for those individual mechanisms.

The testable contribution is bounded to their protocol-first integration for
task-relative sufficiency, internal diagnostic acquisition, analytic
certification, and risk-controlled adaptive computation on partial FixedPred
training trajectories relative to an exact canonical suffix.

## 12. Mandatory scope

The mandatory thesis core is temporal FixedPred prefixes of one
`stage2_baseline`, A0 / A1 / A2, a finite frozen analytic registry,
deterministic shadow replay, safety-first admission, measured cost mapping, and
COMPLETE_SUFFIX as canonical fallback.

Recursive multiscale aggregates, learned routing, spike-like dynamics, and
active control are outside the mandatory core.

## 13. Machine boundary

```text
integrated_frontier_corrective_semantics_frozen=true
frontier_action_alphabet=ACCEPT_FRONTIER,ADVANCE_FRONTIER,COMPLETE_SUFFIX
frontier_advance_kinds=OBSERVATION,ANALYTIC,COMPUTE
deployable_observation_level_order=A0,A1,A2
oracle_level=O
oracle_availability=post_action_only
oracle_is_frontier_action=false
oracle_is_analytic_step=false
frontier_state_schema=F(t,A_i,H)
within_snapshot_observation_monotone=true
within_snapshot_analytic_history_monotone=true
compute_transition_resets_current_observation=A0
acquisition_history_append_only=true
provenance_monotone=true
analytic_registry_finite_and_frozen=true
analytic_steps_pre_action_only=true
analytic_step_is_not_free=true
exact_or_conservative_certificate_may_support_admission=true
heuristic_analytic_direct_accept=false
statistical_estimate_requires_frozen_risk_admission=true
done_semantics=admitted_shadow_outcome
accept_candidate_is_action=false
accept_frontier_requires_positive_admission=true
edge_measurement_vector_required=true
decision_cost_vector_required=true
measurement_to_decision_cost_mapping_required=true
implicit_cost_scalarization_forbidden=true
cost_double_counting_forbidden=true
mandatory_thesis_scope=temporal_fixedpred_prefix
recursive_multiscale_scope=conditional_extension
active_control_scope=outside_mandatory_core
integrated_frontier_controls_execution=false
oracle_label_generation_open=false
feature_collection_permitted=false
a11_off0_execution_open=false
recursive_aggregate_execution_open=false
policy_activation_permitted=false
test_dataset_access=false
full_stage3b_campaign_complete=false
```
