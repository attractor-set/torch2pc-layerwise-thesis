"""Internal one-cell child process for matched Stage 3B execution."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import cast

from torch2pc_thesis.stage3b_execution import load_manifest
from torch2pc_thesis.stage3b_matched_execution import (
    execute_matched_cell,
    verify_matched_authorized_lane,
)


def _load_json_object(path: Path) -> dict[str, object]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return cast(dict[str, object], raw)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument("--matched-manifest", type=Path, required=True)
    parser.add_argument("--opening-request", type=Path, required=True)
    parser.add_argument("--base-manifest", type=Path, required=True)
    parser.add_argument("--base-manifest-path", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--cell-id", required=True)
    parser.add_argument("--device", required=True, choices=("rocm",))
    parser.add_argument("--dtype", required=True, choices=("float32",))
    parser.add_argument("--torch2pc-dir", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--image-digest", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    authorization = _load_json_object(args.authorization)
    matched_manifest = _load_json_object(args.matched_manifest)
    opening_request = _load_json_object(args.opening_request)
    base_manifest = load_manifest(args.base_manifest)
    try:
        verify_matched_authorized_lane(
            authorization,
            matched_manifest,
            opening_request,
            base_manifest,
            base_manifest_path=args.base_manifest_path,
            project_root=args.project_root,
            torch2pc_dir=args.torch2pc_dir,
            output_root=args.output_root,
            source_commit=args.source_commit,
            device=args.device,
            dtype=args.dtype,
            image_digest=args.image_digest,
        )
        terminal = execute_matched_cell(
            matched_manifest,
            opening_request,
            base_manifest,
            authorization,
            output_root=args.output_root,
            cell_id=args.cell_id,
            device=args.device,
            dtype=args.dtype,
            project_root=args.project_root,
            base_manifest_path=args.base_manifest_path,
            torch2pc_dir=args.torch2pc_dir,
            source_commit=args.source_commit,
            image_digest=args.image_digest,
        )
    except Exception as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(terminal, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
