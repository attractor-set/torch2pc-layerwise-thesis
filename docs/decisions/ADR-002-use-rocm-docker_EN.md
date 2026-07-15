# ADR-002: Use native Ubuntu and ROCm Docker

[Русская версия](ADR-002-use-rocm-docker.md)

Status: accepted.

## Context

The primary compute device is an AMD Radeon RX 7700 XT. [Runtime](../glossary_EN.md#term-runtime) and numerical
behavior must be compared in a controlled environment.

## Decision

Run final GPU experiments on native Ubuntu 24.04.4 with a versioned
ROCm/PyTorch Docker image. Run analytical controls on CPU with float64.

## Consequences

The container does not pin the host driver, kernel, BIOS, clock rates,
temperature, or background load. These quantities are recorded separately.
