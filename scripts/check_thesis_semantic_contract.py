#!/usr/bin/env python3
"""Enforce stable thesis terminology, symbol namespaces, and claim-status semantics."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THESIS = ROOT / "thesis"
CLAIMS = THESIS / "data" / "research_claims.json"
ABBREVIATIONS = THESIS / "frontmatter" / "abbreviations.tex"
INTRODUCTION = THESIS / "chapters" / "01_introduction.tex"
RELATED_WORK = THESIS / "chapters" / "02_related_work.tex"
METHODOLOGY = THESIS / "chapters" / "03_methodology.tex"
CONCLUSION = THESIS / "chapters" / "07_conclusion.tex"
GLOSSARY_RU = ROOT / "docs" / "glossary.md"
GLOSSARY_EN = ROOT / "docs" / "glossary_EN.md"

STATUS_LABELS = {"supported", "rejected", "descriptive", "not_tested"}


def thesis_sources() -> dict[Path, str]:
    paths = sorted((THESIS / "chapters").glob("*.tex"))
    paths += sorted((THESIS / "frontmatter").glob("*.tex"))
    return {path: path.read_text(encoding="utf-8") for path in paths}


def fail(bucket: list[str], label: str, detail: str) -> None:
    bucket.append(f"{label}: {detail}")


def require_contains(bucket: list[str], text: str, marker: str, label: str) -> None:
    if marker not in text:
        fail(bucket, label, f"missing canonical marker {marker!r}")


def require_absent_regex(
    bucket: list[str], sources: dict[Path, str], pattern: str, label: str
) -> None:
    regex = re.compile(pattern, flags=re.IGNORECASE | re.MULTILINE)
    for path, text in sources.items():
        match = regex.search(text)
        if match:
            line = text.count("\n", 0, match.start()) + 1
            fail(bucket, label, f"{path.relative_to(ROOT)}:{line}: {match.group(0)!r}")


def check_terminology_invariance(sources: dict[Path, str]) -> list[str]:
    errors: list[str] = []
    # The canonical term is "полная достаточность ... на зарегистрированной области".
    require_absent_regex(
        errors,
        sources,
        r"глобальн\w*\s+достаточност\w*",
        "legacy sufficiency term",
    )
    require_absent_regex(
        errors,
        sources,
        r"предтерминальн\w*\s+исход\w*",
        "record/state type drift",
    )
    require_absent_regex(
        errors,
        sources,
        r"(?:семейств\w*\s+кандидат\w*\s+C2|C2[^\n]{0,80}кандидат\w*|кандидат\w*[^\n]{0,80}C2)",
        "C2 rule/candidate drift",
    )
    require_absent_regex(
        errors,
        sources,
        r"(?:среди|всем|все(?:м)?)\s+кандидат\w*[^\n]{0,100}(?:опасн\w*\s+принят|стоимост\w*\s+решен)",
        "C2 rule/candidate drift",
    )
    require_absent_regex(
        errors,
        sources,
        r"безопасно\s+принят\w*\s+запис",
        "bounded safety shorthand drift",
    )
    require_absent_regex(
        errors,
        sources,
        r"конкретн\w*\s+политик\w*",
        "rule/policy drift",
    )
    require_absent_regex(
        errors,
        sources,
        r"локализовать\s+механизм\s+расхождения|этап\s*3B:\s*стоимость\s+и\s+механизм|к\s+механизму\s+стоимости",
        "RQ2 causal-strength drift",
    )
    builder = (ROOT / "scripts" / "build_thesis_assets.py").read_text(encoding="utf-8")
    for legacy_label in (
        "Всего зафиксированных кандидатов",
        "Небезопасные",
        "Безопасные с ненулевым покрытием",
        "Лучшее безопасное правило QWake",
        "лучшего безопасного правила",
    ):
        if legacy_label in builder:
            fail(errors, "generated terminology drift", legacy_label)
    return errors


def check_theory_layer_separation(sources: dict[Path, str]) -> list[str]:
    errors: list[str] = []
    glossary_ru = GLOSSARY_RU.read_text(encoding="utf-8")
    glossary_en = GLOSSARY_EN.read_text(encoding="utf-8")
    related = RELATED_WORK.read_text(encoding="utf-8")
    conclusion = CONCLUSION.read_text(encoding="utf-8")

    forbidden = (
        (
            glossary_ru,
            "PC-CATM является механизмным слоем PC-TREF",
            "RU glossary collapses PC-CATM into PC-TREF",
        ),
        (
            glossary_en,
            "PC-CATM is the mechanism layer of PC-TREF",
            "EN glossary collapses PC-CATM into PC-TREF",
        ),
    )
    for text, marker, label in forbidden:
        if marker in text:
            fail(errors, "theory layer separation", label)

    required = (
        (
            glossary_ru,
            "PC-CATM является отдельным механизмным уровнем, связанным с PC-TREF",
            "RU glossary relation",
        ),
        (
            glossary_en,
            "PC-CATM is a distinct mechanistic layer linked to PC-TREF",
            "EN glossary relation",
        ),
        (
            related,
            "Два уровня решают разные задачи и поэтому не должны сливаться в одну модель.",
            "related-work separation",
        ),
        (
            conclusion,
            "Эти уровни намеренно не отождествляются.",
            "conclusion separation",
        ),
    )
    for text, marker, label in required:
        require_contains(errors, text, marker, label)

    return errors


def check_qwake_rule_vocabulary() -> list[str]:
    errors: list[str] = []
    english_abstract = (THESIS / "frontmatter" / "abstract_en_content.tex").read_text(
        encoding="utf-8"
    )

    policy_match = re.search(r"\bpolic(?:y|ies)\b", english_abstract, flags=re.IGNORECASE)
    if policy_match:
        fail(
            errors,
            "QWake rule vocabulary",
            f"English abstract uses {policy_match.group(0)!r} for a C2 rule",
        )

    normalized = " ".join(english_abstract.split())
    required = (
        "frozen family of 2,625 scalar rules",
        "264 rules had non-zero coverage with zero dangerous accepts",
        "highest-coverage rule among rules with zero observed dangerous accepts",
        "No rule achieved positive aggregate net saving",
        "no C2 rule freeze was established",
        "rejects the existence of a rule with zero observed dangerous accepts",
    )
    for marker in required:
        require_contains(errors, normalized, marker, "QWake rule vocabulary")

    glossary_en = GLOSSARY_EN.read_text(encoding="utf-8")
    require_contains(
        errors,
        glossary_en,
        "QWake C2 rules are not called candidates",
        "QWake rule vocabulary",
    )
    return errors


def check_qwake_action_semantics() -> list[str]:
    errors: list[str] = []
    abstracts = "\n".join(
        (THESIS / "frontmatter" / name).read_text(encoding="utf-8")
        for name in ("abstract_ru_content.tex", "abstract_en_content.tex")
    )
    related = RELATED_WORK.read_text(encoding="utf-8")
    methodology = METHODOLOGY.read_text(encoding="utf-8")
    experiments = (THESIS / "chapters" / "04_experiments.tex").read_text(encoding="utf-8")
    results = (THESIS / "chapters" / "05_results.tex").read_text(encoding="utf-8")
    discussion = (THESIS / "chapters" / "06_discussion.tex").read_text(encoding="utf-8")
    conclusion = CONCLUSION.read_text(encoding="utf-8")

    forbidden = (
        (
            related,
            "признание текущего состояния достаточным и прекращение оставшегося",
            "QWake-FP acceptance collapses analytic completion into no further compute",
        ),
        (
            methodology,
            "раннее завершение допустимо по эталонной",
            "methodology describes the registered action as bare termination",
        ),
        (
            abstracts,
            "states make early termination task-admissible",
            "English abstract collapses the registered analytic action into termination",
        ),
    )
    for surface, marker, label in forbidden:
        if marker in surface:
            fail(errors, "QWake action semantics", label)

    required = (
        (
            abstracts,
            "fixedpred_eta1_wavefront_completion_v1",
            "abstract analytic candidate",
        ),
        (
            abstracts,
            "complete_suffix_stage2_baseline_v1",
            "abstract exact reference",
        ),
        (
            related,
            "Принятие поэтому не означает",
            "theory non-zero-compute boundary",
        ),
        (
            methodology,
            r"\texttt{ANALYTIC\_COMPLETION}",
            "methodology action family",
        ),
        (
            methodology,
            "fixedpred_eta1_wavefront_completion_v1",
            "methodology candidate id",
        ),
        (
            methodology,
            "complete_suffix_stage2_baseline_v1",
            "methodology exact reference id",
        ),
        (
            experiments,
            r"\texttt{EARLY\_ADMISSIBLE} формируется только после сравнения требуемых",
            "experiment oracle binding",
        ),
        (
            results,
            r"\texttt{compute\_step >= 5}",
            "results temporal rule",
        ),
        (
            discussion,
            "не демонстрирует адаптивность по",
            "discussion adaptivity boundary",
        ),
        (
            conclusion,
            r"\texttt{ANALYTIC\_COMPLETION}",
            "conclusion action family",
        ),
    )
    for surface, marker, label in required:
        require_contains(errors, surface, marker, label)

    return errors


def check_symbol_namespace(sources: dict[Path, str]) -> list[str]:
    errors: list[str] = []
    thesis_text = "\n".join(sources.values())
    forbidden = {
        r"A_p\s*\(": "legacy PC-TREF rule symbol A_p(a)",
        r"A\s*\(p\)": "set/count collision A(p)",
        r"D\s*\(p\)": "legacy dangerous-count symbol D(p)",
        r"N\s*\(p\)": "legacy net-saving symbol N(p)",
        r"\\Omega_\{\\mathrm\{pre\}\}": "record/state collision Omega_pre",
        r"\\sum_a\s+c_l\^\{\(a\)\}": "action/channel index collision",
        r"\\ker\s+S_l": "legacy correction-sum operator S_l",
        r"\$S_t\$": "undefined C1 state symbol S_t",
    }
    for pattern, label in forbidden.items():
        match = re.search(pattern, thesis_text)
        if match:
            fail(errors, label, repr(match.group(0)))

    related = RELATED_WORK.read_text(encoding="utf-8")
    methodology = METHODOLOGY.read_text(encoding="utf-8")
    canonical_related = (
        r"\mathcal T_R=(\mathcal A,L_R,\delta_R,q_R,d_R)",
        r"A_{\pi}(a)",
        r"\mathfrak D_{\pi,a}",
        r"\mathcal S_l",
        r"\sum_k c_l^{(k)}",
    )
    for marker in canonical_related:
        require_contains(errors, related, marker, "related-work symbol contract")

    canonical_method = (
        r"\rho_{j,t}\in\mathcal R_{C1}",
        r"x(\rho_{j,t})\in\mathcal X",
        r"\mathcal R_{\mathrm{pre}}",
        r"n_{\mathrm{acc}}(\pi)",
        r"n_{\mathrm{danger}}(\pi)",
        r"n_{\mathrm{eval}}",
        r"\Delta_{\mathrm{net}}(\pi)",
        r"\kappa_i",
    )
    for marker in canonical_method:
        require_contains(errors, methodology, marker, "methodology symbol contract")
    return errors


def check_first_definitions() -> list[str]:
    errors: list[str] = []
    abbreviations = ABBREVIATIONS.read_text(encoding="utf-8")
    requirements = {
        "B1/B2": ("точные кандидаты реализации", "не меняет их роль кандидата"),
        "NCZ": ("точная тривиальная часть", "численном протоколе отдельно"),
        "ECZ": ("точная нетривиальная часть", "численном протоколе отдельно"),
        "TNZ": ("ядре", "сопряжённого оператора переноса"),
    }
    for term, markers in requirements.items():
        match = re.search(
            rf"\\item\[{term}\](.*?)(?=\\item\[|\\end\{{description\}})", abbreviations, re.DOTALL
        )
        if not match:
            fail(errors, "first definition", f"missing abbreviation definition for {term}")
            continue
        definition = match.group(1)
        for marker in markers:
            if marker not in definition:
                fail(errors, "first definition", f"{term} missing {marker!r}")

    glossary_ru = GLOSSARY_RU.read_text(encoding="utf-8")
    glossary_en = GLOSSARY_EN.read_text(encoding="utf-8")
    require_contains(
        errors,
        glossary_ru,
        "Правила QWake C2 кандидатами не называются",
        "candidate first definition",
    )
    require_contains(
        errors,
        glossary_en,
        "QWake C2 rules are not called candidates",
        "candidate first definition",
    )
    return errors


def check_claim_status_semantics() -> list[str]:
    errors: list[str] = []
    data = json.loads(CLAIMS.read_text(encoding="utf-8"))
    values = data.get("status_values")
    semantics = data.get("status_semantics")
    if set(values or []) != STATUS_LABELS:
        fail(errors, "status values", f"expected {sorted(STATUS_LABELS)}, got {values!r}")
    if not isinstance(semantics, dict) or set(semantics) != STATUS_LABELS:
        fail(errors, "status semantics", "status_semantics keys must exactly match status_values")
    elif not all(isinstance(value, str) and value.strip() for value in semantics.values()):
        fail(errors, "status semantics", "all definitions must be non-empty strings")

    for claim in data.get("claims", []):
        if claim.get("status") not in STATUS_LABELS:
            fail(errors, "claim status", f"{claim.get('id')}: {claim.get('status')!r}")

    intro = INTRODUCTION.read_text(encoding="utf-8")
    conclusion = CONCLUSION.read_text(encoding="utf-8")
    for label in STATUS_LABELS:
        marker = rf"\texttt{{{label.replace('_', r'\_')}}}"
        if marker not in intro:
            fail(errors, "status semantics", f"introduction does not define {label}")
        if marker not in conclusion:
            fail(errors, "status semantics", f"conclusion does not preserve {label}")
    return errors


def main() -> None:
    sources = thesis_sources()
    checks = (
        ("THESIS_TERMINOLOGY_INVARIANCE", check_terminology_invariance(sources)),
        ("THESIS_THEORY_LAYER_SEPARATION", check_theory_layer_separation(sources)),
        ("THESIS_QWAKE_RULE_VOCABULARY", check_qwake_rule_vocabulary()),
        ("THESIS_QWAKE_ACTION_SEMANTICS", check_qwake_action_semantics()),
        ("THESIS_SYMBOL_NAMESPACE", check_symbol_namespace(sources)),
        ("THESIS_TERM_FIRST_DEFINITION", check_first_definitions()),
        ("THESIS_CLAIM_STATUS_SEMANTICS", check_claim_status_semantics()),
    )
    failed = False
    for gate, errors in checks:
        if errors:
            failed = True
            print(f"{gate}=FAIL")
            for error in errors:
                print(f"SEMANTIC_CONTRACT_ERROR={error}")
        else:
            print(f"{gate}=PASS")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
