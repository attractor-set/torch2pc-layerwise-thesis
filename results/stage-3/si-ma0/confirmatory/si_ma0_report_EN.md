# Stage 3B SI-MA0 — confirmatory result

**Contract:** `stage3b-si-ma0-v2`

**Evidence schema:** `stage3b-si-ma0-confirmatory-evidence-v1`

**Execution source/image:** `03016e68ecc7a850da7148d676f47acfb07cc99e`
**Independent unit:** model seed, `n=10`

## Completeness

The confirmatory evidence contains all ten model seeds, the three frozen validation batches per seed, and all registered raw-record counts: 3000 state-update events, 600 output-error records, 150 observer-mode comparisons, 7500 total timing records, 52500 region timing records, and 70 model-region summaries. Internal SHA256 manifests, external seed archives, checkpoint inventory, source commit, and image revision were verified.

## Final gates

- `prerequisites_verified`: `pass`
- `REC-MA0`: `pass`
- `OBS-MA0`: `pass`
- `VER-MA0`: `pass`
- `COST-MA0`: `fail`
- `CMP-MA0`: `pass`

Final decision: `si_ma0_passed = false`. The evidence is complete, so the decision state is `fail`.

## Cost attribution

Each region share was first computed within model seed as summed region device time divided by summed full `state_inference` device time. Bootstrap resampling used only the ten model seeds (`10000` repeats, seed `20260715`).

| Region | Median | Q1 | Q3 | 95% bootstrap CI median |
|---|---:|---:|---:|---:|
| `inference_setup` | 0.000960 | 0.000954 | 0.000963 | [0.000953, 0.000965] |
| `lower_prediction_and_error` | 0.368232 | 0.367077 | 0.368929 | [0.366270, 0.369518] |
| `upper_state_vjp` | 0.271182 | 0.270723 | 0.272472 | [0.269901, 0.272749] |
| `component_aggregation` | 0.078261 | 0.077276 | 0.079254 | [0.077151, 0.079463] |
| `belief_update` | 0.096229 | 0.095222 | 0.096406 | [0.094845, 0.096490] |
| `sweep_bookkeeping` | 0.018431 | 0.018382 | 0.018599 | [0.018374, 0.018712] |
| `inference_finalize` | 0.000150 | 0.000132 | 0.000176 | [0.000130, 0.000179] |
| `unattributed_residual` | 0.167211 | 0.166149 | 0.167843 | [0.166074, 0.168027] |

## COST-MA0

Fraction of measured steps with accounting residual `<= 0.05`: `0.000000`. Passing repetition-aggregate fraction: `0.000000`. Median residual: `0.160608`; mean residual: `0.163658`. The frozen COST-MA0 criterion failed.

## OBS-OH0 context

The previously sealed ROCm joint-VJP observer control estimated primary overhead at `0.137634` and off-first overhead at `0.162849`. The scale is close to the SI-MA0 residual, but the estimands and execution paths differ. The comparison is descriptive only and does not override the frozen COST-MA0 threshold or final failure.

## Allowed conclusion

Across the registered final FashionMNIST Strict checkpoints, PC-CATM mechanism reconstruction, numerical observer non-interference, version coherence, and provenance completeness passed for all ten model seeds. The strict five-percent cost closure over the seven registered regions failed. SI-MA0 therefore ends as `fail` and does not open NCZ/ECZ/TNZ interpretation or the subsequent B1/B2 gates. The negative COST-MA0 result is retained rather than used to justify retuning or replacement.
