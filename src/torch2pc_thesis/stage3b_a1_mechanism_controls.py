from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import torch
import torch.nn as nn

CONTRACT_ID = "stage3b-a1-mechanism-controls-v1"
IMPLEMENTATION_SCHEMA_ID = "stage3b-a1-mechanism-controls-implementation-v1"
CONTROL_ID = "MECH-C0"
TORCH2PC_COMMIT = "b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4"
SPACE_DIMENSION = 8
DEPTH = 6

type Lane = Literal["cpu", "rocm"]
type ExecutionScope = Literal["smoke", "confirmatory"]
type Record = dict[str, Any]


@dataclass(frozen=True)
class ThresholdProfile:
    zero_atol: float
    analytic_max_relative_l2: float
    analytic_max_abs: float
    analytic_min_cosine: float
    snapshot_max_relative_l2: float
    snapshot_max_abs: float
    snapshot_min_cosine: float
    temporal_separation_floor: float


@dataclass(frozen=True)
class Provenance:
    lane: Lane
    device: str
    dtype: str
    source_git_commit: str
    source_git_branch: str
    experiment_image: str
    image_revision: str
    torch2pc_commit: str


@dataclass(frozen=True)
class Comparison:
    absolute_l2: float
    relative_l2: float | None
    max_abs: float
    cosine: float | None
    norm_ratio: float | None
    reference_norm: float
    candidate_norm: float
    finite: bool
    zero_safe_path: bool
    passed: bool

    def to_dict(self) -> Record:
        return {
            "absolute_l2": self.absolute_l2,
            "relative_l2": self.relative_l2,
            "max_abs": self.max_abs,
            "cosine": self.cosine,
            "norm_ratio": self.norm_ratio,
            "reference_norm": self.reference_norm,
            "candidate_norm": self.candidate_norm,
            "finite": self.finite,
            "zero_safe_path": self.zero_safe_path,
            "comparison_passed": self.passed,
        }


def thresholds_for_lane(lane: Lane) -> ThresholdProfile:
    if lane == "cpu":
        return ThresholdProfile(
            zero_atol=1e-12,
            analytic_max_relative_l2=1e-10,
            analytic_max_abs=1e-10,
            analytic_min_cosine=0.999999999,
            snapshot_max_relative_l2=1e-7,
            snapshot_max_abs=1e-9,
            snapshot_min_cosine=0.99999,
            temporal_separation_floor=1e-8,
        )
    return ThresholdProfile(
        zero_atol=1e-6,
        analytic_max_relative_l2=1e-4,
        analytic_max_abs=1e-5,
        analytic_min_cosine=0.9999,
        snapshot_max_relative_l2=1e-3,
        snapshot_max_abs=1e-5,
        snapshot_min_cosine=0.999,
        temporal_separation_floor=1e-5,
    )


def construction_seeds(scope: ExecutionScope) -> list[int]:
    return [0] if scope == "smoke" else [0, 1, 2]


def model_seeds(scope: ExecutionScope) -> list[int]:
    return [0] if scope == "smoke" else [0, 1, 2]


def scale_for_seed(seed: int) -> float:
    scales = {0: 0.25, 1: 1.0, 2: 4.0}
    try:
        return scales[seed]
    except KeyError as exc:
        raise ValueError(f"Unsupported construction seed: {seed}") from exc


def canonical_json_digest(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def contract_digests(contract: Mapping[str, Any]) -> tuple[str, str, str]:
    construction_registry = contract.get("construction_registry")
    thresholds = contract.get("threshold_profiles")
    if not isinstance(construction_registry, Mapping):
        raise ValueError("Contract construction_registry is missing")
    if not isinstance(thresholds, Mapping):
        raise ValueError("Contract threshold_profiles is missing")
    return (
        canonical_json_digest(contract),
        canonical_json_digest(construction_registry),
        canonical_json_digest(thresholds),
    )


def validate_contract(contract: Mapping[str, Any]) -> None:
    if contract.get("contract_id") != CONTRACT_ID:
        raise ValueError("Unexpected mechanism-controls contract id")
    if contract.get("status") != "preregistered":
        raise ValueError("Mechanism-controls contract is not preregistered")
    if contract.get("implementation_present") is not False:
        raise ValueError("Preregistration contract was modified after freeze")
    if contract.get("results_present") is not False:
        raise ValueError("Preregistration contract contains results")
    baseline = contract.get("baseline")
    if not isinstance(baseline, Mapping):
        raise ValueError("Contract baseline is missing")
    if baseline.get("torch2pc_commit") != TORCH2PC_COMMIT:
        raise ValueError("Contract Torch2PC revision mismatch")
    environment = contract.get("environment")
    if not isinstance(environment, Mapping):
        raise ValueError("Contract environment is missing")
    if environment.get("dataset_loader_used") is not False:
        raise ValueError("Primary mechanism suite must not use a dataset loader")
    if environment.get("synthetic_inputs_only") is not True:
        raise ValueError("Primary mechanism suite requires synthetic inputs")


def tensor_fingerprint(tensors: Iterable[torch.Tensor]) -> str:
    digest = hashlib.sha256()
    for tensor in tensors:
        value = tensor.detach().to(device="cpu").contiguous()
        digest.update(str(value.dtype).encode("utf-8"))
        digest.update(str(tuple(value.shape)).encode("utf-8"))
        digest.update(value.numpy().tobytes())
    return digest.hexdigest()


def model_state_fingerprint(model: nn.Module) -> str:
    state = model.state_dict()
    return tensor_fingerprint(state[name] for name in sorted(state))


def rng_fingerprint() -> str:
    tensors = [torch.random.get_rng_state()]
    if torch.cuda.is_available():
        tensors.extend(torch.cuda.get_rng_state_all())
    return tensor_fingerprint(tensors)


def compare_tensors(
    reference: torch.Tensor,
    candidate: torch.Tensor,
    *,
    profile: Literal["analytic_vector", "implementation_snapshot"],
    thresholds: ThresholdProfile,
) -> Comparison:
    ref = reference.detach()
    cand = candidate.detach()
    finite = bool(torch.isfinite(ref).all() and torch.isfinite(cand).all())
    if not finite or ref.shape != cand.shape:
        return Comparison(
            absolute_l2=math.inf,
            relative_l2=None,
            max_abs=math.inf,
            cosine=None,
            norm_ratio=None,
            reference_norm=float(torch.linalg.vector_norm(ref).item())
            if finite
            else math.inf,
            candidate_norm=float(torch.linalg.vector_norm(cand).item())
            if finite
            else math.inf,
            finite=False,
            zero_safe_path=False,
            passed=False,
        )

    difference = cand - ref
    absolute_l2 = float(torch.linalg.vector_norm(difference).item())
    max_abs = float(torch.max(torch.abs(difference)).item()) if difference.numel() else 0.0
    reference_norm = float(torch.linalg.vector_norm(ref).item())
    candidate_norm = float(torch.linalg.vector_norm(cand).item())
    ref_zero = reference_norm <= thresholds.zero_atol
    cand_zero = candidate_norm <= thresholds.zero_atol

    if ref_zero or cand_zero:
        passed = ref_zero and cand_zero and max_abs <= thresholds.zero_atol
        return Comparison(
            absolute_l2=absolute_l2,
            relative_l2=None,
            max_abs=max_abs,
            cosine=None,
            norm_ratio=None,
            reference_norm=reference_norm,
            candidate_norm=candidate_norm,
            finite=True,
            zero_safe_path=True,
            passed=passed,
        )

    relative_l2 = absolute_l2 / reference_norm
    cosine = float(
        torch.nn.functional.cosine_similarity(
            ref.reshape(1, -1), cand.reshape(1, -1), dim=1
        ).item()
    )
    norm_ratio = candidate_norm / reference_norm
    if profile == "analytic_vector":
        max_relative_l2 = thresholds.analytic_max_relative_l2
        max_abs_limit = thresholds.analytic_max_abs
        min_cosine = thresholds.analytic_min_cosine
    else:
        max_relative_l2 = thresholds.snapshot_max_relative_l2
        max_abs_limit = thresholds.snapshot_max_abs
        min_cosine = thresholds.snapshot_min_cosine
    passed = (
        relative_l2 <= max_relative_l2
        and max_abs <= max_abs_limit
        and cosine >= min_cosine
    )
    return Comparison(
        absolute_l2=absolute_l2,
        relative_l2=relative_l2,
        max_abs=max_abs,
        cosine=cosine,
        norm_ratio=norm_ratio,
        reference_norm=reference_norm,
        candidate_norm=candidate_norm,
        finite=True,
        zero_safe_path=False,
        passed=passed,
    )


def base_record(
    *,
    sub_gate: str,
    case_id: str,
    provenance: Provenance,
    construction_seed: int | None,
    model_seed: int | None = None,
    layer_index: int | None = None,
    sweep_index: int | None = None,
) -> Record:
    return {
        "record_key": ":".join(
            [
                sub_gate,
                case_id,
                provenance.lane,
                "c-none" if construction_seed is None else f"c-{construction_seed}",
                "m-none" if model_seed is None else f"m-{model_seed}",
                "l-none" if layer_index is None else f"l-{layer_index}",
                "s-none" if sweep_index is None else f"s-{sweep_index}",
            ]
        ),
        "control_id": CONTROL_ID,
        "sub_gate": sub_gate,
        "case_id": case_id,
        "lane": provenance.lane,
        "device": provenance.device,
        "dtype": provenance.dtype,
        "model_seed": model_seed,
        "construction_seed": construction_seed,
        "layer_index": layer_index,
        "sweep_index": sweep_index,
        "contract_id": CONTRACT_ID,
        "implementation_schema_id": IMPLEMENTATION_SCHEMA_ID,
        "source_git_commit": provenance.source_git_commit,
        "source_git_branch": provenance.source_git_branch,
        "experiment_image": provenance.experiment_image,
        "image_revision": provenance.image_revision,
        "torch2pc_commit": provenance.torch2pc_commit,
    }


def _basis(*, device: torch.device, dtype: torch.dtype) -> torch.Tensor:
    return torch.eye(SPACE_DIMENSION, device=device, dtype=dtype)


def _geometry_metrics(channels: Sequence[torch.Tensor], zero_atol: float) -> Record:
    norms = [float(torch.linalg.vector_norm(channel).item()) for channel in channels]
    aggregate = torch.stack(tuple(channels)).sum(dim=0)
    resultant_norm = float(torch.linalg.vector_norm(aggregate).item())
    activity = float(sum(norms))
    q_value = float(sum(norm * norm for norm in norms))
    pairwise_sum = 0.0
    pairwise_cosines: list[float | None] = []
    for left_index, left in enumerate(channels):
        for right in channels[left_index + 1 :]:
            dot = float(torch.dot(left.reshape(-1), right.reshape(-1)).item())
            pairwise_sum += dot
            left_norm = float(torch.linalg.vector_norm(left).item())
            right_norm = float(torch.linalg.vector_norm(right).item())
            pairwise_cosines.append(
                None
                if left_norm <= zero_atol or right_norm <= zero_atol
                else dot / (left_norm * right_norm)
            )
    negative_interference = max(0.0, -2.0 * pairwise_sum)
    cancellation = None if q_value <= zero_atol else negative_interference / q_value
    chi = None if activity <= zero_atol else resultant_norm / activity
    active = any(norm > 100.0 * zero_atol for norm in norms)
    if not active and resultant_norm <= zero_atol:
        label = "NCZ"
    elif active and resultant_norm <= zero_atol:
        label = "ECZ"
    else:
        label = "active_non_ecz"
    return {
        "channel_norms": norms,
        "activity_a": activity,
        "resultant_r": resultant_norm,
        "q_value": q_value,
        "pairwise_p": pairwise_sum,
        "negative_interference_n": negative_interference,
        "cancellation_d": cancellation,
        "chi": chi,
        "pairwise_cosines": pairwise_cosines,
        "observed_class": label,
        "aggregate": aggregate,
    }


def run_geometry_controls(
    *,
    scope: ExecutionScope,
    provenance: Provenance,
    device: torch.device,
    dtype: torch.dtype,
) -> list[Record]:
    thresholds = thresholds_for_lane(provenance.lane)
    basis = _basis(device=device, dtype=dtype)
    records: list[Record] = []
    delta = 1e-3

    for seed in construction_seeds(scope):
        scale = scale_for_seed(seed)
        zero = torch.zeros(SPACE_DIMENSION, device=device, dtype=dtype)
        cases: list[tuple[str, list[torch.Tensor], str]] = [
            ("GEO-01-exact-ncz", [zero, zero], "NCZ"),
            ("GEO-02-two-channel-exact-ecz", [scale * basis[0], -scale * basis[0]], "ECZ"),
            (
                "GEO-03-two-channel-near-ecz",
                [scale * basis[0], -(1.0 - delta) * scale * basis[0]],
                "near_ecz_control",
            ),
            ("GEO-04-aligned", [scale * basis[0], 2.0 * scale * basis[0]], "active_non_ecz"),
            ("GEO-05-orthogonal", [scale * basis[0], scale * basis[1]], "active_non_ecz"),
            (
                "GEO-06-three-channel-120-degree-ecz",
                [
                    scale * basis[0],
                    scale * (-0.5 * basis[0] + math.sqrt(3.0) / 2.0 * basis[1]),
                    scale * (-0.5 * basis[0] - math.sqrt(3.0) / 2.0 * basis[1]),
                ],
                "ECZ",
            ),
        ]

        for case_id, channels, expected_class in cases:
            metrics = _geometry_metrics(channels, thresholds.zero_atol)
            observed_class = str(metrics["observed_class"])
            if case_id == "GEO-03-two-channel-near-ecz":
                observed_class = (
                    "near_ecz_control"
                    if float(metrics["resultant_r"]) > thresholds.zero_atol
                    else "ECZ"
                )
            expected_aggregate = torch.stack(tuple(channels)).sum(dim=0)
            comparison = compare_tensors(
                expected_aggregate,
                metrics.pop("aggregate"),
                profile="analytic_vector",
                thresholds=thresholds,
            )
            finite = comparison.finite and all(math.isfinite(value) for value in metrics["channel_norms"])
            passed = finite and comparison.passed and observed_class == expected_class
            if case_id == "GEO-02-two-channel-exact-ecz":
                passed = passed and abs(float(metrics["cancellation_d"]) - 1.0) <= thresholds.analytic_max_abs
            elif case_id == "GEO-03-two-channel-near-ecz":
                expected_chi = delta / (2.0 - delta)
                passed = passed and abs(float(metrics["chi"]) - expected_chi) <= thresholds.analytic_max_abs
            elif case_id == "GEO-04-aligned":
                passed = passed and abs(float(metrics["chi"]) - 1.0) <= thresholds.analytic_max_abs
            elif case_id == "GEO-05-orthogonal":
                passed = passed and abs(float(metrics["chi"]) - math.sqrt(2.0) / 2.0) <= thresholds.analytic_max_abs
            elif case_id == "GEO-06-three-channel-120-degree-ecz":
                cosines = [value for value in metrics["pairwise_cosines"] if value is not None]
                passed = passed and all(abs(value + 0.5) <= thresholds.analytic_max_abs for value in cosines)
            record = base_record(
                sub_gate="GEO-C0",
                case_id=case_id,
                provenance=provenance,
                construction_seed=seed,
            )
            record.update(metrics)
            record.update(comparison.to_dict())
            record.update(
                {
                    "threshold_profile": "analytic_vector",
                    "expected_class": expected_class,
                    "observed_class": observed_class,
                    "finite": finite,
                    "passed": passed,
                }
            )
            records.append(record)

        canonical = scale * basis[0] + 2.0 * scale * basis[1]
        split = [0.25 * canonical, 0.75 * canonical]
        canonical_metrics = _geometry_metrics([canonical], thresholds.zero_atol)
        split_grouped = split[0] + split[1]
        split_metrics = _geometry_metrics([split_grouped], thresholds.zero_atol)
        aggregate_comparison = compare_tensors(
            canonical_metrics.pop("aggregate"),
            split_metrics.pop("aggregate"),
            profile="analytic_vector",
            thresholds=thresholds,
        )
        scalar_fields = ("activity_a", "resultant_r", "q_value", "pairwise_p", "negative_interference_n")
        scalar_passed = all(
            abs(float(canonical_metrics[name]) - float(split_metrics[name]))
            <= thresholds.analytic_max_abs
            for name in scalar_fields
        )
        refinement_record = base_record(
            sub_gate="GEO-C0",
            case_id="GEO-07-channel-refinement-invariance",
            provenance=provenance,
            construction_seed=seed,
        )
        refinement_record.update(aggregate_comparison.to_dict())
        refinement_record.update(
            {
                "threshold_profile": "analytic_vector",
                "canonical_metrics": canonical_metrics,
                "refined_metrics": split_metrics,
                "canonical_channel_id": "self",
                "technical_part_count": 2,
                "expected_class": "active_non_ecz",
                "observed_class": split_metrics["observed_class"],
                "finite": aggregate_comparison.finite,
                "passed": aggregate_comparison.passed and scalar_passed,
            }
        )
        records.append(refinement_record)

        active_floor = 100.0 * thresholds.zero_atol
        zero_comparison = compare_tensors(
            zero,
            zero,
            profile="analytic_vector",
            thresholds=thresholds,
        )
        negative_comparison = compare_tensors(
            zero,
            active_floor * basis[0],
            profile="analytic_vector",
            thresholds=thresholds,
        )
        zero_record = base_record(
            sub_gate="GEO-C0",
            case_id="GEO-08-zero-safe-comparison",
            provenance=provenance,
            construction_seed=seed,
        )
        zero_record.update(zero_comparison.to_dict())
        zero_record.update(
            {
                "threshold_profile": "algebraic_zero",
                "negative_control_comparison_passed": negative_comparison.passed,
                "negative_control_finite": negative_comparison.finite,
                "negative_control_cosine": negative_comparison.cosine,
                "expected_class": "zero_safe_control",
                "observed_class": "zero_safe_control",
                "finite": zero_comparison.finite and negative_comparison.finite,
                "passed": zero_comparison.passed and not negative_comparison.passed and negative_comparison.cosine is None,
            }
        )
        records.append(zero_record)

    return records


def _transport_record(
    *,
    case_id: str,
    seed: int,
    provenance: Provenance,
    reference: torch.Tensor,
    candidate: torch.Tensor,
    source: torch.Tensor,
    expected_class: str,
    observed_class: str,
    thresholds: ThresholdProfile,
    extra: Mapping[str, Any] | None = None,
) -> Record:
    comparison = compare_tensors(
        reference,
        candidate,
        profile="analytic_vector",
        thresholds=thresholds,
    )
    source_norm = float(torch.linalg.vector_norm(source).item())
    candidate_norm = float(torch.linalg.vector_norm(candidate).item())
    gamma = None if source_norm <= thresholds.zero_atol else candidate_norm / source_norm
    record = base_record(
        sub_gate="TR-C0",
        case_id=case_id,
        provenance=provenance,
        construction_seed=seed,
    )
    record.update(comparison.to_dict())
    record.update(
        {
            "threshold_profile": "analytic_vector",
            "source_norm": source_norm,
            "transported_norm": candidate_norm,
            "gamma": gamma,
            "expected_class": expected_class,
            "observed_class": observed_class,
            "finite": comparison.finite,
            "passed": comparison.passed and expected_class == observed_class,
        }
    )
    if extra:
        record.update(extra)
        record["passed"] = bool(record["passed"] and extra.get("extra_passed", True))
    return record


def run_transport_controls(
    *,
    scope: ExecutionScope,
    provenance: Provenance,
    device: torch.device,
    dtype: torch.dtype,
) -> list[Record]:
    thresholds = thresholds_for_lane(provenance.lane)
    basis = _basis(device=device, dtype=dtype)
    identity = torch.eye(SPACE_DIMENSION, device=device, dtype=dtype)
    records: list[Record] = []

    for seed in construction_seeds(scope):
        scale = scale_for_seed(seed)
        direction = scale * (basis[0] + 0.5 * basis[3] - 0.25 * basis[7])
        for coefficient in (1.0, 0.5, 0.1, 0.01, 0.0):
            operator = coefficient * identity
            candidate = operator.T @ direction
            expected = coefficient * direction
            observed_class = (
                "TNZ"
                if float(torch.linalg.vector_norm(candidate).item()) <= thresholds.zero_atol
                else "transported_active"
            )
            records.append(
                _transport_record(
                    case_id=f"TR-01-scaled-identity-c-{coefficient:g}",
                    seed=seed,
                    provenance=provenance,
                    reference=expected,
                    candidate=candidate,
                    source=direction,
                    expected_class="TNZ" if coefficient == 0.0 else "transported_active",
                    observed_class=observed_class,
                    thresholds=thresholds,
                    extra={
                        "operator_scale": coefficient,
                        "operator_norm": abs(coefficient),
                        "expected_gamma": abs(coefficient),
                        "extra_passed": abs(
                            (0.0 if coefficient == 0.0 else float(torch.linalg.vector_norm(candidate).item()) / float(torch.linalg.vector_norm(direction).item()))
                            - abs(coefficient)
                        )
                        <= thresholds.analytic_max_abs,
                    },
                )
            )

        projection = torch.diag(
            torch.tensor([1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], device=device, dtype=dtype)
        )
        source_tnz = scale * basis[2]
        candidate_tnz = projection.T @ source_tnz
        records.append(
            _transport_record(
                case_id="TR-02-exact-tnz-nonzero-operator",
                seed=seed,
                provenance=provenance,
                reference=torch.zeros_like(source_tnz),
                candidate=candidate_tnz,
                source=source_tnz,
                expected_class="TNZ",
                observed_class="TNZ" if float(torch.linalg.vector_norm(candidate_tnz).item()) <= thresholds.zero_atol else "transported_active",
                thresholds=thresholds,
                extra={"operator_norm": 1.0, "extra_passed": True},
            )
        )

        source_active = scale * basis[0]
        candidate_active = projection.T @ source_active
        records.append(
            _transport_record(
                case_id="TR-03-active-projection-control",
                seed=seed,
                provenance=provenance,
                reference=source_active,
                candidate=candidate_active,
                source=source_active,
                expected_class="transported_active",
                observed_class="transported_active" if float(torch.linalg.vector_norm(candidate_active).item()) > thresholds.zero_atol else "TNZ",
                thresholds=thresholds,
            )
        )

        orthogonal = identity.clone()
        orthogonal[0, 0] = 0.0
        orthogonal[1, 1] = 0.0
        orthogonal[1, 0] = 1.0
        orthogonal[0, 1] = -1.0
        x = scale * (basis[0] + 2.0 * basis[1] + 0.5 * basis[4])
        source_orthogonal = scale * (0.5 * basis[0] - basis[1] + basis[6])
        candidate_orthogonal = orthogonal.T @ source_orthogonal
        adjoint_left = float(torch.dot(orthogonal @ x, source_orthogonal).item())
        adjoint_right = float(torch.dot(x, candidate_orthogonal).item())
        norm_ratio = float(torch.linalg.vector_norm(candidate_orthogonal).item()) / float(
            torch.linalg.vector_norm(source_orthogonal).item()
        )
        records.append(
            _transport_record(
                case_id="TR-04-orthogonal-norm-preserving",
                seed=seed,
                provenance=provenance,
                reference=candidate_orthogonal,
                candidate=candidate_orthogonal,
                source=source_orthogonal,
                expected_class="transported_active",
                observed_class="transported_active",
                thresholds=thresholds,
                extra={
                    "adjoint_left": adjoint_left,
                    "adjoint_right": adjoint_right,
                    "norm_preservation_ratio": norm_ratio,
                    "extra_passed": abs(adjoint_left - adjoint_right) <= thresholds.analytic_max_abs
                    and abs(norm_ratio - 1.0) <= thresholds.analytic_max_abs,
                },
            )
        )

        j1 = torch.diag(torch.linspace(0.8, 1.1, SPACE_DIMENSION, device=device, dtype=dtype))
        j2 = orthogonal
        j3 = torch.diag(torch.linspace(1.2, 0.9, SPACE_DIMENSION, device=device, dtype=dtype))
        source_chain = scale * (basis[0] + basis[2] - 0.5 * basis[5])
        q_sequential = j1.T @ (j2.T @ (j3.T @ source_chain))
        direct_operator = j3 @ j2 @ j1
        q_direct = direct_operator.T @ source_chain
        direct_gain = float(torch.linalg.vector_norm(q_direct).item()) / float(torch.linalg.vector_norm(source_chain).item())
        local_gains: list[float] = []
        current = source_chain
        for operator in (j3, j2, j1):
            next_value = operator.T @ current
            local_gains.append(float(torch.linalg.vector_norm(next_value).item()) / float(torch.linalg.vector_norm(current).item()))
            current = next_value
        records.append(
            _transport_record(
                case_id="TR-05-direct-cumulative-transport",
                seed=seed,
                provenance=provenance,
                reference=q_direct,
                candidate=q_sequential,
                source=source_chain,
                expected_class="transported_active",
                observed_class="transported_active",
                thresholds=thresholds,
                extra={
                    "direct_cumulative_gain": direct_gain,
                    "product_local_directional_gains": math.prod(local_gains),
                    "extra_passed": True,
                },
            )
        )

        tnz_transport = projection.T @ source_tnz
        tnz_self = scale * basis[0]
        tnz_aggregate = tnz_self - tnz_transport
        ecz_transport = projection.T @ source_active
        ecz_upper = -ecz_transport
        ecz_self = -ecz_upper
        ecz_aggregate = ecz_self + ecz_upper
        tnz_stage = "TNZ" if float(torch.linalg.vector_norm(tnz_transport).item()) <= thresholds.zero_atol else "transported_active"
        tnz_aggregation = _geometry_metrics([tnz_self, -tnz_transport], thresholds.zero_atol)["observed_class"]
        ecz_stage = "transported_active" if float(torch.linalg.vector_norm(ecz_transport).item()) > thresholds.zero_atol else "TNZ"
        ecz_aggregation = _geometry_metrics([ecz_self, ecz_upper], thresholds.zero_atol)["observed_class"]
        zero_comparison = compare_tensors(
            torch.zeros_like(ecz_aggregate),
            ecz_aggregate,
            profile="analytic_vector",
            thresholds=thresholds,
        )
        separation_record = base_record(
            sub_gate="TR-C0",
            case_id="TR-06-tnz-ecz-separation",
            provenance=provenance,
            construction_seed=seed,
        )
        separation_record.update(zero_comparison.to_dict())
        separation_record.update(
            {
                "threshold_profile": "analytic_vector",
                "tnz_transport_class": tnz_stage,
                "tnz_aggregation_class": tnz_aggregation,
                "tnz_aggregate_norm": float(torch.linalg.vector_norm(tnz_aggregate).item()),
                "ecz_transport_class": ecz_stage,
                "ecz_aggregation_class": ecz_aggregation,
                "ecz_aggregate_norm": float(torch.linalg.vector_norm(ecz_aggregate).item()),
                "finite": zero_comparison.finite,
                "passed": zero_comparison.passed
                and tnz_stage == "TNZ"
                and tnz_aggregation == "active_non_ecz"
                and ecz_stage == "transported_active"
                and ecz_aggregation == "ECZ",
            }
        )
        records.append(separation_record)

    return records


def _temporal_matrices(seed: int, *, device: torch.device, dtype: torch.dtype) -> list[torch.Tensor]:
    scale = scale_for_seed(seed)
    matrices: list[torch.Tensor] = []
    for layer in range(DEPTH):
        diagonal = torch.linspace(
            0.72 + 0.01 * layer,
            0.91 + 0.01 * layer,
            SPACE_DIMENSION,
            device=device,
            dtype=dtype,
        )
        diagonal = diagonal * (1.0 + 0.01 * scale)
        matrices.append(torch.diag(diagonal))
    return matrices


def _temporal_wave(
    matrices: Sequence[torch.Tensor],
    source: torch.Tensor,
    *,
    sweeps: int,
    provenance: Provenance,
    construction_seed: int,
    record_events: bool,
) -> tuple[list[Record], torch.Tensor, list[int | None], str]:
    thresholds = thresholds_for_lane(provenance.lane)
    epsilon = [torch.zeros_like(source) for _ in range(DEPTH + 1)]
    epsilon[DEPTH] = source.clone()
    state_versions = [0 for _ in range(DEPTH)]
    first_active: list[int | None] = [None for _ in range(DEPTH)]
    events: list[Record] = []
    jacobian_version = tensor_fingerprint(matrices)
    endpoint_signal = torch.zeros_like(source)

    for sweep in range(1, sweeps + 1):
        epsilon_before = [value.clone() for value in epsilon]
        next_epsilon = [value.clone() for value in epsilon]
        for state_layer in range(DEPTH - 1, -1, -1):
            upper = matrices[state_layer].T @ epsilon_before[state_layer + 1]
            dv = upper.clone()
            epsilon_before_norm = float(torch.linalg.vector_norm(epsilon_before[state_layer]).item())
            upper_norm = float(torch.linalg.vector_norm(upper).item())
            dv_norm = float(torch.linalg.vector_norm(dv).item())
            if first_active[state_layer] is None and dv_norm > 100.0 * thresholds.zero_atol:
                first_active[state_layer] = sweep
            version_before = state_versions[state_layer]
            state_versions[state_layer] += 1
            version_after = state_versions[state_layer]
            next_epsilon[state_layer] = upper
            if state_layer == 1:
                endpoint_signal = epsilon_before[state_layer].clone()
            if record_events:
                expected_first = DEPTH - state_layer
                record = base_record(
                    sub_gate="TMP-C0",
                    case_id="TMP-01-primary-wave-event",
                    provenance=provenance,
                    construction_seed=construction_seed,
                    layer_index=state_layer,
                    sweep_index=sweep,
                )
                record.update(
                    {
                        "epsilon_before_update_norm": epsilon_before_norm,
                        "transported_upper_term_norm": upper_norm,
                        "local_error_norm": epsilon_before_norm,
                        "dv_norm": dv_norm,
                        "state_version_before": version_before,
                        "state_version_after": version_after,
                        "jacobian_version_id": jacobian_version,
                        "expected_first_active_sweep": expected_first,
                        "observed_first_active_sweep": None,
                        "ordering_flag": version_after == version_before + 1,
                        "finite": all(
                            math.isfinite(value)
                            for value in (epsilon_before_norm, upper_norm, dv_norm)
                        ),
                        "passed": True,
                    }
                )
                events.append(record)
        epsilon = next_epsilon

    if record_events:
        for record in events:
            layer = int(record["layer_index"])
            observed = first_active[layer]
            record["observed_first_active_sweep"] = observed
            record["passed"] = bool(
                record["passed"]
                and record["finite"]
                and record["ordering_flag"]
                and observed == record["expected_first_active_sweep"]
                and record["jacobian_version_id"] == jacobian_version
            )
    return events, endpoint_signal, first_active, jacobian_version


def run_temporal_controls(
    *,
    scope: ExecutionScope,
    provenance: Provenance,
    device: torch.device,
    dtype: torch.dtype,
) -> tuple[list[Record], list[Record]]:
    thresholds = thresholds_for_lane(provenance.lane)
    basis = _basis(device=device, dtype=dtype)
    event_records: list[Record] = []
    summary_records: list[Record] = []

    for seed in construction_seeds(scope):
        scale = scale_for_seed(seed)
        matrices = _temporal_matrices(seed, device=device, dtype=dtype)
        source = scale * (basis[0] - 0.5 * basis[2] + 0.25 * basis[7])
        h0 = scale * (basis[1] + 0.25 * basis[4])
        full_error = source
        for matrix in reversed(matrices[1:]):
            full_error = matrix.T @ full_error
        bp_gradient = torch.outer(full_error, h0)

        primary_events, signal_l6, first_active, jacobian_version = _temporal_wave(
            matrices,
            source,
            sweeps=DEPTH,
            provenance=provenance,
            construction_seed=seed,
            record_events=True,
        )
        _, signal_l5, _, _ = _temporal_wave(
            matrices,
            source,
            sweeps=DEPTH - 1,
            provenance=provenance,
            construction_seed=seed,
            record_events=False,
        )
        _, signal_l7, _, _ = _temporal_wave(
            matrices,
            source,
            sweeps=DEPTH + 1,
            provenance=provenance,
            construction_seed=seed,
            record_events=False,
        )
        gradient_l5 = torch.outer(signal_l5, h0)
        gradient_l6 = torch.outer(signal_l6, h0)
        gradient_l7 = torch.outer(signal_l7, h0)
        comparison_l6_bp = compare_tensors(
            bp_gradient,
            gradient_l6,
            profile="implementation_snapshot",
            thresholds=thresholds,
        )
        comparison_l7_bp = compare_tensors(
            bp_gradient,
            gradient_l7,
            profile="implementation_snapshot",
            thresholds=thresholds,
        )
        comparison_l7_l6 = compare_tensors(
            gradient_l6,
            gradient_l7,
            profile="implementation_snapshot",
            thresholds=thresholds,
        )
        difference_l5 = float(torch.linalg.vector_norm(gradient_l5 - bp_gradient).item())
        bp_norm = float(torch.linalg.vector_norm(bp_gradient).item())
        relative_l5 = difference_l5 / bp_norm if bp_norm > thresholds.zero_atol else math.inf
        event_records.extend(primary_events)
        summary = base_record(
            sub_gate="TMP-C0",
            case_id="TMP-02-endpoint-summary",
            provenance=provenance,
            construction_seed=seed,
        )
        summary.update(
            {
                "depth": DEPTH,
                "eta": 1.0,
                "initialization": "feed_forward",
                "primary_trace_sweeps": DEPTH,
                "first_active_sweeps": first_active,
                "expected_first_active_sweeps": [DEPTH - layer for layer in range(DEPTH)],
                "jacobian_version_id": jacobian_version,
                "fixed_jacobian_version": True,
                "n_l_minus_1_first_block_relative_l2": relative_l5,
                "n_l_minus_1_separation_floor": thresholds.temporal_separation_floor,
                "n_l_minus_1_insufficient_control_passed": relative_l5 > thresholds.temporal_separation_floor,
                "n_l_vs_bp": comparison_l6_bp.to_dict(),
                "n_l_plus_1_vs_bp": comparison_l7_bp.to_dict(),
                "n_l_plus_1_vs_n_l": comparison_l7_l6.to_dict(),
                "finite": all(
                    comparison.finite
                    for comparison in (comparison_l6_bp, comparison_l7_bp, comparison_l7_l6)
                )
                and math.isfinite(relative_l5),
                "passed": relative_l5 > thresholds.temporal_separation_floor
                and comparison_l6_bp.passed
                and comparison_l7_bp.passed
                and comparison_l7_l6.passed
                and first_active == [DEPTH - layer for layer in range(DEPTH)],
            }
        )
        summary_records.append(summary)

    return event_records, summary_records


def _linear_blocks(
    seed: int,
    *,
    device: torch.device,
    dtype: torch.dtype,
) -> tuple[list[torch.Tensor], list[torch.Tensor], list[torch.Tensor]]:
    scale = scale_for_seed(seed)
    matrices: list[torch.Tensor] = []
    inputs: list[torch.Tensor] = []
    cotangents: list[torch.Tensor] = []
    basis = _basis(device=device, dtype=dtype)
    for block in range(4):
        diagonal = torch.linspace(
            0.6 + 0.03 * block,
            1.0 + 0.02 * block,
            SPACE_DIMENSION,
            device=device,
            dtype=dtype,
        )
        matrix = torch.diag(diagonal)
        matrix = matrix + 0.01 * torch.roll(torch.eye(SPACE_DIMENSION, device=device, dtype=dtype), shifts=1, dims=1)
        matrices.append(matrix)
        inputs.append((scale * (basis[block] + 0.2 * basis[(block + 3) % SPACE_DIMENSION])).clone())
        cotangents.append(scale * (basis[(block + 1) % SPACE_DIMENSION] - 0.3 * basis[(block + 5) % SPACE_DIMENSION]))
    return matrices, inputs, cotangents


def _autograd_candidates(
    functions: Sequence[Callable[[torch.Tensor], torch.Tensor]],
    raw_inputs: Sequence[torch.Tensor],
    cotangents: Sequence[torch.Tensor],
    *,
    chunks: Sequence[Sequence[int]],
) -> tuple[list[torch.Tensor], list[torch.Tensor], list[torch.Tensor]]:
    leaves = [value.detach().clone().requires_grad_(True) for value in raw_inputs]
    outputs = [function(value) for function, value in zip(functions, leaves, strict=True)]
    isolated: list[torch.Tensor] = []
    for output, leaf, cotangent in zip(outputs, leaves, cotangents, strict=True):
        gradient = torch.autograd.grad(
            output,
            leaf,
            grad_outputs=cotangent,
            retain_graph=True,
            allow_unused=False,
        )[0]
        isolated.append(gradient)
    composite = list(
        torch.autograd.grad(
            tuple(outputs),
            tuple(leaves),
            grad_outputs=tuple(cotangents),
            retain_graph=True,
            allow_unused=False,
        )
    )
    chunked: list[torch.Tensor | None] = [None for _ in leaves]
    for chunk_index, indices in enumerate(chunks):
        gradients = torch.autograd.grad(
            tuple(outputs[index] for index in indices),
            tuple(leaves[index] for index in indices),
            grad_outputs=tuple(cotangents[index] for index in indices),
            retain_graph=chunk_index < len(chunks) - 1,
            allow_unused=False,
        )
        for index, gradient in zip(indices, gradients, strict=True):
            chunked[index] = gradient
    if any(value is None for value in chunked):
        raise RuntimeError("Chunked VJP did not produce every block gradient")
    return isolated, composite, [value for value in chunked if value is not None]


def run_materialized_block_probe(
    *,
    scope: ExecutionScope,
    provenance: Provenance,
    device: torch.device,
    dtype: torch.dtype,
) -> list[Record]:
    thresholds = thresholds_for_lane(provenance.lane)
    records: list[Record] = []
    for seed in construction_seeds(scope):
        matrices, raw_inputs, cotangents = _linear_blocks(seed, device=device, dtype=dtype)
        functions = [lambda value, matrix=matrix: matrix @ value for matrix in matrices]
        isolated, composite, chunked = _autograd_candidates(
            functions,
            raw_inputs,
            cotangents,
            chunks=((0, 1), (2, 3)),
        )
        snapshot_fingerprint = tensor_fingerprint([*raw_inputs, *cotangents, *matrices])
        for block_index, (matrix, raw_input, cotangent) in enumerate(
            zip(matrices, raw_inputs, cotangents, strict=True)
        ):
            jacobian = torch.autograd.functional.jacobian(
                lambda value, matrix=matrix: matrix @ value,
                raw_input,
                create_graph=False,
                strict=True,
            )
            explicit = jacobian.T @ cotangent
            isolated_comparison = compare_tensors(
                explicit,
                isolated[block_index],
                profile="implementation_snapshot",
                thresholds=thresholds,
            )
            for candidate_name, candidate, call_count in (
                ("composite_vjp", composite[block_index], 1),
                ("chunked_composite_vjp", chunked[block_index], 2),
            ):
                comparison = compare_tensors(
                    explicit,
                    candidate,
                    profile="implementation_snapshot",
                    thresholds=thresholds,
                )
                record = base_record(
                    sub_gate="JAC-C0",
                    case_id=f"JAC-01-materialized-{candidate_name}",
                    provenance=provenance,
                    construction_seed=seed,
                    layer_index=block_index,
                )
                record.update(comparison.to_dict())
                record.update(
                    {
                        "probe_family": "materialized_oracle",
                        "candidate_form": candidate_name,
                        "block_count": 4,
                        "vjp_call_count": call_count,
                        "isolated_vjp_call_count": 4,
                        "input_shape": list(raw_input.shape),
                        "output_shape": list((matrix @ raw_input).shape),
                        "cotangent_shape": list(cotangent.shape),
                        "graph_island_count": 4,
                        "allow_unused": False,
                        "missing_gradient_count": 0,
                        "snapshot_fingerprint": snapshot_fingerprint,
                        "model_state_fingerprint": None,
                        "isolated_vs_explicit": isolated_comparison.to_dict(),
                        "finite": comparison.finite and isolated_comparison.finite,
                        "passed": comparison.passed and isolated_comparison.passed,
                    }
                )
                records.append(record)
    return records


def _snapshot_model_blocks(
    model: nn.Sequential,
    synthetic_input: torch.Tensor,
) -> tuple[list[nn.Module], list[torch.Tensor], list[torch.Tensor]]:
    blocks = list(model.children())
    if len(blocks) != DEPTH:
        raise ValueError(f"lenet_classic must expose {DEPTH} top-level blocks")
    block_inputs: list[torch.Tensor] = []
    block_outputs: list[torch.Tensor] = []
    current = synthetic_input
    with torch.no_grad():
        for block in blocks:
            block_inputs.append(current.detach().clone())
            current = block(current)
            block_outputs.append(current.detach().clone())
    return blocks, block_inputs, block_outputs


def run_lenet_block_probe(
    *,
    scope: ExecutionScope,
    provenance: Provenance,
    device: torch.device,
    dtype: torch.dtype,
    model_factory: Callable[[int], nn.Sequential],
) -> list[Record]:
    thresholds = thresholds_for_lane(provenance.lane)
    records: list[Record] = []
    raw_synthetic_input = torch.linspace(
        -1.0,
        1.0,
        8 * 28 * 28,
        device=device,
        dtype=dtype,
    ).reshape(8, 1, 28, 28)
    synthetic_input = torch.nn.functional.pad(
        raw_synthetic_input,
        (2, 2, 2, 2),
    )

    for seed in model_seeds(scope):
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        model = model_factory(seed).to(device=device, dtype=dtype)
        model.eval()
        state_fingerprint_before = model_state_fingerprint(model)
        rng_before = rng_fingerprint()
        blocks, block_inputs, expected_outputs = _snapshot_model_blocks(model, synthetic_input)
        functions = [lambda value, block=block: block(value) for block in blocks]
        cotangents = [
            torch.linspace(
                -0.5,
                0.5,
                output.numel(),
                device=device,
                dtype=dtype,
            ).reshape_as(output)
            for output in expected_outputs
        ]
        isolated, composite, chunked = _autograd_candidates(
            functions,
            block_inputs,
            cotangents,
            chunks=((0, 1, 2), (3, 4, 5)),
        )
        rng_after = rng_fingerprint()
        state_fingerprint_after = model_state_fingerprint(model)
        snapshot_fingerprint = tensor_fingerprint([*block_inputs, *expected_outputs, *cotangents])

        for block_index in range(DEPTH):
            for candidate_name, candidate, call_count in (
                ("composite_vjp", composite[block_index], 1),
                ("chunked_composite_vjp", chunked[block_index], 2),
            ):
                comparison = compare_tensors(
                    isolated[block_index],
                    candidate,
                    profile="implementation_snapshot",
                    thresholds=thresholds,
                )
                record = base_record(
                    sub_gate="JAC-C0",
                    case_id=f"JAC-02-lenet-{candidate_name}",
                    provenance=provenance,
                    construction_seed=None,
                    model_seed=seed,
                    layer_index=block_index,
                )
                record.update(comparison.to_dict())
                record.update(
                    {
                        "probe_family": "lenet_classic_snapshot",
                        "candidate_form": candidate_name,
                        "block_count": DEPTH,
                        "vjp_call_count": call_count,
                        "isolated_vjp_call_count": DEPTH,
                        "input_shape": list(block_inputs[block_index].shape),
                        "output_shape": list(expected_outputs[block_index].shape),
                        "cotangent_shape": list(cotangents[block_index].shape),
                        "graph_island_count": DEPTH,
                        "allow_unused": False,
                        "missing_gradient_count": 0,
                        "snapshot_fingerprint": snapshot_fingerprint,
                        "registered_raw_input_shape": list(
                            raw_synthetic_input.shape
                        ),
                        "model_input_shape_after_canonical_pad": list(
                            synthetic_input.shape
                        ),
                        "canonical_input_preprocessing": "constant_pad_2",
                        "model_state_fingerprint": state_fingerprint_before,
                        "model_state_fingerprint_after": state_fingerprint_after,
                        "rng_fingerprint_before": rng_before,
                        "rng_fingerprint_after": rng_after,
                        "finite": comparison.finite,
                        "passed": comparison.passed
                        and state_fingerprint_before == state_fingerprint_after
                        and rng_before == rng_after,
                    }
                )
                records.append(record)
    return records


def run_pnz_controls(
    *,
    scope: ExecutionScope,
    provenance: Provenance,
    device: torch.device,
    dtype: torch.dtype,
) -> list[Record]:
    thresholds = thresholds_for_lane(provenance.lane)
    operator = torch.tensor(
        [[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]],
        device=device,
        dtype=dtype,
    )
    records: list[Record] = []
    for seed in construction_seeds(scope):
        scale = scale_for_seed(seed)
        source = torch.tensor([0.0, 0.0, scale], device=device, dtype=dtype)
        candidate = operator.T @ source
        comparison = compare_tensors(
            torch.zeros(2, device=device, dtype=dtype),
            candidate,
            profile="analytic_vector",
            thresholds=thresholds,
        )
        rank = int(torch.linalg.matrix_rank(operator).item())
        source_norm = float(torch.linalg.vector_norm(source).item())
        record = base_record(
            sub_gate="PNZ-L0",
            case_id="PNZ-01-linear-parameter-null",
            provenance=provenance,
            construction_seed=seed,
        )
        record.update(comparison.to_dict())
        record.update(
            {
                "operator_rank": rank,
                "expected_rank": 2,
                "source_norm": source_norm,
                "expected_class": "PNZ",
                "observed_class": "PNZ" if float(torch.linalg.vector_norm(candidate).item()) <= thresholds.zero_atol else "parameter_active",
                "finite": comparison.finite,
                "passed": comparison.passed
                and rank == 2
                and source_norm > 100.0 * thresholds.zero_atol,
            }
        )
        records.append(record)
    return records


def expected_counts(scope: ExecutionScope) -> dict[str, int]:
    multiplier = 1 if scope == "smoke" else 3
    return {
        "geometry_records": 8 * multiplier,
        "transport_records": 10 * multiplier,
        "temporal_event_records": 36 * multiplier,
        "temporal_summary_records": multiplier,
        "block_probe_records": 20 * multiplier,
        "pnz_records": multiplier,
    }


def validate_record_collection(
    records: Sequence[Record],
    *,
    expected_count: int,
    sub_gate: str,
) -> bool:
    keys = [str(record.get("record_key", "")) for record in records]
    return (
        len(records) == expected_count
        and len(set(keys)) == len(keys)
        and all(keys)
        and all(record.get("sub_gate") == sub_gate for record in records)
        and all(record.get("finite") is True for record in records)
        and all(record.get("passed") is True for record in records)
    )


def build_summary(
    *,
    scope: ExecutionScope,
    provenance: Provenance,
    contract_digest: str,
    construction_registry_digest: str,
    threshold_registry_digest: str,
    geometry_records: Sequence[Record],
    transport_records: Sequence[Record],
    temporal_events: Sequence[Record],
    temporal_summary: Sequence[Record],
    block_probe_records: Sequence[Record],
    pnz_records: Sequence[Record],
) -> Record:
    counts = expected_counts(scope)
    geo_passed = validate_record_collection(
        geometry_records,
        expected_count=counts["geometry_records"],
        sub_gate="GEO-C0",
    )
    tr_passed = validate_record_collection(
        transport_records,
        expected_count=counts["transport_records"],
        sub_gate="TR-C0",
    )
    tmp_passed = validate_record_collection(
        temporal_events,
        expected_count=counts["temporal_event_records"],
        sub_gate="TMP-C0",
    ) and validate_record_collection(
        temporal_summary,
        expected_count=counts["temporal_summary_records"],
        sub_gate="TMP-C0",
    )
    jac_passed = validate_record_collection(
        block_probe_records,
        expected_count=counts["block_probe_records"],
        sub_gate="JAC-C0",
    )
    pnz_passed = validate_record_collection(
        pnz_records,
        expected_count=counts["pnz_records"],
        sub_gate="PNZ-L0",
    )
    core_passed = geo_passed and tr_passed and tmp_passed and jac_passed
    return {
        "control_id": CONTROL_ID,
        "contract_id": CONTRACT_ID,
        "implementation_schema_id": IMPLEMENTATION_SCHEMA_ID,
        "scope": scope,
        "lane": provenance.lane,
        "device": provenance.device,
        "dtype": provenance.dtype,
        "source_git_commit": provenance.source_git_commit,
        "source_git_branch": provenance.source_git_branch,
        "experiment_image": provenance.experiment_image,
        "image_revision": provenance.image_revision,
        "torch2pc_commit": provenance.torch2pc_commit,
        "contract_digest": contract_digest,
        "construction_registry_digest": construction_registry_digest,
        "threshold_registry_digest": threshold_registry_digest,
        "expected_counts": counts,
        "observed_counts": {
            "geometry_records": len(geometry_records),
            "transport_records": len(transport_records),
            "temporal_event_records": len(temporal_events),
            "temporal_summary_records": len(temporal_summary),
            "block_probe_records": len(block_probe_records),
            "pnz_records": len(pnz_records),
        },
        "geo_c0_passed": geo_passed,
        "tr_c0_passed": tr_passed,
        "tmp_c0_passed": tmp_passed,
        "jac_c0_passed": jac_passed,
        "core_passed": core_passed,
        "pnz_l0_passed": pnz_passed,
        "si_ma0_open": core_passed,
        "passed": core_passed,
        "claim_boundary": (
            "This deterministic gate validates the registered correction-geometry, "
            "state-error transport, FixedPred temporal-wave, and block-VJP controls. "
            "It does not reconstruct actual Strict.state_inference, estimate training "
            "prevalence, establish next-sweep utility, or authorize active control."
        ),
    }


def load_contract(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError("Mechanism-controls contract must be a JSON object")
    validate_contract(value)
    return value
