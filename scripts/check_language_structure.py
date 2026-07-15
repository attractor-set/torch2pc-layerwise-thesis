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


def text_ratio(pattern: re.Pattern[str], text: str) -> float:
    letters = CYRILLIC.findall(text) + LATIN.findall(text)
    if not letters:
        return 0.0
    return len(pattern.findall(text)) / len(letters)




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
    records: list[dict[str, object]] = []

    with MAP.open("r", newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))

    registered_docs_pairs = {
        (row["russian_primary"], row["english_version"])
        for row in rows
        if row["russian_primary"].startswith("docs/")
        and row["russian_primary"].endswith(".md")
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
        ru_ratio = text_ratio(CYRILLIC, ru_text)
        en_ratio = text_ratio(LATIN, en_text)

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
            if normalized_numeric_literals(ru_text) != normalized_numeric_literals(
                en_text
            ):
                errors.append(
                    "Русская и английская версии содержат разные числовые значения: "
                    f"{ru.relative_to(ROOT)} -> {en.relative_to(ROOT)}"
                )

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
        "records": records,
        "glossary_terms": glossary_term_count,
        "discovered_docs_pairs": len(discovered_docs_pairs),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
