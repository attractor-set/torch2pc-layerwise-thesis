# Stage 3 readiness

[Русская версия](stage-3-readiness.md)

## Status meaning

`ready_for_stage3_implementation` authorizes implementation, not pilot/final.
`blocked_until_candidates_and_freeze` keeps Stage 3 out of `TRAINING_STAGES` and
test disabled.

## Checks

```bash
PYTHONPATH=src python scripts/check_stage3_readiness.py
PYTHONPATH=src python -m torch2pc_thesis.cli stage3-check
PYTHONPATH=src python scripts/generate_stage3_design_plan.py
```

Expected: design revision 2, 336 [profiling](glossary_EN.md#term-profiling) cells, 48 core validation-only pilot
cells, 27 predict-correct screening cells, and final blocked until freeze.

## Profiling prerequisites

Require the profiler executor, non-perturbing B0 instrumentation, A0 [endpoint](glossary_EN.md#term-endpoint)
control, pinned source, environment lock, and warmup/synchronization smoke.

## Core-pilot prerequisites

B1/B2/C1/C2 require separate commits. B1/B2 require full-trajectory CPU/GPU
gates, A0 requires an [endpoint](glossary_EN.md#term-endpoint) gate, and C1/C2 require finite/stability gates.
No test loader may be constructed.

## Accelerator-screening prerequisites

The core-pilot selection artifact must be frozen; C4/C5 need separate commits,
at least one exact correction, tested Strict [fallback](glossary_EN.md#term-fallback), residual/VJP/[fallback](glossary_EN.md#term-fallback)
telemetry, a screening environment lock, and no test loader.

## Final prerequisites

Select one exact and at most one approximation [candidate](glossary_EN.md#term-candidate), freeze parameters and
the margin, create `stage3-pilot-freeze`, and enable final in a separate commit.
[Execution](glossary_EN.md#term-execution) and publication states remain distinct.


## Practical interpretation

A successful readiness check means that the researcher may begin implementing
the profiler according to the pinned design. It does not establish [candidate](glossary_EN.md#term-candidate)
efficiency and does not create experimental data. Any mismatch in structure,
[configuration](glossary_EN.md#term-configuration), or guard rules must be resolved before [execution](glossary_EN.md#term-execution) so that later
results remain reproducible and auditable.
