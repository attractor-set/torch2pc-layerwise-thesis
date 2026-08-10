"""Prospective CPU-stabilized matrix executor for QWake Attempt-004.

The historical generic matrix executor remains immutable. This module adds a
separate wrapper that performs CPU process controls and discarded warm-up
cells, then delegates the complete measured matrix to the unchanged generic
executor.
"""

from __future__ import annotations

import os
from collections.abc import Callable

import torch

from torch2pc_thesis.stage3b_qwake_lc4_runtime_backend import (
    BoundedTorchMatrixExecutor,
    RuntimeCellRecord,
    RuntimeMatrixExecutor,
    RuntimeMatrixResult,
    execute_bounded_runtime_cell,
)
from torch2pc_thesis.stage3b_qwake_lc4_runtime_freeze import (
    RUNTIME_CANDIDATE_INDICES,
    QWakeLC4RuntimeAuthorization,
    RuntimeAuthorizationCell,
    RuntimeLane,
    runtime_authorization_cells,
)

PROFILE_ID = "stage3b-qwake-attempt-004-cpu-measurement-stabilization-v1"
ENABLE_ENV = "QWAKE_ATTEMPT_004_CPU_STABILIZATION"
CPU_PRIMARY_CLOCK = "time_process_time_ns"
CPU_AFFINITY = frozenset({0})
THREAD_ENV = {
    "OMP_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
}
WARMUP_REPEAT_INDICES = (2, 3)
WARMUP_PAIR_COUNT_PER_CANDIDATE = 2
WARMUP_CELL_COUNT = 14
MEASURED_PAIR_COUNT_PER_CANDIDATE = 12

_configured = False


class Attempt004CPUStabilizationError(RuntimeError):
    """Raised when the preregistered Attempt-004 CPU profile differs."""


def attempt004_cpu_stabilization_enabled() -> bool:
    value = os.environ.get(ENABLE_ENV)
    if value is None:
        return False
    if value != "1":
        raise Attempt004CPUStabilizationError(
            f"{ENABLE_ENV} must be exactly '1' when present"
        )
    return True


def configure_attempt004_cpu_measurement() -> None:
    """Require exact process/thread controls before warm-up or measurement."""

    global _configured

    if not attempt004_cpu_stabilization_enabled():
        raise Attempt004CPUStabilizationError(
            f"{ENABLE_ENV}=1 is required for Attempt-004 execution"
        )

    for name, expected in THREAD_ENV.items():
        if os.environ.get(name) != expected:
            raise Attempt004CPUStabilizationError(
                f"{name} must be exactly {expected}"
            )

    if not hasattr(os, "sched_getaffinity"):
        raise Attempt004CPUStabilizationError(
            "sched_getaffinity is required for Attempt-004"
        )
    affinity = frozenset(os.sched_getaffinity(0))
    if affinity != CPU_AFFINITY:
        raise Attempt004CPUStabilizationError(
            f"CPU affinity differs: expected [0], observed {sorted(affinity)}"
        )

    if not _configured:
        torch.set_num_threads(1)
        try:
            torch.set_num_interop_threads(1)
        except RuntimeError as exc:
            if torch.get_num_interop_threads() != 1:
                raise Attempt004CPUStabilizationError(
                    "PyTorch inter-op thread count could not be fixed at one"
                ) from exc
        _configured = True

    if torch.get_num_threads() != 1:
        raise Attempt004CPUStabilizationError(
            "PyTorch intra-op thread count differs"
        )
    if torch.get_num_interop_threads() != 1:
        raise Attempt004CPUStabilizationError(
            "PyTorch inter-op thread count differs"
        )


def attempt004_warmup_cells(
    cells: tuple[RuntimeAuthorizationCell, ...],
) -> tuple[RuntimeAuthorizationCell, ...]:
    """Select exact canonical CPU repeats 2 and 3 for discarded warm-up."""

    if cells != runtime_authorization_cells():
        raise Attempt004CPUStabilizationError(
            "Attempt-004 authorization matrix differs"
        )
    selected = tuple(
        cell
        for cell in cells
        if (
            cell.lane is RuntimeLane.CPU_FLOAT64_ENGINEERING
            and cell.repeat_index in WARMUP_REPEAT_INDICES
        )
    )
    expected = tuple(
        (candidate_index, repeat_index)
        for candidate_index in RUNTIME_CANDIDATE_INDICES
        for repeat_index in WARMUP_REPEAT_INDICES
    )
    observed = tuple(
        (cell.candidate_index, cell.repeat_index)
        for cell in selected
    )
    if len(selected) != WARMUP_CELL_COUNT or observed != expected:
        raise Attempt004CPUStabilizationError(
            "Attempt-004 warm-up matrix differs"
        )
    if any(
        cell.reserve_probe_before_repeat_zero
        or cell.reserve_probe_after_repeat_eleven
        for cell in selected
    ):
        raise Attempt004CPUStabilizationError(
            "Attempt-004 warm-up must be reserve-free"
        )
    return selected


WarmupRunner = Callable[[RuntimeAuthorizationCell], RuntimeCellRecord]


class Attempt004CPUStabilizedMatrixExecutor(RuntimeMatrixExecutor):
    """Warm the CPU path, then delegate the unchanged measured matrix."""

    def __init__(
        self,
        *,
        delegate: RuntimeMatrixExecutor | None = None,
        warmup_runner: WarmupRunner = execute_bounded_runtime_cell,
    ) -> None:
        self._delegate = (
            BoundedTorchMatrixExecutor()
            if delegate is None
            else delegate
        )
        self._warmup_runner = warmup_runner

    def execute(
        self,
        authorization: QWakeLC4RuntimeAuthorization,
    ) -> RuntimeMatrixResult:
        if authorization.cells != runtime_authorization_cells():
            raise Attempt004CPUStabilizationError(
                "Attempt-004 authorization matrix differs"
            )

        configure_attempt004_cpu_measurement()

        for cell in attempt004_warmup_cells(authorization.cells):
            self._warmup_runner(cell)

        result = self._delegate.execute(authorization)
        result.require(authorization)
        return result


def attempt004_cpu_measurement_evidence() -> dict[str, object]:
    """Return the preregistered CPU measurement profile."""

    return {
        "profile_id": PROFILE_ID,
        "integration_mode": "separate_runtime_matrix_executor_wrapper",
        "generic_runtime_backend_modified": False,
        "cpu_affinity": [0],
        "torch_num_threads": 1,
        "torch_num_interop_threads": 1,
        "OMP_NUM_THREADS": 1,
        "MKL_NUM_THREADS": 1,
        "OPENBLAS_NUM_THREADS": 1,
        "NUMEXPR_NUM_THREADS": 1,
        "cpu_primary_clock": CPU_PRIMARY_CLOCK,
        "warmup_repeat_indices": [2, 3],
        "cpu_warmup_pair_count_per_candidate": 2,
        "cpu_warmup_cell_count": 14,
        "warmup_reserve_probes": 0,
        "warmup_result_retained": False,
        "warmup_included_in_measured_matrix": False,
        "measured_pair_count_per_candidate": 12,
        "order_effect_tolerance_unchanged": True,
        "automatic_retry_permitted": False,
    }
