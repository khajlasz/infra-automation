# Architecture

## Purpose and Status

This document describes the target logical architecture for the Infrastructure
Automation Framework and the reference platform used to demonstrate it.

The framework uses a declarative Platform Model as its primary source of truth.
The model is validated before deployment artifacts are generated.

The reference platform is a distributed Voice Campaign Platform inspired by
enterprise outbound telecom systems. It is intentionally simplified while
providing realistic infrastructure, networking and operational behaviour.

The current implementation focuses on establishing the Platform Model,
validation framework and artifact generators.

---

# Design Principles

- Define infrastructure and application topology once in a deployment-independent Platform Model.
- Separate logical architecture from deployment technology.
- Validate the Platform Model before artifact generation.
- Generate Terraform, Ansible and NetBox artifacts from the validated model.
- Treat observability as part of the platform rather than an optional add-on.
- Keep implementation simple and evolve abstractions only when multiple concrete use cases require them.

---

# Reference Platform

## Business Workflow

The platform simulates an outbound voice campaign system.

A customer creates a campaign consisting of:

- campaign name,
- campaign description,
- audio announcement,
- optional background music,
- destination telephone numbers,
- meeting information.

The platform performs the following workflow:

1. Customer creates a campaign.
2. Portal validates user input.
3. Campaign Manager performs business validation.
4. Campaign is stored in the database.
5. Campaign Manager dispatches execution.
6. Call Simulation Platform simulates outbound calls.
7. Campaign results are stored.
8. Customer retrieves campaign status and results.

No real SIP signalling or telephone calls are performed.

The objective is to provide realistic platform behaviour suitable for
infrastructure automation, observability and orchestration.

---

# Logical Services

## Portal / REST API

Responsibilities:

- user authentication (simplified),
- campaign creation,
- upload campaign assets,
- input validation,
- campaign status,
- campaign results.

The Portal is the only externally accessible service.

The Portal never communicates directly with the database.

---

## Campaign Manager

The Campaign Manager owns the platform business logic.

Responsibilities:

- business validation,
- campaign lifecycle,
- campaign persistence,
- scheduling,
- dispatching campaigns,
- collecting execution results.

The Campaign Manager is the only service allowed to access the campaign
database.

---

## Call Simulation Platform

Simulates a telecom outbound campaign platform.

Responsibilities:

- receive campaign execution requests,
- simulate outbound calls,
- generate campaign results,
- return execution statistics,
- expose operational metrics.

No real SIP signalling or media processing is performed.

---

## PostgreSQL Database

Persistent storage.

Stores:

- users,
- campaigns,
- subscriber lists,
- execution status,
- execution results.

# Application Endpoints

Applications define the logical endpoints they expose.

An endpoint represents a logical service interface and is independent of the deployment technology.

Each endpoint defines:

- protocol
- port

Examples include:

- HTTPS
- REST
- SQL
- Prometheus metrics

The Platform Model intentionally describes application endpoints rather than Docker ports, Kubernetes Services or firewall rules.

Deployment generators derive technology-specific artifacts from the logical endpoint definitions.

Examples:

Platform Model endpoint

↓

Docker Compose published port

↓

Kubernetes Service

↓

Firewall policy

---

# Security Zones

The platform is divided into logical security zones.

## DMZ

Contains externally accessible services.

Current members:

- Portal / REST API

---

## Application Network

Contains internal business services.

Current members:

- Campaign Manager
- Call Simulation Platform

---

## Database Network

Contains persistent storage.

Current members:

- PostgreSQL

The database is accessible only from the Application Network.

---

# Logical Communication

| Source | Destination | Protocol | Purpose |
| --- | --- | --- | --- |
| Customer | Portal | HTTPS | User interface |
| Portal | Campaign Manager | REST | Campaign operations |
| Campaign Manager | PostgreSQL | SQL | Persistent storage |
| Campaign Manager | Call Simulation Platform | REST | Campaign execution |
| Call Simulation Platform | Campaign Manager | REST | Execution results |

Future versions may replace selected REST interfaces with asynchronous messaging
without changing the Platform Model.

---

# Platform Nodes

The initial reference platform consists of four logical nodes.

| Node | Hosted service |
| --- | --- |
| portal | Portal / REST API |
| campaign | Campaign Manager |
| simulator | Call Simulation Platform |
| database | PostgreSQL |

A node represents a logical compute resource.

Its implementation as a Docker container, virtual machine or cloud instance is
a deployment decision and is intentionally not part of the Platform Model.

---

# Logical Networks

| Network | Security zone | Purpose |
| --- | --- | --- |
| dmz | DMZ | External client access |
| application | Application | Internal service communication |
| database | Database | Persistent storage |

CIDR ranges, subnet allocation and routing policies belong to deployment
artifacts and are generated from the Platform Model.

---

# Service Interface Matrix

| Service | Connected networks |
| --- | --- |
| Portal | dmz, application |
| Campaign Manager | application, database |
| Call Simulation Platform | application |
| PostgreSQL | database |

Semantic validation rules should ensure that unsupported interfaces cannot be
added accidentally.

---

# Network Elements

The initial implementation targets a simple routed topology.

| Element | Role |
| --- | --- |
| Router / Firewall | Connects security zones and enforces traffic policy |
| DMZ Switch | Connects externally accessible services |
| Internal Switch | Connects application services |
| Database Switch | Connects database services |

The first implementation is expected to use MikroTik CHR as the virtual router.

The exact implementation remains independent from the logical Platform Model.

---

# Source of Truth and Automation Flow

The Platform Model is the primary source of truth.

```text
Platform Model
        │
        ▼
Schema Validation
        │
        ▼
Semantic Validation
        │
        ▼
Validated Platform Model
        │
 ┌──────┼─────────┐
 ▼      ▼         ▼
Terraform NetBox Ansible
```

Every deployment artifact is generated from the validated Platform Model.

---

# Initial Deployment Strategy

The first implementation prioritises rapid iteration.

| Component | Initial runtime |
| --- | --- |
| Portal | Docker |
| Campaign Manager | Docker |
| Call Simulation Platform | Docker |
| PostgreSQL | Docker |
| Router / Firewall | MikroTik CHR virtual machine |

Future versions may replace selected Docker deployments with virtual machines
without changing the logical Platform Model.

---

# Observability

Every logical service shall expose:

- structured logs,
- Prometheus metrics,
- health endpoint.

Grafana, Prometheus and Loki are deployed as supporting infrastructure and
monitor the generated platform.

---

# Open Decisions

- Introduce asynchronous messaging between Campaign Manager and Call Simulation Platform.
- Define deployment profiles for multiple runtime targets.
- Define NetBox object generation.
- Define Terraform module structure.
- Define Ansible inventory and host variable generation.
- Define firewall policy between security zones.
- Define cloud and hybrid deployment scenarios.