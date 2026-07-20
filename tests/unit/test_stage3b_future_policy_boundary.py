"""Validate the B1/B2 boundary to future estimator and QWake work."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[2]
PLANNED = ROOT / "experiments" / "planned"


def _contract(name: str) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        json.loads((PLANNED / name).read_text(encoding="utf-8")),
    )


def test_exact_candidates_exclude_future_policy_components() -> None:
    for name in ("STAGE3B-B1-CONTRACT.json", "STAGE3B-B2-CONTRACT.json"):
        boundary = _contract(name)["future_policy_boundary"]
        assert boundary["estimator_present"] is False
        assert boundary["oracle_branching_present"] is False
        assert boundary["cheap_diagnostic_loop_present"] is False
        assert boundary["hysteresis_policy_present"] is False
        assert boundary["offline_trace_collection_present"] is False
        assert boundary["test_split_access"] is False
        assert boundary["branch_labels_are_controller_actions"] is False
        assert boundary["future_sequence"] == [
            "EX-IF0",
            "A11-OFF0",
            "A11-OFF1",
            "predictor_preregistration",
            "shadow_QWake-PC",
        ]
        assert boundary["counterfactual_branch_labels"] == [
            "stop",
            "native_one",
            "exact_one",
        ]


def test_claim_boundary_rejects_policy_inference() -> None:
    required = {
        "QWake estimator or oracle validity",
        "cheap diagnostic-loop benefit",
        "hysteresis or persistence-policy safety",
        "offline policy selection",
    }
    for name in ("STAGE3B-B1-CONTRACT.json", "STAGE3B-B2-CONTRACT.json"):
        not_established = _contract(name)["claim"]["not_established"]
        assert required.issubset(set(not_established))


def test_scenario_freezes_offline_sequence_and_hysteresis_boundary() -> None:
    scenarios = {
        "docs/stage3b-primary-scenario-a.md": "гистерезис",
        "docs/stage3b-primary-scenario-a_EN.md": "hysteresis",
    }

    for name, hysteresis_term in scenarios.items():
        text = (ROOT / name).read_text(encoding="utf-8")
        for token in (
            "A11-OFF0",
            "A11-OFF1",
            "stop",
            "native_one",
            "exact_one",
            "model_seed",
            "fallback_exact",
        ):
            assert token in text
        assert hysteresis_term in text


def test_roadmap_keeps_policy_work_after_ex_if0() -> None:
    for name, heading in (("ROADMAP.md", "## Этап 17"), ("ROADMAP_EN.md", "## Stage 17")):
        text = (ROOT / name).read_text(encoding="utf-8")
        tail = text[text.index(heading) :]
        positions = [
            tail.index("EX-IF0"),
            tail.index("A11-OFF0"),
            tail.index("A11-OFF1"),
            tail.index("predictor"),
            tail.index("shadow"),
        ]
        assert positions == sorted(positions)

def test_hierarchical_future_policy_documents_are_guarded() -> None:
    qwake_documents = (
        "docs/qwake-pc-design.md",
        "docs/qwake-pc-design_EN.md",
        "docs/stage3b-future-policy-boundary.md",
        "docs/stage3b-future-policy-boundary_EN.md",
    )
    required_qwake = {
        "EX-IF0",
        "local_sweep(block_id)",
        "full_exact",
        "fallback_exact",
        "cost_feasibility",
        "zero_dangerous_misses",
        "net_efficiency",
        "0–3",
        "controls_execution=false",
        "A-Max",
    }
    for name in qwake_documents:
        document = (ROOT / name).read_text(encoding="utf-8")
        for token in required_qwake:
            assert token in document

    ecz_documents = (
        "docs/ecz-targeted-local-sweep.md",
        "docs/ecz-targeted-local-sweep_EN.md",
    )
    required_ecz = {
        "EX-IF0",
        "local_sweep(block_id)",
        "full_exact",
        "exact_verification",
        "zero_dangerous_misses",
    }
    for name in ecz_documents:
        document = (ROOT / name).read_text(encoding="utf-8")
        for token in required_ecz:
            assert token in document


def test_future_policy_is_not_retrofitted_into_exact_candidates() -> None:
    for name in ("STAGE3B-B1-CONTRACT.json", "STAGE3B-B2-CONTRACT.json"):
        contract = _contract(name)
        serialized_candidate = json.dumps(
            contract["candidate"],
            ensure_ascii=False,
            sort_keys=True,
        )
        assert "local_sweep" not in serialized_candidate
        assert "ECZ-targeted" not in serialized_candidate
        boundary = contract["future_policy_boundary"]
        assert boundary["estimator_present"] is False
        assert boundary["offline_trace_collection_present"] is False


def test_policy_screening_order_is_frozen_in_design_docs() -> None:
    for name in (
        "docs/qwake-pc-design.md",
        "docs/qwake-pc-design_EN.md",
        "docs/stage3b-future-policy-boundary.md",
        "docs/stage3b-future-policy-boundary_EN.md",
    ):
        document = (ROOT / name).read_text(encoding="utf-8")
        gate_tail = document[document.index("cost_feasibility") :]
        positions = [
            gate_tail.index("cost_feasibility"),
            gate_tail.index("zero_dangerous_misses"),
            gate_tail.index("net_efficiency"),
            gate_tail.index("0–3"),
            gate_tail.index("shadow"),
            gate_tail.index("A-Max"),
        ]
        assert positions == sorted(positions)


def test_qwake_q_is_intentionally_multidimensional_and_unexpanded() -> None:
    documents = {
        "docs/glossary.md": (
            "намеренно не расшифровывается",
            (
                "ни одно измерение не является "
                "единственной канонической "
                "расшифровкой"
            ),
        ),
        "docs/glossary_EN.md": (
            "intentionally left unexpanded",
            "no dimension is the single canonical expansion",
        ),
        "docs/qwake-pc-design.md": (
            "собственным именем",
            "добавление новых расшифровок `Q` требует",
        ),
        "docs/qwake-pc-design_EN.md": (
            "proper name",
            "adding further expansions of `Q` requires",
        ),
    }
    dimensions = ("Qualified", "Quotient", "Quality", "Quiet", "Quick")

    for name, required_phrases in documents.items():
        document = (ROOT / name).read_text(encoding="utf-8")
        for dimension in dimensions:
            assert f"`{dimension}`" in document
        for phrase in required_phrases:
            assert phrase in document

    ru_glossary = (ROOT / "docs/glossary.md").read_text(encoding="utf-8")
    en_glossary = (ROOT / "docs/glossary_EN.md").read_text(encoding="utf-8")
    quick_ru = (
        "только отдельно подтверждаемый "
        "инженерный результат"
    )
    assert quick_ru in ru_glossary
    assert "only a separately demonstrated engineering outcome" in en_glossary


def test_qwake_architecture_is_distinct_from_framework_and_mechanism() -> None:
    documents = (
        "docs/glossary.md",
        "docs/glossary_EN.md",
        "docs/qwake-pc-design.md",
        "docs/qwake-pc-design_EN.md",
        "docs/pc-tref-pc-catm-theoretical-foundation.md",
        "docs/pc-tref-pc-catm-theoretical-foundation_EN.md",
    )

    for name in documents:
        document = (ROOT / name).read_text(encoding="utf-8")
        for token in ("PC-TREF", "PC-CATM", "QWake-PC", "QW-PC0", "QW-AB0"):
            assert token in document

    ru_design = (ROOT / "docs/qwake-pc-design.md").read_text(encoding="utf-8")
    en_design = (ROOT / "docs/qwake-pc-design_EN.md").read_text(encoding="utf-8")
    fixed_algorithm_ru = (
        "не является единственным "
        "фиксированным алгоритмом"
    )
    assert fixed_algorithm_ru in ru_design
    assert "is not one fixed algorithm" in en_design
    assert "не опровергает `PC-CATM` или `PC-TREF`" in ru_design
    assert "does not invalidate" in en_design

    ru_positions = [
        ru_design.index("PC-TREF   —"),
        ru_design.index("PC-CATM   —"),
        ru_design.index("QWake-PC  —"),
        ru_design.index("QW-PC0 / QW-AB0"),
    ]
    en_positions = [
        en_design.index("PC-TREF   —"),
        en_design.index("PC-CATM   —"),
        en_design.index("QWake-PC  —"),
        en_design.index("QW-PC0 / QW-AB0"),
    ]
    assert ru_positions == sorted(ru_positions)
    assert en_positions == sorted(en_positions)
