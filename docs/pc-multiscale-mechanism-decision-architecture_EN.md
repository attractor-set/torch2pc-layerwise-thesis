# Multiscale mechanism–decision architecture for predictive coding

[Русская версия](pc-multiscale-mechanism-decision-architecture.md)

## 1. Status and boundary

The [multiscale mechanism–decision architecture](glossary_EN.md#term-multiscale-mechanism-decision-architecture)
connects `PC-CATM`, `PC-TREF`, and `QWake-PC` in one compositional schema. This
is a theoretical and design-level extension. It does not permit
[execution](glossary_EN.md#term-execution), modify frozen B1/B2 contracts, open
the test split, or make a multiscale controller a mandatory condition of
`A-Core`.

The current study preserves continuous states and errors in the base PC
network. Spike-like properties apply only to the organization of thresholded,
temporally sparse, and scale-selective correction events.

## 2. Scale set

Let

```math
\mathcal S=(S,\preceq)
```

be a finite partially ordered set of computational scales. The notation
$s\preceq t$ means that $s$ is finer than $t$. A possible hierarchy is:

```text
state coordinate
→ coordinate group or channel
→ block
→ layer
→ complete network
```

An implementation need not support every scale. A scale enters the executable
architecture only after its state, norm, aggregation rules, action space, cost,
and exact-verification contracts are frozen.

## 3. Scale-specific PC-CATM model

For every $s\in S$, define

```math
\mathcal M_s=
(\mathcal X_s,\mathcal C_s,\mathcal T_s,\mathcal G_s,
\|\cdot\|_s,\chi_s),
```

where:

- $\mathcal X_s$ is the state space;
- $\mathcal C_s$ is the family of canonical correction channels;
- $\mathcal T_s$ contains error-transport operators;
- $\mathcal G_s$ is the channel-aggregation operator;
- $\|\cdot\|_s$ is the registered norm;
- $\chi_s$ is the mechanism-regime classifier.

For state $x_s$, the resulting correction is

```math
u_s(x_s)=
\mathcal G_s
\left(
T_s^{(1)}c_s^{(1)},\ldots,T_s^{(m_s)}c_s^{(m_s)}
\right).
```

The classifier may return `NCZ`, `ECZ`, `TNZ`, `active`, `unresolved`, or
`invalid`. These categories describe mechanisms and do not directly authorize
a computational action.

## 4. Diagnostic representation and sufficiency

At every scale, define a representation

```math
\phi_s:\mathcal X_s\times\mathcal H_s\rightarrow\mathcal Z_s,
```

which may contain channel geometry, transport, cancellation, residual,
temporal persistence, uncertainty, coverage, and feature cost.

Let $\mathcal A_s$ be the registered action space and $R_s(a,x_s)$ the action
regret. The admissible action set is

```math
\mathcal A_s^*(x_s)=
\{a\in\mathcal A_s:
R_s(a,x_s)\leq\varepsilon_s
\land Safe_s(a,x_s)\}.
```

The diagnostic representation is sufficient for the scale-$s$ decision when

```math
\phi_s(x_s)=\phi_s(y_s)
\Longrightarrow
\mathcal A_s^*(x_s)=\mathcal A_s^*(y_s).
```

This is a scale-specific specialization of `PC-TREF`. Sufficiency at one scale
does not automatically transfer to another scale.

## 5. Cross-scale composition

For $s\preceq t$, define state and channel coarse-graining maps:

```math
P_{s\rightarrow t}:\mathcal X_s\rightarrow\mathcal X_t,
```

```math
A_{s\rightarrow t}:\mathcal C_s\rightarrow\mathcal C_t.
```

The [correction-composition defect](glossary_EN.md#term-correction-composition-defect)
is

```math
\Delta^u_{s\rightarrow t}(x_s)=
\left\|
P^u_{s\rightarrow t}(u_s(x_s))
-
u_t(P_{s\rightarrow t}(x_s))
\right\|_t.
```

A cross-scale claim requires a frozen tolerance
$\tau^u_{s\rightarrow t}$ and the gate

```math
\Delta^u_{s\rightarrow t}(x_s)
\leq\tau^u_{s\rightarrow t}.
```

Without this gate, the following implications are not licensed:

```math
NCZ_s \Rightarrow NCZ_t,
```

```math
ECZ_s \Rightarrow ECZ_t,
```

nor may a local permission to stop be transferred to the complete network.

## 6. QWake-PC policy over scale, action, and budget

The controller selection object is `scale, action, budget`.

`QWake-PC` consumes the available representations

```math
\Phi_t=\{\phi_s(x_{s,t},h_{s,t}):s\in S_t\}
```

and proposes

```math
\pi_Q:(\Phi_t,H_t)\rightarrow(s_t,a_t,k_t),
```

where $s_t$ is the action scale, $a_t\in\mathcal A_{s_t}$ is the action, and
$k_t$ is the computational budget.

Design-level action examples are:

```text
stop
local_sweep(block_id)
layer_sweep(layer_id)
full_exact
fallback_exact
```

Membership in the design action space does not constitute admission. An
action–budget pair is admissible only after positive coverage, sufficiency,
exact counterfactual verification, regret, safety, and complete-cost gates.

## 7. Conservative escalation

When no action is admissible at scale $s$, the controller performs
[adaptive escalation](glossary_EN.md#term-adaptive-escalation) to a coarser
scale:

```text
cheap local diagnostics
→ local action when evidentially admissible
→ coarser scale under insufficiency
→ fallback_exact under unsafe uncertainty
```

Formally, escalation is required when

```math
\mathcal Q_s(\Phi_t,H_t)=\varnothing.
```

Insufficient local information must lead to more complete computation rather
than more aggressive reduction.

## 8. Spike-like boundary of the current study

[Spike-like control dynamics](glossary_EN.md#term-spike-like-control-dynamics)
may include diagnostic accumulation, a wake threshold, hysteresis, persistence,
a discrete budget, and a post-event quiet interval. It makes computation
event-driven and sparse but does not change the type of the base state and error
dynamics.

The canonical boundary of the current study is:

> The multiscale [QWake-PC](glossary_EN.md#term-qwake-pc) architecture moves predictive-coding inference toward
> spike-like event-driven computation by introducing thresholded, temporally
> sparse, and scale-selective correction events, while leaving the underlying
> state and error dynamics non-spiking.

The current system is therefore not classified as a spiking neural network.

## 9. Prospective QWake-SPC boundary

[`QWake-SPC`](glossary_EN.md#term-qwake-spc) denotes a possible subsequent
research line in which qualified correction events become native spikes and the
state, error transport, communication, and learning paths receive spike-native
implementations.

A prospective policy may have the form

```math
\pi_Q^S:\Phi_t^S\rightarrow(s_t,a_t,k_t,\tau_t,Z_t),
```

where $\tau_t$ is a temporal window and $Z_t$ contains native spike events.

`QWake-SPC` is outside the current master's-thesis boundary. The term does not
denote an implemented controller, permit an experiment, or become a completion
condition for `A-Min`, `A-Core`, or `A-Max`.

## 10. Effect on the current plan

The critical path remains unchanged:

```text
B1/B2
→ matched profiling
→ EX-IF0
→ passive PC-CATM
→ offline screening
→ predictor
→ exact verification
→ shadow QWake-PC
→ conditional active control
```

Within the master's thesis, the multiscale architecture serves as:

1. a theoretical organization of the existing mechanism and decision levels;
2. a language for a possible block, layer, and network comparison;
3. a limited exploratory pilot only when already permitted data suffice;
4. a foundation for a future PhD program rather than a new mandatory experiment.

## 11. Architectural invariants

1. `PC-CATM` describes a mechanism but does not authorize an action.
2. Norms, aggregation, thresholds, regret, and cost are defined separately at
   each scale.
3. A local `NCZ` or `ECZ` does not automatically transfer to a coarser scale.
4. `ECZ` does not authorize `local_sweep(block_id)` without separate exact
   verification.
5. Insufficiency, coverage failure, and unsafe uncertainty trigger escalation.
6. A negative result for one controller does not invalidate `PC-TREF`,
   `PC-CATM`, or supported passive observations.
7. No new scale, local action, or spike-native component receives execution
   authority from this document.

## 12. Testable propositions

Until separately preregistered, the following remain hypotheses:

- a cheaper scale may be sufficient for a registered decision;
- conservative escalation may reduce the number of complete exact sweeps;
- the composition defect may remain within a registered tolerance for selected
  scale pairs;
- the minimum sufficient scale may depend on state;
- spike-like event organization may provide a foundation for a later
  spike-native extension.

## 13. Claim boundary

This document does not establish that:

- `PC-CATM` is scale-invariant;
- mechanism regimes are preserved under aggregation;
- a state coordinate is a biological neuron;
- a local correction preserves the network [endpoint](glossary_EN.md#term-endpoint);
- multiscale `QWake-PC` reduces complete [runtime](glossary_EN.md#term-runtime);
- spike-like control is equivalent to neural spikes;
- `QWake-SPC` has been implemented or empirically supported.
