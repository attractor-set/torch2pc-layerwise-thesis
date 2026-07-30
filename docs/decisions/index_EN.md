# Architecture and research decisions

[Русская версия](index.md)

- ADR-001: Use Torch2PC as the primary implementation.
- ADR-002: Use native Ubuntu and ROCm Docker for final results.
- ADR-003: Use macro F1 as the primary selection metric.
- ADR-004: Use paired multi-seed statistics with Holm correction.
- ADR-005: Freeze post-pilot final ordering, resumption, and telemetry.
- [ADR-006](ADR-006-stage3-scope_EN.md): extended Stage 3 scope.
- [ADR-007](ADR-007-stage3-locality-taxonomy_EN.md): multidimensional locality taxonomy.
- [ADR-008](ADR-008-predict-correct-acceleration_EN.md): predict-correct acceleration and exact-correction boundaries.
- [ADR-009](ADR-009-stage3b-rocm-canonical-lane_EN.md): ROCm/float32 as the only Stage 3B B0 canonical lane; CPU/float64 remains an engineering control.
- [ADR-010](ADR-010-stage3b-per-cell-process-isolation_EN.md): a fresh Python child process per Stage 3B B0 canonical cell with fail-fast handling for systemic OOM.
- [ADR-011](ADR-011-stage3b-b0-derived-evidence-seal_EN.md): read-only validation, aggregation, and a content-addressed Stage 3B B0 [evidence](../glossary_EN.md#term-evidence) seal.
- [ADR-012](ADR-012-pc-tref-pc-catm-scenario-a_EN.md): PC-TREF Balanced Core, PC-CATM, and Scenario A as one realistic post-B0 path.
- [ADR-013](ADR-013-pc-tref-operational-semantics_EN.md): operational `PC-TREF`/`PC-CATM` semantics, separate cost boundaries, and B1/B2 admission to preregistration.
- [ADR-014](ADR-014-stage3b-b1-b2-candidate-contracts_EN.md): separate exact
  implementation contracts and equivalence gates for B1/B2.
- [ADR-015](ADR-015-stage3b-matched-measurement-sealing_EN.md): separated
  primary timing and structural counters, locality event streams, and
  matched-specific evidence sealing.
- [ADR-016](ADR-016-stage3b-sufficiency-boundary_EN.md): the one-step
  [operational sufficiency boundary](../glossary_EN.md#term-operational-sufficiency-boundary), separation of oracle label and pre-action
  estimator, conditional geometry, and the unchanged post-`EX-IF0` admission sequence.
- [ADR-017](ADR-017-stage3b-288cell-correctness-repair_EN.md): fail-closed
  lifecycle, confirmatory admission, exact counterbalance, and
  cross-[candidate](../glossary_EN.md#term-candidate) correctness repair before
  the 288-cell campaign.
- [ADR-018](ADR-018-stage3b-b1-confirmatory-preregistration_EN.md): freezes confirmatory `EQ-B1` as 120 matched pairs over ten distinct validation batches and keeps [execution](../glossary_EN.md#term-execution) closed pending a separate opening review.
- [ADR-019](ADR-019-stage3b-b1-confirmatory-opening_EN.md): adds fail-closed
  batch freezing, two-lane authorization, recovery, and confirmatory `EQ-B1`
  sealing infrastructure while keeping [runtime](../glossary_EN.md#term-runtime) execution closed.
- [ADR-020](ADR-020-pc-multiscale-mechanism-decision-architecture_EN.md): [multiscale mechanism–decision architecture](../glossary_EN.md#term-multiscale-mechanism-decision-architecture), scale-specific contracts, and the boundary of the future `QWake-SPC` line.
- [ADR-021](ADR-021-stage3b-b2-confirmatory-preregistration_EN.md): freezes confirmatory `EQ-B2` as 120 matched triples and 240 direct comparisons, reuses the frozen B1 inputs, and keeps [execution](../glossary_EN.md#term-execution) and [matched profiling](../glossary_EN.md#term-matched-profiling) closed pending separate admission.
- [ADR-022](ADR-022-stage3b-b2-confirmatory-opening_EN.md): adds fail-closed request freezing, separated authorization, recovery, and confirmatory `EQ-B2` sealing infrastructure while keeping [execution](../glossary_EN.md#term-execution) closed pending a separate request freeze and runtime admission.
- [ADR-023](ADR-023-stage3b-b2-confirmatory-request-freeze_EN.md): freezes the append-only confirmatory `EQ-B2` request for 120 triples/240 comparisons while keeping [execution](../glossary_EN.md#term-execution) closed pending separate image and [runtime](../glossary_EN.md#term-runtime) validation.
- [ADR-024](ADR-024-stage3b-b2-confirmatory-evidence-preservation_EN.md): preserves byte-for-byte sealed `EQ-B2-CONFIRMATORY=pass` and derived `EQ-B2`, completes the B1/B2 scientific-admission chain, and keeps matched profiling closed until a new versioned freeze.

- [ADR-025](ADR-025-stage3b-matched-profiling-request-refreeze_EN.md): creates a new `v2` request/manifest freeze from sealed confirmatory B1/B2 admissions, preserves historical `v1`, and keeps runtime execution closed.

- [ADR-026](ADR-026-stage3b-matched-profiling-evidence-preservation_EN.md): preserves the sealed 288-cell matched-profiling evidence byte-for-byte, keeps analysis closed, and introduces a draft-only release with separate run artifacts.

- [ADR-027](ADR-027-stage3b-matched-descriptive-analysis-protocol_EN.md): freezes the post-collection/pre-analysis descriptive protocol, `model_seed` independent unit, aggregation order, seven-dimensional Pareto rule, and closed execution/publication boundary.
- [ADR-028](ADR-028-stage3b-matched-descriptive-analysis-implementation_EN.md): replaces the early analyzer with the registered 18-output engine, freezes full synthetic validation, and keeps sealed-evidence execution closed pending a separate authorization.
- [ADR-029](ADR-029-stage3b-matched-descriptive-analysis-preexecution-hardening_EN.md): freezes authorized-output provenance, mutual consistency across the 288/1,440/96 compact rows, and a real `Zstandard` canary without opening execution.

- [ADR-030](ADR-030-stage3b-matched-descriptive-analysis-execution-request-freeze_EN.md): freezes the one-run read-only request, immutable identities, and exact 18-file output contract while keeping authorization and execution closed.

- [ADR-031](ADR-031-stage3b-matched-descriptive-analysis-runtime-preflight-implementation_EN.md): implements fail-closed runtime preflight, future-authorization verification, and a canonical-package executor without opening execution.
- [ADR-032](ADR-032-stage3b-matched-descriptive-analysis-runtime-preflight-freeze_EN.md): freezes the actual runtime preflight for merge commit `272a9258…` while keeping authorization, execution, and publication closed.
- [ADR-033](ADR-033-stage3b-matched-descriptive-analysis-execution-authorization-freeze_EN.md): freezes one prospective read-only authorization, binds request/preflight/runtime identities, and keeps execution pending a merged-main opening gate and publication pending a separate decision.
- [ADR-034](ADR-034-stage3b-matched-descriptive-analysis-output-seal-freeze_EN.md): preserves the exact 18-file output, receipt, and independent audit; binds them through an external seal without changing generated metadata; and keeps publication, superiority, and test boundaries closed.

- [ADR-035](ADR-035-stage3b-recursive-sufficiency-aggregate-direction_EN.md): freezes the [minimum sufficient compute aggregate](../glossary_EN.md#term-minimum-sufficient-compute-aggregate) as the central post-B1/B2 object, recursive two-scale semantics, and the conditional role of spike-like stabilization without execution permission.
- [ADR-036](ADR-036-stage3b-matched-descriptive-analysis-publication-gate_EN.md): freezes the fail-closed publication gate for the sealed descriptive analysis, remote draft-state validation, and the unchanged prohibitions on `EX-IF0`, superiority claims, policy activation, and test access.

- [ADR-037](ADR-037-stage3b-matched-descriptive-analysis-publication-receipt_EN.md): freezes the successful tagged publication action, exact remote receipt, and the still-closed `EX-IF0`, superiority, policy, and test boundaries.
- [ADR-038](ADR-038-stage3b-ex-if0-exact-implementation-and-oracle-sweep-boundary_EN.md): selects `stage2_baseline` as canonical exact reference/[fallback](../glossary_EN.md#term-fallback) and freezes the decision epoch, task-relative [endpoint](../glossary_EN.md#term-endpoint), oracle margin, and full-suffix minimum-stably-sufficient-sweep rule without opening execution or label generation.

- [ADR-039](ADR-039-stage3b-fixedpred-sufficiency-dus-design_EN.md): freezes
  FixedPred, `stage2_baseline`, the Rosenbaum positive control, the corrected
  joint-VJP role, separate compute/diagnostic budgets, and fail-closed
  `DONE / UNKNOWN / SWEEP` without execution permission.

- [ADR-040](ADR-040-stage3b-integrated-frontier-model_EN.md): keeps ADR-039 unchanged and freezes the integrated frontier, `A0 / A1 / A2 / O`, `ACCEPT_FRONTIER / ADVANCE_FRONTIER / COMPLETE_SUFFIX`, transition cost, and the closed execution boundary.
- [ADR-041](ADR-041-stage3b-integrated-frontier-corrective-semantics_EN.md): retains ADR-039/040 as historical decisions and freezes current `A0 -> A1 -> A2`, separate O, `OBSERVATION / ANALYTIC / COMPUTE`, local monotonicity, cost mapping, admission, and bounded temporal-scope semantics.
- [ADR-042](ADR-042-stage3b-qwake-fp-bounded-validation-and-single-image-gating_EN.md): bounds mandatory validation to one [QWake-FP](../glossary_EN.md#term-qwake-fp), freezes the corrected Rosenbaum FixedPred special case, one immutable superset image, C1/C2/C3/R roles, internal permission gates, and a sealed-receipt chain.
- [ADR-043](ADR-043-stage3b-qwake-fp-special-case-contract_EN.md): freezes the machine-readable `QW-2` special-case contract for `FixedPred`, `eta=1`, `stage2_baseline`, `lenet_classic`, exact A0/A1/A2, analytics, B0-B7, P0-P2, and cost mapping without opening execution.
- [ADR-044](ADR-044-stage3b-qwake-fp-pre-freeze-validation_EN.md): freezes the execution-closed `QW-4A` request, pure matched P0/P1/P2 validation harness, negative effect audits, oracle isolation, and mandatory CPU/ROCm gates without authorization, evidence, or image freeze.
- [ADR-045](ADR-045-stage3b-qwake-fp-runtime-validation-implementation_EN.md): implements fail-closed `QW-4B-I` runtime preflight, a separate single-run authorization validator, effect-local adapters, matched state/RNG runner, and pure two-lane engineering-report sealer without issuing authorization or executing the model.
- [ADR-046](ADR-046-stage3b-qwake-documentation-refactor-and-image-reset_EN.md): retires the old authorization before execution, fully synchronizes the active `R/M/Γ/C` and `LOCAL_COMPUTE` model, requires a new image, and moves scientific-image freeze after `QW-LC4-E`.
- [ADR-047](ADR-047-stage3b-qwake-fp-runtime-validation-freeze-v2_EN.md): freezes the new image, live CPU/ROCm preflight, static-receipt chain, and one-[attempt](../glossary_EN.md#term-attempt) authorization for six engineering cells while execution, evidence, `LOCAL_COMPUTE`, and science remain closed.
- [ADR-048](ADR-048-stage3b-qwake-fp-runtime-validation-evidence-v2_EN.md): preserves the exact six-file output, original failing completion receipt, two failed recovery audits, and successful recovery-v3; admits engineering evidence only, prohibits retry, and keeps publication and `QW-LC0` closed.
- [ADR-049](ADR-049-stage3b-qwake-lc0-post-merge-transition_EN.md): records the repository-seal merge into `main`, admits the repository evidence as sealed, and opens `QW-LC0` only for semantics and scope while implementation, execution, the scientific image, test split, and publication remain closed.
- [ADR-050](ADR-050-stage3b-qwake-lc0-semantics-scope-freeze_EN.md): freezes the `R/M/Γ/C` separation, finite `LOCAL_COMPUTE` family, bounded first-candidate scope, and claim restrictions pending later validation.
- [ADR-051](ADR-051-stage3b-qwake-lc0-repository-freeze_EN.md): records the `QW-LC0` contract state on `main`, materializes a separate receipt, and keeps transition to `QW-LC1`, implementation, execution, and publication closed pending merge and revalidation.
- [ADR-052](ADR-052-stage3b-qwake-lc1-transition_EN.md): materializes the transition from completed `QW-LC0` to design of the `R(a,s)` schema, mandatory observables, and `~R`, while keeping `QW-LC1`, cost, code, and execution closed pending merge.
- [ADR-053](ADR-053-stage3b-qwake-lc1-required-response-schema_EN.md): freezes canonical `R(a,s)`, mandatory observables, the zero-safe `~R` operator, and CPU/ROCm profiles while keeping `Γ`, cost, implementation, and execution closed.
- [ADR-054](ADR-054-stage3b-qwake-lc1-repository-freeze_EN.md): records the `QW-LC1` schema state on `main`, materializes a separate receipt, and keeps `QW-LC1` completion, transition to `QW-LC2`, [resource trajectory](../glossary_EN.md#term-resource-trajectory), cost, implementation, and execution closed pending merge and revalidation.
- [ADR-055](ADR-055-stage3b-qwake-lc2-transition_EN.md): materializes the transition from completed `QW-LC1` to design of `Γ`, `Φ`, `C`, and `~C`, while keeping fields, cost, code, and execution closed pending merge.
- [ADR-056](ADR-056-stage3b-qwake-lc2-resource-cost-contract_EN.md): freezes canonical `Γ`, no-double-counting `Φ`, an 11-field `C`, profiles, tolerances, `~C`, Pareto, and tie-break while keeping `QW-LC3`, implementation, and execution closed.

- [ADR-057](ADR-057-stage3b-qwake-lc2-repository-freeze_EN.md): freezes state after the resource-cost contract merge while keeping `QW-LC3`, implementation, and execution closed.
- [ADR-058](ADR-058-stage3b-qwake-lc3-transition_EN.md): materializes the transition from completed `QW-LC2` to design of matched shadow validation, shared-state identity, RNG restoration, a complete exact-reserve suffix, and repeat aggregation while keeping `QW-LC3`, implementation, and execution closed pending merge.
- [ADR-059](ADR-059-stage3b-qwake-lc3-matched-shadow-validation-contract_EN.md): freezes canonical shared-state binding, RNG restoration, twelve balanced pairs, the complete exact-reserve suffix, and componentwise aggregation without opening implementation or execution.
- [ADR-060](ADR-060-stage3b-qwake-lc3-repository-freeze_EN.md): freezes the state after matched shadow-validation contract merge while keeping `QW-LC4-I`, implementation, and execution closed until receipt merge and reverification.
- [ADR-061](ADR-061-stage3b-qwake-lc4-i-bounded-implementation_EN.md): materializes the bounded FixedPred `eta=1` analytic-completion implementation, exact reserve suffix, opaque-state/RNG controls, response and cost mappers, and synthetic-only matched tests while keeping runtime and scientific execution closed.
- [ADR-062](ADR-062-stage3b-qwake-lc4-f-runtime-freeze-authoring_EN.md): materializes the two-phase `QW-LC4-F` authoring slice, frozen runtime request, adapter/preflight/authorization schemas, and sealing boundary while keeping execution and `QW-LC4-E` closed until the actual image and receipts are frozen.
- [ADR-063](ADR-063-stage3b-qwake-lc4-f-runtime-freeze_EN.md): freezes the
  exact image, CPU/ROCm checks, static chain, one-attempt authorization, and
  the ten-file `QW-LC4-F` package while keeping execution and `QW-LC4-E`
  closed pending merge and revalidation.
- [ADR-064](ADR-064-stage3b-qwake-lc4-e-execution-admission-authoring_EN.md):
  introduces a separate fail-closed `QW-LC4-E` admission schema without
  creating an admission record, lease, result root, or executor.
- [ADR-065](ADR-065-stage3b-qwake-lc4-e-execution-admission-freeze_EN.md):
  freezes one concrete `QW-LC4-E` admission while keeping the branch-level
  gate, lease, executor, results, and publication closed.
- [ADR-066](ADR-066-stage3b-qwake-lc4-e-execution-lease-wrapper-authoring_EN.md):
  introduces a prospective one-attempt lease and future execution-wrapper
  contract while keeping writers, executors, results, and execution closed.
- [ADR-067](ADR-067-stage3b-qwake-lc4-e-execution-lease-wrapper-implementation_EN.md):
  implements an exclusive atomic lease claim, post-claim race check, typed
  execution wrapper, and no-replace result promotion while keeping actual
  claim and execution closed.
- [ADR-068](ADR-068-stage3b-qwake-lc4-e-execution-freeze-authoring_EN.md): binds the exact implementation merge and deterministic execution-freeze request while recording the required absence of the concrete backend, one-shot entrypoint, lease, and execution permission.
- [ADR-069](ADR-069-stage3b-qwake-lc4-e-runtime-backend-implementation_EN.md): implements the bounded synthetic backend, numerical canonicalization of the already-completed wavefront, and a one-shot future-freeze guard while keeping the lease, image, and execution closed.

- [ADR-070](ADR-070-stage3b-qwake-lc4-e-execution-freeze-materialization_EN.md): freezes the exact image and canonical execution package while keeping the branch closed until a separate one-shot engineering invocation.

- [ADR-071](ADR-071-stage3b-qwake-lc4-e-one-shot-invocation-authorization_EN.md): binds the exact image, freeze, admission, matrix authorization, backend, and entrypoint to one future engineering invocation while keeping the lease and execution closed.
- [ADR-072](ADR-072-stage3b-qwake-lc4-e-one-shot-invocation-wrapper-authoring_EN.md): freezes the pure host-wrapper contract, exact image, minimal mounts, and isolation while leaving container invocation, lease claim, and execution absent.
- [ADR-073](ADR-073-stage3b-qwake-lc4-e-one-shot-invocation-wrapper-implementation_EN.md): implements exact local-image inspection through `docker image inspect` and deterministic argv materialization without a host invoker, lease, or [execution](../glossary_EN.md#term-execution).
- [ADR-074](ADR-074-stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-authoring_EN.md): freezes the pure single host-spawn contract, container-owned lease claim, post-claim revalidation, and terminal process rules while leaving the invoker and [execution](../glossary_EN.md#term-execution) absent.
- [ADR-075](ADR-075-stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-implementation_EN.md): implements double image/argv revalidation, the sole `Popen`, a child process group, signal forwarding, terminal timeout, and bounded output while keeping branch permission and actual [execution](../glossary_EN.md#term-execution) closed.
- [ADR-076](ADR-076-stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-repository-freeze_EN.md): binds the verified host-runtime-invoker implementation to the exact `main` state while keeping the one-shot invocation, lease, and execution closed until receipt merge and reverification.
- [ADR-077](ADR-077-stage3b-qwake-lc4-e-one-shot-engineering-invocation-admission_EN.md): binds the completed repository freeze, one-shot authorization, exact image, and bounded host invoker into a fail-closed admission while keeping runtime verification and invocation in a separate operation.
- [ADR-078](ADR-078-stage3b-qwake-lc4-e-one-shot-engineering-invocation-operation_EN.md): freezes the exact dynamic inputs and checks for the future one-shot operation while keeping image inspection, command materialization, lease, and spawn closed until a separate execution slice.
- [ADR-079](ADR-079-stage3b-qwake-lc4-e-one-shot-engineering-invocation-execution-authorization_EN.md): binds the merged operation record to the previous one-shot authorization, image, Torch2PC revision, and host invoker, authorizing only a future same-process pre-execution check and one future invocation while keeping authoring effects closed.
- [ADR-080](ADR-080-stage3b-qwake-lc4-e-one-shot-engineering-invocation-preexecution-verification_EN.md): binds the merged authorization to the exact host invoker and freezes continuous current-runtime verification in the same process as the single future child creation while keeping dynamic verification and execution closed.

- [ADR-081](ADR-081-stage3b-qwake-lc4-e-one-shot-engineering-invocation-runtime-operation_EN.md): freezes the bounded atomic-operation entry point, explicit permission and acknowledgement, exact host resources, and sole delegation to the host invoker while keeping dynamic verification, lease, and execution closed.
