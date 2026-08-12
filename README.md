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
             ┌──────────┴──────────┐
             │                     │
             ▼                     ▼
      Docker Compose          Terraform
             │                     │
             ▼                     ▼
       Applications          Infrastructure
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
    --output docker-compose.yaml
```

The generated artifact has been validated with Docker Compose and used to
create the modeled network topology and start application containers.

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
    --output docker-compose.yaml
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

## Next Milestone

The next major backend will generate **Terraform configuration for MikroTik
RouterOS** from the same Platform Model that already generates Docker Compose.

```text
                   Platform Model
                          │
             ┌────────────┴────────────┐
             │                         │
             ▼                         ▼
      Docker Compose              Terraform
             │                         │
             ▼                         ▼
       Docker Host              MikroTik CHR
```

The objective is to demonstrate application deployment and network
infrastructure automation from one source of truth.

---

## Future Direction

The longer-term direction is multiple realizations of the same logical
Platform Model.

Planned areas of exploration include:

- AWS as a cloud deployment backend
- hybrid on-prem/cloud deployment
- shared observability across deployment targets
- NetBox integration for inventory and IPAM
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
| Local routed lab | 🚧 In progress |
| Terraform / RouterOS backend | Planned |
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

The Docker Compose backend provides the first executable end-to-end projection
of the Platform Model.

Current development is focused on establishing the routed local lab and
implementing the first Terraform network backend using MikroTik RouterOS.
