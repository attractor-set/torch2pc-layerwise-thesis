"""Effect-free pre-execution verification contract for QW-LC4-E.

The module binds the independently merged execution authorization to the exact
bounded host runtime invoker that performs the dynamic checks in the same
process as the single future child spawn.  Verification in this module is
static and read-only: it does not inspect a Docker image, materialize an argv,
spawn a process, create or claim an execution lease, execute the backend, write
runtime output, access a dataset, or publish evidence.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final, cast

from torch2pc_thesis.stage3b_qwake_lc4_engineering_invocation_execution_authorization import (
    EXECUTION_AUTHORIZATION_ID,
    verify_engineering_invocation_execution_authorization,
)
from torch2pc_thesis.stage3b_qwake_lc4_engineering_invocation_operation import (
    IMAGE_REPO_DIGEST,
    INVOCATION_OPERATION_ID,
    REQUIRED_HOST_RESOURCE_KEYS,
)
from torch2pc_thesis.stage3b_qwake_lc4_host_runtime_invoker import (
    HOST_PRELAUNCH_SEQUENCE,
    HOST_RUNTIME_INVOKER_CONTRACT_ID,
)
from torch2pc_thesis.stage3b_qwake_lc4_host_runtime_invoker_implementation import (
    HOST_RUNTIME_INVOKER_IMPLEMENTATION_ID,
    build_host_runtime_invoker_implementation_state,
)
from torch2pc_thesis.stage3b_qwake_lc4_invocation_authorization import (
    AUTHORIZED_OUTPUT_ROOT,
    EXECUTION_LEASE_RELATIVE,
    INVOCATION_AUTHORIZATION_ID,
    INVOCATION_OPERATOR_ACKNOWLEDGEMENT,
    LEASE_OPERATOR_ACKNOWLEDGEMENT,
)

PREEXECUTION_VERIFICATION_ID: Final = (
    "stage3b-qwake-lc4-e-one-shot-engineering-invocation-"
    "preexecution-verification-v1"
)
PREEXECUTION_VERIFICATION_STATUS: Final = (
    "one_shot_engineering_invocation_preexecution_contract_frozen_runtime_closed"
)
PREEXECUTION_VERIFICATION_ACKNOWLEDGEMENT: Final = (
    "FREEZE_QWAKE_LC4_PREEXECUTION_VERIFICATION_FROM_MERGED_"
    "EXECUTION_AUTHORIZATION"
)
PREEXECUTION_BASE_COMMIT: Final = (
    "49c4b97e93b47cefbf35576736927ece02c9402b"
)
AUTHORIZATION_HEAD_COMMIT: Final = (
    "9b7074cbb602fff77ad6770ea4978d3bdc73003b"
)
AUTHORIZATION_PARENT_COMMIT: Final = (
    "b0f6729e8fd1cb1aa172eef488dc56e36b335173"
)
AUTHORIZATION_MERGED_AT_UTC: Final = "2026-07-29T21:46:26Z"
AUTHORIZATION_PR_NUMBER: Final = 140
EXECUTION_AUTHORIZATION_SHA256: Final = (
    "sha256:ff136538faee0d7952dc444e521d7ec760c7d54cd38406cb9b19ff1e00d9437b"
)
EXECUTION_AUTHORIZATION_FILE_SHA256: Final = (
    "sha256:11f12d2c2723902716ca9e7209f408b9edae2f793ceb098c8adeb06fee8c0c72"
)
EXECUTION_AUTHORIZATION_REGISTRY_SHA256: Final = (
    "sha256:4ab39c084f330d8679495f4aefdcc11005fc8d83a21b2a5c78cee80aeda562b5"
)
EXECUTION_AUTHORIZATION_MODULE_SHA256: Final = (
    "sha256:2769982c9f36108f1cb70b43ab7cee9eea5a63ac870f5fb1d4d938800ee837f5"
)
EXECUTION_AUTHORIZATION_VERIFIER_SHA256: Final = (
    "sha256:3a4f8f920b1d28036c9f1d690b98f492437de1c2e9ce5106baf102bd05f053bd"
)
EXECUTION_AUTHORIZATION_TEST_SHA256: Final = (
    "sha256:c1b226bc97d4fcd3c5db30ee0c581581dc65da57924c61cb19e4d65daeb29b59"
)

HOST_RUNTIME_INVOKER_IMPLEMENTATION_STATE_SHA256: Final = (
    "sha256:1f5f31d4f220bbf074736f1de0b78a5dafa2849188ac337704d5cc704668fdf4"
)
HOST_RUNTIME_INVOKER_CONTRACT_SHA256: Final = (
    "sha256:607bf719d8a976569c50d7cfe8604ab341843dad00d3eef8784e1dc6cfd9b88d"
)
HOST_RUNTIME_INVOKER_MODULE_SHA256: Final = (
    "sha256:dc55bc711f6126eaf7fd231439a2149e991027a751e58d2c6d3450a9d5ae9b14"
)
HOST_RUNTIME_INVOKER_VERIFIER_SHA256: Final = (
    "sha256:eddc19915c3d258671c6a804b1f2a17cfdcecbea264295632cf7200de2742268"
)
HOST_RUNTIME_INVOKER_TEST_SHA256: Final = (
    "sha256:b7cd39f595d8c39a9f96dde342134240d0eb5a4b6a72fe85464d0ae52144ebac"
)
HOST_RUNTIME_INVOKER_RECORD_SHA256: Final = (
    "sha256:beb24e0fda734aa4a9a74e7887349944f27805817def0f07e33618f566e505e1"
)
HOST_RUNTIME_INVOKER_REGISTRY_SHA256: Final = (
    "sha256:d04ad77ad59ee289fab4ca0bf1a0a44009c47ecb8af058ccebf77b9fe58c173a"
)
TORCH2PC_COMMIT: Final = "b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4"
RUNTIME_ENTRYPOINT: Final = "invoke_one_shot_host_runtime"
IMAGE_INSPECTION_COUNT: Final = 2
INVOCATION_MATERIALIZATION_COUNT: Final = 2
RUNTIME_ENTRYPOINT_CALL_COUNT: Final = 1
SUBPROCESS_POPEN_CALL_LIMIT: Final = 1

PACKAGE_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-one-shot-engineering-invocation-"
    "preexecution-verification-v1"
)
RECORD_RELATIVE: Final = PACKAGE_RELATIVE / "verification.json"
REGISTRY_RELATIVE: Final = PACKAGE_RELATIVE / "SHA256SUMS"
AUTHORIZATION_RECORD_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-one-shot-engineering-invocation-"
    "execution-authorization-v1/authorization.json"
)
AUTHORIZATION_REGISTRY_RELATIVE: Final = AUTHORIZATION_RECORD_RELATIVE.with_name(
    "SHA256SUMS"
)
AUTHORIZATION_MODULE_RELATIVE: Final = Path(
    "src/torch2pc_thesis/"
    "stage3b_qwake_lc4_engineering_invocation_execution_authorization.py"
)
AUTHORIZATION_VERIFIER_RELATIVE: Final = Path(
    "scripts/verify_stage3b_qwake_lc4_engineering_invocation_"
    "execution_authorization.py"
)
AUTHORIZATION_TEST_RELATIVE: Final = Path(
    "tests/unit/test_stage3b_qwake_lc4_engineering_invocation_"
    "execution_authorization.py"
)
INVOKER_RECORD_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-implementation-v1/"
    "implementation.json"
)
INVOKER_REGISTRY_RELATIVE: Final = INVOKER_RECORD_RELATIVE.with_name(
    "SHA256SUMS"
)
INVOKER_MODULE_RELATIVE: Final = Path(
    "src/torch2pc_thesis/stage3b_qwake_lc4_host_runtime_invoker_implementation.py"
)
INVOKER_VERIFIER_RELATIVE: Final = Path(
    "scripts/verify_stage3b_qwake_lc4_host_runtime_invoker_implementation.py"
)
INVOKER_TEST_RELATIVE: Final = Path(
    "tests/unit/test_stage3b_qwake_lc4_host_runtime_invoker_implementation.py"
)

_EXPECTED_PACKAGE_FILES: Final = frozenset({"SHA256SUMS", "verification.json"})
_COMMIT_PATTERN: Final = re.compile(r"^[0-9a-f]{40}$")
_SHA256_PATTERN: Final = re.compile(r"^sha256:[0-9a-f]{64}$")

__all__ = [
    "PREEXECUTION_BASE_COMMIT",
    "PREEXECUTION_VERIFICATION_ID",
    "PREEXECUTION_VERIFICATION_STATUS",
    "OneShotEngineeringInvocationPreexecutionVerification",
    "PreexecutionVerificationContract",
    "PreexecutionVerificationGates",
    "PreexecutionVerificationSource",
    "QWakeLC4EngineeringInvocationPreexecutionVerificationError",
    "build_engineering_invocation_preexecution_verification",
    "canonical_json",
    "load_engineering_invocation_preexecution_verification",
    "sha256_object",
    "verify_engineering_invocation_preexecution_verification",
]


class QWakeLC4EngineeringInvocationPreexecutionVerificationError(RuntimeError):
    """Raised when the pre-execution contract cannot remain fail closed."""


def canonical_json(value: object) -> str:
    """Return canonical UTF-8 JSON with one terminal newline."""

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ) + "\n"


def sha256_object(value: object) -> str:
    """Hash canonical JSON without terminal formatting ambiguity."""

    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _require_sha256(value: str, field_name: str) -> None:
    if _SHA256_PATTERN.fullmatch(value) is None:
        raise QWakeLC4EngineeringInvocationPreexecutionVerificationError(
            f"{field_name} is not SHA-256"
        )


def _require_commit(value: str, field_name: str) -> None:
    if _COMMIT_PATTERN.fullmatch(value) is None:
        raise QWakeLC4EngineeringInvocationPreexecutionVerificationError(
            f"{field_name} is not a commit"
        )


def _require_utc(value: str, field_name: str) -> datetime:
    if not value.endswith("Z"):
        raise QWakeLC4EngineeringInvocationPreexecutionVerificationError(
            f"{field_name} is not UTC"
        )
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise QWakeLC4EngineeringInvocationPreexecutionVerificationError(
            f"{field_name} is not ISO-8601"
        ) from exc
    if parsed.tzinfo != UTC:
        raise QWakeLC4EngineeringInvocationPreexecutionVerificationError(
            f"{field_name} timezone differs"
        )
    return parsed


@dataclass(frozen=True)
class PreexecutionVerificationSource:
    """Exact merged authorization and inherited runtime identities."""

    preexecution_base_commit: str
    execution_authorization_id: str
    authorization_head_commit: str
    authorization_parent_commit: str
    authorization_merged_at_utc: str
    authorization_pr_number: int
    execution_authorization_sha256: str
    execution_authorization_file_sha256: str
    execution_authorization_registry_sha256: str
    execution_authorization_module_sha256: str
    execution_authorization_verifier_sha256: str
    execution_authorization_test_sha256: str
    invocation_operation_id: str
    invocation_authorization_id: str
    host_runtime_invoker_contract_id: str
    host_runtime_invoker_contract_sha256: str
    host_runtime_invoker_implementation_id: str
    host_runtime_invoker_implementation_state_sha256: str
    host_runtime_invoker_module_sha256: str
    host_runtime_invoker_verifier_sha256: str
    host_runtime_invoker_test_sha256: str
    host_runtime_invoker_record_sha256: str
    host_runtime_invoker_registry_sha256: str
    image_repo_digest: str
    torch2pc_commit: str
    output_root: str
    execution_lease_relative: str

    def require(self) -> None:
        exact: Mapping[str, object] = {
            "preexecution_base_commit": PREEXECUTION_BASE_COMMIT,
            "execution_authorization_id": EXECUTION_AUTHORIZATION_ID,
            "authorization_head_commit": AUTHORIZATION_HEAD_COMMIT,
            "authorization_parent_commit": AUTHORIZATION_PARENT_COMMIT,
            "authorization_merged_at_utc": AUTHORIZATION_MERGED_AT_UTC,
            "authorization_pr_number": AUTHORIZATION_PR_NUMBER,
            "execution_authorization_sha256": EXECUTION_AUTHORIZATION_SHA256,
            "execution_authorization_file_sha256": (
                EXECUTION_AUTHORIZATION_FILE_SHA256
            ),
            "execution_authorization_registry_sha256": (
                EXECUTION_AUTHORIZATION_REGISTRY_SHA256
            ),
            "execution_authorization_module_sha256": (
                EXECUTION_AUTHORIZATION_MODULE_SHA256
            ),
            "execution_authorization_verifier_sha256": (
                EXECUTION_AUTHORIZATION_VERIFIER_SHA256
            ),
            "execution_authorization_test_sha256": (
                EXECUTION_AUTHORIZATION_TEST_SHA256
            ),
            "invocation_operation_id": INVOCATION_OPERATION_ID,
            "invocation_authorization_id": INVOCATION_AUTHORIZATION_ID,
            "host_runtime_invoker_contract_id": (
                HOST_RUNTIME_INVOKER_CONTRACT_ID
            ),
            "host_runtime_invoker_contract_sha256": (
                HOST_RUNTIME_INVOKER_CONTRACT_SHA256
            ),
            "host_runtime_invoker_implementation_id": (
                HOST_RUNTIME_INVOKER_IMPLEMENTATION_ID
            ),
            "host_runtime_invoker_implementation_state_sha256": (
                HOST_RUNTIME_INVOKER_IMPLEMENTATION_STATE_SHA256
            ),
            "host_runtime_invoker_module_sha256": (
                HOST_RUNTIME_INVOKER_MODULE_SHA256
            ),
            "host_runtime_invoker_verifier_sha256": (
                HOST_RUNTIME_INVOKER_VERIFIER_SHA256
            ),
            "host_runtime_invoker_test_sha256": (
                HOST_RUNTIME_INVOKER_TEST_SHA256
            ),
            "host_runtime_invoker_record_sha256": (
                HOST_RUNTIME_INVOKER_RECORD_SHA256
            ),
            "host_runtime_invoker_registry_sha256": (
                HOST_RUNTIME_INVOKER_REGISTRY_SHA256
            ),
            "image_repo_digest": IMAGE_REPO_DIGEST,
            "torch2pc_commit": TORCH2PC_COMMIT,
            "output_root": str(AUTHORIZED_OUTPUT_ROOT),
            "execution_lease_relative": str(EXECUTION_LEASE_RELATIVE),
        }
        for field_name, expected in exact.items():
            if getattr(self, field_name) != expected:
                raise QWakeLC4EngineeringInvocationPreexecutionVerificationError(
                    f"pre-execution source differs: {field_name}"
                )
        for field_name in (
            "preexecution_base_commit",
            "authorization_head_commit",
            "authorization_parent_commit",
            "torch2pc_commit",
        ):
            _require_commit(str(getattr(self, field_name)), field_name)
        _require_utc(
            self.authorization_merged_at_utc,
            "authorization_merged_at_utc",
        )
        for field_name in (
            "execution_authorization_sha256",
            "execution_authorization_file_sha256",
            "execution_authorization_registry_sha256",
            "execution_authorization_module_sha256",
            "execution_authorization_verifier_sha256",
            "execution_authorization_test_sha256",
            "host_runtime_invoker_contract_sha256",
            "host_runtime_invoker_implementation_state_sha256",
            "host_runtime_invoker_module_sha256",
            "host_runtime_invoker_verifier_sha256",
            "host_runtime_invoker_test_sha256",
            "host_runtime_invoker_record_sha256",
            "host_runtime_invoker_registry_sha256",
        ):
            _require_sha256(str(getattr(self, field_name)), field_name)


@dataclass(frozen=True)
class PreexecutionVerificationContract:
    """Exact dynamic checks delegated to the frozen same-process invoker."""

    exact_merged_execution_authorization_required: bool
    exact_host_runtime_invoker_required: bool
    direct_runtime_entrypoint_required: str
    runtime_entrypoint_call_count: int
    preexecution_and_spawn_same_process_required: bool
    required_host_resource_keys: tuple[str, ...]
    exact_host_resources_required: bool
    exact_immutable_image_required: bool
    image_inspection_count_required: int
    invocation_materialization_count_required: int
    image_inspection_equality_required: bool
    canonical_argv_equality_required: bool
    authorization_unconsumed_required: bool
    execution_lease_absence_required: bool
    output_absence_required: bool
    runtime_staging_absence_required: bool
    invocation_operator_acknowledgement: str
    lease_operator_acknowledgement: str
    host_prelaunch_sequence: tuple[str, ...]
    subprocess_popen_call_limit: int
    shell_interpretation_forbidden: bool
    host_execution_lease_write_forbidden: bool
    command_persistence_forbidden: bool
    host_log_persistence_forbidden: bool
    automatic_retry_after_spawn_forbidden: bool
    verifier_image_inspection_call_count: int
    verifier_invocation_materialization_call_count: int
    verifier_process_spawn_call_count: int

    def require(self) -> None:
        required_true = (
            self.exact_merged_execution_authorization_required,
            self.exact_host_runtime_invoker_required,
            self.preexecution_and_spawn_same_process_required,
            self.exact_host_resources_required,
            self.exact_immutable_image_required,
            self.image_inspection_equality_required,
            self.canonical_argv_equality_required,
            self.authorization_unconsumed_required,
            self.execution_lease_absence_required,
            self.output_absence_required,
            self.runtime_staging_absence_required,
            self.shell_interpretation_forbidden,
            self.host_execution_lease_write_forbidden,
            self.command_persistence_forbidden,
            self.host_log_persistence_forbidden,
            self.automatic_retry_after_spawn_forbidden,
        )
        if not all(required_true):
            raise QWakeLC4EngineeringInvocationPreexecutionVerificationError(
                "required pre-execution contract gate is closed"
            )
        exact: Mapping[str, object] = {
            "direct_runtime_entrypoint_required": RUNTIME_ENTRYPOINT,
            "runtime_entrypoint_call_count": RUNTIME_ENTRYPOINT_CALL_COUNT,
            "required_host_resource_keys": REQUIRED_HOST_RESOURCE_KEYS,
            "image_inspection_count_required": IMAGE_INSPECTION_COUNT,
            "invocation_materialization_count_required": (
                INVOCATION_MATERIALIZATION_COUNT
            ),
            "invocation_operator_acknowledgement": (
                INVOCATION_OPERATOR_ACKNOWLEDGEMENT
            ),
            "lease_operator_acknowledgement": LEASE_OPERATOR_ACKNOWLEDGEMENT,
            "host_prelaunch_sequence": HOST_PRELAUNCH_SEQUENCE,
            "subprocess_popen_call_limit": SUBPROCESS_POPEN_CALL_LIMIT,
            "verifier_image_inspection_call_count": 0,
            "verifier_invocation_materialization_call_count": 0,
            "verifier_process_spawn_call_count": 0,
        }
        for field_name, expected in exact.items():
            if getattr(self, field_name) != expected:
                raise QWakeLC4EngineeringInvocationPreexecutionVerificationError(
                    f"pre-execution contract differs: {field_name}"
                )


@dataclass(frozen=True)
class PreexecutionVerificationGates:
    """Authoring-state gates; dynamic runtime identity remains unverified."""

    invocation_operation_complete: bool
    execution_authorization_complete: bool
    preexecution_verification_record_present: bool
    preexecution_verifier_implemented: bool
    preexecution_static_contract_verified: bool
    preexecution_verification_slice_open: bool
    preexecution_identity_verified: bool
    one_shot_engineering_invocation_execution_open: bool
    one_shot_engineering_invocation_runtime_operation_open: bool
    one_shot_engineering_invocation_permitted: bool
    one_shot_engineering_invocation_performed: bool
    branch_runtime_execution_permitted: bool
    execution_lease_materialized: bool
    authorization_consumed: bool
    runtime_execution_started: bool
    runtime_execution_performed: bool
    engineering_evidence_present: bool
    scientific_execution_open: bool
    test_dataset_access: bool
    publication_permitted: bool
    image_inspection_performed: bool
    invocation_command_materialized: bool
    docker_run_performed: bool
    local_compute_execution_open: bool

    def require(self) -> None:
        if not all(
            (
                self.invocation_operation_complete,
                self.execution_authorization_complete,
                self.preexecution_verification_record_present,
                self.preexecution_verifier_implemented,
                self.preexecution_static_contract_verified,
                self.preexecution_verification_slice_open,
                self.one_shot_engineering_invocation_execution_open,
            )
        ):
            raise QWakeLC4EngineeringInvocationPreexecutionVerificationError(
                "required pre-execution authoring gate is absent"
            )
        closed = (
            self.preexecution_identity_verified,
            self.one_shot_engineering_invocation_runtime_operation_open,
            self.one_shot_engineering_invocation_permitted,
            self.one_shot_engineering_invocation_performed,
            self.branch_runtime_execution_permitted,
            self.execution_lease_materialized,
            self.authorization_consumed,
            self.runtime_execution_started,
            self.runtime_execution_performed,
            self.engineering_evidence_present,
            self.scientific_execution_open,
            self.test_dataset_access,
            self.publication_permitted,
            self.image_inspection_performed,
            self.invocation_command_materialized,
            self.docker_run_performed,
            self.local_compute_execution_open,
        )
        if any(closed):
            raise QWakeLC4EngineeringInvocationPreexecutionVerificationError(
                "pre-execution authoring opened a runtime effect"
            )


@dataclass(frozen=True)
class OneShotEngineeringInvocationPreexecutionVerification:
    """Canonical static pre-execution verification record."""

    schema_version: int
    verification_id: str
    status: str
    verification_acknowledgement: str
    recorded_at_utc: str
    source: PreexecutionVerificationSource
    contract: PreexecutionVerificationContract
    gates: PreexecutionVerificationGates
    next_slice: str
    post_merge_next_slice: str
    verification_sha256: str

    def require(self) -> None:
        if self.schema_version != 1:
            raise QWakeLC4EngineeringInvocationPreexecutionVerificationError(
                "pre-execution schema version differs"
            )
        exact: Mapping[str, str] = {
            "verification_id": PREEXECUTION_VERIFICATION_ID,
            "status": PREEXECUTION_VERIFICATION_STATUS,
            "verification_acknowledgement": (
                PREEXECUTION_VERIFICATION_ACKNOWLEDGEMENT
            ),
            "next_slice": (
                "QW-LC4-E-one-shot-engineering-invocation-"
                "preexecution-verification-commit"
            ),
            "post_merge_next_slice": (
                "QW-LC4-E-one-shot-engineering-invocation-runtime-operation"
            ),
        }
        for field_name, expected in exact.items():
            if getattr(self, field_name) != expected:
                raise QWakeLC4EngineeringInvocationPreexecutionVerificationError(
                    f"pre-execution record differs: {field_name}"
                )
        _require_utc(self.recorded_at_utc, "recorded_at_utc")
        self.source.require()
        self.contract.require()
        self.gates.require()
        _require_sha256(self.verification_sha256, "verification_sha256")
        if self.verification_sha256 != sha256_object(
            self._payload_without_digest()
        ):
            raise QWakeLC4EngineeringInvocationPreexecutionVerificationError(
                "pre-execution verification digest differs"
            )

    def _payload_without_digest(self) -> Mapping[str, object]:
        payload = asdict(self)
        payload.pop("verification_sha256")
        return cast(Mapping[str, object], payload)

    def canonical_json(self) -> str:
        return canonical_json(asdict(self))


def build_engineering_invocation_preexecution_verification(
    *,
    recorded_at_utc: str = "2026-07-29T22:00:00Z",
) -> OneShotEngineeringInvocationPreexecutionVerification:
    """Build the exact effect-free pre-execution verification record."""

    source = PreexecutionVerificationSource(
        preexecution_base_commit=PREEXECUTION_BASE_COMMIT,
        execution_authorization_id=EXECUTION_AUTHORIZATION_ID,
        authorization_head_commit=AUTHORIZATION_HEAD_COMMIT,
        authorization_parent_commit=AUTHORIZATION_PARENT_COMMIT,
        authorization_merged_at_utc=AUTHORIZATION_MERGED_AT_UTC,
        authorization_pr_number=AUTHORIZATION_PR_NUMBER,
        execution_authorization_sha256=EXECUTION_AUTHORIZATION_SHA256,
        execution_authorization_file_sha256=(
            EXECUTION_AUTHORIZATION_FILE_SHA256
        ),
        execution_authorization_registry_sha256=(
            EXECUTION_AUTHORIZATION_REGISTRY_SHA256
        ),
        execution_authorization_module_sha256=(
            EXECUTION_AUTHORIZATION_MODULE_SHA256
        ),
        execution_authorization_verifier_sha256=(
            EXECUTION_AUTHORIZATION_VERIFIER_SHA256
        ),
        execution_authorization_test_sha256=(
            EXECUTION_AUTHORIZATION_TEST_SHA256
        ),
        invocation_operation_id=INVOCATION_OPERATION_ID,
        invocation_authorization_id=INVOCATION_AUTHORIZATION_ID,
        host_runtime_invoker_contract_id=HOST_RUNTIME_INVOKER_CONTRACT_ID,
        host_runtime_invoker_contract_sha256=(
            HOST_RUNTIME_INVOKER_CONTRACT_SHA256
        ),
        host_runtime_invoker_implementation_id=(
            HOST_RUNTIME_INVOKER_IMPLEMENTATION_ID
        ),
        host_runtime_invoker_implementation_state_sha256=(
            HOST_RUNTIME_INVOKER_IMPLEMENTATION_STATE_SHA256
        ),
        host_runtime_invoker_module_sha256=HOST_RUNTIME_INVOKER_MODULE_SHA256,
        host_runtime_invoker_verifier_sha256=(
            HOST_RUNTIME_INVOKER_VERIFIER_SHA256
        ),
        host_runtime_invoker_test_sha256=HOST_RUNTIME_INVOKER_TEST_SHA256,
        host_runtime_invoker_record_sha256=HOST_RUNTIME_INVOKER_RECORD_SHA256,
        host_runtime_invoker_registry_sha256=(
            HOST_RUNTIME_INVOKER_REGISTRY_SHA256
        ),
        image_repo_digest=IMAGE_REPO_DIGEST,
        torch2pc_commit=TORCH2PC_COMMIT,
        output_root=str(AUTHORIZED_OUTPUT_ROOT),
        execution_lease_relative=str(EXECUTION_LEASE_RELATIVE),
    )
    contract = PreexecutionVerificationContract(
        exact_merged_execution_authorization_required=True,
        exact_host_runtime_invoker_required=True,
        direct_runtime_entrypoint_required=RUNTIME_ENTRYPOINT,
        runtime_entrypoint_call_count=RUNTIME_ENTRYPOINT_CALL_COUNT,
        preexecution_and_spawn_same_process_required=True,
        required_host_resource_keys=REQUIRED_HOST_RESOURCE_KEYS,
        exact_host_resources_required=True,
        exact_immutable_image_required=True,
        image_inspection_count_required=IMAGE_INSPECTION_COUNT,
        invocation_materialization_count_required=(
            INVOCATION_MATERIALIZATION_COUNT
        ),
        image_inspection_equality_required=True,
        canonical_argv_equality_required=True,
        authorization_unconsumed_required=True,
        execution_lease_absence_required=True,
        output_absence_required=True,
        runtime_staging_absence_required=True,
        invocation_operator_acknowledgement=(
            INVOCATION_OPERATOR_ACKNOWLEDGEMENT
        ),
        lease_operator_acknowledgement=LEASE_OPERATOR_ACKNOWLEDGEMENT,
        host_prelaunch_sequence=HOST_PRELAUNCH_SEQUENCE,
        subprocess_popen_call_limit=SUBPROCESS_POPEN_CALL_LIMIT,
        shell_interpretation_forbidden=True,
        host_execution_lease_write_forbidden=True,
        command_persistence_forbidden=True,
        host_log_persistence_forbidden=True,
        automatic_retry_after_spawn_forbidden=True,
        verifier_image_inspection_call_count=0,
        verifier_invocation_materialization_call_count=0,
        verifier_process_spawn_call_count=0,
    )
    gates = PreexecutionVerificationGates(
        invocation_operation_complete=True,
        execution_authorization_complete=True,
        preexecution_verification_record_present=True,
        preexecution_verifier_implemented=True,
        preexecution_static_contract_verified=True,
        preexecution_verification_slice_open=True,
        preexecution_identity_verified=False,
        one_shot_engineering_invocation_execution_open=True,
        one_shot_engineering_invocation_runtime_operation_open=False,
        one_shot_engineering_invocation_permitted=False,
        one_shot_engineering_invocation_performed=False,
        branch_runtime_execution_permitted=False,
        execution_lease_materialized=False,
        authorization_consumed=False,
        runtime_execution_started=False,
        runtime_execution_performed=False,
        engineering_evidence_present=False,
        scientific_execution_open=False,
        test_dataset_access=False,
        publication_permitted=False,
        image_inspection_performed=False,
        invocation_command_materialized=False,
        docker_run_performed=False,
        local_compute_execution_open=False,
    )
    payload: dict[str, object] = {
        "schema_version": 1,
        "verification_id": PREEXECUTION_VERIFICATION_ID,
        "status": PREEXECUTION_VERIFICATION_STATUS,
        "verification_acknowledgement": (
            PREEXECUTION_VERIFICATION_ACKNOWLEDGEMENT
        ),
        "recorded_at_utc": recorded_at_utc,
        "source": asdict(source),
        "contract": asdict(contract),
        "gates": asdict(gates),
        "next_slice": (
            "QW-LC4-E-one-shot-engineering-invocation-"
            "preexecution-verification-commit"
        ),
        "post_merge_next_slice": (
            "QW-LC4-E-one-shot-engineering-invocation-runtime-operation"
        ),
    }
    record = OneShotEngineeringInvocationPreexecutionVerification(
        schema_version=1,
        verification_id=PREEXECUTION_VERIFICATION_ID,
        status=PREEXECUTION_VERIFICATION_STATUS,
        verification_acknowledgement=(
            PREEXECUTION_VERIFICATION_ACKNOWLEDGEMENT
        ),
        recorded_at_utc=recorded_at_utc,
        source=source,
        contract=contract,
        gates=gates,
        next_slice=(
            "QW-LC4-E-one-shot-engineering-invocation-"
            "preexecution-verification-commit"
        ),
        post_merge_next_slice=(
            "QW-LC4-E-one-shot-engineering-invocation-runtime-operation"
        ),
        verification_sha256=sha256_object(payload),
    )
    record.require()
    return record


def load_engineering_invocation_preexecution_verification(
    path: Path,
) -> OneShotEngineeringInvocationPreexecutionVerification:
    """Load a canonical verification record from disk."""

    data = _read_json_object(path)
    source = PreexecutionVerificationSource(
        **cast(Any, _as_dict(data.get("source"), "source"))
    )
    contract_data = _as_dict(data.get("contract"), "contract")
    contract_data["required_host_resource_keys"] = tuple(
        cast(list[str], contract_data["required_host_resource_keys"])
    )
    contract_data["host_prelaunch_sequence"] = tuple(
        cast(list[str], contract_data["host_prelaunch_sequence"])
    )
    contract = PreexecutionVerificationContract(**cast(Any, contract_data))
    gates = PreexecutionVerificationGates(
        **cast(Any, _as_dict(data.get("gates"), "gates"))
    )
    record = OneShotEngineeringInvocationPreexecutionVerification(
        schema_version=cast(int, data.get("schema_version")),
        verification_id=cast(str, data.get("verification_id")),
        status=cast(str, data.get("status")),
        verification_acknowledgement=cast(
            str,
            data.get("verification_acknowledgement"),
        ),
        recorded_at_utc=cast(str, data.get("recorded_at_utc")),
        source=source,
        contract=contract,
        gates=gates,
        next_slice=cast(str, data.get("next_slice")),
        post_merge_next_slice=cast(str, data.get("post_merge_next_slice")),
        verification_sha256=cast(str, data.get("verification_sha256")),
    )
    record.require()
    return record


def verify_engineering_invocation_preexecution_verification(
    project_root: Path,
) -> OneShotEngineeringInvocationPreexecutionVerification:
    """Verify exact static identities while keeping runtime effects closed."""

    root = project_root.expanduser().resolve()
    _require_effect_boundary_closed(root)
    _verify_package(root)

    exact_files: tuple[tuple[Path, str], ...] = (
        (
            AUTHORIZATION_RECORD_RELATIVE,
            EXECUTION_AUTHORIZATION_FILE_SHA256,
        ),
        (
            AUTHORIZATION_REGISTRY_RELATIVE,
            EXECUTION_AUTHORIZATION_REGISTRY_SHA256,
        ),
        (
            AUTHORIZATION_MODULE_RELATIVE,
            EXECUTION_AUTHORIZATION_MODULE_SHA256,
        ),
        (
            AUTHORIZATION_VERIFIER_RELATIVE,
            EXECUTION_AUTHORIZATION_VERIFIER_SHA256,
        ),
        (
            AUTHORIZATION_TEST_RELATIVE,
            EXECUTION_AUTHORIZATION_TEST_SHA256,
        ),
        (INVOKER_RECORD_RELATIVE, HOST_RUNTIME_INVOKER_RECORD_SHA256),
        (INVOKER_REGISTRY_RELATIVE, HOST_RUNTIME_INVOKER_REGISTRY_SHA256),
        (INVOKER_MODULE_RELATIVE, HOST_RUNTIME_INVOKER_MODULE_SHA256),
        (INVOKER_VERIFIER_RELATIVE, HOST_RUNTIME_INVOKER_VERIFIER_SHA256),
        (INVOKER_TEST_RELATIVE, HOST_RUNTIME_INVOKER_TEST_SHA256),
    )
    for relative, expected_sha256 in exact_files:
        if _sha256_file(root / relative) != expected_sha256:
            raise QWakeLC4EngineeringInvocationPreexecutionVerificationError(
                f"pre-execution source SHA-256 differs: {relative}"
            )

    authorization = verify_engineering_invocation_execution_authorization(root)
    if authorization.authorization_sha256 != EXECUTION_AUTHORIZATION_SHA256:
        raise QWakeLC4EngineeringInvocationPreexecutionVerificationError(
            "execution authorization semantic SHA-256 differs"
        )
    invoker_state = build_host_runtime_invoker_implementation_state(root)
    if (
        invoker_state.state_sha256
        != HOST_RUNTIME_INVOKER_IMPLEMENTATION_STATE_SHA256
    ):
        raise QWakeLC4EngineeringInvocationPreexecutionVerificationError(
            "host runtime invoker implementation state differs"
        )
    record = load_engineering_invocation_preexecution_verification(
        root / RECORD_RELATIVE
    )
    expected = build_engineering_invocation_preexecution_verification(
        recorded_at_utc=record.recorded_at_utc
    )
    if record != expected:
        raise QWakeLC4EngineeringInvocationPreexecutionVerificationError(
            "pre-execution verification record differs from reconstruction"
        )
    _require_effect_boundary_closed(root)
    return record


def _verify_package(root: Path) -> None:
    package = root / PACKAGE_RELATIVE
    if not package.is_dir() or package.is_symlink():
        raise QWakeLC4EngineeringInvocationPreexecutionVerificationError(
            "pre-execution package is absent or non-regular"
        )
    observed = frozenset(path.name for path in package.iterdir())
    if observed != _EXPECTED_PACKAGE_FILES:
        raise QWakeLC4EngineeringInvocationPreexecutionVerificationError(
            "pre-execution package scope differs"
        )
    registry = root / REGISTRY_RELATIVE
    if not registry.is_file() or registry.is_symlink():
        raise QWakeLC4EngineeringInvocationPreexecutionVerificationError(
            "pre-execution registry is absent or non-regular"
        )
    lines = tuple(
        line
        for line in registry.read_text(encoding="utf-8").splitlines()
        if line
    )
    if len(lines) != 1 or "  " not in lines[0]:
        raise QWakeLC4EngineeringInvocationPreexecutionVerificationError(
            "pre-execution registry scope differs"
        )
    digest, relative = lines[0].split("  ", 1)
    if relative != "verification.json":
        raise QWakeLC4EngineeringInvocationPreexecutionVerificationError(
            "pre-execution registry path differs"
        )
    if _sha256_file(root / RECORD_RELATIVE) != "sha256:" + digest:
        raise QWakeLC4EngineeringInvocationPreexecutionVerificationError(
            "pre-execution registry digest differs"
        )


def _require_effect_boundary_closed(root: Path) -> None:
    lease = root / EXECUTION_LEASE_RELATIVE
    output = root / AUTHORIZED_OUTPUT_ROOT
    if lease.exists() or lease.is_symlink():
        raise QWakeLC4EngineeringInvocationPreexecutionVerificationError(
            "repository execution lease already exists"
        )
    if output.exists() or output.is_symlink():
        raise QWakeLC4EngineeringInvocationPreexecutionVerificationError(
            "repository runtime output already exists"
        )
    staging = tuple(output.parent.glob(f".{output.name}.staging-*"))
    if staging:
        raise QWakeLC4EngineeringInvocationPreexecutionVerificationError(
            "repository runtime staging tree already exists"
        )


def _read_json_object(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise QWakeLC4EngineeringInvocationPreexecutionVerificationError(
            f"JSON source is absent or non-regular: {path}"
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="strict"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise QWakeLC4EngineeringInvocationPreexecutionVerificationError(
            f"JSON source cannot be decoded: {path}"
        ) from exc
    return _as_dict(data, str(path))


def _as_dict(value: object, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict) or not all(
        isinstance(key, str) for key in value
    ):
        raise QWakeLC4EngineeringInvocationPreexecutionVerificationError(
            f"{field_name} is not an object"
        )
    return cast(dict[str, Any], value)


def _sha256_file(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise QWakeLC4EngineeringInvocationPreexecutionVerificationError(
            f"source is absent or non-regular: {path}"
        )
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
