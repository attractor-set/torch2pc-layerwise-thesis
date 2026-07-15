# ADR-003: Macro-F1 as the primary selection metric

[Русская версия](ADR-003-primary-metric.md)

Status: accepted before the [pilot study](../glossary_EN.md#term-pilot-study).

Macro-F1 is used for validation selection and for the primary final comparison.
Accuracy is published as a secondary metric. The decision does not assume that
macro-F1 will necessarily detect a difference; it fixes the selection rule
before [test-dataset access](../glossary_EN.md#term-test-dataset-access).
