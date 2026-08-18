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
  echo "Релиз создается только из неизмененного tracked Git state." >&2
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
make thesis

log="thesis/main.log"
pdf="thesis/main.pdf"
if [[ ! -s "$pdf" ]]; then
  echo "Final thesis PDF is missing or empty." >&2
  exit 1
fi
if ! command -v pdfinfo >/dev/null 2>&1; then
  echo "pdfinfo is required to build the release manifest." >&2
  exit 1
fi

count_log_pattern() {
  local pattern="$1"
  grep -Ec "$pattern" "$log" 2>/dev/null || true
}

overfull_count="$(count_log_pattern 'Overfull \\hbox')"
undefined_reference_count="$(count_log_pattern 'LaTeX Warning: Reference .* undefined|There were undefined references')"
undefined_citation_count="$(count_log_pattern 'LaTeX Warning: Citation .* undefined|There were undefined citations')"
rerun_reference_count="$(count_log_pattern 'Rerun to get cross-references right')"
pages="$(pdfinfo "$pdf" | awk '/^Pages:/ {print $2}')"

printf 'THESIS_OVERFULL_COUNT=%s\n' "$overfull_count"
printf 'THESIS_UNDEFINED_REFERENCES_COUNT=%s\n' "$undefined_reference_count"
printf 'THESIS_UNDEFINED_CITATIONS_COUNT=%s\n' "$undefined_citation_count"
printf 'THESIS_RERUN_REFERENCES_COUNT=%s\n' "$rerun_reference_count"
printf 'THESIS_PAGES=%s\n' "$pages"

if [[ "$overfull_count" != "0" || \
      "$undefined_reference_count" != "0" || \
      "$undefined_citation_count" != "0" || \
      "$rerun_reference_count" != "0" ]]; then
  echo "Final thesis document contract failed." >&2
  exit 1
fi

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "Release validation changed tracked source files." >&2
  git status --short --untracked-files=no >&2
  exit 1
fi
echo "TRACKED_WORKTREE_UNCHANGED=PASS"

rm -rf artifacts
mkdir -p artifacts

source_archive="artifacts/${name}.zip"
pdf_artifact="artifacts/${name}.pdf"
metadata_artifact="artifacts/${name}.metadata.json"
manifest_artifact="artifacts/${name}.release-manifest.json"
notes_artifact="artifacts/${name}.release-notes.md"

git archive --format=zip --prefix="${name}/" \
  --output="$source_archive" HEAD
cp "$pdf" "$pdf_artifact"

source_sha256="$(sha256sum "$source_archive" | awk '{print $1}')"
pdf_sha256="$(sha256sum "$pdf_artifact" | awk '{print $1}')"
printf '%s  %s\n' "$source_sha256" "${name}.zip" > "${source_archive}.sha256"
printf '%s  %s\n' "$pdf_sha256" "${name}.pdf" > "${pdf_artifact}.sha256"

"$PYTHON_BIN" - \
  "$name" "$version" "$release_tag" "$commit" "$tree" \
  "$source_sha256" "$pdf_sha256" "$pages" \
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
    pdf_sha256,
    pages,
    metadata_path,
    manifest_path,
) = sys.argv[1:]

metadata = {
    "schema_version": 2,
    "artifact": f"{name}.zip",
    "project_version": version,
    "release_tag": release_tag,
    "source_git_commit": commit,
    "source_git_tree": tree,
}
Path(metadata_path).write_text(
    json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)

manifest = {
    "schema_version": 1,
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
        "thesis_pdf": {
            "name": f"{name}.pdf",
            "sha256": pdf_sha256,
            "pages": int(pages),
        },
    },
    "verification": {
        "release_contract": "PASS",
        "thesis_check": "PASS",
        "thesis_build": "PASS",
        "thesis_overfull_count": 0,
        "thesis_undefined_references_count": 0,
        "thesis_undefined_citations_count": 0,
        "thesis_rerun_references_count": 0,
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

Final integrated thesis release after the T24 independent scientific-review closure.

- Version: \`${version}\`
- Source commit: \`${commit}\`
- Source tree: \`${tree}\`
- Thesis pages: \`${pages}\`
- Source archive SHA256: \`${source_sha256}\`
- Thesis PDF SHA256: \`${pdf_sha256}\`
- Semantic/traceability thesis checks: PASS
- Overfull boxes: 0
- Undefined references: 0
- Undefined citations: 0
- Pending cross-reference rerun warnings: 0

The release preserves the registered C01–C11 epistemic statuses and the explicit external-validity boundaries of the final dissertation text.
EOF

printf 'RELEASE_VERSION=%s\n' "$version"
printf 'RELEASE_TAG=%s\n' "$release_tag"
printf 'RELEASE_COMMIT=%s\n' "$commit"
printf 'RELEASE_TREE=%s\n' "$tree"
printf 'SOURCE_ARCHIVE_SHA256=%s\n' "$source_sha256"
printf 'THESIS_PDF_SHA256=%s\n' "$pdf_sha256"
printf 'THESIS_PAGES=%s\n' "$pages"
printf 'RELEASE_ARTIFACTS=PASS\n'
