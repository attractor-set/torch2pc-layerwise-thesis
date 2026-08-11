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
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Final

from torch2pc_thesis.stage3b_qwake_scientific_campaign import (
    ScientificCampaignRequest,
    ScientificHostClaim,
    load_scientific_authorization,
    load_scientific_request,
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
        raise ScientificHostLaunchError(
            f"{label} failed with status {result.returncode}"
        )
    return result.stdout


def _scalar(argv: list[str], *, cwd: Path) -> str:
    return _require_run(argv, cwd=cwd, label=" ".join(argv)).decode(
        "utf-8", errors="strict"
    ).strip()


def _require_exact_source_checkout(root: Path, source_commit: str) -> None:
    if Path(_scalar(["git", "rev-parse", "--show-toplevel"], cwd=root)).resolve() != root:
        raise ScientificHostLaunchError("host project root differs")
    if _scalar(["git", "rev-parse", "HEAD"], cwd=root) != source_commit:
        raise ScientificHostLaunchError("host checkout source commit differs")
    protected = (
        "src",
        "scripts",
        "requirements",
        "Dockerfile.rocm",
        ".dockerignore",
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
) -> None:
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
    image = payload[0]
    if image.get("Id") != request.image_digest:
        raise ScientificHostLaunchError("local Docker image ID differs from request")
    config = image.get("Config")
    if not isinstance(config, dict):
        raise ScientificHostLaunchError("Docker image Config is absent")
    labels = config.get("Labels")
    if not isinstance(labels, dict):
        raise ScientificHostLaunchError("Docker image labels are absent")
    if labels.get("org.opencontainers.image.revision") != request.source_commit:
        raise ScientificHostLaunchError("Docker source-revision label differs")
    env = config.get("Env")
    if not isinstance(env, list):
        raise ScientificHostLaunchError("Docker image environment is absent")
    env_map: dict[str, str] = {}
    for item in env:
        if isinstance(item, str) and "=" in item:
            name, value = item.split("=", 1)
            env_map[name] = value
    if env_map.get("SOURCE_GIT_COMMIT") != request.source_commit:
        raise ScientificHostLaunchError("Docker SOURCE_GIT_COMMIT differs")


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


def _input_parent_mounts(
    root: Path,
    request: ScientificCampaignRequest,
) -> tuple[tuple[Path, Path], ...]:
    """Return deterministic RO parent-directory mounts for bound inputs."""

    directories: dict[Path, Path] = {}

    def add_parent(relative: str) -> None:
        host_file = _resolved(root, relative)
        _require_regular(host_file, "bound scientific input")
        parent = host_file.parent
        relative_parent = Path(relative).parent
        if relative_parent == Path("."):
            raise ScientificHostLaunchError("bound input cannot live at repository root")
        directories[parent] = _CONTAINER_ROOT / relative_parent

    dataset = request.dataset
    if dataset is not None:
        dataset_root = _resolved(root, dataset.dataset_root)
        if not dataset_root.is_dir() or dataset_root.is_symlink():
            raise ScientificHostLaunchError("bound dataset_root must be a real directory")
        directories[dataset_root] = _CONTAINER_ROOT / dataset.dataset_root
        add_parent(dataset.split.relative_path)
        for asset in dataset.dataset_assets:
            add_parent(asset.relative_path)

    if request.sealed_c1_dataset is not None:
        add_parent(request.sealed_c1_dataset.relative_path)
    for binding in request.candidate_policies:
        add_parent(binding.relative_path)
    if request.frozen_policy is not None:
        add_parent(request.frozen_policy.relative_path)
    for receipt in request.predecessor_receipts:
        add_parent(receipt.relative_path)

    # Collapse nested mounts when a broader identical host/container mapping
    # already covers the child.  Broader mounts remain read-only.
    ordered = sorted(
        directories.items(),
        key=lambda item: (len(item[1].parts), item[1].as_posix()),
    )
    kept: list[tuple[Path, Path]] = []
    for host_dir, container_dir in ordered:
        covered = False
        for kept_host, kept_container in kept:
            try:
                host_suffix = host_dir.relative_to(kept_host)
                container_suffix = container_dir.relative_to(kept_container)
            except ValueError:
                continue
            if host_suffix == container_suffix:
                covered = True
                break
        if not covered:
            kept.append((host_dir, container_dir))
    return tuple(kept)


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


def _docker_command(
    docker: str,
    root: Path,
    request_path: Path,
    authorization_path: Path,
    request: ScientificCampaignRequest,
    host_claim: ScientificHostClaim,
    input_mounts: tuple[tuple[Path, Path], ...],
    output_root: Path,
) -> list[str]:
    command = [
        docker,
        "run",
        "--rm",
        "--network=none",
        "--read-only",
        "--security-opt=no-new-privileges",
        "--cap-drop=ALL",
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
        command.extend(
            ["--mount", _mount_arg(host_dir, container_dir, readonly=True)]
        )
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
            "/workspace/scripts/run_stage3b_qwake_scientific_campaign.py",
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
    _require_exact_local_image(docker, root, request)

    if not Path("/dev/kfd").exists() or not Path("/dev/dri").exists():
        raise ScientificHostLaunchError("required ROCm device nodes are unavailable")

    input_mounts = _input_parent_mounts(root, request)
    output_root = _resolved(root, request.output_root)
    if output_root.exists():
        raise ScientificHostLaunchError("authorized output root already exists")
    output_root.parent.mkdir(parents=True, exist_ok=True)

    print("=== QWAKE SCIENTIFIC HOST ADMISSION ===")
    print(f"SOURCE_COMMIT={request.source_commit}")
    print(f"IMAGE_DIGEST={request.image_digest}")
    print(f"REQUEST_SHA256={request.request_sha256}")
    print(f"AUTHORIZATION_SHA256={authorization.authorization_sha256}")
    print(f"ROLE={request.role.value}")
    print(f"INPUT_MOUNT_COUNT={len(input_mounts)}")
    print("SOURCE_OVERLAY=false")
    print("NETWORK_ENABLED=false")
    print("TEST_DATASET_ACCESS=false")
    print("PUBLICATION_PERMITTED=false")
    print("DOCKER_BUILD_INVOKED=false")
    print("AUTOMATIC_RETRY_PERMITTED=false")

    # Authorization-consumption boundary.  Never remove this directory/claim
    # on subsequent failure and never retry automatically.
    output_root.mkdir(parents=False, exist_ok=False)
    host_claim = ScientificHostClaim.create(request, authorization)
    claim_path = output_root / "host-claim.json"
    _write_exclusive(claim_path, host_claim.canonical_json().encode("utf-8"))
    print("=== SCIENTIFIC AUTHORIZATION CONSUMED BY HOST CLAIM ===")
    print(f"HOST_CLAIM_SHA256={host_claim.claim_sha256}")
    print("AUTHORIZATION_CONSUMED=true")
    print("DOCKER_RUN_MAX_COUNT=1")

    command = _docker_command(
        docker,
        root,
        request_path,
        authorization_path,
        request,
        host_claim,
        input_mounts,
        output_root,
    )
    invoked = _run(command, cwd=root)
    output = invoked.stdout.decode("utf-8", errors="replace")
    if output:
        print(output, end="" if output.endswith("\n") else "\n")
    print(f"DOCKER_RUN_STATUS={invoked.returncode}")
    if invoked.returncode != 0:
        raise ScientificHostLaunchError(
            "single scientific Docker invocation failed; authorization remains consumed"
        )
    print("FINAL_STATUS=0")
    print("SCIENTIFIC_DOCKER_INVOCATION_COMPLETED=true")
    print("AUTOMATIC_RETRY_PERMITTED=false")


if __name__ == "__main__":
    main()
