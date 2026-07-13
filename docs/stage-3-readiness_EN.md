# Stage 3 readiness

[Русская версия](stage-3-readiness.md)

## Status meaning

`ready_for_stage3_implementation` means that implementation can start without
changing Stage 1/2. It does not authorize pilot or final execution.

`blocked_until_candidates_and_freeze` means that Stage 3 training stages remain
intentionally absent from `TRAINING_STAGES`.

## Checks

```bash
PYTHONPATH=src python scripts/check_stage3_readiness.py
PYTHONPATH=src python -m torch2pc_thesis.cli stage3-check
PYTHONPATH=src python scripts/generate_stage3_design_plan.py
```

Expected output includes 288 profiling cells, 48 parameterized validation-only screening cells,
and a final template blocked until Stage 3 freeze.

## Profiling execution prerequisites

A profiling executor, non-perturbing B0 instrumentation, a pinned source commit,
a new environment lock, trace-schema checks, and a warmup/synchronization smoke
run are required.

## Pilot prerequisites

B1/B2/C1/C2 require separate Torch2PC commits. Exact candidates require CPU/GPU
equivalence gates; approximation candidates require finite/stability gates. The
profiling report and frozen validation-only pilot plan must exist, and no test
loader may be constructed.

## Final prerequisites

Select one exact and at most one approximate candidate from validation only,
freeze their parameters and the non-inferiority margin, create the Stage 3
environment and control artifacts, create a `stage3-pilot-freeze` manifest/tag,
and enable final execution in a separate commit. The execution and later
publication states remain distinct.
