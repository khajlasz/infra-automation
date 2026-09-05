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

# Completed - Routed Local Lab

- [x] Ubuntu Docker host
- [x] MikroTik CHR router/firewall
- [x] Three modeled network zones
- [x] Inter-zone routing
- [x] Firewall policy enforcement
- [x] Runtime connectivity validation


# Completed - Terraform / RouterOS Backend

- [x] RouterOS Terraform provider
- [x] Model -> RouterOS generator
- [x] Interface realization
- [x] Gateway addressing
- [x] Address lists
- [x] Firewall policy generation
- [x] Generator tests
- [x] CLI generation
- [x] Existing CHR resources imported into Terraform state
- [x] Persistent local backend outside disposable runner checkout


# Completed - CI/CD v0.1

- [x] GitHub-hosted PR validation
- [x] Python tests
- [x] Platform Model validation
- [x] Docker Compose generation and native validation
- [x] RouterOS Terraform generation and native validation
- [x] Generated infrastructure artifacts
- [x] Self-hosted macOS local-lab runner
- [x] Post-merge local deployment workflow
- [x] Generate Terraform from merged Platform Model
- [x] Persistent Terraform state available to self-hosted runner
- [x] Refresh real RouterOS resources from CI/CD workflow
- [x] Automated `terraform plan` against CHR

Deferred intentionally:
- automatic `terraform apply`
- Docker deployment from CD
- deployment approval/gating

CD v0.1 intentionally stops at automated planning against the real
lab. Apply remains controlled/manual until further deployment automation
provides enough value to justify the additional security and lifecycle work.

---

# Current Milestone - Observability / SRE

## OBS-1 - Operational Health Model

- [ ] Define what "healthy" means for the local platform
- [ ] Define host health expectations
- [ ] Define application health expectations
- [ ] Define network-policy expectations
- [ ] Define RouterOS health expectations
- [ ] Classify checks as deployment smoke, continuous synthetic monitoring,
      and/or future Kubernetes probes

Health expectations should be defined conceptually once. Deployment smoke
tests, continuous synthetic monitoring and future Kubernetes probes are
different mechanisms, but should not evolve into unrelated definitions of
platform health.


## OBS-2A - Ansible Host Configuration

Use the observability milestone as the first concrete requirement for
configuration management.

- [ ] Add Ansible project structure
- [ ] Define Ubuntu lab host inventory
- [ ] Create base host configuration role
- [ ] Manage observability prerequisites
- [ ] Manage Node Exporter installation/configuration
- [ ] Demonstrate idempotent second run

Future: evaluate generated Ansible inventory/variables from the Platform Model.


## OBS-2B - Metrics Foundation

- [ ] Deploy/configure Prometheus
- [ ] Collect Ubuntu Node Exporter metrics
- [ ] Verify CPU, memory, disk and network telemetry
- [ ] Define useful infrastructure recording/query patterns


## OBS-2C - RouterOS Metrics

- [ ] Export RouterOS operational metrics
- [ ] Collect interface status/traffic
- [ ] Collect resource utilization
- [ ] Evaluate firewall-rule counters as observability signals


## OBS-3 - Synthetic Application and Network Checks

Initial expectations:

- [ ] Portal responds
- [ ] Campaign Manager responds
- [ ] DMZ -> Internal succeeds
- [ ] Internal -> Database succeeds
- [ ] DMZ -> Database remains blocked
- [ ] CHR is reachable

- [ ] Make appropriate checks reusable as post-deployment smoke tests
- [ ] Execute checks continuously
- [ ] Export results as Prometheus metrics
- [ ] Preserve possibility of deriving network-policy expectations from
      Platform Model policy definitions later


## OBS-4 - Logging

- [ ] Integrate application/container logs with Loki
- [ ] Integrate relevant host/system logs
- [ ] Correlate failures observed in metrics/probes with logs


## OBS-5 - Grafana Operational Dashboard

Create a Local Lab Overview showing:

- [ ] platform component availability
- [ ] application availability
- [ ] expected network-policy behavior
- [ ] host resource utilization
- [ ] network traffic
- [ ] RouterOS/firewall signals


## OBS-6 - SLI / SLO / Error Budget

- [ ] Define initial availability SLIs from measured signals
- [ ] Define application availability SLO
- [ ] Evaluate network-policy correctness as an SLI
- [ ] Introduce error-budget calculation
- [ ] Document SRE interpretation rather than only dashboard metrics


## OBS-7 - Distributed Tracing

Tracing follows metrics, synthetic monitoring and logs.

- [ ] Introduce OpenTelemetry
- [ ] Instrument suitable application request paths
- [ ] Select tracing backend (for example Tempo)
- [ ] Correlate traces with metrics/logs in Grafana
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

# Configuration Management - Ansible

Ansible becomes an active part of the project during the Observability / SRE
milestone.

Its primary responsibility is host configuration rather than infrastructure
resource lifecycle or application realization. Terraform continues to manage
infrastructure resources, while Docker Compose and future Kubernetes
realizations manage application workloads.

Initial use case: configure the existing Ubuntu lab host for observability
and runtime prerequisites.

- [ ] Add Ansible project structure
- [ ] Define inventory for the Ubuntu lab host
- [ ] Create reusable base host role
- [ ] Manage required OS packages and configuration
- [ ] Manage observability prerequisites
- [ ] Install and configure Node Exporter
- [ ] Manage relevant observability agents and configuration
- [ ] Ensure required services are enabled and running
- [ ] Demonstrate idempotency with a second playbook run producing no
      unnecessary changes

Future work:

- [ ] Evaluate generating Ansible inventory from the Platform Model
- [ ] Evaluate generating host/group variables from model and realization data
- [ ] Extend host configuration when additional VM or bare-metal deployment
      targets justify it
- [ ] Evaluate Ansible-based Kubernetes node/bootstrap configuration if a
      concrete requirement emerges

Ansible should remain responsible for configuration management. It should not
duplicate infrastructure lifecycle management performed by Terraform or
application deployment responsibilities owned by deployment realizations.

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

# Next Major Milestone - Kubernetes Realization

Goal: demonstrate that the same logical application intent can be realized
on both Docker Compose and Kubernetes without introducing Kubernetes-specific
concepts into the Platform Model unnecessarily.

- [ ] Establish lightweight local Kubernetes environment
- [ ] Define Platform Model -> Kubernetes mapping
- [ ] Implement Kubernetes generator
- [ ] Generate Deployments
- [ ] Generate Services
- [ ] Map resource requirements
- [ ] Map health intent to readiness/liveness/startup probes
- [ ] Map appropriate connectivity intent to NetworkPolicy
- [ ] Validate generated manifests
- [ ] Deploy the Out-Dialer reference platform
- [ ] Compare functional behavior with Docker Compose realization
  
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


# Observability MS1 Spotted Gaps

## Model/Realization Correction

The current Out-Dialer local-lab deployment requires Docker host-port overrides
because multiple application containers expose their metrics endpoint on port
9090 while running on the same Docker host.

The Platform Model correctly describes the application-side metrics port as
9090. However, deployment-specific host-port mappings such as `19090:9090` and
`29090:9090` are not currently represented in the realization model. These
mappings have therefore been applied manually to the generated Docker Compose
artifact.

In a future realization/generator update:

- represent Docker host-port overrides in the realization;
- keep application/container ports in the Platform Model;
- have the Docker Compose generator combine the model endpoint with the
  realization-specific host-port override;
- eliminate manual modification of generated Docker Compose artifacts.

## Campaign Execution Queue

The current synthetic Out-Dialer implementation starts a new background thread
for every accepted campaign. As a result, a campaign transitions from `queued`
to `running` almost immediately and there is no actual execution queue or
bounded worker capacity.

This limits the usefulness of the synthetic workload for observability
exercises. In particular, `campaign_queue_depth` would normally remain close to
zero and the system cannot realistically demonstrate workload saturation or
queue buildup.

In a future workload update:

- introduce an explicit campaign execution queue;
- use a fixed, configurable number of Campaign Manager worker threads;
- keep accepted campaigns in `queued` state until a worker becomes available;
- transition a campaign to `running` only when a worker starts processing it;
- preserve the existing asynchronous API behavior where `POST /campaigns`
  returns `202 Accepted` without waiting for execution;
- allow later observability scenarios to demonstrate queue depth, worker
  saturation, and increasing campaign execution latency under load.

The implementation should remain lightweight and use Python's standard
threading/queue mechanisms rather than introducing an external task queue or
message broker.
