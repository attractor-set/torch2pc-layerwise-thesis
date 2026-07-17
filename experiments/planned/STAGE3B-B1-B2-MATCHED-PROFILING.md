# Stage 3B B1/B2 matched profiling opening

[English version](STAGE3B-B1-B2-MATCHED-PROFILING_EN.md)

Статус: **scientific admission open; execution not authorized**.

## Основание открытия

Общий matched profiling открыт только после двух положительных и sealed решений:

- `EQ-B1`: `isolated_layer_vjp` прошёл зарегистрированные structural,
  numerical, trajectory, observer и provenance gates;
- `EQ-B2`: `composite_vjp` прошёл соответствующие gates, включая прямое
  B1/B2 comparison;
- оба решения имеют `status=pass`, `sealed=true` и `failed_pairs=[]`.

Открытие не переопределяет B1/B2 contracts и не превращает smoke evidence в
runtime или memory evidence.

## Замороженная matched matrix

Из исходного 336-cell Stage 3B manifest выбираются только:

- `stage2_baseline`: 96 cells;
- `isolated_layer_vjp`: 96 cells;
- `composite_vjp`: 96 cells.

Итого: 288 cells, по 144 для `FixedPred` и `Strict`. Сохраняются исходные
`block_id`, `cell_id`, dimensions, model seeds и counterbalanced candidate order.
A0 `fixedpred_finite_step_control` не входит в этот slice.

Протокол наследуется без изменений: 20 warm-up steps, 50 measured steps,
5 repetitions; независимая единица — `model_seed`.

## Что открыто и что закрыто

Открыта только научная допустимость создания candidate-aware matched runner и
последующей отдельной ROCm/float32 runtime freeze.

В этом slice:

- measurements не выполняются;
- runtime authorization не выдаётся;
- test split остаётся закрытым;
- `full_stage3b_campaign_complete=false`;
- `EX-IF0`, estimator, active `ECZ`, `QWake-PC`, controller actions и offline
  policy selection остаются закрытыми.

Машиночитаемые manifest/request создаются скриптом
`scripts/freeze_stage3b_matched_profiling.py` и должны детерминированно
воспроизводиться в режиме `--check`.
