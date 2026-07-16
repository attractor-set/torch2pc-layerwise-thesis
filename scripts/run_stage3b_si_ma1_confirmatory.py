#!/usr/bin/env python3
"""Run and retain the SI-MA1 confirmatory cohort without aggregation."""

from __future__ import annotations

import argparse
import json
import subprocess
import uuid
from pathlib import Path
from typing import Any

from torch2pc_thesis.stage3b_si_ma1_confirmatory import (
    DEFAULT_REPO_OUTPUT_ROOT,
    EXPECTED_MODEL_SEEDS,
    CheckpointInventoryEntry,
    LedgerEvent,
    SIMA1ConfirmatoryError,
    append_ledger_event,
    archive_attempt,
    build_container_runner_command,
    classify_failed_attempt,
    ensure_external_archive,
    inventory_by_seed,
    inventory_source_commit,
    load_inventory,
    materialize_archive,
    new_ledger_event,
    passed_attempts_by_seed,
    read_ledger,
    run_process,
    validate_attempt_evidence,
    validate_complete_cohort,
    validate_mark_infrastructure_failure,
    validate_replacement_request,
    verify_implementation_ancestry,
)


def parse_seed_list(raw: str) -> tuple[int, ...]:
    values = tuple(int(value) for value in raw.split(",") if value.strip())
    if not values:
        raise argparse.ArgumentTypeError("seed list must not be empty")
    if len(values) != len(set(values)):
        raise argparse.ArgumentTypeError("seed list contains duplicates")
    if any(value not in EXPECTED_MODEL_SEEDS for value in values):
        raise argparse.ArgumentTypeError("seeds must be in 0..9")
    return values


def common_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--archive-root", type=Path, required=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_seed = subparsers.add_parser("run-seed")
    common_parser(run_seed)
    run_seed.add_argument("--seed", type=int, required=True)
    run_seed.add_argument("--attempt-id")
    run_seed.add_argument("--replacement-of")
    run_seed.add_argument(
        "--replacement-reason",
        choices=["infrastructure_failure"],
    )

    run_cohort = subparsers.add_parser("run-cohort")
    common_parser(run_cohort)
    run_cohort.add_argument(
        "--seeds",
        type=parse_seed_list,
        default=EXPECTED_MODEL_SEEDS,
    )

    mark_failed = subparsers.add_parser(
        "mark-infrastructure-failure"
    )
    common_parser(mark_failed)
    mark_failed.add_argument("--attempt-id", required=True)
    mark_failed.add_argument("--detail", required=True)

    status = subparsers.add_parser("status")
    common_parser(status)

    materialize = subparsers.add_parser("materialize")
    common_parser(materialize)
    materialize.add_argument(
        "--destination-root",
        type=Path,
        default=DEFAULT_REPO_OUTPUT_ROOT,
    )
    return parser.parse_args()


def git_output(repo: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", *args],
        cwd=repo,
        text=True,
        stderr=subprocess.STDOUT,
    ).strip()


def ensure_clean_tree(repo: Path) -> None:
    if git_output(repo, "status", "--porcelain"):
        raise SIMA1ConfirmatoryError(
            "confirmatory execution requires a clean repository tree"
        )


def resolve_path(path: Path, *, repo: Path) -> Path:
    return path if path.is_absolute() else repo / path


def archive_relative_path(seed: int, attempt_id: str) -> Path:
    return Path("attempts") / f"seed-{seed}" / attempt_id


def seed_repo_output(seed: int, attempt_id: str) -> Path:
    return (
        DEFAULT_REPO_OUTPUT_ROOT
        / f"seed-{seed}"
        / attempt_id
    )


def seal_inventory(
    *,
    archive_root: Path,
    inventory_path: Path,
) -> Path:
    target = archive_root / "checkpoint_inventory.json"
    if target.is_file():
        if target.read_bytes() != inventory_path.read_bytes():
            raise SIMA1ConfirmatoryError(
                "archive inventory differs from requested inventory"
            )
        return target
    target.write_bytes(inventory_path.read_bytes())
    return target


def run_one_seed(
    *,
    repo: Path,
    archive_root: Path,
    ledger_path: Path,
    entry: CheckpointInventoryEntry,
    events: tuple[LedgerEvent, ...],
    attempt_id: str,
    replacement_of: str | None,
    replacement_reason: str | None,
) -> None:
    validate_replacement_request(
        events,
        model_seed=entry.model_seed,
        replacement_of=replacement_of,
        replacement_reason=replacement_reason,
    )
    ensure_clean_tree(repo)
    relative_archive = archive_relative_path(
        entry.model_seed,
        attempt_id,
    )
    archive_output = archive_root / relative_archive
    repo_output_relative = seed_repo_output(
        entry.model_seed,
        attempt_id,
    )
    repo_output = repo / repo_output_relative
    if repo_output.exists() or archive_output.exists():
        raise SIMA1ConfirmatoryError(
            "attempt id already has retained output"
        )

    append_ledger_event(
        ledger_path,
        new_ledger_event(
            attempt_id=attempt_id,
            model_seed=entry.model_seed,
            status="started",
            inventory_entry=entry,
            archive_path=relative_archive,
            replacement_of=replacement_of,
            replacement_reason=replacement_reason,
        ),
    )
    command = build_container_runner_command(
        checkpoint=entry.checkpoint,
        model_seed=entry.model_seed,
        output_dir=repo_output_relative,
        attempt_id=attempt_id,
        replacement_of=replacement_of,
        replacement_reason=replacement_reason,
    )
    try:
        run_process(command, cwd=repo)
    except (subprocess.CalledProcessError, RuntimeError) as error:
        status = classify_failed_attempt(repo_output)
        if repo_output.exists():
            archive_attempt(repo_output, archive_output)
        append_ledger_event(
            ledger_path,
            new_ledger_event(
                attempt_id=attempt_id,
                model_seed=entry.model_seed,
                status=status,
                inventory_entry=entry,
                archive_path=relative_archive,
                replacement_of=replacement_of,
                replacement_reason=replacement_reason,
                failure_detail=str(error),
            ),
        )
        ensure_clean_tree(repo)
        raise

    archive_attempt(repo_output, archive_output)
    summary = validate_attempt_evidence(
        archive_output,
        inventory_entry=entry,
    )
    append_ledger_event(
        ledger_path,
        new_ledger_event(
            attempt_id=attempt_id,
            model_seed=entry.model_seed,
            status="passed",
            inventory_entry=entry,
            archive_path=relative_archive,
            source_git_commit=str(summary["source_git_commit"]),
            image_revision=str(summary["image_revision"]),
            replacement_of=replacement_of,
            replacement_reason=replacement_reason,
        ),
    )
    ensure_clean_tree(repo)
    print(
        "OK: archived SI-MA1 confirmatory attempt "
        f"seed={entry.model_seed} attempt={attempt_id}"
    )


def status_payload(
    *,
    archive_root: Path,
    inventory: tuple[CheckpointInventoryEntry, ...],
    ledger_path: Path,
) -> dict[str, Any]:
    events = read_ledger(ledger_path)
    passed = passed_attempts_by_seed(events)
    payload: dict[str, Any] = {
        "passed_seeds": sorted(passed),
        "missing_seeds": sorted(set(EXPECTED_MODEL_SEEDS) - set(passed)),
        "ledger_event_count": len(events),
        "cohort_complete": False,
        "confirmatory_decision_made": False,
        "CAL-COST-MA1": None,
        "si_ma1_passed": None,
    }
    if tuple(sorted(passed)) == EXPECTED_MODEL_SEEDS:
        payload.update(
            validate_complete_cohort(
                archive_root=archive_root,
                inventory=inventory,
                events=events,
            )
        )
    return payload


def main() -> None:
    args = parse_args()
    repo = Path(__file__).resolve().parents[1]
    head = git_output(repo, "rev-parse", "HEAD")
    verify_implementation_ancestry(repo, head=head)
    inventory_path = resolve_path(args.inventory, repo=repo)
    if inventory_source_commit(inventory_path) != head:
        raise SIMA1ConfirmatoryError(
            "checkpoint inventory was created from another source commit"
        )
    archive_root = args.archive_root
    ensure_external_archive(repo, archive_root)
    inventory = load_inventory(inventory_path, repo=repo)
    inventory_index = inventory_by_seed(inventory)
    sealed_inventory = seal_inventory(
        archive_root=archive_root,
        inventory_path=inventory_path,
    )
    ledger_path = archive_root / "attempt_ledger.jsonl"

    if args.command == "run-seed":
        if args.seed not in EXPECTED_MODEL_SEEDS:
            raise SIMA1ConfirmatoryError("seed must be in 0..9")
        events = read_ledger(ledger_path)
        attempt_id = args.attempt_id or (
            f"si-ma1-confirmatory-seed-{args.seed}-{uuid.uuid4().hex}"
        )
        run_one_seed(
            repo=repo,
            archive_root=archive_root,
            ledger_path=ledger_path,
            entry=inventory_index[args.seed],
            events=events,
            attempt_id=attempt_id,
            replacement_of=args.replacement_of,
            replacement_reason=args.replacement_reason,
        )
        return

    if args.command == "run-cohort":
        for seed in args.seeds:
            events = read_ledger(ledger_path)
            passed = passed_attempts_by_seed(events)
            if seed in passed:
                print(f"SKIP: seed {seed} already has a passed attempt")
                continue
            latest_for_seed = [
                event
                for event in events
                if event.model_seed == seed
            ]
            if latest_for_seed:
                raise SIMA1ConfirmatoryError(
                    f"seed {seed} has retained attempt history; "
                    "use run-seed with an explicit replacement decision"
                )
            run_one_seed(
                repo=repo,
                archive_root=archive_root,
                ledger_path=ledger_path,
                entry=inventory_index[seed],
                events=events,
                attempt_id=(
                    f"si-ma1-confirmatory-seed-{seed}-{uuid.uuid4().hex}"
                ),
                replacement_of=None,
                replacement_reason=None,
            )
        print(
            json.dumps(
                status_payload(
                    archive_root=archive_root,
                    inventory=inventory,
                    ledger_path=ledger_path,
                ),
                indent=2,
                sort_keys=True,
            )
        )
        return

    if args.command == "mark-infrastructure-failure":
        events = read_ledger(ledger_path)
        started = validate_mark_infrastructure_failure(
            events,
            attempt_id=args.attempt_id,
        )
        relative_archive = Path(started.archive_path)
        repo_output = repo / seed_repo_output(
            started.model_seed,
            started.attempt_id,
        )
        archive_output = archive_root / relative_archive
        if repo_output.exists():
            archive_attempt(repo_output, archive_output)
        append_ledger_event(
            ledger_path,
            new_ledger_event(
                attempt_id=started.attempt_id,
                model_seed=started.model_seed,
                status="failed_infrastructure",
                inventory_entry=inventory_index[started.model_seed],
                archive_path=relative_archive,
                replacement_of=started.replacement_of,
                replacement_reason=started.replacement_reason,
                failure_detail=args.detail,
            ),
        )
        ensure_clean_tree(repo)
        print(
            "OK: retained infrastructure failure "
            f"attempt={started.attempt_id}"
        )
        return

    payload = status_payload(
        archive_root=archive_root,
        inventory=inventory,
        ledger_path=ledger_path,
    )
    if args.command == "status":
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    if args.command == "materialize":
        if payload.get("cohort_complete") is not True:
            raise SIMA1ConfirmatoryError(
                "only a complete validated cohort may be materialized"
            )
        ensure_clean_tree(repo)
        materialize_archive(
            repo=repo,
            archive_root=archive_root,
            destination_root=args.destination_root,
            inventory_path=sealed_inventory,
            ledger_path=ledger_path,
            cohort_summary=payload,
        )
        print(
            "OK: SI-MA1 confirmatory execution evidence materialized "
            f"under {args.destination_root}"
        )
        return

    raise SIMA1ConfirmatoryError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    main()
