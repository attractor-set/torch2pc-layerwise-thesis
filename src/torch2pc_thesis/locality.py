from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from typing import Any

LOCALITY_TRACE_SCHEMA_VERSION = 1
_ALLOWED_PHASES = {
    "initial_forward",
    "state_inference",
    "local_state_vjp",
    "parameter_vjp",
    "optimizer_step",
}


class LocalityTraceError(ValueError):
    """Raised when a Stage 3 locality trace violates the declared schema."""


@dataclass(frozen=True)
class LocalityEvent:
    """One implementation-level observation for the Stage 3 locality audit.

    ``layer`` identifies the layer whose state or parameters are updated.
    ``touched_layers`` records every model layer whose values or graph are
    required by the event.  A mathematically layer-local update normally has a
    dependency radius of at most one.
    """

    candidate_id: str
    method: str
    phase: str
    step: int
    layer: int | None
    touched_layers: tuple[int, ...]
    graph_modules: tuple[int, ...]
    vjp_calls: int = 0
    synchronization_points: int = 0
    saved_tensor_bytes: int = 0
    cpu_time_us: float = 0.0
    device_time_us: float = 0.0

    def __post_init__(self) -> None:
        if not self.candidate_id:
            raise LocalityTraceError("candidate_id is required")
        if self.method not in {"fixedpred", "strict"}:
            raise LocalityTraceError("locality events are defined for fixedpred or strict")
        if self.phase not in _ALLOWED_PHASES:
            raise LocalityTraceError(f"unknown locality phase: {self.phase}")
        if self.step < 0:
            raise LocalityTraceError("step must be non-negative")
        if self.layer is not None and self.layer < 0:
            raise LocalityTraceError("layer must be non-negative")
        if any(value < 0 for value in self.touched_layers):
            raise LocalityTraceError("touched_layers must be non-negative")
        if any(value < 0 for value in self.graph_modules):
            raise LocalityTraceError("graph_modules must be non-negative")
        for name, value in {
            "vjp_calls": self.vjp_calls,
            "synchronization_points": self.synchronization_points,
            "saved_tensor_bytes": self.saved_tensor_bytes,
        }.items():
            if value < 0:
                raise LocalityTraceError(f"{name} must be non-negative")
        if self.cpu_time_us < 0 or self.device_time_us < 0:
            raise LocalityTraceError("timings must be non-negative")

    @property
    def dependency_radius(self) -> int | None:
        if self.layer is None or not self.touched_layers:
            return None
        return max(abs(other - self.layer) for other in self.touched_layers)

    @property
    def graph_span(self) -> int:
        if not self.graph_modules:
            return 0
        return max(self.graph_modules) - min(self.graph_modules) + 1

    def to_record(self) -> dict[str, Any]:
        record = asdict(self)
        record.update(
            {
                "schema_version": LOCALITY_TRACE_SCHEMA_VERSION,
                "dependency_radius": self.dependency_radius,
                "graph_span": self.graph_span,
                "touched_layers": list(self.touched_layers),
                "graph_modules": list(self.graph_modules),
            }
        )
        return record


def assert_layer_local(event: LocalityEvent, *, maximum_radius: int = 1) -> None:
    """Reject an event that touches layers beyond the declared local radius."""

    if maximum_radius < 0:
        raise ValueError("maximum_radius must be non-negative")
    radius = event.dependency_radius
    if radius is not None and radius > maximum_radius:
        raise LocalityTraceError(
            f"event for layer={event.layer} has dependency_radius={radius}, "
            f"expected <= {maximum_radius}"
        )


def summarize_locality_events(events: Iterable[LocalityEvent]) -> dict[str, Any]:
    materialized = list(events)
    if not materialized:
        raise LocalityTraceError("at least one locality event is required")

    radii = [event.dependency_radius for event in materialized if event.dependency_radius is not None]
    return {
        "schema_version": LOCALITY_TRACE_SCHEMA_VERSION,
        "event_count": len(materialized),
        "candidate_ids": sorted({event.candidate_id for event in materialized}),
        "methods": sorted({event.method for event in materialized}),
        "phases": sorted({event.phase for event in materialized}),
        "max_dependency_radius": max(radii) if radii else None,
        "max_graph_span": max(event.graph_span for event in materialized),
        "total_vjp_calls": sum(event.vjp_calls for event in materialized),
        "total_synchronization_points": sum(
            event.synchronization_points for event in materialized
        ),
        "total_saved_tensor_bytes": sum(event.saved_tensor_bytes for event in materialized),
        "total_cpu_time_us": sum(event.cpu_time_us for event in materialized),
        "total_device_time_us": sum(event.device_time_us for event in materialized),
    }
