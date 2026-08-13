#!/usr/bin/env python3
"""Verify the exact minimal QWake scientific Docker build context.

This tool is attempt-independent.  It performs no Docker operation and no
scientific execution; it verifies only the active runtime-manifest identity and
that the physical build context contains no files outside the bound closure.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from torch2pc_thesis.stage3b_qwake_scientific_identity_v2 import (
    ScientificRuntimeIdentity,
    verify_runtime_manifest,
)


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
    print("QWAKE_SCIENTIFIC_BUILD_CONTEXT=PASS")
    print(f"RUNTIME_MANIFEST_RELATIVE={identity.relative_path}")
    print(f"RUNTIME_MANIFEST_SHA256={identity.sha256}")
    print(f"RUNTIME_PATH_COUNT={len(paths)}")
    print("EXTRA_BUILD_CONTEXT_FILE_COUNT=0")


if __name__ == "__main__":
    main()
