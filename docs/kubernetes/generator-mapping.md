# Kubernetes Generator Mapping — Out-Dialer

**Status:** Design contract for incremental implementation
**Target:** `docs/kubernetes/generator-mapping.md`
**Initial scope:** Out-Dialer `portal` Deployment and Service, local UTM/kubeadm lab
**Inputs:** Validated Platform Model + `realizations/out-dialer/local-lab.yaml`

## 1. Architectural boundary

The Platform Model remains deployment-independent. Its objects express logical workloads, application endpoints, and resource requirements. The Deployment Realization selects workloads and configures Kubernetes-specific behavior. The Kubernetes generator projects those inputs into ordinary Kubernetes resources without duplicating authoritative model values.

```text
Platform Model (nodes, deployments, applications, compute profiles,
                platform.external_interfaces.metrics)
                     +
Deployment Realization (kubernetes.namespace, workloads, probes,
                        service type, replica count, image policy,
                        metrics discovery convention)
                     |
                     v
            Validation / reference resolution
                     |
                     v
              Kubernetes Generator
                     |
          +----------+-----------+
          |                      |
          v                      v
  portal-deployment.yaml   portal-service.yaml
```

Do not derive Kubernetes networking from `compute.nodes.*.interfaces` or `external_interfaces.metrics.sourceNetwork` in the initial version. Kubernetes CNI, NetworkPolicy, Ingress, and Prometheus connectivity are separate realization concerns.

## 2. Reference platform facts and changes

The currently running Portal container (`docker/portal/app.py`) listens on **HTTP 8443** and exposes Prometheus metrics at **HTTP 9090** (path `/metrics`). `docker/portal/Dockerfile` does not configure TLS. The existing manually deployed Kubernetes manifests expose those two ports, use `imagePullPolicy: Never`, and configure `/health` HTTP readiness/liveness probes.

The current application model incorrectly names `Portal.endpoints.https` with protocol `HTTPS`, even though the application serves HTTP. Rename only this Portal endpoint key to `http`, change its protocol to `HTTP`, and retain port **8443**. Do **not** change the Flask server or Kubernetes bootstrap manifests. Future external HTTPS will be terminated by an Ingress/Gateway with HTTP forwarded to the Service on 8443. The separately modeled `Authentication.https` endpoint is not part of this correction.

The existing `portal` deployment references both `Portal` and `Authentication`. The Kubernetes realization must explicitly select `Portal.http` for the main port. It must not implicitly expose every endpoint of every application listed under a deployment (in particular, do not expose `Authentication.https:8444`).

## 3. Compute profile resource policy

`compute.nodes.<node>.computeProfile` references `compute.compute_profiles.<profile>`.

**Unit contract:** `cpu` is a positive number of **CPU cores**; `ram` is a positive integer of **MiB**. These are workload **per-replica resource requirements**, not node capacities or entire-deployment totals.

Initial Out-Dialer lab profiles (to be validated against real usage later):

| Profile | `cpu` (cores) | `ram` (MiB) | Kubernetes requests |
|---|---:|---:|---|
| small | 0.25 | 256 | `cpu: 250m`, `memory: 256Mi` |
| medium | 0.5 | 512 | `cpu: 500m`, `memory: 512Mi` |
| large | 1 | 1024 | `cpu: "1"`, `memory: 1024Mi` |

The UTM lab has two workers, each with allocatable **2 CPUs** and **3,360,120 KiB** of RAM (~3,281 MiB). Existing system workloads and node-level placement still affect actual scheduling. Requests multiply by replica count; verify cluster headroom before deploying higher replicas.

**Generator mapping:** `containers[].resources.requests.cpu` and `.memory` derive from the selected profile. Do not emit `resources.limits` in v1. A future realization may optionally set limits without redefining the platform's required resources. The compute-profile Yamale schema currently requires integer CPU >=1 and memory >=1024; revise it to permit positive fractional CPU and smaller positive memory requests.

## 4. Proposed Kubernetes realization section

Append to the **existing** `realizations/out-dialer/local-lab.yaml`, retaining the existing `name`, `docker` and `routeros` sections unchanged:

```yaml
kubernetes:
  namespace: out-dialer

  workloads:
    portal:
      node: portal
      replicas: 2
      imagePullPolicy: Never

      endpoints:
        http:
          application: Portal
          endpoint: http

      service:
        type: ClusterIP

      probes:
        readiness:
          path: /health
          port: http
          initialDelaySeconds: 3
          periodSeconds: 5

        liveness:
          path: /health
          port: http
          initialDelaySeconds: 10
          periodSeconds: 10

  observability:
    metrics:
      externalInterface: metrics
      discovery: prometheus-annotations
```

`workloads.portal` is the Kubernetes object name; `node: portal` binds it to the existing Platform Model node. The workload's `node` resolves `deployment`, `product` (image) and `computeProfile` (requests). The `endpoints` binding selects which ordinary application endpoints are exported. Health probe `port` references that named selected port; it is not an arbitrary numeric literal.

`observability.metrics.externalInterface` selects the **existing** `platform.external_interfaces.metrics` definition. Metrics endpoint identities and ports are not redefined in the realization. `discovery` enables the optional Prometheus-style Service annotation convention. This configures discovery metadata only, not Prometheus deployment, scrape configuration, firewall/routing, or ServiceMonitor.

## 5. Application endpoint metadata

The Platform Model already defines metric endpoints on applications and the `platform.external_interfaces.metrics` target list. Add an optional deployment-independent `path` attribute under application endpoint metadata, validated as a path beginning with `/`.

For currently implemented metrics producers, define `/metrics` on the `metrics` endpoint (Portal, CampaignManager and CallSimulator). This avoids hard-coding the metrics URL path inside the generator. The initial generator only materializes Portal. Authentication's separately modeled endpoints are not part of the Portal endpoint selection.

Example Portal definition:

```yaml
Portal:
  description: User-facing REST API for campaign management.
  endpoints:
    http:
      protocol: HTTP
      port: 8443
    metrics:
      protocol: HTTP
      port: 9090
      path: /metrics
```

## 6. Kubernetes resource mapping

| Kubernetes resource path | Source | Rule |
|---|---|---|
| Deployment/Service `metadata.name` | `kubernetes.workloads.<name>` | Stable workload name (`portal`) |
| `metadata.namespace` | `kubernetes.namespace` | Copy (`out-dialer`) |
| Labels: `app`, `app.kubernetes.io/part-of` | Workload name, `platform.platform.id` | `portal`, `out-dialer` |
| Deployment `spec.replicas` | `workloads.portal.replicas` | Copy; current prototype `2` |
| `spec.selector.matchLabels`, Pod labels | Workload name | Consistent `app: portal` |
| Container `name` | Workload name | `portal` |
| Container `image` | Node → deployment → `product` | Reuse image naming convention: `out-dialer/portal:0.1` |
| `imagePullPolicy` | Realization workload | `Never` for preloaded-image lab |
| `resources.requests.cpu` | Node → compute profile `cpu` | Cores to Kubernetes CPU quantity (`0.25` → `250m`) |
| `resources.requests.memory` | Node → compute profile `ram` | MiB to Kubernetes memory quantity (`256` → `256Mi`) |
| Main `containerPort` | Realization selected application endpoint → model port | `http: 8443`, `protocol: TCP` |
| Metrics `containerPort` | External metrics interface target → model endpoint | `metrics: 9090`, `protocol: TCP`; deduplicate |
| HTTP readiness/liveness probes | Realization `probes` | `/health` on named port `http`; scheme HTTP for HTTP endpoint |
| Service `spec.type` | `workloads.portal.service.type` | `ClusterIP` |
| Service selector | Workload name | `app: portal` |
| Main Service port | Selected application endpoint | `port: 8443`, `targetPort: http`, TCP |
| Metrics Service port | External metrics interface target | `port: 9090`, `targetPort: metrics`, TCP |
| Service scrape annotations | Discovery convention + model metrics endpoint | See below |

Protocol mapping: application-level `HTTP`/`HTTPS` implies transport `TCP` for Kubernetes container and Service port definitions. Protocol-aware HTTP probes should use the selected application endpoint's actual HTTP/HTTPS protocol. Do not assume `8443` means HTTPS. Unknown protocols must not silently default to TCP without a validated mapping.

### Metrics selection

For a workload, resolve its node to its deployment and the deployment's application references. Inspect `platform.external_interfaces[externalInterface].targets`; a matching metrics target must reference an application installed by that deployment and a valid `metrics` endpoint under that application. For Portal, the authoritative target is `Portal.metrics`; it resolves to TCP port 9090 and HTTP path `/metrics`.

Do not use the entire `external_interfaces.metrics.targets` list to open ports on every workload. Do not materialize targets of other applications (CampaignManager or CallSimulator) in the Portal Service. Preserve separation of application endpoint data from exposure policy. Fail validation for invalid or ambiguous mappings instead of silently selecting one.

### Prometheus annotations

When discovery is `prometheus-annotations`, add the following **Service** annotations:

```yaml
metadata:
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/path: "/metrics"
    prometheus.io/port: "9090"
```

`path` and `port` come from the selected metrics application endpoint. These annotations are a convention interpreted only when a Prometheus Kubernetes service-discovery/relabeling configuration is later installed. They **do not** themselves cause scraping or establish network connectivity. Do not create a Prometheus server, `ServiceMonitor`, `NetworkPolicy`, or scrape job in the first generator.

## 7. Expected initial generated artifacts

Generate only two files under a caller-specified output directory:

```text
portal-deployment.yaml
portal-service.yaml
```

Expected Deployment key values: `replicas: 2`, `image: out-dialer/portal:0.1`, `imagePullPolicy: Never`, `requests: {cpu: 250m, memory: 256Mi}`, named ports `http:8443` and `metrics:9090`, and the current `/health` HTTP readiness/liveness settings.

Expected Service key values: `ClusterIP`, `app: portal` selector, `http:8443` and `metrics:9090` TCP ports, and the three Prometheus annotations shown above.

Compare **semantic YAML structures**, not raw YAML text, against `k8s/out-dialer/portal-deployment.yaml` and `k8s/out-dialer/portal-service.yaml`. Differences in replicas, resource requests, and annotations are intentional. Preserve other established behavior.

## 8. CLI and incremental implementation

Target public CLI interface for a later milestone:

```bash
.venv/bin/python src/cli.py generate kubernetes \
  models/out-dialer \
  --realization realizations/out-dialer/local-lab.yaml \
  --output-dir build/k8s/out-dialer
```

Follow the existing generator API shape (`generate(model, realization)` plus `serialize()`), current YAML serialization practices, and repository `AGENTS.md`. Generation should be deterministic and read-only with respect to the live cluster.

**Milestone 1 — model and realization preparation:**
- Update Portal endpoint identity/protocol (without modifying Flask or live manifests).
- Introduce model endpoint optional `path` and appropriate metrics paths.
- Update compute profile values and CPU/RAM schema; document units.
- Append Kubernetes realization section and schema validation.
- Extend realization dataclass/loader to expose `.kubernetes` without disturbing Docker/RouterOS.
- Add minimal semantic realization-reference checks for selected Kubernetes node, endpoint binding, and external metrics interface; keep the existing reference registry/docs in sync.
- Add/adjust tests and document these mappings.

**Milestone 2 — generator + CLI:** implement `src/generators/kubernetes.py`, `generate kubernetes`, output files, and comprehensive generator tests.

**Milestone 3 — integration:** add CI generation and manifest validation, then switch CD to generate artifacts from reviewed `main` before deploying. Preserve existing manual manifests and working CD pipeline until the generated output is verified and the change is reviewed.

## 9. Explicit non-goals

- No Flask TLS changes, certificate provisioning, or Ingress in these milestones.
- No Kubernetes cluster mutation during model/generator development.
- No Kubernetes RBAC, namespace bootstrap, metrics server, external Prometheus, or ServiceMonitor generation.
- No container build/push/image registry pipeline.
- No resource limits or HPA in v1; keep `replicas` realization-owned.
- No changes to Docker Compose or RouterOS output other than consequences of intentionally correcting Portal endpoint metadata; regression tests must continue to pass.
