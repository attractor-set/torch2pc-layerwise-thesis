# Stage 3B B1: `isolated_layer_vjp` candidate contract

[Русская версия](STAGE3B-B1.md)

## Status and scope

This document preregisters B1 as an opt-in, implementation-preserving exact
candidate. Implementation, execution, and results are absent. The reference is
the frozen `stage2_baseline`; B0, `SI-MA0`, `SI-MA1`, and the theory tag remain
unchanged.

## Structural contract

B1 creates a separate VJP graph for every logical upper-state edge. Layer update
order, state versions, the parameter-VJP path, and `FixedPred`/`Strict`
semantics must match the reference. Delegation to the reference VJP helper or
`loss.backward()` is forbidden so the candidate remains structurally testable.

## Equivalence and safety

Every pair starts from one snapshot with restored parameters, optimizer,
beliefs, batch, and RNG. The full sequence of beliefs and errors across sweeps,
endpoint loss, and parameter gradients are compared. Norms and numerical
thresholds are frozen in `STAGE3B-B1-CONTRACT.json`.

Smoke contains 12 matched pairs; confirmatory equivalence contains 120. Zero
dangerous admissions are permitted. Runtime or memory benefit cannot compensate
for structural, numerical, trajectory, provenance, or finite-value failure.

## Profiling and cost

Only a positive `EQ-B1` may admit the candidate to the registered 96-cell
ROCm/float32 matrix. Primary timing uses `no_hooks`; structural counters use a
separate `counters_only` lane. Observer cost is reported separately and is not
subtracted from primary timing. Scientific selection requires full
admissibility first and then Pareto admissibility over the complete cost vector.

## Boundary to future policy

B1 contains no estimator, oracle branching, cheap diagnostic loop, hysteresis,
or offline policy selection. A positive `EQ-B1` only makes the candidate
eligible for future `EX-IF0`; it does not authorize control of exact-sweep count.

After `EX-IF0`, the permitted sequence is `A11-OFF0`, `A11-OFF1`, separate
predictor preregistration, and shadow `QWake-PC`. The
`stop`/`native_one`/`exact_one` labels identify counterfactual offline-dataset
branches and are not B1 actions.

## Claim boundary

A positive `EQ-B1` establishes equivalence only in the registered scope. It
does not establish runtime or memory benefit, full training-trajectory
equivalence, active `QWake-PC` safety, estimator validity, hysteresis safety, or
generalization beyond the pinned implementation and environment.
