"""Fail-closed admission for one future QW-LC4-E host invocation.

The admission binds the independently verified host-runtime-invoker repository
freeze, the existing one-shot authorization, and the exact bounded invoker
implementation.  Verification is read-only.  This module does not inspect a
Docker image, materialize a runtime command, spawn a process, claim an execution
lease, execute the backend, write output, access a dataset, or publish evidence.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Final, cast

from torch2pc_thesis.stage3b_qwake_lc4_host_runtime_invoker_implementation import (
    build_host_runtime_invoker_implementation_state,
)
from torch2pc_thesis.stage3b_qwake_lc4_invocation_authorization import (
    AUTHORIZED_OUTPUT_ROOT,
    EXECUTION_LEASE_RELATIVE,
    verify_invocation_authorization,
)

INVOCATION_ADMISSION_ID: Final = (
    "stage3b-qwake-lc4-e-one-shot-engineering-invocation-admission-v1"
)
INVOCATION_ADMISSION_STATUS: Final = (
    "one_shot_engineering_invocation_admission_materialized_execution_closed"
)
INVOCATION_OPERATOR_ACKNOWLEDGEMENT: Final = (
    "ADMIT_QWAKE_LC4_ONE_SHOT_ENGINEERING_INVOCATION_FROM_VERIFIED_"
    "HOST_INVOKER_FREEZE"
)

INVOCATION_BASE_COMMIT: Final = (
    "3454d12d3cc16c9c50977e2a598e2bc1a8768441"
)
REPOSITORY_FREEZE_HEAD: Final = (
    "cc287334a325f460555bab06725c52ba548985eb"
)
REPOSITORY_FREEZE_PARENT: Final = (
    "da51c8d858c541372525125640db99062041fc20"
)
REPOSITORY_FREEZE_MERGED_AT_UTC: Final = "2026-07-29T16:52:51Z"
REPOSITORY_FREEZE_PR_NUMBER: Final = 137
REPOSITORY_FREEZE_RECEIPT_SHA256: Final = (
    "sha256:6485bd00335fe88e961dc9aa23daf0d27c0cbaa4fc4963af7a463b1ab9c3af58"
)
REPOSITORY_FREEZE_REGISTRY_SHA256: Final = (
    "sha256:14db12de0adfb302356dd081c1492ccfc6398c7627daf201ad84d4477f7ab6f6"
)

INVOCATION_AUTHORIZATION_ID: Final = (
    "stage3b-qwake-lc4-e-one-shot-engineering-invocation-authorization-v1"
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

HOST_RUNTIME_INVOKER_IMPLEMENTATION_ID: Final = (
    "stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-implementation-v1"
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
IMAGE_REPO_DIGEST: Final = (
    "torch2pc-layerwise-thesis@sha256:"
    "7da92b8f77f6dc37d42db832c5613ef6149dc488adc5b66465faa33e48ca021d"
)

PACKAGE_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-one-shot-engineering-invocation-admission-v1"
)
RECORD_RELATIVE: Final = PACKAGE_RELATIVE / "admission.json"
REGISTRY_RELATIVE: Final = PACKAGE_RELATIVE / "SHA256SUMS"
FREEZE_RECEIPT_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-repository-freeze-v1/"
    "receipt.json"
)
FREEZE_REGISTRY_RELATIVE: Final = FREEZE_RECEIPT_RELATIVE.with_name(
    "SHA256SUMS"
)
AUTHORIZATION_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-one-shot-engineering-invocation-authorization-v1/"
    "authorization.json"
)
AUTHORIZATION_REGISTRY_RELATIVE: Final = AUTHORIZATION_RELATIVE.with_name(
    "SHA256SUMS"
)
AUTHORIZATION_SOURCE_REGISTRY_RELATIVE: Final = (
    AUTHORIZATION_RELATIVE.with_name("source-SHA256SUMS")
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

_EXPECTED_PACKAGE_FILES: Final = frozenset({"SHA256SUMS", "admission.json"})
_COMMIT_PATTERN: Final = re.compile(r"^[0-9a-f]{40}$")
_SHA256_PATTERN: Final = re.compile(r"^sha256:[0-9a-f]{64}$")

__all__ = [
    "IMAGE_REPO_DIGEST",
    "INVOCATION_ADMISSION_ID",
    "INVOCATION_ADMISSION_STATUS",
    "INVOCATION_BASE_COMMIT",
    "INVOCATION_OPERATOR_ACKNOWLEDGEMENT",
    "OneShotEngineeringInvocationAdmission",
    "QWakeLC4EngineeringInvocationAdmissionError",
    "canonical_json",
    "load_engineering_invocation_admission",
    "sha256_object",
    "verify_engineering_invocation_admission",
]


class QWakeLC4EngineeringInvocationAdmissionError(RuntimeError):
    """Raised when the one-shot invocation admission fails closed."""


@dataclass(frozen=True)
class InvocationAdmissionSource:
    """Exact immutable identities required before the future invocation."""

    invocation_base_commit: str
    repository_freeze_head: str
    repository_freeze_parent: str
    repository_freeze_merged_at_utc: str
    repository_freeze_pr_number: int
    repository_freeze_receipt_sha256: str
    repository_freeze_registry_sha256: str
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
            "invocation_base_commit": INVOCATION_BASE_COMMIT,
            "repository_freeze_head": REPOSITORY_FREEZE_HEAD,
            "repository_freeze_parent": REPOSITORY_FREEZE_PARENT,
            "repository_freeze_merged_at_utc": (
                REPOSITORY_FREEZE_MERGED_AT_UTC
            ),
            "repository_freeze_pr_number": REPOSITORY_FREEZE_PR_NUMBER,
            "repository_freeze_receipt_sha256": (
                REPOSITORY_FREEZE_RECEIPT_SHA256
            ),
            "repository_freeze_registry_sha256": (
                REPOSITORY_FREEZE_REGISTRY_SHA256
            ),
            "invocation_authorization_id": INVOCATION_AUTHORIZATION_ID,
            "invocation_authorization_sha256": (
                INVOCATION_AUTHORIZATION_SHA256
            ),
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
                raise QWakeLC4EngineeringInvocationAdmissionError(
                    f"invocation admission source differs: {field_name}"
                )
        for field_name in (
            "invocation_base_commit",
            "repository_freeze_head",
            "repository_freeze_parent",
            "torch2pc_commit",
        ):
            _require_commit(str(observed[field_name]), field_name)
        for field_name, value in observed.items():
            if field_name.endswith("_sha256"):
                _require_sha256(str(value), field_name)


@dataclass(frozen=True)
class InvocationAdmissionChecks:
    """Static checks implemented before a separately authorized operation."""

    repository_freeze_complete: bool
    invocation_authorization_present: bool
    invocation_authorization_unconsumed: bool
    host_runtime_invoker_present: bool
    host_runtime_invoker_executable: bool
    exact_argv_required: bool
    shell_interpretation_forbidden: bool
    subprocess_popen_call_limit: int
    immutable_image_inspection_required_at_invocation: bool
    host_resource_validation_required_at_invocation: bool
    execution_lease_absence_required_at_invocation: bool
    output_absence_required_at_invocation: bool
    runtime_staging_absence_required_at_invocation: bool
    preexecution_identity_checks_implemented: bool
    preexecution_identity_verified: bool

    def require(self) -> None:
        required_true = (
            self.repository_freeze_complete,
            self.invocation_authorization_present,
            self.invocation_authorization_unconsumed,
            self.host_runtime_invoker_present,
            self.host_runtime_invoker_executable,
            self.exact_argv_required,
            self.shell_interpretation_forbidden,
            self.immutable_image_inspection_required_at_invocation,
            self.host_resource_validation_required_at_invocation,
            self.execution_lease_absence_required_at_invocation,
            self.output_absence_required_at_invocation,
            self.runtime_staging_absence_required_at_invocation,
            self.preexecution_identity_checks_implemented,
        )
        if not all(required_true):
            raise QWakeLC4EngineeringInvocationAdmissionError(
                "required pre-execution check is absent"
            )
        if self.subprocess_popen_call_limit != 1:
            raise QWakeLC4EngineeringInvocationAdmissionError(
                "host process-spawn limit differs"
            )
        if self.preexecution_identity_verified:
            raise QWakeLC4EngineeringInvocationAdmissionError(
                "runtime pre-execution identity was verified during authoring"
            )


@dataclass(frozen=True)
class InvocationAdmissionGates:
    """Closed effect boundary of the authoring slice."""

    invocation_admission_record_present: bool
    one_shot_engineering_invocation_slice_open: bool
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
    docker_run_performed: bool
    local_compute_execution_open: bool

    def require(self) -> None:
        if not (
            self.invocation_admission_record_present
            and self.one_shot_engineering_invocation_slice_open
        ):
            raise QWakeLC4EngineeringInvocationAdmissionError(
                "invocation admission authoring boundary is absent"
            )
        forbidden = (
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
            self.docker_run_performed,
            self.local_compute_execution_open,
        )
        if any(forbidden):
            raise QWakeLC4EngineeringInvocationAdmissionError(
                "invocation admission authoring opened a runtime effect"
            )


@dataclass(frozen=True)
class OneShotEngineeringInvocationAdmission:
    """Canonical prospective admission for one future operator operation."""

    schema_version: int
    admission_id: str
    status: str
    recorded_at_utc: str
    operator_acknowledgement: str
    source: InvocationAdmissionSource
    checks: InvocationAdmissionChecks
    gates: InvocationAdmissionGates
    next_slice: str
    post_merge_next_slice: str
    admission_sha256: str

    def require(self) -> None:
        if self.schema_version != 1:
            raise QWakeLC4EngineeringInvocationAdmissionError(
                "unexpected invocation admission schema"
            )
        if self.admission_id != INVOCATION_ADMISSION_ID:
            raise QWakeLC4EngineeringInvocationAdmissionError(
                "unexpected invocation admission id"
            )
        if self.status != INVOCATION_ADMISSION_STATUS:
            raise QWakeLC4EngineeringInvocationAdmissionError(
                "unexpected invocation admission status"
            )
        _require_utc(self.recorded_at_utc)
        if self.operator_acknowledgement != INVOCATION_OPERATOR_ACKNOWLEDGEMENT:
            raise QWakeLC4EngineeringInvocationAdmissionError(
                "invocation operator acknowledgement differs"
            )
        self.source.require()
        self.checks.require()
        self.gates.require()
        if self.next_slice != (
            "QW-LC4-E-one-shot-engineering-invocation-admission-commit"
        ):
            raise QWakeLC4EngineeringInvocationAdmissionError(
                "invocation admission next slice differs"
            )
        if self.post_merge_next_slice != (
            "QW-LC4-E-one-shot-engineering-invocation-operation"
        ):
            raise QWakeLC4EngineeringInvocationAdmissionError(
                "invocation admission post-merge slice differs"
            )
        _require_sha256(self.admission_sha256, "admission_sha256")
        if self.admission_sha256 != sha256_object(
            self._payload_without_digest()
        ):
            raise QWakeLC4EngineeringInvocationAdmissionError(
                "invocation admission semantic digest differs"
            )

    def _payload_without_digest(self) -> Mapping[str, object]:
        payload = asdict(self)
        payload.pop("admission_sha256")
        return cast(Mapping[str, object], payload)

    def canonical_json(self) -> str:
        return canonical_json(asdict(self))


def canonical_json(value: object) -> str:
    """Return canonical UTF-8 JSON with one terminal newline."""

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ) + "\n"


def sha256_object(value: object) -> str:
    """Hash canonical JSON without a terminal formatting ambiguity."""

    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def load_engineering_invocation_admission(
    path: Path,
) -> OneShotEngineeringInvocationAdmission:
    """Load a canonical invocation admission from disk."""

    raw = _read_json_object(path)
    source = InvocationAdmissionSource(**_as_dict(raw.pop("source"), "source"))
    checks = InvocationAdmissionChecks(**_as_dict(raw.pop("checks"), "checks"))
    gates = InvocationAdmissionGates(**_as_dict(raw.pop("gates"), "gates"))
    admission = OneShotEngineeringInvocationAdmission(
        source=source,
        checks=checks,
        gates=gates,
        **cast(Any, raw),
    )
    admission.require()
    if path.read_text(encoding="utf-8", errors="strict") != (
        admission.canonical_json()
    ):
        raise QWakeLC4EngineeringInvocationAdmissionError(
            "invocation admission JSON is not canonical"
        )
    return admission


def verify_engineering_invocation_admission(
    project_root: Path,
) -> OneShotEngineeringInvocationAdmission:
    """Verify exact identities and absence of effects without invocation."""

    root = project_root.expanduser().resolve()
    _require_effect_boundary_closed(root)
    _verify_package(root)
    admission = load_engineering_invocation_admission(root / RECORD_RELATIVE)

    authorization = verify_invocation_authorization(root)
    if authorization.authorization_id != INVOCATION_AUTHORIZATION_ID:
        raise QWakeLC4EngineeringInvocationAdmissionError(
            "invocation authorization id differs"
        )
    if authorization.authorization_sha256 != INVOCATION_AUTHORIZATION_SHA256:
        raise QWakeLC4EngineeringInvocationAdmissionError(
            "invocation authorization semantic digest differs"
        )

    invoker_state = build_host_runtime_invoker_implementation_state(root)
    if invoker_state.state_sha256 != (
        HOST_RUNTIME_INVOKER_IMPLEMENTATION_STATE_SHA256
    ):
        raise QWakeLC4EngineeringInvocationAdmissionError(
            "host-runtime-invoker implementation state differs"
        )

    exact_files: Mapping[Path, str] = {
        FREEZE_RECEIPT_RELATIVE: REPOSITORY_FREEZE_RECEIPT_SHA256,
        FREEZE_REGISTRY_RELATIVE: REPOSITORY_FREEZE_REGISTRY_SHA256,
        AUTHORIZATION_RELATIVE: INVOCATION_AUTHORIZATION_FILE_SHA256,
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
            raise QWakeLC4EngineeringInvocationAdmissionError(
                f"pre-execution source SHA-256 differs: {relative}"
            )

    freeze = _read_json_object(root / FREEZE_RECEIPT_RELATIVE)
    expected_freeze: Mapping[str, object] = {
        "implementation_merge_commit": REPOSITORY_FREEZE_PARENT,
        "implementation_head_commit": (
            "181abda36465d3a91db5970e684938266200a798"
        ),
        "host_runtime_invoker_contract_sha256": (
            HOST_RUNTIME_INVOKER_CONTRACT_SHA256
        ),
        "implementation_state_sha256": (
            HOST_RUNTIME_INVOKER_IMPLEMENTATION_STATE_SHA256
        ),
        "repository_freeze_materialized": True,
        "one_shot_engineering_invocation_permitted": False,
        "execution_lease_materialized": False,
        "authorization_consumed": False,
        "runtime_execution_started": False,
        "runtime_execution_performed": False,
        "image_inspection_performed": False,
        "docker_run_performed": False,
        "local_compute_execution_open": False,
    }
    for field_name, expected_value in expected_freeze.items():
        if freeze.get(field_name) != expected_value:
            raise QWakeLC4EngineeringInvocationAdmissionError(
                f"repository-freeze receipt differs: {field_name}"
            )

    implementation = _read_json_object(root / INVOKER_RECORD_RELATIVE)
    if implementation.get("implementation_id") != (
        HOST_RUNTIME_INVOKER_IMPLEMENTATION_ID
    ):
        raise QWakeLC4EngineeringInvocationAdmissionError(
            "host-runtime-invoker implementation id differs"
        )
    contracts = _as_mapping(
        implementation.get("contracts"),
        "host-runtime-invoker contracts",
    )
    gates = _as_mapping(
        implementation.get("gates"),
        "host-runtime-invoker gates",
    )
    expected_contracts: Mapping[str, object] = {
        "implementation_state_sha256": (
            HOST_RUNTIME_INVOKER_IMPLEMENTATION_STATE_SHA256
        ),
        "exact_argv_only": True,
        "shell_interpretation_forbidden": True,
        "subprocess_popen_call_limit": 1,
        "prelaunch_image_inspection_count": 2,
        "prelaunch_materialization_count": 2,
        "host_execution_lease_write_forbidden": True,
    }
    for field_name, expected_value in expected_contracts.items():
        if contracts.get(field_name) != expected_value:
            raise QWakeLC4EngineeringInvocationAdmissionError(
                f"host-runtime-invoker contract differs: {field_name}"
            )
    for field_name, expected_value in {
        "host_runtime_invoker_present": True,
        "host_runtime_invoker_executable": True,
        "host_docker_run_implemented": True,
        "branch_runtime_execution_permitted": False,
        "execution_lease_materialized": False,
        "authorization_consumed": False,
        "runtime_execution_started": False,
        "runtime_execution_performed": False,
        "local_compute_execution_open": False,
    }.items():
        if gates.get(field_name) != expected_value:
            raise QWakeLC4EngineeringInvocationAdmissionError(
                f"host-runtime-invoker gate differs: {field_name}"
            )

    admission.require()
    return admission


def _verify_package(root: Path) -> None:
    package = root / PACKAGE_RELATIVE
    if not package.is_dir() or package.is_symlink():
        raise QWakeLC4EngineeringInvocationAdmissionError(
            "invocation admission package is absent"
        )
    entries = tuple(package.iterdir())
    observed = {
        item.name
        for item in entries
        if item.is_file() and not item.is_symlink()
    }
    if observed != _EXPECTED_PACKAGE_FILES:
        raise QWakeLC4EngineeringInvocationAdmissionError(
            "invocation admission package scope differs"
        )
    if any(item.is_dir() or item.is_symlink() for item in entries):
        raise QWakeLC4EngineeringInvocationAdmissionError(
            "invocation admission package contains a non-regular entry"
        )
    line = (root / REGISTRY_RELATIVE).read_text(
        encoding="utf-8", errors="strict"
    )
    expected_line = (
        _sha256_file(root / RECORD_RELATIVE).removeprefix("sha256:")
        + "  admission.json\n"
    )
    if line != expected_line:
        raise QWakeLC4EngineeringInvocationAdmissionError(
            "invocation admission package registry differs"
        )


def _require_effect_boundary_closed(root: Path) -> None:
    lease = root / EXECUTION_LEASE_RELATIVE
    output = root / AUTHORIZED_OUTPUT_ROOT
    if lease.exists() or lease.is_symlink():
        raise QWakeLC4EngineeringInvocationAdmissionError(
            "execution lease is already present"
        )
    if output.exists() or output.is_symlink():
        raise QWakeLC4EngineeringInvocationAdmissionError(
            "runtime output is already present"
        )
    if output.parent.is_dir() and tuple(
        output.parent.glob(f".{output.name}.staging-*")
    ):
        raise QWakeLC4EngineeringInvocationAdmissionError(
            "runtime staging remainder is present"
        )


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8", errors="strict"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise QWakeLC4EngineeringInvocationAdmissionError(
            f"cannot read JSON object: {path}"
        ) from exc
    if not isinstance(raw, dict):
        raise QWakeLC4EngineeringInvocationAdmissionError(
            f"JSON value is not an object: {path}"
        )
    return cast(dict[str, Any], raw)


def _as_dict(value: object, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise QWakeLC4EngineeringInvocationAdmissionError(
            f"{field_name} is not an object"
        )
    return cast(dict[str, Any], value)


def _as_mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise QWakeLC4EngineeringInvocationAdmissionError(
            f"{field_name} is not an object"
        )
    return cast(Mapping[str, object], value)


def _sha256_file(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise QWakeLC4EngineeringInvocationAdmissionError(
            f"required regular file is absent: {path}"
        )
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _require_commit(value: str, field_name: str) -> None:
    if not _COMMIT_PATTERN.fullmatch(value):
        raise QWakeLC4EngineeringInvocationAdmissionError(
            f"{field_name} is not a canonical commit"
        )


def _require_sha256(value: str, field_name: str) -> None:
    if not _SHA256_PATTERN.fullmatch(value):
        raise QWakeLC4EngineeringInvocationAdmissionError(
            f"{field_name} is not a canonical SHA-256"
        )


def _require_utc(value: str) -> None:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value):
        raise QWakeLC4EngineeringInvocationAdmissionError(
            "recorded_at_utc is not canonical UTC"
        )
