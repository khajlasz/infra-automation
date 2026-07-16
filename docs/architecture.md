# Architecture

## Purpose and Status

This document describes the target logical architecture for the infrastructure
automation project and the current Terraform prototype that supports it.

The target design uses a declarative infrastructure model as its primary source
of truth. The model is validated and used to generate artifacts for deployment
tools. The current implementation is an early AWS networking prototype; it does
not yet model the sites, services, or security zones described below.

## Design Principles

- Define infrastructure data once in a tool-independent model.
- Validate the model before creating deployment artifacts.
- Keep the logical topology independent from a specific cloud provider.
- Use generated artifacts for Terraform and Ansible rather than maintaining
  their inputs independently.

## Logical Topology

The target topology consists of two locations: Warsaw and Stockholm. Each
location represents a separate data centre or availability zone.

All service types are intended to have one instance in each location, except
for NFM, which is deployed as a single instance in Warsaw. The exact HA,
failover, and recovery behaviour remains to be defined.

## Service Types and Placement

| Service | Responsibility | Warsaw | Stockholm |
| --- | --- | --- | --- |
| AS | Service execution | One instance | One instance |
| NS | Call routing | One instance | One instance |
| MS | Media handling | One instance | One instance |
| XSP | Web portal and cloud interconnections | One instance | One instance |
| NFM | Licensing, alarms, performance, and software management | One instance | Not deployed |

In this document, an *instance* is a logical service deployment. Its eventual
implementation as one host, a virtual machine, or an HA pair is an open design
decision.

## Security Zones and Networks

| Zone | Networks | Purpose |
| --- | --- | --- |
| Core / Control | `signalling`, `replication`, `media` | Internal signalling, state replication, and media traffic |
| DMZ | `dmz-int`, `dmz-ext` | Internal and external demilitarized-zone traffic |
| Operations, Administration, and Maintenance (OAM) | `core-oam`, `dmz-oam` | Management connectivity for core and DMZ services |

CIDR ranges, subnet boundaries, and routing policies are not yet defined. They
should be specified in the infrastructure model rather than embedded in the
deployment tools.

## Service Interface Matrix

| Service | Connected networks |
| --- | --- |
| AS | `signalling`, `replication`, `core-oam` |
| NS | `signalling`, `replication`, `core-oam` |
| MS | `signalling`, `replication`, `media`, `core-oam` |
| XSP | `dmz-oam`, `dmz-int`, `dmz-ext` |
| NFM | `core-oam` |

The future validation schema should enforce this matrix so that unsupported
interfaces cannot be added to a service type accidentally.

## Network Elements and Connectivity

| Network element | Connected networks | Role |
| --- | --- | --- |
| Internal switch | `signalling`, `replication`, `media` | Connects internal core/control traffic |
| External switch | `dmz-int`, `dmz-ext`, `dmz-oam` | Connects DMZ traffic |
| OAM switch | `core-oam` | Connects core management traffic |
| Firewall | `replication`, `dmz-int`, `dmz-ext`, `dmz-oam`, `core-oam` | Enforces traffic policy between connected networks |

Firewall rules, permitted source/destination flows, and inter-site routing have
not yet been defined. They should be captured as explicit policy in the model
and translated into provider-specific controls.

## Source of Truth and Automation Flow

As established in [ADR-001](../adr/ADR-001.md), the infrastructure model is the
primary source of truth. Validation schemas are maintained separately, and
deployment tools consume generated artifacts.

```text
Infrastructure model
        |
        v
Schema validation
        |
        v
Artifact generation
   |             |
   v             v
Terraform      Ansible
```

## Current Terraform Implementation Mapping

The Terraform prototype currently deploys AWS networking in `eu-central-1`:

| Resource | Configuration | Target-architecture relationship |
| --- | --- | --- |
| Production VPC | `enterprise-prod-vpc`, `10.10.0.0/16`, subnet `10.10.1.0/24` | Prototype environment; not yet mapped to a site or security zone |
| Development VPC | `enterprise-dev-vpc`, `10.20.0.0/16`, subnet `10.20.1.0/24` | Prototype environment; not yet mapped to a site or security zone |
| Transit Gateway | `central-core-tgw` with VPC attachments | Prototype core routing; not yet a representation of the logical switches or firewall |

Terraform currently contains direct CIDR and resource values. Those values are
temporary prototype inputs and should ultimately be generated from the validated
infrastructure model.

## Open Decisions

- Define HA, failover, and disaster-recovery behaviour for each service.
- Define the CIDR plan and subnet allocation per site and security zone.
- Define firewall policy and allowed traffic flows.
- Define inter-site connectivity and replication behaviour.
- Map logical sites and network elements to AWS accounts, regions, VPCs, and
  availability zones (or to physical data centres).
- Define the model, schemas, generators, and Ansible artifacts required to
  implement the model-driven workflow.
