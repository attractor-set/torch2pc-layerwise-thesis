#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

python - <<'INNERPY'
from pathlib import Path
import hashlib
import json
import subprocess
import yaml
from torchvision import datasets, transforms

config = yaml.safe_load(Path("configs/base.yaml").read_text(encoding="utf-8"))
repo = Path(config["torch2pc"]["local_path"])
url = config["torch2pc"]["repository"]
pinned = str(config["torch2pc"].get("commit", "")).strip()
repo.parent.mkdir(parents=True, exist_ok=True)

if repo.exists():
    status = subprocess.check_output(
        ["git", "-C", str(repo), "status", "--porcelain"], text=True
    ).strip()
    if status:
        raise RuntimeError("Torch2PC worktree must be clean before asset preparation")

if not repo.exists():
    subprocess.run(["git", "clone", url, str(repo)], check=True)
else:
    actual_remote = subprocess.check_output(
        ["git", "-C", str(repo), "remote", "get-url", "origin"], text=True
    ).strip()
    if actual_remote.rstrip("/") != url.rstrip("/"):
        raise RuntimeError(
            f"Torch2PC origin mismatch: expected {url}, observed {actual_remote}"
        )
    subprocess.run(["git", "-C", str(repo), "fetch", "--all", "--tags"], check=True)

if pinned:
    subprocess.run(["git", "-C", str(repo), "checkout", "--detach", pinned], check=True)
actual_commit = subprocess.check_output(
    ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
).strip()
if pinned and actual_commit != pinned:
    raise RuntimeError(f"Torch2PC checkout mismatch: expected {pinned}, found {actual_commit}")
status = subprocess.check_output(
    ["git", "-C", str(repo), "status", "--porcelain"], text=True
).strip()
if status:
    raise RuntimeError("Torch2PC worktree changed during asset preparation")

transform = transforms.Compose([transforms.Pad(2), transforms.ToTensor()])
for cls in [datasets.MNIST, datasets.FashionMNIST, datasets.KMNIST]:
    cls(root="data", train=True, download=True, transform=transform)
    cls(root="data", train=False, download=True, transform=transform)

files = []
for path in sorted(Path("data").rglob("*")):
    if path.is_file():
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        files.append({"path": str(path), "bytes": path.stat().st_size, "sha256": digest})

output = Path("results/summaries/prepared_assets.json")
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(
    json.dumps(
        {
            "torch2pc_repository": url,
            "torch2pc_commit_observed": actual_commit,
            "torch2pc_commit_pinned": pinned or None,
            "dataset_files": files,
        },
        ensure_ascii=False,
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)
print(output)
if not pinned:
    print("Candidate Torch2PC commit. Review controls, then pin explicitly:", actual_commit)
INNERPY

# BEGIN canonical Torch2PC pin reconciliation
# Record the protocol-declared Torch2PC revision and verify that it matches
# the checkout that was actually used to prepare the experimental assets.

_script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
_repo_root="$(cd -- "${_script_dir}/.." && pwd)"

_pin_file="${_repo_root}/results/summaries/torch2pc_pin.json"
_prepared_assets_file="${_repo_root}/results/summaries/prepared_assets.json"
_torch2pc_checkout="${_repo_root}/external/Torch2PC"

if [[ ! -f "${_pin_file}" ]]; then
    echo "ERROR: canonical Torch2PC pin artifact not found: ${_pin_file}" >&2
    exit 1
fi

if [[ ! -f "${_prepared_assets_file}" ]]; then
    echo "ERROR: prepared-assets metadata not found: ${_prepared_assets_file}" >&2
    exit 1
fi

if [[ ! -d "${_torch2pc_checkout}/.git" ]]; then
    echo "ERROR: Torch2PC checkout is not a Git repository: ${_torch2pc_checkout}" >&2
    exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
    echo "ERROR: jq is required to validate Torch2PC provenance." >&2
    exit 1
fi

_pinned_commit="$(
    jq -er '.commit // empty' "${_pin_file}"
)"

_observed_commit="$(
    git -C "${_torch2pc_checkout}" rev-parse HEAD
)"

if [[ ! "${_pinned_commit}" =~ ^[0-9a-fA-F]{40}$ ]]; then
    echo "ERROR: invalid pinned Torch2PC commit: ${_pinned_commit}" >&2
    exit 1
fi

if [[ ! "${_observed_commit}" =~ ^[0-9a-fA-F]{40}$ ]]; then
    echo "ERROR: invalid observed Torch2PC commit: ${_observed_commit}" >&2
    exit 1
fi

if [[ "${_pinned_commit}" != "${_observed_commit}" ]]; then
    echo "ERROR: Torch2PC revision mismatch." >&2
    echo "  pinned:   ${_pinned_commit}" >&2
    echo "  observed: ${_observed_commit}" >&2
    exit 1
fi

_tmp_prepared_assets="$(
    mktemp "${_prepared_assets_file}.tmp.XXXXXX"
)"

cleanup_prepared_assets_tmp() {
    rm -f "${_tmp_prepared_assets}"
}

trap cleanup_prepared_assets_tmp EXIT

jq \
    --arg pinned "${_pinned_commit}" \
    --arg observed "${_observed_commit}" \
    '
      .torch2pc_commit_pinned = $pinned
      | .torch2pc_commit_observed = $observed
    ' \
    "${_prepared_assets_file}" \
    > "${_tmp_prepared_assets}"

mv "${_tmp_prepared_assets}" "${_prepared_assets_file}"
trap - EXIT

echo "Torch2PC provenance verified:"
echo "  pinned:   ${_pinned_commit}"
echo "  observed: ${_observed_commit}"
# END canonical Torch2PC pin reconciliation
