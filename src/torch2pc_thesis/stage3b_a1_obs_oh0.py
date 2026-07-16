from __future__ import annotations

import copy
import math
import statistics
import time
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

import torch
import torch.nn as nn

from torch2pc_thesis.stage3b_a1_obs_ni0 import (
    ObserverArm,
    capture_rng_snapshot,
    restore_rng_snapshot,
)
from torch2pc_thesis.stage3b_a1_observer import (
    OBSERVER_SCHEMA_ID,
    ObserverValidation,
    PassiveLayerObserver,
    observer_schema_manifest,
)
from torch2pc_thesis.stage3b_a1_shortcut import (
    JointVjpDiagnostics,
    reduced_shortcut_backward,
)

BENCHMARK_SCHEMA_ID = "stage3b-a1-obs-oh0-v1"
PRIMARY_RUNTIME_RATIO_LIMIT = 1.25
SEED_RUNTIME_RATIO_LIMIT = 1.35


class TimingPhase(StrEnum):
    """Registered timing phases for OBS-OH0."""

    WARMUP = "warmup"
    MEASURED = "measured"


class ExecutionOrder(StrEnum):
    """Deterministic paired observer execution order."""

    OFF_THEN_ON = "off_then_on"
    ON_THEN_OFF = "on_then_off"


@dataclass(frozen=True)
class TimedExecution:
    """One observer-off or observer-on measured execution."""

    observer_enabled: bool
    elapsed_ns: int
    payload_bytes: int
    observer_validation: ObserverValidation | None
    shortcut_diagnostics: JointVjpDiagnostics | None

    @property
    def valid(self) -> bool:
        if self.elapsed_ns <= 0:
            return False
        if self.observer_enabled:
            return bool(
                self.observer_validation is not None
                and self.observer_validation.passed
                and self.payload_bytes > 0
            )
        return self.observer_validation is None and self.payload_bytes == 0


@dataclass(frozen=True)
class TimingPairRecord:
    """One paired observer-off versus observer-on timing record."""

    phase: TimingPhase
    lane: str
    arm: ObserverArm
    model_seed: int
    batch_index: int
    repeat_index: int
    order: ExecutionOrder
    reference: TimedExecution
    candidate: TimedExecution

    @property
    def runtime_delta_ns(self) -> int:
        return self.candidate.elapsed_ns - self.reference.elapsed_ns

    @property
    def runtime_ratio(self) -> float:
        return self.candidate.elapsed_ns / self.reference.elapsed_ns

    @property
    def runtime_overhead_fraction(self) -> float:
        return self.runtime_ratio - 1.0

    @property
    def key(self) -> str:
        return (
            f"{self.phase.value}:{self.lane}:{self.arm.value}:"
            f"s{self.model_seed}:b{self.batch_index}:r{self.repeat_index}"
        )

    @property
    def passed_structure(self) -> bool:
        return (
            self.reference.valid
            and self.candidate.valid
            and math.isfinite(self.runtime_ratio)
            and self.runtime_ratio > 0.0
        )

    def to_record(self) -> dict[str, Any]:
        validation = self.candidate.observer_validation
        return {
            "benchmark_schema_id": BENCHMARK_SCHEMA_ID,
            "observer_schema_id": OBSERVER_SCHEMA_ID,
            "key": self.key,
            "phase": self.phase.value,
            "lane": self.lane,
            "arm": self.arm.value,
            "model_seed": self.model_seed,
            "batch_index": self.batch_index,
            "repeat_index": self.repeat_index,
            "execution_order": self.order.value,
            "reference_elapsed_ns": self.reference.elapsed_ns,
            "candidate_elapsed_ns": self.candidate.elapsed_ns,
            "runtime_delta_ns": self.runtime_delta_ns,
            "runtime_ratio": self.runtime_ratio,
            "runtime_overhead_fraction": self.runtime_overhead_fraction,
            "candidate_payload_bytes": self.candidate.payload_bytes,
            "candidate_observer_records": (
                validation.observed_records if validation is not None else 0
            ),
            "candidate_cleanup_complete": (
                validation.cleanup_complete if validation is not None else False
            ),
            "passed_structure": self.passed_structure,
        }


@dataclass(frozen=True)
class SeedRuntimeSummary:
    """Seed-level median runtime ratio."""

    arm: ObserverArm
    model_seed: int
    paired_records: int
    median_runtime_ratio: float
    median_runtime_delta_ns: float
    passed: bool

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["arm"] = self.arm.value
        return result


@dataclass(frozen=True)
class ArmRuntimeSummary:
    """Registered arm-level runtime estimand and budget decision."""

    arm: ObserverArm
    seed_summaries: tuple[SeedRuntimeSummary, ...]
    primary_runtime_ratio: float
    min_seed_median_runtime_ratio: float
    max_seed_median_runtime_ratio: float
    median_absolute_runtime_delta_ns: float
    off_first_median_runtime_ratio: float
    on_first_median_runtime_ratio: float
    primary_budget_passed: bool
    seed_budget_passed: bool

    @property
    def passed(self) -> bool:
        return (
            bool(self.seed_summaries)
            and all(item.passed for item in self.seed_summaries)
            and self.primary_budget_passed
            and self.seed_budget_passed
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "arm": self.arm.value,
            "seed_summaries": [item.to_dict() for item in self.seed_summaries],
            "primary_runtime_ratio": self.primary_runtime_ratio,
            "min_seed_median_runtime_ratio": self.min_seed_median_runtime_ratio,
            "max_seed_median_runtime_ratio": self.max_seed_median_runtime_ratio,
            "median_absolute_runtime_delta_ns": (
                self.median_absolute_runtime_delta_ns
            ),
            "off_first_median_runtime_ratio": (
                self.off_first_median_runtime_ratio
            ),
            "on_first_median_runtime_ratio": (
                self.on_first_median_runtime_ratio
            ),
            "primary_runtime_ratio_limit": PRIMARY_RUNTIME_RATIO_LIMIT,
            "seed_runtime_ratio_limit": SEED_RUNTIME_RATIO_LIMIT,
            "primary_budget_passed": self.primary_budget_passed,
            "seed_budget_passed": self.seed_budget_passed,
            "passed": self.passed,
        }


def benchmark_schema_manifest(
    *,
    execution_scope: str,
    top_level_layers: int,
    model_seeds: Iterable[int],
    batches_per_seed: int,
    timing_repeats: int,
    warmup_pairs: int,
    rss_sampler_interval_ms: float,
) -> dict[str, Any]:
    """Return the frozen OBS-OH0 benchmark schema."""
    seeds = list(model_seeds)
    if execution_scope not in {"smoke", "confirmatory", "development"}:
        raise ValueError("OBS-OH0 execution scope is invalid")
    if top_level_layers < 1:
        raise ValueError("OBS-OH0 requires at least one top-level layer")
    if not seeds:
        raise ValueError("OBS-OH0 requires at least one model seed")
    if batches_per_seed < 1 or timing_repeats < 1 or warmup_pairs < 1:
        raise ValueError("OBS-OH0 repeat counts must be positive")
    if not 0.0 < rss_sampler_interval_ms <= 1.0:
        raise ValueError("RSS sampler interval must be within (0, 1] ms")

    arms = list(ObserverArm)
    return {
        "benchmark_schema_id": BENCHMARK_SCHEMA_ID,
        "execution_scope": execution_scope,
        "observer_schema": observer_schema_manifest(top_level_layers),
        "timing_clock": "time.perf_counter_ns",
        "timing_region": {
            "included": [
                "matched observer lifecycle setup",
                "registered backward path",
                "observer cleanup",
                "ROCm synchronization boundary",
            ],
            "excluded": [
                "dataloader",
                "model construction and deepcopy",
                "device transfer",
                "optimizer construction and step",
                "endpoint comparison",
                "payload validation and serialization",
                "disk I/O",
            ],
        },
        "paired_order_rule": (
            "parity = model_seed + batch_index + repeat_index + arm_index"
        ),
        "model_seeds": seeds,
        "batches_per_seed": batches_per_seed,
        "timing_repeats": timing_repeats,
        "warmup_pairs_per_lane_arm": warmup_pairs,
        "memory_pairs_per_seed_batch_arm": 1,
        "rss_sampler_interval_ms": rss_sampler_interval_ms,
        "expected_measured_timing_pairs_per_lane": (
            len(seeds) * batches_per_seed * len(arms) * timing_repeats
        ),
        "expected_memory_pairs_per_lane": (
            len(seeds) * batches_per_seed * len(arms)
        ),
        "record_keys": {
            "timing": (
                "{phase}:{lane}:{arm}:s{model_seed}:"
                "b{batch_index}:r{repeat_index}"
            ),
            "memory": "{lane}:{arm}:s{model_seed}:b{batch_index}",
        },
        "aggregation": {
            "independent_unit": "model_seed",
            "within_seed_repeats": ["batch_index", "repeat_index"],
            "runtime_primary_estimand": (
                "median of three seed-level median runtime ratios"
            ),
            "memory_primary_estimand": (
                "median of three seed-level median paired peak differences"
            ),
            "outlier_policy": "retain all measured records",
        },
        "output_artifacts": [
            "obs_oh0_guard_records.csv",
            "obs_oh0_timing_records.csv",
            "obs_oh0_timing_summary.json",
            "obs_oh0_memory_records.csv",
            "obs_oh0_memory_summary.json",
            "obs_oh0_benchmark_schema.json",
            "obs_oh0_summary.json",
        ],
        "runtime_budget": {
            "primary_runtime_ratio_max": PRIMARY_RUNTIME_RATIO_LIMIT,
            "max_seed_median_runtime_ratio": SEED_RUNTIME_RATIO_LIMIT,
        },
    }


def execution_order_for(
    *,
    arm: ObserverArm,
    model_seed: int,
    batch_index: int,
    repeat_index: int,
) -> ExecutionOrder:
    """Apply the preregistered deterministic parity rule."""
    arm_index = 0 if arm is ObserverArm.FIXEDPRED else 1
    parity = model_seed + batch_index + repeat_index + arm_index
    return (
        ExecutionOrder.OFF_THEN_ON
        if parity % 2 == 0
        else ExecutionOrder.ON_THEN_OFF
    )


def run_registered_backward(
    model: nn.Sequential,
    inputs: torch.Tensor,
    targets: torch.Tensor,
    *,
    arm: ObserverArm,
    torch2pc_dir: str | Path,
) -> JointVjpDiagnostics | None:
    """Execute exactly one registered OBS-OH0 computational path."""
    if arm is ObserverArm.FIXEDPRED:
        from torch2pc_thesis.pc_methods import backward_for_method

        model.zero_grad(set_to_none=True)
        backward_for_method(
            model,
            nn.CrossEntropyLoss(),
            inputs,
            targets,
            method="fixedpred",
            torch2pc_dir=torch2pc_dir,
            eta=1.0,
            inference_steps=len(model),
        )
        return None

    _, diagnostics = reduced_shortcut_backward(
        model,
        nn.CrossEntropyLoss(),
        inputs,
        targets,
    )
    return diagnostics


def _synchronize(device: torch.device) -> None:
    if device.type == "cuda":
        torch.cuda.synchronize(device)


def _matched_noop_start() -> None:
    """Match the reference lifecycle boundary without installing hooks."""


def _matched_noop_close() -> None:
    """Match the reference cleanup boundary without installed hooks."""


def run_timed_execution(
    model: nn.Sequential,
    inputs: torch.Tensor,
    targets: torch.Tensor,
    *,
    arm: ObserverArm,
    torch2pc_dir: str | Path,
    observer_enabled: bool,
    device: torch.device,
) -> TimedExecution:
    """Measure one path with observer lifecycle inside the timing boundary."""
    observer: PassiveLayerObserver | None = None

    _synchronize(device)
    start_ns = time.perf_counter_ns()
    try:
        if observer_enabled:
            observer = PassiveLayerObserver(model)
            observer.start()
        else:
            _matched_noop_start()
        diagnostics = run_registered_backward(
            model,
            inputs,
            targets,
            arm=arm,
            torch2pc_dir=torch2pc_dir,
        )
    finally:
        if observer is not None:
            observer.close()
        else:
            _matched_noop_close()
    _synchronize(device)
    end_ns = time.perf_counter_ns()

    validation = (
        observer.validate(setup_rng_unchanged=True)
        if observer is not None
        else None
    )
    payload_bytes = (
        sum(
            record.tensor.numel() * record.tensor.element_size()
            for record in observer.records
        )
        if observer is not None
        else 0
    )
    return TimedExecution(
        observer_enabled=observer_enabled,
        elapsed_ns=end_ns - start_ns,
        payload_bytes=payload_bytes,
        observer_validation=validation,
        shortcut_diagnostics=diagnostics,
    )


def run_timing_pair(
    base_model: nn.Sequential,
    inputs: torch.Tensor,
    targets: torch.Tensor,
    *,
    phase: TimingPhase,
    lane: str,
    arm: ObserverArm,
    model_seed: int,
    batch_index: int,
    repeat_index: int,
    torch2pc_dir: str | Path,
    device: torch.device,
) -> TimingPairRecord:
    """Run a deterministic observer-off/on timing pair."""
    order = execution_order_for(
        arm=arm,
        model_seed=model_seed,
        batch_index=batch_index,
        repeat_index=repeat_index,
    )
    models = {
        False: copy.deepcopy(base_model),
        True: copy.deepcopy(base_model),
    }
    input_copies = {
        False: inputs.detach().clone(),
        True: inputs.detach().clone(),
    }
    target_copies = {
        False: targets.detach().clone(),
        True: targets.detach().clone(),
    }
    paired_rng = capture_rng_snapshot()
    execution_sequence = (
        (False, True)
        if order is ExecutionOrder.OFF_THEN_ON
        else (True, False)
    )
    executions: dict[bool, TimedExecution] = {}

    for observer_enabled in execution_sequence:
        restore_rng_snapshot(paired_rng)
        executions[observer_enabled] = run_timed_execution(
            models[observer_enabled],
            input_copies[observer_enabled],
            target_copies[observer_enabled],
            arm=arm,
            torch2pc_dir=torch2pc_dir,
            observer_enabled=observer_enabled,
            device=device,
        )

    return TimingPairRecord(
        phase=phase,
        lane=lane,
        arm=arm,
        model_seed=model_seed,
        batch_index=batch_index,
        repeat_index=repeat_index,
        order=order,
        reference=executions[False],
        candidate=executions[True],
    )


def aggregate_timing_records(
    records: Iterable[TimingPairRecord],
    *,
    model_seeds: Iterable[int],
) -> dict[ObserverArm, ArmRuntimeSummary]:
    """Aggregate measured records with model seed as the independent unit."""
    measured = [item for item in records if item.phase is TimingPhase.MEASURED]
    seeds = tuple(model_seeds)
    if not measured:
        raise ValueError("OBS-OH0 timing aggregation requires measured records")
    if len({item.key for item in measured}) != len(measured):
        raise ValueError("OBS-OH0 timing records contain duplicate keys")

    summaries: dict[ObserverArm, ArmRuntimeSummary] = {}
    for arm in ObserverArm:
        seed_summaries: list[SeedRuntimeSummary] = []
        arm_records = [item for item in measured if item.arm is arm]
        for seed in seeds:
            seed_records = [
                item for item in arm_records if item.model_seed == seed
            ]
            if not seed_records:
                raise ValueError(
                    f"OBS-OH0 has no timing records for {arm.value} seed {seed}"
                )
            ratios = [item.runtime_ratio for item in seed_records]
            deltas = [item.runtime_delta_ns for item in seed_records]
            structurally_valid = all(item.passed_structure for item in seed_records)
            median_ratio = float(statistics.median(ratios))
            seed_summaries.append(
                SeedRuntimeSummary(
                    arm=arm,
                    model_seed=seed,
                    paired_records=len(seed_records),
                    median_runtime_ratio=median_ratio,
                    median_runtime_delta_ns=float(statistics.median(deltas)),
                    passed=(
                        structurally_valid
                        and math.isfinite(median_ratio)
                        and median_ratio <= SEED_RUNTIME_RATIO_LIMIT
                    ),
                )
            )

        seed_ratios = [item.median_runtime_ratio for item in seed_summaries]
        absolute_deltas = [
            abs(item.runtime_delta_ns) for item in arm_records
        ]
        off_first_ratios = [
            item.runtime_ratio
            for item in arm_records
            if item.order is ExecutionOrder.OFF_THEN_ON
        ]
        on_first_ratios = [
            item.runtime_ratio
            for item in arm_records
            if item.order is ExecutionOrder.ON_THEN_OFF
        ]
        if not off_first_ratios or not on_first_ratios:
            raise ValueError(
                f"OBS-OH0 timing order is not balanced for {arm.value}"
            )
        primary_ratio = float(statistics.median(seed_ratios))
        max_seed_ratio = max(seed_ratios)
        summaries[arm] = ArmRuntimeSummary(
            arm=arm,
            seed_summaries=tuple(seed_summaries),
            primary_runtime_ratio=primary_ratio,
            min_seed_median_runtime_ratio=min(seed_ratios),
            max_seed_median_runtime_ratio=max_seed_ratio,
            median_absolute_runtime_delta_ns=float(
                statistics.median(absolute_deltas)
            ),
            off_first_median_runtime_ratio=float(
                statistics.median(off_first_ratios)
            ),
            on_first_median_runtime_ratio=float(
                statistics.median(on_first_ratios)
            ),
            primary_budget_passed=(
                math.isfinite(primary_ratio)
                and primary_ratio <= PRIMARY_RUNTIME_RATIO_LIMIT
            ),
            seed_budget_passed=(
                math.isfinite(max_seed_ratio)
                and max_seed_ratio <= SEED_RUNTIME_RATIO_LIMIT
            ),
        )
    return summaries
