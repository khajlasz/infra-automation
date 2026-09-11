# AGENTS.md

# Infrastructure Automation Framework

This document defines the engineering principles for contributors and AI agents
working on this repository.

The project is a declarative, model-driven infrastructure automation framework.
The Platform Model is the primary source of truth. Validation and deployment
artifacts are derived from that model.

---

# Project Goals

The objective is to build a provider-independent framework capable of modelling
distributed platforms and projecting the same logical intent into multiple
deployment and integration backends.

Current implementation:

- Platform Model loader
- schema validation
- semantic/reference validation
- Docker Compose generator
- Docker Compose YAML serialization
- CLI validation and generation workflow

Current roadmap:

- Terraform / MikroTik RouterOS backend
- NetBox inventory and IPAM integration
- Terraform / AWS backend
- hybrid on-prem/cloud scenarios

Ansible is not an active backend for the current container-based reference
implementation. It may be introduced later if a deployment target requires
host or application configuration on virtual machines or bare metal.

The primary reference platform is Out-Dialer, a simplified distributed Voice
Campaign Platform inspired by enterprise telecom deployment patterns. The
repository also retains telecom and minimal reference models for modelling and
validation purposes.

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

The Platform Model is the primary source of truth.

Deployment and integration backends consume the validated model.

Never optimise the logical model for a specific implementation technology.

---

## Declarative First

Describe **what** the platform is.

Do not encode **how** a particular technology deploys it in the Platform Model.

Technology-specific behaviour belongs in generators and integrations.

---

## Keep the Model Normalised

Avoid duplicated information.

If multiple objects share identical data, create a reusable definition when
there is a genuine domain reason to do so.

Use references instead of copying values.

Example:

Good:

```yaml
computeProfile: medium
```

Bad:

```yaml
cpu: 4
ram: 8192
```

on every node.

---

## Provider Independence

The Platform Model must remain independent from technologies such as:

- AWS
- Azure
- GCP
- VMware
- Docker Compose
- Kubernetes
- Terraform
- RouterOS
- Ansible

Provider-specific and runtime-specific logic belongs in backends.

---

## References

Objects reference one another using stable identifiers.

Examples:

```yaml
site: lab
network: internal
deployment: portal
computeProfile: small
```

Cross-file references are validated by the framework rather than the schema.

---

# Model Refactoring Rules

Model refactoring must preserve semantics.

When modifying the model:

- never remove information unless explicitly instructed,
- preserve object identifiers where possible,
- preserve relationships,
- update references where required,
- perform the smallest possible change.

Before deleting any model file, verify that all required information has been
migrated.

---

# Validation Philosophy

Validation occurs in multiple stages:

1. YAML syntax
2. Yamale schema validation
3. semantic/reference validation
4. future business-rule validation where justified

Do not attempt to implement cross-reference validation in Yamale.

Generators should consume an already validated Platform Model and should not
reimplement validation rules.

---

# Working with the Model

When adding new concepts:

- prefer extending existing objects,
- avoid introducing new object types without clear justification,
- avoid speculative abstractions,
- favour simplicity,
- add deployment-specific information to a backend rather than the logical
  model unless it represents genuine platform intent.

Every object should answer a unique engineering question.

If an object exists only for documentation and is not consumed by generators,
validators or integrations, reconsider whether it belongs in the model.

---

# Deployment Backends

A backend projects the validated Platform Model into a target technology.

Current backend:

```text
Platform Model -> Docker Compose
```

Next backend:

```text
Platform Model -> Terraform -> MikroTik RouterOS
```

Future backends may include AWS or Kubernetes.

A new backend should reuse existing logical concepts wherever possible. Model
changes should represent missing domain concepts rather than requirements of a
single technology.

---

# Infrastructure Prerequisites

The framework does not need to provision the complete laboratory or development
workstation.

For the current local reference lab, the following are prerequisites:

- UTM
- Ubuntu Docker host VM
- MikroTik CHR VM
- Docker runtime
- Terraform tooling
- network reachability from the control workstation

Lab construction belongs to the separate `dev-environment` project.

This separation mirrors real environments where compute and network platforms
exist before application/platform automation is applied.

---

# NetBox

NetBox remains a future integration for inventory and IPAM rather than simply
another deployment generator.

Potential responsibilities include:

- sites
- devices and VMs
- interfaces
- prefixes
- IP addresses
- topology metadata
- hierarchical configuration context

The ownership boundary between Platform Model intent and NetBox operational
inventory should be decided through concrete use cases rather than assumed in
advance.

---

# Repository Structure

```text
adr/
docker/
docs/
models/
├── minimal/
├── out-dialer/
└── telecom/
observability/
schema/
src/
├── cli.py
├── generators/
├── loader/
├── model/
├── observability/
└── validation/
terraform/
tests/
```

The structure may evolve as new backends are implemented, but model, schema,
validation and generator responsibilities should remain clearly separated.

---

# Coding Principles

Python should mirror the framework responsibilities.

Prefer clear modules such as:

```text
loader/
validation/
generators/
model/
```

over generic abstractions without an immediate use case.

Keep data objects simple.

Business logic belongs in validators and generators rather than model objects.

---

## Code Readability

The repository serves two purposes:

- implement the Infrastructure Automation Framework,
- remain understandable to engineers reviewing or extending it.

When introducing non-trivial Python language features or design patterns,
prefer concise comments explaining **why** the construct is useful.

Avoid excessive comments on simple or self-explanatory code.

Prefer readable and maintainable code over clever or highly condensed
implementations.

---

## Internal Model

The internal Python object model is not required to mirror the YAML structure
exactly.

The loader may perform small, lossless transformations that improve the API.

Examples include:

- unwrapping a top-level mapping when its single key matches the filename,
- normalising filenames by replacing `-` with `_`.

These transformations must never lose information or change model semantics.

---

# AI Agent Instructions

## Task Types

Every coding task should be treated as one of the following:

**Implementation**

Add or change requested behaviour. Modify only the components required to
implement that behaviour and its tests.

**Refactoring**

Improve code structure without changing externally observable behaviour.
Functionality and existing semantics must remain unchanged.

**Review/Fix**

Address the specified review findings. Do not expand the task into unrelated
cleanup or redesign.

If the task type is provided in the prompt, preserve that scope throughout the
work.

---

## Agent Execution Workflow

For implementation work, follow this sequence:

1. Inspect only the files and code paths relevant to the requested change.
2. Identify the current behaviour and the architectural ownership boundary.
3. Produce a short implementation plan before editing code.
4. Make the smallest coherent change that satisfies the task.
5. Run focused tests for the modified component.
6. Run the broader relevant test suite after focused tests pass.
7. Report:
   - files changed,
   - behaviour changed,
   - tests executed and their results,
   - assumptions made,
   - follow-up work intentionally left out of scope.

Do not begin implementation before understanding the relevant existing code path.
If implementation reveals that the agreed plan is insufficient or incorrect,
stop and update the plan before expanding scope or changing architecture.

---

## Scope Discipline

Do not modify code merely because it is adjacent to the requested change.

In particular:

- do not fix unrelated test failures,
- do not perform opportunistic refactoring,
- do not rename unrelated objects,
- do not reformat untouched code,
- do not update downstream consumers unless the task explicitly includes them,
- do not introduce compatibility layers unless requested,
- do not preserve obsolete behaviour unless compatibility is an explicit
  requirement.

A temporary incompatibility is acceptable when a task intentionally changes an
internal contract and downstream adaptation is scheduled as a separate
milestone.

If a potentially useful improvement is outside the requested scope, report it
as follow-up work instead of implementing it.

---

## Repository Change Boundaries

Treat the major framework responsibilities as separate architectural layers:

```text
Platform Model
    |
    v
Validation
    |
    v
Realization
    |
    v
Generators
    |
    v
Generated Artifacts
```
A change in one layer does not automatically justify changes in another.

Before modifying another layer, determine whether the requested task explicitly
requires it.

Examples:

- changing realization structure does not automatically require modifying the Platform Model,
- changing Platform Model semantics may require corresponding validation changes,
- generator changes should consume established model and realization contracts,
- generated artifacts must not become the source of truth.

Keep changes within the ownership boundary of the current task whenever
possible.

## Testing Strategy

Prefer narrow verification before broad verification.

For a change in a specific component:

1. run its directly related tests,
2. fix failures caused by the requested change,
3. run the broader relevant tests,
4. run the complete test suite when practical.

Do not modify production code solely to make an unrelated test pass.

When reporting completion, include the exact test commands and whether they passed.

If tests cannot be run, state that explicitly. Never infer or claim that tests pass without executing them.

When performing a task:

1. Preserve architectural intent.
2. Make only the requested modifications.
3. Do not silently redesign the model or realization.
4. Preserve existing formatting and naming conventions.
5. Prefer consistency and explicit code over cleverness.
6. Report architectural improvements separately rather than implementing them implicitly.
7. Treat passing tests as verification, not as permission to broaden the task.

When refactoring:

- preserve semantics,
- preserve object identifiers where possible,
- preserve references,
- avoid data loss.

If uncertainty affects architecture or data semantics, stop and ask for
clarification.

---

## Simplicity Before Abstraction

Prefer the simplest implementation that satisfies current requirements.

Do not introduce classes, extension points, interfaces or generic frameworks
unless they provide immediate value.

When in doubt:

- prefer a function over a class,
- prefer explicit code over indirection,
- introduce abstractions only after multiple concrete use cases emerge.

The framework should evolve from working implementations rather than
anticipated future requirements.

---

# Definition of Done

A task is complete only if:

- the model remains valid,
- no required information has been lost,
- references remain consistent,
- relevant tests pass,
- generated artifacts remain deterministic where applicable,
- documentation reflects architectural changes where necessary,
- changes are ready to review and commit,
- follow-up work outside the task scope is identified rather than silently implemented.

---

## Architecture Ownership

Architectural decisions are made explicitly through discussion and review.

Implementation tasks should not introduce new architectural concepts unless
explicitly requested.

If implementation reveals a potential architectural improvement, complete the
requested solution first and propose the improvement separately.
