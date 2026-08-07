# ADR-113: merged-source binding and attempt-003 execution-freeze contract

## Status

Accepted as the authoring contract for source binding and a future execution
freeze. No image is built, no execution freeze is materialized, and no
computational effect is authorized.

## Context

PR #180 merged the clean attempt-003 source-closure implementation into
`main` as `541b34a57297d2c5a82851bd846b583d4904fba6`. Its parents are the previous `main`
`26e0328bbec433d6f2ec1841ee76a8c2c4312ccc` and implementation commit `4cf74c9632c537459b80e494e6ae88b0bc220c90`.
Historical frozen implementation records are not rewritten: their existing
`source_commit_binding_pending=true` remains evidence of the state at the time
of implementation authoring.

The separate post-merge freeze has semantic identity
`sha256:94562e74965156602df877a6b3a04b1425095c37ca8442dc121360e56dd2fe75`. It proves the merge and successful CI, but is not
an execution freeze.

## Decision

The exact attempt-003 source commit is the merge commit `541b34a57297d2c5a82851bd846b583d4904fba6`.
The binding is considered provable only when:

- Git contains the exact two-parent merge topology;
- the implementation commit directly descends from design commit
  `e49cbdb2f3d87717069f8b5d10a20290c565b0be`;
- the implementation `runtime-SHA256SUMS` has its exact file identity and
  exactly 13 paths;
- every one of the 13 objects exists in `541b34a57297d2c5a82851bd846b583d4904fba6`, and bytes obtained
  by `git show <commit>:<path>` match the registered SHA-256;
- the design, implementation, lineage, and scientific engineering-matrix
  authorization identities remain exact;
- the historical implementation record remains unchanged.

A future build must use an exact archive of the source commit, pinned base
image `rocm/pytorch@sha256:96a2fb24dec9896e2f8238178f0c49d0dcc4c7dcc597be09e4564316bd86d191`, and `SOURCE_GIT_COMMIT=541b34a57297d2c5a82851bd846b583d4904fba6`. The existing
prebuild source-closure gate is mandatory before that build. After the build,
a non-executing inspection must establish a new image digest, repository
digest, exact OCI revision, and exact OCI base image.

Only after successful image inspection may a separate later slice materialize
`experiments/frozen/stage3b-qwake-attempt-003-execution-freeze-v1`. Its future
`execution.json` must set both `source_commit` and `wrapper_commit` to
`541b34a57297d2c5a82851bd846b583d4904fba6` and bind the exact image identities, the four runtime
components, pinned Torch2PC `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4`, and the scientific
authorization.

## Boundary

This slice materializes only the authoring contract and a verifiable merged
source binding. It does not build or run Docker, create an image identity,
materialize an execution freeze, issue or use authorization, create a lease or
outcome, invoke runtime/model code, access the dataset, author a host
invocation chain, commit/push/create a PR/merge, or open `QW-5`.
