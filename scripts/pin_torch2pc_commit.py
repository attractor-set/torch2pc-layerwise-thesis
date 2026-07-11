#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
from pathlib import Path

import yaml


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/base.yaml")
    parser.add_argument("--checkout", default="external/Torch2PC")
    args = parser.parse_args()

    config_path = Path(args.config)
    checkout = Path(args.checkout)
    status = subprocess.check_output(
        ["git", "-C", str(checkout), "status", "--porcelain"], text=True
    ).strip()
    if status:
        raise RuntimeError("Torch2PC worktree must be clean before pinning")

    commit = subprocess.check_output(
        ["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True
    ).strip()
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise RuntimeError(f"Unexpected commit value: {commit}")

    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config["torch2pc"]["commit"] = commit
    config_path.write_text(
        yaml.safe_dump(config, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    output = Path("results/summaries/torch2pc_pin.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {
                "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "config": str(config_path),
                "checkout": str(checkout),
                "commit": commit,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(commit)


if __name__ == "__main__":
    main()
