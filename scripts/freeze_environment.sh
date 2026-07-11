#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

[[ -f .env ]] || { echo "Отсутствует .env" >&2; exit 1; }
[[ -d external/Torch2PC/.git ]] || { echo "Torch2PC не подготовлен" >&2; exit 1; }

set -a
. ./.env
set +a
mkdir -p results/summaries

python - "$EXPERIMENT_IMAGE" "$ROCM_PYTORCH_IMAGE" <<'INNERPY'
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import time
import yaml

experiment_image, base_image = sys.argv[1:3]

def output(args, required=True):
    try:
        return subprocess.check_output(
            args, text=True, stderr=subprocess.STDOUT, timeout=60
        ).strip()
    except Exception as exc:
        if required:
            raise
        return f"unavailable: {exc!r}"

def shell(command):
    return output(["bash", "-lc", command], required=False)

def image_info(reference):
    raw = output(["docker", "image", "inspect", reference])
    value = json.loads(raw)[0]
    return {
        "reference": reference,
        "id": value.get("Id"),
        "repo_digests": value.get("RepoDigests", []),
        "created": value.get("Created"),
        "source_git_commit_label": value.get("Config", {}).get("Labels", {}).get(
            "org.opencontainers.image.revision"
        ),
    }

def digest_record(path):
    return {
        "path": str(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }

config_files = sorted(Path("configs").rglob("*.yaml"))
source_files = [
    Path("pyproject.toml"), Path("Dockerfile.rocm"), Path("compose.yaml"),
    Path("Makefile"), Path(".env.example"),
    *sorted(Path("requirements").glob("*.txt")),
    *sorted(Path("src").rglob("*.py")),
    *sorted(Path("scripts").glob("*.py")),
    *sorted(Path("scripts").glob("*.sh")),
]

container_pip = output([
    "docker", "run", "--rm", "--entrypoint", "python",
    experiment_image, "-m", "pip", "freeze"
])
manifest = {
    "schema_version": 1,
    "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "source_git_commit_at_lock_creation": output(["git", "rev-parse", "HEAD"]),
    "source_worktree_clean_before_lock": output(["git", "status", "--porcelain"]) == "",
    "torch2pc_commit": output(["git", "-C", "external/Torch2PC", "rev-parse", "HEAD"]),
    "experiment_image": image_info(experiment_image),
    "base_image": image_info(base_image),
    "config_files": [digest_record(path) for path in config_files],
    "source_files": [digest_record(path) for path in source_files],
    "container_pip_freeze": container_pip.splitlines(),
    "host": {
        "os_release": shell("cat /etc/os-release"),
        "uname": output(["uname", "-a"], required=False),
        "lscpu": output(["lscpu"], required=False),
        "lspci_gpu": shell("lspci -nn | grep -Ei 'VGA|Display|AMD' || true"),
        "docker_version": output(["docker", "version"], required=False),
        "docker_compose_version": output(["docker", "compose", "version"], required=False),
        "rocminfo": shell("rocminfo 2>/dev/null | head -n 200 || true"),
        "rocm_smi": shell("rocm-smi --showproductname --showtemp --showclocks --showpower --showmeminfo vram 2>/dev/null || true"),
    },
}
manifest["image_source_git_commit"] = manifest["experiment_image"].get(
    "source_git_commit_label"
)
if not manifest["image_source_git_commit"] or not __import__("re").fullmatch(
    r"[0-9a-f]{40}", str(manifest["image_source_git_commit"])
):
    raise RuntimeError("Experiment image does not contain a valid source revision label")
if manifest["image_source_git_commit"] != manifest["source_git_commit_at_lock_creation"]:
    raise RuntimeError(
        "Experiment image was not built from the current clean source commit"
    )

base = yaml.safe_load(Path("configs/base.yaml").read_text(encoding="utf-8"))
expected = str(base["torch2pc"]["commit"])
if manifest["torch2pc_commit"] != expected:
    raise RuntimeError(
        f"Torch2PC commit mismatch: expected {expected}, observed {manifest['torch2pc_commit']}"
    )
if not manifest["source_worktree_clean_before_lock"]:
    raise RuntimeError("Environment lock requires a clean source worktree")
if not manifest["experiment_image"]["id"] or not manifest["base_image"]["id"]:
    raise RuntimeError("Immutable Docker image IDs were not observed")
Path("results/summaries/environment-lock.json").write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print("results/summaries/environment-lock.json")
INNERPY
