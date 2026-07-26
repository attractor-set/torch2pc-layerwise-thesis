# ADR-050: фиксация семантики и области `QW-LC0`

[English version](ADR-050-stage3b-qwake-lc0-semantics-scope-freeze_EN.md)

- **Статус:** принято как `QW-LC0`; [выполнение](../glossary.md#term-execution) закрыто
- **Дата:** 25 июля 2026 года

## Контекст

Переход после слияния PR №111 открыл только документационную фиксацию
`QW-LC0`. [Доказательные материалы](../glossary.md#term-evidence) базовой
проверки уже запечатаны, но они не содержат реализацию или проверку
`LOCAL_COMPUTE`.

Предыдущие решения задают временной фронтир, особый случай `FixedPred` при
`eta=1`, полный канонический суффикс и закрытые разрешения. Текущий срез должен
устранить последнюю неоднозначность между результатом, способом получения,
ресурсным путём и стоимостью, не присваивая кандидату ещё не полученные свойства.

## Решение

### 1. Четыре независимых объекта

Для действия `a` из состояния `s` нормативно различаются:

1. [требуемый результат](../glossary.md#term-required-result) `R(a,s)` —
   зарегистрированный относительно задачи ответ;
2. [вычислительный механизм](../glossary.md#term-computational-mechanism) `M(a)` —
   зарегистрированный алгоритмический путь;
3. [ресурсная траектория](../glossary.md#term-resource-trajectory) `Γ(a,s)` —
   упорядоченные измеряемые ресурсные события от начала действия до результата
   или резервного перехода;
4. [вектор стоимости](../glossary.md#term-cost-vector)
   `C(a,s)=Φ(Γ(a,s))` — решенческое представление измеренной ресурсной
   траектории.

Равенство `R` не определяет равенство `M`, `Γ` или `C`. Конкретная сериализация
ответа и оператор [эквивалентности по результату](../glossary.md#term-response-equivalence)
фиксируются в `QW-LC1`.
Измерительная схема `Γ`, отображение `Φ` и оператор
[эквивалентности по стоимости](../glossary.md#term-cost-equivalence) фиксируются
в `QW-LC2`.

### 2. Семейство действий

`LOCAL_COMPUTE` содержит ровно два вида:

```text
LOCAL_SWEEP
ANALYTIC_COMPLETION
```

`LOCAL_SWEEP` означает явное зарегистрированное локальное обновление на
ограниченном агрегате. `ANALYTIC_COMPLETION` означает зарегистрированное
аналитическое получение требуемого ответа без явного воспроизведения всей
последовательности локальных обновлений.

Наличие возможности не является разрешением. Ни один вид не может сам разрешить
`ACCEPT_FRONTIER`; полный `COMPLETE_SUFFIX` остаётся обязательным точным
резервным действием.

### 3. Единственный первый кандидат

Первый [кандидат](../glossary.md#term-candidate) имеет идентификатор
`fixedpred_eta1_wavefront_completion_v1` и одновременно ограничен:

```text
algorithm=FixedPred
eta=1
architecture=lenet_classic
executor=stage2_baseline
mode=shadow_post_action_validation
```

Кандидат пока не проверен на эквивалентность, безопасность, покрытие или
стоимость. Он не распространяется на `Strict`, другие значения `eta`, другие
[архитектуры](../glossary.md#term-architecture), произвольные графы,
соединения с пропусками, универсальный символьный решатель, восстановление полной
траектории или активное управление.

### 4. Граница утверждений

`QW-LC0` подтверждает только:

- разделение `R/M/Γ/C`;
- конечный состав `LOCAL_COMPUTE`;
- ограниченную область первого кандидата;
- последовательность последующих фиксаций.

Он не подтверждает эквивалентность ответа, превосходство по стоимости,
корректность реализации, пригодность политики, переносимость, готовность к
развёртыванию или научный результат.

### 5. Отложенные фиксации

```text
QW-LC1 = схема ответа, обязательные наблюдаемые величины, ~R
QW-LC2 = измеряемая Gamma, отображение Phi, ~C
QW-LC3 = сопоставленная теневая проверка и точный резерв
QW-LC4-I = ограниченная реализация
QW-LC4-F = образ расширения и одноразовое разрешение
QW-LC4-E = запечатанная инженерная проверка
```

## Машиночитаемая фиксация

Контракт запечатан как:

```text
experiments/frozen/stage3b-qwake-lc0-semantics-scope-v1/contract.json
experiments/frozen/stage3b-qwake-lc0-semantics-scope-v1/SHA256SUMS
```

## Граница выполнения

```text
qwake_qw_lc0_semantics_scope_frozen=true
qwake_qw_lc0_contract_id=stage3b-qwake-lc0-semantics-scope-v1
qwake_qw_lc1_transition_permitted=false
qwake_qw_lc1_open=false
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
feature_collection_permitted=false
oracle_label_generation_open=false
policy_activation_permitted=false
qwake_scientific_image_freeze_permitted=false
scientific_execution_open=false
c1_collection_open=false
c2_calibration_open=false
c3_confirmatory_open=false
replication_open=false
test_dataset_access=false
publication_permitted=false
qwake_next_slice=QW-LC0-repository-freeze
qwake_post_merge_next_slice=QW-LC1
```

Срез не вызывает модель, не читает тензоры и не создаёт эталонные метки после
действия. Отрицательный результат следующих этапов сохраняется без изменения
критериев.
