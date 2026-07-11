# Configuration system

[Русская версия](README.md)


Configuration is composed in this order:

```text
base.yaml
-> hardware/<profile>.yaml
-> stages/<stage>.yaml
-> methods/<method>.yaml
-> experiments/<optional-experiment>.yaml
-> CLI overrides
```

Later values override earlier values. Every run stores the fully resolved
configuration and its SHA-256 digest.
