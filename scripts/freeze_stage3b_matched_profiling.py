#!/usr/bin/env python3
"""Freeze or verify the Stage 3B B0/B1/B2 matched-profiling opening."""

from __future__ import annotations

import argparse
from pathlib import Path

from torch2pc_thesis.stage3b_matched_profiling import (
    build_matched_manifest,
    build_matched_request,
    compare_json_file,
    load_json_object,
    write_matched_artifacts,
)

DEFAULT_BASE_MANIFEST = Path(
    "experiments/planned/STAGE3B-EXECUTION-MANIFEST.json"
)
DEFAULT_B1_CONTRACT = Path("experiments/planned/STAGE3B-B1-CONTRACT.json")
DEFAULT_B2_CONTRACT = Path("experiments/planned/STAGE3B-B2-CONTRACT.json")
DEFAULT_B1_DECISION = Path(
    "results/stage-3/b1/stage3b-b1-smoke-attempt-001/decision.json"
)
DEFAULT_B2_DECISION = Path(
    "results/stage-3/b2/stage3b-b2-smoke-attempt-001/decision.json"
)
DEFAULT_MATCHED_MANIFEST = Path(
    "experiments/planned/STAGE3B-B1-B2-MATCHED-PROFILING-MANIFEST.json"
)
DEFAULT_MATCHED_REQUEST = Path(
    "experiments/planned/STAGE3B-B1-B2-MATCHED-PROFILING-REQUEST.json"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--base-manifest", type=Path, default=DEFAULT_BASE_MANIFEST)
    parser.add_argument("--b1-contract", type=Path, default=DEFAULT_B1_CONTRACT)
    parser.add_argument("--b2-contract", type=Path, default=DEFAULT_B2_CONTRACT)
    parser.add_argument("--b1-decision", type=Path, default=DEFAULT_B1_DECISION)
    parser.add_argument("--b2-decision", type=Path, default=DEFAULT_B2_DECISION)
    parser.add_argument("--matched-manifest", type=Path, default=DEFAULT_MATCHED_MANIFEST)
    parser.add_argument("--matched-request", type=Path, default=DEFAULT_MATCHED_REQUEST)
    return parser.parse_args()


def _resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def main() -> int:
    args = parse_args()
    project_root = args.project_root.expanduser().resolve()

    base_manifest_path = _resolve(project_root, args.base_manifest)
    b1_contract_path = _resolve(project_root, args.b1_contract)
    b2_contract_path = _resolve(project_root, args.b2_contract)
    b1_decision_path = _resolve(project_root, args.b1_decision)
    b2_decision_path = _resolve(project_root, args.b2_decision)
    matched_manifest_path = _resolve(project_root, args.matched_manifest)
    matched_request_path = _resolve(project_root, args.matched_request)

    base_manifest = load_json_object(base_manifest_path)
    b1_contract = load_json_object(b1_contract_path)
    b2_contract = load_json_object(b2_contract_path)
    b1_decision = load_json_object(b1_decision_path)
    b2_decision = load_json_object(b2_decision_path)

    matched_manifest = build_matched_manifest(
        base_manifest,
        b1_contract,
        b2_contract,
    )
    matched_request = build_matched_request(
        project_root=project_root,
        base_manifest_path=base_manifest_path,
        b1_contract_path=b1_contract_path,
        b2_contract_path=b2_contract_path,
        b1_decision_path=b1_decision_path,
        b2_decision_path=b2_decision_path,
        matched_manifest_path=matched_manifest_path,
        base_manifest=base_manifest,
        b1_contract=b1_contract,
        b2_contract=b2_contract,
        b1_decision=b1_decision,
        b2_decision=b2_decision,
        matched_manifest=matched_manifest,
    )

    if args.write:
        write_matched_artifacts(
            manifest_path=matched_manifest_path,
            request_path=matched_request_path,
            manifest=matched_manifest,
            request=matched_request,
        )
        action = "written"
    else:
        compare_json_file(matched_manifest_path, matched_manifest)
        compare_json_file(matched_request_path, matched_request)
        action = "verified"

    print(f"ACTION={action}")
    print(f"MANIFEST={matched_manifest_path}")
    print(f"MANIFEST_DIGEST={matched_manifest['manifest_digest']}")
    print(f"REQUEST={matched_request_path}")
    print(f"REQUEST_DIGEST={matched_request['request_digest']}")
    print(f"SELECTED_CELLS={matched_manifest['selected_cell_count']}")
    print("SCIENTIFIC_ADMISSION=open")
    print("RUNTIME_AUTHORIZATION=not_issued")
    print("MEASUREMENTS_ALLOWED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
