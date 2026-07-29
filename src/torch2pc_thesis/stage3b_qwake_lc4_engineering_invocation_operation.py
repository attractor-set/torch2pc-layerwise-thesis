"""Effect-free operation record for one future QW-LC4-E invocation.

The module binds the independently merged invocation admission to the exact
one-shot authorization, immutable image, Torch2PC revision, and bounded host
runtime invoker.  Verification is read-only.  It does not inspect a Docker
image, materialize a runtime command, spawn a process, claim an execution
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

from torch2pc_thesis.stage3b_qwake_lc4_engineering_invocation_admission import (
    INVOCATION_ADMISSION_ID,
    INVOCATION_AUTHORIZATION_FILE_SHA256,
    INVOCATION_AUTHORIZATION_ID,
    INVOCATION_AUTHORIZATION_REGISTRY_SHA256,
    INVOCATION_AUTHORIZATION_SHA256,
    INVOCATION_AUTHORIZATION_SOURCE_REGISTRY_SHA256,
    INVOCATION_OPERATOR_ACKNOWLEDGEMENT,
    verify_engineering_invocation_admission,
)
from torch2pc_thesis.stage3b_qwake_lc4_host_runtime_invoker_implementation import (
    HOST_RUNTIME_INVOKER_IMPLEMENTATION_ID,
    build_host_runtime_invoker_implementation_state,
)
from torch2pc_thesis.stage3b_qwake_lc4_invocation_authorization import (
    AUTHORIZED_OUTPUT_ROOT,
    EXECUTION_LEASE_RELATIVE,
    LEASE_OPERATOR_ACKNOWLEDGEMENT,
    verify_invocation_authorization,
)

INVOCATION_OPERATION_ID: Final = (
    "stage3b-qwake-lc4-e-one-shot-engineering-invocation-operation-v1"
)
INVOCATION_OPERATION_STATUS: Final = (
    "one_shot_engineering_invocation_operation_materialized_execution_closed"
)
OPERATION_AUTHORING_ACKNOWLEDGEMENT: Final = (
    "PREPARE_QWAKE_LC4_ONE_SHOT_ENGINEERING_INVOCATION_FROM_MERGED_ADMISSION"
)

OPERATION_BASE_COMMIT: Final = (
    "28be77706bc86abaf34f86e9bdcbdcb9cc2810a8"
)
ADMISSION_HEAD_COMMIT: Final = (
    "a26419057c133972b18a728575426ef510bcf360"
)
ADMISSION_PARENT_COMMIT: Final = (
    "3454d12d3cc16c9c50977e2a598e2bc1a8768441"
)
ADMISSION_MERGED_AT_UTC: Final = "2026-07-29T18:08:53Z"
ADMISSION_PR_NUMBER: Final = 138
ADMISSION_SHA256: Final = (
    "sha256:fe07bc20bf5866d84730df945c2ababc7b5f4f255648c5de6e3185ba4e37c01d"
)
ADMISSION_FILE_SHA256: Final = (
    "sha256:319f415265d041d883c3980f884dcb736f6f236a90ed3777c65e1ae10b7c9bba"
)
ADMISSION_REGISTRY_SHA256: Final = (
    "sha256:bc4bacb646759e8fa42caf336229a647e7a6d87a9ba292faf38ca9055b3b6ac2"
)
ADMISSION_MODULE_SHA256: Final = (
    "sha256:53264f77a5e72fa4933f0a68825c07dcde01b7e2d362de0cba1b4394113c436f"
)
ADMISSION_VERIFIER_SHA256: Final = (
    "sha256:06f61646988f7798cc57a47796fe0d5f4fff12f3d2fe4c5536b8f64617cd2148"
)
ADMISSION_TEST_SHA256: Final = (
    "sha256:ff9841329831bbfe84fb0fa571ef5f1a6ab6209b97a4e20f51a1ee68bd4f5b3f"
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

REQUIRED_HOST_RESOURCE_KEYS: Final = (
    "HOST_UID",
    "HOST_GID",
    "VIDEO_GID",
    "RENDER_GID",
    "HIP_VISIBLE_DEVICES",
    "CPUSET_GPU",
    "MEM_LIMIT",
    "SHM_SIZE",
    "TMPFS_SIZE",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)

PACKAGE_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-one-shot-engineering-invocation-operation-v1"
)
RECORD_RELATIVE: Final = PACKAGE_RELATIVE / "operation.json"
REGISTRY_RELATIVE: Final = PACKAGE_RELATIVE / "SHA256SUMS"
ADMISSION_RECORD_RELATIVE: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-one-shot-engineering-invocation-admission-v1/"
    "admission.json"
)
ADMISSION_REGISTRY_RELATIVE: Final = ADMISSION_RECORD_RELATIVE.with_name(
    "SHA256SUMS"
)
ADMISSION_MODULE_RELATIVE: Final = Path(
    "src/torch2pc_thesis/"
    "stage3b_qwake_lc4_engineering_invocation_admission.py"
)
ADMISSION_VERIFIER_RELATIVE: Final = Path(
    "scripts/verify_stage3b_qwake_lc4_engineering_invocation_admission.py"
)
ADMISSION_TEST_RELATIVE: Final = Path(
    "tests/unit/test_stage3b_qwake_lc4_engineering_invocation_admission.py"
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

_EXPECTED_PACKAGE_FILES: Final = frozenset({"SHA256SUMS", "operation.json"})
_COMMIT_PATTERN: Final = re.compile(r"^[0-9a-f]{40}$")
_SHA256_PATTERN: Final = re.compile(r"^sha256:[0-9a-f]{64}$")

__all__ = [
    "INVOCATION_OPERATION_ID",
    "INVOCATION_OPERATION_STATUS",
    "OPERATION_BASE_COMMIT",
    "OneShotEngineeringInvocationOperation",
    "QWakeLC4EngineeringInvocationOperationError",
    "canonical_json",
    "load_engineering_invocation_operation",
    "sha256_object",
    "verify_engineering_invocation_operation",
]


class QWakeLC4EngineeringInvocationOperationError(RuntimeError):
    """Raised when the prospective invocation operation fails closed."""


@dataclass(frozen=True)
class InvocationOperationSource:
    """Exact merged identities required by the future execution operation."""

    operation_base_commit: str
    admission_id: str
    admission_head_commit: str
    admission_parent_commit: str
    admission_merged_at_utc: str
    admission_pr_number: int
    admission_sha256: str
    admission_file_sha256: str
    admission_registry_sha256: str
    admission_module_sha256: str
    admission_verifier_sha256: str
    admission_test_sha256: str
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
            "operation_base_commit": OPERATION_BASE_COMMIT,
            "admission_id": INVOCATION_ADMISSION_ID,
            "admission_head_commit": ADMISSION_HEAD_COMMIT,
            "admission_parent_commit": ADMISSION_PARENT_COMMIT,
            "admission_merged_at_utc": ADMISSION_MERGED_AT_UTC,
            "admission_pr_number": ADMISSION_PR_NUMBER,
            "admission_sha256": ADMISSION_SHA256,
            "admission_file_sha256": ADMISSION_FILE_SHA256,
            "admission_registry_sha256": ADMISSION_REGISTRY_SHA256,
            "admission_module_sha256": ADMISSION_MODULE_SHA256,
            "admission_verifier_sha256": ADMISSION_VERIFIER_SHA256,
            "admission_test_sha256": ADMISSION_TEST_SHA256,
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
                raise QWakeLC4EngineeringInvocationOperationError(
                    f"invocation operation source differs: {field_name}"
                )
        for field_name in (
            "operation_base_commit",
            "admission_head_commit",
            "admission_parent_commit",
            "torch2pc_commit",
        ):
            _require_commit(str(observed[field_name]), field_name)
        for field_name, value in observed.items():
            if field_name.endswith("_sha256"):
                _require_sha256(str(value), field_name)


@dataclass(frozen=True)
class InvocationOperationChecks:
    """Checks that the later effectful execution must complete atomically."""

    invocation_admission_complete: bool
    exact_operation_base_required_at_execution: bool
    exact_host_resources_required_at_execution: bool
    required_host_resource_keys: tuple[str, ...]
    claimed_at_utc_required_at_execution: bool
    invocation_operator_acknowledgement_required_at_execution: bool
    lease_operator_acknowledgement_required_at_execution: bool
    immutable_image_inspection_count_required: int
    invocation_materialization_count_required: int
    canonical_argv_equality_required: bool
    authorization_unconsumed_required_at_execution: bool
    execution_lease_absence_required_at_execution: bool
    output_absence_required_at_execution: bool
    runtime_staging_absence_required_at_execution: bool
    subprocess_popen_call_limit: int
    shell_interpretation_forbidden: bool
    no_retry_after_spawn_required: bool
    host_execution_lease_write_forbidden: bool
    preexecution_identity_checks_implemented: bool
    preexecution_identity_verified: bool

    def require(self) -> None:
        required_true = (
            self.invocation_admission_complete,
            self.exact_operation_base_required_at_execution,
            self.exact_host_resources_required_at_execution,
            self.claimed_at_utc_required_at_execution,
            self.invocation_operator_acknowledgement_required_at_execution,
            self.lease_operator_acknowledgement_required_at_execution,
            self.canonical_argv_equality_required,
            self.authorization_unconsumed_required_at_execution,
            self.execution_lease_absence_required_at_execution,
            self.output_absence_required_at_execution,
            self.runtime_staging_absence_required_at_execution,
            self.shell_interpretation_forbidden,
            self.no_retry_after_spawn_required,
            self.host_execution_lease_write_forbidden,
            self.preexecution_identity_checks_implemented,
        )
        if not all(required_true):
            raise QWakeLC4EngineeringInvocationOperationError(
                "required invocation operation check is absent"
            )
        if self.required_host_resource_keys != REQUIRED_HOST_RESOURCE_KEYS:
            raise QWakeLC4EngineeringInvocationOperationError(
                "required host-resource key set differs"
            )
        if self.immutable_image_inspection_count_required != 2:
            raise QWakeLC4EngineeringInvocationOperationError(
                "image inspection count differs"
            )
        if self.invocation_materialization_count_required != 2:
            raise QWakeLC4EngineeringInvocationOperationError(
                "invocation materialization count differs"
            )
        if self.subprocess_popen_call_limit != 1:
            raise QWakeLC4EngineeringInvocationOperationError(
                "host process-spawn limit differs"
            )
        if self.preexecution_identity_verified:
            raise QWakeLC4EngineeringInvocationOperationError(
                "runtime pre-execution identity was verified during authoring"
            )


@dataclass(frozen=True)
class InvocationOperationGates:
    """Closed effect boundary of operation-record authoring."""

    invocation_operation_record_present: bool
    one_shot_engineering_invocation_slice_open: bool
    one_shot_engineering_invocation_operation_open: bool
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
        if not (
            self.invocation_operation_record_present
            and self.one_shot_engineering_invocation_slice_open
            and self.one_shot_engineering_invocation_operation_open
        ):
            raise QWakeLC4EngineeringInvocationOperationError(
                "invocation operation authoring boundary is absent"
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
            self.invocation_command_materialized,
            self.docker_run_performed,
            self.local_compute_execution_open,
        )
        if any(forbidden):
            raise QWakeLC4EngineeringInvocationOperationError(
                "invocation operation authoring opened a runtime effect"
            )


@dataclass(frozen=True)
class OneShotEngineeringInvocationOperation:
    """Canonical prospective record for one future effectful operation."""

    schema_version: int
    operation_id: str
    status: str
    recorded_at_utc: str
    authoring_acknowledgement: str
    invocation_operator_acknowledgement: str
    lease_operator_acknowledgement: str
    source: InvocationOperationSource
    checks: InvocationOperationChecks
    gates: InvocationOperationGates
    next_slice: str
    post_merge_next_slice: str
    operation_sha256: str

    def require(self) -> None:
        if self.schema_version != 1:
            raise QWakeLC4EngineeringInvocationOperationError(
                "unexpected invocation operation schema"
            )
        if self.operation_id != INVOCATION_OPERATION_ID:
            raise QWakeLC4EngineeringInvocationOperationError(
                "unexpected invocation operation id"
            )
        if self.status != INVOCATION_OPERATION_STATUS:
            raise QWakeLC4EngineeringInvocationOperationError(
                "unexpected invocation operation status"
            )
        _require_utc(self.recorded_at_utc)
        if self.authoring_acknowledgement != OPERATION_AUTHORING_ACKNOWLEDGEMENT:
            raise QWakeLC4EngineeringInvocationOperationError(
                "operation authoring acknowledgement differs"
            )
        if (
            self.invocation_operator_acknowledgement
            != INVOCATION_OPERATOR_ACKNOWLEDGEMENT
        ):
            raise QWakeLC4EngineeringInvocationOperationError(
                "invocation operator acknowledgement differs"
            )
        if self.lease_operator_acknowledgement != LEASE_OPERATOR_ACKNOWLEDGEMENT:
            raise QWakeLC4EngineeringInvocationOperationError(
                "lease operator acknowledgement differs"
            )
        self.source.require()
        self.checks.require()
        self.gates.require()
        if self.next_slice != (
            "QW-LC4-E-one-shot-engineering-invocation-operation-commit"
        ):
            raise QWakeLC4EngineeringInvocationOperationError(
                "invocation operation next slice differs"
            )
        if self.post_merge_next_slice != (
            "QW-LC4-E-one-shot-engineering-invocation-execution"
        ):
            raise QWakeLC4EngineeringInvocationOperationError(
                "invocation operation post-merge slice differs"
            )
        _require_sha256(self.operation_sha256, "operation_sha256")
        if self.operation_sha256 != sha256_object(self._payload_without_digest()):
            raise QWakeLC4EngineeringInvocationOperationError(
                "invocation operation semantic digest differs"
            )

    def _payload_without_digest(self) -> Mapping[str, object]:
        payload = asdict(self)
        payload.pop("operation_sha256")
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
    """Hash canonical JSON without terminal formatting ambiguity."""

    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def load_engineering_invocation_operation(
    path: Path,
) -> OneShotEngineeringInvocationOperation:
    """Load and validate a canonical invocation operation record."""

    raw = _read_json_object(path)
    source = InvocationOperationSource(**_as_dict(raw.pop("source"), "source"))
    checks_raw = _as_dict(raw.pop("checks"), "checks")
    resource_keys = checks_raw.get("required_host_resource_keys")
    if not isinstance(resource_keys, list) or not all(
        isinstance(item, str) for item in resource_keys
    ):
        raise QWakeLC4EngineeringInvocationOperationError(
            "required_host_resource_keys is not a string array"
        )
    checks_raw["required_host_resource_keys"] = tuple(resource_keys)
    checks = InvocationOperationChecks(**checks_raw)
    gates = InvocationOperationGates(**_as_dict(raw.pop("gates"), "gates"))
    operation = OneShotEngineeringInvocationOperation(
        source=source,
        checks=checks,
        gates=gates,
        **cast(Any, raw),
    )
    operation.require()
    if path.read_text(encoding="utf-8", errors="strict") != (
        operation.canonical_json()
    ):
        raise QWakeLC4EngineeringInvocationOperationError(
            "invocation operation JSON is not canonical"
        )
    return operation


def verify_engineering_invocation_operation(
    project_root: Path,
) -> OneShotEngineeringInvocationOperation:
    """Verify exact merged identities and effect absence without invocation."""

    root = project_root.expanduser().resolve()
    _require_effect_boundary_closed(root)
    _verify_package(root)
    operation = load_engineering_invocation_operation(root / RECORD_RELATIVE)

    admission = verify_engineering_invocation_admission(root)
    if admission.admission_id != INVOCATION_ADMISSION_ID:
        raise QWakeLC4EngineeringInvocationOperationError(
            "invocation admission id differs"
        )
    if admission.admission_sha256 != ADMISSION_SHA256:
        raise QWakeLC4EngineeringInvocationOperationError(
            "invocation admission semantic digest differs"
        )

    authorization = verify_invocation_authorization(root)
    if authorization.authorization_id != INVOCATION_AUTHORIZATION_ID:
        raise QWakeLC4EngineeringInvocationOperationError(
            "invocation authorization id differs"
        )
    if authorization.authorization_sha256 != INVOCATION_AUTHORIZATION_SHA256:
        raise QWakeLC4EngineeringInvocationOperationError(
            "invocation authorization semantic digest differs"
        )

    invoker_state = build_host_runtime_invoker_implementation_state(root)
    if invoker_state.state_sha256 != (
        HOST_RUNTIME_INVOKER_IMPLEMENTATION_STATE_SHA256
    ):
        raise QWakeLC4EngineeringInvocationOperationError(
            "host-runtime-invoker implementation state differs"
        )

    exact_files: Mapping[Path, str] = {
        ADMISSION_RECORD_RELATIVE: ADMISSION_FILE_SHA256,
        ADMISSION_REGISTRY_RELATIVE: ADMISSION_REGISTRY_SHA256,
        ADMISSION_MODULE_RELATIVE: ADMISSION_MODULE_SHA256,
        ADMISSION_VERIFIER_RELATIVE: ADMISSION_VERIFIER_SHA256,
        ADMISSION_TEST_RELATIVE: ADMISSION_TEST_SHA256,
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
            raise QWakeLC4EngineeringInvocationOperationError(
                f"operation source SHA-256 differs: {relative}"
            )

    admission_record = _read_json_object(root / ADMISSION_RECORD_RELATIVE)
    admission_checks = _as_mapping(
        admission_record.get("checks"),
        "admission checks",
    )
    admission_gates = _as_mapping(
        admission_record.get("gates"),
        "admission gates",
    )
    for field_name, expected_value in {
        "repository_freeze_complete": True,
        "invocation_authorization_unconsumed": True,
        "host_runtime_invoker_executable": True,
        "preexecution_identity_checks_implemented": True,
        "preexecution_identity_verified": False,
    }.items():
        if admission_checks.get(field_name) != expected_value:
            raise QWakeLC4EngineeringInvocationOperationError(
                f"invocation admission check differs: {field_name}"
            )
    for field_name, expected_value in {
        "invocation_admission_record_present": True,
        "one_shot_engineering_invocation_slice_open": True,
        "one_shot_engineering_invocation_permitted": False,
        "one_shot_engineering_invocation_performed": False,
        "execution_lease_materialized": False,
        "authorization_consumed": False,
        "runtime_execution_started": False,
        "runtime_execution_performed": False,
        "image_inspection_performed": False,
        "docker_run_performed": False,
        "local_compute_execution_open": False,
    }.items():
        if admission_gates.get(field_name) != expected_value:
            raise QWakeLC4EngineeringInvocationOperationError(
                f"invocation admission gate differs: {field_name}"
            )

    operation.require()
    return operation


def _verify_package(root: Path) -> None:
    package = root / PACKAGE_RELATIVE
    if not package.is_dir() or package.is_symlink():
        raise QWakeLC4EngineeringInvocationOperationError(
            "invocation operation package is absent"
        )
    entries = tuple(package.iterdir())
    observed = {
        item.name
        for item in entries
        if item.is_file() and not item.is_symlink()
    }
    if observed != _EXPECTED_PACKAGE_FILES:
        raise QWakeLC4EngineeringInvocationOperationError(
            "invocation operation package scope differs"
        )
    if any(item.is_dir() or item.is_symlink() for item in entries):
        raise QWakeLC4EngineeringInvocationOperationError(
            "invocation operation package contains a non-regular entry"
        )
    line = (root / REGISTRY_RELATIVE).read_text(
        encoding="utf-8", errors="strict"
    )
    expected_line = (
        _sha256_file(root / RECORD_RELATIVE).removeprefix("sha256:")
        + "  operation.json\n"
    )
    if line != expected_line:
        raise QWakeLC4EngineeringInvocationOperationError(
            "invocation operation package registry differs"
        )


def _require_effect_boundary_closed(root: Path) -> None:
    lease = root / EXECUTION_LEASE_RELATIVE
    output = root / AUTHORIZED_OUTPUT_ROOT
    if lease.exists() or lease.is_symlink():
        raise QWakeLC4EngineeringInvocationOperationError(
            "execution lease is already present"
        )
    if output.exists() or output.is_symlink():
        raise QWakeLC4EngineeringInvocationOperationError(
            "runtime output is already present"
        )
    if output.parent.is_dir() and tuple(
        output.parent.glob(f".{output.name}.staging-*")
    ):
        raise QWakeLC4EngineeringInvocationOperationError(
            "runtime staging remainder is present"
        )


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8", errors="strict"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise QWakeLC4EngineeringInvocationOperationError(
            f"cannot read JSON object: {path}"
        ) from exc
    if not isinstance(raw, dict):
        raise QWakeLC4EngineeringInvocationOperationError(
            f"JSON value is not an object: {path}"
        )
    return cast(dict[str, Any], raw)


def _as_dict(value: object, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise QWakeLC4EngineeringInvocationOperationError(
            f"{field_name} is not an object"
        )
    return cast(dict[str, Any], value)


def _as_mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise QWakeLC4EngineeringInvocationOperationError(
            f"{field_name} is not an object"
        )
    return cast(Mapping[str, object], value)


def _sha256_file(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise QWakeLC4EngineeringInvocationOperationError(
            f"required regular file is absent: {path}"
        )
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _require_commit(value: str, field_name: str) -> None:
    if not _COMMIT_PATTERN.fullmatch(value):
        raise QWakeLC4EngineeringInvocationOperationError(
            f"{field_name} is not a canonical commit"
        )


def _require_sha256(value: str, field_name: str) -> None:
    if not _SHA256_PATTERN.fullmatch(value):
        raise QWakeLC4EngineeringInvocationOperationError(
            f"{field_name} is not a canonical SHA-256"
        )


def _require_utc(value: str) -> None:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value):
        raise QWakeLC4EngineeringInvocationOperationError(
            "recorded_at_utc is not canonical UTC"
        )
