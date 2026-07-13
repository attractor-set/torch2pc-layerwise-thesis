from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml

Config = dict[str, Any]
FINAL_STAGES = {"final", "final_stage_2"}
PINNED_STAGES = {"pilot", *FINAL_STAGES, "diagnostics", "publication"}
TRAINING_STAGES = {"smoke", "pilot", *FINAL_STAGES}
STAGE3_DESIGN_STAGES = {"stage3_profiling", "stage3_pilot", "stage3_final_template"}


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
    resolved["meta"]["sources"] = [source.relative_to(root_path).as_posix() for source in sources]
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

    if str(config.get("meta", {}).get("method", method)) != method:
        raise ConfigurationError("meta.method must match method.name")
    if str(config["training"]["primary_metric"]) not in {"macro_f1", "accuracy", "loss"}:
        raise ConfigurationError("training.primary_metric must be macro_f1, accuracy, or loss")
    if str(config["runtime"]["device"]).lower() not in {"cpu", "gpu", "cuda", "rocm", "auto"}:
        raise ConfigurationError("runtime.device must be cpu, gpu, cuda, rocm, or auto")
    if bool(config["runtime"].get("mixed_precision", False)):
        raise ConfigurationError("Mixed precision is not implemented in the controlled protocol")
    if bool(config["data"].get("download_during_run", False)):
        raise ConfigurationError("Dataset download during an experiment is prohibited")

    use_test = bool(config["evaluation"]["use_test"])
    if stage in {"correctness", "smoke", "pilot"} and use_test:
        raise ConfigurationError(f"Test access is prohibited during stage={stage}")
    if stage in FINAL_STAGES and not use_test:
        raise ConfigurationError("Final stage requires evaluation.use_test=true")
    if stage in FINAL_STAGES and str(config["protocol"]["status"]) != "frozen":
        raise ConfigurationError("Final stage requires protocol.status=frozen")
    if stage in STAGE3_DESIGN_STAGES:
        if use_test:
            raise ConfigurationError(f"Test access is prohibited during stage={stage}")
        stage3 = config.get("stage3", {})
        if str(stage3.get("design", "")) != "configs/stage3/design.yaml":
            raise ConfigurationError("Stage 3 design stages must reference configs/stage3/design.yaml")
        if stage == "stage3_final_template":
            if str(config["protocol"]["status"]) != "blocked_until_stage3_freeze":
                raise ConfigurationError("Stage 3 final template must remain blocked until freeze")
            if bool(config.get("selection", {}).get("configuration_frozen", False)):
                raise ConfigurationError("Stage 3 final template cannot be marked frozen")
            if config.get("selection", {}).get("selected_candidates") is not None:
                raise ConfigurationError("Stage 3 candidates must be selected only after pilot freeze")
        elif str(stage3.get("candidate_id", "")) == "":
            raise ConfigurationError("Stage 3 profiling and pilot require stage3.candidate_id")
    if stage in FINAL_STAGES:
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

    statistics = config.get("statistics", {})
    selection = config.get("selection", {})
    statistical_metric = str(statistics.get("primary_metric", ""))
    if statistical_metric != str(config["training"]["primary_metric"]):
        raise ConfigurationError("statistics.primary_metric must match training.primary_metric")
    if float(statistics.get("equivalence_margin_macro_f1", 0.0)) <= 0:
        raise ConfigurationError("Equivalence margin must be positive")
    alpha = float(statistics.get("alpha", 0.0))
    if not 0 < alpha < 0.5:
        raise ConfigurationError("statistics.alpha must be in (0, 0.5)")
    minimum_pairs = int(statistics.get("minimum_primary_pairs", 0))
    if minimum_pairs < 2:
        raise ConfigurationError("minimum_primary_pairs must be at least 2")
    primary_model = str(statistics.get("primary_model", ""))
    if not primary_model:
        raise ConfigurationError("statistics.primary_model is required")
    primary_contrasts = [str(value) for value in statistics.get("primary_contrasts", [])]
    if not primary_contrasts:
        raise ConfigurationError("statistics.primary_contrasts is required")
    allowed_contrast_methods = {"exact", "fixedpred", "strict"}
    for contrast in primary_contrasts:
        if not contrast.endswith("_vs_bp"):
            raise ConfigurationError(f"Unsupported primary contrast: {contrast}")
        contrast_method = contrast.removesuffix("_vs_bp")
        if contrast_method not in allowed_contrast_methods:
            raise ConfigurationError(f"Unknown primary contrast method: {contrast_method}")

    confidence = float(statistics.get("confidence", 0.0))
    difference_confidence = float(statistics.get("difference_confidence", 0.0))
    equivalence_confidence = float(statistics.get("equivalence_confidence", 0.0))
    if abs(confidence - (1.0 - alpha)) > 1e-12:
        raise ConfigurationError("statistics.confidence must equal 1 - alpha")
    if abs(difference_confidence - (1.0 - alpha)) > 1e-12:
        raise ConfigurationError("statistics.difference_confidence must equal 1 - alpha")
    if abs(equivalence_confidence - (1.0 - 2.0 * alpha)) > 1e-12:
        raise ConfigurationError("statistics.equivalence_confidence must equal 1 - 2 * alpha")

    controls = config.get("controls", {})
    control_seeds = [int(value) for value in controls.get("model_seeds", [])]
    if not control_seeds or len(control_seeds) != len(set(control_seeds)):
        raise ConfigurationError("controls.model_seeds must contain unique values")
    if int(controls.get("batches_per_seed", 0)) < 1:
        raise ConfigurationError("controls.batches_per_seed must be positive")
    thresholds = controls.get("thresholds", {})
    for device in ["cpu", "gpu"]:
        device_thresholds = thresholds.get(device, {})
        min_cosine = float(device_thresholds.get("min_cosine", -1.0))
        max_relative_l2 = float(device_thresholds.get("max_relative_l2", -1.0))
        if not -1.0 <= min_cosine <= 1.0:
            raise ConfigurationError(f"controls.thresholds.{device}.min_cosine must be in [-1, 1]")
        if max_relative_l2 < 0:
            raise ConfigurationError(
                f"controls.thresholds.{device}.max_relative_l2 must be non-negative"
            )

    if stage == "pilot":
        if str(selection.get("ranking_metric")) != statistical_metric:
            raise ConfigurationError("Pilot ranking_metric must match statistics.primary_metric")
        success_rate = float(selection.get("minimum_success_rate", 0.0))
        if not 0 < success_rate <= 1:
            raise ConfigurationError("Pilot minimum_success_rate must be in (0, 1]")
        expected_seeds = {int(value) for value in statistics.get("pilot_seeds", [])}
        observed_seeds = {int(value) for value in selection.get("seeds", [])}
        if observed_seeds != expected_seeds:
            raise ConfigurationError("Pilot selection.seeds must match statistics.pilot_seeds")
        primary_dataset = str(statistics.get("primary_dataset"))
        secondary_dataset = str(statistics.get("secondary_dataset"))
        if str(selection.get("selection_dataset")) != primary_dataset:
            raise ConfigurationError(
                "Pilot selection_dataset must match statistics.primary_dataset"
            )
        if str(selection.get("secondary_dataset")) != secondary_dataset:
            raise ConfigurationError(
                "Pilot secondary_dataset must match statistics.secondary_dataset"
            )
        if set(selection.get("datasets", [])) != {primary_dataset, secondary_dataset}:
            raise ConfigurationError(
                "Pilot selection.datasets must match the primary and secondary datasets"
            )
        if str(config["data"]["dataset"]) not in set(selection.get("datasets", [])):
            raise ConfigurationError("Dataset is outside the pilot design")
        pilot_models = {str(value) for value in selection.get("models", [])}
        if primary_model not in pilot_models:
            raise ConfigurationError("Pilot models must contain statistics.primary_model")
        if str(config["model"]["architecture"]) not in pilot_models:
            raise ConfigurationError("Model is outside the pilot design")
        if method not in set(selection.get("methods", [])):
            raise ConfigurationError("Method is outside the pilot design")
        if int(config["reproducibility"]["model_seed"]) not in observed_seeds:
            raise ConfigurationError("Model seed is outside the pilot design")
    if stage in FINAL_STAGES:
        expected_seeds = {int(value) for value in statistics.get("final_seeds", [])}
        observed_seeds = {int(value) for value in selection.get("seeds", [])}
        if observed_seeds != expected_seeds:
            raise ConfigurationError("Final selection.seeds must match statistics.final_seeds")
        expected_datasets = {
            str(statistics.get("primary_dataset")),
            str(statistics.get("secondary_dataset")),
        }
        if set(selection.get("datasets", [])) != expected_datasets:
            raise ConfigurationError(
                "Final selection.datasets must match the pre-specified primary and secondary datasets"
            )
        final_models = {str(value) for value in selection.get("models", [])}
        if primary_model not in final_models:
            raise ConfigurationError("Final models must contain statistics.primary_model")
        final_methods = {str(value) for value in selection.get("methods", [])}
        contrast_methods = {value.removesuffix("_vs_bp") for value in primary_contrasts}
        if "bp" not in final_methods or not contrast_methods.issubset(final_methods):
            raise ConfigurationError(
                "Final methods must contain BP and every primary contrast method"
            )
        execution_order = str(selection.get("execution_order", ""))
        if execution_order != "deterministic_hash_counterbalance":
            raise ConfigurationError(
                "Final selection.execution_order must be deterministic_hash_counterbalance"
            )
        if int(selection.get("execution_order_seed", -1)) < 0:
            raise ConfigurationError("Final selection.execution_order_seed must be non-negative")

    if stage == "final_stage_2":
        comparison = config.get("comparison", {})
        original_commit = str(comparison.get("original_torch2pc_commit", ""))
        candidate_commit = str(config["torch2pc"].get("commit", ""))
        if not re.fullmatch(r"[0-9a-f]{40}", original_commit):
            raise ConfigurationError("comparison.original_torch2pc_commit must be a full SHA")
        if candidate_commit == original_commit:
            raise ConfigurationError(
                "final_stage_2 requires a Torch2PC commit different from Stage 1"
            )
        if str(config["paths"]["registry"]) == "experiments/registry.csv":
            raise ConfigurationError("final_stage_2 requires an isolated registry")
        if str(config["paths"]["runs"]) == "results/runs":
            raise ConfigurationError("final_stage_2 requires an isolated run directory")

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
