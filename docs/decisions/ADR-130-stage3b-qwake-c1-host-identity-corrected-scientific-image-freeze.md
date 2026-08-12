# ADR-130: интеграция научного образа после исправления идентичности хоста

[English version](ADR-130-stage3b-qwake-c1-host-identity-corrected-scientific-image-freeze_EN.md)

<!-- LANG-SOURCE: ../../experiments/frozen/stage3b-qwake-c1-host-identity-corrected-scientific-image-freeze-v1/repository-integration.json -->

## Статус

Принято как репозиторная фиксация уже построенного и независимо проверенного
научного образа. Эта запись не создаёт новую [попытку](../glossary.md#term-attempt),
не разрешает [выполнение](../glossary.md#term-execution) C1 и не изменяет байты
образа или внешних [доказательных материалов](../glossary.md#term-evidence).

## Контекст

ADR-129 исправил контракт идентичности контейнера: основная идентичность
привязана к `UID/GID` хоста, группы ROCm `video`/`render` передаются как
дополнительные, каталог вывода проверяется до создания `host-claim.json`, а
`--cap-drop=ALL` сохраняется без добавления `CAP_DAC_OVERRIDE`.

После слияния PR #202 и отдельной послеслияния проверки был построен новый
научный образ из точного дерева `855889593a33bb6450e31cfc9feb152d14bd5292`. Его замкнутая поверхность
[времени выполнения](../glossary.md#term-runtime) задана манифестом
`sha256:fbfd01ecd41cc1615acef9f0fc9b3dd390e9605ebadd9a5dc86d78a425e2ac7b` из 157 путей.

Образ и его фиксация:

```text
SOURCE_COMMIT=98cff5b2ecd64e1c96e19f0b04104ac00a5c3cf2
SOURCE_TREE=855889593a33bb6450e31cfc9feb152d14bd5292
HOST_IDENTITY_CORRECTION_SHA256=sha256:dd827f2ecb5fc983ad9d800961c34f61d443240651dc007526332fe6215d24aa
RUNTIME_SOURCE_MANIFEST_SHA256=sha256:fbfd01ecd41cc1615acef9f0fc9b3dd390e9605ebadd9a5dc86d78a425e2ac7b
IMAGE_DIGEST=sha256:12a4a6792530471517e53b30625bcfc45031a97bb9072f54bfa0c966e3fc2b5d
FREEZE_SHA256=sha256:ea207e6d31507d449e24fc30bb74fb21ec6560b1ec4a777cb1199de3ad63184f
ORIGINAL_EVIDENCE_SHA256SUMS_SHA256=sha256:051b3665616705f0538b7fdd78d43e15eae2fa05815d62848ec68fb4253004aa
REPOSITORY_INTEGRATION_SHA256=sha256:66369e9f6f666e94625f403c341028ae2249a7e74707c22b0fef75231b67fc46
```

## Решение

1. Копировать 18 исходных файлов внешней фиксации побайтно, без нормализации.
2. Добавить только репозиторную авторизацию интеграции, журнал повторной
   независимой проверки, запись интеграции и `repository-SHA256SUMS`.
3. Считать образ `sha256:12a4a6792530471517e53b30625bcfc45031a97bb9072f54bfa0c966e3fc2b5d` единственным кандидатом для следующей
   новой фиксации запроса C1 после слияния и отдельной послеслияния проверки
   этой интеграции.
4. Сохранить прежний образ `sha256:89703b0b37b2729855835a6ed19ba1ca397ae14614c318344bd7625d12c727ef` и прежний замороженный
   запрос C1 как исторические артефакты. Старый запрос не может быть повторно
   использован, поскольку он связан с прежними идентичностями исходного кода и образа.
5. Не открывать `Attempt-002`, C1/C2/C3/R или публикацию этим ADR.

## Граница эффекта

```text
ORIGINAL_EVIDENCE_BYTES_PRESERVED=true
SCIENTIFIC_IMAGE_MUTATED=false
DOCKER_BUILD_INVOKED=false
DOCKER_RUN_INVOKED=false
PREVIOUS_C1_REQUEST_REUSABLE=false
NEW_C1_REQUEST_FREEZE_REQUIRED=true
NEW_C1_REQUEST_FROZEN=false
NEW_C1_EXECUTION_AUTHORIZATION_ISSUED=false
ATTEMPT002_CREATED=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
PR_MERGED=false
```
