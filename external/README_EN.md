# External source code

[Русская версия](README.md)

Torch2PC is cloned into this directory during `make prepare`. The source
checkout itself is excluded from Git.

Before pilot or final experiments:

1. audit the implementation against the official correction;
2. record the complete Torch2PC commit SHA;
3. pin that commit in `configs/base.yaml`;
4. prevent automatic updates of the checkout;
5. record the selected commit in every experiment manifest.

Research conclusions apply only to the pinned implementation and declared
configuration.
