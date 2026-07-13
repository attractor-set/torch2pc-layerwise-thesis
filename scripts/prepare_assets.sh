#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

ASSET_STAGE="${ASSET_STAGE:-final}"
export ASSET_STAGE

python - <<'INNERPY'
from pathlib import Path
import hashlib
import json
import os
import subprocess
from torchvision import datasets, transforms

from torch2pc_thesis.config import resolve_config

stage = os.environ["ASSET_STAGE"]
config = resolve_config("configs", stage=stage, method="exact")
repo = Path(config["torch2pc"]["local_path"])
url = str(config["torch2pc"]["repository"])
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

output = Path(config["paths"]["summaries"]) / "prepared_assets.json"
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(
    json.dumps(
        {
            "campaign_stage": stage,
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
print("Torch2PC provenance verified:")
print(f"  pinned:   {pinned}")
print(f"  observed: {actual_commit}")
INNERPY
