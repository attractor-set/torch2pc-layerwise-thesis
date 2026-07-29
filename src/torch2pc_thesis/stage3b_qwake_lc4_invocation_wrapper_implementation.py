"""Fail-closed implementation of QW-LC4-E host invocation materialization.

The module performs one observational Docker operation: ``docker image
inspect`` against the exact immutable repo digest.  It then constructs an
in-memory ``docker run`` argv tuple.  It never executes that tuple, creates an
execution lease, starts the tensor runtime, writes results, consumes the
one-shot authorization, or publishes evidence.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Any, Final, cast

from torch2pc_thesis.stage3b_qwake_lc4_invocation_authorization import (
    IMAGE_DIGEST,
    IMAGE_REPO_DIGEST,
    IMAGE_TAG,
)
from torch2pc_thesis.stage3b_qwake_lc4_invocation_wrapper import (
    CONTAINER_RUNTIME,
    IMAGE_SOURCE_COMMIT,
    InvocationMountContract,
    OneShotInvocationWrapperContract,
    build_one_shot_invocation_wrapper_contract,
    canonical_json,
    sha256_object,
)

INVOCATION_WRAPPER_IMPLEMENTATION_ID: Final = (
    "stage3b-qwake-lc4-e-one-shot-host-invocation-wrapper-implementation-v1"
)
INVOCATION_WRAPPER_IMPLEMENTATION_STATUS: Final = (
    "image_inspection_and_command_materialization_implemented_runtime_closed"
)
IMPLEMENTATION_BASE_COMMIT: Final = (
    "7cc17c6b36cb5115e63a2b64e4bff90a525b2465"
)
FROZEN_IMAGE_INSPECTION_RELATIVE: Final = Path(
    "experiments/frozen/stage3b-qwake-lc4-e-execution-freeze-v1/"
    "image-inspection.json"
)
FROZEN_IMAGE_INSPECTION_SHA256: Final = (
    "sha256:d771d93b4b3c38599fee9fbf90971bc8d00d9cd7da4cbe90cef67c84d761d675"
)
OCI_REVISION_LABEL: Final = "org.opencontainers.image.revision"
OCI_BASE_IMAGE_LABEL: Final = "io.torch2pc.base-image"
IMAGE_INSPECTION_TIMEOUT_SECONDS: Final = 30.0
FIXTURE_CLAIMED_AT_UTC: Final = "2026-07-29T03:36:18Z"

_CANONICAL_RESOURCE_KEYS: Final = (
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
_SIZE_PATTERN: Final = re.compile(r"[1-9][0-9]*(?:[kmgt]b?)?")
_DECIMAL_PATTERN: Final = re.compile(r"0|[1-9][0-9]*")
_RFC3339_SECONDS_PATTERN: Final = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z"
)

__all__ = [
    "FIXTURE_CLAIMED_AT_UTC",
    "FROZEN_IMAGE_INSPECTION_RELATIVE",
    "FROZEN_IMAGE_INSPECTION_SHA256",
    "IMPLEMENTATION_BASE_COMMIT",
    "IMAGE_INSPECTION_TIMEOUT_SECONDS",
    "INVOCATION_WRAPPER_IMPLEMENTATION_ID",
    "INVOCATION_WRAPPER_IMPLEMENTATION_STATUS",
    "FrozenImageIdentity",
    "HostInvocationResources",
    "LocalImageInspection",
    "MaterializedOneShotInvocation",
    "QWakeLC4InvocationImplementationError",
    "inspect_local_immutable_image",
    "load_frozen_image_identity",
    "load_host_invocation_resources",
    "materialize_one_shot_invocation",
    "parse_local_image_inspection",
    "validate_materialized_one_shot_invocation",
]


class QWakeLC4InvocationImplementationError(RuntimeError):
    """Raised when image inspection or command materialization fails closed."""


@dataclass(frozen=True)
class FrozenImageIdentity:
    """Normalized immutable image identity frozen before authorization."""

    schema_version: int
    image_tag: str
    image_digest: str
    image_repo_digest: str
    image_id: str
    repo_digests_observed: tuple[str, ...]
    architecture: str
    operating_system: str
    created: str
    size_bytes: int
    rootfs_layers: tuple[str, ...]
    oci_revision: str
    oci_base_image: str
    source_git_commit_env: str
    record_sha256: str

    def require(self) -> None:
        exact: Mapping[str, object] = {
            "schema_version": 1,
            "image_tag": IMAGE_TAG,
            "image_digest": IMAGE_DIGEST,
            "image_repo_digest": IMAGE_REPO_DIGEST,
            "image_id": IMAGE_DIGEST,
            "architecture": "amd64",
            "operating_system": "linux",
            "oci_revision": IMAGE_SOURCE_COMMIT,
            "source_git_commit_env": IMAGE_SOURCE_COMMIT,
            "record_sha256": FROZEN_IMAGE_INSPECTION_SHA256,
        }
        for field_name, expected in exact.items():
            if getattr(self, field_name) != expected:
                raise QWakeLC4InvocationImplementationError(
                    f"frozen image identity differs: {field_name}"
                )
        if IMAGE_REPO_DIGEST not in self.repo_digests_observed:
            raise QWakeLC4InvocationImplementationError(
                "frozen image repo digest is absent"
            )
        if self.size_bytes <= 0:
            raise QWakeLC4InvocationImplementationError(
                "frozen image size is not positive"
            )
        if not self.rootfs_layers:
            raise QWakeLC4InvocationImplementationError(
                "frozen image rootfs layers are absent"
            )
        for value, field_name in (
            (self.image_digest, "image_digest"),
            (self.image_id, "image_id"),
            (self.record_sha256, "record_sha256"),
        ):
            _require_sha256(value, field_name)
        for layer in self.rootfs_layers:
            _require_sha256(layer, "rootfs layer")


@dataclass(frozen=True)
class LocalImageInspection:
    """Current local Docker image identity after exact inspection."""

    schema_version: int
    image_reference: str
    image_id: str
    repo_digests: tuple[str, ...]
    repo_tags: tuple[str, ...]
    architecture: str
    operating_system: str
    created: str
    size_bytes: int
    rootfs_layers: tuple[str, ...]
    oci_revision: str
    oci_base_image: str
    source_git_commit_env: str
    image_entrypoint: tuple[str, ...]
    working_dir: str
    inspection_sha256: str

    def require(
        self,
        contract: OneShotInvocationWrapperContract,
        frozen: FrozenImageIdentity,
    ) -> None:
        exact: Mapping[str, object] = {
            "schema_version": 1,
            "image_reference": contract.image_repo_digest,
            "image_id": frozen.image_id,
            "architecture": frozen.architecture,
            "operating_system": frozen.operating_system,
            "created": frozen.created,
            "size_bytes": frozen.size_bytes,
            "rootfs_layers": frozen.rootfs_layers,
            "oci_revision": frozen.oci_revision,
            "oci_base_image": frozen.oci_base_image,
            "source_git_commit_env": frozen.source_git_commit_env,
            "image_entrypoint": contract.container_image_entrypoint,
            "working_dir": contract.container_workdir,
        }
        for field_name, expected in exact.items():
            if getattr(self, field_name) != expected:
                raise QWakeLC4InvocationImplementationError(
                    f"local image inspection differs: {field_name}"
                )
        if self.repo_digests != frozen.repo_digests_observed:
            raise QWakeLC4InvocationImplementationError(
                "local image repo digests differ"
            )
        if contract.image_repo_digest not in self.repo_digests:
            raise QWakeLC4InvocationImplementationError(
                "exact local image repo digest is absent"
            )
        if contract.image_tag not in self.repo_tags:
            raise QWakeLC4InvocationImplementationError(
                "exact local image tag is absent"
            )
        if self.inspection_sha256 != sha256_object(
            self._payload_without_digest()
        ):
            raise QWakeLC4InvocationImplementationError(
                "local image inspection digest differs"
            )

    def _payload_without_digest(self) -> Mapping[str, object]:
        payload = asdict(self)
        payload.pop("inspection_sha256")
        return cast(Mapping[str, object], payload)


@dataclass(frozen=True)
class HostInvocationResources:
    """Canonical host inputs used only to construct a future command."""

    host_uid: str
    host_gid: str
    video_gid: str
    render_gid: str
    hip_visible_devices: str
    cpuset_gpu: str
    mem_limit: str
    shm_size: str
    tmpfs_size: str
    omp_num_threads: str
    mkl_num_threads: str
    openblas_num_threads: str
    numexpr_num_threads: str

    def require(self) -> None:
        for value, field_name in (
            (self.host_uid, "HOST_UID"),
            (self.host_gid, "HOST_GID"),
            (self.video_gid, "VIDEO_GID"),
            (self.render_gid, "RENDER_GID"),
        ):
            _require_canonical_nonnegative_decimal(value, field_name)
        if self.video_gid == self.render_gid:
            raise QWakeLC4InvocationImplementationError(
                "VIDEO_GID and RENDER_GID must differ"
            )
        if self.hip_visible_devices != _canonical_device_list(
            self.hip_visible_devices
        ):
            raise QWakeLC4InvocationImplementationError(
                "HIP_VISIBLE_DEVICES is not canonical"
            )
        if self.cpuset_gpu != _canonical_cpuset(self.cpuset_gpu):
            raise QWakeLC4InvocationImplementationError(
                "CPUSET_GPU is not canonical"
            )
        for value, field_name in (
            (self.mem_limit, "MEM_LIMIT"),
            (self.shm_size, "SHM_SIZE"),
            (self.tmpfs_size, "TMPFS_SIZE"),
        ):
            if _SIZE_PATTERN.fullmatch(value) is None:
                raise QWakeLC4InvocationImplementationError(
                    f"{field_name} is not a canonical Docker size"
                )
        for value, field_name in (
            (self.omp_num_threads, "OMP_NUM_THREADS"),
            (self.mkl_num_threads, "MKL_NUM_THREADS"),
            (self.openblas_num_threads, "OPENBLAS_NUM_THREADS"),
            (self.numexpr_num_threads, "NUMEXPR_NUM_THREADS"),
        ):
            _require_positive_thread_count(value, field_name)

    def host_mapping(self) -> Mapping[str, str]:
        return {
            "HOST_UID": self.host_uid,
            "HOST_GID": self.host_gid,
            "VIDEO_GID": self.video_gid,
            "RENDER_GID": self.render_gid,
            "HIP_VISIBLE_DEVICES": self.hip_visible_devices,
            "CPUSET_GPU": self.cpuset_gpu,
            "MEM_LIMIT": self.mem_limit,
            "SHM_SIZE": self.shm_size,
            "TMPFS_SIZE": self.tmpfs_size,
            "OMP_NUM_THREADS": self.omp_num_threads,
            "MKL_NUM_THREADS": self.mkl_num_threads,
            "OPENBLAS_NUM_THREADS": self.openblas_num_threads,
            "NUMEXPR_NUM_THREADS": self.numexpr_num_threads,
        }


@dataclass(frozen=True)
class MaterializedOneShotInvocation:
    """Deterministic in-memory argv specification that is never executed here."""

    schema_version: int
    implementation_id: str
    status: str
    implementation_base_commit: str
    wrapper_contract_id: str
    wrapper_contract_sha256: str
    image_inspection_sha256: str
    image_reference: str
    project_root: str
    claimed_at_utc: str
    resources: HostInvocationResources
    environment: tuple[tuple[str, str], ...]
    mounts: tuple[tuple[str, str, str], ...]
    argv: tuple[str, ...]
    image_inspection_implemented: bool
    invocation_command_materialized: bool
    invocation_command_persisted: bool
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
    command_sha256: str

    def require(self) -> None:
        exact: Mapping[str, object] = {
            "schema_version": 1,
            "implementation_id": INVOCATION_WRAPPER_IMPLEMENTATION_ID,
            "status": INVOCATION_WRAPPER_IMPLEMENTATION_STATUS,
            "implementation_base_commit": IMPLEMENTATION_BASE_COMMIT,
            "image_reference": IMAGE_REPO_DIGEST,
            "image_inspection_implemented": True,
            "invocation_command_materialized": True,
            "invocation_command_persisted": False,
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
                raise QWakeLC4InvocationImplementationError(
                    f"materialized invocation differs: {field_name}"
                )
        self.resources.require()
        _require_rfc3339_seconds(self.claimed_at_utc)
        _require_sha256(self.wrapper_contract_sha256, "wrapper_contract_sha256")
        _require_sha256(self.image_inspection_sha256, "image_inspection_sha256")
        _require_sha256(self.command_sha256, "command_sha256")
        if not self.project_root.startswith("/"):
            raise QWakeLC4InvocationImplementationError(
                "materialized project root is not absolute"
            )
        if not self.argv or self.argv[:2] != (CONTAINER_RUNTIME, "run"):
            raise QWakeLC4InvocationImplementationError(
                "materialized invocation argv prefix differs"
            )
        if self.argv.count(IMAGE_REPO_DIGEST) != 1:
            raise QWakeLC4InvocationImplementationError(
                "materialized invocation image reference differs"
            )
        if self.command_sha256 != sha256_object(self._payload_without_digest()):
            raise QWakeLC4InvocationImplementationError(
                "materialized invocation digest differs"
            )

    def _payload_without_digest(self) -> Mapping[str, object]:
        payload = asdict(self)
        payload.pop("command_sha256")
        return cast(Mapping[str, object], payload)

    def canonical_json(self) -> str:
        return canonical_json(asdict(self))


def load_frozen_image_identity(project_root: Path) -> FrozenImageIdentity:
    """Load and validate the exact normalized image identity from the freeze."""

    root = project_root.expanduser().resolve()
    path = root / FROZEN_IMAGE_INSPECTION_RELATIVE
    if not path.is_file() or path.is_symlink():
        raise QWakeLC4InvocationImplementationError(
            "frozen image inspection record is absent or non-regular"
        )
    observed_sha256 = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    if observed_sha256 != FROZEN_IMAGE_INSPECTION_SHA256:
        raise QWakeLC4InvocationImplementationError(
            "frozen image inspection file digest differs"
        )
    try:
        raw: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise QWakeLC4InvocationImplementationError(
            "frozen image inspection record cannot be decoded"
        ) from exc
    data = _as_mapping(raw, "frozen image inspection")
    frozen = FrozenImageIdentity(
        schema_version=_as_int(data.get("schema_version"), "schema_version"),
        image_tag=_as_str(data.get("image_tag"), "image_tag"),
        image_digest=_as_str(data.get("image_digest"), "image_digest"),
        image_repo_digest=_as_str(
            data.get("image_repo_digest"), "image_repo_digest"
        ),
        image_id=_as_str(data.get("image_id"), "image_id"),
        repo_digests_observed=_as_string_tuple(
            data.get("repo_digests_observed"), "repo_digests_observed"
        ),
        architecture=_as_str(data.get("architecture"), "architecture"),
        operating_system=_as_str(data.get("os"), "os"),
        created=_as_str(data.get("created"), "created"),
        size_bytes=_as_int(data.get("size_bytes"), "size_bytes"),
        rootfs_layers=_as_string_tuple(
            data.get("rootfs_layers"), "rootfs_layers"
        ),
        oci_revision=_as_str(data.get("oci_revision"), "oci_revision"),
        oci_base_image=_as_str(
            data.get("oci_base_image"), "oci_base_image"
        ),
        source_git_commit_env=_as_str(
            data.get("source_git_commit_env"), "source_git_commit_env"
        ),
        record_sha256=observed_sha256,
    )
    frozen.require()
    return frozen


def parse_local_image_inspection(
    raw_json: str,
    contract: OneShotInvocationWrapperContract,
    frozen: FrozenImageIdentity,
) -> LocalImageInspection:
    """Normalize one Docker inspect response and verify exact image identity."""

    try:
        decoded: Any = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise QWakeLC4InvocationImplementationError(
            "Docker image inspection output is not JSON"
        ) from exc
    records = _as_sequence(decoded, "Docker image inspection")
    if len(records) != 1:
        raise QWakeLC4InvocationImplementationError(
            "Docker image inspection did not return exactly one record"
        )
    record = _as_mapping(records[0], "Docker image record")
    config = _as_mapping(record.get("Config"), "Docker image Config")
    labels = _as_string_mapping(config.get("Labels"), "Docker image Labels")
    environment = _parse_image_environment(
        _as_string_tuple(config.get("Env"), "Docker image Env")
    )
    rootfs = _as_mapping(record.get("RootFS"), "Docker image RootFS")
    inspection = LocalImageInspection(
        schema_version=1,
        image_reference=contract.image_repo_digest,
        image_id=_as_str(record.get("Id"), "Docker image Id"),
        repo_digests=tuple(
            sorted(
                _as_string_tuple(
                    record.get("RepoDigests"), "Docker image RepoDigests"
                )
            )
        ),
        repo_tags=tuple(
            sorted(
                _as_string_tuple(
                    record.get("RepoTags"), "Docker image RepoTags"
                )
            )
        ),
        architecture=_as_str(
            record.get("Architecture"), "Docker image Architecture"
        ),
        operating_system=_as_str(record.get("Os"), "Docker image Os"),
        created=_as_str(record.get("Created"), "Docker image Created"),
        size_bytes=_as_int(record.get("Size"), "Docker image Size"),
        rootfs_layers=_as_string_tuple(
            rootfs.get("Layers"), "Docker image RootFS.Layers"
        ),
        oci_revision=labels.get(OCI_REVISION_LABEL, ""),
        oci_base_image=labels.get(OCI_BASE_IMAGE_LABEL, ""),
        source_git_commit_env=environment.get("SOURCE_GIT_COMMIT", ""),
        image_entrypoint=_as_string_tuple(
            config.get("Entrypoint"), "Docker image Config.Entrypoint"
        ),
        working_dir=_as_str(
            config.get("WorkingDir"), "Docker image Config.WorkingDir"
        ),
        inspection_sha256="sha256:" + "0" * 64,
    )
    inspection = replace(
        inspection,
        inspection_sha256=sha256_object(inspection._payload_without_digest()),
    )
    inspection.require(contract, frozen)
    return inspection


def inspect_local_immutable_image(
    project_root: Path,
    *,
    timeout_seconds: float = IMAGE_INSPECTION_TIMEOUT_SECONDS,
) -> LocalImageInspection:
    """Inspect only the exact local image; no image pull or container run occurs."""

    if timeout_seconds <= 0:
        raise QWakeLC4InvocationImplementationError(
            "image inspection timeout is not positive"
        )
    root = project_root.expanduser().resolve()
    contract = build_one_shot_invocation_wrapper_contract(root)
    frozen = load_frozen_image_identity(root)
    inspection_argv = (
        contract.container_runtime,
        "image",
        "inspect",
        contract.image_repo_digest,
    )
    environment = os.environ.copy()
    environment["LC_ALL"] = "C"
    environment["LANG"] = "C"
    try:
        completed = subprocess.run(
            inspection_argv,
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            env=environment,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise QWakeLC4InvocationImplementationError(
            "local Docker image inspection could not be completed"
        ) from exc
    if completed.returncode != 0:
        raise QWakeLC4InvocationImplementationError(
            "local Docker image inspection returned a non-zero status"
        )
    if not completed.stdout.strip():
        raise QWakeLC4InvocationImplementationError(
            "local Docker image inspection returned no output"
        )
    return parse_local_image_inspection(completed.stdout, contract, frozen)


def load_host_invocation_resources(
    values: Mapping[str, str],
) -> HostInvocationResources:
    """Validate an exact resource mapping without reading the process env."""

    observed_keys = set(values)
    expected_keys = set(_CANONICAL_RESOURCE_KEYS)
    if observed_keys != expected_keys:
        missing = sorted(expected_keys - observed_keys)
        extra = sorted(observed_keys - expected_keys)
        raise QWakeLC4InvocationImplementationError(
            "host resource key set differs: "
            f"missing={missing}, extra={extra}"
        )
    stripped = {key: values[key].strip() for key in _CANONICAL_RESOURCE_KEYS}
    if any(stripped[key] != values[key] for key in _CANONICAL_RESOURCE_KEYS):
        raise QWakeLC4InvocationImplementationError(
            "host resource values contain surrounding whitespace"
        )
    resources = HostInvocationResources(
        host_uid=stripped["HOST_UID"],
        host_gid=stripped["HOST_GID"],
        video_gid=stripped["VIDEO_GID"],
        render_gid=stripped["RENDER_GID"],
        hip_visible_devices=stripped["HIP_VISIBLE_DEVICES"],
        cpuset_gpu=stripped["CPUSET_GPU"],
        mem_limit=stripped["MEM_LIMIT"],
        shm_size=stripped["SHM_SIZE"],
        tmpfs_size=stripped["TMPFS_SIZE"],
        omp_num_threads=stripped["OMP_NUM_THREADS"],
        mkl_num_threads=stripped["MKL_NUM_THREADS"],
        openblas_num_threads=stripped["OPENBLAS_NUM_THREADS"],
        numexpr_num_threads=stripped["NUMEXPR_NUM_THREADS"],
    )
    resources.require()
    return resources


def materialize_one_shot_invocation(
    project_root: Path,
    *,
    image_inspection: LocalImageInspection,
    host_resources: Mapping[str, str],
    claimed_at_utc: str,
    operator_acknowledgement: str,
) -> MaterializedOneShotInvocation:
    """Build deterministic ``docker run`` argv as data and never execute it."""

    root = project_root.expanduser().resolve()
    contract = build_one_shot_invocation_wrapper_contract(root)
    frozen = load_frozen_image_identity(root)
    image_inspection.require(contract, frozen)
    if operator_acknowledgement != contract.invocation_operator_acknowledgement:
        raise QWakeLC4InvocationImplementationError(
            "invocation operator acknowledgement differs"
        )
    _require_rfc3339_seconds(claimed_at_utc)
    resources = load_host_invocation_resources(host_resources)
    environment = _materialized_environment(contract, resources)
    mounts = _materialized_mounts(root, contract.mounts)
    argv = _materialized_argv(
        contract,
        resources,
        claimed_at_utc=claimed_at_utc,
        environment=environment,
        mounts=mounts,
    )
    materialized = MaterializedOneShotInvocation(
        schema_version=1,
        implementation_id=INVOCATION_WRAPPER_IMPLEMENTATION_ID,
        status=INVOCATION_WRAPPER_IMPLEMENTATION_STATUS,
        implementation_base_commit=IMPLEMENTATION_BASE_COMMIT,
        wrapper_contract_id=contract.contract_id,
        wrapper_contract_sha256=contract.contract_sha256,
        image_inspection_sha256=image_inspection.inspection_sha256,
        image_reference=contract.image_repo_digest,
        project_root=root.as_posix(),
        claimed_at_utc=claimed_at_utc,
        resources=resources,
        environment=environment,
        mounts=mounts,
        argv=argv,
        image_inspection_implemented=True,
        invocation_command_materialized=True,
        invocation_command_persisted=False,
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
        command_sha256="sha256:" + "0" * 64,
    )
    materialized = replace(
        materialized,
        command_sha256=sha256_object(materialized._payload_without_digest()),
    )
    materialized.require()
    return materialized


def validate_materialized_one_shot_invocation(
    materialized: MaterializedOneShotInvocation,
    project_root: Path,
    *,
    image_inspection: LocalImageInspection,
    host_resources: Mapping[str, str],
    claimed_at_utc: str,
    operator_acknowledgement: str,
) -> None:
    """Rebuild a command specification and require byte-for-byte equality."""

    materialized.require()
    expected = materialize_one_shot_invocation(
        project_root,
        image_inspection=image_inspection,
        host_resources=host_resources,
        claimed_at_utc=claimed_at_utc,
        operator_acknowledgement=operator_acknowledgement,
    )
    if materialized != expected:
        raise QWakeLC4InvocationImplementationError(
            "materialized invocation differs from deterministic reconstruction"
        )


def _materialized_environment(
    contract: OneShotInvocationWrapperContract,
    resources: HostInvocationResources,
) -> tuple[tuple[str, str], ...]:
    resource_mapping = resources.host_mapping()
    environment = list(contract.fixed_environment)
    for container_key, host_key in contract.host_environment_bindings:
        environment.append((container_key, resource_mapping[host_key]))
    keys = tuple(key for key, _ in environment)
    if len(keys) != len(set(keys)):
        raise QWakeLC4InvocationImplementationError(
            "materialized environment contains duplicate keys"
        )
    return tuple(environment)


def _materialized_mounts(
    root: Path,
    mounts: tuple[InvocationMountContract, ...],
) -> tuple[tuple[str, str, str], ...]:
    materialized: list[tuple[str, str, str]] = []
    for mount in mounts:
        source = root / mount.source_relative
        if not source.is_dir() or source.is_symlink():
            raise QWakeLC4InvocationImplementationError(
                f"invocation mount source is absent or non-regular: {source}"
            )
        resolved = source.resolve(strict=True)
        if resolved != source.absolute():
            raise QWakeLC4InvocationImplementationError(
                f"invocation mount source traverses a symlink: {source}"
            )
        _require_below_root(root, resolved)
        _require_mount_safe_path(resolved.as_posix(), "mount source")
        _require_mount_safe_path(mount.target, "mount target")
        materialized.append(
            (resolved.as_posix(), mount.target, mount.access)
        )
    return tuple(materialized)


def _materialized_argv(
    contract: OneShotInvocationWrapperContract,
    resources: HostInvocationResources,
    *,
    claimed_at_utc: str,
    environment: tuple[tuple[str, str], ...],
    mounts: tuple[tuple[str, str, str], ...],
) -> tuple[str, ...]:
    tmpfs_options = tuple(
        option.replace("${TMPFS_SIZE}", resources.tmpfs_size)
        for option in contract.tmpfs_options
    )
    command = tuple(
        item.replace("{CLAIMED_AT_UTC}", claimed_at_utc)
        for item in contract.container_command_template
    )
    if any("{" in item or "}" in item or "${" in item for item in command):
        raise QWakeLC4InvocationImplementationError(
            "container command contains an unresolved placeholder"
        )
    argv: list[str] = [
        contract.container_runtime,
        "run",
        "--pull=never",
        "--rm",
        "--init",
        "--network",
        "none",
        "--read-only",
        "--security-opt",
        "no-new-privileges=true",
        "--cap-drop",
        "ALL",
        "--user",
        f"{resources.host_uid}:{resources.host_gid}",
        "--group-add",
        resources.video_gid,
        "--group-add",
        resources.render_gid,
    ]
    for source, target, permissions in contract.device_bindings:
        argv.extend(["--device", f"{source}:{target}:{permissions}"])
    argv.extend(
        [
            "--cpuset-cpus",
            resources.cpuset_gpu,
            "--memory",
            resources.mem_limit,
            "--shm-size",
            resources.shm_size,
            "--tmpfs",
            f"{contract.tmpfs_target}:{','.join(tmpfs_options)}",
            "--workdir",
            contract.container_workdir,
        ]
    )
    for key, value in environment:
        argv.extend(["--env", f"{key}={value}"])
    for source, target, access in mounts:
        specification = f"type=bind,source={source},target={target}"
        if access == "read_only":
            specification += ",readonly"
        elif access != "read_write":
            raise QWakeLC4InvocationImplementationError(
                "materialized mount access differs"
            )
        argv.extend(["--mount", specification])
    argv.append(contract.image_repo_digest)
    argv.extend(command)
    result = tuple(argv)
    _require_argv_safety(result, contract, command)
    return result


def _require_argv_safety(
    argv: tuple[str, ...],
    contract: OneShotInvocationWrapperContract,
    command: tuple[str, ...],
) -> None:
    required_tokens = (
        "--pull=never",
        "--rm",
        "--init",
        "--network",
        "none",
        "--read-only",
        "--security-opt",
        "no-new-privileges=true",
        "--cap-drop",
        "ALL",
    )
    for token in required_tokens:
        if token not in argv:
            raise QWakeLC4InvocationImplementationError(
                f"materialized invocation lacks required token: {token}"
            )
    forbidden_tokens = (
        "--privileged",
        "--network=host",
        "--pid=host",
        "--ipc=host",
        "--volume",
        "-v",
    )
    if any(token in argv for token in forbidden_tokens):
        raise QWakeLC4InvocationImplementationError(
            "materialized invocation contains a forbidden option"
        )
    if argv.count("--mount") != len(contract.mounts):
        raise QWakeLC4InvocationImplementationError(
            "materialized invocation mount count differs"
        )
    if argv.count("--device") != len(contract.device_bindings):
        raise QWakeLC4InvocationImplementationError(
            "materialized invocation device count differs"
        )
    image_index = argv.index(contract.image_repo_digest)
    if argv[image_index + 1 :] != command:
        raise QWakeLC4InvocationImplementationError(
            "materialized invocation command tail differs"
        )


def _parse_image_environment(values: tuple[str, ...]) -> Mapping[str, str]:
    parsed: dict[str, str] = {}
    for item in values:
        if "=" not in item:
            raise QWakeLC4InvocationImplementationError(
                "Docker image environment item lacks '='"
            )
        key, value = item.split("=", 1)
        if not key or key in parsed:
            raise QWakeLC4InvocationImplementationError(
                "Docker image environment contains an invalid key"
            )
        parsed[key] = value
    return parsed


def _canonical_device_list(value: str) -> str:
    if not value:
        raise QWakeLC4InvocationImplementationError(
            "HIP_VISIBLE_DEVICES is empty"
        )
    parts = value.split(",")
    devices: list[int] = []
    for part in parts:
        _require_canonical_nonnegative_decimal(part, "HIP_VISIBLE_DEVICES item")
        devices.append(int(part))
    if devices != sorted(set(devices)):
        raise QWakeLC4InvocationImplementationError(
            "HIP_VISIBLE_DEVICES contains duplicates or is not sorted"
        )
    return ",".join(str(item) for item in devices)


def _canonical_cpuset(value: str) -> str:
    if not value:
        raise QWakeLC4InvocationImplementationError("CPUSET_GPU is empty")
    cpus: set[int] = set()
    for part in value.split(","):
        if "-" in part:
            bounds = part.split("-")
            if len(bounds) != 2:
                raise QWakeLC4InvocationImplementationError(
                    "CPUSET_GPU range is malformed"
                )
            start_text, end_text = bounds
            _require_canonical_nonnegative_decimal(start_text, "CPUSET_GPU start")
            _require_canonical_nonnegative_decimal(end_text, "CPUSET_GPU end")
            start = int(start_text)
            end = int(end_text)
            if start >= end:
                raise QWakeLC4InvocationImplementationError(
                    "CPUSET_GPU range is not increasing"
                )
            expanded = set(range(start, end + 1))
        else:
            _require_canonical_nonnegative_decimal(part, "CPUSET_GPU item")
            expanded = {int(part)}
        if cpus & expanded:
            raise QWakeLC4InvocationImplementationError(
                "CPUSET_GPU contains overlapping entries"
            )
        cpus.update(expanded)
    ordered = sorted(cpus)
    ranges: list[str] = []
    start = ordered[0]
    previous = ordered[0]
    for current in ordered[1:]:
        if current == previous + 1:
            previous = current
            continue
        ranges.append(str(start) if start == previous else f"{start}-{previous}")
        start = current
        previous = current
    ranges.append(str(start) if start == previous else f"{start}-{previous}")
    return ",".join(ranges)


def _require_canonical_nonnegative_decimal(value: str, field_name: str) -> None:
    if _DECIMAL_PATTERN.fullmatch(value) is None:
        raise QWakeLC4InvocationImplementationError(
            f"{field_name} is not a canonical non-negative decimal"
        )
    if int(value) > 2_147_483_647:
        raise QWakeLC4InvocationImplementationError(
            f"{field_name} exceeds the supported range"
        )


def _require_positive_thread_count(value: str, field_name: str) -> None:
    _require_canonical_nonnegative_decimal(value, field_name)
    if not 1 <= int(value) <= 1024:
        raise QWakeLC4InvocationImplementationError(
            f"{field_name} is outside 1..1024"
        )


def _require_rfc3339_seconds(value: str) -> None:
    if _RFC3339_SECONDS_PATTERN.fullmatch(value) is None:
        raise QWakeLC4InvocationImplementationError(
            "claimed_at_utc is not canonical RFC3339 UTC seconds"
        )
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise QWakeLC4InvocationImplementationError(
            "claimed_at_utc is not a valid UTC timestamp"
        ) from exc


def _require_mount_safe_path(value: str, field_name: str) -> None:
    if any(character in value for character in (",", "\n", "\r", "\x00")):
        raise QWakeLC4InvocationImplementationError(
            f"{field_name} cannot be represented safely by --mount"
        )


def _require_below_root(root: Path, path: Path) -> None:
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise QWakeLC4InvocationImplementationError(
            f"invocation path escapes project root: {path}"
        ) from exc


def _require_sha256(value: str, field_name: str) -> None:
    if not value.startswith("sha256:") or len(value) != 71:
        raise QWakeLC4InvocationImplementationError(
            f"{field_name} is not a SHA-256 identity"
        )
    digest = value.removeprefix("sha256:")
    if any(character not in "0123456789abcdef" for character in digest):
        raise QWakeLC4InvocationImplementationError(
            f"{field_name} is not a SHA-256 identity"
        )


def _as_mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise QWakeLC4InvocationImplementationError(
            f"{field_name} is not an object"
        )
    return cast(Mapping[str, object], value)


def _as_string_mapping(value: object, field_name: str) -> Mapping[str, str]:
    mapping = _as_mapping(value, field_name)
    result: dict[str, str] = {}
    for key, item in mapping.items():
        if not isinstance(key, str) or not isinstance(item, str):
            raise QWakeLC4InvocationImplementationError(
                f"{field_name} is not a string mapping"
            )
        result[key] = item
    return result


def _as_sequence(value: object, field_name: str) -> Sequence[object]:
    if not isinstance(value, list):
        raise QWakeLC4InvocationImplementationError(
            f"{field_name} is not an array"
        )
    return cast(Sequence[object], value)


def _as_string_tuple(value: object, field_name: str) -> tuple[str, ...]:
    return tuple(
        _as_str(item, f"{field_name} item")
        for item in _as_sequence(value, field_name)
    )


def _as_str(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise QWakeLC4InvocationImplementationError(
            f"{field_name} is not a string"
        )
    return value


def _as_int(value: object, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise QWakeLC4InvocationImplementationError(
            f"{field_name} is not an integer"
        )
    return value
