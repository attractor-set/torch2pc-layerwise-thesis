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
