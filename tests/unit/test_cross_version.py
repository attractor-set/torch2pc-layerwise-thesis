from __future__ import annotations

import pandas as pd

from torch2pc_thesis import cross_version


def _frame(stage: str, time_factor: float, quality_offset: float) -> pd.DataFrame:
    rows = []
    for dataset in ["MNIST", "FashionMNIST"]:
        for seed in range(2):
            base_quality = 0.9 + seed * 0.001
            base_time = 10.0 + seed
            for method, slowdown, delta in [
                ("bp", 1.0, 0.0),
                ("exact", 1.2, 0.0),
                ("fixedpred", 2.7, 0.001),
                ("strict", 5.0, -0.001),
            ]:
                rows.append(
                    {
                        "stage": stage,
                        "test_evaluated": "true",
                        "dataset": dataset,
                        "model": "lenet_classic",
                        "method": method,
                        "model_seed": str(seed),
                        "test_accuracy": base_quality + delta + quality_offset,
                        "test_macro_f1": base_quality + delta + quality_offset,
                        "total_training_time_sec": base_time * slowdown * time_factor,
                        "mean_epoch_time_sec": base_time * slowdown * time_factor / 10,
                        "median_epoch_time_sec": base_time * slowdown * time_factor / 10,
                        "peak_gpu_memory_allocated_bytes": 100.0 * slowdown,
                        "peak_gpu_memory_reserved_bytes": 120.0 * slowdown,
                    }
                )
    return pd.DataFrame(rows)


def test_cross_version_analysis_pairs_identical_cells(tmp_path, monkeypatch) -> None:
    reference = _frame("final", 1.0, 0.0)
    candidate = _frame("final_stage_2", 0.8, 0.0)

    def fake_collect(path):
        return reference.copy() if str(path) == "reference.csv" else candidate.copy()

    monkeypatch.setattr(cross_version, "collect_metrics", fake_collect)
    outputs = cross_version.build_cross_version_assets("reference.csv", "candidate.csv", tmp_path)
    paired = pd.read_csv(outputs["paired_records"])
    assert len(paired) == 16
    assert paired["total_training_time_sec_ratio"].round(6).eq(0.8).all()
    did = pd.read_csv(outputs["difference_in_differences_records"])
    assert did["quality_difference_in_differences"].abs().max() < 1e-12
