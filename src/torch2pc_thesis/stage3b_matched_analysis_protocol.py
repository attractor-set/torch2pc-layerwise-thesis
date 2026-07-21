"""Frozen post-collection protocol for Stage 3B matched descriptive analysis."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import Final, cast

PROTOCOL_SCHEMA_VERSION: Final[int] = 1
PROTOCOL_ID: Final[str] = "stage3b-matched-descriptive-analysis-protocol-v1"
PROTOCOL_STATUS: Final[str] = "frozen_post_collection_pre_analysis"
PROTOCOL_FREEZE_DATE: Final[str] = "2026-07-21"

EVIDENCE_ROOT_RELATIVE: Final[Path] = Path(
    "results/stage-3/profiling/matched/stage3b-matched-profiling-e1dcfb2-v1"
)
PROTOCOL_ROOT_RELATIVE: Final[Path] = Path(
    "experiments/frozen/stage3b-matched-descriptive-analysis-v1"
)
RELEASE_TAG: Final[str] = "stage3b-matched-profiling-evidence-v1"
RELEASE_COMMIT: Final[str] = "21ddfb8840674871f0b9d888b36397f5cf0e111b"
EXECUTION_SOURCE_COMMIT: Final[str] = "e1dcfb26823e1191b98d2aa2a598499b13197583"
IMAGE_DIGEST: Final[str] = (
    "sha256:3c269b4278026b5b69968b3265b506ce626f2baf693859989de3371d639da4d0"
)
EXPECTED_EVIDENCE_SHA256: Final[dict[str, str]] = {
    "SHA256SUMS": "ea9b5facec9605b9af89a69a6ccc5e49a3790c25e6fd9c768bf4fe760114411d",
    "SEALED-SHA256SUMS": "98ba77a375e4cfb2931b0490d642f7861834dfa30981f28e8a305a49765764c8",
    "analysis_metadata.json": "b60b3fd8b24c9c847fac3826131a0ab5b50987c04835841573d9351b8e43f605",
    "locality_events.asset.json": "348e578d4334737d676b0da41ac42f001943653e973dff5183ceb5e7d23519c1",
    "locality_events.jsonl.zst": "59a1479d66f170970b4d0f2b0712b8a825ccca01eab677c887a9046fc4c16f76",
    "profiling_cells.csv": "91f5bf665778f2edefbcdcfa9572df771b1288274e902123e303b59c71733373",
    "profiling_repetitions.csv": "788a16e66d62a8ddba52a200fc19014eab18312cc71fae652d760033161bff27",
    "profiling_summary.csv": "92ba5ae6b3cbba256f54ffccaf44ab21fc8c294442a9a25366d0b7ae0aa1c4c7",
    "seal.json": "83691730d46599a7a4d1ffd8ee0e2b9ee82c13771892b21c8c986d9a700e60f3",
}

BASELINE: Final[str] = "stage2_baseline"
CANDIDATES: Final[tuple[str, ...]] = ("isolated_layer_vjp", "composite_vjp")
ALL_CANDIDATES: Final[tuple[str, ...]] = (BASELINE, *CANDIDATES)
METHODS: Final[tuple[str, ...]] = ("fixedpred", "strict")
DEPTHS: Final[tuple[int, ...]] = (4, 8, 16, 32)
WIDTHS: Final[tuple[int, ...]] = (64, 256)
BATCH_SIZES: Final[tuple[int, ...]] = (64, 256)
MODEL_SEEDS: Final[tuple[int, ...]] = (70, 71, 72)
FIXEDPRED_MIN_DEVICE_REDUCTION: Final[float] = 0.15
STRICT_MIN_DEVICE_REDUCTION: Final[float] = 0.20
MAX_DEVICE_REGRESSION: Final[float] = 0.03
MAX_PEAK_MEMORY_GROWTH: Final[float] = 0.15
PARETO_EPSILON: Final[float] = 1.0e-12

REQUIRED_CELL_COLUMNS: Final[tuple[str, ...]] = (
    "cell_id",
    "block_id",
    "candidate_id",
    "method",
    "depth",
    "width",
    "batch_size",
    "model_seed",
    "primary_host_time_us",
    "primary_device_time_us",
    "primary_peak_allocated_bytes",
    "primary_peak_reserved_bytes",
    "observer_cost_ms",
    "saved_tensor_bytes",
    "state_vjp_calls",
    "graph_span",
    "dependency_radius",
    "graph_lifetimes",
    "feedback_operator",
    "fallback_validation_cost_ms",
    "fallback_validation_status",
)
REQUIRED_REPETITION_COLUMNS: Final[tuple[str, ...]] = (
    "cell_id",
    "block_id",
    "candidate_id",
    "method",
    "depth",
    "width",
    "batch_size",
    "model_seed",
    "repetition",
)


class Stage3BMatchedAnalysisProtocolError(RuntimeError):
    """Raised when the frozen descriptive-analysis protocol cannot be verified."""


def sha256_file(path: Path) -> str:
    """Return SHA-256 for a file without loading it into memory."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Stage3BMatchedAnalysisProtocolError(f"cannot read JSON: {path}") from exc
    if not isinstance(value, dict):
        raise Stage3BMatchedAnalysisProtocolError(f"expected JSON object: {path}")
    return cast(dict[str, object], value)


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
            columns = list(reader.fieldnames or [])
    except OSError as exc:
        raise Stage3BMatchedAnalysisProtocolError(f"cannot read CSV: {path}") from exc
    if not rows:
        raise Stage3BMatchedAnalysisProtocolError(f"CSV is empty: {path}")
    return columns, rows


def _verify_source_identity(evidence_root: Path) -> None:
    for name, expected_digest in EXPECTED_EVIDENCE_SHA256.items():
        path = evidence_root / name
        if not path.is_file():
            raise Stage3BMatchedAnalysisProtocolError(f"missing evidence input: {path}")
        observed_digest = sha256_file(path)
        if observed_digest != expected_digest:
            raise Stage3BMatchedAnalysisProtocolError(
                f"evidence digest mismatch for {name}: "
                f"expected={expected_digest}, observed={observed_digest}"
            )


def _verify_claim_boundary(evidence_root: Path) -> None:
    seal = _load_json(evidence_root / "seal.json")
    expected = {
        "status": "sealed",
        "scope": "stage3b_b1_b2_matched_sealed_evidence_v1",
        "matched_cell_count": 288,
        "cross_candidate_correctness_block_count": 96,
        "evidence": True,
        "results_publication_permitted": False,
        "full_stage3b_campaign_complete": False,
        "test_dataset_access": False,
        "source_commit": EXECUTION_SOURCE_COMMIT,
        "image_digest": IMAGE_DIGEST,
    }
    for key, expected_value in expected.items():
        if seal.get(key) != expected_value:
            raise Stage3BMatchedAnalysisProtocolError(
                f"sealed evidence boundary mismatch for {key}: "
                f"expected={expected_value!r}, observed={seal.get(key)!r}"
            )

    metadata = _load_json(evidence_root / "analysis_metadata.json")
    if metadata.get("independent_unit") != "model_seed":
        raise Stage3BMatchedAnalysisProtocolError("independent unit is not model_seed")
    if metadata.get("results_publication_permitted") is not False:
        raise Stage3BMatchedAnalysisProtocolError("source metadata permits publication")
    if metadata.get("test_dataset_access") is not False:
        raise Stage3BMatchedAnalysisProtocolError("source metadata reports test access")
    if metadata.get("aggregation_order") != [
        "measured_steps_to_repetition",
        "repetitions_to_cell",
        "cells_to_model_seed",
    ]:
        raise Stage3BMatchedAnalysisProtocolError("source aggregation order differs")

    locality = _load_json(evidence_root / "locality_events.asset.json")
    if locality.get("compressed_sha256") != EXPECTED_EVIDENCE_SHA256[
        "locality_events.jsonl.zst"
    ]:
        raise Stage3BMatchedAnalysisProtocolError("locality compressed digest differs")
    if locality.get("uncompressed_sha256") != (
        "3228baaa0f6479b1b4296f96632bd2d99c49642dc38f28f5ed7bc978d9dc538a"
    ):
        raise Stage3BMatchedAnalysisProtocolError("locality source digest differs")
    if locality.get("results_publication_permitted") is not False:
        raise Stage3BMatchedAnalysisProtocolError("locality asset permits publication")


def _verify_matrix_identity(evidence_root: Path) -> None:
    cell_columns, cells = _read_csv(evidence_root / "profiling_cells.csv")
    missing_cell_columns = sorted(set(REQUIRED_CELL_COLUMNS) - set(cell_columns))
    if missing_cell_columns:
        raise Stage3BMatchedAnalysisProtocolError(
            f"profiling_cells.csv missing columns: {missing_cell_columns}"
        )
    if len(cells) != 288:
        raise Stage3BMatchedAnalysisProtocolError(
            f"profiling_cells.csv row count differs: {len(cells)}"
        )
    if len({row["cell_id"] for row in cells}) != 288:
        raise Stage3BMatchedAnalysisProtocolError("profiling cell IDs are not unique")
    if len({row["block_id"] for row in cells}) != 96:
        raise Stage3BMatchedAnalysisProtocolError("matched block count differs")

    candidate_counts = Counter(row["candidate_id"] for row in cells)
    method_counts = Counter(row["method"] for row in cells)
    seed_counts = Counter(int(row["model_seed"]) for row in cells)
    if candidate_counts != Counter({candidate: 96 for candidate in ALL_CANDIDATES}):
        raise Stage3BMatchedAnalysisProtocolError("candidate coverage differs")
    if method_counts != Counter({method: 144 for method in METHODS}):
        raise Stage3BMatchedAnalysisProtocolError("method coverage differs")
    if seed_counts != Counter({seed: 96 for seed in MODEL_SEEDS}):
        raise Stage3BMatchedAnalysisProtocolError("model-seed coverage differs")

    expected_configurations = {
        (method, depth, width, batch_size, seed)
        for method in METHODS
        for depth in DEPTHS
        for width in WIDTHS
        for batch_size in BATCH_SIZES
        for seed in MODEL_SEEDS
    }
    block_candidates: dict[str, set[str]] = {}
    observed_configurations: set[tuple[str, int, int, int, int]] = set()
    for row in cells:
        block_candidates.setdefault(row["block_id"], set()).add(row["candidate_id"])
        observed_configurations.add(
            (
                row["method"],
                int(row["depth"]),
                int(row["width"]),
                int(row["batch_size"]),
                int(row["model_seed"]),
            )
        )
    if observed_configurations != expected_configurations:
        raise Stage3BMatchedAnalysisProtocolError("configuration matrix differs")
    if any(candidates != set(ALL_CANDIDATES) for candidates in block_candidates.values()):
        raise Stage3BMatchedAnalysisProtocolError("candidate coverage differs within a block")

    repetition_columns, repetitions = _read_csv(
        evidence_root / "profiling_repetitions.csv"
    )
    missing_repetition_columns = sorted(
        set(REQUIRED_REPETITION_COLUMNS) - set(repetition_columns)
    )
    if missing_repetition_columns:
        raise Stage3BMatchedAnalysisProtocolError(
            f"profiling_repetitions.csv missing columns: {missing_repetition_columns}"
        )
    if len(repetitions) != 1440:
        raise Stage3BMatchedAnalysisProtocolError(
            f"profiling_repetitions.csv row count differs: {len(repetitions)}"
        )
    repetition_keys = {
        (row["cell_id"], int(row["repetition"]))
        for row in repetitions
    }
    if len(repetition_keys) != 1440:
        raise Stage3BMatchedAnalysisProtocolError("repetition keys are not unique")
    if Counter(int(row["repetition"]) for row in repetitions) != Counter(
        {index: 288 for index in range(5)}
    ):
        raise Stage3BMatchedAnalysisProtocolError("repetition coverage differs")


def build_protocol(project_root: Path) -> dict[str, object]:
    """Build the deterministic protocol without calculating observed effects."""

    root = project_root.expanduser().resolve()
    evidence_root = root / EVIDENCE_ROOT_RELATIVE
    _verify_source_identity(evidence_root)
    _verify_claim_boundary(evidence_root)
    _verify_matrix_identity(evidence_root)

    return {
        "schema_version": PROTOCOL_SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": PROTOCOL_STATUS,
        "freeze_date": PROTOCOL_FREEZE_DATE,
        "phase": "post_collection_pre_analysis",
        "source_evidence": {
            "root": str(EVIDENCE_ROOT_RELATIVE),
            "release_tag": RELEASE_TAG,
            "release_commit": RELEASE_COMMIT,
            "execution_source_commit": EXECUTION_SOURCE_COMMIT,
            "image_digest": IMAGE_DIGEST,
            "expected_sha256": dict(sorted(EXPECTED_EVIDENCE_SHA256.items())),
            "locality_uncompressed_sha256": (
                "3228baaa0f6479b1b4296f96632bd2d99c49642dc38f28f5ed7bc978d9dc538a"
            ),
            "release_asset_count": 10,
            "release_status": "draft_only",
        },
        "claim_boundary": {
            "protocol_frozen": True,
            "protocol_builder_uses_observed_metric_values": False,
            "analysis_implementation_permitted_after_protocol_merge": True,
            "analysis_execution_permitted": False,
            "analysis_results_present": False,
            "source_evidence_read_only": True,
            "results_publication_permitted": False,
            "release_publication_permitted": False,
            "full_stage3b_campaign_complete": False,
            "test_dataset_access": False,
            "ex_if0_opened": False,
            "policy_activation_permitted": False,
            "superiority_claim_permitted": False,
        },
        "design": {
            "baseline": BASELINE,
            "candidates": list(CANDIDATES),
            "methods": list(METHODS),
            "depths": list(DEPTHS),
            "widths": list(WIDTHS),
            "batch_sizes": list(BATCH_SIZES),
            "model_seeds": list(MODEL_SEEDS),
            "independent_unit": "model_seed",
            "matched_block_count": 96,
            "matched_cell_count": 288,
            "repetitions_per_cell": 5,
            "paired_candidate_rows_expected": 192,
            "configuration_rows_expected": 64,
            "candidate_method_rows_expected": 4,
            "pareto_membership_rows_expected": 96,
            "scaling_metric_count": 7,
        },
        "aggregation": {
            "authoritative_compact_inputs": [
                "profiling_repetitions.csv",
                "profiling_cells.csv",
                "profiling_summary.csv",
            ],
            "order": [
                "measured_steps_to_repetition",
                "repetitions_to_cell",
                "candidate_to_baseline_within_matched_block",
                "model_seeds_within_configuration",
                "configurations_within_candidate_method",
            ],
            "step_to_repetition": {
                "time": "median",
                "observer_cost": "median",
                "saved_tensor_bytes": "median",
                "state_vjp_calls": "median",
                "peak_memory": "maximum",
                "graph_span": "maximum",
                "dependency_radius": "maximum",
            },
            "repetition_to_cell": {
                "time": "median_of_repetition_medians",
                "observer_cost": "median_of_repetition_medians",
                "saved_tensor_bytes": "median_of_repetition_medians",
                "state_vjp_calls": "median_of_repetition_medians",
                "peak_memory": "maximum_across_repetitions",
                "graph_span": "maximum_across_repetitions",
                "dependency_radius": "maximum_across_repetitions",
            },
            "within_block": "candidate_divided_by_stage2_baseline",
            "within_configuration_across_seeds": [
                "median",
                "minimum",
                "maximum",
                "directional_consistency_count",
            ],
            "candidate_method_matrix_summary": (
                "median_minimum_maximum_of_16_configuration_medians_descriptive_only"
            ),
            "repetitions_do_not_increase_independent_n": True,
            "configurations_do_not_increase_independent_n_for_inferential_claims": True,
        },
        "estimands": {
            "primary": [
                {
                    "id": "device_time_ratio_to_baseline",
                    "definition": "candidate_primary_device_time_us / baseline_primary_device_time_us",
                    "direction": "minimize",
                },
                {
                    "id": "device_time_reduction",
                    "definition": "1 - device_time_ratio_to_baseline",
                    "direction": "maximize",
                },
                {
                    "id": "device_speedup",
                    "definition": "1 / device_time_ratio_to_baseline",
                    "direction": "maximize",
                },
            ],
            "secondary": [
                "host_time_ratio_to_baseline",
                "peak_allocated_ratio_to_baseline",
                "peak_reserved_ratio_to_baseline",
            ],
            "structural": [
                "saved_tensor_bytes_ratio_to_baseline",
                "state_vjp_calls_ratio_to_baseline",
                "graph_span_ratio_to_baseline",
                "dependency_radius_ratio_to_baseline",
            ],
            "observer": {
                "metric": "observer_cost_ms",
                "reported_separately": True,
                "subtracted_from_primary_timing": False,
                "included_in_primary_pareto_vector": False,
            },
            "locality_event_diagnostics": [
                "event_count_per_measured_step",
                "median_logical_edge_count_per_event",
                "graph_module_coverage_fraction",
                "maximum_graph_island_count",
                "orchestration_barriers_per_measured_step",
                "graph_lifetime_distribution",
            ],
        },
        "scaling": {
            "unit": "candidate_method_model_seed_metric",
            "metrics": [
                "device_time_ratio_to_baseline",
                "peak_allocated_ratio_to_baseline",
                "peak_reserved_ratio_to_baseline",
                "saved_tensor_bytes_ratio_to_baseline",
                "state_vjp_calls_ratio_to_baseline",
                "graph_span_ratio_to_baseline",
                "dependency_radius_ratio_to_baseline",
            ],
            "response": "log2(candidate_to_baseline_ratio)",
            "factors": ["log2(depth)", "log2(width)", "log2(batch_size)"],
            "interactions": False,
            "reported": [
                "2_power_beta_multiplier_per_factor_doubling",
                "r_squared",
                "maximum_absolute_log2_residual",
            ],
            "claim": "descriptive_sensitivity_summary_not_universal_complexity_law",
        },
        "pareto_rule": {
            "unit": "candidate_method_depth_width_batch_size_after_seed_summary",
            "included_alternatives": list(ALL_CANDIDATES),
            "dimensions_to_minimize": [
                "median_device_time_ratio_to_baseline",
                "median_peak_allocated_ratio_to_baseline",
                "median_peak_reserved_ratio_to_baseline",
                "median_saved_tensor_bytes_ratio_to_baseline",
                "median_state_vjp_calls_ratio_to_baseline",
                "median_graph_span_ratio_to_baseline",
                "median_dependency_radius_ratio_to_baseline",
            ],
            "dominance": (
                "a_dominates_b_when_all_dimensions_a_le_b_plus_epsilon_and_"
                "at_least_one_dimension_a_lt_b_minus_epsilon"
            ),
            "epsilon": PARETO_EPSILON,
            "missing_or_nonpositive_baseline": "fail_closed",
            "single_winner_implied": False,
            "observer_cost_excluded_reason": "instrumentation_cost_reported_separately",
        },
        "engineering_decision_rule": {
            "fixedpred_min_device_time_reduction": FIXEDPRED_MIN_DEVICE_REDUCTION,
            "strict_min_device_time_reduction": STRICT_MIN_DEVICE_REDUCTION,
            "maximum_device_time_regression_in_any_seed": MAX_DEVICE_REGRESSION,
            "maximum_peak_allocated_growth": MAX_PEAK_MEMORY_GROWTH,
            "maximum_peak_reserved_growth": MAX_PEAK_MEMORY_GROWTH,
            "configuration_qualified_when": [
                "median_device_time_reduction_meets_method_threshold",
                "maximum_seed_device_time_ratio_is_at_most_1_plus_regression_limit",
                "median_peak_allocated_growth_is_at_most_memory_limit",
                "median_peak_reserved_growth_is_at_most_memory_limit",
                "candidate_is_pareto_admissible",
            ],
            "candidate_method_status": {
                "retain": "all_16_configurations_qualified",
                "conditional": "one_to_15_configurations_qualified",
                "reject_or_revise": "zero_configurations_qualified",
            },
            "candidate_overall_status": {
                "retain": "both_methods_retain",
                "conditional": "at_least_one_method_is_retain_or_conditional",
                "reject_or_revise": "both_methods_reject_or_revise",
            },
            "baseline_role": "mandatory_fallback_not_classified",
            "decision_scope": "engineering_continuation_not_superiority",
        },
        "missingness_and_sensitivity": {
            "post_hoc_exclusion_permitted": False,
            "trimming_permitted": False,
            "winsorization_permitted": False,
            "missing_registered_cell": "fail_closed",
            "nonfinite_registered_metric": "fail_closed",
            "duplicate_registered_key": "fail_closed",
            "sensitivity_outputs": [
                "seed_directional_consistency",
                "leave_one_seed_out_descriptive_summary",
                "host_time_secondary_comparison",
                "allocated_and_reserved_memory_separately",
            ],
            "p_values": False,
            "bootstrap_confidence_intervals": False,
            "superiority_language": False,
        },
        "registered_outputs": {
            "output_root_policy": "new_empty_directory_fail_if_exists_or_nonempty",
            "expected_top_level_file_count": 18,
            "tables": {
                "paired_block_metrics.csv": 192,
                "configuration_summary.csv": 64,
                "candidate_method_summary.csv": 4,
                "pareto_membership.csv": 96,
                "locality_cell_summary.csv": 288,
                "scaling_seed_effects.csv": 84,
            },
            "machine_readable": [
                "analysis_metadata.json",
                "analysis_summary.json",
                "engineering_decision.json",
                "SHA256SUMS",
            ],
            "figures": [
                "device_time_ratio_heatmap.pdf",
                "peak_memory_ratio_heatmap.pdf",
                "structural_cost_ratio_heatmap.pdf",
                "scaling_effects.pdf",
                "pareto_membership.pdf",
                "seed_consistency.pdf",
            ],
            "reports": [
                "REPORT.md",
                "REPORT_EN.md",
            ],
            "analysis_output_evidence_before_sealing": False,
            "results_publication_permitted_before_publication_gate": False,
        },
    }


def protocol_bytes(protocol: Mapping[str, object]) -> bytes:
    """Return canonical JSON bytes for the frozen protocol."""

    return (json.dumps(protocol, indent=2, sort_keys=True) + "\n").encode("utf-8")


def validate_protocol(protocol: Mapping[str, object], project_root: Path) -> None:
    """Validate a protocol by exact equality with the deterministic builder."""

    expected = build_protocol(project_root)
    if dict(protocol) != expected:
        raise Stage3BMatchedAnalysisProtocolError(
            "frozen matched descriptive-analysis protocol differs from deterministic builder"
        )


def write_protocol_package(
    project_root: Path,
    output_root: Path,
    *,
    check: bool = False,
) -> dict[str, object]:
    """Write or verify protocol.json and SHA256SUMS."""

    protocol = build_protocol(project_root)
    protocol_content = protocol_bytes(protocol)
    checksum_content = f"{hashlib.sha256(protocol_content).hexdigest()}  protocol.json\n".encode()
    destination = output_root.expanduser().resolve()
    expected = {
        "protocol.json": protocol_content,
        "SHA256SUMS": checksum_content,
    }
    if check:
        for name, content in expected.items():
            path = destination / name
            if not path.is_file() or path.read_bytes() != content:
                raise Stage3BMatchedAnalysisProtocolError(
                    f"frozen protocol package differs: {path}"
                )
        observed_names = {
            path.name for path in destination.iterdir() if path.is_file()
        }
        if observed_names != set(expected):
            raise Stage3BMatchedAnalysisProtocolError(
                f"frozen protocol file set differs: {sorted(observed_names)}"
            )
        return protocol
    if destination.exists() and any(destination.iterdir()):
        raise Stage3BMatchedAnalysisProtocolError(
            f"protocol output root is not empty: {destination}"
        )
    destination.mkdir(parents=True, exist_ok=True)
    for name, content in expected.items():
        (destination / name).write_bytes(content)
    return protocol
