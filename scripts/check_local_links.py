from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")


def main() -> None:
    errors: list[str] = []
    checked = 0

    for document in sorted(ROOT.rglob("*.md")):
        if any(part in {".venv", "site_ru", "site_en"} for part in document.parts):
            continue
        text = document.read_text(encoding="utf-8")
        for raw_target in LINK.findall(text):
            target = raw_target.strip().split()[0].strip("<>")
            if (
                not target
                or target.startswith("#")
                or "://" in target
                or target.startswith("mailto:")
            ):
                continue
            path_part = unquote(target.split("#", 1)[0])
            if not path_part:
                continue
            resolved = (document.parent / path_part).resolve()
            checked += 1
            try:
                resolved.relative_to(ROOT.resolve())
            except ValueError:
                errors.append(
                    f"{document.relative_to(ROOT)}: ссылка выходит за пределы проекта: {target}"
                )
                continue
            if not resolved.exists():
                errors.append(f"{document.relative_to(ROOT)}: отсутствует цель ссылки: {target}")

    result = {
        "status": "ok" if not errors else "failed",
        "checked_links": checked,
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
