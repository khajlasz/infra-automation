# Infrastructure Object Model

## Purpose

The Infrastructure Object Model defines the platform-independent language used by
the Infrastructure Automation Framework.

The model describes **what** a distributed platform consists of rather than
**how** it is deployed.

Infrastructure tooling such as Terraform, Ansible or Kubernetes consumes
artifacts generated from this model but is not part of the model itself.

The same modelling language should support multiple reference platforms,
including telecommunications, cloud infrastructure, Kubernetes and AI
platforms.

---

# Design Principles

The object model follows these principles.

- Provider independent
- Declarative
- Normalized
- Reference based
- Human readable
- Generator friendly
- Validated before deployment

Every object has a single owner.

Relationships are expressed using references rather than duplicated
information.

---

# Model Domains

The model is organised into four independent domains.

```
Platform
│
├── Network
├── Compute
└── Application
```

Each domain owns a specific part of the platform.

---

# Platform Domain

## Platform

Represents a complete distributed platform.

Examples:

- Telecom Platform
- AI Platform
- Observability Platform
- Web Application Platform

A Platform owns one or more Sites.

---

## Site

Represents a deployment location.

Examples:

- Physical datacentre
- Cloud region
- Availability zone
- Edge location

Sites group network devices and compute resources.

---

# Network Domain

## Network

Represents a logical network.

Examples:

- signalling
- replication
- media
- core-oam
- dmz-int
- dmz-ext

Networks are referenced by device and node interfaces.

---

## Device Profile

Defines a reusable description of a network device.

Examples:

- MikroTik CHR Router
- MikroTik CHR Switch
- MikroTik CHR Firewall

Device Profiles describe hardware or virtual appliance characteristics.

---

## Device

Represents a concrete network device.

Examples:

- Router
- Switch
- Firewall
- Load Balancer

Devices own Interfaces.

---

## Policy

Represents platform-level networking or security policy.

Policy modelling is intentionally minimal in the current version and will evolve
as generators are implemented.

---

# Compute Domain

## Compute Profile

Defines reusable compute characteristics.

Examples:

- small
- medium
- large

A Compute Profile specifies resources such as CPU and memory.

---

## Storage Profile

Defines reusable storage layouts.

Examples:

- standard
- database

A Storage Profile specifies logical storage allocation.

---

## Node

Represents a compute instance.

Examples:

- Virtual machine
- Bare-metal server
- Cloud instance
- Kubernetes node

Nodes reference:

- Site
- Compute Profile
- Storage Profile
- Deployment

Nodes own Interfaces.

---

## Interface

Represents a network attachment.

Interfaces belong to Nodes or Devices.

Each Interface references exactly one Network.

---

# Application Domain

## Application

Represents a reusable deployable software unit.

Examples:

- OCI
- OCI-P
- WebPortal
- DeviceManagement
- XSI-Actions

Applications describe software independently of deployment.

---

## Deployment

Represents a concrete software stack.

A Deployment specifies:

- Product metadata
- Product version
- Installed Applications
- Application versions
- Deployment-specific configuration

Multiple Nodes may reference the same Deployment.

---

# Object Relationships

```
Platform
└── Sites

Network
├── Networks
├── Device Profiles
├── Devices
└── Policies

Compute
├── Compute Profiles
├── Storage Profiles
└── Nodes
    └── Interfaces

Application
├── Applications
└── Deployments
```

Cross-domain relationships are expressed through references.

Examples:

```
Node
    ↓
Deployment

Node
    ↓
Compute Profile

Node
    ↓
Storage Profile

Interface
    ↓
Network

Device
    ↓
Device Profile
```

---

# Validation

Validation is intentionally divided into multiple stages.

## Structural Validation

Performed using Yamale.

Validates:

- YAML structure
- Required fields
- Data types

---

## Reference Validation

Performed by the framework.

Validates that references resolve correctly.

Examples:

- Deployment exists
- Compute Profile exists
- Storage Profile exists
- Network exists
- Site exists

---

## Business Validation

Performed by the framework.

Business validation checks consistency between model objects.

The current implementation intentionally keeps business validation minimal.
Additional rules will be introduced only when required by the implementation.

---

# Future Evolution

The object model is expected to evolve incrementally.

New concepts should only be introduced when they:

- eliminate duplication,
- improve readability,
- support validation,
- support generators, or
- simplify implementation.

Avoid speculative abstractions.