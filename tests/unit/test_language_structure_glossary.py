from pathlib import Path

from scripts.check_language_structure import (
    discover_docs_pairs,
    duplicate_values,
    extract_glossary_term_ids,
    heading_levels,
    long_hashes,
    normalized_numeric_literals,
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


def test_all_discovered_docs_pairs_are_registered() -> None:
    registered: set[tuple[str, str]] = set()
    import csv

    with (ROOT / "docs" / "language-map.csv").open(
        newline="", encoding="utf-8"
    ) as stream:
        for row in csv.DictReader(stream):
            if row["russian_primary"].startswith("docs/"):
                registered.add((row["russian_primary"], row["english_version"]))

    assert discover_docs_pairs() <= registered


def test_heading_levels_capture_bilingual_structure() -> None:
    text = "# Title\n\n## Section\n\n### Detail\n"
    assert heading_levels(text) == [1, 2, 3]


def test_numeric_literals_normalize_language_separators() -> None:
    russian = "0,01; 11,5; 50 202 008; 1250; 2026-07-14"
    english = "0.01; 11.5; 50,202,008; 1,250; 2026-07-14"
    assert normalized_numeric_literals(russian) == normalized_numeric_literals(english)


def test_long_hashes_are_case_insensitive() -> None:
    assert long_hashes("ABCDEF123456") == {"abcdef123456"}
