"""Non-perturbing profiling primitives for the preregistered Stage 3B campaign."""

from __future__ import annotations

import math
import time
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from typing import Final, Literal

import torch
from torch import Tensor

from torch2pc_thesis.profiling import (
    STAGE3_PROFILE_REGIONS,
    ProfilingProtocol,
    Stage3ProfilingError,
    stage3_profile_region,
    synchronize_device,
)

STAGE3B_PROFILE_SCHEMA_VERSION: Final[int] = 1
STAGE3B_BASELINE_CANDIDATE: Final[str] = "stage2_baseline"
STAGE3B_METHODS: Final[frozenset[str]] = frozenset({"fixedpred", "strict"})
CPU_FLOAT64_THRESHOLDS: Final[tuple[float, float]] = (0.99999, 1e-7)
GPU_FLOAT32_THRESHOLDS: Final[tuple[float, float]] = (0.999, 1e-3)

StepKind = Literal["warmup", "measured"]


@dataclass(frozen=True)
class ProtocolStep:
    """One technical step in a Stage 3B profiling repetition."""

    repetition: int
    kind: StepKind
    step: int

    @property
    def measured(self) -> bool:
        return self.kind == "measured"


@dataclass(frozen=True)
class NonPerturbationThresholds:
    """Numerical thresholds frozen by the Stage 3B preregistration."""

    min_cosine: float
    max_relative_l2: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.min_cosine) or not 0.0 <= self.min_cosine <= 1.0:
            raise Stage3ProfilingError("min_cosine must be finite and lie in [0, 1]")
        if not math.isfinite(self.max_relative_l2) or self.max_relative_l2 < 0.0:
            raise Stage3ProfilingError(
                "max_relative_l2 must be finite and non-negative"
            )


@dataclass
class ProfilingCounters:
    """Mutable counters collected while one profiling region executes."""

    vjp_calls: int = 0
    synchronization_points: int = 0
    saved_tensor_bytes: int = 0
    actual_inference_steps: int = 0
    non_finite_events: int = 0

    def validate(self) -> None:
        for name, value in asdict(self).items():
            if value < 0:
                raise Stage3ProfilingError(f"{name} must be non-negative")


@dataclass(frozen=True)
class RegionMeasurement:
    """One measured Stage 3B region observation."""

    candidate_id: str
    method: str
    repetition: int
    step: int
    region: str
    host_time_us: float
    device_time_us: float
    peak_allocated_bytes: int
    peak_reserved_bytes: int
    vjp_calls: int
    synchronization_points: int
    saved_tensor_bytes: int
    actual_inference_steps: int
    non_finite_events: int

    def __post_init__(self) -> None:
        if not self.candidate_id:
            raise Stage3ProfilingError("candidate_id is required")
        if self.method not in STAGE3B_METHODS:
            raise Stage3ProfilingError(f"unsupported Stage 3B method: {self.method}")
        if self.repetition < 0 or self.step < 0:
            raise Stage3ProfilingError("repetition and step must be non-negative")
        if self.region not in STAGE3_PROFILE_REGIONS:
            raise Stage3ProfilingError(f"unsupported profiling region: {self.region}")
        for name, value in {
            "host_time_us": self.host_time_us,
            "device_time_us": self.device_time_us,
        }.items():
            if not math.isfinite(value) or value < 0.0:
                raise Stage3ProfilingError(f"{name} must be finite and non-negative")
        for name, value in {
            "peak_allocated_bytes": self.peak_allocated_bytes,
            "peak_reserved_bytes": self.peak_reserved_bytes,
            "vjp_calls": self.vjp_calls,
            "synchronization_points": self.synchronization_points,
            "saved_tensor_bytes": self.saved_tensor_bytes,
            "actual_inference_steps": self.actual_inference_steps,
            "non_finite_events": self.non_finite_events,
        }.items():
            if value < 0:
                raise Stage3ProfilingError(f"{name} must be non-negative")

    def to_record(self) -> dict[str, object]:
        return {
            "schema_version": STAGE3B_PROFILE_SCHEMA_VERSION,
            **asdict(self),
        }


@dataclass(frozen=True)
class TensorComparison:
    """Numerical comparison for one named tensor in the B0 integrity gate."""

    name: str
    cosine: float
    relative_l2: float
    reference_norm: float
    candidate_norm: float
    finite: bool
    passed: bool

    def to_record(self) -> dict[str, object]:
        return asdict(self)


class Stage3BProfiler:
    """Collect region records without changing the profiled computation."""

    def __init__(
        self,
        *,
        device: torch.device | str,
        candidate_id: str = STAGE3B_BASELINE_CANDIDATE,
        method: str,
    ) -> None:
        if not candidate_id:
            raise Stage3ProfilingError("candidate_id is required")
        if method not in STAGE3B_METHODS:
            raise Stage3ProfilingError(f"unsupported Stage 3B method: {method}")
        self.device = torch.device(device)
        self.candidate_id = candidate_id
        self.method = method
        self._records: list[RegionMeasurement] = []

    @property
    def records(self) -> tuple[RegionMeasurement, ...]:
        return tuple(self._records)

    @property
    def uses_device_timing(self) -> bool:
        return bool(
            self.device.type == "cuda" and torch.cuda.is_available()
        )

    def clear(self) -> None:
        self._records.clear()

    @contextmanager
    def region(
        self,
        region: str,
        *,
        repetition: int,
        step: int,
        measured: bool = True,
    ) -> Iterator[ProfilingCounters]:
        """Measure one declared region and yield mutable instrumentation counters."""
        if repetition < 0 or step < 0:
            raise Stage3ProfilingError("repetition and step must be non-negative")
        if region not in STAGE3_PROFILE_REGIONS:
            raise Stage3ProfilingError(f"unsupported profiling region: {region}")

        counters = ProfilingCounters()
        if not measured:
            with stage3_profile_region(region):
                yield counters
            counters.validate()
            return

        implicit_synchronizations = 0
        start_event: torch.cuda.Event | None = None
        end_event: torch.cuda.Event | None = None

        if self.uses_device_timing:
            synchronize_device(self.device)
            implicit_synchronizations += 1
            torch.cuda.reset_peak_memory_stats(self.device)
            start_event = torch.cuda.Event(enable_timing=True)
            end_event = torch.cuda.Event(enable_timing=True)
            start_event.record()

        started_ns = time.perf_counter_ns()
        with stage3_profile_region(region):
            yield counters
        if end_event is not None:
            end_event.record()
        if self.uses_device_timing:
            synchronize_device(self.device)
            implicit_synchronizations += 1
        finished_ns = time.perf_counter_ns()

        counters.validate()
        host_time_us = (finished_ns - started_ns) / 1_000.0
        device_time_us = 0.0
        peak_allocated_bytes = 0
        peak_reserved_bytes = 0
        if start_event is not None and end_event is not None:
            device_time_us = float(start_event.elapsed_time(end_event)) * 1_000.0
            peak_allocated_bytes = int(torch.cuda.max_memory_allocated(self.device))
            peak_reserved_bytes = int(torch.cuda.max_memory_reserved(self.device))

        self._records.append(
            RegionMeasurement(
                candidate_id=self.candidate_id,
                method=self.method,
                repetition=repetition,
                step=step,
                region=region,
                host_time_us=host_time_us,
                device_time_us=device_time_us,
                peak_allocated_bytes=peak_allocated_bytes,
                peak_reserved_bytes=peak_reserved_bytes,
                vjp_calls=counters.vjp_calls,
                synchronization_points=(
                    counters.synchronization_points + implicit_synchronizations
                ),
                saved_tensor_bytes=counters.saved_tensor_bytes,
                actual_inference_steps=counters.actual_inference_steps,
                non_finite_events=counters.non_finite_events,
            )
        )


def iter_protocol_steps(protocol: ProfilingProtocol) -> Iterator[ProtocolStep]:
    """Yield preregistered warm-up and measured steps in deterministic order."""
    for repetition in range(protocol.repetitions):
        for step in range(protocol.warmup_steps):
            yield ProtocolStep(repetition=repetition, kind="warmup", step=step)
        for step in range(protocol.measured_steps):
            yield ProtocolStep(repetition=repetition, kind="measured", step=step)


def validate_profile_completeness(
    records: Sequence[RegionMeasurement],
    protocol: ProfilingProtocol,
    *,
    required_regions: Sequence[str] = tuple(sorted(STAGE3_PROFILE_REGIONS)),
) -> None:
    """Enforce the preregistered repetition, step, region, and integrity coverage."""
    unknown = sorted(set(required_regions) - STAGE3_PROFILE_REGIONS)
    if unknown:
        raise Stage3ProfilingError(f"unsupported required regions: {unknown}")

    expected_repetitions = set(range(protocol.repetitions))
    actual_repetitions = {record.repetition for record in records}
    if actual_repetitions != expected_repetitions:
        raise Stage3ProfilingError(
            "profiling repetitions are incomplete: "
            f"expected={sorted(expected_repetitions)}, actual={sorted(actual_repetitions)}"
        )

    required = set(required_regions)
    for repetition in range(protocol.repetitions):
        for step in range(protocol.measured_steps):
            step_records = [
                record
                for record in records
                if record.repetition == repetition and record.step == step
            ]
            regions = {record.region for record in step_records}
            missing = sorted(required - regions)
            if missing:
                raise Stage3ProfilingError(
                    "profiling step is incomplete: "
                    f"repetition={repetition}, step={step}, missing={missing}"
                )
            if any(record.non_finite_events for record in step_records):
                raise Stage3ProfilingError(
                    "profiling step contains non-finite integrity events: "
                    f"repetition={repetition}, step={step}"
                )


def thresholds_for_device(
    device: torch.device | str,
    dtype: torch.dtype,
) -> NonPerturbationThresholds:
    """Return the preregistered CPU or ROCm/CUDA non-perturbation thresholds."""
    resolved = torch.device(device)
    if resolved.type == "cpu" and dtype == torch.float64:
        return NonPerturbationThresholds(*CPU_FLOAT64_THRESHOLDS)
    if resolved.type == "cuda" and dtype == torch.float32:
        return NonPerturbationThresholds(*GPU_FLOAT32_THRESHOLDS)
    raise Stage3ProfilingError(
        "Stage 3B thresholds are frozen for CPU/float64 and GPU/float32 only"
    )


def snapshot_named_tensors(values: Mapping[str, Tensor]) -> dict[str, Tensor]:
    """Clone named tensors without retaining autograd history or shared storage."""
    if not values:
        raise Stage3ProfilingError("at least one named tensor is required")
    return {name: tensor.detach().clone() for name, tensor in values.items()}


def compare_named_tensors(
    reference: Mapping[str, Tensor],
    candidate: Mapping[str, Tensor],
    *,
    thresholds: NonPerturbationThresholds,
) -> tuple[TensorComparison, ...]:
    """Compare two tensor snapshots using cosine and relative-L2 gates."""
    reference_names = set(reference)
    candidate_names = set(candidate)
    if reference_names != candidate_names:
        raise Stage3ProfilingError(
            "tensor names differ between reference and candidate: "
            f"reference_only={sorted(reference_names - candidate_names)}, "
            f"candidate_only={sorted(candidate_names - reference_names)}"
        )
    if not reference_names:
        raise Stage3ProfilingError("at least one named tensor is required")

    comparisons: list[TensorComparison] = []
    for name in sorted(reference_names):
        reference_tensor = reference[name]
        candidate_tensor = candidate[name]
        if reference_tensor.shape != candidate_tensor.shape:
            raise Stage3ProfilingError(
                f"tensor shape differs for {name}: "
                f"reference={tuple(reference_tensor.shape)}, "
                f"candidate={tuple(candidate_tensor.shape)}"
            )

        reference_vector = reference_tensor.detach().to(dtype=torch.float64).reshape(-1)
        candidate_vector = candidate_tensor.detach().to(dtype=torch.float64).reshape(-1)
        finite = bool(
            torch.isfinite(reference_vector).all().item()
            and torch.isfinite(candidate_vector).all().item()
        )
        reference_norm = float(torch.linalg.vector_norm(reference_vector).item())
        candidate_norm = float(torch.linalg.vector_norm(candidate_vector).item())

        if reference_norm == 0.0 and candidate_norm == 0.0:
            cosine = 1.0
        elif reference_norm == 0.0 or candidate_norm == 0.0:
            cosine = 0.0
        else:
            cosine = float(
                torch.dot(reference_vector, candidate_vector).item()
                / (reference_norm * candidate_norm)
            )
            cosine = max(-1.0, min(1.0, cosine))

        difference_norm = float(
            torch.linalg.vector_norm(candidate_vector - reference_vector).item()
        )
        denominator = max(reference_norm, torch.finfo(torch.float64).eps)
        relative_l2 = difference_norm / denominator
        passed = bool(
            finite
            and cosine >= thresholds.min_cosine
            and relative_l2 <= thresholds.max_relative_l2
        )
        comparisons.append(
            TensorComparison(
                name=name,
                cosine=cosine,
                relative_l2=relative_l2,
                reference_norm=reference_norm,
                candidate_norm=candidate_norm,
                finite=finite,
                passed=passed,
            )
        )
    return tuple(comparisons)


def assert_non_perturbing(
    reference: Mapping[str, Tensor],
    candidate: Mapping[str, Tensor],
    *,
    thresholds: NonPerturbationThresholds,
) -> tuple[TensorComparison, ...]:
    """Raise when any tensor fails the preregistered B0 numerical gate."""
    comparisons = compare_named_tensors(reference, candidate, thresholds=thresholds)
    failed = [comparison.to_record() for comparison in comparisons if not comparison.passed]
    if failed:
        raise Stage3ProfilingError(f"Stage 3B non-perturbation gate failed: {failed}")
    return comparisons
