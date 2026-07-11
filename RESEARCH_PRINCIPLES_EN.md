# Research principles

[Русская версия](RESEARCH_PRINCIPLES.md)

The project uses a neutral observer position and distinguishes definitions,
assumptions, observations, statistical estimates, interpretations, and
limitations. An interpretation does not replace a recorded observation.

An empirical statement enters the final text only when the procedure was
specified before final-test access, code and configuration are identified,
environment and data are recorded, failed attempts remain visible, the
statistical unit is defined, and uncertainty is reported.

A non-significant difference is not interpreted as equivalence. Equivalence is
assessed separately against the practically relevant absolute macro-F1 margin
of 0.01. The margin is fixed before pilot execution and may be changed later
only through a documented ADR; a change after result access is exploratory.

The primary statistical unit is an independently trained model identified by
`model_seed`. Images, batches, layers, and parameters are not independent model
replications. Protocol changes after final-test access receive a new
exploratory experiment identifier and do not replace the pre-specified
analysis.
