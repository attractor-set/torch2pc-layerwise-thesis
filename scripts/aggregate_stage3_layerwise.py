#!/usr/bin/env python3
"""Aggregate Stage 3 layer-wise probe outputs without treating layers as replicas."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def concatenate(paths: list[Path]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for path in paths:
        frame = pd.read_csv(path)
        frame.insert(0, "source_file", str(path))
        frames.append(frame)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    tables = {
        "all_gradient_metrics.csv": sorted(args.root.rglob("gradient_metrics.csv")),
        "all_gradient_summaries.csv": sorted(args.root.rglob("gradient_summary.csv")),
        "all_representation_metrics.csv": sorted(args.root.rglob("representation_metrics.csv")),
        "all_cross_layer_cka.csv": sorted(args.root.rglob("cross_layer_cka.csv")),
    }
    for filename, paths in tables.items():
        concatenate(paths).to_csv(args.output / filename, index=False)


if __name__ == "__main__":
    main()
