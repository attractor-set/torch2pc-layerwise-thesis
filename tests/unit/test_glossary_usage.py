from __future__ import annotations

from pathlib import Path

from scripts.check_glossary_usage import (
    check_russian_prose,
    first_term_event,
    parse_terms,
    run_checks,
)


def test_real_glossary_has_paired_terms_and_anchors() -> None:
    terms = parse_terms()
    assert len(terms) == 102
    term_ids = {term.term_id for term in terms}
    assert len(term_ids) == len(terms)
    assert {
        "TERM-PRECISION-MASKED-ZERO",
        "TERM-COST-VECTOR",
        "TERM-PARETO-ADMISSIBILITY",
        "TERM-DIAGNOSTIC-MECHANISM-COST",
        "TERM-OBSERVER-COST",
        "TERM-CONTROL-PLANE-COST",
        "TERM-OPERATIONAL-SUFFICIENCY-BOUNDARY",
        "TERM-ORACLE-SUFFICIENCY-MARGIN",
        "TERM-SUFFICIENCY-BOUNDARY-ESTIMATOR",
        "TERM-PREDICTED-SUFFICIENCY-HORIZON",
        "TERM-MINIMUM-SUFFICIENT-COMPUTE-AGGREGATE",
    } <= term_ids


def test_ecz_has_the_error_cancellation_meaning_only() -> None:
    terms = {term.term_id: term for term in parse_terms()}
    ecz = terms["TERM-ECZ"]
    assert ecz.russian == "зона компенсации ошибок"
    assert ecz.english == "Error-Cancellation Zone"


def test_russian_prose_rejects_unformatted_english_term(tmp_path: Path) -> None:
    document = tmp_path / "sample.md"
    errors = check_russian_prose(document, "Обычный runtime не разрешён.\n")
    assert errors
    assert "runtime" in errors[0]


def test_first_term_event_requires_expected_link() -> None:
    text = "Первое профилирование описано здесь.\n"
    event = first_term_event(
        text,
        "профилирование",
        "glossary.md#term-profiling",
    )
    assert event == (1, False, "plain text")

    linked = "Первое [профилирование](glossary.md#term-profiling) описано здесь.\n"
    event = first_term_event(
        linked,
        "профилирование",
        "glossary.md#term-profiling",
    )
    assert event == (1, True, "glossary.md#term-profiling")


def test_repository_glossary_usage_passes() -> None:
    result = run_checks()
    assert result["status"] == "ok", result["errors"]
