"""Freeze one unconsumed authorization for future production-callsite execution.

The module verifies the merged execution-authoring contract, builds one exact
canonical prospective operation and binds it to a single-use authorization.
It does not execute the production callsite, perform the operation, consume
authorization, invoke lower layers, or create runtime evidence.
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
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_authoring import (
    AUTHORING_RECORD_RELATIVE as INVOCATION_AUTHORING_RECORD_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_authoring import (
    IMPLEMENTATION_MERGE_RECEIPT_RELATIVE as INVOCATION_AUTHORING_RECEIPT_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_authoring import (
    build_prospective_acknowledgement_materialization_invocation,
    load_final_execution_acknowledgement_materialization_invocation_authoring,
    load_materialization_implementation_merge_validation_receipt,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_authoring import (
    AUTHORING_RECORD_RELATIVE as OPERATION_AUTHORING_RECORD_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_authoring import (
    FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_OPERATION_PHRASE,
    ProspectiveFinalExecutionAcknowledgementMaterializationInvocationOperation,
    build_prospective_acknowledgement_materialization_invocation_operation,
    load_final_execution_acknowledgement_materialization_invocation_operation_authoring,
    load_invocation_implementation_merge_validation_receipt,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_authoring import (
    IMPLEMENTATION_MERGE_RECEIPT_RELATIVE as OPERATION_AUTHORING_RECEIPT_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authoring import (
    ADR_EN_RELATIVE as EXECUTION_AUTHORING_ADR_EN_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authoring import (
    ADR_RU_RELATIVE as EXECUTION_AUTHORING_ADR_RU_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authoring import (
    AUTHORING_RECORD_RELATIVE as EXECUTION_AUTHORING_RECORD_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authoring import (
    CALLSITE_EXECUTION_AUTHORING_ID,
    CALLSITE_EXECUTION_PHRASE,
    load_callsite_implementation_merge_validation_receipt,
    load_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authoring,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authoring import (
    IMPLEMENTATION_MERGE_RECEIPT_RELATIVE as EXECUTION_AUTHORING_UPSTREAM_RECEIPT_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authoring import (
    MODULE_RELATIVE as EXECUTION_AUTHORING_MODULE_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authoring import (
    REGISTRY_RELATIVE as EXECUTION_AUTHORING_REGISTRY_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authoring import (
    SOURCE_REGISTRY_RELATIVE as EXECUTION_AUTHORING_SOURCE_REGISTRY_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authoring import (
    TEST_RELATIVE as EXECUTION_AUTHORING_TEST_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authoring import (
    VERIFIER_RELATIVE as EXECUTION_AUTHORING_VERIFIER_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_callsite_implementation import (
    OPERATION_JSON_OPTION,
    PRODUCTION_CALLSITE_RELATIVE,
    PRODUCTION_CALLSITE_SYMBOL,
    PROJECT_ROOT_OPTION,
    load_canonical_prospective_operation,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_implementation import (
    OPERATION_IMPLEMENTATION_SYMBOL,
)

EXECUTION_AUTHORIZATION_ID: Final = (
    "stage3b-qwake-lc4-e-final-execution-acknowledgement-materialization-"
    "invocation-operation-callsite-execution-authorization-v1"
)
EXECUTION_AUTHORIZATION_STATUS: Final = (
    "execution_authorization_issued_merge_required_not_consumed_"
    "callsite_not_executed"
)
EXECUTION_AUTHORIZATION_PHRASE: Final = (
    "AUTHORIZE_QWAKE_LC4_FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_"
    "OPERATION_CALLSITE"
)
EXECUTION_AUTHORIZATION_RECORDED_AT_UTC: Final = "2026-08-02T15:55:00Z"
EXECUTION_OPERATOR_IDENTITY: Final = "dzmitry-prychyna"
ACKNOWLEDGED_AT_UTC: Final = "2026-08-02T15:50:00Z"
OPERATION_AUTHORIZED_AT_UTC: Final = "2026-08-02T15:51:00Z"
ISSUED_AT_UTC: Final = "2026-08-02T15:52:00Z"
MATERIALIZED_AT_UTC: Final = "2026-08-02T15:53:00Z"
AUTHORIZATION_ISSUED_AT_UTC: Final = "2026-08-02T15:54:00Z"

EXECUTION_AUTHORIZATION_BASE_COMMIT: Final = (
    "75936adac9ee100f9538f5af13a8ce312642ee0b"
)
EXECUTION_AUTHORING_PR_NUMBER: Final = 164
EXECUTION_AUTHORING_HEAD_COMMIT: Final = (
    "4233ea7a9abd73d2476b1e0b333211bc4e0891bc"
)
EXECUTION_AUTHORING_ORIGINAL_BASE_COMMIT: Final = (
    "78129528d05e8268b4e40fdf708fd9d2c8e3ab29"
)
EXECUTION_AUTHORING_ACTUAL_FIRST_PARENT_COMMIT: Final = (
    EXECUTION_AUTHORING_ORIGINAL_BASE_COMMIT
)
EXECUTION_AUTHORING_MERGE_COMMIT: Final = EXECUTION_AUTHORIZATION_BASE_COMMIT
EXECUTION_AUTHORING_MERGE_BASE_COMMIT: Final = (
    EXECUTION_AUTHORING_ORIGINAL_BASE_COMMIT
)
EXECUTION_AUTHORING_MERGED_AT_UTC: Final = "2026-08-02T14:10:53Z"
EXECUTION_AUTHORING_MERGE_TREE: Final = (
    "325b86676247ad28a1276b260eb553e2425cd6e8"
)
EXECUTION_AUTHORING_SHA256: Final = (
    "sha256:f9f966691b006166f57015df6d9e1e952c798a84dc563d1d8a82190bda10ad38"
)
EXECUTION_AUTHORING_FILE_SHA256: Final = (
    "sha256:14cff4df3b3b3afe329c4cacadd46a1be738830049b6667de7adf57500c4f528"
)
EXECUTION_AUTHORING_UPSTREAM_RECEIPT_FILE_SHA256: Final = (
    "sha256:4c5e0026cbc7f14f809acbbb0be16260aab2d101bad2366538d392144e01de1e"
)
EXECUTION_AUTHORING_PACKAGE_REGISTRY_SHA256: Final = (
    "sha256:05ce28a23f8a5cd74eb62dca3e990e30bdf3589fd584e706a8a6fa1cf40041a0"
)
EXECUTION_AUTHORING_SOURCE_REGISTRY_SHA256: Final = (
    "sha256:fce79dbc6e03ee8d7ca9d9b26c09624834b39a60a0745a0dea55125067588ed2"
)
EXECUTION_AUTHORING_MODULE_SHA256: Final = (
    "sha256:c38d4a908a6fa4146ff7010ddc7207cebd1e6bb0beca8215076a235d2c9b8f2a"
)
EXECUTION_AUTHORING_VERIFIER_SHA256: Final = (
    "sha256:4a1627844a008deeeb9269736b1c948371db98fdec5b242e506dc54ac5dd02bf"
)
EXECUTION_AUTHORING_TEST_SHA256: Final = (
    "sha256:630cbabf2516fa8754729848697a87dea39ce40e89f6b7de802765a3fc9eaeba"
)
EXECUTION_AUTHORING_ADR_RU_SHA256: Final = (
    "sha256:dab2a50b487604ccb91cd43e63e4fb52c7a9cff8bb74b4ea77e909d08f323296"
)
EXECUTION_AUTHORING_ADR_EN_SHA256: Final = (
    "sha256:76316cb171b93503caa326f8031d53c2af4131dece20b5c7be90b2119c98f6fa"
)
PRODUCTION_CALLSITE_SHA256: Final = (
    "sha256:8915c208c69ba6595cd3efd4d85b471989402de96dfdd0d877e0c96c1c145703"
)
TORCH2PC_COMMIT: Final = "b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4"

PACKAGE_RELATIVE: Final = Path(
    "experiments/frozen/stage3b-qwake-lc4-e-final-execution-"
    "acknowledgement-materialization-invocation-operation-callsite-execution-"
    "authorization-v1"
)
AUTHORIZATION_RELATIVE: Final = PACKAGE_RELATIVE / "authorization.json"
OPERATION_JSON_RELATIVE: Final = PACKAGE_RELATIVE / "operation.json"
EXECUTION_AUTHORING_MERGE_RECEIPT_RELATIVE: Final = (
    PACKAGE_RELATIVE / "execution-authoring-merge-validation.json"
)
REGISTRY_RELATIVE: Final = PACKAGE_RELATIVE / "SHA256SUMS"
SOURCE_REGISTRY_RELATIVE: Final = PACKAGE_RELATIVE / "source-SHA256SUMS"
MODULE_RELATIVE: Final = Path(
    "src/torch2pc_thesis/stage3b_qwake_lc4_final_execution_acknowledgement_"
    "materialization_invocation_operation_callsite_execution_authorization.py"
)
VERIFIER_RELATIVE: Final = Path(
    "scripts/verify_stage3b_qwake_lc4_final_execution_acknowledgement_"
    "materialization_invocation_operation_callsite_execution_authorization.py"
)
TEST_RELATIVE: Final = Path(
    "tests/unit/test_stage3b_qwake_lc4_final_execution_acknowledgement_"
    "materialization_invocation_operation_callsite_execution_authorization.py"
)
ADR_RU_RELATIVE: Final = Path(
    "docs/decisions/ADR-098-stage3b-qwake-lc4-e-final-execution-"
    "acknowledgement-materialization-invocation-operation-callsite-execution-"
    "authorization.md"
)
ADR_EN_RELATIVE: Final = Path(
    "docs/decisions/ADR-098-stage3b-qwake-lc4-e-final-execution-"
    "acknowledgement-materialization-invocation-operation-callsite-execution-"
    "authorization_EN.md"
)

EXACT_ARGV_TEMPLATE_JSON: Final = canonical_json(
    [
        "python",
        PRODUCTION_CALLSITE_RELATIVE.as_posix(),
        PROJECT_ROOT_OPTION,
        "<VERIFIED_PROJECT_ROOT>",
        OPERATION_JSON_OPTION,
        OPERATION_JSON_RELATIVE.as_posix(),
    ]
).rstrip("\n")

_EXPECTED_PACKAGE_FILES: Final = frozenset(
    {
        "SHA256SUMS",
        "authorization.json",
        "execution-authoring-merge-validation.json",
        "operation.json",
        "source-SHA256SUMS",
    }
)
_EXPECTED_SOURCE_PATHS: Final = frozenset(
    {
        EXECUTION_AUTHORING_RECORD_RELATIVE.as_posix(),
        EXECUTION_AUTHORING_UPSTREAM_RECEIPT_RELATIVE.as_posix(),
        EXECUTION_AUTHORING_REGISTRY_RELATIVE.as_posix(),
        EXECUTION_AUTHORING_SOURCE_REGISTRY_RELATIVE.as_posix(),
        EXECUTION_AUTHORING_MODULE_RELATIVE.as_posix(),
        EXECUTION_AUTHORING_VERIFIER_RELATIVE.as_posix(),
        EXECUTION_AUTHORING_TEST_RELATIVE.as_posix(),
        EXECUTION_AUTHORING_ADR_RU_RELATIVE.as_posix(),
        EXECUTION_AUTHORING_ADR_EN_RELATIVE.as_posix(),
        INVOCATION_AUTHORING_RECORD_RELATIVE.as_posix(),
        INVOCATION_AUTHORING_RECEIPT_RELATIVE.as_posix(),
        OPERATION_AUTHORING_RECORD_RELATIVE.as_posix(),
        OPERATION_AUTHORING_RECEIPT_RELATIVE.as_posix(),
        PRODUCTION_CALLSITE_RELATIVE.as_posix(),
        MODULE_RELATIVE.as_posix(),
        VERIFIER_RELATIVE.as_posix(),
        TEST_RELATIVE.as_posix(),
        Path("tests/conftest.py").as_posix(),
        ADR_RU_RELATIVE.as_posix(),
        ADR_EN_RELATIVE.as_posix(),
    }
)
_SHA256_PATTERN: Final = re.compile(r"^sha256:[0-9a-f]{64}$")
_COMMIT_PATTERN: Final = re.compile(r"^[0-9a-f]{40}$")
_IDENTITY_PATTERN: Final = re.compile(r"^[^\r\n]{1,256}$")
_TREE_PATTERN: Final = re.compile(r"^[0-9a-f]{40}$")
_FORBIDDEN_IMPORT_ROOTS: Final = frozenset({"docker", "os", "subprocess"})
_FORBIDDEN_CALL_NAMES: Final = frozenset(
    {
        "invoke_final_execution_acknowledgement_materialization",
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
    "EXECUTION_AUTHORIZATION_ID",
    "EXECUTION_AUTHORIZATION_PHRASE",
    "AUTHORIZATION_RELATIVE",
    "OPERATION_JSON_RELATIVE",
    "CallsiteExecutionAuthoringMergeValidationReceipt",
    "FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorization",
    "FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationContract",
    "FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError",
    "FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationGates",
    "FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationSource",
    "build_expected_operation",
    "build_execution_authoring_merge_validation_receipt",
    "build_frozen_execution_authorization",
    "load_execution_authoring_merge_validation_receipt",
    "load_execution_authorization",
    "verify_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authorization",
]


class FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError(
    RuntimeError
):
    """Raised when the execution authorization fails closed."""


def _require_sha256(value: str, field_name: str) -> None:
    if not _SHA256_PATTERN.fullmatch(value):
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError(
            f"{field_name} is not a canonical SHA-256 identity"
        )


def _require_commit(value: str, field_name: str) -> None:
    if not _COMMIT_PATTERN.fullmatch(value):
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError(
            f"{field_name} is not a commit identity"
        )


def _require_tree(value: str, field_name: str) -> None:
    if not _TREE_PATTERN.fullmatch(value):
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError(
            f"{field_name} is not a tree identity"
        )


def _require_identity(value: str, field_name: str) -> None:
    if value != value.strip() or not _IDENTITY_PATTERN.fullmatch(value):
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError(
            f"{field_name} is not a bounded identity"
        )


def _require_utc(value: str, field_name: str) -> datetime:
    if not value.endswith("Z"):
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError(
            f"{field_name} is not UTC"
        )
    try:
        result = datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError as exc:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError(
            f"{field_name} is not an ISO-8601 timestamp"
        ) from exc
    if result.tzinfo != UTC:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError(
            f"{field_name} is not canonical UTC"
        )
    return result


@dataclass(frozen=True)
class CallsiteExecutionAuthoringMergeValidationReceipt:
    receipt_id: str
    pr_number: int
    head_commit: str
    original_base_commit: str
    actual_first_parent_commit: str
    merge_commit: str
    merge_base_commit: str
    merge_tree: str
    merged_at_utc: str
    commit_count: int
    advancement_file_count: int
    advancement_insertions: int
    advancement_deletions: int
    file_count: int
    insertions: int
    deletions: int
    focused_tests_passed: int
    targeted_tests_passed: int
    full_tests_passed: int
    full_test_warnings: int
    required_ci_checks_total: int
    required_ci_checks_passed: bool
    immutable_slice_blobs_equal_exact_pr_head: bool
    production_callsite_executed: bool
    execution_authorization_present: bool
    operation_json_present: bool
    receipt_sha256: str

    @classmethod
    def from_mapping(
        cls, value: Mapping[str, object]
    ) -> CallsiteExecutionAuthoringMergeValidationReceipt:
        return cls(**cast(dict[str, Any], dict(value)))

    def semantic_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload.pop("receipt_sha256")
        return cast(dict[str, object], payload)

    def require(self) -> None:
        expected: dict[str, object] = {
            "receipt_id": (
                "stage3b-qwake-lc4-e-final-execution-acknowledgement-"
                "materialization-invocation-operation-callsite-execution-"
                "authoring-post-merge-validation-v1"
            ),
            "pr_number": EXECUTION_AUTHORING_PR_NUMBER,
            "head_commit": EXECUTION_AUTHORING_HEAD_COMMIT,
            "original_base_commit": EXECUTION_AUTHORING_ORIGINAL_BASE_COMMIT,
            "actual_first_parent_commit": (
                EXECUTION_AUTHORING_ACTUAL_FIRST_PARENT_COMMIT
            ),
            "merge_commit": EXECUTION_AUTHORING_MERGE_COMMIT,
            "merge_base_commit": EXECUTION_AUTHORING_MERGE_BASE_COMMIT,
            "merge_tree": EXECUTION_AUTHORING_MERGE_TREE,
            "merged_at_utc": EXECUTION_AUTHORING_MERGED_AT_UTC,
            "commit_count": 1,
            "advancement_file_count": 0,
            "advancement_insertions": 0,
            "advancement_deletions": 0,
            "file_count": 18,
            "insertions": 1678,
            "deletions": 0,
            "focused_tests_passed": 240,
            "targeted_tests_passed": 441,
            "full_tests_passed": 1488,
            "full_test_warnings": 14,
            "required_ci_checks_total": 4,
            "required_ci_checks_passed": True,
            "immutable_slice_blobs_equal_exact_pr_head": True,
            "production_callsite_executed": False,
            "execution_authorization_present": False,
            "operation_json_present": False,
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError(
                    f"execution-authoring merge receipt differs: {field_name}"
                )
        for field_name in (
            "head_commit",
            "original_base_commit",
            "actual_first_parent_commit",
            "merge_commit",
            "merge_base_commit",
        ):
            _require_commit(cast(str, getattr(self, field_name)), field_name)
        _require_tree(self.merge_tree, "merge_tree")
        _require_utc(self.merged_at_utc, "merged_at_utc")
        _require_sha256(self.receipt_sha256, "receipt_sha256")
        if self.receipt_sha256 != sha256_object(self.semantic_payload()):
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError(
                "execution-authoring merge receipt semantic SHA-256 differs"
            )

    def canonical_json(self) -> str:
        self.require()
        return canonical_json(self)


@dataclass(frozen=True)
class FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationSource:
    authorization_base_commit: str
    execution_authoring_id: str
    execution_authoring_sha256: str
    execution_authoring_file_sha256: str
    execution_authoring_upstream_receipt_file_sha256: str
    execution_authoring_package_registry_sha256: str
    execution_authoring_source_registry_sha256: str
    execution_authoring_module_sha256: str
    execution_authoring_verifier_sha256: str
    execution_authoring_test_sha256: str
    execution_authoring_adr_ru_sha256: str
    execution_authoring_adr_en_sha256: str
    execution_authoring_pr_number: int
    execution_authoring_head_commit: str
    execution_authoring_original_base_commit: str
    execution_authoring_actual_first_parent_commit: str
    execution_authoring_merge_commit: str
    execution_authoring_merge_base_commit: str
    execution_authoring_merged_at_utc: str
    execution_authoring_merge_tree: str
    production_callsite_relative: str
    production_callsite_symbol: str
    production_callsite_sha256: str
    operation_implementation_symbol: str
    operation_json_relative: str
    operation_json_sha256: str
    torch2pc_commit: str

    @classmethod
    def from_mapping(
        cls, value: Mapping[str, object]
    ) -> FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationSource:
        return cls(**cast(dict[str, Any], dict(value)))

    def require(
        self,
        receipt: CallsiteExecutionAuthoringMergeValidationReceipt,
        operation: ProspectiveFinalExecutionAcknowledgementMaterializationInvocationOperation,
    ) -> None:
        receipt.require()
        expected = _build_source(receipt, operation)
        if self != expected:
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError(
                "execution authorization source differs"
            )


@dataclass(frozen=True)
class FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationContract:
    exact_authorization_phrase_required: str
    exact_execution_phrase_required: str
    authorization_phrase_distinct_from_execution_phrase: bool
    exact_production_callsite_relative_required: str
    exact_production_callsite_symbol_required: str
    exact_operation_implementation_symbol_required: str
    exact_operation_json_relative_required: str
    exact_operation_json_sha256_required: str
    exact_argv_template_json_required: str
    project_root_option_required: str
    operation_json_option_required: str
    explicit_operator_identity_required: bool
    explicit_authorization_issued_at_utc_required: bool
    authorization_single_use: bool
    authorization_consumption_required_at_attempt_start: bool
    authorization_consumption_atomic_with_attempt_start: bool
    authorization_consumption_forbidden_before_post_merge: bool
    authorization_effective_only_after_post_merge_verification: bool
    execution_commit_is_authorization_merge_commit: bool
    exact_torch2pc_commit_required: str
    canonical_operation_json_required: bool
    operation_json_sha256_pinning_required: bool
    exact_argv_required: bool
    shell_interpretation_forbidden: bool
    cwd_exact_project_root_required: bool
    execution_attempt_limit: int
    automatic_retry_forbidden: bool
    blind_retry_forbidden: bool
    failure_after_consumption_retry_forbidden: bool
    clean_worktree_required: bool
    clean_index_required: bool
    production_callsite_hash_reverification_required: bool
    operation_json_hash_reverification_required: bool
    acknowledgement_absence_required_before_attempt: bool
    legacy_execution_lease_absence_required_before_attempt: bool
    execution_lease_v2_absence_required_before_attempt: bool
    durable_host_outcome_absence_required_before_attempt: bool
    runtime_output_absence_required_before_attempt: bool
    runtime_staging_absence_required_before_attempt: bool
    success_requires_zero_exit: bool
    success_requires_single_canonical_stdout_object: bool
    stdout_before_success_forbidden: bool
    result_file_write_forbidden: bool
    nonzero_exit_on_failure_required: bool
    standalone_preprobe_forbidden: bool
    direct_invocation_adapter_call_forbidden: bool
    direct_materializer_call_forbidden: bool
    direct_writer_call_forbidden: bool
    authorization_authoring_effects_forbidden: bool
    production_callsite_execution_forbidden: bool
    operation_performance_forbidden: bool
    subprocess_forbidden: bool
    docker_forbidden: bool
    image_inspection_forbidden: bool
    command_materialization_forbidden: bool
    lease_materialization_forbidden: bool
    durable_outcome_persistence_forbidden: bool
    local_compute_forbidden: bool

    @classmethod
    def from_mapping(
        cls, value: Mapping[str, object]
    ) -> FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationContract:
        return cls(**cast(dict[str, Any], dict(value)))

    def require(self, operation_json_sha256: str) -> None:
        if self != _build_contract(operation_json_sha256):
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError(
                "execution authorization contract differs"
            )


@dataclass(frozen=True)
class FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationGates:
    execution_authoring_post_merge_verified: bool
    materialization_invocation_operation_callsite_implemented: bool
    production_callsite_present: bool
    execution_authorization_record_present: bool
    execution_authorization_issued: bool
    canonical_operation_json_materialized: bool
    execution_authorization_post_merge_verified: bool
    callsite_execution_authorized: bool
    production_callsite_executed: bool
    callsite_execution_performed: bool
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
    ) -> FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationGates:
        return cls(**cast(dict[str, Any], dict(value)))

    def require(self) -> None:
        if self != _build_gates():
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError(
                "execution authorization gates differ"
            )


@dataclass(frozen=True)
class FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorization:
    schema_version: int
    authorization_id: str
    status: str
    recorded_at_utc: str
    authorization_phrase: str
    operator_identity: str
    authorization_issued_at_utc: str
    source: FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationSource
    contract: FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationContract
    gates: FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationGates
    next_slice: str
    post_merge_next_slice: str
    authorization_sha256: str

    @classmethod
    def from_mapping(
        cls, value: Mapping[str, object]
    ) -> FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorization:
        payload = dict(value)
        payload["source"] = FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationSource.from_mapping(
            cast(Mapping[str, object], payload["source"])
        )
        payload["contract"] = FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationContract.from_mapping(
            cast(Mapping[str, object], payload["contract"])
        )
        payload["gates"] = FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationGates.from_mapping(
            cast(Mapping[str, object], payload["gates"])
        )
        return cls(**cast(dict[str, Any], payload))

    def semantic_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload.pop("authorization_sha256")
        return cast(dict[str, object], payload)

    def require(
        self,
        receipt: CallsiteExecutionAuthoringMergeValidationReceipt,
        operation: ProspectiveFinalExecutionAcknowledgementMaterializationInvocationOperation,
    ) -> None:
        expected: dict[str, object] = {
            "schema_version": 1,
            "authorization_id": EXECUTION_AUTHORIZATION_ID,
            "status": EXECUTION_AUTHORIZATION_STATUS,
            "recorded_at_utc": EXECUTION_AUTHORIZATION_RECORDED_AT_UTC,
            "authorization_phrase": EXECUTION_AUTHORIZATION_PHRASE,
            "operator_identity": EXECUTION_OPERATOR_IDENTITY,
            "authorization_issued_at_utc": AUTHORIZATION_ISSUED_AT_UTC,
            "next_slice": (
                "QW-LC4-E-final-execution-acknowledgement-materialization-"
                "invocation-operation-callsite-execution-authorization-commit"
            ),
            "post_merge_next_slice": (
                "QW-LC4-E-final-execution-acknowledgement-materialization-"
                "invocation-operation-callsite-execution"
            ),
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError(
                    f"execution authorization differs: {field_name}"
                )
        _require_identity(self.operator_identity, "operator_identity")
        recorded = _require_utc(self.recorded_at_utc, "recorded_at_utc")
        issued = _require_utc(
            self.authorization_issued_at_utc, "authorization_issued_at_utc"
        )
        merged = _require_utc(receipt.merged_at_utc, "merged_at_utc")
        operation_authorized = _require_utc(
            operation.operation_authorized_at_utc,
            "operation_authorized_at_utc",
        )
        if operation.operation_operator_identity != self.operator_identity:
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError(
                "authorization operator differs from operation operator"
            )
        if issued <= merged or issued < operation_authorized or recorded < issued:
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError(
                "authorization timestamps are not ordered after merge"
            )
        operation_sha256 = sha256_bytes(canonical_json(operation).encode("utf-8"))
        self.source.require(receipt, operation)
        self.contract.require(operation_sha256)
        self.gates.require()
        _require_sha256(self.authorization_sha256, "authorization_sha256")
        if self.authorization_sha256 != sha256_object(self.semantic_payload()):
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError(
                "execution authorization semantic SHA-256 differs"
            )

    def canonical_json(
        self,
        receipt: CallsiteExecutionAuthoringMergeValidationReceipt,
        operation: ProspectiveFinalExecutionAcknowledgementMaterializationInvocationOperation,
    ) -> str:
        self.require(receipt, operation)
        return canonical_json(self)


def build_execution_authoring_merge_validation_receipt() -> CallsiteExecutionAuthoringMergeValidationReceipt:
    provisional = CallsiteExecutionAuthoringMergeValidationReceipt(
        receipt_id=(
            "stage3b-qwake-lc4-e-final-execution-acknowledgement-"
            "materialization-invocation-operation-callsite-execution-"
            "authoring-post-merge-validation-v1"
        ),
        pr_number=EXECUTION_AUTHORING_PR_NUMBER,
        head_commit=EXECUTION_AUTHORING_HEAD_COMMIT,
        original_base_commit=EXECUTION_AUTHORING_ORIGINAL_BASE_COMMIT,
        actual_first_parent_commit=EXECUTION_AUTHORING_ACTUAL_FIRST_PARENT_COMMIT,
        merge_commit=EXECUTION_AUTHORING_MERGE_COMMIT,
        merge_base_commit=EXECUTION_AUTHORING_MERGE_BASE_COMMIT,
        merge_tree=EXECUTION_AUTHORING_MERGE_TREE,
        merged_at_utc=EXECUTION_AUTHORING_MERGED_AT_UTC,
        commit_count=1,
        advancement_file_count=0,
        advancement_insertions=0,
        advancement_deletions=0,
        file_count=18,
        insertions=1678,
        deletions=0,
        focused_tests_passed=240,
        targeted_tests_passed=441,
        full_tests_passed=1488,
        full_test_warnings=14,
        required_ci_checks_total=4,
        required_ci_checks_passed=True,
        immutable_slice_blobs_equal_exact_pr_head=True,
        production_callsite_executed=False,
        execution_authorization_present=False,
        operation_json_present=False,
        receipt_sha256="sha256:" + "0" * 64,
    )
    result = replace(
        provisional,
        receipt_sha256=sha256_object(provisional.semantic_payload()),
    )
    result.require()
    return result


def build_expected_operation(
    project_root: Path,
) -> ProspectiveFinalExecutionAcknowledgementMaterializationInvocationOperation:
    root = _verified_project_root(project_root)
    invocation_receipt = load_materialization_implementation_merge_validation_receipt(
        root / INVOCATION_AUTHORING_RECEIPT_RELATIVE
    )
    invocation_authoring = load_final_execution_acknowledgement_materialization_invocation_authoring(
        root / INVOCATION_AUTHORING_RECORD_RELATIVE,
        invocation_receipt,
    )
    invocation = build_prospective_acknowledgement_materialization_invocation(
        invocation_authoring,
        invocation_receipt,
        acknowledgement_phrase=FINAL_EXECUTION_OPERATOR_ACKNOWLEDGEMENT,
        operator_identity=EXECUTION_OPERATOR_IDENTITY,
        acknowledged_at_utc=ACKNOWLEDGED_AT_UTC,
        issuer_identity=EXECUTION_OPERATOR_IDENTITY,
        issued_at_utc=ISSUED_AT_UTC,
        materializer_identity=EXECUTION_OPERATOR_IDENTITY,
        materialized_at_utc=MATERIALIZED_AT_UTC,
    )
    operation_receipt = load_invocation_implementation_merge_validation_receipt(
        root / OPERATION_AUTHORING_RECEIPT_RELATIVE
    )
    operation_authoring = load_final_execution_acknowledgement_materialization_invocation_operation_authoring(
        root / OPERATION_AUTHORING_RECORD_RELATIVE,
        operation_receipt,
    )
    return build_prospective_acknowledgement_materialization_invocation_operation(
        operation_authoring,
        operation_receipt,
        invocation,
        operation_phrase=(
            FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_OPERATION_PHRASE
        ),
        operation_operator_identity=EXECUTION_OPERATOR_IDENTITY,
        operation_authorized_at_utc=OPERATION_AUTHORIZED_AT_UTC,
    )


def _build_source(
    receipt: CallsiteExecutionAuthoringMergeValidationReceipt,
    operation: ProspectiveFinalExecutionAcknowledgementMaterializationInvocationOperation,
) -> FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationSource:
    receipt.require()
    operation_json_sha256 = sha256_bytes(canonical_json(operation).encode("utf-8"))
    return FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationSource(
        authorization_base_commit=EXECUTION_AUTHORIZATION_BASE_COMMIT,
        execution_authoring_id=CALLSITE_EXECUTION_AUTHORING_ID,
        execution_authoring_sha256=EXECUTION_AUTHORING_SHA256,
        execution_authoring_file_sha256=EXECUTION_AUTHORING_FILE_SHA256,
        execution_authoring_upstream_receipt_file_sha256=(
            EXECUTION_AUTHORING_UPSTREAM_RECEIPT_FILE_SHA256
        ),
        execution_authoring_package_registry_sha256=(
            EXECUTION_AUTHORING_PACKAGE_REGISTRY_SHA256
        ),
        execution_authoring_source_registry_sha256=(
            EXECUTION_AUTHORING_SOURCE_REGISTRY_SHA256
        ),
        execution_authoring_module_sha256=EXECUTION_AUTHORING_MODULE_SHA256,
        execution_authoring_verifier_sha256=EXECUTION_AUTHORING_VERIFIER_SHA256,
        execution_authoring_test_sha256=EXECUTION_AUTHORING_TEST_SHA256,
        execution_authoring_adr_ru_sha256=EXECUTION_AUTHORING_ADR_RU_SHA256,
        execution_authoring_adr_en_sha256=EXECUTION_AUTHORING_ADR_EN_SHA256,
        execution_authoring_pr_number=receipt.pr_number,
        execution_authoring_head_commit=receipt.head_commit,
        execution_authoring_original_base_commit=receipt.original_base_commit,
        execution_authoring_actual_first_parent_commit=(
            receipt.actual_first_parent_commit
        ),
        execution_authoring_merge_commit=receipt.merge_commit,
        execution_authoring_merge_base_commit=receipt.merge_base_commit,
        execution_authoring_merged_at_utc=receipt.merged_at_utc,
        execution_authoring_merge_tree=receipt.merge_tree,
        production_callsite_relative=PRODUCTION_CALLSITE_RELATIVE.as_posix(),
        production_callsite_symbol=PRODUCTION_CALLSITE_SYMBOL,
        production_callsite_sha256=PRODUCTION_CALLSITE_SHA256,
        operation_implementation_symbol=OPERATION_IMPLEMENTATION_SYMBOL,
        operation_json_relative=OPERATION_JSON_RELATIVE.as_posix(),
        operation_json_sha256=operation_json_sha256,
        torch2pc_commit=TORCH2PC_COMMIT,
    )


def _build_contract(
    operation_json_sha256: str,
) -> FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationContract:
    _require_sha256(operation_json_sha256, "operation_json_sha256")
    return FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationContract(
        exact_authorization_phrase_required=EXECUTION_AUTHORIZATION_PHRASE,
        exact_execution_phrase_required=CALLSITE_EXECUTION_PHRASE,
        authorization_phrase_distinct_from_execution_phrase=(
            str(EXECUTION_AUTHORIZATION_PHRASE) != str(CALLSITE_EXECUTION_PHRASE)
        ),
        exact_production_callsite_relative_required=(
            PRODUCTION_CALLSITE_RELATIVE.as_posix()
        ),
        exact_production_callsite_symbol_required=PRODUCTION_CALLSITE_SYMBOL,
        exact_operation_implementation_symbol_required=OPERATION_IMPLEMENTATION_SYMBOL,
        exact_operation_json_relative_required=OPERATION_JSON_RELATIVE.as_posix(),
        exact_operation_json_sha256_required=operation_json_sha256,
        exact_argv_template_json_required=EXACT_ARGV_TEMPLATE_JSON,
        project_root_option_required=PROJECT_ROOT_OPTION,
        operation_json_option_required=OPERATION_JSON_OPTION,
        explicit_operator_identity_required=True,
        explicit_authorization_issued_at_utc_required=True,
        authorization_single_use=True,
        authorization_consumption_required_at_attempt_start=True,
        authorization_consumption_atomic_with_attempt_start=True,
        authorization_consumption_forbidden_before_post_merge=True,
        authorization_effective_only_after_post_merge_verification=True,
        execution_commit_is_authorization_merge_commit=True,
        exact_torch2pc_commit_required=TORCH2PC_COMMIT,
        canonical_operation_json_required=True,
        operation_json_sha256_pinning_required=True,
        exact_argv_required=True,
        shell_interpretation_forbidden=True,
        cwd_exact_project_root_required=True,
        execution_attempt_limit=1,
        automatic_retry_forbidden=True,
        blind_retry_forbidden=True,
        failure_after_consumption_retry_forbidden=True,
        clean_worktree_required=True,
        clean_index_required=True,
        production_callsite_hash_reverification_required=True,
        operation_json_hash_reverification_required=True,
        acknowledgement_absence_required_before_attempt=True,
        legacy_execution_lease_absence_required_before_attempt=True,
        execution_lease_v2_absence_required_before_attempt=True,
        durable_host_outcome_absence_required_before_attempt=True,
        runtime_output_absence_required_before_attempt=True,
        runtime_staging_absence_required_before_attempt=True,
        success_requires_zero_exit=True,
        success_requires_single_canonical_stdout_object=True,
        stdout_before_success_forbidden=True,
        result_file_write_forbidden=True,
        nonzero_exit_on_failure_required=True,
        standalone_preprobe_forbidden=True,
        direct_invocation_adapter_call_forbidden=True,
        direct_materializer_call_forbidden=True,
        direct_writer_call_forbidden=True,
        authorization_authoring_effects_forbidden=True,
        production_callsite_execution_forbidden=True,
        operation_performance_forbidden=True,
        subprocess_forbidden=True,
        docker_forbidden=True,
        image_inspection_forbidden=True,
        command_materialization_forbidden=True,
        lease_materialization_forbidden=True,
        durable_outcome_persistence_forbidden=True,
        local_compute_forbidden=True,
    )


def _build_gates() -> FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationGates:
    return FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationGates(
        execution_authoring_post_merge_verified=True,
        materialization_invocation_operation_callsite_implemented=True,
        production_callsite_present=True,
        execution_authorization_record_present=True,
        execution_authorization_issued=True,
        canonical_operation_json_materialized=True,
        execution_authorization_post_merge_verified=False,
        callsite_execution_authorized=False,
        production_callsite_executed=False,
        callsite_execution_performed=False,
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


def build_frozen_execution_authorization(
    receipt: CallsiteExecutionAuthoringMergeValidationReceipt,
    operation: ProspectiveFinalExecutionAcknowledgementMaterializationInvocationOperation,
) -> FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorization:
    operation_sha256 = sha256_bytes(canonical_json(operation).encode("utf-8"))
    provisional = FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorization(
        schema_version=1,
        authorization_id=EXECUTION_AUTHORIZATION_ID,
        status=EXECUTION_AUTHORIZATION_STATUS,
        recorded_at_utc=EXECUTION_AUTHORIZATION_RECORDED_AT_UTC,
        authorization_phrase=EXECUTION_AUTHORIZATION_PHRASE,
        operator_identity=EXECUTION_OPERATOR_IDENTITY,
        authorization_issued_at_utc=AUTHORIZATION_ISSUED_AT_UTC,
        source=_build_source(receipt, operation),
        contract=_build_contract(operation_sha256),
        gates=_build_gates(),
        next_slice=(
            "QW-LC4-E-final-execution-acknowledgement-materialization-"
            "invocation-operation-callsite-execution-authorization-commit"
        ),
        post_merge_next_slice=(
            "QW-LC4-E-final-execution-acknowledgement-materialization-"
            "invocation-operation-callsite-execution"
        ),
        authorization_sha256="sha256:" + "0" * 64,
    )
    result = replace(
        provisional,
        authorization_sha256=sha256_object(provisional.semantic_payload()),
    )
    result.require(receipt, operation)
    return result


def _verified_project_root(project_root: Path) -> Path:
    root = project_root.expanduser().resolve(strict=True)
    if not root.is_dir():
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError(
            "project root is not a directory"
        )
    return root


def _load_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8", errors="strict"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError(
            f"cannot read JSON object: {path}"
        ) from exc
    if not isinstance(value, dict):
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError(
            f"JSON root is not an object: {path}"
        )
    return cast(dict[str, Any], value)


def load_execution_authoring_merge_validation_receipt(
    project_root: Path,
) -> CallsiteExecutionAuthoringMergeValidationReceipt:
    root = _verified_project_root(project_root)
    result = CallsiteExecutionAuthoringMergeValidationReceipt.from_mapping(
        _load_json_object(root / EXECUTION_AUTHORING_MERGE_RECEIPT_RELATIVE)
    )
    result.require()
    return result


def load_execution_authorization(
    project_root: Path,
) -> FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorization:
    root = _verified_project_root(project_root)
    receipt = load_execution_authoring_merge_validation_receipt(root)
    operation = load_canonical_prospective_operation(root, OPERATION_JSON_RELATIVE)
    result = FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorization.from_mapping(
        _load_json_object(root / AUTHORIZATION_RELATIVE)
    )
    result.require(receipt, operation)
    return result


def _load_registry(path: Path) -> dict[str, str]:
    if not path.is_file() or path.is_symlink():
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError(
            f"registry is absent or invalid: {path}"
        )
    result: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8", errors="strict").splitlines()
    except (OSError, UnicodeError) as exc:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError(
            f"cannot read registry: {path}"
        ) from exc
    for line in lines:
        if not line:
            continue
        parts = line.split("  ", 1)
        if len(parts) != 2 or not re.fullmatch(r"[0-9a-f]{64}", parts[0]):
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError(
                f"invalid registry line: {line}"
            )
        if parts[1] in result:
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError(
                f"duplicate registry path: {parts[1]}"
            )
        result[parts[1]] = parts[0]
    return result


def _verify_registry(path: Path, base: Path) -> dict[str, str]:
    registry = _load_registry(path)
    for relative, expected in registry.items():
        target = base / relative
        if not target.is_file() or target.is_symlink():
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError(
                f"registry target is absent or invalid: {target}"
            )
        observed = sha256_bytes(target.read_bytes()).removeprefix("sha256:")
        if observed != expected:
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError(
                f"registry target hash differs: {target}"
            )
    return registry


def _verify_authorization_ast(root: Path) -> None:
    path = root / MODULE_RELATIVE
    tree = ast.parse(path.read_text(encoding="utf-8", errors="strict"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".", 1)[0] in _FORBIDDEN_IMPORT_ROOTS:
                    raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError(
                        f"forbidden import in execution authorization module: {alias.name}"
                    )
        elif isinstance(node, ast.ImportFrom):
            imported = node.module or ""
            if imported.split(".", 1)[0] in _FORBIDDEN_IMPORT_ROOTS:
                raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError(
                    f"forbidden import in execution authorization module: {imported}"
                )
        elif isinstance(node, ast.Call):
            called = ""
            if isinstance(node.func, ast.Name):
                called = node.func.id
            elif isinstance(node.func, ast.Attribute):
                called = node.func.attr
            if isinstance(node.func, ast.Name) and called in _FORBIDDEN_CALL_NAMES:
                raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError(
                    f"forbidden call in execution authorization module: {called}"
                )
            if (
                isinstance(node.func, ast.Attribute)
                and called in _FORBIDDEN_CALL_ATTRIBUTES
            ):
                raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError(
                    f"forbidden effect in execution authorization module: {called}"
                )


def _require_production_boundary_closed(root: Path) -> None:
    for relative in (
        Path("results/stage-3/qwake-lc4-runtime-validation-v1-attempt-001"),
        ACKNOWLEDGEMENT_RELATIVE,
        LEGACY_EXECUTION_LEASE_RELATIVE,
        EXECUTION_LEASE_V2_RELATIVE,
        DURABLE_HOST_OUTCOME_RELATIVE,
    ):
        target = root / relative
        if target.exists() or target.is_symlink():
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError(
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
                raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError(
                    f"production boundary staging artifact exists: {path.name}"
                )


def verify_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authorization(
    project_root: Path,
) -> FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorization:
    root = _verified_project_root(project_root)
    execution_authoring_package = root / EXECUTION_AUTHORING_RECORD_RELATIVE.parent
    if (
        not execution_authoring_package.is_dir()
        or execution_authoring_package.is_symlink()
    ):
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError(
            "execution authoring package is absent or invalid"
        )
    execution_authoring_files = {
        path.name
        for path in execution_authoring_package.iterdir()
        if path.is_file()
    }
    if execution_authoring_files != {
        "SHA256SUMS",
        "authoring.json",
        "implementation-merge-validation.json",
        "source-SHA256SUMS",
    }:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError(
            "execution authoring package file set differs"
        )
    expected_execution_authoring_hashes = {
        EXECUTION_AUTHORING_RECORD_RELATIVE: EXECUTION_AUTHORING_FILE_SHA256,
        EXECUTION_AUTHORING_UPSTREAM_RECEIPT_RELATIVE: (
            EXECUTION_AUTHORING_UPSTREAM_RECEIPT_FILE_SHA256
        ),
        EXECUTION_AUTHORING_REGISTRY_RELATIVE: (
            EXECUTION_AUTHORING_PACKAGE_REGISTRY_SHA256
        ),
        EXECUTION_AUTHORING_SOURCE_REGISTRY_RELATIVE: (
            EXECUTION_AUTHORING_SOURCE_REGISTRY_SHA256
        ),
        EXECUTION_AUTHORING_MODULE_RELATIVE: EXECUTION_AUTHORING_MODULE_SHA256,
        EXECUTION_AUTHORING_VERIFIER_RELATIVE: (
            EXECUTION_AUTHORING_VERIFIER_SHA256
        ),
        EXECUTION_AUTHORING_TEST_RELATIVE: EXECUTION_AUTHORING_TEST_SHA256,
        EXECUTION_AUTHORING_ADR_RU_RELATIVE: EXECUTION_AUTHORING_ADR_RU_SHA256,
        EXECUTION_AUTHORING_ADR_EN_RELATIVE: EXECUTION_AUTHORING_ADR_EN_SHA256,
    }
    for relative, expected_sha256 in expected_execution_authoring_hashes.items():
        target = root / relative
        if (
            not target.is_file()
            or target.is_symlink()
            or sha256_bytes(target.read_bytes()) != expected_sha256
        ):
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError(
                f"execution authoring byte identity differs: {relative}"
            )
    _verify_registry(
        root / EXECUTION_AUTHORING_REGISTRY_RELATIVE,
        execution_authoring_package,
    )
    execution_authoring_source_registry = _load_registry(
        root / EXECUTION_AUTHORING_SOURCE_REGISTRY_RELATIVE
    )
    historical_test_view = "tests/conftest.py"
    historical_test_view_sha256 = (
        "4815e0979efcb3cb189be78f5b0c4279bf17cb0ddf27a2ea8908772c74ee9b09"
    )
    for source_relative, expected in execution_authoring_source_registry.items():
        if source_relative == historical_test_view:
            if expected != historical_test_view_sha256:
                raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError(
                    "historical successor-aware test view SHA-256 differs"
                )
            continue
        target = root / source_relative
        if not target.is_file() or target.is_symlink():
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError(
                f"execution authoring source target is absent: {source_relative}"
            )
        observed = sha256_bytes(target.read_bytes()).removeprefix("sha256:")
        if observed != expected:
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError(
                f"execution authoring source target hash differs: {source_relative}"
            )
    upstream_receipt = load_callsite_implementation_merge_validation_receipt(root)
    execution_authoring = load_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authoring(
        root
    )
    execution_authoring.require(upstream_receipt)
    if execution_authoring.authoring_sha256 != EXECUTION_AUTHORING_SHA256:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError(
            "execution authoring semantic SHA-256 differs"
        )

    package = root / PACKAGE_RELATIVE
    if not package.is_dir() or package.is_symlink():
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError(
            "execution authorization package is absent or invalid"
        )
    package_files = {path.name for path in package.iterdir() if path.is_file()}
    if package_files != _EXPECTED_PACKAGE_FILES:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError(
            "execution authorization package file set differs"
        )

    package_registry = _verify_registry(package / "SHA256SUMS", package)
    if set(package_registry) != {
        "authorization.json",
        "execution-authoring-merge-validation.json",
        "operation.json",
        "source-SHA256SUMS",
    }:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError(
            "execution authorization package registry path set differs"
        )
    source_registry = _verify_registry(package / "source-SHA256SUMS", root)
    if set(source_registry) != _EXPECTED_SOURCE_PATHS:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError(
            "execution authorization source registry path set differs"
        )

    receipt = load_execution_authoring_merge_validation_receipt(root)
    expected_operation = build_expected_operation(root)
    observed_operation = load_canonical_prospective_operation(
        root,
        OPERATION_JSON_RELATIVE,
    )
    if observed_operation != expected_operation:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError(
            "canonical operation JSON differs from the authorized operation"
        )
    authorization = load_execution_authorization(root)
    authorization.require(receipt, observed_operation)
    _verify_authorization_ast(root)

    callsite = root / PRODUCTION_CALLSITE_RELATIVE
    if (
        not callsite.is_file()
        or callsite.is_symlink()
        or sha256_bytes(callsite.read_bytes()) != PRODUCTION_CALLSITE_SHA256
    ):
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthorizationError(
            "production callsite identity differs"
        )
    _require_production_boundary_closed(root)
    return authorization
