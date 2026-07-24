"""Concrete Torch/Torch2PC backend for authorized QW-4B validation.

The implementation is present before the QW-4B freeze/evidence slices so the
future authorization changes data only.  Construction does not authorize a
run.  The public constructor binds the corrected ``stage2_baseline``
``FixedPred`` implementation, ``eta=1``, ``lenet_classic``, and the synthetic
engineering batch frozen by the runtime contract.
"""

from __future__ import annotations

import hashlib
import io
import json
import pickle
import random
import time
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Final, cast

import torch
from torch import Tensor, nn

from torch2pc_thesis.models import build_model
from torch2pc_thesis.pc_methods import load_pc_infer
from torch2pc_thesis.stage3b_qwake_core import (
    Capability,
    EdgeMeasurement,
    ObservationLevel,
)
from torch2pc_thesis.stage3b_qwake_fp_runtime import (
    RUNTIME_EFFECT_AUDIT_CAPABILITIES,
    RUNTIME_ENGINEERING_BATCH_ID,
    MatchedRuntimeBackend,
    QWakeFPRuntimeError,
    RuntimeArmExecution,
    RuntimeCellSpec,
    RuntimeValidationPermissionSet,
)
from torch2pc_thesis.stage3b_qwake_fp_runtime_adapter import (
    AnalyticCapture,
    ObservationCapture,
    OracleCapture,
    QWakeFPRuntimeBackend,
    collect_A0,
    collect_A1,
    collect_A2,
    compute_post_action_oracle,
    record_edge_costs,
)
from torch2pc_thesis.stage3b_qwake_fp_spec import (
    OBSERVATION_REGISTRY,
    PAIRED_VALIDATION_REGISTRY,
    QWakeFPAnalyticId,
    QWakeFPPairId,
)
from torch2pc_thesis.stage3b_qwake_fp_validation import (
    DisabledCapabilityAudit,
    EffectAudit,
    OracleIsolationRecord,
    PairArmId,
    PairArmRecord,
    ValidationLane,
)

type PCInferCallable = Callable[..., Any]
type SnapshotCallback = Callable[
    [int, Sequence[Tensor], Sequence[Tensor | None], Sequence[Tensor]],
    None,
]

_SYNTHETIC_BATCH_SIZE: Final = 2
_SYNTHETIC_IMAGE_SHAPE: Final = (1, 32, 32)
_FIXEDPRED_ETA: Final = 1.0
_ANALYTIC_CAPABILITIES: Final[Mapping[QWakeFPAnalyticId, tuple[Capability, ...]]] = {
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


class TorchFixedPredBackendError(QWakeFPRuntimeError):
    """Raised when the concrete canonical backend violates QW-4B."""


def _instrumented_fixedpred(
    model: nn.Sequential,
    vhat: Sequence[Tensor],
    dldy: Tensor,
    eta: float = 1.0,
    n: int | None = None,
    *,
    snapshot_callback: SnapshotCallback,
) -> tuple[list[Tensor], list[Tensor | None]]:
    """Mirror the pinned corrected FixedPred loop and expose read-only epochs."""

    depth_plus_one = len(model) + 1
    step_count = len(model) if n is None else int(n)
    if step_count < 1:
        raise ValueError("n must be positive")
    if float(eta) != _FIXEDPRED_ETA:
        raise TorchFixedPredBackendError("QWake-FP runtime requires eta=1")

    fixed = [activation.detach() for activation in vhat]
    linear_inputs: list[Tensor] = []
    linear_outputs: list[Tensor] = []
    for layer in range(depth_plus_one - 1):
        linear_input = fixed[layer].detach().requires_grad_(True)
        linear_inputs.append(linear_input)
        linear_outputs.append(model[layer](linear_input))

    epsilon: list[Tensor | None] = [None] * depth_plus_one
    epsilon[-1] = dldy.detach()
    beliefs = [activation.clone() for activation in fixed]
    snapshot_callback(0, beliefs, epsilon, fixed)

    for iteration in range(step_count):
        retain_graph = iteration < step_count - 1
        for layer in reversed(range(depth_plus_one - 1)):
            epsilon[layer] = fixed[layer] - beliefs[layer]
            upper_error = epsilon[layer + 1]
            if upper_error is None:
                raise TorchFixedPredBackendError("FixedPred error chain is incomplete")
            epsdfdv = torch.autograd.grad(
                linear_outputs[layer],
                linear_inputs[layer],
                grad_outputs=upper_error,
                retain_graph=retain_graph,
            )[0]
            delta = cast(Tensor, epsilon[layer]) - epsdfdv
            beliefs[layer] = beliefs[layer] + float(eta) * delta
        for layer in range(1, depth_plus_one - 1):
            beliefs[layer] = beliefs[layer].detach()
            error = epsilon[layer]
            if error is None:
                raise TorchFixedPredBackendError("FixedPred error is missing")
            epsilon[layer] = error.detach()
        snapshot_callback(iteration + 1, beliefs, epsilon, fixed)
    return beliefs, epsilon


@contextmanager
def _instrument_fixedpred(
    pc_infer: PCInferCallable,
    callback: SnapshotCallback,
) -> Iterator[None]:
    namespace = getattr(pc_infer, "__globals__", None)
    if not isinstance(namespace, dict):
        raise TorchFixedPredBackendError("PCInfer has no mutable global namespace")
    original = namespace.get("FixedPredPCPredErrs")
    if not callable(original):
        raise TorchFixedPredBackendError("PCInfer has no FixedPredPCPredErrs")

    def observed(
        model: nn.Sequential,
        vhat: Sequence[Tensor],
        dldy: Tensor,
        eta: float = 1.0,
        n: int | None = None,
    ) -> tuple[list[Tensor], list[Tensor | None]]:
        return _instrumented_fixedpred(
            model,
            vhat,
            dldy,
            eta,
            n,
            snapshot_callback=callback,
        )

    namespace["FixedPredPCPredErrs"] = observed
    try:
        yield
    finally:
        namespace["FixedPredPCPredErrs"] = original


class TorchFixedPredEngineeringBackend(MatchedRuntimeBackend, QWakeFPRuntimeBackend):
    """Canonical state-restorable CPU/ROCm backend for one authorized cell."""

    def __init__(
        self,
        *,
        cell: RuntimeCellSpec,
        torch2pc_dir: Path,
        _model: nn.Sequential | None = None,
        _pc_infer: PCInferCallable | None = None,
        _batch: tuple[Tensor, Tensor] | None = None,
    ) -> None:
        self.cell = cell
        self.device, self.dtype = _lane_device_dtype(cell.lane)
        self.model = (
            _build_seeded_model(cell.model_seed) if _model is None else _model
        ).to(device=self.device, dtype=self.dtype)
        self.optimizer = torch.optim.SGD(self.model.parameters(), lr=0.01)
        self.loss_fn = nn.CrossEntropyLoss()
        self.pc_infer = (
            load_pc_infer(torch2pc_dir) if _pc_infer is None else _pc_infer
        )
        inputs, targets = (
            _synthetic_batch(cell.model_seed) if _batch is None else _batch
        )
        self.inputs = inputs.to(device=self.device, dtype=self.dtype)
        self.targets = targets.to(device=self.device)
        self.inference_steps = len(self.model)
        self._active_state_sha256 = ""
        self._active_rng_sha256 = ""
        self._snapshot_step = -1
        self._beliefs: tuple[Tensor, ...] = ()
        self._errors: tuple[Tensor | None, ...] = ()
        self._fixed: tuple[Tensor, ...] = ()
        self._snapshot_cache: dict[ObservationLevel, ObservationCapture] = {}
        self._observation_digests: dict[ObservationLevel, list[str]] = {
            level: [] for level in ObservationLevel
        }
        self._observer_measurement = EdgeMeasurement()
        self._observer_effects = EffectAudit()
        self._previous_global_error: float | None = None
        self._action_completed = False
        self._oracle_created = False
        self._current_permissions = RuntimeValidationPermissionSet.deny_all()
        self._sample_index_cache: dict[tuple[str, int, int], tuple[int, ...]] = {}
        self._observed_snapshot_steps: list[int] = []

    def capture_initial_state(self) -> bytes:
        payload = {
            "model": self.model.state_dict(),
            "optimizer": self.optimizer.state_dict(),
        }
        buffer = io.BytesIO()
        torch.save(payload, buffer)
        return buffer.getvalue()

    def restore_initial_state(self, state: bytes) -> None:
        payload = torch.load(
            io.BytesIO(state),
            map_location=self.device,
            weights_only=False,
        )
        if not isinstance(payload, dict):
            raise TorchFixedPredBackendError("state snapshot is not a mapping")
        self.model.load_state_dict(payload["model"])
        self.optimizer.load_state_dict(payload["optimizer"])
        self.model.zero_grad(set_to_none=True)
        self._active_state_sha256 = _sha256_bytes(state)

    def capture_rng_state(self) -> bytes:
        payload: dict[str, object] = {
            "python": random.getstate(),
            "torch_cpu": torch.random.get_rng_state(),
            "torch_cuda": (
                torch.cuda.get_rng_state_all()
                if self.device.type == "cuda" and torch.cuda.is_available()
                else None
            ),
        }
        return pickle.dumps(payload, protocol=5)

    def restore_rng_state(self, state: bytes) -> None:
        payload = pickle.loads(state)  # noqa: S301 - trusted in-memory snapshot
        if not isinstance(payload, dict):
            raise TorchFixedPredBackendError("RNG snapshot is not a mapping")
        random.setstate(payload["python"])
        torch.random.set_rng_state(payload["torch_cpu"])
        cuda_states = payload["torch_cuda"]
        if cuda_states is not None:
            torch.cuda.set_rng_state_all(cuda_states)
        self._active_rng_sha256 = _sha256_bytes(state)

    def run_arm(
        self,
        cell: RuntimeCellSpec,
        arm_id: PairArmId,
        permissions: RuntimeValidationPermissionSet,
    ) -> RuntimeArmExecution:
        self._validate_cell(cell)
        permissions.require(
            Capability.EXECUTE_FIXEDPRED,
            Capability.COMPUTE_CANONICAL_SUFFIX,
            Capability.COMPUTE_POST_ACTION_ORACLE,
        )
        self._reset_arm(permissions)
        self.model.train()
        self.model.zero_grad(set_to_none=True)
        instrumented = arm_id is PairArmId.INSTRUMENTED

        if instrumented:
            with _instrument_fixedpred(self.pc_infer, self._capture_snapshot):
                output = self._execute_fixedpred()
        else:
            output = self._execute_fixedpred()
        if instrumented and self._observed_snapshot_steps != list(
            range(self.inference_steps + 1)
        ):
            raise TorchFixedPredBackendError(
                "instrumented FixedPred snapshot sequence differs"
            )
        self._action_completed = True
        values = _validate_pc_output(output)
        oracle = compute_post_action_oracle(permissions, self)
        if not oracle.isolation.passed:
            raise TorchFixedPredBackendError("post-action oracle isolation failed")

        equality_hashes = self._equality_hashes(values)
        observation_hashes: tuple[
            tuple[ObservationLevel, str], ...
        ] = ()
        if instrumented:
            observation_hashes = tuple(
                (level, _sha256_json(self._observation_digests[level]))
                for level in _levels_for_pair(cell.pair_id)
            )
            record_edge_costs(permissions, self)
        pair = next(
            item for item in PAIRED_VALIDATION_REGISTRY
            if item.pair_id is cell.pair_id
        )
        record = PairArmRecord(
            pair_id=cell.pair_id,
            arm_id=arm_id,
            arm_label=(pair.reference if not instrumented else pair.instrumented),
            lane=cell.lane,
            model_seed=cell.model_seed,
            batch_id=cell.batch_id,
            initial_state_sha256=self._active_state_sha256,
            rng_state_before_sha256=self._active_rng_sha256,
            equality_hashes=equality_hashes,
            observation_payload_sha256s=observation_hashes,
            observer_measurement=(
                self._observer_measurement if instrumented else EdgeMeasurement()
            ),
            observer_effects=(
                self._observer_effects if instrumented else EffectAudit()
            ),
        )
        disabled = tuple(
            DisabledCapabilityAudit(
                capability=capability,
                enabled=False,
                effects=EffectAudit(),
            )
            for capability in RUNTIME_EFFECT_AUDIT_CAPABILITIES
            if capability not in permissions.capabilities
        )
        return RuntimeArmExecution(
            record=record,
            oracle_isolation=oracle.isolation,
            disabled_capability_audits=disabled,
        )

    def collect_observation(self, level: ObservationLevel) -> ObservationCapture:
        if self._snapshot_step < 0:
            raise TorchFixedPredBackendError("no active FixedPred snapshot")
        cached = self._snapshot_cache.get(level)
        if cached is not None:
            return cached
        if level is ObservationLevel.A0:
            capture = self._collect_a0()
        elif level is ObservationLevel.A1:
            if ObservationLevel.A0 not in self._snapshot_cache:
                self._snapshot_cache[ObservationLevel.A0] = self._collect_a0()
            capture = self._collect_a1()
        else:
            if ObservationLevel.A1 not in self._snapshot_cache:
                if ObservationLevel.A0 not in self._snapshot_cache:
                    self._snapshot_cache[ObservationLevel.A0] = self._collect_a0()
                self._snapshot_cache[ObservationLevel.A1] = self._collect_a1()
            capture = self._collect_a2()
        self._snapshot_cache[level] = capture
        return capture

    def run_analytic(self, analytic_id: QWakeFPAnalyticId) -> AnalyticCapture:
        self._current_permissions.require(*_ANALYTIC_CAPABILITIES[analytic_id])
        started = time.perf_counter_ns()
        fields: tuple[tuple[str, object], ...]
        if analytic_id is QWakeFPAnalyticId.ROSENBAUM_WAVEFRONT_STATUS_V1:
            fields = (
                ("completed_component_prefix", self._snapshot_step),
                (
                    "next_structurally_unfinished_component",
                    min(self._snapshot_step + 1, self.inference_steps),
                ),
            )
        elif analytic_id is QWakeFPAnalyticId.RESIDUAL_PERSISTENCE_V1:
            current = self._global_prediction_error()
            previous = self._previous_global_error
            ratio = (
                None
                if previous is None or previous == 0.0
                else current / previous
            )
            fields = (
                ("current_residual", current),
                ("previous_residual", previous),
                ("residual_ratio", ratio),
                ("persistence_window", 1),
            )
            self._previous_global_error = current
        else:
            fields = (
                ("estimated_observer_cost_ns", self._observer_measurement.host_time_ns),
                ("estimated_remaining_suffix_cost_ns", 0),
                ("cost_dominance_status", "unresolved"),
            )
        measurement = EdgeMeasurement(
            host_time_ns=time.perf_counter_ns() - started,
            trace_bytes=len(_canonical_json(dict(fields)).encode("utf-8")),
        )
        return AnalyticCapture(
            analytic_id=analytic_id,
            fields=fields,
            measurement=measurement,
            effects=EffectAudit(
                invocation_count=1,
                output_count=len(fields),
                trace_bytes=measurement.trace_bytes,
            ),
        )

    def compute_post_action_oracle(self) -> OracleCapture:
        if not self._action_completed:
            raise TorchFixedPredBackendError("oracle requested before canonical action")
        if self._oracle_created:
            raise TorchFixedPredBackendError("oracle can be created only once")
        self._oracle_created = True
        fields: tuple[tuple[str, object], ...] = (
            ("canonical_action_completed", True),
            ("endpoint_state_available", True),
        )
        isolation = OracleIsolationRecord(
            pre_action_field_names=(
                OBSERVATION_REGISTRY[-1].cumulative_fields
            ),
            action_completed_ordinal=self.inference_steps + 1,
            oracle_created_ordinal=self.inference_steps + 2,
            oracle_read_before_action_count=0,
            pre_action_oracle_access_count=0,
        )
        encoded = _canonical_json(dict(fields)).encode("utf-8")
        return OracleCapture(
            fields=fields,
            isolation=isolation,
            measurement=EdgeMeasurement(trace_bytes=len(encoded)),
            effects=EffectAudit(
                invocation_count=1,
                trace_bytes=len(encoded),
                output_count=len(fields),
            ),
        )

    def record_edge_costs(self) -> EdgeMeasurement:
        return self._observer_measurement

    def _execute_fixedpred(self) -> tuple[Any, ...]:
        output = self.pc_infer(
            self.model,
            self.loss_fn,
            self.inputs.detach().clone(),
            self.targets.detach().clone(),
            "FixedPred",
            eta=_FIXEDPRED_ETA,
            n=self.inference_steps,
        )
        if not isinstance(output, tuple | list):
            raise TorchFixedPredBackendError("PCInfer returned a non-sequence")
        return tuple(output)

    def _capture_snapshot(
        self,
        step: int,
        beliefs: Sequence[Tensor],
        errors: Sequence[Tensor | None],
        fixed: Sequence[Tensor],
    ) -> None:
        self._snapshot_step = step
        self._observed_snapshot_steps.append(step)
        self._beliefs = tuple(beliefs)
        self._errors = tuple(errors)
        self._fixed = tuple(fixed)
        self._snapshot_cache = {}
        levels = _levels_for_pair(self.cell.pair_id)
        functions = {
            ObservationLevel.A0: collect_A0,
            ObservationLevel.A1: collect_A1,
            ObservationLevel.A2: collect_A2,
        }
        for level in levels:
            capture = functions[level](self._current_permissions, self)
            self._observation_digests[level].append(capture.payload_sha256())
            self._observer_measurement = _add_measurements(
                self._observer_measurement,
                capture.measurement,
            )
            self._observer_effects = _add_effects(
                self._observer_effects,
                capture.effects,
            )

    def _collect_a0(self) -> ObservationCapture:
        started = time.perf_counter_ns()
        fields: tuple[tuple[str, object], ...] = (
            ("snapshot_id", self._snapshot_id()),
            ("compute_step", self._snapshot_step),
            ("reference_horizon_k_ref", self.inference_steps),
            ("remaining_sweeps", self.inference_steps - self._snapshot_step),
            ("registered_layer_order", tuple(range(len(self.model)))),
            ("registered_block_order", tuple(range(len(self.model)))),
            ("acquired_analytic_ids", ()),
            ("diagnostic_budget_remaining_ns", 0),
        )
        measurement = EdgeMeasurement(
            host_time_ns=time.perf_counter_ns() - started,
            trace_bytes=len(_canonical_json(dict(fields)).encode("utf-8")),
        )
        return ObservationCapture(
            level=ObservationLevel.A0,
            fields=fields,
            measurement=measurement,
            effects=EffectAudit(
                invocation_count=1,
                trace_bytes=measurement.trace_bytes,
                output_count=len(fields),
            ),
        )

    def _collect_a1(self) -> ObservationCapture:
        base = self._snapshot_cache[ObservationLevel.A0]
        started, start_event = _measurement_start(self.device)
        prediction_errors = self._prediction_errors()
        state_deltas = tuple(
            fixed - belief
            for fixed, belief in zip(self._fixed, self._beliefs, strict=True)
        )
        scalar_tensors: list[Tensor] = []
        for values in (prediction_errors, state_deltas):
            scalar_tensors.extend(_l2_sq_tensor(value) for value in values)
        for values in (prediction_errors, state_deltas):
            scalar_tensors.extend(_max_abs_tensor(value) for value in values)
        transferred = torch.stack(scalar_tensors).detach().cpu()
        per_layer = len(prediction_errors)
        cursor = 0
        error_l2 = tuple(float(value) for value in transferred[cursor:cursor + per_layer])
        cursor += per_layer
        delta_l2 = tuple(float(value) for value in transferred[cursor:cursor + per_layer])
        cursor += per_layer
        error_max = tuple(float(value) for value in transferred[cursor:cursor + per_layer])
        cursor += per_layer
        delta_max = tuple(float(value) for value in transferred[cursor:cursor + per_layer])
        fields: tuple[tuple[str, object], ...] = base.fields + (
            ("global_prediction_error_l2_sq", sum(error_l2)),
            ("global_state_delta_l2_sq", sum(delta_l2)),
            ("per_layer_prediction_error_l2_sq", error_l2),
            ("per_layer_state_delta_l2_sq", delta_l2),
            ("per_layer_prediction_error_max_abs", error_max),
            ("per_layer_state_delta_max_abs", delta_max),
        )
        measurement = _measurement_finish(
            self.device,
            started,
            start_event,
            trace_bytes=len(_canonical_json(dict(fields)).encode("utf-8")),
            d2h_bytes=transferred.numel() * transferred.element_size(),
            temporary_memory_bytes=sum(
                value.numel() * value.element_size() for value in scalar_tensors
            ),
        )
        tensor_count = len(prediction_errors) + len(state_deltas)
        return ObservationCapture(
            level=ObservationLevel.A1,
            fields=fields,
            measurement=measurement,
            effects=EffectAudit(
                invocation_count=1,
                tensor_read_count=tensor_count,
                temporary_allocation_count=len(scalar_tensors) + 1,
                synchronization_count=measurement.synchronization_count,
                d2h_bytes=measurement.d2h_bytes,
                trace_bytes=measurement.trace_bytes,
                output_count=len(fields),
            ),
        )

    def _collect_a2(self) -> ObservationCapture:
        base = self._snapshot_cache[ObservationLevel.A1]
        started, start_event = _measurement_start(self.device)
        errors = self._prediction_errors()
        deltas = tuple(
            fixed - belief
            for fixed, belief in zip(self._fixed, self._beliefs, strict=True)
        )
        roles = (
            ("prediction_error", errors),
            ("state_delta", deltas),
            ("belief", self._beliefs),
        )
        labels: list[tuple[str, str, int, int]] = []
        scalars: list[Tensor] = []
        for role, tensors in roles:
            for prefix in (32, 128, 256):
                for layer, tensor in enumerate(tensors):
                    sample = self._sample(tensor, layer, role, prefix)
                    labels.append((role, "l2_sq", prefix, layer))
                    scalars.append(_l2_sq_tensor(sample))
                    labels.append((role, "max_abs", prefix, layer))
                    scalars.append(_max_abs_tensor(sample))
        transferred = torch.stack(scalars).detach().cpu()
        grouped: dict[str, dict[str, dict[str, list[float]]]] = {}
        for label, scalar in zip(labels, transferred, strict=True):
            role, statistic, prefix, _layer = label
            grouped.setdefault(role, {}).setdefault(statistic, {}).setdefault(
                str(prefix), []
            ).append(float(scalar))
        fields: tuple[tuple[str, object], ...] = base.fields + (
            (
                "sample_prefix_prediction_error_l2_sq",
                grouped["prediction_error"]["l2_sq"],
            ),
            ("sample_prefix_state_delta_l2_sq", grouped["state_delta"]["l2_sq"]),
            ("sample_prefix_belief_l2_sq", grouped["belief"]["l2_sq"]),
            (
                "sample_prefix_prediction_error_max_abs",
                grouped["prediction_error"]["max_abs"],
            ),
            (
                "sample_prefix_state_delta_max_abs",
                grouped["state_delta"]["max_abs"],
            ),
            ("sample_prefix_belief_max_abs", grouped["belief"]["max_abs"]),
        )
        measurement = _measurement_finish(
            self.device,
            started,
            start_event,
            trace_bytes=len(_canonical_json(dict(fields)).encode("utf-8")),
            d2h_bytes=transferred.numel() * transferred.element_size(),
            temporary_memory_bytes=sum(
                value.numel() * value.element_size() for value in scalars
            ),
        )
        tensor_count = len(labels) // 2
        return ObservationCapture(
            level=ObservationLevel.A2,
            fields=fields,
            measurement=measurement,
            effects=EffectAudit(
                invocation_count=1,
                tensor_read_count=tensor_count,
                temporary_allocation_count=len(scalars) + 1,
                synchronization_count=measurement.synchronization_count,
                d2h_bytes=measurement.d2h_bytes,
                trace_bytes=measurement.trace_bytes,
                output_count=len(fields),
            ),
        )

    def _prediction_errors(self) -> tuple[Tensor, ...]:
        values: list[Tensor] = []
        for layer, error in enumerate(self._errors):
            if error is None:
                values.append(torch.zeros_like(self._beliefs[layer]))
            else:
                values.append(error)
        return tuple(values)

    def _global_prediction_error(self) -> float:
        return sum(_l2_sq(value) for value in self._prediction_errors())

    def _sample(self, tensor: Tensor, layer: int, role: str, prefix: int) -> Tensor:
        flat = tensor.detach().reshape(-1)
        count = min(prefix, flat.numel())
        key = (f"{layer}:{role}", flat.numel(), count)
        indices = self._sample_index_cache.get(key)
        if indices is None:
            ranked = sorted(
                range(flat.numel()),
                key=lambda index: hashlib.sha256(
                    (
                        "stage3b-qwake-fp-special-case-v1|"
                        f"{self.cell.model_seed}|{self.cell.batch_id}|"
                        f"{layer}|{role}|{index}"
                    ).encode()
                ).digest(),
            )
            indices = tuple(ranked[:count])
            self._sample_index_cache[key] = indices
        index_tensor = torch.tensor(indices, device=flat.device, dtype=torch.long)
        return flat.index_select(0, index_tensor)

    def _equality_hashes(self, output: tuple[Any, ...]) -> tuple[tuple[str, str], ...]:
        _vhat, loss, _dldy, beliefs, _errors = output
        if not isinstance(loss, Tensor):
            raise TorchFixedPredBackendError("PCInfer loss is not a tensor")
        gradients: dict[str, Tensor] = {}
        for name, parameter in self.model.named_parameters():
            gradient = parameter.grad
            if gradient is None:
                raise TorchFixedPredBackendError(
                    "PCInfer left a parameter gradient unset"
                )
            gradients[name] = gradient
        gradient_hash = _sha256_tensors(gradients)
        belief_hash = _sha256_sequence(cast(Sequence[Tensor], beliefs))
        loss_hash = _sha256_tensors({"loss": loss})
        endpoint_hash = _sha256_json(
            {
                "gradients": gradient_hash,
                "beliefs": belief_hash,
                "loss": loss_hash,
            }
        )
        transition = tuple(self._snapshot_id(step) for step in range(self.inference_steps + 1))
        rng_after = _rng_state_sha256(self.device)
        snapshot_identity = _sha256_json(transition)
        fields = {
            "canonical_endpoint_response": endpoint_hash,
            "named_parameter_gradients": gradient_hash,
            "endpoint_beliefs": belief_hash,
            "endpoint_loss": loss_hash,
            "transition_sequence": _sha256_json(transition),
            "rng_state_after": rng_after,
            "snapshot_identity": snapshot_identity,
        }
        required = PAIRED_VALIDATION_REGISTRY[0].required_equalities
        return tuple((name, fields[name]) for name in required)

    def _snapshot_id(self, step: int | None = None) -> str:
        value = self._snapshot_step if step is None else step
        return (
            f"{self.cell.lane.value}:seed-{self.cell.model_seed}:"
            f"{self.cell.batch_id}:snapshot-{value}"
        )

    def _reset_arm(self, permissions: RuntimeValidationPermissionSet) -> None:
        self._current_permissions = permissions
        self._snapshot_step = -1
        self._beliefs = ()
        self._errors = ()
        self._fixed = ()
        self._snapshot_cache = {}
        self._observation_digests = {level: [] for level in ObservationLevel}
        self._observer_measurement = EdgeMeasurement()
        self._observer_effects = EffectAudit()
        self._previous_global_error = None
        self._action_completed = False
        self._oracle_created = False
        self._observed_snapshot_steps = []

    def _validate_cell(self, cell: RuntimeCellSpec) -> None:
        if cell != self.cell:
            raise TorchFixedPredBackendError("backend received a foreign cell")
        if cell.batch_id != RUNTIME_ENGINEERING_BATCH_ID:
            raise TorchFixedPredBackendError("engineering batch id differs")


def _validate_pc_output(output: tuple[Any, ...]) -> tuple[Any, ...]:
    if len(output) != 5:
        raise TorchFixedPredBackendError("PCInfer must return five values")
    vhat, loss, dldy, beliefs, errors = output
    if not isinstance(loss, Tensor) or loss.ndim != 0:
        raise TorchFixedPredBackendError("PCInfer loss must be scalar")
    if not bool(torch.isfinite(loss).item()):
        raise TorchFixedPredBackendError("PCInfer loss is non-finite")
    for name, values in (("vhat", vhat), ("beliefs", beliefs), ("errors", errors)):
        if not isinstance(values, tuple | list) or not values:
            raise TorchFixedPredBackendError(f"PCInfer {name} is invalid")
        for value in values:
            if value is not None and (
                not isinstance(value, Tensor)
                or not bool(torch.isfinite(value).all().item())
            ):
                raise TorchFixedPredBackendError(f"PCInfer {name} is non-finite")
    if not isinstance(dldy, Tensor) or not bool(torch.isfinite(dldy).all().item()):
        raise TorchFixedPredBackendError("PCInfer dLdy is invalid")
    return output


def _lane_device_dtype(lane: ValidationLane) -> tuple[torch.device, torch.dtype]:
    if lane is ValidationLane.CPU_FLOAT64_ENGINEERING:
        return torch.device("cpu"), torch.float64
    if not torch.cuda.is_available() or not str(torch.version.hip or ""):
        raise TorchFixedPredBackendError("ROCm canonical lane is unavailable")
    return torch.device("cuda:0"), torch.float32



def _build_seeded_model(seed: int) -> nn.Sequential:
    state = torch.random.get_rng_state()
    try:
        torch.manual_seed(seed)
        return build_model("lenet_classic")
    finally:
        torch.random.set_rng_state(state)

def _synthetic_batch(seed: int) -> tuple[Tensor, Tensor]:
    generator = torch.Generator(device="cpu")
    generator.manual_seed(seed + 17_042)
    inputs = torch.randn(
        (_SYNTHETIC_BATCH_SIZE, *_SYNTHETIC_IMAGE_SHAPE),
        generator=generator,
        dtype=torch.float64,
    )
    targets = torch.randint(
        0,
        10,
        (_SYNTHETIC_BATCH_SIZE,),
        generator=generator,
    )
    return inputs, targets


def _levels_for_pair(pair_id: QWakeFPPairId) -> tuple[ObservationLevel, ...]:
    return {
        QWakeFPPairId.P0: (ObservationLevel.A0,),
        QWakeFPPairId.P1: (ObservationLevel.A0, ObservationLevel.A1),
        QWakeFPPairId.P2: tuple(ObservationLevel),
    }[pair_id]


def _measurement_start(
    device: torch.device,
) -> tuple[int, tuple[torch.cuda.Event, torch.cuda.Event] | None]:
    events: tuple[torch.cuda.Event, torch.cuda.Event] | None = None
    if device.type == "cuda":
        torch.cuda.synchronize(device)
        start = torch.cuda.Event(enable_timing=True)
        end = torch.cuda.Event(enable_timing=True)
        start.record()
        events = start, end
    return time.perf_counter_ns(), events


def _measurement_finish(
    device: torch.device,
    started_ns: int,
    events: tuple[torch.cuda.Event, torch.cuda.Event] | None,
    *,
    trace_bytes: int,
    d2h_bytes: int,
    temporary_memory_bytes: int,
) -> EdgeMeasurement:
    device_time_ns = 0
    synchronization_count = 0
    if events is not None:
        start, end = events
        end.record()
        torch.cuda.synchronize(device)
        synchronization_count = 2
        device_time_ns = int(start.elapsed_time(end) * 1_000_000)
    return EdgeMeasurement(
        host_time_ns=time.perf_counter_ns() - started_ns,
        device_time_ns=device_time_ns,
        synchronization_count=synchronization_count,
        d2h_bytes=d2h_bytes,
        temporary_memory_bytes=temporary_memory_bytes,
        trace_bytes=trace_bytes,
    )


def _l2_sq_tensor(value: Tensor) -> Tensor:
    detached = value.detach()
    return torch.sum(detached * detached)


def _max_abs_tensor(value: Tensor) -> Tensor:
    if value.numel() == 0:
        return torch.zeros((), device=value.device, dtype=value.dtype)
    return torch.max(torch.abs(value.detach()))


def _l2_sq(value: Tensor) -> float:
    return float(_l2_sq_tensor(value).item())


def _max_abs(value: Tensor) -> float:
    return float(_max_abs_tensor(value).item())


def _add_measurements(
    left: EdgeMeasurement,
    right: EdgeMeasurement,
) -> EdgeMeasurement:
    return EdgeMeasurement(
        host_time_ns=left.host_time_ns + right.host_time_ns,
        device_time_ns=left.device_time_ns + right.device_time_ns,
        synchronization_count=(
            left.synchronization_count + right.synchronization_count
        ),
        d2h_bytes=left.d2h_bytes + right.d2h_bytes,
        temporary_memory_bytes=(
            left.temporary_memory_bytes + right.temporary_memory_bytes
        ),
        trace_bytes=left.trace_bytes + right.trace_bytes,
    )


def _add_effects(left: EffectAudit, right: EffectAudit) -> EffectAudit:
    return EffectAudit(
        invocation_count=left.invocation_count + right.invocation_count,
        tensor_read_count=left.tensor_read_count + right.tensor_read_count,
        temporary_allocation_count=(
            left.temporary_allocation_count + right.temporary_allocation_count
        ),
        synchronization_count=(
            left.synchronization_count + right.synchronization_count
        ),
        d2h_bytes=left.d2h_bytes + right.d2h_bytes,
        trace_bytes=left.trace_bytes + right.trace_bytes,
        output_count=left.output_count + right.output_count,
    )


def _rng_state_sha256(device: torch.device) -> str:
    digest = hashlib.sha256()
    digest.update(repr(random.getstate()).encode("utf-8"))
    digest.update(torch.random.get_rng_state().cpu().numpy().tobytes())
    if device.type == "cuda" and torch.cuda.is_available():
        for state in torch.cuda.get_rng_state_all():
            digest.update(state.cpu().numpy().tobytes())
    return f"sha256:{digest.hexdigest()}"

def _sha256_tensors(values: Mapping[str, Tensor]) -> str:
    digest = hashlib.sha256()
    for name in sorted(values):
        tensor = values[name].detach().cpu().contiguous()
        digest.update(name.encode("utf-8"))
        digest.update(str(tensor.dtype).encode("ascii"))
        digest.update(json.dumps(tuple(tensor.shape)).encode("ascii"))
        digest.update(tensor.numpy().tobytes())
    return f"sha256:{digest.hexdigest()}"


def _sha256_sequence(values: Sequence[Tensor]) -> str:
    return _sha256_tensors({str(index): value for index, value in enumerate(values)})


def _sha256_bytes(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def _sha256_json(value: object) -> str:
    return f"sha256:{hashlib.sha256(_canonical_json(value).encode('utf-8')).hexdigest()}"


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
