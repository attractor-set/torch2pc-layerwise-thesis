from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from torch2pc_thesis.stage3b_b1_equivalence import sha256_file

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_ROOT = ROOT / (
    "results/stage-3/b2/"
    "stage3b-b2-confirmatory-63885e5-v1"
)

EXPECTED_FILES = {
    "SHA256SUMS",
    "attempt-history.jsonl",
    "authorization.json",
    "decision.json",
    "direct-b1-b2-metrics.csv",
    "endpoint-metrics.csv",
    "matched-profiling-admission.json",
    "request.json",
    "resolved-config.json",
    "structural-events.jsonl",
    "trajectory-metrics.csv",
}

MATCHED_REQUEST_SHA256 = (
    "7c23c9ced5c838e7c3a2ad539d6a5839e986b79ca84ab9c16b14fecfaf819f5e"
)
MATCHED_MANIFEST_SHA256 = (
    "6950470b4188b8c85226649ec631c739eef9cb8a8ef0b3410a82fb0a5106b79d"
)


def _load_json(name: str) -> dict[str, object]:
    value = json.loads(
        (EVIDENCE_ROOT / name).read_text(encoding="utf-8")
    )
    assert isinstance(value, dict)
    return value


def _jsonl(name: str) -> list[dict[str, object]]:
    values: list[dict[str, object]] = []
    for line in (EVIDENCE_ROOT / name).read_text(
        encoding="utf-8"
    ).splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        assert isinstance(value, dict)
        values.append(value)
    return values


def _csv_rows(name: str) -> list[dict[str, str]]:
    with (EVIDENCE_ROOT / name).open(
        encoding="utf-8",
        newline="",
    ) as stream:
        return list(csv.DictReader(stream))


def test_confirmatory_b2_evidence_file_set_and_registry_are_exact() -> None:
    assert {path.name for path in EVIDENCE_ROOT.iterdir()} == EXPECTED_FILES

    registry_lines = (EVIDENCE_ROOT / "SHA256SUMS").read_text(
        encoding="utf-8"
    ).splitlines()
    assert len(registry_lines) == len(EXPECTED_FILES) - 1

    registered_names: set[str] = set()
    for line in registry_lines:
        digest, name = line.split("  ", maxsplit=1)
        assert len(digest) == 64
        assert all(character in "0123456789abcdef" for character in digest)
        assert name in EXPECTED_FILES - {"SHA256SUMS"}
        assert name not in registered_names
        assert sha256_file(EVIDENCE_ROOT / name) == digest
        registered_names.add(name)

    assert registered_names == EXPECTED_FILES - {"SHA256SUMS"}


def test_confirmatory_b2_decision_is_positive_complete_and_sealed() -> None:
    decision = _load_json("decision.json")

    assert decision["decision_id"] == "EQ-B2-CONFIRMATORY"
    assert decision["scope"] == "confirmatory"
    assert decision["confirmatory_equivalence_executed"] is True
    assert decision["status"] == "pass"
    assert decision["sealed"] is True

    assert decision["matched_triples_expected"] == 120
    assert decision["matched_triples_observed"] == 120
    assert decision["pairwise_comparisons_expected"] == 240
    assert decision["pairwise_comparisons_observed"] == 240

    assert decision["failed_pair_count"] == 0
    assert decision["failed_pairs"] == []
    assert decision["failed_triples"] == []
    assert decision["dangerous_misses"] == 0
    assert decision["dangerous_miss_limit"] == 0
    assert decision["test_dataset_access"] is False
    assert decision["results_publication_permitted"] is False

    gates = decision["gates"]
    assert isinstance(gates, dict)
    assert set(gates) == {
        "STRUCT-B2",
        "NUM-B2",
        "TRAJ-B2",
        "OBS-B2",
        "PROV-B2",
    }

    for gate in gates.values():
        assert isinstance(gate, dict)
        assert gate["passed"] is True
        assert gate["failed_triples"] == []


def test_derived_eq_b2_admission_is_bound_to_confirmatory_decision() -> None:
    decision = _load_json("decision.json")
    admission = _load_json("matched-profiling-admission.json")

    decision_sha256 = hashlib.sha256(
        (EVIDENCE_ROOT / "decision.json").read_bytes()
    ).hexdigest()

    assert admission["decision_id"] == "EQ-B2"
    assert admission["source_decision_id"] == "EQ-B2-CONFIRMATORY"
    assert admission["source_decision_path"] == "decision.json"
    assert admission["source_decision_sha256"] == decision_sha256
    assert admission["scope"] == "confirmatory"
    assert admission["status"] == "pass"
    assert admission["sealed"] is True
    assert admission["matched_triples_observed"] == 120
    assert admission["pairwise_comparisons_observed"] == 240
    assert admission["failed_pairs"] == []
    assert admission["failed_triples"] == []
    assert admission["gates"] == decision["gates"]


def test_attempt_history_and_structural_events_are_complete() -> None:
    history = _jsonl("attempt-history.jsonl")
    events = _jsonl("structural-events.jsonl")

    assert len(history) == 120
    assert len({item["triple_id"] for item in history}) == 120
    assert all(item["status"] == "completed" for item in history)
    assert all(item["evidence"] is False for item in history)
    assert all(item["test_dataset_access"] is False for item in history)

    assert len(events) == 1800
    assert len({event["triple_id"] for event in events}) == 120

    method_counts: dict[str, int] = {"FixedPred": 0, "Strict": 0}
    for event in events:
        method = str(event["method"])
        assert method in method_counts
        method_counts[method] += 1
        assert event["candidate_id"] == "composite_vjp"
        assert event["composite_vjp_call_count"] == 1

    assert method_counts == {"FixedPred": 600, "Strict": 1200}


def test_aggregated_metric_tables_are_nonempty_and_passed() -> None:
    for name in (
        "trajectory-metrics.csv",
        "endpoint-metrics.csv",
        "direct-b1-b2-metrics.csv",
    ):
        rows = _csv_rows(name)
        assert rows
        assert all(
            str(row.get("passed", "")).lower() in {"true", "1"}
            for row in rows
        )


def test_authorization_and_request_preserve_pre_seal_boundary() -> None:
    authorization = _load_json("authorization.json")
    request = _load_json("request.json")

    assert authorization["execution_mode"] == "confirmatory"
    assert authorization["authorized_triple_count"] == 120
    assert authorization["authorized_comparison_count"] == 240
    assert authorization["execution_permitted"] is True
    assert authorization["measurements_allowed"] is True
    assert authorization["evidence"] is False
    assert authorization["results_publication_permitted"] is False
    assert authorization["test_dataset_access"] is False

    assert request["scope"] == "confirmatory"
    assert request["matched_triple_count"] == 120
    assert request["pairwise_comparison_count"] == 240
    assert request["test_split_access"] is False


def test_historical_matched_profiling_freeze_remains_byte_identical() -> None:
    request = ROOT / (
        "experiments/planned/"
        "STAGE3B-B1-B2-MATCHED-PROFILING-REQUEST.json"
    )
    manifest = ROOT / (
        "experiments/planned/"
        "STAGE3B-B1-B2-MATCHED-PROFILING-MANIFEST.json"
    )

    assert sha256_file(request) == MATCHED_REQUEST_SHA256
    assert sha256_file(manifest) == MATCHED_MANIFEST_SHA256


def test_documentation_keeps_matched_profiling_execution_closed() -> None:
    for name in ("STATUS.md", "STATUS_EN.md", "ROADMAP.md", "ROADMAP_EN.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "scientific_admission=open_after_eq_b2_confirmatory" in text
        assert "b2_confirmatory_admission=present" in text
        assert "matched_profiling_request_refresh_required=true" in text
        assert "matched_profiling_execution_open=false" in text
        assert "runtime_authorization=not_issued" in text
        assert "measurements_allowed=false" in text
