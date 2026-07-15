# PC-CATM: operator model of correction aggregation and error transport

[Русская версия](pc-catm-operator-model.md)

## 1. Status, purpose, and relationship to PC-TREF

This document defines the normative theory for the primary post-B0 working
scenario. It does not change B0 [evidence](glossary_EN.md#term-evidence), claim that new experiments have been
executed, or merge mathematical consequences with empirical hypotheses and
controller policies.

Statement classes are:

- `T`: mathematical consequence of definitions;
- `I`: implementation invariant requiring verification;
- `H`: empirical hypothesis;
- `P`: controller policy;
- `C`: claim boundary.

## 2. Local energy and canonical channels

For layer \(l\):

\[
p_l=f_l(h_{l-1};\theta_l),\qquad e_l=p_l-h_l.
\]

For a symmetric positive-semidefinite precision operator \(\Pi_l\):

\[
F_l=\frac12 e_l^\top\Pi_l e_l,\qquad
r_l=\Pi_l^{1/2}e_l.
\]

A [canonical correction channel](glossary_EN.md#term-canonical-correction-channel)
groups one causally meaningful energy contribution. The minimal hidden-layer
partition for a sequential network is:

\[
c_l^{(\mathrm{self})}=\Pi_l e_l,
\]

\[
c_l^{(\mathrm{upper})}
=-J_{h,l+1}^{*}\Pi_{l+1}e_{l+1}.
\]

The resultant state correction is:

\[
u_l=S_l(\mathbf c_l)=\sum_a c_l^{(a)}.
\]

**I1.** Every channel in one observation uses compatible state, parameter,
precision, and Jacobian versions.

**I2.** Technical subdivision of one energy term inside a channel does not
change the grouped channel or its diagnostics.

## 3. Correction-zero set

The [correction-zero set](glossary_EN.md#term-correction-zero-set) is:

\[
\mathcal Z_l^{(0)}=\ker S_l.
\]

It is partitioned into:

\[
\mathrm{NCZ}_l^{(0)}=\{\mathbf0\},
\]

\[
\mathrm{ECZ}_l^{(0)}=\ker S_l\setminus\{\mathbf0\}.
\]

The [Null-Contribution Zone](glossary_EN.md#term-ncz) is the trivial zero. The
[Error-Cancellation Zone](glossary_EN.md#term-ecz) is the nontrivial zero where
at least one channel is nonzero while their sum is zero.

**T1.** NCZ and ECZ exhaust the exact kernel of \(S_l\), but not every small
nonzero correction.

## 4. Correction geometry

[Correction geometry](glossary_EN.md#term-correction-geometry) uses:

\[
A_l=\sum_a\|c_l^{(a)}\|,
\qquad
R_l=\left\|\sum_a c_l^{(a)}\right\|.
\]

The triangle inequality gives:

\[
0\le R_l\le A_l.
\]

**T2.** \(A_l=0\) if and only if every channel is zero.

**T3.** \(A_l>0\) and \(R_l=0\) if and only if the observation belongs to exact ECZ.

For \(A_l>0\), [resultant efficiency](glossary_EN.md#term-resultant-efficiency) is:

\[
\chi_l=\frac{R_l}{A_l}.
\]

Its complement is an aggregation deficit, not a cancellation fraction, because
orthogonal channels can also reduce \(R_l/A_l\).

Define:

\[
Q_l=\sum_a\|c_l^{(a)}\|^2,
\]

\[
P_l=2\sum_{a<b}\max(\langle c_l^{(a)},c_l^{(b)}\rangle,0),
\]

\[
N_l=2\sum_{a<b}\max(-\langle c_l^{(a)},c_l^{(b)}\rangle,0).
\]

Then:

\[
R_l^2=Q_l+P_l-N_l.
\]

[Destructive interaction](glossary_EN.md#term-destructive-interaction) is:

\[
D_l=\frac{N_l}{Q_l+P_l},\qquad A_l>0.
\]

**T4.** \(0\le D_l\le1\).

**T5.** For \(A_l>0\), \(D_l=1\) if and only if \(R_l=0\).

The numerical score

\[
Z_l=\frac{A_l-R_l}{A_l+\tau_l}
\]

is retained as a resultant-suppression score, not as standalone evidence of
cancellation.

## 5. Operational classification

After normalizing activity using quantities estimated only on the permitted
selection scope, define:

\[
\alpha_l^{(\mathrm{quiet})}<\alpha_l^{(\mathrm{active})}.
\]

Classes are:

1. `NCZ`: activity below the quiet threshold;
2. `activity_guard`: activity between thresholds;
3. `ECZ`: active, low \(\chi_l\), and high \(D_l\);
4. `active_non_ecz`: active but outside the ECZ gate;
5. `invalid`: incompatible snapshot, nonfinite values, or missing required fields.

Thresholds are frozen before [test-dataset access](glossary_EN.md#term-test-dataset-access).

## 6. State-error transport

[State-error transport](glossary_EN.md#term-state-transport) is:

\[
\widetilde J_{h,l+1}=\Pi_{l+1}^{1/2}J_{h,l+1},
\]

\[
c_l^{(\mathrm{upper})}
=-\widetilde J_{h,l+1}^{*}r_{l+1}.
\]

The [Transport-Null Zone](glossary_EN.md#term-tnz) is:

\[
\mathrm{TNZ}_l^{(0)}
=\ker(\widetilde J_{h,l+1}^{*})\setminus\{0\}.
\]

TNZ and ECZ are distinct kernels: transport of a source versus aggregation of
channels already obtained.

The [directional transport gain](glossary_EN.md#term-directional-transport-gain) is:

\[
\gamma_{h,l}
=\frac{\|\widetilde J_{h,l+1}^{*}r_{l+1}\|}{\|r_{l+1}\|},
\qquad r_{l+1}\ne0.
\]

It describes one observed direction. Cumulative transport is computed directly:

\[
q_l=T_{l\leftarrow L}r_L,
\qquad
\Gamma_{h,l}=\frac{\|q_l\|}{\|r_L\|}.
\]

Products of local directional gains are not used as the primary cumulative
measure because the direction changes after each operator.

## 7. Matrix-free block probe

The [block-Jacobian probe](glossary_EN.md#term-block-jacobian-probe) computes on
one frozen snapshot:

\[
D\mathcal P(H)^*E
=
(J_{h,2}^*e_2,\ldots,J_{h,L}^*e_L)
\]

without materializing a full Jacobian. Isolated, composite, and chunked-composite
forms are compared.

**C1.** One composite call is not called an acceleration before [device time](glossary_EN.md#term-device-time),
memory, [saved tensors](glossary_EN.md#term-saved-tensors), and graph lifetime are measured.

**I3.** A frozen diagnostic probe does not replace sequential `Strict`
[execution](glossary_EN.md#term-execution) before the B2 equivalence gate.

## 8. Parameter null as a limited extension

For layer parameters:

\[
\widetilde J_{\theta,l}=\Pi_l^{1/2}J_{\theta,l},
\qquad
K_{\theta,l}=\widetilde J_{\theta,l}\widetilde J_{\theta,l}^{*}.
\]

The [Plasticity-Null Zone](glossary_EN.md#term-pnz) is:

\[
\mathrm{PNZ}_l^{(0)}
=\ker(\widetilde J_{\theta,l}^{*})\setminus\{0\}.
\]

**T6.** \(\ker K_{\theta,l}=\ker\widetilde J_{\theta,l}^{*}\).

PNZ means only local first-order inaccessibility to that layer's parameters. In
Scenario A it is limited to theory, a deterministic control, and an optional
small passive audit.

## 9. Convergence and claim boundaries

The following are distinct:

\[
u_l=0,
\qquad
u_l=0\ \forall l,
\qquad
\nabla_HF=0,
\qquad
\Phi(H)=H,
\qquad
\nabla_\theta F=0.
\]

Therefore ECZ does not prove false convergence, NCZ does not prove familiarity,
TNZ does not imply absent upper error, PNZ does not imply global
unlearnability, and a zero correction does not authorize skipped computation or
learning.

## 10. Connection to control

[Counterfactual exact verification](glossary_EN.md#term-exact-verification)
compares a proposed decision with an exact branch from identical state. The
primary label is [endpoint-gradient utility](glossary_EN.md#term-endpoint-gradient-utility).

A [dangerous miss](glossary_EN.md#term-dangerous-miss) blocks active mode.
[QWake-PC](glossary_EN.md#term-qwake-pc) operates in [shadow mode](glossary_EN.md#term-shadow-mode) first and may
control only full exact sweeps after registered gates pass.

## 11. Required deterministic controls

- exact NCZ;
- two-channel exact and near ECZ;
- aligned and orthogonal channels;
- three-channel 120-degree exact ECZ;
- channel-refinement invariance;
- \(J=cI\) for \(c\in\{1,0.5,0.1,0.01,0\}\);
- exact TNZ;
- orthogonal norm-preserving transport;
- isolated and block probes;
- deterministic linear PNZ;
- zero-safe comparison without cosine for two zero vectors.

## 12. Relationship to the diagnostic quotient

PC-CATM features define successive refinements of the diagnostic
representation: activity, correction geometry, transport, and temporal
persistence. Their necessity is evaluated by reduction of the
[task-relative equivalence defect](glossary_EN.md#term-task-relative-equivalence-defect)
under controlled observer cost, rather than by descriptive completeness alone.

## 13. Primary hypotheses

- **H-CZ1:** correction geometry adds information about next exact-sweep utility
  beyond activity, layer, and sweep index;
- **H-T1:** transport diagnostics distinguish intrinsic NCZ from
  attenuation-masked NCZ;
- **H-Q1:** combining geometry, transport, temporal persistence, and uncertainty
  reduces dangerous misses;
- **H-R1:** exact-sweep reduction yields measurable device-time reduction after
  observer cost is included.

Unsupported hypotheses remain negative or mixed findings and are not replaced
with broader claims.
