# ADR-119: CPU measurement stabilization for Attempt-004

Normative terms:
[attempt](../glossary_EN.md#term-attempt),
[execution](../glossary_EN.md#term-execution),
[candidate](../glossary_EN.md#term-candidate),
[runtime](../glossary_EN.md#term-runtime),
[warm-up](../glossary_EN.md#term-warm-up),
[freeze](../glossary_EN.md#term-freeze),
[evidence](../glossary_EN.md#term-evidence), and
[dataset](../glossary_EN.md#term-dataset).

## Status

Accepted for implementation authoring. This decision does not authorize
Attempt-004 execution.

## Context

Attempt-003 completed all 168 matched cells and 28 reserve probes. Response
comparison, RNG-state checks, reserve probes, and every ROCm order-effect gate
passed. Engineering validation remained negative only for the CPU
`compute_primary_time_ns` field.

The subsequent read-only audit showed that CPU primary time is measured with
`time.process_time_ns()` while Attempt-003 ran with eight CPU threads.
Retroactively changing Attempt-003 evidence or its tolerance is forbidden.

The generic runtime backend is already bound by SHA-256 into historical
execution freezes and authorizations. Mutating that file for a new attempt is
therefore also forbidden.

## Decision

Attempt-004 adds a separate matrix-executor wrapper and leaves the generic
runtime backend byte-for-byte unchanged.

Before the measured matrix, the wrapper requires:

- process affinity exactly on CPU 0;
- `OMP_NUM_THREADS=1`;
- `MKL_NUM_THREADS=1`;
- `OPENBLAS_NUM_THREADS=1`;
- `NUMEXPR_NUM_THREADS=1`;
- PyTorch intra-op threads = 1;
- PyTorch inter-op threads = 1.

It then executes two discarded matched warm-up cells for each of the seven CPU
candidates: canonical repeat 2 followed by canonical repeat 3. These repeats
have opposite arm orders and contain no reserve probes. Their temporary
records are discarded and are excluded from the measured matrix and
aggregates.

After warm-up, the wrapper delegates to the unchanged generic
`BoundedTorchMatrixExecutor`, which executes the original twelve measured
pairs per candidate. Algorithms, candidates, measured pair schedule, CPU
primary clock, and order-effect tolerance remain unchanged.

## Boundary

This slice only implements and validates the separate wrapper. Historical
freezes, authorizations, and registries are unchanged. Docker is not invoked,
model code is not executed, no dataset is read, no authorization is consumed,
and no execution lease is created. Scientific execution remains closed.
