# Фиксация выхода описательного анализа Stage 3B

[English version](STAGE3B-MATCHED-DESCRIPTIVE-ANALYSIS-OUTPUT-SEAL_EN.md)

## Назначение

Этот документ описывает техническую фиксацию уже выполненного 18-файлового описательного анализа [сопоставленного профилирования](../../docs/glossary.md#term-matched-profiling). Он не запускает анализ повторно, не меняет результаты и не является publication gate.

## Зафиксированные корни

Фиксация разделяет три уровня. Каталог результатов хранит только выход вычисления. Каталог аудита хранит независимую проверку происхождения и контрольных сумм. Каталог печати хранит решение считать неизменённый выход доказательным артефактом репозитория. Такое разделение не позволяет задним числом изменить метаданные анализа и сохраняет исходную границу утверждений.

Каждый уровень проверяется отдельно. Несовпадение хотя бы одной контрольной суммы закрывает переход. Наличие печати не означает, что выводы разрешено публиковать: оно подтверждает только целостность, происхождение и неизменность набора файлов.

```text
output_root=results/stage-3/analysis/matched/stage3b-matched-descriptive-analysis-70d6c3c-v1
audit_root=experiments/frozen/stage3b-matched-descriptive-analysis-output-audit-v1
seal_root=experiments/frozen/stage3b-matched-descriptive-analysis-output-seal-v1
```

Output root содержит ровно 18 зарегистрированных файлов. Audit root содержит `audit.json`, `execution-receipt.json`, `OUTPUT-SHA256SUMS` и `SHA256SUMS`. Seal root содержит `seal.json` и `SHA256SUMS`.

## Идентичности

```text
execution_source_commit=72b95a284e8747a33b8c34d5929d4110aa4bfea1
request_digest=5c813e101c17210443b63b6499c7c6fed88fe34029f438942b71ad9faf127a2e
authorization_digest=5e4f570d81d373637244563afed9d1765fe0d17b3d726db9282b4104c37d83c0
runtime_preflight_digest=428c9a7fdc1baf2b86a033a12189b9b98cce4e41dbb6e87cb73d42f4e9e901cc
runtime_identity_digest=e71f0f8539231e466291843e919b412d44ec6022e4dce863785142b67abe007d
execution_receipt_sha256=997569220aa89261e0d375a70597bb8325186f1739a7977e3a211fce1ffcf8b2
output_registry_sha256=8baa1b55c21ed2b00bd849bbbe4f415d8b5f86d70bd9989d4ec4917765ead1da
audit_record_sha256=a2bfbfc8f57cc681b535e8a8ab0e722fd745f49df9eab8094a6e70e8adb88123
audit_package_registry_sha256=c7984a0559c8ee2c902583abd547dec84f23116b679cdf6cfae665ca167d00c6
seal_digest=dbb8983bd77490ca4feedc035ae31ca4cdd0764ecd89dab1b0c3d91aed0ad3cd
```

## Неизменяемость output

Sealing не добавляет файлов внутрь output root и не переписывает generated metadata. Поле `analysis_output_evidence=false` в generated output сохраняется как исторически точная граница непосредственно после выполнения. Внешний `seal.json` отдельно устанавливает `analysis_output_sealed=true` и `analysis_output_evidence=true` для неизменённого набора файлов.

## Граница утверждений

```text
analysis_execution_performed=true
analysis_results_present=true
analysis_output_audited=true
analysis_output_sealed=true
analysis_output_evidence=true
results_publication_permitted=false
release_publication_permitted=false
superiority_claim_permitted=false
test_dataset_access=false
ex_if0_opened=false
policy_activation_permitted=false
```

До отдельного publication gate запрещены публикация результатов, утверждения о превосходстве, переход к `EX-IF0`, доступ к test split и активация политики.
