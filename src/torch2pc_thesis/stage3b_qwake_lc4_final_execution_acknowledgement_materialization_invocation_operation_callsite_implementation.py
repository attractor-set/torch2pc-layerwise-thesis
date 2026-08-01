"""Bounded production callsite support for acknowledgement materialization.

The module verifies the reconciled callsite-authoring evidence, loads one
canonical prospective operation file, and validates the canonical operation
result before it may be emitted by the production script. It does not invoke
the operation itself and performs no acknowledgement, lease, runtime, Docker,
or local-compute action during package verification.
"""

from __future__ import annotations

import ast
import json
import re
from collections.abc import Mapping
from dataclasses import asdict, dataclass, fields, replace
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
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_authoring import (
    ProspectiveFinalExecutionAcknowledgementMaterializationInvocation,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_authoring import (
    ProspectiveFinalExecutionAcknowledgementMaterializationInvocationOperation,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_callsite_authoring import (
    ADR_EN_RELATIVE as AUTHORING_ADR_EN_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_callsite_authoring import (
    ADR_RU_RELATIVE as AUTHORING_ADR_RU_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_callsite_authoring import (
    AUTHORING_RECORD_RELATIVE,
    CALLSITE_AUTHORING_ID,
    PRODUCTION_CALLSITE_SYMBOL,
    load_final_execution_acknowledgement_materialization_invocation_operation_callsite_authoring,
    load_operation_implementation_merge_validation_receipt,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_callsite_authoring import (
    IMPLEMENTATION_MERGE_RECEIPT_RELATIVE as AUTHORING_UPSTREAM_RECEIPT_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_callsite_authoring import (
    MODULE_RELATIVE as AUTHORING_MODULE_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_callsite_authoring import (
    REGISTRY_RELATIVE as AUTHORING_REGISTRY_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_callsite_authoring import (
    SOURCE_REGISTRY_RELATIVE as AUTHORING_SOURCE_REGISTRY_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_callsite_authoring import (
    VERIFIER_RELATIVE as AUTHORING_VERIFIER_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_implementation import (
    FUTURE_PRODUCTION_CALLSITE_RELATIVE,
    OPERATION_IMPLEMENTATION_SYMBOL,
    FinalExecutionAcknowledgementMaterializationInvocationOperationResult,
)

CALLSITE_IMPLEMENTATION_ID: Final = (
    "stage3b-qwake-lc4-e-final-execution-acknowledgement-materialization-"
    "invocation-operation-callsite-implementation-v1"
)
CALLSITE_IMPLEMENTATION_STATUS: Final = (
    "materialization_invocation_operation_callsite_implemented_not_executed_"
    "operation_not_performed_execution_closed"
)
CALLSITE_IMPLEMENTATION_BASE_COMMIT: Final = (
    "b27e252cf7c64e88d5d61bf7a23c70ffc5957959"
)
CALLSITE_AUTHORING_PR_NUMBER: Final = 162
CALLSITE_AUTHORING_HEAD_COMMIT: Final = (
    "b479320df1a0d0b09a1c6d84614de5e579084b5f"
)
CALLSITE_AUTHORING_ORIGINAL_BASE_COMMIT: Final = (
    "23a86cc0769f20b4b7536e64250f3dee062aaa62"
)
CALLSITE_AUTHORING_ACTUAL_FIRST_PARENT_COMMIT: Final = (
    "dc8dc200515959858d43b68984dbd87f27f3446c"
)
CALLSITE_AUTHORING_MERGE_COMMIT: Final = CALLSITE_IMPLEMENTATION_BASE_COMMIT
CALLSITE_AUTHORING_MERGED_AT_UTC: Final = "2026-08-01T17:22:24Z"
CALLSITE_AUTHORING_MERGE_TREE: Final = (
    "408c9cbbd97c35292ba8a9476c54d3fe0905f00e"
)
CALLSITE_AUTHORING_SHA256: Final = (
    "sha256:ccc6bf8793b8ab2405b1b9d5843fe29fb6a7a3e1d5ed37e457b97a01ab6cde7e"
)
CALLSITE_AUTHORING_FILE_SHA256: Final = (
    "sha256:e687f99f527488641d9c47e187a82ad0cc2d79acdf019c71d69ad054b6a3fe44"
)
CALLSITE_AUTHORING_UPSTREAM_RECEIPT_FILE_SHA256: Final = (
    "sha256:c835b804463a021167d2cc9ed7ff40266489eac50226753c93fd9f5ea327ee5f"
)
CALLSITE_AUTHORING_PACKAGE_REGISTRY_SHA256: Final = (
    "sha256:3ee6a4b6bb0ea2454bd306904ff44af885d41df958076964e20bbf9be66aab25"
)
CALLSITE_AUTHORING_SOURCE_REGISTRY_SHA256: Final = (
    "sha256:4064af163576c2d7c35bb0872afffb7136fbb51ffc5ebcbc7e897ee5b378e9ef"
)
CALLSITE_AUTHORING_MODULE_SHA256: Final = (
    "sha256:2482b457c5df6e6adb42722557e8b5d100285e9e40c52a53cd554887dcaabbb6"
)
CALLSITE_AUTHORING_VERIFIER_SHA256: Final = (
    "sha256:06874621db496142a7231c962ed56594f5c7816f20e4032325c76d5261daa1a6"
)
CALLSITE_AUTHORING_TEST_SHA256: Final = (
    "sha256:e1604581c2e56f5e57ea8fde17d1f2bb3762b8f9d87a778b4f1d2c5b16e20aed"
)
CALLSITE_AUTHORING_ADR_RU_SHA256: Final = (
    "sha256:9a3c1c0d2d3b87a9690b51667e12b99bbcd767523dc73e2eef0ddcb74b404323"
)
CALLSITE_AUTHORING_ADR_EN_SHA256: Final = (
    "sha256:c334ab916c32b25d10bb29c26c058c392ed4530d883f5025c75ac6ab2ce57cb8"
)

PROJECT_ROOT_OPTION: Final = "--project-root"
OPERATION_JSON_OPTION: Final = "--operation-json"

PACKAGE_RELATIVE: Final = Path(
    "experiments/frozen/stage3b-qwake-lc4-e-final-execution-"
    "acknowledgement-materialization-invocation-operation-callsite-"
    "implementation-v1"
)
IMPLEMENTATION_RECORD_RELATIVE: Final = PACKAGE_RELATIVE / "implementation.json"
AUTHORING_MERGE_RECEIPT_RELATIVE: Final = (
    PACKAGE_RELATIVE / "authoring-merge-validation.json"
)
REGISTRY_RELATIVE: Final = PACKAGE_RELATIVE / "SHA256SUMS"
SOURCE_REGISTRY_RELATIVE: Final = PACKAGE_RELATIVE / "source-SHA256SUMS"
MODULE_RELATIVE: Final = Path(
    "src/torch2pc_thesis/stage3b_qwake_lc4_final_execution_acknowledgement_"
    "materialization_invocation_operation_callsite_implementation.py"
)
PRODUCTION_CALLSITE_RELATIVE: Final = FUTURE_PRODUCTION_CALLSITE_RELATIVE
VERIFIER_RELATIVE: Final = Path(
    "scripts/verify_stage3b_qwake_lc4_final_execution_acknowledgement_"
    "materialization_invocation_operation_callsite_implementation.py"
)
TEST_RELATIVE: Final = Path(
    "tests/unit/test_stage3b_qwake_lc4_final_execution_acknowledgement_"
    "materialization_invocation_operation_callsite_implementation.py"
)
HISTORICAL_TEST_VIEW_RELATIVE: Final = Path("tests/conftest.py")
ADR_RU_RELATIVE: Final = Path(
    "docs/decisions/ADR-096-stage3b-qwake-lc4-e-final-execution-"
    "acknowledgement-materialization-invocation-operation-callsite-"
    "implementation.md"
)
ADR_EN_RELATIVE: Final = Path(
    "docs/decisions/ADR-096-stage3b-qwake-lc4-e-final-execution-"
    "acknowledgement-materialization-invocation-operation-callsite-"
    "implementation_EN.md"
)

_EXPECTED_PACKAGE_FILES: Final = frozenset(
    {
        "SHA256SUMS",
        "authoring-merge-validation.json",
        "implementation.json",
        "source-SHA256SUMS",
    }
)
_EXPECTED_SOURCE_PATHS: Final = frozenset(
    {
        AUTHORING_RECORD_RELATIVE.as_posix(),
        AUTHORING_UPSTREAM_RECEIPT_RELATIVE.as_posix(),
        AUTHORING_REGISTRY_RELATIVE.as_posix(),
        AUTHORING_SOURCE_REGISTRY_RELATIVE.as_posix(),
        AUTHORING_MODULE_RELATIVE.as_posix(),
        AUTHORING_VERIFIER_RELATIVE.as_posix(),
        AUTHORING_ADR_RU_RELATIVE.as_posix(),
        AUTHORING_ADR_EN_RELATIVE.as_posix(),
        IMPLEMENTATION_RECORD_RELATIVE.as_posix(),
        AUTHORING_MERGE_RECEIPT_RELATIVE.as_posix(),
        MODULE_RELATIVE.as_posix(),
        PRODUCTION_CALLSITE_RELATIVE.as_posix(),
        VERIFIER_RELATIVE.as_posix(),
        TEST_RELATIVE.as_posix(),
        HISTORICAL_TEST_VIEW_RELATIVE.as_posix(),
        ADR_RU_RELATIVE.as_posix(),
        ADR_EN_RELATIVE.as_posix(),
    }
)
_SHA256_PATTERN: Final = re.compile(r"^sha256:[0-9a-f]{64}$")
_COMMIT_PATTERN: Final = re.compile(r"^[0-9a-f]{40}$")
_TREE_PATTERN: Final = re.compile(r"^[0-9a-f]{40}$")
_FORBIDDEN_SCRIPT_IMPORT_ROOTS: Final = frozenset({"docker", "os", "subprocess"})
_FORBIDDEN_SCRIPT_CALL_NAMES: Final = frozenset(
    {
        "input",
        "invoke_final_execution_acknowledgement_materialization",
        "materialize_final_execution_acknowledgement",
        "persist_final_execution_acknowledgement",
        "probe_final_execution_acknowledgement_state",
        "invoke_lease_bound_host_runtime",
        "invoke_one_shot_host_runtime",
        "materialize_invocation_command",
        "persist_durable_host_outcome_receipt",
        "persist_persistent_execution_lease_v2",
    }
)

__all__ = [
    "CALLSITE_IMPLEMENTATION_ID",
    "PRODUCTION_CALLSITE_RELATIVE",
    "PRODUCTION_CALLSITE_SYMBOL",
    "PROJECT_ROOT_OPTION",
    "OPERATION_JSON_OPTION",
    "AcknowledgementMaterializationInvocationOperationCallsiteAuthoringMergeValidationReceipt",
    "FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementation",
    "FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationContract",
    "FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError",
    "FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationGates",
    "FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationSource",
    "build_callsite_authoring_merge_validation_receipt",
    "build_frozen_materialization_invocation_operation_callsite_implementation_record",
    "canonical_verified_operation_result_json",
    "load_callsite_authoring_merge_validation_receipt",
    "load_final_execution_acknowledgement_materialization_invocation_operation_callsite_implementation",
    "load_canonical_prospective_operation",
    "verify_final_execution_acknowledgement_materialization_invocation_operation_callsite_implementation",
]


class FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
    RuntimeError
):
    """Raised when the bounded production callsite fails closed."""


def _require_sha256(value: str, field_name: str) -> None:
    if not _SHA256_PATTERN.fullmatch(value):
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
            f"{field_name} is not a canonical SHA-256 identity"
        )


def _require_commit(value: str, field_name: str) -> None:
    if not _COMMIT_PATTERN.fullmatch(value):
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
            f"{field_name} is not a commit identity"
        )


def _require_tree(value: str, field_name: str) -> None:
    if not _TREE_PATTERN.fullmatch(value):
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
            f"{field_name} is not a tree identity"
        )


def _require_utc(value: str, field_name: str) -> datetime:
    if not value.endswith("Z"):
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
            f"{field_name} is not UTC"
        )
    try:
        parsed = datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError as exc:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
            f"{field_name} is not an ISO-8601 timestamp"
        ) from exc
    if parsed.tzinfo != UTC:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
            f"{field_name} is not canonical UTC"
        )
    return parsed


@dataclass(frozen=True)
class AcknowledgementMaterializationInvocationOperationCallsiteAuthoringMergeValidationReceipt:
    receipt_id: str
    pr_number: int
    head_commit: str
    original_base_commit: str
    actual_first_parent_commit: str
    merge_commit: str
    merged_at_utc: str
    merge_base_commit: str
    merge_tree: str
    commit_count: int
    file_count: int
    insertions: int
    deletions: int
    aggregate_file_count: int
    aggregate_insertions: int
    aggregate_deletions: int
    focused_tests_passed: int
    targeted_tests_passed: int
    full_tests_passed: int
    full_test_warnings: int
    required_ci_checks_total: int
    required_ci_checks_passed: bool
    automatic_merge_tree_verified: bool
    immutable_slice_blobs_verified: bool
    production_execution_boundary_closed: bool
    receipt_sha256: str

    @classmethod
    def from_mapping(
        cls, value: Mapping[str, object]
    ) -> AcknowledgementMaterializationInvocationOperationCallsiteAuthoringMergeValidationReceipt:
        return cls(**cast(dict[str, Any], dict(value)))

    def semantic_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload.pop("receipt_sha256")
        return cast(dict[str, object], payload)

    def require(self) -> None:
        expected: dict[str, object] = {
            "receipt_id": (
                "stage3b-qwake-lc4-e-final-execution-acknowledgement-"
                "materialization-invocation-operation-callsite-authoring-"
                "advanced-main-post-merge-reconciliation-v2"
            ),
            "pr_number": CALLSITE_AUTHORING_PR_NUMBER,
            "head_commit": CALLSITE_AUTHORING_HEAD_COMMIT,
            "original_base_commit": CALLSITE_AUTHORING_ORIGINAL_BASE_COMMIT,
            "actual_first_parent_commit": (
                CALLSITE_AUTHORING_ACTUAL_FIRST_PARENT_COMMIT
            ),
            "merge_commit": CALLSITE_AUTHORING_MERGE_COMMIT,
            "merged_at_utc": CALLSITE_AUTHORING_MERGED_AT_UTC,
            "merge_base_commit": CALLSITE_AUTHORING_ORIGINAL_BASE_COMMIT,
            "merge_tree": CALLSITE_AUTHORING_MERGE_TREE,
            "commit_count": 1,
            "file_count": 18,
            "insertions": 1516,
            "deletions": 0,
            "aggregate_file_count": 26,
            "aggregate_insertions": 1532,
            "aggregate_deletions": 16,
            "focused_tests_passed": 198,
            "targeted_tests_passed": 399,
            "full_tests_passed": 1446,
            "full_test_warnings": 14,
            "required_ci_checks_total": 4,
            "required_ci_checks_passed": True,
            "automatic_merge_tree_verified": True,
            "immutable_slice_blobs_verified": True,
            "production_execution_boundary_closed": True,
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
                    f"callsite authoring merge receipt differs: {field_name}"
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
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
                "callsite authoring merge receipt semantic SHA-256 differs"
            )


@dataclass(frozen=True)
class FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationSource:
    implementation_base_commit: str
    callsite_authoring_id: str
    callsite_authoring_sha256: str
    callsite_authoring_file_sha256: str
    callsite_authoring_upstream_receipt_file_sha256: str
    callsite_authoring_package_registry_sha256: str
    callsite_authoring_source_registry_sha256: str
    callsite_authoring_module_sha256: str
    callsite_authoring_verifier_sha256: str
    callsite_authoring_test_sha256: str
    callsite_authoring_adr_ru_sha256: str
    callsite_authoring_adr_en_sha256: str
    callsite_authoring_pr_number: int
    callsite_authoring_head_commit: str
    callsite_authoring_original_base_commit: str
    callsite_authoring_actual_first_parent_commit: str
    callsite_authoring_merge_commit: str
    callsite_authoring_merged_at_utc: str
    callsite_authoring_merge_tree: str
    production_callsite_relative: str
    production_callsite_symbol: str
    operation_implementation_symbol: str

    @classmethod
    def from_mapping(
        cls, value: Mapping[str, object]
    ) -> FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationSource:
        return cls(**cast(dict[str, Any], dict(value)))

    def require(
        self,
        receipt: AcknowledgementMaterializationInvocationOperationCallsiteAuthoringMergeValidationReceipt,
    ) -> None:
        receipt.require()
        if self != _build_source(receipt):
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
                "callsite implementation source differs"
            )


@dataclass(frozen=True)
class FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationContract:
    complete_callsite_authoring_identity_verified: bool
    callsite_authoring_post_merge_verification_required: bool
    exact_production_callsite_relative_required: str
    exact_production_callsite_symbol_required: str
    exact_operation_delegate_symbol_required: str
    project_root_option_required: str
    operation_json_option_required: str
    explicit_operation_file_required: bool
    canonical_prospective_operation_json_required: bool
    operation_delegate_call_limit: int
    operation_validation_before_delegate_required: bool
    operation_result_validation_required: bool
    canonical_result_stdout_required: bool
    result_file_write_forbidden: bool
    stdout_before_success_forbidden: bool
    nonzero_exit_on_failure_required: bool
    exit_zero_only_after_verified_result: bool
    stdin_operation_forbidden: bool
    environment_fallback_forbidden: bool
    interactive_prompt_forbidden: bool
    standalone_preprobe_forbidden: bool
    direct_invocation_adapter_call_forbidden: bool
    direct_materializer_call_forbidden: bool
    direct_writer_call_forbidden: bool
    automatic_retry_forbidden: bool
    blind_retry_forbidden: bool
    subprocess_forbidden: bool
    docker_forbidden: bool
    image_inspection_forbidden: bool
    command_materialization_forbidden: bool
    lease_materialization_forbidden: bool
    durable_outcome_persistence_forbidden: bool
    authorization_consumption_forbidden: bool
    local_compute_forbidden: bool
    tests_effects_isolated_only: bool
    historical_stage_verification_isolated_only: bool
    operation_performance_separate: bool

    @classmethod
    def from_mapping(
        cls, value: Mapping[str, object]
    ) -> FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationContract:
        return cls(**cast(dict[str, Any], dict(value)))

    def require(self) -> None:
        if self != _build_contract():
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
                "callsite implementation contract differs"
            )


@dataclass(frozen=True)
class FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationGates:
    callsite_authoring_post_merge_verified: bool
    materialization_invocation_operation_contract_authored: bool
    materialization_invocation_operation_implemented: bool
    materialization_invocation_operation_callsite_contract_authored: bool
    materialization_invocation_operation_callsite_implemented: bool
    production_callsite_present: bool
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
    ) -> FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationGates:
        return cls(**cast(dict[str, Any], dict(value)))

    def require(self) -> None:
        if self != _build_gates():
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
                "callsite implementation gates differ"
            )


@dataclass(frozen=True)
class FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementation:
    schema_version: int
    implementation_id: str
    status: str
    recorded_at_utc: str
    source: FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationSource
    contract: FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationContract
    gates: FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationGates
    next_slice: str
    post_merge_next_slice: str
    implementation_sha256: str

    @classmethod
    def from_mapping(
        cls, value: Mapping[str, object]
    ) -> FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementation:
        payload = dict(value)
        payload["source"] = FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationSource.from_mapping(
            cast(Mapping[str, object], payload["source"])
        )
        payload["contract"] = FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationContract.from_mapping(
            cast(Mapping[str, object], payload["contract"])
        )
        payload["gates"] = FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationGates.from_mapping(
            cast(Mapping[str, object], payload["gates"])
        )
        return cls(**cast(dict[str, Any], payload))

    def semantic_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload.pop("implementation_sha256")
        return cast(dict[str, object], payload)

    def require(
        self,
        receipt: AcknowledgementMaterializationInvocationOperationCallsiteAuthoringMergeValidationReceipt,
    ) -> None:
        expected: dict[str, object] = {
            "schema_version": 1,
            "implementation_id": CALLSITE_IMPLEMENTATION_ID,
            "status": CALLSITE_IMPLEMENTATION_STATUS,
            "recorded_at_utc": "2026-08-01T17:40:00Z",
            "next_slice": (
                "QW-LC4-E-final-execution-acknowledgement-materialization-"
                "invocation-operation-callsite-implementation-commit"
            ),
            "post_merge_next_slice": (
                "QW-LC4-E-final-execution-acknowledgement-materialization-"
                "invocation-operation-callsite-execution-authoring"
            ),
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
                    f"callsite implementation record differs: {field_name}"
                )
        if _require_utc(self.recorded_at_utc, "recorded_at_utc") <= _require_utc(
            receipt.merged_at_utc, "merged_at_utc"
        ):
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
                "callsite implementation timestamp is not after authoring merge"
            )
        self.source.require(receipt)
        self.contract.require()
        self.gates.require()
        _require_sha256(self.implementation_sha256, "implementation_sha256")
        if self.implementation_sha256 != sha256_object(self.semantic_payload()):
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
                "callsite implementation semantic SHA-256 differs"
            )


def build_callsite_authoring_merge_validation_receipt(
) -> AcknowledgementMaterializationInvocationOperationCallsiteAuthoringMergeValidationReceipt:
    provisional = AcknowledgementMaterializationInvocationOperationCallsiteAuthoringMergeValidationReceipt(
        receipt_id=(
            "stage3b-qwake-lc4-e-final-execution-acknowledgement-"
            "materialization-invocation-operation-callsite-authoring-"
            "advanced-main-post-merge-reconciliation-v2"
        ),
        pr_number=CALLSITE_AUTHORING_PR_NUMBER,
        head_commit=CALLSITE_AUTHORING_HEAD_COMMIT,
        original_base_commit=CALLSITE_AUTHORING_ORIGINAL_BASE_COMMIT,
        actual_first_parent_commit=CALLSITE_AUTHORING_ACTUAL_FIRST_PARENT_COMMIT,
        merge_commit=CALLSITE_AUTHORING_MERGE_COMMIT,
        merged_at_utc=CALLSITE_AUTHORING_MERGED_AT_UTC,
        merge_base_commit=CALLSITE_AUTHORING_ORIGINAL_BASE_COMMIT,
        merge_tree=CALLSITE_AUTHORING_MERGE_TREE,
        commit_count=1,
        file_count=18,
        insertions=1516,
        deletions=0,
        aggregate_file_count=26,
        aggregate_insertions=1532,
        aggregate_deletions=16,
        focused_tests_passed=198,
        targeted_tests_passed=399,
        full_tests_passed=1446,
        full_test_warnings=14,
        required_ci_checks_total=4,
        required_ci_checks_passed=True,
        automatic_merge_tree_verified=True,
        immutable_slice_blobs_verified=True,
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
    receipt: AcknowledgementMaterializationInvocationOperationCallsiteAuthoringMergeValidationReceipt,
) -> FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationSource:
    receipt.require()
    return FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationSource(
        implementation_base_commit=CALLSITE_IMPLEMENTATION_BASE_COMMIT,
        callsite_authoring_id=CALLSITE_AUTHORING_ID,
        callsite_authoring_sha256=CALLSITE_AUTHORING_SHA256,
        callsite_authoring_file_sha256=CALLSITE_AUTHORING_FILE_SHA256,
        callsite_authoring_upstream_receipt_file_sha256=(
            CALLSITE_AUTHORING_UPSTREAM_RECEIPT_FILE_SHA256
        ),
        callsite_authoring_package_registry_sha256=(
            CALLSITE_AUTHORING_PACKAGE_REGISTRY_SHA256
        ),
        callsite_authoring_source_registry_sha256=(
            CALLSITE_AUTHORING_SOURCE_REGISTRY_SHA256
        ),
        callsite_authoring_module_sha256=CALLSITE_AUTHORING_MODULE_SHA256,
        callsite_authoring_verifier_sha256=CALLSITE_AUTHORING_VERIFIER_SHA256,
        callsite_authoring_test_sha256=CALLSITE_AUTHORING_TEST_SHA256,
        callsite_authoring_adr_ru_sha256=CALLSITE_AUTHORING_ADR_RU_SHA256,
        callsite_authoring_adr_en_sha256=CALLSITE_AUTHORING_ADR_EN_SHA256,
        callsite_authoring_pr_number=receipt.pr_number,
        callsite_authoring_head_commit=receipt.head_commit,
        callsite_authoring_original_base_commit=receipt.original_base_commit,
        callsite_authoring_actual_first_parent_commit=(
            receipt.actual_first_parent_commit
        ),
        callsite_authoring_merge_commit=receipt.merge_commit,
        callsite_authoring_merged_at_utc=receipt.merged_at_utc,
        callsite_authoring_merge_tree=receipt.merge_tree,
        production_callsite_relative=PRODUCTION_CALLSITE_RELATIVE.as_posix(),
        production_callsite_symbol=PRODUCTION_CALLSITE_SYMBOL,
        operation_implementation_symbol=OPERATION_IMPLEMENTATION_SYMBOL,
    )


def _build_contract(
) -> FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationContract:
    return FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationContract(
        complete_callsite_authoring_identity_verified=True,
        callsite_authoring_post_merge_verification_required=True,
        exact_production_callsite_relative_required=(
            PRODUCTION_CALLSITE_RELATIVE.as_posix()
        ),
        exact_production_callsite_symbol_required=PRODUCTION_CALLSITE_SYMBOL,
        exact_operation_delegate_symbol_required=OPERATION_IMPLEMENTATION_SYMBOL,
        project_root_option_required=PROJECT_ROOT_OPTION,
        operation_json_option_required=OPERATION_JSON_OPTION,
        explicit_operation_file_required=True,
        canonical_prospective_operation_json_required=True,
        operation_delegate_call_limit=1,
        operation_validation_before_delegate_required=True,
        operation_result_validation_required=True,
        canonical_result_stdout_required=True,
        result_file_write_forbidden=True,
        stdout_before_success_forbidden=True,
        nonzero_exit_on_failure_required=True,
        exit_zero_only_after_verified_result=True,
        stdin_operation_forbidden=True,
        environment_fallback_forbidden=True,
        interactive_prompt_forbidden=True,
        standalone_preprobe_forbidden=True,
        direct_invocation_adapter_call_forbidden=True,
        direct_materializer_call_forbidden=True,
        direct_writer_call_forbidden=True,
        automatic_retry_forbidden=True,
        blind_retry_forbidden=True,
        subprocess_forbidden=True,
        docker_forbidden=True,
        image_inspection_forbidden=True,
        command_materialization_forbidden=True,
        lease_materialization_forbidden=True,
        durable_outcome_persistence_forbidden=True,
        authorization_consumption_forbidden=True,
        local_compute_forbidden=True,
        tests_effects_isolated_only=True,
        historical_stage_verification_isolated_only=True,
        operation_performance_separate=True,
    )


def _build_gates(
) -> FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationGates:
    return FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationGates(
        callsite_authoring_post_merge_verified=True,
        materialization_invocation_operation_contract_authored=True,
        materialization_invocation_operation_implemented=True,
        materialization_invocation_operation_callsite_contract_authored=True,
        materialization_invocation_operation_callsite_implemented=True,
        production_callsite_present=True,
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


def build_frozen_materialization_invocation_operation_callsite_implementation_record(
    receipt: AcknowledgementMaterializationInvocationOperationCallsiteAuthoringMergeValidationReceipt,
) -> FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementation:
    provisional = FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementation(
        schema_version=1,
        implementation_id=CALLSITE_IMPLEMENTATION_ID,
        status=CALLSITE_IMPLEMENTATION_STATUS,
        recorded_at_utc="2026-08-01T17:40:00Z",
        source=_build_source(receipt),
        contract=_build_contract(),
        gates=_build_gates(),
        next_slice=(
            "QW-LC4-E-final-execution-acknowledgement-materialization-"
            "invocation-operation-callsite-implementation-commit"
        ),
        post_merge_next_slice=(
            "QW-LC4-E-final-execution-acknowledgement-materialization-"
            "invocation-operation-callsite-execution-authoring"
        ),
        implementation_sha256="sha256:" + "0" * 64,
    )
    result = replace(
        provisional,
        implementation_sha256=sha256_object(provisional.semantic_payload()),
    )
    result.require(receipt)
    return result


def _verified_project_root(project_root: Path) -> Path:
    root = project_root.expanduser().resolve(strict=True)
    if not root.is_dir():
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
            "project root is not a directory"
        )
    return root


def _load_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8", errors="strict"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
            f"cannot read canonical JSON object: {path}"
        ) from exc
    if not isinstance(value, dict):
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
            f"canonical JSON root is not an object: {path}"
        )
    return cast(dict[str, Any], value)


def load_callsite_authoring_merge_validation_receipt(
    project_root: Path,
) -> AcknowledgementMaterializationInvocationOperationCallsiteAuthoringMergeValidationReceipt:
    root = _verified_project_root(project_root)
    result = AcknowledgementMaterializationInvocationOperationCallsiteAuthoringMergeValidationReceipt.from_mapping(
        _load_json_object(root / AUTHORING_MERGE_RECEIPT_RELATIVE)
    )
    result.require()
    return result


def load_final_execution_acknowledgement_materialization_invocation_operation_callsite_implementation(
    project_root: Path,
) -> FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementation:
    root = _verified_project_root(project_root)
    receipt = load_callsite_authoring_merge_validation_receipt(root)
    result = FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementation.from_mapping(
        _load_json_object(root / IMPLEMENTATION_RECORD_RELATIVE)
    )
    result.require(receipt)
    return result


def _require_exact_keys(
    value: Mapping[str, object], expected: frozenset[str], field_name: str
) -> None:
    observed = frozenset(value)
    if observed != expected:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
            f"{field_name} field set differs"
        )


def load_canonical_prospective_operation(
    project_root: Path, operation_json: Path
) -> ProspectiveFinalExecutionAcknowledgementMaterializationInvocationOperation:
    root = _verified_project_root(project_root)
    candidate = operation_json.expanduser()
    unresolved = candidate if candidate.is_absolute() else root / candidate
    if unresolved.is_symlink():
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
            "operation JSON path is not a regular non-symlink file"
        )
    try:
        path = unresolved.resolve(strict=True)
    except OSError as exc:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
            "operation JSON file is absent"
        ) from exc
    if not path.is_file() or path.is_symlink():
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
            "operation JSON path is not a regular non-symlink file"
        )
    try:
        text = path.read_text(encoding="utf-8", errors="strict")
        payload = json.loads(text)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
            "operation JSON is unreadable or invalid"
        ) from exc
    if not isinstance(payload, dict):
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
            "operation JSON root is not an object"
        )
    if canonical_json(payload) != text:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
            "operation JSON is not canonical"
        )
    operation_keys = frozenset(
        field.name
        for field in fields(
            ProspectiveFinalExecutionAcknowledgementMaterializationInvocationOperation
        )
    )
    invocation_keys = frozenset(
        field.name
        for field in fields(
            ProspectiveFinalExecutionAcknowledgementMaterializationInvocation
        )
    )
    _require_exact_keys(payload, operation_keys, "operation")
    invocation_payload = payload.get("invocation")
    if not isinstance(invocation_payload, dict):
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
            "operation invocation is not an object"
        )
    _require_exact_keys(invocation_payload, invocation_keys, "operation invocation")
    try:
        invocation = ProspectiveFinalExecutionAcknowledgementMaterializationInvocation(
            **cast(dict[str, Any], invocation_payload)
        )
        operation_payload = dict(payload)
        operation_payload["invocation"] = invocation
        operation = ProspectiveFinalExecutionAcknowledgementMaterializationInvocationOperation(
            **cast(dict[str, Any], operation_payload)
        )
    except TypeError as exc:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
            "operation JSON structure differs"
        ) from exc
    if canonical_json(operation) != text:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
            "operation JSON does not round-trip canonically"
        )
    return operation


def canonical_verified_operation_result_json(
    result: FinalExecutionAcknowledgementMaterializationInvocationOperationResult,
) -> str:
    expected: dict[str, object] = {
        "operation_performed": True,
        "invocation_adapter_called": True,
        "adapter_call_count": 1,
        "standalone_preprobe_performed": False,
        "direct_materializer_call_performed": False,
        "direct_writer_call_performed": False,
        "automatic_retry_performed": False,
        "blind_retry_performed": False,
        "final_execution_acknowledgement_issued": True,
        "final_execution_acknowledged": True,
        "one_shot_engineering_invocation_permitted": False,
        "execution_lease_materialized": False,
        "durable_host_outcome_present": False,
        "authorization_consumed": False,
    }
    for field_name, expected_value in expected.items():
        if getattr(result, field_name) != expected_value:
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
                f"operation result differs: {field_name}"
            )
    if result.outcome not in {"materialized", "valid_existing"}:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
            "operation result outcome differs"
        )
    invocation_result = result.invocation_result
    if invocation_result.outcome != result.outcome:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
            "operation and invocation result outcomes differ"
        )
    if invocation_result.automatic_retry_performed:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
            "invocation result contains automatic retry"
        )
    if invocation_result.blind_retry_performed:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
            "invocation result contains blind retry"
        )
    return canonical_json(result)


def _load_registry(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8", errors="strict").splitlines()
    except (OSError, UnicodeError) as exc:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
            f"cannot read registry: {path}"
        ) from exc
    for line in lines:
        if not line:
            continue
        parts = line.split("  ", 1)
        if len(parts) != 2 or not re.fullmatch(r"[0-9a-f]{64}", parts[0]):
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
                f"invalid registry line: {line}"
            )
        if parts[1] in result:
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
                f"duplicate registry path: {parts[1]}"
            )
        result[parts[1]] = parts[0]
    return result


def _verify_registry(path: Path, base: Path) -> dict[str, str]:
    registry = _load_registry(path)
    for relative, expected in registry.items():
        target = base / relative
        if not target.is_file() or target.is_symlink():
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
                f"registry target is absent or invalid: {target}"
            )
        if sha256_bytes(target.read_bytes()).removeprefix("sha256:") != expected:
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
                f"registry target hash differs: {target}"
            )
    return registry


def _verify_upstream_authoring_identity(root: Path) -> None:
    receipt = load_operation_implementation_merge_validation_receipt(root)
    authoring = load_final_execution_acknowledgement_materialization_invocation_operation_callsite_authoring(
        root
    )
    authoring.require(receipt)
    expected_hashes = {
        AUTHORING_RECORD_RELATIVE: CALLSITE_AUTHORING_FILE_SHA256,
        AUTHORING_UPSTREAM_RECEIPT_RELATIVE: (
            CALLSITE_AUTHORING_UPSTREAM_RECEIPT_FILE_SHA256
        ),
        AUTHORING_REGISTRY_RELATIVE: CALLSITE_AUTHORING_PACKAGE_REGISTRY_SHA256,
        AUTHORING_SOURCE_REGISTRY_RELATIVE: (
            CALLSITE_AUTHORING_SOURCE_REGISTRY_SHA256
        ),
        AUTHORING_MODULE_RELATIVE: CALLSITE_AUTHORING_MODULE_SHA256,
        AUTHORING_VERIFIER_RELATIVE: CALLSITE_AUTHORING_VERIFIER_SHA256,
        AUTHORING_ADR_RU_RELATIVE: CALLSITE_AUTHORING_ADR_RU_SHA256,
        AUTHORING_ADR_EN_RELATIVE: CALLSITE_AUTHORING_ADR_EN_SHA256,
    }
    for relative, expected in expected_hashes.items():
        target = root / relative
        if not target.is_file() or target.is_symlink():
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
                f"upstream callsite-authoring artifact is absent: {relative}"
            )
        observed = sha256_bytes(target.read_bytes())
        if observed != expected:
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
                f"upstream callsite-authoring artifact differs: {relative}"
            )
    if authoring.authoring_sha256 != CALLSITE_AUTHORING_SHA256:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
            "upstream callsite-authoring semantic identity differs"
        )


def _verify_production_callsite_ast(root: Path) -> None:
    path = root / PRODUCTION_CALLSITE_RELATIVE
    if not path.is_file() or path.is_symlink():
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
            "exact production callsite is absent or invalid"
        )
    tree = ast.parse(path.read_text(encoding="utf-8", errors="strict"))
    operation_name = OPERATION_IMPLEMENTATION_SYMBOL.rsplit(".", 1)[-1]
    operation_calls = 0
    main_found = False
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            if node.name == "main":
                main_found = True
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".", 1)[0] in _FORBIDDEN_SCRIPT_IMPORT_ROOTS:
                    raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
                        f"forbidden callsite import: {alias.name}"
                    )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module.split(".", 1)[0] in _FORBIDDEN_SCRIPT_IMPORT_ROOTS:
                raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
                    f"forbidden callsite import: {module}"
                )
        elif isinstance(node, ast.Call):
            called = ""
            if isinstance(node.func, ast.Name):
                called = node.func.id
            elif isinstance(node.func, ast.Attribute):
                called = node.func.attr
            if called == operation_name:
                operation_calls += 1
            if called in _FORBIDDEN_SCRIPT_CALL_NAMES:
                raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
                    f"forbidden callsite call: {called}"
                )
    if not main_found:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
            "production callsite main symbol is absent"
        )
    if operation_calls != 1:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
            "production callsite operation delegate count differs"
        )


def _require_operation_callsite_unique(root: Path) -> None:
    target_name = OPERATION_IMPLEMENTATION_SYMBOL.rsplit(".", 1)[-1]
    allowed = {
        PRODUCTION_CALLSITE_RELATIVE,
        Path(
            "src/torch2pc_thesis/stage3b_qwake_lc4_final_execution_"
            "acknowledgement_materialization_invocation_operation_"
            "implementation.py"
        ),
    }
    for directory in (root / "src", root / "scripts"):
        for path in directory.rglob("*.py"):
            relative = path.relative_to(root)
            if relative in allowed:
                continue
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
                    raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
                        f"unexpected operation callsite exists: {relative}"
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
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
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
                raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
                    f"production boundary staging artifact exists: {path.name}"
                )


def verify_final_execution_acknowledgement_materialization_invocation_operation_callsite_implementation(
    project_root: Path,
) -> FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementation:
    root = _verified_project_root(project_root)
    _verify_upstream_authoring_identity(root)
    package = root / PACKAGE_RELATIVE
    if not package.is_dir() or package.is_symlink():
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
            "callsite implementation package is absent or invalid"
        )
    package_files = {path.name for path in package.iterdir() if path.is_file()}
    if package_files != _EXPECTED_PACKAGE_FILES:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
            "callsite implementation package file set differs"
        )
    package_registry = _verify_registry(package / "SHA256SUMS", package)
    if set(package_registry) != {
        "authoring-merge-validation.json",
        "implementation.json",
        "source-SHA256SUMS",
    }:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
            "package registry path set differs"
        )
    source_registry = _verify_registry(package / "source-SHA256SUMS", root)
    if set(source_registry) != _EXPECTED_SOURCE_PATHS:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteImplementationError(
            "source registry path set differs"
        )
    receipt = load_callsite_authoring_merge_validation_receipt(root)
    implementation = load_final_execution_acknowledgement_materialization_invocation_operation_callsite_implementation(
        root
    )
    implementation.require(receipt)
    _verify_production_callsite_ast(root)
    _require_operation_callsite_unique(root)
    _require_production_boundary_closed(root)
    return implementation
