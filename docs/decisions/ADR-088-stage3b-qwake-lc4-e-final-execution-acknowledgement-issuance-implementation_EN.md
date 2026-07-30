# ADR-088: `QW-LC4-E` final acknowledgement issuance implementation

- **Status:** accepted
- **Date:** 2026-07-30
- **Basis:** independently verified PR #148 merge
  `8343724c66b1d22f01846d9fc70f01738a09127a`
- **Merge parents:**
  `eb20c157584efff8e9aa0418385242c7d7b26eab` and
  `a3984013f8861a532b3f29e234ed1c61be670d97`

## Context

ADR-087 froze the future final-acknowledgement file schema, complete identity
chain, and atomic issuance requirements. After that contract was merged, no
implementation existed that could persist an already-built canonical
acknowledgement envelope with exclusive no-overwrite semantics.

Implementation must remain separate from actual issuance. A writer function in
the repository is not an operator acknowledgement, does not permit invocation,
and does not create the acknowledgement file.

## Decision

Add a separate implementation module that:

1. reverifies the frozen implementation package and complete ADR-087 chain;
2. accepts only a fully verified `ProspectiveFinalExecutionAcknowledgementIssuance`;
3. requires absence of output root, acknowledgement, lease v1, lease v2, and
   durable outcome;
4. requires a pre-existing real parent-directory chain;
5. rejects symbolic parents and stale temporary files;
6. creates a temporary file with `O_CREAT | O_EXCL` and `O_NOFOLLOW`;
7. writes canonical UTF-8 JSON with mode `0600`;
8. fsyncs the file;
9. links the temporary file to the target with a no-overwrite hard link;
10. fsyncs the parent directory;
11. reverifies exact bytes, mode, and SHA-256;
12. removes the temporary file and fsyncs the directory again;
13. has no production callsite for the writer function;
14. does not inspect the image, materialize a command, or invoke subprocess,
    Docker, or [local compute](../glossary_EN.md#term-local-compute).

## Effect boundary

The static verifier checks the package, AST, absence of production callsites,
and the closed production boundary. Writer tests run only in isolated temporary
directories. The implementation branch, commit, PR, and merge must not create
the production acknowledgement.

```text
ACKNOWLEDGEMENT_ISSUANCE_AUTHORING_POST_MERGE_VERIFIED=true
ACKNOWLEDGEMENT_ISSUANCE_CONTRACT_AUTHORED=true
ACKNOWLEDGEMENT_ISSUANCE_IMPLEMENTED=true
FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUED=false
FINAL_EXECUTION_ACKNOWLEDGED=false
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
DURABLE_HOST_OUTCOME_PRESENT=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
IMAGE_INSPECTION_PERFORMED=false
INVOCATION_COMMAND_MATERIALIZED=false
DOCKER_RUN_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```

## Consequences

After merge, a verifiable persistence mechanism exists, but no persisted
artifact exists. Actual issuance requires a separate materialization slice,
concrete operator and issuer identities, exact timestamps, and a separate
explicit decision. Re-issuance and retry are forbidden.
