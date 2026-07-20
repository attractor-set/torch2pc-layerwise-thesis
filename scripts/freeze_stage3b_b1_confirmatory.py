#!/usr/bin/env python3
"""Freeze the 120-pair confirmatory EQ-B1 request from registered assets."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any, cast

import torch

from scripts.export_stage3b_b1_shared_validation_batch import (
    ExportError,
    atomic_save_json,
    find_resolved_config,
    fingerprint,
    sha256_file,
    sha256_json,
)
from torch2pc_thesis.stage3b_b1_confirmatory import (
    B1_CONFIRMATORY_CAMPAIGN_ID,
    B1_CONFIRMATORY_EXPECTED_BATCH_INDICES,
    B1_CONFIRMATORY_EXPECTED_LANES,
    B1_CONFIRMATORY_EXPECTED_METHODS,
    B1_CONFIRMATORY_EXPECTED_PAIR_COUNT,
    B1_CONFIRMATORY_EXPECTED_SEEDS,
    B1_CONFIRMATORY_MAX_ATTEMPTS,
    B1_CONFIRMATORY_REQUEST_SCOPE,
    validate_confirmatory_request,
)
from torch2pc_thesis.stage3b_b1_equivalence import canonical_json_digest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument(
        "--contract",
        type=Path,
        default=Path("experiments/planned/STAGE3B-B1-CONFIRMATORY-CONTRACT.json"),
    )
    parser.add_argument("--checkpoint-0", type=Path, required=True)
    parser.add_argument("--checkpoint-1", type=Path, required=True)
    parser.add_argument("--checkpoint-2", type=Path, required=True)
    parser.add_argument("--batch-registry", type=Path, required=True)
    parser.add_argument("--request-id", required=True)
    parser.add_argument("--run-seed-base", type=int, default=731000)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.project_root.expanduser().resolve()
    try:
        contract_path = _resolve_under_project(root, args.contract)
        registry_path = _resolve_under_project(root, args.batch_registry)
        output_path = _resolve_under_project(root, args.output)
        checkpoints = {
            seed: _resolve_under_project(root, path)
            for seed, path in zip(
                B1_CONFIRMATORY_EXPECTED_SEEDS,
                (args.checkpoint_0, args.checkpoint_1, args.checkpoint_2),
                strict=True,
            )
        }
        if args.run_seed_base < 0:
            raise ExportError("run seed base must be non-negative")

        contract = _load_object(contract_path)
        if contract.get("contract_id") != B1_CONFIRMATORY_CAMPAIGN_ID:
            raise ExportError("unexpected confirmatory contract id")
        contract_digest = canonical_json_digest(contract)

        sources = [
            find_resolved_config(checkpoints[seed]) for seed in B1_CONFIRMATORY_EXPECTED_SEEDS
        ]
        protocol_fingerprints = [fingerprint(config) for _, config in sources]
        if len({sha256_json(value) for value in protocol_fingerprints}) != 1:
            raise ExportError("checkpoints do not share one resolved data protocol")
        resolved_config = {
            "architecture": "lenet_classic",
            "dataset": "FashionMNIST",
            "split": "validation",
            "common_data_protocol": copy.deepcopy(protocol_fingerprints[0]),
            "training_mode": True,
            "optimizer": {
                "name": "SGD",
                "learning_rate": 0.001,
                "momentum": 0.0,
            },
            "method_controls": copy.deepcopy(contract["method_controls"]),
            "lane_controls": {
                "cpu_float64": {"device": "cpu", "dtype": "float64"},
                "rocm_float32": {"device": "cuda", "dtype": "float32"},
            },
        }
        resolved_config_digest = canonical_json_digest(resolved_config)

        registry = _load_object(registry_path)
        batches = _validate_batch_registry(
            registry,
            root=root,
            checkpoints=checkpoints,
            sources=sources,
        )
        checkpoint_records = {
            str(seed): {
                "path": _relative(root, checkpoints[seed]),
                "sha256": sha256_file(checkpoints[seed]),
                "resolved_config_path": _relative(root, sources[index][0]),
                "resolved_config_sha256": sha256_file(sources[index][0]),
            }
            for index, seed in enumerate(B1_CONFIRMATORY_EXPECTED_SEEDS)
        }
        request: dict[str, Any] = {
            "schema_version": 1,
            "request_scope": B1_CONFIRMATORY_REQUEST_SCOPE,
            "campaign_id": B1_CONFIRMATORY_CAMPAIGN_ID,
            "request_id": args.request_id,
            "scope": "confirmatory",
            "dataset": "FashionMNIST",
            "split": "validation",
            "architecture": "lenet_classic",
            "lanes": list(B1_CONFIRMATORY_EXPECTED_LANES),
            "methods": list(B1_CONFIRMATORY_EXPECTED_METHODS),
            "model_seeds": list(B1_CONFIRMATORY_EXPECTED_SEEDS),
            "validation_batch_indices": list(B1_CONFIRMATORY_EXPECTED_BATCH_INDICES),
            "matched_pair_count": B1_CONFIRMATORY_EXPECTED_PAIR_COUNT,
            "observer_mode": "no_hooks",
            "structural_observer_mode": "counters_only",
            "test_split_access": False,
            "training_mode": True,
            "max_attempts_per_pair": B1_CONFIRMATORY_MAX_ATTEMPTS,
            "torch2pc_commit": str(contract["preregistration_base"]["torch2pc_commit"]),
            "contract_path": _relative(root, contract_path),
            "contract_digest": contract_digest,
            "batch_registry_path": _relative(root, registry_path),
            "batch_registry_sha256": sha256_file(registry_path),
            "batch_registry_digest": str(registry["registry_digest"]),
            "resolved_config": resolved_config,
            "resolved_config_digest": resolved_config_digest,
            "run_seed_base": args.run_seed_base,
            "optimizer": {
                "name": "SGD",
                "learning_rate": 0.001,
                "momentum": 0.0,
            },
            "method_controls": cast(dict[str, object], contract["method_controls"]),
            "lane_controls": {
                "cpu_float64": {"device": "cpu", "dtype": "float64"},
                "rocm_float32": {"device": "cuda", "dtype": "float32"},
            },
            "checkpoints": checkpoint_records,
            "validation_batches": batches,
            "execution_boundary": {
                "request_frozen": True,
                "runtime_authorization_issued": False,
                "execution_started": False,
                "results_present": False,
                "eq_b1_confirmatory_sealed": False,
                "matched_profiling_open": False,
            },
            "evidence": False,
            "results_publication_permitted": False,
        }
        validate_confirmatory_request(request)
        request_digest = canonical_json_digest(request)
        _write_or_verify_request(output_path, request)
    except (ExportError, OSError, ValueError, KeyError, TypeError) as error:
        print(f"ERROR: {error}")
        return 2

    print("OK: confirmatory EQ-B1 request frozen")
    print(f"REQUEST_PATH={_relative(root, output_path)}")
    print(f"REQUEST_SHA256={sha256_file(output_path)}")
    print(f"REQUEST_DIGEST={request_digest}")
    print(f"PAIR_COUNT={request['matched_pair_count']}")
    print("EXECUTION_PERMITTED=false")
    print("EVIDENCE=false")
    return 0


def _validate_batch_registry(
    registry: dict[str, Any],
    *,
    root: Path,
    checkpoints: dict[int, Path],
    sources: list[tuple[Path, dict[str, Any]]],
) -> dict[str, dict[str, object]]:
    expected = {
        "schema_version": 1,
        "artifact_type": "stage3b_b1_confirmatory_validation_batch_registry",
        "dataset": "FashionMNIST",
        "split": "validation",
        "batch_count": 10,
        "batch_size": 256,
        "batch_indices": list(range(10)),
        "distinct_paths_required": True,
        "distinct_content_digests_required": True,
        "include_test": False,
        "test_split_accessed": False,
    }
    for key, value in expected.items():
        if registry.get(key) != value:
            raise ExportError(f"batch registry mismatch for {key}")
    supplied_digest = registry.get("registry_digest")
    if not isinstance(supplied_digest, str):
        raise ExportError("batch registry digest is missing")
    unsigned = dict(registry)
    unsigned.pop("registry_digest", None)
    if sha256_json(unsigned) != supplied_digest:
        raise ExportError("batch registry digest mismatch")

    _validate_registry_sources(
        registry.get("sources"),
        root=root,
        checkpoints=checkpoints,
        sources=sources,
    )

    raw_batches = registry.get("batches")
    if not isinstance(raw_batches, list) or len(raw_batches) != 10:
        raise ExportError("batch registry must contain ten batch records")
    result: dict[str, dict[str, object]] = {}
    paths: set[str] = set()
    manifest_paths: set[str] = set()
    content: set[str] = set()
    for expected_index, raw in enumerate(raw_batches):
        if not isinstance(raw, dict):
            raise ExportError("batch record must be an object")
        if raw.get("batch_index") != expected_index:
            raise ExportError("batch registry order/index mismatch")
        path_value = raw.get("path")
        digest = raw.get("sha256")
        content_digest = raw.get("content_sha256")
        manifest_value = raw.get("manifest_path")
        manifest_digest = raw.get("manifest_sha256")
        if not isinstance(path_value, str) or not isinstance(digest, str):
            raise ExportError("batch path/digest is missing")
        if not isinstance(content_digest, str):
            raise ExportError("batch content digest is missing")
        if not isinstance(manifest_value, str) or not isinstance(manifest_digest, str):
            raise ExportError("batch manifest path/digest is missing")

        artifact_path = _resolve_under_project(root, Path(path_value))
        manifest_path = _resolve_under_project(root, Path(manifest_value))
        if not artifact_path.is_file() or sha256_file(artifact_path) != digest:
            raise ExportError(f"batch artifact mismatch: {artifact_path}")
        if not manifest_path.is_file() or sha256_file(manifest_path) != manifest_digest:
            raise ExportError(f"batch manifest mismatch: {manifest_path}")

        artifact = torch.load(artifact_path, map_location="cpu", weights_only=False)
        if not isinstance(artifact, dict):
            raise ExportError(f"batch artifact is not an object: {artifact_path}")
        raw_inputs = artifact.get("inputs")
        raw_targets = artifact.get("targets")
        if not torch.is_tensor(raw_inputs) or not torch.is_tensor(raw_targets):
            raise ExportError(f"batch artifact lacks tensors: {artifact_path}")
        inputs = cast(torch.Tensor, raw_inputs)
        targets = cast(torch.Tensor, raw_targets)
        if inputs.shape[0] != 256 or targets.shape[0] != 256:
            raise ExportError(f"batch artifact is not a full batch: {artifact_path}")
        computed_content_digest = _tensor_content_digest(inputs, targets)
        artifact_expected = {
            "split": "validation",
            "batch_index": expected_index,
            "batch_size": 256,
            "content_sha256": content_digest,
            "test_split_accessed": False,
        }
        for key, value in artifact_expected.items():
            if artifact.get(key) != value:
                raise ExportError(f"batch artifact metadata mismatch: {artifact_path} {key}")
        if computed_content_digest != content_digest:
            raise ExportError(f"batch content digest mismatch: {artifact_path}")

        manifest = _load_object(manifest_path)
        manifest_expected = {
            "schema_version": 1,
            "artifact_type": "stage3b_b1_confirmatory_validation_batch",
            "artifact_path": path_value,
            "artifact_sha256": digest,
            "content_sha256": content_digest,
            "dataset": "FashionMNIST",
            "split": "validation",
            "batch_index": expected_index,
            "batch_size": 256,
            "include_test": False,
            "test_split_accessed": False,
        }
        for key, value in manifest_expected.items():
            if manifest.get(key) != value:
                raise ExportError(f"batch manifest metadata mismatch: {manifest_path} {key}")

        paths.add(path_value)
        manifest_paths.add(manifest_value)
        content.add(content_digest)
        result[str(expected_index)] = {
            "path": path_value,
            "sha256": digest,
            "content_sha256": content_digest,
            "manifest_path": manifest_value,
            "manifest_sha256": manifest_digest,
            "batch_index": expected_index,
            "split": "validation",
            "batch_size": 256,
        }
    if len(paths) != 10 or len(manifest_paths) != 10 or len(content) != 10:
        raise ExportError("batch registry does not contain ten distinct batches")
    return result


def _validate_registry_sources(
    raw_sources: object,
    *,
    root: Path,
    checkpoints: dict[int, Path],
    sources: list[tuple[Path, dict[str, Any]]],
) -> None:
    if not isinstance(raw_sources, list) or len(raw_sources) != 3:
        raise ExportError("batch registry must contain three checkpoint sources")
    for position, seed in enumerate(B1_CONFIRMATORY_EXPECTED_SEEDS):
        raw = raw_sources[position]
        if not isinstance(raw, dict):
            raise ExportError("batch registry source must be an object")
        checkpoint = checkpoints[seed]
        config_path = sources[position][0]
        expected = {
            "model_seed": seed,
            "checkpoint_path": _relative(root, checkpoint),
            "checkpoint_sha256": sha256_file(checkpoint),
            "resolved_config_path": _relative(root, config_path),
            "resolved_config_sha256": sha256_file(config_path),
        }
        for key, value in expected.items():
            if raw.get(key) != value:
                raise ExportError(f"batch registry source mismatch: seed={seed} {key}")


def _tensor_content_digest(inputs: torch.Tensor, targets: torch.Tensor) -> str:
    digest = hashlib.sha256()
    for name, tensor in (("inputs", inputs), ("targets", targets)):
        value = tensor.detach().cpu().contiguous()
        digest.update(name.encode("utf-8"))
        digest.update(str(value.dtype).encode("utf-8"))
        digest.update(json.dumps(list(value.shape)).encode("utf-8"))
        digest.update(value.numpy().tobytes(order="C"))
    return digest.hexdigest()


def _write_or_verify_request(path: Path, request: dict[str, Any]) -> None:
    if path.exists():
        existing = _load_object(path)
        if existing != request:
            raise ExportError(f"existing frozen request differs: {path}")
        return
    atomic_save_json(request, path)


def _load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ExportError(f"JSON root must be an object: {path}")
    return cast(dict[str, Any], value)


def _resolve_under_project(root: Path, path: Path) -> Path:
    resolved = path.expanduser().resolve() if path.is_absolute() else (root / path).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise ExportError(f"path escapes project root: {path}") from error
    return resolved


def _relative(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
