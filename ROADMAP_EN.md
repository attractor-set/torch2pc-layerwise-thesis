# Roadmap

[Русская версия](ROADMAP.md)

## Phases 1–5 — complete

1. Research scaffold and preregistration.
2. Controlled environment and 96/96 validation-only pilot.
3. Stage 1 confirmatory campaign, 80/80.
4. Stage 2 implementation study, 80/80.
5. Public release and unauthenticated-access verification.

## Phase 6. Stage 3 design-ready — current

ADR-006/ADR-007, RQ6–RQ10, full Stage 2 baseline hashes, the design YAML, stage
templates, candidate overlays, locality schema, scaling MLP family, deterministic
plan, and readiness gate are present. Test remains disabled.

## Phase 7. Stage 3A baseline profiling

Implement the diagnostics/profiler executor, instrument forward/inference/VJP/
optimizer regions, create the B0 locality/runtime/memory profile, verify that
instrumentation does not perturb results, and apply feasibility stop rules.

## Phase 8. Stage 3B exact candidates

Implement B1 isolated VJP and B2 composite VJP, run CPU float64 and GPU float32
equivalence gates, profile matched candidates, and select at most one exact
candidate for pilot.

## Phase 9. Stage 3C approximations

Implement C1 adaptive stopping and C2 periodic VJP refresh, run alignment and
stability gates, execute the 48-cell parameterized validation-only screening, and select at most
one approximation candidate. C3 fixed random feedback remains conditional.

## Phase 10. Stage 3 freeze and final

Freeze candidates, parameters, and the non-inferiority margin; create Stage 3
environment/control artifacts and `stage3-pilot-freeze-v1`; enable test in a
separate commit; run up to 80 final cells; keep execution and publication states
distinct.

## Phase 11. Analysis and thesis

Complete locality/runtime/memory scaling, robustness and representation analysis,
the thesis chapter and article, the replication bundle, clean-room reproduction,
and the review reserve.
