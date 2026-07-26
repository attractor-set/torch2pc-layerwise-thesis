# ADR-053: схема требуемого результата `QW-LC1`

[English version](ADR-053-stage3b-qwake-lc1-required-response-schema_EN.md)

- Статус: принято
- Дата: 26 июля 2026 года

## Контекст

Переход `QW-LC1` слит в `main` коммитом `c3533fcb63ffc869faddbaa99645c9099d16d1cc` и повторно
проверен. Разрешён только срез, который фиксирует каноническую схему
[требуемого результата](../glossary.md#term-required-result) `R(a,s)`,
обязательные наблюдаемые поля и операционный предикат
[эквивалентности по результату](../glossary.md#term-response-equivalence)
`~R`.

Схема должна позволять сравнивать `LOCAL_SWEEP` и `ANALYTIC_COMPLETION`,
не отождествляя ответ с [вычислительным механизмом](../glossary.md#term-computational-mechanism),
[ресурсной траекторией](../glossary.md#term-resource-trajectory) или
[вектором стоимости](../glossary.md#term-cost-vector).

## Решение

1. Зафиксировать контракт `stage3b-qwake-lc1-required-response-schema-v1`.
2. Определить `R(a,s)` как упорядоченную тройку:
   - именованные градиенты параметров;
   - конечные представления в зарегистрированном порядке слоёв;
   - скалярную конечную функцию потерь.
3. Задать каноническую сериализацию как манифест `JSON` и отдельные файлы
   полезных данных с порядком байтов от младшего к старшему и непрерывным
   порядком `C`, без численного приведения.
4. Сделать обязательными структурные поля, манифесты, признаки конечности и
   `SHA-256` каждого файла полезных данных и всего ответа.
5. Проверять структуру точно до численного сравнения. Численные значения
   сравнивать в `float64` отдельно для каждой зарегистрированной записи.
6. Зафиксировать правило, безопасное для нулевых норм:
   - две неактивные записи проходят условие косинусного сходства, но обязаны
     пройти пределы `relative_l2` и `max_abs`;
   - одна активная и одна неактивная запись всегда дают отказ;
   - две активные записи дополнительно обязаны пройти `min_cosine`.
7. Зафиксировать профили `cpu_float64_engineering` и
   `rocm_float32_canonical`; решенческим остаётся ROCm/float32.
8. Не считать `~R` транзитивным и не строить классы эквивалентности без
   отдельного замыкания.
9. Отложить сопоставление состояния, генераторов и резервного пути до
   `QW-LC3`, а `Γ`, `Φ`, `C` и `~C` — до `QW-LC2`.
10. Сохранить реализацию и [выполнение](../glossary.md#term-execution)
    закрытыми.

## Оператор `~R`

После точной структурной проверки для каждой записи вычисляются:

```text
difference_l2 = ||candidate - reference||_2
max_abs       = ||candidate - reference||_∞
scale         = max(||reference||_2, ||candidate||_2, zero_atol)
relative_l2   = difference_l2 / scale
```

Для двух активных записей дополнительно вычисляется [косинусное сходство](../glossary.md#term-cosine-similarity).
Нормированный дефект ответа равен максимуму дефектов всех записей; ответ принят
только при `d_R <= 1`. Точное равенство `SHA-256` достаточно, но не обязательно
для `~R`.

## Проверяемая граница

```text
qwake_qw_lc1_transition_complete=true
qwake_qw_lc1_open=true
qwake_qw_lc1_required_response_schema_frozen=true
qwake_qw_lc1_contract_id=stage3b-qwake-lc1-required-response-schema-v1
qwake_qw_lc1_contract_sha256=sha256:c7923249c538b29a34f8ffcfcac987b9925a911eb107a085a166ab1d7ca22992
mandatory_observables_definition_frozen=true
response_equivalence_operator_definition_frozen=true
qwake_qw_lc1_complete=false
qwake_qw_lc2_transition_permitted=false
resource_trajectory_schema_open=false
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
feature_collection_permitted=false
oracle_label_generation_open=false
policy_activation_permitted=false
scientific_execution_open=false
test_dataset_access=false
publication_permitted=false
qwake_next_slice=QW-LC1-repository-freeze
```

## Последствия

Контракт фиксирует только форму ответа и способ сравнения. Он не подтверждает
эквивалентность аналитического кандидата, корректность реализации, безопасность,
покрытие, экономию стоимости или переносимость за пределы зарегистрированного
случая. Следующий допустимый срез — отдельная фиксация состояния репозитория
`QW-LC1`.
