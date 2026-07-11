# Analysis plan

[Русская версия](analysis-plan.md)

Primary analysis uses paired model seeds on FashionMNIST macro F1, with effect sizes, intervals, multiplicity correction, and a separate equivalence criterion. Layer and sample observations are not treated as independent model replications.

A primary contrast is labelled confirmatory only with at least ten complete
pre-specified seed pairs. With fewer pairs, descriptive estimates are retained,
but Holm-adjusted inference and equivalence claims are not produced. Pilot
selection uses FashionMNIST validation only; MNIST is a secondary transfer
check.
