# Stage 3B B0: контракт статистического и инженерного анализа

[English version](STAGE3B-B0-ANALYSIS_EN.md)

Статус: **analysis implementation authorized; sealed B0 input read-only**.

Дата фиксации: 2026-07-14.

## 1. Область

Анализ использует только опубликованный каталог
`results/stage-3/profiling/b0/sealed-v1`. Повторный B0 execution не выполняется,
а committed evidence не перегенерируется и не изменяется.

Граница claims остаётся:

- `full_b0_campaign_complete=true`;
- `full_stage3b_campaign_complete=false`;
- `test_dataset_access=false`.

## 2. Статистическая единица

Независимая единица — `model_seed`. В каждой конфигурации доступны seeds
`70, 71, 72`, то есть `n=3`.

Repetitions, measured steps, profiling regions и cells являются вложенными или
контролируемыми инженерными наблюдениями. Они не увеличивают независимое `n`.
Из-за дискретности при `n=3` p-values не используются для claims о
превосходстве. Основные summaries — median, min, max и consistency направления
внутри matched конфигурации.

## 3. Зарегистрированные анализы

1. Paired `Strict` относительно `FixedPred` по ключам
   `depth × width × batch_size × model_seed`.
2. Device/host time и peak allocated/reserved memory.
3. Region attribution по пяти зарегистрированным profiling regions.
4. Нормализация region time как доля суммы region medians внутри cell.
5. Seed-level log2 main-effect scaling для depth, width и batch size.
6. VJP-region Amdahl upper-bound proxy как engineering continuation rule.
7. Проверка coverage structural locality fields.
8. Decision gate для candidate-specific B1/B2 equivalence work.

Region medians не считаются аддитивными к composite median. Поэтому attribution
доля является нормализованным инженерным индексом, а не бухгалтерским
разложением end-to-end времени.

## 4. Scaling model

Для каждого `method × model_seed × metric` оценивается:

```text
log2(metric) = intercept
             + beta_depth * log2(depth)
             + beta_width * log2(width)
             + beta_batch * log2(batch_size)
```

Публикуется `2 ** beta` как множитель при удвоении фактора, а также `R²` и
максимальный absolute log2 residual. Модель не содержит interactions и является
описательной sensitivity summary, а не универсальным законом сложности.

## 5. Engineering continuation rules

Из preregistration сохраняются thresholds:

- FixedPred speedup: не менее 15%;
- Strict speedup: не менее 20%.

Для baseline decision gate используется только верхний Amdahl proxy для
нормализованной доли `local_state_vjp + parameter_vjp`. Прохождение proxy gate
разрешает реализацию и candidate-specific numerical gates, но не разрешает
полную B1/B2 matrix до прохождения trajectory equivalence.

## 6. Locality boundary

B0 sealed aggregates поддерживают region-cost attribution. Claims о
многомерной локальности требуют отдельных structural fields:

- dependency radius;
- graph span/modules;
- independent lifetime;
- feedback operator;
- orchestration barriers.

При отсутствии этих полей locality claims блокируются и это сохраняется как
результат анализа, а не заполняется предположениями.

## 7. Производные outputs

Software pipeline создаёт отдельный `analysis-v1` root:

- paired configuration и matrix summaries;
- seed/configuration/matrix region attribution;
- paired region summaries;
- seed-level и matrix scaling summaries;
- `analysis_summary.json`;
- `analysis_metadata.json`;
- четыре deterministic PDF figures;
- bounded reports RU/EN;
- `SHA256SUMS`.

Analysis source commit и fixed generation timestamp фиксируются в metadata.
Output root создаётся только если отсутствует. Sealed input проверяется до и
после анализа.
