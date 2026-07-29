"""Fail-closed authoring contract for the QW-LC4-E host invocation wrapper.

This module verifies the merged one-shot invocation authorization and builds
only an in-memory contract for a future host-side container invocation.  It
does not inspect or invoke Docker, create the execution lease, mount a dataset,
start the runtime, write results, consume authorization, or publish evidence.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Final, cast

from torch2pc_thesis.stage3b_qwake_lc4_invocation_authorization import (
    AUTHORIZED_OUTPUT_ROOT,
    EXECUTION_LEASE_RELATIVE,
    FROZEN_TORCH2PC_COMMIT,
    IMAGE_DIGEST,
    IMAGE_REPO_DIGEST,
    IMAGE_TAG,
    INVOCATION_AUTHORIZATION_ID,
    INVOCATION_OPERATOR_ACKNOWLEDGEMENT,
    LEASE_OPERATOR_ACKNOWLEDGEMENT,
    POST_MERGE_COMMIT,
    POST_MERGE_PARENT_1,
    verify_invocation_authorization,
)

INVOCATION_WRAPPER_CONTRACT_ID: Final = (
    "stage3b-qwake-lc4-e-one-shot-host-invocation-wrapper-contract-v1"
)
INVOCATION_WRAPPER_CONTRACT_STATUS: Final = (
    "prospective_exact_image_invocation_contract_runtime_not_open"
)
AUTHORIZATION_MERGE_COMMIT: Final = (
    "8337d9ad0ac21a69a577ab74a73d05d69f8fa7a1"
)
AUTHORIZATION_HEAD_COMMIT: Final = (
    "ca6363c11218575d567c5dd6cbe8818d10a86d41"
)
IMAGE_SOURCE_COMMIT: Final = POST_MERGE_PARENT_1
CONTAINER_RUNTIME: Final = "docker"
CONTAINER_WORKDIR: Final = "/workspace"
CONTAINER_RUNTIME_ENTRYPOINT: Final = (
    "/workspace/scripts/run_stage3b_qwake_lc4_authorized_runtime.py"
)
CONTAINER_IMAGE_ENTRYPOINT: Final = (
    "/usr/bin/tini",
    "--",
    "/workspace/scripts/container_entrypoint.sh",
)
CONTAINER_COMMAND_TEMPLATE: Final = (
    "python",
    CONTAINER_RUNTIME_ENTRYPOINT,
    "--project-root",
    CONTAINER_WORKDIR,
    "--torch2pc-dir",
    "/workspace/external/Torch2PC",
    "--claimed-at-utc",
    "{CLAIMED_AT_UTC}",
    "--operator-acknowledgement",
    LEASE_OPERATOR_ACKNOWLEDGEMENT,
)
CONTAINER_USER_TEMPLATE: Final = "${HOST_UID}:${HOST_GID}"
CONTAINER_DEVICE_BINDINGS: Final = (
    ("/dev/kfd", "/dev/kfd", "rwm"),
    ("/dev/dri", "/dev/dri", "rwm"),
)
CONTAINER_TMPFS_TARGET: Final = "/tmp"
CONTAINER_TMPFS_OPTIONS: Final = (
    "rw",
    "nosuid",
    "nodev",
    "mode=1777",
    "size=${TMPFS_SIZE}",
)
FROZEN_EXPERIMENTS_RELATIVE: Final = Path("experiments/frozen")
TORCH2PC_RELATIVE: Final = Path("external/Torch2PC")
RESULTS_RELATIVE: Final = Path("results")

_FIXED_ENVIRONMENT: Final = (
    ("HOME", "/tmp/home"),
    ("PYTHONDONTWRITEBYTECODE", "1"),
    ("PYTHONHASHSEED", "0"),
    ("PYTHONUNBUFFERED", "1"),
    ("SOURCE_GIT_COMMIT", IMAGE_SOURCE_COMMIT),
    ("EXPERIMENT_IMAGE_DIGEST", IMAGE_DIGEST),
    ("EXPERIMENT_IMAGE_REPO_DIGEST", IMAGE_REPO_DIGEST),
)
_HOST_ENVIRONMENT_BINDINGS: Final = (
    ("HIP_VISIBLE_DEVICES", "HIP_VISIBLE_DEVICES"),
    ("OMP_NUM_THREADS", "OMP_NUM_THREADS"),
    ("MKL_NUM_THREADS", "MKL_NUM_THREADS"),
    ("OPENBLAS_NUM_THREADS", "OPENBLAS_NUM_THREADS"),
    ("NUMEXPR_NUM_THREADS", "NUMEXPR_NUM_THREADS"),
)
_SUPPLEMENTARY_GROUP_INPUTS: Final = ("VIDEO_GID", "RENDER_GID")
_REQUIRED_HOST_RESOURCE_INPUTS: Final = (
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

__all__ = [
    "AUTHORIZATION_HEAD_COMMIT",
    "AUTHORIZATION_MERGE_COMMIT",
    "CONTAINER_COMMAND_TEMPLATE",
    "CONTAINER_DEVICE_BINDINGS",
    "CONTAINER_IMAGE_ENTRYPOINT",
    "CONTAINER_RUNTIME",
    "CONTAINER_RUNTIME_ENTRYPOINT",
    "CONTAINER_TMPFS_OPTIONS",
    "CONTAINER_TMPFS_TARGET",
    "CONTAINER_USER_TEMPLATE",
    "CONTAINER_WORKDIR",
    "IMAGE_SOURCE_COMMIT",
    "INVOCATION_WRAPPER_CONTRACT_ID",
    "INVOCATION_WRAPPER_CONTRACT_STATUS",
    "InvocationMountContract",
    "OneShotInvocationWrapperContract",
    "QWakeLC4InvocationWrapperError",
    "build_one_shot_invocation_wrapper_contract",
    "canonical_json",
    "load_one_shot_invocation_wrapper_contract",
    "sha256_object",
    "validate_one_shot_invocation_wrapper_contract",
    "verify_invocation_wrapper_prerequisites",
]


class QWakeLC4InvocationWrapperError(RuntimeError):
    """Raised when host invocation-wrapper authoring fails closed."""


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


@dataclass(frozen=True)
class InvocationMountContract:
    """One exact future bind mount without materializing it."""

    source_kind: str
    source_relative: str
    target: str
    access: str

    def require(self) -> None:
        if self.source_kind not in {
            "frozen_experiments",
            "torch2pc_checkout",
            "runtime_results",
        }:
            raise QWakeLC4InvocationWrapperError(
                "invocation mount source kind differs"
            )
        if self.access not in {"read_only", "read_write"}:
            raise QWakeLC4InvocationWrapperError(
                "invocation mount access differs"
            )
        if not self.source_relative or Path(self.source_relative).is_absolute():
            raise QWakeLC4InvocationWrapperError(
                "invocation mount source is not repository-relative"
            )
        if not self.target.startswith("/workspace/"):
            raise QWakeLC4InvocationWrapperError(
                "invocation mount target leaves /workspace"
            )


@dataclass(frozen=True)
class OneShotInvocationWrapperContract:
    """Prospective host wrapper contract with every runtime effect closed."""

    schema_version: int
    contract_id: str
    status: str
    authorization_merge_commit: str
    authorization_head_commit: str
    authorization_id: str
    authorization_sha256: str
    image_tag: str
    image_digest: str
    image_repo_digest: str
    image_source_commit: str
    torch2pc_commit: str
    container_runtime: str
    container_workdir: str
    container_image_entrypoint: tuple[str, ...]
    container_runtime_entrypoint: str
    container_command_template: tuple[str, ...]
    runtime_entrypoint_sha256: str
    output_root: str
    execution_lease_relative: str
    invocation_operator_acknowledgement: str
    lease_operator_acknowledgement: str
    fixed_environment: tuple[tuple[str, str], ...]
    host_environment_bindings: tuple[tuple[str, str], ...]
    required_host_resource_inputs: tuple[str, ...]
    container_user_template: str
    supplementary_group_inputs: tuple[str, ...]
    device_bindings: tuple[tuple[str, str, str], ...]
    cpuset_input: str
    memory_limit_input: str
    shm_size_input: str
    tmpfs_target: str
    tmpfs_options: tuple[str, ...]
    tmpfs_size_input: str
    mounts: tuple[InvocationMountContract, ...]
    image_reference_must_use_repo_digest: bool
    image_identity_inspection_required: bool
    image_source_label_verification_required: bool
    network_disabled: bool
    read_only_root_filesystem: bool
    no_new_privileges: bool
    drop_all_capabilities: bool
    privileged_forbidden: bool
    automatic_remove_required: bool
    init_required: bool
    project_source_bind_forbidden: bool
    test_dataset_mount_forbidden: bool
    frozen_experiments_read_only: bool
    torch2pc_read_only: bool
    results_read_write: bool
    claimed_at_utc_required_at_invocation: bool
    claim_and_execute_same_process_required: bool
    no_retry_after_claim_required: bool
    engineering_only: bool
    synthetic_data_only: bool
    invocation_wrapper_contract_present: bool
    host_runtime_invoker_present: bool
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
    contract_sha256: str

    def require(self) -> None:
        exact: Mapping[str, object] = {
            "schema_version": 1,
            "contract_id": INVOCATION_WRAPPER_CONTRACT_ID,
            "status": INVOCATION_WRAPPER_CONTRACT_STATUS,
            "authorization_merge_commit": AUTHORIZATION_MERGE_COMMIT,
            "authorization_head_commit": AUTHORIZATION_HEAD_COMMIT,
            "authorization_id": INVOCATION_AUTHORIZATION_ID,
            "image_tag": IMAGE_TAG,
            "image_digest": IMAGE_DIGEST,
            "image_repo_digest": IMAGE_REPO_DIGEST,
            "image_source_commit": IMAGE_SOURCE_COMMIT,
            "torch2pc_commit": FROZEN_TORCH2PC_COMMIT,
            "container_runtime": CONTAINER_RUNTIME,
            "container_workdir": CONTAINER_WORKDIR,
            "container_image_entrypoint": CONTAINER_IMAGE_ENTRYPOINT,
            "container_runtime_entrypoint": CONTAINER_RUNTIME_ENTRYPOINT,
            "container_command_template": CONTAINER_COMMAND_TEMPLATE,
            "output_root": AUTHORIZED_OUTPUT_ROOT,
            "execution_lease_relative": EXECUTION_LEASE_RELATIVE.as_posix(),
            "invocation_operator_acknowledgement": (
                INVOCATION_OPERATOR_ACKNOWLEDGEMENT
            ),
            "lease_operator_acknowledgement": LEASE_OPERATOR_ACKNOWLEDGEMENT,
            "fixed_environment": _FIXED_ENVIRONMENT,
            "host_environment_bindings": _HOST_ENVIRONMENT_BINDINGS,
            "required_host_resource_inputs": _REQUIRED_HOST_RESOURCE_INPUTS,
            "container_user_template": CONTAINER_USER_TEMPLATE,
            "supplementary_group_inputs": _SUPPLEMENTARY_GROUP_INPUTS,
            "device_bindings": CONTAINER_DEVICE_BINDINGS,
            "cpuset_input": "CPUSET_GPU",
            "memory_limit_input": "MEM_LIMIT",
            "shm_size_input": "SHM_SIZE",
            "tmpfs_target": CONTAINER_TMPFS_TARGET,
            "tmpfs_options": CONTAINER_TMPFS_OPTIONS,
            "tmpfs_size_input": "TMPFS_SIZE",
            "image_reference_must_use_repo_digest": True,
            "image_identity_inspection_required": True,
            "image_source_label_verification_required": True,
            "network_disabled": True,
            "read_only_root_filesystem": True,
            "no_new_privileges": True,
            "drop_all_capabilities": True,
            "privileged_forbidden": True,
            "automatic_remove_required": True,
            "init_required": True,
            "project_source_bind_forbidden": True,
            "test_dataset_mount_forbidden": True,
            "frozen_experiments_read_only": True,
            "torch2pc_read_only": True,
            "results_read_write": True,
            "claimed_at_utc_required_at_invocation": True,
            "claim_and_execute_same_process_required": True,
            "no_retry_after_claim_required": True,
            "engineering_only": True,
            "synthetic_data_only": True,
            "invocation_wrapper_contract_present": True,
            "host_runtime_invoker_present": False,
            "branch_runtime_execution_permitted": False,
            "execution_lease_materialized": False,
            "authorization_consumed": False,
            "runtime_execution_started": False,
            "runtime_execution_performed": False,
            "engineering_evidence_present": False,
            "scientific_execution_open": False,
            "test_dataset_access": False,
            "publication_permitted": False,
            "local_compute_execution_open": False,
        }
        for field_name, expected in exact.items():
            if getattr(self, field_name) != expected:
                raise QWakeLC4InvocationWrapperError(
                    f"invocation-wrapper contract differs: {field_name}"
                )
        expected_mounts = (
            InvocationMountContract(
                source_kind="frozen_experiments",
                source_relative=FROZEN_EXPERIMENTS_RELATIVE.as_posix(),
                target="/workspace/experiments/frozen",
                access="read_only",
            ),
            InvocationMountContract(
                source_kind="torch2pc_checkout",
                source_relative=TORCH2PC_RELATIVE.as_posix(),
                target="/workspace/external/Torch2PC",
                access="read_only",
            ),
            InvocationMountContract(
                source_kind="runtime_results",
                source_relative=RESULTS_RELATIVE.as_posix(),
                target="/workspace/results",
                access="read_write",
            ),
        )
        if self.mounts != expected_mounts:
            raise QWakeLC4InvocationWrapperError(
                "invocation-wrapper mount contract differs"
            )
        for mount in self.mounts:
            mount.require()
        for value, field_name in (
            (self.authorization_sha256, "authorization_sha256"),
            (self.runtime_entrypoint_sha256, "runtime_entrypoint_sha256"),
            (self.contract_sha256, "contract_sha256"),
        ):
            if not value.startswith("sha256:") or len(value) != 71:
                raise QWakeLC4InvocationWrapperError(
                    f"{field_name} is not SHA-256"
                )
        if self.contract_sha256 != sha256_object(
            self._payload_without_digest()
        ):
            raise QWakeLC4InvocationWrapperError(
                "invocation-wrapper contract digest differs"
            )

    def _payload_without_digest(self) -> Mapping[str, object]:
        payload = asdict(self)
        payload.pop("contract_sha256")
        return cast(Mapping[str, object], payload)

    def canonical_json(self) -> str:
        return canonical_json(asdict(self))


def _effect_boundary(root: Path) -> None:
    lease_path = root / EXECUTION_LEASE_RELATIVE
    output_root = root / AUTHORIZED_OUTPUT_ROOT
    if lease_path.exists() or lease_path.is_symlink():
        raise QWakeLC4InvocationWrapperError(
            "repository execution lease already exists"
        )
    if output_root.exists() or output_root.is_symlink():
        raise QWakeLC4InvocationWrapperError(
            "repository runtime output already exists"
        )
    staging = tuple(output_root.parent.glob(f".{output_root.name}.staging-*"))
    if staging:
        raise QWakeLC4InvocationWrapperError(
            "repository runtime staging tree already exists"
        )


def verify_invocation_wrapper_prerequisites(
    project_root: Path,
) -> tuple[str, str]:
    """Verify exact authorization and repository effect absence."""

    root = project_root.expanduser().resolve()
    _effect_boundary(root)
    authorization = verify_invocation_authorization(root)
    if authorization.source.post_merge_commit != POST_MERGE_COMMIT:
        raise QWakeLC4InvocationWrapperError(
            "authorization source merge identity differs"
        )
    if authorization.authorization_id != INVOCATION_AUTHORIZATION_ID:
        raise QWakeLC4InvocationWrapperError(
            "invocation authorization id differs"
        )
    return (
        authorization.authorization_sha256,
        authorization.source.one_shot_entrypoint_sha256,
    )


def build_one_shot_invocation_wrapper_contract(
    project_root: Path,
) -> OneShotInvocationWrapperContract:
    """Build the pure future invocation contract without a command or effect."""

    authorization_sha256, runtime_entrypoint_sha256 = (
        verify_invocation_wrapper_prerequisites(project_root)
    )
    mounts = (
        InvocationMountContract(
            source_kind="frozen_experiments",
            source_relative=FROZEN_EXPERIMENTS_RELATIVE.as_posix(),
            target="/workspace/experiments/frozen",
            access="read_only",
        ),
        InvocationMountContract(
            source_kind="torch2pc_checkout",
            source_relative=TORCH2PC_RELATIVE.as_posix(),
            target="/workspace/external/Torch2PC",
            access="read_only",
        ),
        InvocationMountContract(
            source_kind="runtime_results",
            source_relative=RESULTS_RELATIVE.as_posix(),
            target="/workspace/results",
            access="read_write",
        ),
    )
    contract = OneShotInvocationWrapperContract(
        schema_version=1,
        contract_id=INVOCATION_WRAPPER_CONTRACT_ID,
        status=INVOCATION_WRAPPER_CONTRACT_STATUS,
        authorization_merge_commit=AUTHORIZATION_MERGE_COMMIT,
        authorization_head_commit=AUTHORIZATION_HEAD_COMMIT,
        authorization_id=INVOCATION_AUTHORIZATION_ID,
        authorization_sha256=authorization_sha256,
        image_tag=IMAGE_TAG,
        image_digest=IMAGE_DIGEST,
        image_repo_digest=IMAGE_REPO_DIGEST,
        image_source_commit=IMAGE_SOURCE_COMMIT,
        torch2pc_commit=FROZEN_TORCH2PC_COMMIT,
        container_runtime=CONTAINER_RUNTIME,
        container_workdir=CONTAINER_WORKDIR,
        container_image_entrypoint=CONTAINER_IMAGE_ENTRYPOINT,
        container_runtime_entrypoint=CONTAINER_RUNTIME_ENTRYPOINT,
        container_command_template=CONTAINER_COMMAND_TEMPLATE,
        runtime_entrypoint_sha256=runtime_entrypoint_sha256,
        output_root=AUTHORIZED_OUTPUT_ROOT,
        execution_lease_relative=EXECUTION_LEASE_RELATIVE.as_posix(),
        invocation_operator_acknowledgement=(
            INVOCATION_OPERATOR_ACKNOWLEDGEMENT
        ),
        lease_operator_acknowledgement=LEASE_OPERATOR_ACKNOWLEDGEMENT,
        fixed_environment=_FIXED_ENVIRONMENT,
        host_environment_bindings=_HOST_ENVIRONMENT_BINDINGS,
        required_host_resource_inputs=_REQUIRED_HOST_RESOURCE_INPUTS,
        container_user_template=CONTAINER_USER_TEMPLATE,
        supplementary_group_inputs=_SUPPLEMENTARY_GROUP_INPUTS,
        device_bindings=CONTAINER_DEVICE_BINDINGS,
        cpuset_input="CPUSET_GPU",
        memory_limit_input="MEM_LIMIT",
        shm_size_input="SHM_SIZE",
        tmpfs_target=CONTAINER_TMPFS_TARGET,
        tmpfs_options=CONTAINER_TMPFS_OPTIONS,
        tmpfs_size_input="TMPFS_SIZE",
        mounts=mounts,
        image_reference_must_use_repo_digest=True,
        image_identity_inspection_required=True,
        image_source_label_verification_required=True,
        network_disabled=True,
        read_only_root_filesystem=True,
        no_new_privileges=True,
        drop_all_capabilities=True,
        privileged_forbidden=True,
        automatic_remove_required=True,
        init_required=True,
        project_source_bind_forbidden=True,
        test_dataset_mount_forbidden=True,
        frozen_experiments_read_only=True,
        torch2pc_read_only=True,
        results_read_write=True,
        claimed_at_utc_required_at_invocation=True,
        claim_and_execute_same_process_required=True,
        no_retry_after_claim_required=True,
        engineering_only=True,
        synthetic_data_only=True,
        invocation_wrapper_contract_present=True,
        host_runtime_invoker_present=False,
        branch_runtime_execution_permitted=False,
        execution_lease_materialized=False,
        authorization_consumed=False,
        runtime_execution_started=False,
        runtime_execution_performed=False,
        engineering_evidence_present=False,
        scientific_execution_open=False,
        test_dataset_access=False,
        publication_permitted=False,
        local_compute_execution_open=False,
        contract_sha256="sha256:" + "0" * 64,
    )
    contract = replace(
        contract,
        contract_sha256=sha256_object(contract._payload_without_digest()),
    )
    contract.require()
    return contract


def _as_mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise QWakeLC4InvocationWrapperError(f"{field_name} is not an object")
    return cast(Mapping[str, object], value)


def _as_sequence(value: object, field_name: str) -> Sequence[object]:
    if not isinstance(value, list):
        raise QWakeLC4InvocationWrapperError(f"{field_name} is not an array")
    return cast(Sequence[object], value)


def _as_pair(value: object, field_name: str) -> tuple[str, str]:
    sequence = _as_sequence(value, field_name)
    if len(sequence) != 2:
        raise QWakeLC4InvocationWrapperError(
            f"{field_name} does not contain two strings"
        )
    return (
        _as_str(sequence[0], f"{field_name}[0]"),
        _as_str(sequence[1], f"{field_name}[1]"),
    )


def _as_triple(value: object, field_name: str) -> tuple[str, str, str]:
    sequence = _as_sequence(value, field_name)
    if len(sequence) != 3:
        raise QWakeLC4InvocationWrapperError(
            f"{field_name} does not contain three strings"
        )
    return (
        _as_str(sequence[0], f"{field_name}[0]"),
        _as_str(sequence[1], f"{field_name}[1]"),
        _as_str(sequence[2], f"{field_name}[2]"),
    )


def _as_string_tuple(value: object, field_name: str) -> tuple[str, ...]:
    return tuple(
        _as_str(item, f"{field_name} item")
        for item in _as_sequence(value, field_name)
    )


def _as_str(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise QWakeLC4InvocationWrapperError(f"{field_name} is not a string")
    return value


def _as_bool(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise QWakeLC4InvocationWrapperError(f"{field_name} is not a boolean")
    return value


def _as_int(value: object, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise QWakeLC4InvocationWrapperError(f"{field_name} is not an integer")
    return value


def load_one_shot_invocation_wrapper_contract(
    path: Path,
) -> OneShotInvocationWrapperContract:
    """Load an exact canonical authoring contract from a regular file."""

    if not path.is_file() or path.is_symlink():
        raise QWakeLC4InvocationWrapperError(
            "invocation-wrapper contract file is absent or non-regular"
        )
    try:
        raw: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise QWakeLC4InvocationWrapperError(
            "invocation-wrapper contract cannot be decoded"
        ) from exc
    data = _as_mapping(raw, "contract")
    fixed_environment = tuple(
        _as_pair(item, "fixed_environment item")
        for item in _as_sequence(
            data.get("fixed_environment"), "fixed_environment"
        )
    )
    host_environment_bindings = tuple(
        _as_pair(item, "host_environment_bindings item")
        for item in _as_sequence(
            data.get("host_environment_bindings"),
            "host_environment_bindings",
        )
    )
    resource_inputs = _as_string_tuple(
        data.get("required_host_resource_inputs"),
        "required_host_resource_inputs",
    )
    supplementary_group_inputs = _as_string_tuple(
        data.get("supplementary_group_inputs"),
        "supplementary_group_inputs",
    )
    device_bindings = tuple(
        _as_triple(item, "device_bindings item")
        for item in _as_sequence(
            data.get("device_bindings"), "device_bindings"
        )
    )
    container_image_entrypoint = _as_string_tuple(
        data.get("container_image_entrypoint"),
        "container_image_entrypoint",
    )
    container_command_template = _as_string_tuple(
        data.get("container_command_template"),
        "container_command_template",
    )
    tmpfs_options = _as_string_tuple(
        data.get("tmpfs_options"), "tmpfs_options"
    )
    mounts = tuple(
        InvocationMountContract(
            source_kind=_as_str(
                _as_mapping(item, "mount").get("source_kind"),
                "mount.source_kind",
            ),
            source_relative=_as_str(
                _as_mapping(item, "mount").get("source_relative"),
                "mount.source_relative",
            ),
            target=_as_str(
                _as_mapping(item, "mount").get("target"),
                "mount.target",
            ),
            access=_as_str(
                _as_mapping(item, "mount").get("access"),
                "mount.access",
            ),
        )
        for item in _as_sequence(data.get("mounts"), "mounts")
    )
    contract = OneShotInvocationWrapperContract(
        schema_version=_as_int(data.get("schema_version"), "schema_version"),
        contract_id=_as_str(data.get("contract_id"), "contract_id"),
        status=_as_str(data.get("status"), "status"),
        authorization_merge_commit=_as_str(
            data.get("authorization_merge_commit"),
            "authorization_merge_commit",
        ),
        authorization_head_commit=_as_str(
            data.get("authorization_head_commit"),
            "authorization_head_commit",
        ),
        authorization_id=_as_str(
            data.get("authorization_id"), "authorization_id"
        ),
        authorization_sha256=_as_str(
            data.get("authorization_sha256"), "authorization_sha256"
        ),
        image_tag=_as_str(data.get("image_tag"), "image_tag"),
        image_digest=_as_str(data.get("image_digest"), "image_digest"),
        image_repo_digest=_as_str(
            data.get("image_repo_digest"), "image_repo_digest"
        ),
        image_source_commit=_as_str(
            data.get("image_source_commit"), "image_source_commit"
        ),
        torch2pc_commit=_as_str(
            data.get("torch2pc_commit"), "torch2pc_commit"
        ),
        container_runtime=_as_str(
            data.get("container_runtime"), "container_runtime"
        ),
        container_workdir=_as_str(
            data.get("container_workdir"), "container_workdir"
        ),
        container_image_entrypoint=container_image_entrypoint,
        container_runtime_entrypoint=_as_str(
            data.get("container_runtime_entrypoint"),
            "container_runtime_entrypoint",
        ),
        container_command_template=container_command_template,
        runtime_entrypoint_sha256=_as_str(
            data.get("runtime_entrypoint_sha256"),
            "runtime_entrypoint_sha256",
        ),
        output_root=_as_str(data.get("output_root"), "output_root"),
        execution_lease_relative=_as_str(
            data.get("execution_lease_relative"),
            "execution_lease_relative",
        ),
        invocation_operator_acknowledgement=_as_str(
            data.get("invocation_operator_acknowledgement"),
            "invocation_operator_acknowledgement",
        ),
        lease_operator_acknowledgement=_as_str(
            data.get("lease_operator_acknowledgement"),
            "lease_operator_acknowledgement",
        ),
        fixed_environment=fixed_environment,
        host_environment_bindings=host_environment_bindings,
        required_host_resource_inputs=resource_inputs,
        container_user_template=_as_str(
            data.get("container_user_template"),
            "container_user_template",
        ),
        supplementary_group_inputs=supplementary_group_inputs,
        device_bindings=device_bindings,
        cpuset_input=_as_str(data.get("cpuset_input"), "cpuset_input"),
        memory_limit_input=_as_str(
            data.get("memory_limit_input"), "memory_limit_input"
        ),
        shm_size_input=_as_str(
            data.get("shm_size_input"), "shm_size_input"
        ),
        tmpfs_target=_as_str(data.get("tmpfs_target"), "tmpfs_target"),
        tmpfs_options=tmpfs_options,
        tmpfs_size_input=_as_str(
            data.get("tmpfs_size_input"), "tmpfs_size_input"
        ),
        mounts=mounts,
        image_reference_must_use_repo_digest=_as_bool(
            data.get("image_reference_must_use_repo_digest"),
            "image_reference_must_use_repo_digest",
        ),
        image_identity_inspection_required=_as_bool(
            data.get("image_identity_inspection_required"),
            "image_identity_inspection_required",
        ),
        image_source_label_verification_required=_as_bool(
            data.get("image_source_label_verification_required"),
            "image_source_label_verification_required",
        ),
        network_disabled=_as_bool(
            data.get("network_disabled"), "network_disabled"
        ),
        read_only_root_filesystem=_as_bool(
            data.get("read_only_root_filesystem"),
            "read_only_root_filesystem",
        ),
        no_new_privileges=_as_bool(
            data.get("no_new_privileges"), "no_new_privileges"
        ),
        drop_all_capabilities=_as_bool(
            data.get("drop_all_capabilities"), "drop_all_capabilities"
        ),
        privileged_forbidden=_as_bool(
            data.get("privileged_forbidden"), "privileged_forbidden"
        ),
        automatic_remove_required=_as_bool(
            data.get("automatic_remove_required"),
            "automatic_remove_required",
        ),
        init_required=_as_bool(data.get("init_required"), "init_required"),
        project_source_bind_forbidden=_as_bool(
            data.get("project_source_bind_forbidden"),
            "project_source_bind_forbidden",
        ),
        test_dataset_mount_forbidden=_as_bool(
            data.get("test_dataset_mount_forbidden"),
            "test_dataset_mount_forbidden",
        ),
        frozen_experiments_read_only=_as_bool(
            data.get("frozen_experiments_read_only"),
            "frozen_experiments_read_only",
        ),
        torch2pc_read_only=_as_bool(
            data.get("torch2pc_read_only"), "torch2pc_read_only"
        ),
        results_read_write=_as_bool(
            data.get("results_read_write"), "results_read_write"
        ),
        claimed_at_utc_required_at_invocation=_as_bool(
            data.get("claimed_at_utc_required_at_invocation"),
            "claimed_at_utc_required_at_invocation",
        ),
        claim_and_execute_same_process_required=_as_bool(
            data.get("claim_and_execute_same_process_required"),
            "claim_and_execute_same_process_required",
        ),
        no_retry_after_claim_required=_as_bool(
            data.get("no_retry_after_claim_required"),
            "no_retry_after_claim_required",
        ),
        engineering_only=_as_bool(
            data.get("engineering_only"), "engineering_only"
        ),
        synthetic_data_only=_as_bool(
            data.get("synthetic_data_only"), "synthetic_data_only"
        ),
        invocation_wrapper_contract_present=_as_bool(
            data.get("invocation_wrapper_contract_present"),
            "invocation_wrapper_contract_present",
        ),
        host_runtime_invoker_present=_as_bool(
            data.get("host_runtime_invoker_present"),
            "host_runtime_invoker_present",
        ),
        branch_runtime_execution_permitted=_as_bool(
            data.get("branch_runtime_execution_permitted"),
            "branch_runtime_execution_permitted",
        ),
        execution_lease_materialized=_as_bool(
            data.get("execution_lease_materialized"),
            "execution_lease_materialized",
        ),
        authorization_consumed=_as_bool(
            data.get("authorization_consumed"), "authorization_consumed"
        ),
        runtime_execution_started=_as_bool(
            data.get("runtime_execution_started"),
            "runtime_execution_started",
        ),
        runtime_execution_performed=_as_bool(
            data.get("runtime_execution_performed"),
            "runtime_execution_performed",
        ),
        engineering_evidence_present=_as_bool(
            data.get("engineering_evidence_present"),
            "engineering_evidence_present",
        ),
        scientific_execution_open=_as_bool(
            data.get("scientific_execution_open"),
            "scientific_execution_open",
        ),
        test_dataset_access=_as_bool(
            data.get("test_dataset_access"), "test_dataset_access"
        ),
        publication_permitted=_as_bool(
            data.get("publication_permitted"), "publication_permitted"
        ),
        local_compute_execution_open=_as_bool(
            data.get("local_compute_execution_open"),
            "local_compute_execution_open",
        ),
        contract_sha256=_as_str(
            data.get("contract_sha256"), "contract_sha256"
        ),
    )
    contract.require()
    if path.read_text(encoding="utf-8") != contract.canonical_json():
        raise QWakeLC4InvocationWrapperError(
            "invocation-wrapper contract serialization differs"
        )
    return contract


def validate_one_shot_invocation_wrapper_contract(
    contract: OneShotInvocationWrapperContract,
    project_root: Path,
) -> None:
    """Validate an authoring contract against current frozen prerequisites."""

    contract.require()
    expected = build_one_shot_invocation_wrapper_contract(project_root)
    if contract != expected:
        raise QWakeLC4InvocationWrapperError(
            "invocation-wrapper contract differs from frozen prerequisites"
        )
