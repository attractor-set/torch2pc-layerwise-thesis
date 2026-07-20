# `PC-TREF` and `PC-CATM` theoretical foundation after `SI-MA1`

[Русская версия](pc-tref-pc-catm-theoretical-foundation.md)

## 1. Status and purpose

This document freezes the normative theoretical refinement of
[PC-TREF](glossary_EN.md#term-pc-tref) and
[PC-CATM](glossary_EN.md#term-pc-catm) required before B1/B2
preregistration. It does not modify the frozen B0, `SI-MA0`, or `SI-MA1`
protocols or results and does not mark B1/B2 as executed.

The empirical sequence at this [publication state](glossary_EN.md#term-publication-state) is:

- `SI-MA0` passed `REC-MA0`, `OBS-MA0`, `VER-MA0`, and `CMP-MA0`, but failed
  `COST-MA0`; its registered median accounting residual was approximately
  `0.1606`;
- `SI-MA1` separately calibrated [observer cost](glossary_EN.md#term-observer-cost), preserved signed values, and
  passed `CAL-COST-MA1`;
- across ten independently trained models, the median `D_seed` was
  `-0.190635073373` and the one-sided 95% bootstrap upper bound was
  `-0.188621876160` against the registered `0.01` threshold;
- `SI-MA1` did not rewrite the negative `SI-MA0` result, include future `ECZ`
  evaluator cost, or measure end-to-end B1/B2 benefit.

The measurement-readiness gate is therefore satisfied, while equivalence,
zero, regret, and cost semantics must be frozen before B1/B2 contracts exist.

## 1.1. Architectural levels

The theoretical and control contribution is separated into four levels:

1. `PC-TREF` is the framework defining
   [task-relative equivalence](glossary_EN.md#term-task-relative-equivalence),
   representation sufficiency, admissible actions, and regret bounds;
2. `PC-CATM` is the mechanism model of correction sources, transport,
   aggregation, and cancellation;
3. [QWake-PC](glossary_EN.md#term-qwake-pc) is the controller
   [architecture](glossary_EN.md#term-architecture) and policy family that
   operationalizes the framework and mechanism model;
4. `QW-PC0`, `QW-AB0`, and later versioned contracts are concrete controller
   designs.

`QWake-PC` is not part of the definition of PC-TREF or PC-CATM and does not
denote one fixed algorithm. A negative result for a concrete policy therefore
bounds that control embodiment without invalidating the theoretical framework
or supported mechanism observations.

The `QW-PC0` and `QW-AB0` identifiers are design-level labels here and do not
permit [execution](glossary_EN.md#term-execution) without separate
preregistration and an admission decision.

## 2. Spaces, representations, and registered relations

Let:

- $x\in\mathcal X$ be a `state_inference` state;
- $\phi_I:\mathcal X\to\mathcal Y_I$ be a diagnostic representation;
- $\mathcal A$ be the registered computational action set;
- $L_R(a,x)$ be the registered task-relative loss of action $a$ in state $x$;
- $V^*(x)=\inf_{a\in\mathcal A}L_R(a,x)$ be the best available loss in the
  registered action space.

Exact [diagnostic quotient](glossary_EN.md#term-diagnostic-quotient) classes are produced only by a registered class map
$q_I:\mathcal Y_I\to\mathcal Q_I$:

```math
x\sim_I^q y
\Longleftrightarrow
q_I(\phi_I(x))=q_I(\phi_I(y)).
```

This is an equivalence relation and is the only relation that directly
licenses the quotient notation $\mathcal X/{\sim_I^q}$. Write its graph as

```math
E_I^q
=
\{(x,y):q_I(\phi_I(x))=q_I(\phi_I(y))\}.
```

## 3. Operational diagnostic indistinguishability

Exact equality is generally too strict for continuous features. Define
[operational diagnostic indistinguishability](glossary_EN.md#term-operational-diagnostic-indistinguishability):

```math
x\approx_{I,\varepsilon}y
\Longleftrightarrow
d_I(\phi_I(x),\phi_I(y))\leq\varepsilon_I,
```

with the feature space, metric or pseudometric, normalization, zero-denominator
rule, tolerance, data scope, and aggregation unit frozen before analysis.

The relation $\approx_{I,\varepsilon}$ is not assumed transitive. It is an
operational proximity criterion and does not create a quotient by itself. A
quotient claim requires an explicit $q_I$, such as a decision class,
preregistered discretization, action set, or clustering rule.

## 4. Regret and required equivalence

[Decision regret](glossary_EN.md#term-decision-regret) is

```math
\operatorname{Regret}_R(a;x)=L_R(a,x)-V^*(x)\geq0.
```

For tolerance $\delta_R$, define the common-admissibility relation

```math
(x,y)\in A_R^{\delta}
\Longleftrightarrow
\exists a\in\mathcal A:
\operatorname{Regret}_R(a;x)\leq\delta_R
\land
\operatorname{Regret}_R(a;y)\leq\delta_R.
```

This is an operational safety relation and need not be transitive.
[Required equivalence](glossary_EN.md#term-required-equivalence) for quotient
claims is defined by a registered decision-class map $q_R$, such as the same
selected action or admissible action set:

```math
x\sim_R^q y
\Longleftrightarrow
q_R(x)=q_R(y),
```

with the mandatory class-level condition

```math
\forall c\in\mathcal Q_R\;\exists a_c\in\mathcal A:
\sup_{x:q_R(x)=c}
\operatorname{Regret}_R(a_c;x)
\leq\delta_R.
```

Write the induced equivalence relation as
$E_R^q=\{(x,y):q_R(x)=q_R(y)\}$.

A B1/B2 primary safety [endpoint](glossary_EN.md#term-endpoint) must use regret, dangerous misses, or an
equivalent preregistered outcome rather than equality of continuous diagnostic
features.

## 5. Task-relative equivalence defect

For partition-based diagnostic and required classes, the exact
[task-relative equivalence defect](glossary_EN.md#term-task-relative-equivalence-defect)
is

```math
\mathfrak D_{I\to R}^{q}
=
E_I^q\setminus E_R^q.
```

It contains pairs merged by a diagnostic class but assigned to different
registered required-decision classes.

Safety is assessed separately through the operational common-admissibility
defect

```math
\mathfrak D_{I\to R}^{q,\delta}
=
E_I^q\setminus A_R^{\delta}.
```

It contains diagnostic-class pairs for which no common action has regret at or
below $\delta_R$. This object is a safety-defect relation rather than a second
equivalence relation.

When only threshold proximity $\approx_{I,\varepsilon}$ is used, the resulting
object is an operational defect relation and is not interpreted as a quotient
space defect without a separate partition map.

## 6. Precision-masked zero

A [precision-masked zero](glossary_EN.md#term-precision-masked-zero) is defined
relative to a registered measurement contract $\mathcal N$:

```math
Z_{\tau}^{\mathcal N}
=
\{z:\|z\|_{\mathcal N}\leq\tau_{\mathcal N}\}.
```

The contract freezes the space and dtype, device and computational path, norm,
scale or denominator, numerical $\epsilon$, threshold, layer, step, and
aggregation rule.

The project distinguishes:

1. mathematical zero, $z=0$;
2. numerical zero, $z\in Z_{\tau}^{\mathcal N}$;
3. diagnostically indistinguishable zero;
4. decision-equivalent zero, for which zero-like action satisfies the regret
   tolerance.

Moving between these levels requires a separate registered claim.

## 7. Explicit norms in `PC-CATM`

Every `PC-CATM` norm carries a measurement contract

```math
\mathcal N=(V,\|\cdot\|,s,\epsilon,\tau,\mathcal G),
```

where $V$ is the space, $s$ is the scale, $\epsilon$ protects the denominator,
$\tau$ is the numerical threshold, and $\mathcal G$ is the aggregation rule.

For example,

```math
\|e_l^{(t)}\|_{2,\mathrm{rel}}
=
\frac{\|e_l^{(t)}\|_2}
     {\max(s_l^{(t)},\epsilon_l)}.
```

The protocol states whether $s_l^{(t)}$ is a state norm, reference norm,
frozen validation scale, or another prespecified quantity. Values from
different layers or times are not aggregated without registered normalization.

Exact `NCZ`, `ECZ`, and `TNZ` remain operator kernels. Operational zones are
precision-masked neighborhoods and always cite the applicable $\mathcal N$ and
thresholds.

## 8. Cost vector and selection rule

Action cost is a [cost vector](glossary_EN.md#term-cost-vector):

```math
\mathbf C(a;\phi)=
\bigl(
C_{\mathrm{compute}},
C_{\mathrm{latency}},
C_{\mathrm{memory}},
C_{\mathrm{diagnostic}},
C_{\mathrm{observer}},
C_{\mathrm{control}},
C_{\mathrm{fallback}}
\bigr).
```

Components are not combined implicitly. Before analysis, the protocol chooses
one of:

1. a registered scalarization with fixed units and weights;
2. [Pareto admissibility](glossary_EN.md#term-pareto-admissibility), followed by
   a separate primary rule selecting among nondominated actions.

Post-hoc weight selection is prohibited. A negative observer-calibrated
`SI-MA1` residual is not negative physical cost and is not counted as
end-to-end savings.

## 9. Three diagnostic-cost boundaries

The project distinguishes:

1. [diagnostic-mechanism cost](glossary_EN.md#term-diagnostic-mechanism-cost):
   computation required to form features in the executed path;
2. [observer cost](glossary_EN.md#term-observer-cost): instrumentation, timers,
   hooks, counters, and measurement-[evidence](glossary_EN.md#term-evidence) publication;
3. [control-plane cost](glossary_EN.md#term-control-plane-cost): additional
   feature acquisition, `ECZ` evaluation, action selection, coordination, and
   [fallback](glossary_EN.md#term-fallback) validation.

`SI-MA1` addresses the second boundary and checks that the registered positive
uncovered observer residual is not above 1% of [baseline](glossary_EN.md#term-baseline). It does not measure
the third boundary or allow over-closure to be subtracted from future
control-plane cost.

## 10. Consequences for B1/B2

After adoption of this package:

- the B1/B2 theoretical prerequisite is satisfied;
- B1/B2 preregistration is permitted;
- implementation and confirmatory [execution](glossary_EN.md#term-execution) remain prohibited until a
  [candidate](glossary_EN.md#term-candidate)-specific contract, numerical-equivalence gate, and provenance
  freeze exist;
- each B1/B2 contract must freeze $q_I$ or explicitly mark a nontransitive
  proximity relation, $q_R$, $\delta_R$, norm contracts, the cost vector, and
  the selection rule;
- `SI-MA0` and `SI-MA1` remain unchanged and are interpreted jointly: the first
  exposed an uncovered observer-sensitive residual, while the second showed
  that registered observer calibration removes a positive residual under the
  one-sided decision rule.

## 11. Claim boundaries

This package does not establish global representation minimality, transitivity
of threshold proximity, exact additive cost decomposition, B1/B2 speedup,
active `QWake-PC` safety, or transfer to other architectures, datasets, dtypes,
or devices. It freezes testable semantics required for the next
preregistrations.
