#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INCLUDE_SUFFIXES = {".md", ".tex", ".yml", ".yaml"}
EXCLUDED_PARTS = {".git", ".venv", "site_ru", "site_en", "notebooks"}
EXCLUDED_FILES = {"LICENSE", "PACKAGE_MANIFEST.json"}

# Patterns target unqualified result claims, not words used in methodological warnings.
PATTERNS = {
    "ru_asserted_proof": re.compile(r"(?<!не )(?<!не было )\\b(?:доказано|доказана|доказан|подтверждено|подтверждена|подтвержден)\\b", re.I),
    "ru_asserted_finding": re.compile(r"\\b(?:установлено|показано|выявлено),? что\\b", re.I),
    "ru_superiority": re.compile(r"\\b(?:метод|режим|алгоритм)\\s+[^.\\n]{0,50}\\s(?:лучше|хуже|превосходит|эффективнее)\\b", re.I),
    "ru_guarantee": re.compile(r"\\b(?:гарантирует|гарантированно|обеспечивает истинность)\\b", re.I),
    "en_asserted_proof": re.compile(r"\\b(?:we|the study|the results?)\\s+(?:prove|proves|proved|confirm|confirms|confirmed|demonstrate|demonstrates|demonstrated)\\b", re.I),
    "en_superiority": re.compile(r"\\b(?:method|regime|algorithm)\\s+[^.\\n]{0,50}\\s(?:is superior|outperforms|is better|is worse)\\b", re.I),
    "en_guarantee": re.compile(r"\\b(?:guarantees?|guaranteed)\\b", re.I),
}


def main() -> None:
    findings: list[dict[str, object]] = []
    checked = 0
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path.name in EXCLUDED_FILES:
            continue
        if path.suffix not in INCLUDE_SUFFIXES:
            continue
        if any(part in EXCLUDED_PARTS for part in path.parts):
            continue
        checked += 1
        text = path.read_text(encoding="utf-8")
        for label, pattern in PATTERNS.items():
            for match in pattern.finditer(text):
                line = text.count("\\n", 0, match.start()) + 1
                findings.append({
                    "file": str(path.relative_to(ROOT)),
                    "line": line,
                    "rule": label,
                    "match": match.group(0),
                })
    result = {
        "status": "ok" if not findings else "failed",
        "checked_files": checked,
        "findings": findings,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if findings:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
