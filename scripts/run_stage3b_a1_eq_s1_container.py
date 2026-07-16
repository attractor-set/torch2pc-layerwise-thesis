#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any


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
            "Canonical EQ-S1 execution requires a clean committed tree. "
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Stage 3B EQ-S1 through the controlled Docker execution lane."
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
        f"eq-s1-{args.device}-smoke"
    )

    if output_dir.is_absolute() or ".." in output_dir.parts:
        raise ValueError("--output-dir must be a repository-relative path")
    if not output_dir.parts or output_dir.parts[0] != "results":
        raise ValueError("--output-dir must be located under results/")

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
        "scripts/run_stage3b_a1_eq_s1.py",
        args.device,
        "--max-batches",
        str(args.max_batches),
        "--output-dir",
        str(output_dir),
    ]

    print(f"source_commit={head}")
    print(f"experiment_image={image}")
    print(f"execution_lane={lane}")
    subprocess.run(command, cwd=repo, check=True)

    summary_path = repo / output_dir / "eq_s1_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    environment = summary.get("execution_environment", {})
    expected = {
        "controlled_container": True,
        "lane": lane,
        "source_git_commit": head,
    }
    observed = {key: environment.get(key) for key in expected}
    if observed != expected:
        raise RuntimeError(
            f"EQ-S1 output provenance mismatch: expected {expected}, observed {observed}"
        )
    if summary.get("control_id") != "EQ-S1" or summary.get("passed") is not True:
        raise RuntimeError("EQ-S1 output does not contain a passing EQ-S1 summary")

    runs = summary.get("runs")
    model_seeds = summary.get("model_seeds")
    batches_per_seed = summary.get("batches_per_seed")
    if not isinstance(runs, list) or not runs:
        raise RuntimeError("EQ-S1 output contains no run summaries")
    if not isinstance(model_seeds, list) or not isinstance(batches_per_seed, int):
        raise RuntimeError("EQ-S1 output has invalid run-count metadata")
    expected_runs = len(model_seeds) * batches_per_seed
    if len(runs) != expected_runs:
        raise RuntimeError(
            f"EQ-S1 output contains {len(runs)} runs; expected {expected_runs}"
        )

    for run in runs:
        diagnostics = run.get("shortcut_diagnostics", {})
        top_level_layers = diagnostics.get("top_level_layers")
        joint_vjp_calls = diagnostics.get("joint_vjp_calls")
        if diagnostics.get("one_call_per_layer") is not True:
            raise RuntimeError("EQ-S1 output violated the one-joint-VJP-per-layer contract")
        if not isinstance(top_level_layers, int) or top_level_layers < 1:
            raise RuntimeError("EQ-S1 output has invalid top-level-layer diagnostics")
        if joint_vjp_calls != top_level_layers:
            raise RuntimeError("EQ-S1 output has inconsistent joint-VJP diagnostics")

    print(f"OK: controlled EQ-S1 {args.device} gate passed with verified provenance")


if __name__ == "__main__":
    main()
