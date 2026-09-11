# Observability Lab Prototype Extension

**Completed and verified:** 2026-09-10

## Observability Extension

The original connectivity prototype proved the DMZ, Internal, and Database
application networks on a single Ubuntu Docker host. The next prototype stage
adds a separate observability Docker host and verifies end-to-end collection of
real application business metrics.

The observability extension deliberately follows the same development method as
the original networking work:

```text
Requirement
    |
    v
Manual prototype
    |
    v
Verify actual behavior
    |
    v
Update Platform Model / realization
    |
    v
Update generators
    |
    v
Generate and reconcile infrastructure
```

The configuration described below is therefore a **verified manual baseline**.
Some parts are intentionally imperative or hard-coded and must not be mistaken
for the final model-driven implementation.

## Extended Lab Topology

The lab now contains two Ubuntu Docker hosts.

```text
                    Management LAN 192.168.1.0/24
                         |                 |
                       Mac             RouterOS
                                         |
                 +-----------------------+----------------------+
                 |             |             |                  |
              DMZ           Internal      Database        Observability
          10.10.10/24     10.10.20/24   10.10.30/24     10.10.40/24
                 |             |             |                  |
                 |             |             |                  |
          +------+-------------+-------------+--+        +------+------+
          |         ubuntu-qemu                  |        | obs. VM     |
          |                                      |        |             |
          | Portal:       DMZ + Internal         |        | Prometheus  |
          | Campaign:     Internal + Database    |        |   bridge    |
          | Call Sim:     Internal               |        |   + obs net |
          +--------------------------------------+        +-------------+
```

The diagram is intentionally interface-centric. It shows the logical networks
to which each containerized service is attached rather than treating a Docker
host as if it had only one application-facing network.

The important architectural distinction is that `observability` is a **second
Docker host**, not an additional application interface on `ubuntu-qemu`.

### Workload Docker host

`ubuntu-qemu` retains the existing application interfaces:

```text
enp0s1   Management   DHCP on management LAN
enp0s2   DMZ          10.10.10.10/24
enp0s3   Internal     10.10.20.10/24
enp0s4   Database     10.10.30.10/24
```

### Observability Docker host

The new observability VM uses:

```text
enp0s1   Management      192.168.1.141/24 during verification
enp0s2   Observability   10.10.40.10/24
```

The observability interface has no default route or DNS configuration. The VM
retains its management default route through `enp0s1`.

The management address is environment-assigned and should not be treated as a
stable application/model identity.

### RouterOS

RouterOS now has an additional logical interface:

```text
observability   10.10.40.1/24
```

The observability network is a fourth UTM Host Network with CIDR
`10.10.40.0/24`.

Layer-2 connectivity between the observability VM and RouterOS was verified in
both directions.

## Observability Docker Network

The observability VM runs the existing observability stack:

- Prometheus
- Grafana
- Loki
- Promtail

The local Compose configuration was extended with a macvlan network equivalent
to:

```yaml
networks:
  observability:
    driver: macvlan
    driver_opts:
      parent: enp0s2
    ipam:
      config:
        - subnet: 10.10.40.0/24
          gateway: 10.10.40.1
          ip_range: 10.10.40.128/28
```

Defining the Docker network alone is not sufficient. A service must explicitly
attach to it before the container receives an address on that network.

## Prometheus Dual-Homed Network Design

Prometheus must satisfy two different connectivity requirements:

1. remain reachable through the observability VM's normal Docker/management
   path;
2. scrape application containers through RouterOS over the observability
   network.

The verified prototype therefore attaches Prometheus to both Docker networks:

```yaml
prometheus:
  # existing image, command, ports and volumes omitted here
  cap_add:
    - NET_ADMIN
  networks:
    default: {}
    observability: {}
```

During verification Prometheus had approximately:

```text
eth0  172.18.0.2       Docker bridge
eth1  10.10.40.128     observability macvlan
```

The Docker bridge remains the default route:

```text
default via 172.18.0.1 dev eth0
```

A more-specific route directs application scrape traffic through RouterOS:

```text
10.10.20.0/24 via 10.10.40.1 dev eth1
```

The prototype route was added imperatively:

```bash
docker exec -u 0 observability-prometheus-1 \
  ip route add 10.10.20.0/24 via 10.10.40.1 dev eth1
```

`NET_ADMIN` was temporarily granted because modifying the container routing
table requires that capability.

### Why the macvlan network must not be the default route

An earlier prototype made the observability macvlan the preferred/default path.
Scraping became possible, but access to the Prometheus UI through the published
host port failed because reply traffic followed a different path from incoming
management traffic.

The working design preserves:

```text
management / published-port traffic -> Docker bridge default route
application scrape traffic          -> specific route via RouterOS
```

This is an important realization requirement. Simply attaching Prometheus to
the observability macvlan does not fully describe the required networking
behavior.

## RouterOS Observability Policy

The `lab-networks` set was extended conceptually to include
`10.10.40.0/24`.

The verified observability policy permits Prometheus to scrape the Internal
network on TCP/9090:

```text
Observability 10.10.40.0/24
        |
        | TCP/9090
        v
Internal 10.10.20.0/24
```

The RouterOS forward-chain rule was verified using packet counters while
Prometheus scraped the services.

Other new Observability-to-Internal application traffic remains outside the
permanent observability policy.

## Workload Generation from macOS

The workload Ubuntu host cannot normally communicate directly with its own
macvlan children. Attempting to reach the Portal container from `ubuntu-qemu`
confirmed the macvlan host-isolation behavior already identified by the
original prototype.

A host-side macvlan shim would solve that problem, but adding another address
and interface only to generate test traffic would create additional unmanaged
host configuration. It was deliberately not introduced.

Instead, the macOS host was used as an external workload client.

RouterOS has a management address on the physical LAN
(`192.168.1.127/24` during verification). The Mac was configured to route the
Internal lab network through RouterOS:

```text
10.10.20.0/24 -> RouterOS management address
```

A narrow RouterOS prototype rule permitted management-LAN traffic to the Portal
API only.

The Portal was verified to listen on TCP/8443. TCP/8080 is used by the Campaign
Manager API and is not the Portal listener.

The resulting workload path is:

```text
Mac
 |
 | TCP/8443
 v
RouterOS
 |
 v
Portal
 |
 v
Campaign Manager
 |
 v
Call Simulator
```

A campaign submitted through this path returned HTTP `202 Accepted` and
executed asynchronously.

The management-to-Portal rule and current management addresses are prototype
test-access details. The final model must decide whether test/control-plane
access is a modeled requirement or remains a lab prerequisite.

## Verified Out-Dialer Addresses During the Prototype

At the time of end-to-end verification the workload containers had:

```text
Portal            10.10.20.130   API 8443, metrics 9090
Campaign Manager  10.10.20.129   API 8080, metrics 9090
Call Simulator    10.10.20.128   metrics 9090
```

These addresses came from Docker macvlan IPAM and can change when containers
are recreated. They are recorded as evidence of the verified prototype, **not
as stable service identities**.

Prometheus currently uses these addresses as static scrape targets. This is
acceptable for the manual prototype but is not a satisfactory final
realization.

## End-to-End Metrics Verification

The complete path was verified:

```text
Mac
 |
 v
Portal -> Campaign Manager -> Call Simulator
  |             |                  |
  +-------------+------------------+
                |
          /metrics :9090
                ^
                |
             RouterOS
                ^
                |
        Prometheus 10.10.40.x
```

Prometheus successfully collected the business metrics introduced in the
Out-Dialer services.

Queries verified during the prototype included:

```promql
up

sum by (operation, status) (portal_requests_total)

sum by (status) (campaigns_total)

sum by (result) (calls_total)

call_duration_seconds_count

histogram_quantile(
  0.95,
  sum by (le) (
    rate(call_duration_seconds_bucket[5m])
  )
)
```

This proves more than endpoint reachability: a real synthetic campaign entered
through the Portal, traversed the application workflow, produced business
telemetry, and that telemetry was collected by Prometheus across the routed lab
network.

## Time Synchronization Discovery

Prometheus initially appeared to return empty query results even though the
scrape path had already been proven.

The Prometheus UI reported approximately twelve minutes of clock drift between
the browser and server. The observability VM showed:

```text
System clock synchronized: no
NTP service: active
```

The VM uses `chrony`, not `systemd-timesyncd`. Chrony itself reported a system
clock error of approximately 720 seconds.

After correcting the clock with chrony, Prometheus query results appeared
normally.

This establishes a new lab prerequisite:

> Hosts participating in monitoring and, later, distributed tracing must have
> synchronized system clocks.

This requirement will become even more important when OpenTelemetry/Tempo
tracing is introduced because cross-service event ordering depends on
consistent timestamps.

## Prototype-Only Configuration

The following parts of the working state are intentionally temporary:

- hard-coded Prometheus scrape target IP addresses;
- dynamically allocated workload container addresses used as service identity;
- `NET_ADMIN` granted to Prometheus;
- the imperative route added inside the Prometheus container;
- management-LAN test access to the Portal;
- environment-assigned management addresses;
- manual RouterOS observability interface and firewall configuration.

These items are discoveries produced by the prototype. They are requirements
for the next model/realization iteration, not acceptable final automation.

## Required Model and Realization Evolution

The existing realization assumes one Docker runtime. The observability
prototype demonstrates that this assumption no longer matches the lab.

The next realization design should represent **named Docker hosts**.

A candidate shape is:

```yaml
name: local-lab

docker:
  hosts:
    workload:
      networkDriver: macvlan
      networks:
        dmz:
          parent: enp0s2
          ipam:
            offset: 128
            prefixLength: 28
        internal:
          parent: enp0s3
          ipam:
            offset: 128
            prefixLength: 28
        database:
          parent: enp0s4
          ipam:
            offset: 128
            prefixLength: 28

    observability:
      networkDriver: macvlan
      networks:
        observability:
          parent: enp0s2
          ipam:
            offset: 128
            prefixLength: 28

routeros:
  interfaces:
    dmz:
      physicalInterface: ether1
    internal:
      physicalInterface: ether2
    database:
      physicalInterface: ether3
    observability:
      physicalInterface: ether4
```

This is a **candidate realization shape**, not an approved schema.

`hosts` is preferred over `vms` because a Docker runtime may later be hosted by
a VM, physical server, remote Docker host, or another compute environment. The
realization should describe the deployment/runtime role without unnecessarily
binding the logical concept to UTM.

The prototype does **not** justify introducing a generalized `providers`
abstraction at this point. Cloud deployment has different semantics and should
be designed from concrete requirements rather than treating every environment
as another Docker host.

## Model Questions Exposed by the Prototype

Before implementing the multi-host realization, the following questions must
be resolved against the current Platform Model, realization loader, schema,
generators, CLI, and tests:

1. **Service placement:** where is the association between a service/workload
   and a named Docker host represented?
2. **Artifact generation:** should one realization produce one Compose artifact
   per Docker host, for example workload and observability Compose files?
3. **Observability network:** how is `10.10.40.0/24` represented in the logical
   model and connected to the RouterOS realization?
4. **Prometheus routing:** how should a required container route be represented
   declaratively without retaining an imperative `docker exec ip route add`?
5. **Capabilities:** can the final design avoid `NET_ADMIN`, or is a controlled
   network capability part of the generated deployment?
6. **Service discovery/addressing:** how should Prometheus obtain stable scrape
   targets without depending on dynamically allocated macvlan addresses?
7. **Firewall identity:** firewall policy must not depend on a container IP that
   may change after recreation.
8. **Test/control access:** is Mac/management access to the Portal part of the
   platform intent, a realization concern, or merely a lab prerequisite?
9. **Time synchronization:** should NTP remain an explicit host prerequisite, or
   does any future host-configuration backend own it?

These questions should be answered incrementally. The working manual prototype
should remain the behavioral reference.

## Expected Generator Direction

If the realization evolves to named Docker hosts, a natural generator boundary
is one Docker Compose artifact per host, conceptually:

```text
Platform Model + local-lab realization
        |
        +--> workload Docker Compose
        |
        +--> observability Docker Compose
        |
        +--> RouterOS Terraform
```

The exact CLI syntax and output paths must be based on the existing CLI and
generator architecture before implementation. They are intentionally not
specified by this prototype document.

## Updated Infrastructure-as-Code Checkpoint

The observability experiment has now reached the same transition point as the
original networking prototype:

```text
Manual:
  [x] observability L2 network proven
  [x] RouterOS interface/gateway proven
  [x] Observability -> Internal TCP/9090 policy proven
  [x] Prometheus routed scrape path proven
  [x] complete Out-Dialer business-metrics path proven
  [x] external workload generation through RouterOS proven
  [x] time-synchronization dependency identified

Next:
  [ ] update logical model where required
  [ ] generalize realization from one Docker runtime to named Docker hosts
  [ ] update realization validation/schema
  [ ] update Docker Compose generation
  [ ] update RouterOS Terraform generation
  [ ] define deterministic addressing or service discovery
  [ ] replace imperative Prometheus routing
  [ ] terraform plan / generated-artifact review
  [ ] reconcile manual prototype state with generated state
```

The next implementation work should start from these verified requirements
rather than extending the manual configuration further.

## Updated Definition of Success

The observability extension is successful because:

- the observability VM is isolated on its own application network;
- RouterOS routes and filters observability traffic;
- Prometheus reaches application metrics through the intended routed path;
- management access to Prometheus remains functional;
- the Out-Dialer accepts a real synthetic campaign through an external client;
- Portal, Campaign Manager, and Call Simulator emit business metrics from that
  campaign;
- Prometheus collects and queries those metrics;
- the experiment exposed the concrete realization changes needed for a
  multi-host deployment;
- no undocumented host-side macvlan shim was introduced merely to make testing
  convenient.

This extended manual baseline should be preserved before changing the Platform
Model or generators.
