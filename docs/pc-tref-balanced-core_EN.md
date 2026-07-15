# PC-TREF Balanced Core for adaptive predictive-coding inference

[Русская версия](pc-tref-balanced-core.md)

## 1. Status and boundary

[PC-TREF](glossary_EN.md#term-pc-tref) is the upper-level framework of the
current master's thesis. It specializes established equivalence, sufficiency,
and quotient-space concepts to the decision problem of allocating exact
predictive-coding inference.

The framework does not claim a universal theory of information zero, a proof
of a globally minimal quotient, or validity beyond the registered Torch2PC
implementation. The contribution is the PC specialization, the PC-CATM
mechanism model, and empirical evaluation of diagnostic sufficiency.

## 2. Induced and required equivalence

Let $x\in\mathcal X$ be an inference state and $\phi_I(x)$ a diagnostic
representation. It induces

$x\sim_I y \Longleftrightarrow \phi_I(x)=\phi_I(y).$

[Task-relative equivalence](glossary_EN.md#term-task-relative-equivalence) is
specified by the required response or action:

$x\sim_R y \Longleftrightarrow \mathcal A^*(x)=\mathcal A^*(y),$

where $\mathcal A^*$ is the set of admissible decisions under the registered
regret bound. Scenario A restricts actions to full sweeps:

```text
continue_exact
sleep_candidate
wake_candidate
stop_candidate
fallback_exact
```

## 3. Equivalence defect

Let $E_I$ and $E_R$ be the diagnostic and required equivalence pair sets. The
[task-relative equivalence defect](glossary_EN.md#term-task-relative-equivalence-defect)
is

$\mathfrak D_{I\to R}=E_I\setminus E_R.$

It contains state pairs merged by the diagnostic representation even though
they require different computational actions. The experiment uses registered
operational proxies rather than exhaustive pair enumeration:

- dangerous-miss rate;
- [endpoint](glossary_EN.md#term-endpoint)-gradient regret;
- unnecessary wake-ups;
- exact-[fallback](glossary_EN.md#term-fallback) rate;
- preservation of equivalence bounds.

## 4. Diagnostic quotient

The [diagnostic quotient](glossary_EN.md#term-diagnostic-quotient) is the space
of equivalence classes induced by $\phi_I$. The study compares a preregistered
nested family:

$\phi_0=$ layer, sweep index, and residual norm;

$\phi_1=\phi_0+\{A_l,R_l\}$;

$\phi_2=\phi_1+\{\chi_l,Z_l,D_l,P_l,N_l\}$;

$\phi_3=\phi_2+\{\gamma_{h,l},\Gamma_{h,l},\text{transport status}\}$;

$\phi_4=\phi_3+\{\text{persistence},\text{transition history}\}$;

$\phi_5=\phi_4+\{\text{predicted utility},\text{uncertainty}\}$.

Each representation refines the previous one. A refinement is retained only
when regret reduction justifies its computational cost.

## 5. PC-CATM as the mechanism refinement

[PC-CATM](glossary_EN.md#term-pc-catm) distinguishes three operator mechanisms:

- $\ker S_l$: `NCZ` and `ECZ` in canonical-channel aggregation;
- $\ker \widetilde J_{h,l+1}^{*}$: `TNZ` in [state-error transport](glossary_EN.md#term-state-transport);
- $\ker \widetilde J_{\theta,l}^{*}$: the limited `PNZ` extension for
  parameter accessibility.

Aggregation and state transport are mandatory in Scenario A. `PNZ` remains a
theoretical extension, deterministic control, and optional small passive audit.

## 6. Empirical sufficiency and cost

Global minimality is not claimed. The admissible main claim is:

> among the registered family $\phi_0,\ldots,\phi_5$, the study identifies the
> least costly representation that passes the preregistered safety gate.

For each $\phi_k$, the study measures dangerous misses, endpoint-gradient
regret, sweep and VJP reduction, device and wall time, memory, [saved tensors](glossary_EN.md#term-saved-tensors),
synchronization, and observer cost. Results form an empirical cost-sufficiency
frontier rather than a proof of a universally minimal quotient.

## 7. Exact verification

A counterfactual exact branch from identical state acts as the empirical
adjudicator of required equivalence. The primary utility is

$U_{G,t+1}=d(G_t,G_*)-d(G_{t+1},G_*).$

A materially positive utility for a proposed skipped sweep is a [dangerous miss](glossary_EN.md#term-dangerous-miss)
and blocks active control.

## 8. Primary hypotheses

- **H-TREF1:** [correction geometry](glossary_EN.md#term-correction-geometry) and state transport reduce operational
  manifestations of $\mathfrak D_{I\to R}$ relative to residual-only
  representation;
- **H-TREF2:** one registered $\phi_k$ reaches a point where further features
  do not provide practically meaningful regret reduction relative to cost;
- **H-Q1:** shadow [QWake-PC](glossary_EN.md#term-qwake-pc) generalizes across `model_seed`;
- **H-R1:** sweep reduction passing the safety gate produces device-time
  reduction.

## 9. Claim boundaries

- task-relative equivalence means the same admissible action, not tensor
  equality;
- sufficiency is evaluated only for the registered action space;
- `NCZ`, `ECZ`, and `TNZ` are diagnostics rather than control decisions;
- findings remain bounded by the studied [architecture](glossary_EN.md#term-architecture), data, seeds, exact
  implementation, and environment;
- a negative QWake result preserves the value of PC-CATM and diagnostic
  sufficiency analysis.
