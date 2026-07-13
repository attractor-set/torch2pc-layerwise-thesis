# Final Stage 2: исправленная реализация Torch2PC

Stage 2 является точной репликацией confirmatory Stage 1. Единственная плановая
интервенция — commit Torch2PC. Датасеты, splits, модель, методы, параметры,
оптимизатор, batch size, epochs, seeds и порядок ячеек сохраняются.

## Матрица

`MNIST/FashionMNIST × lenet_classic × BP/Exact/FixedPred/Strict × seeds 0–9`
— 80 ячеек.

## Сравниваемые реализации

- reference: Stage 1 commit `00c6c50ee3540537bbb56ab2b6567b541f42b093`;
- candidate: commit fork после применения patch series.

## Gates

До test-запусков обязательны CPU и GPU проверки:

- C0: patched Exact против BP;
- C1: patched FixedPred-control против patched Exact;
- C2/C3: original против patched по loss, dLdy, beliefs, epsilon и gradients
  для Exact, FixedPred и Strict.

Stage 2 хранит registry и результаты отдельно от Stage 1. Stage 1 artifacts
остаются неизменяемыми.

## Модель фиксации evidence

Docker-образ собирается из чистого execution commit. Локальный
`prepared_assets.json` создаётся как игнорируемый файл и входит в environment
lock по SHA-256. После формирования environment lock, CPU/GPU gates и execution
plan эти evidence-файлы коммитятся без изменения зафиксированных source/config
файлов. Freeze manifest коммитится следующим evidence commit. Перед запуском
матрицы protocol gate проверяет, что текущая ветвь является потомком execution
commit, а каждый source/config файл всё ещё совпадает с environment lock.

После завершения 80 запусков `prepared_assets.json`, registry, summaries,
tables и manifests добавляются в итоговый evidence commit. Такой порядок
сохраняет соответствие Docker image execution commit и позволяет версионировать
результаты без циклической пересборки environment lock.

## Закрытие матрицы

После завершения запусков команда `make snapshot-stage2` проверяет ровно 80
уникальных successful cells, test evaluation во всех cells, единые source и
Torch2PC commits, а также распределения 40/40 по датасетам и 20/20/20/20 по
методам. Команда создаёт immutable registry snapshot, SHA-256 и completion
summary. Отчёты и cross-version analysis строятся из этого snapshot.
