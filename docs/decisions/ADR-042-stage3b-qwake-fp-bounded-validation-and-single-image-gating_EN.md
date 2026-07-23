# `ADR-042`: bounded `QWake-FP` validation and single-image permission gating

[Русская версия](ADR-042-stage3b-qwake-fp-bounded-validation-and-single-image-gating.md)

- **Status:** accepted as a docs-only scope freeze after `ADR-041`; scientific [execution](../glossary_EN.md#term-execution) is not authorized
- **Date:** 2026-07-23

## Context

`ADR-041` bounded the mandatory core to temporal `FixedPred` prefixes, nested
`A0 / A1 / A2` observations, a finite analytic registry, shadow admission, and
a full canonical suffix. Two practical ambiguities remained.

First, the general `QWake-PC` [architecture](../glossary_EN.md#term-architecture) could be read as an object that the
master's thesis must validate across [predictive coding](../glossary_EN.md#term-predictive-coding). One bounded experiment
cannot support that conclusion and the resulting scope would be excessive.
Second, adding executable code between collection, calibration, and
confirmatory evaluation would weaken campaign comparability and create repeated
build, backport, and validation cycles.

The corrected Rosenbaum `FixedPred` special case at `eta=1` provides a finite
canonical suffix and an exact post-action reference. It is suitable for bounded
validation of one concrete mechanism implementation, not for a general
transfer claim about `QWake-PC`.

## Decision

1. Preserve `QWake-PC` as a general protocol-constrained specification of a
   controller family, not as one experimentally validated algorithm.
2. Introduce `QWake-FP` as the only mandatory concrete implementation in the
   master's thesis.
3. Bound experimental validation to the corrected Rosenbaum special case:
   `FixedPred`, `eta=1`, a registered sequential architecture, the canonical
   `stage2_baseline`, and a finite depth-bounded suffix.
4. Test, in order, the existence of sufficient partial states, cheap pre-action
   recognizability, admission safety, coverage, and complete cost.
5. Implement one finite superset pipeline in advance, containing all mandatory
   collectors, analytics, oracle logic, replay, baselines, and evaluators.
6. After complete pre-freeze testing, build and freeze one immutable scientific
   image. Executable code and dependencies do not change between [evidence](../glossary_EN.md#term-evidence)
   stages.
7. Do not call campaign stages `A1/A2/A3`, because those names conflict with
   observation levels. Use `C1_COLLECTION`, `C2_CALIBRATION`,
   `C3_CONFIRMATORY`, and `R_REPLICATION`.
8. Activate embedded capabilities only through a hashed fail-closed permission
   manifest. A manifest may select only preregistered capabilities and
   entrypoints; arbitrary code, shell, plugin, or formula loading is forbidden.
9. Place permission checks at effect boundaries inside domain functions, not
   only in a CLI or wrapper. A disabled capability is not called, reads no
   tensor, allocates no memory, synchronizes no device, and creates no output.
10. Separate code identity, campaign request, and policy manifest. A frozen
    policy is data for the embedded interpreter, not new executable code.
11. Permit policy selection and freeze only in `C2_CALIBRATION`; policy
    selection combined with confirmatory-partition access is always forbidden.
12. Open each next stage only through a valid chain of sealed receipts from the
    preceding stages and matching image/code identities.
13. Execute `C3_CONFIRMATORY` on untouched model seeds with an already frozen
    policy. After test access, new features, thresholds, baselines, analytic
    order, defect definitions, and cost mapping are forbidden.
14. Run one replication without retuning on a preregistered additional
    [configuration](../glossary_EN.md#term-configuration), preferably `MNIST` with the same architecture.
15. Preserve the publication-strength minimum package: simple [baselines](../glossary_EN.md#term-baseline),
    nested ablations, seed-level safety, complete overhead, and a releasable
    trajectory benchmark.
16. Keep `Strict`, arbitrary `eta`, recursive multiscale control, a learned
    controller, contextual bandit, and online intervention outside the
    mandatory master's scope.
17. This ADR opens no collection, oracle labels, calibration, confirmatory
    access, replication, policy selection, or test data.

## Evidence stages

```text
C1_COLLECTION
  -> full trajectories, A0/A1/A2, analytic outputs, costs, canonical suffix,
     post-action labels, and opportunity evidence

C2_CALIBRATION
  -> recognizability analysis, baseline comparison, one frozen QWake-FP policy

C3_CONFIRMATORY
  -> untouched shadow evaluation: safety -> coverage -> net cost

R_REPLICATION
  -> the same policy and image without retuning on a preregistered setting
```

All policy candidates and ablations compatible with the full trajectory schema
are evaluated through offline replay. A separate GPU campaign for every
[baseline](../glossary_EN.md#term-baseline) is not required.

## Capability boundary

The minimal closed registry covers A0/A1/A2 collection, registered analytics,
full suffix, post-action oracle, partition access, opportunity and
recognizability analysis, policy selection and freeze, shadow execution,
confirmatory and replication evaluation, sealing, and publication.

The following combinations are always invalid:

```text
SELECT_POLICY + ACCESS_CONFIRMATORY_DATA
C3_CONFIRMATORY + FREEZE_POLICY
C1_COLLECTION + EXECUTE_SHADOW_POLICY
C2_CALIBRATION + PUBLISH_RESULTS
R_REPLICATION + RETUNE_POLICY
```

An unknown capability, missing receipt, incompatible role, or mismatched digest
sets `EXECUTION_AUTHORIZED=false`.

## Normative precedence

```text
adr039_authority=dus_outcome_semantics
adr040_authority=historical_integrated_frontier_design
adr041_authority=current_transition_admission_cost_and_scope_semantics
adr042_authority=qwake_fp_validation_scope_and_single_image_permission_protocol
historical_adr_rewrite_permitted=false
```

`ADR-042` does not change the mathematical semantics of `ADR-039`–`ADR-041`.
It refines only the object of experimental validation, evidence stages, and the
activation protocol for already frozen code.

## Machine boundary

```text
qwake_general_specification_frozen=true
qwake_fp_only_mandatory_implementation=true
qwake_fp_validation_case=corrected_rosenbaum_fixedpred_eta1
qwake_fp_canonical_executor=stage2_baseline
qwake_fp_mode=shadow_only
qwake_fp_generalization_claim=false
execution_image_strategy=single_immutable_superset_image
same_image_digest_required_across_c1_c2_c3_r=true
executable_code_changes_after_image_freeze=false
campaign_roles=C1_COLLECTION,C2_CALIBRATION,C3_CONFIRMATORY,R_REPLICATION
stage_activation=fail_closed_permission_manifest
permission_checks_at_effect_boundaries=true
disabled_capability_executes=false
manifest_arbitrary_code_loading=false
manifest_shell_command_loading=false
policy_representation=frozen_data_manifest
policy_interpreter_embedded_in_image=true
policy_selection_permitted_role=C2_CALIBRATION
confirmatory_access_permitted_role=C3_CONFIRMATORY
policy_selection_with_confirmatory_access_forbidden=true
sealed_receipt_chain_required=true
untouched_confirmatory_seeds_required=true
replication_without_retuning_required=true
publication_baselines_required=true
nested_ablation_required=true
trajectory_benchmark_planned=true
safety_precedes_coverage_precedes_cost=true
qwake_fp_scope_freeze_complete=true
qwake_fp_execution_permitted=false
c1_collection_open=false
c2_calibration_open=false
c3_confirmatory_open=false
replication_open=false
oracle_label_generation_open=false
feature_collection_permitted=false
policy_activation_permitted=false
test_dataset_access=false
full_stage3b_campaign_complete=false
```

## Consequence

The next admissible slice is limited to pure contracts, a permission matrix,
receipt verification, a superset schema, and synthetic/non-interference tests.
The final image may be frozen only after all mandatory code and pre-freeze
validation are complete. Every scientific campaign still requires a separate
request freeze, [runtime](../glossary_EN.md#term-runtime) preflight, and authorization.
