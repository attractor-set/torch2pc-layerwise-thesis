#!/usr/bin/env python3
"""Execute one already-frozen QW-4B engineering authorization."""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
from pathlib import Path

from torch2pc_thesis.stage3b_qwake_fp_runtime import (
    build_engineering_report,
    build_lane_report,
    execute_matched_cell,
    load_authorization,
    load_preflight,
    open_runtime_session,
    seal_engineering_report,
    to_pre_freeze_validation_report,
    verify_static_validation_receipt,
)
from torch2pc_thesis.stage3b_qwake_fp_runtime_torch import (
    TorchFixedPredEngineeringBackend,
)
from torch2pc_thesis.stage3b_qwake_fp_validation import ValidationLane


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument(
        "--torch2pc-dir",
        type=Path,
        default=Path("external/Torch2PC"),
    )
    parser.add_argument("--preflight", type=Path, required=True)
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument(
        "--static-validation-receipt",
        type=Path,
        required=True,
    )
    return parser.parse_args()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _write_atomic(
    output_root: Path,
    files: dict[str, bytes],
    authorization_sha256: str,
) -> None:
    temporary = output_root.with_name(
        f".{output_root.name}.tmp-{authorization_sha256[-12:]}"
    )
    if output_root.exists() or temporary.exists():
        raise RuntimeError("authorized output or temporary root already exists")
    temporary.mkdir(parents=True)
    try:
        sums: list[str] = []
        for relative, content in sorted(files.items()):
            target = temporary / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
            sums.append(f"{_sha256_bytes(content)}  {relative}\n")
        sums_bytes = "".join(sums).encode("utf-8")
        (temporary / "SHA256SUMS").write_bytes(sums_bytes)
        os.replace(temporary, output_root)
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def main() -> None:
    args = parse_args()
    project_root = args.project_root.expanduser().resolve()
    torch2pc_dir = args.torch2pc_dir.expanduser().resolve()
    preflight = load_preflight(args.preflight)
    authorization = load_authorization(args.authorization)
    verify_static_validation_receipt(
        authorization,
        args.static_validation_receipt,
    )
    session = open_runtime_session(
        preflight,
        authorization,
        project_root,
        torch2pc_dir,
    )

    results = []
    for cell in authorization.cells:
        backend = TorchFixedPredEngineeringBackend(
            cell=cell,
            torch2pc_dir=torch2pc_dir,
        )
        results.append(execute_matched_cell(session, backend, cell))
    lane_reports = tuple(
        build_lane_report(
            lane,
            tuple(item for item in results if item.cell.lane is lane),
        )
        for lane in ValidationLane
    )
    report = build_engineering_report(
        session,
        lane_reports,
        manifest_integrity_passed=True,
        receipt_chain_passed=True,
        static_and_unit_passed=True,
    )
    sealed = seal_engineering_report(report)
    projection = to_pre_freeze_validation_report(report)
    projection_text = (
        "schema_version=1\n"
        f"image_freeze_eligible={str(projection.image_freeze_eligible).lower()}\n"
        f"cpu_smoke_passed={str(projection.cpu_smoke_passed).lower()}\n"
        f"rocm_smoke_passed={str(projection.rocm_smoke_passed).lower()}\n"
        "scientific_evidence=false\n"
    )
    files = {
        "preflight.json": preflight.canonical_json().encode("utf-8"),
        "authorization.json": authorization.canonical_json().encode("utf-8"),
        "static-validation-receipt": args.static_validation_receipt.read_bytes(),
        "runtime-validation-report.json": sealed.canonical_json.encode("utf-8"),
        "pre-freeze-projection.txt": projection_text.encode("utf-8"),
    }
    _write_atomic(
        session.output_root,
        files,
        authorization.authorization_sha256,
    )
    print("OK: QW-4B engineering runtime validation sealed")
    print(f"OUTPUT_ROOT={session.output_root}")
    print(f"REPORT_SHA256={sealed.sha256}")
    print(f"IMAGE_FREEZE_ELIGIBLE={str(report.image_freeze_eligible).lower()}")
    print("SCIENTIFIC_EVIDENCE=false")
    print("PUBLICATION_PERMITTED=false")
    if not report.image_freeze_eligible:
        raise SystemExit(
            "ERROR: engineering report sealed but validation did not pass"
        )


if __name__ == "__main__":
    main()
