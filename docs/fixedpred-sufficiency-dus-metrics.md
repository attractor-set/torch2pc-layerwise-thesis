# Реестр метрик `DONE / UNKNOWN / SWEEP`

[English version](fixedpred-sufficiency-dus-metrics_EN.md)

**Статус:** проектный реестр; результаты отсутствуют.

## Назначение документа

Документ задаёт не одну сводную оценку, а иерархию проверок, в которой
безопасность имеет безусловный приоритет. Сначала исключаются утечка данных,
вмешательство наблюдателя, превышение бюджета и преждевременное завершение.
Затем измеряется, какую долю действительно достаточных состояний можно
распознать без опасных решений. Только после этого сравниваются стоимость
приобретения признаков, предотвращённая стоимость последующих свипов и
эффективность порядка приобретения. Такое разделение не позволяет хорошему
среднему времени скрыть редкое, но недопустимое преждевременное завершение.

Состояние `UNKNOWN` рассматривается как самостоятельный научный объект. Оно
позволяет отделить отсутствие вычислительной достаточности от отсутствия
дешёвого способа её распознать. Поэтому высокая доля `UNKNOWN` может означать
не слабость `FixedPred`, а ограниченную наблюдаемость выбранного набора
пассивных признаков. Аналогично `SWEEP` разделяется по причинам: доказанная
недостаточность, исчерпание диагностического бюджета, отсутствие доступной
аналитики или закрытие при нарушении контракта.

## 1. Лексикографический порядок

Метрики применяются в порядке:

$\text{safety} \rightarrow \text{coverage} \rightarrow \text{cost}.$

Экономия стоимости не компенсирует нарушение `safety`.

## 2. Жёсткие инварианты

```text
invariant_violations=0
post_action_feature_leakage=0
observer_interference_events=0
budget_overspend_events=0
post_terminal_acquisition_events=0
duplicate_acquisition_events=0
invalid_done_permissions=0
oracle_used_as_feature=0
controls_execution=false
test_dataset_access=false
```

## 3. Метрики `DONE`

[Опасное DONE](glossary.md#term-dangerous-done):

$N_{\mathrm{dangerous\ D}} = \#\{A_t=D\land O_t=0\}.$

`Selective` `risk`:

$R_D= \frac{N_{\mathrm{dangerous\ D}}} {\max(\#\{A_t=D\},1)}.$

Безопасное покрытие:

$C_D^{\mathrm{safe}} = \frac{\#\{A_t=D\land O_t=1\}}{N}.$

Также публикуются:

- `risk`–`coverage` `curve`;
- `coverage` при зарегистрированном ограничении риска;
- верхняя доверительная граница риска;
- задержка распознавания $\Delta t_D=t_D-t^*$;
- доля пропущенных ранних возможностей.

## 4. Метрики `UNKNOWN`

[Диагностический разрыв наблюдаемости](glossary.md#term-diagnostic-observability-gap):

$G_{\mathrm{obs}} = P(O_t=1,A_t=U).$

Дополнительно:

- общий `UNKNOWN` `rate`;
- `UNKNOWN → DONE`;
- `UNKNOWN → SWEEP`;
- число приобретённых аналитик;
- стоимость пребывания в `UNKNOWN`;
- `budget-exhaustion` `rate`;
- `no-affordable-acquisition` `rate`;
- `cascade-exhaustion` `rate`;
- `resolution` `yield` на единицу `diagnostic` `cost`.

## 5. Метрики `SWEEP`

Необходимая точность `SWEEP`:

$P_S= \frac{\#\{A_t=S\land O_t=0\}} {\max(\#\{A_t=S\},1)}.$

Избежимый `SWEEP`:

$R_{\mathrm{avoidable\ S}} = \frac{\#\{A_t=S\land O_t=1\}} {\max(\#\{A_t=S\},1)}.$

Избыточное вычисление:

$K_{\mathrm{over}} = K_{\mathrm{executed}}-t^*.$

Причины `SWEEP` сохраняются отдельно:

```text
insufficiency_certified
budget_exhausted_unknown
no_affordable_acquisition_unknown
cascade_exhausted_unknown
invalid_fail_closed
out_of_scope_fail_closed
```

## 6. Стоимость

$C_{\mathrm{total}} = C_{\mathrm{sweeps}} + C_{\mathrm{observer}} + C_{\mathrm{diagnostics}}.$

$V_{\mathrm{net}} = C_{\mathrm{avoided\ sweeps}} - C_{\mathrm{observer}} - C_{\mathrm{diagnostics}}.$

Публикуются `normalized` `reference` `cost`, `diagnostic-cost` `ratio`, `cost` `per` `safe`
`DONE`, `oracle-policy` `regret`, `acquisition-sequence` `regret`, `expected` `executed`
`sweeps` и `terminal-time` `distribution`.

## 7. Перенос полезных идей

**`Selective` `prediction`**

Переносятся `selective` `risk`, `coverage`, `abstention` и `risk`–`coverage` `curve`.

**`Active` `Feature` `Acquisition`**

Переносятся конечный `registry`, `unused-analytic` `state`, `acquisition` `cost`,
`fixed` `cascade`, `cheapest-first`, `greedy` `quality`/`cost` и `offline` `oracle` `order`.

**`Adaptive` `computation`**

Переносятся `expected` `step` `count`, `stopping-time` `distribution` и
`over-computation`. `Learned` `stochastic` `halting` не входит в обязательный `scope`.

**`Finite-sample` `risk` `control`**

До анализа фиксируется конечное семейство $(\phi_k,\tau_j)$. Порядок выбора:

$\text{risk admission} \rightarrow \text{coverage selection} \rightarrow \text{cost selection}.$

Независимая единица — `model_seed`, а не `layer`, `sweep` или `analytic` `event`.

## 8. `Baselines`

```text
B-DUS-00 always_sweep_full_reference
B-DUS-01 oracle_done_upper_bound
B-DUS-02 rosenbaum_structural_wavefront
B-DUS-03 registered_prediction_error_or_residual_threshold
B-DUS-04 residual_threshold_with_persistence
B-DUS-05 fixed_metric_cascade
B-DUS-06 cheapest_first
B-DUS-07 greedy_quality_only
B-DUS-08 greedy_quality_per_cost
B-DUS-09 all_metrics
B-DUS-10 offline_oracle_acquisition_order
B-DUS-11 deterministic_analytic_registry
```

`Greedy` `policy` является только `shadow-demonstrator`.

## 9. Методические источники

- [Hybrid Predictive Coding](https://doi.org/10.1371/journal.pcbi.1011280);
- [SelectiveNet](https://proceedings.mlr.press/v97/geifman19a.html);
- [Learn then Test](https://arxiv.org/abs/2110.01052);
- [Distribution Guided Active Feature Acquisition](https://arxiv.org/abs/2410.03915);
- [Adaptive Computation Time](https://arxiv.org/abs/1603.08983);
- [Joint Active Feature Acquisition](https://proceedings.neurips.cc/paper_files/paper/2018/hash/e5841df2166dd424a57127423d276bbe-Abstract.html);
- [Learning to select computations](https://arxiv.org/abs/1711.06892).
