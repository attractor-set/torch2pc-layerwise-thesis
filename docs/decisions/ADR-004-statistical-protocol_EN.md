# ADR-004: Paired statistical protocol

[Русская версия](ADR-004-statistical-protocol.md)

Status: accepted before the [pilot study](../glossary_EN.md#term-pilot-study).

- the analysis unit is an independently trained model;
- methods are paired by `model_seed`;
- the primary analysis requires at least 10 complete pairs;
- raw values, effect size, and interval estimates are published;
- difference and equivalence are assessed separately;
- Holm adjustment is applied;
- failed runs remain in the registry and contribute to the reported success
  rate.
