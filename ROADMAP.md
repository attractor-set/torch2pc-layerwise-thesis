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

## Этап 15 — предварительная регистрация B1/B2 — текущий publication step

Заморожены B1 `isolated_layer_vjp`, B2 `composite_vjp`, общий обзор и ADR-014.
B1 implementation открывается после publication tag; B2 — после sealed
`EQ-B1`. Block/chunk B2 требует нового protocol.

## Этап 16 — B1/B2 implementation и candidate gates

- реализовать B1 отдельно и пройти deterministic/CPU controls;
- выполнить controlled ROCm smoke и full-trajectory `EQ-B1`;
- после sealed `EQ-B1` отдельно открыть B2;
- выполнить direct baseline/B2 и B1/B2 gates;
- открыть shared profiling только после `EQ-B1` и `EQ-B2`;
- сохранить отрицательные и смешанные результаты.

## Этап 17 — `EX-IF0`, passive diagnostics и `A11-OFF0`

После выбора допустимой exact implementation зафиксировать её до label
creation. Затем собирать passive PC-CATM representations и из идентичного
snapshot создавать policy-neutral ветви `stop`/`native_one`/`exact_one`,
сохраняя utility/regret, temporal history, feature cost, transitions и
provenance. Independent unit — `model_seed`; test split закрыт.

## Этап 18 — `A11-OFF1`, predictor, exact verification и shadow `QWake-PC`

- провести offline Pareto screening nested $\phi_k$, features и thresholds по
  regret, dangerous misses и полному cost vector;
- до confirmatory access заморозить representation, labels, split, Pareto rule
  и fallback;
- отдельно preregister predictor с split по `model_seed`;
- выполнить counterfactual exact verification из идентичного состояния;
- начать с shadow mode;
- hysteresis регистрировать как stop/wake thresholds, persistence и emergency
  `fallback_exact`, а не как замену utility;
- active allocation разрешать только после safety/end-to-end gates.

## Этап 19 — финальная фиксация и test evaluation

Зафиксировать implementation, features, thresholds, predictor, fallback и
statistical plan. Только затем разрешить однократную final test evaluation.

## Этап 20 — диссертация и статья

Объединить Stage 1/2, Stage 3A, B0, `SI-MA0`, `SI-MA1`, B1/B2 и доступные
Scenario A results. Невыполненные расширения маркируются как future work.
