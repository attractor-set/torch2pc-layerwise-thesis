# Research glossary

[Русская версия](glossary.md)

This glossary is the normative terminology source for public documentation,
protocols, reports, and dissertation text. It fixes Russian–English term
equivalence and limits each meaning to the scope of this project.

## Usage rules

1. Each `TERM-*` identifier is identical in the Russian and English versions
   and remains stable when wording is edited.
2. On first substantive use in an English document, the English term is linked
   to the corresponding entry in this glossary. The Russian equivalent is not
   duplicated in running prose because the glossary entry provides the
   language mapping.
3. Method names, fields, metrics, files, directories, branches, tags, and
   Releases remain untranslated and are formatted as code.
4. Terms are not interchangeable unless the definition explicitly says so.
5. Add a new term to both glossary versions before using it broadly elsewhere.
6. A reserved term has a fixed meaning, but its presence does not imply that
   the corresponding experiment has been executed or that an empirical claim
   is authorized.

## Canonical terms

## Methods and regimes

<a id="term-backpropagation"></a>
### TERM-BACKPROPAGATION — backpropagation (BP)

- **Russian equivalent:** обратное распространение ошибки (BP).
- **Project meaning:** The reference procedure for computing parameter gradients by a reverse pass through the computation graph.
- **Usage rule:** Use `BP` after the first definition. Do not use “backward pass” as a synonym when referring to the learning algorithm itself.

<a id="term-predictive-coding"></a>
### TERM-PREDICTIVE-CODING — predictive coding

- **Russian equivalent:** предиктивное кодирование.
- **Project meaning:** The studied family of learning procedures in which states are inferred iteratively and local errors are used to update states and parameters.
- **Usage rule:** Keep the implementation-regime names `Exact`, `FixedPred`, and `Strict` unchanged.

<a id="term-method-regime"></a>
### TERM-METHOD-REGIME — method regime

- **Russian equivalent:** режим метода.
- **Project meaning:** A concrete computational variant of a method selected by the experiment configuration.
- **Usage rule:** `Exact`, `FixedPred`, and `Strict` are Torch2PC regimes; BP is treated as a separate reference method.

<a id="term-baseline"></a>
### TERM-BASELINE — baseline

- **Russian equivalent:** базовая линия.
- **Project meaning:** A pinned implementation, configuration, or result set used as the reference for subsequent comparison.
- **Usage rule:** Preserve identifiers such as `stage2_baseline`. A baseline does not imply the best method.

<a id="term-candidate"></a>
### TERM-CANDIDATE — candidate

- **Russian equivalent:** кандидат.
- **Project meaning:** A proposed implementation or mechanism change that must pass registered checks before a full experiment.
- **Usage rule:** B1 and B2 remain candidates until they pass numerical-equivalence checks and receive a separate decision-gate approval.

## Execution and reproducibility

<a id="term-execution"></a>
### TERM-EXECUTION — execution

- **Russian equivalent:** выполнение.
- **Project meaning:** The actual running of a registered experimental protocol in a pinned compute environment.
- **Usage rule:** Use “campaign” for a collection of executions; preserve `execution` in machine fields and artifact names.

<a id="term-run"></a>
### TERM-RUN — run

- **Russian equivalent:** запуск.
- **Project meaning:** A separately identifiable execution instance with its own `run_id`, configuration, and results.
- **Usage rule:** Do not use it for a campaign, which contains multiple runs.

<a id="term-attempt"></a>
### TERM-ATTEMPT — attempt

- **Russian equivalent:** попытка.
- **Project meaning:** One scheduler or worker process invocation made to produce the result of an experiment cell.
- **Usage rule:** A successful cell may have one or more attempts; attempt count is not a substitute for the number of independent statistical units.

<a id="term-experiment-cell"></a>
### TERM-EXPERIMENT-CELL — experiment cell

- **Russian equivalent:** экспериментальная ячейка.
- **Project meaning:** One concrete combination of factors in the registered experiment matrix, including method, configuration, and random seed.
- **Usage rule:** Use “cell” for a unit of the execution matrix, not as a synonym for a statistical observation.

<a id="term-configuration"></a>
### TERM-CONFIGURATION — configuration

- **Russian equivalent:** конфигурация.
- **Project meaning:** A pinned set of experimental factors and parameters that defines run conditions.
- **Usage rule:** Preserve the original English identifiers of YAML and JSON fields.

<a id="term-validation-dataset"></a>
### TERM-VALIDATION-DATASET — validation dataset

- **Russian equivalent:** валидационная выборка.
- **Project meaning:** Data permitted for tuning, diagnostics, and decisions before final evaluation on the test dataset.
- **Usage rule:** `validation-only` denotes a claim scope restricted to validation data.

<a id="term-test-dataset-access"></a>
### TERM-TEST-DATASET-ACCESS — test-dataset access

- **Russian equivalent:** доступ к тестовой выборке.
- **Project meaning:** The act of creating, reading, or using test data during execution or analysis.
- **Usage rule:** Preserve the field `test_dataset_access`; `false` is a protocol boundary, not a method-quality property.

<a id="term-non-perturbation"></a>
### TERM-NON-PERTURBATION — measurement non-perturbation

- **Russian equivalent:** отсутствие возмущения измерением.
- **Project meaning:** The property that the measurement path does not alter the studied numerical results beyond the registered tolerance.
- **Usage rule:** It does not imply zero overhead; timing and numerical effects are checked separately.

## Evidence and publication

<a id="term-evidence"></a>
### TERM-EVIDENCE — evidence

- **Russian equivalent:** доказательные материалы.
- **Project meaning:** Published data, metadata, checks, and derived artifacts on which an empirical claim directly depends.
- **Usage rule:** The term does not mean a mathematical proof. Preserve the machine field `evidence`.

<a id="term-integrity-sealing"></a>
### TERM-INTEGRITY-SEALING — integrity sealing

- **Russian equivalent:** фиксация целостности.
- **Project meaning:** The procedure that verifies completeness and checksums and then pins an immutable evidence bundle.
- **Usage rule:** Preserve the directory name `sealed-v1` and `sealing` in artifact identifiers.

<a id="term-provenance"></a>
### TERM-PROVENANCE — artifact provenance

- **Russian equivalent:** происхождение артефактов.
- **Project meaning:** The verifiable chain from source code and execution environment to data, analysis, publication state, and release.
- **Usage rule:** Commit hashes, checksums, tags, and provenance fields remain unchanged.

<a id="term-publication-state"></a>
### TERM-PUBLICATION-STATE — publication state

- **Russian equivalent:** публикационное состояние.
- **Project meaning:** The specific repository commit at which a published artifact and documentation set is considered pinned.
- **Usage rule:** Do not conflate it with the execution source or analysis implementation, which may have different hashes.

## Statistical and engineering analysis

<a id="term-statistical-unit"></a>
### TERM-STATISTICAL-UNIT — independent statistical unit

- **Russian equivalent:** независимая статистическая единица.
- **Project meaning:** The smallest unit treated as independent for statistical aggregation or inference.
- **Usage rule:** In B0 this is an independently trained model identified by `model_seed`; repeated measurements of one model are not independent units.

<a id="term-model-seed"></a>
### TERM-MODEL-SEED — model seed

- **Russian equivalent:** случайное начальное значение модели.
- **Project meaning:** The random-number-generator value that defines an independent model initialization and training instance in the registered protocol.
- **Usage rule:** Preserve `model_seed`. The seed value identifies a unit but is not itself the abstract statistical unit.

<a id="term-descriptive-engineering-analysis"></a>
### TERM-DESCRIPTIVE-ENGINEERING-ANALYSIS — descriptive engineering analysis

- **Russian equivalent:** описательный инженерный анализ.
- **Project meaning:** A summary of observed timing, resource, and structural metrics without a population-level claim beyond the registered matrix.
- **Usage rule:** B0 uses the scope `descriptive_engineering_analysis_n3`; do not restate it as a statistical-significance claim.

<a id="term-bounded-finding"></a>
### TERM-BOUNDED-FINDING — bounded finding

- **Russian equivalent:** вывод в зарегистрированной области.
- **Project meaning:** An empirical finding valid only for the explicitly stated implementation, environment, data, configurations, and protocol.
- **Usage rule:** Do not extend it to a universal method ranking or a general proof of an algorithmic property.

<a id="term-numerical-equivalence-check"></a>
### TERM-NUMERICAL-EQUIVALENCE-CHECK — numerical-equivalence check

- **Russian equivalent:** проверка численной эквивалентности.
- **Project meaning:** A predefined procedure comparing candidate and reference outputs, states, or gradients under registered numerical criteria.
- **Usage rule:** Passing the check means satisfying thresholds in the studied scope, not algorithmic identity.

<a id="term-decision-gate"></a>
### TERM-DECISION-GATE — decision gate

- **Russian equivalent:** решение о допуске.
- **Project meaning:** An explicit documented decision to enter the next experimental phase based on defined criteria and available artifacts.
- **Usage rule:** It is not a statistical hypothesis and does not replace a numerical-equivalence check.

<a id="term-finite-value-check"></a>
### TERM-FINITE-VALUE-CHECK — finite-value check

- **Russian equivalent:** проверка конечности значений.
- **Project meaning:** A check that registered numerical outputs contain no `NaN`, positive infinity, or negative infinity.
- **Usage rule:** Finiteness is a necessary admission condition but does not by itself establish equivalence.

<a id="term-cosine-similarity"></a>
### TERM-COSINE-SIMILARITY — cosine similarity

- **Russian equivalent:** косинусное сходство.
- **Project meaning:** A normalized measure of directional agreement between two vectors.
- **Usage rule:** Machine fields may use `cosine`; directional agreement is evaluated separately from scale difference.

<a id="term-relative-l2-error"></a>
### TERM-RELATIVE-L2-ERROR — relative L2 error

- **Russian equivalent:** относительная ошибка L2.
- **Project meaning:** The L2 norm of the candidate-reference difference divided by the registered normalization quantity.
- **Usage rule:** The exact normalization formula and zero-denominator handling are defined in the candidate protocol.

## Profiling and compute metrics

<a id="term-profiling"></a>
### TERM-PROFILING — profiling

- **Russian equivalent:** профилирование.
- **Project meaning:** Instrumented measurement of time, memory, and computational-region contributions under a registered protocol.
- **Usage rule:** Do not use it as a synonym for training or general experiment execution.

<a id="term-matched-profiling"></a>
### TERM-MATCHED-PROFILING — matched profiling

- **Russian equivalent:** сопоставленное профилирование.
- **Project meaning:** Comparative profiling with matched data, configurations, seeds, warm-up, repetitions, and measured steps.
- **Usage rule:** The full matrix requires a separate decision gate after candidate-specific checks.

<a id="term-device-time"></a>
### TERM-DEVICE-TIME — device time

- **Russian equivalent:** время на устройстве.
- **Project meaning:** Execution time of operations on the compute device measured with a device-synchronized timer.
- **Usage rule:** Do not conflate it with process wall time, data loading, or orchestration.

<a id="term-peak-allocated-memory"></a>
### TERM-PEAK-ALLOCATED-MEMORY — peak allocated memory

- **Russian equivalent:** пиковая выделенная память.
- **Project meaning:** The maximum device memory simultaneously reported as allocated by the allocator within the measured scope.
- **Usage rule:** Do not conflate it with reserved memory, total process memory, or system-wide memory.

<a id="term-measured-region"></a>
### TERM-MEASURED-REGION — measured region

- **Russian equivalent:** область измерения.
- **Project meaning:** A named segment of the computational path for which timing or resource metrics are collected separately.
- **Usage rule:** Preserve region identifiers such as `state_inference`.

<a id="term-state-inference"></a>
### TERM-STATE-INFERENCE — state inference

- **Russian equivalent:** вывод состояний.
- **Project meaning:** The iterative computation or refinement of predictive-coding internal states before parameter updates.
- **Usage rule:** The profiling-region identifier is `state_inference`. It does not mean statistical inference.

<a id="term-saved-tensors"></a>
### TERM-SAVED-TENSORS — saved tensors

- **Russian equivalent:** сохранённые тензоры.
- **Project meaning:** Tensors retained by automatic differentiation for a subsequent backward computation.
- **Usage rule:** Do not conflate them with all live tensors or total allocated memory.

<a id="term-scaling"></a>
### TERM-SCALING — scaling

- **Russian equivalent:** масштабирование.
- **Project meaning:** The change in a measured quantity under a systematic change in model size, depth, batch size, or another registered factor.
- **Usage rule:** Descriptive `log2` coefficients are not interpreted as a universal scaling law.

<a id="term-vjp"></a>
### TERM-VJP — vector–Jacobian product (VJP)

- **Russian equivalent:** произведение вектора на якобиан (VJP).
- **Project meaning:** A vector multiplied by a Jacobian without explicitly materializing the full Jacobian.
- **Usage rule:** Use `VJP` after the first definition; preserve `local_state_vjp` and `parameter_vjp` region identifiers.

<a id="term-structural-locality"></a>
### TERM-STRUCTURAL-LOCALITY — structural locality

- **Russian equivalent:** структурная локальность.
- **Project meaning:** A bounded dependency structure across layers, states, time, or graph structure, supported by dedicated measurements.
- **Usage rule:** Low time or memory alone does not establish structural locality.

## Experimental process and shared concepts

<a id="term-dataset"></a>
### TERM-DATASET — dataset

- **Russian equivalent:** набор данных.
- **Project meaning:** A fixed collection of examples and labels used for training, validation, or test evaluation.
- **Usage rule:** Distinguish dataset, validation dataset, and test dataset by role; preserve names such as FashionMNIST, MNIST, and configuration fields.

<a id="term-architecture"></a>
### TERM-ARCHITECTURE — architecture

- **Russian equivalent:** архитектура.
- **Project meaning:** The model structure that defines layers, connections, and the computational path.
- **Usage rule:** Preserve architecture identifiers such as `lenet_classic`.

<a id="term-pilot-study"></a>
### TERM-PILOT-STUDY — pilot study

- **Russian equivalent:** пилотное исследование.
- **Project meaning:** A bounded preliminary campaign used to verify feasibility, select only preregistered options, and prepare a later freeze.
- **Usage rule:** A pilot study is not the final evaluation and does not access the test dataset unless the protocol explicitly says otherwise.

<a id="term-final-execution"></a>
### TERM-FINAL-EXECUTION — final execution

- **Russian equivalent:** итоговое выполнение.
- **Project meaning:** Execution of the frozen confirmatory protocol after the pilot study and an explicit decision gate.
- **Usage rule:** The term names an execution phase and does not imply universal finality of the research program.

<a id="term-confirmatory-analysis"></a>
### TERM-CONFIRMATORY-ANALYSIS — confirmatory analysis

- **Russian equivalent:** подтверждающий анализ.
- **Project meaning:** Analysis of questions, contrasts, units, and inference rules defined in advance.
- **Usage rule:** Changes made after test-data inspection are not retrospectively included in confirmatory analysis.

<a id="term-exploratory-analysis"></a>
### TERM-EXPLORATORY-ANALYSIS — exploratory analysis

- **Russian equivalent:** разведочный анализ.
- **Project meaning:** Analysis formulated after research begins or after data inspection and used to generate new hypotheses.
- **Usage rule:** Mark exploratory results separately and do not use them to replace confirmatory findings.

<a id="term-checkpoint"></a>
### TERM-CHECKPOINT — checkpoint

- **Russian equivalent:** контрольная точка.
- **Project meaning:** A saved state of the model, optimizer, and related metadata at a defined training point.
- **Usage rule:** Preserve filenames such as `checkpoint.pt`; a checkpoint is not an independent statistical unit by itself.

<a id="term-runtime"></a>
### TERM-RUNTIME — runtime

- **Russian equivalent:** время выполнения.
- **Project meaning:** The duration of a specified computational path within an explicitly stated measured scope.
- **Usage rule:** Qualify runtime as device time, wall-clock time, or measured-region time; do not conflate these metrics.

<a id="term-wall-time"></a>
### TERM-WALL-TIME — wall-clock time

- **Russian equivalent:** астрономическое время.
- **Project meaning:** Real elapsed time between the start and end of a measured action according to the host clock.
- **Usage rule:** State included operations, synchronization, and timer boundaries explicitly.

<a id="term-throughput"></a>
### TERM-THROUGHPUT — throughput

- **Russian equivalent:** пропускная способность.
- **Project meaning:** The number of examples, steps, or other work units processed per unit time.
- **Usage rule:** Always state the work unit and measured scope; throughput is not a synonym for single-operation latency.

<a id="term-warm-up"></a>
### TERM-WARM-UP — warm-up

- **Russian equivalent:** разогрев.
- **Project meaning:** Preliminary steps excluded from the main estimate and used to stabilize compilation, memory allocation, and device state.
- **Usage rule:** The number of warm-up steps is protocol-defined and is not mixed with measured repetitions.

<a id="term-fallback"></a>
### TERM-FALLBACK — fallback

- **Russian equivalent:** резервный переход.
- **Project meaning:** A predefined transition from a candidate to a reference or more stable computational path when a guard condition fails.
- **Usage rule:** Record fallback events and include them in cost accounting; do not remove them as inconvenient observations.

<a id="term-non-inferiority"></a>
### TERM-NON-INFERIORITY — non-inferiority

- **Russian equivalent:** не меньшая эффективность.
- **Project meaning:** Satisfaction of a predefined margin showing that a candidate is not worse than a reference by more than an allowed amount on a selected metric.
- **Usage rule:** Freeze the margin, metric direction, and statistical procedure before final evaluation; non-inferiority is not equivalence or superiority.

<a id="term-state-trajectory"></a>
### TERM-STATE-TRAJECTORY — state trajectory

- **Russian equivalent:** траектория состояний.
- **Project meaning:** The ordered sequence of internal states produced by iterative inference or correction steps.
- **Usage rule:** Endpoint equivalence and full-trajectory equivalence are distinct claims.

<a id="term-endpoint"></a>
### TERM-ENDPOINT — endpoint

- **Russian equivalent:** конечное состояние.
- **Project meaning:** The state, gradients, or parameters after a registered computational path completes.
- **Usage rule:** Endpoint agreement does not imply agreement of the intermediate trajectory.

<a id="term-prediction-error"></a>
### TERM-PREDICTION-ERROR — prediction error

- **Russian equivalent:** ошибка предсказания.
- **Project meaning:** The difference between a predicted and current state or signal at a specified layer of a predictive-coding regime.
- **Usage rule:** The implementation and protocol define the exact formula; do not use the term as a synonym for the overall loss.

<a id="term-computational-graph"></a>
### TERM-COMPUTATIONAL-GRAPH — computational graph

- **Russian equivalent:** вычислительный граф.
- **Project meaning:** The graph of operations and dependencies used for forward computation and automatic differentiation.
- **Usage rule:** Locality analysis reports graph modules, span, and lifetime separately.

<a id="term-automatic-differentiation"></a>
### TERM-AUTOMATIC-DIFFERENTIATION — automatic differentiation

- **Russian equivalent:** автоматическое дифференцирование.
- **Project meaning:** Programmatic derivative construction from the sequence of elementary operations in a computational graph.
- **Usage rule:** Preserve the PyTorch subsystem name `autograd` as a software identifier.

<a id="term-hyperparameter"></a>
### TERM-HYPERPARAMETER — hyperparameter

- **Russian equivalent:** гиперпараметр.
- **Project meaning:** An algorithm or protocol parameter set before training and not estimated as a model parameter from the training data.
- **Usage rule:** State the selection rule and freeze point explicitly.

## Reserved terms for the next research line

The following definitions establish terminology for operator diagnostics,
local-predictor design, and the primary post-B0 working scenario. They do not
change current B0 findings or authorize candidate execution without separate
checks and decision gates.

<a id="term-mechanism-attribution"></a>
### TERM-MECHANISM-ATTRIBUTION — mechanism attribution

- **Russian equivalent:** отнесение эффекта к механизму.
- **Project meaning:** The systematic linking of an observed timing, resource, or numerical effect to a specific computational mechanism using decomposition and dedicated checks.
- **Usage rule:** Without an intervention or exclusion test, report it as engineering attribution rather than established causality.

<a id="term-region-decomposition"></a>
### TERM-REGION-DECOMPOSITION — measured-region decomposition

- **Russian equivalent:** декомпозиция области измерения.
- **Project meaning:** The partition of a named computational region into explicitly defined components for separate accounting of time, memory, saved tensors, or dependencies.
- **Usage rule:** Components require registered boundaries; overlap and uncovered residuals must be reported explicitly.

<a id="term-passive-diagnostics"></a>
### TERM-PASSIVE-DIAGNOSTICS — passive diagnostics

- **Russian equivalent:** пассивная диагностика.
- **Project meaning:** Collection of predictions, features, and diagnostic metrics without changing the primary computational path or update decision.
- **Usage rule:** Shadow mode is one form of passive diagnostics; absence of control-path influence is verified separately.

<a id="term-local-predictor"></a>
### TERM-LOCAL-PREDICTOR — local predictor

- **Russian equivalent:** локальный предиктор.
- **Project meaning:** A candidate mechanism that estimates the next state or correction from a predefined bounded local context.
- **Usage rule:** The term describes the predictor’s available information and does not establish structural locality of the full system.

<a id="term-shadow-mode"></a>
### TERM-SHADOW-MODE — shadow mode

- **Russian equivalent:** теневой режим.
- **Project meaning:** A mode in which a candidate computes predictions and diagnostics but does not affect the primary computational path, updates, or published result.
- **Usage rule:** Use it for passive evaluation before the candidate is allowed to control computation.

<a id="term-pc-tref"></a>
### TERM-PC-TREF — Predictive-Coding Task-Relative Equivalence Framework (PC-TREF)

- **Russian equivalent:** рамка относительной к задаче эквивалентности predictive coding (PC-TREF).
- **Project meaning:** The upper-level framework linking a diagnostic state representation to the required computational action and evaluating whether the retained distinctions are sufficient for adaptive inference.
- **Usage rule:** PC-TREF specializes established equivalence, sufficiency, and quotient-space concepts; it is not presented as a universal theory beyond the registered predictive-coding scope.

<a id="term-pc-catm"></a>
### TERM-PC-CATM — Predictive-Coding Correction Aggregation and Transport Model (PC-CATM)

- **Russian equivalent:** операторная модель агрегации коррекций и переноса ошибок в predictive coding (PC-CATM).
- **Project meaning:** The mechanism operator model of canonical channels, their aggregation, state-error transport, and the NCZ, ECZ, and TNZ null regimes.
- **Usage rule:** PC-CATM is the mechanism layer of PC-TREF; PNZ is included only as a limited parameter-accessibility extension.

<a id="term-task-relative-equivalence"></a>
### TERM-TASK-RELATIVE-EQUIVALENCE — task-relative equivalence

- **Russian equivalent:** относительная к задаче эквивалентность.
- **Project meaning:** A registered identification of states relative to a computational decision: every decision class must satisfy the specified regret tolerance for all states in the class.
- **Usage rule:** A quotient claim requires an explicit partition map. Threshold proximity of continuous features is not itself called an equivalence relation because transitivity is not assumed.

<a id="term-operational-diagnostic-indistinguishability"></a>
### TERM-OPERATIONAL-DIAGNOSTIC-INDISTINGUISHABILITY — operational diagnostic indistinguishability

- **Russian equivalent:** операциональная диагностическая неразличимость.
- **Project meaning:** The threshold relation $d_I(\phi_I(x),\phi_I(y))\leq\varepsilon_I$ for a registered diagnostic space, metric, normalization, and tolerance.
- **Usage rule:** Use it as a proximity criterion; it is not assumed transitive and does not induce a quotient without a separate partition map.

<a id="term-decision-regret"></a>
### TERM-DECISION-REGRET — decision regret

- **Russian equivalent:** regret решения.
- **Project meaning:** The additional registered loss of a selected action relative to the best available action in the same state and action space.
- **Usage rule:** Freeze the loss function, improvement direction, aggregation unit, and admissible tolerance $\delta_R$ before confirmatory analysis.

<a id="term-required-equivalence"></a>
### TERM-REQUIRED-EQUIVALENCE — required equivalence

- **Russian equivalent:** требуемая эквивалентность.
- **Project meaning:** A partition-based relation merging states with the same registered decision class after that class satisfies the specified regret tolerance.
- **Usage rule:** Common admissibility of one action at regret no greater than $\delta_R$ may be a safety relation, but is not called equivalence without transitivity or an explicit partition map.

<a id="term-diagnostic-quotient"></a>
### TERM-DIAGNOSTIC-QUOTIENT — diagnostic quotient

- **Russian equivalent:** диагностическое фактор-пространство.
- **Project meaning:** The space of equivalence classes induced by the selected diagnostic representation of an inference state.
- **Usage rule:** Minimality is claimed only within the preregistered representation family and only after diagnostic cost and the safety gate are considered.

<a id="term-task-relative-equivalence-defect"></a>
### TERM-TASK-RELATIVE-EQUIVALENCE-DEFECT — task-relative equivalence defect

- **Russian equivalent:** дефект относительной к задаче эквивалентности.
- **Project meaning:** State pairs merged by registered diagnostic equivalence but assigned to different required-equivalence classes; formally $\mathfrak D_{I\to R}^{q}=E_I^q\setminus E_R^q$.
- **Usage rule:** A separate common-admissibility safety defect may be estimated through regret, dangerous misses, and unnecessary wake-ups, but it is not called a quotient defect without two explicit partition maps.

<a id="term-operational-sufficiency-boundary"></a>
### TERM-OPERATIONAL-SUFFICIENCY-BOUNDARY — operational sufficiency boundary

- **Russian equivalent:** операционная граница достаточности.
- **Project meaning:** The operational threshold level set of registered states where one-step exact-reference regret or defect of a computational action equals the admissible limit; in the primary line, the safety threshold for skipping the next exact sweep.
- **Usage rule:** This is an operational threshold level set, not automatically a topological boundary; it depends on the task, action space, regret limit, and exact reference, while smoothness, a unique normal, and transferability are not assumed.

<a id="term-oracle-sufficiency-margin"></a>
### TERM-ORACLE-SUFFICIENCY-MARGIN — oracle sufficiency margin

- **Russian equivalent:** oracle-запас достаточности.
- **Project meaning:** The post-action quantity $M^*=\varepsilon_R-r_{\mathrm{skip}}^*$ computed through exact reference and representing the sign and reserve relative to the one-step operational boundary.
- **Usage rule:** Oracle means post-action truth relative to the registered exact reference, not established global optimality; the margin is online-inaccessible before the exact action and remains distinct from its diagnostic estimate.

<a id="term-sufficiency-boundary-estimator"></a>
### TERM-SUFFICIENCY-BOUNDARY-ESTIMATOR — sufficiency-boundary estimator

- **Russian equivalent:** оцениватель границы достаточности.
- **Project meaning:** The pre-action mapping $\widehat M_b=g_b(\phi_b(x))$ that estimates the oracle margin from a budgeted diagnostic representation.
- **Usage rule:** The estimator undergoes separate calibration, uncertainty evaluation, and exact verification; a positive point estimate alone does not authorize an action.

<a id="term-predicted-sufficiency-horizon"></a>
### TERM-PREDICTED-SUFFICIENCY-HORIZON — predicted sufficiency horizon

- **Russian equivalent:** прогнозируемый горизонт достаточности.
- **Project meaning:** A local first-order estimate of time or registered diagnostic steps until estimated margin exhaustion under persistence of the current rate.
- **Usage rule:** The horizon is not a guaranteed count of safe skips and does not replace uncertainty, fallback, or trajectory-level verification.

<a id="term-canonical-correction-channel"></a>
### TERM-CANONICAL-CORRECTION-CHANNEL — canonical correction channel

- **Russian equivalent:** канонический канал коррекции.
- **Project meaning:** A preregistered causally meaningful group of local gradient contributions whose sum is invariant to technical subdivision of one energy term.
- **Usage rule:** Null-regime diagnostics operate on canonical channels rather than arbitrary automatic-differentiation fragments.

<a id="term-correction-geometry"></a>
### TERM-CORRECTION-GEOMETRY — correction geometry

- **Russian equivalent:** геометрия коррекции.
- **Project meaning:** The norms, resultant efficiency, and pairwise interactions of canonical channels that describe their aggregation into a local state correction.
- **Usage rule:** Correction geometry describes observed channel aggregation and does not by itself establish the utility of another exact sweep.

<a id="term-correction-zero-set"></a>
### TERM-CORRECTION-ZERO-SET — correction-zero set

- **Russian equivalent:** множество коррекционного нуля.
- **Project meaning:** The kernel of the linear canonical-channel summation operator: all contribution tuples whose resultant correction is zero.
- **Usage rule:** The exact set is partitioned into the trivial NCZ part and nontrivial ECZ part; numerical neighborhoods require separate thresholds.

<a id="term-ncz"></a>
### TERM-NCZ — Null-Contribution Zone (NCZ)

- **Russian equivalent:** зона нулевого вклада (NCZ).
- **Project meaning:** The trivial part of the correction-zero set in which all canonical channels are zero; operationally, a registered neighborhood of low channel activity.
- **Usage rule:** NCZ does not imply input familiarity, completed learning, or permission to skip computation.

<a id="term-ecz"></a>
### TERM-ECZ — Error-Cancellation Zone (ECZ)

- **Russian equivalent:** зона компенсации ошибок (ECZ).
- **Project meaning:** The nontrivial part of the correction-zero set in which at least one canonical channel is nonzero while their sum is zero; operationally, an active neighborhood with low resultant efficiency and high destructive interaction.
- **Usage rule:** ECZ has only this meaning. The erroneous former definition is removed completely and is not retained under another abbreviation.

<a id="term-resultant-efficiency"></a>
### TERM-RESULTANT-EFFICIENCY — resultant efficiency

- **Russian equivalent:** результирующая эффективность.
- **Project meaning:** The norm of the summed canonical channels divided by the sum of their norms when activity is nonzero: the fraction of activity retained in the resultant direction.
- **Usage rule:** Its complement is an aggregation deficit, not a cancellation fraction, because orthogonal channels can also reduce the ratio.

<a id="term-destructive-interaction"></a>
### TERM-DESTRUCTIVE-INTERACTION — destructive interaction

- **Russian equivalent:** разрушительное взаимодействие.
- **Project meaning:** The negative part of pairwise canonical-channel inner products normalized by individual and constructive quadratic activity.
- **Usage rule:** Combine it with activity and resultant efficiency to distinguish cancellation, orthogonality, and coherent motion.

<a id="term-state-transport"></a>
### TERM-STATE-TRANSPORT — state-error transport

- **Russian equivalent:** перенос ошибки к состоянию.
- **Project meaning:** Application of the next layer's adjoint Jacobian to a registered error source to obtain the current state's upper correction channel.
- **Usage rule:** Local and cumulative transport are recorded separately and tied to explicit state and Jacobian versions.

<a id="term-tnz"></a>
### TERM-TNZ — Transport-Null Zone (TNZ)

- **Russian equivalent:** зона нулевого переноса (TNZ).
- **Project meaning:** A nonzero source error in the kernel of the adjoint state-transport operator, producing a zero upper channel.
- **Usage rule:** TNZ differs from ECZ: TNZ concerns transport of one source, while ECZ concerns aggregation of channels already obtained.

<a id="term-directional-transport-gain"></a>
### TERM-DIRECTIONAL-TRANSPORT-GAIN — directional transport gain

- **Russian equivalent:** направленный коэффициент переноса.
- **Project meaning:** The norm ratio between a transported signal and its particular input error direction for one registered operator.
- **Usage rule:** It characterizes only the observed direction and is not a full-Jacobian spectral estimate or proof of dynamical isometry.

<a id="term-block-jacobian-probe"></a>
### TERM-BLOCK-JACOBIAN-PROBE — block-Jacobian probe

- **Russian equivalent:** блочная проба Якобиана.
- **Project meaning:** A matrix-free computation of multiple local vector–Jacobian or Jacobian–vector products on one frozen state snapshot without materializing the full Jacobian.
- **Usage rule:** One logical automatic-differentiation call does not imply one GPU kernel, lower asymptotic work, lower memory, or guaranteed acceleration.

<a id="term-exact-verification"></a>
### TERM-EXACT-VERIFICATION — counterfactual exact verification

- **Russian equivalent:** точная контрфактическая проверка.
- **Project meaning:** A comparison between a proposed control decision and a separate exact branch started from identical state to measure the actual utility of a skipped or executed exact sweep.
- **Usage rule:** Run this verification before a controller is allowed to alter the primary computational path.

<a id="term-endpoint-gradient-utility"></a>
### TERM-ENDPOINT-GRADIENT-UTILITY — endpoint-gradient utility

- **Russian equivalent:** полезность для конечного градиента.
- **Project meaning:** Improvement in the distance between the current parameter gradient and a frozen exact reference after one additional exact state-inference sweep.
- **Usage rule:** This is the primary next-sweep utility measure in Scenario A; energy reduction and runtime remain separate outcomes.

<a id="term-dangerous-miss"></a>
### TERM-DANGEROUS-MISS — dangerous miss

- **Russian equivalent:** опасный пропуск.
- **Project meaning:** A case where the controller proposes skipping an exact sweep while the counterfactual exact branch shows a preregistered material endpoint-gradient improvement.
- **Usage rule:** Dangerous-miss rate is a mandatory active-control gate and is not replaced by average predictor accuracy.

<a id="term-qwake-pc"></a>
### TERM-QWAKE-PC — QWake-PC

- **Russian equivalent:** QWake-PC.
- **Name semantics:** `Q` is intentionally left unexpanded rather than treated as a conventional acronym. It is a bounded multidimensional semantic marker spanning `Qualified`, `Quotient`, `Quality`, `Quiet`, and `Quick`; no dimension is the single canonical expansion.
- **Project meaning:** A research controller architecture and family that operationalizes PC-TREF representations, PC-CATM mechanism features, temporal persistence, predictor uncertainty, and counterfactual exact verification to allocate predictive-coding computation.
- **Architectural role:** PC-TREF is the theoretical decision-sufficiency framework, PC-CATM is the mechanism model of correction formation and cancellation, and QWake-PC is their control-layer embodiment. `QW-PC0` and `QW-AB0` denote separate versioned concrete-controller designs and are not synonyms for QWake-PC.
- **Usage rule:** `Qualified` governs action admissibility, `Quotient` links the controller to task-relative PC-TREF representation, `Quality` constrains result quality and decision regret, `Quiet` denotes diagnostic context without automatic permission to stop, and `Quick` is only a separately demonstrated engineering outcome. QWake-PC does not denote one fixed algorithm. A controller is evaluated in shadow mode first; active control requires registered safety and complete-cost gates.

<a id="term-precision-masked-zero"></a>
### TERM-PRECISION-MASKED-ZERO — precision-masked zero

- **Russian equivalent:** ноль, маскированный точностью.
- **Project meaning:** A registered numerical neighborhood $Z_{\tau}^{\mathcal N}=\{z:\|z\|_{\mathcal N}\leq\tau_{\mathcal N}\}$ with explicit space, norm, scale, dtype, device, and aggregation rule.
- **Usage rule:** Do not conflate it with mathematical zero, diagnostic indistinguishability, or permission to take a zero-like action.

<a id="term-cost-vector"></a>
### TERM-COST-VECTOR — cost vector

- **Russian equivalent:** вектор стоимости.
- **Project meaning:** Separate compute, latency, memory, diagnostic-mechanism, observer, control-plane, and fallback components associated with one action and diagnostic representation.
- **Usage rule:** Do not combine components implicitly; freeze scalarization, units, and weights before analysis or use a registered Pareto rule.

<a id="term-pareto-admissibility"></a>
### TERM-PARETO-ADMISSIBILITY — Pareto admissibility

- **Russian equivalent:** Pareto-допустимость.
- **Project meaning:** An action is not dominated by another action on every registered quality and cost component with strict improvement on at least one component.
- **Usage rule:** Pareto admissibility does not select one winner; a separate primary decision rule is preregistered.

<a id="term-diagnostic-mechanism-cost"></a>
### TERM-DIAGNOSTIC-MECHANISM-COST — diagnostic-mechanism cost

- **Russian equivalent:** стоимость диагностического механизма.
- **Project meaning:** The computational cost of operations required to form diagnostic features in the candidate's executed path.
- **Usage rule:** Separate it from measurement instrumentation and the future control plane.

<a id="term-observer-cost"></a>
### TERM-OBSERVER-COST — observer cost

- **Russian equivalent:** стоимость наблюдателя.
- **Project meaning:** Overhead from instrumentation, timers, hooks, counters, and measurement-evidence production.
- **Usage rule:** `SI-MA1` calibrates this boundary; a negative calibrated residual is over-closure, not negative physical cost.

<a id="term-control-plane-cost"></a>
### TERM-CONTROL-PLANE-COST — control-plane cost

- **Russian equivalent:** стоимость управляющего контура.
- **Project meaning:** Cost of additional feature acquisition, `ECZ` evaluation, action selection, coordination, and fallback validation in a future controller.
- **Usage rule:** It is excluded from `SI-MA1` and must be measured separately before end-to-end B1/B2 or `QWake-PC` claims.

<a id="term-primary-working-scenario"></a>
### TERM-PRIMARY-WORKING-SCENARIO — primary working scenario

- **Russian equivalent:** основной рабочий сценарий.
- **Project meaning:** A frozen sequence of mandatory and optional stages used to plan future work without claiming that those experiments have already been executed.
- **Usage rule:** Scenario A is the primary post-B0 working scenario; changing its mandatory boundary requires a new ADR decision.

<a id="term-exact-implementation-freeze"></a>
### TERM-EXACT-IMPLEMENTATION-FREEZE — exact-implementation freeze

- **Russian equivalent:** фиксация точной реализации.
- **Project meaning:** Selection and immutable freezing of the exact computational path after B1/B2 gates and before predictor-label generation and counterfactual evidence collection.
- **Usage rule:** The stage identifier is `EX-IF0`; avoid `kernel` here to separate execution implementation from mathematical kernel operators.

<a id="term-pnz"></a>
### TERM-PNZ — Plasticity-Null Zone (PNZ)

- **Russian equivalent:** зона нулевой пластичности (PNZ).
- **Project meaning:** A nonzero local error in the kernel of the adjoint parameter Jacobian and therefore inaccessible to first-order parameter change of that layer.
- **Usage rule:** In Scenario A, PNZ is a limited theoretical extension with a deterministic control; it does not imply global unlearnability or authorize skipped learning.

## Glossary change procedure

Changing the meaning of a canonical term requires updating both language
versions, checking every repository-wide use, and explicitly documenting the
migration from the previous wording. Change a `TERM-*` identifier only when
concepts are split or merged, and record the change in the changelog.
