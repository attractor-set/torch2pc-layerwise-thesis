#!/usr/bin/env python3
"""Verify copied attempt-003 runtime sources during a future image build."""

from __future__ import annotations

import argparse
from pathlib import Path

from torch2pc_thesis.stage3b_qwake_attempt_003_source_closure import (
    verify_dockerfile_gate,
    verify_dockerignore_closure,
    verify_worktree_registry,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path("."))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = args.project_root.expanduser().resolve()
    verify_worktree_registry(root)
    verify_dockerignore_closure(root / ".dockerignore")
    verify_dockerfile_gate(root / "Dockerfile.rocm")
    print("ATTEMPT_003_BUILDTIME_SOURCE_CLOSURE_VERIFIED=true")
    print("RUNTIME_SOURCE_REGISTRY_EXACT=true")
    print("RUNTIME_EXECUTION_PERFORMED=false")
    print("MODEL_CODE_INVOKED=false")
    print("DATASET_ACCESSED=false")


if __name__ == "__main__":
    main()
