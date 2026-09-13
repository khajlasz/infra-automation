# Semantic Validation Registry

This document defines the semantic validation rules implemented by the
Infrastructure Automation Framework.

Unlike schema validation, these rules validate the assembled `PlatformModel`
rather than individual YAML files.

The registry is the authoritative specification for framework validation.

Each rule has a stable identifier that is referenced by:

- Python implementation
- Unit tests
- Log messages
- Documentation

## Scope

The Validation Registry specifies only semantic validation rules that cannot be
enforced by earlier processing stages (YAML parsing or schema validation).

---

# Path Notation

Validation rules describe objects using logical paths through the
`PlatformModel`.

The notation is independent of the Python implementation.

Notation:

- `.` separates object attributes.
- `[*]` means "every element in the collection".
- Paths describe the logical data model.

Examples:

| Path | Meaning |
|------|---------|
| `model.compute.nodes[*].site` | The `site` attribute of every compute node. |
| `model.compute.nodes[*].interfaces[*].network` | The `network` attribute of every interface on every compute node. |
| `model.application.deployments[*].applications[*].application` | Every application referenced by every deployment. |

---

# Validation Coverage

| ID | Category | Title | Severity | Status |
|----|----------|-------|----------|--------|
| REF-001 | Reference Integrity | Node references an existing site | ERROR | Implemented |
| REF-002 | Reference Integrity | Interface references an existing network | ERROR | Planned |
| REF-003 | Reference Integrity | Deployment references an existing application | ERROR | Planned |
| REF-004 | Reference Integrity | External interface target references an existing application | ERROR | Planned |
| REF-005 | Reference Integrity | External interface target references an existing application endpoint | ERROR | Planned |

---

# Reference Integrity Rules

---

## REF-001

### Title

Node references an existing site.

### Purpose

Ensure every compute node belongs to a valid deployment site.

### Source

`model.compute.nodes[*].site`

### Target

`model.network.sites`

### Validation

Every node SHALL reference an existing site.

### Error Message

```
REF-001: Node '{node}' references unknown site '{site}'.
```

### Severity

ERROR

### Status

Implemented

---

## REF-002

### Title

Interface references an existing network.

### Purpose

Ensure every compute node interface is attached to an existing network.

### Source

`model.compute.nodes[*].interfaces[*].network`

### Target

`model.network.networks`

### Validation

Every interface SHALL reference an existing network.

### Error Message

```
REF-002: Interface '{interface}' on node '{node}' references unknown network '{network}'.
```

### Severity

ERROR

### Status

Planned

---

## REF-003

### Title

Deployment references an existing application.

### Purpose

Ensure every deployment references an application defined in the model.

### Source

`model.application.deployments[*].applications[*].application`

### Target

`model.application.applications`

### Validation

Every deployment SHALL reference an existing application.

### Error Message

```
REF-003: Deployment '{deployment}' references unknown application '{application}'.
```

### Severity

ERROR

### Status

Planned

## REF-004

### Title

External interface target references an existing application.

### Purpose

Ensure every external interface target references an application defined in the model.

### Source

`model.platform.external_interfaces[*].targets[*].application`

### Target

`model.application.applications`

### Validation

Every external interface target SHALL reference an existing application.

### Error Message

```text
REF-004: External interface '{interface}' references unknown application '{application}'.
```
### Severity

ERROR

### Status

Planned

## REF-005
### Title

External interface target references an existing application endpoint.

### Purpose

Ensure every external interface target references an endpoint defined by the referenced application.

### Source

`model.platform.external_interfaces[*].targets[*].endpoint`

Target

`model.application.applications[*].endpoints`

### Validation

Every external interface target SHALL reference an endpoint defined by its referenced application.

Error Message
```text
REF-005: External interface '{interface}' references unknown endpoint '{endpoint}' on application '{application}'.
```
### Severity

ERROR

### Status

Planned

## REF-006

### Title

External interface references an existing source network.

### Purpose

Ensure every external interface source network is defined in the platform model.

### Source

`model.platform.external_interfaces[*].sourceNetwork`

### Target

`model.network.networks`

### Validation

Every external interface SHALL reference an existing source network.

### Error Message

```text
REF-006: External interface '{interface}' references unknown source network '{network}'.
```

### Severity

ERROR

### Status

Planned

## REF-007

### Title

External interface target references an existing network.

### Purpose

Ensure every external interface target is associated with a network defined in the platform model.

### Source

`model.platform.external_interfaces[*].targets[*].network`

### Target

`model.network.networks`

### Validation

Every external interface target SHALL reference an existing network.

### Error Message

```text
REF-007: External interface '{interface}' target '{application}.{endpoint}' references unknown network '{network}'.
Severity
```
### Severity

ERROR

### Status

Planned

## REF-008

### Title

Docker host references existing compute nodes.

### Purpose

Ensure every compute node assigned to a Docker realization host exists in the Platform Model.

### Source

`realization.docker.hosts[*].nodes[*]`

### Target

`model.compute.nodes`

### Validation

Every node assigned to a Docker host SHALL reference an existing compute node.

### Error Message

```text
REF-008: Docker host '{host}' references unknown compute node '{node}'.
```

### Severity

ERROR

### Status

Planned

## REF-009

### Title

Compute node is assigned to at most one Docker host.

### Purpose

Prevent ambiguous Docker placement by ensuring that a compute node is not assigned to multiple Docker realization hosts.

### Source

`realization.docker.hosts[*].nodes[*]`

### Target

Docker host placement set

### Validation

Each compute node SHALL appear in at most one Docker host placement list.

### Error Message

```text
REF-009: Compute node '{node}' is assigned to multiple Docker hosts: '{first_host}' and '{second_host}'.
```
### Severity

ERROR

### Status

Planned