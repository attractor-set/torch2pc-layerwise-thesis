# Журнал изменений

[English version](CHANGELOG_EN.md)

## [Unreleased] — синхронизация документации после Stage 3B B0 publication

### Изменено

- README, STATUS, ROADMAP и индексы документации синхронизированы с
  опубликованным Stage 3B B0 evidence;
- следующий этап определён как `stage3b-b0-analysis-v1`, а не повторный B0
  execution или preregistration;
- статические числа passing tests удалены из текущего статуса; источником
  актуального regression status является CI;
- граница результатов явно сохраняет
  `full_stage3b_campaign_complete=false`.

### Сохранено неизменным

- Stage 1/2, Stage 3A и Stage 3B B0 committed evidence;
- execution, sealing и publication provenance;
- существующие tags и GitHub Releases;
- raw canonical archive вне Git.

## [stage3b-b0-evidence-v1] — 2026-07-15

### Добавлено

- Stage 3B B0 ROCm/float32 canonical campaign: 96/96 cells, 0 failed;
- fresh Python child process per cell: 96 process records и 96 unique child PID;
- compact derived evidence: 96 cell, 480 region, 48 paired и 32 configuration
  rows;
- validation, metric definitions, content-addressed seal и `SHA256SUMS`;
- Git-stable LF serialization для evidence CSV;
- GitHub tag и Release `stage3b-b0-evidence-v1`.

### Provenance

- execution source: `95c25d35224abd5e741f1df9327662ff2fde23ad`;
- sealing source: `caa226cc1cd5d4aa0f9772c1fb997f7388d60730`;
- publication state: `ed0d48063a17e2d9c6679869a4d930f933877052`;
- archive inventory:
  `9abc6434b0f59b510e14ef0ad09d5c3b92a4a9472a90974cb92cdb1657e232ed`;
- seal digest:
  `6a3d61838810e559a39f13e6ac39d6b22624c21d72523bddb55c33e83063c93e`.

### Граница утверждений

- B0 measurement baseline завершён и разрешён к публикации;
- test dataset не использовался;
- полный Stage 3B остаётся незавершённым;
- сравнительные claims о времени, памяти и scaling переносятся в отдельный B0
  analysis.

## [stage3a-statistical-publication-v1] — Stage 3A statistical publication

### Добавлено

- итоговый двуязычный отчёт `docs/stage3a-statistical-results*.md`;
- seed-level confirmatory statistics: 40 gradient и 20 representation
  comparisons;
- confirmatory depth analysis: 180 seed-level и 24 statistical rows;
- 8 publication PDF figures, metadata и отдельный figures `SHA256SUMS`;
- ссылки на statistics, figures, provenance metadata и SHA-256 manifests в
  публичной документации;
- Stage 3 profiling/locality design foundation: locality taxonomy, profiling
  contract, structural gates, exact/approximation/predict-correct candidates;
- deterministic Stage 3 design plan: 336 profiling cells, 48 parameterized
  core validation-only pilot cells и 27 predict-correct screening cells.

### Изменено

- Phase 8 отмечена завершённой;
- README, STATUS и ROADMAP синхронизированы с опубликованной Stage 3A
  statistics/depth/figures evidence;
- выводы явно ограничены FashionMNIST, `lenet_classic`, seeds 0–9,
  закреплённой реализацией и validation-only protocol.

### Сохранено неизменным

- committed Stage 3A evidence не перегенерировался;
- Stage 1/2 execution и publication states не изменены;
- immutable evidence history и существующие tags не перемещались.

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
