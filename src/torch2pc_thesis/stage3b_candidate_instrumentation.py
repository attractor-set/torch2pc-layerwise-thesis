"""Native profiling adapter for Stage 3B B1/B2 candidate callables.

The B0 baseline is instrumented by temporarily wrapping the upstream Torch2PC
namespace. B1 and B2 are repository-owned implementations, so they expose
explicit profiling boundaries instead. This observer records the same five
preregistered regions without changing the no-hooks reference arm.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Final, Literal, cast

import torch
from torch import Tensor

from torch2pc_thesis.pcinfer_instrumentation import (
    PCInferInstrumentationSummary,
)
from torch2pc_thesis.profiling import Stage3ProfilingError
from torch2pc_thesis.stage3b_profiling import (
    ProfilingCounters,
    Stage3BProfiler,
)

type NativeCandidateId = Literal["isolated_layer_vjp", "composite_vjp"]
type NativeMethod = Literal["fixedpred", "strict"]

NATIVE_CANDIDATE_IDS: Final[frozenset[str]] = frozenset(
    {"isolated_layer_vjp", "composite_vjp"}
)


class NativeCandidateInstrumentation:
    """Collect native B1/B2 region measurements and structural counters."""

    def __init__(
        self,
        *,
        candidate_id: NativeCandidateId,
        method: NativeMethod,
        configured_inference_steps: int,
        profiler: Stage3BProfiler,
        repetition: int = 0,
        step: int = 0,
        measured: bool = True,
    ) -> None:
        if candidate_id not in NATIVE_CANDIDATE_IDS:
            raise Stage3ProfilingError(
                f"unsupported native candidate instrumentation: {candidate_id}"
            )
        if method not in {"fixedpred", "strict"}:
            raise Stage3ProfilingError(
                f"unsupported native candidate method: {method}"
            )
        if configured_inference_steps < 1:
            raise Stage3ProfilingError(
                "configured_inference_steps must be positive"
            )
        if profiler.candidate_id != candidate_id:
            raise Stage3ProfilingError(
                "native profiler candidate_id differs from instrumentation"
            )
        if profiler.method != method:
            raise Stage3ProfilingError(
                "native profiler method differs from instrumentation"
            )
        self.candidate_id = candidate_id
        self.method = method
        self.configured_inference_steps = configured_inference_steps
        self.profiler = profiler
        self.repetition = repetition
        self.step = step
        self.measured = measured
        self.initial_forward_autograd_calls = 0
        self.state_autograd_calls = 0
        self.local_state_vjp_calls = 0
        self.parameter_vjp_calls = 0
        self.actual_inference_steps: int | None = None
        self._state_region_active = False
        self._sweep_local_calls: Counter[int] = Counter()

    @contextmanager
    def _region(self, region: str) -> Iterator[ProfilingCounters]:
        def pack(tensor: Tensor) -> Tensor:
            counters.saved_tensor_bytes += tensor.numel() * tensor.element_size()
            return tensor

        def unpack(tensor: Tensor) -> Tensor:
            return tensor

        with (
            self.profiler.region(
                region,
                repetition=self.repetition,
                step=self.step,
                measured=self.measured,
            ) as counters,
            torch.autograd.graph.saved_tensors_hooks(pack, unpack),
        ):
            yield counters

    @contextmanager
    def initial_forward(self) -> Iterator[None]:
        with self._region("initial_forward") as counters:
            yield
            counters.vjp_calls = 1
        self.initial_forward_autograd_calls += 1

    @contextmanager
    def state_inference(self, *, model_depth: int) -> Iterator[None]:
        if self._state_region_active:
            raise Stage3ProfilingError(
                "native state-inference instrumentation cannot be nested"
            )
        self._state_region_active = True
        try:
            with self._region("state_inference") as counters:
                yield
                self._finish_state(model_depth=model_depth)
                counters.vjp_calls = self.state_autograd_calls
                counters.actual_inference_steps = self.configured_inference_steps
        finally:
            self._state_region_active = False

    @contextmanager
    def local_state_vjp(
        self,
        *,
        sweep_index: int,
    ) -> Iterator[None]:
        if not self._state_region_active:
            raise Stage3ProfilingError(
                "native local-state VJP was observed outside state inference"
            )
        if sweep_index < 0 or sweep_index >= self.configured_inference_steps:
            raise Stage3ProfilingError(
                "native local-state VJP has an invalid sweep index: "
                f"{sweep_index}"
            )
        with self._region("local_state_vjp") as counters:
            counters.vjp_calls = 1
            yield
        self.local_state_vjp_calls += 1
        self.state_autograd_calls += 1
        self._sweep_local_calls[sweep_index] += 1

    def record_state_autograd_call(self) -> None:
        if not self._state_region_active:
            raise Stage3ProfilingError(
                "native state autograd call was observed outside state inference"
            )
        self.state_autograd_calls += 1

    @contextmanager
    def parameter_vjp(self) -> Iterator[None]:
        with self._region("parameter_vjp") as counters:
            counters.vjp_calls = 1
            yield
        self.parameter_vjp_calls += 1

    def _finish_state(self, *, model_depth: int) -> None:
        if model_depth < 2:
            raise Stage3ProfilingError(
                "native candidate instrumentation requires model depth >= 2"
            )
        expected_sweeps = set(range(self.configured_inference_steps))
        observed_sweeps = set(self._sweep_local_calls)
        if observed_sweeps != expected_sweeps:
            raise Stage3ProfilingError(
                "native candidate did not expose every configured inference sweep: "
                f"expected={sorted(expected_sweeps)}, "
                f"observed={sorted(observed_sweeps)}"
            )
        if self.candidate_id == "isolated_layer_vjp":
            calls_per_sweep = (
                model_depth if self.method == "fixedpred" else model_depth - 1
            )
        else:
            calls_per_sweep = 1
        invalid = {
            sweep: count
            for sweep, count in sorted(self._sweep_local_calls.items())
            if count != calls_per_sweep
        }
        if invalid:
            raise Stage3ProfilingError(
                "native candidate local-state VJP count differs from its structural "
                f"contract: expected_per_sweep={calls_per_sweep}, observed={invalid}"
            )
        expected_state_calls = self.local_state_vjp_calls
        if self.method == "strict":
            expected_state_calls += self.configured_inference_steps
        if self.state_autograd_calls != expected_state_calls:
            raise Stage3ProfilingError(
                "native candidate state autograd count differs from its structural "
                f"contract: expected={expected_state_calls}, "
                f"observed={self.state_autograd_calls}"
            )
        self.actual_inference_steps = len(observed_sweeps)

    def summary(self) -> PCInferInstrumentationSummary:
        if self.actual_inference_steps is None:
            raise Stage3ProfilingError(
                "native candidate inference-step count was not observed"
            )
        if self.initial_forward_autograd_calls != 1:
            raise Stage3ProfilingError(
                "native candidate initial-forward boundary count is incomplete"
            )
        if self.parameter_vjp_calls != 1:
            raise Stage3ProfilingError(
                "native candidate parameter-VJP boundary count is incomplete"
            )
        return PCInferInstrumentationSummary(
            actual_inference_steps=self.actual_inference_steps,
            initial_forward_autograd_calls=self.initial_forward_autograd_calls,
            state_autograd_calls=self.state_autograd_calls,
            local_state_vjp_calls=self.local_state_vjp_calls,
            parameter_vjp_calls=self.parameter_vjp_calls,
        )


def native_candidate_id(pc_infer: object) -> NativeCandidateId | None:
    """Return the explicit native candidate marker attached by B1/B2 loaders."""

    value = getattr(pc_infer, "__stage3b_candidate_id__", None)
    if value not in NATIVE_CANDIDATE_IDS:
        return None
    return cast(NativeCandidateId, value)
