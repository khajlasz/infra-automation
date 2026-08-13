# ADR-008: Deployment Realization and Addressing

## Status

Proposed

---

## Context

The Platform Model describes deployment-independent platform intent.

The Docker Compose backend initially mapped logical compute nodes and logical
networks into Docker services and Docker networks without requiring
environment-specific infrastructure information.

The routed UTM lab prototype demonstrated that a real deployment requires
additional implementation-specific values.

For the local Docker lab these include:

- Docker network driver (`macvlan`)
- Ubuntu parent interfaces (`enp0s2`, `enp0s3`, `enp0s4`)
- Docker IP allocation ranges

These values describe how a logical platform is realized in one particular
environment. They are not properties of the logical platform itself.

The prototype also demonstrated a need for network addressing information.

Addressing has both deployment-independent and deployment-specific aspects.

For example:

- a platform may require three `/24` logical networks;
- a platform may define a default enclosing IPv4 address pool;
- a particular realization may need to use a different address pool;
- Docker, RouterOS, AWS, Hetzner and Kubernetes differ in gateway, reservation
  and endpoint-allocation behaviour.

The framework therefore needs to separate logical addressing intent from
provider-specific allocation mechanics.

---

## Decision

The framework SHALL distinguish between:

1. **Platform Model**
2. **Deployment Realization**
3. **Resolved Deployment**

```text
Platform Model
      +
Deployment Realization
      |
      v
Resolution / Normalization
      |
      v
Resolved Deployment
      |
      v
Generators
```

### Platform Model

The Platform Model SHALL contain deployment-independent intent.

This includes:

- logical networks
- node-to-network relationships
- required subnet sizes
- deterministic subnet allocation identifiers
- an optional default address pool

Example:

```yaml
addressing:
  ipv4Pool: 10.10.0.0/16

networks:

  dmz:
    site: lab
    purpose: External client access
    subnet:
      slot: 10
      prefixLength: 24

  internal:
    site: lab
    purpose: Internal platform communication
    subnet:
      slot: 20
      prefixLength: 24

  database:
    site: lab
    purpose: Database communication
    subnet:
      slot: 30
      prefixLength: 24
```

The Platform Model SHALL NOT contain deployment-specific values such as:

- Linux interface names
- Docker network drivers
- Docker parent interfaces
- Docker IPAM allocation ranges
- RouterOS interface names
- AWS resource identifiers
- provider-specific gateway behaviour

---

### Deployment Realization

A Deployment Realization SHALL describe how a Platform Model is implemented in
a particular environment.

A realization MAY override selected Platform Model defaults.

For example, a Platform Model may define:

```yaml
addressing:
  ipv4Pool: 10.10.0.0/16
```

while an AWS realization may override it with:

```yaml
addressing:
  ipv4Pool: 10.50.0.0/16
```

The realization SHALL contain backend-specific configuration that cannot be
derived from the Platform Model.

For the local Docker lab this includes:

```yaml
name: local-lab

docker:
  networks:

    dmz:
      driver: macvlan
      parent: enp0s2
      ipRange: 10.10.10.128/28

    internal:
      driver: macvlan
      parent: enp0s3
      ipRange: 10.10.20.128/28

    database:
      driver: macvlan
      parent: enp0s4
      ipRange: 10.10.30.128/28
```

Backend-specific sections SHALL be introduced only when a concrete backend
requires them.

RouterOS-specific realization data SHALL therefore not be added until the
Terraform/RouterOS prototype demonstrates which values are required.

---

## Address Pool Resolution

The effective IPv4 pool SHALL be resolved using this precedence:

```text
realization override
        |
        v
Platform Model default
```

If the realization does not provide an override, the Platform Model default is
used.

The initial implementation SHALL support one level of override only.

It SHALL NOT initially implement hierarchical inheritance across global,
region, availability-zone, site, device-role or device scopes.

More advanced hierarchical configuration may be introduced later, potentially
using concepts similar to NetBox Config Context.

---

## Subnet Allocation

Logical networks SHALL describe subnet intent using:

- a prefix length;
- an explicit deterministic subnet slot.

The subnet slot identifies which child subnet of the parent address pool belongs
to the logical network.

Example:

```yaml
subnet:
  slot: 20
  prefixLength: 24
```

Given:

```yaml
ipv4Pool: 10.10.0.0/16
```

the following configuration:

```text
dmz       slot 10 /24
internal  slot 20 /24
database  slot 30 /24
```

resolves to:

```text
dmz       10.10.10.0/24
internal  10.10.20.0/24
database  10.10.30.0/24
```

Subnet allocation SHALL NOT depend on YAML declaration order.

Using stable slots also avoids renumbering existing networks when another
logical network is introduced later.

Generators SHALL consume resolved CIDRs rather than calculating subnets
independently.

---

## Endpoint Address Allocation

The Platform Model SHALL NOT assign individual workload IP addresses by
default.

It SHALL describe which logical networks a workload belongs to.

Endpoint IP allocation SHALL normally be delegated to the deployment backend
or its IPAM mechanism.

Examples include:

- Docker IPAM
- AWS private-IP allocation
- Hetzner private-network allocation
- Kubernetes CNI/IPAM

Explicit workload addresses may be introduced later if a concrete use case
requires deterministic endpoint addressing.

---

## Gateway Semantics

A concrete gateway address SHALL NOT be assumed to be a universal Platform
Model property.

Gateway behaviour differs between deployment technologies.

Examples include:

- RouterOS may explicitly configure the first usable address;
- AWS provides provider-defined subnet routing semantics;
- cloud providers may manage gateway behaviour automatically;
- Kubernetes networking delegates these semantics to the CNI implementation.

Generators and realization logic SHALL therefore handle gateway behaviour
according to backend semantics.

---

## Generator Input

Generators SHOULD ultimately consume a resolved representation rather than
performing model/realization precedence themselves.

Conceptually:

```text
PlatformModel
      +
Realization
      |
      v
ResolvedDeployment
      |
      +------> Docker Compose Generator
      |
      +------> Terraform / RouterOS Generator
      |
      +------> future AWS Generator
```

The exact Python representation of `ResolvedDeployment` is deferred until the
first implementation.

---

## Consequences

### Advantages

- Platform intent remains provider independent.
- Local lab implementation details do not contaminate the domain model.
- Address spaces can be reused or overridden between environments.
- Subnet allocation is deterministic.
- Existing lab addressing remains stable.
- Generators consume consistent resolved topology.
- Future AWS, Hetzner and other backends can use the same logical network
  structure.
- The design provides a controlled path toward hierarchical context without
  implementing it prematurely.

### Trade-offs

- A new realization input must be loaded and validated.
- A resolution/normalization stage is required before generation.
- Configuration precedence must be explicitly defined.
- More than one source file contributes to the final generated artifact.

---

## Deferred Decisions

The following are intentionally deferred:

- hierarchical realization inheritance
- NetBox Config Context integration
- RouterOS-specific realization schema
- explicit host/workload IP allocation
- IPv6 allocation
- multiple address pools
- dynamic/stateful IPAM
- provider-specific gateway policy

---

## Initial Model Changes

The current Out-Dialer network model can evolve from:

```yaml
networks:

  dmz:
    site: lab
    purpose: External client access

  internal:
    site: lab
    purpose: Internal platform communication

  database:
    site: lab
    purpose: Database communication
```

to:

```yaml
addressing:
  ipv4Pool: 10.10.0.0/16

networks:

  dmz:
    site: lab
    purpose: External client access
    subnet:
      slot: 10
      prefixLength: 24

  internal:
    site: lab
    purpose: Internal platform communication
    subnet:
      slot: 20
      prefixLength: 24

  database:
    site: lab
    purpose: Database communication
    subnet:
      slot: 30
      prefixLength: 24
```

This preserves the proven lab addressing:

```text
dmz       10.10.10.0/24
internal  10.10.20.0/24
database  10.10.30.0/24
```

while keeping subnet allocation deterministic and independent of YAML order.

---

## Initial Local-Lab Realization

The first realization file is expected to live at:

```text
models/out-dialer/realizations/local-lab.yaml
```

Initial content:

```yaml
name: local-lab

docker:
  networks:

    dmz:
      driver: macvlan
      parent: enp0s2
      ipRange: 10.10.10.128/28

    internal:
      driver: macvlan
      parent: enp0s3
      ipRange: 10.10.20.128/28

    database:
      driver: macvlan
      parent: enp0s4
      ipRange: 10.10.30.128/28
```

The realization intentionally contains only Docker-specific values currently
proven necessary by the local lab.

RouterOS-specific fields will be added only after the Terraform prototype
demonstrates their requirements.
