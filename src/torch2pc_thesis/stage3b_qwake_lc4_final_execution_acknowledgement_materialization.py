"""Bounded final-execution acknowledgement materialization implementation.

The module exposes one explicit effectful API that validates the complete
frozen authoring chain, delegates exactly one immutable write to the already
verified acknowledgement writer, and then re-verifies the exact persisted
bytes. Importing or statically verifying this module does not call the writer,
create the production acknowledgement, create a lease or outcome, inspect an
image, materialize a command, spawn a process, invoke Docker, consume
authorization, or execute local compute.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
import stat
from collections.abc import Mapping
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Final, cast

from .stage3b_qwake_lc4_final_execution_acknowledgement_authoring import (
    DURABLE_HOST_OUTCOME_RELATIVE,
    EXECUTION_LEASE_V2_RELATIVE,
    FinalExecutionAcknowledgementAuthoring,
    WiringMergeValidationReceipt,
    load_final_execution_acknowledgement_authoring,
    load_wiring_merge_validation_receipt,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_issuance_authoring import (
    ACKNOWLEDGEMENT_RELATIVE,
    UPSTREAM_AUTHORING_RECORD_RELATIVE,
    UPSTREAM_WIRING_RECEIPT_RELATIVE,
    AcknowledgementAuthoringMergeValidationReceipt,
    FinalExecutionAcknowledgementIssuanceAuthoring,
    canonical_json,
    load_acknowledgement_authoring_merge_validation_receipt,
    load_final_execution_acknowledgement_issuance_authoring,
    sha256_bytes,
    sha256_object,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_issuance_authoring import (
    AUTHORING_MERGE_RECEIPT_RELATIVE as ISSUANCE_AUTHORING_MERGE_RECEIPT_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_issuance_authoring import (
    AUTHORING_RECORD_RELATIVE as ISSUANCE_AUTHORING_RECORD_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_issuance_implementation import (
    LEGACY_EXECUTION_LEASE_RELATIVE,
    AcknowledgementIssuanceImplementationError,
    PersistentAcknowledgementWriteResult,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_issuance_implementation import (
    persist_final_execution_acknowledgement as _persist_acknowledgement_once,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_issuance_implementation import (
    verify_persisted_final_execution_acknowledgement as _verify_persisted_acknowledgement_once,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_authoring import (
    ADR_EN_RELATIVE as MATERIALIZATION_AUTHORING_ADR_EN_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_authoring import (
    ADR_RU_RELATIVE as MATERIALIZATION_AUTHORING_ADR_RU_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_authoring import (
    AUTHORING_RECORD_RELATIVE as MATERIALIZATION_AUTHORING_RECORD_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_authoring import (
    IMPLEMENTATION_MERGE_RECEIPT_RELATIVE as MATERIALIZATION_AUTHORING_MERGE_RECEIPT_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_authoring import (
    MODULE_RELATIVE as MATERIALIZATION_AUTHORING_MODULE_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_authoring import (
    PACKAGE_RELATIVE as MATERIALIZATION_AUTHORING_PACKAGE_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_authoring import (
    REGISTRY_RELATIVE as MATERIALIZATION_AUTHORING_REGISTRY_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_authoring import (
    SOURCE_REGISTRY_RELATIVE as MATERIALIZATION_AUTHORING_SOURCE_REGISTRY_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_authoring import (
    TEST_RELATIVE as MATERIALIZATION_AUTHORING_TEST_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_authoring import (
    VERIFIER_RELATIVE as MATERIALIZATION_AUTHORING_VERIFIER_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_authoring import (
    AcknowledgementIssuanceImplementationMergeValidationReceipt,
    FinalExecutionAcknowledgementMaterializationAuthoring,
    FinalExecutionAcknowledgementMaterializationAuthoringError,
    ProspectiveFinalExecutionAcknowledgementMaterialization,
    load_acknowledgement_issuance_implementation_merge_validation_receipt,
    load_final_execution_acknowledgement_materialization_authoring,
)

FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_IMPLEMENTATION_ID: Final = (
    "stage3b-qwake-lc4-e-final-execution-acknowledgement-"
    "materialization-implementation-v1"
)
FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_IMPLEMENTATION_STATUS: Final = (
    "acknowledgement_materializer_implemented_not_called_execution_closed"
)
MATERIALIZATION_IMPLEMENTATION_BASE_COMMIT: Final = (
    "6497cd904f9403622249c5a32f08ef6e8bb11532"
)
MATERIALIZATION_AUTHORING_PR_NUMBER: Final = 150
MATERIALIZATION_AUTHORING_HEAD_COMMIT: Final = (
    "dfcd8b6f054902fb5df74f315a22bcb56c5933ee"
)
MATERIALIZATION_AUTHORING_PARENT_COMMIT: Final = (
    "31206012ef7cbd2b7b21a2017374c11123abd42c"
)
MATERIALIZATION_AUTHORING_MERGE_COMMIT: Final = MATERIALIZATION_IMPLEMENTATION_BASE_COMMIT
MATERIALIZATION_AUTHORING_MERGED_AT_UTC: Final = "2026-07-30T20:59:03Z"

MATERIALIZATION_AUTHORING_SHA256: Final = (
    "sha256:0e947970376b04da3b0ad75507bb8d671d34f6f2b042077cd0c243db6bd346d5"
)
MATERIALIZATION_AUTHORING_FILE_SHA256: Final = (
    "sha256:df16a5ad68b4b3b51c1decd4cae20c0b4f281994d3b803de4241b25716f55a99"
)
MATERIALIZATION_AUTHORING_MERGE_RECEIPT_FILE_SHA256: Final = (
    "sha256:615719d54bce9e9b953b216378cc89eee8dcfa2461d17eb5dff1c069f944478c"
)
MATERIALIZATION_AUTHORING_PACKAGE_REGISTRY_SHA256: Final = (
    "sha256:e478423cf50417267541705e1606b72e47530058377d30b6531889c332427f9f"
)
MATERIALIZATION_AUTHORING_SOURCE_REGISTRY_SHA256: Final = (
    "sha256:8bc01815c733a5c7258524b77abf753b5a7aec0c8955731bb8a5c1e5f92bb962"
)
MATERIALIZATION_AUTHORING_MODULE_SHA256: Final = (
    "sha256:8da29b7347af2999a9300addbf4b7de02498bdef8a9b85197d1f471cc11d43ee"
)
MATERIALIZATION_AUTHORING_VERIFIER_SHA256: Final = (
    "sha256:3d3205385f71f79c0a251ba029679ed24167a3ee57a882c01fb3d493474739ac"
)
MATERIALIZATION_AUTHORING_TEST_SHA256: Final = (
    "sha256:114dee4a203d781ce6f667d213f70fe599fe68b9cd60c0083631f42f96e72bf0"
)
MATERIALIZATION_AUTHORING_ADR_RU_SHA256: Final = (
    "sha256:fed6e29e4014883552361137f4efc6460df6015796dbf2498e033f4182cb1d33"
)
MATERIALIZATION_AUTHORING_ADR_EN_SHA256: Final = (
    "sha256:cfa2819b8eacd1d817ea9d970e94b5bc38105d889b24c461405cc073f87ccd16"
)

IMPLEMENTATION_PACKAGE_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-final-execution-acknowledgement-"
    "materialization-implementation-v1"
)
IMPLEMENTATION_RECORD_RELATIVE: Final = IMPLEMENTATION_PACKAGE_RELATIVE / "implementation.json"
AUTHORING_MERGE_RECEIPT_RELATIVE: Final = (
    IMPLEMENTATION_PACKAGE_RELATIVE / "authoring-merge-validation.json"
)
IMPLEMENTATION_REGISTRY_RELATIVE: Final = IMPLEMENTATION_PACKAGE_RELATIVE / "SHA256SUMS"
IMPLEMENTATION_SOURCE_REGISTRY_RELATIVE: Final = (
    IMPLEMENTATION_PACKAGE_RELATIVE / "source-SHA256SUMS"
)
IMPLEMENTATION_MODULE_RELATIVE: Final = Path(
    "src/torch2pc_thesis/"
    "stage3b_qwake_lc4_final_execution_acknowledgement_materialization.py"
)
IMPLEMENTATION_VERIFIER_RELATIVE: Final = Path(
    "scripts/verify_stage3b_qwake_lc4_"
    "final_execution_acknowledgement_materialization.py"
)
IMPLEMENTATION_TEST_RELATIVE: Final = Path(
    "tests/unit/test_stage3b_qwake_lc4_"
    "final_execution_acknowledgement_materialization.py"
)
IMPLEMENTATION_ADR_RU_RELATIVE: Final = Path(
    "docs/decisions/ADR-090-stage3b-qwake-lc4-e-"
    "final-execution-acknowledgement-materialization-implementation.md"
)
IMPLEMENTATION_ADR_EN_RELATIVE: Final = Path(
    "docs/decisions/ADR-090-stage3b-qwake-lc4-e-"
    "final-execution-acknowledgement-materialization-implementation_EN.md"
)

_EXPECTED_PACKAGE_FILES: Final = frozenset(
    {"SHA256SUMS", "authoring-merge-validation.json", "implementation.json", "source-SHA256SUMS"}
)
_EXPECTED_SOURCE_PATHS: Final = frozenset(
    {
        MATERIALIZATION_AUTHORING_RECORD_RELATIVE.as_posix(),
        MATERIALIZATION_AUTHORING_MERGE_RECEIPT_RELATIVE.as_posix(),
        MATERIALIZATION_AUTHORING_REGISTRY_RELATIVE.as_posix(),
        MATERIALIZATION_AUTHORING_SOURCE_REGISTRY_RELATIVE.as_posix(),
        MATERIALIZATION_AUTHORING_MODULE_RELATIVE.as_posix(),
        MATERIALIZATION_AUTHORING_VERIFIER_RELATIVE.as_posix(),
        MATERIALIZATION_AUTHORING_TEST_RELATIVE.as_posix(),
        MATERIALIZATION_AUTHORING_ADR_RU_RELATIVE.as_posix(),
        MATERIALIZATION_AUTHORING_ADR_EN_RELATIVE.as_posix(),
        IMPLEMENTATION_MODULE_RELATIVE.as_posix(),
        IMPLEMENTATION_VERIFIER_RELATIVE.as_posix(),
        IMPLEMENTATION_TEST_RELATIVE.as_posix(),
        IMPLEMENTATION_ADR_RU_RELATIVE.as_posix(),
        IMPLEMENTATION_ADR_EN_RELATIVE.as_posix(),
    }
)
_SHA256_PATTERN: Final = re.compile(r"^sha256:[0-9a-f]{64}$")
_COMMIT_PATTERN: Final = re.compile(r"^[0-9a-f]{40}$")
_FORBIDDEN_IMPORT_ROOTS: Final = frozenset({"docker", "subprocess"})
_FORBIDDEN_CALL_NAMES: Final = frozenset(
    {
        "inspect_local_image",
        "invoke_lease_bound_host_runtime",
        "invoke_one_shot_host_runtime",
        "materialize_invocation_command",
        "persist_durable_host_outcome_receipt",
        "persist_persistent_execution_lease_v2",
    }
)
_FORBIDDEN_DIRECT_WRITE_CALLS: Final = frozenset(
    {
        "hardlink_to",
        "link",
        "mkdir",
        "open",
        "rename",
        "replace",
        "symlink_to",
        "touch",
        "unlink",
        "write_bytes",
        "write_text",
    }
)

__all__ = [
    "FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_IMPLEMENTATION_ID",
    "AcknowledgementMaterializationAuthoringMergeValidationReceipt",
    "FinalExecutionAcknowledgementMaterializationImplementationContract",
    "FinalExecutionAcknowledgementMaterializationImplementationError",
    "FinalExecutionAcknowledgementMaterializationImplementationGates",
    "FinalExecutionAcknowledgementMaterializationImplementationRecord",
    "FinalExecutionAcknowledgementMaterializationImplementationSource",
    "FinalExecutionAcknowledgementMaterializationResult",
    "build_frozen_acknowledgement_materialization_implementation_record",
    "build_materialization_authoring_merge_validation_receipt",
    "load_acknowledgement_materialization_authoring_merge_validation_receipt",
    "load_final_execution_acknowledgement_materialization_implementation_record",
    "materialize_final_execution_acknowledgement",
    "verify_final_execution_acknowledgement_materialization_implementation",
]


class FinalExecutionAcknowledgementMaterializationImplementationError(RuntimeError):
    """Raised when the bounded materialization implementation fails closed."""


def _require_sha256(value: str, field_name: str) -> None:
    if not _SHA256_PATTERN.fullmatch(value):
        raise FinalExecutionAcknowledgementMaterializationImplementationError(
            f"{field_name} is not a canonical SHA-256 identity"
        )


def _require_commit(value: str, field_name: str) -> None:
    if not _COMMIT_PATTERN.fullmatch(value):
        raise FinalExecutionAcknowledgementMaterializationImplementationError(
            f"{field_name} is not a commit identity"
        )


@dataclass(frozen=True)
class AcknowledgementMaterializationAuthoringMergeValidationReceipt:
    """Exact post-merge receipt for materialization-authoring PR #150."""

    receipt_id: str
    pr_number: int
    head_commit: str
    base_commit: str
    merge_commit: str
    merged_at_utc: str
    commit_count: int
    file_count: int
    focused_tests_passed: int
    targeted_tests_passed: int
    full_tests_passed: int
    full_test_warnings: int
    required_ci_checks_passed: bool
    production_execution_boundary_closed: bool
    receipt_sha256: str

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, object],
    ) -> AcknowledgementMaterializationAuthoringMergeValidationReceipt:
        return cls(**cast(dict[str, Any], dict(value)))

    def semantic_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload.pop("receipt_sha256")
        return cast(dict[str, object], payload)

    def require(self) -> None:
        expected: dict[str, object] = {
            "receipt_id": (
                "stage3b-qwake-lc4-e-final-execution-acknowledgement-"
                "materialization-authoring-post-merge-validation-v1"
            ),
            "pr_number": MATERIALIZATION_AUTHORING_PR_NUMBER,
            "head_commit": MATERIALIZATION_AUTHORING_HEAD_COMMIT,
            "base_commit": MATERIALIZATION_AUTHORING_PARENT_COMMIT,
            "merge_commit": MATERIALIZATION_AUTHORING_MERGE_COMMIT,
            "merged_at_utc": MATERIALIZATION_AUTHORING_MERGED_AT_UTC,
            "commit_count": 1,
            "file_count": 18,
            "focused_tests_passed": 92,
            "targeted_tests_passed": 293,
            "full_tests_passed": 1340,
            "full_test_warnings": 14,
            "required_ci_checks_passed": True,
            "production_execution_boundary_closed": True,
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise FinalExecutionAcknowledgementMaterializationImplementationError(
                    f"materialization authoring merge receipt differs: {field_name}"
                )
        _require_commit(self.head_commit, "head_commit")
        _require_commit(self.base_commit, "base_commit")
        _require_commit(self.merge_commit, "merge_commit")
        _require_sha256(self.receipt_sha256, "receipt_sha256")
        if self.receipt_sha256 != sha256_object(self.semantic_payload()):
            raise FinalExecutionAcknowledgementMaterializationImplementationError(
                "materialization authoring merge receipt semantic SHA-256 differs"
            )

    def canonical_json(self) -> str:
        self.require()
        return canonical_json(self)


@dataclass(frozen=True)
class FinalExecutionAcknowledgementMaterializationImplementationSource:
    """Exact frozen inputs for the bounded materializer implementation."""

    implementation_base_commit: str
    materialization_authoring_id: str
    materialization_authoring_sha256: str
    materialization_authoring_file_sha256: str
    materialization_authoring_merge_receipt_file_sha256: str
    materialization_authoring_package_registry_sha256: str
    materialization_authoring_source_registry_sha256: str
    materialization_authoring_module_sha256: str
    materialization_authoring_verifier_sha256: str
    materialization_authoring_test_sha256: str
    materialization_authoring_adr_ru_sha256: str
    materialization_authoring_adr_en_sha256: str
    materialization_authoring_pr_number: int
    materialization_authoring_head_commit: str
    materialization_authoring_parent_commit: str
    materialization_authoring_merge_commit: str
    materialization_authoring_merged_at_utc: str
    acknowledgement_relative: str
    legacy_execution_lease_relative: str
    execution_lease_v2_relative: str
    durable_host_outcome_relative: str
    acknowledgement_writer_symbol: str
    acknowledgement_verifier_symbol: str

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, object],
    ) -> FinalExecutionAcknowledgementMaterializationImplementationSource:
        return cls(**cast(dict[str, Any], dict(value)))

    def require(
        self,
        receipt: AcknowledgementMaterializationAuthoringMergeValidationReceipt,
    ) -> None:
        receipt.require()
        if self != _build_source(receipt):
            raise FinalExecutionAcknowledgementMaterializationImplementationError(
                "materialization implementation source differs"
            )


@dataclass(frozen=True)
class FinalExecutionAcknowledgementMaterializationImplementationContract:
    """Narrow implementation rules for one explicit future call."""

    complete_authoring_identity_verified: bool
    prospective_materialization_required: bool
    exact_writer_delegate_required: bool
    writer_call_limit: int
    exact_postwrite_reverification_required: bool
    verifier_call_limit: int
    writer_result_equality_required: bool
    direct_filesystem_write_forbidden: bool
    subprocess_forbidden: bool
    docker_forbidden: bool
    image_inspection_forbidden: bool
    command_materialization_forbidden: bool
    lease_materialization_forbidden: bool
    durable_outcome_persistence_forbidden: bool
    authorization_consumption_forbidden: bool
    local_compute_forbidden: bool
    production_callsite_separate: bool
    repository_materializer_callsite_forbidden: bool
    automatic_retry_forbidden: bool
    test_writes_isolated_only: bool

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, object],
    ) -> FinalExecutionAcknowledgementMaterializationImplementationContract:
        return cls(**cast(dict[str, Any], dict(value)))

    def require(self) -> None:
        if self != _build_contract():
            raise FinalExecutionAcknowledgementMaterializationImplementationError(
                "materialization implementation contract differs"
            )


@dataclass(frozen=True)
class FinalExecutionAcknowledgementMaterializationImplementationGates:
    """Closed production state after implementing, but not calling, the materializer."""

    materialization_authoring_post_merge_verified: bool
    acknowledgement_materialization_contract_authored: bool
    acknowledgement_materialization_implemented: bool
    final_execution_acknowledgement_issued: bool
    final_execution_acknowledged: bool
    one_shot_engineering_invocation_permitted: bool
    execution_lease_materialized: bool
    durable_host_outcome_present: bool
    authorization_consumed: bool
    runtime_execution_started: bool
    runtime_execution_performed: bool
    image_inspection_performed: bool
    invocation_command_materialized: bool
    docker_run_performed: bool
    local_compute_execution_open: bool

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, object],
    ) -> FinalExecutionAcknowledgementMaterializationImplementationGates:
        return cls(**cast(dict[str, Any], dict(value)))

    def require(self) -> None:
        if self != _build_gates():
            raise FinalExecutionAcknowledgementMaterializationImplementationError(
                "materialization implementation gates differ"
            )


@dataclass(frozen=True)
class FinalExecutionAcknowledgementMaterializationImplementationRecord:
    """Frozen identity of the bounded materializer implementation."""

    schema_version: int
    implementation_id: str
    status: str
    recorded_at_utc: str
    source: FinalExecutionAcknowledgementMaterializationImplementationSource
    contract: FinalExecutionAcknowledgementMaterializationImplementationContract
    gates: FinalExecutionAcknowledgementMaterializationImplementationGates
    next_slice: str
    post_merge_next_slice: str
    implementation_sha256: str

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, object],
    ) -> FinalExecutionAcknowledgementMaterializationImplementationRecord:
        payload = dict(value)
        payload["source"] = (
            FinalExecutionAcknowledgementMaterializationImplementationSource.from_mapping(
                cast(Mapping[str, object], payload["source"])
            )
        )
        payload["contract"] = (
            FinalExecutionAcknowledgementMaterializationImplementationContract.from_mapping(
                cast(Mapping[str, object], payload["contract"])
            )
        )
        payload["gates"] = (
            FinalExecutionAcknowledgementMaterializationImplementationGates.from_mapping(
                cast(Mapping[str, object], payload["gates"])
            )
        )
        return cls(**cast(dict[str, Any], payload))

    def semantic_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload.pop("implementation_sha256")
        return cast(dict[str, object], payload)

    def require(
        self,
        receipt: AcknowledgementMaterializationAuthoringMergeValidationReceipt,
    ) -> None:
        if self.schema_version != 1:
            raise FinalExecutionAcknowledgementMaterializationImplementationError(
                "materialization implementation schema differs"
            )
        if self.implementation_id != (
            FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_IMPLEMENTATION_ID
        ):
            raise FinalExecutionAcknowledgementMaterializationImplementationError(
                "materialization implementation ID differs"
            )
        if self.status != (
            FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_IMPLEMENTATION_STATUS
        ):
            raise FinalExecutionAcknowledgementMaterializationImplementationError(
                "materialization implementation status differs"
            )
        if self.next_slice != (
            "QW-LC4-E-final-execution-acknowledgement-"
            "materialization-implementation-commit"
        ):
            raise FinalExecutionAcknowledgementMaterializationImplementationError(
                "materialization implementation next slice differs"
            )
        if self.post_merge_next_slice != (
            "QW-LC4-E-final-execution-acknowledgement-"
            "materialization-invocation-authoring"
        ):
            raise FinalExecutionAcknowledgementMaterializationImplementationError(
                "materialization implementation post-merge next slice differs"
            )
        self.source.require(receipt)
        self.contract.require()
        self.gates.require()
        _require_sha256(self.implementation_sha256, "implementation_sha256")
        if self.implementation_sha256 != sha256_object(self.semantic_payload()):
            raise FinalExecutionAcknowledgementMaterializationImplementationError(
                "materialization implementation semantic SHA-256 differs"
            )

    def canonical_json(
        self,
        receipt: AcknowledgementMaterializationAuthoringMergeValidationReceipt,
    ) -> str:
        self.require(receipt)
        return canonical_json(self)


@dataclass(frozen=True)
class FinalExecutionAcknowledgementMaterializationResult:
    """In-memory evidence returned only after one successful explicit call."""

    materialization_id: str
    materialization_authoring_sha256: str
    relative_path: str
    byte_count: int
    persisted_sha256: str
    mode: int
    exact_persisted_bytes_verified: bool
    final_execution_acknowledgement_issued: bool
    final_execution_acknowledged: bool
    one_shot_engineering_invocation_permitted: bool
    execution_lease_materialized: bool
    authorization_consumed: bool

    def require(
        self,
        materialization: ProspectiveFinalExecutionAcknowledgementMaterialization,
        expected_persisted_sha256: str,
    ) -> None:
        expected: dict[str, object] = {
            "materialization_id": materialization.materialization_id,
            "materialization_authoring_sha256": (
                materialization.materialization_authoring_sha256
            ),
            "relative_path": ACKNOWLEDGEMENT_RELATIVE.as_posix(),
            "persisted_sha256": expected_persisted_sha256,
            "mode": 0o600,
            "exact_persisted_bytes_verified": True,
            "final_execution_acknowledgement_issued": True,
            "final_execution_acknowledged": True,
            "one_shot_engineering_invocation_permitted": False,
            "execution_lease_materialized": False,
            "authorization_consumed": False,
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise FinalExecutionAcknowledgementMaterializationImplementationError(
                    f"materialization result differs: {field_name}"
                )
        if self.byte_count <= 0:
            raise FinalExecutionAcknowledgementMaterializationImplementationError(
                "materialization result is empty"
            )


def materialize_final_execution_acknowledgement(
    project_root: Path,
    authoring: FinalExecutionAcknowledgementMaterializationAuthoring,
    authoring_receipt: AcknowledgementIssuanceImplementationMergeValidationReceipt,
    issuance_authoring: FinalExecutionAcknowledgementIssuanceAuthoring,
    issuance_receipt: AcknowledgementAuthoringMergeValidationReceipt,
    upstream_authoring: FinalExecutionAcknowledgementAuthoring,
    upstream_receipt: WiringMergeValidationReceipt,
    materialization: ProspectiveFinalExecutionAcknowledgementMaterialization,
) -> FinalExecutionAcknowledgementMaterializationResult:
    """Perform one explicitly requested materialization through the frozen writer.

    The function writes only the final acknowledgement. It does not create a
    lease or durable outcome, inspect an image, construct a command, invoke the
    host runtime, consume authorization, or execute local compute.
    """

    root = _verified_root(
        project_root,
        authoring,
        authoring_receipt,
        issuance_authoring,
        issuance_receipt,
        upstream_authoring,
        upstream_receipt,
        require_closed_boundary=True,
    )
    try:
        materialization.require(
            authoring,
            authoring_receipt,
            issuance_authoring,
            issuance_receipt,
            upstream_authoring,
            upstream_receipt,
        )
        payload = materialization.issuance.canonical_json(
            issuance_authoring,
            issuance_receipt,
            upstream_authoring,
            upstream_receipt,
        ).encode("utf-8")
        expected_persisted_sha256 = sha256_bytes(payload)
        persisted = _persist_acknowledgement_once(
            root,
            issuance_authoring,
            issuance_receipt,
            upstream_authoring,
            upstream_receipt,
            materialization.issuance,
        )
        verified = _verify_persisted_acknowledgement_once(
            root,
            issuance_authoring,
            issuance_receipt,
            upstream_authoring,
            upstream_receipt,
            materialization.issuance,
        )
    except (
        AcknowledgementIssuanceImplementationError,
        FinalExecutionAcknowledgementMaterializationAuthoringError,
    ) as exc:
        raise FinalExecutionAcknowledgementMaterializationImplementationError(
            str(exc)
        ) from exc
    _require_write_result(persisted, expected_persisted_sha256)
    _require_write_result(verified, expected_persisted_sha256)
    if persisted != verified:
        raise FinalExecutionAcknowledgementMaterializationImplementationError(
            "persisted acknowledgement verification result differs"
        )
    result = FinalExecutionAcknowledgementMaterializationResult(
        materialization_id=materialization.materialization_id,
        materialization_authoring_sha256=materialization.materialization_authoring_sha256,
        relative_path=persisted.relative_path,
        byte_count=persisted.byte_count,
        persisted_sha256=persisted.sha256,
        mode=persisted.mode,
        exact_persisted_bytes_verified=True,
        final_execution_acknowledgement_issued=True,
        final_execution_acknowledged=True,
        one_shot_engineering_invocation_permitted=False,
        execution_lease_materialized=False,
        authorization_consumed=False,
    )
    result.require(materialization, expected_persisted_sha256)
    return result


def verify_final_execution_acknowledgement_materialization_implementation(
    project_root: Path,
) -> FinalExecutionAcknowledgementMaterializationImplementationRecord:
    """Verify the frozen implementation package without calling the materializer."""

    root = _verified_project_root(project_root)
    receipt, record = _verify_implementation_freeze(root)
    _verify_static_authoring_chain(root)
    _verify_runtime_ast_boundary(root)
    _require_repository_materializer_callsite_absent(root)
    _require_production_boundary_closed(root)
    record.require(receipt)
    return record


def _require_write_result(
    result: PersistentAcknowledgementWriteResult,
    expected_sha256: str,
) -> None:
    result.require()
    if result.sha256 != expected_sha256:
        raise FinalExecutionAcknowledgementMaterializationImplementationError(
            "persisted acknowledgement SHA-256 differs"
        )


def _verified_root(
    project_root: Path,
    supplied_authoring: FinalExecutionAcknowledgementMaterializationAuthoring,
    supplied_authoring_receipt: AcknowledgementIssuanceImplementationMergeValidationReceipt,
    supplied_issuance_authoring: FinalExecutionAcknowledgementIssuanceAuthoring,
    supplied_issuance_receipt: AcknowledgementAuthoringMergeValidationReceipt,
    supplied_upstream_authoring: FinalExecutionAcknowledgementAuthoring,
    supplied_upstream_receipt: WiringMergeValidationReceipt,
    *,
    require_closed_boundary: bool,
) -> Path:
    root = _verified_project_root(project_root)
    _verify_implementation_freeze(root)
    (
        frozen_authoring,
        frozen_authoring_receipt,
        frozen_issuance_authoring,
        frozen_issuance_receipt,
        frozen_upstream_authoring,
        frozen_upstream_receipt,
    ) = _verify_static_authoring_chain(root)
    comparisons = (
        (
            supplied_authoring.canonical_json(supplied_authoring_receipt),
            frozen_authoring.canonical_json(frozen_authoring_receipt),
            "supplied materialization authoring differs from frozen authoring",
        ),
        (
            supplied_authoring_receipt.canonical_json(),
            frozen_authoring_receipt.canonical_json(),
            "supplied materialization authoring receipt differs from frozen receipt",
        ),
        (
            supplied_issuance_authoring.canonical_json(supplied_issuance_receipt),
            frozen_issuance_authoring.canonical_json(frozen_issuance_receipt),
            "supplied issuance authoring differs from frozen authoring",
        ),
        (
            supplied_issuance_receipt.canonical_json(),
            frozen_issuance_receipt.canonical_json(),
            "supplied issuance receipt differs from frozen receipt",
        ),
        (
            supplied_upstream_authoring.canonical_json(supplied_upstream_receipt),
            frozen_upstream_authoring.canonical_json(frozen_upstream_receipt),
            "supplied acknowledgement authoring differs from frozen authoring",
        ),
        (
            supplied_upstream_receipt.canonical_json(),
            frozen_upstream_receipt.canonical_json(),
            "supplied acknowledgement receipt differs from frozen receipt",
        ),
    )
    for supplied, frozen, message in comparisons:
        if supplied != frozen:
            raise FinalExecutionAcknowledgementMaterializationImplementationError(message)
    if require_closed_boundary:
        _require_production_boundary_closed(root)
    return root


def _verified_project_root(project_root: Path) -> Path:
    expanded = project_root.expanduser()
    if expanded.is_symlink():
        raise FinalExecutionAcknowledgementMaterializationImplementationError(
            "project root is symbolic"
        )
    root = expanded.resolve()
    if not root.is_dir():
        raise FinalExecutionAcknowledgementMaterializationImplementationError(
            "project root is absent or non-directory"
        )
    return root


def _verify_implementation_freeze(
    root: Path,
) -> tuple[
    AcknowledgementMaterializationAuthoringMergeValidationReceipt,
    FinalExecutionAcknowledgementMaterializationImplementationRecord,
]:
    package = root / IMPLEMENTATION_PACKAGE_RELATIVE
    if not package.is_dir() or package.is_symlink():
        raise FinalExecutionAcknowledgementMaterializationImplementationError(
            "materialization implementation package is absent or invalid"
        )
    if {path.name for path in package.iterdir()} != _EXPECTED_PACKAGE_FILES:
        raise FinalExecutionAcknowledgementMaterializationImplementationError(
            "materialization implementation package file set differs"
        )
    _verify_registry(root / IMPLEMENTATION_REGISTRY_RELATIVE, package)
    source_registry = _verify_registry(
        root / IMPLEMENTATION_SOURCE_REGISTRY_RELATIVE,
        root,
    )
    if frozenset(source_registry) != _EXPECTED_SOURCE_PATHS:
        raise FinalExecutionAcknowledgementMaterializationImplementationError(
            "materialization implementation source registry path set differs"
        )
    receipt = load_acknowledgement_materialization_authoring_merge_validation_receipt(
        root / AUTHORING_MERGE_RECEIPT_RELATIVE
    )
    record = load_final_execution_acknowledgement_materialization_implementation_record(
        root / IMPLEMENTATION_RECORD_RELATIVE,
        receipt,
    )
    return receipt, record


def _verify_static_authoring_chain(
    root: Path,
) -> tuple[
    FinalExecutionAcknowledgementMaterializationAuthoring,
    AcknowledgementIssuanceImplementationMergeValidationReceipt,
    FinalExecutionAcknowledgementIssuanceAuthoring,
    AcknowledgementAuthoringMergeValidationReceipt,
    FinalExecutionAcknowledgementAuthoring,
    WiringMergeValidationReceipt,
]:
    _verify_registry(
        root / MATERIALIZATION_AUTHORING_REGISTRY_RELATIVE,
        root / MATERIALIZATION_AUTHORING_PACKAGE_RELATIVE,
    )
    _verify_registry(root / MATERIALIZATION_AUTHORING_SOURCE_REGISTRY_RELATIVE, root)
    authoring_receipt = (
        load_acknowledgement_issuance_implementation_merge_validation_receipt(
            root / MATERIALIZATION_AUTHORING_MERGE_RECEIPT_RELATIVE
        )
    )
    authoring = load_final_execution_acknowledgement_materialization_authoring(
        root / MATERIALIZATION_AUTHORING_RECORD_RELATIVE,
        authoring_receipt,
    )
    issuance_receipt = load_acknowledgement_authoring_merge_validation_receipt(
        root / ISSUANCE_AUTHORING_MERGE_RECEIPT_RELATIVE
    )
    issuance_authoring = load_final_execution_acknowledgement_issuance_authoring(
        root / ISSUANCE_AUTHORING_RECORD_RELATIVE,
        issuance_receipt,
    )
    upstream_receipt = load_wiring_merge_validation_receipt(
        root / UPSTREAM_WIRING_RECEIPT_RELATIVE
    )
    upstream_authoring = load_final_execution_acknowledgement_authoring(
        root / UPSTREAM_AUTHORING_RECORD_RELATIVE,
        upstream_receipt,
    )
    expected: dict[Path, str] = {
        MATERIALIZATION_AUTHORING_RECORD_RELATIVE: MATERIALIZATION_AUTHORING_FILE_SHA256,
        MATERIALIZATION_AUTHORING_MERGE_RECEIPT_RELATIVE: (
            MATERIALIZATION_AUTHORING_MERGE_RECEIPT_FILE_SHA256
        ),
        MATERIALIZATION_AUTHORING_REGISTRY_RELATIVE: (
            MATERIALIZATION_AUTHORING_PACKAGE_REGISTRY_SHA256
        ),
        MATERIALIZATION_AUTHORING_SOURCE_REGISTRY_RELATIVE: (
            MATERIALIZATION_AUTHORING_SOURCE_REGISTRY_SHA256
        ),
        MATERIALIZATION_AUTHORING_MODULE_RELATIVE: MATERIALIZATION_AUTHORING_MODULE_SHA256,
        MATERIALIZATION_AUTHORING_VERIFIER_RELATIVE: (
            MATERIALIZATION_AUTHORING_VERIFIER_SHA256
        ),
        MATERIALIZATION_AUTHORING_TEST_RELATIVE: MATERIALIZATION_AUTHORING_TEST_SHA256,
        MATERIALIZATION_AUTHORING_ADR_RU_RELATIVE: MATERIALIZATION_AUTHORING_ADR_RU_SHA256,
        MATERIALIZATION_AUTHORING_ADR_EN_RELATIVE: MATERIALIZATION_AUTHORING_ADR_EN_SHA256,
    }
    for relative, digest in expected.items():
        path = root / relative
        if not path.is_file() or path.is_symlink():
            raise FinalExecutionAcknowledgementMaterializationImplementationError(
                f"materialization authoring source is absent or invalid: {relative}"
            )
        if sha256_bytes(path.read_bytes()) != digest:
            raise FinalExecutionAcknowledgementMaterializationImplementationError(
                f"materialization authoring source identity differs: {relative}"
            )
    if authoring.authoring_sha256 != MATERIALIZATION_AUTHORING_SHA256:
        raise FinalExecutionAcknowledgementMaterializationImplementationError(
            "materialization authoring semantic identity differs"
        )
    return (
        authoring,
        authoring_receipt,
        issuance_authoring,
        issuance_receipt,
        upstream_authoring,
        upstream_receipt,
    )


def _verify_runtime_ast_boundary(root: Path) -> None:
    writer_bindings = 0
    verifier_bindings = 0
    writer_calls = 0
    verifier_calls = 0
    for relative in (IMPLEMENTATION_MODULE_RELATIVE, IMPLEMENTATION_VERIFIER_RELATIVE):
        path = root / relative
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="strict"))
        except (OSError, UnicodeError, SyntaxError) as exc:
            raise FinalExecutionAcknowledgementMaterializationImplementationError(
                f"materialization implementation Python source is invalid: {path}"
            ) from exc
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots = {alias.name.split(".", 1)[0] for alias in node.names}
                if roots & _FORBIDDEN_IMPORT_ROOTS:
                    raise FinalExecutionAcknowledgementMaterializationImplementationError(
                        f"forbidden materialization implementation import: {path}"
                    )
            if isinstance(node, ast.ImportFrom) and node.module:
                if node.module.split(".", 1)[0] in _FORBIDDEN_IMPORT_ROOTS:
                    raise FinalExecutionAcknowledgementMaterializationImplementationError(
                        f"forbidden materialization implementation import: {path}"
                    )
                if (
                    relative == IMPLEMENTATION_MODULE_RELATIVE
                    and node.module.endswith(
                        "stage3b_qwake_lc4_final_execution_acknowledgement_"
                        "issuance_implementation"
                    )
                ):
                    for alias in node.names:
                        if (
                            alias.name == "persist_final_execution_acknowledgement"
                            and alias.asname == "_persist_acknowledgement_once"
                        ):
                            writer_bindings += 1
                        if (
                            alias.name
                            == "verify_persisted_final_execution_acknowledgement"
                            and alias.asname
                            == "_verify_persisted_acknowledgement_once"
                        ):
                            verifier_bindings += 1
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Name):
                call_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                call_name = node.func.attr
            else:
                call_name = ""
            if call_name in _FORBIDDEN_CALL_NAMES:
                raise FinalExecutionAcknowledgementMaterializationImplementationError(
                    f"forbidden runtime call in materialization implementation: {path}"
                )
            if (
                isinstance(node.func, ast.Attribute)
                and call_name in _FORBIDDEN_DIRECT_WRITE_CALLS
            ):
                raise FinalExecutionAcknowledgementMaterializationImplementationError(
                    f"direct filesystem write in materialization implementation: {path}"
                )
            if relative == IMPLEMENTATION_MODULE_RELATIVE:
                if call_name == "_persist_acknowledgement_once":
                    writer_calls += 1
                if call_name == "_verify_persisted_acknowledgement_once":
                    verifier_calls += 1
    if writer_bindings != 1:
        raise FinalExecutionAcknowledgementMaterializationImplementationError(
            "materialization writer binding count differs"
        )
    if verifier_bindings != 1:
        raise FinalExecutionAcknowledgementMaterializationImplementationError(
            "materialization verifier binding count differs"
        )
    if writer_calls != 1:
        raise FinalExecutionAcknowledgementMaterializationImplementationError(
            "materialization writer call count differs"
        )
    if verifier_calls != 1:
        raise FinalExecutionAcknowledgementMaterializationImplementationError(
            "materialization postwrite verifier call count differs"
        )


def _require_repository_materializer_callsite_absent(root: Path) -> None:
    target_name = "materialize_final_execution_acknowledgement"
    for path in sorted((root / "src").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8", errors="strict"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Name):
                call_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                call_name = node.func.attr
            else:
                call_name = ""
            if call_name == target_name:
                raise FinalExecutionAcknowledgementMaterializationImplementationError(
                    f"production acknowledgement materializer callsite exists: {path}"
                )


def _require_production_boundary_closed(root: Path) -> None:
    output_root = _target(
        root,
        Path("results/stage-3/qwake-lc4-runtime-validation-v1-attempt-001"),
    )
    paths = {
        "authorized output root": output_root,
        "final execution acknowledgement": _target(root, ACKNOWLEDGEMENT_RELATIVE),
        "legacy execution lease": _target(root, LEGACY_EXECUTION_LEASE_RELATIVE),
        "persistent execution lease v2": _target(root, EXECUTION_LEASE_V2_RELATIVE),
        "durable host outcome": _target(root, DURABLE_HOST_OUTCOME_RELATIVE),
    }
    for label, path in paths.items():
        if _lexists(path):
            raise FinalExecutionAcknowledgementMaterializationImplementationError(
                f"{label} already exists: {path}"
            )


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8", errors="strict"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FinalExecutionAcknowledgementMaterializationImplementationError(
            f"frozen JSON is invalid: {path}"
        ) from exc
    if not isinstance(value, dict):
        raise FinalExecutionAcknowledgementMaterializationImplementationError(
            f"frozen JSON root differs: {path}"
        )
    return cast(dict[str, Any], value)


def _verify_registry(path: Path, base: Path) -> dict[str, str]:
    if not path.is_file() or path.is_symlink():
        raise FinalExecutionAcknowledgementMaterializationImplementationError(
            f"frozen registry is absent or invalid: {path}"
        )
    entries: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="strict").splitlines():
        try:
            digest, relative = line.split("  ", 1)
        except ValueError as exc:
            raise FinalExecutionAcknowledgementMaterializationImplementationError(
                f"frozen registry line is invalid: {path}"
            ) from exc
        target = base / relative
        if relative in entries:
            raise FinalExecutionAcknowledgementMaterializationImplementationError(
                f"frozen registry path is duplicated: {relative}"
            )
        if not target.is_file() or target.is_symlink():
            raise FinalExecutionAcknowledgementMaterializationImplementationError(
                f"frozen registry target is absent or invalid: {target}"
            )
        observed = hashlib.sha256(target.read_bytes()).hexdigest()
        if observed != digest:
            raise FinalExecutionAcknowledgementMaterializationImplementationError(
                f"frozen registry target digest differs: {target}"
            )
        entries[relative] = digest
    if not entries:
        raise FinalExecutionAcknowledgementMaterializationImplementationError(
            f"frozen registry is empty: {path}"
        )
    return entries


def _target(root: Path, relative: Path) -> Path:
    if relative.is_absolute() or ".." in relative.parts:
        raise FinalExecutionAcknowledgementMaterializationImplementationError(
            "persistent target path is not repository-relative"
        )
    target = root.joinpath(relative)
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise FinalExecutionAcknowledgementMaterializationImplementationError(
            "persistent target escapes project root"
        ) from exc
    _require_existing_parent_chain(root, target.parent)
    return target


def _require_existing_parent_chain(root: Path, directory: Path) -> None:
    try:
        relative = directory.relative_to(root)
    except ValueError as exc:
        raise FinalExecutionAcknowledgementMaterializationImplementationError(
            "persistent target parent escapes project root"
        ) from exc
    current = root
    for part in relative.parts:
        current = current / part
        try:
            metadata = current.lstat()
        except FileNotFoundError as exc:
            raise FinalExecutionAcknowledgementMaterializationImplementationError(
                f"persistent target parent is absent: {current}"
            ) from exc
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise FinalExecutionAcknowledgementMaterializationImplementationError(
                f"persistent target parent is not a real directory: {current}"
            )


def _lexists(path: Path) -> bool:
    try:
        path.lstat()
    except FileNotFoundError:
        return False
    return True


def load_acknowledgement_materialization_authoring_merge_validation_receipt(
    path: Path,
) -> AcknowledgementMaterializationAuthoringMergeValidationReceipt:
    result = AcknowledgementMaterializationAuthoringMergeValidationReceipt.from_mapping(
        _load_json(path)
    )
    result.require()
    return result


def load_final_execution_acknowledgement_materialization_implementation_record(
    path: Path,
    receipt: AcknowledgementMaterializationAuthoringMergeValidationReceipt,
) -> FinalExecutionAcknowledgementMaterializationImplementationRecord:
    result = FinalExecutionAcknowledgementMaterializationImplementationRecord.from_mapping(
        _load_json(path)
    )
    result.require(receipt)
    return result


def _build_source(
    receipt: AcknowledgementMaterializationAuthoringMergeValidationReceipt,
) -> FinalExecutionAcknowledgementMaterializationImplementationSource:
    receipt.require()
    return FinalExecutionAcknowledgementMaterializationImplementationSource(
        implementation_base_commit=MATERIALIZATION_IMPLEMENTATION_BASE_COMMIT,
        materialization_authoring_id=(
            "stage3b-qwake-lc4-e-final-execution-acknowledgement-"
            "materialization-authoring-v1"
        ),
        materialization_authoring_sha256=MATERIALIZATION_AUTHORING_SHA256,
        materialization_authoring_file_sha256=MATERIALIZATION_AUTHORING_FILE_SHA256,
        materialization_authoring_merge_receipt_file_sha256=(
            MATERIALIZATION_AUTHORING_MERGE_RECEIPT_FILE_SHA256
        ),
        materialization_authoring_package_registry_sha256=(
            MATERIALIZATION_AUTHORING_PACKAGE_REGISTRY_SHA256
        ),
        materialization_authoring_source_registry_sha256=(
            MATERIALIZATION_AUTHORING_SOURCE_REGISTRY_SHA256
        ),
        materialization_authoring_module_sha256=MATERIALIZATION_AUTHORING_MODULE_SHA256,
        materialization_authoring_verifier_sha256=(
            MATERIALIZATION_AUTHORING_VERIFIER_SHA256
        ),
        materialization_authoring_test_sha256=MATERIALIZATION_AUTHORING_TEST_SHA256,
        materialization_authoring_adr_ru_sha256=(
            MATERIALIZATION_AUTHORING_ADR_RU_SHA256
        ),
        materialization_authoring_adr_en_sha256=(
            MATERIALIZATION_AUTHORING_ADR_EN_SHA256
        ),
        materialization_authoring_pr_number=receipt.pr_number,
        materialization_authoring_head_commit=receipt.head_commit,
        materialization_authoring_parent_commit=receipt.base_commit,
        materialization_authoring_merge_commit=receipt.merge_commit,
        materialization_authoring_merged_at_utc=receipt.merged_at_utc,
        acknowledgement_relative=ACKNOWLEDGEMENT_RELATIVE.as_posix(),
        legacy_execution_lease_relative=LEGACY_EXECUTION_LEASE_RELATIVE.as_posix(),
        execution_lease_v2_relative=EXECUTION_LEASE_V2_RELATIVE.as_posix(),
        durable_host_outcome_relative=DURABLE_HOST_OUTCOME_RELATIVE.as_posix(),
        acknowledgement_writer_symbol=(
            "torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_"
            "issuance_implementation.persist_final_execution_acknowledgement"
        ),
        acknowledgement_verifier_symbol=(
            "torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_"
            "issuance_implementation.verify_persisted_final_execution_acknowledgement"
        ),
    )


def _build_contract() -> FinalExecutionAcknowledgementMaterializationImplementationContract:
    return FinalExecutionAcknowledgementMaterializationImplementationContract(
        complete_authoring_identity_verified=True,
        prospective_materialization_required=True,
        exact_writer_delegate_required=True,
        writer_call_limit=1,
        exact_postwrite_reverification_required=True,
        verifier_call_limit=1,
        writer_result_equality_required=True,
        direct_filesystem_write_forbidden=True,
        subprocess_forbidden=True,
        docker_forbidden=True,
        image_inspection_forbidden=True,
        command_materialization_forbidden=True,
        lease_materialization_forbidden=True,
        durable_outcome_persistence_forbidden=True,
        authorization_consumption_forbidden=True,
        local_compute_forbidden=True,
        production_callsite_separate=True,
        repository_materializer_callsite_forbidden=True,
        automatic_retry_forbidden=True,
        test_writes_isolated_only=True,
    )


def _build_gates() -> FinalExecutionAcknowledgementMaterializationImplementationGates:
    return FinalExecutionAcknowledgementMaterializationImplementationGates(
        materialization_authoring_post_merge_verified=True,
        acknowledgement_materialization_contract_authored=True,
        acknowledgement_materialization_implemented=True,
        final_execution_acknowledgement_issued=False,
        final_execution_acknowledged=False,
        one_shot_engineering_invocation_permitted=False,
        execution_lease_materialized=False,
        durable_host_outcome_present=False,
        authorization_consumed=False,
        runtime_execution_started=False,
        runtime_execution_performed=False,
        image_inspection_performed=False,
        invocation_command_materialized=False,
        docker_run_performed=False,
        local_compute_execution_open=False,
    )


def build_frozen_acknowledgement_materialization_implementation_record(
    receipt: AcknowledgementMaterializationAuthoringMergeValidationReceipt,
) -> FinalExecutionAcknowledgementMaterializationImplementationRecord:
    """Build the exact frozen bounded materializer implementation record."""

    receipt.require()
    record = FinalExecutionAcknowledgementMaterializationImplementationRecord(
        schema_version=1,
        implementation_id=(
            FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_IMPLEMENTATION_ID
        ),
        status=FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_IMPLEMENTATION_STATUS,
        recorded_at_utc="2026-07-30T21:15:00Z",
        source=_build_source(receipt),
        contract=_build_contract(),
        gates=_build_gates(),
        next_slice=(
            "QW-LC4-E-final-execution-acknowledgement-"
            "materialization-implementation-commit"
        ),
        post_merge_next_slice=(
            "QW-LC4-E-final-execution-acknowledgement-"
            "materialization-invocation-authoring"
        ),
        implementation_sha256="sha256:" + "0" * 64,
    )
    result = replace(
        record,
        implementation_sha256=sha256_object(record.semantic_payload()),
    )
    result.require(receipt)
    return result


def build_materialization_authoring_merge_validation_receipt(
) -> AcknowledgementMaterializationAuthoringMergeValidationReceipt:
    """Build the exact PR #150 post-merge validation receipt."""

    receipt = AcknowledgementMaterializationAuthoringMergeValidationReceipt(
        receipt_id=(
            "stage3b-qwake-lc4-e-final-execution-acknowledgement-"
            "materialization-authoring-post-merge-validation-v1"
        ),
        pr_number=MATERIALIZATION_AUTHORING_PR_NUMBER,
        head_commit=MATERIALIZATION_AUTHORING_HEAD_COMMIT,
        base_commit=MATERIALIZATION_AUTHORING_PARENT_COMMIT,
        merge_commit=MATERIALIZATION_AUTHORING_MERGE_COMMIT,
        merged_at_utc=MATERIALIZATION_AUTHORING_MERGED_AT_UTC,
        commit_count=1,
        file_count=18,
        focused_tests_passed=92,
        targeted_tests_passed=293,
        full_tests_passed=1340,
        full_test_warnings=14,
        required_ci_checks_passed=True,
        production_execution_boundary_closed=True,
        receipt_sha256="sha256:" + "0" * 64,
    )
    result = replace(
        receipt,
        receipt_sha256=sha256_object(receipt.semantic_payload()),
    )
    result.require()
    return result
