"""Bounded runtime-operation contract for one future QW-LC4-E invocation.

The module freezes the exact post-merge operation that may call the already
verified host runtime invoker once.  Repository verification remains effect
free.  The executor entry point requires an explicit operation acknowledgement,
an explicit boolean permission, exact host-resource keys, and a current UTC
claim time before it delegates all dynamic image checks, command
materialization, and the single child spawn to ``invoke_one_shot_host_runtime``.

Importing or verifying this module does not inspect Docker, materialize an argv,
spawn a process, create or claim an execution lease, execute local compute,
write output, access a dataset, or publish evidence.
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

from torch2pc_thesis.stage3b_qwake_lc4_engineering_invocation_execution_authorization import (
    EXECUTION_AUTHORIZATION_ID,
)
from torch2pc_thesis.stage3b_qwake_lc4_engineering_invocation_operation import (
    IMAGE_REPO_DIGEST,
    INVOCATION_OPERATION_ID,
    REQUIRED_HOST_RESOURCE_KEYS,
)
from torch2pc_thesis.stage3b_qwake_lc4_engineering_invocation_preexecution_verification import (
    PREEXECUTION_VERIFICATION_ID,
    verify_engineering_invocation_preexecution_verification,
)
from torch2pc_thesis.stage3b_qwake_lc4_host_runtime_invoker import (
    HOST_RUNTIME_INVOKER_CONTRACT_ID,
)
from torch2pc_thesis.stage3b_qwake_lc4_host_runtime_invoker_implementation import (
    HOST_RUNTIME_INVOKER_IMPLEMENTATION_ID,
    HostRuntimeInvocationOutcome,
    build_host_runtime_invoker_implementation_state,
    invoke_one_shot_host_runtime,
)
from torch2pc_thesis.stage3b_qwake_lc4_invocation_authorization import (
    AUTHORIZED_OUTPUT_ROOT,
    EXECUTION_LEASE_RELATIVE,
    INVOCATION_AUTHORIZATION_ID,
    INVOCATION_OPERATOR_ACKNOWLEDGEMENT,
)

RUNTIME_OPERATION_ID: Final = (
    "stage3b-qwake-lc4-e-one-shot-engineering-invocation-runtime-operation-v1"
)
RUNTIME_OPERATION_STATUS: Final = (
    "one_shot_engineering_invocation_runtime_operation_authored_execution_closed"
)
RUNTIME_OPERATION_AUTHORING_ACKNOWLEDGEMENT: Final = (
    "AUTHOR_QWAKE_LC4_ONE_SHOT_RUNTIME_OPERATION_FROM_MERGED_"
    "PREEXECUTION_VERIFICATION"
)
RUNTIME_OPERATION_EXECUTION_ACKNOWLEDGEMENT: Final = (
    "EXECUTE_QWAKE_LC4_ONE_SHOT_ENGINEERING_INVOCATION_FROM_MERGED_"
    "RUNTIME_OPERATION"
)

RUNTIME_OPERATION_BASE_COMMIT: Final = (
    "494e6a0b2f10c26b49c90fbb84c23565699a4064"
)
PREEXECUTION_HEAD_COMMIT: Final = (
    "bb888b900401894441f37fdbbe21c1e25c288366"
)
PREEXECUTION_PARENT_COMMIT: Final = (
    "49c4b97e93b47cefbf35576736927ece02c9402b"
)
PREEXECUTION_MERGED_AT_UTC: Final = "2026-07-29T23:21:31Z"
PREEXECUTION_PR_NUMBER: Final = 141
PREEXECUTION_VERIFICATION_SHA256: Final = (
    "sha256:833371b427a5c8a6e602d675711b85b2edc68441b9e5be191321a2911bce6128"
)
PREEXECUTION_VERIFICATION_FILE_SHA256: Final = (
    "sha256:a0f19309fc7bb2abe47f300a793423e8c764d6330220b4d4e8db3724c01df9f1"
)
PREEXECUTION_VERIFICATION_REGISTRY_SHA256: Final = (
    "sha256:cee3dda10e7d1249ae0a6fb56173a491dd2b87adb916b42b88a10e9e9c801028"
)
PREEXECUTION_VERIFICATION_MODULE_SHA256: Final = (
    "sha256:cae8721fb3278a3fbfeda8db366e864b75dd576fae90cfafe4c62301205dd2f6"
)
PREEXECUTION_VERIFICATION_VERIFIER_SHA256: Final = (
    "sha256:bf052424ecfabe85741ce4ddf13112db5797c2bc666c6b026bb4dd9bac55e4cd"
)
PREEXECUTION_VERIFICATION_TEST_SHA256: Final = (
    "sha256:18386e940984402b5e54c66c9a93cbf692a73be8e2ee4ee6c858a9a314cd1752"
)

EXECUTION_AUTHORIZATION_SHA256: Final = (
    "sha256:ff136538faee0d7952dc444e521d7ec760c7d54cd38406cb9b19ff1e00d9437b"
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

RUNTIME_OPERATION_ENTRYPOINT: Final = (
    "execute_one_shot_engineering_invocation_runtime_operation"
)
DELEGATED_HOST_RUNTIME_ENTRYPOINT: Final = "invoke_one_shot_host_runtime"
HOST_RUNTIME_INVOKER_CALL_COUNT: Final = 1
IMAGE_INSPECTION_COUNT: Final = 2
INVOCATION_MATERIALIZATION_COUNT: Final = 2
SUBPROCESS_POPEN_CALL_LIMIT: Final = 1

PACKAGE_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-one-shot-engineering-invocation-"
    "runtime-operation-v1"
)
RECORD_RELATIVE: Final = PACKAGE_RELATIVE / "operation.json"
REGISTRY_RELATIVE: Final = PACKAGE_RELATIVE / "SHA256SUMS"
PREEXECUTION_RECORD_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-one-shot-engineering-invocation-"
    "preexecution-verification-v1/verification.json"
)
PREEXECUTION_REGISTRY_RELATIVE: Final = PREEXECUTION_RECORD_RELATIVE.with_name(
    "SHA256SUMS"
)
PREEXECUTION_MODULE_RELATIVE: Final = Path(
    "src/torch2pc_thesis/"
    "stage3b_qwake_lc4_engineering_invocation_preexecution_verification.py"
)
PREEXECUTION_VERIFIER_RELATIVE: Final = Path(
    "scripts/verify_stage3b_qwake_lc4_engineering_invocation_"
    "preexecution_verification.py"
)
PREEXECUTION_TEST_RELATIVE: Final = Path(
    "tests/unit/test_stage3b_qwake_lc4_engineering_invocation_"
    "preexecution_verification.py"
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
RUNTIME_OPERATION_MODULE_RELATIVE: Final = Path(
    "src/torch2pc_thesis/"
    "stage3b_qwake_lc4_engineering_invocation_runtime_operation.py"
)

_EXPECTED_PACKAGE_FILES: Final = frozenset({"SHA256SUMS", "operation.json"})
_COMMIT_PATTERN: Final = re.compile(r"^[0-9a-f]{40}$")
_SHA256_PATTERN: Final = re.compile(r"^sha256:[0-9a-f]{64}$")

__all__ = [
    "RUNTIME_OPERATION_BASE_COMMIT",
    "RUNTIME_OPERATION_ENTRYPOINT",
    "RUNTIME_OPERATION_EXECUTION_ACKNOWLEDGEMENT",
    "RUNTIME_OPERATION_ID",
    "RUNTIME_OPERATION_STATUS",
    "OneShotEngineeringInvocationRuntimeOperation",
    "QWakeLC4EngineeringInvocationRuntimeOperationError",
    "RuntimeOperationContract",
    "RuntimeOperationGates",
    "RuntimeOperationSource",
    "build_engineering_invocation_runtime_operation",
    "canonical_json",
    "execute_one_shot_engineering_invocation_runtime_operation",
    "load_engineering_invocation_runtime_operation",
    "sha256_object",
    "verify_engineering_invocation_runtime_operation",
]


class QWakeLC4EngineeringInvocationRuntimeOperationError(RuntimeError):
    """Raised when the bounded runtime operation fails closed."""


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
        raise QWakeLC4EngineeringInvocationRuntimeOperationError(
            f"{field_name} is not SHA-256"
        )


def _require_commit(value: str, field_name: str) -> None:
    if _COMMIT_PATTERN.fullmatch(value) is None:
        raise QWakeLC4EngineeringInvocationRuntimeOperationError(
            f"{field_name} is not a commit"
        )


def _require_utc(value: str, field_name: str) -> datetime:
    if not value.endswith("Z"):
        raise QWakeLC4EngineeringInvocationRuntimeOperationError(
            f"{field_name} is not UTC"
        )
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise QWakeLC4EngineeringInvocationRuntimeOperationError(
            f"{field_name} is not ISO-8601"
        ) from exc
    if parsed.tzinfo != UTC:
        raise QWakeLC4EngineeringInvocationRuntimeOperationError(
            f"{field_name} timezone differs"
        )
    return parsed


@dataclass(frozen=True)
class RuntimeOperationSource:
    """Exact merged pre-execution and inherited runtime identities."""

    runtime_operation_base_commit: str
    preexecution_verification_id: str
    preexecution_head_commit: str
    preexecution_parent_commit: str
    preexecution_merged_at_utc: str
    preexecution_pr_number: int
    preexecution_verification_sha256: str
    preexecution_verification_file_sha256: str
    preexecution_verification_registry_sha256: str
    preexecution_verification_module_sha256: str
    preexecution_verification_verifier_sha256: str
    preexecution_verification_test_sha256: str
    execution_authorization_id: str
    execution_authorization_sha256: str
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
            "runtime_operation_base_commit": RUNTIME_OPERATION_BASE_COMMIT,
            "preexecution_verification_id": PREEXECUTION_VERIFICATION_ID,
            "preexecution_head_commit": PREEXECUTION_HEAD_COMMIT,
            "preexecution_parent_commit": PREEXECUTION_PARENT_COMMIT,
            "preexecution_merged_at_utc": PREEXECUTION_MERGED_AT_UTC,
            "preexecution_pr_number": PREEXECUTION_PR_NUMBER,
            "preexecution_verification_sha256": (
                PREEXECUTION_VERIFICATION_SHA256
            ),
            "preexecution_verification_file_sha256": (
                PREEXECUTION_VERIFICATION_FILE_SHA256
            ),
            "preexecution_verification_registry_sha256": (
                PREEXECUTION_VERIFICATION_REGISTRY_SHA256
            ),
            "preexecution_verification_module_sha256": (
                PREEXECUTION_VERIFICATION_MODULE_SHA256
            ),
            "preexecution_verification_verifier_sha256": (
                PREEXECUTION_VERIFICATION_VERIFIER_SHA256
            ),
            "preexecution_verification_test_sha256": (
                PREEXECUTION_VERIFICATION_TEST_SHA256
            ),
            "execution_authorization_id": EXECUTION_AUTHORIZATION_ID,
            "execution_authorization_sha256": EXECUTION_AUTHORIZATION_SHA256,
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
                raise QWakeLC4EngineeringInvocationRuntimeOperationError(
                    f"runtime-operation source differs: {field_name}"
                )
        for field_name in (
            "runtime_operation_base_commit",
            "preexecution_head_commit",
            "preexecution_parent_commit",
            "torch2pc_commit",
        ):
            _require_commit(str(getattr(self, field_name)), field_name)
        _require_utc(
            self.preexecution_merged_at_utc,
            "preexecution_merged_at_utc",
        )
        for field_name in (
            "preexecution_verification_sha256",
            "preexecution_verification_file_sha256",
            "preexecution_verification_registry_sha256",
            "preexecution_verification_module_sha256",
            "preexecution_verification_verifier_sha256",
            "preexecution_verification_test_sha256",
            "execution_authorization_sha256",
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
class RuntimeOperationContract:
    """Bounded delegation contract for the future atomic host operation."""

    runtime_operation_entrypoint: str
    delegated_host_runtime_entrypoint: str
    runtime_operation_execution_acknowledgement: str
    invocation_operator_acknowledgement: str
    invocation_count: int
    host_runtime_invoker_call_count: int
    runtime_execution_permission_argument_required: bool
    runtime_execution_permission_required_value: bool
    exact_claimed_at_utc_required: bool
    claimed_at_after_preexecution_merge_required: bool
    required_host_resource_keys: tuple[str, ...]
    exact_host_resource_key_set_required: bool
    merged_preexecution_verification_required: bool
    effect_boundary_closed_before_delegate_required: bool
    same_process_dynamic_verification_required: bool
    dynamic_image_inspection_delegated: bool
    dynamic_invocation_materialization_delegated: bool
    child_spawn_delegated: bool
    image_inspection_count_required: int
    invocation_materialization_count_required: int
    subprocess_popen_call_limit: int
    operation_direct_image_inspection_call_count: int
    operation_direct_materialization_call_count: int
    operation_direct_process_spawn_call_count: int
    operation_host_execution_lease_write_forbidden: bool
    automatic_retry_forbidden: bool
    verifier_executor_call_count: int

    def require(self) -> None:
        required_true = (
            self.runtime_execution_permission_argument_required,
            self.runtime_execution_permission_required_value,
            self.exact_claimed_at_utc_required,
            self.claimed_at_after_preexecution_merge_required,
            self.exact_host_resource_key_set_required,
            self.merged_preexecution_verification_required,
            self.effect_boundary_closed_before_delegate_required,
            self.same_process_dynamic_verification_required,
            self.dynamic_image_inspection_delegated,
            self.dynamic_invocation_materialization_delegated,
            self.child_spawn_delegated,
            self.operation_host_execution_lease_write_forbidden,
            self.automatic_retry_forbidden,
        )
        if not all(required_true):
            raise QWakeLC4EngineeringInvocationRuntimeOperationError(
                "required runtime-operation contract gate is closed"
            )
        exact: Mapping[str, object] = {
            "runtime_operation_entrypoint": RUNTIME_OPERATION_ENTRYPOINT,
            "delegated_host_runtime_entrypoint": (
                DELEGATED_HOST_RUNTIME_ENTRYPOINT
            ),
            "runtime_operation_execution_acknowledgement": (
                RUNTIME_OPERATION_EXECUTION_ACKNOWLEDGEMENT
            ),
            "invocation_operator_acknowledgement": (
                INVOCATION_OPERATOR_ACKNOWLEDGEMENT
            ),
            "invocation_count": 1,
            "host_runtime_invoker_call_count": HOST_RUNTIME_INVOKER_CALL_COUNT,
            "required_host_resource_keys": REQUIRED_HOST_RESOURCE_KEYS,
            "image_inspection_count_required": IMAGE_INSPECTION_COUNT,
            "invocation_materialization_count_required": (
                INVOCATION_MATERIALIZATION_COUNT
            ),
            "subprocess_popen_call_limit": SUBPROCESS_POPEN_CALL_LIMIT,
            "operation_direct_image_inspection_call_count": 0,
            "operation_direct_materialization_call_count": 0,
            "operation_direct_process_spawn_call_count": 0,
            "verifier_executor_call_count": 0,
        }
        for field_name, expected in exact.items():
            if getattr(self, field_name) != expected:
                raise QWakeLC4EngineeringInvocationRuntimeOperationError(
                    f"runtime-operation contract differs: {field_name}"
                )


@dataclass(frozen=True)
class RuntimeOperationGates:
    """Authoring-state gates; the runtime operation remains unperformed."""

    execution_authorization_complete: bool
    preexecution_verification_complete: bool
    preexecution_static_contract_verified: bool
    runtime_operation_record_present: bool
    runtime_operation_executor_entrypoint_implemented: bool
    runtime_operation_static_contract_verified: bool
    runtime_operation_slice_open: bool
    runtime_operation_open: bool
    preexecution_identity_verified: bool
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
        required = (
            self.execution_authorization_complete,
            self.preexecution_verification_complete,
            self.preexecution_static_contract_verified,
            self.runtime_operation_record_present,
            self.runtime_operation_executor_entrypoint_implemented,
            self.runtime_operation_static_contract_verified,
            self.runtime_operation_slice_open,
            self.runtime_operation_open,
        )
        if not all(required):
            raise QWakeLC4EngineeringInvocationRuntimeOperationError(
                "required runtime-operation authoring gate is absent"
            )
        closed = (
            self.preexecution_identity_verified,
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
            raise QWakeLC4EngineeringInvocationRuntimeOperationError(
                "runtime-operation authoring opened a runtime effect"
            )


@dataclass(frozen=True)
class OneShotEngineeringInvocationRuntimeOperation:
    """Canonical effect-free runtime-operation record."""

    schema_version: int
    operation_id: str
    status: str
    authoring_acknowledgement: str
    recorded_at_utc: str
    source: RuntimeOperationSource
    contract: RuntimeOperationContract
    gates: RuntimeOperationGates
    next_slice: str
    post_merge_next_slice: str
    operation_sha256: str

    def require(self) -> None:
        if self.schema_version != 1:
            raise QWakeLC4EngineeringInvocationRuntimeOperationError(
                "runtime-operation schema version differs"
            )
        exact: Mapping[str, str] = {
            "operation_id": RUNTIME_OPERATION_ID,
            "status": RUNTIME_OPERATION_STATUS,
            "authoring_acknowledgement": (
                RUNTIME_OPERATION_AUTHORING_ACKNOWLEDGEMENT
            ),
            "next_slice": (
                "QW-LC4-E-one-shot-engineering-invocation-"
                "runtime-operation-commit"
            ),
            "post_merge_next_slice": (
                "QW-LC4-E-one-shot-engineering-invocation-"
                "runtime-operation-execution"
            ),
        }
        for field_name, expected in exact.items():
            if getattr(self, field_name) != expected:
                raise QWakeLC4EngineeringInvocationRuntimeOperationError(
                    f"runtime-operation record differs: {field_name}"
                )
        _require_utc(self.recorded_at_utc, "recorded_at_utc")
        self.source.require()
        self.contract.require()
        self.gates.require()
        _require_sha256(self.operation_sha256, "operation_sha256")
        if self.operation_sha256 != sha256_object(self._payload_without_digest()):
            raise QWakeLC4EngineeringInvocationRuntimeOperationError(
                "runtime-operation semantic digest differs"
            )

    def _payload_without_digest(self) -> Mapping[str, object]:
        payload = asdict(self)
        payload.pop("operation_sha256")
        return cast(Mapping[str, object], payload)

    def canonical_json(self) -> str:
        return canonical_json(asdict(self))


def build_engineering_invocation_runtime_operation(
    *,
    recorded_at_utc: str = "2026-07-29T23:35:00Z",
) -> OneShotEngineeringInvocationRuntimeOperation:
    """Build the exact effect-free runtime-operation authoring record."""

    source = RuntimeOperationSource(
        runtime_operation_base_commit=RUNTIME_OPERATION_BASE_COMMIT,
        preexecution_verification_id=PREEXECUTION_VERIFICATION_ID,
        preexecution_head_commit=PREEXECUTION_HEAD_COMMIT,
        preexecution_parent_commit=PREEXECUTION_PARENT_COMMIT,
        preexecution_merged_at_utc=PREEXECUTION_MERGED_AT_UTC,
        preexecution_pr_number=PREEXECUTION_PR_NUMBER,
        preexecution_verification_sha256=PREEXECUTION_VERIFICATION_SHA256,
        preexecution_verification_file_sha256=(
            PREEXECUTION_VERIFICATION_FILE_SHA256
        ),
        preexecution_verification_registry_sha256=(
            PREEXECUTION_VERIFICATION_REGISTRY_SHA256
        ),
        preexecution_verification_module_sha256=(
            PREEXECUTION_VERIFICATION_MODULE_SHA256
        ),
        preexecution_verification_verifier_sha256=(
            PREEXECUTION_VERIFICATION_VERIFIER_SHA256
        ),
        preexecution_verification_test_sha256=(
            PREEXECUTION_VERIFICATION_TEST_SHA256
        ),
        execution_authorization_id=EXECUTION_AUTHORIZATION_ID,
        execution_authorization_sha256=EXECUTION_AUTHORIZATION_SHA256,
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
    contract = RuntimeOperationContract(
        runtime_operation_entrypoint=RUNTIME_OPERATION_ENTRYPOINT,
        delegated_host_runtime_entrypoint=DELEGATED_HOST_RUNTIME_ENTRYPOINT,
        runtime_operation_execution_acknowledgement=(
            RUNTIME_OPERATION_EXECUTION_ACKNOWLEDGEMENT
        ),
        invocation_operator_acknowledgement=(
            INVOCATION_OPERATOR_ACKNOWLEDGEMENT
        ),
        invocation_count=1,
        host_runtime_invoker_call_count=HOST_RUNTIME_INVOKER_CALL_COUNT,
        runtime_execution_permission_argument_required=True,
        runtime_execution_permission_required_value=True,
        exact_claimed_at_utc_required=True,
        claimed_at_after_preexecution_merge_required=True,
        required_host_resource_keys=REQUIRED_HOST_RESOURCE_KEYS,
        exact_host_resource_key_set_required=True,
        merged_preexecution_verification_required=True,
        effect_boundary_closed_before_delegate_required=True,
        same_process_dynamic_verification_required=True,
        dynamic_image_inspection_delegated=True,
        dynamic_invocation_materialization_delegated=True,
        child_spawn_delegated=True,
        image_inspection_count_required=IMAGE_INSPECTION_COUNT,
        invocation_materialization_count_required=(
            INVOCATION_MATERIALIZATION_COUNT
        ),
        subprocess_popen_call_limit=SUBPROCESS_POPEN_CALL_LIMIT,
        operation_direct_image_inspection_call_count=0,
        operation_direct_materialization_call_count=0,
        operation_direct_process_spawn_call_count=0,
        operation_host_execution_lease_write_forbidden=True,
        automatic_retry_forbidden=True,
        verifier_executor_call_count=0,
    )
    gates = RuntimeOperationGates(
        execution_authorization_complete=True,
        preexecution_verification_complete=True,
        preexecution_static_contract_verified=True,
        runtime_operation_record_present=True,
        runtime_operation_executor_entrypoint_implemented=True,
        runtime_operation_static_contract_verified=True,
        runtime_operation_slice_open=True,
        runtime_operation_open=True,
        preexecution_identity_verified=False,
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
        "operation_id": RUNTIME_OPERATION_ID,
        "status": RUNTIME_OPERATION_STATUS,
        "authoring_acknowledgement": (
            RUNTIME_OPERATION_AUTHORING_ACKNOWLEDGEMENT
        ),
        "recorded_at_utc": recorded_at_utc,
        "source": asdict(source),
        "contract": asdict(contract),
        "gates": asdict(gates),
        "next_slice": (
            "QW-LC4-E-one-shot-engineering-invocation-"
            "runtime-operation-commit"
        ),
        "post_merge_next_slice": (
            "QW-LC4-E-one-shot-engineering-invocation-"
            "runtime-operation-execution"
        ),
    }
    record = OneShotEngineeringInvocationRuntimeOperation(
        schema_version=1,
        operation_id=RUNTIME_OPERATION_ID,
        status=RUNTIME_OPERATION_STATUS,
        authoring_acknowledgement=(
            RUNTIME_OPERATION_AUTHORING_ACKNOWLEDGEMENT
        ),
        recorded_at_utc=recorded_at_utc,
        source=source,
        contract=contract,
        gates=gates,
        next_slice=(
            "QW-LC4-E-one-shot-engineering-invocation-"
            "runtime-operation-commit"
        ),
        post_merge_next_slice=(
            "QW-LC4-E-one-shot-engineering-invocation-"
            "runtime-operation-execution"
        ),
        operation_sha256=sha256_object(payload),
    )
    record.require()
    return record


def load_engineering_invocation_runtime_operation(
    path: Path,
) -> OneShotEngineeringInvocationRuntimeOperation:
    """Load a canonical runtime-operation record from disk."""

    data = _read_json_object(path)
    source = RuntimeOperationSource(
        **cast(Any, _as_dict(data.get("source"), "source"))
    )
    contract_data = _as_dict(data.get("contract"), "contract")
    contract_data["required_host_resource_keys"] = tuple(
        cast(list[str], contract_data["required_host_resource_keys"])
    )
    contract = RuntimeOperationContract(**cast(Any, contract_data))
    gates = RuntimeOperationGates(
        **cast(Any, _as_dict(data.get("gates"), "gates"))
    )
    record = OneShotEngineeringInvocationRuntimeOperation(
        schema_version=cast(int, data.get("schema_version")),
        operation_id=cast(str, data.get("operation_id")),
        status=cast(str, data.get("status")),
        authoring_acknowledgement=cast(
            str,
            data.get("authoring_acknowledgement"),
        ),
        recorded_at_utc=cast(str, data.get("recorded_at_utc")),
        source=source,
        contract=contract,
        gates=gates,
        next_slice=cast(str, data.get("next_slice")),
        post_merge_next_slice=cast(str, data.get("post_merge_next_slice")),
        operation_sha256=cast(str, data.get("operation_sha256")),
    )
    record.require()
    return record


def verify_engineering_invocation_runtime_operation(
    project_root: Path,
) -> OneShotEngineeringInvocationRuntimeOperation:
    """Verify exact static identities while preserving a closed boundary."""

    root = project_root.expanduser().resolve()
    _require_effect_boundary_closed(root)
    _verify_package(root)

    exact_files: tuple[tuple[Path, str], ...] = (
        (
            PREEXECUTION_RECORD_RELATIVE,
            PREEXECUTION_VERIFICATION_FILE_SHA256,
        ),
        (
            PREEXECUTION_REGISTRY_RELATIVE,
            PREEXECUTION_VERIFICATION_REGISTRY_SHA256,
        ),
        (
            PREEXECUTION_MODULE_RELATIVE,
            PREEXECUTION_VERIFICATION_MODULE_SHA256,
        ),
        (
            PREEXECUTION_VERIFIER_RELATIVE,
            PREEXECUTION_VERIFICATION_VERIFIER_SHA256,
        ),
        (
            PREEXECUTION_TEST_RELATIVE,
            PREEXECUTION_VERIFICATION_TEST_SHA256,
        ),
        (INVOKER_RECORD_RELATIVE, HOST_RUNTIME_INVOKER_RECORD_SHA256),
        (INVOKER_REGISTRY_RELATIVE, HOST_RUNTIME_INVOKER_REGISTRY_SHA256),
        (INVOKER_MODULE_RELATIVE, HOST_RUNTIME_INVOKER_MODULE_SHA256),
        (INVOKER_VERIFIER_RELATIVE, HOST_RUNTIME_INVOKER_VERIFIER_SHA256),
        (INVOKER_TEST_RELATIVE, HOST_RUNTIME_INVOKER_TEST_SHA256),
    )
    for relative, expected_sha256 in exact_files:
        if _sha256_file(root / relative) != expected_sha256:
            raise QWakeLC4EngineeringInvocationRuntimeOperationError(
                f"runtime-operation source SHA-256 differs: {relative}"
            )

    preexecution = verify_engineering_invocation_preexecution_verification(root)
    if preexecution.verification_sha256 != PREEXECUTION_VERIFICATION_SHA256:
        raise QWakeLC4EngineeringInvocationRuntimeOperationError(
            "pre-execution verification semantic SHA-256 differs"
        )
    invoker_state = build_host_runtime_invoker_implementation_state(root)
    if (
        invoker_state.state_sha256
        != HOST_RUNTIME_INVOKER_IMPLEMENTATION_STATE_SHA256
    ):
        raise QWakeLC4EngineeringInvocationRuntimeOperationError(
            "host runtime invoker implementation state differs"
        )
    _verify_executor_ast(root / RUNTIME_OPERATION_MODULE_RELATIVE)

    record = load_engineering_invocation_runtime_operation(root / RECORD_RELATIVE)
    expected = build_engineering_invocation_runtime_operation(
        recorded_at_utc=record.recorded_at_utc
    )
    if record != expected:
        raise QWakeLC4EngineeringInvocationRuntimeOperationError(
            "runtime-operation record differs from reconstruction"
        )
    _require_effect_boundary_closed(root)
    return record


def execute_one_shot_engineering_invocation_runtime_operation(
    project_root: Path,
    *,
    host_resources: Mapping[str, str],
    claimed_at_utc: str,
    invocation_operator_acknowledgement: str,
    runtime_operation_acknowledgement: str,
    runtime_execution_permitted: bool,
) -> HostRuntimeInvocationOutcome:
    """Delegate exactly one explicitly permitted bounded host invocation."""

    root = project_root.expanduser().resolve()
    verify_engineering_invocation_runtime_operation(root)
    if runtime_operation_acknowledgement != (
        RUNTIME_OPERATION_EXECUTION_ACKNOWLEDGEMENT
    ):
        raise QWakeLC4EngineeringInvocationRuntimeOperationError(
            "runtime-operation execution acknowledgement differs"
        )
    if runtime_execution_permitted is not True:
        raise QWakeLC4EngineeringInvocationRuntimeOperationError(
            "runtime-operation execution permission is closed"
        )
    if invocation_operator_acknowledgement != (
        INVOCATION_OPERATOR_ACKNOWLEDGEMENT
    ):
        raise QWakeLC4EngineeringInvocationRuntimeOperationError(
            "invocation operator acknowledgement differs"
        )
    claimed_at = _require_utc(claimed_at_utc, "claimed_at_utc")
    merged_at = _require_utc(
        PREEXECUTION_MERGED_AT_UTC,
        "preexecution_merged_at_utc",
    )
    if claimed_at <= merged_at:
        raise QWakeLC4EngineeringInvocationRuntimeOperationError(
            "claimed_at_utc does not follow the pre-execution merge"
        )
    _require_exact_host_resource_keys(host_resources)
    _require_effect_boundary_closed(root)
    return invoke_one_shot_host_runtime(
        root,
        host_resources=host_resources,
        claimed_at_utc=claimed_at_utc,
        operator_acknowledgement=invocation_operator_acknowledgement,
    )


def _verify_executor_ast(module_path: Path) -> None:
    if not module_path.is_file() or module_path.is_symlink():
        raise QWakeLC4EngineeringInvocationRuntimeOperationError(
            "runtime-operation module is absent or non-regular"
        )
    tree = ast.parse(module_path.read_text(encoding="utf-8", errors="strict"))
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    }
    executor = functions.get(RUNTIME_OPERATION_ENTRYPOINT)
    if executor is None:
        raise QWakeLC4EngineeringInvocationRuntimeOperationError(
            "runtime-operation executor entry point is absent"
        )
    direct_calls = [
        node.func.id
        for node in ast.walk(executor)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    ]
    if direct_calls.count(DELEGATED_HOST_RUNTIME_ENTRYPOINT) != 1:
        raise QWakeLC4EngineeringInvocationRuntimeOperationError(
            "runtime-operation host invoker call count differs"
        )
    forbidden = {
        "inspect_local_immutable_image",
        "materialize_one_shot_invocation",
        "claim_execution_lease",
        "run_one_shot_authorized_runtime",
        "Popen",
        "run",
    }
    if forbidden.intersection(direct_calls):
        raise QWakeLC4EngineeringInvocationRuntimeOperationError(
            "runtime-operation executor contains a forbidden direct effect"
        )
    attribute_calls = {
        node.func.attr
        for node in ast.walk(executor)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    if forbidden.intersection(attribute_calls):
        raise QWakeLC4EngineeringInvocationRuntimeOperationError(
            "runtime-operation executor contains a forbidden attributed effect"
        )


def _require_exact_host_resource_keys(
    host_resources: Mapping[str, str],
) -> None:
    observed = frozenset(host_resources)
    expected = frozenset(REQUIRED_HOST_RESOURCE_KEYS)
    if observed != expected:
        missing = sorted(expected - observed)
        extra = sorted(observed - expected)
        raise QWakeLC4EngineeringInvocationRuntimeOperationError(
            "host resource keys differ: "
            f"missing={missing!r}, extra={extra!r}"
        )
    if any(not isinstance(value, str) for value in host_resources.values()):
        raise QWakeLC4EngineeringInvocationRuntimeOperationError(
            "host resource values must be strings"
        )


def _verify_package(root: Path) -> None:
    package = root / PACKAGE_RELATIVE
    if not package.is_dir() or package.is_symlink():
        raise QWakeLC4EngineeringInvocationRuntimeOperationError(
            "runtime-operation package is absent or non-regular"
        )
    observed = frozenset(path.name for path in package.iterdir())
    if observed != _EXPECTED_PACKAGE_FILES:
        raise QWakeLC4EngineeringInvocationRuntimeOperationError(
            "runtime-operation package scope differs"
        )
    registry = root / REGISTRY_RELATIVE
    if not registry.is_file() or registry.is_symlink():
        raise QWakeLC4EngineeringInvocationRuntimeOperationError(
            "runtime-operation registry is absent or non-regular"
        )
    lines = tuple(
        line
        for line in registry.read_text(encoding="utf-8").splitlines()
        if line
    )
    if len(lines) != 1 or "  " not in lines[0]:
        raise QWakeLC4EngineeringInvocationRuntimeOperationError(
            "runtime-operation registry scope differs"
        )
    digest, relative = lines[0].split("  ", 1)
    if relative != "operation.json":
        raise QWakeLC4EngineeringInvocationRuntimeOperationError(
            "runtime-operation registry path differs"
        )
    if _sha256_file(root / RECORD_RELATIVE) != "sha256:" + digest:
        raise QWakeLC4EngineeringInvocationRuntimeOperationError(
            "runtime-operation registry digest differs"
        )


def _require_effect_boundary_closed(root: Path) -> None:
    lease = root / EXECUTION_LEASE_RELATIVE
    output = root / AUTHORIZED_OUTPUT_ROOT
    if lease.exists() or lease.is_symlink():
        raise QWakeLC4EngineeringInvocationRuntimeOperationError(
            "repository execution lease already exists"
        )
    if output.exists() or output.is_symlink():
        raise QWakeLC4EngineeringInvocationRuntimeOperationError(
            "repository runtime output already exists"
        )
    staging = tuple(output.parent.glob(f".{output.name}.staging-*"))
    if staging:
        raise QWakeLC4EngineeringInvocationRuntimeOperationError(
            "repository runtime staging tree already exists"
        )


def _read_json_object(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise QWakeLC4EngineeringInvocationRuntimeOperationError(
            f"JSON source is absent or non-regular: {path}"
        )
    value = json.loads(path.read_text(encoding="utf-8", errors="strict"))
    if not isinstance(value, dict):
        raise QWakeLC4EngineeringInvocationRuntimeOperationError(
            f"JSON source is not an object: {path}"
        )
    return cast(dict[str, Any], value)


def _as_dict(value: object, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise QWakeLC4EngineeringInvocationRuntimeOperationError(
            f"{field_name} is not an object"
        )
    return cast(dict[str, Any], value)


def _sha256_file(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise QWakeLC4EngineeringInvocationRuntimeOperationError(
            f"source is absent or non-regular: {path}"
        )
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
