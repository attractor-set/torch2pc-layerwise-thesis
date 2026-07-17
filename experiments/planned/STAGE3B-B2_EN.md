# Stage 3B B2: `composite_vjp` candidate contract

[Русская версия](STAGE3B-B2.md)

## Status and prerequisite

B2 is preregistered only as `composite_vjp`. B2 implementation remains closed
until sealed `EQ-B1`. Automatic fallback to `block_composite_vjp` or
`chunked_composite_vjp` is forbidden and requires a new protocol.

## Structural contract

B2 performs exactly one composite state VJP per inference sweep and covers all
registered logical upper-state edges. Per-layer state-VJP calls inside the
candidate are forbidden. Update order, state versions, and the parameter-VJP
path must match `stage2_baseline`.

## Trajectory and direct B1/B2 control

Every matched `stage2_baseline`/B1/B2 triple is restored from one snapshot.
Smoke contains 12 triples and 24 pairwise comparisons; confirmatory equivalence
contains 120 triples and 240 comparisons. `EQ-B2` requires both B2-to-baseline
agreement and direct B2-to-admitted-B1 agreement. Any B1/B2 disagreement blocks
B2 independently of potential speedup.

## Profiling and cost

After `EQ-B1` and `EQ-B2`, B2 enters the same 96-cell ROCm/float32 matrix.
Primary timing uses `no_hooks`, the structural lane uses `counters_only`, and
observer cost is reported separately. Exact-implementation selection is
deferred to separate `EX-IF0` and applies safety/numerical admissibility before
the Pareto rule.

## Boundary to future policy

B2 contains no estimator, oracle branching, cheap diagnostic loop, hysteresis,
or offline policy selection. A positive `EQ-B2` only permits B2 to be considered
by separate `EX-IF0`; it does not authorize adaptive stopping, wake-up, or
sweep-budget allocation.

After `EX-IF0`, policy work proceeds through `A11-OFF0`, `A11-OFF1`, separate
predictor preregistration, and shadow `QWake-PC`. Counterfactual
`stop`/`native_one`/`exact_one` labels remain offline branch labels rather than
B2 actions.

## Claim boundary

A positive `EQ-B2` does not establish superiority over B1, runtime or memory
benefit, transfer to other architectures, controller suitability, hysteresis
safety, or safety of skipping full sweeps.
