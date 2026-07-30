"""Effect-free authoring contract for final acknowledgement issuance.

This module freezes how a future operator acknowledgement may be wrapped for
exclusive durable issuance. It only builds and verifies immutable in-memory
records. Importing or verifying it never writes the acknowledgement, creates a
lease or outcome, inspects an image, materializes a command, spawns a process,
invokes Docker, consumes authorization, or executes local compute.
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
    AUTHORIZED_OUTPUT_ROOT,
    DURABLE_HOST_OUTCOME_RELATIVE,
    EXECUTION_LEASE_V2_RELATIVE,
    FINAL_EXECUTION_ACKNOWLEDGEMENT_AUTHORING_ID,
    FINAL_EXECUTION_ACKNOWLEDGEMENT_ID,
    FINAL_EXECUTION_OPERATOR_ACKNOWLEDGEMENT,
    IMAGE_REPO_DIGEST,
    INVOCATION_COUNT,
    TORCH2PC_COMMIT,
    FinalExecutionAcknowledgementAuthoring,
    ProspectiveFinalExecutionAcknowledgement,
    WiringMergeValidationReceipt,
    build_final_execution_acknowledgement,
    canonical_json,
    sha256_bytes,
    sha256_object,
    verify_final_execution_acknowledgement_authoring,
)

FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUANCE_AUTHORING_ID: Final = (
    "stage3b-qwake-lc4-e-final-execution-acknowledgement-issuance-authoring-v1"
)
FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUANCE_AUTHORING_STATUS: Final = (
    "acknowledgement_issuance_contract_authored_not_issued_execution_closed"
)
FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUANCE_ID: Final = (
    "stage3b-qwake-lc4-e-final-execution-acknowledgement-issuance-v1"
)
FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUANCE_STATUS: Final = (
    "prospective_acknowledgement_issuance_not_materialized"
)

ISSUANCE_AUTHORING_BASE_COMMIT: Final = "eb20c157584efff8e9aa0418385242c7d7b26eab"
ACKNOWLEDGEMENT_AUTHORING_PR_NUMBER: Final = 147
ACKNOWLEDGEMENT_AUTHORING_HEAD_COMMIT: Final = (
    "d75a767c714da7437ceef2be78c0c5ee479d66b2"
)
ACKNOWLEDGEMENT_AUTHORING_PARENT_COMMIT: Final = (
    "2957d8f6975c88e7bdb23243e3915c7f51d4ba47"
)
ACKNOWLEDGEMENT_AUTHORING_MERGE_COMMIT: Final = ISSUANCE_AUTHORING_BASE_COMMIT
ACKNOWLEDGEMENT_AUTHORING_MERGED_AT_UTC: Final = "2026-07-30T16:03:05Z"

ACKNOWLEDGEMENT_AUTHORING_SHA256: Final = (
    "sha256:fb76d1c483a5ba15ca629edd6b2866eac0d497fd3569241a0c78fddbb5c50cd7"
)
ACKNOWLEDGEMENT_AUTHORING_FILE_SHA256: Final = (
    "sha256:dd15acc7e5f7d9cae17e9f2b94557ee97b531d45410ead4d09f0d820e39a7b4f"
)
ACKNOWLEDGEMENT_AUTHORING_PACKAGE_REGISTRY_SHA256: Final = (
    "sha256:599b37ea4e81e1be6c46685c224fccb962477a786560809f83f03e85ecc6f9fa"
)
ACKNOWLEDGEMENT_AUTHORING_SOURCE_REGISTRY_SHA256: Final = (
    "sha256:9857d7ee4afa9122514bc1d4eb53e7788ccf3ffb8372aa687d4d5864740fed74"
)
ACKNOWLEDGEMENT_AUTHORING_MODULE_SHA256: Final = (
    "sha256:8610ab93cf3628eb900545f5c101b67a4196a1f0d3d3c70902b047bacf1ca7f4"
)
ACKNOWLEDGEMENT_AUTHORING_VERIFIER_SHA256: Final = (
    "sha256:e820ce613a0edba3f9ebae6d23d987de693a3937f8f1ef620262c0c4e0d2028c"
)
ACKNOWLEDGEMENT_AUTHORING_TEST_SHA256: Final = (
    "sha256:a470ef863b705afaa1c758dc69039dc7094c5f57da5e5cdeb72ad277ed55d8f3"
)
ACKNOWLEDGEMENT_AUTHORING_ADR_RU_SHA256: Final = (
    "sha256:061786e3c4917dc57cb832886e157ae26511994c3386e157e64753a2d56ad65d"
)
ACKNOWLEDGEMENT_AUTHORING_ADR_EN_SHA256: Final = (
    "sha256:6f0211a7dd45a1e94889d03617883bf4c529c83058dd9d65e00ebd2b605cb942"
)

ACKNOWLEDGEMENT_RELATIVE: Final = Path(
    AUTHORIZED_OUTPUT_ROOT + ".final-execution-acknowledgement.json"
)
ACKNOWLEDGEMENT_FILE_MODE: Final = "0600"

PACKAGE_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-final-execution-acknowledgement-issuance-authoring-v1"
)
AUTHORING_RECORD_RELATIVE: Final = PACKAGE_RELATIVE / "authoring.json"
AUTHORING_MERGE_RECEIPT_RELATIVE: Final = (
    PACKAGE_RELATIVE / "authoring-merge-validation.json"
)
REGISTRY_RELATIVE: Final = PACKAGE_RELATIVE / "SHA256SUMS"
SOURCE_REGISTRY_RELATIVE: Final = PACKAGE_RELATIVE / "source-SHA256SUMS"

UPSTREAM_PACKAGE_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-final-execution-acknowledgement-authoring-v1"
)
UPSTREAM_AUTHORING_RECORD_RELATIVE: Final = UPSTREAM_PACKAGE_RELATIVE / "authoring.json"
UPSTREAM_WIRING_RECEIPT_RELATIVE: Final = (
    UPSTREAM_PACKAGE_RELATIVE / "wiring-merge-validation.json"
)
UPSTREAM_PACKAGE_REGISTRY_RELATIVE: Final = UPSTREAM_PACKAGE_RELATIVE / "SHA256SUMS"
UPSTREAM_SOURCE_REGISTRY_RELATIVE: Final = (
    UPSTREAM_PACKAGE_RELATIVE / "source-SHA256SUMS"
)
UPSTREAM_MODULE_RELATIVE: Final = Path(
    "src/torch2pc_thesis/"
    "stage3b_qwake_lc4_final_execution_acknowledgement_authoring.py"
)
UPSTREAM_VERIFIER_RELATIVE: Final = Path(
    "scripts/verify_stage3b_qwake_lc4_final_execution_acknowledgement_authoring.py"
)
UPSTREAM_TEST_RELATIVE: Final = Path(
    "tests/unit/test_stage3b_qwake_lc4_final_execution_acknowledgement_authoring.py"
)
UPSTREAM_ADR_RU_RELATIVE: Final = Path(
    "docs/decisions/ADR-086-stage3b-qwake-lc4-e-"
    "final-execution-acknowledgement-authoring.md"
)
UPSTREAM_ADR_EN_RELATIVE: Final = Path(
    "docs/decisions/ADR-086-stage3b-qwake-lc4-e-"
    "final-execution-acknowledgement-authoring_EN.md"
)
MODULE_RELATIVE: Final = Path(
    "src/torch2pc_thesis/"
    "stage3b_qwake_lc4_final_execution_acknowledgement_issuance_authoring.py"
)
VERIFIER_RELATIVE: Final = Path(
    "scripts/verify_stage3b_qwake_lc4_"
    "final_execution_acknowledgement_issuance_authoring.py"
)
TEST_RELATIVE: Final = Path(
    "tests/unit/test_stage3b_qwake_lc4_"
    "final_execution_acknowledgement_issuance_authoring.py"
)
ADR_RU_RELATIVE: Final = Path(
    "docs/decisions/ADR-087-stage3b-qwake-lc4-e-"
    "final-execution-acknowledgement-issuance-authoring.md"
)
ADR_EN_RELATIVE: Final = Path(
    "docs/decisions/ADR-087-stage3b-qwake-lc4-e-"
    "final-execution-acknowledgement-issuance-authoring_EN.md"
)

_EXPECTED_PACKAGE_FILES: Final = frozenset(
    {
        "SHA256SUMS",
        "authoring-merge-validation.json",
        "authoring.json",
        "source-SHA256SUMS",
    }
)
_EXPECTED_SOURCE_PATHS: Final = frozenset(
    {
        UPSTREAM_AUTHORING_RECORD_RELATIVE.as_posix(),
        UPSTREAM_WIRING_RECEIPT_RELATIVE.as_posix(),
        UPSTREAM_PACKAGE_REGISTRY_RELATIVE.as_posix(),
        UPSTREAM_SOURCE_REGISTRY_RELATIVE.as_posix(),
        UPSTREAM_MODULE_RELATIVE.as_posix(),
        UPSTREAM_VERIFIER_RELATIVE.as_posix(),
        UPSTREAM_TEST_RELATIVE.as_posix(),
        UPSTREAM_ADR_RU_RELATIVE.as_posix(),
        UPSTREAM_ADR_EN_RELATIVE.as_posix(),
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
_FORBIDDEN_IMPORT_ROOTS: Final = frozenset({"subprocess", "docker"})
_FORBIDDEN_CALL_NAMES: Final = frozenset(
    {
        "invoke_lease_bound_host_runtime",
        "invoke_one_shot_host_runtime",
        "persist_persistent_execution_lease_v2",
        "persist_durable_host_outcome_receipt",
        "inspect_local_image",
        "materialize_invocation_command",
    }
)
_FORBIDDEN_CALL_ATTRIBUTES: Final = frozenset(
    {
        "Popen",
        "run",
        "write_bytes",
        "write_text",
        "touch",
        "mkdir",
        "replace",
        "rename",
        "symlink_to",
        "hardlink_to",
        "unlink",
    }
)

__all__ = [
    "ACKNOWLEDGEMENT_RELATIVE",
    "FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUANCE_AUTHORING_ID",
    "AcknowledgementAuthoringMergeValidationReceipt",
    "FinalExecutionAcknowledgementIssuanceAuthoring",
    "FinalExecutionAcknowledgementIssuanceAuthoringError",
    "FinalExecutionAcknowledgementIssuanceContract",
    "FinalExecutionAcknowledgementIssuanceGates",
    "FinalExecutionAcknowledgementIssuanceSource",
    "ProspectiveFinalExecutionAcknowledgementIssuance",
    "build_acknowledgement_authoring_merge_validation_receipt",
    "build_frozen_issuance_authoring_record",
    "build_prospective_acknowledgement_issuance",
    "canonical_json",
    "load_acknowledgement_authoring_merge_validation_receipt",
    "load_final_execution_acknowledgement_issuance_authoring",
    "sha256_bytes",
    "sha256_object",
    "verify_final_execution_acknowledgement_issuance_authoring",
]


class FinalExecutionAcknowledgementIssuanceAuthoringError(RuntimeError):
    """Raised when the issuance-authoring contract fails closed."""


def _require_sha256(value: str, field_name: str) -> None:
    if not _SHA256_PATTERN.fullmatch(value):
        raise FinalExecutionAcknowledgementIssuanceAuthoringError(
            f"{field_name} is not a canonical SHA-256 identity"
        )


def _require_commit(value: str, field_name: str) -> None:
    if not _COMMIT_PATTERN.fullmatch(value):
        raise FinalExecutionAcknowledgementIssuanceAuthoringError(
            f"{field_name} is not a commit identity"
        )


def _require_utc(value: str, field_name: str) -> datetime:
    if not value.endswith("Z"):
        raise FinalExecutionAcknowledgementIssuanceAuthoringError(
            f"{field_name} is not a UTC timestamp"
        )
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise FinalExecutionAcknowledgementIssuanceAuthoringError(
            f"{field_name} is not an ISO-8601 timestamp"
        ) from exc
    if parsed.tzinfo != UTC:
        raise FinalExecutionAcknowledgementIssuanceAuthoringError(
            f"{field_name} is not normalized to UTC"
        )
    return parsed


@dataclass(frozen=True)
class AcknowledgementAuthoringMergeValidationReceipt:
    """Exact post-merge receipt for acknowledgement authoring PR #147."""

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
    ) -> AcknowledgementAuthoringMergeValidationReceipt:
        return cls(**cast(dict[str, Any], dict(value)))

    def semantic_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload.pop("receipt_sha256")
        return cast(dict[str, object], payload)

    def require(self) -> None:
        expected: dict[str, object] = {
            "receipt_id": (
                "stage3b-qwake-lc4-e-final-execution-acknowledgement-"
                "authoring-post-merge-validation-v1"
            ),
            "pr_number": ACKNOWLEDGEMENT_AUTHORING_PR_NUMBER,
            "head_commit": ACKNOWLEDGEMENT_AUTHORING_HEAD_COMMIT,
            "base_commit": ACKNOWLEDGEMENT_AUTHORING_PARENT_COMMIT,
            "merge_commit": ACKNOWLEDGEMENT_AUTHORING_MERGE_COMMIT,
            "merged_at_utc": ACKNOWLEDGEMENT_AUTHORING_MERGED_AT_UTC,
            "commit_count": 1,
            "file_count": 18,
            "focused_tests_passed": 50,
            "targeted_tests_passed": 251,
            "full_tests_passed": 1298,
            "full_test_warnings": 14,
            "required_ci_checks_passed": True,
            "production_execution_boundary_closed": True,
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise FinalExecutionAcknowledgementIssuanceAuthoringError(
                    f"authoring merge receipt differs: {field_name}"
                )
        _require_commit(self.head_commit, "head_commit")
        _require_commit(self.base_commit, "base_commit")
        _require_commit(self.merge_commit, "merge_commit")
        _require_utc(self.merged_at_utc, "merged_at_utc")
        _require_sha256(self.receipt_sha256, "receipt_sha256")
        if self.receipt_sha256 != sha256_object(self.semantic_payload()):
            raise FinalExecutionAcknowledgementIssuanceAuthoringError(
                "authoring merge receipt semantic SHA-256 differs"
            )

    def canonical_json(self) -> str:
        self.require()
        return canonical_json(self)


@dataclass(frozen=True)
class FinalExecutionAcknowledgementIssuanceSource:
    """Exact merged authoring chain bound by future issuance."""

    issuance_authoring_base_commit: str
    acknowledgement_authoring_pr_number: int
    acknowledgement_authoring_head_commit: str
    acknowledgement_authoring_parent_commit: str
    acknowledgement_authoring_merge_commit: str
    acknowledgement_authoring_merged_at_utc: str
    acknowledgement_authoring_merge_receipt_sha256: str
    acknowledgement_authoring_id: str
    acknowledgement_authoring_sha256: str
    acknowledgement_authoring_file_sha256: str
    acknowledgement_authoring_package_registry_sha256: str
    acknowledgement_authoring_source_registry_sha256: str
    acknowledgement_authoring_module_sha256: str
    acknowledgement_authoring_verifier_sha256: str
    acknowledgement_authoring_test_sha256: str
    acknowledgement_authoring_adr_ru_sha256: str
    acknowledgement_authoring_adr_en_sha256: str
    acknowledgement_id: str
    acknowledgement_relative: str
    image_repo_digest: str
    torch2pc_commit: str
    output_root: str
    execution_lease_v2_relative: str
    durable_host_outcome_relative: str
    invocation_count: int

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, object],
    ) -> FinalExecutionAcknowledgementIssuanceSource:
        return cls(**cast(dict[str, Any], dict(value)))

    def require(
        self,
        receipt: AcknowledgementAuthoringMergeValidationReceipt,
    ) -> None:
        expected: dict[str, object] = {
            "issuance_authoring_base_commit": ISSUANCE_AUTHORING_BASE_COMMIT,
            "acknowledgement_authoring_pr_number": (
                ACKNOWLEDGEMENT_AUTHORING_PR_NUMBER
            ),
            "acknowledgement_authoring_head_commit": (
                ACKNOWLEDGEMENT_AUTHORING_HEAD_COMMIT
            ),
            "acknowledgement_authoring_parent_commit": (
                ACKNOWLEDGEMENT_AUTHORING_PARENT_COMMIT
            ),
            "acknowledgement_authoring_merge_commit": (
                ACKNOWLEDGEMENT_AUTHORING_MERGE_COMMIT
            ),
            "acknowledgement_authoring_merged_at_utc": (
                ACKNOWLEDGEMENT_AUTHORING_MERGED_AT_UTC
            ),
            "acknowledgement_authoring_merge_receipt_sha256": (
                receipt.receipt_sha256
            ),
            "acknowledgement_authoring_id": (
                FINAL_EXECUTION_ACKNOWLEDGEMENT_AUTHORING_ID
            ),
            "acknowledgement_authoring_sha256": ACKNOWLEDGEMENT_AUTHORING_SHA256,
            "acknowledgement_authoring_file_sha256": (
                ACKNOWLEDGEMENT_AUTHORING_FILE_SHA256
            ),
            "acknowledgement_authoring_package_registry_sha256": (
                ACKNOWLEDGEMENT_AUTHORING_PACKAGE_REGISTRY_SHA256
            ),
            "acknowledgement_authoring_source_registry_sha256": (
                ACKNOWLEDGEMENT_AUTHORING_SOURCE_REGISTRY_SHA256
            ),
            "acknowledgement_authoring_module_sha256": (
                ACKNOWLEDGEMENT_AUTHORING_MODULE_SHA256
            ),
            "acknowledgement_authoring_verifier_sha256": (
                ACKNOWLEDGEMENT_AUTHORING_VERIFIER_SHA256
            ),
            "acknowledgement_authoring_test_sha256": (
                ACKNOWLEDGEMENT_AUTHORING_TEST_SHA256
            ),
            "acknowledgement_authoring_adr_ru_sha256": (
                ACKNOWLEDGEMENT_AUTHORING_ADR_RU_SHA256
            ),
            "acknowledgement_authoring_adr_en_sha256": (
                ACKNOWLEDGEMENT_AUTHORING_ADR_EN_SHA256
            ),
            "acknowledgement_id": FINAL_EXECUTION_ACKNOWLEDGEMENT_ID,
            "acknowledgement_relative": ACKNOWLEDGEMENT_RELATIVE.as_posix(),
            "image_repo_digest": IMAGE_REPO_DIGEST,
            "torch2pc_commit": TORCH2PC_COMMIT,
            "output_root": AUTHORIZED_OUTPUT_ROOT,
            "execution_lease_v2_relative": EXECUTION_LEASE_V2_RELATIVE.as_posix(),
            "durable_host_outcome_relative": DURABLE_HOST_OUTCOME_RELATIVE.as_posix(),
            "invocation_count": INVOCATION_COUNT,
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise FinalExecutionAcknowledgementIssuanceAuthoringError(
                    f"issuance source differs: {field_name}"
                )
        for field_name in (
            "issuance_authoring_base_commit",
            "acknowledgement_authoring_head_commit",
            "acknowledgement_authoring_parent_commit",
            "acknowledgement_authoring_merge_commit",
        ):
            _require_commit(cast(str, getattr(self, field_name)), field_name)
        for field_name in (
            "acknowledgement_authoring_merge_receipt_sha256",
            "acknowledgement_authoring_sha256",
            "acknowledgement_authoring_file_sha256",
            "acknowledgement_authoring_package_registry_sha256",
            "acknowledgement_authoring_source_registry_sha256",
            "acknowledgement_authoring_module_sha256",
            "acknowledgement_authoring_verifier_sha256",
            "acknowledgement_authoring_test_sha256",
            "acknowledgement_authoring_adr_ru_sha256",
            "acknowledgement_authoring_adr_en_sha256",
        ):
            _require_sha256(cast(str, getattr(self, field_name)), field_name)
        _require_utc(
            self.acknowledgement_authoring_merged_at_utc,
            "acknowledgement_authoring_merged_at_utc",
        )


@dataclass(frozen=True)
class FinalExecutionAcknowledgementIssuanceContract:
    """Prospective persistence rules for an operator acknowledgement."""

    authoring_post_merge_verification_required: bool
    complete_authoring_identity_required: bool
    exact_operator_phrase_required: str
    explicit_operator_identity_required: bool
    explicit_acknowledged_at_utc_required: bool
    acknowledgement_after_authoring_merge_required: bool
    explicit_issuer_identity_required: bool
    explicit_issued_at_utc_required: bool
    issued_at_not_before_acknowledged_at_required: bool
    canonical_json_required: bool
    exact_acknowledgement_path_required: bool
    acknowledgement_target_absent_required: bool
    target_parent_must_preexist: bool
    symbolic_parent_forbidden: bool
    exclusive_atomic_no_overwrite_required: bool
    file_mode_required: str
    file_fsync_required: bool
    parent_directory_fsync_required: bool
    temporary_cleanup_required: bool
    exact_persisted_bytes_reverification_required: bool
    one_issuance_only: bool
    retry_forbidden: bool
    issuance_implementation_separate: bool
    issuance_materialization_separate: bool
    lease_materialization_separate: bool
    issuance_does_not_permit_invocation: bool
    authoring_effects_forbidden: bool

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, object],
    ) -> FinalExecutionAcknowledgementIssuanceContract:
        return cls(**cast(dict[str, Any], dict(value)))

    def require(self) -> None:
        expected = _build_contract()
        if self != expected:
            raise FinalExecutionAcknowledgementIssuanceAuthoringError(
                "issuance contract differs"
            )


@dataclass(frozen=True)
class FinalExecutionAcknowledgementIssuanceGates:
    """Closed production state after issuance-contract authoring."""

    acknowledgement_authoring_post_merge_verified: bool
    final_execution_acknowledgement_authored: bool
    acknowledgement_issuance_contract_authored: bool
    acknowledgement_issuance_implemented: bool
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
    ) -> FinalExecutionAcknowledgementIssuanceGates:
        return cls(**cast(dict[str, Any], dict(value)))

    def require(self) -> None:
        if self != _build_gates():
            raise FinalExecutionAcknowledgementIssuanceAuthoringError(
                "issuance gates differ"
            )


@dataclass(frozen=True)
class FinalExecutionAcknowledgementIssuanceAuthoring:
    """Frozen issuance authoring record; no acknowledgement is issued."""

    schema_version: int
    authoring_id: str
    status: str
    recorded_at_utc: str
    source: FinalExecutionAcknowledgementIssuanceSource
    contract: FinalExecutionAcknowledgementIssuanceContract
    gates: FinalExecutionAcknowledgementIssuanceGates
    next_slice: str
    post_merge_next_slice: str
    authoring_sha256: str

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, object],
    ) -> FinalExecutionAcknowledgementIssuanceAuthoring:
        payload = dict(value)
        payload["source"] = FinalExecutionAcknowledgementIssuanceSource.from_mapping(
            cast(Mapping[str, object], payload["source"])
        )
        payload["contract"] = (
            FinalExecutionAcknowledgementIssuanceContract.from_mapping(
                cast(Mapping[str, object], payload["contract"])
            )
        )
        payload["gates"] = FinalExecutionAcknowledgementIssuanceGates.from_mapping(
            cast(Mapping[str, object], payload["gates"])
        )
        return cls(**cast(dict[str, Any], payload))

    def semantic_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload.pop("authoring_sha256")
        return cast(dict[str, object], payload)

    def require(
        self,
        receipt: AcknowledgementAuthoringMergeValidationReceipt,
    ) -> None:
        if self.schema_version != 1:
            raise FinalExecutionAcknowledgementIssuanceAuthoringError(
                "issuance authoring schema differs"
            )
        if self.authoring_id != FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUANCE_AUTHORING_ID:
            raise FinalExecutionAcknowledgementIssuanceAuthoringError(
                "issuance authoring ID differs"
            )
        if self.status != FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUANCE_AUTHORING_STATUS:
            raise FinalExecutionAcknowledgementIssuanceAuthoringError(
                "issuance authoring status differs"
            )
        _require_utc(self.recorded_at_utc, "recorded_at_utc")
        if self.next_slice != (
            "QW-LC4-E-final-execution-acknowledgement-issuance-authoring-commit"
        ):
            raise FinalExecutionAcknowledgementIssuanceAuthoringError(
                "next slice differs"
            )
        if self.post_merge_next_slice != (
            "QW-LC4-E-final-execution-acknowledgement-issuance-implementation"
        ):
            raise FinalExecutionAcknowledgementIssuanceAuthoringError(
                "post-merge next slice differs"
            )
        self.source.require(receipt)
        self.contract.require()
        self.gates.require()
        _require_sha256(self.authoring_sha256, "authoring_sha256")
        if self.authoring_sha256 != sha256_object(self.semantic_payload()):
            raise FinalExecutionAcknowledgementIssuanceAuthoringError(
                "issuance authoring semantic SHA-256 differs"
            )

    def canonical_json(
        self,
        receipt: AcknowledgementAuthoringMergeValidationReceipt,
    ) -> str:
        self.require(receipt)
        return canonical_json(self)


@dataclass(frozen=True)
class ProspectiveFinalExecutionAcknowledgementIssuance:
    """Pure future issuance envelope; it is never persisted here."""

    issuance_id: str
    status: str
    issuance_authoring_sha256: str
    acknowledgement: ProspectiveFinalExecutionAcknowledgement
    acknowledgement_sha256: str
    issuer_identity: str
    issued_at_utc: str
    acknowledgement_relative: str
    file_mode: str
    exclusive_no_overwrite: bool
    exact_persisted_bytes_required: bool
    retry_permitted: bool
    acknowledgement_materialized: bool
    execution_lease_materialized: bool
    authorization_consumed: bool
    one_shot_engineering_invocation_permitted: bool

    def require(
        self,
        authoring: FinalExecutionAcknowledgementIssuanceAuthoring,
        receipt: AcknowledgementAuthoringMergeValidationReceipt,
        upstream_authoring: FinalExecutionAcknowledgementAuthoring,
        upstream_receipt: WiringMergeValidationReceipt,
    ) -> None:
        authoring.require(receipt)
        self.acknowledgement.require(upstream_authoring, upstream_receipt)
        expected: dict[str, object] = {
            "issuance_id": FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUANCE_ID,
            "status": FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUANCE_STATUS,
            "issuance_authoring_sha256": authoring.authoring_sha256,
            "acknowledgement_sha256": sha256_object(self.acknowledgement),
            "acknowledgement_relative": ACKNOWLEDGEMENT_RELATIVE.as_posix(),
            "file_mode": ACKNOWLEDGEMENT_FILE_MODE,
            "exclusive_no_overwrite": True,
            "exact_persisted_bytes_required": True,
            "retry_permitted": False,
            "acknowledgement_materialized": False,
            "execution_lease_materialized": False,
            "authorization_consumed": False,
            "one_shot_engineering_invocation_permitted": False,
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise FinalExecutionAcknowledgementIssuanceAuthoringError(
                    f"prospective issuance differs: {field_name}"
                )
        if not _IDENTITY_PATTERN.fullmatch(self.issuer_identity):
            raise FinalExecutionAcknowledgementIssuanceAuthoringError(
                "issuer identity is empty or non-canonical"
            )
        issued = _require_utc(self.issued_at_utc, "issued_at_utc")
        acknowledged = _require_utc(
            self.acknowledgement.acknowledged_at_utc,
            "acknowledged_at_utc",
        )
        merged = _require_utc(
            receipt.merged_at_utc,
            "acknowledgement_authoring_merged_at_utc",
        )
        if acknowledged <= merged:
            raise FinalExecutionAcknowledgementIssuanceAuthoringError(
                "acknowledgement timestamp is not after authoring merge"
            )
        if issued < acknowledged:
            raise FinalExecutionAcknowledgementIssuanceAuthoringError(
                "issuance timestamp is before acknowledgement"
            )

    def canonical_json(
        self,
        authoring: FinalExecutionAcknowledgementIssuanceAuthoring,
        receipt: AcknowledgementAuthoringMergeValidationReceipt,
        upstream_authoring: FinalExecutionAcknowledgementAuthoring,
        upstream_receipt: WiringMergeValidationReceipt,
    ) -> str:
        self.require(authoring, receipt, upstream_authoring, upstream_receipt)
        return canonical_json(self)


def build_prospective_acknowledgement_issuance(
    authoring: FinalExecutionAcknowledgementIssuanceAuthoring,
    receipt: AcknowledgementAuthoringMergeValidationReceipt,
    upstream_authoring: FinalExecutionAcknowledgementAuthoring,
    upstream_receipt: WiringMergeValidationReceipt,
    *,
    acknowledgement_phrase: str,
    operator_identity: str,
    acknowledged_at_utc: str,
    issuer_identity: str,
    issued_at_utc: str,
) -> ProspectiveFinalExecutionAcknowledgementIssuance:
    """Build a future issuance envelope without writing any file."""

    authoring.require(receipt)
    acknowledgement = build_final_execution_acknowledgement(
        upstream_authoring,
        upstream_receipt,
        acknowledgement_phrase=acknowledgement_phrase,
        operator_identity=operator_identity,
        acknowledged_at_utc=acknowledged_at_utc,
    )
    result = ProspectiveFinalExecutionAcknowledgementIssuance(
        issuance_id=FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUANCE_ID,
        status=FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUANCE_STATUS,
        issuance_authoring_sha256=authoring.authoring_sha256,
        acknowledgement=acknowledgement,
        acknowledgement_sha256=sha256_object(acknowledgement),
        issuer_identity=issuer_identity,
        issued_at_utc=issued_at_utc,
        acknowledgement_relative=ACKNOWLEDGEMENT_RELATIVE.as_posix(),
        file_mode=ACKNOWLEDGEMENT_FILE_MODE,
        exclusive_no_overwrite=True,
        exact_persisted_bytes_required=True,
        retry_permitted=False,
        acknowledgement_materialized=False,
        execution_lease_materialized=False,
        authorization_consumed=False,
        one_shot_engineering_invocation_permitted=False,
    )
    result.require(authoring, receipt, upstream_authoring, upstream_receipt)
    return result


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8", errors="strict"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FinalExecutionAcknowledgementIssuanceAuthoringError(
            f"cannot load JSON: {path}"
        ) from exc
    if not isinstance(payload, dict):
        raise FinalExecutionAcknowledgementIssuanceAuthoringError(
            f"JSON root is not an object: {path}"
        )
    return cast(dict[str, Any], payload)


def _load_registry(path: Path) -> dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8", errors="strict").splitlines()
    except OSError as exc:
        raise FinalExecutionAcknowledgementIssuanceAuthoringError(
            f"cannot load registry: {path}"
        ) from exc
    result: dict[str, str] = {}
    for line in lines:
        try:
            digest, relative = line.split("  ", 1)
        except ValueError as exc:
            raise FinalExecutionAcknowledgementIssuanceAuthoringError(
                f"malformed registry line: {line!r}"
            ) from exc
        if relative in result:
            raise FinalExecutionAcknowledgementIssuanceAuthoringError(
                f"duplicate registry path: {relative}"
            )
        result[relative] = "sha256:" + digest
    return result


def load_acknowledgement_authoring_merge_validation_receipt(
    path: Path,
) -> AcknowledgementAuthoringMergeValidationReceipt:
    result = AcknowledgementAuthoringMergeValidationReceipt.from_mapping(
        _load_json(path)
    )
    result.require()
    return result


def load_final_execution_acknowledgement_issuance_authoring(
    path: Path,
    receipt: AcknowledgementAuthoringMergeValidationReceipt,
) -> FinalExecutionAcknowledgementIssuanceAuthoring:
    result = FinalExecutionAcknowledgementIssuanceAuthoring.from_mapping(
        _load_json(path)
    )
    result.require(receipt)
    return result


def verify_final_execution_acknowledgement_issuance_authoring(
    project_root: Path,
) -> FinalExecutionAcknowledgementIssuanceAuthoring:
    """Verify the static issuance contract and closed production boundary."""

    root = project_root.expanduser().resolve()
    package = root / PACKAGE_RELATIVE
    if not package.is_dir() or package.is_symlink():
        raise FinalExecutionAcknowledgementIssuanceAuthoringError(
            "issuance authoring package is absent or invalid"
        )
    if frozenset(path.name for path in package.iterdir()) != _EXPECTED_PACKAGE_FILES:
        raise FinalExecutionAcknowledgementIssuanceAuthoringError(
            "issuance authoring package file set differs"
        )
    package_registry = _verify_registry(root / REGISTRY_RELATIVE, package)
    if frozenset(package_registry) != frozenset(
        {
            "authoring-merge-validation.json",
            "authoring.json",
            "source-SHA256SUMS",
        }
    ):
        raise FinalExecutionAcknowledgementIssuanceAuthoringError(
            "issuance package registry scope differs"
        )
    source_registry = _verify_registry(root / SOURCE_REGISTRY_RELATIVE, root)
    if frozenset(source_registry) != _EXPECTED_SOURCE_PATHS:
        raise FinalExecutionAcknowledgementIssuanceAuthoringError(
            "issuance source registry scope differs"
        )
    receipt = load_acknowledgement_authoring_merge_validation_receipt(
        root / AUTHORING_MERGE_RECEIPT_RELATIVE
    )
    authoring = load_final_execution_acknowledgement_issuance_authoring(
        root / AUTHORING_RECORD_RELATIVE,
        receipt,
    )
    upstream_authoring = verify_final_execution_acknowledgement_authoring(root)
    _verify_upstream_records(root, authoring, upstream_authoring)
    _verify_effect_free_authoring_ast(root)
    _require_repository_boundary_closed(root)
    return authoring


def _verify_registry(path: Path, base: Path) -> dict[str, str]:
    registry = _load_registry(path)
    for relative, expected in registry.items():
        target = base / relative
        if not target.is_file() or target.is_symlink():
            raise FinalExecutionAcknowledgementIssuanceAuthoringError(
                f"registry target is absent or invalid: {relative}"
            )
        observed = sha256_bytes(target.read_bytes())
        if observed != expected:
            raise FinalExecutionAcknowledgementIssuanceAuthoringError(
                f"registry digest differs: {relative}"
            )
    return registry


def _verify_upstream_records(
    root: Path,
    authoring: FinalExecutionAcknowledgementIssuanceAuthoring,
    upstream_authoring: FinalExecutionAcknowledgementAuthoring,
) -> None:
    exact_files = (
        (UPSTREAM_AUTHORING_RECORD_RELATIVE, ACKNOWLEDGEMENT_AUTHORING_FILE_SHA256),
        (
            UPSTREAM_PACKAGE_REGISTRY_RELATIVE,
            ACKNOWLEDGEMENT_AUTHORING_PACKAGE_REGISTRY_SHA256,
        ),
        (
            UPSTREAM_SOURCE_REGISTRY_RELATIVE,
            ACKNOWLEDGEMENT_AUTHORING_SOURCE_REGISTRY_SHA256,
        ),
        (UPSTREAM_MODULE_RELATIVE, ACKNOWLEDGEMENT_AUTHORING_MODULE_SHA256),
        (UPSTREAM_VERIFIER_RELATIVE, ACKNOWLEDGEMENT_AUTHORING_VERIFIER_SHA256),
        (UPSTREAM_TEST_RELATIVE, ACKNOWLEDGEMENT_AUTHORING_TEST_SHA256),
        (UPSTREAM_ADR_RU_RELATIVE, ACKNOWLEDGEMENT_AUTHORING_ADR_RU_SHA256),
        (UPSTREAM_ADR_EN_RELATIVE, ACKNOWLEDGEMENT_AUTHORING_ADR_EN_SHA256),
    )
    for relative, expected in exact_files:
        if sha256_bytes((root / relative).read_bytes()) != expected:
            raise FinalExecutionAcknowledgementIssuanceAuthoringError(
                f"upstream authoring file SHA-256 differs: {relative}"
            )
    if upstream_authoring.authoring_id != FINAL_EXECUTION_ACKNOWLEDGEMENT_AUTHORING_ID:
        raise FinalExecutionAcknowledgementIssuanceAuthoringError(
            "upstream acknowledgement authoring ID differs"
        )
    if upstream_authoring.authoring_sha256 != ACKNOWLEDGEMENT_AUTHORING_SHA256:
        raise FinalExecutionAcknowledgementIssuanceAuthoringError(
            "upstream acknowledgement authoring semantic SHA-256 differs"
        )
    if upstream_authoring.gates.final_execution_acknowledgement_issued:
        raise FinalExecutionAcknowledgementIssuanceAuthoringError(
            "upstream authoring unexpectedly records an issued acknowledgement"
        )
    if authoring.source.acknowledgement_authoring_sha256 != (
        upstream_authoring.authoring_sha256
    ):
        raise FinalExecutionAcknowledgementIssuanceAuthoringError(
            "issuance source does not bind upstream authoring"
        )


def _verify_effect_free_authoring_ast(root: Path) -> None:
    tree = ast.parse(
        (root / MODULE_RELATIVE).read_text(encoding="utf-8", errors="strict")
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".", 1)[0] in _FORBIDDEN_IMPORT_ROOTS:
                    raise FinalExecutionAcknowledgementIssuanceAuthoringError(
                        f"forbidden authoring import: {alias.name}"
                    )
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split(".", 1)[0] in _FORBIDDEN_IMPORT_ROOTS:
                raise FinalExecutionAcknowledgementIssuanceAuthoringError(
                    f"forbidden authoring import: {node.module}"
                )
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in _FORBIDDEN_CALL_NAMES:
                raise FinalExecutionAcknowledgementIssuanceAuthoringError(
                    f"forbidden authoring call: {node.func.id}"
                )
            if (
                isinstance(node.func, ast.Attribute)
                and node.func.attr in _FORBIDDEN_CALL_ATTRIBUTES
            ):
                raise FinalExecutionAcknowledgementIssuanceAuthoringError(
                    f"forbidden authoring call: {node.func.attr}"
                )


def _require_repository_boundary_closed(root: Path) -> None:
    output = root / AUTHORIZED_OUTPUT_ROOT
    acknowledgement = root / ACKNOWLEDGEMENT_RELATIVE
    lease_v1 = root / (AUTHORIZED_OUTPUT_ROOT + ".execution-lease.json")
    lease_v2 = root / EXECUTION_LEASE_V2_RELATIVE
    outcome = root / DURABLE_HOST_OUTCOME_RELATIVE
    for path, label in (
        (output, "runtime output"),
        (acknowledgement, "final execution acknowledgement"),
        (lease_v1, "execution lease v1"),
        (lease_v2, "execution lease v2"),
        (outcome, "durable host outcome"),
    ):
        if path.exists() or path.is_symlink():
            raise FinalExecutionAcknowledgementIssuanceAuthoringError(
                f"{label} exists during issuance authoring"
            )
    parent = output.parent
    pattern = ".qwake-lc4-runtime-validation-v1-attempt-001.staging-*"
    if parent.is_dir() and any(parent.glob(pattern)):
        raise FinalExecutionAcknowledgementIssuanceAuthoringError(
            "runtime staging path exists during issuance authoring"
        )


def _build_source(
    receipt: AcknowledgementAuthoringMergeValidationReceipt,
) -> FinalExecutionAcknowledgementIssuanceSource:
    return FinalExecutionAcknowledgementIssuanceSource(
        issuance_authoring_base_commit=ISSUANCE_AUTHORING_BASE_COMMIT,
        acknowledgement_authoring_pr_number=ACKNOWLEDGEMENT_AUTHORING_PR_NUMBER,
        acknowledgement_authoring_head_commit=ACKNOWLEDGEMENT_AUTHORING_HEAD_COMMIT,
        acknowledgement_authoring_parent_commit=(
            ACKNOWLEDGEMENT_AUTHORING_PARENT_COMMIT
        ),
        acknowledgement_authoring_merge_commit=(
            ACKNOWLEDGEMENT_AUTHORING_MERGE_COMMIT
        ),
        acknowledgement_authoring_merged_at_utc=(
            ACKNOWLEDGEMENT_AUTHORING_MERGED_AT_UTC
        ),
        acknowledgement_authoring_merge_receipt_sha256=receipt.receipt_sha256,
        acknowledgement_authoring_id=FINAL_EXECUTION_ACKNOWLEDGEMENT_AUTHORING_ID,
        acknowledgement_authoring_sha256=ACKNOWLEDGEMENT_AUTHORING_SHA256,
        acknowledgement_authoring_file_sha256=(
            ACKNOWLEDGEMENT_AUTHORING_FILE_SHA256
        ),
        acknowledgement_authoring_package_registry_sha256=(
            ACKNOWLEDGEMENT_AUTHORING_PACKAGE_REGISTRY_SHA256
        ),
        acknowledgement_authoring_source_registry_sha256=(
            ACKNOWLEDGEMENT_AUTHORING_SOURCE_REGISTRY_SHA256
        ),
        acknowledgement_authoring_module_sha256=(
            ACKNOWLEDGEMENT_AUTHORING_MODULE_SHA256
        ),
        acknowledgement_authoring_verifier_sha256=(
            ACKNOWLEDGEMENT_AUTHORING_VERIFIER_SHA256
        ),
        acknowledgement_authoring_test_sha256=ACKNOWLEDGEMENT_AUTHORING_TEST_SHA256,
        acknowledgement_authoring_adr_ru_sha256=(
            ACKNOWLEDGEMENT_AUTHORING_ADR_RU_SHA256
        ),
        acknowledgement_authoring_adr_en_sha256=(
            ACKNOWLEDGEMENT_AUTHORING_ADR_EN_SHA256
        ),
        acknowledgement_id=FINAL_EXECUTION_ACKNOWLEDGEMENT_ID,
        acknowledgement_relative=ACKNOWLEDGEMENT_RELATIVE.as_posix(),
        image_repo_digest=IMAGE_REPO_DIGEST,
        torch2pc_commit=TORCH2PC_COMMIT,
        output_root=AUTHORIZED_OUTPUT_ROOT,
        execution_lease_v2_relative=EXECUTION_LEASE_V2_RELATIVE.as_posix(),
        durable_host_outcome_relative=DURABLE_HOST_OUTCOME_RELATIVE.as_posix(),
        invocation_count=INVOCATION_COUNT,
    )


def _build_contract() -> FinalExecutionAcknowledgementIssuanceContract:
    return FinalExecutionAcknowledgementIssuanceContract(
        authoring_post_merge_verification_required=True,
        complete_authoring_identity_required=True,
        exact_operator_phrase_required=FINAL_EXECUTION_OPERATOR_ACKNOWLEDGEMENT,
        explicit_operator_identity_required=True,
        explicit_acknowledged_at_utc_required=True,
        acknowledgement_after_authoring_merge_required=True,
        explicit_issuer_identity_required=True,
        explicit_issued_at_utc_required=True,
        issued_at_not_before_acknowledged_at_required=True,
        canonical_json_required=True,
        exact_acknowledgement_path_required=True,
        acknowledgement_target_absent_required=True,
        target_parent_must_preexist=True,
        symbolic_parent_forbidden=True,
        exclusive_atomic_no_overwrite_required=True,
        file_mode_required=ACKNOWLEDGEMENT_FILE_MODE,
        file_fsync_required=True,
        parent_directory_fsync_required=True,
        temporary_cleanup_required=True,
        exact_persisted_bytes_reverification_required=True,
        one_issuance_only=True,
        retry_forbidden=True,
        issuance_implementation_separate=True,
        issuance_materialization_separate=True,
        lease_materialization_separate=True,
        issuance_does_not_permit_invocation=True,
        authoring_effects_forbidden=True,
    )


def _build_gates() -> FinalExecutionAcknowledgementIssuanceGates:
    return FinalExecutionAcknowledgementIssuanceGates(
        acknowledgement_authoring_post_merge_verified=True,
        final_execution_acknowledgement_authored=True,
        acknowledgement_issuance_contract_authored=True,
        acknowledgement_issuance_implemented=False,
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


def build_frozen_issuance_authoring_record(
    receipt: AcknowledgementAuthoringMergeValidationReceipt,
) -> FinalExecutionAcknowledgementIssuanceAuthoring:
    """Build the canonical static issuance-authoring record."""

    receipt.require()
    provisional = FinalExecutionAcknowledgementIssuanceAuthoring(
        schema_version=1,
        authoring_id=FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUANCE_AUTHORING_ID,
        status=FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUANCE_AUTHORING_STATUS,
        recorded_at_utc="2026-07-30T16:20:00Z",
        source=_build_source(receipt),
        contract=_build_contract(),
        gates=_build_gates(),
        next_slice=(
            "QW-LC4-E-final-execution-acknowledgement-issuance-authoring-commit"
        ),
        post_merge_next_slice=(
            "QW-LC4-E-final-execution-acknowledgement-issuance-implementation"
        ),
        authoring_sha256="sha256:" + "0" * 64,
    )
    result = replace(
        provisional,
        authoring_sha256=sha256_object(provisional.semantic_payload()),
    )
    result.require(receipt)
    return result


def build_acknowledgement_authoring_merge_validation_receipt(
) -> AcknowledgementAuthoringMergeValidationReceipt:
    """Build the exact independently verified PR #147 merge receipt."""

    provisional = AcknowledgementAuthoringMergeValidationReceipt(
        receipt_id=(
            "stage3b-qwake-lc4-e-final-execution-acknowledgement-"
            "authoring-post-merge-validation-v1"
        ),
        pr_number=147,
        head_commit=ACKNOWLEDGEMENT_AUTHORING_HEAD_COMMIT,
        base_commit=ACKNOWLEDGEMENT_AUTHORING_PARENT_COMMIT,
        merge_commit=ACKNOWLEDGEMENT_AUTHORING_MERGE_COMMIT,
        merged_at_utc=ACKNOWLEDGEMENT_AUTHORING_MERGED_AT_UTC,
        commit_count=1,
        file_count=18,
        focused_tests_passed=50,
        targeted_tests_passed=251,
        full_tests_passed=1298,
        full_test_warnings=14,
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
