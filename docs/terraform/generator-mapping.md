# Terraform Generator Mapping

This document specifies how the resolved Platform Model and deployment
realization are transformed into Terraform resources for RouterOS.

Every generated value must originate from one of four sources:

- Platform Model
- Deployment Realization
- Resolver-derived value
- RouterOS/Terraform backend convention

The generator must not invent deployment-specific data outside those sources.

## Interface Mapping

| Terraform Resource / Attribute | Source | Transformation | Notes |
|---|---|---|---|
| `routeros_interface_ethernet.<network>` | Platform Model | network name -> Terraform resource name | `dmz`, `internal`, `database` |
| `name` | Platform Model | copy logical network name | RouterOS interface name |
| `factory_name` | Realization | logical network -> physical interface | e.g. `dmz -> ether1` |

## Gateway Address Mapping

| Terraform Resource / Attribute | Source | Transformation | Notes |
|---|---|---|---|
| `routeros_ip_address.<network>_gateway` | Platform Model | one resource per routed logical network | |
| `interface` | Platform Model | copy logical network name | |
| `address` | Resolver | first usable address of CIDR, retaining prefix | `10.10.10.0/24 -> 10.10.10.1/24` |
| `comment` | Backend convention | `<Network> gateway` | Human-readable |

## Firewall Address List Mapping

| Terraform Resource / Attribute | Source | Transformation | Notes |
|---|---|---|---|
| `routeros_ip_firewall_addr_list.<network>` | Platform Model | one entry per logical network | |
| `address` | Resolved network | copy network CIDR | |
| `list` | Backend convention | `lab-networks` | Current RouterOS implementation |
| `comment` | Platform Model | derive from network identity | |

## Firewall Policy Mapping

| Terraform Resource / Attribute | Source | Transformation | Notes |
|---|---|---|---|
| resource name | Platform Model policy name | convert to Terraform-safe identifier | |
| `chain` | Backend convention | semantic `trafficScope=transit` -> `forward` | RouterOS-specific terminology |
| `action` | Platform Model policy | `allow -> accept`, `deny -> drop` | |
| `src_address` | Resolver | `from` network reference -> CIDR | |
| `dst_address` | Resolver | `to` network reference -> CIDR | |
| `comment` | Platform Model policy | copy `description` | |
| `connection_state` | Backend convention | emit baseline stateful rules | Not user policy intent |
| `src_address_list` | Backend convention | `lab-networks` | Used by default inter-zone deny |
| `dst_address_list` | Backend convention | `lab-networks` | Used by default inter-zone deny |
| `log` | Backend convention | enable on final deny | |
| `log_prefix` | Backend convention | `LAB-DENY ` | Diagnostic only |

## Firewall Rule Ordering

RouterOS firewall order is semantically significant.

The generator must emit rules deterministically in this order:

1. Accept established/related/untracked traffic.
2. Drop invalid traffic.
3. Emit Platform Model policies in deterministic model order.
4. Drop all remaining inter-zone traffic.

The baseline and final deny rules are RouterOS backend conventions. They are
not represented as individual Platform Model policies.

## Management Interface

The CHR management interface and its DHCP client are treated as bootstrap
infrastructure and are not managed by the initial Terraform generator.

Terraform requires management connectivity to RouterOS before it can operate.

## Known Provider Behaviour

Imported `routeros_interface_ethernet` resources expose `default_name` in
state, while configured `factory_name` may continue to appear as an in-place
update in `terraform plan`.

This behaviour is treated as a provider/import characteristic and must be
understood before generated Terraform is allowed to apply interface changes.