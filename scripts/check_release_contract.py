#!/usr/bin/env python3
"""Validate the final thesis release metadata and publication contract."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "1.0.0"
EXPECTED_TAG = f"v{EXPECTED_VERSION}"
RELEASE_URL = (
    f"https://github.com/attractor-set/torch2pc-layerwise-thesis/releases/tag/{EXPECTED_TAG}"
)


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def _single_match(pattern: str, text: str, label: str) -> str:
    matches = re.findall(pattern, text, flags=re.MULTILINE)
    if len(matches) != 1:
        raise AssertionError(f"{label}: expected exactly one match, found {len(matches)}")
    return matches[0]


def main() -> None:
    pyproject = tomllib.loads(_read("pyproject.toml"))
    package_init = _read("src/torch2pc_thesis/__init__.py")
    citation = _read("CITATION.cff")
    workflow = _read(".github/workflows/release.yml")
    builder = _read("scripts/build_release.sh")
    changelog_ru = _read("CHANGELOG.md")
    changelog_en = _read("CHANGELOG_EN.md")
    public_surface = _read("scripts/check_public_surface.py")

    project_version = pyproject["project"]["version"]
    package_version = _single_match(
        r'^__version__\s*=\s*"([^"]+)"$', package_init, "package version"
    )
    citation_version = _single_match(r"^version:\s*([^\s]+)\s*$", citation, "CITATION.cff version")
    citation_date = _single_match(
        r"^date-released:\s*(\d{4}-\d{2}-\d{2})\s*$",
        citation,
        "CITATION.cff release date",
    )

    assert project_version == EXPECTED_VERSION
    assert package_version == EXPECTED_VERSION
    assert citation_version == EXPECTED_VERSION
    assert citation_date == "2026-08-17"
    assert RELEASE_URL in citation
    assert "stage2-results-v1" not in citation
    assert not re.search(r"^commit:\s*", citation, flags=re.MULTILINE)
    print("RELEASE_VERSION_SURFACES=PASS")

    for heading, changelog in (
        ("## [1.0.0] — 2026-08-17", changelog_ru),
        ("## [1.0.0] — 2026-08-17", changelog_en),
    ):
        assert heading in changelog
    assert "## [Не опубликовано]" in changelog_ru
    assert "## [Unreleased]" in changelog_en
    print("RELEASE_CHANGELOG_SURFACE=PASS")

    for marker in (
        "THESIS_V1_PUBLIC_SURFACE=PASS",
        "PUBLIC_README_CURRENTNESS=PASS",
        "PUBLIC_STATUS_PRECEDENCE=PASS",
        "PUBLIC_ROADMAP_PRECEDENCE=PASS",
    ):
        assert marker in public_surface
    print("RELEASE_PUBLIC_SURFACE_CONTRACT=PASS")

    workflow_tokens = (
        'tags:\n      - "v*"',
        "contents: write",
        "scripts/check_public_surface.py",
        "scripts/check_release_contract.py",
        "scripts/build_release.sh",
        "gh release create",
        "--verify-tag",
        ".release-manifest.json",
        ".pdf.sha256",
    )
    for token in workflow_tokens:
        assert token in workflow, f"release workflow missing {token!r}"
    print("RELEASE_WORKFLOW_CONTRACT=PASS")

    builder_tokens = (
        "make thesis-check",
        "make thesis",
        "source_git_tree",
        "release_tag",
        "THESIS_PDF_SHA256",
        "SOURCE_ARCHIVE_SHA256",
        "THESIS_OVERFULL_COUNT",
        "THESIS_UNDEFINED_REFERENCES_COUNT",
        "THESIS_UNDEFINED_CITATIONS_COUNT",
        "THESIS_RERUN_REFERENCES_COUNT",
        "TRACKED_WORKTREE_UNCHANGED=PASS",
        ".release-manifest.json",
    )
    for token in builder_tokens:
        assert token in builder, f"release builder missing {token!r}"
    print("RELEASE_ARTIFACT_CONTRACT=PASS")

    print("THESIS_V1_RELEASE_CONTRACT=PASS")


if __name__ == "__main__":
    main()
