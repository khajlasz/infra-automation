# ADR-008: Deployment Realization and Addressing

## Status

Proposed

## Context

The Platform Model describes deployment-independent platform intent. The routed
UTM/Docker prototype demonstrated that a concrete deployment also requires
environment-specific information such as Docker `macvlan` configuration, Linux
parent interfaces, and backend-specific address allocation ranges.

Addressing also spans both concerns. Logical networks need stable addressing
intent, while Docker, RouterOS, AWS, Hetzner, Kubernetes, and future backends
have different gateway, reservation, subnet-allocation, and endpoint-allocation
semantics.

Automatic subnet carving from a parent pool is deliberately not implemented at
this stage. Real networks can have heterogeneous sizes, and stable subnet
allocation is normally an IPAM responsibility.

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

The Platform Model SHALL contain deployment-independent intent, including:

- logical networks;
- node-to-network relationships;
- explicit default network CIDRs;
- an optional enclosing/default address pool.

Addressing defaults SHALL use a separate, single-root model file:

```yaml
# network/addressing.yaml
addressing:
  ipv4Pool: 10.10.0.0/16
```

Logical networks SHALL carry explicit CIDRs:

```yaml
# network/networks.yaml
networks:

  dmz:
    site: lab
    purpose: External client access
    subnet:
      cidr: 10.10.10.0/24

  internal:
    site: lab
    purpose: Internal platform communication
    subnet:
      cidr: 10.10.20.0/24

  database:
    site: lab
    purpose: Database communication
    subnet:
      cidr: 10.10.30.0/24
```

The enclosing pool expresses the default address space available to the
platform. Explicit CIDRs express the current stable subnet allocation.

The Platform Model SHALL NOT contain deployment-specific values such as Linux
interface names, Docker drivers, Docker parent interfaces, Docker allocation
ranges, RouterOS interface names, AWS resource identifiers, or
provider-specific gateway behaviour.

### Model File Structure

Model files SHALL retain the existing single-root, self-describing YAML
convention. `addressing` is therefore a separate network-domain object rather
than a second root key in `networks.yaml`.

### Deployment Realization

A Deployment Realization SHALL describe how a Platform Model is implemented in
a particular environment.

A realization MAY override selected addressing defaults. If it overrides
network addressing, it SHALL provide a complete and internally consistent
effective configuration. Changing only the enclosing pool SHALL NOT implicitly
renumber explicit network CIDRs.

A realization SHALL contain backend-specific information that cannot be
derived from the Platform Model.

For the local Docker lab, currently proven realization-specific information is:

- `macvlan` as the Docker network driver;
- mapping logical networks to Ubuntu parent interfaces;
- Docker-specific allocation ranges inside resolved logical subnets.

RouterOS-specific fields SHALL be deferred until the Terraform/RouterOS
prototype demonstrates which values are actually required.

## Addressing Resolution

The effective addressing SHALL be established during resolution/normalization
before generators execute.

```text
Platform Model addressing defaults
             +
Realization addressing overrides
             |
             v
Resolved network addressing
```

The initial implementation SHALL support one realization override layer only.
Hierarchical inheritance across global, region, availability-zone, site,
device-role, or device scopes is deferred.

This leaves a future path toward NetBox Config Context-like inheritance without
implementing such a hierarchy prematurely.

## Subnet Allocation

The initial implementation SHALL use explicit network CIDRs.

The framework SHALL NOT derive subnet assignments from:

- YAML declaration order;
- sequential subnet numbering;
- assumptions that all logical networks have the same prefix length.

For example, a real platform may legitimately contain `/22`, `/25`, `/27`, and
other differently sized networks.

Automatic subnet allocation from a larger pool is considered an IPAM concern.
A future NetBox/IPAM integration MAY allocate or validate network CIDRs from an
enclosing pool.

Generators SHALL consume resolved CIDRs and SHALL NOT independently allocate
logical subnets.

## Addressing Validation

The semantic validation layer SHOULD eventually validate relationships that are
not appropriately expressed by the structural schema, including:

- network CIDRs are valid IP networks;
- network CIDRs are contained within the enclosing pool;
- logical network CIDRs do not overlap;
- backend-specific allocation ranges are contained within their resolved
  logical subnet;
- backend-specific ranges avoid addresses reserved by the selected backend.

These checks are implementation work and are not required merely to introduce
the model fields.

## Endpoint Address Allocation

The Platform Model SHALL NOT assign individual workload IP addresses by
default. It describes network membership.

Endpoint IP allocation SHALL normally be delegated to the deployment backend or
its IPAM mechanism, for example Docker IPAM, AWS private-IP allocation, Hetzner
private-network allocation, or Kubernetes CNI/IPAM.

Explicit workload addresses may be introduced later if a concrete use case
requires them.

## Backend-Specific Allocation Ranges

A backend MAY require a restricted allocation range within a logical subnet.
Such a range is realization-specific.

The realization SHOULD express this relative to the resolved logical subnet
when practical rather than duplicating an absolute CIDR derived from generic
addressing.

Allocation policy SHALL be network-specific. The design SHALL NOT assume equal
logical subnet sizes or identical backend allocation requirements.

For example, a future Docker realization may use:

```yaml
docker:
  networks:

    dmz:
      driver: macvlan
      parent: enp0s2
      ipam:
        offset: 128
        prefixLength: 28

    internal:
      driver: macvlan
      parent: enp0s3
      ipam:
        offset: 512
        prefixLength: 26
```

The exact realization schema is deferred until the first realization file is
finalized.

## Gateway Semantics

A concrete gateway address SHALL NOT be assumed to be a universal Platform
Model property.

Gateway behaviour differs between deployment technologies. RouterOS may
explicitly configure an address on an interface; cloud platforms may provide
provider-managed routing and reserved addresses; Kubernetes may delegate these
semantics to its CNI implementation.

Gateway behaviour SHALL therefore be handled according to backend semantics.

## Generator Input

Generators SHOULD consume a resolved representation rather than independently
implementing model/realization precedence.

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

## Consequences

### Advantages

- Platform intent remains provider-independent.
- Local-lab details do not contaminate the domain model.
- Explicit CIDRs support heterogeneous subnet sizes.
- Addressing remains stable when networks are added or reordered.
- Addressing defaults can be overridden per deployment environment.
- The framework does not duplicate IPAM responsibilities.
- Generators receive consistent resolved topology.
- The design leaves a clean path toward NetBox-backed IPAM and hierarchical
  configuration.

### Trade-offs

- Network CIDRs currently need explicit assignment.
- A realization input must be loaded and validated.
- A resolution/normalization stage is required.
- Configuration precedence must be defined explicitly.
- More than one input contributes to the generated artifact.
- Changing the enclosing pool does not automatically renumber explicit CIDRs.

## Deferred Decisions

The following are intentionally deferred:

- automatic subnet allocation from address pools;
- NetBox/IPAM-backed subnet allocation;
- hierarchical realization inheritance;
- NetBox Config Context integration;
- RouterOS-specific realization schema;
- explicit host/workload IP allocation;
- IPv6 allocation;
- multiple address pools;
- dynamic/stateful IPAM;
- provider-specific gateway policy;
- exact Docker realization schema.

## Initial Model Changes

The Out-Dialer model introduces:

```yaml
# addressing.yaml
addressing:
  ipv4Pool: 10.10.0.0/16
```

and:

```yaml
# networks.yaml
networks:

  dmz:
    site: lab
    purpose: External client access
    subnet:
      cidr: 10.10.10.0/24

  internal:
    site: lab
    purpose: Internal platform communication
    subnet:
      cidr: 10.10.20.0/24

  database:
    site: lab
    purpose: Database communication
    subnet:
      cidr: 10.10.30.0/24
```

This preserves the proven local-lab addressing without assuming equal subnet
sizes or implementing automatic subnet allocation.

## Initial Local-Lab Realization

The first realization is expected at:

```text
models/out-dialer/realizations/local-lab.yaml
```

It will initially contain only realization-specific values demonstrated as
necessary by the working Docker/UTM prototype.

The exact Docker IPAM representation will be finalized before its schema and
loader are implemented. RouterOS-specific fields will be added only after the
Terraform prototype demonstrates their requirements.
