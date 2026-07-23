# FixedPred prefix sufficiency and `DONE / UNKNOWN / SWEEP`

[Русская версия](fixedpred-sufficiency-dus-design.md)

**Status:** design freeze; [execution](glossary_EN.md#term-execution), oracle-label generation, feature collection, and control remain closed.

## 1. Consolidated idea

The mandatory scoped continuation fixes FixedPred dynamics and the
`stage2_baseline` exact implementation:

$F=F_{\mathrm{FixedPred}}, \qquad G=G_{\mathrm{stage2\_baseline}}, \qquad S_0,S_1,\ldots,S_{K_{\mathrm{ref}}}.$

The central object is the [minimum stably sufficient FixedPred
prefix](glossary_EN.md#term-minimum-stably-sufficient-fixedpred-prefix):

$t^*= \min\left\{ t: \forall j\in[t,K_{\mathrm{ref}}], M^*(j)\geq0 \right\}.$

The study asks whether a low-cost pre-action representation can safely
recognize \(t\geq t^*\) without access to the full suffix.

## 2. Separate levels

The study separates method dynamics \(F_m\), executed autograd graph \(G\),
nominal [configuration](glossary_EN.md#term-configuration) \(K\), realized [cost vector](glossary_EN.md#term-cost-vector)
\(\mathbf C\), and task-relative [endpoint](glossary_EN.md#term-endpoint) \(Y_t=\Gamma(S_t)\).

$K_1=K_2\not\Rightarrow\mathbf C_1=\mathbf C_2,$

$Y_1\simeq_RY_2\not\Rightarrow G_1=G_2.$

Mathematical preservation is stated separately within FixedPred and within
Strict.

## 3. Completed-stage roles

### Stage 2

Stage 2 is an implementation-preserving study that provides the optimized
verified [baseline](glossary_EN.md#term-baseline). It does not study adaptive
termination or analytic acquisition.

### Joint-VJP

Joint-VJP is an exact reverse-computation organization. It shows that one
endpoint can be realized by another VJP organization.

Joint-VJP is not a shortcut, the Rosenbaum special case, `DONE`, a controller
action, or a replacement for `stage2_baseline`. Historical identifiers
containing `shortcut` remain provenance-only names.

### B0

B0 measures the context-dependent cost surface of `stage2_baseline`. It does
not vary the sweep count of one snapshot and does not measure acquired-analytic
utility.

### B1/B2

B1/B2 compare exact graph organizations under matched nominal configuration
and requested sweep count. Equality of realized cost vectors is not assumed.

### EX-IF0

EX-IF0 retains `stage2_baseline` as canonical exact reference and fail-closed
[fallback](glossary_EN.md#term-fallback) and freezes the decision epoch, endpoint, tolerances, and full-suffix
rule. This package does not alter that contract.

## 4. Rosenbaum special case

The [Rosenbaum wavefront
control](glossary_EN.md#term-rosenbaum-wavefront-control) is an analytic
positive control for the \(\eta=1\) FixedPred special case.

It tests the analytically known completion order of layerwise components but
does not become a new oracle, graph, action, or permission for global `DONE`.

$\text{component completion} \neq \text{global endpoint completion} \neq \text{task-relative sufficiency}.$

Equations and indexing must be checked against the 2022 article and its 2025
correction.

## 5. Oracle and shadow decision

The post-action oracle has two states:

```text
sufficient
insufficient
```

`UNKNOWN` is not an oracle class.

The [D/U/S decision
semantics](glossary_EN.md#term-dus-decision-semantics) uses:

- `DONE`: the available representation passed positive sufficiency admission;
- `UNKNOWN`: [evidence](glossary_EN.md#term-evidence) is insufficient but another analytic is feasible;
- `SWEEP`: execute exactly one next canonical FixedPred sweep.

Unresolved uncertainty fails closed:

$\texttt{UNKNOWN}(0)\rightarrow\texttt{SWEEP}.$

Cost, NCZ, ECZ, inactivity, or a small residual cannot independently authorize
`DONE`.

## 6. Two budgets

Compute budget and diagnostic budget are registered separately. Diagnostic
budget limits evidence acquisition but cannot replace positive sufficiency
admission.

## 7. Mandatory scope

The mandatory core is temporal prefixes on one `stage2_baseline`, the EX-IF0
oracle, Rosenbaum positive controls, passive representations, D/U/S metrics,
deterministic shadow replay, and separate diagnostic and sweep costs.

Spatial recursive aggregates, a learned predictor, hysteresis, and active
control remain conditional extensions.

## 8. Claim boundary

Before separate execution, the project does not claim active acceleration,
universal early stopping, global greedy optimality, automatic NCZ/ECZ
sufficiency, or certificate transfer across graphs.

Valid negative outcomes include no early sufficient prefix, no cheap
observability, cost-infeasible diagnostics, no state dependence, no
incremental PC-CATM value, and no greedy-routing advantage.

## 9. Frontier-action clarification

[ADR-040](decisions/ADR-040-stage3b-integrated-frontier-model_EN.md) does not
change ADR-039. It maps DONE to an ACCEPT_FRONTIER `candidate`, keeps UNKNOWN as
an epistemic state, maps one next SWEEP to ADVANCE_FRONTIER(compute), and adds a
separate fail-closed COMPLETE_SUFFIX. A0 / A1 / A2 are the cumulative pre-action
observation axis; O remains post-action oracle only.
