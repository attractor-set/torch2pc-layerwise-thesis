from __future__ import annotations

from torch2pc_thesis.pcinfer_instrumentation import PCInferInstrumentationSummary
from torch2pc_thesis.stage3b_b0_integration import B0CompositeMeasurement
from torch2pc_thesis.stage3b_b1_isolated_vjp import B1StructuralEvent
from torch2pc_thesis.stage3b_b2_composite_vjp import B2StructuralEvent
from torch2pc_thesis.stage3b_matched_measurement import (
    MatchedStructuralCollector,
    baseline_locality_events,
    observer_cost_measurement,
    structural_measurement_from_events,
)


def test_native_b1_events_are_normalized() -> None:
    collector = MatchedStructuralCollector(
        candidate_id="isolated_layer_vjp",
        method="fixedpred",
    )
    collector(
        B1StructuralEvent(
            candidate_id="isolated_layer_vjp",
            method="fixedpred",
            sweep_index=0,
            layer_index=3,
        )
    )

    [event] = collector.events
    summary = collector.summary(actual_inference_steps=1)

    assert event.graph_module_set == (3,)
    assert event.graph_span == 1
    assert event.dependency_radius == 1
    assert event.feedback_operator == "exact_isolated_layer_vjp"
    assert summary.event_count == 1
    assert summary.state_vjp_calls == 1
    assert summary.fallback_validation_cost_ms is None


def test_native_b2_events_preserve_composite_graph_span() -> None:
    collector = MatchedStructuralCollector(
        candidate_id="composite_vjp",
        method="strict",
    )
    collector(
        B2StructuralEvent(
            candidate_id="composite_vjp",
            method="strict",
            sweep_index=0,
            layer_indices=(1, 2, 3),
            logical_edge_count=3,
        )
    )

    [event] = collector.events
    assert event.graph_module_set == (1, 2, 3)
    assert event.graph_span == 3
    assert event.dependency_radius == 1
    assert event.feedback_operator == "exact_composite_state_vjp"


def test_baseline_events_match_observed_local_vjp_count() -> None:
    instrumentation = PCInferInstrumentationSummary(
        actual_inference_steps=2,
        initial_forward_autograd_calls=1,
        state_autograd_calls=8,
        local_state_vjp_calls=8,
        parameter_vjp_calls=1,
    )
    events = baseline_locality_events(
        method="fixedpred",
        model_depth=4,
        inference_steps=2,
        instrumentation=instrumentation,
    )
    summary = structural_measurement_from_events(
        events,
        actual_inference_steps=2,
    )

    assert len(events) == 8
    assert summary.graph_span == 1
    assert summary.dependency_radius == 1
    assert summary.graph_lifetimes == ("reused_across_inference_sweeps",)


def test_observer_cost_is_reported_without_mutating_primary_timing() -> None:
    primary = B0CompositeMeasurement(
        host_time_us=1_000.0,
        device_time_us=800.0,
        peak_allocated_bytes=10,
        peak_reserved_bytes=20,
        synchronization_points=2,
    )
    structural = B0CompositeMeasurement(
        host_time_us=1_500.0,
        device_time_us=1_100.0,
        peak_allocated_bytes=12,
        peak_reserved_bytes=22,
        synchronization_points=8,
    )

    cost = observer_cost_measurement(
        candidate_id="composite_vjp",
        method="fixedpred",
        primary=primary,
        structural=structural,
    )

    assert cost.observer_host_cost_ms == 0.5
    assert cost.observer_device_cost_ms == 0.3
    assert cost.observer_cost_ms == 0.3
    assert cost.not_subtracted_from_primary_timing is True
    assert primary.device_time_us == 800.0
