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
    sha256_file,
    validate_matched_prelaunch_scientific_gate,
    write_matched_artifacts,
)

DEFAULT_BASE_MANIFEST = Path(
    "experiments/planned/STAGE3B-EXECUTION-MANIFEST.json"
)
DEFAULT_B1_CONTRACT = Path("experiments/planned/STAGE3B-B1-CONTRACT.json")
DEFAULT_B2_CONTRACT = Path("experiments/planned/STAGE3B-B2-CONTRACT.json")
DEFAULT_MATCHED_ROOT = Path("experiments/frozen/stage3b-matched-profiling-v2")
DEFAULT_MATCHED_MANIFEST = DEFAULT_MATCHED_ROOT / "manifest.json"
DEFAULT_MATCHED_REQUEST = DEFAULT_MATCHED_ROOT / "request.json"
DEFAULT_CHECKSUM_REGISTRY = DEFAULT_MATCHED_ROOT / "SHA256SUMS"
DEFAULT_HISTORICAL_MANIFEST = Path(
    "experiments/planned/STAGE3B-B1-B2-MATCHED-PROFILING-MANIFEST.json"
)
DEFAULT_HISTORICAL_REQUEST = Path(
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
    parser.add_argument(
        "--b1-admission",
        type=Path,
        default=Path(
            "results/stage-3/b1/stage3b-b1-confirmatory-ceebdce-v1/"
            "matched-profiling-admission.json"
        ),
        help="sealed confirmatory EQ-B1 admission (120/120 pairs)",
    )
    parser.add_argument(
        "--b2-admission",
        type=Path,
        default=Path(
            "results/stage-3/b2/stage3b-b2-confirmatory-63885e5-v1/"
            "matched-profiling-admission.json"
        ),
        help=(
            "sealed confirmatory EQ-B2 admission "
            "(120/120 triples, 240/240 comparisons)"
        ),
    )
    parser.add_argument("--matched-manifest", type=Path, default=DEFAULT_MATCHED_MANIFEST)
    parser.add_argument("--matched-request", type=Path, default=DEFAULT_MATCHED_REQUEST)
    parser.add_argument("--checksum-registry", type=Path, default=DEFAULT_CHECKSUM_REGISTRY)
    parser.add_argument(
        "--historical-manifest",
        type=Path,
        default=DEFAULT_HISTORICAL_MANIFEST,
    )
    parser.add_argument(
        "--historical-request",
        type=Path,
        default=DEFAULT_HISTORICAL_REQUEST,
    )
    return parser.parse_args()


def _resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def main() -> int:
    args = parse_args()
    project_root = args.project_root.expanduser().resolve()

    base_manifest_path = _resolve(project_root, args.base_manifest)
    b1_contract_path = _resolve(project_root, args.b1_contract)
    b2_contract_path = _resolve(project_root, args.b2_contract)
    b1_decision_path = _resolve(project_root, args.b1_admission)
    b2_decision_path = _resolve(project_root, args.b2_admission)
    matched_manifest_path = _resolve(project_root, args.matched_manifest)
    matched_request_path = _resolve(project_root, args.matched_request)
    checksum_registry_path = _resolve(project_root, args.checksum_registry)
    historical_manifest_path = _resolve(project_root, args.historical_manifest)
    historical_request_path = _resolve(project_root, args.historical_request)

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
        historical_request_path=historical_request_path,
        historical_manifest_path=historical_manifest_path,
        base_manifest=base_manifest,
        b1_contract=b1_contract,
        b2_contract=b2_contract,
        b1_decision=b1_decision,
        b2_decision=b2_decision,
        matched_manifest=matched_manifest,
    )

    prelaunch = validate_matched_prelaunch_scientific_gate(
        matched_manifest,
        matched_request,
        project_root=project_root,
    )

    if args.write:
        write_matched_artifacts(
            manifest_path=matched_manifest_path,
            request_path=matched_request_path,
            manifest=matched_manifest,
            request=matched_request,
        )
        registry = (
            f"{sha256_file(matched_manifest_path)}  manifest.json\n"
            f"{sha256_file(matched_request_path)}  request.json\n"
        )
        if checksum_registry_path.exists():
            if checksum_registry_path.read_text(encoding="utf-8") != registry:
                raise ValueError(
                    f"checksum registry differs from generated package: "
                    f"{checksum_registry_path}"
                )
        else:
            checksum_registry_path.parent.mkdir(parents=True, exist_ok=True)
            checksum_registry_path.write_text(registry, encoding="utf-8")
        action = "written"
    else:
        compare_json_file(matched_manifest_path, matched_manifest)
        compare_json_file(matched_request_path, matched_request)
        expected_registry = (
            f"{sha256_file(matched_manifest_path)}  manifest.json\n"
            f"{sha256_file(matched_request_path)}  request.json\n"
        )
        if checksum_registry_path.read_text(encoding="utf-8") != expected_registry:
            raise ValueError(
                f"checksum registry differs from generated package: "
                f"{checksum_registry_path}"
            )
        action = "verified"

    print(f"ACTION={action}")
    print(f"MANIFEST={matched_manifest_path}")
    print(f"MANIFEST_DIGEST={matched_manifest['manifest_digest']}")
    print(f"REQUEST={matched_request_path}")
    print(f"REQUEST_DIGEST={matched_request['request_digest']}")
    print(f"CHECKSUM_REGISTRY={checksum_registry_path}")
    print(f"SELECTED_CELLS={matched_manifest['selected_cell_count']}")
    print(f"SCIENTIFIC_PRELAUNCH_GATE={prelaunch['status']}")
    print("SCIENTIFIC_ADMISSION=open")
    print("RUNTIME_AUTHORIZATION=not_issued")
    print("MEASUREMENTS_ALLOWED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
