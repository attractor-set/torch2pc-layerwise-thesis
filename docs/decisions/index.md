# Научные и архитектурные решения

[English version](index_EN.md)

ADR фиксируют решения, влияющие на интерпретацию или воспроизводимость:

- ADR-001: Torch2PC как основная реализация;
- ADR-002: native Ubuntu и ROCm Docker;
- ADR-003: macro F1 как основная метрика выбора;
- ADR-004: парный многостартовый статистический протокол;
- ADR-005: постпилотная фиксация порядка и телеметрии final;
- [ADR-006](ADR-006-stage3-scope.md): границы расширенного Stage 3;
- [ADR-007](ADR-007-stage3-locality-taxonomy.md): многомерная таксономия локальности.
- [ADR-008](ADR-008-predict-correct-acceleration.md): predict-correct acceleration и границы exact correction.
- [ADR-009](ADR-009-stage3b-rocm-canonical-lane.md): ROCm/float32 как единственная canonical lane Stage 3B B0; CPU/float64 остаётся инженерным контролем.
- [ADR-010](ADR-010-stage3b-per-cell-process-isolation.md): отдельный Python child process для каждой Stage 3B B0 canonical cell и fail-fast после systemic OOM.
