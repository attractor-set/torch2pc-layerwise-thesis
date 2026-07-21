from __future__ import annotations

import copy
import shutil
from collections import Counter, defaultdict
from itertools import permutations
from pathlib import Path
from typing import cast

import pytest

from torch2pc_thesis.stage3b_execution import generate_manifest
from torch2pc_thesis.stage3b_matched_profiling import (
    MATCHED_PROFILING_EXPECTED_CELL_COUNT,
    MatchedProfilingError,
    build_matched_manifest,
    decision_ids,
    validate_matched_manifest,
    validate_matched_prelaunch_scientific_gate,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _contract(candidate_id: str) -> dict[str, object]:
    return {
        "candidate": {"candidate_id": candidate_id},
        "profiling_scope": {
            "lane": {"device": "rocm", "dtype": "float32"},
            "family": "controlled MLP",
            "methods": ["FixedPred", "Strict"],
            "depth": [4, 8, 16, 32],
            "width": [64, 256],
            "batch_size": [64, 256],
            "model_seeds": [70, 71, 72],
            "cells_per_candidate": 96,
            "measurement_lanes": {
                "primary_timing": {"observer_mode": "no_hooks"},
                "structural_counters": {"observer_mode": "counters_only"},
            },
            "cost_vector": ["device_time_ns", "wall_time_ns"],
        },
        "gate_hierarchy": {
            "matched_profiling_open_rule": (
                "both B1 and B2 equivalence evidence are sealed"
            )
        },
        "future_policy_boundary": {
            "estimator_present": False,
            "oracle_branching_present": False,
            "cheap_diagnostic_loop_present": False,
            "hysteresis_policy_present": False,
            "offline_trace_collection_present": False,
        },
    }


def test_build_matched_manifest_selects_288_cells() -> None:
    manifest = build_matched_manifest(
        generate_manifest(),
        _contract("isolated_layer_vjp"),
        _contract("composite_vjp"),
    )

    validate_matched_manifest(manifest)
    assert manifest["selected_cell_count"] == MATCHED_PROFILING_EXPECTED_CELL_COUNT
    assert manifest["candidate_counts"] == {
        "composite_vjp": 96,
        "isolated_layer_vjp": 96,
        "stage2_baseline": 96,
    }
    assert manifest["method_counts"] == {"fixedpred": 144, "strict": 144}
    assert manifest["execution_performed"] is False
    assert manifest["test_dataset_access"] is False
    assert manifest["full_stage3b_campaign_complete"] is False

    cells = cast(list[dict[str, object]], manifest["cells"])
    assert all(cell["matched_profiling_eligible"] is True for cell in cells)
    assert all(cell["candidate_gate_status"] == "equivalence_gate_passed" for cell in cells)

    by_method_and_block: defaultdict[
        str, defaultdict[str, list[dict[str, object]]]
    ] = defaultdict(lambda: defaultdict(list))
    for cell in cells:
        by_method_and_block[str(cell["method"])][str(cell["block_id"])].append(cell)
    expected_permutations = set(
        permutations(("stage2_baseline", "isolated_layer_vjp", "composite_vjp"))
    )
    for blocks in by_method_and_block.values():
        permutation_counts: Counter[tuple[str, ...]] = Counter()
        position_counts: Counter[tuple[str, int]] = Counter()
        for block_cells in blocks.values():
            ordered = sorted(block_cells, key=lambda cell: int(cell["candidate_order"]))
            permutation = tuple(str(cell["candidate_id"]) for cell in ordered)
            permutation_counts[permutation] += 1
            for position, candidate_id in enumerate(permutation):
                position_counts[(candidate_id, position)] += 1
        assert set(permutation_counts) == expected_permutations
        assert set(permutation_counts.values()) == {8}
        assert set(position_counts.values()) == {16}


def test_build_matched_manifest_rejects_scope_drift() -> None:
    b2 = _contract("composite_vjp")
    cast(dict[str, object], b2["profiling_scope"])["model_seeds"] = [70]

    with pytest.raises(MatchedProfilingError, match="profiling scopes differ"):
        build_matched_manifest(
            generate_manifest(),
            _contract("isolated_layer_vjp"),
            b2,
        )


def test_build_matched_manifest_rejects_future_policy_enablement() -> None:
    b1 = _contract("isolated_layer_vjp")
    cast(dict[str, object], b1["future_policy_boundary"])["estimator_present"] = True

    with pytest.raises(MatchedProfilingError, match="estimator_present"):
        build_matched_manifest(
            generate_manifest(),
            b1,
            _contract("composite_vjp"),
        )


def test_validate_matched_manifest_rejects_digest_change() -> None:
    manifest = build_matched_manifest(
        generate_manifest(),
        _contract("isolated_layer_vjp"),
        _contract("composite_vjp"),
    )
    changed = copy.deepcopy(manifest)
    changed["status"] = "changed"

    with pytest.raises(MatchedProfilingError, match="digest"):
        validate_matched_manifest(changed)


def test_decision_ids_preserves_stable_order() -> None:
    records = ({"decision_id": "EQ-B1"}, {"decision_id": "EQ-B2"})
    assert decision_ids(records) == ("EQ-B1", "EQ-B2")


def test_paths_are_not_used_by_manifest_builder(tmp_path: Path) -> None:
    assert not list(tmp_path.iterdir())
    manifest = build_matched_manifest(
        generate_manifest(),
        _contract("isolated_layer_vjp"),
        _contract("composite_vjp"),
    )
    assert manifest["evidence"] is False
    assert not list(tmp_path.iterdir())


def _decision(decision_id: str) -> dict[str, object]:
    suffix = decision_id.removeprefix("EQ-")
    failure_field = "failed_pairs" if suffix == "B1" else "failed_triples"
    decision: dict[str, object] = {
        "decision_id": decision_id,
        "scope": "confirmatory",
        "confirmatory_equivalence_executed": True,
        "status": "pass",
        "sealed": True,
        "failed_pairs": [],
        "candidate_id": {
            "B1": "isolated_layer_vjp",
            "B2": "composite_vjp",
        }[suffix],
        "control_id": {
            "B1": "stage2_baseline",
            "B2": "isolated_layer_vjp",
        }[suffix],
        "gates": {
            f"NUM-{suffix}": {"passed": True, failure_field: []},
            f"OBS-{suffix}": {"passed": True, failure_field: []},
        },
    }
    if suffix == "B2":
        decision["failed_triples"] = []
    return decision


def _confirmatory_decision(decision_id: str) -> dict[str, object]:
    decision = _decision(decision_id)
    decision["scope"] = "confirmatory"
    decision["confirmatory_equivalence_executed"] = True
    if decision_id == "EQ-B1":
        decision["matched_pairs_expected"] = 120
        decision["matched_pairs_observed"] = 120
    else:
        decision["matched_triples_expected"] = 120
        decision["matched_triples_observed"] = 120
        decision["pairwise_comparisons_expected"] = 240
        decision["pairwise_comparisons_observed"] = 240
    return decision


def _write_json(path: Path, payload: object) -> None:
    import json

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _historical_paths(tmp_path: Path) -> tuple[Path, Path]:
    target_root = tmp_path / "experiments/planned"
    target_root.mkdir(parents=True, exist_ok=True)
    request = target_root / "STAGE3B-B1-B2-MATCHED-PROFILING-REQUEST.json"
    manifest = target_root / "STAGE3B-B1-B2-MATCHED-PROFILING-MANIFEST.json"
    shutil.copyfile(
        PROJECT_ROOT
        / "experiments/planned/STAGE3B-B1-B2-MATCHED-PROFILING-REQUEST.json",
        request,
    )
    shutil.copyfile(
        PROJECT_ROOT
        / "experiments/planned/STAGE3B-B1-B2-MATCHED-PROFILING-MANIFEST.json",
        manifest,
    )
    return request, manifest


def test_build_matched_request_binds_positive_sealed_decisions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from torch2pc_thesis import stage3b_matched_profiling as matched

    monkeypatch.setattr(matched, "require_opening_base_ancestor", lambda _root: None)

    base_manifest = generate_manifest()
    b1_contract = _contract("isolated_layer_vjp")
    b2_contract = _contract("composite_vjp")
    b1_decision = _decision("EQ-B1")
    b2_decision = _decision("EQ-B2")
    matched_manifest = build_matched_manifest(base_manifest, b1_contract, b2_contract)

    base_path = tmp_path / "experiments/planned/STAGE3B-EXECUTION-MANIFEST.json"
    b1_contract_path = tmp_path / "experiments/planned/STAGE3B-B1-CONTRACT.json"
    b2_contract_path = tmp_path / "experiments/planned/STAGE3B-B2-CONTRACT.json"
    b1_decision_path = tmp_path / "results/b1/decision.json"
    b2_decision_path = tmp_path / "results/b2/decision.json"
    matched_path = tmp_path / "experiments/planned/matched.json"
    historical_request_path, historical_manifest_path = _historical_paths(tmp_path)

    for path, payload in (
        (base_path, base_manifest),
        (b1_contract_path, b1_contract),
        (b2_contract_path, b2_contract),
        (b1_decision_path, b1_decision),
        (b2_decision_path, b2_decision),
    ):
        _write_json(path, payload)

    request = matched.build_matched_request(
        project_root=tmp_path,
        base_manifest_path=base_path,
        b1_contract_path=b1_contract_path,
        b2_contract_path=b2_contract_path,
        b1_decision_path=b1_decision_path,
        b2_decision_path=b2_decision_path,
        matched_manifest_path=matched_path,
        historical_request_path=historical_request_path,
        historical_manifest_path=historical_manifest_path,
        base_manifest=base_manifest,
        b1_contract=b1_contract,
        b2_contract=b2_contract,
        b1_decision=b1_decision,
        b2_decision=b2_decision,
        matched_manifest=matched_manifest,
    )

    matched.validate_matched_request(request)
    decisions = cast(list[dict[str, object]], request["prerequisite_decisions"])
    assert decision_ids(decisions) == ("EQ-B1", "EQ-B2")
    assert request["scientific_admission"] == "open"
    assert request["runtime_authorization"] == "not_issued"
    assert request["measurements_allowed"] is False


def test_build_matched_request_rejects_unsealed_decision(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from torch2pc_thesis import stage3b_matched_profiling as matched

    monkeypatch.setattr(matched, "require_opening_base_ancestor", lambda _root: None)
    base_manifest = generate_manifest()
    b1_contract = _contract("isolated_layer_vjp")
    b2_contract = _contract("composite_vjp")
    b1_decision = _decision("EQ-B1")
    b1_decision["sealed"] = False
    b2_decision = _decision("EQ-B2")
    matched_manifest = build_matched_manifest(base_manifest, b1_contract, b2_contract)

    paths = [tmp_path / name for name in ("base.json", "b1.json", "b2.json", "d1.json", "d2.json")]
    for path, payload in zip(
        paths,
        (base_manifest, b1_contract, b2_contract, b1_decision, b2_decision),
        strict=True,
    ):
        _write_json(path, payload)
    historical_request_path, historical_manifest_path = _historical_paths(tmp_path)

    with pytest.raises(MatchedProfilingError, match="must be sealed"):
        matched.build_matched_request(
            project_root=tmp_path,
            base_manifest_path=paths[0],
            b1_contract_path=paths[1],
            b2_contract_path=paths[2],
            b1_decision_path=paths[3],
            b2_decision_path=paths[4],
            matched_manifest_path=tmp_path / "matched.json",
            historical_request_path=historical_request_path,
            historical_manifest_path=historical_manifest_path,
            base_manifest=base_manifest,
            b1_contract=b1_contract,
            b2_contract=b2_contract,
            b1_decision=b1_decision,
            b2_decision=b2_decision,
            matched_manifest=matched_manifest,
        )


def test_prelaunch_gate_requires_confirmatory_equivalence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from torch2pc_thesis import stage3b_matched_profiling as matched

    monkeypatch.setattr(matched, "require_opening_base_ancestor", lambda _root: None)
    base_manifest = generate_manifest()
    b1_contract = _contract("isolated_layer_vjp")
    b2_contract = _contract("composite_vjp")
    b1_decision = _decision("EQ-B1")
    b1_decision["scope"] = "smoke"
    b2_decision = _decision("EQ-B2")
    manifest = build_matched_manifest(base_manifest, b1_contract, b2_contract)

    base_path = tmp_path / "base.json"
    b1_contract_path = tmp_path / "b1-contract.json"
    b2_contract_path = tmp_path / "b2-contract.json"
    b1_decision_path = tmp_path / "b1-decision.json"
    b2_decision_path = tmp_path / "b2-decision.json"
    matched_path = tmp_path / "matched.json"
    historical_request_path, historical_manifest_path = _historical_paths(tmp_path)
    for path, payload in (
        (base_path, base_manifest),
        (b1_contract_path, b1_contract),
        (b2_contract_path, b2_contract),
        (b1_decision_path, b1_decision),
        (b2_decision_path, b2_decision),
    ):
        _write_json(path, payload)

    with pytest.raises(MatchedProfilingError, match="scope=confirmatory"):
        matched.build_matched_request(
            project_root=tmp_path,
            base_manifest_path=base_path,
            b1_contract_path=b1_contract_path,
            b2_contract_path=b2_contract_path,
            b1_decision_path=b1_decision_path,
            b2_decision_path=b2_decision_path,
            matched_manifest_path=matched_path,
            historical_request_path=historical_request_path,
            historical_manifest_path=historical_manifest_path,
            base_manifest=base_manifest,
            b1_contract=b1_contract,
            b2_contract=b2_contract,
            b1_decision=b1_decision,
            b2_decision=b2_decision,
            matched_manifest=manifest,
        )


def test_prelaunch_gate_accepts_confirmatory_equivalence_and_balance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from torch2pc_thesis import stage3b_matched_profiling as matched

    monkeypatch.setattr(matched, "require_opening_base_ancestor", lambda _root: None)
    base_manifest = generate_manifest()
    b1_contract = _contract("isolated_layer_vjp")
    b2_contract = _contract("composite_vjp")
    b1_decision = _confirmatory_decision("EQ-B1")
    b2_decision = _confirmatory_decision("EQ-B2")
    manifest = build_matched_manifest(base_manifest, b1_contract, b2_contract)

    base_path = tmp_path / "base.json"
    b1_contract_path = tmp_path / "b1-contract.json"
    b2_contract_path = tmp_path / "b2-contract.json"
    b1_decision_path = tmp_path / "b1-decision.json"
    b2_decision_path = tmp_path / "b2-decision.json"
    matched_path = tmp_path / "matched.json"
    historical_request_path, historical_manifest_path = _historical_paths(tmp_path)
    for path, payload in (
        (base_path, base_manifest),
        (b1_contract_path, b1_contract),
        (b2_contract_path, b2_contract),
        (b1_decision_path, b1_decision),
        (b2_decision_path, b2_decision),
    ):
        _write_json(path, payload)

    request = matched.build_matched_request(
        project_root=tmp_path,
        base_manifest_path=base_path,
        b1_contract_path=b1_contract_path,
        b2_contract_path=b2_contract_path,
        b1_decision_path=b1_decision_path,
        b2_decision_path=b2_decision_path,
        matched_manifest_path=matched_path,
        historical_request_path=historical_request_path,
        historical_manifest_path=historical_manifest_path,
        base_manifest=base_manifest,
        b1_contract=b1_contract,
        b2_contract=b2_contract,
        b1_decision=b1_decision,
        b2_decision=b2_decision,
        matched_manifest=manifest,
    )

    gate = validate_matched_prelaunch_scientific_gate(
        manifest,
        request,
        project_root=tmp_path,
    )
    assert gate["status"] == "pass"
    assert gate["confirmatory_equivalence"] is True
    assert gate["exact_counterbalance"] is True
