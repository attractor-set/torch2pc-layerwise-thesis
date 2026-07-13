#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from torch2pc_thesis.stage3 import stage3_readiness_report


def main() -> None:
    report = stage3_readiness_report(Path("."))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["status"] != 'ready_for_stage3_implementation':
        raise SystemExit(1)


if __name__ == "__main__":
    main()
