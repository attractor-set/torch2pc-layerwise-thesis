# `PC-CATM`: операторная модель агрегации коррекций и переноса ошибок

[English version](pc-catm-operator-model_EN.md)

## 1. Статус, назначение и связь с `PC-TREF`

[PC-CATM](glossary.md#term-pc-catm) — нормативная механизмная модель цепочки

```math
\text{источник ошибки}
\rightarrow
\text{перенос к состоянию}
\rightarrow
\text{агрегация каналов}
\rightarrow
\text{поправка состояния}.
```

Она является механизмным слоем [PC-TREF](glossary.md#term-pc-tref), не
переименовывает установленные понятия наблюдаемости, достаточности или `factor`
`space` и не разрешает управляющее действие сама по себе. Общая семантика норм,
нуля и стоимости зафиксирована в
[теоретическом основании](pc-tref-pc-catm-theoretical-foundation.md).

Положения маркируются как математические следствия (`T`), проверяемые
инварианты (`I`), эмпирические гипотезы (`H`), правила управления (`P`) и
границы утверждений (`C`).

## 2. Измерительный контракт норм

Каждый показатель нормы связан с зарегистрированным контрактом

```math
\mathcal N=(V,\|\cdot\|,s,\epsilon,\tau,\mathcal G),
```

где задаются пространство, норма, масштаб, защита знаменателя, численный порог
и правило агрегации. Слой $l$, шаг $t$, `dtype`, устройство и версия состояния
входят в `metadata` наблюдения.

Пример относительной нормы:

```math
\|e_l^{(t)}\|_{2,\mathrm{rel}}
=
\frac{\|e_l^{(t)}\|_2}
     {\max(s_l^{(t)},\epsilon_l)}.
```

Нормы разных слоёв и временных шагов не объединяются без зарегистрированной
нормировки. Порог не выбирается после просмотра `confirmatory` `result`.

## 3. Локальная энергия и канонические каналы

Для слоя $l$:

```math
p_l=f_l(h_{l-1};\theta_l),\qquad e_l=p_l-h_l.
```

При симметричном положительно полуопределённом операторе точности $\Pi_l$:

```math
F_l=\frac12 e_l^\top\Pi_l e_l,
\qquad
r_l=\Pi_l^{1/2}e_l.
```

[Канонические каналы коррекции](glossary.md#term-canonical-correction-channel):

```math
c_l^{(\mathrm{self})}=\Pi_l e_l,
\qquad
c_l^{(\mathrm{upper})}=-J_{h,l+1}^{*}\Pi_{l+1}e_{l+1}.
```

Результирующая поправка:

```math
u_l=S_l(\mathbf c_l)=\sum_a c_l^{(a)}.
```

**I1.** Все каналы наблюдения используют совместимые версии состояния,
параметров, $\Pi_l$ и якобианов.

**I2.** Техническое разбиение одного члена энергии не меняет сумму
канонического канала и его зарегистрированные показатели.

## 4. Точные нулевые множества и `precision-masked` окрестности

Точное [множество коррекционного нуля](glossary.md#term-correction-zero-set):

```math
\mathcal Z_l^{(0)}=\ker S_l.
```

Оно распадается на

```math
\mathrm{NCZ}_l^{(0)}=\{\mathbf0\},
\qquad
\mathrm{ECZ}_l^{(0)}=\ker S_l\setminus\{\mathbf0\}.
```

Точные ядра не заменяются пороговыми классами. Операционная окрестность
задаётся как [precision-masked zero](glossary.md#term-precision-masked-zero):

```math
Z_{l,\tau}^{\mathcal N}
=
\{\mathbf c_l:\|S_l(\mathbf c_l)\|_{\mathcal N}\leq\tau_l\}.
```

`NCZ` требует малой активности всех каналов. `ECZ` требует активных каналов и
малой результирующей поправки с зарегистрированным `destructive-interaction`
условием. Между тихим и активным порогами сохраняется `activity_guard`.

**T1.** Точные `NCZ` и `ECZ` исчерпывают $\ker S_l$, но не все малые ненулевые
поправки.

## 5. Геометрия коррекции

В одном `norm` `contract`:

```math
A_l=\sum_a\|c_l^{(a)}\|_{\mathcal N},
\qquad
R_l=\left\|\sum_a c_l^{(a)}\right\|_{\mathcal N}.
```

По неравенству треугольника $0\leq R_l\leq A_l$. При $A_l>0$:

```math
\chi_l=\frac{R_l}{A_l}.
```

Для `inner-product-compatible` нормы:

```math
Q_l=\sum_a\|c_l^{(a)}\|^2,
```

```math
P_l=2\sum_{a<b}\max(\langle c_l^{(a)},c_l^{(b)}\rangle,0),
```

```math
N_l=2\sum_{a<b}\max(-\langle c_l^{(a)},c_l^{(b)}\rangle,0),
```

и $R_l^2=Q_l+P_l-N_l$. [Разрушительное взаимодействие](glossary.md#term-destructive-interaction):

```math
D_l=\frac{N_l}{\max(Q_l+P_l,\epsilon_l)}.
```

Пороговые `ECZ` `claims` требуют одновременно активность, малую $\chi_l$ и
зарегистрированное условие $D_l$. Малое $R_l$ без этих условий не считается
компенсацией.

## 6. Перенос ошибки к состоянию

```math
\widetilde J_{h,l+1}=\Pi_{l+1}^{1/2}J_{h,l+1},
\qquad
c_l^{(\mathrm{upper})}=-\widetilde J_{h,l+1}^{*}r_{l+1}.
```

Точная [TNZ](glossary.md#term-tnz):

```math
\mathrm{TNZ}_l^{(0)}
=
\ker(\widetilde J_{h,l+1}^{*})\setminus\{0\}.
```

[Направленный коэффициент переноса](glossary.md#term-directional-transport-gain):

```math
\gamma_{h,l}
=
\frac{\|\widetilde J_{h,l+1}^{*}r_{l+1}\|_{\mathcal N_{out}}}
     {\max(\|r_{l+1}\|_{\mathcal N_{in}},\epsilon_l)}.
```

Входная и выходная нормы указываются явно. Накопленный перенос вычисляется
непосредственно; произведение локальных коэффициентов не используется как
основной `estimator`.

## 7. Блочная безматричная проба и кандидаты B1/B2

[Блочная проба Якобиана](glossary.md#term-block-jacobian-probe) вычисляет
на одном замороженном снимке несколько VJP/`JVP` без материализации полного
якобиана. Сравниваются изолированный B1, составной B2 и при необходимости
блочно-составной вариант.

**C1.** Один логический `autograd` `call` не означает один GPU `kernel`, меньшую
асимптотику, память или `runtime`.

**I3.** Замороженная проба не заменяет последовательный `Strict` до
`candidate-specific` `numerical-equivalence` `gate`.

B1/B2 `preregistration` должна фиксировать `norm` `contracts`, `state`/`RNG` `restoration`,
сравниваемые `endpoints`, `cost` `vector` и `fallback` `rule`.

## 8. Параметрический ноль как ограниченное расширение

```math
\widetilde J_{\theta,l}=\Pi_l^{1/2}J_{\theta,l},
\qquad
K_{\theta,l}=\widetilde J_{\theta,l}\widetilde J_{\theta,l}^{*}.
```

[PNZ](glossary.md#term-pnz):

```math
\mathrm{PNZ}_l^{(0)}
=
\ker(\widetilde J_{\theta,l}^{*})\setminus\{0\}.
```

**T2.** $\ker K_{\theta,l}=\ker\widetilde J_{\theta,l}^{*}$.

`PNZ` означает только локальную `first-order` недоступность ошибки параметрам слоя
и остаётся ограниченным расширением.

## 9. Разделение стоимости

`PC-CATM` `features` могут создавать три разные стоимости:

1. [стоимость диагностического механизма](glossary.md#term-diagnostic-mechanism-cost);
2. [стоимость наблюдателя](glossary.md#term-observer-cost);
3. [стоимость управляющего контура](glossary.md#term-control-plane-cost).

`SI-MA1` проверил вторую границу в зарегистрированном `observer-calibrated`
контракте. Его `over-closure` не вычитается из первой или третьей компоненты.
`Future` `end-to-end` `analysis` использует [вектор стоимости](glossary.md#term-cost-vector).

## 10. Сходимость и границы утверждений

Различаются:

```math
u_l=0,
\quad
u_l=0\ \forall l,
\quad
\nabla_HF=0,
\quad
\Phi(H)=H,
\quad
\nabla_\theta F=0.
```

Поэтому `ECZ` не доказывает ложную сходимость, `NCZ` — знакомость входа,
`TNZ` — отсутствие верхней ошибки, а `PNZ` — глобальную необучаемость.
Нулевая или `precision-masked` поправка одного слоя не разрешает пропуск
вычисления.

## 11. Управление и обязательные проверки

[Точная контрфактическая проверка](glossary.md#term-exact-verification)
связывает признаки с `task-relative` `utility`. [Опасный пропуск](glossary.md#term-dangerous-miss)
блокирует `active` `control`.

Обязательные детерминированные проверки включают exact и `near-zero` `NCZ/ECZ`,
ортогональность, трёхканальную компенсацию, `invariant` `channel` `subdivision`,
масштабированный $J=cI$, exact/`near` `TNZ`, `block` `probe`, `PNZ` `control` и
безопасную обработку нулевых векторов. Каждая `near-zero` проверка ссылается на
явный `norm` `contract`.

## 12. Гипотезы

- **`H-CZ1`:** `geometry` даёт дополнительную информацию о `next-sweep` `utility`
  сверх `residual-only` `features`;
- **`H-T1`:** `transport` `features` различают внутреннюю `NCZ` и затухание;
- **`H-Q1`:** `geometry`, `transport`, `persistence` и `uncertainty` уменьшают
  `dangerous` `misses`;
- **`H-R1`:** прошедшее `safety` `gate` сокращение exact `sweeps` уменьшает
  `end-to-end` `runtime` после учёта всех `cost` `components`.

Неподтверждённые гипотезы сохраняются как отрицательные или смешанные
результаты.
