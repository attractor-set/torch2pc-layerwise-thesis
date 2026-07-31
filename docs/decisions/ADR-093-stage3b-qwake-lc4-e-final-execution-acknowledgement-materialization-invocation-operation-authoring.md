# ADR-093: подготовка операторской операции вызова материализации финального подтверждения `QW-LC4-E`

[English version](ADR-093-stage3b-qwake-lc4-e-final-execution-acknowledgement-materialization-invocation-operation-authoring_EN.md)

- **Статус:** принят как чистый контракт будущей операторской операции; операция не реализована
- **Дата:** 2026-07-31
- **Базовый коммит:** `0ace9f1025100fa29ff0af7523fde17674c4852b`

## Контекст

PR №153 реализовал ограниченный адаптер вызова материализации и был слит как
`0ace9f1025100fa29ff0af7523fde17674c4852b`. Независимая проверка подтвердила
четыре успешные проверки непрерывной интеграции, `144` направленных, `345`
расширенных и `1392` полных теста при `14` предупреждениях. Адаптер существует,
но производственная точка вызова, подтверждение и остальные рабочие артефакты
отсутствуют.

Наличие адаптера не тождественно разрешению конкретной операции. Требуется
отдельно связать одно операторское действие с точной будущей структурой вызова,
не смешивая фразу подтверждения исполнения с фразой запуска материализации.

## Решение

1. Добавить пакет подготовки
   `stage3b-qwake-lc4-e-final-execution-acknowledgement-materialization-invocation-operation-authoring-v1`.
2. Ввести отдельную точную фразу операции
   `INVOKE_QWAKE_LC4_FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION`. Она не
   заменяет и не дублирует фразу подтверждения исполнения.
3. Связать будущую операцию с точным объектом будущего вызова, идентичностью
   оператора и временем разрешения операции.
4. Требовать порядок времени: слияние реализации предшествует подтверждению;
   подтверждение оператора не позже разрешения операции; разрешение операции не
   позже времени выдачи подтверждения; время выдачи не позже материализации.
5. Будущая реализация операции может вызвать только точный библиотечный адаптер
   и не более одного раза. Отдельный предварительный вызов проверки состояния
   запрещён: авторитетной остаётся встроенная в адаптер проверка, чтобы не
   создавать разрыв между проверкой и действием.
6. Прямые вызовы модуля материализации и модуля записи запрещены.
7. Автоматическая и слепая повторная [попытка](../glossary.md#term-attempt) запрещены. Явное восстановление
   возможно только как новая отдельно разрешённая операция с новой внутренней
   классификацией устойчивого состояния.
8. Подготовка, импорт и проверка пакета не создают подтверждение, файл владения,
   квитанцию исхода, команду, Docker-вызов и не выполняют [локальное вычисление](../glossary.md#term-local-compute).

## Граница

```text
ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_IMPLEMENTATION_POST_MERGE_VERIFIED=true
MATERIALIZATION_INVOCATION_IMPLEMENTED=true
MATERIALIZATION_INVOCATION_OPERATION_CONTRACT_AUTHORED=true
MATERIALIZATION_INVOCATION_OPERATION_IMPLEMENTED=false
MATERIALIZATION_INVOCATION_OPERATION_PERFORMED=false
INVOCATION_ADAPTER_CALLED=false
MATERIALIZATION_INVOKED=false
MATERIALIZER_CALLED=false
WRITER_CALLED=false
ADAPTER_OWNED_RECOVERY_PROBE_REQUIRED=true
STANDALONE_PREPROBE_FORBIDDEN=true
AUTOMATIC_RETRY_FORBIDDEN=true
BLIND_RETRY_FORBIDDEN=true
FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUED=false
FINAL_EXECUTION_ACKNOWLEDGED=false
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
DURABLE_HOST_OUTCOME_PRESENT=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```

## Последствия

После слияния и независимой проверки должен быть открыт отдельный срез реализации
операции. Сам контракт не разрешает и не выполняет материализацию.
