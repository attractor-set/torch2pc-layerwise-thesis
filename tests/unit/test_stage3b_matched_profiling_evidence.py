from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from torch2pc_thesis.stage3b_matched_release import (
    MATCHED_EXECUTION_SOURCE_COMMIT,
    MATCHED_IMAGE_DIGEST,
    MATCHED_LOCALITY_ARCHIVE_NAME,
    MATCHED_LOCALITY_COMPRESSED_SHA256,
    MATCHED_LOCALITY_MANIFEST_NAME,
    MATCHED_LOCALITY_SOURCE_NAME,
    MATCHED_LOCALITY_UNCOMPRESSED_SHA256,
    MATCHED_LOCALITY_UNCOMPRESSED_SIZE_BYTES,
    MATCHED_REPOSITORY_FILES,
    MATCHED_RESULT_ROOT,
    MATCHED_SEALED_REGISTRY_NAME,
    validate_repository_evidence,
)
from torch2pc_thesis.stage3b_matched_sealing import MATCHED_SEALED_FILES

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_ROOT = ROOT / MATCHED_RESULT_ROOT
MANIFEST_PATH = ROOT / "experiments/frozen/stage3b-matched-profiling-v2/manifest.json"
REQUEST_PATH = ROOT / "experiments/frozen/stage3b-matched-profiling-v2/request.json"


def _load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _jsonl(name: str) -> list[dict[str, object]]:
    values: list[dict[str, object]] = []
    for line in (EVIDENCE_ROOT / name).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        assert isinstance(value, dict)
        values.append(value)
    return values


def _csv_rows(name: str) -> list[dict[str, str]]:
    with (EVIDENCE_ROOT / name).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _registry(name: str) -> dict[str, str]:
    records: dict[str, str] = {}
    for line in (EVIDENCE_ROOT / name).read_text(encoding="utf-8").splitlines():
        digest, filename = line.split(maxsplit=1)
        filename = filename.removeprefix("*")
        assert filename not in records
        records[filename] = digest
    return records


def test_matched_repository_evidence_file_set_and_registry_are_exact() -> None:
    assert {path.name for path in EVIDENCE_ROOT.iterdir()} == set(
        MATCHED_REPOSITORY_FILES
    )

    repository_registry = _registry("SHA256SUMS")
    assert set(repository_registry) == set(MATCHED_REPOSITORY_FILES) - {
        "SHA256SUMS"
    }
    for name, digest in repository_registry.items():
        assert _sha(EVIDENCE_ROOT / name) == digest

    sealed_registry = _registry(MATCHED_SEALED_REGISTRY_NAME)
    assert set(sealed_registry) == set(MATCHED_SEALED_FILES)
    for name, digest in sealed_registry.items():
        if name == MATCHED_LOCALITY_SOURCE_NAME:
            assert digest == MATCHED_LOCALITY_UNCOMPRESSED_SHA256
        else:
            assert _sha(EVIDENCE_ROOT / name) == digest


def test_matched_locality_stream_is_losslessly_compressed_for_repository() -> None:
    archive = EVIDENCE_ROOT / MATCHED_LOCALITY_ARCHIVE_NAME
    manifest = _load_json(EVIDENCE_ROOT / MATCHED_LOCALITY_MANIFEST_NAME)

    assert not (EVIDENCE_ROOT / MATCHED_LOCALITY_SOURCE_NAME).exists()
    assert archive.is_file()
    assert archive.stat().st_size < 100_000_000
    assert _sha(archive) == MATCHED_LOCALITY_COMPRESSED_SHA256

    assert manifest == {
        "compressed_sha256": MATCHED_LOCALITY_COMPRESSED_SHA256,
        "compressed_size_bytes": archive.stat().st_size,
        "compression_format": "zstd",
        "compression_level": 19,
        "evidence": True,
        "long_distance_window_log": 27,
        "release_asset_name": (
            "stage3b-matched-profiling-locality-events-v1.jsonl.zst"
        ),
        "release_publication_permitted": False,
        "release_tag": "stage3b-matched-profiling-evidence-v1",
        "repository_name": MATCHED_LOCALITY_ARCHIVE_NAME,
        "results_publication_permitted": False,
        "schema_version": 1,
        "source_name": MATCHED_LOCALITY_SOURCE_NAME,
        "status": "lossless_compressed_repository_representation",
        "uncompressed_sha256": MATCHED_LOCALITY_UNCOMPRESSED_SHA256,
        "uncompressed_size_bytes": MATCHED_LOCALITY_UNCOMPRESSED_SIZE_BYTES,
    }


def test_matched_seal_is_complete_but_publication_remains_closed() -> None:
    seal = validate_repository_evidence(ROOT)
    manifest = _load_json(MANIFEST_PATH)

    assert seal["scope"] == "stage3b_b1_b2_matched_sealed_evidence_v1"
    assert seal["status"] == "sealed"
    assert seal["source_commit"] == MATCHED_EXECUTION_SOURCE_COMMIT
    assert seal["sealing_source_commit"] == MATCHED_EXECUTION_SOURCE_COMMIT
    assert seal["image_digest"] == MATCHED_IMAGE_DIGEST
    assert seal["manifest_digest"] == manifest["manifest_digest"]
    assert seal["matched_cell_count"] == 288
    assert seal["attempt_history_count"] == 288
    assert seal["cross_candidate_correctness_block_count"] == 96
    assert seal["retried_cell_count"] == 0
    assert seal["candidate_counts"] == {
        "composite_vjp": 96,
        "isolated_layer_vjp": 96,
        "stage2_baseline": 96,
    }
    assert seal["evidence"] is True
    assert seal["full_lane_complete"] is True
    assert seal["full_stage3b_campaign_complete"] is False
    assert seal["results_publication_permitted"] is False
    assert seal["test_dataset_access"] is False


def test_matched_analysis_metadata_preserves_registered_boundaries() -> None:
    metadata = _load_json(EVIDENCE_ROOT / "analysis_metadata.json")
    request = _load_json(REQUEST_PATH)

    assert metadata["independent_unit"] == "model_seed"
    assert metadata["cross_candidate_correctness"] == {
        "block_count": 96,
        "comparisons_per_block": 2,
        "required": True,
        "untimed": True,
    }
    assert metadata["observer_cost_rule"] == {
        "not_subtracted_from_primary_timing": True,
        "reported_separately": True,
    }
    assert metadata["fallback_validation"] == {
        "cost_ms": None,
        "status": "not_applicable_before_ex_if0",
    }
    assert metadata["results_publication_permitted"] is False
    assert metadata["test_dataset_access"] is False

    assert request["request_id"] == "stage3b-b1-b2-matched-profiling-request-v2"
    assert request["execution_performed"] is False
    assert request["measurements_allowed"] is False
    assert request["evidence"] is False


def test_matched_tables_have_exact_registered_coverage() -> None:
    cells = _csv_rows("profiling_cells.csv")
    repetitions = _csv_rows("profiling_repetitions.csv")
    summaries = _csv_rows("profiling_summary.csv")

    assert len(cells) == 288
    assert len({row["cell_id"] for row in cells}) == 288
    assert len({row["block_id"] for row in cells}) == 96
    assert Counter(row["candidate_id"] for row in cells) == Counter(
        {
            "stage2_baseline": 96,
            "isolated_layer_vjp": 96,
            "composite_vjp": 96,
        }
    )
    assert Counter(row["method"] for row in cells) == Counter(
        {"fixedpred": 144, "strict": 144}
    )

    assert len(repetitions) == 1440
    assert len({(row["cell_id"], row["repetition"]) for row in repetitions}) == 1440

    assert len(summaries) == 96
    assert all(int(row["model_seed_count"]) == 3 for row in summaries)


def test_matched_attempt_and_correctness_streams_are_complete() -> None:
    history = _jsonl("attempt-history.jsonl")
    correctness = _jsonl("block-correctness.jsonl")

    assert len(history) == 288
    assert len({record["cell_id"] for record in history}) == 288
    assert all(record["terminal_status"] == "matched_cell_complete" for record in history)
    assert all(record["failure_class"] is None for record in history)
    assert all(record["retry_eligible"] is False for record in history)

    assert len(correctness) == 96
    assert len({record["block_id"] for record in correctness}) == 96
    assert all(
        record["status"] == "cross_candidate_correctness_passed"
        for record in correctness
    )
    assert all(record["passed"] is True for record in correctness)
    assert all(len(record["pair_comparisons"]) == 2 for record in correctness)
    assert all(
        comparison["passed"] is True
        for record in correctness
        for comparison in record["pair_comparisons"]
    )


def test_runtime_inventory_and_environment_lock_are_bound_to_execution() -> None:
    inventory = json.loads(
        (EVIDENCE_ROOT / "runtime-inventory.json").read_text(encoding="utf-8")
    )
    environment = _load_json(EVIDENCE_ROOT / "environment-lock.json")
    seal = _load_json(EVIDENCE_ROOT / "seal.json")

    assert isinstance(inventory, list)
    assert inventory
    assert all(
        isinstance(item, dict)
        and isinstance(item.get("path"), str)
        and isinstance(item.get("size_bytes"), int)
        and isinstance(item.get("sha256"), str)
        for item in inventory
    )

    assert environment["source_commit"] == MATCHED_EXECUTION_SOURCE_COMMIT
    assert environment["sealing_source_commit"] == MATCHED_EXECUTION_SOURCE_COMMIT
    assert environment["image_digest"] == MATCHED_IMAGE_DIGEST
    assert environment["authorization_token"] == seal["authorization_token"]
    assert environment["manifest_digest"] == seal["manifest_digest"]
    assert environment["runtime_inventory_sha256"] == seal["runtime_inventory_sha256"]
    cell_environment = environment["cell_environment_sha256"]
    assert isinstance(cell_environment, dict)
    assert len(cell_environment) == 288


def test_current_documentation_records_sealed_evidence_and_closed_analysis() -> None:
    required = (
        "matched_profiling_execution_complete=true",
        "matched_profiling_runtime_validation=valid",
        "matched_profiling_evidence=sealed",
        "matched_profiling_analysis_open=false",
        "runtime_authorization=issued_consumed",
        "measurements_allowed=false",
        "results_publication_permitted=true",
        "release_draft_required=false",
        "release_publication_permitted=true",
        "release_publication_complete=true",
        "matched_profiling_analysis_publication_receipt_frozen=true",
        "ex_if0_opened=false",
        "recursive_aggregate_execution_open=false",
        "full_stage3b_campaign_complete=false",
    )
    for name in ("STATUS.md", "STATUS_EN.md", "ROADMAP.md", "ROADMAP_EN.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        for marker in required:
            assert marker in text, (name, marker)
