# Architecture

## 1. Purpose

The Infrastructure Automation Framework uses a declarative **Platform Model**
as the primary source of truth for distributed platform topology.

The model describes **what the platform is** rather than how a particular
deployment technology realizes it.

Deployment-specific generators translate the validated model into concrete
artifacts such as Docker Compose or Terraform.

The central architectural principle is:

> Platform intent belongs in the model. Deployment implementation belongs in
> generators.

---

## 2. Architecture Overview

```text
                    YAML Platform Model
                            │
                            ▼
                          Loader
                            │
                            ▼
                      PlatformModel
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
                 Deployment Realization
                            │
              ┌─────────────┴─────────────┐
              │                           │
              ▼                           ▼
     Docker Compose Generator  Terraform RouterOS Generator
              │                           │
              ▼                           ▼
       Application Runtime          Infrastructure
```

Generators consume the loaded and validated object model.

They do not independently parse the YAML source and should not duplicate
validation responsibilities.

A deployment realization supplies environment-specific bindings that do not
belong in the provider-independent Platform Model. The local-lab realization
currently maps logical networks to Docker parent interfaces and IPAM ranges,
and to physical RouterOS interfaces.

---

## 3. Design Principles

The framework is designed around the following principles:

- declarative
- provider independent
- deployment independent
- normalized
- reference based
- validated before generation
- human readable
- generator friendly
- incremental rather than over-generalized

Each object should have a single owner.

Relationships should be expressed through references rather than duplicated
values.

New abstractions should be introduced when concrete deployment targets justify
them rather than in anticipation of hypothetical requirements.

---

## 4. Model Boundaries

The Platform Model describes logical platform intent.

Examples include:

- compute nodes
- applications
- deployments
- application endpoints
- logical networks
- interfaces
- network devices
- communication policies
- sites

The Platform Model should not directly describe technology-specific
implementations such as:

- Docker bridge configuration
- Docker Compose syntax
- Kubernetes Services
- AWS subnets
- RouterOS resource syntax
- Linux bridge commands

Those concepts belong to deployment backends.

For example:

```text
                 Logical Network
                       │
          ┌────────────┼────────────┐
          │            │            │
          ▼            ▼            ▼
    Docker Network  RouterOS     AWS Subnet
                    Network
```

The logical object remains stable while its realization changes.

---

## 5. Reference Platform: Out-Dialer

The primary reference platform is **Out-Dialer**, a simplified distributed
Voice Campaign Platform.

It is inspired by enterprise outbound telecom systems while remaining small
enough to serve as an understandable automation example.

### Portal

Responsibilities include:

- external API / user access
- authentication
- campaign creation
- input validation
- campaign status retrieval

The Portal is the externally accessible application component.

### Campaign Manager

Responsibilities include:

- campaign lifecycle
- business validation
- persistence
- scheduling
- execution dispatch
- result collection

The Campaign Manager is the application component allowed to access the
database.

### Call Simulator

Responsibilities include:

- receiving campaign execution requests
- simulating outbound calls
- returning execution results
- exposing operational metrics

No real SIP signalling or media processing is required.

### PostgreSQL

Provides persistent storage for campaign and execution data.

---

## 6. Logical Communication

```text
Customer
   │
   ▼
Portal
   │
   ▼
Campaign Manager
   ├──────────────► PostgreSQL
   │
   ▼
Call Simulator
```

Typical communication includes:

| Source | Destination | Purpose |
|---|---|---|
| Customer | Portal | External API |
| Portal | Campaign Manager | Campaign operations |
| Campaign Manager | PostgreSQL | Persistence |
| Campaign Manager | Call Simulator | Campaign execution |
| Call Simulator | Campaign Manager | Results |

The model describes logical communication rather than Docker-, RouterOS- or
Kubernetes-specific objects.

---

## 7. Logical Compute Model

A node represents a logical compute resource.

For example:

```text
portal
campaign
call_simulator
database
```

A node does not inherently mean:

- Docker container
- virtual machine
- EC2 instance
- Kubernetes Pod

Those are deployment decisions.

A deployment backend maps the logical node into an appropriate runtime
resource.

---

## 8. Logical Network Model

The reference platform contains several logical network/security zones:

```text
DMZ
Internal
Database
```

Nodes connect to networks through modeled interfaces.

Conceptually:

```text
Portal
  ├── DMZ
  └── Internal

Campaign
  ├── Internal
  └── Database

Call Simulator
  └── Internal

Database
  └── Database
```

The Platform Model expresses the topology without prescribing the underlying
network technology.

---

## 9. Application Endpoints

Applications define logical endpoints.

An endpoint represents a service interface and may describe concepts such as:

- protocol
- port
- service purpose

Examples include:

- HTTPS
- REST
- SQL
- Prometheus metrics

One logical endpoint may eventually drive several implementation artifacts:

```text
                  Application Endpoint
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
        Docker Port   Firewall Rule   K8s Service
```

The model therefore represents application intent rather than deployment
syntax.

---

## 10. Docker Compose Backend

The Docker Compose generator is the first implemented deployment backend.

```text
Platform Model
      │
      ▼
DockerComposeGenerator.generate()
      │
      ▼
Compose Object
      │
      ▼
serialize()
      │
      ▼
docker-compose.yaml
```

### Current Mapping

Each compute node becomes a Docker Compose service.

Current mappings include:

```text
compute node       → service
deployment         → image
node name          → hostname
node interfaces    → service networks
application ports  → published ports
logical networks   → top-level Compose networks
```

The first end-to-end implementation proved that a validated Platform Model can
be loaded, transformed into a deployment artifact, serialized and accepted by
the target runtime.

### Current Limitations

Runtime experimentation exposed several concepts that are not yet completely
modeled:

- environment variables
- explicit runtime image metadata
- host/container port overrides
- persistent storage

These are deliberately not blockers for the next architectural milestone.

They can be added when the model has sufficient evidence for the appropriate
abstractions.

---

## 11. Local Reference Lab

The local lab demonstrates compute and network automation from the same
Platform Model.

The lab itself is a prerequisite and is not provisioned by this framework.

```text
                        macOS
                 Automation Control Plane
                          │
                         UTM
                          │
              ┌───────────┴───────────┐
              │                       │
              ▼                       ▼
       Ubuntu Docker Host        MikroTik CHR
              │                       │
              └──── Network Fabric ───┘
```

### macOS

The workstation provides the development and automation control plane.

Typical tools include:

- Git
- Python
- Terraform
- Docker CLI
- WinBox
- VSCode / OpenCode

### Ubuntu Docker Host

The Ubuntu VM represents an existing compute/runtime platform.

Docker Compose artifacts generated by the framework are executed on this host.

### MikroTik CHR

MikroTik CHR represents existing routed network and firewall infrastructure.

Terraform will configure RouterOS rather than provision the CHR virtual
machine itself.

This mirrors a real environment in which compute and networking infrastructure
exist before platform-specific automation is applied.

Lab construction and workstation configuration belong to the separate
`dev-environment` project.

---

## 12. Infrastructure Prerequisites vs Platform Automation

The framework deliberately distinguishes between **building the lab** and
**automating the modeled platform**.

The following are prerequisites and are outside the framework's current scope:

- installing UTM
- creating the Ubuntu VM
- creating the MikroTik CHR VM
- installing Docker on the compute host
- installing Terraform
- configuring the development workstation

The framework begins once deployment targets exist and are reachable.

This boundary mirrors data-center and cloud environments where platform
automation consumes existing infrastructure capabilities.

---

## 13. Terraform / RouterOS Backend

The Terraform / RouterOS backend is the second implemented deployment backend.

Its purpose is to prove that the same Platform Model driving application
deployment can also drive network infrastructure.

```text
                    Platform Model
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
       Docker Compose              Terraform
              │                         │
              ▼                         ▼
        Docker Host               MikroTik CHR
```

Current mappings include:

```text
logical networks       → RouterOS Ethernet interfaces
realization mappings   → physical interface factory names
network CIDRs          → gateway IP addresses
logical networks       → firewall address-list entries
communication policies → firewall filter rules
```

The generator also adds baseline rules for established/related traffic and
invalid connection state, followed by a logged default deny for other
inter-zone traffic.

The CLI requires a deployment realization for this backend because physical
RouterOS interface names are properties of the target environment rather than
logical platform intent. It emits Terraform HCL that has been validated against
the existing MikroTik CHR local lab.

The current scope is intentionally narrow. It does not provision CHR, manage
Terraform state remotely or implement a CI-controlled apply workflow. Additional
RouterOS resources should be introduced only when required by modeled platform
behavior.

---

## 14. Configuration Management

Ansible is not currently an active backend because the reference compute
implementation uses containers.

Docker Compose currently provides the required application realization.

This is a deliberate scope decision rather than a rejection of configuration
management.

If a future deployment target maps logical compute nodes to virtual machines or
bare-metal hosts, configuration management may become appropriate:

```text
Platform Model
      │
      ├── Terraform → infrastructure realization
      │
      └── Ansible   → host/application configuration
```

A backend should be introduced because a deployment target requires it, not
simply because the technology is available.

---

## 15. NetBox: Inventory and IPAM

NetBox remains part of the longer-term architecture as an inventory and IP
Address Management capability.

Its role differs from deployment backends such as Docker Compose or Terraform.

Conceptually:

```text
                       Platform Model
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
       Docker Compose      Terraform        NetBox
              │               │               │
              ▼               ▼               ▼
         Workloads       Infrastructure  Inventory/IPAM
```

Potential uses include:

- device and VM inventory
- site representation
- prefixes and IP address allocation
- interface inventory
- topology information
- operational metadata

The exact ownership boundary between the Platform Model and NetBox remains an
open architectural decision.

Initially, NetBox could be populated from the Platform Model.

In a larger environment, NetBox could instead own selected operational facts
such as assigned prefixes, addresses, sites and physical devices while the
Platform Model continues to own application and platform intent.

---

## 16. Hierarchical Infrastructure Context

The current reference models are intentionally small and mostly flat.

Larger real-world infrastructure frequently introduces hierarchy such as:

```text
system / global
       │
       ▼
     region
       │
       ▼
availability zone / data center
       │
       ▼
      site
       │
       ▼
  device role
       │
       ▼
     device
```

Configuration may be inherited and overridden at different levels.

This creates a requirement fundamentally different from the current flat
reference model.

NetBox Config Context provides one useful reference pattern: metadata can be
associated with different scopes and merged into the effective configuration
for a particular device.

The framework does not currently implement hierarchical context merging.

If future platform models require it, the design should investigate whether:

1. hierarchical context belongs directly in the Platform Model,
2. NetBox should provide the hierarchy and resolved context,
3. or the loader/normalization layer should combine model intent with inventory
   context.

This decision should be driven by a concrete larger-scale use case.

---

## 17. Future AWS Backend

A future phase may introduce AWS as another infrastructure backend.

Conceptually:

```text
                         Platform Model
                                │
             ┌──────────────────┴──────────────────┐
             │                                     │
             ▼                                     ▼
       Local / On-Prem                         AWS Backend
             │                                     │
       ┌─────┴─────┐                         Terraform AWS
       │           │                               │
    Docker      RouterOS                           AWS
```

The architectural test is whether the logical Platform Model remains stable
while infrastructure realization changes.

Possible mappings include:

```text
logical network   → RouterOS segment   → AWS subnet
security policy   → RouterOS firewall  → Security Group / NACL
logical node      → Docker service     → cloud compute/workload
routing intent    → RouterOS routes    → AWS route tables
```

These are backend mappings rather than model-level technology choices.

---

## 18. Hybrid On-Prem / Cloud Direction

A later demonstration may combine the local/on-prem implementation with AWS.

Potential scenarios include:

- shared observability
- routed or VPN connectivity
- cloud disaster recovery
- common inventory/IPAM
- common security-policy intent
- workloads distributed between on-prem and cloud

For example:

```text
            Local / On-Prem
                  │
             RouterOS
                  │
           Hybrid Connectivity
                  │
               AWS VPC
```

The purpose of the hybrid scenario is not simply to demonstrate connectivity.

It should demonstrate that one logical platform description can drive multiple
infrastructure implementations while remaining operationally coherent.

---

## 19. Observability

Observability is treated as a platform capability.

The planned Observability/SRE phase follows the initial CI/CD phase. Its
proposed signal pipeline is:

```text
Ubuntu / Containers / RouterOS / Applications
                       │
          metrics, logs and synthetic probes
                       │
              ┌────────┴────────┐
              ▼                 ▼
          Prometheus           Loki
              └────────┬────────┘
                       ▼
                    Grafana
                       │
                       ▼
          SLIs / SLOs / Error Budgets
```

Planned components include:

- Grafana
- Prometheus
- Loki
- node and RouterOS telemetry collectors
- application metrics and logs
- synthetic network-policy probes

The probes will test runtime behavior against modeled communication policy.
Initial examples are:

```text
DMZ → Internal       expected ALLOW
Internal → Database  expected ALLOW
DMZ → Database       expected DENY
```

Candidate SLIs cover service availability, request latency, allowed-flow
availability and forbidden-flow enforcement. SLOs will be defined only after
the corresponding signals exist and can be measured reliably. Error budgets
and burn-rate alerting are later maturity steps within this phase.

No monitoring stack, dashboards, SLOs or error-budget automation are claimed as
implemented yet. A future hybrid environment may use the same observability
layer across local and cloud deployment targets.

This would provide one operational view over multiple realizations of the same
Platform Model.

---

## 20. Delivery and Platform Evolution

The current direction is:

```text
completed
Platform Model + Validation
      │
      ▼
completed
Docker Compose + Terraform / RouterOS
      │
      ▼
next
GitHub Actions CI/CD
      │
      ▼
planned
Observability + SRE
      │
      ▼
later
NetBox → AWS → Hybrid
```

The initial CI pipeline will validate models, run tests, generate both backend
artifacts and validate them with their native tooling. Artifact publication is
in scope; automated deployment to the local lab is not. A later CD workflow may
add planning, explicit approval and controlled apply once connectivity, secrets
and state management are designed.

Other backends, including Kubernetes or configuration-management systems, may
be introduced when concrete deployment scenarios justify them.

New backends should reuse the existing Platform Model wherever possible.

A change to the model should represent a genuinely missing domain concept
rather than a requirement imposed by one particular implementation technology.

---

## 21. Project Boundary

The project is fundamentally about this relationship:

```text
Platform Intent
       │
       ▼
Validated Domain Model
       │
       ▼
Deployment / Integration Backends
```

It is not intended to become a wrapper around every infrastructure tool.

The framework should remain small enough that its architecture, mappings and
design decisions remain understandable, testable and demonstrable.

The goal is to show that infrastructure technologies can be treated as
different realizations of a stable logical platform model.
