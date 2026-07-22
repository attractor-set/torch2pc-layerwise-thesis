from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OPENING = ROOT / "experiments/planned/STAGE3B-B2-CONFIRMATORY-OPENING.json"


def test_opening_contract_is_execution_closed() -> None:
    payload = json.loads(OPENING.read_text(encoding="utf-8"))

    assert payload["opening_id"] == "stage3b-b2-confirmatory-opening-v1"
    assert payload["status"] == "implementation_ready_execution_closed"
    assert payload["opening_base_commit"] == (
        "cebf658e78c37313b78b0b586f3c05328be2d076"
    )
    assert payload["registered_scope"]["matched_triples"] == 120
    assert payload["registered_scope"]["pairwise_comparisons"] == 240
    assert payload["registered_scope"]["test_split_access"] is False

    boundary = payload["execution_boundary"]
    assert boundary == {
        "frozen_request_present": False,
        "immutable_image_built": False,
        "preflights_present": False,
        "authorization_issued": False,
        "engineering_smoke_passed": False,
        "confirmatory_execution_started": False,
        "confirmatory_evidence_present": False,
        "eq_b2_confirmatory_sealed": False,
        "derived_eq_b2_admission_present": False,
        "matched_profiling_refrozen": False,
        "matched_profiling_open": False,
        "results_present": False,
    }


def test_opening_reuses_b1_inputs_without_new_batch_selection() -> None:
    payload = json.loads(OPENING.read_text(encoding="utf-8"))
    inputs = payload["required_reused_inputs"]

    assert inputs["exact_batch_reuse_required"] is True
    assert inputs["exact_checkpoint_reuse_required"] is True
    assert inputs["new_validation_batch_selection"] is False
    assert inputs["b1_frozen_request"].endswith("/request.json")
    assert inputs["b1_validation_batch_registry"].endswith(
        "/validation-batches.json"
    )


def test_opening_separates_smoke_and_confirmatory_authorization() -> None:
    payload = json.loads(OPENING.read_text(encoding="utf-8"))
    authorization = payload["authorization_requirements"]

    assert authorization["authorization_domains_separated"] is True
    assert authorization["confirmatory_authorized_triple_count"] == 120
    assert authorization["confirmatory_authorized_comparison_count"] == 240
    assert authorization["engineering_smoke_authorized_triple_count"] == 12
    assert authorization["engineering_smoke_authorized_comparison_count"] == 24
    assert "CONFIRMATORY_120_MATCHED_TRIPLES_240_COMPARISONS" in (
        authorization["confirmatory_operator_acknowledgement"]
    )
    assert "NON_EVIDENCE" in (
        authorization["engineering_smoke_operator_acknowledgement"]
    )


def test_runtime_files_exist() -> None:
    payload = json.loads(OPENING.read_text(encoding="utf-8"))

    for relative in payload["runtime_modules"].values():
        assert (ROOT / relative).is_file(), relative
    for relative in payload["runtime_scripts"].values():
        assert (ROOT / relative).is_file(), relative


def test_sealing_contract_requires_complete_confirmatory_matrix() -> None:
    payload = json.loads(OPENING.read_text(encoding="utf-8"))
    sealing = payload["sealing_requirements"]

    assert sealing["scientific_decision_id"] == "EQ-B2-CONFIRMATORY"
    assert sealing["derived_admission_decision_id"] == "EQ-B2"
    assert sealing["scope"] == "confirmatory"
    assert sealing["registered_triple_count"] == 120
    assert sealing["observed_triple_count"] == 120
    assert sealing["registered_comparison_count"] == 240
    assert sealing["observed_comparison_count"] == 240
    assert sealing["failed_pair_count"] == 0
    assert sealing["dangerous_miss_limit"] == 0
    assert sealing["all_gate_ids_required"] == [
        "STRUCT-B2",
        "NUM-B2",
        "TRAJ-B2",
        "OBS-B2",
        "PROV-B2",
    ]


def test_opening_adr_is_historical_and_status_advances_after_sealing() -> None:
    ru_adr = (
        ROOT
        / "docs/decisions/ADR-022-stage3b-b2-confirmatory-opening.md"
    ).read_text(encoding="utf-8")
    en_adr = (
        ROOT
        / "docs/decisions/ADR-022-stage3b-b2-confirmatory-opening_EN.md"
    ).read_text(encoding="utf-8")
    status_ru = (ROOT / "STATUS.md").read_text(encoding="utf-8")
    status_en = (ROOT / "STATUS_EN.md").read_text(encoding="utf-8")

    for text in (ru_adr, en_adr):
        assert "implementation_ready_execution_closed" in text
        assert "EQ-B2-CONFIRMATORY" in text
        assert "120" in text
        assert "240" in text
        assert "experiments/frozen/**" in text
        assert "results/**" in text

    for text in (status_ru, status_en):
        assert "b2_confirmatory_decision=pass_sealed" in text
        assert "b2_confirmatory_request_frozen=true" in text
        assert "b2_confirmatory_admission=present" in text
        assert "matched_profiling_execution_complete=true" in text
        assert "matched_profiling_evidence=sealed" in text
        assert "matched_profiling_analysis_open=false" in text
        assert "runtime_authorization=issued_consumed" in text
        assert "measurements_allowed=false" in text
        assert "results_publication_permitted=true" in text
        assert "release_draft_required=false" in text
        assert "release_publication_permitted=true" in text
        assert "release_publication_complete=true" in text
        assert (
            "matched_profiling_analysis_publication_receipt_frozen=true"
            in text
        )
        assert "ex_if0_protocol_frozen=true" in text
        assert "ex_if0_opened=true" in text
        assert "ex_if0_complete=true" in text
        assert "exact_implementation_candidate=stage2_baseline" in text
        assert "minimum_sufficient_sweep_rule_frozen=true" in text
        assert "ex_if0_execution_permitted=false" in text
        assert "oracle_label_generation_open=false" in text
        assert "recursive_aggregate_execution_open=false" in text


def test_opening_navigation_and_language_pair_are_registered() -> None:
    language_map = (ROOT / "docs/language-map.csv").read_text(
        encoding="utf-8"
    )
    mkdocs_ru = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    mkdocs_en = (ROOT / "mkdocs_EN.yml").read_text(encoding="utf-8")

    assert (
        "docs/decisions/ADR-022-stage3b-b2-confirmatory-opening.md,"
        "docs/decisions/ADR-022-stage3b-b2-confirmatory-opening_EN.md,"
        "required"
    ) in language_map
    assert "ADR-022 Confirmatory EQ-B2 opening" in mkdocs_ru
    assert "ADR-022 Confirmatory EQ-B2 opening" in mkdocs_en
