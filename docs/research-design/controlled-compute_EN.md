# Controlled compute environment

[Русская версия](controlled-compute.md)

Docker pins the user-space environment but not the operating-system kernel,
`amdgpu`, BIOS, temperature, or background load. These quantities are recorded
separately. CPU correctness checks, GPU training, and timing measurements are
treated as distinct [execution](../glossary_EN.md#term-execution) profiles and are not combined in one table
without explicit labeling.
