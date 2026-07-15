from __future__ import annotations

import copy
import math
import re
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

import pandas as pd
import torch
import torch.nn as nn

OptimizerFactory = Callable[[Iterable[nn.Parameter]], torch.optim.Optimizer]
JsonScalar = bool | int | float | str | None


def validate_execution_lane(
    *,
    device: str,
    controlled_container: bool,
    lane: str | None,
    source_git_commit: str | None,
    hip_version: str | None,
    cuda_available: bool,
    torch_version: str,
) -> dict[str, JsonScalar]:
    """Validate and describe the execution lane used by EQ-S0."""

    if device not in {"cpu", "gpu"}:
        raise ValueError(f"Unsupported EQ-S0 device: {device}")

    source_commit = source_git_commit or ""
    if controlled_container and not re.fullmatch(r"[0-9a-f]{40}", source_commit):
        raise RuntimeError(
            "Controlled EQ-S0 execution requires a full SOURCE_GIT_COMMIT. "
            "Commit the changes and rebuild the controlled image with `make build`."
        )

    if device == "gpu":
        if not controlled_container or lane != "rocm":
            raise RuntimeError(
                "EQ-S0 GPU execution is valid only in the controlled Docker/ROCm lane. "
                "Run `make stage3b-a1-eq-s0-gpu` from a clean committed tree."
            )
        if hip_version is None:
            raise RuntimeError(
                "The controlled GPU lane requires a ROCm-enabled PyTorch build "
                "with torch.version.hip available."
            )
        if not cuda_available:
            raise RuntimeError(
                "ROCm PyTorch is present, but the GPU is not visible inside the container."
            )
    elif controlled_container and lane != "cpu":
        raise RuntimeError(
            "Controlled EQ-S0 CPU execution requires TORCH2PC_EXECUTION_LANE=cpu."
        )

    return {
        "controlled_container": controlled_container,
        "lane": lane or "host-development",
        "source_git_commit": source_commit or None,
        "torch_version": torch_version,
        "torch_hip_version": hip_version,
        "torch_cuda_available": cuda_available,
    }


class ZeroRelation(StrEnum):
    """Numerical zero relation between a reference and a candidate tensor."""

    BOTH_ZERO = "both_zero"
    REFERENCE_ZERO = "reference_zero"
    CANDIDATE_ZERO = "candidate_zero"
    NONZERO = "nonzero"


class ObserverMode(StrEnum):
    """Preregistered observer modes for the A1/A2 validity controls."""

    NO_HOOKS = "no_hooks"
    INSTRUMENTED_DISABLED = "instrumented_disabled"
    COUNTERS_ONLY = "counters_only"
    TENSOR_SUMMARIES = "tensor_summaries"
    FULL_ATTRIBUTION = "full_attribution"


@dataclass(frozen=True)
class EquivalenceThresholds:
    """Numerical gates for endpoint-gradient and optimizer-step equivalence."""

    min_cosine: float
    max_relative_l2: float
    zero_atol: float = 1e-12
    max_abs: float | None = None

    def __post_init__(self) -> None:
        if not -1.0 <= self.min_cosine <= 1.0:
            raise ValueError("min_cosine must be within [-1, 1]")
        if self.max_relative_l2 < 0:
            raise ValueError("max_relative_l2 must be non-negative")
        if self.zero_atol <= 0:
            raise ValueError("zero_atol must be positive")
        if self.max_abs is not None and self.max_abs < 0:
            raise ValueError("max_abs must be non-negative when provided")


@dataclass(frozen=True)
class TensorComparison:
    """Zero-safe comparison record for one named tensor."""

    component: str
    zero_relation: ZeroRelation
    cosine: float | None
    relative_l2: float | None
    max_abs: float
    reference_norm: float
    candidate_norm: float
    finite: bool
    passed: bool

    def to_record(self, *, comparison_kind: str) -> dict[str, Any]:
        record = asdict(self)
        record["zero_relation"] = self.zero_relation.value
        record["comparison_kind"] = comparison_kind
        return record


@dataclass(frozen=True)
class EqS0Result:
    """Complete direct BP/FixedPred equivalence result for EQ-S0."""

    control_id: str
    seed: int
    inference_steps: int
    eta: float
    observer_mode: ObserverMode
    gradient_records: tuple[TensorComparison, ...]
    parameter_records: tuple[TensorComparison, ...]
    optimizer_tensor_records: tuple[TensorComparison, ...]
    optimizer_scalar_state_equal: bool

    @property
    def gradient_passed(self) -> bool:
        return bool(self.gradient_records) and all(item.passed for item in self.gradient_records)

    @property
    def parameter_step_passed(self) -> bool:
        return bool(self.parameter_records) and all(item.passed for item in self.parameter_records)

    @property
    def optimizer_state_passed(self) -> bool:
        tensor_state_passed = all(item.passed for item in self.optimizer_tensor_records)
        return tensor_state_passed and self.optimizer_scalar_state_equal

    @property
    def passed(self) -> bool:
        return self.gradient_passed and self.parameter_step_passed and self.optimizer_state_passed

    def records_frame(self) -> pd.DataFrame:
        records: list[dict[str, Any]] = []
        records.extend(
            item.to_record(comparison_kind="endpoint_gradient")
            for item in self.gradient_records
        )
        records.extend(
            item.to_record(comparison_kind="parameter_after_optimizer_step")
            for item in self.parameter_records
        )
        records.extend(
            item.to_record(comparison_kind="optimizer_tensor_state")
            for item in self.optimizer_tensor_records
        )
        return pd.DataFrame.from_records(records)

    def to_summary_dict(self) -> dict[str, Any]:
        return {
            "control_id": self.control_id,
            "seed": self.seed,
            "inference_steps": self.inference_steps,
            "eta": self.eta,
            "observer_mode": self.observer_mode.value,
            "gradient_passed": self.gradient_passed,
            "parameter_step_passed": self.parameter_step_passed,
            "optimizer_state_passed": self.optimizer_state_passed,
            "optimizer_scalar_state_equal": self.optimizer_scalar_state_equal,
            "passed": self.passed,
            "gradient_components": len(self.gradient_records),
            "parameter_components": len(self.parameter_records),
            "optimizer_tensor_components": len(self.optimizer_tensor_records),
        }


@dataclass(frozen=True)
class ObserverSnapshot:
    """Semantic outputs used by OBS-NI0 without prescribing hook implementation."""

    mode: ObserverMode
    gradients: Mapping[str, torch.Tensor]
    parameters: Mapping[str, torch.Tensor]
    loss: torch.Tensor | None = None
    errors: Mapping[str, torch.Tensor] | None = None


@dataclass(frozen=True)
class ObserverComparison:
    """Semantic non-interference comparison between two observer modes."""

    reference_mode: ObserverMode
    candidate_mode: ObserverMode
    records: tuple[TensorComparison, ...]

    @property
    def passed(self) -> bool:
        return bool(self.records) and all(item.passed for item in self.records)

    def records_frame(self) -> pd.DataFrame:
        return pd.DataFrame.from_records(
            item.to_record(comparison_kind="observer_semantic_output") for item in self.records
        )


def compare_tensor(
    component: str,
    reference: torch.Tensor,
    candidate: torch.Tensor,
    thresholds: EquivalenceThresholds,
) -> TensorComparison:
    """Compare tensors with an explicit zero-safe contract."""
    if reference.shape != candidate.shape:
        raise ValueError(
            f"Tensor shape mismatch for {component}: {reference.shape} != {candidate.shape}"
        )

    left = reference.detach().reshape(-1).to(device="cpu", dtype=torch.float64)
    right = candidate.detach().reshape(-1).to(device="cpu", dtype=torch.float64)
    finite = bool(torch.isfinite(left).all() and torch.isfinite(right).all())
    if not finite:
        return TensorComparison(
            component=component,
            zero_relation=ZeroRelation.NONZERO,
            cosine=None,
            relative_l2=None,
            max_abs=float("inf"),
            reference_norm=float("nan"),
            candidate_norm=float("nan"),
            finite=False,
            passed=False,
        )

    reference_norm = float(torch.linalg.vector_norm(left))
    candidate_norm = float(torch.linalg.vector_norm(right))
    difference = left - right
    max_abs = float(torch.max(torch.abs(difference))) if difference.numel() else 0.0
    reference_zero = reference_norm <= thresholds.zero_atol
    candidate_zero = candidate_norm <= thresholds.zero_atol

    if reference_zero and candidate_zero:
        absolute_gate = thresholds.max_abs is None or max_abs <= thresholds.max_abs
        return TensorComparison(
            component=component,
            zero_relation=ZeroRelation.BOTH_ZERO,
            cosine=None,
            relative_l2=None,
            max_abs=max_abs,
            reference_norm=reference_norm,
            candidate_norm=candidate_norm,
            finite=True,
            passed=max_abs <= thresholds.zero_atol and absolute_gate,
        )

    if reference_zero or candidate_zero:
        relation = (
            ZeroRelation.REFERENCE_ZERO if reference_zero else ZeroRelation.CANDIDATE_ZERO
        )
        return TensorComparison(
            component=component,
            zero_relation=relation,
            cosine=None,
            relative_l2=None,
            max_abs=max_abs,
            reference_norm=reference_norm,
            candidate_norm=candidate_norm,
            finite=True,
            passed=False,
        )

    cosine_value = float(torch.dot(left, right) / (reference_norm * candidate_norm))
    relative_l2 = float(torch.linalg.vector_norm(difference)) / reference_norm
    absolute_gate = thresholds.max_abs is None or max_abs <= thresholds.max_abs
    passed = (
        math.isfinite(cosine_value)
        and math.isfinite(relative_l2)
        and cosine_value >= thresholds.min_cosine
        and relative_l2 <= thresholds.max_relative_l2
        and absolute_gate
    )
    return TensorComparison(
        component=component,
        zero_relation=ZeroRelation.NONZERO,
        cosine=cosine_value,
        relative_l2=relative_l2,
        max_abs=max_abs,
        reference_norm=reference_norm,
        candidate_norm=candidate_norm,
        finite=True,
        passed=passed,
    )


def compare_tensor_maps(
    reference: Mapping[str, torch.Tensor],
    candidate: Mapping[str, torch.Tensor],
    thresholds: EquivalenceThresholds,
    *,
    prefix: str = "",
) -> tuple[TensorComparison, ...]:
    """Compare two named tensor maps and reject missing or additional components."""
    if set(reference) != set(candidate):
        missing_in_reference = sorted(set(candidate) - set(reference))
        missing_in_candidate = sorted(set(reference) - set(candidate))
        raise ValueError(
            "Tensor-map keys differ: "
            f"missing_in_reference={missing_in_reference}, "
            f"missing_in_candidate={missing_in_candidate}"
        )
    return tuple(
        compare_tensor(f"{prefix}{name}", reference[name], candidate[name], thresholds)
        for name in sorted(reference)
    )


def compare_observer_snapshots(
    reference: ObserverSnapshot,
    candidate: ObserverSnapshot,
    thresholds: EquivalenceThresholds,
) -> ObserverComparison:
    """Compare observer modes without coupling the gate to a hook implementation."""
    records: list[TensorComparison] = []
    records.extend(
        compare_tensor_maps(
            reference.gradients,
            candidate.gradients,
            thresholds,
            prefix="gradient:",
        )
    )
    records.extend(
        compare_tensor_maps(
            reference.parameters,
            candidate.parameters,
            thresholds,
            prefix="parameter:",
        )
    )
    if (reference.loss is None) != (candidate.loss is None):
        raise ValueError("Observer snapshots differ in loss availability")
    if reference.loss is not None and candidate.loss is not None:
        records.append(compare_tensor("loss", reference.loss, candidate.loss, thresholds))
    if (reference.errors is None) != (candidate.errors is None):
        raise ValueError("Observer snapshots differ in error availability")
    if reference.errors is not None and candidate.errors is not None:
        records.extend(
            compare_tensor_maps(
                reference.errors,
                candidate.errors,
                thresholds,
                prefix="error:",
            )
        )
    return ObserverComparison(
        reference_mode=reference.mode,
        candidate_mode=candidate.mode,
        records=tuple(records),
    )


def evaluate_eq_s0(
    model: nn.Module,
    inputs: torch.Tensor,
    targets: torch.Tensor,
    *,
    torch2pc_dir: str | Path,
    seed: int,
    thresholds: EquivalenceThresholds,
    optimizer_factory: OptimizerFactory,
) -> EqS0Result:
    """Evaluate BP against iterative FixedPred with eta=1 and n=len(model)."""
    if not hasattr(model, "__len__"):
        raise TypeError("EQ-S0 requires a model with a registered Torch2PC layer count")
    inference_steps = int(model.__len__())
    if inference_steps < 1:
        raise ValueError("EQ-S0 requires at least one Torch2PC layer")

    _set_global_seed(seed)
    bp_model = copy.deepcopy(model)
    fixedpred_model = copy.deepcopy(model)

    _run_backward(
        bp_model,
        inputs,
        targets,
        method="bp",
        torch2pc_dir=torch2pc_dir,
        eta=None,
        inference_steps=None,
    )
    _run_backward(
        fixedpred_model,
        inputs,
        targets,
        method="fixedpred",
        torch2pc_dir=torch2pc_dir,
        eta=1.0,
        inference_steps=inference_steps,
    )

    gradient_records = compare_tensor_maps(
        _named_gradients(bp_model),
        _named_gradients(fixedpred_model),
        thresholds,
        prefix="gradient:",
    )

    bp_optimizer = optimizer_factory(bp_model.parameters())
    fixedpred_optimizer = optimizer_factory(fixedpred_model.parameters())
    bp_optimizer.step()
    fixedpred_optimizer.step()

    parameter_records = compare_tensor_maps(
        _named_parameters(bp_model),
        _named_parameters(fixedpred_model),
        thresholds,
        prefix="parameter:",
    )

    bp_optimizer_tensors, bp_optimizer_scalars = _flatten_optimizer_state(bp_optimizer)
    fixed_tensors, fixed_scalars = _flatten_optimizer_state(fixedpred_optimizer)
    optimizer_tensor_records = compare_tensor_maps(
        bp_optimizer_tensors,
        fixed_tensors,
        thresholds,
        prefix="optimizer:",
    )

    return EqS0Result(
        control_id="EQ-S0",
        seed=seed,
        inference_steps=inference_steps,
        eta=1.0,
        observer_mode=ObserverMode.NO_HOOKS,
        gradient_records=gradient_records,
        parameter_records=parameter_records,
        optimizer_tensor_records=optimizer_tensor_records,
        optimizer_scalar_state_equal=bp_optimizer_scalars == fixed_scalars,
    )


def _run_backward(
    model: nn.Module,
    inputs: torch.Tensor,
    targets: torch.Tensor,
    *,
    method: str,
    torch2pc_dir: str | Path,
    eta: float | None,
    inference_steps: int | None,
) -> None:
    from torch2pc_thesis.pc_methods import backward_for_method

    model.zero_grad(set_to_none=True)
    backward_for_method(
        model,
        nn.CrossEntropyLoss(),
        inputs,
        targets,
        method=method,
        torch2pc_dir=torch2pc_dir,
        eta=eta,
        inference_steps=inference_steps,
    )


def _set_global_seed(seed: int) -> None:
    from torch2pc_thesis.reproducibility import set_global_seed

    set_global_seed(seed, warn_only=False)


def _named_gradients(model: nn.Module) -> dict[str, torch.Tensor]:
    gradients: dict[str, torch.Tensor] = {}
    missing: list[str] = []
    for name, parameter in model.named_parameters():
        if not parameter.requires_grad:
            continue
        if parameter.grad is None:
            missing.append(name)
            continue
        gradients[name] = parameter.grad.detach().clone()
    if missing:
        raise RuntimeError(f"Missing gradients for trainable parameters: {missing}")
    if not gradients:
        raise RuntimeError("No trainable parameter gradients were produced")
    return gradients


def _named_parameters(model: nn.Module) -> dict[str, torch.Tensor]:
    parameters = {
        name: parameter.detach().clone()
        for name, parameter in model.named_parameters()
        if parameter.requires_grad
    }
    if not parameters:
        raise RuntimeError("No trainable parameters were found")
    return parameters


def _flatten_optimizer_state(
    optimizer: torch.optim.Optimizer,
) -> tuple[dict[str, torch.Tensor], dict[str, JsonScalar]]:
    tensors: dict[str, torch.Tensor] = {}
    scalars: dict[str, JsonScalar] = {}

    def visit(value: object, path: str) -> None:
        if isinstance(value, torch.Tensor):
            tensors[path] = value.detach().clone()
            return
        if isinstance(value, Mapping):
            for key in sorted(value, key=lambda item: str(item)):
                visit(value[key], f"{path}.{key}")
            return
        if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
            for index, item in enumerate(value):
                visit(item, f"{path}[{index}]")
            return
        if value is None or isinstance(value, bool | int | float | str):
            scalars[path] = value
            return
        scalars[path] = repr(value)

    visit(optimizer.state_dict(), "optimizer")
    return tensors, scalars
