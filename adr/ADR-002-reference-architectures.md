# ADR-002: Reference Architectures

## Status

Accepted

## Context

The framework should remain independent from any particular application
platform.

However, realistic examples are required to validate the object model and
demonstrate deployment workflows.

## Decision

The framework defines only generic infrastructure and platform roles.

Product-specific implementations are provided as Reference Architectures.

The first Reference Architecture will model a telecom platform inspired by
Cisco BroadWorks.

Future Reference Architectures may include:

- Web Application
- Observability Platform
- AI Platform

## Consequences

The Infrastructure Object Model remains reusable across multiple domains.

The telecom architecture serves as a realistic validation case while avoiding
tight coupling to BroadWorks-specific concepts.