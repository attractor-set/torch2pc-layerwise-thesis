#!/usr/bin/env python3
"""Verify the authored QW-LC4-E atomic transition without executing it."""

from __future__ import annotations

import argparse
import ast
from pathlib import Path

from torch2pc_thesis.stage3b_qwake_lc4_final_engineering_invocation_authorization_consumption_attempt_atomic_transition import (
    load_atomic_transition,
    validate_atomic_transition,
    verify_atomic_transition_sources,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--transition", type=Path, required=True)
    parser.add_argument("--authoring-base-commit", required=True)
    return parser


def _verify_effect_boundary(project_root: Path) -> None:
    module_path = project_root / (
        "src/torch2pc_thesis/stage3b_qwake_lc4_final_engineering_"
        "invocation_authorization_consumption_attempt_atomic_transition.py"
    )
    verifier_path = project_root / (
        "scripts/verify_stage3b_qwake_lc4_final_engineering_invocation_"
        "authorization_consumption_attempt_atomic_transition.py"
    )
    for path in (module_path, verifier_path):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = tuple(alias.name for alias in node.names)
                if any(
                    name == "subprocess"
                    or name == "torch" or name.startswith("torch.")
                    or "lease_bound_host_invoker_wiring" in name
                    for name in names
                ):
                    raise RuntimeError(f"forbidden import in {path}")
            if isinstance(node, ast.ImportFrom):
                name = node.module or ""
                if (
                    name == "subprocess"
                    or name == "torch" or name.startswith("torch.")
                    or "lease_bound_host_invoker_wiring" in name
                ):
                    raise RuntimeError(f"forbidden import in {path}")
            if isinstance(node, ast.Call):
                function = node.func
                called_name = ""
                if isinstance(function, ast.Name):
                    called_name = function.id
                elif isinstance(function, ast.Attribute):
                    called_name = function.attr
                if called_name == (
                    "execute_final_engineering_invocation_"
                    "atomic_transition_once"
                ):
                    raise RuntimeError(
                        "verifier calls the effectful transition entrypoint"
                    )


def main() -> int:
    args = _parser().parse_args()
    _verify_effect_boundary(args.project_root)
    source = verify_atomic_transition_sources(args.project_root)
    transition = load_atomic_transition(args.transition)
    validate_atomic_transition(
        transition,
        source,
        args.project_root,
        expected_authoring_base_commit=args.authoring_base_commit,
    )
    print("ATOMIC_TRANSITION_VERIFIED=true")
    print("ATOMIC_TRANSITION_AUTHORED=true")
    print("ATOMIC_TRANSITION_MODULE_CREATED=true")
    print("ATOMIC_TRANSITION_VERIFIER_CREATED=true")
    print("ATOMIC_TRANSITION_TESTS_CREATED=true")
    print("ATOMIC_TRANSITION_RECORD_CREATED=true")
    print("ATOMIC_TRANSITION_POST_MERGE_VERIFIED=false")
    print("ATOMIC_TRANSITION_OPERATION_SCOPE_FREEZE_ADMISSIBLE=false")
    print("AUTHORIZATION_CONSUMED=false")
    print("CONSUMPTION_ATTEMPT_ATOMIC_ACTION_PERMITTED=false")
    print("CONSUMPTION_ATTEMPT_ATOMIC_ACTION_COMMITTED=false")
    print("CONSUMPTION_ATTEMPT_STARTED=false")
    print("INVOCATION_COMMAND_MATERIALIZED=false")
    print("EXECUTION_LEASE_V1_PRESENT=false")
    print("EXECUTION_LEASE_V2_PRESENT=false")
    print("DURABLE_HOST_OUTCOME_PRESENT=false")
    print("RUNTIME_OUTPUT_PRESENT=false")
    print("QW5_TRANSITION_PERMITTED=false")
    print("LOCAL_COMPUTE_EXECUTION_OPEN=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
