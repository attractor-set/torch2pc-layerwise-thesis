from __future__ import annotations

import math

import pytest

from torch2pc_thesis.profiling import (
    ProfilingProtocol,
    Stage3ProfilingError,
    TimingSample,
    amdahl_speedup,
    stage3_profile_region,
    summarize_timing_samples,
)


def test_profiling_protocol_rejects_empty_measurement() -> None:
    with pytest.raises(Stage3ProfilingError, match="measured_steps"):
        ProfilingProtocol(warmup_steps=0, measured_steps=0, repetitions=1)


def test_profile_region_accepts_declared_stage3_region() -> None:
    with stage3_profile_region("local_state_vjp"):
        value = 1 + 1
    assert value == 2


def test_timing_summary_reports_robust_statistics() -> None:
    samples = [
        TimingSample("state_inference", cpu_time_us=value, device_time_us=value / 2)
        for value in (10.0, 20.0, 30.0)
    ]
    summary = summarize_timing_samples(samples)
    assert summary["sample_count"] == 3
    assert summary["cpu_time_us"]["median"] == 20.0
    assert summary["cpu_time_us"]["p95"] == pytest.approx(29.0)


def test_amdahl_speedup_handles_finite_and_infinite_component_speedup() -> None:
    assert amdahl_speedup(0.5, 2.0) == pytest.approx(4 / 3)
    assert amdahl_speedup(0.5, math.inf) == pytest.approx(2.0)
