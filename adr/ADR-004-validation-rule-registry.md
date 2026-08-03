# ADR-004: Validation Registry

## Status

Accepted

---

## Context

The Infrastructure Automation Framework validates infrastructure models in
multiple stages.

Validation is layered. Each stage is responsible for a specific class of
validation and SHALL NOT duplicate responsibilities handled by earlier stages.

Current validation stages are:

- YAML parsing
- Schema validation
- Framework validation

YAML parsing validates syntax.

Schema validation validates the structure of individual model files.

Framework validation validates semantic relationships between objects after the
complete `PlatformModel` has been assembled.

Examples include:

- references to non-existent objects
- duplicate IP addresses
- invalid deployment relationships
- infrastructure consistency rules

As the number of validation rules grows, keeping the specification only in
Python code makes it difficult to:

- understand framework capabilities
- review validation coverage
- track implementation progress
- support deterministic AI-assisted implementation

---

## Decision

Framework validation rules SHALL be maintained in a dedicated Validation
Registry.

The registry is the authoritative specification for framework validation.

Each validation rule receives a stable identifier.

Examples:

- REF-001
- UNI-001
- CON-001

Python implementations, unit tests and log messages SHALL reference these rule
identifiers.

Validation rules SHALL only describe behaviour that cannot be enforced by
earlier validation stages.

---

## Consequences

### Advantages

- Clear separation of validation responsibilities.
- Validation behaviour is documented independently of implementation.
- Validation coverage is easy to review.
- AI implementations can be generated from explicit specifications.
- Tests naturally map to rule identifiers.
- Log messages include stable rule identifiers.

### Trade-offs

- Registry and implementation must remain synchronized.
- Every new validation rule requires documentation before implementation.

---

## Implementation

The Validation Registry is maintained in

```
docs/validation-registry.md
```

The registry is a living document and evolves together with the framework.