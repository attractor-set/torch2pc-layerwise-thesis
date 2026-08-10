from pathlib import Path

from scripts.check_language_structure import (
    discover_docs_pairs,
    duplicate_values,
    extract_glossary_term_ids,
    extract_language_facts,
    heading_levels,
    language_source_paths,
    long_hashes,
    normalized_numeric_literals,
    numeric_literal_drift,
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


def test_numeric_literal_drift_is_diagnostic_not_semantic_equivalence() -> None:
    drift = numeric_literal_drift(
        "Исполнитель использует восемь потоков.",
        "The executor uses 8 threads.",
    )
    assert drift == {
        "russian_only": [],
        "english_only": ["8"],
    }


def test_raw_numeric_set_equality_cannot_detect_context_swap() -> None:
    russian = "7 кандидатов; 2 прогрева."
    english = "2 candidates; 7 warm-ups."
    assert normalized_numeric_literals(russian) == normalized_numeric_literals(
        english
    )

    ru_facts = extract_language_facts(
        "<!-- LANG-FACT: candidate_count = 7 -->\n"
        "<!-- LANG-FACT: warmup_count = 2 -->\n"
    )
    en_facts = extract_language_facts(
        "<!-- LANG-FACT: candidate_count = 2 -->\n"
        "<!-- LANG-FACT: warmup_count = 7 -->\n"
    )
    assert ru_facts != en_facts


def test_language_facts_preserve_json_types_and_context() -> None:
    text = (
        '<!-- LANG-FACT: cpu_affinity = [0] -->\n'
        '<!-- LANG-FACT: measured_pair_count = 12 -->\n'
        '<!-- LANG-FACT: execution_open = false -->\n'
    )
    assert extract_language_facts(text) == {
        "cpu_affinity": [0],
        "measured_pair_count": 12,
        "execution_open": False,
    }


def test_language_source_paths_are_language_neutral() -> None:
    text = (
        "<!-- LANG-SOURCE: ../../experiments/frozen/example/contract.json -->\n"
    )
    assert language_source_paths(text) == {
        "../../experiments/frozen/example/contract.json"
    }
