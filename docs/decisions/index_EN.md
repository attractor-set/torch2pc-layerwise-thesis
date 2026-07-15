# Architecture and research decisions

[Русская версия](index.md)

- ADR-001: Use Torch2PC as the primary implementation.
- ADR-002: Use native Ubuntu and ROCm Docker for final results.
- ADR-003: Use macro F1 as the primary selection metric.
- ADR-004: Use paired multi-seed statistics with Holm correction.
- ADR-005: Freeze post-pilot final ordering, resumption, and telemetry.
- [ADR-006](ADR-006-stage3-scope_EN.md): extended Stage 3 scope.
- [ADR-007](ADR-007-stage3-locality-taxonomy_EN.md): multidimensional locality taxonomy.
- [ADR-008](ADR-008-predict-correct-acceleration_EN.md): predict-correct acceleration and exact-correction boundaries.
- [ADR-009](ADR-009-stage3b-rocm-canonical-lane_EN.md): ROCm/float32 as the only Stage 3B B0 canonical lane; CPU/float64 remains an engineering control.
- [ADR-010](ADR-010-stage3b-per-cell-process-isolation_EN.md): a fresh Python child process per Stage 3B B0 canonical cell with fail-fast handling for systemic OOM.
- [ADR-011](ADR-011-stage3b-b0-derived-evidence-seal_EN.md): read-only validation, aggregation, and a content-addressed Stage 3B B0 [evidence](../glossary_EN.md#term-evidence) seal.
- [ADR-012](ADR-012-pc-tref-pc-catm-scenario-a_EN.md): PC-TREF Balanced Core, PC-CATM, and Scenario A as one realistic post-B0 path.
