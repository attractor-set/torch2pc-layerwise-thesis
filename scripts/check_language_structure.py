from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / "docs" / "language-map.csv"

CYRILLIC = re.compile(r"[А-Яа-яЁё]")
LATIN = re.compile(r"[A-Za-z]")
GLOSSARY_TERM = re.compile(r"^### (TERM-[A-Z0-9-]+) — ", re.MULTILINE)
HEADING = re.compile(r"^(#{1,6})\s+", re.MULTILINE)
LONG_HEX = re.compile(r"\b[0-9a-f]{12,64}\b", re.IGNORECASE)
NUMBER = re.compile(
    r"(?<![A-Za-z_])\d+(?:\.\d+)?(?:e[+-]?\d+)?(?![A-Za-z_])",
    re.IGNORECASE,
)
FENCE = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})(.*)$")
HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
INLINE_CODE = re.compile(r"(`+)(.+?)\1", re.DOTALL)
REFERENCE_DEFINITION = re.compile(r"^[ \t]{0,3}\[[^\]]+\]:\s*\S+.*$", re.MULTILINE)
AUTOLINK = re.compile(r"<(?:(?:https?|mailto):[^>]+)>", re.IGNORECASE)
BARE_URL = re.compile(r"\b(?:https?|ftp)://\S+", re.IGNORECASE)
MARKDOWN_LINK = re.compile(r"!?\[([^\]]*)\]\([^)]*\)")
REFERENCE_LINK = re.compile(r"!?\[([^\]]*)\]\[[^\]]*\]")
HTML_TAG = re.compile(r"</?[A-Za-z][^>]*>")
MACHINE_ASSIGNMENT = re.compile(
    r"(?<![\w`])(?:[A-Z][A-Z0-9_]{2,}|[a-z][A-Za-z0-9_.-]*_[A-Za-z0-9_.-]+)"
    r"\s*=\s*[^\s,;]+"
)
MACHINE_IDENTIFIER = re.compile(r"(?<![\w`])[A-Z][A-Z0-9_]{2,}(?![\w`])")
PATH_TOKEN = re.compile(
    r"(?<![\w`])(?:\.?\.?/)?(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+(?:\.[A-Za-z0-9_.-]+)?"
)
CLI_OPTION = re.compile(r"(?<![\w`])--[A-Za-z0-9][A-Za-z0-9_.-]*(?:=[^\s,;]+)?")
LONG_MACHINE_HEX = re.compile(r"(?<![0-9A-Fa-f])[0-9A-Fa-f]{12,}(?![0-9A-Fa-f])")


def text_ratio(pattern: re.Pattern[str], text: str) -> float:
    letters = CYRILLIC.findall(text) + LATIN.findall(text)
    if not letters:
        return 0.0
    return len(pattern.findall(text)) / len(letters)


def strip_fenced_code_blocks(text: str) -> str:
    """Remove fenced verbatim blocks while preserving surrounding prose lines."""

    output: list[str] = []
    fence_char: str | None = None
    fence_len = 0
    for line in text.splitlines(keepends=True):
        match = FENCE.match(line)
        if fence_char is None:
            if match is None:
                output.append(line)
                continue
            token = match.group(1)
            fence_char = token[0]
            fence_len = len(token)
            output.append("\n" if line.endswith("\n") else "")
            continue

        stripped = line.lstrip(" \t")
        if stripped.startswith(fence_char * fence_len):
            closing = len(stripped) - len(stripped.lstrip(fence_char))
            if closing >= fence_len:
                fence_char = None
                fence_len = 0
        output.append("\n" if line.endswith("\n") else "")
    return "".join(output)


def markdown_prose_surface(text: str) -> str:
    """Return human-language Markdown prose, excluding machine/verbatim surfaces."""

    prose = strip_fenced_code_blocks(text)
    prose = HTML_COMMENT.sub(" ", prose)
    prose = REFERENCE_DEFINITION.sub(" ", prose)
    prose = INLINE_CODE.sub(" ", prose)
    prose = AUTOLINK.sub(" ", prose)
    prose = BARE_URL.sub(" ", prose)
    prose = MARKDOWN_LINK.sub(lambda match: match.group(1), prose)
    prose = REFERENCE_LINK.sub(lambda match: match.group(1), prose)
    prose = HTML_TAG.sub(" ", prose)
    prose = LONG_MACHINE_HEX.sub(" ", prose)
    prose = CLI_OPTION.sub(" ", prose)
    prose = PATH_TOKEN.sub(" ", prose)
    prose = MACHINE_ASSIGNMENT.sub(" ", prose)
    prose = MACHINE_IDENTIFIER.sub(" ", prose)
    return prose


def language_ratio(pattern: re.Pattern[str], text: str) -> float:
    """Measure natural-language identity on the human prose surface only."""

    return text_ratio(pattern, markdown_prose_surface(text))


def normalized_numeric_literals(text: str) -> set[str]:
    normalized = text.replace("\u00a0", " ")
    thousands = re.compile(r"(?<=\d),(?=\d{3}(?:,|\D|$))")
    while thousands.search(normalized):
        normalized = thousands.sub("", normalized)
    grouped_spaces = re.compile(r"(?<=\d) (?=\d{3}(?: |\D|$))")
    while grouped_spaces.search(normalized):
        normalized = grouped_spaces.sub("", normalized)
    normalized = re.sub(r"(?<=\d),(?=\d)", ".", normalized)
    return set(NUMBER.findall(normalized))


def long_hashes(text: str) -> set[str]:
    return {value.lower() for value in LONG_HEX.findall(text)}


def heading_levels(text: str) -> list[int]:
    return [len(match.group(1)) for match in HEADING.finditer(text)]


LANG_FACT = re.compile(r"<!--\s*LANG-FACT:\s*([A-Za-z0-9_.-]+)\s*=\s*(.*?)\s*-->")
LANG_SOURCE = re.compile(r"<!--\s*LANG-SOURCE:\s*([^\s<>]+)\s*-->")


def numeric_literal_drift(
    russian_text: str,
    english_text: str,
) -> dict[str, list[str]]:
    """Report lexical numeric drift without treating it as semantics."""

    russian = normalized_numeric_literals(russian_text)
    english = normalized_numeric_literals(english_text)
    return {
        "russian_only": sorted(russian - english),
        "english_only": sorted(english - russian),
    }


def extract_language_facts(text: str) -> dict[str, object]:
    """Parse language-neutral LANG-FACT key/JSON-value contracts."""

    facts: dict[str, object] = {}
    for match in LANG_FACT.finditer(text):
        key = match.group(1)
        raw_value = match.group(2)
        if key in facts:
            raise ValueError(f"duplicate LANG-FACT key: {key}")
        try:
            value = json.loads(raw_value)
        except json.JSONDecodeError as exc:
            raise ValueError(f"LANG-FACT {key} must contain a JSON value") from exc
        facts[key] = value
    return facts


def language_source_paths(text: str) -> set[str]:
    """Return explicit shared machine-readable semantic sources."""

    return {match.group(1) for match in LANG_SOURCE.finditer(text)}


def validate_language_sources(
    document: Path,
    sources: set[str],
) -> list[str]:
    errors: list[str] = []
    for raw in sorted(sources):
        target = (document.parent / raw).resolve()
        if not target.is_relative_to(ROOT):
            errors.append(f"{document.relative_to(ROOT)}: LANG-SOURCE leaves repository: {raw}")
            continue
        if not target.is_file() or target.is_symlink():
            errors.append(f"{document.relative_to(ROOT)}: LANG-SOURCE is not a regular file: {raw}")
    return errors


def extract_glossary_term_ids(text: str) -> list[str]:
    return GLOSSARY_TERM.findall(text)


def duplicate_values(values: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


def discover_docs_pairs() -> set[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    docs_root = ROOT / "docs"
    for ru in docs_root.rglob("*.md"):
        if ru.name.endswith("_EN.md"):
            continue
        en = ru.with_name(f"{ru.stem}_EN.md")
        if en.exists():
            pairs.add((str(ru.relative_to(ROOT)), str(en.relative_to(ROOT))))
    return pairs


def main() -> None:
    errors: list[str] = []
    warnings: list[dict[str, object]] = []
    fact_contract_pairs = 0
    source_contract_pairs = 0
    records: list[dict[str, object]] = []

    with MAP.open("r", newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))

    registered_docs_pairs = {
        (row["russian_primary"], row["english_version"])
        for row in rows
        if row["russian_primary"].startswith("docs/") and row["russian_primary"].endswith(".md")
    }
    discovered_docs_pairs = discover_docs_pairs()
    missing_pairs = sorted(discovered_docs_pairs - registered_docs_pairs)
    stale_pairs = sorted(registered_docs_pairs - discovered_docs_pairs)
    for ru_name, en_name in missing_pairs:
        errors.append(
            f"Языковая пара не зарегистрирована в docs/language-map.csv: {ru_name} -> {en_name}"
        )
    for ru_name, en_name in stale_pairs:
        errors.append(
            f"В docs/language-map.csv зарегистрирована отсутствующая пара: {ru_name} -> {en_name}"
        )

    for row in rows:
        ru = ROOT / row["russian_primary"]
        en = ROOT / row["english_version"]
        if not ru.exists():
            errors.append(f"Отсутствует русская версия: {ru.relative_to(ROOT)}")
            continue
        if not en.exists():
            errors.append(f"Отсутствует английская версия: {en.relative_to(ROOT)}")
            continue

        ru_text = ru.read_text(encoding="utf-8")
        en_text = en.read_text(encoding="utf-8")
        ru_raw_ratio = text_ratio(CYRILLIC, ru_text)
        en_raw_ratio = text_ratio(LATIN, en_text)
        ru_ratio = language_ratio(CYRILLIC, ru_text)
        en_ratio = language_ratio(LATIN, en_text)

        if (
            ru.suffix == ".md"
            and ru.is_relative_to(ROOT / "docs")
            and heading_levels(ru_text) != heading_levels(en_text)
        ):
            errors.append(
                "Русская и английская версии имеют разную иерархию заголовков: "
                f"{ru.relative_to(ROOT)} -> {en.relative_to(ROOT)}"
            )

        if ru.suffix == ".md" and ru.is_relative_to(ROOT / "docs"):
            if long_hashes(ru_text) != long_hashes(en_text):
                errors.append(
                    "Русская и английская версии содержат разные длинные хэши: "
                    f"{ru.relative_to(ROOT)} -> {en.relative_to(ROOT)}"
                )
            numeric_drift = numeric_literal_drift(ru_text, en_text)
            if numeric_drift["russian_only"] or numeric_drift["english_only"]:
                warnings.append(
                    {
                        "kind": "numeric_literal_drift",
                        "russian": str(ru.relative_to(ROOT)),
                        "english": str(en.relative_to(ROOT)),
                        **numeric_drift,
                    }
                )

            try:
                ru_facts = extract_language_facts(ru_text)
                en_facts = extract_language_facts(en_text)
            except ValueError as exc:
                errors.append(
                    "Некорректный машинно-читаемый языковой факт: "
                    f"{ru.relative_to(ROOT)} -> {en.relative_to(ROOT)}: {exc}"
                )
            else:
                if ru_facts or en_facts:
                    fact_contract_pairs += 1
                    if ru_facts != en_facts:
                        errors.append(
                            "Русская и английская версии имеют разные LANG-FACT контракты: "
                            f"{ru.relative_to(ROOT)} -> {en.relative_to(ROOT)}"
                        )

            ru_sources = language_source_paths(ru_text)
            en_sources = language_source_paths(en_text)
            if ru_sources or en_sources:
                source_contract_pairs += 1
                if ru_sources != en_sources:
                    errors.append(
                        "Русская и английская версии имеют разные LANG-SOURCE контракты: "
                        f"{ru.relative_to(ROOT)} -> {en.relative_to(ROOT)}"
                    )
                else:
                    errors.extend(validate_language_sources(ru, ru_sources))
                    errors.extend(validate_language_sources(en, en_sources))

        if ru.suffix == ".md" and ru_ratio < 0.35:
            errors.append(
                f"Русская версия содержит слишком мало кириллицы: "
                f"{ru.relative_to(ROOT)} ({ru_ratio:.2f})"
            )
        if en.suffix == ".md" and en_ratio < 0.55:
            errors.append(
                f"Английская версия содержит слишком мало латиницы: "
                f"{en.relative_to(ROOT)} ({en_ratio:.2f})"
            )

        records.append(
            {
                "russian": str(ru.relative_to(ROOT)),
                "english": str(en.relative_to(ROOT)),
                "russian_cyrillic_ratio": round(ru_ratio, 4),
                "english_latin_ratio": round(en_ratio, 4),
                "russian_raw_cyrillic_ratio": round(ru_raw_ratio, 4),
                "english_raw_latin_ratio": round(en_raw_ratio, 4),
                "language_surface": "markdown_prose",
            }
        )

    glossary_ru = ROOT / "docs" / "glossary.md"
    glossary_en = ROOT / "docs" / "glossary_EN.md"
    glossary_term_count = 0

    if glossary_ru.exists() and glossary_en.exists():
        ru_ids = extract_glossary_term_ids(glossary_ru.read_text(encoding="utf-8"))
        en_ids = extract_glossary_term_ids(glossary_en.read_text(encoding="utf-8"))
        glossary_term_count = len(ru_ids)

        ru_duplicates = duplicate_values(ru_ids)
        en_duplicates = duplicate_values(en_ids)
        if ru_duplicates:
            errors.append(
                "Повторяются идентификаторы терминов в русском глоссарии: "
                + ", ".join(ru_duplicates)
            )
        if en_duplicates:
            errors.append(
                "Повторяются идентификаторы терминов в английском глоссарии: "
                + ", ".join(en_duplicates)
            )
        if not ru_ids:
            errors.append("Русский глоссарий не содержит идентификаторов TERM-*")
        if ru_ids != en_ids:
            errors.append(
                "Русский и английский глоссарии содержат разные "
                "идентификаторы TERM-* или разный порядок терминов"
            )

    forbidden = ROOT / "README.ru.md"
    if forbidden.exists():
        errors.append("README.ru.md не должен существовать: основной файл README.md русский")

    for path in ROOT.rglob("*.md"):
        if path.name.endswith(".ru.md"):
            errors.append(f"Обнаружено устаревшее имя .ru.md: {path.relative_to(ROOT)}")

    result = {
        "status": "ok" if not errors else "failed",
        "pairs": len(rows),
        "errors": errors,
        "warnings": warnings,
        "fact_contract_pairs": fact_contract_pairs,
        "source_contract_pairs": source_contract_pairs,
        "records": records,
        "glossary_terms": glossary_term_count,
        "discovered_docs_pairs": len(discovered_docs_pairs),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
