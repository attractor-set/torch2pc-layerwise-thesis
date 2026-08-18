#!/usr/bin/env python3
"""Validate claim-to-section traceability across the dissertation."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THESIS = ROOT / "thesis"
CLAIMS_PATH = THESIS / "data" / "research_claims.json"
TRACE_PATH = THESIS / "data" / "thesis_traceability.json"
CHAPTERS = THESIS / "chapters"

REQUIRED_STAGES = (
    "theory",
    "methodology",
    "experiment",
    "results",
    "discussion",
    "conclusion",
)
STAGE_PREFIX = {
    "theory": "02_",
    "methodology": "03_",
    "experiment": "04_",
    "results": "05_",
    "discussion": "06_",
    "conclusion": "07_",
}
CLAIM_ID_RE = re.compile(r"^C(?:0[1-9]|1[01])$")
CLAIM_TOKEN_RE = re.compile(r"\bC(0[1-9]|1[01])\b")
CLAIM_RANGE_RE = re.compile(r"\bC(0[1-9]|1[01])--C(0[1-9]|1[01])\b")
LABEL_RE = re.compile(r"\\label\{([^}]+)\}")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def fail(errors: list[str], detail: str) -> None:
    errors.append(detail)


def chapter_label_index() -> dict[str, Path]:
    index: dict[str, Path] = {}
    duplicates: set[str] = set()
    # Claim-to-section bindings are defined against the canonical Russian
    # dissertation source. The English rendering intentionally reuses the same
    # LaTeX labels in a separate document, so it must not be folded into this
    # single-document label namespace. RU/EN correspondence is enforced by
    # check_thesis_language_congruence.py instead.
    for path in sorted(CHAPTERS.glob("*.tex")):
        if path.name.endswith("_EN.tex"):
            continue
        text = path.read_text(encoding="utf-8")
        for label in LABEL_RE.findall(text):
            if label in index:
                duplicates.add(label)
            else:
                index[label] = path
    if duplicates:
        names = ", ".join(sorted(duplicates))
        raise ValueError(f"duplicate thesis labels: {names}")
    return index


def section_text_for_label(path: Path, label: str) -> str:
    text = path.read_text(encoding="utf-8")
    marker = rf"\label{{{label}}}"
    marker_pos = text.find(marker)
    if marker_pos < 0:
        return ""
    section_pos = text.rfind(r"\section{", 0, marker_pos)
    if section_pos < 0:
        section_pos = marker_pos
    next_section = text.find(r"\section{", marker_pos + len(marker))
    if next_section < 0:
        next_section = len(text)
    return text[section_pos:next_section]


def claim_ids_in_text(text: str) -> set[str]:
    ids = {f"C{value}" for value in CLAIM_TOKEN_RE.findall(text)}
    for start, end in CLAIM_RANGE_RE.findall(text):
        lo = int(start)
        hi = int(end)
        if lo <= hi:
            ids.update(f"C{value:02d}" for value in range(lo, hi + 1))
    return ids


def validate_schema(trace: dict, errors: list[str]) -> None:
    if trace.get("schema_version") != 1:
        fail(errors, "schema_version must be 1")
    if trace.get("document_role") != "dissertation-claim-traceability":
        fail(errors, "unexpected document_role")
    if trace.get("source_contract") != "thesis/data/research_claims.json":
        fail(errors, "source_contract must point to research_claims.json")
    if tuple(trace.get("required_stages", [])) != REQUIRED_STAGES:
        fail(errors, f"required_stages must be {REQUIRED_STAGES!r}")
    claims = trace.get("claims")
    if not isinstance(claims, list) or not claims:
        fail(errors, "claims must be a non-empty list")
        return
    ids = [item.get("id") for item in claims if isinstance(item, dict)]
    if len(ids) != len(set(ids)):
        fail(errors, "claim ids must be unique")
    for cid in ids:
        if not isinstance(cid, str) or not CLAIM_ID_RE.fullmatch(cid):
            fail(errors, f"invalid claim id: {cid!r}")


def validate_contract_alignment(claims: dict, trace: dict, errors: list[str]) -> None:
    source = {item["id"]: item for item in claims.get("claims", [])}
    mapped = {item["id"]: item for item in trace.get("claims", [])}
    if set(source) != set(mapped):
        missing = sorted(set(source) - set(mapped))
        extra = sorted(set(mapped) - set(source))
        fail(errors, f"claim-set mismatch missing={missing} extra={extra}")
        return
    for cid, source_item in source.items():
        mapped_item = mapped[cid]
        if mapped_item.get("rq") != source_item.get("rq"):
            fail(errors, f"{cid}: rq drift")
        if mapped_item.get("status") != source_item.get("status"):
            fail(errors, f"{cid}: status drift")


def validate_sections(trace: dict, labels: dict[str, Path], errors: list[str]) -> None:
    for item in trace.get("claims", []):
        cid = item["id"]
        sections = item.get("sections")
        if not isinstance(sections, dict):
            fail(errors, f"{cid}: sections must be an object")
            continue
        if set(sections) != set(REQUIRED_STAGES):
            fail(errors, f"{cid}: sections must contain exactly {REQUIRED_STAGES!r}")
            continue
        for stage in REQUIRED_STAGES:
            refs = sections.get(stage)
            if not isinstance(refs, list) or not refs:
                fail(errors, f"{cid}: {stage} requires at least one section")
                continue
            for label in refs:
                path = labels.get(label)
                if path is None:
                    fail(errors, f"{cid}: missing label {label!r}")
                    continue
                if not path.name.startswith(STAGE_PREFIX[stage]):
                    fail(
                        errors,
                        f"{cid}: {stage} label {label!r} resolves to {path.name}",
                    )


def validate_local_bindings(trace: dict, labels: dict[str, Path], errors: list[str]) -> None:
    narrative_stages = ("experiment", "results", "discussion", "conclusion")
    for item in trace.get("claims", []):
        cid = item["id"]
        sections = item.get("sections", {})
        for stage in narrative_stages:
            for label in sections.get(stage, []):
                path = labels.get(label)
                if path is None:
                    continue
                section_text = section_text_for_label(path, label)
                if cid not in claim_ids_in_text(section_text):
                    fail(
                        errors,
                        f"{cid}: {stage} section {label!r} lacks local claim binding",
                    )


def validate_surface_closure(trace: dict, errors: list[str]) -> None:
    mapped = {item["id"]: item for item in trace.get("claims", [])}
    surface_files = {
        "results": CHAPTERS / "05_results.tex",
        "discussion": CHAPTERS / "06_discussion.tex",
        "conclusion": CHAPTERS / "07_conclusion.tex",
    }
    for stage, path in surface_files.items():
        text = path.read_text(encoding="utf-8")
        for cid in mapped:
            if cid not in text:
                fail(errors, f"{cid}: absent from {stage} narrative surface")


def main() -> None:
    claims = load(CLAIMS_PATH)
    trace = load(TRACE_PATH)
    labels = chapter_label_index()

    schema_errors: list[str] = []
    alignment_errors: list[str] = []
    section_errors: list[str] = []
    local_binding_errors: list[str] = []
    closure_errors: list[str] = []

    validate_schema(trace, schema_errors)
    validate_contract_alignment(claims, trace, alignment_errors)
    validate_sections(trace, labels, section_errors)
    validate_local_bindings(trace, labels, local_binding_errors)
    validate_surface_closure(trace, closure_errors)

    checks = (
        ("THESIS_CLAIM_TRACEABILITY_SCHEMA", schema_errors),
        ("THESIS_CLAIM_TRACEABILITY_STATUS", alignment_errors),
        ("THESIS_CLAIM_TRACEABILITY_SECTIONS", section_errors),
        ("THESIS_CLAIM_LOCAL_BINDINGS", local_binding_errors),
        ("THESIS_CLAIM_SURFACE_CLOSURE", closure_errors),
    )

    failed = False
    for gate, errors in checks:
        if errors:
            failed = True
            print(f"{gate}=FAIL")
            for error in errors:
                print(f"THESIS_TRACEABILITY_ERROR={error}")
        else:
            print(f"{gate}=PASS")

    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
