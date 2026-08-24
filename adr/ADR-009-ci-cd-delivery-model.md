# ADR-009: CI/CD Delivery Model

## Status

Proposed

## Context

The Infrastructure Automation Framework can now validate a Platform Model,
load a Deployment Realization, and generate Docker Compose and Terraform /
RouterOS deployment artifacts.

The current development workflow still permits direct commits to `main`, and
deployment to the local reference lab is performed manually.

As the framework begins to manage multiple deployment artifacts from a shared
Platform Model, changes need a controlled delivery lifecycle that separates:

1. validation of proposed changes;
2. human review and approval;
3. deployment of trusted changes;
4. runtime verification after deployment.

The framework also introduces an important trust boundary.

Pull Request code is proposed and therefore potentially untrusted. It must not
receive credentials or connectivity that allow it to modify runtime
infrastructure.

Deployment should occur only from reviewed code that has been merged into the
trusted `main` branch.

The first deployment target is the existing local UTM reference lab containing:

- the Ubuntu Docker host;
- the MikroTik CHR router/firewall.

The lab is reachable only from the local environment and is not directly
accessible from GitHub-hosted runners.

## Decision

The project SHALL use a two-stage delivery model:

1. Pull Request Continuous Integration;
2. post-merge Continuous Deployment.

These stages SHALL use separate execution and trust contexts.

```text
Feature Branch
      |
      v
Pull Request
      |
      v
GitHub Actions CI
      |
      +--> tests
      +--> model validation
      +--> realization validation
      +--> artifact generation
      +--> artifact validation
      |
      v
Required Checks
      +
Human Review
      |
      v
Merge to main
      |
      v
Deployment Workflow
      |
      +--> regenerate artifacts
      +--> Terraform plan
      +--> deployment approval
      +--> Terraform apply
      +--> Docker deployment
      +--> smoke tests
      |
      v
Local Reference Lab
```
### Pull Request Continuous Integration

CI SHALL validate proposed changes without modifying runtime infrastructure.

The CI workflow SHALL be stored in the repository under:

`.github/workflows/`

and executed by GitHub Actions.

The initial CI implementation SHALL use GitHub-hosted runners.

CI SHALL execute the complete inexpensive regression suite rather than attempt change-specific test selection.

The initial CI responsibilities are:

1. check out the proposed source revision;
2. configure the supported Python runtime;
3. install the project and development dependencies from pyproject.toml;
4. run the complete automated Python test suite;
5. validate the Platform Model schemas;
6. perform semantic/reference validation;
7. validate the selected Deployment Realization;
8. generate Docker Compose;
9. generate Terraform / RouterOS HCL;
10. validate generated artifacts using their native tooling.

Conceptually:

```text
Platform Model
      +
Deployment Realization
      |
      v
Validation
      |
      v
Generators
      |
      +------------------+
      |                  |
      v                  v
Docker Compose       Terraform
      |                  |
      v                  v
compose config       fmt / validate
```

CI SHALL NOT perform:

- terraform apply;
- Docker deployment to the reference environment;
- direct RouterOS configuration;
- any operation requiring deployment credentials.

### Pull Request Quality Gate

Direct changes to `main` SHOULD be replaced by a feature-branch and Pull-Request workflow.

Repository protection rules SHOULD require relevant automated CI checks to pass before a Pull Request may be merged.

Human review SHOULD provide an independent approval boundary between automated validation and acceptance of the infrastructure change.

The architecture supports a multi-engineer review model even if the initial portfolio repository is operated primarily by one developer.

### Artifact Generation During CI

Generated Docker Compose and Terraform files SHALL be treated as build artifacts rather than independent sources of truth.

The authoritative inputs remain:

```text
Platform Model
        +
Deployment Realization
```

CI SHOULD generate deployment artifacts from the exact proposed revision and MAY publish them as GitHub Actions artifacts for inspection and troubleshooting.

Artifact generation during CI is required because validation of the source model alone does not prove that the generators produce syntactically valid deployment output.

### Post-Merge Continuous Deployment

Deployment SHALL operate only on trusted code from `main`.

The deployment workflow SHALL use a separate execution context from Pull Request CI.

Because GitHub-hosted runners cannot reach the local UTM reference lab, the initial deployment implementation SHALL use a self-hosted GitHub Actions runner with connectivity to the target environment.

The exact self-hosted runner placement is deferred. Candidate locations include:

- the macOS automation workstation;
- a dedicated management host in the local lab.

The deployment workflow SHALL regenerate deployment artifacts from the exact merged main revision being deployed.

It SHALL NOT rely on artifacts generated by an earlier unmerged Pull Request execution as the authoritative deployment input.

### Deployment Sequence

The initial deployment sequence SHALL be:
```text 
trusted main revision
        |
        v
generate deployment artifacts
        |
        v
Terraform plan
        |
        v
deployment approval
        |
        v
Terraform apply
        |
        v
Docker Compose deployment
        |
        v
post-deployment smoke tests
```

Terraform planning SHALL be separated from Terraform application.

The initial implementation SHOULD require an approval boundary before infrastructure modification.

Fully automatic deployment MAY be considered later after rollback, deployment safety and environment recovery procedures are sufficiently mature.

### Post-Deployment Verification

A successful Terraform or Docker command does not by itself prove that the platform is operating correctly.

The initial deployment workflow SHALL therefore execute a small reference platform smoke suite after deployment.

The smoke suite SHALL validate the deployed platform as a whole rather than attempt to select tests based only on the files changed in the commit.

Initial checks MAY include:

- expected application containers are running;
- application health endpoints respond;
- expected allowed network paths succeed;
- expected forbidden network paths remain blocked;
- RouterOS remains reachable after configuration changes.

The first smoke suite is intentionally limited in scope.

It is not intended to represent exhaustive validation for every possible model change.

Model-derived runtime tests, synthetic probes and continuous verification are deferred to the Observability/SRE phase.

Test Selection Strategy

The initial CI implementation SHALL run the complete automated regression suite for every Pull Request.

Model validation SHALL operate on the complete selected Platform Model rather than only on modified YAML files.

This is deliberate because model objects contain cross-domain references and a change in one file may invalidate another part of the model.

Selective test execution MAY be introduced later if the test suite becomes sufficiently expensive to justify the additional complexity.

Post-deployment smoke tests SHALL likewise run as a small complete suite for the reference platform.

### Trust Boundaries

The delivery architecture SHALL maintain the following trust boundaries:

|Stage	|Source	|Infrastructure |Access	|Purpose|
| ------ | ----- | --- | ------- | ------ |
|Feature branch	|Proposed code	|No	|Development|
|Pull Request CI|Proposed code	|No	|Validation and generation|
|Human review	|Proposed code	|No	|Change approval|
|`main`	|Reviewed code	|No direct access	|Trusted source|
|Deployment workflow	|Trusted main	|Yes	C|ontrolled deployment|
|Post-deployment tests	|Runtime environment	|Test/read access	|Runtime verification|

The primary security rule is:

> Unreviewed code SHALL NOT receive credentials capable of modifying the deployment environment.

Secrets required for deployment SHALL only be available to the trusted
deployment workflow.

### Dependency Management

Python runtime and development dependencies SHALL be declared in `pyproject.toml`.

Development/test dependencies SHOULD be defined through an optional dependency group so local development and GitHub Actions use the same installation model.

For example:
```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0",
]
```

The initial CI runner SHOULD use Python 3.13, matching the supported project
runtime declared in `pyproject.toml`.

### Consequences
#### Advantages
- Proposed infrastructure changes are validated before acceptance.
- Direct unreviewed modification of `main` is reduced.
- Deployment credentials are isolated from Pull Request execution.
- Model validation and generated-artifact validation become repeatable.
- Deployment artifacts remain traceable to version-controlled intent.
- The same source revision can be reproduced on a clean runner.
- Runtime verification becomes part of the delivery lifecycle.
- The architecture provides a natural transition toward continuous synthetic monitoring and SLOs.
- The workflow resembles production engineering practices while remaining appropriate for the local reference lab.

#### Trade-offs
- Development changes require branches and Pull Requests.
- GitHub Actions configuration becomes another maintained part of the repository.
- A self-hosted runner must eventually be operated for local deployment.
- Deployment credentials and runner security require explicit management.
- Manual deployment approval initially limits full automation.
- Post-deployment validation introduces additional implementation work.
- Full regression execution may become expensive as the project grows.

### Deferred Decisions

The following decisions are intentionally deferred:

- exact GitHub Actions workflow file structure;
- exact branch protection/ruleset configuration;
- self-hosted runner placement;
- runner lifecycle and hardening;
- deployment-secret storage and rotation;
- remote Terraform state backend;
- Terraform state locking;
- automatic rollback;
- artifact retention policy;
- release/version promotion between environments;
- change-specific integration-test selection;
- model-derived runtime test generation;
- continuous synthetic probes;
- automatic SLO evaluation and burn-rate alerting;
- fully automatic deployment without an approval gate.

### Initial Implementation Plan

The CI/CD milestone will be introduced incrementally.

#### Phase 1 — Pull Request CI
1. add development dependencies to pyproject.toml;
2. add a GitHub Actions CI workflow;
3. execute the complete test suite;
4. validate the Platform Model;
5. validate the Deployment Realization;
6. generate Docker Compose;
7. generate RouterOS Terraform;
8. validate both generated artifacts;
9. publish generated artifacts;
10. configure required checks for Pull Requests.

#### Phase 2 — Controlled Local-Lab Deployment
1. introduce a self-hosted runner;
2. trigger deployment only from trusted main;
3. regenerate artifacts from the merged revision;
4. execute terraform plan;
5. require deployment approval;
6. execute terraform apply;
7. deploy Docker Compose;
8. run the reference-platform smoke suite.

#### Phase 3 — Observability Integration

Post-deployment smoke checks will later evolve into continuous runtime
verification using:

- application health signals;
- infrastructure metrics;
- RouterOS telemetry;
- synthetic connectivity probes;
- Prometheus;
- Grafana;
- SLIs and SLOs.

This phase is governed separately by the observability architecture and does not
need to be completed before the initial CI/CD milestone.