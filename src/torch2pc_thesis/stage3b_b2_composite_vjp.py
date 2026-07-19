from __future__ import annotations

import hashlib
import importlib.util
import subprocess
from collections.abc import Callable, Sequence
from contextlib import nullcontext
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path
from types import ModuleType
from typing import Any, Final, Protocol, cast

import torch
import torch.nn as nn

from torch2pc_thesis.stage3b_b1_isolated_vjp import (
    B1ObserverMode,
    B1SweepSnapshot,
)
from torch2pc_thesis.stage3b_candidate_instrumentation import (
    NativeCandidateInstrumentation,
)

PATCHED_TORCH2PC_COMMIT = "b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4"
PC_INFER_DEFAULT_STEPS: Final[int] = 20

TensorState = list[torch.Tensor | None]
PcInferOutput = tuple[
    TensorState,
    torch.Tensor,
    torch.Tensor,
    TensorState,
    TensorState,
]


class Torch2PCReference(Protocol):
    def FwdPassPlus(
        self,
        model: nn.Sequential,
        loss_fn: nn.Module,
        inputs: torch.Tensor,
        targets: torch.Tensor,
    ) -> tuple[TensorState, torch.Tensor, torch.Tensor]: ...

    def SetPCGrads(
        self,
        model: nn.Sequential,
        epsilon: TensorState,
        inputs: torch.Tensor,
        beliefs: TensorState | None = None,
    ) -> None: ...


@dataclass(frozen=True)
class B2StructuralEvent:
    candidate_id: str
    method: str
    sweep_index: int
    layer_indices: tuple[int, ...]
    logical_edge_count: int
    composite_vjp_call_count: int = 1
    graph_lifetime: str = "single_sweep_composite_vjp_call"

    @property
    def graph_module_set(self) -> tuple[int, ...]:
        return self.layer_indices

    @property
    def graph_span(self) -> int:
        if not self.layer_indices:
            return 0
        return self.layer_indices[-1] - self.layer_indices[0] + 1

    def to_dict(self) -> dict[str, bool | int | str | list[int]]:
        return {
            "candidate_id": self.candidate_id,
            "method": self.method,
            "sweep_index": self.sweep_index,
            "logical_edge_count": self.logical_edge_count,
            "composite_vjp_call_count": self.composite_vjp_call_count,
            "graph_module_set": list(self.graph_module_set),
            "graph_span": self.graph_span,
            "graph_lifetime": self.graph_lifetime,
        }


StructuralEventSink = Callable[[B2StructuralEvent], None]
TrajectorySink = Callable[[B1SweepSnapshot], None]


@dataclass
class B2CounterCollector:
    events: list[B2StructuralEvent] = field(default_factory=list)

    def __call__(self, event: B2StructuralEvent) -> None:
        self.events.append(event)

    @property
    def logical_edge_count(self) -> int:
        return sum(event.logical_edge_count for event in self.events)

    @property
    def composite_vjp_call_count(self) -> int:
        return sum(event.composite_vjp_call_count for event in self.events)

    @property
    def graph_module_sets(self) -> tuple[tuple[int, ...], ...]:
        return tuple(event.graph_module_set for event in self.events)

    @property
    def graph_span(self) -> int:
        return max((event.graph_span for event in self.events), default=0)

    @property
    def graph_lifetimes(self) -> set[str]:
        return {event.graph_lifetime for event in self.events}


def composite_state_vjp(
    layers: Sequence[nn.Module],
    layer_inputs: Sequence[torch.Tensor],
    cotangents: Sequence[torch.Tensor],
    *,
    method: str,
    sweep_index: int,
    layer_indices: Sequence[int],
    observer_mode: B1ObserverMode = B1ObserverMode.NO_HOOKS,
    event_sink: StructuralEventSink | None = None,
    _stage3b_instrumentation: NativeCandidateInstrumentation | None = None,
) -> tuple[torch.Tensor, ...]:
    """Evaluate all registered state-edge VJPs in one autograd call."""
    _validate_observer(observer_mode, event_sink)
    indices = _validate_composite_registration(
        layers,
        layer_inputs,
        cotangents,
        layer_indices,
    )

    local_inputs = tuple(value.detach().requires_grad_(True) for value in layer_inputs)
    outputs: list[torch.Tensor] = []
    for layer, local_input, cotangent, layer_index in zip(
        layers,
        local_inputs,
        cotangents,
        indices,
        strict=True,
    ):
        output = layer(local_input)
        if not isinstance(output, torch.Tensor):
            raise TypeError(
                "B2 requires every registered top-level layer to return one tensor"
            )
        if output.shape != cotangent.shape:
            raise ValueError(
                "B2 cotangent shape mismatch at layer "
                f"{layer_index}: output={tuple(output.shape)}, "
                f"cotangent={tuple(cotangent.shape)}"
            )
        outputs.append(output)

    profiling_context = (
        nullcontext()
        if _stage3b_instrumentation is None
        else _stage3b_instrumentation.local_state_vjp(
            sweep_index=sweep_index,
        )
    )
    with profiling_context:
        gradients = torch.autograd.grad(
            outputs=tuple(outputs),
            inputs=local_inputs,
            grad_outputs=tuple(cotangents),
            create_graph=False,
            retain_graph=False,
            allow_unused=False,
        )
    if len(gradients) != len(indices):
        raise RuntimeError("B2 composite VJP returned an unexpected gradient count")

    detached: list[torch.Tensor] = []
    for gradient, local_input, layer_index in zip(
        gradients,
        local_inputs,
        indices,
        strict=True,
    ):
        if gradient is None:
            raise RuntimeError(f"B2 composite VJP missed layer {layer_index}")
        if gradient.shape != local_input.shape:
            raise RuntimeError(
                "B2 composite VJP gradient shape mismatch at layer "
                f"{layer_index}: gradient={tuple(gradient.shape)}, "
                f"input={tuple(local_input.shape)}"
            )
        detached.append(gradient.detach())

    if observer_mode is B1ObserverMode.COUNTERS_ONLY:
        assert event_sink is not None
        event_sink(
            B2StructuralEvent(
                candidate_id="composite_vjp",
                method=method,
                sweep_index=sweep_index,
                layer_indices=indices,
                logical_edge_count=len(indices),
            )
        )

    return tuple(detached)


def fixedpred_composite_errors(
    model: nn.Sequential,
    vhat: TensorState,
    dldy: torch.Tensor,
    *,
    eta: float = 1.0,
    inference_steps: int | None = None,
    observer_mode: B1ObserverMode = B1ObserverMode.NO_HOOKS,
    event_sink: StructuralEventSink | None = None,
    trajectory_sink: TrajectorySink | None = None,
    _stage3b_instrumentation: NativeCandidateInstrumentation | None = None,
) -> tuple[TensorState, TensorState]:
    """B2 FixedPred inference with one composite state VJP per sweep."""
    _validate_model_and_steps(model, inference_steps)
    _validate_observer(observer_mode, event_sink)
    steps = len(model) if inference_steps is None else inference_steps
    fixed = _require_tensor_state(vhat, expected_length=len(model) + 1)
    beliefs = _clone_required_state(fixed)
    epsilon: TensorState = [None] * (len(model) + 1)
    epsilon[-1] = dldy.detach()
    no_corrections: TensorState = [None] * (len(model) + 1)
    _emit_snapshot(
        method="FixedPred",
        phase="initial",
        sweep_index=-1,
        beliefs=beliefs,
        epsilon=epsilon,
        corrections=no_corrections,
        trajectory_sink=trajectory_sink,
    )

    layer_indices = tuple(range(len(model)))
    layers = tuple(model[index] for index in layer_indices)
    fixed_inputs = tuple(_required(fixed[index]) for index in layer_indices)

    for sweep_index in range(steps):
        corrections: TensorState = [None] * (len(model) + 1)
        for layer_index in layer_indices:
            epsilon[layer_index] = _required(fixed[layer_index]) - _required(
                beliefs[layer_index]
            )

        cotangents = tuple(_required(epsilon[index + 1]) for index in layer_indices)
        propagated = composite_state_vjp(
            layers,
            fixed_inputs,
            cotangents,
            method="FixedPred",
            sweep_index=sweep_index,
            layer_indices=layer_indices,
            observer_mode=observer_mode,
            event_sink=event_sink,
            _stage3b_instrumentation=_stage3b_instrumentation,
        )

        for layer_index in reversed(layer_indices):
            belief = _required(beliefs[layer_index])
            local_error = _required(epsilon[layer_index])
            correction = eta * (local_error - propagated[layer_index])
            corrections[layer_index] = correction.detach()
            beliefs[layer_index] = belief + correction

        _detach_iterative_state(beliefs, epsilon)
        _emit_snapshot(
            method="FixedPred",
            phase="after_sweep",
            sweep_index=sweep_index,
            beliefs=beliefs,
            epsilon=epsilon,
            corrections=corrections,
            trajectory_sink=trajectory_sink,
        )

    return beliefs, epsilon


def strict_composite_errors(
    model: nn.Sequential,
    vinit: TensorState,
    loss_fn: nn.Module,
    targets: torch.Tensor,
    *,
    eta: float,
    inference_steps: int,
    observer_mode: B1ObserverMode = B1ObserverMode.NO_HOOKS,
    event_sink: StructuralEventSink | None = None,
    trajectory_sink: TrajectorySink | None = None,
    _stage3b_instrumentation: NativeCandidateInstrumentation | None = None,
) -> tuple[TensorState, TensorState]:
    """B2 Strict inference with one composite state VJP per sweep."""
    _validate_model_and_steps(model, inference_steps)
    _validate_observer(observer_mode, event_sink)
    initial = _require_tensor_state(vinit, expected_length=len(model) + 1)
    beliefs = _clone_required_state(initial)
    epsilon: TensorState = [None] * (len(model) + 1)
    no_corrections: TensorState = [None] * (len(model) + 1)
    _emit_snapshot(
        method="Strict",
        phase="initial",
        sweep_index=-1,
        beliefs=beliefs,
        epsilon=epsilon,
        corrections=no_corrections,
        trajectory_sink=trajectory_sink,
    )

    layer_indices = tuple(range(1, len(model)))
    layers = tuple(model[index] for index in layer_indices)

    for sweep_index in range(inference_steps):
        corrections: TensorState = [None] * (len(model) + 1)
        penultimate = _required(beliefs[-2])
        output_input = penultimate.detach().requires_grad_(True)
        output = model[-1](output_input)
        if not isinstance(output, torch.Tensor):
            raise TypeError("B2 requires the output layer to return one tensor")
        loss = loss_fn(output, targets)
        if loss.ndim != 0:
            raise ValueError("B2 Strict requires a scalar reduced loss")
        epsilon[-1] = torch.autograd.grad(
            outputs=loss,
            inputs=output,
            create_graph=False,
            retain_graph=False,
            allow_unused=False,
        )[0].detach()
        if _stage3b_instrumentation is not None:
            _stage3b_instrumentation.record_state_autograd_call()

        with torch.no_grad():
            for layer_index in layer_indices:
                lower_prediction = model[layer_index - 1](
                    _required(beliefs[layer_index - 1])
                )
                if not isinstance(lower_prediction, torch.Tensor):
                    raise TypeError(
                        "B2 requires every registered top-level layer to return one "
                        "tensor"
                    )
                epsilon[layer_index] = lower_prediction - _required(
                    beliefs[layer_index]
                )

        state_inputs = tuple(_required(beliefs[index]) for index in layer_indices)
        cotangents = tuple(_required(epsilon[index + 1]) for index in layer_indices)
        propagated = composite_state_vjp(
            layers,
            state_inputs,
            cotangents,
            method="Strict",
            sweep_index=sweep_index,
            layer_indices=layer_indices,
            observer_mode=observer_mode,
            event_sink=event_sink,
            _stage3b_instrumentation=_stage3b_instrumentation,
        )
        propagated_by_layer = dict(zip(layer_indices, propagated, strict=True))

        for layer_index in reversed(layer_indices):
            belief = _required(beliefs[layer_index])
            local_error = _required(epsilon[layer_index])
            correction = eta * (
                local_error - propagated_by_layer[layer_index]
            )
            corrections[layer_index] = correction.detach()
            beliefs[layer_index] = belief + correction

        _detach_iterative_state(beliefs, epsilon)
        _emit_snapshot(
            method="Strict",
            phase="after_sweep",
            sweep_index=sweep_index,
            beliefs=beliefs,
            epsilon=epsilon,
            corrections=corrections,
            trajectory_sink=trajectory_sink,
        )

    return beliefs, epsilon


def pc_infer_b2(
    reference: Torch2PCReference,
    model: nn.Sequential,
    loss_fn: nn.Module,
    inputs: torch.Tensor,
    targets: torch.Tensor,
    method: str,
    *,
    eta: float = 0.1,
    inference_steps: int = 20,
    vinit: TensorState | None = None,
    observer_mode: B1ObserverMode = B1ObserverMode.NO_HOOKS,
    event_sink: StructuralEventSink | None = None,
    trajectory_sink: TrajectorySink | None = None,
    _stage3b_instrumentation: NativeCandidateInstrumentation | None = None,
) -> PcInferOutput:
    """Run opt-in B2 while preserving the patched parameter-VJP path."""
    if not isinstance(model, nn.Sequential):
        raise TypeError("B2 requires a top-level nn.Sequential model")
    if method not in {"FixedPred", "Strict"}:
        raise ValueError("B2 supports only FixedPred and Strict")

    initial_forward_context = (
        nullcontext()
        if _stage3b_instrumentation is None
        else _stage3b_instrumentation.initial_forward()
    )
    with initial_forward_context:
        raw_vhat, loss, dldy = reference.FwdPassPlus(
            model,
            loss_fn,
            inputs,
            targets,
        )
    vhat = _require_tensor_state(raw_vhat, expected_length=len(model) + 1)
    if not torch.is_tensor(loss) or loss.ndim != 0:
        raise RuntimeError("Patched Torch2PC did not return a scalar loss")
    if not torch.is_tensor(dldy):
        raise RuntimeError("Patched Torch2PC did not return an output cotangent")

    state_context = (
        nullcontext()
        if _stage3b_instrumentation is None
        else _stage3b_instrumentation.state_inference(
            model_depth=len(model),
        )
    )
    with state_context:
        if method == "FixedPred":
            beliefs, epsilon = fixedpred_composite_errors(
                model,
                vhat,
                dldy,
                eta=eta,
                inference_steps=inference_steps,
                observer_mode=observer_mode,
                event_sink=event_sink,
                trajectory_sink=trajectory_sink,
                _stage3b_instrumentation=_stage3b_instrumentation,
            )
        else:
            strict_initial = vhat if vinit is None else vinit
            beliefs, epsilon = strict_composite_errors(
                model,
                strict_initial,
                loss_fn,
                targets,
                eta=eta,
                inference_steps=inference_steps,
                observer_mode=observer_mode,
                event_sink=event_sink,
                trajectory_sink=trajectory_sink,
                _stage3b_instrumentation=_stage3b_instrumentation,
            )

    parameter_context = (
        nullcontext()
        if _stage3b_instrumentation is None
        else _stage3b_instrumentation.parameter_vjp()
    )
    with parameter_context:
        if method == "FixedPred":
            reference.SetPCGrads(model, epsilon, inputs, vhat)
        else:
            reference.SetPCGrads(model, epsilon, inputs, beliefs)

    return vhat, loss, dldy, beliefs, epsilon


def _resolve_pc_infer_steps(
    *,
    n: int | None,
    inference_steps: int | None,
) -> int:
    if n is not None and inference_steps is not None and n != inference_steps:
        raise ValueError(
            "conflicting PCInfer step counts: "
            f"n={n}, inference_steps={inference_steps}"
        )
    resolved = PC_INFER_DEFAULT_STEPS
    if n is not None:
        resolved = n
    elif inference_steps is not None:
        resolved = inference_steps
    if isinstance(resolved, bool) or not isinstance(resolved, int) or resolved < 1:
        raise ValueError("PCInfer inference-step count must be a positive integer")
    return resolved


def load_b2_pc_infer(
    torch2pc_dir: str | Path,
    *,
    expected_commit: str = PATCHED_TORCH2PC_COMMIT,
) -> Callable[..., PcInferOutput]:
    """Load the pinned patched reference and return an opt-in B2 callable."""
    reference = load_patched_reference(torch2pc_dir, expected_commit=expected_commit)

    def run(
        model: nn.Sequential,
        loss_fn: nn.Module,
        inputs: torch.Tensor,
        targets: torch.Tensor,
        method: str,
        *,
        eta: float = 0.1,
        n: int | None = None,
        inference_steps: int | None = None,
        vinit: TensorState | None = None,
        observer_mode: B1ObserverMode = B1ObserverMode.NO_HOOKS,
        event_sink: StructuralEventSink | None = None,
        trajectory_sink: TrajectorySink | None = None,
        _stage3b_instrumentation: NativeCandidateInstrumentation | None = None,
    ) -> PcInferOutput:
        resolved_inference_steps = _resolve_pc_infer_steps(
            n=n,
            inference_steps=inference_steps,
        )
        return pc_infer_b2(
            reference,
            model,
            loss_fn,
            inputs,
            targets,
            method,
            eta=eta,
            inference_steps=resolved_inference_steps,
            vinit=vinit,
            observer_mode=observer_mode,
            event_sink=event_sink,
            trajectory_sink=trajectory_sink,
            _stage3b_instrumentation=_stage3b_instrumentation,
        )

    cast(Any, run).__stage3b_candidate_id__ = "composite_vjp"
    return run


def load_patched_reference(
    torch2pc_dir: str | Path,
    *,
    expected_commit: str = PATCHED_TORCH2PC_COMMIT,
) -> Torch2PCReference:
    root = Path(torch2pc_dir).resolve()
    observed_commit = _resolve_git_commit(root)
    if observed_commit != expected_commit:
        raise RuntimeError(
            "B2 requires patched Torch2PC commit "
            f"{expected_commit}, observed {observed_commit}"
        )
    return cast(Torch2PCReference, _load_reference_module(str(root), observed_commit))


@cache
def _load_reference_module(root: str, commit: str) -> ModuleType:
    source = Path(root) / "TorchSeq2PC.py"
    if not source.is_file():
        raise FileNotFoundError(f"Torch2PC checkout is missing: {source}")
    digest = hashlib.sha256(f"{source}:{commit}".encode()).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(
        f"torch2pc_b2_reference_{digest}",
        source,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import patched Torch2PC source: {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name in ("FwdPassPlus", "SetPCGrads"):
        if not callable(getattr(module, name, None)):
            raise RuntimeError(f"Patched Torch2PC source lacks callable {name}")
    return module


def _resolve_git_commit(root: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(f"Unable to resolve Torch2PC commit in {root}: {detail}")
    return completed.stdout.strip()


def _validate_composite_registration(
    layers: Sequence[nn.Module],
    layer_inputs: Sequence[torch.Tensor],
    cotangents: Sequence[torch.Tensor],
    layer_indices: Sequence[int],
) -> tuple[int, ...]:
    counts = {
        len(layers),
        len(layer_inputs),
        len(cotangents),
        len(layer_indices),
    }
    if counts == {0}:
        raise ValueError("B2 composite VJP requires at least one registered edge")
    if len(counts) != 1:
        raise ValueError("B2 composite VJP registration lengths must match")

    indices = tuple(layer_indices)
    if any(not isinstance(index, int) or index < 0 for index in indices):
        raise ValueError("B2 layer indices must be non-negative integers")
    if tuple(sorted(indices)) != indices or len(set(indices)) != len(indices):
        raise ValueError("B2 layer indices must be unique and strictly increasing")
    if any(not isinstance(value, torch.Tensor) for value in layer_inputs):
        raise TypeError("B2 layer inputs must be tensors")
    if any(not isinstance(value, torch.Tensor) for value in cotangents):
        raise TypeError("B2 cotangents must be tensors")
    return indices


def _validate_observer(
    observer_mode: B1ObserverMode,
    event_sink: StructuralEventSink | None,
) -> None:
    if observer_mode is B1ObserverMode.NO_HOOKS and event_sink is not None:
        raise ValueError("no_hooks forbids a structural event sink")
    if observer_mode is B1ObserverMode.COUNTERS_ONLY and event_sink is None:
        raise ValueError("counters_only requires a structural event sink")


def _validate_model_and_steps(
    model: nn.Sequential,
    inference_steps: int | None,
) -> None:
    if not isinstance(model, nn.Sequential):
        raise TypeError("B2 requires a top-level nn.Sequential model")
    if len(model) < 2:
        raise ValueError("B2 requires at least two top-level layers")
    if inference_steps is not None and inference_steps < 1:
        raise ValueError("inference_steps must be positive")


def _require_tensor_state(
    state: Any,
    *,
    expected_length: int,
) -> TensorState:
    if not isinstance(state, list) or len(state) != expected_length:
        raise RuntimeError("Torch2PC state has an unexpected structure")
    tensors: TensorState = []
    for value in state:
        if not torch.is_tensor(value):
            raise RuntimeError("Torch2PC state contains a non-tensor value")
        tensors.append(value)
    return tensors


def _clone_required_state(state: TensorState) -> TensorState:
    return [_required(value).detach().clone() for value in state]


def _required(value: torch.Tensor | None) -> torch.Tensor:
    if value is None:
        raise RuntimeError("B2 encountered a missing tensor state component")
    return value


def _detach_iterative_state(
    beliefs: TensorState,
    epsilon: TensorState,
) -> None:
    for layer_index in range(1, len(beliefs) - 1):
        beliefs[layer_index] = _required(beliefs[layer_index]).detach()
        epsilon[layer_index] = _required(epsilon[layer_index]).detach()


def _emit_snapshot(
    *,
    method: str,
    phase: str,
    sweep_index: int,
    beliefs: TensorState,
    epsilon: TensorState,
    corrections: TensorState,
    trajectory_sink: TrajectorySink | None,
) -> None:
    if trajectory_sink is None:
        return
    trajectory_sink(
        B1SweepSnapshot(
            method=method,
            phase=phase,
            sweep_index=sweep_index,
            beliefs=tuple(_clone_optional(value) for value in beliefs),
            prediction_errors=tuple(_clone_optional(value) for value in epsilon),
            state_corrections=tuple(_clone_optional(value) for value in corrections),
        )
    )


def _clone_optional(value: torch.Tensor | None) -> torch.Tensor | None:
    return None if value is None else value.detach().clone()
