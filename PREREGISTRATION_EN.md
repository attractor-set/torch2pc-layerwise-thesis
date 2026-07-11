# Analysis pre-specification

[Русская версия](PREREGISTRATION.md)

Status: draft before the control gate and pilot.

The statistical unit is an independently trained model. FashionMNIST is the
primary dataset, macro F1 is the primary metric, and the primary contrasts are
FixedPred vs BP and Strict vs BP. Test data are accessed only after pilot
freeze. Equivalence requires the 90% confidence interval of the paired macro-F1
difference to lie inside the pre-specified margin.

Pilot parameters are ranked using FashionMNIST validation only: success rate,
mean validation macro F1, mean training time, inference steps, and eta. MNIST
is a secondary check. Fewer than ten complete final pairs are labelled
incomplete and do not support an equivalence conclusion.
