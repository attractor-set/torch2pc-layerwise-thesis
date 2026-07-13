# Журнал изменений

[English version](CHANGELOG_EN.md)

## [Unreleased] — Stage 3 design-ready

### Добавлено

- подробный двуязычный протокол Stage 3 по locality, approximation и scaling;
- ADR-006 с границами Stage 3, ADR-007 с locality taxonomy и ADR-008 с predict-correct acceleration;
- design contract `configs/stage3/design.yaml`;
- profiling, pilot и final-template конфигурации Stage 3;
- candidate overlays B0/B1/B2/C1/C2/C3;
- locality trace schema, profiling contract и structural locality gate;
- контролируемое MLP family для depths 4/8/16/32 и widths 64/256;
- deterministic Stage 3 design plan: 288 profiling и 48 parameterized screening cells;
- readiness CLI/Make targets и execution guards;
- тесты, сохраняющие Stage 3 execution заблокированным до candidates, gates и
  freeze.

### Изменено

- RQ6–RQ10 добавлены без изменения завершённых Stage 1/2;
- README, STATUS, ROADMAP, документация и структура проекта отражают активную
  подготовку Stage 3;
- public visibility phase отмечена завершённой;
- версия проекта остаётся `0.1.0` до отдельного version milestone.

## [stage2-results-v1] — 2026-07-13

### Добавлено

- Stage 2: 80/80 completed на patched Torch2PC
  `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4`;
- Stage 2 execution source
  `6d66b0a6f82c30c4fb8eca6247383ca13e0636a2`;
- results/publication state
  `bb435432a65b76b7fc4f383b566b9a372fc346ae`;
- CPU/GPU original-vs-patched numerical gates;
- cross-version pair records и summary;
- implementation-equivalence audit для `torch2pc-patched-v1`;
- release tooling и regression coverage до 63 passing tests;
- replication bundle с raw Stage 2 artifacts, archive SHA-256 и file manifest;
- проверка 660 manifest artifacts.

### Наблюдалось

- парные Stage 1/2 test accuracy и macro-F1 совпали;
- BP runtime практически не изменился;
- Exact приблизился к BP и ускорился примерно на 14% относительно Stage 1;
- FixedPred ускорился примерно на 31%;
- Strict ускорился примерно на 26%;
- порядок времени Stage 2: `BP ≈ Exact < FixedPred << Strict`.

## [stage2-execution-v1]

Execution tag фиксирует код, использованный для Stage 2, отдельно от
последующего results state. Экспериментальный протокол Stage 1 был сохранён;
контролируемой интервенцией являлась закреплённая реализация Torch2PC.

## [confirmatory-final-v1]

- Stage 1: 80/80 completed, 0 failed;
- исходный Torch2PC:
  `00c6c50ee3540537bbb56ab2b6567b541f42b093`;
- source lock: `140e77cc2083bf04234dcea16b95803e63cb0537`;
- validation-only pilot до Stage 1: 96/96, test не вычислялся;
- выбранные параметры: FixedPred `eta=0.1`, `n=10`; Strict `eta=0.05`,
  `n=20`.

## [0.1.0] — Первый коммит

Добавлены нейтральная исследовательская позиция, preregistration draft, test
isolation, pilot-freeze gate, append-only registry, фиксируемые splits и
checksums, контейнерная Ubuntu/ROCm-среда, статистические utilities, статические
проверки и каркас диссертации/статьи. Эта запись описывает исходный scaffold до
получения эмпирических результатов.
