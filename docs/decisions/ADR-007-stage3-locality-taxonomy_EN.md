# ADR-007: multidimensional locality taxonomy

[Русская версия](ADR-007-stage3-locality-taxonomy.md)

- Status: accepted for design
- Date: 2026-07-13

## Context

Torch2PC uses layer prediction errors and adjacent dependencies in its equations,
while a centralized Python scheduler and PyTorch autograd execute them. A single
local/non-local flag cannot represent this distinction.

## Decision

Stage 3 reports separate measurements: algorithmic dependency set, dependency
radius, graph modules/span, independent graph lifetime, feedback operator,
orchestration/synchronization, VJP calls, and saved-tensor bytes.

The structural gate `dependency_radius <= 1` applies only to events declared
mathematically layer-local. Composite VJP may have a wider graph span while
retaining the same local update rule.

## Consequences

Locality is not collapsed into one score. B1 versus B2 directly represents the
trade-off between execution locality and throughput. Approximate feedback has a
separate algorithm-changing label.
