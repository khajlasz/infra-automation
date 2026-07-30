# ADR-003: Observability Strategy

## Status

Accepted

## Context

The Infrastructure Automation Framework is intended to evolve into a production-quality software platform rather than a collection of automation scripts.

As the project grows, understanding its runtime behaviour becomes increasingly important. Engineers should be able to answer questions such as:

- What is the application doing?
- How long do operations take?
- Why did a validation fail?
- Which component produced an error?
- How does performance change over time?

Observability is therefore considered an architectural concern from the beginning of the project, not an operational feature added later.

---

## Decision

The framework will be designed around three complementary observability pillars.

### 1. Logging

Logs provide detailed information about individual events occurring during execution.

Typical examples include:

- application startup
- model loading
- validation errors
- generator execution
- unexpected exceptions

Logs are primarily intended for troubleshooting and understanding execution flow.

---

### 2. Metrics

Metrics provide numerical information describing application behaviour over time.

Examples include:

- loader execution duration
- number of YAML files loaded
- validation error count
- generator execution duration

Metrics allow trends and regressions to be detected.

---

### 3. Tracing

Tracing records the execution path of a single operation across multiple components.

A single CLI command should eventually be traceable through:

CLI
→ Loader
→ Structural Validation
→ Reference Validation
→ Business Validation
→ Generator

Tracing is considered an advanced capability and will be introduced after logging and metrics.

---

## Guiding Principles

### Observability is a first-class concern

Every significant feature should consider:

- What should be logged?
- What should be measured?
- How can failures be diagnosed?

Observability is part of the feature design process.

---

### Business events over implementation details

Telemetry should describe meaningful domain events instead of low-level implementation steps.

Prefer:

"Loaded 18 model files"

over

"Calling yaml.safe_load()"

---

### Structured logging

All logging should use Python's logging framework.

Logs should be machine-readable and avoid ad-hoc print statements.

---

### Vendor-neutral architecture

The application must not depend directly on a specific observability platform.

Framework code should communicate through an internal observability abstraction.

This allows different backends to be adopted without changing business logic.

---

### Incremental adoption

Observability will be introduced in stages.

Phase 1
- Python logging

Phase 2
- Application metrics

Phase 3
- Prometheus

Phase 4
- Grafana dashboards

Phase 5
- Centralized logging (Loki)

Phase 6
- Distributed tracing (OpenTelemetry)

Each phase must provide measurable value before introducing additional tooling.

---

## Architecture

```
                     infra-automation
                           │
          ┌────────────────┼────────────────┐
          │                │                │
        Logs           Metrics          Traces
          │                │                │
     logging         Prometheus      OpenTelemetry
          │                │                │
          └────────────────┼────────────────┘
                           │
                        Grafana
```

---

## Initial Scope

The first instrumented components will be:

- Loader
- Reference Validator
- Business Validator
- CLI

Each component should expose meaningful log events and basic execution metrics.

---

## Consequences

### Positive

- Easier troubleshooting
- Performance visibility
- Better engineering practices
- Production-ready architecture
- Valuable learning experience with modern observability tooling

### Negative

- Slightly higher implementation effort
- Additional architectural concepts introduced early
- Future maintenance of observability infrastructure

These trade-offs are considered acceptable because observability is a core engineering capability of modern infrastructure platforms.

The objective is not merely to automate infrastructure, but to build automation that is itself observable, measurable, and diagnosable.