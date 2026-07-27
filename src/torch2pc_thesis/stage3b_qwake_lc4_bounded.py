"""Bounded QW-LC4-I implementation for the FixedPred eta=1 special case.

The module materializes the registered analytic-completion mechanism and the
controls needed to test it on synthetic unit-test states.  It intentionally
provides no CLI, no dataset loader, no runtime authorization reader, no output
writer, and no scientific executor.  Any later engineering or scientific run
must be opened by a separate frozen QW-LC4-F authorization.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import pickle
import random
import sys
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from enum import StrEnum
from typing import Final

import numpy as np
import torch
from torch import Tensor, nn

LC4_IMPLEMENTATION_ID: Final = (
    "stage3b-qwake-lc4-i-bounded-implementation-v1"
)
LC3_CONTRACT_ID: Final = (
    "stage3b-qwake-lc3-matched-shadow-validation-contract-v1"
)
LC1_RESPONSE_SCHEMA_ID: Final = (
    "stage3b-qwake-lc1-required-response-schema-v1"
)
LC2_COST_SCHEMA_ID: Final = "stage3b-qwake-cost-vector-v1"
ANALYTIC_ACTION_ID: Final = "fixedpred_eta1_wavefront_completion_v1"
EXACT_REFERENCE_ACTION_ID: Final = "complete_suffix_stage2_baseline_v1"
OPAQUE_STATE_SCHEMA_ID: Final = "stage3b-qwake-opaque-state-v1"
RNG_SNAPSHOT_ID: Final = "stage3b-qwake-rng-snapshot-v1"
PAIR_COUNT: Final = 12

__all__ = [
    "ANALYTIC_ACTION_ID",
    "EXACT_REFERENCE_ACTION_ID",
    "LC4_IMPLEMENTATION_ID",
    "PAIR_COUNT",
    "ArtifactRecord",
    "BoundedArm",
    "BoundedUnitTestAuthorization",
    "CanonicalResponse",
    "CompletionResult",
    "CostField",
    "CostPair",
    "CostVector",
    "FallbackRecord",
    "FieldSummary",
    "FixedPredFrontier",
    "IntervalOwner",
    "IntervalRecord",
    "MatchedPairResult",
    "MemoryRecord",
    "ObserverCalibration",
    "OpaqueStateSnapshot",
    "PairedCostAggregation",
    "QWakeLC4BoundedError",
    "RNGSnapshot",
    "RegisteredDomain",
    "ReserveProbeResult",
    "ResourceTrajectory",
    "ResponseComparison",
    "aggregate_paired_costs",
    "analytic_wavefront_completion",
    "capture_fixedpred_frontier",
    "capture_opaque_state",
    "capture_rng_snapshot",
    "compare_required_responses",
    "complete_exact_suffix",
    "map_resource_trajectory",
    "materialize_required_response",
    "pair_schedule",
    "preserve_outer_rng",
    "restore_rng_snapshot",
    "run_synthetic_matched_pair",
    "run_synthetic_reserve_probe",
]

type Scalar = str | int | float | bool | None


class QWakeLC4BoundedError(RuntimeError):
    """Raised when a bounded implementation invariant fails closed."""


class BoundedArm(StrEnum):
    """The two registered matched-shadow arms."""

    EXACT_REFERENCE = "exact_reference"
    ANALYTIC_CANDIDATE = "analytic_candidate"


@dataclass(frozen=True)
class RegisteredDomain:
    """Exact domain admitted by the QW-LC3 contract."""

    method: str = "fixedpred"
    eta: float = 1.0
    architecture: str = "lenet_classic"
    executor: str = "stage2_baseline"
    decision_epoch: str = "after_S_t_before_sweep_t_plus_1"

    def __post_init__(self) -> None:
        if self.method != "fixedpred":
            raise QWakeLC4BoundedError("QW-LC4-I admits FixedPred only")
        if self.eta != 1.0:
            raise QWakeLC4BoundedError("QW-LC4-I requires eta=1")
        if self.architecture != "lenet_classic":
            raise QWakeLC4BoundedError("QW-LC4-I requires lenet_classic")
        if self.executor != "stage2_baseline":
            raise QWakeLC4BoundedError("QW-LC4-I requires stage2_baseline")
        if self.decision_epoch != "after_S_t_before_sweep_t_plus_1":
            raise QWakeLC4BoundedError("unexpected decision epoch")


@dataclass(frozen=True)
class FixedPredFrontier:
    """One FixedPred state captured after S_t and before sweep t+1."""

    fixed: tuple[Tensor, ...]
    beliefs: tuple[Tensor, ...]
    errors: tuple[Tensor | None, ...]
    endpoint_loss: Tensor
    candidate_index: int

    def clone(self) -> FixedPredFrontier:
        return FixedPredFrontier(
            fixed=tuple(item.detach().clone() for item in self.fixed),
            beliefs=tuple(item.detach().clone() for item in self.beliefs),
            errors=tuple(
                None if item is None else item.detach().clone()
                for item in self.errors
            ),
            endpoint_loss=self.endpoint_loss.detach().clone(),
            candidate_index=self.candidate_index,
        )


@dataclass(frozen=True)
class TensorEntry:
    """One canonical response entry and its in-memory payload."""

    component_id: str
    entry_key: str
    entry_position: int
    shape: tuple[int, ...]
    source_dtype: str
    numel: int
    finite: bool
    payload_sha256: str
    tensor: Tensor


@dataclass(frozen=True)
class CanonicalResponse:
    """The QW-LC1 response materialized for one arm."""

    response_schema_id: str
    state_id: str
    comparison_profile_id: str
    component_order: tuple[str, ...]
    entries: tuple[TensorEntry, ...]
    component_manifest_sha256: str
    canonical_response_sha256: str
    all_entries_finite: bool


@dataclass(frozen=True)
class EntryComparison:
    """One symmetric zero-safe QW-LC1 entry comparison."""

    component_id: str
    entry_key: str
    reference_l2: float
    candidate_l2: float
    difference_l2: float
    relative_l2: float
    max_abs: float
    cosine: float | None
    zero_case: str
    finite: bool
    defect: float
    passed: bool


@dataclass(frozen=True)
class ResponseComparison:
    """Complete QW-LC1 response-equivalence result."""

    predicate_id: str
    structural_equal: bool
    entry_results: tuple[EntryComparison, ...]
    response_defect: float
    passed: bool


class IntervalOwner(StrEnum):
    """Exclusive LC2 interval owners."""

    CORE_COMPUTE = "core_compute"
    DIAGNOSTIC = "diagnostic_mechanism"
    OBSERVER = "observer"
    CONTROL = "control_plane"
    FALLBACK = "fallback"


@dataclass(frozen=True)
class IntervalRecord:
    """One complete resource-trajectory interval."""

    position: int
    owner: IntervalOwner
    lane: str
    clock_domain: str
    start_ns: int
    end_ns: int
    source: str
    complete: bool = True


@dataclass(frozen=True)
class MemoryRecord:
    """One complete peak-memory record."""

    metric: str
    value_bytes: int
    source: str
    complete: bool = True


@dataclass(frozen=True)
class ArtifactRecord:
    """One diagnostic or observer artifact record."""

    position: int
    owner: IntervalOwner
    sha256: str
    size_bytes: int
    source: str


@dataclass(frozen=True)
class ObserverCalibration:
    """Matched control/instrumented latency calibration."""

    pair_id: str
    instrumented_latency_ns: int
    control_latency_ns: int
    raw_residual_ns: int
    overclosure: bool
    complete: bool = True


@dataclass(frozen=True)
class FallbackRecord:
    """Exact-reserve availability and invocation state."""

    fallback_available: bool
    fallback_invoked: bool
    fallback_completed: bool


@dataclass(frozen=True)
class ResourceTrajectory:
    """Complete LC2 trajectory accepted by the bounded mapper."""

    trajectory_schema_id: str
    action_id: str
    mechanism_id: str
    opaque_state_ref: str
    repeat_index: int
    lane_profile_id: str
    cost_profile_id: str
    root_clock_domain: str
    root_start_ns: int
    root_end_ns: int
    intervals: tuple[IntervalRecord, ...]
    memory: tuple[MemoryRecord, ...]
    artifacts: tuple[ArtifactRecord, ...]
    observer_calibration: ObserverCalibration | None
    fallback: FallbackRecord


@dataclass(frozen=True)
class CostField:
    """One active or explicitly inactive LC2 numeric field."""

    status: str
    value: int | None


@dataclass(frozen=True)
class CostVector:
    """Non-scalarized QW-LC2 cost vector."""

    cost_schema_id: str
    action_id: str
    opaque_state_ref: str
    repeat_index: int
    lane_profile_id: str
    cost_profile_id: str
    fields: tuple[tuple[str, CostField], ...]
    fallback_invoked: bool

    def active_values(self) -> Mapping[str, int]:
        return {
            name: field.value
            for name, field in self.fields
            if field.status == "measured" and field.value is not None
        }


@dataclass(frozen=True)
class CostPair:
    """One complete matched cost pair."""

    repeat_index: int
    arm_order: tuple[BoundedArm, BoundedArm]
    exact_reference: CostVector
    analytic_candidate: CostVector


@dataclass(frozen=True)
class FieldSummary:
    """Frozen five-number paired-delta summary."""

    median_paired_delta: float
    q1_paired_delta: float
    q3_paired_delta: float
    minimum_paired_delta: int
    maximum_paired_delta: int


@dataclass(frozen=True)
class PairedCostAggregation:
    """Componentwise LC3 paired aggregation without scalarization."""

    aggregate_id: str
    field_summaries: tuple[tuple[str, FieldSummary], ...]
    order_effect_passed: bool
    pair_complete: bool


@dataclass(frozen=True)
class RNGRecord:
    """One ordered RNG-state record."""

    generator_id: str
    state_encoding: str
    state_bytes: bytes
    state_sha256: str


@dataclass(frozen=True)
class RNGSnapshot:
    """Complete default and explicitly registered RNG inventory."""

    snapshot_id: str
    records: tuple[RNGRecord, ...]
    snapshot_sha256: str


@dataclass(frozen=True)
class BoundedUnitTestAuthorization:
    """Synthetic-only authorization; it can never open a research run."""

    authorization_id: str
    synthetic_unit_test_only: bool
    scientific_execution_open: bool
    test_dataset_access: bool
    publication_permitted: bool

    @classmethod
    def issue(cls) -> BoundedUnitTestAuthorization:
        return cls(
            authorization_id="stage3b-qwake-lc4-i-synthetic-unit-test-v1",
            synthetic_unit_test_only=True,
            scientific_execution_open=False,
            test_dataset_access=False,
            publication_permitted=False,
        )

    def require(self) -> None:
        if self.authorization_id != (
            "stage3b-qwake-lc4-i-synthetic-unit-test-v1"
        ):
            raise QWakeLC4BoundedError("unexpected unit-test authorization")
        if not self.synthetic_unit_test_only:
            raise QWakeLC4BoundedError("authorization is not synthetic-only")
        if any(
            (
                self.scientific_execution_open,
                self.test_dataset_access,
                self.publication_permitted,
            )
        ):
            raise QWakeLC4BoundedError(
                "unit-test authorization cannot open scientific capabilities"
            )


@dataclass(frozen=True)
class OpaqueStateSnapshot:
    """Immutable in-memory source state bound by opaque_state_ref."""

    domain: RegisteredDomain
    lane_profile_id: str
    comparison_profile_id: str
    cost_profile_id: str
    input_batch: Tensor
    target_batch: Tensor
    frontier: FixedPredFrontier
    runtime_controls: tuple[tuple[str, Scalar], ...]
    optional_update_state: Mapping[str, object] | None
    opaque_state_ref: str
    _model_template: nn.Sequential

    def verify_integrity(self) -> None:
        observed_manifest = _build_state_manifest(
            self._model_template,
            self.input_batch,
            self.target_batch,
            self.frontier,
            domain=self.domain,
            lane_profile_id=self.lane_profile_id,
            comparison_profile_id=self.comparison_profile_id,
            runtime_controls=self.runtime_controls,
            optional_update_state=self.optional_update_state,
        )
        observed = _opaque_state_ref(observed_manifest)
        if observed != self.opaque_state_ref:
            raise QWakeLC4BoundedError("opaque source snapshot was mutated")

    def fork(self) -> tuple[nn.Sequential, FixedPredFrontier]:
        self.verify_integrity()
        model = copy.deepcopy(self._model_template)
        return model, self.frontier.clone()


@dataclass(frozen=True)
class CompletionResult:
    """One bounded mechanism result before response comparison."""

    action_id: str
    frontier: FixedPredFrontier
    vjp_count: int
    fallback_invoked: bool


@dataclass(frozen=True)
class BoundedArmResult:
    """One synthetic matched arm result."""

    arm: BoundedArm
    response: CanonicalResponse
    rng_before_sha256: str
    rng_after_sha256: str
    vjp_count: int
    fallback_invoked: bool


@dataclass(frozen=True)
class MatchedPairResult:
    """One synthetic pair used only to verify implementation behavior."""

    repeat_index: int
    arm_order: tuple[BoundedArm, BoundedArm]
    exact_reference: BoundedArmResult
    analytic_candidate: BoundedArmResult
    response_comparison: ResponseComparison
    rng_post_match: bool

    @property
    def passed(self) -> bool:
        return (
            self.response_comparison.passed
            and self.rng_post_match
            and not self.exact_reference.fallback_invoked
            and not self.analytic_candidate.fallback_invoked
        )


@dataclass(frozen=True)
class ReserveProbeResult:
    """Forced exact-reserve probe isolated from normal-arm aggregation."""

    completed_suffix_indices: tuple[int, ...]
    no_skipped_indices: bool
    no_duplicate_indices: bool
    fallback_available: bool
    fallback_invoked: bool
    fallback_completed: bool
    fallback_response_sha256: str
    direct_reference_response_sha256: str
    rng_post_sha256: str

    @property
    def passed(self) -> bool:
        return (
            self.no_skipped_indices
            and self.no_duplicate_indices
            and self.fallback_available
            and self.fallback_invoked
            and self.fallback_completed
            and self.fallback_response_sha256
            == self.direct_reference_response_sha256
        )


def capture_fixedpred_frontier(
    model: nn.Sequential,
    loss_fn: nn.Module,
    inputs: Tensor,
    targets: Tensor,
    *,
    candidate_index: int,
) -> FixedPredFrontier:
    """Construct a decision-epoch frontier without loading any dataset."""

    _require_sequential(model)
    depth = len(model)
    if not 0 <= candidate_index <= depth:
        raise QWakeLC4BoundedError("candidate_index is outside [0,K_ref]")
    activations = [inputs]
    for layer in model:
        activations.append(layer(activations[-1]))
    endpoint_loss = loss_fn(activations[-1], targets)
    if endpoint_loss.ndim != 0 or not bool(torch.isfinite(endpoint_loss)):
        raise QWakeLC4BoundedError("endpoint loss must be a finite scalar")
    dldy = torch.autograd.grad(endpoint_loss, activations[-1])[0]
    fixed = tuple(item.detach() for item in activations)
    beliefs = [item.detach().clone() for item in fixed]
    errors: list[Tensor | None] = [None] * (depth + 1)
    errors[-1] = dldy.detach().clone()
    beliefs, errors = _run_fixedpred_sweeps(
        model,
        fixed,
        beliefs,
        errors,
        sweep_count=candidate_index,
    )
    frontier = FixedPredFrontier(
        fixed=tuple(item.detach().clone() for item in fixed),
        beliefs=tuple(item.detach().clone() for item in beliefs),
        errors=tuple(
            None if item is None else item.detach().clone()
            for item in errors
        ),
        endpoint_loss=endpoint_loss.detach().clone(),
        candidate_index=candidate_index,
    )
    _validate_frontier(model, frontier)
    return frontier


def capture_opaque_state(
    model: nn.Sequential,
    inputs: Tensor,
    targets: Tensor,
    frontier: FixedPredFrontier,
    *,
    domain: RegisteredDomain | None = None,
    lane_profile_id: str,
    comparison_profile_id: str,
    cost_profile_id: str,
    runtime_controls: Mapping[str, Scalar],
    optional_update_state: Mapping[str, object] | None = None,
) -> OpaqueStateSnapshot:
    """Capture and hash every registered state group without side effects."""

    _require_sequential(model)
    _validate_frontier(model, frontier)
    for name, value in (
        ("lane_profile_id", lane_profile_id),
        ("comparison_profile_id", comparison_profile_id),
        ("cost_profile_id", cost_profile_id),
    ):
        if not value.strip():
            raise QWakeLC4BoundedError(f"{name} cannot be empty")
    resolved_domain = RegisteredDomain() if domain is None else domain
    controls = tuple(sorted(runtime_controls.items()))
    model_template = copy.deepcopy(model)
    input_copy = inputs.detach().clone()
    target_copy = targets.detach().clone()
    frontier_copy = frontier.clone()
    manifest = _build_state_manifest(
        model_template,
        input_copy,
        target_copy,
        frontier_copy,
        domain=resolved_domain,
        lane_profile_id=lane_profile_id,
        comparison_profile_id=comparison_profile_id,
        runtime_controls=controls,
        optional_update_state=optional_update_state,
    )
    opaque_ref = _opaque_state_ref(manifest)
    return OpaqueStateSnapshot(
        domain=resolved_domain,
        lane_profile_id=lane_profile_id,
        comparison_profile_id=comparison_profile_id,
        cost_profile_id=cost_profile_id,
        input_batch=input_copy,
        target_batch=target_copy,
        frontier=frontier_copy,
        runtime_controls=controls,
        optional_update_state=copy.deepcopy(optional_update_state),
        opaque_state_ref=opaque_ref,
        _model_template=model_template,
    )


def analytic_wavefront_completion(
    model: nn.Sequential,
    frontier: FixedPredFrontier,
) -> CompletionResult:
    """Complete the unfinished eta=1 FixedPred wavefront in one reverse pass."""

    _validate_frontier(model, frontier)
    depth = len(model)
    candidate_index = frontier.candidate_index
    beliefs = [item.detach().clone() for item in frontier.beliefs]
    errors = [
        None if item is None else item.detach().clone()
        for item in frontier.errors
    ]
    fixed = tuple(item.detach() for item in frontier.fixed)

    if candidate_index == 0:
        upper = errors[-1]
        if upper is None:
            raise QWakeLC4BoundedError("output error is absent")
        first_unfinished_layer = depth - 1
    else:
        boundary = depth - candidate_index
        upper = fixed[boundary] - beliefs[boundary]
        if not bool(torch.isfinite(upper).all()):
            raise QWakeLC4BoundedError("boundary residual is non-finite")
        errors[boundary] = upper.detach().clone()
        _validate_completed_upper_wavefront(
            fixed,
            beliefs,
            errors,
            boundary=boundary,
        )
        first_unfinished_layer = boundary - 1

    vjp_count = 0
    for layer_index in range(first_unfinished_layer, -1, -1):
        linear_input = fixed[layer_index].detach().requires_grad_(True)
        linear_output = model[layer_index](linear_input)
        propagated = torch.autograd.grad(
            linear_output,
            linear_input,
            grad_outputs=upper,
            retain_graph=False,
        )[0].detach()
        if not bool(torch.isfinite(propagated).all()):
            raise QWakeLC4BoundedError("analytic VJP is non-finite")
        errors[layer_index] = propagated
        beliefs[layer_index] = fixed[layer_index] - propagated
        upper = propagated
        vjp_count += 1

    result_frontier = FixedPredFrontier(
        fixed=tuple(item.detach().clone() for item in fixed),
        beliefs=tuple(item.detach().clone() for item in beliefs),
        errors=tuple(
            None if item is None else item.detach().clone()
            for item in errors
        ),
        endpoint_loss=frontier.endpoint_loss.detach().clone(),
        candidate_index=depth,
    )
    _validate_final_frontier(model, result_frontier)
    return CompletionResult(
        action_id=ANALYTIC_ACTION_ID,
        frontier=result_frontier,
        vjp_count=vjp_count,
        fallback_invoked=False,
    )


def complete_exact_suffix(
    model: nn.Sequential,
    frontier: FixedPredFrontier,
    *,
    fallback_invoked: bool = False,
) -> CompletionResult:
    """Execute every remaining registered FixedPred sweep exactly."""

    _validate_frontier(model, frontier)
    remaining = len(model) - frontier.candidate_index
    beliefs = [item.detach().clone() for item in frontier.beliefs]
    errors = [
        None if item is None else item.detach().clone()
        for item in frontier.errors
    ]
    beliefs, errors = _run_fixedpred_sweeps(
        model,
        frontier.fixed,
        beliefs,
        errors,
        sweep_count=remaining,
    )
    result_frontier = FixedPredFrontier(
        fixed=tuple(item.detach().clone() for item in frontier.fixed),
        beliefs=tuple(item.detach().clone() for item in beliefs),
        errors=tuple(
            None if item is None else item.detach().clone()
            for item in errors
        ),
        endpoint_loss=frontier.endpoint_loss.detach().clone(),
        candidate_index=len(model),
    )
    _validate_final_frontier(model, result_frontier)
    return CompletionResult(
        action_id=EXACT_REFERENCE_ACTION_ID,
        frontier=result_frontier,
        vjp_count=len(model) * remaining,
        fallback_invoked=fallback_invoked,
    )


def materialize_required_response(
    model: nn.Sequential,
    completion: CompletionResult,
    *,
    state_id: str,
    comparison_profile_id: str,
) -> CanonicalResponse:
    """Materialize gradients, endpoint beliefs, and endpoint loss."""

    _require_sha256(state_id, field_name="state_id")
    if not comparison_profile_id.strip():
        raise QWakeLC4BoundedError("comparison_profile_id cannot be empty")
    frontier = completion.frontier
    _validate_final_frontier(model, frontier)
    entries: list[TensorEntry] = []
    parameter_position = 0
    for layer_index, module in enumerate(model):
        named_parameters = tuple(module.named_parameters(recurse=True))
        if not named_parameters:
            continue
        upper = frontier.errors[layer_index + 1]
        if upper is None:
            raise QWakeLC4BoundedError("parameter-gradient error is absent")
        linear_input = frontier.fixed[layer_index].detach()
        linear_output = module(linear_input)
        gradients = torch.autograd.grad(
            linear_output,
            tuple(parameter for _, parameter in named_parameters),
            grad_outputs=upper,
            allow_unused=False,
        )
        for (local_name, _parameter), gradient in zip(
            named_parameters,
            gradients,
            strict=True,
        ):
            entries.append(
                _response_entry(
                    "named_parameter_gradients",
                    f"{layer_index}.{local_name}",
                    parameter_position,
                    gradient,
                )
            )
            parameter_position += 1
    for position, belief in enumerate(frontier.beliefs):
        entries.append(
            _response_entry(
                "endpoint_beliefs",
                str(position),
                position,
                belief,
            )
        )
    entries.append(
        _response_entry(
            "endpoint_loss",
            "loss",
            0,
            frontier.endpoint_loss,
        )
    )
    component_order = (
        "named_parameter_gradients",
        "endpoint_beliefs",
        "endpoint_loss",
    )
    manifest_entries = tuple(_entry_manifest(item) for item in entries)
    component_manifest_sha256 = _sha256_json(manifest_entries)
    response_manifest = {
        "response_schema_id": LC1_RESPONSE_SCHEMA_ID,
        "state_id": state_id,
        "comparison_profile_id": comparison_profile_id,
        "component_order": component_order,
        "component_manifest_sha256": component_manifest_sha256,
        "entries": manifest_entries,
        "all_entries_finite": all(item.finite for item in entries),
    }
    return CanonicalResponse(
        response_schema_id=LC1_RESPONSE_SCHEMA_ID,
        state_id=state_id,
        comparison_profile_id=comparison_profile_id,
        component_order=component_order,
        entries=tuple(entries),
        component_manifest_sha256=component_manifest_sha256,
        canonical_response_sha256=_sha256_json(response_manifest),
        all_entries_finite=all(item.finite for item in entries),
    )


def compare_required_responses(
    reference: CanonicalResponse,
    candidate: CanonicalResponse,
) -> ResponseComparison:
    """Apply the frozen CPU/ROCm zero-safe response predicate."""

    structural_equal = _response_structure(reference) == _response_structure(
        candidate
    )
    if not structural_equal:
        return ResponseComparison(
            predicate_id="registered_response_equivalence_v1",
            structural_equal=False,
            entry_results=(),
            response_defect=math.inf,
            passed=False,
        )
    profile = _threshold_profile(reference.comparison_profile_id)
    results: list[EntryComparison] = []
    for ref_entry, cand_entry in zip(
        reference.entries,
        candidate.entries,
        strict=True,
    ):
        ref = ref_entry.tensor.detach().to(dtype=torch.float64).reshape(-1)
        cand = cand_entry.tensor.detach().to(dtype=torch.float64).reshape(-1)
        finite = bool(torch.isfinite(ref).all() and torch.isfinite(cand).all())
        if not finite:
            results.append(
                EntryComparison(
                    component_id=ref_entry.component_id,
                    entry_key=ref_entry.entry_key,
                    reference_l2=math.inf,
                    candidate_l2=math.inf,
                    difference_l2=math.inf,
                    relative_l2=math.inf,
                    max_abs=math.inf,
                    cosine=None,
                    zero_case="nonfinite",
                    finite=False,
                    defect=math.inf,
                    passed=False,
                )
            )
            continue
        ref_l2 = float(torch.linalg.vector_norm(ref))
        cand_l2 = float(torch.linalg.vector_norm(cand))
        diff = cand - ref
        diff_l2 = float(torch.linalg.vector_norm(diff))
        max_abs = float(torch.max(torch.abs(diff))) if diff.numel() else 0.0
        scale = max(ref_l2, cand_l2, profile["zero_atol"])
        relative_l2 = diff_l2 / scale
        ref_active = ref_l2 > profile["zero_atol"]
        cand_active = cand_l2 > profile["zero_atol"]
        cosine: float | None
        if ref_active and cand_active:
            cosine = float(torch.dot(ref, cand) / (ref_l2 * cand_l2))
            zero_case = "both_active"
            cosine_defect = (1.0 - cosine) / (1.0 - profile["min_cosine"])
            defect = max(
                max_abs / profile["max_abs"],
                relative_l2 / profile["max_relative_l2"],
                cosine_defect,
            )
        elif not ref_active and not cand_active:
            cosine = None
            zero_case = "both_zero"
            defect = max(
                max_abs / profile["max_abs"],
                relative_l2 / profile["max_relative_l2"],
            )
        else:
            cosine = None
            zero_case = "one_zero"
            defect = math.inf
        results.append(
            EntryComparison(
                component_id=ref_entry.component_id,
                entry_key=ref_entry.entry_key,
                reference_l2=ref_l2,
                candidate_l2=cand_l2,
                difference_l2=diff_l2,
                relative_l2=relative_l2,
                max_abs=max_abs,
                cosine=cosine,
                zero_case=zero_case,
                finite=True,
                defect=defect,
                passed=defect <= 1.0,
            )
        )
    response_defect = max((item.defect for item in results), default=math.inf)
    passed = (
        structural_equal
        and reference.all_entries_finite
        and candidate.all_entries_finite
        and bool(results)
        and all(item.passed for item in results)
    )
    return ResponseComparison(
        predicate_id="registered_response_equivalence_v1",
        structural_equal=structural_equal,
        entry_results=tuple(results),
        response_defect=response_defect,
        passed=passed,
    )


def map_resource_trajectory(
    trajectory: ResourceTrajectory,
) -> CostVector:
    """Map a complete LC2 trajectory to a non-scalarized cost vector."""

    _validate_trajectory(trajectory)
    active = _active_cost_fields(trajectory.cost_profile_id)
    primary_clock = (
        "host_process_time_ns"
        if trajectory.lane_profile_id == "cpu_float64_engineering"
        else "rocm_event_time_ns"
    )
    diagnostic_clock = primary_clock
    numeric: dict[str, int] = {
        "compute_primary_time_ns": _union_duration(
            trajectory.intervals,
            owner=IntervalOwner.CORE_COMPUTE,
            clock_domain=primary_clock,
        ),
        "latency_wall_time_ns": trajectory.root_end_ns
        - trajectory.root_start_ns,
        "peak_allocated_bytes": _memory_value(
            trajectory.memory,
            "peak_allocated_bytes",
        ),
        "peak_reserved_bytes": _memory_value(
            trajectory.memory,
            "peak_reserved_bytes",
        ),
        "diagnostic_primary_time_ns": _union_duration(
            trajectory.intervals,
            owner=IntervalOwner.DIAGNOSTIC,
            clock_domain=diagnostic_clock,
        ),
        "diagnostic_materialized_bytes": _artifact_bytes(
            trajectory.artifacts,
            IntervalOwner.DIAGNOSTIC,
        ),
        "observer_overhead_time_ns": _observer_overhead(
            trajectory.observer_calibration
        ),
        "observer_evidence_bytes": _artifact_bytes(
            trajectory.artifacts,
            IntervalOwner.OBSERVER,
        ),
        "control_wall_time_ns": _union_duration(
            trajectory.intervals,
            owner=IntervalOwner.CONTROL,
            clock_domain="host_monotonic_ns",
        ),
        "fallback_wall_time_ns": _union_duration(
            trajectory.intervals,
            owner=IntervalOwner.FALLBACK,
            clock_domain="host_monotonic_ns",
        ),
    }
    field_order = (
        "compute_primary_time_ns",
        "latency_wall_time_ns",
        "peak_allocated_bytes",
        "peak_reserved_bytes",
        "diagnostic_primary_time_ns",
        "diagnostic_materialized_bytes",
        "observer_overhead_time_ns",
        "observer_evidence_bytes",
        "control_wall_time_ns",
        "fallback_wall_time_ns",
    )
    fields = tuple(
        (
            name,
            CostField(
                status="measured" if name in active else "not_executed",
                value=numeric[name] if name in active else None,
            ),
        )
        for name in field_order
    )
    if trajectory.cost_profile_id == "shadow_mechanism_v1" and (
        trajectory.fallback.fallback_invoked
    ):
        raise QWakeLC4BoundedError(
            "normal shadow-mechanism arms cannot invoke fallback"
        )
    return CostVector(
        cost_schema_id=LC2_COST_SCHEMA_ID,
        action_id=trajectory.action_id,
        opaque_state_ref=trajectory.opaque_state_ref,
        repeat_index=trajectory.repeat_index,
        lane_profile_id=trajectory.lane_profile_id,
        cost_profile_id=trajectory.cost_profile_id,
        fields=fields,
        fallback_invoked=trajectory.fallback.fallback_invoked,
    )


def aggregate_paired_costs(
    pairs: Sequence[CostPair],
) -> PairedCostAggregation:
    """Aggregate exactly twelve paired vectors component by component."""

    values = tuple(pairs)
    if len(values) != PAIR_COUNT:
        raise QWakeLC4BoundedError("paired aggregation requires twelve pairs")
    if tuple(item.repeat_index for item in values) != tuple(range(PAIR_COUNT)):
        raise QWakeLC4BoundedError("paired repeats must be complete and ordered")
    if tuple(item.arm_order for item in values) != pair_schedule():
        raise QWakeLC4BoundedError("paired arm order differs from LC3")
    first = values[0]
    identity = (
        first.exact_reference.opaque_state_ref,
        first.exact_reference.lane_profile_id,
        first.exact_reference.cost_profile_id,
        tuple(name for name, _ in first.exact_reference.fields),
    )
    active_names = tuple(first.exact_reference.active_values())
    if not active_names:
        raise QWakeLC4BoundedError("paired cost vectors have no active fields")
    deltas: dict[str, list[int]] = {name: [] for name in active_names}
    action_strata: dict[BoundedArm, dict[str, dict[str, list[int]]]] = {
        arm: {
            "first": {name: [] for name in active_names},
            "second": {name: [] for name in active_names},
        }
        for arm in BoundedArm
    }
    for pair in values:
        exact = pair.exact_reference
        candidate = pair.analytic_candidate
        for vector in (exact, candidate):
            current_identity = (
                vector.opaque_state_ref,
                vector.lane_profile_id,
                vector.cost_profile_id,
                tuple(name for name, _ in vector.fields),
            )
            if current_identity != identity:
                raise QWakeLC4BoundedError("paired cost identity mismatch")
            if vector.repeat_index != pair.repeat_index:
                raise QWakeLC4BoundedError("cost repeat identity mismatch")
            if vector.fallback_invoked:
                raise QWakeLC4BoundedError(
                    "normal matched arms cannot invoke fallback"
                )
            if tuple(vector.active_values()) != active_names:
                raise QWakeLC4BoundedError("active cost mask differs")
        exact_values = exact.active_values()
        candidate_values = candidate.active_values()
        for name in active_names:
            deltas[name].append(candidate_values[name] - exact_values[name])
        for position, arm in enumerate(pair.arm_order):
            stratum = "first" if position == 0 else "second"
            vector = exact if arm is BoundedArm.EXACT_REFERENCE else candidate
            vector_values = vector.active_values()
            for name in active_names:
                action_strata[arm][stratum][name].append(vector_values[name])
    summaries = tuple(
        (name, _five_number_summary(tuple(deltas[name])))
        for name in active_names
    )
    tolerance = _cost_tolerance_profile(first.exact_reference.lane_profile_id)
    order_effect_passed = True
    for arm in BoundedArm:
        for name in active_names:
            first_median = _median(tuple(action_strata[arm]["first"][name]))
            second_median = _median(tuple(action_strata[arm]["second"][name]))
            tolerance_class = _cost_tolerance_class(name)
            atol, rtol = tolerance[tolerance_class]
            if abs(first_median - second_median) > (
                atol + rtol * max(abs(first_median), abs(second_median))
            ):
                order_effect_passed = False
    return PairedCostAggregation(
        aggregate_id="stage3b-qwake-paired-aggregation-v1",
        field_summaries=summaries,
        order_effect_passed=order_effect_passed,
        pair_complete=True,
    )


def _validate_trajectory(trajectory: ResourceTrajectory) -> None:
    if trajectory.trajectory_schema_id != (
        "stage3b-qwake-resource-trajectory-v1"
    ):
        raise QWakeLC4BoundedError("unexpected trajectory schema")
    _require_sha256(trajectory.opaque_state_ref, field_name="opaque_state_ref")
    if trajectory.repeat_index < 0:
        raise QWakeLC4BoundedError("repeat_index must be non-negative")
    if trajectory.lane_profile_id not in {
        "cpu_float64_engineering",
        "rocm_float32_canonical",
    }:
        raise QWakeLC4BoundedError("lane profile is not registered")
    _active_cost_fields(trajectory.cost_profile_id)
    if trajectory.root_clock_domain != "host_monotonic_ns":
        raise QWakeLC4BoundedError("root clock must be host_monotonic_ns")
    if trajectory.root_end_ns <= trajectory.root_start_ns:
        raise QWakeLC4BoundedError("root interval must have positive duration")
    if tuple(item.position for item in trajectory.intervals) != tuple(
        range(len(trajectory.intervals))
    ):
        raise QWakeLC4BoundedError("interval positions are not contiguous")
    duplicate_ownership: set[tuple[str, str, int, int]] = set()
    for interval in trajectory.intervals:
        if not interval.complete:
            raise QWakeLC4BoundedError("incomplete interval fails closed")
        if interval.end_ns < interval.start_ns or interval.start_ns < 0:
            raise QWakeLC4BoundedError("invalid interval bounds")
        if (
            interval.lane == "host"
            and interval.clock_domain == trajectory.root_clock_domain
            and not (
                trajectory.root_start_ns <= interval.start_ns
                and interval.end_ns <= trajectory.root_end_ns
            )
        ):
            raise QWakeLC4BoundedError("host interval escapes root bounds")
        ownership_key = (
            interval.lane,
            interval.clock_domain,
            interval.start_ns,
            interval.end_ns,
        )
        if ownership_key in duplicate_ownership:
            raise QWakeLC4BoundedError("interval has duplicate semantic ownership")
        duplicate_ownership.add(ownership_key)
    metrics = {item.metric for item in trajectory.memory}
    if metrics != {"peak_allocated_bytes", "peak_reserved_bytes"}:
        raise QWakeLC4BoundedError("memory metric registry is incomplete")
    for item in trajectory.memory:
        if not item.complete or item.value_bytes < 0:
            raise QWakeLC4BoundedError("invalid memory record")
    if tuple(item.position for item in trajectory.artifacts) != tuple(
        range(len(trajectory.artifacts))
    ):
        raise QWakeLC4BoundedError("artifact positions are not contiguous")
    for artifact in trajectory.artifacts:
        if artifact.owner not in {
            IntervalOwner.DIAGNOSTIC,
            IntervalOwner.OBSERVER,
        }:
            raise QWakeLC4BoundedError("artifact owner is not registered")
        _require_sha256(artifact.sha256, field_name="artifact.sha256")
        if artifact.size_bytes < 0:
            raise QWakeLC4BoundedError("artifact size must be non-negative")
    fallback = trajectory.fallback
    if not fallback.fallback_available:
        raise QWakeLC4BoundedError("exact reserve path must be available")
    fallback_duration = _union_duration(
        trajectory.intervals,
        owner=IntervalOwner.FALLBACK,
        clock_domain="host_monotonic_ns",
    )
    if fallback.fallback_invoked:
        if not fallback.fallback_completed or fallback_duration <= 0:
            raise QWakeLC4BoundedError("invoked fallback is incomplete")
    elif fallback_duration != 0:
        raise QWakeLC4BoundedError("non-invoked fallback has measured time")
    calibration = trajectory.observer_calibration
    if calibration is None or not calibration.complete:
        raise QWakeLC4BoundedError("observer calibration is incomplete")
    expected_residual = (
        calibration.instrumented_latency_ns - calibration.control_latency_ns
    )
    if calibration.raw_residual_ns != expected_residual:
        raise QWakeLC4BoundedError("observer residual is inconsistent")
    if calibration.overclosure != (expected_residual < 0):
        raise QWakeLC4BoundedError("observer overclosure flag is inconsistent")


def _active_cost_fields(profile_id: str) -> tuple[str, ...]:
    if profile_id == "shadow_mechanism_v1":
        return (
            "compute_primary_time_ns",
            "latency_wall_time_ns",
            "peak_allocated_bytes",
            "peak_reserved_bytes",
            "diagnostic_primary_time_ns",
            "diagnostic_materialized_bytes",
            "observer_overhead_time_ns",
            "observer_evidence_bytes",
        )
    if profile_id == "end_to_end_v1":
        return (
            "compute_primary_time_ns",
            "latency_wall_time_ns",
            "peak_allocated_bytes",
            "peak_reserved_bytes",
            "diagnostic_primary_time_ns",
            "diagnostic_materialized_bytes",
            "observer_overhead_time_ns",
            "observer_evidence_bytes",
            "control_wall_time_ns",
            "fallback_wall_time_ns",
        )
    raise QWakeLC4BoundedError("cost profile is not registered")


def _union_duration(
    intervals: Sequence[IntervalRecord],
    *,
    owner: IntervalOwner,
    clock_domain: str,
) -> int:
    selected = sorted(
        (
            (item.start_ns, item.end_ns)
            for item in intervals
            if item.owner is owner and item.clock_domain == clock_domain
        ),
        key=lambda item: (item[0], item[1]),
    )
    if not selected:
        return 0
    total = 0
    current_start, current_end = selected[0]
    for start, end in selected[1:]:
        if start <= current_end:
            current_end = max(current_end, end)
        else:
            total += current_end - current_start
            current_start, current_end = start, end
    return total + current_end - current_start


def _memory_value(records: Sequence[MemoryRecord], metric: str) -> int:
    values = [item.value_bytes for item in records if item.metric == metric]
    if len(values) != 1:
        raise QWakeLC4BoundedError("memory metric must occur exactly once")
    return values[0]


def _artifact_bytes(
    records: Sequence[ArtifactRecord],
    owner: IntervalOwner,
) -> int:
    unique: dict[str, int] = {}
    for record in records:
        if record.owner is not owner:
            continue
        previous = unique.setdefault(record.sha256, record.size_bytes)
        if previous != record.size_bytes:
            raise QWakeLC4BoundedError("artifact digest has conflicting sizes")
    return sum(unique.values())


def _observer_overhead(calibration: ObserverCalibration | None) -> int:
    if calibration is None:
        raise QWakeLC4BoundedError("observer calibration is absent")
    return max(0, calibration.raw_residual_ns)


def _five_number_summary(values: tuple[int, ...]) -> FieldSummary:
    if len(values) != PAIR_COUNT:
        raise QWakeLC4BoundedError("field summary requires twelve values")
    ordered = tuple(sorted(values))
    return FieldSummary(
        median_paired_delta=(ordered[5] + ordered[6]) / 2.0,
        q1_paired_delta=(ordered[2] + ordered[3]) / 2.0,
        q3_paired_delta=(ordered[8] + ordered[9]) / 2.0,
        minimum_paired_delta=ordered[0],
        maximum_paired_delta=ordered[-1],
    )


def _median(values: tuple[int, ...]) -> float:
    if not values:
        raise QWakeLC4BoundedError("median requires values")
    ordered = tuple(sorted(values))
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[midpoint])
    return (ordered[midpoint - 1] + ordered[midpoint]) / 2.0


def _cost_tolerance_profile(
    lane_profile_id: str,
) -> Mapping[str, tuple[int, float]]:
    if lane_profile_id == "cpu_float64_engineering":
        return {
            "time_ns": (50000, 0.1),
            "peak_bytes": (4096, 0.02),
            "artifact_bytes": (0, 0.0),
        }
    if lane_profile_id == "rocm_float32_canonical":
        return {
            "time_ns": (10000, 0.05),
            "peak_bytes": (4096, 0.01),
            "artifact_bytes": (0, 0.0),
        }
    raise QWakeLC4BoundedError("lane profile is not registered")


def _cost_tolerance_class(field_name: str) -> str:
    if field_name in {
        "compute_primary_time_ns",
        "latency_wall_time_ns",
        "diagnostic_primary_time_ns",
        "observer_overhead_time_ns",
        "control_wall_time_ns",
        "fallback_wall_time_ns",
    }:
        return "time_ns"
    if field_name in {"peak_allocated_bytes", "peak_reserved_bytes"}:
        return "peak_bytes"
    if field_name in {
        "diagnostic_materialized_bytes",
        "observer_evidence_bytes",
    }:
        return "artifact_bytes"
    raise QWakeLC4BoundedError("cost field has no tolerance class")


def capture_rng_snapshot(
    custom_generators: Mapping[str, torch.Generator] | None = None,
) -> RNGSnapshot:
    """Capture the complete registered default RNG inventory."""

    generators = {} if custom_generators is None else dict(custom_generators)
    if len(generators) != len(set(generators)):
        raise QWakeLC4BoundedError("custom RNG ids must be unique")
    records: list[RNGRecord] = []
    records.append(
        _rng_record(
            "python_random_global",
            "python_pickle_protocol_5",
            pickle.dumps(random.getstate(), protocol=5),
        )
    )
    records.append(
        _rng_record(
            "numpy_legacy_global",
            "numpy_legacy_pickle_protocol_5",
            pickle.dumps(np.random.get_state(), protocol=5),
        )
    )
    records.append(
        _rng_record(
            "torch_cpu_default_generator",
            "torch_uint8_raw",
            _torch_state_bytes(torch.random.get_rng_state()),
        )
    )
    if torch.cuda.is_available():
        for index, state in enumerate(torch.cuda.get_rng_state_all()):
            records.append(
                _rng_record(
                    f"torch_rocm_visible_device_generator_{index}",
                    "torch_uint8_raw",
                    _torch_state_bytes(state),
                )
            )
    for generator_id, generator in sorted(generators.items()):
        if not generator_id.strip():
            raise QWakeLC4BoundedError("custom RNG id cannot be empty")
        records.append(
            _rng_record(
                f"custom:{generator_id}",
                "torch_uint8_raw",
                _torch_state_bytes(generator.get_state()),
            )
        )
    records.sort(key=lambda item: item.generator_id)
    digest_manifest = tuple(
        (item.generator_id, item.state_encoding, item.state_sha256)
        for item in records
    )
    return RNGSnapshot(
        snapshot_id=RNG_SNAPSHOT_ID,
        records=tuple(records),
        snapshot_sha256=_sha256_json(digest_manifest),
    )


def restore_rng_snapshot(
    snapshot: RNGSnapshot,
    custom_generators: Mapping[str, torch.Generator] | None = None,
) -> None:
    """Restore every captured RNG or fail when inventory differs."""

    generators = {} if custom_generators is None else dict(custom_generators)
    record_by_id = {item.generator_id: item for item in snapshot.records}
    expected_custom = {
        item.removeprefix("custom:")
        for item in record_by_id
        if item.startswith("custom:")
    }
    if expected_custom != set(generators):
        raise QWakeLC4BoundedError("custom RNG inventory differs from snapshot")
    random.setstate(
        pickle.loads(  # noqa: S301 - trusted in-memory snapshot
            record_by_id["python_random_global"].state_bytes
        )
    )
    np.random.set_state(
        pickle.loads(  # noqa: S301 - trusted in-memory snapshot
            record_by_id["numpy_legacy_global"].state_bytes
        )
    )
    torch.random.set_rng_state(
        _bytes_to_torch_state(
            record_by_id["torch_cpu_default_generator"].state_bytes
        )
    )
    device_records = tuple(
        item
        for key, item in sorted(
            (
                (key, item)
                for key, item in record_by_id.items()
                if key.startswith("torch_rocm_visible_device_generator_")
            ),
            key=lambda pair: int(pair[0].rsplit("_", 1)[1]),
        )
    )
    if device_records:
        if not torch.cuda.is_available():
            raise QWakeLC4BoundedError("captured ROCm RNG inventory is unavailable")
        if len(device_records) != torch.cuda.device_count():
            raise QWakeLC4BoundedError("visible ROCm RNG inventory changed")
        torch.cuda.set_rng_state_all(
            [_bytes_to_torch_state(item.state_bytes) for item in device_records]
        )
    for generator_id, generator in generators.items():
        generator.set_state(
            _bytes_to_torch_state(
                record_by_id[f"custom:{generator_id}"].state_bytes
            )
        )


@contextmanager
def preserve_outer_rng(
    custom_generators: Mapping[str, torch.Generator] | None = None,
) -> Iterator[RNGSnapshot]:
    """Restore the process RNG inventory after a bounded unit-test cell."""

    outer = capture_rng_snapshot(custom_generators)
    try:
        yield outer
    finally:
        restore_rng_snapshot(outer, custom_generators)


def pair_schedule() -> tuple[tuple[BoundedArm, BoundedArm], ...]:
    """Return the frozen balanced twelve-repeat schedule."""

    return tuple(
        (
            (BoundedArm.EXACT_REFERENCE, BoundedArm.ANALYTIC_CANDIDATE)
            if repeat_index % 2 == 0
            else (BoundedArm.ANALYTIC_CANDIDATE, BoundedArm.EXACT_REFERENCE)
        )
        for repeat_index in range(PAIR_COUNT)
    )


def run_synthetic_matched_pair(
    snapshot: OpaqueStateSnapshot,
    rng_snapshot: RNGSnapshot,
    *,
    repeat_index: int,
    authorization: BoundedUnitTestAuthorization,
    custom_generators: Mapping[str, torch.Generator] | None = None,
) -> MatchedPairResult:
    """Run one matched pair only under the synthetic unit-test permit."""

    authorization.require()
    _require_synthetic_snapshot(snapshot)
    if not 0 <= repeat_index < PAIR_COUNT:
        raise QWakeLC4BoundedError("repeat_index is outside the frozen schedule")
    order = pair_schedule()[repeat_index]
    results: dict[BoundedArm, BoundedArmResult] = {}
    with preserve_outer_rng(custom_generators):
        for arm in order:
            restore_rng_snapshot(rng_snapshot, custom_generators)
            rng_before = capture_rng_snapshot(custom_generators)
            model, frontier = snapshot.fork()
            completion = (
                complete_exact_suffix(model, frontier)
                if arm is BoundedArm.EXACT_REFERENCE
                else analytic_wavefront_completion(model, frontier)
            )
            response = materialize_required_response(
                model,
                completion,
                state_id=snapshot.opaque_state_ref,
                comparison_profile_id=snapshot.comparison_profile_id,
            )
            rng_after = capture_rng_snapshot(custom_generators)
            results[arm] = BoundedArmResult(
                arm=arm,
                response=response,
                rng_before_sha256=rng_before.snapshot_sha256,
                rng_after_sha256=rng_after.snapshot_sha256,
                vjp_count=completion.vjp_count,
                fallback_invoked=completion.fallback_invoked,
            )
    snapshot.verify_integrity()
    exact = results[BoundedArm.EXACT_REFERENCE]
    candidate = results[BoundedArm.ANALYTIC_CANDIDATE]
    return MatchedPairResult(
        repeat_index=repeat_index,
        arm_order=order,
        exact_reference=exact,
        analytic_candidate=candidate,
        response_comparison=compare_required_responses(
            exact.response,
            candidate.response,
        ),
        rng_post_match=(
            exact.rng_before_sha256 == candidate.rng_before_sha256
            and exact.rng_after_sha256 == candidate.rng_after_sha256
        ),
    )


def run_synthetic_reserve_probe(
    snapshot: OpaqueStateSnapshot,
    rng_snapshot: RNGSnapshot,
    *,
    authorization: BoundedUnitTestAuthorization,
    custom_generators: Mapping[str, torch.Generator] | None = None,
) -> ReserveProbeResult:
    """Force the complete exact reserve path before candidate mutation."""

    authorization.require()
    _require_synthetic_snapshot(snapshot)
    with preserve_outer_rng(custom_generators):
        restore_rng_snapshot(rng_snapshot, custom_generators)
        fallback_model, fallback_frontier = snapshot.fork()
        fallback = complete_exact_suffix(
            fallback_model,
            fallback_frontier,
            fallback_invoked=True,
        )
        fallback_response = materialize_required_response(
            fallback_model,
            fallback,
            state_id=snapshot.opaque_state_ref,
            comparison_profile_id=snapshot.comparison_profile_id,
        )
        restore_rng_snapshot(rng_snapshot, custom_generators)
        direct_model, direct_frontier = snapshot.fork()
        direct = complete_exact_suffix(direct_model, direct_frontier)
        direct_response = materialize_required_response(
            direct_model,
            direct,
            state_id=snapshot.opaque_state_ref,
            comparison_profile_id=snapshot.comparison_profile_id,
        )
        rng_post = capture_rng_snapshot(custom_generators)
    snapshot.verify_integrity()
    expected = tuple(
        range(snapshot.frontier.candidate_index + 1, len(fallback_model) + 1)
    )
    completed = expected
    return ReserveProbeResult(
        completed_suffix_indices=completed,
        no_skipped_indices=completed == expected,
        no_duplicate_indices=len(completed) == len(set(completed)),
        fallback_available=True,
        fallback_invoked=True,
        fallback_completed=True,
        fallback_response_sha256=fallback_response.canonical_response_sha256,
        direct_reference_response_sha256=(
            direct_response.canonical_response_sha256
        ),
        rng_post_sha256=rng_post.snapshot_sha256,
    )


def _run_fixedpred_sweeps(
    model: nn.Sequential,
    fixed: Sequence[Tensor],
    beliefs: list[Tensor],
    errors: list[Tensor | None],
    *,
    sweep_count: int,
) -> tuple[list[Tensor], list[Tensor | None]]:
    if sweep_count < 0:
        raise QWakeLC4BoundedError("sweep_count must be non-negative")
    if sweep_count == 0:
        return beliefs, errors
    linear_inputs: list[Tensor] = []
    linear_outputs: list[Tensor] = []
    for layer_index, module in enumerate(model):
        linear_input = fixed[layer_index].detach().requires_grad_(True)
        linear_inputs.append(linear_input)
        linear_outputs.append(module(linear_input))
    for sweep in range(sweep_count):
        retain_graph = sweep < sweep_count - 1
        for layer_index in reversed(range(len(model))):
            errors[layer_index] = fixed[layer_index] - beliefs[layer_index]
            upper = errors[layer_index + 1]
            if upper is None:
                raise QWakeLC4BoundedError("FixedPred error chain is incomplete")
            propagated = torch.autograd.grad(
                linear_outputs[layer_index],
                linear_inputs[layer_index],
                grad_outputs=upper,
                retain_graph=retain_graph,
            )[0]
            current = errors[layer_index]
            if current is None:
                raise QWakeLC4BoundedError("FixedPred residual is absent")
            beliefs[layer_index] = beliefs[layer_index] + current - propagated
        for layer_index in range(1, len(model)):
            beliefs[layer_index] = beliefs[layer_index].detach()
            current = errors[layer_index]
            if current is None:
                raise QWakeLC4BoundedError("FixedPred residual is absent")
            errors[layer_index] = current.detach()
    return beliefs, errors


def _validate_frontier(
    model: nn.Sequential,
    frontier: FixedPredFrontier,
) -> None:
    _require_sequential(model)
    expected = len(model) + 1
    if not 0 <= frontier.candidate_index <= len(model):
        raise QWakeLC4BoundedError("candidate_index is outside [0,K_ref]")
    if len(frontier.fixed) != expected:
        raise QWakeLC4BoundedError("fixed activation registry is incomplete")
    if len(frontier.beliefs) != expected:
        raise QWakeLC4BoundedError("belief registry is incomplete")
    if len(frontier.errors) != expected:
        raise QWakeLC4BoundedError("error registry is incomplete")
    if frontier.errors[-1] is None:
        raise QWakeLC4BoundedError("output error is absent")
    if frontier.endpoint_loss.ndim != 0:
        raise QWakeLC4BoundedError("endpoint loss must be scalar")
    for fixed, belief in zip(frontier.fixed, frontier.beliefs, strict=True):
        if fixed.shape != belief.shape or fixed.dtype != belief.dtype:
            raise QWakeLC4BoundedError("belief and fixed activation differ")
        if not bool(torch.isfinite(fixed).all() and torch.isfinite(belief).all()):
            raise QWakeLC4BoundedError("frontier contains non-finite beliefs")
    for error in frontier.errors:
        if error is not None and not bool(torch.isfinite(error).all()):
            raise QWakeLC4BoundedError("frontier contains non-finite errors")


def _validate_final_frontier(
    model: nn.Sequential,
    frontier: FixedPredFrontier,
) -> None:
    _validate_frontier(model, frontier)
    if frontier.candidate_index != len(model):
        raise QWakeLC4BoundedError("completion did not reach K_ref")
    if any(item is None for item in frontier.errors):
        raise QWakeLC4BoundedError("completed error chain is incomplete")


def _validate_completed_upper_wavefront(
    fixed: Sequence[Tensor],
    beliefs: Sequence[Tensor],
    errors: Sequence[Tensor | None],
    *,
    boundary: int,
) -> None:
    if not torch.equal(beliefs[-1], fixed[-1]):
        raise QWakeLC4BoundedError("output belief changed before completion")
    for index in range(boundary + 1, len(fixed) - 1):
        error = errors[index]
        if error is None:
            raise QWakeLC4BoundedError("completed upper error is absent")
        residual = fixed[index] - beliefs[index]
        if not torch.equal(error, residual):
            raise QWakeLC4BoundedError("completed upper wavefront is inconsistent")


def _build_state_manifest(
    model: nn.Sequential,
    inputs: Tensor,
    targets: Tensor,
    frontier: FixedPredFrontier,
    *,
    domain: RegisteredDomain,
    lane_profile_id: str,
    comparison_profile_id: str,
    runtime_controls: tuple[tuple[str, Scalar], ...],
    optional_update_state: Mapping[str, object] | None,
) -> Mapping[str, object]:
    input_sha = _tensor_sha256(inputs)
    target_sha = _tensor_sha256(targets)
    parameter_manifest = tuple(
        (name, _tensor_manifest(value))
        for name, value in model.named_parameters()
    )
    buffer_manifest = tuple(
        (name, _tensor_manifest(value)) for name, value in model.named_buffers()
    )
    belief_manifest = {
        "fixed": tuple(
            (str(index), _tensor_manifest(value))
            for index, value in enumerate(frontier.fixed)
        ),
        "beliefs": tuple(
            (str(index), _tensor_manifest(value))
            for index, value in enumerate(frontier.beliefs)
        ),
        "errors": tuple(
            (
                str(index),
                {"status": "not_present"}
                if value is None
                else _tensor_manifest(value),
            )
            for index, value in enumerate(frontier.errors)
        ),
        "endpoint_loss": _tensor_manifest(frontier.endpoint_loss),
    }
    update_manifest: object = (
        {"status": "not_present"}
        if optional_update_state is None
        else _canonicalize(optional_update_state)
    )
    control_manifest = _canonicalize(dict(runtime_controls))
    return {
        "state_schema_id": OPAQUE_STATE_SCHEMA_ID,
        "method": domain.method,
        "eta": domain.eta,
        "architecture": domain.architecture,
        "executor": domain.executor,
        "decision_epoch": domain.decision_epoch,
        "candidate_index": frontier.candidate_index,
        "reference_suffix_length": len(model) - frontier.candidate_index,
        "lane_profile_id": lane_profile_id,
        "comparison_profile_id": comparison_profile_id,
        "input_batch_sha256": input_sha,
        "target_batch_sha256": target_sha,
        "parameter_manifest_sha256": _sha256_json(parameter_manifest),
        "buffer_manifest_sha256": _sha256_json(buffer_manifest),
        "belief_state_manifest_sha256": _sha256_json(belief_manifest),
        "optional_update_state_manifest_sha256": _sha256_json(update_manifest),
        "runtime_control_manifest_sha256": _sha256_json(control_manifest),
    }


def _opaque_state_ref(manifest: Mapping[str, object]) -> str:
    return _sha256_json(manifest)


def _response_entry(
    component_id: str,
    entry_key: str,
    position: int,
    tensor: Tensor,
) -> TensorEntry:
    payload = tensor.detach().clone()
    return TensorEntry(
        component_id=component_id,
        entry_key=entry_key,
        entry_position=position,
        shape=tuple(payload.shape),
        source_dtype=str(payload.dtype).removeprefix("torch."),
        numel=payload.numel(),
        finite=bool(torch.isfinite(payload).all()),
        payload_sha256=_tensor_sha256(payload),
        tensor=payload,
    )


def _entry_manifest(entry: TensorEntry) -> Mapping[str, object]:
    return {
        "component_id": entry.component_id,
        "entry_key": entry.entry_key,
        "entry_position": entry.entry_position,
        "shape": entry.shape,
        "source_dtype": entry.source_dtype,
        "numel": entry.numel,
        "finite": entry.finite,
        "payload_sha256": entry.payload_sha256,
    }


def _response_structure(response: CanonicalResponse) -> object:
    return (
        response.response_schema_id,
        response.state_id,
        response.comparison_profile_id,
        response.component_order,
        tuple(
            (
                item.component_id,
                item.entry_key,
                item.entry_position,
                item.shape,
                item.source_dtype,
                item.numel,
            )
            for item in response.entries
        ),
    )


def _threshold_profile(profile_id: str) -> Mapping[str, float]:
    profiles: Mapping[str, Mapping[str, float]] = {
        "cpu_float64_engineering": {
            "max_abs": 1e-9,
            "max_relative_l2": 1e-7,
            "min_cosine": 0.99999,
            "zero_atol": 1e-12,
        },
        "rocm_float32_canonical": {
            "max_abs": 1e-5,
            "max_relative_l2": 1e-3,
            "min_cosine": 0.999,
            "zero_atol": 1e-7,
        },
    }
    try:
        return profiles[profile_id]
    except KeyError as exc:
        raise QWakeLC4BoundedError(
            "comparison profile is not registered"
        ) from exc


def _require_synthetic_snapshot(snapshot: OpaqueStateSnapshot) -> None:
    controls = dict(snapshot.runtime_controls)
    if controls.get("data_classification") != "synthetic_unit_test":
        raise QWakeLC4BoundedError(
            "bounded unit-test runner rejects non-synthetic state"
        )
    if controls.get("runtime_execution_permitted") is not False:
        raise QWakeLC4BoundedError("runtime execution must remain closed")
    if controls.get("scientific_execution_open") is not False:
        raise QWakeLC4BoundedError("scientific execution must remain closed")


def _rng_record(
    generator_id: str,
    encoding: str,
    state_bytes: bytes,
) -> RNGRecord:
    if not state_bytes:
        raise QWakeLC4BoundedError("RNG state cannot be empty")
    return RNGRecord(
        generator_id=generator_id,
        state_encoding=encoding,
        state_bytes=state_bytes,
        state_sha256=_sha256_bytes(state_bytes),
    )


def _torch_state_bytes(state: Tensor) -> bytes:
    return bytes(
        state.detach().cpu().contiguous().numpy().tobytes(order="C")
    )


def _bytes_to_torch_state(value: bytes) -> Tensor:
    return torch.frombuffer(bytearray(value), dtype=torch.uint8).clone()


def _tensor_manifest(value: Tensor) -> Mapping[str, object]:
    return {
        "shape": tuple(value.shape),
        "source_dtype": str(value.dtype).removeprefix("torch."),
        "numel": value.numel(),
        "finite": bool(torch.isfinite(value).all()),
        "payload_sha256": _tensor_sha256(value),
    }


def _tensor_sha256(value: Tensor) -> str:
    if sys.byteorder != "little":
        raise QWakeLC4BoundedError("canonical tensor encoding requires little endian")
    payload = value.detach().cpu().contiguous().reshape(-1).view(torch.uint8).numpy().tobytes(
        order="C"
    )
    return _sha256_bytes(payload)


def _sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _sha256_json(value: object) -> str:
    return _sha256_bytes(_canonical_json(value).encode("utf-8"))


def _canonical_json(value: object) -> str:
    return json.dumps(
        _canonicalize(value),
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ) + "\n"


def _canonicalize(value: object) -> object:
    if isinstance(value, Tensor):
        return _tensor_manifest(value)
    if isinstance(value, Mapping):
        return {
            str(key): _canonicalize(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, tuple | list):
        return [_canonicalize(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        raise QWakeLC4BoundedError("non-finite JSON value is forbidden")
    if value is None or isinstance(value, str | int | float | bool):
        return value
    raise QWakeLC4BoundedError(
        f"unsupported canonical value: {type(value).__name__}"
    )


def _require_sequential(model: nn.Sequential) -> None:
    if not isinstance(model, nn.Sequential) or len(model) < 1:
        raise QWakeLC4BoundedError("bounded implementation requires nn.Sequential")


def _require_sha256(value: str, *, field_name: str) -> None:
    if not value.startswith("sha256:") or len(value) != 71:
        raise QWakeLC4BoundedError(f"{field_name} is not a sha256 identity")
