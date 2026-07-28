# ADR-067: atomic `QW-LC4-E` lease-writer and execution-wrapper implementation

[Russian version](ADR-067-stage3b-qwake-lc4-e-execution-lease-wrapper-implementation.md)

- **Status:** accepted as a separate implementation slice; actual claim and [execution](../glossary_EN.md#term-execution) remain prohibited
- **Date:** 27 July 2026

## Context

The lease/wrapper authoring slice merged through PR #127 into `main` as
`e0455dc77b49f5b220231509fe6062d275b6ee9b` and passed independent
post-merge verification. The previous slice froze the prospective lease,
identity binding, and effect contract but intentionally contained no atomic
lease writer, executor, or result writer.

The implementation must preserve one exclusive [attempt](../glossary_EN.md#term-attempt), persistent ownership
after failure, no overwrite of an existing output, and atomic publication of a
complete result tree. Importing or verifying the module must not claim the
repository lease or run the engineering workload.

The implementation must demonstrate:

1. exactly one competing process obtains the lease file;
2. the lease persists after every error and prohibits retry;
3. an existing result directory cannot be overwritten;
4. an incomplete directory never becomes the canonical result;
5. importing and verifying the module creates no repository lease and starts no computation.

## Decision

Add a separate
`stage3b_qwake_lc4_execution_wrapper_implementation.py` module while leaving
the frozen authoring module unchanged.

The explicit effect functions implement:

- same-directory temporary-file creation, `fsync`, and a hard-link no-replace
  lease claim;
- an output-absence recheck after the claim so a race consumes the lease but
  blocks backend invocation;
- canonical materialized-lease validation;
- an injected typed [runtime](../glossary_EN.md#term-runtime) backend confined to a hidden staging directory;
- rejection of symlinks and non-regular staging entries;
- canonical backend and wrapper receipts;
- recursive synchronization and Linux `renameat2(RENAME_NOREPLACE)` output
  promotion;
- staging cleanup after failure while the lease persists.

The module imports neither Torch nor a concrete model backend. The verifier
uses only a temporary synthetic root and confirms that the repository lease and
runtime output remain absent before and after the check.

## Verification model

The verifier runs the full synthetic cycle only below `/tmp`:

1. reverify the frozen admission;
2. build the test lease record;
3. materialize it atomically in a temporary root;
4. run a synthetic backend that creates one engineering file;
5. write the receipt and atomically promote the temporary result;
6. confirm that the lease persists;
7. remove the temporary root;
8. reconfirm that the repository lease and output directory remain absent.

Unit tests separately cover concurrent claim behavior, retry, an existing
output, the post-claim race, a damaged lease, a symlink, backend failure, an
invalid receipt, empty output, the pre-promotion race, and preservation of a
foreign output directory.

## Exact identities

```text
base_commit=e0455dc77b49f5b220231509fe6062d275b6ee9b
authoring_head_commit=0b59a2445d2e3367d717bbdb68d9b9ba45233bb6
authoring_commit=1c9f2ef2ac7e76e7ed0a5da9d54ac773e6e9df6f
torch2pc_commit=b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4
authoring_json_sha256=sha256:a685ba8fa1f7e28020b79fb54e9f94ac54c00564113c40a97d14188b875d9e6c
authoring_registry_sha256=sha256:d0e11bdddac46d8995d51998c453e11a8155f05a461686be8b7f5a88aa4fb29e
implementation_module_sha256=sha256:43e114dfdb69fa54a993a98b2a487777c40168374e61c0949e5cf862d42f7d9f
validator_sha256=sha256:f2aeb396b31810c59e17d669e0345f61294c5b678a5adf217fc1398019ae9ef1
test_sha256=sha256:c93648799fbd9e728a20f2f557589a78c9b9f2767be652486bd4494064c06511
implementation_json_sha256=sha256:f7cb2c72f5e9516d808f8f76802e2e560579f407aa1e155675bae2570a09b08e
implementation_registry_sha256=sha256:348b574bf7093edd4db263779014c256209a38b1c9e4c78f9598d0f82bf8b59a
lease_test_vector_sha256=sha256:d12058ab7732f883162b8592e4a3523bd3ec354d283c3e463ad4680f854f6283
wrapper_contract_test_vector_sha256=sha256:53c15dcc1cb89377851340d3e7aa358f0c6707a9ca9051013181366879b1374b
backend_receipt_test_vector_sha256=sha256:62ab256d71951d31c3b6a9de9761ef0ef260d1257cbf15b654ac3b15ad2f702c
wrapper_receipt_test_vector_sha256=sha256:76a4f22ca8009ae3c9ede57c7d319117f2ab6aa3f84daea99611fb59371ddcff
```

## Current boundaries

```text
LEASE_WRAPPER_AUTHORING_MERGED=true
LEASE_WRAPPER_IMPLEMENTATION_BRANCH_OPEN=true
LEASE_WRAPPER_IMPLEMENTATION_MATERIALIZED=true
EXECUTION_LEASE_WRITER_PRESENT=true
RUNTIME_EXECUTOR_PRESENT=true
RESULT_WRITER_PRESENT=true
EXECUTION_LEASE_MATERIALIZED=false
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

Code availability is not execution authorization. A separate immutable
execution freeze must bind the exact implementation commit, image, operator
acknowledgement, and only permitted invocation before a real claim can occur.

## Consequences

After commit, merge, and independent verification, a separate execution freeze
may bind the exact implementation commit, immutable image, operator
acknowledgement, and only permitted invocation. Until that freeze exists, any
effectful invocation must fail closed and cannot count as `QW-LC4-E`.
