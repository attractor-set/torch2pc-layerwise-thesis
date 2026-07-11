# ADR-002: Use native Ubuntu and ROCm Docker

[Русская версия](ADR-002-use-rocm-docker.md)


Status: accepted

Use native Ubuntu 24.04.4 and a versioned ROCm/PyTorch Docker image for all
final GPU runs. Use CPU float64 for analytical controls.

The host driver, kernel, BIOS, clocks, temperature, and background load are
recorded separately.
