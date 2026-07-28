Version: 0.1
Status: Draft
Last Updated: 2026-07

# Modelling Guidelines

## Purpose

This document defines the modelling principles used throughout the Infrastructure
Automation Framework.

The objective is to build a **declarative, provider-independent platform model**
that can be validated and used to generate deployment artifacts such as
Terraform, Ansible, documentation and other automation outputs.

The platform model is the primary source of truth.

---

# Core Philosophy

The model describes **what** the platform should look like.

It does not describe **how** deployment tools implement it.

```
             Platform Model
                    │
         Structural Validation
                    │
         Reference Validation
                    │
          Business Validation
                    │
     ┌──────────────┼──────────────┐
     │              │              │
 Terraform      Ansible     Documentation
```

---

# Design Principles

## Single Source of Truth

Every piece of information has exactly one owner.

Avoid duplicated values.

Objects reference one another rather than copying data.

Example:

Good

```yaml
compute_profile: medium
```

Bad

```yaml
cpu: 4
ram: 8192
```

on every node.

---

## Normalised Model

The model follows database normalisation principles.

Reusable concepts should be defined once and referenced elsewhere.

Examples include:

- Sites
- Networks
- Compute Profiles
- Storage Profiles
- Device Profiles
- Applications
- Deployments

---

## Definitions vs Instances

The model separates reusable definitions from deployed objects.

| Definitions | Instances |
|------------|-----------|
| Site | Node |
| Network | Device |
| Compute Profile | |
| Storage Profile | |
| Device Profile | |
| Application | |
| Deployment | |

Definitions describe reusable concepts.

Instances describe concrete deployments.

---

## References

Relationships are expressed using stable identifiers.

Example

```yaml
deployment: bw-adp-webex
```

```yaml
compute_profile: medium
```

```yaml
network: signalling
```

References are validated by the framework.

Schemas validate only structure.

---

## File Naming and Root Objects

Each model file represents exactly one collection of objects.

The filename and the root YAML key shall describe the same collection.

The root YAML key must equal the filename after replacing `-` with `_`.

Examples:

| File | Root key |
|------|----------|
| `platform.yaml` | `platform` |
| `sites.yaml` | `sites` |
| `networks.yaml` | `networks` |
| `device-profiles.yaml` | `device_profiles` |
| `devices.yaml` | `devices` |
| `compute-profiles.yaml` | `compute_profiles` |
| `storage-profiles.yaml` | `storage_profiles` |
| `nodes.yaml` | `nodes` |
| `applications.yaml` | `applications` |
| `deployments.yaml` | `deployments` |

This convention enables the Loader to perform a simple, generic mapping:

```
filename
    ↓
replace '-' with '_'
    ↓
expected root key
    ↓
PlatformModel attribute
```

Example:

```yaml
# compute-profiles.yaml

compute_profiles:

  small:
    cpu: 2
    ram: 4096

  medium:
    cpu: 4
    ram: 8192
```

becomes

```python
model.compute.compute_profiles["small"]
```

The Loader removes the outer wrapper object because it is already represented by
the filename and the corresponding `PlatformModel` attribute.

This transformation is lossless and is performed uniformly for every model file.
---

## Provider Independence

The platform model must remain independent from deployment technologies.

Avoid embedding concepts specific to:

- Terraform
- AWS
- Azure
- VMware
- Kubernetes
- MikroTik

Generators translate the platform model into implementation-specific resources.

---

# Domain Separation

The model is divided into four independent domains.

```
Platform
│
├── Network
├── Compute
└── Application
```

Each domain should evolve independently.

---

## Platform Domain

Defines the platform itself.

Examples:

- Platform
- Sites

---

## Network Domain

Defines logical networking.

Contains:

- Sites
- Networks
- Device Profiles
- Devices
- Policies

Physical inventory is intentionally outside the scope of the framework.

External systems such as NetBox are expected to manage inventory and IPAM.

---

## Compute Domain

Defines execution environments.

Contains:

- Compute Profiles
- Storage Profiles
- Nodes

Nodes describe infrastructure.

They reference deployments.

They do not describe installed software directly.

---

## Application Domain

Defines deployable software.

Contains:

- Applications
- Deployments

Applications describe reusable deployable software units.

Examples:

- OCI
- OCI-P
- XSI-Actions
- DeviceManagement

Deployments describe concrete software stacks.

A deployment specifies:

- Product metadata
- Product version
- Installed applications
- Application versions
- Deployment-specific configuration

Examples:

- contextPath
- JVM options
- Configuration parameters

Nodes deploy Deployments.

---

# Validation Philosophy

Validation is intentionally divided into multiple stages.

## Stage 1

Structural validation

Performed using Yamale.

Checks:

- YAML structure
- Required fields
- Data types

No cross-file validation is performed.

---

## Stage 2

Reference validation

Performed by the framework.

Examples:

- deployment exists
- computeProfile exists
- application exists
- network exists
- site exists

---

## Stage 3

Business validation

Business rules are validated by the framework.

Examples:

- required applications
- required networks
- version compatibility
- naming conventions
- dependency validation

Business rules should be driven by the model rather than hardcoded in Python whenever practical.

---

# Model Evolution

Introduce new concepts only when they provide clear value.

Examples:

- eliminate duplication
- improve readability
- support validation
- support generators

Avoid speculative abstractions.

Prefer extending existing objects over introducing new object types.

---

# LLM Guidance

When extending the model:

1. Preserve existing semantics.
2. Prefer references over duplicated values.
3. Keep the model provider independent.
4. Preserve object identifiers.
5. Introduce the smallest possible change.
6. Avoid architectural redesign unless explicitly requested.
7. If a better design is identified, propose it separately rather than silently changing the model.

---

# Long-Term Vision

The telecom model is the first reference implementation of the framework.

Future models may include:

- Cloud Infrastructure
- Kubernetes Platforms
- AI Infrastructure
- Enterprise Applications

The modelling framework should support all of them without changing its core architecture.