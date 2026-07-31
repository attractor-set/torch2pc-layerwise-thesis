"""Effect-free authoring for the final acknowledgement materializer invocation.

The module freezes the sole future invocation boundary around the already
verified acknowledgement materializer. It builds and verifies immutable
in-memory records only. Importing, verifying, or testing the authoring package
never calls the materializer or its writer, creates the acknowledgement, creates
a lease or durable outcome, inspects an image, materializes a command, invokes
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
    canonical_json,
    sha256_bytes,
    sha256_object,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_issuance_authoring import (
    ACKNOWLEDGEMENT_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_issuance_implementation import (
    LEGACY_EXECUTION_LEASE_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization import (
    FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_IMPLEMENTATION_ID,
    IMPLEMENTATION_ADR_EN_RELATIVE,
    IMPLEMENTATION_ADR_RU_RELATIVE,
    IMPLEMENTATION_MODULE_RELATIVE,
    IMPLEMENTATION_PACKAGE_RELATIVE,
    IMPLEMENTATION_RECORD_RELATIVE,
    IMPLEMENTATION_REGISTRY_RELATIVE,
    IMPLEMENTATION_SOURCE_REGISTRY_RELATIVE,
    IMPLEMENTATION_TEST_RELATIVE,
    IMPLEMENTATION_VERIFIER_RELATIVE,
    FinalExecutionAcknowledgementMaterializationImplementationError,
    FinalExecutionAcknowledgementMaterializationImplementationRecord,
    verify_final_execution_acknowledgement_materialization_implementation,
)

FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_AUTHORING_ID: Final = (
    "stage3b-qwake-lc4-e-final-execution-acknowledgement-materialization-"
    "invocation-authoring-v1"
)
FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_AUTHORING_STATUS: Final = (
    "materialization_invocation_contract_authored_not_implemented_not_invoked_"
    "execution_closed"
)
FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_ID: Final = (
    "stage3b-qwake-lc4-e-final-execution-acknowledgement-materialization-"
    "invocation-v1"
)
FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_STATUS: Final = (
    "prospective_materialization_invocation_not_executed"
)

INVOCATION_AUTHORING_BASE_COMMIT: Final = (
    "7d5e5058af6a845cf4a6add2e7fe199894f48b24"
)
MATERIALIZATION_IMPLEMENTATION_PR_NUMBER: Final = 151
MATERIALIZATION_IMPLEMENTATION_HEAD_COMMIT: Final = (
    "c52e8a5ab1de554529b94c772ec76ae24056e834"
)
MATERIALIZATION_IMPLEMENTATION_PARENT_COMMIT: Final = (
    "6497cd904f9403622249c5a32f08ef6e8bb11532"
)
MATERIALIZATION_IMPLEMENTATION_MERGE_COMMIT: Final = INVOCATION_AUTHORING_BASE_COMMIT
MATERIALIZATION_IMPLEMENTATION_MERGED_AT_UTC: Final = "2026-07-30T22:40:10Z"

MATERIALIZATION_IMPLEMENTATION_SHA256: Final = (
    "sha256:6151ec4a3e117fec5560626069d6820c89805858a087cc65d18746f8bb0912cd"
)
MATERIALIZATION_IMPLEMENTATION_FILE_SHA256: Final = (
    "sha256:dd24c23c4bd37d01187a6820eafeb73eb9cbc38e79788d973ea73091be837ead"
)
MATERIALIZATION_IMPLEMENTATION_MERGE_RECEIPT_FILE_SHA256: Final = (
    "sha256:fab15fff0a68921855b2b7e36fb93dd06b2ba971b1d78a9bee612842d5fb9883"
)
MATERIALIZATION_IMPLEMENTATION_PACKAGE_REGISTRY_SHA256: Final = (
    "sha256:50610bb5b972163af678827b7d9551e74cc16d21bf263a6a17c00d0743d0a5d0"
)
MATERIALIZATION_IMPLEMENTATION_SOURCE_REGISTRY_SHA256: Final = (
    "sha256:21c20d3c82c44afb5a8aa8aeb2af0e00a341a69ebe052ce079e4215640792337"
)
MATERIALIZATION_IMPLEMENTATION_MODULE_SHA256: Final = (
    "sha256:efb68eb2fb82b8af6b77203df77b7c449921a4266636caa11eb9b004bdeb6c19"
)
MATERIALIZATION_IMPLEMENTATION_VERIFIER_SHA256: Final = (
    "sha256:949ee75306838067c0a74b8f4674e0ec46e77cdc85a2e3c0c8d7537cf0063444"
)
MATERIALIZATION_IMPLEMENTATION_TEST_SHA256: Final = (
    "sha256:fee007d9ec2a97ac65b5d865dc52a9be94f8c5da763eb91923f8ee34c34406c4"
)
MATERIALIZATION_IMPLEMENTATION_ADR_RU_SHA256: Final = (
    "sha256:8b5a9e8ee9af1851a8a7bc0d89d5bdbaf9ff2d50a06e3c79969f31ac6e411cc0"
)
MATERIALIZATION_IMPLEMENTATION_ADR_EN_SHA256: Final = (
    "sha256:4c5cd896655537571fa8c04e1f78cc3a424c4803fef144a7615259014025d957"
)

PROSPECTIVE_MATERIALIZATION_BUILDER_SYMBOL: Final = (
    "torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_"
    "materialization_authoring.build_prospective_acknowledgement_materialization"
)
ACKNOWLEDGEMENT_MATERIALIZER_SYMBOL: Final = (
    "torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_"
    "materialization.materialize_final_execution_acknowledgement"
)
ACKNOWLEDGEMENT_WRITER_SYMBOL: Final = (
    "torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_"
    "issuance_implementation.persist_final_execution_acknowledgement"
)

PACKAGE_RELATIVE: Final = Path(
    "experiments/frozen/stage3b-qwake-lc4-e-final-execution-"
    "acknowledgement-materialization-invocation-authoring-v1"
)
AUTHORING_RECORD_RELATIVE: Final = PACKAGE_RELATIVE / "authoring.json"
IMPLEMENTATION_MERGE_RECEIPT_RELATIVE: Final = (
    PACKAGE_RELATIVE / "implementation-merge-validation.json"
)
REGISTRY_RELATIVE: Final = PACKAGE_RELATIVE / "SHA256SUMS"
SOURCE_REGISTRY_RELATIVE: Final = PACKAGE_RELATIVE / "source-SHA256SUMS"
MODULE_RELATIVE: Final = Path(
    "src/torch2pc_thesis/stage3b_qwake_lc4_final_execution_acknowledgement_"
    "materialization_invocation_authoring.py"
)
VERIFIER_RELATIVE: Final = Path(
    "scripts/verify_stage3b_qwake_lc4_final_execution_acknowledgement_"
    "materialization_invocation_authoring.py"
)
TEST_RELATIVE: Final = Path(
    "tests/unit/test_stage3b_qwake_lc4_final_execution_acknowledgement_"
    "materialization_invocation_authoring.py"
)
ADR_RU_RELATIVE: Final = Path(
    "docs/decisions/ADR-091-stage3b-qwake-lc4-e-final-execution-"
    "acknowledgement-materialization-invocation-authoring.md"
)
ADR_EN_RELATIVE: Final = Path(
    "docs/decisions/ADR-091-stage3b-qwake-lc4-e-final-execution-"
    "acknowledgement-materialization-invocation-authoring_EN.md"
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
        (IMPLEMENTATION_PACKAGE_RELATIVE / "authoring-merge-validation.json").as_posix(),
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
        "invoke_lease_bound_host_runtime",
        "invoke_one_shot_host_runtime",
        "materialize_final_execution_acknowledgement",
        "materialize_invocation_command",
        "persist_durable_host_outcome_receipt",
        "persist_final_execution_acknowledgement",
        "persist_persistent_execution_lease_v2",
    }
)
_FORBIDDEN_CALL_ATTRIBUTES: Final = frozenset(
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
    "FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_AUTHORING_ID",
    "AcknowledgementMaterializationImplementationMergeValidationReceipt",
    "FinalExecutionAcknowledgementMaterializationInvocationAuthoring",
    "FinalExecutionAcknowledgementMaterializationInvocationAuthoringError",
    "FinalExecutionAcknowledgementMaterializationInvocationContract",
    "FinalExecutionAcknowledgementMaterializationInvocationGates",
    "FinalExecutionAcknowledgementMaterializationInvocationSource",
    "ProspectiveFinalExecutionAcknowledgementMaterializationInvocation",
    "build_frozen_materialization_invocation_authoring_record",
    "build_materialization_implementation_merge_validation_receipt",
    "build_prospective_acknowledgement_materialization_invocation",
    "load_final_execution_acknowledgement_materialization_invocation_authoring",
    "load_materialization_implementation_merge_validation_receipt",
    "verify_final_execution_acknowledgement_materialization_invocation_authoring",
]


class FinalExecutionAcknowledgementMaterializationInvocationAuthoringError(RuntimeError):
    """Raised when the invocation-authoring contract fails closed."""


def _require_sha256(value: str, field_name: str) -> None:
    if not _SHA256_PATTERN.fullmatch(value):
        raise FinalExecutionAcknowledgementMaterializationInvocationAuthoringError(
            f"{field_name} is not a canonical SHA-256 identity"
        )


def _require_commit(value: str, field_name: str) -> None:
    if not _COMMIT_PATTERN.fullmatch(value):
        raise FinalExecutionAcknowledgementMaterializationInvocationAuthoringError(
            f"{field_name} is not a commit identity"
        )


def _require_identity(value: str, field_name: str) -> None:
    if value != value.strip() or not _IDENTITY_PATTERN.fullmatch(value):
        raise FinalExecutionAcknowledgementMaterializationInvocationAuthoringError(
            f"{field_name} is not a bounded identity"
        )


def _require_utc(value: str, field_name: str) -> datetime:
    if not value.endswith("Z"):
        raise FinalExecutionAcknowledgementMaterializationInvocationAuthoringError(
            f"{field_name} is not a UTC timestamp"
        )
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise FinalExecutionAcknowledgementMaterializationInvocationAuthoringError(
            f"{field_name} is not an ISO-8601 timestamp"
        ) from exc
    if parsed.tzinfo != UTC:
        raise FinalExecutionAcknowledgementMaterializationInvocationAuthoringError(
            f"{field_name} is not normalized to UTC"
        )
    return parsed


@dataclass(frozen=True)
class AcknowledgementMaterializationImplementationMergeValidationReceipt:
    """Exact post-merge receipt for materialization implementation PR #151."""

    receipt_id: str
    pr_number: int
    head_commit: str
    base_commit: str
    merge_commit: str
    merged_at_utc: str
    commit_count: int
    file_count: int
    insertions: int
    deletions: int
    focused_tests_passed: int
    targeted_tests_passed: int
    full_tests_passed: int
    full_test_warnings: int
    required_ci_checks_total: int
    required_ci_checks_passed: bool
    production_execution_boundary_closed: bool
    receipt_sha256: str

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, object],
    ) -> AcknowledgementMaterializationImplementationMergeValidationReceipt:
        return cls(**cast(dict[str, Any], dict(value)))

    def semantic_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload.pop("receipt_sha256")
        return cast(dict[str, object], payload)

    def require(self) -> None:
        expected: dict[str, object] = {
            "receipt_id": (
                "stage3b-qwake-lc4-e-final-execution-acknowledgement-"
                "materialization-implementation-post-merge-validation-v1"
            ),
            "pr_number": MATERIALIZATION_IMPLEMENTATION_PR_NUMBER,
            "head_commit": MATERIALIZATION_IMPLEMENTATION_HEAD_COMMIT,
            "base_commit": MATERIALIZATION_IMPLEMENTATION_PARENT_COMMIT,
            "merge_commit": MATERIALIZATION_IMPLEMENTATION_MERGE_COMMIT,
            "merged_at_utc": MATERIALIZATION_IMPLEMENTATION_MERGED_AT_UTC,
            "commit_count": 1,
            "file_count": 18,
            "insertions": 1997,
            "deletions": 0,
            "focused_tests_passed": 108,
            "targeted_tests_passed": 309,
            "full_tests_passed": 1356,
            "full_test_warnings": 14,
            "required_ci_checks_total": 4,
            "required_ci_checks_passed": True,
            "production_execution_boundary_closed": True,
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise FinalExecutionAcknowledgementMaterializationInvocationAuthoringError(
                    f"materialization implementation merge receipt differs: {field_name}"
                )
        _require_commit(self.head_commit, "head_commit")
        _require_commit(self.base_commit, "base_commit")
        _require_commit(self.merge_commit, "merge_commit")
        _require_utc(self.merged_at_utc, "merged_at_utc")
        _require_sha256(self.receipt_sha256, "receipt_sha256")
        if self.receipt_sha256 != sha256_object(self.semantic_payload()):
            raise FinalExecutionAcknowledgementMaterializationInvocationAuthoringError(
                "materialization implementation merge receipt semantic SHA-256 differs"
            )

    def canonical_json(self) -> str:
        self.require()
        return canonical_json(self)


@dataclass(frozen=True)
class FinalExecutionAcknowledgementMaterializationInvocationSource:
    """Exact frozen inputs for the invocation-authoring contract."""

    invocation_authoring_base_commit: str
    materialization_implementation_id: str
    materialization_implementation_sha256: str
    materialization_implementation_file_sha256: str
    materialization_implementation_merge_receipt_file_sha256: str
    materialization_implementation_package_registry_sha256: str
    materialization_implementation_source_registry_sha256: str
    materialization_implementation_module_sha256: str
    materialization_implementation_verifier_sha256: str
    materialization_implementation_test_sha256: str
    materialization_implementation_adr_ru_sha256: str
    materialization_implementation_adr_en_sha256: str
    materialization_implementation_pr_number: int
    materialization_implementation_head_commit: str
    materialization_implementation_parent_commit: str
    materialization_implementation_merge_commit: str
    materialization_implementation_merged_at_utc: str
    acknowledgement_relative: str
    prospective_materialization_builder_symbol: str
    acknowledgement_materializer_symbol: str
    acknowledgement_writer_symbol: str

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, object],
    ) -> FinalExecutionAcknowledgementMaterializationInvocationSource:
        return cls(**cast(dict[str, Any], dict(value)))

    def require(
        self,
        receipt: AcknowledgementMaterializationImplementationMergeValidationReceipt,
    ) -> None:
        receipt.require()
        if self != _build_source(receipt):
            raise FinalExecutionAcknowledgementMaterializationInvocationAuthoringError(
                "materialization invocation source differs"
            )


@dataclass(frozen=True)
class FinalExecutionAcknowledgementMaterializationInvocationContract:
    """Rules for one future explicit materializer invocation."""

    complete_implementation_identity_required: bool
    implementation_post_merge_verification_required: bool
    prospective_invocation_inputs_only: bool
    exact_operator_phrase_required: str
    explicit_operator_identity_required: bool
    explicit_acknowledged_at_utc_required: bool
    explicit_issuer_identity_required: bool
    explicit_issued_at_utc_required: bool
    explicit_materializer_identity_required: bool
    explicit_materialized_at_utc_required: bool
    materializer_must_equal_issuer: bool
    ordered_timestamps_required: bool
    acknowledgement_target_absent_before_first_attempt_required: bool
    exact_acknowledgement_path_required: bool
    exact_prospective_builder_symbol_required: str
    exact_materializer_symbol_required: str
    materializer_call_limit: int
    direct_writer_call_forbidden: bool
    production_callsite_separate: bool
    repository_materializer_callsite_forbidden: bool
    automatic_retry_forbidden: bool
    blind_retry_forbidden: bool
    explicit_recovery_permitted: bool
    recovery_state_probe_required: bool
    absent_target_requires_new_explicit_authorization: bool
    valid_existing_target_treated_as_success: bool
    invalid_existing_target_fail_closed: bool
    target_exists_materializer_recall_forbidden: bool
    authoring_effects_forbidden: bool
    subprocess_forbidden: bool
    docker_forbidden: bool
    image_inspection_forbidden: bool
    command_materialization_forbidden: bool
    lease_materialization_forbidden: bool
    durable_outcome_persistence_forbidden: bool
    authorization_consumption_forbidden: bool
    local_compute_forbidden: bool

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, object],
    ) -> FinalExecutionAcknowledgementMaterializationInvocationContract:
        return cls(**cast(dict[str, Any], dict(value)))

    def require(self) -> None:
        if self != _build_contract():
            raise FinalExecutionAcknowledgementMaterializationInvocationAuthoringError(
                "materialization invocation contract differs"
            )


@dataclass(frozen=True)
class FinalExecutionAcknowledgementMaterializationInvocationGates:
    """Closed production state at invocation-authoring time."""

    materialization_implementation_post_merge_verified: bool
    acknowledgement_materialization_implemented: bool
    materialization_invocation_contract_authored: bool
    materialization_invocation_implemented: bool
    materialization_invoked: bool
    materializer_called: bool
    writer_called: bool
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
    ) -> FinalExecutionAcknowledgementMaterializationInvocationGates:
        return cls(**cast(dict[str, Any], dict(value)))

    def require(self) -> None:
        if self != _build_gates():
            raise FinalExecutionAcknowledgementMaterializationInvocationAuthoringError(
                "materialization invocation gates differ"
            )


@dataclass(frozen=True)
class FinalExecutionAcknowledgementMaterializationInvocationAuthoring:
    """Frozen authoring record for the future explicit invocation."""

    schema_version: int
    authoring_id: str
    status: str
    recorded_at_utc: str
    source: FinalExecutionAcknowledgementMaterializationInvocationSource
    contract: FinalExecutionAcknowledgementMaterializationInvocationContract
    gates: FinalExecutionAcknowledgementMaterializationInvocationGates
    next_slice: str
    post_merge_next_slice: str
    authoring_sha256: str

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, object],
    ) -> FinalExecutionAcknowledgementMaterializationInvocationAuthoring:
        payload = dict(value)
        payload["source"] = (
            FinalExecutionAcknowledgementMaterializationInvocationSource.from_mapping(
                cast(Mapping[str, object], payload["source"])
            )
        )
        payload["contract"] = (
            FinalExecutionAcknowledgementMaterializationInvocationContract.from_mapping(
                cast(Mapping[str, object], payload["contract"])
            )
        )
        payload["gates"] = (
            FinalExecutionAcknowledgementMaterializationInvocationGates.from_mapping(
                cast(Mapping[str, object], payload["gates"])
            )
        )
        return cls(**cast(dict[str, Any], payload))

    def semantic_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload.pop("authoring_sha256")
        return cast(dict[str, object], payload)

    def require(
        self,
        receipt: AcknowledgementMaterializationImplementationMergeValidationReceipt,
    ) -> None:
        expected: dict[str, object] = {
            "schema_version": 1,
            "authoring_id": (
                FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_AUTHORING_ID
            ),
            "status": (
                FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_AUTHORING_STATUS
            ),
            "recorded_at_utc": "2026-07-30T23:10:00Z",
            "next_slice": (
                "QW-LC4-E-final-execution-acknowledgement-materialization-"
                "invocation-authoring-commit"
            ),
            "post_merge_next_slice": (
                "QW-LC4-E-final-execution-acknowledgement-materialization-"
                "invocation-implementation"
            ),
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise FinalExecutionAcknowledgementMaterializationInvocationAuthoringError(
                    f"materialization invocation authoring differs: {field_name}"
                )
        recorded = _require_utc(self.recorded_at_utc, "recorded_at_utc")
        merged = _require_utc(receipt.merged_at_utc, "merged_at_utc")
        if recorded <= merged:
            raise FinalExecutionAcknowledgementMaterializationInvocationAuthoringError(
                "invocation authoring timestamp is not after implementation merge"
            )
        self.source.require(receipt)
        self.contract.require()
        self.gates.require()
        _require_sha256(self.authoring_sha256, "authoring_sha256")
        if self.authoring_sha256 != sha256_object(self.semantic_payload()):
            raise FinalExecutionAcknowledgementMaterializationInvocationAuthoringError(
                "materialization invocation authoring semantic SHA-256 differs"
            )

    def canonical_json(
        self,
        receipt: AcknowledgementMaterializationImplementationMergeValidationReceipt,
    ) -> str:
        self.require(receipt)
        return canonical_json(self)


@dataclass(frozen=True)
class ProspectiveFinalExecutionAcknowledgementMaterializationInvocation:
    """Pure operator-bound inputs for one future invocation; no call occurs."""

    invocation_id: str
    status: str
    invocation_authoring_sha256: str
    materialization_implementation_sha256: str
    acknowledgement_phrase: str
    operator_identity: str
    acknowledged_at_utc: str
    issuer_identity: str
    issued_at_utc: str
    materializer_identity: str
    materialized_at_utc: str
    acknowledgement_relative: str
    prospective_materialization_builder_symbol: str
    acknowledgement_materializer_symbol: str
    materializer_call_limit: int
    automatic_retry_permitted: bool
    blind_retry_permitted: bool
    explicit_recovery_permitted: bool
    recovery_state_probe_performed: bool
    materialization_invoked: bool
    materializer_called: bool
    writer_called: bool
    final_execution_acknowledgement_issued: bool
    final_execution_acknowledged: bool
    one_shot_engineering_invocation_permitted: bool

    def require(
        self,
        authoring: FinalExecutionAcknowledgementMaterializationInvocationAuthoring,
        receipt: AcknowledgementMaterializationImplementationMergeValidationReceipt,
    ) -> None:
        authoring.require(receipt)
        expected: dict[str, object] = {
            "invocation_id": (
                FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_ID
            ),
            "status": (
                FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_STATUS
            ),
            "invocation_authoring_sha256": authoring.authoring_sha256,
            "materialization_implementation_sha256": (
                MATERIALIZATION_IMPLEMENTATION_SHA256
            ),
            "acknowledgement_phrase": FINAL_EXECUTION_OPERATOR_ACKNOWLEDGEMENT,
            "acknowledgement_relative": ACKNOWLEDGEMENT_RELATIVE.as_posix(),
            "prospective_materialization_builder_symbol": (
                PROSPECTIVE_MATERIALIZATION_BUILDER_SYMBOL
            ),
            "acknowledgement_materializer_symbol": ACKNOWLEDGEMENT_MATERIALIZER_SYMBOL,
            "materializer_call_limit": 1,
            "automatic_retry_permitted": False,
            "blind_retry_permitted": False,
            "explicit_recovery_permitted": True,
            "recovery_state_probe_performed": False,
            "materialization_invoked": False,
            "materializer_called": False,
            "writer_called": False,
            "final_execution_acknowledgement_issued": False,
            "final_execution_acknowledged": False,
            "one_shot_engineering_invocation_permitted": False,
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise FinalExecutionAcknowledgementMaterializationInvocationAuthoringError(
                    f"prospective materialization invocation differs: {field_name}"
                )
        _require_identity(self.operator_identity, "operator_identity")
        _require_identity(self.issuer_identity, "issuer_identity")
        _require_identity(self.materializer_identity, "materializer_identity")
        if self.materializer_identity != self.issuer_identity:
            raise FinalExecutionAcknowledgementMaterializationInvocationAuthoringError(
                "materializer identity differs from issuer identity"
            )
        acknowledged = _require_utc(self.acknowledged_at_utc, "acknowledged_at_utc")
        issued = _require_utc(self.issued_at_utc, "issued_at_utc")
        materialized = _require_utc(self.materialized_at_utc, "materialized_at_utc")
        merged = _require_utc(receipt.merged_at_utc, "merged_at_utc")
        if acknowledged <= merged:
            raise FinalExecutionAcknowledgementMaterializationInvocationAuthoringError(
                "acknowledgement timestamp is not after implementation merge"
            )
        if issued < acknowledged:
            raise FinalExecutionAcknowledgementMaterializationInvocationAuthoringError(
                "issuance timestamp is before acknowledgement"
            )
        if materialized < issued:
            raise FinalExecutionAcknowledgementMaterializationInvocationAuthoringError(
                "materialization timestamp is before issuance"
            )

    def canonical_json(
        self,
        authoring: FinalExecutionAcknowledgementMaterializationInvocationAuthoring,
        receipt: AcknowledgementMaterializationImplementationMergeValidationReceipt,
    ) -> str:
        self.require(authoring, receipt)
        return canonical_json(self)


def build_prospective_acknowledgement_materialization_invocation(
    authoring: FinalExecutionAcknowledgementMaterializationInvocationAuthoring,
    receipt: AcknowledgementMaterializationImplementationMergeValidationReceipt,
    *,
    acknowledgement_phrase: str,
    operator_identity: str,
    acknowledged_at_utc: str,
    issuer_identity: str,
    issued_at_utc: str,
    materializer_identity: str,
    materialized_at_utc: str,
) -> ProspectiveFinalExecutionAcknowledgementMaterializationInvocation:
    """Build one future invocation request without invoking the materializer."""

    authoring.require(receipt)
    result = ProspectiveFinalExecutionAcknowledgementMaterializationInvocation(
        invocation_id=FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_ID,
        status=FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_STATUS,
        invocation_authoring_sha256=authoring.authoring_sha256,
        materialization_implementation_sha256=MATERIALIZATION_IMPLEMENTATION_SHA256,
        acknowledgement_phrase=acknowledgement_phrase,
        operator_identity=operator_identity,
        acknowledged_at_utc=acknowledged_at_utc,
        issuer_identity=issuer_identity,
        issued_at_utc=issued_at_utc,
        materializer_identity=materializer_identity,
        materialized_at_utc=materialized_at_utc,
        acknowledgement_relative=ACKNOWLEDGEMENT_RELATIVE.as_posix(),
        prospective_materialization_builder_symbol=(
            PROSPECTIVE_MATERIALIZATION_BUILDER_SYMBOL
        ),
        acknowledgement_materializer_symbol=ACKNOWLEDGEMENT_MATERIALIZER_SYMBOL,
        materializer_call_limit=1,
        automatic_retry_permitted=False,
        blind_retry_permitted=False,
        explicit_recovery_permitted=True,
        recovery_state_probe_performed=False,
        materialization_invoked=False,
        materializer_called=False,
        writer_called=False,
        final_execution_acknowledgement_issued=False,
        final_execution_acknowledged=False,
        one_shot_engineering_invocation_permitted=False,
    )
    result.require(authoring, receipt)
    return result


def load_materialization_implementation_merge_validation_receipt(
    path: Path,
) -> AcknowledgementMaterializationImplementationMergeValidationReceipt:
    receipt = AcknowledgementMaterializationImplementationMergeValidationReceipt.from_mapping(
        _load_json(path)
    )
    receipt.require()
    return receipt


def load_final_execution_acknowledgement_materialization_invocation_authoring(
    path: Path,
    receipt: AcknowledgementMaterializationImplementationMergeValidationReceipt,
) -> FinalExecutionAcknowledgementMaterializationInvocationAuthoring:
    authoring = FinalExecutionAcknowledgementMaterializationInvocationAuthoring.from_mapping(
        _load_json(path)
    )
    authoring.require(receipt)
    return authoring


def verify_final_execution_acknowledgement_materialization_invocation_authoring(
    project_root: Path,
) -> FinalExecutionAcknowledgementMaterializationInvocationAuthoring:
    """Verify the frozen invocation-authoring package without effects."""

    root = _verified_project_root(project_root)
    package = root / PACKAGE_RELATIVE
    if not package.is_dir() or package.is_symlink():
        raise FinalExecutionAcknowledgementMaterializationInvocationAuthoringError(
            "materialization invocation authoring package is absent or invalid"
        )
    if {path.name for path in package.iterdir()} != _EXPECTED_PACKAGE_FILES:
        raise FinalExecutionAcknowledgementMaterializationInvocationAuthoringError(
            "materialization invocation authoring package file set differs"
        )
    _verify_registry(root / REGISTRY_RELATIVE, package)
    source_registry = _verify_registry(root / SOURCE_REGISTRY_RELATIVE, root)
    if frozenset(source_registry) != _EXPECTED_SOURCE_PATHS:
        raise FinalExecutionAcknowledgementMaterializationInvocationAuthoringError(
            "materialization invocation source registry path set differs"
        )
    receipt = load_materialization_implementation_merge_validation_receipt(
        root / IMPLEMENTATION_MERGE_RECEIPT_RELATIVE
    )
    authoring = (
        load_final_execution_acknowledgement_materialization_invocation_authoring(
            root / AUTHORING_RECORD_RELATIVE,
            receipt,
        )
    )
    try:
        implementation = (
            verify_final_execution_acknowledgement_materialization_implementation(root)
        )
    except FinalExecutionAcknowledgementMaterializationImplementationError as exc:
        raise FinalExecutionAcknowledgementMaterializationInvocationAuthoringError(
            str(exc)
        ) from exc
    _verify_implementation_record(implementation)
    _verify_effect_free_authoring_ast(root)
    _require_repository_materializer_callsite_absent(root)
    _require_production_boundary_closed(root)
    authoring.require(receipt)
    return authoring


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8", errors="strict"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FinalExecutionAcknowledgementMaterializationInvocationAuthoringError(
            f"JSON record is unreadable: {path}"
        ) from exc
    if not isinstance(payload, dict):
        raise FinalExecutionAcknowledgementMaterializationInvocationAuthoringError(
            f"JSON record is not an object: {path}"
        )
    return cast(dict[str, Any], payload)


def _load_registry(path: Path) -> dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8", errors="strict").splitlines()
    except (OSError, UnicodeError) as exc:
        raise FinalExecutionAcknowledgementMaterializationInvocationAuthoringError(
            f"registry is unreadable: {path}"
        ) from exc
    result: dict[str, str] = {}
    for line in lines:
        if "  " not in line:
            raise FinalExecutionAcknowledgementMaterializationInvocationAuthoringError(
                f"registry line is invalid: {path}"
            )
        digest, relative = line.split("  ", 1)
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise FinalExecutionAcknowledgementMaterializationInvocationAuthoringError(
                f"registry digest is invalid: {path}"
            )
        if not relative or relative in result:
            raise FinalExecutionAcknowledgementMaterializationInvocationAuthoringError(
                f"registry path is invalid or duplicated: {path}"
            )
        result[relative] = digest
    return result


def _verified_project_root(project_root: Path) -> Path:
    expanded = project_root.expanduser()
    if expanded.is_symlink():
        raise FinalExecutionAcknowledgementMaterializationInvocationAuthoringError(
            "project root is symbolic"
        )
    root = expanded.resolve()
    if not root.is_dir():
        raise FinalExecutionAcknowledgementMaterializationInvocationAuthoringError(
            "project root is absent or non-directory"
        )
    return root


def _verify_registry(path: Path, base: Path) -> dict[str, str]:
    registry = _load_registry(path)
    for relative, expected in registry.items():
        target = base / relative
        if not target.is_file() or target.is_symlink():
            raise FinalExecutionAcknowledgementMaterializationInvocationAuthoringError(
                f"registry target is absent or invalid: {relative}"
            )
        observed = sha256_bytes(target.read_bytes()).removeprefix("sha256:")
        if observed != expected:
            raise FinalExecutionAcknowledgementMaterializationInvocationAuthoringError(
                f"registry target identity differs: {relative}"
            )
    return registry


def _verify_implementation_record(
    implementation: FinalExecutionAcknowledgementMaterializationImplementationRecord,
) -> None:
    if implementation.implementation_id != (
        FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_IMPLEMENTATION_ID
    ):
        raise FinalExecutionAcknowledgementMaterializationInvocationAuthoringError(
            "materialization implementation ID differs"
        )
    if implementation.implementation_sha256 != MATERIALIZATION_IMPLEMENTATION_SHA256:
        raise FinalExecutionAcknowledgementMaterializationInvocationAuthoringError(
            "materialization implementation semantic identity differs"
        )
    if not implementation.gates.acknowledgement_materialization_implemented:
        raise FinalExecutionAcknowledgementMaterializationInvocationAuthoringError(
            "materialization implementation gate is closed"
        )


def _verify_effect_free_authoring_ast(root: Path) -> None:
    for path in (root / MODULE_RELATIVE, root / VERIFIER_RELATIVE):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="strict"))
        except (OSError, UnicodeError, SyntaxError) as exc:
            raise FinalExecutionAcknowledgementMaterializationInvocationAuthoringError(
                f"materialization invocation authoring source is invalid: {path}"
            ) from exc
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots = {alias.name.split(".", 1)[0] for alias in node.names}
                if roots & _FORBIDDEN_IMPORT_ROOTS:
                    raise FinalExecutionAcknowledgementMaterializationInvocationAuthoringError(
                        f"forbidden invocation-authoring import: {path}"
                    )
            if (
                isinstance(node, ast.ImportFrom)
                and node.module
                and node.module.split(".", 1)[0] in _FORBIDDEN_IMPORT_ROOTS
            ):
                raise FinalExecutionAcknowledgementMaterializationInvocationAuthoringError(
                    f"forbidden invocation-authoring import: {path}"
                )
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Name) and node.func.id in _FORBIDDEN_CALL_NAMES:
                raise FinalExecutionAcknowledgementMaterializationInvocationAuthoringError(
                    f"forbidden invocation-authoring call: {path}"
                )
            if (
                isinstance(node.func, ast.Attribute)
                and node.func.attr in _FORBIDDEN_CALL_ATTRIBUTES
            ):
                raise FinalExecutionAcknowledgementMaterializationInvocationAuthoringError(
                    f"forbidden invocation-authoring effect: {path}"
                )


def _require_repository_materializer_callsite_absent(root: Path) -> None:
    for path in sorted((root / "src").rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="strict"))
        except (OSError, UnicodeError, SyntaxError) as exc:
            raise FinalExecutionAcknowledgementMaterializationInvocationAuthoringError(
                f"repository Python source is invalid: {path}"
            ) from exc
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            called = ""
            if isinstance(node.func, ast.Name):
                called = node.func.id
            elif isinstance(node.func, ast.Attribute):
                called = node.func.attr
            if called == "materialize_final_execution_acknowledgement":
                raise FinalExecutionAcknowledgementMaterializationInvocationAuthoringError(
                    f"repository materializer callsite exists: {path}"
                )


def _require_production_boundary_closed(root: Path) -> None:
    for relative in (
        ACKNOWLEDGEMENT_RELATIVE,
        LEGACY_EXECUTION_LEASE_RELATIVE,
        EXECUTION_LEASE_V2_RELATIVE,
        DURABLE_HOST_OUTCOME_RELATIVE,
    ):
        target = root / relative
        if target.exists() or target.is_symlink():
            raise FinalExecutionAcknowledgementMaterializationInvocationAuthoringError(
                f"production boundary artifact exists: {relative}"
            )
    output_parent = root / ACKNOWLEDGEMENT_RELATIVE.parent
    if output_parent.is_dir():
        forbidden_prefixes = (
            ".qwake-lc4-runtime-validation-v1-attempt-001.staging-",
            ".qwake-lc4-runtime-validation-v1-attempt-001.final-execution-"
            "acknowledgement.json.tmp-",
        )
        for path in output_parent.iterdir():
            if any(path.name.startswith(prefix) for prefix in forbidden_prefixes):
                raise FinalExecutionAcknowledgementMaterializationInvocationAuthoringError(
                    f"production boundary staging artifact exists: {path.name}"
                )


def _build_source(
    receipt: AcknowledgementMaterializationImplementationMergeValidationReceipt,
) -> FinalExecutionAcknowledgementMaterializationInvocationSource:
    receipt.require()
    return FinalExecutionAcknowledgementMaterializationInvocationSource(
        invocation_authoring_base_commit=INVOCATION_AUTHORING_BASE_COMMIT,
        materialization_implementation_id=(
            FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_IMPLEMENTATION_ID
        ),
        materialization_implementation_sha256=MATERIALIZATION_IMPLEMENTATION_SHA256,
        materialization_implementation_file_sha256=(
            MATERIALIZATION_IMPLEMENTATION_FILE_SHA256
        ),
        materialization_implementation_merge_receipt_file_sha256=(
            MATERIALIZATION_IMPLEMENTATION_MERGE_RECEIPT_FILE_SHA256
        ),
        materialization_implementation_package_registry_sha256=(
            MATERIALIZATION_IMPLEMENTATION_PACKAGE_REGISTRY_SHA256
        ),
        materialization_implementation_source_registry_sha256=(
            MATERIALIZATION_IMPLEMENTATION_SOURCE_REGISTRY_SHA256
        ),
        materialization_implementation_module_sha256=(
            MATERIALIZATION_IMPLEMENTATION_MODULE_SHA256
        ),
        materialization_implementation_verifier_sha256=(
            MATERIALIZATION_IMPLEMENTATION_VERIFIER_SHA256
        ),
        materialization_implementation_test_sha256=(
            MATERIALIZATION_IMPLEMENTATION_TEST_SHA256
        ),
        materialization_implementation_adr_ru_sha256=(
            MATERIALIZATION_IMPLEMENTATION_ADR_RU_SHA256
        ),
        materialization_implementation_adr_en_sha256=(
            MATERIALIZATION_IMPLEMENTATION_ADR_EN_SHA256
        ),
        materialization_implementation_pr_number=receipt.pr_number,
        materialization_implementation_head_commit=receipt.head_commit,
        materialization_implementation_parent_commit=receipt.base_commit,
        materialization_implementation_merge_commit=receipt.merge_commit,
        materialization_implementation_merged_at_utc=receipt.merged_at_utc,
        acknowledgement_relative=ACKNOWLEDGEMENT_RELATIVE.as_posix(),
        prospective_materialization_builder_symbol=(
            PROSPECTIVE_MATERIALIZATION_BUILDER_SYMBOL
        ),
        acknowledgement_materializer_symbol=ACKNOWLEDGEMENT_MATERIALIZER_SYMBOL,
        acknowledgement_writer_symbol=ACKNOWLEDGEMENT_WRITER_SYMBOL,
    )


def _build_contract() -> FinalExecutionAcknowledgementMaterializationInvocationContract:
    return FinalExecutionAcknowledgementMaterializationInvocationContract(
        complete_implementation_identity_required=True,
        implementation_post_merge_verification_required=True,
        prospective_invocation_inputs_only=True,
        exact_operator_phrase_required=FINAL_EXECUTION_OPERATOR_ACKNOWLEDGEMENT,
        explicit_operator_identity_required=True,
        explicit_acknowledged_at_utc_required=True,
        explicit_issuer_identity_required=True,
        explicit_issued_at_utc_required=True,
        explicit_materializer_identity_required=True,
        explicit_materialized_at_utc_required=True,
        materializer_must_equal_issuer=True,
        ordered_timestamps_required=True,
        acknowledgement_target_absent_before_first_attempt_required=True,
        exact_acknowledgement_path_required=True,
        exact_prospective_builder_symbol_required=(
            PROSPECTIVE_MATERIALIZATION_BUILDER_SYMBOL
        ),
        exact_materializer_symbol_required=ACKNOWLEDGEMENT_MATERIALIZER_SYMBOL,
        materializer_call_limit=1,
        direct_writer_call_forbidden=True,
        production_callsite_separate=True,
        repository_materializer_callsite_forbidden=True,
        automatic_retry_forbidden=True,
        blind_retry_forbidden=True,
        explicit_recovery_permitted=True,
        recovery_state_probe_required=True,
        absent_target_requires_new_explicit_authorization=True,
        valid_existing_target_treated_as_success=True,
        invalid_existing_target_fail_closed=True,
        target_exists_materializer_recall_forbidden=True,
        authoring_effects_forbidden=True,
        subprocess_forbidden=True,
        docker_forbidden=True,
        image_inspection_forbidden=True,
        command_materialization_forbidden=True,
        lease_materialization_forbidden=True,
        durable_outcome_persistence_forbidden=True,
        authorization_consumption_forbidden=True,
        local_compute_forbidden=True,
    )


def _build_gates() -> FinalExecutionAcknowledgementMaterializationInvocationGates:
    return FinalExecutionAcknowledgementMaterializationInvocationGates(
        materialization_implementation_post_merge_verified=True,
        acknowledgement_materialization_implemented=True,
        materialization_invocation_contract_authored=True,
        materialization_invocation_implemented=False,
        materialization_invoked=False,
        materializer_called=False,
        writer_called=False,
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


def build_frozen_materialization_invocation_authoring_record(
    receipt: AcknowledgementMaterializationImplementationMergeValidationReceipt,
) -> FinalExecutionAcknowledgementMaterializationInvocationAuthoring:
    """Build the exact frozen invocation-authoring record."""

    receipt.require()
    provisional = FinalExecutionAcknowledgementMaterializationInvocationAuthoring(
        schema_version=1,
        authoring_id=(
            FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_AUTHORING_ID
        ),
        status=(
            FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_AUTHORING_STATUS
        ),
        recorded_at_utc="2026-07-30T23:10:00Z",
        source=_build_source(receipt),
        contract=_build_contract(),
        gates=_build_gates(),
        next_slice=(
            "QW-LC4-E-final-execution-acknowledgement-materialization-"
            "invocation-authoring-commit"
        ),
        post_merge_next_slice=(
            "QW-LC4-E-final-execution-acknowledgement-materialization-"
            "invocation-implementation"
        ),
        authoring_sha256="sha256:" + "0" * 64,
    )
    result = replace(
        provisional,
        authoring_sha256=sha256_object(provisional.semantic_payload()),
    )
    result.require(receipt)
    return result


def build_materialization_implementation_merge_validation_receipt(
) -> AcknowledgementMaterializationImplementationMergeValidationReceipt:
    """Build the exact independently verified PR #151 merge receipt."""

    provisional = AcknowledgementMaterializationImplementationMergeValidationReceipt(
        receipt_id=(
            "stage3b-qwake-lc4-e-final-execution-acknowledgement-"
            "materialization-implementation-post-merge-validation-v1"
        ),
        pr_number=MATERIALIZATION_IMPLEMENTATION_PR_NUMBER,
        head_commit=MATERIALIZATION_IMPLEMENTATION_HEAD_COMMIT,
        base_commit=MATERIALIZATION_IMPLEMENTATION_PARENT_COMMIT,
        merge_commit=MATERIALIZATION_IMPLEMENTATION_MERGE_COMMIT,
        merged_at_utc=MATERIALIZATION_IMPLEMENTATION_MERGED_AT_UTC,
        commit_count=1,
        file_count=18,
        insertions=1997,
        deletions=0,
        focused_tests_passed=108,
        targeted_tests_passed=309,
        full_tests_passed=1356,
        full_test_warnings=14,
        required_ci_checks_total=4,
        required_ci_checks_passed=True,
        production_execution_boundary_closed=True,
        receipt_sha256="sha256:" + "0" * 64,
    )
    result = replace(
        provisional,
        receipt_sha256=sha256_object(provisional.semantic_payload()),
    )
    result.require()
    return result
