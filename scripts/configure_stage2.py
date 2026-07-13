#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

import yaml


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", required=True)
    parser.add_argument("--repository")
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.commit):
        raise SystemExit("--commit must be a full 40-character lowercase Git SHA")

    path = Path("configs/stages/final_stage_2.yaml")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    original = str(value["comparison"]["original_torch2pc_commit"])
    if args.commit == original:
        raise SystemExit("Stage 2 candidate commit must differ from Stage 1")
    value["torch2pc"]["commit"] = args.commit
    if args.repository:
        value["torch2pc"]["repository"] = args.repository
    path.write_text(
        yaml.safe_dump(value, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    print(path)


if __name__ == "__main__":
    main()
