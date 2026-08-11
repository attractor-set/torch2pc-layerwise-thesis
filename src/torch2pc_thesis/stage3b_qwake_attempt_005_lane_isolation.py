"""Prospective lane-isolated matrix executor for QWake Attempt-005.

The frozen scientific matrix, clocks, paired schedule, reserve probes and
order-effect tolerances are unchanged.  CPU and ROCm lanes execute in separate
Python processes so the Attempt-004 CPU stabilization controls cannot leak into
the canonical ROCm host-control profile.  Warm-up cells are explicitly
excluded from the measured 168-cell matrix.
"""

from __future__ import annotations

import argparse
import os
import pickle
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Final, cast

from torch2pc_thesis import stage3b_qwake_lc4_runtime_backend as generic_runtime
from torch2pc_thesis.stage3b_qwake_attempt_004_cpu_measurement_stabilization import (
    CPU_AFFINITY,
    WARMUP_REPEAT_INDICES,
    configure_attempt004_cpu_measurement,
)
from torch2pc_thesis.stage3b_qwake_attempt_004_cpu_measurement_stabilization import (
    THREAD_ENV as CPU_THREAD_ENV,
)
from torch2pc_thesis.stage3b_qwake_lc4_bounded import (
    CostPair,
    aggregate_paired_costs,
    capture_rng_snapshot,
    preserve_outer_rng,
)
from torch2pc_thesis.stage3b_qwake_lc4_runtime_backend import (
    ReserveProbeRecord,
    RuntimeCellRecord,
    RuntimeMatrixExecutor,
    RuntimeMatrixResult,
)
from torch2pc_thesis.stage3b_qwake_lc4_runtime_freeze import (
    RUNTIME_CANDIDATE_INDICES,
    QWakeLC4RuntimeAuthorization,
    RuntimeAuthorizationCell,
    RuntimeLane,
    runtime_authorization_cells,
)

PROFILE_ID: Final = "stage3b-qwake-attempt-005-lane-isolation-v1"
ENABLE_ENV: Final = "QWAKE_ATTEMPT_005_LANE_ISOLATION"
ROCM_CPU_AFFINITY: Final = frozenset(range(8))
ROCM_THREAD_ENV: Final = {
    "OMP_NUM_THREADS": "8",
    "MKL_NUM_THREADS": "8",
    "OPENBLAS_NUM_THREADS": "8",
    "NUMEXPR_NUM_THREADS": "8",
}
HIP_VISIBLE_DEVICES: Final = "0"
WARMUP_PAIR_COUNT_PER_CANDIDATE: Final = 2
WARMUP_CELL_COUNT_PER_LANE: Final = 14
MEASURED_CELL_COUNT_PER_LANE: Final = 84
RESERVE_PROBE_COUNT_PER_LANE: Final = 14
AGGREGATE_COUNT_PER_LANE: Final = 7
INTERNAL_LANE_WORKER_COUNT: Final = 2
WORKER_TIMEOUT_SECONDS: Final = 3600


class Attempt005LaneIsolationError(RuntimeError):
    """Raised when the prospective Attempt-005 lane profile differs."""


def _require_enabled() -> None:
    if os.environ.get(ENABLE_ENV) != "1":
        raise Attempt005LaneIsolationError(f"{ENABLE_ENV}=1 is required")


def _require_exact_affinity(expected: frozenset[int], label: str) -> None:
    if not hasattr(os, "sched_getaffinity"):
        raise Attempt005LaneIsolationError("sched_getaffinity is required")
    observed = frozenset(os.sched_getaffinity(0))
    if observed != expected:
        raise Attempt005LaneIsolationError(
            f"{label} affinity differs: expected {sorted(expected)}, "
            f"observed {sorted(observed)}"
        )


def _require_thread_env(expected: Mapping[str, str], label: str) -> None:
    for name, value in expected.items():
        if os.environ.get(name) != value:
            raise Attempt005LaneIsolationError(
                f"{label} {name} must be exactly {value}"
            )


def _warmup_cells(
    authorization: QWakeLC4RuntimeAuthorization,
    lane: RuntimeLane,
) -> tuple[RuntimeAuthorizationCell, ...]:
    if authorization.cells != runtime_authorization_cells():
        raise Attempt005LaneIsolationError(
            "Attempt-005 authorization matrix differs"
        )
    selected = tuple(
        cell
        for cell in authorization.cells
        if cell.lane is lane and cell.repeat_index in WARMUP_REPEAT_INDICES
    )
    expected = tuple(
        (candidate_index, repeat_index)
        for candidate_index in RUNTIME_CANDIDATE_INDICES
        for repeat_index in WARMUP_REPEAT_INDICES
    )
    observed = tuple(
        (cell.candidate_index, cell.repeat_index) for cell in selected
    )
    if len(selected) != WARMUP_CELL_COUNT_PER_LANE or observed != expected:
        raise Attempt005LaneIsolationError(
            f"{lane.value} warm-up matrix differs"
        )
    if any(
        cell.reserve_probe_before_repeat_zero
        or cell.reserve_probe_after_repeat_eleven
        for cell in selected
    ):
        raise Attempt005LaneIsolationError("warm-up must be reserve-free")
    return selected


def _configure_cpu_worker() -> None:
    _require_enabled()
    if not hasattr(os, "sched_setaffinity"):
        raise Attempt005LaneIsolationError("sched_setaffinity is required")
    os.sched_setaffinity(0, CPU_AFFINITY)
    _require_exact_affinity(CPU_AFFINITY, "CPU worker")
    _require_thread_env(CPU_THREAD_ENV, "CPU worker")
    configure_attempt004_cpu_measurement()


def _configure_rocm_worker() -> None:
    _require_enabled()
    _require_exact_affinity(ROCM_CPU_AFFINITY, "ROCm worker")
    _require_thread_env(ROCM_THREAD_ENV, "ROCm worker")
    if os.environ.get("HIP_VISIBLE_DEVICES") != HIP_VISIBLE_DEVICES:
        raise Attempt005LaneIsolationError(
            "ROCm worker HIP_VISIBLE_DEVICES must be exactly 0"
        )
    if "QWAKE_ATTEMPT_004_CPU_STABILIZATION" in os.environ:
        raise Attempt005LaneIsolationError(
            "Attempt-004 CPU stabilization leaked into ROCm worker"
        )


def _execute_lane(
    authorization: QWakeLC4RuntimeAuthorization,
    lane: RuntimeLane,
) -> tuple[
    tuple[RuntimeCellRecord, ...],
    tuple[ReserveProbeRecord, ...],
    tuple[Mapping[str, object], ...],
]:
    if authorization.cells != runtime_authorization_cells():
        raise Attempt005LaneIsolationError(
            "Attempt-005 authorization matrix differs"
        )
    if lane is RuntimeLane.CPU_FLOAT64_ENGINEERING:
        _configure_cpu_worker()
        cell_offset = 0
        probe_offset = 0
    else:
        _configure_rocm_worker()
        cell_offset = MEASURED_CELL_COUNT_PER_LANE
        probe_offset = RESERVE_PROBE_COUNT_PER_LANE

    for cell in _warmup_cells(authorization, lane):
        generic_runtime.execute_bounded_runtime_cell(cell)

    lane_cells = tuple(cell for cell in authorization.cells if cell.lane is lane)
    grouped: dict[int, list[RuntimeAuthorizationCell]] = {}
    for cell in lane_cells:
        grouped.setdefault(cell.candidate_index, []).append(cell)

    cells: list[RuntimeCellRecord] = []
    probes: list[ReserveProbeRecord] = []
    aggregates: list[Mapping[str, object]] = []
    cell_position = cell_offset
    probe_position = probe_offset

    for candidate_index in RUNTIME_CANDIDATE_INDICES:
        group = grouped[candidate_index]
        if tuple(item.repeat_index for item in group) != tuple(range(12)):
            raise Attempt005LaneIsolationError(
                "lane measured repeat order differs"
            )
        with preserve_outer_rng():
            snapshot, normalization = generic_runtime._build_snapshot(lane, candidate_index)
            rng_snapshot = capture_rng_snapshot()
            cost_pairs: list[CostPair] = []
            for cell in group:
                if cell.reserve_probe_before_repeat_zero:
                    probes.append(
                        generic_runtime._run_reserve_probe(
                            snapshot,
                            rng_snapshot,
                            lane=lane,
                            candidate_index=candidate_index,
                            placement="before_repeat_zero",
                            position=probe_position,
                        )
                    )
                    probe_position += 1
                record, cost_pair = generic_runtime._run_matched_cell(
                    snapshot,
                    rng_snapshot,
                    cell,
                    position=cell_position,
                )
                cells.append(record)
                cost_pairs.append(cost_pair)
                cell_position += 1
                if cell.reserve_probe_after_repeat_eleven:
                    probes.append(
                        generic_runtime._run_reserve_probe(
                            snapshot,
                            rng_snapshot,
                            lane=lane,
                            candidate_index=candidate_index,
                            placement="after_repeat_eleven",
                            position=probe_position,
                        )
                    )
                    probe_position += 1
            aggregation = aggregate_paired_costs(cost_pairs)
            aggregates.append(
                generic_runtime._aggregation_payload(
                    lane,
                    candidate_index,
                    snapshot.opaque_state_ref,
                    aggregation,
                    normalization,
                )
            )

    if len(cells) != MEASURED_CELL_COUNT_PER_LANE:
        raise Attempt005LaneIsolationError("lane measured cell count differs")
    if len(probes) != RESERVE_PROBE_COUNT_PER_LANE:
        raise Attempt005LaneIsolationError("lane reserve-probe count differs")
    if len(aggregates) != AGGREGATE_COUNT_PER_LANE:
        raise Attempt005LaneIsolationError("lane aggregate count differs")
    return tuple(cells), tuple(probes), tuple(aggregates)


def _worker_env(lane: RuntimeLane) -> dict[str, str]:
    env = os.environ.copy()
    env[ENABLE_ENV] = "1"
    env["HIP_VISIBLE_DEVICES"] = HIP_VISIBLE_DEVICES
    if lane is RuntimeLane.CPU_FLOAT64_ENGINEERING:
        env.update(CPU_THREAD_ENV)
        env["QWAKE_ATTEMPT_004_CPU_STABILIZATION"] = "1"
    else:
        env.update(ROCM_THREAD_ENV)
        env.pop("QWAKE_ATTEMPT_004_CPU_STABILIZATION", None)
    return env


def _run_worker(lane: RuntimeLane) -> tuple[
    tuple[RuntimeCellRecord, ...],
    tuple[ReserveProbeRecord, ...],
    tuple[Mapping[str, object], ...],
]:
    argv = (
        sys.executable,
        "-m",
        "torch2pc_thesis.stage3b_qwake_attempt_005_lane_isolation",
        "--worker-lane",
        lane.value,
    )
    result = subprocess.run(
        argv,
        env=_worker_env(lane),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=False,
        timeout=WORKER_TIMEOUT_SECONDS,
    )
    if result.returncode != 0:
        stderr = (result.stderr or b"").decode("utf-8", errors="replace")
        raise Attempt005LaneIsolationError(
            f"{lane.value} worker failed with {result.returncode}: {stderr}"
        )
    try:
        payload = pickle.loads(result.stdout or b"")  # noqa: S301 - trusted child IPC
    except Exception as exc:
        raise Attempt005LaneIsolationError(
            f"{lane.value} worker result could not be decoded"
        ) from exc
    if not isinstance(payload, tuple) or len(payload) != 3:
        raise Attempt005LaneIsolationError("lane worker payload differs")
    cells, probes, aggregates = payload
    if not isinstance(cells, tuple) or not all(
        isinstance(item, RuntimeCellRecord) for item in cells
    ):
        raise Attempt005LaneIsolationError("lane worker cells differ")
    if not isinstance(probes, tuple) or not all(
        isinstance(item, ReserveProbeRecord) for item in probes
    ):
        raise Attempt005LaneIsolationError("lane worker probes differ")
    if not isinstance(aggregates, tuple) or not all(
        isinstance(item, Mapping) for item in aggregates
    ):
        raise Attempt005LaneIsolationError("lane worker aggregates differ")
    return cast(tuple[RuntimeCellRecord, ...], cells), cast(
        tuple[ReserveProbeRecord, ...], probes
    ), cast(tuple[Mapping[str, object], ...], aggregates)


class Attempt005LaneIsolatedMatrixExecutor(RuntimeMatrixExecutor):
    """Run the two frozen lanes in distinct child processes and combine them."""

    def execute(
        self,
        authorization: QWakeLC4RuntimeAuthorization,
    ) -> RuntimeMatrixResult:
        _require_enabled()
        _require_exact_affinity(ROCM_CPU_AFFINITY, "Attempt-005 parent")
        _require_thread_env(ROCM_THREAD_ENV, "Attempt-005 parent")
        if authorization.cells != runtime_authorization_cells():
            raise Attempt005LaneIsolationError(
                "Attempt-005 authorization matrix differs"
            )

        cpu = _run_worker(RuntimeLane.CPU_FLOAT64_ENGINEERING)
        rocm = _run_worker(RuntimeLane.ROCM_FLOAT32_CANONICAL)
        result = RuntimeMatrixResult(
            cells=cpu[0] + rocm[0],
            reserve_probes=cpu[1] + rocm[1],
            aggregates=cpu[2] + rocm[2],
        )
        result.require(authorization)
        return result


def attempt005_lane_isolation_evidence() -> dict[str, object]:
    """Return the prospective lane-local execution profile."""

    return {
        "profile_id": PROFILE_ID,
        "lane_process_isolation": True,
        "internal_lane_worker_count": INTERNAL_LANE_WORKER_COUNT,
        "automatic_worker_retry_permitted": False,
        "generic_runtime_backend_modified": False,
        "measured_authorized_cell_count": 168,
        "measured_pair_count_per_candidate": 12,
        "reserve_probe_count": 28,
        "aggregate_count": 14,
        "order_effect_tolerance_unchanged": True,
        "cpu_primary_clock": "time_process_time_ns",
        "rocm_primary_clock": "rocm_event_time_ns",
        "cpu_worker_affinity": [0],
        "cpu_worker_torch_num_threads": 1,
        "cpu_worker_torch_num_interop_threads": 1,
        "cpu_worker_thread_env": {key: int(value) for key, value in CPU_THREAD_ENV.items()},
        "cpu_warmup_repeat_indices": list(WARMUP_REPEAT_INDICES),
        "cpu_warmup_cell_count": WARMUP_CELL_COUNT_PER_LANE,
        "rocm_worker_affinity": sorted(ROCM_CPU_AFFINITY),
        "rocm_worker_thread_env": {key: int(value) for key, value in ROCM_THREAD_ENV.items()},
        "rocm_hip_visible_devices": HIP_VISIBLE_DEVICES,
        "rocm_warmup_repeat_indices": list(WARMUP_REPEAT_INDICES),
        "rocm_warmup_cell_count": WARMUP_CELL_COUNT_PER_LANE,
        "warmup_result_retained": False,
        "warmup_included_in_measured_matrix": False,
        "cross_lane_comparison_permitted": False,
        "single_combined_runtime_report_required": True,
    }


def _worker_main(lane: RuntimeLane) -> int:
    from torch2pc_thesis.stage3b_qwake_lc4_runtime_freeze import (
        load_runtime_authorization,
    )

    authorization = load_runtime_authorization(
        Path.cwd()
        / "experiments/frozen/stage3b-qwake-lc4-f-runtime-freeze-v1/authorization.json"
    )
    payload = _execute_lane(authorization, lane)
    sys.stdout.buffer.write(pickle.dumps(payload, protocol=5))
    sys.stdout.buffer.flush()
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--worker-lane",
        choices=[item.value for item in RuntimeLane],
        required=True,
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    raise SystemExit(_worker_main(RuntimeLane(args.worker_lane)))
