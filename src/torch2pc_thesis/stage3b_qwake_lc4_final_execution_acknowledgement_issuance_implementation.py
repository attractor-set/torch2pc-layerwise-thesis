"""Fail-closed persistence for final-execution acknowledgement issuance.

The module implements an exclusive durable writer and exact verifier for the
already-authored final-execution acknowledgement issuance envelope. Importing
or statically verifying this module does not write the production
acknowledgement, create a lease or outcome, inspect an image, materialize a
command, spawn a process, invoke Docker, consume authorization, or execute
local compute.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import secrets
import stat
from collections.abc import Mapping
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final, cast

from .stage3b_qwake_lc4_final_execution_acknowledgement_authoring import (
    DURABLE_HOST_OUTCOME_RELATIVE,
    EXECUTION_LEASE_V2_RELATIVE,
    FinalExecutionAcknowledgementAuthoring,
    FinalExecutionAcknowledgementAuthoringError,
    WiringMergeValidationReceipt,
    load_final_execution_acknowledgement_authoring,
    load_wiring_merge_validation_receipt,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_issuance_authoring import (
    ACKNOWLEDGEMENT_RELATIVE,
    AUTHORING_RECORD_RELATIVE,
    UPSTREAM_AUTHORING_RECORD_RELATIVE,
    UPSTREAM_WIRING_RECEIPT_RELATIVE,
    AcknowledgementAuthoringMergeValidationReceipt,
    FinalExecutionAcknowledgementIssuanceAuthoring,
    FinalExecutionAcknowledgementIssuanceAuthoringError,
    ProspectiveFinalExecutionAcknowledgementIssuance,
    canonical_json,
    load_acknowledgement_authoring_merge_validation_receipt,
    load_final_execution_acknowledgement_issuance_authoring,
    sha256_bytes,
    sha256_object,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_issuance_authoring import (
    ADR_EN_RELATIVE as AUTHORING_ADR_EN_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_issuance_authoring import (
    ADR_RU_RELATIVE as AUTHORING_ADR_RU_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_issuance_authoring import (
    AUTHORING_MERGE_RECEIPT_RELATIVE as ISSUANCE_AUTHORING_MERGE_RECEIPT_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_issuance_authoring import (
    MODULE_RELATIVE as AUTHORING_MODULE_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_issuance_authoring import (
    PACKAGE_RELATIVE as AUTHORING_PACKAGE_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_issuance_authoring import (
    REGISTRY_RELATIVE as AUTHORING_REGISTRY_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_issuance_authoring import (
    SOURCE_REGISTRY_RELATIVE as AUTHORING_SOURCE_REGISTRY_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_issuance_authoring import (
    TEST_RELATIVE as AUTHORING_TEST_RELATIVE,
)
from .stage3b_qwake_lc4_final_execution_acknowledgement_issuance_authoring import (
    VERIFIER_RELATIVE as AUTHORING_VERIFIER_RELATIVE,
)

FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUANCE_IMPLEMENTATION_ID: Final = (
    "stage3b-qwake-lc4-e-final-execution-acknowledgement-issuance-implementation-v1"
)
FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUANCE_IMPLEMENTATION_STATUS: Final = (
    "acknowledgement_writer_implemented_not_issued_execution_closed"
)
IMPLEMENTATION_BASE_COMMIT: Final = "8343724c66b1d22f01846d9fc70f01738a09127a"
AUTHORING_PR_NUMBER: Final = 148
AUTHORING_HEAD_COMMIT: Final = "a3984013f8861a532b3f29e234ed1c61be670d97"
AUTHORING_PARENT_COMMIT: Final = "eb20c157584efff8e9aa0418385242c7d7b26eab"
AUTHORING_MERGE_COMMIT: Final = IMPLEMENTATION_BASE_COMMIT
AUTHORING_MERGED_AT_UTC: Final = "2026-07-30T17:12:05Z"

AUTHORING_SHA256: Final = (
    "sha256:e40cd617d9485fa141f172b4efc637000b2746081441a2955bb699e8905b2217"
)
AUTHORING_FILE_SHA256: Final = (
    "sha256:aefec22c93cbaf1ddedc188497b8589308ac4b1a950810927d5d8735125db1e6"
)
AUTHORING_PACKAGE_REGISTRY_SHA256: Final = (
    "sha256:2c67780c2cd563512ba781bd44ac9fca454e4aa2129a8874bd6e2a35f2270620"
)
AUTHORING_SOURCE_REGISTRY_SHA256: Final = (
    "sha256:042d50e366112d13778aa8f727c00122b3da413aafe7e31fc8b881b1cf8fc3a5"
)
AUTHORING_MODULE_SHA256: Final = (
    "sha256:d8331326d6df098cabe041e42f78b5aab6cfa38c243b52c1b20dcd040540c209"
)
AUTHORING_VERIFIER_SHA256: Final = (
    "sha256:155be9a79804a3ff8e3b3161fe3b98591972085b46931d050d8cc362e5948266"
)
AUTHORING_TEST_SHA256: Final = (
    "sha256:10a547899ee5fe4179a6730386a6c5e5defd0e78f1297e53f8c31e00798fe8f7"
)
AUTHORING_ADR_RU_SHA256: Final = (
    "sha256:162ca46de9d8d483e40376fab55bdbadb004c3eb593bf10a8bce9cde9c6370e2"
)
AUTHORING_ADR_EN_SHA256: Final = (
    "sha256:00d2697e3e13eb0483166643c884976afab387ff44da10e02979b3177ffa1512"
)

LEGACY_EXECUTION_LEASE_RELATIVE: Final = Path(
    "results/stage-3/"
    "qwake-lc4-runtime-validation-v1-attempt-001.execution-lease.json"
)

IMPLEMENTATION_PACKAGE_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-final-execution-acknowledgement-issuance-implementation-v1"
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
        ISSUANCE_AUTHORING_MERGE_RECEIPT_RELATIVE.as_posix(),
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
_FORBIDDEN_IMPORT_ROOTS: Final = frozenset({"subprocess", "docker"})
_FORBIDDEN_RUNTIME_CALLS: Final = frozenset(
    {
        "invoke_lease_bound_host_runtime",
        "invoke_one_shot_host_runtime",
        "inspect_local_image",
        "materialize_invocation_command",
        "persist_persistent_execution_lease_v2",
        "persist_durable_host_outcome_receipt",
    }
)

__all__ = [
    "FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUANCE_IMPLEMENTATION_ID",
    "AcknowledgementIssuanceAuthoringMergeValidationReceipt",
    "AcknowledgementIssuanceImplementationError",
    "AcknowledgementIssuanceImplementationRecord",
    "PersistentAcknowledgementWriteResult",
    "build_acknowledgement_issuance_authoring_merge_validation_receipt",
    "build_frozen_acknowledgement_issuance_implementation_record",
    "load_acknowledgement_issuance_authoring_merge_validation_receipt",
    "load_acknowledgement_issuance_implementation_record",
    "persist_final_execution_acknowledgement",
    "verify_final_execution_acknowledgement_issuance_implementation",
    "verify_persisted_final_execution_acknowledgement",
]


class AcknowledgementIssuanceImplementationError(RuntimeError):
    """Raised when implementation or persistent issuance fails closed."""


def _require_sha256(value: str, field_name: str) -> None:
    if not _SHA256_PATTERN.fullmatch(value):
        raise AcknowledgementIssuanceImplementationError(
            f"{field_name} is not a canonical SHA-256 identity"
        )


def _require_commit(value: str, field_name: str) -> None:
    if not _COMMIT_PATTERN.fullmatch(value):
        raise AcknowledgementIssuanceImplementationError(
            f"{field_name} is not a commit identity"
        )


def _require_utc(value: str, field_name: str) -> datetime:
    if not value.endswith("Z"):
        raise AcknowledgementIssuanceImplementationError(
            f"{field_name} is not a UTC timestamp"
        )
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise AcknowledgementIssuanceImplementationError(
            f"{field_name} is not an ISO-8601 timestamp"
        ) from exc
    if parsed.tzinfo != UTC:
        raise AcknowledgementIssuanceImplementationError(
            f"{field_name} is not normalized to UTC"
        )
    return parsed


@dataclass(frozen=True)
class AcknowledgementIssuanceAuthoringMergeValidationReceipt:
    """Exact post-merge receipt for issuance-authoring PR #148."""

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
    acknowledgement_absent: bool
    production_execution_boundary_closed: bool
    receipt_sha256: str

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, object],
    ) -> AcknowledgementIssuanceAuthoringMergeValidationReceipt:
        return cls(**cast(dict[str, Any], dict(value)))

    def semantic_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload.pop("receipt_sha256")
        return cast(dict[str, object], payload)

    def require(self) -> None:
        expected: dict[str, object] = {
            "receipt_id": (
                "stage3b-qwake-lc4-e-final-execution-acknowledgement-"
                "issuance-authoring-post-merge-validation-v1"
            ),
            "pr_number": AUTHORING_PR_NUMBER,
            "head_commit": AUTHORING_HEAD_COMMIT,
            "base_commit": AUTHORING_PARENT_COMMIT,
            "merge_commit": AUTHORING_MERGE_COMMIT,
            "merged_at_utc": AUTHORING_MERGED_AT_UTC,
            "commit_count": 1,
            "file_count": 18,
            "focused_tests_passed": 61,
            "targeted_tests_passed": 262,
            "full_tests_passed": 1309,
            "full_test_warnings": 14,
            "required_ci_checks_passed": True,
            "acknowledgement_absent": True,
            "production_execution_boundary_closed": True,
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise AcknowledgementIssuanceImplementationError(
                    f"issuance-authoring merge receipt differs: {field_name}"
                )
        _require_commit(self.head_commit, "head_commit")
        _require_commit(self.base_commit, "base_commit")
        _require_commit(self.merge_commit, "merge_commit")
        _require_utc(self.merged_at_utc, "merged_at_utc")
        _require_sha256(self.receipt_sha256, "receipt_sha256")
        if self.receipt_sha256 != sha256_object(self.semantic_payload()):
            raise AcknowledgementIssuanceImplementationError(
                "issuance-authoring merge receipt semantic SHA-256 differs"
            )

    def canonical_json(self) -> str:
        self.require()
        return canonical_json(self)


@dataclass(frozen=True)
class AcknowledgementIssuanceImplementationSource:
    """Complete identity of the merged issuance-authoring package."""

    implementation_base_commit: str
    authoring_pr_number: int
    authoring_head_commit: str
    authoring_parent_commit: str
    authoring_merge_commit: str
    authoring_merged_at_utc: str
    authoring_merge_receipt_sha256: str
    authoring_id: str
    authoring_sha256: str
    authoring_file_sha256: str
    authoring_package_registry_sha256: str
    authoring_source_registry_sha256: str
    authoring_module_sha256: str
    authoring_verifier_sha256: str
    authoring_test_sha256: str
    authoring_adr_ru_sha256: str
    authoring_adr_en_sha256: str
    acknowledgement_relative: str
    legacy_execution_lease_relative: str
    execution_lease_v2_relative: str
    durable_host_outcome_relative: str

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, object],
    ) -> AcknowledgementIssuanceImplementationSource:
        return cls(**cast(dict[str, Any], dict(value)))

    def require(
        self,
        receipt: AcknowledgementIssuanceAuthoringMergeValidationReceipt,
    ) -> None:
        expected: dict[str, object] = {
            "implementation_base_commit": IMPLEMENTATION_BASE_COMMIT,
            "authoring_pr_number": AUTHORING_PR_NUMBER,
            "authoring_head_commit": AUTHORING_HEAD_COMMIT,
            "authoring_parent_commit": AUTHORING_PARENT_COMMIT,
            "authoring_merge_commit": AUTHORING_MERGE_COMMIT,
            "authoring_merged_at_utc": AUTHORING_MERGED_AT_UTC,
            "authoring_merge_receipt_sha256": receipt.receipt_sha256,
            "authoring_id": (
                "stage3b-qwake-lc4-e-final-execution-"
                "acknowledgement-issuance-authoring-v1"
            ),
            "authoring_sha256": AUTHORING_SHA256,
            "authoring_file_sha256": AUTHORING_FILE_SHA256,
            "authoring_package_registry_sha256": (
                AUTHORING_PACKAGE_REGISTRY_SHA256
            ),
            "authoring_source_registry_sha256": (
                AUTHORING_SOURCE_REGISTRY_SHA256
            ),
            "authoring_module_sha256": AUTHORING_MODULE_SHA256,
            "authoring_verifier_sha256": AUTHORING_VERIFIER_SHA256,
            "authoring_test_sha256": AUTHORING_TEST_SHA256,
            "authoring_adr_ru_sha256": AUTHORING_ADR_RU_SHA256,
            "authoring_adr_en_sha256": AUTHORING_ADR_EN_SHA256,
            "acknowledgement_relative": ACKNOWLEDGEMENT_RELATIVE.as_posix(),
            "legacy_execution_lease_relative": (
                LEGACY_EXECUTION_LEASE_RELATIVE.as_posix()
            ),
            "execution_lease_v2_relative": EXECUTION_LEASE_V2_RELATIVE.as_posix(),
            "durable_host_outcome_relative": DURABLE_HOST_OUTCOME_RELATIVE.as_posix(),
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise AcknowledgementIssuanceImplementationError(
                    f"implementation source differs: {field_name}"
                )
        for field_name in (
            "implementation_base_commit",
            "authoring_head_commit",
            "authoring_parent_commit",
            "authoring_merge_commit",
        ):
            _require_commit(cast(str, getattr(self, field_name)), field_name)
        for field_name in (
            "authoring_merge_receipt_sha256",
            "authoring_sha256",
            "authoring_file_sha256",
            "authoring_package_registry_sha256",
            "authoring_source_registry_sha256",
            "authoring_module_sha256",
            "authoring_verifier_sha256",
            "authoring_test_sha256",
            "authoring_adr_ru_sha256",
            "authoring_adr_en_sha256",
        ):
            _require_sha256(cast(str, getattr(self, field_name)), field_name)
        _require_utc(self.authoring_merged_at_utc, "authoring_merged_at_utc")


@dataclass(frozen=True)
class AcknowledgementIssuanceImplementationContract:
    """Implemented persistence properties without production materialization."""

    complete_authoring_identity_verified: bool
    canonical_issuance_envelope_required: bool
    exact_acknowledgement_path_enforced: bool
    production_boundary_absence_required: bool
    target_parent_must_preexist: bool
    symbolic_parent_chain_forbidden: bool
    stale_temporary_collision_forbidden: bool
    exclusive_atomic_no_overwrite_implemented: bool
    file_mode: str
    file_fsync_implemented: bool
    parent_directory_fsync_implemented: bool
    temporary_cleanup_implemented: bool
    exact_persisted_bytes_reverification_implemented: bool
    regular_file_required: bool
    retry_forbidden: bool
    production_materialization_separate: bool
    repository_production_callsite_forbidden: bool
    image_inspection_forbidden: bool
    command_materialization_forbidden: bool
    subprocess_forbidden: bool
    docker_forbidden: bool
    local_compute_forbidden: bool

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, object],
    ) -> AcknowledgementIssuanceImplementationContract:
        return cls(**cast(dict[str, Any], dict(value)))

    def require(self) -> None:
        if self != _build_contract():
            raise AcknowledgementIssuanceImplementationError(
                "implementation contract differs"
            )


@dataclass(frozen=True)
class AcknowledgementIssuanceImplementationGates:
    """Closed production state after writer implementation."""

    acknowledgement_issuance_authoring_post_merge_verified: bool
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
    ) -> AcknowledgementIssuanceImplementationGates:
        return cls(**cast(dict[str, Any], dict(value)))

    def require(self) -> None:
        if self != _build_gates():
            raise AcknowledgementIssuanceImplementationError(
                "implementation gates differ"
            )


@dataclass(frozen=True)
class AcknowledgementIssuanceImplementationRecord:
    """Frozen implementation record; production acknowledgement is absent."""

    schema_version: int
    implementation_id: str
    status: str
    recorded_at_utc: str
    source: AcknowledgementIssuanceImplementationSource
    contract: AcknowledgementIssuanceImplementationContract
    gates: AcknowledgementIssuanceImplementationGates
    next_slice: str
    post_merge_next_slice: str
    implementation_sha256: str

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, object],
    ) -> AcknowledgementIssuanceImplementationRecord:
        payload = dict(value)
        payload["source"] = AcknowledgementIssuanceImplementationSource.from_mapping(
            cast(Mapping[str, object], payload["source"])
        )
        payload["contract"] = AcknowledgementIssuanceImplementationContract.from_mapping(
            cast(Mapping[str, object], payload["contract"])
        )
        payload["gates"] = AcknowledgementIssuanceImplementationGates.from_mapping(
            cast(Mapping[str, object], payload["gates"])
        )
        return cls(**cast(dict[str, Any], payload))

    def semantic_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload.pop("implementation_sha256")
        return cast(dict[str, object], payload)

    def require(
        self,
        receipt: AcknowledgementIssuanceAuthoringMergeValidationReceipt,
    ) -> None:
        if self.schema_version != 1:
            raise AcknowledgementIssuanceImplementationError(
                "implementation schema differs"
            )
        if self.implementation_id != (
            FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUANCE_IMPLEMENTATION_ID
        ):
            raise AcknowledgementIssuanceImplementationError(
                "implementation ID differs"
            )
        if self.status != (
            FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUANCE_IMPLEMENTATION_STATUS
        ):
            raise AcknowledgementIssuanceImplementationError(
                "implementation status differs"
            )
        _require_utc(self.recorded_at_utc, "recorded_at_utc")
        if self.next_slice != (
            "QW-LC4-E-final-execution-acknowledgement-issuance-implementation-commit"
        ):
            raise AcknowledgementIssuanceImplementationError(
                "implementation next slice differs"
            )
        if self.post_merge_next_slice != (
            "QW-LC4-E-final-execution-acknowledgement-issuance-materialization"
        ):
            raise AcknowledgementIssuanceImplementationError(
                "implementation post-merge next slice differs"
            )
        self.source.require(receipt)
        self.contract.require()
        self.gates.require()
        _require_sha256(self.implementation_sha256, "implementation_sha256")
        if self.implementation_sha256 != sha256_object(self.semantic_payload()):
            raise AcknowledgementIssuanceImplementationError(
                "implementation semantic SHA-256 differs"
            )

    def canonical_json(
        self,
        receipt: AcknowledgementIssuanceAuthoringMergeValidationReceipt,
    ) -> str:
        self.require(receipt)
        return canonical_json(self)


@dataclass(frozen=True)
class PersistentAcknowledgementWriteResult:
    """Identity of one successfully persisted acknowledgement envelope."""

    relative_path: str
    byte_count: int
    sha256: str
    mode: int

    def require(self) -> None:
        if not self.relative_path or Path(self.relative_path).is_absolute():
            raise AcknowledgementIssuanceImplementationError(
                "persistent acknowledgement result path is invalid"
            )
        if self.relative_path != ACKNOWLEDGEMENT_RELATIVE.as_posix():
            raise AcknowledgementIssuanceImplementationError(
                "persistent acknowledgement result path differs"
            )
        if self.byte_count <= 0:
            raise AcknowledgementIssuanceImplementationError(
                "persistent acknowledgement result is empty"
            )
        _require_sha256(self.sha256, "persistent acknowledgement result digest")
        if self.mode != 0o600:
            raise AcknowledgementIssuanceImplementationError(
                "persistent acknowledgement result mode differs"
            )


def persist_final_execution_acknowledgement(
    project_root: Path,
    authoring: FinalExecutionAcknowledgementIssuanceAuthoring,
    authoring_receipt: AcknowledgementAuthoringMergeValidationReceipt,
    upstream_authoring: FinalExecutionAcknowledgementAuthoring,
    upstream_receipt: WiringMergeValidationReceipt,
    issuance: ProspectiveFinalExecutionAcknowledgementIssuance,
) -> PersistentAcknowledgementWriteResult:
    """Persist one immutable acknowledgement envelope after exact checks.

    The function writes only the acknowledgement envelope. It does not create
    the execution lease, inspect the image, materialize a command, invoke the
    host runtime, consume authorization, or execute local compute.
    """

    root = _verified_root(
        project_root,
        authoring,
        authoring_receipt,
        upstream_authoring,
        upstream_receipt,
        require_closed_boundary=True,
    )
    _require_issuance(
        authoring,
        authoring_receipt,
        upstream_authoring,
        upstream_receipt,
        issuance,
    )
    output_root = _target(root, Path(authoring.source.output_root))
    acknowledgement_target = _target(root, ACKNOWLEDGEMENT_RELATIVE)
    legacy_lease = _target(root, LEGACY_EXECUTION_LEASE_RELATIVE)
    lease_v2 = _target(root, EXECUTION_LEASE_V2_RELATIVE)
    outcome = _target(root, DURABLE_HOST_OUTCOME_RELATIVE)

    _require_absent(output_root, "authorized output root")
    _require_absent(acknowledgement_target, "final execution acknowledgement")
    _require_absent(legacy_lease, "legacy execution lease")
    _require_absent(lease_v2, "persistent execution lease v2")
    _require_absent(outcome, "durable host outcome")
    _require_no_stale_temporaries(acknowledgement_target)

    payload = issuance.canonical_json(
        authoring,
        authoring_receipt,
        upstream_authoring,
        upstream_receipt,
    ).encode("utf-8")
    return _atomic_write_once(root, acknowledgement_target, payload)


def verify_persisted_final_execution_acknowledgement(
    project_root: Path,
    authoring: FinalExecutionAcknowledgementIssuanceAuthoring,
    authoring_receipt: AcknowledgementAuthoringMergeValidationReceipt,
    upstream_authoring: FinalExecutionAcknowledgementAuthoring,
    upstream_receipt: WiringMergeValidationReceipt,
    issuance: ProspectiveFinalExecutionAcknowledgementIssuance,
) -> PersistentAcknowledgementWriteResult:
    """Verify exact persisted acknowledgement bytes and filesystem identity."""

    root = _verified_root(
        project_root,
        authoring,
        authoring_receipt,
        upstream_authoring,
        upstream_receipt,
        require_closed_boundary=False,
    )
    _require_issuance(
        authoring,
        authoring_receipt,
        upstream_authoring,
        upstream_receipt,
        issuance,
    )
    payload = issuance.canonical_json(
        authoring,
        authoring_receipt,
        upstream_authoring,
        upstream_receipt,
    ).encode("utf-8")
    return _verify_exact_file(
        root,
        _target(root, ACKNOWLEDGEMENT_RELATIVE),
        payload,
    )


def verify_final_execution_acknowledgement_issuance_implementation(
    project_root: Path,
) -> AcknowledgementIssuanceImplementationRecord:
    """Verify the frozen implementation package without materialization."""

    root = _verified_project_root(project_root)
    receipt, record = _verify_implementation_freeze(root)
    _verify_static_authoring_chain(root)
    _verify_runtime_ast_boundary(root)
    _require_repository_production_callsite_absent(root)
    _require_production_boundary_closed(root)
    record.require(receipt)
    return record


def _require_issuance(
    authoring: FinalExecutionAcknowledgementIssuanceAuthoring,
    receipt: AcknowledgementAuthoringMergeValidationReceipt,
    upstream_authoring: FinalExecutionAcknowledgementAuthoring,
    upstream_receipt: WiringMergeValidationReceipt,
    issuance: ProspectiveFinalExecutionAcknowledgementIssuance,
) -> None:
    try:
        issuance.require(
            authoring,
            receipt,
            upstream_authoring,
            upstream_receipt,
        )
    except FinalExecutionAcknowledgementIssuanceAuthoringError as exc:
        raise AcknowledgementIssuanceImplementationError(str(exc)) from exc


def _verified_root(
    project_root: Path,
    supplied_authoring: FinalExecutionAcknowledgementIssuanceAuthoring,
    supplied_receipt: AcknowledgementAuthoringMergeValidationReceipt,
    supplied_upstream_authoring: FinalExecutionAcknowledgementAuthoring,
    supplied_upstream_receipt: WiringMergeValidationReceipt,
    *,
    require_closed_boundary: bool,
) -> Path:
    root = _verified_project_root(project_root)
    try:
        _verify_implementation_freeze(root)
        (
            frozen_authoring,
            frozen_receipt,
            frozen_upstream_authoring,
            frozen_upstream_receipt,
        ) = _verify_static_authoring_chain(root)
        if require_closed_boundary:
            _require_production_boundary_closed(root)
        supplied_receipt.require()
        supplied_authoring.require(supplied_receipt)
        supplied_upstream_receipt.require()
        supplied_upstream_authoring.require(supplied_upstream_receipt)
    except AcknowledgementIssuanceImplementationError:
        raise
    except (
        FinalExecutionAcknowledgementAuthoringError,
        FinalExecutionAcknowledgementIssuanceAuthoringError,
        OSError,
        UnicodeError,
        ValueError,
    ) as exc:
        raise AcknowledgementIssuanceImplementationError(str(exc)) from exc
    comparisons = (
        (
            supplied_receipt.canonical_json(),
            frozen_receipt.canonical_json(),
            "supplied authoring receipt differs from frozen receipt",
        ),
        (
            supplied_authoring.canonical_json(supplied_receipt),
            frozen_authoring.canonical_json(frozen_receipt),
            "supplied issuance authoring differs from frozen authoring",
        ),
        (
            supplied_upstream_receipt.canonical_json(),
            frozen_upstream_receipt.canonical_json(),
            "supplied upstream receipt differs from frozen receipt",
        ),
        (
            supplied_upstream_authoring.canonical_json(supplied_upstream_receipt),
            frozen_upstream_authoring.canonical_json(frozen_upstream_receipt),
            "supplied upstream authoring differs from frozen authoring",
        ),
    )
    for supplied, frozen, message in comparisons:
        if supplied != frozen:
            raise AcknowledgementIssuanceImplementationError(message)
    return root


def _verified_project_root(project_root: Path) -> Path:
    expanded = project_root.expanduser()
    if expanded.is_symlink():
        raise AcknowledgementIssuanceImplementationError(
            "project root is symbolic"
        )
    root = expanded.resolve()
    if not root.is_dir():
        raise AcknowledgementIssuanceImplementationError(
            "project root is absent or non-directory"
        )
    return root


def _verify_implementation_freeze(
    root: Path,
) -> tuple[
    AcknowledgementIssuanceAuthoringMergeValidationReceipt,
    AcknowledgementIssuanceImplementationRecord,
]:
    package = root / IMPLEMENTATION_PACKAGE_RELATIVE
    if not package.is_dir() or package.is_symlink():
        raise AcknowledgementIssuanceImplementationError(
            "implementation package is absent or invalid"
        )
    if {path.name for path in package.iterdir()} != _EXPECTED_PACKAGE_FILES:
        raise AcknowledgementIssuanceImplementationError(
            "implementation package file set differs"
        )
    _verify_registry(root / IMPLEMENTATION_REGISTRY_RELATIVE, package)
    source_registry = _verify_registry(
        root / IMPLEMENTATION_SOURCE_REGISTRY_RELATIVE,
        root,
    )
    if frozenset(source_registry) != _EXPECTED_SOURCE_PATHS:
        raise AcknowledgementIssuanceImplementationError(
            "implementation source registry path set differs"
        )
    receipt = load_acknowledgement_issuance_authoring_merge_validation_receipt(
        root / AUTHORING_MERGE_RECEIPT_RELATIVE
    )
    record = load_acknowledgement_issuance_implementation_record(
        root / IMPLEMENTATION_RECORD_RELATIVE,
        receipt,
    )
    return receipt, record


def _verify_static_authoring_chain(
    root: Path,
) -> tuple[
    FinalExecutionAcknowledgementIssuanceAuthoring,
    AcknowledgementAuthoringMergeValidationReceipt,
    FinalExecutionAcknowledgementAuthoring,
    WiringMergeValidationReceipt,
]:
    _verify_registry(root / AUTHORING_REGISTRY_RELATIVE, root / AUTHORING_PACKAGE_RELATIVE)
    _verify_registry(root / AUTHORING_SOURCE_REGISTRY_RELATIVE, root)
    receipt = load_acknowledgement_authoring_merge_validation_receipt(
        root / ISSUANCE_AUTHORING_MERGE_RECEIPT_RELATIVE
    )
    authoring = load_final_execution_acknowledgement_issuance_authoring(
        root / AUTHORING_RECORD_RELATIVE,
        receipt,
    )
    upstream_receipt = load_wiring_merge_validation_receipt(
        root / UPSTREAM_WIRING_RECEIPT_RELATIVE
    )
    upstream_authoring = load_final_execution_acknowledgement_authoring(
        root / UPSTREAM_AUTHORING_RECORD_RELATIVE,
        upstream_receipt,
    )
    expected: dict[Path, str] = {
        AUTHORING_RECORD_RELATIVE: AUTHORING_FILE_SHA256,
        AUTHORING_REGISTRY_RELATIVE: AUTHORING_PACKAGE_REGISTRY_SHA256,
        AUTHORING_SOURCE_REGISTRY_RELATIVE: AUTHORING_SOURCE_REGISTRY_SHA256,
        AUTHORING_MODULE_RELATIVE: AUTHORING_MODULE_SHA256,
        AUTHORING_VERIFIER_RELATIVE: AUTHORING_VERIFIER_SHA256,
        AUTHORING_TEST_RELATIVE: AUTHORING_TEST_SHA256,
        AUTHORING_ADR_RU_RELATIVE: AUTHORING_ADR_RU_SHA256,
        AUTHORING_ADR_EN_RELATIVE: AUTHORING_ADR_EN_SHA256,
    }
    for relative, digest in expected.items():
        path = root / relative
        if not path.is_file() or path.is_symlink():
            raise AcknowledgementIssuanceImplementationError(
                f"authoring source is absent or invalid: {relative}"
            )
        if sha256_bytes(path.read_bytes()) != digest:
            raise AcknowledgementIssuanceImplementationError(
                f"authoring source identity differs: {relative}"
            )
    if authoring.authoring_sha256 != AUTHORING_SHA256:
        raise AcknowledgementIssuanceImplementationError(
            "authoring semantic identity differs"
        )
    return authoring, receipt, upstream_authoring, upstream_receipt


def _verify_runtime_ast_boundary(root: Path) -> None:
    paths = (
        root / IMPLEMENTATION_MODULE_RELATIVE,
        root / IMPLEMENTATION_VERIFIER_RELATIVE,
    )
    for path in paths:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="strict"))
        except (OSError, UnicodeError, SyntaxError) as exc:
            raise AcknowledgementIssuanceImplementationError(
                f"implementation Python source is invalid: {path}"
            ) from exc
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots = {alias.name.split(".", 1)[0] for alias in node.names}
                if roots & _FORBIDDEN_IMPORT_ROOTS:
                    raise AcknowledgementIssuanceImplementationError(
                        f"forbidden implementation import: {path}"
                    )
            if (
                isinstance(node, ast.ImportFrom)
                and node.module
                and node.module.split(".", 1)[0] in _FORBIDDEN_IMPORT_ROOTS
            ):
                raise AcknowledgementIssuanceImplementationError(
                    f"forbidden implementation import: {path}"
                )
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    call_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    call_name = node.func.attr
                else:
                    call_name = ""
                if call_name in _FORBIDDEN_RUNTIME_CALLS:
                    raise AcknowledgementIssuanceImplementationError(
                        f"forbidden runtime call in implementation source: {path}"
                    )


def _require_repository_production_callsite_absent(root: Path) -> None:
    target_name = "persist_final_execution_acknowledgement"
    for path in sorted((root / "src").rglob("*.py")):
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
                raise AcknowledgementIssuanceImplementationError(
                    f"production acknowledgement writer callsite exists: {path}"
                )


def _require_production_boundary_closed(root: Path) -> None:
    output_root = _target(
        root,
        Path("results/stage-3/qwake-lc4-runtime-validation-v1-attempt-001"),
    )
    paths = {
        "authorized output root": output_root,
        "final execution acknowledgement": _target(root, ACKNOWLEDGEMENT_RELATIVE),
        "legacy execution lease": _target(root, LEGACY_EXECUTION_LEASE_RELATIVE),
        "persistent execution lease v2": _target(root, EXECUTION_LEASE_V2_RELATIVE),
        "durable host outcome": _target(root, DURABLE_HOST_OUTCOME_RELATIVE),
    }
    for label, path in paths.items():
        _require_absent(path, label)
    _require_no_stale_temporaries(paths["final execution acknowledgement"])


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8", errors="strict"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AcknowledgementIssuanceImplementationError(
            f"frozen JSON is invalid: {path}"
        ) from exc
    if not isinstance(value, dict):
        raise AcknowledgementIssuanceImplementationError(
            f"frozen JSON root differs: {path}"
        )
    return cast(dict[str, Any], value)


def load_acknowledgement_issuance_authoring_merge_validation_receipt(
    path: Path,
) -> AcknowledgementIssuanceAuthoringMergeValidationReceipt:
    receipt = AcknowledgementIssuanceAuthoringMergeValidationReceipt.from_mapping(
        _load_json(path)
    )
    receipt.require()
    return receipt


def load_acknowledgement_issuance_implementation_record(
    path: Path,
    receipt: AcknowledgementIssuanceAuthoringMergeValidationReceipt,
) -> AcknowledgementIssuanceImplementationRecord:
    record = AcknowledgementIssuanceImplementationRecord.from_mapping(
        _load_json(path)
    )
    record.require(receipt)
    return record


def _verify_registry(path: Path, base: Path) -> dict[str, str]:
    if not path.is_file() or path.is_symlink():
        raise AcknowledgementIssuanceImplementationError(
            f"frozen registry is absent or invalid: {path}"
        )
    entries: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="strict").splitlines():
        try:
            digest, relative = line.split("  ", 1)
        except ValueError as exc:
            raise AcknowledgementIssuanceImplementationError(
                f"frozen registry line is invalid: {path}"
            ) from exc
        target = base / relative
        if relative in entries:
            raise AcknowledgementIssuanceImplementationError(
                f"frozen registry path is duplicated: {relative}"
            )
        if not target.is_file() or target.is_symlink():
            raise AcknowledgementIssuanceImplementationError(
                f"frozen registry target is absent or invalid: {target}"
            )
        observed = hashlib.sha256(target.read_bytes()).hexdigest()
        if observed != digest:
            raise AcknowledgementIssuanceImplementationError(
                f"frozen registry target digest differs: {target}"
            )
        entries[relative] = digest
    if not entries:
        raise AcknowledgementIssuanceImplementationError(
            f"frozen registry is empty: {path}"
        )
    return entries


def _target(root: Path, relative: Path) -> Path:
    if relative.is_absolute() or ".." in relative.parts:
        raise AcknowledgementIssuanceImplementationError(
            "persistent target path is not repository-relative"
        )
    target = root.joinpath(relative)
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise AcknowledgementIssuanceImplementationError(
            "persistent target escapes project root"
        ) from exc
    _require_safe_parent_chain(root, target.parent)
    return target


def _require_safe_parent_chain(root: Path, directory: Path) -> None:
    try:
        relative = directory.relative_to(root)
    except ValueError as exc:
        raise AcknowledgementIssuanceImplementationError(
            "persistent target parent escapes project root"
        ) from exc
    current = root
    for part in relative.parts:
        current = current / part
        try:
            metadata = current.lstat()
        except FileNotFoundError as exc:
            raise AcknowledgementIssuanceImplementationError(
                f"persistent target parent is absent: {current}"
            ) from exc
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise AcknowledgementIssuanceImplementationError(
                f"persistent target parent is not a real directory: {current}"
            )


def _require_absent(path: Path, label: str) -> None:
    if _lexists(path):
        raise AcknowledgementIssuanceImplementationError(
            f"{label} already exists: {path}"
        )


def _require_no_stale_temporaries(target: Path) -> None:
    pattern = f".{target.name}.tmp-*"
    stale = sorted(target.parent.glob(pattern))
    if stale:
        raise AcknowledgementIssuanceImplementationError(
            f"stale acknowledgement temporary exists: {stale[0]}"
        )


def _atomic_write_once(
    root: Path,
    target: Path,
    payload: bytes,
) -> PersistentAcknowledgementWriteResult:
    if not payload or not payload.endswith(b"\n"):
        raise AcknowledgementIssuanceImplementationError(
            "acknowledgement JSON payload is empty or non-canonical"
        )
    _require_json_object(payload)
    _target(root, target.relative_to(root))
    _require_absent(target, "atomic acknowledgement target")
    _require_no_stale_temporaries(target)

    temporary = target.parent / (
        f".{target.name}.tmp-{os.getpid()}-{secrets.token_hex(16)}"
    )
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor: int | None = None
    linked = False
    try:
        descriptor = os.open(temporary, flags, 0o600)
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise AcknowledgementIssuanceImplementationError(
                    "acknowledgement write made no progress"
                )
            view = view[written:]
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = None
        try:
            os.link(temporary, target, follow_symlinks=False)
        except FileExistsError as exc:
            raise AcknowledgementIssuanceImplementationError(
                f"atomic acknowledgement target already exists: {target}"
            ) from exc
        linked = True
        _fsync_directory(target.parent)
        result = _verify_exact_file(root, target, payload)
    except OSError as exc:
        raise AcknowledgementIssuanceImplementationError(
            f"acknowledgement atomic write failed: {target}"
        ) from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if _lexists(temporary):
            temporary.unlink()
            _fsync_directory(temporary.parent)
    if not linked:
        raise AcknowledgementIssuanceImplementationError(
            "acknowledgement atomic target was not linked"
        )
    return result


def _verify_exact_file(
    root: Path,
    target: Path,
    expected: bytes,
) -> PersistentAcknowledgementWriteResult:
    _target(root, target.relative_to(root))
    try:
        metadata = target.lstat()
    except FileNotFoundError as exc:
        raise AcknowledgementIssuanceImplementationError(
            f"persistent acknowledgement is absent: {target}"
        ) from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise AcknowledgementIssuanceImplementationError(
            f"persistent acknowledgement is not a regular file: {target}"
        )
    observed = target.read_bytes()
    if observed != expected:
        raise AcknowledgementIssuanceImplementationError(
            f"persistent acknowledgement bytes differ: {target}"
        )
    mode = stat.S_IMODE(metadata.st_mode)
    if mode != 0o600:
        raise AcknowledgementIssuanceImplementationError(
            f"persistent acknowledgement mode differs: {target}"
        )
    result = PersistentAcknowledgementWriteResult(
        relative_path=target.relative_to(root).as_posix(),
        byte_count=len(observed),
        sha256="sha256:" + hashlib.sha256(observed).hexdigest(),
        mode=mode,
    )
    result.require()
    return result


def _require_json_object(payload: bytes) -> None:
    try:
        value = json.loads(payload.decode("utf-8", errors="strict"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise AcknowledgementIssuanceImplementationError(
            "acknowledgement payload is not valid UTF-8 JSON"
        ) from exc
    if not isinstance(value, dict):
        raise AcknowledgementIssuanceImplementationError(
            "acknowledgement payload JSON root differs"
        )


def _fsync_directory(directory: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    flags |= getattr(os, "O_CLOEXEC", 0)
    descriptor = os.open(directory, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _lexists(path: Path) -> bool:
    return os.path.lexists(path)


def _build_source(
    receipt: AcknowledgementIssuanceAuthoringMergeValidationReceipt,
) -> AcknowledgementIssuanceImplementationSource:
    return AcknowledgementIssuanceImplementationSource(
        implementation_base_commit=IMPLEMENTATION_BASE_COMMIT,
        authoring_pr_number=AUTHORING_PR_NUMBER,
        authoring_head_commit=AUTHORING_HEAD_COMMIT,
        authoring_parent_commit=AUTHORING_PARENT_COMMIT,
        authoring_merge_commit=AUTHORING_MERGE_COMMIT,
        authoring_merged_at_utc=AUTHORING_MERGED_AT_UTC,
        authoring_merge_receipt_sha256=receipt.receipt_sha256,
        authoring_id=(
            "stage3b-qwake-lc4-e-final-execution-"
            "acknowledgement-issuance-authoring-v1"
        ),
        authoring_sha256=AUTHORING_SHA256,
        authoring_file_sha256=AUTHORING_FILE_SHA256,
        authoring_package_registry_sha256=AUTHORING_PACKAGE_REGISTRY_SHA256,
        authoring_source_registry_sha256=AUTHORING_SOURCE_REGISTRY_SHA256,
        authoring_module_sha256=AUTHORING_MODULE_SHA256,
        authoring_verifier_sha256=AUTHORING_VERIFIER_SHA256,
        authoring_test_sha256=AUTHORING_TEST_SHA256,
        authoring_adr_ru_sha256=AUTHORING_ADR_RU_SHA256,
        authoring_adr_en_sha256=AUTHORING_ADR_EN_SHA256,
        acknowledgement_relative=ACKNOWLEDGEMENT_RELATIVE.as_posix(),
        legacy_execution_lease_relative=LEGACY_EXECUTION_LEASE_RELATIVE.as_posix(),
        execution_lease_v2_relative=EXECUTION_LEASE_V2_RELATIVE.as_posix(),
        durable_host_outcome_relative=DURABLE_HOST_OUTCOME_RELATIVE.as_posix(),
    )


def _build_contract() -> AcknowledgementIssuanceImplementationContract:
    return AcknowledgementIssuanceImplementationContract(
        complete_authoring_identity_verified=True,
        canonical_issuance_envelope_required=True,
        exact_acknowledgement_path_enforced=True,
        production_boundary_absence_required=True,
        target_parent_must_preexist=True,
        symbolic_parent_chain_forbidden=True,
        stale_temporary_collision_forbidden=True,
        exclusive_atomic_no_overwrite_implemented=True,
        file_mode="0600",
        file_fsync_implemented=True,
        parent_directory_fsync_implemented=True,
        temporary_cleanup_implemented=True,
        exact_persisted_bytes_reverification_implemented=True,
        regular_file_required=True,
        retry_forbidden=True,
        production_materialization_separate=True,
        repository_production_callsite_forbidden=True,
        image_inspection_forbidden=True,
        command_materialization_forbidden=True,
        subprocess_forbidden=True,
        docker_forbidden=True,
        local_compute_forbidden=True,
    )


def _build_gates() -> AcknowledgementIssuanceImplementationGates:
    return AcknowledgementIssuanceImplementationGates(
        acknowledgement_issuance_authoring_post_merge_verified=True,
        acknowledgement_issuance_contract_authored=True,
        acknowledgement_issuance_implemented=True,
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


def build_frozen_acknowledgement_issuance_implementation_record(
    receipt: AcknowledgementIssuanceAuthoringMergeValidationReceipt,
) -> AcknowledgementIssuanceImplementationRecord:
    """Build the canonical frozen writer-implementation record."""

    receipt.require()
    provisional = AcknowledgementIssuanceImplementationRecord(
        schema_version=1,
        implementation_id=(
            FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUANCE_IMPLEMENTATION_ID
        ),
        status=FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUANCE_IMPLEMENTATION_STATUS,
        recorded_at_utc="2026-07-30T17:30:00Z",
        source=_build_source(receipt),
        contract=_build_contract(),
        gates=_build_gates(),
        next_slice=(
            "QW-LC4-E-final-execution-acknowledgement-issuance-"
            "implementation-commit"
        ),
        post_merge_next_slice=(
            "QW-LC4-E-final-execution-acknowledgement-issuance-materialization"
        ),
        implementation_sha256="sha256:" + "0" * 64,
    )
    result = replace(
        provisional,
        implementation_sha256=sha256_object(provisional.semantic_payload()),
    )
    result.require(receipt)
    return result


def build_acknowledgement_issuance_authoring_merge_validation_receipt(
) -> AcknowledgementIssuanceAuthoringMergeValidationReceipt:
    """Build the independently verified PR #148 merge receipt."""

    provisional = AcknowledgementIssuanceAuthoringMergeValidationReceipt(
        receipt_id=(
            "stage3b-qwake-lc4-e-final-execution-acknowledgement-"
            "issuance-authoring-post-merge-validation-v1"
        ),
        pr_number=AUTHORING_PR_NUMBER,
        head_commit=AUTHORING_HEAD_COMMIT,
        base_commit=AUTHORING_PARENT_COMMIT,
        merge_commit=AUTHORING_MERGE_COMMIT,
        merged_at_utc=AUTHORING_MERGED_AT_UTC,
        commit_count=1,
        file_count=18,
        focused_tests_passed=61,
        targeted_tests_passed=262,
        full_tests_passed=1309,
        full_test_warnings=14,
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
