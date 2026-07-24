# Backlog

---

# Sprint 0 - Foundation

## Architecture

- [x] Define project vision
- [x] Define design principles
- [x] Define Infrastructure Object Model
- [x] Introduce Reference Architecture concept
- [ ] Finalize Platform Role taxonomy
- [ ] Review object relationships
- [ ] Define Connection model
- [ ] Define Policy model
- [ ] Define deployment lifecycle
- [ ] Separate framework documentation from reference architectures

## Documentation

- [x] architecture.md
- [x] model.md
- [x] ADR-001 Source of Truth
- [x] ADR-002 Reference Architectures
- [ ] reference-architecture-telecom.md
- [ ] platform-roles.md

---

# Sprint 1 - Infrastructure Model

## Model

- [ ] Design YAML structure
- [ ] Define naming conventions
- [ ] Define validation schema
- [ ] Define object identifiers
- [ ] Create sample telecom model

## Validation

- [ ] Validate required objects
- [ ] Validate object relationships
- [ ] Validate interface matrix
- [ ] Validate connection matrix

---

# Sprint 2 - Engine

## Python Domain Model

- [ ] Platform
- [ ] Site
- [ ] Zone
- [ ] Network
- [ ] Node
- [ ] Interface
- [ ] Role
- [ ] Service (or Component)
- [ ] Connection
- [ ] Policy

## Framework

- [ ] YAML loader
- [ ] Internal Object Model
- [ ] Validation engine
- [ ] Generator framework

---

# Sprint 3 - Generators

- [ ] Terraform tfvars generator
- [ ] Terraform module generator
- [ ] Ansible inventory generator
- [ ] host_vars generator
- [ ] group_vars generator

---

# Sprint 4 - Deployment

- [ ] AWS prototype
- [ ] Hetzner prototype
- [ ] Multi-cloud deployment
- [ ] Sample application deployment

---

# Sprint 5 - Operations

- [ ] NetBox integration
- [ ] GitHub Actions pipeline
- [ ] Documentation site
- [ ] Monitoring
- [ ] Smoke tests

---

# Future Ideas

- [ ] Kubernetes deployment target
- [ ] Docker Compose deployment target
- [ ] AI Platform reference architecture
- [ ] Web Application reference architecture
- [ ] Observability reference architecture

---

# Open Questions

- [ ] Service vs Component terminology
- [ ] Role inheritance
- [ ] Capability model
- [ ] Provider abstraction
- [ ] Secret management strategy