# Threats to validity

[Русская версия](threats-to-validity.md)

## Internal validity

Potential confounders include implementation mismatch, unequal initialization
or data order, test-driven [configuration](glossary_EN.md#term-configuration) changes, nondeterministic GPU
operations, counting reruns as independent models, and environment drift.
Mitigations include a pinned Torch2PC commit, C0/C1 controls, shared splits and
seeds, strict determinism, protocol freeze, an append-only registry, duplicate
final-run prevention, and an environment lock.

## Construct validity

Macro F1 measures classification quality rather than biological plausibility.
CKA and RSA measure selected forms of representational similarity rather than
identity of mechanisms. Wall-clock measurements remain implementation- and
hardware-dependent.

## Statistical conclusion validity

The design uses paired independently trained models, at least ten complete
pairs for confirmatory contrasts, effect sizes, confidence intervals, Holm
correction, and a separate equivalence margin. Incomplete pair sets are not
used to claim equivalence.

## External validity

Observations are limited to the pinned Torch2PC implementation, LeNet-like
architectures, selected datasets, optimizers, inference budgets, and the stated
Ubuntu/ROCm hardware profile. Generalization requires separate experiments.

## Reproducibility validity

Docker does not freeze BIOS, physical temperature, host-driver state, power
conditions, or background load. These variables are recorded. Procedural and
statistical reproducibility is sought; bitwise identity across GPUs is not
assumed.

The observations are bounded by the pinned Torch2PC commit, LeNet-like
architectures, selected image datasets, the declared optimizers and inference
budgets, the RX 7700 XT / Ryzen 7 5700X3D hardware profile, and the
Ubuntu/ROCm software environment.

## Researcher degrees of freedom

Primary outcomes, contrasts, seeds, test policy, and equivalence margin are
specified before final test access. Post-test analyses are labelled
exploratory and do not replace the pre-specified analysis.
