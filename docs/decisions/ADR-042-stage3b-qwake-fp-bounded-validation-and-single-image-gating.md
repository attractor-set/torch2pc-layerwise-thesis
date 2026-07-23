# `ADR-042`: ограниченная проверка `QWake-FP` и единый образ с `permission` `gates`

[English version](ADR-042-stage3b-qwake-fp-bounded-validation-and-single-image-gating_EN.md)

- **Статус:** принято как `docs-only` `scope` `freeze` после `ADR-041`; научное [выполнение](../glossary.md#term-execution) не разрешено
- **Дата:** 2026-07-23

## Контекст

`ADR-041` ограничил обязательное ядро временными префиксами `FixedPred`,
вложенными наблюдениями `A0 / A1 / A2`, конечным аналитическим реестром,
теневым допуском и полным каноническим суффиксом. Однако оставались две
практические неоднозначности.

Во-первых, общая [архитектура](../glossary.md#term-architecture) `QWake-PC` могла читаться как объект, который
магистерская работа должна подтвердить во всём пространстве `predictive` `coding`.
Такой вывод не поддерживается одним ограниченным экспериментом и создаёт
чрезмерный `scope`. Во-вторых, последовательное добавление кода между сбором,
калибровкой и подтверждающей проверкой ухудшило бы сравнимость кампаний и
создало повторные циклы сборки, `backport` и валидации.

Особый случай исправленного `FixedPred` Розенбаума при `eta=1` предоставляет
конечный канонический суффикс и точный `post-action` `reference`. Он подходит для
ограниченной проверки одной конкретной реализации механизма, но не для
утверждения общей переносимости `QWake-PC`.

## Решение

1. Сохранить `QWake-PC` как общую протокольно ограниченную спецификацию класса
   контроллеров, а не как один подтверждённый алгоритм.
2. Ввести `QWake-FP` как единственную обязательную конкретную реализацию
   магистерской работы.
3. Ограничить экспериментальную проверку исправленным особым случаем
   Розенбаума: `FixedPred`, `eta=1`, зарегистрированная последовательная
   архитектура, канонический `stage2_baseline` и конечный `depth-bounded` `suffix`.
4. Проверять последовательно: существование достаточных частичных состояний,
   их дешёвую `pre-action` распознаваемость, безопасность допуска, `coverage` и
   полную стоимость.
5. Заранее реализовать один конечный `superset` `pipeline`, содержащий обязательные
   сборщики, аналитику, `oracle`, `replay`, `baselines` и `evaluators`.
6. После полного `pre-freeze` тестирования собрать и зафиксировать один `immutable`
   `scientific` `image`. Между доказательными стадиями `executable` `code` и
   зависимости не меняются.
7. Не использовать обозначения `A1/A2/A3` для стадий кампании, чтобы не
   смешивать их с уровнями наблюдения. Стадии называются:
   `C1_COLLECTION`, `C2_CALIBRATION`, `C3_CONFIRMATORY` и `R_REPLICATION`.
8. Активировать встроенные возможности только через хешированный
   `fail-closed` `permission` `manifest`. `Manifest` может выбирать лишь заранее
   зарегистрированные `capabilities` и `entrypoints`; произвольный код, `shell`,
   `plugin` или формула через `manifest` запрещены.
9. Размещать `permission` `checks` на границах эффектов внутри доменных функций, а
   не только в `CLI` или `wrapper`. Выключенная `capability` не вызывается, не читает
   `tensor`, не выделяет память, не синхронизирует устройство и не создаёт `output`.
10. Разделить `code` `identity`, `campaign` `request` и `policy` `manifest`. Замороженная
    `policy` является данными для встроенного интерпретатора, а не новым кодом.
11. Разрешить `selection`/`freeze` `policy` только в `C2_CALIBRATION`; сочетание
    выбора `policy` и доступа к `confirmatory` `partition` всегда запрещено.
12. Открывать каждую следующую стадию только по валидной цепочке `sealed`
    `receipts` предыдущих стадий и при совпадении `image`/`code` `identities`.
13. Выполнять `C3_CONFIRMATORY` на `untouched` `model` `seeds` с уже замороженной
    `policy`. После `test` `access` запрещены новые признаки, `thresholds`, `baselines`,
    `analytic` `order`, `defect` и `cost` `mapping`.
14. Выполнить одну `replication` без `retuning` на заранее выбранной дополнительной
    конфигурации, предпочтительно `MNIST` с той же архитектурой.
15. Сохранить публикационно сильный минимальный пакет: простые `baselines`,
    вложенные `ablations`, `seed-level` `safety`, полный `overhead` и открываемый
    `trajectory` `benchmark`.
16. Оставить `Strict`, `arbitrary` `eta`, `recursive` `multiscale` `control`, `learned`
    `controller`, `contextual` `bandit` и `online` `intervention` вне обязательного
    магистерского `scope`.
17. Не открывать сбор, `oracle` `labels`, `calibration`, `confirmatory`, `replication`,
    `policy` `selection` или `test` `access` этим ADR.

## Доказательные стадии

```text
C1_COLLECTION
  -> полные trajectories, A0/A1/A2, analytic outputs, costs, canonical suffix,
     post-action labels и opportunity evidence

C2_CALIBRATION
  -> recognizability analysis, baseline comparison, одна frozen QWake-FP policy

C3_CONFIRMATORY
  -> untouched shadow evaluation: safety -> coverage -> net cost

R_REPLICATION
  -> та же policy и тот же image без retuning на заранее выбранной конфигурации
```

Все `policy` `candidates` и `ablations`, совместимые с полной `trajectory` `schema`,
оцениваются `offline` `replay`. Отдельная GPU-кампания на каждый `baseline` не
требуется.

## `Capability` `boundary`

Минимальный закрытый реестр включает `capabilities` сбора `A0/A1/A2`,
зарегистрированной аналитики, полного `suffix`, `post-action` `oracle`, доступа к
`partition`, `opportunity`/`recognizability` `analysis`, выбора и заморозки `policy`,
`shadow` `execution`, `confirmatory`/`replication` `evaluation`, `sealing` и `publication`.

Следующие сочетания всегда недопустимы:

```text
SELECT_POLICY + ACCESS_CONFIRMATORY_DATA
C3_CONFIRMATORY + FREEZE_POLICY
C1_COLLECTION + EXECUTE_SHADOW_POLICY
C2_CALIBRATION + PUBLISH_RESULTS
R_REPLICATION + RETUNE_POLICY
```

Неизвестная `capability`, отсутствующий `receipt`, несовместимый `role` или
несовпадающий `digest` приводят к `EXECUTION_AUTHORIZED=false`.

## Нормативное первенство

```text
adr039_authority=dus_outcome_semantics
adr040_authority=historical_integrated_frontier_design
adr041_authority=current_transition_admission_cost_and_scope_semantics
adr042_authority=qwake_fp_validation_scope_and_single_image_permission_protocol
historical_adr_rewrite_permitted=false
```

`ADR-042` не меняет математическую семантику `ADR-039`–`ADR-041`. Он уточняет
только объект экспериментального подтверждения, доказательные стадии и способ
активации заранее замороженного кода.

## Машинная граница

```text
qwake_general_specification_frozen=true
qwake_fp_only_mandatory_implementation=true
qwake_fp_validation_case=corrected_rosenbaum_fixedpred_eta1
qwake_fp_canonical_executor=stage2_baseline
qwake_fp_mode=shadow_only
qwake_fp_generalization_claim=false
execution_image_strategy=single_immutable_superset_image
same_image_digest_required_across_c1_c2_c3_r=true
executable_code_changes_after_image_freeze=false
campaign_roles=C1_COLLECTION,C2_CALIBRATION,C3_CONFIRMATORY,R_REPLICATION
stage_activation=fail_closed_permission_manifest
permission_checks_at_effect_boundaries=true
disabled_capability_executes=false
manifest_arbitrary_code_loading=false
manifest_shell_command_loading=false
policy_representation=frozen_data_manifest
policy_interpreter_embedded_in_image=true
policy_selection_permitted_role=C2_CALIBRATION
confirmatory_access_permitted_role=C3_CONFIRMATORY
policy_selection_with_confirmatory_access_forbidden=true
sealed_receipt_chain_required=true
untouched_confirmatory_seeds_required=true
replication_without_retuning_required=true
publication_baselines_required=true
nested_ablation_required=true
trajectory_benchmark_planned=true
safety_precedes_coverage_precedes_cost=true
qwake_fp_scope_freeze_complete=true
qwake_fp_execution_permitted=false
c1_collection_open=false
c2_calibration_open=false
c3_confirmatory_open=false
replication_open=false
oracle_label_generation_open=false
feature_collection_permitted=false
policy_activation_permitted=false
test_dataset_access=false
full_stage3b_campaign_complete=false
```

## Следствие

Следующий допустимый `slice` является только реализацией `pure` `contracts`,
`permission` `matrix`, `receipt` `verifier`, `superset` `schema` и `synthetic`/`non-interference`
тестов. Финальный образ можно замораживать лишь после завершения всего
обязательного кода и `pre-freeze` `validation`. Любая научная кампания требует
отдельного `request` `freeze`, `runtime` `preflight` и `authorization`.
