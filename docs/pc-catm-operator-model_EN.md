# `PC-CATM`: operator model of correction aggregation and error transport

[Русская версия](pc-catm-operator-model.md)

## 1. Status, purpose, and relation to `PC-TREF`

[PC-CATM](glossary_EN.md#term-pc-catm) is the normative mechanism model of

```math
\text{error source}
\rightarrow
\text{state transport}
\rightarrow
\text{channel aggregation}
\rightarrow
\text{state correction}.
```

It is the mechanism layer of [PC-TREF](glossary_EN.md#term-pc-tref), does not
rename established observability, sufficiency, or quotient-space concepts, and
does not authorize a control action by itself. Norm, zero, and cost semantics
are frozen in the
[theoretical foundation](pc-tref-pc-catm-theoretical-foundation_EN.md).

Statements are marked as mathematical consequences (`T`), implementation
invariants (`I`), empirical hypotheses (`H`), controller rules (`P`), and claim
boundaries (`C`).

## 2. Norm measurement contract

Every norm-based indicator has a registered contract

```math
\mathcal N=(V,\|\cdot\|,s,\epsilon,\tau,\mathcal G),
```

specifying the space, norm, scale, denominator protection, numerical threshold,
and aggregation rule. Layer $l$, step $t$, dtype, device, and state version are
observation metadata.

For example,

```math
\|e_l^{(t)}\|_{2,\mathrm{rel}}
=
\frac{\|e_l^{(t)}\|_2}
     {\max(s_l^{(t)},\epsilon_l)}.
```

Values across layers or times are not combined without registered
normalization. Thresholds are not selected after confirmatory-result access.

## 3. Local energy and canonical channels

For layer $l$,

```math
p_l=f_l(h_{l-1};\theta_l),\qquad e_l=p_l-h_l.
```

With symmetric positive-semidefinite precision operator $\Pi_l$,

```math
F_l=\frac12 e_l^\top\Pi_l e_l,
\qquad
r_l=\Pi_l^{1/2}e_l.
```

[Canonical correction channels](glossary_EN.md#term-canonical-correction-channel)
include

```math
c_l^{(\mathrm{self})}=\Pi_l e_l,
\qquad
c_l^{(\mathrm{upper})}=-J_{h,l+1}^{*}\Pi_{l+1}e_{l+1}.
```

The resultant correction is

```math
u_l=S_l(\mathbf c_l)=\sum_a c_l^{(a)}.
```

`I1`: all channels in one observation use compatible state, parameter,
precision-operator, and Jacobian versions. `I2`: technical subdivision of one
energy term does not change its canonical-channel sum or registered indicators.

## 4. Exact null sets and precision-masked neighborhoods

The exact [correction-zero set](glossary_EN.md#term-correction-zero-set) is

```math
\mathcal Z_l^{(0)}=\ker S_l,
```

partitioned into

```math
\mathrm{NCZ}_l^{(0)}=\{\mathbf0\},
\qquad
\mathrm{ECZ}_l^{(0)}=\ker S_l\setminus\{\mathbf0\}.
```

Exact kernels are not replaced by threshold classes. The operational
neighborhood is a
[precision-masked zero](glossary_EN.md#term-precision-masked-zero):

```math
Z_{l,\tau}^{\mathcal N}
=
\{\mathbf c_l:\|S_l(\mathbf c_l)\|_{\mathcal N}\leq\tau_l\}.
```

`NCZ` requires low activity in every channel. `ECZ` requires active channels,
low resultant correction, and a registered destructive-interaction condition.
An `activity_guard` remains between quiet and active thresholds.

`T1`: exact `NCZ` and `ECZ` exhaust $\ker S_l$ but not every small nonzero
correction.

## 5. Correction geometry

Under one norm contract,

```math
A_l=\sum_a\|c_l^{(a)}\|_{\mathcal N},
\qquad
R_l=\left\|\sum_a c_l^{(a)}\right\|_{\mathcal N}.
```

The triangle inequality gives $0\leq R_l\leq A_l$. For $A_l>0$,
$\chi_l=R_l/A_l$.

For an inner-product-compatible norm, define $Q_l$, constructive interaction
$P_l$, and [destructive interaction](glossary_EN.md#term-destructive-interaction) $N_l$ so that
$R_l^2=Q_l+P_l-N_l$. The registered indicator is

```math
D_l=\frac{N_l}{\max(Q_l+P_l,\epsilon_l)}.
```

An operational `ECZ` claim requires activity, low $\chi_l$, and a registered
$D_l$ condition. Low $R_l$ alone is not [evidence](glossary_EN.md#term-evidence) of cancellation.

## 6. State-error transport

```math
\widetilde J_{h,l+1}=\Pi_{l+1}^{1/2}J_{h,l+1},
\qquad
c_l^{(\mathrm{upper})}=-\widetilde J_{h,l+1}^{*}r_{l+1}.
```

Exact [TNZ](glossary_EN.md#term-tnz) is

```math
\mathrm{TNZ}_l^{(0)}
=
\ker(\widetilde J_{h,l+1}^{*})\setminus\{0\}.
```

[Directional transport gain](glossary_EN.md#term-directional-transport-gain) is

```math
\gamma_{h,l}
=
\frac{\|\widetilde J_{h,l+1}^{*}r_{l+1}\|_{\mathcal N_{out}}}
     {\max(\|r_{l+1}\|_{\mathcal N_{in}},\epsilon_l)}.
```

Input and output norms are explicit. Cumulative transport is evaluated
directly rather than by multiplying local gains.

## 7. Matrix-free block probe and B1/B2 candidates

A [block-Jacobian probe](glossary_EN.md#term-block-jacobian-probe) evaluates
multiple VJP/JVP quantities on one frozen state snapshot without materializing
the full Jacobian. Isolated B1, composite B2, and optionally block-composite
variants are compared.

`C1`: one logical autograd call does not imply one GPU kernel, lower asymptotic
work, lower memory, or lower [runtime](glossary_EN.md#term-runtime). `I3`: a frozen probe does not replace the
sequential `Strict` path before a [candidate](glossary_EN.md#term-candidate)-specific numerical-equivalence
gate.

B1/B2 preregistration freezes norm contracts, state/RNG restoration, endpoints,
the [cost vector](glossary_EN.md#term-cost-vector), and [fallback](glossary_EN.md#term-fallback) rule.

## 8. Parameter null as a limited extension

```math
\widetilde J_{\theta,l}=\Pi_l^{1/2}J_{\theta,l},
\qquad
K_{\theta,l}=\widetilde J_{\theta,l}\widetilde J_{\theta,l}^{*}.
```

[PNZ](glossary_EN.md#term-pnz) is

```math
\mathrm{PNZ}_l^{(0)}
=
\ker(\widetilde J_{\theta,l}^{*})\setminus\{0\}.
```

`T2`: $\ker K_{\theta,l}=\ker\widetilde J_{\theta,l}^{*}$. PNZ only means
local first-order inaccessibility to one layer's parameters and remains a
limited extension.

## 9. Cost separation

`PC-CATM` features may incur [diagnostic-mechanism cost](glossary_EN.md#term-diagnostic-mechanism-cost), [observer cost](glossary_EN.md#term-observer-cost), and
[control-plane cost](glossary_EN.md#term-control-plane-cost). `SI-MA1` evaluated the second boundary under its registered
observer-calibrated contract. Its over-closure is not subtracted from the first
or third component. Future end-to-end analysis uses the registered
[cost vector](glossary_EN.md#term-cost-vector).

## 10. Convergence and claim boundaries

The conditions $u_l=0$, $u_l=0$ for every layer, $\nabla_HF=0$,
$\Phi(H)=H$, and $\nabla_\theta F=0$ are distinct. Therefore `ECZ` does not
establish false convergence, `NCZ` input familiarity, `TNZ` absence of upstream
error, or `PNZ` global unlearnability. A zero or precision-masked correction in
one layer does not permit skipped computation.

## 11. Control and mandatory tests

[Counterfactual exact verification](glossary_EN.md#term-exact-verification)
links features to task-relative utility. A
[dangerous miss](glossary_EN.md#term-dangerous-miss) blocks active control.

Mandatory deterministic tests include exact and near-zero `NCZ/ECZ`,
orthogonality, three-channel cancellation, channel-subdivision invariance,
scaled $J=cI$, exact/near `TNZ`, block probes, a `PNZ` control, and safe handling
of zero vectors. Every near-zero test cites an explicit norm contract.

## 12. Hypotheses

`H-CZ1` expects [correction geometry](glossary_EN.md#term-correction-geometry) to add information about next-sweep utility
beyond residual-only features. `H-T1` expects transport features to separate
internal `NCZ` from attenuation. `H-Q1` expects geometry, transport,
persistence, and uncertainty to reduce dangerous misses. `H-R1` expects
safety-gated exact-sweep reduction to lower end-to-end runtime after every cost
component is included.

Unsupported hypotheses remain negative or mixed results.
