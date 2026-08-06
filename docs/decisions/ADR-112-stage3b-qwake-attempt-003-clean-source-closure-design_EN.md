# ADR-112: clean attempt-003 source-closure design

## Status

Accepted as a design-only decision without implementation or computational
effects.

## Context

The archive preserves the terminal history of the previous
[attempt](../glossary_EN.md#term-attempt). The clean branch starts before
QWake attempt 002 and does not transplant its image freeze, authorization,
host invocation chain, or durable outcome.

## Decision

Attempt 003 receives an independent source-closure contract.

Before a future build, the implementation must verify:

- presence of every object in one exact Git commit;
- exact bytes of every object;
- the SHA-256 identity of every required path;
- semantic inclusion of every path in the build context;
- a deterministic report created without replacement.

During a future build, `sha256sum -c` and a non-executing closure verifier
must run after `COPY . /workspace`. A separate post-build gate must verify
the OCI revision, a new digest, and absence of
[runtime](../glossary_EN.md#term-runtime)
[execution](../glossary_EN.md#term-execution).

`docs/language-map.csv` is checked semantically: exactly one Russian and
English ADR pair must exist. The shared index bytes are not part of this
package's immutable registry.

## Boundary

This slice authors the design only. Implementation,
[run](../glossary_EN.md#term-run), `.dockerignore` or
`Dockerfile.rocm` modification, image build or use, authorization issuance,
lease or outcome creation, model invocation,
[dataset](../glossary_EN.md#term-dataset) access, PR creation or merge,
remote `main` modification, and `QW-5` opening are forbidden.
