from __future__ import annotations

import argparse
import json
from pathlib import Path

from torch2pc_thesis.stage3b_b2_smoke import (
    aggregate_attempt,
    load_and_validate_request,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aggregate and seal one complete Stage 3B B2 smoke attempt."
    )
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("results/stage-3/b2"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    request = load_and_validate_request(args.request)
    attempt_root = args.output_root / str(request["attempt_id"])
    decision = aggregate_attempt(request, attempt_root)
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0 if decision["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
