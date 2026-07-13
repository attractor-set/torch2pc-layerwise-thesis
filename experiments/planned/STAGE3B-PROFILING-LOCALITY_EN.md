# Stage 3B: profiling and locality preregistration

[Русская версия](STAGE3B-PROFILING-LOCALITY.md)

Status: **preregistered design; execution blocked**.

Freeze date: 2026-07-13.

## 1. Purpose and stage boundary

Stage 3B establishes the measurement basis for later claims about
locality, cost, and possible predictive-coding acceleration in Torch2PC.
The stage measures the existing implementation and exact candidates before
selecting any algorithm-changing approximation.

Stage 3B does not reopen Stage 1, Stage 2, or the published Stage 3A
diagnostics. The test dataset remains inaccessible. Profiling results are
not interpreted as evidence of universal superiority for any method.

## 2. Naming clarification

The early Stage 3 design revision 2 used the name `Stage 3A` for
profiling. After a separate diagnostic campaign was published under the
`stage3a-results-v1` tag, the next prospective stage is named
`Stage 3B profiling/locality`.

This is a prospective naming clarification:

- published Stage 3A commits, paths, manifests, and tags remain unchanged;
- historical documents retain their original wording;
- new implementation, execution, and publication artifacts use the
  `stage3b` prefix.

## 3. Immutable provenance baseline

| Role | Identifier |
|---|---|
| Project baseline | `b05e97c9917f06b1b46d84a259f2aa7de9f24379` |
| Stage 3A publication tag | `stage3a-results-v1` |
| Stage 2 execution source | `6d66b0a6f82c30c4fb8eca6247383ca13e0636a2` |
| Stage 2 publication state | `bb435432a65b76b7fc4f383b566b9a372fc346ae` |
| Patched Torch2PC | `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4` |

Stage 2 execution/publication tags and Stage 3A evidence tags are not
moved. The new campaign receives a separate commit and tag chain.

## 4. Research questions

### RQ-P1. Cost attribution

What fraction of CPU/device time, VJP/autograd calls, synchronization
points, saved tensor bytes, and peak memory is attributable to individual
`FixedPred` and `Strict` regions?

### RQ-P2. Multidimensional locality

How do algorithmic dependency radius, graph span, independent lifetime,
feedback operator, and orchestration barriers relate in actual Torch2PC
execution?

### RQ-P3. Scaling

How do depth, width, and batch size affect runtime, memory, VJP count, and
the locality profile under matched configurations?

### RQ-P4. Exact candidates

Do B1 `isolated_layer_vjp` and B2 `composite_vjp` change runtime or memory
after passing full-trajectory equivalence gates?

### RQ-P5. Exact-shortcut control

Does A0 `fixedpred_finite_step_control` preserve endpoint gradients and
one optimizer step within the locked scope, and what upper bound on
possible cost reduction does it provide?

## 5. Candidates and ordering

| ID | Candidate | Track | Permission to profile |
|---|---|---|---|
| B0 | `stage2_baseline` | baseline | after the non-perturbation gate |
| A0 | `fixedpred_finite_step_control` | exact shortcut | after the endpoint gate |
| B1 | `isolated_layer_vjp` | implementation-preserving | after CPU/GPU full-trajectory gates |
| B2 | `composite_vjp` | implementation-preserving | after CPU/GPU full-trajectory gates |

Execution order:

1. implement a non-perturbing profiler;
2. check instrumented B0 against uninstrumented B0;
3. perform B0/A0 smoke and attribution audit;
4. implement B1 in a separate commit and pass exact gates;
5. implement B2 in a separate commit and pass exact gates;
6. only then execute the full randomized matched profiling matrix.

B1 and B2 are not combined before a separate attribution analysis.

## 6. Profiling matrix

Controlled MLP family:

- depth: `4, 8, 16, 32`;
- width: `64, 256`;
- batch size: `64, 256`;
- model seeds: `70, 71, 72`.

Matrix:

```text
B0/B1/B2:
3 candidates × 2 methods × 4 depths × 2 widths × 2 batches × 3 seeds
= 288 matched cells

A0:
1 candidate × FixedPred × 4 depths × 2 widths × 2 batches × 3 seeds
= 48 matched cells

Total = 336 short matched cells
```

A0 applies only to `FixedPred`. B0/B1/B2 are profiled for `FixedPred` and
`Strict`.

## 7. Observation units and aggregation

The independent research unit is `model_seed`.

- a repetition is a technical replicate within a cell;
- measured steps are repeated measurements within a repetition;
- regions and layers are nested observations;
- they do not increase the independent `n`.

For each cell, the median is first calculated across measured steps within
a repetition and then across the five repetitions. Candidate comparisons
are paired within identical `method × depth × width × batch × model_seed`
settings.

Because profiling uses three model seeds, the primary analysis is
descriptive and engineering-oriented. Discrete p-values at `n=3` are not
used for scientific superiority claims.

## 8. Measurement protocol

Each cell uses:

- `20` warm-up steps;
- `50` measured steps;
- `5` repetitions;
- explicit device synchronization at predefined boundaries;
- hash-counterbalanced candidate order;
- the same resolved config for matched comparisons.

Primary regions:

- `initial_forward`;
- `state_inference`;
- `local_state_vjp`;
- `parameter_vjp`;
- `optimizer_step`.

Required metrics:

- host wall time;
- device time;
- VJP/autograd call count;
- explicit synchronization count;
- saved tensor bytes;
- peak allocated/reserved device memory;
- actual inference steps;
- graph modules and graph span;
- dependency radius;
- graph lifetime/freedom point;
- feedback operator type;
- non-finite and profiler-integrity events.

Runtime comparisons use identical synchronization rules. Instrumentation
cost is published separately and is not silently subtracted.

## 9. Locality taxonomy

The following measurements are published separately:

1. **algorithmic locality** — mathematical inputs to an update;
2. **dependency radius** — maximum distance to a referenced layer;
3. **graph locality** — modules and span of one autograd graph;
4. **execution locality** — independent build/execute/free capability;
5. **feedback locality** — exact, reused exact, or approximate operator;
6. **orchestration locality** — ordering, barriers, and synchronization points.

No single locality score is calculated. The structural gate
`dependency_radius <= 1` applies only to events preregistered as
mathematically layer-local.

## 10. Numerical and measurement gates

### 10.1. Profiler non-perturbation gate

Instrumented and uninstrumented B0 must agree on:

- beliefs and prediction errors;
- state updates;
- parameter gradients;
- one optimizer step;
- the actual number of inference steps.

Thresholds:

| Device | dtype | min cosine | max relative L2 |
|---|---|---:|---:|
| CPU | float64 | `0.99999` | `1e-7` |
| GPU | float32 | `0.999` | `1e-3` |

### 10.2. B1/B2 full-trajectory gate

B1 and B2 enter matched profiling only after full-trajectory agreement
within the same CPU/GPU thresholds.

### 10.3. A0 endpoint gate

A0 enters profiling after parameter gradients and one optimizer step
agree. Equivalence of the intermediate belief trajectory is not claimed.

### 10.4. Completeness gate

A cell is measurement-complete when:

- all five repetitions are stored;
- every repetition contains 50 measured steps;
- required regions and counters are present;
- no new non-finite events occur;
- resolved config, environment lock, and source identifiers are stored;
- the output manifest and SHA-256 checks pass.

An incomplete cell is retained as failed/incomplete and is not silently
replaced.

## 11. Engineering continuation rules

The following thresholds are engineering continuation rules rather than
superiority claims:

- FixedPred speedup: at least `15%`;
- Strict speedup: at least `20%`;
- baseline regression: at most `3%`;
- memory growth: at most `15%` without a separate ADR.

Absolute times, paired deltas, VJP reduction, memory change,
instrumentation overhead, and the Amdahl upper bound are also published.

## 12. Stop rules

A candidate or profiling block stops on:

- numerical-gate failure;
- optimizer-trajectory change in the implementation-preserving track;
- non-finite values;
- missing or inconsistent profiler events;
- insufficient optimizable fraction;
- an Amdahl upper bound below the continuation threshold;
- baseline regression above the locked boundary;
- uncontrolled memory growth;
- a violation of test isolation or the provenance chain.

Negative results and failed cells remain in the registry.

## 13. Test isolation

Stage 3B does not create a test loader or calculate test metrics.

Allowed inputs are:

- the synthetic scaling family for profiling;
- training/validation data where needed for smoke or gates;
- numerical controls on locked minibatches.

Test access can be enabled only by a separate commit after a later pilot
freeze. Successful profiling does not grant that permission automatically.

## 14. Planned outputs

Public evidence root:

```text
results/stage3/profiling/
```

Minimum output set:

- `profiling_cells.csv`;
- `profiling_repetitions.csv`;
- `locality_events.jsonl`;
- `profiling_summary.csv`;
- `analysis_metadata.json`;
- `environment-lock.json`;
- `SHA256SUMS`.

Metadata must include the project commit, Torch2PC commit, resolved config
hashes, environment versions, device identifiers, timing backend,
synchronization policy, timestamps, and input/output SHA-256 values.

## 15. Commit and tag chain

Recommended sequence:

1. `research: preregister Stage 3B profiling and locality`;
2. `feat: add non-perturbing Stage 3B profiler`;
3. `test: add Stage 3B profiler integrity gates`;
4. `research: lock Stage 3B profiling environment`;
5. `research: publish Stage 3B B0/A0 smoke evidence`;
6. separate B1/B2 implementation and gate commits;
7. execution commit/tag;
8. evidence commit;
9. checksum commit;
10. publication documentation commit/tag.

Planned tags:

- `stage3b-profiling-prereg-v1`;
- `stage3b-profiling-execution-v1`;
- `stage3b-profiling-results-v1`.

Execution and publication states are separate provenance points. History is
not rewritten, and force-push is not used for published branches or tags.

## 16. Permission to begin implementation

After this preregistration is merged, only profiler implementation and its
unit/integrity tests are authorized. The full profiling matrix remains
blocked until non-perturbation, environment-lock, and candidate-specific
gates have passed.
