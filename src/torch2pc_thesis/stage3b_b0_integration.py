"""Real Torch2PC B0 integration and non-perturbation gate.

The reference arm remains uninstrumented.  For a compatible loaded Torch2PC
``PCInfer`` callable, the candidate arm installs temporary wrappers around the
five preregistered regions and restores the original namespace after the call.
"""

from __future__ import annotations

import math
import time
from collections import Counter
from collections.abc import Callable, Mapping
from copy import deepcopy
from dataclasses import asdict, dataclass
from typing import Any, Final, Literal, cast

import torch
from torch import Tensor, nn

from torch2pc_thesis.pcinfer_instrumentation import (
    PCInferInstrumentationSummary,
    instrument_pcinfer,
    supports_pcinfer_instrumentation,
)
from torch2pc_thesis.profiling import (
    STAGE3_PROFILE_REGIONS,
    Stage3ProfilingError,
    synchronize_device,
)
from torch2pc_thesis.stage3b_profiling import (
    RegionMeasurement,
    Stage3BProfiler,
    TensorComparison,
    assert_non_perturbing,
    snapshot_named_tensors,
    thresholds_for_device,
)

type PCInferCallable = Callable[..., Any]
type OptimizerFactory = Callable[[nn.Module], torch.optim.Optimizer]
type MethodName = Literal["fixedpred", "strict"]

B0_TORCH2PC_LABELS: Final[dict[MethodName, str]] = {
    "fixedpred": "FixedPred",
    "strict": "Strict",
}
B0_METHODS: Final[frozenset[str]] = frozenset(B0_TORCH2PC_LABELS)
B0_COMPOSITE_LABEL: Final[str] = "stage3::b0_pcinfer_composite_gate"
B0_GATE_SCHEMA_VERSION: Final[int] = 2


@dataclass(frozen=True)
class B0GateConfig:
    """Frozen inputs for one matched instrumented/uninstrumented B0 step."""

    method: MethodName
    torch2pc_method: str
    eta: float
    inference_steps: int
    device: torch.device
    dtype: torch.dtype

    def __post_init__(self) -> None:
        if self.method not in B0_METHODS:
            raise Stage3ProfilingError(f"unsupported B0 method: {self.method}")
        expected_label = B0_TORCH2PC_LABELS[self.method]
        if self.torch2pc_method != expected_label:
            raise Stage3ProfilingError(
                "Torch2PC method label does not match the repository method: "
                f"expected={expected_label}, received={self.torch2pc_method}"
            )
        if not math.isfinite(self.eta) or self.eta <= 0.0:
            raise Stage3ProfilingError("eta must be finite and positive")
        if self.inference_steps < 1:
            raise Stage3ProfilingError("inference_steps must be positive")
        thresholds_for_device(self.device, self.dtype)


@dataclass(frozen=True)
class B0CompositeMeasurement:
    """Composite gate timing, explicitly not internal region attribution."""

    host_time_us: float
    device_time_us: float
    peak_allocated_bytes: int
    peak_reserved_bytes: int
    synchronization_points: int

    def __post_init__(self) -> None:
        if not math.isfinite(self.host_time_us) or self.host_time_us < 0.0:
            raise Stage3ProfilingError("host_time_us must be finite and non-negative")
        if not math.isfinite(self.device_time_us) or self.device_time_us < 0.0:
            raise Stage3ProfilingError("device_time_us must be finite and non-negative")
        for name, value in {
            "peak_allocated_bytes": self.peak_allocated_bytes,
            "peak_reserved_bytes": self.peak_reserved_bytes,
            "synchronization_points": self.synchronization_points,
        }.items():
            if value < 0:
                raise Stage3ProfilingError(f"{name} must be non-negative")

    def to_record(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class B0StepSnapshot:
    """Observable state after one real Torch2PC B0 optimizer step."""

    tensors: Mapping[str, Tensor]
    configured_inference_steps: int
    observed_inference_steps: int | None = None
    region_measurements: tuple[RegionMeasurement, ...] = ()
    instrumentation: PCInferInstrumentationSummary | None = None


@dataclass(frozen=True)
class B0GateReport:
    """Result of the real B0 instrumented/uninstrumented equivalence gate."""

    method: MethodName
    configured_inference_steps: int
    comparisons: tuple[TensorComparison, ...]
    measurement: B0CompositeMeasurement
    observed_inference_steps: int | None = None
    region_measurements: tuple[RegionMeasurement, ...] = ()
    instrumentation: PCInferInstrumentationSummary | None = None

    @property
    def passed(self) -> bool:
        return all(comparison.passed for comparison in self.comparisons)

    @property
    def internal_region_attribution_ready(self) -> bool:
        if self.instrumentation is None:
            return False
        counts = Counter(
            measurement.region for measurement in self.region_measurements
        )
        return bool(
            counts["initial_forward"] == 1
            and counts["state_inference"] == 1
            and counts["local_state_vjp"] >= 1
            and counts["parameter_vjp"] == 1
            and counts["optimizer_step"] == 1
            and set(counts) == STAGE3_PROFILE_REGIONS
        )

    @property
    def actual_inference_step_count_observed(self) -> bool:
        return self.observed_inference_steps == self.configured_inference_steps

    @property
    def full_preregistered_gate_complete(self) -> bool:
        return bool(
            self.passed
            and self.internal_region_attribution_ready
            and self.actual_inference_step_count_observed
        )

    def to_record(self) -> dict[str, object]:
        return {
            "schema_version": B0_GATE_SCHEMA_VERSION,
            "gate": "stage3b_real_b0_non_perturbation",
            "method": self.method,
            "configured_inference_steps": self.configured_inference_steps,
            "observed_inference_steps": self.observed_inference_steps,
            "comparison_count": len(self.comparisons),
            "comparisons": [item.to_record() for item in self.comparisons],
            "measurement_scope": (
                "pcinfer_internal_regions_plus_optimizer_step"
                if self.internal_region_attribution_ready
                else "pcinfer_composite_gate_only"
            ),
            "internal_region_attribution_ready": self.internal_region_attribution_ready,
            "full_preregistered_gate_complete": self.full_preregistered_gate_complete,
            "actual_inference_step_count_observed": (
                self.actual_inference_step_count_observed
            ),
            "returned_tensor_coverage": (
                "all_tensors_exposed_by_pcinfer_return"
            ),
            "region_measurement_count": len(self.region_measurements),
            "region_measurements": [item.to_record() for item in self.region_measurements],
            "instrumentation": (
                self.instrumentation.to_record()
                if self.instrumentation is not None
                else None
            ),
            "evidence": False,
            "observed_tensor_gate_passed": self.passed,
            "passed": self.passed,
            "measurement": self.measurement.to_record(),
        }


def torch2pc_method_label(method: str) -> str:
    """Map the repository method name to the upstream Torch2PC label."""

    normalized = method.lower()
    try:
        return B0_TORCH2PC_LABELS[cast(MethodName, normalized)]
    except KeyError as exc:
        raise Stage3ProfilingError(f"unsupported B0 method: {method}") from exc


def flatten_output_tensors(value: Any, *, prefix: str = "pc_output") -> dict[str, Tensor]:
    """Recursively snapshot every tensor exposed by ``PCInfer`` output."""

    tensors: dict[str, Tensor] = {}

    def visit(item: Any, path: str) -> None:
        if isinstance(item, Tensor):
            tensors[path] = item
            return
        if isinstance(item, Mapping):
            for key in sorted(item, key=lambda candidate: str(candidate)):
                visit(item[key], f"{path}.{key}")
            return
        if isinstance(item, tuple | list):
            for index, child in enumerate(item):
                visit(child, f"{path}[{index}]")

    visit(value, prefix)
    if not tensors:
        raise Stage3ProfilingError("PCInfer output did not expose any tensors")
    return snapshot_named_tensors(tensors)


def _gradient_tensors(model: nn.Module) -> dict[str, Tensor]:
    values: dict[str, Tensor] = {}
    for name, parameter in model.named_parameters():
        if parameter.grad is None:
            values[f"gradient::{name}"] = torch.zeros_like(parameter)
        else:
            values[f"gradient::{name}"] = parameter.grad
    return snapshot_named_tensors(values)


def _model_state_tensors(model: nn.Module) -> dict[str, Tensor]:
    return snapshot_named_tensors(
        {
            f"model_state::{name}": tensor
            for name, tensor in model.state_dict().items()
        }
    )


def _clone_inputs(inputs: Tensor, targets: Tensor) -> tuple[Tensor, Tensor]:
    return inputs.detach().clone(), targets.detach().clone()


def _capture_rng_state(device: torch.device) -> tuple[Tensor, list[Tensor] | None]:
    cpu_state = torch.random.get_rng_state()
    cuda_states: list[Tensor] | None = None
    if device.type == "cuda" and torch.cuda.is_available():
        cuda_states = torch.cuda.get_rng_state_all()
    return cpu_state, cuda_states


def _restore_rng_state(
    state: tuple[Tensor, list[Tensor] | None],
) -> None:
    cpu_state, cuda_states = state
    torch.random.set_rng_state(cpu_state)
    if cuda_states is not None:
        torch.cuda.set_rng_state_all(cuda_states)


def _validate_pc_output(output: Any) -> Tensor:
    if not isinstance(output, tuple | list) or len(output) < 2:
        raise Stage3ProfilingError("Torch2PC PCInfer returned an unexpected structure")
    loss = output[1]
    if not isinstance(loss, Tensor) or loss.ndim != 0:
        raise Stage3ProfilingError("Torch2PC PCInfer did not return a scalar loss")
    if not bool(torch.isfinite(loss).item()):
        raise Stage3ProfilingError("Torch2PC PCInfer returned a non-finite loss")
    return loss


def _run_step(
    *,
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    loss_fn: nn.Module,
    inputs: Tensor,
    targets: Tensor,
    pc_infer: PCInferCallable,
    config: B0GateConfig,
    instrumented: bool,
) -> tuple[B0StepSnapshot, B0CompositeMeasurement | None]:
    model.train()
    optimizer.zero_grad(set_to_none=True)
    run_inputs, run_targets = _clone_inputs(inputs, targets)

    start_event: torch.cuda.Event | None = None
    end_event: torch.cuda.Event | None = None
    synchronization_points = 0
    if instrumented and config.device.type == "cuda" and torch.cuda.is_available():
        synchronize_device(config.device)
        synchronization_points += 1
        torch.cuda.reset_peak_memory_stats(config.device)
        start_event = torch.cuda.Event(enable_timing=True)
        end_event = torch.cuda.Event(enable_timing=True)
        start_event.record()

    profiler: Stage3BProfiler | None = None
    instrumentation: PCInferInstrumentationSummary | None = None
    observed_inference_steps: int | None = None
    started_ns = time.perf_counter_ns()
    if instrumented and supports_pcinfer_instrumentation(pc_infer):
        profiler = Stage3BProfiler(device=config.device, method=config.method)
        with torch.autograd.profiler.record_function(B0_COMPOSITE_LABEL):
            with instrument_pcinfer(
                pc_infer,
                profiler=profiler,
                configured_inference_steps=config.inference_steps,
            ) as observer:
                output = pc_infer(
                    model,
                    loss_fn,
                    run_inputs,
                    run_targets,
                    config.torch2pc_method,
                    eta=config.eta,
                    n=config.inference_steps,
                )
            instrumentation = observer.summary()
            observed_inference_steps = instrumentation.actual_inference_steps
    elif instrumented:
        with torch.autograd.profiler.record_function(B0_COMPOSITE_LABEL):
            output = pc_infer(
                model,
                loss_fn,
                run_inputs,
                run_targets,
                config.torch2pc_method,
                eta=config.eta,
                n=config.inference_steps,
            )
    else:
        output = pc_infer(
            model,
            loss_fn,
            run_inputs,
            run_targets,
            config.torch2pc_method,
            eta=config.eta,
            n=config.inference_steps,
        )

    _validate_pc_output(output)
    if profiler is not None:
        with profiler.region("optimizer_step", repetition=0, step=0):
            optimizer.step()
    else:
        optimizer.step()
    if end_event is not None:
        end_event.record()
    finished_ns = time.perf_counter_ns()

    device_time_us = 0.0
    peak_allocated_bytes = 0
    peak_reserved_bytes = 0
    if instrumented and config.device.type == "cuda" and torch.cuda.is_available():
        synchronize_device(config.device)
        synchronization_points += 1
    if start_event is not None and end_event is not None:
        device_time_us = float(start_event.elapsed_time(end_event)) * 1_000.0
        peak_allocated_bytes = int(torch.cuda.max_memory_allocated(config.device))
        peak_reserved_bytes = int(torch.cuda.max_memory_reserved(config.device))

    returned = flatten_output_tensors(output)
    gradients = _gradient_tensors(model)
    model_state = _model_state_tensors(model)
    snapshot = B0StepSnapshot(
        tensors={**returned, **gradients, **model_state},
        configured_inference_steps=config.inference_steps,
        observed_inference_steps=observed_inference_steps,
        region_measurements=profiler.records if profiler is not None else (),
        instrumentation=instrumentation,
    )
    if not instrumented:
        return snapshot, None

    measurement = B0CompositeMeasurement(
        host_time_us=(finished_ns - started_ns) / 1_000.0,
        device_time_us=device_time_us,
        peak_allocated_bytes=peak_allocated_bytes,
        peak_reserved_bytes=peak_reserved_bytes,
        synchronization_points=synchronization_points,
    )
    return snapshot, measurement


def run_b0_non_perturbation_gate(
    *,
    model: nn.Module,
    optimizer_factory: OptimizerFactory,
    loss_fn: nn.Module,
    inputs: Tensor,
    targets: Tensor,
    pc_infer: PCInferCallable,
    config: B0GateConfig,
) -> B0GateReport:
    """Compare one real B0 step with and without composite instrumentation."""

    reference_model = deepcopy(model).to(device=config.device, dtype=config.dtype)
    candidate_model = deepcopy(model).to(device=config.device, dtype=config.dtype)
    reference_optimizer = optimizer_factory(reference_model)
    candidate_optimizer = optimizer_factory(candidate_model)
    prepared_inputs = inputs.to(device=config.device, dtype=config.dtype)
    prepared_targets = targets.to(device=config.device)

    rng_state = _capture_rng_state(config.device)
    reference, reference_measurement = _run_step(
        model=reference_model,
        optimizer=reference_optimizer,
        loss_fn=loss_fn,
        inputs=prepared_inputs,
        targets=prepared_targets,
        pc_infer=pc_infer,
        config=config,
        instrumented=False,
    )
    if reference_measurement is not None:
        raise Stage3ProfilingError("reference B0 step unexpectedly produced a measurement")

    _restore_rng_state(rng_state)
    candidate, measurement = _run_step(
        model=candidate_model,
        optimizer=candidate_optimizer,
        loss_fn=loss_fn,
        inputs=prepared_inputs,
        targets=prepared_targets,
        pc_infer=pc_infer,
        config=config,
        instrumented=True,
    )
    if measurement is None:
        raise Stage3ProfilingError("instrumented B0 step produced no measurement")
    if reference.configured_inference_steps != candidate.configured_inference_steps:
        raise Stage3ProfilingError("configured inference-step counts differ")

    comparisons = assert_non_perturbing(
        reference.tensors,
        candidate.tensors,
        thresholds=thresholds_for_device(config.device, config.dtype),
    )
    return B0GateReport(
        method=config.method,
        configured_inference_steps=config.inference_steps,
        comparisons=comparisons,
        measurement=measurement,
        observed_inference_steps=candidate.observed_inference_steps,
        region_measurements=candidate.region_measurements,
        instrumentation=candidate.instrumentation,
    )
