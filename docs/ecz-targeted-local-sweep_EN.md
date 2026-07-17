# ECZ-targeted local sweep: future design

[Русская версия](ecz-targeted-local-sweep.md)

## Status

`ECZ` means only `Error-Cancellation Zone`. Before `EX-IF0`, it remains a
passive diagnostic category. This document does not add a local action to B1/B2
and does not modify sealed contracts.

## What ECZ establishes and does not establish

ECZ may indicate that a small aggregate correction hides active components. It
does not establish:

- the need for another sweep;
- correctness of the selected block;
- sufficiency of a local sweep;
- savings relative to `full_exact`;
- safe stopping after a local sweep.

The transition from ECZ to action therefore requires separate
`exact_verification`.

## Local-action candidate

The future branch has the form:

```text
local_sweep(block_id)
```

`block_id` is selected only by a frozen rule over eligible blocks. The rule may
use ECZ strength, transport [evidence](glossary_EN.md#term-evidence), layer/sweep context, and uncertainty, but
not the test split.

A technical block/chunk is not automatically a scientific block. The mapping
from diagnostic block to executable local action is frozen before confirmatory
results are inspected.

## Exact-verification gate

From one restored state, execute:

```text
stop
local_sweep(block_id)
full_exact
```

Compare [endpoint-gradient utility](glossary_EN.md#term-endpoint-gradient-utility), [decision regret](glossary_EN.md#term-decision-regret), dangerous misses, state
transition, and the complete [cost vector](glossary_EN.md#term-cost-vector). The local branch is admissible only
when it is safe and cheaper than the corresponding `full_exact`.

`zero_dangerous_misses` is a hard barrier. Mean improvement cannot compensate
for one [dangerous miss](glossary_EN.md#term-dangerous-miss).

## Cost feasibility

Total cost includes:

- ECZ/PC-CATM feature computation;
- block selection;
- local sweep;
- observer and synchronization;
- predictor/controller;
- [fallback](glossary_EN.md#term-fallback) validation;
- actual `fallback_exact`.

If total policy cost is not below `full_exact`, the [candidate](glossary_EN.md#term-candidate) is rejected
before Pareto screening.

## Claim boundary

A positive result supports only the claim that the frozen ECZ-targeted local
action is useful in the registered scope. It does not establish universal
predictive-coding locality and does not transfer automatically to other
architectures, precisions, or hardware.
