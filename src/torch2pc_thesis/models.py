from __future__ import annotations

from collections.abc import Callable

import torch
import torch.nn as nn


class Flatten(nn.Module):
    def forward(self, value: torch.Tensor) -> torch.Tensor:
        return torch.flatten(value, 1)


def make_lenet_classic(num_classes: int = 10) -> nn.Sequential:
    return nn.Sequential(
        nn.Sequential(nn.Conv2d(1, 6, 5), nn.Tanh(), nn.AvgPool2d(2, 2)),
        nn.Sequential(nn.Conv2d(6, 16, 5), nn.Tanh(), nn.AvgPool2d(2, 2)),
        Flatten(),
        nn.Sequential(nn.Linear(16 * 5 * 5, 120), nn.Tanh()),
        nn.Sequential(nn.Linear(120, 84), nn.Tanh()),
        nn.Linear(84, num_classes),
    )


def make_lenet_modern(num_classes: int = 10) -> nn.Sequential:
    return nn.Sequential(
        nn.Sequential(nn.Conv2d(1, 6, 5), nn.ReLU(), nn.MaxPool2d(2, 2)),
        nn.Sequential(nn.Conv2d(6, 16, 5), nn.ReLU(), nn.MaxPool2d(2, 2)),
        Flatten(),
        nn.Sequential(nn.Linear(16 * 5 * 5, 120), nn.ReLU()),
        nn.Sequential(nn.Linear(120, 84), nn.ReLU()),
        nn.Linear(84, num_classes),
    )


def make_lenet_small(num_classes: int = 10) -> nn.Sequential:
    return nn.Sequential(
        nn.Sequential(nn.Conv2d(1, 4, 5), nn.Tanh(), nn.AvgPool2d(2, 2)),
        nn.Sequential(nn.Conv2d(4, 8, 5), nn.Tanh(), nn.AvgPool2d(2, 2)),
        Flatten(),
        nn.Sequential(nn.Linear(8 * 5 * 5, 64), nn.Tanh()),
        nn.Linear(64, num_classes),
    )


def make_scaling_mlp(depth: int, width: int, num_classes: int = 10) -> nn.Sequential:
    if depth < 2:
        raise ValueError("depth must be at least 2")
    if width < 1:
        raise ValueError("width must be positive")
    modules: list[nn.Module] = [
        nn.Sequential(Flatten(), nn.Linear(28 * 28, width), nn.Tanh())
    ]
    for _ in range(depth - 2):
        modules.append(nn.Sequential(nn.Linear(width, width), nn.Tanh()))
    modules.append(nn.Linear(width, num_classes))
    return nn.Sequential(*modules)


def _scaling_factory(depth: int, width: int) -> Callable[[int], nn.Sequential]:
    return lambda num_classes: make_scaling_mlp(depth, width, num_classes)


FACTORIES: dict[str, Callable[[int], nn.Sequential]] = {
    "lenet_classic": make_lenet_classic,
    "lenet_modern": make_lenet_modern,
    "lenet_small": make_lenet_small,
    **{
        f"mlp_d{depth}_w{width}": _scaling_factory(depth, width)
        for depth in (4, 8, 16, 32)
        for width in (64, 256)
    },
}


def build_model(name: str, num_classes: int = 10) -> nn.Sequential:
    try:
        return FACTORIES[name](num_classes)
    except KeyError as exc:
        raise ValueError(f"Unknown model architecture: {name}") from exc


def count_parameters(model: nn.Module) -> int:
    return sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)
