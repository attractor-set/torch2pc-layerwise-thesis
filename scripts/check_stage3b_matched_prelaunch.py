#!/usr/bin/env python3
"""Fail-closed scientific prelaunch gate for the Stage 3B 288-cell lane."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from torch2pc_thesis.stage3b_matched_profiling import (
    MatchedProfilingError,
    load_json_object,
    validate_matched_prelaunch_scientific_gate,
)

DEFAULT_MANIFEST = Path(
    "experiments/frozen/stage3b-matched-profiling-v2/manifest.json"
)
DEFAULT_REQUEST = Path(
    "experiments/frozen/stage3b-matched-profiling-v2/request.json"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--request", type=Path, default=DEFAULT_REQUEST)
    return parser.parse_args()


def _resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def main() -> int:
    args = parse_args()
    root = args.project_root.expanduser().resolve()
    manifest = load_json_object(_resolve(root, args.manifest))
    request = load_json_object(_resolve(root, args.request))
    try:
        report = validate_matched_prelaunch_scientific_gate(
            manifest,
            request,
            project_root=root,
        )
    except MatchedProfilingError as error:
        print(
            json.dumps(
                {
                    "status": "blocked",
                    "reason": str(error),
                },
                indent=2,
                sort_keys=True,
            )
        )
        print("SCIENTIFIC_PRELAUNCH_GATE=blocked")
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    print("SCIENTIFIC_PRELAUNCH_GATE=pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
