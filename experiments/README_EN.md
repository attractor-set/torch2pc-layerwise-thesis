# Experiment lifecycle

[Русская версия](README.md)

`registry.csv` is an append-only event log. Each attempt has a unique `run_id`
and normally records `running` followed by `completed` or `failed`.

A completed procedure is not itself evidence that a hypothesis is true.
