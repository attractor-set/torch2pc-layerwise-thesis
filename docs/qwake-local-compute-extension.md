# Расширение `QWake-FP` для выбора способа локального вычисления

[English version](qwake-local-compute-extension_EN.md)

**Статус:** проектная фиксация `QW-4B-DOC-R1`; реализация и
[выполнение](glossary.md#term-execution) закрыты.

## 1. Причина пересмотра

Предыдущая активная дорожная карта не разделяла результат вычисления, способ его
получения и фактически использованные ресурсы. Такое объединение не позволяет
строго сравнить два способа, которые дают один и тот же ответ, но проходят
разные вычислительные пути и имеют разную стоимость.

Новая модель вводится до нового контейнерного образа и до повторного выпуска
разрешения. Старые предварительная проверка и разрешение сохранены только как
журнал аудита и не могут быть использованы повторно.

## 2. Четыре независимых объекта

Для каждого состояния `s` и действия `a` различаются:

1. [требуемый результат](glossary.md#term-required-result) `R(a,s)`;
2. [вычислительный механизм](glossary.md#term-computational-mechanism) `M(a)`;
3. [ресурсная траектория](glossary.md#term-resource-trajectory) `Γ(a,s)`;
4. [вектор стоимости](glossary.md#term-cost-vector) `C(a,s)=Φ(Γ(a,s))`.

Требуемый результат не определяет единственный механизм и не определяет
однозначно ресурсную траекторию. Поэтому равенство ответа не является
доказательством равенства вычислительной стоимости.

## 3. Два отношения эквивалентности

[Эквивалентность по результату](glossary.md#term-response-equivalence)
задаётся относительно зарегистрированного ответа:

```math
a_i \sim_R a_j
\iff
R(a_i,s) \approx_R R(a_j,s)
```

[Эквивалентность по стоимости](glossary.md#term-cost-equivalence) задаётся
отдельно:

```math
a_i \sim_C a_j
\iff
C(a_i,s) \approx_C C(a_j,s)
```

Допустим случай:

```math
a_{explicit} \sim_R a_{analytic}
a_{explicit} \not\sim_C a_{analytic}
```

Он означает одинаковый требуемый ответ при различимой структуре вычислений и
стоимости. Он не означает независимость результата от вычислительных ресурсов.

## 4. Семейство `LOCAL_COMPUTE`

[Локальное вычисление](glossary.md#term-local-compute) является семейством
действий, а не одним алгоритмом:

```text
LOCAL_COMPUTE
├── LOCAL_SWEEP
└── ANALYTIC_COMPLETION
```

Явный локальный проход выполняет явное зарегистрированное
обновление на ограниченном агрегате. [Аналитическое завершение](glossary.md#term-analytic-completion)
получает тот же зарегистрированный ответ без явного воспроизведения всей
вычислительной последовательности, если это проходит зарегистрированную проверку для ограниченного случая.

Оба способа обязаны сохранять одну и ту же границу ответа, происхождение
артефактов, правила стоимости и возможность точного резервного перехода.

## 5. Допуск действия

Множество допустимых действий определяется ограничением на
[regret решения](glossary.md#term-decision-regret):

```math
\mathcal A_{adm}(s)=\{a:\operatorname{Regret}_R(a,s)\le\varepsilon\}
```

Выбор выполняется только внутри этого множества:

```math
a^*(s)=\arg\min_{a\in\mathcal A_{adm}(s)} C(a,s)
```

Если компоненты стоимости не допускают зарегистрированного скалярного сравнения,
используется [Pareto-допустимость](glossary.md#term-pareto-admissibility) и
заранее выбранное правило разрешения неоднозначности.

## 6. Ограниченный аналитический кандидат

Первый [кандидат](glossary.md#term-candidate) имеет идентификатор:

```text
fixedpred_eta1_wavefront_completion_v1
```

Его область ограничена одновременно следующими условиями:

```text
algorithm=FixedPred
eta=1
architecture=lenet_classic
executor=stage2_baseline
mode=shadow_post_action_validation
```

Он должен выдавать только конечные градиенты и заранее зарегистрированные
наблюдаемые величины. Вне области остаются `Strict`, произвольные значения
`eta`, произвольные графы, пропускающие соединения, универсальный символьный
решатель и восстановление полной траектории.

## 7. Последовательность этапов

```text
QW-4B-DOC-R1
→ new immutable baseline image
→ QW-4B-F-v2
→ QW-4B-E-v2
→ sealed baseline report
→ QW-LC0
→ QW-LC1
→ QW-LC2
→ QW-LC3
→ QW-LC4-I
→ QW-LC4-F
→ QW-LC4-E
→ QW-5
→ C1
→ C2
→ C3
→ R
```

`QW-LC0` фиксирует семантику и область. `QW-LC1` фиксирует наблюдаемые ответы.
`QW-LC2` фиксирует модель ресурсов. `QW-LC3` задаёт сопоставленную проверку.
`QW-LC4-I`, `QW-LC4-F` и `QW-LC4-E` разделяют реализацию, разрешение и
инженерное выполнение. Только после успешного отчёта расширения допускается
`QW-5` — единая заморозка научного образа.

## 8. Текущая граница

```text
qwake_documentation_refactor_complete=true
qwake_old_runtime_authorization_retired=true
qwake_new_image_required=true
qwake_new_runtime_preflight_captured=false
qwake_new_runtime_authorization_issued=false
qwake_runtime_validation_performed=false
qwake_engineering_evidence_present=false
qwake_local_compute_contract_frozen=true
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
qwake_scientific_image_freeze_permitted=false
c1_collection_open=false
c2_calibration_open=false
c3_confirmatory_open=false
replication_open=false
test_dataset_access=false
publication_permitted=false
```


## 9. Открытие `QW-LC0` после слияния

[Доказательные материалы](glossary.md#term-evidence) базового отчёта зафиксированы на `main`
`4f23b752a40ae05de9fc7ee49c9962c44083b71d`. Поэтому разрешена только следующая документационная
операция: окончательная фиксация семантики `R/M/Γ/C`, области
`LOCAL_COMPUTE`, первого аналитического кандидата и запретов обобщения.

```text
qwake_qw4b_e_v2_repository_evidence_sealed=true
qwake_qw_lc0_open=true
qwake_qw_lc0_semantics_scope_frozen=false
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
qwake_next_slice=QW-LC0
qwake_post_lc0_next_slice=QW-LC1
```

Открытие `QW-LC0` не является разрешением на вызов модели, сбор признаков,
создание эталонной метки после действия, выполнение локального прохода или аналитического
завершения.


## 10. Нормативная фиксация `QW-LC0`

Контракт `stage3b-qwake-lc0-semantics-scope-v1` делает разделение `R/M/Γ/C` нормативным для
`LOCAL_COMPUTE`. `LOCAL_SWEEP` и `ANALYTIC_COMPLETION` являются разными
механизмами; равенство их требуемого результата не означает равенство ресурсной
траектории или стоимости.

Текущий срез не задаёт окончательную сериализацию ответа, измерительную схему
ресурсов или отображение стоимости. Эти поля принадлежат соответственно
`QW-LC1` и `QW-LC2`. Первый кандидат остаётся непроверенной гипотезой в строго
ограниченной области.

```text
qwake_qw_lc0_semantics_scope_frozen=true
qwake_qw_lc1_open=false
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
qwake_next_slice=QW-LC0-repository-freeze
qwake_post_merge_next_slice=QW-LC1
```

## 11. Фиксация состояния репозитория `QW-LC0`

После слияния контракта в `main` `8429f54257685a879b0a44499d5fa81eab7310ea` отдельная
квитанция фиксирует точные коммиты и контрольные суммы. Её материализация не
разрешает переход к `QW-LC1` до собственного слияния и повторной проверки.

```text
repository_freeze_materialized=true
repository_freeze_complete=false
qw_lc1_transition_permitted=false
qw_lc1_open=false
local_compute_implementation_open=false
local_compute_execution_open=false
```

## 12. Переход к `QW-LC1`

Переход фиксирует только область следующего определения: каноническую схему
`R(a,s)`, обязательные наблюдаемые поля и оператор `~R`. Он не задаёт поля,
допуски или алгоритм сравнения и не открывает `Γ`, `Φ`, стоимость, код или
выполнение.

```text
lc1_transition_materialized=true
lc1_transition_complete=false
lc1_open=false
required_response_schema_open=false
resource_trajectory_schema_open=false
local_compute_implementation_open=false
local_compute_execution_open=false
```
## 13. Схема требуемого результата `QW-LC1`

Контракт `stage3b-qwake-lc1-required-response-schema-v1` фиксирует `R(a,s)` как упорядоченную совокупность именованных градиентов параметров, конечных представлений слоёв и скалярной функции потерь. Ответ сериализуется как канонический манифест `JSON` и отдельные файлы полезных данных с порядком байтов от младшего к старшему, непрерывным порядком `C` и сохранением исходного типа данных.

До численного сравнения точно совпадают схема, состояние, профиль, порядок компонентов, ключи, позиции, формы, типы данных и число элементов. Каждая запись затем сравнивается в `float64` по `relative_l2`, `max_abs` и, только для двух активных записей, по косинусному сходству. Две неактивные записи проходят условие косинусного сходства; одна активная и одна неактивная всегда дают отказ.

```text
required_result_components=
  named_parameter_gradients,
  endpoint_beliefs,
  endpoint_loss
canonical_profile=rocm_float32_canonical
engineering_profile=cpu_float64_engineering
response_equivalence_transitivity_assumed=false
resource_trajectory_schema_open=false
local_compute_implementation_open=false
local_compute_execution_open=false
next_slice=QW-LC1-repository-freeze
```
## 14. Фиксация состояния репозитория `QW-LC1`

После слияния схемы в `main` `59e3143ba105a5b298e2cd551b221b8f6dae96f7` отдельная квитанция фиксирует
точные коммиты и контрольные суммы контракта. Материализация квитанции не
завершает `QW-LC1` и не разрешает переход к `QW-LC2` до собственного слияния и
повторной проверки.

```text
repository_freeze_materialized=true
repository_freeze_complete=false
qw_lc1_complete=false
qw_lc2_transition_permitted=false
resource_trajectory_schema_open=false
measurement_to_cost_mapping_open=false
cost_equivalence_operator_definition_open=false
local_compute_implementation_open=false
local_compute_execution_open=false
```

## 15. Переход к `QW-LC2`

После завершения `QW-LC1` переход ограничивает следующий контракт тремя
частями: измерительной схемой `Γ(a,s)`, отображением `Φ: Γ -> C` и оператором
`~C`. Переход не задаёт измеряемые поля, единицы, окна, агрегацию, пороги,
скаляризацию или эмпирические значения. Сопоставленная теневая проверка,
идентичность состояния, состояние генераторов случайных чисел, резервный путь,
код и выполнение остаются последующими срезами.

```text
lc1_complete=true
lc2_transition_materialized=true
lc2_transition_complete=false
lc2_open=false
resource_trajectory_schema_open=false
measurement_to_cost_mapping_open=false
cost_equivalence_operator_definition_open=false
local_compute_implementation_open=false
local_compute_execution_open=false
```

## 16. Контракт ресурсов и стоимости `QW-LC2`

Контракт `stage3b-qwake-lc2-resource-cost-contract-v1` фиксирует ресурсную траекторию
`Γ(a,s;r,p)` как упорядоченную запись идентификаторов, корневого интервала,
принадлежности интервалов, пиков памяти, уникальных объёмов артефактов,
калибровки наблюдателя и резервного пути. `Φ` формирует следующий порядок `C`:

```text
compute_primary_time_ns
latency_wall_time_ns
peak_allocated_bytes
peak_reserved_bytes
diagnostic_primary_time_ns
diagnostic_materialized_bytes
observer_overhead_time_ns
observer_evidence_bytes
control_wall_time_ns
fallback_wall_time_ns
fallback_invoked
```

Задержка остаётся отдельной включающей компонентой и не складывается с
декомпозированными временами. Интервалы объединяются, память задаётся максимумом,
а объём артефактов учитывается один раз по владельцу и `SHA-256`; накладное
время наблюдателя не вычитается из задержки или времени вычисления.

`shadow_mechanism_v1` не является решенческим. Будущий `end_to_end_v1` требует
завершённого `QW-LC3`. `~C` применяется только при одинаковой непрозрачной
привязке состояния, вычислительной линии и профиле стоимости; транзитивность не
предполагается. После допуска по `~R` используется правило Парето с допусками и
зарегистрированное детерминированное разрешение неоднозначности. Отсутствующий
или неполный вектор стоимости приводит к `LOCAL_SWEEP`.

```text
resource_trajectory_schema_frozen=true
measurement_to_cost_mapping_frozen=true
cost_equivalence_operator_definition_frozen=true
pareto_and_tie_break_rule_frozen=true
qwake_qw_lc2_complete=false
qwake_qw_lc3_transition_permitted=false
local_compute_implementation_open=false
local_compute_execution_open=false
```

## 17. Фиксация состояния репозитория `QW-LC2`

Квитанция связывает `stage3b-qwake-lc2-resource-cost-contract-v1` с коммитом слияния `8f24229bcf19736086fe6f0340bda26dd533936a`, первым
родителем `858403cbb2423ad3427ab7a042266880ca34c0b7` и коммитом контракта `3f1682765089b0819dcaaf9bb449c4c1bd155142`.
Она подтверждает сохранение `Γ`, `Φ`, `C`, `~C`, профилей и правил, но не
содержит реализации и не разрешает выполнение.

```text
qwake_qw_lc2_repository_freeze_materialized=true
qwake_qw_lc2_repository_freeze_complete=false
qwake_qw_lc3_transition_permitted=false
local_compute_implementation_open=false
local_compute_execution_open=false
```

## 18. Переход к `QW-LC3`

После слияния фиксации состояния репозитория `QW-LC2` в `main`
`4f7c533047214398e7ec4dde9d58b5fc06964b90` и отдельной проверки `QW-LC2`
завершён. Квитанция перехода ограничивает следующий контракт протоколом
сопоставленной теневой проверки, построением непрозрачной ссылки на общее
состояние, восстановлением ГПСЧ, проверкой полного точного резервного суффикса и
сопоставленной агрегацией повторов.

Переход не задаёт сериализацию снимков, список генераторов, порядок рук, число
повторов, допуски или критерии успешного результата. Он не открывает
реализацию, разрешение или выполнение.

```text
qwake_qw_lc2_complete=true
qwake_qw_lc3_transition_materialized=true
qwake_qw_lc3_transition_complete=false
qwake_qw_lc3_open=false
matched_shadow_validation_protocol_open=false
opaque_state_ref_definition_open=false
rng_restoration_protocol_open=false
exact_reserve_suffix_validation_open=false
repeat_aggregation_protocol_open=false
local_compute_implementation_open=false
local_compute_execution_open=false
next_slice=QW-LC3-transition-merge
post_merge_next_slice=QW-LC3-matched-shadow-validation-contract
```

## 19. Контракт сопоставленной теневой проверки `QW-LC3`

Контракт `stage3b-qwake-lc3-matched-shadow-validation-contract-v1` связывает
`R`, `Γ` и `C` в одной закрытой проверочной конструкции. Общий снимок состояния
получает канонический `opaque_state_ref`; каждая рука и резервный зонд получают
новое одноразовое ответвление этого снимка. Все зарегистрированные ГПСЧ
восстанавливаются перед каждой рукой, а их состояния после двух рук пары должны
совпасть точно.

Для каждой проверочной ячейки зафиксированы двенадцать пар с чередующимся
порядком рук. Все пары обязаны пройти `~R`; пропуск или исключение повтора
закрывает ячейку. Два принудительных зонда проверяют, что до первого и после
последнего повтора полный резервный `LOCAL_SWEEP` выполняет весь суффикс без
пропусков, повторов и использования промежуточного состояния кандидата.

Стоимость агрегируется отдельно по каждому полю как парная разность
`ANALYTIC_COMPLETION - LOCAL_SWEEP`; сохраняются медиана, нижний и верхний
шарниры, минимум и максимум. Скалярный итог и заявление статистической
значимости запрещены. Контракт не реализует механизм и не разрешает выполнение.

```text
qwake_qw_lc3_matched_shadow_validation_contract_frozen=true
matched_shadow_validation_protocol_frozen=true
opaque_state_ref_definition_frozen=true
rng_restoration_protocol_frozen=true
exact_reserve_suffix_validation_frozen=true
repeat_aggregation_protocol_frozen=true
qwake_qw_lc3_complete=false
qwake_qw_lc4_implementation_permitted=false
local_compute_implementation_open=false
local_compute_execution_open=false
next_slice=QW-LC3-repository-freeze
```

## 20. Фиксация состояния репозитория `QW-LC3`

После слияния контракта через PR №121 в `main` `71e73f56408c720334b8fa03e7133762c8bbcc43` отдельная
квитанция связывает проверенное дерево с коммитом контракта
`fb3f1cd4a4d3b4261db1179badcc1ccacddfe936`, переходом `QW-LC3` и их контрольными суммами.
Материализация квитанции не завершает `QW-LC3` до собственного слияния и
повторной проверки.

```text
qwake_qw_lc3_repository_freeze_materialized=true
qwake_qw_lc3_repository_freeze_complete=false
qwake_qw_lc3_complete=false
qwake_qw_lc4_implementation_permitted=false
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
qwake_next_slice=QW-LC3-repository-freeze-merge
qwake_post_merge_next_slice=QW-LC4-I
```

## 21. Ограниченная реализация `QW-LC4-I`

После слияния фиксации состояния `QW-LC3` в `main`
`7c6cbb6ba4941cf78b2bfec3e6e8955c2830a58b` материализован первый код
зарегистрированного кандидата `ANALYTIC_COMPLETION`. В индексе кандидата `t`
завершённая граница волны задаёт остаток, после чего распространяется только
незавершённая нижняя цепочка VJP. Точная эталонная ветвь выполняет все
оставшиеся свипы FixedPred из другого одноразового ответвления.

Тот же модуль материализует `opaque_state_ref`, полное восстановление ГПСЧ,
оператор ответа `QW-LC1`, нескалярное отображение стоимости `QW-LC2`, два
принудительных точных резервных зонда, сбалансированное расписание двенадцати
повторов и покомпонентную парную агрегацию. Разрешение только для синтетических
тестов намеренно отделено от любого будущего разрешения рабочей среды.

```text
qw_lc3_complete=true
qw_lc4_i_implementation_materialized=true
synthetic_unit_test_only=true
local_compute_implementation_open=false
local_compute_execution_open=false
scientific_execution_open=false
next_slice=QW-LC4-I-merge
post_merge_next_slice=QW-LC4-F
```

## 22. Авторинг фиксации рабочей среды `QW-LC4-F`

После слияния `QW-LC4-I` через PR №123 в `main`
`c9f3dadcd5330887584b8bf71d906c667dacf076` материализован слой авторинга
фиксации рабочей среды. Он добавляет адаптер уже захваченного состояния
FixedPred, запрещающий все возможности `preflight`, точную схему одной
инженерной `authorization` и процедуру фиксации без исполнителя рабочей среды.

Запрос фиксирует две полосы, семь индексов кандидата, двенадцать повторов на
каждую комбинацию и два резервных зонда. Это 14 ячеек рабочей среды, 168
сопоставленных пар и 28 резервных зондов. Ни одна ячейка не выполняется в
срезе авторинга.

Фиксация разделена на две фазы, потому что хэш образа должен принадлежать
коммиту, содержащему сам адаптер и код допуска. Сначала код авторинга должен
быть проверен и закоммичен; затем из этого коммита строится неизменяемый образ
и материализуются фактические объекты `preflight`, `authorization` и квитанции
проверки.

```text
qw_lc4_i_complete=true
qw_lc4_f_authoring_materialized=true
qw_lc4_f_request_frozen=true
qw_lc4_f_materialized=false
qw_lc4_e_branch_permitted=false
local_compute_execution_open=false
runtime_execution_performed=false
scientific_execution_open=false
next_slice=QW-LC4-F-authoring-commit
post_commit_next_slice=QW-LC4-F-runtime-materialization
```
## `QW-LC4-F`: разрешение зафиксировано без исполнения

[ADR-063](decisions/ADR-063-stage3b-qwake-lc4-f-runtime-freeze.md) связывает
ограниченную реализацию с точным образом, проверками CPU/ROCm, статической
квитанцией и одноразовым разрешением. Зафиксированы 14 ячеек рабочей среды,
168 сопоставленных ячеек и 28 резервных зондов.

Флаг `runtime_execution_permitted=true` внутри разрешения не открывает
исполнение на ветке фиксации. `QW-LC4-E` разрешается только после слияния и
независимой проверки `QW-LC4-F`.
## `QW-LC4-E`: отдельный допуск перед выполнением

[ADR-064](decisions/ADR-064-stage3b-qwake-lc4-e-execution-admission-authoring.md)
разделяет наличие замороженного разрешения, проверенный допуск контура
управления и фактическое начало выполнения. Текущий срез материализует только
схему и валидатор; файл одноразового владения и исполнитель отсутствуют.
## `QW-LC4-E`: фиксация конкретного допуска

[ADR-065](decisions/ADR-065-stage3b-qwake-lc4-e-execution-admission-freeze.md)
фиксирует запись допуска, связанную с `main` `bce821dff0729629db0ccb306d8f3fd1dd9a2e13`. Разрешение записи на
одну попытку не открывает разрешение выполнения на ветке. Файл владения,
исполнитель, результаты и доказательные материалы отсутствуют.
## `QW-LC4-E`: проектирование владения и исполняющей обёртки

[ADR-066](decisions/ADR-066-stage3b-qwake-lc4-e-execution-lease-wrapper-authoring.md)
вводит предварительную одноразовую запись владения и контракт исполняющей
обёртки. Оба объекта строятся только в памяти; файл владения, исполнитель,
каталог результатов и доказательные материалы отсутствуют.

## `QW-LC4-E`: атомарная реализация владения и обёртки

[ADR-067](decisions/ADR-067-stage3b-qwake-lc4-e-execution-lease-wrapper-implementation.md)
добавляет код эффектов отдельным модулем и сохраняет зафиксированный модуль
проектирования неизменным. Захват имени файла владения использует временный
файл в том же каталоге, `fsync` и жёсткую ссылку, которая не может заменить
существующую запись. После захвата отсутствие результата проверяется повторно;
обнаруженная гонка оставляет разрешение потреблённым и блокирует вычислительный модуль.

Вычислительный модуль получает только скрытый каталог подготовки, запись владения и
проверенный контракт. Дерево с символическими ссылками, нерегулярными файлами,
пустым результатом или неверной квитанцией отклоняется. Успешное дерево
синхронизируется и продвигается через `renameat2(RENAME_NOREPLACE)`. Ошибка
удаляет только подготовительный каталог; файл владения сохраняется и повтор
остаётся запрещённым.

Синтетическая программа проверки проверяет этот цикл под `/tmp`. Он не создаёт
репозиторный файл владения, не запускает модельный вычислительный модуль и не формирует
инженерное свидетельство. Фактическое выполнение остаётся закрытым до
отдельной фиксации точного коммита реализации.
## `QW-LC4-E`: проектирование фиксации выполнения

См. [ADR-068](decisions/ADR-068-stage3b-qwake-lc4-e-execution-freeze-authoring.md).

- PR №128 слит в `main` `24966cd2a0380e46ab1924ff4ab8987f17e1fe9e`;
- exact 16-файловое дерево реализации, его SHA-256 и CI 2/2 подтверждены;
- детерминированный запрос связывает реализацию, допуск, пути владения и
  результата, 168 ячеек и 28 резервных проверок;
- захват и выполнение обязаны происходить одним процессом без повтора;
- конкретный вычислительный модуль и одноразовая точка входа пока отсутствуют;
- фиксация выполнения, файл владения, выполнение, инженерное свидетельство и публикация
  остаются закрытыми;
- следующий срез после слияния — `QW-LC4-E-runtime-backend-implementation`.

## `QW-LC4-E`: `bounded backend` и сохранение отрицательного исхода

См. [ADR-069](decisions/ADR-069-stage3b-qwake-lc4-e-runtime-backend-implementation.md).

Конкретный `backend` связывает замороженную матрицу с `lenet_classic`,
синтетическим `batch`, точным суффиксом `LOCAL_SWEEP` и
`ANALYTIC_COMPLETION`. Численная канонизация не расширяет область: она меняет
только уже завершённые верхние `residuals` на их алгебраическое представление
`fixed - beliefs`, если `raw`-дефект находится внутри допуска полосы, и сохраняет
обе контрольные суммы. Все руки стартуют из одного канонического
`opaque_state_ref`.

Целостность и эмпирический успех разделены. Неполная матрица, неверная
идентичность или хэш закрывают `backend`. Полная матрица с отрицательным `~R`,
`RNG`, `reserve` или `order-effect` результатом сохраняется с
`validation_passed=false`. Это предотвращает необратимую потерю отрицательного
результата после одноразового захвата допуска.

### Материализация фиксации выполнения `QW-LC4-E`

См. [ADR-070](decisions/ADR-070-stage3b-qwake-lc4-e-execution-freeze-materialization.md).

- PR №130 слит в `main` `67a084c0b970ad79ad0692442f660085a73b080a` и независимо проверен;
- из этого коммита построен неизменяемый образ `torch2pc-layerwise-thesis:0.1.0-qw-lc4-e-freeze-67a084c0b970` с идентификатором `sha256:7da92b8f77f6dc37d42db832c5613ef6149dc488adc5b66465faa33e48ca021d`;
- девятифайловый пакет `execution-freeze-v1` связывает образ, вычислительный модуль, точку входа, допуск и авторизацию;
- исходный `image-build.log` сохраняется байт-в-байт и точечно классифицируется в `.gitattributes` как двоичное запечатанное свидетельство;
- внутренняя запись разрешает будущую одноразовую точку входа, но веточный допуск выполнения остаётся закрытым;
- файл владения, каталог результата, инженерные материалы, научное выполнение, тестовая выборка и публикация отсутствуют.

### Разрешение одноразового инженерного вызова `QW-LC4-E`

См. [ADR-071](decisions/ADR-071-stage3b-qwake-lc4-e-one-shot-invocation-authorization.md).

После проверенного слияния PR №131 материализован отдельный машиночитаемый
пакет разрешения. Он связывает точные идентичности неизменяемого образа,
`execution-freeze-v1`, допуска, матричной авторизации, вычислительного модуля, обёртки и точки
входа. Внутренняя запись разрешает один будущий инженерный вызов и один будущий
захват файла владения.

Разрешение не является выполнением. На ветке не создан файл владения, отсутствуют
каталог результата и подготовительный каталог, авторизация не потреблена, модель не вызывалась.

```text
qwake_adr=ADR-071-stage3b-qwake-lc4-e-one-shot-invocation-authorization
qwake_invocation_authorization_sha256=sha256:0a60dacc1bfd5073cf52d76f2ec33ae54f00899aad9877d44607199659fda75a
qwake_invocation_authorization_registry_sha256=sha256:9a47f79e9607db98a2c7c224c25cbeee920974d4c339eef4ef82d4f9aa7c8f83
ONE_SHOT_INVOCATION_AUTHORIZED=true
FUTURE_LEASE_CLAIM_AUTHORIZED=true
FUTURE_RUNTIME_EXECUTION_AUTHORIZED=true
BRANCH_RUNTIME_EXECUTION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
ENGINEERING_EVIDENCE_PRESENT=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
FILES_STAGED=false
```

### Авторинг хостовой обёртки одноразового вызова `QW-LC4-E`

См. [ADR-072](decisions/ADR-072-stage3b-qwake-lc4-e-one-shot-invocation-wrapper-authoring.md).

После проверенного слияния PR №132 материализован только чистый контракт
будущей хостовой обёртки. Он привязывает разрешение к точному неизменяемому
образу и внутренней точке входа, запрещает монтирование исходного дерева и
набора данных и ограничивает будущий контейнер зафиксированными пакетами,
Torch2PC и каталогом результатов. Дополнительно зафиксированы устройства
`/dev/kfd` и `/dev/dri`, пользователь и группы, входы ограничений ресурсов,
точный шаблон команды и временная файловая система `/tmp`, необходимая при
корневой файловой системе только для чтения. Вызов Docker, проверка локального
образа, файл владения и выполнение отсутствуют.

```text
qwake_invocation_wrapper_contract_sha256=sha256:4c4cb163e8c2a33b0563cc3b9cb873a87acf8ea75bb3e807d157d51c5a4dd29b
INVOCATION_WRAPPER_CONTRACT_PRESENT=true
CONTAINER_COMMAND_TEMPLATE_PRESENT=true
GPU_DEVICE_BINDING_COUNT=2
TMPFS_REQUIRED=true
TMPFS_TARGET=/tmp
HOST_RUNTIME_INVOKER_PRESENT=false
BRANCH_RUNTIME_EXECUTION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```

### Реализация хостовой обёртки одноразового вызова `QW-LC4-E`

ADR-073 добавляет закрытую при ошибке проверку точного локального образа и
детерминированный построитель будущего `docker run` как данных. Реализация
сверяет полную нормализованную идентичность образа, требует канонические входы
ресурсов и формирует ровно три монтирования и два устройства. Она не содержит
хостового исполнителя, не создаёт файл владения и не открывает
[выполнение](glossary.md#term-execution) `LOCAL_COMPUTE`.

### Авторинг одноразового хостового исполнителя `QW-LC4-E`

См. [ADR-074](decisions/ADR-074-stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-authoring.md).

- PR №134 слит в `main` `be6486a9e3670343132f2c863a5a0cd5969ee9f6` и независимо проверен;
- чистый контракт связывает точную реализацию проверки образа и канонического `argv` с одной будущей попыткой запуска;
- хостовый процесс обязан повторно проверить образ, команду и отсутствие эффектов непосредственно перед запуском;
- файл владения может захватить только контейнерная точка входа в том же процессе, который выполняет вычислительный модуль;
- после запуска автоматический повтор запрещён, а после захвата файла владения он сохраняется при любой ошибке;
- исполнитель, файл владения, результат, [доказательные материалы](glossary.md#term-evidence), тестовые данные и публикация отсутствуют.

### Реализация одноразового хостового исполнителя `QW-LC4-E`

См. [ADR-075](decisions/ADR-075-stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-implementation.md).

- PR №135 слит в `main` `7f1655346bca77834d73a660c9857f1ff23b826c` и независимо проверен;
- реализованы двойная проверка образа и канонического `argv`, один `Popen` без оболочки и фиксированная хостовая среда;
- дочерний процесс получает отдельную группу, пересылку `SIGINT`/`SIGTERM`, терминальный тайм-аут и ограниченный вывод;
- хост не записывает файл владения и не сохраняет команду или журналы;
- проверяющая программа и тесты не вызывают рабочую среду Docker, поэтому выполнение и результаты отсутствуют.

### Фиксация состояния репозитория одноразового хостового исполнителя `QW-LC4-E`

См. [ADR-076](decisions/ADR-076-stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-repository-freeze.md).

- PR №136 слит в `main` `da51c8d858c541372525125640db99062041fc20` и независимо проверен;
- квитанция связывает оба родителя, два коммита реализации, 16-файловое дерево и исправленные хэши;
- зафиксированы 2/2 CI-проверки, 139 целевых и 1186 полных тестов;
- реализация и точный `docker run` присутствуют, но одноразовый инженерный вызов ещё не разрешён;
- проверка образа, `docker run`, файл владения, потребление разрешения, результат и научные возможности отсутствуют;
- следующий атомарный шаг после слияния квитанции — отдельная одноразовая операторская операция.

### Допуск одноразового инженерного вызова `QW-LC4-E`

См. [ADR-077](decisions/ADR-077-stage3b-qwake-lc4-e-one-shot-engineering-invocation-admission.md).

- фиксация репозитория PR №137 завершена на `main` `3454d12d3cc16c9c50977e2a598e2bc1a8768441`;
- допуск повторно связывает разрешение, образ, Torch2PC и `executable host invoker`;
- статические идентичности проверяются без `image inspection` или запуска процесса;
- будущая операторская операция обязана заново проверить образ, ресурсы, `lease`, `output` и `staging`;
- веточное разрешение, вызов, файл владения, результат и научные возможности остаются закрытыми.

### Запись операции одноразового инженерного вызова `QW-LC4-E`

См. [ADR-078](decisions/ADR-078-stage3b-qwake-lc4-e-one-shot-engineering-invocation-operation.md).

- PR №138 слит в `main` `28be77706bc86abaf34f86e9bdcbdcb9cc2810a8` и независимо проверен;
- запись операции связывает коммит слияния допуска, авторизацию, образ, Torch2PC и хостовый исполнитель;
- зафиксированы 13 обязательных ключей ресурсов хоста, две проверки образа, две материализации канонического `argv` и один допустимый `Popen`;
- проверка текущей рабочей среды ещё не выполнена: `PREEXECUTION_IDENTITY_VERIFIED=false`;
- проверка образа, команда, `lease`, [запуск](glossary.md#term-run), результат и научные возможности остаются закрытыми;
- следующий атомарный шаг после слияния записи — отдельная операция выполнения с эффектами рабочей среды.

### Авторизация выполнения одноразового инженерного вызова `QW-LC4-E`

См. [ADR-079](decisions/ADR-079-stage3b-qwake-lc4-e-one-shot-engineering-invocation-execution-authorization.md).

- PR №139 слит в `main` `b0f6729e8fd1cb1aa172eef488dc56e36b335173` и независимо проверен;
- авторизация связывает коммит слияния операции, `operation-v1`, прежнее одноразовое разрешение, образ, Torch2PC и хостовый исполнитель;
- разрешены только одна будущая проверка перед выполнением и один будущий инженерный вызов после отдельной проверки после слияния;
- проверка обязана использовать 13 точных ресурсов хоста, два одинаковых `image inspection`, две одинаковые материализации `argv` и не более одного `Popen`;
- подготовительная ветка сохраняет `PREEXECUTION_IDENTITY_VERIFIED=false` и `ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false`;
- образ не проверялся, команда не материализовалась, `lease`, запуск, результат и научные возможности отсутствуют.

### Контракт проверки перед одноразовым инженерным вызовом `QW-LC4-E`

См. [ADR-080](decisions/ADR-080-stage3b-qwake-lc4-e-one-shot-engineering-invocation-preexecution-verification.md).

- PR №140 слит в `main` `49c4b97e93b47cefbf35576736927ece02c9402b` и независимо проверен;
- контракт связывает слитую авторизацию с точной реализацией хостового исполнителя;
- будущая атомарная операция обязана вызвать `invoke_one_shot_host_runtime` ровно один раз;
- две проверки образа, две материализации канонического `argv` и создание единственного дочернего процесса остаются одной непрерывной последовательностью;
- статическая проверяющая программа не вызывает Docker и сохраняет `PREEXECUTION_IDENTITY_VERIFIED=false`;
- файл владения, результат, [доказательные материалы](glossary.md#term-evidence) и фактическое [выполнение](glossary.md#term-execution) отсутствуют.

`decision marker`: `ADR-080-stage3b-qwake-lc4-e-one-shot-engineering-invocation-preexecution-verification`.

## `QW-LC4-E`: ограниченная операция одноразового инженерного вызова

См. [ADR-081](decisions/ADR-081-stage3b-qwake-lc4-e-one-shot-engineering-invocation-runtime-operation.md).

После независимой проверки слияния PR №141 материализован чистый контракт
атомарной операции и ограниченная точка входа. Она принимает точные ресурсы
хоста, время требования, два подтверждения и явное разрешение, а затем может
ровно один раз делегировать динамическую проверку и запуск ранее зафиксированному
хостовому исполнителю. Проверяющая программа новую точку входа не вызывает.

```text
qwake_adr=ADR-081-stage3b-qwake-lc4-e-one-shot-engineering-invocation-runtime-operation
qwake_runtime_operation_base_commit=494e6a0b2f10c26b49c90fbb84c23565699a4064
qwake_runtime_operation_sha256=sha256:0332428014f7f8385c789ba7e7c55d6c2ec03b020e3f83df9ac9714483bb6bf8
PREEXECUTION_VERIFICATION_COMPLETE=true
RUNTIME_OPERATION_RECORD_PRESENT=true
RUNTIME_OPERATION_EXECUTOR_ENTRYPOINT_IMPLEMENTED=true
RUNTIME_OPERATION_STATIC_CONTRACT_VERIFIED=true
ONE_SHOT_ENGINEERING_INVOCATION_RUNTIME_OPERATION_OPEN=true
PREEXECUTION_IDENTITY_VERIFIED=false
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
BRANCH_RUNTIME_EXECUTION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
IMAGE_INSPECTION_PERFORMED=false
INVOCATION_COMMAND_MATERIALIZED=false
DOCKER_RUN_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```

### Восстановление идентичности операции рабочей среды `QW-LC4-E`

См. [ADR-082](decisions/ADR-082-stage3b-qwake-lc4-e-runtime-operation-identity-repair.md).

Исторический ADR-081 и его пакет v1 сохранены неизменными. Отдельный пакет
исправления связывает исправленное дерево исходного кода с коммитом слияния PR
№142 и заставляет проверяющую программу операции рабочей среды проверять
собственную исполняемую идентичность. Запрос выполнения остаётся закрытым до
повторной полной проверки, слияния исправления, постоянного файла владения v2
и устойчивой квитанции отрицательного исхода хоста.

### Постоянная доказательная цепочка v2 `QW-LC4-E`

См. [ADR-083](decisions/ADR-083-stage3b-qwake-lc4-e-persistent-evidence-chain-v2.md).

После независимой проверки слияния PR №143 отдельный пакет подготовки связывает
актуальные идентичности авторизации вызова, авторизации выполнения, проверки
перед выполнением, операции рабочей среды и восстановления идентичности с
точным образом, Torch2PC, каталогом результатов и `invocation_count=1`. Чистые
конструкторы определяют будущий постоянный файл владения v2 и обязательную
терминальную квитанцию исхода хоста, включая отказ до запуска, ошибку создания
процесса, ненулевой код, тайм-аут и сигнал. Атомарная запись, привязка полномочия
к файлу владения и фактический вызов остаются закрытыми.

```text
qwake_adr=ADR-083-stage3b-qwake-lc4-e-persistent-evidence-chain-v2
qwake_persistent_evidence_chain_v2_sha256=sha256:c0a6195080cec64e6104a90076366cc2bfa10a723b45a7389cd77fa1b3b11bd1
CORRECTED_FULL_VALIDATION_RECEIPT_PRESENT=true
RUNTIME_OPERATION_IDENTITY_REPAIR_MERGED=true
LATEST_AUTHORIZATION_BOUND_IN_PERSISTENT_LEASE_TEMPLATE=true
DURABLE_NEGATIVE_HOST_OUTCOME_DEFINED=true
PERSISTENT_LEASE_V2_IMPLEMENTATION_PRESENT=false
DURABLE_OUTCOME_WRITER_IMPLEMENTED=false
LEASE_BOUND_HOST_INVOKER_ENFORCED=false
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
RUNTIME_EXECUTION_PERFORMED=false
DOCKER_RUN_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```

## `QW-LC4-E`: реализация постоянной доказательной цепочки v2

ADR-084 реализует эксклюзивную запись постоянного файла владения v2 и
устойчивой квитанции терминального исхода хоста. Запись закрывается при любой
коллизии, символьной ссылке, неполной замороженной идентичности или
несовпадении точных байтов файла владения. Долговечность обеспечивается
режимом `0600`, `fsync` файла, продвижением через жёсткую ссылку без
перезаписи и `fsync` родительского каталога. Реализация пока не подключена к
исполнителю хоста; реальный файл владения, квитанция исхода, инспекция образа,
материализация команды и выполнение отсутствуют.

## Привязка исполнителя хоста к файлу владения v2

ADR-085 вводит единственный перспективный вход, привязанный к файлу владения: до проверки образа и создания процесса он требует точные сохранённые байты постоянного файла владения v2, а после требования формирует устойчивую терминальную квитанцию без повторной попытки. Историческая прямая операция сохранена только как замороженное свидетельство и заменена для будущей авторизации. Выполнение остаётся закрытым.

## `QW-LC4-E`: подготовка финального подтверждения выполнения

ADR-086 вводит статический контракт будущего отдельного операторского
подтверждения после проверенного слияния PR №146 на
`2957d8f6975c88e7bdb23243e3915c7f51d4ba47`. Контракт связывает цепочку v2,
реализацию постоянной записи, привязанный к файлу владения исполнитель, образ,
Torch2PC, каталог результатов и `invocation_count=1`. Для будущего выпуска
обязательны точная фраза
`ACKNOWLEDGE_QWAKE_LC4_FINAL_ONE_SHOT_EXECUTION`, идентичность оператора и время
по всемирному координированному времени после слияния. Авторинг не выпускает подтверждение, не материализует файл
владения и не выполняет вызов.

```text
wiring_pr=146
wiring_focused_tests=39
wiring_targeted_tests=240
wiring_full_tests=1287
wiring_full_test_warnings=14
FINAL_EXECUTION_ACKNOWLEDGEMENT_AUTHORED=true
FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUED=false
FINAL_EXECUTION_ACKNOWLEDGED=false
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
DURABLE_HOST_OUTCOME_PRESENT=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
IMAGE_INSPECTION_PERFORMED=false
INVOCATION_COMMAND_MATERIALIZED=false
DOCKER_RUN_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```


## `QW-LC4-E`: подготовка выпуска финального подтверждения

ADR-087 связывает проверенное слияние PR №147 и точный пакет ADR-086 с
единственным будущим файлом подтверждения. Контракт требует отдельные
идентичности оператора и выпускающего, упорядоченные времена, канонический `JSON`,
атомарную запись без перезаписи, режим `0600`, `fsync` и повторную проверку
сохранённых байтов. Реализация записи, само подтверждение, файл владения и
вызов отсутствуют.

```text
acknowledgement_authoring_pr=147
acknowledgement_authoring_focused_tests=50
acknowledgement_authoring_targeted_tests=251
acknowledgement_authoring_full_tests=1298
acknowledgement_authoring_full_test_warnings=14
ACKNOWLEDGEMENT_ISSUANCE_CONTRACT_AUTHORED=true
ACKNOWLEDGEMENT_ISSUANCE_IMPLEMENTED=false
FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUED=false
FINAL_EXECUTION_ACKNOWLEDGED=false
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
DURABLE_HOST_OUTCOME_PRESENT=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
IMAGE_INSPECTION_PERFORMED=false
INVOCATION_COMMAND_MATERIALIZED=false
DOCKER_RUN_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```


## `QW-LC4-E`: реализация механизма записи финального подтверждения

ADR-088 реализует атомарное сохранение уже проверенного конверта подтверждения
в единственный путь ADR-087. Применяются `O_EXCL`, жёсткая ссылка без
перезаписи, режим `0600`, `fsync`, запрет символических родительских каталогов,
запрет оставшихся временных файлов и точная повторная проверка байтов.
Производственная точка вызова отсутствует, поэтому слияние реализации не
создаёт подтверждение и не открывает вызов.

```text
issuance_authoring_pr=148
issuance_authoring_focused_tests=61
issuance_authoring_targeted_tests=262
issuance_authoring_full_tests=1309
issuance_authoring_full_test_warnings=14
ACKNOWLEDGEMENT_ISSUANCE_IMPLEMENTED=true
FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUED=false
FINAL_EXECUTION_ACKNOWLEDGED=false
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
DURABLE_HOST_OUTCOME_PRESENT=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
IMAGE_INSPECTION_PERFORMED=false
INVOCATION_COMMAND_MATERIALIZED=false
DOCKER_RUN_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```


### Подготовка материализации финального подтверждения

После слияния реализации механизма записи отдельный статический срез связывает
будущую материализацию с точным оператором, выпускающим, материализующим
субъектом, упорядоченными временами по всемирному координированному времени,
путём и SHA-256 канонического конверта. Сам механизм записи не вызывается;
подтверждение, файл владения и [локальное вычисление](glossary.md#term-local-compute) отсутствуют.


### Реализация материализации финального подтверждения

ADR-090 добавляет функцию материализации, импорт которой не создаёт побочных
эффектов. Только отдельный явный вызов сможет передать точную предварительно
сформированную материализацию существующему атомарному модулю записи и затем
повторно проверить сохранённые байты. На текущем этапе вызова нет; подтверждение,
маркер владения выполнением и локальные вычисления остаются отсутствующими.

### Подготовка вызова материализации финального подтверждения

ADR-091 отделяет чистый контракт вызова от реализации адаптера и от фактической
материализации. Будущий адаптер сможет вызвать только точный модуль
материализации и не сможет обращаться к модулю записи напрямую. Автоматическая
и слепая [попытка](glossary.md#term-attempt) повтора запрещена: после неопределённого исхода требуется
сначала проверить устойчивый целевой файл. Отсутствие файла допускает только
новую явно авторизованную попытку, корректный существующий файл считается
успехом без повторного вызова, а некорректный файл закрывает процесс при ошибке.
В текущем срезе модуль материализации не вызывается.

### Реализация адаптера вызова материализации финального подтверждения

ADR-092 реализует библиотечный адаптер без производственной точки вызова. Перед
обращением к модулю материализации он проверяет целевой файл: отсутствие
допускает один вызов, корректный существующий файл считается успешным
восстановлением без повторного вызова, а некорректный файл закрывает операцию
при ошибке. Автоматическая и слепая повторная попытка отсутствуют.

### `QW-LC4-E`: операторская операция вызова материализации подтверждения

После реализации адаптера отдельный слой подготовки связывает одну будущую
операцию с точным объектом вызова, оператором и временем разрешения. Фраза
операции отлична от фразы подтверждения исполнения. Будущая реализация не должна
вызывать проверку состояния отдельно от адаптера: встроенная проверка адаптера
остаётся единственной авторитетной классификацией перед действием.


### `QW-LC4-E`: реализация операторской операции вызова материализации

ADR-094 реализует чисто импортируемую библиотечную операцию, которая проверяет
замороженный объект действия и передаёт его точный будущий вызов существующему
адаптеру ровно один раз. Отдельная проверка устойчивого состояния и прямые
вызовы нижних модулей запрещены. В репозитории нет производственной точки
вызова, поэтому операция, подтверждение и [локальное вычисление](glossary.md#term-local-compute)
остаются отсутствующими.


### Подготовка производственной точки вызова операторской операции

ADR-095 фиксирует единственный будущий путь командного интерфейса, явные входы и единственный
делегат библиотечной операции. Неявные входы, отдельная предварительная проверка,
прямые нижележащие вызовы и повторы запрещены. На этом этапе файл точки вызова
не создаётся и подтверждение отсутствует.
