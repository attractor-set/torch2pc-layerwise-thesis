# ADR-066: `QW-LC4-E` lease and wrapper contract authoring

[Russian version](ADR-066-stage3b-qwake-lc4-e-execution-lease-wrapper-authoring.md)

- **Status:** accepted as an authoring-only slice; [execution](../glossary_EN.md#term-execution) has not started
- **Date:** July 27, 2026

## Context

The `QW-LC4-E` admission freeze was merged into `main` as
`12b7d24153a681f731a43e8497275016ad4e1656` and independently verified. The admission record permits one
engineering [attempt](../glossary_EN.md#term-attempt), but no exclusive lease
exists, the authorization has not been consumed, and model execution has not
started.

Effects require explicit contracts first:

1. a canonical prospective one-attempt lease schema;
2. exact binding to the merged admission, image, Torch2PC, and future wrapper
   commit;
3. a future execution-wrapper contract;
4. exclusive claim, no retry after claim, and atomic output-promotion rules.

## Decision

Add the pure `stage3b_qwake_lc4_execution_wrapper.py` module and a read-only
verifier. They:

- reverify the exact five-file admission package and both SHA-256 registries;
- verify all 168 cells, CPU/ROCm ordering, and 28 reserve probes;
- construct only an in-memory prospective lease that would consume the
  authorization at a future claim;
- construct only an in-memory wrapper contract;
- require an exclusive atomic claim, persistent lease after failure, no retry
  after claim, and atomic output promotion;
- keep scientific execution, [dataset](../glossary_EN.md#term-dataset) access,
  and publication closed.

This slice contains no lease writer, [runtime](../glossary_EN.md#term-runtime) executor, result writer, model
backend, or materialized lease. Prospective `authorization_consumed=true` is a
future-claim test-vector property; repository state remains
`AUTHORIZATION_CONSUMED=false`.

## Exact identities

```text
admission_freeze_merge_commit=12b7d24153a681f731a43e8497275016ad4e1656
admission_freeze_head_commit=52e8bbd54bdea70abbd9e7aff86872b69a8c341d
torch2pc_commit=b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4
admission_sha256=sha256:d1ee6d022588f0a2cf0ac23f3bf8de9b27f9aad4fc1153435bd70e1ab83e296c
admission_package_registry_sha256=sha256:411f3e8d62b367755a6f02070ad84bc6f37cfefad602d885674a844b57aa74cd
admission_source_registry_sha256=sha256:01c9a29d1f80098707d6715ffd5160ad48bb497b08a71180c2b71d8e89b66504
module_sha256=sha256:34980a70d76b582d70333034b4a259b50bd948bb751888f17db9a988c2c77a9b
validator_sha256=sha256:5ce921dc10f95320191effce0b57caef0bbd528550587c4ad443c71b516b75c6
test_sha256=sha256:b7b28b17ab80679ea3653fd1b3586053172c6b74967fa9247a58b404f8042e60
prospective_test_vector_lease_sha256=sha256:66961a641d7f9cc9b7b2f958c432a492c1ada171056b827136171dd0df2b355a
prospective_test_vector_wrapper_contract_sha256=sha256:0ff0cf0b0f23bf21d65567079212e5bad04e16e257815143d3f581664fa4dbf0
authorized_cell_count=168
reserve_probe_count=28
```

## Boundaries

```text
ADMISSION_FREEZE_MERGED=true
EXECUTION_LEASE_WRAPPER_AUTHORING_BRANCH_OPEN=true
EXECUTION_LEASE_SCHEMA_IMPLEMENTED=true
EXECUTION_WRAPPER_CONTRACT_IMPLEMENTED=true
EXECUTION_LEASE_MATERIALIZED=false
EXECUTION_LEASE_WRITER_PRESENT=false
RUNTIME_EXECUTOR_PRESENT=false
RESULT_WRITER_PRESENT=false
QW_LC4_E_EXECUTION_PERMITTED=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
ENGINEERING_EVIDENCE_PRESENT=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```

## Consequences

After merge and independent reverification, a separate slice may implement the
atomic lease writer and concrete execution wrapper. Their presence must not
materialize a lease or start execution. The actual claim and run require a
separate immutable execution freeze.
