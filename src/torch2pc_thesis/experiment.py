from __future__ import annotations

import json
import os
import re
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any, cast

from torch2pc_thesis.assets import verify_locked_prepared_assets
from torch2pc_thesis.config import FINAL_STAGES, PINNED_STAGES, config_sha256
from torch2pc_thesis.manifests import directory_manifest, environment_snapshot, write_json
from torch2pc_thesis.registry import RegistryEntry, append_entry, completed_experiments
from torch2pc_thesis.training import run_training


def timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def compact_timestamp() -> str:
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


def experiment_id(
    config: dict[str, Any],
    source_commit: str,
    environment_lock_sha256: str | None,
) -> str:
    stage = config["meta"]["stage"]
    dataset = config["data"]["dataset"]
    method = config["method"]["name"]
    seed = config["reproducibility"]["model_seed"]
    digest = config_sha256(config)[:10]
    revision = source_commit[:8]
    environment = "unlocked" if environment_lock_sha256 is None else environment_lock_sha256[:8]
    return (f"{stage}-{dataset}-{method}-s{seed}-{digest}-{revision}-{environment}").lower()


def new_run_id() -> str:
    return f"{compact_timestamp()}-{uuid.uuid4().hex[:8]}"


def _git_output(args: list[str]) -> str:
    return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT).strip()


def observed_source_commit() -> str:
    value = os.environ.get("SOURCE_GIT_COMMIT", "").strip()
    if re.fullmatch(r"[0-9a-f]{40}", value):
        return value
    try:
        value = _git_output(["git", "rev-parse", "HEAD"])
    except Exception as exc:
        raise RuntimeError(
            "SOURCE_GIT_COMMIT is absent and the Git revision is unavailable"
        ) from exc
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        raise RuntimeError("A valid source Git commit is required for execution")
    return value


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise RuntimeError(f"Required protocol artifact is missing: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"Protocol artifact must contain a JSON object: {path}")
    return cast(dict[str, Any], value)


def _sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _protocol_path(config: dict[str, Any], key: str, default: str) -> Path:
    return Path(str(config.get("protocol", {}).get(key, default)))


def _assert_control_gates(config: dict[str, Any], source_commit: str) -> str:
    environment_lock = _protocol_path(
        config, "environment_lock", "results/summaries/environment-lock.json"
    )
    lock = _load_json(environment_lock)
    if lock.get("image_source_git_commit") != source_commit:
        raise RuntimeError("Container source commit differs from environment lock")
    verify_locked_prepared_assets(lock, verify_hashes=False)
    for group in ["config_files", "source_files"]:
        records = lock.get(group)
        if not isinstance(records, list) or not records:
            raise RuntimeError(f"Environment lock has no {group} records")
        for item in records:
            if not isinstance(item, dict):
                raise RuntimeError(f"Invalid environment-lock record in {group}")
            path = Path(str(item.get("path", "")))
            expected = str(item.get("sha256", ""))
            if not path.is_file() or _sha256(path) != expected:
                raise RuntimeError(f"File differs from environment lock: {path}")
    lock_sha256 = _sha256(environment_lock)
    gate_defaults = {
        "cpu": "results/summaries/control_gate_cpu.json",
        "gpu": "results/summaries/control_gate_gpu.json",
    }
    for device, default in gate_defaults.items():
        gate_path = _protocol_path(config, f"control_gate_{device}", default)
        value = _load_json(gate_path)
        if value.get("environment_lock_sha256") != lock_sha256:
            raise RuntimeError(f"Control gate belongs to another environment lock: device={device}")
        if not value.get("gate_observed_within_thresholds"):
            raise RuntimeError(f"Control gate is outside thresholds for device={device}")
    return lock_sha256


def _assert_freeze(config: dict[str, Any]) -> dict[str, Any]:
    freeze_path = _protocol_path(
        config, "freeze_manifest", "results/summaries/pilot-freeze_manifest.json"
    )
    freeze = _load_json(freeze_path)
    expected_milestone = str(config.get("protocol", {}).get("freeze_milestone", "pilot-freeze"))
    if freeze.get("milestone") != expected_milestone:
        raise RuntimeError("Unexpected freeze artifact")
    for item in freeze.get("files", []):
        path = Path(str(item["path"]))
        actual = _sha256(path)
        if actual != item["sha256"]:
            raise RuntimeError(f"Frozen configuration changed: {path}")
    environment_lock_path = _protocol_path(
        config, "environment_lock", "results/summaries/environment-lock.json"
    )
    if freeze.get("environment_lock_sha256") != _sha256(environment_lock_path):
        raise RuntimeError("Freeze artifact belongs to another environment lock")
    return freeze


def assert_research_prerequisites(config: dict[str, Any]) -> str | None:
    stage = str(config["meta"]["stage"])
    source_commit = observed_source_commit()
    environment_lock_sha256: str | None = None
    if stage == "pilot" or stage in FINAL_STAGES:
        environment_lock_sha256 = _assert_control_gates(config, source_commit)
    freeze: dict[str, Any] | None = None
    if stage in FINAL_STAGES:
        freeze = _assert_freeze(config)
    torch2pc_path = Path(config["torch2pc"]["local_path"])
    expected_commit = str(config["torch2pc"].get("commit", ""))

    if stage in PINNED_STAGES:
        if not re.fullmatch(r"[0-9a-f]{40}", expected_commit):
            raise RuntimeError("A full Torch2PC commit must be pinned before this stage")
        if not (torch2pc_path / ".git").exists():
            raise RuntimeError(f"Torch2PC checkout is missing: {torch2pc_path}")
        actual_commit = _git_output(["git", "-C", str(torch2pc_path), "rev-parse", "HEAD"])
        if actual_commit != expected_commit:
            raise RuntimeError(
                f"Torch2PC checkout mismatch: expected {expected_commit}, found {actual_commit}"
            )
        worktree_status = _git_output(["git", "-C", str(torch2pc_path), "status", "--porcelain"])
        if worktree_status:
            raise RuntimeError("Torch2PC worktree contains uncommitted changes")

    required = config.get("protocol", {}).get("required_artifacts", [])
    missing = [str(path) for path in required if not Path(path).exists()]
    if missing:
        raise RuntimeError(f"Required protocol artifacts are missing: {missing}")

    if stage in FINAL_STAGES:
        if not bool(config["evaluation"]["use_test"]):
            raise RuntimeError("Final stage must explicitly enable test evaluation")
        if str(config["protocol"]["status"]) != "frozen":
            raise RuntimeError("Final stage requires a frozen protocol")
        method_name = str(config["method"]["name"])
        if method_name in {"fixedpred", "strict"}:
            if freeze is None:
                raise RuntimeError("Pilot freeze was not loaded")
            selected = freeze.get("selected_method_parameters", {}).get(method_name)
            if not isinstance(selected, dict):
                raise RuntimeError(f"Frozen parameters are missing for method={method_name}")
            observed_eta = float(config["method"]["eta"])
            observed_steps = int(config["method"]["inference_steps"])
            if observed_eta != float(selected["eta"]) or observed_steps != int(
                selected["inference_steps"]
            ):
                raise RuntimeError(f"Resolved {method_name} parameters differ from pilot-freeze")
    return environment_lock_sha256


def execute(config: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    environment_lock_sha256 = assert_research_prerequisites(config)
    source_commit = observed_source_commit()
    identifier = experiment_id(config, source_commit, environment_lock_sha256)
    run_id = new_run_id()
    run_directory = Path(config["paths"]["runs"]) / identifier / run_id
    registry_path = config["paths"]["registry"]
    if str(config["meta"]["stage"]) in FINAL_STAGES:
        completed_ids = {row["experiment_id"] for row in completed_experiments(registry_path)}
        if identifier in completed_ids:
            raise RuntimeError(
                "A completed final run already exists for this code/configuration/seed"
            )
    started = timestamp()
    eta = "" if config["method"].get("eta") is None else str(config["method"]["eta"])
    inference_steps = (
        ""
        if config["method"].get("inference_steps") is None
        else str(config["method"]["inference_steps"])
    )
    base = {
        "run_id": run_id,
        "experiment_id": identifier,
        "stage": str(config["meta"]["stage"]),
        "dataset": str(config["data"]["dataset"]),
        "model": str(config["model"]["architecture"]),
        "method": str(config["method"]["name"]),
        "eta": eta,
        "inference_steps": inference_steps,
        "model_seed": int(config["reproducibility"]["model_seed"]),
        "split_seed": int(config["reproducibility"]["split_seed"]),
        "config_sha256": config_sha256(config),
        "git_commit": source_commit,
        "torch2pc_commit": str(config["torch2pc"].get("commit", "")),
        "run_directory": str(run_directory),
        "started_utc": started,
    }
    run_directory.mkdir(parents=True, exist_ok=False)
    environment = environment_snapshot()
    environment.update(
        {
            "source_git_commit": source_commit,
            "environment_lock_sha256": environment_lock_sha256,
            "experiment_id": identifier,
            "run_id": run_id,
            "config_sha256": config_sha256(config),
        }
    )
    write_json(environment, run_directory / "environment.json")
    (run_directory / "resolved_config.json").write_text(
        json.dumps(config, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    append_entry(
        registry_path,
        RegistryEntry(status="running", **base),  # type: ignore[arg-type]
    )

    try:
        metrics = run_training(config, run_directory)
        write_json(directory_manifest(run_directory), run_directory / "manifest.json")
        append_entry(
            registry_path,
            RegistryEntry(
                status="completed",
                finished_utc=timestamp(),
                test_evaluated=str(bool(metrics["test_evaluated"])).lower(),
                **base,  # type: ignore[arg-type]
            ),
        )
        return identifier, run_id, metrics
    except Exception as exc:
        run_directory.mkdir(parents=True, exist_ok=True)
        (run_directory / "failure.json").write_text(
            json.dumps(
                {
                    "exception_type": type(exc).__name__,
                    "message": str(exc),
                    "repr": repr(exc),
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        write_json(directory_manifest(run_directory), run_directory / "manifest.json")
        append_entry(
            registry_path,
            RegistryEntry(
                status="failed",
                finished_utc=timestamp(),
                notes=f"{type(exc).__name__}: {exc}",
                **base,  # type: ignore[arg-type]
            ),
        )
        raise
