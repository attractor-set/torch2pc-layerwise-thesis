# Analysis plan

[Русская версия](analysis-plan.md)

## Principles

Analysis begins only after a frozen protocol and provenance check. The primary
inference level is `model_seed`. Signed outcomes are retained; values are not
clipped at zero, inconvenient seeds are not excluded post hoc, and exploratory
results remain separate from confirmatory results.

## Completed analyses

- Stage 1/2: quality, time, and method comparability;
- Stage 3A: gradient cosine, relative L2, norm ratio, sign agreement, CKA, RSA,
  cross-layer CKA, and depth statistics;
- Stage 3B B0: matched time/memory, region attribution, and [saved tensors](glossary_EN.md#term-saved-tensors);
- `SI-MA0`: reconstruction, observer, version, cost, and comparison gates;
- `SI-MA1`: observer-calibrated closure with bootstrap by `model_seed`.

`SI-MA0` and `SI-MA1` are analyzed as sequential, separate experiments. The
first result is not replaced by the second.

## Operational theoretical definitions

An exact [diagnostic quotient](glossary_EN.md#term-diagnostic-quotient) requires a partition map $q_I$. Continuous
features may use
[operational diagnostic indistinguishability](glossary_EN.md#term-operational-diagnostic-indistinguishability),
but transitivity is not assumed. Safety is evaluated through
[decision regret](glossary_EN.md#term-decision-regret), dangerous misses, and
[fallback](glossary_EN.md#term-fallback), not literal feature equality.

Every norm and [precision-masked zero](glossary_EN.md#term-precision-masked-zero)
has a registered measurement contract. Layer/time aggregation occurs only
after authorized normalization.

## B1/B2 analysis preregistration

B1 and B2 separately freeze:

- [candidate](glossary_EN.md#term-candidate)/reference pair and scope;
- primary numerical-equivalence [endpoint](glossary_EN.md#term-endpoint);
- absolute and/or relative tolerance with a zero-denominator rule;
- safety endpoint, $\delta_R$, and allowed dangerous-miss rate;
- independent unit `model_seed` and nesting;
- [execution](glossary_EN.md#term-execution) matrix, order balancing, and replacement policy;
- the [cost vector](glossary_EN.md#term-cost-vector);
- scalarization or [Pareto admissibility](glossary_EN.md#term-pareto-admissibility);
- multiplicity, bootstrap/random seed, replication count, and decision rule;
- stop/fallback rules and conditions for opening full [profiling](glossary_EN.md#term-profiling).

## Primary candidate gates

1. **NUM-B1/B2:** candidate matches the frozen reference within registered
   numerical tolerances.
2. **STATE:** state, beliefs, and RNG are restored before matched arms.
3. **SAFETY:** regret/dangerous-miss stays within the registered limit.
4. **COST:** benefit persists after separate diagnostic-mechanism, observer,
   control-plane, and fallback accounting.
5. **CMP:** cardinality, provenance, manifests, and planned comparisons are
   complete.

Failure of numerical equivalence or safety closes the candidate to confirmatory
profiling. Failure of cost remains a scientific result but does not support a
speedup claim.

## Future policy analysis after `EX-IF0`

Before `EX-IF0`, `ECZ` remains a passive diagnostic category and cannot control
execution. After the exact implementation is frozen, a separate
development-only counterfactual analysis is permitted. The [baseline](glossary_EN.md#term-baseline)
`stop`/`native_one`/`exact_one` branches retain their B1/B2-contract meaning as
offline labels. Exact reference separately creates oracle skip regret and
oracle margin $M^*$; pre-action estimator $\widehat M_b$ is evaluated as a
predictor of that label under
[`PC-TREF-SB`](pc-tref-sufficiency-boundary_EN.md), rather than being defined
through its own prediction.

A `local_sweep(block_id)` branch may appear only in a new preregistered
protocol. `ECZ` selects a candidate block but does not establish local-action
utility. Before a local sweep enters a policy family, it must pass an
`exact_verification` gate:

```text
same restored state
→ proposed local_sweep(block_id)
→ full_exact
→ endpoint utility/regret comparison
```

Offline selection follows a fixed sequence:

1. `cost_feasibility`;
2. `safety` with `zero_dangerous_misses`;
3. `net_efficiency` over the complete cost vector;
4. Pareto screening with `0–3` finalists.

A result of `0` viable policies is a valid scientific result. Finalists,
representation, features, split, thresholds, fallback, and hysteresis are
frozen before confirmatory shadow evaluation. Active control is forbidden
until positive shadow [evidence](glossary_EN.md#term-evidence); `A-Max` is considered only as a conditional
extension.

Normative documents:
[QWake-PC](glossary_EN.md#term-qwake-pc) — [QWake-PC design](qwake-pc-design_EN.md),
[ECZ-targeted local sweep](ecz-targeted-local-sweep_EN.md), and
[future-policy boundary](stage3b-future-policy-boundary_EN.md).

## Secondary analyses

- layer, [dataset](glossary_EN.md#term-dataset), method, and seed heterogeneity;
- sensitivity to prespecified norm/threshold variants;
- order and thermal effects;
- descriptive relation between PC-CATM features and candidate error;
- regret–cost frontier across registered representations;
- fallback frequency and tail latency.

Secondary analyses do not alter the primary decision.

## B1/B2 matched profiling: post-collection/pre-analysis freeze

After the 288-cell campaign and before comparative result computation, the
project freezes a separate
[`STAGE3B-MATCHED-DESCRIPTIVE-ANALYSIS_EN.md`](https://github.com/attractor-set/torch2pc-layerwise-thesis/blob/main/experiments/planned/STAGE3B-MATCHED-DESCRIPTIVE-ANALYSIS_EN.md)
protocol. It binds analysis to the immutable evidence tag, retains `model_seed`
as the independent unit, and fixes estimands, aggregation, a seven-dimensional
Pareto rule, continuation thresholds, and `retain / conditional /
reject_or_revise` decisions. This is a post-collection/pre-analysis freeze, not
a preregistration made before data collection. After implementation and hardening, a separate
[execution request](https://github.com/attractor-set/torch2pc-layerwise-thesis/blob/main/experiments/planned/STAGE3B-MATCHED-DESCRIPTIVE-ANALYSIS-EXECUTION-REQUEST_EN.md)
binds one read-only run, immutable inputs, the analysis core, one new output
root, and the exact 18-file inventory. The request is not authorization and
does not open result computation. The implemented [runtime](glossary_EN.md#term-runtime) [preflight layer](https://github.com/attractor-set/torch2pc-layerwise-thesis/blob/main/experiments/planned/STAGE3B-MATCHED-DESCRIPTIVE-ANALYSIS-RUNTIME-PREFLIGHT_EN.md) checks only identities and structural integrity; the actual runtime preflight and a separate [authorization](https://github.com/attractor-set/torch2pc-layerwise-thesis/blob/main/experiments/planned/STAGE3B-MATCHED-DESCRIPTIVE-ANALYSIS-EXECUTION-AUTHORIZATION_EN.md) are frozen. Authorization permits one future read-only [attempt](glossary_EN.md#term-attempt) but does not claim execution or open publication.

## Completeness and publication

Publish raw retained attempts, compact derived tables, machine-readable
summary/decision, bilingual report, environment record, and `SHA256SUMS`.
Aggregation does not modify raw [evidence](glossary_EN.md#term-evidence). The test split is not used before a
separate final-evaluation contract.
