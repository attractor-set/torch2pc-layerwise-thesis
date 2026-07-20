# Stage 3B B2 confirmatory equivalence

[English version](STAGE3B-B2-CONFIRMATORY_EN.md)

## Статус

`preregistered_execution_closed`. Документ фиксирует подтверждающий дизайн B2.
Frozen request, immutable image, runtime authorization и результаты отсутствуют.

## Предпосылка

Подтверждающий B1 завершён и запечатан:

```text
EQ-B1-CONFIRMATORY
scope=confirmatory
matched_pairs=120/120
failed_pairs=[]
sealed=true
status=pass
```

Существующий B2 smoke имеет только `12` троек и `24` сравнения и остаётся
инженерным evidence. Он не открывает production matched profiling.

## Матрица

| Фактор | Значения |
|---|---|
| lane | `cpu_float64`, `rocm_float32` |
| method | `FixedPred`, `Strict` |
| model seed | `0`, `1`, `2` |
| validation batch index | `0..9` |

Полная мощность:

```text
2 × 2 × 3 × 10 = 120 matched triples
```

[Зерно модели](../../docs/glossary.md#term-model-seed) остаётся независимой
единицей. Lane, method, batch, comparison, layer, sweep и tensor component —
вложенные единицы.

## Повторное использование входов

Подтверждающий B2 обязан использовать без изменения:

- registry десяти batch
  `experiments/frozen/stage3b-b1-confirmatory/validation-batches.json`;
- batch artifacts и manifests с индексами `0..9`;
- три checkpoint и resolved config из frozen B1 confirmatory request;
- B1 confirmatory decision и derived admission по зарегистрированным SHA-256.

Новая выборка batch не выполняется. Test split не создаётся и не читается.

## Triple и comparison contract

Triple ID строится из `lane`, `method`, `model_seed` и
`validation_batch_index`. Перед тремя кандидатами восстанавливаются одинаковые
model state, buffers, beliefs, optimizer, RNG и batch.

Каждая тройка создаёт ровно два зарегистрированных сравнения:

1. `stage2_baseline ↔ composite_vjp`;
2. `isolated_layer_vjp ↔ composite_vjp`.

Итого обязательны `120` уникальных triple ID и `240` pairwise comparisons.
Primary equivalence использует `no_hooks`; структурный replay — отдельный
`counters_only` контур.

## Жизненный цикл

История попыток append-only. На одну тройку допускается не более двух попыток.
Повтор возможен только после infrastructure, operator interruption или system
interruption. Correctness, scientific, provenance и unknown failures
non-retryable и блокируют sealing.

## Открытие выполнения

Отдельная opening ветка должна создать и проверить:

1. frozen request с `120` уникальными triple ID;
2. точные ссылки и SHA-256 reused B1 batches/checkpoints;
3. B1 confirmatory decision/admission и B2 contracts;
4. source commit, Torch2PC commit и immutable image digest;
5. разделённый preflight для `cpu_float64` и `rocm_float32`;
6. явную runtime authorization;
7. dry-run с `pending=120` и пустым output root.

До прохождения этих условий confirmatory execution закрыт.

## Решение и следующий переход

Положительное научное решение обязано содержать:

```text
decision_id=EQ-B2-CONFIRMATORY
scope=confirmatory
confirmatory_equivalence_executed=true
matched_triples_expected=120
matched_triples_observed=120
pairwise_comparisons_expected=240
pairwise_comparisons_observed=240
failed_pairs=[]
sealed=true
status=pass
```

После него создаётся отдельный derived admission `EQ-B2` с теми же
confirmatory counts. Только этот admission разрешает новую версию
matched-profiling request/manifest. Он не разрешает 288-cell execution,
`EX-IF0`, QWake-PC или test split.
