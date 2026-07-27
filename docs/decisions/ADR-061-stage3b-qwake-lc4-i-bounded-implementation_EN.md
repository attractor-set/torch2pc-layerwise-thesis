# ADR-061: `QW-LC4-I` bounded implementation

[Russian version](ADR-061-stage3b-qwake-lc4-i-bounded-implementation.md)

- Status: accepted
- Date: July 27, 2026

## Context

The `QW-LC3` repository freeze was merged through PR #122 into `main`
`7c6cbb6ba4941cf78b2bfec3e6e8955c2830a58b` and independently verified. The
validated contract permits authoring one bounded implementation for the
registered `FixedPred`, `eta=1`, `lenet_classic`, `stage2_baseline` domain. It
does not permit a [runtime](../glossary_EN.md#term-runtime) run, [test-dataset access](../glossary_EN.md#term-test-dataset-access), collection of scientific
[evidence](../glossary_EN.md#term-evidence), policy activation, or publication.

The implementation must preserve the separation between the
[required result](../glossary_EN.md#term-required-result) `R`, the
[resource trajectory](../glossary_EN.md#term-resource-trajectory) `Γ`, and the
[cost vector](../glossary_EN.md#term-cost-vector) `C`. Equality or admissibility
under `~R` must not be converted into a cost or deployment claim.

## Decision

1. Materialize module
   `src/torch2pc_thesis/stage3b_qwake_lc4_bounded.py` and freeze its identity in
   `stage3b-qwake-lc4-i-bounded-implementation-v1`.
2. Implement the registered
   [analytic completion](../glossary_EN.md#term-analytic-completion)
   `fixedpred_eta1_wavefront_completion_v1` only. At frontier `S_t`, the
   implementation derives the already completed boundary residual and
   propagates the unfinished lower VJP chain. Its registered VJP count is
   `K_ref - t`; no broader method, step size, [architecture](../glossary_EN.md#term-architecture), or graph claim is
   admitted.
3. Implement the exact [fallback](../glossary_EN.md#term-fallback)
   `complete_suffix_stage2_baseline_v1` as every remaining registered FixedPred
   sweep from a fresh disposable fork. The normal analytic arm never silently
   invokes this path.
4. Bind inputs, targets, model parameters and buffers, fixed predictions,
   decision-epoch beliefs and errors, [endpoint](../glossary_EN.md#term-endpoint) loss, optional update state, and
   deterministic controls into `opaque_state_ref`. Every arm and reserve probe
   receives a new deep fork, while source integrity is rechecked before use.
5. Capture and restore the complete default RNG inventory: Python global,
   NumPy legacy global, Torch CPU default, all visible ROCm device generators,
   and every explicitly registered custom generator. Restore the outer process
   state after each bounded synthetic cell.
6. Materialize the `QW-LC1` canonical response and zero-safe `~R` predicate for
   named parameter gradients, [endpoint](../glossary_EN.md#term-endpoint) beliefs, and endpoint loss.
7. Materialize the `QW-LC2` trajectory-to-cost mapping with interval union,
   digest-based artifact deduplication, peak-memory maxima, observer
   calibration, exact fallback state, and no scalar total.
8. Materialize the twelve-repeat balanced schedule and componentwise paired
   aggregation, including the separate order-effect gate. Repeat exclusion,
   imputation, majority voting, and scalarization remain forbidden.
9. Expose only a synthetic-unit-test permit. The module contains no CLI,
   dataset loader, output writer, runtime authorization reader, or scientific
   executor. A separate `QW-LC4-F` freeze must bind the real source, image,
   adapter, clocks, memory sources, authorization, output root, and [attempt](../glossary_EN.md#term-attempt)
   count before any engineering [execution](../glossary_EN.md#term-execution).

## Consequences

The code is reviewable and unit-testable, but it is not runtime-authorized and
produces no engineering or scientific evidence. Passing synthetic tests shows
only that the bounded implementation obeys its internal contracts on synthetic
states. It does not establish [response equivalence](../glossary_EN.md#term-response-equivalence) on the registered runtime,
cost superiority, safety, coverage, policy quality, or deployment readiness.

After merge and independent post-merge verification, `QW-LC4-I` may be marked
complete and authoring of `QW-LC4-F` may open. Local-compute execution,
scientific execution, feature collection, oracle-label generation, test data,
and publication remain closed.
