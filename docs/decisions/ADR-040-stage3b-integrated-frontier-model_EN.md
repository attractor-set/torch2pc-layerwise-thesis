# `ADR-040`: integrated frontier model

[Русская версия](ADR-040-stage3b-integrated-frontier-model.md)

- **Status:** accepted as a design freeze after `ADR-039`; [execution](../glossary_EN.md#term-execution) is not authorized
- **Date:** 2026-07-23

## Context

ADR-039 froze DONE / UNKNOWN / SWEEP, separate compute and diagnostic budgets,
and fail-closed semantics. The follow-up clarification found two overloads:

1. UNKNOWN denoted both lack of knowledge and the transition to another
   analytic;
2. SWEEP could be read as either one next sweep or the full [fallback](../glossary_EN.md#term-fallback) suffix.

The A0 / A1 / A2 observation levels and their cost also had to be integrated
without collapsing PC-TREF semantics, the PC-CATM mechanism, and [QWake-PC](../glossary_EN.md#term-qwake-pc)
orchestration.

## Decision

1. Keep ADR-039 unchanged as the preceding normative layer.
2. Introduce an integrated frontier containing the compute snapshot, cumulative
   pre-action representation, two remaining budgets, and provenance.
3. Freeze A0 as structural features, A1 as cheap device-side reductions, A2 as
   local reductions on a nested deterministic subsample, and O as post-action
   oracle only.
4. Introduce the action alphabet
   `ACCEPT_FRONTIER / ADVANCE_FRONTIER / COMPLETE_SUFFIX`.
5. Permit ACCEPT_FRONTIER only after positive PC-TREF admission.
6. Define ADVANCE_FRONTIER as exactly one registered adjacent observation
   transition or one canonical sweep.
7. Define COMPLETE_SUFFIX as the sole full fail-closed `stage2_baseline`
   fallback.
8. Map DONE to an ACCEPT_FRONTIER [candidate](../glossary_EN.md#term-candidate), UNKNOWN to an epistemic state, and
   one-step SWEEP to `ADVANCE_FRONTIER(compute)`.
9. Attach the complete [cost vector](../glossary_EN.md#term-cost-vector) to every frontier edge and account for O
   generation separately.
10. Require nested deterministic sampling, pre-action/post-action separation,
    non-interference, and complete provenance.
11. Freeze PC-TREF as admission semantics, PC-CATM as mechanism [evidence](../glossary_EN.md#term-evidence), and
    QWake-PC as future transition orchestration.
12. Keep the model deterministic, offline, and shadow-only.
13. Do not open label generation, feature collection, A11-OFF0, recursive
    aggregates, policy activation, or the test split.

## Machine boundary

```text
integrated_frontier_model_frozen=true
frontier_action_alphabet=ACCEPT_FRONTIER,ADVANCE_FRONTIER,COMPLETE_SUFFIX
observation_level_order=A0,A1,A2,O
nested_deterministic_sampling_required=true
pre_action_post_action_separation_required=true
observer_non_interference_required=true
frontier_edge_cost_vector_required=true
oracle_cost_separate_from_deployable_cost=true
pc_tref_role=admission_semantics
pc_catm_role=mechanism_evidence
qwake_pc_role=frontier_orchestration
integrated_frontier_controls_execution=false
oracle_label_generation_open=false
feature_collection_permitted=false
a11_off0_execution_open=false
recursive_aggregate_execution_open=false
policy_activation_permitted=false
test_dataset_access=false
full_stage3b_campaign_complete=false
```

## Consequence

The next admissible slice is limited to pure frontier types, an adjacent-edge
registry, deterministic sampling, cost accounting, and synthetic
non-interference checks. Scientific collection requires a separate contract,
[runtime](../glossary_EN.md#term-runtime) preflight, and authorization.
