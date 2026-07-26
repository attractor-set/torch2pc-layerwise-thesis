# ADR-051: `QW-LC0` repository freeze

        [Russian version](ADR-051-stage3b-qwake-lc0-repository-freeze.md)

        - Status: accepted
        - Date: 26 July 2026

        ## Context

        Contract `stage3b-qwake-lc0-semantics-scope-v1` was recorded by commit
        `715308451ac3e696d4c2209276d36853f6799d6f` and merged into `main` by merge commit
        `8429f54257685a879b0a44499d5fa81eab7310ea`. Post-merge verification confirmed the second parent, preservation of
        the 22-file tree, and the exact contract and registry checksums.

        Transition to `QW-LC1` requires a separate [integrity sealing](../glossary_EN.md#term-integrity-sealing)
        record of the contract state on `main`. Materializing that record does not open
        the next slice before its own merge and post-merge verification.

        ## Decision

        1. Materialize a two-file `QW-LC0` repository-freeze receipt.
        2. Bind it to the exact `main`, first-parent, contract, and predecessor-transition
           commits.
        3. Preserve the contract and all predecessor [evidence](../glossary_EN.md#term-evidence) byte-for-byte.
        4. Keep transition to `QW-LC1` prohibited and `QW-LC1` closed until this freeze
           is merged and reverified.
        5. Do not open implementation, [execution](../glossary_EN.md#term-execution), feature collection, oracle-label
           generation, the scientific image, test split, or publication.

        ## Verifiable boundary

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

        ## Consequences

        A separate post-merge verification of this receipt on `main` is required. Only
        its success may permit an independent transition to `QW-LC1`; this decision
        does not open `QW-LC1`.
