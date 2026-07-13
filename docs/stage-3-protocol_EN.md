# Stage 3 protocol: locality, approximation, and scaling

[Русская версия](stage-3-protocol.md)

Status: **design-ready; execution remains blocked until candidate
implementations, numerical gates, and a separate Stage 3 freeze exist**.

## 1. Purpose

Stage 3 is a new campaign. It does not reopen or modify Stage 1 or Stage 2. It
studies the relationship among:

- mathematical layer locality in predictive coding;
- the span of the executed autograd graph;
- VJP calls, synchronization points, and saved tensors;
- runtime, memory, and depth scaling;
- exact and approximate credit-signal computation;
- quality, robustness, and gradient alignment.

Two tracks remain separate:

1. **implementation-preserving:** execution changes while the update equations
   remain fixed;
2. **algorithm-changing approximation:** stopping, linearization refresh, or the
   feedback operator changes.

## 2. Immutable baseline

| Role | Identifier |
|---|---|
| Stage 2 execution source | `6d66b0a6f82c30c4fb8eca6247383ca13e0636a2` |
| Stage 2 publication state | `bb435432a65b76b7fc4f383b566b9a372fc346ae` |
| Stage 2 Torch2PC | `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4` |
| Observed runtime order | `BP ≈ Exact < FixedPred << Strict` |

The execution and publication states remain distinct provenance points. Stage 2
tags are not moved, and Stage 1/2 are not rerun to create Stage 3.

## 3. Research questions

- **RQ6:** What dependency radius, graph span, VJP count, synchronization count,
  and saved-tensor volume occur for each FixedPred and Strict layer update?
- **RQ7:** How do isolated layer graphs and composite VJP change execution
  locality, runtime, and memory while preserving the equations?
- **RQ8:** How does adaptive stopping affect inference steps, alignment, runtime,
  memory, and validation quality?
- **RQ9:** How does periodic or state-triggered VJP refresh interpolate between
  Strict and fixed-linearization behavior?
- **RQ10:** Can a separate local feedback operator reduce cost inside a declared
  non-inferiority margin while its alignment change is reported?

RQ10 is conditional and begins only after the core Stage 3 track is complete.

## 4. Locality profile

No single locality score is used. The report keeps separate dimensions:

- algorithmic inputs required by a layer update;
- dependency radius in the layer graph;
- autograd graph modules and graph span;
- independent construction/execution/release of local graphs;
- exact, reused, or approximate feedback;
- sequential, synchronous, or barrier-based orchestration.

For mathematically local PC events, the structural gate is
`dependency_radius <= 1`. Graph span is reported separately because a composite
implementation may execute a wider graph without changing the local equations.

## 5. Candidates

| ID | Track | Methods | Initial status |
|---|---|---|---|
| `stage2_baseline` | baseline | FixedPred, Strict | available |
| `isolated_layer_vjp` | implementation-preserving | FixedPred, Strict | planned |
| `composite_vjp` | implementation-preserving | FixedPred, Strict | planned |
| `adaptive_stopping` | approximation | FixedPred, Strict | planned |
| `periodic_vjp_refresh` | approximation | Strict | planned |
| `fixed_random_feedback` | approximation | Strict | deferred |

B1 isolates detached layer-local graphs. B2 groups mathematically local VJPs into
fewer autograd invocations. C1 introduces a residual-based stopping rule. C2
refreshes Strict pullbacks at intervals `1, 2, 5, 20` or by a state trigger. C3
uses a separate feedback operator and has no Stage 2 equivalence claim.

## 6. Phases

### Stage 3A — baseline audit and profiling

Instrument:

- `initial_forward`;
- `state_inference`;
- `local_state_vjp`;
- `parameter_vjp`;
- `optimizer_step`.

Record CPU/device time, VJP calls, synchronization points, saved-tensor bytes,
peak memory, dependency radius, graph span, and actual inference iterations.

### Stage 3B — exact implementation candidates

Implement and gate B1 first, then B2. Run CPU float64 and GPU float32
comparisons for beliefs, errors, state updates, gradients, and one optimizer
step. Profile B0/B1/B2 in randomized back-to-back blocks.

### Stage 3C — approximations

Implement C1, then C2. C3 is a separate conditional exploratory track.
Approximation candidates use alignment and non-inferiority gates rather than an
equivalence claim.

### Stage 3D — scaling

The controlled model family contains depths `4, 8, 16, 32`, widths `64, 256`,
and names such as `mlp_d16_w256`.

## 7. Profiling design

```text
2 methods
x 3 exact candidates
x 4 depths
x 2 widths
x 2 batch sizes
x 3 seeds
= 288 profiling cells
```

Each cell is a short benchmark: 20 warm-up steps, 50 measured steps, five
repetitions, explicit synchronization, and randomized matched ordering.

## 8. Validation-only pilot

The screening phase expands approximation parameters before they are frozen:

```text
B0/B1/B2 defaults:
  3 candidates x 2 methods x 3 seeds = 18 cells
C1 adaptive stopping:
  3 tolerances x 2 methods x 3 seeds = 18 cells
C2 periodic refresh:
  4 intervals x Strict x 3 seeds = 12 cells
Total = 48 validation-only terminal cells
```

C1 uses tolerances `1e-2`, `5e-3`, and `1e-3`; maximum steps are 10 for
FixedPred and 20 for Strict. C2 uses intervals `1, 2, 5, 20`. Every plan cell
contains a `variant_id` and complete parameters so the selection remains
reproducible.

The pilot does not construct a test loader. It selects one exact and one
approximate candidate, estimates validation variability, chooses stopping and
refresh parameters, and fixes the non-inferiority rule. MNIST and test are not
used for candidate selection.

## 9. Final template

Before freeze:

```yaml
evaluation:
  use_test: false
protocol:
  status: blocked_until_stage3_freeze
```

The planned frozen design is:

```text
2 datasets x applicable candidate-method pairs x 10 seeds = at most 80 cells
```

One candidate is implementation-preserving and one is approximate. If
`periodic_vjp_refresh` is selected, it applies only to Strict, yielding 60
cells: 40 for the exact candidate and 20 for the approximation. If no
approximation passes the pilot gates, the final campaign is reduced to the
40-cell exact candidate and the decision is recorded before any Stage 3 test
access.

## 10. Gates

### Exact implementation gates

Compare beliefs, prediction errors, state updates, parameter gradients, and one
optimizer step. Initial thresholds preserve the Stage 2 scope:

| Device | dtype | min cosine | max relative L2 |
|---|---|---:|---:|
| CPU | float64 | 0.99999 | `1e-7` |
| GPU | float32 | 0.999 | `1e-3` |

### Approximation gates

Report per-layer cosine, relative L2, sign agreement, residuals, iteration/VJP
reduction, validation macro F1, seed variation, and non-finite events. The
non-inferiority margin is fixed from Stage 2 variability and the Stage 3 pilot,
not after Stage 3 test access.

### Engineering continuation gates

- FixedPred speedup: at least 15%;
- Strict speedup: at least 20%;
- baseline timing regression: at most 3%;
- peak-memory growth: at most 15% without a separate rationale.

These thresholds govern engineering continuation and do not by themselves form
a superiority claim.

## 11. Stop rules

Stop a candidate when the optimizable region is below 20% of runtime, the Amdahl
upper bound is below the declared threshold, exact gates fail, non-finite values
appear, or an approximation misses the validation non-inferiority rule. Negative
outcomes remain in the registry and report.

## 12. Test access and provenance

Profiling, pilot, and the current final template all keep test disabled. Test is
enabled only in a separate commit after `stage3-pilot-freeze-v1`. Planned tags:

- `stage3-design-v1`;
- `stage3-pilot-freeze-v1`;
- `stage3-execution-v1`;
- `stage3-results-v1`.

Execution and publication states remain separate commits.

## 13. Twelve-month schedule

| Period | Deliverable |
|---|---|
| Months 1–2 | literature update, RQs/ADRs, design freeze, profiling executor |
| Months 3–4 | B0 audit, locality traces, scaling baseline |
| Months 5–6 | B1/B2 and exact gates |
| Month 7 | C1/C2 and validation-only pilot |
| Month 8 | candidate freeze and core final execution |
| Month 9 | conditional C3 go/no-go |
| Month 10 | robustness, representations, and scaling analysis |
| Month 11 | thesis chapter, article, replication bundle |
| Month 12 | clean-room reproduction, review corrections, reserve |

## 14. Current readiness definition

The repository is ready for Stage 3 implementation when the design, ADRs,
full baseline hashes, locality schema, scaling models, deterministic design
plan, and execution guards are present. The locality schema lives in
`src/torch2pc_thesis/locality.py`; measured region names, timing summaries, and
Amdahl feasibility calculations are fixed in
`src/torch2pc_thesis/profiling.py`. This is not pilot/final readiness: candidate
commits, environment locks, numerical gates, and freeze artifacts are still
required.
