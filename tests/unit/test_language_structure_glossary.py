from pathlib import Path

from scripts.check_language_structure import (
    duplicate_values,
    extract_glossary_term_ids,
)

ROOT = Path(__file__).resolve().parents[2]


def test_extract_glossary_term_ids() -> None:
    text = """
### TERM-ONE — первый термин
### TERM-TWO — второй термин
"""
    assert extract_glossary_term_ids(text) == ["TERM-ONE", "TERM-TWO"]


def test_duplicate_values() -> None:
    assert duplicate_values(["TERM-ONE", "TERM-TWO", "TERM-ONE"]) == ["TERM-ONE"]


def test_project_glossaries_have_matching_unique_term_ids() -> None:
    ru = extract_glossary_term_ids(
        (ROOT / "docs" / "glossary.md").read_text(encoding="utf-8")
    )
    en = extract_glossary_term_ids(
        (ROOT / "docs" / "glossary_EN.md").read_text(encoding="utf-8")
    )

    assert ru
    assert ru == en
    assert duplicate_values(ru) == []
