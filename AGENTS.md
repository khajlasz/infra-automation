# AGENTS.md

# Infrastructure Automation Framework

This document defines the engineering principles for contributors and AI
agents working on this repository.

The project is a declarative, model-driven infrastructure automation
framework. The Platform Model is the primary source of truth. Validation
and deployment artifacts are derived from that model.

------------------------------------------------------------------------

# Project Goals

The objective is to build a provider-independent framework capable of
modelling distributed platforms and projecting the same logical intent
into multiple deployment and integration backends.

Current implementation:

-   Platform Model loader
-   schema validation
-   semantic/reference validation
-   deployment realizations
-   named Docker hosts and compute-node placement
-   Docker Compose generation
-   Terraform / MikroTik RouterOS generation
-   CLI validation and generation workflow
-   Pull Request CI
-   external observability interface modelling
-   provisioned Grafana dashboards for the Out-Dialer reference platform

Current engineering focus:

-   Observability/SRE for the reference platform
-   persistent observability storage
-   application and infrastructure telemetry
-   dashboards, followed by SLIs/SLOs once signals are reliable

Longer-term exploration includes NetBox inventory/IPAM, AWS, hybrid
on-prem/cloud scenarios and Kubernetes.

Ansible is not an active backend for the current container-based
reference implementation. It may be introduced later if a deployment
target requires host or application configuration on virtual machines or
bare metal.

The primary reference platform is Out-Dialer, a simplified distributed
Voice Campaign Platform inspired by enterprise telecom deployment
patterns. The repository also retains telecom and minimal reference
models for modelling and validation purposes.

------------------------------------------------------------------------

# Engineering Principles

## Preserve the Architecture

The architecture is intentionally designed before implementation.

When implementing changes:

-   preserve existing architectural decisions,
-   avoid redesigning the model unless explicitly requested,
-   implement the smallest change necessary.

If a better design is identified, propose it separately instead of
silently changing the implementation.

## The Model is the Product

The Platform Model is the primary source of truth.

Deployment and integration backends consume the validated model.

Never optimise the logical model for a specific implementation
technology.

## Declarative First

Describe **what** the platform is.

Do not encode **how** a particular technology deploys it in the Platform
Model.

Technology-specific behaviour belongs in realizations, generators and
integrations.

## Keep the Model Normalised

Avoid duplicated information.

If multiple objects share identical data, create a reusable definition
when there is a genuine domain reason to do so.

Use references instead of copying values.

Example:

``` yaml
computeProfile: medium
```

rather than repeating CPU and RAM values on every node.

## Provider Independence

The Platform Model must remain independent from technologies such as:

-   AWS
-   Azure
-   GCP
-   VMware
-   Docker Compose
-   Kubernetes
-   Terraform
-   RouterOS
-   Ansible

Provider-specific and runtime-specific logic belongs outside the logical
model.

## References

Objects reference one another using stable identifiers.

Cross-file references are validated by the framework rather than the
schema.

------------------------------------------------------------------------

# Model and Realization Boundaries

The Platform Model describes stable logical platform intent.

A deployment realization describes environment-specific bindings such
as:

-   Docker hosts
-   compute-node placement
-   Docker network drivers
-   host interface names
-   IPAM ranges
-   physical RouterOS interface mappings

Changing a realization should not require changing logical platform
intent unless the domain itself has changed.

External platform interfaces describe application capabilities that must
be consumed from outside the platform boundary. For example, the
Out-Dialer model describes metrics endpoints reachable from the
observability network.

The external observability stack itself is supporting infrastructure. It
is not an Out-Dialer application workload and should not be pulled into
the logical model merely because it consumes modeled telemetry.

------------------------------------------------------------------------

# Model Refactoring Rules

Model refactoring must preserve semantics.

When modifying the model:

-   never remove information unless explicitly instructed,
-   preserve object identifiers where possible,
-   preserve relationships,
-   update references where required,
-   perform the smallest possible change.

Before deleting any model file, verify that all required information has
been migrated.

------------------------------------------------------------------------

# Validation Philosophy

Validation occurs in multiple stages:

1.  YAML syntax
2.  Yamale schema validation
3.  semantic/reference validation
4.  realization-reference validation
5.  future business-rule validation where justified

Do not attempt to implement cross-reference validation in Yamale.

Generators should consume validated inputs and should not reimplement
validation rules.

The semantic validation registry in
`docs/semantic-validation-registry.md` defines the implemented
reference-integrity rules.

------------------------------------------------------------------------

# Deployment Backends

A backend projects the validated Platform Model and, where required, a
deployment realization into a target technology.

Current backends:

``` text
Platform Model + Realization
        │
        ├── Docker Compose → application workloads
        │
        └── Terraform      → MikroTik RouterOS
```

The Docker backend supports named hosts and compute-node placement. It
produces one Compose specification per Docker host containing assigned
nodes.

The RouterOS backend derives network interfaces, gateway addresses,
address lists and firewall policy from modeled intent and realization
bindings. External-interface access rules must remain before the
terminal inter-zone deny rule.

Future backends may include AWS or Kubernetes.

A new backend should reuse existing logical concepts wherever possible.
Model changes should represent missing domain concepts rather than
requirements of a single technology.

------------------------------------------------------------------------

# Delivery Trust Boundary

Pull Request CI and local-lab delivery have different trust levels.

``` text
feature branch / Pull Request
        │
        ▼
GitHub-hosted CI
        │
        │ no local-lab credentials or connectivity
        ▼
      merge
        │
        ▼
trusted main
        │
        ▼
self-hosted macOS local-lab runner
        │
        ▼
real RouterOS Terraform plan
```

The current `deploy-local-lab.yml` workflow runs on pushes to `main` and
manual dispatch. It validates the model, regenerates RouterOS Terraform,
initializes the real local-lab state and performs `terraform plan` using
protected RouterOS credentials.

It does not currently perform `terraform apply` or Docker workload
deployment. Do not claim those stages are automated until the workflow
implements them.

------------------------------------------------------------------------

# Observability Boundary

Observability is an active project phase and a practical consumer of the
model.

The architectural rule is:

> The Platform Model describes how a platform can be observed; it does
> not own the external observability platform.

Out-Dialer applications expose real Prometheus metrics. The external
metrics interface in the model describes which endpoints may be consumed
from the observability network. RouterOS generation realizes the
required connectivity.

Prometheus, Grafana, Loki and related collectors are supporting lab
infrastructure. Their configuration may live in this repository where
useful for the reference environment, but they are not application
components of the Out-Dialer Platform Model.

Dashboard JSON intended to be reproducible should be kept as code.
Runtime monitoring data such as Prometheus TSDB blocks, Loki chunks and
Grafana runtime database state are operational data and are not
source-controlled.

------------------------------------------------------------------------

# Infrastructure Prerequisites

The framework does not provision the complete laboratory or development
workstation.

For the current local reference lab, prerequisites include:

-   UTM
-   Ubuntu workload VM
-   Ubuntu observability VM
-   MikroTik CHR VM
-   Docker runtime
-   Terraform tooling
-   network reachability from the control workstation

Lab construction belongs to the separate `dev-environment` project.

------------------------------------------------------------------------

# Repository Structure

``` text
adr/
docker/
docs/
models/
├── minimal/
├── out-dialer/
└── telecom/
observability/
realizations/
schema/
src/
├── cli.py
├── generators/
├── loader/
├── model/
├── observability/
└── validation/
lab/
└── terraform/
tests/
```

------------------------------------------------------------------------

# Coding Principles

Python should mirror the framework responsibilities.

Prefer clear modules such as:

``` text
loader/
validation/
generators/
model/
```

over generic abstractions without an immediate use case.

Keep data objects simple.

Business logic belongs in validators and generators rather than model
objects.

## Code Readability

The repository serves two purposes:

-   implement the Infrastructure Automation Framework,
-   remain understandable to engineers reviewing or extending it.

When introducing non-trivial Python language features or design
patterns, prefer concise comments explaining **why** the construct is
useful.

Avoid excessive comments on simple or self-explanatory code.

Prefer readable and maintainable code over clever or highly condensed
implementations.

## Internal Model

The internal Python object model is not required to mirror the YAML
structure exactly.

The loader may perform small, lossless transformations that improve the
API.

These transformations must never lose information or change model
semantics.

------------------------------------------------------------------------

# AI Agent Instructions

## Task Types

Every coding task should be treated as one of the following:

**Implementation**

Add or change requested behaviour. Modify only the components required
to implement that behaviour and its tests.

**Refactoring**

Improve code structure without changing externally observable behaviour.
Functionality and existing semantics must remain unchanged.

**Review/Fix**

Address the specified review findings. Do not expand the task into
unrelated cleanup or redesign.

If the task type is provided in the prompt, preserve that scope
throughout the work.

## Agent Execution Workflow

For implementation work:

1.  inspect only the files and code paths relevant to the requested
    change;
2.  identify current behaviour and the architectural ownership boundary;
3.  produce a short implementation plan before editing code;
4.  make the smallest coherent change that satisfies the task;
5.  run focused tests for the modified component;
6.  run the broader relevant test suite after focused tests pass;
7.  report files changed, behaviour changed, tests executed, assumptions
    and intentionally deferred follow-up work.

Do not begin implementation before understanding the relevant existing
code path.

If implementation reveals that the agreed plan is insufficient or
incorrect, stop and update the plan before expanding scope or changing
architecture.

## Scope Discipline

Do not modify code merely because it is adjacent to the requested
change.

In particular:

-   do not fix unrelated test failures,
-   do not perform opportunistic refactoring,
-   do not rename unrelated objects,
-   do not reformat untouched code,
-   do not update downstream consumers unless the task explicitly
    includes them,
-   do not introduce compatibility layers unless requested,
-   do not preserve obsolete behaviour unless compatibility is explicit.

A useful improvement outside scope should be reported as follow-up work
instead of being implemented.

## Repository Change Boundaries

Treat the major framework responsibilities as separate architectural
layers:

``` text
Platform Model
    │
    ▼
Validation
    │
    ▼
Realization
    │
    ▼
Generators
    │
    ▼
Generated Artifacts
```

A change in one layer does not automatically justify changes in another.

Generated artifacts must never become the source of truth.

## Testing Strategy

Prefer narrow verification before broad verification.

For a change in a specific component:

1.  run its directly related tests;
2.  fix failures caused by the requested change;
3.  run the broader relevant tests;
4.  run the complete test suite when practical.

Do not modify production code solely to make an unrelated test pass.

When reporting completion, include exact test commands and results. If
tests cannot be run, state that explicitly.

## Simplicity Before Abstraction

Prefer the simplest implementation that satisfies current requirements.

Do not introduce classes, extension points, interfaces or generic
frameworks unless they provide immediate value.

When in doubt:

-   prefer a function over a class,
-   prefer explicit code over indirection,
-   introduce abstractions only after multiple concrete use cases
    emerge.

------------------------------------------------------------------------

# Definition of Done

A task is complete only if:

-   the model remains valid,
-   no required information has been lost,
-   references remain consistent,
-   relevant tests pass,
-   generated artifacts remain deterministic where applicable,
-   documentation reflects architectural changes where necessary,
-   changes are ready to review and commit,
-   follow-up work outside scope is identified rather than silently
    implemented.

------------------------------------------------------------------------

## Architecture Ownership

Architectural decisions are made explicitly through discussion and
review.

Implementation tasks should not introduce new architectural concepts
unless explicitly requested.

If implementation reveals a potential architectural improvement,
complete the requested solution first and propose the improvement
separately.
