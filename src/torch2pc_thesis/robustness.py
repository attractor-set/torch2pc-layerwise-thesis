from __future__ import annotations

import torch
import torch.nn.functional as functional

from torch2pc_thesis.reproducibility import stable_int_seed


def corruption_strength(severity: int) -> float:
    if severity not in {1, 2, 3, 4, 5}:
        raise ValueError("severity must be in 1..5")
    return severity / 5.0


def corrupt_batch(
    inputs: torch.Tensor,
    corruption: str,
    severity: int,
    *,
    seed: int,
) -> torch.Tensor:
    strength = corruption_strength(severity)
    generator = torch.Generator(device=inputs.device)
    generator.manual_seed(seed)
    value = inputs.clone()

    if corruption == "clean":
        return value
    if corruption == "gaussian_noise":
        noise = torch.randn(
            value.shape,
            generator=generator,
            device=value.device,
            dtype=value.dtype,
        )
        return torch.clamp(value + noise * (0.08 + 0.35 * strength), 0, 1)
    if corruption == "gaussian_blur":
        kernel_size = 3 if severity <= 2 else 5
        padding = kernel_size // 2
        return functional.avg_pool2d(
            value,
            kernel_size=kernel_size,
            stride=1,
            padding=padding,
        )
    if corruption == "occlusion":
        side = max(2, int(round(value.shape[-1] * (0.1 + 0.35 * strength))))
        max_top = value.shape[-2] - side
        max_left = value.shape[-1] - side
        for sample_index in range(value.shape[0]):
            sample_generator = torch.Generator(device=value.device)
            sample_generator.manual_seed(stable_int_seed(seed, sample_index))
            top = int(
                torch.randint(
                    max_top + 1,
                    (1,),
                    generator=sample_generator,
                    device=value.device,
                ).item()
            )
            left = int(
                torch.randint(
                    max_left + 1,
                    (1,),
                    generator=sample_generator,
                    device=value.device,
                ).item()
            )
            value[sample_index, :, top : top + side, left : left + side] = 0
        return value
    if corruption == "pixel_dropout":
        mask = torch.rand(value.shape, generator=generator, device=value.device) < (
            0.05 + 0.45 * strength
        )
        value[mask] = 0
        return value
    raise ValueError(f"Unknown corruption: {corruption}")


def batch_corruption_seed(
    base_seed: int,
    dataset: str,
    corruption: str,
    severity: int,
    batch_index: int,
) -> int:
    return stable_int_seed(base_seed, dataset, corruption, severity, batch_index)
