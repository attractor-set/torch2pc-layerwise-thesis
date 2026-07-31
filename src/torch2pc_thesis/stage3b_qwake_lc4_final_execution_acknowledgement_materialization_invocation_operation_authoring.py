"""Effect-free authoring for one operator-bound materialization operation.

The module freezes the future operation that may call the already verified
acknowledgement-materialization invocation adapter. It builds and verifies
immutable in-memory records only. It never calls the adapter, recovery probe,
materializer, writer, runtime, Docker, image inspection, command materializer,
or local compute and never creates an acknowledgement, lease, or durable
outcome.
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
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation import (
    FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_IMPLEMENTATION_ID,
    IMPLEMENTATION_ADR_EN_RELATIVE,
    IMPLEMENTATION_ADR_RU_RELATIVE,
    IMPLEMENTATION_MODULE_RELATIVE,
    IMPLEMENTATION_PACKAGE_RELATIVE,
    IMPLEMENTATION_RECORD_RELATIVE,
    IMPLEMENTATION_REGISTRY_RELATIVE,
    IMPLEMENTATION_SOURCE_REGISTRY_RELATIVE,
    IMPLEMENTATION_TEST_RELATIVE,
    IMPLEMENTATION_VERIFIER_RELATIVE,
    INVOCATION_AUTHORING_SHA256,
    MATERIALIZATION_IMPLEMENTATION_SHA256,
    MATERIALIZER_SYMBOL,
    PROSPECTIVE_BUILDER_SYMBOL,
    WRITER_SYMBOL,
    FinalExecutionAcknowledgementMaterializationInvocationImplementationRecord,
    verify_final_execution_acknowledgement_materialization_invocation_implementation,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_authoring import (
    ACKNOWLEDGEMENT_MATERIALIZER_SYMBOL,
    ProspectiveFinalExecutionAcknowledgementMaterializationInvocation,
)

FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_OPERATION_AUTHORING_ID: Final = (
    "stage3b-qwake-lc4-e-final-execution-acknowledgement-materialization-"
    "invocation-operation-authoring-v1"
)
FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_OPERATION_AUTHORING_STATUS: Final = (
    "materialization_invocation_operation_contract_authored_not_implemented_"
    "not_performed_execution_closed"
)
FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_OPERATION_ID: Final = (
    "stage3b-qwake-lc4-e-final-execution-acknowledgement-materialization-"
    "invocation-operation-v1"
)
FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_OPERATION_STATUS: Final = (
    "prospective_materialization_invocation_operation_not_performed"
)
FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_OPERATION_PHRASE: Final = (
    "INVOKE_QWAKE_LC4_FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION"
)

OPERATION_AUTHORING_BASE_COMMIT: Final = "0ace9f1025100fa29ff0af7523fde17674c4852b"
INVOCATION_IMPLEMENTATION_PR_NUMBER: Final = 153
INVOCATION_IMPLEMENTATION_HEAD_COMMIT: Final = (
    "8699932246782dfee9dc06030fa0ebd25c2473b4"
)
INVOCATION_IMPLEMENTATION_PARENT_COMMIT: Final = (
    "febfba65d2f200fd2163928643eadd807a6b4d21"
)
INVOCATION_IMPLEMENTATION_MERGE_COMMIT: Final = OPERATION_AUTHORING_BASE_COMMIT
INVOCATION_IMPLEMENTATION_MERGED_AT_UTC: Final = "2026-07-31T03:55:42Z"

INVOCATION_IMPLEMENTATION_SHA256: Final = (
    "sha256:849643c7c9e71e8d2b7a109478bc6e6b6950c02f3ff2efffdd3ff010bb17519e"
)
INVOCATION_IMPLEMENTATION_FILE_SHA256: Final = (
    "sha256:09bdb9453a89404b3a1b85a80787618af1bbf493f74c0214fcd7300fbb177daa"
)
INVOCATION_IMPLEMENTATION_MERGE_RECEIPT_FILE_SHA256: Final = (
    "sha256:8eeb46e2489586c1d40387bc2052ab877b8d8a10bda059f3885411161ea1fa9e"
)
INVOCATION_IMPLEMENTATION_PACKAGE_REGISTRY_SHA256: Final = (
    "sha256:d4ce1102e52f5fd9d7e526a43a52a0fafcb90fb736aba985da3eb0ec61a54456"
)
INVOCATION_IMPLEMENTATION_SOURCE_REGISTRY_SHA256: Final = (
    "sha256:e669ed140411169e0c59e7a1d971bb17b3344466f9a333eabf32b2c6f59660a8"
)
INVOCATION_IMPLEMENTATION_MODULE_SHA256: Final = (
    "sha256:6c2c3d2e3ae943b4a2cb4dd832ce4550b99b2ac23fcb58e5dbb973e864abac82"
)
INVOCATION_IMPLEMENTATION_VERIFIER_SHA256: Final = (
    "sha256:2efd9e464d546a9d08977b4bd22bd7702f137e458b789ec22cf6113ff292d36d"
)
INVOCATION_IMPLEMENTATION_TEST_SHA256: Final = (
    "sha256:48f67a2f87d6919730b97b579f5e37e769577bae241d177b1b8872cb2c9b0355"
)
INVOCATION_IMPLEMENTATION_ADR_RU_SHA256: Final = (
    "sha256:2d9d6cc571d74ad19311a3ee39cd3015160e234189381da7123d68ad3c696882"
)
INVOCATION_IMPLEMENTATION_ADR_EN_SHA256: Final = (
    "sha256:7e394a25a7f2e356da765cb27abf435dfd7472bb0a557e9c86e9a2c08bae19bd"
)

INVOCATION_ADAPTER_SYMBOL: Final = (
    "torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_"
    "materialization_invocation.invoke_final_execution_acknowledgement_"
    "materialization"
)
INVOCATION_RECOVERY_PROBE_SYMBOL: Final = (
    "torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_"
    "materialization_invocation.probe_final_execution_acknowledgement_state"
)

PACKAGE_RELATIVE: Final = Path(
    "experiments/frozen/stage3b-qwake-lc4-e-final-execution-"
    "acknowledgement-materialization-invocation-operation-authoring-v1"
)
AUTHORING_RECORD_RELATIVE: Final = PACKAGE_RELATIVE / "authoring.json"
IMPLEMENTATION_MERGE_RECEIPT_RELATIVE: Final = (
    PACKAGE_RELATIVE / "implementation-merge-validation.json"
)
REGISTRY_RELATIVE: Final = PACKAGE_RELATIVE / "SHA256SUMS"
SOURCE_REGISTRY_RELATIVE: Final = PACKAGE_RELATIVE / "source-SHA256SUMS"
MODULE_RELATIVE: Final = Path(
    "src/torch2pc_thesis/stage3b_qwake_lc4_final_execution_acknowledgement_"
    "materialization_invocation_operation_authoring.py"
)
VERIFIER_RELATIVE: Final = Path(
    "scripts/verify_stage3b_qwake_lc4_final_execution_acknowledgement_"
    "materialization_invocation_operation_authoring.py"
)
TEST_RELATIVE: Final = Path(
    "tests/unit/test_stage3b_qwake_lc4_final_execution_acknowledgement_"
    "materialization_invocation_operation_authoring.py"
)
ADR_RU_RELATIVE: Final = Path(
    "docs/decisions/ADR-093-stage3b-qwake-lc4-e-final-execution-"
    "acknowledgement-materialization-invocation-operation-authoring.md"
)
ADR_EN_RELATIVE: Final = Path(
    "docs/decisions/ADR-093-stage3b-qwake-lc4-e-final-execution-"
    "acknowledgement-materialization-invocation-operation-authoring_EN.md"
)
FUTURE_OPERATION_IMPLEMENTATION_RELATIVE: Final = Path(
    "src/torch2pc_thesis/stage3b_qwake_lc4_final_execution_acknowledgement_"
    "materialization_invocation_operation.py"
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
        "invoke_final_execution_acknowledgement_materialization",
        "probe_final_execution_acknowledgement_state",
        "materialize_final_execution_acknowledgement",
        "persist_final_execution_acknowledgement",
        "invoke_lease_bound_host_runtime",
        "invoke_one_shot_host_runtime",
        "materialize_invocation_command",
        "persist_durable_host_outcome_receipt",
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
    "FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_OPERATION_AUTHORING_ID",
    "FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_OPERATION_PHRASE",
    "AcknowledgementMaterializationInvocationImplementationMergeValidationReceipt",
    "FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoring",
    "FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError",
    "FinalExecutionAcknowledgementMaterializationInvocationOperationContract",
    "FinalExecutionAcknowledgementMaterializationInvocationOperationGates",
    "FinalExecutionAcknowledgementMaterializationInvocationOperationSource",
    "ProspectiveFinalExecutionAcknowledgementMaterializationInvocationOperation",
    "build_frozen_materialization_invocation_operation_authoring_record",
    "build_invocation_implementation_merge_validation_receipt",
    "build_prospective_acknowledgement_materialization_invocation_operation",
    "load_final_execution_acknowledgement_materialization_invocation_operation_authoring",
    "load_invocation_implementation_merge_validation_receipt",
    "verify_final_execution_acknowledgement_materialization_invocation_operation_authoring",
]


class FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
    RuntimeError
):
    """Raised when the operation-authoring boundary fails closed."""


def _require_sha256(value: str, field_name: str) -> None:
    if not _SHA256_PATTERN.fullmatch(value):
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
            f"{field_name} is not a canonical SHA-256 identity"
        )


def _require_commit(value: str, field_name: str) -> None:
    if not _COMMIT_PATTERN.fullmatch(value):
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
            f"{field_name} is not a commit identity"
        )


def _require_identity(value: str, field_name: str) -> None:
    if not _IDENTITY_PATTERN.fullmatch(value):
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
            f"{field_name} is absent or non-canonical"
        )


def _require_utc(value: str, field_name: str) -> datetime:
    if not value.endswith("Z"):
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
            f"{field_name} is not UTC"
        )
    try:
        parsed = datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError as exc:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
            f"{field_name} is not an ISO-8601 timestamp"
        ) from exc
    if parsed.tzinfo != UTC:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
            f"{field_name} is not canonical UTC"
        )
    return parsed


@dataclass(frozen=True)
class AcknowledgementMaterializationInvocationImplementationMergeValidationReceipt:
    """Exact independent post-merge receipt for invocation implementation PR #153."""

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
    acknowledgement_absent: bool
    production_execution_boundary_closed: bool
    receipt_sha256: str

    @classmethod
    def from_mapping(
        cls, value: Mapping[str, object]
    ) -> AcknowledgementMaterializationInvocationImplementationMergeValidationReceipt:
        return cls(**cast(dict[str, Any], dict(value)))

    def semantic_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload.pop("receipt_sha256")
        return cast(dict[str, object], payload)

    def require(self) -> None:
        expected: dict[str, object] = {
            "receipt_id": (
                "stage3b-qwake-lc4-e-final-execution-acknowledgement-"
                "materialization-invocation-implementation-post-merge-validation-v1"
            ),
            "pr_number": INVOCATION_IMPLEMENTATION_PR_NUMBER,
            "head_commit": INVOCATION_IMPLEMENTATION_HEAD_COMMIT,
            "base_commit": INVOCATION_IMPLEMENTATION_PARENT_COMMIT,
            "merge_commit": INVOCATION_IMPLEMENTATION_MERGE_COMMIT,
            "merged_at_utc": INVOCATION_IMPLEMENTATION_MERGED_AT_UTC,
            "commit_count": 1,
            "file_count": 18,
            "insertions": 2076,
            "deletions": 0,
            "focused_tests_passed": 144,
            "targeted_tests_passed": 345,
            "full_tests_passed": 1392,
            "full_test_warnings": 14,
            "required_ci_checks_total": 4,
            "required_ci_checks_passed": True,
            "acknowledgement_absent": True,
            "production_execution_boundary_closed": True,
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
                    f"invocation implementation merge receipt differs: {field_name}"
                )
        _require_commit(self.head_commit, "head_commit")
        _require_commit(self.base_commit, "base_commit")
        _require_commit(self.merge_commit, "merge_commit")
        _require_utc(self.merged_at_utc, "merged_at_utc")
        _require_sha256(self.receipt_sha256, "receipt_sha256")
        if self.receipt_sha256 != sha256_object(self.semantic_payload()):
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
                "invocation implementation merge receipt semantic SHA-256 differs"
            )

    def canonical_json(self) -> str:
        self.require()
        return canonical_json(self)


@dataclass(frozen=True)
class FinalExecutionAcknowledgementMaterializationInvocationOperationSource:
    operation_authoring_base_commit: str
    invocation_implementation_id: str
    invocation_implementation_sha256: str
    invocation_implementation_file_sha256: str
    invocation_implementation_merge_receipt_file_sha256: str
    invocation_implementation_package_registry_sha256: str
    invocation_implementation_source_registry_sha256: str
    invocation_implementation_module_sha256: str
    invocation_implementation_verifier_sha256: str
    invocation_implementation_test_sha256: str
    invocation_implementation_adr_ru_sha256: str
    invocation_implementation_adr_en_sha256: str
    invocation_implementation_pr_number: int
    invocation_implementation_head_commit: str
    invocation_implementation_parent_commit: str
    invocation_implementation_merge_commit: str
    invocation_implementation_merged_at_utc: str
    invocation_authoring_sha256: str
    materialization_implementation_sha256: str
    acknowledgement_relative: str
    invocation_adapter_symbol: str
    invocation_recovery_probe_symbol: str
    acknowledgement_materializer_symbol: str
    acknowledgement_writer_symbol: str

    @classmethod
    def from_mapping(
        cls, value: Mapping[str, object]
    ) -> FinalExecutionAcknowledgementMaterializationInvocationOperationSource:
        return cls(**cast(dict[str, Any], dict(value)))

    def require(
        self,
        receipt: AcknowledgementMaterializationInvocationImplementationMergeValidationReceipt,
    ) -> None:
        receipt.require()
        if self != _build_source(receipt):
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
                "materialization invocation operation source differs"
            )


@dataclass(frozen=True)
class FinalExecutionAcknowledgementMaterializationInvocationOperationContract:
    complete_invocation_implementation_identity_required: bool
    invocation_implementation_post_merge_verification_required: bool
    prospective_operation_inputs_only: bool
    exact_operation_phrase_required: str
    operation_phrase_distinct_from_acknowledgement_phrase: bool
    explicit_operation_operator_identity_required: bool
    explicit_operation_authorized_at_utc_required: bool
    operation_authorized_after_implementation_merge_required: bool
    operation_authorized_not_before_acknowledgement_required: bool
    operation_authorized_not_after_issuance_required: bool
    exact_invocation_adapter_symbol_required: str
    exact_invocation_recovery_probe_symbol_required: str
    adapter_owned_recovery_probe_required: bool
    standalone_preprobe_forbidden: bool
    adapter_call_limit: int
    direct_materializer_call_forbidden: bool
    direct_writer_call_forbidden: bool
    production_callsite_separate: bool
    repository_adapter_callsite_forbidden: bool
    operation_implementation_separate: bool
    automatic_retry_forbidden: bool
    blind_retry_forbidden: bool
    explicit_recovery_permitted: bool
    absent_target_requires_new_explicit_authorization: bool
    valid_existing_target_treated_as_success: bool
    invalid_existing_target_fail_closed: bool
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
        cls, value: Mapping[str, object]
    ) -> FinalExecutionAcknowledgementMaterializationInvocationOperationContract:
        return cls(**cast(dict[str, Any], dict(value)))

    def require(self) -> None:
        if self != _build_contract():
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
                "materialization invocation operation contract differs"
            )


@dataclass(frozen=True)
class FinalExecutionAcknowledgementMaterializationInvocationOperationGates:
    invocation_implementation_post_merge_verified: bool
    materialization_invocation_contract_authored: bool
    materialization_invocation_implemented: bool
    materialization_invocation_operation_contract_authored: bool
    materialization_invocation_operation_implemented: bool
    materialization_invocation_operation_performed: bool
    invocation_adapter_called: bool
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
        cls, value: Mapping[str, object]
    ) -> FinalExecutionAcknowledgementMaterializationInvocationOperationGates:
        return cls(**cast(dict[str, Any], dict(value)))

    def require(self) -> None:
        if self != _build_gates():
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
                "materialization invocation operation gates differ"
            )


@dataclass(frozen=True)
class FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoring:
    schema_version: int
    authoring_id: str
    status: str
    recorded_at_utc: str
    source: FinalExecutionAcknowledgementMaterializationInvocationOperationSource
    contract: FinalExecutionAcknowledgementMaterializationInvocationOperationContract
    gates: FinalExecutionAcknowledgementMaterializationInvocationOperationGates
    next_slice: str
    post_merge_next_slice: str
    authoring_sha256: str

    @classmethod
    def from_mapping(
        cls, value: Mapping[str, object]
    ) -> FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoring:
        payload = dict(value)
        payload["source"] = FinalExecutionAcknowledgementMaterializationInvocationOperationSource.from_mapping(
            cast(Mapping[str, object], payload["source"])
        )
        payload["contract"] = FinalExecutionAcknowledgementMaterializationInvocationOperationContract.from_mapping(
            cast(Mapping[str, object], payload["contract"])
        )
        payload["gates"] = FinalExecutionAcknowledgementMaterializationInvocationOperationGates.from_mapping(
            cast(Mapping[str, object], payload["gates"])
        )
        return cls(**cast(dict[str, Any], payload))

    def semantic_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload.pop("authoring_sha256")
        return cast(dict[str, object], payload)

    def require(
        self,
        receipt: AcknowledgementMaterializationInvocationImplementationMergeValidationReceipt,
    ) -> None:
        expected: dict[str, object] = {
            "schema_version": 1,
            "authoring_id": FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_OPERATION_AUTHORING_ID,
            "status": FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_OPERATION_AUTHORING_STATUS,
            "recorded_at_utc": "2026-07-31T04:10:00Z",
            "next_slice": (
                "QW-LC4-E-final-execution-acknowledgement-materialization-"
                "invocation-operation-authoring-commit"
            ),
            "post_merge_next_slice": (
                "QW-LC4-E-final-execution-acknowledgement-materialization-"
                "invocation-operation-implementation"
            ),
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
                    f"materialization invocation operation authoring differs: {field_name}"
                )
        if _require_utc(self.recorded_at_utc, "recorded_at_utc") <= _require_utc(
            receipt.merged_at_utc, "merged_at_utc"
        ):
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
                "operation authoring timestamp is not after invocation implementation merge"
            )
        self.source.require(receipt)
        self.contract.require()
        self.gates.require()
        _require_sha256(self.authoring_sha256, "authoring_sha256")
        if self.authoring_sha256 != sha256_object(self.semantic_payload()):
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
                "materialization invocation operation authoring semantic SHA-256 differs"
            )

    def canonical_json(
        self,
        receipt: AcknowledgementMaterializationInvocationImplementationMergeValidationReceipt,
    ) -> str:
        self.require(receipt)
        return canonical_json(self)


@dataclass(frozen=True)
class ProspectiveFinalExecutionAcknowledgementMaterializationInvocationOperation:
    operation_id: str
    status: str
    operation_authoring_sha256: str
    invocation_implementation_sha256: str
    operation_phrase: str
    operation_operator_identity: str
    operation_authorized_at_utc: str
    prospective_invocation_sha256: str
    invocation: ProspectiveFinalExecutionAcknowledgementMaterializationInvocation
    acknowledgement_relative: str
    invocation_adapter_symbol: str
    invocation_recovery_probe_symbol: str
    adapter_call_limit: int
    standalone_preprobe_permitted: bool
    direct_materializer_call_permitted: bool
    direct_writer_call_permitted: bool
    automatic_retry_permitted: bool
    blind_retry_permitted: bool
    explicit_recovery_permitted: bool
    operation_performed: bool
    invocation_adapter_called: bool
    materialization_invoked: bool
    materializer_called: bool
    writer_called: bool
    final_execution_acknowledgement_issued: bool
    final_execution_acknowledged: bool
    one_shot_engineering_invocation_permitted: bool

    def require(
        self,
        authoring: FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoring,
        receipt: AcknowledgementMaterializationInvocationImplementationMergeValidationReceipt,
    ) -> None:
        authoring.require(receipt)
        _require_prospective_invocation(self.invocation)
        expected: dict[str, object] = {
            "operation_id": FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_OPERATION_ID,
            "status": FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_OPERATION_STATUS,
            "operation_authoring_sha256": authoring.authoring_sha256,
            "invocation_implementation_sha256": INVOCATION_IMPLEMENTATION_SHA256,
            "operation_phrase": FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_OPERATION_PHRASE,
            "prospective_invocation_sha256": sha256_object(self.invocation),
            "acknowledgement_relative": ACKNOWLEDGEMENT_RELATIVE.as_posix(),
            "invocation_adapter_symbol": INVOCATION_ADAPTER_SYMBOL,
            "invocation_recovery_probe_symbol": INVOCATION_RECOVERY_PROBE_SYMBOL,
            "adapter_call_limit": 1,
            "standalone_preprobe_permitted": False,
            "direct_materializer_call_permitted": False,
            "direct_writer_call_permitted": False,
            "automatic_retry_permitted": False,
            "blind_retry_permitted": False,
            "explicit_recovery_permitted": True,
            "operation_performed": False,
            "invocation_adapter_called": False,
            "materialization_invoked": False,
            "materializer_called": False,
            "writer_called": False,
            "final_execution_acknowledgement_issued": False,
            "final_execution_acknowledged": False,
            "one_shot_engineering_invocation_permitted": False,
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
                    f"prospective invocation operation differs: {field_name}"
                )
        _require_identity(self.operation_operator_identity, "operation_operator_identity")
        if self.operation_operator_identity != self.invocation.operator_identity:
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
                "operation operator differs from acknowledgement operator"
            )
        authorized = _require_utc(
            self.operation_authorized_at_utc, "operation_authorized_at_utc"
        )
        merged = _require_utc(receipt.merged_at_utc, "merged_at_utc")
        acknowledged = _require_utc(
            self.invocation.acknowledged_at_utc, "acknowledged_at_utc"
        )
        issued = _require_utc(self.invocation.issued_at_utc, "issued_at_utc")
        if authorized <= merged:
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
                "operation authorization is not after invocation implementation merge"
            )
        if authorized < acknowledged:
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
                "operation authorization is before operator acknowledgement"
            )
        if authorized > issued:
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
                "operation authorization is after acknowledgement issuance"
            )

    def canonical_json(
        self,
        authoring: FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoring,
        receipt: AcknowledgementMaterializationInvocationImplementationMergeValidationReceipt,
    ) -> str:
        self.require(authoring, receipt)
        return canonical_json(self)


def _require_prospective_invocation(
    invocation: ProspectiveFinalExecutionAcknowledgementMaterializationInvocation,
) -> None:
    expected: dict[str, object] = {
        "invocation_authoring_sha256": INVOCATION_AUTHORING_SHA256,
        "materialization_implementation_sha256": MATERIALIZATION_IMPLEMENTATION_SHA256,
        "acknowledgement_phrase": FINAL_EXECUTION_OPERATOR_ACKNOWLEDGEMENT,
        "acknowledgement_relative": ACKNOWLEDGEMENT_RELATIVE.as_posix(),
        "prospective_materialization_builder_symbol": PROSPECTIVE_BUILDER_SYMBOL,
        "acknowledgement_materializer_symbol": MATERIALIZER_SYMBOL,
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
        if getattr(invocation, field_name) != expected_value:
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
                f"prospective invocation identity differs: {field_name}"
            )
    _require_identity(invocation.operator_identity, "operator_identity")
    _require_identity(invocation.issuer_identity, "issuer_identity")
    _require_identity(invocation.materializer_identity, "materializer_identity")
    if invocation.materializer_identity != invocation.issuer_identity:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
            "materializer identity differs from issuer identity"
        )
    acknowledged = _require_utc(invocation.acknowledged_at_utc, "acknowledged_at_utc")
    issued = _require_utc(invocation.issued_at_utc, "issued_at_utc")
    materialized = _require_utc(invocation.materialized_at_utc, "materialized_at_utc")
    if acknowledged <= _require_utc(
        INVOCATION_IMPLEMENTATION_MERGED_AT_UTC, "merged_at_utc"
    ):
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
            "acknowledgement timestamp is not after invocation implementation merge"
        )
    if issued < acknowledged or materialized < issued:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
            "prospective invocation timestamps are not ordered"
        )


def build_prospective_acknowledgement_materialization_invocation_operation(
    authoring: FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoring,
    receipt: AcknowledgementMaterializationInvocationImplementationMergeValidationReceipt,
    invocation: ProspectiveFinalExecutionAcknowledgementMaterializationInvocation,
    *,
    operation_phrase: str,
    operation_operator_identity: str,
    operation_authorized_at_utc: str,
) -> ProspectiveFinalExecutionAcknowledgementMaterializationInvocationOperation:
    """Build a future operator-bound adapter operation without performing it."""

    authoring.require(receipt)
    _require_prospective_invocation(invocation)
    result = ProspectiveFinalExecutionAcknowledgementMaterializationInvocationOperation(
        operation_id=FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_OPERATION_ID,
        status=FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_OPERATION_STATUS,
        operation_authoring_sha256=authoring.authoring_sha256,
        invocation_implementation_sha256=INVOCATION_IMPLEMENTATION_SHA256,
        operation_phrase=operation_phrase,
        operation_operator_identity=operation_operator_identity,
        operation_authorized_at_utc=operation_authorized_at_utc,
        prospective_invocation_sha256=sha256_object(invocation),
        invocation=invocation,
        acknowledgement_relative=ACKNOWLEDGEMENT_RELATIVE.as_posix(),
        invocation_adapter_symbol=INVOCATION_ADAPTER_SYMBOL,
        invocation_recovery_probe_symbol=INVOCATION_RECOVERY_PROBE_SYMBOL,
        adapter_call_limit=1,
        standalone_preprobe_permitted=False,
        direct_materializer_call_permitted=False,
        direct_writer_call_permitted=False,
        automatic_retry_permitted=False,
        blind_retry_permitted=False,
        explicit_recovery_permitted=True,
        operation_performed=False,
        invocation_adapter_called=False,
        materialization_invoked=False,
        materializer_called=False,
        writer_called=False,
        final_execution_acknowledgement_issued=False,
        final_execution_acknowledged=False,
        one_shot_engineering_invocation_permitted=False,
    )
    result.require(authoring, receipt)
    return result


def load_invocation_implementation_merge_validation_receipt(
    path: Path,
) -> AcknowledgementMaterializationInvocationImplementationMergeValidationReceipt:
    receipt = AcknowledgementMaterializationInvocationImplementationMergeValidationReceipt.from_mapping(
        _load_json(path)
    )
    receipt.require()
    return receipt


def load_final_execution_acknowledgement_materialization_invocation_operation_authoring(
    path: Path,
    receipt: AcknowledgementMaterializationInvocationImplementationMergeValidationReceipt,
) -> FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoring:
    authoring = FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoring.from_mapping(
        _load_json(path)
    )
    authoring.require(receipt)
    return authoring


def verify_final_execution_acknowledgement_materialization_invocation_operation_authoring(
    project_root: Path,
) -> FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoring:
    """Verify the frozen operation-authoring package without effects."""

    root = _verified_project_root(project_root)
    package = root / PACKAGE_RELATIVE
    if not package.is_dir() or package.is_symlink():
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
            "operation-authoring package is absent or invalid"
        )
    package_files = {path.name for path in package.iterdir() if path.is_file()}
    if package_files != _EXPECTED_PACKAGE_FILES:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
            "operation-authoring package file set differs"
        )
    _verify_registry(package / "SHA256SUMS", package)
    source_registry = _verify_registry(root / SOURCE_REGISTRY_RELATIVE, root)
    if frozenset(source_registry) != _EXPECTED_SOURCE_PATHS:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
            "operation-authoring source registry path set differs"
        )
    try:
        implementation = verify_final_execution_acknowledgement_materialization_invocation_implementation(
            root
        )
    except Exception as exc:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
            str(exc)
        ) from exc
    _verify_implementation_record(implementation)
    receipt = load_invocation_implementation_merge_validation_receipt(
        root / IMPLEMENTATION_MERGE_RECEIPT_RELATIVE
    )
    authoring = load_final_execution_acknowledgement_materialization_invocation_operation_authoring(
        root / AUTHORING_RECORD_RELATIVE,
        receipt,
    )
    _verify_effect_free_authoring_ast(root)
    _require_repository_adapter_callsite_absent(root)
    _require_operation_implementation_absent(root)
    _require_production_boundary_closed(root)
    return authoring


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8", errors="strict"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
            f"frozen JSON is invalid: {path}"
        ) from exc
    if not isinstance(value, dict):
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
            f"frozen JSON is not an object: {path}"
        )
    return cast(dict[str, Any], value)


def _load_registry(path: Path) -> dict[str, str]:
    if not path.is_file() or path.is_symlink():
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
            f"frozen registry is absent or invalid: {path}"
        )
    entries: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8", errors="strict").splitlines():
        parts = raw_line.split("  ", 1)
        if len(parts) != 2 or not re.fullmatch(r"[0-9a-f]{64}", parts[0]):
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
                f"frozen registry line is invalid: {path}"
            )
        if parts[1] in entries:
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
                f"frozen registry path is duplicated: {parts[1]}"
            )
        entries[parts[1]] = parts[0]
    if not entries:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
            f"frozen registry is empty: {path}"
        )
    return entries


def _verified_project_root(project_root: Path) -> Path:
    expanded = project_root.expanduser()
    if expanded.is_symlink():
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
            "project root is symbolic"
        )
    root = expanded.resolve()
    if not root.is_dir():
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
            "project root is absent or non-directory"
        )
    return root


def _verify_registry(path: Path, base: Path) -> dict[str, str]:
    entries = _load_registry(path)
    for relative, digest in entries.items():
        target = base / relative
        if not target.is_file() or target.is_symlink():
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
                f"frozen registry target is absent or invalid: {target}"
            )
        if hashlib_sha256(target) != digest:
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
                f"frozen registry target digest differs: {target}"
            )
    return entries


def hashlib_sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes()).removeprefix("sha256:")


def _verify_implementation_record(
    implementation: FinalExecutionAcknowledgementMaterializationInvocationImplementationRecord,
) -> None:
    if implementation.implementation_id != (
        FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_IMPLEMENTATION_ID
    ):
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
            "invocation implementation ID differs"
        )
    if implementation.implementation_sha256 != INVOCATION_IMPLEMENTATION_SHA256:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
            "invocation implementation semantic identity differs"
        )
    gates = implementation.gates
    if not gates.materialization_invocation_implemented or gates.materialization_invoked:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
            "invocation implementation gate differs"
        )


def _verify_effect_free_authoring_ast(root: Path) -> None:
    for path in (root / MODULE_RELATIVE, root / VERIFIER_RELATIVE):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="strict"))
        except (OSError, UnicodeError, SyntaxError) as exc:
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
                f"operation-authoring source is invalid: {path}"
            ) from exc
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots = {alias.name.split(".", 1)[0] for alias in node.names}
                if roots & _FORBIDDEN_IMPORT_ROOTS:
                    raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
                        f"forbidden operation-authoring import: {path}"
                    )
            if (
                isinstance(node, ast.ImportFrom)
                and node.module
                and node.module.split(".", 1)[0] in _FORBIDDEN_IMPORT_ROOTS
            ):
                raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
                    f"forbidden operation-authoring import: {path}"
                )
            if not isinstance(node, ast.Call):
                continue
            called = ""
            if isinstance(node.func, ast.Name):
                called = node.func.id
            elif isinstance(node.func, ast.Attribute):
                called = node.func.attr
            if isinstance(node.func, ast.Name) and called in _FORBIDDEN_CALL_NAMES:
                raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
                    f"forbidden operation-authoring call: {path}"
                )
            if (
                isinstance(node.func, ast.Attribute)
                and called in _FORBIDDEN_CALL_ATTRIBUTES
            ):
                raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
                    f"forbidden operation-authoring effect: {path}"
                )


def _require_repository_adapter_callsite_absent(root: Path) -> None:
    target_name = "invoke_final_execution_acknowledgement_materialization"
    for path in sorted((root / "src").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8", errors="strict"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            called = ""
            if isinstance(node.func, ast.Name):
                called = node.func.id
            elif isinstance(node.func, ast.Attribute):
                called = node.func.attr
            if called == target_name:
                raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
                    f"repository invocation-adapter callsite exists: {path}"
                )


def _require_operation_implementation_absent(root: Path) -> None:
    target = root / FUTURE_OPERATION_IMPLEMENTATION_RELATIVE
    if target.exists() or target.is_symlink():
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
            "invocation operation implementation already exists"
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
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
                f"production boundary artifact exists: {relative}"
            )
    output_parent = root / ACKNOWLEDGEMENT_RELATIVE.parent
    if output_parent.is_dir():
        prefixes = (
            ".qwake-lc4-runtime-validation-v1-attempt-001.staging-",
            ".qwake-lc4-runtime-validation-v1-attempt-001.final-execution-"
            "acknowledgement.json.tmp-",
        )
        for path in output_parent.iterdir():
            if any(path.name.startswith(prefix) for prefix in prefixes):
                raise FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoringError(
                    f"production boundary staging artifact exists: {path.name}"
                )


def _build_source(
    receipt: AcknowledgementMaterializationInvocationImplementationMergeValidationReceipt,
) -> FinalExecutionAcknowledgementMaterializationInvocationOperationSource:
    receipt.require()
    return FinalExecutionAcknowledgementMaterializationInvocationOperationSource(
        operation_authoring_base_commit=OPERATION_AUTHORING_BASE_COMMIT,
        invocation_implementation_id=(
            FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_IMPLEMENTATION_ID
        ),
        invocation_implementation_sha256=INVOCATION_IMPLEMENTATION_SHA256,
        invocation_implementation_file_sha256=INVOCATION_IMPLEMENTATION_FILE_SHA256,
        invocation_implementation_merge_receipt_file_sha256=(
            INVOCATION_IMPLEMENTATION_MERGE_RECEIPT_FILE_SHA256
        ),
        invocation_implementation_package_registry_sha256=(
            INVOCATION_IMPLEMENTATION_PACKAGE_REGISTRY_SHA256
        ),
        invocation_implementation_source_registry_sha256=(
            INVOCATION_IMPLEMENTATION_SOURCE_REGISTRY_SHA256
        ),
        invocation_implementation_module_sha256=INVOCATION_IMPLEMENTATION_MODULE_SHA256,
        invocation_implementation_verifier_sha256=(
            INVOCATION_IMPLEMENTATION_VERIFIER_SHA256
        ),
        invocation_implementation_test_sha256=INVOCATION_IMPLEMENTATION_TEST_SHA256,
        invocation_implementation_adr_ru_sha256=INVOCATION_IMPLEMENTATION_ADR_RU_SHA256,
        invocation_implementation_adr_en_sha256=INVOCATION_IMPLEMENTATION_ADR_EN_SHA256,
        invocation_implementation_pr_number=receipt.pr_number,
        invocation_implementation_head_commit=receipt.head_commit,
        invocation_implementation_parent_commit=receipt.base_commit,
        invocation_implementation_merge_commit=receipt.merge_commit,
        invocation_implementation_merged_at_utc=receipt.merged_at_utc,
        invocation_authoring_sha256=INVOCATION_AUTHORING_SHA256,
        materialization_implementation_sha256=MATERIALIZATION_IMPLEMENTATION_SHA256,
        acknowledgement_relative=ACKNOWLEDGEMENT_RELATIVE.as_posix(),
        invocation_adapter_symbol=INVOCATION_ADAPTER_SYMBOL,
        invocation_recovery_probe_symbol=INVOCATION_RECOVERY_PROBE_SYMBOL,
        acknowledgement_materializer_symbol=ACKNOWLEDGEMENT_MATERIALIZER_SYMBOL,
        acknowledgement_writer_symbol=WRITER_SYMBOL,
    )


def _build_contract() -> FinalExecutionAcknowledgementMaterializationInvocationOperationContract:
    return FinalExecutionAcknowledgementMaterializationInvocationOperationContract(
        complete_invocation_implementation_identity_required=True,
        invocation_implementation_post_merge_verification_required=True,
        prospective_operation_inputs_only=True,
        exact_operation_phrase_required=(
            FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_OPERATION_PHRASE
        ),
        operation_phrase_distinct_from_acknowledgement_phrase=True,
        explicit_operation_operator_identity_required=True,
        explicit_operation_authorized_at_utc_required=True,
        operation_authorized_after_implementation_merge_required=True,
        operation_authorized_not_before_acknowledgement_required=True,
        operation_authorized_not_after_issuance_required=True,
        exact_invocation_adapter_symbol_required=INVOCATION_ADAPTER_SYMBOL,
        exact_invocation_recovery_probe_symbol_required=INVOCATION_RECOVERY_PROBE_SYMBOL,
        adapter_owned_recovery_probe_required=True,
        standalone_preprobe_forbidden=True,
        adapter_call_limit=1,
        direct_materializer_call_forbidden=True,
        direct_writer_call_forbidden=True,
        production_callsite_separate=True,
        repository_adapter_callsite_forbidden=True,
        operation_implementation_separate=True,
        automatic_retry_forbidden=True,
        blind_retry_forbidden=True,
        explicit_recovery_permitted=True,
        absent_target_requires_new_explicit_authorization=True,
        valid_existing_target_treated_as_success=True,
        invalid_existing_target_fail_closed=True,
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


def _build_gates() -> FinalExecutionAcknowledgementMaterializationInvocationOperationGates:
    return FinalExecutionAcknowledgementMaterializationInvocationOperationGates(
        invocation_implementation_post_merge_verified=True,
        materialization_invocation_contract_authored=True,
        materialization_invocation_implemented=True,
        materialization_invocation_operation_contract_authored=True,
        materialization_invocation_operation_implemented=False,
        materialization_invocation_operation_performed=False,
        invocation_adapter_called=False,
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


def build_frozen_materialization_invocation_operation_authoring_record(
    receipt: AcknowledgementMaterializationInvocationImplementationMergeValidationReceipt,
) -> FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoring:
    receipt.require()
    provisional = FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoring(
        schema_version=1,
        authoring_id=(
            FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_OPERATION_AUTHORING_ID
        ),
        status=(
            FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_OPERATION_AUTHORING_STATUS
        ),
        recorded_at_utc="2026-07-31T04:10:00Z",
        source=_build_source(receipt),
        contract=_build_contract(),
        gates=_build_gates(),
        next_slice=(
            "QW-LC4-E-final-execution-acknowledgement-materialization-"
            "invocation-operation-authoring-commit"
        ),
        post_merge_next_slice=(
            "QW-LC4-E-final-execution-acknowledgement-materialization-"
            "invocation-operation-implementation"
        ),
        authoring_sha256="sha256:" + "0" * 64,
    )
    result = replace(
        provisional,
        authoring_sha256=sha256_object(provisional.semantic_payload()),
    )
    result.require(receipt)
    return result


def build_invocation_implementation_merge_validation_receipt(
) -> AcknowledgementMaterializationInvocationImplementationMergeValidationReceipt:
    provisional = AcknowledgementMaterializationInvocationImplementationMergeValidationReceipt(
        receipt_id=(
            "stage3b-qwake-lc4-e-final-execution-acknowledgement-"
            "materialization-invocation-implementation-post-merge-validation-v1"
        ),
        pr_number=INVOCATION_IMPLEMENTATION_PR_NUMBER,
        head_commit=INVOCATION_IMPLEMENTATION_HEAD_COMMIT,
        base_commit=INVOCATION_IMPLEMENTATION_PARENT_COMMIT,
        merge_commit=INVOCATION_IMPLEMENTATION_MERGE_COMMIT,
        merged_at_utc=INVOCATION_IMPLEMENTATION_MERGED_AT_UTC,
        commit_count=1,
        file_count=18,
        insertions=2076,
        deletions=0,
        focused_tests_passed=144,
        targeted_tests_passed=345,
        full_tests_passed=1392,
        full_test_warnings=14,
        required_ci_checks_total=4,
        required_ci_checks_passed=True,
        acknowledgement_absent=True,
        production_execution_boundary_closed=True,
        receipt_sha256="sha256:" + "0" * 64,
    )
    result = replace(
        provisional,
        receipt_sha256=sha256_object(provisional.semantic_payload()),
    )
    result.require()
    return result
