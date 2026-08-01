"""Effect-free authoring for the future production operation callsite.

This module freezes the exact repository path and command-line boundary of a
future production callsite for the already verified acknowledgement-
materialization invocation operation. It builds and verifies immutable records
only. It does not add the callsite, call the operation, adapter, materializer,
or writer, and it never creates acknowledgement, lease, outcome, runtime, or
local-compute evidence.
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
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_implementation import (
    AUTHORING_MERGE_RECEIPT_RELATIVE as IMPLEMENTATION_UPSTREAM_RECEIPT_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_implementation import (
    FUTURE_PRODUCTION_CALLSITE_RELATIVE,
    IMPLEMENTATION_ADR_EN_RELATIVE,
    IMPLEMENTATION_ADR_RU_RELATIVE,
    IMPLEMENTATION_MODULE_RELATIVE,
    IMPLEMENTATION_RECORD_RELATIVE,
    IMPLEMENTATION_REGISTRY_RELATIVE,
    IMPLEMENTATION_SOURCE_REGISTRY_RELATIVE,
    IMPLEMENTATION_TEST_RELATIVE,
    IMPLEMENTATION_VERIFIER_RELATIVE,
    OPERATION_IMPLEMENTATION_SYMBOL,
    verify_final_execution_acknowledgement_materialization_invocation_operation_implementation,
)

CALLSITE_AUTHORING_ID: Final = (
    "stage3b-qwake-lc4-e-final-execution-acknowledgement-materialization-"
    "invocation-operation-callsite-authoring-v1"
)
CALLSITE_AUTHORING_STATUS: Final = (
    "materialization_invocation_operation_callsite_contract_authored_"
    "not_implemented_not_performed_execution_closed"
)
CALLSITE_AUTHORING_BASE_COMMIT: Final = "23a86cc0769f20b4b7536e64250f3dee062aaa62"

OPERATION_IMPLEMENTATION_PR_NUMBER: Final = 155
OPERATION_IMPLEMENTATION_HEAD_COMMIT: Final = (
    "a9bfe779a2a9fa432cdf8d7134bb5ba135bebe12"
)
OPERATION_IMPLEMENTATION_PARENT_COMMIT: Final = (
    "5ee6d2346e558be19cfdf79e8a77b0568475bf4c"
)
OPERATION_IMPLEMENTATION_MERGE_COMMIT: Final = CALLSITE_AUTHORING_BASE_COMMIT
OPERATION_IMPLEMENTATION_MERGED_AT_UTC: Final = "2026-07-31T20:26:21Z"

OPERATION_IMPLEMENTATION_SHA256: Final = (
    "sha256:fe7c2d3ec26076fce5935a2a168502a1bfa7a1a462bbe251555884969dbe5f7e"
)
OPERATION_IMPLEMENTATION_FILE_SHA256: Final = (
    "sha256:0382abe3552c09c55379a4ddcf9d3170842802856f6bf97e039eda4367549f49"
)
OPERATION_IMPLEMENTATION_MERGE_RECEIPT_FILE_SHA256: Final = (
    "sha256:c57d044fdb4dd5e794f22b5711fd0cf47dce5f7341e416809e8418f111efc2da"
)
OPERATION_IMPLEMENTATION_PACKAGE_REGISTRY_SHA256: Final = (
    "sha256:ef7bbce0127f8cff45fbe087c28e4a2524d34f6697aef4ef0b9f649aa0bbfe1f"
)
OPERATION_IMPLEMENTATION_SOURCE_REGISTRY_SHA256: Final = (
    "sha256:fab0494cf82cecd7fadaf0f8f0dbf0e091f6aa7b4851e99c0fc62c793554e0fc"
)
OPERATION_IMPLEMENTATION_MODULE_SHA256: Final = (
    "sha256:005f43ceb11ff90d3c4ec722d3525396fc32acfd4a51f5c4e546e185bbc027b0"
)
OPERATION_IMPLEMENTATION_VERIFIER_SHA256: Final = (
    "sha256:ad01f3a164e72c5c2691155049cb304c090358a3ff6ddbf9f859925036813607"
)
OPERATION_IMPLEMENTATION_TEST_SHA256: Final = (
    "sha256:3ee292f05939e186e15d495b9370043e95229cc90d261fdc21eb9172fab6b159"
)
OPERATION_IMPLEMENTATION_ADR_RU_SHA256: Final = (
    "sha256:4bd12895965bdbb1b4c139e65c271401e8d7fe7a4813157f0555c20afae796d3"
)
OPERATION_IMPLEMENTATION_ADR_EN_SHA256: Final = (
    "sha256:ba29b308b98a90e0c65de32ec1c64b6ec8492364bfb94de3a492091f6cdeb8ce"
)

PRODUCTION_CALLSITE_SYMBOL: Final = (
    "scripts.invoke_stage3b_qwake_lc4_final_execution_acknowledgement_"
    "materialization_operation.main"
)
PROJECT_ROOT_OPTION: Final = "--project-root"
OPERATION_JSON_OPTION: Final = "--operation-json"

PACKAGE_RELATIVE: Final = Path(
    "experiments/frozen/stage3b-qwake-lc4-e-final-execution-"
    "acknowledgement-materialization-invocation-operation-callsite-authoring-v1"
)
AUTHORING_RECORD_RELATIVE: Final = PACKAGE_RELATIVE / "authoring.json"
IMPLEMENTATION_MERGE_RECEIPT_RELATIVE: Final = (
    PACKAGE_RELATIVE / "implementation-merge-validation.json"
)
REGISTRY_RELATIVE: Final = PACKAGE_RELATIVE / "SHA256SUMS"
SOURCE_REGISTRY_RELATIVE: Final = PACKAGE_RELATIVE / "source-SHA256SUMS"
MODULE_RELATIVE: Final = Path(
    "src/torch2pc_thesis/stage3b_qwake_lc4_final_execution_acknowledgement_"
    "materialization_invocation_operation_callsite_authoring.py"
)
VERIFIER_RELATIVE: Final = Path(
    "scripts/verify_stage3b_qwake_lc4_final_execution_acknowledgement_"
    "materialization_invocation_operation_callsite_authoring.py"
)
TEST_RELATIVE: Final = Path(
    "tests/unit/test_stage3b_qwake_lc4_final_execution_acknowledgement_"
    "materialization_invocation_operation_callsite_authoring.py"
)
ADR_RU_RELATIVE: Final = Path(
    "docs/decisions/ADR-095-stage3b-qwake-lc4-e-final-execution-"
    "acknowledgement-materialization-invocation-operation-callsite-authoring.md"
)
ADR_EN_RELATIVE: Final = Path(
    "docs/decisions/ADR-095-stage3b-qwake-lc4-e-final-execution-"
    "acknowledgement-materialization-invocation-operation-callsite-authoring_EN.md"
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
        IMPLEMENTATION_UPSTREAM_RECEIPT_RELATIVE.as_posix(),
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
    "CALLSITE_AUTHORING_ID",
    "PRODUCTION_CALLSITE_SYMBOL",
    "PROJECT_ROOT_OPTION",
    "OPERATION_JSON_OPTION",
    "AcknowledgementMaterializationInvocationOperationImplementationMergeValidationReceipt",
    "FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoring",
    "FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringContract",
    "FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringError",
    "FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringGates",
    "FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringSource",
    "build_frozen_materialization_invocation_operation_callsite_authoring_record",
    "build_operation_implementation_merge_validation_receipt",
    "load_final_execution_acknowledgement_materialization_invocation_operation_callsite_authoring",
    "load_operation_implementation_merge_validation_receipt",
    "verify_final_execution_acknowledgement_materialization_invocation_operation_callsite_authoring",
]


class FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringError(
    RuntimeError
):
    """Raised when the production-callsite authoring boundary fails closed."""


def _require_sha256(value: str, field_name: str) -> None:
    if not _SHA256_PATTERN.fullmatch(value):
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringError(
            f"{field_name} is not a canonical SHA-256 identity"
        )


def _require_commit(value: str, field_name: str) -> None:
    if not _COMMIT_PATTERN.fullmatch(value):
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringError(
            f"{field_name} is not a commit identity"
        )


def _require_utc(value: str, field_name: str) -> datetime:
    if not value.endswith("Z"):
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringError(
            f"{field_name} is not UTC"
        )
    try:
        parsed = datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError as exc:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringError(
            f"{field_name} is not an ISO-8601 timestamp"
        ) from exc
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringError(
            f"{field_name} is not UTC"
        )
    return parsed


@dataclass(frozen=True)
class AcknowledgementMaterializationInvocationOperationImplementationMergeValidationReceipt:
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
    ) -> AcknowledgementMaterializationInvocationOperationImplementationMergeValidationReceipt:
        return cls(**cast(dict[str, Any], dict(value)))

    def semantic_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload.pop("receipt_sha256")
        return cast(dict[str, object], payload)

    def require(self) -> None:
        expected: dict[str, object] = {
            "receipt_id": (
                "stage3b-qwake-lc4-e-final-execution-acknowledgement-"
                "materialization-invocation-operation-implementation-"
                "post-merge-validation-v1"
            ),
            "pr_number": OPERATION_IMPLEMENTATION_PR_NUMBER,
            "head_commit": OPERATION_IMPLEMENTATION_HEAD_COMMIT,
            "base_commit": OPERATION_IMPLEMENTATION_PARENT_COMMIT,
            "merge_commit": OPERATION_IMPLEMENTATION_MERGE_COMMIT,
            "merged_at_utc": OPERATION_IMPLEMENTATION_MERGED_AT_UTC,
            "commit_count": 1,
            "file_count": 18,
            "insertions": 1808,
            "deletions": 0,
            "focused_tests_passed": 180,
            "targeted_tests_passed": 381,
            "full_tests_passed": 1428,
            "full_test_warnings": 14,
            "required_ci_checks_total": 4,
            "required_ci_checks_passed": True,
            "acknowledgement_absent": True,
            "production_execution_boundary_closed": True,
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringError(
                    f"operation implementation merge receipt differs: {field_name}"
                )
        _require_commit(self.head_commit, "head_commit")
        _require_commit(self.base_commit, "base_commit")
        _require_commit(self.merge_commit, "merge_commit")
        _require_utc(self.merged_at_utc, "merged_at_utc")
        _require_sha256(self.receipt_sha256, "receipt_sha256")
        if self.receipt_sha256 != sha256_object(self.semantic_payload()):
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringError(
                "operation implementation merge receipt semantic SHA-256 differs"
            )

    def canonical_json(self) -> str:
        self.require()
        return canonical_json(self)


@dataclass(frozen=True)
class FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringSource:
    callsite_authoring_base_commit: str
    operation_implementation_id: str
    operation_implementation_sha256: str
    operation_implementation_file_sha256: str
    operation_implementation_merge_receipt_file_sha256: str
    operation_implementation_package_registry_sha256: str
    operation_implementation_source_registry_sha256: str
    operation_implementation_module_sha256: str
    operation_implementation_verifier_sha256: str
    operation_implementation_test_sha256: str
    operation_implementation_adr_ru_sha256: str
    operation_implementation_adr_en_sha256: str
    operation_implementation_pr_number: int
    operation_implementation_head_commit: str
    operation_implementation_parent_commit: str
    operation_implementation_merge_commit: str
    operation_implementation_merged_at_utc: str
    operation_implementation_symbol: str
    production_callsite_relative: str
    production_callsite_symbol: str
    operation_phrase: str
    acknowledgement_relative: str

    @classmethod
    def from_mapping(
        cls, value: Mapping[str, object]
    ) -> FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringSource:
        return cls(**cast(dict[str, Any], dict(value)))

    def require(
        self,
        receipt: AcknowledgementMaterializationInvocationOperationImplementationMergeValidationReceipt,
    ) -> None:
        receipt.require()
        if self != _build_source(receipt):
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringError(
                "operation callsite authoring source differs"
            )


@dataclass(frozen=True)
class FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringContract:
    complete_operation_implementation_identity_required: bool
    operation_implementation_post_merge_verification_required: bool
    exact_production_callsite_relative_required: str
    exact_production_callsite_symbol_required: str
    exact_operation_delegate_symbol_required: str
    exact_operation_phrase_required: str
    project_root_option_required: str
    operation_json_option_required: str
    canonical_prospective_operation_json_required: bool
    explicit_operation_file_required: bool
    stdin_operation_forbidden: bool
    environment_fallback_forbidden: bool
    interactive_prompt_forbidden: bool
    operation_delegate_call_limit: int
    standalone_preprobe_forbidden: bool
    direct_invocation_adapter_call_forbidden: bool
    direct_materializer_call_forbidden: bool
    direct_writer_call_forbidden: bool
    automatic_retry_forbidden: bool
    blind_retry_forbidden: bool
    canonical_result_stdout_required: bool
    result_file_write_forbidden: bool
    exit_zero_only_after_verified_result: bool
    nonzero_exit_on_failure_required: bool
    production_callsite_implementation_separate: bool
    operation_performance_separate: bool
    repository_production_callsite_forbidden: bool
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
    ) -> FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringContract:
        return cls(**cast(dict[str, Any], dict(value)))

    def require(self) -> None:
        if self != _build_contract():
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringError(
                "operation callsite authoring contract differs"
            )


@dataclass(frozen=True)
class FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringGates:
    operation_implementation_post_merge_verified: bool
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
    ) -> FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringGates:
        return cls(**cast(dict[str, Any], dict(value)))

    def require(self) -> None:
        if self != _build_gates():
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringError(
                "operation callsite authoring gates differ"
            )


@dataclass(frozen=True)
class FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoring:
    schema_version: int
    authoring_id: str
    status: str
    recorded_at_utc: str
    source: FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringSource
    contract: FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringContract
    gates: FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringGates
    next_slice: str
    post_merge_next_slice: str
    authoring_sha256: str

    @classmethod
    def from_mapping(
        cls, value: Mapping[str, object]
    ) -> FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoring:
        payload = dict(value)
        payload["source"] = FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringSource.from_mapping(
            cast(Mapping[str, object], payload["source"])
        )
        payload["contract"] = FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringContract.from_mapping(
            cast(Mapping[str, object], payload["contract"])
        )
        payload["gates"] = FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringGates.from_mapping(
            cast(Mapping[str, object], payload["gates"])
        )
        return cls(**cast(dict[str, Any], payload))

    def semantic_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload.pop("authoring_sha256")
        return cast(dict[str, object], payload)

    def require(
        self,
        receipt: AcknowledgementMaterializationInvocationOperationImplementationMergeValidationReceipt,
    ) -> None:
        expected: dict[str, object] = {
            "schema_version": 1,
            "authoring_id": CALLSITE_AUTHORING_ID,
            "status": CALLSITE_AUTHORING_STATUS,
            "recorded_at_utc": "2026-07-31T20:40:00Z",
            "next_slice": (
                "QW-LC4-E-final-execution-acknowledgement-materialization-"
                "invocation-operation-callsite-authoring-commit"
            ),
            "post_merge_next_slice": (
                "QW-LC4-E-final-execution-acknowledgement-materialization-"
                "invocation-operation-callsite-implementation"
            ),
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringError(
                    f"operation callsite authoring record differs: {field_name}"
                )
        if _require_utc(self.recorded_at_utc, "recorded_at_utc") <= _require_utc(
            receipt.merged_at_utc, "merged_at_utc"
        ):
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringError(
                "callsite authoring timestamp is not after operation implementation merge"
            )
        self.source.require(receipt)
        self.contract.require()
        self.gates.require()
        _require_sha256(self.authoring_sha256, "authoring_sha256")
        if self.authoring_sha256 != sha256_object(self.semantic_payload()):
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringError(
                "operation callsite authoring semantic SHA-256 differs"
            )


def build_operation_implementation_merge_validation_receipt(
) -> AcknowledgementMaterializationInvocationOperationImplementationMergeValidationReceipt:
    provisional = AcknowledgementMaterializationInvocationOperationImplementationMergeValidationReceipt(
        receipt_id=(
            "stage3b-qwake-lc4-e-final-execution-acknowledgement-"
            "materialization-invocation-operation-implementation-"
            "post-merge-validation-v1"
        ),
        pr_number=OPERATION_IMPLEMENTATION_PR_NUMBER,
        head_commit=OPERATION_IMPLEMENTATION_HEAD_COMMIT,
        base_commit=OPERATION_IMPLEMENTATION_PARENT_COMMIT,
        merge_commit=OPERATION_IMPLEMENTATION_MERGE_COMMIT,
        merged_at_utc=OPERATION_IMPLEMENTATION_MERGED_AT_UTC,
        commit_count=1,
        file_count=18,
        insertions=1808,
        deletions=0,
        focused_tests_passed=180,
        targeted_tests_passed=381,
        full_tests_passed=1428,
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
    receipt: AcknowledgementMaterializationInvocationOperationImplementationMergeValidationReceipt,
) -> FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringSource:
    receipt.require()
    return FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringSource(
        callsite_authoring_base_commit=CALLSITE_AUTHORING_BASE_COMMIT,
        operation_implementation_id=(
            "stage3b-qwake-lc4-e-final-execution-acknowledgement-"
            "materialization-invocation-operation-implementation-v1"
        ),
        operation_implementation_sha256=OPERATION_IMPLEMENTATION_SHA256,
        operation_implementation_file_sha256=OPERATION_IMPLEMENTATION_FILE_SHA256,
        operation_implementation_merge_receipt_file_sha256=(
            OPERATION_IMPLEMENTATION_MERGE_RECEIPT_FILE_SHA256
        ),
        operation_implementation_package_registry_sha256=(
            OPERATION_IMPLEMENTATION_PACKAGE_REGISTRY_SHA256
        ),
        operation_implementation_source_registry_sha256=(
            OPERATION_IMPLEMENTATION_SOURCE_REGISTRY_SHA256
        ),
        operation_implementation_module_sha256=OPERATION_IMPLEMENTATION_MODULE_SHA256,
        operation_implementation_verifier_sha256=(
            OPERATION_IMPLEMENTATION_VERIFIER_SHA256
        ),
        operation_implementation_test_sha256=OPERATION_IMPLEMENTATION_TEST_SHA256,
        operation_implementation_adr_ru_sha256=OPERATION_IMPLEMENTATION_ADR_RU_SHA256,
        operation_implementation_adr_en_sha256=OPERATION_IMPLEMENTATION_ADR_EN_SHA256,
        operation_implementation_pr_number=receipt.pr_number,
        operation_implementation_head_commit=receipt.head_commit,
        operation_implementation_parent_commit=receipt.base_commit,
        operation_implementation_merge_commit=receipt.merge_commit,
        operation_implementation_merged_at_utc=receipt.merged_at_utc,
        operation_implementation_symbol=OPERATION_IMPLEMENTATION_SYMBOL,
        production_callsite_relative=FUTURE_PRODUCTION_CALLSITE_RELATIVE.as_posix(),
        production_callsite_symbol=PRODUCTION_CALLSITE_SYMBOL,
        operation_phrase=(
            FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_OPERATION_PHRASE
        ),
        acknowledgement_relative=ACKNOWLEDGEMENT_RELATIVE.as_posix(),
    )


def _build_contract(
) -> FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringContract:
    return FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringContract(
        complete_operation_implementation_identity_required=True,
        operation_implementation_post_merge_verification_required=True,
        exact_production_callsite_relative_required=(
            FUTURE_PRODUCTION_CALLSITE_RELATIVE.as_posix()
        ),
        exact_production_callsite_symbol_required=PRODUCTION_CALLSITE_SYMBOL,
        exact_operation_delegate_symbol_required=OPERATION_IMPLEMENTATION_SYMBOL,
        exact_operation_phrase_required=(
            FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_OPERATION_PHRASE
        ),
        project_root_option_required=PROJECT_ROOT_OPTION,
        operation_json_option_required=OPERATION_JSON_OPTION,
        canonical_prospective_operation_json_required=True,
        explicit_operation_file_required=True,
        stdin_operation_forbidden=True,
        environment_fallback_forbidden=True,
        interactive_prompt_forbidden=True,
        operation_delegate_call_limit=1,
        standalone_preprobe_forbidden=True,
        direct_invocation_adapter_call_forbidden=True,
        direct_materializer_call_forbidden=True,
        direct_writer_call_forbidden=True,
        automatic_retry_forbidden=True,
        blind_retry_forbidden=True,
        canonical_result_stdout_required=True,
        result_file_write_forbidden=True,
        exit_zero_only_after_verified_result=True,
        nonzero_exit_on_failure_required=True,
        production_callsite_implementation_separate=True,
        operation_performance_separate=True,
        repository_production_callsite_forbidden=True,
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


def _build_gates(
) -> FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringGates:
    return FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringGates(
        operation_implementation_post_merge_verified=True,
        materialization_invocation_operation_contract_authored=True,
        materialization_invocation_operation_implemented=True,
        materialization_invocation_operation_callsite_contract_authored=True,
        materialization_invocation_operation_callsite_implemented=False,
        production_callsite_present=False,
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


def build_frozen_materialization_invocation_operation_callsite_authoring_record(
    receipt: AcknowledgementMaterializationInvocationOperationImplementationMergeValidationReceipt,
) -> FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoring:
    receipt.require()
    provisional = FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoring(
        schema_version=1,
        authoring_id=CALLSITE_AUTHORING_ID,
        status=CALLSITE_AUTHORING_STATUS,
        recorded_at_utc="2026-07-31T20:40:00Z",
        source=_build_source(receipt),
        contract=_build_contract(),
        gates=_build_gates(),
        next_slice=(
            "QW-LC4-E-final-execution-acknowledgement-materialization-"
            "invocation-operation-callsite-authoring-commit"
        ),
        post_merge_next_slice=(
            "QW-LC4-E-final-execution-acknowledgement-materialization-"
            "invocation-operation-callsite-implementation"
        ),
        authoring_sha256="sha256:" + "0" * 64,
    )
    result = replace(
        provisional,
        authoring_sha256=sha256_object(provisional.semantic_payload()),
    )
    result.require(receipt)
    return result


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8", errors="strict"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringError(
            f"cannot read canonical JSON: {path}"
        ) from exc
    if not isinstance(value, dict):
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringError(
            f"canonical JSON root is not an object: {path}"
        )
    return cast(dict[str, Any], value)


def load_operation_implementation_merge_validation_receipt(
    project_root: Path,
) -> AcknowledgementMaterializationInvocationOperationImplementationMergeValidationReceipt:
    root = _verified_project_root(project_root)
    result = AcknowledgementMaterializationInvocationOperationImplementationMergeValidationReceipt.from_mapping(
        _load_json(root / IMPLEMENTATION_MERGE_RECEIPT_RELATIVE)
    )
    result.require()
    return result


def load_final_execution_acknowledgement_materialization_invocation_operation_callsite_authoring(
    project_root: Path,
) -> FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoring:
    root = _verified_project_root(project_root)
    receipt = load_operation_implementation_merge_validation_receipt(root)
    result = FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoring.from_mapping(
        _load_json(root / AUTHORING_RECORD_RELATIVE)
    )
    result.require(receipt)
    return result


def _verified_project_root(project_root: Path) -> Path:
    root = project_root.resolve(strict=True)
    if not root.is_dir():
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringError(
            "project root is not a directory"
        )
    return root


def _load_registry(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8", errors="strict").splitlines()
    except (OSError, UnicodeError) as exc:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringError(
            f"cannot read registry: {path}"
        ) from exc
    for line in lines:
        if not line:
            continue
        parts = line.split("  ", 1)
        if len(parts) != 2 or not re.fullmatch(r"[0-9a-f]{64}", parts[0]):
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringError(
                f"invalid registry line: {line}"
            )
        if parts[1] in result:
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringError(
                f"duplicate registry path: {parts[1]}"
            )
        result[parts[1]] = parts[0]
    return result


def _verify_registry(path: Path, base: Path) -> dict[str, str]:
    registry = _load_registry(path)
    for relative, expected in registry.items():
        target = base / relative
        if not target.is_file() or target.is_symlink():
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringError(
                f"registry target is absent or invalid: {target}"
            )
        if sha256_bytes(target.read_bytes()).removeprefix("sha256:") != expected:
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringError(
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
                    raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringError(
                        f"forbidden import in callsite authoring module: {alias.name}"
                    )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module.split(".", 1)[0] in _FORBIDDEN_IMPORT_ROOTS:
                raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringError(
                    f"forbidden import in callsite authoring module: {module}"
                )
        elif isinstance(node, ast.Call):
            called = ""
            if isinstance(node.func, ast.Name):
                called = node.func.id
            elif isinstance(node.func, ast.Attribute):
                called = node.func.attr
            if isinstance(node.func, ast.Name) and called in _FORBIDDEN_CALL_NAMES:
                raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringError(
                    f"forbidden call in callsite authoring module: {called}"
                )
            if (
                isinstance(node.func, ast.Attribute)
                and called in _FORBIDDEN_CALL_ATTRIBUTES
            ):
                raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringError(
                    f"forbidden effect in callsite authoring module: {called}"
                )


def _require_production_callsite_absent(root: Path) -> None:
    target = root / FUTURE_PRODUCTION_CALLSITE_RELATIVE
    if target.exists() or target.is_symlink():
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringError(
            "production operation callsite already exists"
        )


def _require_repository_operation_calls_absent(root: Path) -> None:
    target_name = OPERATION_IMPLEMENTATION_SYMBOL.rsplit(".", 1)[-1]
    excluded = {
        IMPLEMENTATION_MODULE_RELATIVE,
        MODULE_RELATIVE,
    }
    for directory in (root / "src", root / "scripts"):
        for path in directory.rglob("*.py"):
            relative = path.relative_to(root)
            if relative in excluded:
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
                    raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringError(
                        f"repository operation callsite exists: {relative}"
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
            raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringError(
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
                raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringError(
                    f"production boundary staging artifact exists: {path.name}"
                )


def verify_final_execution_acknowledgement_materialization_invocation_operation_callsite_authoring(
    project_root: Path,
) -> FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoring:
    root = _verified_project_root(project_root)
    try:
        verify_final_execution_acknowledgement_materialization_invocation_operation_implementation(
            root
        )
    except Exception as exc:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringError(
            str(exc)
        ) from exc

    package = root / PACKAGE_RELATIVE
    if not package.is_dir() or package.is_symlink():
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringError(
            "callsite authoring package is absent or invalid"
        )
    package_files = {path.name for path in package.iterdir() if path.is_file()}
    if package_files != _EXPECTED_PACKAGE_FILES:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringError(
            "callsite authoring package file set differs"
        )

    package_registry = _verify_registry(package / "SHA256SUMS", package)
    if set(package_registry) != {
        "authoring.json",
        "implementation-merge-validation.json",
        "source-SHA256SUMS",
    }:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringError(
            "package registry path set differs"
        )
    source_registry = _verify_registry(package / "source-SHA256SUMS", root)
    if set(source_registry) != _EXPECTED_SOURCE_PATHS:
        raise FinalExecutionAcknowledgementMaterializationInvocationOperationCallsiteAuthoringError(
            "source registry path set differs"
        )

    receipt = load_operation_implementation_merge_validation_receipt(root)
    authoring = load_final_execution_acknowledgement_materialization_invocation_operation_callsite_authoring(
        root
    )
    authoring.require(receipt)
    _verify_authoring_ast(root)
    _require_production_callsite_absent(root)
    _require_repository_operation_calls_absent(root)
    _require_production_boundary_closed(root)
    return authoring
