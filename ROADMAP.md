# Дорожная карта

[English version](ROADMAP_EN.md)

Дорожная карта отделяет завершённые этапы от разрешённой и заблокированной
работы. Переход требует проверенных артефактов, сохранения границ утверждений и
отдельного решения о допуске.

## Этапы 1–10 — завершены

Завершены инфраструктура и pilot, Stage 1/2, Stage 3A, Stage 3B B0 evidence и
B0 statistical/engineering analysis. Test split оставался закрытым на Stage 3A
и Stage 3B.

Публикационные теги включают `stage3a-statistical-publication-v1`,
`stage3b-b0-evidence-v1` и `stage3b-b0-analysis-evidence-v1`.

## Этап 11 — Scenario A и исходная теория — завершён

`ADR-012` закрепил PC-TREF Balanced Core, PC-CATM и Scenario A. `ECZ` имеет
единственное значение `Error-Cancellation Zone`; B0 остаётся неизменяемой
базовой линией.

## Этап 12 — validity controls и `SI-MA0` — завершён

Завершены shortcut/equivalence controls, observer non-interference,
deterministic mechanism controls и `SI-MA0` mechanism attribution.

`SI-MA0` прошёл `REC`, `OBS`, `VER` и `CMP`, но не прошёл `COST`; global result
сохранён как fail. Непокрытый residual стал основанием для отдельного
observer-calibration эксперимента, а не для изменения frozen contract.

## Этап 13 — `SI-MA1` observer-calibrated closure — завершён

- preregistration: `stage3b-si-ma1-prereg-v1`;
- implementation: `stage3b-si-ma1-implementation-v1`;
- confirmatory execution: `stage3b-si-ma1-confirmatory-execution-v1`;
- final decision: `stage3b-si-ma1-confirmatory-v1`;
- 10 model seeds, 180 matched blocks;
- one-sided bootstrap upper bound below threshold `0.01`;
- `CAL-COST-MA1=true`, `SI-MA1=pass`;
- `SI-MA0` unchanged; `ECZ` evaluator cost excluded.

## Этап 14 — теоретическая фиксация перед B1/B2 — завершён

Операциональная semantics PC-TREF/PC-CATM, regret, norm contracts, precision-
masked zero, cost vector и разделение costs опубликованы под ADR-013.

## Этап 15 — предварительная регистрация B1/B2 — завершён

Заморожены B1 `isolated_layer_vjp`, B2 `composite_vjp`, общий обзор и ADR-014.
Публикационный тег `stage3b-b1-b2-prereg-v1` сохраняет эти определения
неизменными. `ECZ`, локальные проходы и `QWake-PC` не входят в B1/B2 и не могут
быть добавлены к ним ретроспективно.

## Этап 16 — B1/B2 implementation и candidate gates — текущий этап

B1 implementation и B1 equivalence smoke harness слиты в `main`. Следующий
разрешённый шаг — отдельное выполнение CPU `float64` и ROCm `float32` smoke,
агрегация полной траектории и sealed `EQ-B1`.

- B2 остаётся закрыт до положительного sealed `EQ-B1`;
- shared profiling остаётся закрыт до положительных `EQ-B1` и `EQ-B2`;
- scientific failures сохраняются;
- design-only обновления будущей политики не блокируют B1 smoke execution.

## Этап 17 — `EX-IF0`, пассивная диагностика и нейтральные ветви

После `EQ-B1`, `EQ-B2` и matched exact-candidate profiling выбрать допустимую
точную реализацию и зафиксировать `EX-IF0` до создания policy labels. Затем
выполнить `A11-OFF0`: собирать пассивные представления PC-CATM и из
идентичного snapshot создавать замороженные B1/B2-контрактами ветви `stop`/`native_one`/`exact_one`.
Эти ветви остаются офлайн-метками и не являются действиями контроллера.

Активное использование `ECZ` до `EX-IF0` запрещено. Подробные границы:
[future-policy boundary](docs/stage3b-future-policy-boundary.md).

## Этап 18 — `A11-OFF1`, ECZ-targeted local sweep и offline screening

После `EX-IF0` отдельная предварительная регистрация может добавить
контрфактическую ветвь `local_sweep(block_id)`. `ECZ` разрешает только выбор
кандидата блока; полезность локального действия должна пройти отдельный
`exact_verification` gate относительно `full_exact`.

Отбор выполняется последовательно:

1. `cost_feasibility`: полная стоимость политики должна быть ниже стоимости
   соответствующего полного точного прохода;
2. `safety`: допустимо ровно `zero_dangerous_misses`;
3. `net_efficiency`: учитываются диагностика, предиктор, локальный проход,
   резервные переходы и управляющий контур;
4. Pareto screening выбирает `0–3` финалистов, не гарантируя наличие хотя бы
   одного допустимого кандидата.

Только после отдельной `predictor`/controller preregistration выполняется
shadow-режим иерархии:

```text
stop
→ ECZ-targeted local sweep
→ full exact sweep
→ fallback_exact
```

`controls_execution=false` сохраняется до прохождения shadow safety и
end-to-end cost gates. `A-Max` является условным расширением и открывается
только после положительных shadow evidence. Подробности:
[QWake-PC design](docs/qwake-pc-design.md) и
[ECZ local-sweep design](docs/ecz-targeted-local-sweep.md).

## Этап 19 — финальная фиксация и test evaluation

Зафиксировать implementation, features, thresholds, predictor, fallback и
statistical plan. Только затем разрешить однократную final test evaluation.

## Этап 20 — диссертация и статья

Объединить Stage 1/2, Stage 3A, B0, `SI-MA0`, `SI-MA1`, B1/B2 и доступные
Scenario A results. Невыполненные расширения маркируются как future work.
