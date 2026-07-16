# Analysis pre-specification

[Русская версия](PREREGISTRATION.md)

Status: **pre-specified before pilot execution and before final-test access**.
Later changes require a timestamped ADR stating the reason and affected claims.
Changes after final-test access are exploratory and do not replace the original
confirmatory analysis.

## Statistical unit and primary design

The statistical unit is an independently trained model identified by a unique
`model_seed`. FashionMNIST is primary, MNIST is secondary, `lenet_classic` is
the primary architecture, macro F1 is the primary metric, and the primary
contrasts are FixedPred vs BP and Strict vs BP. Exact is retained as a technical
control and secondary comparison.

## Number of replications

The initial minimum is ten complete pairs, seeds 0-9. Before final-test access,
the number may only increase according to a pre-specified advisory precision
rule. For each primary contrast, the standard deviation of the paired pilot
validation macro-F1 difference is estimated from three pilot seeds. The
advisory number is `ceil((1.96 * SD / 0.01)^2)`, bounded to 10-30; the maximum
across the two contrasts is used. This validation-based planning estimate does not guarantee statistical power.

## Test access and equivalence

Correctness, smoke, and pilot do not construct a test loader. Final test is
accessed only after `pilot-freeze`. The absolute equivalence margin is fixed
before pilot at 0.01 macro-F1 units. Equivalence is recorded only with at least
ten complete pairs and a 90% confidence interval fully inside
`[-0.01, 0.01]`. A non-significant difference is not treated as equivalence.

## Difference analysis

Each primary contrast reports seed-level values, mean paired difference, 95%
CI, Cohen dz, an exact sign-flip test for at most 20 non-zero pairs, the declared
Wilcoxon approximation above that size, and Holm correction across the two
primary contrasts. With fewer than ten complete pairs, estimates remain
descriptive and no confirmatory equivalence conclusion is produced.

## Failed attempts and pilot selection

Success rate uses the first terminal attempt for each configuration/seed. A
later successful rerun does not erase an initial failure and is not counted as
an independent replication. FixedPred and Strict are ranked using FashionMNIST
validation only, in this order: 1. success rate; 2. mean validation macro F1;
3. mean measured training epoch time; 4. inference steps; 5. eta. MNIST is
descriptive for selection.

Before final execution, `pilot-freeze_manifest.json` records the source commit,
the SHA-256 environment-lock hash, selected parameters, and SHA-256 hashes of
the governing configuration and analysis documents.


## Stage 3 addendum

The specification above belongs to completed Stage 1/2 and is not rewritten.
Stage 3 receives a separate protocol and freeze. Profiling and pilot do not
construct a test loader. Exact implementation candidates require equivalence
gates; approximation candidates use a separate non-inferiority rule and have no
Stage 2 equivalence claim. Candidate selection, stopping tolerance, refresh
interval, predict-correct correction budget, EMA/secant parameters, fallback
rule, and the margin are frozen before Stage 3 test access. A0 uses a separate
endpoint-equivalence gate; C4/C5 require at least one exact correction and a
reported fallback rate.


## Amendment: primary post-B0 working Scenario A

This amendment is design-only and adopts PC-TREF Balanced Core as the upper-level framework and PC-CATM as the mechanism model. It freezes future ordering but does not authorize
confirmatory execution. Normative documents are:

- `docs/pc-tref-balanced-core_EN.md`;
- `docs/pc-catm-operator-model_EN.md`;
- `docs/masters-thesis-plan_EN.md`;
- `docs/stage3b-primary-scenario-a_EN.md`;
- `docs/decisions/ADR-012-pc-tref-pc-catm-scenario-a_EN.md`.

Required order: shortcut and temporal controls; observer non-interference and
overhead; deterministic controls; SI-MA0; candidate-specific B1/B2; EX-IF0;
passive diagnostics; predictor; counterfactual exact verification; shadow
QWake-PC; active control only at full-sweep granularity after a separate
authorization decision.

The independent statistical unit is `model_seed`. Thresholds, features, model
splits, endpoint-gradient utility, dangerous-miss limit, and exact fallback
rules must be frozen before test access. PNZ and the parameter tangent kernel
are outside mandatory confirmatory execution.

## Post-`SI-MA1` amendment: B1/B2 preregistration conditions

This amendment does not rewrite the original Stage 1/2 specification, the
Stage 3 addendum, the design-only Scenario A ordering, or the B0, `SI-MA0`, and
`SI-MA1` contracts or results. The final `SI-MA1` result is frozen by tag
`stage3b-si-ma1-confirmatory-v1`: `CAL-COST-MA1` passed, while future `ECZ`
evaluator and action-selection cost was excluded.

The normative documents for the next step are:

- [`PC-TREF`/`PC-CATM` theoretical foundation after `SI-MA1`](docs/pc-tref-pc-catm-theoretical-foundation_EN.md);
- [`PC-TREF` Balanced Core](docs/pc-tref-balanced-core_EN.md);
- [`PC-CATM` operator model](docs/pc-catm-operator-model_EN.md);
- [ADR-013](docs/decisions/ADR-013-pc-tref-operational-semantics_EN.md);
- [primary Scenario A plan](docs/stage3b-primary-scenario-a_EN.md).

After publication of the theoretical package, preparation of separate B1 and
B2 preregistrations is permitted. Implementation and confirmatory execution of
each candidate remain closed until its own contract, preregistration tag, and
authorization decision are published.

Before implementation and test access, every candidate-specific contract must
freeze:

- an exact diagnostic partition map $q_I$, or an explicitly nontransitive
  operational-proximity rule with its metric, normalization, and tolerance;
- a decision-class map $q_R$, action space, primary outcome,
  [decision regret](docs/glossary_EN.md#term-decision-regret), regret tolerance,
  and dangerous-miss limit;
- norm measurement contracts covering the space, norm, scale, `epsilon`,
  threshold, layer, step, and aggregation rule;
- the [cost vector](docs/glossary_EN.md#term-cost-vector), units for every
  component, and a prespecified scalarization or
  [Pareto admissibility](docs/glossary_EN.md#term-pareto-admissibility);
- separate accounting for [diagnostic-mechanism cost](docs/glossary_EN.md#term-diagnostic-mechanism-cost),
  [observer cost](docs/glossary_EN.md#term-observer-cost),
  [control-plane cost](docs/glossary_EN.md#term-control-plane-cost), and
  fallback;
- candidate equations and code path, restoration of state, beliefs, and RNG,
  the numerical-equivalence or non-inferiority gate, and fallback validation;
- the independent `model_seed` unit, execution matrix, replacement policy,
  provenance, append-only ledger, evidence layout, and stopping rules;
- a closed test loader until the corresponding freeze.

A negative `D_seed` or `SI-MA1` over-closure remains a signed
observer-calibration result and is not interpreted as negative physical cost,
end-to-end acceleration, or a budget for the future control plane.
