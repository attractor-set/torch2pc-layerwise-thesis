"""Fail-closed authorization for one future QW-LC4-E invocation.

This module verifies a separately materialized machine-readable authorization
for exactly one future engineering invocation.  It does not claim the
execution lease, invoke the immutable image, execute the runtime backend, load
a dataset, write results, or publish evidence.
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

INVOCATION_AUTHORIZATION_ID: Final = (
    "stage3b-qwake-lc4-e-one-shot-engineering-invocation-authorization-v1"
)
INVOCATION_AUTHORIZATION_STATUS: Final = (
    "authorized_single_future_engineering_invocation_execution_not_started"
)
INVOCATION_OPERATOR_ACKNOWLEDGEMENT: Final = (
    "AUTHORIZE_QWAKE_LC4_ONE_SHOT_ENGINEERING_INVOCATION_FROM_"
    "MATERIALIZED_EXECUTION_FREEZE"
)
LEASE_OPERATOR_ACKNOWLEDGEMENT: Final = (
    "CLAIM_QWAKE_LC4_SINGLE_ENGINEERING_ATTEMPT_FROM_FROZEN_ADMISSION"
)

POST_MERGE_COMMIT: Final = "375db196b615f7024cd5f715de9c9be7b526a9f7"
POST_MERGE_PARENT_1: Final = "67a084c0b970ad79ad0692442f660085a73b080a"
POST_MERGE_PARENT_2: Final = "7633261f9962c3c7d33ce6b0096138fb4902c65a"
POST_MERGE_TIMESTAMP_UTC: Final = "2026-07-28T19:37:52Z"
FROZEN_TORCH2PC_COMMIT: Final = (
    "b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4"
)

EXECUTION_FREEZE_ID: Final = "stage3b-qwake-lc4-e-execution-freeze-v1"
EXECUTION_FREEZE_FILE_SHA256: Final = (
    "sha256:1ff7a7892c7db555270ec2655f7d49b21d9c52e2ecacf46a016985f1d0d1b303"
)
EXECUTION_FREEZE_PACKAGE_REGISTRY_SHA256: Final = (
    "sha256:dbb5ff6c596f300d9482eefd656ef2a57df5d48fd0a5a086985bb29025992ef7"
)
EXECUTION_FREEZE_MATERIALIZATION_FILE_SHA256: Final = (
    "sha256:41e893d7d77398b9e7ce61bb10add417f7e3d2e7077a6be2f9a2d88f3ae5d786"
)

EXECUTION_ADMISSION_ID: Final = "stage3b-qwake-lc4-e-execution-admission-v1"
EXECUTION_ADMISSION_SHA256: Final = (
    "sha256:d1ee6d022588f0a2cf0ac23f3bf8de9b27f9aad4fc1153435bd70e1ab83e296c"
)
EXECUTION_ADMISSION_FILE_SHA256: Final = (
    "sha256:d819f8a7e03314242c0072e2d020a59fbe6b7f6984fda99ff0dcd306cc97ca70"
)
EXECUTION_ADMISSION_PACKAGE_REGISTRY_SHA256: Final = (
    "sha256:411f3e8d62b367755a6f02070ad84bc6f37cfefad602d885674a844b57aa74cd"
)

RUNTIME_AUTHORIZATION_ID: Final = "stage3b-qwake-lc4-runtime-authorization-v1"
RUNTIME_AUTHORIZATION_SHA256: Final = (
    "sha256:d11b662a5c5eeada5333e69c6fddf2e50726c01b4d8c78a556a68167dbdd301e"
)
RUNTIME_AUTHORIZATION_FILE_SHA256: Final = (
    "sha256:a380cffcfa73cb2dcf984a3cc7de013cb50d79f075677ad5e762417486f06ebd"
)
RUNTIME_AUTHORIZATION_PACKAGE_REGISTRY_SHA256: Final = (
    "sha256:8f8a0dfaaff934ac3c8f654e7e65d9460168755532547dcf924e51c6451aeb6d"
)

IMAGE_TAG: Final = (
    "torch2pc-layerwise-thesis:0.1.0-qw-lc4-e-freeze-67a084c0b970"
)
IMAGE_DIGEST: Final = (
    "sha256:7da92b8f77f6dc37d42db832c5613ef6149dc488adc5b66465faa33e48ca021d"
)
IMAGE_REPO_DIGEST: Final = (
    "torch2pc-layerwise-thesis@"
    "sha256:7da92b8f77f6dc37d42db832c5613ef6149dc488adc5b66465faa33e48ca021d"
)

AUTHORIZED_OUTPUT_ROOT: Final = (
    "results/stage-3/qwake-lc4-runtime-validation-v1-attempt-001"
)
EXECUTION_LEASE_RELATIVE: Final = Path(
    AUTHORIZED_OUTPUT_ROOT + ".execution-lease.json"
)

AUTHORIZATION_ROOT_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-one-shot-engineering-invocation-authorization-v1"
)
AUTHORIZATION_RELATIVE: Final = AUTHORIZATION_ROOT_RELATIVE / "authorization.json"
AUTHORIZATION_REGISTRY_RELATIVE: Final = AUTHORIZATION_ROOT_RELATIVE / "SHA256SUMS"
AUTHORIZATION_SOURCE_REGISTRY_RELATIVE: Final = (
    AUTHORIZATION_ROOT_RELATIVE / "source-SHA256SUMS"
)

EXECUTION_FREEZE_RELATIVE: Final = Path(
    "experiments/frozen/stage3b-qwake-lc4-e-execution-freeze-v1/execution.json"
)
EXECUTION_FREEZE_REGISTRY_RELATIVE: Final = Path(
    "experiments/frozen/stage3b-qwake-lc4-e-execution-freeze-v1/SHA256SUMS"
)
EXECUTION_FREEZE_MATERIALIZATION_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-execution-freeze-v1/materialization.json"
)
EXECUTION_ADMISSION_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-execution-admission-freeze-v1/admission.json"
)
EXECUTION_ADMISSION_REGISTRY_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-execution-admission-freeze-v1/SHA256SUMS"
)
RUNTIME_AUTHORIZATION_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-f-runtime-freeze-v1/authorization.json"
)
RUNTIME_AUTHORIZATION_REGISTRY_RELATIVE: Final = Path(
    "experiments/frozen/stage3b-qwake-lc4-f-runtime-freeze-v1/SHA256SUMS"
)
RUNTIME_BACKEND_MODULE_RELATIVE: Final = Path(
    "src/torch2pc_thesis/stage3b_qwake_lc4_runtime_backend.py"
)
ONE_SHOT_ENTRYPOINT_RELATIVE: Final = Path(
    "scripts/run_stage3b_qwake_lc4_authorized_runtime.py"
)
EXECUTION_WRAPPER_MODULE_RELATIVE: Final = Path(
    "src/torch2pc_thesis/stage3b_qwake_lc4_execution_wrapper.py"
)
EXECUTION_WRAPPER_IMPLEMENTATION_RELATIVE: Final = Path(
    "src/torch2pc_thesis/stage3b_qwake_lc4_execution_wrapper_implementation.py"
)
AUTHORIZATION_MODULE_RELATIVE: Final = Path(
    "src/torch2pc_thesis/stage3b_qwake_lc4_invocation_authorization.py"
)
AUTHORIZATION_VERIFIER_RELATIVE: Final = Path(
    "scripts/verify_stage3b_qwake_lc4_invocation_authorization.py"
)
AUTHORIZATION_TEST_RELATIVE: Final = Path(
    "tests/unit/test_stage3b_qwake_lc4_invocation_authorization.py"
)

EXPECTED_RUNTIME_BACKEND_MODULE_SHA256: Final = (
    "sha256:d9ad10efe959e19d7f1b6d61d8eddd1228cb9753fa9191823d5d1ded68e9fd72"
)
EXPECTED_ONE_SHOT_ENTRYPOINT_SHA256: Final = (
    "sha256:504c3e614e199789b25c8b1927d0a35b1b95e1f3a5411e42db794fc93782cc79"
)
EXPECTED_EXECUTION_WRAPPER_MODULE_SHA256: Final = (
    "sha256:34980a70d76b582d70333034b4a259b50bd948bb751888f17db9a988c2c77a9b"
)
EXPECTED_EXECUTION_WRAPPER_IMPLEMENTATION_SHA256: Final = (
    "sha256:43e114dfdb69fa54a993a98b2a487777c40168374e61c0949e5cf862d42f7d9f"
)

_EXPECTED_PACKAGE_FILES: Final = frozenset(
    {
        "SHA256SUMS",
        "authorization.json",
        "identity.env",
        "source-SHA256SUMS",
    }
)
_EXPECTED_SOURCE_PATHS: Final = frozenset(
    {
        EXECUTION_FREEZE_RELATIVE.as_posix(),
        EXECUTION_FREEZE_REGISTRY_RELATIVE.as_posix(),
        EXECUTION_FREEZE_MATERIALIZATION_RELATIVE.as_posix(),
        EXECUTION_ADMISSION_RELATIVE.as_posix(),
        EXECUTION_ADMISSION_REGISTRY_RELATIVE.as_posix(),
        RUNTIME_AUTHORIZATION_RELATIVE.as_posix(),
        RUNTIME_AUTHORIZATION_REGISTRY_RELATIVE.as_posix(),
        RUNTIME_BACKEND_MODULE_RELATIVE.as_posix(),
        ONE_SHOT_ENTRYPOINT_RELATIVE.as_posix(),
        EXECUTION_WRAPPER_MODULE_RELATIVE.as_posix(),
        EXECUTION_WRAPPER_IMPLEMENTATION_RELATIVE.as_posix(),
        AUTHORIZATION_MODULE_RELATIVE.as_posix(),
        AUTHORIZATION_VERIFIER_RELATIVE.as_posix(),
        AUTHORIZATION_TEST_RELATIVE.as_posix(),
    }
)
_COMMIT_PATTERN: Final = re.compile(r"^[0-9a-f]{40}$")
_SHA256_PATTERN: Final = re.compile(r"^sha256:[0-9a-f]{64}$")

__all__ = [
    "AUTHORIZATION_RELATIVE",
    "AUTHORIZATION_ROOT_RELATIVE",
    "EXECUTION_LEASE_RELATIVE",
    "INVOCATION_AUTHORIZATION_ID",
    "INVOCATION_AUTHORIZATION_STATUS",
    "INVOCATION_OPERATOR_ACKNOWLEDGEMENT",
    "LEASE_OPERATOR_ACKNOWLEDGEMENT",
    "OneShotInvocationAuthorization",
    "QWakeLC4InvocationAuthorizationError",
    "canonical_json",
    "load_invocation_authorization",
    "sha256_object",
    "verify_invocation_authorization",
]


class QWakeLC4InvocationAuthorizationError(RuntimeError):
    """Raised when the one-shot invocation authorization fails closed."""


def canonical_json(value: object) -> str:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    )


def sha256_object(value: object) -> str:
    return "sha256:" + hashlib.sha256(
        canonical_json(value).encode("utf-8")
    ).hexdigest()


def _require_sha256(value: str, field_name: str) -> None:
    if _SHA256_PATTERN.fullmatch(value) is None:
        raise QWakeLC4InvocationAuthorizationError(
            f"{field_name} is not SHA-256"
        )


def _require_commit(value: str, field_name: str) -> None:
    if _COMMIT_PATTERN.fullmatch(value) is None:
        raise QWakeLC4InvocationAuthorizationError(
            f"{field_name} is not a commit"
        )


def _require_utc(value: str, field_name: str) -> datetime:
    if not value.endswith("Z"):
        raise QWakeLC4InvocationAuthorizationError(
            f"{field_name} is not UTC"
        )
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise QWakeLC4InvocationAuthorizationError(
            f"{field_name} is not an ISO timestamp"
        ) from exc
    if parsed.tzinfo != UTC:
        raise QWakeLC4InvocationAuthorizationError(
            f"{field_name} timezone differs"
        )
    return parsed


@dataclass(frozen=True)
class InvocationSourceIdentity:
    """Immutable artifacts bound by the invocation authorization."""

    post_merge_commit: str
    post_merge_parent_1: str
    post_merge_parent_2: str
    torch2pc_commit: str
    execution_freeze_id: str
    execution_freeze_file_sha256: str
    execution_freeze_package_registry_sha256: str
    execution_freeze_materialization_file_sha256: str
    execution_admission_id: str
    execution_admission_sha256: str
    execution_admission_file_sha256: str
    execution_admission_package_registry_sha256: str
    runtime_authorization_id: str
    runtime_authorization_sha256: str
    runtime_authorization_file_sha256: str
    runtime_authorization_package_registry_sha256: str
    authorized_cell_count: int
    reserve_probe_count: int
    image_tag: str
    image_digest: str
    image_repo_digest: str
    runtime_backend_module_path: str
    runtime_backend_module_sha256: str
    one_shot_entrypoint_path: str
    one_shot_entrypoint_sha256: str
    execution_wrapper_module_path: str
    execution_wrapper_module_sha256: str
    execution_wrapper_implementation_path: str
    execution_wrapper_implementation_sha256: str
    authorization_module_path: str
    authorization_module_sha256: str
    verifier_path: str
    verifier_sha256: str
    test_path: str
    test_sha256: str

    def require(self) -> None:
        exact: Mapping[str, object] = {
            "post_merge_commit": POST_MERGE_COMMIT,
            "post_merge_parent_1": POST_MERGE_PARENT_1,
            "post_merge_parent_2": POST_MERGE_PARENT_2,
            "torch2pc_commit": FROZEN_TORCH2PC_COMMIT,
            "execution_freeze_id": EXECUTION_FREEZE_ID,
            "execution_freeze_file_sha256": EXECUTION_FREEZE_FILE_SHA256,
            "execution_freeze_package_registry_sha256": (
                EXECUTION_FREEZE_PACKAGE_REGISTRY_SHA256
            ),
            "execution_freeze_materialization_file_sha256": (
                EXECUTION_FREEZE_MATERIALIZATION_FILE_SHA256
            ),
            "execution_admission_id": EXECUTION_ADMISSION_ID,
            "execution_admission_sha256": EXECUTION_ADMISSION_SHA256,
            "execution_admission_file_sha256": (
                EXECUTION_ADMISSION_FILE_SHA256
            ),
            "execution_admission_package_registry_sha256": (
                EXECUTION_ADMISSION_PACKAGE_REGISTRY_SHA256
            ),
            "runtime_authorization_id": RUNTIME_AUTHORIZATION_ID,
            "runtime_authorization_sha256": RUNTIME_AUTHORIZATION_SHA256,
            "runtime_authorization_file_sha256": (
                RUNTIME_AUTHORIZATION_FILE_SHA256
            ),
            "runtime_authorization_package_registry_sha256": (
                RUNTIME_AUTHORIZATION_PACKAGE_REGISTRY_SHA256
            ),
            "authorized_cell_count": 168,
            "reserve_probe_count": 28,
            "image_tag": IMAGE_TAG,
            "image_digest": IMAGE_DIGEST,
            "image_repo_digest": IMAGE_REPO_DIGEST,
            "runtime_backend_module_path": (
                RUNTIME_BACKEND_MODULE_RELATIVE.as_posix()
            ),
            "runtime_backend_module_sha256": (
                EXPECTED_RUNTIME_BACKEND_MODULE_SHA256
            ),
            "one_shot_entrypoint_path": (
                ONE_SHOT_ENTRYPOINT_RELATIVE.as_posix()
            ),
            "one_shot_entrypoint_sha256": (
                EXPECTED_ONE_SHOT_ENTRYPOINT_SHA256
            ),
            "execution_wrapper_module_path": (
                EXECUTION_WRAPPER_MODULE_RELATIVE.as_posix()
            ),
            "execution_wrapper_module_sha256": (
                EXPECTED_EXECUTION_WRAPPER_MODULE_SHA256
            ),
            "execution_wrapper_implementation_path": (
                EXECUTION_WRAPPER_IMPLEMENTATION_RELATIVE.as_posix()
            ),
            "execution_wrapper_implementation_sha256": (
                EXPECTED_EXECUTION_WRAPPER_IMPLEMENTATION_SHA256
            ),
            "authorization_module_path": (
                AUTHORIZATION_MODULE_RELATIVE.as_posix()
            ),
            "verifier_path": AUTHORIZATION_VERIFIER_RELATIVE.as_posix(),
            "test_path": AUTHORIZATION_TEST_RELATIVE.as_posix(),
        }
        for field_name, expected in exact.items():
            if getattr(self, field_name) != expected:
                raise QWakeLC4InvocationAuthorizationError(
                    f"source identity differs: {field_name}"
                )
        for field_name in (
            "post_merge_commit",
            "post_merge_parent_1",
            "post_merge_parent_2",
            "torch2pc_commit",
        ):
            _require_commit(str(getattr(self, field_name)), field_name)
        for field_name in (
            "execution_freeze_file_sha256",
            "execution_freeze_package_registry_sha256",
            "execution_freeze_materialization_file_sha256",
            "execution_admission_sha256",
            "execution_admission_file_sha256",
            "execution_admission_package_registry_sha256",
            "runtime_authorization_sha256",
            "runtime_authorization_file_sha256",
            "runtime_authorization_package_registry_sha256",
            "runtime_backend_module_sha256",
            "one_shot_entrypoint_sha256",
            "execution_wrapper_module_sha256",
            "execution_wrapper_implementation_sha256",
            "authorization_module_sha256",
            "verifier_sha256",
            "test_sha256",
        ):
            _require_sha256(str(getattr(self, field_name)), field_name)


@dataclass(frozen=True)
class InvocationContract:
    """Prospective one-shot invocation permissions without effects."""

    authorization_scope: str
    invocation_count: int
    output_root: str
    execution_lease_relative: str
    operator_acknowledgement: str
    lease_operator_acknowledgement: str
    exact_immutable_image_required: bool
    exact_execution_freeze_required: bool
    exact_matrix_authorization_required: bool
    claimed_at_utc_required_at_invocation: bool
    claim_and_execute_same_process_required: bool
    no_retry_after_claim_required: bool
    engineering_only: bool
    synthetic_data_only: bool
    future_lease_claim_permitted: bool
    future_one_shot_invocation_permitted: bool
    future_runtime_execution_permitted: bool

    def require(self) -> None:
        exact: Mapping[str, object] = {
            "authorization_scope": "single_engineering_invocation",
            "invocation_count": 1,
            "output_root": AUTHORIZED_OUTPUT_ROOT,
            "execution_lease_relative": EXECUTION_LEASE_RELATIVE.as_posix(),
            "operator_acknowledgement": (
                INVOCATION_OPERATOR_ACKNOWLEDGEMENT
            ),
            "lease_operator_acknowledgement": (
                LEASE_OPERATOR_ACKNOWLEDGEMENT
            ),
            "exact_immutable_image_required": True,
            "exact_execution_freeze_required": True,
            "exact_matrix_authorization_required": True,
            "claimed_at_utc_required_at_invocation": True,
            "claim_and_execute_same_process_required": True,
            "no_retry_after_claim_required": True,
            "engineering_only": True,
            "synthetic_data_only": True,
            "future_lease_claim_permitted": True,
            "future_one_shot_invocation_permitted": True,
            "future_runtime_execution_permitted": True,
        }
        for field_name, expected in exact.items():
            if getattr(self, field_name) != expected:
                raise QWakeLC4InvocationAuthorizationError(
                    f"invocation contract differs: {field_name}"
                )


@dataclass(frozen=True)
class InvocationGates:
    """Capability/effect split preserved by the authorization record."""

    invocation_authorization_record_present: bool
    one_shot_invocation_authorized: bool
    future_lease_claim_authorized: bool
    future_runtime_execution_authorized: bool
    branch_runtime_execution_permitted: bool
    execution_lease_materialized: bool
    authorization_consumed: bool
    runtime_execution_started: bool
    runtime_execution_performed: bool
    engineering_evidence_present: bool
    scientific_execution_open: bool
    test_dataset_access: bool
    publication_permitted: bool
    local_compute_execution_open: bool

    def require(self) -> None:
        for field_name in (
            "invocation_authorization_record_present",
            "one_shot_invocation_authorized",
            "future_lease_claim_authorized",
            "future_runtime_execution_authorized",
        ):
            if getattr(self, field_name) is not True:
                raise QWakeLC4InvocationAuthorizationError(
                    f"authorization capability is absent: {field_name}"
                )
        for field_name in (
            "branch_runtime_execution_permitted",
            "execution_lease_materialized",
            "authorization_consumed",
            "runtime_execution_started",
            "runtime_execution_performed",
            "engineering_evidence_present",
            "scientific_execution_open",
            "test_dataset_access",
            "publication_permitted",
            "local_compute_execution_open",
        ):
            if getattr(self, field_name) is not False:
                raise QWakeLC4InvocationAuthorizationError(
                    f"authorization effect is open: {field_name}"
                )


@dataclass(frozen=True)
class OneShotInvocationAuthorization:
    """Canonical authorization for one future engineering invocation."""

    schema_version: int
    authorization_id: str
    status: str
    issued_at_utc: str
    source: InvocationSourceIdentity
    contract: InvocationContract
    gates: InvocationGates
    next_slice: str
    post_merge_next_slice: str
    authorization_sha256: str

    def require(self) -> None:
        if self.schema_version != 1:
            raise QWakeLC4InvocationAuthorizationError(
                "unexpected invocation authorization schema"
            )
        if self.authorization_id != INVOCATION_AUTHORIZATION_ID:
            raise QWakeLC4InvocationAuthorizationError(
                "unexpected invocation authorization id"
            )
        if self.status != INVOCATION_AUTHORIZATION_STATUS:
            raise QWakeLC4InvocationAuthorizationError(
                "unexpected invocation authorization status"
            )
        issued = _require_utc(self.issued_at_utc, "issued_at_utc")
        merged = _require_utc(
            POST_MERGE_TIMESTAMP_UTC,
            "post_merge_timestamp_utc",
        )
        if issued < merged:
            raise QWakeLC4InvocationAuthorizationError(
                "invocation authorization predates the verified merge"
            )
        self.source.require()
        self.contract.require()
        self.gates.require()
        if self.next_slice != (
            "QW-LC4-E-one-shot-engineering-invocation-authorization-commit"
        ):
            raise QWakeLC4InvocationAuthorizationError(
                "invocation authorization next slice differs"
            )
        if self.post_merge_next_slice != (
            "QW-LC4-E-one-shot-engineering-invocation-wrapper"
        ):
            raise QWakeLC4InvocationAuthorizationError(
                "invocation authorization post-merge slice differs"
            )
        _require_sha256(
            self.authorization_sha256,
            "authorization_sha256",
        )
        if self.authorization_sha256 != sha256_object(
            self._payload_without_digest()
        ):
            raise QWakeLC4InvocationAuthorizationError(
                "invocation authorization digest differs"
            )

    def _payload_without_digest(self) -> Mapping[str, object]:
        payload = asdict(self)
        payload.pop("authorization_sha256")
        return cast(Mapping[str, object], payload)

    def canonical_json(self) -> str:
        return canonical_json(asdict(self))


def _as_object(value: object, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise QWakeLC4InvocationAuthorizationError(
            f"{field_name} is not an object"
        )
    return cast(dict[str, Any], value)


def _as_str(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise QWakeLC4InvocationAuthorizationError(
            f"{field_name} is not a string"
        )
    return value


def _as_int(value: object, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise QWakeLC4InvocationAuthorizationError(
            f"{field_name} is not an integer"
        )
    return value


def _as_bool(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise QWakeLC4InvocationAuthorizationError(
            f"{field_name} is not a boolean"
        )
    return value


def _load_source(value: object) -> InvocationSourceIdentity:
    payload = _as_object(value, "source")
    return InvocationSourceIdentity(
        post_merge_commit=_as_str(
            payload.get("post_merge_commit"),
            "source.post_merge_commit",
        ),
        post_merge_parent_1=_as_str(
            payload.get("post_merge_parent_1"),
            "source.post_merge_parent_1",
        ),
        post_merge_parent_2=_as_str(
            payload.get("post_merge_parent_2"),
            "source.post_merge_parent_2",
        ),
        torch2pc_commit=_as_str(
            payload.get("torch2pc_commit"),
            "source.torch2pc_commit",
        ),
        execution_freeze_id=_as_str(
            payload.get("execution_freeze_id"),
            "source.execution_freeze_id",
        ),
        execution_freeze_file_sha256=_as_str(
            payload.get("execution_freeze_file_sha256"),
            "source.execution_freeze_file_sha256",
        ),
        execution_freeze_package_registry_sha256=_as_str(
            payload.get("execution_freeze_package_registry_sha256"),
            "source.execution_freeze_package_registry_sha256",
        ),
        execution_freeze_materialization_file_sha256=_as_str(
            payload.get("execution_freeze_materialization_file_sha256"),
            "source.execution_freeze_materialization_file_sha256",
        ),
        execution_admission_id=_as_str(
            payload.get("execution_admission_id"),
            "source.execution_admission_id",
        ),
        execution_admission_sha256=_as_str(
            payload.get("execution_admission_sha256"),
            "source.execution_admission_sha256",
        ),
        execution_admission_file_sha256=_as_str(
            payload.get("execution_admission_file_sha256"),
            "source.execution_admission_file_sha256",
        ),
        execution_admission_package_registry_sha256=_as_str(
            payload.get("execution_admission_package_registry_sha256"),
            "source.execution_admission_package_registry_sha256",
        ),
        runtime_authorization_id=_as_str(
            payload.get("runtime_authorization_id"),
            "source.runtime_authorization_id",
        ),
        runtime_authorization_sha256=_as_str(
            payload.get("runtime_authorization_sha256"),
            "source.runtime_authorization_sha256",
        ),
        runtime_authorization_file_sha256=_as_str(
            payload.get("runtime_authorization_file_sha256"),
            "source.runtime_authorization_file_sha256",
        ),
        runtime_authorization_package_registry_sha256=_as_str(
            payload.get("runtime_authorization_package_registry_sha256"),
            "source.runtime_authorization_package_registry_sha256",
        ),
        authorized_cell_count=_as_int(
            payload.get("authorized_cell_count"),
            "source.authorized_cell_count",
        ),
        reserve_probe_count=_as_int(
            payload.get("reserve_probe_count"),
            "source.reserve_probe_count",
        ),
        image_tag=_as_str(
            payload.get("image_tag"),
            "source.image_tag",
        ),
        image_digest=_as_str(
            payload.get("image_digest"),
            "source.image_digest",
        ),
        image_repo_digest=_as_str(
            payload.get("image_repo_digest"),
            "source.image_repo_digest",
        ),
        runtime_backend_module_path=_as_str(
            payload.get("runtime_backend_module_path"),
            "source.runtime_backend_module_path",
        ),
        runtime_backend_module_sha256=_as_str(
            payload.get("runtime_backend_module_sha256"),
            "source.runtime_backend_module_sha256",
        ),
        one_shot_entrypoint_path=_as_str(
            payload.get("one_shot_entrypoint_path"),
            "source.one_shot_entrypoint_path",
        ),
        one_shot_entrypoint_sha256=_as_str(
            payload.get("one_shot_entrypoint_sha256"),
            "source.one_shot_entrypoint_sha256",
        ),
        execution_wrapper_module_path=_as_str(
            payload.get("execution_wrapper_module_path"),
            "source.execution_wrapper_module_path",
        ),
        execution_wrapper_module_sha256=_as_str(
            payload.get("execution_wrapper_module_sha256"),
            "source.execution_wrapper_module_sha256",
        ),
        execution_wrapper_implementation_path=_as_str(
            payload.get("execution_wrapper_implementation_path"),
            "source.execution_wrapper_implementation_path",
        ),
        execution_wrapper_implementation_sha256=_as_str(
            payload.get("execution_wrapper_implementation_sha256"),
            "source.execution_wrapper_implementation_sha256",
        ),
        authorization_module_path=_as_str(
            payload.get("authorization_module_path"),
            "source.authorization_module_path",
        ),
        authorization_module_sha256=_as_str(
            payload.get("authorization_module_sha256"),
            "source.authorization_module_sha256",
        ),
        verifier_path=_as_str(
            payload.get("verifier_path"),
            "source.verifier_path",
        ),
        verifier_sha256=_as_str(
            payload.get("verifier_sha256"),
            "source.verifier_sha256",
        ),
        test_path=_as_str(
            payload.get("test_path"),
            "source.test_path",
        ),
        test_sha256=_as_str(
            payload.get("test_sha256"),
            "source.test_sha256",
        ),
    )


def _load_contract(value: object) -> InvocationContract:
    payload = _as_object(value, "contract")
    return InvocationContract(
        authorization_scope=_as_str(
            payload.get("authorization_scope"),
            "contract.authorization_scope",
        ),
        invocation_count=_as_int(
            payload.get("invocation_count"),
            "contract.invocation_count",
        ),
        output_root=_as_str(
            payload.get("output_root"),
            "contract.output_root",
        ),
        execution_lease_relative=_as_str(
            payload.get("execution_lease_relative"),
            "contract.execution_lease_relative",
        ),
        operator_acknowledgement=_as_str(
            payload.get("operator_acknowledgement"),
            "contract.operator_acknowledgement",
        ),
        lease_operator_acknowledgement=_as_str(
            payload.get("lease_operator_acknowledgement"),
            "contract.lease_operator_acknowledgement",
        ),
        exact_immutable_image_required=_as_bool(
            payload.get("exact_immutable_image_required"),
            "contract.exact_immutable_image_required",
        ),
        exact_execution_freeze_required=_as_bool(
            payload.get("exact_execution_freeze_required"),
            "contract.exact_execution_freeze_required",
        ),
        exact_matrix_authorization_required=_as_bool(
            payload.get("exact_matrix_authorization_required"),
            "contract.exact_matrix_authorization_required",
        ),
        claimed_at_utc_required_at_invocation=_as_bool(
            payload.get("claimed_at_utc_required_at_invocation"),
            "contract.claimed_at_utc_required_at_invocation",
        ),
        claim_and_execute_same_process_required=_as_bool(
            payload.get("claim_and_execute_same_process_required"),
            "contract.claim_and_execute_same_process_required",
        ),
        no_retry_after_claim_required=_as_bool(
            payload.get("no_retry_after_claim_required"),
            "contract.no_retry_after_claim_required",
        ),
        engineering_only=_as_bool(
            payload.get("engineering_only"),
            "contract.engineering_only",
        ),
        synthetic_data_only=_as_bool(
            payload.get("synthetic_data_only"),
            "contract.synthetic_data_only",
        ),
        future_lease_claim_permitted=_as_bool(
            payload.get("future_lease_claim_permitted"),
            "contract.future_lease_claim_permitted",
        ),
        future_one_shot_invocation_permitted=_as_bool(
            payload.get("future_one_shot_invocation_permitted"),
            "contract.future_one_shot_invocation_permitted",
        ),
        future_runtime_execution_permitted=_as_bool(
            payload.get("future_runtime_execution_permitted"),
            "contract.future_runtime_execution_permitted",
        ),
    )


def _load_gates(value: object) -> InvocationGates:
    payload = _as_object(value, "gates")
    return InvocationGates(
        invocation_authorization_record_present=_as_bool(
            payload.get("invocation_authorization_record_present"),
            "gates.invocation_authorization_record_present",
        ),
        one_shot_invocation_authorized=_as_bool(
            payload.get("one_shot_invocation_authorized"),
            "gates.one_shot_invocation_authorized",
        ),
        future_lease_claim_authorized=_as_bool(
            payload.get("future_lease_claim_authorized"),
            "gates.future_lease_claim_authorized",
        ),
        future_runtime_execution_authorized=_as_bool(
            payload.get("future_runtime_execution_authorized"),
            "gates.future_runtime_execution_authorized",
        ),
        branch_runtime_execution_permitted=_as_bool(
            payload.get("branch_runtime_execution_permitted"),
            "gates.branch_runtime_execution_permitted",
        ),
        execution_lease_materialized=_as_bool(
            payload.get("execution_lease_materialized"),
            "gates.execution_lease_materialized",
        ),
        authorization_consumed=_as_bool(
            payload.get("authorization_consumed"),
            "gates.authorization_consumed",
        ),
        runtime_execution_started=_as_bool(
            payload.get("runtime_execution_started"),
            "gates.runtime_execution_started",
        ),
        runtime_execution_performed=_as_bool(
            payload.get("runtime_execution_performed"),
            "gates.runtime_execution_performed",
        ),
        engineering_evidence_present=_as_bool(
            payload.get("engineering_evidence_present"),
            "gates.engineering_evidence_present",
        ),
        scientific_execution_open=_as_bool(
            payload.get("scientific_execution_open"),
            "gates.scientific_execution_open",
        ),
        test_dataset_access=_as_bool(
            payload.get("test_dataset_access"),
            "gates.test_dataset_access",
        ),
        publication_permitted=_as_bool(
            payload.get("publication_permitted"),
            "gates.publication_permitted",
        ),
        local_compute_execution_open=_as_bool(
            payload.get("local_compute_execution_open"),
            "gates.local_compute_execution_open",
        ),
    )


def load_invocation_authorization(
    path: Path,
) -> OneShotInvocationAuthorization:
    """Load and validate one canonical invocation authorization record."""

    if not path.is_file() or path.is_symlink():
        raise QWakeLC4InvocationAuthorizationError(
            "invocation authorization record is absent"
        )
    try:
        raw = path.read_text(encoding="utf-8")
        value = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise QWakeLC4InvocationAuthorizationError(
            "invocation authorization JSON is invalid"
        ) from exc
    payload = _as_object(value, "authorization")
    authorization = OneShotInvocationAuthorization(
        schema_version=_as_int(
            payload.get("schema_version"),
            "schema_version",
        ),
        authorization_id=_as_str(
            payload.get("authorization_id"),
            "authorization_id",
        ),
        status=_as_str(payload.get("status"), "status"),
        issued_at_utc=_as_str(
            payload.get("issued_at_utc"),
            "issued_at_utc",
        ),
        source=_load_source(payload.get("source")),
        contract=_load_contract(payload.get("contract")),
        gates=_load_gates(payload.get("gates")),
        next_slice=_as_str(
            payload.get("next_slice"),
            "next_slice",
        ),
        post_merge_next_slice=_as_str(
            payload.get("post_merge_next_slice"),
            "post_merge_next_slice",
        ),
        authorization_sha256=_as_str(
            payload.get("authorization_sha256"),
            "authorization_sha256",
        ),
    )
    authorization.require()
    if raw != authorization.canonical_json():
        raise QWakeLC4InvocationAuthorizationError(
            "invocation authorization serialization differs"
        )
    return authorization


def _read_registry(path: Path) -> dict[str, str]:
    if not path.is_file() or path.is_symlink():
        raise QWakeLC4InvocationAuthorizationError(
            f"registry is absent: {path}"
        )
    result: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        digest, separator, relative = raw.partition("  ")
        if not separator or not relative or relative in result:
            raise QWakeLC4InvocationAuthorizationError(
                f"invalid registry line: {raw!r}"
            )
        if len(digest) != 64 or any(
            character not in "0123456789abcdef"
            for character in digest
        ):
            raise QWakeLC4InvocationAuthorizationError(
                "registry digest is not SHA-256"
            )
        result[relative] = "sha256:" + digest
    if not result:
        raise QWakeLC4InvocationAuthorizationError(
            "registry is empty"
        )
    return result


def _sha256_file(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise QWakeLC4InvocationAuthorizationError(
            f"regular file is absent: {path}"
        )
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _verify_registry(path: Path, base: Path) -> dict[str, str]:
    registry = _read_registry(path)
    for relative, expected in registry.items():
        actual = _sha256_file(base / relative)
        if actual != expected:
            raise QWakeLC4InvocationAuthorizationError(
                f"registry digest differs: {relative}"
            )
    return registry


def _verify_effect_boundary(root: Path) -> None:
    lease = root / EXECUTION_LEASE_RELATIVE
    output = root / AUTHORIZED_OUTPUT_ROOT
    if lease.exists() or lease.is_symlink():
        raise QWakeLC4InvocationAuthorizationError(
            "execution lease is already present"
        )
    if output.exists() or output.is_symlink():
        raise QWakeLC4InvocationAuthorizationError(
            "runtime output is already present"
        )
    output_parent = output.parent
    if output_parent.is_dir():
        remainders = tuple(
            output_parent.glob(f".{output.name}.staging-*")
        )
        if remainders:
            raise QWakeLC4InvocationAuthorizationError(
                "runtime staging remainder is present"
            )


def verify_invocation_authorization(
    project_root: Path,
) -> OneShotInvocationAuthorization:
    """Verify the exact authorization package without invoking runtime."""

    root = project_root.expanduser().resolve()
    package = root / AUTHORIZATION_ROOT_RELATIVE
    if not package.is_dir() or package.is_symlink():
        raise QWakeLC4InvocationAuthorizationError(
            "invocation authorization package is absent"
        )
    entries = tuple(package.iterdir())
    observed = {
        item.name
        for item in entries
        if item.is_file() and not item.is_symlink()
    }
    if observed != _EXPECTED_PACKAGE_FILES:
        raise QWakeLC4InvocationAuthorizationError(
            "invocation authorization package scope differs"
        )
    if any(item.is_dir() or item.is_symlink() for item in entries):
        raise QWakeLC4InvocationAuthorizationError(
            "invocation authorization package contains a non-regular entry"
        )

    package_registry = _verify_registry(
        root / AUTHORIZATION_REGISTRY_RELATIVE,
        package,
    )
    if set(package_registry) != _EXPECTED_PACKAGE_FILES - {"SHA256SUMS"}:
        raise QWakeLC4InvocationAuthorizationError(
            "invocation authorization package registry differs"
        )
    source_registry = _verify_registry(
        root / AUTHORIZATION_SOURCE_REGISTRY_RELATIVE,
        root,
    )
    if set(source_registry) != _EXPECTED_SOURCE_PATHS:
        raise QWakeLC4InvocationAuthorizationError(
            "invocation authorization source registry differs"
        )

    authorization = load_invocation_authorization(
        root / AUTHORIZATION_RELATIVE
    )
    source = authorization.source
    expected_source_hashes = {
        source.runtime_backend_module_path: (
            source.runtime_backend_module_sha256
        ),
        source.one_shot_entrypoint_path: (
            source.one_shot_entrypoint_sha256
        ),
        source.execution_wrapper_module_path: (
            source.execution_wrapper_module_sha256
        ),
        source.execution_wrapper_implementation_path: (
            source.execution_wrapper_implementation_sha256
        ),
        source.authorization_module_path: (
            source.authorization_module_sha256
        ),
        source.verifier_path: source.verifier_sha256,
        source.test_path: source.test_sha256,
    }
    for relative, expected in expected_source_hashes.items():
        if source_registry.get(relative) != expected:
            raise QWakeLC4InvocationAuthorizationError(
                f"source registry binding differs: {relative}"
            )

    exact_existing = {
        EXECUTION_FREEZE_RELATIVE.as_posix(): (
            EXECUTION_FREEZE_FILE_SHA256
        ),
        EXECUTION_FREEZE_REGISTRY_RELATIVE.as_posix(): (
            EXECUTION_FREEZE_PACKAGE_REGISTRY_SHA256
        ),
        EXECUTION_FREEZE_MATERIALIZATION_RELATIVE.as_posix(): (
            EXECUTION_FREEZE_MATERIALIZATION_FILE_SHA256
        ),
        EXECUTION_ADMISSION_RELATIVE.as_posix(): (
            EXECUTION_ADMISSION_FILE_SHA256
        ),
        EXECUTION_ADMISSION_REGISTRY_RELATIVE.as_posix(): (
            EXECUTION_ADMISSION_PACKAGE_REGISTRY_SHA256
        ),
        RUNTIME_AUTHORIZATION_RELATIVE.as_posix(): (
            RUNTIME_AUTHORIZATION_FILE_SHA256
        ),
        RUNTIME_AUTHORIZATION_REGISTRY_RELATIVE.as_posix(): (
            RUNTIME_AUTHORIZATION_PACKAGE_REGISTRY_SHA256
        ),
    }
    for relative, expected in exact_existing.items():
        if source_registry.get(relative) != expected:
            raise QWakeLC4InvocationAuthorizationError(
                f"frozen source binding differs: {relative}"
            )

    _verify_effect_boundary(root)
    return authorization
