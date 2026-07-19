# `PC-TREF`: Balanced Core for adaptive predictive-coding inference

[Русская версия](pc-tref-balanced-core.md)

## 1. Status and boundary

[PC-TREF](glossary_EN.md#term-pc-tref) is the upper-level framework of the
current master's project. It specializes established equivalence, sufficiency,
and quotient-space concepts for selecting the amount of exact
[state inference](glossary_EN.md#term-state-inference) in Torch2PC.

It does not claim a universal information-zero theory, a globally minimal
representation, or transfer beyond the registered architectures, datasets,
dtypes, devices, and action space. Cross-document normative semantics are
frozen in the [theoretical foundation](pc-tref-pc-catm-theoretical-foundation_EN.md)
and [ADR-013](decisions/ADR-013-pc-tref-operational-semantics_EN.md).

## 2. Diagnostic classes and threshold proximity

Let $x\in\mathcal X$ and $\phi_I(x)\in\mathcal Y_I$. The equivalence relation
required for a [diagnostic quotient](glossary_EN.md#term-diagnostic-quotient) is
defined by a registered partition map $q_I$:

```math
x\sim_I^q y
\Longleftrightarrow
q_I(\phi_I(x))=q_I(\phi_I(y)).
```

Continuous features also use
[operational diagnostic indistinguishability](glossary_EN.md#term-operational-diagnostic-indistinguishability):

```math
x\approx_{I,\varepsilon}y
\Longleftrightarrow
d_I(\phi_I(x),\phi_I(y))\leq\varepsilon_I.
```

Metric, normalization, tolerance, and aggregation unit are frozen before
analysis. Threshold proximity is not assumed transitive and does not create a
quotient by itself.

## 3. Required equivalence and regret

Let $\mathcal A$ be the registered action space and $L_R(a,x)$ the task-relative
loss. [Decision regret](glossary_EN.md#term-decision-regret) is

```math
\operatorname{Regret}_R(a;x)
=
L_R(a,x)-\inf_{b\in\mathcal A}L_R(b,x).
```

Two states are commonly admissible at tolerance $\delta_R$ when one action has
regret at or below $\delta_R$ for both. Literal
[required equivalence](glossary_EN.md#term-required-equivalence) uses a
registered decision-class map $q_R$ whose classes separately pass the regret
criterion.

The Scenario A action set is preregistered, for example:

```text
continue_exact
local_sweep_candidate
composite_sweep_candidate
stop_candidate
fallback_exact
```

[Candidate](glossary_EN.md#term-candidate)-specific B1/B2 contracts freeze the final list and semantics.

## 4. Task-relative equivalence defect

For partition-based diagnostic and required classes, the
[task-relative equivalence defect](glossary_EN.md#term-task-relative-equivalence-defect)
is

```math
\mathfrak D_{I\to R}^{q}
=
E_I^q\setminus E_R^q.
```

It contains pairs merged by a diagnostic class but assigned to different
required-decision classes. The separate operational safety defect
$\mathfrak D_{I\to R}^{q,\delta}=E_I^q\setminus A_R^{\delta}$ contains pairs
for which no common action has admissible regret. Registered operational
manifestations include dangerous misses,
[endpoint](glossary_EN.md#term-endpoint)-utility regret, unnecessary exact
sweeps, [fallback](glossary_EN.md#term-fallback) rate, and numerical-equivalence
or safety-gate violations.

When only $\approx_{I,\varepsilon}$ is used, the result is an operational defect
relation rather than a quotient defect.

## 5. Nested representation family

The preregistered family contains:

- $\phi_0$: layer, sweep index, and registered residual norm;
- $\phi_1$: $\phi_0$ plus activity and resultant correction;
- $\phi_2$: $\phi_1$ plus canonical-channel geometry;
- $\phi_3$: $\phi_2$ plus [state-error transport](glossary_EN.md#term-state-transport);
- $\phi_4$: $\phi_3$ plus temporal persistence;
- $\phi_5$: $\phi_4$ plus predicted utility and uncertainty.

Protocols define the exact features, norms, and thresholds. A level is retained
only when it yields a registered reduction in regret or safety errors relative
to its cost.

## 6. `PC-CATM` as the mechanism layer

[PC-CATM](glossary_EN.md#term-pc-catm) distinguishes:

- $\ker S_l$: exact `NCZ` and `ECZ` in canonical-channel aggregation;
- $\ker \widetilde J_{h,l+1}^{*}$: `TNZ` in state-error transport;
- $\ker \widetilde J_{\theta,l}^{*}$: limited `PNZ` extension.

Exact kernels are separated from
[precision-masked zero](glossary_EN.md#term-precision-masked-zero), diagnostic
indistinguishability, and decision-equivalent zero. A diagnostic regime does
not authorize a computational-path change.

## 7. Sufficiency and cost vector

Global minimality is not claimed. The admissible statement is:

> within the preregistered family, identify the least costly representation
> that passes the specified regret, safety, and equivalence gates.

Each $\phi_k$ is evaluated with a [cost vector](glossary_EN.md#term-cost-vector):

```math
\mathbf C=
(C_{\mathrm{compute}},C_{\mathrm{latency}},C_{\mathrm{memory}},
C_{\mathrm{diagnostic}},C_{\mathrm{observer}},C_{\mathrm{control}},
C_{\mathrm{fallback}}).
```

Selection uses preregistered scalarization or
[Pareto admissibility](glossary_EN.md#term-pareto-admissibility) followed by a
separate primary rule. Costs are not combined implicitly.

## 8. Cost boundaries after `SI-MA1`

The project separates [diagnostic-mechanism cost](glossary_EN.md#term-diagnostic-mechanism-cost), [observer cost](glossary_EN.md#term-observer-cost), and
[control-plane cost](glossary_EN.md#term-control-plane-cost). `SI-MA1` passed the one-sided observer-calibrated gate but
did not measure `ECZ` evaluation, action selection, fallback validation, or
end-to-end B1/B2 benefit. Negative `D_seed` values indicate calibration
over-closure, not negative physical cost.

## 9. Counterfactual exact verification

[Counterfactual exact verification](glossary_EN.md#term-exact-verification) from
identical state is the empirical arbiter of required equivalence. Primary
utility, regret margin, and the dangerous-miss rule are frozen before analysis.
Active control is blocked by a safety-gate failure.

## 10. Consequences for B1/B2

After theoretical-package publication:

- B1/B2 preregistration is permitted;
- implementation and confirmatory [execution](glossary_EN.md#term-execution) remain closed until separate
  candidate-specific contracts exist;
- each contract freezes $q_I$ or explicitly marks a proximity relation, $q_R$,
  $\delta_R$, norm contracts, the cost vector, and decision rule;
- `SI-MA0` and `SI-MA1` remain unchanged;
- the test split remains closed.

## 11. Operational sufficiency boundary after `EX-IF0`

A separate design-only extension,
[`PC-TREF-SB`](pc-tref-sufficiency-boundary_EN.md), defines one-step oracle skip
regret, oracle margin $M^*$, its pre-action estimate $\widehat M_b$, and a
first-order predicted horizon. The oracle label and diagnostic estimate are
distinct objects; the new theory neither modifies B1/B2 nor authorizes control
of execution.

Geometric notions of normal, angle, and tangential component are permitted only
for a registered differentiable surrogate and explicit metric. The primary
master's claim remains operational and assumes no smooth boundary.

## 12. Hypotheses and claim boundaries

`H-TREF1` expects [correction geometry](glossary_EN.md#term-correction-geometry) and transport to reduce operational
manifestations of $\mathfrak D_{I\to R}^{q}$ and its safety version
$\mathfrak D_{I\to R}^{q,\delta}$ relative to residual-only
representations. `H-TREF2` expects a representation level after which added
features do not materially reduce regret relative to cost. `H-R1` expects safe
exact-sweep reduction to lower end-to-end [runtime](glossary_EN.md#term-runtime) after all costs are included.

PC-TREF does not establish these hypotheses, transitivity of threshold
proximity, representation minimality, or active-control safety. Negative and
mixed results remain valid.
