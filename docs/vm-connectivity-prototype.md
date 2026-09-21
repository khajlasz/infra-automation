# UTM VM Connectivity Prototype

## Status

**Completed and verified:** 2026-08-13

This document records the working local networking prototype for the
`infra-automation` project. It is the empirical baseline for the next design
work on the Platform Model, Docker deployment realization, and Terraform
configuration of MikroTik RouterOS.

The prototype proves that containers running on one Ubuntu Docker host can be
placed on separate Layer-2 networks and communicate across a dedicated
RouterOS router/firewall. RouterOS performs both inter-network routing and
stateful policy enforcement.

## Purpose

The long-term project objective is:

```text
Platform Model
    ├── Docker Compose generator -> application workloads
    └── Terraform generator      -> RouterOS network infrastructure
```

Before designing the Terraform backend or changing the model, the lab needed
to answer several practical questions:

1. Can RouterOS run on an Apple Silicon Mac under UTM?
2. Can the Ubuntu and RouterOS VMs share controlled, isolated networks?
3. Can Docker containers appear directly on those networks?
4. Does traffic between containers cross RouterOS rather than the Ubuntu host?
5. Can RouterOS enforce stateful policy between the networks?

All five questions have been answered successfully.

## Architectural Boundary

UTM VM creation and base operating-system installation are lab prerequisites,
not responsibilities of `infra-automation`.

The project may configure the existing RouterOS instance and generate workload
deployment artifacts, but it does not create:

* the UTM VMs;
* the Ubuntu operating system;
* the RouterOS VM disk;
* the UTM Host Networks;
* the initial Docker installation.

This mirrors a real environment in which compute hosts, network devices, and
physical or virtual Layer-2 connectivity exist before platform automation is
applied.

## Host and VM Architecture

### Host

* Apple Silicon MacBook Pro M3
* UTM on macOS

### Ubuntu Docker host

* VM name: `ubuntu-qemu`
* Guest architecture: ARM64 (`aarch64`)
* UTM backend: QEMU
* QEMU machine: ARM Virtual Machine (`virt`)
* Hardware acceleration: macOS Hypervisor enabled
* Operating system: Ubuntu Server 26.04 ARM64
* Resources used in the prototype: 2 vCPU, 4 GiB RAM

### MikroTik router

* VM name: `routerOS`
* Operating system: MikroTik RouterOS CHR 7.23.3
* Guest architecture: x86-64
* UTM backend: QEMU using x86-64 emulation
* Resources used in the prototype: 1 vCPU, 512 MiB RAM
* Boot disk: official CHR RAW image imported by UTM as QCOW2
* Disk interface: IDE
* Network adapter model: Intel e1000

### Important compatibility finding

MikroTik CHR supports x86-64, not ARM64. Consequently, CHR must run through
QEMU x86-64 emulation on Apple Silicon. It cannot run through native Apple
Virtualization as an ARM64 guest.

The original Ubuntu VM used Apple Virtualization. Its UTM Shared Network was
different from the QEMU Shared Network used by CHR:

```text
Apple Virtualization Shared Network: 192.168.65.0/24
QEMU Shared Network:                 192.168.64.0/24
```

Those backend-specific shared networks could not provide VM-to-VM
connectivity. Bridging both VMs to the physical LAN proved cross-backend
connectivity, but Apple Virtualization did not expose the named QEMU Host
Networks required for multiple isolated segments.

A second ARM64 Ubuntu VM was therefore created with the QEMU backend and
hardware acceleration. This combines near-native ARM64 execution with access
to QEMU Host Networks.

## Final Topology

The lab now separates the **bootstrap/management plane** from the
**platform/data plane**.

```text
                         Bootstrap / Management
                            172.31.255.0/24
                                   |
                  +----------------+----------------+
                  |                                 |
               macOS                           RouterOS CHR
            172.31.255.1                       172.31.255.10
                  |                                 |
                  |                        routing + firewall
                  |                                 |
                  |             Platform / Data Plane
                  |                                 |
                  |       +-------------+-----------+-------------+
                  |       |             |                         |
                  |      DMZ         Internal                 Database
                  | 10.10.10.0/24 10.10.20.0/24          10.10.30.0/24
                  |                     |
                  |                     |
                  |              Observability
                  |             10.10.40.0/24
                  |
          automation control
              plane
```
The platform/data-plane networks carry modeled application and
observability traffic:
```text
DMZ             10.10.10.0/24
Internal        10.10.20.0/24
Database        10.10.30.0/24
Observability   10.10.40.0/24
```
The bootstrap/management network is deliberately separate:
```text
Management      172.31.255.0/24
macOS host      172.31.255.1
RouterOS        172.31.255.10
```

In the original prototype, VM management interfaces were bridged to the
physical LAN and received addresses through that LAN's DHCP service. This
worked but made automation dependent on the network to which the MacBook was
currently connected.

The management path was therefore migrated to a dedicated UTM host-only
network. RouterOS now has the stable management address
`172.31.255.10/24`, allowing Terraform and the self-hosted GitHub Actions
runner to reach it independently of the current Wi-Fi or physical LAN.

The management network is a lab/bootstrap prerequisite. It is not part of the
provider-independent Platform Model.

## UTM Host Networks

The lab uses two different UTM networking mechanisms because the management
and platform networks have different requirements.

### Platform networks

Named global UTM Host Networks provide shared Layer-2 domains for the
platform/data-plane networks:

| UTM Host Network | IPv4 subnet     | Purpose                                     |
| ---------------- | --------------- | ------------------------------------------- |
| `dmz`            | `10.10.10.0/24` | Externally facing/application edge services |
| `internal`       | `10.10.20.0/24` | Internal application services               |
| `database`       | `10.10.30.0/24` | Data services                               |
| `observability`  | `10.10.40.0/24` | External observability services             |

These networks must be shared between the relevant VMs and therefore use
named UTM Host Networks.

The initial prototype network was created as `lab-net` and later renamed to
`dmz`. Its UTM UUID at the time of testing was:

```text
B6A04FFC-602A-4DDA-951F-C01D90670A42
```

Addresses on the platform networks are assigned explicitly in Ubuntu,
RouterOS, Docker IPAM, or the corresponding deployment realization.

### Management network

Management uses a different UTM mechanism:
```text
Network Mode:    Host Only
Host Network:    Default (private)
Guest Network:   172.31.255.0/24
Host isolation:  disabled
```
This creates stable host-to-guest connectivity without depending on the
physical LAN.

The verified RouterOS management path is:
```text
macOS / UTM host    172.31.255.1
        |
        | UTM Host Only
        |
RouterOS             172.31.255.10
```
UTM may also assign a dynamic guest address on this network. RouterOS uses
the explicitly configured 172.31.255.10/24 address as its stable automation
endpoint.

The distinction between the two UTM mechanisms is intentional:
```text
Default (private) Host Only
    -> bootstrap and host-to-VM management

Named UTM Host Networks
    -> shared Layer-2 platform/data-plane segments
```
The management network is outside the Platform Model and deployment
realization because it provides the bootstrap path through which the
automation reaches the infrastructure it manages.

## Original Prototype Interface and Address Inventory

The following inventory records the original physical-LAN management
configuration used when the connectivity prototype was first verified.

The current RouterOS automation endpoint is instead the stable UTM host-only
address `172.31.255.10/24` described in the management-network section above.

### Ubuntu

| Network    | Interface | MAC address         | Address              |
| ---------- | --------- | ------------------- | -------------------- |
| Management | `enp0s1`  | `16:7d:9e:fb:56:92` | DHCP on physical LAN |
| DMZ        | `enp0s2`  | `72:8f:a2:6a:6e:8e` | `10.10.10.10/24`     |
| Internal   | `enp0s3`  | `1a:e9:56:25:f8:5b` | `10.10.20.10/24`     |
| Database   | `enp0s4`  | `26:76:d6:42:da:72` | `10.10.30.10/24`     |

### RouterOS

| Network    | RouterOS interface | MAC address         | Address              |
| ---------- | ------------------ | ------------------- | -------------------- |
| Management | `ether1`           | `EA:44:E4:7C:67:96` | DHCP on physical LAN |
| DMZ        | `dmz`              | `0E:12:F9:FC:30:31` | `10.10.10.1/24`      |
| Internal   | `internal`         | `3A:41:CA:23:AC:D8` | `10.10.20.1/24`      |
| Database   | `database`         | `3A:5E:BB:17:BA:6E` | `10.10.30.1/24`      |

The MAC addresses are the stable lab identity. Interface names were explicitly
matched or renamed so that UTM device enumeration cannot silently exchange the
logical networks.

## Ubuntu Persistent Network Configuration

Ubuntu uses Netplan. The verified configuration is equivalent to:

```yaml
network:
  ethernets:
    enp0s1:
      dhcp4: true
      dhcp6: true
      match:
        macaddress: 16:7d:9e:fb:56:92
      set-name: enp0s1

    enp0s2:
      addresses:
        - 10.10.10.10/24
      dhcp4: false
      dhcp6: false
      match:
        macaddress: 72:8f:a2:6a:6e:8e
      set-name: enp0s2

    enp0s3:
      addresses:
        - 10.10.20.10/24
      dhcp4: false
      dhcp6: false
      match:
        macaddress: 1a:e9:56:25:f8:5b
      set-name: enp0s3

    enp0s4:
      addresses:
        - 10.10.30.10/24
      dhcp4: false
      dhcp6: false
      match:
        macaddress: 26:76:d6:42:da:72
      set-name: enp0s4

  version: 2
```

No default routes or DNS servers are configured on the application interfaces.
Ubuntu retains its default route through `enp0s1` on the management LAN.

The configuration survived reboot and all three RouterOS gateway addresses
remained reachable.

## RouterOS Network Configuration

The effective RouterOS configuration was created manually as follows:

```routeros
/interface ethernet set [find mac-address=0E:12:F9:FC:30:31] name=dmz
/interface ethernet set [find mac-address=3A:41:CA:23:AC:D8] name=internal
/interface ethernet set [find mac-address=3A:5E:BB:17:BA:6E] name=database

/ip address add address=10.10.10.1/24 interface=dmz comment="DMZ gateway"
/ip address add address=10.10.20.1/24 interface=internal comment="Internal gateway"
/ip address add address=10.10.30.1/24 interface=database comment="Database gateway"
```

RouterOS automatically installed connected routes for all three subnets.
No static routes were required.

## Management and Automation Control Plane

The macOS host acts as both the development workstation and the trusted
self-hosted GitHub Actions runner for local-lab delivery.

Terraform reaches RouterOS through the dedicated management network:

```text
GitHub
   |
   | trusted main workflow
   v
Self-hosted GitHub Actions runner
macOS
172.31.255.1
   |
   | HTTPS / RouterOS REST API
   | UTM Host Only
   v
RouterOS CHR
172.31.255.10:443
   |
   v
Platform networks
```

This management path is deliberately independent of the physical network to
which the MacBook is connected.

### RouterOS REST API

Terraform uses the RouterOS REST API over HTTPS.

The RouterOS `www-ssl` service must therefore be enabled and available on
TCP port 443.

The lab currently uses a locally issued RouterOS TLS certificate. The lab CA
is not installed as a trusted CA for the Terraform execution environment, so
certificate verification is currently disabled for this isolated lab.

This is a lab-specific compromise rather than a general production
recommendation. A future improvement can install and trust the lab CA and
remove the insecure provider setting.

### Terraform RouterOS environment

The RouterOS Terraform provider is configured through environment variables:
```text
ROS_HOSTURL=https://172.31.255.10
ROS_USERNAME=<RouterOS automation username>
ROS_PASSWORD=<RouterOS automation password>
ROS_INSECURE=true
```

`ROS_USERNAME` and `ROS_PASSWORD` are credentials and must not be committed
to the repository.

For GitHub Actions they are stored as repository Actions secrets:
```text
ROS_HOSTURL
ROS_USERNAME
ROS_PASSWORD
```
`ROS_INSECURE` is not a credential and may be set directly by the trusted
local-lab workflow:
```yaml
env:
  ROS_HOSTURL: ${{ secrets.ROS_HOSTURL }}
  ROS_USERNAME: ${{ secrets.ROS_USERNAME }}
  ROS_PASSWORD: ${{ secrets.ROS_PASSWORD }}
  ROS_INSECURE: "true"
```
Terraform state is stored outside the repository. The local-lab workflow
receives its location through:
```text
LOCAL_LAB_STATE_PATH
```
and initializes the backend with:
```sh
terraform init -reconfigure \
  -backend-config="path=${LOCAL_LAB_STATE_PATH}"
```
The exact state path and credentials are runtime configuration and are not
part of the Platform Model.

### macOS Local Network access

During self-hosted runner setup, Terraform executed as the normal macOS user
was initially unable to reach the RouterOS management endpoint even though
the route and direct host connectivity were valid.

The observed behavior was:
```text
terraform plan             -> no route to host
sudo -E terraform plan     -> succeeds
```
Running Terraform as root was not adopted as the solution because the
self-hosted CI runner should not require root privileges.

The dedicated lab management subnet was instead allowed through the macOS
Local Network privacy configuration:
```sh
sudo defaults write com.apple.network.local-network \
  AllowedEthernetLocalNetworkAddresses \
  -array "172.31.255.0/24"

sudo defaults write com.apple.network.local-network \
  AllowedWiFiLocalNetworkAddresses \
  -array "172.31.255.0/24"
```
The Mac was restarted after applying the configuration.

After restart:
```
terraform plan
```
successfully reached RouterOS as the normal user.

This configuration is therefore part of the workstation bootstrap required
for the trusted self-hosted GitHub Actions runner.

### Delivery trust boundary

Pull-request CI and local-lab delivery intentionally operate across different
trust boundaries:
```
Feature branch
      |
      v
Pull Request
      |
      v
GitHub-hosted CI
tests / validation / generation
no local-lab credentials
      |
      v
Human review + merge
      |
      v
main
      |
      v
Self-hosted macOS runner
      |
      +-- local Terraform state
      +-- RouterOS credentials
      +-- local-lab network access
      |
      v
RouterOS
```
Feature-branch workflow definitions are therefore not used to execute
privileged local-lab operations. Changes to the delivery workflow pass through
Pull Request CI and review before the merged main workflow runs on the
trusted self-hosted runner.

## Docker Network Realization

Docker uses a macvlan network on each Ubuntu application interface. This gives
every container its own MAC address and makes it a first-class endpoint on the
corresponding UTM Layer-2 segment.

### DMZ

```bash
docker network create \
  --driver macvlan \
  --subnet 10.10.10.0/24 \
  --gateway 10.10.10.1 \
  --ip-range 10.10.10.128/28 \
  --opt parent=enp0s2 \
  dmz-net
```

### Internal

```bash
docker network create \
  --driver macvlan \
  --subnet 10.10.20.0/24 \
  --gateway 10.10.20.1 \
  --ip-range 10.10.20.128/28 \
  --opt parent=enp0s3 \
  internal-net
```

### Database

```bash
docker network create \
  --driver macvlan \
  --subnet 10.10.30.0/24 \
  --gateway 10.10.30.1 \
  --ip-range 10.10.30.128/28 \
  --opt parent=enp0s4 \
  database-net
```

The `/28` ranges reserve addresses `128-143` in each subnet for Docker while
leaving the remaining addresses available for infrastructure or future
allocation schemes.

### Test containers

```bash
docker run -d --name dmz-test \
  --network dmz-net --ip 10.10.10.130 \
  alpine sleep infinity

docker run -d --name internal-test \
  --network internal-net --ip 10.10.20.130 \
  alpine sleep infinity

docker run -d --name database-test \
  --network database-net --ip 10.10.30.130 \
  alpine sleep infinity
```

### macvlan operational characteristic

By default, an Ubuntu host cannot communicate directly with macvlan children
attached to its own parent interface. This is normal macvlan behavior, not a
routing failure. Containers can communicate with RouterOS, and inter-network
container traffic is routed through RouterOS.

If host-to-container communication is required later, a dedicated macvlan host
interface can be added. That was not necessary for this prototype.

## Verified Routing Evidence

The following paths were verified:

* container to RouterOS gateway within DMZ;
* container to RouterOS gateway within Internal;
* container to RouterOS gateway within Database;
* DMZ container to Internal container;
* Internal container to DMZ container before firewall enforcement;
* Internal container to Database container;
* DMZ container to Database container before firewall enforcement.

Same-subnet ICMP replies arrived with TTL 64. Cross-subnet replies arrived with
TTL 63, showing that a router decremented the TTL.

Traceroute provided explicit path evidence:

```text
traceroute from 10.10.10.130 to 10.10.20.130

1  10.10.10.1
2  10.10.20.130
```

This proves that the Linux host did not route the container traffic directly;
the first hop was the RouterOS DMZ gateway.

## Stateful Firewall Policy

### Intended prototype policy

| Initiator                 | Destination        | Result               |
| ------------------------- | ------------------ | -------------------- |
| DMZ                       | Internal           | Allow                |
| Internal                  | Database           | Allow                |
| DMZ                       | Database           | Deny                 |
| Internal                  | DMZ                | Deny new connections |
| Database                  | Internal           | Deny new connections |
| Established reply traffic | Original initiator | Allow                |

### RouterOS configuration

```routeros
/ip firewall address-list add list=lab-networks address=10.10.10.0/24 comment="DMZ"
/ip firewall address-list add list=lab-networks address=10.10.20.0/24 comment="Internal"
/ip firewall address-list add list=lab-networks address=10.10.30.0/24 comment="Database"

/ip firewall filter add chain=forward \
    connection-state=established,related,untracked \
    action=accept \
    comment="LAB: allow established and related"

/ip firewall filter add chain=forward \
    connection-state=invalid \
    action=drop \
    comment="LAB: drop invalid"

/ip firewall filter add chain=forward \
    src-address=10.10.10.0/24 \
    dst-address=10.10.20.0/24 \
    action=accept \
    comment="LAB: allow DMZ to Internal"

/ip firewall filter add chain=forward \
    src-address=10.10.20.0/24 \
    dst-address=10.10.30.0/24 \
    action=accept \
    comment="LAB: allow Internal to Database"

/ip firewall filter add chain=forward \
    src-address-list=lab-networks \
    dst-address-list=lab-networks \
    action=drop \
    log=yes \
    log-prefix="LAB-DENY " \
    comment="LAB: deny other inter-zone traffic"
```

These are `forward` chain rules. They do not control traffic addressed to
RouterOS itself and therefore do not replace a management-plane input policy.

### Verified counters

After the policy tests, RouterOS reported:

| Rule                          | Packets | Interpretation                                        |
| ----------------------------- | ------: | ----------------------------------------------------- |
| Allow established and related |      14 | Return and subsequent stateful traffic                |
| Drop invalid                  |       0 | No invalid packets observed                           |
| Allow DMZ to Internal         |       1 | First permitted connection packet                     |
| Allow Internal to Database    |       1 | First permitted connection packet                     |
| Deny other inter-zone traffic |       8 | Four DMZ-to-Database and four Internal-to-DMZ packets |

RouterOS logs showed the denied flows with the correct zone interfaces:

```text
in:dmz      out:database  10.10.10.130 -> 10.10.30.130
in:internal out:dmz       10.10.20.130 -> 10.10.10.130
```

This proves both policy ordering and stateful behavior.

Logging every default-deny packet is useful during prototyping but may be too
verbose for sustained workloads. Production realization should disable it or
apply an appropriate rate limit.

## Internet Egress Is Not Yet Implemented

Containers on the application networks do not currently have functional
internet access. RouterOS has a management-side default route, but it does not
source-NAT the `10.10.10.0/24`, `10.10.20.0/24`, or `10.10.30.0/24` networks.

This was observed when an Alpine container could not fetch package indexes over
TLS. It did not affect routing or firewall verification.

Internet egress and NAT should be modeled only if required by application
behavior. They are not prerequisites for proving inter-zone routing.

## RouterOS Recovery Artifacts

The working RouterOS state can be captured with:

```routeros
/export hide-sensitive file=vm-connectivity-prototype
/system backup save name=vm-connectivity-prototype
```

The text export is the useful input for Terraform resource mapping. The binary
backup is a RouterOS-specific recovery artifact and should not be treated as
declarative source code.

## Proven Conclusions

1. CHR is viable on Apple Silicon through QEMU x86-64 emulation.
2. QEMU ARM64 Ubuntu can use hardware acceleration and named UTM Host Networks.
3. Separate UTM Host Networks provide the required isolated Layer-2 domains.
4. Docker macvlan exposes container endpoints directly to RouterOS.
5. RouterOS routes container traffic between networks on the same Docker host.
6. TTL and traceroute prove the traffic path through RouterOS.
7. RouterOS connection tracking supports stateful policy and return traffic.
8. Firewall counters and logs provide observable evidence of allowed and denied
   flows.
9. The manual topology is stable across Ubuntu reboot.
10. A physical-LAN DHCP address is unsuitable as the long-term automation
    endpoint for a portable development workstation.
11. A dedicated UTM host-only management subnet provides stable bootstrap
    connectivity independently of the current physical LAN.
12. The management/bootstrap plane should remain separate from the modeled
    platform/data plane.
13. The self-hosted GitHub Actions runner can use the same non-root Terraform
    execution path as interactive development.
14. macOS Local Network privacy configuration is a workstation prerequisite
    for non-root automation access to the dedicated lab management subnet.

## Implications for the Platform Model

The current provider-independent concepts remain appropriate:

* `Network` expresses a logical Layer-3 segment and its CIDR/gateway intent.
* `Interface` connects a node or workload to a logical network.
* `Connection` expresses desired communication between roles or services.
* `Policy` constrains communication and supplies security intent.

The prototype suggests that the model eventually needs enough information to
derive or reference:

* network name;
* CIDR;
* gateway intent;
* node/workload network attachment;
* allowed source and destination roles, services, or networks;
* protocol and port constraints;
* stateful behavior;
* default inter-zone policy;
* optional logging intent;
* optional internet-egress/NAT intent.

Provider-specific details should not be embedded directly in the logical
objects. In particular, the following belong in deployment realization or
provider configuration rather than the core model:

* UTM Host Network UUIDs;
* Ubuntu interface names and MAC addresses;
* Docker `macvlan` driver and parent interfaces;
* Docker IP allocation ranges;
* RouterOS interface identifiers;
* Terraform provider resource names.

The distinction is:

```text
Logical intent                         Provider realization
--------------                         --------------------
network: dmz                           UTM Host Network + macvlan
cidr: 10.10.10.0/24                    RouterOS IP address resource
gateway: 10.10.10.1                    RouterOS interface address
DMZ may reach Internal                 ordered firewall accept rule
DMZ may not reach Database             default-deny/drop rule
```

## Candidate Terraform Mapping

The exact provider schema must be verified before implementation, but the
manual baseline implies the following resource categories:

| Proven manual object        | Candidate Terraform responsibility                     |
| --------------------------- | ------------------------------------------------------ |
| RouterOS interface names    | Interface discovery/rename or stable interface mapping |
| Gateway addresses           | RouterOS IP address resources                          |
| Connected networks          | Derived automatically from interface addresses         |
| `lab-networks` address list | RouterOS firewall address-list resources               |
| Stateful accept rule        | RouterOS firewall filter resource                      |
| Invalid drop rule           | RouterOS firewall filter resource                      |
| Directed allow rules        | Generated firewall filter resources                    |
| Default inter-zone deny     | Final ordered firewall filter resource                 |
| Optional log prefix         | Firewall observability configuration                   |
| Optional source NAT         | RouterOS NAT resource                                  |

Rule ordering is part of behavior and must be deterministic. A Terraform
implementation must not rely on unordered iteration when emitting firewall
rules.

Terraform should configure the existing CHR VM. It should not create the UTM
VM or UTM Host Networks.

## Open Design Decisions

The prototype deliberately does not settle the following questions:

1. Whether Docker macvlan networks are generated directly in Compose or
   created as external deployment prerequisites.
2. Where provider-specific interface mappings live.
3. How container IPs are allocated from the logical network.
4. Whether policies reference networks, roles, services, connections, or a
   combination of them.
5. How protocol and port-level policy is expressed.
6. Whether the default policy is global, per zone, or per site.
7. How firewall rule priorities/order are represented and validated.
8. Whether application networks require NAT or controlled package-repository
   access.
9. Whether Ubuntu's own addresses on DMZ/Internal/Database remain necessary
   after the container deployment is finalized.
10. Whether a host-side macvlan interface is needed for operational access to
    containers.

These should be resolved from the needs of the Out-Dialer reference deployment
and the existing object model, not by generalizing the lab configuration
prematurely.

## Evolution Since the Prototype

The original manual connectivity prototype became the empirical basis for the
current model-driven implementation.

The project subsequently progressed through:

```text
Manual UTM / RouterOS connectivity prototype
                    |
                    v
Logical Platform Model
                    |
                    v
Deployment realization
                    |
          +---------+---------+
          |                   |
          v                   v
Host-aware Docker       RouterOS Terraform
Compose generation         generation
          |                   |
          +---------+---------+
                    |
                    v
          Runtime Out-Dialer lab
                    |
                    v
External observability interface
                    |
                    v
RouterOS-generated metrics access
                    |
                    v
Prometheus -> RouterOS -> Out-Dialer
                    |
                    v
Trusted self-hosted local-lab workflow
```
The prototype's provider-specific observations were intentionally kept outside
the logical Platform Model.

The current implementation now derives Docker and RouterOS artifacts from the
validated model and deployment realization rather than reproducing the manual
prototype configuration directly.

The stable management network remains a bootstrap prerequisite rather than
modeled platform intent.

Current work has moved into the Observability/SRE phase. The next
infrastructure objective is persistent storage for Prometheus, Grafana and
Loki, followed by richer application signals, SLIs, SLOs and related
operational practices.

## Definition of Success Achieved

The manual prototype is successful because:

* all three networks survive VM reboot;
* each container reaches its RouterOS gateway;
* cross-network container traffic traverses RouterOS;
* permitted stateful flows succeed;
* prohibited new flows fail;
* RouterOS counters and logs explain the result;
* the implementation boundary between lab construction and infrastructure
  automation is now concrete.

This is the baseline against which the future Platform Model and Terraform
implementation should be evaluated.
