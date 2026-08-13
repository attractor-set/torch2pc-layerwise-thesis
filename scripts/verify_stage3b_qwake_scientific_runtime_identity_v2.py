#!/usr/bin/env python3
"""Read-only production-equivalence check for image-bound QWake identity."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from torch2pc_thesis.stage3b_qwake_scientific_identity_v2 import (
    runtime_identity_from_environment,
    verify_runtime_manifest,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path("/workspace"))
    args = parser.parse_args()

    root = args.project_root.expanduser().resolve()
    identity = runtime_identity_from_environment(os.environ)
    paths = verify_runtime_manifest(root, identity)
    print("QWAKE_RUNTIME_IDENTITY_PREFLIGHT=PASS")
    print(f"RUNTIME_MANIFEST_RELATIVE={identity.relative_path}")
    print(f"RUNTIME_MANIFEST_SHA256={identity.sha256}")
    print(f"RUNTIME_PATH_COUNT={len(paths)}")


if __name__ == "__main__":
    main()
