#!/usr/bin/env python3
"""Validate the bilingual thesis release metadata and publication contract."""

from __future__ import annotations

import hashlib
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "1.0.1"
FROZEN_RUNTIME_PACKAGE_VERSION = "0.1.0"
FROZEN_RUNTIME_INIT_SHA256 = "99a15a1f681efaaff846df254eab58412a16fc8e1c7767d0ccd00b5e721b08f0"
FROZEN_RUNTIME_PYPROJECT_SHA256 = "5646a4275998b91efe05c215f334eb2ab1f292828434a7eddfc715bf56746352"
FROZEN_RUNTIME_MANIFEST = (
    "experiments/runtime/stage3b-qwake-scientific-successor-v1/runtime-SHA256SUMS"
)
ATTEMPT003_RUNTIME_MANIFEST = (
    "experiments/frozen/"
    "stage3b-qwake-attempt-003-clean-source-closure-implementation-authoring-v1/"
    "runtime-SHA256SUMS"
)
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


def _verify_runtime_registry(manifest_relative: str) -> None:
    manifest = _read(manifest_relative)
    for line in manifest.splitlines():
        if not line.strip():
            continue
        digest, relative = line.split("  ", 1)
        target = ROOT / relative
        assert target.is_file() and not target.is_symlink(), relative
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        assert actual == digest, relative


def main() -> None:
    release_version_raw = _read("RELEASE_VERSION")
    pyproject = tomllib.loads(_read("pyproject.toml"))
    package_init = _read("src/torch2pc_thesis/__init__.py")
    citation = _read("CITATION.cff")
    workflow = _read(".github/workflows/release.yml")
    thesis_workflow = _read(".github/workflows/thesis.yml")
    builder = _read("scripts/build_release.sh")
    changelog_ru = _read("CHANGELOG.md")
    changelog_en = _read("CHANGELOG_EN.md")
    public_surface = _read("scripts/check_public_surface.py")
    runtime_manifest = _read(FROZEN_RUNTIME_MANIFEST)
    attempt003_runtime_manifest = _read(ATTEMPT003_RUNTIME_MANIFEST)
    package_init_sha256 = hashlib.sha256(
        (ROOT / "src/torch2pc_thesis/__init__.py").read_bytes()
    ).hexdigest()
    pyproject_sha256 = hashlib.sha256((ROOT / "pyproject.toml").read_bytes()).hexdigest()

    release_version = release_version_raw.strip()
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

    assert release_version_raw == f"{EXPECTED_VERSION}\n"
    assert release_version == EXPECTED_VERSION
    assert project_version == FROZEN_RUNTIME_PACKAGE_VERSION
    assert package_version == FROZEN_RUNTIME_PACKAGE_VERSION
    assert citation_version == EXPECTED_VERSION
    assert citation_date == "2026-08-18"
    assert RELEASE_URL in citation
    assert "stage2-results-v1" not in citation
    assert not re.search(r"^commit:\s*", citation, flags=re.MULTILINE)
    print("RELEASE_VERSION_SURFACES=PASS")

    assert package_init_sha256 == FROZEN_RUNTIME_INIT_SHA256
    assert f"{FROZEN_RUNTIME_INIT_SHA256}  src/torch2pc_thesis/__init__.py" in runtime_manifest
    _verify_runtime_registry(FROZEN_RUNTIME_MANIFEST)
    _verify_runtime_registry(ATTEMPT003_RUNTIME_MANIFEST)
    assert pyproject_sha256 == FROZEN_RUNTIME_PYPROJECT_SHA256
    assert f"{FROZEN_RUNTIME_PYPROJECT_SHA256}  pyproject.toml" in attempt003_runtime_manifest
    print("RELEASE_FROZEN_RUNTIME_CLOSURE=PASS")

    for heading, changelog in (
        ("## [1.0.1] — 2026-08-18", changelog_ru),
        ("## [1.0.1] — 2026-08-18", changelog_en),
    ):
        assert heading in changelog
    assert "## [1.0.0] — 2026-08-17" in changelog_ru
    assert "## [1.0.0] — 2026-08-17" in changelog_en
    assert "## [Не опубликовано]" in changelog_ru
    assert "## [Unreleased]" in changelog_en
    print("RELEASE_CHANGELOG_SURFACE=PASS")

    for marker in (
        "THESIS_V1_PUBLIC_SURFACE=PASS",
        "PUBLIC_README_CURRENTNESS=PASS",
        "PUBLIC_STATUS_PRECEDENCE=PASS",
        "PUBLIC_ROADMAP_PRECEDENCE=PASS",
        "PUBLIC_BILINGUAL_THESIS_SURFACE=PASS",
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
        "${name}-ru.pdf",
        "${name}-en.pdf",
        "${name}-ru.pdf.sha256",
        "${name}-en.pdf.sha256",
    )
    for token in workflow_tokens:
        assert token in workflow, f"release workflow missing {token!r}"
    assert "RELEASE_VERSION" in workflow
    assert "tomllib" not in workflow
    assert "from torch2pc_thesis import __version__" not in workflow
    print("RELEASE_WORKFLOW_CONTRACT=PASS")

    for token in (
        "make thesis-all",
        "scripts/check_thesis_language_congruence.py",
        "thesis/main_EN.pdf",
        "THESIS_EN_PDF_SHA256",
    ):
        assert token in thesis_workflow, f"thesis workflow missing {token!r}"
    print("RELEASE_BILINGUAL_CI_CONTRACT=PASS")

    builder_tokens = (
        "make thesis-check",
        "make thesis-all",
        "source_git_tree",
        "release_tag",
        "THESIS_RU_PDF_SHA256",
        "THESIS_EN_PDF_SHA256",
        "SOURCE_ARCHIVE_SHA256",
        "THESIS_%s_OVERFULL_COUNT",
        'check_document "RU"',
        'check_document "EN"',
        "TRACKED_WORKTREE_UNCHANGED=PASS",
        ".release-manifest.json",
        '"thesis_pdf_ru"',
        '"thesis_pdf_en"',
        '"thesis_languages": ["ru", "en"]',
    )
    for token in builder_tokens:
        assert token in builder, f"release builder missing {token!r}"
    assert "RELEASE_VERSION" in builder
    assert "tomllib" not in builder
    assert "from torch2pc_thesis import __version__" not in builder
    print("RELEASE_ARTIFACT_CONTRACT=PASS")

    print("THESIS_V1_BILINGUAL_RELEASE_CONTRACT=PASS")
    print("THESIS_V1_RELEASE_CONTRACT=PASS")


if __name__ == "__main__":
    main()
