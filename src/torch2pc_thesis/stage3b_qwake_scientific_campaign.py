"""Closed scientific campaign contract for the superseding QW-5 image.

This module contains no Torch, dataset, filesystem, subprocess, network, or
publication effects.  It freezes the data-only request/authorization grammar
and the exact role-local orchestration sequence that the superseding image must
embed before any new scientific-image freeze.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, is_dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Final, cast

from torch2pc_thesis.stage3b_qwake_core import CampaignRole, ReceiptKind
from torch2pc_thesis.stage3b_qwake_fp_pipeline import PipelineComponentId

_SHA256_RE: Final = re.compile(r"^sha256:[0-9a-f]{64}$")
_COMMIT_RE: Final = re.compile(r"^[0-9a-f]{40}$")

SCIENTIFIC_CAMPAIGN_REQUEST_SCHEMA_VERSION: Final = 1
SCIENTIFIC_CAMPAIGN_AUTHORIZATION_SCHEMA_VERSION: Final = 1
SCIENTIFIC_HOST_CLAIM_SCHEMA_VERSION: Final = 1
SCIENTIFIC_CAMPAIGN_REQUEST_ID: Final = "stage3b-qwake-scientific-campaign-request-v1"
SCIENTIFIC_CAMPAIGN_AUTHORIZATION_ID: Final = (
    "stage3b-qwake-scientific-campaign-authorization-v1"
)
SCIENTIFIC_CAMPAIGN_AUTHORIZATION_STATUS: Final = "issued_single_scientific_attempt"
SCIENTIFIC_HOST_CLAIM_ID: Final = "stage3b-qwake-scientific-host-claim-v1"
SCIENTIFIC_HOST_CLAIM_STATUS: Final = "authorization_consumed_host_claimed"


class ScientificCampaignError(ValueError):
    """Raised when a scientific campaign contract is malformed."""


class ScientificBackendId(StrEnum):
    """Closed embedded scientific backend registry."""

    TORCH_FIXEDPRED_BOUNDED_V1 = "torch_fixedpred_bounded_v1"


class ScientificDataPartition(StrEnum):
    """Data partitions visible to live scientific stages."""

    DESIGN = "design"
    CONFIRMATORY = "confirmatory"
    REPLICATION = "replication"


@dataclass(frozen=True)
class ArtifactBinding:
    """One confined immutable artifact reference."""

    relative_path: str
    sha256: str

    def __post_init__(self) -> None:
        _require_confined_relative(self.relative_path, "artifact path")
        _require_artifact_namespace(self.relative_path, "artifact path")
        _require_sha256(self.sha256, "artifact sha256")


@dataclass(frozen=True)
class ProtocolReceiptBinding:
    """One exact predecessor protocol receipt, including its confined path."""

    kind: ReceiptKind
    relative_path: str
    receipt_sha256: str
    file_sha256: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, ReceiptKind):
            raise ScientificCampaignError("receipt kind is invalid")
        _require_confined_relative(self.relative_path, "receipt path")
        _require_nondata_artifact_namespace(self.relative_path, "receipt path")
        _require_sha256(self.receipt_sha256, "receipt semantic sha256")
        _require_sha256(self.file_sha256, "receipt file sha256")


@dataclass(frozen=True)
class ScientificBatchSpec:
    """Exact sample indices forming one deterministic live batch."""

    batch_id: str
    indices: tuple[int, ...]

    def __post_init__(self) -> None:
        if not self.batch_id.strip():
            raise ScientificCampaignError("batch_id cannot be empty")
        if not self.indices:
            raise ScientificCampaignError("batch indices cannot be empty")
        if any(index < 0 for index in self.indices):
            raise ScientificCampaignError("batch indices must be non-negative")
        if len(self.indices) != len(set(self.indices)):
            raise ScientificCampaignError("batch indices cannot repeat")
        if self.indices != tuple(sorted(self.indices)):
            raise ScientificCampaignError("batch indices must be canonically sorted")


@dataclass(frozen=True)
class ScientificDatasetBinding:
    """Read-only dataset/split binding; test data is never represented."""

    dataset_name: str
    dataset_root: str
    split: ArtifactBinding
    dataset_assets: tuple[ArtifactBinding, ...]
    split_key: str
    partition: ScientificDataPartition
    batches: tuple[ScientificBatchSpec, ...]

    def __post_init__(self) -> None:
        if self.dataset_name not in {"FashionMNIST", "MNIST"}:
            raise ScientificCampaignError("dataset is outside the QWake-FP registry")
        _require_confined_relative(self.dataset_root, "dataset_root")
        if Path(self.dataset_root).parts[0] != "data":
            raise ScientificCampaignError("dataset_root must remain under data/")
        if not self.dataset_assets:
            raise ScientificCampaignError("dataset binding requires exact dataset assets")
        _require_unique_artifacts(self.dataset_assets)
        dataset_root = Path(self.dataset_root)
        for asset in self.dataset_assets:
            try:
                Path(asset.relative_path).relative_to(dataset_root)
            except ValueError as exc:
                raise ScientificCampaignError(
                    "dataset asset must remain under dataset_root"
                ) from exc
        _require_nondata_artifact_namespace(self.split.relative_path, "split artifact")
        if not self.split_key.strip():
            raise ScientificCampaignError("split_key cannot be empty")
        if not self.batches:
            raise ScientificCampaignError("live dataset binding requires batches")
        batch_ids = tuple(batch.batch_id for batch in self.batches)
        if len(batch_ids) != len(set(batch_ids)):
            raise ScientificCampaignError("batch ids cannot repeat")
        if batch_ids != tuple(sorted(batch_ids)):
            raise ScientificCampaignError("batches must be canonically sorted")


_C1_COMPONENTS: Final = (
    PipelineComponentId.COLLECT_A0,
    PipelineComponentId.COLLECT_A1,
    PipelineComponentId.COLLECT_A2,
    PipelineComponentId.RUN_EXACT_ANALYTIC,
    PipelineComponentId.RUN_CONSERVATIVE_ANALYTIC,
    PipelineComponentId.RUN_HEURISTIC_ANALYTIC,
    PipelineComponentId.COMPLETE_CANONICAL_SUFFIX,
    PipelineComponentId.COMPUTE_POST_ACTION_ORACLE,
    PipelineComponentId.MAP_EDGE_COSTS,
    PipelineComponentId.ANALYZE_OPPORTUNITY,
    PipelineComponentId.SEAL_ARTIFACT,
)
_C2_COMPONENTS: Final = (
    PipelineComponentId.MAP_EDGE_COSTS,
    PipelineComponentId.ANALYZE_RECOGNIZABILITY,
    PipelineComponentId.INTERPRET_OFFLINE_POLICY,
    PipelineComponentId.REPLAY_BASELINES,
    PipelineComponentId.REPLAY_ABLATIONS,
    PipelineComponentId.SEAL_ARTIFACT,
)
_C3_COMPONENTS: Final = (
    PipelineComponentId.COLLECT_A0,
    PipelineComponentId.COLLECT_A1,
    PipelineComponentId.COLLECT_A2,
    PipelineComponentId.RUN_EXACT_ANALYTIC,
    PipelineComponentId.RUN_CONSERVATIVE_ANALYTIC,
    PipelineComponentId.RUN_HEURISTIC_ANALYTIC,
    PipelineComponentId.COMPLETE_CANONICAL_SUFFIX,
    PipelineComponentId.COMPUTE_POST_ACTION_ORACLE,
    PipelineComponentId.MAP_EDGE_COSTS,
    PipelineComponentId.INTERPRET_FROZEN_POLICY,
    PipelineComponentId.EVALUATE_CONFIRMATORY_SHADOW,
    PipelineComponentId.SEAL_ARTIFACT,
)
_R_COMPONENTS: Final = (
    PipelineComponentId.COLLECT_A0,
    PipelineComponentId.COLLECT_A1,
    PipelineComponentId.COLLECT_A2,
    PipelineComponentId.RUN_EXACT_ANALYTIC,
    PipelineComponentId.RUN_CONSERVATIVE_ANALYTIC,
    PipelineComponentId.RUN_HEURISTIC_ANALYTIC,
    PipelineComponentId.COMPLETE_CANONICAL_SUFFIX,
    PipelineComponentId.COMPUTE_POST_ACTION_ORACLE,
    PipelineComponentId.MAP_EDGE_COSTS,
    PipelineComponentId.INTERPRET_FROZEN_POLICY,
    PipelineComponentId.EVALUATE_REPLICATION,
    PipelineComponentId.SEAL_ARTIFACT,
)

ROLE_COMPONENT_SEQUENCE: Final = {
    CampaignRole.C1_COLLECTION: _C1_COMPONENTS,
    CampaignRole.C2_CALIBRATION: _C2_COMPONENTS,
    CampaignRole.C3_CONFIRMATORY: _C3_COMPONENTS,
    CampaignRole.R_REPLICATION: _R_COMPONENTS,
}


@dataclass(frozen=True)
class ScientificCampaignRequest:
    """Data-only request consumed by one embedded campaign entrypoint."""

    schema_version: int
    request_id: str
    role: CampaignRole
    backend_id: ScientificBackendId
    source_commit: str
    image_digest: str
    manifest_sha256: str
    code_manifest_sha256: str
    dataset: ScientificDatasetBinding | None
    sealed_c1_dataset: ArtifactBinding | None
    candidate_policies: tuple[ArtifactBinding, ...]
    frozen_policy: ArtifactBinding | None
    predecessor_receipts: tuple[ProtocolReceiptBinding, ...]
    model_seeds: tuple[int, ...]
    component_sequence: tuple[PipelineComponentId, ...]
    output_root: str
    control_overhead_lower_bound_ns: int
    arbitrary_code_loading: bool
    shell_command_loading: bool
    test_dataset_access: bool
    publication_permitted: bool
    request_sha256: str

    @classmethod
    def create(
        cls,
        *,
        role: CampaignRole,
        source_commit: str,
        image_digest: str,
        manifest_sha256: str,
        code_manifest_sha256: str,
        dataset: ScientificDatasetBinding | None,
        sealed_c1_dataset: ArtifactBinding | None = None,
        candidate_policies: tuple[ArtifactBinding, ...] = (),
        frozen_policy: ArtifactBinding | None = None,
        predecessor_receipts: tuple[ProtocolReceiptBinding, ...] = (),
        model_seeds: tuple[int, ...] = (),
        output_root: str,
        control_overhead_lower_bound_ns: int = 0,
    ) -> ScientificCampaignRequest:
        """Construct one canonical closed request and compute its self hash."""

        payload: dict[str, object] = {
            "schema_version": SCIENTIFIC_CAMPAIGN_REQUEST_SCHEMA_VERSION,
            "request_id": SCIENTIFIC_CAMPAIGN_REQUEST_ID,
            "role": role,
            "backend_id": ScientificBackendId.TORCH_FIXEDPRED_BOUNDED_V1,
            "source_commit": source_commit,
            "image_digest": image_digest,
            "manifest_sha256": manifest_sha256,
            "code_manifest_sha256": code_manifest_sha256,
            "dataset": dataset,
            "sealed_c1_dataset": sealed_c1_dataset,
            "candidate_policies": candidate_policies,
            "frozen_policy": frozen_policy,
            "predecessor_receipts": predecessor_receipts,
            "model_seeds": model_seeds,
            "component_sequence": ROLE_COMPONENT_SEQUENCE[role],
            "output_root": output_root,
            "control_overhead_lower_bound_ns": control_overhead_lower_bound_ns,
            "arbitrary_code_loading": False,
            "shell_command_loading": False,
            "test_dataset_access": False,
            "publication_permitted": False,
        }
        digest = _sha256_object(payload)
        return cls(
            schema_version=SCIENTIFIC_CAMPAIGN_REQUEST_SCHEMA_VERSION,
            request_id=SCIENTIFIC_CAMPAIGN_REQUEST_ID,
            role=role,
            backend_id=ScientificBackendId.TORCH_FIXEDPRED_BOUNDED_V1,
            source_commit=source_commit,
            image_digest=image_digest,
            manifest_sha256=manifest_sha256,
            code_manifest_sha256=code_manifest_sha256,
            dataset=dataset,
            sealed_c1_dataset=sealed_c1_dataset,
            candidate_policies=candidate_policies,
            frozen_policy=frozen_policy,
            predecessor_receipts=predecessor_receipts,
            model_seeds=model_seeds,
            component_sequence=ROLE_COMPONENT_SEQUENCE[role],
            output_root=output_root,
            control_overhead_lower_bound_ns=control_overhead_lower_bound_ns,
            arbitrary_code_loading=False,
            shell_command_loading=False,
            test_dataset_access=False,
            publication_permitted=False,
            request_sha256=digest,
        )

    def __post_init__(self) -> None:
        if self.schema_version != SCIENTIFIC_CAMPAIGN_REQUEST_SCHEMA_VERSION:
            raise ScientificCampaignError("scientific request schema_version must be 1")
        if self.request_id != SCIENTIFIC_CAMPAIGN_REQUEST_ID:
            raise ScientificCampaignError("scientific request id differs")
        if not isinstance(self.role, CampaignRole):
            raise ScientificCampaignError("scientific role is invalid")
        if self.backend_id is not ScientificBackendId.TORCH_FIXEDPRED_BOUNDED_V1:
            raise ScientificCampaignError("scientific backend id differs")
        if not _COMMIT_RE.fullmatch(self.source_commit):
            raise ScientificCampaignError("source_commit must be exact")
        for value, name in (
            (self.image_digest, "image_digest"),
            (self.manifest_sha256, "manifest_sha256"),
            (self.code_manifest_sha256, "code_manifest_sha256"),
            (self.request_sha256, "request_sha256"),
        ):
            _require_sha256(value, name)
        _require_confined_relative(self.output_root, "output_root")
        if Path(self.output_root).parts[0] != "results":
            raise ScientificCampaignError("scientific output_root must remain under results/")
        if self.control_overhead_lower_bound_ns < 0:
            raise ScientificCampaignError("control overhead lower bound must be non-negative")
        if any(
            (
                self.arbitrary_code_loading,
                self.shell_command_loading,
                self.test_dataset_access,
                self.publication_permitted,
            )
        ):
            raise ScientificCampaignError(
                "scientific request cannot enable code/shell/test/publication effects"
            )
        expected_components = ROLE_COMPONENT_SEQUENCE[self.role]
        if self.component_sequence != expected_components:
            raise ScientificCampaignError("role component sequence differs")
        if len(self.model_seeds) != len(set(self.model_seeds)):
            raise ScientificCampaignError("model seeds cannot repeat")
        if any(seed < 0 for seed in self.model_seeds):
            raise ScientificCampaignError("model seeds must be non-negative")
        if self.model_seeds != tuple(sorted(self.model_seeds)):
            raise ScientificCampaignError("model seeds must be canonically sorted")
        self._require_role_inputs()
        if self.request_sha256 != self.computed_sha256():
            raise ScientificCampaignError("scientific request self hash differs")

    def _require_role_inputs(self) -> None:
        receipt_kinds = tuple(item.kind for item in self.predecessor_receipts)
        if len(receipt_kinds) != len(set(receipt_kinds)):
            raise ScientificCampaignError("predecessor receipt kinds cannot repeat")
        if self.predecessor_receipts != tuple(
            sorted(self.predecessor_receipts, key=lambda item: item.kind.value)
        ):
            raise ScientificCampaignError("predecessor receipts must be canonically sorted")
        required_receipts = {
            CampaignRole.C1_COLLECTION: frozenset(),
            CampaignRole.C2_CALIBRATION: frozenset({ReceiptKind.C1_COLLECTION}),
            CampaignRole.C3_CONFIRMATORY: frozenset(
                {ReceiptKind.C1_COLLECTION, ReceiptKind.C2_POLICY_FREEZE}
            ),
            CampaignRole.R_REPLICATION: frozenset(
                {
                    ReceiptKind.C1_COLLECTION,
                    ReceiptKind.C2_POLICY_FREEZE,
                    ReceiptKind.C3_CONFIRMATORY,
                }
            ),
        }[self.role]
        if set(receipt_kinds) != required_receipts:
            raise ScientificCampaignError(
                f"predecessor receipt set differs for {self.role.value}"
            )
        for artifact in (
            *(() if self.sealed_c1_dataset is None else (self.sealed_c1_dataset,)),
            *self.candidate_policies,
            *(() if self.frozen_policy is None else (self.frozen_policy,)),
        ):
            _require_nondata_artifact_namespace(
                artifact.relative_path, "scientific artifact"
            )
        if self.role is CampaignRole.C1_COLLECTION:
            _require_live_dataset(self.dataset, ScientificDataPartition.DESIGN)
            if not self.model_seeds:
                raise ScientificCampaignError("C1 requires model seeds")
            if self.sealed_c1_dataset or self.candidate_policies or self.frozen_policy:
                raise ScientificCampaignError("C1 cannot load C2/C3 artifacts")
            return
        if self.role is CampaignRole.C2_CALIBRATION:
            if self.dataset is not None or self.model_seeds:
                raise ScientificCampaignError("C2 must remain offline-only")
            if self.sealed_c1_dataset is None:
                raise ScientificCampaignError("C2 requires sealed C1 trajectories")
            if not self.candidate_policies:
                raise ScientificCampaignError("C2 requires frozen policy candidates")
            if self.frozen_policy is not None:
                raise ScientificCampaignError("C2 selects rather than loads final policy")
            _require_unique_artifacts(self.candidate_policies)
            return
        if self.role is CampaignRole.C3_CONFIRMATORY:
            _require_live_dataset(self.dataset, ScientificDataPartition.CONFIRMATORY)
        else:
            _require_live_dataset(self.dataset, ScientificDataPartition.REPLICATION)
        if not self.model_seeds:
            raise ScientificCampaignError("C3/R require untouched model seeds")
        if self.sealed_c1_dataset is None or self.frozen_policy is None:
            raise ScientificCampaignError("C3/R require C1 receipt and frozen policy")
        if self.candidate_policies:
            raise ScientificCampaignError("C3/R cannot retune policy candidates")

    def payload_without_digest(self) -> dict[str, object]:
        payload = cast(dict[str, object], _canonicalize(asdict(self)))
        payload.pop("request_sha256")
        return payload

    def computed_sha256(self) -> str:
        return _sha256_object(self.payload_without_digest())

    def canonical_json(self) -> str:
        return _canonical_json(self)


@dataclass(frozen=True)
class ScientificCampaignAuthorization:
    """One-shot authorization bound to exactly one scientific request/image."""

    schema_version: int
    authorization_id: str
    status: str
    issued_at_utc: str
    request_sha256: str
    source_commit: str
    image_digest: str
    role: CampaignRole
    output_root: str
    output_root_absent_at_issue: bool
    host_claim_required: bool
    execution_count: int
    scientific_execution_open: bool
    arbitrary_code_loading: bool
    shell_command_loading: bool
    test_dataset_access: bool
    publication_permitted: bool
    authorization_sha256: str

    @classmethod
    def issue(
        cls,
        request: ScientificCampaignRequest,
        *,
        issued_at_utc: str,
    ) -> ScientificCampaignAuthorization:
        """Issue one canonical one-shot authorization for an exact request."""

        payload: dict[str, object] = {
            "schema_version": SCIENTIFIC_CAMPAIGN_AUTHORIZATION_SCHEMA_VERSION,
            "authorization_id": SCIENTIFIC_CAMPAIGN_AUTHORIZATION_ID,
            "status": SCIENTIFIC_CAMPAIGN_AUTHORIZATION_STATUS,
            "issued_at_utc": issued_at_utc,
            "request_sha256": request.request_sha256,
            "source_commit": request.source_commit,
            "image_digest": request.image_digest,
            "role": request.role,
            "output_root": request.output_root,
            "output_root_absent_at_issue": True,
            "host_claim_required": True,
            "execution_count": 1,
            "scientific_execution_open": True,
            "arbitrary_code_loading": False,
            "shell_command_loading": False,
            "test_dataset_access": False,
            "publication_permitted": False,
        }
        digest = _sha256_object(payload)
        return cls(
            schema_version=SCIENTIFIC_CAMPAIGN_AUTHORIZATION_SCHEMA_VERSION,
            authorization_id=SCIENTIFIC_CAMPAIGN_AUTHORIZATION_ID,
            status=SCIENTIFIC_CAMPAIGN_AUTHORIZATION_STATUS,
            issued_at_utc=issued_at_utc,
            request_sha256=request.request_sha256,
            source_commit=request.source_commit,
            image_digest=request.image_digest,
            role=request.role,
            output_root=request.output_root,
            output_root_absent_at_issue=True,
            host_claim_required=True,
            execution_count=1,
            scientific_execution_open=True,
            arbitrary_code_loading=False,
            shell_command_loading=False,
            test_dataset_access=False,
            publication_permitted=False,
            authorization_sha256=digest,
        )

    def __post_init__(self) -> None:
        if self.schema_version != SCIENTIFIC_CAMPAIGN_AUTHORIZATION_SCHEMA_VERSION:
            raise ScientificCampaignError("scientific authorization schema_version must be 1")
        if self.authorization_id != SCIENTIFIC_CAMPAIGN_AUTHORIZATION_ID:
            raise ScientificCampaignError("scientific authorization id differs")
        if self.status != SCIENTIFIC_CAMPAIGN_AUTHORIZATION_STATUS:
            raise ScientificCampaignError("scientific authorization status differs")
        if not self.issued_at_utc.endswith("Z"):
            raise ScientificCampaignError("authorization timestamp must be UTC")
        _require_sha256(self.request_sha256, "request_sha256")
        if not _COMMIT_RE.fullmatch(self.source_commit):
            raise ScientificCampaignError("authorization source_commit must be exact")
        _require_sha256(self.image_digest, "image_digest")
        _require_confined_relative(self.output_root, "output_root")
        if not self.output_root_absent_at_issue:
            raise ScientificCampaignError("authorization output root must be absent at issue")
        if not self.host_claim_required:
            raise ScientificCampaignError("authorization must require host-side one-shot claim")
        if self.execution_count != 1:
            raise ScientificCampaignError("authorization must permit exactly one execution")
        if not self.scientific_execution_open:
            raise ScientificCampaignError("authorization must explicitly open one scientific run")
        if any(
            (
                self.arbitrary_code_loading,
                self.shell_command_loading,
                self.test_dataset_access,
                self.publication_permitted,
            )
        ):
            raise ScientificCampaignError(
                "authorization cannot enable code/shell/test/publication effects"
            )
        _require_sha256(self.authorization_sha256, "authorization_sha256")
        if self.authorization_sha256 != self.computed_sha256():
            raise ScientificCampaignError("scientific authorization self hash differs")

    def require_request(self, request: ScientificCampaignRequest) -> None:
        if self.request_sha256 != request.request_sha256:
            raise ScientificCampaignError("authorization request identity differs")
        if self.source_commit != request.source_commit:
            raise ScientificCampaignError("authorization source identity differs")
        if self.image_digest != request.image_digest:
            raise ScientificCampaignError("authorization image identity differs")
        if self.role is not request.role:
            raise ScientificCampaignError("authorization role differs")
        if self.output_root != request.output_root:
            raise ScientificCampaignError("authorization output root differs")

    def payload_without_digest(self) -> dict[str, object]:
        payload = cast(dict[str, object], _canonicalize(asdict(self)))
        payload.pop("authorization_sha256")
        return payload

    def computed_sha256(self) -> str:
        return _sha256_object(self.payload_without_digest())

    def canonical_json(self) -> str:
        return _canonical_json(self)


@dataclass(frozen=True)
class ScientificHostClaim:
    """Host-side one-shot claim created immediately before Docker invocation."""

    schema_version: int
    claim_id: str
    status: str
    request_sha256: str
    authorization_sha256: str
    source_commit: str
    image_digest: str
    role: CampaignRole
    output_root: str
    docker_run_count: int
    automatic_retry_permitted: bool
    test_dataset_access: bool
    publication_permitted: bool
    claim_sha256: str

    @classmethod
    def create(
        cls,
        request: ScientificCampaignRequest,
        authorization: ScientificCampaignAuthorization,
    ) -> ScientificHostClaim:
        authorization.require_request(request)
        payload: dict[str, object] = {
            "schema_version": SCIENTIFIC_HOST_CLAIM_SCHEMA_VERSION,
            "claim_id": SCIENTIFIC_HOST_CLAIM_ID,
            "status": SCIENTIFIC_HOST_CLAIM_STATUS,
            "request_sha256": request.request_sha256,
            "authorization_sha256": authorization.authorization_sha256,
            "source_commit": request.source_commit,
            "image_digest": request.image_digest,
            "role": request.role,
            "output_root": request.output_root,
            "docker_run_count": 1,
            "automatic_retry_permitted": False,
            "test_dataset_access": False,
            "publication_permitted": False,
        }
        digest = _sha256_object(payload)
        return cls(
            schema_version=SCIENTIFIC_HOST_CLAIM_SCHEMA_VERSION,
            claim_id=SCIENTIFIC_HOST_CLAIM_ID,
            status=SCIENTIFIC_HOST_CLAIM_STATUS,
            request_sha256=request.request_sha256,
            authorization_sha256=authorization.authorization_sha256,
            source_commit=request.source_commit,
            image_digest=request.image_digest,
            role=request.role,
            output_root=request.output_root,
            docker_run_count=1,
            automatic_retry_permitted=False,
            test_dataset_access=False,
            publication_permitted=False,
            claim_sha256=digest,
        )

    def __post_init__(self) -> None:
        if self.schema_version != SCIENTIFIC_HOST_CLAIM_SCHEMA_VERSION:
            raise ScientificCampaignError("host claim schema_version differs")
        if self.claim_id != SCIENTIFIC_HOST_CLAIM_ID:
            raise ScientificCampaignError("host claim id differs")
        if self.status != SCIENTIFIC_HOST_CLAIM_STATUS:
            raise ScientificCampaignError("host claim status differs")
        _require_sha256(self.request_sha256, "host claim request sha256")
        _require_sha256(self.authorization_sha256, "host claim authorization sha256")
        if not _COMMIT_RE.fullmatch(self.source_commit):
            raise ScientificCampaignError("host claim source_commit must be exact")
        _require_sha256(self.image_digest, "host claim image digest")
        _require_confined_relative(self.output_root, "host claim output_root")
        if self.docker_run_count != 1:
            raise ScientificCampaignError("host claim must permit exactly one docker run")
        if self.automatic_retry_permitted:
            raise ScientificCampaignError("host claim cannot permit automatic retry")
        if self.test_dataset_access or self.publication_permitted:
            raise ScientificCampaignError("host claim cannot open test/publication")
        _require_sha256(self.claim_sha256, "host claim sha256")
        if self.claim_sha256 != self.computed_sha256():
            raise ScientificCampaignError("host claim self hash differs")

    def require(
        self,
        request: ScientificCampaignRequest,
        authorization: ScientificCampaignAuthorization,
    ) -> None:
        authorization.require_request(request)
        exact = {
            "request_sha256": request.request_sha256,
            "authorization_sha256": authorization.authorization_sha256,
            "source_commit": request.source_commit,
            "image_digest": request.image_digest,
            "role": request.role,
            "output_root": request.output_root,
        }
        for name, expected in exact.items():
            if getattr(self, name) != expected:
                raise ScientificCampaignError(f"host claim {name} differs")

    def payload_without_digest(self) -> dict[str, object]:
        payload = cast(dict[str, object], _canonicalize(asdict(self)))
        payload.pop("claim_sha256")
        return payload

    def computed_sha256(self) -> str:
        return _sha256_object(self.payload_without_digest())

    def canonical_json(self) -> str:
        return _canonical_json(self)


def load_scientific_host_claim(path: Path) -> ScientificHostClaim:
    """Load one canonical host claim without executing any effect."""

    payload = _read_json(path)
    claim = ScientificHostClaim(
        schema_version=_int(payload, "schema_version"),
        claim_id=_str(payload, "claim_id"),
        status=_str(payload, "status"),
        request_sha256=_str(payload, "request_sha256"),
        authorization_sha256=_str(payload, "authorization_sha256"),
        source_commit=_str(payload, "source_commit"),
        image_digest=_str(payload, "image_digest"),
        role=CampaignRole(_str(payload, "role")),
        output_root=_str(payload, "output_root"),
        docker_run_count=_int(payload, "docker_run_count"),
        automatic_retry_permitted=_bool(payload, "automatic_retry_permitted"),
        test_dataset_access=_bool(payload, "test_dataset_access"),
        publication_permitted=_bool(payload, "publication_permitted"),
        claim_sha256=_str(payload, "claim_sha256"),
    )
    if path.read_text(encoding="utf-8") != claim.canonical_json():
        raise ScientificCampaignError("host claim file is not canonical")
    return claim


def load_scientific_request(path: Path) -> ScientificCampaignRequest:
    """Load one canonical request without executing any campaign effect."""

    payload = _read_json(path)
    dataset_raw = payload.get("dataset")
    dataset = None if dataset_raw is None else _dataset_binding(dataset_raw)
    request = ScientificCampaignRequest(
        schema_version=_int(payload, "schema_version"),
        request_id=_str(payload, "request_id"),
        role=CampaignRole(_str(payload, "role")),
        backend_id=ScientificBackendId(_str(payload, "backend_id")),
        source_commit=_str(payload, "source_commit"),
        image_digest=_str(payload, "image_digest"),
        manifest_sha256=_str(payload, "manifest_sha256"),
        code_manifest_sha256=_str(payload, "code_manifest_sha256"),
        dataset=dataset,
        sealed_c1_dataset=_optional_artifact(payload.get("sealed_c1_dataset")),
        candidate_policies=tuple(
            _artifact(item) for item in _list(payload, "candidate_policies")
        ),
        frozen_policy=_optional_artifact(payload.get("frozen_policy")),
        predecessor_receipts=tuple(
            _receipt_binding(item) for item in _list(payload, "predecessor_receipts")
        ),
        model_seeds=tuple(_int_value(item, "model_seed") for item in _list(payload, "model_seeds")),
        component_sequence=tuple(
            PipelineComponentId(_str_value(item, "component_sequence item"))
            for item in _list(payload, "component_sequence")
        ),
        output_root=_str(payload, "output_root"),
        control_overhead_lower_bound_ns=_int(payload, "control_overhead_lower_bound_ns"),
        arbitrary_code_loading=_bool(payload, "arbitrary_code_loading"),
        shell_command_loading=_bool(payload, "shell_command_loading"),
        test_dataset_access=_bool(payload, "test_dataset_access"),
        publication_permitted=_bool(payload, "publication_permitted"),
        request_sha256=_str(payload, "request_sha256"),
    )
    if path.read_text(encoding="utf-8") != request.canonical_json():
        raise ScientificCampaignError("request file is not canonical")
    return request


def load_scientific_authorization(path: Path) -> ScientificCampaignAuthorization:
    """Load one canonical authorization without consuming it."""

    payload = _read_json(path)
    authorization = ScientificCampaignAuthorization(
        schema_version=_int(payload, "schema_version"),
        authorization_id=_str(payload, "authorization_id"),
        status=_str(payload, "status"),
        issued_at_utc=_str(payload, "issued_at_utc"),
        request_sha256=_str(payload, "request_sha256"),
        source_commit=_str(payload, "source_commit"),
        image_digest=_str(payload, "image_digest"),
        role=CampaignRole(_str(payload, "role")),
        output_root=_str(payload, "output_root"),
        output_root_absent_at_issue=_bool(payload, "output_root_absent_at_issue"),
        host_claim_required=_bool(payload, "host_claim_required"),
        execution_count=_int(payload, "execution_count"),
        scientific_execution_open=_bool(payload, "scientific_execution_open"),
        arbitrary_code_loading=_bool(payload, "arbitrary_code_loading"),
        shell_command_loading=_bool(payload, "shell_command_loading"),
        test_dataset_access=_bool(payload, "test_dataset_access"),
        publication_permitted=_bool(payload, "publication_permitted"),
        authorization_sha256=_str(payload, "authorization_sha256"),
    )
    if path.read_text(encoding="utf-8") != authorization.canonical_json():
        raise ScientificCampaignError("authorization file is not canonical")
    return authorization


def _dataset_binding(value: object) -> ScientificDatasetBinding:
    payload = _mapping(value, "dataset")
    return ScientificDatasetBinding(
        dataset_name=_str(payload, "dataset_name"),
        dataset_root=_str(payload, "dataset_root"),
        split=_artifact(payload.get("split")),
        dataset_assets=tuple(
            _artifact(item) for item in _list(payload, "dataset_assets")
        ),
        split_key=_str(payload, "split_key"),
        partition=ScientificDataPartition(_str(payload, "partition")),
        batches=tuple(_batch(item) for item in _list(payload, "batches")),
    )


def _batch(value: object) -> ScientificBatchSpec:
    payload = _mapping(value, "batch")
    return ScientificBatchSpec(
        batch_id=_str(payload, "batch_id"),
        indices=tuple(_int_value(item, "batch index") for item in _list(payload, "indices")),
    )


def _artifact(value: object) -> ArtifactBinding:
    payload = _mapping(value, "artifact")
    return ArtifactBinding(
        relative_path=_str(payload, "relative_path"),
        sha256=_str(payload, "sha256"),
    )


def _receipt_binding(value: object) -> ProtocolReceiptBinding:
    payload = _mapping(value, "receipt binding")
    return ProtocolReceiptBinding(
        kind=ReceiptKind(_str(payload, "kind")),
        relative_path=_str(payload, "relative_path"),
        receipt_sha256=_str(payload, "receipt_sha256"),
        file_sha256=_str(payload, "file_sha256"),
    )


def _optional_artifact(value: object) -> ArtifactBinding | None:
    return None if value is None else _artifact(value)


def _require_live_dataset(
    dataset: ScientificDatasetBinding | None,
    partition: ScientificDataPartition,
) -> None:
    if dataset is None or dataset.partition is not partition:
        raise ScientificCampaignError(f"live role requires {partition.value} data")


def _require_unique_artifacts(values: tuple[ArtifactBinding, ...]) -> None:
    paths = tuple(item.relative_path for item in values)
    if len(paths) != len(set(paths)) or paths != tuple(sorted(paths)):
        raise ScientificCampaignError("artifact bindings must be unique and sorted")


def _require_artifact_namespace(value: str, field_name: str) -> None:
    parts = Path(value).parts
    if not parts:
        raise ScientificCampaignError(f"{field_name} has no namespace")
    if parts[0] in {"data", "results"}:
        return
    if len(parts) >= 2 and parts[:2] == ("experiments", "frozen"):
        return
    raise ScientificCampaignError(
        f"{field_name} must remain under data/, results/, or experiments/frozen/"
    )


def _require_nondata_artifact_namespace(value: str, field_name: str) -> None:
    _require_artifact_namespace(value, field_name)
    if Path(value).parts[0] == "data":
        raise ScientificCampaignError(
            f"{field_name} cannot use the live data namespace"
        )


def _require_confined_relative(value: str, field_name: str) -> None:
    path = Path(value)
    if not value.strip() or path.is_absolute() or path == Path(".") or ".." in path.parts:
        raise ScientificCampaignError(f"{field_name} must be a confined relative path")


def _require_sha256(value: str, field_name: str) -> None:
    if not _SHA256_RE.fullmatch(value):
        raise ScientificCampaignError(f"{field_name} must be sha256:<64 hex>")


def _canonicalize(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _canonicalize(asdict(value))
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _canonicalize(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, tuple | list):
        return [_canonicalize(item) for item in value]
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


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise ScientificCampaignError(f"regular JSON file required: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ScientificCampaignError(f"invalid JSON: {path}") from exc
    if not isinstance(value, dict):
        raise ScientificCampaignError(f"JSON object required: {path}")
    return cast(dict[str, Any], value)


def _mapping(value: object, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ScientificCampaignError(f"{field_name} must be an object")
    return cast(dict[str, Any], value)


def _list(payload: dict[str, Any], field_name: str) -> list[object]:
    value = payload.get(field_name)
    if not isinstance(value, list):
        raise ScientificCampaignError(f"{field_name} must be a list")
    return cast(list[object], value)


def _str(payload: dict[str, Any], field_name: str) -> str:
    return _str_value(payload.get(field_name), field_name)


def _str_value(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise ScientificCampaignError(f"{field_name} must be a string")
    return value


def _int(payload: dict[str, Any], field_name: str) -> int:
    return _int_value(payload.get(field_name), field_name)


def _int_value(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ScientificCampaignError(f"{field_name} must be an integer")
    return value


def _bool(payload: dict[str, Any], field_name: str) -> bool:
    value = payload.get(field_name)
    if not isinstance(value, bool):
        raise ScientificCampaignError(f"{field_name} must be a boolean")
    return value
