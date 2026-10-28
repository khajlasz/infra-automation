# Semantic Validation Registry

This document defines the semantic validation rules implemented by the
Infrastructure Automation Framework.

Unlike schema validation, these rules validate references across the
assembled `PlatformModel` and between the model and a deployment
realization.

The registry is the authoritative specification for framework semantic
validation.

Each rule has a stable identifier referenced by:

-   Python implementation
-   unit tests
-   log messages
-   documentation

## Scope

The Validation Registry specifies semantic rules that cannot be enforced
by individual YAML schemas alone.

Model rules REF-001 through REF-007 operate on the assembled Platform
Model.

Realization rules REF-008 through REF-012 validate references between a
loaded Platform Model and a deployment realization.

------------------------------------------------------------------------

# Path Notation

Validation rules describe objects using logical paths.

-   `.` separates object attributes.
-   `[*]` means every element in a collection.
-   paths describe logical model structure rather than Python
    implementation details.

Examples:

``` text
model.compute.nodes[*].site
model.compute.nodes[*].interfaces[*].network
model.application.deployments[*].applications[*].application
realization.docker.hosts[*].nodes[*]
```

------------------------------------------------------------------------

# Validation Coverage

``` text
REF-001  Node references an existing site                         Implemented
REF-002  Interface references an existing network                 Implemented
REF-003  Deployment references an existing application            Implemented
REF-004  External target references an existing application       Implemented
REF-005  External target references an existing endpoint          Implemented
REF-006  External interface references an existing source network Implemented
REF-007  External target references an existing network           Implemented
REF-008  Docker host references existing compute nodes            Implemented
REF-009  Compute node is assigned to at most one Docker host      Implemented
REF-010  Kubernetes workload references a capacity profile       Implemented
REF-011  Kubernetes selected endpoints and probes resolve        Implemented
REF-012  Kubernetes metrics binding resolves unambiguously       Implemented
```

------------------------------------------------------------------------

# Reference Integrity Rules

## REF-001 --- Node references an existing site

**Purpose**

Ensure every compute node belongs to a valid deployment site.

**Source**

`model.compute.nodes[*].site`

**Target**

`model.network.sites`

**Validation**

Every node SHALL reference an existing site.

**Error**

``` text
REF-001: Node '{node}' references unknown site '{site}'.
```

**Severity:** ERROR\
**Status:** Implemented

------------------------------------------------------------------------

## REF-002 --- Interface references an existing network

**Purpose**

Ensure every compute-node interface is attached to an existing logical
network.

**Source**

`model.compute.nodes[*].interfaces[*].network`

**Target**

`model.network.networks`

**Validation**

Every interface SHALL reference an existing network.

**Error**

``` text
REF-002: Interface '{interface}' on node '{node}' references unknown network '{network}'.
```

**Severity:** ERROR\
**Status:** Implemented

------------------------------------------------------------------------

## REF-003 --- Deployment references an existing application

**Purpose**

Ensure every deployment references an application defined in the model.

**Source**

`model.application.deployments[*].applications[*].application`

**Target**

`model.application.applications`

**Validation**

Every deployment SHALL reference an existing application.

**Error**

``` text
REF-003: Deployment '{deployment}' references unknown application '{application}'.
```

**Severity:** ERROR\
**Status:** Implemented

------------------------------------------------------------------------

## REF-004 --- External interface target references an existing application

**Purpose**

Ensure every external-interface target references an application defined
in the model.

**Source**

`model.platform.external_interfaces[*].targets[*].application`

**Target**

`model.application.applications`

**Validation**

Every external-interface target SHALL reference an existing application.

**Error**

``` text
REF-004: External interface '{interface}' references unknown application '{application}'.
```

**Severity:** ERROR\
**Status:** Implemented

------------------------------------------------------------------------

## REF-005 --- External interface target references an existing application endpoint

**Purpose**

Ensure every external-interface target references an endpoint defined by
its referenced application.

**Source**

`model.platform.external_interfaces[*].targets[*].endpoint`

**Target**

`model.application.applications[*].endpoints`

**Validation**

Every external-interface target SHALL reference an endpoint defined by
the referenced application.

If the application itself does not exist, REF-004 owns that failure and
REF-005 does not emit a duplicate error.

**Error**

``` text
REF-005: External interface '{interface}' references unknown endpoint '{endpoint}' on application '{application}'.
```

**Severity:** ERROR\
**Status:** Implemented

------------------------------------------------------------------------

## REF-006 --- External interface references an existing source network

**Purpose**

Ensure every external interface's source network is defined in the
Platform Model.

**Source**

`model.platform.external_interfaces[*].sourceNetwork`

**Target**

`model.network.networks`

**Validation**

Every external interface SHALL reference an existing source network.

**Error**

``` text
REF-006: External interface '{interface}' references unknown source network '{network}'.
```

**Severity:** ERROR\
**Status:** Implemented

------------------------------------------------------------------------

## REF-007 --- External interface target references an existing network

**Purpose**

Ensure every external-interface target is associated with a network
defined in the Platform Model.

**Source**

`model.platform.external_interfaces[*].targets[*].network`

**Target**

`model.network.networks`

**Validation**

Every external-interface target SHALL reference an existing network.

**Error**

``` text
REF-007: External interface '{interface}' target '{application}.{endpoint}' references unknown network '{network}'.
```

**Severity:** ERROR\
**Status:** Implemented

------------------------------------------------------------------------

# Realization Reference Rules

## REF-008 --- Docker host references existing compute nodes

**Purpose**

Ensure every compute node assigned to a Docker realization host exists
in the Platform Model.

**Source**

`realization.docker.hosts[*].nodes[*]`

**Target**

`model.compute.nodes`

**Validation**

Every node assigned to a Docker host SHALL reference an existing compute
node.

**Error**

``` text
REF-008: Docker host '{host}' references unknown compute node '{node}'.
```

**Severity:** ERROR\
**Status:** Implemented

------------------------------------------------------------------------

## REF-009 --- Compute node is assigned to at most one Docker host

**Purpose**

Prevent ambiguous Docker placement by ensuring that a compute node is
not assigned to multiple Docker realization hosts.

**Source**

`realization.docker.hosts[*].nodes[*]`

**Target**

Docker host placement set.

**Validation**

Each compute node SHALL appear in at most one Docker host placement
list.

This rule intentionally does not require every model node to be
assigned. A future completeness rule may be introduced separately if
deployment semantics require it.

**Error**

``` text
REF-009: Compute node '{node}' is assigned to multiple Docker hosts: '{first_host}' and '{second_host}'.
```

**Severity:** ERROR\
**Status:** Implemented


## REF-010 --- Kubernetes workload capacity binding

**Source:** `realization.kubernetes.workloads[*].computeProfile` and `replicas`.
**Target:** `model.compute.compute_profiles`.

Each workload SHALL directly reference an existing shared capacity profile.
Replica count SHALL be a positive integer (not boolean). CPU capacity SHALL be
positive and finite; RAM capacity SHALL be a positive integer MiB. Half the
capacity divided by replicas, floored to millicores/MiB, SHALL remain at least
1m/1Mi. Failures raise `ModelError` with `REF-010` and workload context.
Workload keys are object names; compute-node references are not required.

**Severity:** ERROR; **Status:** Implemented.

## REF-011 --- Kubernetes endpoint and probe references resolve

**Source:** Each workload's `endpoints` and `probes`.
**Target:** Explicit workload deployment → selected application → application endpoints.

The workload's explicit deployment and application SHALL exist, and the
application SHALL belong to that deployment. Every selected endpoint SHALL
belong to that single application. Compute nodes are not traversed. Duplicate endpoint identities and protocols outside HTTP, HTTPS,
TCP, UDP fail. Distinct selected endpoints SHALL resolve to unique numeric
container ports within each workload, regardless of protocol. Port conflicts
identify the workload ID, numeric port and both endpoint identities. Probe ports SHALL reference a selected endpoint using HTTP or
HTTPS. Failures raise `ModelError` with `REF-011` and workload context.

**Severity:** ERROR; **Status:** Implemented.

## REF-012 --- Kubernetes metrics bindings resolve unambiguously

**Source:** `kubernetes.observability.metrics.externalInterface`.
**Target:** `model.platform.external_interfaces` (initially `metrics`).

When metrics discovery is configured, the selected external interface SHALL
exist with a valid source-network reference and a targets list. Every target
SHALL resolve to an existing application and `metrics` endpoint using HTTP and
an explicit path beginning with `/`, and reference an existing target network.
Validate all targets before filtering, including targets for applications not
installed by any selected workload. Invalid references or required metadata
raise `ModelError` with `REF-012`.

For each selected workload, zero matching targets is valid; the future generator
SHALL omit Prometheus scrape annotations and metrics ports for that workload.
Exactly one target matching the workload's explicitly selected application
is valid. Multiple matching targets raise `ModelError` with `REF-012`, the
workload ID and ambiguous target identities. Targets for other applications
are validated but are not selected.
No Kubernetes connectivity is inferred from source or target networks.

**Severity:** ERROR; **Status:** Implemented.
