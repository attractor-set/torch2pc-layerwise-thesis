#!/usr/bin/env python3
"""Validate thesis-facing data and render deterministic LaTeX assets."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THESIS = ROOT / "thesis"
CLAIMS_PATH = THESIS / "data" / "research_claims.json"
QWAKE_PATH = THESIS / "data" / "qwake_c2_verified_summary.json"
CORE_RESULTS_PATH = THESIS / "data" / "core_results_verified_summary.json"
GENERATED = THESIS / "generated"
CLAIMS_TEX = GENERATED / "claims_matrix.tex"
PROGRAM_TEX = GENERATED / "experimental_program.tex"
STAGE12_TEX = GENERATED / "stage12_results.tex"
STAGE3_TEX = GENERATED / "stage3_results.tex"
QWAKE_TEX = GENERATED / "qwake_results.tex"
REPRO_TEX = GENERATED / "reproducibility_manifest.tex"

STATUS_LABELS = {
    "supported": "поддержано",
    "rejected": "отклонено",
    "not_tested": "не проверено",
    "descriptive": "описательно",
}


def load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def latex_escape(value: object) -> str:
    text = str(value)
    replacements = (
        ("\\", r"\textbackslash{}"),
        ("&", r"\&"),
        ("%", r"\%"),
        ("$", r"\$"),
        ("#", r"\#"),
        ("_", r"\_"),
        ("{", r"\{"),
        ("}", r"\}"),
        ("~", r"\textasciitilde{}"),
        ("^", r"\textasciicircum{}"),
    )
    for source, target in replacements:
        text = text.replace(source, target)
    return text


def latex_breakable(value: object) -> str:
    return latex_escape(value).replace(r"\_", r"\_\allowbreak{}")


def latex_code(value: object) -> str:
    text = str(value).replace("\\", "/")
    return r"\code{" + text + "}"


def latex_digest(value: object) -> str:
    text = str(value)
    if not text.startswith("sha256:") or len(text) != 71:
        return latex_escape(text)
    digest = text.removeprefix("sha256:")
    chunks = [digest[index : index + 8] for index in range(0, len(digest), 8)]
    return r"\texttt{sha256:" + r"\allowbreak{}".join(chunks) + "}"


def validate_sha256_identity(value: object, label: str) -> None:
    require(isinstance(value, str), f"{label} must be a string")
    require(value.startswith("sha256:") and len(value) == 71, f"{label} must be sha256:<64 hex>")
    try:
        int(value.removeprefix("sha256:"), 16)
    except ValueError as exc:
        raise ValueError(f"{label} contains non-hex digest characters") from exc


def csv_rows(relative: str) -> list[dict[str, str]]:
    with (ROOT / relative).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def one_row(rows: list[dict[str, str]], **filters: object) -> dict[str, str]:
    matches = [row for row in rows if all(row.get(key) == str(value) for key, value in filters.items())]
    require(len(matches) == 1, f"expected one row for {filters}, got {len(matches)}")
    return matches[0]


def close(actual: float, expected: float, *, atol: float = 1e-12) -> bool:
    return math.isclose(actual, expected, rel_tol=0.0, abs_tol=atol)


def validate_claims(data: dict[str, object]) -> None:
    require(data.get("schema_version") == 1, "claims schema_version must be 1")
    rqs = data.get("research_questions")
    claims = data.get("claims")
    require(isinstance(rqs, list) and bool(rqs), "research_questions must be non-empty")
    require(isinstance(claims, list) and bool(claims), "claims must be non-empty")
    rq_ids = {item.get("id") for item in rqs if isinstance(item, dict)}
    claim_ids: list[object] = []
    for item in claims:
        require(isinstance(item, dict), "each claim must be an object")
        claim_ids.append(item.get("id"))
        require(item.get("rq") in rq_ids, f"claim {item.get('id')} has unknown RQ")
        require(item.get("status") in STATUS_LABELS, f"claim {item.get('id')} has invalid status")
    require(len(claim_ids) == len(set(claim_ids)), "claim ids must be unique")


def validate_qwake(data: dict[str, object]) -> None:
    require(data.get("schema_version") == 1, "QWake summary schema_version must be 1")
    selection = data.get("selection")
    best = data.get("best_safe_policy")
    protocol = data.get("protocol")
    require(isinstance(selection, dict), "selection must be an object")
    require(isinstance(best, dict), "best_safe_policy must be an object")
    require(isinstance(protocol, dict), "protocol must be an object")
    source = data.get("source")
    require(isinstance(source, dict), "QWake source must be an object")
    for key in (
        "policy_selection_file_sha256",
        "receipt_semantic_sha256",
        "receipt_file_sha256",
        "best_safe_policy_sha256",
        "common_decision_cost_sequence_sha256",
    ):
        validate_sha256_identity(source.get(key), f"QWake source.{key}")

    candidate_count = int(selection["candidate_count"])
    unsafe_count = int(selection["unsafe_count"])
    zero_danger_count = int(selection["zero_danger_count"])
    zero_coverage = int(selection["zero_danger_zero_coverage_count"])
    safe_nontrivial = int(selection["safe_nontrivial_count"])
    eligible = int(selection["eligible_policy_count"])
    require(candidate_count == 2625, "QWake candidate count must remain frozen at 2625")
    require(unsafe_count + zero_danger_count == candidate_count, "safety partition mismatch")
    require(zero_coverage + safe_nontrivial == zero_danger_count, "safe coverage partition mismatch")
    require(eligible == 0, "sealed C2 must have zero eligible policies")

    evaluated = int(best["evaluated_records"])
    accepted = int(best["accepted_records"])
    dangerous = int(best["dangerous_accepts"])
    coverage = float(best["coverage"])
    require(evaluated == 756, "best-safe evaluated_records must remain 756")
    require(accepted == 216 and dangerous == 0, "best-safe acceptance identity mismatch")
    require(math.isclose(coverage, accepted / evaluated, rel_tol=0.0, abs_tol=1e-15), "coverage mismatch")

    component_sum = sum(
        int(best[name])
        for name in (
            "cost_compute_ns",
            "cost_latency_ns",
            "cost_diagnostic_ns",
            "cost_observer_ns",
            "cost_control_ns",
            "cost_fallback_ns",
        )
    )
    total_cost = int(best["total_decision_cost_ns"])
    gross = int(best["gross_implied_avoided_suffix_ns"])
    net = int(best["total_net_saving_ns"])
    require(component_sum == total_cost, "QWake cost components do not sum to total")
    require(gross - total_cost == net, "QWake net-saving arithmetic mismatch")
    require(int(best["cost_observer_ns"]) > 0, "observer cost must be positive")
    require(protocol.get("c2_policy_freeze_established") is False, "C2 policy freeze must remain false")
    require(protocol.get("c3_open") is False, "C3 must remain closed")


def validate_core_results(data: dict[str, object]) -> None:
    require(data.get("schema_version") == 1, "core results schema_version must be 1")
    require(data.get("scientific_evidence_status") == "not_new_scientific_evidence", "core results must not claim new evidence")
    bindings = data.get("source_bindings")
    require(isinstance(bindings, dict) and bool(bindings), "core source_bindings must be non-empty")
    for relative, expected in bindings.items():
        require(isinstance(relative, str) and isinstance(expected, str), "invalid source binding")
        source = ROOT / relative
        require(source.is_file(), f"bound source missing: {relative}")
        require(sha256_file(source) == expected, f"bound source digest mismatch: {relative}")

    stage1 = data["stage1"]
    stage2 = data["stage2"]
    stage3a = data["stage3a"]
    stage3b = data["stage3b"]
    require(isinstance(stage1, dict) and isinstance(stage2, dict), "stage1/stage2 must be objects")
    require(isinstance(stage3a, dict) and isinstance(stage3b, dict), "stage3a/stage3b must be objects")

    plan = load(ROOT / "results/summaries/final_execution_plan.json")
    require(int(plan["planned_cells"]) == int(stage1["planned_cells"]) == 80, "Stage 1 planned cell count mismatch")

    primary = csv_rows("results/summaries/primary_test_summary.csv")
    compute = csv_rows("results/summaries/computational_summary.csv")
    paired = csv_rows("results/summaries/primary_paired_analysis.csv")
    fashion = stage1["fashionmnist"]
    require(isinstance(fashion, dict), "stage1 fashionmnist must be an object")
    f1 = fashion["test_macro_f1_mean"]
    times = fashion["total_training_time_sec_mean"]
    require(isinstance(f1, dict) and isinstance(times, dict), "Stage 1 metric maps invalid")
    for method in ("bp", "exact", "fixedpred", "strict"):
        row = one_row(primary, dataset="FashionMNIST", model="lenet_classic", method=method, metric="test_macro_f1")
        require(close(float(row["mean"]), float(f1[method])), f"Stage 1 F1 mismatch for {method}")
        row = one_row(compute, dataset="FashionMNIST", model="lenet_classic", method=method, metric="total_training_time_sec")
        require(close(float(row["mean"]), float(times[method])), f"Stage 1 time mismatch for {method}")
    for contrast, key in (("fixedpred_vs_bp", "fixedpred_equivalent_within_margin"), ("strict_vs_bp", "strict_equivalent_within_margin")):
        row = one_row(paired, dataset="FashionMNIST", model="lenet_classic", contrast=contrast, metric="test_macro_f1")
        require((row["equivalent_within_margin"] == "True") is bool(fashion[key]), f"Stage 1 equivalence mismatch for {contrast}")
        require(close(float(row["equivalence_margin"]), float(fashion["paired_macro_f1_equivalence_margin"])), "Stage 1 margin mismatch")

    completion = load(ROOT / "results/stage-2/summaries/stage-2-completion.json")
    require(int(completion["completed_unique_cells"]) == int(stage2["completed_unique_cells"]) == 80, "Stage 2 completion mismatch")
    require(completion["all_test_evaluated"] is stage2["all_test_evaluated"] is True, "Stage 2 test evaluation mismatch")
    did = csv_rows("results/cross-version/difference_in_differences_summary.csv")
    quality_rows = [row for row in did if row["metric"] == "quality_difference_in_differences"]
    require(len(quality_rows) == 6 and all(close(float(row["mean"]), 0.0) for row in quality_rows), "Stage 2 quality DiD mismatch")
    ratios = stage2["runtime_slowdown_ratio_stage2_to_stage1"]
    require(isinstance(ratios, dict), "Stage 2 ratio map invalid")
    for dataset, methods in ratios.items():
        require(isinstance(methods, dict), "Stage 2 method ratios invalid")
        for method, expected in methods.items():
            row = one_row(did, dataset=dataset, model="lenet_classic", method=method, metric="runtime_slowdown_ratio")
            require(close(float(row["mean"]), float(expected)), f"Stage 2 runtime ratio mismatch for {dataset}/{method}")

    exact = csv_rows("results/stage3/layerwise/confirmatory/statistics/exact_numerical_control.csv")
    require(all(row["passed"] == "True" for row in exact), "Stage 3A Exact control contains failure")
    require(close(max(float(row["max_abs_error"]) for row in exact), float(stage3a["exact_control_max_abs_error"]), atol=1e-20), "Stage 3A Exact max error mismatch")
    gradients = csv_rows("results/stage3/layerwise/confirmatory/statistics/gradient_statistics.csv")
    fixed = stage3a["fixedpred"]
    strict = stage3a["strict"]
    require(isinstance(fixed, dict) and isinstance(strict, dict), "Stage 3A method summaries invalid")
    row = one_row(gradients, method="fixedpred", layer="0", metric="cosine")
    require(close(float(row["candidate_mean"]), float(fixed["gradient_layer0_cosine_mean"])), "Stage 3A FixedPred cosine mismatch")
    row = one_row(gradients, method="fixedpred", layer="0", metric="norm_ratio")
    require(close(float(row["candidate_mean"]), float(fixed["gradient_layer0_norm_ratio_mean"])), "Stage 3A FixedPred norm mismatch")
    hidden_cos = [float(row["candidate_mean"]) for row in gradients if row["method"] == "strict" and row["metric"] == "cosine" and row["layer"] != "5"]
    require(all(close(a, b) for a, b in zip((min(hidden_cos), max(hidden_cos)), strict["gradient_hidden_cosine_mean_range"], strict=True)), "Stage 3A Strict cosine range mismatch")
    reps = csv_rows("results/stage3/layerwise/confirmatory/statistics/representation_statistics.csv")
    for method, summary in (("fixedpred", fixed), ("strict", strict)):
        for metric, key in (("cka", "representation_cka_mean_range"), ("rsa_spearman", "representation_rsa_mean_range")):
            values = [float(row["candidate_mean"]) for row in reps if row["method"] == method and row["metric"] == metric]
            actual = (min(values), max(values))
            require(all(close(a, b) for a, b in zip(actual, summary[key], strict=True)), f"Stage 3A {method}/{metric} range mismatch")

    b0 = load(ROOT / "results/stage-3/profiling/b0/analysis-v1/analysis_summary.json")
    b0s = stage3b["b0"]
    require(isinstance(b0s, dict), "B0 summary invalid")
    require(b0["status"] == "analysis_complete" and b0s["analysis_complete"] is True, "B0 status mismatch")
    paired_b0 = b0["paired_strict_relative_to_fixedpred"]
    require(close(float(paired_b0["device_time"]["configuration_median_ratio"]), float(b0s["strict_to_fixedpred_device_time_configuration_median_ratio"])), "B0 device ratio mismatch")
    require(close(float(paired_b0["peak_allocated"]["configuration_median_ratio"]), float(b0s["strict_to_fixedpred_peak_allocated_configuration_median_ratio"])), "B0 memory ratio mismatch")
    require(close(float(b0["bottlenecks"]["fixedpred"]["state_inference_share_median"]), float(b0s["fixedpred_state_inference_device_share_median"])), "B0 FixedPred state share mismatch")
    require(close(float(b0["bottlenecks"]["strict"]["state_inference_share_median"]), float(b0s["strict_state_inference_device_share_median"])), "B0 Strict state share mismatch")

    ma0 = load(ROOT / "results/stage-3/si-ma0/confirmatory/si_ma0_summary.json")
    ma0s = stage3b["si_ma0"]
    require(isinstance(ma0s, dict), "SI-MA0 summary invalid")
    require(ma0["si_ma0_passed"] is ma0s["passed"] is False, "SI-MA0 decision mismatch")
    require(ma0["gates"]["COST-MA0"] is ma0s["cost_gate_passed"] is False, "SI-MA0 COST gate mismatch")
    residual = ma0["accounting_residual_statistics"]
    require(int(residual["counts"]["measured_steps"]) == int(ma0s["measured_steps"]), "SI-MA0 measured steps mismatch")
    require(close(float(residual["accounting_residual"]["median"]), float(ma0s["accounting_residual_median"])), "SI-MA0 residual mismatch")

    ma1 = load(ROOT / "results/stage-3/si-ma1/confirmatory/si_ma1_summary.json")
    ma1s = stage3b["si_ma1"]
    require(isinstance(ma1s, dict), "SI-MA1 summary invalid")
    require(ma1["si_ma1_passed"] is ma1s["passed"] is True, "SI-MA1 decision mismatch")
    require(int(ma1["matched_block_count"]) == int(ma1s["matched_block_count"]) == 180, "SI-MA1 block count mismatch")
    require(int(ma1["model_seed_count"]) == int(ma1s["model_seed_count"]) == 10, "SI-MA1 seed count mismatch")
    estimand = ma1["primary_estimand"]
    ma1_expected_keys = {
        "observed": "primary_estimand_observed",
        "upper_one_sided_95": "upper_one_sided_95",
        "threshold": "threshold",
    }
    for source_key, summary_key in ma1_expected_keys.items():
        require(
            close(float(estimand[source_key]), float(ma1s[summary_key])),
            f"SI-MA1 {source_key} mismatch",
        )

    b1 = load(ROOT / "results/stage-3/b1/stage3b-b1-confirmatory-ceebdce-v1/decision.json")
    b1s = stage3b["b1"]
    require(b1["status"] == b1s["status"] == "pass", "B1 status mismatch")
    require(int(b1["observed_pair_count"]) == int(b1s["observed_pair_count"]) == 120, "B1 pair count mismatch")
    require(int(b1["failed_pair_count"]) == int(b1s["failed_pair_count"]) == 0, "B1 failures mismatch")

    b2 = load(ROOT / "results/stage-3/b2/stage3b-b2-confirmatory-63885e5-v1/decision.json")
    b2s = stage3b["b2"]
    require(b2["status"] == b2s["status"] == "pass", "B2 status mismatch")
    require(int(b2["matched_triples_observed"]) == int(b2s["matched_triples_observed"]) == 120, "B2 triple count mismatch")
    require(int(b2["failed_pair_count"]) == int(b2s["failed_pair_count"]) == 0, "B2 failures mismatch")

    seal = load(ROOT / "results/stage-3/profiling/matched/stage3b-matched-profiling-e1dcfb2-v1/seal.json")
    matched = stage3b["matched_profiling"]
    require(seal["status"] == "sealed" and matched["sealed"] is True, "matched profiling seal mismatch")
    require(int(seal["matched_cell_count"]) == int(matched["matched_cell_count"]) == 288, "matched profiling cell count mismatch")
    require(int(seal["cross_candidate_correctness_block_count"]) == int(matched["cross_candidate_correctness_block_count"]) == 96, "matched profiling block count mismatch")
    require(int(seal["retried_cell_count"]) == int(matched["retried_cell_count"]) == 0, "matched profiling retry count mismatch")


def render_claims(data: dict[str, object]) -> str:
    claims = data["claims"]
    assert isinstance(claims, list)
    lines = [
        "% Generated by scripts/build_thesis_assets.py; do not edit manually.",
        r"\begingroup\small",
        r"\begin{longtable}{@{}L{0.05\textwidth}L{0.05\textwidth}L{0.39\textwidth}L{0.13\textwidth}L{0.21\textwidth}@{}}",
        r"\toprule",
        r"ID & RQ & Проверяемое утверждение & Статус & Граница вывода \\",
        r"\midrule",
        r"\endfirsthead",
        r"\toprule",
        r"ID & RQ & Проверяемое утверждение & Статус & Граница вывода \\",
        r"\midrule",
        r"\endhead",
    ]
    for item in claims:
        assert isinstance(item, dict)
        lines.append(
            "{} & {} & {} & {} & {} \\\\".format(
                latex_escape(item["id"]),
                latex_escape(item["rq"]),
                latex_breakable(item["claim"]),
                latex_escape(STATUS_LABELS[str(item["status"])]),
                latex_breakable(item["scope"]),
            )
        )
    lines.extend([r"\bottomrule", r"\end{longtable}", r"\endgroup", ""])
    return "\n".join(lines)


def texrow(text: str) -> str:
    return text + r" \\"


def render_program(core: dict[str, object], qwake: dict[str, object]) -> str:
    s1 = core["stage1"]
    s2 = core["stage2"]
    s3a = core["stage3a"]
    s3b = core["stage3b"]
    selection = qwake["selection"]
    lines = [
        "% Generated by scripts/build_thesis_assets.py; do not edit manually.",
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{Сводная структура завершённой экспериментальной программы}",
        r"\label{tab:experimental-program}",
        r"\begin{tabular}{@{}L{0.13\textwidth}L{0.22\textwidth}L{0.18\textwidth}L{0.32\textwidth}@{}}",
        r"\toprule",
        texrow("Этап & Основная единица/объём & Роль & Завершённая граница"),
        r"\midrule",
        texrow(f"Stage 1 & {int(s1['planned_cells'])} final cells; 10 model seeds & качество и стоимость & исходная сравнительная кампания"),
        texrow(f"Stage 2 & {int(s2['completed_unique_cells'])} final cells & controlled implementation change & все final cells завершены; test evaluated"),
        texrow(f"Stage 3A & {int(s3a['independent_model_seeds'])} model seeds & mechanism diagnostics & gradients, CKA/RSA и численный Exact-control"),
        texrow(f"Stage 3B & {int(s3b['matched_profiling']['matched_cell_count'])} matched cells & cost/mechanism attribution & B0, SI-MA0/1, B1/B2 и sealed profiling"),
        texrow(f"QWake C2 & {int(selection['candidate_count'])} frozen policies; 756 records & безопасность и экономика & bounded negative result; C3 closed"),
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
        "",
    ]
    return "\n".join(lines)


def render_stage12(core: dict[str, object]) -> str:
    s1 = core["stage1"]["fashionmnist"]
    s2 = core["stage2"]
    f1 = s1["test_macro_f1_mean"]
    times = s1["total_training_time_sec_mean"]
    ratios = s2["runtime_slowdown_ratio_stage2_to_stage1"]
    lines = [
        "% Generated by scripts/build_thesis_assets.py; do not edit manually.",
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{Stage 1: FashionMNIST, средние значения по 10 model seeds}",
        r"\label{tab:stage1-summary}",
        r"\begin{tabular}{lrr}",
        r"\toprule",
        texrow("Метод & Test macro-F1 & Training time, s"),
        r"\midrule",
    ]
    for method, label in (("bp", "BP"), ("exact", "Exact"), ("fixedpred", "FixedPred"), ("strict", "Strict")):
        lines.append(texrow(f"{label} & {float(f1[method]):.6f} & {float(times[method]):.3f}"))
    lines.extend(
        [
            r"\bottomrule",
            r"\end{tabular}",
            r"\end{table}",
            "",
            r"\begin{table}[htbp]",
            r"\centering",
            r"\caption{Stage 2: cross-version отношение runtime-over-BP к Stage 1}",
            r"\label{tab:stage2-runtime-ratio}",
            r"\begin{tabular}{lrr}",
            r"\toprule",
            texrow("Метод & FashionMNIST & MNIST"),
            r"\midrule",
        ]
    )
    for method, label in (("exact", "Exact"), ("fixedpred", "FixedPred"), ("strict", "Strict")):
        lines.append(texrow(f"{label} & {float(ratios['FashionMNIST'][method]):.3f} & {float(ratios['MNIST'][method]):.3f}"))
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}", ""])
    return "\n".join(lines)


def render_stage3(core: dict[str, object]) -> str:
    s3a = core["stage3a"]
    s3b = core["stage3b"]
    b0 = s3b["b0"]
    ma0 = s3b["si_ma0"]
    ma1 = s3b["si_ma1"]
    lines = [
        "% Generated by scripts/build_thesis_assets.py; do not edit manually.",
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{Ключевые зарегистрированные результаты Stage 3}",
        r"\label{tab:stage3-summary}",
        r"\begin{tabular}{@{}L{0.14\textwidth}L{0.73\textwidth}@{}}",
        r"\toprule",
        texrow("Подэтап & Зарегистрированный результат"),
        r"\midrule",
        texrow(f"Stage 3A & Exact max abs error = {float(s3a['exact_control_max_abs_error']):.3e}; FixedPred layer-0 cosine = {float(s3a['fixedpred']['gradient_layer0_cosine_mean']):.6f}, norm ratio = {float(s3a['fixedpred']['gradient_layer0_norm_ratio_mean']):.6f}."),
        texrow(f"B0 & median Strict/FixedPred device-time ratio = {float(b0['strict_to_fixedpred_device_time_configuration_median_ratio']):.3f}; peak-allocated ratio = {float(b0['strict_to_fixedpred_peak_allocated_configuration_median_ratio']):.3f}."),
        texrow(f"SI-MA0 & COST-MA0 = FAIL; {int(ma0['passing_measured_steps'])}/{int(ma0['measured_steps'])} measured steps passed; median signed accounting residual = {float(ma0['accounting_residual_median']):.3f}."),
        texrow(f"SI-MA1 & CAL-COST-MA1 = PASS; 10 model seeds, {int(ma1['matched_block_count'])} matched blocks; upper one-sided 95\\% = {float(ma1['upper_one_sided_95']):.3f} at threshold {float(ma1['threshold']):.2f}."),
        texrow(f"B1/B2 & EQ-B1 and EQ-B2 = PASS; B1: {int(s3b['b1']['observed_pair_count'])} pairs, B2: {int(s3b['b2']['matched_triples_observed'])} matched triples; zero failed pairs."),
        texrow(f"Matched profiling & {int(s3b['matched_profiling']['matched_cell_count'])}/{int(s3b['matched_profiling']['matched_cell_count'])} cells sealed, {int(s3b['matched_profiling']['cross_candidate_correctness_block_count'])} correctness blocks, retries = {int(s3b['matched_profiling']['retried_cell_count'])}."),
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
        "",
    ]
    return "\n".join(lines)


def render_qwake(qwake: dict[str, object]) -> str:
    s = qwake["selection"]
    b = qwake["best_safe_policy"]
    observer_share = int(b["cost_observer_ns"]) / int(b["total_decision_cost_ns"]) * 100.0
    lines = [
        "% Generated by scripts/build_thesis_assets.py; do not edit manually.",
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{QWake C2: последовательность зарегистрированных gates}",
        r"\label{tab:qwake-funnel}",
        r"\begin{tabular}{lr}",
        r"\toprule",
        texrow("Категория & Число policies"),
        r"\midrule",
        texrow(f"Всего frozen candidates & {int(s['candidate_count'])}"),
        texrow(f"Unsafe & {int(s['unsafe_count'])}"),
        texrow(f"Zero-danger & {int(s['zero_danger_count'])}"),
        texrow(f"Safe + nontrivial coverage & {int(s['safe_nontrivial_count'])}"),
        texrow(f"Safe + beneficial & {int(s['eligible_policy_count'])}"),
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
        "",
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{QWake C2: decomposition лучшей безопасной policy при frozen accounting}",
        r"\label{tab:qwake-cost}",
        r"\begin{tabular}{lr}",
        r"\toprule",
        texrow("Показатель & Значение"),
        r"\midrule",
        texrow(f"Accepted / evaluated & {int(b['accepted_records'])} / {int(b['evaluated_records'])}"),
        texrow(f"Dangerous accepts & {int(b['dangerous_accepts'])}"),
        texrow(f"Coverage & {float(b['coverage']) * 100.0:.2f}\\%"),
        texrow(f"Gross safely avoidable suffix & {int(b['gross_implied_avoided_suffix_ns']) / 1e9:.3f} s"),
        texrow(f"Full decision cost & {int(b['total_decision_cost_ns']) / 1e9:.3f} s"),
        texrow(f"Observer share of full cost & {observer_share:.3f}\\%"),
        texrow(f"Aggregate net saving & {int(b['total_net_saving_ns']) / 1e9:.3f} s"),
        texrow(f"Break-even cost reduction & {float(b['required_cost_reduction_for_zero_net_fraction']) * 100.0:.3f}\\%"),
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
        "",
    ]
    return "\n".join(lines)


def render_reproducibility(core: dict[str, object], qwake: dict[str, object]) -> str:
    bindings = core["source_bindings"]
    source = qwake["source"]
    assert isinstance(bindings, dict)
    assert isinstance(source, dict)

    lines = [
        "% Generated by scripts/build_thesis_assets.py; do not edit manually.",
        r"\begingroup",
        r"\footnotesize",
        r"\begin{longtable}{@{}L{0.50\textwidth}L{0.38\textwidth}@{}}",
        r"\toprule",
        r"Источник / identity & SHA-256 \\",
        r"\midrule",
        r"\endfirsthead",
        r"\toprule",
        r"Источник / identity & SHA-256 \\",
        r"\midrule",
        r"\endhead",
    ]
    for relative, digest in bindings.items():
        lines.append(f"{latex_code(relative)} & {latex_digest(digest)} \\\\")

    qlabels = (
        ("QWake C2 policy-selection file", "policy_selection_file_sha256"),
        ("QWake C2 receipt semantic", "receipt_semantic_sha256"),
        ("QWake C2 receipt file", "receipt_file_sha256"),
        ("QWake best-safe policy", "best_safe_policy_sha256"),
        ("QWake common decision-cost sequence", "common_decision_cost_sequence_sha256"),
    )
    for label, key in qlabels:
        lines.append(f"{latex_escape(label)} & {latex_digest(source[key])} \\\\")

    lines.extend([r"\bottomrule", r"\end{longtable}", r"\endgroup", ""])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="validate inputs without writing generated files")
    args = parser.parse_args()

    claims = load(CLAIMS_PATH)
    qwake = load(QWAKE_PATH)
    core = load(CORE_RESULTS_PATH)
    validate_claims(claims)
    validate_qwake(qwake)
    validate_core_results(core)

    print("THESIS_CLAIMS_SCHEMA=PASS")
    print("THESIS_QWAKE_SUMMARY_ARITHMETIC=PASS")
    print("THESIS_QWAKE_PROTOCOL_BOUNDARY=PASS")
    print("THESIS_CORE_RESULTS_SOURCE_BINDINGS=PASS")
    print("THESIS_CORE_RESULTS_RECONCILIATION=PASS")
    print("THESIS_PROVENANCE_IDENTITIES=PASS")

    if args.check:
        print("THESIS_ASSET_WRITE=false")
        return

    GENERATED.mkdir(parents=True, exist_ok=True)
    assets = {
        CLAIMS_TEX: render_claims(claims),
        PROGRAM_TEX: render_program(core, qwake),
        STAGE12_TEX: render_stage12(core),
        STAGE3_TEX: render_stage3(core),
        QWAKE_TEX: render_qwake(qwake),
        REPRO_TEX: render_reproducibility(core, qwake),
    }
    for path, rendered in assets.items():
        path.write_text(rendered, encoding="utf-8", newline="\n")
        print(f"THESIS_ASSET_RENDERED={path.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
