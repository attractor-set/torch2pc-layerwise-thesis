from __future__ import annotations

import argparse
import json
from pathlib import Path

from torch2pc_thesis.models import build_model
from torch2pc_thesis.stage3b_b1_smoke import (
    build_pair_specs,
    load_and_validate_request,
    run_pair,
    write_pair_result,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate or execute the preregistered Stage 3B B1 smoke request."
    )
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--torch2pc-dir", type=Path, default=Path("external/Torch2PC"))
    parser.add_argument("--output-root", type=Path, default=Path("results/stage-3/b1"))
    parser.add_argument("--lane", choices=("cpu_float64", "rocm_float32"))
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    request = load_and_validate_request(args.request)
    specs = build_pair_specs(request)
    selected = [spec for spec in specs if args.lane is None or spec.lane == args.lane]
    print(
        json.dumps(
            {
                "request_id": request["request_id"],
                "attempt_id": request["attempt_id"],
                "selected_pairs": [spec.pair_id for spec in selected],
                "execute": args.execute,
            },
            indent=2,
            sort_keys=True,
        )
    )
    if not args.execute:
        return 0

    attempt_root = args.output_root / str(request["attempt_id"])
    for spec in selected:
        result = run_pair(
            spec,
            torch2pc_dir=args.torch2pc_dir,
            model_builder=build_model,
        )
        pair_dir = write_pair_result(attempt_root, result)
        print(f"wrote {pair_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
