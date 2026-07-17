#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

import torch
import yaml

from torch2pc_thesis.data import build_dataloaders

REQUIRED = {"data", "training", "reproducibility", "runtime"}
SEEDS = (0, 1, 2)


class ExportError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_json(value: Any) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def load_object(path: Path) -> dict[str, Any]:
    if path.suffix.lower() == ".json":
        value = json.loads(path.read_text(encoding="utf-8"))
    else:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ExportError(f"not an object: {path}")
    return cast(dict[str, Any], value)


def section(config: Mapping[str, Any], name: str) -> dict[str, Any]:
    value = config.get(name)
    if not isinstance(value, dict):
        raise ExportError(f"missing config section: {name}")
    return cast(dict[str, Any], value)


def fingerprint(config: Mapping[str, Any]) -> dict[str, Any]:
    data = section(config, "data")
    training = section(config, "training")
    reproducibility = section(config, "reproducibility")

    for key in (
        "dataset",
        "root",
        "validation_fraction",
        "train_subset",
        "split_dir",
    ):
        if key not in data:
            raise ExportError(f"missing data.{key}")
    if "batch_size" not in training:
        raise ExportError("missing training.batch_size")
    if "split_seed" not in reproducibility:
        raise ExportError("missing reproducibility.split_seed")

    return {
        "data": {
            key: data[key]
            for key in (
                "dataset",
                "root",
                "validation_fraction",
                "train_subset",
                "split_dir",
            )
        },
        "training": {"batch_size": training["batch_size"]},
        "reproducibility": {
            "split_seed": reproducibility["split_seed"]
        },
    }


def config_score(path: Path) -> int:
    name = path.name.lower()
    return (
        100 * int("resolved" in name)
        + 50 * int("config" in name)
        - 20 * int("metadata" in name)
    )


def find_resolved_config(checkpoint: Path) -> tuple[Path, dict[str, Any]]:
    checkpoint = checkpoint.resolve()
    if not checkpoint.is_file():
        raise ExportError(f"checkpoint missing: {checkpoint}")

    candidates: list[tuple[int, Path, dict[str, Any]]] = []
    for directory in (checkpoint.parent, checkpoint.parent.parent):
        if not directory.is_dir():
            continue
        for path in directory.iterdir():
            if path.suffix.lower() not in {".json", ".yaml", ".yml"}:
                continue
            try:
                value = load_object(path)
            except Exception:
                continue
            if REQUIRED.issubset(value):
                candidates.append((config_score(path), path.resolve(), value))

    if not candidates:
        raise ExportError(
            f"resolved config not found near checkpoint: {checkpoint}"
        )

    candidates.sort(key=lambda item: (-item[0], item[1].as_posix()))
    top_score = candidates[0][0]
    top = [item for item in candidates if item[0] == top_score]
    protocol_hashes = {sha256_json(fingerprint(item[2])) for item in top}
    if len(protocol_hashes) != 1:
        paths = "\n".join(f"  {item[1]}" for item in top)
        raise ExportError(f"ambiguous resolved configs:\n{paths}")

    _, path, value = top[0]
    return path, value


def atomic_save_torch(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as stream:
        temp = Path(stream.name)
    try:
        torch.save(payload, temp)
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def atomic_save_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as stream:
        stream.write(text)
        temp = Path(stream.name)
    try:
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint-0", type=Path, required=True)
    parser.add_argument("--checkpoint-1", type=Path, required=True)
    parser.add_argument("--checkpoint-2", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "experiments/frozen/stage3b-b1-smoke/"
            "shared-validation-batch-0.pt"
        ),
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(
            "experiments/frozen/stage3b-b1-smoke/"
            "shared-validation-batch-0.manifest.json"
        ),
    )
    parser.add_argument("--download", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    checkpoints = (
        args.checkpoint_0,
        args.checkpoint_1,
        args.checkpoint_2,
    )

    try:
        sources = [find_resolved_config(path) for path in checkpoints]
        protocols = [fingerprint(config) for _, config in sources]
        protocol_hashes = [sha256_json(value) for value in protocols]
        if len(set(protocol_hashes)) != 1:
            raise ExportError(
                "Stage 2 BP runs do not share one data protocol:\n"
                + "\n".join(
                    f"  seed={seed} protocol={digest} config={path}"
                    for seed, digest, (path, _) in zip(
                        SEEDS,
                        protocol_hashes,
                        sources,
                        strict=True,
                    )
                )
            )

        config = copy.deepcopy(sources[0][1])
        runtime = section(config, "runtime")
        runtime["device"] = "cpu"
        runtime["loader_workers"] = 0
        reproducibility = section(config, "reproducibility")
        reproducibility.setdefault("loader_seed", 0)

        bundle = build_dataloaders(
            config,
            include_test=False,
            download=bool(args.download),
        )
        batch = next(iter(bundle.validation))
        if not isinstance(batch, tuple | list) or len(batch) < 2:
            raise ExportError("invalid validation batch structure")

        inputs, targets = batch[0], batch[1]
        if not torch.is_tensor(inputs) or not torch.is_tensor(targets):
            raise ExportError("validation batch does not contain tensors")
        inputs = inputs.detach().cpu().contiguous()
        targets = targets.detach().cpu().contiguous()
        if inputs.shape[0] != targets.shape[0]:
            raise ExportError("input and target batch sizes differ")

        payload = {
            "inputs": inputs,
            "targets": targets,
            "split": "validation",
            "dataset": protocols[0]["data"]["dataset"],
            "batch_index": 0,
            "shared_across_model_seeds": [0, 1, 2],
            "selection_rule": (
                "first batch from the deterministic shuffle=False "
                "validation loader reconstructed from the common "
                "Stage 2 BP data protocol"
            ),
        }

        if args.output.exists():
            existing = torch.load(
                args.output,
                map_location="cpu",
                weights_only=False,
            )
            if (
                not isinstance(existing, dict)
                or existing.get("split") != "validation"
                or not torch.equal(existing.get("inputs"), inputs)
                or not torch.equal(existing.get("targets"), targets)
            ):
                raise ExportError(
                    f"existing output differs from reconstruction: {args.output}"
                )
            reused = True
        else:
            atomic_save_torch(payload, args.output)
            reused = False

        artifact_sha = sha256_file(args.output)
        manifest = {
            "schema_version": 1,
            "artifact_type": "stage3b_b1_shared_validation_batch",
            "artifact_path": args.output.as_posix(),
            "artifact_sha256": artifact_sha,
            "dataset": protocols[0]["data"]["dataset"],
            "split": "validation",
            "batch_index": 0,
            "inputs_shape": list(inputs.shape),
            "inputs_dtype": str(inputs.dtype),
            "targets_shape": list(targets.shape),
            "targets_dtype": str(targets.dtype),
            "shared_across_model_seeds": [0, 1, 2],
            "include_test": False,
            "test_split_accessed": False,
            "common_data_protocol": protocols[0],
            "common_data_protocol_sha256": protocol_hashes[0],
            "split_files": [path.as_posix() for path in bundle.split_files],
            "split_sha256": dict(bundle.split_sha256),
            "sources": [
                {
                    "model_seed": seed,
                    "checkpoint_path": checkpoint.resolve().as_posix(),
                    "checkpoint_sha256": sha256_file(checkpoint.resolve()),
                    "resolved_config_path": config_path.as_posix(),
                    "resolved_config_sha256": sha256_file(config_path),
                }
                for seed, checkpoint, (config_path, _) in zip(
                    SEEDS,
                    checkpoints,
                    sources,
                    strict=True,
                )
            ],
        }
        atomic_save_json(manifest, args.manifest)
    except (ExportError, StopIteration) as exc:
        print(f"ERROR: {exc}")
        return 2

    print("OK: shared deterministic validation batch exported")
    print(f"BATCH_PATH={args.output}")
    print(f"BATCH_SHA256={artifact_sha}")
    print(f"MANIFEST_PATH={args.manifest}")
    print(f"MANIFEST_SHA256={sha256_file(args.manifest)}")
    print(f"EXISTING_ARTIFACT_REUSED={str(reused).lower()}")
    print(f"INPUTS_SHAPE={list(inputs.shape)}")
    print(f"TARGETS_SHAPE={list(targets.shape)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
