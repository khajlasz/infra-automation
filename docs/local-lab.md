# Local Reference Lab

## Status

**Current lab baseline:** 2026-09-27

This document is the source of truth for the project-specific local
infrastructure used to exercise `infra-automation` deployment realizations.

The lab is intentionally separate from the provider-independent Platform Model.
It describes the environment in which generated artifacts are executed and
validated.

The original networking experiments remain documented in
`docs/vm-connectivity-prototype.md`.

## Ownership Boundary

The local reference lab belongs to this repository because it exists
specifically to develop and validate `infra-automation`.

The project currently assumes that UTM virtual machines and UTM virtual
networks already exist. Creating those objects is a lab bootstrap prerequisite,
not a responsibility of the Platform Model or its generators.

Generic developer-workstation configuration remains outside this repository.

The current ownership boundary is:

```text
UTM
  VM and virtual-network bootstrap
        |
        v
Terraform
  RouterOS/network realization
        |
        v
Linux hosts
  manually configured today
  candidate for Ansible automation
        |
        v
Runtime realization
  Docker today
  Kubernetes under preparation
```

## Host Platform

- Apple Silicon MacBook Pro
- UTM on macOS
- macOS acts as the development workstation and automation control plane
- RouterOS CHR runs as an x86-64 QEMU guest
- Ubuntu lab VMs run as ARM64 QEMU guests with macOS Hypervisor acceleration

For ARM64 Ubuntu QEMU VMs, UTM's **Hypervisor** option must be enabled. This
keeps the QEMU device model required by the lab while using hardware-assisted
CPU virtualization. Running the same ARM64 guests without Hypervisor
acceleration was observed to cause extremely slow device discovery and
multi-minute boot times.

## Current Topology

The lab separates management/Internet access from the routed platform
data plane.

```text
                            macOS / UTM
                                 |
                    Management + Internet
                       192.168.64.0/24
                         gateway .64.1
                                 |
          +----------+-----------+-----------+-----------+-----------+
          |          |           |           |           |           |
       RouterOS   ubuntu-qemu   obs        k8s-c00     k8s-w00     k8s-w10
        .64.10      .64.20     .64.30      .64.40      .64.41      .64.42
          |
          | RouterOS routed platform fabric
          |
          +-- dmz             10.10.10.0/24
          +-- internal        10.10.20.0/24
          +-- database        10.10.30.0/24
          +-- observability   10.10.40.0/24
          +-- k8s-c0          10.10.50.0/24
          +-- k8s-w0          10.10.51.0/24
          +-- k8s-w1          10.10.52.0/24
```

## Management Network

Management uses the UTM **Shared Network**:

```text
Network             192.168.64.0/24
UTM gateway / DNS   192.168.64.1
RouterOS            192.168.64.10
ubuntu-qemu         192.168.64.20
observability       192.168.64.30
k8s-c00             192.168.64.40
k8s-w00             192.168.64.41
k8s-w10             192.168.64.42
```

The previous `172.31.255.0/24` host-only management network has been retired.

The Shared Network provides three functions:

- stable Mac-to-VM management connectivity;
- VM Internet access through UTM NAT;
- the default route and DNS path for Ubuntu lab VMs.

The management network is a bootstrap/lab concern. It is not part of the
provider-independent Platform Model.

## Platform Networks

The routed platform networks use named UTM Host Networks:

```text
dmz             10.10.10.0/24
internal        10.10.20.0/24
database        10.10.30.0/24
observability   10.10.40.0/24
k8s-c0          10.10.50.0/24
k8s-w0          10.10.51.0/24
k8s-w1          10.10.52.0/24
```

RouterOS owns `.1` on each routed platform subnet.

A critical UTM requirement for named Host Networks is:

```text
Isolate VM from Host = disabled
```

This was discovered while building the Kubernetes underlay. With isolation
enabled on the worker data-plane NICs, the interfaces were locally up but ARP
between the Ubuntu guests and RouterOS failed. Disabling isolation restored the
shared Layer-2 domain.

## Existing Docker / Out-Dialer Host

`ubuntu-qemu` remains the current Docker workload host.

Its management address is:

```text
192.168.64.20/24
```

Its platform interfaces attach to the existing DMZ, Internal and Database UTM
Host Networks:

```text
enp0s2   10.10.10.10/24   DMZ
enp0s3   10.10.20.10/24   Internal
enp0s4   10.10.30.10/24   Database
```

The existing Docker realization uses these networks through macvlan as
documented by the realization and generator mapping.

## Observability Host

The observability VM uses:

```text
Management       192.168.64.30/24
Observability    10.10.40.10/24
```

The observability stack remains external supporting infrastructure rather than
an Out-Dialer application workload.

## Kubernetes Underlay

The Kubernetes preparation lab currently contains three Ubuntu nodes:

```text
Node       Management       Data-plane network    Data-plane address
k8s-c00    192.168.64.40    k8s-c0                10.10.50.10/24
k8s-w00    192.168.64.41    k8s-w0                10.10.51.10/24
k8s-w10    192.168.64.42    k8s-w1                10.10.52.10/24
```

The naming convention encodes role and network placement:

```text
k8s-c00 = control-plane 0 on control-plane network 0
k8s-w00 = worker 0 on worker network 0
k8s-w10 = worker 0 on worker network 1
```

Each Kubernetes node therefore has two interfaces:

```text
enp0s1
  UTM Shared Network
  management + Internet
  default route via 192.168.64.1

enp0s2
  dedicated named UTM Host Network
  Kubernetes/lab traffic
  routed through RouterOS
```

The node routes to the other Kubernetes subnets through the local RouterOS
gateway:

```text
k8s-c00:
  10.10.51.0/24 via 10.10.50.1
  10.10.52.0/24 via 10.10.50.1

k8s-w00:
  10.10.50.0/24 via 10.10.51.1
  10.10.52.0/24 via 10.10.51.1

k8s-w10:
  10.10.50.0/24 via 10.10.52.1
  10.10.51.0/24 via 10.10.52.1
```

RouterOS has directly connected interfaces on all three networks, so no static
routes between the Kubernetes subnets are required on RouterOS.

Kubernetes itself has not yet been installed. The current objective is to
establish and understand the underlay before introducing kubeadm, containerd,
CNI behavior, or a Kubernetes deployment realization.

## RouterOS Kubernetes Policy

The three Kubernetes networks are members of the RouterOS
`k8s-networks` address list:

```text
10.10.50.0/24   k8s-c0
10.10.51.0/24   k8s-w0
10.10.52.0/24   k8s-w1
```

They are also members of the broader `lab-networks` address list.

Inter-node Kubernetes traffic is explicitly permitted before the terminal
inter-zone deny:

```routeros
chain=forward action=accept     src-address-list=k8s-networks     dst-address-list=k8s-networks     comment="LAB: allow inter-Kubernetes-node traffic"
```

No NAT is used between the Kubernetes node networks.

Internet egress for the Ubuntu nodes uses their management interfaces and the
UTM Shared Network rather than RouterOS.

## Ubuntu Network Configuration Pattern

Ubuntu lab VMs use static management addresses. The management interface owns
the default route and DNS configuration:

```yaml
enp0s1:
  dhcp4: false
  dhcp6: false
  addresses:
    - 192.168.64.X/24
  routes:
    - to: default
      via: 192.168.64.1
  nameservers:
    addresses:
      - 192.168.64.1
```

Data-plane interfaces use static addresses and do not own the default route.

For Kubernetes nodes, explicit routes to the other Kubernetes node networks
are installed through the RouterOS address on the node's local data-plane
segment.

## Management Access

The Mac uses OpenSSH host aliases in `~/.ssh/config` so operational commands
do not depend on remembering management addresses.

The current aliases are:

```text
routeros   192.168.64.10
qemu       192.168.64.20
obs        192.168.64.30
c00        192.168.64.40
w00        192.168.64.41
w10        192.168.64.42
```

Examples:

```bash
ssh routeros
ssh qemu
ssh obs
ssh c00
ssh w00
ssh w10
```

The Ubuntu hosts and RouterOS accept the Mac user's SSH public key. Private
keys and credentials are workstation state and must not be committed to this
repository.

## Verification

Useful underlay checks before Kubernetes installation include:

```bash
# From each Ubuntu node
ip addr
ip route

# Verify the local RouterOS gateway
ping <local-10.10.x.1>

# Verify routed Kubernetes node connectivity
ping <remote-node-10.10.x.10>
```

On RouterOS:

```routeros
/ip address print
/ip route print
/ip firewall address-list print where list=k8s-networks
/ip firewall filter print
```

The Kubernetes underlay is ready only when each node can reach the other nodes
through RouterOS and the expected firewall rule handles the traffic.

## Automation Boundary and Next Steps

Current automation responsibilities are deliberately incremental.

### Terraform

Terraform already configures RouterOS from the Platform Model and Out-Dialer
local-lab realization.

The manually added Kubernetes RouterOS state must be reconciled with the
model/realization/Terraform design before it is treated as generated desired
state. This includes:

- the three Kubernetes routed networks;
- RouterOS interface mappings and gateway addresses;
- `lab-networks` membership;
- `k8s-networks` membership;
- the Kubernetes inter-node firewall policy.

The exact ownership of these objects must follow the existing model versus
realization boundary rather than embedding UTM-specific implementation details
in the Platform Model.

### Ansible candidate

Linux host configuration is still manual. As the lab grows, Ansible is a
natural candidate for reproducible configuration of existing Ubuntu hosts.

A future structure may include:

```text
lab/
  ansible/
    inventory/
    group_vars/
    roles/
      ubuntu_base/
      kubernetes_node/
    site.yaml
```

Ansible should be introduced after the manual Kubernetes build has established
the required host configuration. That preserves the current learn-first,
automate-second workflow.

UTM VM creation and UTM Host Network creation remain bootstrap prerequisites
for now and should not be pulled into Ansible merely because the tool can
automate host configuration.

### Kubernetes realization

The Kubernetes cluster should first be built manually with kubeadm so its
runtime requirements are understood.

Only then should the project decide which Kubernetes-specific values belong in
a deployment realization and which artifacts a future Kubernetes generator
should produce.

The intended progression is:

```text
manual cluster build
        |
        v
understand runtime behavior
        |
        v
identify required inputs
        |
        v
assign model vs realization ownership
        |
        v
document architectural decisions
        |
        v
implement automation/generation
```

This follows the same empirical approach used for the Docker and RouterOS
backends.
