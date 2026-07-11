from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml

Config = dict[str, Any]
PINNED_STAGES = {"pilot", "final", "diagnostics", "publication"}
TRAINING_STAGES = {"smoke", "pilot", "final"}


class ConfigurationError(ValueError):
    pass


def load_yaml(path: str | Path) -> Config:
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(source)
    value = yaml.safe_load(source.read_text(encoding="utf-8"))
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ConfigurationError(f"Top-level YAML object must be a mapping: {source}")
    return value


def deep_merge(base: Config, override: Config) -> Config:
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def resolve_config(
    root: str | Path,
    *,
    stage: str,
    method: str,
    hardware: str = "rx7700xt_5700x3d",
    experiment: str | None = None,
) -> Config:
    root_path = Path(root)
    sources = [
        root_path / "base.yaml",
        root_path / "hardware" / f"{hardware}.yaml",
        root_path / "stages" / f"{stage}.yaml",
        root_path / "methods" / f"{method}.yaml",
    ]
    if experiment:
        sources.append(root_path / "experiments" / f"{experiment}.yaml")

    resolved: Config = {}
    for source in sources:
        resolved = deep_merge(resolved, load_yaml(source))

    resolved.setdefault("meta", {})
    resolved["meta"]["stage"] = stage
    resolved["meta"]["method"] = method
    resolved["meta"]["hardware_profile"] = hardware
    resolved["meta"]["sources"] = [
        source.relative_to(root_path).as_posix() for source in sources
    ]
    validate_config(resolved)
    return resolved


def _value(config: Config, path: tuple[str, ...]) -> Any:
    cursor: Any = config
    for part in path:
        if not isinstance(cursor, dict) or part not in cursor:
            raise ConfigurationError(f"Missing configuration value: {'.'.join(path)}")
        cursor = cursor[part]
    return cursor


def validate_config(config: Config) -> None:
    required_paths = [
        ("project", "name"),
        ("protocol", "status"),
        ("data", "dataset"),
        ("data", "validation_fraction"),
        ("model", "architecture"),
        ("training", "epochs"),
        ("training", "batch_size"),
        ("training", "primary_metric"),
        ("method", "name"),
        ("evaluation", "use_test"),
        ("reproducibility", "split_seed"),
        ("reproducibility", "model_seed"),
        ("reproducibility", "loader_seed"),
        ("runtime", "device"),
        ("runtime", "dtype"),
        ("torch2pc", "repository"),
        ("torch2pc", "local_path"),
    ]
    for path in required_paths:
        _value(config, path)

    stage = str(config.get("meta", {}).get("stage", ""))
    method = str(config["method"]["name"])
    if method not in {"bp", "exact", "fixedpred", "strict"}:
        raise ConfigurationError(f"Unknown method: {method}")
    if int(config["training"]["epochs"]) < 0:
        raise ConfigurationError("training.epochs must be non-negative")
    if int(config["training"]["batch_size"]) < 1:
        raise ConfigurationError("training.batch_size must be positive")
    fraction = float(config["data"]["validation_fraction"])
    if not 0 < fraction < 1:
        raise ConfigurationError("data.validation_fraction must be in (0, 1)")
    if str(config["runtime"]["dtype"]) not in {"float32", "float64"}:
        raise ConfigurationError("runtime.dtype must be float32 or float64")

    use_test = bool(config["evaluation"]["use_test"])
    if stage in {"correctness", "smoke", "pilot"} and use_test:
        raise ConfigurationError(f"Test access is prohibited during stage={stage}")
    if stage == "final" and not use_test:
        raise ConfigurationError("Final stage requires evaluation.use_test=true")
    if stage == "final" and str(config["protocol"]["status"]) != "frozen":
        raise ConfigurationError("Final stage requires protocol.status=frozen")
    if stage == "final":
        selection = config.get("selection", {})
        for key in ["datasets", "models", "methods", "seeds"]:
            if not selection.get(key):
                raise ConfigurationError(f"Final stage requires selection.{key}")
        if str(config["data"]["dataset"]) not in set(selection["datasets"]):
            raise ConfigurationError("Dataset is outside the frozen final design")
        if str(config["model"]["architecture"]) not in set(selection["models"]):
            raise ConfigurationError("Model is outside the frozen final design")
        if method not in set(selection["methods"]):
            raise ConfigurationError("Method is outside the frozen final design")
        if int(config["reproducibility"]["model_seed"]) not in {
            int(value) for value in selection["seeds"]
        }:
            raise ConfigurationError("Model seed is outside the frozen final design")

    if method in {"fixedpred", "strict"}:
        if config["method"].get("eta") is None:
            raise ConfigurationError(f"method.eta is required for {method}")
        if config["method"].get("inference_steps") is None:
            raise ConfigurationError(f"method.inference_steps is required for {method}")
        if float(config["method"]["eta"]) <= 0:
            raise ConfigurationError("method.eta must be positive")
        if int(config["method"]["inference_steps"]) < 1:
            raise ConfigurationError("method.inference_steps must be positive")

    commit = str(config["torch2pc"].get("commit", ""))
    if commit and not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ConfigurationError("torch2pc.commit must be empty or a 40-character SHA")


def canonical_json(config: Config) -> str:
    return json.dumps(config, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def config_sha256(config: Config) -> str:
    return hashlib.sha256(canonical_json(config).encode("utf-8")).hexdigest()


def write_resolved(config: Config, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        yaml.safe_dump(config, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return output
