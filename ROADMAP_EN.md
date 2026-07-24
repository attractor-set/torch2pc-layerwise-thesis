# Roadmap

[Русская версия](ROADMAP.md)

The roadmap separates completed, permitted, and blocked work. Every transition
requires verified artifacts, preserved claim boundaries, and a separate
admission decision.

## Stages 1–10 — complete

Infrastructure and pilot work, Stage 1/2, Stage 3A, Stage 3B B0 evidence, and
B0 statistical and engineering analysis are complete. The test dataset
remained closed.

## Stage 11 — Scenario A and initial theory — complete

`ADR-012` froze PC-TREF Balanced Core, PC-CATM, and Scenario A. `ECZ` has the
single meaning `Error-Cancellation Zone`; B0 remains an immutable baseline.

## Stage 12 — validity controls and `SI-MA0` — complete

Shortcut/equivalence controls, observer non-interference, deterministic
mechanism controls, and `SI-MA0` are complete. `REC`, `OBS`, `VER`, and `CMP`
passed, while `COST` failed; the negative global outcome is retained.

## Stage 13 — `SI-MA1` — complete

`SI-MA1` preregistration, implementation, confirmatory execution, and final
decision are complete. Across ten `model_seed` values and 180 matched blocks,
`CAL-COST-MA1=true` and `SI-MA1=pass`. The `SI-MA0` result remains unchanged,
and the cost of a future `ECZ` evaluator is excluded.

## Stage 14 — theoretical freeze before B1/B2 — complete

Operational PC-TREF/PC-CATM semantics, regret, norm contracts,
`precision-masked zero`, the cost vector, and cost separation are published
under `ADR-013`.

## Stage 15 — B1/B2 preregistration — complete

B1 `isolated_layer_vjp`, B2 `composite_vjp`, the shared overview, and
`ADR-014` are frozen. Publication tag: `stage3b-b1-b2-prereg-v1`. B2
`block`/`chunk` variants are outside this contract and require separate
preregistration.

## Stage 16 — exact candidates and [matched profiling](docs/glossary_EN.md#term-matched-profiling) — analysis published and receipt frozen

Complete:

- B1 is implemented and sealed as confirmatory `EQ-B1` over 120/120 pairs;
- B2 is implemented and passed engineering smoke over 12/12 triples and 24/24
  comparisons;
- the candidate-aware matched-profiling runner is implemented;
- the fail-closed confirmatory-B2 requirement before production launch is
  frozen;
- confirmatory B2 is preregistered for 120 triples and 240 comparisons;
- confirmatory B2 is executed and sealed: 120/120 triples, 240/240 comparisons, `EQ-B2-CONFIRMATORY=pass`, and derived `EQ-B2`; evidence is preserved as `stage3b-b2-confirmatory-63885e5-v1`.

Current boundary:

```text
scientific_admission=open
candidate_aware_runner=complete
b2_confirmatory_decision=pass_sealed
b2_confirmatory_request_frozen=true
b2_confirmatory_admission=present
matched_profiling_request_refrozen=true
matched_profiling_request_refresh_required=false
matched_profiling_execution_open=false
matched_profiling_execution_complete=true
matched_profiling_runtime_validation=valid
matched_profiling_evidence=sealed
matched_profiling_analysis_protocol_frozen=true
matched_profiling_analysis_implementation_complete=true
matched_profiling_analysis_preexecution_hardening=complete
matched_profiling_analysis_execution_request_frozen=true
matched_profiling_analysis_runtime_preflight_implementation=complete
matched_profiling_analysis_runtime_preflight_frozen=true
matched_profiling_analysis_execution_authorization_present=true
matched_profiling_analysis_synthetic_validation=pass
matched_profiling_analysis_execution_open=false
matched_profiling_analysis_execution_complete=true
matched_profiling_analysis_results_present=true
matched_profiling_analysis_output_audited=true
matched_profiling_analysis_output_seal_frozen=true
matched_profiling_analysis_output_evidence=true
matched_profiling_analysis_publication_gate_frozen=true
matched_profiling_analysis_publication_action_complete=true
matched_profiling_analysis_publication_receipt_frozen=true
matched_profiling_analysis_open=false
runtime_authorization=issued_consumed
measurements_allowed=false
results_publication_permitted=true
release_draft_required=false
release_publication_permitted=true
release_publication_complete=true
ex_if0_protocol_frozen=true
ex_if0_opened=true
ex_if0_complete=true
exact_implementation_frozen=true
exact_implementation_candidate=stage2_baseline
minimum_sufficient_sweep_rule_frozen=true
ex_if0_execution_permitted=false
oracle_label_generation_open=false
feature_collection_permitted=false
a11_off0_execution_open=false
recursive_aggregate_execution_open=false
policy_activation_permitted=false
test_dataset_access=false
full_stage3b_campaign_complete=false
```

Execution request `v1`, runtime preflight, and authorization were frozen before
computation. The single read-only attempt completed on verified `main`; the
18-file output, receipt, and independent audit are preserved without rerunning.
An external seal binds those artifacts and moves the unchanged output into
repository evidence without rewriting generated metadata.

Stage 16 is complete: the fail-closed publication action succeeded, and the
exact remote receipt/status is frozen without rerunning the analysis.
Superiority claims, policy activation, and test access remain closed. Negative
and mixed results are retained.

## Stage 17 — `EX-IF0` and current design boundary — complete

`stage2_baseline` is frozen as the canonical exact reference and fail-closed
fallback. The decision epoch, task-relative endpoint, oracle margin, and
full-suffix rule for the minimum stably sufficient sweep are frozen. Execution
and oracle-label generation remain closed.

ADR-039–ADR-041 define D/U/S and the integrated temporal frontier. ADR-042
further bounds mandatory validation to one
[QWake-FP](docs/glossary_EN.md#term-qwake-fp) implementation for corrected
Rosenbaum FixedPred at `eta=1` and introduces one immutable permission-gated
image.

The historical policy queue after `EX-IF0` remains as provenance rather than
as the current mandatory critical path: `A11-OFF0` denotes offline opportunity
and recognizability analysis, `A11-OFF1` freezes the selected `predictor`, and
only then may `shadow` evaluation proceed. ADR-042 maps this work onto the
`C1/C2/C3` roles without opening execution gates.

## Stage 18 — `QW-0`: scope freeze — current docs-only stage

Freeze:

- general `QWake-PC` versus concrete `QWake-FP`;
- the corrected Rosenbaum FixedPred special case;
- `C1_COLLECTION / C2_CALIBRATION / C3_CONFIRMATORY / R_REPLICATION` roles;
- one finite superset image;
- permission checks at effect boundaries;
- frozen policy as a data manifest;
- publication-strength baselines, untouched seeds, ablations, replication, and
  a trajectory benchmark.

Scientific execution, labels, features, calibration, and test access remain
closed.

## Stage 19 — `QW-1`: pure QWake contract

Without Torch2PC or GPU, implement pure types for frontier state, observations,
analytics, actions, admission, costs, oracle labels, and provenance, plus
`Capability`, [campaign role](docs/glossary_EN.md#term-campaign-role),
`PermissionSet`, and `ExecutionContext`.

Gate: fail-closed defaults, deterministic replay, property tests, and rejection
of every incompatible permission combination.

Status: `QW-1` is implemented as a pure Python contract without Torch2PC/GPU;
all permissions default to deny, while role/receipt/digest bindings and
deterministic transitions are covered by exhaustive unit/property guards.
Scientific execution is not opened. The next mandatory stage is `QW-2`.

## Stage 20 — `QW-2`: QWake-FP special-case contract

Freeze FixedPred, eta=1, stage2_baseline, architecture, horizon, snapshot
boundaries, task-relative response, primary defect, A0/A1/A2, analytic
registry, cost schema, baselines, role matrix, and receipt requirements.

Status: `QW-2` is complete. `ADR-043`, the pure Python specification, and the
sealed `stage3b-qwake-fp-special-case-v1/contract.json` freeze `lenet_classic`,
the EX-IF0 defect, exact A0/A1/A2, analytic, B0-B7, and P0-P2 registries,
while permission/receipt mapping is inherited from `QW-1`. Execution remains
closed. The next mandatory stage is `QW-3`.

## Stage 21 — `QW-3`: superset pipeline implementation

Before the first scientific freeze, implement the complete mandatory code:

```text
collector
A0/A1/A2
analytic registry
canonical suffix and post-action O
cost instrumentation
opportunity and recognizability analysis
policy interpreter
baseline and ablation replay
shadow confirmatory evaluation
replication evaluation
sealing and publication export
```

A manifest cannot load arbitrary code and may activate only embedded
capabilities.

## Stage 22 — `QW-4`: pre-freeze validation

Run static/unit/integration checks, CPU/ROCm smoke, permission matrix, negative
permission tests, deterministic replay, schema tests, corrupt/missing-manifest
tests, receipt-chain tests, and baseline replay tests.

Validate observation through three matched pairs:

```text
P0: B0 <-> B0+A0
P1: B0 <-> B0+A0+A1
P2: B0 <-> B0+A0+A1+A2
```

The pairs establish non-interference, correctness, and accumulated observation
cost; nesting, disabled capabilities, oracle isolation, and analytics are
checked separately.

A disabled capability must not be called, read tensors, allocate memory,
synchronize the device, or create output.

## Stage 23 — `QW-5`: single scientific-image freeze

Freeze source commit/tree, Torch2PC commit, image digest, code manifest, and
output/capability/policy schema versions. Executable code and dependencies do
not change across C1/C2/C3/R.

A material post-freeze defect requires a new digest and protocol version; old
evidence remains preserved and is not rewritten.

## Stage 24 — `QW-6`: `C1_COLLECTION` and opportunity

With the same image, collect complete design/calibration temporal trajectories,
A0/A1/A2, analytic outputs, edge costs, canonical suffix, and post-action oracle
labels. The sealed C1 dataset must be a self-contained input to offline C2.

Opportunity gate:

```text
exists_preterminal_sufficient_state=true
potential_avoided_cost_exceeds_control_overhead_lower_bound=true
```

If the gate fails, policy selection is not mandatory; the result is preserved
as a bounded negative finding.

## Stage 25 — `QW-7`: `C2_CALIBRATION` offline replay and policy freeze

Using only sealed C1 artifacts and no new FixedPred execution, compare A0,
A0+A1, A0+A1+A2, and A0+A1+A2+analytics, run baselines and nested ablations,
and select the simplest safe nearly non-dominated policy.

`ACCESS_SEALED_C1_ARTIFACTS`, `RUN_OFFLINE_REPLAY`, `SELECT_POLICY`, and
`FREEZE_POLICY` are permitted only here. `EXECUTE_FIXEDPRED`, new observation
collection, new oracle generation, and confirmatory access are forbidden. The
output is a frozen policy manifest and sealed C2 receipt.

## Stage 26 — `QW-8`: `C3_CONFIRMATORY`

On untouched model seeds, load the frozen policy and run shadow evaluation,
always completing the canonical suffix for post-action audit.

Decision order is immutable:

```text
safety
coverage
net cost
```

After partition opening, features, thresholds, analytic order, primary defect,
baselines, and cost mapping do not change.

## Stage 27 — `QW-9`: replication without retuning

With the same image digest and policy manifest, run one preregistered
replication, preferably MNIST with the same architecture. Policy or threshold
changes are forbidden. Transfer failure is an admissible result.

## Stage 28 — `QW-10`: synthesis, thesis, and publication gate

Integrate Stage 1/2, Stage 3A, B0, SI-MA0/1, B1/B2, EX-IF0, opportunity,
recognizability, confirmatory safety/coverage/cost, ablations, and replication.

Publication opens through a separate bounded decision only after sealed C1,
C2, C3, and replication receipts, or a preregistered decision not to run
replication.

Full plan: [bounded QWake-FP validation](docs/qwake-fp-experimental-plan_EN.md).

## Post-master's boundary — prospective PhD line

After the current critical path is complete, a separate `QWake-SPC` program may
move from QWake-PC
[spike-like control dynamics](docs/glossary_EN.md#term-spike-like-control-dynamics)
to native spikes, spike-native error transport, local learning, and
neuromorphic validation. This program is not Stage 21, does not open execution,
and does not change the master's-thesis completion criteria.
