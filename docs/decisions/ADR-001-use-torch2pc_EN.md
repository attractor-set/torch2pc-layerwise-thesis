# ADR-001: Use Torch2PC as the primary implementation

[Русская версия](ADR-001-use-torch2pc.md)

Status: accepted.

## Context

The study compares the Exact, FixedPred, and Strict regimes from Rosenbaum’s
line of work.

## Decision

Use a fully pinned Torch2PC commit, audit it against the 2025 correction, and
block pilot and final [execution](../glossary_EN.md#term-execution) until C0/C1 pass.

## Consequences

Results apply to the specific implementation revision and declared
architectures rather than automatically to every predictive-coding algorithm.
