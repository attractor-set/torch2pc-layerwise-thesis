"""Effect-local runtime adapter contracts for QWake-FP validation.

The module binds the finite symbols frozen by QW-4A without importing Torch or
Torch2PC at module import time.  Every effectful function requires an explicit
validation permission guard and delegates to a backend object supplied by the
future authorized runtime request.  It does not construct a model, load a
dataset, issue an authorization, or execute a campaign by itself.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, is_dataclass
from enum import StrEnum
from typing import Any, Protocol, cast

from torch2pc_thesis.stage3b_qwake_core import (
    AnalyticClass,
    Capability,
    EdgeMeasurement,
    ObservationLevel,
)
from torch2pc_thesis.stage3b_qwake_fp_spec import (
    ANALYTIC_REGISTRY,
    OBSERVATION_REGISTRY,
    QWakeFPAnalyticId,
)
from torch2pc_thesis.stage3b_qwake_fp_validation import (
    EffectAudit,
    OracleIsolationRecord,
)


class QWakeFPRuntimeAdapterError(RuntimeError):
    """Raised when a live adapter violates the frozen QWake-FP contract."""


class CapabilityGuard(Protocol):
    """Minimal permission boundary required by effect-local adapters."""

    def require(self, *capabilities: Capability) -> None:
        """Raise unless every capability is currently authorized."""


@dataclass(frozen=True)
class ObservationCapture:
    """One cumulative observation payload emitted by a live backend."""

    level: ObservationLevel
    fields: tuple[tuple[str, object], ...]
    measurement: EdgeMeasurement
    effects: EffectAudit

    def __post_init__(self) -> None:
        expected = next(
            spec for spec in OBSERVATION_REGISTRY if spec.level is self.level
        )
        names = tuple(name for name, _value in self.fields)
        if names != expected.cumulative_fields:
            raise QWakeFPRuntimeAdapterError(
                f"{self.level.value} fields differ from the QW-2 registry"
            )
        if len(names) != len(set(names)):
            raise QWakeFPRuntimeAdapterError("observation fields cannot repeat")
        if self.effects.invocation_count < 1:
            raise QWakeFPRuntimeAdapterError("observation must record one invocation")
        if self.effects.output_count < len(names):
            raise QWakeFPRuntimeAdapterError(
                "observation output count is below the cumulative field count"
            )
        if self.level is ObservationLevel.A0 and (
            self.effects.tensor_read_count != 0
            or self.effects.temporary_allocation_count != 0
            or self.effects.synchronization_count != 0
            or self.effects.d2h_bytes != 0
        ):
            raise QWakeFPRuntimeAdapterError(
                "A0 must remain structural and tensor-free"
            )

    def payload_sha256(self) -> str:
        """Return a deterministic digest of the cumulative payload."""

        encoded = _canonical_json(dict(self.fields)).encode("utf-8")
        return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


@dataclass(frozen=True)
class AnalyticCapture:
    """One registered analytic output produced before the action boundary."""

    analytic_id: QWakeFPAnalyticId
    fields: tuple[tuple[str, object], ...]
    measurement: EdgeMeasurement
    effects: EffectAudit

    def __post_init__(self) -> None:
        expected = next(
            spec for spec in ANALYTIC_REGISTRY if spec.analytic_id is self.analytic_id
        )
        names = tuple(name for name, _value in self.fields)
        if names != expected.output_fields:
            raise QWakeFPRuntimeAdapterError(
                f"{self.analytic_id.value} output fields differ from QW-2"
            )
        if self.effects.invocation_count < 1:
            raise QWakeFPRuntimeAdapterError("analytic must record one invocation")
        if self.effects.output_count < len(names):
            raise QWakeFPRuntimeAdapterError(
                "analytic output count is below the registered field count"
            )

    def payload_sha256(self) -> str:
        encoded = _canonical_json(dict(self.fields)).encode("utf-8")
        return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


@dataclass(frozen=True)
class OracleCapture:
    """Post-action engineering oracle output and its ordering audit."""

    fields: tuple[tuple[str, object], ...]
    isolation: OracleIsolationRecord
    measurement: EdgeMeasurement
    effects: EffectAudit

    def __post_init__(self) -> None:
        if not self.isolation.passed:
            raise QWakeFPRuntimeAdapterError("post-action oracle isolation failed")
        if self.effects.invocation_count != 1:
            raise QWakeFPRuntimeAdapterError("oracle must be created exactly once")
        if self.effects.output_count < len(self.fields):
            raise QWakeFPRuntimeAdapterError(
                "oracle output count is below the emitted field count"
            )

    def payload_sha256(self) -> str:
        encoded = _canonical_json(dict(self.fields)).encode("utf-8")
        return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


class QWakeFPRuntimeBackend(Protocol):
    """Backend boundary implemented by the authorized CPU/ROCm runner."""

    def collect_observation(self, level: ObservationLevel) -> ObservationCapture:
        """Collect exactly one cumulative A0/A1/A2 observation."""

    def run_analytic(self, analytic_id: QWakeFPAnalyticId) -> AnalyticCapture:
        """Run one frozen analytic implementation."""

    def compute_post_action_oracle(self) -> OracleCapture:
        """Create the engineering oracle after canonical completion."""

    def record_edge_costs(self) -> EdgeMeasurement:
        """Return the current non-overlapping edge-cost record."""


_ANALYTIC_CAPABILITIES: Mapping[QWakeFPAnalyticId, tuple[Capability, ...]] = {
    QWakeFPAnalyticId.ROSENBAUM_WAVEFRONT_STATUS_V1: (
        Capability.RUN_LIVE_ANALYTICS,
        Capability.RUN_ANALYTIC_EXACT,
    ),
    QWakeFPAnalyticId.RESIDUAL_PERSISTENCE_V1: (
        Capability.RUN_LIVE_ANALYTICS,
        Capability.RUN_ANALYTIC_HEURISTIC,
    ),
    QWakeFPAnalyticId.COST_DOMINANCE_V1: (
        Capability.RUN_LIVE_ANALYTICS,
        Capability.RUN_ANALYTIC_CONSERVATIVE,
        Capability.RUN_COST_DOMINANCE_CHECK,
    ),
}

_OBSERVATION_CAPABILITY: Mapping[ObservationLevel, Capability] = {
    ObservationLevel.A0: Capability.COLLECT_A0,
    ObservationLevel.A1: Capability.COLLECT_A1,
    ObservationLevel.A2: Capability.COLLECT_A2,
}


def collect_A0(
    guard: CapabilityGuard,
    backend: QWakeFPRuntimeBackend,
) -> ObservationCapture:
    """Collect structural A0 after an effect-local capability check."""

    return _collect_observation(guard, backend, ObservationLevel.A0)


def collect_A1(
    guard: CapabilityGuard,
    backend: QWakeFPRuntimeBackend,
) -> ObservationCapture:
    """Collect cumulative A1 after an effect-local capability check."""

    return _collect_observation(guard, backend, ObservationLevel.A1)


def collect_A2(
    guard: CapabilityGuard,
    backend: QWakeFPRuntimeBackend,
) -> ObservationCapture:
    """Collect cumulative A2 after an effect-local capability check."""

    return _collect_observation(guard, backend, ObservationLevel.A2)


def run_registered_analytics(
    guard: CapabilityGuard,
    backend: QWakeFPRuntimeBackend,
    analytic_ids: Sequence[QWakeFPAnalyticId],
) -> tuple[AnalyticCapture, ...]:
    """Run only the frozen finite analytic registry in requested order."""

    if not analytic_ids:
        raise QWakeFPRuntimeAdapterError("analytic request cannot be empty")
    if len(analytic_ids) != len(set(analytic_ids)):
        raise QWakeFPRuntimeAdapterError("analytic request cannot contain duplicates")
    allowed = tuple(spec.analytic_id for spec in ANALYTIC_REGISTRY)
    if any(analytic_id not in allowed for analytic_id in analytic_ids):
        raise QWakeFPRuntimeAdapterError("analytic request is outside the registry")
    captures: list[AnalyticCapture] = []
    for analytic_id in analytic_ids:
        guard.require(*_ANALYTIC_CAPABILITIES[analytic_id])
        capture = backend.run_analytic(analytic_id)
        if capture.analytic_id is not analytic_id:
            raise QWakeFPRuntimeAdapterError("backend returned the wrong analytic")
        captures.append(capture)
    return tuple(captures)


def compute_post_action_oracle(
    guard: CapabilityGuard,
    backend: QWakeFPRuntimeBackend,
) -> OracleCapture:
    """Create the engineering oracle only after the backend action boundary."""

    guard.require(Capability.COMPUTE_POST_ACTION_ORACLE)
    return backend.compute_post_action_oracle()


def record_edge_costs(
    guard: CapabilityGuard,
    backend: QWakeFPRuntimeBackend,
) -> EdgeMeasurement:
    """Read the explicit raw edge-cost record without remapping it."""

    guard.require(Capability.RUN_COST_DOMINANCE_CHECK)
    return backend.record_edge_costs()


def _collect_observation(
    guard: CapabilityGuard,
    backend: QWakeFPRuntimeBackend,
    level: ObservationLevel,
) -> ObservationCapture:
    guard.require(_OBSERVATION_CAPABILITY[level])
    capture = backend.collect_observation(level)
    if capture.level is not level:
        raise QWakeFPRuntimeAdapterError("backend returned the wrong observation level")
    return capture


def analytic_class_for(analytic_id: QWakeFPAnalyticId) -> AnalyticClass:
    """Expose the frozen analytic class for runtime admission checks."""

    return next(
        spec.analytic_class
        for spec in ANALYTIC_REGISTRY
        if spec.analytic_id is analytic_id
    )


def _canonicalize(value: object) -> object:
    if isinstance(value, StrEnum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return _canonicalize(asdict(cast(Any, value)))
    if isinstance(value, Mapping):
        return {
            str(key): _canonicalize(item)
            for key, item in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, tuple | list):
        return [_canonicalize(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        raise QWakeFPRuntimeAdapterError(
            "runtime payload cannot contain non-finite floats"
        )
    if value is None or isinstance(value, bool | int | float | str):
        return value
    raise QWakeFPRuntimeAdapterError(
        f"runtime payload is not canonical JSON data: {type(value).__name__}"
    )


def _canonical_json(value: object) -> str:
    return json.dumps(
        _canonicalize(value),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
