#!/usr/bin/env python3
"""Verify the exact minimal QWake scientific Docker build context.

This tool is attempt-independent.  It performs no Docker operation and no
scientific execution; it verifies only the active runtime-manifest identity and
that the physical build context contains no files outside the bound closure.
"""

from __future__ import annotations

import argparse
import stat
from pathlib import Path

from torch2pc_thesis.stage3b_qwake_scientific_identity_v2 import (
    ScientificRuntimeIdentity,
    verify_runtime_manifest,
)

_REQUIRED_DIRECTORY_MODE = 0o755


def _require_deterministic_directory_modes(root: Path) -> int:
    directories = [root]
    directories.extend(path for path in root.rglob("*") if path.is_dir() and not path.is_symlink())
    invalid: list[str] = []
    for directory in sorted(directories, key=lambda path: path.as_posix()):
        mode = stat.S_IMODE(directory.stat().st_mode)
        if mode != _REQUIRED_DIRECTORY_MODE:
            relative = "." if directory == root else directory.relative_to(root).as_posix()
            invalid.append(f"{relative}:{oct(mode)}")
    if invalid:
        raise RuntimeError(
            "QWake build-context directory modes are not deterministic/non-root traversable: "
            + ", ".join(invalid)
        )
    return len(directories)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--runtime-manifest-relative", required=True)
    parser.add_argument("--runtime-manifest-sha256", required=True)
    args = parser.parse_args()

    root = args.project_root.expanduser().resolve()
    identity = ScientificRuntimeIdentity(
        relative_path=args.runtime_manifest_relative,
        sha256=args.runtime_manifest_sha256,
    )
    paths = verify_runtime_manifest(
        root,
        identity,
        exact_inventory_root=root,
    )
    directory_count = _require_deterministic_directory_modes(root)
    print("QWAKE_SCIENTIFIC_BUILD_CONTEXT=PASS")
    print(f"RUNTIME_MANIFEST_RELATIVE={identity.relative_path}")
    print(f"RUNTIME_MANIFEST_SHA256={identity.sha256}")
    print(f"RUNTIME_PATH_COUNT={len(paths)}")
    print(f"BUILD_CONTEXT_DIRECTORY_COUNT={directory_count}")
    print("BUILD_CONTEXT_DIRECTORY_MODE=0o755")
    print("BUILD_CONTEXT_NON_ROOT_TRAVERSAL_CONTRACT=PASS")
    print("EXTRA_BUILD_CONTEXT_FILE_COUNT=0")


if __name__ == "__main__":
    main()
