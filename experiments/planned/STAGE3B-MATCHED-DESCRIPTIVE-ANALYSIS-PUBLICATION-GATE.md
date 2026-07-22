# Stage 3B: publication gate описательного анализа сопоставленного профилирования

[English version](STAGE3B-MATCHED-DESCRIPTIVE-ANALYSIS-PUBLICATION-GATE_EN.md)

Статус: **gate frozen; remote publication action pending**.

## 1. Назначение

Этот gate разрешает ограниченную публикацию уже запечатанного 18-файлового
выхода описательного анализа. Он не запускает анализ повторно, не изменяет
запечатанные файлы и не переопределяет решения кандидатов.

Связанные идентичности:

- output registry: `8baa1b55c21ed2b00bd849bbbe4f415d8b5f86d70bd9989d4ec4917765ead1da`;
- external seal: `dbb8983bd77490ca4feedc035ae31ca4cdd0764ecd89dab1b0c3d91aed0ad3cd`;
- evidence release: `stage3b-matched-profiling-evidence-v1`;
- publication action tag: `stage3b-matched-descriptive-analysis-publication-v1`.

## 2. Предусловия

Publication action закрывается при любом нарушении:

1. output, audit, seal или gate registry не проходят SHA-256;
2. inventory 18-файлового output отличается;
3. candidate decisions отличаются от зафиксированных `reject_or_revise`;
4. удалённый evidence release не находится в состоянии `draft`;
5. release уже является immutable;
6. tag выполнения отличается от publication action tag.

Если release был опубликован до gate, его необходимо сначала вернуть в draft.
Это исправляет внешнее состояние GitHub и не изменяет Git tag, assets или
запечатанные исследовательские файлы.

## 3. Публикуемые материалы

До перевода release из draft загружаются:

- воспроизводимый архив 18-файлового output;
- архив audit и external seal;
- publication manifest;
- отдельный реестр SHA-256.

Исходные отчёты сохраняют wording состояния, существовавшего во время их
генерации. Более поздний publication state задаётся внешними audit, seal,
gate и release record без изменения отчётов.

## 4. Граница утверждений после успешного action

Разрешается:

```text
results_publication_permitted=true
release_publication_permitted=true
```

Остаётся запрещено:

```text
superiority_claim_permitted=false
ex_if0_opened=false
policy_activation_permitted=false
test_dataset_access=false
full_stage3b_campaign_complete=false
```

Зафиксированные решения:

- `isolated_layer_vjp`: `reject_or_revise`;
- `composite_vjp`: `reject_or_revise`;
- квалифицированные конфигурации: `0/16` для каждой пары кандидат × метод.

## 5. Следующий переход

Только после успешного publication action и отдельной фиксации его результата
следующим формальным переходом становится `EX-IF0`. Этот gate не открывает
`EX-IF0` сам по себе.
