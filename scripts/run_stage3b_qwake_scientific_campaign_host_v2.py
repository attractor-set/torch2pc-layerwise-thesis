#!/usr/bin/env python3
"""Host-side one-shot launcher for a preregistered QWake scientific campaign.

The launcher is part of the frozen source closure.  It accepts no command
snippet, plugin, module name, Docker options, or alternate entrypoint.  Before
crossing the one-shot boundary it verifies the canonical request/authorization,
the exact clean source checkout, the exact local Docker image ID and source
revision, confined input namespaces, and absence of the authorized output root.

Authorization is consumed by atomically creating the output root and writing
``host-claim.json``.  Exactly one ``docker run`` is then attempted.  The claim
is never removed and the launcher never retries automatically.
"""

from __future__ import annotations

import argparse
import grp
import hashlib
import json
import os
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path
from typing import Final

from torch2pc_thesis.stage3b_qwake_scientific_campaign import (
    ScientificCampaignRequest,
    ScientificHostClaim,
    load_scientific_authorization,
    load_scientific_request,
)
from torch2pc_thesis.stage3b_qwake_scientific_identity_v2 import (
    ScientificRuntimeIdentity,
    ScientificRuntimeIdentityError,
    runtime_identity_from_image_inspection,
    verify_runtime_manifest,
)
from torch2pc_thesis.stage3b_qwake_scientific_runtime_v2 import (
    ScientificRuntimeError,
    preflight_scientific_campaign,
)

_CONTAINER_ROOT: Final = Path("/workspace")
_CONTAINER_REQUEST: Final = Path("/run/qwake-scientific-request.json")
_CONTAINER_AUTHORIZATION: Final = Path("/run/qwake-scientific-authorization.json")


class ScientificHostLaunchError(RuntimeError):
    """Raised when host admission or the single Docker invocation fails."""


def _run(
    argv: list[str],
    *,
    cwd: Path,
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        argv,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def _require_run(argv: list[str], *, cwd: Path, label: str) -> bytes:
    result = _run(argv, cwd=cwd)
    if result.returncode != 0:
        output = result.stdout.decode("utf-8", errors="replace")
        if output:
            print(output, end="" if output.endswith("\n") else "\n")
        raise ScientificHostLaunchError(f"{label} failed with status {result.returncode}")
    return result.stdout


def _scalar(argv: list[str], *, cwd: Path) -> str:
    return (
        _require_run(argv, cwd=cwd, label=" ".join(argv)).decode("utf-8", errors="strict").strip()
    )


def _require_exact_source_checkout(root: Path, source_commit: str) -> None:
    if Path(_scalar(["git", "rev-parse", "--show-toplevel"], cwd=root)).resolve() != root:
        raise ScientificHostLaunchError("host project root differs")
    if _scalar(["git", "rev-parse", "HEAD"], cwd=root) != source_commit:
        raise ScientificHostLaunchError("host checkout source commit differs")
    protected = (
        "src",
        "scripts",
        "requirements",
        "Dockerfile.qwake-scientific",
                "pyproject.toml",
    )
    status = _require_run(
        [
            "git",
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "--",
            *protected,
        ],
        cwd=root,
        label="protected source status",
    )
    if status:
        raise ScientificHostLaunchError(
            "host executable/dependency closure is not clean: "
            + status.decode("utf-8", errors="replace")
        )


def _require_exact_local_image(
    docker: str,
    root: Path,
    request: ScientificCampaignRequest,
) -> ScientificRuntimeIdentity:
    """Derive the sole active runtime identity from immutable image metadata."""

    raw = _require_run(
        [docker, "image", "inspect", request.image_digest],
        cwd=root,
        label="docker image inspect",
    )
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ScientificHostLaunchError("docker image inspect JSON is invalid") from exc
    if not isinstance(payload, list) or len(payload) != 1 or not isinstance(payload[0], dict):
        raise ScientificHostLaunchError("docker image inspect cardinality differs")
    try:
        return runtime_identity_from_image_inspection(
            payload[0],
            expected_image_digest=request.image_digest,
            expected_source_commit=request.source_commit,
            expected_code_manifest_sha256=request.code_manifest_sha256,
        )
    except ScientificRuntimeIdentityError as exc:
        raise ScientificHostLaunchError(str(exc)) from exc


def _require_commit_bound_runtime_closure(
    root: Path,
    source_commit: str,
    identity: ScientificRuntimeIdentity,
) -> tuple[str, ...]:
    """Require manifest and every runtime member to be tracked bytes of HEAD."""

    try:
        paths = verify_runtime_manifest(root, identity)
    except ScientificRuntimeIdentityError as exc:
        raise ScientificHostLaunchError(str(exc)) from exc
    bound_paths = tuple(sorted(set(paths) | {identity.relative_path}))
    _require_run(
        ["git", "ls-files", "--error-unmatch", "--", *bound_paths],
        cwd=root,
        label="tracked scientific runtime closure",
    )
    dirty = _require_run(
        ["git", "diff", "--name-only", source_commit, "--", *bound_paths],
        cwd=root,
        label="scientific runtime closure Git binding",
    )
    if dirty.strip():
        raise ScientificHostLaunchError(
            "scientific runtime closure differs from source commit: "
            + dirty.decode("utf-8", errors="replace").strip()
        )
    return paths


def _resolved(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ScientificHostLaunchError("request path escapes host project root") from exc
    return candidate


def _require_regular(path: Path, label: str) -> None:
    if not path.is_file() or path.is_symlink():
        raise ScientificHostLaunchError(f"{label} must be a regular file: {path}")


def _sha256_file_prefixed(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _bound_input_files(
    request: ScientificCampaignRequest,
) -> tuple[tuple[str, str], ...]:
    """Return every request-bound physical input and its exact file digest."""

    bound: list[tuple[str, str]] = []
    if request.dataset is not None:
        bound.append((request.dataset.split.relative_path, request.dataset.split.sha256))
        bound.extend(
            (asset.relative_path, asset.sha256)
            for asset in request.dataset.dataset_assets
        )
    if request.sealed_c1_dataset is not None:
        bound.append(
            (request.sealed_c1_dataset.relative_path, request.sealed_c1_dataset.sha256)
        )
    bound.extend(
        (binding.relative_path, binding.sha256)
        for binding in request.candidate_policies
    )
    if request.frozen_policy is not None:
        bound.append((request.frozen_policy.relative_path, request.frozen_policy.sha256))
    bound.extend(
        (receipt.relative_path, receipt.file_sha256)
        for receipt in request.predecessor_receipts
    )
    paths = tuple(relative for relative, _digest in bound)
    if len(paths) != len(set(paths)):
        raise ScientificHostLaunchError("bound scientific input paths repeat")
    return tuple(sorted(bound))


def _require_bound_input_bytes(
    root: Path,
    request: ScientificCampaignRequest,
) -> tuple[tuple[str, str], ...]:
    """Verify every request-bound input byte before authorization consumption."""

    bound = _bound_input_files(request)
    for relative, expected_sha256 in bound:
        path = _resolved(root, relative)
        _require_regular(path, "bound scientific input")
        if _sha256_file_prefixed(path) != expected_sha256:
            raise ScientificHostLaunchError(
                f"bound scientific input digest differs: {relative}"
            )
    return bound


def _minimal_input_mount_parents(
    bound: tuple[tuple[str, str], ...],
) -> tuple[Path, ...]:
    """Choose non-overlapping relative parents that cover every bound input."""

    parents = sorted(
        {Path(relative).parent for relative, _digest in bound},
        key=lambda path: (len(path.parts), path.as_posix()),
    )
    selected: list[Path] = []
    for parent in parents:
        if parent == Path("."):
            raise ScientificHostLaunchError(
                "bound input cannot live at repository root"
            )
        if any(existing == parent or existing in parent.parents for existing in selected):
            continue
        selected.append(parent)
    return tuple(selected)


def _copy_bound_input(
    source: Path,
    target: Path,
    *,
    expected_sha256: str,
) -> None:
    """Copy one verified regular file into an exclusive read-only staging path."""

    target.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    source_fd = os.open(source, flags)
    target_fd: int | None = None
    try:
        target_fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o400)
        while True:
            chunk = os.read(source_fd, 1024 * 1024)
            if not chunk:
                break
            remaining = memoryview(chunk)
            while remaining:
                written = os.write(target_fd, remaining)
                if written <= 0:
                    raise ScientificHostLaunchError(
                        f"failed to stage scientific input bytes: {source}"
                    )
                remaining = remaining[written:]
        os.fsync(target_fd)
    finally:
        os.close(source_fd)
        if target_fd is not None:
            os.close(target_fd)
    os.chmod(target, 0o400, follow_symlinks=False)
    if _sha256_file_prefixed(target) != expected_sha256:
        raise ScientificHostLaunchError(
            f"staged scientific input digest differs: {source}"
        )


def _materialize_exact_input_stage(
    root: Path,
    request: ScientificCampaignRequest,
    stage_root: Path,
) -> tuple[tuple[Path, Path], ...]:
    """Create an exact, sibling-free physical input surface for Docker.

    Source directories may contain unrelated historical or test artifacts.  The
    container never sees those directories directly.  Every request-bound file
    is copied into a private staging tree, re-hashed there, and only minimal
    non-overlapping staging parents are mounted read-only at the original
    in-container relative paths.
    """

    bound = _require_bound_input_bytes(root, request)
    if not stage_root.is_dir() or stage_root.is_symlink():
        raise ScientificHostLaunchError("scientific input stage must be a real directory")

    expected_stage_files: set[Path] = set()
    for relative, expected_sha256 in bound:
        source = _resolved(root, relative)
        target = (stage_root / relative).resolve()
        try:
            target.relative_to(stage_root)
        except ValueError as exc:
            raise ScientificHostLaunchError(
                "staged scientific input escapes stage root"
            ) from exc
        _copy_bound_input(source, target, expected_sha256=expected_sha256)
        expected_stage_files.add(target)

    observed_stage_files: set[Path] = set()
    for path in stage_root.rglob("*"):
        if path.is_symlink():
            raise ScientificHostLaunchError(
                f"scientific input stage contains symlink: {path}"
            )
        if path.is_file():
            observed_stage_files.add(path.resolve())
    if observed_stage_files != expected_stage_files:
        extra = sorted(str(path) for path in observed_stage_files - expected_stage_files)
        missing = sorted(str(path) for path in expected_stage_files - observed_stage_files)
        raise ScientificHostLaunchError(
            "scientific input stage inventory differs: "
            f"extra={extra}; missing={missing}"
        )

    mounts: list[tuple[Path, Path]] = []
    for relative_parent in _minimal_input_mount_parents(bound):
        host_parent = (stage_root / relative_parent).resolve()
        container_parent = _CONTAINER_ROOT / relative_parent
        if not host_parent.is_dir() or host_parent.is_symlink():
            raise ScientificHostLaunchError(
                "scientific input staging parent is absent"
            )
        mounts.append((host_parent, container_parent))
    return tuple(mounts)


def _mount_arg(host: Path, container: Path, *, readonly: bool) -> str:
    fields = [
        "type=bind",
        f"src={host}",
        f"dst={container}",
    ]
    if readonly:
        fields.append("readonly")
    return ",".join(fields)


def _write_exclusive(path: Path, content: bytes) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, "wb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())


def _group_gid(name: str) -> int:
    try:
        return grp.getgrnam(name).gr_gid
    except KeyError as exc:
        raise ScientificHostLaunchError(f"required host group is unavailable: {name}") from exc


def _host_container_identity() -> tuple[int, int, int, int]:
    return (
        os.getuid(),
        os.getgid(),
        _group_gid("video"),
        _group_gid("render"),
    )


def _require_output_parent_preclaim(
    output_root: Path,
    *,
    host_uid: int,
) -> int:
    """Verify the existing output parent without creating or modifying it."""

    parent = output_root.parent
    if not parent.is_dir() or parent.is_symlink():
        raise ScientificHostLaunchError(
            "authorized output parent must preexist as a real directory"
        )
    snapshot = os.stat(parent, follow_symlinks=False)
    if snapshot.st_uid != host_uid:
        raise ScientificHostLaunchError(
            "authorized output parent owner differs from container uid"
        )
    mode = stat.S_IMODE(snapshot.st_mode)
    if not mode & stat.S_IWUSR or not mode & stat.S_IXUSR:
        raise ScientificHostLaunchError(
            "authorized output parent lacks owner write/execute permission"
        )
    return mode


def _write_consumed_failure_outcome(
    output_root: Path,
    request: ScientificCampaignRequest,
    host_claim: ScientificHostClaim,
    *,
    docker_status: int,
) -> None:
    """Materialize the predefined terminal consumed-failure state."""

    payload = {
        "schema_version": 1,
        "status": "terminal_consumed_failure",
        "request_sha256": request.request_sha256,
        "image_digest": request.image_digest,
        "host_claim_sha256": host_claim.claim_sha256,
        "docker_status": docker_status,
        "authorization_consumed": True,
        "automatic_retry_permitted": False,
        "test_dataset_access": False,
        "publication_permitted": False,
    }
    raw = (
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    _write_exclusive(output_root / "host-outcome.json", raw)


def _docker_command(
    docker: str,
    root: Path,
    request_path: Path,
    authorization_path: Path,
    request: ScientificCampaignRequest,
    host_claim: ScientificHostClaim,
    input_mounts: tuple[tuple[Path, Path], ...],
    output_root: Path,
    *,
    host_uid: int,
    host_gid: int,
    video_gid: int,
    render_gid: int,
) -> list[str]:
    command = [
        docker,
        "run",
        "--rm",
        "--network=none",
        "--read-only",
        "--security-opt=no-new-privileges",
        "--cap-drop=ALL",
        "--user",
        f"{host_uid}:{host_gid}",
        "--group-add",
        str(video_gid),
        "--group-add",
        str(render_gid),
        "--shm-size=2g",
        "--tmpfs",
        "/tmp:rw,nosuid,nodev,size=2g",
        "--device=/dev/kfd",
        "--device=/dev/dri",
        "--env",
        f"EXPERIMENT_IMAGE_DIGEST={request.image_digest}",
        "--env",
        f"QWAKE_SCIENTIFIC_HOST_CLAIM_SHA256={host_claim.claim_sha256}",
        "--env",
        "HOME=/tmp",
        "--mount",
        _mount_arg(request_path, _CONTAINER_REQUEST, readonly=True),
        "--mount",
        _mount_arg(authorization_path, _CONTAINER_AUTHORIZATION, readonly=True),
    ]
    for host_dir, container_dir in input_mounts:
        command.extend(["--mount", _mount_arg(host_dir, container_dir, readonly=True)])
    command.extend(
        [
            "--mount",
            _mount_arg(
                output_root,
                _CONTAINER_ROOT / request.output_root,
                readonly=False,
            ),
            request.image_digest,
            "python",
            "/workspace/scripts/run_stage3b_qwake_scientific_campaign_v2.py",
            "--project-root",
            "/workspace",
            "--request",
            str(_CONTAINER_REQUEST),
            "--authorization",
            str(_CONTAINER_AUTHORIZATION),
        ]
    )
    return command


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--authorization", required=True, type=Path)
    args = parser.parse_args()

    root = args.project_root.expanduser().resolve()
    request_path = args.request.expanduser().resolve()
    authorization_path = args.authorization.expanduser().resolve()
    if not root.is_dir() or root.is_symlink():
        raise ScientificHostLaunchError("host project root must be a real directory")
    _require_regular(request_path, "scientific request")
    _require_regular(authorization_path, "scientific authorization")

    request = load_scientific_request(request_path)
    authorization = load_scientific_authorization(authorization_path)
    authorization.require_request(request)
    _require_exact_source_checkout(root, request.source_commit)

    docker = shutil.which("docker")
    if docker is None:
        raise ScientificHostLaunchError("docker executable is unavailable")
    runtime_identity = _require_exact_local_image(docker, root, request)
    _require_commit_bound_runtime_closure(
        root,
        request.source_commit,
        runtime_identity,
    )

    if not Path("/dev/kfd").exists() or not Path("/dev/dri").exists():
        raise ScientificHostLaunchError("required ROCm device nodes are unavailable")

    host_uid, host_gid, video_gid, render_gid = _host_container_identity()

    _require_bound_input_bytes(root, request)
    try:
        preclaim = preflight_scientific_campaign(
            root,
            request,
            authorization,
            runtime_identity=runtime_identity,
        )
    except ScientificRuntimeError as exc:
        raise ScientificHostLaunchError(str(exc)) from exc

    output_root = _resolved(root, request.output_root)
    if output_root.exists():
        raise ScientificHostLaunchError("authorized output root already exists")
    output_parent_mode = _require_output_parent_preclaim(
        output_root,
        host_uid=host_uid,
    )
    host_claim = ScientificHostClaim.create(request, authorization)

    with tempfile.TemporaryDirectory(prefix="qwake-scientific-inputs-") as raw_stage:
        stage_root = Path(raw_stage).resolve()
        input_mounts = _materialize_exact_input_stage(root, request, stage_root)
        command = _docker_command(
            docker,
            root,
            request_path,
            authorization_path,
            request,
            host_claim,
            input_mounts,
            output_root,
            host_uid=host_uid,
            host_gid=host_gid,
            video_gid=video_gid,
            render_gid=render_gid,
        )

        print("=== QWAKE SCIENTIFIC HOST ADMISSION ===")
        print(f"SOURCE_COMMIT={request.source_commit}")
        print(f"IMAGE_DIGEST={request.image_digest}")
        print(f"REQUEST_SHA256={request.request_sha256}")
        print(f"AUTHORIZATION_SHA256={authorization.authorization_sha256}")
        print(f"ROLE={request.role.value}")
        print(f"RUNTIME_MANIFEST_RELATIVE={runtime_identity.relative_path}")
        print(f"RUNTIME_MANIFEST_SHA256={runtime_identity.sha256}")
        print(f"INPUT_MOUNT_COUNT={len(input_mounts)}")
        print(f"PRECLAIM_COMPONENT_PLAN_COUNT={len(preclaim.component_plans)}")
        print(f"PRECLAIM_PREDECESSOR_RECEIPT_COUNT={len(preclaim.predecessor_receipts)}")
        print(f"OUTPUT_PARENT_MODE={oct(output_parent_mode)}")
        print("HOST_PRECLAIM_COMPLETE=true")
        print("SOURCE_OVERLAY=false")
        print("NETWORK_ENABLED=false")
        print("TEST_DATASET_ACCESS=false")
        print("PUBLICATION_PERMITTED=false")
        print("DOCKER_BUILD_INVOKED=false")
        print("AUTOMATIC_RETRY_PERMITTED=false")
        print(f"HOST_UID={host_uid}")
        print(f"HOST_GID={host_gid}")
        print(f"VIDEO_GID={video_gid}")
        print(f"RENDER_GID={render_gid}")
        print(f"CONTAINER_PRIMARY_IDENTITY={host_uid}:{host_gid}")
        print("CAP_DROP_ALL=true")
        print("CAP_DAC_OVERRIDE_PRESENT=false")

        # Final admission transition. Every deterministic identity/input/receipt/plan
        # check and the exact Docker command have already completed above.
        output_root.mkdir(parents=False, exist_ok=False, mode=0o700)
        claim_path = output_root / "host-claim.json"
        _write_exclusive(claim_path, host_claim.canonical_json().encode("utf-8"))
        print("=== SCIENTIFIC AUTHORIZATION CONSUMED BY HOST CLAIM ===")
        print(f"HOST_CLAIM_SHA256={host_claim.claim_sha256}")
        print("AUTHORIZATION_CONSUMED=true")
        print("CLAIM_IS_FINAL_ADMISSION_TRANSITION=true")
        print("DOCKER_RUN_MAX_COUNT=1")

        invoked = _run(command, cwd=root)
        output = invoked.stdout.decode("utf-8", errors="replace")
        if output:
            print(output, end="" if output.endswith("\n") else "\n")
        print(f"DOCKER_RUN_STATUS={invoked.returncode}")
        if invoked.returncode != 0:
            _write_consumed_failure_outcome(
                output_root,
                request,
                host_claim,
                docker_status=invoked.returncode,
            )
            raise ScientificHostLaunchError(
                "single scientific Docker invocation failed; authorization remains consumed"
            )
        print("FINAL_STATUS=0")
        print("SCIENTIFIC_DOCKER_INVOCATION_COMPLETED=true")
        print("AUTOMATIC_RETRY_PERMITTED=false")

if __name__ == "__main__":
    main()
