# Infrastructure Automation Framework

[![wakatime](https://wakatime.com/badge/user/a1ce8987-7edd-4c00-a0e9-f9b15cd05d24/project/1d9c846a-d8fb-4d80-8588-66fbc7b9f06a.svg)](https://wakatime.com/badge/user/a1ce8987-7edd-4c00-a0e9-f9b15cd05d24/project/1d9c846a-d8fb-4d80-8588-66fbc7b9f06a)

A declarative, model-driven framework for describing distributed
platforms once and generating deployment-specific artifacts from the
same validated Platform Model.

The project separates **platform intent** from **implementation
technology**.

Instead of maintaining independent definitions for Docker, Terraform,
cloud platforms and network devices, the platform is described once and
projected into target-specific artifacts.

``` text
                 Platform Model
                        │
             Validation & Normalisation
                        │
                 Deployment Realization
                        │
             ┌──────────┴──────────┐
             │                     │
             ▼                     ▼
      Docker Compose       Terraform / RouterOS
             │                     │
             ▼                     ▼
       Applications          Network Infrastructure
```

The Platform Model is the **single source of truth**.

See `docs/architecture.md` for the detailed architecture, model
boundaries and design rationale.

------------------------------------------------------------------------

## Why

Infrastructure automation often grows around individual tools.

Terraform, Docker Compose, Kubernetes, cloud platforms and network
devices each introduce their own configuration models. This can result
in the same nodes, networks, interfaces, endpoints and policies being
described several times.

This project takes the opposite approach:

1.  Define the logical platform.
2.  Validate the model.
3.  Bind it to a deployment realization.
4.  Generate deployment-specific artifacts.
5.  Validate and operate the resulting platform.

Deployment technology becomes an implementation of the model rather than
the source of truth.

------------------------------------------------------------------------

## Reference Platform

The primary reference implementation is **Out-Dialer**, a simplified
distributed Voice Campaign Platform inspired by enterprise telecom
systems.

It currently contains four logical compute nodes:

-   Portal
-   Campaign Manager
-   Call Simulator
-   PostgreSQL

The application workload uses three logical security zones:

-   DMZ
-   Internal
-   Database

The model also defines an **Observability** network. It represents an
external supporting network from which the platform can be observed. The
observability stack itself is not an Out-Dialer workload and is not
deployed by the Out-Dialer Docker realization.

The repository also contains:

-   `models/minimal` --- deliberately small model used for framework
    tests.
-   `models/telecom` --- earlier telecom-oriented reference model used
    during model development.

See `docs/architecture.md` for the reference platform topology and
modelling details.

------------------------------------------------------------------------

## Current Capabilities

### Platform Model and Validation

-   declarative YAML model
-   schema validation
-   semantic/reference validation
-   Python object model and loader
-   logical compute, application and network relationships
-   external platform interfaces describing externally consumed
    application endpoints
-   semantic validation of model and realization references

### Deployment Realization

A deployment realization binds provider-independent model intent to a
concrete environment.

The current local-lab realization defines:

-   named Docker hosts
-   compute-node placement on Docker hosts
-   Docker network driver, parent interfaces and IPAM configuration
-   logical-to-physical RouterOS interface mappings

Placement remains outside the Platform Model because it is a property of
a specific deployment.

### Docker Compose Backend

The Docker Compose generator derives:

-   services from compute nodes
-   image references from deployment metadata
-   hostnames from node names
-   service network attachments from node interfaces
-   published ports from application endpoints
-   top-level Docker networks
-   one Compose specification per Docker host containing assigned
    compute nodes

Generation is available through the CLI:

``` bash
python src/cli.py generate docker-compose \
  models/out-dialer \
  --realization realizations/out-dialer/local-lab.yaml \
  --output docker-compose.yaml
```

The `--output` path is a base artifact name. For the current `local-lab`
realization this produces:

``` text
docker-compose.workload.yaml
```

The generated artifact has been validated with Docker Compose and used
to run the modeled workload in the local reference lab.

### Terraform / RouterOS Backend

The RouterOS backend generates Terraform configuration from the Platform
Model and deployment realization. It currently derives:

-   physical RouterOS interface mappings from the realization
-   gateway addresses from modeled network CIDRs
-   firewall address-list entries for modeled networks
-   firewall filter rules from modeled communication policies
-   externally required access rules from modeled external interfaces
-   baseline connection-state handling
-   a terminal inter-zone deny rule

Generated external-access rules are inserted before the terminal deny
rule so that modeled access remains reachable without weakening the
default-deny policy.

The generated configuration has been applied and validated against the
local MikroTik CHR lab. The backend configures existing RouterOS
infrastructure; it does not provision the CHR virtual machine itself.

### Continuous Integration and Local-Lab Delivery

Pull Request CI is implemented with GitHub Actions.

For relevant changes it:

-   installs the project and development dependencies
-   runs the complete Python test suite
-   validates the Out-Dialer model
-   generates host-specific Docker Compose artifacts
-   validates generated Compose with `docker compose config`
-   generates RouterOS Terraform
-   initializes and validates Terraform
-   checks that the tracked generated RouterOS artifact is reproducible
-   publishes generated infrastructure artifacts for inspection

CI intentionally has no credentials or network access capable of
modifying the local reference lab.

### Observability / SRE

The project has entered its Observability/SRE phase.

The current lab contains an external supporting observability stack
using:

-   Prometheus
-   Grafana
-   Loki
-   Promtail

Out-Dialer applications expose Prometheus metrics. The Platform Model
describes the external metrics interface and the RouterOS backend
derives the firewall access required for the observability network to
reach those endpoints.

The routed metrics path has been validated end to end:

``` text
Prometheus
10.10.40.0/24 Observability
        │
        ▼
   MikroTik CHR
        │
        ▼
10.10.20.0/24 Internal
        │
        ├── Portal :9090
        ├── Campaign Manager :9090
        └── Call Simulator :9090
```

Prometheus successfully scrapes all three application targets through
the RouterOS-controlled path.

The first provisioned Out-Dialer Grafana dashboard is stored as code in:

``` text
observability/grafana/dashboards/out-dialer.json
```

It currently contains Call Simulator panels for:

-   calls per minute
-   call failure rate
-   mean call duration
-   p95 call duration

The next observability milestone is persistent storage for Grafana,
Prometheus and Loki before expanding the dashboards and moving toward
SLIs/SLOs.

------------------------------------------------------------------------

## CLI

### Validate a model

``` bash
python src/cli.py validate models/out-dialer
```

### Generate Docker Compose

``` bash
python src/cli.py generate docker-compose \
  models/out-dialer \
  --realization realizations/out-dialer/local-lab.yaml \
  --output docker-compose.yaml
```

### Generate RouterOS Terraform

``` bash
python src/cli.py generate terraform-routeros \
  models/out-dialer \
  --realization realizations/out-dialer/local-lab.yaml \
  --output lab/terraform/routeros/generated.tf
```

### Validate generated Docker Compose

``` bash
docker compose -f docker-compose.workload.yaml config
```

------------------------------------------------------------------------

## Local Demonstration Lab

The framework assumes that target infrastructure already exists.

The reference lab therefore treats VM and runtime provisioning as
prerequisites rather than responsibilities of the framework.

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

The workload Ubuntu VM represents the application runtime.

MikroTik CHR represents routed network and firewall infrastructure.

The observability Ubuntu VM hosts the supporting monitoring stack.

The macOS workstation acts as the automation control plane.

Lab construction and workstation configuration belong to the separate
`dev-environment` project.

------------------------------------------------------------------------

## Roadmap

### Completed

-   Platform Model, schema validation and semantic/reference validation
-   Python loader and internal domain model
-   Docker Compose generation and local runtime validation
-   deployment realization loading
-   named Docker hosts and compute-node placement
-   host-aware Docker Compose generation
-   Docker macvlan network/IPAM realization
-   Terraform / RouterOS generation
-   RouterOS validation against the local CHR lab
-   Pull Request CI for test, generation and artifact validation
-   external observability interface modelling
-   RouterOS realization of observability access
-   end-to-end Prometheus scraping through the routed lab
-   first provisioned Out-Dialer Grafana dashboard

### Current: Observability and SRE

-   persist Prometheus, Grafana and Loki runtime data
-   expand application dashboards
-   replace Promtail with Grafana Alloy when appropriate
-   introduce additional infrastructure telemetry, including RouterOS
-   define SLIs from established signals
-   define SLOs and error budgets after the corresponding signals are
    reliable
-   add tracing with OpenTelemetry and Tempo
-   correlate metrics, logs and traces

### Planned: Controlled Local-Lab Deployment

The current CI validates proposed changes but does not deploy them.

A later delivery milestone may introduce a trusted deployment workflow
for the existing local lab:

-   trigger deployment only from trusted `main`
-   regenerate artifacts from the exact merged revision
-   run `terraform plan`
-   require approval before infrastructure modification
-   apply RouterOS configuration
-   deploy application runtime
-   run post-deployment smoke tests

### Later Exploration

-   NetBox inventory and IPAM integration
-   Terraform / AWS realization
-   hybrid on-prem/cloud deployment and shared observability
-   hierarchical infrastructure context for larger environments
-   Kubernetes as an alternative application runtime

------------------------------------------------------------------------

## Repository Structure

``` text
adr/
docker/
docs/
models/
observability/
realizations/
schema/
src/
├── cli.py
├── generators/
├── loader/
├── model/
├── observability/
└── validation/
lab/
└── terraform/
tests/
```

------------------------------------------------------------------------

## Status

``` text
Platform Model                         implemented
Schema validation                      implemented
Semantic/reference validation          implemented
Python loader                          implemented
Validation CLI                         implemented
Out-Dialer reference model             implemented
Deployment realization                 implemented
Host-aware Docker Compose generation   implemented
Docker runtime validation              implemented
Terraform / RouterOS generation        implemented
RouterOS CHR runtime validation        implemented
Pull Request CI                        implemented
Local-lab self-hosted runner            implemented
Local-lab Terraform plan workflow       implemented
Automated Terraform apply/deployment    planned
External observability connectivity    implemented
Prometheus application scraping        implemented
Out-Dialer Grafana dashboard           initial implementation
Observability persistence              next milestone
SLIs / SLOs / error budgets            planned
NetBox integration                     future
AWS backend                            future
Hybrid deployment                      future
Kubernetes backend                     future
```

------------------------------------------------------------------------

## Architecture

For detailed information about model boundaries, realization
responsibilities, generator mappings, the local reference lab,
observability ownership and delivery trust boundaries, see
`docs/architecture.md`.

------------------------------------------------------------------------

## Project Status

This project is under active development.

Docker Compose and Terraform / RouterOS provide two executable
projections of the same validated Platform Model and local-lab
realization.

The current development focus is Observability/SRE: making the reference
platform observable through real telemetry paths and then using those
signals to develop operational practices such as dashboards, SLIs, SLOs
and error budgets.
