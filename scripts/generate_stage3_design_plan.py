#!/usr/bin/env python3
from __future__ import annotations

from torch2pc_thesis.stage3 import load_stage3_design, write_stage3_design_plan


def main() -> None:
    design = load_stage3_design()
    print(write_stage3_design_plan(design))


if __name__ == "__main__":
    main()
