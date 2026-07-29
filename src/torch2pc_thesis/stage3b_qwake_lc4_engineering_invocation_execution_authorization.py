"""Effect-free authorization for one future QW-LC4-E host invocation.

This module binds the independently merged invocation-operation record to the
previously frozen one-shot authorization, immutable image, Torch2PC revision,
and bounded host runtime invoker.  It materializes the exact pre-execution
verification contract but performs no Docker image inspection, command
materialization, process spawn, lease claim, backend execution, output write,
dataset access, or publication.
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

from torch2pc_thesis.stage3b_qwake_lc4_engineering_invocation_operation import (
    IMAGE_REPO_DIGEST,
    INVOCATION_OPERATION_ID,
    REQUIRED_HOST_RESOURCE_KEYS,
    verify_engineering_invocation_operation,
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
    verify_invocation_authorization,
)

EXECUTION_AUTHORIZATION_ID: Final = (
    "stage3b-qwake-lc4-e-one-shot-engineering-invocation-"
    "execution-authorization-v1"
)
EXECUTION_AUTHORIZATION_STATUS: Final = (
    "one_shot_engineering_invocation_execution_authorized_merge_required"
)
EXECUTION_AUTHORIZATION_ACKNOWLEDGEMENT: Final = (
    "AUTHORIZE_QWAKE_LC4_ONE_SHOT_ENGINEERING_INVOCATION_FROM_"
    "MERGED_OPERATION"
)

EXECUTION_BASE_COMMIT: Final = (
    "b0f6729e8fd1cb1aa172eef488dc56e36b335173"
)
OPERATION_HEAD_COMMIT: Final = (
    "aa8886221e286a5881f2b720414859bb313c2867"
)
OPERATION_PARENT_COMMIT: Final = (
    "28be77706bc86abaf34f86e9bdcbdcb9cc2810a8"
)
OPERATION_MERGED_AT_UTC: Final = "2026-07-29T18:57:10Z"
OPERATION_PR_NUMBER: Final = 139
OPERATION_SHA256: Final = (
    "sha256:10a612ef1b765362b361ecea57923d00a9f7339c9d3f9e3b27337f92f15326e9"
)
OPERATION_FILE_SHA256: Final = (
    "sha256:b8cabec098b14f1007adc9fa660fa1e31af9501f2266219aca3ddec24129f610"
)
OPERATION_REGISTRY_SHA256: Final = (
    "sha256:eeb417ba5d2c72dc198b22be69ea1d933da5bb03245615d418bbf0a6ba15edbd"
)
OPERATION_MODULE_SHA256: Final = (
    "sha256:f653468c77494205a6daf7af6ea3cd151260c9b9479b9a02f0a41949a0a5ab30"
)
OPERATION_VERIFIER_SHA256: Final = (
    "sha256:a51b22004bb8da9611538c01bf718710e5a6eda4111b3dec44aa7dbcb777448c"
)
OPERATION_TEST_SHA256: Final = (
    "sha256:bc11ec8443cf7432bb89d6ebbf1698448125c30e3ae74331347a866be17d4458"
)

INVOCATION_AUTHORIZATION_SHA256: Final = (
    "sha256:0a60dacc1bfd5073cf52d76f2ec33ae54f00899aad9877d44607199659fda75a"
)
INVOCATION_AUTHORIZATION_FILE_SHA256: Final = (
    "sha256:e7b58ad04a932b36a0eaea5a276e95c593d4e88e303e05dadbb25eaf3eb5c999"
)
INVOCATION_AUTHORIZATION_REGISTRY_SHA256: Final = (
    "sha256:9a47f79e9607db98a2c7c224c25cbeee920974d4c339eef4ef82d4f9aa7c8f83"
)
INVOCATION_AUTHORIZATION_SOURCE_REGISTRY_SHA256: Final = (
    "sha256:9f295ea2970e24c4b88ffb0136c5c8cf7e5c48fbfd259db38bc895578d3a6813"
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
HOST_RUNTIME_INVOKER_RECORD_SHA256: Final = (
    "sha256:beb24e0fda734aa4a9a74e7887349944f27805817def0f07e33618f566e505e1"
)
HOST_RUNTIME_INVOKER_REGISTRY_SHA256: Final = (
    "sha256:d04ad77ad59ee289fab4ca0bf1a0a44009c47ecb8af058ccebf77b9fe58c173a"
)

TORCH2PC_COMMIT: Final = "b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4"

PACKAGE_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-one-shot-engineering-invocation-"
    "execution-authorization-v1"
)
RECORD_RELATIVE: Final = PACKAGE_RELATIVE / "authorization.json"
REGISTRY_RELATIVE: Final = PACKAGE_RELATIVE / "SHA256SUMS"
OPERATION_RECORD_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-one-shot-engineering-invocation-operation-v1/"
    "operation.json"
)
OPERATION_REGISTRY_RELATIVE: Final = OPERATION_RECORD_RELATIVE.with_name(
    "SHA256SUMS"
)
OPERATION_MODULE_RELATIVE: Final = Path(
    "src/torch2pc_thesis/"
    "stage3b_qwake_lc4_engineering_invocation_operation.py"
)
OPERATION_VERIFIER_RELATIVE: Final = Path(
    "scripts/verify_stage3b_qwake_lc4_engineering_invocation_operation.py"
)
OPERATION_TEST_RELATIVE: Final = Path(
    "tests/unit/test_stage3b_qwake_lc4_engineering_invocation_operation.py"
)
AUTHORIZATION_RECORD_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-one-shot-engineering-invocation-authorization-v1/"
    "authorization.json"
)
AUTHORIZATION_REGISTRY_RELATIVE: Final = AUTHORIZATION_RECORD_RELATIVE.with_name(
    "SHA256SUMS"
)
AUTHORIZATION_SOURCE_REGISTRY_RELATIVE: Final = (
    AUTHORIZATION_RECORD_RELATIVE.with_name("source-SHA256SUMS")
)
INVOKER_MODULE_RELATIVE: Final = Path(
    "src/torch2pc_thesis/"
    "stage3b_qwake_lc4_host_runtime_invoker_implementation.py"
)
INVOKER_RECORD_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-implementation-v1/"
    "implementation.json"
)
INVOKER_REGISTRY_RELATIVE: Final = INVOKER_RECORD_RELATIVE.with_name(
    "SHA256SUMS"
)

_EXPECTED_PACKAGE_FILES: Final = frozenset({"SHA256SUMS", "authorization.json"})
_COMMIT_PATTERN: Final = re.compile(r"^[0-9a-f]{40}$")
_SHA256_PATTERN: Final = re.compile(r"^sha256:[0-9a-f]{64}$")

__all__ = [
    "EXECUTION_AUTHORIZATION_ID",
    "EXECUTION_AUTHORIZATION_STATUS",
    "EXECUTION_BASE_COMMIT",
    "ExecutionAuthorizationContract",
    "ExecutionAuthorizationGates",
    "ExecutionAuthorizationSource",
    "OneShotEngineeringInvocationExecutionAuthorization",
    "QWakeLC4EngineeringInvocationExecutionAuthorizationError",
    "build_engineering_invocation_execution_authorization",
    "canonical_json",
    "load_engineering_invocation_execution_authorization",
    "sha256_object",
    "verify_engineering_invocation_execution_authorization",
]


class QWakeLC4EngineeringInvocationExecutionAuthorizationError(RuntimeError):
    """Raised when the execution authorization cannot remain fail closed."""


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
        raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
            f"{field_name} is not SHA-256"
        )


def _require_commit(value: str, field_name: str) -> None:
    if _COMMIT_PATTERN.fullmatch(value) is None:
        raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
            f"{field_name} is not a commit"
        )


def _require_utc(value: str) -> datetime:
    if not value.endswith("Z"):
        raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
            "recorded_at_utc is not UTC"
        )
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
            "recorded_at_utc is not ISO-8601"
        ) from exc
    if parsed.tzinfo != UTC:
        raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
            "recorded_at_utc timezone differs"
        )
    return parsed


@dataclass(frozen=True)
class ExecutionAuthorizationSource:
    """Exact merged operation and inherited runtime identities."""

    execution_base_commit: str
    operation_id: str
    operation_head_commit: str
    operation_parent_commit: str
    operation_merged_at_utc: str
    operation_pr_number: int
    operation_sha256: str
    operation_file_sha256: str
    operation_registry_sha256: str
    operation_module_sha256: str
    operation_verifier_sha256: str
    operation_test_sha256: str
    invocation_authorization_id: str
    invocation_authorization_sha256: str
    invocation_authorization_file_sha256: str
    invocation_authorization_registry_sha256: str
    invocation_authorization_source_registry_sha256: str
    host_runtime_invoker_implementation_id: str
    host_runtime_invoker_implementation_state_sha256: str
    host_runtime_invoker_contract_sha256: str
    host_runtime_invoker_module_sha256: str
    host_runtime_invoker_record_sha256: str
    host_runtime_invoker_registry_sha256: str
    torch2pc_commit: str
    image_repo_digest: str
    output_root: str
    execution_lease_relative: str

    def require(self) -> None:
        expected: Mapping[str, object] = {
            "execution_base_commit": EXECUTION_BASE_COMMIT,
            "operation_id": INVOCATION_OPERATION_ID,
            "operation_head_commit": OPERATION_HEAD_COMMIT,
            "operation_parent_commit": OPERATION_PARENT_COMMIT,
            "operation_merged_at_utc": OPERATION_MERGED_AT_UTC,
            "operation_pr_number": OPERATION_PR_NUMBER,
            "operation_sha256": OPERATION_SHA256,
            "operation_file_sha256": OPERATION_FILE_SHA256,
            "operation_registry_sha256": OPERATION_REGISTRY_SHA256,
            "operation_module_sha256": OPERATION_MODULE_SHA256,
            "operation_verifier_sha256": OPERATION_VERIFIER_SHA256,
            "operation_test_sha256": OPERATION_TEST_SHA256,
            "invocation_authorization_id": INVOCATION_AUTHORIZATION_ID,
            "invocation_authorization_sha256": INVOCATION_AUTHORIZATION_SHA256,
            "invocation_authorization_file_sha256": (
                INVOCATION_AUTHORIZATION_FILE_SHA256
            ),
            "invocation_authorization_registry_sha256": (
                INVOCATION_AUTHORIZATION_REGISTRY_SHA256
            ),
            "invocation_authorization_source_registry_sha256": (
                INVOCATION_AUTHORIZATION_SOURCE_REGISTRY_SHA256
            ),
            "host_runtime_invoker_implementation_id": (
                HOST_RUNTIME_INVOKER_IMPLEMENTATION_ID
            ),
            "host_runtime_invoker_implementation_state_sha256": (
                HOST_RUNTIME_INVOKER_IMPLEMENTATION_STATE_SHA256
            ),
            "host_runtime_invoker_contract_sha256": (
                HOST_RUNTIME_INVOKER_CONTRACT_SHA256
            ),
            "host_runtime_invoker_module_sha256": (
                HOST_RUNTIME_INVOKER_MODULE_SHA256
            ),
            "host_runtime_invoker_record_sha256": (
                HOST_RUNTIME_INVOKER_RECORD_SHA256
            ),
            "host_runtime_invoker_registry_sha256": (
                HOST_RUNTIME_INVOKER_REGISTRY_SHA256
            ),
            "torch2pc_commit": TORCH2PC_COMMIT,
            "image_repo_digest": IMAGE_REPO_DIGEST,
            "output_root": AUTHORIZED_OUTPUT_ROOT,
            "execution_lease_relative": str(EXECUTION_LEASE_RELATIVE),
        }
        observed = asdict(self)
        for field_name, expected_value in expected.items():
            if observed.get(field_name) != expected_value:
                raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
                    f"execution authorization source differs: {field_name}"
                )
        for field_name in (
            "execution_base_commit",
            "operation_head_commit",
            "operation_parent_commit",
            "torch2pc_commit",
        ):
            _require_commit(str(observed[field_name]), field_name)
        for field_name, value in observed.items():
            if field_name.endswith("_sha256"):
                _require_sha256(str(value), field_name)


@dataclass(frozen=True)
class ExecutionAuthorizationContract:
    """Prospective permission and mandatory same-process launch checks."""

    invocation_count: int
    future_preexecution_verification_authorized: bool
    future_one_shot_engineering_invocation_authorized: bool
    exact_execution_base_required: bool
    exact_operation_required: bool
    exact_invocation_authorization_required: bool
    exact_host_runtime_invoker_required: bool
    exact_immutable_image_required: bool
    exact_host_resources_required: bool
    required_host_resource_keys: tuple[str, ...]
    claimed_at_utc_required: bool
    invocation_operator_acknowledgement: str
    lease_operator_acknowledgement: str
    preexecution_verification_same_process_required: bool
    immutable_image_inspection_count_required: int
    invocation_materialization_count_required: int
    canonical_argv_equality_required: bool
    authorization_unconsumed_required: bool
    execution_lease_absence_required: bool
    output_absence_required: bool
    runtime_staging_absence_required: bool
    subprocess_popen_call_limit: int
    shell_interpretation_forbidden: bool
    no_retry_after_spawn_required: bool
    host_execution_lease_write_forbidden: bool

    def require(self) -> None:
        if self.invocation_count != 1:
            raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
                "execution authorization is not single-invocation"
            )
        required_true = (
            self.future_preexecution_verification_authorized,
            self.future_one_shot_engineering_invocation_authorized,
            self.exact_execution_base_required,
            self.exact_operation_required,
            self.exact_invocation_authorization_required,
            self.exact_host_runtime_invoker_required,
            self.exact_immutable_image_required,
            self.exact_host_resources_required,
            self.claimed_at_utc_required,
            self.preexecution_verification_same_process_required,
            self.canonical_argv_equality_required,
            self.authorization_unconsumed_required,
            self.execution_lease_absence_required,
            self.output_absence_required,
            self.runtime_staging_absence_required,
            self.shell_interpretation_forbidden,
            self.no_retry_after_spawn_required,
            self.host_execution_lease_write_forbidden,
        )
        if not all(required_true):
            raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
                "required execution authorization control is disabled"
            )
        if self.required_host_resource_keys != REQUIRED_HOST_RESOURCE_KEYS:
            raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
                "required host-resource key set differs"
            )
        if self.invocation_operator_acknowledgement != (
            INVOCATION_OPERATOR_ACKNOWLEDGEMENT
        ):
            raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
                "invocation operator acknowledgement differs"
            )
        if self.lease_operator_acknowledgement != LEASE_OPERATOR_ACKNOWLEDGEMENT:
            raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
                "lease operator acknowledgement differs"
            )
        if self.immutable_image_inspection_count_required != 2:
            raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
                "image inspection count differs"
            )
        if self.invocation_materialization_count_required != 2:
            raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
                "invocation materialization count differs"
            )
        if self.subprocess_popen_call_limit != 1:
            raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
                "process-spawn limit differs"
            )


@dataclass(frozen=True)
class ExecutionAuthorizationGates:
    """Effect-free branch state before the authorization is merged."""

    execution_authorization_record_present: bool
    execution_authorization_issued: bool
    preexecution_verification_materialization_implemented: bool
    preexecution_identity_verified: bool
    one_shot_engineering_invocation_slice_open: bool
    one_shot_engineering_invocation_operation_open: bool
    one_shot_engineering_invocation_execution_open: bool
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
                self.execution_authorization_record_present,
                self.execution_authorization_issued,
                self.preexecution_verification_materialization_implemented,
                self.one_shot_engineering_invocation_slice_open,
                self.one_shot_engineering_invocation_operation_open,
                self.one_shot_engineering_invocation_execution_open,
            )
        ):
            raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
                "execution authorization boundary is absent"
            )
        forbidden = (
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
        if any(forbidden):
            raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
                "execution authorization authoring opened a runtime effect"
            )


@dataclass(frozen=True)
class OneShotEngineeringInvocationExecutionAuthorization:
    """Canonical authorization for one future post-merge invocation."""

    schema_version: int
    authorization_id: str
    status: str
    recorded_at_utc: str
    authorization_acknowledgement: str
    source: ExecutionAuthorizationSource
    contract: ExecutionAuthorizationContract
    gates: ExecutionAuthorizationGates
    next_slice: str
    post_merge_next_slice: str
    authorization_sha256: str

    def require(self) -> None:
        if self.schema_version != 1:
            raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
                "unexpected execution authorization schema"
            )
        if self.authorization_id != EXECUTION_AUTHORIZATION_ID:
            raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
                "unexpected execution authorization id"
            )
        if self.status != EXECUTION_AUTHORIZATION_STATUS:
            raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
                "unexpected execution authorization status"
            )
        _require_utc(self.recorded_at_utc)
        if self.authorization_acknowledgement != (
            EXECUTION_AUTHORIZATION_ACKNOWLEDGEMENT
        ):
            raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
                "execution authorization acknowledgement differs"
            )
        self.source.require()
        self.contract.require()
        self.gates.require()
        if self.next_slice != (
            "QW-LC4-E-one-shot-engineering-invocation-"
            "execution-authorization-commit"
        ):
            raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
                "execution authorization next slice differs"
            )
        if self.post_merge_next_slice != (
            "QW-LC4-E-one-shot-engineering-invocation-"
            "preexecution-verification"
        ):
            raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
                "execution authorization post-merge slice differs"
            )
        _require_sha256(self.authorization_sha256, "authorization_sha256")
        if self.authorization_sha256 != sha256_object(
            self._payload_without_digest()
        ):
            raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
                "execution authorization semantic digest differs"
            )

    def _payload_without_digest(self) -> Mapping[str, object]:
        payload = asdict(self)
        payload.pop("authorization_sha256")
        return cast(Mapping[str, object], payload)

    def canonical_json(self) -> str:
        return canonical_json(asdict(self))


def build_engineering_invocation_execution_authorization(
    *,
    recorded_at_utc: str = "2026-07-29T19:05:00Z",
) -> OneShotEngineeringInvocationExecutionAuthorization:
    """Build the exact authorization record without environmental effects."""

    source = ExecutionAuthorizationSource(
        execution_base_commit=EXECUTION_BASE_COMMIT,
        operation_id=INVOCATION_OPERATION_ID,
        operation_head_commit=OPERATION_HEAD_COMMIT,
        operation_parent_commit=OPERATION_PARENT_COMMIT,
        operation_merged_at_utc=OPERATION_MERGED_AT_UTC,
        operation_pr_number=OPERATION_PR_NUMBER,
        operation_sha256=OPERATION_SHA256,
        operation_file_sha256=OPERATION_FILE_SHA256,
        operation_registry_sha256=OPERATION_REGISTRY_SHA256,
        operation_module_sha256=OPERATION_MODULE_SHA256,
        operation_verifier_sha256=OPERATION_VERIFIER_SHA256,
        operation_test_sha256=OPERATION_TEST_SHA256,
        invocation_authorization_id=INVOCATION_AUTHORIZATION_ID,
        invocation_authorization_sha256=INVOCATION_AUTHORIZATION_SHA256,
        invocation_authorization_file_sha256=(
            INVOCATION_AUTHORIZATION_FILE_SHA256
        ),
        invocation_authorization_registry_sha256=(
            INVOCATION_AUTHORIZATION_REGISTRY_SHA256
        ),
        invocation_authorization_source_registry_sha256=(
            INVOCATION_AUTHORIZATION_SOURCE_REGISTRY_SHA256
        ),
        host_runtime_invoker_implementation_id=(
            HOST_RUNTIME_INVOKER_IMPLEMENTATION_ID
        ),
        host_runtime_invoker_implementation_state_sha256=(
            HOST_RUNTIME_INVOKER_IMPLEMENTATION_STATE_SHA256
        ),
        host_runtime_invoker_contract_sha256=(
            HOST_RUNTIME_INVOKER_CONTRACT_SHA256
        ),
        host_runtime_invoker_module_sha256=(
            HOST_RUNTIME_INVOKER_MODULE_SHA256
        ),
        host_runtime_invoker_record_sha256=(
            HOST_RUNTIME_INVOKER_RECORD_SHA256
        ),
        host_runtime_invoker_registry_sha256=(
            HOST_RUNTIME_INVOKER_REGISTRY_SHA256
        ),
        torch2pc_commit=TORCH2PC_COMMIT,
        image_repo_digest=IMAGE_REPO_DIGEST,
        output_root=AUTHORIZED_OUTPUT_ROOT,
        execution_lease_relative=str(EXECUTION_LEASE_RELATIVE),
    )
    contract = ExecutionAuthorizationContract(
        invocation_count=1,
        future_preexecution_verification_authorized=True,
        future_one_shot_engineering_invocation_authorized=True,
        exact_execution_base_required=True,
        exact_operation_required=True,
        exact_invocation_authorization_required=True,
        exact_host_runtime_invoker_required=True,
        exact_immutable_image_required=True,
        exact_host_resources_required=True,
        required_host_resource_keys=REQUIRED_HOST_RESOURCE_KEYS,
        claimed_at_utc_required=True,
        invocation_operator_acknowledgement=(
            INVOCATION_OPERATOR_ACKNOWLEDGEMENT
        ),
        lease_operator_acknowledgement=LEASE_OPERATOR_ACKNOWLEDGEMENT,
        preexecution_verification_same_process_required=True,
        immutable_image_inspection_count_required=2,
        invocation_materialization_count_required=2,
        canonical_argv_equality_required=True,
        authorization_unconsumed_required=True,
        execution_lease_absence_required=True,
        output_absence_required=True,
        runtime_staging_absence_required=True,
        subprocess_popen_call_limit=1,
        shell_interpretation_forbidden=True,
        no_retry_after_spawn_required=True,
        host_execution_lease_write_forbidden=True,
    )
    gates = ExecutionAuthorizationGates(
        execution_authorization_record_present=True,
        execution_authorization_issued=True,
        preexecution_verification_materialization_implemented=True,
        preexecution_identity_verified=False,
        one_shot_engineering_invocation_slice_open=True,
        one_shot_engineering_invocation_operation_open=True,
        one_shot_engineering_invocation_execution_open=True,
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
        "authorization_id": EXECUTION_AUTHORIZATION_ID,
        "status": EXECUTION_AUTHORIZATION_STATUS,
        "recorded_at_utc": recorded_at_utc,
        "authorization_acknowledgement": (
            EXECUTION_AUTHORIZATION_ACKNOWLEDGEMENT
        ),
        "source": asdict(source),
        "contract": asdict(contract),
        "gates": asdict(gates),
        "next_slice": (
            "QW-LC4-E-one-shot-engineering-invocation-"
            "execution-authorization-commit"
        ),
        "post_merge_next_slice": (
            "QW-LC4-E-one-shot-engineering-invocation-"
            "preexecution-verification"
        ),
    }
    authorization = OneShotEngineeringInvocationExecutionAuthorization(
        source=source,
        contract=contract,
        gates=gates,
        authorization_sha256=sha256_object(payload),
        **cast(Any, {k: v for k, v in payload.items() if k not in {"source", "contract", "gates"}}),
    )
    authorization.require()
    return authorization


def load_engineering_invocation_execution_authorization(
    path: Path,
) -> OneShotEngineeringInvocationExecutionAuthorization:
    """Load and validate a canonical execution authorization record."""

    raw = _read_json_object(path)
    source = ExecutionAuthorizationSource(**_as_dict(raw.pop("source"), "source"))
    contract_raw = _as_dict(raw.pop("contract"), "contract")
    keys = contract_raw.get("required_host_resource_keys")
    if not isinstance(keys, list) or not all(isinstance(item, str) for item in keys):
        raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
            "required_host_resource_keys is not a string array"
        )
    contract_raw["required_host_resource_keys"] = tuple(keys)
    contract = ExecutionAuthorizationContract(**contract_raw)
    gates = ExecutionAuthorizationGates(**_as_dict(raw.pop("gates"), "gates"))
    authorization = OneShotEngineeringInvocationExecutionAuthorization(
        source=source,
        contract=contract,
        gates=gates,
        **cast(Any, raw),
    )
    authorization.require()
    if path.read_text(encoding="utf-8", errors="strict") != (
        authorization.canonical_json()
    ):
        raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
            "execution authorization JSON is not canonical"
        )
    return authorization


def verify_engineering_invocation_execution_authorization(
    project_root: Path,
) -> OneShotEngineeringInvocationExecutionAuthorization:
    """Verify exact merged identities and effect absence without invocation."""

    root = project_root.expanduser().resolve()
    _require_effect_boundary_closed(root)
    _verify_package(root)
    authorization = load_engineering_invocation_execution_authorization(
        root / RECORD_RELATIVE
    )

    operation = verify_engineering_invocation_operation(root)
    if operation.operation_id != INVOCATION_OPERATION_ID:
        raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
            "invocation operation id differs"
        )
    if operation.operation_sha256 != OPERATION_SHA256:
        raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
            "invocation operation semantic digest differs"
        )

    inherited = verify_invocation_authorization(root)
    if inherited.authorization_id != INVOCATION_AUTHORIZATION_ID:
        raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
            "inherited invocation authorization id differs"
        )
    if inherited.authorization_sha256 != INVOCATION_AUTHORIZATION_SHA256:
        raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
            "inherited invocation authorization digest differs"
        )
    if not inherited.contract.future_one_shot_invocation_permitted:
        raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
            "inherited future invocation is not authorized"
        )
    if inherited.gates.authorization_consumed:
        raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
            "inherited invocation authorization is consumed"
        )

    invoker = build_host_runtime_invoker_implementation_state(root)
    if invoker.state_sha256 != HOST_RUNTIME_INVOKER_IMPLEMENTATION_STATE_SHA256:
        raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
            "host-runtime-invoker implementation state differs"
        )

    exact_files: Mapping[Path, str] = {
        OPERATION_RECORD_RELATIVE: OPERATION_FILE_SHA256,
        OPERATION_REGISTRY_RELATIVE: OPERATION_REGISTRY_SHA256,
        OPERATION_MODULE_RELATIVE: OPERATION_MODULE_SHA256,
        OPERATION_VERIFIER_RELATIVE: OPERATION_VERIFIER_SHA256,
        OPERATION_TEST_RELATIVE: OPERATION_TEST_SHA256,
        AUTHORIZATION_RECORD_RELATIVE: INVOCATION_AUTHORIZATION_FILE_SHA256,
        AUTHORIZATION_REGISTRY_RELATIVE: (
            INVOCATION_AUTHORIZATION_REGISTRY_SHA256
        ),
        AUTHORIZATION_SOURCE_REGISTRY_RELATIVE: (
            INVOCATION_AUTHORIZATION_SOURCE_REGISTRY_SHA256
        ),
        INVOKER_MODULE_RELATIVE: HOST_RUNTIME_INVOKER_MODULE_SHA256,
        INVOKER_RECORD_RELATIVE: HOST_RUNTIME_INVOKER_RECORD_SHA256,
        INVOKER_REGISTRY_RELATIVE: HOST_RUNTIME_INVOKER_REGISTRY_SHA256,
    }
    for relative, expected_sha256 in exact_files.items():
        if _sha256_file(root / relative) != expected_sha256:
            raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
                f"execution authorization source SHA-256 differs: {relative}"
            )

    operation_gates = operation.gates
    if not operation_gates.invocation_operation_record_present:
        raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
            "operation record is absent"
        )
    if operation_gates.authorization_consumed:
        raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
            "operation observes consumed authorization"
        )
    if operation_gates.runtime_execution_started:
        raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
            "operation observes started runtime"
        )
    authorization.require()
    return authorization


def _verify_package(root: Path) -> None:
    package = root / PACKAGE_RELATIVE
    if package.is_symlink() or not package.is_dir():
        raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
            "execution authorization package is absent"
        )
    observed = {
        path.relative_to(package).as_posix()
        for path in package.rglob("*")
        if path.is_file()
    }
    if observed != _EXPECTED_PACKAGE_FILES:
        raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
            "execution authorization package contents differ"
        )
    registry = _read_registry(package / "SHA256SUMS")
    if set(registry) != {"authorization.json"}:
        raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
            "execution authorization registry contents differ"
        )
    if _sha256_file(package / "authorization.json") != registry["authorization.json"]:
        raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
            "execution authorization registry digest differs"
        )


def _require_effect_boundary_closed(root: Path) -> None:
    lease = root / EXECUTION_LEASE_RELATIVE
    output = root / AUTHORIZED_OUTPUT_ROOT
    if lease.exists() or lease.is_symlink():
        raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
            "execution lease is already materialized"
        )
    if output.exists() or output.is_symlink():
        raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
            "runtime output is already present"
        )
    staging = tuple(output.parent.glob(f".{output.name}.staging-*"))
    if staging:
        raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
            "runtime staging is already present"
        )


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8", errors="strict"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
            f"cannot read JSON: {path}"
        ) from exc
    if not isinstance(value, dict):
        raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
            f"JSON object required: {path}"
        )
    return cast(dict[str, Any], value)


def _as_dict(value: object, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
            f"{field_name} is not an object"
        )
    return cast(dict[str, Any], value)


def _read_registry(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8", errors="strict").splitlines()
    except (OSError, UnicodeError) as exc:
        raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
            f"cannot read registry: {path}"
        ) from exc
    for raw in lines:
        digest, separator, relative = raw.partition("  ")
        if not separator or not relative or relative in result:
            raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
                "execution authorization registry format differs"
            )
        value = "sha256:" + digest
        _require_sha256(value, relative)
        result[relative] = value
    return result


def _sha256_file(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise QWakeLC4EngineeringInvocationExecutionAuthorizationError(
            f"required file is absent: {path}"
        )
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
