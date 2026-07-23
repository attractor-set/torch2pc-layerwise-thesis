# ADR-039: FixedPred sufficiency and `DONE / UNKNOWN / SWEEP`

[Русская версия](ADR-039-stage3b-fixedpred-sufficiency-dus-design.md)

- **Status:** accepted as a design freeze without [execution](../glossary_EN.md#term-execution) permission
- **Date:** 2026-07-23

## Context

EX-IF0 selected `stage2_baseline` as canonical exact reference and fail-closed
[fallback](../glossary_EN.md#term-fallback). Subsequent review clarified:

1. B0 measures a context-dependent cost surface, not varying prefix budgets.
2. B1/B2 match nominal allocation, not realized cost.
3. Mathematical preservation is stated separately within FixedPred and Strict.
4. Joint-VJP is an exact graph-organization control, not a shortcut.
5. The Rosenbaum special case is an analytic positive control.

## Decision

1. The mandatory next-stage method is FixedPred.
2. The exact graph and oracle source are `stage2_baseline`.
3. Temporal prefix study is mandatory.
4. Spatial recursive aggregates remain conditional.
5. The oracle alphabet is sufficient / insufficient.
6. The shadow alphabet is `DONE / UNKNOWN / SWEEP`.
7. `DONE` requires positive sufficiency admission.
8. Unresolved `UNKNOWN` becomes `SWEEP`.
9. Compute and diagnostic budgets remain separate.
10. Metrics follow safety → coverage → cost.
11. Greedy acquisition remains a shadow-only demonstrator.
12. Joint-VJP is not an action.
13. Rosenbaum control does not replace EX-IF0.
14. Execution, oracle-label generation, feature collection, policy activation,
    and test access remain closed.

## Machine boundary

```text
fixedpred_sufficiency_dus_design_frozen=true
fixedpred_sufficiency_method=fixedpred
fixedpred_sufficiency_exact_graph=stage2_baseline
rosenbaum_wavefront_role=analytic_positive_control
joint_vjp_role=exact_graph_organization_control
dus_controls_execution=false
oracle_label_generation_open=false
feature_collection_permitted=false
a11_off0_execution_open=false
policy_activation_permitted=false
test_dataset_access=false
full_stage3b_campaign_complete=false
```

## Consequence

The next admissible slice is limited to refactoring and synthetic validation.
Scientific execution requires separate contracts, preflight, and
authorization.
