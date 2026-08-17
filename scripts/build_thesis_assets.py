#!/usr/bin/env python3
"""Validate thesis-facing data and render deterministic LaTeX assets."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
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
TERMINOLOGY_TEX = GENERATED / "terminology_registry.tex"
GLOSSARY_RU_PATH = ROOT / "docs" / "glossary.md"
GLOSSARY_EN_PATH = ROOT / "docs" / "glossary_EN.md"
EXPECTED_GLOSSARY_TERM_COUNT = 117



RUSSIAN_THESIS_SOURCES = (
    THESIS / "chapters" / "01_introduction.tex",
    THESIS / "chapters" / "02_related_work.tex",
    THESIS / "chapters" / "03_methodology.tex",
    THESIS / "chapters" / "04_experiments.tex",
    THESIS / "chapters" / "05_results.tex",
    THESIS / "chapters" / "06_discussion.tex",
    THESIS / "chapters" / "07_conclusion.tex",
    THESIS / "frontmatter" / "abstracts.tex",
    THESIS / "frontmatter" / "abbreviations.tex",
    THESIS / "appendices" / "terminology.tex",
    THESIS / "appendices" / "reproducibility.tex",
)

RUSSIAN_THESIS_SUPPORT_DOCS = (
    THESIS / "README.md",
    THESIS / "data" / "README.md",
)

# Generic English working vocabulary is not permitted in Russian dissertation
# prose. Exact method names, acronyms, machine identifiers and artifact paths
# are masked before this list is checked.
NONCANONICAL_RUSSIAN_PROSE = (
    "scope",
    "stage",
    "scenario",
    "baseline",
    "evidence",
    "policy",
    "policies",
    "accounting",
    "surface",
    "pre-action",
    "post-action",
    "preterminal",
    "observer",
    "recognizer",
    "recognizability",
    "candidate",
    "candidates",
    "confirmatory",
    "runtime",
    "marginal",
    "implementation",
    "admission",
    "claim",
    "claims",
    "gate",
    "gates",
    "provenance",
    "seed",
    "seeds",
    "dataset",
    "datasets",
    "profiling",
    "matched",
    "retry",
    "retries",
    "outcome",
    "outcomes",
    "sufficiency",
    "safe",
    "safety",
    "beneficial",
    "decision cost",
    "thesis-facing",
    "tracked",
    "execution",
    "estimand",
    "bounded",
    "feasibility",
    "lineage",
    "hardware",
    "software",
    "entrypoint",
    "artifact",
    "artifacts",
    "upstream",
    "workflow",
    "checkout",
    "metadata",
    "threshold",
    "residual",
    "final",
    "test",
    "quality",
    "device",
    "memory",
    "gradient",
    "representation",
    "difference",
    "equivalence",
    "environment",
    "measurement",
    "failure",
    "failures",
    "superiority",
    "eligible",
    "records",
    "dangerous",
    "coverage",
    "cost",
    "calibration",
)

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



def latex_prose(value: object) -> str:
    """Escape prose while preserving a small set of exact machine identifiers."""
    rendered = latex_breakable(value)
    identifiers = (
        "lenet_classic",
        "state_inference",
        "isolated_layer_vjp",
        "composite_vjp",
    )
    for identifier in identifiers:
        escaped = latex_breakable(identifier)
        rendered = rendered.replace(escaped, latex_code(identifier))
    return rendered


def visible_russian_tex(text: str, *, strip_english_abstract: bool = False) -> str:
    """Return user-visible Russian LaTeX prose with technical surfaces masked."""
    if strip_english_abstract:
        text = re.sub(
            r"\\begin\{otherlanguage\}\{english\}.*?\\end\{otherlanguage\}",
            " ",
            text,
            flags=re.DOTALL,
        )
    text = re.sub(r"(?m)%.*$", " ", text)
    text = re.sub(
        r"\\begin\{verbatim\}.*?\\end\{verbatim\}",
        " ",
        text,
        flags=re.DOTALL,
    )
    for command in (
        "code",
        "texttt",
        "cite",
        "label",
        "ref",
        "pageref",
        "input",
        "includegraphics",
        "url",
        "href",
    ):
        text = re.sub(
            rf"\\{command}(?:\[[^\]]*\])?\{{[^{{}}]*\}}",
            " ",
            text,
        )
    return text


def visible_russian_markdown(text: str) -> str:
    """Return Russian Markdown prose with code and link targets masked."""
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"`[^`]+`", " ", text)
    text = re.sub(r"\[[^\]]*\]\([^)]*\)", lambda m: m.group(0).split("]", 1)[0][1:], text)
    return text


def validate_russian_thesis_prose(rendered_assets: dict[Path, str]) -> None:
    """Reject generic English working vocabulary in Russian thesis-facing prose."""
    surfaces: list[tuple[str, str]] = []
    for path in RUSSIAN_THESIS_SOURCES:
        source = path.read_text(encoding="utf-8")
        visible = visible_russian_tex(
            source,
            strip_english_abstract=path.name == "abstracts.tex",
        )
        surfaces.append((path.relative_to(ROOT).as_posix(), visible))

    for path in RUSSIAN_THESIS_SUPPORT_DOCS:
        source = path.read_text(encoding="utf-8")
        surfaces.append(
            (path.relative_to(ROOT).as_posix(), visible_russian_markdown(source))
        )

    for path, rendered in rendered_assets.items():
        surfaces.append(
            (
                path.relative_to(ROOT).as_posix(),
                visible_russian_tex(rendered),
            )
        )

    violations: list[str] = []
    for label, text in surfaces:
        lowered = text.casefold()
        for term in NONCANONICAL_RUSSIAN_PROSE:
            pattern = rf"(?<![A-Za-z0-9_-]){re.escape(term)}(?![A-Za-z0-9_-])"
            if re.search(pattern, lowered, flags=re.IGNORECASE):
                violations.append(f"{label}: {term}")

    require(
        not violations,
        "noncanonical English prose in Russian dissertation: " + "; ".join(violations),
    )

def parse_glossary_entries() -> list[dict[str, str]]:
    """Parse the canonical Russian glossary and verify bilingual TERM-* parity."""
    ru_text = GLOSSARY_RU_PATH.read_text(encoding="utf-8")
    en_text = GLOSSARY_EN_PATH.read_text(encoding="utf-8")

    entry_re = re.compile(r"^### (TERM-[A-Z0-9-]+) — (.+)$")

    def parse_russian(text: str) -> list[dict[str, str]]:
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
            fields = (
                ("- **Значение в работе:** ", "meaning"),
                ("- **Правило употребления:** ", "rule"),
                ("- **Семантика имени:** ", "name_semantics"),
                ("- **Архитектурная роль:** ", "architectural_role"),
            )
            for prefix, key in fields:
                if raw_line.startswith(prefix):
                    current[key] = raw_line.removeprefix(prefix).strip()
                    break
        if current is not None:
            entries.append(current)
        return entries

    ru_entries = parse_russian(ru_text)
    en_ids = [
        match.group(1)
        for line in en_text.splitlines()
        if (match := entry_re.match(line)) is not None
    ]
    ru_ids = [item["term_id"] for item in ru_entries]

    require(
        len(ru_entries) == EXPECTED_GLOSSARY_TERM_COUNT,
        f"expected {EXPECTED_GLOSSARY_TERM_COUNT} glossary terms, got {len(ru_entries)}",
    )
    require(len(ru_ids) == len(set(ru_ids)), "Russian glossary TERM-* identifiers must be unique")
    require(ru_ids == en_ids, "Russian and English glossary TERM-* identifiers/order differ")
    for item in ru_entries:
        require(bool(item["section"]), f"{item['term_id']} has no glossary section")
        require(bool(item["meaning"]), f"{item['term_id']} has no Russian meaning")
        require(bool(item["rule"]), f"{item['term_id']} has no Russian usage rule")
    return ru_entries


def latex_glossary_inline(value: str) -> str:
    """Render glossary Markdown inline code/math without translating identifiers."""
    parts = re.split(r"(`[^`]*`|\$[^$]*\$|\\\([^)]*\\\))", value)
    rendered: list[str] = []
    for part in parts:
        if not part:
            continue
        if part.startswith("`") and part.endswith("`"):
            rendered.append(latex_code(part[1:-1]))
        elif (part.startswith("$") and part.endswith("$")) or (
            part.startswith(r"\(") and part.endswith(r"\)")
        ):
            rendered.append(part)
        else:
            rendered.append(latex_escape(part))
    return "".join(rendered)


def render_terminology_registry(entries: list[dict[str, str]]) -> str:
    """Render every canonical TERM-* entry into the dissertation appendix."""
    lines = [
        "% Generated by scripts/build_thesis_assets.py; do not edit manually.",
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
                    rf"\section{{{latex_escape(section)}}}",
                    r"\begin{longtable}{@{}L{0.31\textwidth}L{0.59\textwidth}@{}}",
                    r"\toprule",
                    r"Термин & Каноническое значение и граница употребления \\",
                    r"\midrule",
                    r"\endfirsthead",
                    r"\toprule",
                    r"Термин & Каноническое значение и граница употребления \\",
                    r"\midrule",
                    r"\endhead",
                ]
            )
        left = (
            rf"\textbf{{{latex_glossary_inline(item['term'])}}}"
            + r"\newline "
            + latex_code(item["term_id"])
        )
        right_parts = [latex_glossary_inline(item["meaning"])]
        if item["name_semantics"]:
            right_parts.append(
                r"\par\smallskip\emph{Семантика имени: }"
                + latex_glossary_inline(item["name_semantics"])
            )
        if item["architectural_role"]:
            right_parts.append(
                r"\par\smallskip\emph{Архитектурная роль: }"
                + latex_glossary_inline(item["architectural_role"])
            )
        right_parts.append(
            r"\par\smallskip\emph{Правило употребления: }"
            + latex_glossary_inline(item["rule"])
        )
        lines.append(left + " & " + "".join(right_parts) + r" \\")
    if current_section:
        lines.extend([r"\bottomrule", r"\end{longtable}"])
    lines.extend([r"\endgroup", ""])
    rendered = "\n".join(lines)
    rendered_ids = re.findall(r"TERM-[A-Z0-9-]+", rendered)
    require(
        len(set(rendered_ids)) == EXPECTED_GLOSSARY_TERM_COUNT,
        "rendered terminology registry does not contain every TERM-* identifier",
    )
    return rendered


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
    require(
        data.get("document_role") == "thesis-facing-derived-summary",
        "QWake summary must remain a thesis-facing derived summary",
    )
    require(
        data.get("scientific_evidence_status") == "not_new_scientific_evidence",
        "QWake summary must not claim new scientific evidence",
    )
    selection = data.get("selection")
    best = data.get("best_safe_policy")
    protocol = data.get("protocol")
    require(isinstance(selection, dict), "selection must be an object")
    require(isinstance(best, dict), "best_safe_policy must be an object")
    require(isinstance(protocol, dict), "protocol must be an object")
    source = data.get("source")
    require(isinstance(source, dict), "QWake source must be an object")
    for key in (
        "c1_request_file_sha256",
        "qwake_contract_file_sha256",
        "policy_selection_file_sha256",
        "receipt_semantic_sha256",
        "receipt_file_sha256",
        "best_safe_policy_sha256",
        "common_decision_cost_sequence_sha256",
    ):
        validate_sha256_identity(source.get(key), f"QWake source.{key}")

    bound_sources: dict[str, Path] = {}
    for path_key, digest_key in (
        ("c1_request_relative_path", "c1_request_file_sha256"),
        ("qwake_contract_relative_path", "qwake_contract_file_sha256"),
    ):
        relative = source.get(path_key)
        require(
            isinstance(relative, str) and bool(relative),
            f"QWake source.{path_key} must be a path",
        )
        bound = ROOT / relative
        require(bound.is_file(), f"QWake bound source missing: {relative}")
        require(
            sha256_file(bound) == source[digest_key],
            f"QWake bound source digest mismatch: {relative}",
        )
        bound_sources[path_key] = bound

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
    require(
        math.isclose(coverage, accepted / evaluated, rel_tol=0.0, abs_tol=1e-15),
        "coverage mismatch",
    )

    decomposition = data.get("temporal_surface_decomposition")
    require(
        isinstance(decomposition, dict),
        "temporal_surface_decomposition must be an object",
    )
    require(
        decomposition.get("derivation_status")
        == "structural_reconciliation_not_new_scientific_execution",
        "temporal decomposition must remain a structural reconciliation",
    )
    c1_request = load(bound_sources["c1_request_relative_path"])
    qwake_contract = load(bound_sources["qwake_contract_relative_path"])
    model_seeds = c1_request.get("model_seeds")
    dataset = c1_request.get("dataset")
    require(
        isinstance(model_seeds, list) and bool(model_seeds),
        "C1 request model_seeds must be non-empty",
    )
    require(isinstance(dataset, dict), "C1 request dataset must be an object")
    batches = dataset.get("batches")
    require(
        isinstance(batches, list) and bool(batches),
        "C1 request batches must be non-empty",
    )
    require(
        c1_request.get("role") == "C1_COLLECTION",
        "bound request must remain C1_COLLECTION",
    )
    require(
        qwake_contract.get("decision_epoch")
        == "after S_t and before sweep t+1 for t in [0,K_ref]",
        "QWake decision epoch must remain inclusive through K_ref",
    )
    require(
        qwake_contract.get("horizon_rule") == "registered_inference_steps",
        "QWake horizon rule must remain registered_inference_steps",
    )
    trajectory_count = len(model_seeds) * len(batches)
    require(
        evaluated % trajectory_count == 0,
        "QWake evaluated records must factor by C1 trajectories",
    )
    steps_per_trajectory = evaluated // trajectory_count
    k_ref = steps_per_trajectory - 1
    require(
        (len(model_seeds), len(batches), trajectory_count) == (3, 36, 108),
        "C1 trajectory identity mismatch",
    )
    require(
        (steps_per_trajectory, k_ref) == (7, 6),
        "QWake temporal surface identity mismatch",
    )
    require(
        best.get("feature_name") == "compute_step",
        "best-safe feature must remain compute_step",
    )
    require(
        best.get("predicate") == "feature_ge",
        "best-safe predicate must remain feature_ge",
    )
    threshold = float(best["threshold"])
    require(threshold == 5.0, "best-safe compute_step threshold must remain 5")
    accepted_steps = [step for step in range(k_ref + 1) if step >= threshold]
    preterminal_steps = [step for step in accepted_steps if step < k_ref]
    terminal_steps = [step for step in accepted_steps if step == k_ref]
    require(
        accepted_steps == [5, 6],
        "best-safe accepted temporal steps must remain 5 and 6",
    )
    require(
        preterminal_steps == [5] and terminal_steps == [6],
        "preterminal/terminal step partition mismatch",
    )
    preterminal_accepted = trajectory_count * len(preterminal_steps)
    terminal_accepted = trajectory_count * len(terminal_steps)
    preterminal_surface = trajectory_count * k_ref
    terminal_surface = trajectory_count
    require(
        preterminal_accepted + terminal_accepted == accepted,
        "accepted temporal decomposition mismatch",
    )
    expected_temporal = {
        "model_seed_count": len(model_seeds),
        "batch_count": len(batches),
        "trajectory_count": trajectory_count,
        "reference_horizon_k_ref": k_ref,
        "candidate_steps_per_trajectory": steps_per_trajectory,
        "preterminal_surface_records": preterminal_surface,
        "terminal_boundary_records": terminal_surface,
        "best_safe_policy_accepted_preterminal_records": preterminal_accepted,
        "best_safe_policy_accepted_terminal_records": terminal_accepted,
        "best_safe_policy_preterminal_compute_step": preterminal_steps[0],
        "best_safe_policy_preterminal_remaining_sweeps": k_ref - preterminal_steps[0],
        "best_safe_policy_terminal_compute_step": terminal_steps[0],
        "best_safe_policy_terminal_remaining_sweeps": k_ref - terminal_steps[0],
    }
    for key, expected in expected_temporal.items():
        require(
            decomposition.get(key) == expected,
            f"QWake temporal decomposition mismatch: {key}",
        )
    require(
        decomposition.get("registered_full_surface_coverage_includes_terminal_boundary")
        is True,
        "registered C2 coverage must explicitly retain the terminal boundary",
    )
    require(
        decomposition.get(
            "registered_full_surface_coverage_must_not_be_reinterpreted_as_preterminal_coverage"
        )
        is True,
        "registered C2 coverage must not be relabeled as preterminal coverage",
    )
    require(
        decomposition.get("cost_accounting_recalculated") is False,
        "T19 must not recalculate C2 cost accounting",
    )

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


def validate_qwake_claim_reconciliation(
    claims_data: dict[str, object], qwake: dict[str, object]
) -> None:
    claims = claims_data.get("claims")
    require(isinstance(claims, list), "claims must be a list for QWake reconciliation")
    by_id = {item.get("id"): item for item in claims if isinstance(item, dict)}
    for claim_id in ("C08", "C09", "C10", "C11"):
        require(claim_id in by_id, f"missing QWake claim {claim_id}")

    selection = qwake["selection"]
    best = qwake["best_safe_policy"]
    decomposition = qwake.get("temporal_surface_decomposition")
    protocol = qwake["protocol"]
    verification = qwake.get("verification")
    require(isinstance(selection, dict), "QWake selection must be an object")
    require(isinstance(best, dict), "QWake best_safe_policy must be an object")
    require(
        isinstance(decomposition, dict),
        "QWake temporal_surface_decomposition must be an object",
    )
    require(isinstance(protocol, dict), "QWake protocol must be an object")
    require(isinstance(verification, dict), "QWake verification must be an object")
    require(int(verification.get("sealed_result_audit_fail", -1)) == 0, "sealed QWake audit must have zero failures")
    require(int(verification.get("cost_decomposition_audit_fail", -1)) == 0, "QWake cost audit must have zero failures")
    require(verification.get("zero_write") is True, "QWake thesis-facing verification must remain zero-write")

    accepted = int(best["accepted_records"])
    dangerous = int(best["dangerous_accepts"])
    safe_accepts = accepted - dangerous
    safe_nontrivial = int(selection["safe_nontrivial_count"])
    eligible = int(selection["eligible_policy_count"])

    require(safe_accepts > 0, "C08 requires at least one safe accepted record")
    require(
        int(decomposition.get("best_safe_policy_accepted_preterminal_records", 0))
        == 108,
        "C08 requires the structurally reconciled 108 preterminal accepted records",
    )
    require(
        int(decomposition.get("best_safe_policy_accepted_terminal_records", 0))
        == 108,
        "C08 full-surface coverage must retain the 108 terminal-boundary accepts",
    )
    require(safe_nontrivial > 0, "C08 requires non-zero safe recognizability")
    require(by_id["C08"].get("status") == "supported", "C08 status must be supported")

    require(eligible == 0, "C09 rejection requires zero eligible policies")
    require(
        selection.get("status") == "bounded_negative_no_safe_beneficial_policy",
        "C09 requires the frozen bounded-negative selection status",
    )
    require(by_id["C09"].get("status") == "rejected", "C09 status must be rejected")

    require(by_id["C10"].get("status") == "not_tested", "C10 must remain not_tested")
    require(by_id["C11"].get("status") == "not_tested", "C11 must remain not_tested")
    require(protocol.get("c3_open") is False, "C11 not_tested requires C3 to remain closed")

    require(
        verification.get("policy_evaluation_performed") is False,
        "thesis validation must not perform a new QWake policy evaluation",
    )
    require(
        verification.get("policy_interpretation_performed") is False,
        "thesis validation must not reinterpret the sealed QWake result",
    )
    require(
        verification.get("cost_model_changed") is False,
        "thesis validation must preserve frozen QWake cost accounting",
    )


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

    matched_analysis = stage3b["matched_analysis"]
    require(isinstance(matched_analysis, dict), "matched analysis summary invalid")
    decision = load(ROOT / "results/stage-3/analysis/matched/stage3b-matched-descriptive-analysis-70d6c3c-v1/engineering_decision.json")
    candidate_rows = csv_rows("results/stage-3/analysis/matched/stage3b-matched-descriptive-analysis-70d6c3c-v1/candidate_method_summary.csv")
    receipt = load(ROOT / "experiments/frozen/stage3b-matched-descriptive-analysis-publication-receipt-v1/receipt.json")

    require(decision["decision_scope"] == matched_analysis["decision_scope"] == "engineering_continuation_not_superiority", "matched analysis decision scope mismatch")
    require(decision["superiority_claim_permitted"] is matched_analysis["superiority_claim_permitted"] is False, "matched analysis superiority boundary mismatch")
    require(len(candidate_rows) == int(matched_analysis["candidate_method_group_count"]) == 4, "matched analysis candidate-method group count mismatch")
    expected_pairs = {
        ("isolated_layer_vjp", "fixedpred"),
        ("isolated_layer_vjp", "strict"),
        ("composite_vjp", "fixedpred"),
        ("composite_vjp", "strict"),
    }
    require({(row["candidate_id"], row["method"]) for row in candidate_rows} == expected_pairs, "matched analysis candidate-method groups mismatch")
    for row in candidate_rows:
        require(int(row["configuration_count"]) == int(matched_analysis["configuration_count_per_group"]) == 16, "matched analysis configuration count mismatch")
        require(int(row["qualified_configuration_count"]) == int(matched_analysis["qualified_configuration_count_per_group"]) == 0, "matched analysis qualified count mismatch")
        require(row["status"] == "reject_or_revise", "matched analysis group decision mismatch")

    expected_decisions = matched_analysis["candidate_decisions"]
    require(isinstance(expected_decisions, dict), "matched analysis candidate decisions invalid")
    observed_decisions = {item["candidate_id"]: item["status"] for item in decision["candidate_decisions"]}
    require(observed_decisions == expected_decisions == {"isolated_layer_vjp": "reject_or_revise", "composite_vjp": "reject_or_revise"}, "matched analysis candidate decision mismatch")

    claim_boundary = receipt["claim_boundary"]
    require(receipt["status"] == "publication_action_complete", "matched analysis publication receipt incomplete")
    require(claim_boundary["results_publication_permitted"] is matched_analysis["results_publication_permitted"] is True, "matched analysis publication permission mismatch")
    require(claim_boundary["release_publication_complete"] is matched_analysis["release_publication_complete"] is True, "matched analysis release publication mismatch")
    require(claim_boundary["superiority_claim_permitted"] is matched_analysis["superiority_claim_permitted"] is False, "matched analysis publication superiority boundary mismatch")


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
                latex_prose(item["claim"]),
                latex_escape(STATUS_LABELS[str(item["status"])]),
                latex_prose(item["scope"]),
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
        texrow(f"этап 1 & {int(s1['planned_cells'])} итоговых ячеек; 10 независимо обученных моделей & качество и стоимость & исходная сравнительная кампания"),
        texrow(f"этап 2 & {int(s2['completed_unique_cells'])} итоговых ячеек & контролируемое изменение реализации & все итоговые ячейки завершены; тестовая оценка выполнена"),
        texrow(f"этап 3A & {int(s3a['independent_model_seeds'])} независимо обученных моделей & диагностика механизма & градиенты, CKA/RSA и численный контроль Exact"),
        texrow(f"этап 3B & {int(s3b['matched_profiling']['matched_cell_count'])} сопоставленных ячеек & стоимость и отнесение к механизму & B0, SI-MA0/1, B1/B2 и профилирование с зафиксированной целостностью"),
        texrow(f"QWake C2 & {int(selection['candidate_count'])} зафиксированных правил; 756 записей & безопасность и экономика & ограниченно отрицательный результат; C3 закрыт"),
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
        r"\caption{Этап 1: FashionMNIST, средние значения по 10 независимо обученным моделям}",
        r"\label{tab:stage1-summary}",
        r"\begin{tabular}{lrr}",
        r"\toprule",
        texrow("Метод & Тестовая macro-F1 & Время обучения, с"),
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
            r"\caption{Этап 2: межверсионное отношение времени выполнения относительно BP к этапу 1}",
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
        r"\caption{Ключевые зарегистрированные результаты этапа 3}",
        r"\label{tab:stage3-summary}",
        r"\begin{tabular}{@{}L{0.18\textwidth}L{0.69\textwidth}@{}}",
        r"\toprule",
        texrow("Подэтап & Зарегистрированный результат"),
        r"\midrule",
        texrow(f"этап 3A & максимальная абсолютная ошибка Exact = {float(s3a['exact_control_max_abs_error']):.3e}; косинусное сходство FixedPred на слое 0 = {float(s3a['fixedpred']['gradient_layer0_cosine_mean']):.6f}, отношение норм = {float(s3a['fixedpred']['gradient_layer0_norm_ratio_mean']):.6f}."),
        texrow(f"B0 & медианное отношение времени устройства Strict/FixedPred = {float(b0['strict_to_fixedpred_device_time_configuration_median_ratio']):.3f}; отношение пиковой выделенной памяти = {float(b0['strict_to_fixedpred_peak_allocated_configuration_median_ratio']):.3f}."),
        texrow(f"SI-MA0 & COST-MA0 не пройдена; проверку прошли {int(ma0['passing_measured_steps'])}/{int(ma0['measured_steps'])} измеренных шагов; медианный знаковый остаток учёта = {float(ma0['accounting_residual_median']):.3f}."),
        texrow(f"SI-MA1 & CAL-COST-MA1 пройдена; 10 независимо обученных моделей, {int(ma1['matched_block_count'])} сопоставленных блоков; верхняя односторонняя 95\\%-я граница = {float(ma1['upper_one_sided_95']):.3f} при пороге {float(ma1['threshold']):.2f}."),
        texrow(f"B1/B2 & EQ-B1 и EQ-B2 пройдены; B1: {int(s3b['b1']['observed_pair_count'])} пар, B2: {int(s3b['b2']['matched_triples_observed'])} сопоставленных троек; неуспешных пар нет."),
        texrow(f"Сопоставленное профилирование & целостность зафиксирована для {int(s3b['matched_profiling']['matched_cell_count'])}/{int(s3b['matched_profiling']['matched_cell_count'])} ячеек; {int(s3b['matched_profiling']['cross_candidate_correctness_block_count'])} блоков проверки корректности; повторных запусков = {int(s3b['matched_profiling']['retried_cell_count'])}."),
        texrow(f"Инженерный экран B1/B2 & четыре группы кандидат×метод по {int(s3b['matched_analysis']['configuration_count_per_group'])} конфигураций; квалифицировано {int(s3b['matched_analysis']['qualified_configuration_count_per_group'])}/{int(s3b['matched_analysis']['configuration_count_per_group'])} в каждой группе; оба кандидата получили решение reject\\_or\\_revise; утверждение о превосходстве не разрешено."),
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
        "",
    ]
    return "\n".join(lines)


def render_qwake(qwake: dict[str, object]) -> str:
    s = qwake["selection"]
    b = qwake["best_safe_policy"]
    d = qwake["temporal_surface_decomposition"]
    observer_share = int(b["cost_observer_ns"]) / int(b["total_decision_cost_ns"]) * 100.0
    lines = [
        "% Generated by scripts/build_thesis_assets.py; do not edit manually.",
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{QWake C2: последовательность зарегистрированных проверок}",
        r"\label{tab:qwake-funnel}",
        r"\begin{tabular}{lr}",
        r"\toprule",
        texrow("Категория & Число правил"),
        r"\midrule",
        texrow(f"Всего зафиксированных кандидатов & {int(s['candidate_count'])}"),
        texrow(f"Небезопасные & {int(s['unsafe_count'])}"),
        texrow(f"Без опасных принятий & {int(s['zero_danger_count'])}"),
        texrow(f"Безопасные с ненулевым покрытием & {int(s['safe_nontrivial_count'])}"),
        texrow(f"Безопасные и экономически выгодные & {int(s['eligible_policy_count'])}"),
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
        "",
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{QWake C2: временное разложение и стоимость лучшего безопасного правила}",
        r"\label{tab:qwake-cost}",
        r"\begin{tabular}{@{}p{0.76\textwidth}r@{}}",
        r"\toprule",
        texrow("Показатель & Значение"),
        r"\midrule",
        texrow(f"Принято / оценено на полной поверхности C1 & {int(b['accepted_records'])} / {int(b['evaluated_records'])}"),
        texrow(f"Опасные принятия & {int(b['dangerous_accepts'])}"),
        texrow(f"Зарегистрированное покрытие полной поверхности & {float(b['coverage']) * 100.0:.2f}\\%"),
        texrow(f"Предтерминальных записей на поверхности C1 & {int(d['preterminal_surface_records'])}"),
        texrow(f"Принятые предтерминальные записи (шаг 5, один оставшийся проход) & {int(d['best_safe_policy_accepted_preterminal_records'])}"),
        texrow(f"Записей терминальной границы на поверхности C1 & {int(d['terminal_boundary_records'])}"),
        texrow(f"Принятые записи терминальной границы (шаг 6) & {int(d['best_safe_policy_accepted_terminal_records'])}"),
        texrow(f"Зарегистрированная сумма {latex_code('remaining_suffix_ns')} по безопасно принятым записям & {int(b['gross_implied_avoided_suffix_ns']) / 1e9:.3f} с"),
        texrow(f"Полная стоимость решения & {int(b['total_decision_cost_ns']) / 1e9:.3f} с"),
        texrow(f"Доля наблюдателя в полной стоимости & {observer_share:.3f}\\%"),
        texrow(f"Совокупная чистая экономия & {int(b['total_net_saving_ns']) / 1e9:.3f} с"),
        texrow(f"Снижение стоимости до безубыточности & {float(b['required_cost_reduction_for_zero_net_fraction']) * 100.0:.3f}\\%"),
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
        r"Источник / идентификатор & SHA-256 \\",
        r"\midrule",
        r"\endfirsthead",
        r"\toprule",
        r"Источник / идентификатор & SHA-256 \\",
        r"\midrule",
        r"\endhead",
    ]
    for relative, digest in bindings.items():
        lines.append(f"{latex_code(relative)} & {latex_digest(digest)} \\\\")

    qlabels = (
        ("Замороженный запрос QWake C1", "c1_request_file_sha256"),
        ("Контракт специального случая QWake-FP", "qwake_contract_file_sha256"),
        ("Файл выбора правила QWake C2", "policy_selection_file_sha256"),
        ("Семантика квитанции QWake C2", "receipt_semantic_sha256"),
        ("Файл квитанции QWake C2", "receipt_file_sha256"),
        ("Лучшее безопасное правило QWake", "best_safe_policy_sha256"),
        ("Общая последовательность стоимости решения QWake", "common_decision_cost_sequence_sha256"),
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
    glossary_entries = parse_glossary_entries()
    validate_claims(claims)
    validate_qwake(qwake)
    validate_qwake_claim_reconciliation(claims, qwake)
    validate_core_results(core)

    assets = {
        CLAIMS_TEX: render_claims(claims),
        PROGRAM_TEX: render_program(core, qwake),
        STAGE12_TEX: render_stage12(core),
        STAGE3_TEX: render_stage3(core),
        QWAKE_TEX: render_qwake(qwake),
        REPRO_TEX: render_reproducibility(core, qwake),
        TERMINOLOGY_TEX: render_terminology_registry(glossary_entries),
    }
    validate_russian_thesis_prose(assets)

    print("THESIS_CLAIMS_SCHEMA=PASS")
    print("THESIS_QWAKE_SUMMARY_ARITHMETIC=PASS")
    print("THESIS_QWAKE_PROTOCOL_BOUNDARY=PASS")
    print("THESIS_QWAKE_CLAIM_RECONCILIATION=PASS")
    print("THESIS_QWAKE_TEMPORAL_SURFACE_RECONCILIATION=PASS")
    print("THESIS_CORE_RESULTS_SOURCE_BINDINGS=PASS")
    print("THESIS_CORE_RESULTS_RECONCILIATION=PASS")
    print("THESIS_STAGE3B_MATCHED_DECISION_RECONCILIATION=PASS")
    print("THESIS_PROVENANCE_IDENTITIES=PASS")
    print("THESIS_RUSSIAN_PROSE=PASS")
    print(f"THESIS_GLOSSARY_TERM_COUNT={len(glossary_entries)}")
    print(f"THESIS_GLOSSARY_COVERAGE={len(glossary_entries)}/{EXPECTED_GLOSSARY_TERM_COUNT}")
    print("THESIS_GLOSSARY_COVERAGE=PASS")

    if args.check:
        print("THESIS_ASSET_WRITE=false")
        return

    GENERATED.mkdir(parents=True, exist_ok=True)
    for path, rendered in assets.items():
        path.write_text(rendered, encoding="utf-8", newline="\n")
        print(f"THESIS_ASSET_RENDERED={path.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
