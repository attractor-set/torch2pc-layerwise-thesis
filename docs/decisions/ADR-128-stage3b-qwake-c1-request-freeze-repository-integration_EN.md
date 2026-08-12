# ADR-128: repository integration of the frozen `C1` request

[Русская версия](ADR-128-stage3b-qwake-c1-request-freeze-repository-integration.md)

<!-- LANG-SOURCE: ../../experiments/frozen/stage3b-qwake-fresh-corrected-image-bound-c1-request-freeze-v1/repository-integration.json -->

Normative terms:
[execution](../glossary_EN.md#term-execution),
[evidence](../glossary_EN.md#term-evidence),
[freeze](../glossary_EN.md#term-freeze),
[campaign role](../glossary_EN.md#term-campaign-role),
[dataset](../glossary_EN.md#term-dataset), and
[test-dataset access](../glossary_EN.md#term-test-dataset-access).

## Status

Accepted as repository integration of the already frozen and independently
verified `C1_COLLECTION` request. This slice does not modify the request or
preregistration manifest, refreeze the request, or issue scientific execution
authorization.

## Bound chain

The canonical repository state before request freeze is
`ba771e77f3ecff23d9f22319f413a708d930ed6e` / `76c7244d522c381cbcb7ce8c7dd1b5553b7ad329`.

The executable image remains `sha256:89703b0b37b2729855835a6ed19ba1ca397ae14614c318344bd7625d12c727ef`, built from source
commit `3858d3a7e6d7b3401e999523bc6675dc7dd0223d` and frozen as `sha256:ce8c054c92df18512b2a88ac25148f44c15487d8c2d4e68d8751966ac17bf287`.
Its repository integration is `sha256:70012413e1d6bd69dbad060cef0d4b19e0bfe2635eca4dbe746ccfc42544ae72`.

The C1 preregistration identity is `sha256:c9fa7efb2f6816a9f7f09c7acce7cdc2e531935b28c70d00774bf79c38d47a48`.
The canonical request has semantic identity `sha256:7e238ed8a61b7d80e52d67eef8a5f3af6e0c889c81b885a28a98df237284442e`, file
identity `sha256:ee72e90ef7f1bef3abbe9d2fcea5cea6f7d203aa1138c5d2d1eb8c39fe9ab694`, and freeze
`sha256:340f46bae2ca11e679893464f9f430ac93f1af49d39606b57638ba714e131bcc`.

## Decision

1. The seven original request-freeze evidence files are copied into the
   repository byte-for-byte; their original `SHA256SUMS`, whose hash is
   `sha256:2b36093a310a81bacb8a46122481ae071c882008e16e1be8f192634739a531d9`, remains unchanged.
2. The repository wrapper binds those bytes to the integration authorization,
   a fresh independent read-only verification, and integration hash
   `sha256:a053011096dee7c3b4e5690190bca1909b2bf325fc4352366728c6ef4129a433`.
3. `request.json` and `preregistration-manifest.json` are not modified or
   recreated.
4. The historical old authorization remains unconsumed and unconsumable; the
   fresh request-freeze authorization has already been consumed exactly once
   and cannot be consumed again.
5. `C1_REQUEST_FROZEN=true`, while
   `C1_EXECUTION_AUTHORIZATION_ISSUED=false`.
6. C1/C2/C3/R execution, Docker effects, test-dataset access, and publication
   remain closed.
7. After this ADR is merged and separately post-merge verified, the next
   boundary may only be a separate C1 execution authorization.

## Verifiable boundary

```text
C1_REQUEST_SHA256=sha256:7e238ed8a61b7d80e52d67eef8a5f3af6e0c889c81b885a28a98df237284442e
C1_REQUEST_FILE_SHA256=sha256:ee72e90ef7f1bef3abbe9d2fcea5cea6f7d203aa1138c5d2d1eb8c39fe9ab694
C1_REQUEST_FREEZE_SHA256=sha256:340f46bae2ca11e679893464f9f430ac93f1af49d39606b57638ba714e131bcc
PREREGISTRATION_MANIFEST_SHA256=sha256:c9fa7efb2f6816a9f7f09c7acce7cdc2e531935b28c70d00774bf79c38d47a48
C1_REQUEST_FREEZE_INDEPENDENTLY_VERIFIED=true
ORIGINAL_EVIDENCE_BYTES_PRESERVED=true
ORIGINAL_EVIDENCE_FILE_COUNT=7
HISTORICAL_C1_REQUEST_FREEZE_AUTHORIZATION_CONSUMED=false
HISTORICAL_C1_REQUEST_FREEZE_AUTHORIZATION_CONSUMABLE=false
FRESH_REQUEST_FREEZE_AUTHORIZATION_CONSUMED=true
FRESH_REQUEST_FREEZE_AUTHORIZATION_RECONSUMED=false
C1_REQUEST_FROZEN=true
C1_EXECUTION_AUTHORIZATION_ISSUED=false
C1_COLLECTION_OPEN=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
NEXT_SLICE=merge-post-merge-verify-then-authorize-C1-execution-boundary
```

Repository integration hash: `sha256:a053011096dee7c3b4e5690190bca1909b2bf325fc4352366728c6ef4129a433`.
