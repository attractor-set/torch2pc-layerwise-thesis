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


def text_ratio(pattern: re.Pattern[str], text: str) -> float:
    letters = CYRILLIC.findall(text) + LATIN.findall(text)
    if not letters:
        return 0.0
    return len(pattern.findall(text)) / len(letters)


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


def main() -> None:
    errors: list[str] = []
    records: list[dict[str, object]] = []

    with MAP.open("r", newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))

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
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
