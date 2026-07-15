from __future__ import annotations

import copy
import random
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, cast

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

from torch2pc_thesis.stage3b_a1_controls import (
    EquivalenceThresholds,
    TensorComparison,
    compare_tensor,
    compare_tensor_maps,
)
from torch2pc_thesis.stage3b_a1_observer import (
    OBSERVER_SCHEMA_ID,
    ObserverPayload,
    ObserverValidation,
    PassiveLayerObserver,
)
from torch2pc_thesis.stage3b_a1_shortcut import (
    JointVjpDiagnostics,
    reduced_shortcut_backward,
)

OptimizerFactory = Callable[[Iterable[nn.Parameter]], torch.optim.Optimizer]
JsonScalar = bool | int | float | str | None


class ObserverArm(StrEnum):
    """Preregistered computational paths covered by OBS-NI0."""

    FIXEDPRED = "fixedpred"
    JOINT_VJP = "joint_vjp"


@dataclass(frozen=True)
class RngSnapshot:
    """Exact Python, NumPy, CPU and ROCm RNG state snapshot."""

    python_state: object
    numpy_state: tuple[Any, ...]
    torch_cpu_state: torch.Tensor
    torch_device_states: tuple[torch.Tensor, ...]


@dataclass(frozen=True)
class _PathArtifacts:
    gradients: Mapping[str, torch.Tensor]
    parameters: Mapping[str, torch.Tensor]
    optimizer_tensors: Mapping[str, torch.Tensor]
    optimizer_scalars: Mapping[str, JsonScalar]
    buffers: Mapping[str, torch.Tensor]
    inputs_after: torch.Tensor
    targets_after: torch.Tensor
    post_rng: RngSnapshot
    observer_validation: ObserverValidation | None
    observer_payload: tuple[ObserverPayload, ...]
    shortcut_diagnostics: JointVjpDiagnostics | None


@dataclass(frozen=True)
class ObsNi0ArmResult:
    """One observer-disabled versus observer-enabled paired comparison."""

    control_id: str
    arm: ObserverArm
    seed: int
    inference_steps: int
    eta: float | None
    gradient_records: tuple[TensorComparison, ...]
    parameter_records: tuple[TensorComparison, ...]
    optimizer_tensor_records: tuple[TensorComparison, ...]
    buffer_records: tuple[TensorComparison, ...]
    input_record: TensorComparison
    target_record: TensorComparison
    optimizer_scalar_state_equal: bool
    python_rng_equal: bool
    numpy_rng_equal: bool
    torch_cpu_rng_equal: bool
    torch_device_rng_equal: bool
    observer_validation: ObserverValidation
    shortcut_diagnostics: JointVjpDiagnostics | None
    observer_payload: tuple[ObserverPayload, ...]

    @property
    def gradient_passed(self) -> bool:
        return bool(self.gradient_records) and all(
            item.passed for item in self.gradient_records
        )

    @property
    def parameter_step_passed(self) -> bool:
        return bool(self.parameter_records) and all(
            item.passed for item in self.parameter_records
        )

    @property
    def optimizer_state_passed(self) -> bool:
        return (
            all(item.passed for item in self.optimizer_tensor_records)
            and self.optimizer_scalar_state_equal
        )

    @property
    def buffers_passed(self) -> bool:
        return all(item.passed for item in self.buffer_records)

    @property
    def inputs_passed(self) -> bool:
        return self.input_record.passed and self.target_record.passed

    @property
    def rng_passed(self) -> bool:
        return (
            self.python_rng_equal
            and self.numpy_rng_equal
            and self.torch_cpu_rng_equal
            and self.torch_device_rng_equal
        )

    @property
    def structural_contract_passed(self) -> bool:
        if self.arm is ObserverArm.FIXEDPRED:
            return self.inference_steps > 0
        diagnostics = self.shortcut_diagnostics
        return bool(
            diagnostics is not None
            and diagnostics.one_call_per_layer
            and diagnostics.top_level_layers == self.inference_steps
        )

    @property
    def passed(self) -> bool:
        return (
            self.gradient_passed
            and self.parameter_step_passed
            and self.optimizer_state_passed
            and self.buffers_passed
            and self.inputs_passed
            and self.rng_passed
            and self.observer_validation.passed
            and self.structural_contract_passed
        )

    def endpoint_records_frame(self) -> pd.DataFrame:
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
        frame = pd.DataFrame.from_records(records)
        frame.insert(0, "arm", self.arm.value)
        return frame

    def state_records_frame(self) -> pd.DataFrame:
        records: list[dict[str, Any]] = []
        records.extend(
            item.to_record(comparison_kind="model_buffer")
            for item in self.buffer_records
        )
        records.append(self.input_record.to_record(comparison_kind="input_after_execution"))
        records.append(
            self.target_record.to_record(comparison_kind="target_after_execution")
        )
        exact_states = {
            "optimizer_scalar_state": self.optimizer_scalar_state_equal,
            "python_rng": self.python_rng_equal,
            "numpy_rng": self.numpy_rng_equal,
            "torch_cpu_rng": self.torch_cpu_rng_equal,
            "torch_device_rng": self.torch_device_rng_equal,
            "observer_payload": self.observer_validation.passed,
            "structural_contract": self.structural_contract_passed,
        }
        records.extend(
            {
                "comparison_kind": "exact_state",
                "component": component,
                "finite": True,
                "passed": passed,
            }
            for component, passed in exact_states.items()
        )
        frame = pd.DataFrame.from_records(records)
        frame.insert(0, "arm", self.arm.value)
        return frame

    def payload_records_frame(self) -> pd.DataFrame:
        frame = pd.DataFrame.from_records(
            record.to_record() for record in self.observer_payload
        )
        frame.insert(0, "arm", self.arm.value)
        return frame

    def to_summary_dict(self) -> dict[str, Any]:
        shortcut = (
            self.shortcut_diagnostics.to_dict()
            if self.shortcut_diagnostics is not None
            else None
        )
        return {
            "control_id": self.control_id,
            "arm": self.arm.value,
            "seed": self.seed,
            "inference_steps": self.inference_steps,
            "eta": self.eta,
            "reference_observer_mode": "no_hooks",
            "candidate_observer_mode": "passive_first_forward_io",
            "observer_schema_id": OBSERVER_SCHEMA_ID,
            "gradient_passed": self.gradient_passed,
            "parameter_step_passed": self.parameter_step_passed,
            "optimizer_state_passed": self.optimizer_state_passed,
            "optimizer_scalar_state_equal": self.optimizer_scalar_state_equal,
            "buffers_passed": self.buffers_passed,
            "inputs_passed": self.inputs_passed,
            "python_rng_equal": self.python_rng_equal,
            "numpy_rng_equal": self.numpy_rng_equal,
            "torch_cpu_rng_equal": self.torch_cpu_rng_equal,
            "torch_device_rng_equal": self.torch_device_rng_equal,
            "rng_passed": self.rng_passed,
            "observer_validation": self.observer_validation.to_dict(),
            "shortcut_diagnostics": shortcut,
            "structural_contract_passed": self.structural_contract_passed,
            "passed": self.passed,
            "gradient_components": len(self.gradient_records),
            "parameter_components": len(self.parameter_records),
            "optimizer_tensor_components": len(self.optimizer_tensor_records),
            "buffer_components": len(self.buffer_records),
            "observer_payload_components": len(self.observer_payload),
        }


@dataclass(frozen=True)
class ObsNi0Result:
    """Complete two-arm passive-observer non-interference result."""

    control_id: str
    seed: int
    arms: tuple[ObsNi0ArmResult, ...]

    @property
    def passed(self) -> bool:
        return len(self.arms) == len(tuple(ObserverArm)) and all(
            arm.passed for arm in self.arms
        )

    def endpoint_records_frame(self) -> pd.DataFrame:
        return pd.concat(
            [arm.endpoint_records_frame() for arm in self.arms],
            ignore_index=True,
        )

    def state_records_frame(self) -> pd.DataFrame:
        return pd.concat(
            [arm.state_records_frame() for arm in self.arms],
            ignore_index=True,
        )

    def payload_records_frame(self) -> pd.DataFrame:
        return pd.concat(
            [arm.payload_records_frame() for arm in self.arms],
            ignore_index=True,
        )

    def to_summary_dicts(self) -> list[dict[str, Any]]:
        return [arm.to_summary_dict() for arm in self.arms]


def evaluate_obs_ni0(
    model: nn.Sequential,
    inputs: torch.Tensor,
    targets: torch.Tensor,
    *,
    torch2pc_dir: str | Path,
    seed: int,
    thresholds: EquivalenceThresholds,
    optimizer_factory: OptimizerFactory,
) -> ObsNi0Result:
    """Evaluate passive-observer non-interference for both registered arms."""
    if not isinstance(model, nn.Sequential):
        raise TypeError("OBS-NI0 requires a top-level nn.Sequential model")
    if len(model) < 1:
        raise ValueError("OBS-NI0 requires at least one top-level layer")

    arms = tuple(
        _evaluate_arm(
            model,
            inputs,
            targets,
            arm=arm,
            torch2pc_dir=torch2pc_dir,
            seed=seed,
            thresholds=thresholds,
            optimizer_factory=optimizer_factory,
        )
        for arm in ObserverArm
    )
    return ObsNi0Result(control_id="OBS-NI0", seed=seed, arms=arms)


def _evaluate_arm(
    model: nn.Sequential,
    inputs: torch.Tensor,
    targets: torch.Tensor,
    *,
    arm: ObserverArm,
    torch2pc_dir: str | Path,
    seed: int,
    thresholds: EquivalenceThresholds,
    optimizer_factory: OptimizerFactory,
) -> ObsNi0ArmResult:
    from torch2pc_thesis.reproducibility import set_global_seed

    set_global_seed(seed, warn_only=False)
    reference_model = copy.deepcopy(model)
    candidate_model = copy.deepcopy(model)
    reference_inputs = inputs.detach().clone()
    candidate_inputs = inputs.detach().clone()
    reference_targets = targets.detach().clone()
    candidate_targets = targets.detach().clone()
    paired_rng = capture_rng_snapshot()

    restore_rng_snapshot(paired_rng)
    reference = _execute_path(
        reference_model,
        reference_inputs,
        reference_targets,
        arm=arm,
        torch2pc_dir=torch2pc_dir,
        optimizer_factory=optimizer_factory,
        observer_enabled=False,
    )

    restore_rng_snapshot(paired_rng)
    candidate = _execute_path(
        candidate_model,
        candidate_inputs,
        candidate_targets,
        arm=arm,
        torch2pc_dir=torch2pc_dir,
        optimizer_factory=optimizer_factory,
        observer_enabled=True,
    )
    validation = candidate.observer_validation
    if validation is None:
        raise RuntimeError("OBS-NI0 candidate path did not produce observer validation")

    inference_steps = len(model)
    return ObsNi0ArmResult(
        control_id="OBS-NI0",
        arm=arm,
        seed=seed,
        inference_steps=inference_steps,
        eta=1.0 if arm is ObserverArm.FIXEDPRED else None,
        gradient_records=compare_tensor_maps(
            reference.gradients,
            candidate.gradients,
            thresholds,
            prefix="gradient:",
        ),
        parameter_records=compare_tensor_maps(
            reference.parameters,
            candidate.parameters,
            thresholds,
            prefix="parameter:",
        ),
        optimizer_tensor_records=compare_tensor_maps(
            reference.optimizer_tensors,
            candidate.optimizer_tensors,
            thresholds,
            prefix="optimizer:",
        ),
        buffer_records=_compare_buffers(
            reference.buffers,
            candidate.buffers,
            thresholds,
        ),
        input_record=_compare_exact_tensor(
            "input",
            reference.inputs_after,
            candidate.inputs_after,
            thresholds,
        ),
        target_record=_compare_exact_tensor(
            "target",
            reference.targets_after,
            candidate.targets_after,
            thresholds,
        ),
        optimizer_scalar_state_equal=(
            reference.optimizer_scalars == candidate.optimizer_scalars
        ),
        python_rng_equal=(
            reference.post_rng.python_state == candidate.post_rng.python_state
        ),
        numpy_rng_equal=_numpy_rng_equal(reference.post_rng, candidate.post_rng),
        torch_cpu_rng_equal=torch.equal(
            reference.post_rng.torch_cpu_state,
            candidate.post_rng.torch_cpu_state,
        ),
        torch_device_rng_equal=_device_rng_equal(
            reference.post_rng,
            candidate.post_rng,
        ),
        observer_validation=validation,
        shortcut_diagnostics=candidate.shortcut_diagnostics,
        observer_payload=candidate.observer_payload,
    )


def _execute_path(
    model: nn.Sequential,
    inputs: torch.Tensor,
    targets: torch.Tensor,
    *,
    arm: ObserverArm,
    torch2pc_dir: str | Path,
    optimizer_factory: OptimizerFactory,
    observer_enabled: bool,
) -> _PathArtifacts:
    observer: PassiveLayerObserver | None = None
    setup_rng_unchanged = True
    if observer_enabled:
        before_setup = capture_rng_snapshot()
        observer = PassiveLayerObserver(model)
        observer.start()
        setup_rng_unchanged = rng_snapshots_equal(
            before_setup,
            capture_rng_snapshot(),
        )

    try:
        if arm is ObserverArm.FIXEDPRED:
            _run_fixedpred_backward(model, inputs, targets, torch2pc_dir)
            diagnostics = None
        else:
            _, diagnostics = reduced_shortcut_backward(
                model,
                nn.CrossEntropyLoss(),
                inputs,
                targets,
            )

        gradients = _named_gradients(model)
        optimizer = optimizer_factory(model.parameters())
        optimizer.step()
        parameters = _named_parameters(model)
        optimizer_tensors, optimizer_scalars = _flatten_optimizer_state(optimizer)
        buffers = _named_buffers(model)
    finally:
        if observer is not None:
            observer.close()

    post_rng = capture_rng_snapshot()
    validation = (
        observer.validate(setup_rng_unchanged=setup_rng_unchanged)
        if observer is not None
        else None
    )
    payload = observer.records if observer is not None else ()

    return _PathArtifacts(
        gradients=gradients,
        parameters=parameters,
        optimizer_tensors=optimizer_tensors,
        optimizer_scalars=optimizer_scalars,
        buffers=buffers,
        inputs_after=inputs.detach().clone(),
        targets_after=targets.detach().clone(),
        post_rng=post_rng,
        observer_validation=validation,
        observer_payload=payload,
        shortcut_diagnostics=diagnostics,
    )


def _run_fixedpred_backward(
    model: nn.Sequential,
    inputs: torch.Tensor,
    targets: torch.Tensor,
    torch2pc_dir: str | Path,
) -> None:
    from torch2pc_thesis.pc_methods import backward_for_method

    model.zero_grad(set_to_none=True)
    backward_for_method(
        model,
        nn.CrossEntropyLoss(),
        inputs,
        targets,
        method="fixedpred",
        torch2pc_dir=torch2pc_dir,
        eta=1.0,
        inference_steps=len(model),
    )


def capture_rng_snapshot() -> RngSnapshot:
    numpy_state = cast(tuple[Any, ...], np.random.get_state())
    copied_numpy_state: tuple[Any, ...] = (
        numpy_state[0],
        numpy_state[1].copy(),
        numpy_state[2],
        numpy_state[3],
        numpy_state[4],
    )
    device_states = (
        tuple(state.clone() for state in torch.cuda.get_rng_state_all())
        if torch.cuda.is_available()
        else ()
    )
    return RngSnapshot(
        python_state=copy.deepcopy(random.getstate()),
        numpy_state=copied_numpy_state,
        torch_cpu_state=torch.random.get_rng_state().clone(),
        torch_device_states=device_states,
    )


def restore_rng_snapshot(snapshot: RngSnapshot) -> None:
    random.setstate(cast(tuple[Any, ...], copy.deepcopy(snapshot.python_state)))
    np.random.set_state(snapshot.numpy_state)
    torch.random.set_rng_state(snapshot.torch_cpu_state)
    if snapshot.torch_device_states:
        torch.cuda.set_rng_state_all(list(snapshot.torch_device_states))


def rng_snapshots_equal(reference: RngSnapshot, candidate: RngSnapshot) -> bool:
    return (
        reference.python_state == candidate.python_state
        and _numpy_rng_equal(reference, candidate)
        and torch.equal(reference.torch_cpu_state, candidate.torch_cpu_state)
        and _device_rng_equal(reference, candidate)
    )


def _numpy_rng_equal(reference: RngSnapshot, candidate: RngSnapshot) -> bool:
    left = reference.numpy_state
    right = candidate.numpy_state
    return bool(
        left[0] == right[0]
        and np.array_equal(left[1], right[1])
        and left[2:] == right[2:]
    )


def _device_rng_equal(reference: RngSnapshot, candidate: RngSnapshot) -> bool:
    return len(reference.torch_device_states) == len(candidate.torch_device_states) and all(
        torch.equal(left, right)
        for left, right in zip(
            reference.torch_device_states,
            candidate.torch_device_states,
            strict=True,
        )
    )


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


def _named_buffers(model: nn.Module) -> dict[str, torch.Tensor]:
    return {
        name: buffer.detach().clone() for name, buffer in model.named_buffers()
    }


def _compare_buffers(
    reference: Mapping[str, torch.Tensor],
    candidate: Mapping[str, torch.Tensor],
    thresholds: EquivalenceThresholds,
) -> tuple[TensorComparison, ...]:
    if set(reference) != set(candidate):
        raise ValueError("OBS-NI0 model-buffer key sets differ")
    records: list[TensorComparison] = []
    for name in sorted(reference):
        left = reference[name]
        right = candidate[name]
        if torch.is_floating_point(left) or torch.is_complex(left):
            records.append(compare_tensor(f"buffer:{name}", left, right, thresholds))
        else:
            records.append(
                _compare_exact_tensor(f"buffer:{name}", left, right, thresholds)
            )
    return tuple(records)


def _compare_exact_tensor(
    component: str,
    reference: torch.Tensor,
    candidate: torch.Tensor,
    thresholds: EquivalenceThresholds,
) -> TensorComparison:
    exact = EquivalenceThresholds(
        min_cosine=-1.0,
        max_relative_l2=0.0,
        zero_atol=thresholds.zero_atol,
        max_abs=0.0,
    )
    return compare_tensor(component, reference, candidate, exact)


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
        if isinstance(value, Sequence) and not isinstance(
            value,
            str | bytes | bytearray,
        ):
            for index, item in enumerate(value):
                visit(item, f"{path}[{index}]")
            return
        if value is None or isinstance(value, bool | int | float | str):
            scalars[path] = value
            return
        scalars[path] = repr(value)

    visit(optimizer.state_dict(), "optimizer")
    return tensors, scalars
