# Hardware and software environment

[Русская версия](hardware.md)

The target node is an RX 7700 XT with a Ryzen 7 5700X3D, 64 GB RAM, and native
Ubuntu. Exact kernel, `amdgpu`, ROCm, PyTorch, Docker-image, and BIOS versions
are recorded when timing measurements first run rather than assumed in
advance.

CPU/float64 is used for strict analytical controls. GPU/float32 is used for
primary training. Timing is measured separately, without background GPU load,
with [warm-up](glossary_EN.md#term-warm-up) and synchronization.
