"""Internal one-cell child process for Stage 3B B0 canonical execution."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import cast

from torch2pc_thesis.stage3b_canonical import (
    execute_canonical_cell,
    verify_authorized_lane,
)
from torch2pc_thesis.stage3b_execution import load_manifest


def _load_json_object(path: Path) -> dict[str, object]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return cast(dict[str, object], raw)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--cell-id", required=True)
    parser.add_argument("--device", required=True, choices=("cpu", "rocm"))
    parser.add_argument("--dtype", required=True, choices=("float32", "float64"))
    parser.add_argument("--torch2pc-dir", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--image-digest", required=True)
    args = parser.parse_args()
    if (args.device, args.dtype) != ("rocm", "float32"):
        parser.error(
            "canonical B0 child is limited to --device rocm --dtype float32"
        )
    return args


def main() -> int:
    args = parse_args()
    authorization = _load_json_object(args.authorization)
    manifest = load_manifest(args.manifest)
    try:
        verify_authorized_lane(
            authorization,
            manifest,
            torch2pc_dir=args.torch2pc_dir,
            output_root=args.output_root,
            source_commit=args.source_commit,
            device=args.device,
            dtype=args.dtype,
            image_digest=args.image_digest,
        )
        terminal = execute_canonical_cell(
            manifest,
            authorization,
            output_root=args.output_root,
            cell_id=args.cell_id,
            device=args.device,
            dtype=args.dtype,
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
