#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from collections.abc import Iterable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INCLUDE_SUFFIXES = {".md", ".tex", ".yml", ".yaml", ".ipynb"}
EXCLUDED_PARTS = {".git", ".venv", "site_ru", "site_en"}
EXCLUDED_FILES = {"LICENSE"}

PATTERNS = {
    "ru_asserted_proof": re.compile(
        r"\b(?:доказано|доказана|доказан|подтверждено|подтверждена|подтвержден)\b",
        re.IGNORECASE,
    ),
    "ru_asserted_finding": re.compile(
        r"\b(?:установлено|показано|выявлено),?\s+что\b",
        re.IGNORECASE,
    ),
    "ru_superiority": re.compile(
        r"\b(?:метод|режим|алгоритм)\s+[^.\n]{0,60}\s"
        r"(?:лучше|хуже|превосходит|эффективнее)\b",
        re.IGNORECASE,
    ),
    "ru_guarantee": re.compile(
        r"\b(?:гарантирует|гарантированно|обеспечивает истинность)\b",
        re.IGNORECASE,
    ),
    "en_asserted_proof": re.compile(
        r"\b(?:we|the study|the results?)\s+"
        r"(?:prove|proves|proved|confirm|confirms|confirmed|"
        r"demonstrate|demonstrates|demonstrated)\b",
        re.IGNORECASE,
    ),
    "en_superiority": re.compile(
        r"\b(?:method|regime|algorithm)\s+[^.\n]{0,60}\s"
        r"(?:is superior|outperforms|is better|is worse)\b",
        re.IGNORECASE,
    ),
    "en_guarantee": re.compile(r"\b(?:guarantees?|guaranteed)\b", re.IGNORECASE),
}

NEGATED_CONTEXT = re.compile(
    r"(?:"
    r"\bне\s+(?:было\s+)?(?:доказано|подтверждено|установлено|показано|выявлено)\b|"
    r"\bне\s+(?:используется|используются|следует|является|считается|означает)\b|"
    r"\b(?:запрещено|нельзя)\b|"
    r"\b(?:do\s+not|does\s+not|did\s+not|must\s+not|cannot|is\s+not|are\s+not)\b|"
    r"\bnot\s+(?:a\s+)?(?:guarantee|proof|confirmation)\b"
    r")",
    re.IGNORECASE,
)
INLINE_CODE = re.compile(r"`[^`]*`")


def _strip_fenced_code(text: str) -> str:
    lines = text.splitlines()
    in_fence = False
    result: list[str] = []
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            result.append("")
        elif in_fence:
            result.append("")
        else:
            result.append(INLINE_CODE.sub("", line))
    return "\n".join(result)


def _text_sources(path: Path) -> Iterable[tuple[str, str]]:
    if path.suffix != ".ipynb":
        yield str(path.relative_to(ROOT)), _strip_fenced_code(path.read_text(encoding="utf-8"))
        return

    notebook = json.loads(path.read_text(encoding="utf-8"))
    for index, cell in enumerate(notebook.get("cells", [])):
        if cell.get("cell_type") != "markdown":
            continue
        source = cell.get("source", "")
        text = "".join(source) if isinstance(source, list) else str(source)
        yield f"{path.relative_to(ROOT)}::markdown_cell_{index}", _strip_fenced_code(text)


def _is_negated(line: str, match_start: int) -> bool:
    context = line[max(0, match_start - 120) : match_start + 120]
    return NEGATED_CONTEXT.search(context) is not None


def scan_text(source_name: str, text: str) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for label, pattern in PATTERNS.items():
            for match in pattern.finditer(line):
                if _is_negated(line, match.start()):
                    continue
                findings.append(
                    {
                        "file": source_name,
                        "line": line_number,
                        "rule": label,
                        "match": match.group(0),
                        "context": line.strip(),
                    }
                )
    return findings


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
        for source_name, text in _text_sources(path):
            checked += 1
            findings.extend(scan_text(source_name, text))
    result = {
        "status": "ok" if not findings else "failed",
        "checked_sources": checked,
        "findings": findings,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if findings:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
