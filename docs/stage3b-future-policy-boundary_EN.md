# Stage 3B future-policy boundary

[Русская версия](stage3b-future-policy-boundary.md)

## Purpose

This document separates sealed exact-[candidate](glossary_EN.md#term-candidate) experiments from future policy
research. It is a design-only boundary and does not permit [execution](glossary_EN.md#term-execution).

## Immutable scope

The following remain unchanged:

- `STAGE3B-B1-CONTRACT.json`;
- `STAGE3B-B2-CONTRACT.json`;
- `stage3b-b1-b2-prereg-v1`;
- B1 `isolated_layer_vjp` and B2 `composite_vjp` definitions;
- B1/B2 [evidence](glossary_EN.md#term-evidence) and decisions.

`ECZ`, `local_sweep(block_id)`, predictor, hysteresis, and `QWake-PC` are not
retrofitted into B1/B2.

## Phase sequence

| Phase | Permitted | Forbidden |
|---|---|---|
| B1/B2 gates | exact-candidate equivalence and [profiling](glossary_EN.md#term-profiling) | ECZ control, policy selection |
| after `EX-IF0` | [passive diagnostics](glossary_EN.md#term-passive-diagnostics), neutral offline labels | active control |
| `PC-TREF-SB` | oracle margin, pre-action estimate, uncertainty, and first-order horizon | geometric proof or permission to skip |
| ECZ verification | counterfactual `local_sweep(block_id)` | confirmatory policy without preregistration |
| offline screening | cost, safety, net efficiency, Pareto | test split, post-hoc thresholds |
| shadow | proposals, uncertainty, [fallback](glossary_EN.md#term-fallback) reasons | `controls_execution=true` |
| active | only after all gates | bypassing `fallback_exact` |

## Normative policy gates

The order is not changed post hoc:

1. oracle-label integrity and absence of pre-action leakage;
2. `cost_feasibility`;
3. `zero_dangerous_misses` with a preregistered upper confidence bound;
4. `net_efficiency`;
5. Pareto selection `0–3`;
6. predictor/controller preregistration;
7. shadow evidence;
8. conditional active mode.

Later benefit cannot compensate for an earlier failure. A result of `0`
admissible finalists is a valid scientific result.

## Recursive future-controller hierarchy

The future controller operates over a nested aggregate family:

```text
stop                      = empty aggregate
local_sweep(block_id)     = partial aggregate
full_exact                = maximum parent aggregate
fallback_exact            = exact uncertified parent
```

No separate `GLOBAL` policy action is introduced. Until shadow admission, the
aggregates remain proposals and counterfactual actions only;
`controls_execution=false`.

## Multiscale and PhD boundary

The [multiscale mechanism–decision architecture](glossary_EN.md#term-multiscale-mechanism-decision-architecture)
is not retrofitted into B1/B2. After the publication gate and `EX-IF0`, the
central oracle object becomes the
[minimum sufficient compute aggregate](glossary_EN.md#term-minimum-sufficient-compute-aggregate),
tested at a minimum on the layer-within-block and block-within-network scales.

[Spike-like control dynamics](glossary_EN.md#term-spike-like-control-dynamics)
is off the critical path. The work first measures chattering and tests basic
hysteresis. `QWake-SPC`, spike-native communication, and learning remain
outside the current work.

## Test split and A-Max

The test split remains closed for feature, threshold, finalist, and policy
selection. One final evaluation requires a separate freeze.

`A-Max` opens only after successful shadow evidence and end-to-end cost
benefit. If the conditions are not met, the study stops at `A-Core` without
rewriting the negative result.
