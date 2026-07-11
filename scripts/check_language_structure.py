from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / "docs" / "language-map.csv"

CYRILLIC = re.compile(r"[А-Яа-яЁё]")
LATIN = re.compile(r"[A-Za-z]")


def text_ratio(pattern: re.Pattern[str], text: str) -> float:
    letters = CYRILLIC.findall(text) + LATIN.findall(text)
    if not letters:
        return 0.0
    return len(pattern.findall(text)) / len(letters)


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
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
