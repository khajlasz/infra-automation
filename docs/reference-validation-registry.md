# Validation Registry

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
| REF-001 | Reference Integrity | Node references an existing site | ERROR | Planned |
| REF-002 | Reference Integrity | Interface references an existing network | ERROR | Planned |
| REF-003 | Reference Integrity | Deployment references an existing application | ERROR | Planned |
| UNI-001 | Uniqueness | IP addresses are unique | ERROR | Planned |
| UNI-002 | Uniqueness | Node names are unique | ERROR | Planned |

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

Planned

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

---

# Uniqueness Rules

---

## UNI-001

### Title

IP addresses are unique.

### Purpose

Ensure every interface has a globally unique IP address.

### Scope

`model.compute.nodes[*].interfaces[*]`

### Property

`ipAddress`

### Validation

The value of `ipAddress` SHALL be unique across all interfaces.

### Error Message

```
UNI-001: Duplicate IP address '{ipAddress}' found on interface '{interface2}'
of node '{node2}'. It is already assigned to interface '{interface1}' of node
'{node1}'.
```

### Severity

ERROR

### Status

Planned

