"""Regression guards for the design-only PC-TREF sufficiency-boundary theory."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

THEORY_DOCUMENTS = (
    ROOT / "docs" / "pc-tref-sufficiency-boundary.md",
    ROOT / "docs" / "pc-tref-sufficiency-boundary_EN.md",
)
ADR_DOCUMENTS = (
    ROOT / "docs" / "decisions" / "ADR-016-stage3b-sufficiency-boundary.md",
    ROOT / "docs" / "decisions" / "ADR-016-stage3b-sufficiency-boundary_EN.md",
)


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_oracle_margin_and_pre_action_estimate_are_distinct() -> None:
    for path in THEORY_DOCUMENTS:
        text = _text(path)
        assert r"M^*(x)=\varepsilon_R-r_{\mathrm{skip}}^*(x)" in text
        assert r"\widehat M_b(x)=g_b(\phi_b(x))" in text
        assert "pre-action" in text
        assert "post-action" in text
        assert "цикличес" in text or "circular" in text


def test_stop_safety_is_weaker_than_full_required_equivalence() -> None:
    for path in THEORY_DOCUMENTS:
        text = _text(path)
        assert r"q_{\mathrm{stop}}(x)" in text
        assert r"\mathcal A_\varepsilon(x)" in text
        assert r"\mathcal P_C(x)" in text
        assert "tie-break" in text
        assert "local" in text
        assert "fallback" in text


def test_operational_boundary_is_not_claimed_as_topological_boundary() -> None:
    for path in THEORY_DOCUMENTS:
        text = _text(path)
        assert r"\mathcal B^*=\{x:M^*(x)=0\}" in text
        assert r"\partial\mathcal S^*" in text
        assert "level set" in text
        assert "тополог" in text or "topological" in text


def test_tnz_remains_a_transport_null_regime() -> None:
    for path in THEORY_DOCUMENTS:
        text = _text(path)
        assert r"\mathrm{active\_non\_ecz}^0" in text
        assert r"\widetilde J_{h,l+1}^{*}e_{l+1}(x)=0" in text
        assert r"\mathrm{TNZ}^0=\{x:u(x)\neq0" not in text
        assert "transport" in text or "перенос" in text


def test_adr_keeps_theory_design_only_and_policy_neutral() -> None:
    for path in ADR_DOCUMENTS:
        text = _text(path)
        assert "design-only" in text
        assert "EX-IF0" in text
        assert "action_permission" in text
        assert "trajectory-level" in text
        assert "dangerous_miss" in text
        assert "confidence" in text or "доверитель" in text
