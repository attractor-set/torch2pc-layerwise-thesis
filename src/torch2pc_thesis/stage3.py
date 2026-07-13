from __future__ import annotations

import hashlib
import itertools
import json
import math
from pathlib import Path
from typing import Any

import yaml

Stage3Design = dict[str, Any]
_COMMIT = 40
_ALLOWED_METHODS = {"fixedpred", "strict"}
_ALLOWED_TRACKS = {"baseline", "exact_shortcut", "implementation_preserving", "approximation"}
_EQUIVALENCE_SCOPES = {"full_trajectory", "endpoint_gradient"}


class Stage3DesignError(ValueError):
    """Raised when the Stage 3 design contract is incomplete or inconsistent."""


def _mapping(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise Stage3DesignError(f"{name} must be a mapping")
    return value


def _sequence(value: Any, name: str) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise Stage3DesignError(f"{name} must be a non-empty list")
    return value


def _full_commit(value: Any, name: str) -> str:
    text = str(value)
    if len(text) != _COMMIT or any(character not in "0123456789abcdef" for character in text):
        raise Stage3DesignError(f"{name} must be a full lowercase 40-character Git commit")
    return text


def _positive(value: Any, name: str, *, allow_zero: bool = False) -> float:
    number = float(value)
    invalid = number < 0 if allow_zero else number <= 0
    if not math.isfinite(number) or invalid:
        qualifier = "finite and non-negative" if allow_zero else "finite and positive"
        raise Stage3DesignError(f"{name} must be {qualifier}")
    return number


def _unit_interval(value: Any, name: str, *, include_zero: bool = False) -> float:
    number = _positive(value, name, allow_zero=include_zero)
    if number > 1:
        raise Stage3DesignError(f"{name} must not exceed 1")
    return number


def _candidate_variants(candidate: dict[str, Any], method: str) -> list[dict[str, Any]]:
    raw_variants = candidate.get("pilot_variants")
    if raw_variants is None:
        return [{"id": "default", "parameters": {}}]
    variants_by_method = _mapping(raw_variants, f"{candidate['id']}.pilot_variants")
    raw_method_variants = _sequence(
        variants_by_method.get(method), f"{candidate['id']}.pilot_variants.{method}"
    )
    variants: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw_variant in enumerate(raw_method_variants):
        variant = _mapping(raw_variant, f"{candidate['id']}.{method}.variants[{index}]")
        variant_id = str(variant.get("id", ""))
        if not variant_id or variant_id in seen:
            raise Stage3DesignError(
                f"{candidate['id']}.{method} variants require unique non-empty ids"
            )
        parameters = _mapping(variant.get("parameters", {}), f"{variant_id}.parameters")
        seen.add(variant_id)
        variants.append({"id": variant_id, "parameters": parameters})
    return variants


def _phase_candidate_ids(
    phase: dict[str, Any],
    phase_name: str,
    candidate_by_id: dict[str, dict[str, Any]],
) -> list[str]:
    candidate_ids = [
        str(value) for value in _sequence(phase.get("candidates"), f"{phase_name}.candidates")
    ]
    unknown = sorted(set(candidate_ids) - set(candidate_by_id))
    if unknown:
        raise Stage3DesignError(f"{phase_name} references unknown candidates: {unknown}")
    deferred = [
        candidate_id
        for candidate_id in candidate_ids
        if candidate_by_id[candidate_id].get("implementation_status") == "deferred"
    ]
    if deferred:
        raise Stage3DesignError(f"{phase_name} cannot include deferred candidates: {deferred}")
    return candidate_ids


def _validate_screening_phase(
    phase: dict[str, Any],
    phase_name: str,
    candidate_by_id: dict[str, dict[str, Any]],
) -> None:
    if phase.get("test_access") is not False:
        raise Stage3DesignError(f"test access must be disabled during Stage 3 {phase_name}")
    _phase_candidate_ids(phase, phase_name, candidate_by_id)
    methods = {str(value) for value in _sequence(phase.get("methods"), f"{phase_name}.methods")}
    if not methods <= _ALLOWED_METHODS:
        raise Stage3DesignError(f"{phase_name} contains unsupported methods")
    seeds = [int(value) for value in _sequence(phase.get("seeds"), f"{phase_name}.seeds")]
    if len(seeds) != len(set(seeds)) or len(seeds) < 3:
        raise Stage3DesignError(f"{phase_name}.seeds must contain at least three unique values")


def load_stage3_design(path: str | Path = "configs/stage3/design.yaml") -> Stage3Design:
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(source)
    value = yaml.safe_load(source.read_text(encoding="utf-8"))
    design = _mapping(value, str(source))
    validate_stage3_design(design)
    return design


def validate_stage3_design(design: Stage3Design) -> None:
    if int(design.get("schema_version", 0)) != 1:
        raise Stage3DesignError("schema_version must equal 1")

    campaign = _mapping(design.get("campaign"), "campaign")
    if not str(campaign.get("id", "")):
        raise Stage3DesignError("campaign.id is required")
    if int(campaign.get("design_revision", 0)) < 1:
        raise Stage3DesignError("campaign.design_revision must be a positive integer")
    if campaign.get("status") != "design_ready":
        raise Stage3DesignError("campaign.status must be design_ready before implementation")
    if campaign.get("stage1_stage2_immutable") is not True:
        raise Stage3DesignError("Stage 1 and Stage 2 must be declared immutable")

    baseline = _mapping(design.get("baseline"), "baseline")
    execution = _full_commit(
        baseline.get("stage2_execution_source"), "baseline.stage2_execution_source"
    )
    publication = _full_commit(
        baseline.get("stage2_publication_state"), "baseline.stage2_publication_state"
    )
    _full_commit(baseline.get("torch2pc_commit"), "baseline.torch2pc_commit")
    if execution == publication:
        raise Stage3DesignError("execution source and publication state must remain distinct")

    candidates = _sequence(design.get("candidates"), "candidates")
    candidate_by_id: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(candidates):
        candidate = _mapping(raw, f"candidates[{index}]")
        candidate_id = str(candidate.get("id", ""))
        if not candidate_id:
            raise Stage3DesignError(f"candidates[{index}].id is required")
        if candidate_id in candidate_by_id:
            raise Stage3DesignError(f"duplicate candidate id: {candidate_id}")
        track = str(candidate.get("track", ""))
        if track not in _ALLOWED_TRACKS:
            raise Stage3DesignError(f"unsupported candidate track: {track}")
        changes_algorithm = candidate.get("changes_algorithm")
        if not isinstance(changes_algorithm, bool):
            raise Stage3DesignError(f"candidate {candidate_id} must declare changes_algorithm")
        if track in {"implementation_preserving", "exact_shortcut"} and changes_algorithm:
            raise Stage3DesignError(f"exact candidate {candidate_id} cannot change the algorithm")
        if track == "approximation" and not changes_algorithm:
            raise Stage3DesignError(
                f"approximation candidate {candidate_id} must be marked algorithm-changing"
            )
        if track in {"implementation_preserving", "exact_shortcut"}:
            if candidate.get("equivalence_gate") is not True:
                raise Stage3DesignError(f"exact candidate {candidate_id} requires equivalence_gate=true")
            equivalence_scope = str(candidate.get("equivalence_scope", ""))
            if equivalence_scope not in _EQUIVALENCE_SCOPES:
                raise Stage3DesignError(
                    f"exact candidate {candidate_id} requires a supported equivalence_scope"
                )
            if track == "implementation_preserving" and equivalence_scope != "full_trajectory":
                raise Stage3DesignError(
                    f"implementation-preserving candidate {candidate_id} requires full_trajectory scope"
                )
            if track == "exact_shortcut" and equivalence_scope != "endpoint_gradient":
                raise Stage3DesignError(
                    f"exact shortcut {candidate_id} requires endpoint_gradient scope"
                )
        if track == "approximation" and candidate.get("non_inferiority_gate") is not True:
            raise Stage3DesignError(
                f"approximation candidate {candidate_id} requires non_inferiority_gate=true"
            )
        methods = {
            str(value) for value in _sequence(candidate.get("methods"), f"{candidate_id}.methods")
        }
        if not methods <= _ALLOWED_METHODS:
            raise Stage3DesignError(f"candidate {candidate_id} contains unsupported methods")
        if candidate.get("pilot_variants") is not None:
            variants_by_method = _mapping(
                candidate["pilot_variants"], f"{candidate_id}.pilot_variants"
            )
            unexpected_methods = sorted(set(variants_by_method) - methods)
            if unexpected_methods:
                raise Stage3DesignError(
                    f"candidate {candidate_id} has variants for unsupported methods: "
                    f"{unexpected_methods}"
                )
            for method in methods:
                _candidate_variants(candidate, method)
        candidate_by_id[candidate_id] = candidate

    baseline_candidate = candidate_by_id.get("stage2_baseline")
    if baseline_candidate is None or baseline_candidate.get("track") != "baseline":
        raise Stage3DesignError("stage2_baseline must be present in the baseline track")
    if baseline_candidate.get("implementation_status") != "available":
        raise Stage3DesignError("stage2_baseline must be available")

    phases = _mapping(design.get("phases"), "phases")
    profiling = _mapping(phases.get("profiling"), "phases.profiling")
    if profiling.get("test_access") is not False:
        raise Stage3DesignError("test access must be disabled during Stage 3 profiling")
    _phase_candidate_ids(profiling, "profiling", candidate_by_id)
    profiling_methods = {
        str(value) for value in _sequence(profiling.get("methods"), "profiling.methods")
    }
    if not profiling_methods <= _ALLOWED_METHODS:
        raise Stage3DesignError("profiling contains unsupported methods")

    pilot = _mapping(phases.get("pilot"), "phases.pilot")
    _validate_screening_phase(pilot, "pilot", candidate_by_id)
    accelerator = _mapping(
        phases.get("accelerator_screening"), "phases.accelerator_screening"
    )
    _validate_screening_phase(accelerator, "accelerator_screening", candidate_by_id)

    final_template = _mapping(phases.get("final_template"), "phases.final_template")
    if final_template.get("status") != "blocked_until_stage3_freeze":
        raise Stage3DesignError("final_template must remain blocked until Stage 3 freeze")
    if final_template.get("test_access") is not False:
        raise Stage3DesignError("final_template must not enable test access before freeze")

    gates = _mapping(design.get("gates"), "gates")
    for gate in ["equivalence", "non_inferiority", "performance", "locality", "predict_correct"]:
        if gate not in gates:
            raise Stage3DesignError(f"gates.{gate} is required")
    _unit_interval(gates["equivalence"].get("cpu_min_cosine"), "cpu_min_cosine")
    _unit_interval(gates["equivalence"].get("gpu_min_cosine"), "gpu_min_cosine")
    _positive(gates["equivalence"].get("cpu_max_relative_l2"), "cpu_max_relative_l2")
    _positive(gates["equivalence"].get("gpu_max_relative_l2"), "gpu_max_relative_l2")
    equivalence_compare = _mapping(gates["equivalence"].get("compare"), "equivalence.compare")
    for scope in _EQUIVALENCE_SCOPES:
        _sequence(equivalence_compare.get(scope), f"equivalence.compare.{scope}")
    _unit_interval(
        gates["performance"].get("fixedpred_min_speedup_fraction"),
        "fixedpred speedup",
    )
    _unit_interval(
        gates["performance"].get("strict_min_speedup_fraction"),
        "strict speedup",
    )
    _unit_interval(
        gates["performance"].get("maximum_baseline_regression_fraction"),
        "maximum baseline regression",
        include_zero=True,
    )
    _unit_interval(
        gates["performance"].get("maximum_memory_growth_fraction"),
        "maximum memory growth",
        include_zero=True,
    )
    _positive(
        gates["locality"].get("maximum_dependency_radius"),
        "maximum_dependency_radius",
        allow_zero=True,
    )
    _unit_interval(
        gates["predict_correct"].get("minimum_vjp_reduction_fraction"),
        "minimum VJP reduction",
    )
    _unit_interval(
        gates["predict_correct"].get("maximum_fallback_fraction"),
        "maximum fallback fraction",
        include_zero=True,
    )
    if gates["predict_correct"].get("require_residual_nonincrease") is not True:
        raise Stage3DesignError("predict_correct must require non-increasing residual")
    if gates["predict_correct"].get("require_at_least_one_exact_correction") is not True:
        raise Stage3DesignError("predict_correct must require at least one exact correction")


def stage3_design_sha256(design: Stage3Design) -> str:
    validate_stage3_design(design)
    payload = json.dumps(design, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _build_screening_cells(
    phase: dict[str, Any],
    candidate_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    cells: list[dict[str, Any]] = []
    for dataset, model, method, candidate_id, seed in itertools.product(
        phase["datasets"],
        phase["models"],
        phase["methods"],
        phase["candidates"],
        phase["seeds"],
    ):
        candidate = candidate_by_id[str(candidate_id)]
        method_name = str(method)
        if method_name not in {str(value) for value in candidate["methods"]}:
            continue
        for variant in _candidate_variants(candidate, method_name):
            cells.append(
                {
                    "dataset": str(dataset),
                    "model": str(model),
                    "method": method_name,
                    "candidate_id": str(candidate_id),
                    "variant_id": str(variant["id"]),
                    "parameters": variant["parameters"],
                    "model_seed": int(seed),
                    "test_access": False,
                }
            )
    order_seed = int(phase["execution_order_seed"])
    cells.sort(
        key=lambda cell: hashlib.sha256(
            f"{order_seed}|{cell['dataset']}|{cell['model']}|{cell['method']}|"
            f"{cell['candidate_id']}|{cell['variant_id']}|{cell['model_seed']}".encode()
        ).hexdigest()
    )
    return cells


def build_stage3_design_plan(design: Stage3Design) -> dict[str, Any]:
    validate_stage3_design(design)
    phases = design["phases"]
    candidate_by_id = {str(candidate["id"]): candidate for candidate in design["candidates"]}

    profiling = phases["profiling"]
    profiling_cells: list[dict[str, Any]] = []
    for candidate_id, method, depth, width, batch_size, seed in itertools.product(
        profiling["candidates"],
        profiling["methods"],
        profiling["depths"],
        profiling["widths"],
        profiling["batch_sizes"],
        profiling["seeds"],
    ):
        candidate = candidate_by_id[str(candidate_id)]
        if str(method) not in {str(value) for value in candidate["methods"]}:
            continue
        profiling_cells.append(
            {
                "candidate_id": str(candidate_id),
                "method": str(method),
                "model": f"mlp_d{int(depth)}_w{int(width)}",
                "depth": int(depth),
                "width": int(width),
                "batch_size": int(batch_size),
                "seed": int(seed),
                "warmup_steps": int(profiling["warmup_steps"]),
                "measured_steps": int(profiling["measured_steps"]),
                "repetitions": int(profiling["repetitions"]),
                "test_access": False,
            }
        )
    profiling_order_seed = int(profiling["execution_order_seed"])
    profiling_cells.sort(
        key=lambda cell: hashlib.sha256(
            f"{profiling_order_seed}|{cell['candidate_id']}|{cell['method']}|"
            f"{cell['model']}|{cell['batch_size']}|{cell['seed']}".encode()
        ).hexdigest()
    )

    pilot_cells = _build_screening_cells(phases["pilot"], candidate_by_id)
    accelerator_cells = _build_screening_cells(
        phases["accelerator_screening"], candidate_by_id
    )

    return {
        "schema_version": 1,
        "campaign_id": design["campaign"]["id"],
        "design_revision": int(design["campaign"]["design_revision"]),
        "design_sha256": stage3_design_sha256(design),
        "status": "design_only_not_executable",
        "baseline": design["baseline"],
        "test_access": False,
        "profiling_planned_cells": len(profiling_cells),
        "profiling_cells": profiling_cells,
        "pilot_planned_cells": len(pilot_cells),
        "pilot_cells": pilot_cells,
        "accelerator_screening_planned_cells": len(accelerator_cells),
        "accelerator_screening_cells": accelerator_cells,
        "final_status": phases["final_template"]["status"],
        "final_formula": phases["final_template"]["design_formula"],
        "final_maximum_cells": int(phases["final_template"]["maximum_cells"]),
    }


def write_stage3_design_plan(
    design: Stage3Design,
    output: str | Path = "build/stage3/stage3_design_plan.json",
) -> Path:
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(build_stage3_design_plan(design), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return target


def stage3_readiness_report(
    root: str | Path = ".",
    design_path: str | Path = "configs/stage3/design.yaml",
) -> dict[str, Any]:
    repository = Path(root)
    design_file = repository / design_path
    design = load_stage3_design(design_file)
    required_files = [
        "docs/stage-3-protocol.md",
        "docs/stage-3-protocol_EN.md",
        "docs/stage-3-readiness.md",
        "docs/stage-3-readiness_EN.md",
        "docs/decisions/ADR-006-stage3-scope.md",
        "docs/decisions/ADR-006-stage3-scope_EN.md",
        "docs/decisions/ADR-007-stage3-locality-taxonomy.md",
        "docs/decisions/ADR-007-stage3-locality-taxonomy_EN.md",
        "docs/decisions/ADR-008-predict-correct-acceleration.md",
        "docs/decisions/ADR-008-predict-correct-acceleration_EN.md",
        "configs/stages/stage3_profiling.yaml",
        "configs/stages/stage3_pilot.yaml",
        "configs/stages/stage3_accelerator_screening.yaml",
        "configs/stages/stage3_final_template.yaml",
        "configs/experiments/STAGE3-A0-fixedpred-finite-step.yaml",
        "configs/experiments/STAGE3-C4-predict-correct.yaml",
        "configs/experiments/STAGE3-C5-local-secant.yaml",
        "configs/experiments/STAGE3-C6-layer-local-anderson.yaml",
        "src/torch2pc_thesis/locality.py",
        "src/torch2pc_thesis/profiling.py",
        "src/torch2pc_thesis/stage3.py",
    ]
    missing = [path for path in required_files if not (repository / path).is_file()]
    plan = build_stage3_design_plan(design)
    blockers = [
        "Stage 3 candidate Torch2PC commits are not pinned yet.",
        "Stage 3 CPU/GPU full-trajectory and endpoint-equivalence gates have not been produced yet.",
        "Predict-correct fallback and residual guards have not been implemented yet.",
        "Stage 3 profiling, core-pilot, and accelerator-screening environment locks are not frozen yet.",
        "The final Stage 3 template keeps test access disabled until a separate freeze.",
    ]
    return {
        "status": "ready_for_stage3_implementation" if not missing else "incomplete",
        "execution_status": "blocked_until_candidates_and_freeze",
        "campaign_id": design["campaign"]["id"],
        "design_revision": plan["design_revision"],
        "design_sha256": plan["design_sha256"],
        "profiling_planned_cells": plan["profiling_planned_cells"],
        "pilot_planned_cells": plan["pilot_planned_cells"],
        "accelerator_screening_planned_cells": plan[
            "accelerator_screening_planned_cells"
        ],
        "missing_files": missing,
        "blockers": blockers,
    }
