# План рефакторинга `FixedPred` `sufficiency`

[English version](fixedpred-sufficiency-dus-refactoring-plan_EN.md)

**Статус:** план реализации; этим документом код и [выполнение](glossary.md#term-execution) не открываются.

## Назначение документа

Рефакторинг нужен не для изменения научного результата, а для предотвращения
смешения источников знания. Код, вычисляющий истинную достаточность по полному
продолжению траектории, должен быть физически отделён от кода пассивных
признаков и теневого решения. Такое разделение делает утечку после действия
проверяемым нарушением архитектуры, а не только договорённостью в тексте.
Отдельные типы для истинного состояния, теневого предложения и причины
резервного перехода сохраняют различие между тем, что известно после полного
вычисления, и тем, что было доступно до решения.

## 1. Цели

Рефакторинг должен разделить:

- `frozen` `evidence` и новый код;
- `oracle` и `pre-action` `features`;
- `decision` `semantics` и `acquisition` `policy`;
- `safety` и `cost` `optimization`;
- `canonical` `execution` и `shadow` `proposal`;
- `historical` `identifiers` и нормативную терминологию.

## 2. Новый `namespace`

```text
src/torch2pc_thesis/stage3b_sufficiency/
├── types.py
├── context.py
├── rosenbaum_control.py
├── snapshot.py
├── endpoint.py
├── oracle.py
├── margin.py
├── cost.py
├── registry.py
├── acquisition.py
├── policy.py
├── trace.py
├── validation.py
└── features/
```

## 3. Типы

```text
OracleStatus = SUFFICIENT | INSUFFICIENT
Decision = DONE | UNKNOWN | SWEEP
ReasonCode
EpochContext
CostVector
AnalyticResult
ShadowTraceRecord
```

`UNKNOWN` не входит в `OracleStatus`.

## 4. Изоляция `oracle`

Модули `features` не импортируют `oracle` `implementation` и не получают:

- полный `suffix`;
- $Y_{\mathrm{ref}}$;
- $M^*$;
- `post-action` `outcomes`;
- `oracle-optimal` `acquisition`.

Это закрепляется `architecture` `test`.

## 5. Интерфейс аналитики

Каждая аналитика имеет:

```text
analytic_id
acquisition_level
admissibility predicate
cost contract
pre_action_available=true
deterministic acquisition
```

Одна аналитика приобретается не более одного раза за `decision` `epoch`.

## 6. Последовательность рефакторинга

### `RF-0` — границы

Зафиксировать `successor` `ADR`, `allowed` `scope`, `forbidden` `paths` и `terminology` `map`.

### `RF-1` — чистые типы

Добавить `enums`, `dataclasses`, `schemas` и `serialization` `tests`.

### `RF-2` — `endpoint` и `margin`

Извлечь семантику `EX-IF0` без запуска научного выполнения.

### `RF-3` — `Rosenbaum` `control`

Добавить `explicit` `mapping` между индексами статьи, `PC` `layers` и `PyTorch` `modules`.

### `RF-4` — `immutable` `snapshot`

Запретить изменение `states`, `parameters`, `buffers`, `RNG` и `computation` `path`.

### `RF-5` — `finite` `analytic` `registry`

Запретить `dynamic` `discovery`, повторное `acquisition` и недетерминированный
`tie-break`.

### `RF-6` — `cost` `accounting`

Разделить `observer` `cost`, `analytic` `cost`, `marginal` `sweep` `cost` и `full-reference`
`cost`.

### `RF-7` — `shadow` `D`/`U`/`S`

`Policy` получает только `pre-action` `representation` и не управляет `execution`.

### `RF-8` — `trace`

Добавить `deterministic` `JSONL`, `reason` `codes` и полный `provenance`.

### `RF-9` — `compatibility`

Оставить `thin` `adapters` и `historical` `filenames` без переименования `frozen`
артефактов.

### `RF-10` — независимый аудит

Проверить `scope`, `imports`, `terminology`, `hashes`, `RU`/`EN` `parity` и `claim` `boundary`.

## 7. Запрещено

Рефакторинг не должен изменять `external/Torch2PC`, `canonical` `FixedPred`,
`frozen` `evidence`, `tags` или `hashes`; не должен читать `test` `split`, генерировать
`oracle` `labels` или активировать `policy`.
