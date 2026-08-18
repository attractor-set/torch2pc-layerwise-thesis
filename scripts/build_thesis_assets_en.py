#!/usr/bin/env python3
"""Validate and render the English dissertation assets from frozen thesis data."""

from __future__ import annotations

import argparse
import re

import build_thesis_assets as base

ROOT = base.ROOT
THESIS = base.THESIS
GENERATED = base.GENERATED
GLOSSARY_EN_PATH = base.GLOSSARY_EN_PATH
EXPECTED_GLOSSARY_TERM_COUNT = base.EXPECTED_GLOSSARY_TERM_COUNT

CLAIMS_TEX = GENERATED / "claims_matrix_EN.tex"
PROGRAM_TEX = GENERATED / "experimental_program_EN.tex"
STAGE12_TEX = GENERATED / "stage12_results_EN.tex"
STAGE3_TEX = GENERATED / "stage3_results_EN.tex"
QWAKE_TEX = GENERATED / "qwake_results_EN.tex"
REPRO_TEX = GENERATED / "reproducibility_manifest_EN.tex"
TERMINOLOGY_TEX = GENERATED / "terminology_registry_EN.tex"

STATUS_LABELS = {
    "supported": "supported",
    "rejected": "rejected",
    "not_tested": "not_tested",
    "descriptive": "descriptive",
}

# English claim text is a rendering of the canonical C01-C11 registry. The
# IDs/statuses remain data-driven and the translation is deliberately explicit
# so that a wording change cannot silently change an epistemic boundary.
CLAIM_TEXT = {
    "C01": (
        "In Stage 1 on FashionMNIST, FixedPred and Strict lie inside the preregistered paired macro-F1 equivalence margin of ±0.01 relative to BP; Stage 2 preserves the registered final-quality surface while runtime changes measurably relative to Stage 1.",
        "Stage 1: FashionMNIST paired macro-F1 comparison; Stage 2: cross-version comparison on FashionMNIST and MNIST.",
    ),
    "C02": (
        "Within the registered Stage 3A domain, FixedPred shows higher observed proximity to BP than Strict in gradient direction and representations, while substantially reducing early-layer gradient norm.",
        "Stage 3A; FashionMNIST; lenet_classic architecture; ten independently trained models.",
    ),
    "C03": (
        "In Stage 3B B0, Strict is more expensive than FixedPred in device time and peak memory, and state_inference is the dominant timing region.",
        "Stage 3B B0; ROCm/float32; 96 canonical cells; independent unit = model seed; three values per configuration; descriptive engineering localization.",
    ),
    "C04": (
        "The initial SI-MA0 mechanism-cost attribution model fails the registered COST-MA0 gate.",
        "SI-MA0; ten independently trained models.",
    ),
    "C05": (
        "The separate SI-MA1 observer-cost calibration passes CAL-COST-MA1; the signed residual indicates over-closure of the accounting model rather than negative physical cost.",
        "SI-MA1; ten independently trained models; 180 matched blocks.",
    ),
    "C06": (
        "The exact B1 isolated_layer_vjp and B2 composite_vjp candidates pass their frozen EQ-B1 and EQ-B2 equivalence checks.",
        "Stage 3B B1/B2; exact implementation candidates.",
    ),
    "C07": (
        "Matched B0/B1/B2 profiling is complete without failed or retried runs in the registered 288-cell matrix; on the registered engineering-continuation screen, none of the 16 configurations in each of the four B1/B2 × FixedPred/Strict groups qualifies, and both candidates receive reject_or_revise.",
        "288/288 cells; 96/96 matched blocks; four candidate × method groups of 16 configurations; 0/16 qualified configurations in every group; the decision concerns only engineering continuation in the immutable ROCm/float32 environment; no superiority claim is authorized.",
    ),
    "C08": (
        "On the integrity-sealed QWake C1/C2 surface, preterminal records exist whose states the reference check labels EARLY_ADMISSIBLE, and the frozen C2 rule family contains non-zero selective recognizability of a subset from pre-action state with zero observed dangerous accepts on 756 calibration records.",
        "QWake C1/C2; selective PC-TREF case for the early action, not full sufficiency of the complete diagnostic representation; 2,625 frozen scalar rules; 756 integrity-sealed calibration records with a post-action sufficiency oracle; full temporal-surface reconciliation: 108 trajectories, with the highest-coverage zero-danger rule accepting 108 preterminal step-5 records with one sweep remaining and 108 terminal-boundary step-6 records; 216/756 coverage refers to the full surface, not preterminal coverage; zero observed dangerous accepts does not establish population-risk control.",
    ),
    "C09": (
        "Within the frozen C2 rule family, a rule exists that simultaneously has zero observed dangerous accepts, non-zero coverage, and positive aggregate net saving under frozen full decision-cost accounting.",
        "QWake C2; the same full 756-record surface including the terminal boundary; the same frozen rule family, interpreter, evidence, and cost accounting; the C08 structural decomposition does not remove terminal records or authorize retrospective recomputation of the economic estimand.",
    ),
    "C10": (
        "A minimal recognizer implementing the identified simple rule is economically non-viable by marginal execution cost.",
        "The separate marginal-execution-cost estimand was not part of the integrity-sealed C2 evaluation.",
    ),
    "C11": (
        "Confirmatory C3 was opened and independently confirmed the selected C2 rule.",
        "No eligible C2 rule was selected and frozen for confirmatory C3; the protocol receipt chain did not open C3.",
    ),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def parse_english_glossary() -> list[dict[str, str]]:
    text = GLOSSARY_EN_PATH.read_text(encoding="utf-8")
    entry_re = re.compile(r"^### (TERM-[A-Z0-9-]+) — (.+)$")
    entries: list[dict[str, str]] = []
    section = ""
    current: dict[str, str] | None = None
    for raw_line in text.splitlines():
        if raw_line.startswith("## "):
            section = raw_line.removeprefix("## ").strip()
            continue
        match = entry_re.match(raw_line)
        if match:
            if current is not None:
                entries.append(current)
            current = {
                "term_id": match.group(1),
                "term": match.group(2).strip(),
                "section": section,
                "meaning": "",
                "rule": "",
                "name_semantics": "",
                "architectural_role": "",
            }
            continue
        if current is None:
            continue
        for prefix, key in (
            ("- **Project meaning:** ", "meaning"),
            ("- **Usage rule:** ", "rule"),
            ("- **Name semantics:** ", "name_semantics"),
            ("- **Architectural role:** ", "architectural_role"),
        ):
            if raw_line.startswith(prefix):
                current[key] = raw_line.removeprefix(prefix).strip()
                break
    if current is not None:
        entries.append(current)

    require(
        len(entries) == EXPECTED_GLOSSARY_TERM_COUNT,
        f"expected {EXPECTED_GLOSSARY_TERM_COUNT} English glossary terms, got {len(entries)}",
    )
    ids = [item["term_id"] for item in entries]
    require(len(ids) == len(set(ids)), "English glossary TERM-* identifiers must be unique")
    for item in entries:
        require(bool(item["section"]), f"{item['term_id']} has no English section")
        require(bool(item["meaning"]), f"{item['term_id']} has no English meaning")
        require(bool(item["rule"]), f"{item['term_id']} has no English usage rule")
    return entries


def render_claims(data: dict[str, object]) -> str:
    claims = data["claims"]
    assert isinstance(claims, list)
    ids = [str(item["id"]) for item in claims if isinstance(item, dict)]
    require(ids == list(CLAIM_TEXT), "English C01-C11 translation registry/order mismatch")
    lines = [
        "% Generated by scripts/build_thesis_assets_en.py; do not edit manually.",
        r"\begingroup\small",
        r"\begin{longtable}{@{}L{0.05\textwidth}L{0.05\textwidth}L{0.39\textwidth}L{0.13\textwidth}L{0.21\textwidth}@{}}",
        r"\toprule",
        "ID & RQ & Testable claim & Status & Inference boundary" + base.LATEX_ROW_END,
        r"\midrule",
        r"\endfirsthead",
        r"\toprule",
        "ID & RQ & Testable claim & Status & Inference boundary" + base.LATEX_ROW_END,
        r"\midrule",
        r"\endhead",
    ]
    for item in claims:
        assert isinstance(item, dict)
        claim, scope = CLAIM_TEXT[str(item["id"])]
        lines.append(
            "{} & {} & {} & {} & {}{}".format(
                base.latex_escape(item["id"]),
                base.latex_escape(item["rq"]),
                base.latex_prose(claim),
                base.latex_escape(STATUS_LABELS[str(item["status"])]),
                base.latex_prose(scope),
                base.LATEX_ROW_END,
            )
        )
    lines.extend([r"\bottomrule", r"\end{longtable}", r"\endgroup", ""])
    return "\n".join(lines)


def render_program(core: dict[str, object], qwake: dict[str, object]) -> str:
    s1 = core["stage1"]
    s2 = core["stage2"]
    s3a = core["stage3a"]
    s3b = core["stage3b"]
    selection = qwake["selection"]
    lines = [
        "% Generated by scripts/build_thesis_assets_en.py; do not edit manually.",
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{Summary structure of the completed experimental program}",
        r"\label{tab:experimental-program-en}",
        r"\begin{tabular}{@{}L{0.13\textwidth}L{0.22\textwidth}L{0.18\textwidth}L{0.32\textwidth}@{}}",
        r"\toprule",
        base.texrow("Stage & Main unit/volume & Role & Completed boundary"),
        r"\midrule",
        base.texrow(
            f"Stage 1 & {int(s1['planned_cells'])} final cells; 10 independently trained models & quality and cost & initial comparative campaign"
        ),
        base.texrow(
            f"Stage 2 & {int(s2['completed_unique_cells'])} final cells & controlled implementation change & all final cells complete; test evaluation performed"
        ),
        base.texrow(
            f"Stage 3A & {int(s3a['independent_model_seeds'])} independently trained models & mechanism diagnostics & gradients, CKA/RSA, and Exact numerical control"
        ),
        base.texrow(
            f"Stage 3B & {int(s3b['matched_profiling']['matched_cell_count'])} matched cells & cost and mechanism attribution & B0, SI-MA0/1, B1/B2, and integrity-sealed profiling"
        ),
        base.texrow(
            f"QWake C2 & {int(selection['candidate_count'])} frozen rules; 756 records & dangerous-accept barrier and economics & bounded negative economic result; C3 closed"
        ),
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
        "% Generated by scripts/build_thesis_assets_en.py; do not edit manually.",
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{Stage 1: FashionMNIST means over 10 independently trained models}",
        r"\label{tab:stage1-summary-en}",
        r"\begin{tabular}{lrr}",
        r"\toprule",
        base.texrow("Method & Test macro-F1 & Training time, s"),
        r"\midrule",
    ]
    for method, label in (
        ("bp", "BP"),
        ("exact", "Exact"),
        ("fixedpred", "FixedPred"),
        ("strict", "Strict"),
    ):
        lines.append(base.texrow(f"{label} & {float(f1[method]):.6f} & {float(times[method]):.3f}"))
    lines.extend(
        [
            r"\bottomrule",
            r"\end{tabular}",
            r"\end{table}",
            "",
            r"\begin{table}[htbp]",
            r"\centering",
            r"\caption{Stage 2: cross-version runtime slowdown relative to BP versus Stage 1}",
            r"\label{tab:stage2-runtime-ratio-en}",
            r"\begin{tabular}{lrr}",
            r"\toprule",
            base.texrow("Method & FashionMNIST & MNIST"),
            r"\midrule",
        ]
    )
    for method, label in (("exact", "Exact"), ("fixedpred", "FixedPred"), ("strict", "Strict")):
        lines.append(
            base.texrow(
                f"{label} & {float(ratios['FashionMNIST'][method]):.3f} & {float(ratios['MNIST'][method]):.3f}"
            )
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}", ""])
    return "\n".join(lines)


def render_stage3(core: dict[str, object]) -> str:
    s3a = core["stage3a"]
    s3b = core["stage3b"]
    b0 = s3b["b0"]
    ma0 = s3b["si_ma0"]
    ma1 = s3b["si_ma1"]
    lines = [
        "% Generated by scripts/build_thesis_assets_en.py; do not edit manually.",
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{Key registered Stage 3 results}",
        r"\label{tab:stage3-summary-en}",
        r"\begin{tabular}{@{}L{0.18\textwidth}L{0.69\textwidth}@{}}",
        r"\toprule",
        base.texrow("Substage & Registered result"),
        r"\midrule",
        base.texrow(
            f"Stage 3A & Exact maximum absolute error = {float(s3a['exact_control_max_abs_error']):.3e}; FixedPred layer-0 gradient cosine similarity = {float(s3a['fixedpred']['gradient_layer0_cosine_mean']):.6f}, norm ratio = {float(s3a['fixedpred']['gradient_layer0_norm_ratio_mean']):.6f}."
        ),
        base.texrow(
            f"B0 & Strict/FixedPred median device-time ratio = {float(b0['strict_to_fixedpred_device_time_configuration_median_ratio']):.3f}; peak allocated-memory ratio = {float(b0['strict_to_fixedpred_peak_allocated_configuration_median_ratio']):.3f}."
        ),
        base.texrow(
            f"SI-MA0 & COST-MA0 failed; {int(ma0['passing_measured_steps'])}/{int(ma0['measured_steps'])} measured steps passed; median signed accounting residual = {float(ma0['accounting_residual_median']):.3f}."
        ),
        base.texrow(
            f"SI-MA1 & CAL-COST-MA1 passed; 10 independently trained models, {int(ma1['matched_block_count'])} matched blocks; upper one-sided 95\\% bound = {float(ma1['upper_one_sided_95']):.3f} at threshold {float(ma1['threshold']):.2f}."
        ),
        base.texrow(
            f"B1/B2 & EQ-B1 and EQ-B2 passed; B1: {int(s3b['b1']['observed_pair_count'])} pairs, B2: {int(s3b['b2']['matched_triples_observed'])} matched triples; no failed pairs."
        ),
        base.texrow(
            f"Matched profiling & integrity sealed for {int(s3b['matched_profiling']['matched_cell_count'])}/{int(s3b['matched_profiling']['matched_cell_count'])} cells; {int(s3b['matched_profiling']['cross_candidate_correctness_block_count'])} correctness blocks; retries = {int(s3b['matched_profiling']['retried_cell_count'])}."
        ),
        base.texrow(
            f"B1/B2 engineering screen & four candidate × method groups of {int(s3b['matched_analysis']['configuration_count_per_group'])} configurations; {int(s3b['matched_analysis']['qualified_configuration_count_per_group'])}/{int(s3b['matched_analysis']['configuration_count_per_group'])} qualify in every group; both candidates receive reject\\_or\\_revise; superiority claim not authorized."
        ),
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
        "",
    ]
    return "\n".join(lines)


def render_qwake(qwake: dict[str, object]) -> str:
    selection = qwake["selection"]
    best = qwake["best_safe_policy"]
    decomposition = qwake["temporal_surface_decomposition"]
    observer_share = int(best["cost_observer_ns"]) / int(best["total_decision_cost_ns"]) * 100.0
    lines = [
        "% Generated by scripts/build_thesis_assets_en.py; do not edit manually.",
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{QWake C2: sequence of registered filters}",
        r"\label{tab:qwake-funnel-en}",
        r"\begin{tabular}{lr}",
        r"\toprule",
        base.texrow("Category & Rule count"),
        r"\midrule",
        base.texrow(f"Total frozen rules & {int(selection['candidate_count'])}"),
        base.texrow(f"With at least one dangerous accept & {int(selection['unsafe_count'])}"),
        base.texrow(
            f"With zero observed dangerous accepts & {int(selection['zero_danger_count'])}"
        ),
        base.texrow(
            f"Zero dangerous accepts and non-zero coverage & {int(selection['safe_nontrivial_count'])}"
        ),
        base.texrow(
            f"Eligible under the full C2 criterion & {int(selection['eligible_policy_count'])}"
        ),
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
        "",
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{QWake C2: temporal decomposition and cost of the highest-coverage zero-danger rule}",
        r"\label{tab:qwake-cost-en}",
        r"\begin{tabular}{@{}p{0.76\textwidth}r@{}}",
        r"\toprule",
        base.texrow("Metric & Value"),
        r"\midrule",
        base.texrow(
            f"Accepted / evaluated on the full C1 surface & {int(best['accepted_records'])} / {int(best['evaluated_records'])}"
        ),
        base.texrow(f"Dangerous accepts & {int(best['dangerous_accepts'])}"),
        base.texrow(f"Registered full-surface coverage & {float(best['coverage']) * 100.0:.2f}\\%"),
        base.texrow(
            f"Preterminal records on the C1 surface & {int(decomposition['preterminal_surface_records'])}"
        ),
        base.texrow(
            f"Accepted preterminal records (step 5, one sweep remaining) & {int(decomposition['best_safe_policy_accepted_preterminal_records'])}"
        ),
        base.texrow(
            f"Terminal-boundary records on the C1 surface & {int(decomposition['terminal_boundary_records'])}"
        ),
        base.texrow(
            f"Accepted terminal-boundary records (step 6) & {int(decomposition['best_safe_policy_accepted_terminal_records'])}"
        ),
        base.texrow(
            f"Registered sum of {base.latex_code('remaining_suffix_ns')} over accepted zero-danger records & {int(best['gross_implied_avoided_suffix_ns']) / 1e9:.3f} s"
        ),
        base.texrow(f"Full decision cost & {int(best['total_decision_cost_ns']) / 1e9:.3f} s"),
        base.texrow(f"Observer share of full decision cost & {observer_share:.3f}\\%"),
        base.texrow(f"Aggregate net saving & {int(best['total_net_saving_ns']) / 1e9:.3f} s"),
        base.texrow(
            f"Cost reduction required for break-even & {float(best['required_cost_reduction_for_zero_net_fraction']) * 100.0:.3f}\\%"
        ),
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
        "% Generated by scripts/build_thesis_assets_en.py; do not edit manually.",
        r"\begingroup",
        r"\footnotesize",
        r"\begin{longtable}{@{}L{0.50\textwidth}L{0.38\textwidth}@{}}",
        r"\toprule",
        "Source / identifier & SHA-256" + base.LATEX_ROW_END,
        r"\midrule",
        r"\endfirsthead",
        r"\toprule",
        "Source / identifier & SHA-256" + base.LATEX_ROW_END,
        r"\midrule",
        r"\endhead",
        r"\multicolumn{2}{@{}l}{\textbf{Locally re-verifiable bindings}} " + base.LATEX_ROW_END,
    ]
    for relative, digest in bindings.items():
        lines.append(
            f"{base.latex_code(relative)} & {base.latex_digest(digest)}{base.LATEX_ROW_END}"
        )
    for label, key in (
        ("Frozen QWake C1 request", "c1_request_file_sha256"),
        ("QWake-FP special-case contract", "qwake_contract_file_sha256"),
    ):
        lines.append(
            f"{base.latex_escape(label)} & {base.latex_digest(source[key])}{base.LATEX_ROW_END}"
        )
    lines.extend(
        [
            r"\addlinespace",
            r"\multicolumn{2}{@{}l}{\textbf{Preserved identifiers of sealed material}} "
            + base.LATEX_ROW_END,
        ]
    )
    for label, key in (
        ("QWake C2 rule-selection file", "policy_selection_file_sha256"),
        ("QWake C2 receipt semantics", "receipt_semantic_sha256"),
        ("QWake C2 receipt file", "receipt_file_sha256"),
        ("Highest-coverage QWake zero-danger rule", "best_safe_policy_sha256"),
        ("QWake common decision-cost sequence", "common_decision_cost_sequence_sha256"),
    ):
        lines.append(
            f"{base.latex_escape(label)} & {base.latex_digest(source[key])}{base.LATEX_ROW_END}"
        )
    lines.extend([r"\bottomrule", r"\end{longtable}", r"\endgroup", ""])
    return "\n".join(lines)


def render_terminology(entries: list[dict[str, str]]) -> str:
    lines = [
        "% Generated by scripts/build_thesis_assets_en.py; do not edit manually.",
        r"\begingroup",
        r"\small",
    ]
    current_section = ""
    for item in entries:
        section = item["section"]
        if section != current_section:
            if current_section:
                lines.extend([r"\bottomrule", r"\end{longtable}", ""])
            current_section = section
            lines.extend(
                [
                    rf"\section{{{base.latex_escape(section)}}}",
                    r"\begin{longtable}{@{}L{0.31\textwidth}L{0.59\textwidth}@{}}",
                    r"\toprule",
                    "Term & Canonical meaning and usage boundary" + base.LATEX_ROW_END,
                    r"\midrule",
                    r"\endfirsthead",
                    r"\toprule",
                    "Term & Canonical meaning and usage boundary" + base.LATEX_ROW_END,
                    r"\midrule",
                    r"\endhead",
                ]
            )
        left = (
            rf"\textbf{{{base.latex_glossary_inline(item['term'])}}}"
            + r"\newline "
            + base.latex_code(item["term_id"])
        )
        right_parts = [base.latex_glossary_inline(item["meaning"])]
        if item["name_semantics"]:
            right_parts.append(
                r"\par\smallskip\emph{Name semantics: }"
                + base.latex_glossary_inline(item["name_semantics"])
            )
        if item["architectural_role"]:
            right_parts.append(
                r"\par\smallskip\emph{Architectural role: }"
                + base.latex_glossary_inline(item["architectural_role"])
            )
        right_parts.append(
            r"\par\smallskip\emph{Usage rule: }" + base.latex_glossary_inline(item["rule"])
        )
        lines.append(left + " & " + "".join(right_parts) + base.LATEX_ROW_END)
    if current_section:
        lines.extend([r"\bottomrule", r"\end{longtable}"])
    lines.extend([r"\endgroup", ""])
    rendered = "\n".join(lines)
    rendered_ids = re.findall(r"TERM-[A-Z0-9-]+", rendered)
    require(
        len(set(rendered_ids)) == EXPECTED_GLOSSARY_TERM_COUNT,
        "rendered English terminology registry does not contain every TERM-* identifier",
    )
    return rendered


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check", action="store_true", help="validate inputs without writing generated files"
    )
    args = parser.parse_args()

    claims = base.load(base.CLAIMS_PATH)
    qwake = base.load(base.QWAKE_PATH)
    core = base.load(base.CORE_RESULTS_PATH)

    base.validate_claims(claims)
    base.validate_qwake(qwake)
    base.validate_qwake_claim_reconciliation(claims, qwake)
    base.validate_core_results(core)
    # Keep the existing canonical bilingual TERM-* parity check authoritative.
    base.parse_glossary_entries()
    glossary = parse_english_glossary()

    assets = {
        CLAIMS_TEX: render_claims(claims),
        PROGRAM_TEX: render_program(core, qwake),
        STAGE12_TEX: render_stage12(core),
        STAGE3_TEX: render_stage3(core),
        QWAKE_TEX: render_qwake(qwake),
        REPRO_TEX: render_reproducibility(core, qwake),
        TERMINOLOGY_TEX: render_terminology(glossary),
    }

    print("THESIS_ENGLISH_CLAIMS_SCHEMA=PASS")
    print("THESIS_ENGLISH_SOURCE_RECONCILIATION=PASS")
    print(f"THESIS_ENGLISH_GLOSSARY_COVERAGE={len(glossary)}/{EXPECTED_GLOSSARY_TERM_COUNT}")
    print("THESIS_ENGLISH_GLOSSARY_COVERAGE=PASS")

    if args.check:
        print("THESIS_ENGLISH_ASSET_WRITE=false")
        return

    GENERATED.mkdir(parents=True, exist_ok=True)
    for path, rendered in assets.items():
        path.write_text(rendered, encoding="utf-8", newline="\n")
        print(f"THESIS_ENGLISH_ASSET_RENDERED={path.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
