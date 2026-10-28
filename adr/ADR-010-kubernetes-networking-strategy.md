# ADR-010: Kubernetes Networking Strategy

## Status

Accepted

## Context

The Infrastructure Automation Framework describes deployment-independent platform intent and generates artifacts for different deployment technologies.

The Out-Dialer reference architecture defines logical security zones:

- DMZ
- Internal
- Database

In the existing Docker/RouterOS realization, these zones are implemented using separate Docker networks and MikroTik firewall rules. Inter-zone communication is explicitly controlled.

The Kubernetes realization introduces a different networking model:

- Pods receive IP addresses through the cluster CNI.
- Pods can communicate across Kubernetes nodes.
- Services provide stable endpoints and service discovery.
- Namespaces organize Kubernetes resources but do not provide network isolation by themselves.
- NetworkPolicies can restrict Pod ingress and egress when supported by the CNI.

The local Kubernetes lab uses kubeadm with Calico as its CNI. Calico supports Kubernetes NetworkPolicy enforcement.

The initial Kubernetes implementation is intended to validate the Platform Model, Deployment Realization, generator architecture, and controlled deployment workflow.

Reproducing the complete Docker/RouterOS network segmentation is not required for this initial milestone.

The architecture must nevertheless make this limitation explicit and avoid introducing Kubernetes-specific networking assumptions into the Platform Model.

## Decision

### Initial Kubernetes Networking Model

The initial Kubernetes realization SHALL use:

1. A single Kubernetes namespace, `out-dialer`, for Out-Dialer application workloads.
2. Kubernetes-native Pod networking provided by the installed CNI.
3. Kubernetes Services of type `ClusterIP` for internal application connectivity.
4. Kubernetes DNS for service discovery between application workloads.
5. CNI-managed Pod IP allocation without assigning fixed Pod addresses in the Platform Model.

Application workloads SHALL communicate using Kubernetes Service endpoints rather than relying on individual Pod IP addresses.

The initial Kubernetes generator SHALL NOT generate NetworkPolicy resources.

### Logical Security Zones

The logical DMZ, Internal, and Database zones remain part of the deployment-independent Platform Model.

The initial Kubernetes realization SHALL NOT automatically translate these zones into:

- separate Kubernetes namespaces;
- separate Pod subnets;
- Kubernetes NetworkPolicies;
- Calico-specific security policies;
- MikroTik firewall rules between Kubernetes workloads.

The presence of logical security zones in the Platform Model SHALL NOT imply that equivalent network isolation has been implemented in every deployment realization.

### MikroTik Responsibilities

MikroTik remains part of the local infrastructure and continues to provide routing and firewall functionality where traffic traverses the routed lab network.

The initial Kubernetes realization SHALL NOT require ordinary Pod-to-Pod or Service-to-Service traffic to traverse MikroTik.

External access to Kubernetes workloads SHALL be addressed separately through an appropriate cluster entry-point mechanism and the surrounding infrastructure network configuration.

The selection of an external exposure mechanism is outside the scope of this decision.

### Network Security

The initial Kubernetes realization does not provide security isolation equivalent to the existing Docker/RouterOS DMZ architecture.

Without applicable NetworkPolicies or other enforcement mechanisms, application workloads may communicate across logical security-zone boundaries.

This limitation SHALL be documented and SHALL NOT be represented as production-equivalent network segmentation.

Kubernetes NetworkPolicy generation is deferred until a subsequent networking/security milestone.

## Alternatives Considered

### Separate Namespaces for Security Zones

Mapping DMZ, Internal, and Database to separate Kubernetes namespaces would provide clearer administrative organization and support namespace-based policy selection.

However, namespaces alone do not enforce network isolation.

This option is deferred because it introduces additional realization and generator complexity without providing the required security boundary independently.

### Kubernetes NetworkPolicies from the Initial Milestone

Calico supports Kubernetes NetworkPolicies, allowing application communication to be restricted using Pod selectors, namespace selectors, and ports.

This is a valid production-oriented approach.

However, implementing policy generation immediately would require additional decisions concerning:

- translation of logical security zones into Kubernetes policy selectors;
- default-deny behavior;
- permitted application communication flows;
- DNS and infrastructure traffic exceptions;
- policy validation and runtime connectivity testing.

These concerns are deferred to keep the initial generator milestone focused on application deployment and service connectivity.

### Routing Inter-Application Traffic Through MikroTik

Routing Kubernetes application traffic through MikroTik could preserve the existing firewall-centric security model.

However, ordinary Kubernetes Pod networking does not guarantee that inter-Pod traffic traverses an external router.

Enforcing this architecture would require additional CNI, routing, or network-topology design.

This approach is not selected for the initial Kubernetes realization.

## Consequences

### Advantages

- The initial Kubernetes generator remains focused on standard Deployment and Service resources.
- The realization uses common Kubernetes networking and service-discovery mechanisms.
- The design avoids unnecessary dependencies on Calico-specific APIs.
- Pod IP addressing remains the responsibility of Kubernetes CNI/IPAM, consistent with ADR-008.
- The framework preserves the distinction between deployment-independent intent and deployment-specific implementation.
- The initial milestone can be validated without introducing network-security policy generation.

### Trade-offs

- The Kubernetes realization does not initially reproduce the Docker/RouterOS DMZ security boundary.
- Logical security zones are not enforced within the Kubernetes cluster.
- Additional security design and implementation will be necessary before claiming production-equivalent isolation.
- Future NetworkPolicy generation may require extensions to the Deployment Realization and semantic validation.

## Deferred Decisions

The following are intentionally deferred:

- Kubernetes NetworkPolicy generation;
- default-deny ingress and egress policies;
- mapping logical security zones to namespaces or Pod labels;
- application communication policy translation;
- Calico-specific policy resources;
- external ingress and gateway implementation;
- production network-isolation requirements;
- runtime validation of permitted and denied application traffic.

A future networking/security milestone SHALL review these decisions before implementing network segmentation.

## Related Decisions

- ADR-002: Reference Architectures
- ADR-007: Naming Conventions
- ADR-008: Deployment Realization and Addressing
- ADR-009: CI/CD Delivery Model

## Implementation Scope

This ADR governs the initial Kubernetes realization and generator.

It does not require changes to the existing Docker Compose or Terraform/RouterOS generators.

The Kubernetes generator mapping documentation SHALL reference this ADR and describe only the networking behavior required for the initial implementation.