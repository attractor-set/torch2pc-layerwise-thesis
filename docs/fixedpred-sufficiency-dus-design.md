# `FixedPred`: достаточность префикса и решения `DONE / UNKNOWN / SWEEP`

[English version](fixedpred-sufficiency-dus-design_EN.md)

**Статус:** проектная фиксация; [выполнение](glossary.md#term-execution), создание `oracle`-меток, сбор признаков и управление остаются закрытыми.

## 1. Консолидированная идея

Следующий обязательный частный случай фиксирует математическую динамику
`FixedPred` и точную реализацию `stage2_baseline`:

$F=F_{\mathrm{FixedPred}}, \qquad G=G_{\mathrm{stage2\_baseline}}, \qquad S_0,S_1,\ldots,S_{K_{\mathrm{ref}}}.$

Центральный объект — [минимальный устойчиво достаточный префикс `FixedPred`](glossary.md#term-minimum-stably-sufficient-fixedpred-prefix):

$t^*= \min\left\{ t: \forall j\in[t,K_{\mathrm{ref}}], M^*(j)\geq0 \right\}.$

Работа исследует, существует ли малозатратное `pre-action` представление,
которое безопасно распознаёт $t\geq t^*$ без доступа к полному `suffix`.

## 2. Разделение уровней

Необходимо различать:

- математическую динамику метода $F_m$;
- выполненный `autograd`-граф $G$;
- номинальную аллокацию $K$, например число свипов;
- фактически реализованный [вектор стоимости](glossary.md#term-cost-vector)
  $\mathbf C$;
- `task-relative` `endpoint` $Y_t=\Gamma(S_t)$.

Поэтому:

$K_1=K_2\not\Rightarrow\mathbf C_1=\mathbf C_2,$

$Y_1\simeq_RY_2\not\Rightarrow G_1=G_2.$

Сохранение математики формулируется отдельно внутри `FixedPred` и внутри
`Strict`; эти режимы не считаются одной динамикой.

## 3. Роль завершённых этапов

### `Stage` 2

`Stage` 2 является `implementation-preserving` исследованием и создаёт
оптимизированную проверенную [базовую линию](glossary.md#term-baseline).
Он не исследует адаптивное завершение или приобретение аналитик.

### `Joint-VJP`

`Joint-VJP` является точной организацией `reverse` `computation`. Он показывает,
что один `endpoint` может быть реализован другой организацией `VJP`.

`Joint-VJP`:

- не является шоткатом;
- не является частным случаем `Rosenbaum`;
- не является `DONE`;
- не входит в алфавит действий;
- не заменяет `stage2_baseline`.

Исторические `identifiers` со словом `shortcut` сохраняются только в
неизменяемом происхождении.

### `B0`

`B0` измеряет `context-dependent` `cost` `surface` `stage2_baseline`. Он не варьирует
число свипов одного `snapshot` и не измеряет ценность приобретаемых аналитик.

`B0` мотивирует контекстную оценку предотвращаемой стоимости, но
диагностическая полезность аналитики должна измеряться отдельно.

### `B1`/`B2`

`B1`/`B2` сравнивают разные `exact` `graph` `organizations` при одинаковой номинальной
конфигурации и одинаковом `requested` `sweep` `count`. Равенство реализованного
`cost` `vector` не предполагается.

### `EX-IF0`

`EX-IF0` сохраняет `stage2_baseline` как `canonical` `exact` `reference` и
`fail-closed` `fallback`, фиксирует `decision` `epoch`, `endpoint`, допуски и правило
полного `suffix`. Новый пакет не изменяет этот контракт.

## 4. Частный случай `Rosenbaum`

[Wavefront-контроль Rosenbaum](glossary.md#term-rosenbaum-wavefront-control)
используется как аналитический положительный контроль для `FixedPred` при
$\eta=1$.

Он проверяет заранее известный порядок завершения послойных компонентов, но
не становится новым `oracle`, новым графом, действием или разрешением `global`
`DONE`.

Следует различать:

$\text{component completion} \neq \text{global endpoint completion} \neq \text{task-relative sufficiency}.$

Формулы и индексирование должны быть сверены с исходной статьёй 2022 года и
коррекцией 2025 года.

## 5. `Oracle` и теневое решение

`Post-action` `oracle` имеет два состояния:

```text
sufficient
insufficient
```

`UNKNOWN` не является `oracle`-классом.

[Семантика решений D/U/S](glossary.md#term-dus-decision-semantics)
использует:

- `DONE`: доступное представление прошло положительный `sufficiency` `admission`;
- `UNKNOWN`: информации недостаточно, но допустима ещё одна аналитика;
- `SWEEP`: выполняется ровно один следующий `canonical` `FixedPred`-свип.

Неразрешённая неопределённость закрывается консервативно:

$\texttt{UNKNOWN}(0)\rightarrow\texttt{SWEEP}.$

Стоимость, `NCZ`, `ECZ`, `inactivity` или малый `residual` сами по себе не разрешают
`DONE`.

## 6. Два бюджета

Отдельно регистрируются:

$B^{\mathrm{compute}}$

— бюджет следующих свипов;

$B^{\mathrm{diag}}$

— бюджет `pre-action` аналитик.

Диагностический бюджет ограничивает поиск доказательства, но не заменяет
положительный допуск достаточности.

## 7. Обязательный `scope`

Обязательное ядро:

1. `temporal` `prefixes` одного `stage2_baseline`;
2. `oracle` `EX-IF0`;
3. `Rosenbaum` `positive` `control`;
4. `passive` `representations`;
5. метрики `D`/`U`/`S`;
6. `deterministic` `shadow` `replay`;
7. измерение стоимости диагностики и следующего свипа.

Пространственные рекурсивные агрегаты, обучаемый `predictor`, `hysteresis` и
активное управление остаются условным расширением.

## 8. Граница утверждений

До отдельного выполнения запрещены утверждения об активном ускорении,
универсальном `early` `stopping`, глобальной оптимальности `greedy` `policy`,
автоматической `sufficiency` `NCZ`/`ECZ` и переносимости сертификатов между графами.

Допустимы отрицательные результаты:

- ранний достаточный префикс отсутствует;
- он существует, но дёшево не наблюдаем;
- диагностика дороже предотвращаемого `suffix`;
- `state` `dependence` отсутствует;
- `PC-CATM` не даёт дополнительной ценности;
- `greedy` `routing` не превосходит фиксированный порядок.
