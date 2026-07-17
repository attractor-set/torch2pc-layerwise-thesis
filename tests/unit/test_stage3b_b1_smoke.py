from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from torch2pc_thesis.stage3b_b1_equivalence import canonical_json_digest
from torch2pc_thesis.stage3b_b1_smoke import (
    aggregate_attempt,
    build_pair_specs,
    validate_request,
)


def _sha() -> str:
    return "a" * 64


def _request() -> dict[str, Any]:
    resolved_config = {
        "dataset": "FashionMNIST",
        "architecture": "lenet_classic",
        "split": "validation",
    }
    asset = {"path": "placeholder.pt", "sha256": _sha()}
    return {
        "schema_version": 1,
        "request_id": "stage3b-b1-smoke-v1",
        "attempt_id": "attempt-001",
        "scope": "smoke",
        "dataset": "FashionMNIST",
        "split": "validation",
        "architecture": "lenet_classic",
        "methods": ["FixedPred", "Strict"],
        "model_seeds": [0, 1, 2],
        "batches_per_seed": 1,
        "lanes": ["cpu_float64", "rocm_float32"],
        "observer_mode": "no_hooks",
        "structural_observer_mode": "counters_only",
        "test_split_access": False,
        "dangerous_miss_limit": 0,
        "torch2pc_commit": "b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4",
        "project_base_commit": "542d1dd10cfbc96746c2925c025e3f5311e753db",
        "b1_implementation_commit": "ec12e9a",
        "resolved_config": resolved_config,
        "resolved_config_digest": canonical_json_digest(resolved_config),
        "source_image_digest": _sha(),
        "run_seed_base": 1000,
        "training_mode": True,
        "optimizer": {"name": "SGD", "learning_rate": 0.001, "momentum": 0.0},
        "lane_controls": {
            "cpu_float64": {"device": "cpu", "dtype": "float64"},
            "rocm_float32": {"device": "cuda", "dtype": "float32"},
        },
        "method_controls": {
            "FixedPred": {"eta": 0.1, "inference_steps": 3},
            "Strict": {"eta": 0.05, "inference_steps": 3},
        },
        "checkpoints": {"0": asset, "1": asset, "2": asset},
        "batches": {"0": asset, "1": asset, "2": asset},
    }


def test_request_resolves_exactly_twelve_pairs() -> None:
    request = _request()
    validate_request(request)
    specs = build_pair_specs(request)
    assert len(specs) == 12
    assert len({spec.pair_id for spec in specs}) == 12


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("split", "test"),
        ("test_split_access", True),
        ("methods", ["Strict", "FixedPred"]),
        ("model_seeds", [0, 1]),
    ],
)
def test_request_rejects_scope_drift(field: str, value: object) -> None:
    request = _request()
    request[field] = value
    with pytest.raises(ValueError):
        validate_request(request)


def test_request_rejects_resolved_config_digest_mismatch() -> None:
    request = _request()
    request["resolved_config_digest"] = "b" * 64
    with pytest.raises(ValueError, match="resolved_config_digest"):
        validate_request(request)


def test_aggregate_requires_all_twelve_pairs_and_writes_registered_layout(
    tmp_path: Path,
) -> None:
    request = _request()
    specs = build_pair_specs(request)
    attempt_root = tmp_path / str(request["attempt_id"])
    for spec in specs:
        pair_root = attempt_root / "pairs" / spec.pair_id
        pair_root.mkdir(parents=True)
        (pair_root / "pair.json").write_text(
            json.dumps(
                {
                    "pair_id": spec.pair_id,
                    "pair_admissible": True,
                    "gates": {
                        gate: {"passed": True, "reasons": []}
                        for gate in (
                            "STRUCT-B1",
                            "NUM-B1",
                            "TRAJ-B1",
                            "OBS-B1",
                            "PROV-B1",
                        )
                    },
                }
            ),
            encoding="utf-8",
        )
        for filename in ("trajectory-metrics.csv", "endpoint-metrics.csv"):
            with (pair_root / filename).open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=["pair_id", "component", "passed"])
                writer.writeheader()
                writer.writerow(
                    {"pair_id": spec.pair_id, "component": "x", "passed": True}
                )
        (pair_root / "structural-events.jsonl").write_text(
            json.dumps({"candidate_id": "isolated_layer_vjp"}) + "\n",
            encoding="utf-8",
        )

    decision = aggregate_attempt(request, attempt_root)
    assert decision["status"] == "pass"
    required = {
        "request.json",
        "resolved-config.json",
        "trajectory-metrics.csv",
        "endpoint-metrics.csv",
        "structural-events.jsonl",
        "decision.json",
        "SHA256SUMS",
    }
    assert required <= {path.name for path in attempt_root.iterdir()}
    sums = (attempt_root / "SHA256SUMS").read_text(encoding="utf-8")
    assert hashlib.sha256((attempt_root / "decision.json").read_bytes()).hexdigest() in sums


def test_aggregate_refuses_incomplete_attempt(tmp_path: Path) -> None:
    request = _request()
    attempt_root = tmp_path / str(request["attempt_id"])
    attempt_root.mkdir(parents=True)
    with pytest.raises(RuntimeError, match="Incomplete smoke attempt"):
        aggregate_attempt(request, attempt_root)
