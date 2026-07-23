# Stage 3B: FixedPred sufficiency and D/U/S

[Русская версия](STAGE3B-FIXEDPRED-SUFFICIENCY-DUS.md)

**Status:** planned; execution is not authorized.

## Plan purpose

Every transition requires a separate verifiable decision. A design freeze does
not authorize collection, collector implementation does not authorize a run,
collection does not permit post-hoc metric changes, and shadow replay does not
authorize control. Negative outcomes close the corresponding branch without
changing the criterion after results are observed.

## Stages

1. `DUS-0`: design freeze.
2. `DUS-1`: refactoring and synthetic validation.
3. `DUS-2`: Rosenbaum analytic positive control.
4. `DUS-3`: separate `A11-OFF0` freeze.
5. `DUS-4`: policy-neutral collector implementation.
6. `DUS-5`: runtime preflight and authorization.
7. `DUS-6`: oracle collection.
8. `DUS-7`: post-collection/pre-analysis freeze.
9. `DUS-8`: sufficiency opportunity analysis.
10. `DUS-9`: nested representation screening.
11. `DUS-10`: deterministic shadow replay.
12. `DUS-11`: conditional confirmatory evaluation.
13. `DUS-12`: thesis integration.

## Oracle collection

For every snapshot, a future authorized collector must:

1. retain the pre-action representation;
2. execute the full canonical suffix;
3. compute \(M^*(t)\);
4. determine \(t^*\);
5. measure the full cost vector;
6. retain provenance.

No policy controls execution.

## Representations

```text
phi_0 structural
phi_1 magnitude
phi_2 temporal
phi_3 PC-CATM
phi_4 compact directional
```

## Analysis decisions

```text
early_sufficiency_present
no_early_sufficiency
state_dependent
static_only
diagnostically_observable
diagnostically_unobservable
cost_feasible
cost_infeasible
```

## Invariants

```text
dangerous_done_count=0
post_action_feature_leakage=0
observer_interference_events=0
budget_overspend_events=0
post_terminal_acquisition_events=0
controls_execution=false
test_dataset_access=false
```

## Negative routes

Valid outcomes include no early sufficient prefix, no cheap observability,
cost-infeasible diagnostics, no state dependence, no incremental PC-CATM
value, and no greedy-routing advantage.
