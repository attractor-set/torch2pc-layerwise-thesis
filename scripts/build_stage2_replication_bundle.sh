#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

OUTPUT_DIR="${1:-artifacts}"
SOURCE_COMMIT="6d66b0a6f82c30c4fb8eca6247383ca13e0636a2"
RESULTS_MANIFEST="results/stage-2/summaries/results_manifest.json"
COMPLETION_FILE="results/stage-2/summaries/stage-2-completion.json"
SNAPSHOT_SIDECAR="experiments/registry-stage-2-80-completed.csv.sha256"

required_paths=(
  "$RESULTS_MANIFEST"
  "$COMPLETION_FILE"
  "$SNAPSHOT_SIDECAR"
  "results/stage-2/runs"
  "results/stage-2/summaries"
  "results/stage-2/tables"
  "results/cross-version"
  "experiments/registry-stage-2.csv"
  "experiments/registry-stage-2-80-completed.csv"
  "configs/stages/final_stage_2.yaml"
  "patches/torch2pc-patched-v1.patch"
  "patches/torch2pc-patched-v1.patch.sha256"
  "docs/stage-2-protocol.md"
  "docs/stage-2-protocol_EN.md"
  "docs/torch2pc-patched-v1-equivalence.md"
)

for path in "${required_paths[@]}"; do
  if [[ ! -e "$path" ]]; then
    printf 'Required Stage 2 artifact is missing: %s\n' "$path" >&2
    exit 1
  fi
done

if ! command -v zstd >/dev/null 2>&1; then
  printf '%s\n' 'zstd is required. On Ubuntu: sudo apt-get install zstd' >&2
  exit 1
fi

if [[ -n "$(git status --short --untracked-files=no)" ]]; then
  printf '%s\n' 'Tracked worktree changes are present; commit or restore them first.' >&2
  exit 1
fi

sha256sum -c "$SNAPSHOT_SIDECAR"

python3 - <<'PY'
from __future__ import annotations

import hashlib
import json
from pathlib import Path

root = Path("results/stage-2")
manifest_path = root / "summaries/results_manifest.json"
completion_path = root / "summaries/stage-2-completion.json"

completion = json.loads(completion_path.read_text(encoding="utf-8"))
if completion.get("completed_unique_cells") != 80:
    raise SystemExit("Stage 2 completion artifact does not report 80 unique cells")
if completion.get("all_test_evaluated") is not True:
    raise SystemExit("Stage 2 completion artifact does not confirm all test evaluations")

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
entries = manifest.get("artifacts", {}).get("files", [])
if not entries:
    raise SystemExit("Stage 2 results manifest contains no artifacts")

missing: list[str] = []
mismatched: list[str] = []
for entry in entries:
    relative = Path(entry["path"])
    path = root / relative
    if not path.is_file():
        missing.append(relative.as_posix())
        continue
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != entry["sha256"]:
        mismatched.append(relative.as_posix())

if missing or mismatched:
    if missing:
        print("Missing manifest artifacts:")
        print("\n".join(f"  - {path}" for path in missing))
    if mismatched:
        print("Hash-mismatched manifest artifacts:")
        print("\n".join(f"  - {path}" for path in mismatched))
    raise SystemExit(1)

source_commit = manifest.get("environment", {}).get("source_git_commit")
expected_source = "6d66b0a6f82c30c4fb8eca6247383ca13e0636a2"
if source_commit != expected_source:
    raise SystemExit(
        f"Unexpected Stage 2 execution source: {source_commit!r}; "
        f"expected {expected_source}"
    )

print(f"Verified {len(entries)} Stage 2 manifest artifacts")
print(f"Stage 2 execution source: {source_commit}")
PY

mkdir -p "$OUTPUT_DIR"
HEAD_SHORT="$(git rev-parse --short=12 HEAD)"
BASENAME="torch2pc-stage2-replication-${HEAD_SHORT}"
BUNDLE="$OUTPUT_DIR/${BASENAME}.tar.zst"
FILE_MANIFEST="$OUTPUT_DIR/${BASENAME}.files.sha256"
BUNDLE_SIDECAR="$BUNDLE.sha256"
FILE_LIST="$(mktemp)"
trap 'rm -f "$FILE_LIST"' EXIT

{
  printf '%s\n' \
    README.md \
    LICENSE \
    LICENSE-DOCS \
    CITATION.cff \
    configs/stages/final_stage_2.yaml \
    experiments/registry-stage-2.csv \
    experiments/registry-stage-2-80-completed.csv \
    experiments/registry-stage-2-80-completed.csv.sha256 \
    patches/torch2pc-patched-v1.patch \
    patches/torch2pc-patched-v1.patch.sha256 \
    docs/stage-2-protocol.md \
    docs/stage-2-protocol_EN.md \
    docs/torch2pc-patched-v1-equivalence.md
  find results/stage-2/runs -type f -print
  find results/stage-2/summaries -type f -print
  find results/stage-2/tables -type f -print
  find results/cross-version -type f -print
} | LC_ALL=C sort -u > "$FILE_LIST"

: > "$FILE_MANIFEST"
while IFS= read -r path; do
  sha256sum "$path" >> "$FILE_MANIFEST"
done < "$FILE_LIST"
printf '%s\n' "$FILE_MANIFEST" >> "$FILE_LIST"

rm -f "$BUNDLE" "$BUNDLE_SIDECAR"
tar \
  --sort=name \
  --mtime='UTC 1970-01-01' \
  --owner=0 \
  --group=0 \
  --numeric-owner \
  --pax-option=delete=atime,delete=ctime \
  -cf - \
  -T "$FILE_LIST" \
  | zstd --no-progress -19 -T0 -o "$BUNDLE"

sha256sum "$BUNDLE" > "$BUNDLE_SIDECAR"

printf 'Created Stage 2 replication bundle:\n'
printf '  archive:       %s\n' "$BUNDLE"
printf '  archive SHA:   %s\n' "$BUNDLE_SIDECAR"
printf '  file manifest: %s\n' "$FILE_MANIFEST"
printf '  execution:     %s\n' "$SOURCE_COMMIT"
