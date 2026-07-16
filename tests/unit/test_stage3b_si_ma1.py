from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import torch

from torch2pc_thesis.stage3b_si_ma0 import ModeRunResult, SIMA0Recorder
from torch2pc_thesis.stage3b_si_ma1 import (
    ORDER_PERMUTATIONS,
    DeferredArmTimer,
    RecorderTopology,
    SIMA1Error,
    aggregate_numerical_comparisons,
    balanced_orders,
    build_order_seed_values,
    build_seed_summary,
    compare_topologies,
    compute_block_estimand,
    expected_attempt_counts,
    finalize_recorders_after_block_sync,
    load_contract,
    thresholds_for_si_ma1,
    topology_from_recorders,
    validate_attempt_counts,
    validate_balanced_orders,
)


class FakeEvent:
    def __init__(self, values: list[float]) -> None:
        self.values = values
        self.recorded = False

    def record(self) -> None:
        self.recorded = True

    def elapsed_time(self, other: FakeEvent) -> float:
        assert self.recorded and other.recorded
        return self.values.pop(0)


def contract_payload() -> dict[str, Any]:
    return {
        "contract_id": "stage3b-si-ma1-v1",
        "status": "frozen_preregistration",
        "balanced_order": {
            "permutations": list(ORDER_PERMUTATIONS),
            "blocks_per_model_seed_batch": 6,
        },
        "timing_protocol": {
            "required_sync_point": "end_of_arm_block",
            "per_region_device_synchronization": False,
        },
        "primary_estimand": {
            "observer_cost_time": "H = B - A",
            "live_unattributed_time": "R = C - K",
            "excess_time": "E = R - H = (C - K) - (B - A)",
            "calibrated_excess_gap": "D = E / max(A, epsilon)",
            "excess_margin": 0.01,
        },
        "numerical_thresholds": {
            "rocm_float32": {
                "zero_atol": 1e-6,
                "max_relative_l2": 1e-3,
                "max_abs": 1e-5,
                "min_cosine": 0.999,
            }
        },
        "ecz_evaluator_boundary": {"included_in_si_ma1": False},
    }


def test_load_contract_accepts_registered_formulas(tmp_path: Path) -> None:
    path = tmp_path / "contract.json"
    path.write_text(json.dumps(contract_payload()), encoding="utf-8")
    assert load_contract(path)["contract_id"] == "stage3b-si-ma1-v1"


def test_load_contract_rejects_old_mixed_denominator_formula(
    tmp_path: Path,
) -> None:
    payload = contract_payload()
    payload["primary_estimand"]["calibrated_excess_gap"] = "D = G - O"
    path = tmp_path / "contract.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(SIMA1Error, match="formula mismatch"):
        load_contract(path)


def test_threshold_loader_uses_registered_float32_profile() -> None:
    thresholds = thresholds_for_si_ma1(contract_payload())
    assert thresholds.zero_atol == pytest.approx(1e-6)
    assert thresholds.max_relative_l2 == pytest.approx(1e-3)


@pytest.mark.parametrize("model_seed", [0, 1, 5, 9])
@pytest.mark.parametrize("batch_id", [0, 1, 2])
def test_balanced_orders_are_exact_and_position_balanced(
    model_seed: int,
    batch_id: int,
) -> None:
    orders = balanced_orders(model_seed, batch_id)
    assert validate_balanced_orders(
        orders,
        model_seed=model_seed,
        batch_id=batch_id,
    )
    assert set(orders) == set(ORDER_PERMUTATIONS)


def test_balanced_order_rejects_repetition() -> None:
    orders = list(balanced_orders(0, 0))
    orders[-1] = orders[0]
    assert not validate_balanced_orders(orders, model_seed=0, batch_id=0)


def test_deferred_cuda_timer_synchronizes_once_for_whole_block() -> None:
    values = [1.0, 2.0, 3.0]
    sync_calls: list[int] = []
    events: list[FakeEvent] = []

    def event_factory() -> FakeEvent:
        event = FakeEvent(values)
        events.append(event)
        return event

    timer = DeferredArmTimer(
        torch.device("cuda"),
        event_factory=event_factory,
        synchronize=lambda: sync_calls.append(1),
    )
    for _ in range(3):
        with timer.step():
            pass
    durations = timer.finalize()
    assert durations == [1.0, 2.0, 3.0]
    assert len(events) == 6
    assert sync_calls == [1]
    assert timer.synchronization_count == 1


def test_block_estimand_subtracts_absolute_times_before_normalizing() -> None:
    result = compute_block_estimand(
        baseline_time_ms=100.0,
        calibration_time_ms=116.0,
        live_time_ms=117.0,
        live_region_time_ms=100.0,
        epsilon=1e-12,
    )
    assert result.observer_cost_time_ms == pytest.approx(16.0)
    assert result.live_unattributed_time_ms == pytest.approx(17.0)
    assert result.excess_time_ms == pytest.approx(1.0)
    assert result.calibrated_excess_gap == pytest.approx(0.01)


def test_block_estimand_preserves_negative_excess() -> None:
    result = compute_block_estimand(
        baseline_time_ms=100.0,
        calibration_time_ms=120.0,
        live_time_ms=115.0,
        live_region_time_ms=100.0,
        epsilon=1e-12,
    )
    assert result.excess_time_ms == pytest.approx(-5.0)
    assert result.calibrated_excess_gap == pytest.approx(-0.05)


def topology(*, sync_count: int = 1) -> RecorderTopology:
    return RecorderTopology(
        measured_step_count=50,
        hook_invocation_count=50,
        outer_step_event_pair_count=50,
        internal_region_occurrence_count=1000,
        internal_region_record_count=350,
        total_timer_count=50,
        vjp_call_count=6000,
        saved_tensor_count=0,
        saved_tensor_bytes=0,
        pending_buffer_write_count=1050,
        finalized_buffer_write_count=400,
        block_synchronization_count=sync_count,
        instrumentation_configuration_hash="a" * 64,
    )


def test_topology_comparison_is_exact() -> None:
    assert compare_topologies(
        topology(),
        topology(),
        metadata={"order": "ABC"},
    )["passed"] is True


def test_topology_comparison_detects_sync_difference() -> None:
    assert compare_topologies(
        topology(),
        topology(sync_count=2),
        metadata={"order": "ABC"},
    )["passed"] is False


def test_expected_attempt_counts_match_one_confirmatory_seed() -> None:
    assert expected_attempt_counts(
        batch_count=3,
        measured_steps_per_arm_block=50,
    ) == {
        "model_seed_batch_pairs": 3,
        "matched_blocks": 18,
        "arm_blocks": 54,
        "arm_timing_records": 2700,
        "live_region_timing_records": 6300,
        "numerical_comparison_rows": 36,
        "topology_comparison_rows": 18,
        "block_summary_rows": 18,
        "seed_summary_rows": 1,
        "order_seed_value_rows": 6,
    }


def test_validate_attempt_counts_fails_closed() -> None:
    observed = expected_attempt_counts(
        batch_count=3,
        measured_steps_per_arm_block=50,
    )
    observed["arm_timing_records"] -= 1
    with pytest.raises(SIMA1Error, match="count mismatch"):
        validate_attempt_counts(
            observed,
            batch_count=3,
            measured_steps_per_arm_block=50,
        )


def block_records() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for batch_id in range(3):
        for index, order in enumerate(ORDER_PERMUTATIONS):
            rows.append(
                {
                    "batch_id": batch_id,
                    "order": order,
                    "calibrated_excess_gap": 0.001 * (batch_id + index),
                }
            )
    return rows


def test_seed_summary_requires_all_eighteen_blocks() -> None:
    summary = build_seed_summary(
        block_records(),
        model_seed=3,
        expected_block_count=18,
    )
    assert summary["matched_block_count"] == 18
    assert summary["confirmatory_decision_made"] is False


def test_order_seed_values_produce_six_non_authorizing_rows() -> None:
    rows = build_order_seed_values(
        block_records(),
        model_seed=3,
        expected_batch_count=3,
    )
    assert [row["order"] for row in rows] == list(ORDER_PERMUTATIONS)
    assert all(row["batch_count"] == 3 for row in rows)


def mode_result(mode: str, value: float = 1.0) -> ModeRunResult:
    tensor = torch.tensor([value], dtype=torch.float32)
    return ModeRunResult(
        mode=mode,  # type: ignore[arg-type]
        loss=tensor.clone(),
        beliefs=(tensor.clone(),),
        gradients=(tensor.clone(),),
        model_fingerprint_before="m",
        model_fingerprint_after="m",
        input_fingerprint_before="i",
        input_fingerprint_after="i",
        target_fingerprint_before="t",
        target_fingerprint_after="t",
        rng_fingerprint_before="r",
        rng_fingerprint_after="r",
        wall_time_ms=1.0,
        device_time_ms=1.0,
        recorder=None,
    )


def test_numerical_block_summary_covers_all_fifty_steps() -> None:
    thresholds = thresholds_for_si_ma1(contract_payload())
    references = [mode_result("no_hooks") for _ in range(50)]
    candidates = [mode_result("counters_only") for _ in range(50)]
    row = aggregate_numerical_comparisons(
        references,
        candidates,
        thresholds,
        candidate_arm="B",
        metadata={"order": "ABC"},
    )
    assert row["step_count"] == 50
    assert row["step_pass_count"] == 50
    assert row["passed"] is True


def test_recorder_resolution_adds_no_second_sync() -> None:
    thresholds = thresholds_for_si_ma1(contract_payload())
    recorder = SIMA0Recorder(
        mode="counters_only",
        device=torch.device("cpu"),
        thresholds=thresholds,
        metadata={"step": 0},
        aggregate_regions=True,
        defer_timing_resolution=True,
    )
    with recorder.total_timer():
        for region in (
            "inference_setup",
            "lower_prediction_and_error",
            "upper_state_vjp",
            "component_aggregation",
            "belief_update",
            "sweep_bookkeeping",
            "inference_finalize",
        ):
            with recorder.region(region):  # type: ignore[arg-type]
                pass
    finalize_recorders_after_block_sync(
        [recorder],
        block_synchronization_count=0,
    )
    assert recorder.synchronization_count == 0
    topology = topology_from_recorders(
        [recorder],
        outer_step_event_pair_count=1,
        block_synchronization_count=0,
    )
    assert topology.internal_region_record_count == 7
    assert topology.total_timer_count == 1


def test_smoke_seed_summary_accepts_one_complete_batch() -> None:
    rows = [
        {
            "order": order,
            "calibrated_excess_gap": 0.001 * index,
        }
        for index, order in enumerate(ORDER_PERMUTATIONS)
    ]
    summary = build_seed_summary(
        rows,
        model_seed=0,
        expected_block_count=6,
    )
    order_rows = build_order_seed_values(
        rows,
        model_seed=0,
        expected_batch_count=1,
    )
    assert summary["matched_block_count"] == 6
    assert len(order_rows) == 6
