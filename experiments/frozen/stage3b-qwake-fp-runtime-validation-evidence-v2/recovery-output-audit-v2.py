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

output = Path(output_arg)
inputs = Path("/authorization")

expected_inventory = {
    "SHA256SUMS",
    "authorization.json",
    "pre-freeze-projection.txt",
    "preflight.json",
    "runtime-validation-report.json",
    "static-validation-receipt",
}
actual_inventory = {
    p.name for p in output.iterdir() if p.is_file()
}
if actual_inventory != expected_inventory:
    raise RuntimeError("sealed output inventory differs")

out_preflight_p = output / "preflight.json"
out_auth_p = output / "authorization.json"
report_p = output / "runtime-validation-report.json"
in_preflight_p = inputs / "preflight.json"
in_auth_p = inputs / "authorization.json"

out_preflight = load_preflight(out_preflight_p)
in_preflight = load_preflight(in_preflight_p)
out_auth = load_authorization(out_auth_p)
in_auth = load_authorization(in_auth_p)

def sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()

def canonical_sha(path: Path) -> str:
    value = json.loads(path.read_text(encoding="utf-8"))
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()

identity = out_preflight.source_identity
if identity.source_commit != source_commit:
    raise RuntimeError("source commit differs")
if identity.torch2pc_commit != torch2pc_commit:
    raise RuntimeError("Torch2PC commit differs")
if identity.image_digest != image_digest:
    raise RuntimeError("image digest differs")
if out_preflight.preflight_sha256 != preflight_sha256:
    raise RuntimeError("output preflight digest differs")
if in_preflight.preflight_sha256 != preflight_sha256:
    raise RuntimeError("input preflight digest differs")
if out_preflight != in_preflight:
    raise RuntimeError("input/output preflight models differ")
if out_preflight_p.read_bytes() != in_preflight_p.read_bytes():
    raise RuntimeError("input/output preflight bytes differ")

if out_auth.authorization_sha256 != authorization_sha256:
    raise RuntimeError("output authorization digest differs")
if in_auth.authorization_sha256 != authorization_sha256:
    raise RuntimeError("input authorization digest differs")
if out_auth != in_auth:
    raise RuntimeError("input/output authorization models differ")
if out_auth.preflight_sha256 != preflight_sha256:
    raise RuntimeError("authorization/preflight binding differs")
if out_auth.receipt_chain_sha256 != receipt_chain_sha256:
    raise RuntimeError("receipt chain differs")
if out_auth.execution_count != 1 or len(out_auth.cells) != 6:
    raise RuntimeError("authorization execution boundary differs")

in_json = json.loads(in_auth_p.read_text(encoding="utf-8"))
out_json = json.loads(out_auth_p.read_text(encoding="utf-8"))
if in_json != out_json:
    raise RuntimeError("authorization JSON values differ")
if canonical_sha(in_auth_p) != canonical_sha(out_auth_p):
    raise RuntimeError("canonical authorization digests differ")

if (
    output / "static-validation-receipt"
).read_bytes() != (
    inputs / "static-validation-receipt.json"
).read_bytes():
    raise RuntimeError("static receipt bytes differ")

report = json.loads(report_p.read_text(encoding="utf-8"))
expected_report = {
    "schema_version": 1,
    "report_id": "stage3b-qwake-fp-runtime-validation-report-v1",
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
for key, value in expected_report.items():
    if report.get(key) != value:
        raise RuntimeError(f"report differs for {key}")
if sha(report_p) != report_sha256:
    raise RuntimeError("report SHA-256 differs")

lanes = report.get("lanes")
if not isinstance(lanes, list) or len(lanes) != 2:
    raise RuntimeError("lane count differs")

expected_lanes = ("cpu_float64_engineering", "rocm_float32_canonical")
expected_pairs = ("P0", "P1", "P2")
count = 0

for lane, expected_lane in zip(lanes, expected_lanes):
    if lane.get("lane") != expected_lane:
        raise RuntimeError("lane identity differs")
    if lane.get("nested_observations_passed") is not True:
        raise RuntimeError("nested observation gate failed")
    cells = lane.get("cells")
    if not isinstance(cells, list) or len(cells) != 3:
        raise RuntimeError("cell count differs")
    if tuple(c.get("cell", {}).get("pair_id") for c in cells) != expected_pairs:
        raise RuntimeError("pair order differs")

    for item in cells:
        count += 1
        cell = item.get("cell", {})
        pair = item.get("pair_validation", {})
        if cell.get("lane") != expected_lane:
            raise RuntimeError("cell lane differs")
        if pair.get("lane") != expected_lane:
            raise RuntimeError("pair-validation lane differs")
        if pair.get("pair_id") != cell.get("pair_id"):
            raise RuntimeError("pair identity differs")
        if pair.get("passed") is not True:
            raise RuntimeError("matched pair failed")
        if pair.get("equality_mismatches") != []:
            raise RuntimeError("equality mismatch present")
        if pair.get("initial_state_equal") is not True:
            raise RuntimeError("initial state mismatch")
        if pair.get("rng_state_before_equal") is not True:
            raise RuntimeError("RNG state mismatch")
        if item.get("oracle_isolation_passed") is not True:
            raise RuntimeError("oracle isolation failed")
        audits = item.get("disabled_capability_audits", [])
        if any(a.get("passed") is not True for a in audits):
            raise RuntimeError("disabled-capability audit failed")

if count != 6:
    raise RuntimeError("total cell count differs")

projection = (
    output / "pre-freeze-projection.txt"
).read_text(encoding="utf-8")
if projection != (
    "schema_version=1\n"
    "image_freeze_eligible=true\n"
    "cpu_smoke_passed=true\n"
    "rocm_smoke_passed=true\n"
    "scientific_evidence=false\n"
):
    raise RuntimeError("pre-freeze projection differs")

lane_counts = Counter(c.lane.value for c in out_auth.cells)
pair_counts = Counter(c.pair_id.value for c in out_auth.cells)
if lane_counts != {
    "cpu_float64_engineering": 3,
    "rocm_float32_canonical": 3,
}:
    raise RuntimeError("authorization lane counts differ")
if pair_counts != {"P0": 2, "P1": 2, "P2": 2}:
    raise RuntimeError("authorization pair counts differ")

print("OK: independent recovery-v2 audit passed")
print(f"REPORT_SHA256={sha(report_p)}")
print(f"INPUT_AUTHORIZATION_RAW_SHA256={sha(in_auth_p)}")
print(f"OUTPUT_AUTHORIZATION_RAW_SHA256={sha(out_auth_p)}")
print(f"AUTHORIZATION_CANONICAL_JSON_SHA256={canonical_sha(in_auth_p)}")
print("AUTHORIZATION_JSON_VALUES_EQUAL=true")
print("AUTHORIZATION_MODELS_EQUAL=true")
print("AUTHORIZED_CELL_COUNT=6")
print("CPU_LANE_PASSED=true")
print("ROCM_LANE_PASSED=true")
print("ENGINEERING_EVIDENCE_PRESENT=true")
print("IMAGE_FREEZE_ELIGIBLE=true")
print("SCIENTIFIC_EVIDENCE=false")
print("PUBLICATION_PERMITTED=false")
print("RUNTIME_RERUN_PERFORMED=false")
