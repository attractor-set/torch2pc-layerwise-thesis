# Stage 3B B1 confirmatory equivalence

[English version](STAGE3B-B1-CONFIRMATORY_EN.md)

## Статус

`preregistered_execution_closed`. Этот документ фиксирует подтверждающий
дизайн B1; execution request, batch artifacts, image, authorization и результаты
отсутствуют.

## Матрица

| Фактор | Значения |
|---|---|
| lane | `cpu_float64`, `rocm_float32` |
| method | `FixedPred`, `Strict` |
| model seed | `0`, `1`, `2` |
| validation batch index | `0..9` |

Полная мощность:

```text
2 × 2 × 3 × 10 = 120 matched pairs
```

Model seed — независимая единица. Остальные уровни вложены.

## Batch freeze

Batch indices `0..9` соответствуют первым десяти различным полным batch
validation loader, восстановленного из общего Stage 2 BP data protocol с
`shuffle=False`. Каждый batch сохраняется отдельно и проверяется собственным
SHA-256. Один batch не может занимать несколько индексов. Одинаковые batch
используются для всех model seed, methods и lanes. `include_test=false` и
`test_split_access=false` обязательны.

## Pair contract

Pair ID строится из `lane`, `method`, `model_seed`, `validation_batch_index`.
Перед reference и B1 восстанавливаются одинаковые model state, buffers,
beliefs, optimizer, RNG и batch. Primary equivalence использует `no_hooks`;
структурный replay выполняется отдельно в `counters_only`.

Пороги и компоненты наследуются без изменения из
`STAGE3B-B1-CONTRACT.json`. Threshold retuning, удаление outlier и замена
scientific failure запрещены.

## Открытие выполнения

Последующая opening ветка должна создать и проверить:

1. десять batch artifacts и десять manifests;
2. frozen request с 120 уникальными pair ID;
3. source commit, Torch2PC commit и immutable image digest;
4. checkpoint path/SHA-256 для seed `0..2`;
5. runtime preflight и явную authorization;
6. dry-run с `pending=120`.

До выполнения этих условий `EQ-B1-CONFIRMATORY` закрыт.

## Решение

Положительное решение обязано содержать:

```text
scope=confirmatory
confirmatory_equivalence_executed=true
registered_pair_count=120
observed_pair_count=120
failed_pair_count=0
sealed=true
status=pass
```

Оно открывает только confirmatory B2. Matched profiling остаётся закрытым до
положительного подтверждающего `EQ-B2`.
