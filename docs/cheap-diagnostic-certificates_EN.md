# Cheap ECZ/NCZ diagnostic certificates

[Русская версия](cheap-diagnostic-certificates.md)

Normative terms: [execution](glossary_EN.md#term-execution),
[evidence](glossary_EN.md#term-evidence),
[candidate](glossary_EN.md#term-candidate),
[passive diagnostics](glossary_EN.md#term-passive-diagnostics),
[canonical correction channel](glossary_EN.md#term-canonical-correction-channel),
[correction geometry](glossary_EN.md#term-correction-geometry),
[matched profiling](glossary_EN.md#term-matched-profiling),
[device time](glossary_EN.md#term-device-time),
[saved tensors](glossary_EN.md#term-saved-tensors),
[observer cost](glossary_EN.md#term-observer-cost),
[cost vector](glossary_EN.md#term-cost-vector),
[decision regret](glossary_EN.md#term-decision-regret),
[exact-implementation freeze](glossary_EN.md#term-exact-implementation-freeze),
[local predictor](glossary_EN.md#term-local-predictor), and
[shadow mode](glossary_EN.md#term-shadow-mode).

## 1. Status and purpose

Status: **design-only; implementation and data collection are closed**.

This document freezes the type of cheap estimate for future passive `PC-CATM`
diagnostics. It adds no topological hypothesis, changes no sealed B0/B1/B2
evidence, does not open matched-profiling execution, and is not a
preregistration of thresholds or policy.

Research question:

> Can a subset of ECZ and NCZ states be distinguished reliably at lower cost
> than the full canonical diagnostic calculation by using one-sided
> certificates and abstaining on ambiguous cases?

## 2. Exact reference observer

For the canonical correction channels of layer $l$:

$$
A_l=\sum_a \lVert c_l^{(a)}\rVert,
\qquad
R_l=\left\lVert\sum_a c_l^{(a)}\right\rVert.
$$

Within the registered norm contract:

- `NCZ`: $A_l$ is in the quiet/zero neighbourhood and $R_l$ is small;
- `ECZ`: $A_l$ is in the active region and $R_l$ is small while the registered
  geometry guards pass;
- `active_non_ecz`: activity/resultant do not satisfy the ECZ conditions;
- `activity_guard`: the activity margin is insufficient;
- `invalid`: snapshot/provenance/numerical checks fail.

Reference labels are created only by the exact observer from one compatible
snapshot. The cheap observer does not redefine those labels.

## 3. Certificate and mechanism label are separate axes

A future observer result stores at least:

```json
{
  "mechanism_label": "ECZ",
  "certificate_status": "certified",
  "certificate_type": "positive_channel_witness",
  "margin": 0.0,
  "action_permission": "none"
}
```

Permitted `certificate_status` values:

- `exact` — the full reference observer was computed;
- `certified` — a registered sufficient condition passed;
- `abstained` — the available information is insufficient;
- `invalid` — the snapshot, provenance, or numerical contract failed.

Certification does not create new mechanism classes `certified_ncz` or
`certified_ecz`: `NCZ`, `ECZ`, `active_non_ecz`, `activity_guard`, and
`invalid` remain a separate axis.

## 4. One-sided ECZ certificate

Suppose the cheap observer has a lower bound for one channel's activity:

$$
L_{l,j}\le \lVert c_l^{(j)}\rVert.
$$

For a compatible snapshot, the condition

$$
R_l\le\tau_R,
\qquad
L_{l,j}>\tau_{\mathrm{active}}
$$

excludes `NCZ`. If the preregistered ECZ geometry guards also pass, the
observation receives `mechanism_label=ECZ` and
`certificate_status=certified`.

Diagnostics may terminate after the first reliable activity witness. This is
a potential saving relative to computing the full $A_l$.

## 5. One-sided NCZ certificate

`NCZ` requires an upper bound for every relevant channel:

$$
\lVert c_l^{(a)}\rVert\le U_{l,a}
\quad\text{for every }a,
$$

and the registered condition

$$
R_l\le\tau_R,
\qquad
\sum_a U_{l,a}<\tau_{\mathrm{quiet}}.
$$

Upper bounds are cheap only when they follow from already available
intermediates, structural masks, channel-path provenance, or analytical
bounds. Failure to find an active channel is not an `NCZ` certificate.

## 6. Mandatory abstention

If neither the ECZ witness nor the all-channel NCZ upper bound passes, the
observer must return `certificate_status=abstained`. Forced binary `ECZ/NCZ`
classification is prohibited.

`abstained` routes the observation to the exact observer or a registered
[fallback](glossary_EN.md#term-fallback) and is not itself a mechanism error.

## 7. Control boundary

No certificate grants action permission:

- `NCZ` does not mean `stop`;
- `ECZ` does not mean `continue` or local sweep;
- zero correction in one layer does not permit skipping that layer;
- an action requires separate `EX-IF0`, expected utility, exact verification,
  and bounded decision regret.

Until separate predictor/controller preregistration,
`action_permission=none` and `controls_execution=false` always hold.

## 8. Future validation metrics

A future preregistration must freeze:

- coverage: the fraction of observations without `abstained`;
- selective error among issued certificates;
- separate false-NCZ and false-ECZ rates;
- observer device time, memory, saved tensors, and graph lifetime;
- the fraction of exact diagnostics avoided;
- observer non-interference;
- stability across `model_seed`, layers, and time;
- downstream decision regret only after `EX-IF0`.

False `NCZ` requires the stricter safety gate if it is later used in a
stop/sleep candidate policy.

## 9. Admission order

1. complete and seal clean B0/B1/B2 matched profiling;
2. select an admissible exact substrate;
3. freeze `EX-IF0` and policy-neutral labels;
4. separately preregister the exact reference observer and cheap certificates;
5. run passive collection without controlling execution;
6. only then evaluate a predictor, shadow policy, and possible active actions.

Topological claims are outside this route: the original analogy only
illustrated the type of cheap sufficient test.
