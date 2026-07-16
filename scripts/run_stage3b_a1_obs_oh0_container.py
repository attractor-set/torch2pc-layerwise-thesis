#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

from torch2pc_thesis.stage3b_a1_obs_oh0 import BENCHMARK_SCHEMA_ID
from torch2pc_thesis.stage3b_a1_observer import OBSERVER_SCHEMA_ID


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
    if len(records) != 1:
        raise RuntimeError(f"Expected one Docker image record for {image!r}")
    return records[0]


def verify_controlled_image(repo: Path) -> tuple[str, str, str]:
    dotenv_path = repo / ".env"
    if not dotenv_path.is_file():
        raise RuntimeError("Missing .env; run `make init` first")

    head = output(["git", "rev-parse", "HEAD"], cwd=repo)
    branch = output(["git", "branch", "--show-current"], cwd=repo)
    if not re.fullmatch(r"[0-9a-f]{40}", head):
        raise RuntimeError("Unable to resolve the full source Git commit")
    if not branch:
        raise RuntimeError("Canonical OBS-OH0 execution requires a named branch")

    dirty = output(["git", "status", "--porcelain"], cwd=repo)
    if dirty:
        raise RuntimeError(
            "Canonical OBS-OH0 execution requires a clean committed tree. "
            "Commit the patch before rebuilding and running the controlled image."
        )

    dotenv = read_dotenv(dotenv_path)
    image = dotenv.get("EXPERIMENT_IMAGE", "")
    env_commit = dotenv.get("SOURCE_GIT_COMMIT", "")
    if not image:
        raise RuntimeError("EXPERIMENT_IMAGE is missing from .env")
    if env_commit != head:
        raise RuntimeError(
            "The .env SOURCE_GIT_COMMIT does not match HEAD. "
            "Run `make build` from the current clean commit."
        )

    image_info = inspect_image(image, cwd=repo)
    labels = image_info.get("Config", {}).get("Labels", {}) or {}
    image_commit = labels.get("org.opencontainers.image.revision")
    if image_commit != head:
        raise RuntimeError(
            "The controlled Docker image was not built from the current commit. "
            "Run `make build` and repeat the gate."
        )
    return head, branch, image


def controlled_compose_environment(
    *,
    head: str,
    branch: str,
    image: str,
) -> dict[str, str]:
    environment = os.environ.copy()
    environment["SOURCE_GIT_COMMIT"] = head
    environment["SOURCE_GIT_BRANCH"] = branch
    environment["EXPERIMENT_IMAGE"] = image
    return environment


def validate_output_dir(output_dir: Path) -> None:
    if output_dir.is_absolute() or ".." in output_dir.parts:
        raise ValueError("--output-dir must be a repository-relative path")
    if not output_dir.parts or output_dir.parts[0] != "results":
        raise ValueError("--output-dir must be located under results/")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Stage 3B OBS-OH0 through the controlled Docker lane."
    )
    parser.add_argument("device", choices=["cpu", "gpu"])
    parser.add_argument(
        "--execution-scope",
        choices=["smoke", "confirmatory", "development"],
        default="smoke",
    )
    parser.add_argument("--max-batches", type=int, default=1)
    parser.add_argument("--timing-repeats", type=int, default=3)
    parser.add_argument("--warmup-pairs", type=int, default=1)
    parser.add_argument("--rss-sampler-interval-ms", type=float, default=1.0)
    parser.add_argument("--output-dir", type=Path)
    return parser.parse_args()


def validate_execution_scope(args: argparse.Namespace) -> None:
    registered = {
        "smoke": (1, 3, 1),
        "confirmatory": (10, 3, 3),
    }
    expected = registered.get(args.execution_scope)
    observed = (args.max_batches, args.timing_repeats, args.warmup_pairs)
    if expected is not None and observed != expected:
        raise ValueError(
            f"OBS-OH0 {args.execution_scope} requires "
            f"max_batches/timing_repeats/warmup_pairs={expected}; "
            f"observed {observed}"
        )


def validate_summary(
    summary: dict[str, Any],
    *,
    lane: str,
    head: str,
    branch: str,
    max_batches: int,
    timing_repeats: int,
    warmup_pairs: int,
    execution_scope: str,
) -> None:
    if summary.get("control_id") != "OBS-OH0":
        raise RuntimeError("OBS-OH0 output has an invalid control id")
    if summary.get("benchmark_schema_id") != BENCHMARK_SCHEMA_ID:
        raise RuntimeError("OBS-OH0 output has an invalid benchmark schema")
    if summary.get("observer_schema_id") != OBSERVER_SCHEMA_ID:
        raise RuntimeError("OBS-OH0 output has an invalid observer schema")
    if summary.get("passed") is not True:
        raise RuntimeError("OBS-OH0 output does not contain a passing summary")
    if summary.get("scope") != execution_scope:
        raise RuntimeError("OBS-OH0 output has an invalid execution scope")

    environment = summary.get("execution_environment", {})
    expected_environment = {
        "controlled_container": True,
        "lane": lane,
        "source_git_commit": head,
        "source_git_branch": branch,
    }
    observed_environment = {
        key: environment.get(key) for key in expected_environment
    }
    if observed_environment != expected_environment:
        raise RuntimeError(
            f"OBS-OH0 provenance mismatch: expected {expected_environment}, "
            f"observed {observed_environment}"
        )

    model_seeds = summary.get("model_seeds")
    if model_seeds != [0, 1, 2]:
        raise RuntimeError("OBS-OH0 output has invalid model seeds")
    if summary.get("batches_per_seed") != max_batches:
        raise RuntimeError("OBS-OH0 output has invalid batch metadata")
    if summary.get("timing_repeats") != timing_repeats:
        raise RuntimeError("OBS-OH0 output has invalid timing-repeat metadata")
    if summary.get("warmup_pairs_per_lane_arm") != warmup_pairs:
        raise RuntimeError("OBS-OH0 output has invalid warm-up metadata")

    expected_measured = len(model_seeds) * max_batches * 2 * timing_repeats
    expected_warmup = 2 * warmup_pairs
    expected_memory = len(model_seeds) * max_batches * 2
    expected_guards = len(model_seeds) * max_batches * 2
    aggregate = summary.get("aggregate", {})
    expected_aggregate = {
        "warmup_timing_pairs": expected_warmup,
        "measured_timing_pairs": expected_measured,
        "timed_executions": expected_measured * 2,
        "memory_pairs": expected_memory,
        "memory_workers": expected_memory * 2,
    }
    if aggregate != expected_aggregate:
        raise RuntimeError(
            f"OBS-OH0 aggregate mismatch: expected {expected_aggregate}, "
            f"observed {aggregate}"
        )
    guards = summary.get("guards", {})
    if guards != {"runs": expected_guards, "passed": True}:
        raise RuntimeError("OBS-OH0 correctness-guard aggregate is invalid")
    if summary.get("structural_passed") is not True:
        raise RuntimeError("OBS-OH0 structural validation failed")
    if execution_scope == "confirmatory":
        if summary.get("budget_enforced") is not True:
            raise RuntimeError("OBS-OH0 confirmatory budget was not enforced")
        timing = summary.get("timing", {})
        memory = summary.get("memory", {})
        if timing.get("budget_passed") is not True:
            raise RuntimeError("OBS-OH0 confirmatory runtime budget failed")
        if memory.get("budget_passed") is not True:
            raise RuntimeError("OBS-OH0 confirmatory memory budget failed")


def main() -> None:
    args = parse_args()
    if args.max_batches < 1:
        raise ValueError("--max-batches must be at least one")
    if args.timing_repeats < 1:
        raise ValueError("--timing-repeats must be at least one")
    if args.warmup_pairs < 1:
        raise ValueError("--warmup-pairs must be at least one")
    if not 0.0 < args.rss_sampler_interval_ms <= 1.0:
        raise ValueError("--rss-sampler-interval-ms must be within (0, 1]")
    validate_execution_scope(args)

    repo = Path(__file__).resolve().parents[1]
    head, branch, image = verify_controlled_image(repo)
    lane = "rocm" if args.device == "gpu" else "cpu"
    service = "control-gpu" if args.device == "gpu" else "control-cpu"
    output_dir = args.output_dir or Path(
        "results/stage-3/a1-shortcut-observer-controls/working/"
        f"obs-oh0-{args.device}-{args.execution_scope}"
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
        service,
        "python",
        "scripts/run_stage3b_a1_obs_oh0.py",
        args.device,
        "--execution-scope",
        args.execution_scope,
        "--max-batches",
        str(args.max_batches),
        "--timing-repeats",
        str(args.timing_repeats),
        "--warmup-pairs",
        str(args.warmup_pairs),
        "--rss-sampler-interval-ms",
        str(args.rss_sampler_interval_ms),
        "--output-dir",
        str(output_dir),
    ]

    print(f"source_commit={head}")
    print(f"source_branch={branch}")
    print(f"experiment_image={image}")
    print(f"execution_lane={lane}")
    subprocess.run(
        command,
        cwd=repo,
        check=True,
        env=controlled_compose_environment(
            head=head,
            branch=branch,
            image=image,
        ),
    )

    paths = {
        "summary": repo / output_dir / "obs_oh0_summary.json",
        "schema": repo / output_dir / "obs_oh0_benchmark_schema.json",
        "guards": repo / output_dir / "obs_oh0_guard_records.csv",
        "timing": repo / output_dir / "obs_oh0_timing_records.csv",
        "timing_summary": repo / output_dir / "obs_oh0_timing_summary.json",
        "memory": repo / output_dir / "obs_oh0_memory_records.csv",
        "memory_summary": repo / output_dir / "obs_oh0_memory_summary.json",
    }
    for path in paths.values():
        if not path.is_file():
            raise RuntimeError(f"OBS-OH0 output is missing {path.name}")

    summary = json.loads(paths["summary"].read_text(encoding="utf-8"))
    if not isinstance(summary, dict):
        raise TypeError("OBS-OH0 summary must be a JSON object")
    validate_summary(
        summary,
        lane=lane,
        head=head,
        branch=branch,
        max_batches=args.max_batches,
        timing_repeats=args.timing_repeats,
        warmup_pairs=args.warmup_pairs,
        execution_scope=args.execution_scope,
    )

    schema = json.loads(paths["schema"].read_text(encoding="utf-8"))
    if schema.get("benchmark_schema_id") != BENCHMARK_SCHEMA_ID:
        raise RuntimeError("OBS-OH0 schema artifact has an invalid schema id")
    if schema.get("execution_scope") != args.execution_scope:
        raise RuntimeError("OBS-OH0 schema artifact has an invalid execution scope")
    observer_schema = schema.get("observer_schema", {})
    if observer_schema.get("observer_schema_id") != OBSERVER_SCHEMA_ID:
        raise RuntimeError("OBS-OH0 schema artifact changed the observer schema")
    if observer_schema.get("expected_records_per_arm_run") != 12:
        raise RuntimeError("OBS-OH0 schema artifact has an invalid payload contract")

    with paths["guards"].open(encoding="utf-8", newline="") as handle:
        guards = list(csv.DictReader(handle))
    expected_guards = 3 * args.max_batches * 2
    if len(guards) != expected_guards:
        raise RuntimeError("OBS-OH0 guard-record count is invalid")
    if Counter(row["arm"] for row in guards) != {
        "fixedpred": 3 * args.max_batches,
        "joint_vjp": 3 * args.max_batches,
    }:
        raise RuntimeError("OBS-OH0 guard arm counts are invalid")
    if not all(row["passed"].strip().lower() == "true" for row in guards):
        raise RuntimeError("OBS-OH0 correctness guard contains a failure")

    with paths["timing"].open(encoding="utf-8", newline="") as handle:
        timing = list(csv.DictReader(handle))
    expected_timing = 2 * args.warmup_pairs + 3 * args.max_batches * 2 * args.timing_repeats
    if len(timing) != expected_timing:
        raise RuntimeError("OBS-OH0 timing-record count is invalid")
    keys = [row["key"] for row in timing]
    if len(keys) != len(set(keys)):
        raise RuntimeError("OBS-OH0 timing records contain duplicate keys")
    if not all(
        row["benchmark_schema_id"] == BENCHMARK_SCHEMA_ID
        and row["observer_schema_id"] == OBSERVER_SCHEMA_ID
        and row["source_git_commit"] == head
        and row["source_git_branch"] == branch
        and row["experiment_image"] == image
        and row["passed_structure"].strip().lower() == "true"
        and int(row["reference_elapsed_ns"]) > 0
        and int(row["candidate_elapsed_ns"]) > 0
        for row in timing
    ):
        raise RuntimeError("OBS-OH0 timing records violate the schema")

    with paths["memory"].open(encoding="utf-8", newline="") as handle:
        memory = list(csv.DictReader(handle))
    expected_memory = 3 * args.max_batches * 2
    if len(memory) != expected_memory:
        raise RuntimeError("OBS-OH0 memory-record count is invalid")
    memory_keys = [row["key"] for row in memory]
    if len(memory_keys) != len(set(memory_keys)):
        raise RuntimeError("OBS-OH0 memory records contain duplicate keys")
    if not all(
        row["benchmark_schema_id"] == BENCHMARK_SCHEMA_ID
        and row["observer_schema_id"] == OBSERVER_SCHEMA_ID
        and row["source_git_commit"] == head
        and row["source_git_branch"] == branch
        and row["experiment_image"] == image
        and row["passed_structure"].strip().lower() == "true"
        and int(row["candidate_payload_records"]) == 12
        for row in memory
    ):
        raise RuntimeError("OBS-OH0 memory records violate the schema")

    print(f"OK: controlled OBS-OH0 {args.device} gate passed with verified provenance")


if __name__ == "__main__":
    main()
