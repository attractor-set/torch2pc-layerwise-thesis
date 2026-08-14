#!/usr/bin/env python3
"""Read-only production-equivalence check for image-bound QWake identity."""

from __future__ import annotations

import argparse
import os
import runpy
from pathlib import Path

from torch2pc_thesis.stage3b_qwake_scientific_identity_v2 import (
    runtime_identity_from_environment,
    verify_runtime_manifest,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path("/workspace"))
    parser.add_argument("--require-non-root", action="store_true")
    args = parser.parse_args()

    if args.require_non_root and os.geteuid() == 0:
        raise RuntimeError("production-equivalence preflight unexpectedly runs as root")

    root = args.project_root.expanduser().resolve()
    identity = runtime_identity_from_environment(os.environ)
    paths = verify_runtime_manifest(root, identity)
    entrypoint = root / "scripts/run_stage3b_qwake_scientific_campaign_v2.py"
    loaded = runpy.run_path(
        str(entrypoint),
        run_name="qwake_scientific_production_preflight",
    )
    if not callable(loaded.get("main")):
        raise RuntimeError("production scientific entrypoint main is unavailable")
    print("QWAKE_RUNTIME_IDENTITY_PREFLIGHT=PASS")
    print("QWAKE_PRODUCTION_ENTRYPOINT_IMPORT_PREFLIGHT=PASS")
    print(f"QWAKE_PRODUCTION_PREFLIGHT_UID={os.geteuid()}")
    print(f"QWAKE_PRODUCTION_PREFLIGHT_GID={os.getegid()}")
    if args.require_non_root:
        print("QWAKE_NON_ROOT_EXECUTION_PRINCIPAL=PASS")
    print(f"RUNTIME_MANIFEST_RELATIVE={identity.relative_path}")
    print(f"RUNTIME_MANIFEST_SHA256={identity.sha256}")
    print(f"RUNTIME_PATH_COUNT={len(paths)}")


if __name__ == "__main__":
    main()
