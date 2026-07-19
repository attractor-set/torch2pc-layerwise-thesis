# `PC-TREF-SB`: operational sufficiency boundary for `state_inference`

[Русская версия](pc-tref-sufficiency-boundary.md)

## 1. Status and claim boundary

This document formalizes a design-only extension of
[PC-TREF](glossary_EN.md#term-pc-tref) after `EX-IF0`. It concerns selection of
the next computational action during `state_inference` and does not modify B1,
B2, their preregistration, exact contracts, results, or
[evidence](glossary_EN.md#term-evidence).

The mandatory master's object is the
[operational sufficiency boundary](glossary_EN.md#term-operational-sufficiency-boundary)
for one next action. The document does not claim:

- a universal neural-network learning boundary;
- equivalence between the inference boundary and parameter-update boundary;
- smoothness, connectedness, or a unique boundary normal;
- safety of a sequence of active skips;
- permission to control [execution](glossary_EN.md#term-execution) before separate gates.

## 2. Registered decision context

The registered context is the tuple

```math
\Gamma=
(\mathcal X,\mathcal A,a_E,\ell_R,\varepsilon_R,
\delta_{\mathrm{miss}},\mathbf C,\preceq_C,\mathbb P_\Gamma),
```

where:

- $\mathcal X$ is the complete experimental state space;
- $\mathcal A$ is the fixed computational action space;
- $a_E\in\mathcal A$ is the registered exact reference action;
- $\ell_R(x,a)$ is the task-relative action loss;
- $\varepsilon_R\geq0$ is the allowed one-step regret;
- $\delta_{\mathrm{miss}}\in[0,1]$ is the allowed dangerous-policy-decision probability;
- $\mathbf C(x,a)$ is the complete [cost vector](glossary_EN.md#term-cost-vector);
- $\preceq_C$ is the preregistered cost-dominance relation;
- $\mathbb P_\Gamma$ is the state distribution inside the registered scope.

State $x$ includes at least [dataset](glossary_EN.md#term-dataset), sample, `model_seed`, parameters, latent
state, sweep index, method, and cost context. Parameters remain fixed within one
counterfactual comparison.

## 3. Actions and one-step regret

For the primary line:

```math
\mathcal A=
\{a_{\mathrm{stop}},a_{\mathrm{local}},
a_{\mathrm{exact}},a_{\mathrm{fallback}}\}.
```

Operational regret relative to the exact reference is

```math
r_\Gamma(x,a)
=
[\ell_R(x,a)-\ell_R(x,a_E)]_+,
\qquad [z]_+=\max(0,z).
```

If the required response is a structured object, a preregistered nonnegative
defect may be used:

```math
r_\Gamma(x,a)=D_R(Y(x,a),Y(x,a_E)),
\qquad D_R(y,y)=0.
```

The condition $D_R(y,y)=0$, together with the first semantic, ensures
$a_E\in\mathcal A_\varepsilon(x)$ and a nonempty admissible set. In either case, $r_\Gamma$ is a registered exact-reference quantity. It equals
classical [decision regret](glossary_EN.md#term-decision-regret) only when $a_E$ realizes the registered $V^*(x)$ in
the evaluated action space. Otherwise, claims must say exact-reference regret
or exact-reference defect rather than global optimality.

One semantics is selected for [confirmatory analysis](glossary_EN.md#term-confirmatory-analysis). An action is admissible if

```math
r_\Gamma(x,a)\leq\varepsilon_R.
```

The admissible action set is

```math
\mathcal A_\varepsilon(x)
=
\{a\in\mathcal A:r_\Gamma(x,a)\leq\varepsilon_R\}.
```

## 4. Required equivalence

The binary stop-admissibility class is

```math
q_{\mathrm{stop}}(x)
=
\mathbf 1\{a_{\mathrm{stop}}\in\mathcal A_\varepsilon(x)\}.
```

It is the minimal required response for the primary boundary in this document.
For a stronger safety claim, define equality of the full admissible action sets:

```math
x\equiv_S y
\Longleftrightarrow
\mathcal A_\varepsilon(x)=\mathcal A_\varepsilon(y).
```

Set equality is reflexive, symmetric, and transitive, so $\equiv_S$ is an
equivalence relation. It permits ties and several safe actions. Nonempty
intersection of admissible sets alone is not called equivalence.

Full [required equivalence](glossary_EN.md#term-required-equivalence) is defined
by a separately registered decision-class map $q_R$. For a Pareto claim,
the strict cost relation is

```math
c'\prec_C c
\Longleftrightarrow
c'\preceq_C c\land\neg(c\preceq_C c'),
```

and the nondominated safe actions are

```math
\mathcal P_C(x)
=
\left\{
a\in\mathcal A_\varepsilon(x):
\nexists a'\in\mathcal A_\varepsilon(x),
\mathbf C(x,a')\prec_C\mathbf C(x,a)
\right\}.
```

Admissible specializations of $q_R$ depend on the claim:

- for a binary stop-safety claim: $q_R(x)=q_{\mathrm{stop}}(x)$;
- for a full safety claim: $q_R(x)=\mathcal A_\varepsilon(x)$;
- for a Pareto-set claim:
  $q_R(x)=(\mathcal A_\varepsilon(x),\mathcal P_C(x))$;
- for an executed-action claim: $q_R(x)$ includes the result of the
  preregistered tie-break.

In every case,

```math
x\equiv_R y
\Longleftrightarrow
q_R(x)=q_R(y).
```

Predicting the sign of the primary boundary establishes information only about
$q_{\mathrm{stop}}$. By itself, it does not establish representation
sufficiency for recovering the complete admissible set or selecting among
`local`, `exact`, and `fallback` under cost.

## 5. Diagnostic representation

For diagnostic budget $b$, define

```math
\phi_b:\mathcal X\rightarrow\mathcal Z_b,
```

containing only information available before the exact action. A literal
quotient uses a registered partition map

```math
q_b:\mathcal Z_b\rightarrow\mathcal K_b,
```

and the relation

```math
x\equiv_b y
\Longleftrightarrow
q_b(\phi_b(x))=q_b(\phi_b(y)).
```

Threshold proximity

```math
d_b(\phi_b(x),\phi_b(y))\leq\tau_b
```

remains a proximity relation and does not create a quotient without a separate
partition map or proof of transitivity.

## 6. Sufficiency and two distinct defects

A representation is sufficient for the registered
[task-relative equivalence](glossary_EN.md#term-task-relative-equivalence) decision when

```math
x\equiv_b y\Longrightarrow x\equiv_R y.
```

The exact [task-relative equivalence defect](glossary_EN.md#term-task-relative-equivalence-defect) is

```math
\mathfrak D_{b\rightarrow R}=E_b\setminus E_R.
```

It contains state pairs merged by a diagnostic class but requiring different
admissible action sets.

For a concrete policy $\pi_b$, define a separate safety defect:

```math
\mathfrak D_{\mathrm{safe}}(\pi_b)
=
\{x:r_\Gamma(x,\pi_b(\phi_b(x)))>\varepsilon_R\}.
```

The first object is a set of state pairs. The second is a set of dangerous
policy decisions. They are not interchangeable.

## 7. Aggregate `NCZ`/`ECZ` regimes and separate `TNZ`

Let the full observer provide frozen canonical channels

```math
C(x)=(C_1(x),\ldots,C_m(x)),
```

and let the registered aggregation operator define $u(x)=A(C(x))$ with
$A(0)=0$. Exact aggregation regimes are

```math
\mathrm{NCZ}^0=\{x:C_i(x)=0\ \forall i\},
```

```math
\mathrm{ECZ}^0=
\{x:u(x)=0\land\exists i:C_i(x)\neq0\},
```

```math
\mathrm{active\_non\_ecz}^0=\{x:u(x)\neq0\}.
```

These three regimes form a pairwise-disjoint partition of the registered
aggregation scope. A small or zero resultant does not distinguish `NCZ` from
`ECZ`.

`TNZ` is not the third aggregation complement. It is defined separately for the
transport operator as a nonzero error source in the kernel of the adjoint
Jacobian:

```math
\mathrm{TNZ}^0
=
\{x:e_{l+1}(x)\neq0\land
\widetilde J_{h,l+1}^{*}e_{l+1}(x)=0\}.
```

A state may therefore have one aggregation regime and a separate transport
status. Numerical neighborhoods use a
[precision-masked zero](glossary_EN.md#term-precision-masked-zero) contract and
do not authorize an action.

## 8. One-sided certificates and abstention

A cheap `NCZ` certificate requires upper bounds $U_i(x)$:

```math
\|C_i(x)\|\leq U_i(x),
\qquad U_i(x)\leq\tau_i\ \forall i.
```

Absence of a detected activity witness is insufficient.

A cheap `ECZ` certificate simultaneously requires

```math
U_u(x)\leq\tau_u,
\qquad L_{\mathrm{act}}(x)>\tau_{\mathrm{act}},
```

and registered geometry guards. If the bounds do not give a one-sided decision,
the result is `abstained`. The certifier also abstains when confidence bounds
overlap.

Every certificate retains `action_permission=none` until a separately
preregistered predictor, exact verification, regret gate, and [shadow mode](glossary_EN.md#term-shadow-mode).

## 9. Accumulated diagnostic demand

For layer $l$, introduce a canonical pre-action signal

```math
c_l(t)\in\mathbb R^{d_l}.
```

It is called a diagnostic-demand vector for additional inference rather than a
parameter-learning-need vector.

The signed accumulator is

```math
p_l(t+1)=\Lambda_l^p p_l(t)+c_l(t).
```

The non-cancelling activity accumulator is

```math
e_l(t+1)=\Lambda_l^e e_l(t)+|c_l(t)|.
```

The memory operators $\Lambda_l^p$ and $\Lambda_l^e$, their spectral radii,
step units, norms, and reset rules are frozen before analysis. Large $e_l$ with
small $p_l$ is interpreted only under registered norms, scales, and thresholds.
It indicates cancellation or oscillation, but is not an independent `ECZ` label
and does not authorize a local action.

## 10. Oracle one-step boundary

For `stop`, define the online-inaccessible oracle regret

```math
r_{\mathrm{skip}}^*(x)=r_\Gamma(x,a_{\mathrm{stop}}).
```

The [oracle sufficiency margin](glossary_EN.md#term-oracle-sufficiency-margin) is

```math
M^*(x)=\varepsilon_R-r_{\mathrm{skip}}^*(x).
```

Then

```math
\mathcal S^*=\{x:M^*(x)\geq0\},
```

```math
\mathcal U^*=\{x:M^*(x)<0\},
```

```math
\mathcal B^*=\{x:M^*(x)=0\}.
```

The binary oracle label for the primary task is

```math
y_{\mathrm{stop}}^*(x)
=
\mathbf 1\{M^*(x)\geq0\}
=
q_{\mathrm{stop}}(x).
```

$\mathcal B^*$ is called the one-step operational boundary by convention, but
formally it is a threshold level set. It need not equal the topological boundary
$\partial\mathcal S^*$. Such equality requires at least a registered topology,
sufficient regularity of $M^*$, and local sign change. Its definition also
implies no smoothness, connectedness, unique normal, or transfer beyond
$\Gamma$.

## 11. Pre-action boundary estimate

The [sufficiency-boundary estimator](glossary_EN.md#term-sufficiency-boundary-estimator)
uses only pre-action information:

```math
\widehat M_b(x)=g_b(\phi_b(x)).
```

$M^*$ is a post-action oracle label, while $\widehat M_b$ is its diagnostic
estimate. Their separation prevents a circular definition.

The predictor returns an interval

```math
I_b(x)=[L_b(x),U_b(x)].
```

Interpretation under the registered interval-construction procedure:

- $L_b(x)\geq0$: the [candidate](glossary_EN.md#term-candidate) is classified as safe;
- $U_b(x)<0$: the candidate is classified as unsafe;
- $L_b(x)<0\leq U_b(x)$: `abstained` or `fallback_exact`.

These classifications support a safety claim only after separate interval-coverage
validation on data not used to construct the interval. A point estimate
$\widehat M_b>0$ is not by itself a safety certificate.

## 12. First-order horizon

For a fixed diagnostic budget $b$, the estimated-margin change is

```math
\Delta\widehat M_b(t)
=
\widehat M_b(t)-\widehat M_b(t-1).
```

The margin-consumption speed is

```math
V_b^M(t)=\max(0,-\Delta\widehat M_b(t)).
```

The [predicted sufficiency horizon](glossary_EN.md#term-predicted-sufficiency-horizon)
is

```math
\widehat H_b^{(1)}(t)
=
\frac{\max(0,\widehat M_b(t))}
{V_b^M(t)+\epsilon_H},
\qquad \epsilon_H>0.
```

The numerical constant $\epsilon_H$, step unit, and maximum horizon are frozen
before analysis. A conservative version uses lower bound $L_b$. This is a local
first-order estimate under persistence of the current rate and does not
constitute a certified count of safe skips.

A layer index $l$ may replace $b$ only when a layer-specific action and oracle
label $M_l^*$ are separately defined. Using layer features to estimate global
$M^*$ does not by itself create a layer boundary.

## 13. Conditional geometric extension

A geometric interpretation is permitted only under additional conditions:

- a locally differentiable surrogate $h_l(z)$ exists;
- its target is registered as either global $M^*$ or a separately defined $M_l^*$;
- $h_l(z)=0$ defines only the corresponding surrogate boundary;
- $\nabla h_l(z)\neq0$ at the evaluated point;
- a positive-definite metric $G_l$ is registered.

The metric gradient is

```math
\operatorname{grad}_{G_l}h_l=G_l^{-1}\nabla h_l.
```

The normalized direction is

```math
n_l^G
=
\frac{\operatorname{grad}_{G_l}h_l}
{\|\operatorname{grad}_{G_l}h_l\|_{G_l}}.
```

The normal speed is

```math
q_l=\langle n_l^G,\dot z_l\rangle_{G_l}.
```

Tangency to a surrogate level set means only low local first-order sensitivity
of the selected surrogate. It does not prove preservation of a
required-equivalence class. A nonsmooth case requires a normal cone,
subgradient, or directional derivative and is outside the mandatory claim.

## 14. ECZ-protected normal activity

With a preregistered decomposition

```math
\dot z_l=\sum_i\dot z_{l,i},
```

compare

```math
q_l^{\mathrm{net}}
=
\left\langle n_l^G,\sum_i\dot z_{l,i}\right\rangle_{G_l},
```

```math
q_l^{\mathrm{abs}}
=
\sum_i
\left|\langle n_l^G,\dot z_{l,i}\rangle_{G_l}\right|.
```

Small $q_l^{\mathrm{net}}$ with large $q_l^{\mathrm{abs}}$ indicates possible
normal cancellation. $q_l^{\mathrm{abs}}$ depends on the canonical
decomposition and is not invariant under an arbitrary basis change.

## 15. Safety-first selection and cost-sufficiency frontier

First construct the actions passing the upper regret bound:

```math
\widehat{\mathcal A}_{\mathrm{safe}}(x)
=
\{a:\widehat r^{\,\mathrm{upper}}(x,a)\leq\varepsilon_R\}.
```

Only then apply [Pareto admissibility](glossary_EN.md#term-pareto-admissibility)
under the full cost vector. Cost cannot make an unsafe action admissible. In the
primary stop-boundary branch, such an upper regret bound is constructed only for
$a_{\mathrm{stop}}$; `local` enters the safe set only after separate
action-specific exact verification or estimation.

Budget $b$ is admissible when

```math
\Pr_{\mathbb P_\Gamma}
[r_\Gamma(x,\pi_b(\phi_b(x)))>\varepsilon_R]
\leq\delta_{\mathrm{miss}}.
```

The resulting object is the set of Pareto-minimal diagnostic representations
among those passing the safety constraint. A unique globally minimal
representation is not claimed.

## 16. Empirical hypotheses and gates

A future separate protocol tests:

- whether $\widehat M_b$ improves the safety-cost trade-off over simple norms;
- whether $\widehat H^{(1)}$ adds out-of-sample information;
- whether ECZ protection reduces the false-safe rate;
- whether spatial feature structure predicts local-action admissibility;
- whether diagnostics remain cheaper than an avoided exact sweep;
- whether results reproduce at the independent `model_seed` level.

An observed zero `dangerous_miss` count must be accompanied by a preregistered
upper confidence bound for the miss probability. It is not evidence of universal
safety.

The mandatory sequence is

```text
EX-IF0
→ policy-neutral oracle labels
→ passive boundary features
→ offline validation
→ predictor preregistration
→ shadow mode
→ conditional active mode
```

`B1`/`B2`, `EX-IF0`, the exact implementation, `model_seed` as the independent
unit, the closed test dataset, and `controls_execution=false` remain unchanged.
A one-step result is not presented as trajectory-level safety.
