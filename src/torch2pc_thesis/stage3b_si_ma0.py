"""Model-level SI-MA0 instrumentation for canonical Strict state inference.

The implementation is intentionally non-invasive: it mirrors the frozen
``StrictPCPredErrs`` control flow inside a temporary replacement installed in
the loaded Torch2PC ``PCInfer`` function globals.  The upstream checkout is
never edited and the original callable is restored after every run.
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from collections.abc import Callable, Iterator, Mapping, MutableMapping, Sequence
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass, field
from pathlib import Path
from types import MethodType
from typing import Any, Final, Literal, cast

import torch
from torch import Tensor, nn

CONTRACT_ID: Final[str] = "stage3b-si-ma0-v2"
IMPLEMENTATION_SCHEMA_ID: Final[str] = "stage3b-si-ma0-implementation-v1"
TORCH2PC_COMMIT: Final[str] = "b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4"

ObserverMode = Literal[
    "no_hooks",
    "instrumented_disabled",
    "counters_only",
    "tensor_summaries",
    "full_attribution",
]
ExecutionScope = Literal["smoke", "confirmatory"]
RegionName = Literal[
    "inference_setup",
    "lower_prediction_and_error",
    "upper_state_vjp",
    "component_aggregation",
    "belief_update",
    "sweep_bookkeeping",
    "inference_finalize",
]

OBSERVER_MODES: Final[tuple[ObserverMode, ...]] = (
    "no_hooks",
    "instrumented_disabled",
    "counters_only",
    "tensor_summaries",
    "full_attribution",
)
REGIONS: Final[tuple[RegionName, ...]] = (
    "inference_setup",
    "lower_prediction_and_error",
    "upper_state_vjp",
    "component_aggregation",
    "belief_update",
    "sweep_bookkeeping",
    "inference_finalize",
)


class SIMA0Error(RuntimeError):
    """Raised when the frozen SI-MA0 implementation contract is violated."""


@dataclass(frozen=True)
class NumericalThresholds:
    """Zero-safe numerical comparison thresholds."""

    zero_atol: float
    max_relative_l2: float
    max_abs: float
    min_cosine: float


@dataclass(frozen=True)
class TensorComparison:
    """Serializable zero-safe comparison result."""

    reference_norm: float
    candidate_norm: float
    absolute_l2: float
    relative_l2: float
    max_abs: float
    cosine: float | None
    finite: bool
    passed: bool

    def to_record(self, prefix: str = "") -> dict[str, float | bool | None]:
        return {
            f"{prefix}reference_norm": self.reference_norm,
            f"{prefix}candidate_norm": self.candidate_norm,
            f"{prefix}absolute_l2": self.absolute_l2,
            f"{prefix}relative_l2": self.relative_l2,
            f"{prefix}max_abs": self.max_abs,
            f"{prefix}cosine": self.cosine,
            f"{prefix}finite": self.finite,
            f"{prefix}passed": self.passed,
        }


@dataclass
class _PendingRegion:
    region: RegionName
    sweep_index: int | None
    layer_index: int | None
    start_ns: int | None = None
    end_ns: int | None = None
    start_event: torch.cuda.Event | None = None
    end_event: torch.cuda.Event | None = None


@dataclass
class _PendingTotal:
    start_ns: int | None = None
    end_ns: int | None = None
    start_event: torch.cuda.Event | None = None
    end_event: torch.cuda.Event | None = None


@dataclass(frozen=True)
class PendingStateUpdate:
    """Deferred tensor payload for one real Strict belief update."""

    sequence_index: int
    sweep_index: int
    layer_index: int
    state_version_before: int
    state_version_after: int
    jacobian_version: str
    state_before: Tensor
    state_after: Tensor
    c_self: Tensor
    c_upper: Tensor
    observed_update: Tensor
    source_error: Tensor
    transported_upper: Tensor
    saved_tensor_count: int
    saved_tensor_bytes: int
    graph_birth_event: int
    graph_release_event: int


@dataclass(frozen=True)
class PendingOutputError:
    """Deferred tensor payload for one output-error observation."""

    sequence_index: int
    sweep_index: int
    output_error: Tensor
    output_error_vjp_call_count: int
    saved_tensor_count: int
    saved_tensor_bytes: int
    graph_birth_event: int
    graph_release_event: int


@dataclass
class SIMA0Recorder:
    """Collect passive SI-MA0 observations for one ``StrictPCPredErrs`` call."""

    mode: ObserverMode
    device: torch.device
    thresholds: NumericalThresholds
    metadata: Mapping[str, Any]
    state_updates: list[PendingStateUpdate] = field(default_factory=list)
    output_errors: list[PendingOutputError] = field(default_factory=list)
    region_records: list[dict[str, Any]] = field(default_factory=list)
    total_records: list[dict[str, Any]] = field(default_factory=list)
    vjp_call_count: int = 0
    saved_tensor_count: int = 0
    saved_tensor_bytes: int = 0
    synchronization_count: int = 0
    _sequence_index: int = 0
    _pending_regions: list[_PendingRegion] = field(default_factory=list)
    _pending_total: _PendingTotal | None = None

    @property
    def capture_timing(self) -> bool:
        return self.mode in {
            "counters_only",
            "tensor_summaries",
            "full_attribution",
        }

    @property
    def capture_tensors(self) -> bool:
        return self.mode in {"tensor_summaries", "full_attribution"}

    @property
    def capture_records(self) -> bool:
        return self.mode == "full_attribution"

    def next_sequence(self) -> int:
        value = self._sequence_index
        self._sequence_index += 1
        return value

    def saved_tensor_snapshot(self) -> tuple[int, int]:
        return self.saved_tensor_count, self.saved_tensor_bytes

    @contextmanager
    def saved_tensor_accounting(self) -> Iterator[None]:
        if not self.capture_tensors:
            yield
            return

        def pack(tensor: Tensor) -> Tensor:
            self.saved_tensor_count += 1
            self.saved_tensor_bytes += tensor.numel() * tensor.element_size()
            return tensor

        def unpack(tensor: Tensor) -> Tensor:
            return tensor

        with torch.autograd.graph.saved_tensors_hooks(pack, unpack):
            yield

    @contextmanager
    def region(
        self,
        region: RegionName,
        *,
        sweep_index: int | None = None,
        layer_index: int | None = None,
    ) -> Iterator[None]:
        if not self.capture_timing:
            yield
            return
        pending = _PendingRegion(
            region=region,
            sweep_index=sweep_index,
            layer_index=layer_index,
        )
        if self.device.type == "cuda":
            pending.start_event = torch.cuda.Event(enable_timing=True)
            pending.end_event = torch.cuda.Event(enable_timing=True)
            pending.start_event.record()
        else:
            pending.start_ns = time.perf_counter_ns()
        try:
            yield
        finally:
            if self.device.type == "cuda":
                assert pending.end_event is not None
                pending.end_event.record()
            else:
                pending.end_ns = time.perf_counter_ns()
            self._pending_regions.append(pending)

    @contextmanager
    def total_timer(self) -> Iterator[None]:
        if not self.capture_timing:
            yield
            return
        if self._pending_total is not None:
            raise SIMA0Error("state-inference total timer is already active")
        pending = _PendingTotal()
        self._pending_total = pending
        if self.device.type == "cuda":
            pending.start_event = torch.cuda.Event(enable_timing=True)
            pending.end_event = torch.cuda.Event(enable_timing=True)
            pending.start_event.record()
        else:
            pending.start_ns = time.perf_counter_ns()
        try:
            yield
        finally:
            if self.device.type == "cuda":
                assert pending.end_event is not None
                pending.end_event.record()
            else:
                pending.end_ns = time.perf_counter_ns()

    def finalize_timing(self) -> None:
        if not self.capture_timing:
            return
        if self._pending_total is None:
            raise SIMA0Error("state-inference total timer was not recorded")
        if self.device.type == "cuda":
            torch.cuda.synchronize(self.device)
            self.synchronization_count += 1
        for pending in self._pending_regions:
            duration_ms = _pending_duration_ms(pending)
            self.region_records.append(
                {
                    **self.metadata,
                    "implementation_schema_id": IMPLEMENTATION_SCHEMA_ID,
                    "observer_mode": self.mode,
                    "region": pending.region,
                    "sweep_index": pending.sweep_index,
                    "layer_index": pending.layer_index,
                    "duration_ms": duration_ms,
                    "finite": math.isfinite(duration_ms),
                    "nonnegative": duration_ms >= 0.0,
                }
            )
        total_ms = _pending_total_duration_ms(self._pending_total)
        region_sum_ms = sum(
            float(record["duration_ms"]) for record in self.region_records
        )
        residual = abs(total_ms - region_sum_ms) / max(total_ms, 1e-12)
        self.total_records.append(
            {
                **self.metadata,
                "implementation_schema_id": IMPLEMENTATION_SCHEMA_ID,
                "observer_mode": self.mode,
                "total_device_time_ms": total_ms,
                "exclusive_region_time_sum_ms": region_sum_ms,
                "accounting_residual": residual,
                "synchronization_count": self.synchronization_count,
                "finite": math.isfinite(total_ms) and math.isfinite(residual),
                "nonnegative": total_ms >= 0.0,
            }
        )


@dataclass(frozen=True)
class ModeRunResult:
    """Numerical outputs from one observer mode."""

    mode: ObserverMode
    loss: Tensor
    beliefs: tuple[Tensor | None, ...]
    gradients: tuple[Tensor | None, ...]
    model_fingerprint_before: str
    model_fingerprint_after: str
    input_fingerprint_before: str
    input_fingerprint_after: str
    target_fingerprint_before: str
    target_fingerprint_after: str
    rng_fingerprint_before: str
    rng_fingerprint_after: str
    recorder: SIMA0Recorder | None


def _pending_duration_ms(pending: _PendingRegion) -> float:
    if pending.start_event is not None and pending.end_event is not None:
        return float(pending.start_event.elapsed_time(pending.end_event))
    if pending.start_ns is None or pending.end_ns is None:
        raise SIMA0Error(f"incomplete timing record for region {pending.region}")
    return (pending.end_ns - pending.start_ns) / 1_000_000.0


def _pending_total_duration_ms(pending: _PendingTotal) -> float:
    if pending.start_event is not None and pending.end_event is not None:
        return float(pending.start_event.elapsed_time(pending.end_event))
    if pending.start_ns is None or pending.end_ns is None:
        raise SIMA0Error("incomplete state-inference total timing record")
    return (pending.end_ns - pending.start_ns) / 1_000_000.0


def canonical_json_digest(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def tensor_digest(tensor: Tensor) -> str:
    value = tensor.detach().contiguous().cpu()
    header = f"{value.dtype}:{tuple(value.shape)}:".encode()
    return hashlib.sha256(header + value.numpy().tobytes()).hexdigest()


def tensor_sequence_digest(values: Sequence[Tensor | None]) -> str:
    digest = hashlib.sha256()
    for value in values:
        if value is None:
            digest.update(b"<none>")
        else:
            digest.update(tensor_digest(value).encode("ascii"))
    return digest.hexdigest()


def model_state_digest(model: nn.Module) -> str:
    digest = hashlib.sha256()
    for name, value in sorted(model.state_dict().items()):
        digest.update(name.encode("utf-8"))
        digest.update(tensor_digest(value).encode("ascii"))
    return digest.hexdigest()


def rng_digest(device: torch.device) -> str:
    digest = hashlib.sha256(torch.get_rng_state().cpu().numpy().tobytes())
    if device.type == "cuda":
        digest.update(torch.cuda.get_rng_state(device).cpu().numpy().tobytes())
    return digest.hexdigest()


def compare_tensors(
    reference: Tensor,
    candidate: Tensor,
    thresholds: NumericalThresholds,
) -> TensorComparison:
    if reference.shape != candidate.shape:
        return TensorComparison(
            reference_norm=math.inf,
            candidate_norm=math.inf,
            absolute_l2=math.inf,
            relative_l2=math.inf,
            max_abs=math.inf,
            cosine=None,
            finite=False,
            passed=False,
        )
    ref = reference.detach().to(dtype=torch.float64).reshape(-1)
    cand = candidate.detach().to(dtype=torch.float64).reshape(-1)
    finite = bool(torch.isfinite(ref).all() and torch.isfinite(cand).all())
    if not finite:
        return TensorComparison(
            reference_norm=math.inf,
            candidate_norm=math.inf,
            absolute_l2=math.inf,
            relative_l2=math.inf,
            max_abs=math.inf,
            cosine=None,
            finite=False,
            passed=False,
        )
    reference_norm = float(torch.linalg.vector_norm(ref).item())
    candidate_norm = float(torch.linalg.vector_norm(cand).item())
    difference = cand - ref
    absolute_l2 = float(torch.linalg.vector_norm(difference).item())
    max_abs = (
        float(difference.abs().max().item()) if difference.numel() else 0.0
    )
    reference_zero = reference_norm <= thresholds.zero_atol
    candidate_zero = candidate_norm <= thresholds.zero_atol
    denominator = max(reference_norm, candidate_norm, thresholds.zero_atol)
    relative_l2 = absolute_l2 / denominator
    cosine: float | None
    if reference_zero and candidate_zero:
        cosine = None
        passed = max_abs <= thresholds.max_abs
    elif reference_zero != candidate_zero:
        cosine = None
        passed = False
    else:
        cosine = float(
            torch.nn.functional.cosine_similarity(
                ref.unsqueeze(0),
                cand.unsqueeze(0),
                dim=1,
            ).item()
        )
        passed = (
            relative_l2 <= thresholds.max_relative_l2
            and max_abs <= thresholds.max_abs
            and cosine >= thresholds.min_cosine
        )
    return TensorComparison(
        reference_norm=reference_norm,
        candidate_norm=candidate_norm,
        absolute_l2=absolute_l2,
        relative_l2=relative_l2,
        max_abs=max_abs,
        cosine=cosine,
        finite=True,
        passed=passed,
    )


def load_contract(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SIMA0Error("SI-MA0 contract must contain a JSON object")
    if value.get("contract_id") != CONTRACT_ID:
        raise SIMA0Error("SI-MA0 implementation requires preregistration v2")
    if value.get("schema_version") != 2:
        raise SIMA0Error("SI-MA0 contract schema_version must be 2")
    if value.get("status") != "frozen_preregistration_amendment":
        raise SIMA0Error("SI-MA0 contract is not the frozen amendment")
    scope = value.get("scope")
    counts = value.get("expected_counts")
    reconstruction = value.get("reconstruction")
    if not isinstance(scope, dict) or not isinstance(counts, dict):
        raise SIMA0Error("SI-MA0 contract scope/counts are missing")
    if not isinstance(reconstruction, dict):
        raise SIMA0Error("SI-MA0 reconstruction contract is missing")
    expected_scope = {
        "model_modules": 6,
        "updated_state_layers_per_sweep": 5,
        "output_error_records_per_sweep": 1,
        "inference_steps": 20,
    }
    for key, expected in expected_scope.items():
        if scope.get(key) != expected:
            raise SIMA0Error(f"SI-MA0 contract field scope.{key} is invalid")
    expected_counts = {
        "confirmatory_state_update_events": 3000,
        "confirmatory_output_error_records": 600,
        "confirmatory_diagnostic_records": 3600,
    }
    for key, expected in expected_counts.items():
        if counts.get(key) != expected:
            raise SIMA0Error(
                f"SI-MA0 contract field expected_counts.{key} is invalid"
            )
    if reconstruction.get("record_scope") != "state_update_events_only":
        raise SIMA0Error("SI-MA0 reconstruction scope is invalid")
    if reconstruction.get("output_error_is_not_state_update") is not True:
        raise SIMA0Error("output error must remain separate from state updates")
    return value


def thresholds_for(
    contract: Mapping[str, Any],
    *,
    lane: Literal["cpu", "rocm"],
) -> NumericalThresholds:
    threshold_root = contract.get("thresholds")
    if not isinstance(threshold_root, Mapping):
        raise SIMA0Error("SI-MA0 numerical thresholds are missing")
    key = "cpu_smoke_float64" if lane == "cpu" else "rocm_float32"
    raw = threshold_root.get(key)
    if not isinstance(raw, Mapping):
        raise SIMA0Error(f"SI-MA0 threshold profile is missing: {key}")
    return NumericalThresholds(
        zero_atol=float(raw["zero_atol"]),
        max_relative_l2=float(raw["max_relative_l2"]),
        max_abs=float(raw["max_abs"]),
        min_cosine=float(raw["min_cosine"]),
    )


def expected_record_counts(
    *,
    model_count: int,
    batch_count: int,
    inference_steps: int,
    updated_state_layers: int,
) -> dict[str, int]:
    output_errors = model_count * batch_count * inference_steps
    updates = output_errors * updated_state_layers
    return {
        "state_update_events": updates,
        "output_error_records": output_errors,
        "diagnostic_records": updates + output_errors,
        "mode_comparisons": model_count
        * batch_count
        * (len(OBSERVER_MODES) - 1),
    }


def _function_globals(callable_value: Callable[..., Any]) -> MutableMapping[str, Any]:
    namespace = getattr(callable_value, "__globals__", None)
    if isinstance(namespace, dict):
        return namespace
    if isinstance(callable_value, MethodType):
        bound = getattr(callable_value.__func__, "__globals__", None)
        if isinstance(bound, dict):
            return bound
    raise SIMA0Error("PCInfer does not expose a mutable function namespace")


def supports_si_ma0_instrumentation(pc_infer: Callable[..., Any]) -> bool:
    try:
        namespace = _function_globals(pc_infer)
    except SIMA0Error:
        return False
    return callable(namespace.get("StrictPCPredErrs"))


def _clone_optional(values: Sequence[Tensor | None]) -> tuple[Tensor | None, ...]:
    return tuple(
        None if value is None else value.detach().clone() for value in values
    )


def _parameter_gradients(model: nn.Module) -> tuple[Tensor | None, ...]:
    return tuple(
        None if parameter.grad is None else parameter.grad.detach().clone()
        for parameter in model.parameters()
    )


def _strict_instrumented(
    model: Sequence[nn.Module],
    vinit: Sequence[Tensor],
    loss_function: Callable[[Tensor, Tensor], Tensor],
    targets: Tensor,
    eta: float,
    n: int,
    *,
    recorder: SIMA0Recorder | None,
) -> tuple[list[Tensor | None], list[Tensor | None]]:
    if n < 1:
        raise ValueError("n must be positive")
    depth_plus_one = len(model) + 1
    epsilon: list[Tensor | None] = [None] * depth_plus_one
    total_context = (
        recorder.total_timer() if recorder is not None else nullcontext()
    )
    saved_context = (
        recorder.saved_tensor_accounting()
        if recorder is not None
        else nullcontext()
    )
    with total_context, saved_context:
        setup_context = (
            recorder.region("inference_setup")
            if recorder is not None
            else nullcontext()
        )
        with setup_context:
            v: list[Tensor | None] = [
                activation.detach().clone() for activation in vinit
            ]
            state_versions = [0] * depth_plus_one

        for sweep_index in range(n):
            bookkeeping_context = (
                recorder.region(
                    "sweep_bookkeeping",
                    sweep_index=sweep_index,
                )
                if recorder is not None
                else nullcontext()
            )
            with bookkeeping_context:
                if sweep_index < 0:
                    raise SIMA0Error("negative sweep index")

            saved_before = (
                recorder.saved_tensor_snapshot()
                if recorder is not None
                else (0, 0)
            )
            lower_context = (
                recorder.region(
                    "lower_prediction_and_error",
                    sweep_index=sweep_index,
                )
                if recorder is not None
                else nullcontext()
            )
            with lower_context:
                top_state = cast(Tensor, v[-2])
                current_input = top_state.detach().requires_grad_(True)
                current_output = model[-1](current_input)
                loss = loss_function(current_output, targets)
                output_error = torch.autograd.grad(
                    loss,
                    current_output,
                    retain_graph=True,
                )[0]
                epsilon[-1] = output_error
                if recorder is not None:
                    recorder.vjp_call_count += 1
            output_sequence = (
                recorder.next_sequence() if recorder is not None else -1
            )
            saved_after = (
                recorder.saved_tensor_snapshot()
                if recorder is not None
                else (0, 0)
            )
            if recorder is not None and recorder.capture_records:
                recorder.output_errors.append(
                    PendingOutputError(
                        sequence_index=output_sequence,
                        sweep_index=sweep_index,
                        output_error=output_error.detach().clone(),
                        output_error_vjp_call_count=1,
                        saved_tensor_count=saved_after[0] - saved_before[0],
                        saved_tensor_bytes=saved_after[1] - saved_before[1],
                        graph_birth_event=output_sequence,
                        graph_release_event=output_sequence + 1,
                    )
                )
            current_graph_birth_event = output_sequence

            for layer in reversed(range(1, depth_plus_one - 1)):
                sequence_index = (
                    recorder.next_sequence() if recorder is not None else -1
                )
                before = cast(Tensor, v[layer])
                saved_before = (
                    recorder.saved_tensor_snapshot()
                    if recorder is not None
                    else (0, 0)
                )
                jacobian_input = current_input
                jacobian_output = current_output
                upper_context = (
                    recorder.region(
                        "upper_state_vjp",
                        sweep_index=sweep_index,
                        layer_index=layer,
                    )
                    if recorder is not None
                    else nullcontext()
                )
                with upper_context:
                    upper_error = cast(Tensor, epsilon[layer + 1])
                    transported_upper = torch.autograd.grad(
                        jacobian_output,
                        jacobian_input,
                        grad_outputs=upper_error,
                        retain_graph=False,
                    )[0]
                    if recorder is not None:
                        recorder.vjp_call_count += 1

                lower_context = (
                    recorder.region(
                        "lower_prediction_and_error",
                        sweep_index=sweep_index,
                        layer_index=layer,
                    )
                    if recorder is not None
                    else nullcontext()
                )
                with lower_context:
                    if layer == 1:
                        with torch.no_grad():
                            lower_output = model[0](cast(Tensor, v[0]))
                        lower_input: Tensor | None = None
                    else:
                        lower_input = (
                            cast(Tensor, v[layer - 1])
                            .detach()
                            .requires_grad_(True)
                        )
                        lower_output = model[layer - 1](lower_input)
                    self_error = lower_output - before
                    epsilon[layer] = self_error

                aggregate_context = (
                    recorder.region(
                        "component_aggregation",
                        sweep_index=sweep_index,
                        layer_index=layer,
                    )
                    if recorder is not None
                    else nullcontext()
                )
                with aggregate_context:
                    c_self = self_error
                    c_upper = -transported_upper
                    observed_update = self_error - transported_upper
                    jacobian_version = (
                        f"s{sweep_index}:l{layer}:"
                        f"{tensor_digest(jacobian_input)}:"
                        f"{tensor_digest(jacobian_output)}"
                        if recorder is not None and recorder.capture_tensors
                        else f"s{sweep_index}:l{layer}"
                    )

                update_context = (
                    recorder.region(
                        "belief_update",
                        sweep_index=sweep_index,
                        layer_index=layer,
                    )
                    if recorder is not None
                    else nullcontext()
                )
                with update_context:
                    after = before + eta * observed_update
                    v[layer] = after
                    version_before = state_versions[layer]
                    state_versions[layer] += 1
                    version_after = state_versions[layer]

                saved_after = (
                    recorder.saved_tensor_snapshot()
                    if recorder is not None
                    else (0, 0)
                )
                if recorder is not None and recorder.capture_records:
                    recorder.state_updates.append(
                        PendingStateUpdate(
                            sequence_index=sequence_index,
                            sweep_index=sweep_index,
                            layer_index=layer,
                            state_version_before=version_before,
                            state_version_after=version_after,
                            jacobian_version=jacobian_version,
                            state_before=before.detach().clone(),
                            state_after=after.detach().clone(),
                            c_self=c_self.detach().clone(),
                            c_upper=c_upper.detach().clone(),
                            observed_update=observed_update.detach().clone(),
                            source_error=self_error.detach().clone(),
                            transported_upper=(
                                transported_upper.detach().clone()
                            ),
                            saved_tensor_count=(
                                saved_after[0] - saved_before[0]
                            ),
                            saved_tensor_bytes=(
                                saved_after[1] - saved_before[1]
                            ),
                            graph_birth_event=current_graph_birth_event,
                            graph_release_event=sequence_index,
                        )
                    )
                if layer > 1:
                    current_graph_birth_event = sequence_index
                current_input = cast(Tensor, lower_input)
                current_output = lower_output

            detach_context = (
                recorder.region(
                    "sweep_bookkeeping",
                    sweep_index=sweep_index,
                )
                if recorder is not None
                else nullcontext()
            )
            with detach_context:
                for layer in range(1, depth_plus_one - 1):
                    v[layer] = cast(Tensor, v[layer]).detach()
                    epsilon[layer] = cast(Tensor, epsilon[layer]).detach()

        finalize_context = (
            recorder.region("inference_finalize")
            if recorder is not None
            else nullcontext()
        )
        with finalize_context:
            if len(v) != depth_plus_one or len(epsilon) != depth_plus_one:
                raise SIMA0Error("Strict state-inference result is incomplete")

    if recorder is not None:
        recorder.finalize_timing()
    return v, epsilon


@contextmanager
def instrument_strict_pcinfer(
    pc_infer: Callable[..., Any],
    *,
    recorder: SIMA0Recorder | None,
) -> Iterator[None]:
    """Temporarily replace only ``StrictPCPredErrs`` in ``PCInfer`` globals."""

    if recorder is None or recorder.mode == "no_hooks":
        yield
        return
    namespace = _function_globals(pc_infer)
    original = namespace.get("StrictPCPredErrs")
    if not callable(original):
        raise SIMA0Error("PCInfer namespace has no StrictPCPredErrs callable")

    def wrapped(
        model: Sequence[nn.Module],
        vinit: Sequence[Tensor],
        loss_function: Callable[[Tensor, Tensor], Tensor],
        targets: Tensor,
        eta: float,
        n: int,
    ) -> tuple[list[Tensor | None], list[Tensor | None]]:
        return _strict_instrumented(
            model,
            vinit,
            loss_function,
            targets,
            eta,
            n,
            recorder=recorder,
        )

    namespace["StrictPCPredErrs"] = wrapped
    try:
        yield
    finally:
        namespace["StrictPCPredErrs"] = original


def run_observer_mode(
    *,
    pc_infer: Callable[..., Any],
    model: nn.Module,
    loss_function: Callable[[Tensor, Tensor], Tensor],
    inputs: Tensor,
    targets: Tensor,
    eta: float,
    inference_steps: int,
    mode: ObserverMode,
    thresholds: NumericalThresholds,
    metadata: Mapping[str, Any],
) -> ModeRunResult:
    """Run one fresh-model observer arm without an optimizer update."""

    model.zero_grad(set_to_none=True)
    before_model = model_state_digest(model)
    before_input = tensor_digest(inputs)
    before_target = tensor_digest(targets)
    before_rng = rng_digest(inputs.device)
    recorder = (
        None
        if mode == "no_hooks"
        else SIMA0Recorder(
            mode=mode,
            device=inputs.device,
            thresholds=thresholds,
            metadata=metadata,
        )
    )
    with instrument_strict_pcinfer(pc_infer, recorder=recorder):
        output = pc_infer(
            model,
            loss_function,
            inputs,
            targets,
            "Strict",
            eta,
            inference_steps,
            None,
        )
    if not isinstance(output, tuple) or len(output) != 5:
        raise SIMA0Error("PCInfer returned an unexpected result")
    _vhat, loss, _dldy, beliefs, _epsilon = output
    if not isinstance(loss, Tensor) or not isinstance(beliefs, Sequence):
        raise SIMA0Error("PCInfer returned invalid loss/belief values")
    after_model = model_state_digest(model)
    after_input = tensor_digest(inputs)
    after_target = tensor_digest(targets)
    after_rng = rng_digest(inputs.device)
    return ModeRunResult(
        mode=mode,
        loss=loss.detach().clone(),
        beliefs=_clone_optional(cast(Sequence[Tensor | None], beliefs)),
        gradients=_parameter_gradients(model),
        model_fingerprint_before=before_model,
        model_fingerprint_after=after_model,
        input_fingerprint_before=before_input,
        input_fingerprint_after=after_input,
        target_fingerprint_before=before_target,
        target_fingerprint_after=after_target,
        rng_fingerprint_before=before_rng,
        rng_fingerprint_after=after_rng,
        recorder=recorder,
    )


def compare_mode_results(
    reference: ModeRunResult,
    candidate: ModeRunResult,
    thresholds: NumericalThresholds,
    *,
    metadata: Mapping[str, Any],
) -> dict[str, Any]:
    """Compare one observer mode with the canonical no-hooks reference."""

    if reference.mode != "no_hooks":
        raise SIMA0Error("observer comparison reference must be no_hooks")
    loss_comparison = compare_tensors(
        reference.loss.reshape(1),
        candidate.loss.reshape(1),
        thresholds,
    )
    belief_pairs = list(zip(reference.beliefs, candidate.beliefs, strict=True))
    belief_metrics = [
        compare_tensors(ref, cand, thresholds)
        for ref, cand in belief_pairs
        if ref is not None and cand is not None
    ]
    gradient_pairs = list(
        zip(reference.gradients, candidate.gradients, strict=True)
    )
    gradient_metrics = [
        compare_tensors(ref, cand, thresholds)
        for ref, cand in gradient_pairs
        if ref is not None and cand is not None
    ]
    missing_beliefs = any(
        (ref is None) != (cand is None) for ref, cand in belief_pairs
    )
    missing_gradients = any(
        (ref is None) != (cand is None) for ref, cand in gradient_pairs
    )
    model_unchanged = (
        candidate.model_fingerprint_before
        == candidate.model_fingerprint_after
        == reference.model_fingerprint_before
        == reference.model_fingerprint_after
    )
    input_target_unchanged = (
        candidate.input_fingerprint_before
        == candidate.input_fingerprint_after
        == reference.input_fingerprint_before
        == reference.input_fingerprint_after
        and candidate.target_fingerprint_before
        == candidate.target_fingerprint_after
        == reference.target_fingerprint_before
        == reference.target_fingerprint_after
    )
    rng_equal = (
        candidate.rng_fingerprint_before == reference.rng_fingerprint_before
        and candidate.rng_fingerprint_after == reference.rng_fingerprint_after
    )
    passed = (
        loss_comparison.passed
        and not missing_beliefs
        and not missing_gradients
        and all(item.passed for item in belief_metrics)
        and all(item.passed for item in gradient_metrics)
        and model_unchanged
        and input_target_unchanged
        and rng_equal
    )
    return {
        **metadata,
        "implementation_schema_id": IMPLEMENTATION_SCHEMA_ID,
        "reference_mode": reference.mode,
        "candidate_mode": candidate.mode,
        **loss_comparison.to_record("loss_"),
        "belief_record_count": len(belief_metrics),
        "belief_max_relative_l2": max(
            (item.relative_l2 for item in belief_metrics),
            default=0.0,
        ),
        "belief_max_abs": max(
            (item.max_abs for item in belief_metrics),
            default=0.0,
        ),
        "belief_all_passed": all(item.passed for item in belief_metrics),
        "gradient_record_count": len(gradient_metrics),
        "gradient_max_relative_l2": max(
            (item.relative_l2 for item in gradient_metrics),
            default=0.0,
        ),
        "gradient_max_abs": max(
            (item.max_abs for item in gradient_metrics),
            default=0.0,
        ),
        "gradient_all_passed": all(
            item.passed for item in gradient_metrics
        ),
        "model_state_unchanged": model_unchanged,
        "input_target_fingerprint_unchanged": input_target_unchanged,
        "rng_fingerprint_equal": rng_equal,
        "finite": (
            loss_comparison.finite
            and all(item.finite for item in belief_metrics)
            and all(item.finite for item in gradient_metrics)
        ),
        "passed": passed,
    }


def materialize_state_update_records(
    recorder: SIMA0Recorder,
    *,
    eta: float,
) -> list[dict[str, Any]]:
    """Convert deferred update tensors to zero-safe CSV-ready records."""

    records: list[dict[str, Any]] = []
    for pending in recorder.state_updates:
        reconstructed_update = pending.c_self + pending.c_upper
        reconstruction = compare_tensors(
            pending.observed_update,
            reconstructed_update,
            recorder.thresholds,
        )
        expected_after = (
            pending.state_before + eta * pending.observed_update
        )
        transition = compare_tensors(
            expected_after,
            pending.state_after,
            recorder.thresholds,
        )
        finite = reconstruction.finite and transition.finite
        passed = (
            reconstruction.passed
            and transition.passed
            and pending.state_version_after
            == pending.state_version_before + 1
        )
        records.append(
            {
                **recorder.metadata,
                "implementation_schema_id": IMPLEMENTATION_SCHEMA_ID,
                "observer_mode": recorder.mode,
                "record_type": "state_update",
                "sequence_index": pending.sequence_index,
                "sweep_index": pending.sweep_index,
                "layer_index": pending.layer_index,
                "state_version_before": pending.state_version_before,
                "state_version_after": pending.state_version_after,
                "jacobian_version": pending.jacobian_version,
                "canonical_channel_ids": "self,upper",
                "c_self_norm": float(
                    torch.linalg.vector_norm(pending.c_self).item()
                ),
                "c_upper_norm": float(
                    torch.linalg.vector_norm(pending.c_upper).item()
                ),
                "source_error_norm": float(
                    torch.linalg.vector_norm(pending.source_error).item()
                ),
                "transported_upper_norm": float(
                    torch.linalg.vector_norm(
                        pending.transported_upper
                    ).item()
                ),
                "observed_update_norm": float(
                    torch.linalg.vector_norm(
                        pending.observed_update
                    ).item()
                ),
                "reconstructed_update_norm": float(
                    torch.linalg.vector_norm(
                        reconstructed_update
                    ).item()
                ),
                **reconstruction.to_record(),
                **transition.to_record("state_transition_"),
                "vjp_call_count": 1,
                "saved_tensor_count": pending.saved_tensor_count,
                "saved_tensor_bytes": pending.saved_tensor_bytes,
                "graph_birth_event": pending.graph_birth_event,
                "graph_release_event": pending.graph_release_event,
                "synchronization_count": recorder.synchronization_count,
                "finite": finite,
                "passed": passed,
            }
        )
    return records


def materialize_output_error_records(
    recorder: SIMA0Recorder,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for pending in recorder.output_errors:
        finite = bool(torch.isfinite(pending.output_error).all())
        records.append(
            {
                **recorder.metadata,
                "implementation_schema_id": IMPLEMENTATION_SCHEMA_ID,
                "observer_mode": recorder.mode,
                "record_type": "output_error",
                "sequence_index": pending.sequence_index,
                "sweep_index": pending.sweep_index,
                "output_error_norm": float(
                    torch.linalg.vector_norm(
                        pending.output_error
                    ).item()
                ),
                "output_error_vjp_call_count": (
                    pending.output_error_vjp_call_count
                ),
                "saved_tensor_count": pending.saved_tensor_count,
                "saved_tensor_bytes": pending.saved_tensor_bytes,
                "graph_birth_event": pending.graph_birth_event,
                "graph_release_event": pending.graph_release_event,
                "synchronization_count": recorder.synchronization_count,
                "finite": finite,
                "passed": finite,
            }
        )
    return records


def validate_event_order(
    state_records: Sequence[Mapping[str, Any]],
    output_records: Sequence[Mapping[str, Any]],
    *,
    inference_steps: int,
    updated_state_layers: int,
) -> None:
    if len(state_records) != inference_steps * updated_state_layers:
        raise SIMA0Error("unexpected state-update event count")
    if len(output_records) != inference_steps:
        raise SIMA0Error("unexpected output-error record count")
    state_keys = {
        (
            int(record["sweep_index"]),
            int(record["layer_index"]),
        )
        for record in state_records
    }
    if len(state_keys) != len(state_records):
        raise SIMA0Error("duplicate state-update event key")
    output_keys = {int(record["sweep_index"]) for record in output_records}
    if len(output_keys) != len(output_records):
        raise SIMA0Error("duplicate output-error event key")
    expected_layers = list(range(updated_state_layers, 0, -1))
    for sweep_index in range(inference_steps):
        output = [
            record
            for record in output_records
            if int(record["sweep_index"]) == sweep_index
        ]
        updates = sorted(
            (
                record
                for record in state_records
                if int(record["sweep_index"]) == sweep_index
            ),
            key=lambda record: int(record["sequence_index"]),
        )
        if len(output) != 1 or len(updates) != updated_state_layers:
            raise SIMA0Error("incomplete Strict sweep records")
        if int(output[0]["sequence_index"]) >= int(
            updates[0]["sequence_index"]
        ):
            raise SIMA0Error("output error must precede state updates")
        observed_layers = [int(record["layer_index"]) for record in updates]
        if observed_layers != expected_layers:
            raise SIMA0Error("Strict layer-update ordering is invalid")
    for layer_index in range(1, updated_state_layers + 1):
        layer_records = sorted(
            (
                record
                for record in state_records
                if int(record["layer_index"]) == layer_index
            ),
            key=lambda record: int(record["sweep_index"]),
        )
        if len(layer_records) != inference_steps:
            raise SIMA0Error("state-version sequence is incomplete")
        for expected_before, record in enumerate(layer_records):
            before = int(record["state_version_before"])
            after = int(record["state_version_after"])
            if before != expected_before or after != expected_before + 1:
                raise SIMA0Error("state versions are not monotone")


def validate_region_accounting(
    recorder: SIMA0Recorder,
    *,
    maximum_residual: float,
) -> dict[str, Any]:
    if not recorder.total_records:
        raise SIMA0Error("timing summary is missing")
    total = recorder.total_records[-1]
    residual = float(total["accounting_residual"])
    finite = bool(total["finite"])
    nonnegative = bool(total["nonnegative"])
    return {
        "accounting_residual": residual,
        "maximum_residual": maximum_residual,
        "finite": finite,
        "nonnegative": nonnegative,
        "passed": finite and nonnegative and residual <= maximum_residual,
    }
