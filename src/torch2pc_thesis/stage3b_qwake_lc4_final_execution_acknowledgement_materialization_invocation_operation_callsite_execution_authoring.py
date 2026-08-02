"""Effect-free authoring for future production-callsite execution.

This module freezes the exact evidence, authorization, argv, and fail-closed
boundary required before the already implemented production callsite may be
executed.  It verifies immutable repository records only.  It does not execute
the callsite, build the operation JSON, authorize execution, call the operation
or lower layers, or create acknowledgement, lease, runtime, Docker, or local-
compute evidence.
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
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_authoring import (
    FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_OPERATION_PHRASE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_callsite_implementation import (
    ADR_EN_RELATIVE as CALLSITE_IMPLEMENTATION_ADR_EN_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_callsite_implementation import (
    ADR_RU_RELATIVE as CALLSITE_IMPLEMENTATION_ADR_RU_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_callsite_implementation import (
    AUTHORING_MERGE_RECEIPT_RELATIVE as CALLSITE_IMPLEMENTATION_UPSTREAM_RECEIPT_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_callsite_implementation import (
    CALLSITE_IMPLEMENTATION_ID,
    OPERATION_JSON_OPTION,
    PRODUCTION_CALLSITE_RELATIVE,
    PRODUCTION_CALLSITE_SYMBOL,
    PROJECT_ROOT_OPTION,
    verify_final_execution_acknowledgement_materialization_invocation_operation_callsite_implementation,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_callsite_implementation import (
    HISTORICAL_TEST_VIEW_RELATIVE as CALLSITE_IMPLEMENTATION_HISTORICAL_TEST_VIEW_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_callsite_implementation import (
    IMPLEMENTATION_RECORD_RELATIVE as CALLSITE_IMPLEMENTATION_RECORD_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_callsite_implementation import (
    MODULE_RELATIVE as CALLSITE_IMPLEMENTATION_MODULE_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_callsite_implementation import (
    REGISTRY_RELATIVE as CALLSITE_IMPLEMENTATION_REGISTRY_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_callsite_implementation import (
    SOURCE_REGISTRY_RELATIVE as CALLSITE_IMPLEMENTATION_SOURCE_REGISTRY_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_callsite_implementation import (
    TEST_RELATIVE as CALLSITE_IMPLEMENTATION_TEST_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_callsite_implementation import (
    VERIFIER_RELATIVE as CALLSITE_IMPLEMENTATION_VERIFIER_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_implementation import (
    OPERATION_IMPLEMENTATION_SYMBOL,
)

CALLSITE_EXECUTION_AUTHORING_ID: Final = (
    "stage3b-qwake-lc4-e-final-execution-acknowledgement-materialization-"
    "invocation-operation-callsite-execution-authoring-v1"
)
CALLSITE_EXECUTION_AUTHORING_STATUS: Final = (
    "materialization_invocation_operation_callsite_execution_contract_authored_"
    "not_authorized_not_performed_execution_closed"
)
CALLSITE_EXECUTION_AUTHORING_BASE_COMMIT: Final = (
    "78129528d05e8268b4e40fdf708fd9d2c8e3ab29"
)
CALLSITE_IMPLEMENTATION_PR_NUMBER: Final = 163
CALLSITE_IMPLEMENTATION_HEAD_COMMIT: Final = (
    "c9bac0b4d407e4a8e75de6ebf80c80781302c48c"
)
CALLSITE_IMPLEMENTATION_PARENT_COMMIT: Final = (
    "b27e252cf7c64e88d5d61bf7a23c70ffc5957959"
)
CALLSITE_IMPLEMENTATION_MERGE_COMMIT: Final = CALLSITE_EXECUTION_AUTHORING_BASE_COMMIT
CALLSITE_IMPLEMENTATION_MERGED_AT_UTC: Final = "2026-08-01T19:52:10Z"
CALLSITE_IMPLEMENTATION_MERGE_TREE: Final = (
    "68d4ebec9ce720402ff238fc2ec5e9c570833d0e"
)

CALLSITE_IMPLEMENTATION_SHA256: Final = (
    "sha256:d69664e4d1a2b2140a873750086270bb1d3578ff7c0c897d8240f4bb0796ba89"
)
CALLSITE_IMPLEMENTATION_FILE_SHA256: Final = (
    "sha256:b93949abedfdddbb01001aeb2ec6b10c473fc1dc4eddb70358ae2c54c7a0e89f"
)
CALLSITE_IMPLEMENTATION_MERGE_RECEIPT_FILE_SHA256: Final = (
    "sha256:e2dd701180238c7deccbd6577e9373f116cc92b5199fe9db2ae4b91f1c68ceba"
)
CALLSITE_IMPLEMENTATION_PACKAGE_REGISTRY_SHA256: Final = (
    "sha256:5cbcba5246957c984881bf45cbb0677a5a743a558b49c4b5ed1671cbeb3418b8"
)
CALLSITE_IMPLEMENTATION_SOURCE_REGISTRY_SHA256: Final = (
    "sha256:986ee11f7f63bc5520e4d8f1037bbb0c513e7dedbe777d1c77a5fd2a29ef623f"
)
CALLSITE_IMPLEMENTATION_CALLSITE_SHA256: Final = (
    "sha256:8915c208c69ba6595cd3efd4d85b471989402de96dfdd0d877e0c96c1c145703"
)
CALLSITE_IMPLEMENTATION_MODULE_SHA256: Final = (
    "sha256:4d6941ade858dc3b015aa6779b24f1ec5ff030d477a57e0e42939e1c67507a93"
)
CALLSITE_IMPLEMENTATION_VERIFIER_SHA256: Final = (
    "sha256:7d8dc13fd8aa498703e23a42a45887316a03eeb67bd62eb68e835074f271ea1d"
)
CALLSITE_IMPLEMENTATION_TEST_SHA256: Final = (
    "sha256:c35fda6649c77f91645f5e3898f93b867c657d18785b8248adf02abfcb865222"
)
CALLSITE_IMPLEMENTATION_HISTORICAL_TEST_VIEW_SHA256: Final = (
    "sha256:4815e0979efcb3cb189be78f5b0c4279bf17cb0ddf27a2ea8908772c74ee9b09"
)
CALLSITE_IMPLEMENTATION_ADR_RU_SHA256: Final = (
    "sha256:15b2c9bb5978b47755ce559f67aed0c1ea79f04e87e00465195115f040c02223"
)
CALLSITE_IMPLEMENTATION_ADR_EN_SHA256: Final = (
    "sha256:20bbaacc12013e3349a4c0515bbeac83ff7110162595d69ecb6e5a5560b3a03f"
)

CALLSITE_EXECUTION_PHRASE: Final = (
    "EXECUTE_QWAKE_LC4_FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_"
    "OPERATION_CALLSITE"
)
FUTURE_EXECUTION_AUTHORIZATION_PACKAGE_RELATIVE: Final = Path(
    "experiments/frozen/stage3b-qwake-lc4-e-final-execution-"
    "acknowledgement-materialization-invocation-operation-callsite-execution-"
    "authorization-v1"
)
FUTURE_EXECUTION_AUTHORIZATION_RELATIVE: Final = (
    FUTURE_EXECUTION_AUTHORIZATION_PACKAGE_RELATIVE / "authorization.json"
)
FUTURE_OPERATION_JSON_RELATIVE: Final = (
    FUTURE_EXECUTION_AUTHORIZATION_PACKAGE_RELATIVE / "operation.json"
)

PACKAGE_RELATIVE: Final = Path(
    "experiments/frozen/stage3b-qwake-lc4-e-final-execution-"
    "acknowledgement-materialization-invocation-operation-callsite-execution-"
    "authoring-v1"
)
AUTHORING_RECORD_RELATIVE: Final = PACKAGE_RELATIVE / "authoring.json"
IMPLEMENTATION_MERGE_RECEIPT_RELATIVE: Final = (
    PACKAGE_RELATIVE / "implementation-merge-validation.json"
)
REGISTRY_RELATIVE: Final = PACKAGE_RELATIVE / "SHA256SUMS"
SOURCE_REGISTRY_RELATIVE: Final = PACKAGE_RELATIVE / "source-SHA256SUMS"
MODULE_RELATIVE: Final = Path(
    "src/torch2pc_thesis/stage3b_qwake_lc4_final_execution_acknowledgement_"
    "materialization_invocation_operation_callsite_execution_authoring.py"
)
VERIFIER_RELATIVE: Final = Path(
    "scripts/verify_stage3b_qwake_lc4_final_execution_acknowledgement_"
    "materialization_invocation_operation_callsite_execution_authoring.py"
)
TEST_RELATIVE: Final = Path(
    "tests/unit/test_stage3b_qwake_lc4_final_execution_acknowledgement_"
    "materialization_invocation_operation_callsite_execution_authoring.py"
)
ADR_RU_RELATIVE: Final = Path(
    "docs/decisions/ADR-097-stage3b-qwake-lc4-e-final-execution-"
    "acknowledgement-materialization-invocation-operation-callsite-execution-"
    "authoring.md"
)
ADR_EN_RELATIVE: Final = Path(
    "docs/decisions/ADR-097-stage3b-qwake-lc4-e-final-execution-"
    "acknowledgement-materialization-invocation-operation-callsite-execution-"
    "authoring_EN.md"
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
        CALLSITE_IMPLEMENTATION_RECORD_RELATIVE.as_posix(),
        CALLSITE_IMPLEMENTATION_UPSTREAM_RECEIPT_RELATIVE.as_posix(),
        CALLSITE_IMPLEMENTATION_REGISTRY_RELATIVE.as_posix(),
        CALLSITE_IMPLEMENTATION_SOURCE_REGISTRY_RELATIVE.as_posix(),
        PRODUCTION_CALLSITE_RELATIVE.as_posix(),
        CALLSITE_IMPLEMENTATION_MODULE_RELATIVE.as_posix(),
        CALLSITE_IMPLEMENTATION_VERIFIER_RELATIVE.as_posix(),
        CALLSITE_IMPLEMENTATION_TEST_RELATIVE.as_posix(),
        CALLSITE_IMPLEMENTATION_HISTORICAL_TEST_VIEW_RELATIVE.as_posix(),
        CALLSITE_IMPLEMENTATION_ADR_RU_RELATIVE.as_posix(),
        CALLSITE_IMPLEMENTATION_ADR_EN_RELATIVE.as_posix(),
        MODULE_RELATIVE.as_posix(),
        VERIFIER_RELATIVE.as_posix(),
        TEST_RELATIVE.as_posix(),
        ADR_RU_RELATIVE.as_posix(),
        ADR_EN_RELATIVE.as_posix(),
    }
)
_SHA256_PATTERN: Final = re.compile(r"^sha256:[0-9a-f]{64}$")
_COMMIT_PATTERN: Final = re.compile(r"^[0-9a-f]{40}$")
_FORBIDDEN_IMPORT_ROOTS: Final = frozenset({"docker", "os", "subprocess"})
_FORBIDDEN_CALL_NAMES: Final = frozenset(
    {
        "input",
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
    "CALLSITE_EXECUTION_AUTHORING_ID",
    "CALLSITE_EXECUTION_AUTHORING_BASE_COMMIT",
    "CALLSITE_EXECUTION_PHRASE",
    "FUTURE_EXECUTION_AUTHORIZATION_RELATIVE",
    "FUTURE_OPERATION_JSON_RELATIVE",
    "AcknowledgementMaterializationInvocationOperationCallsiteImplementationMergeValidationReceipt",
    "FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoring",
    "FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringContract",
    "FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringError",
    "FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringGates",
    "FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringSource",
    "build_callsite_implementation_merge_validation_receipt",
    "build_frozen_materialization_invocation_operation_callsite_execution_authoring_record",
    "load_callsite_implementation_merge_validation_receipt",
    "load_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authoring",
    "verify_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authoring",
]


class FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringError(
    RuntimeError
):
    """Raised when the execution-authoring boundary fails closed."""


def _require_sha256(value: str, field_name: str) -> None:
    if not _SHA256_PATTERN.fullmatch(value):
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringError(
            f"{field_name} is not a canonical SHA-256 identity"
        )


def _require_commit(value: str, field_name: str) -> None:
    if not _COMMIT_PATTERN.fullmatch(value):
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringError(
            f"{field_name} is not a commit identity"
        )


def _require_utc(value: str, field_name: str) -> datetime:
    if not value.endswith("Z"):
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringError(
            f"{field_name} is not UTC"
        )
    try:
        result = datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError as exc:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringError(
            f"{field_name} is not an ISO timestamp"
        ) from exc
    if result.tzinfo != UTC:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringError(
            f"{field_name} is not UTC"
        )
    return result


@dataclass(frozen=True)
class AcknowledgementMaterializationInvocationOperationCallsiteImplementationMergeValidationReceipt:
    receipt_id: str
    pr_number: int
    head_commit: str
    base_commit: str
    merge_commit: str
    merge_tree: str
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
    callsite_implementation_sha256: str
    production_callsite_present: bool
    production_callsite_executed: bool
    acknowledgement_absent: bool
    production_execution_boundary_closed: bool
    receipt_sha256: str

    @classmethod
    def from_mapping(
        cls, value: Mapping[str, object]
    ) -> AcknowledgementMaterializationInvocationOperationCallsiteImplementationMergeValidationReceipt:
        return cls(**cast(dict[str, Any], dict(value)))

    def semantic_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload.pop("receipt_sha256")
        return cast(dict[str, object], payload)

    def require(self) -> None:
        expected: dict[str, object] = {
            "receipt_id": (
                "stage3b-qwake-lc4-e-final-execution-acknowledgement-"
                "materialization-invocation-operation-callsite-implementation-"
                "post-merge-validation-v1"
            ),
            "pr_number": CALLSITE_IMPLEMENTATION_PR_NUMBER,
            "head_commit": CALLSITE_IMPLEMENTATION_HEAD_COMMIT,
            "base_commit": CALLSITE_IMPLEMENTATION_PARENT_COMMIT,
            "merge_commit": CALLSITE_IMPLEMENTATION_MERGE_COMMIT,
            "merge_tree": CALLSITE_IMPLEMENTATION_MERGE_TREE,
            "merged_at_utc": CALLSITE_IMPLEMENTATION_MERGED_AT_UTC,
            "commit_count": 1,
            "file_count": 20,
            "insertions": 2107,
            "deletions": 0,
            "focused_tests_passed": 219,
            "targeted_tests_passed": 420,
            "full_tests_passed": 1467,
            "full_test_warnings": 14,
            "required_ci_checks_total": 4,
            "required_ci_checks_passed": True,
            "callsite_implementation_sha256": CALLSITE_IMPLEMENTATION_SHA256,
            "production_callsite_present": True,
            "production_callsite_executed": False,
            "acknowledgement_absent": True,
            "production_execution_boundary_closed": True,
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringError(
                    f"callsite implementation merge receipt differs: {field_name}"
                )
        for field_name in ("head_commit", "base_commit", "merge_commit", "merge_tree"):
            _require_commit(cast(str, getattr(self, field_name)), field_name)
        _require_utc(self.merged_at_utc, "merged_at_utc")
        _require_sha256(self.callsite_implementation_sha256, "callsite_implementation_sha256")
        _require_sha256(self.receipt_sha256, "receipt_sha256")
        if self.receipt_sha256 != sha256_object(self.semantic_payload()):
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringError(
                "callsite implementation merge receipt semantic SHA-256 differs"
            )

    def canonical_json(self) -> str:
        self.require()
        return canonical_json(self)


@dataclass(frozen=True)
class FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringSource:
    execution_authoring_base_commit: str
    callsite_implementation_id: str
    callsite_implementation_sha256: str
    callsite_implementation_file_sha256: str
    callsite_implementation_merge_receipt_file_sha256: str
    callsite_implementation_package_registry_sha256: str
    callsite_implementation_source_registry_sha256: str
    callsite_implementation_callsite_sha256: str
    callsite_implementation_module_sha256: str
    callsite_implementation_verifier_sha256: str
    callsite_implementation_test_sha256: str
    callsite_implementation_historical_test_view_sha256: str
    callsite_implementation_adr_ru_sha256: str
    callsite_implementation_adr_en_sha256: str
    callsite_implementation_pr_number: int
    callsite_implementation_head_commit: str
    callsite_implementation_parent_commit: str
    callsite_implementation_merge_commit: str
    callsite_implementation_merge_tree: str
    callsite_implementation_merged_at_utc: str
    production_callsite_relative: str
    production_callsite_symbol: str
    operation_implementation_symbol: str
    execution_phrase: str
    future_execution_authorization_relative: str
    future_operation_json_relative: str
    acknowledgement_relative: str

    @classmethod
    def from_mapping(
        cls, value: Mapping[str, object]
    ) -> FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringSource:
        return cls(**cast(dict[str, Any], dict(value)))

    def require(
        self,
        receipt: AcknowledgementMaterializationInvocationOperationCallsiteImplementationMergeValidationReceipt,
    ) -> None:
        receipt.require()
        if self != _build_source(receipt):
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringError(
                "callsite execution authoring source differs"
            )


@dataclass(frozen=True)
class FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringContract:
    complete_callsite_implementation_identity_required: bool
    callsite_implementation_post_merge_verification_required: bool
    exact_production_callsite_relative_required: str
    exact_production_callsite_symbol_required: str
    exact_operation_delegate_symbol_required: str
    exact_execution_phrase_required: str
    execution_phrase_distinct_from_operation_phrase: bool
    explicit_execution_operator_identity_required: bool
    explicit_execution_authorized_at_utc_required: bool
    execution_authorization_separate: bool
    execution_authorization_post_merge_verification_required: bool
    exact_future_authorization_relative_required: str
    exact_future_operation_json_relative_required: str
    canonical_operation_json_required: bool
    operation_json_sha256_pinning_required: bool
    operation_json_materialization_separate: bool
    project_root_option_required: str
    operation_json_option_required: str
    exact_argv_required: bool
    shell_interpretation_forbidden: bool
    cwd_exact_project_root_required: bool
    execution_attempt_limit: int
    automatic_retry_forbidden: bool
    blind_retry_forbidden: bool
    exact_execution_commit_required: bool
    exact_torch2pc_commit_required: bool
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
    authoring_effects_forbidden: bool
    production_callsite_execution_forbidden: bool
    operation_performance_forbidden: bool
    authorization_consumption_forbidden: bool
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
    ) -> FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringContract:
        return cls(**cast(dict[str, Any], dict(value)))

    def require(self) -> None:
        if self != _build_contract():
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringError(
                "callsite execution authoring contract differs"
            )


@dataclass(frozen=True)
class FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringGates:
    callsite_implementation_post_merge_verified: bool
    materialization_invocation_operation_callsite_implemented: bool
    production_callsite_present: bool
    callsite_execution_contract_authored: bool
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
    ) -> FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringGates:
        return cls(**cast(dict[str, Any], dict(value)))

    def require(self) -> None:
        if self != _build_gates():
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringError(
                "callsite execution authoring gates differ"
            )


@dataclass(frozen=True)
class FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoring:
    schema_version: int
    authoring_id: str
    status: str
    recorded_at_utc: str
    source: FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringSource
    contract: FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringContract
    gates: FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringGates
    next_slice: str
    post_merge_next_slice: str
    authoring_sha256: str

    @classmethod
    def from_mapping(
        cls, value: Mapping[str, object]
    ) -> FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoring:
        payload = dict(value)
        payload["source"] = FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringSource.from_mapping(
            cast(Mapping[str, object], payload["source"])
        )
        payload["contract"] = FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringContract.from_mapping(
            cast(Mapping[str, object], payload["contract"])
        )
        payload["gates"] = FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringGates.from_mapping(
            cast(Mapping[str, object], payload["gates"])
        )
        return cls(**cast(dict[str, Any], payload))

    def semantic_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload.pop("authoring_sha256")
        return cast(dict[str, object], payload)

    def require(
        self,
        receipt: AcknowledgementMaterializationInvocationOperationCallsiteImplementationMergeValidationReceipt,
    ) -> None:
        expected: dict[str, object] = {
            "schema_version": 1,
            "authoring_id": CALLSITE_EXECUTION_AUTHORING_ID,
            "status": CALLSITE_EXECUTION_AUTHORING_STATUS,
            "recorded_at_utc": "2026-08-02T01:20:00Z",
            "next_slice": (
                "QW-LC4-E-final-execution-acknowledgement-materialization-"
                "invocation-operation-callsite-execution-authoring-commit"
            ),
            "post_merge_next_slice": (
                "QW-LC4-E-final-execution-acknowledgement-materialization-"
                "invocation-operation-callsite-execution-authorization"
            ),
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringError(
                    f"callsite execution authoring record differs: {field_name}"
                )
        if _require_utc(self.recorded_at_utc, "recorded_at_utc") <= _require_utc(
            receipt.merged_at_utc, "merged_at_utc"
        ):
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringError(
                "execution authoring timestamp is not after callsite implementation merge"
            )
        self.source.require(receipt)
        self.contract.require()
        self.gates.require()
        _require_sha256(self.authoring_sha256, "authoring_sha256")
        if self.authoring_sha256 != sha256_object(self.semantic_payload()):
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringError(
                "callsite execution authoring semantic SHA-256 differs"
            )

    def canonical_json(
        self,
        receipt: AcknowledgementMaterializationInvocationOperationCallsiteImplementationMergeValidationReceipt,
    ) -> str:
        self.require(receipt)
        return canonical_json(self)


def build_callsite_implementation_merge_validation_receipt(
) -> AcknowledgementMaterializationInvocationOperationCallsiteImplementationMergeValidationReceipt:
    provisional = AcknowledgementMaterializationInvocationOperationCallsiteImplementationMergeValidationReceipt(
        receipt_id=(
            "stage3b-qwake-lc4-e-final-execution-acknowledgement-"
            "materialization-invocation-operation-callsite-implementation-"
            "post-merge-validation-v1"
        ),
        pr_number=CALLSITE_IMPLEMENTATION_PR_NUMBER,
        head_commit=CALLSITE_IMPLEMENTATION_HEAD_COMMIT,
        base_commit=CALLSITE_IMPLEMENTATION_PARENT_COMMIT,
        merge_commit=CALLSITE_IMPLEMENTATION_MERGE_COMMIT,
        merge_tree=CALLSITE_IMPLEMENTATION_MERGE_TREE,
        merged_at_utc=CALLSITE_IMPLEMENTATION_MERGED_AT_UTC,
        commit_count=1,
        file_count=20,
        insertions=2107,
        deletions=0,
        focused_tests_passed=219,
        targeted_tests_passed=420,
        full_tests_passed=1467,
        full_test_warnings=14,
        required_ci_checks_total=4,
        required_ci_checks_passed=True,
        callsite_implementation_sha256=CALLSITE_IMPLEMENTATION_SHA256,
        production_callsite_present=True,
        production_callsite_executed=False,
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
    receipt: AcknowledgementMaterializationInvocationOperationCallsiteImplementationMergeValidationReceipt,
) -> FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringSource:
    receipt.require()
    return FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringSource(
        execution_authoring_base_commit=CALLSITE_EXECUTION_AUTHORING_BASE_COMMIT,
        callsite_implementation_id=CALLSITE_IMPLEMENTATION_ID,
        callsite_implementation_sha256=CALLSITE_IMPLEMENTATION_SHA256,
        callsite_implementation_file_sha256=CALLSITE_IMPLEMENTATION_FILE_SHA256,
        callsite_implementation_merge_receipt_file_sha256=(
            CALLSITE_IMPLEMENTATION_MERGE_RECEIPT_FILE_SHA256
        ),
        callsite_implementation_package_registry_sha256=(
            CALLSITE_IMPLEMENTATION_PACKAGE_REGISTRY_SHA256
        ),
        callsite_implementation_source_registry_sha256=(
            CALLSITE_IMPLEMENTATION_SOURCE_REGISTRY_SHA256
        ),
        callsite_implementation_callsite_sha256=(
            CALLSITE_IMPLEMENTATION_CALLSITE_SHA256
        ),
        callsite_implementation_module_sha256=CALLSITE_IMPLEMENTATION_MODULE_SHA256,
        callsite_implementation_verifier_sha256=(
            CALLSITE_IMPLEMENTATION_VERIFIER_SHA256
        ),
        callsite_implementation_test_sha256=CALLSITE_IMPLEMENTATION_TEST_SHA256,
        callsite_implementation_historical_test_view_sha256=(
            CALLSITE_IMPLEMENTATION_HISTORICAL_TEST_VIEW_SHA256
        ),
        callsite_implementation_adr_ru_sha256=CALLSITE_IMPLEMENTATION_ADR_RU_SHA256,
        callsite_implementation_adr_en_sha256=CALLSITE_IMPLEMENTATION_ADR_EN_SHA256,
        callsite_implementation_pr_number=receipt.pr_number,
        callsite_implementation_head_commit=receipt.head_commit,
        callsite_implementation_parent_commit=receipt.base_commit,
        callsite_implementation_merge_commit=receipt.merge_commit,
        callsite_implementation_merge_tree=receipt.merge_tree,
        callsite_implementation_merged_at_utc=receipt.merged_at_utc,
        production_callsite_relative=PRODUCTION_CALLSITE_RELATIVE.as_posix(),
        production_callsite_symbol=PRODUCTION_CALLSITE_SYMBOL,
        operation_implementation_symbol=OPERATION_IMPLEMENTATION_SYMBOL,
        execution_phrase=CALLSITE_EXECUTION_PHRASE,
        future_execution_authorization_relative=(
            FUTURE_EXECUTION_AUTHORIZATION_RELATIVE.as_posix()
        ),
        future_operation_json_relative=FUTURE_OPERATION_JSON_RELATIVE.as_posix(),
        acknowledgement_relative=ACKNOWLEDGEMENT_RELATIVE.as_posix(),
    )


def _build_contract(
) -> FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringContract:
    return FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringContract(
        complete_callsite_implementation_identity_required=True,
        callsite_implementation_post_merge_verification_required=True,
        exact_production_callsite_relative_required=PRODUCTION_CALLSITE_RELATIVE.as_posix(),
        exact_production_callsite_symbol_required=PRODUCTION_CALLSITE_SYMBOL,
        exact_operation_delegate_symbol_required=OPERATION_IMPLEMENTATION_SYMBOL,
        exact_execution_phrase_required=CALLSITE_EXECUTION_PHRASE,
        execution_phrase_distinct_from_operation_phrase=(
            str(CALLSITE_EXECUTION_PHRASE)
            != str(FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_OPERATION_PHRASE)
        ),
        explicit_execution_operator_identity_required=True,
        explicit_execution_authorized_at_utc_required=True,
        execution_authorization_separate=True,
        execution_authorization_post_merge_verification_required=True,
        exact_future_authorization_relative_required=(
            FUTURE_EXECUTION_AUTHORIZATION_RELATIVE.as_posix()
        ),
        exact_future_operation_json_relative_required=(
            FUTURE_OPERATION_JSON_RELATIVE.as_posix()
        ),
        canonical_operation_json_required=True,
        operation_json_sha256_pinning_required=True,
        operation_json_materialization_separate=True,
        project_root_option_required=PROJECT_ROOT_OPTION,
        operation_json_option_required=OPERATION_JSON_OPTION,
        exact_argv_required=True,
        shell_interpretation_forbidden=True,
        cwd_exact_project_root_required=True,
        execution_attempt_limit=1,
        automatic_retry_forbidden=True,
        blind_retry_forbidden=True,
        exact_execution_commit_required=True,
        exact_torch2pc_commit_required=True,
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
        authoring_effects_forbidden=True,
        production_callsite_execution_forbidden=True,
        operation_performance_forbidden=True,
        authorization_consumption_forbidden=True,
        subprocess_forbidden=True,
        docker_forbidden=True,
        image_inspection_forbidden=True,
        command_materialization_forbidden=True,
        lease_materialization_forbidden=True,
        durable_outcome_persistence_forbidden=True,
        local_compute_forbidden=True,
    )


def _build_gates(
) -> FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringGates:
    return FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringGates(
        callsite_implementation_post_merge_verified=True,
        materialization_invocation_operation_callsite_implemented=True,
        production_callsite_present=True,
        callsite_execution_contract_authored=True,
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


def build_frozen_materialization_invocation_operation_callsite_execution_authoring_record(
    receipt: AcknowledgementMaterializationInvocationOperationCallsiteImplementationMergeValidationReceipt,
) -> FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoring:
    receipt.require()
    provisional = FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoring(
        schema_version=1,
        authoring_id=CALLSITE_EXECUTION_AUTHORING_ID,
        status=CALLSITE_EXECUTION_AUTHORING_STATUS,
        recorded_at_utc="2026-08-02T01:20:00Z",
        source=_build_source(receipt),
        contract=_build_contract(),
        gates=_build_gates(),
        next_slice=(
            "QW-LC4-E-final-execution-acknowledgement-materialization-"
            "invocation-operation-callsite-execution-authoring-commit"
        ),
        post_merge_next_slice=(
            "QW-LC4-E-final-execution-acknowledgement-materialization-"
            "invocation-operation-callsite-execution-authorization"
        ),
        authoring_sha256="sha256:" + "0" * 64,
    )
    result = replace(
        provisional,
        authoring_sha256=sha256_object(provisional.semantic_payload()),
    )
    result.require(receipt)
    return result


def _verified_project_root(project_root: Path) -> Path:
    root = project_root.expanduser().resolve(strict=True)
    if not root.is_dir() or root.is_symlink():
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringError(
            "project root is absent, symbolic, or not a directory"
        )
    return root


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringError(
            f"JSON file is absent or invalid: {path}"
        )
    try:
        value = json.loads(path.read_text(encoding="utf-8", errors="strict"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringError(
            f"cannot read canonical JSON: {path}"
        ) from exc
    if not isinstance(value, dict):
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringError(
            f"canonical JSON root is not an object: {path}"
        )
    return cast(dict[str, Any], value)


def load_callsite_implementation_merge_validation_receipt(
    project_root: Path,
) -> AcknowledgementMaterializationInvocationOperationCallsiteImplementationMergeValidationReceipt:
    root = _verified_project_root(project_root)
    result = AcknowledgementMaterializationInvocationOperationCallsiteImplementationMergeValidationReceipt.from_mapping(
        _load_json(root / IMPLEMENTATION_MERGE_RECEIPT_RELATIVE)
    )
    result.require()
    return result


def load_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authoring(
    project_root: Path,
) -> FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoring:
    root = _verified_project_root(project_root)
    receipt = load_callsite_implementation_merge_validation_receipt(root)
    result = FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoring.from_mapping(
        _load_json(root / AUTHORING_RECORD_RELATIVE)
    )
    result.require(receipt)
    return result


def _load_registry(path: Path) -> dict[str, str]:
    if not path.is_file() or path.is_symlink():
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringError(
            f"registry is absent or invalid: {path}"
        )
    result: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8", errors="strict").splitlines()
    except (OSError, UnicodeError) as exc:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringError(
            f"cannot read registry: {path}"
        ) from exc
    for line in lines:
        if not line:
            continue
        parts = line.split("  ", 1)
        if len(parts) != 2 or not re.fullmatch(r"[0-9a-f]{64}", parts[0]):
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringError(
                f"invalid registry line: {line}"
            )
        if parts[1] in result:
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringError(
                f"duplicate registry path: {parts[1]}"
            )
        result[parts[1]] = parts[0]
    return result


def _verify_registry(path: Path, base: Path) -> dict[str, str]:
    registry = _load_registry(path)
    for relative, expected in registry.items():
        target = base / relative
        if not target.is_file() or target.is_symlink():
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringError(
                f"registry target is absent or invalid: {target}"
            )
        observed = sha256_bytes(target.read_bytes()).removeprefix("sha256:")
        if observed != expected:
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringError(
                f"registry target hash differs: {target}"
            )
    return registry


def _verify_authoring_ast(root: Path) -> None:
    path = root / MODULE_RELATIVE
    tree = ast.parse(path.read_text(encoding="utf-8", errors="strict"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".", 1)[0] in _FORBIDDEN_IMPORT_ROOTS:
                    raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringError(
                        f"forbidden import in execution authoring module: {alias.name}"
                    )
        elif isinstance(node, ast.ImportFrom):
            imported = node.module or ""
            if imported.split(".", 1)[0] in _FORBIDDEN_IMPORT_ROOTS:
                raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringError(
                    f"forbidden import in execution authoring module: {imported}"
                )
        elif isinstance(node, ast.Call):
            called = ""
            if isinstance(node.func, ast.Name):
                called = node.func.id
            elif isinstance(node.func, ast.Attribute):
                called = node.func.attr
            if isinstance(node.func, ast.Name) and called in _FORBIDDEN_CALL_NAMES:
                raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringError(
                    f"forbidden call in execution authoring module: {called}"
                )
            if (
                isinstance(node.func, ast.Attribute)
                and called in _FORBIDDEN_CALL_ATTRIBUTES
            ):
                raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringError(
                    f"forbidden effect in execution authoring module: {called}"
                )


def _require_production_callsite_present(root: Path) -> None:
    target = root / PRODUCTION_CALLSITE_RELATIVE
    if not target.is_file() or target.is_symlink():
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringError(
            "production operation callsite is absent or invalid"
        )
    observed = sha256_bytes(target.read_bytes())
    if observed != CALLSITE_IMPLEMENTATION_CALLSITE_SHA256:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringError(
            "production operation callsite SHA-256 differs"
        )


def _require_future_authorization_absent(root: Path) -> None:
    for relative in (
        FUTURE_EXECUTION_AUTHORIZATION_RELATIVE,
        FUTURE_OPERATION_JSON_RELATIVE,
    ):
        target = root / relative
        if target.exists() or target.is_symlink():
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringError(
                f"future execution authorization artifact already exists: {relative}"
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
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringError(
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
                raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringError(
                    f"production boundary staging artifact exists: {path.name}"
                )


def verify_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authoring(
    project_root: Path,
) -> FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoring:
    root = _verified_project_root(project_root)
    try:
        verify_final_execution_acknowledgement_materialization_invocation_operation_callsite_implementation(
            root
        )
    except Exception as exc:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringError(
            str(exc)
        ) from exc

    package = root / PACKAGE_RELATIVE
    if not package.is_dir() or package.is_symlink():
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringError(
            "callsite execution authoring package is absent or invalid"
        )
    package_files = {path.name for path in package.iterdir() if path.is_file()}
    if package_files != _EXPECTED_PACKAGE_FILES:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringError(
            "callsite execution authoring package file set differs"
        )

    package_registry = _verify_registry(package / "SHA256SUMS", package)
    if set(package_registry) != {
        "authoring.json",
        "implementation-merge-validation.json",
        "source-SHA256SUMS",
    }:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringError(
            "package registry path set differs"
        )
    source_registry = _verify_registry(package / "source-SHA256SUMS", root)
    if set(source_registry) != _EXPECTED_SOURCE_PATHS:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteExecutionAuthoringError(
            "source registry path set differs"
        )

    receipt = load_callsite_implementation_merge_validation_receipt(root)
    authoring = load_final_execution_acknowledgement_materialization_invocation_operation_callsite_execution_authoring(
        root
    )
    authoring.require(receipt)
    _verify_authoring_ast(root)
    _require_production_callsite_present(root)
    _require_future_authorization_absent(root)
    _require_production_boundary_closed(root)
    return authoring
