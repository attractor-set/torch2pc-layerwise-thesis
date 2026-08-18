# Experiment lifecycle

[Русская версия](README.md)

This directory preserves scientific-procedure lifecycle artifacts: planned
contracts, freeze/authorization/receipt packages, completed summaries, and the
append-only registry. Completing a procedure does not make a hypothesis true.

For historical Stage/QWake branches, local `open/closed` fields describe the
state at the time of that document. They **are not current authorization for a
new run after `v1.0.0`**.

Any post-dissertation scientific execution requires a new protocol/claim
identifier and a separate authorization boundary. The original QWake C1/C2
chain is not rerun, and C3 is not opened retroactively.

Where applicable, `registry.csv` remains append-only: each attempt retains a
unique `run_id`, terminal outcome, and provenance; earlier records are not
rewritten.
