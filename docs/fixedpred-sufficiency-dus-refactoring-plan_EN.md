# FixedPred sufficiency refactoring plan

[Русская версия](fixedpred-sufficiency-dus-refactoring-plan.md)

**Status:** implementation plan; this document does not open code [execution](glossary_EN.md#term-execution).

## Document purpose

The refactoring prevents oracle knowledge, passive observations, shadow
decisions, and cost optimization from being mixed in one implementation. The
separation makes post-action leakage an architectural violation rather than a
documentation convention.

## 1. Goals

The refactoring separates frozen [evidence](glossary_EN.md#term-evidence) from new code, oracle logic from
pre-action features, decision semantics from acquisition policy, safety from
cost optimization, canonical execution from shadow proposals, and historical
identifiers from normative terminology.

## 2. New namespace

```text
src/torch2pc_thesis/stage3b_sufficiency/
├── types.py
├── context.py
├── rosenbaum_control.py
├── snapshot.py
├── endpoint.py
├── oracle.py
├── margin.py
├── cost.py
├── registry.py
├── acquisition.py
├── policy.py
├── trace.py
├── validation.py
└── features/
```

## 3. Types

```text
OracleStatus = SUFFICIENT | INSUFFICIENT
Decision = DONE | UNKNOWN | SWEEP
ReasonCode
EpochContext
CostVector
AnalyticResult
ShadowTraceRecord
```

`UNKNOWN` is not a member of `OracleStatus`.

## 4. Oracle isolation

Feature modules cannot import the oracle implementation or access the full
suffix, \(Y_{\mathrm{ref}}\), \(M^*\), post-action outcomes, or
oracle-optimal acquisition. An [architecture](glossary_EN.md#term-architecture) test enforces this boundary.

## 5. Analytic interface

Each analytic has an identifier, acquisition level, admissibility predicate,
cost contract, pre-action availability, and deterministic acquisition. One
analytic can be acquired at most once per decision epoch.

## 6. Refactoring sequence

### RF-0 — boundaries

Freeze the successor ADR, allowed scope, forbidden paths, and terminology map.

### RF-1 — pure types

Add enums, dataclasses, schemas, and serialization tests.

### RF-2 — endpoint and margin

Extract EX-IF0 semantics without scientific execution.

### RF-3 — Rosenbaum control

Add explicit mapping among article indices, PC layers, and PyTorch modules.

### RF-4 — immutable snapshot

Prevent mutation of states, parameters, buffers, RNG, and computation paths.

### RF-5 — finite analytic registry

Disallow dynamic discovery, duplicate acquisition, and nondeterministic
tie-breaking.

### RF-6 — cost accounting

Separate observer, analytic, marginal-sweep, and full-reference costs.

### RF-7 — shadow D/U/S

The policy receives only pre-action representations and does not control
execution.

### RF-8 — trace

Add deterministic JSONL, reason codes, and full provenance.

### RF-9 — compatibility

Retain thin adapters and historical filenames without renaming frozen
artifacts.

### RF-10 — independent audit

Check scope, imports, terminology, hashes, RU/EN parity, and claim boundaries.

## 7. Prohibited changes

The refactoring cannot modify `external/Torch2PC`, canonical FixedPred, frozen
evidence, tags, or hashes; it cannot read the test split, generate oracle
labels, or activate a policy.
