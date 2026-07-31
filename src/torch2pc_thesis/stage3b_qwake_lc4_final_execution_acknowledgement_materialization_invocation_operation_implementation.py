"""Bounded library implementation of one materialization invocation operation.

The module verifies the frozen operator-bound operation and delegates exactly
once to the already verified acknowledgement-materialization invocation
adapter. It adds no production callsite and performs no operation at import or
package-verification time. Runtime effects occur only when the exported
operation function is explicitly called; tests exercise that path only inside
isolated temporary repository copies.
"""

from __future__ import annotations

import ast
import json
import re
from collections.abc import Mapping
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final, Literal, cast

from .stage3b_qwake_lc4_final_execution_acknowledgement_authoring import (
    DURABLE_HOST_OUTCOME_RELATIVE,
    EXECUTION_LEASE_V2_RELATIVE,
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
    FinalExecutionAcknowledgementMaterializationInvocationResult,
    invoke_final_execution_acknowledgement_materialization,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_authoring import (
    ADR_EN_RELATIVE as AUTHORING_ADR_EN_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_authoring import (
    ADR_RU_RELATIVE as AUTHORING_ADR_RU_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_authoring import (
    AUTHORING_RECORD_RELATIVE as OPERATION_AUTHORING_RECORD_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_authoring import (
    FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_OPERATION_AUTHORING_ID,
    FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_OPERATION_PHRASE,
    AcknowledgementMaterializationInvocationImplementationMergeValidationReceipt,
    FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoring,
    ProspectiveFinalExecutionAcknowledgementMaterializationInvocationOperation,
    load_final_execution_acknowledgement_materialization_invocation_operation_authoring,
    load_invocation_implementation_merge_validation_receipt,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_authoring import (
    IMPLEMENTATION_MERGE_RECEIPT_RELATIVE as OPERATION_AUTHORING_UPSTREAM_RECEIPT_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_authoring import (
    MODULE_RELATIVE as AUTHORING_MODULE_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_authoring import (
    PACKAGE_RELATIVE as AUTHORING_PACKAGE_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_authoring import (
    REGISTRY_RELATIVE as AUTHORING_REGISTRY_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_authoring import (
    SOURCE_REGISTRY_RELATIVE as AUTHORING_SOURCE_REGISTRY_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_authoring import (
    TEST_RELATIVE as AUTHORING_TEST_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_authoring import (
    VERIFIER_RELATIVE as AUTHORING_VERIFIER_RELATIVE,
)

FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_OPERATION_IMPLEMENTATION_ID: Final = (
    "stage3b-qwake-lc4-e-final-execution-acknowledgement-materialization-"
    "invocation-operation-implementation-v1"
)
FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_OPERATION_IMPLEMENTATION_STATUS: Final = (
    "materialization_invocation_operation_implemented_not_performed_execution_closed"
)
FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_OPERATION_RESULT_STATUS: Final = (
    "materialization_invocation_operation_performed"
)

IMPLEMENTATION_BASE_COMMIT: Final = "5ee6d2346e558be19cfdf79e8a77b0568475bf4c"
AUTHORING_PR_NUMBER: Final = 154
AUTHORING_HEAD_COMMIT: Final = "bf14d4ecced6e87f429db2c1c51b3e42161a941c"
AUTHORING_PARENT_COMMIT: Final = "0ace9f1025100fa29ff0af7523fde17674c4852b"
AUTHORING_MERGE_COMMIT: Final = IMPLEMENTATION_BASE_COMMIT
AUTHORING_MERGED_AT_UTC: Final = "2026-07-31T14:16:48Z"

OPERATION_AUTHORING_SHA256: Final = (
    "sha256:88af9e1fa190d2da34516c9e90cb40f8504183a97dac014e978a21f1127a1c5e"
)
OPERATION_AUTHORING_FILE_SHA256: Final = (
    "sha256:22cce82c224f3807adab3e1461b43305fbcd91b94e07bac4213b5f84f9e95d4a"
)
OPERATION_AUTHORING_MERGE_RECEIPT_FILE_SHA256: Final = (
    "sha256:9ef0558d4e2a1a7bf5370e7a383f5bafcbb39605ecb42d1311d04ba6318dc6a8"
)
OPERATION_AUTHORING_PACKAGE_REGISTRY_SHA256: Final = (
    "sha256:e150d89c766ca3b91e1e834f659172c561773a36743e62e015c5b5d94aa3e765"
)
OPERATION_AUTHORING_SOURCE_REGISTRY_SHA256: Final = (
    "sha256:00279278bcc88304f161b1eca0f72108e5d868d07871962ce503bb9af0ebe305"
)
OPERATION_AUTHORING_MODULE_SHA256: Final = (
    "sha256:4f4a1685e3b1f086d73982cc886bcc1b39af1a08ea4ec555afb793688c8d55eb"
)
OPERATION_AUTHORING_VERIFIER_SHA256: Final = (
    "sha256:105f733fe6a200ebcbaba04175aae9b5b3668a612a68d5f7515b70b0547bf16c"
)
OPERATION_AUTHORING_TEST_SHA256: Final = (
    "sha256:e46a9f04b8c7a9fd2f5a8d6194cc85af84a3b149c1b94ff11ec2c24c527fa05a"
)
OPERATION_AUTHORING_ADR_RU_SHA256: Final = (
    "sha256:5dd254755756515d41a8a807f4e6e7de84fdd43a30508bf4ec3e416466b0cca0"
)
OPERATION_AUTHORING_ADR_EN_SHA256: Final = (
    "sha256:7607c3b45a88d1fbe32166a958dd9359d567da27338adb54b1c19d5a6ade80a5"
)

INVOCATION_ADAPTER_SYMBOL: Final = (
    "torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_"
    "materialization_invocation.invoke_final_execution_acknowledgement_"
    "materialization"
)
OPERATION_IMPLEMENTATION_SYMBOL: Final = (
    "torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_"
    "materialization_invocation_operation_implementation.perform_final_execution_"
    "acknowledgement_materialization_invocation_operation"
)

IMPLEMENTATION_PACKAGE_RELATIVE: Final = Path(
    "experiments/frozen/stage3b-qwake-lc4-e-final-execution-"
    "acknowledgement-materialization-invocation-operation-implementation-v1"
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
    "src/torch2pc_thesis/stage3b_qwake_lc4_final_execution_acknowledgement_"
    "materialization_invocation_operation_implementation.py"
)
IMPLEMENTATION_VERIFIER_RELATIVE: Final = Path(
    "scripts/verify_stage3b_qwake_lc4_final_execution_acknowledgement_"
    "materialization_invocation_operation_implementation.py"
)
IMPLEMENTATION_TEST_RELATIVE: Final = Path(
    "tests/unit/test_stage3b_qwake_lc4_final_execution_acknowledgement_"
    "materialization_invocation_operation_implementation.py"
)
IMPLEMENTATION_ADR_RU_RELATIVE: Final = Path(
    "docs/decisions/ADR-094-stage3b-qwake-lc4-e-final-execution-"
    "acknowledgement-materialization-invocation-operation-implementation.md"
)
IMPLEMENTATION_ADR_EN_RELATIVE: Final = Path(
    "docs/decisions/ADR-094-stage3b-qwake-lc4-e-final-execution-"
    "acknowledgement-materialization-invocation-operation-implementation_EN.md"
)
FUTURE_PRODUCTION_CALLSITE_RELATIVE: Final = Path(
    "scripts/invoke_stage3b_qwake_lc4_final_execution_acknowledgement_"
    "materialization_operation.py"
)

_EXPECTED_PACKAGE_FILES: Final = frozenset(
    {"SHA256SUMS", "authoring-merge-validation.json", "implementation.json", "source-SHA256SUMS"}
)
_EXPECTED_SOURCE_PATHS: Final = frozenset(
    {
        OPERATION_AUTHORING_RECORD_RELATIVE.as_posix(),
        (AUTHORING_PACKAGE_RELATIVE / "implementation-merge-validation.json").as_posix(),
        AUTHORING_REGISTRY_RELATIVE.as_posix(),
        AUTHORING_SOURCE_REGISTRY_RELATIVE.as_posix(),
        AUTHORING_MODULE_RELATIVE.as_posix(),
        AUTHORING_VERIFIER_RELATIVE.as_posix(),
        AUTHORING_TEST_RELATIVE.as_posix(),
        AUTHORING_ADR_RU_RELATIVE.as_posix(),
        AUTHORING_ADR_EN_RELATIVE.as_posix(),
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
_FORBIDDEN_DIRECT_CALLS: Final = frozenset(
    {
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

__all__ = [
    "FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_OPERATION_IMPLEMENTATION_ID",
    "AcknowledgementMaterializationInvocationOperationAuthoringMergeValidationReceipt",
    "FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError",
    "FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationRecord",
    "FinalExecutionAcknowledgementMaterializationInvocationOperationResult",
    "build_authoring_merge_validation_receipt",
    "build_frozen_materialization_invocation_operation_implementation_record",
    "load_authoring_merge_validation_receipt",
    "load_materialization_invocation_operation_implementation_record",
    "perform_final_execution_acknowledgement_materialization_invocation_operation",
    "verify_final_execution_acknowledgement_materialization_invocation_operation_implementation",
]


class FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError(
    RuntimeError
):
    """Raised when the bounded operation implementation fails closed."""


def _require_sha256(value: str, field_name: str) -> None:
    if not _SHA256_PATTERN.fullmatch(value):
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError(
            f"{field_name} is not a canonical SHA-256 identity"
        )


def _require_commit(value: str, field_name: str) -> None:
    if not _COMMIT_PATTERN.fullmatch(value):
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError(
            f"{field_name} is not a commit identity"
        )


def _require_utc(value: str, field_name: str) -> datetime:
    if not value.endswith("Z"):
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError(
            f"{field_name} is not UTC"
        )
    try:
        parsed = datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError as exc:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError(
            f"{field_name} is not an ISO-8601 timestamp"
        ) from exc
    if parsed.tzinfo != UTC:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError(
            f"{field_name} is not canonical UTC"
        )
    return parsed


@dataclass(frozen=True)
class AcknowledgementMaterializationInvocationOperationAuthoringMergeValidationReceipt:
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
    ) -> AcknowledgementMaterializationInvocationOperationAuthoringMergeValidationReceipt:
        return cls(**cast(dict[str, Any], dict(value)))

    def semantic_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload.pop("receipt_sha256")
        return cast(dict[str, object], payload)

    def require(self) -> None:
        expected: dict[str, object] = {
            "receipt_id": (
                "stage3b-qwake-lc4-e-final-execution-acknowledgement-"
                "materialization-invocation-operation-authoring-post-merge-validation-v1"
            ),
            "pr_number": AUTHORING_PR_NUMBER,
            "head_commit": AUTHORING_HEAD_COMMIT,
            "base_commit": AUTHORING_PARENT_COMMIT,
            "merge_commit": AUTHORING_MERGE_COMMIT,
            "merged_at_utc": AUTHORING_MERGED_AT_UTC,
            "commit_count": 1,
            "file_count": 18,
            "insertions": 1878,
            "deletions": 0,
            "focused_tests_passed": 162,
            "targeted_tests_passed": 363,
            "full_tests_passed": 1410,
            "full_test_warnings": 14,
            "required_ci_checks_total": 4,
            "required_ci_checks_passed": True,
            "acknowledgement_absent": True,
            "production_execution_boundary_closed": True,
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError(
                    f"operation authoring merge receipt differs: {field_name}"
                )
        _require_commit(self.head_commit, "head_commit")
        _require_commit(self.base_commit, "base_commit")
        _require_commit(self.merge_commit, "merge_commit")
        _require_utc(self.merged_at_utc, "merged_at_utc")
        _require_sha256(self.receipt_sha256, "receipt_sha256")
        if self.receipt_sha256 != sha256_object(self.semantic_payload()):
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError(
                "operation authoring merge receipt semantic SHA-256 differs"
            )


@dataclass(frozen=True)
class FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationSource:
    implementation_base_commit: str
    operation_authoring_id: str
    operation_authoring_sha256: str
    operation_authoring_file_sha256: str
    operation_authoring_merge_receipt_file_sha256: str
    operation_authoring_package_registry_sha256: str
    operation_authoring_source_registry_sha256: str
    operation_authoring_module_sha256: str
    operation_authoring_verifier_sha256: str
    operation_authoring_test_sha256: str
    operation_authoring_adr_ru_sha256: str
    operation_authoring_adr_en_sha256: str
    operation_authoring_pr_number: int
    operation_authoring_head_commit: str
    operation_authoring_parent_commit: str
    operation_authoring_merge_commit: str
    operation_authoring_merged_at_utc: str
    invocation_adapter_symbol: str
    operation_implementation_symbol: str
    acknowledgement_relative: str

    @classmethod
    def from_mapping(
        cls, value: Mapping[str, object]
    ) -> FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationSource:
        return cls(**cast(dict[str, Any], dict(value)))

    def require(
        self,
        receipt: AcknowledgementMaterializationInvocationOperationAuthoringMergeValidationReceipt,
    ) -> None:
        receipt.require()
        if self != _build_source(receipt):
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError(
                "operation implementation source differs"
            )


@dataclass(frozen=True)
class FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationContract:
    complete_operation_authoring_identity_verified: bool
    operation_authoring_post_merge_verification_required: bool
    exact_prospective_operation_validation_required: bool
    exact_invocation_adapter_delegate_required: bool
    adapter_call_limit: int
    standalone_preprobe_forbidden: bool
    direct_materializer_call_forbidden: bool
    direct_writer_call_forbidden: bool
    adapter_result_validation_required: bool
    adapter_failure_propagated_without_retry: bool
    automatic_retry_forbidden: bool
    blind_retry_forbidden: bool
    valid_existing_target_treated_as_success: bool
    invalid_existing_target_fail_closed: bool
    production_callsite_separate: bool
    repository_production_callsite_forbidden: bool
    test_effects_isolated_only: bool
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
    ) -> FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationContract:
        return cls(**cast(dict[str, Any], dict(value)))

    def require(self) -> None:
        if self != _build_contract():
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError(
                "operation implementation contract differs"
            )


@dataclass(frozen=True)
class FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationGates:
    operation_authoring_post_merge_verified: bool
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
    ) -> FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationGates:
        return cls(**cast(dict[str, Any], dict(value)))

    def require(self) -> None:
        if self != _build_gates():
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError(
                "operation implementation gates differ"
            )


@dataclass(frozen=True)
class FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationRecord:
    schema_version: int
    implementation_id: str
    status: str
    recorded_at_utc: str
    source: FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationSource
    contract: FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationContract
    gates: FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationGates
    next_slice: str
    post_merge_next_slice: str
    implementation_sha256: str

    @classmethod
    def from_mapping(
        cls, value: Mapping[str, object]
    ) -> FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationRecord:
        payload = dict(value)
        payload["source"] = FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationSource.from_mapping(
            cast(Mapping[str, object], payload["source"])
        )
        payload["contract"] = FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationContract.from_mapping(
            cast(Mapping[str, object], payload["contract"])
        )
        payload["gates"] = FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationGates.from_mapping(
            cast(Mapping[str, object], payload["gates"])
        )
        return cls(**cast(dict[str, Any], payload))

    def semantic_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload.pop("implementation_sha256")
        return cast(dict[str, object], payload)

    def require(
        self,
        receipt: AcknowledgementMaterializationInvocationOperationAuthoringMergeValidationReceipt,
    ) -> None:
        expected: dict[str, object] = {
            "schema_version": 1,
            "implementation_id": FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_OPERATION_IMPLEMENTATION_ID,
            "status": FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_OPERATION_IMPLEMENTATION_STATUS,
            "recorded_at_utc": "2026-07-31T14:30:00Z",
            "next_slice": (
                "QW-LC4-E-final-execution-acknowledgement-materialization-"
                "invocation-operation-implementation-commit"
            ),
            "post_merge_next_slice": (
                "QW-LC4-E-final-execution-acknowledgement-materialization-"
                "invocation-operation-callsite-authoring"
            ),
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError(
                    f"operation implementation record differs: {field_name}"
                )
        if _require_utc(self.recorded_at_utc, "recorded_at_utc") <= _require_utc(
            receipt.merged_at_utc, "merged_at_utc"
        ):
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError(
                "operation implementation timestamp is not after authoring merge"
            )
        self.source.require(receipt)
        self.contract.require()
        self.gates.require()
        _require_sha256(self.implementation_sha256, "implementation_sha256")
        if self.implementation_sha256 != sha256_object(self.semantic_payload()):
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError(
                "operation implementation semantic SHA-256 differs"
            )


@dataclass(frozen=True)
class FinalExecutionAcknowledgementMaterializationInvocationOperationResult:
    operation_id: str
    operation_authoring_sha256: str
    operation_phrase: str
    operation_operator_identity: str
    operation_authorized_at_utc: str
    prospective_invocation_sha256: str
    outcome: Literal["materialized", "valid_existing"]
    invocation_result: FinalExecutionAcknowledgementMaterializationInvocationResult
    operation_performed: bool
    invocation_adapter_called: bool
    adapter_call_count: int
    standalone_preprobe_performed: bool
    direct_materializer_call_performed: bool
    direct_writer_call_performed: bool
    automatic_retry_performed: bool
    blind_retry_performed: bool
    materialization_invoked: bool
    materializer_called: bool
    writer_called: bool
    final_execution_acknowledgement_issued: bool
    final_execution_acknowledged: bool
    one_shot_engineering_invocation_permitted: bool
    execution_lease_materialized: bool
    durable_host_outcome_present: bool
    authorization_consumed: bool

    def require(
        self,
        operation: ProspectiveFinalExecutionAcknowledgementMaterializationInvocationOperation,
        authoring: FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoring,
        authoring_receipt: AcknowledgementMaterializationInvocationImplementationMergeValidationReceipt,
    ) -> None:
        operation.require(authoring, authoring_receipt)
        self.invocation_result.probe.require()
        expected: dict[str, object] = {
            "operation_id": operation.operation_id,
            "operation_authoring_sha256": operation.operation_authoring_sha256,
            "operation_phrase": FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_OPERATION_PHRASE,
            "operation_operator_identity": operation.operation_operator_identity,
            "operation_authorized_at_utc": operation.operation_authorized_at_utc,
            "prospective_invocation_sha256": operation.prospective_invocation_sha256,
            "outcome": self.invocation_result.outcome,
            "operation_performed": True,
            "invocation_adapter_called": True,
            "adapter_call_count": 1,
            "standalone_preprobe_performed": False,
            "direct_materializer_call_performed": False,
            "direct_writer_call_performed": False,
            "automatic_retry_performed": False,
            "blind_retry_performed": False,
            "materialization_invoked": self.invocation_result.materialization_invoked,
            "materializer_called": self.invocation_result.materializer_called,
            "writer_called": self.invocation_result.writer_called,
            "final_execution_acknowledgement_issued": True,
            "final_execution_acknowledged": True,
            "one_shot_engineering_invocation_permitted": False,
            "execution_lease_materialized": False,
            "durable_host_outcome_present": False,
            "authorization_consumed": False,
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError(
                    f"operation result differs: {field_name}"
                )
        if self.invocation_result.invocation_id != operation.invocation.invocation_id:
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError(
                "operation result invocation identity differs"
            )
        if self.invocation_result.invocation_authoring_sha256 != (
            operation.invocation.invocation_authoring_sha256
        ):
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError(
                "operation result invocation authoring identity differs"
            )
        if self.invocation_result.automatic_retry_performed:
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError(
                "operation result contains automatic retry"
            )
        if self.invocation_result.blind_retry_performed:
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError(
                "operation result contains blind retry"
            )


_invoke_once = invoke_final_execution_acknowledgement_materialization


def perform_final_execution_acknowledgement_materialization_invocation_operation(
    project_root: Path,
    operation: ProspectiveFinalExecutionAcknowledgementMaterializationInvocationOperation,
) -> FinalExecutionAcknowledgementMaterializationInvocationOperationResult:
    """Validate one operator operation and delegate exactly once to the adapter."""

    root = _verified_project_root(project_root)
    _, authoring_receipt, authoring = _verify_implementation_freeze(root)
    try:
        operation.require(authoring, authoring_receipt)
    except Exception as exc:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError(
            str(exc)
        ) from exc
    try:
        invocation_result = _invoke_once(root, operation.invocation)
    except Exception as exc:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError(
            str(exc)
        ) from exc
    result = FinalExecutionAcknowledgementMaterializationInvocationOperationResult(
        operation_id=operation.operation_id,
        operation_authoring_sha256=operation.operation_authoring_sha256,
        operation_phrase=operation.operation_phrase,
        operation_operator_identity=operation.operation_operator_identity,
        operation_authorized_at_utc=operation.operation_authorized_at_utc,
        prospective_invocation_sha256=operation.prospective_invocation_sha256,
        outcome=invocation_result.outcome,
        invocation_result=invocation_result,
        operation_performed=True,
        invocation_adapter_called=True,
        adapter_call_count=1,
        standalone_preprobe_performed=False,
        direct_materializer_call_performed=False,
        direct_writer_call_performed=False,
        automatic_retry_performed=False,
        blind_retry_performed=False,
        materialization_invoked=invocation_result.materialization_invoked,
        materializer_called=invocation_result.materializer_called,
        writer_called=invocation_result.writer_called,
        final_execution_acknowledgement_issued=True,
        final_execution_acknowledged=True,
        one_shot_engineering_invocation_permitted=False,
        execution_lease_materialized=False,
        durable_host_outcome_present=False,
        authorization_consumed=False,
    )
    result.require(operation, authoring, authoring_receipt)
    return result


def build_authoring_merge_validation_receipt(
) -> AcknowledgementMaterializationInvocationOperationAuthoringMergeValidationReceipt:
    provisional = AcknowledgementMaterializationInvocationOperationAuthoringMergeValidationReceipt(
        receipt_id=(
            "stage3b-qwake-lc4-e-final-execution-acknowledgement-"
            "materialization-invocation-operation-authoring-post-merge-validation-v1"
        ),
        pr_number=AUTHORING_PR_NUMBER,
        head_commit=AUTHORING_HEAD_COMMIT,
        base_commit=AUTHORING_PARENT_COMMIT,
        merge_commit=AUTHORING_MERGE_COMMIT,
        merged_at_utc=AUTHORING_MERGED_AT_UTC,
        commit_count=1,
        file_count=18,
        insertions=1878,
        deletions=0,
        focused_tests_passed=162,
        targeted_tests_passed=363,
        full_tests_passed=1410,
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


def _build_source(
    receipt: AcknowledgementMaterializationInvocationOperationAuthoringMergeValidationReceipt,
) -> FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationSource:
    receipt.require()
    return FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationSource(
        implementation_base_commit=IMPLEMENTATION_BASE_COMMIT,
        operation_authoring_id=(
            FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_OPERATION_AUTHORING_ID
        ),
        operation_authoring_sha256=OPERATION_AUTHORING_SHA256,
        operation_authoring_file_sha256=OPERATION_AUTHORING_FILE_SHA256,
        operation_authoring_merge_receipt_file_sha256=(
            OPERATION_AUTHORING_MERGE_RECEIPT_FILE_SHA256
        ),
        operation_authoring_package_registry_sha256=(
            OPERATION_AUTHORING_PACKAGE_REGISTRY_SHA256
        ),
        operation_authoring_source_registry_sha256=(
            OPERATION_AUTHORING_SOURCE_REGISTRY_SHA256
        ),
        operation_authoring_module_sha256=OPERATION_AUTHORING_MODULE_SHA256,
        operation_authoring_verifier_sha256=OPERATION_AUTHORING_VERIFIER_SHA256,
        operation_authoring_test_sha256=OPERATION_AUTHORING_TEST_SHA256,
        operation_authoring_adr_ru_sha256=OPERATION_AUTHORING_ADR_RU_SHA256,
        operation_authoring_adr_en_sha256=OPERATION_AUTHORING_ADR_EN_SHA256,
        operation_authoring_pr_number=receipt.pr_number,
        operation_authoring_head_commit=receipt.head_commit,
        operation_authoring_parent_commit=receipt.base_commit,
        operation_authoring_merge_commit=receipt.merge_commit,
        operation_authoring_merged_at_utc=receipt.merged_at_utc,
        invocation_adapter_symbol=INVOCATION_ADAPTER_SYMBOL,
        operation_implementation_symbol=OPERATION_IMPLEMENTATION_SYMBOL,
        acknowledgement_relative=ACKNOWLEDGEMENT_RELATIVE.as_posix(),
    )


def _build_contract(
) -> FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationContract:
    return FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationContract(
        complete_operation_authoring_identity_verified=True,
        operation_authoring_post_merge_verification_required=True,
        exact_prospective_operation_validation_required=True,
        exact_invocation_adapter_delegate_required=True,
        adapter_call_limit=1,
        standalone_preprobe_forbidden=True,
        direct_materializer_call_forbidden=True,
        direct_writer_call_forbidden=True,
        adapter_result_validation_required=True,
        adapter_failure_propagated_without_retry=True,
        automatic_retry_forbidden=True,
        blind_retry_forbidden=True,
        valid_existing_target_treated_as_success=True,
        invalid_existing_target_fail_closed=True,
        production_callsite_separate=True,
        repository_production_callsite_forbidden=True,
        test_effects_isolated_only=True,
        subprocess_forbidden=True,
        docker_forbidden=True,
        image_inspection_forbidden=True,
        command_materialization_forbidden=True,
        lease_materialization_forbidden=True,
        durable_outcome_persistence_forbidden=True,
        authorization_consumption_forbidden=True,
        local_compute_forbidden=True,
    )


def _build_gates(
) -> FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationGates:
    return FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationGates(
        operation_authoring_post_merge_verified=True,
        materialization_invocation_operation_contract_authored=True,
        materialization_invocation_operation_implemented=True,
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


def build_frozen_materialization_invocation_operation_implementation_record(
    receipt: AcknowledgementMaterializationInvocationOperationAuthoringMergeValidationReceipt,
) -> FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationRecord:
    receipt.require()
    provisional = FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationRecord(
        schema_version=1,
        implementation_id=(
            FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_OPERATION_IMPLEMENTATION_ID
        ),
        status=(
            FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_OPERATION_IMPLEMENTATION_STATUS
        ),
        recorded_at_utc="2026-07-31T14:30:00Z",
        source=_build_source(receipt),
        contract=_build_contract(),
        gates=_build_gates(),
        next_slice=(
            "QW-LC4-E-final-execution-acknowledgement-materialization-"
            "invocation-operation-implementation-commit"
        ),
        post_merge_next_slice=(
            "QW-LC4-E-final-execution-acknowledgement-materialization-"
            "invocation-operation-callsite-authoring"
        ),
        implementation_sha256="sha256:" + "0" * 64,
    )
    result = replace(
        provisional,
        implementation_sha256=sha256_object(provisional.semantic_payload()),
    )
    result.require(receipt)
    return result


def load_authoring_merge_validation_receipt(
    path: Path,
) -> AcknowledgementMaterializationInvocationOperationAuthoringMergeValidationReceipt:
    result = AcknowledgementMaterializationInvocationOperationAuthoringMergeValidationReceipt.from_mapping(
        _load_json(path)
    )
    result.require()
    return result


def load_materialization_invocation_operation_implementation_record(
    path: Path,
    receipt: AcknowledgementMaterializationInvocationOperationAuthoringMergeValidationReceipt,
) -> FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationRecord:
    result = FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationRecord.from_mapping(
        _load_json(path)
    )
    result.require(receipt)
    return result


def verify_final_execution_acknowledgement_materialization_invocation_operation_implementation(
    project_root: Path,
) -> FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationRecord:
    root = _verified_project_root(project_root)
    implementation, _, _ = _verify_implementation_freeze(root)
    _verify_operation_implementation_ast(root)
    _require_repository_production_callsite_absent(root)
    _require_production_boundary_closed(root)
    return implementation


def _verify_implementation_freeze(
    root: Path,
) -> tuple[
    FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationRecord,
    AcknowledgementMaterializationInvocationImplementationMergeValidationReceipt,
    FinalExecutionAcknowledgementMaterializationInvocationOperationAuthoring,
]:
    package = root / IMPLEMENTATION_PACKAGE_RELATIVE
    if not package.is_dir() or package.is_symlink():
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError(
            "operation implementation package is absent or invalid"
        )
    if {path.name for path in package.iterdir()} != _EXPECTED_PACKAGE_FILES:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError(
            "operation implementation package file set differs"
        )
    _verify_registry(root / IMPLEMENTATION_REGISTRY_RELATIVE, package)
    source_registry = _verify_registry(
        root / IMPLEMENTATION_SOURCE_REGISTRY_RELATIVE, root
    )
    if frozenset(source_registry) != _EXPECTED_SOURCE_PATHS:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError(
            "operation implementation source registry path set differs"
        )
    authoring_merge_receipt = load_authoring_merge_validation_receipt(
        root / AUTHORING_MERGE_RECEIPT_RELATIVE
    )
    implementation = load_materialization_invocation_operation_implementation_record(
        root / IMPLEMENTATION_RECORD_RELATIVE,
        authoring_merge_receipt,
    )
    upstream_authoring_receipt = load_invocation_implementation_merge_validation_receipt(
        root / OPERATION_AUTHORING_UPSTREAM_RECEIPT_RELATIVE
    )
    authoring = load_final_execution_acknowledgement_materialization_invocation_operation_authoring(
        root / OPERATION_AUTHORING_RECORD_RELATIVE,
        upstream_authoring_receipt,
    )
    return implementation, upstream_authoring_receipt, authoring


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError(
            f"JSON file is absent or invalid: {path}"
        )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError(
            f"JSON file is invalid: {path}"
        ) from exc
    if not isinstance(payload, dict):
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError(
            f"JSON root is not an object: {path}"
        )
    return cast(dict[str, Any], payload)


def _load_registry(path: Path) -> dict[str, str]:
    if not path.is_file() or path.is_symlink():
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError(
            f"checksum registry is absent or invalid: {path}"
        )
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        try:
            digest, relative = line.split("  ", 1)
        except ValueError as exc:
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError(
                f"checksum registry line is invalid: {path}"
            ) from exc
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError(
                f"checksum registry digest is invalid: {path}"
            )
        if not relative or relative in result:
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError(
                f"checksum registry path is invalid: {path}"
            )
        result[relative] = digest
    return result


def _verified_project_root(project_root: Path) -> Path:
    expanded = project_root.expanduser()
    if expanded.is_symlink():
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError(
            "project root is symbolic"
        )
    resolved = expanded.resolve(strict=True)
    if not resolved.is_dir():
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError(
            "project root is not a directory"
        )
    return resolved


def _verify_registry(path: Path, base: Path) -> dict[str, str]:
    result = _load_registry(path)
    for relative, expected in result.items():
        candidate = base / relative
        if not candidate.is_file() or candidate.is_symlink():
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError(
                f"checksum target is absent or invalid: {candidate}"
            )
        observed = sha256_bytes(candidate.read_bytes()).removeprefix("sha256:")
        if observed != expected:
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError(
                f"checksum target differs: {candidate}"
            )
    return result


def _verify_operation_implementation_ast(root: Path) -> None:
    path = root / IMPLEMENTATION_MODULE_RELATIVE
    tree = ast.parse(path.read_text(encoding="utf-8"))
    exported_function_count = 0
    adapter_delegate_calls = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Import | ast.ImportFrom):
            names: list[str]
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            else:
                names = [node.module or ""]
            for name in names:
                if name.split(".", 1)[0] in _FORBIDDEN_IMPORT_ROOTS:
                    raise FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError(
                        f"forbidden operation implementation import: {path}"
                    )
        if isinstance(node, ast.FunctionDef) and node.name == (
            "perform_final_execution_acknowledgement_materialization_invocation_operation"
        ):
            exported_function_count += 1
        if isinstance(node, ast.Call):
            call_name = ""
            if isinstance(node.func, ast.Name):
                call_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                call_name = node.func.attr
            adapter_delegate_calls += int(call_name == "_invoke_once")
            if call_name in _FORBIDDEN_DIRECT_CALLS:
                raise FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError(
                    f"forbidden direct operation implementation call: {call_name}"
                )
    if exported_function_count != 1:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError(
            "operation implementation function count differs"
        )
    if adapter_delegate_calls != 1:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError(
            "operation implementation adapter delegation count differs"
        )


def _require_repository_production_callsite_absent(root: Path) -> None:
    if (root / FUTURE_PRODUCTION_CALLSITE_RELATIVE).exists():
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError(
            "future production callsite already exists"
        )
    symbol = "perform_final_execution_acknowledgement_materialization_invocation_operation"
    allowed = {
        IMPLEMENTATION_MODULE_RELATIVE,
        IMPLEMENTATION_VERIFIER_RELATIVE,
        IMPLEMENTATION_TEST_RELATIVE,
    }
    for base in (root / "src", root / "scripts"):
        for path in base.rglob("*.py"):
            relative = path.relative_to(root)
            if relative in allowed:
                continue
            if symbol in path.read_text(encoding="utf-8", errors="strict"):
                raise FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError(
                    f"repository production callsite is present: {relative}"
                )


def _require_production_boundary_closed(root: Path) -> None:
    for relative in (
        ACKNOWLEDGEMENT_RELATIVE,
        LEGACY_EXECUTION_LEASE_RELATIVE,
        EXECUTION_LEASE_V2_RELATIVE,
        DURABLE_HOST_OUTCOME_RELATIVE,
    ):
        candidate = root / relative
        if candidate.exists() or candidate.is_symlink():
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationImplementationError(
                f"production boundary is open: {relative}"
            )
