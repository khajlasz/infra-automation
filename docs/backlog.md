# Backlog

---

# Sprint 0 - Foundation

## Architecture

- [x] Define project vision
- [x] Define design principles
- [x] Define platform architecture
- [x] Define platform object model
- [x] Separate framework from reference models
- [x] Establish modelling guidelines

## Documentation

- [x] README.md
- [x] architecture.md
- [x] model.md
- [x] modelling-guidelines.md
- [x] AGENTS.md
- [x] ADR-001 Source of Truth
- [x] ADR-002 Reference Architectures

---

# Sprint 1 - Platform Model

## Model

- [x] Design model directory structure
- [x] Split model into domains
- [x] Define object identifiers
- [x] Define naming conventions
- [x] Normalize object relationships
- [x] Create telecom reference model

## Schema

- [x] Generate Yamale schemas
- [ ] Review generated schemas
- [ ] Validate complete telecom model using Yamale

---

# Sprint 2 - Core Framework

## Loader

- [ ] Load complete model
- [ ] Load Yamale schemas
- [ ] Validate model structure
- [ ] Build internal object model
- [ ] Resolve object references

## Validation

- [ ] Reference validation
- [ ] Duplicate identifier detection
- [ ] Circular dependency detection
- [ ] Human-readable validation report

## CLI

- [ ] validate command
- [ ] summary command

---

# Sprint 3 - Generators

## Terraform

- [ ] tfvars generator
- [ ] AWS infrastructure generator
- [ ] MikroTik configuration generator

## Ansible

- [ ] inventory generator
- [ ] host_vars generator
- [ ] group_vars generator

## Documentation

- [ ] Platform summary
- [ ] Inventory report
- [ ] Network documentation

---

# Sprint 4 - Reference Implementation

- [ ] AWS deployment prototype
- [ ] MikroTik deployment prototype
- [ ] Mock application deployment
- [ ] End-to-end deployment

---

# Sprint 5 - Tooling

- [ ] NetBox integration
- [ ] GitHub Actions pipeline
- [ ] Model visualisation
- [ ] Documentation site

---

# Framework Milestones

## v0.1

- [x] Platform architecture
- [x] Platform object model
- [x] Telecom reference model
- [x] Yamale schema draft

## v0.2

- [ ] Python loader
- [ ] Structural validation
- [ ] Reference validation
- [ ] Validation CLI

## v0.3

- [ ] Terraform generator
- [ ] Ansible generator
- [ ] Documentation generator

## v1.0

- [ ] End-to-end reference deployment

---

# Future Ideas

- [ ] Kubernetes deployment target
- [ ] Docker Compose deployment target
- [ ] AI Platform reference model
- [ ] Web Application reference model
- [ ] Observability reference model
- [ ] VMware platform model
- [ ] OpenAPI platform model

---

# Open Questions

- [ ] Should products become first-class model objects?
- [ ] Should deployment requirements remain part of deployments?
- [ ] How should software version compatibility be modelled?
- [ ] How should policies be represented?
- [ ] What should be the long-term validation architecture?

---

# Future Language Features

The following concepts have intentionally been postponed until implementation
demonstrates a real need for them.

- Deployment requirements (requiredNetworks, requiredStorageProfile)
- Application dependency validation
- Interface naming conventions
- Version compatibility rules
- Policy-based validation
- Capability model

---

# Design Principles

The following principles guide the evolution of the framework.

- The platform model is the primary source of truth.
- Every piece of information has exactly one owner.
- Prefer references over duplicated information.
- Keep the model provider-independent.
- Structural validation belongs to Yamale.
- Reference validation belongs to the framework.
- Business validation should be implemented only when required by the model.
- Introduce new abstractions only when implementation proves they are needed.