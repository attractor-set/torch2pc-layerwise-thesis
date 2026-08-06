#!/usr/bin/env python3
"""Verify exact committed attempt-003 sources before any image build."""

from __future__ import annotations

import argparse
from pathlib import Path

from torch2pc_thesis.stage3b_qwake_attempt_003_source_closure import (
    RUNTIME_REGISTRY,
    build_closure_report,
    verify_commit_registry,
    verify_dockerfile_gate,
    verify_dockerignore_closure,
    write_report_no_replace,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--report", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = args.project_root.expanduser().resolve()
    entries = verify_commit_registry(root, args.source_commit)
    verify_dockerignore_closure(root / ".dockerignore")
    verify_dockerfile_gate(root / "Dockerfile.rocm")
    registry_raw = (root / RUNTIME_REGISTRY).read_bytes()
    dockerignore_raw = (root / ".dockerignore").read_bytes()
    report = build_closure_report(
        source_commit=args.source_commit,
        registry_raw=registry_raw,
        dockerignore_raw=dockerignore_raw,
        entries=entries,
    )
    write_report_no_replace(args.report, report)
    print("ATTEMPT_003_PREBUILD_SOURCE_CLOSURE_VERIFIED=true")
    print("GIT_OBJECT_PRESENCE_EXACT=true")
    print("COMMITTED_BLOB_HASHES_EXACT=true")
    print("DOCKER_CONTEXT_INCLUSION_EXACT=true")
    print("DOCKER_BUILD_INVOKED=false")
    print("RUNTIME_INVOKED=false")


if __name__ == "__main__":
    main()
