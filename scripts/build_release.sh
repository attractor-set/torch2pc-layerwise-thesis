#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

PYTHON_BIN="${PYTHON_BIN:-.venv/bin/python3}"
if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="$(command -v python3)"
fi

# Untracked scientific/runtime evidence is intentionally outside the release
# archive and must not block packaging. Tracked source/index changes do.
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "Release packaging requires an unchanged tracked Git state." >&2
  exit 1
fi

version="$(< RELEASE_VERSION)"
expected_tag="v${version}"
release_tag="${RELEASE_TAG:-${GITHUB_REF_NAME:-$expected_tag}}"
commit="$(git rev-parse HEAD)"
tree="$(git rev-parse HEAD^{tree})"
name="torch2pc-layerwise-thesis-${version}"

if [[ "$release_tag" != "$expected_tag" ]]; then
  printf 'Release tag %s does not match release version %s (expected %s).\n' \
    "$release_tag" "$version" "$expected_tag" >&2
  exit 1
fi

if git rev-parse -q --verify "refs/tags/${release_tag}^{commit}" >/dev/null; then
  tagged_commit="$(git rev-parse "refs/tags/${release_tag}^{commit}")"
  if [[ "$tagged_commit" != "$commit" ]]; then
    printf 'Tag %s resolves to %s, not HEAD %s.\n' \
      "$release_tag" "$tagged_commit" "$commit" >&2
    exit 1
  fi
fi

"$PYTHON_BIN" scripts/check_public_surface.py
"$PYTHON_BIN" scripts/check_release_contract.py
make thesis-check
make thesis-all

if ! command -v pdfinfo >/dev/null 2>&1; then
  echo "pdfinfo is required to build the release manifest." >&2
  exit 1
fi

check_document() {
  local language="$1"
  local log="$2"
  local pdf="$3"

  if [[ ! -s "$pdf" ]]; then
    printf '%s thesis PDF is missing or empty: %s\n' "$language" "$pdf" >&2
    return 1
  fi

  local overfull_count
  local undefined_reference_count
  local undefined_citation_count
  local rerun_reference_count
  local pages

  overfull_count="$(grep -Ec 'Overfull \\hbox' "$log" 2>/dev/null || true)"
  undefined_reference_count="$(grep -Ec 'LaTeX Warning: Reference .* undefined|There were undefined references' "$log" 2>/dev/null || true)"
  undefined_citation_count="$(grep -Ec 'LaTeX Warning: Citation .* undefined|There were undefined citations' "$log" 2>/dev/null || true)"
  rerun_reference_count="$(grep -Ec 'Rerun to get cross-references right' "$log" 2>/dev/null || true)"
  pages="$(pdfinfo "$pdf" | awk '/^Pages:/ {print $2}')"

  printf 'THESIS_%s_OVERFULL_COUNT=%s\n' "$language" "$overfull_count"
  printf 'THESIS_%s_UNDEFINED_REFERENCES_COUNT=%s\n' "$language" "$undefined_reference_count"
  printf 'THESIS_%s_UNDEFINED_CITATIONS_COUNT=%s\n' "$language" "$undefined_citation_count"
  printf 'THESIS_%s_RERUN_REFERENCES_COUNT=%s\n' "$language" "$rerun_reference_count"
  printf 'THESIS_%s_PAGES=%s\n' "$language" "$pages"

  if [[ "$overfull_count" != "0" || \
        "$undefined_reference_count" != "0" || \
        "$undefined_citation_count" != "0" || \
        "$rerun_reference_count" != "0" ]]; then
    printf '%s thesis document contract failed.\n' "$language" >&2
    return 1
  fi
}

ru_pdf="thesis/main.pdf"
en_pdf="thesis/main_EN.pdf"
check_document "RU" "thesis/main.log" "$ru_pdf"
check_document "EN" "thesis/main_EN.log" "$en_pdf"

ru_pages="$(pdfinfo "$ru_pdf" | awk '/^Pages:/ {print $2}')"
en_pages="$(pdfinfo "$en_pdf" | awk '/^Pages:/ {print $2}')"

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "Release validation changed tracked source files." >&2
  git status --short --untracked-files=no >&2
  exit 1
fi
echo "TRACKED_WORKTREE_UNCHANGED=PASS"

rm -rf artifacts
mkdir -p artifacts

source_archive="artifacts/${name}.zip"
ru_pdf_artifact="artifacts/${name}-ru.pdf"
en_pdf_artifact="artifacts/${name}-en.pdf"
metadata_artifact="artifacts/${name}.metadata.json"
manifest_artifact="artifacts/${name}.release-manifest.json"
notes_artifact="artifacts/${name}.release-notes.md"

git archive --format=zip --prefix="${name}/" \
  --output="$source_archive" HEAD
cp "$ru_pdf" "$ru_pdf_artifact"
cp "$en_pdf" "$en_pdf_artifact"

source_sha256="$(sha256sum "$source_archive" | awk '{print $1}')"
ru_pdf_sha256="$(sha256sum "$ru_pdf_artifact" | awk '{print $1}')"
en_pdf_sha256="$(sha256sum "$en_pdf_artifact" | awk '{print $1}')"
printf '%s  %s\n' "$source_sha256" "${name}.zip" > "${source_archive}.sha256"
printf '%s  %s\n' "$ru_pdf_sha256" "${name}-ru.pdf" > "${ru_pdf_artifact}.sha256"
printf '%s  %s\n' "$en_pdf_sha256" "${name}-en.pdf" > "${en_pdf_artifact}.sha256"

"$PYTHON_BIN" - \
  "$name" "$version" "$release_tag" "$commit" "$tree" \
  "$source_sha256" "$ru_pdf_sha256" "$ru_pages" \
  "$en_pdf_sha256" "$en_pages" \
  "$metadata_artifact" "$manifest_artifact" <<'PY'
from pathlib import Path
import json
import sys

(
    name,
    version,
    release_tag,
    commit,
    tree,
    source_sha256,
    ru_pdf_sha256,
    ru_pages,
    en_pdf_sha256,
    en_pages,
    metadata_path,
    manifest_path,
) = sys.argv[1:]

metadata = {
    "schema_version": 3,
    "artifact": f"{name}.zip",
    "project_version": version,
    "release_tag": release_tag,
    "source_git_commit": commit,
    "source_git_tree": tree,
    "thesis_languages": ["ru", "en"],
}
Path(metadata_path).write_text(
    json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)

manifest = {
    "schema_version": 2,
    "release": {
        "project": "torch2pc-layerwise-thesis",
        "version": version,
        "tag": release_tag,
        "source_git_commit": commit,
        "source_git_tree": tree,
    },
    "assets": {
        "source_archive": {
            "name": f"{name}.zip",
            "sha256": source_sha256,
        },
        "thesis_pdf_ru": {
            "language": "ru",
            "name": f"{name}-ru.pdf",
            "sha256": ru_pdf_sha256,
            "pages": int(ru_pages),
        },
        "thesis_pdf_en": {
            "language": "en",
            "name": f"{name}-en.pdf",
            "sha256": en_pdf_sha256,
            "pages": int(en_pages),
        },
    },
    "verification": {
        "release_contract": "PASS",
        "thesis_check": "PASS",
        "thesis_language_congruence": "PASS",
        "thesis_build_ru": "PASS",
        "thesis_build_en": "PASS",
        "thesis_ru_overfull_count": 0,
        "thesis_ru_undefined_references_count": 0,
        "thesis_ru_undefined_citations_count": 0,
        "thesis_ru_rerun_references_count": 0,
        "thesis_en_overfull_count": 0,
        "thesis_en_undefined_references_count": 0,
        "thesis_en_undefined_citations_count": 0,
        "thesis_en_rerun_references_count": 0,
        "tracked_worktree_unchanged": "PASS",
    },
}
Path(manifest_path).write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
PY

cat > "$notes_artifact" <<EOF
# Torch2PC Layer-wise Thesis ${release_tag}

Bilingual dissertation publication release. The scientific claims, registered
C01–C11 epistemic statuses, evidence bindings, and T24 external-validity boundaries
are unchanged from v1.0.0; this release adds the complete English rendering and a
language-explicit release asset contract.

- Version: \`${version}\`
- Source commit: \`${commit}\`
- Source tree: \`${tree}\`
- Russian thesis pages: \`${ru_pages}\`
- English thesis pages: \`${en_pages}\`
- Source archive SHA256: \`${source_sha256}\`
- Russian PDF SHA256: \`${ru_pdf_sha256}\`
- English PDF SHA256: \`${en_pdf_sha256}\`
- Semantic/traceability/language-congruence thesis checks: PASS
- Overfull boxes: 0 in both language builds
- Undefined references/citations: 0 in both language builds
- Pending cross-reference rerun warnings: 0 in both language builds
EOF

printf 'RELEASE_VERSION=%s\n' "$version"
printf 'RELEASE_TAG=%s\n' "$release_tag"
printf 'RELEASE_COMMIT=%s\n' "$commit"
printf 'RELEASE_TREE=%s\n' "$tree"
printf 'SOURCE_ARCHIVE_SHA256=%s\n' "$source_sha256"
printf 'THESIS_RU_PDF_SHA256=%s\n' "$ru_pdf_sha256"
printf 'THESIS_EN_PDF_SHA256=%s\n' "$en_pdf_sha256"
printf 'THESIS_RU_PAGES=%s\n' "$ru_pages"
printf 'THESIS_EN_PAGES=%s\n' "$en_pages"
printf 'RELEASE_ARTIFACTS=PASS\n'
