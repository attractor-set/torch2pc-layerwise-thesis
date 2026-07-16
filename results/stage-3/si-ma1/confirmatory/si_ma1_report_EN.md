# Stage 3B SI-MA1 — final confirmatory report

## Decision

**CAL-COST-MA1: PASS.**

- Observed median `D_seed`: `-0.190635073373`.
- One-sided 95% bootstrap upper bound: `-0.188621876160`.
- Registered threshold: `0.010000000000`.
- Bootstrap: `10000` resamples, seed `20260716`.
- Resampling unit: independently trained model (`model_seed`).

Decision rule: `CAL-COST-MA1 = upper_bound <= 0.01`.
Signed values were retained without truncation.

## Model-seed values

| model_seed | D_seed |
|---:|---:|
| 0 | -0.187972485458 |
| 1 | -0.191186514448 |
| 2 | -0.180166985312 |
| 3 | -0.190691093465 |
| 4 | -0.190579053280 |
| 5 | -0.190193127024 |
| 6 | -0.195711199375 |
| 7 | -0.201173567696 |
| 8 | -0.188621876160 |
| 9 | -0.207881278205 |

## Scientific boundary

SI-MA1 calibrates observer cost for the existing `state_inference`
implementation. It does not rewrite the negative SI-MA0 result, include ECZ
evaluator cost, or establish end-to-end B1/B2 savings.
