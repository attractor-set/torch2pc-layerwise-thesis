from __future__ import annotations

import json
import math
import statistics
import threading
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import torch
import torch.nn as nn

from torch2pc_thesis.stage3b_a1_obs_ni0 import ObserverArm
from torch2pc_thesis.stage3b_a1_obs_oh0 import (
    BENCHMARK_SCHEMA_ID,
    ExecutionOrder,
    run_registered_backward,
)
from torch2pc_thesis.stage3b_a1_observer import (
    OBSERVER_SCHEMA_ID,
    ObserverPayload,
    PassiveLayerObserver,
)

PAYLOAD_LIMIT_BYTES = 64 * 1024 * 1024
CPU_ABSOLUTE_TOLERANCE_BYTES = 8 * 1024 * 1024
GPU_ABSOLUTE_TOLERANCE_BYTES = 1 * 1024 * 1024
CPU_RELATIVE_TOLERANCE = 0.25
GPU_RELATIVE_TOLERANCE = 0.10


@dataclass(frozen=True)
class MemoryWorkerRequest:
    """Serializable request for one isolated memory execution."""

    device: str
    lane: str
    arm: ObserverArm
    observer_enabled: bool
    model_seed: int
    batch_index: int
    source_git_commit: str
    source_git_branch: str
    experiment_image: str
    rss_sampler_interval_ms: float

    def __post_init__(self) -> None:
        if self.device not in {"cpu", "gpu"}:
            raise ValueError("OBS-OH0 memory worker device must be cpu or gpu")
        if self.lane not in {"cpu", "rocm"}:
            raise ValueError("OBS-OH0 memory worker lane must be cpu or rocm")
        if self.batch_index < 0:
            raise ValueError("OBS-OH0 batch index must be non-negative")
        if not self.source_git_commit or not self.source_git_branch:
            raise ValueError("OBS-OH0 source provenance must be non-empty")
        if not self.experiment_image:
            raise ValueError("OBS-OH0 experiment image must be non-empty")
        if not 0.0 < self.rss_sampler_interval_ms <= 1.0:
            raise ValueError("RSS sampler interval must be within (0, 1] ms")

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["arm"] = self.arm.value
        return result

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> MemoryWorkerRequest:
        return cls(
            device=str(value["device"]),
            lane=str(value["lane"]),
            arm=ObserverArm(str(value["arm"])),
            observer_enabled=bool(value["observer_enabled"]),
            model_seed=int(value["model_seed"]),
            batch_index=int(value["batch_index"]),
            source_git_commit=str(value["source_git_commit"]),
            source_git_branch=str(value["source_git_branch"]),
            experiment_image=str(value["experiment_image"]),
            rss_sampler_interval_ms=float(value["rss_sampler_interval_ms"]),
        )


@dataclass(frozen=True)
class MemoryExecutionResult:
    """One isolated observer-off or observer-on memory measurement."""

    lane: str
    arm: ObserverArm
    observer_enabled: bool
    model_seed: int
    batch_index: int
    source_git_commit: str
    source_git_branch: str
    experiment_image: str
    device_name: str
    dtype: str
    payload_bytes: int
    payload_records: int
    payload_bytes_by_role: Mapping[str, int]
    payload_bytes_by_layer: Mapping[str, int]
    observer_validation_passed: bool
    baseline_rss_bytes: int | None
    peak_rss_bytes: int | None
    final_rss_bytes: int | None
    vm_hwm_bytes: int | None
    incremental_peak_rss_bytes: int | None
    incremental_final_rss_bytes: int | None
    baseline_allocated_bytes: int | None
    baseline_reserved_bytes: int | None
    peak_allocated_bytes: int | None
    peak_reserved_bytes: int | None
    current_allocated_bytes: int | None
    current_reserved_bytes: int | None
    incremental_peak_allocated_bytes: int | None
    incremental_peak_reserved_bytes: int | None

    @property
    def valid(self) -> bool:
        if self.payload_bytes < 0 or self.payload_records < 0:
            return False
        if self.observer_enabled:
            if not self.observer_validation_passed or self.payload_records != 12:
                return False
        elif self.payload_bytes != 0 or self.payload_records != 0:
            return False

        values: tuple[int | None, ...]
        if self.lane == "cpu":
            values = (
                self.baseline_rss_bytes,
                self.peak_rss_bytes,
                self.final_rss_bytes,
                self.vm_hwm_bytes,
                self.incremental_peak_rss_bytes,
                self.incremental_final_rss_bytes,
            )
        else:
            values = (
                self.baseline_allocated_bytes,
                self.baseline_reserved_bytes,
                self.peak_allocated_bytes,
                self.peak_reserved_bytes,
                self.current_allocated_bytes,
                self.current_reserved_bytes,
                self.incremental_peak_allocated_bytes,
                self.incremental_peak_reserved_bytes,
            )
        return all(value is not None and value >= 0 for value in values)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["benchmark_schema_id"] = BENCHMARK_SCHEMA_ID
        result["observer_schema_id"] = OBSERVER_SCHEMA_ID
        result["arm"] = self.arm.value
        result["valid"] = self.valid
        return result

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> MemoryExecutionResult:
        def optional_int(name: str) -> int | None:
            raw = value.get(name)
            return None if raw is None else int(raw)

        by_role = value.get("payload_bytes_by_role", {})
        by_layer = value.get("payload_bytes_by_layer", {})
        if not isinstance(by_role, Mapping) or not isinstance(by_layer, Mapping):
            raise TypeError("OBS-OH0 payload memory maps must be mappings")
        return cls(
            lane=str(value["lane"]),
            arm=ObserverArm(str(value["arm"])),
            observer_enabled=bool(value["observer_enabled"]),
            model_seed=int(value["model_seed"]),
            batch_index=int(value["batch_index"]),
            source_git_commit=str(value["source_git_commit"]),
            source_git_branch=str(value["source_git_branch"]),
            experiment_image=str(value["experiment_image"]),
            device_name=str(value["device_name"]),
            dtype=str(value["dtype"]),
            payload_bytes=int(value["payload_bytes"]),
            payload_records=int(value["payload_records"]),
            payload_bytes_by_role={
                str(key): int(item) for key, item in by_role.items()
            },
            payload_bytes_by_layer={
                str(key): int(item) for key, item in by_layer.items()
            },
            observer_validation_passed=bool(
                value["observer_validation_passed"]
            ),
            baseline_rss_bytes=optional_int("baseline_rss_bytes"),
            peak_rss_bytes=optional_int("peak_rss_bytes"),
            final_rss_bytes=optional_int("final_rss_bytes"),
            vm_hwm_bytes=optional_int("vm_hwm_bytes"),
            incremental_peak_rss_bytes=optional_int(
                "incremental_peak_rss_bytes"
            ),
            incremental_final_rss_bytes=optional_int(
                "incremental_final_rss_bytes"
            ),
            baseline_allocated_bytes=optional_int(
                "baseline_allocated_bytes"
            ),
            baseline_reserved_bytes=optional_int("baseline_reserved_bytes"),
            peak_allocated_bytes=optional_int("peak_allocated_bytes"),
            peak_reserved_bytes=optional_int("peak_reserved_bytes"),
            current_allocated_bytes=optional_int("current_allocated_bytes"),
            current_reserved_bytes=optional_int("current_reserved_bytes"),
            incremental_peak_allocated_bytes=optional_int(
                "incremental_peak_allocated_bytes"
            ),
            incremental_peak_reserved_bytes=optional_int(
                "incremental_peak_reserved_bytes"
            ),
        )


@dataclass(frozen=True)
class MemoryPairRecord:
    """Paired isolated memory executions."""

    order: ExecutionOrder
    reference: MemoryExecutionResult
    candidate: MemoryExecutionResult

    def __post_init__(self) -> None:
        comparable = (
            self.reference.lane == self.candidate.lane
            and self.reference.arm is self.candidate.arm
            and self.reference.model_seed == self.candidate.model_seed
            and self.reference.batch_index == self.candidate.batch_index
            and self.reference.source_git_commit == self.candidate.source_git_commit
            and self.reference.source_git_branch == self.candidate.source_git_branch
            and self.reference.experiment_image == self.candidate.experiment_image
            and self.reference.device_name == self.candidate.device_name
            and self.reference.dtype == self.candidate.dtype
            and not self.reference.observer_enabled
            and self.candidate.observer_enabled
        )
        if not comparable:
            raise ValueError("OBS-OH0 memory executions do not form a valid pair")

    @property
    def key(self) -> str:
        return (
            f"{self.reference.lane}:{self.reference.arm.value}:"
            f"s{self.reference.model_seed}:b{self.reference.batch_index}"
        )

    @property
    def paired_peak_memory_difference_bytes(self) -> int:
        if self.reference.lane == "cpu":
            reference = self.reference.incremental_peak_rss_bytes
            candidate = self.candidate.incremental_peak_rss_bytes
        else:
            reference = self.reference.incremental_peak_allocated_bytes
            candidate = self.candidate.incremental_peak_allocated_bytes
        if reference is None or candidate is None:
            raise RuntimeError("OBS-OH0 memory pair is missing its primary metric")
        return candidate - reference

    @property
    def memory_accounting_residual_bytes(self) -> int:
        return (
            self.paired_peak_memory_difference_bytes
            - self.candidate.payload_bytes
        )

    @property
    def passed_structure(self) -> bool:
        return self.reference.valid and self.candidate.valid

    def to_record(self) -> dict[str, Any]:
        return {
            "benchmark_schema_id": BENCHMARK_SCHEMA_ID,
            "observer_schema_id": OBSERVER_SCHEMA_ID,
            "key": self.key,
            "lane": self.reference.lane,
            "arm": self.reference.arm.value,
            "model_seed": self.reference.model_seed,
            "batch_index": self.reference.batch_index,
            "execution_order": self.order.value,
            "source_git_commit": self.reference.source_git_commit,
            "source_git_branch": self.reference.source_git_branch,
            "experiment_image": self.reference.experiment_image,
            "device_name": self.reference.device_name,
            "dtype": self.reference.dtype,
            "reference_baseline_rss_bytes": self.reference.baseline_rss_bytes,
            "reference_peak_rss_bytes": self.reference.peak_rss_bytes,
            "reference_final_rss_bytes": self.reference.final_rss_bytes,
            "reference_vm_hwm_bytes": self.reference.vm_hwm_bytes,
            "candidate_baseline_rss_bytes": self.candidate.baseline_rss_bytes,
            "candidate_peak_rss_bytes": self.candidate.peak_rss_bytes,
            "candidate_final_rss_bytes": self.candidate.final_rss_bytes,
            "candidate_vm_hwm_bytes": self.candidate.vm_hwm_bytes,
            "reference_incremental_peak_rss_bytes": (
                self.reference.incremental_peak_rss_bytes
            ),
            "candidate_incremental_peak_rss_bytes": (
                self.candidate.incremental_peak_rss_bytes
            ),
            "reference_baseline_allocated_bytes": (
                self.reference.baseline_allocated_bytes
            ),
            "candidate_baseline_allocated_bytes": (
                self.candidate.baseline_allocated_bytes
            ),
            "reference_peak_allocated_bytes": (
                self.reference.peak_allocated_bytes
            ),
            "candidate_peak_allocated_bytes": (
                self.candidate.peak_allocated_bytes
            ),
            "reference_current_allocated_bytes": (
                self.reference.current_allocated_bytes
            ),
            "candidate_current_allocated_bytes": (
                self.candidate.current_allocated_bytes
            ),
            "reference_incremental_peak_allocated_bytes": (
                self.reference.incremental_peak_allocated_bytes
            ),
            "candidate_incremental_peak_allocated_bytes": (
                self.candidate.incremental_peak_allocated_bytes
            ),
            "reference_baseline_reserved_bytes": (
                self.reference.baseline_reserved_bytes
            ),
            "candidate_baseline_reserved_bytes": (
                self.candidate.baseline_reserved_bytes
            ),
            "reference_peak_reserved_bytes": (
                self.reference.peak_reserved_bytes
            ),
            "candidate_peak_reserved_bytes": (
                self.candidate.peak_reserved_bytes
            ),
            "reference_current_reserved_bytes": (
                self.reference.current_reserved_bytes
            ),
            "candidate_current_reserved_bytes": (
                self.candidate.current_reserved_bytes
            ),
            "reference_incremental_peak_reserved_bytes": (
                self.reference.incremental_peak_reserved_bytes
            ),
            "candidate_incremental_peak_reserved_bytes": (
                self.candidate.incremental_peak_reserved_bytes
            ),
            "candidate_payload_bytes": self.candidate.payload_bytes,
            "candidate_payload_records": self.candidate.payload_records,
            "candidate_payload_bytes_by_role": json.dumps(
                self.candidate.payload_bytes_by_role,
                sort_keys=True,
            ),
            "candidate_payload_bytes_by_layer": json.dumps(
                self.candidate.payload_bytes_by_layer,
                sort_keys=True,
            ),
            "paired_peak_memory_difference_bytes": (
                self.paired_peak_memory_difference_bytes
            ),
            "memory_accounting_residual_bytes": (
                self.memory_accounting_residual_bytes
            ),
            "passed_structure": self.passed_structure,
        }


@dataclass(frozen=True)
class SeedMemorySummary:
    """Seed-level memory budget decision."""

    arm: ObserverArm
    model_seed: int
    paired_records: int
    median_payload_bytes: float
    median_paired_peak_memory_difference_bytes: float
    median_memory_accounting_residual_bytes: float
    allowed_paired_peak_memory_difference_bytes: float
    payload_budget_passed: bool
    peak_memory_budget_passed: bool
    passed_structure: bool

    @property
    def passed(self) -> bool:
        return (
            self.payload_budget_passed
            and self.peak_memory_budget_passed
            and self.passed_structure
        )

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["arm"] = self.arm.value
        result["passed"] = self.passed
        return result


@dataclass(frozen=True)
class ArmMemorySummary:
    """Arm-level aggregation of seed memory summaries."""

    arm: ObserverArm
    seed_summaries: tuple[SeedMemorySummary, ...]
    primary_median_payload_bytes: float
    primary_median_paired_peak_memory_difference_bytes: float
    primary_median_memory_accounting_residual_bytes: float

    @property
    def passed(self) -> bool:
        return bool(self.seed_summaries) and all(
            item.passed for item in self.seed_summaries
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "arm": self.arm.value,
            "seed_summaries": [item.to_dict() for item in self.seed_summaries],
            "primary_median_payload_bytes": self.primary_median_payload_bytes,
            "primary_median_paired_peak_memory_difference_bytes": (
                self.primary_median_paired_peak_memory_difference_bytes
            ),
            "primary_median_memory_accounting_residual_bytes": (
                self.primary_median_memory_accounting_residual_bytes
            ),
            "payload_limit_bytes": PAYLOAD_LIMIT_BYTES,
            "passed": self.passed,
        }


def read_proc_status_bytes(
    field: str,
    *,
    path: Path = Path("/proc/self/status"),
) -> int:
    """Read one Linux /proc status memory field expressed in bytes."""
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.startswith(f"{field}:"):
            continue
        parts = raw_line.split()
        if len(parts) != 3 or parts[2] != "kB":
            raise RuntimeError(f"Unexpected /proc status format for {field}")
        value = int(parts[1])
        if value < 0:
            raise RuntimeError(f"Negative /proc status value for {field}")
        return value * 1024
    raise RuntimeError(f"Missing {field} in {path}")


class CpuRssSampler:
    """Sample Linux VmRSS while an isolated memory execution is active."""

    def __init__(self, interval_ms: float) -> None:
        if not 0.0 < interval_ms <= 1.0:
            raise ValueError("RSS sampler interval must be within (0, 1] ms")
        self._interval_seconds = interval_ms / 1000.0
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._peak_bytes = 0
        self._error: BaseException | None = None

    @property
    def peak_bytes(self) -> int:
        if self._error is not None:
            raise RuntimeError("CPU RSS sampler failed") from self._error
        return self._peak_bytes

    def start(self) -> None:
        if self._thread is not None:
            raise RuntimeError("CPU RSS sampler has already been started")
        self._peak_bytes = read_proc_status_bytes("VmRSS")
        self._thread = threading.Thread(
            target=self._sample,
            name="obs-oh0-rss-sampler",
            daemon=True,
        )
        self._thread.start()

    def _sample(self) -> None:
        try:
            while not self._stop.is_set():
                self._peak_bytes = max(
                    self._peak_bytes,
                    read_proc_status_bytes("VmRSS"),
                )
                self._stop.wait(self._interval_seconds)
            self._peak_bytes = max(
                self._peak_bytes,
                read_proc_status_bytes("VmRSS"),
            )
        except BaseException as error:
            self._error = error

    def stop(self) -> None:
        if self._thread is None:
            raise RuntimeError("CPU RSS sampler has not been started")
        self._stop.set()
        self._thread.join()
        self._thread = None
        if self._error is not None:
            raise RuntimeError("CPU RSS sampler failed") from self._error


def payload_memory_breakdown(
    records: Iterable[ObserverPayload],
) -> tuple[int, dict[str, int], dict[str, int]]:
    """Calculate exact retained payload bytes by role and layer."""
    total = 0
    by_role: dict[str, int] = {}
    by_layer: dict[str, int] = {}
    for record in records:
        size = record.tensor.numel() * record.tensor.element_size()
        total += size
        by_role[record.role] = by_role.get(record.role, 0) + size
        layer_key = str(record.layer_index)
        by_layer[layer_key] = by_layer.get(layer_key, 0) + size
    return total, by_role, by_layer


def _matched_noop_start() -> None:
    """Match the reference observer setup boundary."""


def _matched_noop_close() -> None:
    """Match the reference observer cleanup boundary."""


def measure_memory_execution(
    model: nn.Sequential,
    inputs: torch.Tensor,
    targets: torch.Tensor,
    *,
    request: MemoryWorkerRequest,
    torch2pc_dir: str | Path,
    device: torch.device,
    dtype: torch.dtype,
    device_name: str,
) -> MemoryExecutionResult:
    """Measure one isolated CPU-RSS or ROCm-allocator execution."""
    observer: PassiveLayerObserver | None = None
    baseline_rss: int | None = None
    peak_rss: int | None = None
    final_rss: int | None = None
    vm_hwm: int | None = None
    incremental_peak_rss: int | None = None
    incremental_final_rss: int | None = None
    baseline_allocated: int | None = None
    baseline_reserved: int | None = None
    peak_allocated: int | None = None
    peak_reserved: int | None = None
    current_allocated: int | None = None
    current_reserved: int | None = None
    incremental_peak_allocated: int | None = None
    incremental_peak_reserved: int | None = None
    sampler: CpuRssSampler | None = None

    if request.lane == "cpu":
        baseline_rss = read_proc_status_bytes("VmRSS")
        sampler = CpuRssSampler(request.rss_sampler_interval_ms)
        sampler.start()
    else:
        torch.cuda.synchronize(device)
        baseline_allocated = int(torch.cuda.memory_allocated(device))
        baseline_reserved = int(torch.cuda.memory_reserved(device))
        torch.cuda.reset_peak_memory_stats(device)

    try:
        if request.observer_enabled:
            observer = PassiveLayerObserver(model)
            observer.start()
        else:
            _matched_noop_start()
        run_registered_backward(
            model,
            inputs,
            targets,
            arm=request.arm,
            torch2pc_dir=torch2pc_dir,
        )
    finally:
        if observer is not None:
            observer.close()
        else:
            _matched_noop_close()

    if request.lane == "cpu":
        if sampler is None or baseline_rss is None:
            raise RuntimeError("OBS-OH0 CPU sampler was not initialized")
        sampler.stop()
        peak_rss = sampler.peak_bytes
        final_rss = read_proc_status_bytes("VmRSS")
        vm_hwm = read_proc_status_bytes("VmHWM")
        incremental_peak_rss = max(0, peak_rss - baseline_rss)
        incremental_final_rss = max(0, final_rss - baseline_rss)
    else:
        torch.cuda.synchronize(device)
        if baseline_allocated is None or baseline_reserved is None:
            raise RuntimeError("OBS-OH0 ROCm baseline was not initialized")
        peak_allocated = int(torch.cuda.max_memory_allocated(device))
        peak_reserved = int(torch.cuda.max_memory_reserved(device))
        current_allocated = int(torch.cuda.memory_allocated(device))
        current_reserved = int(torch.cuda.memory_reserved(device))
        incremental_peak_allocated = max(
            0,
            peak_allocated - baseline_allocated,
        )
        incremental_peak_reserved = max(
            0,
            peak_reserved - baseline_reserved,
        )

    validation = (
        observer.validate(setup_rng_unchanged=True)
        if observer is not None
        else None
    )
    payload_records = observer.records if observer is not None else ()
    payload_bytes, by_role, by_layer = payload_memory_breakdown(payload_records)

    return MemoryExecutionResult(
        lane=request.lane,
        arm=request.arm,
        observer_enabled=request.observer_enabled,
        model_seed=request.model_seed,
        batch_index=request.batch_index,
        source_git_commit=request.source_git_commit,
        source_git_branch=request.source_git_branch,
        experiment_image=request.experiment_image,
        device_name=device_name,
        dtype=str(dtype),
        payload_bytes=payload_bytes,
        payload_records=len(payload_records),
        payload_bytes_by_role=by_role,
        payload_bytes_by_layer=by_layer,
        observer_validation_passed=(
            validation.passed if validation is not None else True
        ),
        baseline_rss_bytes=baseline_rss,
        peak_rss_bytes=peak_rss,
        final_rss_bytes=final_rss,
        vm_hwm_bytes=vm_hwm,
        incremental_peak_rss_bytes=incremental_peak_rss,
        incremental_final_rss_bytes=incremental_final_rss,
        baseline_allocated_bytes=baseline_allocated,
        baseline_reserved_bytes=baseline_reserved,
        peak_allocated_bytes=peak_allocated,
        peak_reserved_bytes=peak_reserved,
        current_allocated_bytes=current_allocated,
        current_reserved_bytes=current_reserved,
        incremental_peak_allocated_bytes=incremental_peak_allocated,
        incremental_peak_reserved_bytes=incremental_peak_reserved,
    )


def _allowed_peak_difference(lane: str, payload_bytes: float) -> float:
    if lane == "cpu":
        return payload_bytes + max(
            float(CPU_ABSOLUTE_TOLERANCE_BYTES),
            CPU_RELATIVE_TOLERANCE * payload_bytes,
        )
    return payload_bytes + max(
        float(GPU_ABSOLUTE_TOLERANCE_BYTES),
        GPU_RELATIVE_TOLERANCE * payload_bytes,
    )


def aggregate_memory_records(
    records: Iterable[MemoryPairRecord],
    *,
    lane: str,
    model_seeds: Iterable[int],
) -> dict[ObserverArm, ArmMemorySummary]:
    """Aggregate paired memory records with seed-level median decisions."""
    pairs = list(records)
    seeds = tuple(model_seeds)
    if not pairs:
        raise ValueError("OBS-OH0 memory aggregation requires records")
    if len({item.key for item in pairs}) != len(pairs):
        raise ValueError("OBS-OH0 memory records contain duplicate keys")
    if any(item.reference.lane != lane for item in pairs):
        raise ValueError("OBS-OH0 memory records contain a lane mismatch")

    result: dict[ObserverArm, ArmMemorySummary] = {}
    for arm in ObserverArm:
        seed_summaries: list[SeedMemorySummary] = []
        arm_pairs = [item for item in pairs if item.reference.arm is arm]
        for seed in seeds:
            seed_pairs = [
                item
                for item in arm_pairs
                if item.reference.model_seed == seed
            ]
            if not seed_pairs:
                raise ValueError(
                    f"OBS-OH0 has no memory records for {arm.value} seed {seed}"
                )
            payloads = [item.candidate.payload_bytes for item in seed_pairs]
            differences = [
                item.paired_peak_memory_difference_bytes for item in seed_pairs
            ]
            residuals = [
                item.memory_accounting_residual_bytes for item in seed_pairs
            ]
            median_payload = float(statistics.median(payloads))
            median_difference = float(statistics.median(differences))
            allowed = _allowed_peak_difference(lane, median_payload)
            seed_summaries.append(
                SeedMemorySummary(
                    arm=arm,
                    model_seed=seed,
                    paired_records=len(seed_pairs),
                    median_payload_bytes=median_payload,
                    median_paired_peak_memory_difference_bytes=median_difference,
                    median_memory_accounting_residual_bytes=float(
                        statistics.median(residuals)
                    ),
                    allowed_paired_peak_memory_difference_bytes=allowed,
                    payload_budget_passed=(
                        all(value <= PAYLOAD_LIMIT_BYTES for value in payloads)
                        and median_payload <= PAYLOAD_LIMIT_BYTES
                    ),
                    peak_memory_budget_passed=(
                        math.isfinite(median_difference)
                        and median_difference <= allowed
                    ),
                    passed_structure=all(
                        item.passed_structure for item in seed_pairs
                    ),
                )
            )

        result[arm] = ArmMemorySummary(
            arm=arm,
            seed_summaries=tuple(seed_summaries),
            primary_median_payload_bytes=float(
                statistics.median(
                    item.median_payload_bytes for item in seed_summaries
                )
            ),
            primary_median_paired_peak_memory_difference_bytes=float(
                statistics.median(
                    item.median_paired_peak_memory_difference_bytes
                    for item in seed_summaries
                )
            ),
            primary_median_memory_accounting_residual_bytes=float(
                statistics.median(
                    item.median_memory_accounting_residual_bytes
                    for item in seed_summaries
                )
            ),
        )
    return result
