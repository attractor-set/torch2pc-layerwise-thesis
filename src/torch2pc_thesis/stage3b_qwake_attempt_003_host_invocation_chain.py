"""Pure host invocation chain for QWake Attempt-003.

This module defines the exact future Docker invocation as data.  It can parse
already-captured ``docker image inspect`` JSON and can construct an argv vector
in memory, but it contains no process spawner and performs no Docker operation.
It does not consume authorization, create a lease or outcome, invoke runtime or
model code, access a dataset, or publish evidence.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Final, cast

ATTEMPT_ID: Final = "stage3b-qwake-lc4-runtime-validation-v1-attempt-003"
HOST_INVOCATION_CHAIN_ID: Final = (
    "stage3b-qwake-attempt-003-host-invocation-chain-v1"
)
HOST_INVOCATION_CONTRACT_ID: Final = (
    "stage3b-qwake-attempt-003-host-invocation-contract-v1"
)
HOST_INVOCATION_STATUS: Final = (
    "attempt_003_host_invocation_chain_authored_execution_not_permitted"
)
AUTHORIZED_PARENT_HEAD: Final = "e7a0fb92d17bdb9a1165f211db7a1e94ff296999"
SOURCE_COMMIT: Final = "541b34a57297d2c5a82851bd846b583d4904fba6"
TORCH2PC_COMMIT: Final = "b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4"
FREEZE_SHA256: Final = (
    "sha256:82e7509a0d2627f8b91daa34049307da573619b740a2022b72b922edcd07898e"
)
AUTHORIZATION_ID: Final = "stage3b-qwake-attempt-003-authorization-v1"
AUTHORIZATION_SHA256: Final = (
    "sha256:46baed5cebc1efe4abf68c21652775eee5c1123df09465d332c151303d890d63"
)
AUTHORIZATION_ACTION_PHRASE: Final = (
    "AUTHORIZE_QWAKE_LC4_ATTEMPT_003_ONE_SHOT_ENGINEERING_INVOCATION"
)
LEASE_ACKNOWLEDGEMENT: Final = (
    "CLAIM_QWAKE_LC4_ATTEMPT_003_FROM_CORRECTED_EXECUTION_FREEZE"
)
IMAGE_DIGEST: Final = (
    "sha256:aec2178f1de409143553ccaecb34b2d0e4d19332040fce56742e422f770ef188"
)
IMAGE_REPO_DIGEST: Final = (
    "torch2pc-layerwise-thesis@"
    "sha256:aec2178f1de409143553ccaecb34b2d0e4d19332040fce56742e422f770ef188"
)
IMPLEMENTATION_RECORD_SHA256: Final = (
    "sha256:06ea2a9133cc9c008017e7cc7ca3c38e4d88a6ad6da05a44b361846a335e8342"
)
SOURCE_BINDING_CONTRACT_SHA256: Final = (
    "sha256:7b7e6ab40c5a77bb88e1c6ff18fca341fe87df6af7285c7916d8de8c5253d333"
)
BASE_IMAGE: Final = (
    "rocm/pytorch@"
    "sha256:96a2fb24dec9896e2f8238178f0c49d0dcc4c7dcc597be09e4564316bd86d191"
)
CONTAINER_RUNTIME: Final = "docker"
CONTAINER_WORKDIR: Final = "/workspace"
CONTAINER_IMAGE_ENTRYPOINT: Final = (
    "/usr/bin/tini",
    "--",
    "/workspace/scripts/container_entrypoint.sh",
)
CONTAINER_RUNTIME_ENTRYPOINT: Final = (
    "/workspace/scripts/run_stage3b_qwake_attempt_003_authorized_runtime.py"
)
OUTPUT_ROOT: Final = "results/stage-3/qwake-lc4-runtime-validation-v1-attempt-003"
LEASE_V1_RELATIVE: Final = OUTPUT_ROOT + ".execution-lease.json"
LEASE_V2_RELATIVE: Final = OUTPUT_ROOT + ".execution-lease-v2.json"
DURABLE_OUTCOME_RELATIVE: Final = OUTPUT_ROOT + ".host-outcome.json"

FROZEN_EXPERIMENTS_RELATIVE: Final = Path("experiments/frozen")
TORCH2PC_RELATIVE: Final = Path("external/Torch2PC")
RESULTS_RELATIVE: Final = Path("results")

REQUIRED_RESOURCE_KEYS: Final = (
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
FIXED_ENVIRONMENT: Final = (
    ("HOME", "/tmp/home"),
    ("PYTHONDONTWRITEBYTECODE", "1"),
    ("PYTHONHASHSEED", "0"),
    ("PYTHONUNBUFFERED", "1"),
    ("SOURCE_GIT_COMMIT", SOURCE_COMMIT),
    ("EXPERIMENT_IMAGE_DIGEST", IMAGE_DIGEST),
    ("EXPERIMENT_IMAGE_REPO_DIGEST", IMAGE_REPO_DIGEST),
)
HOST_ENVIRONMENT_BINDINGS: Final = (
    ("HIP_VISIBLE_DEVICES", "HIP_VISIBLE_DEVICES"),
    ("OMP_NUM_THREADS", "OMP_NUM_THREADS"),
    ("MKL_NUM_THREADS", "MKL_NUM_THREADS"),
    ("OPENBLAS_NUM_THREADS", "OPENBLAS_NUM_THREADS"),
    ("NUMEXPR_NUM_THREADS", "NUMEXPR_NUM_THREADS"),
)

__all__ = [
    "AUTHORIZATION_ACTION_PHRASE",
    "AUTHORIZATION_SHA256",
    "AUTHORIZED_PARENT_HEAD",
    "BASE_IMAGE",
    "CONTAINER_IMAGE_ENTRYPOINT",
    "FREEZE_SHA256",
    "HOST_INVOCATION_CHAIN_ID",
    "HOST_INVOCATION_CONTRACT_ID",
    "HOST_INVOCATION_STATUS",
    "HostInvocationContract",
    "HostInvocationResources",
    "HostMountContract",
    "IMAGE_DIGEST",
    "IMAGE_REPO_DIGEST",
    "IMPLEMENTATION_RECORD_SHA256",
    "LEASE_ACKNOWLEDGEMENT",
    "LocalImageInspection",
    "MaterializedHostInvocation",
    "QWakeAttempt003HostInvocationChainError",
    "SOURCE_BINDING_CONTRACT_SHA256",
    "SOURCE_COMMIT",
    "TORCH2PC_COMMIT",
    "build_attempt_003_host_invocation_contract",
    "canonical_json",
    "load_attempt_003_host_invocation_contract",
    "materialize_attempt_003_host_invocation",
    "parse_attempt_003_local_image_inspection",
    "sha256_object",
]


class QWakeAttempt003HostInvocationChainError(RuntimeError):
    """Raised when the Attempt-003 host invocation chain differs."""


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
    if re.fullmatch(r"sha256:[0-9a-f]{64}", value) is None:
        raise QWakeAttempt003HostInvocationChainError(
            f"invalid SHA-256 field: {field_name}"
        )


def _require_rfc3339_seconds(value: str) -> None:
    if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", value) is None:
        raise QWakeAttempt003HostInvocationChainError(
            "claimed_at_utc must be RFC3339 UTC seconds"
        )


@dataclass(frozen=True)
class HostMountContract:
    source_relative: str
    target: str
    access: str

    def require(self) -> None:
        allowed = {
            FROZEN_EXPERIMENTS_RELATIVE.as_posix(): (
                "/workspace/experiments/frozen",
                "read_only",
            ),
            TORCH2PC_RELATIVE.as_posix(): (
                "/workspace/external/Torch2PC",
                "read_only",
            ),
            RESULTS_RELATIVE.as_posix(): (
                "/workspace/results",
                "read_write",
            ),
        }
        if self.source_relative not in allowed:
            raise QWakeAttempt003HostInvocationChainError(
                "host mount source differs"
            )
        if (self.target, self.access) != allowed[self.source_relative]:
            raise QWakeAttempt003HostInvocationChainError(
                "host mount target/access differs"
            )


@dataclass(frozen=True)
class HostInvocationResources:
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
        if set(values) != set(REQUIRED_RESOURCE_KEYS):
            raise QWakeAttempt003HostInvocationChainError(
                "host resource key set differs"
            )
        for key, value in values.items():
            if not value or any(character.isspace() for character in value):
                raise QWakeAttempt003HostInvocationChainError(
                    f"host resource value differs: {key}"
                )
        numeric = (
            "HOST_UID",
            "HOST_GID",
            "VIDEO_GID",
            "RENDER_GID",
            "OMP_NUM_THREADS",
            "MKL_NUM_THREADS",
            "OPENBLAS_NUM_THREADS",
            "NUMEXPR_NUM_THREADS",
        )
        for key in numeric:
            if re.fullmatch(r"[0-9]+", values[key]) is None:
                raise QWakeAttempt003HostInvocationChainError(
                    f"numeric host resource differs: {key}"
                )
        for key in numeric[4:]:
            if int(values[key]) <= 0:
                raise QWakeAttempt003HostInvocationChainError(
                    f"thread host resource differs: {key}"
                )
        if re.fullmatch(r"[0-9]+(?:,[0-9]+)*", values["HIP_VISIBLE_DEVICES"]) is None:
            raise QWakeAttempt003HostInvocationChainError(
                "HIP_VISIBLE_DEVICES differs"
            )
        if re.fullmatch(
            r"[0-9]+(?:-[0-9]+)?(?:,[0-9]+(?:-[0-9]+)?)*",
            values["CPUSET_GPU"],
        ) is None:
            raise QWakeAttempt003HostInvocationChainError("CPUSET_GPU differs")
        for key in ("MEM_LIMIT", "SHM_SIZE", "TMPFS_SIZE"):
            if re.fullmatch(r"[1-9][0-9]*(?:[kKmMgG])?", values[key]) is None:
                raise QWakeAttempt003HostInvocationChainError(
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
    schema_version: int
    contract_id: str
    contract_sha256: str
    status: str
    attempt_id: str
    authorized_parent_head: str
    freeze_sha256: str
    authorization_id: str
    authorization_sha256: str
    authorization_action_phrase: str
    authorization_required_before_invocation: bool
    authorization_consumption_owner: str
    execution_count: int
    source_commit: str
    torch2pc_commit: str
    image_digest: str
    image_repo_digest: str
    base_image: str
    historical_implementation_record_sha256: str
    source_binding_contract_sha256: str
    historical_implementation_host_invocation_chain_authored: bool
    source_binding_host_invocation_chain_authored: bool
    source_binding_torch2pc_readonly_mount_required: bool
    historical_records_rewritten: bool
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
    lease_acknowledgement_required: bool
    lease_acknowledgement: str
    host_command_constructor_authored: bool
    host_command_materialized: bool
    host_process_spawner_present: bool
    docker_run_implemented: bool
    runtime_execution_permitted: bool
    authorization_used: bool
    authorization_consumed: bool
    attempt_started: bool
    execution_lease_materialized: bool
    durable_outcome_present: bool
    runtime_execution_started: bool
    runtime_execution_performed: bool
    scientific_execution_open: bool
    test_dataset_access: bool
    publication_permitted: bool

    def require(self) -> None:
        expected: Mapping[str, object] = {
            "schema_version": 1,
            "contract_id": HOST_INVOCATION_CONTRACT_ID,
            "status": HOST_INVOCATION_STATUS,
            "attempt_id": ATTEMPT_ID,
            "authorized_parent_head": AUTHORIZED_PARENT_HEAD,
            "freeze_sha256": FREEZE_SHA256,
            "authorization_id": AUTHORIZATION_ID,
            "authorization_sha256": AUTHORIZATION_SHA256,
            "authorization_action_phrase": AUTHORIZATION_ACTION_PHRASE,
            "authorization_required_before_invocation": True,
            "authorization_consumption_owner": "container_entrypoint_atomic_execution_lease",
            "execution_count": 1,
            "source_commit": SOURCE_COMMIT,
            "torch2pc_commit": TORCH2PC_COMMIT,
            "image_digest": IMAGE_DIGEST,
            "image_repo_digest": IMAGE_REPO_DIGEST,
            "base_image": BASE_IMAGE,
            "historical_implementation_record_sha256": IMPLEMENTATION_RECORD_SHA256,
            "source_binding_contract_sha256": SOURCE_BINDING_CONTRACT_SHA256,
            "historical_implementation_host_invocation_chain_authored": False,
            "source_binding_host_invocation_chain_authored": False,
            "source_binding_torch2pc_readonly_mount_required": True,
            "historical_records_rewritten": False,
            "container_runtime": CONTAINER_RUNTIME,
            "container_workdir": CONTAINER_WORKDIR,
            "container_image_entrypoint": CONTAINER_IMAGE_ENTRYPOINT,
            "container_runtime_entrypoint": CONTAINER_RUNTIME_ENTRYPOINT,
            "output_root": OUTPUT_ROOT,
            "lease_v1_relative": LEASE_V1_RELATIVE,
            "lease_v2_relative": LEASE_V2_RELATIVE,
            "durable_outcome_relative": DURABLE_OUTCOME_RELATIVE,
            "required_host_resource_inputs": REQUIRED_RESOURCE_KEYS,
            "fixed_environment": FIXED_ENVIRONMENT,
            "host_environment_bindings": HOST_ENVIRONMENT_BINDINGS,
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
            "lease_acknowledgement_required": True,
            "lease_acknowledgement": LEASE_ACKNOWLEDGEMENT,
            "host_command_constructor_authored": True,
            "host_command_materialized": False,
            "host_process_spawner_present": False,
            "docker_run_implemented": False,
            "runtime_execution_permitted": False,
            "authorization_used": False,
            "authorization_consumed": False,
            "attempt_started": False,
            "execution_lease_materialized": False,
            "durable_outcome_present": False,
            "runtime_execution_started": False,
            "runtime_execution_performed": False,
            "scientific_execution_open": False,
            "test_dataset_access": False,
            "publication_permitted": False,
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise QWakeAttempt003HostInvocationChainError(
                    f"host invocation contract differs: {field_name}"
                )
        if len(self.mounts) != 3:
            raise QWakeAttempt003HostInvocationChainError(
                "host invocation mount count differs"
            )
        for mount in self.mounts:
            mount.require()
        if tuple(mount.source_relative for mount in self.mounts) != (
            FROZEN_EXPERIMENTS_RELATIVE.as_posix(),
            TORCH2PC_RELATIVE.as_posix(),
            RESULTS_RELATIVE.as_posix(),
        ):
            raise QWakeAttempt003HostInvocationChainError(
                "host invocation mount order differs"
            )
        _require_sha256(self.contract_sha256, "contract_sha256")
        if self.contract_sha256 != sha256_object(self._payload_without_digest()):
            raise QWakeAttempt003HostInvocationChainError(
                "host invocation contract digest differs"
            )

    def _payload_without_digest(self) -> Mapping[str, object]:
        payload = asdict(self)
        payload.pop("contract_sha256")
        return cast(Mapping[str, object], payload)

    def canonical_json(self) -> str:
        return canonical_json(asdict(self))


@dataclass(frozen=True)
class LocalImageInspection:
    image_id: str
    repo_digests: tuple[str, ...]
    architecture: str
    os: str
    source_revision: str
    base_image: str
    source_environment_commit: str
    working_directory: str
    entrypoint: tuple[str, ...]
    inspection_sha256: str

    def require(self, contract: HostInvocationContract) -> None:
        expected: Mapping[str, object] = {
            "image_id": contract.image_digest,
            "architecture": "amd64",
            "os": "linux",
            "source_revision": contract.source_commit,
            "base_image": contract.base_image,
            "source_environment_commit": contract.source_commit,
            "working_directory": contract.container_workdir,
            "entrypoint": contract.container_image_entrypoint,
        }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise QWakeAttempt003HostInvocationChainError(
                    f"local image inspection differs: {field_name}"
                )
        if contract.image_repo_digest not in self.repo_digests:
            raise QWakeAttempt003HostInvocationChainError(
                "local image repository digest is absent"
            )
        _require_sha256(self.inspection_sha256, "inspection_sha256")
        if self.inspection_sha256 != sha256_object(self._payload_without_digest()):
            raise QWakeAttempt003HostInvocationChainError(
                "local image inspection digest differs"
            )

    def _payload_without_digest(self) -> Mapping[str, object]:
        payload = asdict(self)
        payload.pop("inspection_sha256")
        return cast(Mapping[str, object], payload)


@dataclass(frozen=True)
class MaterializedHostInvocation:
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
    authorization_consumed: bool
    attempt_started: bool
    execution_lease_created: bool
    runtime_execution_started: bool
    runtime_execution_performed: bool
    invocation_sha256: str

    def require(
        self,
        contract: HostInvocationContract,
        inspection: LocalImageInspection,
    ) -> None:
        exact: Mapping[str, object] = {
            "schema_version": 1,
            "contract_sha256": contract.contract_sha256,
            "image_inspection_sha256": inspection.inspection_sha256,
            "shell_interpretation_used": False,
            "environment_inherited": False,
            "subprocess_spawned": False,
            "container_created": False,
            "authorization_consumed": False,
            "attempt_started": False,
            "execution_lease_created": False,
            "runtime_execution_started": False,
            "runtime_execution_performed": False,
        }
        for field_name, expected_value in exact.items():
            if getattr(self, field_name) != expected_value:
                raise QWakeAttempt003HostInvocationChainError(
                    f"materialized host invocation differs: {field_name}"
                )
        _require_rfc3339_seconds(self.claimed_at_utc)
        if self.argv[:2] != ("docker", "run"):
            raise QWakeAttempt003HostInvocationChainError(
                "materialized host argv prefix differs"
            )
        if contract.image_repo_digest not in self.argv:
            raise QWakeAttempt003HostInvocationChainError(
                "materialized host image differs"
            )
        if any("/workspace/data" in item for item in self.argv):
            raise QWakeAttempt003HostInvocationChainError(
                "materialized host dataset mount is present"
            )
        _require_sha256(self.invocation_sha256, "invocation_sha256")
        if self.invocation_sha256 != sha256_object(self._payload_without_digest()):
            raise QWakeAttempt003HostInvocationChainError(
                "materialized host invocation digest differs"
            )

    def _payload_without_digest(self) -> Mapping[str, object]:
        payload = asdict(self)
        payload.pop("invocation_sha256")
        return cast(Mapping[str, object], payload)

    def canonical_json(self) -> str:
        return canonical_json(asdict(self))


def _mounts() -> tuple[HostMountContract, ...]:
    return (
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


def build_attempt_003_host_invocation_contract() -> HostInvocationContract:
    payload: dict[str, object] = {
        "schema_version": 1,
        "contract_id": HOST_INVOCATION_CONTRACT_ID,
        "status": HOST_INVOCATION_STATUS,
        "attempt_id": ATTEMPT_ID,
        "authorized_parent_head": AUTHORIZED_PARENT_HEAD,
        "freeze_sha256": FREEZE_SHA256,
        "authorization_id": AUTHORIZATION_ID,
        "authorization_sha256": AUTHORIZATION_SHA256,
        "authorization_action_phrase": AUTHORIZATION_ACTION_PHRASE,
        "authorization_required_before_invocation": True,
        "authorization_consumption_owner": "container_entrypoint_atomic_execution_lease",
        "execution_count": 1,
        "source_commit": SOURCE_COMMIT,
        "torch2pc_commit": TORCH2PC_COMMIT,
        "image_digest": IMAGE_DIGEST,
        "image_repo_digest": IMAGE_REPO_DIGEST,
        "base_image": BASE_IMAGE,
        "historical_implementation_record_sha256": IMPLEMENTATION_RECORD_SHA256,
        "source_binding_contract_sha256": SOURCE_BINDING_CONTRACT_SHA256,
        "historical_implementation_host_invocation_chain_authored": False,
        "source_binding_host_invocation_chain_authored": False,
        "source_binding_torch2pc_readonly_mount_required": True,
        "historical_records_rewritten": False,
        "container_runtime": CONTAINER_RUNTIME,
        "container_workdir": CONTAINER_WORKDIR,
        "container_image_entrypoint": CONTAINER_IMAGE_ENTRYPOINT,
        "container_runtime_entrypoint": CONTAINER_RUNTIME_ENTRYPOINT,
        "output_root": OUTPUT_ROOT,
        "lease_v1_relative": LEASE_V1_RELATIVE,
        "lease_v2_relative": LEASE_V2_RELATIVE,
        "durable_outcome_relative": DURABLE_OUTCOME_RELATIVE,
        "required_host_resource_inputs": REQUIRED_RESOURCE_KEYS,
        "fixed_environment": FIXED_ENVIRONMENT,
        "host_environment_bindings": HOST_ENVIRONMENT_BINDINGS,
        "mounts": tuple(asdict(mount) for mount in _mounts()),
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
        "lease_acknowledgement_required": True,
        "lease_acknowledgement": LEASE_ACKNOWLEDGEMENT,
        "host_command_constructor_authored": True,
        "host_command_materialized": False,
        "host_process_spawner_present": False,
        "docker_run_implemented": False,
        "runtime_execution_permitted": False,
        "authorization_used": False,
        "authorization_consumed": False,
        "attempt_started": False,
        "execution_lease_materialized": False,
        "durable_outcome_present": False,
        "runtime_execution_started": False,
        "runtime_execution_performed": False,
        "scientific_execution_open": False,
        "test_dataset_access": False,
        "publication_permitted": False,
    }
    values = dict(payload)
    values["mounts"] = _mounts()
    contract = HostInvocationContract(
        **cast(dict[str, Any], values),
        contract_sha256=sha256_object(payload),
    )
    contract.require()
    return contract


def load_attempt_003_host_invocation_contract(path: Path) -> HostInvocationContract:
    if not path.is_file() or path.is_symlink():
        raise QWakeAttempt003HostInvocationChainError(
            "regular host invocation contract is absent"
        )
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise QWakeAttempt003HostInvocationChainError(
            "invalid host invocation contract JSON"
        ) from exc
    if not isinstance(value, dict):
        raise QWakeAttempt003HostInvocationChainError(
            "host invocation contract root differs"
        )
    if path.read_bytes() != canonical_json(value).encode("utf-8"):
        raise QWakeAttempt003HostInvocationChainError(
            "host invocation contract serialization differs"
        )
    mounts_raw = value.get("mounts")
    if not isinstance(mounts_raw, list):
        raise QWakeAttempt003HostInvocationChainError("host mounts differ")
    mounts = tuple(
        HostMountContract(**cast(dict[str, str], item))
        for item in mounts_raw
        if isinstance(item, dict)
    )
    if len(mounts) != len(mounts_raw):
        raise QWakeAttempt003HostInvocationChainError("host mount record differs")
    values = dict(value)
    values["mounts"] = mounts
    for field_name in (
        "container_image_entrypoint",
        "required_host_resource_inputs",
    ):
        raw = values.get(field_name)
        if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
            raise QWakeAttempt003HostInvocationChainError(
                f"host invocation tuple field differs: {field_name}"
            )
        values[field_name] = tuple(raw)
    for field_name in (
        "fixed_environment",
        "host_environment_bindings",
        "device_bindings",
    ):
        raw = values.get(field_name)
        if not isinstance(raw, list):
            raise QWakeAttempt003HostInvocationChainError(
                f"host invocation nested tuple field differs: {field_name}"
            )
        normalized: list[tuple[str, ...]] = []
        for item in raw:
            if not isinstance(item, list) or not all(isinstance(value, str) for value in item):
                raise QWakeAttempt003HostInvocationChainError(
                    f"host invocation nested tuple item differs: {field_name}"
                )
            normalized.append(tuple(item))
        values[field_name] = tuple(normalized)
    contract = HostInvocationContract(**cast(dict[str, Any], values))
    contract.require()
    return contract


def parse_attempt_003_local_image_inspection(
    raw_json: str | bytes,
    contract: HostInvocationContract,
) -> LocalImageInspection:
    try:
        value = json.loads(raw_json)
    except (json.JSONDecodeError, UnicodeDecodeError, TypeError) as exc:
        raise QWakeAttempt003HostInvocationChainError(
            "local image inspection JSON is invalid"
        ) from exc
    if not isinstance(value, list) or len(value) != 1 or not isinstance(value[0], dict):
        raise QWakeAttempt003HostInvocationChainError(
            "local image inspection record count differs"
        )
    record = cast(dict[str, Any], value[0])
    config = record.get("Config")
    if not isinstance(config, dict):
        raise QWakeAttempt003HostInvocationChainError("image Config differs")
    labels = config.get("Labels")
    if not isinstance(labels, dict):
        raise QWakeAttempt003HostInvocationChainError("image Labels differ")
    environment: dict[str, str] = {}
    raw_env = config.get("Env")
    if not isinstance(raw_env, list) or not all(isinstance(item, str) for item in raw_env):
        raise QWakeAttempt003HostInvocationChainError("image Env differs")
    for item in raw_env:
        key, sep, item_value = item.partition("=")
        if not sep:
            raise QWakeAttempt003HostInvocationChainError("image Env entry differs")
        environment[key] = item_value
    repo_digests_raw = record.get("RepoDigests")
    entrypoint_raw = config.get("Entrypoint")
    if not isinstance(repo_digests_raw, list) or not all(
        isinstance(item, str) for item in repo_digests_raw
    ):
        raise QWakeAttempt003HostInvocationChainError("image RepoDigests differs")
    if not isinstance(entrypoint_raw, list) or not all(
        isinstance(item, str) for item in entrypoint_raw
    ):
        raise QWakeAttempt003HostInvocationChainError("image Entrypoint differs")
    payload: dict[str, object] = {
        "image_id": str(record.get("Id") or ""),
        "repo_digests": tuple(cast(list[str], repo_digests_raw)),
        "architecture": str(record.get("Architecture") or ""),
        "os": str(record.get("Os") or ""),
        "source_revision": str(labels.get("org.opencontainers.image.revision") or ""),
        "base_image": str(labels.get("io.torch2pc.base-image") or ""),
        "source_environment_commit": environment.get("SOURCE_GIT_COMMIT", ""),
        "working_directory": str(config.get("WorkingDir") or ""),
        "entrypoint": tuple(cast(list[str], entrypoint_raw)),
    }
    inspection = LocalImageInspection(
        **cast(dict[str, Any], payload),
        inspection_sha256=sha256_object(payload),
    )
    inspection.require(contract)
    return inspection


def _require_below_root(root: Path, candidate: Path) -> None:
    if candidate == root or root not in candidate.parents:
        raise QWakeAttempt003HostInvocationChainError(
            "host mount source escapes project root"
        )


def materialize_attempt_003_host_invocation(
    project_root: Path,
    contract: HostInvocationContract,
    inspection: LocalImageInspection,
    resources: HostInvocationResources,
    *,
    claimed_at_utc: str,
    lease_acknowledgement: str,
) -> MaterializedHostInvocation:
    """Construct exact future Docker argv without spawning a process."""

    root = project_root.expanduser().resolve()
    contract.require()
    inspection.require(contract)
    _require_rfc3339_seconds(claimed_at_utc)
    if lease_acknowledgement != contract.lease_acknowledgement:
        raise QWakeAttempt003HostInvocationChainError(
            "attempt-003 lease acknowledgement differs"
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
        if not source.is_dir():
            raise QWakeAttempt003HostInvocationChainError(
                f"host mount source directory is absent: {mount.source_relative}"
            )
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
        "authorization_consumed": False,
        "attempt_started": False,
        "execution_lease_created": False,
        "runtime_execution_started": False,
        "runtime_execution_performed": False,
    }
    materialized = MaterializedHostInvocation(
        **cast(dict[str, Any], payload),
        invocation_sha256=sha256_object(payload),
    )
    materialized.require(contract, inspection)
    return materialized
