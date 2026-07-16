"""Stage 3B SI-MA1 confirmatory-execution orchestration primitives."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final, Literal, cast

from torch2pc_thesis.stage3b_si_ma1 import (
    CONTRACT_ID,
    IMPLEMENTATION_SCHEMA_ID,
    PREREGISTRATION_COMMIT,
)

CONFIRMATORY_SCHEMA_ID: Final[str] = (
    "stage3b-si-ma1-confirmatory-execution-v1"
)
IMPLEMENTATION_TAG: Final[str] = "stage3b-si-ma1-implementation-v1"
IMPLEMENTATION_COMMIT: Final[str] = (
    "f14a7cb640ee96a292ad5c664ae60c036df7e62f"
)
EXPECTED_MODEL_SEEDS: Final[tuple[int, ...]] = tuple(range(10))
EXPECTED_VALIDATION_BATCHES: Final[int] = 3
EXPECTED_MEASURED_STEPS_PER_ARM_BLOCK: Final[int] = 50
DEFAULT_REPO_OUTPUT_ROOT: Final[Path] = Path(
    "results/stage-3/si-ma1/working/confirmatory"
)
MANDATORY_ATTEMPT_FILES: Final[tuple[str, ...]] = (
    "si_ma1_contract.json",
    "si_ma1_attempts.jsonl",
    "si_ma1_environment.json",
    "si_ma1_arm_timing_records.csv",
    "si_ma1_region_timing_records.csv",
    "si_ma1_numerical_comparisons.csv",
    "si_ma1_topology_comparisons.csv",
    "si_ma1_block_summaries.csv",
    "si_ma1_seed_summaries.csv",
    "si_ma1_order_seed_values.csv",
    "si_ma1_summary.json",
    "si_ma1_decision.json",
    "SHA256SUMS",
)

AttemptStatus = Literal[
    "started",
    "passed",
    "failed_infrastructure",
    "failed_scientific_cell",
    "failed_unclassified",
]


class SIMA1ConfirmatoryError(RuntimeError):
    """Raised when confirmatory orchestration violates a frozen invariant."""


@dataclass(frozen=True)
class CheckpointInventoryEntry:
    """One frozen Strict checkpoint selected for a model seed."""

    model_seed: int
    checkpoint: str
    checkpoint_sha256: str
    dataset: str
    architecture: str
    method: str
    eta: float
    inference_steps: int

    def to_record(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LedgerEvent:
    """One append-only attempt lifecycle event."""

    event_id: str
    timestamp_utc: str
    schema_id: str
    attempt_id: str
    model_seed: int
    status: AttemptStatus
    checkpoint: str
    checkpoint_sha256: str
    archive_path: str
    source_git_commit: str | None
    image_revision: str | None
    replacement_of: str | None
    replacement_reason: str | None
    failure_detail: str | None

    def to_record(self) -> dict[str, Any]:
        return asdict(self)


def utc_now() -> str:
    """Return a stable UTC timestamp for ledger events."""

    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    """Hash one file using streaming reads."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_digest(value: Any) -> str:
    """Hash a JSON-serializable value canonically."""

    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_repo_relative_results_path(path: Path) -> None:
    """Require a safe repository-relative path rooted in results/."""

    if path.is_absolute() or ".." in path.parts:
        raise SIMA1ConfirmatoryError(
            "checkpoint path must be repository-relative"
        )
    if not path.parts or path.parts[0] != "results":
        raise SIMA1ConfirmatoryError(
            "checkpoint path must be rooted in results/"
        )


def validate_attempt_id(attempt_id: str) -> None:
    """Require a path-safe immutable attempt identifier."""

    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", attempt_id):
        raise SIMA1ConfirmatoryError(
            "attempt id must be a path-safe 1..128 character token"
        )


def inventory_source_commit(path: Path) -> str:
    """Read the source commit sealed into an inventory."""

    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SIMA1ConfirmatoryError("inventory must be a JSON object")
    commit = str(value.get("source_commit_at_inventory_creation", ""))
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise SIMA1ConfirmatoryError(
            "inventory source commit is missing or invalid"
        )
    return commit


def verify_implementation_ancestry(repo: Path, *, head: str) -> None:
    """Verify the frozen implementation tag and ancestry."""

    implementation_commit = subprocess.check_output(
        ["git", "rev-list", "-n", "1", IMPLEMENTATION_TAG],
        cwd=repo,
        text=True,
        stderr=subprocess.STDOUT,
    ).strip()
    if implementation_commit != IMPLEMENTATION_COMMIT:
        raise SIMA1ConfirmatoryError(
            "SI-MA1 implementation tag target differs"
        )
    ancestry = subprocess.run(
        [
            "git",
            "merge-base",
            "--is-ancestor",
            implementation_commit,
            head,
        ],
        cwd=repo,
        check=False,
    )
    if ancestry.returncode != 0:
        raise SIMA1ConfirmatoryError(
            "SI-MA1 implementation tag is not an ancestor of HEAD"
        )


def build_inventory_payload(
    entries: Sequence[CheckpointInventoryEntry],
    *,
    source_commit: str,
) -> dict[str, Any]:
    """Build a deterministic ten-seed inventory payload."""

    if not re.fullmatch(r"[0-9a-f]{40}", source_commit):
        raise SIMA1ConfirmatoryError("inventory source commit is invalid")
    ordered = sorted(entries, key=lambda entry: entry.model_seed)
    seeds = tuple(entry.model_seed for entry in ordered)
    if seeds != EXPECTED_MODEL_SEEDS:
        raise SIMA1ConfirmatoryError(
            f"checkpoint inventory seeds differ: {seeds}"
        )
    serialized = [entry.to_record() for entry in ordered]
    return {
        "schema_id": CONFIRMATORY_SCHEMA_ID,
        "contract_id": CONTRACT_ID,
        "implementation_schema_id": IMPLEMENTATION_SCHEMA_ID,
        "implementation_tag": IMPLEMENTATION_TAG,
        "implementation_commit": IMPLEMENTATION_COMMIT,
        "preregistration_commit": PREREGISTRATION_COMMIT,
        "source_commit_at_inventory_creation": source_commit,
        "expected_model_seeds": list(EXPECTED_MODEL_SEEDS),
        "entries": serialized,
        "entries_sha256": canonical_json_digest(serialized),
    }


def write_inventory(path: Path, payload: Mapping[str, Any]) -> None:
    """Write an inventory with LF-only deterministic JSON."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            dict(payload),
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


def load_inventory(
    path: Path,
    *,
    repo: Path,
    verify_files: bool = True,
) -> tuple[CheckpointInventoryEntry, ...]:
    """Load and fully validate the frozen checkpoint inventory."""

    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise SIMA1ConfirmatoryError("inventory must be a JSON object")
    expected_metadata = {
        "schema_id": CONFIRMATORY_SCHEMA_ID,
        "contract_id": CONTRACT_ID,
        "implementation_schema_id": IMPLEMENTATION_SCHEMA_ID,
        "implementation_tag": IMPLEMENTATION_TAG,
        "implementation_commit": IMPLEMENTATION_COMMIT,
        "preregistration_commit": PREREGISTRATION_COMMIT,
        "expected_model_seeds": list(EXPECTED_MODEL_SEEDS),
    }
    observed = {key: raw.get(key) for key in expected_metadata}
    if observed != expected_metadata:
        raise SIMA1ConfirmatoryError("inventory metadata mismatch")
    raw_entries = raw.get("entries")
    if not isinstance(raw_entries, list):
        raise SIMA1ConfirmatoryError("inventory entries are missing")
    if raw.get("entries_sha256") != canonical_json_digest(raw_entries):
        raise SIMA1ConfirmatoryError("inventory entries digest mismatch")

    entries: list[CheckpointInventoryEntry] = []
    for value in raw_entries:
        if not isinstance(value, dict):
            raise SIMA1ConfirmatoryError(
                "inventory entry must be an object"
            )
        entry = CheckpointInventoryEntry(
            model_seed=int(value["model_seed"]),
            checkpoint=str(value["checkpoint"]),
            checkpoint_sha256=str(value["checkpoint_sha256"]),
            dataset=str(value["dataset"]),
            architecture=str(value["architecture"]),
            method=str(value["method"]),
            eta=float(value["eta"]),
            inference_steps=int(value["inference_steps"]),
        )
        validate_repo_relative_results_path(Path(entry.checkpoint))
        if not re.fullmatch(r"[0-9a-f]{64}", entry.checkpoint_sha256):
            raise SIMA1ConfirmatoryError(
                "checkpoint SHA256 must be lowercase hexadecimal"
            )
        if entry.dataset.lower() != "fashionmnist":
            raise SIMA1ConfirmatoryError("inventory dataset mismatch")
        if entry.architecture != "lenet_classic":
            raise SIMA1ConfirmatoryError("inventory architecture mismatch")
        if entry.method.lower() != "strict":
            raise SIMA1ConfirmatoryError("inventory method mismatch")
        if entry.eta != 0.05 or entry.inference_steps != 20:
            raise SIMA1ConfirmatoryError(
                "inventory inference configuration mismatch"
            )
        if verify_files:
            checkpoint = repo / entry.checkpoint
            if not checkpoint.is_file():
                raise SIMA1ConfirmatoryError(
                    f"checkpoint is missing: {entry.checkpoint}"
                )
            if sha256_file(checkpoint) != entry.checkpoint_sha256:
                raise SIMA1ConfirmatoryError(
                    f"checkpoint checksum mismatch: {entry.checkpoint}"
                )
        entries.append(entry)

    ordered = tuple(sorted(entries, key=lambda item: item.model_seed))
    if tuple(entry.model_seed for entry in ordered) != EXPECTED_MODEL_SEEDS:
        raise SIMA1ConfirmatoryError(
            "inventory must contain exactly one entry for every seed 0..9"
        )
    return ordered


def inventory_by_seed(
    entries: Sequence[CheckpointInventoryEntry],
) -> dict[int, CheckpointInventoryEntry]:
    """Index a validated inventory by model seed."""

    result = {entry.model_seed: entry for entry in entries}
    if tuple(sorted(result)) != EXPECTED_MODEL_SEEDS:
        raise SIMA1ConfirmatoryError("inventory seed index is incomplete")
    return result


def append_ledger_event(path: Path, event: LedgerEvent) -> None:
    """Append one immutable JSONL ledger event and fsync it."""

    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (
        json.dumps(
            event.to_record(),
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
    descriptor = os.open(
        path,
        os.O_APPEND | os.O_CREAT | os.O_WRONLY,
        0o644,
    )
    try:
        os.write(descriptor, payload)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def read_ledger(path: Path) -> tuple[LedgerEvent, ...]:
    """Read all append-only ledger events."""

    if not path.is_file():
        return ()
    events: list[LedgerEvent] = []
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        if not raw_line:
            continue
        value = json.loads(raw_line)
        if not isinstance(value, dict):
            raise SIMA1ConfirmatoryError(
                f"ledger line {line_number} is not an object"
            )
        events.append(
            LedgerEvent(
                event_id=str(value["event_id"]),
                timestamp_utc=str(value["timestamp_utc"]),
                schema_id=str(value["schema_id"]),
                attempt_id=str(value["attempt_id"]),
                model_seed=int(value["model_seed"]),
                status=cast(AttemptStatus, str(value["status"])),
                checkpoint=str(value["checkpoint"]),
                checkpoint_sha256=str(value["checkpoint_sha256"]),
                archive_path=str(value["archive_path"]),
                source_git_commit=(
                    None
                    if value.get("source_git_commit") is None
                    else str(value["source_git_commit"])
                ),
                image_revision=(
                    None
                    if value.get("image_revision") is None
                    else str(value["image_revision"])
                ),
                replacement_of=(
                    None
                    if value.get("replacement_of") is None
                    else str(value["replacement_of"])
                ),
                replacement_reason=(
                    None
                    if value.get("replacement_reason") is None
                    else str(value["replacement_reason"])
                ),
                failure_detail=(
                    None
                    if value.get("failure_detail") is None
                    else str(value["failure_detail"])
                ),
            )
        )
    event_ids = [event.event_id for event in events]
    if len(event_ids) != len(set(event_ids)):
        raise SIMA1ConfirmatoryError("ledger event ids are not unique")
    return tuple(events)


def latest_events_by_attempt(
    events: Iterable[LedgerEvent],
) -> dict[str, LedgerEvent]:
    """Return the latest appended event for each attempt id."""

    latest: dict[str, LedgerEvent] = {}
    for event in events:
        if event.schema_id != CONFIRMATORY_SCHEMA_ID:
            raise SIMA1ConfirmatoryError("ledger schema mismatch")
        latest[event.attempt_id] = event
    return latest


def passed_attempts_by_seed(
    events: Iterable[LedgerEvent],
) -> dict[int, LedgerEvent]:
    """Require at most one terminal passed attempt per seed."""

    grouped: dict[int, list[LedgerEvent]] = defaultdict(list)
    for event in latest_events_by_attempt(events).values():
        if event.status == "passed":
            grouped[event.model_seed].append(event)
    result: dict[int, LedgerEvent] = {}
    for seed, values in grouped.items():
        if len(values) != 1:
            raise SIMA1ConfirmatoryError(
                f"seed {seed} has multiple passed attempts"
            )
        result[seed] = values[0]
    return result


def validate_mark_infrastructure_failure(
    events: Sequence[LedgerEvent],
    *,
    attempt_id: str,
) -> LedgerEvent:
    """Require an unresolved started attempt before manual failure marking."""

    validate_attempt_id(attempt_id)
    latest = latest_events_by_attempt(events)
    event = latest.get(attempt_id)
    if event is None:
        raise SIMA1ConfirmatoryError(
            "attempt to mark is absent from the ledger"
        )
    if event.status != "started":
        raise SIMA1ConfirmatoryError(
            "only a latest started attempt may be marked as infrastructure failure"
        )
    return event


def validate_replacement_request(
    events: Sequence[LedgerEvent],
    *,
    model_seed: int,
    replacement_of: str | None,
    replacement_reason: str | None,
) -> None:
    """Permit replacement only for a retained infrastructure failure."""

    if (replacement_of is None) != (replacement_reason is None):
        raise SIMA1ConfirmatoryError(
            "replacement id and reason must be supplied together"
        )
    passed = passed_attempts_by_seed(events)
    if model_seed in passed:
        raise SIMA1ConfirmatoryError(
            f"seed {model_seed} already has a passed attempt"
        )
    if replacement_of is None:
        return
    if replacement_reason != "infrastructure_failure":
        raise SIMA1ConfirmatoryError(
            "only infrastructure_failure is a valid replacement reason"
        )
    latest = latest_events_by_attempt(events)
    original = latest.get(replacement_of)
    if original is None:
        raise SIMA1ConfirmatoryError(
            "replacement target is absent from the ledger"
        )
    if original.model_seed != model_seed:
        raise SIMA1ConfirmatoryError(
            "replacement target belongs to another model seed"
        )
    if original.status != "failed_infrastructure":
        raise SIMA1ConfirmatoryError(
            "only a failed_infrastructure attempt may be replaced"
        )


def verify_sha256_manifest(root: Path) -> int:
    """Verify one attempt manifest without invoking a shell."""

    manifest = root / "SHA256SUMS"
    if not manifest.is_file():
        raise SIMA1ConfirmatoryError("attempt SHA256SUMS is missing")
    count = 0
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        expected, separator, name = line.partition("  ")
        if separator != "  " or len(expected) != 64:
            raise SIMA1ConfirmatoryError("invalid SHA256SUMS line")
        target = root / name
        if not target.is_file() or sha256_file(target) != expected:
            raise SIMA1ConfirmatoryError(
                f"attempt checksum mismatch: {target}"
            )
        count += 1
    return count


def classify_failed_attempt(output_dir: Path) -> AttemptStatus:
    """Classify a failed process conservatively from retained evidence."""

    summary_path = output_dir / "si_ma1_summary.json"
    if not summary_path.is_file():
        return "failed_infrastructure"
    try:
        value = json.loads(summary_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return "failed_infrastructure"
    if not isinstance(value, dict):
        return "failed_infrastructure"
    gates = value.get("gates")
    if not isinstance(gates, dict):
        return "failed_infrastructure"
    cell_keys = (
        "prerequisites_verified",
        "NUM-MA1-cell",
        "TOPO-MA1-cell",
        "BAL-MA1-cell",
        "CMP-MA1-cell",
    )
    if any(gates.get(key) is False for key in cell_keys):
        return "failed_scientific_cell"
    return "failed_unclassified"


def validate_attempt_evidence(
    root: Path,
    *,
    inventory_entry: CheckpointInventoryEntry,
) -> dict[str, Any]:
    """Validate one archived confirmatory attempt without aggregating it."""

    missing = [
        name
        for name in MANDATORY_ATTEMPT_FILES
        if not (root / name).is_file()
    ]
    if missing:
        raise SIMA1ConfirmatoryError(
            f"attempt files are missing: {missing}"
        )
    verify_sha256_manifest(root)
    summary = json.loads(
        (root / "si_ma1_summary.json").read_text(encoding="utf-8")
    )
    decision = json.loads(
        (root / "si_ma1_decision.json").read_text(encoding="utf-8")
    )
    environment = json.loads(
        (root / "si_ma1_environment.json").read_text(encoding="utf-8")
    )
    if not all(
        isinstance(value, dict)
        for value in (summary, decision, environment)
    ):
        raise SIMA1ConfirmatoryError(
            "attempt summary, decision, and environment must be objects"
        )
    if summary.get("contract_id") != CONTRACT_ID:
        raise SIMA1ConfirmatoryError("attempt contract mismatch")
    if summary.get("implementation_schema_id") != IMPLEMENTATION_SCHEMA_ID:
        raise SIMA1ConfirmatoryError("attempt implementation schema mismatch")
    if summary.get("scope") != "confirmatory":
        raise SIMA1ConfirmatoryError("attempt is not confirmatory")
    if summary.get("lane") != "rocm":
        raise SIMA1ConfirmatoryError("attempt lane is not ROCm")
    if summary.get("model_seed") != inventory_entry.model_seed:
        raise SIMA1ConfirmatoryError("attempt model seed mismatch")
    if summary.get("checkpoint_sha256") != inventory_entry.checkpoint_sha256:
        raise SIMA1ConfirmatoryError("attempt checkpoint checksum mismatch")
    gates = summary.get("gates")
    if not isinstance(gates, dict):
        raise SIMA1ConfirmatoryError("attempt gates are missing")
    for key in (
        "prerequisites_verified",
        "NUM-MA1-cell",
        "TOPO-MA1-cell",
        "BAL-MA1-cell",
        "CMP-MA1-cell",
    ):
        if gates.get(key) is not True:
            raise SIMA1ConfirmatoryError(
                f"attempt cell gate did not pass: {key}"
            )
    if gates.get("CAL-COST-MA1") is not None:
        raise SIMA1ConfirmatoryError(
            "attempt made an unauthorized cohort cost decision"
        )
    for value in (summary, decision):
        if value.get("confirmatory_decision_made") is not False:
            raise SIMA1ConfirmatoryError(
                "attempt made an unauthorized global decision"
            )
        if value.get("si_ma1_passed") is not None:
            raise SIMA1ConfirmatoryError(
                "attempt populated an unauthorized global result"
            )
    if environment.get("ecz_evaluator_executed") is not False:
        raise SIMA1ConfirmatoryError(
            "attempt unexpectedly executed the ECZ evaluator"
        )
    source_commit = str(summary.get("source_git_commit", ""))
    image_revision = str(summary.get("image_revision", ""))
    if source_commit != image_revision or len(source_commit) != 40:
        raise SIMA1ConfirmatoryError(
            "attempt source/image provenance mismatch"
        )
    if summary.get("si_ma1_prereg_commit") != PREREGISTRATION_COMMIT:
        raise SIMA1ConfirmatoryError(
            "attempt preregistration provenance mismatch"
        )
    return cast(dict[str, Any], summary)


def validate_complete_cohort(
    *,
    archive_root: Path,
    inventory: Sequence[CheckpointInventoryEntry],
    events: Sequence[LedgerEvent],
) -> dict[str, Any]:
    """Validate complete execution evidence without computing the bootstrap."""

    selected = passed_attempts_by_seed(events)
    if tuple(sorted(selected)) != EXPECTED_MODEL_SEEDS:
        missing = sorted(set(EXPECTED_MODEL_SEEDS) - set(selected))
        raise SIMA1ConfirmatoryError(
            f"confirmatory cohort is incomplete; missing seeds: {missing}"
        )
    by_seed = inventory_by_seed(inventory)
    provenance: set[tuple[str, str, str]] = set()
    attempt_records: list[dict[str, Any]] = []
    for seed in EXPECTED_MODEL_SEEDS:
        event = selected[seed]
        attempt_root = archive_root / event.archive_path
        summary = validate_attempt_evidence(
            attempt_root,
            inventory_entry=by_seed[seed],
        )
        provenance.add(
            (
                str(summary["source_git_commit"]),
                str(summary["image_revision"]),
                str(summary["experiment_image"]),
            )
        )
        seed_summary = summary.get("seed_summary")
        if not isinstance(seed_summary, dict):
            raise SIMA1ConfirmatoryError(
                "attempt seed summary is missing"
            )
        attempt_records.append(
            {
                "model_seed": seed,
                "attempt_id": event.attempt_id,
                "archive_path": event.archive_path,
                "checkpoint_sha256": by_seed[seed].checkpoint_sha256,
                "d_seed": seed_summary["d_seed"],
            }
        )
    if len(provenance) != 1:
        raise SIMA1ConfirmatoryError(
            "confirmatory attempts do not share one source/image provenance"
        )
    source_commit, image_revision, image = next(iter(provenance))
    return {
        "schema_id": CONFIRMATORY_SCHEMA_ID,
        "contract_id": CONTRACT_ID,
        "cohort_complete": True,
        "model_seed_count": len(attempt_records),
        "source_git_commit": source_commit,
        "image_revision": image_revision,
        "experiment_image": image,
        "attempts": attempt_records,
        "confirmatory_decision_made": False,
        "CAL-COST-MA1": None,
        "si_ma1_passed": None,
        "aggregation_required": True,
    }


def build_container_runner_command(
    *,
    checkpoint: str,
    model_seed: int,
    output_dir: Path,
    attempt_id: str,
    replacement_of: str | None,
    replacement_reason: str | None,
) -> list[str]:
    """Build the frozen one-seed controlled runner command."""

    validate_attempt_id(attempt_id)
    command = [
        os.fspath(Path(sys.executable)),
        "scripts/run_stage3b_si_ma1_container.py",
        "gpu",
        "--execution-scope",
        "confirmatory",
        "--checkpoint",
        checkpoint,
        "--model-seed",
        str(model_seed),
        "--max-batches",
        str(EXPECTED_VALIDATION_BATCHES),
        "--output-dir",
        os.fspath(output_dir),
        "--attempt-id",
        attempt_id,
    ]
    if replacement_of is not None:
        command.extend(
            [
                "--replacement-of",
                replacement_of,
                "--replacement-reason",
                cast(str, replacement_reason),
            ]
        )
    return command


def ensure_external_archive(repo: Path, archive_root: Path) -> None:
    """Require an absolute archive outside the repository tree."""

    if not archive_root.is_absolute():
        raise SIMA1ConfirmatoryError("archive root must be absolute")
    repo_resolved = repo.resolve()
    archive_resolved = archive_root.resolve()
    if archive_resolved == repo_resolved or repo_resolved in archive_resolved.parents:
        raise SIMA1ConfirmatoryError(
            "archive root must be outside the repository"
        )
    archive_root.mkdir(parents=True, exist_ok=True)


def archive_attempt(
    repo_output: Path,
    archive_output: Path,
) -> None:
    """Move one attempt out of the repository before the next seed."""

    if not repo_output.exists():
        raise SIMA1ConfirmatoryError(
            "repository attempt output is missing"
        )
    if archive_output.exists():
        raise SIMA1ConfirmatoryError(
            "archive attempt destination already exists"
        )
    archive_output.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(os.fspath(repo_output), os.fspath(archive_output))


def new_ledger_event(
    *,
    attempt_id: str,
    model_seed: int,
    status: AttemptStatus,
    inventory_entry: CheckpointInventoryEntry,
    archive_path: Path,
    source_git_commit: str | None = None,
    image_revision: str | None = None,
    replacement_of: str | None = None,
    replacement_reason: str | None = None,
    failure_detail: str | None = None,
) -> LedgerEvent:
    """Create one append-only ledger event."""

    validate_attempt_id(attempt_id)
    return LedgerEvent(
        event_id=uuid.uuid4().hex,
        timestamp_utc=utc_now(),
        schema_id=CONFIRMATORY_SCHEMA_ID,
        attempt_id=attempt_id,
        model_seed=model_seed,
        status=status,
        checkpoint=inventory_entry.checkpoint,
        checkpoint_sha256=inventory_entry.checkpoint_sha256,
        archive_path=archive_path.as_posix(),
        source_git_commit=source_git_commit,
        image_revision=image_revision,
        replacement_of=replacement_of,
        replacement_reason=replacement_reason,
        failure_detail=failure_detail,
    )


def run_process(
    command: Sequence[str],
    *,
    cwd: Path,
) -> None:
    """Run one isolated controlled attempt."""

    subprocess.run(list(command), cwd=cwd, check=True)


def materialize_archive(
    *,
    repo: Path,
    archive_root: Path,
    destination_root: Path,
    inventory_path: Path,
    ledger_path: Path,
    cohort_summary: Mapping[str, Any],
) -> None:
    """Copy complete retained execution evidence back into results/."""

    if destination_root.is_absolute() or ".." in destination_root.parts:
        raise SIMA1ConfirmatoryError(
            "materialization destination must be repository-relative"
        )
    expected_prefix = DEFAULT_REPO_OUTPUT_ROOT.parts
    if tuple(destination_root.parts[: len(expected_prefix)]) != expected_prefix:
        raise SIMA1ConfirmatoryError(
            "materialization destination must use the SI-MA1 confirmatory root"
        )
    destination = repo / destination_root
    if destination.exists() and any(destination.iterdir()):
        raise SIMA1ConfirmatoryError(
            "materialization destination must be new and empty"
        )
    destination.mkdir(parents=True, exist_ok=True)

    attempts_root = archive_root / "attempts"
    if not attempts_root.is_dir():
        raise SIMA1ConfirmatoryError("archive attempts directory is missing")
    for seed_dir in sorted(attempts_root.iterdir()):
        if not seed_dir.is_dir():
            continue
        target_seed = destination / seed_dir.name
        shutil.copytree(seed_dir, target_seed)

    shutil.copy2(inventory_path, destination / "checkpoint_inventory.json")
    shutil.copy2(ledger_path, destination / "attempt_ledger.jsonl")
    (destination / "cohort_execution_summary.json").write_text(
        json.dumps(
            dict(cohort_summary),
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
