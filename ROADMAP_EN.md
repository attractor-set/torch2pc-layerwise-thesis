# Roadmap

[Русская версия](ROADMAP.md)

## Phases 1–5 — complete

Research scaffold, controlled environment and 96/96 pilot, Stage 1 80/80,
Stage 2 80/80, and public release are complete.

## Phase 6. Stage 3 design-ready revision 2 — current

ADR-006/007/008, RQ6–RQ11, full Stage 2 hashes, locality/profiling contracts,
the scaling MLP family, exact-shortcut control A0, core approximations C1/C2,
and predict-correct candidates C4/C5 are declared. Test remains disabled.

## Phase 7. Stage 3A profiling

Implement the non-perturbing executor, profile B0/A0, execute 336 matched cells,
and apply feasibility and endpoint-equivalence gates.

## Phase 8. Stage 3B exact candidates

Implement B1/B2, run CPU float64 and GPU float32 full-trajectory gates, perform
attribution, and select at most one exact candidate.

## Phase 9. Stage 3C core approximations

Implement C1/C2, run the 48-cell validation-only pilot, and select at most one
core approximation candidate.

## Phase 10. Stage 3C2 predict-correct screening

Implement C4/C5, run 27 validation-only cells, and apply residual, VJP-reduction,
fallback, and non-inferiority gates. C3H/C6 remain deferred.

## Phase 11. Stage 3 freeze and final

Freeze candidates and parameters, create environment/control artifacts and
`stage3-pilot-freeze-v1`, enable test in a separate commit, run up to 80 final
cells, and keep execution/publication states distinct.

## Phase 12. Analysis and thesis

Complete scaling, robustness, representations, thesis/article writing,
replication bundle, clean-room reproduction, and review reserve.
