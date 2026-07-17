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
