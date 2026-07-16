#!/usr/bin/env python3
"""Run one SI-MA1 attempt in the controlled Docker image."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import uuid
from pathlib import Path
from typing import Any

from torch2pc_thesis.stage3b_si_ma1 import (
    CONTRACT_ID,
    IMPLEMENTATION_SCHEMA_ID,
    PREREGISTRATION_COMMIT,
    PREREGISTRATION_TAG,
    expected_attempt_counts,
)

OUTPUT_FILES = (
    "si_ma1_contract.json",
    "si_ma1_attempts.jsonl",
    "si_ma1_environment.json",
    "si_ma1_arm_timing_records.csv",
    "si_ma1_region_timing_records.csv",
    "si_ma1_numerical_comparisons.csv",
    "si_ma1_topology_comparisons.csv",
    "si_ma1_block_summaries.csv",
    "si_ma1_seed_summaries.csv",
    "si_ma1_order_seed_values.csv",
    "si_ma1_summary.json",
    "si_ma1_decision.json",
    "SHA256SUMS",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("device", choices=["cpu", "gpu"])
    parser.add_argument(
        "--execution-scope",
        choices=["smoke", "confirmatory"],
        default="smoke",
    )
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--model-seed", type=int, required=True)
    parser.add_argument("--max-batches", type=int, default=1)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--attempt-id")
    parser.add_argument("--replacement-of")
    parser.add_argument(
        "--replacement-reason",
        choices=["infrastructure_failure"],
    )
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
    value = json.loads(output(["docker", "image", "inspect", image], cwd=cwd))
    if not isinstance(value, list) or len(value) != 1:
        raise RuntimeError(f"expected one Docker image record for {image!r}")
    record = value[0]
    if not isinstance(record, dict):
        raise TypeError("Docker image record must be an object")
    return record


def verify_controlled_image(repo: Path) -> tuple[str, str, str, str]:
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
        raise RuntimeError("controlled SI-MA1 execution requires a clean tree")
    dotenv = read_dotenv(dotenv_path)
    image = dotenv.get("EXPERIMENT_IMAGE", "")
    if not image:
        raise RuntimeError("EXPERIMENT_IMAGE is missing from .env")
    if dotenv.get("SOURCE_GIT_COMMIT") != head:
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
        raise RuntimeError("controlled image revision differs from HEAD")
    return head, branch, image, str(image_revision)


def resolve_preregistration_commit(repo: Path, *, head: str) -> str:
    prereg_commit = output(
        ["git", "rev-list", "-n", "1", PREREGISTRATION_TAG],
        cwd=repo,
    )
    if prereg_commit != PREREGISTRATION_COMMIT:
        raise RuntimeError("SI-MA1 preregistration tag target differs")
    ancestry = subprocess.run(
        ["git", "merge-base", "--is-ancestor", prereg_commit, head],
        cwd=repo,
        check=False,
    )
    if ancestry.returncode != 0:
        raise RuntimeError("SI-MA1 preregistration is absent from HEAD")
    return prereg_commit


def validate_repo_relative(path: Path, *, root: str) -> None:
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("path must be repository-relative")
    if not path.parts or path.parts[0] != root:
        raise ValueError(f"path must be under {root}/")


def validate_confirmatory_output_path(path: Path, *, model_seed: int) -> None:
    expected = ("results", "stage-3", "si-ma1", "working", "confirmatory")
    if tuple(path.parts[: len(expected)]) != expected:
        raise ValueError(
            "confirmatory output must be under "
            "results/stage-3/si-ma1/working/confirmatory/"
        )
    if f"seed-{model_seed}" not in path.parts:
        raise ValueError("confirmatory output must include seed-<model_seed>")


def build_container_command(
    *,
    device: str,
    scope: str,
    checkpoint: Path,
    model_seed: int,
    max_batches: int,
    output_dir: Path,
    attempt_id: str,
    head: str,
    branch: str,
    image: str,
    image_revision: str,
    prereg_commit: str,
    replacement_of: str | None = None,
    replacement_reason: str | None = None,
) -> list[str]:
    lane = "rocm" if device == "gpu" else "cpu"
    service = "control-gpu" if device == "gpu" else "control-cpu"
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
        "-e",
        f"SI_MA1_PREREG_COMMIT={prereg_commit}",
        service,
        "python",
        "scripts/run_stage3b_si_ma1.py",
        device,
        "--execution-scope",
        scope,
        "--checkpoint",
        str(checkpoint),
        "--model-seed",
        str(model_seed),
        "--max-batches",
        str(max_batches),
        "--output-dir",
        str(output_dir),
        "--attempt-id",
        attempt_id,
    ]
    if replacement_of is not None:
        command.extend(
            [
                "--replacement-of",
                replacement_of,
                "--replacement-reason",
                str(replacement_reason),
            ]
        )
    return command


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
    prereg_commit: str,
) -> None:
    if summary.get("contract_id") != CONTRACT_ID:
        raise RuntimeError("SI-MA1 summary contract mismatch")
    if summary.get("implementation_schema_id") != IMPLEMENTATION_SCHEMA_ID:
        raise RuntimeError("SI-MA1 summary schema mismatch")
    if summary.get("scope") != scope or summary.get("lane") != lane:
        raise RuntimeError("SI-MA1 summary scope/lane mismatch")
    expected_provenance = {
        "source_git_commit": head,
        "source_git_branch": branch,
        "experiment_image": image,
        "image_revision": image_revision,
        "si_ma1_prereg_commit": prereg_commit,
    }
    if {key: summary.get(key) for key in expected_provenance} != expected_provenance:
        raise RuntimeError("SI-MA1 summary provenance mismatch")
    if summary.get("model_seed") != model_seed:
        raise RuntimeError("SI-MA1 summary model-seed mismatch")
    expected_counts = expected_attempt_counts(
        batch_count=max_batches,
        measured_steps_per_arm_block=50,
    )
    if summary.get("expected_counts") != expected_counts:
        raise RuntimeError("SI-MA1 summary expected counts mismatch")
    if summary.get("observed_counts") != expected_counts:
        raise RuntimeError("SI-MA1 summary observed counts mismatch")
    gates = summary.get("gates")
    if not isinstance(gates, dict):
        raise RuntimeError("SI-MA1 summary gates are missing")
    for key in (
        "prerequisites_verified",
        "NUM-MA1-cell",
        "TOPO-MA1-cell",
        "BAL-MA1-cell",
        "CMP-MA1-cell",
    ):
        if gates.get(key) is not True:
            raise RuntimeError(f"SI-MA1 attempt gate did not pass: {key}")
    if gates.get("CAL-COST-MA1") is not None:
        raise RuntimeError("SI-MA1 attempt must defer the cohort cost gate")
    if summary.get("confirmatory_decision_made") is not False:
        raise RuntimeError("SI-MA1 attempt made an unauthorized decision")
    if summary.get("si_ma1_passed") is not None:
        raise RuntimeError("SI-MA1 attempt set an unauthorized global result")


def main() -> None:
    args = parse_args()
    if args.max_batches < 1:
        raise ValueError("--max-batches must be positive")
    if (args.replacement_of is None) != (args.replacement_reason is None):
        raise ValueError("replacement fields must be provided together")
    if args.execution_scope == "confirmatory":
        if args.device != "gpu":
            raise ValueError("confirmatory SI-MA1 requires gpu")
        if args.model_seed not in range(10):
            raise ValueError("confirmatory model seed must be in 0..9")
        if args.max_batches != 3:
            raise ValueError("confirmatory SI-MA1 requires max-batches=3")

    repo = Path(__file__).resolve().parents[1]
    validate_repo_relative(args.checkpoint, root="results")
    validate_repo_relative(args.output_dir, root="results")
    if args.execution_scope == "confirmatory":
        validate_confirmatory_output_path(
            args.output_dir,
            model_seed=args.model_seed,
        )
    output_dir = repo / args.output_dir
    if output_dir.exists() and any(output_dir.iterdir()):
        raise RuntimeError("SI-MA1 output directory must be new and empty")
    if not (repo / args.checkpoint).is_file():
        raise RuntimeError(f"checkpoint is missing: {args.checkpoint}")

    head, branch, image, image_revision = verify_controlled_image(repo)
    prereg_commit = resolve_preregistration_commit(repo, head=head)
    lane = "rocm" if args.device == "gpu" else "cpu"
    attempt_id = args.attempt_id or (
        f"host-{args.execution_scope}-seed-{args.model_seed}-{uuid.uuid4().hex}"
    )
    command = build_container_command(
        device=args.device,
        scope=args.execution_scope,
        checkpoint=args.checkpoint,
        model_seed=args.model_seed,
        max_batches=args.max_batches,
        output_dir=args.output_dir,
        attempt_id=attempt_id,
        head=head,
        branch=branch,
        image=image,
        image_revision=image_revision,
        prereg_commit=prereg_commit,
        replacement_of=args.replacement_of,
        replacement_reason=args.replacement_reason,
    )
    subprocess.run(command, cwd=repo, check=True, env=os.environ.copy())

    for name in OUTPUT_FILES:
        if not (output_dir / name).is_file():
            raise RuntimeError(f"SI-MA1 output is missing: {name}")
    summary = json.loads(
        (output_dir / "si_ma1_summary.json").read_text(encoding="utf-8")
    )
    if not isinstance(summary, dict):
        raise TypeError("SI-MA1 summary must be a JSON object")
    validate_summary(
        summary,
        scope=args.execution_scope,
        lane=lane,
        model_seed=args.model_seed,
        max_batches=args.max_batches,
        head=head,
        branch=branch,
        image=image,
        image_revision=image_revision,
        prereg_commit=prereg_commit,
    )
    frozen_contract = repo / "experiments/planned/STAGE3B-SI-MA1-CONTRACT.json"
    if (output_dir / "si_ma1_contract.json").read_bytes() != frozen_contract.read_bytes():
        raise RuntimeError("SI-MA1 contract artifact is not byte-identical")
    subprocess.run(
        ["sha256sum", "-c", "SHA256SUMS"],
        cwd=output_dir,
        check=True,
        stdout=subprocess.DEVNULL,
    )
    print(
        f"OK: controlled SI-MA1 {args.device} {args.execution_scope} "
        f"seed={args.model_seed}"
    )


if __name__ == "__main__":
    main()
