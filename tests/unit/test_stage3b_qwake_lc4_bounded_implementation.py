from __future__ import annotations

import random
from dataclasses import replace

import numpy as np
import pytest
import torch
from torch import Tensor, nn

from torch2pc_thesis.stage3b_qwake_lc4_bounded import (
    ANALYTIC_ACTION_ID,
    EXACT_REFERENCE_ACTION_ID,
    PAIR_COUNT,
    ArtifactRecord,
    BoundedArm,
    BoundedUnitTestAuthorization,
    CostPair,
    FallbackRecord,
    IntervalOwner,
    IntervalRecord,
    MemoryRecord,
    ObserverCalibration,
    QWakeLC4BoundedError,
    ResourceTrajectory,
    aggregate_paired_costs,
    analytic_wavefront_completion,
    capture_fixedpred_frontier,
    capture_opaque_state,
    capture_rng_snapshot,
    compare_required_responses,
    complete_exact_suffix,
    map_resource_trajectory,
    materialize_required_response,
    pair_schedule,
    preserve_outer_rng,
    restore_rng_snapshot,
    run_synthetic_matched_pair,
    run_synthetic_reserve_probe,
)


def _model() -> nn.Sequential:
    state = torch.random.get_rng_state()
    try:
        torch.manual_seed(641)
        return nn.Sequential(
            nn.Linear(4, 6),
            nn.Tanh(),
            nn.Linear(6, 3),
        ).to(dtype=torch.float64)
    finally:
        torch.random.set_rng_state(state)


def _batch() -> tuple[Tensor, Tensor]:
    generator = torch.Generator().manual_seed(642)
    return (
        torch.randn(3, 4, generator=generator, dtype=torch.float64),
        torch.tensor([0, 2, 1]),
    )


def _snapshot(candidate_index: int = 1):
    model = _model()
    inputs, targets = _batch()
    frontier = capture_fixedpred_frontier(
        model,
        nn.CrossEntropyLoss(),
        inputs,
        targets,
        candidate_index=candidate_index,
    )
    return capture_opaque_state(
        model,
        inputs,
        targets,
        frontier,
        lane_profile_id="cpu_float64_engineering",
        comparison_profile_id="cpu_float64_engineering",
        cost_profile_id="shadow_mechanism_v1",
        runtime_controls={
            "data_classification": "synthetic_unit_test",
            "runtime_execution_permitted": False,
            "scientific_execution_open": False,
            "deterministic_algorithms": True,
        },
    )


def test_analytic_completion_matches_exact_suffix_for_every_candidate_index() -> None:
    depth = len(_model())
    for candidate_index in range(depth + 1):
        snapshot = _snapshot(candidate_index)
        exact_model, exact_frontier = snapshot.fork()
        candidate_model, candidate_frontier = snapshot.fork()
        exact = complete_exact_suffix(exact_model, exact_frontier)
        candidate = analytic_wavefront_completion(
            candidate_model,
            candidate_frontier,
        )
        exact_response = materialize_required_response(
            exact_model,
            exact,
            state_id=snapshot.opaque_state_ref,
            comparison_profile_id=snapshot.comparison_profile_id,
        )
        candidate_response = materialize_required_response(
            candidate_model,
            candidate,
            state_id=snapshot.opaque_state_ref,
            comparison_profile_id=snapshot.comparison_profile_id,
        )
        comparison = compare_required_responses(
            exact_response,
            candidate_response,
        )
        assert exact.action_id == EXACT_REFERENCE_ACTION_ID
        assert candidate.action_id == ANALYTIC_ACTION_ID
        assert exact.vjp_count == depth * (depth - candidate_index)
        assert candidate.vjp_count == depth - candidate_index
        assert comparison.structural_equal
        assert comparison.passed
        assert comparison.response_defect <= 1.0


def test_opaque_state_ref_binds_payloads_and_forks_are_disposable() -> None:
    snapshot = _snapshot(1)
    first_model, first_frontier = snapshot.fork()
    second_model, second_frontier = snapshot.fork()
    with torch.no_grad():
        next(first_model.parameters()).add_(1.0)
        first_frontier.beliefs[0].add_(1.0)
    assert not torch.equal(
        next(first_model.parameters()),
        next(second_model.parameters()),
    )
    assert not torch.equal(
        first_frontier.beliefs[0],
        second_frontier.beliefs[0],
    )
    snapshot.verify_integrity()

    snapshot.frontier.beliefs[0].add_(1.0)
    with pytest.raises(QWakeLC4BoundedError, match="source snapshot was mutated"):
        snapshot.verify_integrity()


def test_rng_snapshot_restores_default_and_custom_inventory() -> None:
    custom = torch.Generator().manual_seed(643)
    random.seed(644)
    np.random.seed(645)
    torch.manual_seed(646)
    target = capture_rng_snapshot({"local": custom})
    expected = (
        random.random(),
        float(np.random.random()),
        float(torch.rand(())),
        float(torch.rand((), generator=custom)),
    )
    random.random()
    np.random.random()
    torch.rand(())
    torch.rand((), generator=custom)
    restore_rng_snapshot(target, {"local": custom})
    observed = (
        random.random(),
        float(np.random.random()),
        float(torch.rand(())),
        float(torch.rand((), generator=custom)),
    )
    assert observed == expected
    with pytest.raises(QWakeLC4BoundedError, match="custom RNG inventory"):
        restore_rng_snapshot(target, {})


def test_preserve_outer_rng_is_non_interfering() -> None:
    random.seed(647)
    np.random.seed(648)
    torch.manual_seed(649)
    outer = capture_rng_snapshot()
    with preserve_outer_rng():
        random.random()
        np.random.random()
        torch.rand(())
    assert capture_rng_snapshot().snapshot_sha256 == outer.snapshot_sha256


def test_balanced_schedule_and_all_synthetic_pairs_pass() -> None:
    schedule = pair_schedule()
    assert len(schedule) == PAIR_COUNT
    assert sum(order[0] is BoundedArm.EXACT_REFERENCE for order in schedule) == 6
    assert sum(order[0] is BoundedArm.ANALYTIC_CANDIDATE for order in schedule) == 6
    snapshot = _snapshot(1)
    rng = capture_rng_snapshot()
    authorization = BoundedUnitTestAuthorization.issue()
    for repeat_index in range(PAIR_COUNT):
        result = run_synthetic_matched_pair(
            snapshot,
            rng,
            repeat_index=repeat_index,
            authorization=authorization,
        )
        assert result.arm_order == schedule[repeat_index]
        assert result.passed
        assert result.response_comparison.response_defect <= 1.0
        assert result.exact_reference.rng_before_sha256 == rng.snapshot_sha256
        assert result.analytic_candidate.rng_before_sha256 == rng.snapshot_sha256


def test_forced_reserve_probe_completes_exact_registered_suffix() -> None:
    snapshot = _snapshot(1)
    probe = run_synthetic_reserve_probe(
        snapshot,
        capture_rng_snapshot(),
        authorization=BoundedUnitTestAuthorization.issue(),
    )
    assert probe.completed_suffix_indices == (2, 3)
    assert probe.passed
    assert probe.fallback_response_sha256 == (
        probe.direct_reference_response_sha256
    )


def test_synthetic_runner_rejects_non_synthetic_or_open_scientific_state() -> None:
    snapshot = _snapshot(1)
    unsafe = replace(
        snapshot,
        runtime_controls=(
            ("data_classification", "scientific_dataset"),
            ("runtime_execution_permitted", False),
            ("scientific_execution_open", False),
        ),
    )
    with pytest.raises(QWakeLC4BoundedError, match="non-synthetic"):
        run_synthetic_matched_pair(
            unsafe,
            capture_rng_snapshot(),
            repeat_index=0,
            authorization=BoundedUnitTestAuthorization.issue(),
        )

    authorization = replace(
        BoundedUnitTestAuthorization.issue(),
        scientific_execution_open=True,
    )
    with pytest.raises(QWakeLC4BoundedError, match="scientific capabilities"):
        authorization.require()


def test_response_predicate_fails_closed_on_state_mismatch() -> None:
    snapshot = _snapshot(1)
    exact_model, exact_frontier = snapshot.fork()
    completion = complete_exact_suffix(exact_model, exact_frontier)
    reference = materialize_required_response(
        exact_model,
        completion,
        state_id=snapshot.opaque_state_ref,
        comparison_profile_id=snapshot.comparison_profile_id,
    )
    mismatch = replace(
        reference,
        state_id="sha256:" + "0" * 64,
    )
    result = compare_required_responses(reference, mismatch)
    assert not result.structural_equal
    assert not result.passed



def _trajectory(
    *,
    action_id: str,
    repeat_index: int,
    opaque_state_ref: str,
    compute_shift: int = 0,
) -> ResourceTrajectory:
    return ResourceTrajectory(
        trajectory_schema_id="stage3b-qwake-resource-trajectory-v1",
        action_id=action_id,
        mechanism_id=action_id,
        opaque_state_ref=opaque_state_ref,
        repeat_index=repeat_index,
        lane_profile_id="cpu_float64_engineering",
        cost_profile_id="shadow_mechanism_v1",
        root_clock_domain="host_monotonic_ns",
        root_start_ns=100,
        root_end_ns=1100,
        intervals=(
            IntervalRecord(
                position=0,
                owner=IntervalOwner.CORE_COMPUTE,
                lane="host",
                clock_domain="host_process_time_ns",
                start_ns=10,
                end_ns=80 + compute_shift,
                source="core-a",
            ),
            IntervalRecord(
                position=1,
                owner=IntervalOwner.CORE_COMPUTE,
                lane="host",
                clock_domain="host_process_time_ns",
                start_ns=70,
                end_ns=100 + compute_shift,
                source="core-b",
            ),
            IntervalRecord(
                position=2,
                owner=IntervalOwner.DIAGNOSTIC,
                lane="host",
                clock_domain="host_process_time_ns",
                start_ns=110,
                end_ns=130,
                source="diagnostic",
            ),
            IntervalRecord(
                position=3,
                owner=IntervalOwner.OBSERVER,
                lane="host",
                clock_domain="host_process_time_ns",
                start_ns=140,
                end_ns=150,
                source="observer",
            ),
        ),
        memory=(
            MemoryRecord(
                metric="peak_allocated_bytes",
                value_bytes=4096,
                source="rss",
            ),
            MemoryRecord(
                metric="peak_reserved_bytes",
                value_bytes=8192,
                source="vms",
            ),
        ),
        artifacts=(
            ArtifactRecord(
                position=0,
                owner=IntervalOwner.DIAGNOSTIC,
                sha256="sha256:" + "1" * 64,
                size_bytes=32,
                source="diag-a",
            ),
            ArtifactRecord(
                position=1,
                owner=IntervalOwner.DIAGNOSTIC,
                sha256="sha256:" + "1" * 64,
                size_bytes=32,
                source="diag-duplicate",
            ),
            ArtifactRecord(
                position=2,
                owner=IntervalOwner.OBSERVER,
                sha256="sha256:" + "2" * 64,
                size_bytes=16,
                source="observer-a",
            ),
        ),
        observer_calibration=ObserverCalibration(
            pair_id="synthetic",
            instrumented_latency_ns=120,
            control_latency_ns=100,
            raw_residual_ns=20,
            overclosure=False,
        ),
        fallback=FallbackRecord(
            fallback_available=True,
            fallback_invoked=False,
            fallback_completed=False,
        ),
    )


def test_resource_trajectory_mapping_preserves_non_scalar_cost_vector() -> None:
    state_ref = _snapshot(1).opaque_state_ref
    vector = map_resource_trajectory(
        _trajectory(
            action_id=ANALYTIC_ACTION_ID,
            repeat_index=0,
            opaque_state_ref=state_ref,
        )
    )
    active = vector.active_values()
    assert active["compute_primary_time_ns"] == 90
    assert active["latency_wall_time_ns"] == 1000
    assert active["diagnostic_primary_time_ns"] == 20
    assert active["diagnostic_materialized_bytes"] == 32
    assert active["observer_overhead_time_ns"] == 20
    assert active["observer_evidence_bytes"] == 16
    assert "control_wall_time_ns" not in active
    assert "fallback_wall_time_ns" not in active
    assert not hasattr(vector, "total")


def test_paired_cost_aggregation_is_complete_componentwise_and_balanced() -> None:
    state_ref = _snapshot(1).opaque_state_ref
    pairs = []
    for repeat_index, order in enumerate(pair_schedule()):
        exact = map_resource_trajectory(
            _trajectory(
                action_id=EXACT_REFERENCE_ACTION_ID,
                repeat_index=repeat_index,
                opaque_state_ref=state_ref,
                compute_shift=0,
            )
        )
        candidate = map_resource_trajectory(
            _trajectory(
                action_id=ANALYTIC_ACTION_ID,
                repeat_index=repeat_index,
                opaque_state_ref=state_ref,
                compute_shift=-10,
            )
        )
        pairs.append(
            CostPair(
                repeat_index=repeat_index,
                arm_order=order,
                exact_reference=exact,
                analytic_candidate=candidate,
            )
        )
    aggregate = aggregate_paired_costs(pairs)
    summaries = dict(aggregate.field_summaries)
    assert aggregate.pair_complete
    assert aggregate.order_effect_passed
    assert summaries["compute_primary_time_ns"].median_paired_delta == -10.0
    assert summaries["compute_primary_time_ns"].minimum_paired_delta == -10
    assert summaries["compute_primary_time_ns"].maximum_paired_delta == -10


def test_resource_trajectory_fails_closed_on_duplicate_interval_ownership() -> None:
    trajectory = _trajectory(
        action_id=ANALYTIC_ACTION_ID,
        repeat_index=0,
        opaque_state_ref=_snapshot(1).opaque_state_ref,
    )
    duplicate = replace(
        trajectory.intervals[0],
        position=len(trajectory.intervals),
        owner=IntervalOwner.OBSERVER,
    )
    broken = replace(
        trajectory,
        intervals=trajectory.intervals + (duplicate,),
    )
    with pytest.raises(QWakeLC4BoundedError, match="duplicate semantic ownership"):
        map_resource_trajectory(broken)


def test_frozen_implementation_manifest_binds_exact_source_and_closed_gates() -> None:
    import hashlib
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    package = root / (
        "experiments/frozen/"
        "stage3b-qwake-lc4-i-bounded-implementation-v1"
    )
    assert sorted(path.name for path in package.iterdir()) == [
        "SHA256SUMS",
        "implementation.json",
    ]
    implementation_bytes = (package / "implementation.json").read_bytes()
    implementation_sha = hashlib.sha256(implementation_bytes).hexdigest()
    registry_text = (package / "SHA256SUMS").read_text(
        encoding="utf-8",
        errors="strict",
    )
    assert registry_text == f"{implementation_sha}  implementation.json\n"
    implementation = json.loads(implementation_bytes)
    assert implementation["implementation_id"] == (
        "stage3b-qwake-lc4-i-bounded-implementation-v1"
    )
    assert implementation["status"] == (
        "bounded_implementation_materialized_execution_closed"
    )
    source_path = root / implementation["module"]["path"]
    source_sha = hashlib.sha256(source_path.read_bytes()).hexdigest()
    assert implementation["module"]["sha256"] == f"sha256:{source_sha}"
    assert implementation["module"]["cli_entrypoint_present"] is False
    assert implementation["module"]["dataset_loader_present"] is False
    assert implementation["module"]["output_writer_present"] is False
    assert implementation["module"]["scientific_executor_present"] is False
    gates = implementation["gates"]
    assert gates["qw_lc3_complete"] is True
    assert gates["qw_lc4_i_implementation_materialized"] is True
    assert gates["qw_lc4_i_complete"] is False
    assert gates["qw_lc4_f_branch_permitted"] is False
    assert gates["synthetic_unit_test_only"] is True
    assert gates["local_compute_implementation_open"] is False
    assert gates["local_compute_execution_open"] is False
    assert gates["scientific_execution_open"] is False
    assert gates["test_dataset_access"] is False
    assert gates["publication_permitted"] is False
    assert implementation["next_slice"] == "QW-LC4-I-merge"
    assert implementation["post_merge_next_slice"] == "QW-LC4-F"


def test_status_and_bilingual_indexes_record_lc4_i_boundary() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    markers = (
        "qwake_qw_lc3_complete=true",
        "qwake_qw_lc4_i_authoring_open=true",
        "qwake_qw_lc4_i_implementation_materialized=true",
        "qwake_qw_lc4_i_complete=false",
        "qwake_qw_lc4_f_branch_permitted=false",
        "qwake_synthetic_unit_test_only=true",
        "qwake_local_compute_implementation_open=false",
        "qwake_local_compute_execution_open=false",
        "scientific_execution_open=false",
        "test_dataset_access=false",
        "publication_permitted=false",
        "qwake_next_slice=QW-LC4-I-merge",
        "qwake_post_merge_next_slice=QW-LC4-F",
    )
    for name, heading in (
        ("STATUS.md", "## `QW-LC4-I`: ограниченная реализация материализована"),
        ("STATUS_EN.md", "## `QW-LC4-I`: bounded implementation materialized"),
    ):
        text = (root / name).read_text(encoding="utf-8", errors="strict")
        section = text[text.index(heading) :]
        for marker in markers:
            assert marker in section, (name, marker)
    language_map = (root / "docs/language-map.csv").read_text(
        encoding="utf-8",
        errors="strict",
    )
    assert (
        "docs/decisions/ADR-061-stage3b-qwake-lc4-i-bounded-implementation.md,"
        "docs/decisions/ADR-061-stage3b-qwake-lc4-i-bounded-implementation_EN.md,"
        "required"
    ) in language_map
