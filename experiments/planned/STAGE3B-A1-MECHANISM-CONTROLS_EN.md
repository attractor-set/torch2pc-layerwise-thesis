# Stage 3B A1 — deterministic PC-CATM mechanism controls

[Русская версия](STAGE3B-A1-MECHANISM-CONTROLS.md)

## Status

The protocol is frozen. The executable implementation, smoke results, and confirmatory results are absent.

This package freezes the mandatory deterministic checks for Scenario A stages A4–A7 before `SI-MA0` begins. It does not modify previously published implementations or evidence packages.

## Registered baseline

- repository evidence commit: `0b6a9e4aa0ac665adcc82d897845a0179fa3f990`;
- OBS-OH0 implementation commit: `59dbcfa41a9c35cc8b72e75288aaa505459499d8`;
- OBS-OH0 tag: `stage3b-a1-obs-oh0-v1`;
- OBS-OH0 benchmark schema: `stage3b-a1-obs-oh0-v1`;
- passive-observer schema: `stage3b-a1-obs-ni0-first-forward-io-v1`;
- Torch2PC commit: `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4`;
- mechanism-controls contract id: `stage3b-a1-mechanism-controls-v1`.

The sealed `EQ-S0`, `EQ-S1`, `EQ-S2`, `OBS-NI0`, and `OBS-OH0` packages are immutable prerequisites. Their checksums are verified before controlled smoke and confirmatory execution.

## Research question

Does the future PC-CATM implementation correctly distinguish and reproduce the registered mechanisms:

1. trivial aggregation zero (`NCZ`);
2. nontrivial aggregation zero (`ECZ`);
3. active geometry without cancellation;
4. null transport (`TNZ`);
5. scaled and norm-preserving transport;
6. the FixedPred temporal wave at `eta=1`;
7. isolated, composite, and chunked-composite VJP probes on one frozen snapshot?

A limited additional question asks whether a deterministic linear `PNZ` construction is reproduced without using it as an `SI-MA0` gate.

## Role of the package

The package is a deterministic validity gate. It tests definitions, constructions, indexing, matrix-free VJPs, and consistency with the frozen operator equations.

A positive result opens `SI-MA0` preregistration but does not by itself establish:

- empirical prevalence of `NCZ`, `ECZ`, or `TNZ` during training;
- predictive usefulness of diagnostic features;
- sufficiency of the diagnostic quotient;
- permission to skip exact sweeps;
- acceleration of `Strict`;
- causal validity of PC-CATM beyond the registered constructions.

## Gate hierarchy

The core gate contains four mandatory sub-gates:

```text
GEO-C0  correction-geometry controls
TR-C0   state-transport controls
TMP-C0  Rosenbaum temporal-wave control
JAC-C0  frozen block-Jacobian probe
```

`SI-MA0` opens only when:

```text
core_passed = GEO-C0 and TR-C0 and TMP-C0 and JAC-C0
```

Limited extension:

```text
PNZ-L0  deterministic linear parameter-null control
```

`PNZ-L0` is executed and published separately. Its status does not alter `core_passed` and does not control access to `SI-MA0`.

## Normative operator model

For hidden layer `l`:

\[
c_l^{(\mathrm{self})}=\Pi_l e_l,
\]

\[
c_l^{(\mathrm{upper})}=-J_{h,l+1}^{*}\Pi_{l+1}e_{l+1},
\]

\[
u_l=S_l(\mathbf c_l)=\sum_a c_l^{(a)}.
\]

The correction-zero set is:

\[
\mathcal Z_l^{(0)}=\ker S_l.
\]

Its registered partition is:

\[
\mathrm{NCZ}_l^{(0)}=\{\mathbf0\},
\]

\[
\mathrm{ECZ}_l^{(0)}=\ker S_l\setminus\{\mathbf0\}.
\]

Geometry quantities are:

\[
A_l=\sum_a\|c_l^{(a)}\|,
\qquad
R_l=\left\|\sum_a c_l^{(a)}\right\|,
\]

\[
\chi_l=R_l/A_l \quad (A_l>0),
\]

\[
Q_l=\sum_a\|c_l^{(a)}\|^2,
\]

\[
P_l=2\sum_{a<b}\max(\langle c_l^{(a)},c_l^{(b)}\rangle,0),
\]

\[
N_l=2\sum_{a<b}\max(-\langle c_l^{(a)},c_l^{(b)}\rangle,0),
\]

\[
D_l=N_l/(Q_l+P_l) \quad (A_l>0).
\]

State-error transport is:

\[
\widetilde J_{h,l+1}=\Pi_{l+1}^{1/2}J_{h,l+1},
\]

\[
c_l^{(\mathrm{upper})}=-\widetilde J_{h,l+1}^{*}r_{l+1},
\]

\[
\mathrm{TNZ}_l^{(0)}=\ker(\widetilde J_{h,l+1}^{*})\setminus\{0\}.
\]

Directional transport gain is:

\[
\gamma_{h,l}=\frac{\|\widetilde J_{h,l+1}^{*}r_{l+1}\|}{\|r_{l+1}\|},
\qquad r_{l+1}\ne0.
\]

## General execution contract

All controlled executions use:

- contract id `stage3b-a1-mechanism-controls-v1`;
- a frozen implementation source commit before the first controlled smoke run;
- canonical Docker CPU and Docker/ROCm lanes;
- CPU dtype `float64`;
- ROCm dtype `float32`;
- deterministic algorithms;
- Python, NumPy, CPU Torch, and ROCm RNG snapshots;
- explicit source commit, branch, image, image revision, and Torch2PC commit;
- no test-split access;
- no train or validation dataset in the primary deterministic suite;
- synthetic tensors, operators, inputs, and targets fully defined by the contract;
- retention of every failed and nonfinite record;
- no outlier or repeat deletion after results are inspected.

Every record contains:

```text
control_id
sub_gate
case_id
lane
device
dtype
model_seed
construction_seed
layer_index
sweep_index
contract_id
source_git_commit
experiment_image
image_revision
torch2pc_commit
finite
passed
```

Inapplicable indices are stored as `null` rather than replaced with sentinel values.

## Tensor comparison

For nonzero reference tensors, the implementation stores:

- absolute L2 error;
- relative L2 error;
- maximum absolute error;
- cosine similarity;
- norm ratio;
- finite flag.

Cosine similarity is not calculated for two zero-like tensors. The zero-safe rule is:

1. when both norms are at most `zero_atol`, comparison uses `max_abs`;
2. when only one tensor is zero-like, the comparison fails;
3. cosine is stored as `null` for a zero-like pair;
4. NaN and infinity always fail the record.

## Registered threshold profiles

### Algebraic zero

```text
CPU float64: zero_atol = 1e-12
ROCm float32: zero_atol = 1e-6
```

### Analytic vector equivalence

```text
CPU float64:
  max_relative_l2 = 1e-10
  max_abs = 1e-10
  min_cosine = 0.999999999

ROCm float32:
  max_relative_l2 = 1e-4
  max_abs = 1e-5
  min_cosine = 0.9999
```

### Implementation snapshot equivalence

```text
CPU float64:
  max_relative_l2 = 1e-7
  max_abs = 1e-9
  min_cosine = 0.99999

ROCm float32:
  max_relative_l2 = 1e-3
  max_abs = 1e-5
  min_cosine = 0.999
```

Each record names its threshold profile. Thresholds are not retuned after the first controlled output.

## Registered construction seeds

For algebraic constructions:

```text
construction_seed = 0 -> scale = 0.25
construction_seed = 1 -> scale = 1.0
construction_seed = 2 -> scale = 4.0
```

The primary space is `R^8` with standard basis `e_0,...,e_7`.

Construction seed indexes a registered construction and is not a statistical unit. The deterministic package performs no statistical tests and does not treat repeated constructions as independent samples.

# GEO-C0 — correction geometry

## GEO-01: exact NCZ

For each scale:

```text
c_self  = 0
c_upper = 0
```

Expected:

```text
A = 0
R = 0
class = NCZ
chi = null
D = null
```

Every channel norm and the resultant norm must pass the algebraic-zero threshold.

## GEO-02: exact two-channel ECZ

```text
c_self  = scale * e_0
c_upper = -scale * e_0
```

Expected:

```text
A = 2 * scale
R = 0
chi = 0
D = 1
class = ECZ
```

At least one channel norm must be strictly above `active_floor = 100 * zero_atol`.

## GEO-03: near two-channel ECZ

Freeze `delta = 1e-3`:

```text
c_self  = scale * e_0
c_upper = -(1 - delta) * scale * e_0
```

Analytic references:

\[
A=(2-\delta)s,
\qquad
R=\delta s,
\qquad
\chi=\frac{\delta}{2-\delta}.
\]

The correction is nonzero and the expected label is `near_ecz_control`, not exact `ECZ`.

## GEO-04: aligned channels

```text
c_self  = scale * e_0
c_upper = 2 * scale * e_0
```

Expected:

```text
R = A
chi = 1
D = 0
class = active_non_ecz
```

## GEO-05: orthogonal channels

```text
c_self  = scale * e_0
c_upper = scale * e_1
```

Expected:

```text
A = 2 * scale
R = sqrt(2) * scale
chi = sqrt(2) / 2
P = 0
N = 0
D = 0
class = active_non_ecz
```

This control freezes the fact that reduced `R/A` is not by itself evidence of cancellation.

## GEO-06: three-channel 120-degree ECZ

In the first two coordinates:

```text
c_0 = scale * (1, 0)
c_1 = scale * (-1/2,  sqrt(3)/2)
c_2 = scale * (-1/2, -sqrt(3)/2)
```

Expected:

```text
A = 3 * scale
R = 0
chi = 0
D = 1
all pairwise cosine = -1/2
class = ECZ
```

## GEO-07: channel-refinement invariance

Canonical channel:

```text
c_self = scale * e_0 + 2 * scale * e_1
```

Technical split:

```text
part_0 = 0.25 * c_self
part_1 = 0.75 * c_self
```

After grouping by canonical channel id, the following must agree:

- grouped channel tensor;
- `A`, `R`, `Q`, `P`, `N`, `D`, and `chi`;
- final class;
- canonical-channel record key.

Technical parts are not treated as separate causal channels.

## GEO-08: zero-safe comparison

Compare:

```text
reference = 0
candidate = 0
```

Expected:

```text
passed = true
cosine = null
zero_safe_path = true
```

A separate negative-control record compares `0` with `active_floor * e_0`; it must correctly return `passed = false` without NaN. This expected false result is successful behavior of the control case.

## GEO-C0 volume

Per confirmatory lane:

```text
8 case families * 3 construction seeds = 24 case records
```

GEO-C0 passes only when every analytic identity, expected label, and zero-safe behavior passes on both lanes.

# TR-C0 — state-error transport

## TR-01: scaled identity transport

In `R^8`:

```text
J = c * I
c in {1, 0.5, 0.1, 0.01, 0}
r = registered nonzero source direction
```

Every construction seed uses a fixed nonzero direction with norm `scale`.

Expected:

\[
J^*r=cr,
\qquad
\gamma=|c|.
\]

For `c=0`, the source remains active, the transported vector is zero, and class is `TNZ`.

## TR-02: exact TNZ of a nonzero operator

```text
J = diag(1, 1, 0, 0, 0, 0, 0, 0)
r = scale * e_2
```

Expected:

```text
source norm > active_floor
transported norm <= zero_atol
gamma = 0
class = TNZ
operator norm > 0
```

## TR-03: active control for the same operator

```text
J = diag(1, 1, 0, 0, 0, 0, 0, 0)
r = scale * e_0
```

Expected:

```text
J* r = r
gamma = 1
class = transported_active
```

## TR-04: orthogonal norm-preserving transport

Use a fixed signed permutation operator `O`:

```text
O e_0 = e_1
O e_1 = -e_0
O e_k = e_k for k >= 2
```

Expected:

```text
||O* r|| = ||r||
gamma = 1
inner-product adjoint identity passed
class = transported_active
```

Adjoint identity:

\[
\langle Jx,r\rangle=\langle x,J^*r\rangle.
\]

## TR-05: direct cumulative transport

For a chain of three registered operators, calculate:

```text
q_sequential = J_1* (J_2* (J_3* r))
q_direct     = T* r
T            = J_3 J_2 J_1
```

Verify `q_sequential ≈ q_direct`. Primary cumulative gain is calculated directly as `||q_direct|| / ||r||`. The product of local directional gains is retained only as a descriptive field.

## TR-06: distinguishing TNZ from ECZ

Two constructions use the same active source.

### TNZ construction

```text
J* r = 0
c_self != 0
u = c_self
```

Expected: `TNZ` at the transport stage and `active_non_ecz` at the aggregation stage.

### ECZ construction

```text
J* r != 0
c_upper = -J* r
c_self = -c_upper
u = 0
```

Expected: active transport and `ECZ` at the aggregation stage.

The two mechanisms remain distinct.

## TR-C0 volume

Per confirmatory lane:

```text
TR-01: 5 scales * 3 construction seeds = 15
TR-02..TR-06: 5 families * 3 construction seeds = 15
total = 30 transport records
```

TR-C0 passes only when every analytic output, adjoint identity, mechanism label, and cumulative comparison passes on both lanes.

# TMP-C0 — Rosenbaum temporal control

## Purpose

The control tests FixedPred temporal error propagation under:

```text
eta = 1
network depth L = 6
feed-forward initialization
```

It uses a separate nondegenerate linear sequential model rather than FashionMNIST or MNIST. Every local Jacobian is diagonal with nonzero diagonal entries. Inputs, targets, and weights are fully determined by construction seed.

## Indices

Registered indices are:

```text
prediction layer index: 1..L
state layer index:      0..L-1
sweep index:            1..n
output error source:    epsilon_L before sweep 1
```

For the reverse-layer FixedPred loop, expect:

```text
first nonzero dv at state layer l = sweep L - l
first nonzero stored epsilon_l for l=1..L-1 = sweep L - l + 1
epsilon_L is active before sweep 1
```

`nonzero` means norm above the lane-specific `active_floor`.

## Registered sweep counts

Run:

```text
n = L - 1
n = L
n = L + 1
```

Expected:

- `n=L-1` is a positive insufficient-wave control and retains a nonzero difference in the first parameter-gradient block relative to BP;
- `n=L` reaches the first layer and passes endpoint-gradient equivalence with BP;
- `n=L+1` remains equivalent to `n=L` and BP in the registered linear construction.

Separation floor for the expected `n=L-1` difference:

```text
CPU float64: first-block relative L2 > 1e-8
ROCm float32: first-block relative L2 > 1e-5
```

If the construction does not create this preregistered difference, the record fails; the construction is not replaced after results are inspected.

## Trace contract

For every `(lane, construction_seed, sweep, state_layer)`, store:

- epsilon-before-update norm;
- transported upper-term norm;
- local-error norm;
- `dv` norm;
- state version before and after update;
- Jacobian version id;
- expected first-active sweep;
- observed first-active sweep;
- finite flag;
- ordering flag.

Per confirmatory lane:

```text
3 construction seeds * 6 sweeps * 6 state layers = 108 temporal event records
3 temporal summary records
```

The `n=L-1` and `n=L+1` endpoint comparisons are included in summary records; the primary wave trace is recorded for `n=L`.

## TMP-C0 pass criteria

TMP-C0 passes when, on both lanes:

- the output source is active before sweep 1;
- every first-active index matches the registered formula;
- state versions are monotonic and increase exactly once per update event;
- the Jacobian version remains fixed for FixedPred;
- `n=L-1` passes the expected-insufficient positive control;
- `n=L` matches BP;
- `n=L+1` matches `n=L` and BP;
- all 108 event records and 3 summary records are present;
- keys are unique and values finite.

# JAC-C0 — frozen block-Jacobian probe

## Common object

On one frozen snapshot, calculate:

\[
D\mathcal P(H)^*E=(J_{h,2}^*e_2,\ldots,J_{h,L}^*e_L).
\]

Compare:

```text
isolated_vjp
composite_vjp
chunked_composite_vjp
```

Every form uses identical detached leaf inputs, local outputs, cotangents, dtype, device, and model state. The snapshot is not updated between forms.

## JAC-01: small materialized oracle

Use a synthetic linear chain of `4` blocks in `R^8`.

For each block:

1. obtain a materialized Jacobian through the registered `torch.autograd.functional.jacobian` or equivalent frozen `torch.func.jacrev` path;
2. calculate explicit reference `J.T @ e`;
3. compare isolated, composite, and chunked-composite VJPs with the explicit reference.

Per confirmatory lane:

```text
3 construction seeds * 4 blocks * 2 candidate comparisons = 24 records
```

## JAC-02: lenet_classic matrix-free snapshot

Use canonical `lenet_classic` with:

```text
model seeds = 0, 1, 2
batch size = 8
input shape = [8, 1, 28, 28]
synthetic deterministic input
targets = [0,1,2,3,4,5,6,7]
6 top-level blocks
```

Synthetic input is built from a fixed `torch.linspace` sequence and does not use a dataset loader.

For every block, deterministic shape-matched cotangents are constructed. Isolated VJP is the matrix-free reference. Composite and chunked-composite forms are compared with it.

Chunk partition is frozen before smoke:

```text
chunk 0 = blocks 0,1,2
chunk 1 = blocks 3,4,5
```

Per confirmatory lane:

```text
3 model seeds * 6 blocks * 2 candidate comparisons = 36 records
```

## Structural diagnostics

For each form, store:

- block count;
- VJP call count;
- input and output shapes;
- cotangent shapes;
- graph-island count;
- allow-unused status;
- missing-gradient count;
- snapshot fingerprint;
- model-state fingerprint;
- RNG fingerprint before and after;
- source commit and image provenance.

Expected:

```text
isolated_vjp calls = number of blocks
composite_vjp calls = 1
chunked_composite_vjp calls = 2
missing-gradient count = 0
snapshot fingerprints identical
model-state fingerprints identical
```

Call count is a structural fact, not evidence of acceleration.

## JAC-C0 volume and pass criteria

Per confirmatory lane:

```text
24 materialized-oracle comparison records
36 lenet matrix-free comparison records
total = 60 block-probe comparison records
```

JAC-C0 passes only when:

- every candidate VJP matches its registered reference;
- implementation-snapshot thresholds pass;
- snapshot and model-state fingerprints agree;
- no gradients are missing;
- the exact VJP call-count contract passes;
- all records are present on both lanes.

JAC-C0 does not compare runtime, memory, saved tensors, or graph lifetime and does not open B2. Those properties belong to separate B1/B2 gates.

# PNZ-L0 — limited parameter control

Use the linear operator:

\[
\widetilde J_\theta=
\begin{bmatrix}
1&0\\
0&1\\
0&0
\end{bmatrix}.
\]

Source:

\[
r=(0,0,\mathrm{scale})^\top.
\]

Expected:

```text
source norm > active_floor
J_theta* r = 0
class = PNZ
operator rank = 2
```

Run `3` PNZ records per confirmatory lane. Publish the result as a limited extension. It does not alter `core_passed`.

# Execution scopes

## Smoke

Smoke runs in controlled Docker CPU and Docker/ROCm lanes after the implementation source commit is frozen.

Per lane:

```text
construction_seed = 0
model_seed = 0
GEO-C0 records = 8
TR-C0 records = 10
TMP-C0 event records = 36
TMP-C0 summary records = 1
JAC-C0 records = 20
PNZ-L0 records = 1
```

Smoke validates schemas, keys, thresholds, device placement, finite values, deterministic replay, and provenance. Smoke results are excluded from confirmatory evidence.

## Confirmatory

Per lane:

```text
construction seeds = 0,1,2
model seeds = 0,1,2
GEO-C0 records = 24
TR-C0 records = 30
TMP-C0 event records = 108
TMP-C0 summary records = 3
JAC-C0 records = 60
PNZ-L0 records = 3
```

Across both lanes:

```text
GEO-C0 records = 48
TR-C0 records = 60
TMP-C0 event records = 216
TMP-C0 summary records = 6
JAC-C0 records = 120
PNZ-L0 records = 6
```

Each registered construction executes once per lane. Re-executing the same construction after inspecting results creates a new evidence version and does not replace the original record.

# Output contract

Before the first controlled smoke run, implementation freezes:

```text
mechanism_geometry_records.csv
mechanism_transport_records.csv
mechanism_temporal_events.csv
mechanism_temporal_summary.csv
mechanism_block_probe_records.csv
mechanism_pnz_records.csv
mechanism_controls_contract.json
mechanism_controls_summary.json
```

`mechanism_controls_summary.json` stores separately:

```text
geo_c0_passed
tr_c0_passed
tmp_c0_passed
jac_c0_passed
core_passed
pnz_l0_passed
si_ma0_open
```

Rule:

```text
si_ma0_open = core_passed
```

# Provenance contract

Every output records:

- full source Git commit;
- source branch;
- controlled image identifier;
- image revision label;
- contract id;
- Torch2PC commit;
- PyTorch version;
- HIP version;
- lane;
- device name;
- dtype;
- CPU thread count;
- visible ROCm devices;
- deterministic-algorithm status;
- model and construction seeds;
- case-registry digest;
- threshold-registry digest.

CPU and ROCm confirmatory outputs must refer to one source commit, contract id, case registry, and threshold registry.

# Pass criteria

The core gate passes only when all conditions hold:

- prerequisites remain checksum-valid;
- implementation schema is frozen before smoke;
- GEO-C0 passes on CPU and ROCm;
- TR-C0 passes on CPU and ROCm;
- TMP-C0 passes on CPU and ROCm;
- JAC-C0 passes on CPU and ROCm;
- every expected record is present;
- record keys are unique;
- all mandatory values are finite;
- the expected-false zero-safe control behaves according to contract;
- source commit and image provenance are verified;
- the test split remains closed;
- confirmatory outputs have `core_passed=true` and `si_ma0_open=true`.

`PNZ-L0` receives its own pass status.

# Stop rules

When a core sub-gate fails:

- set `core_passed=false`;
- set `si_ma0_open=false`;
- retain every record and diagnostic;
- preserve thresholds and construction registry without post-hoc changes;
- investigate the cause in a separate diagnostic commit;
- assign any corrected implementation a new source commit;
- assign any new confirmatory execution a new evidence version.

When only `PNZ-L0` fails:

- preserve the independently calculated core status;
- determine `SI-MA0` access only from core sub-gates;
- keep PNZ claims closed;
- publish the limited-extension failure.

OOM, worker crash, missing record, duplicate key, provenance mismatch, nonfinite value, and unexpected exception create a failed record and close the corresponding sub-gate.

# Supported claim

A positive core gate supports the claim that the registered implementation reproduces analytic correction-geometry and transport mechanisms, the expected FixedPred temporal wave, and equivalence of matrix-free block-VJP forms in the controlled CPU/ROCm deterministic suite.

# Claim boundary

A positive result does not establish:

- empirical prevalence of the mechanisms during real training;
- mechanistic reconstruction of actual `Strict.state_inference`;
- utility of the next exact sweep;
- sufficiency of PC-TREF features;
- acceleration from composite VJP;
- permission for active control;
- transfer to other architectures, precisions, batch sizes, or devices.

# Evidence policy

Working outputs are stored under an ignored `working/` directory. After a successful confirmatory core gate, create a separate immutable package with:

- every raw record;
- CPU and ROCm summaries;
- frozen contract and registries;
- provenance manifests;
- supported claim and claim boundary;
- SHA-256 checksums;
- a separate evidence commit;
- annotated tag `stage3b-a1-mechanism-controls-v1`.

Previously sealed evidence packages remain unchanged.
