"""Effect-free authoring contract for final QW-LC4-E execution acknowledgement.

This module freezes the exact post-merge evidence chain required before a
future operator may issue a final one-shot execution acknowledgement.  The
module only builds and verifies immutable in-memory records.  Importing or
verifying it never writes an acknowledgement, materializes a lease, inspects
an image, materializes a command, spawns a process, invokes Docker, consumes
an authorization, or executes local compute.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final, cast

FINAL_EXECUTION_ACKNOWLEDGEMENT_AUTHORING_ID: Final = (
    "stage3b-qwake-lc4-e-final-execution-acknowledgement-authoring-v1"
)
FINAL_EXECUTION_ACKNOWLEDGEMENT_AUTHORING_STATUS: Final = (
    "final_execution_acknowledgement_authored_not_issued_execution_closed"
)
FINAL_EXECUTION_ACKNOWLEDGEMENT_ID: Final = (
    "stage3b-qwake-lc4-e-final-execution-acknowledgement-v1"
)
FINAL_EXECUTION_ACKNOWLEDGEMENT_STATUS: Final = (
    "prospective_final_execution_acknowledgement_not_materialized"
)
FINAL_EXECUTION_OPERATOR_ACKNOWLEDGEMENT: Final = (
    "ACKNOWLEDGE_QWAKE_LC4_FINAL_ONE_SHOT_EXECUTION"
)

AUTHORING_BASE_COMMIT: Final = "2957d8f6975c88e7bdb23243e3915c7f51d4ba47"
WIRING_PR_NUMBER: Final = 146
WIRING_HEAD_COMMIT: Final = "1d4096a8086c9f9c32e1d14515ef3b702d2237ab"
WIRING_PARENT_COMMIT: Final = "0303a1514e2875a057ef1b20293a01b36a9c6b2b"
WIRING_MERGE_COMMIT: Final = AUTHORING_BASE_COMMIT
WIRING_MERGED_AT_UTC: Final = "2026-07-30T14:37:25Z"

PERSISTENT_EVIDENCE_CHAIN_V2_ID: Final = (
    "stage3b-qwake-lc4-e-persistent-evidence-chain-v2-authoring-v1"
)
PERSISTENT_EVIDENCE_CHAIN_V2_SHA256: Final = (
    "sha256:c0a6195080cec64e6104a90076366cc2bfa10a723b45a7389cd77fa1b3b11bd1"
)
PERSISTENT_EVIDENCE_CHAIN_V2_FILE_SHA256: Final = (
    "sha256:aaacdf8d105b6ce186a84df82b8d5298f3601339cdfaedd70746632d52026dc4"
)
PERSISTENT_EVIDENCE_CHAIN_V2_IMPLEMENTATION_ID: Final = (
    "stage3b-qwake-lc4-e-persistent-evidence-chain-v2-implementation-v1"
)
PERSISTENT_EVIDENCE_CHAIN_V2_IMPLEMENTATION_SHA256: Final = (
    "sha256:3671f7b12b570e7caace38dec0e023691bc1051b3cbf8e72ddfda59058369362"
)
PERSISTENT_EVIDENCE_CHAIN_V2_IMPLEMENTATION_FILE_SHA256: Final = (
    "sha256:fdbad25b58c995ec7b1db7f6d292e3185b93352b4234cee9f6f52a05229c8473"
)
LEASE_BOUND_HOST_INVOKER_WIRING_ID: Final = (
    "stage3b-qwake-lc4-e-lease-bound-host-invoker-wiring-v1"
)
LEASE_BOUND_HOST_INVOKER_WIRING_SHA256: Final = (
    "sha256:a064b518b960159d0fe7d9178962ecab5d2c1660deddffb3155c76db7d937655"
)
LEASE_BOUND_HOST_INVOKER_WIRING_FILE_SHA256: Final = (
    "sha256:60199510764aa4827bfb2deac69675b7d5d79e7209fa8f0aa53ba8d79a5c4ff3"
)

INVOCATION_AUTHORIZATION_ID: Final = (
    "stage3b-qwake-lc4-e-one-shot-engineering-invocation-authorization-v1"
)
INVOCATION_AUTHORIZATION_SHA256: Final = (
    "sha256:0a60dacc1bfd5073cf52d76f2ec33ae54f00899aad9877d44607199659fda75a"
)
EXECUTION_AUTHORIZATION_ID: Final = (
    "stage3b-qwake-lc4-e-one-shot-engineering-invocation-"
    "execution-authorization-v1"
)
EXECUTION_AUTHORIZATION_SHA256: Final = (
    "sha256:ff136538faee0d7952dc444e521d7ec760c7d54cd38406cb9b19ff1e00d9437b"
)
PREEXECUTION_VERIFICATION_ID: Final = (
    "stage3b-qwake-lc4-e-one-shot-engineering-invocation-"
    "preexecution-verification-v1"
)
PREEXECUTION_VERIFICATION_SHA256: Final = (
    "sha256:833371b427a5c8a6e602d675711b85b2edc68441b9e5be191321a2911bce6128"
)
RUNTIME_OPERATION_ID: Final = (
    "stage3b-qwake-lc4-e-one-shot-engineering-invocation-runtime-operation-v1"
)
RUNTIME_OPERATION_SHA256: Final = (
    "sha256:0332428014f7f8385c789ba7e7c55d6c2ec03b020e3f83df9ac9714483bb6bf8"
)
IDENTITY_REPAIR_ID: Final = (
    "stage3b-qwake-lc4-e-one-shot-engineering-invocation-"
    "runtime-operation-identity-repair-v1"
)
IDENTITY_REPAIR_SHA256: Final = (
    "sha256:ff6d22e98257bb55774abf8ad2418a60c759981049994720ae814e9ff6ccc4c6"
)

IMAGE_REPO_DIGEST: Final = (
    "torch2pc-layerwise-thesis@sha256:"
    "7da92b8f77f6dc37d42db832c5613ef6149dc488adc5b66465faa33e48ca021d"
)
TORCH2PC_COMMIT: Final = "b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4"
AUTHORIZED_OUTPUT_ROOT: Final = (
    "results/stage-3/qwake-lc4-runtime-validation-v1-attempt-001"
)
EXECUTION_LEASE_V2_RELATIVE: Final = Path(
    AUTHORIZED_OUTPUT_ROOT + ".execution-lease-v2.json"
)
DURABLE_HOST_OUTCOME_RELATIVE: Final = Path(
    AUTHORIZED_OUTPUT_ROOT + ".host-outcome.json"
)
INVOCATION_COUNT: Final = 1

PACKAGE_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-final-execution-acknowledgement-authoring-v1"
)
AUTHORING_RECORD_RELATIVE: Final = PACKAGE_RELATIVE / "authoring.json"
WIRING_MERGE_RECEIPT_RELATIVE: Final = (
    PACKAGE_RELATIVE / "wiring-merge-validation.json"
)
REGISTRY_RELATIVE: Final = PACKAGE_RELATIVE / "SHA256SUMS"
SOURCE_REGISTRY_RELATIVE: Final = PACKAGE_RELATIVE / "source-SHA256SUMS"

CHAIN_RECORD_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-persistent-evidence-chain-v2-authoring-v1/chain.json"
)
IMPLEMENTATION_RECORD_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-persistent-evidence-chain-v2-implementation-v1/"
    "implementation.json"
)
WIRING_RECORD_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-lease-bound-host-invoker-wiring-v1/wiring.json"
)
WIRING_PACKAGE_REGISTRY_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-lease-bound-host-invoker-wiring-v1/SHA256SUMS"
)
WIRING_SOURCE_REGISTRY_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-lease-bound-host-invoker-wiring-v1/source-SHA256SUMS"
)
WIRING_MODULE_RELATIVE: Final = Path(
    "src/torch2pc_thesis/stage3b_qwake_lc4_lease_bound_host_invoker_wiring.py"
)
WIRING_VERIFIER_RELATIVE: Final = Path(
    "scripts/verify_stage3b_qwake_lc4_lease_bound_host_invoker_wiring.py"
)
WIRING_TEST_RELATIVE: Final = Path(
    "tests/unit/test_stage3b_qwake_lc4_lease_bound_host_invoker_wiring.py"
)
WIRING_ADR_RU_RELATIVE: Final = Path(
    "docs/decisions/"
    "ADR-085-stage3b-qwake-lc4-e-lease-bound-host-invoker-wiring.md"
)
WIRING_ADR_EN_RELATIVE: Final = Path(
    "docs/decisions/"
    "ADR-085-stage3b-qwake-lc4-e-lease-bound-host-invoker-wiring_EN.md"
)
MODULE_RELATIVE: Final = Path(
    "src/torch2pc_thesis/"
    "stage3b_qwake_lc4_final_execution_acknowledgement_authoring.py"
)
VERIFIER_RELATIVE: Final = Path(
    "scripts/verify_stage3b_qwake_lc4_final_execution_acknowledgement_authoring.py"
)
TEST_RELATIVE: Final = Path(
    "tests/unit/"
    "test_stage3b_qwake_lc4_final_execution_acknowledgement_authoring.py"
)
ADR_RU_RELATIVE: Final = Path(
    "docs/decisions/"
    "ADR-086-stage3b-qwake-lc4-e-final-execution-acknowledgement-authoring.md"
)
ADR_EN_RELATIVE: Final = Path(
    "docs/decisions/"
    "ADR-086-stage3b-qwake-lc4-e-final-execution-acknowledgement-authoring_EN.md"
)

_EXPECTED_PACKAGE_FILES: Final = frozenset(
    {
        "SHA256SUMS",
        "authoring.json",
        "source-SHA256SUMS",
        "wiring-merge-validation.json",
    }
)
_EXPECTED_SOURCE_PATHS: Final = frozenset(
    {
        CHAIN_RECORD_RELATIVE.as_posix(),
        IMPLEMENTATION_RECORD_RELATIVE.as_posix(),
        WIRING_RECORD_RELATIVE.as_posix(),
        WIRING_PACKAGE_REGISTRY_RELATIVE.as_posix(),
        WIRING_SOURCE_REGISTRY_RELATIVE.as_posix(),
        WIRING_MODULE_RELATIVE.as_posix(),
        WIRING_VERIFIER_RELATIVE.as_posix(),
        WIRING_TEST_RELATIVE.as_posix(),
        WIRING_ADR_RU_RELATIVE.as_posix(),
        WIRING_ADR_EN_RELATIVE.as_posix(),
        MODULE_RELATIVE.as_posix(),
        VERIFIER_RELATIVE.as_posix(),
        TEST_RELATIVE.as_posix(),
        ADR_RU_RELATIVE.as_posix(),
        ADR_EN_RELATIVE.as_posix(),
    }
)
_SHA256_PATTERN: Final = re.compile(r"^sha256:[0-9a-f]{64}$")
_COMMIT_PATTERN: Final = re.compile(r"^[0-9a-f]{40}$")
_OPERATOR_IDENTITY_PATTERN: Final = re.compile(r"^[^\r\n]{1,256}$")
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
    "FINAL_EXECUTION_ACKNOWLEDGEMENT_AUTHORING_ID",
    "FINAL_EXECUTION_ACKNOWLEDGEMENT_ID",
    "FINAL_EXECUTION_OPERATOR_ACKNOWLEDGEMENT",
    "FinalExecutionAcknowledgementAuthoring",
    "FinalExecutionAcknowledgementAuthoringError",
    "FinalExecutionAcknowledgementContract",
    "FinalExecutionAcknowledgementGates",
    "FinalExecutionAcknowledgementSource",
    "ProspectiveFinalExecutionAcknowledgement",
    "WiringMergeValidationReceipt",
    "build_final_execution_acknowledgement",
    "build_frozen_authoring_record",
    "build_wiring_merge_validation_receipt",
    "canonical_json",
    "load_final_execution_acknowledgement_authoring",
    "load_wiring_merge_validation_receipt",
    "sha256_bytes",
    "sha256_object",
    "verify_final_execution_acknowledgement_authoring",
]


class FinalExecutionAcknowledgementAuthoringError(RuntimeError):
    """Raised when the acknowledgement-authoring contract fails closed."""


def canonical_json(value: object) -> str:
    """Return canonical UTF-8 JSON with one terminal newline."""

    if hasattr(value, "__dataclass_fields__"):
        value = asdict(cast(Any, value))
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ) + "\n"


def sha256_object(value: object) -> str:
    """Hash a JSON-compatible object without terminal formatting ambiguity."""

    if hasattr(value, "__dataclass_fields__"):
        value = asdict(cast(Any, value))
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def sha256_bytes(value: bytes) -> str:
    """Return a prefixed SHA-256 digest."""

    return "sha256:" + hashlib.sha256(value).hexdigest()


def _require_sha256(value: str, field_name: str) -> None:
    if not _SHA256_PATTERN.fullmatch(value):
        raise FinalExecutionAcknowledgementAuthoringError(
            f"{field_name} is not a canonical SHA-256 identity"
        )


def _require_commit(value: str, field_name: str) -> None:
    if not _COMMIT_PATTERN.fullmatch(value):
        raise FinalExecutionAcknowledgementAuthoringError(
            f"{field_name} is not a commit identity"
        )


def _require_utc(value: str, field_name: str) -> datetime:
    if not value.endswith("Z"):
        raise FinalExecutionAcknowledgementAuthoringError(
            f"{field_name} is not a UTC timestamp"
        )
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise FinalExecutionAcknowledgementAuthoringError(
            f"{field_name} is not an ISO-8601 timestamp"
        ) from exc
    if parsed.tzinfo != UTC:
        raise FinalExecutionAcknowledgementAuthoringError(
            f"{field_name} is not normalized to UTC"
        )
    return parsed


@dataclass(frozen=True)
class WiringMergeValidationReceipt:
    """Exact post-merge receipt for the lease-bound wiring PR."""

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
    runtime_boundary_closed: bool
    receipt_sha256: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> WiringMergeValidationReceipt:
        return cls(**cast(dict[str, Any], dict(value)))

    def semantic_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload.pop("receipt_sha256")
        return cast(dict[str, object], payload)

    def require(self) -> None:
        expected: dict[str, object] = {
            "receipt_id": (
                "stage3b-qwake-lc4-e-lease-bound-host-invoker-wiring-"
                "post-merge-validation-v1"
            ),
            "pr_number": WIRING_PR_NUMBER,
            "head_commit": WIRING_HEAD_COMMIT,
            "base_commit": WIRING_PARENT_COMMIT,
            "merge_commit": WIRING_MERGE_COMMIT,
            "merged_at_utc": WIRING_MERGED_AT_UTC,
            "commit_count": 1,
            "file_count": 18,
            "focused_tests_passed": 39,
            "targeted_tests_passed": 240,
            "full_tests_passed": 1287,
            "full_test_warnings": 14,
            "required_ci_checks_passed": True,
            "runtime_boundary_closed": True,
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise FinalExecutionAcknowledgementAuthoringError(
                    f"wiring merge receipt differs: {field_name}"
                )
        _require_commit(self.head_commit, "head_commit")
        _require_commit(self.base_commit, "base_commit")
        _require_commit(self.merge_commit, "merge_commit")
        _require_utc(self.merged_at_utc, "merged_at_utc")
        _require_sha256(self.receipt_sha256, "receipt_sha256")
        if self.receipt_sha256 != sha256_object(self.semantic_payload()):
            raise FinalExecutionAcknowledgementAuthoringError(
                "wiring merge receipt semantic SHA-256 differs"
            )

    def canonical_json(self) -> str:
        self.require()
        return canonical_json(self)


@dataclass(frozen=True)
class FinalExecutionAcknowledgementSource:
    """Complete immutable chain bound by a future acknowledgement."""

    authoring_base_commit: str
    wiring_pr_number: int
    wiring_head_commit: str
    wiring_parent_commit: str
    wiring_merge_commit: str
    wiring_merged_at_utc: str
    wiring_merge_receipt_sha256: str
    persistent_evidence_chain_v2_id: str
    persistent_evidence_chain_v2_sha256: str
    persistent_evidence_chain_v2_file_sha256: str
    persistent_evidence_chain_v2_implementation_id: str
    persistent_evidence_chain_v2_implementation_sha256: str
    persistent_evidence_chain_v2_implementation_file_sha256: str
    lease_bound_host_invoker_wiring_id: str
    lease_bound_host_invoker_wiring_sha256: str
    lease_bound_host_invoker_wiring_file_sha256: str
    invocation_authorization_id: str
    invocation_authorization_sha256: str
    execution_authorization_id: str
    execution_authorization_sha256: str
    preexecution_verification_id: str
    preexecution_verification_sha256: str
    runtime_operation_id: str
    runtime_operation_sha256: str
    identity_repair_id: str
    identity_repair_sha256: str
    image_repo_digest: str
    torch2pc_commit: str
    output_root: str
    execution_lease_v2_relative: str
    durable_host_outcome_relative: str
    invocation_count: int

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> FinalExecutionAcknowledgementSource:
        return cls(**cast(dict[str, Any], dict(value)))

    def require(self, receipt: WiringMergeValidationReceipt) -> None:
        expected: dict[str, object] = {
            "authoring_base_commit": AUTHORING_BASE_COMMIT,
            "wiring_pr_number": WIRING_PR_NUMBER,
            "wiring_head_commit": WIRING_HEAD_COMMIT,
            "wiring_parent_commit": WIRING_PARENT_COMMIT,
            "wiring_merge_commit": WIRING_MERGE_COMMIT,
            "wiring_merged_at_utc": WIRING_MERGED_AT_UTC,
            "wiring_merge_receipt_sha256": receipt.receipt_sha256,
            "persistent_evidence_chain_v2_id": PERSISTENT_EVIDENCE_CHAIN_V2_ID,
            "persistent_evidence_chain_v2_sha256": PERSISTENT_EVIDENCE_CHAIN_V2_SHA256,
            "persistent_evidence_chain_v2_file_sha256": (
                PERSISTENT_EVIDENCE_CHAIN_V2_FILE_SHA256
            ),
            "persistent_evidence_chain_v2_implementation_id": (
                PERSISTENT_EVIDENCE_CHAIN_V2_IMPLEMENTATION_ID
            ),
            "persistent_evidence_chain_v2_implementation_sha256": (
                PERSISTENT_EVIDENCE_CHAIN_V2_IMPLEMENTATION_SHA256
            ),
            "persistent_evidence_chain_v2_implementation_file_sha256": (
                PERSISTENT_EVIDENCE_CHAIN_V2_IMPLEMENTATION_FILE_SHA256
            ),
            "lease_bound_host_invoker_wiring_id": LEASE_BOUND_HOST_INVOKER_WIRING_ID,
            "lease_bound_host_invoker_wiring_sha256": (
                LEASE_BOUND_HOST_INVOKER_WIRING_SHA256
            ),
            "lease_bound_host_invoker_wiring_file_sha256": (
                LEASE_BOUND_HOST_INVOKER_WIRING_FILE_SHA256
            ),
            "invocation_authorization_id": INVOCATION_AUTHORIZATION_ID,
            "invocation_authorization_sha256": INVOCATION_AUTHORIZATION_SHA256,
            "execution_authorization_id": EXECUTION_AUTHORIZATION_ID,
            "execution_authorization_sha256": EXECUTION_AUTHORIZATION_SHA256,
            "preexecution_verification_id": PREEXECUTION_VERIFICATION_ID,
            "preexecution_verification_sha256": PREEXECUTION_VERIFICATION_SHA256,
            "runtime_operation_id": RUNTIME_OPERATION_ID,
            "runtime_operation_sha256": RUNTIME_OPERATION_SHA256,
            "identity_repair_id": IDENTITY_REPAIR_ID,
            "identity_repair_sha256": IDENTITY_REPAIR_SHA256,
            "image_repo_digest": IMAGE_REPO_DIGEST,
            "torch2pc_commit": TORCH2PC_COMMIT,
            "output_root": AUTHORIZED_OUTPUT_ROOT,
            "execution_lease_v2_relative": EXECUTION_LEASE_V2_RELATIVE.as_posix(),
            "durable_host_outcome_relative": DURABLE_HOST_OUTCOME_RELATIVE.as_posix(),
            "invocation_count": INVOCATION_COUNT,
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise FinalExecutionAcknowledgementAuthoringError(
                    f"acknowledgement source differs: {field_name}"
                )
        for field_name in (
            "authoring_base_commit",
            "wiring_head_commit",
            "wiring_parent_commit",
            "wiring_merge_commit",
            "torch2pc_commit",
        ):
            _require_commit(cast(str, getattr(self, field_name)), field_name)
        for field_name in (
            "wiring_merge_receipt_sha256",
            "persistent_evidence_chain_v2_sha256",
            "persistent_evidence_chain_v2_file_sha256",
            "persistent_evidence_chain_v2_implementation_sha256",
            "persistent_evidence_chain_v2_implementation_file_sha256",
            "lease_bound_host_invoker_wiring_sha256",
            "lease_bound_host_invoker_wiring_file_sha256",
            "invocation_authorization_sha256",
            "execution_authorization_sha256",
            "preexecution_verification_sha256",
            "runtime_operation_sha256",
            "identity_repair_sha256",
        ):
            _require_sha256(cast(str, getattr(self, field_name)), field_name)
        _require_utc(self.wiring_merged_at_utc, "wiring_merged_at_utc")


@dataclass(frozen=True)
class FinalExecutionAcknowledgementContract:
    """Fail-closed requirements for a future explicit acknowledgement."""

    exact_operator_phrase_required: str
    explicit_operator_identity_required: bool
    explicit_utc_timestamp_required: bool
    acknowledgement_after_wiring_merge_required: bool
    complete_identity_chain_required: bool
    exact_image_digest_required: bool
    exact_torch2pc_commit_required: bool
    exact_output_root_required: bool
    exact_lease_and_outcome_paths_required: bool
    invocation_count_required: int
    single_attempt_only: bool
    automatic_retry_forbidden: bool
    automatic_transition_from_authoring_forbidden: bool
    acknowledgement_materialization_separate: bool
    execution_lease_materialization_separate: bool
    acknowledgement_required_before_lease_claim: bool
    lease_required_before_host_invocation: bool
    durable_terminal_outcome_required: bool
    authoring_effects_forbidden: bool

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> FinalExecutionAcknowledgementContract:
        return cls(**cast(dict[str, Any], dict(value)))

    def require(self) -> None:
        expected: dict[str, object] = {
            "exact_operator_phrase_required": FINAL_EXECUTION_OPERATOR_ACKNOWLEDGEMENT,
            "explicit_operator_identity_required": True,
            "explicit_utc_timestamp_required": True,
            "acknowledgement_after_wiring_merge_required": True,
            "complete_identity_chain_required": True,
            "exact_image_digest_required": True,
            "exact_torch2pc_commit_required": True,
            "exact_output_root_required": True,
            "exact_lease_and_outcome_paths_required": True,
            "invocation_count_required": 1,
            "single_attempt_only": True,
            "automatic_retry_forbidden": True,
            "automatic_transition_from_authoring_forbidden": True,
            "acknowledgement_materialization_separate": True,
            "execution_lease_materialization_separate": True,
            "acknowledgement_required_before_lease_claim": True,
            "lease_required_before_host_invocation": True,
            "durable_terminal_outcome_required": True,
            "authoring_effects_forbidden": True,
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise FinalExecutionAcknowledgementAuthoringError(
                    f"acknowledgement contract differs: {field_name}"
                )


@dataclass(frozen=True)
class FinalExecutionAcknowledgementGates:
    """Repository gates after authoring but before issuance."""

    wiring_post_merge_verified: bool
    persistent_evidence_chain_v2_present: bool
    persistent_lease_v2_implementation_present: bool
    durable_outcome_writer_implemented: bool
    lease_bound_host_invoker_enforced: bool
    final_execution_acknowledgement_authored: bool
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
    def from_mapping(cls, value: Mapping[str, object]) -> FinalExecutionAcknowledgementGates:
        return cls(**cast(dict[str, Any], dict(value)))

    def require(self) -> None:
        expected: dict[str, bool] = {
            "wiring_post_merge_verified": True,
            "persistent_evidence_chain_v2_present": True,
            "persistent_lease_v2_implementation_present": True,
            "durable_outcome_writer_implemented": True,
            "lease_bound_host_invoker_enforced": True,
            "final_execution_acknowledgement_authored": True,
            "final_execution_acknowledgement_issued": False,
            "final_execution_acknowledged": False,
            "one_shot_engineering_invocation_permitted": False,
            "execution_lease_materialized": False,
            "durable_host_outcome_present": False,
            "authorization_consumed": False,
            "runtime_execution_started": False,
            "runtime_execution_performed": False,
            "image_inspection_performed": False,
            "invocation_command_materialized": False,
            "docker_run_performed": False,
            "local_compute_execution_open": False,
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) is not expected_value:
                raise FinalExecutionAcknowledgementAuthoringError(
                    f"acknowledgement authoring gate differs: {field_name}"
                )


@dataclass(frozen=True)
class FinalExecutionAcknowledgementAuthoring:
    """Frozen authoring record; it is not an issued acknowledgement."""

    schema_version: int
    authoring_id: str
    status: str
    recorded_at_utc: str
    source: FinalExecutionAcknowledgementSource
    contract: FinalExecutionAcknowledgementContract
    gates: FinalExecutionAcknowledgementGates
    next_slice: str
    post_merge_next_slice: str
    authoring_sha256: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> FinalExecutionAcknowledgementAuthoring:
        payload = dict(value)
        payload["source"] = FinalExecutionAcknowledgementSource.from_mapping(
            cast(Mapping[str, object], payload["source"])
        )
        payload["contract"] = FinalExecutionAcknowledgementContract.from_mapping(
            cast(Mapping[str, object], payload["contract"])
        )
        payload["gates"] = FinalExecutionAcknowledgementGates.from_mapping(
            cast(Mapping[str, object], payload["gates"])
        )
        return cls(**cast(dict[str, Any], payload))

    def semantic_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload.pop("authoring_sha256")
        return cast(dict[str, object], payload)

    def require(self, receipt: WiringMergeValidationReceipt) -> None:
        if self.schema_version != 1:
            raise FinalExecutionAcknowledgementAuthoringError(
                "acknowledgement authoring schema differs"
            )
        if self.authoring_id != FINAL_EXECUTION_ACKNOWLEDGEMENT_AUTHORING_ID:
            raise FinalExecutionAcknowledgementAuthoringError(
                "acknowledgement authoring ID differs"
            )
        if self.status != FINAL_EXECUTION_ACKNOWLEDGEMENT_AUTHORING_STATUS:
            raise FinalExecutionAcknowledgementAuthoringError(
                "acknowledgement authoring status differs"
            )
        _require_utc(self.recorded_at_utc, "recorded_at_utc")
        if self.next_slice != "QW-LC4-E-final-execution-acknowledgement-authoring-commit":
            raise FinalExecutionAcknowledgementAuthoringError("next slice differs")
        if self.post_merge_next_slice != (
            "QW-LC4-E-final-execution-acknowledgement-issuance"
        ):
            raise FinalExecutionAcknowledgementAuthoringError(
                "post-merge next slice differs"
            )
        self.source.require(receipt)
        self.contract.require()
        self.gates.require()
        _require_sha256(self.authoring_sha256, "authoring_sha256")
        if self.authoring_sha256 != sha256_object(self.semantic_payload()):
            raise FinalExecutionAcknowledgementAuthoringError(
                "acknowledgement authoring semantic SHA-256 differs"
            )

    def canonical_json(self, receipt: WiringMergeValidationReceipt) -> str:
        self.require(receipt)
        return canonical_json(self)


@dataclass(frozen=True)
class ProspectiveFinalExecutionAcknowledgement:
    """Pure future receipt built only after explicit operator acknowledgement."""

    acknowledgement_id: str
    status: str
    acknowledgement_authoring_sha256: str
    acknowledgement_phrase: str
    operator_identity: str
    acknowledged_at_utc: str
    wiring_merge_commit: str
    persistent_evidence_chain_v2_sha256: str
    persistent_evidence_chain_v2_implementation_sha256: str
    lease_bound_host_invoker_wiring_sha256: str
    invocation_authorization_sha256: str
    execution_authorization_sha256: str
    preexecution_verification_sha256: str
    runtime_operation_sha256: str
    identity_repair_sha256: str
    image_repo_digest: str
    torch2pc_commit: str
    output_root: str
    execution_lease_v2_relative: str
    durable_host_outcome_relative: str
    invocation_count: int
    single_attempt_only: bool
    retry_permitted: bool
    execution_lease_materialized: bool
    authorization_consumed: bool

    def require(
        self,
        authoring: FinalExecutionAcknowledgementAuthoring,
        receipt: WiringMergeValidationReceipt,
    ) -> None:
        authoring.require(receipt)
        expected: dict[str, object] = {
            "acknowledgement_id": FINAL_EXECUTION_ACKNOWLEDGEMENT_ID,
            "status": FINAL_EXECUTION_ACKNOWLEDGEMENT_STATUS,
            "acknowledgement_authoring_sha256": authoring.authoring_sha256,
            "acknowledgement_phrase": FINAL_EXECUTION_OPERATOR_ACKNOWLEDGEMENT,
            "wiring_merge_commit": authoring.source.wiring_merge_commit,
            "persistent_evidence_chain_v2_sha256": (
                authoring.source.persistent_evidence_chain_v2_sha256
            ),
            "persistent_evidence_chain_v2_implementation_sha256": (
                authoring.source.persistent_evidence_chain_v2_implementation_sha256
            ),
            "lease_bound_host_invoker_wiring_sha256": (
                authoring.source.lease_bound_host_invoker_wiring_sha256
            ),
            "invocation_authorization_sha256": (
                authoring.source.invocation_authorization_sha256
            ),
            "execution_authorization_sha256": (
                authoring.source.execution_authorization_sha256
            ),
            "preexecution_verification_sha256": (
                authoring.source.preexecution_verification_sha256
            ),
            "runtime_operation_sha256": authoring.source.runtime_operation_sha256,
            "identity_repair_sha256": authoring.source.identity_repair_sha256,
            "image_repo_digest": authoring.source.image_repo_digest,
            "torch2pc_commit": authoring.source.torch2pc_commit,
            "output_root": authoring.source.output_root,
            "execution_lease_v2_relative": (
                authoring.source.execution_lease_v2_relative
            ),
            "durable_host_outcome_relative": (
                authoring.source.durable_host_outcome_relative
            ),
            "invocation_count": 1,
            "single_attempt_only": True,
            "retry_permitted": False,
            "execution_lease_materialized": False,
            "authorization_consumed": False,
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise FinalExecutionAcknowledgementAuthoringError(
                    f"prospective acknowledgement differs: {field_name}"
                )
        if not _OPERATOR_IDENTITY_PATTERN.fullmatch(self.operator_identity):
            raise FinalExecutionAcknowledgementAuthoringError(
                "operator identity is empty or non-canonical"
            )
        acknowledged = _require_utc(
            self.acknowledged_at_utc,
            "acknowledged_at_utc",
        )
        merged = _require_utc(receipt.merged_at_utc, "merged_at_utc")
        if acknowledged <= merged:
            raise FinalExecutionAcknowledgementAuthoringError(
                "acknowledgement timestamp is not after wiring merge"
            )

    def canonical_json(
        self,
        authoring: FinalExecutionAcknowledgementAuthoring,
        receipt: WiringMergeValidationReceipt,
    ) -> str:
        self.require(authoring, receipt)
        return canonical_json(self)


def build_final_execution_acknowledgement(
    authoring: FinalExecutionAcknowledgementAuthoring,
    receipt: WiringMergeValidationReceipt,
    *,
    acknowledgement_phrase: str,
    operator_identity: str,
    acknowledged_at_utc: str,
) -> ProspectiveFinalExecutionAcknowledgement:
    """Build an in-memory future acknowledgement without materializing it."""

    authoring.require(receipt)
    if acknowledgement_phrase != FINAL_EXECUTION_OPERATOR_ACKNOWLEDGEMENT:
        raise FinalExecutionAcknowledgementAuthoringError(
            "operator acknowledgement phrase differs"
        )
    result = ProspectiveFinalExecutionAcknowledgement(
        acknowledgement_id=FINAL_EXECUTION_ACKNOWLEDGEMENT_ID,
        status=FINAL_EXECUTION_ACKNOWLEDGEMENT_STATUS,
        acknowledgement_authoring_sha256=authoring.authoring_sha256,
        acknowledgement_phrase=acknowledgement_phrase,
        operator_identity=operator_identity,
        acknowledged_at_utc=acknowledged_at_utc,
        wiring_merge_commit=authoring.source.wiring_merge_commit,
        persistent_evidence_chain_v2_sha256=(
            authoring.source.persistent_evidence_chain_v2_sha256
        ),
        persistent_evidence_chain_v2_implementation_sha256=(
            authoring.source.persistent_evidence_chain_v2_implementation_sha256
        ),
        lease_bound_host_invoker_wiring_sha256=(
            authoring.source.lease_bound_host_invoker_wiring_sha256
        ),
        invocation_authorization_sha256=(
            authoring.source.invocation_authorization_sha256
        ),
        execution_authorization_sha256=(
            authoring.source.execution_authorization_sha256
        ),
        preexecution_verification_sha256=(
            authoring.source.preexecution_verification_sha256
        ),
        runtime_operation_sha256=authoring.source.runtime_operation_sha256,
        identity_repair_sha256=authoring.source.identity_repair_sha256,
        image_repo_digest=authoring.source.image_repo_digest,
        torch2pc_commit=authoring.source.torch2pc_commit,
        output_root=authoring.source.output_root,
        execution_lease_v2_relative=authoring.source.execution_lease_v2_relative,
        durable_host_outcome_relative=authoring.source.durable_host_outcome_relative,
        invocation_count=1,
        single_attempt_only=True,
        retry_permitted=False,
        execution_lease_materialized=False,
        authorization_consumed=False,
    )
    result.require(authoring, receipt)
    return result


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8", errors="strict"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FinalExecutionAcknowledgementAuthoringError(
            f"cannot load JSON: {path}"
        ) from exc
    if not isinstance(payload, dict):
        raise FinalExecutionAcknowledgementAuthoringError(
            f"JSON root is not an object: {path}"
        )
    return cast(dict[str, Any], payload)


def _load_registry(path: Path) -> dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8", errors="strict").splitlines()
    except OSError as exc:
        raise FinalExecutionAcknowledgementAuthoringError(
            f"cannot load registry: {path}"
        ) from exc
    result: dict[str, str] = {}
    for line in lines:
        try:
            digest, relative = line.split("  ", 1)
        except ValueError as exc:
            raise FinalExecutionAcknowledgementAuthoringError(
                f"malformed registry line: {line!r}"
            ) from exc
        if relative in result:
            raise FinalExecutionAcknowledgementAuthoringError(
                f"duplicate registry path: {relative}"
            )
        result[relative] = "sha256:" + digest
    return result


def load_wiring_merge_validation_receipt(
    path: Path,
) -> WiringMergeValidationReceipt:
    result = WiringMergeValidationReceipt.from_mapping(_load_json(path))
    result.require()
    return result


def load_final_execution_acknowledgement_authoring(
    path: Path,
    receipt: WiringMergeValidationReceipt,
) -> FinalExecutionAcknowledgementAuthoring:
    result = FinalExecutionAcknowledgementAuthoring.from_mapping(_load_json(path))
    result.require(receipt)
    return result


def verify_final_execution_acknowledgement_authoring(
    project_root: Path,
) -> FinalExecutionAcknowledgementAuthoring:
    """Verify the complete static authoring freeze and closed runtime boundary."""

    root = project_root.expanduser().resolve()
    package = root / PACKAGE_RELATIVE
    if not package.is_dir() or package.is_symlink():
        raise FinalExecutionAcknowledgementAuthoringError(
            "acknowledgement authoring package is absent or invalid"
        )
    if frozenset(path.name for path in package.iterdir()) != _EXPECTED_PACKAGE_FILES:
        raise FinalExecutionAcknowledgementAuthoringError(
            "acknowledgement authoring package file set differs"
        )
    package_registry = _verify_registry(root / REGISTRY_RELATIVE, package)
    if frozenset(package_registry) != frozenset(
        {
            "authoring.json",
            "source-SHA256SUMS",
            "wiring-merge-validation.json",
        }
    ):
        raise FinalExecutionAcknowledgementAuthoringError(
            "acknowledgement package registry scope differs"
        )
    source_registry = _verify_registry(root / SOURCE_REGISTRY_RELATIVE, root)
    if frozenset(source_registry) != _EXPECTED_SOURCE_PATHS:
        raise FinalExecutionAcknowledgementAuthoringError(
            "acknowledgement source registry scope differs"
        )
    receipt = load_wiring_merge_validation_receipt(
        root / WIRING_MERGE_RECEIPT_RELATIVE
    )
    authoring = load_final_execution_acknowledgement_authoring(
        root / AUTHORING_RECORD_RELATIVE,
        receipt,
    )
    _verify_upstream_records(root, authoring)
    _verify_effect_free_authoring_ast(root)
    _require_repository_boundary_closed(root)
    return authoring


def _verify_registry(path: Path, base: Path) -> dict[str, str]:
    registry = _load_registry(path)
    for relative, expected in registry.items():
        target = base / relative
        if not target.is_file() or target.is_symlink():
            raise FinalExecutionAcknowledgementAuthoringError(
                f"registry target is absent or invalid: {relative}"
            )
        observed = sha256_bytes(target.read_bytes())
        if observed != expected:
            raise FinalExecutionAcknowledgementAuthoringError(
                f"registry digest differs: {relative}"
            )
    return registry


def _verify_upstream_records(
    root: Path,
    authoring: FinalExecutionAcknowledgementAuthoring,
) -> None:
    chain_path = root / CHAIN_RECORD_RELATIVE
    implementation_path = root / IMPLEMENTATION_RECORD_RELATIVE
    wiring_path = root / WIRING_RECORD_RELATIVE
    if sha256_bytes(chain_path.read_bytes()) != (
        authoring.source.persistent_evidence_chain_v2_file_sha256
    ):
        raise FinalExecutionAcknowledgementAuthoringError(
            "persistent evidence chain file SHA-256 differs"
        )
    if sha256_bytes(implementation_path.read_bytes()) != (
        authoring.source.persistent_evidence_chain_v2_implementation_file_sha256
    ):
        raise FinalExecutionAcknowledgementAuthoringError(
            "persistent implementation file SHA-256 differs"
        )
    if sha256_bytes(wiring_path.read_bytes()) != (
        authoring.source.lease_bound_host_invoker_wiring_file_sha256
    ):
        raise FinalExecutionAcknowledgementAuthoringError(
            "wiring file SHA-256 differs"
        )
    chain = _load_json(chain_path)
    implementation = _load_json(implementation_path)
    wiring = _load_json(wiring_path)
    exact: tuple[tuple[dict[str, Any], str, object], ...] = (
        (chain, "chain_id", authoring.source.persistent_evidence_chain_v2_id),
        (
            chain,
            "chain_sha256",
            authoring.source.persistent_evidence_chain_v2_sha256,
        ),
        (
            implementation,
            "implementation_id",
            authoring.source.persistent_evidence_chain_v2_implementation_id,
        ),
        (
            implementation,
            "implementation_sha256",
            authoring.source.persistent_evidence_chain_v2_implementation_sha256,
        ),
        (wiring, "wiring_id", authoring.source.lease_bound_host_invoker_wiring_id),
        (
            wiring,
            "wiring_sha256",
            authoring.source.lease_bound_host_invoker_wiring_sha256,
        ),
        (wiring, "implementation_merge_commit", WIRING_PARENT_COMMIT),
        (wiring, "lease_bound_host_invoker_enforced", True),
        (wiring, "final_execution_acknowledged", False),
        (wiring, "one_shot_engineering_invocation_permitted", False),
        (wiring, "execution_lease_materialized", False),
        (wiring, "runtime_execution_performed", False),
    )
    for payload, field_name, expected in exact:
        if payload.get(field_name) != expected:
            raise FinalExecutionAcknowledgementAuthoringError(
                f"upstream record differs: {field_name}"
            )


def _verify_effect_free_authoring_ast(root: Path) -> None:
    tree = ast.parse(
        (root / MODULE_RELATIVE).read_text(encoding="utf-8", errors="strict")
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".", 1)[0] in _FORBIDDEN_IMPORT_ROOTS:
                    raise FinalExecutionAcknowledgementAuthoringError(
                        f"forbidden authoring import: {alias.name}"
                    )
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split(".", 1)[0] in _FORBIDDEN_IMPORT_ROOTS:
                raise FinalExecutionAcknowledgementAuthoringError(
                    f"forbidden authoring import: {node.module}"
                )
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in _FORBIDDEN_CALL_NAMES:
                raise FinalExecutionAcknowledgementAuthoringError(
                    f"forbidden authoring call: {node.func.id}"
                )
            if (
                isinstance(node.func, ast.Attribute)
                and node.func.attr in _FORBIDDEN_CALL_ATTRIBUTES
            ):
                raise FinalExecutionAcknowledgementAuthoringError(
                    f"forbidden authoring call: {node.func.attr}"
                )


def _require_repository_boundary_closed(root: Path) -> None:
    output = root / AUTHORIZED_OUTPUT_ROOT
    lease_v1 = root / (AUTHORIZED_OUTPUT_ROOT + ".execution-lease.json")
    lease_v2 = root / EXECUTION_LEASE_V2_RELATIVE
    outcome = root / DURABLE_HOST_OUTCOME_RELATIVE
    for path, label in (
        (output, "runtime output"),
        (lease_v1, "execution lease v1"),
        (lease_v2, "execution lease v2"),
        (outcome, "durable host outcome"),
    ):
        if path.exists() or path.is_symlink():
            raise FinalExecutionAcknowledgementAuthoringError(
                f"{label} exists during acknowledgement authoring"
            )
    parent = output.parent
    pattern = ".qwake-lc4-runtime-validation-v1-attempt-001.staging-*"
    if parent.is_dir() and any(parent.glob(pattern)):
        raise FinalExecutionAcknowledgementAuthoringError(
            "runtime staging path exists during acknowledgement authoring"
        )


def _build_source(
    receipt: WiringMergeValidationReceipt,
) -> FinalExecutionAcknowledgementSource:
    return FinalExecutionAcknowledgementSource(
        authoring_base_commit=AUTHORING_BASE_COMMIT,
        wiring_pr_number=WIRING_PR_NUMBER,
        wiring_head_commit=WIRING_HEAD_COMMIT,
        wiring_parent_commit=WIRING_PARENT_COMMIT,
        wiring_merge_commit=WIRING_MERGE_COMMIT,
        wiring_merged_at_utc=WIRING_MERGED_AT_UTC,
        wiring_merge_receipt_sha256=receipt.receipt_sha256,
        persistent_evidence_chain_v2_id=PERSISTENT_EVIDENCE_CHAIN_V2_ID,
        persistent_evidence_chain_v2_sha256=PERSISTENT_EVIDENCE_CHAIN_V2_SHA256,
        persistent_evidence_chain_v2_file_sha256=(
            PERSISTENT_EVIDENCE_CHAIN_V2_FILE_SHA256
        ),
        persistent_evidence_chain_v2_implementation_id=(
            PERSISTENT_EVIDENCE_CHAIN_V2_IMPLEMENTATION_ID
        ),
        persistent_evidence_chain_v2_implementation_sha256=(
            PERSISTENT_EVIDENCE_CHAIN_V2_IMPLEMENTATION_SHA256
        ),
        persistent_evidence_chain_v2_implementation_file_sha256=(
            PERSISTENT_EVIDENCE_CHAIN_V2_IMPLEMENTATION_FILE_SHA256
        ),
        lease_bound_host_invoker_wiring_id=LEASE_BOUND_HOST_INVOKER_WIRING_ID,
        lease_bound_host_invoker_wiring_sha256=(
            LEASE_BOUND_HOST_INVOKER_WIRING_SHA256
        ),
        lease_bound_host_invoker_wiring_file_sha256=(
            LEASE_BOUND_HOST_INVOKER_WIRING_FILE_SHA256
        ),
        invocation_authorization_id=INVOCATION_AUTHORIZATION_ID,
        invocation_authorization_sha256=INVOCATION_AUTHORIZATION_SHA256,
        execution_authorization_id=EXECUTION_AUTHORIZATION_ID,
        execution_authorization_sha256=EXECUTION_AUTHORIZATION_SHA256,
        preexecution_verification_id=PREEXECUTION_VERIFICATION_ID,
        preexecution_verification_sha256=PREEXECUTION_VERIFICATION_SHA256,
        runtime_operation_id=RUNTIME_OPERATION_ID,
        runtime_operation_sha256=RUNTIME_OPERATION_SHA256,
        identity_repair_id=IDENTITY_REPAIR_ID,
        identity_repair_sha256=IDENTITY_REPAIR_SHA256,
        image_repo_digest=IMAGE_REPO_DIGEST,
        torch2pc_commit=TORCH2PC_COMMIT,
        output_root=AUTHORIZED_OUTPUT_ROOT,
        execution_lease_v2_relative=EXECUTION_LEASE_V2_RELATIVE.as_posix(),
        durable_host_outcome_relative=DURABLE_HOST_OUTCOME_RELATIVE.as_posix(),
        invocation_count=INVOCATION_COUNT,
    )


def _build_contract() -> FinalExecutionAcknowledgementContract:
    return FinalExecutionAcknowledgementContract(
        exact_operator_phrase_required=FINAL_EXECUTION_OPERATOR_ACKNOWLEDGEMENT,
        explicit_operator_identity_required=True,
        explicit_utc_timestamp_required=True,
        acknowledgement_after_wiring_merge_required=True,
        complete_identity_chain_required=True,
        exact_image_digest_required=True,
        exact_torch2pc_commit_required=True,
        exact_output_root_required=True,
        exact_lease_and_outcome_paths_required=True,
        invocation_count_required=1,
        single_attempt_only=True,
        automatic_retry_forbidden=True,
        automatic_transition_from_authoring_forbidden=True,
        acknowledgement_materialization_separate=True,
        execution_lease_materialization_separate=True,
        acknowledgement_required_before_lease_claim=True,
        lease_required_before_host_invocation=True,
        durable_terminal_outcome_required=True,
        authoring_effects_forbidden=True,
    )


def _build_gates() -> FinalExecutionAcknowledgementGates:
    return FinalExecutionAcknowledgementGates(
        wiring_post_merge_verified=True,
        persistent_evidence_chain_v2_present=True,
        persistent_lease_v2_implementation_present=True,
        durable_outcome_writer_implemented=True,
        lease_bound_host_invoker_enforced=True,
        final_execution_acknowledgement_authored=True,
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


def build_frozen_authoring_record(
    receipt: WiringMergeValidationReceipt,
) -> FinalExecutionAcknowledgementAuthoring:
    """Build the canonical static authoring record."""

    receipt.require()
    provisional = FinalExecutionAcknowledgementAuthoring(
        schema_version=1,
        authoring_id=FINAL_EXECUTION_ACKNOWLEDGEMENT_AUTHORING_ID,
        status=FINAL_EXECUTION_ACKNOWLEDGEMENT_AUTHORING_STATUS,
        recorded_at_utc="2026-07-30T15:00:00Z",
        source=_build_source(receipt),
        contract=_build_contract(),
        gates=_build_gates(),
        next_slice="QW-LC4-E-final-execution-acknowledgement-authoring-commit",
        post_merge_next_slice=(
            "QW-LC4-E-final-execution-acknowledgement-issuance"
        ),
        authoring_sha256="sha256:" + "0" * 64,
    )
    result = replace(
        provisional,
        authoring_sha256=sha256_object(provisional.semantic_payload()),
    )
    result.require(receipt)
    return result


def build_wiring_merge_validation_receipt() -> WiringMergeValidationReceipt:
    """Build the exact independently verified PR 146 merge receipt."""

    provisional = WiringMergeValidationReceipt(
        receipt_id=(
            "stage3b-qwake-lc4-e-lease-bound-host-invoker-wiring-"
            "post-merge-validation-v1"
        ),
        pr_number=146,
        head_commit=WIRING_HEAD_COMMIT,
        base_commit=WIRING_PARENT_COMMIT,
        merge_commit=WIRING_MERGE_COMMIT,
        merged_at_utc=WIRING_MERGED_AT_UTC,
        commit_count=1,
        file_count=18,
        focused_tests_passed=39,
        targeted_tests_passed=240,
        full_tests_passed=1287,
        full_test_warnings=14,
        required_ci_checks_passed=True,
        runtime_boundary_closed=True,
        receipt_sha256="sha256:" + "0" * 64,
    )
    result = replace(
        provisional,
        receipt_sha256=sha256_object(provisional.semantic_payload()),
    )
    result.require()
    return result
