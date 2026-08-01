#!/usr/bin/env python3
"""Invoke one canonical acknowledgement-materialization operation."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_callsite_implementation import (
    canonical_verified_operation_result_json,
    load_canonical_prospective_operation,
)
from torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_implementation import (
    perform_final_execution_acknowledgement_materialization_invocation_operation,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Perform one explicitly authorized final acknowledgement-"
            "materialization operation."
        )
    )
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--operation-json", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        project_root = args.project_root.expanduser().resolve(strict=True)
        operation = load_canonical_prospective_operation(
            project_root,
            args.operation_json,
        )
        result = perform_final_execution_acknowledgement_materialization_invocation_operation(
            project_root,
            operation,
        )
        output = canonical_verified_operation_result_json(result)
    except Exception as exc:
        sys.stderr.write(f"ERROR: {exc}\n")
        return 1
    sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
