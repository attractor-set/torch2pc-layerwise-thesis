"""Pure host-invocation authoring chain for QW-LC4-E attempt 002.

The module binds the corrected execution freeze to a deterministic host image
inspection and a future ``docker run`` command represented only as data.  It
never invokes Docker, creates a container, issues or consumes authorization,
creates a lease, starts model code, or writes runtime results.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Final, cast

from torch2pc_thesis.stage3b_qwake_lc4_attempt_002_contract import (
    ATTEMPT_002_AUTHORIZATION_ROOT,
    ATTEMPT_002_DURABLE_OUTCOME_RELATIVE,
    ATTEMPT_002_FREEZE_RELATIVE,
    ATTEMPT_002_FREEZE_ROOT,
    ATTEMPT_002_ID,
    ATTEMPT_002_INVOCATION_ACKNOWLEDGEMENT,
    ATTEMPT_002_LEASE_ACKNOWLEDGEMENT,
    ATTEMPT_002_LEASE_V1_RELATIVE,
    ATTEMPT_002_LEASE_V2_RELATIVE,
    ATTEMPT_002_OUTPUT_ROOT,
    Attempt002ExecutionFreeze,
    verify_unconsumed_attempt_002_authorization,
)

HOST_INVOCATION_CHAIN_ID: Final = (
    "stage3b-qwake-lc4-e-attempt-002-host-invocation-chain-v1"
)
HOST_INVOCATION_CHAIN_STATUS: Final = (
    "corrected_image_host_command_chain_authored_authorization_absent"
)
HOST_INVOCATION_CHAIN_AUTHORIZED_STATUS: Final = (
    "corrected_image_host_command_chain_authorized_unconsumed"
)
HOST_INVOCATION_CONTRACT_ID: Final = (
    "stage3b-qwake-lc4-e-attempt-002-host-invocation-contract-v1"
)
HOST_IMAGE_IDENTITY_ID: Final = (
    "stage3b-qwake-lc4-e-attempt-002-host-image-identity-v1"
)
HOST_RUNTIME: Final = "docker"
CONTAINER_WORKDIR: Final = "/workspace"
CONTAINER_RUNTIME_ENTRYPOINT: Final = (
    "/workspace/scripts/run_stage3b_qwake_lc4_attempt_002_authorized_runtime.py"
)
CONTAINER_IMAGE_ENTRYPOINT: Final = (
    "/usr/bin/tini",
    "--",
    "/workspace/scripts/container_entrypoint.sh",
)
EXPECTED_SOURCE_COMMIT: Final = (
    "02afcc3e79b2d456cc3f1c075d4d792a0be608f7"
)
EXPECTED_TORCH2PC_COMMIT: Final = (
    "b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4"
)
EXPECTED_IMAGE_TAG: Final = (
    "torch2pc-layerwise-thesis:0.1.0-qw-lc4-e-attempt-002-02afcc3e79b2"
)
EXPECTED_IMAGE_DIGEST: Final = (
    "sha256:f78fdbc699f3d00347d1dfdb78c03dd3df3957371f64eca9488de7cc06ce2b1d"
)
EXPECTED_IMAGE_REPO_DIGEST: Final = (
    "torch2pc-layerwise-thesis@"
    "sha256:f78fdbc699f3d00347d1dfdb78c03dd3df3957371f64eca9488de7cc06ce2b1d"
)
EXPECTED_BASE_IMAGE: Final = (
    "rocm/pytorch@"
    "sha256:96a2fb24dec9896e2f8238178f0c49d0dcc4c7dcc597be09e4564316bd86d191"
)
EXPECTED_IMAGE_SIZE_BYTES: Final = 10_906_632_054
EXPECTED_FREEZE_SHA256: Final = (
    "sha256:09ca6e2b70fe1c7352c35d694952b4ea199e85dd816588f29454a4157b711f5c"
)
EXPECTED_IMAGE_IDENTITY_SHA256: Final = (
    "sha256:11f15e3e92680632221bd879ba8aff680f171fb4af2d212afb2aca4763addb3a"
)
HOST_IMAGE_IDENTITY_RELATIVE: Final = ATTEMPT_002_FREEZE_ROOT / "image-identity.json"
HOST_INVOCATION_CHAIN_ROOT: Final = Path(
    "experiments/frozen/"
    "stage3b-qwake-lc4-e-attempt-002-host-invocation-chain-v1"
)
HOST_INVOCATION_RECORD_RELATIVE: Final = (
    HOST_INVOCATION_CHAIN_ROOT / "host-invocation-contract.json"
)
HOST_CHAIN_AUTHORING_RELATIVE: Final = HOST_INVOCATION_CHAIN_ROOT / "authoring.json"
HOST_CHAIN_REGISTRY_RELATIVE: Final = HOST_INVOCATION_CHAIN_ROOT / "SHA256SUMS"
HOST_CHAIN_SOURCE_REGISTRY_RELATIVE: Final = (
    HOST_INVOCATION_CHAIN_ROOT / "source-SHA256SUMS"
)
FROZEN_EXPERIMENTS_RELATIVE: Final = Path("experiments/frozen")
TORCH2PC_RELATIVE: Final = Path("external/Torch2PC")
RESULTS_RELATIVE: Final = Path("results")

_REQUIRED_RESOURCE_KEYS: Final = (
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
_FIXED_ENVIRONMENT: Final = (
    ("HOME", "/tmp/home"),
    ("PYTHONDONTWRITEBYTECODE", "1"),
    ("PYTHONHASHSEED", "0"),
    ("PYTHONUNBUFFERED", "1"),
    ("SOURCE_GIT_COMMIT", EXPECTED_SOURCE_COMMIT),
    ("EXPERIMENT_IMAGE_DIGEST", EXPECTED_IMAGE_DIGEST),
    ("EXPERIMENT_IMAGE_REPO_DIGEST", EXPECTED_IMAGE_REPO_DIGEST),
)
_HOST_ENVIRONMENT_BINDINGS: Final = (
    ("HIP_VISIBLE_DEVICES", "HIP_VISIBLE_DEVICES"),
    ("OMP_NUM_THREADS", "OMP_NUM_THREADS"),
    ("MKL_NUM_THREADS", "MKL_NUM_THREADS"),
    ("OPENBLAS_NUM_THREADS", "OPENBLAS_NUM_THREADS"),
    ("NUMEXPR_NUM_THREADS", "NUMEXPR_NUM_THREADS"),
)

__all__ = [
    "Attempt002HostImageIdentity",
    "Attempt002HostInvocationChainError",
    "Attempt002HostInvocationChainState",
    "HostInvocationContract",
    "HostInvocationResources",
    "HostMountContract",
    "HOST_INVOCATION_CHAIN_AUTHORIZED_STATUS",
    "LocalImageInspection",
    "MaterializedHostInvocation",
    "build_attempt_002_host_invocation_chain_state",
    "build_attempt_002_host_invocation_contract",
    "canonical_json",
    "load_attempt_002_host_execution_freeze",
    "load_attempt_002_host_image_identity",
    "materialize_attempt_002_host_invocation",
    "parse_attempt_002_local_image_inspection",
    "sha256_object",
    "validate_attempt_002_host_invocation_contract",
]


class Attempt002HostInvocationChainError(RuntimeError):
    """Raised when the attempt-002 host chain fails closed."""


def canonical_json(value: object) -> str:
    """Return deterministic UTF-8 JSON text."""

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
    """Hash a canonical JSON object."""

    return "sha256:" + hashlib.sha256(
        canonical_json(value).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class HostMountContract:
    """One exact future bind mount represented without applying it."""

    source_relative: str
    target: str
    access: str

    def require(self) -> None:
        if self.source_relative not in {
            FROZEN_EXPERIMENTS_RELATIVE.as_posix(),
            TORCH2PC_RELATIVE.as_posix(),
            RESULTS_RELATIVE.as_posix(),
        }:
            raise Attempt002HostInvocationChainError(
                "host mount source differs"
            )
        if self.target not in {
            "/workspace/experiments/frozen",
            "/workspace/external/Torch2PC",
            "/workspace/results",
        }:
            raise Attempt002HostInvocationChainError(
                "host mount target differs"
            )
        if self.access not in {"read_only", "read_write"}:
            raise Attempt002HostInvocationChainError(
                "host mount access differs"
            )
        if self.source_relative == RESULTS_RELATIVE.as_posix():
            if self.access != "read_write":
                raise Attempt002HostInvocationChainError(
                    "results mount is not read-write"
                )
        elif self.access != "read_only":
            raise Attempt002HostInvocationChainError(
                "immutable input mount is not read-only"
            )


@dataclass(frozen=True)
class Attempt002HostImageIdentity:
    """Normalized exact image identity from the ADR-113 freeze package."""

    schema_version: int
    record_id: str
    source_commit: str
    torch2pc_commit: str
    image_tag: str
    image_digest: str
    image_repo_digest: str
    image_size_bytes: int
    architecture: str
    os: str
    base_image: str
    container_workdir: str
    container_entrypoint: tuple[str, ...]
    capture_sha256: str
    identity_sha256: str

    def require(self, freeze: Attempt002ExecutionFreeze) -> None:
        expected: Mapping[str, object] = {
            "schema_version": 1,
            "record_id": HOST_IMAGE_IDENTITY_ID,
            "source_commit": EXPECTED_SOURCE_COMMIT,
            "torch2pc_commit": EXPECTED_TORCH2PC_COMMIT,
            "image_tag": EXPECTED_IMAGE_TAG,
            "image_digest": EXPECTED_IMAGE_DIGEST,
            "image_repo_digest": EXPECTED_IMAGE_REPO_DIGEST,
            "image_size_bytes": EXPECTED_IMAGE_SIZE_BYTES,
            "architecture": "amd64",
            "os": "linux",
            "base_image": EXPECTED_BASE_IMAGE,
            "container_workdir": CONTAINER_WORKDIR,
            "container_entrypoint": CONTAINER_IMAGE_ENTRYPOINT,
            "identity_sha256": EXPECTED_IMAGE_IDENTITY_SHA256,
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise Attempt002HostInvocationChainError(
                    f"host image identity differs: {field_name}"
                )
        _require_sha256(self.capture_sha256, "capture_sha256")
        if freeze.source_commit != self.source_commit:
            raise Attempt002HostInvocationChainError(
                "host image source and freeze differ"
            )
        if freeze.torch2pc_commit != self.torch2pc_commit:
            raise Attempt002HostInvocationChainError(
                "host image Torch2PC and freeze differ"
            )
        if freeze.image_digest != self.image_digest:
            raise Attempt002HostInvocationChainError(
                "host image digest and freeze differ"
            )
        if freeze.image_repo_digest != self.image_repo_digest:
            raise Attempt002HostInvocationChainError(
                "host image repository digest and freeze differ"
            )


@dataclass(frozen=True)
class LocalImageInspection:
    """Read-only local image inspection normalized from Docker JSON."""

    image_id: str
    repo_tags: tuple[str, ...]
    repo_digests: tuple[str, ...]
    architecture: str
    os: str
    size_bytes: int
    source_revision: str
    base_image: str
    source_environment_commit: str
    working_directory: str
    entrypoint: tuple[str, ...]
    inspection_sha256: str

    def require(self, expected: Attempt002HostImageIdentity) -> None:
        exact: Mapping[str, object] = {
            "image_id": expected.image_digest,
            "architecture": expected.architecture,
            "os": expected.os,
            "size_bytes": expected.image_size_bytes,
            "source_revision": expected.source_commit,
            "base_image": expected.base_image,
            "source_environment_commit": expected.source_commit,
            "working_directory": expected.container_workdir,
            "entrypoint": expected.container_entrypoint,
        }
        for field_name, expected_value in exact.items():
            if getattr(self, field_name) != expected_value:
                raise Attempt002HostInvocationChainError(
                    f"local image inspection differs: {field_name}"
                )
        if expected.image_tag not in self.repo_tags:
            raise Attempt002HostInvocationChainError(
                "local image tag is absent"
            )
        if expected.image_repo_digest not in self.repo_digests:
            raise Attempt002HostInvocationChainError(
                "local image repository digest is absent"
            )
        _require_sha256(self.inspection_sha256, "inspection_sha256")


@dataclass(frozen=True)
class HostInvocationResources:
    """Canonical host resource values for future command materialization."""

    host_uid: str
    host_gid: str
    video_gid: str
    render_gid: str
    hip_visible_devices: str
    cpuset_gpu: str
    memory_limit: str
    shm_size: str
    tmpfs_size: str
    omp_num_threads: str
    mkl_num_threads: str
    openblas_num_threads: str
    numexpr_num_threads: str

    @classmethod
    def from_mapping(
        cls,
        values: Mapping[str, str],
    ) -> HostInvocationResources:
        if set(values) != set(_REQUIRED_RESOURCE_KEYS):
            raise Attempt002HostInvocationChainError(
                "host resource key set differs"
            )
        for key, value in values.items():
            if not value or any(character.isspace() for character in value):
                raise Attempt002HostInvocationChainError(
                    f"host resource value differs: {key}"
                )
        identity_keys = (
            "HOST_UID",
            "HOST_GID",
            "VIDEO_GID",
            "RENDER_GID",
        )
        thread_keys = (
            "OMP_NUM_THREADS",
            "MKL_NUM_THREADS",
            "OPENBLAS_NUM_THREADS",
            "NUMEXPR_NUM_THREADS",
        )
        for key in identity_keys + thread_keys:
            if re.fullmatch(r"[0-9]+", values[key]) is None:
                raise Attempt002HostInvocationChainError(
                    f"host numeric resource differs: {key}"
                )
        for key in thread_keys:
            if int(values[key]) <= 0:
                raise Attempt002HostInvocationChainError(
                    f"host thread resource differs: {key}"
                )
        if re.fullmatch(r"[0-9]+(?:,[0-9]+)*", values["HIP_VISIBLE_DEVICES"]) is None:
            raise Attempt002HostInvocationChainError(
                "HIP_VISIBLE_DEVICES differs"
            )
        if (
            re.fullmatch(
                r"[0-9]+(?:-[0-9]+)?(?:,[0-9]+(?:-[0-9]+)?)*",
                values["CPUSET_GPU"],
            )
            is None
        ):
            raise Attempt002HostInvocationChainError("CPUSET_GPU differs")
        for key in ("MEM_LIMIT", "SHM_SIZE", "TMPFS_SIZE"):
            if re.fullmatch(r"[1-9][0-9]*(?:[kKmMgG])?", values[key]) is None:
                raise Attempt002HostInvocationChainError(
                    f"host size resource differs: {key}"
                )
        return cls(
            host_uid=values["HOST_UID"],
            host_gid=values["HOST_GID"],
            video_gid=values["VIDEO_GID"],
            render_gid=values["RENDER_GID"],
            hip_visible_devices=values["HIP_VISIBLE_DEVICES"],
            cpuset_gpu=values["CPUSET_GPU"],
            memory_limit=values["MEM_LIMIT"],
            shm_size=values["SHM_SIZE"],
            tmpfs_size=values["TMPFS_SIZE"],
            omp_num_threads=values["OMP_NUM_THREADS"],
            mkl_num_threads=values["MKL_NUM_THREADS"],
            openblas_num_threads=values["OPENBLAS_NUM_THREADS"],
            numexpr_num_threads=values["NUMEXPR_NUM_THREADS"],
        )

    def as_host_mapping(self) -> Mapping[str, str]:
        return {
            "HOST_UID": self.host_uid,
            "HOST_GID": self.host_gid,
            "VIDEO_GID": self.video_gid,
            "RENDER_GID": self.render_gid,
            "HIP_VISIBLE_DEVICES": self.hip_visible_devices,
            "CPUSET_GPU": self.cpuset_gpu,
            "MEM_LIMIT": self.memory_limit,
            "SHM_SIZE": self.shm_size,
            "TMPFS_SIZE": self.tmpfs_size,
            "OMP_NUM_THREADS": self.omp_num_threads,
            "MKL_NUM_THREADS": self.mkl_num_threads,
            "OPENBLAS_NUM_THREADS": self.openblas_num_threads,
            "NUMEXPR_NUM_THREADS": self.numexpr_num_threads,
        }


@dataclass(frozen=True)
class HostInvocationContract:
    """Complete future host invocation policy without executable authority."""

    schema_version: int
    contract_id: str
    status: str
    attempt_id: str
    freeze_sha256: str
    image_identity_sha256: str
    image_repo_digest: str
    source_commit: str
    torch2pc_commit: str
    container_runtime: str
    container_workdir: str
    container_image_entrypoint: tuple[str, ...]
    container_runtime_entrypoint: str
    output_root: str
    lease_v1_relative: str
    lease_v2_relative: str
    durable_outcome_relative: str
    required_host_resource_inputs: tuple[str, ...]
    fixed_environment: tuple[tuple[str, str], ...]
    host_environment_bindings: tuple[tuple[str, str], ...]
    mounts: tuple[HostMountContract, ...]
    device_bindings: tuple[tuple[str, str, str], ...]
    network_disabled: bool
    read_only_root_filesystem: bool
    no_new_privileges: bool
    drop_all_capabilities: bool
    automatic_remove_required: bool
    init_required: bool
    project_source_bind_forbidden: bool
    test_dataset_mount_forbidden: bool
    image_inspection_required: bool
    exact_repo_digest_required: bool
    shell_interpretation_forbidden: bool
    environment_inheritance_forbidden: bool
    automatic_retry_forbidden: bool
    claimed_at_utc_required: bool
    invocation_acknowledgement_required: bool
    lease_acknowledgement_required: bool
    authorization_required_before_invocation: bool
    host_command_materialization_present: bool
    host_process_spawner_present: bool
    docker_run_implemented: bool
    runtime_execution_permitted: bool
    contract_sha256: str

    def require(self) -> None:
        expected: Mapping[str, object] = {
            "schema_version": 1,
            "contract_id": HOST_INVOCATION_CONTRACT_ID,
            "status": HOST_INVOCATION_CHAIN_STATUS,
            "attempt_id": ATTEMPT_002_ID,
            "freeze_sha256": EXPECTED_FREEZE_SHA256,
            "image_identity_sha256": EXPECTED_IMAGE_IDENTITY_SHA256,
            "image_repo_digest": EXPECTED_IMAGE_REPO_DIGEST,
            "source_commit": EXPECTED_SOURCE_COMMIT,
            "torch2pc_commit": EXPECTED_TORCH2PC_COMMIT,
            "container_runtime": HOST_RUNTIME,
            "container_workdir": CONTAINER_WORKDIR,
            "container_image_entrypoint": CONTAINER_IMAGE_ENTRYPOINT,
            "container_runtime_entrypoint": CONTAINER_RUNTIME_ENTRYPOINT,
            "output_root": ATTEMPT_002_OUTPUT_ROOT.as_posix(),
            "lease_v1_relative": ATTEMPT_002_LEASE_V1_RELATIVE.as_posix(),
            "lease_v2_relative": ATTEMPT_002_LEASE_V2_RELATIVE.as_posix(),
            "durable_outcome_relative": (
                ATTEMPT_002_DURABLE_OUTCOME_RELATIVE.as_posix()
            ),
            "required_host_resource_inputs": _REQUIRED_RESOURCE_KEYS,
            "fixed_environment": _FIXED_ENVIRONMENT,
            "host_environment_bindings": _HOST_ENVIRONMENT_BINDINGS,
            "device_bindings": (
                ("/dev/kfd", "/dev/kfd", "rwm"),
                ("/dev/dri", "/dev/dri", "rwm"),
            ),
            "network_disabled": True,
            "read_only_root_filesystem": True,
            "no_new_privileges": True,
            "drop_all_capabilities": True,
            "automatic_remove_required": True,
            "init_required": True,
            "project_source_bind_forbidden": True,
            "test_dataset_mount_forbidden": True,
            "image_inspection_required": True,
            "exact_repo_digest_required": True,
            "shell_interpretation_forbidden": True,
            "environment_inheritance_forbidden": True,
            "automatic_retry_forbidden": True,
            "claimed_at_utc_required": True,
            "invocation_acknowledgement_required": True,
            "lease_acknowledgement_required": True,
            "authorization_required_before_invocation": True,
            "host_command_materialization_present": True,
            "host_process_spawner_present": False,
            "docker_run_implemented": False,
            "runtime_execution_permitted": False,
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise Attempt002HostInvocationChainError(
                    f"host invocation contract differs: {field_name}"
                )
        if len(self.mounts) != 3:
            raise Attempt002HostInvocationChainError(
                "host invocation mount count differs"
            )
        for mount in self.mounts:
            mount.require()
        _require_sha256(self.contract_sha256, "contract_sha256")
        if self.contract_sha256 != sha256_object(self._payload_without_digest()):
            raise Attempt002HostInvocationChainError(
                "host invocation contract digest differs"
            )

    def _payload_without_digest(self) -> Mapping[str, object]:
        payload = asdict(self)
        payload.pop("contract_sha256")
        return cast(Mapping[str, object], payload)

    def canonical_json(self) -> str:
        return canonical_json(asdict(self))


@dataclass(frozen=True)
class MaterializedHostInvocation:
    """Exact future Docker argv represented only as immutable data."""

    schema_version: int
    contract_sha256: str
    image_inspection_sha256: str
    claimed_at_utc: str
    argv: tuple[str, ...]
    environment: tuple[tuple[str, str], ...]
    mount_sources: tuple[str, ...]
    shell_interpretation_used: bool
    environment_inherited: bool
    subprocess_spawned: bool
    container_created: bool
    authorization_issued: bool
    authorization_consumed: bool
    execution_lease_created: bool
    runtime_execution_started: bool
    runtime_execution_performed: bool
    invocation_sha256: str

    def require(
        self,
        contract: HostInvocationContract,
        inspection: LocalImageInspection,
    ) -> None:
        expected: Mapping[str, object] = {
            "schema_version": 1,
            "contract_sha256": contract.contract_sha256,
            "image_inspection_sha256": inspection.inspection_sha256,
            "shell_interpretation_used": False,
            "environment_inherited": False,
            "subprocess_spawned": False,
            "container_created": False,
            "authorization_issued": False,
            "authorization_consumed": False,
            "execution_lease_created": False,
            "runtime_execution_started": False,
            "runtime_execution_performed": False,
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise Attempt002HostInvocationChainError(
                    f"materialized host invocation differs: {field_name}"
                )
        _require_rfc3339_seconds(self.claimed_at_utc)
        if not self.argv or self.argv[0:2] != ("docker", "run"):
            raise Attempt002HostInvocationChainError(
                "materialized host argv prefix differs"
            )
        if contract.image_repo_digest not in self.argv:
            raise Attempt002HostInvocationChainError(
                "materialized host argv image differs"
            )
        if "--network" not in self.argv or "none" not in self.argv:
            raise Attempt002HostInvocationChainError(
                "materialized host network policy differs"
            )
        if "--read-only" not in self.argv:
            raise Attempt002HostInvocationChainError(
                "materialized host root policy differs"
            )
        if "--cap-drop" not in self.argv or "ALL" not in self.argv:
            raise Attempt002HostInvocationChainError(
                "materialized host capability policy differs"
            )
        if any(
            ":/workspace/data" in argument.casefold()
            or argument.casefold().startswith("/workspace/data")
            for argument in self.argv
        ):
            raise Attempt002HostInvocationChainError(
                "materialized host dataset mount is present"
            )
        _require_sha256(self.invocation_sha256, "invocation_sha256")
        if self.invocation_sha256 != sha256_object(self._payload_without_digest()):
            raise Attempt002HostInvocationChainError(
                "materialized host invocation digest differs"
            )

    def _payload_without_digest(self) -> Mapping[str, object]:
        payload = asdict(self)
        payload.pop("invocation_sha256")
        return cast(Mapping[str, object], payload)


@dataclass(frozen=True)
class Attempt002HostInvocationChainState:
    """Machine-checkable authoring state with all runtime effects closed."""

    schema_version: int
    chain_id: str
    status: str
    freeze_sha256: str
    image_identity_sha256: str
    contract_sha256: str
    host_image_identity_present: bool
    host_invocation_contract_present: bool
    host_command_materialization_present: bool
    host_process_spawner_present: bool
    docker_run_implemented: bool
    authorization_authoring_admissible: bool
    authorization_issued: bool
    authorization_consumed: bool
    lease_v1_present: bool
    lease_v2_present: bool
    durable_outcome_present: bool
    runtime_execution_started: bool
    runtime_execution_performed: bool
    scientific_execution_open: bool
    test_dataset_access: bool
    publication_permitted: bool
    state_sha256: str

    def require(self) -> None:
        expected_status = (
            HOST_INVOCATION_CHAIN_AUTHORIZED_STATUS
            if self.authorization_issued
            else HOST_INVOCATION_CHAIN_STATUS
        )
        expected: Mapping[str, object] = {
            "schema_version": 1,
            "chain_id": HOST_INVOCATION_CHAIN_ID,
            "status": expected_status,
            "freeze_sha256": EXPECTED_FREEZE_SHA256,
            "image_identity_sha256": EXPECTED_IMAGE_IDENTITY_SHA256,
            "host_image_identity_present": True,
            "host_invocation_contract_present": True,
            "host_command_materialization_present": True,
            "host_process_spawner_present": False,
            "docker_run_implemented": False,
            "authorization_authoring_admissible": not self.authorization_issued,
            "authorization_consumed": False,
            "lease_v1_present": False,
            "lease_v2_present": False,
            "durable_outcome_present": False,
            "runtime_execution_started": False,
            "runtime_execution_performed": False,
            "scientific_execution_open": False,
            "test_dataset_access": False,
            "publication_permitted": False,
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise Attempt002HostInvocationChainError(
                    f"host invocation chain state differs: {field_name}"
                )
        for value, field_name in (
            (self.contract_sha256, "contract_sha256"),
            (self.state_sha256, "state_sha256"),
        ):
            _require_sha256(value, field_name)
        if self.state_sha256 != sha256_object(self._payload_without_digest()):
            raise Attempt002HostInvocationChainError(
                "host invocation chain state digest differs"
            )

    def _payload_without_digest(self) -> Mapping[str, object]:
        payload = asdict(self)
        payload.pop("state_sha256")
        return cast(Mapping[str, object], payload)



def load_attempt_002_host_execution_freeze(
    project_root: Path,
) -> Attempt002ExecutionFreeze:
    """Verify the committed execution freeze without runtime environment input."""

    root = project_root.expanduser().resolve()
    mapping = _read_json_object(root / ATTEMPT_002_FREEZE_RELATIVE)
    freeze = Attempt002ExecutionFreeze(**cast(dict[str, Any], mapping))
    freeze.require()
    _verify_registry(
        root / ATTEMPT_002_FREEZE_ROOT / "SHA256SUMS",
        root / ATTEMPT_002_FREEZE_ROOT,
    )
    _verify_registry(
        root / ATTEMPT_002_FREEZE_ROOT / "source-SHA256SUMS",
        root,
    )
    return freeze

def load_attempt_002_host_image_identity(
    project_root: Path,
    freeze: Attempt002ExecutionFreeze | None = None,
) -> Attempt002HostImageIdentity:
    """Load and validate the ADR-113 image identity record."""

    root = project_root.expanduser().resolve()
    verified_freeze = freeze or load_attempt_002_host_execution_freeze(root)
    record = _read_json_object(root / HOST_IMAGE_IDENTITY_RELATIVE)
    entrypoint = _as_string_tuple(
        record.get("container_entrypoint"),
        "container_entrypoint",
    )
    identity = Attempt002HostImageIdentity(
        schema_version=_as_int(record.get("schema_version"), "schema_version"),
        record_id=_as_str(record.get("record_id"), "record_id"),
        source_commit=_as_str(record.get("source_commit"), "source_commit"),
        torch2pc_commit=_as_str(record.get("torch2pc_commit"), "torch2pc_commit"),
        image_tag=_as_str(record.get("image_tag"), "image_tag"),
        image_digest=_as_str(record.get("image_digest"), "image_digest"),
        image_repo_digest=_as_str(record.get("image_repo_digest"), "image_repo_digest"),
        image_size_bytes=_as_int(record.get("image_size_bytes"), "image_size_bytes"),
        architecture=_as_str(record.get("architecture"), "architecture"),
        os=_as_str(record.get("os"), "os"),
        base_image=_as_str(record.get("base_image"), "base_image"),
        container_workdir=_as_str(record.get("container_workdir"), "container_workdir"),
        container_entrypoint=entrypoint,
        capture_sha256=_as_str(record.get("capture_sha256"), "capture_sha256"),
        identity_sha256=_as_str(record.get("identity_sha256"), "identity_sha256"),
    )
    identity.require(verified_freeze)
    return identity


def build_attempt_002_host_invocation_contract(
    project_root: Path,
) -> HostInvocationContract:
    """Build the pure host invocation contract from the corrected freeze."""

    root = project_root.expanduser().resolve()
    _require_effect_boundary(root)
    freeze = load_attempt_002_host_execution_freeze(root)
    if freeze.freeze_sha256 != EXPECTED_FREEZE_SHA256:
        raise Attempt002HostInvocationChainError(
            "attempt-002 execution freeze identity differs"
        )
    identity = load_attempt_002_host_image_identity(root, freeze)
    mounts = (
        HostMountContract(
            source_relative=FROZEN_EXPERIMENTS_RELATIVE.as_posix(),
            target="/workspace/experiments/frozen",
            access="read_only",
        ),
        HostMountContract(
            source_relative=TORCH2PC_RELATIVE.as_posix(),
            target="/workspace/external/Torch2PC",
            access="read_only",
        ),
        HostMountContract(
            source_relative=RESULTS_RELATIVE.as_posix(),
            target="/workspace/results",
            access="read_write",
        ),
    )
    payload: dict[str, object] = {
        "schema_version": 1,
        "contract_id": HOST_INVOCATION_CONTRACT_ID,
        "status": HOST_INVOCATION_CHAIN_STATUS,
        "attempt_id": ATTEMPT_002_ID,
        "freeze_sha256": freeze.freeze_sha256,
        "image_identity_sha256": identity.identity_sha256,
        "image_repo_digest": identity.image_repo_digest,
        "source_commit": identity.source_commit,
        "torch2pc_commit": identity.torch2pc_commit,
        "container_runtime": HOST_RUNTIME,
        "container_workdir": CONTAINER_WORKDIR,
        "container_image_entrypoint": CONTAINER_IMAGE_ENTRYPOINT,
        "container_runtime_entrypoint": CONTAINER_RUNTIME_ENTRYPOINT,
        "output_root": ATTEMPT_002_OUTPUT_ROOT.as_posix(),
        "lease_v1_relative": ATTEMPT_002_LEASE_V1_RELATIVE.as_posix(),
        "lease_v2_relative": ATTEMPT_002_LEASE_V2_RELATIVE.as_posix(),
        "durable_outcome_relative": ATTEMPT_002_DURABLE_OUTCOME_RELATIVE.as_posix(),
        "required_host_resource_inputs": _REQUIRED_RESOURCE_KEYS,
        "fixed_environment": _FIXED_ENVIRONMENT,
        "host_environment_bindings": _HOST_ENVIRONMENT_BINDINGS,
        "mounts": tuple(asdict(mount) for mount in mounts),
        "device_bindings": (
            ("/dev/kfd", "/dev/kfd", "rwm"),
            ("/dev/dri", "/dev/dri", "rwm"),
        ),
        "network_disabled": True,
        "read_only_root_filesystem": True,
        "no_new_privileges": True,
        "drop_all_capabilities": True,
        "automatic_remove_required": True,
        "init_required": True,
        "project_source_bind_forbidden": True,
        "test_dataset_mount_forbidden": True,
        "image_inspection_required": True,
        "exact_repo_digest_required": True,
        "shell_interpretation_forbidden": True,
        "environment_inheritance_forbidden": True,
        "automatic_retry_forbidden": True,
        "claimed_at_utc_required": True,
        "invocation_acknowledgement_required": True,
        "lease_acknowledgement_required": True,
        "authorization_required_before_invocation": True,
        "host_command_materialization_present": True,
        "host_process_spawner_present": False,
        "docker_run_implemented": False,
        "runtime_execution_permitted": False,
    }
    contract_values = dict(payload)
    contract_values["mounts"] = mounts
    contract = HostInvocationContract(
        **cast(dict[str, Any], contract_values),
        contract_sha256=sha256_object(payload),
    )
    contract.require()
    return contract


def validate_attempt_002_host_invocation_contract(
    contract: HostInvocationContract,
) -> None:
    """Validate a host invocation contract."""

    contract.require()


def parse_attempt_002_local_image_inspection(
    raw_json: str | bytes,
    expected: Attempt002HostImageIdentity,
) -> LocalImageInspection:
    """Parse Docker inspect JSON without invoking Docker."""

    try:
        payload = json.loads(raw_json)
    except (json.JSONDecodeError, UnicodeDecodeError, TypeError) as exc:
        raise Attempt002HostInvocationChainError(
            "local image inspection JSON is invalid"
        ) from exc
    if not isinstance(payload, list) or len(payload) != 1:
        raise Attempt002HostInvocationChainError(
            "local image inspection record count differs"
        )
    record = _as_mapping(payload[0], "image inspection")
    config = _as_mapping(record.get("Config"), "Config")
    labels = _as_string_mapping(config.get("Labels"), "Labels")
    environment: dict[str, str] = {}
    for item in _as_string_tuple(config.get("Env"), "Env"):
        if "=" not in item:
            raise Attempt002HostInvocationChainError(
                "local image environment entry differs"
            )
        key, value = item.split("=", 1)
        environment[key] = value
    image_id = _as_str(record.get("Id"), "Id")
    repo_tags = _as_string_tuple(record.get("RepoTags"), "RepoTags")
    repo_digests = _as_string_tuple(record.get("RepoDigests"), "RepoDigests")
    architecture = _as_str(record.get("Architecture"), "Architecture")
    operating_system = _as_str(record.get("Os"), "Os")
    size_bytes = _as_int(record.get("Size"), "Size")
    source_revision = labels.get("org.opencontainers.image.revision", "")
    base_image = labels.get("io.torch2pc.base-image", "")
    source_environment_commit = environment.get("SOURCE_GIT_COMMIT", "")
    working_directory = _as_str(config.get("WorkingDir"), "WorkingDir")
    entrypoint = _as_string_tuple(config.get("Entrypoint"), "Entrypoint")
    normalized_payload: dict[str, object] = {
        "image_id": image_id,
        "repo_tags": repo_tags,
        "repo_digests": repo_digests,
        "architecture": architecture,
        "os": operating_system,
        "size_bytes": size_bytes,
        "source_revision": source_revision,
        "base_image": base_image,
        "source_environment_commit": source_environment_commit,
        "working_directory": working_directory,
        "entrypoint": entrypoint,
    }
    inspection = LocalImageInspection(
        image_id=image_id,
        repo_tags=repo_tags,
        repo_digests=repo_digests,
        architecture=architecture,
        os=operating_system,
        size_bytes=size_bytes,
        source_revision=source_revision,
        base_image=base_image,
        source_environment_commit=source_environment_commit,
        working_directory=working_directory,
        entrypoint=entrypoint,
        inspection_sha256=sha256_object(normalized_payload),
    )
    inspection.require(expected)
    return inspection


def materialize_attempt_002_host_invocation(
    project_root: Path,
    contract: HostInvocationContract,
    inspection: LocalImageInspection,
    resources: HostInvocationResources,
    *,
    claimed_at_utc: str,
    invocation_acknowledgement: str,
    lease_acknowledgement: str,
) -> MaterializedHostInvocation:
    """Construct exact future Docker argv without spawning any process."""

    root = project_root.expanduser().resolve()
    _require_effect_boundary(root)
    contract.require()
    identity = load_attempt_002_host_image_identity(root)
    inspection.require(identity)
    _require_rfc3339_seconds(claimed_at_utc)
    if invocation_acknowledgement != ATTEMPT_002_INVOCATION_ACKNOWLEDGEMENT:
        raise Attempt002HostInvocationChainError(
            "attempt-002 invocation acknowledgement differs"
        )
    if lease_acknowledgement != ATTEMPT_002_LEASE_ACKNOWLEDGEMENT:
        raise Attempt002HostInvocationChainError(
            "attempt-002 lease acknowledgement differs"
        )
    host_values = resources.as_host_mapping()
    environment = list(contract.fixed_environment)
    for container_key, host_key in contract.host_environment_bindings:
        environment.append((container_key, host_values[host_key]))

    argv: list[str] = [
        "docker",
        "run",
        "--rm",
        "--init",
        "--network",
        "none",
        "--read-only",
        "--security-opt",
        "no-new-privileges",
        "--cap-drop",
        "ALL",
        "--user",
        f"{resources.host_uid}:{resources.host_gid}",
        "--group-add",
        resources.video_gid,
        "--group-add",
        resources.render_gid,
        "--device",
        "/dev/kfd:/dev/kfd:rwm",
        "--device",
        "/dev/dri:/dev/dri:rwm",
        "--cpuset-cpus",
        resources.cpuset_gpu,
        "--memory",
        resources.memory_limit,
        "--shm-size",
        resources.shm_size,
        "--tmpfs",
        f"/tmp:rw,nosuid,nodev,mode=1777,size={resources.tmpfs_size}",
        "--workdir",
        contract.container_workdir,
    ]
    for key, value in environment:
        argv.extend(("--env", f"{key}={value}"))

    mount_sources: list[str] = []
    for mount in contract.mounts:
        source = (root / mount.source_relative).resolve()
        _require_below_root(root, source)
        mount_sources.append(str(source))
        suffix = ":ro" if mount.access == "read_only" else ":rw"
        argv.extend(("--volume", f"{source}:{mount.target}{suffix}"))

    argv.extend(
        (
            contract.image_repo_digest,
            "python",
            contract.container_runtime_entrypoint,
            "--project-root",
            contract.container_workdir,
            "--torch2pc-dir",
            "/workspace/external/Torch2PC",
            "--claimed-at-utc",
            claimed_at_utc,
            "--operator-acknowledgement",
            lease_acknowledgement,
        )
    )
    payload: dict[str, object] = {
        "schema_version": 1,
        "contract_sha256": contract.contract_sha256,
        "image_inspection_sha256": inspection.inspection_sha256,
        "claimed_at_utc": claimed_at_utc,
        "argv": tuple(argv),
        "environment": tuple(environment),
        "mount_sources": tuple(mount_sources),
        "shell_interpretation_used": False,
        "environment_inherited": False,
        "subprocess_spawned": False,
        "container_created": False,
        "authorization_issued": False,
        "authorization_consumed": False,
        "execution_lease_created": False,
        "runtime_execution_started": False,
        "runtime_execution_performed": False,
    }
    materialized = MaterializedHostInvocation(
        schema_version=1,
        contract_sha256=contract.contract_sha256,
        image_inspection_sha256=inspection.inspection_sha256,
        claimed_at_utc=claimed_at_utc,
        argv=tuple(argv),
        environment=tuple(environment),
        mount_sources=tuple(mount_sources),
        shell_interpretation_used=False,
        environment_inherited=False,
        subprocess_spawned=False,
        container_created=False,
        authorization_issued=False,
        authorization_consumed=False,
        execution_lease_created=False,
        runtime_execution_started=False,
        runtime_execution_performed=False,
        invocation_sha256=sha256_object(payload),
    )
    materialized.require(contract, inspection)
    return materialized


def build_attempt_002_host_invocation_chain_state(
    project_root: Path,
) -> Attempt002HostInvocationChainState:
    """Build the current host chain state without starting execution."""

    root = project_root.expanduser().resolve()
    _require_effect_boundary(root)
    contract = build_attempt_002_host_invocation_contract(root)
    authorization_path = root / ATTEMPT_002_AUTHORIZATION_ROOT / "authorization.json"
    authorization_issued = authorization_path.is_file() and not authorization_path.is_symlink()
    if authorization_issued:
        freeze = load_attempt_002_host_execution_freeze(root)
        verify_unconsumed_attempt_002_authorization(root, freeze)
    status = (
        HOST_INVOCATION_CHAIN_AUTHORIZED_STATUS
        if authorization_issued
        else HOST_INVOCATION_CHAIN_STATUS
    )
    authorization_authoring_admissible = not authorization_issued
    payload: dict[str, object] = {
        "schema_version": 1,
        "chain_id": HOST_INVOCATION_CHAIN_ID,
        "status": status,
        "freeze_sha256": EXPECTED_FREEZE_SHA256,
        "image_identity_sha256": EXPECTED_IMAGE_IDENTITY_SHA256,
        "contract_sha256": contract.contract_sha256,
        "host_image_identity_present": True,
        "host_invocation_contract_present": True,
        "host_command_materialization_present": True,
        "host_process_spawner_present": False,
        "docker_run_implemented": False,
        "authorization_authoring_admissible": authorization_authoring_admissible,
        "authorization_issued": authorization_issued,
        "authorization_consumed": False,
        "lease_v1_present": False,
        "lease_v2_present": False,
        "durable_outcome_present": False,
        "runtime_execution_started": False,
        "runtime_execution_performed": False,
        "scientific_execution_open": False,
        "test_dataset_access": False,
        "publication_permitted": False,
    }
    state = Attempt002HostInvocationChainState(
        schema_version=1,
        chain_id=HOST_INVOCATION_CHAIN_ID,
        status=status,
        freeze_sha256=EXPECTED_FREEZE_SHA256,
        image_identity_sha256=EXPECTED_IMAGE_IDENTITY_SHA256,
        contract_sha256=contract.contract_sha256,
        host_image_identity_present=True,
        host_invocation_contract_present=True,
        host_command_materialization_present=True,
        host_process_spawner_present=False,
        docker_run_implemented=False,
        authorization_authoring_admissible=authorization_authoring_admissible,
        authorization_issued=authorization_issued,
        authorization_consumed=False,
        lease_v1_present=False,
        lease_v2_present=False,
        durable_outcome_present=False,
        runtime_execution_started=False,
        runtime_execution_performed=False,
        scientific_execution_open=False,
        test_dataset_access=False,
        publication_permitted=False,
        state_sha256=sha256_object(payload),
    )
    state.require()
    return state


def _require_effect_boundary(root: Path) -> None:
    for relative in (
        ATTEMPT_002_OUTPUT_ROOT,
        ATTEMPT_002_LEASE_V1_RELATIVE,
        ATTEMPT_002_LEASE_V2_RELATIVE,
        ATTEMPT_002_DURABLE_OUTCOME_RELATIVE,
    ):
        path = root / relative
        if path.exists() or path.is_symlink():
            raise Attempt002HostInvocationChainError(
                f"attempt-002 closed effect exists: {relative.as_posix()}"
            )


def _read_json_object(path: Path) -> dict[str, object]:
    if not path.is_file() or path.is_symlink():
        raise Attempt002HostInvocationChainError(
            f"required JSON file differs: {path}"
        )
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise Attempt002HostInvocationChainError(
            f"required JSON file is invalid: {path}"
        ) from exc
    if not isinstance(value, dict):
        raise Attempt002HostInvocationChainError(
            f"required JSON object differs: {path}"
        )
    if path.read_bytes() != canonical_json(value).encode("utf-8"):
        raise Attempt002HostInvocationChainError(
            f"required JSON serialization differs: {path}"
        )
    return cast(dict[str, object], value)


def _verify_registry(registry_path: Path, base: Path) -> None:
    if not registry_path.is_file() or registry_path.is_symlink():
        raise Attempt002HostInvocationChainError(
            f"required registry differs: {registry_path}"
        )
    for raw_line in registry_path.read_text(encoding="utf-8").splitlines():
        if not raw_line:
            continue
        digest, separator, relative = raw_line.partition("  ")
        if separator != "  " or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise Attempt002HostInvocationChainError(
                f"registry line differs: {registry_path}"
            )
        target = (base / relative).resolve()
        _require_below_root(base.resolve(), target)
        if not target.is_file() or target.is_symlink():
            raise Attempt002HostInvocationChainError(
                f"registry target differs: {relative}"
            )
        observed = hashlib.sha256(target.read_bytes()).hexdigest()
        if observed != digest:
            raise Attempt002HostInvocationChainError(
                f"registry target digest differs: {relative}"
            )


def _require_below_root(root: Path, path: Path) -> None:
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise Attempt002HostInvocationChainError(
            "host mount source leaves project root"
        ) from exc


def _require_rfc3339_seconds(value: str) -> None:
    if re.fullmatch(
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z",
        value,
    ) is None:
        raise Attempt002HostInvocationChainError(
            "claimed_at_utc is not RFC3339 seconds"
        )


def _require_sha256(value: str, field_name: str) -> None:
    if re.fullmatch(r"sha256:[0-9a-f]{64}", value) is None:
        raise Attempt002HostInvocationChainError(
            f"{field_name} is not canonical SHA-256"
        )


def _as_mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise Attempt002HostInvocationChainError(
            f"{field_name} is not an object"
        )
    return cast(Mapping[str, object], value)


def _as_string_mapping(value: object, field_name: str) -> Mapping[str, str]:
    mapping = _as_mapping(value, field_name)
    if not all(
        isinstance(key, str) and isinstance(item, str)
        for key, item in mapping.items()
    ):
        raise Attempt002HostInvocationChainError(
            f"{field_name} is not a string mapping"
        )
    return cast(Mapping[str, str], mapping)


def _as_string_tuple(value: object, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, str | bytes):
        raise Attempt002HostInvocationChainError(
            f"{field_name} is not a sequence"
        )
    if not all(isinstance(item, str) for item in value):
        raise Attempt002HostInvocationChainError(
            f"{field_name} contains a non-string"
        )
    return tuple(cast(Sequence[str], value))


def _as_str(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise Attempt002HostInvocationChainError(
            f"{field_name} is not a string"
        )
    return value


def _as_int(value: object, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise Attempt002HostInvocationChainError(
            f"{field_name} is not an integer"
        )
    return value
