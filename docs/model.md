# Infrastructure Object Model

## Purpose

The Infrastructure Object Model defines the core concepts used throughout the
Infrastructure Automation Framework.

These objects form the platform-independent language from which deployment
artifacts are generated. They intentionally avoid implementation-specific
details such as cloud providers, operating systems, or deployment technologies.

The model should be expressive enough to describe multiple distributed systems,
including telecom platforms, cloud-native applications and AI infrastructure.

---

# Design Principles

The object model follows several principles:

- platform independent
- provider agnostic
- declarative
- composable
- validated before deployment
- implementation independent

Infrastructure tooling (Terraform, Ansible, Kubernetes, etc.) consumes generated
artifacts derived from this model and is not part of the model itself.

---

# Core Objects

## Platform

Represents a complete distributed platform.

A platform consists of one or more deployment sites together with the
applications, policies and operational components required to operate it.

Examples:

- Telecom Platform
- AI Platform
- Observability Platform
- Web Application Platform

---

## Site

Represents a deployment location.

A site may correspond to:

- physical datacenter
- cloud region
- availability zone
- edge location

A Site owns:

- Zones
- Nodes

---

## Zone

Represents a security or trust boundary.

Examples:

- Internet
- DMZ
- Application
- Management
- Storage

Zones contain one or more Networks.

---

## Network

Represents a Layer-3 network segment.

Examples:

- signalling
- replication
- media
- management

Networks contain Interfaces.

---

## Role

Represents a logical responsibility.

A Role describes *what* a component does rather than *how* it is implemented.

Examples:

- Application Server
- API Gateway
- Database
- Monitoring
- Identity Provider

Roles define:

- responsibilities
- provided capabilities
- required capabilities

---

## Node

Represents a concrete deployment of one or more Roles.

Examples:

- virtual machine
- bare metal host
- container
- Kubernetes pod

Nodes own:

- Interfaces
- Services

---

## Interface

Represents a network attachment of a Node.

Interfaces connect Nodes to Networks.

---

## Connection

Represents desired communication between Roles.

Connections are independent of implementation.

Generators translate Connections into:

- firewall rules
- Security Groups
- ACLs
- routing policies

---

## Policy

Defines communication rules and security constraints.

Policies express architectural intent rather than vendor-specific firewall
configuration.

---

## Service

Represents deployed application functionality.

A Service implements one or more Roles.

Examples:

- BroadWorks AS
- PostgreSQL
- FastAPI application
- Prometheus

---

# Object Relationships

Platform
├── Sites
│   ├── Zones
│   │   └── Networks
│   └── Nodes
│       ├── Interfaces
│       └── Services
└── Policies

Roles describe Services.

Connections describe communication between Roles.

Policies constrain Connections.