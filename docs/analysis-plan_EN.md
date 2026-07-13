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

Final execution uses a deterministically counterbalanced method order within
each dataset/model/seed block, GPU synchronization around timed epochs, and
explicit peak-memory telemetry. The post-pilot execution amendment is recorded
in `docs/decisions/ADR-005-post-pilot-final-execution_EN.md`.


## Stage 3 addendum

Stage 3 does not modify the Stage 1/2 confirmatory analysis. Training quality
uses independently trained model seeds; profiling uses matched cell/repetition
inside a hardware block; locality events are aggregated within run before
between-seed analysis; layer alignment is aggregated within model first.

B1/B2 use numerical-equivalence and paired runtime/memory observations. C1/C2
use validation non-inferiority, gradient alignment, and compute reduction. The
final non-inferiority margin is fixed before Stage 3 test access. See
[stage-3-protocol_EN.md](stage-3-protocol_EN.md).
