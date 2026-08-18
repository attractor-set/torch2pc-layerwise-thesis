# External source code

[Русская версия](README.md)

The `external/` directory is reserved for local checkouts of external
implementations and is excluded from Git. Historical dissertation experiments
used a pinned Torch2PC checkout with a full commit identity and separate
environment/provenance bindings.

The dissertation release `v1.0.0` does not require recloning Torch2PC and does
not authorize rerunning completed scientific protocols.

A new independent experiment must separately:

1. select and audit the external implementation;
2. record its complete commit SHA;
3. bind it to a new configuration and protocol identity;
4. prevent automatic checkout updates during registered execution;
5. record the selected identity in the new experiment manifest.

Dissertation conclusions apply only to the historically pinned implementations
and declared configurations that were actually evaluated.
