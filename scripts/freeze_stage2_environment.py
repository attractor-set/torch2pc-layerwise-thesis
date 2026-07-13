#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any

from torch2pc_thesis.assets import sha256_file, validate_prepared_assets
from torch2pc_thesis.config import resolve_config


def output(args: list[str], *, required: bool = True) -> str:
    try:
        return subprocess.check_output(
            args, text=True, stderr=subprocess.STDOUT, timeout=120
        ).strip()
    except Exception as exc:
        if required:
            raise
        return f"unavailable: {exc!r}"


def shell(command: str) -> str:
    return output(["bash", "-lc", command], required=False)


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = value.strip().strip('"').strip("'")
    return values


def image_info(reference: str) -> dict[str, Any]:
    value = json.loads(output(["docker", "image", "inspect", reference]))[0]
    return {
        "reference": reference,
        "id": value.get("Id"),
        "repo_digests": value.get("RepoDigests", []),
        "created": value.get("Created"),
        "source_git_commit_label": value.get("Config", {}).get("Labels", {}).get(
            "org.opencontainers.image.revision"
        ),
    }


def digest_record(path: Path) -> dict[str, str]:
    return {"path": str(path), "sha256": sha256_file(path)}


def digest_records(records: list[dict[str, str]]) -> str:
    canonical = json.dumps(
        sorted(records, key=lambda item: item["path"]),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def assert_clean_checkout(path: Path, expected_commit: str, label: str) -> None:
    actual = output(["git", "-C", str(path), "rev-parse", "HEAD"])
    if actual != expected_commit:
        raise RuntimeError(
            f"{label} commit mismatch: expected {expected_commit}, observed {actual}"
        )
    status = output(["git", "-C", str(path), "status", "--porcelain"])
    if status:
        raise RuntimeError(f"{label} worktree must be clean")


def main() -> None:
    env_path = Path(".env")
    if not env_path.is_file():
        raise RuntimeError(".env is required")
    env = {**load_env(env_path), **os.environ}
    experiment_image = env["EXPERIMENT_IMAGE"]
    base_image = env["ROCM_PYTORCH_IMAGE"]
    config = resolve_config("configs", stage="final_stage_2", method="exact")

    candidate_path = Path(config["torch2pc"]["local_path"])
    candidate_commit = str(config["torch2pc"]["commit"])
    comparison = config["comparison"]
    reference_path = Path(comparison["original_torch2pc_path"])
    reference_commit = str(comparison["original_torch2pc_commit"])
    assert_clean_checkout(candidate_path, candidate_commit, "Candidate Torch2PC")
    assert_clean_checkout(reference_path, reference_commit, "Reference Torch2PC")

    source_commit = output(["git", "rev-parse", "HEAD"])
    if not re.fullmatch(r"[0-9a-f]{40}", source_commit):
        raise RuntimeError("A full source Git revision is required")
    if output(["git", "status", "--porcelain"]):
        raise RuntimeError("Stage 2 environment lock requires a clean source worktree")

    config_files = sorted(Path("configs").rglob("*.yaml"))
    config_records = [digest_record(path) for path in config_files]
    source_files = [
        Path("pyproject.toml"),
        Path("Dockerfile.rocm"),
        Path("compose.yaml"),
        Path("Makefile"),
        Path(".env.example"),
        *sorted(Path("requirements").glob("*.txt")),
        *sorted(Path("src").rglob("*.py")),
        *sorted(Path("scripts").glob("*.py")),
        *sorted(Path("scripts").glob("*.sh")),
    ]

    prepared_assets_path = Path(config["paths"]["summaries"]) / "prepared_assets.json"
    prepared_assets = validate_prepared_assets(prepared_assets_path, verify_hashes=True)
    if prepared_assets.get("torch2pc_commit_pinned") != candidate_commit:
        raise RuntimeError("Stage 2 prepared-assets metadata contains another commit")

    experiment = image_info(experiment_image)
    base = image_info(base_image)
    if experiment.get("source_git_commit_label") != source_commit:
        raise RuntimeError("Experiment image was not built from the current source commit")

    container_pip = output(
        [
            "docker",
            "run",
            "--rm",
            "--entrypoint",
            "python",
            experiment_image,
            "-m",
            "pip",
            "freeze",
        ]
    )
    runtime = output(
        [
            "docker",
            "run",
            "--rm",
            "--entrypoint",
            "python",
            experiment_image,
            "-c",
            (
                "import json, platform, torch, torchvision; "
                "print(json.dumps({'python': platform.python_version(), "
                "'torch': torch.__version__, 'torchvision': torchvision.__version__, "
                "'hip': getattr(torch.version, 'hip', None)}, sort_keys=True))"
            ),
        ]
    )

    manifest: dict[str, Any] = {
        "schema_version": 2,
        "campaign_stage": "final_stage_2",
        "campaign_id": config["meta"]["campaign_id"],
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_git_commit_at_lock_creation": source_commit,
        "source_worktree_clean_before_lock": True,
        "image_source_git_commit": experiment.get("source_git_commit_label"),
        "torch2pc_commit": candidate_commit,
        "torch2pc_worktree_clean": True,
        "torch2pc_reference_commit": reference_commit,
        "torch2pc_reference_worktree_clean": True,
        "prepared_assets": {
            "path": str(prepared_assets_path),
            "sha256": sha256_file(prepared_assets_path),
            "dataset_file_count": len(prepared_assets["dataset_files"]),
        },
        "experiment_image": experiment,
        "base_image": base,
        "config_sha256": digest_records(config_records),
        "config_sha256_kind": "sha256_of_sorted_config_path_and_content_digests",
        "config_files": config_records,
        "source_files": [digest_record(path) for path in source_files],
        "container_pip_freeze": container_pip.splitlines(),
        "container_python_runtime": json.loads(runtime),
        "host": {
            "os_release": shell("cat /etc/os-release"),
            "uname": output(["uname", "-a"], required=False),
            "lscpu": output(["lscpu"], required=False),
            "lspci_gpu": shell("lspci -nn | grep -Ei 'VGA|Display|AMD' || true"),
            "docker_version": output(["docker", "version"], required=False),
            "docker_compose_version": output(
                ["docker", "compose", "version"], required=False
            ),
            "rocminfo": shell("rocminfo 2>/dev/null | head -n 200 || true"),
            "rocm_smi": shell(
                "rocm-smi --showproductname --showtemp --showclocks --showpower "
                "--showmeminfo vram 2>/dev/null || true"
            ),
        },
    }
    destination = Path(config["protocol"]["environment_lock"])
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(destination)


if __name__ == "__main__":
    main()
