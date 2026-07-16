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

## Этап 14 — теоретическая фиксация перед B1/B2 — текущий publication step

- разделить partition-based quotient и нетранзитивную threshold proximity;
- определить required equivalence и safety через decision regret;
- формализовать task-relative defect;
- закрепить precision-masked zero и explicit norm contracts;
- использовать cost vector и preregistered scalarization/Pareto rule;
- разделить diagnostic-mechanism, observer и control-plane costs;
- зафиксировать решение в `ADR-013`;
- обновить двуязычную документацию без изменения sealed evidence.

После merge и тега этого пакета теоретический prerequisite B1/B2 считается
выполненным.

## Этап 15 — B1/B2 preregistration — следующий

Для B1 isolated-layer probe и B2 composite/block-composite probe подготовить
раздельные candidate contracts. Каждый контракт фиксирует:

- frozen reference и candidate implementation boundary;
- state, belief и RNG restoration;
- numerical-equivalence endpoints и tolerances;
- norm contracts;
- decision regret, dangerous-miss и fallback semantics;
- cost vector и primary selection rule;
- execution matrix, independent unit и replacement policy;
- immutable provenance and evidence layout.

Preregistration не означает implementation permission.

## Этап 16 — B1/B2 implementation и candidate gates

После tagged preregistration:

- реализовать кандидатов в отдельной ветке;
- выполнить deterministic и CPU structural tests;
- выполнить controlled ROCm smoke;
- проверить numerical equivalence до full profiling;
- сохранить отрицательные и смешанные результаты;
- открыть confirmatory execution только отдельным decision gate.

## Этап 17 — `EX-IF0` и passive diagnostics

После выбора допустимой exact implementation зафиксировать её до label
creation. Затем собирать passive PC-CATM representations и сравнивать
зарегистрированные $\phi_k$ по regret/cost frontier.

## Этап 18 — predictor, exact verification и `QWake-PC`

- split по `model_seed`;
- counterfactual exact verification из идентичного состояния;
- shadow mode first;
- active full-sweep allocation только после safety и end-to-end runtime gates;
- control-plane cost измеряется отдельно.

## Этап 19 — финальная фиксация и test evaluation

Зафиксировать implementation, features, thresholds, predictor, fallback и
statistical plan. Только затем разрешить однократную final test evaluation.

## Этап 20 — диссертация и статья

Объединить Stage 1/2, Stage 3A, B0, `SI-MA0`, `SI-MA1`, B1/B2 и доступные
Scenario A results. Невыполненные расширения маркируются как future work.
