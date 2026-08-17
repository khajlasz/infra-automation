# Infrastructure Automation Framework

A declarative, model-driven framework for describing distributed platforms once
and generating deployment-specific artifacts from the same validated Platform
Model.

The project separates **platform intent** from **implementation technology**.

Instead of maintaining independent definitions for Docker, Terraform, cloud
platforms and network devices, the platform is described once and projected
into target-specific artifacts.

```text
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

See [docs/architecture.md](docs/architecture.md) for the detailed architecture,
model boundaries and design rationale.

---

## Why

Infrastructure automation often grows around individual tools.

Terraform, Docker Compose, Kubernetes, cloud platforms and network devices each
introduce their own configuration models. This can result in the same nodes,
networks, interfaces, endpoints and policies being described several times.

This project takes the opposite approach:

1. Define the logical platform.
2. Validate the model.
3. Generate deployment-specific artifacts.

Deployment technology becomes an implementation of the model rather than the
source of truth.

---

## Reference Platform

The primary reference implementation is **Out-Dialer**, a simplified distributed
Voice Campaign Platform inspired by enterprise telecom systems.

It currently contains four logical compute nodes:

- Portal
- Campaign Manager
- Call Simulator
- PostgreSQL

and three logical network zones:

- DMZ
- Internal
- Database

The repository also contains:

- `models/minimal` — deliberately small model used for framework tests.
- `models/telecom` — earlier telecom-oriented reference model used during model
  development.

See [docs/architecture.md](docs/architecture.md) for the reference platform
topology and modelling details.

---

## Current Capabilities

### Platform Model

- declarative YAML model
- schema validation
- semantic/reference validation
- Python object model and loader
- logical compute, application and network relationships

### Docker Compose Backend

The first executable deployment backend is available in **v0.1.0**.

The generator currently derives:

- services from compute nodes
- image references from deployment metadata
- hostnames from node names
- service network attachments from node interfaces
- published ports from application endpoints
- top-level Docker networks

Generated specifications are serialized to YAML and can be produced through
the CLI.

```bash
PYTHONPATH=src .venv/bin/python src/cli.py \
    generate docker-compose \
    models/out-dialer \
    --realization realizations/out-dialer/local-lab.yaml \
    --output docker-compose.yaml
```

The generated artifact has been validated with Docker Compose and used to
create the modeled network topology and start application containers.

When a deployment realization is supplied, the generator also resolves the
local-lab macvlan driver, parent interfaces and IPAM subnets. Model-only
generation remains available for simpler use cases.

### Terraform / RouterOS Backend

The RouterOS backend generates Terraform configuration from the Platform Model
and a deployment realization. It currently derives:

- physical RouterOS interface mappings from the realization
- gateway addresses from modeled network CIDRs
- firewall address-list entries for modeled networks
- firewall filter rules from modeled communication policies
- baseline connection-state handling and a final inter-zone deny rule

The generated configuration has been tested against the local MikroTik CHR
lab. The backend configures existing RouterOS infrastructure; it does not
provision the CHR virtual machine itself.

---

## CLI

Validate a model:

```bash
PYTHONPATH=src .venv/bin/python src/cli.py \
    validate models/out-dialer
```

Generate Docker Compose:

```bash
PYTHONPATH=src .venv/bin/python src/cli.py \
    generate docker-compose \
    models/out-dialer \
    --realization realizations/out-dialer/local-lab.yaml \
    --output docker-compose.yaml
```

The `--realization` option is optional for Docker Compose generation.

Generate RouterOS Terraform:

```bash
PYTHONPATH=src .venv/bin/python src/cli.py \
    generate terraform-routeros \
    models/out-dialer \
    --realization realizations/out-dialer/local-lab.yaml \
    --output generated.tf
```

Validate the generated artifact:

```bash
docker compose -f docker-compose.yaml config
```

---

## Local Demonstration Lab

The framework assumes that target infrastructure already exists.

The reference lab therefore treats VM and runtime provisioning as prerequisites
rather than responsibilities of the framework.

```text
                    macOS
                      │
                     UTM
                      │
          ┌───────────┴───────────┐
          │                       │
          ▼                       ▼
 Ubuntu Docker Host          MikroTik CHR
          │                       │
          └──── Network Fabric ───┘
```

The Ubuntu VM represents the compute/runtime platform.

MikroTik CHR represents routed network and firewall infrastructure.

The macOS workstation acts as the automation control plane.

Lab construction and workstation configuration belong to the separate
`dev-environment` project.

---

## Next Milestone: CI/CD

The next phase is a basic GitHub Actions pipeline that validates both source
intent and generated artifacts. The intended initial scope is:

- install the Python dependencies
- validate model schemas and references
- run the test suite
- generate Docker Compose and RouterOS Terraform artifacts
- run `docker compose config`
- run `terraform fmt -check` and `terraform validate`
- publish generated artifacts for inspection

Controlled deployment is deliberately a later step. Planning or applying to
the local lab requires decisions about secrets, connectivity, state and
approval gates that are outside the initial CI scope.

---

## Roadmap

### Completed

- Platform Model, schema validation and semantic/reference validation
- Python loader and internal domain model
- Docker Compose generation and local runtime validation
- deployment realization loading and network/IPAM resolution
- Terraform / RouterOS generation and validation against the local CHR lab
- CLI commands for validation and both generation backends

### Next: CI/CD

- GitHub Actions validation and test workflow
- generation and validation of Docker Compose and RouterOS Terraform artifacts
- publication of generated artifacts
- later, a controlled plan/apply workflow

### Planned: Observability and SRE

- Prometheus metrics for Ubuntu nodes, containers and RouterOS
- Loki-based application and infrastructure log aggregation
- Grafana dashboards correlating platform, network and application signals
- synthetic network-policy probes for expected allowed and denied flows
- SLIs and SLOs for service availability, latency, allowed-flow availability
  and forbidden-flow enforcement
- error budgets and, later, burn-rate alerting

The synthetic probes are intended to compare runtime behavior with modeled
security intent. Representative checks include DMZ to Internal and Internal to
Database as expected allowed flows, and DMZ to Database as an expected denied
flow.

### Later Exploration

- NetBox inventory and IPAM integration
- Terraform / AWS realization
- hybrid on-prem/cloud deployment and shared observability
- hierarchical infrastructure context for larger environments
- Kubernetes as an alternative application runtime

Conceptually:

```text
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

The architectural goal is that adding a deployment backend should not require
redesigning the logical platform.

---

## Repository Structure

```text
adr/
docker/
docs/
models/
observability/
schema/
src/
├── cli.py
├── generators/
├── loader/
├── model/
├── observability/
└── validation/
tests/
```

---

## Status

| Area | Status |
|---|---|
| Platform Model | ✅ |
| Schema validation | ✅ |
| Semantic/reference validation | ✅ |
| Python loader | ✅ |
| Validation CLI | ✅ |
| Out-Dialer reference model | ✅ |
| Docker Compose generator | ✅ v0.1.0 |
| Docker Compose CLI generation | ✅ v0.1.0 |
| Docker runtime validation | ✅ Initial validation |
| Deployment realization | ✅ Local lab |
| Local routed lab | ✅ Initial validation |
| Terraform / RouterOS generator | ✅ Initial implementation |
| Terraform / RouterOS CLI generation | ✅ |
| RouterOS CHR validation | ✅ Initial validation |
| CI/CD pipeline | Next phase |
| Observability / SRE | Planned |
| NetBox inventory/IPAM integration | Future |
| AWS backend | Future |
| Hybrid deployment scenario | Future |
| Kubernetes backend | Future |

---

## Architecture

For detailed information about:

- model boundaries
- reference platform topology
- generator responsibilities
- Docker Compose mapping
- local lab architecture
- Terraform / RouterOS direction
- NetBox and hierarchical infrastructure modelling
- cloud and hybrid evolution

see **[Architecture](docs/architecture.md)**.

---

## Project Status

This project is under active development.

Docker Compose and Terraform / RouterOS now provide two executable projections
of the same Platform Model and local-lab realization.

Current development is focused on CI/CD. Observability and SRE are the next
planned platform phase after that foundation is in place.
