#!/usr/bin/env python3
"""Run one SI-MA0 implementation cell in the controlled Docker image."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

from torch2pc_thesis.stage3b_si_ma0 import (
    CONTRACT_ID,
    IMPLEMENTATION_SCHEMA_ID,
    expected_record_counts,
)

OUTPUT_FILES = (
    "si_ma0_contract.json",
    "si_ma0_attempts.jsonl",
    "si_ma0_environment.json",
    "si_ma0_event_records.csv",
    "si_ma0_output_error_records.csv",
    "si_ma0_mode_comparisons.csv",
    "si_ma0_total_timing_records.csv",
    "si_ma0_region_timing_records.csv",
    "si_ma0_vjp_records.csv",
    "si_ma0_saved_tensor_records.csv",
    "si_ma0_graph_lifetime_records.csv",
    "si_ma0_batch_summaries.csv",
    "si_ma0_model_region_summaries.csv",
    "si_ma0_summary.json",
    "si_ma0_decision.json",
    "SHA256SUMS",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("device", choices=["cpu", "gpu"])
    parser.add_argument(
        "--execution-scope",
        choices=["smoke"],
        default="smoke",
    )
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--model-seed", type=int, required=True)
    parser.add_argument("--max-batches", type=int, default=1)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


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
    value = json.loads(raw)
    if not isinstance(value, list) or len(value) != 1:
        raise RuntimeError(f"expected one Docker image record for {image!r}")
    record = value[0]
    if not isinstance(record, dict):
        raise TypeError("Docker image record must be an object")
    return record


def verify_controlled_image(
    repo: Path,
) -> tuple[str, str, str, str]:
    dotenv_path = repo / ".env"
    if not dotenv_path.is_file():
        raise RuntimeError("missing .env; run `make init` first")
    head = output(["git", "rev-parse", "HEAD"], cwd=repo)
    branch = output(["git", "branch", "--show-current"], cwd=repo)
    if not re.fullmatch(r"[0-9a-f]{40}", head):
        raise RuntimeError("unable to resolve source commit")
    if not branch:
        raise RuntimeError("controlled execution requires a named branch")
    if output(["git", "status", "--porcelain"], cwd=repo):
        raise RuntimeError(
            "controlled SI-MA0 execution requires a clean committed tree"
        )
    dotenv = read_dotenv(dotenv_path)
    image = dotenv.get("EXPERIMENT_IMAGE", "")
    env_commit = dotenv.get("SOURCE_GIT_COMMIT", "")
    if not image:
        raise RuntimeError("EXPERIMENT_IMAGE is missing from .env")
    if env_commit != head:
        raise RuntimeError(".env SOURCE_GIT_COMMIT does not match HEAD")
    image_info = inspect_image(image, cwd=repo)
    config = image_info.get("Config")
    labels: dict[str, Any] = {}
    if isinstance(config, dict):
        raw_labels = config.get("Labels")
        if isinstance(raw_labels, dict):
            labels = raw_labels
    image_revision = labels.get("org.opencontainers.image.revision")
    if image_revision != head:
        raise RuntimeError(
            "controlled image revision differs from HEAD; rebuild image"
        )
    return head, branch, image, str(image_revision)


def controlled_environment(
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


def validate_repo_relative(path: Path, *, root: str) -> None:
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("path must be repository-relative")
    if not path.parts or path.parts[0] != root:
        raise ValueError(f"path must be under {root}/")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def validate_summary(
    summary: dict[str, Any],
    *,
    scope: str,
    lane: str,
    model_seed: int,
    max_batches: int,
    head: str,
    branch: str,
    image: str,
    image_revision: str,
) -> None:
    if summary.get("contract_id") != CONTRACT_ID:
        raise RuntimeError("SI-MA0 summary contract mismatch")
    if summary.get("implementation_schema_id") != IMPLEMENTATION_SCHEMA_ID:
        raise RuntimeError("SI-MA0 summary schema mismatch")
    if summary.get("scope") != scope or summary.get("lane") != lane:
        raise RuntimeError("SI-MA0 summary scope/lane mismatch")
    expected_provenance = {
        "source_git_commit": head,
        "source_git_branch": branch,
        "experiment_image": image,
        "image_revision": image_revision,
    }
    observed = {key: summary.get(key) for key in expected_provenance}
    if observed != expected_provenance:
        raise RuntimeError("SI-MA0 summary provenance mismatch")
    if summary.get("model_seed") != model_seed:
        raise RuntimeError("SI-MA0 summary model-seed mismatch")
    expected_counts = expected_record_counts(
        model_count=1,
        batch_count=max_batches,
        inference_steps=20,
        updated_state_layers=5,
    )
    if summary.get("expected_counts") != expected_counts:
        raise RuntimeError("SI-MA0 expected-count metadata mismatch")
    if summary.get("observed_counts") != expected_counts:
        raise RuntimeError("SI-MA0 observed-count metadata mismatch")
    for key in (
        "rec_ma0_smoke_passed",
        "obs_ma0_smoke_passed",
        "ver_ma0_smoke_passed",
        "cost_ma0_timer_operational",
        "cmp_ma0_smoke_passed",
        "passed",
    ):
        if summary.get(key) is not True:
            raise RuntimeError(f"SI-MA0 smoke field is not passing: {key}")
    if summary.get("confirmatory_decision_made") is not False:
        raise RuntimeError("implementation smoke made a confirmatory decision")
    if summary.get("si_ma0_passed") is not None:
        raise RuntimeError("implementation smoke populated si_ma0_passed")
    if summary.get("dataset_loader_used") is not True:
        raise RuntimeError("SI-MA0 validation loader metadata is missing")
    if summary.get("test_split_access") is not False:
        raise RuntimeError("SI-MA0 smoke accessed the test split")


def validate_record_counts(
    output_dir: Path,
    *,
    max_batches: int,
) -> None:
    expected = expected_record_counts(
        model_count=1,
        batch_count=max_batches,
        inference_steps=20,
        updated_state_layers=5,
    )
    observed = {
        "state_update_events": len(
            read_csv(output_dir / "si_ma0_event_records.csv")
        ),
        "output_error_records": len(
            read_csv(output_dir / "si_ma0_output_error_records.csv")
        ),
        "mode_comparisons": len(
            read_csv(output_dir / "si_ma0_mode_comparisons.csv")
        ),
    }
    observed["diagnostic_records"] = (
        observed["state_update_events"]
        + observed["output_error_records"]
    )
    if observed != expected:
        raise RuntimeError(
            f"SI-MA0 output count mismatch: {observed} != {expected}"
        )


def main() -> None:
    args = parse_args()
    if args.max_batches < 1:
        raise ValueError("--max-batches must be positive")
    repo = Path(__file__).resolve().parents[1]
    validate_repo_relative(args.checkpoint, root="results")
    validate_repo_relative(args.output_dir, root="results")
    checkpoint = repo / args.checkpoint
    if not checkpoint.is_file():
        raise RuntimeError(f"checkpoint is missing: {args.checkpoint}")
    head, branch, image, image_revision = verify_controlled_image(repo)
    lane = "rocm" if args.device == "gpu" else "cpu"
    service = "control-gpu" if args.device == "gpu" else "control-cpu"
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
        "scripts/run_stage3b_si_ma0.py",
        args.device,
        "--execution-scope",
        args.execution_scope,
        "--checkpoint",
        str(args.checkpoint),
        "--model-seed",
        str(args.model_seed),
        "--max-batches",
        str(args.max_batches),
        "--output-dir",
        str(args.output_dir),
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
        env=controlled_environment(
            head=head,
            branch=branch,
            image=image,
            image_revision=image_revision,
        ),
    )
    output_dir = repo / args.output_dir
    for name in OUTPUT_FILES:
        if not (output_dir / name).is_file():
            raise RuntimeError(f"SI-MA0 output is missing: {name}")
    summary_value = json.loads(
        (output_dir / "si_ma0_summary.json").read_text(
            encoding="utf-8"
        )
    )
    if not isinstance(summary_value, dict):
        raise TypeError("SI-MA0 summary must be a JSON object")
    validate_summary(
        summary_value,
        scope=args.execution_scope,
        lane=lane,
        model_seed=args.model_seed,
        max_batches=args.max_batches,
        head=head,
        branch=branch,
        image=image,
        image_revision=image_revision,
    )
    validate_record_counts(
        output_dir,
        max_batches=args.max_batches,
    )
    contract_artifact = output_dir / "si_ma0_contract.json"
    frozen_contract = (
        repo / "experiments/planned/STAGE3B-SI-MA0-CONTRACT.json"
    )
    if contract_artifact.read_bytes() != frozen_contract.read_bytes():
        raise RuntimeError("SI-MA0 contract artifact is not byte-identical")
    contract_value = json.loads(
        contract_artifact.read_text(encoding="utf-8")
    )
    if contract_value.get("contract_id") != CONTRACT_ID:
        raise RuntimeError("SI-MA0 contract artifact mismatch")
    subprocess.run(
        ["sha256sum", "-c", "SHA256SUMS"],
        cwd=output_dir,
        check=True,
        stdout=subprocess.DEVNULL,
    )
    print(
        f"OK: controlled SI-MA0 {args.device} implementation "
        "smoke passed with verified provenance"
    )


if __name__ == "__main__":
    main()
