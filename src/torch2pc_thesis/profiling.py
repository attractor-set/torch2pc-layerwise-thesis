from __future__ import annotations

import math
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from statistics import fmean, median
from typing import Any

import torch

STAGE3_PROFILE_REGIONS = frozenset(
    {
        "initial_forward",
        "state_inference",
        "local_state_vjp",
        "parameter_vjp",
        "optimizer_step",
    }
)


class Stage3ProfilingError(ValueError):
    """Raised when a Stage 3 profiling protocol or sample is invalid."""


@dataclass(frozen=True)
class ProfilingProtocol:
    warmup_steps: int
    measured_steps: int
    repetitions: int

    def __post_init__(self) -> None:
        for name, value in {
            "warmup_steps": self.warmup_steps,
            "measured_steps": self.measured_steps,
            "repetitions": self.repetitions,
        }.items():
            minimum = 0 if name == "warmup_steps" else 1
            if value < minimum:
                raise Stage3ProfilingError(f"{name} must be >= {minimum}")


@dataclass(frozen=True)
class TimingSample:
    region: str
    cpu_time_us: float
    device_time_us: float

    def __post_init__(self) -> None:
        if self.region not in STAGE3_PROFILE_REGIONS:
            raise Stage3ProfilingError(f"unsupported profiling region: {self.region}")
        if not math.isfinite(self.cpu_time_us) or self.cpu_time_us < 0:
            raise Stage3ProfilingError("cpu_time_us must be finite and non-negative")
        if not math.isfinite(self.device_time_us) or self.device_time_us < 0:
            raise Stage3ProfilingError("device_time_us must be finite and non-negative")


@contextmanager
def stage3_profile_region(region: str) -> Iterator[None]:
    """Label a Stage 3 code region for ``torch.profiler`` traces."""

    if region not in STAGE3_PROFILE_REGIONS:
        raise Stage3ProfilingError(f"unsupported profiling region: {region}")
    with torch.autograd.profiler.record_function(f"stage3::{region}"):
        yield


def synchronize_device(device: torch.device | str) -> None:
    """Synchronize CUDA/ROCm devices while leaving CPU execution untouched."""

    resolved = torch.device(device)
    if resolved.type == "cuda" and torch.cuda.is_available():
        torch.cuda.synchronize(resolved)


def _percentile(values: Sequence[float], probability: float) -> float:
    if not values:
        raise Stage3ProfilingError("at least one timing value is required")
    if not 0 <= probability <= 1:
        raise Stage3ProfilingError("probability must be in [0, 1]")
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def summarize_timing_samples(samples: Sequence[TimingSample]) -> dict[str, Any]:
    if not samples:
        raise Stage3ProfilingError("at least one timing sample is required")
    regions = {sample.region for sample in samples}
    if len(regions) != 1:
        raise Stage3ProfilingError("timing samples must belong to one region")
    cpu = [sample.cpu_time_us for sample in samples]
    device = [sample.device_time_us for sample in samples]
    return {
        "region": next(iter(regions)),
        "sample_count": len(samples),
        "cpu_time_us": {
            "mean": fmean(cpu),
            "median": median(cpu),
            "p95": _percentile(cpu, 0.95),
            "min": min(cpu),
            "max": max(cpu),
        },
        "device_time_us": {
            "mean": fmean(device),
            "median": median(device),
            "p95": _percentile(device, 0.95),
            "min": min(device),
            "max": max(device),
        },
    }


def amdahl_speedup(optimizable_fraction: float, component_speedup: float) -> float:
    """Return total speedup predicted by Amdahl's law."""

    if not math.isfinite(optimizable_fraction) or not 0 <= optimizable_fraction <= 1:
        raise Stage3ProfilingError("optimizable_fraction must be finite and in [0, 1]")
    if component_speedup < 1 or math.isnan(component_speedup):
        raise Stage3ProfilingError("component_speedup must be >= 1")
    if math.isinf(component_speedup):
        return math.inf if optimizable_fraction == 1 else 1 / (1 - optimizable_fraction)
    return 1 / ((1 - optimizable_fraction) + optimizable_fraction / component_speedup)
