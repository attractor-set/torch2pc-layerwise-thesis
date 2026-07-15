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


def verify_controlled_image(repo: Path) -> tuple[str, str]:
    dotenv_path = repo / ".env"
    if not dotenv_path.is_file():
        raise RuntimeError("Missing .env; run `make init` first")

    head = output(["git", "rev-parse", "HEAD"], cwd=repo)
    if not re.fullmatch(r"[0-9a-f]{40}", head):
        raise RuntimeError("Unable to resolve the full source Git commit")

    dirty = output(["git", "status", "--porcelain"], cwd=repo)
    if dirty:
        raise RuntimeError(
            "Canonical OBS-NI0 execution requires a clean committed tree. "
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
    return head, image


def controlled_compose_environment(
    *,
    head: str,
    image: str,
) -> dict[str, str]:
    environment = os.environ.copy()
    environment["SOURCE_GIT_COMMIT"] = head
    environment["EXPERIMENT_IMAGE"] = image
    return environment


def validate_output_dir(output_dir: Path) -> None:
    if output_dir.is_absolute() or ".." in output_dir.parts:
        raise ValueError("--output-dir must be a repository-relative path")
    if not output_dir.parts or output_dir.parts[0] != "results":
        raise ValueError("--output-dir must be located under results/")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Stage 3B OBS-NI0 through the controlled Docker lane."
    )
    parser.add_argument("device", choices=["cpu", "gpu"])
    parser.add_argument("--max-batches", type=int, default=1)
    parser.add_argument("--output-dir", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.max_batches < 1:
        raise ValueError("--max-batches must be at least one")

    repo = Path(__file__).resolve().parents[1]
    head, image = verify_controlled_image(repo)
    lane = "rocm" if args.device == "gpu" else "cpu"
    service = "control-gpu" if args.device == "gpu" else "control-cpu"
    output_dir = args.output_dir or Path(
        "results/stage-3/a1-shortcut-observer-controls/working/"
        f"obs-ni0-{args.device}-smoke"
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
        f"EXPERIMENT_IMAGE={image}",
        service,
        "python",
        "scripts/run_stage3b_a1_obs_ni0.py",
        args.device,
        "--max-batches",
        str(args.max_batches),
        "--output-dir",
        str(output_dir),
    ]

    print(f"source_commit={head}")
    print(f"experiment_image={image}")
    print(f"execution_lane={lane}")
    subprocess.run(
        command,
        cwd=repo,
        check=True,
        env=controlled_compose_environment(head=head, image=image),
    )

    summary_path = repo / output_dir / "obs_ni0_summary.json"
    endpoint_path = repo / output_dir / "obs_ni0_records.csv"
    payload_path = repo / output_dir / "obs_ni0_payload_records.csv"
    state_path = repo / output_dir / "obs_ni0_state_records.csv"
    for path in (summary_path, endpoint_path, payload_path, state_path):
        if not path.is_file():
            raise RuntimeError(f"OBS-NI0 output is missing {path.name}")

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    environment = summary.get("execution_environment", {})
    expected_environment = {
        "controlled_container": True,
        "lane": lane,
        "source_git_commit": head,
    }
    observed_environment = {
        key: environment.get(key) for key in expected_environment
    }
    if observed_environment != expected_environment:
        raise RuntimeError(
            f"OBS-NI0 provenance mismatch: expected {expected_environment}, "
            f"observed {observed_environment}"
        )
    if summary.get("control_id") != "OBS-NI0" or summary.get("passed") is not True:
        raise RuntimeError("OBS-NI0 output does not contain a passing summary")

    schema = summary.get("observer_schema", {})
    if schema.get("observer_schema_id") != OBSERVER_SCHEMA_ID:
        raise RuntimeError("OBS-NI0 output has an unexpected observer schema")
    if schema.get("expected_top_level_layers") != 6:
        raise RuntimeError("OBS-NI0 output has an unexpected layer count")
    if schema.get("expected_records_per_arm_run") != 12:
        raise RuntimeError("OBS-NI0 output has an unexpected payload count contract")
    if schema.get("capture_policy") != "first forward invocation per top-level layer":
        raise RuntimeError("OBS-NI0 output has an unexpected capture policy")
    if schema.get("additional_forward_calls") != "counted but not captured":
        raise RuntimeError("OBS-NI0 output has an unexpected repeated-call policy")

    runs = summary.get("runs")
    model_seeds = summary.get("model_seeds")
    batches_per_seed = summary.get("batches_per_seed")
    if not isinstance(runs, list) or not runs:
        raise RuntimeError("OBS-NI0 output contains no run summaries")
    if not isinstance(model_seeds, list) or not isinstance(batches_per_seed, int):
        raise RuntimeError("OBS-NI0 output has invalid run-count metadata")
    expected_runs = len(model_seeds) * batches_per_seed * 2
    if len(runs) != expected_runs:
        raise RuntimeError(
            f"OBS-NI0 output contains {len(runs)} runs; expected {expected_runs}"
        )

    arm_counts = Counter(str(run.get("arm")) for run in runs)
    expected_arm_runs = len(model_seeds) * batches_per_seed
    if arm_counts != {
        "fixedpred": expected_arm_runs,
        "joint_vjp": expected_arm_runs,
    }:
        raise RuntimeError(f"OBS-NI0 arm counts are invalid: {dict(arm_counts)}")

    for run in runs:
        validation = run.get("observer_validation", {})
        arm = run.get("arm")
        if run.get("passed") is not True:
            raise RuntimeError("OBS-NI0 contains a failed paired run")
        if run.get("gradient_components") != 10:
            raise RuntimeError("OBS-NI0 run has an invalid gradient count")
        if run.get("parameter_components") != 10:
            raise RuntimeError("OBS-NI0 run has an invalid parameter count")
        if run.get("observer_payload_components") != 12:
            raise RuntimeError("OBS-NI0 run has an invalid payload count")
        if run.get("optimizer_tensor_components") != 0:
            raise RuntimeError("OBS-NI0 stateless SGD produced tensor optimizer state")
        if run.get("buffer_components") != 0:
            raise RuntimeError("OBS-NI0 lenet control produced unexpected buffers")
        if run.get("candidate_observer_mode") != "passive_first_forward_io":
            raise RuntimeError("OBS-NI0 run has an unexpected observer mode")
        if run.get("observer_schema_id") != OBSERVER_SCHEMA_ID:
            raise RuntimeError("OBS-NI0 run has an unexpected observer schema id")
        if run.get("rng_passed") is not True:
            raise RuntimeError("OBS-NI0 contains an RNG-state mismatch")
        if run.get("buffers_passed") is not True:
            raise RuntimeError("OBS-NI0 contains a model-buffer mismatch")
        if run.get("inputs_passed") is not True:
            raise RuntimeError("OBS-NI0 contains an input-state mismatch")
        if run.get("structural_contract_passed") is not True:
            raise RuntimeError("OBS-NI0 contains a structural-contract failure")
        if validation.get("passed") is not True:
            raise RuntimeError("OBS-NI0 observer validation failed")
        if validation.get("expected_records") != 12:
            raise RuntimeError("OBS-NI0 run has an invalid expected payload count")
        if validation.get("observed_records") != 12:
            raise RuntimeError("OBS-NI0 run has an invalid observed payload count")
        if validation.get("balanced_forward_calls") is not True:
            raise RuntimeError("OBS-NI0 run has unbalanced forward-hook calls")
        input_calls = validation.get("input_call_counts")
        output_calls = validation.get("output_call_counts")
        if not isinstance(input_calls, list) or not isinstance(output_calls, list):
            raise RuntimeError("OBS-NI0 run has invalid forward-call diagnostics")
        if len(input_calls) != 6 or input_calls != output_calls:
            raise RuntimeError("OBS-NI0 run has inconsistent forward-call diagnostics")
        if not all(isinstance(count, int) and count >= 1 for count in input_calls):
            raise RuntimeError("OBS-NI0 run has an invalid forward-call count")
        if arm == "fixedpred":
            if run.get("eta") != 1.0 or run.get("inference_steps") != 6:
                raise RuntimeError("OBS-NI0 FixedPred contract is invalid")
        elif arm == "joint_vjp":
            diagnostics = run.get("shortcut_diagnostics", {})
            if run.get("eta") is not None or run.get("inference_steps") != 6:
                raise RuntimeError("OBS-NI0 joint-VJP contract is invalid")
            if diagnostics.get("joint_vjp_calls") != 6:
                raise RuntimeError("OBS-NI0 joint-VJP call count is invalid")
            if diagnostics.get("one_call_per_layer") is not True:
                raise RuntimeError("OBS-NI0 joint-VJP structure is invalid")
            if input_calls != [1, 1, 1, 1, 1, 1]:
                raise RuntimeError("OBS-NI0 joint-VJP forward-call count is invalid")
        else:
            raise RuntimeError(f"OBS-NI0 contains an unknown arm: {arm!r}")

    with endpoint_path.open(encoding="utf-8", newline="") as handle:
        endpoint_records = list(csv.DictReader(handle))
    endpoint_counts = Counter(
        row["comparison_kind"] for row in endpoint_records
    )
    expected_components = expected_runs * 10
    if endpoint_counts != {
        "endpoint_gradient": expected_components,
        "parameter_after_optimizer_step": expected_components,
    }:
        raise RuntimeError(
            f"OBS-NI0 endpoint counts are invalid: {dict(endpoint_counts)}"
        )
    if not all(row["passed"].strip().lower() == "true" for row in endpoint_records):
        raise RuntimeError("OBS-NI0 endpoint records contain a failed comparison")

    with payload_path.open(encoding="utf-8", newline="") as handle:
        payload_records = list(csv.DictReader(handle))
    if len(payload_records) != expected_runs * 12:
        raise RuntimeError("OBS-NI0 payload-record count is invalid")
    if not all(
        row["observer_schema_id"] == OBSERVER_SCHEMA_ID
        and row["occurrence"] == "0"
        and row["detached"].strip().lower() == "true"
        and row["finite"].strip().lower() == "true"
        and row["metadata_preserved"].strip().lower() == "true"
        for row in payload_records
    ):
        raise RuntimeError("OBS-NI0 payload records violate the observer contract")

    with state_path.open(encoding="utf-8", newline="") as handle:
        state_records = list(csv.DictReader(handle))
    if len(state_records) != expected_runs * 9:
        raise RuntimeError("OBS-NI0 state-record count is invalid")
    if not all(
        row["finite"].strip().lower() == "true"
        and row["passed"].strip().lower() == "true"
        for row in state_records
    ):
        raise RuntimeError("OBS-NI0 state records contain a failed comparison")

    aggregate = summary.get("aggregate", {})
    if aggregate.get("paired_runs") != expected_runs:
        raise RuntimeError("OBS-NI0 aggregate paired-run count is invalid")
    if aggregate.get("endpoint_records") != len(endpoint_records):
        raise RuntimeError("OBS-NI0 aggregate endpoint count is invalid")
    if aggregate.get("payload_records") != len(payload_records):
        raise RuntimeError("OBS-NI0 aggregate payload count is invalid")
    if aggregate.get("state_records") != len(state_records):
        raise RuntimeError("OBS-NI0 aggregate state count is invalid")

    print(f"OK: controlled OBS-NI0 {args.device} gate passed with verified provenance")


if __name__ == "__main__":
    main()
