#!/usr/bin/env bash
set -euo pipefail
cd /workspace

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
