from __future__ import annotations

import json
from pathlib import Path

import torch

from torch2pc_thesis.models import build_model
from torch2pc_thesis.stage3b_a1_mechanism_controls import (
    CONTRACT_ID,
    IMPLEMENTATION_SCHEMA_ID,
    TORCH2PC_COMMIT,
    Provenance,
    build_summary,
    compare_tensors,
    contract_digests,
    expected_counts,
    load_contract,
    run_geometry_controls,
    run_lenet_block_probe,
    run_materialized_block_probe,
    run_pnz_controls,
    run_temporal_controls,
    run_transport_controls,
    thresholds_for_lane,
)


def provenance() -> Provenance:
    return Provenance(
        lane="cpu",
        device="cpu",
        dtype="torch.float64",
        source_git_commit="a" * 40,
        source_git_branch="research/test",
        experiment_image="torch2pc:test",
        image_revision="a" * 40,
        torch2pc_commit=TORCH2PC_COMMIT,
    )


def test_contract_is_preregistered_and_digests_are_stable() -> None:
    path = Path(
        "experiments/planned/"
        "STAGE3B-A1-MECHANISM-CONTROLS-CONTRACT.json"
    )
    contract = load_contract(path)
    first = contract_digests(contract)
    second = contract_digests(json.loads(path.read_text(encoding="utf-8")))
    assert contract["contract_id"] == CONTRACT_ID
    assert first == second
    assert all(len(value) == 64 for value in first)


def test_zero_safe_comparison() -> None:
    thresholds = thresholds_for_lane("cpu")
    zero = torch.zeros(8, dtype=torch.float64)
    active = torch.zeros(8, dtype=torch.float64)
    active[0] = 100.0 * thresholds.zero_atol
    positive = compare_tensors(
        zero,
        zero,
        profile="analytic_vector",
        thresholds=thresholds,
    )
    negative = compare_tensors(
        zero,
        active,
        profile="analytic_vector",
        thresholds=thresholds,
    )
    assert positive.passed
    assert positive.cosine is None
    assert positive.zero_safe_path
    assert not negative.passed
    assert negative.cosine is None
    assert negative.finite


def test_geometry_transport_temporal_and_pnz_smoke_pass() -> None:
    device = torch.device("cpu")
    dtype = torch.float64
    prov = provenance()
    geometry = run_geometry_controls(
        scope="smoke",
        provenance=prov,
        device=device,
        dtype=dtype,
    )
    transport = run_transport_controls(
        scope="smoke",
        provenance=prov,
        device=device,
        dtype=dtype,
    )
    temporal_events, temporal_summary = run_temporal_controls(
        scope="smoke",
        provenance=prov,
        device=device,
        dtype=dtype,
    )
    pnz = run_pnz_controls(
        scope="smoke",
        provenance=prov,
        device=device,
        dtype=dtype,
    )
    assert len(geometry) == 8
    assert len(transport) == 10
    assert len(temporal_events) == 36
    assert len(temporal_summary) == 1
    assert len(pnz) == 1
    assert all(record["passed"] for record in geometry)
    assert all(record["passed"] for record in transport)
    assert all(record["passed"] for record in temporal_events)
    assert all(record["passed"] for record in temporal_summary)
    assert all(record["passed"] for record in pnz)
    assert temporal_summary[0]["first_active_sweeps"] == [6, 5, 4, 3, 2, 1]


def test_block_probe_smoke_passes_with_canonical_lenet() -> None:
    device = torch.device("cpu")
    dtype = torch.float64
    prov = provenance()
    materialized = run_materialized_block_probe(
        scope="smoke",
        provenance=prov,
        device=device,
        dtype=dtype,
    )
    lenet = run_lenet_block_probe(
        scope="smoke",
        provenance=prov,
        device=device,
        dtype=dtype,
        model_factory=lambda seed: build_model("lenet_classic"),
    )
    assert len(materialized) == 8
    assert len(lenet) == 12
    assert all(record["passed"] for record in materialized)
    assert all(record["passed"] for record in lenet)
    assert {
        record["candidate_form"] for record in materialized + lenet
    } == {"composite_vjp", "chunked_composite_vjp"}
    assert all(
        record["registered_raw_input_shape"] == [8, 1, 28, 28]
        for record in lenet
    )
    assert all(
        record["model_input_shape_after_canonical_pad"] == [8, 1, 32, 32]
        for record in lenet
    )


def test_smoke_summary_opens_si_ma0_when_core_passes() -> None:
    device = torch.device("cpu")
    dtype = torch.float64
    prov = provenance()
    geometry = run_geometry_controls(
        scope="smoke", provenance=prov, device=device, dtype=dtype
    )
    transport = run_transport_controls(
        scope="smoke", provenance=prov, device=device, dtype=dtype
    )
    temporal_events, temporal_summary = run_temporal_controls(
        scope="smoke", provenance=prov, device=device, dtype=dtype
    )
    block_probe = run_materialized_block_probe(
        scope="smoke", provenance=prov, device=device, dtype=dtype
    )
    block_probe.extend(
        run_lenet_block_probe(
            scope="smoke",
            provenance=prov,
            device=device,
            dtype=dtype,
            model_factory=lambda seed: build_model("lenet_classic"),
        )
    )
    pnz = run_pnz_controls(
        scope="smoke", provenance=prov, device=device, dtype=dtype
    )
    summary = build_summary(
        scope="smoke",
        provenance=prov,
        contract_digest="1" * 64,
        construction_registry_digest="2" * 64,
        threshold_registry_digest="3" * 64,
        geometry_records=geometry,
        transport_records=transport,
        temporal_events=temporal_events,
        temporal_summary=temporal_summary,
        block_probe_records=block_probe,
        pnz_records=pnz,
    )
    assert summary["implementation_schema_id"] == IMPLEMENTATION_SCHEMA_ID
    assert summary["expected_counts"] == expected_counts("smoke")
    assert summary["core_passed"]
    assert summary["pnz_l0_passed"]
    assert summary["si_ma0_open"]
    assert summary["passed"]
