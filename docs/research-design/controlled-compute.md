# Контролируемое вычислительное пространство

[English version](controlled-compute_EN.md)

Docker фиксирует user-space окружение, но не kernel, amdgpu, BIOS, temperature
или background load. Эти параметры записываются отдельно. CPU correctness,
GPU training и timing рассматриваются как разные контуры и не смешиваются в
одну таблицу без явной маркировки.
