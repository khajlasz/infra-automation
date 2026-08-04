# AGENTS.md

# Infrastructure Automation Framework

This document defines the engineering principles for contributors and AI agents
working on this repository.

The project is a declarative platform modelling framework. The platform model is
the primary source of truth. Infrastructure automation, validation and
deployment artifacts are generated from this model.

---

# Project Goals

The objective is to build a provider-independent framework capable of modelling
distributed platforms and generating deployment artifacts.

Current generators will include:

- Terraform
- Ansible
- Documentation
- Validation

The first reference implementation models a telecom platform inspired by
BroadWorks deployments.

---

# Engineering Principles

## Preserve the Architecture

The architecture is intentionally designed before implementation.

When implementing changes:

- preserve existing architectural decisions,
- avoid redesigning the model unless explicitly requested,
- implement the smallest change necessary.

If a better design is identified, propose it separately instead of silently
changing the implementation.

---

## The Model is the Product

The platform model is the primary source of truth.

Python, Terraform, Ansible and documentation are generated from the model.

Never optimise the model for a specific implementation technology.

---

## Declarative First

Describe **what** the platform is.

Do not model **how** it is deployed.

Deployment logic belongs in generators.

---

## Keep the Model Normalised

Avoid duplicated information.

If multiple objects share identical data, create a reusable definition.

Use references instead of copying values.

Example:

Good

```yaml
computeProfile: medium
```

Bad

```yaml
cpu: 4
ram: 8192
```

on every node.

---

## Provider Independence

The model must remain independent from:

- AWS
- Azure
- GCP
- VMware
- Terraform
- Ansible

Provider-specific logic belongs in generators.

---

## References

Objects reference one another using stable identifiers.

Examples:

```yaml
site: warsaw
network: signalling
deployment: bw-adp-webex
computeProfile: medium
```

Cross-file references are validated by the framework rather than the schema.

---

# Model Refactoring Rules

Model refactoring must preserve semantics.

When modifying the model:

- never remove information unless explicitly instructed,
- preserve object identifiers,
- preserve relationships,
- update references where required,
- perform the smallest possible change.

Before deleting any model file, verify that all information has been migrated.

---

# Validation Philosophy

Validation occurs in multiple stages.

1. YAML syntax
2. Yamale schema validation
3. Cross-reference validation
4. Business rule validation

Do not attempt to implement cross-reference validation in Yamale.

---

# Working with the Model

When adding new concepts:

- prefer extending existing objects,
- avoid introducing new object types without clear justification,
- avoid speculative abstractions,
- favour simplicity.

Every object should answer a unique engineering question.

If an object exists only for documentation and is not consumed by generators or
validators, reconsider whether it belongs in the model.

---

# Repository Structure

```
docs/
    architecture.md
    model.md
    modelling-guidelines.md

model/
    telecom/
        platform/
        network/
        compute/
        application/

schema/
    telecom/

src/
    loader/
    validator/
    generators/
```

The directory structure should remain consistent across models and schemas.

---

# Coding Principles

Python should mirror the model.

Prefer:

```
loader/
validator/
generators/
model/
```

over generic utility modules.

Keep data classes simple.

Business logic belongs in validators and generators rather than model objects.

---
## Code Readability

The repository serves two purposes:

- implement the Infrastructure Automation Framework,
- help the project owner learn and understand the implementation.

When introducing non-trivial Python language features or design patterns,
prefer adding concise explanatory comments.

Examples include:

- dataclasses
- field(default_factory=...)
- __getattr__()
- __contains__()
- __repr__()
- decorators
- context managers
- pathlib idioms
- type hints
- generic programming

Comments should explain **why** a construct is used rather than merely
describing what the code does.

Example:

```python
# Each ModelDomain instance receives its own dictionary.
# Using default_factory avoids sharing a mutable default between instances.
data: dict[str, Any] = field(default_factory=dict)
```

Avoid excessive commenting of simple or self-explanatory code.
Comments should improve maintainability and help a reader understand the
design decisions behind the implementation.

When implementing a new framework component, favour clear, educational code over
clever or highly condensed implementations. Readability and maintainability are
more important than minimising the number of lines of code.
---
### Internal Model

The internal Python object model is not required to mirror the YAML structure
exactly.

The loader may perform small, lossless transformations that improve the
usability of the API.

Examples:

- unwrap a top-level mapping when its single key matches the filename
- normalise filenames by replacing '-' with '_'

These transformations must never lose information or change the semantics of
the model.
---

# AI Agent Instructions

When performing a task:

1. Read the existing model before making changes.
2. Preserve architectural intent.
3. Make only the requested modifications.
4. Do not silently redesign the model.
5. If a better design is identified, explain it separately.
6. Preserve formatting and naming conventions.
7. Prefer consistency over cleverness.

When refactoring:

- preserve semantics,
- preserve object identifiers,
- preserve references,
- avoid data loss.

If uncertain, stop and ask for clarification.

## Simplicity Before Abstraction

Prefer the simplest implementation that satisfies the current requirements.

Do not introduce classes, extension points, interfaces or generic frameworks
unless they provide immediate value.

When in doubt:

- prefer a function over a class,
- prefer explicit code over indirection,
- introduce abstractions only after multiple concrete use cases emerge.

The framework should evolve from working implementations rather than anticipated
future requirements.

---

# Definition of Done

A task is complete only if:

- the model remains valid,
- no information has been lost,
- references remain consistent,
- documentation reflects the changes where necessary,
- changes are ready to commit.

## Architecture Ownership

Architectural decisions are made explicitly through discussion and review.

Implementation tasks should not introduce new architectural concepts unless
explicitly requested.

If an implementation task reveals a potential improvement to the architecture,
implement the requested solution first, then propose the improvement separately.