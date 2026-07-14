"""Temporary, non-invasive instrumentation for a loaded Torch2PC ``PCInfer``.

The upstream checkout remains unchanged.  The context manager replaces selected
objects only in the function globals used by the loaded ``PCInfer`` callable and
restores every original object before returning.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, MutableMapping
from contextlib import contextmanager
from dataclasses import dataclass
from types import MethodType
from typing import Any, Final, Literal, cast

import torch
from torch import Tensor

from torch2pc_thesis.profiling import Stage3ProfilingError
from torch2pc_thesis.stage3b_profiling import ProfilingCounters, Stage3BProfiler

type PCInferCallable = Callable[..., Any]
type Phase = Literal["idle", "initial_forward", "state_inference", "parameter_vjp"]

_REQUIRED_GLOBALS: Final[frozenset[str]] = frozenset(
    {
        "torch",
        "FwdPassPlus",
        "FixedPredPCPredErrs",
        "StrictPCPredErrs",
        "SetPCGrads",
    }
)


@dataclass(frozen=True)
class PCInferInstrumentationSummary:
    """Observed counters from one instrumented ``PCInfer`` call."""

    actual_inference_steps: int
    initial_forward_autograd_calls: int
    state_autograd_calls: int
    local_state_vjp_calls: int
    parameter_vjp_calls: int

    def to_record(self) -> dict[str, int]:
        return {
            "actual_inference_steps": self.actual_inference_steps,
            "initial_forward_autograd_calls": self.initial_forward_autograd_calls,
            "state_autograd_calls": self.state_autograd_calls,
            "local_state_vjp_calls": self.local_state_vjp_calls,
            "parameter_vjp_calls": self.parameter_vjp_calls,
        }


class _AutogradProxy:
    def __init__(self, original: Any, observer: PCInferInstrumentation) -> None:
        self._original = original
        self._observer = observer

    def __getattr__(self, name: str) -> Any:
        return getattr(self._original, name)

    def grad(self, *args: Any, **kwargs: Any) -> Any:
        return self._observer.call_grad(self._original.grad, *args, **kwargs)


class _TorchProxy:
    def __init__(self, original: Any, observer: PCInferInstrumentation) -> None:
        self._original = original
        self.autograd = _AutogradProxy(original.autograd, observer)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._original, name)


class PCInferInstrumentation:
    """Mutable observer used only while one upstream ``PCInfer`` call executes."""

    def __init__(
        self,
        *,
        profiler: Stage3BProfiler,
        configured_inference_steps: int,
        repetition: int,
        step: int,
        measured: bool,
    ) -> None:
        if configured_inference_steps < 1:
            raise Stage3ProfilingError("configured_inference_steps must be positive")
        self.profiler = profiler
        self.configured_inference_steps = configured_inference_steps
        self.repetition = repetition
        self.step = step
        self.measured = measured
        self.phase: Phase = "idle"
        self.phase_counters: ProfilingCounters | None = None
        self.initial_forward_autograd_calls = 0
        self.state_autograd_calls = 0
        self.local_state_vjp_calls = 0
        self.output_error_calls = 0
        self.parameter_vjp_calls = 0
        self.actual_inference_steps: int | None = None

    @contextmanager
    def activate(
        self,
        phase: Phase,
        counters: ProfilingCounters,
    ) -> Iterator[None]:
        previous_phase = self.phase
        previous_counters = self.phase_counters
        self.phase = phase
        self.phase_counters = counters
        try:
            yield
        finally:
            self.phase = previous_phase
            self.phase_counters = previous_counters

    @contextmanager
    def saved_tensor_accounting(
        self,
        counters: ProfilingCounters,
    ) -> Iterator[None]:
        def pack(tensor: Tensor) -> Tensor:
            counters.saved_tensor_bytes += tensor.numel() * tensor.element_size()
            return tensor

        def unpack(tensor: Tensor) -> Tensor:
            return tensor

        with torch.autograd.graph.saved_tensors_hooks(pack, unpack):
            yield

    def call_grad(
        self,
        original_grad: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        counters = self.phase_counters
        if counters is None or self.phase == "idle":
            return original_grad(*args, **kwargs)

        counters.vjp_calls += 1
        if self.phase == "initial_forward":
            self.initial_forward_autograd_calls += 1
            return original_grad(*args, **kwargs)

        if self.phase == "parameter_vjp":
            self.parameter_vjp_calls += 1
            return original_grad(*args, **kwargs)

        if self.phase != "state_inference":
            raise Stage3ProfilingError(f"unexpected instrumentation phase: {self.phase}")

        self.state_autograd_calls += 1
        grad_outputs = kwargs.get("grad_outputs")
        if grad_outputs is None and len(args) >= 3:
            grad_outputs = args[2]
        if grad_outputs is None:
            self.output_error_calls += 1
            return original_grad(*args, **kwargs)

        self.local_state_vjp_calls += 1
        with self.profiler.region(
            "local_state_vjp",
            repetition=self.repetition,
            step=self.step,
            measured=self.measured,
        ) as local_counters:
            local_counters.vjp_calls = 1
            return original_grad(*args, **kwargs)

    def finish_state(self, *, method: str, model_depth: int, requested_steps: int) -> None:
        if model_depth < 1:
            raise Stage3ProfilingError("Torch2PC model must contain at least one layer")
        normalized = method.lower()
        if normalized == "fixedpred":
            calls_per_step = model_depth
            quotient, remainder = divmod(self.local_state_vjp_calls, calls_per_step)
            if remainder:
                raise Stage3ProfilingError(
                    "FixedPred local-state VJP count is not divisible by model depth"
                )
            observed = quotient
        elif normalized == "strict":
            observed = self.output_error_calls
            expected_local = observed * max(model_depth - 1, 0)
            if self.local_state_vjp_calls != expected_local:
                raise Stage3ProfilingError(
                    "Strict local-state VJP count does not match observed inference steps: "
                    f"expected={expected_local}, actual={self.local_state_vjp_calls}"
                )
        else:
            raise Stage3ProfilingError(f"unsupported instrumented method: {method}")

        if observed != requested_steps or observed != self.configured_inference_steps:
            raise Stage3ProfilingError(
                "actual inference-step count differs from the configured count: "
                f"configured={self.configured_inference_steps}, "
                f"requested={requested_steps}, observed={observed}"
            )
        self.actual_inference_steps = observed
        if self.phase_counters is None:
            raise Stage3ProfilingError("state-inference counters are unavailable")
        self.phase_counters.actual_inference_steps = observed

    def summary(self) -> PCInferInstrumentationSummary:
        if self.actual_inference_steps is None:
            raise Stage3ProfilingError("actual inference-step count was not observed")
        return PCInferInstrumentationSummary(
            actual_inference_steps=self.actual_inference_steps,
            initial_forward_autograd_calls=self.initial_forward_autograd_calls,
            state_autograd_calls=self.state_autograd_calls,
            local_state_vjp_calls=self.local_state_vjp_calls,
            parameter_vjp_calls=self.parameter_vjp_calls,
        )


def _function_globals(pc_infer: PCInferCallable) -> MutableMapping[str, Any] | None:
    namespace = getattr(pc_infer, "__globals__", None)
    if isinstance(namespace, dict):
        return namespace
    if isinstance(pc_infer, MethodType):
        bound_namespace = getattr(pc_infer.__func__, "__globals__", None)
        if isinstance(bound_namespace, dict):
            return bound_namespace
    return None


def supports_pcinfer_instrumentation(pc_infer: PCInferCallable) -> bool:
    """Return whether the callable exposes the known Torch2PC function namespace."""

    namespace = _function_globals(pc_infer)
    return bool(namespace is not None and namespace.keys() >= _REQUIRED_GLOBALS)


def _requested_steps(args: tuple[Any, ...], kwargs: dict[str, Any], index: int) -> int:
    value = kwargs.get("n")
    if value is None and len(args) > index:
        value = args[index]
    if value is None:
        raise Stage3ProfilingError("instrumented Torch2PC call did not expose n")
    steps = int(value)
    if steps < 1:
        raise Stage3ProfilingError("instrumented Torch2PC n must be positive")
    return steps


@contextmanager
def instrument_pcinfer(
    pc_infer: PCInferCallable,
    *,
    profiler: Stage3BProfiler,
    configured_inference_steps: int,
    repetition: int = 0,
    step: int = 0,
    measured: bool = True,
) -> Iterator[PCInferInstrumentation]:
    """Install and restore temporary wrappers around known Torch2PC boundaries."""

    namespace = _function_globals(pc_infer)
    if namespace is None or not namespace.keys() >= _REQUIRED_GLOBALS:
        missing = sorted(
            _REQUIRED_GLOBALS - (set(namespace) if namespace is not None else set())
        )
        raise Stage3ProfilingError(
            f"PCInfer namespace does not support Stage 3B instrumentation: missing={missing}"
        )

    observer = PCInferInstrumentation(
        profiler=profiler,
        configured_inference_steps=configured_inference_steps,
        repetition=repetition,
        step=step,
        measured=measured,
    )
    originals = {name: namespace[name] for name in _REQUIRED_GLOBALS}
    original_forward = cast(Callable[..., Any], originals["FwdPassPlus"])
    original_fixedpred = cast(Callable[..., Any], originals["FixedPredPCPredErrs"])
    original_strict = cast(Callable[..., Any], originals["StrictPCPredErrs"])
    original_parameter_vjp = cast(Callable[..., Any], originals["SetPCGrads"])

    def wrapped_forward(*args: Any, **kwargs: Any) -> Any:
        with (
            profiler.region(
                "initial_forward",
                repetition=repetition,
                step=step,
                measured=measured,
            ) as counters,
            observer.activate("initial_forward", counters),
            observer.saved_tensor_accounting(counters),
        ):
            return original_forward(*args, **kwargs)

    def wrap_state(
        original: Callable[..., Any],
        method: str,
        n_index: int,
    ) -> Callable[..., Any]:
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            if not args:
                raise Stage3ProfilingError("instrumented state inference has no model")
            model = args[0]
            try:
                model_depth = len(model)
            except TypeError as exc:
                raise Stage3ProfilingError(
                    "instrumented Torch2PC model has no layer count"
                ) from exc
            requested_steps = _requested_steps(args, kwargs, n_index)
            with (
                profiler.region(
                    "state_inference",
                    repetition=repetition,
                    step=step,
                    measured=measured,
                ) as counters,
                observer.activate("state_inference", counters),
                observer.saved_tensor_accounting(counters),
            ):
                output = original(*args, **kwargs)
                observer.finish_state(
                    method=method,
                    model_depth=int(model_depth),
                    requested_steps=requested_steps,
                )
                return output

        return wrapped

    def wrapped_parameter_vjp(*args: Any, **kwargs: Any) -> Any:
        with (
            profiler.region(
                "parameter_vjp",
                repetition=repetition,
                step=step,
                measured=measured,
            ) as counters,
            observer.activate("parameter_vjp", counters),
            observer.saved_tensor_accounting(counters),
        ):
            return original_parameter_vjp(*args, **kwargs)

    namespace["torch"] = _TorchProxy(originals["torch"], observer)
    namespace["FwdPassPlus"] = wrapped_forward
    namespace["FixedPredPCPredErrs"] = wrap_state(original_fixedpred, "fixedpred", 4)
    namespace["StrictPCPredErrs"] = wrap_state(original_strict, "strict", 5)
    namespace["SetPCGrads"] = wrapped_parameter_vjp
    try:
        yield observer
    finally:
        for name, value in originals.items():
            namespace[name] = value
