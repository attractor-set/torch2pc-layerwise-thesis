from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import random
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn

from torch2pc_thesis.stage3b_b1_isolated_vjp import B1SweepSnapshot

type JsonScalar = bool | float | int | str | None
type JsonValue = Any
type OptionalTensorMap = dict[str, torch.Tensor | None]


@dataclass(frozen=True)
class ThresholdProfile:
    lane: str
    min_cosine: float
    max_relative_l2: float
    max_abs: float
    zero_atol: float


THRESHOLD_PROFILES: dict[str, ThresholdProfile] = {
    "cpu_float64": ThresholdProfile(
        lane="cpu_float64",
        min_cosine=0.99999,
        max_relative_l2=1.0e-7,
        max_abs=1.0e-9,
        zero_atol=1.0e-12,
    ),
    "rocm_float32": ThresholdProfile(
        lane="rocm_float32",
        min_cosine=0.999,
        max_relative_l2=1.0e-3,
        max_abs=1.0e-5,
        zero_atol=1.0e-7,
    ),
}


@dataclass(frozen=True)
class TensorMetric:
    component: str
    passed: bool
    finite: bool
    presence_match: bool
    reference_l2: float | None
    candidate_l2: float | None
    difference_l2: float | None
    relative_l2: float | None
    cosine: float | None
    max_abs: float | None
    zero_case: str

    def to_row(self) -> dict[str, JsonScalar]:
        return asdict(self)


@dataclass(frozen=True)
class ScalarMetric:
    component: str
    passed: bool
    reference: JsonScalar
    candidate: JsonScalar

    def to_row(self) -> dict[str, JsonScalar]:
        return asdict(self)


@dataclass(frozen=True)
class GateOutcome:
    gate_id: str
    passed: bool
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "gate_id": self.gate_id,
            "passed": self.passed,
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True)
class RngSnapshot:
    python_state: Any
    numpy_state: Any
    torch_cpu_state: torch.Tensor
    torch_accelerator_states: tuple[torch.Tensor, ...]


@dataclass(frozen=True)
class OptimizerSnapshot:
    tensor_state: dict[str, torch.Tensor]
    scalar_state: dict[str, JsonScalar]


@dataclass(frozen=True)
class RunEndpoints:
    loss: torch.Tensor
    output_cotangent: torch.Tensor
    final_beliefs: tuple[torch.Tensor | None, ...]
    final_prediction_errors: tuple[torch.Tensor | None, ...]
    gradients: dict[str, torch.Tensor]
    parameters_after_step: dict[str, torch.Tensor]
    optimizer: OptimizerSnapshot
    inference_steps: int
    rng_before: str
    rng_after: str


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_json_digest(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def capture_rng_snapshot() -> RngSnapshot:
    accelerator_states: tuple[torch.Tensor, ...] = ()
    if torch.cuda.is_available():
        accelerator_states = tuple(
            state.detach().cpu().clone() for state in torch.cuda.get_rng_state_all()
        )
    return RngSnapshot(
        python_state=random.getstate(),
        numpy_state=np.random.get_state(),
        torch_cpu_state=torch.get_rng_state().detach().cpu().clone(),
        torch_accelerator_states=accelerator_states,
    )


def restore_rng_snapshot(snapshot: RngSnapshot) -> None:
    random.setstate(snapshot.python_state)
    np.random.set_state(snapshot.numpy_state)
    torch.set_rng_state(snapshot.torch_cpu_state)
    if snapshot.torch_accelerator_states:
        torch.cuda.set_rng_state_all(list(snapshot.torch_accelerator_states))


def rng_snapshot_digest(snapshot: RngSnapshot) -> str:
    digest = hashlib.sha256()
    digest.update(repr(snapshot.python_state).encode("utf-8"))
    digest.update(repr(snapshot.numpy_state[:-1]).encode("utf-8"))
    numpy_values = np.asarray(snapshot.numpy_state[1], dtype=np.uint32)
    digest.update(numpy_values.tobytes())
    digest.update(snapshot.torch_cpu_state.numpy().tobytes())
    for state in snapshot.torch_accelerator_states:
        digest.update(state.numpy().tobytes())
    return digest.hexdigest()


def compare_optional_tensors(
    component: str,
    reference: torch.Tensor | None,
    candidate: torch.Tensor | None,
    profile: ThresholdProfile,
) -> TensorMetric:
    if reference is None or candidate is None:
        matched = reference is None and candidate is None
        return TensorMetric(
            component=component,
            passed=matched,
            finite=matched,
            presence_match=matched,
            reference_l2=None,
            candidate_l2=None,
            difference_l2=None,
            relative_l2=None,
            cosine=None,
            max_abs=None,
            zero_case="both_missing" if matched else "presence_mismatch",
        )
    return compare_tensors(component, reference, candidate, profile)


def compare_tensors(
    component: str,
    reference: torch.Tensor,
    candidate: torch.Tensor,
    profile: ThresholdProfile,
) -> TensorMetric:
    if reference.shape != candidate.shape:
        return TensorMetric(
            component=component,
            passed=False,
            finite=False,
            presence_match=True,
            reference_l2=None,
            candidate_l2=None,
            difference_l2=None,
            relative_l2=None,
            cosine=None,
            max_abs=None,
            zero_case="shape_mismatch",
        )

    reference_flat = reference.detach().to(device="cpu", dtype=torch.float64).reshape(-1)
    candidate_flat = candidate.detach().to(device="cpu", dtype=torch.float64).reshape(-1)
    finite = bool(
        torch.isfinite(reference_flat).all().item()
        and torch.isfinite(candidate_flat).all().item()
    )
    if not finite:
        return TensorMetric(
            component=component,
            passed=False,
            finite=False,
            presence_match=True,
            reference_l2=None,
            candidate_l2=None,
            difference_l2=None,
            relative_l2=None,
            cosine=None,
            max_abs=None,
            zero_case="non_finite",
        )

    reference_l2 = float(torch.linalg.vector_norm(reference_flat).item())
    candidate_l2 = float(torch.linalg.vector_norm(candidate_flat).item())
    difference = candidate_flat - reference_flat
    difference_l2 = float(torch.linalg.vector_norm(difference).item())
    max_abs = float(torch.max(torch.abs(difference)).item()) if difference.numel() else 0.0
    scale = max(reference_l2, candidate_l2, profile.zero_atol)
    relative_l2 = difference_l2 / scale
    reference_active = reference_l2 > profile.zero_atol
    candidate_active = candidate_l2 > profile.zero_atol

    cosine: float | None
    if not reference_active and not candidate_active:
        cosine = None
        zero_case = "both_zero"
        cosine_pass = True
    elif reference_active != candidate_active:
        cosine = None
        zero_case = "one_zero"
        cosine_pass = False
    else:
        denominator = reference_l2 * candidate_l2
        cosine = float(torch.dot(reference_flat, candidate_flat).item() / denominator)
        zero_case = "both_active"
        cosine_pass = cosine >= profile.min_cosine

    passed = (
        cosine_pass
        and relative_l2 <= profile.max_relative_l2
        and max_abs <= profile.max_abs
    )
    return TensorMetric(
        component=component,
        passed=passed,
        finite=True,
        presence_match=True,
        reference_l2=reference_l2,
        candidate_l2=candidate_l2,
        difference_l2=difference_l2,
        relative_l2=relative_l2,
        cosine=cosine,
        max_abs=max_abs,
        zero_case=zero_case,
    )


def compare_tensor_maps(
    reference: Mapping[str, torch.Tensor | None],
    candidate: Mapping[str, torch.Tensor | None],
    profile: ThresholdProfile,
) -> list[TensorMetric]:
    names = sorted(set(reference) | set(candidate))
    metrics: list[TensorMetric] = []
    for name in names:
        metrics.append(
            compare_optional_tensors(
                name,
                reference.get(name),
                candidate.get(name),
                profile,
            )
        )
    return metrics


def flatten_state(
    prefix: str,
    state: Sequence[torch.Tensor | None],
) -> OptionalTensorMap:
    return {f"{prefix}/layer_{index}": value for index, value in enumerate(state)}


def flatten_trajectory(
    snapshots: Sequence[B1SweepSnapshot],
) -> OptionalTensorMap:
    flattened: OptionalTensorMap = {}
    seen: set[tuple[str, int]] = set()
    for snapshot in snapshots:
        key = (snapshot.phase, snapshot.sweep_index)
        if key in seen:
            raise ValueError(f"Duplicate trajectory snapshot: {key}")
        seen.add(key)
        prefix = f"trajectory/{snapshot.phase}/sweep_{snapshot.sweep_index}"
        flattened.update(flatten_state(f"{prefix}/beliefs", snapshot.beliefs))
        flattened.update(
            flatten_state(
                f"{prefix}/prediction_errors",
                snapshot.prediction_errors,
            )
        )
        flattened.update(
            flatten_state(
                f"{prefix}/state_corrections",
                snapshot.state_corrections,
            )
        )
    return flattened


def collect_named_gradients(model: nn.Module) -> dict[str, torch.Tensor]:
    gradients: dict[str, torch.Tensor] = {}
    for name, parameter in model.named_parameters():
        if parameter.grad is None:
            raise RuntimeError(f"Missing gradient for parameter: {name}")
        gradients[name] = parameter.grad.detach().clone()
    return gradients


def collect_named_parameters(model: nn.Module) -> dict[str, torch.Tensor]:
    return {
        name: parameter.detach().clone()
        for name, parameter in model.named_parameters()
    }


def apply_registered_sgd_step(model: nn.Module) -> OptimizerSnapshot:
    optimizer = torch.optim.SGD(
        model.parameters(),
        lr=0.001,
        momentum=0.0,
    )
    optimizer.step()
    return snapshot_optimizer(optimizer, model)


def snapshot_optimizer(
    optimizer: torch.optim.Optimizer,
    model: nn.Module,
) -> OptimizerSnapshot:
    name_by_parameter = {parameter: name for name, parameter in model.named_parameters()}
    tensor_state: dict[str, torch.Tensor] = {}
    scalar_state: dict[str, JsonScalar] = {}

    for group_index, group in enumerate(optimizer.param_groups):
        for key, value in sorted(group.items()):
            if key == "params":
                continue
            scalar_state[f"param_group/{group_index}/{key}"] = _json_scalar(value)

    for parameter, state in optimizer.state.items():
        parameter_name = name_by_parameter.get(parameter)
        if parameter_name is None:
            raise RuntimeError("Optimizer contains an unknown parameter")
        for key, value in sorted(state.items()):
            component = f"state/{parameter_name}/{key}"
            if torch.is_tensor(value):
                tensor_state[component] = value.detach().clone()
            else:
                scalar_state[component] = _json_scalar(value)

    return OptimizerSnapshot(
        tensor_state=tensor_state,
        scalar_state=scalar_state,
    )


def scalar_map_metrics(
    prefix: str,
    reference: Mapping[str, JsonScalar],
    candidate: Mapping[str, JsonScalar],
) -> list[ScalarMetric]:
    names = sorted(set(reference) | set(candidate))
    return [
        ScalarMetric(
            component=f"{prefix}/{name}",
            passed=(reference.get(name) == candidate.get(name)),
            reference=reference.get(name),
            candidate=candidate.get(name),
        )
        for name in names
    ]


def gate_from_tensor_metrics(
    gate_id: str,
    metrics: Sequence[TensorMetric],
) -> GateOutcome:
    reasons = tuple(metric.component for metric in metrics if not metric.passed)
    return GateOutcome(gate_id=gate_id, passed=not reasons, reasons=reasons)


def gate_from_scalar_metrics(
    gate_id: str,
    metrics: Sequence[ScalarMetric],
) -> GateOutcome:
    reasons = tuple(metric.component for metric in metrics if not metric.passed)
    return GateOutcome(gate_id=gate_id, passed=not reasons, reasons=reasons)


def write_csv_rows(
    path: Path,
    rows: Iterable[Mapping[str, JsonScalar]],
) -> None:
    materialized = list(rows)
    if not materialized:
        raise ValueError(f"Refusing to write empty CSV: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(materialized[0])
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(materialized)


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _json_scalar(value: Any) -> JsonScalar:
    if value is None or isinstance(value, bool | float | int | str):
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("Non-finite optimizer scalar")
        return value
    raise TypeError(f"Unsupported optimizer scalar type: {type(value).__name__}")
