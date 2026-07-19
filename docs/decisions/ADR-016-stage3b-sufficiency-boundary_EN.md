# ADR-016: operational sufficiency boundary after `EX-IF0`

[Русская версия](ADR-016-stage3b-sufficiency-boundary.md)

- Status: accepted as a design-only theoretical decision
- Date: 2026-07-19

## Context

`ADR-013` froze operational `PC-TREF` semantics,
[required equivalence](../glossary_EN.md#term-required-equivalence), regret,
norms, and cost. B1/B2 are frozen separately and define no estimator, oracle,
hysteresis, or policy. Continued work after `EX-IF0` requires separation of the
post-action ground-truth skip-safety label from the diagnostic estimate
available before the action.

Without this separation, a sufficiency-margin definition would be circular,
while normal and horizon concepts could silently assume smoothness and
coordinate invariance that have not been established.

## Decision

1. Introduce a one-step [operational sufficiency boundary](../glossary_EN.md#term-operational-sufficiency-boundary) only for
   `state_inference` and the registered action space.
2. Qualify $r_\Gamma$ as exact-reference regret or exact-reference defect; it
   equals classical [decision regret](../glossary_EN.md#term-decision-regret) only when the exact action realizes the
   registered $V^*$.
3. Define oracle skip quantity $r_{\mathrm{skip}}^*$ through exact reference and
   oracle margin $M^*=\varepsilon_R-r_{\mathrm{skip}}^*$.
4. Define pre-action estimator $\widehat M_b=g_b(\phi_b(x))$ as a separate
   object trained and evaluated without test leakage.
5. Separate equal-safety-admissibility equivalence from full required
   equivalence; the latter uses a separately registered $q_R$ that includes the
   Pareto set or tie-break whenever the claim requires it.
6. Treat $\{M^*=0\}$ as an operational threshold level set rather than
   automatically as the topological boundary of the safe region.
7. Require an uncertainty interval, separate coverage validation, and
   `abstained`/`fallback_exact` when that interval crosses the boundary.
8. Call $\widehat H^{(1)}$ only a first-order predicted horizon rather than a
   certified count of safe skips.
9. Permit a normal and cosine only as a conditional geometric extension under
   a registered surrogate, regularity condition, and metric.
10. Do not interpret tangential motion as proven task equivalence.
11. Use ECZ-protected absolute activity only for frozen canonical channels.
12. Apply the regret safety constraint first, then select under the full cost
    vector and preregistered Pareto rule.
13. Treat an observed zero `dangerous_miss` count only as an empirical result
    requiring a preregistered upper confidence bound for the miss probability.
14. Preserve the sequence `EX-IF0` → policy-neutral oracle labels → passive
    features → offline validation → preregistration → shadow → conditional
    active mode.

## Consequences

- B1/B2, `ADR-014`, `ADR-015`, frozen contracts, and [evidence](../glossary_EN.md#term-evidence) remain unchanged;
- the new theory grants no `action_permission` and authorizes neither
  measurement nor active control;
- one-step safety and trajectory-level safety remain distinct objects;
- the parameter-learning boundary remains outside mandatory master's scope;
- a negative estimator or horizon result remains a valid scientific result.

## Claim boundary

The decision permits preparation of a separate `PC-TREF-SB` preregistration
after `EX-IF0`. It does not establish a smooth boundary, utility of geometric
features, compute savings, or active-policy safety.
