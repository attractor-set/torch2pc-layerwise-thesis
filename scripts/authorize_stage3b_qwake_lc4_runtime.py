#!/usr/bin/env python3
"""Issue the exact single-attempt QW-LC4 engineering authorization."""

from __future__ import annotations

import argparse
from pathlib import Path

from torch2pc_thesis.stage3b_qwake_lc4_runtime_freeze import (
    RUNTIME_OUTPUT_ROOT,
    build_runtime_authorization,
    load_runtime_preflight,
    validate_runtime_preflight,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--torch2pc-dir", type=Path, required=True)
    parser.add_argument("--preflight", type=Path, required=True)
    parser.add_argument("--issued-at-utc", required=True)
    parser.add_argument("--operator-acknowledgement", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    project_root = args.project_root.expanduser().resolve()
    output = args.output.expanduser().resolve()
    if output.exists() or output.is_symlink():
        raise SystemExit(f"refusing to overwrite authorization output: {output}")
    preflight = load_runtime_preflight(args.preflight)
    validate_runtime_preflight(
        preflight,
        project_root,
        args.torch2pc_dir,
    )
    output_root_absent = not (project_root / RUNTIME_OUTPUT_ROOT).exists()
    authorization = build_runtime_authorization(
        preflight,
        issued_at_utc=args.issued_at_utc,
        operator_acknowledgement=args.operator_acknowledgement,
        output_root_absent_at_issue=output_root_absent,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(authorization.canonical_json(), encoding="utf-8")
    print(f"AUTHORIZATION={output}")
    print(f"AUTHORIZATION_SHA256={authorization.authorization_sha256}")
    print(f"AUTHORIZED_CELL_COUNT={len(authorization.cells)}")
    print("RUNTIME_EXECUTION_PERFORMED=false")
    print("SCIENTIFIC_EXECUTION_OPEN=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
