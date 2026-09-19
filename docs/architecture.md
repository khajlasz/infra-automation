# Architecture

## 1. Purpose

The Infrastructure Automation Framework uses a declarative **Platform
Model** as the primary source of truth for distributed platform
topology.

The model describes **what the platform is** rather than how a
particular deployment technology realizes it.

Deployment-specific generators translate the validated model and a
deployment realization into concrete artifacts such as Docker Compose or
Terraform.

The central architectural principle is:

> Platform intent belongs in the model. Deployment implementation
> belongs in realizations and generators.

------------------------------------------------------------------------

## 2. Architecture Overview

``` text
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
       Application Runtime          Network Infrastructure
```

Generators consume validated inputs. They do not independently parse the
YAML source and should not duplicate validation responsibilities.

A deployment realization supplies environment-specific bindings that do
not belong in the provider-independent Platform Model.

The current local-lab realization maps:

-   compute nodes to named Docker hosts;
-   logical networks to Docker parent interfaces and IPAM ranges;
-   logical networks to physical RouterOS interfaces.

------------------------------------------------------------------------

## 3. Design Principles

The framework is:

-   declarative
-   provider independent
-   deployment independent
-   normalized
-   reference based
-   validated before generation
-   human readable
-   generator friendly
-   incremental rather than over-generalized

Each object should have a single owner.

Relationships should be expressed through references rather than
duplicated values.

New abstractions should be introduced when concrete deployment targets
justify them rather than in anticipation of hypothetical requirements.

------------------------------------------------------------------------

## 4. Model Boundaries

The Platform Model describes logical platform intent.

Examples include:

-   compute nodes
-   applications
-   deployments
-   application endpoints
-   logical networks
-   interfaces
-   network devices
-   communication policies
-   sites
-   external platform interfaces

The Platform Model should not directly describe technology-specific
implementations such as:

-   Docker network syntax
-   Docker host interface names
-   Kubernetes Services
-   AWS subnets
-   RouterOS resource syntax
-   physical RouterOS interface identifiers

Those concepts belong to deployment realizations and backends.

``` text
                 Logical Network
                       │
          ┌────────────┼────────────┐
          │            │            │
          ▼            ▼            ▼
    Docker Network  RouterOS     AWS Subnet
                    Network
```

The logical object remains stable while its realization changes.

------------------------------------------------------------------------

## 5. Reference Platform: Out-Dialer

The primary reference platform is **Out-Dialer**, a simplified
distributed Voice Campaign Platform.

It contains four logical compute nodes:

``` text
portal
campaign
call_simulator
database
```

The application components are Portal, Campaign Manager and Call
Simulator. PostgreSQL provides persistent application storage.

The reference workload is intentionally synthetic. Its purpose is to
provide a small distributed system against which infrastructure
automation and SRE concepts can be implemented and observed.

------------------------------------------------------------------------

## 6. Logical Communication

``` text
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

The model describes logical communication rather than Docker-, RouterOS-
or Kubernetes-specific objects.

------------------------------------------------------------------------

## 7. Logical Compute Model

A node represents a logical compute resource.

A node does not inherently mean:

-   Docker container
-   virtual machine
-   EC2 instance
-   Kubernetes Pod

Those are deployment decisions.

A deployment backend maps a logical node into the appropriate runtime
resource.

Host placement is likewise deployment-specific. The Platform Model does
not state that `portal`, `campaign`, `call_simulator` or `database`
belongs on a particular Docker host. The deployment realization owns
that decision.

------------------------------------------------------------------------

## 8. Logical Network Model

The application workload uses three logical security zones:

``` text
DMZ
Internal
Database
```

Nodes connect to them through modeled interfaces:

``` text
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

The model also contains an **Observability** network.

Observability differs from the application zones: it represents an
external supporting network from which telemetry consumers can reach
modeled application endpoints.

``` text
Observability
     │
     ▼
  RouterOS
     │
     ▼
 Internal
     │
     ├── Portal metrics
     ├── Campaign Manager metrics
     └── Call Simulator metrics
```

The observability stack itself is not an Out-Dialer compute node or
deployment.

------------------------------------------------------------------------

## 9. Application Endpoints and External Interfaces

Applications define logical endpoints describing capabilities such as
protocol, port and service purpose.

Examples include:

-   HTTPS
-   REST
-   SQL
-   Prometheus metrics

An endpoint represents application intent and may drive several
implementation artifacts.

External platform interfaces describe which application endpoints are
intended to be consumed from outside the application platform boundary.

For Out-Dialer, the `metrics` external interface currently declares:

-   source network: `observability`
-   Portal `metrics` endpoint on `internal`
-   Campaign Manager `metrics` endpoint on `internal`
-   Call Simulator `metrics` endpoint on `internal`

This distinction is important:

> The Platform Model describes how the platform can be observed; it does
> not model the external observability platform as an Out-Dialer
> workload.

The RouterOS generator can therefore derive the access required for a
metrics consumer without making Prometheus part of the application
model.

------------------------------------------------------------------------

## 10. Deployment Realization

A deployment realization binds logical model objects to a specific
environment.

The current `local-lab` realization defines a named Docker host:

``` text
workload
```

and assigns the four Out-Dialer compute nodes to it.

It also defines Docker macvlan realization data:

``` text
logical network → Linux parent interface
logical network → IPAM offset/prefix
```

and RouterOS realization data:

``` text
logical network → physical RouterOS interface
```

This separation prevents environment-specific details from leaking into
the logical Platform Model.

The structure supports multiple Docker hosts without requiring host
placement to become platform intent.

------------------------------------------------------------------------

## 11. Docker Compose Backend

The Docker Compose backend projects the validated model and realization
into host-specific Compose specifications.

``` text
Platform Model + Realization
            │
            ▼
Docker Compose Generator
            │
            ▼
one Compose specification per Docker host
```

Current mappings include:

``` text
compute node       → service
deployment         → image
node name          → hostname
node interfaces    → service networks
application ports  → published ports
logical networks   → top-level Compose networks
realization host   → output Compose artifact
```

For the current local-lab realization:

``` text
docker-compose.yaml
        │ base output name
        ▼
docker-compose.workload.yaml
```

The generated artifact has been validated with native Docker Compose
tooling and used to run the reference workload.

------------------------------------------------------------------------

## 12. Local Reference Lab

The framework consumes an existing lab rather than provisioning every VM
and development dependency.

``` text
                         macOS
                           │
                          UTM
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
 Ubuntu Workload       MikroTik CHR    Ubuntu Observability
      Host                  │                Host
          │                 │                 │
          └──────── Routed Network Fabric ────┘
```

Responsibilities are separated as follows:

-   macOS: automation control plane and development workstation
-   workload VM: Docker application runtime
-   MikroTik CHR: routed network and firewall policy
-   observability VM: Prometheus/Grafana/Loki supporting stack

VM creation, UTM configuration and workstation setup are prerequisites
and belong to the separate `dev-environment` project.

------------------------------------------------------------------------

## 13. Terraform / RouterOS Backend

The Terraform / RouterOS backend is the second implemented deployment
backend.

Its purpose is to prove that the same Platform Model driving application
deployment can also drive network infrastructure.

Current mappings include:

``` text
logical networks        → RouterOS Ethernet interfaces
realization mappings    → physical interface factory names
network CIDRs           → gateway IP addresses
logical networks        → firewall address-list entries
communication policies  → firewall filter rules
external interfaces     → external-access firewall rules
```

The generator also adds baseline rules for established/related traffic
and invalid connection state, followed by a terminal default deny for
other inter-zone traffic.

Rules generated from external interfaces are explicitly placed before
the terminal deny rule.

The generated Terraform has been formatted, validated and applied
against the existing MikroTik CHR local lab.

The backend configures existing RouterOS infrastructure; it does not
provision the CHR VM itself.

------------------------------------------------------------------------

## 14. Semantic Validation

Semantic validation is separated from YAML schema validation.

Current model-reference rules validate:

-   node → site
-   node interface → network
-   deployment → application
-   external target → application
-   external target → application endpoint
-   external interface → source network
-   external target → network

Realization-reference rules validate:

-   Docker host → compute node
-   compute node assigned to at most one Docker host

The authoritative rule definitions are maintained in
`docs/semantic-validation-registry.md`.

A completeness rule requiring every model node to be assigned to a
Docker host is intentionally not part of the current implementation.

------------------------------------------------------------------------

## 15. Configuration Management

Ansible is not currently an active backend because the reference compute
implementation uses containers.

If a future deployment target maps logical compute nodes to virtual
machines or bare-metal hosts, configuration management may become
appropriate.

A backend should be introduced because a concrete deployment target
requires it, not simply because the technology is available.

------------------------------------------------------------------------

## 16. NetBox and Future Infrastructure Context

NetBox remains a future inventory and IPAM integration rather than
simply another deployment generator.

Potential responsibilities include:

-   sites
-   devices and VMs
-   interfaces
-   prefixes
-   IP addresses
-   topology metadata
-   hierarchical configuration context

The ownership boundary between Platform Model intent and NetBox
operational inventory should be decided through concrete use cases.

Likewise, hierarchical context and inheritance should be introduced only
when a larger-scale use case requires them.

------------------------------------------------------------------------

## 17. Future Deployment Backends

AWS and Kubernetes remain future exploration areas.

The architectural test for a new backend is whether the logical Platform
Model can remain stable while the deployment realization changes.

Conceptually:

``` text
                         Platform Model
                                │
             ┌──────────────────┼──────────────────┐
             │                  │                  │
             ▼                  ▼                  ▼
      Docker Compose      Terraform/RouterOS   Terraform/AWS
             │                  │                  │
             ▼                  ▼                  ▼
       Local Compute       On-Prem Network         AWS
```

------------------------------------------------------------------------

## 18. Continuous Integration and Delivery Boundary

Pull Request CI is implemented with GitHub Actions.

The CI trust boundary is:

``` text
Feature Branch
      │
      ▼
Pull Request
      │
      ▼
GitHub Actions CI
      │
      ├── tests
      ├── model validation
      ├── Docker Compose generation + validation
      ├── RouterOS Terraform generation + validation
      ├── generated-artifact reproducibility check
      └── artifact publication
      │
      ▼
Human Review
      │
      ▼
Merge to main
```

CI validates proposed changes but does not receive credentials or
connectivity allowing it to modify the local lab.

A future controlled deployment workflow may operate from trusted `main`
using a self-hosted runner with lab connectivity.

Generated deployment artifacts remain projections of authoritative
inputs, not independent sources of truth.

Where a generated artifact is intentionally tracked in Git, CI may
additionally regenerate it and use `git diff --exit-code` to prove that
the committed copy is current.

------------------------------------------------------------------------

## 19. Observability

Observability is now an active implementation phase rather than only a
future roadmap item.

The current signal path is:

``` text
Out-Dialer Applications
        │
        │ Prometheus metrics
        ▼
     RouterOS
        │
        ▼
    Prometheus
        │
        ▼
      Grafana
```

The local observability host also runs Loki and Promtail for logs.

### Current implementation

The application components expose real Prometheus metrics.

The Out-Dialer model declares the external metrics interface. RouterOS
generation realizes the firewall access required from the
`observability` network to the application metrics endpoints on
`internal`.

The resulting routed path has been validated end to end. Prometheus
successfully scrapes:

``` text
Portal            :9090
Campaign Manager  :9090
Call Simulator    :9090
```

through RouterOS.

The first provisioned Out-Dialer Grafana dashboard is version controlled
in:

``` text
observability/grafana/dashboards/out-dialer.json
```

Its initial Call Simulator view includes:

-   calls per minute
-   call failure rate
-   mean call duration
-   p95 call duration

### Ownership

The observability stack is supporting infrastructure, not part of the
Out-Dialer application model.

Configuration and reproducible dashboard definitions may be version
controlled. Operational state is different:

``` text
Grafana database/state   runtime data
Prometheus TSDB          runtime data
Loki chunks/index        runtime data
```

These are not Platform Model source data and should not become
Git-managed configuration.

### Next observability milestone

The next step is to add persistent storage for the observability
services so that container recreation does not discard useful history or
Grafana runtime state.

After persistence, the project can expand application and infrastructure
telemetry and move toward:

``` text
signals
  → dashboards
  → SLIs
  → SLOs
  → error budgets
  → alerting
```

OpenTelemetry/Tempo tracing and metrics/logs/traces correlation are
later maturity steps.

No SLO or error-budget automation is claimed as implemented yet.

------------------------------------------------------------------------

## 20. Project Evolution

The current evolution is:

``` text
completed
Platform Model + Validation
      │
      ▼
completed
Docker Compose + Terraform / RouterOS
      │
      ▼
completed
Pull Request CI
      │
      ▼
completed foundation
Trusted local-lab workflow
(self-hosted runner + Terraform plan)
      │
      ▼
current
Observability / SRE
      │
      ▼
next within observability
Persistent telemetry storage
      │
      ▼
later
SLIs / SLOs / tracing / richer infrastructure telemetry
      │
      ▼
later delivery extension
Controlled Terraform apply / workload deployment / smoke tests
      │
      ▼
later exploration
NetBox / AWS / Hybrid / Kubernetes
```

The sequencing is deliberately incremental. Each new capability should
be driven by a concrete operational or deployment requirement.

------------------------------------------------------------------------

## 21. Project Boundary

The project is fundamentally about this relationship:

``` text
Platform Intent
       │
       ▼
Validated Domain Model
       │
       ▼
Deployment Realization
       │
       ▼
Deployment / Integration Backends
```

It is not intended to become a wrapper around every infrastructure tool.

The framework should remain small enough that its architecture, mappings
and design decisions remain understandable, testable and demonstrable.

The goal is to show that infrastructure technologies can be treated as
different realizations of a stable logical platform model, and that the
resulting platform can be operated and observed using real SRE
practices.
