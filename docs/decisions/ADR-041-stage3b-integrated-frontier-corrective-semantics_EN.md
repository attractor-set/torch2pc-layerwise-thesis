# `ADR-041`: integrated-frontier corrective semantics

[Русская версия](ADR-041-stage3b-integrated-frontier-corrective-semantics.md)

- **Status:** accepted as a corrective design freeze after `ADR-040`; [execution](../glossary_EN.md#term-execution) is not authorized
- **Date:** 2026-07-23

## Context

ADR-039 froze DONE / UNKNOWN / SWEEP semantics, and ADR-040 introduced the
integrated frontier. A follow-up audit found five areas that required
clarification without retrospectively rewriting accepted decisions:

1. O was listed in one order with deployable A0 / A1 / A2 even though it is a
   post-action oracle only;
2. global monotonicity conflicted with a transition to a new snapshot whose
   current observation returns to A0;
3. measurement and decision [cost vectors](../glossary_EN.md#term-cost-vector) lacked an explicit mapping;
4. DONE could be read both as an admitted outcome and as an admission
   [candidate](../glossary_EN.md#term-candidate);
5. the transition alphabet did not expose a cheap analytic step as an
   independent way to advance the frontier.

The novelty-boundary audit also showed that adaptive stopping, feature
acquisition, selective prediction, value of computation, and a posteriori
certification are prior research directions. The project contribution must be
bounded to their protocol-constrained integration for a partial FixedPred
training trajectory relative to the full exact suffix.

## Decision

1. Keep ADR-039 and ADR-040 unchanged as historical decisions.
2. Make ADR-041 normative for the current interpretation of transitions,
   admission, cost, the oracle boundary, and mandatory research scope.
3. Limit the deployable observation axis to A0 -> A1 -> A2. Account for O
   separately as a post-action oracle unavailable to any action proposal.
4. Represent the frontier as `F(t, A_i, H)`, where H is immutable history of
   acquired analytic results and certificates.
5. Retain the top-level alphabet ACCEPT_FRONTIER / ADVANCE_FRONTIER /
   COMPLETE_SUFFIX, while splitting ADVANCE_FRONTIER into adjacent
   OBSERVATION, ANALYTIC, and COMPUTE kinds.
6. Permit an analytic transition before the first sweep, between sweeps, or in
   place of the next sweep when it is preregistered, uses pre-action data only,
   and has measured cost.
7. Separate exact certificates, conservative certified bounds, and
   statistical or heuristic estimates. The latter cannot directly authorize
   ACCEPT_FRONTIER and requires a frozen risk-control procedure.
8. Define monotonicity locally: within one snapshot, observation level and
   analytic history can only expand. A COMPUTE transition creates snapshot
   t+1 with current A0 while preserving append-only provenance and history.
9. Separate the raw edge measurement vector from the decision [cost vector](../glossary_EN.md#term-cost-vector).
   Require a frozen mapping between them and forbid implicit scalarization and
   double counting.
10. Treat DONE as an already admitted ADR-039 shadow outcome. A non-admitted
    record is called `accept_candidate` only and is not an action. Positive
    PC-TREF admission converts it to DONE, whose canonical shadow
    interpretation is ACCEPT_FRONTIER.
11. Bound the mandatory thesis core to temporal prefixes of one
    `stage2_baseline`, A0 / A1 / A2, a finite frozen analytic registry,
    deterministic shadow replay, and COMPLETE_SUFFIX.
12. Keep spatial recursive aggregates, learned routing, spike-like dynamics,
    and active control as conditional extensions.
13. Register mandatory comparisons against the full suffix, a fixed sweep
    budget, a simple prediction-error or residual threshold, A0-only, a fixed
    A0 -> A1 -> A2 cascade, the deterministic analytic registry,
    cheapest-first, and an offline-oracle upper bound.
14. Do not open scientific collection, oracle-label generation, A11-OFF0,
    recursive-aggregate execution, policy activation, or the test split.

## Normative precedence

```text
adr039_authority=dus_outcome_semantics
adr040_authority=historical_integrated_frontier_design
adr041_authority=current_transition_admission_cost_and_scope_semantics
adr041_refines_adr040_fields=observation_oracle_boundary,transition_kinds,monotonicity,cost_mapping,admission,mandatory_scope
historical_adr_rewrite_permitted=false
```

## Machine boundary

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

## Prior-art and claim boundary

Adaptive [predictive coding](../glossary_EN.md#term-predictive-coding) stopping has a direct neighbor in
[Hybrid Predictive Coding](https://doi.org/10.1371/journal.pcbi.1011280).
The general mechanisms of adaptive computation, active feature acquisition,
selective prediction, and internal computation selection are represented by
[Adaptive Computation Time](https://arxiv.org/abs/1603.08983),
[Joint Active Feature Acquisition](https://proceedings.neurips.cc/paper_files/paper/2018/hash/e5841df2166dd424a57127423d276bbe-Abstract.html),
[SelectiveNet](https://proceedings.mlr.press/v97/geifman19a.html), and
[Learning to select computations](https://arxiv.org/abs/1711.06892).

The package therefore does not claim priority for the individual mechanisms.
Its testable contribution boundary is the protocol-first integration of
task-relative sufficiency, internal diagnostic acquisition, analytic
certification, and risk-controlled adaptive computation for partial FixedPred
training trajectories relative to an exact canonical suffix.

## Consequence

The next admissible slice is limited to pure types, a finite adjacent-edge
registry, synthetic certificates, explicit cost mapping, non-interference, and
regression guards. Scientific execution requires a separate contract, [runtime](../glossary_EN.md#term-runtime)
preflight, and authorization.
