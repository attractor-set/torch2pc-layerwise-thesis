"""Effect-free authoring contracts for the QW-LC4-E evidence chain v2.

The module freezes the complete authorization-to-runtime identity chain and
provides pure builders for a future persistent execution lease v2 and a durable
terminal host-outcome receipt.  Importing, loading, or verifying this module
never inspects an image, materializes an invocation, writes a lease or receipt,
spawns a child process, invokes Docker, or executes local compute.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final, cast

PERSISTENT_EVIDENCE_CHAIN_V2_ID: Final = (
    "stage3b-qwake-lc4-e-persistent-evidence-chain-v2-authoring-v1"
)
PERSISTENT_EVIDENCE_CHAIN_V2_STATUS: Final = (
    "persistent_evidence_chain_v2_authored_execution_closed"
)
POST_MERGE_VALIDATION_RECEIPT_ID: Final = (
    "stage3b-qwake-lc4-e-runtime-operation-identity-repair-"
    "post-merge-validation-v1"
)
PERSISTENT_EXECUTION_LEASE_V2_ID: Final = (
    "stage3b-qwake-lc4-e-persistent-execution-lease-v2"
)
PERSISTENT_EXECUTION_LEASE_V2_STATUS: Final = (
    "prospective_single_attempt_persistent_lease_not_materialized"
)
DURABLE_HOST_OUTCOME_RECEIPT_ID: Final = (
    "stage3b-qwake-lc4-e-durable-host-outcome-receipt-v1"
)
PERSISTENT_LEASE_V2_OPERATOR_ACKNOWLEDGEMENT: Final = (
    "CLAIM_QWAKE_LC4_ONE_SHOT_PERSISTENT_EVIDENCE_CHAIN_V2"
)

AUTHORING_BASE_COMMIT: Final = "5e61ed650c9beda2cde1f58650345f01694836f6"
IDENTITY_REPAIR_PR_NUMBER: Final = 143
IDENTITY_REPAIR_HEAD_COMMIT: Final = (
    "d7a5c121b2f7e56155603bbfbf98f3713f0c0e87"
)
IDENTITY_REPAIR_PARENT_COMMIT: Final = (
    "97dacb207aa201f1fd2f43c66ae34b1adced32bb"
)
IDENTITY_REPAIR_MERGE_COMMIT: Final = AUTHORING_BASE_COMMIT
IDENTITY_REPAIR_MERGED_AT_UTC: Final = "2026-07-30T02:21:08Z"

INVOCATION_AUTHORIZATION_ID: Final = (
    "stage3b-qwake-lc4-e-one-shot-engineering-invocation-authorization-v1"
)
INVOCATION_AUTHORIZATION_SHA256: Final = (
    "sha256:0a60dacc1bfd5073cf52d76f2ec33ae54f00899aad9877d44607199659fda75a"
)
INVOCATION_AUTHORIZATION_FILE_SHA256: Final = (
    "sha256:e7b58ad04a932b36a0eaea5a276e95c593d4e88e303e05dadbb25eaf3eb5c999"
)
INVOCATION_AUTHORIZATION_MERGE_COMMIT: Final = (
    "375db196b615f7024cd5f715de9c9be7b526a9f7"
)

EXECUTION_AUTHORIZATION_ID: Final = (
    "stage3b-qwake-lc4-e-one-shot-engineering-invocation-"
    "execution-authorization-v1"
)
EXECUTION_AUTHORIZATION_SHA256: Final = (
    "sha256:ff136538faee0d7952dc444e521d7ec760c7d54cd38406cb9b19ff1e00d9437b"
)
EXECUTION_AUTHORIZATION_FILE_SHA256: Final = (
    "sha256:11f12d2c2723902716ca9e7209f408b9edae2f793ceb098c8adeb06fee8c0c72"
)
EXECUTION_AUTHORIZATION_MERGE_COMMIT: Final = (
    "49c4b97e93b47cefbf35576736927ece02c9402b"
)

PREEXECUTION_VERIFICATION_ID: Final = (
    "stage3b-qwake-lc4-e-one-shot-engineering-invocation-"
    "preexecution-verification-v1"
)
PREEXECUTION_VERIFICATION_SHA256: Final = (
    "sha256:833371b427a5c8a6e602d675711b85b2edc68441b9e5be191321a2911bce6128"
)
PREEXECUTION_VERIFICATION_FILE_SHA256: Final = (
    "sha256:a0f19309fc7bb2abe47f300a793423e8c764d6330220b4d4e8db3724c01df9f1"
)
PREEXECUTION_VERIFICATION_MERGE_COMMIT: Final = (
    "494e6a0b2f10c26b49c90fbb84c23565699a4064"
)

RUNTIME_OPERATION_ID: Final = (
    "stage3b-qwake-lc4-e-one-shot-engineering-invocation-runtime-operation-v1"
)
RUNTIME_OPERATION_SHA256: Final = (
    "sha256:0332428014f7f8385c789ba7e7c55d6c2ec03b020e3f83df9ac9714483bb6bf8"
)
RUNTIME_OPERATION_FILE_SHA256: Final = (
    "sha256:ba9b514980bf5f8629cc6a140a0b95114689020a4cffb8bf3ce4a58fade10247"
)
RUNTIME_OPERATION_MERGE_COMMIT: Final = (
    "97dacb207aa201f1fd2f43c66ae34b1adced32bb"
)
CORRECTED_RUNTIME_OPERATION_MODULE_SHA256: Final = (
    "sha256:da08c66e78340c067e391a28f326f0d9bb7465d4a56073deac458a764ae6b30d"
)

IDENTITY_REPAIR_ID: Final = (
    "stage3b-qwake-lc4-e-one-shot-engineering-invocation-"
    "runtime-operation-identity-repair-v1"
)
IDENTITY_REPAIR_SHA256: Final = (
    "sha256:ff6d22e98257bb55774abf8ad2418a60c759981049994720ae814e9ff6ccc4c6"
)
IDENTITY_REPAIR_FILE_SHA256: Final = (
    "sha256:eac8f15bc9768eebd2d83d229d75444de62c5052b23e1b531185eb65180be71e"
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
    "stage3b-qwake-lc4-e-persistent-evidence-chain-v2-authoring-v1"
)
CHAIN_RECORD_RELATIVE: Final = PACKAGE_RELATIVE / "chain.json"
POST_MERGE_RECEIPT_RELATIVE: Final = (
    PACKAGE_RELATIVE / "post-merge-validation.json"
)
REGISTRY_RELATIVE: Final = PACKAGE_RELATIVE / "SHA256SUMS"
SOURCE_REGISTRY_RELATIVE: Final = PACKAGE_RELATIVE / "source-SHA256SUMS"

INVOCATION_AUTHORIZATION_RECORD_RELATIVE: Final = Path(
    "experiments/frozen/stage3b-qwake-lc4-e-one-shot-engineering-"
    "invocation-authorization-v1/authorization.json"
)
EXECUTION_AUTHORIZATION_RECORD_RELATIVE: Final = Path(
    "experiments/frozen/stage3b-qwake-lc4-e-one-shot-engineering-"
    "invocation-execution-authorization-v1/authorization.json"
)
PREEXECUTION_RECORD_RELATIVE: Final = Path(
    "experiments/frozen/stage3b-qwake-lc4-e-one-shot-engineering-"
    "invocation-preexecution-verification-v1/verification.json"
)
RUNTIME_OPERATION_RECORD_RELATIVE: Final = Path(
    "experiments/frozen/stage3b-qwake-lc4-e-one-shot-engineering-"
    "invocation-runtime-operation-v1/operation.json"
)
IDENTITY_REPAIR_RECORD_RELATIVE: Final = Path(
    "experiments/frozen/stage3b-qwake-lc4-e-one-shot-engineering-"
    "invocation-runtime-operation-identity-repair-v1/repair.json"
)
RUNTIME_OPERATION_MODULE_RELATIVE: Final = Path(
    "src/torch2pc_thesis/"
    "stage3b_qwake_lc4_engineering_invocation_runtime_operation.py"
)
HOST_RUNTIME_INVOKER_MODULE_RELATIVE: Final = Path(
    "src/torch2pc_thesis/"
    "stage3b_qwake_lc4_host_runtime_invoker_implementation.py"
)
EXECUTION_WRAPPER_MODULE_RELATIVE: Final = Path(
    "src/torch2pc_thesis/stage3b_qwake_lc4_execution_wrapper.py"
)
EXECUTION_WRAPPER_IMPLEMENTATION_RELATIVE: Final = Path(
    "src/torch2pc_thesis/"
    "stage3b_qwake_lc4_execution_wrapper_implementation.py"
)
MODULE_RELATIVE: Final = Path(
    "src/torch2pc_thesis/stage3b_qwake_lc4_persistent_evidence_chain_v2.py"
)
VERIFIER_RELATIVE: Final = Path(
    "scripts/verify_stage3b_qwake_lc4_persistent_evidence_chain_v2.py"
)
TEST_RELATIVE: Final = Path(
    "tests/unit/test_stage3b_qwake_lc4_persistent_evidence_chain_v2.py"
)
ADR_RU_RELATIVE: Final = Path(
    "docs/decisions/ADR-083-stage3b-qwake-lc4-e-persistent-evidence-chain-v2.md"
)
ADR_EN_RELATIVE: Final = Path(
    "docs/decisions/"
    "ADR-083-stage3b-qwake-lc4-e-persistent-evidence-chain-v2_EN.md"
)

_EXPECTED_PACKAGE_FILES: Final = frozenset(
    {
        "SHA256SUMS",
        "chain.json",
        "post-merge-validation.json",
        "source-SHA256SUMS",
    }
)
_EXPECTED_SOURCE_PATHS: Final = frozenset(
    {
        INVOCATION_AUTHORIZATION_RECORD_RELATIVE.as_posix(),
        EXECUTION_AUTHORIZATION_RECORD_RELATIVE.as_posix(),
        PREEXECUTION_RECORD_RELATIVE.as_posix(),
        RUNTIME_OPERATION_RECORD_RELATIVE.as_posix(),
        IDENTITY_REPAIR_RECORD_RELATIVE.as_posix(),
        RUNTIME_OPERATION_MODULE_RELATIVE.as_posix(),
        HOST_RUNTIME_INVOKER_MODULE_RELATIVE.as_posix(),
        EXECUTION_WRAPPER_MODULE_RELATIVE.as_posix(),
        EXECUTION_WRAPPER_IMPLEMENTATION_RELATIVE.as_posix(),
        MODULE_RELATIVE.as_posix(),
        VERIFIER_RELATIVE.as_posix(),
        TEST_RELATIVE.as_posix(),
        ADR_RU_RELATIVE.as_posix(),
        ADR_EN_RELATIVE.as_posix(),
    }
)
_ALLOWED_TERMINATION_CLASSES: Final = frozenset(
    {
        "success",
        "nonzero_return_code",
        "child_signal",
        "timeout",
        "forwarded_signal",
        "prelaunch_rejected",
        "spawn_failed",
        "process_control_failed",
        "capture_failed",
        "unexpected_failure",
    }
)
_SHA256_PATTERN: Final = re.compile(r"^sha256:[0-9a-f]{64}$")
_COMMIT_PATTERN: Final = re.compile(r"^[0-9a-f]{40}$")

__all__ = [
    "DURABLE_HOST_OUTCOME_RECEIPT_ID",
    "PERSISTENT_EVIDENCE_CHAIN_V2_ID",
    "PERSISTENT_EXECUTION_LEASE_V2_ID",
    "PERSISTENT_LEASE_V2_OPERATOR_ACKNOWLEDGEMENT",
    "DurableHostOutcomeReceipt",
    "OutputSnapshot",
    "PersistentEvidenceChainV2",
    "PersistentEvidenceChainV2Contract",
    "PersistentEvidenceChainV2Error",
    "PersistentEvidenceChainV2Gates",
    "PersistentEvidenceChainV2Source",
    "PersistentExecutionLeaseV2",
    "PostMergeValidationReceipt",
    "build_durable_host_outcome_receipt",
    "build_persistent_execution_lease_v2",
    "canonical_json",
    "load_persistent_evidence_chain_v2",
    "load_post_merge_validation_receipt",
    "sha256_bytes",
    "sha256_object",
    "verify_persistent_evidence_chain_v2",
]


class PersistentEvidenceChainV2Error(RuntimeError):
    """Raised when the evidence-chain-v2 contract fails closed."""


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
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def sha256_bytes(value: bytes) -> str:
    """Hash exact bytes using the repository SHA-256 notation."""

    return "sha256:" + hashlib.sha256(value).hexdigest()


def _require_sha256(value: str, field_name: str) -> None:
    if _SHA256_PATTERN.fullmatch(value) is None:
        raise PersistentEvidenceChainV2Error(
            f"{field_name} is not SHA-256"
        )


def _require_commit(value: str, field_name: str) -> None:
    if _COMMIT_PATTERN.fullmatch(value) is None:
        raise PersistentEvidenceChainV2Error(f"{field_name} is not a commit")


def _require_utc(value: str, field_name: str) -> datetime:
    if not value.endswith("Z"):
        raise PersistentEvidenceChainV2Error(f"{field_name} is not UTC")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise PersistentEvidenceChainV2Error(
            f"{field_name} is not an ISO-8601 timestamp"
        ) from exc
    if parsed.tzinfo != UTC:
        raise PersistentEvidenceChainV2Error(f"{field_name} is not UTC")
    return parsed


@dataclass(frozen=True)
class PostMergeValidationReceipt:
    """Durable record of the independently verified PR 143 merge."""

    schema_version: int
    receipt_id: str
    recorded_at_utc: str
    pr_number: int
    pr_head_commit: str
    pr_base_commit: str
    merge_commit: str
    merged_at_utc: str
    merge_parent_1: str
    merge_parent_2: str
    commit_count: int
    file_count: int
    focused_passed: int
    targeted_passed: int
    full_passed: int
    warning_count: int
    required_ci_checks_passed: bool
    package_registries_passed: bool
    ruff_passed: bool
    mypy_passed: bool
    ru_mkdocs_passed: bool
    en_mkdocs_passed: bool
    torch2pc_identity_passed: bool
    runtime_boundary_closed: bool
    receipt_sha256: str

    def require(self) -> None:
        exact: Mapping[str, object] = {
            "schema_version": 1,
            "receipt_id": POST_MERGE_VALIDATION_RECEIPT_ID,
            "pr_number": IDENTITY_REPAIR_PR_NUMBER,
            "pr_head_commit": IDENTITY_REPAIR_HEAD_COMMIT,
            "pr_base_commit": IDENTITY_REPAIR_PARENT_COMMIT,
            "merge_commit": IDENTITY_REPAIR_MERGE_COMMIT,
            "merged_at_utc": IDENTITY_REPAIR_MERGED_AT_UTC,
            "merge_parent_1": IDENTITY_REPAIR_PARENT_COMMIT,
            "merge_parent_2": IDENTITY_REPAIR_HEAD_COMMIT,
            "commit_count": 1,
            "file_count": 18,
            "focused_passed": 24,
            "targeted_passed": 201,
            "full_passed": 1248,
            "warning_count": 14,
            "required_ci_checks_passed": True,
            "package_registries_passed": True,
            "ruff_passed": True,
            "mypy_passed": True,
            "ru_mkdocs_passed": True,
            "en_mkdocs_passed": True,
            "torch2pc_identity_passed": True,
            "runtime_boundary_closed": True,
        }
        for field_name, expected in exact.items():
            if getattr(self, field_name) != expected:
                raise PersistentEvidenceChainV2Error(
                    f"post-merge validation differs: {field_name}"
                )
        _require_utc(self.recorded_at_utc, "recorded_at_utc")
        _require_utc(self.merged_at_utc, "merged_at_utc")
        for value, field_name in (
            (self.pr_head_commit, "pr_head_commit"),
            (self.pr_base_commit, "pr_base_commit"),
            (self.merge_commit, "merge_commit"),
            (self.merge_parent_1, "merge_parent_1"),
            (self.merge_parent_2, "merge_parent_2"),
        ):
            _require_commit(value, field_name)
        _require_sha256(self.receipt_sha256, "receipt_sha256")
        if self.receipt_sha256 != sha256_object(self._payload_without_digest()):
            raise PersistentEvidenceChainV2Error(
                "post-merge validation receipt digest differs"
            )

    def _payload_without_digest(self) -> Mapping[str, object]:
        payload = asdict(self)
        payload.pop("receipt_sha256")
        return cast(Mapping[str, object], payload)

    def canonical_json(self) -> str:
        return canonical_json(self)


@dataclass(frozen=True)
class PersistentEvidenceChainV2Source:
    """Exact authorization, runtime, image, and repository identities."""

    authoring_base_commit: str
    invocation_authorization_id: str
    invocation_authorization_sha256: str
    invocation_authorization_file_sha256: str
    invocation_authorization_merge_commit: str
    execution_authorization_id: str
    execution_authorization_sha256: str
    execution_authorization_file_sha256: str
    execution_authorization_merge_commit: str
    preexecution_verification_id: str
    preexecution_verification_sha256: str
    preexecution_verification_file_sha256: str
    preexecution_verification_merge_commit: str
    runtime_operation_id: str
    runtime_operation_sha256: str
    runtime_operation_file_sha256: str
    runtime_operation_merge_commit: str
    corrected_runtime_operation_module_sha256: str
    identity_repair_id: str
    identity_repair_sha256: str
    identity_repair_file_sha256: str
    identity_repair_merge_commit: str
    image_repo_digest: str
    torch2pc_commit: str
    output_root: str
    execution_lease_v2_relative: str
    durable_host_outcome_relative: str
    invocation_count: int

    def require(self) -> None:
        exact: Mapping[str, object] = {
            "authoring_base_commit": AUTHORING_BASE_COMMIT,
            "invocation_authorization_id": INVOCATION_AUTHORIZATION_ID,
            "invocation_authorization_sha256": (
                INVOCATION_AUTHORIZATION_SHA256
            ),
            "invocation_authorization_file_sha256": (
                INVOCATION_AUTHORIZATION_FILE_SHA256
            ),
            "invocation_authorization_merge_commit": (
                INVOCATION_AUTHORIZATION_MERGE_COMMIT
            ),
            "execution_authorization_id": EXECUTION_AUTHORIZATION_ID,
            "execution_authorization_sha256": EXECUTION_AUTHORIZATION_SHA256,
            "execution_authorization_file_sha256": (
                EXECUTION_AUTHORIZATION_FILE_SHA256
            ),
            "execution_authorization_merge_commit": (
                EXECUTION_AUTHORIZATION_MERGE_COMMIT
            ),
            "preexecution_verification_id": PREEXECUTION_VERIFICATION_ID,
            "preexecution_verification_sha256": (
                PREEXECUTION_VERIFICATION_SHA256
            ),
            "preexecution_verification_file_sha256": (
                PREEXECUTION_VERIFICATION_FILE_SHA256
            ),
            "preexecution_verification_merge_commit": (
                PREEXECUTION_VERIFICATION_MERGE_COMMIT
            ),
            "runtime_operation_id": RUNTIME_OPERATION_ID,
            "runtime_operation_sha256": RUNTIME_OPERATION_SHA256,
            "runtime_operation_file_sha256": RUNTIME_OPERATION_FILE_SHA256,
            "runtime_operation_merge_commit": RUNTIME_OPERATION_MERGE_COMMIT,
            "corrected_runtime_operation_module_sha256": (
                CORRECTED_RUNTIME_OPERATION_MODULE_SHA256
            ),
            "identity_repair_id": IDENTITY_REPAIR_ID,
            "identity_repair_sha256": IDENTITY_REPAIR_SHA256,
            "identity_repair_file_sha256": IDENTITY_REPAIR_FILE_SHA256,
            "identity_repair_merge_commit": IDENTITY_REPAIR_MERGE_COMMIT,
            "image_repo_digest": IMAGE_REPO_DIGEST,
            "torch2pc_commit": TORCH2PC_COMMIT,
            "output_root": AUTHORIZED_OUTPUT_ROOT,
            "execution_lease_v2_relative": (
                EXECUTION_LEASE_V2_RELATIVE.as_posix()
            ),
            "durable_host_outcome_relative": (
                DURABLE_HOST_OUTCOME_RELATIVE.as_posix()
            ),
            "invocation_count": INVOCATION_COUNT,
        }
        for field_name, expected in exact.items():
            if getattr(self, field_name) != expected:
                raise PersistentEvidenceChainV2Error(
                    f"persistent evidence source differs: {field_name}"
                )
        for field_name in (
            "authoring_base_commit",
            "invocation_authorization_merge_commit",
            "execution_authorization_merge_commit",
            "preexecution_verification_merge_commit",
            "runtime_operation_merge_commit",
            "identity_repair_merge_commit",
            "torch2pc_commit",
        ):
            _require_commit(cast(str, getattr(self, field_name)), field_name)
        for field_name in (
            "invocation_authorization_sha256",
            "invocation_authorization_file_sha256",
            "execution_authorization_sha256",
            "execution_authorization_file_sha256",
            "preexecution_verification_sha256",
            "preexecution_verification_file_sha256",
            "runtime_operation_sha256",
            "runtime_operation_file_sha256",
            "corrected_runtime_operation_module_sha256",
            "identity_repair_sha256",
            "identity_repair_file_sha256",
        ):
            _require_sha256(cast(str, getattr(self, field_name)), field_name)


@dataclass(frozen=True)
class PersistentEvidenceChainV2Contract:
    """Required semantics for future lease and outcome persistence."""

    persistent_lease_v2_required: bool
    complete_identity_chain_required: bool
    claimed_at_utc_required: bool
    invocation_count_required: int
    exclusive_atomic_lease_claim_required: bool
    lease_persists_after_terminal_failure: bool
    lease_bound_host_invoker_capability_required: bool
    direct_lower_level_invocation_forbidden: bool
    durable_terminal_outcome_required: bool
    outcome_required_after_lease_claim: bool
    outcome_required_for_prelaunch_failure: bool
    outcome_required_for_spawn_failure: bool
    outcome_required_for_nonzero_return: bool
    outcome_required_for_timeout_or_signal: bool
    outcome_start_end_utc_required: bool
    outcome_return_code_required_when_available: bool
    stdout_stderr_sha256_required: bool
    output_before_after_snapshots_required: bool
    automatic_retry_forbidden: bool
    receipt_atomic_exclusive_write_required: bool
    authoring_effects_forbidden: bool

    def require(self) -> None:
        exact: Mapping[str, object] = {
            "persistent_lease_v2_required": True,
            "complete_identity_chain_required": True,
            "claimed_at_utc_required": True,
            "invocation_count_required": 1,
            "exclusive_atomic_lease_claim_required": True,
            "lease_persists_after_terminal_failure": True,
            "lease_bound_host_invoker_capability_required": True,
            "direct_lower_level_invocation_forbidden": True,
            "durable_terminal_outcome_required": True,
            "outcome_required_after_lease_claim": True,
            "outcome_required_for_prelaunch_failure": True,
            "outcome_required_for_spawn_failure": True,
            "outcome_required_for_nonzero_return": True,
            "outcome_required_for_timeout_or_signal": True,
            "outcome_start_end_utc_required": True,
            "outcome_return_code_required_when_available": True,
            "stdout_stderr_sha256_required": True,
            "output_before_after_snapshots_required": True,
            "automatic_retry_forbidden": True,
            "receipt_atomic_exclusive_write_required": True,
            "authoring_effects_forbidden": True,
        }
        for field_name, expected in exact.items():
            if getattr(self, field_name) != expected:
                raise PersistentEvidenceChainV2Error(
                    f"persistent evidence contract differs: {field_name}"
                )


@dataclass(frozen=True)
class PersistentEvidenceChainV2Gates:
    """Current authoring gates; implementation and execution remain closed."""

    post_merge_validation_receipt_present: bool
    runtime_operation_identity_repair_merged: bool
    latest_authorization_bound_in_lease_template: bool
    durable_negative_host_outcome_defined: bool
    persistent_lease_v2_implementation_present: bool
    durable_outcome_writer_implemented: bool
    lease_bound_host_invoker_enforced: bool
    final_execution_acknowledged: bool
    one_shot_engineering_invocation_permitted: bool
    execution_lease_materialized: bool
    authorization_consumed: bool
    runtime_execution_started: bool
    runtime_execution_performed: bool
    image_inspection_performed: bool
    invocation_command_materialized: bool
    docker_run_performed: bool
    local_compute_execution_open: bool

    def require(self) -> None:
        exact: Mapping[str, object] = {
            "post_merge_validation_receipt_present": True,
            "runtime_operation_identity_repair_merged": True,
            "latest_authorization_bound_in_lease_template": True,
            "durable_negative_host_outcome_defined": True,
            "persistent_lease_v2_implementation_present": False,
            "durable_outcome_writer_implemented": False,
            "lease_bound_host_invoker_enforced": False,
            "final_execution_acknowledged": False,
            "one_shot_engineering_invocation_permitted": False,
            "execution_lease_materialized": False,
            "authorization_consumed": False,
            "runtime_execution_started": False,
            "runtime_execution_performed": False,
            "image_inspection_performed": False,
            "invocation_command_materialized": False,
            "docker_run_performed": False,
            "local_compute_execution_open": False,
        }
        for field_name, expected in exact.items():
            if getattr(self, field_name) != expected:
                raise PersistentEvidenceChainV2Error(
                    f"persistent evidence gates differ: {field_name}"
                )


@dataclass(frozen=True)
class PersistentEvidenceChainV2:
    """Canonical authoring record for the complete persistent chain."""

    schema_version: int
    chain_id: str
    status: str
    recorded_at_utc: str
    post_merge_validation_receipt_sha256: str
    source: PersistentEvidenceChainV2Source
    contract: PersistentEvidenceChainV2Contract
    gates: PersistentEvidenceChainV2Gates
    next_slice: str
    post_merge_next_slice: str
    chain_sha256: str

    def require(self) -> None:
        exact: Mapping[str, object] = {
            "schema_version": 2,
            "chain_id": PERSISTENT_EVIDENCE_CHAIN_V2_ID,
            "status": PERSISTENT_EVIDENCE_CHAIN_V2_STATUS,
            "next_slice": "QW-LC4-E-persistent-evidence-chain-v2-commit",
            "post_merge_next_slice": (
                "QW-LC4-E-persistent-evidence-chain-v2-implementation"
            ),
        }
        for field_name, expected in exact.items():
            if getattr(self, field_name) != expected:
                raise PersistentEvidenceChainV2Error(
                    f"persistent evidence chain differs: {field_name}"
                )
        _require_utc(self.recorded_at_utc, "recorded_at_utc")
        _require_sha256(
            self.post_merge_validation_receipt_sha256,
            "post_merge_validation_receipt_sha256",
        )
        self.source.require()
        self.contract.require()
        self.gates.require()
        _require_sha256(self.chain_sha256, "chain_sha256")
        if self.chain_sha256 != sha256_object(self._payload_without_digest()):
            raise PersistentEvidenceChainV2Error(
                "persistent evidence chain digest differs"
            )

    def _payload_without_digest(self) -> Mapping[str, object]:
        payload = asdict(self)
        payload.pop("chain_sha256")
        return cast(Mapping[str, object], payload)

    def canonical_json(self) -> str:
        return canonical_json(self)


@dataclass(frozen=True)
class PersistentExecutionLeaseV2:
    """Pure prospective representation of the future persistent lease v2."""

    schema_version: int
    lease_id: str
    status: str
    claimed_at_utc: str
    operator_acknowledgement: str
    execution_commit: str
    persistent_evidence_chain_id: str
    persistent_evidence_chain_sha256: str
    invocation_authorization_id: str
    invocation_authorization_sha256: str
    invocation_authorization_merge_commit: str
    execution_authorization_id: str
    execution_authorization_sha256: str
    execution_authorization_merge_commit: str
    preexecution_verification_id: str
    preexecution_verification_sha256: str
    preexecution_verification_merge_commit: str
    runtime_operation_id: str
    runtime_operation_sha256: str
    runtime_operation_merge_commit: str
    corrected_runtime_operation_module_sha256: str
    identity_repair_id: str
    identity_repair_sha256: str
    identity_repair_merge_commit: str
    image_repo_digest: str
    torch2pc_commit: str
    output_root: str
    execution_lease_v2_relative: str
    durable_host_outcome_relative: str
    output_root_absent_at_claim: bool
    execution_lease_absent_at_claim: bool
    durable_outcome_absent_at_claim: bool
    invocation_count: int
    authorization_consumed: bool
    runtime_execution_permitted: bool
    lease_bound_host_invoker_capability_required: bool
    durable_terminal_outcome_required: bool
    retry_permitted: bool
    runtime_execution_started: bool
    runtime_execution_performed: bool
    lease_sha256: str

    def require(self, chain: PersistentEvidenceChainV2) -> None:
        chain.require()
        exact: Mapping[str, object] = {
            "schema_version": 2,
            "lease_id": PERSISTENT_EXECUTION_LEASE_V2_ID,
            "status": PERSISTENT_EXECUTION_LEASE_V2_STATUS,
            "operator_acknowledgement": (
                PERSISTENT_LEASE_V2_OPERATOR_ACKNOWLEDGEMENT
            ),
            "persistent_evidence_chain_id": chain.chain_id,
            "persistent_evidence_chain_sha256": chain.chain_sha256,
            "invocation_authorization_id": chain.source.invocation_authorization_id,
            "invocation_authorization_sha256": (
                chain.source.invocation_authorization_sha256
            ),
            "invocation_authorization_merge_commit": (
                chain.source.invocation_authorization_merge_commit
            ),
            "execution_authorization_id": chain.source.execution_authorization_id,
            "execution_authorization_sha256": (
                chain.source.execution_authorization_sha256
            ),
            "execution_authorization_merge_commit": (
                chain.source.execution_authorization_merge_commit
            ),
            "preexecution_verification_id": chain.source.preexecution_verification_id,
            "preexecution_verification_sha256": (
                chain.source.preexecution_verification_sha256
            ),
            "preexecution_verification_merge_commit": (
                chain.source.preexecution_verification_merge_commit
            ),
            "runtime_operation_id": chain.source.runtime_operation_id,
            "runtime_operation_sha256": chain.source.runtime_operation_sha256,
            "runtime_operation_merge_commit": (
                chain.source.runtime_operation_merge_commit
            ),
            "corrected_runtime_operation_module_sha256": (
                chain.source.corrected_runtime_operation_module_sha256
            ),
            "identity_repair_id": chain.source.identity_repair_id,
            "identity_repair_sha256": chain.source.identity_repair_sha256,
            "identity_repair_merge_commit": (
                chain.source.identity_repair_merge_commit
            ),
            "image_repo_digest": chain.source.image_repo_digest,
            "torch2pc_commit": chain.source.torch2pc_commit,
            "output_root": chain.source.output_root,
            "execution_lease_v2_relative": (
                chain.source.execution_lease_v2_relative
            ),
            "durable_host_outcome_relative": (
                chain.source.durable_host_outcome_relative
            ),
            "invocation_count": 1,
            "authorization_consumed": True,
            "runtime_execution_permitted": True,
            "lease_bound_host_invoker_capability_required": True,
            "durable_terminal_outcome_required": True,
            "retry_permitted": False,
            "runtime_execution_started": False,
            "runtime_execution_performed": False,
        }
        for field_name, expected in exact.items():
            if getattr(self, field_name) != expected:
                raise PersistentEvidenceChainV2Error(
                    f"persistent lease v2 differs: {field_name}"
                )
        _require_utc(self.claimed_at_utc, "claimed_at_utc")
        _require_commit(self.execution_commit, "execution_commit")
        if not self.output_root_absent_at_claim:
            raise PersistentEvidenceChainV2Error(
                "output root existed at persistent lease claim"
            )
        if not self.execution_lease_absent_at_claim:
            raise PersistentEvidenceChainV2Error(
                "persistent lease existed at claim"
            )
        if not self.durable_outcome_absent_at_claim:
            raise PersistentEvidenceChainV2Error(
                "durable host outcome existed at claim"
            )
        _require_sha256(self.lease_sha256, "lease_sha256")
        if self.lease_sha256 != sha256_object(self._payload_without_digest()):
            raise PersistentEvidenceChainV2Error(
                "persistent lease v2 digest differs"
            )

    def _payload_without_digest(self) -> Mapping[str, object]:
        payload = asdict(self)
        payload.pop("lease_sha256")
        return cast(Mapping[str, object], payload)

    def canonical_json(self) -> str:
        return canonical_json(self)


@dataclass(frozen=True)
class OutputSnapshot:
    """Canonical before/after observation of the authorized output location."""

    present: bool
    tree_sha256: str
    file_count: int
    byte_count: int
    staging_count: int

    def require(self) -> None:
        _require_sha256(self.tree_sha256, "tree_sha256")
        if min(self.file_count, self.byte_count, self.staging_count) < 0:
            raise PersistentEvidenceChainV2Error(
                "output snapshot contains a negative count"
            )
        if not self.present and (self.file_count != 0 or self.byte_count != 0):
            raise PersistentEvidenceChainV2Error(
                "absent output snapshot contains files or bytes"
            )


@dataclass(frozen=True)
class DurableHostOutcomeReceipt:
    """Pure canonical terminal receipt required after a lease v2 claim."""

    schema_version: int
    receipt_id: str
    persistent_evidence_chain_sha256: str
    lease_id: str
    lease_sha256: str
    execution_commit: str
    started_at_utc: str
    ended_at_utc: str
    termination_class: str
    return_code: int | None
    child_spawn_count: int
    command_sha256: str | None
    image_inspection_sha256: str | None
    stdout_sha256: str
    stderr_sha256: str
    stdout_total_bytes: int
    stderr_total_bytes: int
    stdout_captured_bytes: int
    stderr_captured_bytes: int
    stdout_truncated: bool
    stderr_truncated: bool
    output_before: OutputSnapshot
    output_after: OutputSnapshot
    lease_present_before: bool
    lease_present_after: bool
    automatic_retry_performed: bool
    retry_permitted: bool
    durable_receipt_required: bool
    receipt_sha256: str

    def require(
        self,
        chain: PersistentEvidenceChainV2,
        lease: PersistentExecutionLeaseV2,
    ) -> None:
        chain.require()
        lease.require(chain)
        exact: Mapping[str, object] = {
            "schema_version": 1,
            "receipt_id": DURABLE_HOST_OUTCOME_RECEIPT_ID,
            "persistent_evidence_chain_sha256": chain.chain_sha256,
            "lease_id": lease.lease_id,
            "lease_sha256": lease.lease_sha256,
            "execution_commit": lease.execution_commit,
            "lease_present_before": True,
            "lease_present_after": True,
            "automatic_retry_performed": False,
            "retry_permitted": False,
            "durable_receipt_required": True,
        }
        for field_name, expected in exact.items():
            if getattr(self, field_name) != expected:
                raise PersistentEvidenceChainV2Error(
                    f"durable host outcome differs: {field_name}"
                )
        started = _require_utc(self.started_at_utc, "started_at_utc")
        ended = _require_utc(self.ended_at_utc, "ended_at_utc")
        if ended < started:
            raise PersistentEvidenceChainV2Error(
                "durable host outcome ends before it starts"
            )
        _require_commit(self.execution_commit, "execution_commit")
        if self.termination_class not in _ALLOWED_TERMINATION_CLASSES:
            raise PersistentEvidenceChainV2Error(
                "durable host outcome termination class differs"
            )
        if self.child_spawn_count not in {0, 1}:
            raise PersistentEvidenceChainV2Error(
                "durable host outcome child count differs"
            )
        no_child = {"prelaunch_rejected", "spawn_failed"}
        if self.termination_class in no_child:
            if self.child_spawn_count != 0 or self.return_code is not None:
                raise PersistentEvidenceChainV2Error(
                    "pre-spawn outcome contains a child terminal status"
                )
        elif self.child_spawn_count != 1:
            raise PersistentEvidenceChainV2Error(
                "post-spawn outcome has no single child"
            )
        if self.termination_class == "success" and self.return_code != 0:
            raise PersistentEvidenceChainV2Error(
                "successful host outcome has a nonzero return code"
            )
        if (
            self.termination_class == "nonzero_return_code"
            and (self.return_code is None or self.return_code <= 0)
        ):
            raise PersistentEvidenceChainV2Error(
                "nonzero-return outcome lacks a positive return code"
            )
        if (
            self.termination_class == "child_signal"
            and (self.return_code is None or self.return_code >= 0)
        ):
            raise PersistentEvidenceChainV2Error(
                "child-signal outcome lacks a negative return code"
            )
        for optional_digest, field_name in (
            (self.command_sha256, "command_sha256"),
            (self.image_inspection_sha256, "image_inspection_sha256"),
        ):
            if optional_digest is not None:
                _require_sha256(optional_digest, field_name)
        _require_sha256(self.stdout_sha256, "stdout_sha256")
        _require_sha256(self.stderr_sha256, "stderr_sha256")
        stream_counts = (
            (
                self.stdout_total_bytes,
                self.stdout_captured_bytes,
                self.stdout_truncated,
                "stdout",
            ),
            (
                self.stderr_total_bytes,
                self.stderr_captured_bytes,
                self.stderr_truncated,
                "stderr",
            ),
        )
        for total_bytes, captured_bytes, truncated, stream_name in stream_counts:
            if total_bytes < 0 or captured_bytes < 0:
                raise PersistentEvidenceChainV2Error(
                    f"{stream_name} byte count is negative"
                )
            if captured_bytes > total_bytes:
                raise PersistentEvidenceChainV2Error(
                    f"{stream_name} captured bytes exceed total bytes"
                )
            if truncated != (captured_bytes < total_bytes):
                raise PersistentEvidenceChainV2Error(
                    f"{stream_name} truncation flag differs"
                )
        self.output_before.require()
        self.output_after.require()
        _require_sha256(self.receipt_sha256, "receipt_sha256")
        if self.receipt_sha256 != sha256_object(self._payload_without_digest()):
            raise PersistentEvidenceChainV2Error(
                "durable host outcome receipt digest differs"
            )

    def _payload_without_digest(self) -> Mapping[str, object]:
        payload = asdict(self)
        payload.pop("receipt_sha256")
        return cast(Mapping[str, object], payload)

    def canonical_json(self) -> str:
        return canonical_json(self)


def _build_source() -> PersistentEvidenceChainV2Source:
    return PersistentEvidenceChainV2Source(
        authoring_base_commit=AUTHORING_BASE_COMMIT,
        invocation_authorization_id=INVOCATION_AUTHORIZATION_ID,
        invocation_authorization_sha256=INVOCATION_AUTHORIZATION_SHA256,
        invocation_authorization_file_sha256=(
            INVOCATION_AUTHORIZATION_FILE_SHA256
        ),
        invocation_authorization_merge_commit=(
            INVOCATION_AUTHORIZATION_MERGE_COMMIT
        ),
        execution_authorization_id=EXECUTION_AUTHORIZATION_ID,
        execution_authorization_sha256=EXECUTION_AUTHORIZATION_SHA256,
        execution_authorization_file_sha256=(
            EXECUTION_AUTHORIZATION_FILE_SHA256
        ),
        execution_authorization_merge_commit=(
            EXECUTION_AUTHORIZATION_MERGE_COMMIT
        ),
        preexecution_verification_id=PREEXECUTION_VERIFICATION_ID,
        preexecution_verification_sha256=PREEXECUTION_VERIFICATION_SHA256,
        preexecution_verification_file_sha256=(
            PREEXECUTION_VERIFICATION_FILE_SHA256
        ),
        preexecution_verification_merge_commit=(
            PREEXECUTION_VERIFICATION_MERGE_COMMIT
        ),
        runtime_operation_id=RUNTIME_OPERATION_ID,
        runtime_operation_sha256=RUNTIME_OPERATION_SHA256,
        runtime_operation_file_sha256=RUNTIME_OPERATION_FILE_SHA256,
        runtime_operation_merge_commit=RUNTIME_OPERATION_MERGE_COMMIT,
        corrected_runtime_operation_module_sha256=(
            CORRECTED_RUNTIME_OPERATION_MODULE_SHA256
        ),
        identity_repair_id=IDENTITY_REPAIR_ID,
        identity_repair_sha256=IDENTITY_REPAIR_SHA256,
        identity_repair_file_sha256=IDENTITY_REPAIR_FILE_SHA256,
        identity_repair_merge_commit=IDENTITY_REPAIR_MERGE_COMMIT,
        image_repo_digest=IMAGE_REPO_DIGEST,
        torch2pc_commit=TORCH2PC_COMMIT,
        output_root=AUTHORIZED_OUTPUT_ROOT,
        execution_lease_v2_relative=EXECUTION_LEASE_V2_RELATIVE.as_posix(),
        durable_host_outcome_relative=DURABLE_HOST_OUTCOME_RELATIVE.as_posix(),
        invocation_count=INVOCATION_COUNT,
    )


def _build_contract() -> PersistentEvidenceChainV2Contract:
    return PersistentEvidenceChainV2Contract(
        persistent_lease_v2_required=True,
        complete_identity_chain_required=True,
        claimed_at_utc_required=True,
        invocation_count_required=1,
        exclusive_atomic_lease_claim_required=True,
        lease_persists_after_terminal_failure=True,
        lease_bound_host_invoker_capability_required=True,
        direct_lower_level_invocation_forbidden=True,
        durable_terminal_outcome_required=True,
        outcome_required_after_lease_claim=True,
        outcome_required_for_prelaunch_failure=True,
        outcome_required_for_spawn_failure=True,
        outcome_required_for_nonzero_return=True,
        outcome_required_for_timeout_or_signal=True,
        outcome_start_end_utc_required=True,
        outcome_return_code_required_when_available=True,
        stdout_stderr_sha256_required=True,
        output_before_after_snapshots_required=True,
        automatic_retry_forbidden=True,
        receipt_atomic_exclusive_write_required=True,
        authoring_effects_forbidden=True,
    )


def _build_gates() -> PersistentEvidenceChainV2Gates:
    return PersistentEvidenceChainV2Gates(
        post_merge_validation_receipt_present=True,
        runtime_operation_identity_repair_merged=True,
        latest_authorization_bound_in_lease_template=True,
        durable_negative_host_outcome_defined=True,
        persistent_lease_v2_implementation_present=False,
        durable_outcome_writer_implemented=False,
        lease_bound_host_invoker_enforced=False,
        final_execution_acknowledged=False,
        one_shot_engineering_invocation_permitted=False,
        execution_lease_materialized=False,
        authorization_consumed=False,
        runtime_execution_started=False,
        runtime_execution_performed=False,
        image_inspection_performed=False,
        invocation_command_materialized=False,
        docker_run_performed=False,
        local_compute_execution_open=False,
    )


def build_persistent_execution_lease_v2(
    chain: PersistentEvidenceChainV2,
    *,
    claimed_at_utc: str,
    execution_commit: str,
    operator_acknowledgement: str,
    output_root_absent_at_claim: bool,
    execution_lease_absent_at_claim: bool,
    durable_outcome_absent_at_claim: bool,
) -> PersistentExecutionLeaseV2:
    """Build a prospective lease v2 in memory without writing it."""

    chain.require()
    payload: dict[str, object] = {
        "schema_version": 2,
        "lease_id": PERSISTENT_EXECUTION_LEASE_V2_ID,
        "status": PERSISTENT_EXECUTION_LEASE_V2_STATUS,
        "claimed_at_utc": claimed_at_utc,
        "operator_acknowledgement": operator_acknowledgement,
        "execution_commit": execution_commit,
        "persistent_evidence_chain_id": chain.chain_id,
        "persistent_evidence_chain_sha256": chain.chain_sha256,
        "invocation_authorization_id": chain.source.invocation_authorization_id,
        "invocation_authorization_sha256": (
            chain.source.invocation_authorization_sha256
        ),
        "invocation_authorization_merge_commit": (
            chain.source.invocation_authorization_merge_commit
        ),
        "execution_authorization_id": chain.source.execution_authorization_id,
        "execution_authorization_sha256": (
            chain.source.execution_authorization_sha256
        ),
        "execution_authorization_merge_commit": (
            chain.source.execution_authorization_merge_commit
        ),
        "preexecution_verification_id": chain.source.preexecution_verification_id,
        "preexecution_verification_sha256": (
            chain.source.preexecution_verification_sha256
        ),
        "preexecution_verification_merge_commit": (
            chain.source.preexecution_verification_merge_commit
        ),
        "runtime_operation_id": chain.source.runtime_operation_id,
        "runtime_operation_sha256": chain.source.runtime_operation_sha256,
        "runtime_operation_merge_commit": (
            chain.source.runtime_operation_merge_commit
        ),
        "corrected_runtime_operation_module_sha256": (
            chain.source.corrected_runtime_operation_module_sha256
        ),
        "identity_repair_id": chain.source.identity_repair_id,
        "identity_repair_sha256": chain.source.identity_repair_sha256,
        "identity_repair_merge_commit": chain.source.identity_repair_merge_commit,
        "image_repo_digest": chain.source.image_repo_digest,
        "torch2pc_commit": chain.source.torch2pc_commit,
        "output_root": chain.source.output_root,
        "execution_lease_v2_relative": chain.source.execution_lease_v2_relative,
        "durable_host_outcome_relative": (
            chain.source.durable_host_outcome_relative
        ),
        "output_root_absent_at_claim": output_root_absent_at_claim,
        "execution_lease_absent_at_claim": execution_lease_absent_at_claim,
        "durable_outcome_absent_at_claim": durable_outcome_absent_at_claim,
        "invocation_count": 1,
        "authorization_consumed": True,
        "runtime_execution_permitted": True,
        "lease_bound_host_invoker_capability_required": True,
        "durable_terminal_outcome_required": True,
        "retry_permitted": False,
        "runtime_execution_started": False,
        "runtime_execution_performed": False,
    }
    lease = PersistentExecutionLeaseV2(
        **cast(Any, payload),
        lease_sha256=sha256_object(payload),
    )
    lease.require(chain)
    return lease


def build_durable_host_outcome_receipt(
    chain: PersistentEvidenceChainV2,
    lease: PersistentExecutionLeaseV2,
    *,
    started_at_utc: str,
    ended_at_utc: str,
    termination_class: str,
    return_code: int | None,
    child_spawn_count: int,
    command_sha256: str | None,
    image_inspection_sha256: str | None,
    stdout_sha256: str,
    stderr_sha256: str,
    stdout_total_bytes: int,
    stderr_total_bytes: int,
    stdout_captured_bytes: int,
    stderr_captured_bytes: int,
    stdout_truncated: bool,
    stderr_truncated: bool,
    output_before: OutputSnapshot,
    output_after: OutputSnapshot,
) -> DurableHostOutcomeReceipt:
    """Build a canonical terminal receipt in memory without persisting it."""

    chain.require()
    lease.require(chain)
    payload: dict[str, object] = {
        "schema_version": 1,
        "receipt_id": DURABLE_HOST_OUTCOME_RECEIPT_ID,
        "persistent_evidence_chain_sha256": chain.chain_sha256,
        "lease_id": lease.lease_id,
        "lease_sha256": lease.lease_sha256,
        "execution_commit": lease.execution_commit,
        "started_at_utc": started_at_utc,
        "ended_at_utc": ended_at_utc,
        "termination_class": termination_class,
        "return_code": return_code,
        "child_spawn_count": child_spawn_count,
        "command_sha256": command_sha256,
        "image_inspection_sha256": image_inspection_sha256,
        "stdout_sha256": stdout_sha256,
        "stderr_sha256": stderr_sha256,
        "stdout_total_bytes": stdout_total_bytes,
        "stderr_total_bytes": stderr_total_bytes,
        "stdout_captured_bytes": stdout_captured_bytes,
        "stderr_captured_bytes": stderr_captured_bytes,
        "stdout_truncated": stdout_truncated,
        "stderr_truncated": stderr_truncated,
        "output_before": asdict(output_before),
        "output_after": asdict(output_after),
        "lease_present_before": True,
        "lease_present_after": True,
        "automatic_retry_performed": False,
        "retry_permitted": False,
        "durable_receipt_required": True,
    }
    receipt = DurableHostOutcomeReceipt(
        schema_version=1,
        receipt_id=DURABLE_HOST_OUTCOME_RECEIPT_ID,
        persistent_evidence_chain_sha256=chain.chain_sha256,
        lease_id=lease.lease_id,
        lease_sha256=lease.lease_sha256,
        execution_commit=lease.execution_commit,
        started_at_utc=started_at_utc,
        ended_at_utc=ended_at_utc,
        termination_class=termination_class,
        return_code=return_code,
        child_spawn_count=child_spawn_count,
        command_sha256=command_sha256,
        image_inspection_sha256=image_inspection_sha256,
        stdout_sha256=stdout_sha256,
        stderr_sha256=stderr_sha256,
        stdout_total_bytes=stdout_total_bytes,
        stderr_total_bytes=stderr_total_bytes,
        stdout_captured_bytes=stdout_captured_bytes,
        stderr_captured_bytes=stderr_captured_bytes,
        stdout_truncated=stdout_truncated,
        stderr_truncated=stderr_truncated,
        output_before=output_before,
        output_after=output_after,
        lease_present_before=True,
        lease_present_after=True,
        automatic_retry_performed=False,
        retry_permitted=False,
        durable_receipt_required=True,
        receipt_sha256=sha256_object(payload),
    )
    receipt.require(chain, lease)
    return receipt


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise PersistentEvidenceChainV2Error(
            f"required JSON file is absent or non-regular: {path}"
        )
    try:
        payload = json.loads(path.read_text(encoding="utf-8", errors="strict"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PersistentEvidenceChainV2Error(
            f"required JSON file is invalid: {path}"
        ) from exc
    if not isinstance(payload, dict):
        raise PersistentEvidenceChainV2Error(f"JSON root differs: {path}")
    return cast(dict[str, Any], payload)


def _load_registry(path: Path) -> dict[str, str]:
    if not path.is_file() or path.is_symlink():
        raise PersistentEvidenceChainV2Error(
            f"required registry is absent or non-regular: {path}"
        )
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="strict").splitlines():
        if not line or "  " not in line:
            raise PersistentEvidenceChainV2Error(
                f"registry line is invalid: {path}"
            )
        digest, relative = line.split("  ", 1)
        value = "sha256:" + digest
        _require_sha256(value, f"registry digest for {relative}")
        if relative in result:
            raise PersistentEvidenceChainV2Error(
                f"registry path is duplicated: {relative}"
            )
        result[relative] = value
    return result


def load_post_merge_validation_receipt(
    path: Path,
) -> PostMergeValidationReceipt:
    payload = _load_json(path)
    receipt = PostMergeValidationReceipt(**cast(Any, payload))
    receipt.require()
    if path.read_text(encoding="utf-8") != receipt.canonical_json():
        raise PersistentEvidenceChainV2Error(
            "post-merge validation receipt serialization differs"
        )
    return receipt


def load_persistent_evidence_chain_v2(path: Path) -> PersistentEvidenceChainV2:
    payload = _load_json(path)
    payload["source"] = PersistentEvidenceChainV2Source(
        **cast(Any, payload["source"])
    )
    payload["contract"] = PersistentEvidenceChainV2Contract(
        **cast(Any, payload["contract"])
    )
    payload["gates"] = PersistentEvidenceChainV2Gates(
        **cast(Any, payload["gates"])
    )
    chain = PersistentEvidenceChainV2(**cast(Any, payload))
    chain.require()
    if path.read_text(encoding="utf-8") != chain.canonical_json():
        raise PersistentEvidenceChainV2Error(
            "persistent evidence chain serialization differs"
        )
    return chain


def verify_persistent_evidence_chain_v2(
    project_root: Path,
) -> PersistentEvidenceChainV2:
    """Verify the complete authoring package and preserve a closed boundary."""

    root = project_root.expanduser().resolve()
    package = root / PACKAGE_RELATIVE
    if not package.is_dir() or package.is_symlink():
        raise PersistentEvidenceChainV2Error(
            "persistent evidence package is absent or invalid"
        )
    observed_files = frozenset(path.name for path in package.iterdir())
    if observed_files != _EXPECTED_PACKAGE_FILES:
        raise PersistentEvidenceChainV2Error(
            "persistent evidence package files differ"
        )

    chain_path = root / CHAIN_RECORD_RELATIVE
    receipt_path = root / POST_MERGE_RECEIPT_RELATIVE
    chain = load_persistent_evidence_chain_v2(chain_path)
    receipt = load_post_merge_validation_receipt(receipt_path)
    if chain.post_merge_validation_receipt_sha256 != sha256_bytes(
        receipt_path.read_bytes()
    ):
        raise PersistentEvidenceChainV2Error(
            "post-merge validation file identity differs"
        )

    package_registry = _load_registry(root / REGISTRY_RELATIVE)
    expected_package_registry = {
        "chain.json": sha256_bytes(chain_path.read_bytes()),
        "post-merge-validation.json": sha256_bytes(receipt_path.read_bytes()),
        "source-SHA256SUMS": sha256_bytes(
            (root / SOURCE_REGISTRY_RELATIVE).read_bytes()
        ),
    }
    if package_registry != expected_package_registry:
        raise PersistentEvidenceChainV2Error(
            "persistent evidence package registry differs"
        )

    source_registry = _load_registry(root / SOURCE_REGISTRY_RELATIVE)
    if frozenset(source_registry) != _EXPECTED_SOURCE_PATHS:
        raise PersistentEvidenceChainV2Error(
            "persistent evidence source registry paths differ"
        )
    for relative, expected_digest in source_registry.items():
        target = root / relative
        if not target.is_file() or target.is_symlink():
            raise PersistentEvidenceChainV2Error(
                f"bound source is absent or non-regular: {relative}"
            )
        if sha256_bytes(target.read_bytes()) != expected_digest:
            raise PersistentEvidenceChainV2Error(
                f"bound source SHA-256 differs: {relative}"
            )

    _verify_upstream_records(root, chain)
    _verify_effect_free_authoring_ast(root)
    _require_repository_boundary_closed(root)
    receipt.require()
    chain.require()
    return chain


def _verify_upstream_records(
    root: Path,
    chain: PersistentEvidenceChainV2,
) -> None:
    checks: tuple[tuple[Path, Mapping[str, object]], ...] = (
        (
            INVOCATION_AUTHORIZATION_RECORD_RELATIVE,
            {
                "authorization_id": chain.source.invocation_authorization_id,
                "authorization_sha256": (
                    chain.source.invocation_authorization_sha256
                ),
            },
        ),
        (
            EXECUTION_AUTHORIZATION_RECORD_RELATIVE,
            {
                "authorization_id": chain.source.execution_authorization_id,
                "authorization_sha256": (
                    chain.source.execution_authorization_sha256
                ),
            },
        ),
        (
            PREEXECUTION_RECORD_RELATIVE,
            {
                "verification_id": chain.source.preexecution_verification_id,
                "verification_sha256": (
                    chain.source.preexecution_verification_sha256
                ),
            },
        ),
        (
            RUNTIME_OPERATION_RECORD_RELATIVE,
            {
                "operation_id": chain.source.runtime_operation_id,
                "operation_sha256": chain.source.runtime_operation_sha256,
            },
        ),
        (
            IDENTITY_REPAIR_RECORD_RELATIVE,
            {
                "repair_id": chain.source.identity_repair_id,
                "repair_sha256": chain.source.identity_repair_sha256,
            },
        ),
    )
    for relative, expected in checks:
        payload = _load_json(root / relative)
        for field_name, expected_value in expected.items():
            if payload.get(field_name) != expected_value:
                raise PersistentEvidenceChainV2Error(
                    f"upstream record identity differs: {relative}:{field_name}"
                )


def _verify_effect_free_authoring_ast(root: Path) -> None:
    tree = ast.parse(
        (root / MODULE_RELATIVE).read_text(
            encoding="utf-8",
            errors="strict",
        )
    )
    forbidden_imports = {"subprocess", "docker"}
    forbidden_calls = {
        "invoke_one_shot_host_runtime",
        "execute_one_shot_engineering_invocation_runtime_operation",
        "claim_execution_lease",
        "materialize_execution_lease",
        "Popen",
        "run",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".", 1)[0] in forbidden_imports:
                    raise PersistentEvidenceChainV2Error(
                        "authoring module imports an execution dependency"
                    )
        if (
            isinstance(node, ast.ImportFrom)
            and node.module is not None
            and node.module.split(".", 1)[0] in forbidden_imports
        ):
            raise PersistentEvidenceChainV2Error(
                "authoring module imports an execution dependency"
            )
        if isinstance(node, ast.Call):
            name = ""
            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr
            if name in forbidden_calls:
                raise PersistentEvidenceChainV2Error(
                    f"authoring module contains forbidden call: {name}"
                )


def _require_repository_boundary_closed(root: Path) -> None:
    output_root = root / AUTHORIZED_OUTPUT_ROOT
    lease_v1 = root / (AUTHORIZED_OUTPUT_ROOT + ".execution-lease.json")
    lease_v2 = root / EXECUTION_LEASE_V2_RELATIVE
    outcome = root / DURABLE_HOST_OUTCOME_RELATIVE
    for path, label in (
        (output_root, "runtime output"),
        (lease_v1, "execution lease v1"),
        (lease_v2, "execution lease v2"),
        (outcome, "durable host outcome"),
    ):
        if path.exists() or path.is_symlink():
            raise PersistentEvidenceChainV2Error(
                f"repository {label} already exists"
            )
    staging = tuple(
        output_root.parent.glob(f".{output_root.name}.staging-*")
    )
    if staging:
        raise PersistentEvidenceChainV2Error(
            "repository runtime staging already exists"
        )


def build_frozen_chain_record(
    *,
    recorded_at_utc: str,
    post_merge_validation_receipt_sha256: str,
) -> PersistentEvidenceChainV2:
    """Build the canonical authoring record for package generation."""

    payload: dict[str, object] = {
        "schema_version": 2,
        "chain_id": PERSISTENT_EVIDENCE_CHAIN_V2_ID,
        "status": PERSISTENT_EVIDENCE_CHAIN_V2_STATUS,
        "recorded_at_utc": recorded_at_utc,
        "post_merge_validation_receipt_sha256": (
            post_merge_validation_receipt_sha256
        ),
        "source": asdict(_build_source()),
        "contract": asdict(_build_contract()),
        "gates": asdict(_build_gates()),
        "next_slice": "QW-LC4-E-persistent-evidence-chain-v2-commit",
        "post_merge_next_slice": (
            "QW-LC4-E-persistent-evidence-chain-v2-implementation"
        ),
    }
    chain = PersistentEvidenceChainV2(
        schema_version=2,
        chain_id=PERSISTENT_EVIDENCE_CHAIN_V2_ID,
        status=PERSISTENT_EVIDENCE_CHAIN_V2_STATUS,
        recorded_at_utc=recorded_at_utc,
        post_merge_validation_receipt_sha256=(
            post_merge_validation_receipt_sha256
        ),
        source=_build_source(),
        contract=_build_contract(),
        gates=_build_gates(),
        next_slice="QW-LC4-E-persistent-evidence-chain-v2-commit",
        post_merge_next_slice=(
            "QW-LC4-E-persistent-evidence-chain-v2-implementation"
        ),
        chain_sha256=sha256_object(payload),
    )
    chain.require()
    return chain


def build_post_merge_validation_receipt(
    *,
    recorded_at_utc: str,
) -> PostMergeValidationReceipt:
    """Build the canonical PR 143 validation receipt for package generation."""

    payload: dict[str, object] = {
        "schema_version": 1,
        "receipt_id": POST_MERGE_VALIDATION_RECEIPT_ID,
        "recorded_at_utc": recorded_at_utc,
        "pr_number": IDENTITY_REPAIR_PR_NUMBER,
        "pr_head_commit": IDENTITY_REPAIR_HEAD_COMMIT,
        "pr_base_commit": IDENTITY_REPAIR_PARENT_COMMIT,
        "merge_commit": IDENTITY_REPAIR_MERGE_COMMIT,
        "merged_at_utc": IDENTITY_REPAIR_MERGED_AT_UTC,
        "merge_parent_1": IDENTITY_REPAIR_PARENT_COMMIT,
        "merge_parent_2": IDENTITY_REPAIR_HEAD_COMMIT,
        "commit_count": 1,
        "file_count": 18,
        "focused_passed": 24,
        "targeted_passed": 201,
        "full_passed": 1248,
        "warning_count": 14,
        "required_ci_checks_passed": True,
        "package_registries_passed": True,
        "ruff_passed": True,
        "mypy_passed": True,
        "ru_mkdocs_passed": True,
        "en_mkdocs_passed": True,
        "torch2pc_identity_passed": True,
        "runtime_boundary_closed": True,
    }
    receipt = PostMergeValidationReceipt(
        **cast(Any, payload),
        receipt_sha256=sha256_object(payload),
    )
    receipt.require()
    return receipt
