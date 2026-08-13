#!/usr/bin/env python3
"""Authoritative attempt-independent builder for QWake scientific images.

The builder derives runtime-manifest identity from manifest bytes, creates an
exact temporary Docker context containing only that closure plus the manifest,
bakes path+digest into immutable image metadata, and runs positive and stale-
manifest production-equivalence checks. It does not create a request or issue
scientific authorization.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from torch2pc_thesis.stage3b_qwake_scientific_identity_v2 import (
    ScientificRuntimeIdentity,
    runtime_identity_from_image_inspection,
    verify_runtime_manifest,
)

DEFAULT_RUNTIME_MANIFEST = Path(
    "experiments/runtime/stage3b-qwake-scientific-successor-v1/runtime-SHA256SUMS"
)


class ScientificImageBuildError(RuntimeError):
    pass


def _run(argv: list[str], *, cwd: Path) -> subprocess.CompletedProcess[bytes]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    source_root = cwd / "src"
    if source_root.is_dir():
        existing = env.get("PYTHONPATH")
        env["PYTHONPATH"] = (
            str(source_root)
            if not existing
            else str(source_root) + os.pathsep + existing
        )
    return subprocess.run(
        argv,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def _require(argv: list[str], *, cwd: Path, label: str) -> bytes:
    result = _run(argv, cwd=cwd)
    if result.returncode != 0:
        output = result.stdout.decode("utf-8", errors="replace")
        if output:
            print(output, end="" if output.endswith("\n") else "\n")
        raise ScientificImageBuildError(f"{label} failed with status {result.returncode}")
    return result.stdout


def _manifest_identity(root: Path, relative: Path) -> ScientificRuntimeIdentity:
    manifest = (root / relative).resolve()
    try:
        manifest.relative_to(root)
    except ValueError as exc:
        raise ScientificImageBuildError("runtime manifest escapes project root") from exc
    if not manifest.is_file() or manifest.is_symlink():
        raise ScientificImageBuildError("runtime manifest is absent")
    return ScientificRuntimeIdentity(
        relative_path=relative.as_posix(),
        sha256="sha256:" + hashlib.sha256(manifest.read_bytes()).hexdigest(),
    )


def _require_commit_bound_sources(
    root: Path,
    *,
    source_commit: str,
    identity: ScientificRuntimeIdentity,
    paths: tuple[str, ...],
) -> None:
    """Bind builder, manifest, and every copied source byte to exact Git HEAD."""

    if _require(["git", "rev-parse", "--show-toplevel"], cwd=root, label="git root").decode().strip() != str(root):
        raise ScientificImageBuildError("builder project root differs")
    observed_head = _require(
        ["git", "rev-parse", "HEAD"], cwd=root, label="git HEAD"
    ).decode().strip()
    if observed_head != source_commit:
        raise ScientificImageBuildError("builder source commit differs from HEAD")

    builder_relative = Path(__file__).resolve().relative_to(root).as_posix()
    bound_paths = tuple(sorted(set(paths) | {identity.relative_path, builder_relative}))
    tracked = _run(
        ["git", "ls-files", "--error-unmatch", "--", *bound_paths],
        cwd=root,
    )
    if tracked.returncode != 0:
        raise ScientificImageBuildError("builder/runtime source closure contains untracked paths")
    dirty = _run(
        ["git", "diff", "--name-only", source_commit, "--", *bound_paths],
        cwd=root,
    )
    if dirty.returncode != 0:
        raise ScientificImageBuildError("builder/runtime source closure Git diff failed")
    if dirty.stdout.strip():
        raise ScientificImageBuildError(
            "builder/runtime source closure differs from source commit: "
            + dirty.stdout.decode("utf-8", errors="replace").strip()
        )


def _materialize_context(
    source_root: Path,
    context_root: Path,
    identity: ScientificRuntimeIdentity,
    paths: tuple[str, ...],
) -> None:
    for relative in paths + (identity.relative_path,):
        source = source_root / relative
        target = context_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--image-tag", required=True)
    parser.add_argument("--runtime-manifest", type=Path, default=DEFAULT_RUNTIME_MANIFEST)
    parser.add_argument(
        "--base-image",
        default="rocm/pytorch@sha256:96a2fb24dec9896e2f8238178f0c49d0dcc4c7dcc597be09e4564316bd86d191",
    )
    args = parser.parse_args()

    root = args.project_root.expanduser().resolve()
    if re.fullmatch(r"[0-9a-f]{40}", args.source_commit) is None:
        raise ScientificImageBuildError("source commit must be exact")
    if re.fullmatch(r"[^@\s]+@sha256:[0-9a-f]{64}", args.base_image) is None:
        raise ScientificImageBuildError("base image must be pinned by repository digest")
    identity = _manifest_identity(root, args.runtime_manifest)
    paths = verify_runtime_manifest(root, identity)
    _require_commit_bound_sources(
        root,
        source_commit=args.source_commit,
        identity=identity,
        paths=paths,
    )

    docker = shutil.which("docker")
    if docker is None:
        raise ScientificImageBuildError("docker executable is unavailable")

    with tempfile.TemporaryDirectory(prefix="qwake-scientific-context-") as raw_context:
        context = Path(raw_context)
        _materialize_context(root, context, identity, paths)
        _require(
            [
                sys.executable,
                "scripts/verify_stage3b_qwake_scientific_build_context_v2.py",
                "--project-root",
                str(context),
                "--runtime-manifest-relative",
                identity.relative_path,
                "--runtime-manifest-sha256",
                identity.sha256,
            ],
            cwd=context,
            label="exact build-context verification",
        )
        _require(
            [
                docker,
                "build",
                "--file",
                "Dockerfile.qwake-scientific",
                "--pull=false",
                "--build-arg",
                f"BASE_IMAGE={args.base_image}",
                "--build-arg",
                f"SOURCE_GIT_COMMIT={args.source_commit}",
                "--build-arg",
                f"QWAKE_RUNTIME_MANIFEST_RELATIVE={identity.relative_path}",
                "--build-arg",
                f"QWAKE_RUNTIME_MANIFEST_SHA256={identity.sha256}",
                "--tag",
                args.image_tag,
                ".",
            ],
            cwd=context,
            label="scientific image build",
        )

    inspected_raw = _require(
        [docker, "image", "inspect", args.image_tag],
        cwd=root,
        label="scientific image inspection",
    )
    inspected = json.loads(inspected_raw.decode("utf-8", errors="strict"))
    if not isinstance(inspected, list) or len(inspected) != 1 or not isinstance(inspected[0], dict):
        raise ScientificImageBuildError("scientific image inspection cardinality differs")
    image_id = inspected[0].get("Id")
    if not isinstance(image_id, str):
        raise ScientificImageBuildError("scientific image ID is absent")
    observed_identity = runtime_identity_from_image_inspection(
        inspected[0],
        expected_image_digest=image_id,
        expected_source_commit=args.source_commit,
        expected_code_manifest_sha256=identity.sha256,
    )
    if observed_identity != identity:
        raise ScientificImageBuildError("built image runtime identity differs")

    positive = _run(
        [
            docker,
            "run",
            "--rm",
            "--network=none",
            "--read-only",
            image_id,
            "python",
            "/workspace/scripts/verify_stage3b_qwake_scientific_runtime_identity_v2.py",
        ],
        cwd=root,
    )
    if positive.returncode != 0:
        raise ScientificImageBuildError("in-image runtime identity preflight failed")

    stale_digest = "sha256:" + "0" * 64
    negative = _run(
        [
            docker,
            "run",
            "--rm",
            "--network=none",
            "--read-only",
            "--env",
            f"QWAKE_RUNTIME_MANIFEST_SHA256={stale_digest}",
            image_id,
            "python",
            "/workspace/scripts/verify_stage3b_qwake_scientific_runtime_identity_v2.py",
        ],
        cwd=root,
    )
    if negative.returncode == 0:
        raise ScientificImageBuildError("stale-manifest negative preflight unexpectedly passed")

    print("QWAKE_SCIENTIFIC_IMAGE_BUILD=PASS")
    print(f"IMAGE_DIGEST={image_id}")
    print(f"SOURCE_COMMIT={args.source_commit}")
    print(f"RUNTIME_MANIFEST_RELATIVE={identity.relative_path}")
    print(f"RUNTIME_MANIFEST_SHA256={identity.sha256}")
    print(f"RUNTIME_PATH_COUNT={len(paths)}")
    print("PRODUCTION_EQUIVALENCE_PREFLIGHT=PASS")
    print("STALE_MANIFEST_NEGATIVE=PASS")
    print("REQUEST_FROZEN=false")
    print("SCIENTIFIC_AUTHORIZATION_ISSUED=false")
    print("SCIENTIFIC_EXECUTION_PERFORMED=false")


if __name__ == "__main__":
    main()
