"""Regression guards for the recursive sufficient-aggregate direction freeze."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

DIRECTION_DOCS = (
    ROOT / "docs" / "stage3b-recursive-sufficiency-aggregate-direction.md",
    ROOT / "docs" / "stage3b-recursive-sufficiency-aggregate-direction_EN.md",
)
ADR_DOCS = (
    ROOT / "docs" / "decisions" / "ADR-035-stage3b-recursive-sufficiency-aggregate-direction.md",
    ROOT / "docs" / "decisions" / "ADR-035-stage3b-recursive-sufficiency-aggregate-direction_EN.md",
)


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_direction_freezes_recursive_minimum_sufficient_aggregate() -> None:
    for path in DIRECTION_DOCS:
        text = _text(path)
        for token in (
            "RESEARCH_DIRECTION_FROZEN=true",
            "CENTRAL_OBJECT=minimum_task_sufficient_compute_aggregate",
            "CONTROL_SEMANTICS=recursive_multiscale",
            "GLOBAL_POLICY_ACTION=false",
            "FULL_SWEEP=maximum_root_aggregate",
            r"B_0=\varnothing",
            "B_K=R",
            "fallback_exact",
        ):
            assert token in text


def test_b1_b2_are_premise_not_adaptive_control_proof() -> None:
    ru = _text(DIRECTION_DOCS[0])
    en = _text(DIRECTION_DOCS[1])
    formula = r"a\sim_N b\;\not\Rightarrow\;\mathbf C(a)=\mathbf C(b)"
    assert formula in ru
    assert formula in en
    assert "не доказывает" in ru
    assert "does not prove" in en
    assert "state dependence" in en


def test_existence_gates_precede_predictor_and_controller() -> None:
    for path in DIRECTION_DOCS:
        text = _text(path)
        sequence = (
            "E2 existence",
            "E3 state dependence",
            "E5 cross-scale semantics",
            "P0 diagnostic opportunity",
            "pre-action estimator",
            "shadow QWake-PC",
        )
        positions = [text.index(token) for token in sequence]
        assert positions == sorted(positions)


def test_spike_like_mechanism_is_conditional() -> None:
    for path in DIRECTION_DOCS + ADR_DOCS:
        text = _text(path)
        assert "spike" in text.lower() or "спайк" in text.lower()
        assert "hyster" in text.lower() or "гистер" in text.lower()
        assert "critical path" in text.lower() or "критический путь" in text.lower()
    for path in DIRECTION_DOCS:
        text = _text(path)
        assert "SPIKE_ACCUMULATOR=conditional" in text
        assert "CONTROLLER_IMPLEMENTATION_AUTHORIZED=false" in text


def test_publication_gate_remains_first_formal_transition() -> None:
    for name in ("ROADMAP.md", "ROADMAP_EN.md"):
        text = _text(ROOT / name)
        publication = text.index("publication gate")
        assert publication < text.index("EX-IF0", publication)

    for path in DIRECTION_DOCS:
        text = _text(path)
        assert "NEXT_FORMAL_TRANSITION=publication_gate_then_EX_IF0" in text
        assert "POLICY_ACTIVATION_PERMITTED=false" in text


def test_direction_is_registered_as_a_language_pair_and_adr() -> None:
    language_map = _text(ROOT / "docs" / "language-map.csv")
    assert (
        "docs/stage3b-recursive-sufficiency-aggregate-direction.md,"
        "docs/stage3b-recursive-sufficiency-aggregate-direction_EN.md,required"
    ) in language_map
    assert (
        "docs/decisions/ADR-035-stage3b-recursive-sufficiency-aggregate-direction.md,"
        "docs/decisions/ADR-035-stage3b-recursive-sufficiency-aggregate-direction_EN.md,required"
    ) in language_map

    for path in ADR_DOCS:
        text = _text(path)
        assert "ADR-035" in text
        assert "EX-IF0" in text
        assert "execution" in text.lower() or "выполнен" in text.lower()
