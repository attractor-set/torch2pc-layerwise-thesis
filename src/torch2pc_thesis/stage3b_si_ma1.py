"""Stage 3B SI-MA1 observer-calibrated timing primitives."""

from __future__ import annotations

import math
import statistics
import time
from collections import Counter, defaultdict
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Final, Literal, cast

import torch

from torch2pc_thesis.stage3b_si_ma0 import (
    REGIONS,
    ModeRunResult,
    NumericalThresholds,
    SIMA0Recorder,
    canonical_json_digest,
    compare_mode_results,
)

CONTRACT_ID: Final[str] = "stage3b-si-ma1-v1"
IMPLEMENTATION_SCHEMA_ID: Final[str] = "stage3b-si-ma1-implementation-v1"
PREREGISTRATION_TAG: Final[str] = "stage3b-si-ma1-prereg-v1"
PREREGISTRATION_COMMIT: Final[str] = (
    "5b8adfb404b5dd7f1a11d778c0d531e6e2b4c69b"
)
TORCH2PC_COMMIT: Final[str] = (
    "b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4"
)

ArmLabel = Literal["A", "B", "C"]
ARM_LABELS: Final[tuple[ArmLabel, ...]] = ("A", "B", "C")
ORDER_PERMUTATIONS: Final[tuple[str, ...]] = (
    "ABC",
    "BCA",
    "CAB",
    "ACB",
    "CBA",
    "BAC",
)


class SIMA1Error(RuntimeError):
    """Raised when a frozen SI-MA1 invariant is violated."""


@dataclass(frozen=True)
class BlockEstimand:
    """Registered timing quantities for one matched A/B/C block."""

    baseline_time_ms: float
    calibration_time_ms: float
    live_time_ms: float
    live_region_time_ms: float
    observer_cost_time_ms: float
    live_unattributed_time_ms: float
    excess_time_ms: float
    calibrated_excess_gap: float

    def to_record(self) -> dict[str, float]:
        return asdict(self)


@dataclass(frozen=True)
class RecorderTopology:
    """Observed B/C instrumentation topology for one measured arm block."""

    measured_step_count: int
    hook_invocation_count: int
    outer_step_event_pair_count: int
    internal_region_occurrence_count: int
    internal_region_record_count: int
    total_timer_count: int
    vjp_call_count: int
    saved_tensor_count: int
    saved_tensor_bytes: int
    pending_buffer_write_count: int
    finalized_buffer_write_count: int
    block_synchronization_count: int
    instrumentation_configuration_hash: str

    def to_record(self, *, prefix: str) -> dict[str, Any]:
        return {f"{prefix}{key}": value for key, value in asdict(self).items()}


@dataclass
class _PendingOuterStep:
    start_ns: int | None = None
    end_ns: int | None = None
    start_event: Any | None = None
    end_event: Any | None = None


class DeferredArmTimer:
    """Resolve all outer step timings after one arm-block synchronization."""

    def __init__(
        self,
        device: torch.device,
        *,
        event_factory: Callable[[], Any] | None = None,
        synchronize: Callable[[], None] | None = None,
        clock_ns: Callable[[], int] = time.perf_counter_ns,
    ) -> None:
        self.device = device
        self._clock_ns = clock_ns
        self._event_factory = event_factory
        self._synchronize = synchronize
        self._pending: list[_PendingOuterStep] = []
        self._finalized = False
        self.synchronization_count = 0

    def _new_event(self) -> Any:
        if self._event_factory is not None:
            return self._event_factory()
        return torch.cuda.Event(enable_timing=True)

    @contextmanager
    def step(self) -> Iterator[None]:
        if self._finalized:
            raise SIMA1Error("cannot add timing after arm-block finalization")
        pending = _PendingOuterStep()
        if self.device.type == "cuda":
            pending.start_event = self._new_event()
            pending.end_event = self._new_event()
            pending.start_event.record()
        else:
            pending.start_ns = self._clock_ns()
        try:
            yield
        finally:
            if self.device.type == "cuda":
                if pending.end_event is None:
                    raise SIMA1Error("outer timing end event is missing")
                pending.end_event.record()
            else:
                pending.end_ns = self._clock_ns()
            self._pending.append(pending)

    def finalize(self) -> list[float]:
        if self._finalized:
            raise SIMA1Error("arm-block timing was finalized twice")
        if not self._pending:
            raise SIMA1Error("arm-block timing has no measured steps")
        if self.device.type == "cuda":
            if self._synchronize is not None:
                self._synchronize()
            else:
                torch.cuda.synchronize(self.device)
            self.synchronization_count += 1
        durations: list[float] = []
        for pending in self._pending:
            if self.device.type == "cuda":
                if pending.start_event is None or pending.end_event is None:
                    raise SIMA1Error("outer timing event pair is incomplete")
                duration_ms = float(
                    pending.start_event.elapsed_time(pending.end_event)
                )
            else:
                if pending.start_ns is None or pending.end_ns is None:
                    raise SIMA1Error("outer CPU timing pair is incomplete")
                duration_ms = (pending.end_ns - pending.start_ns) / 1_000_000.0
            if not math.isfinite(duration_ms) or duration_ms < 0.0:
                raise SIMA1Error("outer arm timing must be finite and nonnegative")
            durations.append(duration_ms)
        self._finalized = True
        return durations


def load_contract(path: Path) -> dict[str, Any]:
    """Load and validate the frozen SI-MA1 contract."""

    import json

    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SIMA1Error("SI-MA1 contract must be a JSON object")
    if value.get("contract_id") != CONTRACT_ID:
        raise SIMA1Error("unexpected SI-MA1 contract id")
    if value.get("status") != "frozen_preregistration":
        raise SIMA1Error("SI-MA1 contract is not frozen")
    balanced = value.get("balanced_order")
    if not isinstance(balanced, dict):
        raise SIMA1Error("SI-MA1 balanced-order definition is missing")
    if tuple(balanced.get("permutations", ())) != ORDER_PERMUTATIONS:
        raise SIMA1Error("SI-MA1 permutation list differs from preregistration")
    if balanced.get("blocks_per_model_seed_batch") != 6:
        raise SIMA1Error("SI-MA1 requires six matched blocks")
    timing = value.get("timing_protocol")
    if not isinstance(timing, dict):
        raise SIMA1Error("SI-MA1 timing protocol is missing")
    if timing.get("required_sync_point") != "end_of_arm_block":
        raise SIMA1Error("SI-MA1 synchronization boundary differs")
    if timing.get("per_region_device_synchronization") is not False:
        raise SIMA1Error("SI-MA1 forbids per-region synchronization")
    estimand = value.get("primary_estimand")
    if not isinstance(estimand, dict):
        raise SIMA1Error("SI-MA1 primary estimand is missing")
    expected = {
        "observer_cost_time": "H = B - A",
        "live_unattributed_time": "R = C - K",
        "excess_time": "E = R - H = (C - K) - (B - A)",
        "calibrated_excess_gap": "D = E / max(A, epsilon)",
    }
    for key, formula in expected.items():
        if estimand.get(key) != formula:
            raise SIMA1Error(f"SI-MA1 formula mismatch: {key}")
    if float(estimand.get("excess_margin", math.nan)) != 0.01:
        raise SIMA1Error("SI-MA1 excess margin differs")
    boundary = value.get("ecz_evaluator_boundary")
    if not isinstance(boundary, dict) or boundary.get("included_in_si_ma1") is not False:
        raise SIMA1Error("SI-MA1 must exclude the ECZ evaluator")
    return cast(dict[str, Any], value)


def thresholds_for_si_ma1(contract: Mapping[str, Any]) -> NumericalThresholds:
    """Load the registered float32 profile for CPU/ROCm structural checks."""

    root = contract.get("numerical_thresholds")
    if not isinstance(root, Mapping):
        raise SIMA1Error("SI-MA1 numerical thresholds are missing")
    raw = root.get("rocm_float32")
    if not isinstance(raw, Mapping):
        raise SIMA1Error("SI-MA1 float32 threshold profile is missing")
    return NumericalThresholds(
        zero_atol=float(raw["zero_atol"]),
        max_relative_l2=float(raw["max_relative_l2"]),
        max_abs=float(raw["max_abs"]),
        min_cosine=float(raw["min_cosine"]),
    )


def balanced_orders(model_seed: int, batch_id: int) -> tuple[str, ...]:
    offset = (model_seed + batch_id) % len(ORDER_PERMUTATIONS)
    return ORDER_PERMUTATIONS[offset:] + ORDER_PERMUTATIONS[:offset]


def validate_balanced_orders(
    orders: Sequence[str],
    *,
    model_seed: int,
    batch_id: int,
) -> bool:
    if tuple(orders) != balanced_orders(model_seed, batch_id):
        return False
    if Counter(orders) != Counter(ORDER_PERMUTATIONS):
        return False
    return all(
        Counter(order[position] for order in orders)
        == Counter({"A": 2, "B": 2, "C": 2})
        for position in range(3)
    )


def compute_block_estimand(
    *,
    baseline_time_ms: float,
    calibration_time_ms: float,
    live_time_ms: float,
    live_region_time_ms: float,
    epsilon: float,
) -> BlockEstimand:
    values = (
        baseline_time_ms,
        calibration_time_ms,
        live_time_ms,
        live_region_time_ms,
    )
    if not all(math.isfinite(value) for value in (*values, epsilon)):
        raise SIMA1Error("SI-MA1 timing contains a non-finite value")
    if min(values) < 0.0 or epsilon <= 0.0:
        raise SIMA1Error("SI-MA1 timing values and epsilon are invalid")
    observer_cost = calibration_time_ms - baseline_time_ms
    live_gap = live_time_ms - live_region_time_ms
    excess = live_gap - observer_cost
    return BlockEstimand(
        baseline_time_ms=baseline_time_ms,
        calibration_time_ms=calibration_time_ms,
        live_time_ms=live_time_ms,
        live_region_time_ms=live_region_time_ms,
        observer_cost_time_ms=observer_cost,
        live_unattributed_time_ms=live_gap,
        excess_time_ms=excess,
        calibrated_excess_gap=excess / max(baseline_time_ms, epsilon),
    )


def finalize_recorders_after_block_sync(
    recorders: Sequence[SIMA0Recorder],
    *,
    block_synchronization_count: int,
) -> None:
    """Resolve internal events without adding a second synchronization."""

    for recorder in recorders:
        recorder.finalize_timing(
            synchronize=False,
            repetition_synchronization_count=block_synchronization_count,
        )


def topology_from_recorders(
    recorders: Sequence[SIMA0Recorder],
    *,
    outer_step_event_pair_count: int,
    block_synchronization_count: int,
) -> RecorderTopology:
    if not recorders:
        raise SIMA1Error("SI-MA1 topology requires recorder evidence")
    for recorder in recorders:
        if recorder.mode != "counters_only":
            raise SIMA1Error("SI-MA1 B/C must use counters_only")
        if len(recorder.total_records) != 1 or len(recorder.region_records) != len(REGIONS):
            raise SIMA1Error("SI-MA1 recorder was not finalized as one step")
    occurrence_count = sum(
        int(record["occurrence_count"])
        for recorder in recorders
        for record in recorder.region_records
    )
    configuration = {
        "observer_mode": "counters_only",
        "aggregate_regions": True,
        "defer_timing_resolution": True,
        "regions": list(REGIONS),
        "measured_steps": len(recorders),
        "outer_step_event_pairs": outer_step_event_pair_count,
        "block_sync_count": block_synchronization_count,
    }
    return RecorderTopology(
        measured_step_count=len(recorders),
        hook_invocation_count=len(recorders),
        outer_step_event_pair_count=outer_step_event_pair_count,
        internal_region_occurrence_count=occurrence_count,
        internal_region_record_count=sum(len(item.region_records) for item in recorders),
        total_timer_count=sum(len(item.total_records) for item in recorders),
        vjp_call_count=sum(item.vjp_call_count for item in recorders),
        saved_tensor_count=sum(item.saved_tensor_count for item in recorders),
        saved_tensor_bytes=sum(item.saved_tensor_bytes for item in recorders),
        pending_buffer_write_count=occurrence_count + len(recorders),
        finalized_buffer_write_count=sum(
            len(item.region_records) + len(item.total_records) for item in recorders
        ),
        block_synchronization_count=block_synchronization_count,
        instrumentation_configuration_hash=canonical_json_digest(configuration),
    )


def compare_topologies(
    calibration: RecorderTopology,
    live: RecorderTopology,
    *,
    metadata: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        **metadata,
        "implementation_schema_id": IMPLEMENTATION_SCHEMA_ID,
        **calibration.to_record(prefix="calibration_"),
        **live.to_record(prefix="live_"),
        "passed": calibration == live,
    }


def aggregate_numerical_comparisons(
    references: Sequence[ModeRunResult],
    candidates: Sequence[ModeRunResult],
    thresholds: NumericalThresholds,
    *,
    candidate_arm: Literal["B", "C"],
    metadata: Mapping[str, Any],
) -> dict[str, Any]:
    if len(references) != len(candidates) or not references:
        raise SIMA1Error("SI-MA1 numerical block comparison is incomplete")
    rows = [
        compare_mode_results(reference, candidate, thresholds, metadata={})
        for reference, candidate in zip(references, candidates, strict=True)
    ]
    return {
        **metadata,
        "implementation_schema_id": IMPLEMENTATION_SCHEMA_ID,
        "reference_arm": "A",
        "candidate_arm": candidate_arm,
        "step_count": len(rows),
        "step_pass_count": sum(bool(row["passed"]) for row in rows),
        "loss_max_relative_l2": max(float(row["loss_relative_l2"]) for row in rows),
        "loss_max_abs": max(float(row["loss_max_abs"]) for row in rows),
        "belief_max_relative_l2": max(float(row["belief_max_relative_l2"]) for row in rows),
        "belief_max_abs": max(float(row["belief_max_abs"]) for row in rows),
        "gradient_max_relative_l2": max(
            float(row["gradient_max_relative_l2"]) for row in rows
        ),
        "gradient_max_abs": max(float(row["gradient_max_abs"]) for row in rows),
        "model_state_unchanged": all(bool(row["model_state_unchanged"]) for row in rows),
        "input_target_fingerprint_unchanged": all(
            bool(row["input_target_fingerprint_unchanged"]) for row in rows
        ),
        "rng_fingerprint_equal": all(bool(row["rng_fingerprint_equal"]) for row in rows),
        "finite": all(bool(row["finite"]) for row in rows),
        "passed": all(bool(row["passed"]) for row in rows),
    }


def expected_attempt_counts(
    *,
    batch_count: int,
    measured_steps_per_arm_block: int,
) -> dict[str, int]:
    matched_blocks = batch_count * len(ORDER_PERMUTATIONS)
    return {
        "model_seed_batch_pairs": batch_count,
        "matched_blocks": matched_blocks,
        "arm_blocks": matched_blocks * len(ARM_LABELS),
        "arm_timing_records": matched_blocks * len(ARM_LABELS) * measured_steps_per_arm_block,
        "live_region_timing_records": matched_blocks * measured_steps_per_arm_block * len(REGIONS),
        "numerical_comparison_rows": matched_blocks * 2,
        "topology_comparison_rows": matched_blocks,
        "block_summary_rows": matched_blocks,
        "seed_summary_rows": 1,
        "order_seed_value_rows": len(ORDER_PERMUTATIONS),
    }


def validate_attempt_counts(
    observed: Mapping[str, int],
    *,
    batch_count: int,
    measured_steps_per_arm_block: int,
) -> None:
    expected = expected_attempt_counts(
        batch_count=batch_count,
        measured_steps_per_arm_block=measured_steps_per_arm_block,
    )
    if dict(observed) != expected:
        raise SIMA1Error(f"SI-MA1 count mismatch: {dict(observed)} != {expected}")


def build_seed_summary(
    block_summaries: Sequence[Mapping[str, Any]],
    *,
    model_seed: int,
    expected_block_count: int,
) -> dict[str, Any]:
    values = [float(row["calibrated_excess_gap"]) for row in block_summaries]
    if (
        expected_block_count <= 0
        or len(values) != expected_block_count
        or not all(math.isfinite(value) for value in values)
    ):
        raise SIMA1Error(
            "SI-MA1 seed summary has an invalid finite block count"
        )
    return {
        "model_seed": model_seed,
        "matched_block_count": len(values),
        "d_seed": float(statistics.median(values)),
        "mean_d": float(statistics.fmean(values)),
        "min_d": min(values),
        "max_d": max(values),
        "confirmatory_decision_made": False,
    }


def build_order_seed_values(
    block_summaries: Iterable[Mapping[str, Any]],
    *,
    model_seed: int,
    expected_batch_count: int,
) -> list[dict[str, Any]]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for row in block_summaries:
        grouped[str(row["order"])].append(float(row["calibrated_excess_gap"]))
    if set(grouped) != set(ORDER_PERMUTATIONS):
        raise SIMA1Error("SI-MA1 order evidence is incomplete")
    result: list[dict[str, Any]] = []
    for order in ORDER_PERMUTATIONS:
        values = grouped[order]
        if expected_batch_count <= 0 or len(values) != expected_batch_count:
            raise SIMA1Error(
                "each SI-MA1 order requires one value per selected batch"
            )
        result.append(
            {
                "model_seed": model_seed,
                "order": order,
                "batch_count": len(values),
                "median_d": float(statistics.median(values)),
                "mean_d": float(statistics.fmean(values)),
            }
        )
    return result
