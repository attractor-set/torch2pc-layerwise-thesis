"""Bounded adapter for one final-acknowledgement materializer invocation.

The module implements the library boundary frozen by ADR-091. Importing or
verifying it is effect-free. The explicit adapter probes durable state first:
an absent target may delegate exactly one call to the already verified
materializer; an exactly valid existing target is treated as completed without
a second materializer call; an invalid existing target fails closed. No
production callsite is provided here.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Final, Literal, cast

from .stage3b_qwake_lc4_final_execution_acknowledgement_authoring import (
    DURABLE_HOST_OUTCOME_RELATIVE,
    EXECUTION_LEASE_V2_RELATIVE,
    FinalExecutionAcknowledgementAuthoring,
    WiringMergeValidationReceipt,
    canonical_json,
    load_final_execution_acknowledgement_authoring,
    load_wiring_merge_validation_receipt,
    sha256_bytes,
    sha256_object,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_issuance_authoring import (
    ACKNOWLEDGEMENT_RELATIVE,
    UPSTREAM_AUTHORING_RECORD_RELATIVE,
    UPSTREAM_WIRING_RECEIPT_RELATIVE,
    AcknowledgementAuthoringMergeValidationReceipt,
    FinalExecutionAcknowledgementIssuanceAuthoring,
    load_acknowledgement_authoring_merge_validation_receipt,
    load_final_execution_acknowledgement_issuance_authoring,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_issuance_authoring import (
    AUTHORING_MERGE_RECEIPT_RELATIVE as ISSUANCE_AUTHORING_MERGE_RECEIPT_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_issuance_authoring import (
    AUTHORING_RECORD_RELATIVE as ISSUANCE_AUTHORING_RECORD_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_issuance_implementation import (
    LEGACY_EXECUTION_LEASE_RELATIVE,
    PersistentAcknowledgementWriteResult,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_issuance_implementation import (
    verify_persisted_final_execution_acknowledgement as _verify_persisted_once,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization import (
    IMPLEMENTATION_ADR_EN_RELATIVE as MATERIALIZATION_IMPLEMENTATION_ADR_EN_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization import (
    IMPLEMENTATION_ADR_RU_RELATIVE as MATERIALIZATION_IMPLEMENTATION_ADR_RU_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization import (
    IMPLEMENTATION_MODULE_RELATIVE as MATERIALIZATION_IMPLEMENTATION_MODULE_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization import (
    IMPLEMENTATION_PACKAGE_RELATIVE as MATERIALIZATION_IMPLEMENTATION_PACKAGE_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization import (
    IMPLEMENTATION_RECORD_RELATIVE as MATERIALIZATION_IMPLEMENTATION_RECORD_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization import (
    IMPLEMENTATION_REGISTRY_RELATIVE as MATERIALIZATION_IMPLEMENTATION_REGISTRY_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization import (
    IMPLEMENTATION_SOURCE_REGISTRY_RELATIVE as MATERIALIZATION_IMPLEMENTATION_SOURCE_REGISTRY_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization import (
    IMPLEMENTATION_TEST_RELATIVE as MATERIALIZATION_IMPLEMENTATION_TEST_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization import (
    IMPLEMENTATION_VERIFIER_RELATIVE as MATERIALIZATION_IMPLEMENTATION_VERIFIER_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization import (
    AcknowledgementMaterializationAuthoringMergeValidationReceipt,
    FinalExecutionAcknowledgementMaterializationImplementationRecord,
    FinalExecutionAcknowledgementMaterializationResult,
    load_acknowledgement_materialization_authoring_merge_validation_receipt,
    load_final_execution_acknowledgement_materialization_implementation_record,
    verify_final_execution_acknowledgement_materialization_implementation,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization import (
    materialize_final_execution_acknowledgement as _materialize_once,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_authoring import (
    AUTHORING_RECORD_RELATIVE as MATERIALIZATION_AUTHORING_RECORD_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_authoring import (
    IMPLEMENTATION_MERGE_RECEIPT_RELATIVE as MATERIALIZATION_AUTHORING_MERGE_RECEIPT_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_authoring import (
    AcknowledgementIssuanceImplementationMergeValidationReceipt,
    FinalExecutionAcknowledgementMaterializationAuthoring,
    ProspectiveFinalExecutionAcknowledgementMaterialization,
    load_acknowledgement_issuance_implementation_merge_validation_receipt,
    load_final_execution_acknowledgement_materialization_authoring,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_authoring import (
    build_prospective_acknowledgement_materialization as _build_prospective_materialization,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_authoring import (
    ADR_EN_RELATIVE as INVOCATION_AUTHORING_ADR_EN_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_authoring import (
    ADR_RU_RELATIVE as INVOCATION_AUTHORING_ADR_RU_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_authoring import (
    AUTHORING_RECORD_RELATIVE as INVOCATION_AUTHORING_RECORD_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_authoring import (
    IMPLEMENTATION_MERGE_RECEIPT_RELATIVE as INVOCATION_AUTHORING_IMPLEMENTATION_MERGE_RECEIPT_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_authoring import (
    MODULE_RELATIVE as INVOCATION_AUTHORING_MODULE_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_authoring import (
    REGISTRY_RELATIVE as INVOCATION_AUTHORING_REGISTRY_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_authoring import (
    SOURCE_REGISTRY_RELATIVE as INVOCATION_AUTHORING_SOURCE_REGISTRY_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_authoring import (
    TEST_RELATIVE as INVOCATION_AUTHORING_TEST_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_authoring import (
    VERIFIER_RELATIVE as INVOCATION_AUTHORING_VERIFIER_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_authoring import (
    AcknowledgementMaterializationImplementationMergeValidationReceipt,
    FinalExecutionAcknowledgementMaterializationInvocationAuthoring,
    ProspectiveFinalExecutionAcknowledgementMaterializationInvocation,
    load_final_execution_acknowledgement_materialization_invocation_authoring,
    load_materialization_implementation_merge_validation_receipt,
    verify_final_execution_acknowledgement_materialization_invocation_authoring,
)

FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_IMPLEMENTATION_ID: Final = (
    "stage3b-qwake-lc4-e-final-execution-acknowledgement-materialization-"
    "invocation-implementation-v1"
)
FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_IMPLEMENTATION_STATUS: Final = (
    "materialization_invocation_adapter_implemented_not_called_execution_closed"
)
IMPLEMENTATION_BASE_COMMIT: Final = "febfba65d2f200fd2163928643eadd807a6b4d21"
AUTHORING_PR_NUMBER: Final = 152
AUTHORING_HEAD_COMMIT: Final = "8411b80ee6c088c219f34973f84379c653b1626e"
AUTHORING_PARENT_COMMIT: Final = "7d5e5058af6a845cf4a6add2e7fe199894f48b24"
AUTHORING_MERGE_COMMIT: Final = IMPLEMENTATION_BASE_COMMIT
AUTHORING_MERGED_AT_UTC: Final = "2026-07-31T01:12:05Z"

INVOCATION_AUTHORING_SHA256: Final = (
    "sha256:132a5dc5770f12e240aabc08e1a3ae483b7208c77cd6bc782a1d06d39e20931d"
)
INVOCATION_AUTHORING_FILE_SHA256: Final = (
    "sha256:e511ee5eea68e392368ab0977ab21b19c238da5bdcca96c7244e146fdfac5dcb"
)
INVOCATION_AUTHORING_IMPLEMENTATION_RECEIPT_FILE_SHA256: Final = (
    "sha256:0898b07eea6c416008856e27285fef3e34a3329584e85589bf5d9b963a68b185"
)
INVOCATION_AUTHORING_PACKAGE_REGISTRY_SHA256: Final = (
    "sha256:08d2c47e6a14dfca7a27e17cf92822bce96e9675be976d63573b3499165f4fd2"
)
INVOCATION_AUTHORING_SOURCE_REGISTRY_SHA256: Final = (
    "sha256:e37f8bf3856979b0a590b6a8c3a3db7d64c0df25c8a5152df22ee3b812df11a9"
)
INVOCATION_AUTHORING_MODULE_SHA256: Final = (
    "sha256:792ad78dc71afd378e299ba0b91f9840c6271696e1a5509417e01ac899c2bccd"
)
INVOCATION_AUTHORING_VERIFIER_SHA256: Final = (
    "sha256:77baec61f5ada233d99d427c10ac8834a2456e90fa980775c8742c3bbad16fd5"
)
INVOCATION_AUTHORING_TEST_SHA256: Final = (
    "sha256:f09572b537266df0df9b4e2d368aebf96621de58f02a28b900fbde420a4cf850"
)
INVOCATION_AUTHORING_ADR_RU_SHA256: Final = (
    "sha256:539e3ddeeb645ec6bfaba4286a0ec084274ce2b9883dec3bfa5e7e1ef45c3917"
)
INVOCATION_AUTHORING_ADR_EN_SHA256: Final = (
    "sha256:719aa0b7b7a9f2c3c418b5c19b11bb9a5e982569e194f6eefc4a929f2937d468"
)

MATERIALIZATION_IMPLEMENTATION_SHA256: Final = (
    "sha256:6151ec4a3e117fec5560626069d6820c89805858a087cc65d18746f8bb0912cd"
)
PROSPECTIVE_BUILDER_SYMBOL: Final = (
    "torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_"
    "materialization_authoring.build_prospective_acknowledgement_materialization"
)
MATERIALIZER_SYMBOL: Final = (
    "torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_"
    "materialization.materialize_final_execution_acknowledgement"
)
PERSISTED_VERIFIER_SYMBOL: Final = (
    "torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_"
    "issuance_implementation.verify_persisted_final_execution_acknowledgement"
)
WRITER_SYMBOL: Final = (
    "torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_"
    "issuance_implementation.persist_final_execution_acknowledgement"
)

IMPLEMENTATION_PACKAGE_RELATIVE: Final = Path(
    "experiments/frozen/stage3b-qwake-lc4-e-final-execution-acknowledgement-"
    "materialization-invocation-implementation-v1"
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
    "materialization_invocation.py"
)
IMPLEMENTATION_VERIFIER_RELATIVE: Final = Path(
    "scripts/verify_stage3b_qwake_lc4_final_execution_acknowledgement_"
    "materialization_invocation.py"
)
IMPLEMENTATION_TEST_RELATIVE: Final = Path(
    "tests/unit/test_stage3b_qwake_lc4_final_execution_acknowledgement_"
    "materialization_invocation.py"
)
IMPLEMENTATION_ADR_RU_RELATIVE: Final = Path(
    "docs/decisions/ADR-092-stage3b-qwake-lc4-e-final-execution-"
    "acknowledgement-materialization-invocation-implementation.md"
)
IMPLEMENTATION_ADR_EN_RELATIVE: Final = Path(
    "docs/decisions/ADR-092-stage3b-qwake-lc4-e-final-execution-"
    "acknowledgement-materialization-invocation-implementation_EN.md"
)

_EXPECTED_PACKAGE_FILES: Final = frozenset(
    {"SHA256SUMS", "authoring-merge-validation.json", "implementation.json", "source-SHA256SUMS"}
)
_EXPECTED_SOURCE_PATHS: Final = frozenset(
    {
        INVOCATION_AUTHORING_RECORD_RELATIVE.as_posix(),
        INVOCATION_AUTHORING_IMPLEMENTATION_MERGE_RECEIPT_RELATIVE.as_posix(),
        INVOCATION_AUTHORING_REGISTRY_RELATIVE.as_posix(),
        INVOCATION_AUTHORING_SOURCE_REGISTRY_RELATIVE.as_posix(),
        INVOCATION_AUTHORING_MODULE_RELATIVE.as_posix(),
        INVOCATION_AUTHORING_VERIFIER_RELATIVE.as_posix(),
        INVOCATION_AUTHORING_TEST_RELATIVE.as_posix(),
        INVOCATION_AUTHORING_ADR_RU_RELATIVE.as_posix(),
        INVOCATION_AUTHORING_ADR_EN_RELATIVE.as_posix(),
        MATERIALIZATION_IMPLEMENTATION_RECORD_RELATIVE.as_posix(),
        (
            MATERIALIZATION_IMPLEMENTATION_PACKAGE_RELATIVE
            / "authoring-merge-validation.json"
        ).as_posix(),
        MATERIALIZATION_IMPLEMENTATION_REGISTRY_RELATIVE.as_posix(),
        MATERIALIZATION_IMPLEMENTATION_SOURCE_REGISTRY_RELATIVE.as_posix(),
        MATERIALIZATION_IMPLEMENTATION_MODULE_RELATIVE.as_posix(),
        MATERIALIZATION_IMPLEMENTATION_VERIFIER_RELATIVE.as_posix(),
        MATERIALIZATION_IMPLEMENTATION_TEST_RELATIVE.as_posix(),
        MATERIALIZATION_IMPLEMENTATION_ADR_RU_RELATIVE.as_posix(),
        MATERIALIZATION_IMPLEMENTATION_ADR_EN_RELATIVE.as_posix(),
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
_FORBIDDEN_RUNTIME_CALLS: Final = frozenset(
    {
        "invoke_lease_bound_host_runtime",
        "invoke_one_shot_host_runtime",
        "materialize_invocation_command",
        "persist_durable_host_outcome_receipt",
        "persist_final_execution_acknowledgement",
        "persist_persistent_execution_lease_v2",
    }
)

__all__ = [
    "FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_IMPLEMENTATION_ID",
    "AcknowledgementMaterializationInvocationAuthoringMergeValidationReceipt",
    "AcknowledgementMaterializationInvocationImplementationError",
    "AcknowledgementMaterializationRecoveryProbe",
    "FinalExecutionAcknowledgementMaterializationInvocationImplementationRecord",
    "FinalExecutionAcknowledgementMaterializationInvocationResult",
    "build_authoring_merge_validation_receipt",
    "build_frozen_materialization_invocation_implementation_record",
    "invoke_final_execution_acknowledgement_materialization",
    "load_authoring_merge_validation_receipt",
    "load_materialization_invocation_implementation_record",
    "probe_final_execution_acknowledgement_state",
    "verify_final_execution_acknowledgement_materialization_invocation_implementation",
]


class AcknowledgementMaterializationInvocationImplementationError(RuntimeError):
    """Raised when the invocation adapter or its freeze fails closed."""


def _require_sha256(value: str, field_name: str) -> None:
    if not _SHA256_PATTERN.fullmatch(value):
        raise AcknowledgementMaterializationInvocationImplementationError(
            f"{field_name} is not a canonical SHA-256 identity"
        )


def _require_commit(value: str, field_name: str) -> None:
    if not _COMMIT_PATTERN.fullmatch(value):
        raise AcknowledgementMaterializationInvocationImplementationError(
            f"{field_name} is not a commit identity"
        )


@dataclass(frozen=True)
class AcknowledgementMaterializationInvocationAuthoringMergeValidationReceipt:
    """Exact independent post-merge receipt for invocation-authoring PR #152."""

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
    required_ci_check_count: int
    acknowledgement_absent: bool
    production_execution_boundary_closed: bool
    receipt_sha256: str

    @classmethod
    def from_mapping(
        cls, value: Mapping[str, object]
    ) -> AcknowledgementMaterializationInvocationAuthoringMergeValidationReceipt:
        return cls(**cast(dict[str, Any], dict(value)))

    def semantic_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload.pop("receipt_sha256")
        return cast(dict[str, object], payload)

    def require(self) -> None:
        expected: dict[str, object] = {
            "receipt_id": (
                "stage3b-qwake-lc4-e-final-execution-acknowledgement-"
                "materialization-invocation-authoring-post-merge-validation-v1"
            ),
            "pr_number": AUTHORING_PR_NUMBER,
            "head_commit": AUTHORING_HEAD_COMMIT,
            "base_commit": AUTHORING_PARENT_COMMIT,
            "merge_commit": AUTHORING_MERGE_COMMIT,
            "merged_at_utc": AUTHORING_MERGED_AT_UTC,
            "commit_count": 1,
            "file_count": 18,
            "focused_tests_passed": 124,
            "targeted_tests_passed": 325,
            "full_tests_passed": 1372,
            "full_test_warnings": 14,
            "required_ci_checks_passed": True,
            "required_ci_check_count": 4,
            "acknowledgement_absent": True,
            "production_execution_boundary_closed": True,
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise AcknowledgementMaterializationInvocationImplementationError(
                    f"invocation-authoring merge receipt differs: {field_name}"
                )
        for field_name in ("head_commit", "base_commit", "merge_commit"):
            _require_commit(cast(str, getattr(self, field_name)), field_name)
        _require_sha256(self.receipt_sha256, "receipt_sha256")
        if self.receipt_sha256 != sha256_object(self.semantic_payload()):
            raise AcknowledgementMaterializationInvocationImplementationError(
                "invocation-authoring merge receipt semantic SHA-256 differs"
            )

    def canonical_json(self) -> str:
        self.require()
        return canonical_json(self)


@dataclass(frozen=True)
class FinalExecutionAcknowledgementMaterializationInvocationImplementationSource:
    implementation_base_commit: str
    invocation_authoring_id: str
    invocation_authoring_sha256: str
    invocation_authoring_file_sha256: str
    invocation_authoring_implementation_receipt_file_sha256: str
    invocation_authoring_package_registry_sha256: str
    invocation_authoring_source_registry_sha256: str
    invocation_authoring_module_sha256: str
    invocation_authoring_verifier_sha256: str
    invocation_authoring_test_sha256: str
    invocation_authoring_adr_ru_sha256: str
    invocation_authoring_adr_en_sha256: str
    invocation_authoring_pr_number: int
    invocation_authoring_head_commit: str
    invocation_authoring_parent_commit: str
    invocation_authoring_merge_commit: str
    invocation_authoring_merged_at_utc: str
    materialization_implementation_sha256: str
    prospective_builder_symbol: str
    materializer_symbol: str
    persisted_verifier_symbol: str
    writer_symbol: str
    acknowledgement_relative: str

    @classmethod
    def from_mapping(
        cls, value: Mapping[str, object]
    ) -> FinalExecutionAcknowledgementMaterializationInvocationImplementationSource:
        return cls(**cast(dict[str, Any], dict(value)))

    def require(
        self, receipt: AcknowledgementMaterializationInvocationAuthoringMergeValidationReceipt
    ) -> None:
        receipt.require()
        if self != _build_source(receipt):
            raise AcknowledgementMaterializationInvocationImplementationError(
                "materialization invocation implementation source differs"
            )


@dataclass(frozen=True)
class FinalExecutionAcknowledgementMaterializationInvocationImplementationContract:
    complete_invocation_authoring_identity_verified: bool
    invocation_authoring_post_merge_verification_required: bool
    exact_prospective_builder_delegate_required: bool
    exact_materializer_delegate_required: bool
    exact_existing_target_verifier_delegate_required: bool
    recovery_state_probe_before_materializer_required: bool
    materializer_call_limit: int
    persisted_verifier_call_limit: int
    direct_writer_call_forbidden: bool
    automatic_retry_forbidden: bool
    blind_retry_forbidden: bool
    explicit_recovery_permitted: bool
    absent_target_requires_new_explicit_authorization: bool
    valid_existing_target_treated_as_success: bool
    valid_existing_target_materializer_call_forbidden: bool
    invalid_existing_target_fail_closed: bool
    materializer_failure_propagated_without_retry: bool
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
    ) -> FinalExecutionAcknowledgementMaterializationInvocationImplementationContract:
        return cls(**cast(dict[str, Any], dict(value)))

    def require(self) -> None:
        if self != _build_contract():
            raise AcknowledgementMaterializationInvocationImplementationError(
                "materialization invocation implementation contract differs"
            )


@dataclass(frozen=True)
class FinalExecutionAcknowledgementMaterializationInvocationImplementationGates:
    invocation_authoring_post_merge_verified: bool
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
        cls, value: Mapping[str, object]
    ) -> FinalExecutionAcknowledgementMaterializationInvocationImplementationGates:
        return cls(**cast(dict[str, Any], dict(value)))

    def require(self) -> None:
        if self != _build_gates():
            raise AcknowledgementMaterializationInvocationImplementationError(
                "materialization invocation implementation gates differ"
            )


@dataclass(frozen=True)
class FinalExecutionAcknowledgementMaterializationInvocationImplementationRecord:
    schema_version: int
    implementation_id: str
    status: str
    recorded_at_utc: str
    source: FinalExecutionAcknowledgementMaterializationInvocationImplementationSource
    contract: FinalExecutionAcknowledgementMaterializationInvocationImplementationContract
    gates: FinalExecutionAcknowledgementMaterializationInvocationImplementationGates
    next_slice: str
    post_merge_next_slice: str
    implementation_sha256: str

    @classmethod
    def from_mapping(
        cls, value: Mapping[str, object]
    ) -> FinalExecutionAcknowledgementMaterializationInvocationImplementationRecord:
        payload = dict(value)
        payload["source"] = FinalExecutionAcknowledgementMaterializationInvocationImplementationSource.from_mapping(
            cast(Mapping[str, object], payload["source"])
        )
        payload["contract"] = FinalExecutionAcknowledgementMaterializationInvocationImplementationContract.from_mapping(
            cast(Mapping[str, object], payload["contract"])
        )
        payload["gates"] = FinalExecutionAcknowledgementMaterializationInvocationImplementationGates.from_mapping(
            cast(Mapping[str, object], payload["gates"])
        )
        return cls(**cast(dict[str, Any], payload))

    def semantic_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload.pop("implementation_sha256")
        return cast(dict[str, object], payload)

    def require(
        self, receipt: AcknowledgementMaterializationInvocationAuthoringMergeValidationReceipt
    ) -> None:
        expected: dict[str, object] = {
            "schema_version": 1,
            "implementation_id": FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_IMPLEMENTATION_ID,
            "status": FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_IMPLEMENTATION_STATUS,
            "recorded_at_utc": "2026-07-31T01:25:00Z",
            "next_slice": (
                "QW-LC4-E-final-execution-acknowledgement-materialization-"
                "invocation-implementation-commit"
            ),
            "post_merge_next_slice": (
                "QW-LC4-E-final-execution-acknowledgement-materialization-"
                "invocation-operation-authoring"
            ),
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise AcknowledgementMaterializationInvocationImplementationError(
                    f"materialization invocation implementation differs: {field_name}"
                )
        self.source.require(receipt)
        self.contract.require()
        self.gates.require()
        _require_sha256(self.implementation_sha256, "implementation_sha256")
        if self.implementation_sha256 != sha256_object(self.semantic_payload()):
            raise AcknowledgementMaterializationInvocationImplementationError(
                "materialization invocation implementation semantic SHA-256 differs"
            )

    def canonical_json(
        self, receipt: AcknowledgementMaterializationInvocationAuthoringMergeValidationReceipt
    ) -> str:
        self.require(receipt)
        return canonical_json(self)


@dataclass(frozen=True)
class AcknowledgementMaterializationRecoveryProbe:
    """Effect-free classification of the exact acknowledgement target."""

    state: Literal["absent", "valid_existing"]
    acknowledgement_relative: str
    target_present: bool
    exact_existing_bytes_verified: bool
    materializer_call_permitted: bool
    materializer_recall_forbidden: bool
    explicit_recovery_required: bool

    def require(self) -> None:
        expected_common = {
            "acknowledgement_relative": ACKNOWLEDGEMENT_RELATIVE.as_posix(),
            "explicit_recovery_required": True,
        }
        for field_name, expected_value in expected_common.items():
            if getattr(self, field_name) != expected_value:
                raise AcknowledgementMaterializationInvocationImplementationError(
                    f"recovery probe differs: {field_name}"
                )
        if self.state == "absent":
            expected = (False, False, True, False)
        elif self.state == "valid_existing":
            expected = (True, True, False, True)
        else:
            raise AcknowledgementMaterializationInvocationImplementationError(
                "recovery probe state differs"
            )
        observed = (
            self.target_present,
            self.exact_existing_bytes_verified,
            self.materializer_call_permitted,
            self.materializer_recall_forbidden,
        )
        if observed != expected:
            raise AcknowledgementMaterializationInvocationImplementationError(
                "recovery probe classification differs"
            )


@dataclass(frozen=True)
class FinalExecutionAcknowledgementMaterializationInvocationResult:
    invocation_id: str
    invocation_authoring_sha256: str
    outcome: Literal["materialized", "valid_existing"]
    probe: AcknowledgementMaterializationRecoveryProbe
    materialization: FinalExecutionAcknowledgementMaterializationResult
    recovery_state_probe_performed: bool
    materialization_invoked: bool
    materializer_called: bool
    writer_called: bool
    automatic_retry_performed: bool
    blind_retry_performed: bool
    existing_valid_target_reused: bool
    final_execution_acknowledgement_issued: bool
    final_execution_acknowledged: bool
    one_shot_engineering_invocation_permitted: bool
    execution_lease_materialized: bool
    durable_host_outcome_present: bool
    authorization_consumed: bool

    def require(
        self,
        invocation: ProspectiveFinalExecutionAcknowledgementMaterializationInvocation,
        materialization: ProspectiveFinalExecutionAcknowledgementMaterialization,
    ) -> None:
        self.probe.require()
        expected_common: dict[str, object] = {
            "invocation_id": invocation.invocation_id,
            "invocation_authoring_sha256": invocation.invocation_authoring_sha256,
            "recovery_state_probe_performed": True,
            "automatic_retry_performed": False,
            "blind_retry_performed": False,
            "final_execution_acknowledgement_issued": True,
            "final_execution_acknowledged": True,
            "one_shot_engineering_invocation_permitted": False,
            "execution_lease_materialized": False,
            "durable_host_outcome_present": False,
            "authorization_consumed": False,
        }
        for field_name, expected_value in expected_common.items():
            if getattr(self, field_name) != expected_value:
                raise AcknowledgementMaterializationInvocationImplementationError(
                    f"materialization invocation result differs: {field_name}"
                )
        if self.outcome == "materialized":
            expected = ("absent", True, True, True, False)
        elif self.outcome == "valid_existing":
            expected = ("valid_existing", False, False, False, True)
        else:
            raise AcknowledgementMaterializationInvocationImplementationError(
                "materialization invocation result outcome differs"
            )
        observed = (
            self.probe.state,
            self.materialization_invoked,
            self.materializer_called,
            self.writer_called,
            self.existing_valid_target_reused,
        )
        if observed != expected:
            raise AcknowledgementMaterializationInvocationImplementationError(
                "materialization invocation result call state differs"
            )
        self.materialization.require(
            materialization, self.materialization.persisted_sha256
        )


@dataclass(frozen=True)
class _RuntimeChain:
    invocation_authoring_receipt: AcknowledgementMaterializationImplementationMergeValidationReceipt
    invocation_authoring: FinalExecutionAcknowledgementMaterializationInvocationAuthoring
    materialization_implementation_receipt: AcknowledgementMaterializationAuthoringMergeValidationReceipt
    materialization_implementation: FinalExecutionAcknowledgementMaterializationImplementationRecord
    materialization_authoring_receipt: AcknowledgementIssuanceImplementationMergeValidationReceipt
    materialization_authoring: FinalExecutionAcknowledgementMaterializationAuthoring
    issuance_receipt: AcknowledgementAuthoringMergeValidationReceipt
    issuance_authoring: FinalExecutionAcknowledgementIssuanceAuthoring
    upstream_receipt: WiringMergeValidationReceipt
    upstream_authoring: FinalExecutionAcknowledgementAuthoring


def build_authoring_merge_validation_receipt() -> AcknowledgementMaterializationInvocationAuthoringMergeValidationReceipt:
    provisional = AcknowledgementMaterializationInvocationAuthoringMergeValidationReceipt(
        receipt_id=(
            "stage3b-qwake-lc4-e-final-execution-acknowledgement-"
            "materialization-invocation-authoring-post-merge-validation-v1"
        ),
        pr_number=AUTHORING_PR_NUMBER,
        head_commit=AUTHORING_HEAD_COMMIT,
        base_commit=AUTHORING_PARENT_COMMIT,
        merge_commit=AUTHORING_MERGE_COMMIT,
        merged_at_utc=AUTHORING_MERGED_AT_UTC,
        commit_count=1,
        file_count=18,
        focused_tests_passed=124,
        targeted_tests_passed=325,
        full_tests_passed=1372,
        full_test_warnings=14,
        required_ci_checks_passed=True,
        required_ci_check_count=4,
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
    receipt: AcknowledgementMaterializationInvocationAuthoringMergeValidationReceipt,
) -> FinalExecutionAcknowledgementMaterializationInvocationImplementationSource:
    receipt.require()
    return FinalExecutionAcknowledgementMaterializationInvocationImplementationSource(
        implementation_base_commit=IMPLEMENTATION_BASE_COMMIT,
        invocation_authoring_id=(
            "stage3b-qwake-lc4-e-final-execution-acknowledgement-"
            "materialization-invocation-authoring-v1"
        ),
        invocation_authoring_sha256=INVOCATION_AUTHORING_SHA256,
        invocation_authoring_file_sha256=INVOCATION_AUTHORING_FILE_SHA256,
        invocation_authoring_implementation_receipt_file_sha256=(
            INVOCATION_AUTHORING_IMPLEMENTATION_RECEIPT_FILE_SHA256
        ),
        invocation_authoring_package_registry_sha256=(
            INVOCATION_AUTHORING_PACKAGE_REGISTRY_SHA256
        ),
        invocation_authoring_source_registry_sha256=(
            INVOCATION_AUTHORING_SOURCE_REGISTRY_SHA256
        ),
        invocation_authoring_module_sha256=INVOCATION_AUTHORING_MODULE_SHA256,
        invocation_authoring_verifier_sha256=INVOCATION_AUTHORING_VERIFIER_SHA256,
        invocation_authoring_test_sha256=INVOCATION_AUTHORING_TEST_SHA256,
        invocation_authoring_adr_ru_sha256=INVOCATION_AUTHORING_ADR_RU_SHA256,
        invocation_authoring_adr_en_sha256=INVOCATION_AUTHORING_ADR_EN_SHA256,
        invocation_authoring_pr_number=receipt.pr_number,
        invocation_authoring_head_commit=receipt.head_commit,
        invocation_authoring_parent_commit=receipt.base_commit,
        invocation_authoring_merge_commit=receipt.merge_commit,
        invocation_authoring_merged_at_utc=receipt.merged_at_utc,
        materialization_implementation_sha256=MATERIALIZATION_IMPLEMENTATION_SHA256,
        prospective_builder_symbol=PROSPECTIVE_BUILDER_SYMBOL,
        materializer_symbol=MATERIALIZER_SYMBOL,
        persisted_verifier_symbol=PERSISTED_VERIFIER_SYMBOL,
        writer_symbol=WRITER_SYMBOL,
        acknowledgement_relative=ACKNOWLEDGEMENT_RELATIVE.as_posix(),
    )


def _build_contract() -> FinalExecutionAcknowledgementMaterializationInvocationImplementationContract:
    return FinalExecutionAcknowledgementMaterializationInvocationImplementationContract(
        complete_invocation_authoring_identity_verified=True,
        invocation_authoring_post_merge_verification_required=True,
        exact_prospective_builder_delegate_required=True,
        exact_materializer_delegate_required=True,
        exact_existing_target_verifier_delegate_required=True,
        recovery_state_probe_before_materializer_required=True,
        materializer_call_limit=1,
        persisted_verifier_call_limit=1,
        direct_writer_call_forbidden=True,
        automatic_retry_forbidden=True,
        blind_retry_forbidden=True,
        explicit_recovery_permitted=True,
        absent_target_requires_new_explicit_authorization=True,
        valid_existing_target_treated_as_success=True,
        valid_existing_target_materializer_call_forbidden=True,
        invalid_existing_target_fail_closed=True,
        materializer_failure_propagated_without_retry=True,
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


def _build_gates() -> FinalExecutionAcknowledgementMaterializationInvocationImplementationGates:
    return FinalExecutionAcknowledgementMaterializationInvocationImplementationGates(
        invocation_authoring_post_merge_verified=True,
        acknowledgement_materialization_implemented=True,
        materialization_invocation_contract_authored=True,
        materialization_invocation_implemented=True,
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


def build_frozen_materialization_invocation_implementation_record(
    receipt: AcknowledgementMaterializationInvocationAuthoringMergeValidationReceipt,
) -> FinalExecutionAcknowledgementMaterializationInvocationImplementationRecord:
    provisional = FinalExecutionAcknowledgementMaterializationInvocationImplementationRecord(
        schema_version=1,
        implementation_id=FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_IMPLEMENTATION_ID,
        status=FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_IMPLEMENTATION_STATUS,
        recorded_at_utc="2026-07-31T01:25:00Z",
        source=_build_source(receipt),
        contract=_build_contract(),
        gates=_build_gates(),
        next_slice=(
            "QW-LC4-E-final-execution-acknowledgement-materialization-"
            "invocation-implementation-commit"
        ),
        post_merge_next_slice=(
            "QW-LC4-E-final-execution-acknowledgement-materialization-"
            "invocation-operation-authoring"
        ),
        implementation_sha256="sha256:" + "0" * 64,
    )
    result = replace(
        provisional,
        implementation_sha256=sha256_object(provisional.semantic_payload()),
    )
    result.require(receipt)
    return result


def _load_runtime_chain(root: Path) -> _RuntimeChain:
    invocation_authoring_receipt = load_materialization_implementation_merge_validation_receipt(
        root / INVOCATION_AUTHORING_IMPLEMENTATION_MERGE_RECEIPT_RELATIVE
    )
    invocation_authoring = load_final_execution_acknowledgement_materialization_invocation_authoring(
        root / INVOCATION_AUTHORING_RECORD_RELATIVE,
        invocation_authoring_receipt,
    )
    materialization_implementation_receipt = load_acknowledgement_materialization_authoring_merge_validation_receipt(
        root / MATERIALIZATION_IMPLEMENTATION_PACKAGE_RELATIVE / "authoring-merge-validation.json"
    )
    materialization_implementation = load_final_execution_acknowledgement_materialization_implementation_record(
        root / MATERIALIZATION_IMPLEMENTATION_RECORD_RELATIVE,
        materialization_implementation_receipt,
    )
    materialization_authoring_receipt = load_acknowledgement_issuance_implementation_merge_validation_receipt(
        root / MATERIALIZATION_AUTHORING_MERGE_RECEIPT_RELATIVE
    )
    materialization_authoring = load_final_execution_acknowledgement_materialization_authoring(
        root / MATERIALIZATION_AUTHORING_RECORD_RELATIVE,
        materialization_authoring_receipt,
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
    if materialization_implementation.implementation_sha256 != MATERIALIZATION_IMPLEMENTATION_SHA256:
        raise AcknowledgementMaterializationInvocationImplementationError(
            "materialization implementation semantic identity differs"
        )
    return _RuntimeChain(
        invocation_authoring_receipt=invocation_authoring_receipt,
        invocation_authoring=invocation_authoring,
        materialization_implementation_receipt=materialization_implementation_receipt,
        materialization_implementation=materialization_implementation,
        materialization_authoring_receipt=materialization_authoring_receipt,
        materialization_authoring=materialization_authoring,
        issuance_receipt=issuance_receipt,
        issuance_authoring=issuance_authoring,
        upstream_receipt=upstream_receipt,
        upstream_authoring=upstream_authoring,
    )


def _build_materialization(
    chain: _RuntimeChain,
    invocation: ProspectiveFinalExecutionAcknowledgementMaterializationInvocation,
) -> ProspectiveFinalExecutionAcknowledgementMaterialization:
    try:
        invocation.require(
            chain.invocation_authoring, chain.invocation_authoring_receipt
        )
        result = _build_prospective_materialization(
            chain.materialization_authoring,
            chain.materialization_authoring_receipt,
            chain.issuance_authoring,
            chain.issuance_receipt,
            chain.upstream_authoring,
            chain.upstream_receipt,
            acknowledgement_phrase=invocation.acknowledgement_phrase,
            operator_identity=invocation.operator_identity,
            acknowledged_at_utc=invocation.acknowledged_at_utc,
            issuer_identity=invocation.issuer_identity,
            issued_at_utc=invocation.issued_at_utc,
            materializer_identity=invocation.materializer_identity,
            materialized_at_utc=invocation.materialized_at_utc,
        )
        result.require(
            chain.materialization_authoring,
            chain.materialization_authoring_receipt,
            chain.issuance_authoring,
            chain.issuance_receipt,
            chain.upstream_authoring,
            chain.upstream_receipt,
        )
    except Exception as exc:
        raise AcknowledgementMaterializationInvocationImplementationError(
            str(exc)
        ) from exc
    return result


def _target_present(root: Path) -> bool:
    target = root / ACKNOWLEDGEMENT_RELATIVE
    try:
        target.lstat()
    except FileNotFoundError:
        return False
    return True


def _require_non_acknowledgement_boundary_closed(root: Path) -> None:
    paths = {
        "authorized output root": root / Path(
            "results/stage-3/qwake-lc4-runtime-validation-v1-attempt-001"
        ),
        "legacy execution lease": root / LEGACY_EXECUTION_LEASE_RELATIVE,
        "persistent execution lease v2": root / EXECUTION_LEASE_V2_RELATIVE,
        "durable host outcome": root / DURABLE_HOST_OUTCOME_RELATIVE,
    }
    for label, path in paths.items():
        try:
            path.lstat()
        except FileNotFoundError:
            continue
        raise AcknowledgementMaterializationInvocationImplementationError(
            f"{label} already exists: {path}"
        )


def _probe_with_chain(
    root: Path,
    chain: _RuntimeChain,
    materialization: ProspectiveFinalExecutionAcknowledgementMaterialization,
) -> tuple[AcknowledgementMaterializationRecoveryProbe, PersistentAcknowledgementWriteResult | None]:
    _require_non_acknowledgement_boundary_closed(root)
    if not _target_present(root):
        probe = AcknowledgementMaterializationRecoveryProbe(
            state="absent",
            acknowledgement_relative=ACKNOWLEDGEMENT_RELATIVE.as_posix(),
            target_present=False,
            exact_existing_bytes_verified=False,
            materializer_call_permitted=True,
            materializer_recall_forbidden=False,
            explicit_recovery_required=True,
        )
        probe.require()
        return probe, None
    try:
        verified = _verify_persisted_once(
            root,
            chain.issuance_authoring,
            chain.issuance_receipt,
            chain.upstream_authoring,
            chain.upstream_receipt,
            materialization.issuance,
        )
    except Exception as exc:
        raise AcknowledgementMaterializationInvocationImplementationError(
            "existing final execution acknowledgement is invalid"
        ) from exc
    probe = AcknowledgementMaterializationRecoveryProbe(
        state="valid_existing",
        acknowledgement_relative=ACKNOWLEDGEMENT_RELATIVE.as_posix(),
        target_present=True,
        exact_existing_bytes_verified=True,
        materializer_call_permitted=False,
        materializer_recall_forbidden=True,
        explicit_recovery_required=True,
    )
    probe.require()
    return probe, verified


def probe_final_execution_acknowledgement_state(
    project_root: Path,
    invocation: ProspectiveFinalExecutionAcknowledgementMaterializationInvocation,
) -> AcknowledgementMaterializationRecoveryProbe:
    """Classify the exact target without materializer or writer effects."""

    root = _verified_project_root(project_root)
    _verify_implementation_freeze(root)
    chain = _load_runtime_chain(root)
    materialization = _build_materialization(chain, invocation)
    probe, _ = _probe_with_chain(root, chain, materialization)
    return probe


def _result_from_existing(
    materialization: ProspectiveFinalExecutionAcknowledgementMaterialization,
    verified: PersistentAcknowledgementWriteResult,
) -> FinalExecutionAcknowledgementMaterializationResult:
    result = FinalExecutionAcknowledgementMaterializationResult(
        materialization_id=materialization.materialization_id,
        materialization_authoring_sha256=materialization.materialization_authoring_sha256,
        relative_path=verified.relative_path,
        byte_count=verified.byte_count,
        persisted_sha256=verified.sha256,
        mode=verified.mode,
        exact_persisted_bytes_verified=True,
        final_execution_acknowledgement_issued=True,
        final_execution_acknowledged=True,
        one_shot_engineering_invocation_permitted=False,
        execution_lease_materialized=False,
        authorization_consumed=False,
    )
    result.require(materialization, verified.sha256)
    return result


def invoke_final_execution_acknowledgement_materialization(
    project_root: Path,
    invocation: ProspectiveFinalExecutionAcknowledgementMaterializationInvocation,
) -> FinalExecutionAcknowledgementMaterializationInvocationResult:
    """Probe durable state and perform at most one explicit materializer call."""

    root = _verified_project_root(project_root)
    _verify_implementation_freeze(root)
    chain = _load_runtime_chain(root)
    materialization = _build_materialization(chain, invocation)
    probe, verified = _probe_with_chain(root, chain, materialization)
    if probe.state == "valid_existing":
        if verified is None:
            raise AcknowledgementMaterializationInvocationImplementationError(
                "valid existing acknowledgement lacks verification result"
            )
        materialization_result = _result_from_existing(materialization, verified)
        outcome: Literal["materialized", "valid_existing"] = "valid_existing"
        materialization_invoked = False
        materializer_called = False
        writer_called = False
        existing_valid_target_reused = True
    else:
        try:
            materialization_result = _materialize_once(
                root,
                chain.materialization_authoring,
                chain.materialization_authoring_receipt,
                chain.issuance_authoring,
                chain.issuance_receipt,
                chain.upstream_authoring,
                chain.upstream_receipt,
                materialization,
            )
        except Exception as exc:
            raise AcknowledgementMaterializationInvocationImplementationError(
                str(exc)
            ) from exc
        outcome = "materialized"
        materialization_invoked = True
        materializer_called = True
        writer_called = True
        existing_valid_target_reused = False
    result = FinalExecutionAcknowledgementMaterializationInvocationResult(
        invocation_id=invocation.invocation_id,
        invocation_authoring_sha256=invocation.invocation_authoring_sha256,
        outcome=outcome,
        probe=probe,
        materialization=materialization_result,
        recovery_state_probe_performed=True,
        materialization_invoked=materialization_invoked,
        materializer_called=materializer_called,
        writer_called=writer_called,
        automatic_retry_performed=False,
        blind_retry_performed=False,
        existing_valid_target_reused=existing_valid_target_reused,
        final_execution_acknowledgement_issued=True,
        final_execution_acknowledged=True,
        one_shot_engineering_invocation_permitted=False,
        execution_lease_materialized=False,
        durable_host_outcome_present=False,
        authorization_consumed=False,
    )
    result.require(invocation, materialization)
    return result


def _verified_project_root(project_root: Path) -> Path:
    expanded = project_root.expanduser()
    if expanded.is_symlink():
        raise AcknowledgementMaterializationInvocationImplementationError(
            "project root is symbolic"
        )
    root = expanded.resolve()
    if not root.is_dir():
        raise AcknowledgementMaterializationInvocationImplementationError(
            "project root is absent or non-directory"
        )
    return root


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8", errors="strict"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AcknowledgementMaterializationInvocationImplementationError(
            f"frozen JSON is invalid: {path}"
        ) from exc
    if not isinstance(value, dict):
        raise AcknowledgementMaterializationInvocationImplementationError(
            f"frozen JSON root differs: {path}"
        )
    return cast(dict[str, Any], value)


def _verify_registry(path: Path, base: Path) -> dict[str, str]:
    if not path.is_file() or path.is_symlink():
        raise AcknowledgementMaterializationInvocationImplementationError(
            f"frozen registry is absent or invalid: {path}"
        )
    entries: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="strict").splitlines():
        try:
            digest, relative = line.split("  ", 1)
        except ValueError as exc:
            raise AcknowledgementMaterializationInvocationImplementationError(
                f"frozen registry line is invalid: {path}"
            ) from exc
        target = base / relative
        if relative in entries:
            raise AcknowledgementMaterializationInvocationImplementationError(
                f"frozen registry path is duplicated: {relative}"
            )
        if not target.is_file() or target.is_symlink():
            raise AcknowledgementMaterializationInvocationImplementationError(
                f"frozen registry target is absent or invalid: {target}"
            )
        observed = hashlib.sha256(target.read_bytes()).hexdigest()
        if observed != digest:
            raise AcknowledgementMaterializationInvocationImplementationError(
                f"frozen registry target digest differs: {target}"
            )
        entries[relative] = digest
    if not entries:
        raise AcknowledgementMaterializationInvocationImplementationError(
            f"frozen registry is empty: {path}"
        )
    return entries


def _verify_runtime_ast_boundary(root: Path) -> None:
    builder_bindings = 0
    builder_calls = 0
    materializer_bindings = 0
    materializer_calls = 0
    verifier_bindings = 0
    verifier_calls = 0
    writer_bindings = 0
    for relative in (IMPLEMENTATION_MODULE_RELATIVE, IMPLEMENTATION_VERIFIER_RELATIVE):
        path = root / relative
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="strict"))
        except (OSError, UnicodeError, SyntaxError) as exc:
            raise AcknowledgementMaterializationInvocationImplementationError(
                f"invocation implementation Python source is invalid: {path}"
            ) from exc
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots = {alias.name.split(".", 1)[0] for alias in node.names}
                if roots & _FORBIDDEN_IMPORT_ROOTS:
                    raise AcknowledgementMaterializationInvocationImplementationError(
                        f"forbidden invocation implementation import: {path}"
                    )
            if isinstance(node, ast.ImportFrom) and node.module:
                if node.module.split(".", 1)[0] in _FORBIDDEN_IMPORT_ROOTS:
                    raise AcknowledgementMaterializationInvocationImplementationError(
                        f"forbidden invocation implementation import: {path}"
                    )
                if relative == IMPLEMENTATION_MODULE_RELATIVE:
                    for alias in node.names:
                        if alias.name == "build_prospective_acknowledgement_materialization" and alias.asname == "_build_prospective_materialization":
                            builder_bindings += 1
                        if alias.name == "materialize_final_execution_acknowledgement" and alias.asname == "_materialize_once":
                            materializer_bindings += 1
                        if alias.name == "verify_persisted_final_execution_acknowledgement" and alias.asname == "_verify_persisted_once":
                            verifier_bindings += 1
                        if alias.name == "persist_final_execution_acknowledgement":
                            writer_bindings += 1
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Name):
                call_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                call_name = node.func.attr
            else:
                call_name = ""
            if call_name in _FORBIDDEN_RUNTIME_CALLS:
                raise AcknowledgementMaterializationInvocationImplementationError(
                    f"forbidden runtime call in invocation implementation: {path}"
                )
            if relative == IMPLEMENTATION_MODULE_RELATIVE:
                builder_calls += int(call_name == "_build_prospective_materialization")
                materializer_calls += int(call_name == "_materialize_once")
                verifier_calls += int(call_name == "_verify_persisted_once")
    observed = (
        builder_bindings,
        builder_calls,
        materializer_bindings,
        materializer_calls,
        verifier_bindings,
        verifier_calls,
        writer_bindings,
    )
    if observed != (1, 1, 1, 1, 1, 1, 0):
        raise AcknowledgementMaterializationInvocationImplementationError(
            f"invocation adapter delegate boundary differs: {observed}"
        )


def _require_production_callsite_absent(root: Path) -> None:
    allowed = (root / IMPLEMENTATION_MODULE_RELATIVE).resolve()
    target_name = "invoke_final_execution_acknowledgement_materialization"
    for path in sorted((root / "src").rglob("*.py")):
        if path.resolve() == allowed:
            continue
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
                raise AcknowledgementMaterializationInvocationImplementationError(
                    f"production invocation-adapter callsite exists: {path}"
                )


def _verify_static_authoring_identity(root: Path) -> None:
    verify_final_execution_acknowledgement_materialization_invocation_authoring(root)
    verify_final_execution_acknowledgement_materialization_implementation(root)
    expected: dict[Path, str] = {
        INVOCATION_AUTHORING_RECORD_RELATIVE: INVOCATION_AUTHORING_FILE_SHA256,
        INVOCATION_AUTHORING_IMPLEMENTATION_MERGE_RECEIPT_RELATIVE: INVOCATION_AUTHORING_IMPLEMENTATION_RECEIPT_FILE_SHA256,
        INVOCATION_AUTHORING_REGISTRY_RELATIVE: INVOCATION_AUTHORING_PACKAGE_REGISTRY_SHA256,
        INVOCATION_AUTHORING_SOURCE_REGISTRY_RELATIVE: INVOCATION_AUTHORING_SOURCE_REGISTRY_SHA256,
        INVOCATION_AUTHORING_MODULE_RELATIVE: INVOCATION_AUTHORING_MODULE_SHA256,
        INVOCATION_AUTHORING_VERIFIER_RELATIVE: INVOCATION_AUTHORING_VERIFIER_SHA256,
        INVOCATION_AUTHORING_TEST_RELATIVE: INVOCATION_AUTHORING_TEST_SHA256,
        INVOCATION_AUTHORING_ADR_RU_RELATIVE: INVOCATION_AUTHORING_ADR_RU_SHA256,
        INVOCATION_AUTHORING_ADR_EN_RELATIVE: INVOCATION_AUTHORING_ADR_EN_SHA256,
    }
    for relative, digest in expected.items():
        path = root / relative
        if not path.is_file() or path.is_symlink():
            raise AcknowledgementMaterializationInvocationImplementationError(
                f"invocation authoring source is absent or invalid: {relative}"
            )
        if sha256_bytes(path.read_bytes()) != digest:
            raise AcknowledgementMaterializationInvocationImplementationError(
                f"invocation authoring source identity differs: {relative}"
            )


def _verify_implementation_freeze(
    root: Path,
) -> tuple[
    AcknowledgementMaterializationInvocationAuthoringMergeValidationReceipt,
    FinalExecutionAcknowledgementMaterializationInvocationImplementationRecord,
]:
    package = root / IMPLEMENTATION_PACKAGE_RELATIVE
    if not package.is_dir() or package.is_symlink():
        raise AcknowledgementMaterializationInvocationImplementationError(
            "materialization invocation implementation package is absent or invalid"
        )
    if {path.name for path in package.iterdir()} != _EXPECTED_PACKAGE_FILES:
        raise AcknowledgementMaterializationInvocationImplementationError(
            "materialization invocation implementation package file set differs"
        )
    _verify_registry(root / IMPLEMENTATION_REGISTRY_RELATIVE, package)
    source_registry = _verify_registry(
        root / IMPLEMENTATION_SOURCE_REGISTRY_RELATIVE, root
    )
    if frozenset(source_registry) != _EXPECTED_SOURCE_PATHS:
        raise AcknowledgementMaterializationInvocationImplementationError(
            "materialization invocation source registry path set differs"
        )
    receipt = load_authoring_merge_validation_receipt(
        root / AUTHORING_MERGE_RECEIPT_RELATIVE
    )
    record = load_materialization_invocation_implementation_record(
        root / IMPLEMENTATION_RECORD_RELATIVE, receipt
    )
    return receipt, record


def load_authoring_merge_validation_receipt(
    path: Path,
) -> AcknowledgementMaterializationInvocationAuthoringMergeValidationReceipt:
    result = AcknowledgementMaterializationInvocationAuthoringMergeValidationReceipt.from_mapping(
        _load_json(path)
    )
    result.require()
    return result


def load_materialization_invocation_implementation_record(
    path: Path,
    receipt: AcknowledgementMaterializationInvocationAuthoringMergeValidationReceipt,
) -> FinalExecutionAcknowledgementMaterializationInvocationImplementationRecord:
    result = FinalExecutionAcknowledgementMaterializationInvocationImplementationRecord.from_mapping(
        _load_json(path)
    )
    result.require(receipt)
    return result


def verify_final_execution_acknowledgement_materialization_invocation_implementation(
    project_root: Path,
) -> FinalExecutionAcknowledgementMaterializationInvocationImplementationRecord:
    """Verify the frozen adapter package without invoking it."""

    root = _verified_project_root(project_root)
    _, record = _verify_implementation_freeze(root)
    _verify_static_authoring_identity(root)
    _verify_runtime_ast_boundary(root)
    _require_production_callsite_absent(root)
    _require_non_acknowledgement_boundary_closed(root)
    if _target_present(root):
        raise AcknowledgementMaterializationInvocationImplementationError(
            "final execution acknowledgement already exists during static verification"
        )
    return record
