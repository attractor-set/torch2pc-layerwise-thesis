# Stage 3B SI-MA0 — подтверждающий итог

**Contract:** `stage3b-si-ma0-v2`

**Evidence schema:** `stage3b-si-ma0-confirmatory-evidence-v1`

**Execution source/image:** `03016e68ecc7a850da7148d676f47acfb07cc99e`
**Независимая единица:** model seed, `n=10`

## Полнота

Подтверждающий набор содержит все десять model seeds, три фиксированных validation batches на seed и зарегистрированные количества raw records: 3000 state-update events, 600 output-error records, 150 observer-mode comparisons, 7500 total timing records, 52500 region timing records и 70 model-region summaries. Внутренние SHA256 manifests, внешние seed archives, checkpoint inventory, source commit и image revision проверены.

## Итоговые gates

- `prerequisites_verified`: `pass`
- `REC-MA0`: `pass`
- `OBS-MA0`: `pass`
- `VER-MA0`: `pass`
- `COST-MA0`: `fail`
- `CMP-MA0`: `pass`

Итоговое решение: `si_ma0_passed = false`. Evidence является полным, поэтому состояние решения — `fail`.

## Атрибуция стоимости

Доля каждой области сначала вычислена внутри model seed как сумма device time области, делённая на сумму полного `state_inference` device time. Bootstrap выполнен только по десяти model seeds (`10000` повторов, seed `20260715`).

| Область | Median | Q1 | Q3 | 95% bootstrap CI median |
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

Доля measured steps с accounting residual `<= 0.05`: `0.000000`. Доля прошедших repetition aggregates: `0.000000`. Медианный residual: `0.160608`, средний: `0.163658`. Frozen критерий COST-MA0 не выполнен.

## Контекст OBS-OH0

Ранее запечатанный ROCm joint-VJP observer control оценил primary overhead как `0.137634`, off-first overhead как `0.162849`. Масштаб близок к SI-MA0 residual, но это разные estimands и разные execution paths. Сопоставление является только описательным и не изменяет frozen COST-MA0 threshold или итоговый fail.

## Допустимый вывод

На зарегистрированных финальных FashionMNIST Strict checkpoints механизмная реконструкция PC-CATM, численная невозмущающесть наблюдения, согласованность версий и полнота provenance прошли на всех десяти model seeds. Строгое пятипроцентное замыкание стоимости по семи областям не прошло. Поэтому SI-MA0 в целом завершён как `fail` и не открывает интерпретацию NCZ/ECZ/TNZ или последующие B1/B2 gates. Отрицательный COST-MA0 сохраняется как результат, а не как основание для retuning или replacement.
