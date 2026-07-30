"""Effect-free authoring for production acknowledgement materialization.

The module freezes the operator-bound request and provenance schema for one
future production acknowledgement materialization. It only builds and verifies
immutable in-memory records. Importing or verifying it never calls the
acknowledgement writer, creates the production acknowledgement, creates a lease
or outcome, inspects an image, materializes a command, spawns a process, invokes
Docker, consumes authorization, or executes local compute.
"""

from __future__ import annotations

import ast
import json
import re
from collections.abc import Mapping
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final, cast

from .stage3b_qwake_lc4_final_execution_acknowledgement_authoring import (
    DURABLE_HOST_OUTCOME_RELATIVE,
    EXECUTION_LEASE_V2_RELATIVE,
    FINAL_EXECUTION_OPERATOR_ACKNOWLEDGEMENT,
    FinalExecutionAcknowledgementAuthoring,
    FinalExecutionAcknowledgementAuthoringError,
    WiringMergeValidationReceipt,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_issuance_authoring import (
    ACKNOWLEDGEMENT_RELATIVE,
    AcknowledgementAuthoringMergeValidationReceipt,
    FinalExecutionAcknowledgementIssuanceAuthoring,
    FinalExecutionAcknowledgementIssuanceAuthoringError,
    ProspectiveFinalExecutionAcknowledgementIssuance,
    build_prospective_acknowledgement_issuance,
    canonical_json,
    sha256_bytes,
    sha256_object,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_issuance_implementation import (
    FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUANCE_IMPLEMENTATION_ID,
    IMPLEMENTATION_RECORD_RELATIVE,
    LEGACY_EXECUTION_LEASE_RELATIVE,
    AcknowledgementIssuanceImplementationError,
    AcknowledgementIssuanceImplementationRecord,
    verify_final_execution_acknowledgement_issuance_implementation,
)

FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_AUTHORING_ID: Final = (
    "stage3b-qwake-lc4-e-final-execution-acknowledgement-"
    "materialization-authoring-v1"
)
FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_AUTHORING_STATUS: Final = (
    "operator_bound_materialization_contract_authored_not_materialized_"
    "execution_closed"
)
FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_ID: Final = (
    "stage3b-qwake-lc4-e-final-execution-acknowledgement-materialization-v1"
)
FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_STATUS: Final = (
    "prospective_acknowledgement_materialization_not_written"
)

MATERIALIZATION_AUTHORING_BASE_COMMIT: Final = (
    "31206012ef7cbd2b7b21a2017374c11123abd42c"
)
ISSUANCE_IMPLEMENTATION_PR_NUMBER: Final = 149
ISSUANCE_IMPLEMENTATION_HEAD_COMMIT: Final = (
    "855276445432bceadb852d60e5dfdeaa633de96c"
)
ISSUANCE_IMPLEMENTATION_PARENT_COMMIT: Final = (
    "8343724c66b1d22f01846d9fc70f01738a09127a"
)
ISSUANCE_IMPLEMENTATION_MERGE_COMMIT: Final = MATERIALIZATION_AUTHORING_BASE_COMMIT
ISSUANCE_IMPLEMENTATION_MERGED_AT_UTC: Final = "2026-07-30T19:19:46Z"

ISSUANCE_IMPLEMENTATION_SHA256: Final = (
    "sha256:3e4bf0a15f10e3a37858372c21c011e08b75b924e898635448616a1de881001a"
)
ISSUANCE_IMPLEMENTATION_FILE_SHA256: Final = (
    "sha256:1abf3ee117d03d44f4954234493757d4ce2868180a4591275e42336871b6b544"
)
ISSUANCE_IMPLEMENTATION_PACKAGE_REGISTRY_SHA256: Final = (
    "sha256:fb5367b36ed35f8bde899a3ceb37f38ad96b80c3b9860f9e360e0421d9729775"
)
ISSUANCE_IMPLEMENTATION_SOURCE_REGISTRY_SHA256: Final = (
    "sha256:1f9659f53464ce960228f951c50ed791bd717f2668def3b7da9a1e69fac04a04"
)
ISSUANCE_IMPLEMENTATION_MODULE_SHA256: Final = (
    "sha256:6397bdef1d5510808e68bbd41017323ef7a4287d7a6f1a9fa3e9ff0c96e0baf3"
)
ISSUANCE_IMPLEMENTATION_VERIFIER_SHA256: Final = (
    "sha256:b07457d6295daafb01e3ec89877a0c410ef792270db6dc41f7ded53c94e29332"
)
ISSUANCE_IMPLEMENTATION_TEST_SHA256: Final = (
    "sha256:42dba269abc9bbe40a10b678e7d159761dca7ab617da1034f8b265afed2b20e3"
)
ISSUANCE_IMPLEMENTATION_ADR_RU_SHA256: Final = (
    "sha256:72db18c154b46420402edef478e7108e4286161e0883079d4ebc4ec35b61b525"
)
ISSUANCE_IMPLEMENTATION_ADR_EN_SHA256: Final = (
    "sha256:048ec09ec01c1e7bd721fde31fb0be40c3649a2b9548f4413ea65433dab76d0f"
)

ACKNOWLEDGEMENT_WRITER_SYMBOL: Final = (
    "torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_"
    "issuance_implementation.persist_final_execution_acknowledgement"
)
ACKNOWLEDGEMENT_FILE_MODE: Final = "0600"

PACKAGE_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-final-execution-acknowledgement-"
    "materialization-authoring-v1"
)
AUTHORING_RECORD_RELATIVE: Final = PACKAGE_RELATIVE / "authoring.json"
IMPLEMENTATION_MERGE_RECEIPT_RELATIVE: Final = (
    PACKAGE_RELATIVE / "implementation-merge-validation.json"
)
REGISTRY_RELATIVE: Final = PACKAGE_RELATIVE / "SHA256SUMS"
SOURCE_REGISTRY_RELATIVE: Final = PACKAGE_RELATIVE / "source-SHA256SUMS"

IMPLEMENTATION_PACKAGE_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-final-execution-acknowledgement-"
    "issuance-implementation-v1"
)
IMPLEMENTATION_MERGE_RECEIPT_UPSTREAM_RELATIVE: Final = (
    IMPLEMENTATION_PACKAGE_RELATIVE / "authoring-merge-validation.json"
)
IMPLEMENTATION_REGISTRY_RELATIVE: Final = IMPLEMENTATION_PACKAGE_RELATIVE / "SHA256SUMS"
IMPLEMENTATION_SOURCE_REGISTRY_RELATIVE: Final = (
    IMPLEMENTATION_PACKAGE_RELATIVE / "source-SHA256SUMS"
)
IMPLEMENTATION_MODULE_RELATIVE: Final = Path(
    "src/torch2pc_thesis/"
    "stage3b_qwake_lc4_final_execution_acknowledgement_issuance_implementation.py"
)
IMPLEMENTATION_VERIFIER_RELATIVE: Final = Path(
    "scripts/verify_stage3b_qwake_lc4_"
    "final_execution_acknowledgement_issuance_implementation.py"
)
IMPLEMENTATION_TEST_RELATIVE: Final = Path(
    "tests/unit/test_stage3b_qwake_lc4_"
    "final_execution_acknowledgement_issuance_implementation.py"
)
IMPLEMENTATION_ADR_RU_RELATIVE: Final = Path(
    "docs/decisions/ADR-088-stage3b-qwake-lc4-e-"
    "final-execution-acknowledgement-issuance-implementation.md"
)
IMPLEMENTATION_ADR_EN_RELATIVE: Final = Path(
    "docs/decisions/ADR-088-stage3b-qwake-lc4-e-"
    "final-execution-acknowledgement-issuance-implementation_EN.md"
)
MODULE_RELATIVE: Final = Path(
    "src/torch2pc_thesis/"
    "stage3b_qwake_lc4_final_execution_acknowledgement_"
    "materialization_authoring.py"
)
VERIFIER_RELATIVE: Final = Path(
    "scripts/verify_stage3b_qwake_lc4_"
    "final_execution_acknowledgement_materialization_authoring.py"
)
TEST_RELATIVE: Final = Path(
    "tests/unit/test_stage3b_qwake_lc4_"
    "final_execution_acknowledgement_materialization_authoring.py"
)
ADR_RU_RELATIVE: Final = Path(
    "docs/decisions/ADR-089-stage3b-qwake-lc4-e-"
    "final-execution-acknowledgement-materialization-authoring.md"
)
ADR_EN_RELATIVE: Final = Path(
    "docs/decisions/ADR-089-stage3b-qwake-lc4-e-"
    "final-execution-acknowledgement-materialization-authoring_EN.md"
)

_EXPECTED_PACKAGE_FILES: Final = frozenset(
    {
        "SHA256SUMS",
        "authoring.json",
        "implementation-merge-validation.json",
        "source-SHA256SUMS",
    }
)
_EXPECTED_SOURCE_PATHS: Final = frozenset(
    {
        IMPLEMENTATION_RECORD_RELATIVE.as_posix(),
        IMPLEMENTATION_MERGE_RECEIPT_UPSTREAM_RELATIVE.as_posix(),
        IMPLEMENTATION_REGISTRY_RELATIVE.as_posix(),
        IMPLEMENTATION_SOURCE_REGISTRY_RELATIVE.as_posix(),
        IMPLEMENTATION_MODULE_RELATIVE.as_posix(),
        IMPLEMENTATION_VERIFIER_RELATIVE.as_posix(),
        IMPLEMENTATION_TEST_RELATIVE.as_posix(),
        IMPLEMENTATION_ADR_RU_RELATIVE.as_posix(),
        IMPLEMENTATION_ADR_EN_RELATIVE.as_posix(),
        MODULE_RELATIVE.as_posix(),
        VERIFIER_RELATIVE.as_posix(),
        TEST_RELATIVE.as_posix(),
        ADR_RU_RELATIVE.as_posix(),
        ADR_EN_RELATIVE.as_posix(),
    }
)
_SHA256_PATTERN: Final = re.compile(r"^sha256:[0-9a-f]{64}$")
_COMMIT_PATTERN: Final = re.compile(r"^[0-9a-f]{40}$")
_IDENTITY_PATTERN: Final = re.compile(r"^[^\r\n]{1,256}$")
_FORBIDDEN_IMPORT_ROOTS: Final = frozenset({"docker", "subprocess"})
_FORBIDDEN_CALL_NAMES: Final = frozenset(
    {
        "inspect_local_image",
        "invoke_lease_bound_host_runtime",
        "invoke_one_shot_host_runtime",
        "materialize_invocation_command",
        "persist_durable_host_outcome_receipt",
        "persist_final_execution_acknowledgement",
        "persist_persistent_execution_lease_v2",
    }
)
_FORBIDDEN_CALL_ATTRIBUTES: Final = frozenset(
    {
        "Popen",
        "hardlink_to",
        "mkdir",
        "rename",
        "replace",
        "run",
        "symlink_to",
        "touch",
        "unlink",
        "write_bytes",
        "write_text",
    }
)

__all__ = [
    "ACKNOWLEDGEMENT_WRITER_SYMBOL",
    "FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_AUTHORING_ID",
    "AcknowledgementIssuanceImplementationMergeValidationReceipt",
    "FinalExecutionAcknowledgementMaterializationAuthoring",
    "FinalExecutionAcknowledgementMaterializationAuthoringError",
    "FinalExecutionAcknowledgementMaterializationContract",
    "FinalExecutionAcknowledgementMaterializationGates",
    "FinalExecutionAcknowledgementMaterializationSource",
    "ProspectiveFinalExecutionAcknowledgementMaterialization",
    "build_acknowledgement_issuance_implementation_merge_validation_receipt",
    "build_frozen_materialization_authoring_record",
    "build_prospective_acknowledgement_materialization",
    "load_acknowledgement_issuance_implementation_merge_validation_receipt",
    "load_final_execution_acknowledgement_materialization_authoring",
    "verify_final_execution_acknowledgement_materialization_authoring",
]


class FinalExecutionAcknowledgementMaterializationAuthoringError(RuntimeError):
    """Raised when materialization authoring fails closed."""


def _require_sha256(value: str, field_name: str) -> None:
    if not _SHA256_PATTERN.fullmatch(value):
        raise FinalExecutionAcknowledgementMaterializationAuthoringError(
            f"{field_name} is not a canonical SHA-256 identity"
        )


def _require_commit(value: str, field_name: str) -> None:
    if not _COMMIT_PATTERN.fullmatch(value):
        raise FinalExecutionAcknowledgementMaterializationAuthoringError(
            f"{field_name} is not a commit identity"
        )


def _require_identity(value: str, field_name: str) -> None:
    if not _IDENTITY_PATTERN.fullmatch(value):
        raise FinalExecutionAcknowledgementMaterializationAuthoringError(
            f"{field_name} is empty or non-canonical"
        )


def _require_utc(value: str, field_name: str) -> datetime:
    if not value.endswith("Z"):
        raise FinalExecutionAcknowledgementMaterializationAuthoringError(
            f"{field_name} is not a UTC timestamp"
        )
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise FinalExecutionAcknowledgementMaterializationAuthoringError(
            f"{field_name} is not an ISO-8601 timestamp"
        ) from exc
    if parsed.tzinfo != UTC:
        raise FinalExecutionAcknowledgementMaterializationAuthoringError(
            f"{field_name} is not normalized to UTC"
        )
    return parsed


@dataclass(frozen=True)
class AcknowledgementIssuanceImplementationMergeValidationReceipt:
    """Exact post-merge receipt for acknowledgement implementation PR #149."""

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
    ) -> AcknowledgementIssuanceImplementationMergeValidationReceipt:
        return cls(**cast(dict[str, Any], dict(value)))

    def semantic_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload.pop("receipt_sha256")
        return cast(dict[str, object], payload)

    def require(self) -> None:
        expected: dict[str, object] = {
            "receipt_id": (
                "stage3b-qwake-lc4-e-final-execution-acknowledgement-"
                "issuance-implementation-post-merge-validation-v1"
            ),
            "pr_number": ISSUANCE_IMPLEMENTATION_PR_NUMBER,
            "head_commit": ISSUANCE_IMPLEMENTATION_HEAD_COMMIT,
            "base_commit": ISSUANCE_IMPLEMENTATION_PARENT_COMMIT,
            "merge_commit": ISSUANCE_IMPLEMENTATION_MERGE_COMMIT,
            "merged_at_utc": ISSUANCE_IMPLEMENTATION_MERGED_AT_UTC,
            "commit_count": 1,
            "file_count": 18,
            "focused_tests_passed": 79,
            "targeted_tests_passed": 280,
            "full_tests_passed": 1327,
            "full_test_warnings": 14,
            "required_ci_checks_passed": True,
            "production_execution_boundary_closed": True,
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise FinalExecutionAcknowledgementMaterializationAuthoringError(
                    f"implementation merge receipt differs: {field_name}"
                )
        _require_commit(self.head_commit, "head_commit")
        _require_commit(self.base_commit, "base_commit")
        _require_commit(self.merge_commit, "merge_commit")
        _require_utc(self.merged_at_utc, "merged_at_utc")
        _require_sha256(self.receipt_sha256, "receipt_sha256")
        if self.receipt_sha256 != sha256_object(self.semantic_payload()):
            raise FinalExecutionAcknowledgementMaterializationAuthoringError(
                "implementation merge receipt semantic SHA-256 differs"
            )

    def canonical_json(self) -> str:
        self.require()
        return canonical_json(self)


@dataclass(frozen=True)
class FinalExecutionAcknowledgementMaterializationSource:
    """Exact merged implementation identity bound by materialization."""

    materialization_authoring_base_commit: str
    issuance_implementation_pr_number: int
    issuance_implementation_head_commit: str
    issuance_implementation_parent_commit: str
    issuance_implementation_merge_commit: str
    issuance_implementation_merged_at_utc: str
    issuance_implementation_merge_receipt_sha256: str
    issuance_implementation_id: str
    issuance_implementation_sha256: str
    issuance_implementation_file_sha256: str
    issuance_implementation_package_registry_sha256: str
    issuance_implementation_source_registry_sha256: str
    issuance_implementation_module_sha256: str
    issuance_implementation_verifier_sha256: str
    issuance_implementation_test_sha256: str
    issuance_implementation_adr_ru_sha256: str
    issuance_implementation_adr_en_sha256: str
    acknowledgement_relative: str
    legacy_execution_lease_relative: str
    execution_lease_v2_relative: str
    durable_host_outcome_relative: str
    acknowledgement_writer_symbol: str

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, object],
    ) -> FinalExecutionAcknowledgementMaterializationSource:
        return cls(**cast(dict[str, Any], dict(value)))

    def require(
        self,
        receipt: AcknowledgementIssuanceImplementationMergeValidationReceipt,
    ) -> None:
        expected: dict[str, object] = {
            "materialization_authoring_base_commit": (
                MATERIALIZATION_AUTHORING_BASE_COMMIT
            ),
            "issuance_implementation_pr_number": (
                ISSUANCE_IMPLEMENTATION_PR_NUMBER
            ),
            "issuance_implementation_head_commit": (
                ISSUANCE_IMPLEMENTATION_HEAD_COMMIT
            ),
            "issuance_implementation_parent_commit": (
                ISSUANCE_IMPLEMENTATION_PARENT_COMMIT
            ),
            "issuance_implementation_merge_commit": (
                ISSUANCE_IMPLEMENTATION_MERGE_COMMIT
            ),
            "issuance_implementation_merged_at_utc": (
                ISSUANCE_IMPLEMENTATION_MERGED_AT_UTC
            ),
            "issuance_implementation_merge_receipt_sha256": (
                receipt.receipt_sha256
            ),
            "issuance_implementation_id": (
                FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUANCE_IMPLEMENTATION_ID
            ),
            "issuance_implementation_sha256": ISSUANCE_IMPLEMENTATION_SHA256,
            "issuance_implementation_file_sha256": (
                ISSUANCE_IMPLEMENTATION_FILE_SHA256
            ),
            "issuance_implementation_package_registry_sha256": (
                ISSUANCE_IMPLEMENTATION_PACKAGE_REGISTRY_SHA256
            ),
            "issuance_implementation_source_registry_sha256": (
                ISSUANCE_IMPLEMENTATION_SOURCE_REGISTRY_SHA256
            ),
            "issuance_implementation_module_sha256": (
                ISSUANCE_IMPLEMENTATION_MODULE_SHA256
            ),
            "issuance_implementation_verifier_sha256": (
                ISSUANCE_IMPLEMENTATION_VERIFIER_SHA256
            ),
            "issuance_implementation_test_sha256": (
                ISSUANCE_IMPLEMENTATION_TEST_SHA256
            ),
            "issuance_implementation_adr_ru_sha256": (
                ISSUANCE_IMPLEMENTATION_ADR_RU_SHA256
            ),
            "issuance_implementation_adr_en_sha256": (
                ISSUANCE_IMPLEMENTATION_ADR_EN_SHA256
            ),
            "acknowledgement_relative": ACKNOWLEDGEMENT_RELATIVE.as_posix(),
            "legacy_execution_lease_relative": (
                LEGACY_EXECUTION_LEASE_RELATIVE.as_posix()
            ),
            "execution_lease_v2_relative": EXECUTION_LEASE_V2_RELATIVE.as_posix(),
            "durable_host_outcome_relative": DURABLE_HOST_OUTCOME_RELATIVE.as_posix(),
            "acknowledgement_writer_symbol": ACKNOWLEDGEMENT_WRITER_SYMBOL,
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise FinalExecutionAcknowledgementMaterializationAuthoringError(
                    f"materialization source differs: {field_name}"
                )
        for field_name in (
            "materialization_authoring_base_commit",
            "issuance_implementation_head_commit",
            "issuance_implementation_parent_commit",
            "issuance_implementation_merge_commit",
        ):
            _require_commit(cast(str, getattr(self, field_name)), field_name)
        for field_name in (
            "issuance_implementation_merge_receipt_sha256",
            "issuance_implementation_sha256",
            "issuance_implementation_file_sha256",
            "issuance_implementation_package_registry_sha256",
            "issuance_implementation_source_registry_sha256",
            "issuance_implementation_module_sha256",
            "issuance_implementation_verifier_sha256",
            "issuance_implementation_test_sha256",
            "issuance_implementation_adr_ru_sha256",
            "issuance_implementation_adr_en_sha256",
        ):
            _require_sha256(cast(str, getattr(self, field_name)), field_name)
        _require_utc(
            self.issuance_implementation_merged_at_utc,
            "issuance_implementation_merged_at_utc",
        )


@dataclass(frozen=True)
class FinalExecutionAcknowledgementMaterializationContract:
    """Operator-bound rules for one future acknowledgement write."""

    implementation_post_merge_verification_required: bool
    complete_implementation_identity_required: bool
    exact_operator_phrase_required: str
    explicit_operator_identity_required: bool
    explicit_issuer_identity_required: bool
    explicit_materializer_identity_required: bool
    materializer_must_equal_issuer: bool
    explicit_acknowledged_at_utc_required: bool
    explicit_issued_at_utc_required: bool
    explicit_materialized_at_utc_required: bool
    acknowledgement_after_implementation_merge_required: bool
    issued_at_not_before_acknowledged_at_required: bool
    materialized_at_not_before_issued_at_required: bool
    materialized_after_implementation_merge_required: bool
    canonical_issuance_envelope_required: bool
    exact_acknowledgement_path_required: bool
    exact_acknowledgement_sha256_required: bool
    exact_writer_symbol_required: str
    acknowledgement_target_absent_required: bool
    target_parent_must_preexist: bool
    symbolic_parent_forbidden: bool
    exclusive_atomic_no_overwrite_required: bool
    file_mode_required: str
    file_fsync_required: bool
    parent_directory_fsync_required: bool
    temporary_cleanup_required: bool
    exact_persisted_bytes_reverification_required: bool
    one_materialization_only: bool
    retry_forbidden: bool
    production_callsite_separate: bool
    lease_materialization_separate: bool
    materialization_does_not_permit_invocation: bool
    authoring_effects_forbidden: bool

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, object],
    ) -> FinalExecutionAcknowledgementMaterializationContract:
        return cls(**cast(dict[str, Any], dict(value)))

    def require(self) -> None:
        if self != _build_contract():
            raise FinalExecutionAcknowledgementMaterializationAuthoringError(
                "materialization contract differs"
            )


@dataclass(frozen=True)
class FinalExecutionAcknowledgementMaterializationGates:
    """Closed production state after materialization-contract authoring."""

    acknowledgement_issuance_implementation_post_merge_verified: bool
    acknowledgement_issuance_implemented: bool
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
    ) -> FinalExecutionAcknowledgementMaterializationGates:
        return cls(**cast(dict[str, Any], dict(value)))

    def require(self) -> None:
        if self != _build_gates():
            raise FinalExecutionAcknowledgementMaterializationAuthoringError(
                "materialization gates differ"
            )


@dataclass(frozen=True)
class FinalExecutionAcknowledgementMaterializationAuthoring:
    """Frozen authoring record; no production acknowledgement is written."""

    schema_version: int
    authoring_id: str
    status: str
    recorded_at_utc: str
    source: FinalExecutionAcknowledgementMaterializationSource
    contract: FinalExecutionAcknowledgementMaterializationContract
    gates: FinalExecutionAcknowledgementMaterializationGates
    next_slice: str
    post_merge_next_slice: str
    authoring_sha256: str

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, object],
    ) -> FinalExecutionAcknowledgementMaterializationAuthoring:
        payload = dict(value)
        payload["source"] = FinalExecutionAcknowledgementMaterializationSource.from_mapping(
            cast(Mapping[str, object], payload["source"])
        )
        payload["contract"] = (
            FinalExecutionAcknowledgementMaterializationContract.from_mapping(
                cast(Mapping[str, object], payload["contract"])
            )
        )
        payload["gates"] = FinalExecutionAcknowledgementMaterializationGates.from_mapping(
            cast(Mapping[str, object], payload["gates"])
        )
        return cls(**cast(dict[str, Any], payload))

    def semantic_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload.pop("authoring_sha256")
        return cast(dict[str, object], payload)

    def require(
        self,
        receipt: AcknowledgementIssuanceImplementationMergeValidationReceipt,
    ) -> None:
        if self.schema_version != 1:
            raise FinalExecutionAcknowledgementMaterializationAuthoringError(
                "materialization authoring schema differs"
            )
        if self.authoring_id != FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_AUTHORING_ID:
            raise FinalExecutionAcknowledgementMaterializationAuthoringError(
                "materialization authoring ID differs"
            )
        if self.status != FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_AUTHORING_STATUS:
            raise FinalExecutionAcknowledgementMaterializationAuthoringError(
                "materialization authoring status differs"
            )
        _require_utc(self.recorded_at_utc, "recorded_at_utc")
        if self.next_slice != (
            "QW-LC4-E-final-execution-acknowledgement-"
            "materialization-authoring-commit"
        ):
            raise FinalExecutionAcknowledgementMaterializationAuthoringError(
                "next slice differs"
            )
        if self.post_merge_next_slice != (
            "QW-LC4-E-final-execution-acknowledgement-materialization"
        ):
            raise FinalExecutionAcknowledgementMaterializationAuthoringError(
                "post-merge next slice differs"
            )
        self.source.require(receipt)
        self.contract.require()
        self.gates.require()
        _require_sha256(self.authoring_sha256, "authoring_sha256")
        if self.authoring_sha256 != sha256_object(self.semantic_payload()):
            raise FinalExecutionAcknowledgementMaterializationAuthoringError(
                "materialization authoring semantic SHA-256 differs"
            )

    def canonical_json(
        self,
        receipt: AcknowledgementIssuanceImplementationMergeValidationReceipt,
    ) -> str:
        self.require(receipt)
        return canonical_json(self)


@dataclass(frozen=True)
class ProspectiveFinalExecutionAcknowledgementMaterialization:
    """Pure operator-bound materialization request; it is not executed here."""

    materialization_id: str
    status: str
    materialization_authoring_sha256: str
    issuance: ProspectiveFinalExecutionAcknowledgementIssuance
    acknowledgement_sha256: str
    materializer_identity: str
    materialized_at_utc: str
    acknowledgement_relative: str
    acknowledgement_writer_symbol: str
    file_mode: str
    exact_persisted_bytes_required: bool
    retry_permitted: bool
    acknowledgement_materialized: bool
    execution_lease_materialized: bool
    authorization_consumed: bool
    one_shot_engineering_invocation_permitted: bool

    def require(
        self,
        authoring: FinalExecutionAcknowledgementMaterializationAuthoring,
        receipt: AcknowledgementIssuanceImplementationMergeValidationReceipt,
        issuance_authoring: FinalExecutionAcknowledgementIssuanceAuthoring,
        issuance_receipt: AcknowledgementAuthoringMergeValidationReceipt,
        upstream_authoring: FinalExecutionAcknowledgementAuthoring,
        upstream_receipt: WiringMergeValidationReceipt,
    ) -> None:
        authoring.require(receipt)
        self.issuance.require(
            issuance_authoring,
            issuance_receipt,
            upstream_authoring,
            upstream_receipt,
        )
        expected: dict[str, object] = {
            "materialization_id": FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_ID,
            "status": FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_STATUS,
            "materialization_authoring_sha256": authoring.authoring_sha256,
            "acknowledgement_sha256": sha256_object(self.issuance.acknowledgement),
            "acknowledgement_relative": ACKNOWLEDGEMENT_RELATIVE.as_posix(),
            "acknowledgement_writer_symbol": ACKNOWLEDGEMENT_WRITER_SYMBOL,
            "file_mode": ACKNOWLEDGEMENT_FILE_MODE,
            "exact_persisted_bytes_required": True,
            "retry_permitted": False,
            "acknowledgement_materialized": False,
            "execution_lease_materialized": False,
            "authorization_consumed": False,
            "one_shot_engineering_invocation_permitted": False,
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise FinalExecutionAcknowledgementMaterializationAuthoringError(
                    f"prospective materialization differs: {field_name}"
                )
        _require_identity(self.materializer_identity, "materializer_identity")
        if self.materializer_identity != self.issuance.issuer_identity:
            raise FinalExecutionAcknowledgementMaterializationAuthoringError(
                "materializer identity differs from issuer identity"
            )
        acknowledged = _require_utc(
            self.issuance.acknowledgement.acknowledged_at_utc,
            "acknowledged_at_utc",
        )
        issued = _require_utc(self.issuance.issued_at_utc, "issued_at_utc")
        materialized = _require_utc(
            self.materialized_at_utc,
            "materialized_at_utc",
        )
        merged = _require_utc(
            receipt.merged_at_utc,
            "issuance_implementation_merged_at_utc",
        )
        if acknowledged <= merged:
            raise FinalExecutionAcknowledgementMaterializationAuthoringError(
                "acknowledgement timestamp is not after implementation merge"
            )
        if issued < acknowledged:
            raise FinalExecutionAcknowledgementMaterializationAuthoringError(
                "issuance timestamp is before acknowledgement"
            )
        if materialized < issued:
            raise FinalExecutionAcknowledgementMaterializationAuthoringError(
                "materialization timestamp is before issuance"
            )
        if materialized <= merged:
            raise FinalExecutionAcknowledgementMaterializationAuthoringError(
                "materialization timestamp is not after implementation merge"
            )

    def canonical_json(
        self,
        authoring: FinalExecutionAcknowledgementMaterializationAuthoring,
        receipt: AcknowledgementIssuanceImplementationMergeValidationReceipt,
        issuance_authoring: FinalExecutionAcknowledgementIssuanceAuthoring,
        issuance_receipt: AcknowledgementAuthoringMergeValidationReceipt,
        upstream_authoring: FinalExecutionAcknowledgementAuthoring,
        upstream_receipt: WiringMergeValidationReceipt,
    ) -> str:
        self.require(
            authoring,
            receipt,
            issuance_authoring,
            issuance_receipt,
            upstream_authoring,
            upstream_receipt,
        )
        return canonical_json(self)


def build_prospective_acknowledgement_materialization(
    authoring: FinalExecutionAcknowledgementMaterializationAuthoring,
    receipt: AcknowledgementIssuanceImplementationMergeValidationReceipt,
    issuance_authoring: FinalExecutionAcknowledgementIssuanceAuthoring,
    issuance_receipt: AcknowledgementAuthoringMergeValidationReceipt,
    upstream_authoring: FinalExecutionAcknowledgementAuthoring,
    upstream_receipt: WiringMergeValidationReceipt,
    *,
    acknowledgement_phrase: str,
    operator_identity: str,
    acknowledged_at_utc: str,
    issuer_identity: str,
    issued_at_utc: str,
    materializer_identity: str,
    materialized_at_utc: str,
) -> ProspectiveFinalExecutionAcknowledgementMaterialization:
    """Build a future materialization request without writing any file."""

    authoring.require(receipt)
    try:
        issuance = build_prospective_acknowledgement_issuance(
            issuance_authoring,
            issuance_receipt,
            upstream_authoring,
            upstream_receipt,
            acknowledgement_phrase=acknowledgement_phrase,
            operator_identity=operator_identity,
            acknowledged_at_utc=acknowledged_at_utc,
            issuer_identity=issuer_identity,
            issued_at_utc=issued_at_utc,
        )
    except (
        FinalExecutionAcknowledgementAuthoringError,
        FinalExecutionAcknowledgementIssuanceAuthoringError,
    ) as exc:
        raise FinalExecutionAcknowledgementMaterializationAuthoringError(
            str(exc)
        ) from exc
    result = ProspectiveFinalExecutionAcknowledgementMaterialization(
        materialization_id=FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_ID,
        status=FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_STATUS,
        materialization_authoring_sha256=authoring.authoring_sha256,
        issuance=issuance,
        acknowledgement_sha256=sha256_object(issuance.acknowledgement),
        materializer_identity=materializer_identity,
        materialized_at_utc=materialized_at_utc,
        acknowledgement_relative=ACKNOWLEDGEMENT_RELATIVE.as_posix(),
        acknowledgement_writer_symbol=ACKNOWLEDGEMENT_WRITER_SYMBOL,
        file_mode=ACKNOWLEDGEMENT_FILE_MODE,
        exact_persisted_bytes_required=True,
        retry_permitted=False,
        acknowledgement_materialized=False,
        execution_lease_materialized=False,
        authorization_consumed=False,
        one_shot_engineering_invocation_permitted=False,
    )
    result.require(
        authoring,
        receipt,
        issuance_authoring,
        issuance_receipt,
        upstream_authoring,
        upstream_receipt,
    )
    return result


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8", errors="strict"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FinalExecutionAcknowledgementMaterializationAuthoringError(
            f"JSON record is unreadable: {path}"
        ) from exc
    if not isinstance(payload, dict):
        raise FinalExecutionAcknowledgementMaterializationAuthoringError(
            f"JSON record is not an object: {path}"
        )
    return cast(dict[str, Any], payload)


def _load_registry(path: Path) -> dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8", errors="strict").splitlines()
    except (OSError, UnicodeError) as exc:
        raise FinalExecutionAcknowledgementMaterializationAuthoringError(
            f"registry is unreadable: {path}"
        ) from exc
    result: dict[str, str] = {}
    for line in lines:
        if "  " not in line:
            raise FinalExecutionAcknowledgementMaterializationAuthoringError(
                f"registry line is invalid: {path}"
            )
        digest, relative = line.split("  ", 1)
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise FinalExecutionAcknowledgementMaterializationAuthoringError(
                f"registry digest is invalid: {path}"
            )
        if not relative or relative in result:
            raise FinalExecutionAcknowledgementMaterializationAuthoringError(
                f"registry path is invalid or duplicated: {path}"
            )
        result[relative] = digest
    return result


def load_acknowledgement_issuance_implementation_merge_validation_receipt(
    path: Path,
) -> AcknowledgementIssuanceImplementationMergeValidationReceipt:
    receipt = AcknowledgementIssuanceImplementationMergeValidationReceipt.from_mapping(
        _load_json(path)
    )
    receipt.require()
    return receipt


def load_final_execution_acknowledgement_materialization_authoring(
    path: Path,
    receipt: AcknowledgementIssuanceImplementationMergeValidationReceipt,
) -> FinalExecutionAcknowledgementMaterializationAuthoring:
    authoring = FinalExecutionAcknowledgementMaterializationAuthoring.from_mapping(
        _load_json(path)
    )
    authoring.require(receipt)
    return authoring


def verify_final_execution_acknowledgement_materialization_authoring(
    project_root: Path,
) -> FinalExecutionAcknowledgementMaterializationAuthoring:
    """Verify the frozen materialization authoring package without effects."""

    root = _verified_project_root(project_root)
    package = root / PACKAGE_RELATIVE
    if not package.is_dir() or package.is_symlink():
        raise FinalExecutionAcknowledgementMaterializationAuthoringError(
            "materialization authoring package is absent or invalid"
        )
    if {path.name for path in package.iterdir()} != _EXPECTED_PACKAGE_FILES:
        raise FinalExecutionAcknowledgementMaterializationAuthoringError(
            "materialization authoring package file set differs"
        )
    _verify_registry(root / REGISTRY_RELATIVE, package)
    source_registry = _verify_registry(root / SOURCE_REGISTRY_RELATIVE, root)
    if frozenset(source_registry) != _EXPECTED_SOURCE_PATHS:
        raise FinalExecutionAcknowledgementMaterializationAuthoringError(
            "materialization source registry path set differs"
        )
    receipt = load_acknowledgement_issuance_implementation_merge_validation_receipt(
        root / IMPLEMENTATION_MERGE_RECEIPT_RELATIVE
    )
    authoring = load_final_execution_acknowledgement_materialization_authoring(
        root / AUTHORING_RECORD_RELATIVE,
        receipt,
    )
    try:
        implementation = (
            verify_final_execution_acknowledgement_issuance_implementation(root)
        )
    except AcknowledgementIssuanceImplementationError as exc:
        raise FinalExecutionAcknowledgementMaterializationAuthoringError(
            str(exc)
        ) from exc
    _verify_implementation_record(implementation)
    _verify_effect_free_authoring_ast(root)
    _require_repository_writer_callsite_absent(root)
    _require_production_boundary_closed(root)
    authoring.require(receipt)
    return authoring


def _verified_project_root(project_root: Path) -> Path:
    expanded = project_root.expanduser()
    if expanded.is_symlink():
        raise FinalExecutionAcknowledgementMaterializationAuthoringError(
            "project root is symbolic"
        )
    root = expanded.resolve()
    if not root.is_dir():
        raise FinalExecutionAcknowledgementMaterializationAuthoringError(
            "project root is absent or non-directory"
        )
    return root


def _verify_registry(path: Path, base: Path) -> dict[str, str]:
    registry = _load_registry(path)
    for relative, expected in registry.items():
        target = base / relative
        if not target.is_file() or target.is_symlink():
            raise FinalExecutionAcknowledgementMaterializationAuthoringError(
                f"registry target is absent or invalid: {relative}"
            )
        observed = sha256_bytes(target.read_bytes()).removeprefix("sha256:")
        if observed != expected:
            raise FinalExecutionAcknowledgementMaterializationAuthoringError(
                f"registry target identity differs: {relative}"
            )
    return registry


def _verify_implementation_record(
    implementation: AcknowledgementIssuanceImplementationRecord,
) -> None:
    if implementation.implementation_id != (
        FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUANCE_IMPLEMENTATION_ID
    ):
        raise FinalExecutionAcknowledgementMaterializationAuthoringError(
            "issuance implementation ID differs"
        )
    if implementation.implementation_sha256 != ISSUANCE_IMPLEMENTATION_SHA256:
        raise FinalExecutionAcknowledgementMaterializationAuthoringError(
            "issuance implementation semantic identity differs"
        )


def _verify_effect_free_authoring_ast(root: Path) -> None:
    paths = (root / MODULE_RELATIVE, root / VERIFIER_RELATIVE)
    for path in paths:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="strict"))
        except (OSError, UnicodeError, SyntaxError) as exc:
            raise FinalExecutionAcknowledgementMaterializationAuthoringError(
                f"materialization authoring source is invalid: {path}"
            ) from exc
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots = {alias.name.split(".", 1)[0] for alias in node.names}
                if roots & _FORBIDDEN_IMPORT_ROOTS:
                    raise FinalExecutionAcknowledgementMaterializationAuthoringError(
                        f"forbidden authoring import: {path}"
                    )
            if (
                isinstance(node, ast.ImportFrom)
                and node.module
                and node.module.split(".", 1)[0] in _FORBIDDEN_IMPORT_ROOTS
            ):
                raise FinalExecutionAcknowledgementMaterializationAuthoringError(
                    f"forbidden authoring import: {path}"
                )
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Name) and node.func.id in _FORBIDDEN_CALL_NAMES:
                raise FinalExecutionAcknowledgementMaterializationAuthoringError(
                    f"forbidden authoring call: {path}"
                )
            if (
                isinstance(node.func, ast.Attribute)
                and node.func.attr in _FORBIDDEN_CALL_ATTRIBUTES
            ):
                raise FinalExecutionAcknowledgementMaterializationAuthoringError(
                    f"forbidden authoring call: {path}"
                )


def _require_repository_writer_callsite_absent(root: Path) -> None:
    for path in sorted((root / "src").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8", errors="strict"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if (
                isinstance(node.func, ast.Name)
                and node.func.id == "persist_final_execution_acknowledgement"
            ):
                raise FinalExecutionAcknowledgementMaterializationAuthoringError(
                    f"production acknowledgement writer callsite exists: {path}"
                )
            if (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "persist_final_execution_acknowledgement"
            ):
                raise FinalExecutionAcknowledgementMaterializationAuthoringError(
                    f"production acknowledgement writer callsite exists: {path}"
                )


def _require_production_boundary_closed(root: Path) -> None:
    targets = (
        root / ACKNOWLEDGEMENT_RELATIVE,
        root / LEGACY_EXECUTION_LEASE_RELATIVE,
        root / EXECUTION_LEASE_V2_RELATIVE,
        root / DURABLE_HOST_OUTCOME_RELATIVE,
        root / Path(ACKNOWLEDGEMENT_RELATIVE.as_posix().removesuffix(
            ".final-execution-acknowledgement.json"
        )),
    )
    for target in targets:
        if target.exists() or target.is_symlink():
            raise FinalExecutionAcknowledgementMaterializationAuthoringError(
                f"production boundary is not closed: {target}"
            )
    parent = root / ACKNOWLEDGEMENT_RELATIVE.parent
    prefix = f".{ACKNOWLEDGEMENT_RELATIVE.name}.tmp-"
    if parent.is_dir() and any(path.name.startswith(prefix) for path in parent.iterdir()):
        raise FinalExecutionAcknowledgementMaterializationAuthoringError(
            "acknowledgement temporary artifact exists"
        )


def _build_source(
    receipt: AcknowledgementIssuanceImplementationMergeValidationReceipt,
) -> FinalExecutionAcknowledgementMaterializationSource:
    return FinalExecutionAcknowledgementMaterializationSource(
        materialization_authoring_base_commit=MATERIALIZATION_AUTHORING_BASE_COMMIT,
        issuance_implementation_pr_number=ISSUANCE_IMPLEMENTATION_PR_NUMBER,
        issuance_implementation_head_commit=ISSUANCE_IMPLEMENTATION_HEAD_COMMIT,
        issuance_implementation_parent_commit=ISSUANCE_IMPLEMENTATION_PARENT_COMMIT,
        issuance_implementation_merge_commit=ISSUANCE_IMPLEMENTATION_MERGE_COMMIT,
        issuance_implementation_merged_at_utc=ISSUANCE_IMPLEMENTATION_MERGED_AT_UTC,
        issuance_implementation_merge_receipt_sha256=receipt.receipt_sha256,
        issuance_implementation_id=(
            FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUANCE_IMPLEMENTATION_ID
        ),
        issuance_implementation_sha256=ISSUANCE_IMPLEMENTATION_SHA256,
        issuance_implementation_file_sha256=ISSUANCE_IMPLEMENTATION_FILE_SHA256,
        issuance_implementation_package_registry_sha256=(
            ISSUANCE_IMPLEMENTATION_PACKAGE_REGISTRY_SHA256
        ),
        issuance_implementation_source_registry_sha256=(
            ISSUANCE_IMPLEMENTATION_SOURCE_REGISTRY_SHA256
        ),
        issuance_implementation_module_sha256=ISSUANCE_IMPLEMENTATION_MODULE_SHA256,
        issuance_implementation_verifier_sha256=(
            ISSUANCE_IMPLEMENTATION_VERIFIER_SHA256
        ),
        issuance_implementation_test_sha256=ISSUANCE_IMPLEMENTATION_TEST_SHA256,
        issuance_implementation_adr_ru_sha256=ISSUANCE_IMPLEMENTATION_ADR_RU_SHA256,
        issuance_implementation_adr_en_sha256=ISSUANCE_IMPLEMENTATION_ADR_EN_SHA256,
        acknowledgement_relative=ACKNOWLEDGEMENT_RELATIVE.as_posix(),
        legacy_execution_lease_relative=LEGACY_EXECUTION_LEASE_RELATIVE.as_posix(),
        execution_lease_v2_relative=EXECUTION_LEASE_V2_RELATIVE.as_posix(),
        durable_host_outcome_relative=DURABLE_HOST_OUTCOME_RELATIVE.as_posix(),
        acknowledgement_writer_symbol=ACKNOWLEDGEMENT_WRITER_SYMBOL,
    )


def _build_contract() -> FinalExecutionAcknowledgementMaterializationContract:
    return FinalExecutionAcknowledgementMaterializationContract(
        implementation_post_merge_verification_required=True,
        complete_implementation_identity_required=True,
        exact_operator_phrase_required=FINAL_EXECUTION_OPERATOR_ACKNOWLEDGEMENT,
        explicit_operator_identity_required=True,
        explicit_issuer_identity_required=True,
        explicit_materializer_identity_required=True,
        materializer_must_equal_issuer=True,
        explicit_acknowledged_at_utc_required=True,
        explicit_issued_at_utc_required=True,
        explicit_materialized_at_utc_required=True,
        acknowledgement_after_implementation_merge_required=True,
        issued_at_not_before_acknowledged_at_required=True,
        materialized_at_not_before_issued_at_required=True,
        materialized_after_implementation_merge_required=True,
        canonical_issuance_envelope_required=True,
        exact_acknowledgement_path_required=True,
        exact_acknowledgement_sha256_required=True,
        exact_writer_symbol_required=ACKNOWLEDGEMENT_WRITER_SYMBOL,
        acknowledgement_target_absent_required=True,
        target_parent_must_preexist=True,
        symbolic_parent_forbidden=True,
        exclusive_atomic_no_overwrite_required=True,
        file_mode_required=ACKNOWLEDGEMENT_FILE_MODE,
        file_fsync_required=True,
        parent_directory_fsync_required=True,
        temporary_cleanup_required=True,
        exact_persisted_bytes_reverification_required=True,
        one_materialization_only=True,
        retry_forbidden=True,
        production_callsite_separate=True,
        lease_materialization_separate=True,
        materialization_does_not_permit_invocation=True,
        authoring_effects_forbidden=True,
    )


def _build_gates() -> FinalExecutionAcknowledgementMaterializationGates:
    return FinalExecutionAcknowledgementMaterializationGates(
        acknowledgement_issuance_implementation_post_merge_verified=True,
        acknowledgement_issuance_implemented=True,
        acknowledgement_materialization_contract_authored=True,
        acknowledgement_materialization_implemented=False,
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


def build_frozen_materialization_authoring_record(
    receipt: AcknowledgementIssuanceImplementationMergeValidationReceipt,
) -> FinalExecutionAcknowledgementMaterializationAuthoring:
    """Build the exact frozen materialization authoring record."""

    receipt.require()
    record = FinalExecutionAcknowledgementMaterializationAuthoring(
        schema_version=1,
        authoring_id=FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_AUTHORING_ID,
        status=FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_AUTHORING_STATUS,
        recorded_at_utc="2026-07-30T19:45:00Z",
        source=_build_source(receipt),
        contract=_build_contract(),
        gates=_build_gates(),
        next_slice=(
            "QW-LC4-E-final-execution-acknowledgement-"
            "materialization-authoring-commit"
        ),
        post_merge_next_slice=(
            "QW-LC4-E-final-execution-acknowledgement-materialization"
        ),
        authoring_sha256="sha256:" + "0" * 64,
    )
    result = replace(
        record,
        authoring_sha256=sha256_object(record.semantic_payload()),
    )
    result.require(receipt)
    return result


def build_acknowledgement_issuance_implementation_merge_validation_receipt(
) -> AcknowledgementIssuanceImplementationMergeValidationReceipt:
    """Build the exact PR #149 post-merge validation receipt."""

    receipt = AcknowledgementIssuanceImplementationMergeValidationReceipt(
        receipt_id=(
            "stage3b-qwake-lc4-e-final-execution-acknowledgement-"
            "issuance-implementation-post-merge-validation-v1"
        ),
        pr_number=ISSUANCE_IMPLEMENTATION_PR_NUMBER,
        head_commit=ISSUANCE_IMPLEMENTATION_HEAD_COMMIT,
        base_commit=ISSUANCE_IMPLEMENTATION_PARENT_COMMIT,
        merge_commit=ISSUANCE_IMPLEMENTATION_MERGE_COMMIT,
        merged_at_utc=ISSUANCE_IMPLEMENTATION_MERGED_AT_UTC,
        commit_count=1,
        file_count=18,
        focused_tests_passed=79,
        targeted_tests_passed=280,
        full_tests_passed=1327,
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
