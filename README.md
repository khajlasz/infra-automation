# Infrastructure Automation Framework

A declarative framework for modelling distributed platforms and generating
deployment artifacts.

The framework separates **platform intent** from **implementation**, allowing
the same platform model to generate Terraform, Ansible, documentation and other
automation artifacts.

The initial reference model is inspired by my experience automating Cisco BroadWorks deployments. Product-specific concepts are progressively generalized into reusable modelling patterns applicable to distributed platforms beyond telecommunications.

---

## Motivation

Infrastructure automation often evolves around deployment tools rather than the
platform itself.

Terraform, Ansible and Kubernetes all require their own configuration models,
which frequently duplicate the same information.

This project takes the opposite approach.

Instead of maintaining multiple infrastructure descriptions, the platform is
described once in a provider-independent model.

```
              Platform Model
                     │
          Validation & Normalisation
                     │
      ┌──────────────┼──────────────┐
      │              │              │
 Terraform       Ansible      Documentation
```

The platform model becomes the **single source of truth**.

---

## Project Goals

- Build a provider-independent platform model.
- Eliminate duplicated infrastructure definitions.
- Generate deployment artifacts from a validated model.
- Demonstrate Infrastructure Automation and Network Automation techniques.
- Keep the logical platform independent from deployment technologies.

---

## Current Reference Platform

The first platform implemented in the repository is a telecom reference
architecture inspired by Cisco BroadWorks.

It models:

- multiple deployment sites
- logical networks
- network devices
- compute nodes
- software deployments
- deployment policies

BroadWorks is used only as a reference architecture.

The modelling framework itself is product independent.

---

## Repository Structure

```
docs/
├── architecture.md
├── model.md
└── modelling-guidelines.md

model/
└── telecom/
    ├── platform/
    ├── network/
    ├── compute/
    └── application/

terraform/
```

Future implementation will add:

```
src/
├── loader/
├── validator/
├── generators/
│   ├── terraform/
│   ├── ansible/
│   └── documentation/
└── cli/
```

---

## Modelling Principles

The model follows several principles.

- Declarative
- Provider independent
- Normalised
- Validated before deployment
- Reference based (avoid duplicated information)
- Human readable
- Generator friendly

Every object has a single owner.

Relationships are expressed through references rather than duplicated values.

---

## Current Status

| Area | Status |
|------|--------|
| Platform Architecture | ✅ |
| Infrastructure Object Model | ✅ |
| Telecom Reference Model | 🚧 |
| YAML Validation | Planned |
| Python Loader | Planned |
| Terraform Generator | Planned |
| Ansible Generator | Planned |
| Documentation Generator | Planned |

---

## Long-Term Vision

The telecom model is only the first consumer of the framework.

Future platform models may include:

- Cloud Infrastructure
- Kubernetes Platforms
- AI Infrastructure
- Enterprise Applications

without changing the underlying modelling framework.

---

## Project Status

This project is under active development.

The current focus is establishing a clean, extensible platform model before
implementing generators and deployment tooling.