import pandas as pd

from torch2pc_thesis.reporting import build_paired_primary_analysis


def _final_frame(candidate_offset: float, seeds: range) -> pd.DataFrame:
    rows = []
    for seed in seeds:
        baseline = 0.80 + seed * 0.001
        rows.extend(
            [
                {
                    "stage": "final",
                    "dataset": "FashionMNIST",
                    "model": "lenet_classic",
                    "method": "bp",
                    "model_seed": str(seed),
                    "test_macro_f1": baseline,
                },
                {
                    "stage": "final",
                    "dataset": "FashionMNIST",
                    "model": "lenet_classic",
                    "method": "fixedpred",
                    "model_seed": str(seed),
                    "test_macro_f1": baseline + candidate_offset,
                },
                {
                    "stage": "final",
                    "dataset": "FashionMNIST",
                    "model": "lenet_classic",
                    "method": "strict",
                    "model_seed": str(seed),
                    "test_macro_f1": baseline - candidate_offset,
                },
            ]
        )
    return pd.DataFrame(rows)


def test_paired_primary_analysis_requires_minimum_pairs() -> None:
    result = build_paired_primary_analysis(_final_frame(0.002, range(3)))
    assert not result["confirmatory_complete"].any()
    assert result["sign_flip_p_holm"].isna().all()
    assert not result["equivalent_within_margin"].any()


def test_paired_primary_analysis_reports_equivalence_only_when_complete() -> None:
    result = build_paired_primary_analysis(_final_frame(0.002, range(10)))
    assert result["confirmatory_complete"].all()
    assert result["equivalent_within_margin"].all()
    assert result["sign_flip_p_holm"].notna().all()
