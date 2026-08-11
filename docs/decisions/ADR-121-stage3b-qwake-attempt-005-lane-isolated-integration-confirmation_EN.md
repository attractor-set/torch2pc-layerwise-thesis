# ADR-121: lane isolation for Attempt-005 integration confirmation

<!-- LANG-SOURCE: ../../experiments/frozen/stage3b-qwake-attempt-005-lane-isolation-authoring-v1/contract.json -->

Normative terms:
[attempt](../glossary_EN.md#term-attempt),
[execution](../glossary_EN.md#term-execution),
[run](../glossary_EN.md#term-run),
[candidate](../glossary_EN.md#term-candidate),
[runtime](../glossary_EN.md#term-runtime),
[warm-up](../glossary_EN.md#term-warm-up),
[freeze](../glossary_EN.md#term-freeze),
[evidence](../glossary_EN.md#term-evidence),
[test-dataset access](../glossary_EN.md#term-test-dataset-access), and
[dataset](../glossary_EN.md#term-dataset).

## Status

Accepted before Attempt-005 execution. Execution remains closed until the
implementation is merged and a distinct one-shot authorization is issued.

## Context

Attempt-003 completed the full engineering matrix: five of seven CPU aggregates
failed the order-effect gate while all seven ROCm aggregates passed. Attempt-004
applied the CPU stabilization profile process-wide: CPU 0 affinity, one
PyTorch/library thread, and fourteen warm-up cells excluded from the measured
matrix. All seven CPU aggregates then passed, while all seven ROCm aggregates
failed the order-effect gate.

Field-level decomposition showed that the Attempt-004 regression is confined
to ROCm timing fields rather than response correctness, RNG state, reserve
probes, or pair completeness. The CPU correction is therefore validated, but
its scope was too broad: CPU-specific process controls leaked into the
canonical ROCm lane.

The current contract requires one complete successful report over the same
fourteen aggregates. Post-hoc stitching of passing aggregates from separate
attempts is not permitted.

## Decision

Attempt-005 is the single prospective lane-isolated integration confirmation.

One external one-shot run creates two internal processes with no automatic
retry:

1. The CPU process executes only `cpu_float64_engineering`. It preserves the
   validated Attempt-004 profile: CPU 0 affinity, one PyTorch intra-op thread,
   one PyTorch inter-op thread, `OMP/MKL/OPENBLAS/NUMEXPR=1`, and warm-up
   repeats 2 and 3 for each of the seven candidates.
2. The ROCm process executes only `rocm_float32_canonical`. It restores the
   canonical Attempt-003 host-control profile: CPUs 0–7,
   `HIP_VISIBLE_DEVICES=0`, `OMP/MKL/OPENBLAS/NUMEXPR=8`. Symmetric warm-up
   repeats 2 and 3 are executed for every candidate before the measured matrix.
3. Both warm-up sets are excluded from the measured matrix and create no
   reserve probes.
4. The two process results are combined into one result of the original
   matrix: 168 measured cells, 28 reserve probes, and 14 aggregates in the
   original CPU → ROCm order.
5. The combined result is checked by the unchanged `RuntimeMatrixResult.require()`
   and unchanged `validation_passed` conditions.

## Unchanged elements

Exact and Analytic algorithms, the synthetic batch, seeds, 12 measured repeats,
the AB/BA schedule, primary clocks, cost fields, reserve probes, order-effect
tolerances, response/RNG criteria, the generic runtime backend, and the
scientific authorization remain unchanged.

Cross-lane comparison remains forbidden. CPU and ROCm execution profiles are
local to their respective processes.

## Completion criterion

Attempt-005 passes only when its single terminal report contains
`validation_passed=true` and all fourteen aggregates pass the original
order-effect gate. The attempt is one-shot regardless of PASS/FAIL and has no
automatic retry.

Scientific execution, test-dataset access, and publication remain closed.
