from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

from torch2pc_thesis.stage3b_qwake_fp_runtime import (
    load_authorization,
    load_preflight,
)

(
    output_arg,
    source_commit,
    torch2pc_commit,
    image_digest,
    preflight_sha256,
    authorization_sha256,
    receipt_chain_sha256,
    report_sha256,
) = sys.argv[1:]

root = Path(output_arg)

expected_files = {
    "SHA256SUMS",
    "authorization.json",
    "pre-freeze-projection.txt",
    "preflight.json",
    "runtime-validation-report.json",
    "static-validation-receipt",
}
observed_files = {
    path.name
    for path in root.iterdir()
    if path.is_file()
}
if observed_files != expected_files:
    raise RuntimeError(
        "sealed output inventory differs: "
        f"{sorted(observed_files)}"
    )

preflight = load_preflight(root / "preflight.json")
authorization = load_authorization(
    root / "authorization.json"
)
report_path = root / "runtime-validation-report.json"
report = json.loads(
    report_path.read_text(
        encoding="utf-8",
        errors="strict",
    )
)
projection = (
    root / "pre-freeze-projection.txt"
).read_text(
    encoding="utf-8",
    errors="strict",
)

def sha(path: Path) -> str:
    return (
        "sha256:"
        + hashlib.sha256(path.read_bytes()).hexdigest()
    )

identity = preflight.source_identity
if identity.source_commit != source_commit:
    raise RuntimeError("output source commit differs")
if identity.torch2pc_commit != torch2pc_commit:
    raise RuntimeError("output Torch2PC commit differs")
if identity.image_digest != image_digest:
    raise RuntimeError("output image digest differs")
if preflight.preflight_sha256 != preflight_sha256:
    raise RuntimeError("output preflight digest differs")
if authorization.authorization_sha256 != authorization_sha256:
    raise RuntimeError("output authorization digest differs")
if authorization.preflight_sha256 != preflight_sha256:
    raise RuntimeError("authorization/preflight binding differs")
if authorization.receipt_chain_sha256 != receipt_chain_sha256:
    raise RuntimeError("authorization receipt chain differs")
if authorization.source_identity != identity:
    raise RuntimeError("authorization source identity differs")
if authorization.execution_count != 1:
    raise RuntimeError("authorization execution count differs")
if len(authorization.cells) != 6:
    raise RuntimeError("authorization cell count differs")

if (
    root / "static-validation-receipt"
).read_bytes() != Path(
    "/authorization/static-validation-receipt.json"
).read_bytes():
    raise RuntimeError(
        "static-validation receipt bytes differ"
    )

if (
    root / "preflight.json"
).read_bytes() != Path(
    "/authorization/preflight.json"
).read_bytes():
    raise RuntimeError("preflight bytes differ")

if (
    root / "authorization.json"
).read_bytes() != Path(
    "/authorization/authorization.json"
).read_bytes():
    raise RuntimeError("authorization bytes differ")

expected_report = {
    "schema_version": 1,
    "report_id": (
        "stage3b-qwake-fp-runtime-validation-report-v1"
    ),
    "status": "engineering_validation_sealed",
    "preflight_sha256": preflight_sha256,
    "authorization_sha256": authorization_sha256,
    "manifest_integrity_passed": True,
    "receipt_chain_passed": True,
    "static_and_unit_passed": True,
    "engineering_evidence_only": True,
    "scientific_evidence": False,
    "publication_permitted": False,
    "image_freeze_eligible": True,
}

for key, expected in expected_report.items():
    if report.get(key) != expected:
        raise RuntimeError(
            f"runtime report differs for {key}: "
            f"{report.get(key)!r}"
        )

if sha(report_path) != report_sha256:
    raise RuntimeError("runtime report SHA-256 differs")

lanes = report.get("lanes")
if not isinstance(lanes, list) or len(lanes) != 2:
    raise RuntimeError("runtime lane count differs")

expected_lanes = (
    "cpu_float64_engineering",
    "rocm_float32_canonical",
)
expected_pairs = ("P0", "P1", "P2")
observed_cell_count = 0

for lane, expected_lane in zip(lanes, expected_lanes):
    if lane.get("lane") != expected_lane:
        raise RuntimeError("runtime lane identity differs")
    if lane.get("nested_observations_passed") is not True:
        raise RuntimeError(
            f"nested observation gate failed: {expected_lane}"
        )

    cells = lane.get("cells")
    if not isinstance(cells, list) or len(cells) != 3:
        raise RuntimeError(
            f"runtime cell count differs: {expected_lane}"
        )

    observed_pairs = tuple(
        item.get("cell", {}).get("pair_id")
        for item in cells
    )
    if observed_pairs != expected_pairs:
        raise RuntimeError(
            f"runtime pair order differs: {observed_pairs}"
        )

    for item in cells:
        observed_cell_count += 1
        cell = item.get("cell", {})
        pair = item.get("pair_validation", {})

        if cell.get("lane") != expected_lane:
            raise RuntimeError("cell lane differs")
        if pair.get("lane") != expected_lane:
            raise RuntimeError("pair-validation lane differs")
        if pair.get("pair_id") != cell.get("pair_id"):
            raise RuntimeError("pair-validation identity differs")
        if pair.get("passed") is not True:
            raise RuntimeError("matched pair did not pass")
        if pair.get("equality_mismatches") != []:
            raise RuntimeError("equality mismatch present")
        if pair.get("initial_state_equal") is not True:
            raise RuntimeError("initial state did not match")
        if pair.get("rng_state_before_equal") is not True:
            raise RuntimeError("RNG state did not match")
        if item.get("oracle_isolation_passed") is not True:
            raise RuntimeError("oracle-isolation gate failed")

        audits = item.get(
            "disabled_capability_audits",
            [],
        )
        if not isinstance(audits, list):
            raise RuntimeError(
                "disabled-capability audit registry invalid"
            )
        if any(audit.get("passed") is not True for audit in audits):
            raise RuntimeError(
                "disabled-capability audit failed"
            )

if observed_cell_count != 6:
    raise RuntimeError("observed runtime cell count differs")

expected_projection = (
    "schema_version=1\n"
    "image_freeze_eligible=true\n"
    "cpu_smoke_passed=true\n"
    "rocm_smoke_passed=true\n"
    "scientific_evidence=false\n"
)
if projection != expected_projection:
    raise RuntimeError("pre-freeze projection differs")

lane_counts = Counter(
    cell.lane.value
    for cell in authorization.cells
)
pair_counts = Counter(
    cell.pair_id.value
    for cell in authorization.cells
)

if lane_counts != {
    "cpu_float64_engineering": 3,
    "rocm_float32_canonical": 3,
}:
    raise RuntimeError("authorization lane counts differ")
if pair_counts != {"P0": 2, "P1": 2, "P2": 2}:
    raise RuntimeError("authorization pair counts differ")

print("OK: independent recovery audit passed")
print(f"REPORT_SHA256={sha(report_path)}")
print("AUTHORIZED_CELL_COUNT=6")
print("CPU_LANE_PASSED=true")
print("ROCM_LANE_PASSED=true")
print("ENGINEERING_EVIDENCE_PRESENT=true")
print("IMAGE_FREEZE_ELIGIBLE=true")
print("SCIENTIFIC_EVIDENCE=false")
print("PUBLICATION_PERMITTED=false")
print("RUNTIME_RERUN_PERFORMED=false")
