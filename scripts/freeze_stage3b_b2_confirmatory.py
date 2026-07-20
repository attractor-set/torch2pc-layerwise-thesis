#!/usr/bin/env python3
"""Freeze the 120-triple confirmatory EQ-B2 request from registered assets."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any, cast

from torch2pc_thesis.stage3b_b1_equivalence import (
    atomic_write_json,
    canonical_json_digest,
    sha256_file,
)
from torch2pc_thesis.stage3b_b2_confirmatory import (
    B2_CONFIRMATORY_CAMPAIGN_ID,
    B2_CONFIRMATORY_EXPECTED_BATCH_INDICES,
    B2_CONFIRMATORY_EXPECTED_COMPARISON_COUNT,
    B2_CONFIRMATORY_EXPECTED_LANES,
    B2_CONFIRMATORY_EXPECTED_METHODS,
    B2_CONFIRMATORY_EXPECTED_SEEDS,
    B2_CONFIRMATORY_EXPECTED_TRIPLE_COUNT,
    B2_CONFIRMATORY_MAX_ATTEMPTS,
    B2_CONFIRMATORY_REQUEST_SCOPE,
    validate_confirmatory_request,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument(
        "--contract",
        type=Path,
        default=Path(
            "experiments/planned/STAGE3B-B2-CONFIRMATORY-CONTRACT.json"
        ),
    )
    parser.add_argument(
        "--b1-request",
        type=Path,
        default=Path("experiments/frozen/stage3b-b1-confirmatory/request.json"),
    )
    parser.add_argument(
        "--b1-batch-registry",
        type=Path,
        default=Path(
            "experiments/frozen/stage3b-b1-confirmatory/validation-batches.json"
        ),
    )
    parser.add_argument(
        "--b1-decision",
        type=Path,
        default=Path(
            "results/stage-3/b1/stage3b-b1-confirmatory-ceebdce-v1/decision.json"
        ),
    )
    parser.add_argument(
        "--b1-admission",
        type=Path,
        default=Path(
            "results/stage-3/b1/stage3b-b1-confirmatory-ceebdce-v1/"
            "matched-profiling-admission.json"
        ),
    )
    parser.add_argument(
        "--b2-candidate-contract",
        type=Path,
        default=Path("experiments/planned/STAGE3B-B2-CONTRACT.json"),
    )
    parser.add_argument(
        "--b2-implementation-contract",
        type=Path,
        default=Path(
            "experiments/planned/STAGE3B-B2-IMPLEMENTATION-CONTRACT.json"
        ),
    )
    parser.add_argument(
        "--b2-harness-contract",
        type=Path,
        default=Path(
            "experiments/planned/STAGE3B-B2-SMOKE-HARNESS-CONTRACT.json"
        ),
    )
    parser.add_argument("--request-id", required=True)
    parser.add_argument("--run-seed-base", type=int, default=732000)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.project_root.expanduser().resolve()
    try:
        paths = {
            "contract": _resolve_under_project(root, args.contract),
            "b1_request": _resolve_under_project(root, args.b1_request),
            "b1_batch_registry": _resolve_under_project(
                root,
                args.b1_batch_registry,
            ),
            "b1_decision": _resolve_under_project(root, args.b1_decision),
            "b1_admission": _resolve_under_project(root, args.b1_admission),
            "b2_candidate_contract": _resolve_under_project(
                root,
                args.b2_candidate_contract,
            ),
            "b2_implementation_contract": _resolve_under_project(
                root,
                args.b2_implementation_contract,
            ),
            "b2_harness_contract": _resolve_under_project(
                root,
                args.b2_harness_contract,
            ),
        }
        output_path = _resolve_under_project(root, args.output)
        if args.run_seed_base < 0:
            raise ValueError("run seed base must be non-negative")

        contract = _load_object(paths["contract"])
        if contract.get("contract_id") != B2_CONFIRMATORY_CAMPAIGN_ID:
            raise ValueError("unexpected B2 confirmatory contract id")
        b1_request = _load_object(paths["b1_request"])
        if b1_request.get("campaign_id") != "stage3b-b1-confirmatory-equivalence-v1":
            raise ValueError("unexpected B1 confirmatory request")
        if b1_request.get("test_split_access") is not False:
            raise ValueError("B1 request must keep the test split closed")
        if b1_request.get("validation_batch_indices") != list(range(10)):
            raise ValueError("B1 request must contain validation batches 0 through 9")

        prereg = cast(dict[str, Any], contract["preregistration_base"])
        input_reuse = cast(dict[str, Any], contract["input_reuse"])
        _verify_registered_digest(
            paths["b1_request"],
            cast(dict[str, Any], input_reuse["b1_frozen_request"]),
        )
        _verify_registered_digest(
            paths["b1_batch_registry"],
            cast(dict[str, Any], input_reuse["validation_batch_registry"]),
        )
        _verify_registered_digest(
            paths["b1_decision"],
            cast(dict[str, Any], prereg["b1_confirmatory_decision"]),
        )
        _verify_registered_digest(
            paths["b1_admission"],
            cast(dict[str, Any], prereg["b1_confirmatory_admission"]),
        )
        _verify_registered_digest(
            paths["b2_candidate_contract"],
            cast(dict[str, Any], prereg["b2_candidate_contract"]),
        )
        _verify_registered_digest(
            paths["b2_implementation_contract"],
            cast(dict[str, Any], prereg["b2_implementation_contract"]),
        )

        resolved_config = {
            "architecture": "lenet_classic",
            "dataset": "FashionMNIST",
            "split": "validation",
            "training_mode": True,
            "candidate_id": "composite_vjp",
            "control_candidate_id": "isolated_layer_vjp",
            "reference_id": "stage2_baseline",
            "optimizer": copy.deepcopy(contract["optimizer"]),
            "method_controls": copy.deepcopy(contract["method_controls"]),
            "lane_controls": {
                "cpu_float64": {"device": "cpu", "dtype": "float64"},
                "rocm_float32": {"device": "cuda", "dtype": "float32"},
            },
            "b1_resolved_config_digest": b1_request["resolved_config_digest"],
        }
        request: dict[str, Any] = {
            "schema_version": 1,
            "request_scope": B2_CONFIRMATORY_REQUEST_SCOPE,
            "campaign_id": B2_CONFIRMATORY_CAMPAIGN_ID,
            "request_id": args.request_id,
            "scope": "confirmatory",
            "dataset": "FashionMNIST",
            "split": "validation",
            "architecture": "lenet_classic",
            "lanes": list(B2_CONFIRMATORY_EXPECTED_LANES),
            "methods": list(B2_CONFIRMATORY_EXPECTED_METHODS),
            "model_seeds": list(B2_CONFIRMATORY_EXPECTED_SEEDS),
            "validation_batch_indices": list(
                B2_CONFIRMATORY_EXPECTED_BATCH_INDICES
            ),
            "matched_triple_count": B2_CONFIRMATORY_EXPECTED_TRIPLE_COUNT,
            "pairwise_comparison_count": (
                B2_CONFIRMATORY_EXPECTED_COMPARISON_COUNT
            ),
            "candidate_id": "composite_vjp",
            "control_candidate_id": "isolated_layer_vjp",
            "reference_id": "stage2_baseline",
            "observer_mode": "no_hooks",
            "structural_observer_mode": "counters_only",
            "test_split_access": False,
            "dangerous_miss_limit": 0,
            "training_mode": True,
            "max_attempts_per_triple": B2_CONFIRMATORY_MAX_ATTEMPTS,
            "torch2pc_commit": str(prereg["torch2pc_commit"]),
            "contract_path": _relative(root, paths["contract"]),
            "contract_digest": canonical_json_digest(contract),
            "resolved_config": resolved_config,
            "resolved_config_digest": canonical_json_digest(resolved_config),
            "run_seed_base": args.run_seed_base,
            "optimizer": copy.deepcopy(contract["optimizer"]),
            "method_controls": copy.deepcopy(contract["method_controls"]),
            "lane_controls": {
                "cpu_float64": {"device": "cpu", "dtype": "float64"},
                "rocm_float32": {"device": "cuda", "dtype": "float32"},
            },
            "checkpoints": copy.deepcopy(b1_request["checkpoints"]),
            "validation_batches": copy.deepcopy(
                b1_request["validation_batches"]
            ),
            "b1_confirmatory_decision": _asset(root, paths["b1_decision"]),
            "b1_admission": _asset(root, paths["b1_admission"]),
            "b1_frozen_request": _asset(root, paths["b1_request"]),
            "b1_batch_registry": _asset(root, paths["b1_batch_registry"]),
            "b2_confirmatory_contract": _asset(root, paths["contract"]),
            "b2_candidate_contract": _asset(
                root,
                paths["b2_candidate_contract"],
            ),
            "b2_implementation_contract": _asset(
                root,
                paths["b2_implementation_contract"],
            ),
            "b2_harness_contract": _asset(
                root,
                paths["b2_harness_contract"],
            ),
            "execution_boundary": {
                "request_frozen": True,
                "runtime_authorization_issued": False,
                "execution_started": False,
                "results_present": False,
                "eq_b2_confirmatory_sealed": False,
                "derived_eq_b2_admission_present": False,
                "matched_profiling_refrozen": False,
                "matched_profiling_execution_open": False,
            },
            "evidence": False,
            "results_publication_permitted": False,
        }
        validate_confirmatory_request(request)
        request_digest = canonical_json_digest(request)
        _write_or_verify_request(output_path, request)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"ERROR: {error}")
        return 2

    print("OK: confirmatory EQ-B2 request frozen")
    print(f"REQUEST_PATH={_relative(root, output_path)}")
    print(f"REQUEST_SHA256={sha256_file(output_path)}")
    print(f"REQUEST_DIGEST={request_digest}")
    print(f"TRIPLE_COUNT={request['matched_triple_count']}")
    print(f"COMPARISON_COUNT={request['pairwise_comparison_count']}")
    print("EXECUTION_PERMITTED=false")
    print("EVIDENCE=false")
    return 0


def _verify_registered_digest(path: Path, record: dict[str, Any]) -> None:
    expected_path = record.get("path")
    expected_digest = record.get("sha256")
    if not isinstance(expected_path, str) or not isinstance(expected_digest, str):
        raise ValueError("registered path/digest is missing")
    if sha256_file(path) != expected_digest:
        raise ValueError(f"registered digest mismatch: {path}")


def _asset(root: Path, path: Path) -> dict[str, str]:
    return {"path": _relative(root, path), "sha256": sha256_file(path)}


def _write_or_verify_request(path: Path, request: dict[str, Any]) -> None:
    if path.exists():
        existing = _load_object(path)
        if existing != request:
            raise ValueError(f"append-only request already differs: {path}")
        return
    atomic_write_json(path, request)


def _load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return cast(dict[str, Any], value)


def _resolve_under_project(root: Path, path: Path) -> Path:
    candidate = path.expanduser()
    resolved = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise ValueError(f"path escapes project root: {path}") from error
    return resolved


def _relative(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
