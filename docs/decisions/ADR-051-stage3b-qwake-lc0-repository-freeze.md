# ADR-051: фиксация состояния репозитория `QW-LC0`

        [English version](ADR-051-stage3b-qwake-lc0-repository-freeze_EN.md)

        - Статус: принято
        - Дата: 26 июля 2026 года

        ## Контекст

        Контракт `stage3b-qwake-lc0-semantics-scope-v1` записан коммитом
        `715308451ac3e696d4c2209276d36853f6799d6f` и слит в `main` коммитом слияния
        `8429f54257685a879b0a44499d5fa81eab7310ea`. Проверка после слияния подтвердила второго родителя, неизменность
        22-файлового дерева и точные контрольные суммы контракта и реестра.

        Для перехода к `QW-LC1` требуется отдельная [фиксация целостности](../glossary.md#term-integrity-sealing),
        которая записывает состояние контракта на `main`, но сама по себе не открывает
        следующий срез до собственного слияния и повторной проверки.

        ## Решение

        1. Материализовать двухфайловую квитанцию состояния репозитория `QW-LC0`.
        2. Связать её с точными коммитами `main`, первого родителя, контракта и
           предшествующего перехода.
        3. Сохранить контракт и все предшествующие [доказательные материалы](../glossary.md#term-evidence)
           неизменными.
        4. До слияния этой фиксации оставить переход к `QW-LC1` запрещённым, а сам
           `QW-LC1` закрытым.
        5. Не открывать реализацию, [выполнение](../glossary.md#term-execution), сбор признаков, создание эталонных
           меток, научный образ, тестовую выборку или публикацию.

        ## Проверяемая граница

        ```text
        qwake_qw_lc0_semantics_scope_frozen=true
        qwake_qw_lc0_contract_id=stage3b-qwake-lc0-semantics-scope-v1
        qwake_qw_lc0_contract_sha256=sha256:e68e953aa3d5c425678d54b8dd3b756e706e5cc1a1c4862d4c0ba0bda19bf3c3
        qwake_qw_lc0_repository_main_commit=8429f54257685a879b0a44499d5fa81eab7310ea
        qwake_qw_lc0_repository_freeze_materialized=true
        qwake_qw_lc0_repository_freeze_complete=false
        qwake_qw_lc1_transition_permitted=false
        qwake_qw_lc1_open=false
        qwake_local_compute_implementation_open=false
        qwake_local_compute_execution_open=false
        feature_collection_permitted=false
        oracle_label_generation_open=false
        policy_activation_permitted=false
        scientific_execution_open=false
        test_dataset_access=false
        publication_permitted=false
        qwake_next_slice=QW-LC0-repository-freeze-merge
        qwake_post_merge_next_slice=QW-LC1-transition
        ```

        ## Последствия

        После слияния требуется отдельная проверка квитанции на `main`. Только её
        успех может разрешить самостоятельный переход к `QW-LC1`; он не открывается
        этим решением.
