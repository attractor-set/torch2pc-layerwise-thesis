#!/usr/bin/env python3
"""Validate that current public entry points describe the final v1.0.0 thesis."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def _require(relative: str, tokens: tuple[str, ...]) -> None:
    text = _read(relative)
    missing = [token for token in tokens if token not in text]
    if missing:
        raise AssertionError(f"{relative}: missing public-surface markers: {missing}")


def _require_prefix(relative: str, tokens: tuple[str, ...], lines: int = 180) -> None:
    text = "\n".join(_read(relative).splitlines()[:lines])
    missing = [token for token in tokens if token not in text]
    if missing:
        raise AssertionError(f"{relative}: missing current-prefix markers: {missing}")


def main() -> None:
    for relative in ("README.md", "README_EN.md"):
        _require(
            relative,
            (
                "v1.0.0",
                "T24_COMMIT=9d45c897d35225fd541aa1b96aeed7fa7e945531",
                "T24_TREE=44575ea3aced7c76633aa05f6ac22b89a20c615f",
                "THESIS_STATUS=DEFENSE_READY_WITH_EXPLICIT_EXTERNAL_VALIDITY_BOUNDARIES",
                "C08",
                "C09",
                "C10",
                "C11",
                "fixedpred_eta1_wavefront_completion_v1",
                "complete_suffix_stage2_baseline_v1",
                "compute_step >= 5",
                "99",
            ),
        )
    assert "Текущее состояние на 23 июля 2026 года" not in _read("README.md")
    assert "Current state as of 23 July 2026" not in _read("README_EN.md")
    print("PUBLIC_README_CURRENTNESS=PASS")

    _require_prefix(
        "STATUS.md",
        (
            "## Текущий статус v1.0.0 — 17 августа 2026 года",
            "авторитетным текущим статусом",
            "FULL_PYTEST=1732_passed_8_skipped",
            "C09 | RQ3 | `rejected`",
            "C10 | RQ3 | `not_tested`",
            "C11 | RQ3 | `not_tested`",
            "разрешает новый scientific execution",
            "### Исторический журнал",
        ),
    )
    _require_prefix(
        "STATUS_EN.md",
        (
            "## Current v1.0.0 status — 17 August 2026",
            "authoritative current repository status",
            "FULL_PYTEST=1732_passed_8_skipped",
            "C09 | RQ3 | `rejected`",
            "C10 | RQ3 | `not_tested`",
            "C11 | RQ3 | `not_tested`",
            "authorize new scientific execution",
            "### Historical ledger",
        ),
    )
    print("PUBLIC_STATUS_PRECEDENCE=PASS")

    _require_prefix(
        "ROADMAP.md",
        (
            "## Актуальная дорожная карта после завершения диссертации",
            "### R0 — публикация `v1.0.0`",
            "### R1 — новый эксперимент для C10",
            "### R3 — прямая эмпирическая проверка PC-CATM",
            "### R4 — внешняя валидность",
            "### Исторический roadmap",
        ),
    )
    _require_prefix(
        "ROADMAP_EN.md",
        (
            "## Current post-dissertation roadmap",
            "### R0 — publish `v1.0.0`",
            "### R1 — new experiment for C10",
            "### R3 — direct empirical test of PC-CATM",
            "### R4 — external validity",
            "### Historical roadmap",
        ),
    )
    print("PUBLIC_ROADMAP_PRECEDENCE=PASS")

    repository_blob_root = "https://github.com/attractor-set/torch2pc-layerwise-thesis/blob/main"
    index_contracts = {
        "docs/index.md": (
            f"{repository_blob_root}/README.md",
            f"{repository_blob_root}/STATUS.md",
            f"{repository_blob_root}/ROADMAP.md",
        ),
        "docs/index_EN.md": (
            f"{repository_blob_root}/README_EN.md",
            f"{repository_blob_root}/STATUS_EN.md",
            f"{repository_blob_root}/ROADMAP_EN.md",
        ),
    }
    for relative, repository_links in index_contracts.items():
        _require(
            relative,
            (
                "v1.0.0",
                "C08",
                "C09",
                "C10",
                "C11",
                "fixedpred_eta1_wavefront_completion_v1",
                "complete_suffix_stage2_baseline_v1",
                "thesis/data/thesis_traceability.json",
                *repository_links,
            ),
        )
        assert "](../README" not in _read(relative)
        assert "](../STATUS" not in _read(relative)
        assert "](../ROADMAP" not in _read(relative)
    assert "На 21 июля 2026 года" not in _read("docs/index.md")
    assert "As of 21 July 2026" not in _read("docs/index_EN.md")
    print("PUBLIC_DOC_INDEX_CURRENTNESS=PASS")

    for relative in ("PROJECT_STRUCTURE.md", "PROJECT_STRUCTURE_EN.md"):
        _require(
            relative,
            (
                "v1.0.0",
                "thesis/data/thesis_traceability.json",
                "scripts/build_release.sh",
                "release-manifest.json",
                "C09",
                "C11",
            ),
        )
    print("PUBLIC_STRUCTURE_CURRENTNESS=PASS")

    for relative in (
        "article/README.md",
        "article/README_EN.md",
        "results/README.md",
        "results/README_EN.md",
        "notebooks/README.md",
        "notebooks/README_EN.md",
        "experiments/README.md",
        "experiments/README_EN.md",
        "configs/README.md",
        "configs/README_EN.md",
        "thesis/README.md",
        "thesis/README_EN.md",
    ):
        _require(
            relative,
            ("v1.0.0",)
            if "notebooks" in relative
            or "article" in relative
            or "experiments" in relative
            or "configs" in relative
            or "thesis" in relative
            else ("C01",),
        )
    print("PUBLIC_SUBREADME_CURRENTNESS=PASS")

    for relative in (
        "docs/research-question.md",
        "docs/research-question_EN.md",
        "docs/methodology.md",
        "docs/methodology_EN.md",
    ):
        _require(
            relative,
            (
                "C08",
                "C09",
                "C10",
                "C11",
                "fixedpred_eta1_wavefront_completion_v1",
                "complete_suffix_stage2_baseline_v1",
            ),
        )
    print("PUBLIC_METHOD_RQ_CURRENTNESS=PASS")

    _require(
        "docs/validation.md",
        ("v1.0.0", "release-manifest.json", "scripts/check_release_contract.py"),
    )
    _require(
        "docs/validation_EN.md",
        ("v1.0.0", "release-manifest.json", "scripts/check_release_contract.py"),
    )
    for relative in (
        "references/README.md",
        "references/README_EN.md",
        "data/README.md",
        "data/README_EN.md",
        "external/README.md",
        "external/README_EN.md",
    ):
        _require(relative, ("v1.0.0",))
    print("PUBLIC_RELEASE_SUPPORT_DOCS_CURRENTNESS=PASS")

    for relative in (
        "article/structure.md",
        "article/structure_EN.md",
    ):
        _require(relative, ("v1.0.0", "C08", "C09", "C10/C11"))
    _require(
        "article/manuscript_EN.tex",
        ("historical article scaffold", "release v1.0.0", "C08 remains supported"),
    )
    _require(
        "article/supplementary_EN.tex",
        ("historical supplementary-material scaffold", "v1.0.0 release"),
    )
    print("PUBLIC_ARTICLE_STATUS_CURRENTNESS=PASS")

    _require(
        "mkdocs.yml",
        (
            "Финальная диссертация",
            "Исторический план анализа",
            "Исторический план диссертации",
            "Исторический план статьи",
            "Полный индекс ADR",
        ),
    )
    _require(
        "mkdocs_EN.yml",
        (
            "Final dissertation",
            "Historical analysis plan",
            "Historical thesis plan",
            "Historical article plan",
            "Full ADR index",
        ),
    )
    print("PUBLIC_DOCS_NAV_CURRENTNESS=PASS")

    print("THESIS_V1_PUBLIC_SURFACE=PASS")


if __name__ == "__main__":
    main()
