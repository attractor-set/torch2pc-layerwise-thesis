# `DONE / UNKNOWN / SWEEP` metric registry

[Русская версия](fixedpred-sufficiency-dus-metrics.md)

**Status:** planned registry; no results are claimed.

## Document purpose

The registry is hierarchical rather than a single aggregate score. Safety and
non-interference are checked first, safe recognition is evaluated second, and
diagnostic and avoided-compute costs are compared only after admission.

`UNKNOWN` is treated as a separate scientific object so that computational
insufficiency can be distinguished from the inability of a low-cost passive
representation to recognize an already sufficient state. `SWEEP` reasons also
remain separate.

## 1. Lexicographic order

$\text{safety} \rightarrow \text{coverage} \rightarrow \text{cost}.$

Cost savings cannot offset a safety failure.

## 2. Hard invariants

```text
invariant_violations=0
post_action_feature_leakage=0
observer_interference_events=0
budget_overspend_events=0
post_terminal_acquisition_events=0
duplicate_acquisition_events=0
invalid_done_permissions=0
oracle_used_as_feature=0
controls_execution=false
test_dataset_access=false
```

## 3. `DONE` metrics

[Dangerous DONE](glossary_EN.md#term-dangerous-done):

$N_{\mathrm{dangerous\ D}} = \#\{A_t=D\land O_t=0\}.$

Selective risk:

$R_D= \frac{N_{\mathrm{dangerous\ D}}} {\max(\#\{A_t=D\},1)}.$

Safe coverage:

$C_D^{\mathrm{safe}} = \frac{\#\{A_t=D\land O_t=1\}}{N}.$

Also report the risk–coverage curve, coverage under the registered risk bound,
a risk upper confidence bound, recognition delay
\(\Delta t_D=t_D-t^*\), and missed early opportunities.

## 4. `UNKNOWN` metrics

[Diagnostic observability
gap](glossary_EN.md#term-diagnostic-observability-gap):

$G_{\mathrm{obs}} = P(O_t=1,A_t=U).$

Also report overall UNKNOWN rate, `UNKNOWN → DONE`, `UNKNOWN → SWEEP`,
acquisition depth, UNKNOWN dwell cost, budget exhaustion, unaffordable
acquisition, cascade exhaustion, and resolution yield per diagnostic cost.

## 5. `SWEEP` metrics

Necessary-SWEEP precision:

$P_S= \frac{\#\{A_t=S\land O_t=0\}} {\max(\#\{A_t=S\},1)}.$

Avoidable-SWEEP rate:

$R_{\mathrm{avoidable\ S}} = \frac{\#\{A_t=S\land O_t=1\}} {\max(\#\{A_t=S\},1)}.$

Over-computation:

$K_{\mathrm{over}} = K_{\mathrm{executed}}-t^*.$

Keep insufficiency, exhausted UNKNOWN, unaffordable acquisition, exhausted
cascade, invalid, and out-of-scope reason codes separate.

## 6. Cost

$C_{\mathrm{total}} = C_{\mathrm{sweeps}} + C_{\mathrm{observer}} + C_{\mathrm{diagnostics}}.$

$V_{\mathrm{net}} = C_{\mathrm{avoided\ sweeps}} - C_{\mathrm{observer}} - C_{\mathrm{diagnostics}}.$

Also report normalized reference cost, diagnostic-cost ratio, cost per safe
DONE, oracle-policy regret, acquisition-sequence regret, expected executed
sweeps, and terminal-time distributions.

## 7. Transferred methodological ideas

Selective prediction contributes risk, coverage, abstention, and risk–coverage
curves. Active Feature Acquisition contributes a finite registry, unused
analytic state, acquisition cost, fixed and greedy baselines, and an offline
oracle order. Adaptive computation contributes expected step count,
stopping-time distributions, and over-computation. Finite-sample risk control
contributes a frozen finite [candidate](glossary_EN.md#term-candidate) family and the order risk admission,
coverage selection, then cost selection.

The independent unit is `model_seed`, not a layer, sweep, or analytic event.

## 8. Baselines

```text
B-DUS-00 always_sweep_full_reference
B-DUS-01 oracle_done_upper_bound
B-DUS-02 rosenbaum_structural_wavefront
B-DUS-03 registered_prediction_error_or_residual_threshold
B-DUS-04 residual_threshold_with_persistence
B-DUS-05 fixed_metric_cascade
B-DUS-06 cheapest_first
B-DUS-07 greedy_quality_only
B-DUS-08 greedy_quality_per_cost
B-DUS-09 all_metrics
B-DUS-10 offline_oracle_acquisition_order
B-DUS-11 deterministic_analytic_registry
```

The greedy policy remains a shadow demonstrator.

## 9. Methodological sources

- [Hybrid [predictive coding](glossary_EN.md#term-predictive-coding)](https://doi.org/10.1371/journal.pcbi.1011280);
- [SelectiveNet](https://proceedings.mlr.press/v97/geifman19a.html);
- [Learn then Test](https://arxiv.org/abs/2110.01052);
- [Distribution Guided Active Feature Acquisition](https://arxiv.org/abs/2410.03915);
- [Adaptive Computation Time](https://arxiv.org/abs/1603.08983);
- [Joint Active Feature Acquisition](https://proceedings.neurips.cc/paper_files/paper/2018/hash/e5841df2166dd424a57127423d276bbe-Abstract.html);
- [Learning to select computations](https://arxiv.org/abs/1711.06892).
