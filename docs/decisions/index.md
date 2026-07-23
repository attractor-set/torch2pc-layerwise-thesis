# Научные и архитектурные решения

[English version](index_EN.md)

ADR фиксируют решения, влияющие на интерпретацию или воспроизводимость:

- ADR-001: Torch2PC как основная реализация;
- ADR-002: непосредственно установленная Ubuntu и контейнер Docker с ROCm;
- ADR-003: макро-F1 как основная метрика выбора;
- ADR-004: парный многостартовый статистический протокол;
- ADR-005: постпилотная фиксация порядка и телеметрии итогового выполнения;
- [ADR-006](ADR-006-stage3-scope.md): границы расширенного этапа 3;
- [ADR-007](ADR-007-stage3-locality-taxonomy.md): многомерная таксономия
  локальности;
- [ADR-008](ADR-008-predict-correct-acceleration.md): ускорение по схеме
  «предсказание–коррекция» и границы точной коррекции;
- [ADR-009](ADR-009-stage3b-rocm-canonical-lane.md): ROCm/float32 как
  единственный канонический контур этапа 3B B0; CPU/float64 остаётся инженерным
  контролем;
- [ADR-010](ADR-010-stage3b-per-cell-process-isolation.md): отдельный дочерний
  процесс Python для каждой канонической экспериментальной ячейки этапа 3B B0
  и немедленная остановка после системной нехватки памяти;
- [ADR-011](ADR-011-stage3b-b0-derived-evidence-seal.md): проверка только для
  чтения, агрегирование и адресуемая по содержимому [фиксация целостности](../glossary.md#term-integrity-sealing)
  доказательных материалов этапа 3B B0.
- [ADR-012](ADR-012-pc-tref-pc-catm-scenario-a.md): `PC-TREF` `Balanced` `Core`, `PC-CATM` и сценарий A как единый реалистичный маршрут после B0.
- [ADR-013](ADR-013-pc-tref-operational-semantics.md): операциональная семантика `PC-TREF`/`PC-CATM`, раздельные границы стоимости и допуск B1/B2 к предварительной регистрации.
- [ADR-014](ADR-014-stage3b-b1-b2-candidate-contracts.md): отдельные точные
  контракты реализации и проверки эквивалентности кандидатов B1/B2.
- [ADR-015](ADR-015-stage3b-matched-measurement-sealing.md): разделение основного времени и
  структурных счётчиков, поток событий локальности и специальная фиксация
  сопоставленных доказательных материалов.
- [ADR-016](ADR-016-stage3b-sufficiency-boundary.md): `one-step` операционная
  граница достаточности, разделение `oracle`-метки и `pre-action` оценивателя,
  условная геометрия и неизменная последовательность допуска после `EX-IF0`.
- [ADR-017](ADR-017-stage3b-288cell-correctness-repair.md): закрытое при
  ошибке исправление жизненного цикла попыток, подтверждающего допуска,
  точной балансировки порядка и межкандидатной проверки корректности перед
  кампанией из 288 ячеек.
- [ADR-018](ADR-018-stage3b-b1-confirmatory-preregistration.md): фиксирует подтверждающий `EQ-B1` как 120 сопоставленных пар на десяти различных проверочных пакетах и сохраняет [выполнение](../glossary.md#term-execution) закрытым до отдельной проверки открытия.
- [ADR-019](ADR-019-stage3b-b1-confirmatory-opening.md): добавляет закрытую при
  ошибке инфраструктуру заморозки пакетов, двухконтурной авторизации,
  восстановления и фиксации подтверждающего `EQ-B1`, сохраняя
  [выполнение](../glossary.md#term-execution) закрытым до отдельной проверки среды.
- [ADR-020](ADR-020-pc-multiscale-mechanism-decision-architecture.md): [многомасштабная механизмно-решающая архитектура](../glossary.md#term-multiscale-mechanism-decision-architecture), отдельные контракты масштаба и граница будущей линии `QWake-SPC`.
- [ADR-021](ADR-021-stage3b-b2-confirmatory-preregistration.md): фиксирует подтверждающий `EQ-B2` как 120 сопоставленных троек и 240 прямых сравнений, повторно использует замороженные входы B1 и сохраняет [выполнение](../glossary.md#term-execution) и [сопоставленное профилирование](../glossary.md#term-matched-profiling) закрытыми до отдельного допуска.
- [ADR-022](ADR-022-stage3b-b2-confirmatory-opening.md): добавляет закрытую при ошибке инфраструктуру фиксации запроса, раздельной авторизации, восстановления и фиксации подтверждающего `EQ-B2`, сохраняя [выполнение](../glossary.md#term-execution) закрытым до отдельной фиксации запроса и допуска [среды выполнения](../glossary.md#term-runtime).
- [ADR-023](ADR-023-stage3b-b2-confirmatory-request-freeze.md): фиксирует неизменяемый запрос подтверждающего `EQ-B2` на 120 троек/240 сравнений и сохраняет [выполнение](../glossary.md#term-execution) закрытым до отдельной проверки образа и [среды выполнения](../glossary.md#term-runtime).
- [ADR-024](ADR-024-stage3b-b2-confirmatory-evidence-preservation.md): побайтно сохраняет запечатанный `EQ-B2-CONFIRMATORY=pass` и производный `EQ-B2`, завершает научную цепочку допуска B1/B2 и сохраняет сопоставленное профилирование закрытым до новой версионированной фиксации.

- [ADR-025](ADR-025-stage3b-matched-profiling-request-refreeze.md): создаёт новую фиксацию `v2` запроса и манифеста на основе запечатанных подтверждающих допусков B1/B2, сохраняет историческую версию `v1` неизменной и оставляет выполнение закрытым.

- [ADR-026](ADR-026-stage3b-matched-profiling-evidence-preservation.md): побайтно сохраняет запечатанные [доказательные материалы](../glossary.md#term-evidence) сопоставленного профилирования на 288 ячейках, фиксирует закрытую границу анализа и вводит черновой релиз с отдельными артефактами запуска.

- [ADR-027](ADR-027-stage3b-matched-descriptive-analysis-protocol.md): фиксирует протокол описательного анализа после сбора и до анализа, независимую единицу `model_seed`, порядок агрегации, семимерное Парето-правило и закрытую границу выполнения/публикации.
- [ADR-028](ADR-028-stage3b-matched-descriptive-analysis-implementation.md): заменяет ранний анализатор зарегистрированным ядром на 18 выходов, фиксирует полную синтетическую проверку и сохраняет выполнение на запечатанных доказательных материалах закрытым до отдельного допуска.
- [ADR-029](ADR-029-stage3b-matched-descriptive-analysis-preexecution-hardening.md): фиксирует корректное происхождение будущего авторизованного выхода, взаимную согласованность 288/1440/96 компактных строк и настоящую проверку `Zstandard`-кадра, не открывая выполнение.

- [ADR-030](ADR-030-stage3b-matched-descriptive-analysis-execution-request-freeze.md): фиксирует запрос одного `read-only` запуска, неизменяемые идентичности и точный 18-файловый `output contract`, сохраняя `authorization` и выполнение закрытыми.

- [ADR-031](ADR-031-stage3b-matched-descriptive-analysis-runtime-preflight-implementation.md): реализует `fail-closed runtime preflight`, `verifier` будущего `authorization` и `executor` с каноническим `frozen`-пакетом, не открывая выполнение.
- [ADR-032](ADR-032-stage3b-matched-descriptive-analysis-runtime-preflight-freeze.md): фиксирует фактическую `runtime-preflight` проверку для `merge commit` `272a9258…`, сохраняя `authorization`, выполнение и публикацию закрытыми.
- [ADR-033](ADR-033-stage3b-matched-descriptive-analysis-execution-authorization-freeze.md): фиксирует одно перспективное `read-only` разрешение, связывает `request`/`preflight`/`runtime identities` и сохраняет выполнение до `merged-main opening gate`, а публикацию — до отдельного решения.
- [ADR-034](ADR-034-stage3b-matched-descriptive-analysis-output-seal-freeze.md): сохраняет точный 18-файловый набор результатов, квитанцию выполнения и независимую проверку, связывает их внешней печатью без изменения сгенерированных метаданных и оставляет границы публикации, превосходства и тестовой выборки закрытыми.

- [ADR-035](ADR-035-stage3b-recursive-sufficiency-aggregate-direction.md): фиксирует [минимальный достаточный вычислительный агрегат](../glossary.md#term-minimum-sufficient-compute-aggregate) как центральный объект после B1/B2, рекурсивную семантику двух масштабов и условную роль спайкоподобной стабилизации без разрешения выполнения.
- [ADR-036](ADR-036-stage3b-matched-descriptive-analysis-publication-gate.md): фиксирует публикационный барьер запечатанного описательного анализа с закрытием при ошибке, проверку чернового состояния выпуска и сохранение запретов `EX-IF0`, утверждений о превосходстве, политики и тестовой выборки.

- [ADR-037](ADR-037-stage3b-matched-descriptive-analysis-publication-receipt.md): фиксирует успешное действие публикации, точную удалённую квитанцию и сохранение закрытых границ `EX-IF0`, превосходства, политики и тестовой выборки.
- [ADR-038](ADR-038-stage3b-ex-if0-exact-implementation-and-oracle-sweep-boundary.md): выбирает `stage2_baseline` как канонический точный эталон и резервный путь, фиксирует момент решения, требуемый конечный ответ, оракульный запас и правило полного суффикса для минимального устойчиво достаточного свипа, не открывая вычисление или создание меток.

- [ADR-039](ADR-039-stage3b-fixedpred-sufficiency-dus-design.md): фиксирует
  `FixedPred`, `stage2_baseline`, `Rosenbaum` `positive` `control`, исправленную роль
  `joint-VJP`, раздельные `compute`/`diagnostic` `budgets` и `fail-closed`
  `DONE / UNKNOWN / SWEEP` без разрешения выполнения.

- [ADR-040](ADR-040-stage3b-integrated-frontier-model.md): сохраняет ADR-039 неизменным и фиксирует интегрированный фронтир, `A0 / A1 / A2 / O`, действия `ACCEPT_FRONTIER / ADVANCE_FRONTIER / COMPLETE_SUFFIX`, стоимость переходов и закрытую границу выполнения.
- [ADR-041](ADR-041-stage3b-integrated-frontier-corrective-semantics.md): сохраняет ADR-039/040 как исторические решения и фиксирует текущую семантику `A0 -> A1 -> A2`, отдельный `O`, переходы `OBSERVATION / ANALYTIC / COMPUTE`, локальную монотонность, отображение стоимости, `admission` и ограниченный `temporal scope`.
- [ADR-042](ADR-042-stage3b-qwake-fp-bounded-validation-and-single-image-gating.md): ограничивает обязательную проверку одной `QWake-FP`, фиксирует `corrected` `Rosenbaum` FixedPred `special` `case`, один `immutable` `superset` `image`, роли C1/C2/C3/R, внутренние `permission` `gates` и `sealed` `receipt` `chain`.
