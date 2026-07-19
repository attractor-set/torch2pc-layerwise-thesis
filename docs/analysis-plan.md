# План анализа

[English version](analysis-plan_EN.md)

## Принципы

Анализ выполняется только после `frozen` `protocol` и `provenance` `check`. Основной
уровень вывода — `model_seed`. `Signed` результаты сохраняются; значения не
обрезаются к нулю, неудобные `seeds` не исключаются постфактум, а `exploratory`
результаты отделяются от `confirmatory`.

## Завершённые анализы

- `Stage` 1/2: качество, время и сопоставимость методов;
- `Stage` 3A: `gradient` `cosine`, `relative` L2, `norm` `ratio`, `sign` `agreement`, CKA, RSA,
  `cross-layer` CKA и `depth` `statistics`;
- `Stage` 3B B0: `matched` `time`/`memory`, `region` `attribution` и `saved` `tensors`;
- `SI-MA0`: `reconstruction`, `observer`, `version`, `cost` и `comparison` `gates`;
- `SI-MA1`: `observer-calibrated` `closure` с `bootstrap` по `model_seed`.

`SI-MA0` и `SI-MA1` анализируются как последовательные отдельные эксперименты.
Первый результат не заменяется вторым.

## Теоретические операциональные определения

Exact `diagnostic` `quotient` требует `partition` `map` $q_I$. Для непрерывных
признаков допускается
[операциональная диагностическая неразличимость](glossary.md#term-operational-diagnostic-indistinguishability),
но её транзитивность не предполагается. `Safety` оценивается через
[regret решения](glossary.md#term-decision-regret), `dangerous` `misses` и `fallback`,
а не через буквальное равенство признаков.

Каждая норма и [ноль, маскированный точностью](glossary.md#term-precision-masked-zero)
имеют зарегистрированный `measurement` `contract`. Агрегация по слоям и времени
выполняется только после разрешённой нормировки.

## B1/B2: предварительная регистрация анализа

Для B1 и B2 отдельно фиксируются:

- `candidate`/`reference` `pair` и `scope`;
- `primary` `numerical-equivalence` `endpoint`;
- абсолютный и/или относительный `tolerance` с `zero-denominator` `rule`;
- `safety` `endpoint`, $\delta_R$ и допустимый `dangerous-miss` `rate`;
- `independent` `unit` `model_seed` и вложенная структура;
- `execution` `matrix`, `order` `balancing` и `replacement` `policy`;
- [вектор стоимости](glossary.md#term-cost-vector);
- `scalarization` или [Pareto-допустимость](glossary.md#term-pareto-admissibility);
- `multiplicity`, `bootstrap`/`random` `seed`, число повторов и `decision` `rule`;
- `stop`/`fallback` `rules` и условия открытия `full` `profiling`.

## `Primary` `candidate` `gates`

1. **`NUM-B1`/B2:** `candidate` соответствует `frozen` `reference` в пределах
   зарегистрированных численных `tolerances`.
2. **`STATE`:** состояние, `beliefs` и `RNG` восстановлены перед `matched` `arms`.
3. **`SAFETY`:** `regret`/`dangerous-miss` не превышают зарегистрированный предел.
4. **`COST`:** выигрыш сохраняется после раздельного учёта `diagnostic-mechanism`,
   `observer`, `control-plane` и `fallback` `costs`.
5. **`CMP`:** `cardinality`, `provenance`, `manifests` и `planned` `comparisons` полны.

Провал `numerical-equivalence` или `safety` `gate` закрывает `candidate` для
`confirmatory` `profiling`. Провал `cost` `gate` сохраняет научный результат, но не
разрешает утверждение об ускорении.

## Будущий анализ политики после `EX-IF0`

До `EX-IF0` `ECZ` остаётся пассивной диагностической категорией и не управляет
выполнением. После фиксации точной реализации разрешается отдельный
контрфактический анализ только на разработочных данных. Базовые ветви
`stop`/`native_one`/`exact_one` сохраняют значение офлайн-меток, заданное
B1/B2-контрактами. `Exact-reference` отдельно создаёт `oracle` `skip` `regret` и
`oracle`-запас $M^*$; `pre-action` оцениватель $\widehat M_b$ проверяется как
предиктор этой метки согласно
[`PC-TREF-SB`](pc-tref-sufficiency-boundary.md), а не определяется через
собственный прогноз.

Ветвь `local_sweep(block_id)` может появиться только в новом предварительно
зарегистрированном протоколе. `ECZ` выбирает [кандидат](glossary.md#term-candidate)
блока, но не доказывает полезность локального действия. До включения локального
прохода в семейство политик обязательна `exact_verification`:

```text
same restored state
→ proposed local_sweep(block_id)
→ full_exact
→ endpoint utility/regret comparison
```

Офлайн-отбор выполняется в фиксированном порядке:

1. `cost_feasibility`;
2. `safety` с правилом `zero_dangerous_misses`;
3. `net_efficiency` по полному [вектору стоимости](glossary.md#term-cost-vector);
4. отбор по Парето с результатом `0–3` финалиста.

Результат `0` допустимых политик является полноценным научным результатом.
Финалисты, представление, признаки, разбиение, пороги, [резервный переход](glossary.md#term-fallback) и
гистерезис замораживаются до подтверждающей оценки в теневом режиме. Активное
управление запрещено до появления положительных доказательных материалов
теневого режима; `A-Max` рассматривается только как условное расширение.

Нормативные документы:
[QWake-PC](glossary.md#term-qwake-pc) и его [проект](qwake-pc-design.md),
[проект локального прохода по ECZ](ecz-targeted-local-sweep.md) и
[граница будущей политики](stage3b-future-policy-boundary.md).

## `Secondary` `analyses`

- `layer`, `dataset`, `method` `and` `seed` `heterogeneity`;
- `sensitivity` to `prespecified` `norm`/`threshold` `variants`;
- `order` `and` `thermal` `effects`;
- `descriptive` `relation` `between` `PC-CATM` `features` `and` `candidate` `error`;
- `regret`–`cost` `frontier` `across` `registered` `representations`;
- `fallback` `frequency` `and` `tail` `latency`.

`Secondary` `analyses` не изменяют `primary` `decision`.

## Полнота и публикация

Публикуются `raw` `retained` `attempts`, `compact` `derived` `tables`, `machine-readable`
`summary`/`decision`, `bilingual` `report`, `environment` `record` и `SHA256SUMS`.
`Aggregation` не изменяет `raw` `evidence`. `Test` `split` не используется до отдельного
`final-evaluation` `contract`.
