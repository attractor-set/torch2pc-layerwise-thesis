from __future__ import annotations

import csv
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANGUAGE_MAP = ROOT / "docs" / "language-map.csv"
RU_GLOSSARY = ROOT / "docs" / "glossary.md"
EN_GLOSSARY = ROOT / "docs" / "glossary_EN.md"

ENTRY = re.compile(r"^### (TERM-[A-Z0-9-]+) — (.+)$", re.MULTILINE)
ANCHOR = re.compile(r'^<a id="(term-[a-z0-9-]+)"></a>$', re.MULTILINE)
LINK = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)")
INLINE_CODE = re.compile(r"`[^`]*`")
RAW_URL = re.compile(r"https?://\S+")
HTML = re.compile(r"<!--.*?-->|<[^>]+>")
INLINE_MATH = re.compile(r"\\\([^)]*\\\)|\$[^$]*\$")
LATIN_TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)*")

ALLOWED_LATIN_TOKENS = {
    "actions",
    "amd",
    "adr",
    "bios",
    "bp",
    "c3h",
    "cka",
    "cpu",
    "csv",
    "cuda",
    "docker",
    "doi",
    "exact",
    "fashionmnist",
    "fixedpred",
    "float32",
    "float64",
    "git",
    "github",
    "gpu",
    "hip",
    "kmnist",
    "latex",
    "lenet",
    "mib",
    "mnist",
    "npz",
    "oom",
    "p95",
    "pdf",
    "python",
    "pytorch",
    "radeon",
    "ram",
    "rocm",
    "rho",
    "rsa",
    "ruff",
    "ryzen",
    "sha",
    "sha-256",
    "sha256",
    "strict",
    "torch2pc",
    "torchvision",
    "ubuntu",
    "vjp",
    "x3d",
    "zenodo",
}

ALLOWED_TOKEN_PATTERNS = (
    re.compile(r"ADR-\d+", re.IGNORECASE),
    re.compile(r"RQ\d+", re.IGNORECASE),
    re.compile(r"[ABC]\d+[A-Z]?", re.IGNORECASE),
    re.compile(r"p\d+", re.IGNORECASE),
)


@dataclass(frozen=True)
class GlossaryTerm:
    term_id: str
    russian: str
    english: str

    @property
    def anchor(self) -> str:
        return self.term_id.lower()


def without_terminal_parenthetical(value: str) -> str:
    return re.sub(r"\s*\([^)]*\)\s*$", "", value).strip()


def parse_terms(root: Path = ROOT) -> list[GlossaryTerm]:
    ru_text = (root / "docs" / "glossary.md").read_text(encoding="utf-8")
    en_text = (root / "docs" / "glossary_EN.md").read_text(encoding="utf-8")
    ru_entries = ENTRY.findall(ru_text)
    en_entries = ENTRY.findall(en_text)
    if [item[0] for item in ru_entries] != [item[0] for item in en_entries]:
        raise ValueError("Glossary TERM-* identifiers or order differ")
    return [
        GlossaryTerm(
            term_id=ru_id,
            russian=without_terminal_parenthetical(ru_term),
            english=without_terminal_parenthetical(en_term),
        )
        for (ru_id, ru_term), (en_id, en_term) in zip(
            ru_entries, en_entries, strict=True
        )
        if ru_id == en_id
    ]


def display_path(path: Path, root: Path = ROOT) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def expected_glossary_target(document: Path, english: bool, term: GlossaryTerm) -> str:
    root = document
    while root.name != "docs":
        root = root.parent
    target = root / ("glossary_EN.md" if english else "glossary.md")
    relative = Path(os.path.relpath(target, document.parent)).as_posix()
    return f"{relative}#{term.anchor}"


def iter_substantive_lines(text: str) -> list[tuple[int, str]]:
    lines: list[tuple[int, str]] = []
    fenced = False
    fence = ""
    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            token = stripped[:3]
            if not fenced:
                fenced = True
                fence = token
            elif token == fence:
                fenced = False
                fence = ""
            continue
        if fenced or stripped.startswith("#"):
            continue
        lines.append((number, line))
    return lines


def protected_ranges(line: str) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    for pattern in (INLINE_CODE, INLINE_MATH, RAW_URL, HTML, LINK):
        ranges.extend((match.start(), match.end()) for match in pattern.finditer(line))
    return ranges


def is_protected(start: int, end: int, ranges: list[tuple[int, int]]) -> bool:
    return any(start < protected_end and end > protected_start for protected_start, protected_end in ranges)


def first_term_event(
    text: str,
    term: str,
    expected_target: str,
    accepted_targets: set[str] | None = None,
) -> tuple[int, bool, str] | None:
    valid_targets = accepted_targets or {expected_target}
    pattern = re.compile(
        r"(?<![\wА-Яа-яЁё])" + re.escape(term) + r"(?![\wА-Яа-яЁё])",
        re.IGNORECASE,
    )
    for number, line in iter_substantive_lines(text):
        events: list[tuple[int, bool, str]] = []
        for link in LINK.finditer(line):
            label = link.group(1)
            target = link.group(2).strip().split()[0].strip("<>")
            label_match = pattern.search(label)
            if label_match:
                events.append((link.start(), target in valid_targets, target))
        ranges = protected_ranges(line)
        for match in pattern.finditer(line):
            if not is_protected(match.start(), match.end(), ranges):
                events.append((match.start(), False, "plain text"))
        if events:
            _, linked, target = min(events, key=lambda item: item[0])
            return number, linked, target
    return None


def plain_text(line: str) -> str:
    result = INLINE_CODE.sub(" ", line)
    result = INLINE_MATH.sub(" ", result)
    result = LINK.sub(" ", result)
    result = RAW_URL.sub(" ", result)
    result = HTML.sub(" ", result)
    return result


def latin_token_allowed(token: str) -> bool:
    normalized = token.casefold()
    if len(normalized) < 3 or normalized in ALLOWED_LATIN_TOKENS:
        return True
    return any(pattern.fullmatch(token) for pattern in ALLOWED_TOKEN_PATTERNS)


def check_russian_prose(document: Path, text: str) -> list[str]:
    errors: list[str] = []
    fenced = False
    fence = ""
    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            token = stripped[:3]
            if not fenced:
                fenced = True
                fence = token
            elif token == fence:
                fenced = False
                fence = ""
            continue
        if fenced:
            continue
        for token_match in LATIN_TOKEN.finditer(plain_text(line)):
            token = token_match.group(0)
            if latin_token_allowed(token):
                continue
            errors.append(
                f"{display_path(document)}:{number}: "
                f"неканоническая английская проза: {token}"
            )
    return errors


def documented_pairs(root: Path = ROOT) -> list[tuple[Path, Path]]:
    pairs: list[tuple[Path, Path]] = []
    with (root / "docs" / "language-map.csv").open(
        newline="", encoding="utf-8"
    ) as stream:
        for row in csv.DictReader(stream):
            ru = root / row["russian_primary"]
            en = root / row["english_version"]
            if ru.suffix == ".md" and ru.is_relative_to(root / "docs"):
                pairs.append((ru, en))
    return pairs


def run_checks(root: Path = ROOT) -> dict[str, object]:
    terms = parse_terms(root)
    errors: list[str] = []
    linked_uses = 0
    scanned_documents = 0

    ru_glossary = (root / "docs" / "glossary.md").read_text(encoding="utf-8")
    en_glossary = (root / "docs" / "glossary_EN.md").read_text(encoding="utf-8")
    expected_anchors = [term.anchor for term in terms]
    if ANCHOR.findall(ru_glossary) != expected_anchors:
        errors.append("Русский глоссарий не содержит полный упорядоченный набор якорей")
    if ANCHOR.findall(en_glossary) != expected_anchors:
        errors.append("Английский глоссарий не содержит полный упорядоченный набор якорей")

    paired_paths: set[Path] = set()
    documents: list[tuple[Path, bool]] = []
    for ru_path, en_path in documented_pairs(root):
        if not ru_path.exists() or not en_path.exists():
            continue
        paired_paths.add(ru_path)
        paired_paths.add(en_path)
        documents.extend(((ru_path, False), (en_path, True)))

    for ru_path in sorted((root / "docs").rglob("*.md")):
        if ru_path.name.endswith("_EN.md") or ru_path in paired_paths:
            continue
        documents.append((ru_path, False))

    for path, english in documents:
        if path.name in {"glossary.md", "glossary_EN.md"}:
            continue
        scanned_documents += 1
        text = path.read_text(encoding="utf-8")
        if not english:
            errors.extend(check_russian_prose(path, text))
        glossary_targets = {
            expected_glossary_target(path, english, item)
            for item in terms
        }
        for term in terms:
            # The English word "run" is also a common verb. Requiring an
            # automatic first-use link would create false links in commands
            # and ordinary prose. The Russian noun remains link-protected.
            if english and term.term_id == "TERM-RUN":
                continue
            canonical = term.english if english else term.russian
            event = first_term_event(
                text,
                canonical,
                expected_glossary_target(path, english, term),
                accepted_targets=glossary_targets,
            )
            if event is None:
                continue
            line_number, linked, actual_target = event
            if linked:
                linked_uses += 1
                continue
            errors.append(
                f"{display_path(path, root)}:{line_number}: первое содержательное "
                f"употребление '{canonical}' должно ссылаться на "
                f"{expected_glossary_target(path, english, term)}; "
                f"обнаружено: {actual_target}"
            )

    return {
        "status": "ok" if not errors else "failed",
        "glossary_terms": len(terms),
        "scanned_documents": scanned_documents,
        "linked_first_uses": linked_uses,
        "errors": errors,
    }


def main() -> None:
    result = run_checks()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
