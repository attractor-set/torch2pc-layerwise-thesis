"""Matched Stage 3B timing-lane and structural-locality records.

The frozen matched protocol separates the primary no-hooks timing lane from the
counters-only structural lane.  This module normalizes B0/B1/B2 structural
events into one serializable schema and reports observer cost without silently
subtracting it from primary timing.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Final, Protocol, cast

from torch2pc_thesis.pcinfer_instrumentation import PCInferInstrumentationSummary
from torch2pc_thesis.profiling import Stage3ProfilingError

MATCHED_LOCALITY_EVENT_SCHEMA_VERSION: Final[int] = 1
MATCHED_STRUCTURAL_MEASUREMENT_SCHEMA_VERSION: Final[int] = 1
MATCHED_OBSERVER_COST_SCHEMA_VERSION: Final[int] = 1
MATCHED_PRIMARY_TIMING_LANE: Final[str] = "primary_timing"
MATCHED_STRUCTURAL_COUNTERS_LANE: Final[str] = "structural_counters"
MATCHED_FALLBACK_STATUS: Final[str] = "not_applicable_before_ex_if0"


class CompositeMeasurementLike(Protocol):
    @property
    def host_time_us(self) -> float: ...

    @property
    def device_time_us(self) -> float: ...



@dataclass(frozen=True)
class MatchedLocalityEvent:
    """One normalized graph/locality event from the counters-only lane."""

    candidate_id: str
    method: str
    sweep_index: int
    event_index: int
    logical_edge_count: int
    state_vjp_call_count: int
    graph_island_count: int
    graph_module_set: tuple[int, ...]
    graph_span: int
    dependency_radius: int | None
    graph_lifetime: str
    freedom_point: str
    feedback_operator: str
    orchestration_barriers: int
    structural_source: str

    def __post_init__(self) -> None:
        if not self.candidate_id:
            raise Stage3ProfilingError("candidate_id is required")
        if self.method not in {"fixedpred", "strict"}:
            raise Stage3ProfilingError(f"unsupported structural method: {self.method}")
        for name, value in {
            "sweep_index": self.sweep_index,
            "event_index": self.event_index,
            "logical_edge_count": self.logical_edge_count,
            "state_vjp_call_count": self.state_vjp_call_count,
            "graph_island_count": self.graph_island_count,
            "graph_span": self.graph_span,
            "orchestration_barriers": self.orchestration_barriers,
        }.items():
            if value < 0:
                raise Stage3ProfilingError(f"{name} must be non-negative")
        if self.dependency_radius is not None and self.dependency_radius < 0:
            raise Stage3ProfilingError("dependency_radius must be non-negative")
        if self.graph_module_set:
            expected_span = self.graph_module_set[-1] - self.graph_module_set[0] + 1
            if self.graph_span != expected_span:
                raise Stage3ProfilingError(
                    "graph span differs from graph module set: "
                    f"expected={expected_span}, observed={self.graph_span}"
                )
        elif self.graph_span != 0:
            raise Stage3ProfilingError("empty graph module set requires graph_span=0")

    def to_record(self) -> dict[str, object]:
        return {
            "schema_version": MATCHED_LOCALITY_EVENT_SCHEMA_VERSION,
            **asdict(self),
            "graph_module_set": list(self.graph_module_set),
        }


@dataclass(frozen=True)
class MatchedStructuralMeasurement:
    """One step-level structural summary for the counters-only lane."""

    candidate_id: str
    method: str
    actual_inference_steps: int
    event_count: int
    state_vjp_calls: int
    logical_edge_count: int
    graph_island_count: int
    graph_module_sets: tuple[tuple[int, ...], ...]
    graph_span: int
    dependency_radius: int | None
    graph_lifetimes: tuple[str, ...]
    freedom_points: tuple[str, ...]
    feedback_operator: str
    orchestration_barriers: int
    structural_source: str
    fallback_validation_cost_ms: float | None = None
    fallback_validation_status: str = MATCHED_FALLBACK_STATUS

    def __post_init__(self) -> None:
        if self.actual_inference_steps < 1:
            raise Stage3ProfilingError("actual_inference_steps must be positive")
        for name, value in {
            "event_count": self.event_count,
            "state_vjp_calls": self.state_vjp_calls,
            "logical_edge_count": self.logical_edge_count,
            "graph_island_count": self.graph_island_count,
            "graph_span": self.graph_span,
            "orchestration_barriers": self.orchestration_barriers,
        }.items():
            if value < 0:
                raise Stage3ProfilingError(f"{name} must be non-negative")
        if self.event_count < 1:
            raise Stage3ProfilingError("at least one structural event is required")
        if self.state_vjp_calls < 1:
            raise Stage3ProfilingError("at least one state VJP call is required")
        if self.dependency_radius is not None and self.dependency_radius < 0:
            raise Stage3ProfilingError("dependency_radius must be non-negative")
        if self.fallback_validation_cost_ms is not None and (
            not math.isfinite(self.fallback_validation_cost_ms)
            or self.fallback_validation_cost_ms < 0.0
        ):
            raise Stage3ProfilingError(
                "fallback_validation_cost_ms must be finite and non-negative"
            )
        if self.fallback_validation_status != MATCHED_FALLBACK_STATUS:
            raise Stage3ProfilingError(
                "fallback validation must remain explicitly not applicable before EX-IF0"
            )

    def to_record(self) -> dict[str, object]:
        return {
            "schema_version": MATCHED_STRUCTURAL_MEASUREMENT_SCHEMA_VERSION,
            **asdict(self),
            "graph_module_sets": [list(value) for value in self.graph_module_sets],
            "graph_lifetimes": list(self.graph_lifetimes),
            "freedom_points": list(self.freedom_points),
        }


@dataclass(frozen=True)
class MatchedObserverCostMeasurement:
    """Reported structural-observer cost relative to no-hooks primary timing."""

    candidate_id: str
    method: str
    primary_host_time_us: float
    structural_host_time_us: float
    observer_host_cost_ms: float
    primary_device_time_us: float
    structural_device_time_us: float
    observer_device_cost_ms: float
    observer_cost_ms: float
    observer_cost_basis: str
    not_subtracted_from_primary_timing: bool = True

    def __post_init__(self) -> None:
        for name, value in {
            "primary_host_time_us": self.primary_host_time_us,
            "structural_host_time_us": self.structural_host_time_us,
            "observer_host_cost_ms": self.observer_host_cost_ms,
            "primary_device_time_us": self.primary_device_time_us,
            "structural_device_time_us": self.structural_device_time_us,
            "observer_device_cost_ms": self.observer_device_cost_ms,
            "observer_cost_ms": self.observer_cost_ms,
        }.items():
            if not math.isfinite(value):
                raise Stage3ProfilingError(f"{name} must be finite")
        if not self.not_subtracted_from_primary_timing:
            raise Stage3ProfilingError(
                "observer cost must not be silently subtracted from primary timing"
            )
        if self.observer_cost_basis not in {"device_time", "host_time"}:
            raise Stage3ProfilingError("unsupported observer cost basis")

    def to_record(self) -> dict[str, object]:
        return {
            "schema_version": MATCHED_OBSERVER_COST_SCHEMA_VERSION,
            **asdict(self),
        }


def observer_cost_measurement(
    *,
    candidate_id: str,
    method: str,
    primary: CompositeMeasurementLike,
    structural: CompositeMeasurementLike,
) -> MatchedObserverCostMeasurement:
    """Return signed observer overhead; primary values remain unchanged."""

    host_cost_ms = (structural.host_time_us - primary.host_time_us) / 1_000.0
    device_cost_ms = (structural.device_time_us - primary.device_time_us) / 1_000.0
    if primary.device_time_us > 0.0 or structural.device_time_us > 0.0:
        basis = "device_time"
        selected = device_cost_ms
    else:
        basis = "host_time"
        selected = host_cost_ms
    return MatchedObserverCostMeasurement(
        candidate_id=candidate_id,
        method=method,
        primary_host_time_us=primary.host_time_us,
        structural_host_time_us=structural.host_time_us,
        observer_host_cost_ms=host_cost_ms,
        primary_device_time_us=primary.device_time_us,
        structural_device_time_us=structural.device_time_us,
        observer_device_cost_ms=device_cost_ms,
        observer_cost_ms=selected,
        observer_cost_basis=basis,
    )


def _feedback_operator(candidate_id: str, method: str) -> str:
    if candidate_id == "composite_vjp":
        return "exact_composite_state_vjp"
    if candidate_id == "isolated_layer_vjp":
        return "exact_isolated_layer_vjp"
    if candidate_id == "stage2_baseline" and method == "fixedpred":
        return "exact_local_vjp_reused_fixed_prediction_graph"
    if candidate_id == "stage2_baseline" and method == "strict":
        return "exact_local_vjp_recomputed_strict_graph"
    raise Stage3ProfilingError(
        f"unsupported structural candidate/method: {candidate_id}/{method}"
    )


def _required_int(value: object, *, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise Stage3ProfilingError(f"{label} must be an integer")
    return value


class MatchedStructuralCollector:
    """Normalize native B1/B2 event objects without retaining tensor state."""

    def __init__(self, *, candidate_id: str, method: str) -> None:
        if candidate_id not in {"isolated_layer_vjp", "composite_vjp"}:
            raise Stage3ProfilingError(
                f"native structural collector does not support {candidate_id}"
            )
        if method not in {"fixedpred", "strict"}:
            raise Stage3ProfilingError(f"unsupported structural method: {method}")
        self.candidate_id = candidate_id
        self.method = method
        self._events: list[MatchedLocalityEvent] = []

    @property
    def events(self) -> tuple[MatchedLocalityEvent, ...]:
        return tuple(self._events)

    def __call__(self, event: object) -> None:
        raw_method = getattr(event, "to_dict", None)
        if not callable(raw_method):
            raise Stage3ProfilingError("native structural event is not serializable")
        raw = raw_method()
        if not isinstance(raw, Mapping):
            raise Stage3ProfilingError("native structural event is not a mapping")
        candidate_id = str(raw.get("candidate_id", ""))
        method = str(raw.get("method", "")).lower()
        if candidate_id != self.candidate_id or method != self.method:
            raise Stage3ProfilingError(
                "native structural event identity differs from collector"
            )
        modules: tuple[int, ...]
        if "layer_index" in raw:
            modules = (_required_int(raw["layer_index"], label="layer_index"),)
            state_calls = _required_int(
                raw.get("state_vjp_call_count", 1),
                label="state_vjp_call_count",
            )
            graph_islands = _required_int(
                raw.get("graph_island_count", 1),
                label="graph_island_count",
            )
        else:
            raw_modules = cast(Sequence[object], raw.get("graph_module_set", ()))
            modules = tuple(
                _required_int(value, label="graph_module_set")
                for value in raw_modules
            )
            state_calls = _required_int(
                raw.get("composite_vjp_call_count", 1),
                label="composite_vjp_call_count",
            )
            graph_islands = 1
        modules = tuple(sorted(modules))
        graph_span = int(cast(int, raw.get("graph_span", 0)))
        lifetime = str(raw.get("graph_lifetime", "unknown"))
        logical_edges = int(cast(int, raw.get("logical_edge_count", 0)))
        dependency_radius = 1 if logical_edges > 0 else None
        self._events.append(
            MatchedLocalityEvent(
                candidate_id=self.candidate_id,
                method=self.method,
                sweep_index=int(cast(int, raw.get("sweep_index", -1))),
                event_index=len(self._events),
                logical_edge_count=logical_edges,
                state_vjp_call_count=state_calls,
                graph_island_count=graph_islands,
                graph_module_set=modules,
                graph_span=graph_span,
                dependency_radius=dependency_radius,
                graph_lifetime=lifetime,
                freedom_point=lifetime,
                feedback_operator=_feedback_operator(self.candidate_id, self.method),
                orchestration_barriers=0,
                structural_source="native_counters_only",
            )
        )

    def summary(self, *, actual_inference_steps: int) -> MatchedStructuralMeasurement:
        return structural_measurement_from_events(
            self._events,
            actual_inference_steps=actual_inference_steps,
        )


def baseline_locality_events(
    *,
    method: str,
    model_depth: int,
    inference_steps: int,
    instrumentation: PCInferInstrumentationSummary,
) -> tuple[MatchedLocalityEvent, ...]:
    """Normalize the pinned Stage-2 Torch2PC local VJP structure.

    The pinned implementation executes one exact layer-local VJP per logical
    upper-state edge.  FixedPred reuses one local graph per layer across sweeps;
    Strict rebuilds and frees each local graph in the sweep.
    """

    if method not in {"fixedpred", "strict"}:
        raise Stage3ProfilingError(f"unsupported baseline method: {method}")
    if model_depth < 2 or inference_steps < 1:
        raise Stage3ProfilingError("invalid baseline structural dimensions")
    if method == "fixedpred":
        layer_indices = tuple(range(model_depth))
        lifetime = "reused_across_inference_sweeps"
    else:
        layer_indices = tuple(range(1, model_depth))
        lifetime = "single_vjp_call"
    events: list[MatchedLocalityEvent] = []
    for sweep_index in range(inference_steps):
        for layer_index in layer_indices:
            events.append(
                MatchedLocalityEvent(
                    candidate_id="stage2_baseline",
                    method=method,
                    sweep_index=sweep_index,
                    event_index=len(events),
                    logical_edge_count=1,
                    state_vjp_call_count=1,
                    graph_island_count=1,
                    graph_module_set=(layer_index,),
                    graph_span=1,
                    dependency_radius=1,
                    graph_lifetime=lifetime,
                    freedom_point=lifetime,
                    feedback_operator=_feedback_operator("stage2_baseline", method),
                    orchestration_barriers=0,
                    structural_source="pinned_torch2pc_autograd_counter",
                )
            )
    if len(events) != instrumentation.local_state_vjp_calls:
        raise Stage3ProfilingError(
            "baseline structural event count differs from observed local VJP calls: "
            f"events={len(events)}, observed={instrumentation.local_state_vjp_calls}"
        )
    return tuple(events)


def structural_measurement_from_events(
    events: Sequence[MatchedLocalityEvent],
    *,
    actual_inference_steps: int,
) -> MatchedStructuralMeasurement:
    if not events:
        raise Stage3ProfilingError("structural measurement requires events")
    candidate_ids = {event.candidate_id for event in events}
    methods = {event.method for event in events}
    if len(candidate_ids) != 1 or len(methods) != 1:
        raise Stage3ProfilingError("structural events mix candidates or methods")
    dependency_values = [
        event.dependency_radius
        for event in events
        if event.dependency_radius is not None
    ]
    return MatchedStructuralMeasurement(
        candidate_id=next(iter(candidate_ids)),
        method=next(iter(methods)),
        actual_inference_steps=actual_inference_steps,
        event_count=len(events),
        state_vjp_calls=sum(event.state_vjp_call_count for event in events),
        logical_edge_count=sum(event.logical_edge_count for event in events),
        graph_island_count=sum(event.graph_island_count for event in events),
        graph_module_sets=tuple(event.graph_module_set for event in events),
        graph_span=max(event.graph_span for event in events),
        dependency_radius=max(dependency_values) if dependency_values else None,
        graph_lifetimes=tuple(sorted({event.graph_lifetime for event in events})),
        freedom_points=tuple(sorted({event.freedom_point for event in events})),
        feedback_operator=events[0].feedback_operator,
        orchestration_barriers=sum(event.orchestration_barriers for event in events),
        structural_source=events[0].structural_source,
    )
