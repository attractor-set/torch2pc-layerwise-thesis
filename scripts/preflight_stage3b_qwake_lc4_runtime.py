#!/usr/bin/env python3
"""Materialize a deny-all QW-LC4 runtime preflight without model execution."""

from __future__ import annotations

import argparse
from pathlib import Path

from torch2pc_thesis.stage3b_qwake_lc4_runtime_freeze import (
    build_runtime_preflight,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--torch2pc-dir", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--torch2pc-commit", required=True)
    parser.add_argument("--image-digest", required=True)
    parser.add_argument("--image-repo-digest", required=True)
    parser.add_argument("--captured-at-utc", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    output = args.output.expanduser().resolve()
    if output.exists() or output.is_symlink():
        raise SystemExit(f"refusing to overwrite preflight output: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    preflight = build_runtime_preflight(
        args.project_root,
        args.torch2pc_dir,
        source_commit=args.source_commit,
        torch2pc_commit=args.torch2pc_commit,
        image_digest=args.image_digest,
        image_repo_digest=args.image_repo_digest,
        captured_at_utc=args.captured_at_utc,
    )
    output.write_text(preflight.canonical_json(), encoding="utf-8")
    print(f"PREFLIGHT={output}")
    print(f"PREFLIGHT_SHA256={preflight.preflight_sha256}")
    print("RUNTIME_EXECUTION_PERFORMED=false")
    print("SCIENTIFIC_EXECUTION_OPEN=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
