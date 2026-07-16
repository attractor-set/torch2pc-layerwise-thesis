#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

from torch2pc_thesis.stage3b_a1_mechanism_controls import (
    CONTRACT_ID,
    CONTROL_ID,
    IMPLEMENTATION_SCHEMA_ID,
    expected_counts,
)

OUTPUT_FILES = (
    "mechanism_geometry_records.csv",
    "mechanism_transport_records.csv",
    "mechanism_temporal_events.csv",
    "mechanism_temporal_summary.csv",
    "mechanism_block_probe_records.csv",
    "mechanism_pnz_records.csv",
    "mechanism_controls_contract.json",
    "mechanism_controls_summary.json",
)


def output(args: list[str], *, cwd: Path) -> str:
    return subprocess.check_output(
        args,
        cwd=cwd,
        text=True,
        stderr=subprocess.STDOUT,
    ).strip()


def read_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def inspect_image(image: str, *, cwd: Path) -> dict[str, Any]:
    raw = output(["docker", "image", "inspect", image], cwd=cwd)
    records = json.loads(raw)
    if not isinstance(records, list) or len(records) != 1:
        raise RuntimeError(f"Expected one Docker image record for {image!r}")
    record = records[0]
    if not isinstance(record, dict):
        raise TypeError("Docker image record must be an object")
    return record


def verify_controlled_image(repo: Path) -> tuple[str, str, str, str]:
    dotenv_path = repo / ".env"
    if not dotenv_path.is_file():
        raise RuntimeError("Missing .env; run `make init` first")
    head = output(["git", "rev-parse", "HEAD"], cwd=repo)
    branch = output(["git", "branch", "--show-current"], cwd=repo)
    if not re.fullmatch(r"[0-9a-f]{40}", head):
        raise RuntimeError("Unable to resolve the source commit")
    if not branch:
        raise RuntimeError("Controlled execution requires a named branch")
    if output(["git", "status", "--porcelain"], cwd=repo):
        raise RuntimeError(
            "Controlled mechanism execution requires a clean committed tree"
        )
    dotenv = read_dotenv(dotenv_path)
    image = dotenv.get("EXPERIMENT_IMAGE", "")
    env_commit = dotenv.get("SOURCE_GIT_COMMIT", "")
    if not image:
        raise RuntimeError("EXPERIMENT_IMAGE is missing from .env")
    if env_commit != head:
        raise RuntimeError(".env SOURCE_GIT_COMMIT does not match HEAD")
    image_info = inspect_image(image, cwd=repo)
    labels = image_info.get("Config", {}).get("Labels", {}) or {}
    image_revision = labels.get("org.opencontainers.image.revision")
    if image_revision != head:
        raise RuntimeError(
            "Controlled image revision differs from HEAD; rebuild the image"
        )
    return head, branch, image, str(image_revision)


def controlled_compose_environment(
    *,
    head: str,
    branch: str,
    image: str,
    image_revision: str,
) -> dict[str, str]:
    environment = os.environ.copy()
    environment["SOURCE_GIT_COMMIT"] = head
    environment["SOURCE_GIT_BRANCH"] = branch
    environment["EXPERIMENT_IMAGE"] = image
    environment["IMAGE_REVISION"] = image_revision
    return environment


def validate_output_dir(output_dir: Path) -> None:
    if output_dir.is_absolute() or ".." in output_dir.parts:
        raise ValueError("--output-dir must be repository-relative")
    if not output_dir.parts or output_dir.parts[0] != "results":
        raise ValueError("--output-dir must be under results/")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run deterministic mechanism controls in Docker."
    )
    parser.add_argument("device", choices=["cpu", "gpu"])
    parser.add_argument(
        "--execution-scope",
        choices=["smoke", "confirmatory"],
        default="smoke",
    )
    parser.add_argument("--output-dir", type=Path)
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def validate_records(
    rows: list[dict[str, str]],
    *,
    expected_count: int,
    expected_sub_gate: str,
    head: str,
    branch: str,
    image: str,
    image_revision: str,
) -> None:
    if len(rows) != expected_count:
        raise RuntimeError(
            f"Expected {expected_count} {expected_sub_gate} records, "
            f"observed {len(rows)}"
        )
    keys = [row.get("record_key", "") for row in rows]
    if any(not key for key in keys) or len(keys) != len(set(keys)):
        raise RuntimeError(f"{expected_sub_gate} record keys are invalid")
    for row in rows:
        if row.get("sub_gate") != expected_sub_gate:
            raise RuntimeError(f"Unexpected sub-gate in {expected_sub_gate} file")
        if row.get("contract_id") != CONTRACT_ID:
            raise RuntimeError("Mechanism record contract mismatch")
        if row.get("implementation_schema_id") != IMPLEMENTATION_SCHEMA_ID:
            raise RuntimeError("Mechanism record implementation-schema mismatch")
        if row.get("source_git_commit") != head:
            raise RuntimeError("Mechanism record source-commit mismatch")
        if row.get("source_git_branch") != branch:
            raise RuntimeError("Mechanism record source-branch mismatch")
        if row.get("experiment_image") != image:
            raise RuntimeError("Mechanism record image mismatch")
        if row.get("image_revision") != image_revision:
            raise RuntimeError("Mechanism record image-revision mismatch")
        if row.get("finite", "").lower() != "true":
            raise RuntimeError("Mechanism record contains a nonfinite value")
        if row.get("passed", "").lower() != "true":
            raise RuntimeError("Mechanism record contains a failed control")


def validate_summary(
    summary: dict[str, Any],
    *,
    scope: str,
    lane: str,
    head: str,
    branch: str,
    image: str,
    image_revision: str,
) -> None:
    if summary.get("control_id") != CONTROL_ID:
        raise RuntimeError("Mechanism summary control id mismatch")
    if summary.get("contract_id") != CONTRACT_ID:
        raise RuntimeError("Mechanism summary contract mismatch")
    if summary.get("implementation_schema_id") != IMPLEMENTATION_SCHEMA_ID:
        raise RuntimeError("Mechanism summary schema mismatch")
    if summary.get("scope") != scope or summary.get("lane") != lane:
        raise RuntimeError("Mechanism summary execution metadata mismatch")
    expected_provenance = {
        "source_git_commit": head,
        "source_git_branch": branch,
        "experiment_image": image,
        "image_revision": image_revision,
    }
    observed_provenance = {
        key: summary.get(key) for key in expected_provenance
    }
    if observed_provenance != expected_provenance:
        raise RuntimeError("Mechanism summary provenance mismatch")
    for field in (
        "geo_c0_passed",
        "tr_c0_passed",
        "tmp_c0_passed",
        "jac_c0_passed",
        "core_passed",
        "si_ma0_open",
        "passed",
    ):
        if summary.get(field) is not True:
            raise RuntimeError(f"Mechanism summary field is not passing: {field}")
    if summary.get("pnz_l0_passed") is not True:
        raise RuntimeError("PNZ-L0 limited extension failed")
    counts = expected_counts(scope)  # type: ignore[arg-type]
    if summary.get("expected_counts") != counts:
        raise RuntimeError("Mechanism expected-count metadata mismatch")
    if summary.get("observed_counts") != counts:
        raise RuntimeError("Mechanism observed-count metadata mismatch")


def main() -> None:
    args = parse_args()
    repo = Path(__file__).resolve().parents[1]
    head, branch, image, image_revision = verify_controlled_image(repo)
    lane = "rocm" if args.device == "gpu" else "cpu"
    service = "control-gpu" if args.device == "gpu" else "control-cpu"
    output_dir = args.output_dir or Path(
        "results/stage-3/a1-shortcut-observer-controls/working/"
        f"mechanism-controls-{args.device}-{args.execution_scope}"
    )
    validate_output_dir(output_dir)
    command = [
        "docker",
        "compose",
        "run",
        "--rm",
        "-e",
        "TORCH2PC_CONTROLLED_CONTAINER=1",
        "-e",
        f"TORCH2PC_EXECUTION_LANE={lane}",
        "-e",
        f"SOURCE_GIT_COMMIT={head}",
        "-e",
        f"SOURCE_GIT_BRANCH={branch}",
        "-e",
        f"EXPERIMENT_IMAGE={image}",
        "-e",
        f"IMAGE_REVISION={image_revision}",
        service,
        "python",
        "scripts/run_stage3b_a1_mechanism_controls.py",
        args.device,
        "--execution-scope",
        args.execution_scope,
        "--output-dir",
        str(output_dir),
    ]
    print(f"source_commit={head}")
    print(f"source_branch={branch}")
    print(f"experiment_image={image}")
    print(f"image_revision={image_revision}")
    print(f"execution_lane={lane}")
    subprocess.run(
        command,
        cwd=repo,
        check=True,
        env=controlled_compose_environment(
            head=head,
            branch=branch,
            image=image,
            image_revision=image_revision,
        ),
    )

    paths = {name: repo / output_dir / name for name in OUTPUT_FILES}
    for path in paths.values():
        if not path.is_file():
            raise RuntimeError(f"Mechanism output is missing: {path.name}")

    summary_value = json.loads(
        paths["mechanism_controls_summary.json"].read_text(encoding="utf-8")
    )
    if not isinstance(summary_value, dict):
        raise TypeError("Mechanism summary must be a JSON object")
    validate_summary(
        summary_value,
        scope=args.execution_scope,
        lane=lane,
        head=head,
        branch=branch,
        image=image,
        image_revision=image_revision,
    )
    counts = expected_counts(args.execution_scope)
    validate_records(
        read_csv(paths["mechanism_geometry_records.csv"]),
        expected_count=counts["geometry_records"],
        expected_sub_gate="GEO-C0",
        head=head,
        branch=branch,
        image=image,
        image_revision=image_revision,
    )
    validate_records(
        read_csv(paths["mechanism_transport_records.csv"]),
        expected_count=counts["transport_records"],
        expected_sub_gate="TR-C0",
        head=head,
        branch=branch,
        image=image,
        image_revision=image_revision,
    )
    validate_records(
        read_csv(paths["mechanism_temporal_events.csv"]),
        expected_count=counts["temporal_event_records"],
        expected_sub_gate="TMP-C0",
        head=head,
        branch=branch,
        image=image,
        image_revision=image_revision,
    )
    validate_records(
        read_csv(paths["mechanism_temporal_summary.csv"]),
        expected_count=counts["temporal_summary_records"],
        expected_sub_gate="TMP-C0",
        head=head,
        branch=branch,
        image=image,
        image_revision=image_revision,
    )
    validate_records(
        read_csv(paths["mechanism_block_probe_records.csv"]),
        expected_count=counts["block_probe_records"],
        expected_sub_gate="JAC-C0",
        head=head,
        branch=branch,
        image=image,
        image_revision=image_revision,
    )
    validate_records(
        read_csv(paths["mechanism_pnz_records.csv"]),
        expected_count=counts["pnz_records"],
        expected_sub_gate="PNZ-L0",
        head=head,
        branch=branch,
        image=image,
        image_revision=image_revision,
    )

    contract_value = json.loads(
        paths["mechanism_controls_contract.json"].read_text(encoding="utf-8")
    )
    if contract_value.get("contract_id") != CONTRACT_ID:
        raise RuntimeError("Mechanism contract artifact mismatch")
    if contract_value.get("implementation_schema_id") != IMPLEMENTATION_SCHEMA_ID:
        raise RuntimeError("Mechanism contract schema artifact mismatch")
    print(
        f"OK: controlled mechanism-controls {args.device} "
        "gate passed with verified provenance"
    )


if __name__ == "__main__":
    main()
