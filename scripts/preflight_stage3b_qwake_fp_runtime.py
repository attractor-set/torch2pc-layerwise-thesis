#!/usr/bin/env python3
"""Build or verify the non-computational QW-4B runtime preflight."""

from __future__ import annotations

import argparse
from pathlib import Path

from torch2pc_thesis.stage3b_qwake_fp_runtime import (
    build_runtime_preflight,
    load_preflight,
    validate_runtime_preflight,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--torch2pc-dir", type=Path, default=Path("external/Torch2PC"))
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--torch2pc-commit", required=True)
    parser.add_argument("--image-digest", required=True)
    parser.add_argument("--captured-at-utc")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--verify", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = args.project_root.resolve()
    torch2pc_dir = args.torch2pc_dir.resolve()
    if args.verify is not None:
        preflight = load_preflight(args.verify)
        validate_runtime_preflight(preflight, project_root, torch2pc_dir)
        print("OK: QW-4B runtime preflight verified")
        print(f"PREFLIGHT_SHA256={preflight.preflight_sha256}")
        return
    if args.captured_at_utc is None or args.output is None:
        raise SystemExit(
            "--captured-at-utc and --output are required when building"
        )
    output = args.output.resolve()
    if output.exists():
        raise SystemExit(f"refusing to overwrite existing preflight: {output}")
    preflight = build_runtime_preflight(
        project_root,
        torch2pc_dir,
        source_commit=args.source_commit,
        torch2pc_commit=args.torch2pc_commit,
        image_digest=args.image_digest,
        captured_at_utc=args.captured_at_utc,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(preflight.canonical_json(), encoding="utf-8")
    print("OK: QW-4B runtime preflight written")
    print(f"OUTPUT={output}")
    print(f"PREFLIGHT_SHA256={preflight.preflight_sha256}")
    print("EXECUTION_AUTHORIZATION_PRESENT=false")
    print("RUNTIME_VALIDATION_PERMITTED=false")


if __name__ == "__main__":
    main()
