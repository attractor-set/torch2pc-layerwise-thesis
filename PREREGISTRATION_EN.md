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
validation only: success rate, mean validation macro F1, mean measured training
epoch time, inference steps, and eta. MNIST is descriptive for selection.

Before final execution, `pilot-freeze_manifest.json` records the source commit,
environment-lock hash, selected parameters, and hashes of the governing
configuration and analysis documents.
