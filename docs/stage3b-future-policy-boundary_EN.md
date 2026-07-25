# Stage 3B future policy and mechanism-selection boundary

[Русская версия](stage3b-future-policy-boundary.md)

## Purpose

This document separates sealed exact-method experiments from future policy
and computational-mechanism selection. It does not authorize
[execution](glossary_EN.md#term-execution).

## Immutable scope

B1/B2 contracts, their preregistration, the `isolated_layer_vjp` and
`composite_vjp` definitions, and sealed [evidence](glossary_EN.md#term-evidence)
remain unchanged. `ECZ`, `LOCAL_COMPUTE`, the predictor, and hysteresis are not
retrofitted into those candidates.

## Active sequence

```text
EX-IF0
→ QW-4B-DOC-R1
→ QW-4B-F-v2
→ QW-4B-E-v2
→ QW-LC0 → QW-LC1 → QW-LC2 → QW-LC3
→ QW-LC4-I → QW-LC4-F → QW-LC4-E
→ QW-5
→ C1 → C2 → C3 → R
```

The old active `QW-6`–`QW-10` labels are replaced by campaign roles. They may
remain only in historical records.

## Normative admission order

1. post-action label integrity and no pre-action leakage;
2. reproducibility of the registered response;
3. bounded [decision regret](glossary_EN.md#term-decision-regret);
4. full-cost feasibility;
5. zero dangerous misses;
6. positive net efficiency;
7. Pareto screening;
8. policy preregistration;
9. shadow-mode evidence;
10. conditional active mode.

A later gain cannot offset an earlier failure. Zero admissible candidates is a
valid scientific result.

## Action hierarchy

```text
STOP
LOCAL_COMPUTE
├── LOCAL_SWEEP(block_id)
└── ANALYTIC_COMPLETION(candidate_id)
FULL_EXACT
FALLBACK_EXACT
```

Until a separate admission decision, every action is a shadow proposal:

```text
controls_execution=false
```

## Analytic-completion boundary

Admission of an analytic [candidate](glossary_EN.md#term-candidate) requires a separate scope, mandatory
responses, resource model, matched validation, and an exact reserve path. Response
equivalence does not automatically transfer to mechanism or cost.

The first [candidate](glossary_EN.md#term-candidate) is restricted to
`fixedpred_eta1_wavefront_completion_v1`. Generalization to `Strict`, arbitrary
`eta`, arbitrary graphs, or full trajectories is forbidden without a new
decision.

## Compatibility with the previously frozen boundary

The following machine-readable markers remain for compatibility with previously
frozen design checks:

```text
local_sweep(block_id)
full_exact
fallback_exact
cost_feasibility
zero_dangerous_misses
net_efficiency
0–3
shadow
A-Max
```

`QWake-SPC` remains outside the current master's-thesis boundary. Its mention
does not permit an experiment, open execution, or change the admission order.


## Test split and `A-Max`

[Test-dataset access](glossary_EN.md#term-test-dataset-access) is closed for
mechanism, feature, threshold, candidate, and policy selection. `A-Max` opens
only after successful shadow validation, end-to-end saving, and a separate
decision. Otherwise the work ends at the bounded variant without rewriting a
negative result.
