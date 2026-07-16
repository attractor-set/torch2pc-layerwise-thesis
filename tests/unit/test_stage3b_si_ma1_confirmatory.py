from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.build_stage3b_si_ma1_checkpoint_inventory import (
    resolve_source_commit,
)
from torch2pc_thesis.stage3b_si_ma1_confirmatory import (
    CONFIRMATORY_SCHEMA_ID,
    EXPECTED_MODEL_SEEDS,
    IMPLEMENTATION_COMMIT,
    CheckpointInventoryEntry,
    SIMA1ConfirmatoryError,
    append_ledger_event,
    build_container_runner_command,
    build_inventory_payload,
    canonical_json_digest,
    classify_failed_attempt,
    load_inventory,
    new_ledger_event,
    passed_attempts_by_seed,
    read_ledger,
    validate_mark_infrastructure_failure,
    validate_replacement_request,
    validate_repo_relative_results_path,
    write_inventory,
)


def entry(seed: int, *, checksum: str = "a" * 64) -> CheckpointInventoryEntry:
    return CheckpointInventoryEntry(
        model_seed=seed,
        checkpoint=f"results/checkpoints/strict-seed-{seed}.pt",
        checkpoint_sha256=checksum,
        dataset="FashionMNIST",
        architecture="lenet_classic",
        method="Strict",
        eta=0.05,
        inference_steps=20,
    )


def test_inventory_payload_has_exact_ten_seed_matrix() -> None:
    payload = build_inventory_payload(
        [entry(seed) for seed in EXPECTED_MODEL_SEEDS],
        source_commit="1" * 40,
    )
    assert payload["schema_id"] == CONFIRMATORY_SCHEMA_ID
    assert payload["expected_model_seeds"] == list(EXPECTED_MODEL_SEEDS)
    assert payload["entries_sha256"] == canonical_json_digest(
        payload["entries"]
    )


def test_inventory_payload_rejects_missing_seed() -> None:
    with pytest.raises(SIMA1ConfirmatoryError, match="seeds differ"):
        build_inventory_payload(
            [entry(seed) for seed in range(9)],
            source_commit="1" * 40,
        )


def test_load_inventory_verifies_files_and_hashes(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    checkpoint_root = repo / "results/checkpoints"
    checkpoint_root.mkdir(parents=True)
    entries = []
    for seed in EXPECTED_MODEL_SEEDS:
        path = checkpoint_root / f"strict-seed-{seed}.pt"
        path.write_bytes(f"seed-{seed}".encode())
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        entries.append(entry(seed, checksum=digest))
    payload = build_inventory_payload(entries, source_commit="1" * 40)
    inventory_path = tmp_path / "inventory.json"
    write_inventory(inventory_path, payload)

    loaded = load_inventory(inventory_path, repo=repo)

    assert [value.model_seed for value in loaded] == list(
        EXPECTED_MODEL_SEEDS
    )


@pytest.mark.parametrize(
    "path",
    [
        Path("/tmp/checkpoint.pt"),
        Path("../results/checkpoint.pt"),
        Path("configs/checkpoint.pt"),
    ],
)
def test_repo_relative_checkpoint_path_is_restricted(path: Path) -> None:
    with pytest.raises(SIMA1ConfirmatoryError):
        validate_repo_relative_results_path(path)


def test_ledger_is_append_only_and_preserves_lifecycle(tmp_path: Path) -> None:
    ledger = tmp_path / "attempt_ledger.jsonl"
    item = entry(0)
    started = new_ledger_event(
        attempt_id="attempt-0",
        model_seed=0,
        status="started",
        inventory_entry=item,
        archive_path=Path("attempts/seed-0/attempt-0"),
    )
    passed = new_ledger_event(
        attempt_id="attempt-0",
        model_seed=0,
        status="passed",
        inventory_entry=item,
        archive_path=Path("attempts/seed-0/attempt-0"),
        source_git_commit="1" * 40,
        image_revision="1" * 40,
    )

    append_ledger_event(ledger, started)
    append_ledger_event(ledger, passed)

    events = read_ledger(ledger)
    assert [event.status for event in events] == ["started", "passed"]
    assert passed_attempts_by_seed(events)[0].attempt_id == "attempt-0"


def test_replacement_requires_retained_infrastructure_failure(
    tmp_path: Path,
) -> None:
    ledger = tmp_path / "attempt_ledger.jsonl"
    item = entry(3)
    failed = new_ledger_event(
        attempt_id="failed-3",
        model_seed=3,
        status="failed_infrastructure",
        inventory_entry=item,
        archive_path=Path("attempts/seed-3/failed-3"),
    )
    append_ledger_event(ledger, failed)
    events = read_ledger(ledger)

    validate_replacement_request(
        events,
        model_seed=3,
        replacement_of="failed-3",
        replacement_reason="infrastructure_failure",
    )

    with pytest.raises(SIMA1ConfirmatoryError):
        validate_replacement_request(
            events,
            model_seed=4,
            replacement_of="failed-3",
            replacement_reason="infrastructure_failure",
        )


def test_scientific_cell_failure_is_not_replaceable(tmp_path: Path) -> None:
    ledger = tmp_path / "attempt_ledger.jsonl"
    item = entry(2)
    failed = new_ledger_event(
        attempt_id="failed-2",
        model_seed=2,
        status="failed_scientific_cell",
        inventory_entry=item,
        archive_path=Path("attempts/seed-2/failed-2"),
    )
    append_ledger_event(ledger, failed)

    with pytest.raises(SIMA1ConfirmatoryError, match="infrastructure"):
        validate_replacement_request(
            read_ledger(ledger),
            model_seed=2,
            replacement_of="failed-2",
            replacement_reason="infrastructure_failure",
        )


def test_failure_classification_detects_scientific_cell(tmp_path: Path) -> None:
    output = tmp_path / "attempt"
    output.mkdir()
    (output / "si_ma1_summary.json").write_text(
        json.dumps(
            {
                "gates": {
                    "prerequisites_verified": True,
                    "NUM-MA1-cell": False,
                    "TOPO-MA1-cell": True,
                    "BAL-MA1-cell": True,
                    "CMP-MA1-cell": True,
                }
            }
        ),
        encoding="utf-8",
    )
    assert classify_failed_attempt(output) == "failed_scientific_cell"


def test_failure_without_summary_is_infrastructure(tmp_path: Path) -> None:
    assert classify_failed_attempt(tmp_path) == "failed_infrastructure"


def test_container_command_is_one_seed_rocm_confirmatory() -> None:
    command = build_container_runner_command(
        checkpoint="results/checkpoints/strict-seed-7.pt",
        model_seed=7,
        output_dir=Path(
            "results/stage-3/si-ma1/working/confirmatory/"
            "seed-7/attempt-7"
        ),
        attempt_id="attempt-7",
        replacement_of=None,
        replacement_reason=None,
    )
    assert command[1:4] == [
        "scripts/run_stage3b_si_ma1_container.py",
        "gpu",
        "--execution-scope",
    ]
    assert "confirmatory" in command
    assert "--max-batches" in command
    assert command[command.index("--max-batches") + 1] == "3"
    assert command[command.index("--model-seed") + 1] == "7"


def test_only_started_attempt_can_be_marked_infrastructure(
    tmp_path: Path,
) -> None:
    ledger = tmp_path / "attempt_ledger.jsonl"
    item = entry(5)
    started = new_ledger_event(
        attempt_id="started-5",
        model_seed=5,
        status="started",
        inventory_entry=item,
        archive_path=Path("attempts/seed-5/started-5"),
    )
    append_ledger_event(ledger, started)
    events = read_ledger(ledger)

    selected = validate_mark_infrastructure_failure(
        events,
        attempt_id="started-5",
    )
    assert selected.model_seed == 5

    passed = new_ledger_event(
        attempt_id="started-5",
        model_seed=5,
        status="passed",
        inventory_entry=item,
        archive_path=Path("attempts/seed-5/started-5"),
        source_git_commit="1" * 40,
        image_revision="1" * 40,
    )
    append_ledger_event(ledger, passed)
    with pytest.raises(SIMA1ConfirmatoryError, match="started"):
        validate_mark_infrastructure_failure(
            read_ledger(ledger),
            attempt_id="started-5",
        )


def test_inventory_builder_accepts_host_verified_gitless_provenance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "workspace"
    repo.mkdir()
    source_commit = "1" * 40

    monkeypatch.setenv("SOURCE_GIT_COMMIT", source_commit)
    monkeypatch.setenv("IMAGE_REVISION", source_commit)
    monkeypatch.setenv(
        "SI_MA1_IMPLEMENTATION_COMMIT",
        IMPLEMENTATION_COMMIT,
    )
    monkeypatch.setenv(
        "SI_MA1_IMPLEMENTATION_ANCESTRY_VERIFIED",
        "1",
    )

    assert resolve_source_commit(repo) == source_commit


def test_inventory_builder_rejects_gitless_image_revision_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "workspace"
    repo.mkdir()

    monkeypatch.setenv("SOURCE_GIT_COMMIT", "1" * 40)
    monkeypatch.setenv("IMAGE_REVISION", "2" * 40)
    monkeypatch.setenv(
        "SI_MA1_IMPLEMENTATION_COMMIT",
        IMPLEMENTATION_COMMIT,
    )
    monkeypatch.setenv(
        "SI_MA1_IMPLEMENTATION_ANCESTRY_VERIFIED",
        "1",
    )

    with pytest.raises(
        SIMA1ConfirmatoryError,
        match="image revision",
    ):
        resolve_source_commit(repo)


def test_inventory_builder_requires_host_ancestry_attestation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "workspace"
    repo.mkdir()
    source_commit = "1" * 40

    monkeypatch.setenv("SOURCE_GIT_COMMIT", source_commit)
    monkeypatch.setenv("IMAGE_REVISION", source_commit)
    monkeypatch.setenv(
        "SI_MA1_IMPLEMENTATION_COMMIT",
        IMPLEMENTATION_COMMIT,
    )
    monkeypatch.delenv(
        "SI_MA1_IMPLEMENTATION_ANCESTRY_VERIFIED",
        raising=False,
    )

    with pytest.raises(
        SIMA1ConfirmatoryError,
        match="ANCESTRY_VERIFIED",
    ):
        resolve_source_commit(repo)
