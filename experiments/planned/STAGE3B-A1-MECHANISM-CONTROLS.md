# Stage 3B A1 — детерминированные механизмные контроли PC-CATM

[English version](STAGE3B-A1-MECHANISM-CONTROLS_EN.md)

## Статус

Протокол заморожен. Исполняемая реализация, smoke-результаты и confirmatory-результаты отсутствуют.

Этот пакет фиксирует обязательные детерминированные проверки этапов A4–A7 основного сценария A до начала `SI-MA0`. Он не изменяет опубликованные реализации и evidence предыдущих барьеров.

## Зарегистрированная отправная точка

- repository evidence commit: `0b6a9e4aa0ac665adcc82d897845a0179fa3f990`;
- OBS-OH0 implementation commit: `59dbcfa41a9c35cc8b72e75288aaa505459499d8`;
- OBS-OH0 tag: `stage3b-a1-obs-oh0-v1`;
- OBS-OH0 benchmark schema: `stage3b-a1-obs-oh0-v1`;
- passive-observer schema: `stage3b-a1-obs-ni0-first-forward-io-v1`;
- Torch2PC commit: `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4`;
- mechanism-controls contract id: `stage3b-a1-mechanism-controls-v1`.

Запечатанные `EQ-S0`, `EQ-S1`, `EQ-S2`, `OBS-NI0` и `OBS-OH0` являются immutable prerequisites. Их checksum-проверка выполняется до controlled smoke и до confirmatory execution.

## Исследовательский вопрос

Корректно ли будущая реализация PC-CATM различает и воспроизводит зарегистрированные механизмы:

1. тривиальный ноль агрегации `NCZ`;
2. нетривиальный ноль агрегации `ECZ`;
3. активную геометрию без компенсации;
4. нулевой перенос `TNZ`;
5. масштабированный и нормосохраняющий перенос;
6. временную волну FixedPred при `eta=1`;
7. изолированную, составную и блочно-составную VJP-пробу на одном замороженном снимке?

Дополнительный ограниченный вопрос: корректно ли воспроизводится линейная конструкция `PNZ` без использования её как барьера для `SI-MA0`?

## Роль пакета

Пакет является deterministic validity gate. Он проверяет определения, конструкции, индексацию, матрично-свободные VJP и совместимость с зафиксированными операторными формулами.

Положительный результат открывает preregistration `SI-MA0`, но сам по себе не подтверждает:

- частоту `NCZ`, `ECZ` или `TNZ` при обучении;
- полезность диагностических признаков для предиктора;
- достаточность диагностического фактор-пространства;
- возможность пропуска exact sweeps;
- ускорение `Strict`;
- причинную валидность PC-CATM за пределами зарегистрированных конструкций.

## Иерархия gate

Core gate состоит из четырёх обязательных sub-gates:

```text
GEO-C0  correction-geometry controls
TR-C0   state-transport controls
TMP-C0  Rosenbaum temporal-wave control
JAC-C0  frozen block-Jacobian probe
```

`SI-MA0` открывается только при:

```text
core_passed = GEO-C0 and TR-C0 and TMP-C0 and JAC-C0
```

Ограниченное расширение:

```text
PNZ-L0  deterministic linear parameter-null control
```

`PNZ-L0` выполняется и публикуется отдельно. Его статус не изменяет `core_passed` и не управляет доступом к `SI-MA0`.

## Нормативная операторная модель

Для скрытого слоя `l`:

\[
c_l^{(\mathrm{self})}=\Pi_l e_l,
\]

\[
c_l^{(\mathrm{upper})}=-J_{h,l+1}^{*}\Pi_{l+1}e_{l+1},
\]

\[
u_l=S_l(\mathbf c_l)=\sum_a c_l^{(a)}.
\]

Множество коррекционного нуля:

\[
\mathcal Z_l^{(0)}=\ker S_l.
\]

Его зарегистрированное разбиение:

\[
\mathrm{NCZ}_l^{(0)}=\{\mathbf0\},
\]

\[
\mathrm{ECZ}_l^{(0)}=\ker S_l\setminus\{\mathbf0\}.
\]

Геометрические величины:

\[
A_l=\sum_a\|c_l^{(a)}\|,
\qquad
R_l=\left\|\sum_a c_l^{(a)}\right\|,
\]

\[
\chi_l=R_l/A_l \quad (A_l>0),
\]

\[
Q_l=\sum_a\|c_l^{(a)}\|^2,
\]

\[
P_l=2\sum_{a<b}\max(\langle c_l^{(a)},c_l^{(b)}\rangle,0),
\]

\[
N_l=2\sum_{a<b}\max(-\langle c_l^{(a)},c_l^{(b)}\rangle,0),
\]

\[
D_l=N_l/(Q_l+P_l) \quad (A_l>0).
\]

Перенос ошибки к состоянию:

\[
\widetilde J_{h,l+1}=\Pi_{l+1}^{1/2}J_{h,l+1},
\]

\[
c_l^{(\mathrm{upper})}=-\widetilde J_{h,l+1}^{*}r_{l+1},
\]

\[
\mathrm{TNZ}_l^{(0)}=\ker(\widetilde J_{h,l+1}^{*})\setminus\{0\}.
\]

Направленный коэффициент переноса:

\[
\gamma_{h,l}=\frac{\|\widetilde J_{h,l+1}^{*}r_{l+1}\|}{\|r_{l+1}\|},
\qquad r_{l+1}\ne0.
\]

## Общий execution contract

Все контролируемые исполнения используют:

- contract id `stage3b-a1-mechanism-controls-v1`;
- frozen implementation source commit до первого controlled smoke;
- canonical Docker CPU lane и Docker/ROCm lane;
- CPU dtype `float64`;
- ROCm dtype `float32`;
- deterministic algorithms;
- Python, NumPy, CPU Torch и ROCm RNG snapshots;
- явную фиксацию source commit, branch, image, image revision и Torch2PC commit;
- отсутствие доступа к test split;
- отсутствие train/validation dataset в основном deterministic suite;
- synthetic tensors, operators, inputs и targets, полностью определённые contract;
- полное сохранение failed и nonfinite records;
- отсутствие удаления outliers или повторов после просмотра результатов.

Каждый record содержит:

```text
control_id
sub_gate
case_id
lane
device
dtype
model_seed
construction_seed
layer_index
sweep_index
contract_id
source_git_commit
experiment_image
image_revision
torch2pc_commit
finite
passed
```

Неприменимые индексы записываются как `null`, а не заменяются фиктивным значением.

## Сравнение тензоров

Для ненулевых reference tensors сохраняются:

- absolute L2 error;
- relative L2 error;
- maximum absolute error;
- cosine similarity;
- norm ratio;
- finite flag.

Для двух zero-like tensors cosine similarity не вычисляется. Используется zero-safe rule:

1. если обе нормы не превышают `zero_atol`, сравнение определяется через `max_abs`;
2. если zero-like только один tensor, сравнение завершается как failed;
3. cosine field записывается как `null` для пары zero-like tensors;
4. NaN и infinity всегда завершают record как failed.

## Зарегистрированные threshold profiles

### Algebraic zero

```text
CPU float64: zero_atol = 1e-12
ROCm float32: zero_atol = 1e-6
```

### Analytic vector equivalence

```text
CPU float64:
  max_relative_l2 = 1e-10
  max_abs = 1e-10
  min_cosine = 0.999999999

ROCm float32:
  max_relative_l2 = 1e-4
  max_abs = 1e-5
  min_cosine = 0.9999
```

### Implementation snapshot equivalence

```text
CPU float64:
  max_relative_l2 = 1e-7
  max_abs = 1e-9
  min_cosine = 0.99999

ROCm float32:
  max_relative_l2 = 1e-3
  max_abs = 1e-5
  min_cosine = 0.999
```

Threshold profile выбирается по типу record и фиксируется в record. Threshold retuning после первого controlled output не выполняется.

## Зарегистрированные construction seeds

Для алгебраических конструкций:

```text
construction_seed = 0 -> scale = 0.25
construction_seed = 1 -> scale = 1.0
construction_seed = 2 -> scale = 4.0
```

Основное пространство — `R^8` со стандартным базисом `e_0,...,e_7`.

Construction seed является индексом зарегистрированной конструкции, а не статистической единицей. Детерминированный пакет не выполняет статистические тесты и не трактует повторные конструкции как независимые выборки.

# GEO-C0 — геометрия коррекции

## GEO-01: точная NCZ

Для каждого scale:

```text
c_self  = 0
c_upper = 0
```

Ожидается:

```text
A = 0
R = 0
class = NCZ
chi = null
D = null
```

Все channel norms и resultant norm должны пройти algebraic-zero threshold.

## GEO-02: двухканальная точная ECZ

```text
c_self  = scale * e_0
c_upper = -scale * e_0
```

Ожидается:

```text
A = 2 * scale
R = 0
chi = 0
D = 1
class = ECZ
```

Хотя бы один channel norm должен быть строго выше `active_floor = 100 * zero_atol`.

## GEO-03: двухканальная почти ECZ

Фиксируется `delta = 1e-3`:

```text
c_self  = scale * e_0
c_upper = -(1 - delta) * scale * e_0
```

Аналитические reference values:

\[
A=(2-\delta)s,
\qquad
R=\delta s,
\qquad
\chi=\frac{\delta}{2-\delta}.
\]

Ожидается ненулевая поправка и label `near_ecz_control`, а не exact `ECZ`.

## GEO-04: согласованные каналы

```text
c_self  = scale * e_0
c_upper = 2 * scale * e_0
```

Ожидается:

```text
R = A
chi = 1
D = 0
class = active_non_ecz
```

## GEO-05: ортогональные каналы

```text
c_self  = scale * e_0
c_upper = scale * e_1
```

Ожидается:

```text
A = 2 * scale
R = sqrt(2) * scale
chi = sqrt(2) / 2
P = 0
N = 0
D = 0
class = active_non_ecz
```

Этот контроль фиксирует, что уменьшение `R/A` само по себе не является доказательством компенсации.

## GEO-06: трёхканальная ECZ с углами 120 градусов

В первых двух координатах:

```text
c_0 = scale * (1, 0)
c_1 = scale * (-1/2,  sqrt(3)/2)
c_2 = scale * (-1/2, -sqrt(3)/2)
```

Ожидается:

```text
A = 3 * scale
R = 0
chi = 0
D = 1
all pairwise cosine = -1/2
class = ECZ
```

## GEO-07: инвариантность к техническому разбиению канала

Канонический канал:

```text
c_self = scale * e_0 + 2 * scale * e_1
```

Техническое разбиение:

```text
part_0 = 0.25 * c_self
part_1 = 0.75 * c_self
```

После группировки по canonical channel id должны совпасть:

- grouped channel tensor;
- `A`, `R`, `Q`, `P`, `N`, `D`, `chi`;
- итоговый class;
- record key canonical channel.

Технические части не считаются отдельными причинными каналами.

## GEO-08: zero-safe comparison

Сравниваются:

```text
reference = 0
candidate = 0
```

Ожидается:

```text
passed = true
cosine = null
zero_safe_path = true
```

Отдельный negative-control record сравнивает `0` и `active_floor * e_0`; он должен корректно вернуть `passed = false` без NaN. Этот ожидаемый false-result считается успешным поведением самого control case.

## GEO-C0 объём

На каждом confirmatory lane:

```text
8 case families * 3 construction seeds = 24 case records
```

GEO-C0 проходит только при выполнении всех аналитических identities, expected labels и zero-safe behaviours на обоих lanes.

# TR-C0 — перенос ошибки к состоянию

## TR-01: масштабированный identity transport

Для `R^8`:

```text
J = c * I
c in {1, 0.5, 0.1, 0.01, 0}
r = registered nonzero source direction
```

Для каждого construction seed используется фиксированное ненулевое направление с нормой `scale`.

Ожидается:

\[
J^*r=cr,
\qquad
\gamma=|c|.
\]

При `c=0` source остаётся активным, transported vector равен нулю и class равен `TNZ`.

## TR-02: точная TNZ ненулевого оператора

```text
J = diag(1, 1, 0, 0, 0, 0, 0, 0)
r = scale * e_2
```

Ожидается:

```text
source norm > active_floor
transported norm <= zero_atol
gamma = 0
class = TNZ
operator norm > 0
```

## TR-03: активный контроль того же оператора

```text
J = diag(1, 1, 0, 0, 0, 0, 0, 0)
r = scale * e_0
```

Ожидается:

```text
J* r = r
gamma = 1
class = transported_active
```

## TR-04: ортогональный нормосохраняющий перенос

Используется фиксированный signed permutation operator `O`:

```text
O e_0 = e_1
O e_1 = -e_0
O e_k = e_k for k >= 2
```

Ожидается:

```text
||O* r|| = ||r||
gamma = 1
inner-product adjoint identity passed
class = transported_active
```

Adjoint identity:

\[
\langle Jx,r\rangle=\langle x,J^*r\rangle.
\]

## TR-05: прямой накопленный перенос

Для цепочки из трёх зарегистрированных operators вычисляются:

```text
q_sequential = J_1* (J_2* (J_3* r))
q_direct     = T* r
T            = J_3 J_2 J_1
```

Проверяется `q_sequential ≈ q_direct`. Primary cumulative gain вычисляется непосредственно как `||q_direct|| / ||r||`. Произведение локальных directional gains сохраняется только как descriptive field.

## TR-06: различение TNZ и ECZ

Две конструкции используют одинаковый active source:

### TNZ construction

```text
J* r = 0
c_self != 0
u = c_self
```

Ожидается `TNZ` на transport stage и `active_non_ecz` на aggregation stage.

### ECZ construction

```text
J* r != 0
c_upper = -J* r
c_self = -c_upper
u = 0
```

Ожидается active transport и `ECZ` на aggregation stage.

Ни один из механизмов не подменяет другой.

## TR-C0 объём

На каждом confirmatory lane:

```text
TR-01: 5 scales * 3 construction seeds = 15
TR-02..TR-06: 5 families * 3 construction seeds = 15
total = 30 transport records
```

TR-C0 проходит только при выполнении всех analytic outputs, adjoint identities, mechanism labels и cumulative comparisons на обоих lanes.

# TMP-C0 — временной контроль Розенбаума

## Назначение

Контроль проверяет временное распространение FixedPred error wave при:

```text
eta = 1
network depth L = 6
feed-forward initialization
```

Используется отдельная невырожденная линейная последовательная модель, а не FashionMNIST или MNIST. Все локальные Jacobians диагональны и имеют ненулевые диагонали. Input, target и weights полностью задаются construction seed.

## Индексы

Зарегистрированы:

```text
prediction layer index: 1..L
state layer index:      0..L-1
sweep index:            1..n
output error source:    epsilon_L before sweep 1
```

Для FixedPred loop, выполняющего layers в обратном порядке, ожидается:

```text
first nonzero dv at state layer l = sweep L - l
first nonzero stored epsilon_l for l=1..L-1 = sweep L - l + 1
epsilon_L is active before sweep 1
```

`nonzero` означает norm выше `active_floor` соответствующего lane.

## Зарегистрированные числа sweeps

Выполняются три варианты:

```text
n = L - 1
n = L
n = L + 1
```

Ожидается:

- `n=L-1` является положительным insufficient-wave control и сохраняет ненулевое отличие первого parameter-gradient block от BP;
- `n=L` достигает первого слоя и проходит endpoint-gradient equivalence с BP;
- `n=L+1` остаётся эквивалентным `n=L` и BP в зарегистрированной линейной конструкции.

Separation floor для ожидаемого отличия `n=L-1`:

```text
CPU float64: first-block relative L2 > 1e-8
ROCm float32: first-block relative L2 > 1e-5
```

Если construction не создаёт это заранее зарегистрированное различие, соответствующий record завершается как failed; construction после просмотра результата не заменяется.

## Trace contract

Для каждого `(lane, construction_seed, sweep, state_layer)` сохраняются:

- epsilon-before-update norm;
- transported upper term norm;
- local error norm;
- `dv` norm;
- state version before and after update;
- Jacobian version id;
- expected first-active sweep;
- observed first-active sweep;
- finite flag;
- ordering flag.

На каждом confirmatory lane:

```text
3 construction seeds * 6 sweeps * 6 state layers = 108 temporal event records
3 temporal summary records
```

`n=L-1` и `n=L+1` endpoint comparisons входят в summary records, но базовый wave trace фиксируется для `n=L`.

## TMP-C0 pass criteria

TMP-C0 проходит, когда на обоих lanes:

- output source активен до sweep 1;
- все first-active indices совпадают с зарегистрированной формулой;
- state versions монотонны и увеличиваются ровно один раз на update event;
- Jacobian version остаётся fixed для FixedPred;
- `n=L-1` проходит expected-insufficient positive control;
- `n=L` совпадает с BP;
- `n=L+1` совпадает с `n=L` и BP;
- все 108 event records и 3 summary records присутствуют;
- отсутствуют duplicate keys и nonfinite values.

# JAC-C0 — frozen block-Jacobian probe

## Общий объект

На одном замороженном snapshot вычисляется:

\[
D\mathcal P(H)^*E=(J_{h,2}^*e_2,\ldots,J_{h,L}^*e_L).
\]

Сравниваются формы:

```text
isolated_vjp
composite_vjp
chunked_composite_vjp
```

Каждая форма использует идентичные detached leaf inputs, local outputs, cotangents, dtype, device и model state. Snapshot не обновляется между формами.

## JAC-01: малый materialized oracle

Используется синтетическая линейная цепочка из `4` blocks в `R^8`.

Для каждого block:

1. materialized Jacobian получается через зарегистрированный `torch.autograd.functional.jacobian` либо эквивалентный frozen `torch.func.jacrev` path;
2. reference вычисляется как explicit `J.T @ e`;
3. isolated, composite и chunked-composite VJP сравниваются с explicit reference.

На каждом confirmatory lane:

```text
3 construction seeds * 4 blocks * 2 candidate comparisons = 24 records
```

## JAC-02: lenet_classic matrix-free snapshot

Используется canonical `lenet_classic` с:

```text
model seeds = 0, 1, 2
batch size = 8
input shape = [8, 1, 28, 28]
synthetic deterministic input
targets = [0,1,2,3,4,5,6,7]
6 top-level blocks
```

Synthetic input строится из фиксированной `torch.linspace`-последовательности и не использует dataset loader.

Для каждого block создаются deterministic cotangents совпадающей shape. Isolated VJP является matrix-free reference. Composite и chunked-composite формы сравниваются с ним.

Chunk partition фиксируется до smoke:

```text
chunk 0 = blocks 0,1,2
chunk 1 = blocks 3,4,5
```

На каждом confirmatory lane:

```text
3 model seeds * 6 blocks * 2 candidate comparisons = 36 records
```

## Structural diagnostics

Для каждой формы сохраняются:

- block count;
- VJP call count;
- input and output shapes;
- cotangent shapes;
- graph-island count;
- allow-unused status;
- missing-gradient count;
- snapshot fingerprint;
- model-state fingerprint;
- RNG fingerprint before and after;
- source commit and image provenance.

Ожидается:

```text
isolated_vjp calls = number of blocks
composite_vjp calls = 1
chunked_composite_vjp calls = 2
missing-gradient count = 0
snapshot fingerprints identical
model-state fingerprints identical
```

Call-count result является structural fact, а не доказательством ускорения.

## JAC-C0 объём и pass criteria

На каждом confirmatory lane:

```text
24 materialized-oracle comparison records
36 lenet matrix-free comparison records
total = 60 block-probe comparison records
```

JAC-C0 проходит только при:

- совпадении всех candidate VJP с зарегистрированным reference;
- выполнении implementation-snapshot thresholds;
- совпадении snapshot и model-state fingerprints;
- отсутствии missing gradients;
- выполнении exact VJP call-count contract;
- полном составе records на обоих lanes.

JAC-C0 не сравнивает runtime, memory, saved tensors или graph lifetime и не открывает B2. Эти свойства проверяются отдельными B1/B2 gates.

# PNZ-L0 — ограниченный параметрический контроль

Используется линейный operator:

\[
\widetilde J_\theta=
\begin{bmatrix}
1&0\\
0&1\\
0&0
\end{bmatrix}.
\]

Source:

\[
r=(0,0,\mathrm{scale})^\top.
\]

Ожидается:

```text
source norm > active_floor
J_theta* r = 0
class = PNZ
operator rank = 2
```

На каждом confirmatory lane выполняются `3` PNZ records. Результат публикуется как limited extension. Он не меняет `core_passed`.

# Execution scopes

## Smoke

Smoke выполняется в controlled Docker CPU и Docker/ROCm lanes после фиксации implementation source commit.

На каждом lane:

```text
construction_seed = 0
model_seed = 0
GEO-C0 records = 8
TR-C0 records = 10
TMP-C0 event records = 36
TMP-C0 summary records = 1
JAC-C0 records = 20
PNZ-L0 records = 1
```

Smoke проверяет schemas, keys, thresholds, device placement, finite values, deterministic replay и provenance. Smoke не входит в confirmatory evidence.

## Confirmatory

На каждом lane:

```text
construction seeds = 0,1,2
model seeds = 0,1,2
GEO-C0 records = 24
TR-C0 records = 30
TMP-C0 event records = 108
TMP-C0 summary records = 3
JAC-C0 records = 60
PNZ-L0 records = 3
```

По двум lanes:

```text
GEO-C0 records = 48
TR-C0 records = 60
TMP-C0 event records = 216
TMP-C0 summary records = 6
JAC-C0 records = 120
PNZ-L0 records = 6
```

Каждая зарегистрированная construction выполняется один раз на lane. Повторный execution той же construction после просмотра результата создаёт новую evidence version и не заменяет исходный record.

# Output contract

Implementation до первого controlled smoke фиксирует файлы:

```text
mechanism_geometry_records.csv
mechanism_transport_records.csv
mechanism_temporal_events.csv
mechanism_temporal_summary.csv
mechanism_block_probe_records.csv
mechanism_pnz_records.csv
mechanism_controls_contract.json
mechanism_controls_summary.json
```

`mechanism_controls_summary.json` содержит отдельно:

```text
geo_c0_passed
tr_c0_passed
tmp_c0_passed
jac_c0_passed
core_passed
pnz_l0_passed
si_ma0_open
```

Правило:

```text
si_ma0_open = core_passed
```

# Provenance contract

Каждый output фиксирует:

- full source Git commit;
- source branch;
- controlled image identifier;
- image revision label;
- contract id;
- Torch2PC commit;
- PyTorch version;
- HIP version;
- lane;
- device name;
- dtype;
- CPU thread count;
- visible ROCm devices;
- deterministic-algorithm status;
- model and construction seeds;
- case registry digest;
- threshold registry digest.

CPU и ROCm confirmatory outputs должны ссылаться на один source commit, contract id, case registry и threshold registry.

# Pass criteria

Core gate проходит только при одновременном выполнении:

- prerequisites остаются checksum-valid;
- implementation schema зафиксирована до smoke;
- GEO-C0 проходит на CPU и ROCm;
- TR-C0 проходит на CPU и ROCm;
- TMP-C0 проходит на CPU и ROCm;
- JAC-C0 проходит на CPU и ROCm;
- все expected records присутствуют;
- record keys уникальны;
- все обязательные values finite;
- expected false-result zero-safe control ведёт себя согласно contract;
- source commit и image provenance подтверждены;
- test split остаётся закрытым;
- confirmatory outputs имеют `core_passed=true` и `si_ma0_open=true`.

`PNZ-L0` получает отдельный pass status.

# Stop rules

При failure core sub-gate:

- `core_passed=false`;
- `si_ma0_open=false`;
- все records и diagnostics сохраняются;
- threshold и construction registry сохраняются без post-hoc изменения;
- причина исследуется отдельным diagnostic commit;
- исправленная реализация получает новый source commit;
- новый confirmatory execution получает новую evidence version.

При failure только `PNZ-L0`:

- core gate сохраняет собственный вычисленный статус;
- `SI-MA0` определяется только core sub-gates;
- PNZ claims остаются закрытыми;
- limited-extension failure публикуется.

OOM, worker crash, missing record, duplicate key, provenance mismatch, nonfinite value и unexpected exception создают failed record и закрывают соответствующий sub-gate.

# Поддерживаемое утверждение

Положительный core gate поддерживает утверждение, что зарегистрированная реализация воспроизводит аналитические механизмы коррекционной геометрии и переноса, ожидаемую временную волну FixedPred и эквивалентность matrix-free block-VJP forms в controlled CPU/ROCm deterministic suite.

# Граница утверждения

Положительный результат не устанавливает:

- наблюдаемую распространённость механизмов в реальном обучении;
- механизмную реконструкцию фактического `Strict.state_inference`;
- полезность следующего exact sweep;
- достаточность признаков PC-TREF;
- ускорение composite VJP;
- возможность активного управления;
- перенос результатов на другие architectures, precisions, batch sizes или devices.

# Evidence policy

Working outputs сохраняются в игнорируемом каталоге `working/`. После успешного confirmatory core gate создаётся отдельный immutable package с:

- всеми raw records;
- CPU и ROCm summaries;
- frozen contract и registries;
- provenance manifests;
- supported claim и claim boundary;
- SHA-256;
- отдельным evidence commit;
- annotated tag `stage3b-a1-mechanism-controls-v1`.

Предыдущие sealed evidence packages не изменяются.
