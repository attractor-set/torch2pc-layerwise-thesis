#!/usr/bin/env python3
"""Export ten distinct frozen validation batches for confirmatory EQ-B1."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import torch

from scripts.export_stage3b_b1_shared_validation_batch import (
    SEEDS,
    ExportError,
    atomic_save_json,
    atomic_save_torch,
    find_resolved_config,
    fingerprint,
    section,
    sha256_file,
    sha256_json,
)
from torch2pc_thesis.data import build_dataloaders

EXPECTED_BATCH_COUNT = 10
EXPECTED_BATCH_SIZE = 256


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--checkpoint-0", type=Path, required=True)
    parser.add_argument("--checkpoint-1", type=Path, required=True)
    parser.add_argument("--checkpoint-2", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("experiments/frozen/stage3b-b1-confirmatory/batches"),
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("experiments/frozen/stage3b-b1-confirmatory/validation-batches.json"),
    )
    parser.add_argument("--download", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_root = args.project_root.expanduser().resolve()
    output_dir = _resolve_under_project(project_root, args.output_dir)
    registry_path = _resolve_under_project(project_root, args.registry)
    checkpoints = tuple(
        _resolve_under_project(project_root, path)
        for path in (args.checkpoint_0, args.checkpoint_1, args.checkpoint_2)
    )
    try:
        sources = [find_resolved_config(path) for path in checkpoints]
        protocols = [fingerprint(config) for _, config in sources]
        protocol_hashes = [sha256_json(protocol) for protocol in protocols]
        if len(set(protocol_hashes)) != 1:
            raise ExportError("Stage 2 BP checkpoints do not share one data protocol")

        config = copy.deepcopy(sources[0][1])
        training = section(config, "training")
        if int(training["batch_size"]) != EXPECTED_BATCH_SIZE:
            raise ExportError(
                f"registered batch size is {EXPECTED_BATCH_SIZE}, observed {training['batch_size']}"
            )
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
        batches: list[dict[str, Any]] = []
        content_digests: set[str] = set()
        reused_artifact_count = 0
        iterator = iter(bundle.validation)
        for batch_index in range(EXPECTED_BATCH_COUNT):
            try:
                raw = next(iterator)
            except StopIteration as error:
                raise ExportError("validation loader does not contain ten full batches") from error
            inputs, targets = _validate_batch(raw, batch_index=batch_index)
            content_sha256 = _content_digest(inputs, targets)
            if content_sha256 in content_digests:
                raise ExportError(f"validation batch content is duplicated at index {batch_index}")
            content_digests.add(content_sha256)
            artifact_path = output_dir / f"validation-batch-{batch_index:03d}.pt"
            manifest_path = output_dir / f"validation-batch-{batch_index:03d}.json"
            payload = {
                "inputs": inputs,
                "targets": targets,
                "split": "validation",
                "dataset": protocols[0]["data"]["dataset"],
                "batch_index": batch_index,
                "batch_size": EXPECTED_BATCH_SIZE,
                "content_sha256": content_sha256,
                "shared_across_lanes": ["cpu_float64", "rocm_float32"],
                "shared_across_methods": ["FixedPred", "Strict"],
                "shared_across_model_seeds": list(SEEDS),
                "selection_rule": (
                    "first ten full batches from the deterministic shuffle=False "
                    "validation loader reconstructed from the common Stage 2 BP "
                    "data protocol"
                ),
                "test_split_accessed": False,
            }
            if _write_or_verify_artifact(artifact_path, payload):
                reused_artifact_count += 1
            artifact_sha256 = sha256_file(artifact_path)
            manifest = {
                "schema_version": 1,
                "artifact_type": "stage3b_b1_confirmatory_validation_batch",
                "artifact_path": _relative_path(project_root, artifact_path),
                "artifact_sha256": artifact_sha256,
                "content_sha256": content_sha256,
                "dataset": protocols[0]["data"]["dataset"],
                "split": "validation",
                "batch_index": batch_index,
                "batch_size": EXPECTED_BATCH_SIZE,
                "inputs_shape": list(inputs.shape),
                "inputs_dtype": str(inputs.dtype),
                "targets_shape": list(targets.shape),
                "targets_dtype": str(targets.dtype),
                "include_test": False,
                "test_split_accessed": False,
                "common_data_protocol_sha256": protocol_hashes[0],
            }
            _write_or_verify_json(manifest_path, manifest)
            batches.append(
                {
                    "batch_index": batch_index,
                    "path": _relative_path(project_root, artifact_path),
                    "sha256": artifact_sha256,
                    "content_sha256": content_sha256,
                    "manifest_path": _relative_path(project_root, manifest_path),
                    "manifest_sha256": sha256_file(manifest_path),
                    "split": "validation",
                    "batch_size": EXPECTED_BATCH_SIZE,
                }
            )

        registry = {
            "schema_version": 1,
            "artifact_type": "stage3b_b1_confirmatory_validation_batch_registry",
            "dataset": protocols[0]["data"]["dataset"],
            "split": "validation",
            "batch_count": EXPECTED_BATCH_COUNT,
            "batch_size": EXPECTED_BATCH_SIZE,
            "batch_indices": list(range(EXPECTED_BATCH_COUNT)),
            "distinct_paths_required": True,
            "distinct_content_digests_required": True,
            "include_test": False,
            "test_split_accessed": False,
            "common_data_protocol": protocols[0],
            "common_data_protocol_sha256": protocol_hashes[0],
            "split_files": [_relative_path(project_root, path) for path in bundle.split_files],
            "split_sha256": dict(bundle.split_sha256),
            "sources": [
                {
                    "model_seed": seed,
                    "checkpoint_path": _relative_path(project_root, checkpoint),
                    "checkpoint_sha256": sha256_file(checkpoint),
                    "resolved_config_path": _relative_path(project_root, config_path),
                    "resolved_config_sha256": sha256_file(config_path),
                }
                for seed, checkpoint, (config_path, _) in zip(
                    SEEDS, checkpoints, sources, strict=True
                )
            ],
            "batches": batches,
        }
        registry["registry_digest"] = sha256_json(registry)
        _write_or_verify_json(registry_path, registry)
    except (ExportError, OSError, ValueError) as error:
        print(f"ERROR: {error}")
        return 2

    print("OK: ten distinct confirmatory validation batches exported")
    print(f"REGISTRY_PATH={_relative_path(project_root, registry_path)}")
    print(f"REGISTRY_SHA256={sha256_file(registry_path)}")
    print(f"BATCH_COUNT={len(batches)}")
    print(f"DISTINCT_CONTENT_DIGESTS={len(content_digests)}")
    print(f"REUSED_ARTIFACT_COUNT={reused_artifact_count}")
    print("TEST_SPLIT_ACCESSED=false")
    return 0


def _validate_batch(raw: object, *, batch_index: int) -> tuple[torch.Tensor, torch.Tensor]:
    if not isinstance(raw, tuple | list) or len(raw) < 2:
        raise ExportError(f"invalid validation batch structure at index {batch_index}")
    inputs, targets = raw[0], raw[1]
    if not torch.is_tensor(inputs) or not torch.is_tensor(targets):
        raise ExportError(f"validation batch {batch_index} lacks tensors")
    inputs = inputs.detach().cpu().contiguous()
    targets = targets.detach().cpu().contiguous()
    if inputs.shape[0] != EXPECTED_BATCH_SIZE or targets.shape[0] != EXPECTED_BATCH_SIZE:
        raise ExportError(
            f"validation batch {batch_index} is not a full {EXPECTED_BATCH_SIZE}-item batch"
        )
    return inputs, targets


def _content_digest(inputs: torch.Tensor, targets: torch.Tensor) -> str:
    digest = hashlib.sha256()
    for name, tensor in (("inputs", inputs), ("targets", targets)):
        digest.update(name.encode("utf-8"))
        digest.update(str(tensor.dtype).encode("utf-8"))
        digest.update(json.dumps(list(tensor.shape)).encode("utf-8"))
        digest.update(tensor.numpy().tobytes(order="C"))
    return digest.hexdigest()


def _write_or_verify_artifact(path: Path, payload: dict[str, Any]) -> bool:
    if path.exists():
        existing = torch.load(path, map_location="cpu", weights_only=False)
        if not isinstance(existing, dict):
            raise ExportError(f"existing artifact is not an object: {path}")
        for key in ("split", "batch_index", "batch_size", "content_sha256"):
            if existing.get(key) != payload[key]:
                raise ExportError(f"existing artifact metadata differs: {path} {key}")
        existing_inputs = existing.get("inputs")
        existing_targets = existing.get("targets")
        if not torch.is_tensor(existing_inputs) or not torch.is_tensor(existing_targets):
            raise ExportError(f"existing artifact tensors are missing: {path}")
        if not torch.equal(existing_inputs, payload["inputs"]):
            raise ExportError(f"existing artifact inputs differ: {path}")
        if not torch.equal(existing_targets, payload["targets"]):
            raise ExportError(f"existing artifact targets differ: {path}")
        return True
    atomic_save_torch(payload, path)
    return False


def _write_or_verify_json(path: Path, payload: dict[str, Any]) -> None:
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing != payload:
            raise ExportError(f"existing JSON artifact differs: {path}")
        return
    atomic_save_json(payload, path)


def _resolve_under_project(project_root: Path, path: Path) -> Path:
    resolved = (
        path.expanduser().resolve() if path.is_absolute() else (project_root / path).resolve()
    )
    try:
        resolved.relative_to(project_root)
    except ValueError as error:
        raise ExportError(f"path escapes project root: {path}") from error
    return resolved


def _relative_path(project_root: Path, path: Path) -> str:
    return path.resolve().relative_to(project_root).as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
