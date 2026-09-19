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

Realization rules REF-008 and REF-009 validate references between a
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
