# ADR-007: многомерная таксономия локальности

[English version](ADR-007-stage3-locality-taxonomy_EN.md)

- Статус: принято для проектирования
- Дата: 2026-07-13

## Контекст

Torch2PC использует послойные prediction errors и соседние зависимости в
формулах, но исполняет их централизованным Python scheduler и PyTorch autograd.
Один бинарный признак «локально/нелокально» не описывает этот разрыв.

## Решение

Stage 3 публикует отдельные измерения:

- algorithmic dependency set;
- dependency radius;
- graph modules и graph span;
- independent graph lifetime;
- feedback operator type;
- orchestration и synchronization points;
- VJP calls и saved tensor bytes.

Structural gate `dependency_radius <= 1` применяется только к событиям,
объявленным mathematically layer-local. Composite VJP может иметь больший graph
span и при этом сохранять локальный update rule.

## Последствия

Locality не сводится к одному score. Сравнение B1 и B2 явно представляет
trade-off между execution locality и throughput. Approximate feedback получает
отдельный algorithm-changing label.
