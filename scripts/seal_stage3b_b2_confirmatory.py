#!/usr/bin/env python3
"""Seal one complete 120-triple confirmatory Stage 3B B2 campaign."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from torch2pc_thesis.stage3b_b2_confirmatory import (
    load_and_validate_confirmatory_request,
    load_json_object,
)
from torch2pc_thesis.stage3b_b2_confirmatory_sealing import (
    seal_b2_confirmatory_campaign,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    request = load_and_validate_confirmatory_request(args.request)
    authorization = load_json_object(args.authorization)
    decision = seal_b2_confirmatory_campaign(
        request,
        authorization,
        output_root=args.output_root,
    )
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0 if decision["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
