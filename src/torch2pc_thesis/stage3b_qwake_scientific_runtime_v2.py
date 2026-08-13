"""Embedded scientific executor for the superseding QW-5 image.

The executor uses only preregistered QWake-FP/LC4 primitives.  Live stages
reconstruct bounded FixedPred frontiers from exact data bindings, collect the
frozen A0/A1/A2 observations, run the finite analytic registry, compare the
registered analytic completion against the exact suffix, attach post-action
oracle labels, and seal deterministic artifacts.  C2 remains strictly offline.

Importing this module performs no scientific effect.  Filesystem/dataset/model
work occurs only through :func:`execute_scientific_campaign` after an exact
request and one-shot authorization have been verified.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import struct
import time
from dataclasses import asdict, dataclass, is_dataclass, replace
from enum import StrEnum
from pathlib import Path
from typing import Any, Final, cast

import numpy as np
import torch
from torch import Tensor, nn
from torch.nn import functional as F

from torch2pc_thesis.models import build_model
from torch2pc_thesis.stage3b_qwake_core import (
    ROLE_CAPABILITY_ALLOWLIST,
    AnalyticClass,
    AnalyticOutcome,
    CampaignRole,
    Capability,
    EdgeMeasurement,
    ExecutionContext,
    FrontierAction,
    FrontierActionKind,
    ObservationLevel,
    OracleLabel,
    PermissionSet,
    Provenance,
    ReceiptKind,
    ReceiptReference,
)
from torch2pc_thesis.stage3b_qwake_fp_pipeline import (
    ABLATION_REGISTRY,
    BASELINE_REGISTRY,
    BaselineConfiguration,
    CostCategory,
    EvaluationClass,
    EvaluationSummary,
    FrozenAnalyticOutput,
    FrozenFeatureVector,
    FrozenPolicyManifest,
    MeasuredEdge,
    PipelinePlan,
    PolicyPredicateKind,
    PolicyRule,
    SealedTrajectoryDataset,
    TrajectorySnapshotRecord,
    analyze_opportunity,
    apply_ablation,
    build_feature_vector,
    canonical_value_from_json,
    evaluate_baseline,
    evaluate_policy,
    plan_component,
)
from torch2pc_thesis.stage3b_qwake_fp_spec import (
    ANALYTIC_REGISTRY,
    QWAKE_FP_SPECIAL_CASE_CONTRACT,
    QWakeFPAnalyticId,
    QWakeFPBaselineId,
)
from torch2pc_thesis.stage3b_qwake_lc4_bounded import (
    FixedPredFrontier,
    analytic_wavefront_completion,
    capture_fixedpred_frontier,
    capture_opaque_state,
    compare_required_responses,
    complete_exact_suffix,
    materialize_required_response,
    preserve_outer_rng,
)
from torch2pc_thesis.stage3b_qwake_scientific_campaign import (
    ArtifactBinding,
    ScientificBatchSpec,
    ScientificCampaignAuthorization,
    ScientificCampaignError,
    ScientificCampaignRequest,
    ScientificDatasetBinding,
    ScientificHostClaim,
    canonical_train_dataset_asset_paths,
    load_scientific_host_claim,
)
from torch2pc_thesis.stage3b_qwake_scientific_identity_v2 import (
    SOURCE_COMMIT_ENV,
    ScientificRuntimeIdentity,
    ScientificRuntimeIdentityError,
    runtime_identity_from_environment,
    verify_runtime_manifest,
)

_SAMPLE_PREFIXES: Final = (32, 128, 256)
_CONTRACT_ID: Final = QWAKE_FP_SPECIAL_CASE_CONTRACT.contract_id
_COMPARISON_PROFILE_ID: Final = "rocm_float32_canonical"
_COST_PROFILE_ID: Final = "shadow_mechanism_v1"
_HOST_CLAIM_FILENAME: Final = "host-claim.json"
_PREDECESSOR_COMPATIBILITY_CONTRACT_ID: Final = (
    "qwake-scientific-predecessor-lineage-v1"
)
_RUNTIME_REQUIRED_PATHS: Final = (
    "Dockerfile.qwake-scientific",
    "requirements/qwake-scientific-runtime.txt",
    "scripts/container_entrypoint.sh",
    "scripts/run_stage3b_qwake_scientific_campaign_v2.py",
    "scripts/verify_stage3b_qwake_scientific_build_context_v2.py",
    "scripts/verify_stage3b_qwake_scientific_runtime_identity_v2.py",
    "src/torch2pc_thesis/__init__.py",
    "src/torch2pc_thesis/models.py",
    "src/torch2pc_thesis/stage3b_qwake_core.py",
    "src/torch2pc_thesis/stage3b_qwake_fp_pipeline.py",
    "src/torch2pc_thesis/stage3b_qwake_fp_spec.py",
    "src/torch2pc_thesis/stage3b_qwake_lc4_bounded.py",
    "src/torch2pc_thesis/stage3b_qwake_scientific_campaign.py",
    "src/torch2pc_thesis/stage3b_qwake_scientific_identity_v2.py",
    "src/torch2pc_thesis/stage3b_qwake_scientific_runtime_v2.py",
)


class ScientificRuntimeError(RuntimeError):
    """Raised when an authorized scientific execution violates its contract."""


@dataclass(frozen=True)
class CampaignExecutionReceipt:
    """Canonical terminal receipt for one campaign execution attempt."""

    schema_version: int
    role: CampaignRole
    protocol_receipt_kind: ReceiptKind | None
    source_commit: str
    request_sha256: str
    authorization_sha256: str
    image_digest: str
    output_root: str
    status: str
    primary_artifact_name: str
    primary_artifact_sha256: str
    artifact_sha256s: tuple[tuple[str, str], ...]
    component_plan_sha256s: tuple[tuple[str, str], ...]
    scientific_execution_performed: bool
    test_dataset_access: bool
    publication_permitted: bool
    receipt_sha256: str

    def payload_without_digest(self) -> dict[str, object]:
        payload = cast(dict[str, object], _canonicalize(asdict(self)))
        payload.pop("receipt_sha256")
        return payload

    def computed_sha256(self) -> str:
        return _sha256_object(self.payload_without_digest())

    def require(self) -> None:
        if self.schema_version != 1:
            raise ScientificRuntimeError("campaign receipt schema_version must be 1")
        if self.status != "scientific_execution_sealed":
            raise ScientificRuntimeError("campaign receipt status differs")
        if not re.fullmatch(r"[0-9a-f]{40}", self.source_commit):
            raise ScientificRuntimeError("campaign receipt source commit differs")
        if not self.primary_artifact_name.strip():
            raise ScientificRuntimeError("campaign receipt primary artifact name is empty")
        for value, name in (
            (self.request_sha256, "request_sha256"),
            (self.authorization_sha256, "authorization_sha256"),
            (self.image_digest, "image_digest"),
            (self.primary_artifact_sha256, "primary_artifact_sha256"),
            (self.receipt_sha256, "receipt_sha256"),
        ):
            if re.fullmatch(r"sha256:[0-9a-f]{64}", value) is None:
                raise ScientificRuntimeError(f"campaign receipt {name} differs")
        artifact_names = tuple(item[0] for item in self.artifact_sha256s)
        if artifact_names != tuple(sorted(artifact_names)) or len(artifact_names) != len(set(artifact_names)):
            raise ScientificRuntimeError("campaign receipt artifact registry differs")
        for _name, digest in self.artifact_sha256s:
            if re.fullmatch(r"sha256:[0-9a-f]{64}", digest) is None:
                raise ScientificRuntimeError("campaign receipt artifact digest differs")
        artifact_map = dict(self.artifact_sha256s)
        if artifact_map.get(self.primary_artifact_name) != self.primary_artifact_sha256:
            raise ScientificRuntimeError("campaign receipt primary artifact is not registry-bound")
        plan_ids = tuple(item[0] for item in self.component_plan_sha256s)
        if len(plan_ids) != len(set(plan_ids)):
            raise ScientificRuntimeError("campaign receipt component plans repeat")
        for _component_id, digest in self.component_plan_sha256s:
            if re.fullmatch(r"sha256:[0-9a-f]{64}", digest) is None:
                raise ScientificRuntimeError("campaign receipt component-plan digest differs")
        if not self.scientific_execution_performed:
            raise ScientificRuntimeError("campaign receipt must record execution")
        if self.test_dataset_access or self.publication_permitted:
            raise ScientificRuntimeError("campaign receipt cannot open test/publication")
        expected_kind: ReceiptKind | None
        if self.role is CampaignRole.C1_COLLECTION:
            expected_kind = ReceiptKind.C1_COLLECTION
        elif self.role is CampaignRole.C2_CALIBRATION:
            expected_kind = (
                ReceiptKind.C2_POLICY_FREEZE
                if self.primary_artifact_name == "selected-policy.json"
                else None
            )
        elif self.role is CampaignRole.C3_CONFIRMATORY:
            expected_kind = ReceiptKind.C3_CONFIRMATORY
        else:
            expected_kind = None
        if self.protocol_receipt_kind is not expected_kind:
            raise ScientificRuntimeError("campaign protocol receipt kind differs")
        if self.receipt_sha256 != self.computed_sha256():
            raise ScientificRuntimeError("campaign receipt self hash differs")

    def canonical_json(self) -> str:
        return _canonical_json(self)


@dataclass(frozen=True)
class C2PolicySelection:
    """Deterministic safety -> coverage -> net-cost policy-selection result."""

    status: str
    selected_policy_sha256: str | None
    selected_policy_id: str | None
    candidate_evaluations: tuple[tuple[str, EvaluationSummary], ...]


def _require_runtime_manifest_identity(
    root: Path,
    request: ScientificCampaignRequest,
    identity: ScientificRuntimeIdentity,
) -> ScientificRuntimeIdentity:
    """Verify the request against one image-bound runtime identity."""

    if identity.sha256 != request.code_manifest_sha256:
        raise ScientificRuntimeError(
            "request runtime-manifest digest differs from image-bound identity"
        )
    try:
        verify_runtime_manifest(
            root,
            identity,
            required_paths=_RUNTIME_REQUIRED_PATHS,
        )
    except ScientificRuntimeIdentityError as exc:
        raise ScientificRuntimeError(str(exc)) from exc
    return identity


def _require_embedded_runtime_identity(
    root: Path,
    request: ScientificCampaignRequest,
) -> ScientificRuntimeIdentity:
    """Bind embedded execution to the immutable image runtime identity."""

    if os.environ.get(SOURCE_COMMIT_ENV) != request.source_commit:
        raise ScientificRuntimeError("embedded successor source commit differs from request")
    if os.environ.get("EXPERIMENT_IMAGE_DIGEST") != request.image_digest:
        raise ScientificRuntimeError("embedded image digest differs from request")
    try:
        identity = runtime_identity_from_environment(os.environ)
    except ScientificRuntimeIdentityError as exc:
        raise ScientificRuntimeError(str(exc)) from exc
    return _require_runtime_manifest_identity(root, request, identity)


def _require_host_claim(
    output_root: Path,
    request: ScientificCampaignRequest,
    authorization: ScientificCampaignAuthorization,
) -> ScientificHostClaim:
    """Require the exact host-side claim that already consumed authorization."""

    if not output_root.is_dir() or output_root.is_symlink():
        raise ScientificRuntimeError(
            "authorized output root was not atomically claimed by the host launcher"
        )
    observed = tuple(sorted(path.name for path in output_root.iterdir()))
    if observed != (_HOST_CLAIM_FILENAME,):
        raise ScientificRuntimeError(
            "claimed output root contains unexpected pre-execution artifacts"
        )
    claim = load_scientific_host_claim(output_root / _HOST_CLAIM_FILENAME)
    try:
        claim.require(request, authorization)
    except ScientificCampaignError as exc:
        raise ScientificRuntimeError("host claim binding differs") from exc
    if os.environ.get("QWAKE_SCIENTIFIC_HOST_CLAIM_SHA256") != claim.claim_sha256:
        raise ScientificRuntimeError("host-claim environment identity differs")
    return claim


@dataclass(frozen=True)
class VerifiedPredecessorLineage:
    """Exact producer provenance accepted by this successor runtime."""

    kind: ReceiptKind
    receipt_sha256: str
    receipt_file_sha256: str
    producer_source_commit: str
    producer_image_digest: str
    primary_artifact_name: str
    primary_artifact_sha256: str
    compatibility_contract_id: str

    def receipt_reference(self) -> ReceiptReference:
        return ReceiptReference(self.kind, self.receipt_sha256)

    def canonical_record(self) -> dict[str, object]:
        return {
            "kind": self.kind.value,
            "receipt_sha256": self.receipt_sha256,
            "receipt_file_sha256": self.receipt_file_sha256,
            "producer_source_commit": self.producer_source_commit,
            "producer_image_digest": self.producer_image_digest,
            "primary_artifact_name": self.primary_artifact_name,
            "primary_artifact_sha256": self.primary_artifact_sha256,
            "compatibility_contract_id": self.compatibility_contract_id,
        }


def _verify_predecessor_lineage(
    root: Path,
    request: ScientificCampaignRequest,
) -> tuple[VerifiedPredecessorLineage, ...]:
    """Verify producer provenance separately from the current executor identity.

    The request already binds every predecessor receipt by both semantic and
    file digest.  The receipt therefore remains the immutable source of its
    producer commit/image identity.  Compatibility is established by the
    current image's code-manifest-bound parser and artifact contract, never by
    pretending that a predecessor was produced by the current image.
    """

    verified: list[VerifiedPredecessorLineage] = []
    for binding in request.predecessor_receipts:
        path = _resolve_confined(root, binding.relative_path)
        if not path.is_file() or path.is_symlink():
            raise ScientificRuntimeError(
                f"bound predecessor receipt is absent: {binding.relative_path}"
            )
        if _sha256_file_prefixed(path) != binding.file_sha256:
            raise ScientificRuntimeError(
                f"predecessor receipt file digest differs: {binding.relative_path}"
            )
        receipt = load_campaign_execution_receipt(path)
        if receipt.receipt_sha256 != binding.receipt_sha256:
            raise ScientificRuntimeError(
                f"predecessor receipt semantic identity differs: {binding.relative_path}"
            )
        if receipt.protocol_receipt_kind is not binding.kind:
            raise ScientificRuntimeError(
                f"predecessor receipt kind differs: {binding.relative_path}"
            )
        expected_role = {
            ReceiptKind.C1_COLLECTION: CampaignRole.C1_COLLECTION,
            ReceiptKind.C2_POLICY_FREEZE: CampaignRole.C2_CALIBRATION,
            ReceiptKind.C3_CONFIRMATORY: CampaignRole.C3_CONFIRMATORY,
        }[binding.kind]
        if receipt.role is not expected_role:
            raise ScientificRuntimeError(
                f"predecessor receipt role differs: {binding.relative_path}"
            )

        if binding.kind is ReceiptKind.C1_COLLECTION:
            c1_artifact = request.sealed_c1_dataset
            if c1_artifact is None:
                raise ScientificRuntimeError(
                    "C1 predecessor receipt has no bound trajectory artifact"
                )
            c1_path = _verified_artifact(root, c1_artifact)
            if (
                receipt.primary_artifact_name != "trajectory-dataset.json"
                or receipt.primary_artifact_sha256 != c1_artifact.sha256
            ):
                raise ScientificRuntimeError(
                    "C1 receipt does not bind the requested sealed trajectory"
                )
            dataset = load_sealed_trajectory_dataset(c1_path)
            if dataset.source_receipt_sha256 != receipt.authorization_sha256:
                raise ScientificRuntimeError(
                    "sealed C1 trajectory authorization lineage differs"
                )
        elif binding.kind is ReceiptKind.C2_POLICY_FREEZE:
            policy_artifact = request.frozen_policy
            if policy_artifact is None:
                raise ScientificRuntimeError(
                    "C2 policy-freeze receipt has no bound frozen policy"
                )
            policy_path = _verified_artifact(root, policy_artifact)
            if (
                receipt.primary_artifact_name != "selected-policy.json"
                or receipt.primary_artifact_sha256 != policy_artifact.sha256
            ):
                raise ScientificRuntimeError(
                    "C2 receipt does not bind the requested frozen policy"
                )
            load_frozen_policy(policy_path)

        verified.append(
            VerifiedPredecessorLineage(
                kind=binding.kind,
                receipt_sha256=receipt.receipt_sha256,
                receipt_file_sha256=binding.file_sha256,
                producer_source_commit=receipt.source_commit,
                producer_image_digest=receipt.image_digest,
                primary_artifact_name=receipt.primary_artifact_name,
                primary_artifact_sha256=receipt.primary_artifact_sha256,
                compatibility_contract_id=_PREDECESSOR_COMPATIBILITY_CONTRACT_ID,
            )
        )
    return tuple(verified)


def _verify_predecessor_receipts(
    root: Path,
    request: ScientificCampaignRequest,
) -> tuple[ReceiptReference, ...]:
    """Compatibility wrapper returning only protocol receipt references."""

    return tuple(
        lineage.receipt_reference()
        for lineage in _verify_predecessor_lineage(root, request)
    )


def _execution_context(
    request: ScientificCampaignRequest,
    predecessor_receipts: tuple[ReceiptReference, ...],
) -> ExecutionContext:
    """Bind the request to the existing role/capability/receipt model."""

    return ExecutionContext(
        role=request.role,
        permissions=PermissionSet(
            role=request.role,
            capabilities=ROLE_CAPABILITY_ALLOWLIST[request.role],
        ),
        source_commit=request.source_commit,
        image_digest=request.image_digest,
        request_sha256=request.request_sha256,
        manifest_sha256=request.manifest_sha256,
        code_manifest_sha256=request.code_manifest_sha256,
        receipts=predecessor_receipts,
        policy_manifest_sha256=(
            None if request.frozen_policy is None else request.frozen_policy.sha256
        ),
    )


def _plan_campaign_components(
    context: ExecutionContext,
    request: ScientificCampaignRequest,
) -> tuple[PipelinePlan, ...]:
    """Admit the exact closed role-local component sequence before effects."""

    plans = tuple(plan_component(context, component) for component in request.component_sequence)
    if tuple(plan.component_id for plan in plans) != request.component_sequence:
        raise ScientificRuntimeError("component plan sequence differs from request")
    return plans


def _require_role_data_capability(context: ExecutionContext) -> None:
    """Require the role-specific data boundary before any dataset/artifact read."""

    if context.role is CampaignRole.C1_COLLECTION:
        context.permissions.require(Capability.ACCESS_DESIGN_DATA)
    elif context.role is CampaignRole.C2_CALIBRATION:
        context.permissions.require(
            Capability.ACCESS_SEALED_C1_ARTIFACTS,
            Capability.RUN_OFFLINE_REPLAY,
        )
    elif context.role is CampaignRole.C3_CONFIRMATORY:
        context.permissions.require(
            Capability.ACCESS_CONFIRMATORY_DATA,
            Capability.LOAD_FROZEN_POLICY,
            Capability.EXECUTE_SHADOW_POLICY,
        )
    else:
        context.permissions.require(
            Capability.ACCESS_REPLICATION_DATA,
            Capability.LOAD_FROZEN_POLICY,
            Capability.EXECUTE_SHADOW_POLICY,
        )


@dataclass(frozen=True)
class ScientificPreclaimPlan:
    """Effect-free deterministic admission result computed before host claim."""

    runtime_identity: ScientificRuntimeIdentity
    predecessor_receipts: tuple[ReceiptReference, ...]
    predecessor_lineage: tuple[VerifiedPredecessorLineage, ...]
    component_plans: tuple[PipelinePlan, ...]


def preflight_scientific_campaign(
    project_root: Path,
    request: ScientificCampaignRequest,
    authorization: ScientificCampaignAuthorization,
    *,
    runtime_identity: ScientificRuntimeIdentity | None = None,
) -> ScientificPreclaimPlan:
    """Resolve all deterministic scientific admission before one-shot claim.

    Host admission supplies the runtime identity derived from immutable image
    metadata.  Embedded execution omits it and therefore rereads the exact same
    identity from image environment metadata.  This function performs no write,
    process spawn, dataset construction, model invocation, or authorization
    consumption.
    """

    root = project_root.expanduser().resolve()
    if not root.is_dir() or root.is_symlink():
        raise ScientificRuntimeError("project root must be a real directory")
    authorization.require_request(request)
    identity = (
        _require_embedded_runtime_identity(root, request)
        if runtime_identity is None
        else _require_runtime_manifest_identity(root, request, runtime_identity)
    )
    predecessor_lineage = _verify_predecessor_lineage(root, request)
    predecessor_receipts = tuple(
        lineage.receipt_reference() for lineage in predecessor_lineage
    )
    context = _execution_context(request, predecessor_receipts)
    component_plans = _plan_campaign_components(context, request)
    _require_role_data_capability(context)
    return ScientificPreclaimPlan(
        runtime_identity=identity,
        predecessor_receipts=predecessor_receipts,
        predecessor_lineage=predecessor_lineage,
        component_plans=component_plans,
    )


def execute_scientific_campaign(
    project_root: Path,
    request: ScientificCampaignRequest,
    authorization: ScientificCampaignAuthorization,
) -> CampaignExecutionReceipt:
    """Consume one exact authorization and execute its closed role handler."""

    root = project_root.expanduser().resolve()
    preclaim = preflight_scientific_campaign(root, request, authorization)
    predecessor_receipts = preclaim.predecessor_receipts
    predecessor_lineage = preclaim.predecessor_lineage
    component_plans = preclaim.component_plans
    output_root = _resolve_confined(root, request.output_root)
    host_claim = _require_host_claim(output_root, request, authorization)

    # The host claim is the one-shot authorization-consumption boundary.  From
    # this point onward this embedded runner only continues that exact attempt.
    _write_exclusive(
        output_root / "authorization-consumption.json",
        _canonical_json(
            {
                "schema_version": 1,
                "status": "authorization_consumed_attempt_started",
                "request_sha256": request.request_sha256,
                "authorization_sha256": authorization.authorization_sha256,
                "image_digest": request.image_digest,
                "role": request.role.value,
                "host_claim_sha256": host_claim.claim_sha256,
                "component_plans": tuple(
                    (plan.component_id.value, plan.plan_sha256)
                    for plan in component_plans
                ),
                "predecessor_receipts": tuple(
                    (receipt.kind.value, receipt.sha256)
                    for receipt in predecessor_receipts
                ),
                "predecessor_lineage": tuple(
                    lineage.canonical_record() for lineage in predecessor_lineage
                ),
                "automatic_retry_permitted": False,
                "test_dataset_access": False,
                "publication_permitted": False,
            }
        ).encode("utf-8"),
    )

    artifact_sha256s: dict[str, str]
    if request.role is CampaignRole.C1_COLLECTION:
        artifact_sha256s = _execute_c1(root, output_root, request, authorization)
    elif request.role is CampaignRole.C2_CALIBRATION:
        artifact_sha256s = _execute_c2(root, output_root, request)
    elif request.role is CampaignRole.C3_CONFIRMATORY:
        artifact_sha256s = _execute_c3_or_r(root, output_root, request, authorization)
    else:
        artifact_sha256s = _execute_c3_or_r(root, output_root, request, authorization)

    if not artifact_sha256s:
        raise ScientificRuntimeError("campaign produced no scientific artifacts")
    primary_preference = (
        "trajectory-dataset.json",
        "selected-policy.json",
        "policy-selection.json",
        "shadow-evaluation.json",
    )
    primary_name = next(
        (name for name in primary_preference if name in artifact_sha256s),
        sorted(artifact_sha256s)[0],
    )
    primary_sha = artifact_sha256s[primary_name]
    auxiliary = tuple(sorted(artifact_sha256s.items()))
    protocol_kind: ReceiptKind | None
    if request.role is CampaignRole.C1_COLLECTION:
        protocol_kind = ReceiptKind.C1_COLLECTION
    elif request.role is CampaignRole.C2_CALIBRATION and primary_name == "selected-policy.json":
        protocol_kind = ReceiptKind.C2_POLICY_FREEZE
    elif request.role is CampaignRole.C3_CONFIRMATORY:
        protocol_kind = ReceiptKind.C3_CONFIRMATORY
    else:
        protocol_kind = None
    provisional = CampaignExecutionReceipt(
        schema_version=1,
        role=request.role,
        protocol_receipt_kind=protocol_kind,
        source_commit=request.source_commit,
        request_sha256=request.request_sha256,
        authorization_sha256=authorization.authorization_sha256,
        image_digest=request.image_digest,
        output_root=request.output_root,
        status="scientific_execution_sealed",
        primary_artifact_name=primary_name,
        primary_artifact_sha256=primary_sha,
        artifact_sha256s=auxiliary,
        component_plan_sha256s=tuple(
            (plan.component_id.value, plan.plan_sha256) for plan in component_plans
        ),
        scientific_execution_performed=True,
        test_dataset_access=False,
        publication_permitted=False,
        receipt_sha256="sha256:" + "0" * 64,
    )
    receipt = replace(
        provisional,
        receipt_sha256=provisional.computed_sha256(),
    )
    receipt.require()
    _write_exclusive(output_root / "receipt.json", receipt.canonical_json().encode("utf-8"))
    _write_sums(output_root)
    return receipt


def collect_live_trajectory(
    project_root: Path,
    request: ScientificCampaignRequest,
    authorization: ScientificCampaignAuthorization,
    *,
    _device: torch.device | None = None,
) -> SealedTrajectoryDataset:
    """Collect full shadow trajectories for C1/C3/R without test-data access."""

    if request.role not in {
        CampaignRole.C1_COLLECTION,
        CampaignRole.C3_CONFIRMATORY,
        CampaignRole.R_REPLICATION,
    }:
        raise ScientificRuntimeError("live trajectory collection is forbidden for C2")
    dataset_binding = request.dataset
    if dataset_binding is None:
        raise ScientificRuntimeError("live request has no dataset binding")
    device = _canonical_scientific_device() if _device is None else _device
    if _device is None and device.type != "cuda":
        raise ScientificRuntimeError("canonical scientific execution requires ROCm")

    dataset, allowed_indices = _load_read_only_dataset(project_root, dataset_binding)
    records: list[TrajectorySnapshotRecord] = []
    for model_seed in request.model_seeds:
        for batch in dataset_binding.batches:
            if not set(batch.indices).issubset(allowed_indices):
                raise ScientificRuntimeError(
                    f"batch {batch.batch_id} escapes its frozen split partition"
                )
            inputs, targets = _materialize_batch(dataset, batch)
            inputs = inputs.to(device=device, dtype=torch.float32)
            targets = targets.to(device=device)
            records.extend(
                _collect_model_batch(
                    request,
                    authorization,
                    model_seed=model_seed,
                    batch=batch,
                    inputs=inputs,
                    targets=targets,
                    device=device,
                )
            )
    if not records:
        raise ScientificRuntimeError("live campaign produced no trajectory records")
    return SealedTrajectoryDataset(
        schema_version=1,
        contract_id=_CONTRACT_ID,
        records=tuple(sorted(records, key=lambda item: item.record_id)),
        source_receipt_sha256=authorization.authorization_sha256,
    )


def _execute_c1(
    root: Path,
    output_root: Path,
    request: ScientificCampaignRequest,
    authorization: ScientificCampaignAuthorization,
) -> dict[str, str]:
    dataset = collect_live_trajectory(root, request, authorization)
    opportunity = analyze_opportunity(
        dataset,
        request.control_overhead_lower_bound_ns,
    )
    trajectory_path = output_root / "trajectory-dataset.json"
    opportunity_path = output_root / "opportunity-summary.json"
    _write_exclusive(trajectory_path, dataset.canonical_json().encode("utf-8"))
    _write_exclusive(opportunity_path, _canonical_json(opportunity).encode("utf-8"))
    return {
        trajectory_path.name: _sha256_file_prefixed(trajectory_path),
        opportunity_path.name: _sha256_file_prefixed(opportunity_path),
    }


def _execute_c2(
    root: Path,
    output_root: Path,
    request: ScientificCampaignRequest,
) -> dict[str, str]:
    c1_binding = cast(ArtifactBinding, request.sealed_c1_dataset)
    c1_path = _verified_artifact(root, c1_binding)
    dataset = load_sealed_trajectory_dataset(c1_path)
    candidates = tuple(
        load_frozen_policy(_verified_artifact(root, binding))
        for binding in request.candidate_policies
    )
    selection = select_c2_policy(dataset, candidates)
    selection_path = output_root / "policy-selection.json"
    _write_exclusive(selection_path, _canonical_json(selection).encode("utf-8"))

    artifacts = {selection_path.name: _sha256_file_prefixed(selection_path)}
    if selection.selected_policy_sha256 is not None:
        selected = next(
            policy for policy in candidates if policy.sha256() == selection.selected_policy_sha256
        )
        policy_path = output_root / "selected-policy.json"
        _write_exclusive(policy_path, selected.canonical_json().encode("utf-8"))
        artifacts[policy_path.name] = _sha256_file_prefixed(policy_path)

        baselines = tuple(
            (
                baseline.value,
                evaluate_baseline(
                    dataset,
                    baseline,
                    BaselineConfiguration(),
                    selected if baseline is QWakeFPBaselineId.B6_FROZEN_QWAKE_FP else None,
                ),
            )
            for baseline in BASELINE_REGISTRY
        )
        ablations = tuple(
            (
                ablation.value,
                evaluate_policy(dataset, apply_ablation(selected, ablation)),
            )
            for ablation in ABLATION_REGISTRY
        )
        diagnostics_path = output_root / "offline-diagnostics.json"
        _write_exclusive(
            diagnostics_path,
            _canonical_json({"baselines": baselines, "ablations": ablations}).encode("utf-8"),
        )
        artifacts[diagnostics_path.name] = _sha256_file_prefixed(diagnostics_path)
    return artifacts


def _execute_c3_or_r(
    root: Path,
    output_root: Path,
    request: ScientificCampaignRequest,
    authorization: ScientificCampaignAuthorization,
) -> dict[str, str]:
    policy_binding = cast(ArtifactBinding, request.frozen_policy)
    policy = load_frozen_policy(_verified_artifact(root, policy_binding))
    dataset = collect_live_trajectory(root, request, authorization)
    evaluation = evaluate_policy(dataset, policy)
    dataset_path = output_root / "trajectory-dataset.json"
    evaluation_path = output_root / "shadow-evaluation.json"
    _write_exclusive(dataset_path, dataset.canonical_json().encode("utf-8"))
    _write_exclusive(evaluation_path, _canonical_json(evaluation).encode("utf-8"))
    return {
        dataset_path.name: _sha256_file_prefixed(dataset_path),
        evaluation_path.name: _sha256_file_prefixed(evaluation_path),
    }


def select_c2_policy(
    dataset: SealedTrajectoryDataset,
    candidates: tuple[FrozenPolicyManifest, ...],
) -> C2PolicySelection:
    """Select one safe/covered/beneficial policy or return a bounded negative result."""

    if not candidates:
        raise ScientificRuntimeError("C2 candidate policy registry cannot be empty")
    if len({policy.policy_id for policy in candidates}) != len(candidates):
        raise ScientificRuntimeError("C2 candidate policy ids cannot repeat")
    evaluations = tuple(
        (policy.sha256(), evaluate_policy(dataset, policy)) for policy in candidates
    )
    eligible: list[tuple[FrozenPolicyManifest, EvaluationSummary]] = []
    for policy, (_sha, summary) in zip(candidates, evaluations, strict=True):
        if (
            summary.dangerous_accepts == 0
            and summary.accepted_records > 0
            and summary.total_net_saving_ns > 0
            and summary.result_class is EvaluationClass.SAFE_AND_BENEFICIAL
        ):
            eligible.append((policy, summary))
    if not eligible:
        return C2PolicySelection(
            status="bounded_negative_no_safe_beneficial_policy",
            selected_policy_sha256=None,
            selected_policy_id=None,
            candidate_evaluations=evaluations,
        )
    eligible.sort(
        key=lambda item: (
            -item[1].coverage,
            -item[1].total_net_saving_ns,
            item[0].sha256(),
        )
    )
    selected = eligible[0][0]
    return C2PolicySelection(
        status="selected_safe_coverage_cost_order",
        selected_policy_sha256=selected.sha256(),
        selected_policy_id=selected.policy_id,
        candidate_evaluations=evaluations,
    )


def _normalize_frontier_for_analytic_completion(
    frontier: FixedPredFrontier,
) -> FixedPredFrontier:
    """Canonicalize redundant float frontier errors without changing beliefs.

    Historical LC4 validation requires completed upper-wavefront errors to be
    bitwise equal to ``fixed - belief``.  In float32, a stored error that was
    used to materialize ``belief = fixed - error`` need not survive the inverse
    subtraction bit-for-bit.  The superseding scientific path therefore
    canonicalizes only that redundant representation before invoking the
    unchanged frozen analytic primitive.  No response-comparison threshold is
    modified.
    """

    normalized = frontier.clone()
    if normalized.candidate_index <= 1:
        return normalized
    depth = len(normalized.fixed) - 1
    boundary = depth - normalized.candidate_index
    errors = list(normalized.errors)
    for index in range(boundary + 1, depth):
        error = errors[index]
        if error is None:
            raise ScientificRuntimeError(
                "completed upper-wavefront error is absent during normalization"
            )
        residual = normalized.fixed[index] - normalized.beliefs[index]
        if not bool(torch.isfinite(residual).all()):
            raise ScientificRuntimeError(
                "completed upper-wavefront residual is non-finite"
            )
        errors[index] = residual.detach().clone()
    return FixedPredFrontier(
        fixed=normalized.fixed,
        beliefs=normalized.beliefs,
        errors=tuple(errors),
        endpoint_loss=normalized.endpoint_loss,
        candidate_index=normalized.candidate_index,
    )


def _collect_model_batch(
    request: ScientificCampaignRequest,
    authorization: ScientificCampaignAuthorization,
    *,
    model_seed: int,
    batch: ScientificBatchSpec,
    inputs: Tensor,
    targets: Tensor,
    device: torch.device,
) -> list[TrajectorySnapshotRecord]:
    model = _build_seeded_model(model_seed).to(device=device, dtype=torch.float32)
    loss_fn = nn.CrossEntropyLoss()
    depth = len(model)
    previous_error: float | None = None
    previous_delta: float | None = None
    records: list[TrajectorySnapshotRecord] = []

    with preserve_outer_rng():
        for candidate_index in range(depth + 1):
            frontier = capture_fixedpred_frontier(
                model,
                loss_fn,
                inputs,
                targets,
                candidate_index=candidate_index,
            )
            snapshot = capture_opaque_state(
                model,
                inputs,
                targets,
                frontier,
                lane_profile_id=_COMPARISON_PROFILE_ID,
                comparison_profile_id=_COMPARISON_PROFILE_ID,
                cost_profile_id=_COST_PROFILE_ID,
                runtime_controls={
                    "data_classification": request.dataset.partition.value if request.dataset else "none",
                    "scientific_execution_open": True,
                    "test_dataset_access": False,
                    "publication_permitted": False,
                    "deterministic_algorithms": True,
                    "fixedpred_eta": 1,
                    "model_id": "lenet_classic",
                    "method_id": "stage2_baseline_fixedpred",
                },
            )
            observation, observation_edges, current_error, current_delta = _observe_frontier(
                frontier,
                model_seed=model_seed,
                batch_id=batch.batch_id,
                device=device,
            )
            analytics, analytic_edges = _analytics_for_frontier(
                frontier,
                previous_error=previous_error,
                previous_delta=previous_delta,
            )
            previous_error = current_error
            previous_delta = current_delta

            _synchronize(device)
            exact_started = time.perf_counter_ns()
            exact_model, exact_frontier = snapshot.fork()
            exact_completion = complete_exact_suffix(exact_model, exact_frontier)
            _synchronize(device)
            remaining_suffix_ns = time.perf_counter_ns() - exact_started
            exact_response = materialize_required_response(
                exact_model,
                exact_completion,
                state_id=snapshot.opaque_state_ref,
                comparison_profile_id=snapshot.comparison_profile_id,
            )

            _synchronize(device)
            analytic_started = time.perf_counter_ns()
            analytic_model, analytic_frontier = snapshot.fork()
            analytic_completion = analytic_wavefront_completion(
                analytic_model,
                _normalize_frontier_for_analytic_completion(analytic_frontier),
            )
            _synchronize(device)
            analytic_ns = time.perf_counter_ns() - analytic_started
            analytic_response = materialize_required_response(
                analytic_model,
                analytic_completion,
                state_id=snapshot.opaque_state_ref,
                comparison_profile_id=snapshot.comparison_profile_id,
            )
            comparison = compare_required_responses(exact_response, analytic_response)
            defect = comparison.response_defect
            if not math.isfinite(defect):
                raise ScientificRuntimeError(
                    "non-finite task-relative defect cannot enter sealed scientific data"
                )
            oracle = OracleLabel(
                snapshot_id=_snapshot_id(model_seed, batch.batch_id, candidate_index),
                response_sha256=analytic_response.canonical_response_sha256,
                defect=defect,
                sufficient=comparison.passed,
            )
            compute_edge = MeasuredEdge(
                edge_id="analytic_completion",
                category=CostCategory.COMPUTE,
                measurement=EdgeMeasurement(host_time_ns=analytic_ns),
            )
            provenance = Provenance(
                schema_version=1,
                source_identity=request.image_digest,
                request_sha256=request.request_sha256,
                manifest_sha256=request.manifest_sha256,
            )
            records.append(
                TrajectorySnapshotRecord(
                    model_seed=model_seed,
                    batch_id=batch.batch_id,
                    snapshot_id=oracle.snapshot_id,
                    compute_step=candidate_index,
                    observation=observation,
                    analytics=analytics,
                    measured_edges=(*observation_edges, *analytic_edges, compute_edge),
                    remaining_suffix_ns=remaining_suffix_ns,
                    provenance=provenance,
                    oracle_label=oracle,
                )
            )
    return records


def _observe_frontier(
    frontier: FixedPredFrontier,
    *,
    model_seed: int,
    batch_id: str,
    device: torch.device,
) -> tuple[FrozenFeatureVector, tuple[MeasuredEdge, ...], float, float]:
    snapshot_id = _snapshot_id(model_seed, batch_id, frontier.candidate_index)
    started = time.perf_counter_ns()
    a0: dict[str, object] = {
        "snapshot_id": snapshot_id,
        "compute_step": frontier.candidate_index,
        "reference_horizon_k_ref": len(frontier.fixed) - 1,
        "remaining_sweeps": len(frontier.fixed) - 1 - frontier.candidate_index,
        "registered_layer_order": tuple(range(len(frontier.fixed) - 1)),
        "registered_block_order": tuple(range(len(frontier.fixed) - 1)),
        "acquired_analytic_ids": (),
        "diagnostic_budget_remaining_ns": 0,
    }
    a0_ns = time.perf_counter_ns() - started

    _synchronize(device)
    started = time.perf_counter_ns()
    prediction_errors = tuple(
        torch.zeros_like(frontier.beliefs[index]) if error is None else error
        for index, error in enumerate(frontier.errors)
    )
    state_deltas = tuple(
        fixed - belief
        for fixed, belief in zip(frontier.fixed, frontier.beliefs, strict=True)
    )
    error_l2 = tuple(_l2_sq(value) for value in prediction_errors)
    delta_l2 = tuple(_l2_sq(value) for value in state_deltas)
    error_max = tuple(_max_abs(value) for value in prediction_errors)
    delta_max = tuple(_max_abs(value) for value in state_deltas)
    _synchronize(device)
    a1_ns = time.perf_counter_ns() - started
    a1 = {
        **a0,
        "global_prediction_error_l2_sq": sum(error_l2),
        "global_state_delta_l2_sq": sum(delta_l2),
        "per_layer_prediction_error_l2_sq": error_l2,
        "per_layer_state_delta_l2_sq": delta_l2,
        "per_layer_prediction_error_max_abs": error_max,
        "per_layer_state_delta_max_abs": delta_max,
    }

    _synchronize(device)
    started = time.perf_counter_ns()
    a2 = {
        **a1,
        "sample_prefix_prediction_error_l2_sq": _sample_reductions(
            prediction_errors, model_seed, batch_id, "prediction_error", "l2_sq"
        ),
        "sample_prefix_state_delta_l2_sq": _sample_reductions(
            state_deltas, model_seed, batch_id, "state_delta", "l2_sq"
        ),
        "sample_prefix_belief_l2_sq": _sample_reductions(
            frontier.beliefs, model_seed, batch_id, "belief", "l2_sq"
        ),
        "sample_prefix_prediction_error_max_abs": _sample_reductions(
            prediction_errors, model_seed, batch_id, "prediction_error", "max_abs"
        ),
        "sample_prefix_state_delta_max_abs": _sample_reductions(
            state_deltas, model_seed, batch_id, "state_delta", "max_abs"
        ),
        "sample_prefix_belief_max_abs": _sample_reductions(
            frontier.beliefs, model_seed, batch_id, "belief", "max_abs"
        ),
    }
    _synchronize(device)
    a2_ns = time.perf_counter_ns() - started
    vector = build_feature_vector(ObservationLevel.A2, cast(dict[str, Any], a2))
    edges = (
        MeasuredEdge("collect_a0", CostCategory.OBSERVER, EdgeMeasurement(host_time_ns=a0_ns)),
        MeasuredEdge("collect_a1", CostCategory.OBSERVER, EdgeMeasurement(host_time_ns=a1_ns)),
        MeasuredEdge("collect_a2", CostCategory.OBSERVER, EdgeMeasurement(host_time_ns=a2_ns)),
    )
    return vector, edges, sum(error_l2), sum(delta_l2)


def _analytics_for_frontier(
    frontier: FixedPredFrontier,
    *,
    previous_error: float | None,
    previous_delta: float | None,
) -> tuple[tuple[FrozenAnalyticOutput, ...], tuple[MeasuredEdge, ...]]:
    current_error = sum(
        _l2_sq(torch.zeros_like(frontier.beliefs[index]) if error is None else error)
        for index, error in enumerate(frontier.errors)
    )
    current_delta = sum(
        _l2_sq(fixed - belief)
        for fixed, belief in zip(frontier.fixed, frontier.beliefs, strict=True)
    )
    values: list[FrozenAnalyticOutput] = []
    edges: list[MeasuredEdge] = []
    for spec in ANALYTIC_REGISTRY:
        started = time.perf_counter_ns()
        if spec.analytic_id is QWakeFPAnalyticId.ROSENBAUM_WAVEFRONT_STATUS_V1:
            fields: tuple[tuple[str, object], ...] = (
                ("completed_component_prefix", frontier.candidate_index),
                (
                    "next_structurally_unfinished_component",
                    min(frontier.candidate_index + 1, len(frontier.fixed) - 1),
                ),
            )
        elif spec.analytic_id is QWakeFPAnalyticId.RESIDUAL_PERSISTENCE_V1:
            fields = (
                (
                    "prediction_error_nonincreasing",
                    previous_error is not None and current_error <= previous_error,
                ),
                (
                    "state_delta_nonincreasing",
                    previous_delta is not None and current_delta <= previous_delta,
                ),
                ("persistence_window_complete", previous_error is not None),
            )
        else:
            fields = (
                ("candidate_acquisition_dominated", False),
                ("lower_bound_remaining_suffix_ns", 0),
                ("upper_bound_acquisition_ns", 0),
            )
        elapsed = time.perf_counter_ns() - started
        measurement = EdgeMeasurement(host_time_ns=elapsed)
        values.append(
            FrozenAnalyticOutput(
                analytic_id=spec.analytic_id,
                outcome=AnalyticOutcome.UNRESOLVED,
                fields=cast(tuple[tuple[str, Any], ...], fields),
                measurement=measurement,
            )
        )
        edges.append(
            MeasuredEdge(
                edge_id=f"analytic:{spec.analytic_id.value}",
                category=CostCategory.DIAGNOSTIC,
                measurement=measurement,
            )
        )
    return tuple(values), tuple(edges)


def _sample_reductions(
    tensors: tuple[Tensor, ...],
    model_seed: int,
    batch_id: str,
    tensor_role: str,
    statistic: str,
) -> dict[str, tuple[float, ...]]:
    result: dict[str, tuple[float, ...]] = {}
    for prefix in _SAMPLE_PREFIXES:
        layer_values: list[float] = []
        for layer_id, tensor in enumerate(tensors):
            flat = tensor.detach().reshape(-1)
            count = min(prefix, flat.numel())
            ranked = sorted(
                range(flat.numel()),
                key=lambda index: hashlib.sha256(
                    (
                        f"{_CONTRACT_ID}|{model_seed}|{batch_id}|"
                        f"{layer_id}|{tensor_role}|{index}"
                    ).encode()
                ).digest(),
            )
            indices = torch.tensor(ranked[:count], device=flat.device, dtype=torch.long)
            sample = flat.index_select(0, indices)
            layer_values.append(_l2_sq(sample) if statistic == "l2_sq" else _max_abs(sample))
        result[str(prefix)] = tuple(layer_values)
    return result


@dataclass(frozen=True)
class _TrainOnlyIDXDataset:
    """In-memory train-only MNIST-family dataset with the canonical 32x32 transform."""

    images: Tensor
    targets: Tensor

    def __post_init__(self) -> None:
        if self.images.dtype != torch.uint8 or self.images.ndim != 3:
            raise ScientificRuntimeError("train image tensor must be uint8 N x H x W")
        if self.images.shape[1:] != (28, 28):
            raise ScientificRuntimeError("train image geometry must be 28x28")
        if self.targets.dtype != torch.uint8 or self.targets.ndim != 1:
            raise ScientificRuntimeError("train target tensor must be uint8 N")
        if self.images.shape[0] != self.targets.shape[0]:
            raise ScientificRuntimeError("train image/target cardinality differs")

    def __len__(self) -> int:
        return int(self.targets.shape[0])

    def __getitem__(self, index: int) -> tuple[Tensor, int]:
        image = self.images[index].to(dtype=torch.float32).div(255.0).unsqueeze(0)
        padded = F.pad(image, (2, 2, 2, 2), value=0.0)
        return padded, int(self.targets[index].item())


def _read_idx_images(path: Path) -> Tensor:
    raw = path.read_bytes()
    if len(raw) < 16:
        raise ScientificRuntimeError("train image IDX payload is truncated")
    magic, count, rows, columns = struct.unpack(">IIII", raw[:16])
    if magic != 2051:
        raise ScientificRuntimeError("train image IDX magic differs")
    if rows != 28 or columns != 28:
        raise ScientificRuntimeError("train image IDX geometry differs")
    expected = count * rows * columns
    payload = raw[16:]
    if len(payload) != expected:
        raise ScientificRuntimeError("train image IDX payload length differs")
    array = np.frombuffer(payload, dtype=np.uint8).copy().reshape(count, rows, columns)
    return torch.from_numpy(array)


def _read_idx_labels(path: Path) -> Tensor:
    raw = path.read_bytes()
    if len(raw) < 8:
        raise ScientificRuntimeError("train label IDX payload is truncated")
    magic, count = struct.unpack(">II", raw[:8])
    if magic != 2049:
        raise ScientificRuntimeError("train label IDX magic differs")
    payload = raw[8:]
    if len(payload) != count:
        raise ScientificRuntimeError("train label IDX payload length differs")
    return torch.from_numpy(np.frombuffer(payload, dtype=np.uint8).copy())


def _load_read_only_dataset(
    root: Path,
    binding: ScientificDatasetBinding,
) -> tuple[_TrainOnlyIDXDataset, set[int]]:
    dataset_root = _resolve_confined(root, binding.dataset_root)
    if not dataset_root.is_dir():
        raise ScientificRuntimeError("dataset root is absent")

    expected_assets = canonical_train_dataset_asset_paths(
        binding.dataset_name,
        binding.dataset_root,
    )
    observed_assets = tuple(asset.relative_path for asset in binding.dataset_assets)
    if observed_assets != expected_assets:
        raise ScientificRuntimeError(
            "live dataset binding is not the exact train-only IDX pair"
        )

    verified_assets: dict[str, Path] = {}
    for asset in binding.dataset_assets:
        asset_path = _verified_artifact(root, asset)
        try:
            asset_path.relative_to(dataset_root)
        except ValueError as exc:
            raise ScientificRuntimeError(
                "bound dataset asset is outside dataset_root"
            ) from exc
        verified_assets[asset.relative_path] = asset_path

    split_path = _verified_artifact(root, binding.split)
    with np.load(split_path, allow_pickle=False) as loaded:
        if binding.split_key not in loaded.files:
            raise ScientificRuntimeError("frozen split key is absent")
        allowed = {
            int(value)
            for value in np.asarray(loaded[binding.split_key], dtype=np.int64)
        }

    images = _read_idx_images(verified_assets[expected_assets[0]])
    targets = _read_idx_labels(verified_assets[expected_assets[1]])
    dataset = _TrainOnlyIDXDataset(images=images, targets=targets)
    if any(index < 0 or index >= len(dataset) for index in allowed):
        raise ScientificRuntimeError("split contains out-of-range dataset index")
    return dataset, allowed


def _materialize_batch(dataset: Any, batch: ScientificBatchSpec) -> tuple[Tensor, Tensor]:
    images: list[Tensor] = []
    targets: list[int] = []
    for index in batch.indices:
        sample = dataset[index]
        if not isinstance(sample, tuple | list) or len(sample) != 2:
            raise ScientificRuntimeError("dataset sample must be (input,target)")
        image, target = sample
        if not isinstance(image, Tensor):
            raise ScientificRuntimeError("dataset transform must return a tensor")
        images.append(image)
        targets.append(int(target))
    return torch.stack(images), torch.tensor(targets, dtype=torch.long)


def _build_seeded_model(seed: int) -> nn.Sequential:
    state = torch.random.get_rng_state()
    try:
        torch.manual_seed(seed)
        return build_model("lenet_classic")
    finally:
        torch.random.set_rng_state(state)


def _canonical_scientific_device() -> torch.device:
    if not torch.cuda.is_available() or not str(torch.version.hip or "").strip():
        raise ScientificRuntimeError("canonical ROCm device is unavailable")
    return torch.device("cuda")


def _synchronize(device: torch.device) -> None:
    if device.type == "cuda":
        torch.cuda.synchronize(device)


def _snapshot_id(model_seed: int, batch_id: str, candidate_index: int) -> str:
    return f"seed-{model_seed}:{batch_id}:snapshot-{candidate_index}"


def _l2_sq(value: Tensor) -> float:
    return float(torch.sum(value.detach().to(dtype=torch.float64) ** 2).item())


def _max_abs(value: Tensor) -> float:
    if value.numel() == 0:
        return 0.0
    return float(torch.max(torch.abs(value.detach())).item())


def _verified_artifact(root: Path, binding: ArtifactBinding) -> Path:
    path = _resolve_confined(root, binding.relative_path)
    if not path.is_file() or path.is_symlink():
        raise ScientificRuntimeError(f"bound artifact is absent: {binding.relative_path}")
    if _sha256_file_prefixed(path) != binding.sha256:
        raise ScientificRuntimeError(f"bound artifact digest differs: {binding.relative_path}")
    return path


def _resolve_confined(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ScientificRuntimeError("path escapes project root") from exc
    return candidate


def load_campaign_execution_receipt(path: Path) -> CampaignExecutionReceipt:
    """Load and verify one canonical terminal campaign receipt."""

    payload = _read_object(path)
    kind_raw = payload.get("protocol_receipt_kind")
    if kind_raw is not None and not isinstance(kind_raw, str):
        raise ScientificRuntimeError("protocol_receipt_kind must be string or null")
    auxiliary_raw = payload.get("artifact_sha256s")
    plans_raw = payload.get("component_plan_sha256s")
    if not isinstance(auxiliary_raw, list) or not isinstance(plans_raw, list):
        raise ScientificRuntimeError("receipt artifact/plan registries must be lists")
    auxiliary = tuple(_string_pair(item, "auxiliary artifact") for item in auxiliary_raw)
    plans = tuple(_string_pair(item, "component plan") for item in plans_raw)
    receipt = CampaignExecutionReceipt(
        schema_version=_integer(payload, "schema_version"),
        role=CampaignRole(_string(payload, "role")),
        protocol_receipt_kind=(None if kind_raw is None else ReceiptKind(kind_raw)),
        source_commit=_string(payload, "source_commit"),
        request_sha256=_string(payload, "request_sha256"),
        authorization_sha256=_string(payload, "authorization_sha256"),
        image_digest=_string(payload, "image_digest"),
        output_root=_string(payload, "output_root"),
        status=_string(payload, "status"),
        primary_artifact_name=_string(payload, "primary_artifact_name"),
        primary_artifact_sha256=_string(payload, "primary_artifact_sha256"),
        artifact_sha256s=auxiliary,
        component_plan_sha256s=plans,
        scientific_execution_performed=_boolean(
            payload, "scientific_execution_performed"
        ),
        test_dataset_access=_boolean(payload, "test_dataset_access"),
        publication_permitted=_boolean(payload, "publication_permitted"),
        receipt_sha256=_string(payload, "receipt_sha256"),
    )
    receipt.require()
    if path.read_text(encoding="utf-8") != receipt.canonical_json():
        raise ScientificRuntimeError("campaign receipt is not canonical")
    return receipt


def load_sealed_trajectory_dataset(path: Path) -> SealedTrajectoryDataset:
    payload = _read_object(path)
    records_raw = payload.get("records")
    if not isinstance(records_raw, list):
        raise ScientificRuntimeError("trajectory records must be a list")
    records = tuple(_trajectory_record(item) for item in records_raw)
    dataset = SealedTrajectoryDataset(
        schema_version=_integer(payload, "schema_version"),
        contract_id=_string(payload, "contract_id"),
        records=records,
        source_receipt_sha256=_string(payload, "source_receipt_sha256"),
    )
    if path.read_text(encoding="utf-8") != dataset.canonical_json():
        raise ScientificRuntimeError("sealed trajectory dataset is not canonical")
    return dataset


def load_frozen_policy(path: Path) -> FrozenPolicyManifest:
    payload = _read_object(path)
    rules_raw = payload.get("rules")
    if not isinstance(rules_raw, list):
        raise ScientificRuntimeError("policy rules must be a list")
    policy = FrozenPolicyManifest(
        schema_version=_integer(payload, "schema_version"),
        policy_id=_string(payload, "policy_id"),
        contract_id=_string(payload, "contract_id"),
        rules=tuple(_policy_rule(item) for item in rules_raw),
        default_action=_frontier_action(payload.get("default_action")),
    )
    if path.read_text(encoding="utf-8") != policy.canonical_json():
        raise ScientificRuntimeError("frozen policy is not canonical")
    return policy


def _trajectory_record(value: object) -> TrajectorySnapshotRecord:
    payload = _object(value, "trajectory record")
    observation_raw = _object(payload.get("observation"), "observation")
    analytics_raw = payload.get("analytics")
    edges_raw = payload.get("measured_edges")
    provenance_raw = _object(payload.get("provenance"), "provenance")
    oracle_raw = _object(payload.get("oracle_label"), "oracle_label")
    if not isinstance(analytics_raw, list) or not isinstance(edges_raw, list):
        raise ScientificRuntimeError("trajectory analytics/edges must be lists")
    fields = observation_raw.get("fields")
    if not isinstance(fields, list):
        raise ScientificRuntimeError("observation fields must be a list")
    observation = FrozenFeatureVector(
        level=ObservationLevel(_string(observation_raw, "level")),
        fields=tuple(_pair(item, "observation field") for item in fields),
    )
    analytics = tuple(_analytic(item) for item in analytics_raw)
    edges = tuple(_edge(item) for item in edges_raw)
    provenance = Provenance(
        schema_version=_integer(provenance_raw, "schema_version"),
        source_identity=_string(provenance_raw, "source_identity"),
        request_sha256=_string(provenance_raw, "request_sha256"),
        manifest_sha256=_string(provenance_raw, "manifest_sha256"),
    )
    oracle = OracleLabel(
        snapshot_id=_string(oracle_raw, "snapshot_id"),
        response_sha256=_string(oracle_raw, "response_sha256"),
        defect=_number(oracle_raw, "defect"),
        sufficient=_boolean(oracle_raw, "sufficient"),
        post_action=_boolean(oracle_raw, "post_action"),
    )
    return TrajectorySnapshotRecord(
        model_seed=_integer(payload, "model_seed"),
        batch_id=_string(payload, "batch_id"),
        snapshot_id=_string(payload, "snapshot_id"),
        compute_step=_integer(payload, "compute_step"),
        observation=observation,
        analytics=analytics,
        measured_edges=edges,
        remaining_suffix_ns=_integer(payload, "remaining_suffix_ns"),
        provenance=provenance,
        oracle_label=oracle,
    )


def _analytic(value: object) -> FrozenAnalyticOutput:
    payload = _object(value, "analytic")
    fields = payload.get("fields")
    if not isinstance(fields, list):
        raise ScientificRuntimeError("analytic fields must be a list")
    return FrozenAnalyticOutput(
        analytic_id=QWakeFPAnalyticId(_string(payload, "analytic_id")),
        outcome=AnalyticOutcome(_string(payload, "outcome")),
        fields=tuple(_pair(item, "analytic field") for item in fields),
        measurement=_measurement(payload.get("measurement")),
    )


def _edge(value: object) -> MeasuredEdge:
    payload = _object(value, "measured edge")
    return MeasuredEdge(
        edge_id=_string(payload, "edge_id"),
        category=CostCategory(_string(payload, "category")),
        measurement=_measurement(payload.get("measurement")),
    )


def _measurement(value: object) -> EdgeMeasurement:
    payload = _object(value, "measurement")
    return EdgeMeasurement(
        host_time_ns=_integer(payload, "host_time_ns"),
        device_time_ns=_integer(payload, "device_time_ns"),
        synchronization_count=_integer(payload, "synchronization_count"),
        d2h_bytes=_integer(payload, "d2h_bytes"),
        temporary_memory_bytes=_integer(payload, "temporary_memory_bytes"),
        trace_bytes=_integer(payload, "trace_bytes"),
    )


def _policy_rule(value: object) -> PolicyRule:
    payload = _object(value, "policy rule")
    analytic_id = payload.get("analytic_id")
    analytic_outcome = payload.get("analytic_outcome")
    minimum = payload.get("minimum_observation")
    threshold = payload.get("threshold")
    feature_name = payload.get("feature_name")
    return PolicyRule(
        rule_id=_string(payload, "rule_id"),
        predicate=PolicyPredicateKind(_string(payload, "predicate")),
        action=_frontier_action(payload.get("action")),
        feature_name=None if feature_name is None else str(feature_name),
        threshold=None if threshold is None else float(threshold),
        analytic_id=None if analytic_id is None else QWakeFPAnalyticId(str(analytic_id)),
        analytic_outcome=None if analytic_outcome is None else AnalyticOutcome(str(analytic_outcome)),
        minimum_observation=None if minimum is None else ObservationLevel(str(minimum)),
    )


def _frontier_action(value: object) -> FrontierAction:
    payload = _object(value, "frontier action")
    target = payload.get("target_observation")
    analytic_class = payload.get("analytic_class")
    return FrontierAction(
        kind=FrontierActionKind(_string(payload, "kind")),
        target_observation=None if target is None else ObservationLevel(str(target)),
        analytic_id=None if payload.get("analytic_id") is None else str(payload["analytic_id"]),
        analytic_class=None if analytic_class is None else AnalyticClass(str(analytic_class)),
        next_snapshot_id=None if payload.get("next_snapshot_id") is None else str(payload["next_snapshot_id"]),
    )


def _read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ScientificRuntimeError(f"invalid JSON: {path}") from exc
    if not isinstance(value, dict):
        raise ScientificRuntimeError(f"JSON object required: {path}")
    return cast(dict[str, Any], value)


def _object(value: object, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ScientificRuntimeError(f"{name} must be an object")
    return cast(dict[str, Any], value)


def _string_pair(value: object, name: str) -> tuple[str, str]:
    if (
        not isinstance(value, list)
        or len(value) != 2
        or not isinstance(value[0], str)
        or not isinstance(value[1], str)
    ):
        raise ScientificRuntimeError(f"{name} must be [string,string]")
    return value[0], value[1]


def _pair(value: object, name: str) -> tuple[str, Any]:
    if not isinstance(value, list) or len(value) != 2 or not isinstance(value[0], str):
        raise ScientificRuntimeError(f"{name} must be [name,value]")
    field_name = value[0]
    try:
        decoded = canonical_value_from_json(value[1], field_name=field_name)
    except QWakeFPPipelineError as exc:
        raise ScientificRuntimeError(
            f"{name} canonical value differs: {field_name}"
        ) from exc
    return field_name, decoded


def _string(payload: dict[str, Any], name: str) -> str:
    value = payload.get(name)
    if not isinstance(value, str):
        raise ScientificRuntimeError(f"{name} must be a string")
    return value


def _integer(payload: dict[str, Any], name: str) -> int:
    value = payload.get(name)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ScientificRuntimeError(f"{name} must be an integer")
    return value


def _boolean(payload: dict[str, Any], name: str) -> bool:
    value = payload.get(name)
    if not isinstance(value, bool):
        raise ScientificRuntimeError(f"{name} must be a boolean")
    return value


def _number(payload: dict[str, Any], name: str) -> float:
    value = payload.get(name)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ScientificRuntimeError(f"{name} must be a number")
    return float(value)


def _canonicalize(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _canonicalize(asdict(value))
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _canonicalize(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, tuple | list):
        return [_canonicalize(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return "Infinity" if value > 0 else "-Infinity"
    return value


def _canonical_json(value: object) -> str:
    return json.dumps(
        _canonicalize(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ) + "\n"


def _sha256_object(value: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _sha256_file_prefixed(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return "sha256:" + digest.hexdigest()


def _write_exclusive(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, "wb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())


def _write_sums(root: Path) -> None:
    entries: list[str] = []
    for path in sorted(root.iterdir(), key=lambda item: item.name):
        if path.name == "SHA256SUMS" or not path.is_file() or path.is_symlink():
            continue
        entries.append(f"{_sha256_file_prefixed(path).removeprefix('sha256:')}  {path.name}\n")
    _write_exclusive(root / "SHA256SUMS", "".join(entries).encode("utf-8"))
