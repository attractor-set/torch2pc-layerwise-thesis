#!/usr/bin/env python3
"""Materialize and execute exactly one QWake Attempt-005 engineering run.

This host-side operation is intentionally self-contained and fail-closed:
1. verify a clean canonical source commit and unchanged scientific inputs;
2. build and inspect one immutable image;
3. materialize a new Attempt-005 execution freeze;
4. materialize a distinct unconsumed one-shot authorization;
5. persist the exact Docker command before spawning;
6. invoke exactly one child process with no shell and no automatic retry;
7. persist a durable host outcome whether the child succeeds or fails.

The runtime authorization is consumed only inside the container when the
Attempt-005 execution lease is atomically materialized. The host never writes
that lease. Scientific execution, test-dataset access and publication remain
closed.
"""

from __future__ import annotations

import argparse
import grp
import hashlib
import json
import os
import pwd
import re
import shutil
import signal
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Final, cast

from torch2pc_thesis.stage3b_qwake_attempt_005_contract import (
    ATTEMPT_005_AUTHORIZATION_ID,
    ATTEMPT_005_AUTHORIZATION_ROOT,
    ATTEMPT_005_AUTHORIZATION_STATUS,
    ATTEMPT_005_BACKEND_RELATIVE,
    ATTEMPT_005_CONTRACT_RELATIVE,
    ATTEMPT_005_DURABLE_OUTCOME_RELATIVE,
    ATTEMPT_005_ENTRYPOINT_RELATIVE,
    ATTEMPT_005_FREEZE_ID,
    ATTEMPT_005_FREEZE_RELATIVE,
    ATTEMPT_005_FREEZE_ROOT,
    ATTEMPT_005_FREEZE_STATUS,
    ATTEMPT_005_HOST_COMMAND_RELATIVE,
    ATTEMPT_005_HOST_SPAWNER_RELATIVE,
    ATTEMPT_005_ID,
    ATTEMPT_005_INVOCATION_ACKNOWLEDGEMENT,
    ATTEMPT_005_LEASE_ACKNOWLEDGEMENT,
    ATTEMPT_005_LEASE_V1_RELATIVE,
    ATTEMPT_005_LEASE_V2_RELATIVE,
    ATTEMPT_005_OUTPUT_ROOT,
    ATTEMPT_005_PROFILE_RELATIVE,
    ATTEMPT_005_WRAPPER_RELATIVE,
    AUTHORIZED_CELL_COUNT,
    EXPECTED_GENERIC_RUNTIME_BACKEND_SHA256,
    EXPECTED_SCIENTIFIC_AUTHORIZATION_FILE_SHA256,
    EXPECTED_SCIENTIFIC_AUTHORIZATION_SHA256,
    EXPECTED_TORCH2PC_COMMIT,
    GENERIC_RUNTIME_BACKEND_RELATIVE,
    RESERVE_PROBE_COUNT,
    SCIENTIFIC_RUNTIME_AUTHORIZATION_RELATIVE,
    Attempt005Authorization,
    Attempt005ExecutionFreeze,
    canonical_json,
    sha256_object,
    verify_attempt_005_execution_freeze,
    verify_unconsumed_attempt_005_authorization,
)
from torch2pc_thesis.stage3b_qwake_attempt_005_lane_isolation import (
    ENABLE_ENV as LANE_ISOLATION_ENABLE_ENV,
)
from torch2pc_thesis.stage3b_qwake_attempt_005_lane_isolation import (
    HIP_VISIBLE_DEVICES,
    ROCM_THREAD_ENV,
)

BASE_IMAGE: Final = (
    "rocm/pytorch@sha256:"
    "96a2fb24dec9896e2f8238178f0c49d0dcc4c7dcc597be09e4564316bd86d191"
)
IMAGE_REPO_PREFIX: Final = "torch2pc-layerwise-thesis@sha256:"
CPUSET_CPUS: Final = "0-7"
THREAD_ENV: Final = tuple(ROCM_THREAD_ENV.items())
RUNTIME_TIMEOUT_SECONDS: Final = 7200
TERMINATION_GRACE_SECONDS: Final = 30


class Attempt005HostOneShotError(RuntimeError):
    """Raised when the host-side one-shot boundary cannot be preserved."""


def _canonical_mapping(value: dict[str, object]) -> bytes:
    return canonical_json(value).encode("utf-8")


def _sha256_file(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise Attempt005HostOneShotError(f"regular file required: {path}")
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _hex_sha256(path: Path) -> str:
    return _sha256_file(path).removeprefix("sha256:")


def _run(
    argv: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        argv,
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def _require_command(
    argv: list[str],
    *,
    cwd: Path,
    label: str,
    env: dict[str, str] | None = None,
) -> bytes:
    result = _run(argv, cwd=cwd, env=env)
    if result.returncode != 0:
        output = result.stdout.decode("utf-8", errors="replace")
        raise Attempt005HostOneShotError(
            f"{label} failed with status {result.returncode}: {output}"
        )
    return result.stdout


def _git_scalar(root: Path, *args: str) -> str:
    return _require_command(
        ["git", *args],
        cwd=root,
        label="git " + " ".join(args),
    ).decode("utf-8").strip()


def _remote_main(root: Path) -> str:
    raw = _require_command(
        ["git", "ls-remote", "--refs", "origin", "refs/heads/main"],
        cwd=root,
        label="git ls-remote main",
    ).decode("utf-8").strip()
    parts = raw.split()
    if len(parts) != 2 or parts[1] != "refs/heads/main":
        raise Attempt005HostOneShotError("remote main identity differs")
    return parts[0]


def _require_rfc3339_seconds(value: str) -> None:
    if re.fullmatch(
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z",
        value,
    ) is None:
        raise Attempt005HostOneShotError(
            "claimed-at-utc must be RFC3339 UTC seconds"
        )
    datetime.fromisoformat(value.replace("Z", "+00:00"))


def _write_exclusive(path: Path, content: bytes, mode: int = 0o600) -> None:
    if not content:
        raise Attempt005HostOneShotError("empty durable payload")
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, mode)
    try:
        view = memoryview(content)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise Attempt005HostOneShotError(
                    "durable write made no progress"
                )
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write_registry(path: Path, base: Path, relatives: list[str]) -> None:
    lines = []
    for relative in sorted(relatives):
        lines.append(f"{_hex_sha256(base / relative)}  {relative}\n")
    _write_exclusive(path, "".join(lines).encode("utf-8"))


def _require_absent_effects(root: Path) -> None:
    for relative in (
        ATTEMPT_005_FREEZE_ROOT,
        ATTEMPT_005_AUTHORIZATION_ROOT,
        ATTEMPT_005_OUTPUT_ROOT,
        ATTEMPT_005_LEASE_V1_RELATIVE,
        ATTEMPT_005_LEASE_V2_RELATIVE,
        ATTEMPT_005_HOST_COMMAND_RELATIVE,
        ATTEMPT_005_DURABLE_OUTCOME_RELATIVE,
    ):
        if os.path.lexists(root / relative):
            raise Attempt005HostOneShotError(
                f"Attempt-005 effect already exists: {relative}"
            )
    staging = tuple(
        (root / ATTEMPT_005_OUTPUT_ROOT.parent).glob(
            f".{ATTEMPT_005_OUTPUT_ROOT.name}.staging-*"
        )
    )
    if staging:
        raise Attempt005HostOneShotError(
            "Attempt-005 staging already exists"
        )


def _require_source_state(root: Path) -> tuple[str, str]:
    if Path(_git_scalar(root, "rev-parse", "--show-toplevel")).resolve() != root:
        raise Attempt005HostOneShotError("project root differs")
    head = _git_scalar(root, "rev-parse", "HEAD")
    tree = _git_scalar(root, "rev-parse", "HEAD^{tree}")
    if _remote_main(root) != head:
        raise Attempt005HostOneShotError(
            "execution source is not current remote main"
        )
    if _git_scalar(root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise Attempt005HostOneShotError(
            "execution source worktree must be clean before materialization"
        )
    torch2pc = root / "external/Torch2PC"
    if not torch2pc.is_dir() or torch2pc.is_symlink():
        raise Attempt005HostOneShotError("Torch2PC checkout is absent")
    torch2pc_head = _git_scalar(torch2pc, "rev-parse", "HEAD")
    if torch2pc_head != EXPECTED_TORCH2PC_COMMIT:
        raise Attempt005HostOneShotError(
            "Torch2PC commit differs from preregistered Attempt-005 input"
        )
    if _sha256_file(root / GENERIC_RUNTIME_BACKEND_RELATIVE) != (
        EXPECTED_GENERIC_RUNTIME_BACKEND_SHA256
    ):
        raise Attempt005HostOneShotError(
            "historical generic runtime backend changed"
        )
    if _sha256_file(root / SCIENTIFIC_RUNTIME_AUTHORIZATION_RELATIVE) != (
        EXPECTED_SCIENTIFIC_AUTHORIZATION_FILE_SHA256
    ):
        raise Attempt005HostOneShotError(
            "scientific runtime authorization file changed"
        )
    scientific = json.loads(
        (root / SCIENTIFIC_RUNTIME_AUTHORIZATION_RELATIVE).read_text(
            encoding="utf-8"
        )
    )
    if scientific.get("authorization_sha256") != (
        EXPECTED_SCIENTIFIC_AUTHORIZATION_SHA256
    ):
        raise Attempt005HostOneShotError(
            "scientific runtime authorization identity changed"
        )
    return head, tree


def _build_image(
    root: Path,
    source_commit: str,
) -> tuple[str, str, bytes, bytes]:
    docker = shutil.which("docker")
    if docker is None:
        raise Attempt005HostOneShotError("docker executable is unavailable")
    tag = f"torch2pc-layerwise-thesis:attempt005-{source_commit[:12]}"
    build_argv = [
        docker,
        "build",
        "--file",
        "Dockerfile.rocm",
        "--build-arg",
        f"BASE_IMAGE={BASE_IMAGE}",
        "--build-arg",
        f"SOURCE_GIT_COMMIT={source_commit}",
        "--tag",
        tag,
        ".",
    ]
    build = _run(build_argv, cwd=root)
    if build.returncode != 0:
        output = build.stdout.decode("utf-8", errors="replace")
        raise Attempt005HostOneShotError(
            f"Docker build failed with status {build.returncode}: {output}"
        )

    inspect_raw = _require_command(
        [docker, "image", "inspect", tag],
        cwd=root,
        label="docker image inspect",
    )
    value = json.loads(inspect_raw)
    if not isinstance(value, list) or len(value) != 1:
        raise Attempt005HostOneShotError("Docker image inspection differs")
    record = cast(dict[str, Any], value[0])
    image_digest = record.get("Id")
    if not isinstance(image_digest, str) or re.fullmatch(
        r"sha256:[0-9a-f]{64}",
        image_digest,
    ) is None:
        raise Attempt005HostOneShotError("Docker local image ID differs")

    repo_digests = record.get("RepoDigests")
    if repo_digests is None:
        repo_digests = []
    if not isinstance(repo_digests, list):
        raise Attempt005HostOneShotError("Docker RepoDigests differs")
    matching = sorted(
        item
        for item in repo_digests
        if isinstance(item, str) and item.startswith(IMAGE_REPO_PREFIX)
    )
    if len(matching) > 1:
        raise Attempt005HostOneShotError(
            "multiple local torch2pc-layerwise-thesis repo digests observed"
        )
    repo_digest = matching[0] if matching else ""
    labels = (
        record.get("Config", {}).get("Labels", {})
        if isinstance(record.get("Config"), dict)
        else {}
    )
    if not isinstance(labels, dict):
        raise Attempt005HostOneShotError("Docker labels differ")
    if labels.get("org.opencontainers.image.revision") != source_commit:
        raise Attempt005HostOneShotError("image source revision differs")
    if labels.get("io.torch2pc.base-image") != BASE_IMAGE:
        raise Attempt005HostOneShotError("image base-image label differs")
    return image_digest, repo_digest, build.stdout, inspect_raw


def _materialize_freeze(
    root: Path,
    *,
    source_commit: str,
    source_tree: str,
    image_digest: str,
    image_repo_digest: str,
    build_log: bytes,
    inspection_raw: bytes,
) -> Attempt005ExecutionFreeze:
    source_files = {
        ATTEMPT_005_CONTRACT_RELATIVE.as_posix(): _sha256_file(
            root / ATTEMPT_005_CONTRACT_RELATIVE
        ),
        ATTEMPT_005_WRAPPER_RELATIVE.as_posix(): _sha256_file(
            root / ATTEMPT_005_WRAPPER_RELATIVE
        ),
        ATTEMPT_005_BACKEND_RELATIVE.as_posix(): _sha256_file(
            root / ATTEMPT_005_BACKEND_RELATIVE
        ),
        ATTEMPT_005_PROFILE_RELATIVE.as_posix(): _sha256_file(
            root / ATTEMPT_005_PROFILE_RELATIVE
        ),
        GENERIC_RUNTIME_BACKEND_RELATIVE.as_posix(): _sha256_file(
            root / GENERIC_RUNTIME_BACKEND_RELATIVE
        ),
        ATTEMPT_005_HOST_SPAWNER_RELATIVE.as_posix(): _sha256_file(
            root / ATTEMPT_005_HOST_SPAWNER_RELATIVE
        ),
        ATTEMPT_005_ENTRYPOINT_RELATIVE.as_posix(): _sha256_file(
            root / ATTEMPT_005_ENTRYPOINT_RELATIVE
        ),
        SCIENTIFIC_RUNTIME_AUTHORIZATION_RELATIVE.as_posix(): _sha256_file(
            root / SCIENTIFIC_RUNTIME_AUTHORIZATION_RELATIVE
        ),
    }
    freeze_payload: dict[str, object] = {
        "schema_version": 1,
        "freeze_id": ATTEMPT_005_FREEZE_ID,
        "status": ATTEMPT_005_FREEZE_STATUS,
        "attempt_id": ATTEMPT_005_ID,
        "source_commit": source_commit,
        "source_tree": source_tree,
        "wrapper_commit": source_commit,
        "torch2pc_commit": EXPECTED_TORCH2PC_COMMIT,
        "image_digest": image_digest,
        "image_repo_digest": image_repo_digest,
        "contract_sha256": source_files[
            ATTEMPT_005_CONTRACT_RELATIVE.as_posix()
        ],
        "wrapper_sha256": source_files[
            ATTEMPT_005_WRAPPER_RELATIVE.as_posix()
        ],
        "backend_sha256": source_files[
            ATTEMPT_005_BACKEND_RELATIVE.as_posix()
        ],
        "profile_sha256": source_files[
            ATTEMPT_005_PROFILE_RELATIVE.as_posix()
        ],
        "generic_backend_sha256": source_files[
            GENERIC_RUNTIME_BACKEND_RELATIVE.as_posix()
        ],
        "host_spawner_sha256": source_files[
            ATTEMPT_005_HOST_SPAWNER_RELATIVE.as_posix()
        ],
        "entrypoint_sha256": source_files[
            ATTEMPT_005_ENTRYPOINT_RELATIVE.as_posix()
        ],
        "scientific_authorization_relative": (
            SCIENTIFIC_RUNTIME_AUTHORIZATION_RELATIVE.as_posix()
        ),
        "scientific_authorization_sha256": (
            EXPECTED_SCIENTIFIC_AUTHORIZATION_SHA256
        ),
        "scientific_authorization_file_sha256": (
            EXPECTED_SCIENTIFIC_AUTHORIZATION_FILE_SHA256
        ),
        "output_root": ATTEMPT_005_OUTPUT_ROOT.as_posix(),
        "lease_v1_relative": ATTEMPT_005_LEASE_V1_RELATIVE.as_posix(),
        "lease_v2_relative": ATTEMPT_005_LEASE_V2_RELATIVE.as_posix(),
        "durable_outcome_relative": (
            ATTEMPT_005_DURABLE_OUTCOME_RELATIVE.as_posix()
        ),
        "authorized_cell_count": AUTHORIZED_CELL_COUNT,
        "reserve_probe_count": RESERVE_PROBE_COUNT,
        "execution_count": 1,
        "runtime_execution_started": False,
        "runtime_execution_performed": False,
        "engineering_evidence_present": False,
        "scientific_execution_open": False,
        "test_dataset_access": False,
        "publication_permitted": False,
    }
    freeze_payload["freeze_sha256"] = sha256_object(freeze_payload)
    freeze = Attempt005ExecutionFreeze(**cast(dict[str, Any], freeze_payload))
    freeze.require()

    freeze_root = root / ATTEMPT_005_FREEZE_ROOT
    freeze_root.mkdir(parents=True, exist_ok=False)
    _write_exclusive(
        freeze_root / "execution.json",
        freeze.canonical_json().encode("utf-8"),
    )
    source_lines = "".join(
        f"{digest.removeprefix('sha256:')}  {relative}\n"
        for relative, digest in sorted(source_files.items())
    )
    _write_exclusive(
        freeze_root / "source-SHA256SUMS",
        source_lines.encode("utf-8"),
    )
    _write_exclusive(freeze_root / "image-build.log", build_log)
    _write_exclusive(freeze_root / "image-inspection.json", inspection_raw)
    _write_registry(
        freeze_root / "SHA256SUMS",
        freeze_root,
        [
            "execution.json",
            "image-build.log",
            "image-inspection.json",
            "source-SHA256SUMS",
        ],
    )
    verified = verify_attempt_005_execution_freeze(
        root,
        require_runtime_environment=False,
    )
    if verified != freeze:
        raise Attempt005HostOneShotError(
            "materialized Attempt-005 freeze differs"
        )
    return freeze


def _materialize_authorization(
    root: Path,
    freeze: Attempt005ExecutionFreeze,
    *,
    operator_identity: str,
    action_phrase: str,
) -> Attempt005Authorization:
    current_operator = pwd.getpwuid(os.getuid()).pw_name
    if operator_identity != current_operator:
        raise Attempt005HostOneShotError(
            "operator identity differs from current POSIX account"
        )
    if action_phrase != ATTEMPT_005_INVOCATION_ACKNOWLEDGEMENT:
        raise Attempt005HostOneShotError(
            "Attempt-005 authorization phrase differs"
        )
    payload: dict[str, object] = {
        "schema_version": 1,
        "authorization_id": ATTEMPT_005_AUTHORIZATION_ID,
        "status": ATTEMPT_005_AUTHORIZATION_STATUS,
        "attempt_id": ATTEMPT_005_ID,
        "freeze_sha256": freeze.freeze_sha256,
        "operator_identity_kind": "local-posix-account",
        "operator_identity": operator_identity,
        "action_phrase": action_phrase,
        "execution_count": 1,
        "authorization_effective": True,
        "authorization_consumed": False,
        "attempt_started": False,
        "runtime_execution_started": False,
        "runtime_execution_performed": False,
        "retry_permitted": False,
        "scientific_execution_open": False,
        "test_dataset_access": False,
        "publication_permitted": False,
    }
    payload["authorization_sha256"] = sha256_object(payload)
    authorization = Attempt005Authorization(**cast(dict[str, Any], payload))
    authorization.require(freeze)

    authorization_root = root / ATTEMPT_005_AUTHORIZATION_ROOT
    authorization_root.mkdir(parents=True, exist_ok=False)
    _write_exclusive(
        authorization_root / "authorization.json",
        authorization.canonical_json().encode("utf-8"),
    )
    source_relatives = [
        ATTEMPT_005_FREEZE_RELATIVE.as_posix(),
        (ATTEMPT_005_FREEZE_ROOT / "SHA256SUMS").as_posix(),
        (ATTEMPT_005_FREEZE_ROOT / "source-SHA256SUMS").as_posix(),
        ATTEMPT_005_CONTRACT_RELATIVE.as_posix(),
        ATTEMPT_005_HOST_SPAWNER_RELATIVE.as_posix(),
    ]
    _write_registry(
        authorization_root / "source-SHA256SUMS",
        root,
        source_relatives,
    )
    _write_registry(
        authorization_root / "SHA256SUMS",
        authorization_root,
        ["authorization.json", "source-SHA256SUMS"],
    )
    verified = verify_unconsumed_attempt_005_authorization(root, freeze)
    if verified != authorization:
        raise Attempt005HostOneShotError(
            "materialized Attempt-005 authorization differs"
        )
    return authorization


def _group_gid(name: str) -> int:
    try:
        return grp.getgrnam(name).gr_gid
    except KeyError as exc:
        raise Attempt005HostOneShotError(
            f"required host group is absent: {name}"
        ) from exc


def _materialize_command(
    root: Path,
    freeze: Attempt005ExecutionFreeze,
    authorization: Attempt005Authorization,
    *,
    claimed_at_utc: str,
    lease_acknowledgement: str,
    memory_limit: str,
    shm_size: str,
    tmpfs_size: str,
) -> tuple[dict[str, object], list[str]]:
    _require_rfc3339_seconds(claimed_at_utc)
    if lease_acknowledgement != ATTEMPT_005_LEASE_ACKNOWLEDGEMENT:
        raise Attempt005HostOneShotError(
            "Attempt-005 lease acknowledgement differs"
        )
    for value, label in (
        (memory_limit, "memory-limit"),
        (shm_size, "shm-size"),
        (tmpfs_size, "tmpfs-size"),
    ):
        if re.fullmatch(r"[1-9][0-9]*(?:[kKmMgG])?", value) is None:
            raise Attempt005HostOneShotError(f"{label} differs")

    docker = shutil.which("docker")
    if docker is None:
        raise Attempt005HostOneShotError("docker executable is unavailable")

    env_pairs = [
        ("HOME", "/tmp/home"),
        ("PYTHONDONTWRITEBYTECODE", "1"),
        ("PYTHONHASHSEED", "0"),
        ("PYTHONUNBUFFERED", "1"),
        ("SOURCE_GIT_COMMIT", freeze.source_commit),
        ("EXPERIMENT_IMAGE_DIGEST", freeze.image_digest),
        ("EXPERIMENT_IMAGE_REPO_DIGEST", freeze.image_repo_digest),
        ("HIP_VISIBLE_DEVICES", HIP_VISIBLE_DEVICES),
        (LANE_ISOLATION_ENABLE_ENV, "1"),
        *THREAD_ENV,
    ]
    argv = [
        docker,
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
        f"{os.getuid()}:{os.getgid()}",
        "--group-add",
        str(_group_gid("video")),
        "--group-add",
        str(_group_gid("render")),
        "--device",
        "/dev/kfd:/dev/kfd:rwm",
        "--device",
        "/dev/dri:/dev/dri:rwm",
        "--cpuset-cpus",
        CPUSET_CPUS,
        "--memory",
        memory_limit,
        "--shm-size",
        shm_size,
        "--tmpfs",
        f"/tmp:rw,nosuid,nodev,mode=1777,size={tmpfs_size}",
        "--workdir",
        "/workspace",
    ]
    for key, value in env_pairs:
        argv.extend(("--env", f"{key}={value}"))
    for source, target, access in (
        (root / "experiments/frozen", "/workspace/experiments/frozen", "ro"),
        (root / "external/Torch2PC", "/workspace/external/Torch2PC", "ro"),
        (root / "results", "/workspace/results", "rw"),
    ):
        if not source.is_dir() or source.is_symlink():
            raise Attempt005HostOneShotError(
                f"required mount source differs: {source}"
            )
        argv.extend(("--volume", f"{source}:{target}:{access}"))
    argv.extend(
        (
            freeze.image_digest,
            "python",
            f"/workspace/{ATTEMPT_005_ENTRYPOINT_RELATIVE.as_posix()}",
            "--project-root",
            "/workspace",
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
        "attempt_id": ATTEMPT_005_ID,
        "freeze_sha256": freeze.freeze_sha256,
        "authorization_sha256": authorization.authorization_sha256,
        "claimed_at_utc": claimed_at_utc,
        "argv": argv,
        "environment": env_pairs,
        "cpuset_cpus": CPUSET_CPUS,
        "host_command_constructor": ATTEMPT_005_HOST_SPAWNER_RELATIVE.as_posix(),
        "shell_interpretation_used": False,
        "environment_inherited": False,
        "host_process_spawned": False,
        "authorization_consumed": False,
        "attempt_started": False,
        "execution_lease_materialized": False,
        "runtime_execution_started": False,
        "runtime_execution_performed": False,
        "automatic_retry_permitted": False,
    }
    payload["command_sha256"] = sha256_object(payload)
    _write_exclusive(
        root / ATTEMPT_005_HOST_COMMAND_RELATIVE,
        _canonical_mapping(payload),
    )
    return payload, argv


def _bounded_host_env() -> dict[str, str]:
    return {
        "HOME": os.environ.get("HOME", "/tmp"),
        "PATH": os.defpath,
        "LANG": os.environ.get("LANG", "C.UTF-8"),
    }


def _run_one_child(
    root: Path,
    command: dict[str, object],
    argv: list[str],
) -> int:
    outcome_path = root / ATTEMPT_005_DURABLE_OUTCOME_RELATIVE
    if os.path.lexists(outcome_path):
        raise Attempt005HostOneShotError(
            "durable host outcome already exists"
        )
    spawned = False
    timed_out = False
    return_code: int | None = None
    stdout = b""
    stderr = b""
    spawn_error: str | None = None
    try:
        process = subprocess.Popen(  # noqa: S603
            tuple(argv),
            cwd=root,
            env=_bounded_host_env(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            start_new_session=True,
            close_fds=True,
            text=False,
            bufsize=0,
        )
        spawned = True
        try:
            stdout, stderr = process.communicate(
                timeout=RUNTIME_TIMEOUT_SECONDS
            )
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(process.pid, signal.SIGTERM)
            try:
                stdout, stderr = process.communicate(
                    timeout=TERMINATION_GRACE_SECONDS
                )
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                stdout, stderr = process.communicate()
        return_code = process.returncode
    except OSError as exc:
        spawn_error = f"{type(exc).__name__}: {exc}"

    lease_exists = (
        root / ATTEMPT_005_LEASE_V1_RELATIVE
    ).is_file()
    output_exists = (root / ATTEMPT_005_OUTPUT_ROOT).is_dir()
    outcome: dict[str, object] = {
        "schema_version": 1,
        "attempt_id": ATTEMPT_005_ID,
        "command_sha256": command["command_sha256"],
        "spawn_call_entered": True,
        "child_spawn_count": 1 if spawned else 0,
        "host_process_spawned": spawned,
        "return_code": return_code,
        "timed_out": timed_out,
        "spawn_error": spawn_error,
        "stdout_utf8": stdout.decode("utf-8", errors="replace"),
        "stderr_utf8": stderr.decode("utf-8", errors="replace"),
        "authorization_consumed": lease_exists,
        "attempt_started": lease_exists,
        "execution_lease_materialized": lease_exists,
        "runtime_output_present": output_exists,
        "automatic_retry_performed": False,
        "automatic_retry_permitted": False,
        "scientific_execution_open": False,
        "test_dataset_access": False,
        "publication_permitted": False,
    }
    outcome["outcome_sha256"] = sha256_object(outcome)
    _write_exclusive(outcome_path, _canonical_mapping(outcome))

    print("=== ATTEMPT-005 HOST ONE-SHOT OUTCOME ===")
    print(f"HOST_PROCESS_SPAWNED={str(spawned).lower()}")
    print(f"CHILD_SPAWN_COUNT={outcome['child_spawn_count']}")
    print(f"RETURN_CODE={return_code}")
    print(f"TIMED_OUT={str(timed_out).lower()}")
    print(f"AUTHORIZATION_CONSUMED={str(lease_exists).lower()}")
    print(f"ATTEMPT_STARTED={str(lease_exists).lower()}")
    print(f"RUNTIME_OUTPUT_PRESENT={str(output_exists).lower()}")
    print("AUTOMATIC_RETRY_PERFORMED=false")
    print(f"HOST_OUTCOME_SHA256={outcome['outcome_sha256']}")
    if stdout:
        print("=== CHILD STDOUT ===")
        sys.stdout.write(stdout.decode("utf-8", errors="replace"))
        if not stdout.endswith(b"\n"):
            print()
    if stderr:
        print("=== CHILD STDERR ===")
        sys.stderr.write(stderr.decode("utf-8", errors="replace"))
        if not stderr.endswith(b"\n"):
            print(file=sys.stderr)

    if not spawned:
        raise Attempt005HostOneShotError(
            "host child was not spawned; no retry is permitted"
        )
    if timed_out:
        raise Attempt005HostOneShotError(
            "host child timed out; no retry is permitted"
        )
    if return_code is None:
        raise Attempt005HostOneShotError("host child return code is absent")
    return return_code


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--claimed-at-utc", required=True)
    parser.add_argument("--operator-identity", required=True)
    parser.add_argument(
        "--authorization-phrase",
        required=True,
        help=f"Must exactly equal {ATTEMPT_005_INVOCATION_ACKNOWLEDGEMENT}",
    )
    parser.add_argument(
        "--lease-acknowledgement",
        required=True,
        help=f"Must exactly equal {ATTEMPT_005_LEASE_ACKNOWLEDGEMENT}",
    )
    parser.add_argument("--memory-limit", default="48g")
    parser.add_argument("--shm-size", default="8g")
    parser.add_argument("--tmpfs-size", default="4g")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.project_root.expanduser().resolve()
    _require_rfc3339_seconds(args.claimed_at_utc)
    _require_absent_effects(root)
    source_commit, source_tree = _require_source_state(root)

    image_digest, image_repo_digest, build_log, inspection_raw = _build_image(
        root,
        source_commit,
    )
    freeze = _materialize_freeze(
        root,
        source_commit=source_commit,
        source_tree=source_tree,
        image_digest=image_digest,
        image_repo_digest=image_repo_digest,
        build_log=build_log,
        inspection_raw=inspection_raw,
    )
    authorization = _materialize_authorization(
        root,
        freeze,
        operator_identity=args.operator_identity,
        action_phrase=args.authorization_phrase,
    )
    command, argv = _materialize_command(
        root,
        freeze,
        authorization,
        claimed_at_utc=args.claimed_at_utc,
        lease_acknowledgement=args.lease_acknowledgement,
        memory_limit=args.memory_limit,
        shm_size=args.shm_size,
        tmpfs_size=args.tmpfs_size,
    )

    print("=== ATTEMPT-005 PRE-SPAWN IDENTITY ===")
    print(f"SOURCE_COMMIT={source_commit}")
    print(f"SOURCE_TREE={source_tree}")
    print(f"IMAGE_DIGEST={image_digest}")
    print(f"IMAGE_REPO_DIGEST={image_repo_digest}")
    print(f"FREEZE_SHA256={freeze.freeze_sha256}")
    print(f"AUTHORIZATION_SHA256={authorization.authorization_sha256}")
    print(f"COMMAND_SHA256={command['command_sha256']}")
    print("CPUSET_CPUS=0-7")
    print("ROCM_OMP_NUM_THREADS=8")
    print("ROCM_MKL_NUM_THREADS=8")
    print("ROCM_OPENBLAS_NUM_THREADS=8")
    print("ROCM_NUMEXPR_NUM_THREADS=8")
    print("CPU_WORKER_CPUSET=0")
    print("CPU_WORKER_THREADS=1")
    print("INTERNAL_LANE_WORKER_COUNT=2")
    print("AUTHORIZATION_CONSUMED=false")
    print("ATTEMPT_STARTED=false")
    print("AUTOMATIC_RETRY_PERMITTED=false")

    return_code = _run_one_child(root, command, argv)
    if return_code != 0:
        raise Attempt005HostOneShotError(
            f"Attempt-005 child returned {return_code}; no retry is permitted"
        )
    print("ATTEMPT004_ONE_SHOT_ENGINEERING_INVOCATION_COMPLETED=true")
    print("SCIENTIFIC_EXECUTION_OPEN=false")
    print("TEST_DATASET_ACCESS=false")
    print("PUBLICATION_PERMITTED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
