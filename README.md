# Infrastructure Automation

> Infrastructure automation using Python, Terraform and Ansible.

## Overview

Infrastructure teams often maintain the same information in multiple places:

- Terraform variables
- Ansible inventory
- host variables
- documentation
- spreadsheets

This project explores a different approach.

Infrastructure is described once using a simple declarative model. Python validates the data and generates artifacts consumed by automation tools such as Terraform and Ansible.

The objective is not to build another Terraform example, but to reduce duplication, improve consistency and automate repetitive work.

The project is inspired by practical experience gained while automating provisioning and infrastructure workflows in large-scale telecommunications environments.

---

## Goals

The project focuses on solving practical infrastructure automation problems:

- describe infrastructure only once
- eliminate duplicated configuration
- validate infrastructure data before deployment
- generate automation artifacts
- keep infrastructure consistent across multiple tools
- provide a clean and maintainable codebase

---

## Current Technology Stack

- Python
- YAML
- Terraform
- Ansible
- Git
- GitHub

Additional technologies may be introduced as the project evolves.

---

## Repository Structure

```
.
├── adr/            # Architecture Decision Records
├── ansible/        # Ansible inventories and playbooks
├── docs/           # Documentation
├── examples/       # Example models
├── model/          # Infrastructure model
├── python/         # Validation and generators
├── schemas/        # Validation schemas
└── terraform/      # Terraform configuration
```

---

## High-Level Workflow

```
Infrastructure Model (YAML)
            │
            ▼
      Schema Validation
            │
            ▼
     Python Processing
            │
     ┌──────┴──────┐
     ▼             ▼
Terraform      Ansible
Artifacts      Inventory
```

The implementation should remain simple. The model exists to support automation, not to introduce unnecessary complexity.

---

## Engineering Principles

- Solve real problems.
- Working software comes first.
- Prefer simple solutions over clever ones.
- Automate repetitive work.
- Keep infrastructure data independent of implementation tools.
- Treat documentation as part of the project.

---

## Roadmap

### Phase 1

- repository structure
- infrastructure model
- schema validation
- Terraform prototype

### Phase 2

- artifact generation
- Ansible inventory generation
- automated validation

### Phase 3

- CI/CD
- automated testing
- additional providers and integrations

---

## Status

The project is under active development.