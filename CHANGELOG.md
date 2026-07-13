# Журнал изменений

[English version](CHANGELOG_EN.md)

## [Unreleased] — Подготовка public visibility

### Изменено

- публичные README, STATUS, ROADMAP и publication plan синхронизированы с
  завершённым Stage 2;
- execution state и results/publication state описаны как разные provenance
  points;
- экспериментальные артефакты и их хэши не изменялись;
- версия проекта сохранена как `0.1.0` до отдельного решения автора о
  semantic-version milestone.

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
