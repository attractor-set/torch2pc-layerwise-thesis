#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.generate_final_execution_plan import (
    _load_json,
    _load_yaml,
    build_final_execution_plan,
)


def main() -> None:
    lock_path = Path("results/stage-2/summaries/environment-lock.json")
    if not lock_path.is_file():
        raise RuntimeError("Stage 2 environment lock is required before plan generation")
    base = _load_yaml(Path("configs/base.yaml"))
    stage2 = _load_yaml(Path("configs/stages/final_stage_2.yaml"))
    lock = _load_json(lock_path)
    plan = build_final_execution_plan(
        base,
        stage2,
        lock,
        environment_lock_sha256=hashlib.sha256(lock_path.read_bytes()).hexdigest(),
        stage="final_stage_2",
        test_access="once_per_completed_run_after_stage_2_freeze",
    )
    output = Path("results/stage-2/summaries/final_stage_2_execution_plan.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(plan, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(output)


if __name__ == "__main__":
    main()
