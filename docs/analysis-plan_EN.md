# Analysis plan

[Русская версия](analysis-plan.md)

Primary analysis uses paired model seeds on FashionMNIST macro F1. The primary
contrasts are FixedPred vs BP and Strict vs BP. Each contrast reports seed-level
values, mean paired difference, 95% confidence interval, Cohen dz, the declared
paired test, Holm adjustment, and a separate equivalence assessment.

The absolute macro-F1 equivalence margin of 0.01 is fixed before pilot
execution. Equivalence requires at least ten complete pairs and a 90%
confidence interval entirely inside the margin. A non-significant difference
is not treated as evidence of equivalence.

A contrast is confirmatory only with at least ten complete pre-specified seed
pairs. With fewer pairs, descriptive estimates are retained, but no
Holm-adjusted confirmatory conclusion or equivalence conclusion is produced.

Pilot selection uses FashionMNIST validation only. Success rate is based on the
first terminal attempt for each configuration/seed. MNIST is a secondary
transfer description and does not enter ranking. An advisory final sample size
may only increase the initial ten pairs and follows the rule documented in
`PREREGISTRATION.md`.

Layer and sample observations are not treated as independent model
replications. Representation uncertainty must include between-seed variation;
a bootstrap over images alone is insufficient. Equal-update and
equal-wall-clock comparisons are reported separately.
