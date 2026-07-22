# Stage 3B `EX-IF0`: фиксация точной реализации и oracle-границы свипов

[English version](STAGE3B-EX-IF0_EN.md)

Статус: **проектный контракт зафиксирован; выполнение и создание меток закрыты**.

## 1. Цель

`EX-IF0` фиксирует [точную реализацию](../../docs/glossary.md#term-exact-implementation-freeze), относительно которой последующие офлайн-ветви будут вычислять task-relative regret, [oracle-запас достаточности](../../docs/glossary.md#term-oracle-sufficiency-margin) и минимальный устойчиво достаточный номер свипа.

Машиночитаемый источник истины:

```text
experiments/frozen/stage3b-ex-if0-design-v1/contract.json
```

Эта фиксация не запускает новые вычисления, не создаёт oracle-метки, не собирает признаки и не активирует управление.

## 2. Выбор точной реализации

Опубликованный сопоставленный анализ сохранил оба новых точных кандидата — `isolated_layer_vjp` и `composite_vjp` — со статусом `reject_or_revise` для `FixedPred` и `Strict`. Поэтому ни B1, ни B2 не заменяют обязательный резервный путь.

`EX-IF0 v1` выбирает:

```text
selected_candidate_id=stage2_baseline
selected_role=canonical_exact_reference_and_fail_closed_fallback
selected_methods=fixedpred,strict
selection_is_superiority_claim=false
```

Выбор B0 означает сохранение уже проверенного точного пути, а не утверждение его универсального превосходства. B1/B2 остаются опубликованными численно допустимыми исследованными кандидатами со своими инженерными решениями `reject_or_revise`.

## 3. Полная reference-траектория

Для каждой зарегистрированной конфигурации число reference-свипов

\[
K_{\mathrm{ref}}
\]

равно закреплённому `inference_steps` соответствующих метода и конфигурации. Адаптивная ранняя остановка reference-траектории запрещена.

Состояние

\[
S_t
\]

определяется после завершения свипа `t`, причём `S_0` — инициализированное состояние до первого свипа. Решение о потенциальной остановке относится к моменту после готовности `S_t` и до начала свипа `t+1`.

## 4. Task-relative endpoint

Для каждого `S_t` вычисляется endpoint-readout

\[
Y_t=\Gamma(S_t),
\]

содержащий:

- именованные тензоры параметрических градиентов;
- конечные `beliefs` зарегистрированных слоёв;
- конечный `loss`;
- обязательные проверки формы, конечности и происхождения.

Точный endpoint:

\[
Y_{\mathrm{ref}}=\Gamma(S_{K_{\mathrm{ref}}}).
\]

Полная промежуточная траектория не обязана совпадать с более коротким префиксом: достаточность в этом контракте относится к требуемому endpoint-ответу.

## 5. Regret и signed margin

Для профиля `rocm_float32` заморожены существующие B1/B2 пороги:

```text
max_abs=1e-5
max_relative_l2=1e-3
min_cosine=0.999
zero_atol=1e-7
```

По всем зарегистрированным компонентам используется максимальное нормированное нарушение без усреднения:

\[
r_\Gamma(t)=\max\left(
\frac{E_{\mathrm{abs}}(t)}{\tau_{\mathrm{abs}}},
\frac{E_{\mathrm{rel}}(t)}{\tau_{\mathrm{rel}}},
\frac{1-C(t)}{1-\tau_{\cos}}
\right).
\]

Структурное несоответствие, неконечное значение или несовпадение компонент дают

\[
r_\Gamma(t)=+\infty.
\]

Signed margin:

\[
M^*(t)=1-r_\Gamma(t).
\]

Свип `t` достаточен тогда и только тогда, когда

\[
M^*(t)\geq 0.
\]

Стоимость не может компенсировать отрицательный запас.

## 6. Минимальный устойчиво достаточный свип

Первое случайное прохождение порога не считается достаточным. Используется полная устойчивость суффикса:

\[
t^*=\min\left\{t:\;M^*(j)\geq0\quad\forall j\in[t,K_{\mathrm{ref}}]\right\}.
\]

`S_K_ref` обязан пройти self-check по тождеству. Если точный endpoint не проходит собственную проверку, весь набор закрывается при ошибке.

Для каждого состояния будущая oracle-таблица должна хранить:

```text
sufficient_at_t
exact_reference_regret
oracle_sufficiency_margin_M_star
minimum_stably_sufficient_sweep_t_star
remaining_unnecessary_sweeps
```

Но этот документ не создаёт такую таблицу.

## 7. Контрфактические ветви

Схема сохраняет метки:

```text
stop
native_one
exact_one
```

Они являются post-action данными офлайн-набора, а не действиями контроллера. В `EX-IF0 v1` и `native_one`, и `exact_one` используют выбранный `stage2_baseline`; поэтому ожидается их identity-equivalence. Допускается одно физическое выполнение с двумя логическими метками, если происхождение явно фиксирует alias и endpoint fingerprints совпадают.

Разделение одного snapshot требует восстановления параметров, optimizer, `beliefs`, batch, RNG и конфигурации метода.

## 8. Граница признаков и меток

Pre-action представление для решения после `S_t` может использовать только информацию, материализованную не позднее `S_t`.

В признаки запрещено включать:

- будущие состояния `S_{t+1},...,S_K_ref`;
- `Y_ref`;
- `M^*(t)`;
- `t^*`;
- результаты контрфактических ветвей.

Все перечисленные величины являются post-action oracle-метками. Сбор уровней `A0/A1/A2`, обучение оценивателя и теневой каскад требуют следующих отдельных контрактов.

## 9. Иерархия агрегатов

Временное семейство уже определено префиксами полной reference-траектории:

\[
P_0\subset P_1\subset\cdots\subset P_{K_{\mathrm{ref}}}.
\]

Для пространственного исследования заморожена только нормативная форма:

\[
B_0=\varnothing\subset B_1\subset\cdots\subset B_K=R.
\]

Обязательны минимум два масштаба:

1. слои внутри зарегистрированного блока;
2. блоки внутри сети.

Точный состав пространственных кандидатов должен быть отдельно зафиксирован до создания меток `A11-OFF0`. Перебор всех подмножеств запрещён; допускаются только заранее зарегистрированные вложенные префиксы. Отдельное действие `GLOBAL` не вводится, а полный root-свип остаётся максимальным агрегатом.

## 10. Ошибки и безопасность

Будущий [опасный пропуск](../../docs/glossary.md#term-dangerous-miss) — предложение `stop` при `M^*(t)<0`. Для будущего confirmatory admission допустимое число таких ошибок равно нулю. Ошибка `continue`, когда свип уже достаточен, безопасна по качеству, но учитывается как вычислительная потеря.

До отдельной preregistration оцениватель не существует и не может использовать abstention. Полный `stage2_baseline` остаётся [резервным переходом](../../docs/glossary.md#term-fallback).

## 11. Зафиксированная граница

```text
ex_if0_opened=true
ex_if0_complete=true
ex_if0_protocol_frozen=true
exact_implementation_frozen=true
exact_implementation_candidate=stage2_baseline
minimum_sufficient_sweep_rule_frozen=true
ex_if0_execution_permitted=false
oracle_label_generation_open=false
feature_collection_permitted=false
recursive_aggregate_execution_open=false
a11_off0_execution_open=false
policy_activation_permitted=false
test_dataset_access=false
full_stage3b_campaign_complete=false
```

Следующий допустимый переход — отдельная preregistration конкретной иерархии, snapshot-ветвления и oracle trace generation для `A11-OFF0`. Никакое выполнение не открывается автоматически.
