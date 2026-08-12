from pathlib import Path

from scripts.check_language_structure import (
    CYRILLIC,
    LATIN,
    discover_docs_pairs,
    duplicate_values,
    extract_glossary_term_ids,
    extract_language_facts,
    heading_levels,
    language_ratio,
    language_source_paths,
    long_hashes,
    markdown_prose_surface,
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
    ru = extract_glossary_term_ids((ROOT / "docs" / "glossary.md").read_text(encoding="utf-8"))
    en = extract_glossary_term_ids((ROOT / "docs" / "glossary_EN.md").read_text(encoding="utf-8"))

    assert ru
    assert ru == en
    assert duplicate_values(ru) == []


def test_all_discovered_docs_pairs_are_registered() -> None:
    registered: set[tuple[str, str]] = set()
    import csv

    with (ROOT / "docs" / "language-map.csv").open(newline="", encoding="utf-8") as stream:
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
    assert normalized_numeric_literals(russian) == normalized_numeric_literals(english)

    ru_facts = extract_language_facts(
        "<!-- LANG-FACT: candidate_count = 7 -->\n<!-- LANG-FACT: warmup_count = 2 -->\n"
    )
    en_facts = extract_language_facts(
        "<!-- LANG-FACT: candidate_count = 2 -->\n<!-- LANG-FACT: warmup_count = 7 -->\n"
    )
    assert ru_facts != en_facts


def test_language_facts_preserve_json_types_and_context() -> None:
    text = (
        "<!-- LANG-FACT: cpu_affinity = [0] -->\n"
        "<!-- LANG-FACT: measured_pair_count = 12 -->\n"
        "<!-- LANG-FACT: execution_open = false -->\n"
    )
    assert extract_language_facts(text) == {
        "cpu_affinity": [0],
        "measured_pair_count": 12,
        "execution_open": False,
    }


def test_language_source_paths_are_language_neutral() -> None:
    text = "<!-- LANG-SOURCE: ../../experiments/frozen/example/contract.json -->\n"
    assert language_source_paths(text) == {"../../experiments/frozen/example/contract.json"}


def test_markdown_prose_surface_excludes_fenced_and_inline_machine_content() -> None:
    text = """
# Русский заголовок

Это содержательное русское объяснение.

```text
AUTHORIZATION_CONSUMED=true
CAP_DAC_OVERRIDE=false
abcdef1234567890abcdef1234567890
```

Проверка сохраняет `HOST_CLAIM_SHA256=abcdef1234567890` как машинный маркер.
"""
    prose = markdown_prose_surface(text)
    assert "содержательное русское объяснение" in prose
    assert "AUTHORIZATION_CONSUMED" not in prose
    assert "CAP_DAC_OVERRIDE" not in prose
    assert "HOST_CLAIM_SHA256" not in prose
    assert "abcdef1234567890" not in prose


def test_markdown_prose_surface_keeps_human_link_labels_not_destinations() -> None:
    text = (
        "См. [доказательные материалы](../../results/scientific/report.json) "
        "и https://example.invalid/technical-path.\n"
    )
    prose = markdown_prose_surface(text)
    assert "доказательные материалы" in prose
    assert "results/scientific/report.json" not in prose
    assert "example.invalid" not in prose


def test_markdown_prose_surface_excludes_comments_paths_options_and_assignments() -> None:
    text = (
        "<!-- LANG-FACT: measured_pair_count = 12 -->\n"
        "Русский текст перед scripts/check_language_structure.py и "
        "--network=none, AUTHORIZATION_CONSUMED=true.\n"
    )
    prose = markdown_prose_surface(text)
    assert "LANG-FACT" not in prose
    assert "scripts/check_language_structure.py" not in prose
    assert "--network=none" not in prose
    assert "AUTHORIZATION_CONSUMED" not in prose
    assert "Русский текст" in prose


def test_language_ratio_is_not_diluted_by_large_machine_surface() -> None:
    machine = "\n".join(f"FIELD_{index}=VALUE_{index}" for index in range(500))
    text = f"Русское содержательное описание.\n```text\n{machine}\n```\n"
    assert language_ratio(CYRILLIC, text) > 0.80


def test_language_ratio_still_detects_wrong_language_human_prose() -> None:
    russian_document = (
        "Короткое русское введение.\n\n"
        "This is a long English paragraph written as ordinary human prose. "
        "It must remain visible to language validation and must not be hidden "
        "as a technical or machine-readable surface.\n"
    )
    assert language_ratio(CYRILLIC, russian_document) < 0.35


def test_machine_only_markdown_has_no_language_signal() -> None:
    text = """
```text
AUTHORIZATION_CONSUMED=true
HOST_CLAIM_SHA256=abcdef1234567890
```
<!-- LANG-SOURCE: ../../experiments/frozen/example/contract.json -->
"""
    assert markdown_prose_surface(text).strip() == ""
    assert language_ratio(CYRILLIC, text) == 0.0
    assert language_ratio(LATIN, text) == 0.0


def test_plain_machine_identifiers_do_not_create_english_language_signal() -> None:
    text = (
        "Русская проверка фиксирует AUTHORIZATION_CONSUMED=true и "
        "CAP_DROP_ALL=true без изменения смысла.\n"
    )
    assert language_ratio(CYRILLIC, text) > 0.85


def test_project_markdown_pairs_pass_prose_surface_language_thresholds() -> None:
    import csv

    with (ROOT / "docs" / "language-map.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))

    failures: list[tuple[str, float, str, float]] = []
    for row in rows:
        ru = ROOT / row["russian_primary"]
        en = ROOT / row["english_version"]
        if ru.suffix != ".md" or en.suffix != ".md":
            continue
        ru_ratio = language_ratio(CYRILLIC, ru.read_text(encoding="utf-8"))
        en_ratio = language_ratio(LATIN, en.read_text(encoding="utf-8"))
        if ru_ratio < 0.35 or en_ratio < 0.55:
            failures.append(
                (
                    str(ru.relative_to(ROOT)),
                    round(ru_ratio, 4),
                    str(en.relative_to(ROOT)),
                    round(en_ratio, 4),
                )
            )

    assert failures == []
