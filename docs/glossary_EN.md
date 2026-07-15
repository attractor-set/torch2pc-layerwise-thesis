# Research glossary

[Русская версия](glossary.md)

This glossary is the normative terminology source for public documentation,
protocols, reports, and dissertation text. It fixes Russian–English term
equivalence and limits each meaning to the scope of this project.

## Usage rules

1. Each `TERM-*` identifier is identical in the Russian and English versions
   and remains stable when wording is edited.
2. Russian prose uses the Russian term first; the English equivalent is added
   on first use when needed to connect the text to literature, code, or an
   artifact name.
3. Method names, fields, metrics, files, directories, branches, tags, and
   Releases remain untranslated and are formatted as code.
4. Terms are not interchangeable unless the definition explicitly says so.
5. Add a new term to both glossary versions before using it broadly elsewhere.
6. A reserved term has a fixed meaning, but its presence does not imply that
   the corresponding experiment has been executed or that an empirical claim
   is authorized.

## Canonical terms

## Methods and regimes

### TERM-BACKPROPAGATION — backpropagation (BP)

- **Russian equivalent:** обратное распространение ошибки (BP).
- **Project meaning:** The reference procedure for computing parameter gradients by a reverse pass through the computation graph.
- **Usage rule:** Use `BP` after the first definition. Do not use “backward pass” as a synonym when referring to the learning algorithm itself.

### TERM-PREDICTIVE-CODING — predictive coding

- **Russian equivalent:** предиктивное кодирование.
- **Project meaning:** The studied family of learning procedures in which states are inferred iteratively and local errors are used to update states and parameters.
- **Usage rule:** Keep the implementation-regime names `Exact`, `FixedPred`, and `Strict` unchanged.

### TERM-METHOD-REGIME — method regime

- **Russian equivalent:** режим метода.
- **Project meaning:** A concrete computational variant of a method selected by the experiment configuration.
- **Usage rule:** `Exact`, `FixedPred`, and `Strict` are Torch2PC regimes; BP is treated as a separate reference method.

### TERM-BASELINE — baseline

- **Russian equivalent:** базовая линия.
- **Project meaning:** A pinned implementation, configuration, or result set used as the reference for subsequent comparison.
- **Usage rule:** Preserve identifiers such as `stage2_baseline`. A baseline does not imply the best method.

### TERM-CANDIDATE — candidate

- **Russian equivalent:** кандидат.
- **Project meaning:** A proposed implementation or mechanism change that must pass registered checks before a full experiment.
- **Usage rule:** B1 and B2 remain candidates until they pass numerical-equivalence checks and receive a separate decision-gate approval.

## Execution and reproducibility

### TERM-EXECUTION — execution

- **Russian equivalent:** выполнение.
- **Project meaning:** The actual running of a registered experimental protocol in a pinned compute environment.
- **Usage rule:** Use “campaign” for a collection of executions; preserve `execution` in machine fields and artifact names.

### TERM-RUN — run

- **Russian equivalent:** запуск.
- **Project meaning:** A separately identifiable execution instance with its own `run_id`, configuration, and results.
- **Usage rule:** Do not use it for a campaign, which contains multiple runs.

### TERM-ATTEMPT — attempt

- **Russian equivalent:** попытка.
- **Project meaning:** One scheduler or worker process invocation made to produce the result of an experiment cell.
- **Usage rule:** A successful cell may have one or more attempts; attempt count is not a substitute for the number of independent statistical units.

### TERM-EXPERIMENT-CELL — experiment cell

- **Russian equivalent:** экспериментальная ячейка.
- **Project meaning:** One concrete combination of factors in the registered experiment matrix, including method, configuration, and random seed.
- **Usage rule:** Use “cell” for a unit of the execution matrix, not as a synonym for a statistical observation.

### TERM-CONFIGURATION — configuration

- **Russian equivalent:** конфигурация.
- **Project meaning:** A pinned set of experimental factors and parameters that defines run conditions.
- **Usage rule:** Preserve the original English identifiers of YAML and JSON fields.

### TERM-VALIDATION-DATASET — validation dataset

- **Russian equivalent:** валидационная выборка.
- **Project meaning:** Data permitted for tuning, diagnostics, and decisions before final evaluation on the test dataset.
- **Usage rule:** `validation-only` denotes a claim scope restricted to validation data.

### TERM-TEST-DATASET-ACCESS — test-dataset access

- **Russian equivalent:** доступ к тестовой выборке.
- **Project meaning:** The act of creating, reading, or using test data during execution or analysis.
- **Usage rule:** Preserve the field `test_dataset_access`; `false` is a protocol boundary, not a method-quality property.

### TERM-NON-PERTURBATION — measurement non-perturbation

- **Russian equivalent:** отсутствие возмущения измерением.
- **Project meaning:** The property that the measurement path does not alter the studied numerical results beyond the registered tolerance.
- **Usage rule:** It does not imply zero overhead; timing and numerical effects are checked separately.

## Evidence and publication

### TERM-EVIDENCE — evidence

- **Russian equivalent:** доказательные материалы.
- **Project meaning:** Published data, metadata, checks, and derived artifacts on which an empirical claim directly depends.
- **Usage rule:** The term does not mean a mathematical proof. Preserve the machine field `evidence`.

### TERM-INTEGRITY-SEALING — integrity sealing

- **Russian equivalent:** фиксация целостности.
- **Project meaning:** The procedure that verifies completeness and checksums and then pins an immutable evidence bundle.
- **Usage rule:** Preserve the directory name `sealed-v1` and `sealing` in artifact identifiers.

### TERM-PROVENANCE — artifact provenance

- **Russian equivalent:** происхождение артефактов.
- **Project meaning:** The verifiable chain from source code and execution environment to data, analysis, publication state, and release.
- **Usage rule:** Commit hashes, checksums, tags, and provenance fields remain unchanged.

### TERM-PUBLICATION-STATE — publication state

- **Russian equivalent:** публикационное состояние.
- **Project meaning:** The specific repository commit at which a published artifact and documentation set is considered pinned.
- **Usage rule:** Do not conflate it with the execution source or analysis implementation, which may have different hashes.

## Statistical and engineering analysis

### TERM-STATISTICAL-UNIT — independent statistical unit

- **Russian equivalent:** независимая статистическая единица.
- **Project meaning:** The smallest unit treated as independent for statistical aggregation or inference.
- **Usage rule:** In B0 this is an independently trained model identified by `model_seed`; repeated measurements of one model are not independent units.

### TERM-MODEL-SEED — model seed

- **Russian equivalent:** случайное начальное значение модели.
- **Project meaning:** The random-number-generator value that defines an independent model initialization and training instance in the registered protocol.
- **Usage rule:** Preserve `model_seed`. The seed value identifies a unit but is not itself the abstract statistical unit.

### TERM-DESCRIPTIVE-ENGINEERING-ANALYSIS — descriptive engineering analysis

- **Russian equivalent:** описательный инженерный анализ.
- **Project meaning:** A summary of observed timing, resource, and structural metrics without a population-level claim beyond the registered matrix.
- **Usage rule:** B0 uses the scope `descriptive_engineering_analysis_n3`; do not restate it as a statistical-significance claim.

### TERM-BOUNDED-FINDING — bounded finding

- **Russian equivalent:** вывод в зарегистрированной области.
- **Project meaning:** An empirical finding valid only for the explicitly stated implementation, environment, data, configurations, and protocol.
- **Usage rule:** Do not extend it to a universal method ranking or a general proof of an algorithmic property.

### TERM-NUMERICAL-EQUIVALENCE-CHECK — numerical-equivalence check

- **Russian equivalent:** проверка численной эквивалентности.
- **Project meaning:** A predefined procedure comparing candidate and reference outputs, states, or gradients under registered numerical criteria.
- **Usage rule:** Passing the check means satisfying thresholds in the studied scope, not algorithmic identity.

### TERM-DECISION-GATE — decision gate

- **Russian equivalent:** решение о допуске.
- **Project meaning:** An explicit documented decision to enter the next experimental phase based on defined criteria and available artifacts.
- **Usage rule:** It is not a statistical hypothesis and does not replace a numerical-equivalence check.

### TERM-FINITE-VALUE-CHECK — finite-value check

- **Russian equivalent:** проверка конечности значений.
- **Project meaning:** A check that registered numerical outputs contain no `NaN`, positive infinity, or negative infinity.
- **Usage rule:** Finiteness is a necessary admission condition but does not by itself establish equivalence.

### TERM-COSINE-SIMILARITY — cosine similarity

- **Russian equivalent:** косинусное сходство.
- **Project meaning:** A normalized measure of directional agreement between two vectors.
- **Usage rule:** Machine fields may use `cosine`; directional agreement is evaluated separately from scale difference.

### TERM-RELATIVE-L2-ERROR — relative L2 error

- **Russian equivalent:** относительная ошибка L2.
- **Project meaning:** The L2 norm of the candidate-reference difference divided by the registered normalization quantity.
- **Usage rule:** The exact normalization formula and zero-denominator handling are defined in the candidate protocol.

## Profiling and compute metrics

### TERM-PROFILING — profiling

- **Russian equivalent:** профилирование.
- **Project meaning:** Instrumented measurement of time, memory, and computational-region contributions under a registered protocol.
- **Usage rule:** Do not use it as a synonym for training or general experiment execution.

### TERM-MATCHED-PROFILING — matched profiling

- **Russian equivalent:** сопоставленное профилирование.
- **Project meaning:** Comparative profiling with matched data, configurations, seeds, warm-up, repetitions, and measured steps.
- **Usage rule:** The full matrix requires a separate decision gate after candidate-specific checks.

### TERM-DEVICE-TIME — device time

- **Russian equivalent:** время на устройстве.
- **Project meaning:** Execution time of operations on the compute device measured with a device-synchronized timer.
- **Usage rule:** Do not conflate it with process wall time, data loading, or orchestration.

### TERM-PEAK-ALLOCATED-MEMORY — peak allocated memory

- **Russian equivalent:** пиковая выделенная память.
- **Project meaning:** The maximum device memory simultaneously reported as allocated by the allocator within the measured scope.
- **Usage rule:** Do not conflate it with reserved memory, total process memory, or system-wide memory.

### TERM-MEASURED-REGION — measured region

- **Russian equivalent:** область измерения.
- **Project meaning:** A named segment of the computational path for which timing or resource metrics are collected separately.
- **Usage rule:** Preserve region identifiers such as `state_inference`.

### TERM-STATE-INFERENCE — state inference

- **Russian equivalent:** вывод состояний.
- **Project meaning:** The iterative computation or refinement of predictive-coding internal states before parameter updates.
- **Usage rule:** The profiling-region identifier is `state_inference`. It does not mean statistical inference.

### TERM-SAVED-TENSORS — saved tensors

- **Russian equivalent:** сохранённые тензоры.
- **Project meaning:** Tensors retained by automatic differentiation for a subsequent backward computation.
- **Usage rule:** Do not conflate them with all live tensors or total allocated memory.

### TERM-SCALING — scaling

- **Russian equivalent:** масштабирование.
- **Project meaning:** The change in a measured quantity under a systematic change in model size, depth, batch size, or another registered factor.
- **Usage rule:** Descriptive `log2` coefficients are not interpreted as a universal scaling law.

### TERM-VJP — vector–Jacobian product (VJP)

- **Russian equivalent:** произведение вектора на якобиан (VJP).
- **Project meaning:** A vector multiplied by a Jacobian without explicitly materializing the full Jacobian.
- **Usage rule:** Use `VJP` after the first definition; preserve `local_state_vjp` and `parameter_vjp` region identifiers.

### TERM-STRUCTURAL-LOCALITY — structural locality

- **Russian equivalent:** структурная локальность.
- **Project meaning:** A bounded dependency structure across layers, states, time, or graph structure, supported by dedicated measurements.
- **Usage rule:** Low time or memory alone does not establish structural locality.

## Reserved terms for the next research line

The following definitions establish terminology for local-predictor design and
passive ECZ diagnostics. They do not change current B0 findings or authorize
full profiling of new candidates.

### TERM-MECHANISM-ATTRIBUTION — mechanism attribution

- **Russian equivalent:** отнесение эффекта к механизму.
- **Project meaning:** The systematic linking of an observed timing, resource, or numerical effect to a specific computational mechanism using decomposition and dedicated checks.
- **Usage rule:** Without an intervention or exclusion test, report it as engineering attribution rather than established causality.

### TERM-REGION-DECOMPOSITION — measured-region decomposition

- **Russian equivalent:** декомпозиция области измерения.
- **Project meaning:** The partition of a named computational region into explicitly defined components for separate accounting of time, memory, saved tensors, or dependencies.
- **Usage rule:** Components require registered boundaries; overlap and uncovered residuals must be reported explicitly.

### TERM-PASSIVE-DIAGNOSTICS — passive diagnostics

- **Russian equivalent:** пассивная диагностика.
- **Project meaning:** Collection of predictions, features, and diagnostic metrics without changing the primary computational path or update decision.
- **Usage rule:** Shadow mode is one form of passive diagnostics; absence of control-path influence is verified separately.

### TERM-LOCAL-PREDICTOR — local predictor

- **Russian equivalent:** локальный предиктор.
- **Project meaning:** A candidate mechanism that estimates the next state or correction from a predefined bounded local context.
- **Usage rule:** The term describes the predictor’s available information and does not establish structural locality of the full system.

### TERM-SHADOW-MODE — shadow mode

- **Russian equivalent:** теневой режим.
- **Project meaning:** A mode in which a candidate computes predictions and diagnostics but does not affect the primary computational path, updates, or published result.
- **Usage rule:** Use it for passive evaluation before the candidate is allowed to control computation.

### TERM-ECZ — equivalence-certified zone (ECZ)

- **Russian equivalent:** зона подтверждённой эквивалентности (ECZ).
- **Project meaning:** An operationally defined region of states, configurations, or observations in which a candidate satisfies registered equivalence criteria relative to a reference.
- **Usage rule:** “Certified” does not mean a global mathematical proof or external certification. ECZ boundaries are protocol-defined and do not extend beyond tested conditions.

## Glossary change procedure

Changing the meaning of a canonical term requires updating both language
versions, checking every repository-wide use, and explicitly documenting the
migration from the previous wording. Change a `TERM-*` identifier only when
concepts are split or merged, and record the change in the changelog.
