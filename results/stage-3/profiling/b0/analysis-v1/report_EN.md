# Stage 3B B0: statistical and engineering analysis

[Русская версия](report.md)

## Scope and statistical unit

The analysis reads the published sealed B0 evidence without rerunning the
campaign. The independent unit is `model_seed`, with three seeds per
configuration. Results are therefore descriptive engineering estimates. Cells,
regions, steps, and repetitions do not increase the independent `n`, and
discrete p-values at `n=3` are not used for superiority claims.

The publication boundary remains:

- `full_b0_campaign_complete=true`;
- `full_stage3b_campaign_complete=false`;
- the test dataset was not accessed.

## Strict relative to FixedPred

The median configuration-level Strict/FixedPred ratio was:

| Metric | Median | Configuration range |
|---|---:|---:|
| Device time | 2.327× | 1.966–2.619× |
| Host time | 2.327× | 1.969–2.619× |
| Peak allocated memory | 1.328× | 1.068–2.160× |
| Peak reserved memory | 1.323× | 1.064–2.058× |

Strict is more expensive than FixedPred in every configuration median for time
and peak memory. This is a bounded observation for the synthetic scaling family,
ROCm/float32, and the pinned implementation rather than a universal ranking.

## Bottleneck attribution

The analysis normalizes each region by the sum of the five region medians within
the cell. Region medians are not assumed to be additive to the composite median.

| Method | Dominant region | State inference | VJP regions | Amdahl proxy |
|---|---|---:|---:|---:|
| FixedPred | `state_inference` | 71.8% | 26.7% | 1.364× |
| Strict | `state_inference` | 78.8% | 20.5% | 1.258× |

`state_inference` is the dominant device-time region for both methods. The VJP
proxy exceeds the preregistered continuation thresholds, but it is only an
engineering upper bound under hypothetical removal of the normalized
`local_state_vjp + parameter_vjp` share.

Saved tensors in `state_inference`:

| Method | Median mean saved-tensor bytes | MiB |
|---|---:|---:|
| FixedPred | 3352832 | 3.20 |
| Strict | 40227920 | 38.36 |

The Strict/FixedPred ratio is
`11.998×`. This
identifies a separate graph-retention/memory bottleneck inside
`state_inference`, while remaining distinct from peak allocated/reserved memory.

## Scaling

Median per-doubling multipliers from seed-level log2 main-effect models:

| Method | Metric | Depth | Width | Batch size |
|---|---|---:|---:|---:|
| FixedPred | Device time | 1.941× | 0.998× | 0.999× |
| Strict | Device time | 2.089× | 1.000× | 1.001× |
| FixedPred | Peak allocated | 1.544× | 2.097× | 1.237× |
| Strict | Peak allocated | 1.384× | 2.084× | 1.399× |

The models omit interaction terms and are compact engineering-matrix
sensitivities rather than universal complexity laws.

## Locality boundary

Published B0 aggregates support region-cost attribution but do not contain the
full structural locality contract: dependency radius, graph span/modules,
independent lifetime, feedback operator, and orchestration barriers. Claims
about multidimensional locality therefore remain blocked.

## Decision gate

- B1/B2 candidate-specific equivalence work: **continue**;
- full B1/B2 matched profiling: **blocked_pending_candidate_specific_gates**;
- locality claims: **blocked_by_missing_structural_evidence**;
- new B0 execution: **not_required**.

The decision authorizes implementation and candidate-specific numerical gates
only. Full Stage 3B and comparative candidate profiling remain incomplete.

## Artifacts

- `paired_configuration_summary.csv`;
- `paired_matrix_summary.csv`;
- `region_seed_attribution.csv`;
- `region_configuration_summary.csv`;
- `region_matrix_summary.csv`;
- `region_paired_configuration_summary.csv`;
- `scaling_seed_effects.csv`;
- `scaling_summary.csv`;
- four PDF figures;
- `analysis_summary.json`, `analysis_metadata.json`, and `SHA256SUMS`.
