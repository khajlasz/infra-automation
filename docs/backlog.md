# Backlog

This backlog tracks the evolution of the Infrastructure Automation Framework.
It intentionally separates implemented capabilities, the current milestone and
future ideas.

---

# Completed Foundations

## Architecture and Model

- [x] Define project vision and design principles
- [x] Define Platform Model architecture
- [x] Split model into platform, network, compute and application domains
- [x] Define naming conventions and stable references
- [x] Create telecom reference model
- [x] Create minimal reference model
- [x] Create Out-Dialer reference platform
- [x] Establish modelling guidelines and ADRs

## Loader and Validation

- [x] YAML parser with syntax validation
- [x] Platform Model loader
- [x] Python internal object model
- [x] Shared model-independent Yamale schema
- [x] Schema validation for telecom and Out-Dialer models
- [x] Semantic/reference validation framework
- [x] Validation registry
- [x] Validation CLI

## Observability

- [x] Local Grafana / Prometheus / Loki / Promtail stack
- [x] Framework logging integration
- [x] Grafana datasource and dashboard provisioning

---

# v0.1.0 - First Executable Platform Model

Released.

- [x] Docker Compose generator framework
- [x] Generate services from compute nodes
- [x] Generate image references from deployment metadata
- [x] Generate hostnames
- [x] Generate service network attachments
- [x] Generate published ports from application endpoints
- [x] Generate top-level Docker networks
- [x] Serialize generated Compose specification to YAML
- [x] Add `generate docker-compose` CLI command
- [x] Add generator and CLI tests
- [x] Validate generated artifact with `docker compose config`
- [x] Start modeled application containers during runtime prototype

Runtime validation identified future Docker-model extensions:

- environment variables
- explicit host/container port mappings
- runtime image metadata
- persistent volumes

These are intentionally deferred while the next infrastructure backend is
implemented.

---

# Current Milestone - Routed Local Lab

The local lab is a prerequisite environment used to demonstrate compute and
network automation from the same Platform Model.

Lab construction itself belongs to the separate `dev-environment` project.

## Compute Runtime

- [ ] Keep Ubuntu VM as dedicated Docker host
- [ ] Install and verify Docker on Ubuntu
- [ ] Enable SSH administration from macOS
- [ ] Optionally configure a remote Docker context
- [ ] Copy/generated Compose artifact to the Docker host
- [ ] Run generated Out-Dialer deployment on the VM

## Network Runtime

- [ ] Create MikroTik CHR VM in UTM
- [ ] Establish management connectivity from macOS
- [ ] Define VM NIC topology for management and modeled networks
- [ ] Prove manual routing between required lab segments
- [ ] Prove traffic visibility/firewall enforcement through RouterOS

---

# Next Backend - Terraform / RouterOS

Goal: project the same Platform Model used by Docker Compose into network
infrastructure configuration.

- [ ] Select and validate RouterOS Terraform provider
- [ ] Define minimum Platform Model -> RouterOS mapping
- [ ] Generate routed network / VLAN resources
- [ ] Generate IP addressing
- [ ] Generate routing configuration
- [ ] Generate firewall policy from modeled communication intent
- [ ] Keep deterministic Terraform output
- [ ] Add generator unit tests
- [ ] Add CLI generation path
- [ ] Apply generated configuration to the existing CHR lab router
- [ ] Demonstrate application and network topology from one model

---

# NetBox Integration

NetBox remains in the project vision as inventory and IPAM rather than merely
another deployment generator.

Potential work:

- [ ] Define ownership boundary between Platform Model and NetBox
- [ ] Represent sites, devices/VMs and interfaces
- [ ] Manage prefixes and IP addresses
- [ ] Evaluate generation/population of NetBox inventory from Platform Model
- [ ] Evaluate consuming operational inventory/IPAM data from NetBox
- [ ] Prototype hierarchical context for larger environments
- [ ] Evaluate NetBox Config Context as a reference pattern for inherited and
      device-specific configuration

---

# Future Cloud Backend - AWS

Goal: prove that logical platform intent can be realized by a cloud backend
without redesigning the model.

- [ ] Define a minimum AWS mapping for logical compute and networks
- [ ] Implement Terraform / AWS generator
- [ ] Decide initial compute target (for example EC2, ECS or Kubernetes)
- [ ] Map logical networks to VPC/subnet constructs
- [ ] Map routing intent to AWS route tables
- [ ] Map security intent to appropriate AWS controls
- [ ] Validate the same reference model against local and AWS realizations

---

# Hybrid On-Prem / AWS Scenario

Candidate demonstrations:

- [ ] Routed or VPN connectivity between RouterOS lab and AWS VPC
- [ ] Common observability across local and cloud workloads
- [ ] Common inventory/IPAM
- [ ] Consistent security-policy intent across backends
- [ ] Primary/on-prem and cloud disaster-recovery scenario
- [ ] Workloads distributed across on-prem and AWS

The hybrid scenario should demonstrate shared platform intent rather than merely
showing that two networks can communicate.

---

# Configuration Management

Ansible is not an active milestone for the current Docker-based compute model.

If a future deployment target uses VMs or bare-metal hosts, revisit:

- [ ] Ansible inventory generation
- [ ] host/group variable generation
- [ ] OS configuration
- [ ] application configuration

Configuration management should be added only when a concrete runtime requires
it.

---

# Tooling and Quality

- [ ] GitHub Actions pipeline
- [ ] Public-repository cleanup and documentation consistency
- [ ] Repository secret/history scan before publication
- [ ] Model visualization
- [ ] Documentation site if the project grows enough to justify it
- [ ] Clean-clone validation workflow

---

# Future Deployment Backends

Potential future directions, to be justified by concrete use cases:

- [ ] Kubernetes deployment backend
- [ ] Additional cloud provider
- [ ] VM-based compute realization
- [ ] AI infrastructure reference platform

---

# Open Architectural Questions

- [ ] What is the exact ownership boundary between Platform Model and NetBox?
- [ ] When should IP allocation become an operational/IPAM concern rather than
      static model data?
- [ ] How should hierarchical context be represented when the model grows to
      region / AZ / site / role / device scale?
- [ ] How should one Platform Model select or parameterize multiple deployment
      targets?
- [ ] Which security-policy concepts are generic enough to map cleanly to both
      RouterOS and AWS?
- [ ] Which Docker runtime details should eventually become model concepts and
      which should remain backend-specific configuration?

---

# Design Principles

- The Platform Model is the primary source of truth.
- Every piece of information should have a clear owner.
- Prefer references over duplicated information.
- Keep the logical model provider-independent.
- Structural validation belongs to Yamale.
- Semantic/reference validation belongs to the framework.
- Generators consume the validated model rather than duplicating validation.
- Deployment-specific implementation belongs in backends.
- Introduce new abstractions only when implementation proves they are needed.
