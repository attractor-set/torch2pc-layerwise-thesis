# Реалистичный план магистерской диссертации

[English version](masters-thesis-plan_EN.md)

## 1. Текущая точка

На 16 июля 2026 года завершены `Stage` 1/2, `Stage` 3A, `Stage` 3B B0, `SI-MA0` и
`SI-MA1`. Итог `SI-MA1` опубликован тегом
`stage3b-si-ma1-confirmatory-v1`: `CAL-COST-MA1=true`, при этом отрицательный
`COST-MA0` сохранён. B0 и оба SI-эксперимента являются неизменяемыми
доказательными пакетами.

Текущий пакет завершает теоретическое предварительное условие B1/B2. Следующая
разрешённая работа — отдельная предварительная регистрация B1 и B2.

## 2. Основная научная линия

1. [PC-TREF](pc-tref-balanced-core.md) задаёт относительную к задаче
   эквивалентность, `diagnostic` `quotient`, `regret` и границы `sufficiency`.
2. [PC-CATM](pc-catm-operator-model.md) задаёт канонические каналы коррекции,
   `NCZ`, `ECZ`, `TNZ`, `state-error` `transport` и измерительные `norm` `contracts`.
3. [Scenario A](stage3b-primary-scenario-a.md) переводит теорию в
   последовательность `validity` `controls`, exact `candidates`, `passive` `diagnostics`,
   `predictor`, exact `verification` и `controller`.

## 3. Обязательный объём

### Уже завершено

- воспроизводимая ROCm/Docker среда и `frozen` `baselines`;
- `Stage` 3A `layer-wise` `evidence`;
- B0 `execution`, `sealing` и `engineering` `analysis`;
- `shortcut`/`observer`/`mechanism` `controls`;
- `SI-MA0` и `corrective` `SI-MA1`;
- операциональная семантика `PC-TREF`/`PC-CATM` и ADR-013.

### Обязательно до основной защиты

- `candidate-specific` `preregistration` и `gates` B1/B2;
- `EX-IF0` — фиксация допустимой exact `implementation`;
- `passive` `PC-CATM` `diagnostics` и сравнение зарегистрированных представлений;
- локальный `predictor` с `split` по `model_seed`;
- `counterfactual` exact `verification`;
- `shadow-mode` `evaluation` и итоговая `end-to-end` оценка;
- однократный `final` `test` после полной фиксации.

### Ограниченное дополнение

`PNZ`, дополнительные архитектуры или `datasets` и `active` `QWake-PC` включаются
только при сохранении обязательного пути и отдельном протоколе.

## 4. Уровни завершения

### `A-Min`

Теоретический пакет, B1/B2 `candidate` `gates`, `passive` `diagnostics` и сравнение
представлений опубликованы. Отрицательный результат кандидатов является
допустимым завершением механистической части.

### `A-Core`

Дополнительно завершены допустимый B1/B2 `path`, `EX-IF0`, `predictor`,
`counterfactual` exact `verification` и `shadow` `controller` с `regret`/`cost` `analysis`.

### `A-Max`

`Active` `control` и расширенная переносимость добавлены только после `safety` и
`end-to-end` `gates`.

## 5. Последовательность работ

### Июль–август 2026

- опубликовать теоретический пакет и ADR-013;
- подготовить раздельные B1/B2 `preregistration` `contracts`;
- зафиксировать `numerical-equivalence`, `regret`, `norms`, `cost` `vector` и `stop` `rules`;
- реализовать `deterministic`/`unit` `controls` после `tagged` `preregistration`.

### Сентябрь–октябрь 2026

- выполнить `controlled` ROCm `smoke` и `candidate-specific` `equivalence` `gates`;
- принять отдельные решения о допуске к `full` `profiling`;
- выполнить `matched` B1/B2 `confirmatory` `campaigns` для допущенных кандидатов;
- зафиксировать `EX-IF0`.

### Ноябрь 2026 – январь 2027

- собрать `passive` `PC-CATM` `features`;
- сравнить $\phi_0,\ldots,\phi_k$ по `regret`–`cost` `frontier`;
- определить `frozen` `representation` и `label` `protocol`;
- обучить `predictor` только на `development` `splits` по `model_seed`.

### Февраль–март 2027

- выполнить `counterfactual` exact `verification`;
- оценить `dangerous` `misses`, `unnecessary` `wakes`, `fallback` и `tail` `latency`;
- провести `shadow-mode` `QWake-PC` без изменения основного пути.

### Апрель–май 2027

- зафиксировать итоговую `implementation`/`threshold`/`predictor` `configuration`;
- выполнить однократную `final` `test` `evaluation`;
- закрыть `evidence` `manifests`, `bilingual` `reports` и `claim` `boundaries`.

### Июнь 2027

- консолидировать диссертацию, статью, ограничения и `future` `work`;
- провести воспроизводимый `release` `audit`.

## 6. Параллельное написание

Теоретическая глава `PC-TREF`/`PC-CATM`, `Stage` 3A, B0, `SI-MA0` и `SI-MA1`
могут писаться уже сейчас. Главы B1/B2 и управления обновляются только после
соответствующих `frozen` `evidence` `packages`.

## 7. Основные `endpoints`

- `numerical` `equivalence` `candidate`/`reference`;
- `decision` `regret` и `dangerous-miss` `rate`;
- `gradient`/`representation` `endpoints`;
- `device`/`wall` `time`, `memory`, `saved` `tensors` и `tail` `latency`;
- `diagnostic-mechanism`, `observer`, `control-plane` и `fallback` `costs`;
- `end-to-end` `utility` относительно `frozen` exact `reference`.

## 8. Статистический контракт

Независимая единица — `model_seed`. Вложенные `observations` агрегируются до
`seed-level`. `Primary` `estimand`, `direction`, `bootstrap` `seed`/`repetitions`,
`multiplicity` и `threshold` фиксируются заранее. `Test` `split` не участвует в
выборе.

## 9. Управление рисками

- провал B2 сохраняет B1 или `canonical` Strict;
- провал обоих кандидатов остаётся валидным отрицательным результатом;
- слабая диагностика оставляет `descriptive` `PC-CATM` `analysis`;
- высокий `regret` или `control-plane` `cost` блокирует `active` `control`;
- `timeline` защищается приоритетом `A-Min`, затем `A-Core`.

## 10. Граница вклада

Планируемый вклад — зарегистрированная, механизмно интерпретируемая и
`cost-aware` проверка того, какие различия состояния достаточно сохранять для
вычислительного решения при ограниченном `regret`. Работа не заявляет глобальную
теорию нуля или универсальную минимальность представления.
