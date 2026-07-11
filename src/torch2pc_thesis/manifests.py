from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def command_output(command: list[str]) -> str:
    try:
        return subprocess.check_output(
            command,
            text=True,
            stderr=subprocess.STDOUT,
            timeout=30,
        ).strip()
    except Exception as exc:
        return f"unavailable: {exc!r}"


def git_head(path: str | Path = ".") -> str:
    return command_output(["git", "-C", str(path), "rev-parse", "HEAD"])


def environment_snapshot() -> dict[str, Any]:
    environment_lock = Path("results/summaries/environment-lock.json")
    snapshot: dict[str, Any] = {
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "python": sys.version,
        "platform": platform.platform(),
        "kernel": platform.release(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "source_git_commit": os.environ.get("SOURCE_GIT_COMMIT") or git_head("."),
        "image_reference": os.environ.get("EXPERIMENT_IMAGE"),
        "base_image_reference": os.environ.get("ROCM_PYTORCH_IMAGE"),
        "environment_lock_sha256": (
            sha256_file(environment_lock) if environment_lock.exists() else None
        ),
        "uname": command_output(["uname", "-a"]),
        "lscpu": command_output(["lscpu"]),
        "pip_freeze": command_output([sys.executable, "-m", "pip", "freeze"]),
    }
    try:
        import torch

        snapshot.update(
            {
                "torch": torch.__version__,
                "hip": getattr(torch.version, "hip", None),
                "cuda_api_available": torch.cuda.is_available(),
                "device_name": (
                    torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
                ),
            }
        )
    except Exception as exc:
        snapshot["torch_error"] = repr(exc)
    return snapshot


def directory_manifest(directory: str | Path) -> dict[str, Any]:
    root = Path(directory)
    files = []
    for path in sorted(root.rglob("*")):
        if path.is_file():
            files.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
    return {"root": str(root), "files": files}


def write_json(value: Any, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return output
