from __future__ import annotations

import pytest

from torch2pc_thesis.locality import (
    LocalityEvent,
    LocalityTraceError,
    assert_layer_local,
    summarize_locality_events,
)


def _event(**overrides: object) -> LocalityEvent:
    values: dict[str, object] = {
        "candidate_id": "isolated_layer_vjp",
        "method": "strict",
        "phase": "local_state_vjp",
        "step": 2,
        "layer": 3,
        "touched_layers": (2, 3, 4),
        "graph_modules": (3, 4),
        "vjp_calls": 1,
        "synchronization_points": 0,
        "saved_tensor_bytes": 1024,
        "cpu_time_us": 12.5,
        "device_time_us": 8.0,
    }
    values.update(overrides)
    return LocalityEvent(**values)  # type: ignore[arg-type]


def test_locality_event_derives_radius_and_graph_span() -> None:
    event = _event()
    assert event.dependency_radius == 1
    assert event.graph_span == 2
    assert event.to_record()["schema_version"] == 1


def test_layer_local_gate_rejects_non_adjacent_dependency() -> None:
    event = _event(touched_layers=(0, 3, 4))
    with pytest.raises(LocalityTraceError, match="dependency_radius=3"):
        assert_layer_local(event)


def test_locality_summary_preserves_cost_dimensions() -> None:
    summary = summarize_locality_events([_event(), _event(step=3, vjp_calls=2)])
    assert summary["event_count"] == 2
    assert summary["total_vjp_calls"] == 3
    assert summary["max_dependency_radius"] == 1
    assert summary["total_saved_tensor_bytes"] == 2048
