from __future__ import annotations

import hashlib
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

import torch2pc_thesis.stage3b_qwake_attempt_004_cpu_measurement_stabilization as profile
from torch2pc_thesis.stage3b_qwake_lc4_runtime_backend import RuntimeMatrixExecutor
from torch2pc_thesis.stage3b_qwake_lc4_runtime_freeze import (
    RUNTIME_CANDIDATE_INDICES,
    runtime_authorization_cells,
)

ROOT = Path(__file__).resolve().parents[2]
GENERIC_BACKEND = (
    ROOT / "src/torch2pc_thesis/stage3b_qwake_lc4_runtime_backend.py"
)
GENERIC_BACKEND_SHA256 = (
    "d9ad10efe959e19d7f1b6d61d8eddd1228cb9753fa9191823d5d1ded68e9fd72"
)


def test_generic_backend_remains_byte_exact() -> None:
    assert hashlib.sha256(GENERIC_BACKEND.read_bytes()).hexdigest() == (
        GENERIC_BACKEND_SHA256
    )


def test_profile_is_disabled_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(profile.ENABLE_ENV, raising=False)
    assert profile.attempt004_cpu_stabilization_enabled() is False


def test_noncanonical_opt_in_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(profile.ENABLE_ENV, "true")
    with pytest.raises(profile.Attempt004CPUStabilizationError):
        profile.attempt004_cpu_stabilization_enabled()


def test_warmup_selection_is_symmetric_and_reserve_free() -> None:
    selected = profile.attempt004_warmup_cells(runtime_authorization_cells())
    assert len(selected) == 14
    assert tuple(
        (cell.candidate_index, cell.repeat_index)
        for cell in selected
    ) == tuple(
        (candidate_index, repeat_index)
        for candidate_index in RUNTIME_CANDIDATE_INDICES
        for repeat_index in (2, 3)
    )
    assert all(
        not cell.reserve_probe_before_repeat_zero
        and not cell.reserve_probe_after_repeat_eleven
        for cell in selected
    )


def test_configuration_requires_exact_process_controls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(profile.ENABLE_ENV, "1")
    for name in profile.THREAD_ENV:
        monkeypatch.setenv(name, "1")
    monkeypatch.setattr(profile.os, "sched_getaffinity", lambda _: {0})
    monkeypatch.setattr(profile, "_configured", False)

    intra: list[int] = []
    inter: list[int] = []
    monkeypatch.setattr(profile.torch, "set_num_threads", intra.append)
    monkeypatch.setattr(profile.torch, "set_num_interop_threads", inter.append)
    monkeypatch.setattr(profile.torch, "get_num_threads", lambda: 1)
    monkeypatch.setattr(profile.torch, "get_num_interop_threads", lambda: 1)

    profile.configure_attempt004_cpu_measurement()
    assert intra == [1]
    assert inter == [1]


def test_configuration_rejects_wrong_affinity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(profile.ENABLE_ENV, "1")
    for name in profile.THREAD_ENV:
        monkeypatch.setenv(name, "1")
    monkeypatch.setattr(profile.os, "sched_getaffinity", lambda _: {0, 1})
    with pytest.raises(profile.Attempt004CPUStabilizationError):
        profile.configure_attempt004_cpu_measurement()


def test_executor_warms_then_delegates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, object]] = []

    monkeypatch.setattr(
        profile,
        "configure_attempt004_cpu_measurement",
        lambda: calls.append(("configure", None)),
    )

    def warmup(cell: object) -> Any:
        calls.append(
            (
                "warmup",
                (
                    cell.candidate_index,
                    cell.repeat_index,
                ),
            )
        )
        return object()

    class FakeResult:
        def require(self, authorization: object) -> None:
            calls.append(("require", authorization))

    result = FakeResult()

    class FakeDelegate:
        def execute(self, authorization: object) -> Any:
            calls.append(("delegate", authorization))
            return result

    authorization = SimpleNamespace(cells=runtime_authorization_cells())
    executor = profile.Attempt004CPUStabilizedMatrixExecutor(
        delegate=cast(RuntimeMatrixExecutor, FakeDelegate()),
        warmup_runner=cast(Any, warmup),
    )
    observed = executor.execute(cast(Any, authorization))

    assert observed is result
    assert calls[0] == ("configure", None)
    assert [value for kind, value in calls if kind == "warmup"] == [
        (candidate_index, repeat_index)
        for candidate_index in RUNTIME_CANDIDATE_INDICES
        for repeat_index in (2, 3)
    ]
    assert calls[-2] == ("delegate", authorization)
    assert calls[-1] == ("require", authorization)


def test_evidence_freezes_separate_executor_protocol() -> None:
    payload = profile.attempt004_cpu_measurement_evidence()
    assert payload["generic_runtime_backend_modified"] is False
    assert payload["cpu_affinity"] == [0]
    assert payload["cpu_warmup_cell_count"] == 14
    assert payload["warmup_reserve_probes"] == 0
    assert payload["warmup_result_retained"] is False
    assert payload["warmup_included_in_measured_matrix"] is False
    assert payload["measured_pair_count_per_candidate"] == 12
    assert payload["order_effect_tolerance_unchanged"] is True
