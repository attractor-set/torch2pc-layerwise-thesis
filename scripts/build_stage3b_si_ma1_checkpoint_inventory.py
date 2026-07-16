#!/usr/bin/env python3
"""Build the frozen SI-MA1 ten-seed checkpoint inventory."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import Any, cast

import torch
from torch import Tensor

from torch2pc_thesis.stage3b_si_ma1_confirmatory import (
    IMPLEMENTATION_COMMIT,
    IMPLEMENTATION_TAG,
    CheckpointInventoryEntry,
    SIMA1ConfirmatoryError,
    build_inventory_payload,
    sha256_file,
    write_inventory,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--search-root",
        type=Path,
        default=Path("results/stage-2/runs"),
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--checkpoint",
        action="append",
        default=[],
        metavar="SEED=PATH",
        help=(
            "Explicitly select one repository-relative checkpoint. "
            "Provide exactly ten entries to bypass discovery."
        ),
    )
    return parser.parse_args()


def git_output(repo: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", *args],
        cwd=repo,
        text=True,
        stderr=subprocess.STDOUT,
    ).strip()


def inspect_checkpoint(
    repo: Path,
    path: Path,
) -> CheckpointInventoryEntry | None:
    relative = path.relative_to(repo)
    payload = torch.load(path, map_location="cpu", weights_only=False)
    if not isinstance(payload, dict):
        return None
    config = payload.get("config")
    state_dict = payload.get("state_dict")
    if not isinstance(config, dict) or not isinstance(state_dict, dict):
        return None
    if not all(isinstance(value, Tensor) for value in state_dict.values()):
        return None
    data = config.get("data")
    model = config.get("model")
    method = config.get("method")
    reproducibility = config.get("reproducibility")
    if not all(
        isinstance(value, dict)
        for value in (data, model, method, reproducibility)
    ):
        return None
    data = cast(dict[str, Any], data)
    model = cast(dict[str, Any], model)
    method = cast(dict[str, Any], method)
    reproducibility = cast(dict[str, Any], reproducibility)

    dataset = str(data.get("dataset", ""))
    architecture = str(model.get("architecture", ""))
    method_name = str(method.get("name", ""))
    eta = float(method.get("eta", float("nan")))
    inference_steps = int(method.get("inference_steps", -1))
    model_seed = int(reproducibility.get("model_seed", -1))

    if (
        dataset.lower() != "fashionmnist"
        or architecture != "lenet_classic"
        or method_name.lower() != "strict"
        or eta != 0.05
        or inference_steps != 20
        or model_seed not in range(10)
    ):
        return None
    expected_fragment = f"final_stage_2-fashionmnist-strict-s{model_seed}-"
    if expected_fragment not in relative.as_posix():
        return None
    return CheckpointInventoryEntry(
        model_seed=model_seed,
        checkpoint=relative.as_posix(),
        checkpoint_sha256=sha256_file(path),
        dataset=dataset,
        architecture=architecture,
        method=method_name,
        eta=eta,
        inference_steps=inference_steps,
    )


def parse_checkpoint_overrides(
    values: list[str],
) -> dict[int, Path]:
    """Parse explicit seed-to-checkpoint mappings."""

    result: dict[int, Path] = {}
    for raw in values:
        seed_text, separator, path_text = raw.partition("=")
        if separator != "=" or not path_text:
            raise SIMA1ConfirmatoryError(
                "--checkpoint must use SEED=PATH"
            )
        seed = int(seed_text)
        if seed not in range(10):
            raise SIMA1ConfirmatoryError(
                "checkpoint seed must be in 0..9"
            )
        if seed in result:
            raise SIMA1ConfirmatoryError(
                f"duplicate checkpoint override for seed {seed}"
            )
        path = Path(path_text)
        if path.is_absolute() or ".." in path.parts:
            raise SIMA1ConfirmatoryError(
                "checkpoint override must be repository-relative"
            )
        result[seed] = path
    if result and tuple(sorted(result)) != tuple(range(10)):
        raise SIMA1ConfirmatoryError(
            "explicit checkpoint mode requires all seeds 0..9"
        )
    return result


def main() -> None:
    args = parse_args()
    repo = Path(__file__).resolve().parents[1]
    head = git_output(repo, "rev-parse", "HEAD")
    implementation_commit = git_output(
        repo,
        "rev-list",
        "-n",
        "1",
        IMPLEMENTATION_TAG,
    )
    if implementation_commit != IMPLEMENTATION_COMMIT:
        raise SIMA1ConfirmatoryError(
            "SI-MA1 implementation tag target differs"
        )
    ancestry = subprocess.run(
        [
            "git",
            "merge-base",
            "--is-ancestor",
            implementation_commit,
            head,
        ],
        cwd=repo,
        check=False,
    )
    if ancestry.returncode != 0:
        raise SIMA1ConfirmatoryError(
            "SI-MA1 implementation tag is not an ancestor of HEAD"
        )
    root = repo / args.search_root
    if not root.is_dir():
        raise SIMA1ConfirmatoryError(
            f"checkpoint search root is missing: {args.search_root}"
        )

    overrides = parse_checkpoint_overrides(args.checkpoint)
    if overrides:
        entries = []
        for seed in range(10):
            checkpoint = repo / overrides[seed]
            if not checkpoint.is_file():
                raise SIMA1ConfirmatoryError(
                    f"checkpoint override is missing: {overrides[seed]}"
                )
            entry = inspect_checkpoint(repo, checkpoint)
            if entry is None or entry.model_seed != seed:
                raise SIMA1ConfirmatoryError(
                    f"checkpoint override failed scope validation: "
                    f"{overrides[seed]}"
                )
            entries.append(entry)
    else:
        matches: dict[int, list[CheckpointInventoryEntry]] = {
            seed: [] for seed in range(10)
        }
        for checkpoint in sorted(root.rglob("checkpoint.pt")):
            entry = inspect_checkpoint(repo, checkpoint)
            if entry is not None:
                matches[entry.model_seed].append(entry)

        problems = {
            seed: values
            for seed, values in matches.items()
            if len(values) != 1
        }
        if problems:
            details = {
                seed: [value.checkpoint for value in values]
                for seed, values in problems.items()
            }
            raise SIMA1ConfirmatoryError(
                f"checkpoint discovery is not unique: {details}"
            )
        entries = [matches[seed][0] for seed in range(10)]
    payload = build_inventory_payload(entries, source_commit=head)
    output = args.output
    if not output.is_absolute():
        output = repo / output
    if output.exists():
        raise SIMA1ConfirmatoryError(
            f"inventory output already exists: {output}"
        )
    write_inventory(output, payload)
    print(f"OK: SI-MA1 checkpoint inventory written: {output}")
    print(f"entries_sha256={payload['entries_sha256']}")


if __name__ == "__main__":
    main()
