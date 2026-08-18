#!/usr/bin/env python3
"""Check structural and scientific congruence of RU/EN dissertation renderings."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import build_thesis_assets_en as english_assets

ROOT = Path(__file__).resolve().parents[1]
THESIS = ROOT / "thesis"

CHAPTER_PAIRS = tuple(
    (
        THESIS / "chapters" / f"{number:02d}_{stem}.tex",
        THESIS / "chapters" / f"{number:02d}_{stem}_EN.tex",
    )
    for number, stem in (
        (1, "introduction"),
        (2, "related_work"),
        (3, "methodology"),
        (4, "experiments"),
        (5, "results"),
        (6, "discussion"),
        (7, "conclusion"),
    )
)

REQUIRED_ENGLISH_FILES = (
    THESIS / "main_EN.tex",
    THESIS / "frontmatter" / "abstracts_EN.tex",
    THESIS / "frontmatter" / "abstract_en_content.tex",
    THESIS / "frontmatter" / "abbreviations_EN.tex",
    *(pair[1] for pair in CHAPTER_PAIRS),
    THESIS / "appendices" / "terminology_EN.tex",
    THESIS / "appendices" / "reproducibility_EN.tex",
)

STRUCTURE_COMMAND = re.compile(r"\\(chapter|section|subsection|subsubsection|paragraph)\*?\{")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def structure_sequence(path: Path) -> list[str]:
    return STRUCTURE_COMMAND.findall(path.read_text(encoding="utf-8"))


ENVIRONMENT = re.compile(r"\\begin\{([^}]+)\}")
LABEL = re.compile(r"\\label\{([^}]+)\}")
WORD = re.compile(r"[A-Za-zА-Яа-яЁё]+(?:[-'][A-Za-zА-Яа-яЁё]+)*")
CITATION = re.compile(r"\\cite\{([^}]+)\}")
MONOSPACE_TOKEN = re.compile(r"\\(?:texttt|code|nolinkurl)\{([^}]+)\}")
CLAIM_ID = re.compile(r"\bC(?:0[1-9]|1[01])\b")

EXPECTED_ENGLISH_TITLE = (
    "Layer-wise Comparison of Predictive-Coding Regimes and Backpropagation "
    "under Comparable Computational Conditions"
)


def environment_counts(path: Path) -> Counter[str]:
    return Counter(ENVIRONMENT.findall(path.read_text(encoding="utf-8")))


def normalized_labels(path: Path) -> list[str]:
    labels = LABEL.findall(path.read_text(encoding="utf-8"))
    return [label[:-3] if label.endswith("-en") else label for label in labels]


def word_count(path: Path) -> int:
    return len(WORD.findall(path.read_text(encoding="utf-8")))


def citation_counts(path: Path) -> Counter[str]:
    keys: list[str] = []
    for group in CITATION.findall(path.read_text(encoding="utf-8")):
        keys.extend(key.strip() for key in group.split(","))
    return Counter(keys)


def monospace_tokens(path: Path) -> set[str]:
    return {
        normalized_tex(token) for token in MONOSPACE_TOKEN.findall(path.read_text(encoding="utf-8"))
    }


def claim_ids(path: Path) -> set[str]:
    return set(CLAIM_ID.findall(path.read_text(encoding="utf-8")))


def input_sequence(path: Path) -> list[str]:
    return re.findall(r"\\input\{([^}]+)\}", path.read_text(encoding="utf-8"))


def normalized_tex(text: str) -> str:
    normalized = (
        text.replace(r"\_", "_").replace(r"\%", "%").replace(r"\,", "").replace("\u00a0", " ")
    )
    return re.sub(r"\s+", " ", normalized)


def main() -> None:
    for path in REQUIRED_ENGLISH_FILES:
        require(path.is_file(), f"missing English dissertation source: {path.relative_to(ROOT)}")

    total_russian_words = 0
    total_english_words = 0
    for russian, english in CHAPTER_PAIRS:
        require(
            structure_sequence(russian) == structure_sequence(english),
            "RU/EN chapter structure differs: "
            f"{russian.relative_to(ROOT)} -> {english.relative_to(ROOT)}",
        )
        require(
            environment_counts(russian) == environment_counts(english),
            "RU/EN chapter environment counts differ: "
            f"{russian.relative_to(ROOT)} -> {english.relative_to(ROOT)}",
        )
        require(
            normalized_labels(russian) == normalized_labels(english),
            "RU/EN chapter label sequence differs: "
            f"{russian.relative_to(ROOT)} -> {english.relative_to(ROOT)}",
        )
        require(
            citation_counts(russian) == citation_counts(english),
            "RU/EN chapter citation multiset differs: "
            f"{russian.relative_to(ROOT)} -> {english.relative_to(ROOT)}",
        )
        require(
            monospace_tokens(russian) == monospace_tokens(english),
            "RU/EN chapter technical identifier/token set differs: "
            f"{russian.relative_to(ROOT)} -> {english.relative_to(ROOT)}",
        )
        require(
            claim_ids(russian) == claim_ids(english),
            "RU/EN chapter C01-C11 surface differs: "
            f"{russian.relative_to(ROOT)} -> {english.relative_to(ROOT)}",
        )
        russian_words = word_count(russian)
        english_words = word_count(english)
        ratio = english_words / russian_words
        require(
            0.90 <= ratio <= 1.10,
            "RU/EN chapter word-count ratio outside omission guard: "
            f"{russian.relative_to(ROOT)} -> {english.relative_to(ROOT)} "
            f"({russian_words} RU vs {english_words} EN; ratio={ratio:.3f})",
        )
        total_russian_words += russian_words
        total_english_words += english_words
    total_ratio = total_english_words / total_russian_words
    require(
        0.95 <= total_ratio <= 1.05,
        "RU/EN total chapter word-count ratio outside omission guard: "
        f"{total_russian_words} RU vs {total_english_words} EN; ratio={total_ratio:.3f}",
    )
    print("THESIS_ENGLISH_STRUCTURE=PASS")
    print(
        "THESIS_ENGLISH_CONTENT_COVERAGE=PASS "
        f"RU_WORDS={total_russian_words} EN_WORDS={total_english_words} "
        f"RATIO={total_ratio:.3f}"
    )
    print("THESIS_ENGLISH_REFERENCE_IDENTITY=PASS")
    print("THESIS_ENGLISH_TECHNICAL_IDENTIFIER_IDENTITY=PASS")
    print("THESIS_ENGLISH_CLAIM_SURFACE_IDENTITY=PASS")

    main_english = (THESIS / "main_EN.tex").read_text(encoding="utf-8")
    english_abstract = (THESIS / "frontmatter" / "abstract_en_content.tex").read_text(
        encoding="utf-8"
    )
    require(
        EXPECTED_ENGLISH_TITLE in main_english,
        "English title no longer preserves the computational-comparability meaning",
    )
    require(
        "computationally controlled" not in (main_english + english_abstract).lower(),
        "English title/abstract must not translate computational comparability as control",
    )
    require(
        "under comparable computational conditions" in english_abstract.lower(),
        "English abstract does not preserve the computational-comparability boundary",
    )
    print("THESIS_ENGLISH_TITLE_SEMANTICS=PASS")

    russian_abstracts = THESIS / "frontmatter" / "abstracts.tex"
    english_abstracts = THESIS / "frontmatter" / "abstracts_EN.tex"
    require(
        input_sequence(russian_abstracts)
        == [
            "frontmatter/abstract_ru_content",
            "frontmatter/abstract_en_content",
        ],
        "Russian rendering must use canonical RU then EN abstract bodies",
    )
    require(
        input_sequence(english_abstracts)
        == [
            "frontmatter/abstract_en_content",
            "frontmatter/abstract_ru_content",
        ],
        "English rendering must use canonical EN then RU abstract bodies",
    )
    print("THESIS_BILINGUAL_ABSTRACT_IDENTITY=PASS")

    claims = json.loads((THESIS / "data" / "research_claims.json").read_text(encoding="utf-8"))[
        "claims"
    ]
    statuses = {item["id"]: item["status"] for item in claims}
    require(statuses["C08"] == "supported", "C08 English rendering must remain supported")
    require(statuses["C09"] == "rejected", "C09 English rendering must remain rejected")
    require(statuses["C10"] == "not_tested", "C10 English rendering must remain not_tested")
    require(statuses["C11"] == "not_tested", "C11 English rendering must remain not_tested")
    require(
        list(english_assets.CLAIM_TEXT) == [item["id"] for item in claims],
        "English C01-C11 translation registry does not match canonical claim IDs/order",
    )
    print("THESIS_ENGLISH_CLAIM_STATUS_SEMANTICS=PASS")

    experiments_en = normalized_tex(
        (THESIS / "chapters" / "04_experiments_EN.tex").read_text(encoding="utf-8")
    )
    for token in ("C10", "C11", "protocol", "marginal execution cost", "not_tested"):
        require(token in experiments_en, f"English experiment stopping boundary missing: {token}")
    require(
        "C3 did not open" in experiments_en,
        "English experiment chapter must state that C3 did not open, not assign a claim status to C3",
    )
    print("THESIS_ENGLISH_C10_C11_STOPPING_BOUNDARY=PASS")

    combined = normalized_tex(
        "\n".join(path.read_text(encoding="utf-8") for path in REQUIRED_ENGLISH_FILES)
    )
    for token in (
        "PC-TREF",
        "PC-CATM",
        "QWake-PC",
        "QWake-FP",
        "NCZ",
        "ECZ",
        "TNZ",
        "fixedpred_eta1_wavefront_completion_v1",
        "complete_suffix_stage2_baseline_v1",
    ):
        require(
            token in combined, f"English dissertation missing canonical term/identifier: {token}"
        )
    require(
        "must not be collapsed into one model" in combined,
        "PC-CATM/PC-TREF separation marker missing from English theory",
    )
    print("THESIS_ENGLISH_TERMINOLOGY_INVARIANCE=PASS")

    for token in (
        "compute_step >= 5",
        "216/756",
        "28.57%",
        "2,625",
        "0/16",
        "108 terminal-boundary",
        "108 preterminal",
    ):
        require(
            token in combined,
            f"English dissertation missing critical QWake/Stage3 boundary: {token}",
        )
    require(
        "replaces the remaining canonical iterative sweeps with a bounded analytic completion"
        in combined,
        "English QWake-FP action semantics drifted",
    )
    require(
        "not a population-level safety guarantee" in combined
        or "not a population-risk estimate" in combined,
        "English zero-danger language lacks the population-inference boundary",
    )
    require(
        "marginal execution cost" in combined and "not tested" in combined,
        "English C09/C10 cost boundary is missing",
    )
    print("THESIS_LANGUAGE_CONGRUENCE=PASS")


if __name__ == "__main__":
    main()
